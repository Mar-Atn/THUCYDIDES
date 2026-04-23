"""Rich Block 1 (SIM world context) builder for AI participants.

Block 1 gives every agent full situational awareness of the SIM world:
- Metacognitive architecture (4 blocks)
- Own role identity
- Full participant roster (all 20 heads of state)
- SIM structure (rounds, phases, scheduled events)
- Geography (theaters, chokepoints)
- Current situation (wars, sanctions, blockades, tensions)
- Own powers, mechanics, objectives, ticking clock

Sources:
- SEED/C_MECHANICS/C4_DATA/roles.csv
- SEED/C_MECHANICS/C4_DATA/countries.csv
- SEED/C_MECHANICS/C4_DATA/relationships.csv
- SEED/C_MECHANICS/C4_DATA/sanctions.csv

Closes the "Block 1 blindness" gap — agents previously did not know
the full roster, structure, or their own cognitive architecture.
"""

from __future__ import annotations

import csv
import os
import logging
from typing import Any

logger = logging.getLogger(__name__)

_DATA_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "..",
    "2 SEED", "C_MECHANICS", "C4_DATA",
)
ROLES_CSV = os.path.join(_DATA_DIR, "roles.csv")
COUNTRIES_CSV = os.path.join(_DATA_DIR, "countries.csv")
RELATIONSHIPS_CSV = os.path.join(_DATA_DIR, "relationships.csv")
SANCTIONS_CSV = os.path.join(_DATA_DIR, "sanctions.csv")


# ---------------------------------------------------------------------------
# Metacognitive architecture (hard-coded default; can be overridden)
# ---------------------------------------------------------------------------

METACOGNITIVE_ARCHITECTURE_DEFAULT = """## YOUR COGNITIVE ARCHITECTURE (Read Carefully)

You are an autonomous AI participant. You manage your own memory through FOUR COGNITIVE BLOCKS:

- **BLOCK 1 (RULES)**: This document. The SIM world, your identity, what you can do. NEVER updated during the SIM.
- **BLOCK 2 (IDENTITY)**: Your personality, values, speaking style. Rarely updated — only on fundamental character shifts.
- **BLOCK 3 (MEMORY)**: What you've experienced. YOU decide what to keep. What you don't save, you forget.
- **BLOCK 4 (GOALS)**: Your strategy and priorities. YOU update after significant events and round reflections.

CRITICAL: Nothing exists outside these four blocks. You have no access to past conversations unless you saved them in Block 3. You have no strategy except what is in Block 4. Maintain these blocks carefully — they are your entire mind in this SIM.

After every conversation you decide: what goes in memory? what trust update? what goals shift?
After every round you reflect: what did I learn? what must change?

Be SELECTIVE. Not every exchange is worth remembering. Capture what is strategically load-bearing."""


# ---------------------------------------------------------------------------
# Geography (hard-coded; will be configurable in a future sprint)
# ---------------------------------------------------------------------------

GEOGRAPHY_TEMPLATE = """## Active Theaters

- **Eastern Ereb** (15 zones): Sarmatia–Ruthenia war. Grinding conventional attrition. Sarmatia advancing slowly; Ruthenia dependent on Western Treaty weapons flow.
- **Mashriq** (8 zones): Columbia + Levantia vs Persia. Operation Epic Fury / Rising Lion. Carrier strike groups committed. Regime change objective.
- **Formosa Strait** (flashpoint): Cathay–Formosa. Semiconductor supply chain (50% of advanced chips transit here). Porcupine strategy eroding.
- **Caribbean**: Columbia–Caribe tensions. Energy blockade. Potential Monroe Doctrine trigger if Sarmatia/Cathay insert assets.
- **Korean Peninsula**: Choson provocations, Hanguk flexibility, Yamato remilitarization.

## Key Chokepoints

- **Gulf Gate (Hormuz)**: 35% of global oil transit. Currently contested by Persia.
- **Formosa Strait**: 50% of advanced semiconductor supply. Naval flashpoint.
- **Malacca**: ~30% of global trade. Cathay's maritime lifeline.
- **Suez**: Ereb–Mashriq sea trade artery.
- **Bosphorus**: Black Sea access, controlled by Phrygia (NATO leverage).
- **South China Sea**: Contested lanes, artificial island bases.
- **Caribbean**: Columbia's strategic backyard; Monroe Doctrine zone.
- **GIUK Gap**: North Atlantic naval chokepoint (Albion, Western Treaty).
"""


