"""Phase 3 — Managed Agent session lifecycle.

Creates and manages a Claude Managed Agent session:
  1. Create agent (system prompt + custom tools)
  2. Create environment (cloud, unrestricted network)
  3. Create session (agent + environment)
  4. Send events (round prompts, alerts)
  5. Stream responses (tool calls, agent reasoning)

Dependencies: anthropic SDK with managed-agents-2026-04-01 beta.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any

from anthropic import Anthropic

from engine.agents.managed.system_prompt import build_system_prompt
from engine.agents.managed.tool_definitions import get_custom_tools_for_agent
from engine.agents.managed.tool_executor import ToolExecutor

logger = logging.getLogger(__name__)


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
    round_num: int = 1
    tool_executor: ToolExecutor | None = None
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    events_sent: int = 0
    actions_submitted: int = 0
    transcript: list[dict] = field(default_factory=list)


class ManagedSessionManager:
    """Manages the lifecycle of a Managed Agent session for TTT."""

    def __init__(self, api_key: str | None = None):
        self.client = Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))
        self._sessions: dict[str, SessionContext] = {}

    def create_session(
        self,
        role_id: str,
        country_code: str,
        sim_run_id: str,
        scenario_code: str,
        round_num: int = 1,
        model: str = "claude-sonnet-4-20250514",
    ) -> SessionContext:
        """Create a full managed agent session.

        Args:
            role_id: Role identifier (e.g., "dealer").
            country_code: Country code (e.g., "columbia").
            sim_run_id: UUID of the sim_run.
            scenario_code: Scenario code for tool binding.
            round_num: Starting round number.
            model: Claude model ID.

        Returns:
            SessionContext with all IDs and the tool executor.
        """
        # Build system prompt (Layer 1)
        system_prompt = build_system_prompt(role_id)
        logger.info("Built system prompt for %s (%d chars)", role_id, len(system_prompt))

        # Get custom tool definitions
        custom_tools = get_custom_tools_for_agent()
        logger.info("Defined %d custom tools", len(custom_tools))

        # Create agent
        agent = self.client.beta.agents.create(
            name=f"TTT-{role_id}-{country_code}",
            model=model,
            system=system_prompt,
            tools=custom_tools,
        )
        logger.info("Created agent: %s (version %d)", agent.id, agent.version)

        # Create environment
        environment = self.client.beta.environments.create(
            name=f"ttt-spike-{sim_run_id[:8]}",
            config={
                "type": "cloud",
                "networking": {"type": "unrestricted"},
            },
        )
        logger.info("Created environment: %s", environment.id)

        # Create session
        session = self.client.beta.sessions.create(
            agent=agent.id,
            environment_id=environment.id,
            title=f"TTT Spike: {role_id} R{round_num}",
        )
        logger.info("Created session: %s", session.id)

        # Create tool executor
        executor = ToolExecutor(
            country_code=country_code,
            scenario_code=scenario_code,
            sim_run_id=sim_run_id,
            round_num=round_num,
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
            round_num=round_num,
            tool_executor=executor,
        )
        self._sessions[session.id] = ctx
        return ctx

    def send_event(self, ctx: SessionContext, message: str) -> list[dict]:
        """Send a message to the session and process the full response.

        Handles the event stream: dispatches custom tool calls, logs agent
        reasoning, tracks token usage. Returns when session becomes idle.

        Args:
            ctx: The session context.
            message: The message to send (e.g., round prompt, alert).

        Returns:
            List of transcript entries (agent messages, tool calls, actions).
        """
        transcript: list[dict] = []
        ctx.events_sent += 1

        logger.info("Sending event #%d to session %s: %s",
                     ctx.events_sent, ctx.session_id, message[:100])

        transcript.append({"type": "user_message", "content": message})

        # Check session status — if it's waiting for tool results, interrupt first
        try:
            status = self.client.beta.sessions.retrieve(ctx.session_id)
            if status.status != "idle":
                logger.warning("Session status is '%s', sending interrupt before new message",
                               status.status)
                self.client.beta.sessions.events.send(
                    ctx.session_id,
                    events=[{"type": "user.interrupt"}],
                )
                import time
                time.sleep(1)
        except Exception as e:
            logger.warning("Could not check/interrupt session: %s", e)

        with self.client.beta.sessions.events.stream(ctx.session_id) as stream:
            # Send the user message
            self.client.beta.sessions.events.send(
                ctx.session_id,
                events=[
                    {
                        "type": "user.message",
                        "content": [{"type": "text", "text": message}],
                    },
                ],
            )

            # Process streaming events
            for event in stream:
                try:
                    entry = self._handle_event(ctx, event)
                    if entry:
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
                        # These are tool calls we failed to respond to in the
                        # stream. Send empty results so the session can continue.
                        for eid in pending_ids:
                            try:
                                self.client.beta.sessions.events.send(
                                    ctx.session_id,
                                    events=[{
                                        "type": "user.custom_tool_result",
                                        "custom_tool_use_id": eid,
                                        "content": [{"type": "text", "text": '{"note": "Tool result was already sent in stream"}'}],
                                    }],
                                )
                            except Exception as e:
                                logger.warning("Failed to send pending result for %s: %s", eid, e)
                        continue  # Stay in the stream loop

                    break  # Normal idle — agent finished

                if event.type == "session.status_terminated":
                    logger.error("Session terminated: %s",
                                 getattr(event, "error", "unknown"))
                    transcript.append({
                        "type": "error",
                        "content": f"Session terminated: {getattr(event, 'error', 'unknown')}",
                    })
                    break

        ctx.transcript.extend(transcript)
        return transcript

    def _handle_event(self, ctx: SessionContext, event: Any) -> dict | None:
        """Handle a single SSE event from the stream."""
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

            # Execute the tool
            result = ctx.tool_executor.execute(tool_name, tool_input)

            # Track actions
            if tool_name in ("submit_action", "commit_action"):
                ctx.actions_submitted += 1

            # Send result back to the agent
            self.client.beta.sessions.events.send(
                ctx.session_id,
                events=[
                    {
                        "type": "user.custom_tool_result",
                        "custom_tool_use_id": event.id,
                        "content": [{"type": "text", "text": result}],
                    },
                ],
            )

            return {
                "type": "tool_call",
                "tool": tool_name,
                "input": tool_input,
                "result_preview": result[:300] if len(result) > 300 else result,
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

    def update_round(self, ctx: SessionContext, round_num: int) -> None:
        """Update the round number for an active session."""
        ctx.round_num = round_num
        if ctx.tool_executor:
            ctx.tool_executor.round_num = round_num

    def get_cost_estimate(self, ctx: SessionContext) -> dict:
        """Estimate session cost based on token usage.

        Pricing: Sonnet 4 — $3/M input, $15/M output (as of 2026-04).
        """
        input_cost = ctx.total_input_tokens * 3.0 / 1_000_000
        output_cost = ctx.total_output_tokens * 15.0 / 1_000_000
        return {
            "input_tokens": ctx.total_input_tokens,
            "output_tokens": ctx.total_output_tokens,
            "input_cost_usd": round(input_cost, 4),
            "output_cost_usd": round(output_cost, 4),
            "total_cost_usd": round(input_cost + output_cost, 4),
            "events_sent": ctx.events_sent,
            "actions_submitted": ctx.actions_submitted,
            "tool_calls": len(ctx.tool_executor.call_log) if ctx.tool_executor else 0,
        }

    def cleanup(self, ctx: SessionContext) -> None:
        """Archive and clean up session resources."""
        try:
            self.client.beta.sessions.archive(ctx.session_id)
            logger.info("Archived session %s", ctx.session_id)
        except Exception as e:
            logger.warning("Failed to archive session: %s", e)

        try:
            self.client.beta.agents.archive(ctx.agent_id)
            logger.info("Archived agent %s", ctx.agent_id)
        except Exception as e:
            logger.warning("Failed to archive agent: %s", e)
