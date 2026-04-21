"""Phase 1 — Build Layer 1 (IMMUTABLE) system prompt from DB data.

Assembles the full system prompt for a Managed Agent session from 4 sources:
  1. World context (roster, geography, theaters, situation)
  2. Game rules (all action types, combat, economy, diplomacy, covert, nuclear)
  3. Character identity + traits + assertiveness nudge
  4. Autonomy doctrine + meta-awareness (static)

Reuses: world_context.build_rich_block1, profiles.load_role/load_country_context,
        game_rules_context.build_game_rules_context,
        meta_context.build_meta_awareness_static
"""
from __future__ import annotations

import logging

from engine.agents.world_context import build_rich_block1
from engine.agents.profiles import load_role, load_country_context
from engine.agents.managed.game_rules_context import build_game_rules_context
from engine.agents.managed.meta_context import build_meta_awareness_static

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


CHARACTER_TRAIT_FRAMEWORK = """## YOUR CHARACTER TRAITS

Based on your identity as {character_name}, self-assign these traits on first activation.
These shape HOW you make decisions (not WHAT you decide).

- **Conflict style** (Thomas-Kilmann): competing / collaborating / compromising / avoiding / accommodating
- **Risk orientation** (1-5): 1=very cautious, 5=very bold
- **Decision speed** (1-5): 1=very deliberate, 5=impulsive
- **Trust default** (1-5): 1=deeply suspicious, 5=readily trusting
- **Communication style** (1-5): 1=very guarded, 5=very transparent
- **Strategic horizon** (1-5): 1=reactive/tactical, 5=long-term planner

Write your trait self-assessment to memory (key: "character_traits") on your first action.
These traits should be consistent with your character's background, age, regime type,
and political position. Let them guide your tone, risk appetite, and negotiation style
throughout the simulation."""


ASSERTIVENESS_COOPERATIVE = (
    "\n\n**World disposition:** The world tends toward cooperation. "
    "Diplomatic solutions are valued. Consider others' interests alongside your own. "
    "Escalation carries higher reputational cost than usual."
)

ASSERTIVENESS_COMPETITIVE = (
    "\n\n**World disposition:** The world is competitive. Strength is respected. "
    "Protect your interests assertively. Others will do the same. "
    "Accommodation without leverage is perceived as weakness."
)


def build_system_prompt(
    role_id: str,
    *,
    assertiveness: int = 5,
    countries: dict | None = None,
    world_state: dict | None = None,
) -> str:
    """Build the complete Layer 1 system prompt for a Managed Agent.

    This prompt is IMMUTABLE for the session. Round-specific context
    (pulse number, resource state, events) is sent per-pulse by the
    orchestrator via meta_context.build_meta_context().

    Args:
        role_id: Role identifier (e.g., "dealer" for Columbia HoS).
        assertiveness: Global assertiveness dial (1=cooperative, 10=assertive).
            Default 5 = neutral (no nudge).
        countries: Optional live country state dict.
        world_state: Optional live world state dict.

    Returns:
        Complete system prompt (~5-8K tokens).
    """
    # ── Source 1: World context (identity, roster, geography, situation) ──
    block1 = build_rich_block1(
        role_id=role_id,
        countries=countries,
        world_state=world_state,
    )

    # ── Source 2: Game rules ──
    game_rules = build_game_rules_context()

    # ── Source 3: Character identity + traits + assertiveness ──
    role = load_role(role_id)
    country = load_country_context(role["country_code"])

    character_brief = _build_character_brief(role, country)
    traits = CHARACTER_TRAIT_FRAMEWORK.format(
        character_name=role.get("character_name", role_id),
    )

    # Assertiveness nudge (only when not neutral)
    assertiveness_nudge = ""
    if assertiveness < 5:
        assertiveness_nudge = ASSERTIVENESS_COOPERATIVE
    elif assertiveness > 5:
        assertiveness_nudge = ASSERTIVENESS_COMPETITIVE

    # ── Source 4: Autonomy doctrine + static meta-awareness ──
    meta_static = build_meta_awareness_static()

    # ── Assembly ──
    sections = [
        block1,
        game_rules,
        character_brief,
        traits + assertiveness_nudge,
        AUTONOMY_DOCTRINE,
        meta_static,
    ]

    prompt = "\n\n".join(s for s in sections if s)
    logger.info(
        "Built Layer 1 prompt for %s: %d chars (~%d tokens est.)",
        role_id,
        len(prompt),
        len(prompt) // 4,
    )
    return prompt


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
