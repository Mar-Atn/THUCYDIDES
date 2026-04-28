"""Avatar Conversation Service — fast text chat via Claude Messages API.

Replaces the slow ConversationRouter (30-60s/turn via Managed Agent SSE)
with direct Claude API calls (~1-3s/turn). The avatar is a lightweight
conversation agent with cached system prompt and no tool calls.

Architecture: SPEC_M5_AVATAR_CONVERSATIONS.md
"""
from __future__ import annotations

import asyncio
import logging
import os

from anthropic import AsyncAnthropic

from engine.agents.managed.ai_config import get_ai_model
from engine.agents.managed.event_handler import write_agent_log_event
from engine.services.meeting_service import send_message
from engine.config.settings import settings

logger = logging.getLogger(__name__)

# Marker the agent can use to end a meeting early (shared with conversations.py)
END_MEETING_MARKER = "[END MEETING]"

TEXT_CHAT_RULES = (
    "You are in a live text conversation. You are a head of state, not an AI.\n"
    "\n"
    "CHAT RULES:\n"
    "- 1-3 sentences per message. This is messaging, not speechwriting.\n"
    "- React emotionally BEFORE logic. If surprised, show it.\n"
    "- Vary your energy. Not every message same intensity.\n"
    "- If you disagree, say so directly.\n"
    '- NEVER say "That\'s a great question", "I appreciate your perspective", '
    'or "Let me elaborate."\n'
    "- Write as a real person would text — direct, sometimes incomplete, human.\n"
    f"- To end the meeting early, say: {END_MEETING_MARKER}"
)

# Shared async client — lazy init
_client: AsyncAnthropic | None = None


def _get_client() -> AsyncAnthropic:
    """Get or create the shared AsyncAnthropic client."""
    global _client
    if _client is None:
        api_key = settings.anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY")
        _client = AsyncAnthropic(api_key=api_key)
    return _client


def build_avatar_system_prompt(
    avatar_identity: str,
    intent_note: str,
    rules: str = TEXT_CHAT_RULES,
) -> str:
    """Assemble the full system prompt from avatar identity + intent note + rules.

    The intent note is the Brain's complete briefing for this meeting —
    it includes who the counterpart is, objectives, approach, boundaries.
    No additional counterpart info injected by the system (M5.7 SPEC 3.2).

    Args:
        avatar_identity: Persistent identity document.
        intent_note: Per-meeting tactical briefing (includes counterpart info).
        rules: Chat behavior rules (defaults to TEXT_CHAT_RULES).

    Returns:
        Combined system prompt string.
    """
    return (
        f"=== YOUR IDENTITY ===\n{avatar_identity}\n\n"
        f"=== MEETING BRIEFING ===\n{intent_note}\n\n"
        f"=== RULES ===\n{rules}"
    )


