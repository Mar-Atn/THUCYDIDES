"""Round Runner — orchestrates complete AI-driven simulation rounds.

Implements the full round flow:
1. Start round: update all agents with world state
2. Active loop: agents decide, converse, propose transactions
3. Mandatory submission: budget, tariffs, sanctions, OPEC
4. Engine processing: economic + political (Pass 1)
5. NOUS judgment (Pass 2)
6. Reflection: agents update cognitive blocks
7. Return RoundReport

Designed for unmanned mode — no database, pure in-memory.
Loads starting data from countries.csv (same as tests/layer3/run_scenarios.py).

Source: SEED_E5_AI_PARTICIPANT_MODULE_v1.md, DET_C1
"""

from __future__ import annotations

import asyncio
import csv
import copy
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Optional

from engine.agents.leader import LeaderAgent
from engine.agents.profiles import load_heads_of_state

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# DATA MODELS
# ---------------------------------------------------------------------------

@dataclass
class RoundReport:
    """Complete output of one simulation round."""
    round_num: int = 0
    actions_taken: dict[str, list[dict]] = field(default_factory=dict)  # role_id → actions
    conversations: list[dict] = field(default_factory=list)
    transactions: list[dict] = field(default_factory=list)
    mandatory_inputs: dict[str, dict] = field(default_factory=dict)  # role_id → inputs
    engine_results: dict = field(default_factory=dict)
    nous_adjustments: dict | None = None
    agent_reflections: dict[str, dict] = field(default_factory=dict)
    log: list[str] = field(default_factory=list)
    duration_seconds: float = 0.0

    def summary(self) -> str:
        """Brief text summary of the round."""
        n_actions = sum(len(v) for v in self.actions_taken.values())
        return (
            f"Round {self.round_num}: {n_actions} actions, "
            f"{len(self.conversations)} conversations, "
            f"{len(self.transactions)} transactions, "
            f"{len(self.mandatory_inputs)} mandatory submissions, "
            f"{self.duration_seconds:.1f}s"
        )


@dataclass
class SimReport:
    """Complete output of a full simulation run."""
    rounds: list[RoundReport] = field(default_factory=list)
    num_rounds: int = 0
    agents: dict[str, dict] = field(default_factory=dict)  # role_id → final info
    total_duration_seconds: float = 0.0

    def summary(self) -> str:
        """Brief text summary of the full sim."""
        return (
            f"SIM complete: {self.num_rounds} rounds, "
            f"{len(self.agents)} agents, "
            f"{self.total_duration_seconds:.1f}s total"
        )


# ---------------------------------------------------------------------------
# DATA LOADING — from CSV (no database, mirrors tests/layer3/run_scenarios.py)
# ---------------------------------------------------------------------------

CSV_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..",
    "2 SEED", "C_MECHANICS", "C4_DATA", "countries.csv",
)


def load_countries_from_csv() -> dict[str, dict]:
    """Load all countries from CSV into flat dict format for runner.

    Returns country data in the same format as profiles.load_country_context()
    but for ALL countries at once.
    """
    countries = {}
    with open(CSV_PATH) as f:
        for row in csv.DictReader(f):
            cid = row["id"]
            countries[cid] = {
                "id": cid,
                "sim_name": row["sim_name"],
                "parallel": row["parallel"],
                "regime_type": row["regime_type"],
                "gdp": float(row["gdp"]),
                "gdp_growth_base": float(row["gdp_growth_base"]),
                "treasury": float(row["treasury"]),
                "inflation": float(row["inflation"]),
                "debt_burden": float(row.get("debt_burden", 0)),
                "tax_rate": float(row.get("tax_rate", 0.24)),
                "social_baseline": float(row.get("social_baseline", 0.30)),
                "stability": float(row["stability"]),
                "political_support": float(row["political_support"]),
                "war_tiredness": float(row.get("war_tiredness", 0)),
                "oil_producer": row["oil_producer"].lower() == "true",
                "opec_member": row["opec_member"].lower() == "true",
                "oil_production_mbpd": float(row.get("oil_production_mbpd", 0)) if row.get("oil_production_mbpd", "0") not in ("", "na") else 0,
                "nuclear_level": int(row["nuclear_level"]),
                "nuclear_rd_progress": float(row["nuclear_rd_progress"]),
                "ai_level": int(row["ai_level"]),
                "ai_rd_progress": float(row["ai_rd_progress"]),
                "mil_ground": int(float(row["mil_ground"])),
                "mil_naval": int(float(row["mil_naval"])),
                "mil_tactical_air": int(float(row["mil_tactical_air"])),
                "mil_strategic_missiles": int(float(row.get("mil_strategic_missiles", 0))),
                "mil_air_defense": int(float(row.get("mil_air_defense", 0))),
                "mobilization_pool": int(float(row.get("mobilization_pool", 0))),
                "maintenance_per_unit": float(row.get("maintenance_per_unit", 0.05)),
                "at_war_with": row.get("at_war_with", ""),
                "sector_resources": float(row.get("sector_resources", 0.25)),
                "sector_industry": float(row.get("sector_industry", 0.25)),
                "sector_services": float(row.get("sector_services", 0.25)),
                "sector_technology": float(row.get("sector_technology", 0.25)),
                "trade_balance": float(row.get("trade_balance", 0)),
                "formosa_dependency": float(row.get("formosa_dependency", 0)),
                "team_type": row.get("team_type", ""),
            }
    return countries


