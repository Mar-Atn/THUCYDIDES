"""LeaderAgent — LLM-powered head of state implementing DET_C1 C6 interface.

4-block cognitive model (KING-style) with context caching.
Each method corresponds to the abstract interface defined in
DET_C1 PART 5 (AI Participant Abstract Interface).

Source: SEED_E5_AI_PARTICIPANT_MODULE_v1.md
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Optional

from engine.agents.profiles import (
    load_role, load_country_context, build_identity_prompt,
)
from engine.agents.memory import CognitiveState
from engine.agents.world_context import build_rich_block1

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# BLOCK 1: RULES (abbreviated — full rules in context assembly)
# ---------------------------------------------------------------------------

RULES_TEMPLATE = """# SIM Rules for {title} of {country_name}

You are {character_name}, {title} of {country_name}.
This is the Thucydides Trap — a geopolitical simulation with 21 countries, 6-8 rounds (~6 months each).

## CRITICAL: USE ONLY SIM NAMES
You live in the SIM world. NEVER use real-world country names.
- Your country is {country_name}, NOT {parallel}
- Use ONLY these SIM names: Columbia (not USA/America), Cathay (not China), Sarmatia (not Russia), Ruthenia (not Ukraine), Persia (not Iran), Teutonia (not Germany), Gallia (not France), Albion (not UK/Britain), Bharata (not India), Yamato (not Japan), Formosa (not Taiwan), Hanguk (not South Korea), Choson (not North Korea), Solaria (not Saudi Arabia), Freeland (not Poland), Ponte (not Italy), Phrygia (not Turkey), Mirage (not UAE), Caribe (not Cuba/Venezuela), Levantia (not Israel)
- Continent: Ereb (not Europe), Western Treaty (not NATO), Eastern Pact (not BRICS)
- Refer to other leaders by their CHARACTER NAMES (Dealer, Helmsman, Pathfinder, Beacon, etc.), never real-world names
- This is absolute. Any use of real-world names breaks immersion.

## Your Powers
{powers_list}

## Key Mechanics
- Budget: set social spending (0.5-1.5× baseline), military allocation, tech investment
- Tariffs: L0 (none) to L3 (heavy) per target country. Hurt both sides asymmetrically.
- Sanctions: L0-L3. Coalition-based. Cost imposer 30-50% of damage inflicted.
- Military: ground attack (needs co-sign), naval/air/blockade, strategic missiles
- Covert: espionage, sabotage, cyber, disinfo (limited by intelligence pool: {intel_pool})
- Transactions: arms sales, coin transfers, treaties, basing rights (bilateral, both confirm)
- Political: propaganda (+stability), repression (autocracy), public statements

## Your Objectives
{objectives_list}