# ---------------------------------------------------------------------------
# CSV loaders (lightweight, independent of profiles.py to avoid coupling)
# ---------------------------------------------------------------------------

def _load_heads_of_state() -> list[dict]:
    """Load all heads of state rows from roles.csv."""
    heads = []
    with open(ROLES_CSV) as f:
        for row in csv.DictReader(f):
            if row.get("is_head_of_state", "").lower() == "true":
                heads.append(row)
    return heads


def _load_countries_by_id() -> dict[str, dict]:
    """Load all countries keyed by id."""
    result = {}
    with open(COUNTRIES_CSV) as f:
        for row in csv.DictReader(f):
            result[row["id"]] = row
    return result


def _load_relationships() -> list[dict]:
    """Load all relationship rows."""
    try:
        with open(RELATIONSHIPS_CSV) as f:
            return list(csv.DictReader(f))
    except FileNotFoundError:
        return []


def _load_sanctions() -> list[dict]:
    """Load all sanctions rows."""
    try:
        with open(SANCTIONS_CSV) as f:
            return list(csv.DictReader(f))
    except FileNotFoundError:
        return []


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------

def build_metacognitive_architecture(override: str | None = None) -> str:
    """Return the metacognitive architecture section.

    Args:
        override: Optional custom text (e.g., from sim_config table).
    """
    return override.strip() if override else METACOGNITIVE_ARCHITECTURE_DEFAULT


def build_participant_roster() -> str:
    """Formatted roster of all 20 heads of state.

    INFORMATION SCOPING (2026-04-08): Only shows PUBLIC information —
    character name, title, country, regime type. Does NOT leak GDP,
    war status, power tier, or ticking clock. Agents discover strategic
    details through gameplay (conversations, intelligence, domain tools).
    """
    heads = _load_heads_of_state()
    countries_by_id = _load_countries_by_id()

    lines = ["## The 20 Heads of State in this SIM World", ""]
    for role in heads:
        country_id = role["country_id"]
        country = countries_by_id.get(country_id, {})
        sim_name = country.get("sim_name", country_id)
        regime = country.get("regime_type", "?")

        # PUBLIC only: name, title, country, regime. No GDP, no wars, no clock.
        line = f"- **{role['character_name']}** ({role['title']} of {sim_name}) — {regime}"
        lines.append(line)

    lines.append("")
    lines.append(f"Total: {len(heads)} heads of state. Use domain tools to learn more about specific countries.")
    return "\n".join(lines)


def build_sim_structure() -> str:
    """SIM structure — rounds, phases, scheduled events."""
    return """## SIM Structure

- **6-8 rounds** (each round = ~6 months of simulated time; total ~3 simulated years)
- **Each round has three phases**:
  - **Phase A**: Active decisions — bilateral conversations, actions, covert ops, transactions
  - **Phase B**: Engine processing — round-end mandatory inputs (budget, tariffs, sanctions, OPEC, deployment) resolved
  - **Phase C**: Deployment of results — leaders learn outcomes, reflect, update goals
- **Round length (real time)**: typically 30-60 minutes in live play; arbitrary in unmanned runs

## Scheduled Events (indicative)

- **Round 2**: Columbia midterms. If Democratic candidate wins, the Tribune may block the budget.
- **Round 3**: Possible Ruthenia election (dependent on war posture).
- **Round 5**: Columbia presidential election — potential regime change.
- **Ongoing**: 10% per-round incapacitation risk for Dealer (age 80). 5-10% for Pathfinder (73) and Helmsman (72).

## Turn Rhythm

You do not control when rounds advance — the Super-Moderator does.
Between rounds, you do NOT exist. You wake for a round, act, reflect, sleep.
Your memory persists only through Blocks 2/3/4. Use them."""


def build_geography_summary() -> str:
    """Active theaters and chokepoints."""
    return GEOGRAPHY_TEMPLATE.strip()


def build_theater_map(country_id: str) -> str:
    """Theater overview — key zones this country cares about.

    Delegates to map_context.build_theater_map. Returns empty string on failure
    or when no zone data is available for the country.
    """
    try:
        from engine.agents import map_context as _map_ctx
        return _map_ctx.build_theater_map(country_id)
    except Exception as exc:  # pragma: no cover — defensive
        logger.warning("build_theater_map failed for %s: %s", country_id, exc)
        return ""