def _build_engine_countries(countries_flat: dict[str, dict]) -> dict[str, dict]:
    """Convert flat country dicts to engine-format nested dicts (for process_economy).

    Mirrors the format in tests/layer3/run_scenarios.py.
    """
    engine_countries = {}
    for cid, c in countries_flat.items():
        engine_countries[cid] = {
            "id": cid,
            "sim_name": c["sim_name"],
            "parallel": c["parallel"],
            "regime_type": c["regime_type"],
            "team_type": c.get("team_type", ""),
            "economic": {
                "gdp": c["gdp"],
                "gdp_growth_rate": c["gdp_growth_base"],
                "gdp_growth_base": c["gdp_growth_base"],
                "sectors": {
                    "resources": c.get("sector_resources", 0.25),
                    "industry": c.get("sector_industry", 0.25),
                    "services": c.get("sector_services", 0.25),
                    "technology": c.get("sector_technology", 0.25),
                },
                "sector_resources": c.get("sector_resources", 0.25),
                "sector_industry": c.get("sector_industry", 0.25),
                "sector_services": c.get("sector_services", 0.25),
                "sector_technology": c.get("sector_technology", 0.25),
                "tax_rate": c["tax_rate"],
                "treasury": c["treasury"],
                "inflation": c["inflation"],
                "starting_inflation": c["inflation"],
                "trade_balance": c.get("trade_balance", 0),
                "oil_producer": c["oil_producer"],
                "oil_production_mbpd": c["oil_production_mbpd"],
                "opec_member": c["opec_member"],
                "opec_production": "normal",
                "formosa_dependency": c.get("formosa_dependency", 0),
                "debt_burden": c["debt_burden"],
                "social_spending_baseline": c["social_baseline"],
                "oil_revenue": 0.0,
                "inflation_revenue_erosion": 0.0,
                # sanctions_rounds / adaptation / recovery removed 2026-04-10 per CONTRACT_SANCTIONS v1.0
                "sanctions_coefficient": 1.0,
                "tariff_coefficient": 1.0,
                "formosa_disruption_rounds": 0,
                "economic_state": "normal",
                "momentum": 0.0,
                "crisis_rounds": 0,
                "recovery_rounds": 0,
                "money_printed_this_round": 0.0,
                "starting_oil_price": 80.0,
            },
            "military": {
                "ground": c["mil_ground"],
                "naval": c["mil_naval"],
                "tactical_air": c["mil_tactical_air"],
                "strategic_missile": c["mil_strategic_missiles"],
                "air_defense": c["mil_air_defense"],
                "production_costs": {"ground": 2.0, "naval": 3.0, "tactical_air": 3.0},
                "production_capacity": {"ground": 2, "naval": 1, "tactical_air": 1},
                "maintenance_cost_per_unit": c["maintenance_per_unit"],
                "strategic_missile_growth": 0,
                "mobilization_pool": c["mobilization_pool"],
            },
            "political": {
                "stability": c["stability"],
                # DEPRECATED 2026-04-15: political_support replaced by stability only
                "political_support": 0,
                # DEPRECATED 2026-04-15: dem_rep_split removed — parliament simplified to 3 seats
                # "dem_rep_split": {"dem": 50, "rep": 50},
                "war_tiredness": c["war_tiredness"],
                "regime_type": c["regime_type"],
                "regime_status": "stable",
                "protest_risk": False,
                "coup_risk": False,
            },
            "technology": {
                "nuclear_level": c["nuclear_level"],
                "nuclear_rd_progress": c["nuclear_rd_progress"],
                "nuclear_tested": c["nuclear_level"] >= 1,
                "ai_level": c["ai_level"],
                "ai_rd_progress": c["ai_rd_progress"],
            },
            "home_zones": [],
        }
    return engine_countries


def _build_default_world_state(round_num: int = 1) -> dict:
    """Build default world state matching tests/layer3 format."""
    return {
        "oil_price": 80.0,
        "oil_price_index": 100.0,
        "global_trade_volume_index": 100.0,
        "dollar_credibility": 100.0,
        "nuclear_used_this_sim": False,
        "formosa_blockade": False,
        "opec_production": {
            "sarmatia": "normal", "solaria": "normal",
            "persia": "normal", "mirage": "normal",
        },
        "chokepoint_status": {},
        "wars": [
            {"belligerents_a": ["sarmatia"], "belligerents_b": ["ruthenia"], "theater": "eastern_ereb"},
            {"belligerents_a": ["columbia", "levantia"], "belligerents_b": ["persia"], "theater": "mashriq"},
        ],
        "active_blockades": {},
        "oil_above_150_rounds": 0,
        "market_indexes": None,
        "rare_earth_restrictions": {},
        "round_num": round_num,
        "bilateral": {
            "sanctions": {
                "columbia": {"sarmatia": 2, "persia": 3},
                "teutonia": {"sarmatia": 2},
                "gallia": {"sarmatia": 2},
                "albion": {"sarmatia": 2},
                "yamato": {"sarmatia": 1},
            },
            "tariffs": {},
        },
        "relationships": {},
    }


