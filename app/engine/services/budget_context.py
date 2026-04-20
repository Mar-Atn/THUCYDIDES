"""Budget context assembler + dry-run forecast.

Step 5 of the budget vertical slice (CONTRACT_BUDGET v1.1 §3).

Two pure, read-only services:

* ``build_budget_context(country_code, scenario_code, round_num)`` — assembles
  the BUDGET REVIEW DATA payload for a decision-maker (AI or human). Reads
  only from DB state tables + structural ``countries`` data. No mutations.

* ``dry_run_budget(country_code, scenario_code, round_num, budget_override)``
  — runs the same economic engine functions used by ``round_tick`` on an
  in-memory country dict, then discards the dict. Produces expected treasury,
  stability, unit counts, R&D progress, etc. WITHOUT persisting anything.

Architectural notes:
  * Both functions load fresh country dicts per call (no shared state).
  * The dry-run reuses ``_merge_to_engine_dict`` from ``round_tick`` so the
    in-memory country shape matches the real pipeline exactly. This is the
    guarantee that the "no-change forecast" in the context package matches
    what the engine will actually compute when the round is resolved.
  * If the requested round row does not yet exist in
    ``country_states_per_round``, we fall back to round N-1 (typical when
    the context is assembled BEFORE the snapshot for round N is cloned).
"""
from __future__ import annotations

import copy
import logging

