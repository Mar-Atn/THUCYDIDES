"""Tariff decision context assembler — CONTRACT_TARIFFS v1.0 §3.

Step 5 of the tariff vertical slice.

Pure read-only service: ``build_tariff_context(country_code, scenario_code,
round_num)`` assembles the decision-specific context payload for a tariff
decision-maker (AI or human). No DB mutations, no cognitive blocks.

Context includes:
* economic_state — own country snapshot
* country_roster — all 20 countries with GDP, sector profile, relationship, trade rank
* my_tariffs — current tariffs I impose (from tariffs state table)
* tariffs_on_me — current tariffs others impose on me
* decision_rules — text block describing levels 0-3, carry-forward, no_change reminder
* instruction — what to decide + JSON schema pointer
"""
from __future__ import annotations

import logging

from engine.engines.economic import derive_trade_weights
from engine.engines.round_tick import _merge_to_engine_dict, _safe_float
from engine.services.supabase import get_client

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_tariff_context(
    country_code: str,
    scenario_code: str,
    round_num: int,
    sim_run_id: str | None = None,
) -> dict:
    """Assemble the full context package for a tariff decision.

    Returns a dict matching CONTRACT_TARIFFS v1.0 §3. Pure read — no DB
    mutations. If ``round_num`` has no snapshot row yet, falls back to
    ``round_num - 1``.

    F1 (2026-04-11): ``sim_run_id`` may be passed explicitly to target an
    isolated run; otherwise resolves to the legacy archived run for the
    scenario.
    """
    from engine.services.sim_run_manager import resolve_sim_run_id
    client = get_client()
    sim_run_id = sim_run_id or resolve_sim_run_id(scenario_code)

    base_countries = _load_base_countries(client)
    if country_code not in base_countries:
        raise ValueError(f"Unknown country '{country_code}'")

    # Load snapshot for target round, fall back to N-1
    snapshot_round, rs_row = _load_snapshot(
        client, sim_run_id, country_code, round_num
    )

    country = _merge_to_engine_dict(base_countries[country_code], rs_row or {})
    eco = country["economic"]
    pol = country["political"]

    # 1. economic_state — own country snapshot
    economic_state = {
        "gdp": round(eco.get("gdp", 0.0), 2),
        "treasury": round(eco.get("treasury", 0.0), 2),
        "inflation": round(eco.get("inflation", 0.0), 4),
        "sector_mix": {
            "resources": round(eco["sectors"].get("resources", 0.20), 4),
            "industry": round(eco["sectors"].get("industry", 0.30), 4),
            "services": round(eco["sectors"].get("services", 0.30), 4),
            "technology": round(eco["sectors"].get("technology", 0.20), 4),
        },
        "trade_balance": round(eco.get("trade_balance", 0.0), 2),
        "oil_producer": eco.get("oil_producer", False),
        "oil_production_mbpd": round(eco.get("oil_production_mbpd", 0.0), 2),
        "stability": float(pol.get("stability", 5)),
        "political_support": float(pol.get("political_support", 50)),
        "snapshot_round": snapshot_round,
    }

    # 2. country_roster — all 20 countries
    # Build engine dicts for trade weight computation
    all_countries = {}
    for cc, base in base_countries.items():
        if cc == country_code:
            all_countries[cc] = country
        else:
            all_countries[cc] = _merge_to_engine_dict(base, {})

    trade_weights = derive_trade_weights(all_countries)
    my_weights = trade_weights.get(country_code, {})

    # Sort partners by trade weight descending -> assign rank 1..19
    sorted_partners = sorted(my_weights.items(), key=lambda x: x[1], reverse=True)
    rank_map = {}
    for rank, (cc, _weight) in enumerate(sorted_partners, start=1):
        rank_map[cc] = rank

    # Load relationships
    relationships = _load_all_relationships(client, country_code)

    country_roster = []
    for cc, base in base_countries.items():
        if cc == country_code:
            continue  # self excluded from roster
        merged = all_countries[cc]
        merged_eco = merged["economic"]
        sector_profile = _derive_sector_profile(merged_eco)
        country_roster.append({
            "code": cc,
            "gdp": round(merged_eco.get("gdp", 0.0), 2),
            "sector_profile": sector_profile,
            "relationship_status": relationships.get(cc, "neutral"),
            "trade_rank": rank_map.get(cc, 19),
        })

    # Sort roster by trade_rank ascending
    country_roster.sort(key=lambda x: x["trade_rank"])

    # 3. my_tariffs — current tariffs I impose
    my_tariffs = _load_my_tariffs(client, country_code)

    # 4. tariffs_on_me — current tariffs others impose on me
    tariffs_on_me = _load_tariffs_on_me(client, country_code)

    # 5. decision_rules — text block
    decision_rules = _decision_rules_text()

    # 6. instruction
    instruction = (
        "Decide whether to CHANGE your tariff posture or keep it NO_CHANGE.\n"
        "Either way you MUST provide a rationale of at least 30 characters\n"
        "explaining WHY.\n\n"
        "Respond with JSON ONLY, matching the schema in CONTRACT_TARIFFS §2."
    )

    return {
        "country_code": country_code,
        "round_num": round_num,
        "economic_state": economic_state,
        "country_roster": country_roster,
        "my_tariffs": my_tariffs,
        "tariffs_on_me": tariffs_on_me,
        "decision_rules": decision_rules,
        "instruction": instruction,
    }


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _get_scenario_id(client, scenario_code: str) -> str:
    res = (
        client.table("sim_scenarios")
        .select("id")
        .eq("code", scenario_code)
        .limit(1)
        .execute()
    )
    if not res.data:
        raise ValueError(f"Scenario '{scenario_code}' not found")
    return res.data[0]["id"]