# ---------------------------------------------------------------------------
# ROUND CONTEXT BUILDER — for agent decisions
# ---------------------------------------------------------------------------

def _build_round_context(
    agent_country: dict,
    world_state: dict,
    round_num: int,
    recent_events: list[dict] | None = None,
) -> dict:
    """Build the round_context dict that agents need for decisions."""
    return {
        "round_num": round_num,
        "economic": {
            "gdp": agent_country.get("gdp", 0),
            "treasury": agent_country.get("treasury", 0),
            "inflation": agent_country.get("inflation", 0),
            "debt_burden": agent_country.get("debt_burden", 0),
            "tax_rate": agent_country.get("tax_rate", 0.24),
            "social_baseline": agent_country.get("social_baseline", 0.30),
            "maintenance_cost": agent_country.get("maintenance_per_unit", 0.05),
            "oil_production_mbpd": agent_country.get("oil_production_mbpd", 0),
        },
        "political": {
            "stability": agent_country.get("stability", 5),
            "political_support": agent_country.get("political_support", 50),
        },
        "oil_price": world_state.get("oil_price", 80),
        "bilateral": world_state.get("bilateral", {"tariffs": {}, "sanctions": {}, "trade": {}}),
        "wars": world_state.get("wars", []),
        "military": {
            "units": {
                "ground": agent_country.get("mil_ground", 0),
                "naval": agent_country.get("mil_naval", 0),
                "tactical_air": agent_country.get("mil_tactical_air", 0),
                "strategic_missiles": agent_country.get("mil_strategic_missiles", 0),
                "air_defense": agent_country.get("mil_air_defense", 0),
            },
            "zones": {},
            "reserves": {},
            "enemy_visible": {},
            "mobilization_pool": agent_country.get("mobilization_pool", 0),
        },
        "recent_events": recent_events or [],
        "pending_conversations": [],
    }


# ---------------------------------------------------------------------------
# PHASE 1: START ROUND — update all agents with world state
# ---------------------------------------------------------------------------

async def _start_round(
    round_num: int,
    agents: dict[str, LeaderAgent],
    countries: dict[str, dict],
    world_state: dict,
    log: list[str],
) -> None:
    """Update all agents at round start with current world state."""
    log.append(f"Starting round {round_num} — updating {len(agents)} agents")

    events_since_last: list[dict] = []
    if round_num > 1:
        events_since_last.append({
            "type": "round_end",
            "summary": f"Round {round_num - 1} completed. New round beginning.",
        })

    for role_id, agent in agents.items():
        # Build visible world state for this agent
        country_id = agent.role.get("country_code", "")
        country_data = countries.get(country_id, {})

        # Update agent's country data with current state
        if country_data:
            agent.country.update(country_data)

        # Call start_round on agent (updates situational awareness)
        world_state_visible = {
            "round_num": round_num,
            "oil_price": world_state.get("oil_price", 80),
            "wars": world_state.get("wars", []),
            "bilateral": world_state.get("bilateral", {}),
        }
        agent.cognitive.update_immediate(
            f"Round {round_num} starting. Oil price: ${world_state.get('oil_price', 80):.0f}. "
            f"Active wars: {len(world_state.get('wars', []))}."
        )
        agent.status = "idle"

    log.append(f"All agents updated for round {round_num}")


# ---------------------------------------------------------------------------
# PHASE 2: ACTIVE LOOP — agents decide, converse, transact
# ---------------------------------------------------------------------------