from engine.engines.economic import (
    BUDGET_PRODUCTION_BRANCHES,
    MAINTENANCE_MULTIPLIER,
    OIL_BASE_PRICE,
    UNIT_TYPES,
    calc_budget_execution,
    calc_military_production,
    calc_oil_price,
    calc_revenue,
    calc_tech_advancement,
    derive_trade_weights,
)
from engine.engines.round_tick import _merge_to_engine_dict, _safe_float
from engine.services.supabase import get_client

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_budget_context(
    country_code: str,
    scenario_code: str,
    round_num: int,
    sim_run_id: str | None = None,
) -> dict:
    """Assemble the full context package for a budget decision.

    Returns a dict matching CONTRACT_BUDGET v1.1 §3.2. Pure read — no DB
    mutations. If ``round_num`` has no snapshot row yet, falls back to
    ``round_num - 1``.

    F1 (2026-04-11): ``sim_run_id`` may be passed explicitly to read from an
    isolated run. If omitted, resolves to the legacy archived run for the
    scenario (so pre-F1 callers that only pass ``scenario_code`` still work).
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
    mil = country["military"]
    tech = country["technology"]

    # Current budget from snapshot (defaults if null)
    current_budget = _extract_current_budget(rs_row or {})

    # Revenue forecast — compute oil, then call calc_revenue on a copy
    revenue_forecast = _compute_revenue_forecast(
        client, sim_run_id, base_countries, country_code, round_num
    )

    # Mandatory costs
    total_units = sum(int(mil.get(ut, 0) or 0) for ut in UNIT_TYPES)
    maint_rate = mil.get("maintenance_cost_per_unit", 0.02)
    maintenance = total_units * maint_rate * MAINTENANCE_MULTIPLIER

    social_baseline_pct = eco.get("social_spending_baseline", 0.25)
    # At social_pct=1.0 this is the "baseline" social cost
    social_baseline = social_baseline_pct * max(revenue_forecast["total"], 0.0)

    mandatory_total = maintenance + social_baseline
    discretionary = max(revenue_forecast["total"] - mandatory_total, 0.0)

    # Military state — what we have + production capacity
    cap = mil.get("production_capacity", {}) or {}
    military_state = {
        "ground": int(mil.get("ground", 0)),
        "naval": int(mil.get("naval", 0)),
        "tactical_air": int(mil.get("tactical_air", 0)),
        "strategic_missile": int(mil.get("strategic_missile", 0)),
        "air_defense": int(mil.get("air_defense", 0)),
        "production_capacity": {
            branch: int(cap.get(branch, 0) or 0)
            for branch in BUDGET_PRODUCTION_BRANCHES
        },
        "total_units": total_units,
    }

    # R&D progress
    research_progress = {
        "nuclear": {
            "level": int(tech.get("nuclear_level", 0) or 0),
            "progress": float(tech.get("nuclear_rd_progress", 0) or 0),
            "maxed": int(tech.get("nuclear_level", 0) or 0) >= 3,
        },
        "ai": {
            "level": int(tech.get("ai_level", 0) or 0),
            "progress": float(tech.get("ai_rd_progress", 0) or 0),
            "maxed": int(tech.get("ai_level", 0) or 0) >= 4,
        },
    }

    # Relationships — wars + alliances
    relationships = _load_relationships(client, country_code)

    # Economic state block
    economic_state = {
        "gdp": round(eco.get("gdp", 0.0), 2),
        "treasury": round(eco.get("treasury", 0.0), 2),
        "inflation": round(eco.get("inflation", 0.0), 4),
        "debt_burden": round(eco.get("debt_burden", 0.0), 2),
        "stability": float(country["political"].get("stability", 5)),
        "political_support": float(country["political"].get("political_support", 50)),
        "at_war_with": relationships["wars"],
        "snapshot_round": snapshot_round,
    }

    # No-change forecast — run dry_run with no override (uses current budget)
    try:
        no_change_forecast = dry_run_budget(
            country_code=country_code,
            scenario_code=scenario_code,
            round_num=round_num,
            budget_override=None,
            sim_run_id=sim_run_id,
        )
    except Exception as e:  # pragma: no cover — defensive
        logger.warning("no-change dry-run failed for %s R%d: %s",
                       country_code, round_num, e)
        no_change_forecast = {"error": str(e)}

    return {
        "country_code": country_code,
        "round_num": round_num,
        "economic_state": economic_state,
        "revenue_forecast": revenue_forecast,
        "mandatory_costs": {
            "maintenance": round(maintenance, 2),
            "social_baseline": round(social_baseline, 2),
            "total": round(mandatory_total, 2),
        },
        "discretionary": round(discretionary, 2),
        "military_state": military_state,
        "research_progress": research_progress,
        "current_budget": current_budget,
        "no_change_forecast": no_change_forecast,
        "relationships": relationships,
    }


def dry_run_budget(
    country_code: str,
    scenario_code: str,
    round_num: int,
    budget_override: dict | None = None,
    sim_run_id: str | None = None,
) -> dict:
    """Run the economic engine in dry-run mode — NO DB writes.

    Loads a fresh country dict, applies either ``budget_override`` or the
    budget currently persisted on the snapshot (via ``_extract_current_budget``),
    runs the same pure engine functions that ``round_tick`` does for the
    budget step, and returns the result as a flat dict.

    The loaded country dict is local to this call and discarded on return.

    F1: ``sim_run_id`` may be passed explicitly; otherwise resolves to the
    legacy archived run for ``scenario_code``.
    """
    from engine.services.sim_run_manager import resolve_sim_run_id
    client = get_client()
    sim_run_id = sim_run_id or resolve_sim_run_id(scenario_code)

    base_countries = _load_base_countries(client)
    if country_code not in base_countries:
        raise ValueError(f"Unknown country '{country_code}'")

    snapshot_round, rs_row = _load_snapshot(
        client, sim_run_id, country_code, round_num
    )

    # Build full-world engine dict (so calc_oil_price sees all producers)
    # but only CALL engine per-country on the target. We still want a fresh
    # deep-copied dict so mutations don't leak between calls.
    countries: dict[str, dict] = {}
    for cc, base in base_countries.items():
        # Use the same snapshot round for other countries (best-effort). For
        # the target country we already have rs_row; for others we re-query
        # the same round. If missing, engine uses structural base values.
        if cc == country_code:
            countries[cc] = _merge_to_engine_dict(base, rs_row or {})
        else:
            countries[cc] = _merge_to_engine_dict(base, {})
    # Deep-copy to guarantee isolation
    countries = copy.deepcopy(countries)

    # Populate oil revenue (mutates countries in place)
    log: list[str] = []
    try:
        calc_oil_price(
            countries=countries,
            opec_production={},
            chokepoint_status={},
            active_blockades={},
            formosa_blockade=False,
            wars=[],
            previous_oil_price=OIL_BASE_PRICE,
            oil_above_150_rounds=0,
            sanctions={},
            log=log,
        )
    except Exception as e:  # pragma: no cover
        logger.warning("dry-run oil price calc failed: %s", e)
        countries[country_code]["economic"]["oil_revenue"] = 0.0

    # Determine budget to apply
    if budget_override is not None:
        budget = _normalize_budget(budget_override)
    else:
        budget = _extract_current_budget(rs_row or {})

    # Snapshot pre-state for deltas
    pre_treasury = float(countries[country_code]["economic"].get("treasury", 0.0))
    pre_stability = float(countries[country_code]["political"].get("stability", 5))
    pre_support = float(countries[country_code]["political"].get("political_support", 50))
    pre_units = {
        branch: int(countries[country_code]["military"].get(branch, 0) or 0)
        for branch in BUDGET_PRODUCTION_BRANCHES
    }
    pre_nuclear = {
        "level": int(countries[country_code]["technology"].get("nuclear_level", 0) or 0),
        "progress": float(countries[country_code]["technology"].get("nuclear_rd_progress", 0) or 0),
    }
    pre_ai = {
        "level": int(countries[country_code]["technology"].get("ai_level", 0) or 0),
        "progress": float(countries[country_code]["technology"].get("ai_rd_progress", 0) or 0),
    }

    # Revenue — needs trade_weights for sanctions cost
    trade_weights = derive_trade_weights(countries)
    rev_result = calc_revenue(
        country_code, countries, wars=[], sanctions={},
        trade_weights=trade_weights, log=log,
    )

    # Budget execution (mutates eco: treasury, inflation, debt, social stash)
    bud_result, production_result = calc_budget_execution(
        country_code, countries, budget, rev_result.total, log,
    )

    # Military production (credits units to in-memory military dict)
    calc_military_production(
        country_code, countries, production_result, round_num, log,
    )

    # Tech advancement (updates progress + levels on in-memory tech dict)
    rd = {
        "nuclear": countries[country_code]["economic"].get(
            "_research_nuclear_coins", 0
        ),
        "ai": countries[country_code]["economic"].get(
            "_research_ai_coins", 0
        ),
    }
    calc_tech_advancement(
        country_code, countries, rd, rare_earth_restrictions={}, log=log,
    )

    # Extract post-state
    post = countries[country_code]
    post_eco = post["economic"]
    post_tech = post["technology"]
    post_mil = post["military"]

    # Units produced = post - pre (the engine ADDS to the dict)
    units_produced: dict[str, int] = {}
    for branch in BUDGET_PRODUCTION_BRANCHES:
        delta = int(post_mil.get(branch, 0) or 0) - pre_units[branch]
        units_produced[branch] = max(delta, 0)

    # R&D progress deltas (note: level-up resets progress to 0)
    research_progress = {}
    for key, pre_state in (("nuclear", pre_nuclear), ("ai", pre_ai)):
        level_attr = f"{key}_level"
        progress_attr = f"{key}_rd_progress"
        new_level = int(post_tech.get(level_attr, 0) or 0)
        new_progress = float(post_tech.get(progress_attr, 0) or 0)
        leveled_up = new_level > pre_state["level"]
        if leveled_up:
            # We can't easily reconstruct the delta after a level-up, but
            # the standard case is clear.
            delta = new_progress + 1.0 - pre_state["progress"]
        else:
            delta = new_progress - pre_state["progress"]
        coins = int(rd.get(key, 0) or 0)
        research_progress[key] = {
            "coins": coins,
            "delta": round(delta, 6),
            "level": new_level,
            "progress": round(new_progress, 6),
            "leveled_up": leveled_up,
        }

    # Stability / support deltas (from social spending only — other sources
    # are handled by calc_stability, not the budget step)
    stability_delta = float(bud_result.stability_delta)
    support_delta = float(bud_result.political_support_delta)

    expected_stability = _clamp(pre_stability + stability_delta, 0, 10)
    expected_support = _clamp(pre_support + support_delta, 0, 100)
    expected_treasury = float(post_eco.get("treasury", pre_treasury))

    # Warnings — budget-relevant advisories
    warnings: list[str] = []
    if bud_result.deficit > 0:
        warnings.append(
            f"Deficit of {bud_result.deficit:.1f} coins — "
            f"treasury drawn {bud_result.treasury_drawn:.1f}, "
            f"money printed {bud_result.money_printed:.1f}"
        )
    if pre_nuclear["level"] >= 3 and (rd.get("nuclear", 0) or 0) > 0:
        warnings.append("Nuclear already at T3 — research investment wasted")
    if pre_ai["level"] >= 4 and (rd.get("ai", 0) or 0) > 0:
        warnings.append("AI already at L4 — research investment wasted")
    if all(
        int((budget.get("production") or {}).get(b, 0) or 0) == 0
        for b in BUDGET_PRODUCTION_BRANCHES
    ):
        warnings.append("No military production this round")
    social_pct_val = float(budget.get("social_pct", 1.0) or 1.0)
    if social_pct_val <= 0.5 and pre_stability < 4:
        warnings.append("Austerity during unrest may trigger crisis")

    return {
        "social_spending": round(float(bud_result.social_spending), 2),
        "military_spending": round(float(bud_result.military_spending), 2),
        "research_spending": round(float(bud_result.research_spending), 2),
        "maintenance": round(float(bud_result.maintenance), 2),
        "total_spending": round(float(bud_result.total_spending), 2),
        "revenue": round(float(rev_result.total), 2),
        "deficit": round(float(bud_result.deficit), 2),
        "treasury_drawn": round(float(bud_result.treasury_drawn), 2),
        "money_printed": round(float(bud_result.money_printed), 2),
        "units_produced": units_produced,
        "coins_by_branch": {
            b: int(bud_result.coins_by_branch.get(b, 0) or 0)
            for b in BUDGET_PRODUCTION_BRANCHES
        },
        "research_progress": research_progress,
        "stability_delta": round(stability_delta, 4),
        "political_support_delta": round(support_delta, 4),
        "expected_treasury": round(expected_treasury, 2),
        "expected_stability": round(expected_stability, 2),
        "expected_support": round(expected_support, 2),
        "warnings": warnings,
        "budget_applied": budget,
    }


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))




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


def _extract_current_budget(rs_row: dict) -> dict:
    """Pull the v1.1 budget out of a country_states_per_round row.

    Returns a fully populated budget dict with defaults for any missing
    fields. Safe to pass directly to ``calc_budget_execution``.
    """
    social_pct = rs_row.get("budget_social_pct")
    production = rs_row.get("budget_production")
    research = rs_row.get("budget_research")

    return {
        "social_pct": _safe_float(social_pct, 1.0) if social_pct is not None else 1.0,
        "production": production or {
            "ground": 0,
            "naval": 0,
            "tactical_air": 0,
            "strategic_missile": 0,
            "air_defense": 0,
        },
        "research": research or {
            "nuclear_coins": 0,
            "ai_coins": 0,
        },
    }


def _normalize_budget(budget: dict) -> dict:
    """Fill missing keys in a partially-specified budget override."""
    out = {
        "social_pct": float(budget.get("social_pct", 1.0) or 1.0),
        "production": {
            "ground": 0,
            "naval": 0,
            "tactical_air": 0,
            "strategic_missile": 0,
            "air_defense": 0,
        },
        "research": {"nuclear_coins": 0, "ai_coins": 0},
    }
    prod = budget.get("production") or {}
    for branch in BUDGET_PRODUCTION_BRANCHES:
        try:
            out["production"][branch] = int(prod.get(branch, 0) or 0)
        except (TypeError, ValueError):
            out["production"][branch] = 0
    research = budget.get("research") or {}
    for key in ("nuclear_coins", "ai_coins"):
        try:
            out["research"][key] = int(research.get(key, 0) or 0)
        except (TypeError, ValueError):
            out["research"][key] = 0
    return out


def _compute_revenue_forecast(
    client, sim_run_id: str, base_countries: dict,
    country_code: str, round_num: int,
) -> dict:
    """Independent revenue forecast using calc_revenue on a fresh copy.

    Does NOT mutate any shared state. Same formulas as the real engine.
    """
    # Build a minimal countries dict — just the target country is enough for
    # calc_revenue (it only touches countries[country_code]).
    _, rs_row = _load_snapshot(client, sim_run_id, country_code, round_num)
    country = _merge_to_engine_dict(base_countries[country_code], rs_row or {})

    # Compute oil revenue (needs the producer set; pass a minimal world)
    countries = {country_code: country}
    # Also include other oil producers so supply/demand isn't degenerate —
    # but we only care about country_code's oil_revenue field.
    for cc, base in base_countries.items():
        if cc == country_code:
            continue
        if str(base.get("oil_producer", "False")).lower() == "true":
            countries[cc] = _merge_to_engine_dict(base, {})

    log: list[str] = []
    try:
        calc_oil_price(
            countries=countries,
            opec_production={},
            chokepoint_status={},
            active_blockades={},
            formosa_blockade=False,
            wars=[],
            previous_oil_price=OIL_BASE_PRICE,
            oil_above_150_rounds=0,
            sanctions={},
            log=log,
        )
    except Exception as e:  # pragma: no cover
        logger.warning("revenue-forecast oil calc failed: %s", e)
        country["economic"]["oil_revenue"] = 0.0

    trade_weights = derive_trade_weights(countries)
    rev_result = calc_revenue(
        country_code, countries, wars=[], sanctions={},
        trade_weights=trade_weights, log=log,
    )
    eco = country["economic"]
    return {
        "total": float(rev_result.total),
        "base_revenue": float(rev_result.base_revenue),
        "oil_revenue": float(rev_result.oil_revenue),
        "debt_cost": float(rev_result.debt_cost),
        "inflation_erosion": float(rev_result.inflation_erosion),
        "war_damage_cost": float(rev_result.war_damage_cost),
        "sanctions_cost": float(rev_result.sanctions_cost),
        "tax_rate": float(eco.get("tax_rate", 0.24)),
        "gdp": float(eco.get("gdp", 0.0)),
    }


def _load_relationships(client, country_code: str) -> dict:
    """Return wars + alliances for the given country.

    Reads from the canonical ``relationships`` state table.
    """
    wars: list[str] = []
    alliances: list[str] = []
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
            status = (row.get("status") or "").lower()
            if "conflict" in status or "war" in status:
                if other not in wars:
                    wars.append(other)
            elif status in ("allied", "friendly", "alliance"):
                if other not in alliances:
                    alliances.append(other)
    except Exception as e:  # pragma: no cover
        logger.debug("relationships lookup failed for %s: %s", country_code, e)
    return {"wars": wars, "alliances": alliances}
