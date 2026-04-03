"""Bilateral conversation engine — AI agent-to-agent dialogue.

Implements the conversation flow from SEED E5 Section 6 and DET_C1 C6 Section 5.5:
1. Intent note generation (private, per agent)
2. Turn-by-turn dialogue (max 8 turns)
3. Post-conversation reflection (both agents update blocks)

Source: SEED_E5_AI_PARTICIPANT_MODULE_v1.md, DET_C1 C6
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

END_MARKER = "[END CONVERSATION]"


@dataclass
class ConversationResult:
    """Output of a bilateral conversation."""
    transcript: list[dict] = field(default_factory=list)  # [{speaker_role_id, text}]
    turns: int = 0
    ended_by: str = ""  # role_id or "max_turns"
    intent_notes: dict = field(default_factory=dict)  # {role_a: str, role_b: str} — moderator-only
    reflections: dict = field(default_factory=dict)  # {role_a: dict, role_b: dict}


# ---------------------------------------------------------------------------
# System prompt template for conversation turns
# ---------------------------------------------------------------------------

CONVERSATION_SYSTEM_TEMPLATE = """You are {character_name}, {title} of {country_name}.

{block_2_identity}

YOU ARE IN A PRIVATE BILATERAL MEETING with {counterpart_name}, {counterpart_title} of {counterpart_country}.

ABSOLUTE RULE: Use ONLY SIM names. Never real-world names. Columbia not USA, Cathay not China, Sarmatia not Russia, Teutonia not Germany, etc. Call leaders by character names (Dealer, Helmsman, Forge, etc.).

HOW TO CONDUCT THIS MEETING:
- You have a maximum of 4 messages. Plan accordingly — don't waste turns.
- TURN 1: State your position or ask your key question. Get to the point.
- TURNS 2-3: Negotiate, probe, respond. Seek concrete commitments.
- TURN 4 (if needed): Summarize what was agreed or disagree clearly. Close.
- End EARLIER if you got what you needed or it's going nowhere.
- To end the conversation: include [END] at the end of your message.

HOW TO SPEAK:
- Like a real leader, not an AI. Short, direct sentences.
- Make concrete proposals: "I propose we coordinate L2 tariffs on Cathay — will you join?"
- Ask direct questions: "Will you commit troops if Formosa is blockaded?"
- React genuinely: agree, push back, express concern, counter-offer.
- NEVER summarize your reasoning process out loud. Just SPEAK.
- NEVER say "As the leader of..." — you ARE the leader. Just talk.

WHAT NOT TO DO:
- Don't monologue. Keep messages under 100 words.
- Don't be agreeable when your interests diverge — push back.
- Don't reveal everything at once. Hold cards back.
- Don't repeat what was just said.
- Don't use assistant language ("Great point", "I appreciate your perspective").

YOUR PRIVATE INTENT (never reveal):
{intent_notes}

YOUR MEMORY:
{memory_highlights}

YOUR GOALS:
{goals_highlights}
"""

# ---------------------------------------------------------------------------
# Intent note generation prompt
# ---------------------------------------------------------------------------

INTENT_NOTE_PROMPT = """You are about to have a private bilateral meeting with {counterpart_name}, {counterpart_title} of {counterpart_country}.

YOUR IDENTITY:
{block_2_identity}

YOUR MEMORY:
{memory_highlights}

YOUR GOALS:
{goals_highlights}

YOUR RELATIONSHIP WITH {counterpart_name}:
{relationship_info}

Write your PRIVATE INTENT NOTES for this conversation (3-5 bullet points):
1. What do you want to accomplish in this meeting?
2. What are you willing to share? What will you withhold?
3. What is your approach/tone? (assertive, conciliatory, probing, etc.)
4. What are your red lines — things you will NOT agree to?
5. What do you want to learn from the other side?