async def _active_loop(
    tick: int,
    agents: dict[str, LeaderAgent],
    countries: dict[str, dict],
    world_state: dict,
    round_num: int,
    log: list[str],
) -> tuple[list[dict], list[dict], list[dict]]:
    """One iteration of the active loop.

    Returns:
        (actions, conversations, transactions) for this tick.
    """
    from engine.agents.conversations import ConversationEngine
    from engine.agents.transactions import run_transaction_flow

    actions: list[dict] = []
    conversations: list[dict] = []
    transactions: list[dict] = []

    log.append(f"  Active loop tick {tick + 1}")

    # Step A: All agents decide what to do (parallel)
    time_remaining = 1.0 - (tick / 3.0)  # decreasing urgency
    decision_tasks = {}

    for role_id, agent in agents.items():
        country_id = agent.role.get("country_code", "")
        country_data = countries.get(country_id, {})
        round_context = _build_round_context(country_data, world_state, round_num)
        decision_tasks[role_id] = agent.decide_action(
            time_remaining=time_remaining,
            new_events=[],
            round_context=round_context,
        )

    # Run all decisions in parallel
    results = await asyncio.gather(
        *decision_tasks.values(),
        return_exceptions=True,
    )
    role_ids = list(decision_tasks.keys())

    # Collect conversation requests and other actions
    conversation_requests: list[tuple[str, str, str]] = []  # (requester, target, detail)
    transaction_requests: list[tuple[str, str]] = []  # (proposer, target)

    for i, result in enumerate(results):
        role_id = role_ids[i]
        if isinstance(result, Exception):
            log.append(f"    {role_id}: decision error — {result}")
            continue
        if result is None:
            continue  # agent chose to wait

        action_type = result.get("type", "unknown")
        actions.append({"role_id": role_id, **result})
        log.append(f"    {role_id}: {action_type} — {result.get('detail', result.get('reasoning', ''))[:60]}")

        if action_type == "request_conversation":
            target = result.get("target", "")
            if target and target in agents:
                conversation_requests.append((role_id, target, result.get("detail", "")))
            elif target:
                # Target might be a country_id — find the head of state
                for rid, ag in agents.items():
                    if ag.role.get("country_code") == target:
                        conversation_requests.append((role_id, rid, result.get("detail", "")))
                        break

        elif action_type == "propose_transaction":
            target = result.get("target", "")
            if target:
                transaction_requests.append((role_id, target))

    # Step B: Match and run conversations (sequential to avoid agent conflicts)
    matched: set[str] = set()
    conv_engine = ConversationEngine()

    for requester, target, detail in conversation_requests:
        if requester in matched or target in matched:
            continue
        if requester not in agents or target not in agents:
            continue

        matched.add(requester)
        matched.add(target)

        log.append(f"    Bilateral: {requester} <-> {target}")
        try:
            conv_result = await conv_engine.run_bilateral(
                agents[requester], agents[target],
                max_turns=6,
                topic=detail,
            )
            conversations.append({
                "agents": [requester, target],
                "turns": conv_result.turns,
                "ended_by": conv_result.ended_by,
                "transcript_summary": [
                    f"{t['speaker_name']}: {t['text'][:80]}..."
                    for t in conv_result.transcript[:3]
                ],
            })
            log.append(f"    Bilateral complete: {conv_result.turns} turns")
        except Exception as e:
            log.append(f"    Bilateral failed: {e}")

    # Step C: Transaction proposals (simplified — pick random pairs for now)
    # In the active loop, agents that chose "propose_transaction" get matched
    for proposer_id, target_id in transaction_requests:
        if proposer_id not in agents or target_id not in agents:
            continue
        try:
            proposal = await run_transaction_flow(
                proposer_agent=agents[proposer_id],
                counterpart_agent=agents[target_id],
                world_state=world_state,
                countries=countries,
            )
            transactions.append(proposal.to_dict())
            log.append(f"    Transaction: {proposer_id} → {target_id}: {proposal.type} ({proposal.status})")
        except Exception as e:
            log.append(f"    Transaction failed: {e}")

    return actions, conversations, transactions


# ---------------------------------------------------------------------------
# PHASE 3: MANDATORY SUBMISSION
# ---------------------------------------------------------------------------

async def _mandatory_submission(
    agents: dict[str, LeaderAgent],
    countries: dict[str, dict],
    world_state: dict,
    round_num: int,
    log: list[str],
) -> dict[str, dict]:
    """All agents submit mandatory round-end decisions (parallel)."""
    log.append("  Mandatory submissions starting")

    tasks = {}
    for role_id, agent in agents.items():
        country_id = agent.role.get("country_code", "")
        country_data = countries.get(country_id, {})
        round_context = _build_round_context(country_data, world_state, round_num)
        tasks[role_id] = agent.submit_mandatory_inputs(round_context)

    results = await asyncio.gather(*tasks.values(), return_exceptions=True)
    role_ids = list(tasks.keys())

    mandatory_inputs: dict[str, dict] = {}
    for i, result in enumerate(results):
        role_id = role_ids[i]
        if isinstance(result, Exception):
            log.append(f"    {role_id}: mandatory submission error — {result}")
            mandatory_inputs[role_id] = _default_mandatory(countries.get(
                agents[role_id].role.get("country_code", ""), {}
            ))
        else:
            mandatory_inputs[role_id] = result
            budget = result.get("budget", {})
            log.append(
                f"    {role_id}: social={budget.get('social_pct', 1.0):.2f} "
                f"mil={budget.get('military_coins', 0):.0f} tech={budget.get('tech_coins', 0):.0f}"
            )

    log.append(f"  {len(mandatory_inputs)} mandatory submissions collected")
    return mandatory_inputs


def _default_mandatory(country: dict) -> dict:
    """Fallback mandatory inputs if LLM call fails."""
    return {
        "budget": {"social_pct": 1.0, "military_coins": 0, "tech_coins": 0},
        "tariffs": {},
        "sanctions": {},
        "opec_production": "normal" if country.get("opec_member") else None,
        "reasoning": {"budget": "default", "tariffs": "default", "sanctions": "default", "opec": "default"},
    }


