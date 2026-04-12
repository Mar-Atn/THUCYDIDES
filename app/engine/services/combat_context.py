"""Combat decision context builder — CONTRACT_GROUND_COMBAT v1.0 §3.

Pure read-only service: ``build_ground_combat_context(country_code,
scenario_code, round_num, sim_run_id?)`` returns the validator-grade dict
the AI sees before deciding whether to launch a ground attack.

Per F1 boundary, this is **decision-specific only** — no cognitive
context, no doctrine, no goals. The AI Participant Module v1.0 will
compose those layers separately. See ``F1_CONTEXT_GAPS.md``.

The heart of the context is the **adjacent enemy hexes** block. For each
of the AI's source hexes (hexes containing ≥1 own active ground unit),
the validator pre-computes adjacent hexes containing enemy units, plus
the modifier flags that WOULD apply if an attack were launched.

Used by:
- AI skill harness (M2 L3 tests)
- Future AI Participant Module
- Test fixtures
"""

from __future__ import annotations

import logging
from typing import Optional

from engine.services.supabase import get_client

logger = logging.getLogger(__name__)

GROUND_ATTACKER_TYPES = frozenset({"ground", "armor"})


def build_ground_combat_context(
    country_code: str,
    scenario_code: str,
    round_num: int,
    sim_run_id: Optional[str] = None,
) -> dict:
    """Assemble the M2 ground combat decision context.

    F1: pass an explicit ``sim_run_id`` to read from an isolated run,
    otherwise resolves to the legacy archived run for ``scenario_code``.

    Returns a dict matching CONTRACT_GROUND_COMBAT v1.0 §3.
    """
    from engine.services.sim_run_manager import resolve_sim_run_id

    client = get_client()
    sim_run_id = sim_run_id or resolve_sim_run_id(scenario_code)

    # 1. Load all units for this round (pre-attack snapshot)
    units = _load_units(client, sim_run_id, round_num)

    # 2. Load own country snapshot for economic_state
    own_state = _load_country_state(client, sim_run_id, round_num, country_code)

    # 3. Group own active ground units by source hex
    my_grounds = [
        u for u in units
        if u.get("country_code") == country_code
        and (u.get("unit_type") or "").lower() in GROUND_ATTACKER_TYPES
        and (u.get("status") or "").lower() == "active"
        and u.get("global_row") is not None
        and u.get("global_col") is not None
    ]
    source_hexes: dict[tuple[int, int], list[dict]] = {}
    for u in my_grounds:
        key = (u["global_row"], u["global_col"])
        source_hexes.setdefault(key, []).append({
            "unit_code": u["unit_code"],
            "unit_type": u["unit_type"],
            "status": u["status"],
        })

    # 4. For each source hex, find adjacent enemy hexes + their composition + modifier flags
    adjacent_enemy_hexes = []
    for (sr, sc), src_units in sorted(source_hexes.items()):
        for nr, nc in _hex_neighbors(sr, sc):
            enemies_here = [
                u for u in units
                if u.get("global_row") == nr and u.get("global_col") == nc
                and u.get("country_code") not in (None, country_code)
                and (u.get("status") or "").lower() == "active"
            ]
            if not enemies_here:
                continue
            enemy_country = enemies_here[0].get("country_code")
            comp: dict[str, int] = {}
            for u in enemies_here:
                t = (u.get("unit_type") or "?").lower()
                comp[t] = comp.get(t, 0) + 1
            mods = _preview_modifiers(
                client, sim_run_id, round_num,
                attacker_country=country_code,
                defender_country=enemy_country,
                target_row=nr, target_col=nc,
                units=units,
                attacker_units_at_source=[u for u in my_grounds if (u["global_row"], u["global_col"]) == (sr, sc)],
            )
            adjacent_enemy_hexes.append({
                "source": {"global_row": sr, "global_col": sc},
                "target": {"global_row": nr, "global_col": nc},
                "enemy_country": enemy_country,
                "defenders": comp,
                "modifiers_preview": mods,
            })

    # 5. Recent combat events (last 3 rounds)
    recent = _load_recent_combat(client, sim_run_id, country_code, round_num)

    # 6. Build the result
    return {
        "country_code": country_code,
        "round_num": round_num,
        "economic_state": {
            "gdp": float(own_state.get("gdp") or 0),
            "treasury": float(own_state.get("treasury") or 0),
            "stability": int(own_state.get("stability") or 5),
            "war_tiredness": int(own_state.get("war_tiredness") or 0),
            "at_war_with": _at_war_with(client, country_code),
        },
        "my_ground_forces_by_hex": {
            f"{sr},{sc}": units_list
            for (sr, sc), units_list in sorted(source_hexes.items())
        },
        "adjacent_enemy_hexes": adjacent_enemy_hexes,
        "recent_combat_events": recent,
        "decision_rules": _decision_rules_text(),
        "instruction": (
            "Decide whether to LAUNCH a ground attack this round (change) or "
            "HOLD (no_change). One source hex → one adjacent target per "
            "decision. Submit multiple decisions for multiple attacks. "
            "Either way you MUST provide a rationale of at least 30 chars. "
            "Respond with JSON ONLY matching CONTRACT_GROUND_COMBAT §2."
        ),
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _hex_neighbors(row: int, col: int) -> list[tuple[int, int]]:
    """Cardinal 4-neighbors on the global hex grid (1..10, 1..20)."""
    out: list[tuple[int, int]] = []
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nr, nc = row + dr, col + dc
        if 1 <= nr <= 10 and 1 <= nc <= 20:
            out.append((nr, nc))
    return out


def _load_units(client, sim_run_id: str, round_num: int) -> list[dict]:
    """Load the unit_states_per_round snapshot for the round (or fall back to most recent)."""
    res = (
        client.table("unit_states_per_round")
        .select("unit_code,country_code,unit_type,status,global_row,global_col,embarked_on")
        .eq("sim_run_id", sim_run_id)
        .lte("round_num", round_num)
        .order("round_num", desc=True)
        .execute()
    )
    rows = res.data or []
    if not rows:
        return []
    # Group to latest row per unit_code
    latest: dict[str, dict] = {}
    for r in rows:
        c = r.get("unit_code")
        if c and c not in latest:
            latest[c] = r
    return list(latest.values())


def _load_country_state(client, sim_run_id: str, round_num: int, country_code: str) -> dict:
    """Load the latest country snapshot at or before this round."""
    res = (
        client.table("country_states_per_round")
        .select("gdp,treasury,inflation,stability,political_support,war_tiredness,ai_level")
        .eq("sim_run_id", sim_run_id)
        .eq("country_code", country_code)
        .lte("round_num", round_num)
        .order("round_num", desc=True)
        .limit(1)
        .execute()
    )
    return (res.data or [{}])[0]


def _at_war_with(client, country_code: str) -> list[str]:
    """Return list of countries this country is at war with (best-effort)."""
    out: list[str] = []
    try:
        res = client.table("relationships") \
            .select("from_country_id,to_country_id,status,relationship") \
            .or_(f"from_country_id.eq.{country_code},to_country_id.eq.{country_code}") \
            .execute()
        for r in (res.data or []):
            rel = (r.get("status") or r.get("relationship") or "").lower()
            if "war" in rel or "military_conflict" in rel:
                other = r["to_country_id"] if r.get("from_country_id") == country_code else r.get("from_country_id")
                if other:
                    out.append(other)
    except Exception as e:
        logger.debug("at_war_with lookup failed: %s", e)
    return out


def _load_recent_combat(
    client, sim_run_id: str, country_code: str, round_num: int,
) -> list[dict]:
    """Last 3 rounds of combat events involving this country."""
    out: list[dict] = []
    try:
        low = max(0, round_num - 3)
        res = (
            client.table("observatory_combat_results")
            .select("round_num,combat_type,attacker_country,defender_country,"
                    "location_global_row,location_global_col,narrative")
            .eq("sim_run_id", sim_run_id)
            .gte("round_num", low)
            .lte("round_num", round_num)
            .or_(f"attacker_country.eq.{country_code},defender_country.eq.{country_code}")
            .order("round_num", desc=True)
            .execute()
        )
        for row in (res.data or []):
            out.append({
                "round_num": row["round_num"],
                "combat_type": row.get("combat_type"),
                "attacker": row.get("attacker_country"),
                "defender": row.get("defender_country"),
                "location": [row.get("location_global_row"), row.get("location_global_col")],
                "narrative": row.get("narrative"),
            })
    except Exception as e:
        logger.debug("recent_combat lookup failed: %s", e)
    return out


def _preview_modifiers(
    client, sim_run_id: str, round_num: int,
    attacker_country: str, defender_country: str,
    target_row: int, target_col: int,
    units: list[dict],
    attacker_units_at_source: list[dict],
) -> list[dict]:
    """Preview the modifier list that WOULD apply if this attack happened.

    Mirrors `engine.round_engine.resolve_round._build_ground_modifiers`
    but takes its inputs as already-loaded data dicts so this stays a
    pure read.
    """
    mods: list[dict] = []

    # Defender air support
    def_air = next((
        u for u in units
        if u.get("global_row") == target_row and u.get("global_col") == target_col
        and u.get("country_code") == defender_country
        and (u.get("unit_type") or "").lower() == "tactical_air"
        and (u.get("status") or "").lower() not in ("destroyed", "embarked")
    ), None)
    if def_air:
        mods.append({"side": "defender", "value": 1, "reason": f"air_support: {def_air['unit_code']} on hex"})

    # Amphibious: any attacker is currently embarked
    for au in attacker_units_at_source:
        if au.get("embarked_on") or (au.get("status") == "embarked"):
            mods.append({"side": "attacker", "value": -1, "reason": "amphibious assault from embarked carrier"})
            break

    # AI L4 + low morale: read country snapshots
    atk_state = _load_country_state(client, sim_run_id, round_num, attacker_country)
    def_state = _load_country_state(client, sim_run_id, round_num, defender_country)

    if int(atk_state.get("ai_level", 0) or 0) >= 4:
        mods.append({"side": "attacker", "value": 1, "reason": "ai_l4 doctrine bonus"})
    if int(def_state.get("ai_level", 0) or 0) >= 4:
        mods.append({"side": "defender", "value": 1, "reason": "ai_l4 doctrine bonus"})
    if int(atk_state.get("stability", 5) or 5) <= 3:
        mods.append({"side": "attacker", "value": -1, "reason": "low morale (stability ≤ 3)"})
    if int(def_state.get("stability", 5) or 5) <= 3:
        mods.append({"side": "defender", "value": -1, "reason": "low morale (stability ≤ 3)"})

    return mods


def _decision_rules_text() -> str:
    return """HOW GROUND COMBAT WORKS (RISK iterative dice)
- Attacker selects units from ONE source hex, attacks ONE adjacent enemy hex
- Must leave ≥1 ground unit on every occupied FOREIGN hex (own territory may be emptied)
- Each exchange: attacker rolls min(3, attackers_alive) dice, defender rolls min(2, defenders_alive) dice
- Compare highest-vs-highest then second-vs-second; ties go to defender; losing pair removes one unit
- Loop until one side has zero units
- Modifiers apply to highest die per side per exchange (max bonus = +2)
- Approximate win rates: no mods 42%, def +1 28%, def +2 17%, atk -1 vs def +2 8%

ON ATTACKER VICTORY
- All surviving attackers move ONTO captured hex
- Non-ground enemy units on hex become CAPTURED → attacker's reserve, original type preserved
- Hex becomes occupied_by=attacker (owner stays original)
- IF ≥2 surviving attackers AND adjacent enemy hex AND allow_chain=true: chain attack auto-fires (leaves ≥1 unit behind on the just-captured hex)
- Chain max bound: 10 hops

DECISION RULES
- decision="change"    → MUST include all 5 changes fields (source/target row+col + attacker_unit_codes)
- decision="no_change" → MUST OMIT the changes field entirely
- rationale ≥ 30 chars REQUIRED in both cases
- One attack per decision; submit multiple decisions for multiple attacks

REMINDER — no_change is a legitimate choice
Combat has real costs: unit losses, war tiredness, stability hits, GDP damage from
infrastructure destruction. If your current position serves your goals, no_change
with a clear rationale is the correct answer.
"""


def build_air_strike_context(
    country_code: str,
    scenario_code: str,
    round_num: int,
    sim_run_id: Optional[str] = None,
) -> dict:
    """Assemble the M3 air strike decision context.

    Returns a dict matching CONTRACT_AIR_STRIKES v1.0 §6:
      - economic_state
      - my_air_forces_by_hex (own active tactical_air grouped by hex)
      - targetable_enemy_hexes (within 2-hex range, with hit_prob preview)
      - recent_combat_events
      - decision_rules + instruction
    """
    from engine.services.sim_run_manager import resolve_sim_run_id

    client = get_client()
    sim_run_id = sim_run_id or resolve_sim_run_id(scenario_code)

    units = _load_units(client, sim_run_id, round_num)
    own_state = _load_country_state(client, sim_run_id, round_num, country_code)

    # Group own active tactical_air by source hex
    my_air = [
        u for u in units
        if u.get("country_code") == country_code
        and (u.get("unit_type") or "").lower() == "tactical_air"
        and (u.get("status") or "").lower() == "active"
        and u.get("global_row") is not None
    ]
    source_hexes: dict[tuple[int, int], list[dict]] = {}
    for u in my_air:
        key = (u["global_row"], u["global_col"])
        source_hexes.setdefault(key, []).append({
            "unit_code": u["unit_code"],
            "unit_type": u["unit_type"],
            "status": u["status"],
        })

    # For each source hex, find enemy hexes within 2 cardinal hexes
    targetable: list[dict] = []
    for (sr, sc), src_units in sorted(source_hexes.items()):
        for tr in range(max(1, sr - 2), min(10, sr + 2) + 1):
            for tc in range(max(1, sc - 2), min(20, sc + 2) + 1):
                if (tr, tc) == (sr, sc):
                    continue
                if abs(tr - sr) + abs(tc - sc) > 2:
                    continue
                enemies = [
                    u for u in units
                    if u.get("global_row") == tr and u.get("global_col") == tc
                    and u.get("country_code") not in (None, country_code)
                    and (u.get("status") or "").lower() == "active"
                ]
                if not enemies:
                    continue
                enemy_country = enemies[0].get("country_code")
                comp: dict[str, int] = {}
                for u in enemies:
                    t = (u.get("unit_type") or "?").lower()
                    comp[t] = comp.get(t, 0) + 1
                # AD coverage preview: any enemy AD on this hex
                ad_present = any(
                    (u.get("unit_type") or "").lower() == "air_defense"
                    for u in enemies
                )
                # Per CARD_FORMULAS D.2: 12% base, 6% with AD. No air superiority bonus.
                hit_prob = 0.12 * (0.5 if ad_present else 1.0)
                downed_prob = 0.15 if ad_present else 0.0
                targetable.append({
                    "source": {"global_row": sr, "global_col": sc},
                    "target": {"global_row": tr, "global_col": tc},
                    "distance": abs(tr - sr) + abs(tc - sc),
                    "enemy_country": enemy_country,
                    "defenders": comp,
                    "ad_coverage": ad_present,
                    "hit_prob_preview": round(hit_prob, 4),
                    "downed_prob_preview": round(downed_prob, 4),
                })

    recent = _load_recent_combat(client, sim_run_id, country_code, round_num)

    return {
        "country_code": country_code,
        "round_num": round_num,
        "economic_state": {
            "gdp": float(own_state.get("gdp") or 0),
            "treasury": float(own_state.get("treasury") or 0),
            "stability": int(own_state.get("stability") or 5),
            "war_tiredness": int(own_state.get("war_tiredness") or 0),
            "at_war_with": _at_war_with(client, country_code),
        },
        "my_air_forces_by_hex": {
            f"{sr},{sc}": units_list
            for (sr, sc), units_list in sorted(source_hexes.items())
        },
        "targetable_enemy_hexes": targetable,
        "recent_combat_events": recent,
        "decision_rules": _air_strike_rules_text(),
        "instruction": (
            "Decide whether to LAUNCH an air strike this round (change) or "
            "HOLD (no_change). One source hex → one target hex per decision. "
            "Submit multiple decisions for multiple strikes. "
            "Either way you MUST provide a rationale of at least 30 chars. "
            "Respond with JSON ONLY matching CONTRACT_AIR_STRIKES §2."
        ),
    }


def _air_strike_rules_text() -> str:
    return """HOW AIR STRIKES WORK (probability rolls per attacker)
- Source hex must contain own active tactical_air units
- Target hex must contain enemy active units
- Range: ≤2 cardinal hexes (Manhattan distance)
- Each attacker rolls INDEPENDENTLY for hit + AD downed
- Hit probability: 12% base + 2% per extra friendly tac_air on source (cap +4%), HALVED if AD covers target
- Hit probability is clamped to [3%, 20%]
- AD-downed probability: 15% per shot if any enemy AD covers the target
- Hit and downed are independent (attacker can hit AND be downed)
- Templates may customize all percentages

DECISION RULES
- decision="change"    → MUST include source/target row+col + attacker_unit_codes
- decision="no_change" → MUST OMIT the changes field entirely
- rationale ≥ 30 chars REQUIRED in both cases
- One strike per decision; submit multiple decisions for multiple strikes

REMINDER — no_change is a legitimate choice
Air strikes have low hit rates and risk losing aircraft to AD. If your
current air assets are better held in reserve, no_change with a clear
rationale is the correct answer.
"""


__all__ = ["build_ground_combat_context", "build_air_strike_context"]