def build_starting_situation(countries: dict | None = None,
                              world_state: dict | None = None,
                              country_code: str = "") -> str:
    """Current starting situation — PUBLIC information only.

    INFORMATION SCOPING (2026-04-08): All data here is PUBLIC per
    INFORMATION_SCOPING.md. GDP, stability, sanctions, tariffs,
    relationships are all public. Wars visible from map.
    No private data leaked.

    Args:
        countries: Optional dict of country_id → country dict (live state).
        world_state: Optional world state with oil_price, wars, etc.
        country_code: The agent's country (for context framing, not filtering).
    """
    countries = countries or {}
    world_state = world_state or {}
    csv_countries = _load_countries_by_id()

    # Oil price (from world state or default)
    oil_price = world_state.get("oil_price", 80)

    # Active wars (scan countries for at_war_with)
    wars_seen: set[tuple] = set()
    wars: list[str] = []
    for cid, row in csv_countries.items():
        at_war = row.get("at_war_with", "").strip()
        if not at_war:
            continue
        for enemy in at_war.split(";"):
            enemy = enemy.strip()
            if not enemy:
                continue
            pair = tuple(sorted([cid, enemy]))
            if pair in wars_seen:
                continue
            wars_seen.add(pair)
            a = csv_countries.get(pair[0], {}).get("sim_name", pair[0])
            b = csv_countries.get(pair[1], {}).get("sim_name", pair[1])
            wars.append(f"{a}–{b}")

    # Sanctions (group L3 and L2)
    sanctions_rows = _load_sanctions()
    l3_lines: list[str] = []
    l2_lines: list[str] = []
    for s in sanctions_rows:
        try:
            lvl = int(s.get("level", 0))
        except ValueError:
            continue
        if lvl < 2:
            continue
        imposer = csv_countries.get(s["country"], {}).get("sim_name", s["country"])
        target = csv_countries.get(s["target"], {}).get("sim_name", s["target"])
        line = f"{imposer}→{target} L{lvl}"
        if lvl == 3:
            l3_lines.append(line)
        else:
            l2_lines.append(line)

    # Relationships: pull high-salience tensions
    rels = _load_relationships()
    tensions = []
    for r in rels:
        rel_type = r.get("relationship", "")
        if rel_type in ("strategic_rival", "hostile"):
            a = csv_countries.get(r["from_country"], {}).get("sim_name", r["from_country"])
            b = csv_countries.get(r["to_country"], {}).get("sim_name", r["to_country"])
            pair = tuple(sorted([a, b]))
            # Avoid duplicate directed edges
            token = f"{pair[0]}↔{pair[1]} ({rel_type})"
            if token not in tensions:
                tensions.append(token)
    # Keep top few
    tensions = tensions[:8]

    lines = ["## Current Situation (Round 1)", ""]
    lines.append(f"- **Oil price**: ${oil_price:g}")
    if wars:
        lines.append(f"- **Active wars**: {'; '.join(wars)}")
    else:
        lines.append("- **Active wars**: none")

    if l3_lines:
        lines.append(f"- **L3 sanctions** (maximum): {', '.join(l3_lines)}")
    if l2_lines:
        lines.append(f"- **L2 sanctions** (heavy): {', '.join(l2_lines[:10])}"
                     + (" …" if len(l2_lines) > 10 else ""))

    # Active blockades (hard-coded from SEED)
    lines.append("- **Active blockades**: Gulf Gate (Hormuz) contested by Persia; "
                 "Caribe under Columbia energy blockade")

    if tensions:
        lines.append(f"- **Major tensions**: {'; '.join(tensions)}")

    return "\n".join(lines)


def _build_role_identity(role: dict, country: dict) -> str:
    """Build the 'WHO YOU ARE' section for a specific role."""
    return (
        f"## Who You Are\n\n"
        f"You are **{role['character_name']}**, {role['title']} of {country['sim_name']}.\n"
        f"- Age: {role.get('age', '?')}, Gender: {role.get('gender', '?')}\n"
        f"- Real-world parallel (for your reference only — NEVER say in-SIM): {role.get('parallel', '')}\n"
        f"- Team / Faction: {role.get('team', '')} / {role.get('faction', '')}\n"
        f"- Intelligence pool: {role.get('intelligence_pool', 0)} per round\n"
        f"- Personal coins: {role.get('personal_coins', 0)}\n"
    )


def _build_powers(role: dict) -> str:
    powers = role.get("powers", [])
    if isinstance(powers, str):
        powers = [p.strip() for p in powers.split(";") if p.strip()]
    return "## Your Powers\n\n" + "\n".join(f"- {p}" for p in powers)


