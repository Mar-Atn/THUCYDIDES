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
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from engine.agents.managed.session_manager import ManagedSessionManager, SessionContext
from engine.agents.managed.tool_executor import ToolExecutor
from engine.services.supabase import get_client

logger = logging.getLogger(__name__)

# Tier check intervals (seconds)
TIER_1_INTERVAL = 3
TIER_2_INTERVAL = 5
TIER_3_INTERVAL = 30  # Configurable per sim

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
        self._running = False
        self._tasks: list[asyncio.Task] = []

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

    def dequeue(self, role_id: str, max_tier: int = 3) -> list[dict]:
        """Get all unprocessed events for a role, up to max_tier.

        Returns events ordered by tier (critical first), then created_at.
        """
        db = get_client()
        result = (
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

    def mark_processed(self, event_ids: list[str], error: str | None = None) -> None:
        """Mark events as processed (or failed)."""
        if not event_ids:
            return
        db = get_client()
        update: dict = {"processed_at": datetime.now(timezone.utc).isoformat()}
        if error:
            update["processing_error"] = error
        for eid in event_ids:
            db.table("agent_event_queue").update(update).eq("id", eid).execute()

    def get_queue_depth(self, role_id: str) -> dict:
        """Get count of unprocessed events by tier for a role."""
        db = get_client()
        events = (
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

    def clear_queue(self, role_id: str | None = None) -> int:
        """Clear unprocessed events. If role_id given, clear only for that role."""
        db = get_client()
        query = (
            db.table("agent_event_queue")
            .delete()
            .eq("sim_run_id", self.sim_run_id)
            .is_("processed_at", "null")
        )
        if role_id:
            query = query.eq("role_id", role_id)
        result = query.execute()
        count = len(result.data or [])
        logger.info("[dispatcher] Cleared %d queued events (role=%s)", count, role_id or "ALL")
        return count

    # -- Agent Registration ------------------------------------------------

    def register_agent(self, role_id: str, ctx: SessionContext) -> None:
        """Register an agent with the dispatcher."""
        self.agents[role_id] = ctx
        self.agent_states[role_id] = IDLE
        logger.info("[dispatcher] Registered agent %s", role_id)

    def set_agent_state(self, role_id: str, state: str) -> None:
        """Update agent state (IDLE, ACTING, IN_MEETING, FROZEN)."""
        old = self.agent_states.get(role_id)
        self.agent_states[role_id] = state
        if old != state:
            logger.info("[dispatcher] Agent %s: %s -> %s", role_id, old, state)

    # -- Dispatch Loop -----------------------------------------------------

    async def start(self) -> None:
        """Start the dispatch loop (background task)."""
        self._running = True
        self._tasks.append(asyncio.create_task(self._dispatch_loop()))
        logger.info(
            "[dispatcher] Started for sim %s with %d agents",
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

                await asyncio.sleep(1)  # Base check interval

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("[dispatcher] Loop error: %s", e)
                await asyncio.sleep(5)  # Back off on error

    async def _check_and_deliver(self, max_tier: int) -> None:
        """Check queue for each idle agent and deliver events."""
        for role_id, ctx in self.agents.items():
            state = self.agent_states.get(role_id, IDLE)

            if state != IDLE:
                continue  # Skip busy/frozen agents

            events = self.dequeue(role_id, max_tier=max_tier)
            if not events:
                continue

            # Build combined message from queued events
            message = self._format_events(events)
            event_ids = [e["id"] for e in events]

            # Deliver
            self.set_agent_state(role_id, ACTING)
            try:
                transcript = await self.session_manager.send_event(ctx, message)
                self.mark_processed(event_ids)

                # Log to observatory
                from engine.agents.managed.event_handler import log_transcript_to_observatory
                log_transcript_to_observatory(
                    self.sim_run_id, ctx.country_code,
                    ctx.round_num, transcript,
                )

                # Handle chat_message events — write AI response to meeting_messages
                for ev in events:
                    if ev["event_type"] == "chat_message":
                        meeting_id = (ev.get("metadata") or {}).get("meeting_id")
                        if meeting_id and transcript:
                            self._write_chat_response(role_id, meeting_id, transcript)

                # Update DB session stats
                self.session_manager._update_token_counts(ctx)

            except Exception as e:
                logger.error("[dispatcher] Delivery failed for %s: %s", role_id, e)
                self.mark_processed(event_ids, error=str(e))
            finally:
                self.set_agent_state(role_id, IDLE)

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

    # -- Chat response writeback -------------------------------------------

    def _write_chat_response(
        self, role_id: str, meeting_id: str, transcript: list[dict]
    ) -> None:
        """Write AI agent's chat response to meeting_messages.

        After the dispatcher delivers a chat_message event, the agent may
        respond with text. If the agent didn't explicitly use the send_message
        tool, we extract the first agent_message from the transcript and
        write it as a meeting message.
        """
        # Check if agent already used send_message tool
        used_send_message = any(
            e.get("type") == "tool_call" and e.get("tool") == "send_message"
            for e in transcript
        )
        if used_send_message:
            return  # Agent handled it

        from engine.services.meeting_service import send_message

        for entry in transcript:
            if entry.get("type") == "agent_message" and entry.get("content"):
                text = entry["content"].strip()
                if text and len(text) > 3:
                    ctx = self.agents.get(role_id)
                    if ctx:
                        send_message(meeting_id, role_id, ctx.country_code, text[:500])
                    break

    # -- Status & helpers --------------------------------------------------

    def get_status(self) -> dict:
        """Get all agent states, costs, queue depths, and activity summary."""
        agents_status = []
        total_input_tokens = 0
        total_output_tokens = 0

        for role_id, ctx in self.agents.items():
            cost = self.session_manager.get_cost_estimate(ctx)
            queue = self.get_queue_depth(role_id)

            total_input_tokens += cost.get("input_tokens", 0)
            total_output_tokens += cost.get("output_tokens", 0)

            agents_status.append({
                "role_id": role_id,
                "country_code": ctx.country_code,
                "state": self.agent_states.get(role_id, "UNKNOWN"),
                "session_id": ctx.session_id,
                "round_num": ctx.round_num,
                "cost": cost,
                "queue_depth": queue,
            })

        total_cost = (
            (total_input_tokens * 3.0 / 1_000_000)
            + (total_output_tokens * 15.0 / 1_000_000)
        )

        return {
            "sim_run_id": self.sim_run_id,
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
            "total_cost_usd": round(total_cost, 2),
            "agents": agents_status,
        }

    # -- Initialization ----------------------------------------------------

    async def initialize_agent(
        self,
        role_id: str,
        country_code: str,
        character_name: str,
        title: str,
        model: str = "claude-sonnet-4-6",
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

    # -- Reconnect from DB -------------------------------------------------

    async def reconnect_from_db(self) -> int:
        """Rebuild dispatcher state from DB sessions after backend restart."""
        db = get_client()
        sessions = (
            db.table("ai_agent_sessions")
            .select("*")
            .eq("sim_run_id", self.sim_run_id)
            .in_("status", ["initializing", "ready", "active"])
            .execute()
        )

        count = 0
        for s in sessions.data or []:
            role_id = s["role_id"]
            executor = ToolExecutor(
                country_code=s["country_code"],
                scenario_code=self.sim_run_id,
                sim_run_id=self.sim_run_id,
                round_num=s.get("round_num", 1),
                role_id=role_id,
            )
            ctx = SessionContext(
                agent_id=s["agent_id"],
                agent_version=1,
                environment_id=s["environment_id"],
                session_id=s["session_id"],
                role_id=role_id,
                country_code=s["country_code"],
                sim_run_id=self.sim_run_id,
                scenario_code=self.sim_run_id,
                model=s.get("model", "claude-sonnet-4-6"),
                round_num=s.get("round_num", 1),
                tool_executor=executor,
                total_input_tokens=s.get("total_input_tokens", 0),
                total_output_tokens=s.get("total_output_tokens", 0),
                events_sent=s.get("events_sent", 0),
                actions_submitted=s.get("actions_submitted", 0),
                tool_calls=s.get("tool_calls", 0),
            )
            self.register_agent(role_id, ctx)
            count += 1

        logger.info("[dispatcher] Reconnected %d agents from DB", count)
        return count

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

    # -- Shutdown ----------------------------------------------------------

    async def shutdown(self) -> None:
        """Stop dispatcher, archive all sessions, clear queue."""
        await self.stop()

        for role_id, ctx in self.agents.items():
            try:
                await self.session_manager.cleanup(ctx)
            except Exception as e:
                logger.warning("[dispatcher] Cleanup failed for %s: %s", role_id, e)

        self.clear_queue()
        self.agents.clear()
        self.agent_states.clear()
        logger.info("[dispatcher] Shutdown complete for sim %s", self.sim_run_id)


# -- Helper: find HoS role for a country -----------------------------------

def _find_hos_for_country(sim_run_id: str, country_code: str) -> str | None:
    """Find the AI-operated Head of State role_id for a country."""
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


def get_dispatcher(sim_run_id: str) -> EventDispatcher | None:
    """Get the dispatcher for a sim run, or None if not running."""
    return _dispatchers.get(sim_run_id)


def create_dispatcher(sim_run_id: str) -> EventDispatcher:
    """Create and register a new dispatcher for a sim run."""
    d = EventDispatcher(sim_run_id)
    _dispatchers[sim_run_id] = d
    return d


def remove_dispatcher(sim_run_id: str) -> None:
    """Remove a dispatcher from the registry."""
    _dispatchers.pop(sim_run_id, None)
