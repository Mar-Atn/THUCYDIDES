"""Phase 1C — Hardened Managed Agent session lifecycle (async).

Creates and manages a Claude Managed Agent session:
  1. Create agent (system prompt + custom tools)
  2. Create environment (cloud, unrestricted network)
  3. Create session (agent + environment)
  4. Send events (round prompts, alerts)
  5. Stream responses (tool calls, agent reasoning)
  6. Persist session metadata to DB (ai_agent_sessions)
  7. Health check, freeze/resume, recovery from termination
  8. Retry logic for transient API errors

Dependencies: anthropic SDK with managed-agents-2026-04-01 beta.

Migration note (2026-04-21): Converted from sync Anthropic to AsyncAnthropic
to eliminate thread exhaustion ([Errno 35] Resource temporarily unavailable)
when 8+ agents run in parallel. Pure async — no threads, single event loop.
"""
from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from anthropic import AsyncAnthropic

from engine.agents.managed.ai_config import get_ai_model
from engine.agents.managed.system_prompt import build_system_prompt
from engine.agents.managed.tool_definitions import get_custom_tools_for_agent
from engine.agents.managed.tool_executor import ToolExecutor
from engine.services.supabase import get_client

logger = logging.getLogger(__name__)

# Retry constants
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 2


@dataclass
class SessionContext:
    """Tracks a managed agent session and its associated resources."""
    agent_id: str
    agent_version: int
    environment_id: str
    session_id: str
    role_id: str
    country_code: str
    sim_run_id: str
    scenario_code: str
    model: str = "claude-sonnet-4-6"
    round_num: int = 1
    tool_executor: ToolExecutor | None = None
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    events_sent: int = 0
    actions_submitted: int = 0
    tool_calls: int = 0
    transcript: list[dict] = field(default_factory=list)


