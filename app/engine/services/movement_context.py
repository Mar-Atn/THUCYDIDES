"""Movement decision context assembler — CONTRACT_MOVEMENT v1.0 §3.

Step 5 of the M1 movement vertical slice.

Pure read-only service: ``build_movement_context(country_code, scenario_code,
round_num)`` assembles the decision-specific context payload for a movement
decision-maker (AI or human). No DB mutations, no cognitive blocks.

Per §3.1, the assembler returns these blocks:

1. economic_state — own GDP/treasury/stability/at_war
2. my_units — full inventory (active / reserve / embarked / destroyed)
3. own_territory — zones the country owns or controls
4. basing_rights_i_have — host countries that grant basing
5. previously_occupied_hexes — hexes I have ≥1 active unit on
6. recent_combat_events — last 3 rounds involving my units
7. world_zone_map — all 57 high-level zones from the zones DB table
8. zone_adjacency — the adjacency graph from zone_adjacency table
9. decision_rules — text block with rules + no_change reminder
10. instruction — what to decide

Strictly DATA ONLY — no commentary, no persona, no cognitive layer.
Follows the sanction_context.py / opec_context.py pattern.
"""
from __future__ import annotations

import logging

from engine.services.movement_data import (
    load_basing_rights,
    load_global_grid_zones,
)
from engine.services.supabase import get_client

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_movement_context(
    country_code: str,
    scenario_code: str,
    round_num: int,
    sim_run_id: str | None = None,
) -> dict:
    """Assemble the full context package for a movement decision.

    Returns a dict matching CONTRACT_MOVEMENT v1.0 §3. Pure read — no DB
    mutations. Falls back to ``round_num - 1`` for snapshots if the
    requested round has no row yet.

    F1: pass an explicit ``sim_run_id`` to read from an isolated run,
    otherwise falls back to the legacy archived run for ``scenario_code``.
    """
    from engine.services.sim_run_manager import resolve_sim_run_id
    client = get_client()
    sim_run_id = sim_run_id or resolve_sim_run_id(scenario_code)

    # 1. Economic state (own snapshot)
    economic_state = _load_economic_state(
        client, sim_run_id, country_code, round_num,
    )

    # 2. My units — full inventory
    my_units = _load_my_units(
        client, sim_run_id, country_code, round_num,
    )

    # 3. Own territory — zones I own or control (from canonical 57-zones table)
    zones_table = _load_zones_table(client)
    own_territory = [
        {
            "zone_id": z["id"],
            "display_name": z.get("display_name"),
            "theater": z.get("theater"),
            "type": z.get("type"),
            "ownership": "owned" if z.get("owner") == country_code else "controlled",
        }
        for z in zones_table
        if z.get("owner") == country_code or z.get("controlled_by") == country_code
    ]

    # 4. Basing rights I have — list of grantor countries
    basing_rights = load_basing_rights(client)
    grantors = sorted(basing_rights.get(country_code, set()))
    basing_rights_i_have = [{"grantor": g} for g in grantors]

    # 5. Previously occupied hexes — distinct (row, col) for active units I own
    previously_occupied_hexes = sorted(
        {
            (u["global_row"], u["global_col"])
            for u in my_units
            if u.get("status") == "active"
            and u.get("global_row") is not None
            and u.get("global_col") is not None
        }
    )
    previously_occupied_hexes = [
        {"global_row": r, "global_col": c} for (r, c) in previously_occupied_hexes
    ]

    # 6. Recent combat events — last 3 rounds involving my units
    recent_combat_events = _load_recent_combat(
        client, sim_run_id, country_code, round_num,
    )

    # 7. World zone map — all 57 zones (compact)
    world_zone_map = [
        {
            "zone_id": z["id"],
            "display_name": z.get("display_name"),
            "theater": z.get("theater"),
            "type": z.get("type"),
            "owner": z.get("owner"),
            "controlled_by": z.get("controlled_by"),
            "is_chokepoint": bool(z.get("is_chokepoint")),
            "die_hard": bool(z.get("die_hard")),
        }
        for z in zones_table
    ]

    # 8. Zone adjacency
    zone_adjacency = _load_zone_adjacency(client)

    # 9. Decision rules
    decision_rules = _decision_rules_text()

    # 10. Instruction
    instruction = (
        "Decide whether to CHANGE your unit dispositions or keep them NO_CHANGE.\n"
        "Either way you MUST provide a rationale of at least 30 characters.\n\n"
        "Respond with JSON ONLY, matching the schema in CONTRACT_MOVEMENT §2."
    )

    return {
        "country_code": country_code,
        "round_num": round_num,
        "economic_state": economic_state,
        "my_units": my_units,
        "own_territory": own_territory,
        "basing_rights_i_have": basing_rights_i_have,
        "previously_occupied_hexes": previously_occupied_hexes,
        "recent_combat_events": recent_combat_events,
        "world_zone_map": world_zone_map,
        "zone_adjacency": zone_adjacency,
        "decision_rules": decision_rules,
        "instruction": instruction,
    }


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------




def _load_economic_state(
    client, sim_run_id: str, country_code: str, round_num: int,
) -> dict:
    """Load economic snapshot, falling back to most recent prior round."""
    res = (
        client.table("country_states_per_round")
        .select(
            "round_num, gdp, treasury, inflation, stability, "
            "political_support, war_tiredness"
        )
        .eq("sim_run_id", sim_run_id)
        .eq("country_code", country_code)
        .lte("round_num", round_num)
        .order("round_num", desc=True)
        .limit(1)
        .execute()
    )
    if res.data:
        row = res.data[0]
        candidate = row.get("round_num", round_num)
        if True:
            wars = _load_wars(client, country_code)
            return {
                "gdp": float(row.get("gdp") or 0),
                "treasury": float(row.get("treasury") or 0),
                "stability": int(row.get("stability") or 0),
                "political_support": int(row.get("political_support") or 0),
                "war_tiredness": int(row.get("war_tiredness") or 0),
                "at_war_with": wars,
                "at_war": len(wars) > 0,
                "snapshot_round": candidate,
            }
    return {
        "gdp": 0.0, "treasury": 0.0, "stability": 0,
        "political_support": 0, "war_tiredness": 0,
        "at_war_with": [], "at_war": False,
        "snapshot_round": round_num,
    }


