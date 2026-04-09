"""Round Tick — bridge between per-round snapshots and the designed engines.

Runs the economic + political + technology engines on `country_states_per_round`
data, merging with structural base data from the `countries` table.

This is the Phase 3 canonical module that gives the Observatory dynamic
country state changes between rounds (GDP, inflation, stability, treasury
etc.) — fixing the "engines-not-running" bug where country stats were
flat across rounds.

Called by ``full_round_runner`` after combat/movement resolution.

ARCHITECTURE (2026-04-08): Engine reads from DB STATE TABLES, never from
agent_decisions. The flow is:
    Participant -> Communication Layer -> DB state tables -> Engine reads state
Sanctions come from ``sanctions`` table, tariffs from ``tariffs`` table,
relationships/war state from ``relationships`` table. The engine is agnostic
to whether a human or AI made the decision.
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

        # 4. Build REAL world_state from DB STATE TABLES (not agent_decisions)
        from engine.config.settings import Settings
        sim_run_id = Settings().default_sim_id
        actions = _load_state_from_tables(client, sim_run_id, scenario_id, round_num)
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
                    social_spending_ratio=eco.get("_actual_social_ratio", eco.get("social_spending_baseline", 0.20)),
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
                # Persist computed coefficients so next round uses ratio (one-time shock, not repeated)
                "sanctions_coefficient": round(eco.get("sanctions_coefficient", 1.0), 6),
                "tariff_coefficient": round(eco.get("tariff_coefficient", 1.0), 6),
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


def _load_state_from_tables(client, sim_run_id: str, scenario_id: str, round_num: int) -> dict:
    """Load engine inputs from DB STATE TABLES (not agent_decisions).

    Architecture: Participant -> Communication Layer -> DB state tables -> Engine reads state.
    The engine is STATELESS — it reads current world state from canonical tables,
    computes effects, writes updated state back. It never reads agent_decisions.

    Returns dict in the format process_economy expects:
      {tariff_changes: {imposer: {target: level}},
       sanction_changes: {imposer: {target: level}},
       blockade_changes: {chokepoint: {status, ...}},
       budgets: {country: {social_pct, production: {...5 branches}, research: {nuclear_coins, ai_coins}}},
       tech_rd: {country: {nuclear: float, ai: float}},
       opec_production: {country: level_str}}
    """
    # --- Sanctions: read from `sanctions` state table ---
    sanction_changes: dict = {}
    try:
        res = client.table("sanctions").select("imposer_country_id, target_country_id, level") \
            .eq("sim_run_id", sim_run_id).execute()
        for row in (res.data or []):
            imposer = row.get("imposer_country_id", "")
            target = row.get("target_country_id", "")
            level = row.get("level", 0)
            if imposer and target and level != 0:
                sanction_changes.setdefault(imposer, {})[target] = level
        logger.info("[state] Loaded %d sanction pairs from sanctions table",
                    sum(len(v) for v in sanction_changes.values()))
    except Exception as e:
        logger.warning("Failed to load sanctions state: %s", e)

    # --- Tariffs: read from `tariffs` state table ---
    tariff_changes: dict = {}
    try:
        res = client.table("tariffs").select("imposer_country_id, target_country_id, level") \
            .eq("sim_run_id", sim_run_id).execute()
        for row in (res.data or []):
            imposer = row.get("imposer_country_id", "")
            target = row.get("target_country_id", "")
            level = row.get("level", 0)
            if imposer and target and level != 0:
                tariff_changes.setdefault(imposer, {})[target] = level
        logger.info("[state] Loaded %d tariff pairs from tariffs table",
                    sum(len(v) for v in tariff_changes.values()))
    except Exception as e:
        logger.warning("Failed to load tariffs state: %s", e)

    # --- Blockades: read from `blockades` state table ---
    blockade_changes: dict = {}
    try:
        res = client.table("blockades").select("*") \
            .eq("sim_run_id", sim_run_id) \
            .eq("status", "active").execute()
        for row in (res.data or []):
            zone = row.get("zone_id", "")
            if zone:
                blockade_changes[zone] = {
                    "status": "active",
                    "imposer": row.get("imposer_country_id", ""),
                    "level": row.get("level", "full"),
                    "zone_id": zone,
                }
        logger.info("[state] Loaded %d active blockades from blockades table",
                    len(blockade_changes))
    except Exception as e:
        logger.warning("Failed to load blockade state: %s", e)

    # --- Budgets: read from country_states_per_round (CONTRACT_BUDGET v1.1) ---
    # Budget decisions are persisted as columns on country_states_per_round by
    # resolve_round: budget_social_pct (numeric), budget_production (jsonb),
    # budget_research (jsonb). If a country has none set, it is omitted from
    # the dict and the economic engine uses its default.
    budgets: dict = {}
    try:
        res = client.table("country_states_per_round") \
            .select("country_code, budget_social_pct, budget_production, budget_research") \
            .eq("scenario_id", scenario_id).eq("round_num", round_num).execute()
        for row in (res.data or []):
            cc = row.get("country_code", "")
            if not cc:
                continue
            social_pct = row.get("budget_social_pct")
            production = row.get("budget_production")
            research = row.get("budget_research")
            if social_pct is None and not production and not research:
                continue
            budgets[cc] = {
                "social_pct": _safe_float(social_pct, 1.0),
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
    except Exception as e:
        # Budget columns may not exist yet — fall back gracefully
        logger.debug("Budget columns not available in country_states: %s", e)

    # --- Tech R&D: read from country_states_per_round tech progress ---
    # R&D investments are applied by resolve_round and reflected in
    # nuclear_rd_progress / ai_rd_progress. Engine reads current state.
    tech_rd: dict = {}

    # --- OPEC production: read from country_states_per_round ---
    opec_prod: dict = {}
    try:
        res = client.table("country_states_per_round") \
            .select("country_code, opec_production") \
            .eq("scenario_id", scenario_id).eq("round_num", round_num).execute()
        for row in (res.data or []):
            cc = row.get("country_code", "")
            prod = row.get("opec_production")
            if cc and prod:
                opec_prod[cc] = prod
    except Exception as e:
        logger.debug("OPEC production column not available: %s", e)

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

    Reads from state tables only:
    - ``relationships`` table (status == 'war')
    - ``observatory_combat_results`` (countries involved in combat)
    """
    at_war: set[str] = set()
    try:
        # Check relationships state table — status='military_conflict' means at war
        res = client.table("relationships") \
            .select("from_country_id, to_country_id, status") \
            .eq("status", "military_conflict").execute()
        for r in (res.data or []):
            at_war.add(r.get("from_country_id", ""))
            at_war.add(r.get("to_country_id", ""))
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

    Reads from `blockades` state table (canonical source).
    Returns 'partial' | 'full' | None.
    """
    try:
        from engine.config.settings import Settings
        sim_run_id = Settings().default_sim_id
        res = client.table("blockades").select("zone_id, level, status") \
            .eq("sim_run_id", sim_run_id) \
            .eq("status", "active").execute()
        for row in (res.data or []):
            zone = row.get("zone_id", "")
            if "formosa" in zone.lower() or "taiwan" in zone.lower():
                return row.get("level", "partial")
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
            "_starting_gdp": _safe_float(base.get("gdp"), 10),  # R0 GDP for stable coefficient calc
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
            # Read COMPUTED coefficients from previous round state (not base structural data)
            # These are the GDP modifiers (0.5-1.0 range), NOT the per-country vulnerability factors
            "sanctions_coefficient": _safe_float(rs.get("sanctions_coefficient"), 1.0),
            "tariff_coefficient": _safe_float(rs.get("tariff_coefficient"), 1.0),
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