class ManagedSessionManager:
    """Manages the lifecycle of a Managed Agent session for TTT.

    Production-hardened with DB persistence, health checks, session
    recovery, freeze/resume, and retry logic for transient errors.

    Uses AsyncAnthropic for pure async operation — no threads needed,
    supports 20+ concurrent agents on a single event loop.
    """

    def __init__(self, api_key: str | None = None):
        self.client = AsyncAnthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))
        self._sessions: dict[str, SessionContext] = {}

    # ------------------------------------------------------------------
    # DB persistence helpers
    # ------------------------------------------------------------------

    def _persist_session(self, ctx: SessionContext, status: str = "initializing") -> None:
        """Write or update session metadata in ai_agent_sessions table."""
        try:
            db = get_client()
            row = {
                "sim_run_id": ctx.sim_run_id,
                "role_id": ctx.role_id,
                "country_code": ctx.country_code,
                "agent_id": ctx.agent_id,
                "environment_id": ctx.environment_id,
                "session_id": ctx.session_id,
                "status": status,
                "model": ctx.model,
                "round_num": ctx.round_num,
                "total_input_tokens": ctx.total_input_tokens,
                "total_output_tokens": ctx.total_output_tokens,
                "events_sent": ctx.events_sent,
                "actions_submitted": ctx.actions_submitted,
                "tool_calls": ctx.tool_calls,
                "last_active_at": datetime.now(timezone.utc).isoformat(),
            }
            db.table("ai_agent_sessions").upsert(
                row, on_conflict="sim_run_id,role_id"
            ).execute()
        except Exception as e:
            logger.warning("Failed to persist session to DB: %s", e)

    def _update_session_field(self, ctx: SessionContext, **fields: Any) -> None:
        """Update specific fields in ai_agent_sessions for this session."""
        try:
            db = get_client()
            fields["last_active_at"] = datetime.now(timezone.utc).isoformat()
            db.table("ai_agent_sessions").update(fields).eq(
                "sim_run_id", ctx.sim_run_id
            ).eq("role_id", ctx.role_id).execute()
        except Exception as e:
            logger.warning("Failed to update session fields: %s", e)

    def _update_token_counts(self, ctx: SessionContext) -> None:
        """Sync cumulative token counts to DB."""
        self._update_session_field(
            ctx,
            total_input_tokens=ctx.total_input_tokens,
            total_output_tokens=ctx.total_output_tokens,
            events_sent=ctx.events_sent,
            actions_submitted=ctx.actions_submitted,
            tool_calls=ctx.tool_calls,
        )

    # ------------------------------------------------------------------
    # Session creation
    # ------------------------------------------------------------------

    async def create_session(
        self,
        role_id: str,
        country_code: str,
        sim_run_id: str,
        scenario_code: str,
        round_num: int = 1,
        model: str | None = None,
    ) -> SessionContext:
        """Create a full managed agent session.

        Args:
            role_id: Role identifier (e.g., "dealer").
            country_code: Country code (e.g., "columbia").
            sim_run_id: UUID of the sim_run.
            scenario_code: Scenario code for tool binding.
            round_num: Starting round number.
            model: Claude model ID. If None, reads from M9 AI Settings (sim_config).

        Returns:
            SessionContext with all IDs and the tool executor.
        """
        if model is None:
            model = get_ai_model("decisions")
        # Build system prompt (Layer 1) — use DB context when sim_run_id available
        system_prompt = build_system_prompt(role_id, sim_run_id=sim_run_id)
        logger.info("Built system prompt for %s (%d chars)", role_id, len(system_prompt))

        # Get custom tool definitions
        custom_tools = get_custom_tools_for_agent()
        logger.info("Defined %d custom tools", len(custom_tools))

        # Create agent (async)
        agent = await self.client.beta.agents.create(
            name=f"TTT-{role_id}-{country_code}",
            model=model,
            system=system_prompt,
            tools=custom_tools,
        )
        logger.info("Created agent: %s (version %d)", agent.id, agent.version)

        # Create environment (async)
        environment = await self.client.beta.environments.create(
            name=f"ttt-{sim_run_id[:8]}",
            config={
                "type": "cloud",
                "networking": {"type": "unrestricted"},
            },
        )
        logger.info("Created environment: %s", environment.id)

        # Create session (async)
        session = await self.client.beta.sessions.create(
            agent=agent.id,
            environment_id=environment.id,
            title=f"TTT: {role_id} R{round_num}",
        )
        logger.info("Created session: %s", session.id)

        # Create tool executor
        executor = ToolExecutor(
            country_code=country_code,
            scenario_code=scenario_code,
            sim_run_id=sim_run_id,
            round_num=round_num,
            role_id=role_id,
        )

        ctx = SessionContext(
            agent_id=agent.id,
            agent_version=agent.version,
            environment_id=environment.id,
            session_id=session.id,
            role_id=role_id,
            country_code=country_code,
            sim_run_id=sim_run_id,
            scenario_code=scenario_code,
            model=model,
            round_num=round_num,
            tool_executor=executor,
        )
        self._sessions[session.id] = ctx

        # Persist to DB
        self._persist_session(ctx, status="ready")

        return ctx

    # ------------------------------------------------------------------
    # Event sending (with retry)
    # ------------------------------------------------------------------

    async def send_event(self, ctx: SessionContext, message: str) -> list[dict]:
        """Send a message to the session and process the full response.

        Handles the event stream: dispatches custom tool calls, logs agent
        reasoning, tracks token usage. Returns when session becomes idle.
        Retries up to MAX_RETRIES on transient connection errors.

        Args:
            ctx: The session context.
            message: The message to send (e.g., round prompt, alert).

        Returns:
            List of transcript entries (agent messages, tool calls, actions).
        """
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                return await self._send_event_inner(ctx, message)
            except ConnectionError as e:
                if attempt < MAX_RETRIES:
                    wait = RETRY_BACKOFF_SECONDS * attempt
                    logger.warning(
                        "Connection error on attempt %d/%d, retrying in %ds: %s",
                        attempt, MAX_RETRIES, wait, e,
                    )
                    await asyncio.sleep(wait)
                else:
                    logger.error("Connection error after %d attempts: %s", MAX_RETRIES, e)
                    raise
            except Exception as e:
                # For non-connection errors, check if it looks transient
                err_str = str(e).lower()
                is_transient = any(
                    tok in err_str
                    for tok in ("timeout", "502", "503", "connection reset", "rate limit")
                )
                if is_transient and attempt < MAX_RETRIES:
                    wait = RETRY_BACKOFF_SECONDS * attempt
                    logger.warning(
                        "Transient error on attempt %d/%d, retrying in %ds: %s",
                        attempt, MAX_RETRIES, wait, e,
                    )
                    await asyncio.sleep(wait)
                else:
                    raise

        # Should not reach here, but just in case
        return await self._send_event_inner(ctx, message)

    async def _send_event_inner(self, ctx: SessionContext, message: str) -> list[dict]:
        """Core send_event logic (no retry wrapper).

        Includes robust interrupt-before-send: checks session status, sends
        interrupt if stuck (requires_action), and retries up to 3 times on
        400 errors about 'waiting on responses'.
        """
        transcript: list[dict] = []
        ctx.events_sent += 1

        logger.info("Sending event #%d to session %s: %s",
                     ctx.events_sent, ctx.session_id, message[:100])

        transcript.append({"type": "user_message", "content": message})

        # Update last_active_at in DB (sync — fast)
        self._update_session_field(ctx, status="active", events_sent=ctx.events_sent)

        # Robust interrupt-before-send: check status and clear stuck state
        await self._ensure_session_idle(ctx)

        # Retry loop for sending the message (handles 400 "waiting on responses")
        send_attempts = 3
        for send_attempt in range(1, send_attempts + 1):
            try:
                return await self._stream_event(ctx, message, transcript)
            except Exception as e:
                err_str = str(e).lower()
                is_waiting_error = any(
                    tok in err_str
                    for tok in ("waiting on responses", "waiting for tool", "requires_action", "not idle")
                )
                if is_waiting_error and send_attempt < send_attempts:
                    logger.warning(
                        "Session stuck on attempt %d/%d, sending interrupt and retrying: %s",
                        send_attempt, send_attempts, e,
                    )
                    try:
                        await self.client.beta.sessions.events.send(
                            ctx.session_id,
                            events=[{"type": "user.interrupt"}],
                        )
                    except Exception as int_e:
                        logger.warning("Interrupt failed: %s", int_e)
                    await asyncio.sleep(2)
                    # Re-check status after interrupt
                    await self._ensure_session_idle(ctx)
                else:
                    raise

        # Should not reach here, but just in case
        return await self._stream_event(ctx, message, transcript)

    async def _ensure_session_idle(self, ctx: SessionContext) -> None:
        """Check session status; if not idle, send interrupt and wait."""
        try:
            status = await self.client.beta.sessions.retrieve(ctx.session_id)
            session_status = getattr(status, "status", "unknown")
            if session_status not in ("idle", "unknown"):
                logger.warning(
                    "Session status is '%s', sending interrupt before new message",
                    session_status,
                )
                await self.client.beta.sessions.events.send(
                    ctx.session_id,
                    events=[{"type": "user.interrupt"}],
                )
                await asyncio.sleep(2)
                # Verify it's idle now
                status2 = await self.client.beta.sessions.retrieve(ctx.session_id)
                status2_val = getattr(status2, "status", "unknown")
                if status2_val not in ("idle", "unknown"):
                    logger.warning(
                        "Session still '%s' after interrupt, proceeding anyway",
                        status2_val,
                    )
        except Exception as e:
            logger.warning("Could not check/interrupt session: %s", e)

    # Timeout for SSE stream idle (no events received). Known Anthropic issue:
    # streams can hang indefinitely (~10-15% frequency per community reports).
    # See: https://github.com/anthropics/anthropic-sdk-typescript/issues/867
    STREAM_IDLE_TIMEOUT_SECONDS = 60  # 1 minute — balances agent response time vs hang detection

    async def _stream_event(
        self, ctx: SessionContext, message: str, transcript: list[dict]
    ) -> list[dict]:
        """Open a stream, send user.message, and process events until idle.

        Includes stream idle timeout to handle known Anthropic SSE hang issue.
        If no events arrive within STREAM_IDLE_TIMEOUT_SECONDS, the stream is
        abandoned and the method returns whatever transcript was collected.
        """
        async with await self.client.beta.sessions.events.stream(ctx.session_id) as stream:
            # Send the user message
            await self.client.beta.sessions.events.send(
                ctx.session_id,
                events=[
                    {
                        "type": "user.message",
                        "content": [{"type": "text", "text": message}],
                    },
                ],
            )

            # Process streaming events with idle timeout
            async def _next_event():
                """Get next event from stream, with timeout."""
                async for ev in stream:
                    return ev
                return None  # Stream ended

            while True:
                try:
                    event = await asyncio.wait_for(
                        _next_event(),
                        timeout=self.STREAM_IDLE_TIMEOUT_SECONDS,
                    )
                except asyncio.TimeoutError:
                    logger.error(
                        "Stream idle timeout (%ds) for session %s — aborting stream",
                        self.STREAM_IDLE_TIMEOUT_SECONDS, ctx.session_id,
                    )
                    break

                if event is None:
                    break  # Stream ended normally
                try:
                    entry = self._handle_event(ctx, event)
                    if entry:
                        # If this was a tool call, send the result back (async)
                        tool_result = entry.pop("_tool_result_to_send", None)
                        if tool_result:
                            try:
                                await self.client.beta.sessions.events.send(
                                    ctx.session_id,
                                    events=[
                                        {
                                            "type": "user.custom_tool_result",
                                            "custom_tool_use_id": tool_result["event_id"],
                                            "content": [{"type": "text", "text": tool_result["result"]}],
                                        },
                                    ],
                                )
                            except Exception as tool_err:
                                # Parallel tool calls: API may reject out-of-order results.
                                # The requires_action handler will resend in correct order.
                                if "waiting on responses" in str(tool_err):
                                    logger.debug("Tool result queued for reorder: %s", tool_result["event_id"][:20])
                                else:
                                    logger.warning("Tool result send failed: %s", tool_err)
                        transcript.append(entry)
                except Exception as e:
                    logger.error("Error handling event %s: %s", event.type, e)
                    transcript.append({"type": "error", "content": str(e)})

                if event.type == "session.status_idle":
                    stop_reason = getattr(event, "stop_reason", None)
                    logger.info("Session idle (stop_reason: %s)", stop_reason)

                    # If requires_action, the agent made tool calls but went
                    # idle waiting for results we already sent. Send a nudge
                    # to resume processing.
                    if stop_reason and getattr(stop_reason, "type", "") == "requires_action":
                        pending_ids = getattr(stop_reason, "event_ids", [])
                        logger.info("Session requires action for %d pending tools", len(pending_ids))
                        # Send results one at a time, LAST first (API accepts most recent first)
                        for eid in reversed(pending_ids):
                            try:
                                await self.client.beta.sessions.events.send(
                                    ctx.session_id,
                                    events=[{
                                        "type": "user.custom_tool_result",
                                        "custom_tool_use_id": eid,
                                        "content": [{"type": "text", "text": '{"note": "Tool result delivered"}'}],
                                    }],
                                )
                            except Exception:
                                pass  # Will be resent on next requires_action cycle
                        continue  # Stay in the stream loop

                    break  # Normal idle — agent finished

                # Handle rescheduled — API is retrying automatically
                if event.type == "session.status_rescheduled":
                    logger.info("Session rescheduled (API retrying): %s",
                                getattr(event, "reason", "unknown"))
                    continue

                if event.type == "session.status_terminated":
                    logger.error("Session terminated: %s",
                                 getattr(event, "error", "unknown"))
                    transcript.append({
                        "type": "error",
                        "content": f"Session terminated: {getattr(event, 'error', 'unknown')}",
                    })
                    # Update DB status
                    self._update_session_field(ctx, status="terminated")
                    break

        ctx.transcript.extend(transcript)

        # Sync token counts to DB after each event
        self._update_token_counts(ctx)

        return transcript

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------

    def _handle_event(self, ctx: SessionContext, event: Any) -> dict | None:
        """Handle a single SSE event from the stream.

        Note: This method is intentionally sync. The tool executor calls
        Supabase (sync client) for DB operations which are fast (<100ms).
        Tool results are returned as metadata — the caller (_stream_event)
        sends them back to the agent via the async client.
        """
        etype = event.type

        # Agent text message
        if etype == "agent.message":
            text = ""
            for block in getattr(event, "content", []):
                if hasattr(block, "text"):
                    text += block.text
            if text:
                logger.info("Agent says: %s", text[:200])
                return {"type": "agent_message", "content": text}

        # Agent thinking
        if etype == "agent.thinking":
            text = ""
            for block in getattr(event, "content", []):
                if hasattr(block, "text"):
                    text += block.text
            if text:
                return {"type": "agent_thinking", "content": text[:500]}

        # Custom tool use — our game tools
        if etype == "agent.custom_tool_use":
            tool_name = event.name
            tool_input = event.input or {}
            logger.info("Agent calls tool: %s(%s)", tool_name,
                        str(tool_input)[:100])

            # Execute the tool (SYNC — Supabase client is sync, fast <100ms)
            result = ctx.tool_executor.execute(tool_name, tool_input)

            # Track actions and tool calls
            ctx.tool_calls += 1
            if tool_name in ("submit_action", "commit_action"):
                ctx.actions_submitted += 1

            # Return tool result metadata — _stream_event sends it async
            return {
                "type": "tool_call",
                "tool": tool_name,
                "input": tool_input,
                "result_preview": result[:300] if len(result) > 300 else result,
                "_tool_result_to_send": {
                    "event_id": event.id,
                    "result": result,
                },
            }

        # Token usage tracking
        if etype == "span.model_request_end":
            usage = getattr(event, "model_usage", None)
            if usage:
                inp = getattr(usage, "input_tokens", 0)
                out = getattr(usage, "output_tokens", 0)
                ctx.total_input_tokens += inp
                ctx.total_output_tokens += out
                logger.info("Tokens: +%d in, +%d out (total: %d/%d)",
                            inp, out, ctx.total_input_tokens, ctx.total_output_tokens)

        # Session errors
        if etype == "session.error":
            error_msg = getattr(event, "error", str(event))
            logger.error("Session error: %s", error_msg)
            return {"type": "error", "content": str(error_msg)}

        return None

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    async def health_check(self, ctx: SessionContext) -> str:
        """Check session health via the Anthropic API.

        Returns:
            Status string: 'idle', 'running', 'terminated', or 'unknown'.
        """
        try:
            status = await self.client.beta.sessions.retrieve(ctx.session_id)
            session_status = getattr(status, "status", "unknown")
            if session_status == "terminated":
                logger.warning(
                    "Session %s (role=%s) is terminated",
                    ctx.session_id, ctx.role_id,
                )
            logger.info("Health check for %s: %s", ctx.session_id, session_status)
            return session_status
        except Exception as e:
            logger.error("Health check failed for session %s: %s", ctx.session_id, e)
            return "unknown"

    # ------------------------------------------------------------------
    # Session recovery
    # ------------------------------------------------------------------

    async def recover_session(self, ctx: SessionContext) -> SessionContext:
        """Recover a terminated session by creating a new one with memory context.

        Loads the agent's memory notes from agent_memories and injects them
        into the new session's initialization message so the agent retains
        continuity.

        Args:
            ctx: The old (terminated) session context.

        Returns:
            New SessionContext with fresh agent/environment/session IDs.
        """
        logger.info(
            "Recovering session for role=%s country=%s (old session=%s)",
            ctx.role_id, ctx.country_code, ctx.session_id,
        )

        # Load memory notes from agent_memories (sync — DB query)
        memory_notes = self._load_agent_memories(ctx.sim_run_id, ctx.country_code)

        # Create a fresh session (async)
        new_ctx = await self.create_session(
            role_id=ctx.role_id,
            country_code=ctx.country_code,
            sim_run_id=ctx.sim_run_id,
            scenario_code=ctx.scenario_code,
            round_num=ctx.round_num,
            model=ctx.model,
        )

        # Carry over cumulative token counts from the old session
        new_ctx.total_input_tokens = ctx.total_input_tokens
        new_ctx.total_output_tokens = ctx.total_output_tokens
        new_ctx.events_sent = ctx.events_sent
        new_ctx.actions_submitted = ctx.actions_submitted
        new_ctx.tool_calls = ctx.tool_calls

        # Send recovery initialization message
        if memory_notes:
            notes_text = "\n".join(
                f"- [{n['memory_key']}] (R{n.get('round_num', '?')}): {n['content']}"
                for n in memory_notes
            )
            recovery_msg = (
                "Your previous session was interrupted. "
                "Here are your notes from memory:\n\n"
                f"{notes_text}\n\n"
                f"You are currently in Round {ctx.round_num}. "
                "Review your notes and continue with your strategy."
            )
        else:
            recovery_msg = (
                "Your previous session was interrupted. "
                f"You are currently in Round {ctx.round_num}. "
                "You have no saved notes. Assess the situation using your tools."
            )

        logger.info("Sending recovery message (%d chars) to new session", len(recovery_msg))
        await self.send_event(new_ctx, recovery_msg)

        # Remove old session from local cache
        self._sessions.pop(ctx.session_id, None)

        # Mark old session as terminated in DB, new one is already persisted
        self._update_session_field(ctx, status="terminated")

        logger.info(
            "Session recovered: old=%s -> new=%s",
            ctx.session_id, new_ctx.session_id,
        )
        return new_ctx

    def _load_agent_memories(self, sim_run_id: str, country_code: str) -> list[dict]:
        """Load all memory notes for an agent from agent_memories table."""
        try:
            db = get_client()
            result = (
                db.table("agent_memories")
                .select("memory_key,content,round_num")
                .eq("sim_run_id", sim_run_id)
                .eq("country_code", country_code)
                .order("round_num")
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.warning("Failed to load agent memories: %s", e)
            return []

    # ------------------------------------------------------------------
    # Freeze / Resume
    # ------------------------------------------------------------------

    def freeze_session(self, ctx: SessionContext) -> None:
        """Freeze an AI participant -- stop sending pulses.

        Sets status to 'frozen' in DB. The orchestrator checks this
        before sending round events and skips frozen agents.
        """
        logger.info("Freezing session %s (role=%s)", ctx.session_id, ctx.role_id)
        self._update_session_field(ctx, status="frozen")

    def resume_session(self, ctx: SessionContext) -> None:
        """Resume a frozen AI participant.

        Sets status back to 'ready' so the orchestrator includes
        this agent in the next pulse cycle.
        """
        logger.info("Resuming session %s (role=%s)", ctx.session_id, ctx.role_id)
        self._update_session_field(ctx, status="ready")

    # ------------------------------------------------------------------
    # Session listing
    # ------------------------------------------------------------------

    def list_active_sessions(self, sim_run_id: str) -> list[dict]:
        """List all active AI sessions for a sim run from DB.

        Returns rows where status is not 'archived' or 'terminated'.
        """
        try:
            db = get_client()
            result = (
                db.table("ai_agent_sessions")
                .select("*")
                .eq("sim_run_id", sim_run_id)
                .in_("status", ["initializing", "ready", "active", "frozen"])
                .order("role_id")
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error("Failed to list active sessions: %s", e)
            return []

    # ------------------------------------------------------------------
    # Round management
    # ------------------------------------------------------------------

    def update_round(self, ctx: SessionContext, round_num: int) -> None:
        """Update the round number for an active session."""
        ctx.round_num = round_num
        if ctx.tool_executor:
            ctx.tool_executor.round_num = round_num
        self._update_session_field(ctx, round_num=round_num)

    # ------------------------------------------------------------------
    # Cost tracking
    # ------------------------------------------------------------------

    def get_cost_estimate(self, ctx: SessionContext) -> dict:
        """Estimate session cost based on token usage.

        Reads from DB for cross-session totals if available.
        Pricing: Sonnet 4 -- $3/M input, $15/M output (as of 2026-04).
        """
        # Try to get DB totals (covers recovered sessions)
        db_tokens = self._get_db_token_totals(ctx.sim_run_id, ctx.role_id)

        input_tokens = db_tokens.get("total_input_tokens", ctx.total_input_tokens)
        output_tokens = db_tokens.get("total_output_tokens", ctx.total_output_tokens)
        model_name = db_tokens.get("model", ctx.model)

        input_cost = input_tokens * 3.0 / 1_000_000
        output_cost = output_tokens * 15.0 / 1_000_000
        return {
            "model": model_name,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_cost_usd": round(input_cost, 4),
            "output_cost_usd": round(output_cost, 4),
            "total_cost_usd": round(input_cost + output_cost, 4),
            "events_sent": db_tokens.get("events_sent", ctx.events_sent),
            "actions_submitted": db_tokens.get("actions_submitted", ctx.actions_submitted),
            "tool_calls": db_tokens.get("tool_calls", ctx.tool_calls),
        }

    def _get_db_token_totals(self, sim_run_id: str, role_id: str) -> dict:
        """Fetch token totals from DB for cross-session accuracy."""
        try:
            db = get_client()
            result = (
                db.table("ai_agent_sessions")
                .select("total_input_tokens,total_output_tokens,events_sent,"
                        "actions_submitted,tool_calls,model")
                .eq("sim_run_id", sim_run_id)
                .eq("role_id", role_id)
                .execute()
            )
            if result.data:
                return result.data[0]
        except Exception as e:
            logger.warning("Failed to read DB token totals: %s", e)
        return {}

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    async def cleanup(self, ctx: SessionContext) -> None:
        """Archive and clean up session resources."""
        try:
            await self.client.beta.sessions.archive(ctx.session_id)
            logger.info("Archived session %s", ctx.session_id)
        except Exception as e:
            logger.warning("Failed to archive session: %s", e)

        try:
            await self.client.beta.agents.archive(ctx.agent_id)
            logger.info("Archived agent %s", ctx.agent_id)
        except Exception as e:
            logger.warning("Failed to archive agent: %s", e)

        # Mark as archived in DB (sync)
        self._update_session_field(ctx, status="archived")

        # Remove from local cache
        self._sessions.pop(ctx.session_id, None)
