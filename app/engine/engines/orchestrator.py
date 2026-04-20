"""TTT Round Orchestrator — calls all four engines in the correct sequence.

THIN layer: loads state from Supabase, converts to engine dict format,
calls engines in CHAINED sequence (SEED world_model_engine.py), writes back.

Processing sequence:
  Step 0:  Apply submitted actions (tariff/sanction/OPEC/blockade)
  Steps 1-11: Economic engine (oil -> GDP -> revenue -> budget -> production
              -> tech -> inflation -> debt -> crisis -> momentum -> contagion)
  Step 12: Stability per country
  Step 13: Political support per country
  Then: war tiredness, revolution checks, health events, elections, capitulation

Source: 2 SEED/D_ENGINES/world_model_engine.py (deterministic_pass)
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from engine.engines.economic import EconomicResult, process_economy, get_market_stress_for_country
from engine.engines.political import (
    StabilityInput, StabilityResult, PoliticalSupportInput, PoliticalSupportResult,
    ElectionInput, ElectionResult, RevolutionResult, HealthEventResult,
    WarTirednessInput, WarTirednessResult, ThresholdFlagsResult,
    calc_stability, calc_political_support, process_election,
    check_revolution, check_health_events, update_war_tiredness,
    update_threshold_flags, check_capitulation,
)
from engine.models.db import (
    Country, Relationship, Sanction, Tariff, WorldState as WorldStateDB,
)
from engine.services.supabase import (
    get_sim_run, get_countries, get_relationships,
    get_sanctions, get_tariffs, get_world_state, get_client,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# RESULT MODEL
# ---------------------------------------------------------------------------

class RoundResult(BaseModel):
    """Complete output of one round of processing."""
    sim_id: str
    round_num: int
    economic: EconomicResult
    stability: dict[str, StabilityResult] = Field(default_factory=dict)
    support: dict[str, PoliticalSupportResult] = Field(default_factory=dict)
    war_tiredness: dict[str, WarTirednessResult] = Field(default_factory=dict)
    threshold_flags: dict[str, ThresholdFlagsResult] = Field(default_factory=dict)
    elections: dict[str, ElectionResult] = Field(default_factory=dict)
    revolutions: dict[str, RevolutionResult] = Field(default_factory=dict)
    health_events: dict[str, HealthEventResult] = Field(default_factory=dict)
    capitulation_flags: list[str] = Field(default_factory=list)
    phase_a_results: list[dict] = Field(default_factory=list)
    log: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# DB MODEL -> ENGINE DICT CONVERSION
# ---------------------------------------------------------------------------

def _country_to_dict(c: Country) -> dict[str, Any]:
    """Convert Country DB model to nested-dict format engines expect."""
    return {
        "id": c.id, "sim_name": c.sim_name, "parallel": c.parallel,
        "regime_type": c.regime_type, "team_type": c.team_type,
        "economic": {
            "gdp": c.gdp, "gdp_growth_rate": c.gdp_growth_base,
            "gdp_growth_base": c.gdp_growth_base,  # immutable structural rate
            "sectors": {
                "resources": c.sector_resources, "industry": c.sector_industry,
                "services": c.sector_services, "technology": c.sector_technology,
            },
            "sector_resources": c.sector_resources, "sector_industry": c.sector_industry,
            "sector_services": c.sector_services, "sector_technology": c.sector_technology,
            "tax_rate": c.tax_rate, "treasury": c.treasury,
            "inflation": c.inflation, "starting_inflation": c.inflation,
            "trade_balance": c.trade_balance, "oil_producer": c.oil_producer,
            "oil_production_mbpd": c.oil_production_mbpd,
            "opec_member": c.opec_member, "opec_production": c.opec_production,
            "formosa_dependency": c.formosa_dependency, "debt_burden": c.debt_burden,
            "social_spending_baseline": c.social_baseline,
            "oil_revenue": 0.0, "inflation_revenue_erosion": 0.0,
            # sanctions_rounds / adaptation / recovery removed 2026-04-10 per CONTRACT_SANCTIONS v1.0
            "sanctions_coefficient": c.sanctions_coefficient,
            "tariff_coefficient": c.tariff_coefficient,
            "formosa_disruption_rounds": 0,
            "economic_state": "normal", "momentum": 0.0, "crisis_rounds": 0,
            "recovery_rounds": 0, "money_printed_this_round": 0.0,
            # Cal-9: Baseline snapshots — factors only count as CHANGES from starting state
            "starting_oil_price": 80.0,  # baseline oil price at game start
        },
        "military": {
            "ground": c.mil_ground, "naval": c.mil_naval,
            "tactical_air": c.mil_tactical_air, "strategic_missile": c.mil_strategic_missiles,
            "air_defense": c.mil_air_defense,
            "production_costs": {
                "ground": c.prod_cost_ground, "naval": c.prod_cost_naval,
                "tactical_air": c.prod_cost_tactical,
            },
            "production_capacity": {
                "ground": c.prod_cap_ground, "naval": c.prod_cap_naval,
                "tactical_air": c.prod_cap_tactical,
            },
            "maintenance_cost_per_unit": c.maintenance_per_unit,
            "strategic_missile_growth": c.strategic_missile_growth,
            "mobilization_pool": c.mobilization_pool,
        },
        "political": {
            "stability": c.stability, "political_support": c.political_support,
            "dem_rep_split": {
                "dem": c.dem_rep_split_dem, "rep": c.dem_rep_split_rep,
            },
            "war_tiredness": c.war_tiredness,
            "regime_type": c.regime_type,
            "regime_status": "stable", "protest_risk": False, "coup_risk": False,
        },
        "technology": {
            "nuclear_level": c.nuclear_level, "nuclear_rd_progress": c.nuclear_rd_progress,
            "nuclear_tested": c.nuclear_level >= 1,
            "ai_level": c.ai_level, "ai_rd_progress": c.ai_rd_progress,
        },
        "home_zones": [z.strip() for z in c.home_zones.split(",") if z.strip()],
    }


def _build_world_dict(
    ws: WorldStateDB, sanctions: list[Sanction],
    tariffs: list[Tariff], relationships: list[Relationship], round_num: int,
) -> dict[str, Any]:
    """Convert DB world state + relations into engine dict format."""
    sanc: dict[str, dict[str, int]] = {}
    for s in sanctions:
        sanc.setdefault(s.imposer_country_code, {})[s.target_country_code] = s.level
    tar: dict[str, dict[str, int]] = {}
    for t in tariffs:
        tar.setdefault(t.imposer_country_code, {})[t.target_country_code] = t.level
    rel: dict[str, dict[str, str]] = {}
    for r in relationships:
        rel.setdefault(r.from_country_code, {})[r.to_country_code] = r.relationship
    return {
        "oil_price": ws.oil_price, "oil_price_index": ws.oil_price_index,
        "global_trade_volume_index": ws.global_trade_volume_index,
        "dollar_credibility": ws.dollar_credibility,
        "nuclear_used_this_sim": ws.nuclear_used_this_sim,
        "formosa_blockade": ws.formosa_blockade,
        "opec_production": ws.opec_production, "chokepoint_status": ws.chokepoint_status,
        "wars": ws.wars, "active_blockades": ws.active_blockades,
        "oil_above_150_rounds": ws.opec_production.get("_oil_above_threshold_rounds", 0) if isinstance(ws.opec_production, dict) else 0,
        "market_indexes": ws.market_indexes if isinstance(ws.market_indexes, dict) and ws.market_indexes else None,
        "rare_earth_restrictions": {},
        "round_num": round_num,
        "bilateral": {"sanctions": sanc, "tariffs": tar},
        "relationships": rel,
    }


def _is_at_war(cid: str, wars: list[dict]) -> bool:
    """Check if country is a belligerent in any active war."""
    return any(cid in w.get("belligerents_a", []) or cid in w.get("belligerents_b", []) for w in wars)


def _snapshot_prev(countries: dict[str, dict], wars: list[dict]) -> dict[str, dict]:
    """Capture pre-round state for transition detection."""
    return {
        cid: {
            "economic_state": c["economic"].get("economic_state", "normal"),
            "gdp": c["economic"]["gdp"],
            "stability": c["political"]["stability"],
            "at_war": _is_at_war(cid, wars),
        }
        for cid, c in countries.items()
    }


def _sync_econ_results(countries: dict[str, dict], er: EconomicResult) -> None:
    """Sync economic engine result model fields back into country dicts."""
    for cid, cr in er.countries.items():
        if cid not in countries:
            continue
        eco = countries[cid]["economic"]
        eco["gdp"] = cr.gdp.new_gdp
        eco["gdp_growth_rate"] = cr.gdp.growth_pct
        eco["inflation"] = cr.inflation
        eco["debt_burden"] = cr.debt_burden
        eco["economic_state"] = cr.economic_state.new_state
        eco["momentum"] = cr.momentum.new_momentum


def _country_update_payload(c: dict[str, Any]) -> dict[str, Any]:
    """Build Supabase update payload from mutated engine dict."""
    eco, pol, tech, mil = c["economic"], c["political"], c["technology"], c["military"]
    return {
        "gdp": round(eco["gdp"], 2),
        "gdp_growth_base": round(eco.get("gdp_growth_base", eco.get("gdp_growth_rate", 0)), 4),
        "treasury": round(eco.get("treasury", 0), 2),
        "inflation": round(eco["inflation"], 2),
        "debt_burden": round(eco["debt_burden"], 4),
        # sanctions_recovery_rounds / sanctions_adaptation_rounds removed 2026-04-10 per CONTRACT_SANCTIONS v1.0
        "sanctions_coefficient": round(eco.get("sanctions_coefficient", 1.0), 4),
        "tariff_coefficient": round(eco.get("tariff_coefficient", 1.0), 4),
        "stability": round(pol["stability"], 2),
        "political_support": round(pol["political_support"], 2),
        "war_tiredness": round(pol.get("war_tiredness", 0), 2),
        "nuclear_level": tech.get("nuclear_level", 0),
        "nuclear_rd_progress": round(tech.get("nuclear_rd_progress", 0), 4),
        "ai_level": tech.get("ai_level", 0),
        "ai_rd_progress": round(tech.get("ai_rd_progress", 0), 4),
        "mil_ground": mil.get("ground", 0), "mil_naval": mil.get("naval", 0),
        "mil_tactical_air": mil.get("tactical_air", 0),
        "mil_strategic_missiles": mil.get("strategic_missiles", 0),
        "mil_air_defense": mil.get("air_defense", 0),
    }


# ---------------------------------------------------------------------------
# ACTION APPLICATION (Step 0)
# ---------------------------------------------------------------------------

def _apply_actions(ws: dict, actions: dict) -> None:
    """Mutate world_state dicts with submitted action changes."""
    bilateral = ws.setdefault("bilateral", {})
    s_dict, t_dict = bilateral.setdefault("sanctions", {}), bilateral.setdefault("tariffs", {})
    for imp, tgts in actions.get("tariff_changes", {}).items():
        for tgt, lvl in tgts.items():
            t_dict.setdefault(imp, {})[tgt] = lvl
    sanctions_affected = set()
    for imp, tgts in actions.get("sanction_changes", {}).items():
        for tgt, lvl in tgts.items():
            s_dict.setdefault(imp, {})[tgt] = lvl
            sanctions_affected.add(tgt)
    ws["_sanctions_affected"] = sanctions_affected
    opec = ws.setdefault("opec_production", {})
    for country, level in actions.get("opec_production", {}).items():
        opec[country] = level
    blockades = ws.setdefault("active_blockades", {})
    for cp, info in actions.get("blockade_changes", {}).items():
        if info.get("status") == "removed":
            blockades.pop(cp, None)
        else:
            blockades[cp] = info


# ---------------------------------------------------------------------------
# DB PERSISTENCE
# ---------------------------------------------------------------------------

async def _persist(
    sim_id: str, round_num: int, countries: dict[str, dict],
    econ_result: EconomicResult, ws_db: WorldStateDB,
) -> None:
    """Write all updated state back to Supabase."""
    client = get_client()
    for cid, c_dict in countries.items():
        client.table("countries").update(
            _country_update_payload(c_dict)
        ).eq("sim_run_id", sim_id).eq("id", cid).execute()
    # Market indexes — store for next round's inertia calculation
    mkt_idx_data = None
    if econ_result.market_indexes is not None:
        mi = econ_result.market_indexes
        mkt_idx_data = {
            "wall_street": mi.wall_street.new_value,
            "europa": mi.europa.new_value,
            "dragon": mi.dragon.new_value,
        }

    client.table("world_state").upsert({
        "sim_run_id": sim_id, "round_num": round_num,
        "oil_price": round(econ_result.oil_price.price, 2),
        "oil_price_index": round(econ_result.oil_price.price / 80.0 * 100.0, 1),
        "dollar_credibility": round(econ_result.dollar_credibility, 2),
        "nuclear_used_this_sim": ws_db.nuclear_used_this_sim,
        "formosa_blockade": ws_db.formosa_blockade,
        "opec_production": {
            **(ws_db.opec_production if isinstance(ws_db.opec_production, dict) else {}),
            "_oil_above_threshold_rounds": econ_result.oil_above_150_rounds,
        },
        "chokepoint_status": ws_db.chokepoint_status,
        "wars": ws_db.wars, "active_blockades": ws_db.active_blockades,
        "market_indexes": mkt_idx_data,
    }, on_conflict="sim_run_id,round_num").execute()


# ---------------------------------------------------------------------------
# L0: SIM INITIALIZATION (run once before R1)
# ---------------------------------------------------------------------------

async def initialize_sim(sim_id: str) -> dict:
    """Initialize all derived values from seed data. Run ONCE before Round 1.

    Computes and persists:
    - sanctions_coefficient per country (from starting sanctions)
    - tariff_coefficient per country (from starting tariffs)
    - tariff inflation baseline

    After this runs, all coefficients in DB reflect the starting state.
    process_round() then has no special R1 handling — all rounds identical.
    """
    from engine.engines.economic import calc_sanctions_coefficient, calc_tariff_coefficient

    db_countries = await get_countries(sim_id)
    db_ws = await get_world_state(sim_id)
    db_sanctions = await get_sanctions(sim_id)
    db_tariffs = await get_tariffs(sim_id)
    db_rels = await get_relationships(sim_id)

    if not db_countries or db_ws is None:
        raise ValueError(f"No data for sim {sim_id}")

    countries = {c.id: _country_to_dict(c) for c in db_countries}
    world_state = _build_world_dict(db_ws, db_sanctions, db_tariffs, db_rels, 0)

    client = get_client()
    results = {}

    for cid, c in countries.items():
        eco = c["economic"]

        # Sanctions coefficient
        sanc_coeff = calc_sanctions_coefficient(
            cid, countries, world_state["bilateral"]["sanctions"],
        )

        # Tariff coefficient + inflation baseline
        tar_coeff, tar_inflation, tar_revenue = calc_tariff_coefficient(
            cid, countries, world_state["bilateral"]["tariffs"],
        )

        # Persist to DB
        client.table("countries").update({
            "sanctions_coefficient": round(sanc_coeff, 4),
            "tariff_coefficient": round(tar_coeff, 4),
        }).eq("id", cid).eq("sim_run_id", sim_id).execute()

        # Update in-memory dict too (for return)
        eco["sanctions_coefficient"] = sanc_coeff
        eco["tariff_coefficient"] = tar_coeff
        eco["_tariff_inflation_level"] = tar_inflation

        results[cid] = {
            "sanctions_coefficient": round(sanc_coeff, 4),
            "tariff_coefficient": round(tar_coeff, 4),
            "tariff_inflation": round(tar_inflation, 2),
        }

    return results


# ---------------------------------------------------------------------------
# PHASE A — FREE ACTION DISPATCH
# ---------------------------------------------------------------------------

# Action types that are regular/batch decisions (Phase B), NOT Phase A free actions.
_BATCH_ACTION_TYPES = {
    "set_budget", "set_sanction", "set_tariff", "set_opec",
    "move_units",  # inter-round movement, not Phase A
}


def _dispatch_phase_a_actions(
    sim_run_id: str, round_num: int, log: list[str],
) -> list[dict]:
    """Load and dispatch all Phase A free actions from agent_decisions.

    Reads unprocessed actions for this round, dispatches each through
    action_dispatcher, marks them as processed, returns results.
    """
    from engine.services.action_dispatcher import dispatch_action

    client = get_client()
    results = []

    try:
        # Load all decisions for this round that haven't been processed yet
        rows = client.table("agent_decisions") \
            .select("id,action_type,action_payload,country_code") \
            .eq("sim_run_id", sim_run_id) \
            .eq("round_num", round_num) \
            .is_("processed_at", "null") \
            .execute().data or []
    except Exception as e:
        logger.warning("Failed to load Phase A actions: %s", e)
        return results

    # Filter to free actions only (exclude batch/movement decisions)
    free_actions = [r for r in rows if r.get("action_type") not in _BATCH_ACTION_TYPES]

    if free_actions:
        log.append(f"  Phase A: dispatching {len(free_actions)} free actions")

    for row in free_actions:
        action_type = row.get("action_type", "")
        payload = row.get("action_payload", {})
        if isinstance(payload, str):
            import json
            try:
                payload = json.loads(payload)
            except Exception:
                payload = {}

        # Ensure action_type and country_code are in payload
        payload.setdefault("action_type", action_type)
        payload.setdefault("country_code", row.get("country_code", ""))

        try:
            result = dispatch_action(sim_run_id, round_num, payload)
            results.append({"action_id": row["id"], "action_type": action_type, **result})

            success = result.get("success", False)
            log.append(f"    {action_type} → {'OK' if success else 'FAILED'}")

            # Mark as processed
            client.table("agent_decisions").update({
                "processed_at": "now()",
            }).eq("id", row["id"]).execute()

        except Exception as e:
            logger.warning("Phase A dispatch failed for %s: %s", action_type, e)
            results.append({"action_id": row["id"], "action_type": action_type,
                            "success": False, "narrative": f"Dispatch error: {e}"})

    return results


# ---------------------------------------------------------------------------
# MAIN ORCHESTRATOR
# ---------------------------------------------------------------------------

async def process_round(
    sim_id: str, round_num: int, actions: dict[str, Any],
) -> RoundResult:
    """Process one complete simulation round.

    1. Load state from Supabase  2. Convert to engine dicts
    3. Call engines in CHAINED order  4. Write back  5. Return RoundResult
    """
    log: list[str] = [f"=== ROUND {round_num} START (sim={sim_id}) ==="]

    # 1. LOAD STATE
    sim_run = await get_sim_run(sim_id)
    if sim_run is None:
        raise ValueError(f"SIM run not found: {sim_id}")
    if sim_run.status not in ("active", "setup", "processing"):
        raise ValueError(f"SIM run not active: {sim_run.status}")

    db_countries = await get_countries(sim_id)
    db_ws = await get_world_state(sim_id)
    db_sanctions = await get_sanctions(sim_id)
    db_tariffs = await get_tariffs(sim_id)
    db_rels = await get_relationships(sim_id)
    if db_ws is None:
        raise ValueError(f"No world state for sim={sim_id}")
    if not db_countries:
        raise ValueError(f"No countries for sim={sim_id}")

    # 2. CONVERT TO ENGINE FORMAT
    countries = {c.id: _country_to_dict(c) for c in db_countries}
    world_state = _build_world_dict(db_ws, db_sanctions, db_tariffs, db_rels, round_num)
    previous_states = _snapshot_prev(countries, world_state["wars"])

    # ── PHASE A: DISPATCH FREE ACTIONS ────────────────────────────────
    # Process any Phase A actions submitted to agent_decisions during the round.
    # These are immediate-resolution actions (combat, covert ops, domestic politics,
    # transactions). See CONTRACT_ROUND_FLOW.md.
    phase_a_results = _dispatch_phase_a_actions(sim_id, round_num, log)

    # STEP 0: APPLY REGULAR DECISIONS (tariffs, sanctions, OPEC, blockades)
    _apply_actions(world_state, actions)

    # ── PHASE B: BATCH PROCESSING ─────────────────────────────────────
    # STEPS 1-11: ECONOMIC ENGINE
    econ_result = process_economy(countries, world_state, actions, previous_states)
    _sync_econ_results(countries, econ_result)
    log.append(f"  Economic engine done. Oil={econ_result.oil_price.price:.1f}")

    # STEP 12: STABILITY + WAR TIREDNESS
    stability_results: dict[str, StabilityResult] = {}
    wt_results: dict[str, WarTirednessResult] = {}
    tf_results: dict[str, ThresholdFlagsResult] = {}
    wars = world_state["wars"]

    # Count territory changes from hex_control for stability
    territory_changes: dict[str, dict[str, int]] = {}
    try:
        hc_rows = client.table("hex_control").select("owner, controlled_by") \
            .eq("sim_run_id", sim_run_id).execute().data or []
        for hc in hc_rows:
            owner = hc.get("owner", "")
            occupier = hc.get("controlled_by")
            if not occupier or occupier == owner:
                continue
            territory_changes.setdefault(owner, {"gained": 0, "lost": 0})["lost"] += 1
            territory_changes.setdefault(occupier, {"gained": 0, "lost": 0})["gained"] += 1
    except Exception:
        pass

    for cid, c in countries.items():
        eco, pol = c["economic"], c["political"]
        at_war = _is_at_war(cid, wars)

        wt = update_war_tiredness(WarTirednessInput(
            country_id=cid, war_tiredness=pol["war_tiredness"], at_war=at_war,
            is_defender=any(cid in w.get("belligerents_b", []) for w in wars),
            is_attacker=any(cid in w.get("belligerents_a", []) for w in wars),
        ))
        pol["war_tiredness"] = wt.new_war_tiredness
        wt_results[cid] = wt

        # Market stress from regional indexes
        mkt_stress = 0.0
        if econ_result.market_indexes is not None:
            mkt_stress = get_market_stress_for_country(cid, econ_result.market_indexes)

        tc = territory_changes.get(cid, {"gained": 0, "lost": 0})
        sr = calc_stability(StabilityInput(
            country_id=cid, stability=pol["stability"], regime_type=c["regime_type"],
            gdp_growth_rate=eco.get("gdp_growth_rate", 0.0),
            economic_state=eco.get("economic_state", "normal"),
            inflation=eco["inflation"], starting_inflation=eco.get("starting_inflation", 0.0),
            at_war=at_war, war_tiredness=pol["war_tiredness"],
            market_stress=mkt_stress,
            social_spending_ratio=eco.get("_actual_social_ratio", eco.get("social_spending_baseline", 0.20)),
            social_spending_baseline=eco.get("social_spending_baseline", 0.20), gdp=eco["gdp"],
            territory_lost=tc["lost"],
            territory_gained=tc["gained"],
        ))
        pol["stability"] = sr.new_stability
        stability_results[cid] = sr
        tf_results[cid] = update_threshold_flags(pol["stability"])

    # STEP 13: POLITICAL SUPPORT
    support_results: dict[str, PoliticalSupportResult] = {}
    for cid, c in countries.items():
        eco, pol = c["economic"], c["political"]
        sp = calc_political_support(PoliticalSupportInput(
            country_id=cid, political_support=pol["political_support"],
            stability=pol["stability"], regime_type=c["regime_type"],
            gdp_growth_rate=eco.get("gdp_growth_rate", 0.0),
            economic_state=eco.get("economic_state", "normal"),
            oil_price=econ_result.oil_price.price,
            oil_producer=eco.get("oil_producer", False),
            round_num=round_num, war_tiredness=pol["war_tiredness"],
        ))
        pol["political_support"] = sp.new_support
        support_results[cid] = sp

    # REVOLUTION CHECKS
    rev_results: dict[str, RevolutionResult] = {}
    for cid, c in countries.items():
        pol = c["political"]
        rev = check_revolution(cid, pol["stability"], pol["political_support"])
        if rev is not None:
            rev_results[cid] = rev
            log.append(f"  REVOLUTION: {cid} — {rev.severity}")

    # HEALTH EVENTS
    health_results: dict[str, HealthEventResult] = {}
    for cid in countries:
        h = check_health_events(cid, round_num)
        if h is not None:
            health_results[cid] = h
            log.append(f"  HEALTH: {cid} — {h.event}")

    # ELECTIONS — read from sim_run.key_events (DB), not hardcoded
    election_results: dict[str, ElectionResult] = {}
    key_events = sim_run.key_events if isinstance(sim_run.key_events, list) else []
    scheduled_elections = [
        e for e in key_events
        if e.get("type") == "election" and e.get("round") == round_num
    ]
    for event in scheduled_elections:
        ecid = event.get("country_code", "")
        if ecid not in countries:
            log.append(f"  ELECTION skipped: {event.get('name', '?')} — country {ecid} not found")
            continue
        eco, pol = countries[ecid]["economic"], countries[ecid]["political"]
        election_subtype = event.get("subtype", "parliamentary_midterm")
        el = process_election(ElectionInput(
            country_id=ecid, election_type=election_subtype, round_num=round_num,
            gdp_growth_rate=eco.get("gdp_growth_rate", 0.0), stability=pol["stability"],
            economic_state=eco.get("economic_state", "normal"),
            oil_price=econ_result.oil_price.price,
            oil_producer=eco.get("oil_producer", False),
            war_tiredness=pol["war_tiredness"], wars=wars,
            incumbent_pct=actions.get("votes", {}).get(ecid, {}).get("incumbent_pct", 50.0),
        ))
        election_results[ecid] = el
        log.append(f"  ELECTION: {event.get('name', ecid)} — {'incumbent wins' if el.incumbent_wins else 'incumbent loses'}")

    # Log mandatory meetings scheduled for this round (informational)
    scheduled_meetings = [
        e for e in key_events
        if e.get("type") == "mandatory_meeting" and e.get("round") == round_num
    ]
    for meeting in scheduled_meetings:
        log.append(f"  MEETING: {meeting.get('name', '?')} (round {round_num})")

    # CAPITULATION CHECK
    cap_flags: list[str] = []
    for cid, c in countries.items():
        cr = econ_result.countries.get(cid)
        crisis_rounds = cr.economic_state.crisis_rounds if cr else 0
        if check_capitulation(c["economic"].get("economic_state", "normal"), crisis_rounds):
            cap_flags.append(cid)
            log.append(f"  CAPITULATION: {cid}")

    # PERSIST TO DB
    await _persist(sim_id, round_num, countries, econ_result, db_ws)
    # Note: sim_run phase transitions are managed by sim_run_manager, not here.
    log.append(f"=== ROUND {round_num} COMPLETE ===")

    return RoundResult(
        sim_id=sim_id, round_num=round_num, economic=econ_result,
        stability=stability_results, support=support_results,
        war_tiredness=wt_results, threshold_flags=tf_results,
        elections=election_results, revolutions=rev_results,
        health_events=health_results, capitulation_flags=cap_flags,
        phase_a_results=phase_a_results, log=log,
    )


# ---------------------------------------------------------------------------
# FASTAPI ROUTE — mount in main.py:
#   from engine.engines.orchestrator import router as orchestrator_router
#   app.include_router(orchestrator_router, prefix="/api/v1")
# ---------------------------------------------------------------------------

router = APIRouter(tags=["orchestrator"])


class ProcessRoundRequest(BaseModel):
    """Request body for the process-round endpoint."""
    sim_id: str
    round_num: int
    actions: dict[str, Any] = Field(default_factory=dict)


@router.post("/sim/{sim_id}/round/{round_num}", response_model=RoundResult)
async def api_process_round(sim_id: str, round_num: int, body: ProcessRoundRequest) -> RoundResult:
    """Process one complete simulation round."""
    try:
        return await process_round(sim_id=sim_id, round_num=round_num, actions=body.actions)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Round processing failed: %s", e)
        raise HTTPException(status_code=500, detail="Round processing failed")