## Ticking Clock
{ticking_clock}
"""


class LeaderAgent:
    """AI-powered head of state. Implements DET_C1 C6 abstract interface."""

    def __init__(self, role_id: str):
        self.role_id = role_id
        self.role: dict = {}
        self.country: dict = {}
        self.cognitive = CognitiveState(role_id)
        self.status: str = "uninitialized"  # uninitialized → idle → deciding → acting → busy → reflecting
        self._initialized = False
        self._conversation_history: list[dict] = []
        self._conversation_counterpart: str = ""

    # ------------------------------------------------------------------
    # DET_C1 C6: initialize()
    # ------------------------------------------------------------------

    async def initialize(self, sim_config: dict | None = None, world_state: dict | None = None):
        """Initialize agent: load role, generate identity, set up cognitive blocks.

        Args:
            sim_config: Optional SIM configuration overrides.
            world_state: Optional initial world state for relationship setup.
        """
        # Load role data
        self.role = load_role(self.role_id)
        self.country = load_country_context(self.role["country_code"])

        # Block 1: Rich SIM world context (roster, structure, geography, situation)
        metacog_override = (sim_config or {}).get("metacognitive_architecture") if sim_config else None
        rules = build_rich_block1(
            self.role_id,
            countries=None,
            world_state=world_state,
            metacognitive_override=metacog_override,
        )
        self.cognitive.set_rules(rules)

        # Block 2: Identity (LLM call)
        identity = await self._generate_identity()
        self.cognitive.set_identity(identity)

        # Block 3: Memory (initial relationships)
        self.cognitive.set_relationships(self._initial_relationships(world_state))

        # Block 4: Goals & Strategy (LLM-generated — rich strategic thinking)
        goals_text = await self._generate_goals()
        self.cognitive.set_goals_text(goals_text)

        self.status = "idle"
        self._initialized = True
        logger.info("Agent %s (%s) initialized — %s of %s",
                     self.role_id, self.role["character_name"],
                     self.role["title"], self.country["sim_name"])

    def initialize_sync(self, identity_text: str = "", world_state: dict | None = None):
        """Synchronous initialization (no LLM call — identity provided)."""
        self.role = load_role(self.role_id)
        self.country = load_country_context(self.role["country_code"])

        rules = build_rich_block1(
            self.role_id,
            countries=None,
            world_state=world_state,
        )
        self.cognitive.set_rules(rules)

        if identity_text:
            self.cognitive.set_identity(identity_text)
        else:
            self.cognitive.set_identity(
                f"You are {self.role['character_name']}, {self.role['title']} of {self.country['sim_name']}. "
                f"You are {self.role['age']} years old. Your objectives: {', '.join(self.role['objectives'])}."
            )

        self.cognitive.set_relationships(self._initial_relationships(world_state))

        # Block 4: simple default for sync (no LLM)
        self.cognitive.set_goals_text(
            f"OBJECTIVES:\n"
            + "\n".join(f"- {obj}" for obj in self.role["objectives"])
            + f"\n\nTICKING CLOCK: {self.role['ticking_clock']}\n\n"
            f"INITIAL STRATEGY: Assess the situation. Establish key relationships. "
            f"Prioritize {self.role['objectives'][0] if self.role['objectives'] else 'survival'}.\n\n"
            f"PLANS: To be developed based on initial assessment."
        )

        self.status = "idle"
        self._initialized = True

    # ------------------------------------------------------------------
    # DET_C1 C6: get_cognitive_state() / get_state_history()
    # ------------------------------------------------------------------

    def get_cognitive_state(self) -> dict:
        """Return current cognitive state (all 4 blocks)."""
        return self.cognitive.snapshot()

    def get_state_history(self) -> list[dict]:
        """Return all past versions of cognitive state."""
        return self.cognitive.get_history()

    # ------------------------------------------------------------------
    # DET_C1 C6: chat() — debug interface
    # ------------------------------------------------------------------

    async def chat(self, message: str) -> str:
        """One message within an ongoing conversation.

        The conversation history is maintained in self._conversation_history.
        Memory is NOT updated per message — only when end_conversation() is called.
        """
        from engine.services.llm import call_llm
        from engine.config.settings import LLMUseCase

        # Build system prompt from cognitive blocks
        system = (
            f"You are {self.role['character_name']}, {self.role['title']} of {self.country['sim_name']}. "
            f"Respond in character. Be strategic, direct, and authentic to your personality.\n\n"
            f"{self.cognitive.block2_identity}\n\n"
            f"{self.cognitive.get_memory_text()}\n\n"
            f"{self.cognitive.get_goals_text()}"
        )

        # Add to conversation history
        self._conversation_history.append({"role": "user", "content": message})

        response = await call_llm(
            use_case=LLMUseCase.AGENT_DECISION,
            messages=list(self._conversation_history),
            system=system,
            max_tokens=500,
            temperature=0.7,
        )
        agent_response = response.text

        # Add response to history (LLM sees full conversation next turn)
        self._conversation_history.append({"role": "assistant", "content": agent_response})

        return agent_response

    def start_conversation(self, counterpart: str = "human_operator"):
        """Begin a new conversation. Clears message history."""
        self._conversation_history = []
        self._conversation_counterpart = counterpart
        self.status = "busy"
        logger.info("Conversation started: %s with %s", self.role_id, counterpart)

    async def end_conversation(self) -> dict:
        """End conversation and reflect. Updates Blocks 2/3/4 as needed.

        Returns dict with what was updated.
        """
        from engine.services.llm import call_llm
        from engine.config.settings import LLMUseCase

        if not self._conversation_history:
            self.status = "idle"
            return {"updated": []}

        # Build transcript summary for reflection
        transcript = "\n".join(
            f"{'THEM' if m['role'] == 'user' else 'YOU'}: {m['content']}"
            for m in self._conversation_history
        )
        counterpart = getattr(self, '_conversation_counterpart', 'unknown')

        # Single reflection call — agent decides what to update
        reflection_prompt = (
            f"You just finished a conversation with {counterpart}.\n\n"
            f"TRANSCRIPT:\n{transcript}\n\n"
            f"YOUR CURRENT MEMORY (Block 3):\n{self.cognitive.get_memory_text()}\n\n"
            f"YOUR CURRENT GOALS (Block 4):\n{self.cognitive.get_goals_text()}\n\n"
            f"REFLECT on this conversation. Return a JSON object:\n"
            f'{{\n'
            f'  "memory_update": "What to add to your memory (1-3 sentences of what matters strategically. null if nothing worth remembering)",\n'
            f'  "relationship_change": 0.0,  // -0.3 to +0.3 trust change with counterpart\n'
            f'  "goals_update": "Any adjustment to your goals/priorities (null if no change)",\n'
            f'  "identity_update": "Only if something fundamental changed about who you are (almost always null)"\n'
            f'}}\n\n'
            f"Be selective. Not every conversation is worth remembering in full. "
            f"Return ONLY valid JSON."
        )

        try:
            reflection = await call_llm(
                use_case=LLMUseCase.AGENT_REFLECTION,
                messages=[{"role": "user", "content": reflection_prompt}],
                system=f"You are {self.role['character_name']}. Reflect on this conversation and decide what to update in your cognitive blocks. Return JSON only.",
                max_tokens=500,
                temperature=0.3,
            )
            updates = self._parse_reflection(reflection.text, counterpart)
        except Exception as e:
            logger.warning("Reflection failed for %s: %s", self.role_id, e)
            updates = {
                "memory_update": f"Spoke with {counterpart} about various matters.",
                "relationship_change": 0.0,
                "goals_update": None,
                "identity_update": None,
            }

        # Apply updates
        updated_blocks = []

        if updates.get("memory_update"):
            self.cognitive.add_conversation(
                counterpart=counterpart,
                summary=updates["memory_update"],
                trust_change=updates.get("relationship_change", 0.0),
            )
            updated_blocks.append("block3_memory")

        if updates.get("goals_update"):
            current_goals = self.cognitive.get_goals_text()
            new_goals = f"{current_goals}\n\n[Updated after conversation with {counterpart}]:\n{updates['goals_update']}"
            self.cognitive.update_goals_text(new_goals, reason=f"conversation_with_{counterpart}")
            updated_blocks.append("block4_goals")

        if updates.get("identity_update"):
            old_identity = self.cognitive.block2_identity
            self.cognitive.block2_identity = f"{old_identity}\n\n[Updated]: {updates['identity_update']}"
            self.cognitive.save_version(f"identity_shift_after_{counterpart}")
            updated_blocks.append("block2_identity")

        # Clear conversation history, return to idle
        self._conversation_history = []
        self.status = "idle"

        logger.info("Reflection complete for %s: updated %s", self.role_id, updated_blocks)
        return {
            "updated": updated_blocks,
            "details": updates,
        }

    def _parse_reflection(self, text: str, counterpart: str) -> dict:
        """Parse LLM reflection JSON output."""
        import json as _json
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        if text.startswith("json"):
            text = text[4:].strip()

        try:
            return _json.loads(text)
        except Exception:
            return {
                "memory_update": f"Spoke with {counterpart}.",
                "relationship_change": 0.0,
                "goals_update": None,
                "identity_update": None,
            }

    def chat_sync(self, message: str) -> str:
        """Synchronous chat (for testing without LLM)."""
        return (
            f"[{self.role['character_name']}, {self.role['title']} of {self.country['sim_name']}]\n"
            f"(Sync mode — no LLM call)\n"
            f"My priorities: {', '.join(self.role['objectives'][:3])}\n"
            f"Ticking clock: {self.role['ticking_clock']}\n"
            f"Your message: {message}"
        )

    # ------------------------------------------------------------------
    # DET_C1 C6: submit_mandatory_inputs()
    # ------------------------------------------------------------------

    async def submit_mandatory_inputs(self, round_context: dict) -> dict:
        """Produce round-end mandatory decisions (budget, tariffs, sanctions, OPEC, deployment).

        Uses decisions module to build task-specific context and call LLM for each decision type.
        """
        from engine.agents.decisions import submit_all_mandatory

        cognitive_blocks = self._get_cognitive_blocks()
        result = await submit_all_mandatory(cognitive_blocks, self.country, self.role, round_context)

        # Record decisions in memory
        self.cognitive.add_decision("budget", f"social={result['budget']['social_pct']:.2f}, mil={result['budget']['military_coins']:.0f}, tech={result['budget']['tech_coins']:.0f}")
        if result["tariffs"]:
            self.cognitive.add_decision("tariffs", f"changed: {result['tariffs']}")
        if result["sanctions"]:
            self.cognitive.add_decision("sanctions", f"changed: {result['sanctions']}")
        if result["opec_production"]:
            self.cognitive.add_decision("opec", f"production: {result['opec_production']}")

        return result

    # ------------------------------------------------------------------
    # DET_C1 C6: decide_action()
    # ------------------------------------------------------------------

    async def decide_action(self, time_remaining: float, new_events: list[dict],
                            round_context: dict | None = None) -> dict | None:
        """Proactive decision: what to do RIGHT NOW? Returns action or None (wait).

        Uses active loop to decide what to do, then dispatches to specific
        decision type (military, covert, conversation request, etc.).
        """
        from engine.agents.decisions import decide_action_dispatch

        cognitive_blocks = self._get_cognitive_blocks()
        ctx = round_context or {}
        result = await decide_action_dispatch(
            cognitive_blocks, self.country, self.role, ctx, time_remaining, new_events,
        )

        if result:
            self.cognitive.add_decision(result.get("type", "action"), result.get("detail", str(result)[:100]))

        return result

    # ------------------------------------------------------------------
    # DET_C1 C6: react_to_event()
    # ------------------------------------------------------------------

    async def react_to_event(self, event: dict) -> dict | None:
        """Handle an incoming event. Returns reaction action or None."""
        # TODO: Phase 3B of build plan
        return None

    # ------------------------------------------------------------------
    # DET_C1 C6: generate_conversation_message()
    # ------------------------------------------------------------------

    async def generate_conversation_message(self, conversation_context: dict) -> dict:
        """Produce next message in a bilateral conversation.

        Args:
            conversation_context: dict with keys:
                - counterpart_name, counterpart_title, counterpart_country
                - intent_notes: str (private)
                - transcript: list of {speaker_role_id, speaker_name, text}
                - extra_context: str (optional)

        Returns:
            dict with 'text', 'end_conversation'.
        """
        from engine.agents.conversations import ConversationEngine, _transcript_to_messages, CONVERSATION_SYSTEM_TEMPLATE, END_MARKER
        from engine.services.llm import call_llm
        from engine.config.settings import LLMUseCase

        system = CONVERSATION_SYSTEM_TEMPLATE.format(
            character_name=self.role["character_name"],
            title=self.role["title"],
            country_name=self.country["sim_name"],
            block_2_identity=self.cognitive.block2_identity,
            counterpart_name=conversation_context["counterpart_name"],
            counterpart_title=conversation_context["counterpart_title"],
            counterpart_country=conversation_context["counterpart_country"],
            intent_notes=conversation_context.get("intent_notes", ""),
            memory_highlights=self.cognitive.get_memory_text(),
            goals_highlights=self.cognitive.get_goals_text(),
        )

        extra = conversation_context.get("extra_context", "")
        if extra:
            system += extra

        messages = _transcript_to_messages(
            conversation_context.get("transcript", []), self.role_id,
        )
        if not messages:
            messages = [{"role": "user", "content": (
                f"You are starting a private bilateral meeting with "
                f"{conversation_context['counterpart_name']}. "
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
        clean_text = text.replace(END_MARKER, "").strip()

        return {"text": clean_text, "end_conversation": end_conversation}

    # ------------------------------------------------------------------
    # DET_C1 C6: evaluate_proposal()
    # ------------------------------------------------------------------

    async def evaluate_proposal(self, proposal, counterpart_context: dict | None = None) -> dict:
        """Accept, reject, or counter a transaction proposal.

        Args:
            proposal: TransactionProposal instance or dict.
            counterpart_context: Optional additional context (unused — agent uses own blocks).

        Returns:
            {decision: "accept"|"reject"|"counter", counter_terms: dict|None, reasoning: str}
        """
        from engine.agents.transactions import evaluate_transaction, TransactionProposal

        # Accept both dict and TransactionProposal
        if isinstance(proposal, dict):
            proposal = TransactionProposal(**proposal)

        cognitive_blocks = self._get_cognitive_blocks()
        result = await evaluate_transaction(
            cognitive_blocks=cognitive_blocks,
            agent_country=self.country,
            agent_role=self.role,
            proposal=proposal,
        )

        # Record in memory
        self.cognitive.add_decision(
            f"transaction_{result['decision']}",
            f"{result['decision'].upper()} {proposal.type} from {proposal.proposer_role_id}: {result.get('reasoning', '')[:80]}",
        )

        return result

    async def propose_transaction(self, counterpart, transaction_type: str | None = None,
                                   world_state: dict | None = None) -> dict:
        """Propose a transaction to another agent.

        Args:
            counterpart: LeaderAgent to propose to.
            transaction_type: Optional type hint.
            world_state: Current world state dict.

        Returns:
            TransactionProposal.to_dict()
        """
        from engine.agents.transactions import propose_transaction

        cognitive_blocks = self._get_cognitive_blocks()
        proposal = await propose_transaction(
            cognitive_blocks=cognitive_blocks,
            agent_country=self.country,
            agent_role=self.role,
            counterpart_country=counterpart.country,
            counterpart_role=counterpart.role,
            world_state=world_state or {},
            transaction_type=transaction_type,
        )

        self.cognitive.add_decision(
            "transaction_proposed",
            f"Proposed {proposal.type} to {counterpart.role_id}: {proposal.reasoning[:80]}",
        )

        return proposal.to_dict()

    # ------------------------------------------------------------------
    # DET_C1 C6: start_round() / reflect_on_round()
    # ------------------------------------------------------------------

    async def start_round(self, round_num: int, world_state_visible: dict, events_since_last: list[dict]):
        """Begin a new round. Update situational awareness.

        Args:
            round_num: Current round number.
            world_state_visible: World state visible to this agent.
            events_since_last: Events that happened since last round.
        """
        self.status = "idle"

        # Update immediate memory with round start info
        oil_price = world_state_visible.get("oil_price", "?")
        wars = world_state_visible.get("wars", [])
        self.cognitive.update_immediate(
            f"Round {round_num} starting. Oil: ${oil_price}. Wars: {len(wars)}."
        )

        # Add significant events to memory
        for event in events_since_last:
            summary = event.get("summary", str(event)[:100])
            self.cognitive.add_decision("event_received", summary)

        logger.info("Agent %s ready for round %d", self.role_id, round_num)

    async def reflect_on_round(self, round_results: dict):
        """Update internal state after round results arrive.

        Args:
            round_results: Engine results for this round.
        """
        from engine.services.llm import call_llm
        from engine.config.settings import LLMUseCase

        country_id = self.role.get("country_code", "")
        eco = round_results.get("economic_summary", {}).get(country_id, {})
        stab = round_results.get("stability", {}).get(country_id, {})
        supp = round_results.get("support", {}).get(country_id, {})
        oil = round_results.get("oil_price", "?")

        summary = (
            f"GDP growth {eco.get('growth', 0):.1%}, inflation {eco.get('inflation', 0):.1f}%, "
            f"stability {stab.get('new', '?')}, support {supp.get('new', '?')}%. Oil ${oil}."
        )

        try:
            response = await call_llm(
                use_case=LLMUseCase.AGENT_REFLECTION,
                messages=[{"role": "user", "content": (
                    f"Round results: {summary}\n\n"
                    f"Write 3-5 bullet points on what this means for your strategy."
                )}],
                system=(
                    f"You are {self.role.get('character_name', self.role_id)}. "
                    f"Briefly reflect on these results."
                ),
                max_tokens=300,
                temperature=0.5,
            )
            reflection = response.text
        except Exception as e:
            logger.warning("Reflection failed for %s: %s", self.role_id, e)
            reflection = f"Round completed. {summary}"

        # Update goals
        current_goals = self.cognitive.get_goals_text()
        self.cognitive.update_goals_text(
            f"{current_goals}\n\n[Post-Round Assessment]:\n{reflection}",
            reason="round_reflection",
        )

        self.status = "idle"
        logger.info("Agent %s reflected on round results", self.role_id)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _generate_goals(self) -> str:
        """Generate Block 4 goals & strategy via LLM."""
        from engine.services.llm import call_llm
        from engine.config.settings import LLMUseCase

        prompt = (
            f"You are {self.role['character_name']}, {self.role['title']} of {self.country['sim_name']} ({self.country['parallel']}).\n\n"
            f"YOUR IDENTITY:\n{self.cognitive.block2_identity}\n\n"
            f"YOUR OBJECTIVES (from role brief):\n"
            + "\n".join(f"- {obj}" for obj in self.role["objectives"])
            + f"\n\nYOUR TICKING CLOCK: {self.role['ticking_clock']}\n\n"
            f"YOUR COUNTRY:\n"
            f"- GDP: {self.country['gdp']} ({self.country['regime_type']})\n"
            f"- Stability: {self.country['stability']}\n"
            f"- Military: {self.country['mil_ground']} ground, {self.country['mil_naval']} naval, {self.country['mil_tactical_air']} air\n"
            f"- Nuclear L{self.country['nuclear_level']}, AI L{self.country['ai_level']}\n\n"
            f"Create your STRATEGIC BRIEF (Block 4). Write as plain text, ~400-600 words:\n\n"
            f"1. RANKED OBJECTIVES — your priorities in order, with urgency level and brief status assessment\n"
            f"2. CURRENT STRATEGY — how you plan to pursue your top 2-3 objectives. Be specific: who to talk to, what leverage to use, what sequence of actions\n"
            f"3. KEY RELATIONSHIPS — who are your allies, rivals, and unknowns? What do you need from each?\n"
            f"4. RISKS & CONTINGENCIES — what could go wrong? What's your fallback?\n"
            f"5. TIMELINE PRESSURE — what must happen by when? (relate to your ticking clock)\n\n"
            f"Write as a leader thinks — concrete, strategic, action-oriented. Not abstract."
        )

        response = await call_llm(
            use_case=LLMUseCase.AGENT_DECISION,
            messages=[{"role": "user", "content": prompt}],
            system="Generate a strategic goals brief for this leader. Write as plain text, structured but natural. Be specific and actionable.",
            max_tokens=800,
            temperature=0.7,
        )
        return response.text

    async def _generate_identity(self) -> str:
        """Generate Block 2 identity via LLM."""
        from engine.services.llm import call_llm
        from engine.config.settings import LLMUseCase

        prompt = build_identity_prompt(self.role, self.country)
        response = await call_llm(
            use_case=LLMUseCase.AGENT_DECISION,
            messages=[{"role": "user", "content": prompt}],
            system="Generate a vivid, specific character identity for a geopolitical simulation. Write in second person. 3-4 sentences.",
            max_tokens=300,
            temperature=0.85,
        )
        return response.text

    def _get_cognitive_blocks(self) -> dict:
        """Extract cognitive blocks as dict for decisions module."""
        return {
            "block1_rules": self.cognitive.block1_rules,
            "block2_identity": self.cognitive.block2_identity,
            "memory_text": self.cognitive.get_memory_text(),
            "goals_text": self.cognitive.get_goals_text(),
        }

    def _initial_relationships(self, world_state: dict | None) -> dict[str, float]:
        """Set initial relationships from world state."""
        # Canonical 8-state model (status column) + legacy labels (relationship column)
        rel_map = {
            # 8-state canonical (from status column)
            "allied": 0.8,
            "friendly": 0.3,
            "neutral": 0.0,
            "tense": -0.3,
            "hostile": -0.6,
            "military_conflict": -1.0,
            "armistice": -0.4,
            "peace": 0.1,
            # Legacy labels (from relationship column, for backwards compat)
            "close_ally": 0.8,
            "alliance": 0.5,
            "at_war": -1.0,
            "strategic_rival": -0.5,
        }
        relationships = {}
        if world_state and "relationships" in world_state:
            my_country = self.role["country_code"]
            for country_id, rel in world_state.get("relationships", {}).get(my_country, {}).items():
                rel_str = rel if isinstance(rel, str) else rel.get("relationship", "neutral")
                relationships[country_id] = rel_map.get(rel_str, 0.0)
        return relationships

    # ------------------------------------------------------------------
    # Info
    # ------------------------------------------------------------------

    def __repr__(self):
        return f"LeaderAgent({self.role_id}, {self.role.get('character_name', '?')}, status={self.status})"

    def info(self) -> dict:
        """Brief agent info for display."""
        return {
            "role_id": self.role_id,
            "character_name": self.role.get("character_name", ""),
            "title": self.role.get("title", ""),
            "country": self.country.get("sim_name", ""),
            "parallel": self.country.get("parallel", ""),
            "status": self.status,
            "cognitive_version": self.cognitive.version,
            "objectives": self.role.get("objectives", []),
        }
