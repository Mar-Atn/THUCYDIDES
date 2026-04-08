"""Round Tick — bridge between per-round snapshots and the designed engines.

Runs the economic + political + technology engines on `country_states_per_round`
data, merging with structural base data from the `countries` table.

This is the Phase 3 canonical module that gives the Observatory dynamic
country state changes between rounds (GDP, inflation, stability, treasury
etc.) — fixing the "engines-not-running" bug where country stats were
flat across rounds.

Called by ``full_round_runner`` after combat/movement resolution.

Design note: the long-term target is full orchestrator integration
(``engines/orchestrator.process_round``). This module is the bridge step
that reuses the designed engine functions without requiring the
orchestrator's sim_runs-based DB model.
"""
from __future__ import annotations

import logging
from typing import Any

from engine.services.supabase import get_client

logger = logging.getLogger(__name__)


def run_engine_tick(scenario_code: str, round_num: int) -> dict:
    """Run economic + political engines on the current round's country state.

    Steps:
        1. Load structural base data from ``countries`` table
        2. Load current ``country_states_per_round`` for this round
        3. Merge into engine-format dicts
        4. Call ``process_economy`` (11-step economic pipeline)
        5. Call ``calc_stability`` + ``calc_political_support`` per country
        6. Write updated values back to ``country_states_per_round``
        7. Update ``global_state_per_round`` (oil price etc.)

    Returns summary dict.
    """
    try:
        client = get_client()

        # 1. Load base structural data (immutable per template)
        base_countries = _load_base_countries(client)
        if not base_countries:
            return {"success": False, "error": "no countries in base table"}

        # 2. Load per-round state
        scen = client.table("sim_scenarios").select("id").eq("code", scenario_code).limit(1).execute()
        if not scen.data:
            return {"success": False, "error": f"scenario {scenario_code} not found"}
        scenario_id = scen.data[0]["id"]

        round_states = client.table("country_states_per_round") \
            .select("*").eq("scenario_id", scenario_id).eq("round_num", round_num).execute()
        if not round_states.data:
            return {"success": False, "error": f"no country_states for round {round_num}"}

        # Index by country_code
        round_by_cc = {}
        for rs in round_states.data:
            cc = rs.get("country_code")
            if cc:
                round_by_cc[cc] = rs

        # 3. Merge into engine-format dicts
        countries = {}
        for cc, base in base_countries.items():
            rs = round_by_cc.get(cc, {})
            countries[cc] = _merge_to_engine_dict(base, rs)

        # 4. Build REAL world_state from agent decisions + relationships
        actions = _extract_actions_from_decisions(client, scenario_id, round_num)
        war_countries = _extract_war_state(client, scenario_id)
        combat_losses = _count_combat_losses(client, scenario_id, round_num)
        world_state = _build_world_state(round_num, base_countries, actions, war_countries)

        # Mark countries at war + apply combat loss costs
        for cc, c in countries.items():
            c["_at_war"] = cc in war_countries
            losses = combat_losses.get(cc, 0)
            if losses > 0:
                # Each lost unit costs ~maintenance equivalent in treasury
                cost = losses * c["economic"].get("_loss_cost", 0.5)
                c["economic"]["treasury"] = max(0, c["economic"]["treasury"] - cost)

        # 4b. Formosa blockade semiconductor cascade (CARD_ACTIONS 1.10, CARD_FORMULAS D.8)
        formosa_blocked = _detect_formosa_blockade(client, scenario_id, round_num)
        if formosa_blocked:
            level = formosa_blocked  # "partial" or "full"
            multiplier = 0.10 if level == "partial" else 0.20
            for cc, c in countries.items():
                tech_sector = _safe_float(c["economic"].get("sector_technology"), 20) / 100.0
                gdp_hit = c["economic"]["gdp"] * multiplier * tech_sector
                c["economic"]["gdp"] = max(0.5, c["economic"]["gdp"] - gdp_hit)
                if cc == "formosa":
                    extra = c["economic"]["gdp"] * multiplier
                    c["economic"]["gdp"] = max(0.5, c["economic"]["gdp"] - extra)
                # AI R&D frozen globally
                c["technology"]["ai_rd_progress"] = c["technology"].get("ai_rd_progress", 0)
                # Mark frozen so tech engine skips AI advancement
                c["_ai_rd_frozen"] = True
            logger.info("[tick R%d] Formosa %s blockade: GDP hits applied, AI R&D frozen globally", round_num, level)

        # 5. Run economic engine
        from engine.engines.economic import process_economy
        try:
            econ_result = process_economy(
                countries, world_state, actions=actions, previous_states=None,
            )
            new_oil = econ_result.oil_price.price if econ_result.oil_price else world_state["oil_price"]
            logger.info("[tick R%d] economic done: oil=%.1f", round_num, new_oil)
        except Exception as e:
            logger.exception("[tick R%d] economic engine failed: %s", round_num, e)
            econ_result = None
            new_oil = world_state["oil_price"]

        # 6. Run stability + political support
        from engine.engines.political import (
            StabilityInput, calc_stability,
            PoliticalSupportInput, calc_political_support,
            WarTirednessInput, update_war_tiredness,
        )
        for cc, c in countries.items():
            eco = c.get("economic", {})
            pol = c.get("political", {})
            try:
                # War tiredness
                at_war = c.get("_at_war", False)
                wt = update_war_tiredness(WarTirednessInput(
                    country_id=cc, war_tiredness=pol.get("war_tiredness", 0),
                    at_war=at_war, is_defender=False, is_attacker=at_war,
                ))
                pol["war_tiredness"] = wt.new_war_tiredness

                # Stability
                sr = calc_stability(StabilityInput(
                    country_id=cc,
                    stability=pol.get("stability", 5),
                    regime_type=c.get("regime_type", "democratic"),
                    gdp_growth_rate=eco.get("gdp_growth_rate", 0.0),
                    economic_state=eco.get("economic_state", "normal"),
                    inflation=eco.get("inflation", 0),
                    starting_inflation=eco.get("starting_inflation", 0),
                    at_war=at_war,
                    war_tiredness=pol.get("war_tiredness", 0),
                    market_stress=0.0,
                    social_spending_ratio=eco.get("social_spending_baseline", 0.20),
                    social_spending_baseline=eco.get("social_spending_baseline", 0.20),
                    gdp=eco.get("gdp", 10),
                ))
                pol["stability"] = sr.new_stability

                # Political support
                ps = calc_political_support(PoliticalSupportInput(
                    country_id=cc,
                    political_support=pol.get("political_support", 50),
                    stability=pol["stability"],
                    at_war=at_war,
                    war_tiredness=pol["war_tiredness"],
                    regime_type=c.get("regime_type", "democratic"),
                    gdp_growth_rate=eco.get("gdp_growth_rate", 0.0),
                    economic_state=eco.get("economic_state", "normal"),
                ))
                pol["political_support"] = ps.new_support
            except Exception as e:
                logger.warning("[tick R%d %s] political engine error: %s", round_num, cc, e)

        # 7. Write back to country_states_per_round
        updates_applied = 0
        for cc, c in countries.items():
            eco = c.get("economic", {})
            pol = c.get("political", {})
            rs = round_by_cc.get(cc)
            if not rs:
                continue
            row_id = rs["id"]
            payload = {
                "gdp": round(eco.get("gdp", rs.get("gdp", 0)), 2),
                "treasury": round(eco.get("treasury", rs.get("treasury", 0)), 2),
                "inflation": round(eco.get("inflation", rs.get("inflation", 0)), 4),
                "stability": int(round(pol.get("stability", rs.get("stability", 5)))),
                "political_support": int(round(pol.get("political_support", rs.get("political_support", 5)))),
                "war_tiredness": int(round(pol.get("war_tiredness", rs.get("war_tiredness", 0)))),
            }
            try:
                client.table("country_states_per_round") \
                    .update(payload).eq("id", row_id).execute()
                updates_applied += 1
            except Exception as e:
                logger.warning("[tick R%d %s] update failed: %s", round_num, cc, e)

        # 8. Update global_state_per_round with new oil price
        try:
            client.table("global_state_per_round").upsert(
                {
                    "scenario_id": scenario_id,
                    "round_num": round_num,
                    "oil_price": round(new_oil, 2),
                    "stock_index": round(100 + round_num * 1.2, 2),
                    "bond_yield": round(4.20 + round_num * 0.05, 2),
                    "gold_price": round(2400 + round_num * 30, 2),
                    "notes": f"Engine tick round {round_num}",
                },
                on_conflict="scenario_id,round_num",
            ).execute()
        except Exception as e:
            logger.warning("[tick R%d] global_state upsert failed: %s", round_num, e)

        return {
            "success": True,
            "round_num": round_num,
            "countries_updated": updates_applied,
            "oil_price": new_oil,
        }

    except Exception as e:
        logger.exception("[tick R%d] engine tick failed", round_num)
        return {"success": False, "error": str(e)}


