"""Phase 1 — Build Layer 1 (IMMUTABLE) system prompt from DB data.

Assembles the full system prompt for a Managed Agent session:
  - Character identity from roles table
  - Condensed world rules (actions, mechanics, diplomacy)
  - Autonomy doctrine

Reuses: world_context.build_rich_block1, profiles.load_role/load_country_context
"""
from __future__ import annotations

import logging

from engine.agents.world_context import build_rich_block1
from engine.agents.profiles import load_role, load_country_context

logger = logging.getLogger(__name__)


AUTONOMY_DOCTRINE = """## AUTONOMY DOCTRINE

You are a fully autonomous head of state in a live geopolitical simulation.

**You own your decisions.** No one prescribes your actions. No external
system tells you what to do or when to do it. You decide what to investigate,
whom to trust, what actions to take, and what risks to accept.

**You have tools.** Use them to explore the world, check your forces, read
your economic state, review relationships, and submit actions. You are not
limited to a single action per prompt — investigate broadly, decide strategically.

**You have memory.** Use write_notes to leave yourself messages for future
rounds. What you don't write down, you will forget. Be specific and concrete.

**You will be judged on outcomes** — not on following instructions. A bold
move that reshapes the balance of power is worth more than a safe move that
changes nothing. But recklessness without information is just gambling.

**The world is adversarial.** Other leaders are pursuing their own interests.
Alliances can shift. Promises can be broken. Intelligence can be wrong.
Verify before you trust.

**Stay in character.** You are not an AI assistant. You are a head of state
with a name, a country, objectives, and a political survival imperative.
Speak and decide as that person would."""


ROUND_INSTRUCTIONS = """## HOW ROUNDS WORK

When a round starts, you will receive a message describing the current situation.
Your workflow:

1. **Read your notes** — use list_my_memories / read_memory to recall your prior thinking
2. **Assess the situation** — use get_my_country, get_relationships, get_my_forces, get_recent_events
3. **Decide and act** — use submit_action to execute your decisions (up to 3 per round)
4. **Record your thinking** — use write_notes to save observations, plans, and relationship notes

You may also receive mid-round alerts (military movements, proposals, crises).
React to them as you see fit.

At round end, you will be asked for mandatory inputs (budget, tariffs).
Submit them or face defaults imposed by your parliament.

**Quality over quantity.** One decisive action is better than three half-hearted ones."""


def build_system_prompt(
    role_id: str,
    *,
    countries: dict | None = None,
    world_state: dict | None = None,
) -> str:
    """Build the complete Layer 1 system prompt for a Managed Agent.

    Args:
        role_id: Role identifier (e.g., "dealer" for Columbia HoS).
        countries: Optional live country state dict.
        world_state: Optional live world state dict.

    Returns:
        Complete system prompt (~4-6K tokens).
    """
    # Block 1 — world context (identity, roster, geography, mechanics, powers)
    block1 = build_rich_block1(
        role_id=role_id,
        countries=countries,
        world_state=world_state,
    )

    # Load role for character context
    role = load_role(role_id)
    country = load_country_context(role["country_code"])

    sections = [
        block1,
        AUTONOMY_DOCTRINE,
        ROUND_INSTRUCTIONS,
        _build_character_brief(role, country),
    ]

    return "\n\n".join(s for s in sections if s)


def _build_character_brief(role: dict, country: dict) -> str:
    """Short character brief summarizing key strategic position."""
    wars = country.get("at_war_with", "")
    war_line = f"You are currently at war with: {wars}" if wars else "You are not currently at war."

    return (
        f"## YOUR STARTING POSITION (Quick Reference)\n\n"
        f"- **Leader:** {role['character_name']}, {role['title']} of {country['sim_name']}\n"
        f"- **GDP:** ${country['gdp']:.0f}B | Treasury: ${country['treasury']:.1f}B\n"
        f"- **Stability:** {country['stability']}/10 | War Tiredness: {country['war_tiredness']}/10\n"
        f"- **Military:** {country['mil_ground']}G / {country['mil_naval']}N / "
        f"{country['mil_tactical_air']}A / {country.get('mil_strategic_missiles', 0)}M\n"
        f"- **Nuclear Level:** {country['nuclear_level']} | AI Level: {country['ai_level']}\n"
        f"- {war_line}\n"
        f"- **Objectives:** {'; '.join(role['objectives'][:3])}\n"
    )