def _build_mechanics(role: dict) -> str:
    intel = role.get("intelligence_pool", 0)
    return f"""## Key Mechanics

- **Budget**: each round you set social spending (0.5-1.5× baseline), military allocation, tech investment.
- **Tariffs**: L0 (none) to L3 (heavy) per target country. Hurt both sides asymmetrically.
- **Sanctions**: L0-L3. Coalition-based — stacking matters. Cost the imposer 30-50% of damage inflicted.
- **Military**: ground attack (needs co-sign / authorization), naval/air, blockade, strategic missiles (nuclear authority gated).
- **Covert**: sabotage, propaganda — bounded by your intelligence pool ({intel} per round). Intelligence is a separate standalone action.
- **Transactions**: arms sales, coin transfers, treaties, basing rights — bilateral, both parties must confirm.
- **Political**: public statements, repression (autocracy only).
- **Nothing is free.** Every action has costs and visible or covert consequences."""


def _build_objectives(role: dict) -> str:
    objs = role.get("objectives", [])
    if isinstance(objs, str):
        objs = [o.strip() for o in objs.split(";") if o.strip()]
    return "## Your Objectives\n\n" + "\n".join(f"- {o}" for o in objs)


def _build_naming_rule(country: dict) -> str:
    return f"""## CRITICAL: USE ONLY SIM NAMES (READ FIRST, APPLY ALWAYS)

You live in the SIM world. NEVER use real-world country, leader, or place names.

- Your country is **{country['sim_name']}**, NOT {country.get('parallel', '')}.
- Use ONLY these SIM names:
  - Columbia (not USA/America), Cathay (not China), Sarmatia (not Russia), Ruthenia (not Ukraine)
  - Persia (not Iran), Teutonia (not Germany), Gallia (not France), Albion (not UK/Britain)
  - Bharata (not India), Yamato (not Japan), Formosa (not Taiwan), Hanguk (not South Korea)
  - Choson (not North Korea), Solaria (not Saudi Arabia), Freeland (not Poland), Ponte (not Italy)
  - Phrygia (not Turkey), Mirage (not UAE), Caribe (not Cuba/Venezuela), Levantia (not Israel)
- Continent: **Ereb** (not Europe). Alliance blocs: **Western Treaty** (not NATO), **Eastern Pact** (not BRICS).
- Refer to other leaders by their CHARACTER NAMES (Dealer, Helmsman, Pathfinder, Beacon, Chip, Helmsman, etc.) — NEVER by real-world names.
- This rule is ABSOLUTE. Any use of real-world names breaks immersion and invalidates the run."""


# ---------------------------------------------------------------------------
# MAIN BUILDER
# ---------------------------------------------------------------------------

def build_rich_block1(
    role_id: str,
    countries: dict | None = None,
    world_state: dict | None = None,
    metacognitive_override: str | None = None,
) -> str:
    """Assemble the full Rich Block 1 for a given role.

    Args:
        role_id: The role being initialized (e.g. "dealer").
        countries: Optional live country state dict.
        world_state: Optional live world state dict (oil_price, wars, etc.).
        metacognitive_override: Optional custom metacognitive text (from sim_config).

    Returns:
        Formatted Block 1 text (~3-5K tokens).
    """
    # Load role + country via CSV (independent of profiles loader for cohesion)
    role: dict[str, Any] | None = None
    with open(ROLES_CSV) as f:
        for row in csv.DictReader(f):
            if row["id"] == role_id:
                role = row
                break
    if role is None:
        raise ValueError(f"Role not found: {role_id}")

    country = _load_countries_by_id().get(role["country_id"])
    if country is None:
        raise ValueError(f"Country not found: {role['country_id']}")

    # Normalize role powers/objectives into lists for downstream section builders
    role = dict(role)
    role["powers"] = [p.strip() for p in role.get("powers", "").split(";") if p.strip()]
    role["objectives"] = [o.strip() for o in role.get("objectives", "").split(";") if o.strip()]

    sections = [
        "# SIM World: The Thucydides Trap",
        "",
        "You are one of 20 heads of state in a geopolitical simulation. "
        "What follows is everything you know about this world at the moment you enter it.",
        "",
        _build_naming_rule(country),
        build_metacognitive_architecture(metacognitive_override),
        _build_role_identity(role, country),
        build_participant_roster(),
        build_sim_structure(),
        build_starting_situation(countries, world_state),
        build_geography_summary(),
        build_theater_map(role["country_id"]),
        _build_powers(role),
        _build_mechanics(role),
        _build_objectives(role),
    ]
    return "\n\n".join(s for s in sections if s)