def _extract_actions_from_decisions(client, scenario_id: str, round_num: int) -> dict:
    """Extract tariff/sanction/blockade/budget actions from agent_decisions.

    Returns dict in the format process_economy expects:
      {tariff_changes: {imposer: {target: level}},
       sanction_changes: {imposer: {target: level}},
       blockade_changes: {chokepoint: {status, ...}},
       budgets: {country: {social_pct, military_coins, tech_coins}},
       tech_rd: {country: {nuclear: float, ai: float}},
       opec_production: {country: level_str}}
    """
    try:
        res = client.table("agent_decisions") \
            .select("country_code, action_type, action_payload") \
            .eq("scenario_id", scenario_id).eq("round_num", round_num).execute()
    except Exception as e:
        logger.warning("Failed to load decisions for engine: %s", e)
        return {}

    tariff_changes: dict = {}
    sanction_changes: dict = {}
    blockade_changes: dict = {}
    tech_rd: dict = {}
    budgets: dict = {}
    opec_prod: dict = {}

    for row in (res.data or []):
        cc = row.get("country_code", "")
        atype = row.get("action_type", "")
        payload = row.get("action_payload") or {}
        if isinstance(payload, str):
            try:
                import json as _json
                payload = _json.loads(payload)
            except Exception:
                payload = {}

        if atype == "set_tariff":
            target = payload.get("target_country", "")
            level = payload.get("level", 0)
            if target:
                tariff_changes.setdefault(cc, {})[target] = level

        elif atype == "set_sanction":
            target = payload.get("target_country", "")
            level = payload.get("level", 0)
            if target:
                sanction_changes.setdefault(cc, {})[target] = level

        elif atype == "declare_blockade":
            zone = payload.get("zone_id") or payload.get("chokepoint", "")
            if zone:
                blockade_changes[zone] = {"status": "active", "imposer": cc, **payload}

        elif atype == "rd_investment":
            domain = payload.get("domain", "ai")
            amount = _safe_float(payload.get("amount"), 1.0)
            rd = tech_rd.setdefault(cc, {"nuclear": 0.0, "ai": 0.0})
            if domain == "nuclear":
                rd["nuclear"] += amount
            else:
                rd["ai"] += amount

        elif atype == "set_budget":
            budgets[cc] = {
                "social_pct": _safe_float(payload.get("social_pct"), 1.0),
                "military_coins": _safe_float(payload.get("military_coins"), 0),
                "tech_coins": _safe_float(payload.get("tech_coins"), 0),
            }

        elif atype == "set_opec":
            opec_prod[cc] = payload.get("production", "maintain")

    return {
        "tariff_changes": tariff_changes,
        "sanction_changes": sanction_changes,
        "blockade_changes": blockade_changes,
        "budgets": budgets,
        "tech_rd": tech_rd,
        "opec_production": opec_prod,
    }