async def text_avatar_turn(
    avatar_identity: str,
    intent_note: str,
    conversation_history: list[dict[str, str]],
    model: str | None = None,
) -> str:
    """Execute a single conversation turn via the Claude Messages API.

    Builds a system prompt from the avatar identity + intent note +
    chat rules, then calls the API with prompt caching enabled.

    Args:
        avatar_identity: The avatar's persistent identity document.
        intent_note: Per-meeting tactical briefing (includes counterpart info).
        conversation_history: List of {"role": "user"|"assistant", "content": str}.
        model: Model ID override. Defaults to ai_config conversations model.

    Returns:
        The avatar's response text.
    """
    if model is None:
        model = get_ai_model("conversations")

    system_prompt = build_avatar_system_prompt(avatar_identity, intent_note)
    client = _get_client()

    response = await asyncio.wait_for(
        client.messages.create(
            model=model,
            max_tokens=300,
            system=[
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=conversation_history,
        ),
        timeout=30.0,
    )

    # Extract text from response
    text = ""
    for block in response.content:
        if block.type == "text":
            text += block.text

    return text.strip()


async def run_text_meeting(
    meeting_id: str,
    agent_a_identity: str,
    agent_a_intent: str,
    agent_a_role_id: str,
    agent_a_country: str,
    agent_b_identity: str,
    agent_b_intent: str,
    agent_b_role_id: str,
    agent_b_country: str,
    sim_run_id: str = "",
    round_num: int = 0,
    max_turns: int = 16,
) -> str:
    """Run a full AI-AI text meeting via avatar turns.

    Alternates between agent A and agent B, writing each message
    to the meeting_messages table via meeting_service.send_message().

    Args:
        meeting_id: UUID of the meeting row.
        agent_a_identity: Agent A's avatar identity document.
        agent_a_intent: Agent A's intent note for this meeting.
        agent_a_role_id: Agent A's role ID.
        agent_a_country: Agent A's country code.
        agent_b_identity: Agent B's avatar identity document.
        agent_b_intent: Agent B's intent note for this meeting.
        agent_b_role_id: Agent B's role ID.
        agent_b_country: Agent B's country code.
        sim_run_id: SIM run UUID (for observatory logging).
        round_num: Current round number (for observatory logging).
        max_turns: Maximum total messages (both sides combined).

    Returns:
        Formatted transcript string.
    """
    # Conversation histories — what each avatar "sees"
    # Agent A sees its own messages as "assistant" and B's as "user"
    history_a: list[dict[str, str]] = []
    history_b: list[dict[str, str]] = []

    transcript_lines: list[str] = []
    total_turns = 0
    end_reason = "turn_limit"

    # Agent A speaks first
    speakers = [
        {
            "identity": agent_a_identity,
            "intent": agent_a_intent,
            "role_id": agent_a_role_id,
            "country": agent_a_country,
            "history": history_a,
            "other_history": history_b,
        },
        {
            "identity": agent_b_identity,
            "intent": agent_b_intent,
            "role_id": agent_b_role_id,
            "country": agent_b_country,
            "history": history_b,
            "other_history": history_a,
        },
    ]

    for turn_idx in range(max_turns):
        speaker = speakers[turn_idx % 2]

        # First turn: seed with a user message (Claude API requires non-empty messages)
        history = speaker["history"]
        if not history:
            history = [{"role": "user", "content": "The meeting has started. Begin the conversation."}]

        try:
            response_text = await text_avatar_turn(
                avatar_identity=speaker["identity"],
                intent_note=speaker["intent"],
                conversation_history=history,
            )
        except Exception as e:
            logger.error(
                "[avatar] Turn %d failed for %s: %s",
                turn_idx + 1, speaker["role_id"], e,
            )
            end_reason = "api_error"
            break

        if not response_text:
            response_text = "..."

        # Write to DB via meeting_service
        result = send_message(
            meeting_id=meeting_id,
            role_id=speaker["role_id"],
            country_code=speaker["country"],
            content=response_text,
        )
        if not result.get("success"):
            logger.warning(
                "[avatar] send_message failed turn %d: %s",
                turn_idx + 1, result.get("narrative", "unknown"),
            )

        total_turns += 1

        # Update conversation histories
        # Speaker sees this as their own message ("assistant")
        speaker["history"].append({"role": "assistant", "content": response_text})
        # Listener sees this as incoming message ("user")
        speaker["other_history"].append({"role": "user", "content": response_text})

        # Build transcript
        transcript_lines.append(
            f"[{speaker['role_id']}] {response_text}"
        )

        # Check for early end
        if END_MEETING_MARKER in response_text.upper():
            end_reason = f"ended_by_{speaker['role_id']}"
            break

    transcript = "\n".join(transcript_lines)

    # Log to observatory
    if sim_run_id:
        write_agent_log_event(
            sim_run_id,
            agent_a_country,
            round_num,
            event_type="avatar_meeting_completed",
            title=f"Avatar Meeting: {agent_a_role_id} x {agent_b_role_id}",
            description=(
                f"{total_turns} turns, ended: {end_reason}"
            ),
            metadata={
                "meeting_id": meeting_id,
                "participants": [agent_a_role_id, agent_b_role_id],
                "turns": total_turns,
                "end_reason": end_reason,
            },
        )

    logger.info(
        "[avatar] Meeting %s completed: %d turns, reason=%s",
        meeting_id, total_turns, end_reason,
    )

    return transcript
