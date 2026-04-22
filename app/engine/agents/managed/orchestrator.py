"""Phase 2 — AI Orchestrator: manages all AI participants in a simulation.

Coordinates session lifecycle, pulse scheduling, event batching, busy state,
parallel agent execution, round transitions, and cost tracking for 1-40 AI
agents. The orchestrator is INVISIBLE to agents — it provides context and
lets each agent decide autonomously.

Key responsibilities:
  1. Initialize all AI agents for a sim_run
  2. Run rounds — send N pulses to all agents in parallel
  3. Batch events — gather observatory events, categorize public/private
  4. Build pulse messages — events + resource dashboard + meta context
  5. Manage agent states — IDLE, ACTING, IN_MEETING, FROZEN
  6. Handle critical interrupts — nuclear, direct attack bypass schedule
  7. Enforce timing — pulse intervals from round duration
  8. Between-round transitions — results summary, reflection
  9. Auto-advance (co-moderator mode) — unmanned testing
  10. Track costs — aggregate token usage across all agents

Dependencies: session_manager (Phase 1C), meta_context, event_handler.
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from engine.agents.managed.conversations import ConversationRouter
from engine.agents.managed.event_handler import (
    log_transcript_to_observatory,
    write_agent_log_event,
    extract_actions_from_transcript,
)
from engine.agents.managed.meta_context import build_meta_context
from engine.agents.managed.session_manager import ManagedSessionManager, SessionContext
from engine.services.supabase import get_client

logger = logging.getLogger(__name__)

# ── Agent states ─────────────────────────────────────────────────────
IDLE = "IDLE"
ACTING = "ACTING"
IN_MEETING = "IN_MEETING"
FROZEN = "FROZEN"

VALID_STATES = {IDLE, ACTING, IN_MEETING, FROZEN}

# ── Critical event types that bypass pulse schedule ──────────────────
CRITICAL_EVENT_TYPES = {
    "nuclear_launch",
    "direct_attack",
    "leader_incapacitated",
    "territory_invaded",
}


@dataclass
class OrchestratorConfig:
    """Global AI configuration (from SPEC section 7)."""

    assertiveness: int = 5  # 1=cooperative, 10=assertive
    pulses_per_round: int = 8  # 1-20, recommended 5-10
    max_meetings_per_round: int = 5
    max_lookups_per_pulse: int = 10
    max_turns_per_meeting: int = 8  # per side (16 total)
    model: str = "claude-sonnet-4-6"
    auto_advance: bool = False  # co-moderator mode for testing
    round_duration_seconds: int = 300  # 5 min default for unmanned
    total_rounds: int = 6


@dataclass
class AgentRoundStats:
    """Per-agent stats accumulated during a round."""

    actions_submitted: int = 0
    tool_calls: int = 0
    meetings_used: int = 0
    pulses_received: int = 0
    errors: int = 0


class AIOrchestrator:
    """Orchestrates all AI participants in a simulation.

    Manages session lifecycle, pulse scheduling, event batching,
    busy state, and round transitions for 1-40 AI agents.
    """

    def __init__(self, sim_run_id: str, config: OrchestratorConfig | None = None):
        self.sim_run_id = sim_run_id
        self.config = config or OrchestratorConfig()
        self.session_manager = ManagedSessionManager()
        self.conversation_router = ConversationRouter(self.session_manager, sim_run_id)
        self.agents: dict[str, SessionContext] = {}  # role_id -> session
        self.agent_states: dict[str, str] = {}  # role_id -> IDLE|ACTING|IN_MEETING|FROZEN
        self.round_num: int = 1
        self.pulse_num: int = 0
        self.round_stats: dict[str, AgentRoundStats] = {}  # role_id -> stats
        self._last_pulse_time: str | None = None
        self._queued_events: dict[str, list[dict]] = {}  # role_id -> events queued while busy
        self._scenario_code: str = ""
        self._initialized: bool = False

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    async def initialize_agents(
        self, role_ids: list[str] | None = None
    ) -> dict:
        """Initialize all AI-operated agents for the sim run.

        Args:
            role_ids: Specific roles to initialize. If None, loads all
                      AI-operated roles from the roles table.

        Returns:
            Status summary: {agents_initialized, roles, errors}.
        """
        logger.info("Initializing AI agents for sim %s", self.sim_run_id)

        # Load sim run info
        db = get_client()
        run_data = (
            db.table("sim_runs")
            .select("scenario_id, current_round")
            .eq("id", self.sim_run_id)
            .limit(1)
            .execute()
        )
        if not run_data.data:
            return {"error": f"SimRun {self.sim_run_id} not found", "agents_initialized": 0}

        run = run_data.data[0]
        # scenario_code for tools.py — use sim_run_id directly (resolves via sim_run_manager)
        self._scenario_code = self.sim_run_id
        self.round_num = run.get("current_round", 1)

        # Load roles to initialize
        if role_ids:
            roles_data = (
                db.table("roles")
                .select("id, country_code, character_name, title")
                .eq("sim_run_id", self.sim_run_id)
                .in_("id", role_ids)
                .execute()
            )
        else:
            # Get all ACTIVE AI-operated roles (exclude inactive from reduced templates)
            roles_data = (
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

        logger.info("Found %d AI roles to initialize", len(roles))

        initialized = []
        errors = []

        async def _init_one_agent(role: dict) -> dict:
            """Initialize a single agent — runs in thread pool (sync SDK)."""
            role_id = role["id"]
            country_code = role["country_code"]
            character_name = role.get("character_name", role_id)
            title = role.get("title", "Leader")

            loop = asyncio.get_event_loop()

            # Create managed agent session (sync → thread)
            ctx = await loop.run_in_executor(
                None,
                lambda: self.session_manager.create_session(
                    role_id=role_id,
                    country_code=country_code,
                    sim_run_id=self.sim_run_id,
                    scenario_code=self._scenario_code,
                    round_num=self.round_num,
                    model=self.config.model,
                ),
            )

            self.agents[role_id] = ctx
            self.agent_states[role_id] = IDLE
            self.round_stats[role_id] = AgentRoundStats()
            self._queued_events[role_id] = []

            # Send initialization message (sync → thread)
            init_msg = (
                f"The simulation has begun. You are {character_name}, "
                f"{title} of {country_code}. "
                f"This is Round {self.round_num}. Assess your situation."
            )
            transcript = await loop.run_in_executor(
                None, self.session_manager.send_event, ctx, init_msg
            )

            # Log initialization to observatory
            log_transcript_to_observatory(
                self.sim_run_id, country_code, self.round_num, transcript
            )

            logger.info(
                "Initialized agent: %s (%s) session=%s",
                role_id, country_code, ctx.session_id,
            )
            return {
                "role_id": role_id,
                "country_code": country_code,
                "character_name": character_name,
                "session_id": ctx.session_id,
                "status": "ready",
            }

        # Initialize agents with limited concurrency (max 2 at a time).
        # macOS has tight thread limits — [Errno 35] Resource temporarily
        # unavailable with 3+ concurrent run_in_executor calls.
        sem = asyncio.Semaphore(2)

        async def _init_with_semaphore(role: dict) -> dict:
            async with sem:
                await asyncio.sleep(0.5)  # Brief stagger to avoid thread exhaustion
                return await _init_one_agent(role)

        results = await asyncio.gather(
            *[_init_with_semaphore(r) for r in roles], return_exceptions=True
        )

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                role_id = roles[i]["id"]
                logger.exception("Failed to initialize agent %s: %s", role_id, result)
                errors.append({"role_id": role_id, "error": str(result)})
            else:
                initialized.append(result)

        self._initialized = True

        write_agent_log_event(
            self.sim_run_id, "", self.round_num,
            event_type="orchestrator",
            title="AI Agents Initialized",
            description=(
                f"{len(initialized)} agents initialized, {len(errors)} errors"
            ),
            metadata={"initialized": [a.get("role_id") or a.get("id") for a in initialized], "errors": errors},
        )

        return {
            "agents_initialized": len(initialized),
            "roles": initialized,
            "errors": errors,
        }

    # ------------------------------------------------------------------
    # Round execution
    # ------------------------------------------------------------------

    async def run_round(self, round_num: int) -> dict:
        """Run a complete round — all pulses for all agents.

        Args:
            round_num: The round number to run.

        Returns:
            Round summary: actions per agent, costs, meetings, errors.
        """
        self.round_num = round_num
        self.pulse_num = 0
        pulse_interval = self.config.round_duration_seconds / self.config.pulses_per_round

        # Reset round stats
        for role_id in self.agents:
            self.round_stats[role_id] = AgentRoundStats()
            self.session_manager.update_round(self.agents[role_id], round_num)

        logger.info(
            "Starting round %d for %d agents (%d pulses, %.1fs interval)",
            round_num, len(self.agents), self.config.pulses_per_round, pulse_interval,
        )

        write_agent_log_event(
            self.sim_run_id, "", round_num,
            event_type="orchestrator",
            title=f"Round {round_num} Started",
            description=(
                f"{len(self.agents)} agents, {self.config.pulses_per_round} pulses, "
                f"{self.config.round_duration_seconds}s duration"
            ),
        )

        pulse_results = []
        meeting_results = []

        for pulse in range(1, self.config.pulses_per_round + 1):
            pulse_result = await self.send_pulse(pulse)
            pulse_results.append(pulse_result)

            # After each pulse, check for and run accepted meetings
            mtg_results = await self._process_meetings()
            if mtg_results:
                meeting_results.extend(mtg_results)

            # Auto-advance: wait between pulses
            if self.config.auto_advance and pulse < self.config.pulses_per_round:
                await asyncio.sleep(pulse_interval)

        # After all pulses: send mandatory input reminder to agents
        # that have unsubmitted mandatory inputs
        await self._send_mandatory_reminders()

        summary = self.get_round_summary()

        write_agent_log_event(
            self.sim_run_id, "", round_num,
            event_type="orchestrator",
            title=f"Round {round_num} Complete",
            description=(
                f"Total actions: {summary['total_actions']}, "
                f"Total cost: ${summary['total_cost_usd']:.2f}"
            ),
            metadata=summary,
        )

        return summary

    # ------------------------------------------------------------------
    # Pulse dispatch
    # ------------------------------------------------------------------

    async def send_pulse(self, pulse_num: int) -> dict:
        """Send a single pulse to all eligible agents in parallel.

        For each agent not FROZEN and not IN_MEETING:
          - Build pulse message with batched events + meta context
          - Send to agent session
          - Process response (actions, tool calls, meeting requests)
          - Log to observatory

        Args:
            pulse_num: Pulse number within the current round (1-indexed).

        Returns:
            Pulse summary: {pulse_num, agents_pulsed, actions, errors}.
        """
        self.pulse_num = pulse_num
        now_iso = datetime.now(timezone.utc).isoformat()

        logger.info(
            "Pulse %d/%d for round %d — %d agents",
            pulse_num, self.config.pulses_per_round, self.round_num, len(self.agents),
        )

        # Collect events since last pulse
        events_by_role = {}
        for role_id, ctx in self.agents.items():
            state = self.agent_states.get(role_id, IDLE)
            if state == FROZEN:
                continue
            events_by_role[role_id] = await self._collect_events_for_agent(
                role_id, ctx.country_code
            )

        # Build and send pulse to eligible agents in parallel
        tasks = []
        pulsed_roles = []

        for role_id, ctx in self.agents.items():
            state = self.agent_states.get(role_id, IDLE)

            if state == FROZEN:
                continue

            if state == IN_MEETING:
                # Queue events for delivery when meeting ends
                role_events = events_by_role.get(role_id, {})
                queued = self._queued_events.setdefault(role_id, [])
                for evt in role_events.get("public", []):
                    queued.append(evt)
                for evt in role_events.get("private", []):
                    queued.append(evt)
                continue

            # Health check before pulse
            health = self.session_manager.health_check(ctx)
            if health == "terminated":
                logger.warning("Session terminated for %s, recovering...", role_id)
                try:
                    new_ctx = self.session_manager.recover_session(ctx)
                    self.agents[role_id] = new_ctx
                    ctx = new_ctx
                except Exception as e:
                    logger.error("Recovery failed for %s: %s", role_id, e)
                    self.round_stats[role_id].errors += 1
                    continue

            pulsed_roles.append(role_id)
            events = events_by_role.get(role_id, {})
            tasks.append(self._pulse_single_agent(role_id, ctx, pulse_num, events))

        # Execute all agent pulses in parallel
        results = []
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        pulse_summary = {
            "pulse_num": pulse_num,
            "round_num": self.round_num,
            "agents_pulsed": len(pulsed_roles),
            "agents_frozen": sum(1 for s in self.agent_states.values() if s == FROZEN),
            "agents_in_meeting": sum(1 for s in self.agent_states.values() if s == IN_MEETING),
            "actions": 0,
            "errors": 0,
            "agent_results": {},
        }

        for i, role_id in enumerate(pulsed_roles):
            if i < len(results):
                result = results[i]
                if isinstance(result, Exception):
                    logger.error("Pulse failed for %s: %s", role_id, result)
                    pulse_summary["errors"] += 1
                    self.round_stats[role_id].errors += 1
                    pulse_summary["agent_results"][role_id] = {"error": str(result)}
                elif isinstance(result, dict):
                    pulse_summary["actions"] += result.get("actions", 0)
                    pulse_summary["agent_results"][role_id] = result

        self._last_pulse_time = now_iso
        return pulse_summary

    async def _pulse_single_agent(
        self,
        role_id: str,
        ctx: SessionContext,
        pulse_num: int,
        events: dict,
    ) -> dict:
        """Send a pulse to one agent and process the response.

        Runs in a thread pool because session_manager.send_event is synchronous.
        """
        self.agent_states[role_id] = ACTING

        try:
            # Build pulse message
            message = self._build_pulse_message(role_id, ctx, pulse_num, events)

            # Send event (synchronous — run in executor)
            loop = asyncio.get_event_loop()
            transcript = await loop.run_in_executor(
                None, self.session_manager.send_event, ctx, message
            )

            # Log to observatory
            log_transcript_to_observatory(
                self.sim_run_id, ctx.country_code, self.round_num, transcript
            )

            # Extract actions submitted
            actions = extract_actions_from_transcript(transcript)
            successful_actions = [a for a in actions if a.get("success")]

            # Update stats
            stats = self.round_stats[role_id]
            stats.actions_submitted += len(successful_actions)
            stats.tool_calls += sum(
                1 for t in transcript if t.get("type") == "tool_call"
            )
            stats.pulses_received += 1

            result = {
                "role_id": role_id,
                "actions": len(successful_actions),
                "tool_calls": stats.tool_calls,
                "transcript_entries": len(transcript),
            }

        except Exception as e:
            logger.exception("Error pulsing agent %s", role_id)
            self.round_stats[role_id].errors += 1
            result = {"role_id": role_id, "error": str(e), "actions": 0}

        finally:
            # Return to IDLE unless meeting started during processing
            if self.agent_states.get(role_id) == ACTING:
                self.agent_states[role_id] = IDLE

        return result

    # ------------------------------------------------------------------
    # Meeting processing
    # ------------------------------------------------------------------

    async def _process_meetings(self) -> list[dict]:
        """Check for and run any pending accepted meetings.

        Queries meetings table for accepted meetings where both
        participants are IDLE. Runs each meeting sequentially
        (agents are IN_MEETING during relay, so parallelism is
        not applicable per pair).

        Returns:
            List of meeting result dicts.
        """
        ready = await self.conversation_router.check_pending_meetings(
            self.agents, self.agent_states,
        )

        if not ready:
            return []

        results = []
        for meeting in ready:
            meeting_id = meeting["id"]
            role_a = meeting["participant_a_role_id"]
            role_b = meeting["participant_b_role_id"]

            agent_a = self.agents.get(role_a)
            agent_b = self.agents.get(role_b)

            if not agent_a or not agent_b:
                logger.warning(
                    "[orchestrator] Meeting %s skipped: missing agent (%s or %s)",
                    meeting_id, role_a, role_b,
                )
                continue

            # Check both still IDLE (could have changed since query)
            if self.agent_states.get(role_a) != IDLE:
                continue
            if self.agent_states.get(role_b) != IDLE:
                continue

            logger.info(
                "[orchestrator] Running meeting %s: %s vs %s",
                meeting_id, role_a, role_b,
            )

            try:
                result = await self.conversation_router.run_meeting(
                    meeting_id=meeting_id,
                    agent_a=agent_a,
                    agent_b=agent_b,
                    agent_states=self.agent_states,
                    round_num=self.round_num,
                    max_turns=self.config.max_turns_per_meeting,
                )
                results.append(result)

                # Update meeting stats
                stats_a = self.round_stats.get(role_a)
                stats_b = self.round_stats.get(role_b)
                if stats_a:
                    stats_a.meetings_used += 1
                if stats_b:
                    stats_b.meetings_used += 1

            except Exception as e:
                logger.exception(
                    "[orchestrator] Meeting %s failed: %s", meeting_id, e,
                )
                # Ensure agents are returned to IDLE on failure
                self.agent_states[role_a] = IDLE
                self.agent_states[role_b] = IDLE
                results.append({
                    "meeting_id": meeting_id,
                    "error": str(e),
                    "turns": 0,
                })

        return results

    # ------------------------------------------------------------------
    # Pulse message building
    # ------------------------------------------------------------------

    def _build_pulse_message(
        self,
        role_id: str,
        ctx: SessionContext,
        pulse_num: int,
        events: dict,
    ) -> str:
        """Build the complete pulse message for an agent.

        Combines:
          - Meta context (pulse/round/resource info)
          - Public events (visible to all)
          - Private events (this agent only)
          - Queued events (from while agent was busy)
          - Pending items (meeting invitations, proposals)
        """
        stats = self.round_stats.get(role_id, AgentRoundStats())

        # Mandatory inputs status (check from DB)
        mandatory_submitted = self._get_mandatory_status(role_id)

        # Tool summary for meta context
        tools_summary = [
            "get_my_country — Full country dashboard (economy, political, strategic, tech)",
            "get_my_forces — Your military units and deployments",
            "get_relationships — Bilateral relationships with all countries",
            "get_pending_proposals — Incoming/outgoing proposals awaiting response",
            "get_recent_events — Observatory feed (recent events)",
            "get_country_info(country) — Public info about any country",
            "get_hex_info(row, col) — Map hex details",
            "get_organizations — Your organization memberships",
            "get_my_artefacts — Intel reports, cables, artefacts",
            "get_action_rules(type) — Rules and fields for any action type",
            "request_meeting(country, agenda) — Invite another leader to meet",
            "respond_to_invitation(id, decision) — Accept/decline meeting invitation",
            "send_message(meeting_id, text) — Send chat message in active meeting",
            "submit_action(action) — Submit a game action",
            "write_notes(key, content) — Save notes to persistent memory",
            "read_notes(key) — Read your saved notes",
        ]

        # Build meta context section
        meta = build_meta_context(
            round_num=self.round_num,
            total_rounds=self.config.total_rounds,
            pulse_num=pulse_num,
            total_pulses=self.config.pulses_per_round,
            meetings_remaining=max(0, self.config.max_meetings_per_round - stats.meetings_used),
            intel_cards_remaining=self._get_intel_cards_remaining(role_id),
            mandatory_submitted=mandatory_submitted,
            tools_summary=tools_summary,
        )

        # Format events sections
        public_events = events.get("public", [])
        private_events = events.get("private", [])
        pending_items = events.get("pending", [])

        # Include queued events from while agent was busy
        queued = self._queued_events.get(role_id, [])
        if queued:
            public_events = queued + public_events
            self._queued_events[role_id] = []

        sections = [meta]

        # Public events
        if public_events:
            lines = ["PUBLIC EVENTS:"]
            for evt in public_events[:20]:  # Cap at 20 to manage context size
                summary = evt.get("summary", evt.get("event_type", "event"))
                by = evt.get("country_code", "")
                if by:
                    lines.append(f"- [{by}] {summary}")
                else:
                    lines.append(f"- {summary}")
            sections.append("\n".join(lines))

        # Private / confidential events
        if private_events:
            lines = ["PRIVATE / CONFIDENTIAL:"]
            for evt in private_events[:10]:
                summary = evt.get("summary", evt.get("event_type", "event"))
                lines.append(f"- {summary}")
            sections.append("\n".join(lines))

        # Pending items
        if pending_items:
            lines = ["PENDING ITEMS:"]
            for item in pending_items[:10]:
                item_type = item.get("type", "item")
                summary = item.get("summary", str(item))
                lines.append(f"- [{item_type}] {summary}")
            sections.append("\n".join(lines))

        # Agent status footer
        state = self.agent_states.get(role_id, IDLE)
        status_lines = [
            "YOUR STATUS:",
            f"- State: {state}",
            f"- Meetings used: {stats.meetings_used} of {self.config.max_meetings_per_round}",
            f"- Actions this round: {stats.actions_submitted}",
            f"- Pulses remaining: {self.config.pulses_per_round - pulse_num}",
        ]

        # Mandatory inputs status
        for key, done in mandatory_submitted.items():
            label = "submitted" if done else "NOT submitted"
            status_lines.append(f"- Mandatory: {key} ({label})")

        sections.append("\n".join(status_lines))

        # Closing prompt
        sections.append(
            "Decide what to do. You may act, investigate, request a meeting, or wait."
        )

        return "\n\n".join(sections)

    # ------------------------------------------------------------------
    # Event collection
    # ------------------------------------------------------------------

    async def _collect_events_for_agent(
        self, role_id: str, country_code: str
    ) -> dict:
        """Collect events since last pulse, categorized for this agent.

        Returns:
            {public: [...], private: [...], pending: [...]}.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._collect_events_sync, role_id, country_code
        )

    def _collect_events_sync(self, role_id: str, country_code: str) -> dict:
        """Synchronous event collection from observatory_events."""
        try:
            db = get_client()

            # Query recent events
            q = (
                db.table("observatory_events")
                .select("event_type, category, summary, country_code, payload, created_at")
                .eq("sim_run_id", self.sim_run_id)
                .eq("round_num", self.round_num)
                .order("created_at", desc=True)
                .limit(50)
            )

            if self._last_pulse_time:
                q = q.gte("created_at", self._last_pulse_time)

            result = q.execute()
            all_events = result.data or []

            # Categorize: public vs private vs pending
            public = []
            private = []

            for evt in all_events:
                # Skip our own AI agent log entries
                if evt.get("event_type") == "ai_agent_log":
                    continue

                event_entry = {
                    "event_type": evt.get("event_type"),
                    "category": evt.get("category"),
                    "summary": evt.get("summary"),
                    "country_code": evt.get("country_code"),
                    "created_at": evt.get("created_at"),
                }

                # Private events: targeted at this country only
                payload = evt.get("payload") or {}
                target_country = payload.get("target_country_code")
                visibility = payload.get("visibility", "public")

                if visibility == "private" and target_country == country_code:
                    private.append(event_entry)
                elif visibility == "private" and target_country != country_code:
                    continue  # Not for this agent
                else:
                    public.append(event_entry)

            # Collect pending items (meeting invitations + proposals)
            pending = self._collect_pending_items(role_id, country_code)

            return {"public": public, "private": private, "pending": pending}

        except Exception as e:
            logger.warning("Failed to collect events for %s: %s", role_id, e)
            return {"public": [], "private": [], "pending": []}

    def _collect_pending_items(self, role_id: str, country_code: str) -> list[dict]:
        """Collect pending meeting invitations and proposals for this agent."""
        pending = []
        try:
            db = get_client()

            # Pending meeting invitations targeting this role
            invitations = (
                db.table("meeting_invitations")
                .select("id, inviter_role_id, inviter_country_code, message, status")
                .eq("sim_run_id", self.sim_run_id)
                .eq("invitee_role_id", role_id)
                .eq("status", "pending")
                .execute()
            )
            for inv in invitations.data or []:
                pending.append({
                    "type": "meeting_invitation",
                    "summary": (
                        f"Meeting invitation from {inv['inviter_country_code']} — "
                        f"{inv.get('message', 'no agenda')}"
                    ),
                    "invitation_id": inv["id"],
                    "from_country": inv["inviter_country_code"],
                })

            # Pending proposals/transactions targeting this country
            proposals = (
                db.table("pending_actions")
                .select("id, action_type, country_code, target_info, payload")
                .eq("sim_run_id", self.sim_run_id)
                .eq("status", "pending")
                .execute()
            )
            for p in proposals.data or []:
                target_info = p.get("target_info") or ""
                if country_code in target_info:
                    pending.append({
                        "type": "proposal",
                        "summary": (
                            f"{p['action_type']} from {p['country_code']}"
                        ),
                        "proposal_id": p["id"],
                        "from_country": p["country_code"],
                    })

        except Exception as e:
            logger.warning("Failed to collect pending items for %s: %s", role_id, e)

        return pending

    # ------------------------------------------------------------------
    # Critical interrupts
    # ------------------------------------------------------------------

    async def send_critical_interrupt(
        self, role_ids: list[str], message: str
    ) -> dict:
        """Bypass pulse schedule for urgent events.

        For IDLE agents: sends immediately.
        For IN_MEETING agents: queues for delivery when meeting ends.
        For FROZEN agents: queues for delivery on resume.

        Args:
            role_ids: Agents to interrupt.
            message: The critical event message.

        Returns:
            {sent: [...], queued: [...], errors: [...]}.
        """
        sent = []
        queued = []
        errors = []

        tasks = []
        task_roles = []

        for role_id in role_ids:
            if role_id not in self.agents:
                errors.append({"role_id": role_id, "error": "Agent not found"})
                continue

            state = self.agent_states.get(role_id, IDLE)

            if state in (IN_MEETING, FROZEN):
                # Queue the interrupt for later delivery
                self._queued_events.setdefault(role_id, []).append({
                    "event_type": "critical_interrupt",
                    "summary": message,
                    "category": "critical",
                })
                queued.append(role_id)
                continue

            tasks.append(self._interrupt_single_agent(role_id, message))
            task_roles.append(role_id)

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for i, role_id in enumerate(task_roles):
                if isinstance(results[i], Exception):
                    errors.append({"role_id": role_id, "error": str(results[i])})
                else:
                    sent.append(role_id)

        return {"sent": sent, "queued": queued, "errors": errors}

    async def _interrupt_single_agent(self, role_id: str, message: str) -> None:
        """Send a critical interrupt to one agent."""
        ctx = self.agents[role_id]
        interrupt_msg = (
            f"⚠️ CRITICAL ALERT ⚠️\n\n{message}\n\n"
            "This is an emergency interrupt outside the normal pulse schedule. "
            "Assess the situation and respond immediately."
        )

        loop = asyncio.get_event_loop()
        transcript = await loop.run_in_executor(
            None, self.session_manager.send_event, ctx, interrupt_msg
        )

        log_transcript_to_observatory(
            self.sim_run_id, ctx.country_code, self.round_num, transcript
        )

        write_agent_log_event(
            self.sim_run_id, ctx.country_code, self.round_num,
            event_type="critical_interrupt",
            title=f"Critical interrupt sent to {role_id}",
            description=message[:500],
        )

    # ------------------------------------------------------------------
    # State management
    # ------------------------------------------------------------------

    def get_agent_state(self, role_id: str) -> str:
        """Return current state: IDLE, ACTING, IN_MEETING, FROZEN."""
        return self.agent_states.get(role_id, "UNKNOWN")

    def freeze_agent(self, role_id: str) -> dict:
        """Freeze an agent — stops receiving pulses, events queue."""
        if role_id not in self.agents:
            return {"success": False, "error": f"Agent {role_id} not found"}

        prev_state = self.agent_states.get(role_id, IDLE)
        self.agent_states[role_id] = FROZEN

        ctx = self.agents[role_id]
        self.session_manager.freeze_session(ctx)

        logger.info("Froze agent %s (was %s)", role_id, prev_state)
        return {"success": True, "role_id": role_id, "state": FROZEN, "previous_state": prev_state}

    def resume_agent(self, role_id: str) -> dict:
        """Resume a frozen agent — receives batched events at next pulse."""
        if role_id not in self.agents:
            return {"success": False, "error": f"Agent {role_id} not found"}

        if self.agent_states.get(role_id) != FROZEN:
            return {
                "success": False,
                "error": f"Agent {role_id} is not frozen (state: {self.agent_states.get(role_id)})",
            }

        self.agent_states[role_id] = IDLE

        ctx = self.agents[role_id]
        self.session_manager.resume_session(ctx)

        queued_count = len(self._queued_events.get(role_id, []))
        logger.info("Resumed agent %s (%d queued events)", role_id, queued_count)
        return {
            "success": True,
            "role_id": role_id,
            "state": IDLE,
            "queued_events": queued_count,
        }

    def freeze_all(self) -> dict:
        """Freeze all AI agents."""
        results = {}
        for role_id in list(self.agents.keys()):
            if self.agent_states.get(role_id) != FROZEN:
                results[role_id] = self.freeze_agent(role_id)
        return {
            "frozen_count": sum(1 for r in results.values() if r.get("success")),
            "agents": results,
        }

    def resume_all(self) -> dict:
        """Resume all frozen AI agents."""
        results = {}
        for role_id in list(self.agents.keys()):
            if self.agent_states.get(role_id) == FROZEN:
                results[role_id] = self.resume_agent(role_id)
        return {
            "resumed_count": sum(1 for r in results.values() if r.get("success")),
            "agents": results,
        }

    # ------------------------------------------------------------------
    # Status & summary
    # ------------------------------------------------------------------

    def get_status(self) -> dict:
        """Get all agent states, costs, and activity summary."""
        agents_status = []
        total_input_tokens = 0
        total_output_tokens = 0

        for role_id, ctx in self.agents.items():
            cost = self.session_manager.get_cost_estimate(ctx)
            stats = self.round_stats.get(role_id, AgentRoundStats())

            total_input_tokens += cost.get("input_tokens", 0)
            total_output_tokens += cost.get("output_tokens", 0)

            agents_status.append({
                "role_id": role_id,
                "country_code": ctx.country_code,
                "state": self.agent_states.get(role_id, "UNKNOWN"),
                "session_id": ctx.session_id,
                "round_num": ctx.round_num,
                "cost": cost,
                "round_stats": {
                    "actions": stats.actions_submitted,
                    "tool_calls": stats.tool_calls,
                    "meetings_used": stats.meetings_used,
                    "pulses_received": stats.pulses_received,
                    "errors": stats.errors,
                },
            })

        total_cost = (total_input_tokens * 3.0 / 1_000_000) + (total_output_tokens * 15.0 / 1_000_000)

        return {
            "sim_run_id": self.sim_run_id,
            "round_num": self.round_num,
            "pulse_num": self.pulse_num,
            "total_agents": len(self.agents),
            "agents_idle": sum(1 for s in self.agent_states.values() if s == IDLE),
            "agents_frozen": sum(1 for s in self.agent_states.values() if s == FROZEN),
            "agents_in_meeting": sum(1 for s in self.agent_states.values() if s == IN_MEETING),
            "agents_acting": sum(1 for s in self.agent_states.values() if s == ACTING),
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
            "total_cost_usd": round(total_cost, 2),
            "agents": agents_status,
        }

    def get_round_summary(self) -> dict:
        """Aggregate round stats: actions per agent, total costs, meetings, errors."""
        agent_summaries = {}
        total_actions = 0
        total_errors = 0
        total_meetings = 0

        for role_id, stats in self.round_stats.items():
            ctx = self.agents.get(role_id)
            cost = self.session_manager.get_cost_estimate(ctx) if ctx else {}

            agent_summaries[role_id] = {
                "actions": stats.actions_submitted,
                "tool_calls": stats.tool_calls,
                "meetings_used": stats.meetings_used,
                "pulses_received": stats.pulses_received,
                "errors": stats.errors,
                "cost_usd": cost.get("total_cost_usd", 0),
            }
            total_actions += stats.actions_submitted
            total_errors += stats.errors
            total_meetings += stats.meetings_used

        total_cost = sum(a.get("cost_usd", 0) for a in agent_summaries.values())

        return {
            "sim_run_id": self.sim_run_id,
            "round_num": self.round_num,
            "total_agents": len(self.agents),
            "total_actions": total_actions,
            "total_errors": total_errors,
            "total_meetings": total_meetings,
            "total_cost_usd": round(total_cost, 2),
            "agents": agent_summaries,
        }

    # ------------------------------------------------------------------
    # Shutdown
    # ------------------------------------------------------------------

    async def shutdown(self) -> None:
        """Archive all sessions and persist final state to DB."""
        logger.info("Shutting down orchestrator for sim %s", self.sim_run_id)

        for role_id, ctx in self.agents.items():
            try:
                self.session_manager.cleanup(ctx)
                logger.info("Archived session for %s", role_id)
            except Exception as e:
                logger.warning("Failed to archive session for %s: %s", role_id, e)

        write_agent_log_event(
            self.sim_run_id, "", self.round_num,
            event_type="orchestrator",
            title="Orchestrator Shutdown",
            description=f"Archived {len(self.agents)} agent sessions",
        )

        self.agents.clear()
        self.agent_states.clear()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_mandatory_status(self, role_id: str) -> dict:
        """Check which mandatory inputs have been submitted this round."""
        try:
            db = get_client()
            decisions = (
                db.table("agent_decisions")
                .select("action_type")
                .eq("sim_run_id", self.sim_run_id)
                .eq("country_code", self.agents[role_id].country_code)
                .eq("round_num", self.round_num)
                .execute()
            )
            submitted_types = {d["action_type"] for d in (decisions.data or [])}

            return {
                "budget": "set_budget" in submitted_types,
                "tariffs": "set_tariffs" in submitted_types,
            }
        except Exception as e:
            logger.warning("Failed to check mandatory status for %s: %s", role_id, e)
            return {"budget": False, "tariffs": False}

    def _get_intel_cards_remaining(self, role_id: str) -> int:
        """Get remaining intelligence cards for this agent."""
        try:
            db = get_client()
            ctx = self.agents[role_id]

            # Count covert ops used this sim
            ops_used = (
                db.table("agent_decisions")
                .select("id", count="exact")
                .eq("sim_run_id", self.sim_run_id)
                .eq("country_code", ctx.country_code)
                .in_("action_type", [
                    "espionage", "sabotage", "cyber_attack",
                    "disinformation", "election_meddling", "assassination",
                ])
                .execute()
            )
            used = ops_used.count or 0

            # Default pool: 3 per round (from game rules)
            total_pool = self.round_num * 3
            return max(0, total_pool - used)
        except Exception as e:
            logger.warning("Failed to get intel cards for %s: %s", role_id, e)
            return 0

    async def _send_mandatory_reminders(self) -> None:
        """Send reminder to agents with unsubmitted mandatory inputs."""
        for role_id, ctx in self.agents.items():
            if self.agent_states.get(role_id) == FROZEN:
                continue

            mandatory = self._get_mandatory_status(role_id)
            unsubmitted = [k for k, v in mandatory.items() if not v]

            if unsubmitted:
                reminder = (
                    f"ROUND {self.round_num} ENDING SOON.\n\n"
                    f"You have NOT submitted these mandatory inputs: "
                    f"{', '.join(unsubmitted)}.\n\n"
                    "If you do not submit them before the round ends, "
                    "parliament will impose defaults (budget cuts, no tariff changes). "
                    "Submit now using submit_action."
                )
                try:
                    loop = asyncio.get_event_loop()
                    transcript = await loop.run_in_executor(
                        None, self.session_manager.send_event, ctx, reminder
                    )
                    log_transcript_to_observatory(
                        self.sim_run_id, ctx.country_code, self.round_num, transcript
                    )
                except Exception as e:
                    logger.warning(
                        "Failed to send mandatory reminder to %s: %s", role_id, e
                    )