# ---------------------------------------------------------------------------
# PHASE 4: ENGINE PROCESSING (Pass 1)
# ---------------------------------------------------------------------------

def _run_engines(
    engine_countries: dict[str, dict],
    world_state: dict,
    mandatory_inputs: dict[str, dict],
    agents: dict[str, LeaderAgent],
    round_num: int,
    log: list[str],
) -> dict:
    """Run economic + political engines (Pass 1).

    Returns engine results dict.
    """
    from engine.engines.economic import process_economy, get_market_stress_for_country
    from engine.engines.political import (
        StabilityInput, PoliticalSupportInput, WarTirednessInput,
        calc_stability, calc_political_support, update_war_tiredness,
        check_revolution,
    )

    # Build actions dict from mandatory inputs
    actions: dict[str, Any] = {
        "tariff_changes": {},
        "sanction_changes": {},
        "opec_production": {},
        "budget": {},
        "blockade_changes": {},
    }

    for role_id, inputs in mandatory_inputs.items():
        if role_id not in agents:
            continue
        country_id = agents[role_id].role.get("country_code", "")
        if not country_id:
            continue

        # Tariffs
        for target, level in inputs.get("tariffs", {}).items():
            actions["tariff_changes"].setdefault(country_id, {})[target] = level

        # Sanctions
        for target, level in inputs.get("sanctions", {}).items():
            actions["sanction_changes"].setdefault(country_id, {})[target] = level

        # OPEC
        if inputs.get("opec_production"):
            actions["opec_production"][country_id] = inputs["opec_production"]

        # Budget — apply social spending
        budget = inputs.get("budget", {})
        if country_id in engine_countries:
            eco = engine_countries[country_id]["economic"]
            eco["_actual_social_ratio"] = (
                eco["social_spending_baseline"] * budget.get("social_pct", 1.0)
            )

    # Apply action changes to world state
    bilateral = world_state.setdefault("bilateral", {})
    s_dict = bilateral.setdefault("sanctions", {})
    t_dict = bilateral.setdefault("tariffs", {})
    for imp, tgts in actions["tariff_changes"].items():
        for tgt, lvl in tgts.items():
            t_dict.setdefault(imp, {})[tgt] = lvl
    for imp, tgts in actions["sanction_changes"].items():
        for tgt, lvl in tgts.items():
            s_dict.setdefault(imp, {})[tgt] = lvl
    opec = world_state.setdefault("opec_production", {})
    for country, level in actions["opec_production"].items():
        opec[country] = level

    world_state["round_num"] = round_num

    # Snapshot previous state
    wars = world_state.get("wars", [])
    previous_states = {
        cid: {
            "economic_state": c["economic"].get("economic_state", "normal"),
            "gdp": c["economic"]["gdp"],
            "stability": c["political"]["stability"],
            "at_war": _is_at_war(cid, wars),
        }
        for cid, c in engine_countries.items()
    }

    # ECONOMIC ENGINE
    econ_result = process_economy(engine_countries, world_state, actions, previous_states)

    # Sync results back
    for cid, cr in econ_result.countries.items():
        if cid not in engine_countries:
            continue
        eco = engine_countries[cid]["economic"]
        eco["gdp"] = cr.gdp.new_gdp
        eco["gdp_growth_rate"] = cr.gdp.growth_pct
        eco["inflation"] = cr.inflation
        eco["debt_burden"] = cr.debt_burden
        eco["economic_state"] = cr.economic_state.new_state
        eco["momentum"] = cr.momentum.new_momentum
        eco["treasury"] = cr.budget.new_treasury if hasattr(cr, "budget") else eco["treasury"]

    # Update world state
    world_state["oil_price"] = econ_result.oil_price.price
    world_state["oil_above_150_rounds"] = econ_result.oil_above_150_rounds
    if econ_result.market_indexes:
        world_state["market_indexes"] = {
            "wall_street": econ_result.market_indexes.wall_street.new_value,
            "europa": econ_result.market_indexes.europa.new_value,
            "dragon": econ_result.market_indexes.dragon.new_value,
        }

    # POLITICAL ENGINE — stability + support
    stability_results = {}
    support_results = {}
    revolution_results = {}

    for cid, c in engine_countries.items():
        eco, pol = c["economic"], c["political"]
        at_war = _is_at_war(cid, wars)

        # War tiredness
        wt = update_war_tiredness(WarTirednessInput(
            country_id=cid, war_tiredness=pol["war_tiredness"], at_war=at_war,
            is_defender=any(cid in w.get("belligerents_b", []) for w in wars),
            is_attacker=any(cid in w.get("belligerents_a", []) for w in wars),
        ))
        pol["war_tiredness"] = wt.new_war_tiredness

        # Market stress
        mkt_stress = 0.0
        if econ_result.market_indexes is not None:
            mkt_stress = get_market_stress_for_country(cid, econ_result.market_indexes)

        sr = calc_stability(StabilityInput(
            country_id=cid, stability=pol["stability"], regime_type=c["regime_type"],
            gdp_growth_rate=eco.get("gdp_growth_rate", 0.0),
            economic_state=eco.get("economic_state", "normal"),
            inflation=eco["inflation"], starting_inflation=eco.get("starting_inflation", 0.0),
            at_war=at_war, war_tiredness=pol["war_tiredness"],
            market_stress=mkt_stress,
            social_spending_ratio=eco.get("_actual_social_ratio", eco.get("social_spending_baseline", 0.20)),
            social_spending_baseline=eco.get("social_spending_baseline", 0.20), gdp=eco["gdp"],
        ))
        pol["stability"] = sr.new_stability
        stability_results[cid] = {"old": sr.old_stability, "new": sr.new_stability}

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
        support_results[cid] = {"old": sp.old_support, "new": sp.new_support}

        # Revolution check
        rev = check_revolution(cid, pol["stability"], pol["political_support"])
        if rev is not None:
            revolution_results[cid] = {"severity": rev.severity}
            log.append(f"  REVOLUTION: {cid} — {rev.severity}")

    log.append(f"  Engines complete. Oil=${econ_result.oil_price.price:.1f}")

    return {
        "oil_price": econ_result.oil_price.price,
        "stability": stability_results,
        "support": support_results,
        "revolutions": revolution_results,
        "economic_summary": {
            cid: {
                "gdp": cr.gdp.new_gdp,
                "growth": cr.gdp.growth_pct,
                "inflation": cr.inflation,
                "state": cr.economic_state.new_state,
            }
            for cid, cr in econ_result.countries.items()
        },
    }