Be specific and strategic. These notes are private — the other person will not see them."""


class ConversationEngine:
    """Manages bilateral conversations between two AI agents."""

    async def generate_intent_note(
        self,
        agent,  # LeaderAgent
        counterpart,  # LeaderAgent
    ) -> str:
        """Generate private intent notes for an agent before a conversation.

        Args:
            agent: The agent generating intent notes.
            counterpart: The agent they will be speaking with.

        Returns:
            Intent notes as a string.
        """
        from engine.services.llm import call_llm
        from engine.config.settings import LLMUseCase

        # Build relationship context
        rel_score = agent.cognitive.block3_memory["relationships"].get(
            counterpart.role_id, 0.0
        )
        rel_label = _trust_label(rel_score)
        convos = [
            c for c in agent.cognitive.block3_memory["conversations_this_round"]
            if c["with"] == counterpart.role_id
        ]
        rel_info = f"Trust: {rel_score:+.1f} ({rel_label})"
        if convos:
            rel_info += f"\nRecent interactions: {'; '.join(c['summary'] for c in convos[-2:])}"

        prompt = INTENT_NOTE_PROMPT.format(
            counterpart_name=counterpart.role["character_name"],
            counterpart_title=counterpart.role["title"],
            counterpart_country=counterpart.country["sim_name"],
            block_2_identity=agent.cognitive.block2_identity,
            memory_highlights=agent.cognitive.get_memory_text(),
            goals_highlights=agent.cognitive.get_goals_text(),
            relationship_info=rel_info,
        )

        response = await call_llm(
            use_case=LLMUseCase.AGENT_REFLECTION,
            messages=[{"role": "user", "content": prompt}],
            system=(
                f"You are {agent.role['character_name']}. "
                f"Generate concise, strategic intent notes for an upcoming meeting. "
                f"Write as bullet points. Be specific."
            ),
            max_tokens=400,
            temperature=0.5,
        )
        return response.text

    async def run_bilateral(
        self,
        agent_a,  # LeaderAgent
        agent_b,  # LeaderAgent
        max_turns: int = 8,
        on_turn: Any = None,  # async callback(turn_data) for live streaming
        topic: str = "",
    ) -> ConversationResult:
        """Run a full bilateral conversation between two agents.

        Args:
            agent_a: Initiating agent.
            agent_b: Responding agent.
            max_turns: Maximum total turns (both sides combined).
            topic: Optional topic hint for the opening message.

        Returns:
            ConversationResult with transcript, reflections, etc.
        """
        result = ConversationResult()

        # Step 1: Generate intent notes (parallel)
        logger.info(
            "Bilateral: %s (%s) <-> %s (%s) — generating intent notes",
            agent_a.role_id, agent_a.role["character_name"],
            agent_b.role_id, agent_b.role["character_name"],
        )
        import asyncio
        intent_a, intent_b = await asyncio.gather(
            self.generate_intent_note(agent_a, agent_b),
            self.generate_intent_note(agent_b, agent_a),
        )
        result.intent_notes = {
            agent_a.role_id: intent_a,
            agent_b.role_id: intent_b,
        }
        logger.info("Intent notes generated for both agents")

        # Step 2: Turn-by-turn conversation
        transcript: list[dict] = []
        speakers = [agent_a, agent_b]
        intents = [intent_a, intent_b]
        listeners = [agent_b, agent_a]

        for turn_num in range(max_turns):
            idx = turn_num % 2
            speaker = speakers[idx]
            listener = listeners[idx]
            intent = intents[idx]

            # Add topic hint for first message
            extra_context = ""
            if turn_num == 0 and topic:
                extra_context = f"\n\nYou initiated this meeting to discuss: {topic}"

            turn = await self._generate_turn(
                speaker=speaker,
                listener=listener,
                transcript=transcript,
                intent=intent,
                extra_context=extra_context,
            )

            turn_data = {
                "speaker_role_id": speaker.role_id,
                "speaker_name": speaker.role["character_name"],
                "text": turn["text"],
                "turn": turn_num + 1,
            }
            transcript.append(turn_data)

            # Live streaming callback
            if on_turn is not None:
                try:
                    if asyncio.iscoroutinefunction(on_turn):
                        await on_turn(turn_data)
                    else:
                        on_turn(turn_data)
                except Exception:
                    pass  # Don't break conversation if callback fails

            logger.info(
                "Turn %d: %s (%d words)%s",
                turn_num + 1,
                speaker.role["character_name"],
                len(turn["text"].split()),
                " [ENDED]" if turn["end_conversation"] else "",
            )

            if turn["end_conversation"]:
                result.ended_by = speaker.role_id
                break
        else:
            result.ended_by = "max_turns"

        result.transcript = transcript
        result.turns = len(transcript)

        # Step 3: Post-conversation reflection (both agents, parallel)
        logger.info("Bilateral complete (%d turns). Reflecting...", result.turns)
        reflections = await self._reflect_both(
            agent_a, agent_b, transcript, intent_a, intent_b,
        )
        result.reflections = reflections

        logger.info(
            "Bilateral %s <-> %s complete: %d turns, ended_by=%s",
            agent_a.role_id, agent_b.role_id, result.turns, result.ended_by,
        )
        return result

    async def _generate_turn(
        self,
        speaker,  # LeaderAgent
        listener,  # LeaderAgent
        transcript: list[dict],
        intent: str,
        extra_context: str = "",
    ) -> dict:
        """Generate one conversation turn for the speaker.

        Returns:
            dict with 'text' and 'end_conversation' boolean.
        """
        from engine.services.llm import call_llm
        from engine.config.settings import LLMUseCase

        # Build system prompt
        system = CONVERSATION_SYSTEM_TEMPLATE.format(
            character_name=speaker.role["character_name"],
            title=speaker.role["title"],
            country_name=speaker.country["sim_name"],
            block_2_identity=speaker.cognitive.block2_identity,
            counterpart_name=listener.role["character_name"],
            counterpart_title=listener.role["title"],
            counterpart_country=listener.country["sim_name"],
            intent_notes=intent,
            memory_highlights=speaker.cognitive.get_memory_text(),
            goals_highlights=speaker.cognitive.get_goals_text(),
        )

        if extra_context:
            system += extra_context

        # Build message history from transcript
        messages = _transcript_to_messages(transcript, speaker.role_id)

        # If this is the first turn (no messages yet), add a prompt
        if not messages:
            messages = [{"role": "user", "content": (
                f"You are starting a private bilateral meeting with "
                f"{listener.role['character_name']}, {listener.role['title']} of "
                f"{listener.country['sim_name']}. "
                f"Open the conversation. Be direct and purposeful."
            )}]

        response = await call_llm(
            use_case=LLMUseCase.AGENT_CONVERSATION,
            messages=messages,
            system=system,
            max_tokens=300,
            temperature=0.8,
        )

        text = response.text.strip()
        end_conversation = END_MARKER in text

        # Clean up the end marker from displayed text
        clean_text = text.replace(END_MARKER, "").strip()

        return {
            "text": clean_text,
            "end_conversation": end_conversation,
        }

    async def _reflect_both(
        self,
        agent_a,  # LeaderAgent
        agent_b,  # LeaderAgent
        transcript: list[dict],
        intent_a: str,
        intent_b: str,
    ) -> dict:
        """Run post-conversation reflection for both agents (parallel).

        Uses the existing end_conversation pattern from LeaderAgent.

        Returns:
            dict with agent role_ids as keys and reflection results as values.
        """
        import asyncio

        # Build transcript text
        transcript_text = _format_transcript(transcript)

        result_a, result_b = await asyncio.gather(
            self._reflect_single(agent_a, agent_b, transcript_text, intent_a),
            self._reflect_single(agent_b, agent_a, transcript_text, intent_b),
        )

        return {
            agent_a.role_id: result_a,
            agent_b.role_id: result_b,
        }

    async def _reflect_single(
        self,
        agent,  # LeaderAgent — the one reflecting
        counterpart,  # LeaderAgent — the other side
        transcript_text: str,
        intent: str,
    ) -> dict:
        """Post-conversation reflection for a single agent.

        Updates the agent's cognitive blocks (Block 3 memory, optionally Block 4 goals).
        Mirrors the end_conversation() pattern in LeaderAgent.
        """
        from engine.services.llm import call_llm
        from engine.config.settings import LLMUseCase

        counterpart_name = counterpart.role["character_name"]
        counterpart_id = counterpart.role_id

        reflection_prompt = (
            f"You just finished a bilateral meeting with {counterpart_name}, "
            f"{counterpart.role['title']} of {counterpart.country['sim_name']}.\n\n"
            f"YOUR INTENT GOING IN:\n{intent}\n\n"
            f"TRANSCRIPT:\n{transcript_text}\n\n"
            f"YOUR CURRENT MEMORY (Block 3):\n{agent.cognitive.get_memory_text()}\n\n"
            f"YOUR CURRENT GOALS (Block 4):\n{agent.cognitive.get_goals_text()}\n\n"
            f"REFLECT on this conversation. Return a JSON object:\n"
            f'{{\n'
            f'  "memory_update": "What to add to your memory (1-3 sentences of what matters strategically. null if nothing worth remembering)",\n'
            f'  "relationship_change": 0.0,  // -0.3 to +0.3 trust change with counterpart\n'
            f'  "goals_update": "Any adjustment to your goals/priorities (null if no change)",\n'
            f'  "assessment": "Brief assessment: did you achieve your intent? What did you learn?"\n'
            f'}}\n\n'
            f"Be selective. Focus on what's strategically significant. "
            f"Return ONLY valid JSON."
        )

        try:
            reflection = await call_llm(
                use_case=LLMUseCase.AGENT_REFLECTION,
                messages=[{"role": "user", "content": reflection_prompt}],
                system=(
                    f"You are {agent.role['character_name']}. "
                    f"Reflect on this bilateral meeting and decide what to update. "
                    f"Return JSON only."
                ),
                max_tokens=500,
                temperature=0.3,
            )
            updates = agent._parse_reflection(reflection.text, counterpart_id)
        except Exception as e:
            logger.warning("Reflection failed for %s: %s", agent.role_id, e)
            updates = {
                "memory_update": f"Bilateral meeting with {counterpart_name}.",
                "relationship_change": 0.0,
                "goals_update": None,
                "assessment": None,
            }

        # Apply updates to cognitive blocks
        updated_blocks = []

        if updates.get("memory_update"):
            agent.cognitive.add_conversation(
                counterpart=counterpart_id,
                summary=updates["memory_update"],
                trust_change=updates.get("relationship_change", 0.0),
            )
            updated_blocks.append("block3_memory")

        if updates.get("goals_update"):
            current_goals = agent.cognitive.get_goals_text()
            new_goals = (
                f"{current_goals}\n\n"
                f"[Updated after bilateral with {counterpart_name}]:\n"
                f"{updates['goals_update']}"
            )
            agent.cognitive.update_goals_text(
                new_goals, reason=f"bilateral_with_{counterpart_id}",
            )
            updated_blocks.append("block4_goals")

        logger.info(
            "Reflection for %s after bilateral with %s: updated %s",
            agent.role_id, counterpart_id, updated_blocks,
        )

        return {
            "updated": updated_blocks,
            "details": updates,
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _transcript_to_messages(
    transcript: list[dict], speaker_role_id: str,
) -> list[dict]:
    """Convert transcript to LLM message format from speaker's perspective.

    Speaker's own messages become 'assistant', counterpart's become 'user'.
    """
    messages = []
    for entry in transcript:
        if entry["speaker_role_id"] == speaker_role_id:
            role = "assistant"
        else:
            role = "user"
        messages.append({
            "role": role,
            "content": entry["text"],
        })
    return messages


def _format_transcript(transcript: list[dict]) -> str:
    """Format transcript as readable text for reflection prompts."""
    lines = []
    for entry in transcript:
        lines.append(f"{entry['speaker_name']}: {entry['text']}")
    return "\n\n".join(lines)


def _trust_label(score: float) -> str:
    """Convert trust score to human-readable label."""
    if score > 0.5:
        return "ally"
    elif score > 0.2:
        return "friendly"
    elif score > -0.2:
        return "neutral"
    elif score > -0.5:
        return "tense"
    else:
        return "hostile"