def _load_wars(client, country_code: str) -> list[str]:
    """Return the list of country_codes this country is at war with."""
    out: list[str] = []
    try:
        res = (
            client.table("relationships")
            .select("from_country_code, to_country_code, relationship, status")
            .or_(
                f"from_country_code.eq.{country_code},"
                f"to_country_code.eq.{country_code}"
            )
            .execute()
        )
        for row in (res.data or []):
            rel = (row.get("relationship") or row.get("status") or "").lower()
            if rel != "war":
                continue
            other = (
                row["to_country_code"]
                if row.get("from_country_code") == country_code
                else row.get("from_country_code")
            )
            if other:
                out.append(other)
    except Exception as e:
        logger.debug("wars lookup failed for %s: %s", country_code, e)
    return out


def _load_my_units(
    client, sim_run_id: str, country_code: str, round_num: int,
) -> list[dict]:
    """Return full inventory of own units at round_num (or most recent prior)."""
    # Find the latest round_num <= round_num that has any rows for this country.
    latest = (
        client.table("unit_states_per_round")
        .select("round_num")
        .eq("sim_run_id", sim_run_id)
        .eq("country_code", country_code)
        .lte("round_num", round_num)
        .order("round_num", desc=True)
        .limit(1)
        .execute()
    )
    if not latest.data:
        return []
    snapshot_round = latest.data[0]["round_num"]
    res = (
        client.table("unit_states_per_round")
        .select(
            "unit_code, unit_type, status, global_row, global_col, "
            "theater, theater_row, theater_col, embarked_on"
        )
        .eq("sim_run_id", sim_run_id)
        .eq("country_code", country_code)
        .eq("round_num", snapshot_round)
        .execute()
    )
    return [dict(row) for row in (res.data or [])]


def _load_zones_table(client) -> list[dict]:
    """Load the canonical 57 zones from the zones table (for the world map)."""
    try:
        res = client.table("zones").select("*").execute()
        return list(res.data or [])
    except Exception as e:
        logger.warning("zones table load failed: %s", e)
        return []


def _load_zone_adjacency(client) -> list[dict]:
    """Load the zone_adjacency edges as a flat list of {zone_a, zone_b}."""
    try:
        res = client.table("zone_adjacency").select(
            "zone_a, zone_b, connection_type"
        ).execute()
        return [
            {
                "zone_a": r.get("zone_a"),
                "zone_b": r.get("zone_b"),
                "connection_type": r.get("connection_type"),
            }
            for r in (res.data or [])
        ]
    except Exception as e:
        logger.warning("zone_adjacency load failed: %s", e)
        return []


def _load_recent_combat(
    client, sim_run_id: str, country_code: str, round_num: int,
) -> list[dict]:
    """Last 3 rounds of combat events involving this country (attacker or defender)."""
    out: list[dict] = []
    try:
        low = max(0, round_num - 3)
        res = (
            client.table("observatory_combat_results")
            .select(
                "round_num, combat_type, attacker_country, defender_country, "
                "location_global_row, location_global_col, narrative"
            )
            .eq("sim_run_id", sim_run_id)
            .gte("round_num", low)
            .lte("round_num", round_num)
            .or_(
                f"attacker_country.eq.{country_code},"
                f"defender_country.eq.{country_code}"
            )
            .order("round_num", desc=True)
            .execute()
        )
        for row in (res.data or []):
            out.append({
                "round_num": row.get("round_num"),
                "combat_type": row.get("combat_type"),
                "attacker_country": row.get("attacker_country"),
                "defender_country": row.get("defender_country"),
                "global_row": row.get("location_global_row"),
                "global_col": row.get("location_global_col"),
                "narrative": row.get("narrative"),
            })
    except Exception as e:
        logger.debug("recent combat lookup failed: %s", e)
    return out


def _decision_rules_text() -> str:
    """Return the decision rules text block per CONTRACT_MOVEMENT v1.0 §3.10."""
    return """HOW MOVEMENT WORKS (mechanically)
- Three use cases per unit: reposition / deploy from reserve / withdraw to reserve
- Two auto-detected flows: embark (onto own naval with capacity) / debark (implicit)
- Range: unlimited during deployment phase
- Timing: moves take effect at the start of the next round
- One move_units submission per country per round (batch all moves together)
- Last submission in a round wins (supports human correction)

CONSTRAINTS by unit type
- Ground / AD / Strategic Missile: target hex NOT sea; must be own territory,
  basing-rights zone, OR previously occupied hex (>=1 own unit there)
- Tactical Air: same as ground, PLUS can auto-embark on own naval
- Naval: sea hexes ONLY (cannot touch land)
- Carrier capacity: 1 ground + 2 tactical_air per friendly naval

DECISION RULES
- decision="change"    -> must include changes.moves with >=1 valid move
- decision="no_change" -> must OMIT the changes field entirely
- rationale >=30 chars REQUIRED in both cases
- duplicate unit_code in the same batch is invalid

REMINDER -- no_change is a legitimate choice
Movement has real costs: units in transit are committed, withdrawing to
reserve loses a round of availability. If your current deployment serves
your goals, no_change with a clear rationale is the correct answer."""


__all__ = ["build_movement_context"]