def _extract_war_state(client, scenario_id: str) -> set[str]:
    """Return set of country_codes that are currently at war.

    Reads from relationships table (bilateral_tension >= war threshold)
    OR from agent_decisions with declare_war action type.
    For now: reads from observatory_events with war-related types.
    """
    at_war: set[str] = set()
    try:
        # Check relationships for war state
        res = client.table("relationships") \
            .select("country_a, country_b, status") \
            .eq("status", "war").execute()
        for r in (res.data or []):
            at_war.add(r.get("country_a", ""))
            at_war.add(r.get("country_b", ""))
    except Exception:
        pass
    # Also check for countries involved in combat this sim
    try:
        res = client.table("observatory_combat_results") \
            .select("attacker_country, defender_country") \
            .eq("scenario_id", scenario_id).execute()
        for r in (res.data or []):
            at_war.add(r.get("attacker_country", ""))
            at_war.add(r.get("defender_country", ""))
    except Exception:
        pass
    at_war.discard("")
    return at_war


def _count_combat_losses(client, scenario_id: str, round_num: int) -> dict[str, int]:
    """Count military units lost per country this round from combat results."""
    losses: dict[str, int] = {}
    try:
        res = client.table("observatory_combat_results") \
            .select("defender_country, defender_losses, attacker_country, attacker_losses") \
            .eq("scenario_id", scenario_id).eq("round_num", round_num).execute()
        for r in (res.data or []):
            dl = r.get("defender_losses") or []
            al = r.get("attacker_losses") or []
            if isinstance(dl, list):
                dc = r.get("defender_country", "")
                losses[dc] = losses.get(dc, 0) + len(dl)
            if isinstance(al, list):
                ac = r.get("attacker_country", "")
                losses[ac] = losses.get(ac, 0) + len(al)
    except Exception as e:
        logger.warning("combat losses count failed: %s", e)
    return losses


