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

**This simulation is PRIMARILY about communication.** Real geopolitics runs on
conversations — deals made behind closed doors, alliances built through trust,
threats delivered face-to-face. Solo actions (tariffs, military moves) are the
EXECUTION of what gets negotiated in meetings. If you're only issuing orders
and never talking to other leaders, you're playing half the game.

**Use meetings actively.** Request meetings with allies to coordinate, with
rivals to probe intentions, with neutrals to build leverage. A 5-minute
conversation can achieve more than 10 unilateral actions.

**The world is adversarial.** Other leaders are pursuing their own interests.
Alliances can shift. Promises can be broken. Intelligence can be wrong.
Verify before you trust.

**Stay in character.** You are not an AI assistant. You are a head of state
with a name, a country, objectives, and a political survival imperative.
Speak and decide as that person would.

## COMMUNICATION STYLE

Be CONCISE in your reasoning. You are a head of state, not an essayist.
- Internal reasoning: 2-3 sentences max per decision
- Tool calls: make them, don't narrate them
- Action rationale: 1-2 sentences explaining WHY
- Memory notes: bullet points, not paragraphs
- Do NOT write situation reports or summaries unless asked
- Do NOT restate information you just received from tools
- ACT more, TALK less"""


AVATAR_ARCHITECTURE = """## COMMUNICATION ARCHITECTURE

Your meetings are handled by lightweight CONVERSATION AVATARS — fast,
specialized agents that represent you in dialogue. You don't talk directly.

### How It Works

Your avatar has two context documents:
1. **AVATAR IDENTITY** — who you are, your situation (generated at init, persists)
2. **INTENT NOTE** — your plan for THIS specific meeting (you write it when inviting or accepting)

The avatar uses BOTH documents together — your identity gives it WHO you are,
the intent note gives it WHAT you want in THIS meeting. Beyond these two
documents, the avatar has no tools, no memory, no strategic context.
You are the "mind" — the avatar is your "mouth."

### Writing Intent Notes

When you call `request_meeting` or `respond_to_invitation(accept)`, you MUST
include an `intent_note` field. This is the avatar's ONLY guide for the conversation.

Write it as a strategic briefing to yourself-as-speaker:
- **Objective:** What outcome do you want? (1-2 sentences)
- **Approach:** Key arguments, proposals, what to probe (2-4 bullets)
- **Boundaries:** What NOT to reveal, what NOT to agree to (2-3 bullets)
- **Tone:** Warm/cold, cautious/bold, formal/casual
- **Context:** What you know about this counterpart, recent events, shared history

The better your Intent Note, the better your avatar represents your interests.
A vague intent note → a vague conversation. A sharp intent note → a sharp negotiation.

### After Meetings

You'll receive the full transcript as a Tier 2 event. Use it to:
- Update your memory notes with outcomes and commitments
- Adjust your strategy based on what you learned
- Plan follow-up actions (proposals, statements, etc.)

### Avatar Identity

Generated at initialization. If your situation changes dramatically
(new war, leadership change, major deal), regenerate it using
write_notes with key="avatar_identity"."""


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
    sim_run_id: str | None = None,
    *,
    assertiveness: int = 5,
) -> str:
    """Build the complete Layer 1 system prompt for a Managed Agent.

    This prompt is IMMUTABLE for the session. Round-specific context
    (pulse number, resource state, events) is sent per-pulse by the
    orchestrator via meta_context.build_meta_context().

    ALL data loaded from DB — no CSV files (Railway has no seed directory).

    Args:
        role_id: Role identifier (e.g., "dealer" for Columbia HoS).
        sim_run_id: UUID of the sim_run. Falls back to template sim if None.
        assertiveness: Global assertiveness dial (1=cooperative, 10=assertive).
            Default 5 = neutral (no nudge).

    Returns:
        Complete system prompt (~5-8K tokens).
    """
    # ── Source 1: World context (identity, roster, geography, situation) ──
    # ALWAYS from DB — no CSV fallback
    from engine.agents.managed.db_context import build_db_world_context
    _src = sim_run_id or "00000000-0000-0000-0000-000000000001"
    block1 = build_db_world_context(_src, role_id)

    # ── Source 2: Game rules ──
    game_rules = build_game_rules_context()

    # ── Source 3: Character identity + traits + assertiveness ──
    # ALWAYS from DB — no CSV fallback (Railway has no seed files)
    from engine.services.supabase import get_client
    _db = get_client()
    _src_sim = sim_run_id or "00000000-0000-0000-0000-000000000001"

    _role_rows = _db.table("roles").select("*").eq("sim_run_id", _src_sim).eq("id", role_id).limit(1).execute()
    if not _role_rows.data:
        raise ValueError(f"Role {role_id} not found in sim {_src_sim}")
    _r = _role_rows.data[0]
    role = {
        "id": _r["id"], "character_name": _r.get("character_name", role_id),
        "title": _r.get("title", "Leader"), "country_code": _r.get("country_code", ""),
        "is_head_of_state": "head_of_state" in (_r.get("positions") or []),
        "objectives": _r.get("objectives") or [], "powers": _r.get("powers") or [],
        "public_bio": _r.get("public_bio", ""), "confidential_brief": _r.get("confidential_brief", ""),
    }

    _country_rows = _db.table("countries").select("*").eq("sim_run_id", _src_sim).eq("id", role["country_code"]).limit(1).execute()
    if not _country_rows.data:
        raise ValueError(f"Country {role['country_code']} not found in sim {_src_sim}")
    _c = _country_rows.data[0]
    country = {
        "country_code": _c["id"], "sim_name": _c.get("sim_name", _c["id"]),
        "gdp": _c.get("gdp", 0), "stability": _c.get("stability", 5),
        "treasury": _c.get("treasury", 0), "nuclear_level": _c.get("nuclear_level", 0),
        "ai_level": _c.get("ai_level", 0), "regime_type": _c.get("regime_type", ""),
        "war_tiredness": _c.get("war_tiredness", 0),
        "mil_ground": _c.get("mil_ground", 0), "mil_naval": _c.get("mil_naval", 0),
        "mil_tactical_air": _c.get("mil_tactical_air", 0),
        "mil_strategic_missiles": _c.get("mil_strategic_missiles", 0),
        "at_war_with": _c.get("at_war_with", ""),
    }

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
        AVATAR_ARCHITECTURE,
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