# ---------------------------------------------------------------------------
# PHASE 5: NOUS (Pass 2) — optional
# ---------------------------------------------------------------------------

async def _run_nous(
    engine_countries: dict[str, dict],
    world_state: dict,
    engine_results: dict,
    round_num: int,
    nous_intensity: int,
    log: list[str],
) -> dict | None:
    """Run NOUS judgment layer (Pass 2). Returns adjustments or None."""
    if nous_intensity <= 0:
        log.append("  NOUS skipped (intensity=0)")
        return None

    try:
        from engine.context.assembler import ContextAssembler
        from engine.judgment.judge import WorldJudge

        assembler = ContextAssembler(
            sim_run_id="unmanned_sim",
            template_id="default",
            countries=engine_countries,
            world_state=world_state,
            round_results=engine_results,
        )
        judge = WorldJudge(assembler=assembler, intensity=nous_intensity)
        judgment, warnings = await judge.judge_round(round_num)

        log.append(f"  NOUS complete: confidence={judgment.confidence:.2f}, warnings={len(warnings)}")

        # Apply NOUS adjustments to engine countries
        for adj in judgment.stability_adjustments:
            cid = adj.country
            if cid in engine_countries:
                pol = engine_countries[cid]["political"]
                pol["stability"] = max(0, min(9, pol["stability"] + adj.delta))

        for adj in judgment.support_adjustments:
            cid = adj.country
            if cid in engine_countries:
                pol = engine_countries[cid]["political"]
                pol["political_support"] = max(0, min(100, pol["political_support"] + adj.delta))

        return {
            "confidence": judgment.confidence,
            "stability_adjustments": [{"country": a.country, "delta": a.delta} for a in judgment.stability_adjustments],
            "support_adjustments": [{"country": a.country, "delta": a.delta} for a in judgment.support_adjustments],
            "warnings": warnings,
        }
    except Exception as e:
        log.append(f"  NOUS error: {e}")
        return None


# ---------------------------------------------------------------------------
# PHASE 6: REFLECTION — agents update cognitive blocks
# ---------------------------------------------------------------------------