def _build_world_state(
    round_num: int, base_countries: dict,
    actions: dict, war_countries: set[str],
) -> dict:
    """Build world_state dict for the economic engine with real inputs."""
    # Derive wars list from war_countries set
    wars: list[dict] = []
    war_list = sorted(war_countries)
    # Simple: each pair at war gets a war entry (deduped later by engine)
    # For now just mark which countries are belligerents
    if war_list:
        wars.append({"belligerents_a": war_list, "belligerents_b": []})

    return {
        "oil_price": 85.0,   # starting price; will be mutated by engine
        "opec_production": actions.get("opec_production", {}),
        "chokepoint_status": {},
        "active_blockades": {
            k: v for k, v in actions.get("blockade_changes", {}).items()
            if v.get("status") == "active"
        },
        "formosa_blockade": any(
            "formosa" in str(v) for v in actions.get("blockade_changes", {}).values()
        ),
        "wars": wars,
        "dollar_credibility": 1.0,
        "oil_above_150_rounds": 0,
        "rare_earth_restrictions": {},
        "round_num": round_num,
        "bilateral": {
            "sanctions": _flatten_bilateral(actions.get("sanction_changes", {})),
            "tariffs": _flatten_bilateral(actions.get("tariff_changes", {})),
        },
    }


def _flatten_bilateral(changes: dict) -> dict:
    """Convert {imposer: {target: level}} to the shape economic engine expects."""
    return changes  # engine already expects this shape


def _detect_formosa_blockade(client, scenario_id: str, round_num: int) -> str | None:
    """Check if Formosa Strait is blockaded this round.

    Reads blockade_declared events from observatory_events.
    Returns 'partial' | 'full' | None.
    """
    try:
        res = client.table("observatory_events") \
            .select("payload") \
            .eq("scenario_id", scenario_id) \
            .eq("round_num", round_num) \
            .eq("event_type", "blockade_declared") \
            .execute()
        for row in (res.data or []):
            payload = row.get("payload") or {}
            zone = payload.get("zone_id", "")
            if "formosa" in zone.lower() or "taiwan" in zone.lower():
                action = payload.get("action", "establish")
                if action == "lift":
                    return None
                return payload.get("level", "partial")
    except Exception as e:
        logger.warning("formosa blockade detection failed: %s", e)
    return None


def _load_base_countries(client) -> dict[str, dict]:
    """Load structural country data from ``countries`` table."""
    res = client.table("countries").select("*").execute()
    out = {}
    for row in (res.data or []):
        cid = row.get("sim_name", "").lower().replace(" ", "")
        if not cid:
            continue
        out[cid] = row
    return out


def _safe_float(val, default=0.0) -> float:
    """Parse float, treating 'na', '', None as default."""
    if val is None or val == "" or (isinstance(val, str) and val.strip().lower() in ("na", "n/a", "none")):
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _safe_int(val, default=0) -> int:
    return int(_safe_float(val, default))