def _load_base_countries(client) -> dict[str, dict]:
    res = client.table("countries").select("*").execute()
    out: dict[str, dict] = {}
    for row in (res.data or []):
        cid = (row.get("sim_name", "") or "").lower().replace(" ", "")
        if cid:
            out[cid] = row
    return out


def _load_snapshot(
    client, sim_run_id: str, country_code: str, round_num: int,
) -> tuple[int, dict | None]:
    """Return (actual_round_used, row_dict_or_None).

    Tries ``round_num`` first, falls back to ``round_num - 1`` if no row.
    """
    for candidate in (round_num, round_num - 1):
        if candidate < 0:
            continue
        res = (
            client.table("country_states_per_round")
            .select("*")
            .eq("sim_run_id", sim_run_id)
            .eq("round_num", candidate)
            .eq("country_code", country_code)
            .limit(1)
            .execute()
        )
        if res.data:
            return candidate, res.data[0]
    return round_num, None


def _derive_sector_profile(eco: dict) -> str:
    """Short label derived from the dominant 1-2 sectors."""
    sectors = eco.get("sectors", {})
    # Sort by value descending
    ranked = sorted(sectors.items(), key=lambda x: x[1], reverse=True)
    if not ranked:
        return "mixed"
    top = ranked[0]
    if len(ranked) >= 2:
        second = ranked[1]
        # Only include second if it's at least 60% of the top
        if second[1] >= top[1] * 0.6:
            return f"{top[0]} / {second[0]}"
    return top[0]


def _load_all_relationships(client, country_code: str) -> dict[str, str]:
    """Return {other_code: status_string} for all countries that have a
    relationship entry with country_code."""
    result: dict[str, str] = {}
    try:
        res = (
            client.table("relationships")
            .select("from_country_id, to_country_id, status")
            .or_(
                f"from_country_id.eq.{country_code},"
                f"to_country_id.eq.{country_code}"
            )
            .execute()
        )
        for row in (res.data or []):
            other = (
                row["to_country_id"]
                if row.get("from_country_id") == country_code
                else row.get("from_country_id")
            )
            if not other:
                continue
            status = (row.get("status") or "neutral").lower()
            result[other] = status
    except Exception as e:
        logger.debug("relationships lookup failed for %s: %s", country_code, e)
    return result


def _load_my_tariffs(client, country_code: str) -> list[dict]:
    """Load tariffs I impose from the tariffs state table."""
    from engine.config.settings import Settings
    sim_run_id = Settings().default_sim_id
    tariffs: list[dict] = []
    try:
        res = (
            client.table("tariffs")
            .select("target_country_id, level, notes")
            .eq("sim_run_id", sim_run_id)
            .eq("imposer_country_id", country_code)
            .execute()
        )
        for row in (res.data or []):
            target = row.get("target_country_id", "")
            level = row.get("level", 0)
            if target and level > 0:
                tariffs.append({
                    "target": target,
                    "level": int(level),
                    "notes": row.get("notes", ""),
                })
    except Exception as e:
        logger.debug("tariffs lookup (imposer) failed for %s: %s", country_code, e)
    return tariffs


def _load_tariffs_on_me(client, country_code: str) -> list[dict]:
    """Load tariffs others impose on me from the tariffs state table."""
    from engine.config.settings import Settings
    sim_run_id = Settings().default_sim_id
    tariffs: list[dict] = []
    try:
        res = (
            client.table("tariffs")
            .select("imposer_country_id, level, notes")
            .eq("sim_run_id", sim_run_id)
            .eq("target_country_id", country_code)
            .execute()
        )
        for row in (res.data or []):
            imposer = row.get("imposer_country_id", "")
            level = row.get("level", 0)
            if imposer and level > 0:
                tariffs.append({
                    "imposer": imposer,
                    "level": int(level),
                    "notes": row.get("notes", ""),
                })
    except Exception as e:
        logger.debug("tariffs lookup (target) failed for %s: %s", country_code, e)
    return tariffs


def _decision_rules_text() -> str:
    """Return the decision rules text block per CONTRACT_TARIFFS v1.0 §3.6."""
    return """HOW TARIFFS WORK (mechanically)
- Bilateral. Set a level (0-3) for any subset of the other 19 countries.
- Levels: 0 = none / lift, 1 = light, 2 = moderate, 3 = heavy / near-embargo.
- As imposer you get: customs revenue + small self-damage + inflation pressure.
- As target you get: GDP hit proportional to imposer's market share.
- Setting a target to 0 LIFTS the tariff. No separate "lift" action.
- Untouched targets keep their previous level (carry-forward).
- Trade agreements (separate action) override tariffs between signatories.

DECISION RULES
- decision="change"    -> must include changes.tariffs with >=1 (target, level) entry
- decision="no_change" -> must OMIT the changes field entirely
- rationale >=30 chars REQUIRED in both cases
- self-tariff and unknown-target are validation errors

REMINDER -- no_change is a legitimate choice
Tariffs are a possibility, not an obligation. If your current posture still
serves your goals, no_change is the right answer with a clear rationale.
Do not invent changes for the sake of action."""