async def _reflect(
    agents: dict[str, LeaderAgent],
    engine_countries: dict[str, dict],
    engine_results: dict,
    round_num: int,
    log: list[str],
) -> dict[str, dict]:
    """All agents reflect on round results (parallel)."""
    from engine.services.llm import call_llm
    from engine.config.settings import LLMUseCase

    reflections: dict[str, dict] = {}

    # Build round summary for agents
    oil_price = engine_results.get("oil_price", 80)
    revolutions = engine_results.get("revolutions", {})

    tasks = {}
    for role_id, agent in agents.items():
        country_id = agent.role.get("country_code", "")
        eco_summary = engine_results.get("economic_summary", {}).get(country_id, {})
        stab = engine_results.get("stability", {}).get(country_id, {})
        supp = engine_results.get("support", {}).get(country_id, {})

        round_summary = (
            f"Round {round_num} results for {agent.country.get('sim_name', country_id)}: "
            f"GDP growth {eco_summary.get('growth', 0):.1%}, "
            f"inflation {eco_summary.get('inflation', 0):.1f}%, "
            f"state={eco_summary.get('state', 'normal')}, "
            f"stability {stab.get('new', '?'):.1f}, "
            f"support {supp.get('new', '?'):.0f}%. "
            f"Oil price: ${oil_price:.0f}."
        )

        if country_id in revolutions:
            round_summary += f" REVOLUTION: {revolutions[country_id]['severity']}!"

        prompt = (
            f"Round {round_num} just ended. Here are the results:\n\n{round_summary}\n\n"
            f"Update your strategic assessment. What should you prioritize next round? "
            f"Any threats or opportunities? Keep it to 3-5 bullet points."
        )

        tasks[role_id] = call_llm(
            use_case=LLMUseCase.AGENT_REFLECTION,
            messages=[{"role": "user", "content": prompt}],
            system=(
                f"You are {agent.role.get('character_name', role_id)}, "
                f"{agent.role.get('title', '')} of {agent.country.get('sim_name', '')}. "
                f"Reflect briefly on round results. Write 3-5 bullet points."
            ),
            max_tokens=400,
            temperature=0.5,
        )

    # Run all reflections in parallel
    results = await asyncio.gather(*tasks.values(), return_exceptions=True)
    role_ids = list(tasks.keys())

    for i, result in enumerate(results):
        role_id = role_ids[i]
        agent = agents[role_id]
        country_id = agent.role.get("country_code", "")

        if isinstance(result, Exception):
            reflection_text = f"Round {round_num} completed. Continuing current strategy."
            log.append(f"    {role_id}: reflection error — {result}")
        else:
            reflection_text = result.text

        # Update agent's goals with reflection
        current_goals = agent.cognitive.get_goals_text()
        agent.cognitive.update_goals_text(
            f"{current_goals}\n\n[Post-Round {round_num} Assessment]:\n{reflection_text}",
            reason=f"round_{round_num}_reflection",
        )

        # End round in memory
        eco_summary = engine_results.get("economic_summary", {}).get(country_id, {})
        agent.cognitive.end_round(
            round_num,
            f"GDP {eco_summary.get('growth', 0):.1%}, oil ${oil_price:.0f}. {reflection_text[:100]}",
        )

        reflections[role_id] = {"reflection": reflection_text[:200]}

    log.append(f"  {len(reflections)} agents reflected")
    return reflections


# ---------------------------------------------------------------------------
# SYNC ENGINE RESULTS BACK TO FLAT COUNTRIES
# ---------------------------------------------------------------------------

def _sync_to_flat_countries(
    countries_flat: dict[str, dict],
    engine_countries: dict[str, dict],
) -> None:
    """Sync engine-format nested dicts back to flat country dicts."""
    for cid, ec in engine_countries.items():
        if cid not in countries_flat:
            continue
        c = countries_flat[cid]
        eco = ec["economic"]
        pol = ec["political"]
        c["gdp"] = eco["gdp"]
        c["inflation"] = eco["inflation"]
        c["debt_burden"] = eco["debt_burden"]
        c["treasury"] = eco.get("treasury", c.get("treasury", 0))
        c["stability"] = pol["stability"]
        c["political_support"] = pol["political_support"]
        c["war_tiredness"] = pol.get("war_tiredness", 0)


# ---------------------------------------------------------------------------
# MAIN: RUN ONE ROUND
# ---------------------------------------------------------------------------

async def run_round(
    round_num: int,
    agents: dict[str, LeaderAgent],
    countries: dict[str, dict],
    world_state: dict,
    active_loop_ticks: int = 3,
    nous_intensity: int = 3,
    sim_run_id: str | None = None,
) -> RoundReport:
    """Orchestrate a complete simulation round.

    Args:
        round_num: Current round number.
        agents: {role_id: LeaderAgent} — initialized agents.
        countries: {country_id: country_flat_data} — mutable.
        world_state: Current world state dict — mutable.
        active_loop_ticks: How many active loop iterations.
        nous_intensity: NOUS judgment intensity (0 = skip).
        sim_run_id: Optional sim_runs row id. If provided, the completed
            RoundReport (and its children) are persisted to Supabase.
            DB errors are logged but do not fail the round.

    Returns:
        RoundReport with all round data.
    """
    t0 = time.time()
    log: list[str] = [f"=== ROUND {round_num} START ({len(agents)} agents) ==="]
    report = RoundReport(round_num=round_num)

    # Phase 1: Start round
    await _start_round(round_num, agents, countries, world_state, log)

    # Phase 2: Active loop
    all_actions: dict[str, list[dict]] = {}
    all_conversations: list[dict] = []
    all_transactions: list[dict] = []

    for tick in range(active_loop_ticks):
        tick_actions, tick_convos, tick_txns = await _active_loop(
            tick, agents, countries, world_state, round_num, log,
        )
        for action in tick_actions:
            rid = action.get("role_id", "unknown")
            all_actions.setdefault(rid, []).append(action)
        all_conversations.extend(tick_convos)
        all_transactions.extend(tick_txns)

    report.actions_taken = all_actions
    report.conversations = all_conversations
    report.transactions = all_transactions

    # Phase 3: Mandatory submission
    mandatory_inputs = await _mandatory_submission(
        agents, countries, world_state, round_num, log,
    )
    report.mandatory_inputs = mandatory_inputs

    # Phase 4: Engine processing (Pass 1)
    engine_countries = _build_engine_countries(countries)
    engine_results = _run_engines(
        engine_countries, world_state, mandatory_inputs, agents, round_num, log,
    )
    report.engine_results = engine_results

    # Phase 5: NOUS (Pass 2)
    nous_adjustments = await _run_nous(
        engine_countries, world_state, engine_results, round_num, nous_intensity, log,
    )
    report.nous_adjustments = nous_adjustments

    # Sync engine results back to flat countries
    _sync_to_flat_countries(countries, engine_countries)

    # Phase 6: Reflection
    reflections = await _reflect(agents, engine_countries, engine_results, round_num, log)
    report.agent_reflections = reflections

    report.duration_seconds = time.time() - t0
    report.log = log
    log.append(f"=== ROUND {round_num} COMPLETE ({report.duration_seconds:.1f}s) ===")

    logger.info(report.summary())

    # Optional DB persistence
    if sim_run_id:
        try:
            from engine.agents.persistence import save_round_report
            save_round_report(sim_run_id, report)
        except Exception as e:
            logger.error("Persistence failed for round %d (sim_run=%s): %s",
                         round_num, sim_run_id, e)

    return report


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def _is_at_war(cid: str, wars: list[dict]) -> bool:
    """Check if country is a belligerent in any active war."""
    return any(
        cid in w.get("belligerents_a", []) or cid in w.get("belligerents_b", [])
        for w in wars
    )


