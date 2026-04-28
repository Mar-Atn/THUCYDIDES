"""Unified Event Dispatcher — single point of delivery for all AI agent events.

Replaces both the orchestrator pulse system and the auto-pulse service.
All events flow through one queue, one dispatcher. No race conditions.

Architecture:
  ANY EVENT --> enqueue(role_id, tier, event_type, message) --> DB queue
  DISPATCHER LOOP --> check queue every N seconds --> send_event to idle agents

Tiers:
  1 = Critical (attacks, nuclear) — checked every 3s
  2 = Urgent (chat, meetings, transactions) — checked every 5s
  3 = Routine (round updates, news) — checked at pulse interval

Async DB Migration (2026-04-22):
  Queue reads (dequeue, mark_processed, get_queue_depth, clear_queue) use the
  async Supabase client to avoid blocking the event loop. Writes from sync
  callers (enqueue, enqueue_for_country) keep the sync client for compatibility
  with action_dispatcher which runs in threads.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from engine.agents.managed.session_manager import ManagedSessionManager, SessionContext
from engine.agents.managed.tool_executor import ToolExecutor
from engine.services.supabase import get_client
from engine.services.async_db import get_async_client

logger = logging.getLogger(__name__)

# Tier check intervals (seconds)
# T1/T2 kept fast for responsive chat; T3 for routine polling
TIER_1_INTERVAL = 3
TIER_2_INTERVAL = 5
TIER_3_INTERVAL = 30

# Agent states
IDLE = "IDLE"
ACTING = "ACTING"
IN_MEETING = "IN_MEETING"
FROZEN = "FROZEN"


class EventDispatcher:
    """Central event queue + dispatch loop for all AI agents in a sim run."""

    def __init__(self, sim_run_id: str):
        self.sim_run_id = sim_run_id
        # Load API key from settings (.env) — os.environ may not have it
        try:
            from engine.config import settings
            api_key = settings.anthropic_api_key or None
        except Exception:
            api_key = None
        self.session_manager = ManagedSessionManager(api_key=api_key)
        self.agents: dict[str, SessionContext] = {}  # role_id -> session
        self.agent_states: dict[str, str] = {}  # role_id -> state
        self._state_since: dict[str, float] = {}  # role_id -> timestamp of last state change
        self._running = False
        self._tasks: list[asyncio.Task] = []
    # Max time an agent can stay in ACTING before forced back to IDLE (seconds)
    ACTING_TIMEOUT = 180  # 3 minutes

    # -- Queue Operations --------------------------------------------------

    def enqueue(
        self,
        role_id: str,
        tier: int,
        event_type: str,
        message: str,
        metadata: dict | None = None,
    ) -> str:
        """Write an event to the queue. Called from anywhere (sync).

        STAYS SYNC — called from sync action_dispatcher (runs in threads).
        Uses the sync Supabase client for a single fast insert (<100ms).
        Returns the event ID.
        """
        db = get_client()
        result = db.table("agent_event_queue").insert({
            "sim_run_id": self.sim_run_id,
            "role_id": role_id,
            "tier": tier,
            "event_type": event_type,
            "message": message,
            "metadata": metadata or {},
        }).execute()
        event_id = result.data[0]["id"] if result.data else "?"
        logger.info(
            "[dispatcher] Enqueued T%d %s for %s: %s",
            tier, event_type, role_id, message[:80],
        )
        return event_id

    async def dequeue(self, role_id: str, max_tier: int = 3) -> list[dict]:
        """Get all unprocessed events for a role, up to max_tier.

        ASYNC — called from dispatch loop. Uses async Supabase client
        to avoid blocking the event loop.

        Returns events ordered by tier (critical first), then created_at.
        """
        db = await get_async_client()
        result = await (
            db.table("agent_event_queue")
            .select("*")
            .eq("sim_run_id", self.sim_run_id)
            .eq("role_id", role_id)
            .lte("tier", max_tier)
            .is_("processed_at", "null")
            .order("tier")
            .order("created_at")
            .execute()
        )
        return result.data or []

    async def mark_processed(self, event_ids: list[str], error: str | None = None) -> None:
        """Mark events as processed (or failed).

        ASYNC — called from dispatch loop.
        """
        if not event_ids:
            return
        db = await get_async_client()
        update: dict = {"processed_at": datetime.now(timezone.utc).isoformat()}
        if error:
            update["processing_error"] = error
        for eid in event_ids:
            await db.table("agent_event_queue").update(update).eq("id", eid).execute()

    async def get_queue_depth(self, role_id: str) -> dict:
        """Get count of unprocessed events by tier for a role.

        ASYNC — called from dispatch loop and async endpoints.
        """
        db = await get_async_client()
        events = await (
            db.table("agent_event_queue")
            .select("tier")
            .eq("sim_run_id", self.sim_run_id)
            .eq("role_id", role_id)
            .is_("processed_at", "null")
            .execute()
        )
        tiers: dict[int, int] = {1: 0, 2: 0, 3: 0}
        for e in events.data or []:
            tiers[e["tier"]] = tiers.get(e["tier"], 0) + 1
        return tiers

    async def clear_queue(self, role_id: str | None = None) -> int:
        """Clear unprocessed events. If role_id given, clear only for that role.

        ASYNC — called from shutdown and async endpoints.
        """
        db = await get_async_client()
        query = (
            db.table("agent_event_queue")
            .delete()
            .eq("sim_run_id", self.sim_run_id)
            .is_("processed_at", "null")
        )
        if role_id:
            query = query.eq("role_id", role_id)
        result = await query.execute()
        count = len(result.data or [])
        logger.info("[dispatcher] Cleared %d queued events (role=%s)", count, role_id or "ALL")
        return count

    # -- Agent Registration ------------------------------------------------

    def register_agent(self, role_id: str, ctx: SessionContext) -> None:
        """Register an agent with the dispatcher."""
        self.agents[role_id] = ctx
        self.agent_states[role_id] = IDLE
        logger.info("[dispatcher] Registered agent %s", role_id)

        # Ask the managed agent to generate its Avatar Identity
        self._enqueue_avatar_identity_generation(role_id)

    def _enqueue_avatar_identity_generation(self, role_id: str) -> None:
        """Ask the managed agent to generate its Avatar Identity.

        Deduplicates: skips if an unprocessed avatar_identity_request
        already exists in the queue for this role.
        """
        try:
            db = get_client()
            existing = db.table("agent_event_queue") \
                .select("id") \
                .eq("sim_run_id", self.sim_run_id) \
                .eq("role_id", role_id) \
                .eq("event_type", "avatar_identity_request") \
                .is_("processed_at", "null") \
                .limit(1).execute()
            if existing.data:
                logger.info("[dispatcher] Skipping duplicate avatar_identity_request for %s", role_id)
                return
        except Exception:
            pass  # on error, enqueue anyway

        from engine.agents.managed.avatar_generator import build_avatar_identity_prompt
        self.enqueue(
            role_id=role_id,
            tier=2,
            event_type="avatar_identity_request",
            message=build_avatar_identity_prompt(),
        )

    def set_agent_state(self, role_id: str, state: str) -> None:
        """Update agent state (IDLE, ACTING, IN_MEETING, FROZEN).

        Write-through: persists to ai_agent_sessions table (M5.8).
        """
        old = self.agent_states.get(role_id)
        self.agent_states[role_id] = state
        self._state_since[role_id] = asyncio.get_event_loop().time()
        if old != state:
            logger.info("[dispatcher] Agent %s: %s -> %s", role_id, old, state)
            # Write-through to DB (fire-and-forget)
            try:
                db = get_client()
                db.table("ai_agent_sessions") \
                    .update({"agent_state": state}) \
                    .eq("sim_run_id", self.sim_run_id) \
                    .eq("role_id", role_id) \
                    .execute()
            except Exception as e:
                logger.warning("[dispatcher] Failed to persist state for %s: %s", role_id, e)

    # -- Auto-Recovery (M5.8) ----------------------------------------------

    async def recover_from_db(self) -> int:
        """Recover dispatcher state from DB after server restart.

        SPEC: M4 Section 5.3 (Server Recovery).

        For each active session in DB:
        1. Health-check the Anthropic session (log status for diagnostics)
        2. Always recreate — reconnection to old sessions is unreliable
        3. Verify the new session works (retrieve status)
        4. Register as IDLE — old state is meaningless after restart
        5. Send recovery pulse if agent has saved memories

        Returns number of agents recovered.
        """
        import hashlib
        from engine.agents.managed.system_prompt import build_system_prompt

        db = get_client()
        sessions = db.table("ai_agent_sessions") \
            .select("*") \
            .eq("sim_run_id", self.sim_run_id) \
            .in_("status", ["ready", "active"]) \
            .execute().data or []

        if not sessions:
            logger.info("[recovery] No active sessions found for sim %s", self.sim_run_id[:8])
            return 0

        logger.info("[recovery] Found %d active sessions for sim %s", len(sessions), self.sim_run_id[:8])
        recovered = 0

        for row in sessions:
            role_id = row["role_id"]
            country_code = row["country_code"]
            round_num = row.get("round_num", 1)

            # Step 1: Health-check the existing Anthropic session
            old_session_id = row["session_id"]
            session_alive = False
            try:
                status = await self.session_manager.client.beta.sessions.retrieve(old_session_id)
                session_status = getattr(status, "status", "unknown")
                session_alive = session_status in ("idle", "running", "requires_action")
                logger.info("[recovery] Session %s for %s: %s (alive=%s)",
                            old_session_id[:20], role_id, session_status, session_alive)
            except Exception as e:
                logger.warning("[recovery] Cannot reach session %s for %s: %s",
                               old_session_id[:20], role_id, e)

            # Step 2: Always recreate on server restart.
            # Even "alive" sessions can become zombie (health-check passes but events
            # are never processed). Recreation is ~10s per agent and guarantees a
            # working session. Prompt hash comparison kept for logging only.
            needs_recreation = True
            if session_alive:
                try:
                    current_prompt = build_system_prompt(role_id, sim_run_id=self.sim_run_id)
                    current_hash = hashlib.md5(current_prompt.encode()).hexdigest()[:16]
                    stored_hash = row.get("prompt_hash")
                    prompt_changed = (current_hash and stored_hash and current_hash != stored_hash)
                    logger.info("[recovery] %s: session alive, prompt %s — recreating for reliability",
                                role_id, "CHANGED" if prompt_changed else "unchanged")
                except Exception:
                    logger.info("[recovery] %s: session alive — recreating for reliability", role_id)

            # Step 3: Recreate session (always — reconnection is unreliable)
            ctx = None
            logger.info("[recovery] Recreating session for %s...", role_id)
            try:
                ctx = await self.session_manager.create_session(
                    role_id=role_id,
                    country_code=country_code,
                    sim_run_id=self.sim_run_id,
                    scenario_code=self.sim_run_id,
                    round_num=round_num,
                    model=row.get("model"),
                )
            except Exception as e:
                logger.error("[recovery] Failed to recreate session for %s: %s", role_id, e)
                # Archive the broken DB row so we don't retry forever
                try:
                    db.table("ai_agent_sessions") \
                        .update({"status": "archived"}) \
                        .eq("sim_run_id", self.sim_run_id) \
                        .eq("role_id", role_id) \
                        .in_("status", ["ready", "active"]) \
                        .execute()
                except Exception:
                    pass
                continue

            # Step 4: Verify the session works
            try:
                verify = await self.session_manager.client.beta.sessions.retrieve(ctx.session_id)
                verify_status = getattr(verify, "status", "unknown")
                if verify_status not in ("idle", "running", "requires_action"):
                    raise ValueError(f"Session not usable: status={verify_status}")
            except Exception as e:
                logger.error("[recovery] Session verification failed for %s: %s — archiving", role_id, e)
                try:
                    db.table("ai_agent_sessions") \
                        .update({"status": "archived"}) \
                        .eq("sim_run_id", self.sim_run_id) \
                        .eq("role_id", role_id) \
                        .in_("status", ["ready", "active"]) \
                        .execute()
                except Exception:
                    pass
                continue

            # Step 5: Register — always IDLE after recovery (M4 SPEC 5.3)
            self.agents[role_id] = ctx
            self.agent_states[role_id] = IDLE
            self.set_agent_state(role_id, IDLE)
            self._state_since[role_id] = asyncio.get_event_loop().time()
            recovered += 1

            # Step 6: Recovery pulse — tell agent to read its notes
            memories = self.session_manager._load_agent_memories(self.sim_run_id, country_code)
            if memories:
                notes_text = "\n".join(
                    f"- [{n['memory_key']}]: {n['content'][:200]}"
                    for n in memories[:10]
                )
                self.enqueue(
                    role_id=role_id, tier=2,
                    event_type="recovery_pulse",
                    message=(
                        f"Your session was recovered after a server restart. "
                        f"You are in Round {round_num}. Your saved notes:\n\n{notes_text}\n\n"
                        f"Read your full notes with read_notes, then continue with your strategy."
                    ),
                )

            # Check if avatar identity exists — regenerate if missing
            identity = self._fetch_avatar_identity(role_id)
            if not identity or len(identity) < 50:
                self._enqueue_avatar_identity_generation(role_id)

            logger.info("[recovery] Recovered agent %s (%s)",
                        role_id, "recreated")

        return recovered

    # -- Dispatch Loop -----------------------------------------------------

    async def start(self) -> None:
        """Start the dispatch loop + auto-pulse + meeting monitor (background tasks)."""
        self._running = True
        self._tasks.append(asyncio.create_task(self._dispatch_loop()))
        self._tasks.append(asyncio.create_task(self._auto_pulse_loop()))
        self._tasks.append(asyncio.create_task(self._meeting_monitor_loop()))
        logger.info(
            "[dispatcher] Started for sim %s with %d agents (dispatch + auto-pulse + meetings)",
            self.sim_run_id, len(self.agents),
        )

    async def stop(self) -> None:
        """Stop the dispatch loop."""
        self._running = False
        for t in self._tasks:
            t.cancel()
        self._tasks.clear()
        logger.info("[dispatcher] Stopped for sim %s", self.sim_run_id)

    async def _dispatch_loop(self) -> None:
        """Main loop — checks queue and delivers events to idle agents."""
        last_tier1_check = 0.0
        last_tier2_check = 0.0
        last_tier3_check = 0.0

        while self._running:
            try:
                now = asyncio.get_event_loop().time()

                # Tier 1: every 3s
                if now - last_tier1_check >= TIER_1_INTERVAL:
                    await self._check_and_deliver(max_tier=1)
                    last_tier1_check = now

                # Tier 2: every 5s (includes Tier 1)
                if now - last_tier2_check >= TIER_2_INTERVAL:
                    await self._check_and_deliver(max_tier=2)
                    last_tier2_check = now

                # Tier 3: every 30s (includes all tiers)
                if now - last_tier3_check >= TIER_3_INTERVAL:
                    await self._check_and_deliver(max_tier=3)
                    last_tier3_check = now

                # Detect stuck agents (ACTING/IN_MEETING too long → force IDLE)
                now_ts = asyncio.get_event_loop().time()
                for role_id in list(self.agents.keys()):
                    state = self.agent_states.get(role_id, IDLE)
                    if state in (ACTING, IN_MEETING):
                        since = self._state_since.get(role_id, now_ts)
                        if now_ts - since > self.ACTING_TIMEOUT:
                            logger.warning(
                                "[dispatcher] Agent %s stuck in %s for %ds — forcing IDLE",
                                role_id, state, int(now_ts - since),
                            )
                            self.set_agent_state(role_id, IDLE)

                await asyncio.sleep(1)  # Base check interval

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("[dispatcher] Loop error: %s", e)
                await asyncio.sleep(5)  # Back off on error

    async def _auto_pulse_loop(self) -> None:
        """Auto-pulse scheduler — sends periodic round_pulse events to all agents.

        Per M5 SPEC D4: "N pulses per round, evenly spaced across round duration."
        Default: 8 pulses per round. Reads pulses_per_round from ai_settings.

        Only sends pulses during active Phase A. Pauses during Phase B,
        inter_round, pre_start, paused, etc.
        """
        from engine.agents.managed.ai_config import _read_setting

        pulse_count = 0
        last_phase = None

        while self._running:
            try:
                # Read sim state
                db = get_client()
                run = db.table("sim_runs").select("status,current_phase,current_round,phase_duration_seconds") \
                    .eq("id", self.sim_run_id).limit(1).execute()

                if not run.data:
                    await asyncio.sleep(10)
                    continue

                sim = run.data[0]
                status = sim.get("status", "")
                phase = sim.get("current_phase", "")
                round_num = sim.get("current_round", 0)
                phase_duration = sim.get("phase_duration_seconds") or 3600  # default 60 min

                # Reset pulse count on phase change + sync round_num on agents
                current_phase_key = f"{round_num}-{phase}"
                if current_phase_key != last_phase:
                    pulse_count = 0
                    last_phase = current_phase_key
                    # Keep agent round_num in sync with sim
                    self.sync_round_num(round_num)

                # Only auto-pulse during active Phase A
                if status != "active" or phase != "A":
                    await asyncio.sleep(5)
                    continue

                # Read pulses_per_round from settings (default 8, 0 = manual only)
                pulses_str = _read_setting("pulses_per_round", "8")
                try:
                    pulses_per_round = max(0, min(10, int(pulses_str)))
                except (ValueError, TypeError):
                    pulses_per_round = 8

                # 0 = manual only — no auto-pulses
                if pulses_per_round == 0:
                    await asyncio.sleep(10)
                    continue

                # Calculate interval
                interval_seconds = max(30, phase_duration / pulses_per_round)

                # Check if we've sent enough pulses this round
                if pulse_count >= pulses_per_round:
                    await asyncio.sleep(10)
                    continue

                # Send enriched pulse to all idle agents
                pulse_count += 1
                for role_id in list(self.agents.keys()):
                    if self.agent_states.get(role_id) in (IDLE,):
                        try:
                            message = self._build_pulse_context(
                                role_id, round_num, pulse_count, pulses_per_round)
                        except Exception as ctx_err:
                            logger.warning("[auto-pulse] Context build failed for %s: %s", role_id, ctx_err)
                            message = (f"Round {round_num}, Phase A — pulse {pulse_count}/{pulses_per_round}. "
                                       f"Assess your situation and take strategic actions.")
                        self.enqueue(
                            role_id=role_id,
                            tier=3,
                            event_type="round_pulse",
                            message=message,
                            metadata={"round_num": round_num, "pulse_num": pulse_count,
                                      "total_pulses": pulses_per_round},
                        )

                logger.info(
                    "[auto-pulse] Round %d pulse %d/%d sent to %d agents (interval=%ds)",
                    round_num, pulse_count, pulses_per_round, len(self.agents), int(interval_seconds),
                )

                # Wait for next pulse interval
                await asyncio.sleep(interval_seconds)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("[auto-pulse] Error: %s", e)
                await asyncio.sleep(10)

    async def _meeting_monitor_loop(self) -> None:
        """Monitor active meetings and drive AI participation.

        Checks every 10s for:
        1. AI-AI meetings (both participants are AI) → run ConversationRouter
        2. AI-Human meetings (one AI, one human) → prompt AI to speak when
           human has sent a message the AI hasn't responded to yet

        Per M5 SPEC D6: AI uses the SAME meeting/chat system as humans.
        """
        MEETING_CHECK_INTERVAL = 10  # seconds

        while self._running:
            try:
                db = get_client()

                # Only monitor meetings during Phase A (no meetings during Phase B)
                run = db.table("sim_runs").select("status,current_phase") \
                    .eq("id", self.sim_run_id).limit(1).execute()
                if run.data:
                    _phase = run.data[0].get("current_phase", "")
                    _status = run.data[0].get("status", "")
                    if _phase != "A" or _status != "active":
                        await asyncio.sleep(MEETING_CHECK_INTERVAL)
                        continue

                # Find active meetings
                active_meetings = db.table("meetings") \
                    .select("id,participant_a_role_id,participant_a_country,participant_b_role_id,participant_b_country,agenda,turn_count,status,metadata,started_at") \
                    .eq("sim_run_id", self.sim_run_id) \
                    .eq("status", "active") \
                    .execute().data or []

                # Auto-end meetings older than 15 minutes
                from datetime import datetime, timezone
                now = datetime.now(timezone.utc)
                for meeting in list(active_meetings):
                    started = meeting.get("started_at")
                    if started:
                        try:
                            started_dt = datetime.fromisoformat(started.replace("Z", "+00:00"))
                            age_minutes = (now - started_dt).total_seconds() / 60
                            if age_minutes > 15:
                                mid = meeting["id"]
                                logger.info("[meetings] Auto-ending meeting %s (age=%.0f min)", mid[:8], age_minutes)
                                from engine.services.meeting_service import end_meeting
                                end_meeting(mid, meeting["participant_a_role_id"])
                                active_meetings.remove(meeting)
                        except (ValueError, TypeError):
                            pass

                for meeting in active_meetings:
                    mid = meeting["id"]
                    role_a = meeting["participant_a_role_id"]
                    role_b = meeting["participant_b_role_id"]
                    turn_count = meeting.get("turn_count", 0)

                    a_is_ai = role_a in self.agents
                    b_is_ai = role_b in self.agents

                    if not a_is_ai and not b_is_ai:
                        continue  # Human-Human meeting — not our business

                    if a_is_ai and b_is_ai:
                        # AI-AI meeting — use avatar text chat if both IDLE and not yet started
                        if turn_count == 0:
                            a_state = self.agent_states.get(role_a, IDLE)
                            b_state = self.agent_states.get(role_b, IDLE)
                            if a_state == IDLE and b_state == IDLE:
                                logger.info("[meetings] Starting AI-AI avatar meeting %s (%s ↔ %s)",
                                            mid[:8], role_a, role_b)
                                # Agents already IN_MEETING (set by tool_executor on accept)
                                # If not (e.g. human accepted for both), set now
                                self.set_agent_state(role_a, IN_MEETING)
                                self.set_agent_state(role_b, IN_MEETING)

                                # Fetch avatar identities
                                identity_a = self._fetch_avatar_identity(role_a)
                                identity_b = self._fetch_avatar_identity(role_b)

                                # Read intent notes from meetings.metadata
                                # (written by Managed Agents via tool_executor per SPEC 4.2)
                                metadata = meeting.get("metadata") or {}
                                intent_a = metadata.get("intent_note_a", "")
                                intent_b = metadata.get("intent_note_b", "")

                                # Run avatar meeting in background
                                asyncio.create_task(
                                    self._run_avatar_meeting(
                                        mid, role_a, role_b,
                                        identity_a, identity_b,
                                        intent_a, intent_b, meeting,
                                    )
                                )
                    else:
                        # AI-Human meeting
                        # Human speaks first (M5.7 v2.0 SPEC 5.6).
                        # Avatar responds via _avatar_respond_to_message (triggered by
                        # send_meeting_message endpoint when human sends a message).
                        # No system-generated opening message.
                        pass

                await asyncio.sleep(MEETING_CHECK_INTERVAL)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("[meetings] Monitor error: %s", e)
                await asyncio.sleep(15)

    # -- Avatar meeting helpers --------------------------------------------

    async def _run_avatar_meeting(
        self, meeting_id: str, role_a: str, role_b: str,
        identity_a: str, identity_b: str,
        intent_a: str, intent_b: str, meeting: dict,
    ) -> None:
        """Run an avatar text meeting and handle cleanup.

        Called as a background task. Both agents are already IN_MEETING.
        """
        try:
            from engine.agents.managed.avatar_service import run_text_meeting
            from engine.services.meeting_service import save_transcript, end_meeting

            ctx_a = self.agents[role_a]
            ctx_b = self.agents[role_b]

            transcript = await run_text_meeting(
                meeting_id=meeting_id,
                agent_a_identity=identity_a,
                agent_a_intent=intent_a,
                agent_a_role_id=role_a,
                agent_a_country=ctx_a.country_code,
                agent_b_identity=identity_b,
                agent_b_intent=intent_b,
                agent_b_role_id=role_b,
                agent_b_country=ctx_b.country_code,
                sim_run_id=self.sim_run_id,
                round_num=ctx_a.round_num,
                max_turns=16,
            )

            # Save transcript and end meeting
            save_transcript(meeting_id, transcript)
            end_meeting(meeting_id, role_a)

            # Deliver transcript to both agents for reflection
            for role_id in (role_a, role_b):
                self.enqueue(
                    role_id=role_id,
                    tier=2,
                    event_type="meeting_transcript",
                    message=(
                        f"MEETING COMPLETED\n\nTranscript:\n{transcript}\n\n"
                        f"Review this conversation. Update your notes with key outcomes, "
                        f"commitments made, and intelligence gathered."
                    ),
                    metadata={"meeting_id": meeting_id},
                )

            logger.info("[meetings] Avatar meeting %s completed", meeting_id[:8])
        except Exception as e:
            logger.error("[meetings] Avatar meeting %s failed: %s", meeting_id[:8], e)
        finally:
            self.set_agent_state(role_a, IDLE)
            self.set_agent_state(role_b, IDLE)

    def _fetch_avatar_identity(self, role_id: str) -> str:
        """Read avatar_identity from agent_memories table.

        Returns the identity text, or a minimal fallback if not found.
        agent_memories is keyed by (sim_run_id, country_code, memory_key).
        """
        ctx = self.agents.get(role_id)
        country_code = ctx.country_code if ctx else role_id
        try:
            db = get_client()
            result = (
                db.table("agent_memories")
                .select("content")
                .eq("sim_run_id", self.sim_run_id)
                .eq("country_code", country_code)
                .eq("memory_key", "avatar_identity")
                .limit(1)
                .execute()
            )
            if result.data and result.data[0].get("content"):
                return result.data[0]["content"]
        except Exception as e:
            logger.warning("[meetings] Failed to fetch avatar identity for %s: %s", role_id, e)

        # Fallback: minimal identity from session context
        if ctx:
            return f"You are the leader of {ctx.country_code}. Role: {role_id}."
        return f"You are a head of state. Role: {role_id}."

    async def _check_and_deliver(self, max_tier: int) -> None:
        """Check queue for each idle agent and deliver events IN PARALLEL.

        All idle agents with pending events are processed concurrently
        via asyncio.gather(). Each agent has its own independent session —
        no shared state, no race conditions. State machine (IDLE → ACTING →
        IDLE) prevents double-delivery to the same agent.
        """
        # Collect all idle agents with pending events
        deliveries: list[tuple[str, SessionContext, list[dict]]] = []
        for role_id, ctx in list(self.agents.items()):
            state = self.agent_states.get(role_id, IDLE)
            if state != IDLE:
                continue

            events = await self.dequeue(role_id, max_tier=max_tier)
            if not events:
                continue

            deliveries.append((role_id, ctx, events))

        if not deliveries:
            return

        # Deliver to ALL idle agents in parallel
        async def _deliver_one(role_id: str, ctx: SessionContext, events: list[dict]) -> None:
            message = self._format_events(events)
            event_ids = [e["id"] for e in events]

            self.set_agent_state(role_id, ACTING)
            try:
                transcript = await self.session_manager.send_event(ctx, message)

                has_content = any(
                    e.get("type") in ("agent_message", "tool_call", "agent_thinking")
                    for e in transcript
                )
                if not has_content:
                    if ctx.events_sent >= 3 and ctx.total_output_tokens == 0:
                        logger.error(
                            "[dispatcher] Dead session for %s (sent=%d, tokens=0) — recreating",
                            role_id, ctx.events_sent,
                        )
                        try:
                            await self.session_manager.cleanup(ctx)
                            new_ctx = await self.session_manager.create_session(
                                role_id=role_id,
                                country_code=ctx.country_code,
                                sim_run_id=self.sim_run_id,
                                scenario_code=self.sim_run_id,
                                round_num=ctx.round_num,
                            )
                            self.agents[role_id] = new_ctx
                            logger.info("[dispatcher] Recreated session for %s", role_id)
                        except Exception as recreate_err:
                            logger.error("[dispatcher] Failed to recreate session for %s: %s", role_id, recreate_err)
                    else:
                        logger.warning(
                            "[dispatcher] Empty response from %s — will retry on next poll",
                            role_id,
                        )
                    return  # Do NOT mark processed — event stays in queue for retry

                await self.mark_processed(event_ids)

                from engine.agents.managed.event_handler import log_transcript_to_observatory
                log_transcript_to_observatory(
                    self.sim_run_id, ctx.country_code,
                    ctx.round_num, transcript,
                )

                # Avatar handles all meeting messages (M5.7).
                # Managed agent does NOT write to meeting_messages directly.

                self.session_manager._update_token_counts(ctx)

            except Exception as e:
                logger.error("[dispatcher] Delivery failed for %s: %s", role_id, e)
                await self.mark_processed(event_ids, error=str(e))
            finally:
                self.set_agent_state(role_id, IDLE)

        logger.info("[dispatcher] Delivering to %d agents in parallel", len(deliveries))
        await asyncio.gather(
            *[_deliver_one(rid, ctx, evts) for rid, ctx, evts in deliveries],
            return_exceptions=True,
        )

    def _format_events(self, events: list[dict]) -> str:
        """Format queued events into a single message for the agent."""
        if len(events) == 1:
            return events[0]["message"]

        # Multiple events — batch them
        lines = []
        for e in events:
            tier_label = {1: "CRITICAL", 2: "URGENT", 3: "UPDATE"}.get(e["tier"], "INFO")
            lines.append(f"[{tier_label}] {e['message']}")

        return (
            f"You have {len(events)} pending updates:\n\n"
            + "\n\n".join(lines)
            + "\n\nProcess these and respond."
        )

    # -- Status & helpers --------------------------------------------------

    async def get_status(self) -> dict:
        """Get all agent states, costs, queue depths, and activity summary.

        ASYNC — reads token counts and action counts from DB (survives restarts).
        Uses async client to avoid blocking the event loop.
        """
        db = await get_async_client()
        agents_status = []
        total_input_tokens = 0
        total_output_tokens = 0
        total_actions = 0
        total_tool_calls = 0

        for role_id, ctx in list(self.agents.items()):
            # Read from DB for accurate cross-session totals
            db_session = await (
                db.table("ai_agent_sessions")
                .select("total_input_tokens,total_output_tokens,events_sent,actions_submitted,tool_calls")
                .eq("sim_run_id", self.sim_run_id)
                .eq("role_id", role_id)
                .limit(1)
                .execute()
            )
            db_data = db_session.data[0] if db_session.data else {}

            inp = db_data.get("total_input_tokens", 0) or 0
            out = db_data.get("total_output_tokens", 0) or 0
            actions = db_data.get("actions_submitted", 0) or 0
            tools = db_data.get("tool_calls", 0) or 0
            events = db_data.get("events_sent", 0) or 0

            total_input_tokens += inp
            total_output_tokens += out
            total_actions += actions
            total_tool_calls += tools

            cost_usd = round(inp * 3.0 / 1_000_000 + out * 15.0 / 1_000_000, 4)
            queue = await self.get_queue_depth(role_id)

            agents_status.append({
                "role_id": role_id,
                "country_code": ctx.country_code,
                "state": self.agent_states.get(role_id, "UNKNOWN"),
                "session_id": ctx.session_id,
                "round_num": ctx.round_num,
                "actions_submitted": actions,
                "tool_calls": tools,
                "events_sent": events,
                "cost": {
                    "input_tokens": inp,
                    "output_tokens": out,
                    "total_cost_usd": cost_usd,
                },
                "queue_depth": queue,
            })

        total_cost = round(
            total_input_tokens * 3.0 / 1_000_000
            + total_output_tokens * 15.0 / 1_000_000, 2
        )

        # Get round info from sim_run
        run_data = await (
            db.table("sim_runs")
            .select("current_round")
            .eq("id", self.sim_run_id)
            .limit(1)
            .execute()
        )
        current_round = run_data.data[0]["current_round"] if run_data.data else 1

        return {
            "sim_run_id": self.sim_run_id,
            "round_num": current_round,
            "pulse_num": 0,
            "total_agents": len(self.agents),
            "agents_idle": sum(1 for s in self.agent_states.values() if s == IDLE),
            "agents_frozen": sum(1 for s in self.agent_states.values() if s == FROZEN),
            "agents_in_meeting": sum(
                1 for s in self.agent_states.values() if s == IN_MEETING
            ),
            "agents_acting": sum(
                1 for s in self.agent_states.values() if s == ACTING
            ),
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
            "total_cost_usd": total_cost,
            "total_actions": total_actions,
            "total_tool_calls": total_tool_calls,
            "agents": agents_status,
        }

    # -- Initialization ----------------------------------------------------

    async def initialize_agent(
        self,
        role_id: str,
        country_code: str,
        character_name: str,
        title: str,
        model: str | None = None,
        round_num: int = 1,
    ) -> SessionContext:
        """Create a managed agent session and register with dispatcher."""
        ctx = await self.session_manager.create_session(
            role_id=role_id,
            country_code=country_code,
            sim_run_id=self.sim_run_id,
            scenario_code=self.sim_run_id,
            round_num=round_num,
            model=model,
        )
        self.register_agent(role_id, ctx)

        # Enqueue init event (Tier 2 — picked up by dispatcher loop)
        self.enqueue(
            role_id=role_id,
            tier=2,
            event_type="initialization",
            message=(
                f"The simulation has begun. You are {character_name}, "
                f"{title} of {country_code}. "
                f"This is Round {round_num}. Assess your situation."
            ),
        )

        return ctx

    async def initialize_all_agents(
        self,
        role_ids: list[str] | None = None,
        model: str | None = None,
    ) -> dict:
        """Initialize all AI-operated agents for this sim_run.

        1. Clean up orphaned sessions from previous runs
        2. Load AI roles from DB
        3. Create Anthropic sessions (with semaphore for rate limiting)
        4. Register each with dispatcher
        5. Enqueue init message for each (Tier 2)

        The caller should call dispatcher.start() after this to begin
        delivering queued events.

        Args:
            role_ids: Specific roles to initialize. If None, loads all
                      AI-operated active roles from the roles table.
            model: Claude model ID.

        Returns:
            Summary: {agents_initialized, roles, errors}.
        """
        logger.info("[dispatcher] Initializing all AI agents for sim %s", self.sim_run_id)

        # Set initializing lock — prevents recovery from interfering (M4 SPEC 5.4)
        _initializing_sims.add(self.sim_run_id)

        # Clear any previously registered agents (e.g., from auto-reconnect of stale sessions)
        if self.agents:
            logger.info("[dispatcher] Clearing %d stale in-memory agents before fresh init", len(self.agents))
            self.agents.clear()
            self.agent_states.clear()

        db = await get_async_client()

        # Clean up orphaned sessions from previous runs
        old_sessions = await (
            db.table("ai_agent_sessions")
            .select("session_id,agent_id,role_id,status")
            .eq("sim_run_id", self.sim_run_id)
            .in_("status", ["initializing", "ready", "active", "frozen"])
            .execute()
        )
        if old_sessions.data:
            logger.info("[dispatcher] Archiving %d old sessions before fresh init", len(old_sessions.data))
            for old in old_sessions.data:
                try:
                    await self.session_manager.client.beta.sessions.archive(old["session_id"])
                except Exception:
                    pass
                try:
                    await self.session_manager.client.beta.agents.archive(old["agent_id"])
                except Exception:
                    pass
            await (
                db.table("ai_agent_sessions")
                .update({"status": "archived"})
                .eq("sim_run_id", self.sim_run_id)
                .in_("status", ["initializing", "ready", "active", "frozen"])
                .execute()
            )
            # Wait for Anthropic to fully process the archives
            await asyncio.sleep(3)

        # Load sim run info
        run_data = await (
            db.table("sim_runs")
            .select("scenario_id, current_round")
            .eq("id", self.sim_run_id)
            .limit(1)
            .execute()
        )
        if not run_data.data:
            return {"error": f"SimRun {self.sim_run_id} not found", "agents_initialized": 0}

        run = run_data.data[0]
        round_num = run.get("current_round", 1)

        # Load roles to initialize
        if role_ids:
            roles_data = await (
                db.table("roles")
                .select("id, country_code, character_name, title")
                .eq("sim_run_id", self.sim_run_id)
                .in_("id", role_ids)
                .execute()
            )
        else:
            roles_data = await (
                db.table("roles")
                .select("id, country_code, character_name, title, is_ai_operated")
                .eq("sim_run_id", self.sim_run_id)
                .eq("is_ai_operated", True)
                .eq("status", "active")
                .execute()
            )

        roles = roles_data.data or []
        if not roles:
            return {
                "agents_initialized": 0,
                "roles": [],
                "errors": ["No AI-operated roles found for this sim run"],
            }

        logger.info("[dispatcher] Found %d AI roles to initialize", len(roles))

        # Semaphore to limit concurrent session creation (API rate limit)
        # Keep at 2 to avoid Anthropic rate limits and session readiness issues
        sem = asyncio.Semaphore(2)
        initialized: list[dict] = []
        errors: list[str] = []

        async def _init_one(role: dict) -> None:
            role_id = role["id"]
            country_code = role["country_code"]
            character_name = role.get("character_name", role_id)
            title = role.get("title", "Leader")

            async with sem:
                # Small stagger to avoid hitting Anthropic API simultaneously
                await asyncio.sleep(1)
                try:
                    ctx = await self.session_manager.create_session(
                        role_id=role_id,
                        country_code=country_code,
                        sim_run_id=self.sim_run_id,
                        scenario_code=self.sim_run_id,
                        round_num=round_num,
                        model=model,
                    )
                    self.register_agent(role_id, ctx)

                    # Enqueue init event (Tier 2 — dispatcher loop delivers it)
                    self.enqueue(
                        role_id=role_id,
                        tier=2,
                        event_type="initialization",
                        message=(
                            f"The simulation is in PRE-START phase (Round {round_num}). You are {character_name}, "
                            f"{title} of {country_code}. "
                            f"EXPLORE ONLY — use observation tools (get_my_country, get_relationships, "
                            f"get_my_forces, get_all_countries, get_organizations) and write_notes to "
                            f"assess your situation and plan your strategy. "
                            f"Do NOT submit actions or request meetings — these are available once the round starts."
                        ),
                    )

                    initialized.append({
                        "role_id": role_id,
                        "country_code": country_code,
                        "session_id": ctx.session_id,
                    })
                    logger.info(
                        "[dispatcher] Initialized %s (%s) session=%s",
                        role_id, country_code, ctx.session_id,
                    )
                except Exception as e:
                    err = f"Failed to initialize {role_id}: {e}"
                    errors.append(err)
                    logger.error("[dispatcher] %s", err)

        # Run all initializations concurrently (bounded by semaphore)
        try:
            await asyncio.gather(*[_init_one(r) for r in roles])
        finally:
            # Clear initializing lock (M4 SPEC 5.4)
            _initializing_sims.discard(self.sim_run_id)

        summary = {
            "agents_initialized": len(initialized),
            "roles": initialized,
            "errors": errors,
            "round_num": round_num,
        }
        logger.info("[dispatcher] Initialization complete: %s", summary)
        return summary

    # -- Shutdown ----------------------------------------------------------

    # -- Country-level enqueue ---------------------------------------------

    def enqueue_for_country(
        self,
        country_code: str,
        tier: int,
        event_type: str,
        message: str,
        metadata: dict | None = None,
    ) -> str | None:
        """Enqueue an event for a country's HoS (if AI-operated).

        STAYS SYNC — called from sync action_dispatcher.
        Returns event ID if enqueued, None if no AI HoS found.
        """
        hos_role_id = _find_hos_for_country(self.sim_run_id, country_code)
        if not hos_role_id:
            return None
        return self.enqueue(
            role_id=hos_role_id,
            tier=tier,
            event_type=event_type,
            message=message,
            metadata=metadata,
        )

    # -- Round transition --------------------------------------------------

    def enqueue_round_results(self, round_num: int, results_by_country: dict) -> None:
        """Enqueue round results for all AI agents.

        STAYS SYNC — called by the engine after round processing completes.
        Each agent gets their country's results + public events.
        """
        for role_id, ctx in list(self.agents.items()):
            country_results = results_by_country.get(ctx.country_code, {})
            message = (
                f"Round {round_num} complete. Results for {ctx.country_code}: "
                f"{country_results}"
            )
            self.enqueue(
                role_id=role_id,
                tier=3,
                event_type="round_results",
                message=message,
                metadata={
                    "round_num": round_num,
                    "country_code": ctx.country_code,
                    "results": country_results,
                },
            )
        logger.info(
            "[dispatcher] Enqueued round %d results for %d agents",
            round_num, len(self.agents),
        )

    # -- Shutdown ----------------------------------------------------------

    # -- Phase B Solicitation ------------------------------------------------

    def _build_pulse_context(self, role_id: str, round_num: int,
                              pulse_num: int, total_pulses: int) -> str:
        """Build enriched per-pulse context: recent events + pending items + snapshot.

        Per M5 SPEC D4: each pulse contains public events, pending items,
        resource dashboard. Agents can use tools for full details.
        """
        db = get_client()
        ctx = self.agents.get(role_id)
        cc = ctx.country_code if ctx else ""
        lines: list[str] = []

        lines.append(f"Round {round_num}, Phase A — pulse {pulse_num}/{total_pulses}.")

        # Recent public events (last 5 since previous pulse)
        try:
            events = db.table("observatory_events") \
                .select("event_type,summary,country_code") \
                .eq("sim_run_id", self.sim_run_id) \
                .eq("round_num", round_num) \
                .neq("event_type", "ai_agent_log") \
                .order("created_at", desc=True).limit(5).execute().data or []
            if events:
                lines.append("\nRecent events:")
                for e in events:
                    lines.append(f"  - {(e.get('summary') or e.get('event_type', ''))[:80]}")
        except Exception:
            pass

        # Pending proposals (transactions/agreements awaiting response)
        try:
            pending_txns = db.table("exchange_transactions") \
                .select("id,proposer") \
                .eq("sim_run_id", self.sim_run_id) \
                .eq("counterpart", cc).eq("status", "pending").execute().data or []
            pending_agrs = db.table("agreements") \
                .select("id,proposer_country_code") \
                .eq("sim_run_id", self.sim_run_id) \
                .eq("status", "proposed") \
                .contains("signatories", [cc]).execute().data or []
            if pending_txns or pending_agrs:
                lines.append("\nPending items requiring your response:")
                for t in pending_txns:
                    lines.append(f"  - Transaction from {t['proposer']} (id: {t['id'][:8]})")
                for a in pending_agrs:
                    lines.append(f"  - Agreement from {a.get('proposer_country_code', '?')} (id: {a['id'][:8]})")
        except Exception:
            pass

        # Country snapshot (key numbers only — use tools for full details)
        try:
            country = db.table("countries") \
                .select("gdp,treasury,stability,inflation,nuclear_level,ai_level") \
                .eq("sim_run_id", self.sim_run_id).eq("id", cc).limit(1).execute()
            if country.data:
                c = country.data[0]
                lines.append(f"\nYour country snapshot: GDP ${c.get('gdp',0):.0f}B, "
                             f"treasury ${c.get('treasury',0):.1f}B, "
                             f"stability {c.get('stability',5):.1f}/10, "
                             f"inflation {c.get('inflation',0):.0f}%")
        except Exception:
            pass

        lines.append("\nAssess your situation and take strategic actions. "
                     "Use get_my_country, get_my_forces, get_relationships for full details.")

        return "\n".join(lines)

    def _build_batch_context(self, role_id: str, round_num: int) -> str:
        """Build enriched context for batch decision solicitation.

        Includes economic snapshot so agent can make informed budget decisions
        without needing a separate tool call.
        """
        db = get_client()
        ctx = self.agents.get(role_id)
        cc = ctx.country_code if ctx else ""
        lines: list[str] = []

        lines.append(f"ROUND {round_num} — SUBMIT YOUR BATCH DECISIONS NOW.\n")

        # Economic snapshot
        try:
            country = db.table("countries") \
                .select("gdp,treasury,stability,inflation,nuclear_level,ai_level,"
                        "mil_ground,mil_naval,mil_tactical_air,mil_strategic_missiles,mil_air_defense,"
                        "opec_member") \
                .eq("sim_run_id", self.sim_run_id).eq("id", cc).limit(1).execute()
            if country.data:
                c = country.data[0]
                lines.append("YOUR ECONOMIC STATE:")
                lines.append(f"  GDP: ${c.get('gdp',0):.1f}B | Treasury: ${c.get('treasury',0):.1f}B | "
                             f"Inflation: {c.get('inflation',0):.0f}% | Stability: {c.get('stability',5):.1f}/10")
                lines.append(f"  Military: {c.get('mil_ground',0)}G {c.get('mil_naval',0)}N "
                             f"{c.get('mil_tactical_air',0)}A {c.get('mil_strategic_missiles',0)}M "
                             f"{c.get('mil_air_defense',0)}AD")
                lines.append(f"  Nuclear L{c.get('nuclear_level',0)} | AI L{c.get('ai_level',0)}"
                             + (" | OPEC member" if c.get('opec_member') else ""))
                lines.append("")
        except Exception:
            pass

        lines.append("DECISIONS TO SUBMIT:")
        lines.append("1. set_budget — social_pct (0.5-1.5), production {branch: 0-4}, research {nuclear_coins, ai_coins}")
        lines.append("2. set_tariffs — target_country + level 0-3 (optional)")
        lines.append("3. set_sanctions — target_country + level -3 to +3 (optional)")
        lines.append("4. set_opec — production: min/low/normal/high/max (OPEC members only)")
        lines.append("")
        lines.append("Use get_my_country for full details. Submit each via submit_action. "
                     "You will NOT get another chance this round.")

        return "\n".join(lines)

    def sync_round_num(self, round_num: int) -> None:
        """Update round_num on all agent sessions + their ToolExecutors.

        Must be called whenever the sim advances rounds (start, advance_round).
        Without this, agents submit actions with stale round_num.
        """
        for role_id, ctx in self.agents.items():
            self.session_manager.update_round(ctx, round_num)
        logger.info("[dispatcher] Synced round_num=%d for %d agents", round_num, len(self.agents))

    async def solicit_batch_decisions(self, round_num: int, timeout_seconds: int = 120) -> dict:
        """Ask all AI agents to submit batch decisions (budget, tariffs, sanctions, OPEC).

        Called at the START of Phase B, BEFORE engine processing.
        Sends one event per agent and waits for all responses or timeout.

        Args:
            round_num: Current round number.
            timeout_seconds: Max wait time (default 2 minutes).

        Returns:
            Summary: {agents_asked, agents_responded, timed_out}.
        """
        # Sync round_num on all agents before soliciting
        self.sync_round_num(round_num)
        logger.info("[dispatcher] Soliciting batch decisions for round %d (timeout=%ds)", round_num, timeout_seconds)

        agents_asked = 0
        for role_id in list(self.agents.keys()):
            if self.agent_states.get(role_id) == FROZEN:
                continue
            try:
                message = self._build_batch_context(role_id, round_num)
            except Exception as ctx_err:
                logger.warning("[batch] Context build failed for %s: %s", role_id, ctx_err)
                message = (f"ROUND {round_num} — SUBMIT YOUR BATCH DECISIONS NOW.\n"
                           f"Submit set_budget, set_tariffs, set_sanctions, set_opec.")
            self.enqueue(
                role_id=role_id,
                tier=1,
                event_type="batch_decision_request",
                message=message,
                metadata={"round_num": round_num, "solicitation_type": "batch_decisions"},
            )
            agents_asked += 1

        # Phase 1: Wait for agents to START processing (leave IDLE → ACTING)
        # The enqueue writes to DB; the dispatch loop delivers on next cycle.
        # We must yield control so the dispatch loop can run.
        start = asyncio.get_event_loop().time()
        agents_started = False
        while asyncio.get_event_loop().time() - start < 30:  # 30s max to start
            await asyncio.sleep(3)  # Let dispatch loop deliver events
            busy = sum(1 for rid in self.agents if self.agent_states.get(rid) not in (IDLE, FROZEN))
            if busy > 0:
                agents_started = True
                logger.info("[dispatcher] Batch solicitation: %d agents now processing", busy)
                break

        if not agents_started:
            logger.warning("[dispatcher] Batch solicitation: no agents started processing within 30s")

        # Phase 2: Wait for all agents to FINISH (return to IDLE)
        agents_responded = 0
        while asyncio.get_event_loop().time() - start < timeout_seconds:
            busy = sum(1 for rid in self.agents if self.agent_states.get(rid) not in (IDLE, FROZEN))
            if busy == 0 and agents_started:
                agents_responded = agents_asked
                break
            await asyncio.sleep(5)

        timed_out = agents_responded < agents_asked
        logger.info(
            "[dispatcher] Batch decisions: asked=%d, responded=%d, timed_out=%s, started=%s",
            agents_asked, agents_responded, timed_out, agents_started,
        )
        return {"agents_asked": agents_asked, "agents_responded": agents_responded, "timed_out": timed_out}

    async def solicit_troop_movements(self, round_num: int, timeout_seconds: int = 120) -> dict:
        """Ask all AI agents to submit troop movements (move_units).

        Called AFTER engine processing, before Phase B completes.
        Sends one event per agent and waits for all responses or timeout.
        """
        self.sync_round_num(round_num)
        logger.info("[dispatcher] Soliciting troop movements for round %d (timeout=%ds)", round_num, timeout_seconds)

        agents_asked = 0
        for role_id in list(self.agents.keys()):
            if self.agent_states.get(role_id) == FROZEN:
                continue
            self.enqueue(
                role_id=role_id,
                tier=1,
                event_type="movement_request",
                message=(
                    f"ROUND {round_num} — SUBMIT TROOP MOVEMENTS NOW.\n\n"
                    f"The round engines have processed. Review updated world state with get_my_country.\n"
                    f"This is your ONE opportunity to reposition forces using move_units.\n"
                    f"You can: deploy from reserve, withdraw to reserve, reposition between hexes.\n"
                    f"If no movement needed, do nothing — your forces stay in place."
                ),
                metadata={"round_num": round_num, "solicitation_type": "troop_movements"},
            )
            agents_asked += 1

        # Phase 1: Wait for agents to START processing
        start = asyncio.get_event_loop().time()
        agents_started = False
        while asyncio.get_event_loop().time() - start < 30:
            await asyncio.sleep(3)
            busy = sum(1 for rid in self.agents if self.agent_states.get(rid) not in (IDLE, FROZEN))
            if busy > 0:
                agents_started = True
                break

        # Phase 2: Wait for all agents to FINISH
        agents_responded = 0
        while asyncio.get_event_loop().time() - start < timeout_seconds:
            busy = sum(1 for rid in self.agents if self.agent_states.get(rid) not in (IDLE, FROZEN))
            if busy == 0 and agents_started:
                agents_responded = agents_asked
                break
            await asyncio.sleep(5)

        timed_out = agents_responded < agents_asked
        logger.info(
            "[dispatcher] Troop movements: asked=%d, responded=%d, timed_out=%s",
            agents_asked, agents_responded, timed_out,
        )
        return {"agents_asked": agents_asked, "agents_responded": agents_responded, "timed_out": timed_out}

    # -- Shutdown ----------------------------------------------------------

    async def shutdown(self) -> None:
        """Stop dispatcher, archive all sessions, clear queue."""
        await self.stop()

        for role_id, ctx in list(self.agents.items()):
            try:
                await self.session_manager.cleanup(ctx)
            except Exception as e:
                logger.warning("[dispatcher] Cleanup failed for %s: %s", role_id, e)

        await self.clear_queue()
        self.agents.clear()
        self.agent_states.clear()
        logger.info("[dispatcher] Shutdown complete for sim %s", self.sim_run_id)


# -- SIM lifecycle: cleanup on restart -------------------------------------

async def cleanup_sim_ai_state(
    sim_run_id: str,
    clear_memories: bool = False,
    clear_decisions: bool = False,
) -> dict:
    """Clean up ALL AI state for a sim_run. Called on SIM restart.

    ASYNC — uses async Supabase client for all DB operations.

    1. Stop dispatcher if running
    2. Archive all Anthropic sessions
    3. Set ai_agent_sessions status='archived'
    4. Clear unprocessed events from agent_event_queue
    5. Optionally clear agent_memories (configurable)
    6. Optionally clear agent_decisions (configurable)

    Returns summary of what was cleaned.
    """
    summary: dict = {
        "sim_run_id": sim_run_id,
        "dispatcher_stopped": False,
        "sessions_archived": 0,
        "db_sessions_archived": 0,
        "events_cleared": 0,
        "memories_cleared": 0,
        "decisions_cleared": 0,
    }

    # 1. Stop dispatcher if running
    dispatcher = get_dispatcher(sim_run_id)
    if dispatcher:
        await dispatcher.shutdown()
        remove_dispatcher(sim_run_id)
        summary["dispatcher_stopped"] = True
        summary["sessions_archived"] = len(dispatcher.agents)
        logger.info("[cleanup] Dispatcher stopped and sessions archived for sim %s", sim_run_id)

    # 2+3. Archive any remaining DB sessions that weren't handled by dispatcher
    db = await get_async_client()
    try:
        active = await (
            db.table("ai_agent_sessions")
            .select("id, session_id, agent_id, role_id")
            .eq("sim_run_id", sim_run_id)
            .in_("status", ["initializing", "ready", "active", "frozen"])
            .execute()
        )
        if active.data:
            # Archive via Anthropic API (best-effort)
            from anthropic import AsyncAnthropic
            try:
                from engine.config import settings
                api_key = settings.anthropic_api_key or None
            except Exception:
                api_key = None
            client = AsyncAnthropic(api_key=api_key)

            for s in active.data:
                try:
                    await client.beta.sessions.archive(s["session_id"])
                except Exception as e:
                    logger.warning("[cleanup] Failed to archive Anthropic session %s: %s", s["session_id"], e)
                try:
                    await client.beta.agents.archive(s["agent_id"])
                except Exception as e:
                    logger.warning("[cleanup] Failed to archive Anthropic agent %s: %s", s["agent_id"], e)

            # Update DB status
            await (
                db.table("ai_agent_sessions")
                .update({"status": "archived"})
                .eq("sim_run_id", sim_run_id)
                .in_("status", ["initializing", "ready", "active", "frozen"])
                .execute()
            )
            summary["db_sessions_archived"] = len(active.data)
            logger.info("[cleanup] Archived %d DB sessions", len(active.data))
    except Exception as e:
        logger.error("[cleanup] Failed to archive DB sessions: %s", e)

    # 4. Clear ALL events (processed and unprocessed) — clean slate on restart
    try:
        result = await (
            db.table("agent_event_queue")
            .delete()
            .eq("sim_run_id", sim_run_id)
            .execute()
        )
        summary["events_cleared"] = len(result.data or [])
        logger.info("[cleanup] Cleared %d events (all)", summary["events_cleared"])
    except Exception as e:
        logger.error("[cleanup] Failed to clear event queue: %s", e)

    # 4a. Clear observatory AI agent logs
    try:
        result = await (
            db.table("observatory_events")
            .delete()
            .eq("sim_run_id", sim_run_id)
            .eq("event_type", "ai_agent_log")
            .execute()
        )
        summary["observatory_events_cleared"] = len(result.data or [])
        logger.info("[cleanup] Cleared %d observatory AI logs", summary["observatory_events_cleared"])
    except Exception as e:
        logger.error("[cleanup] Failed to clear observatory events: %s", e)

    # 4b. Clear meetings and meeting messages
    try:
        # Delete messages first (FK constraint)
        meeting_ids = await (
            db.table("meetings")
            .select("id")
            .eq("sim_run_id", sim_run_id)
            .execute()
        )
        mid_list = [m["id"] for m in (meeting_ids.data or [])]
        msgs_cleared = 0
        for mid in mid_list:
            r = await db.table("meeting_messages").delete().eq("meeting_id", mid).execute()
            msgs_cleared += len(r.data or [])
        # Then delete meetings
        r = await db.table("meetings").delete().eq("sim_run_id", sim_run_id).execute()
        meetings_cleared = len(r.data or [])
        # Clear invitations too
        r = await db.table("meeting_invitations").delete().eq("sim_run_id", sim_run_id).execute()
        invitations_cleared = len(r.data or [])
        summary["meetings_cleared"] = meetings_cleared
        summary["meeting_messages_cleared"] = msgs_cleared
        summary["invitations_cleared"] = invitations_cleared
        logger.info("[cleanup] Cleared %d meetings, %d messages, %d invitations",
                    meetings_cleared, msgs_cleared, invitations_cleared)
    except Exception as e:
        logger.error("[cleanup] Failed to clear meetings: %s", e)

    # 5. Optionally clear agent_memories
    if clear_memories:
        try:
            result = await (
                db.table("agent_memories")
                .delete()
                .eq("sim_run_id", sim_run_id)
                .execute()
            )
            summary["memories_cleared"] = len(result.data or [])
            logger.info("[cleanup] Cleared %d agent memories", summary["memories_cleared"])
        except Exception as e:
            logger.error("[cleanup] Failed to clear memories: %s", e)

    # 6. Optionally clear agent_decisions
    if clear_decisions:
        try:
            result = await (
                db.table("agent_decisions")
                .delete()
                .eq("sim_run_id", sim_run_id)
                .execute()
            )
            summary["decisions_cleared"] = len(result.data or [])
            logger.info("[cleanup] Cleared %d agent decisions", summary["decisions_cleared"])
        except Exception as e:
            logger.error("[cleanup] Failed to clear decisions: %s", e)

    logger.info("[cleanup] AI state cleanup complete for sim %s: %s", sim_run_id, summary)
    return summary


# -- Helper: find HoS role for a country -----------------------------------

def _find_hos_for_country(sim_run_id: str, country_code: str) -> str | None:
    """Find the AI-operated Head of State role_id for a country.

    STAYS SYNC — called from sync enqueue_for_country (action_dispatcher context).
    """
    try:
        db = get_client()
        result = (
            db.table("roles")
            .select("id, is_ai_operated, positions")
            .eq("sim_run_id", sim_run_id)
            .eq("country_code", country_code)
            .eq("status", "active")
            .execute()
        )
        for role in result.data or []:
            positions = role.get("positions") or []
            if "head_of_state" in positions:
                return role["id"] if role.get("is_ai_operated") else None
        return None
    except Exception as e:
        logger.warning("[dispatcher] Failed to find HoS for %s: %s", country_code, e)
        return None


# -- Global dispatcher registry -------------------------------------------
_dispatchers: dict[str, EventDispatcher] = {}
_initializing_sims: set[str] = set()  # sims currently being initialized (blocks recovery)


def get_dispatcher(sim_run_id: str) -> EventDispatcher | None:
    """Get the dispatcher for a sim run, or None if not running."""
    return _dispatchers.get(sim_run_id)


def is_initializing(sim_run_id: str) -> bool:
    """Check if a sim is currently being initialized (blocks recovery)."""
    return sim_run_id in _initializing_sims


def create_dispatcher(sim_run_id: str) -> EventDispatcher:
    """Create and register a new dispatcher for a sim run."""
    d = EventDispatcher(sim_run_id)
    _dispatchers[sim_run_id] = d
    return d


def remove_dispatcher(sim_run_id: str) -> None:
    """Remove a dispatcher from the registry."""
    _dispatchers.pop(sim_run_id, None)
