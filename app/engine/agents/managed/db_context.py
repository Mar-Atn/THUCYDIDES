"""Build world context from sim_run DB tables instead of CSV files.

Used by the managed agent system prompt builder to get actual sim_run state
rather than generic template data from CSVs.

Replaces world_context.build_rich_block1() for managed agents so that:
  1. Participant roster shows only ACTIVE roles for this sim_run
  2. Country data comes from the actual DB state (may have changed)
  3. Relationships come from DB (may have changed during the sim)
  4. Role data comes from DB (positions may have changed)

Geography and game mechanics sections stay hardcoded (they don't change per sim_run).
"""

from __future__ import annotations

import logging
from typing import Any

from engine.services.supabase import get_client
from engine.agents.world_context import (
    build_metacognitive_architecture,
    build_sim_structure,
    build_geography_summary,
    build_theater_map,
    GEOGRAPHY_TEMPLATE,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# DB loaders
# ---------------------------------------------------------------------------

def load_role_from_db(sim_run_id: str, role_id: str) -> dict[str, Any]:
    """Load a role from the roles table for this sim_run.

    Returns raw dict from DB row. Raises ValueError if not found.
    """
    client = get_client()
    result = (
        client.table("roles")
        .select("*")
        .eq("sim_run_id", sim_run_id)
        .eq("id", role_id)
        .execute()
    )
    if not result.data:
        raise ValueError(f"Role not found in DB: {role_id} (sim_run={sim_run_id})")
    return result.data[0]


def load_country_from_db(sim_run_id: str, country_code: str) -> dict[str, Any]:
    """Load country state from the countries table for this sim_run.

    Returns raw dict from DB row. Raises ValueError if not found.
    """
    client = get_client()
    result = (
        client.table("countries")
        .select("*")
        .eq("sim_run_id", sim_run_id)
        .eq("id", country_code)
        .execute()
    )
    if not result.data:
        raise ValueError(f"Country not found in DB: {country_code} (sim_run={sim_run_id})")
    return result.data[0]


def load_all_countries_from_db(sim_run_id: str) -> dict[str, dict[str, Any]]:
    """Load all countries for this sim_run, keyed by country id."""
    client = get_client()
    result = (
        client.table("countries")
        .select("*")
        .eq("sim_run_id", sim_run_id)
        .order("id")
        .execute()
    )
    return {row["id"]: row for row in (result.data or [])}


def load_all_active_roles(sim_run_id: str) -> list[dict[str, Any]]:
    """Load all active roles for this sim_run (for participant roster).

    Only returns roles with status='active'. This ensures the roster
    shows only participants actually in the sim, not all 20+ template roles.
    """
    client = get_client()
    result = (
        client.table("roles")
        .select("*")
        .eq("sim_run_id", sim_run_id)
        .eq("status", "active")
        .order("id")
        .execute()
    )
    return result.data or []


def load_relationships_from_db(
    sim_run_id: str, country_code: str | None = None
) -> list[dict[str, Any]]:
    """Load relationships from DB for this sim_run.

    If country_code is provided, loads only relationships where
    from_country_code matches. Otherwise loads all.
    """
    client = get_client()
    query = client.table("relationships").select("*").eq("sim_run_id", sim_run_id)
    if country_code:
        query = query.eq("from_country_code", country_code)
    result = query.execute()
    return result.data or []


def load_sanctions_from_db(sim_run_id: str) -> list[dict[str, Any]]:
    """Load all sanctions for this sim_run."""
    client = get_client()
    result = (
        client.table("sanctions")
        .select("*")
        .eq("sim_run_id", sim_run_id)
        .execute()
    )
    return result.data or []


def load_world_state_from_db(sim_run_id: str) -> dict[str, Any] | None:
    """Load the latest world_state row for this sim_run."""
    client = get_client()
    result = (
        client.table("world_state")
        .select("*")
        .eq("sim_run_id", sim_run_id)
        .order("round_num", desc=True)
        .limit(1)
        .execute()
    )
    if result.data:
        return result.data[0]
    return None


# ---------------------------------------------------------------------------
# Section builders (DB-sourced equivalents of world_context.py)
# ---------------------------------------------------------------------------

def _build_naming_rule_db(country: dict[str, Any]) -> str:
    """Build the naming rule section from DB country data."""
    sim_name = country.get("sim_name", country.get("id", "?"))
    parallel = country.get("parallel", "")
    return f"""## CRITICAL: USE ONLY SIM NAMES (READ FIRST, APPLY ALWAYS)

You live in the SIM world. NEVER use real-world country, leader, or place names.

- Your country is **{sim_name}**, NOT {parallel}.
- Use ONLY these SIM names:
  - Columbia (not USA/America), Cathay (not China), Sarmatia (not Russia), Ruthenia (not Ukraine)
  - Persia (not Iran), Teutonia (not Germany), Gallia (not France), Albion (not UK/Britain)
  - Bharata (not India), Yamato (not Japan), Formosa (not Taiwan), Hanguk (not South Korea)
  - Choson (not North Korea), Solaria (not Saudi Arabia), Freeland (not Poland), Ponte (not Italy)
  - Phrygia (not Turkey), Mirage (not UAE), Caribe (not Cuba/Venezuela), Levantia (not Israel)
- Continent: **Ereb** (not Europe). Alliance blocs: **Western Treaty** (not NATO), **Eastern Pact** (not BRICS).
- Refer to other leaders by their CHARACTER NAMES (Dealer, Helmsman, Pathfinder, Beacon, Chip, Helmsman, etc.) — NEVER by real-world names.
- This rule is ABSOLUTE. Any use of real-world names breaks immersion and invalidates the run."""


def _build_role_identity_db(role: dict[str, Any], country: dict[str, Any]) -> str:
    """Build the WHO YOU ARE section from DB role + country."""
    sim_name = country.get("sim_name", country.get("id", "?"))
    return (
        f"## Who You Are\n\n"
        f"You are **{role.get('character_name', role['id'])}**, "
        f"{role.get('title', 'Leader')} of {sim_name}.\n"
        f"- Age: {role.get('age', '?')}, Gender: {role.get('gender', '?')}\n"
        f"- Real-world parallel (for your reference only — NEVER say in-SIM): "
        f"{role.get('parallel', '')}\n"
        f"- Team / Faction: {role.get('team', '')} / {role.get('faction', '')}\n"
        f"- Intelligence pool: {role.get('intelligence_pool', 0)} per round\n"
    )


def _build_participant_roster_db(
    roles: list[dict[str, Any]],
    countries_by_id: dict[str, dict[str, Any]],
) -> str:
    """Build participant roster from DB roles — only ACTIVE roles.

    INFORMATION SCOPING: Only shows PUBLIC information — character name,
    title, country, regime type. Does NOT leak GDP, war status, etc.
    """
    heads = [r for r in roles if r.get("is_head_of_state")]
    if not heads:
        # Fallback: show all active roles if no heads flagged
        heads = roles

    lines = [f"## The {len(heads)} Heads of State in this SIM World", ""]
    for role in heads:
        country_code = role.get("country_code", "")
        country = countries_by_id.get(country_code, {})
        sim_name = country.get("sim_name", country_code)
        regime = country.get("regime_type", "?")
        char_name = role.get("character_name", role.get("id", "?"))
        title = role.get("title", "Leader")

        line = f"- **{char_name}** ({title} of {sim_name}) — {regime}"
        lines.append(line)

    lines.append("")
    lines.append(
        f"Total: {len(heads)} heads of state. "
        "Use domain tools to learn more about specific countries."
    )
    return "\n".join(lines)


def _build_starting_situation_db(
    countries_by_id: dict[str, dict[str, Any]],
    relationships: list[dict[str, Any]],
    sanctions: list[dict[str, Any]],
    world_state: dict[str, Any] | None,
) -> str:
    """Build current situation section from DB data.

    All data here is PUBLIC per INFORMATION_SCOPING.md.
    """
    # Oil price
    oil_price = 80
    if world_state:
        oil_price = world_state.get("oil_price", 80)

    # Active wars — scan relationships for military_conflict status
    wars_seen: set[tuple[str, str]] = set()
    wars: list[str] = []
    for rel in relationships:
        status = rel.get("status", "")
        if status == "military_conflict":
            a = rel.get("from_country_code", "")
            b = rel.get("to_country_code", "")
            pair = tuple(sorted([a, b]))
            if pair in wars_seen:
                continue
            wars_seen.add(pair)
            a_name = countries_by_id.get(pair[0], {}).get("sim_name", pair[0])
            b_name = countries_by_id.get(pair[1], {}).get("sim_name", pair[1])
            wars.append(f"{a_name}–{b_name}")

    # Also check world_state.wars if present
    if world_state and not wars:
        ws_wars = world_state.get("wars", [])
        for w in ws_wars:
            if isinstance(w, dict):
                a = w.get("attacker", w.get("side_a", ""))
                b = w.get("defender", w.get("side_b", ""))
                if a and b:
                    a_name = countries_by_id.get(a, {}).get("sim_name", a)
                    b_name = countries_by_id.get(b, {}).get("sim_name", b)
                    wars.append(f"{a_name}–{b_name}")

    # Also check country at_war_with field (legacy)
    for cid, cdata in countries_by_id.items():
        at_war = str(cdata.get("at_war_with", "")).strip()
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
            a_name = countries_by_id.get(pair[0], {}).get("sim_name", pair[0])
            b_name = countries_by_id.get(pair[1], {}).get("sim_name", pair[1])
            wars.append(f"{a_name}–{b_name}")

    # Sanctions (L2 and L3)
    l3_lines: list[str] = []
    l2_lines: list[str] = []
    for s in sanctions:
        try:
            lvl = int(s.get("level", 0))
        except (ValueError, TypeError):
            continue
        if lvl < 2:
            continue
        imposer = countries_by_id.get(
            s.get("imposer_country_code", ""), {}
        ).get("sim_name", s.get("imposer_country_code", "?"))
        target = countries_by_id.get(
            s.get("target_country_code", ""), {}
        ).get("sim_name", s.get("target_country_code", "?"))
        line = f"{imposer}\u2192{target} L{lvl}"
        if lvl == 3:
            l3_lines.append(line)
        else:
            l2_lines.append(line)

    # Relationships: high-salience tensions
    tensions: list[str] = []
    for r in relationships:
        rel_type = r.get("status", r.get("relationship", ""))
        if rel_type in ("hostile", "tense"):
            a = countries_by_id.get(
                r.get("from_country_code", ""), {}
            ).get("sim_name", r.get("from_country_code", ""))
            b = countries_by_id.get(
                r.get("to_country_code", ""), {}
            ).get("sim_name", r.get("to_country_code", ""))
            pair = tuple(sorted([a, b]))
            token = f"{pair[0]}\u2194{pair[1]} ({rel_type})"
            if token not in tensions:
                tensions.append(token)
    tensions = tensions[:8]

    # Active blockades
    blockade_lines: list[str] = []
    if world_state:
        blockades = world_state.get("active_blockades", {})
        if isinstance(blockades, dict):
            for zone, info in blockades.items():
                if isinstance(info, dict):
                    by = info.get("by", "?")
                    by_name = countries_by_id.get(by, {}).get("sim_name", by)
                    blockade_lines.append(f"{zone} by {by_name}")
                elif isinstance(info, str):
                    blockade_lines.append(f"{zone}: {info}")

    # Assemble
    lines = ["## Current Situation", ""]
    lines.append(f"- **Oil price**: ${oil_price:g}")
    if wars:
        lines.append(f"- **Active wars**: {'; '.join(wars)}")
    else:
        lines.append("- **Active wars**: none")

    if l3_lines:
        lines.append(f"- **L3 sanctions** (maximum): {', '.join(l3_lines)}")
    if l2_lines:
        lines.append(
            f"- **L2 sanctions** (heavy): {', '.join(l2_lines[:10])}"
            + (" \u2026" if len(l2_lines) > 10 else "")
        )

    if blockade_lines:
        lines.append(f"- **Active blockades**: {'; '.join(blockade_lines)}")
    else:
        # Fallback: hardcoded from SEED if no DB blockade data
        lines.append(
            "- **Active blockades**: Gulf Gate (Hormuz) contested by Persia; "
            "Caribe under Columbia energy blockade"
        )

    if tensions:
        lines.append(f"- **Major tensions**: {'; '.join(tensions)}")

    return "\n".join(lines)


def _build_powers_db(role: dict[str, Any]) -> str:
    """Build powers section from DB role data."""
    powers = role.get("powers", [])
    if isinstance(powers, str):
        powers = [p.strip() for p in powers.split(";") if p.strip()]
    if not powers:
        return "## Your Powers\n\n- (No specific powers assigned)"
    return "## Your Powers\n\n" + "\n".join(f"- {p}" for p in powers)


def _build_mechanics_db(role: dict[str, Any]) -> str:
    """Build key mechanics section from DB role data."""
    intel = role.get("intelligence_pool", 0)
    return f"""## Key Mechanics

- **Budget**: each round you set social spending (0.5-1.5\u00d7 baseline), military allocation, tech investment.
- **Tariffs**: L0 (none) to L3 (heavy) per target country. Hurt both sides asymmetrically.
- **Sanctions**: L0-L3. Coalition-based \u2014 stacking matters. Cost the imposer 30-50% of damage inflicted.
- **Military**: ground attack (needs co-sign / authorization), naval/air, blockade, strategic missiles (nuclear authority gated).
- **Covert**: sabotage, propaganda \u2014 bounded by your intelligence pool ({intel} per round). Intelligence is a separate standalone action.
- **Transactions**: arms sales, coin transfers, treaties, basing rights \u2014 bilateral, both parties must confirm.
- **Political**: public statements, repression (autocracy only).
- **Nothing is free.** Every action has costs and visible or covert consequences."""


def _build_objectives_db(role: dict[str, Any]) -> str:
    """Build objectives section from DB role data."""
    objs = role.get("objectives", [])
    if isinstance(objs, str):
        objs = [o.strip() for o in objs.split(";") if o.strip()]
    if not objs:
        return "## Your Objectives\n\n- (No specific objectives assigned)"
    return "## Your Objectives\n\n" + "\n".join(f"- {o}" for o in objs)


# ---------------------------------------------------------------------------
# MAIN BUILDER
# ---------------------------------------------------------------------------

def build_db_world_context(
    sim_run_id: str,
    role_id: str,
    metacognitive_override: str | None = None,
) -> str:
    """Build the full world context section from DB data.

    Replaces build_rich_block1() for managed agents. Returns formatted text
    matching the same structure as the CSV version but sourced from the
    sim_run's actual DB tables.

    Args:
        sim_run_id: The sim_run UUID.
        role_id: The role being initialized (e.g. "dealer").
        metacognitive_override: Optional custom metacognitive text.

    Returns:
        Formatted Block 1 text (~3-5K tokens).
    """
    # Load role and country from DB
    role = load_role_from_db(sim_run_id, role_id)
    country_code = role.get("country_code", "")
    country = load_country_from_db(sim_run_id, country_code)

    # Load all countries (for roster, situation building)
    countries_by_id = load_all_countries_from_db(sim_run_id)

    # Load active roles (for participant roster)
    active_roles = load_all_active_roles(sim_run_id)

    # Load relationships (all, for situation overview)
    all_relationships = load_relationships_from_db(sim_run_id)

    # Load sanctions
    all_sanctions = load_sanctions_from_db(sim_run_id)

    # Load world state
    world_state = load_world_state_from_db(sim_run_id)

    # Count active heads of state for intro text
    heads = [r for r in active_roles if r.get("is_head_of_state")]
    head_count = len(heads) if heads else len(active_roles)

    sections = [
        "# SIM World: The Thucydides Trap",
        "",
        f"You are one of {head_count} heads of state in a geopolitical simulation. "
        "What follows is everything you know about this world at the moment you enter it.",
        "",
        _build_naming_rule_db(country),
        build_metacognitive_architecture(metacognitive_override),
        _build_role_identity_db(role, country),
        _build_participant_roster_db(active_roles, countries_by_id),
        build_sim_structure(),
        _build_starting_situation_db(
            countries_by_id, all_relationships, all_sanctions, world_state,
        ),
        build_geography_summary(),
        build_theater_map(country_code),
        _build_powers_db(role),
        _build_mechanics_db(role),
        _build_objectives_db(role),
    ]
    return "\n\n".join(s for s in sections if s)
