"""Phase 5 — Conversation Router: mediates bilateral AI-AI meetings.

Routes bilateral conversations between two AI agent sessions via the
shared meeting_messages table. Messages are visible in the same
Telegram-style chat UI that humans use.

Flow:
  1. Agent A calls request_meeting() -> meeting_invitations table
  2. Agent B receives invitation at next pulse -> calls respond_to_invitation(accept)
  3. Orchestrator detects accepted meeting via check_pending_meetings()
  4. ConversationRouter.run_meeting() sets both agents IN_MEETING,
     relays messages turn-by-turn, writes to meeting_messages table
  5. Meeting ends (turn limit or [END MEETING]) -> both agents IDLE

Dependencies: session_manager (Phase 1C), meeting_service, event_handler.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from engine.agents.managed.event_handler import write_agent_log_event
from engine.agents.managed.session_manager import ManagedSessionManager, SessionContext
from engine.services.meeting_service import get_meeting, send_message, end_meeting
from engine.services.supabase import get_client

logger = logging.getLogger(__name__)

# Marker the agent can use to end a meeting early
END_MEETING_MARKER = "[END MEETING]"

MEETING_RULES_TEMPLATE = (
    "MEETING RULES:\n"
    "- Speak naturally. 1-3 sentences per turn. Like texting, not speechmaking.\n"
    "- You may propose deals, make threats, share intelligence, or build rapport.\n"
    "- To end the meeting early, say: [END MEETING]\n"
    "- Maximum {max_turns} messages from you in this meeting."
)


class ConversationRouter:
    """Routes bilateral conversations between two AI agent sessions.

    Uses the meetings + meeting_messages tables (shared with human UI).
    Messages appear in the same chat interface humans use.

    When a dispatcher is provided, state transitions go through
    dispatcher.set_agent_state() so the dispatcher loop correctly
    skips agents that are IN_MEETING and resumes delivery when
    they return to IDLE.
    """

    def __init__(
        self,
        session_manager: ManagedSessionManager,
        sim_run_id: str,
        dispatcher: Any | None = None,
    ):
        self.session_manager = session_manager
        self.sim_run_id = sim_run_id
        self._dispatcher = dispatcher

    # ------------------------------------------------------------------
    # State transitions — route through dispatcher when available
    # ------------------------------------------------------------------

    def _set_agent_state(
        self, agent_states: dict[str, str], role_id: str, state: str
    ) -> None:
        """Set agent state via dispatcher (preferred) or direct dict write."""
        if self._dispatcher:
            self._dispatcher.set_agent_state(role_id, state)
        else:
            agent_states[role_id] = state

    # ------------------------------------------------------------------
    # Discovery: find accepted meetings ready to start
    # ------------------------------------------------------------------

    async def check_pending_meetings(
        self,
        agents: dict[str, SessionContext],
        agent_states: dict[str, str],
    ) -> list[dict]:
        """Check for accepted meetings where both agents are IDLE.

        Queries the meetings table for active meetings in this sim_run
        that have not yet been started (turn_count == 0). Both
        participants must be IDLE and present in the agents dict.

        Args:
            agents: role_id -> SessionContext mapping.
            agent_states: role_id -> state string mapping.

        Returns:
            List of meeting dicts ready to run.
        """
        # Sync DB call — fast (<100ms), no need for executor
        return self._check_pending_sync(agents, agent_states)

    def _check_pending_sync(
        self,
        agents: dict[str, SessionContext],
        agent_states: dict[str, str],
    ) -> list[dict]:
        """Synchronous helper: query DB for ready meetings."""
        try:
            db = get_client()
            result = (
                db.table("meetings")
                .select("*")
                .eq("sim_run_id", self.sim_run_id)
                .eq("status", "active")
                .eq("turn_count", 0)
                .execute()
            )
            meetings = result.data or []

            ready = []
            for m in meetings:
                role_a = m.get("participant_a_role_id", "")
                role_b = m.get("participant_b_role_id", "")

                # Both must be known agents
                if role_a not in agents or role_b not in agents:
                    continue

                # Both must be IDLE
                if agent_states.get(role_a) != "IDLE":
                    continue
                if agent_states.get(role_b) != "IDLE":
                    continue

                ready.append(m)

            logger.info(
                "[conversations] Found %d ready meetings out of %d active",
                len(ready), len(meetings),
            )
            return ready

        except Exception as e:
            logger.warning("[conversations] Failed to check pending meetings: %s", e)
            return []

    # ------------------------------------------------------------------
    # Meeting execution
    # ------------------------------------------------------------------

    async def run_meeting(
        self,
        meeting_id: str,
        agent_a: SessionContext,
        agent_b: SessionContext,
        agent_states: dict[str, str],
        round_num: int,
        max_turns: int = 8,
    ) -> dict:
        """Run a bilateral meeting between two agents.

        Sets both to IN_MEETING, relays messages turn-by-turn,
        writes to meeting_messages table, ends when turn limit
        reached or agent ends meeting.

        Args:
            meeting_id: UUID of the meeting row.
            agent_a: The inviter's session context.
            agent_b: The invitee's session context.
            agent_states: Shared dict (modified in place).
            round_num: Current round number.
            max_turns: Maximum messages per side.

        Returns:
            Meeting summary dict.
        """
        # Set both busy (routed through dispatcher when available)
        self._set_agent_state(agent_states, agent_a.role_id, "IN_MEETING")
        self._set_agent_state(agent_states, agent_b.role_id, "IN_MEETING")

        logger.info(
            "[conversations] Starting meeting %s: %s vs %s",
            meeting_id, agent_a.role_id, agent_b.role_id,
        )

        # Get meeting details
        meeting_data = get_meeting(meeting_id)
        if not meeting_data:
            logger.error("[conversations] Meeting %s not found", meeting_id)
            self._set_agent_state(agent_states, agent_a.role_id, "IDLE")
            self._set_agent_state(agent_states, agent_b.role_id, "IDLE")
            return {"meeting_id": meeting_id, "error": "Meeting not found", "turns": 0}

        meeting = meeting_data["meeting"]
        agenda = meeting.get("agenda") or "General discussion"

        # Resolve display names for each agent
        name_a = self._resolve_display_name(agent_a)
        name_b = self._resolve_display_name(agent_b)

        rules = MEETING_RULES_TEMPLATE.format(max_turns=max_turns)

        # Notify Agent A (inviter speaks first)
        opening_a = (
            f"Meeting started with {name_b} ({agent_b.country_code}). "
            f"Agenda: {agenda}. You speak first. Keep messages short (1-3 sentences).\n\n"
            f"{rules}"
        )

        # Turn-by-turn relay
        speaker = agent_a
        listener = agent_b
        speaker_name = name_a
        listener_name = name_b
        turns_a = 0
        turns_b = 0
        total_turns = 0
        end_reason = "turn_limit"
        messages_log: list[dict] = []

        # Send opening to agent A and get first message
        try:
            first_msg = await self._relay_turn(
                meeting_id=meeting_id,
                speaker=speaker,
                speaker_name=speaker_name,
                listener_name=listener_name,
                turn_num=1,
                prompt_prefix=opening_a,
            )
        except Exception as e:
            logger.error("[conversations] First turn failed: %s", e)
            first_msg = None

        if first_msg is None:
            # Agent A failed to respond — abort meeting
            end_reason = "speaker_error"
            await self._end_meeting_safe(meeting_id, agent_a.role_id, end_reason)
            self._set_agent_state(agent_states, agent_a.role_id, "IDLE")
            self._set_agent_state(agent_states, agent_b.role_id, "IDLE")
            return {
                "meeting_id": meeting_id,
                "turns": 0,
                "end_reason": end_reason,
                "messages": [],
            }

        turns_a += 1
        total_turns += 1
        messages_log.append(first_msg)

        # Check for early end
        if self._wants_to_end(first_msg.get("content", "")):
            end_reason = "ended_by_speaker"
            await self._end_meeting_safe(meeting_id, agent_a.role_id, end_reason)
            self._set_agent_state(agent_states, agent_a.role_id, "IDLE")
            self._set_agent_state(agent_states, agent_b.role_id, "IDLE")
            return {
                "meeting_id": meeting_id,
                "turns": total_turns,
                "end_reason": end_reason,
                "messages": messages_log,
            }

        # Swap: now listener becomes speaker
        speaker, listener = listener, speaker
        speaker_name, listener_name = listener_name, speaker_name

        # Relay loop: up to (max_turns * 2 - 1) remaining turns
        max_total = max_turns * 2
        for turn_idx in range(2, max_total + 1):
            # Check per-side limit
            if speaker is agent_a and turns_a >= max_turns:
                end_reason = "turn_limit"
                break
            if speaker is agent_b and turns_b >= max_turns:
                end_reason = "turn_limit"
                break

            # Build prompt: relay previous message from the other side
            prev_content = messages_log[-1].get("content", "")
            if turn_idx == 2:
                # First message to listener — include context + rules
                relay_prompt = (
                    f"Meeting started with {listener_name} ({listener.country_code}). "
                    f"Agenda: {agenda}.\n\n{rules}\n\n"
                    f"{listener_name} says: \"{prev_content}\""
                )
            else:
                relay_prompt = f"{listener_name} says: \"{prev_content}\""

            try:
                msg = await self._relay_turn(
                    meeting_id=meeting_id,
                    speaker=speaker,
                    speaker_name=speaker_name,
                    listener_name=listener_name,
                    turn_num=turn_idx,
                    prompt_prefix=relay_prompt,
                )
            except Exception as e:
                logger.error(
                    "[conversations] Turn %d failed for %s: %s",
                    turn_idx, speaker.role_id, e,
                )
                end_reason = "speaker_error"
                break

            if msg is None:
                # Session died mid-meeting
                end_reason = "session_error"
                break

            if speaker is agent_a:
                turns_a += 1
            else:
                turns_b += 1
            total_turns += 1
            messages_log.append(msg)

            # Check for [END MEETING]
            if self._wants_to_end(msg.get("content", "")):
                end_reason = f"ended_by_{speaker.role_id}"
                break

            # Swap
            speaker, listener = listener, speaker
            speaker_name, listener_name = listener_name, speaker_name

        # End meeting
        await self._end_meeting_safe(meeting_id, agent_a.role_id, end_reason)

        # Return both agents to IDLE (routed through dispatcher)
        self._set_agent_state(agent_states, agent_a.role_id, "IDLE")
        self._set_agent_state(agent_states, agent_b.role_id, "IDLE")

        # Log to observatory
        write_agent_log_event(
            self.sim_run_id, agent_a.country_code, round_num,
            event_type="meeting_completed",
            title=f"Meeting: {name_a} x {name_b}",
            description=(
                f"{total_turns} turns, ended: {end_reason}. "
                f"Agenda: {agenda}"
            ),
            metadata={
                "meeting_id": meeting_id,
                "participants": [agent_a.role_id, agent_b.role_id],
                "turns": total_turns,
                "end_reason": end_reason,
            },
        )

        logger.info(
            "[conversations] Meeting %s ended: %d turns, reason=%s",
            meeting_id, total_turns, end_reason,
        )

        return {
            "meeting_id": meeting_id,
            "participant_a": agent_a.role_id,
            "participant_b": agent_b.role_id,
            "turns": total_turns,
            "turns_a": turns_a,
            "turns_b": turns_b,
            "end_reason": end_reason,
            "agenda": agenda,
            "messages": messages_log,
        }

    # ------------------------------------------------------------------
    # Single turn relay
    # ------------------------------------------------------------------

    async def _relay_turn(
        self,
        meeting_id: str,
        speaker: SessionContext,
        speaker_name: str,
        listener_name: str,
        turn_num: int,
        prompt_prefix: str,
    ) -> dict | None:
        """Send a prompt to the speaker, capture their message, write to DB.

        The speaker receives the prompt and responds with text. We extract
        the agent's text response and write it to meeting_messages.

        Args:
            meeting_id: Meeting UUID.
            speaker: The agent session that should speak.
            speaker_name: Display name for the speaker.
            listener_name: Display name for the listener (unused in prompt
                but available for logging).
            turn_num: Turn number in the meeting.
            prompt_prefix: The full prompt to send to the speaker.

        Returns:
            Dict with role_id, country_code, content, turn_num.
            None if the speaker's session is dead or unresponsive.
        """
        # Health check before sending (async)
        health = await self.session_manager.health_check(speaker)
        if health == "terminated":
            logger.warning(
                "[conversations] Speaker %s session terminated mid-meeting",
                speaker.role_id,
            )
            return None

        # Send event (async — no threads)
        try:
            transcript = await self.session_manager.send_event(speaker, prompt_prefix)
        except Exception as e:
            logger.error(
                "[conversations] send_event failed for %s: %s",
                speaker.role_id, e,
            )
            return None

        # Extract the agent's text message from transcript
        message_text = self._extract_agent_message(transcript)
        if not message_text:
            logger.warning(
                "[conversations] No text response from %s on turn %d",
                speaker.role_id, turn_num,
            )
            # Use a fallback so the conversation can continue
            message_text = "..."

        # Write to meeting_messages table (shared with human chat UI)
        result = send_message(
            meeting_id=meeting_id,
            role_id=speaker.role_id,
            country_code=speaker.country_code,
            content=message_text,
        )

        if not result.get("success"):
            logger.warning(
                "[conversations] send_message DB write failed: %s",
                result.get("narrative", "unknown"),
            )

        return {
            "role_id": speaker.role_id,
            "country_code": speaker.country_code,
            "content": message_text,
            "turn_num": turn_num,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_agent_message(transcript: list[dict]) -> str:
        """Extract the last agent text message from a transcript.

        The agent may use tools during its turn (reading notes, etc.)
        but we care about the final text message it produces.
        """
        # Walk backwards to find the last agent_message
        for entry in reversed(transcript):
            if entry.get("type") == "agent_message":
                text = entry.get("content", "").strip()
                if text:
                    return text[:2000]  # Cap length
        return ""

    @staticmethod
    def _wants_to_end(content: str) -> bool:
        """Check if the agent's message contains the end-meeting marker."""
        return END_MEETING_MARKER in content.upper()

    @staticmethod
    def _resolve_display_name(ctx: SessionContext) -> str:
        """Build a display name from session context.

        Uses role_id as fallback if no character_name is available.
        The format used is: 'RoleId (country_code)' simplified to
        the role_id portion before any underscore.
        """
        # role_id is like "dealer" or "columbia_hos" — use as-is
        # In a real run, the orchestrator could pass character names
        # but for now we capitalize the role_id
        return ctx.role_id.replace("_", " ").title()

    async def _end_meeting_safe(
        self, meeting_id: str, role_id: str, reason: str
    ) -> None:
        """End a meeting, catching any errors."""
        try:
            # Sync DB call — fast (<100ms), no need for executor
            end_meeting(meeting_id, role_id)
            logger.info(
                "[conversations] Meeting %s ended (reason=%s, ended_by=%s)",
                meeting_id, reason, role_id,
            )
        except Exception as e:
            logger.warning(
                "[conversations] Failed to end meeting %s: %s",
                meeting_id, e,
            )