# ── Global orchestrator registry (one per sim_run) ───────────────────

_orchestrators: dict[str, AIOrchestrator] = {}


def get_orchestrator(sim_run_id: str) -> AIOrchestrator | None:
    """Get the active orchestrator for a sim run, if any."""
    return _orchestrators.get(sim_run_id)


def create_orchestrator(
    sim_run_id: str, config: OrchestratorConfig | None = None
) -> AIOrchestrator:
    """Create and register an orchestrator for a sim run."""
    orch = AIOrchestrator(sim_run_id, config)
    _orchestrators[sim_run_id] = orch
    return orch


def remove_orchestrator(sim_run_id: str) -> None:
    """Remove an orchestrator from the registry."""
    _orchestrators.pop(sim_run_id, None)


# ── Quick test ───────────────────────────────────────────────────────

if __name__ == "__main__":
    import asyncio

    async def quick_test():
        """Quick test: create orchestrator, check config defaults."""
        config = OrchestratorConfig()
        print(f"Config: assertiveness={config.assertiveness}, "
              f"pulses={config.pulses_per_round}, "
              f"model={config.model}")

        orch = AIOrchestrator("test-sim-id", config)
        print(f"Orchestrator created: sim={orch.sim_run_id}, "
              f"agents={len(orch.agents)}")

        # Verify state machine
        orch.agent_states["test_role"] = IDLE
        assert orch.get_agent_state("test_role") == IDLE
        assert orch.get_agent_state("missing_role") == "UNKNOWN"

        # Verify config
        assert config.pulses_per_round == 8
        assert config.max_meetings_per_round == 5
        assert config.round_duration_seconds == 300
        assert config.total_rounds == 6

        print("All checks passed.")

    asyncio.run(quick_test())