# ---------------------------------------------------------------------------
# MAIN: RUN FULL SIM
# ---------------------------------------------------------------------------

async def run_full_sim(
    num_rounds: int = 6,
    active_loop_ticks: int = 3,
    nous_intensity: int = 3,
    sim_run_id: str | None = None,
) -> SimReport:
    """Run a complete unmanned simulation.

    Loads data from CSV, initializes all agents, runs N rounds.

    Args:
        num_rounds: Number of rounds to simulate (default 6).
        active_loop_ticks: Active loop iterations per round (default 3).
        nous_intensity: NOUS judgment intensity 0-5 (default 3).
        sim_run_id: Optional sim_runs row id. If provided, every round
            is persisted to Supabase and the run is marked complete at
            the end.

    Returns:
        SimReport with all round reports.
    """
    t0 = time.time()
    sim_report = SimReport(num_rounds=num_rounds)

    logger.info("=== UNMANNED SIM START: %d rounds, %d ticks/round, NOUS=%d ===",
                num_rounds, active_loop_ticks, nous_intensity)

    # Load data
    countries = load_countries_from_csv()
    world_state = _build_default_world_state(round_num=1)
    logger.info("Loaded %d countries from CSV", len(countries))

    # Initialize all head-of-state agents
    heads = load_heads_of_state()
    agents: dict[str, LeaderAgent] = {}

    logger.info("Initializing %d agents...", len(heads))
    init_tasks = {}
    for role_id in heads:
        agent = LeaderAgent(role_id)
        agents[role_id] = agent
        init_tasks[role_id] = agent.initialize(world_state={"relationships": world_state.get("relationships", {})})

    # Initialize all agents in parallel
    init_results = await asyncio.gather(*init_tasks.values(), return_exceptions=True)
    init_role_ids = list(init_tasks.keys())

    failed_inits = []
    for i, result in enumerate(init_results):
        role_id = init_role_ids[i]
        if isinstance(result, Exception):
            logger.warning("Agent %s init failed: %s — using sync fallback", role_id, result)
            agents[role_id].initialize_sync(world_state={"relationships": world_state.get("relationships", {})})
            failed_inits.append(role_id)

    logger.info("Agents initialized: %d OK, %d fallback", len(agents) - len(failed_inits), len(failed_inits))

    # Run rounds
    for round_num in range(1, num_rounds + 1):
        logger.info("--- Starting round %d of %d ---", round_num, num_rounds)
        world_state["round_num"] = round_num

        round_report = await run_round(
            round_num=round_num,
            agents=agents,
            countries=countries,
            world_state=world_state,
            active_loop_ticks=active_loop_ticks,
            nous_intensity=nous_intensity,
            sim_run_id=sim_run_id,
        )
        sim_report.rounds.append(round_report)
        logger.info("Round %d complete: %s", round_num, round_report.summary())

    # Final agent info
    sim_report.agents = {rid: agent.info() for rid, agent in agents.items()}
    sim_report.total_duration_seconds = time.time() - t0

    if sim_run_id:
        try:
            from engine.agents.persistence import mark_sim_run_complete
            mark_sim_run_complete(sim_run_id, current_round=num_rounds)
        except Exception as e:
            logger.error("Failed to mark sim_run complete: %s", e)

    logger.info("=== UNMANNED SIM COMPLETE: %s ===", sim_report.summary())
    return sim_report