def _merge_to_engine_dict(base: dict, rs: dict) -> dict:
    """Merge structural base + per-round snapshot into engine-format dict."""
    gdp = _safe_float(rs.get("gdp") or base.get("gdp"), 10)
    inflation = _safe_float(rs.get("inflation") or base.get("inflation"), 0)
    treasury = _safe_float(rs.get("treasury") or base.get("treasury"), 0)
    stability = _safe_float(rs.get("stability") or base.get("stability"), 5)
    pol_support = _safe_float(rs.get("political_support") or base.get("political_support"), 50)
    war_tired = _safe_float(rs.get("war_tiredness") or base.get("war_tiredness"), 0)

    return {
        "id": base.get("sim_name", "").lower().replace(" ", ""),
        "sim_name": base.get("sim_name", ""),
        "regime_type": base.get("regime_type", "democratic"),
        "economic": {
            "gdp": gdp,
            "gdp_growth_rate": _safe_float(base.get("gdp_growth_base"), 0.02),
            "gdp_growth_base": _safe_float(base.get("gdp_growth_base"), 0.02),
            "sectors": {
                "resources": _safe_float(base.get("sector_resources"), 0.20),
                "industry": _safe_float(base.get("sector_industry"), 0.30),
                "services": _safe_float(base.get("sector_services"), 0.30),
                "technology": _safe_float(base.get("sector_technology"), 0.20),
            },
            "sector_resources": _safe_float(base.get("sector_resources"), 0.20),
            "sector_industry": _safe_float(base.get("sector_industry"), 0.30),
            "sector_services": _safe_float(base.get("sector_services"), 0.30),
            "sector_technology": _safe_float(base.get("sector_technology"), 0.20),
            "tax_rate": _safe_float(base.get("tax_rate"), 0.24),
            "treasury": treasury,
            "inflation": inflation,
            "starting_inflation": inflation,
            "trade_balance": _safe_float(base.get("trade_balance"), 0),
            "oil_producer": str(base.get("oil_producer", "False")).lower() == "true",
            "oil_production_mbpd": _safe_float(base.get("oil_production_mbpd"), 0),
            "opec_member": str(base.get("opec_member", "False")).lower() == "true",
            "opec_production": _safe_float(base.get("opec_production"), 0),
            "formosa_dependency": _safe_float(base.get("formosa_dependency"), 0),
            "debt_burden": _safe_float(base.get("debt_burden"), 0),
            "debt_ratio": _safe_float(base.get("debt_ratio"), 0),
            "social_spending_baseline": _safe_float(base.get("social_baseline"), 0.20),
            "oil_revenue": 0.0,
            "inflation_revenue_erosion": 0.0,
            "sanctions_rounds": 0,
            "sanctions_recovery_rounds": int(base.get("sanctions_recovery_rounds") or 0),
            "sanctions_adaptation_rounds": int(base.get("sanctions_adaptation_rounds") or 0),
            "sanctions_coefficient": _safe_float(base.get("sanctions_coefficient"), 0.05),
            "tariff_coefficient": _safe_float(base.get("tariff_coefficient"), 0.015),
            "formosa_disruption_rounds": 0,
            "economic_state": "normal",
            "momentum": 0.0,
            "crisis_rounds": 0,
            "recovery_rounds": 0,
            "money_printed_this_round": 0.0,
            "starting_oil_price": 80.0,
        },
        "military": {
            "ground": int(_safe_float(base.get("mil_ground"), 0)),
            "naval": int(_safe_float(base.get("mil_naval"), 0)),
            "tactical_air": int(_safe_float(base.get("mil_tactical_air"), 0)),
            "strategic_missile": int(_safe_float(base.get("mil_strategic_missiles"), 0)),
            "air_defense": int(_safe_float(base.get("mil_air_defense"), 0)),
            "production_costs": {
                "ground": _safe_float(base.get("prod_cost_ground"), 3),
                "naval": _safe_float(base.get("prod_cost_naval"), 5),
                "tactical_air": _safe_float(base.get("prod_cost_tactical"), 4),
            },
            "production_capacity": {
                "ground": int(_safe_float(base.get("prod_cap_ground"), 2)),
                "naval": int(_safe_float(base.get("prod_cap_naval"), 1)),
                "tactical_air": int(_safe_float(base.get("prod_cap_tactical"), 1)),
            },
            "maintenance_cost_per_unit": _safe_float(base.get("maintenance_per_unit"), 0.3),
            "strategic_missile_growth": int(_safe_float(base.get("strategic_missile_growth"), 0)),
            "mobilization_pool": int(_safe_float(base.get("mobilization_pool"), 0)),
        },
        "political": {
            "stability": stability,
            "political_support": pol_support,
            "dem_rep_split": {
                "dem": _safe_float(base.get("dem_rep_split_dem"), 50),
                "rep": _safe_float(base.get("dem_rep_split_rep"), 50),
            },
            "war_tiredness": war_tired,
            "regime_type": base.get("regime_type", "democratic"),
            "regime_status": "stable",
            "protest_risk": False,
            "coup_risk": False,
        },
        "technology": {
            "nuclear_level": int(_safe_float(rs.get("nuclear_level") or base.get("nuclear_level"), 0)),
            "nuclear_rd_progress": int(_safe_float(rs.get("nuclear_rd_progress") or base.get("nuclear_rd_progress"), 0)),
            "nuclear_tested": int(_safe_float(base.get("nuclear_level"), 0)) >= 1,
            "ai_level": int(_safe_float(rs.get("ai_level") or base.get("ai_level"), 0)),
            "ai_rd_progress": int(_safe_float(rs.get("ai_rd_progress") or base.get("ai_rd_progress"), 0)),
        },
        "home_zones": [],
        "_at_war": False,  # TODO: derive from relationships
    }


# _build_minimal_world_state removed 2026-04-06 — replaced by _build_world_state
# which reads real agent actions + war state
