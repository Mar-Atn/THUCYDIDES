"""Layer 3 Scenario Test Runner — 5 scenarios × 6 rounds.

Runs the economic + political engines directly (no DB, no FastAPI).
Loads starting data from countries.csv, applies scenario-specific actions each round,
outputs results as markdown analysis.

Usage: cd app && PYTHONPATH=. python3 tests/layer3/run_scenarios.py
"""

import csv
import copy
import os
import sys
import json
from datetime import datetime
from typing import Any

# Add app/ to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from engine.engines.economic import (
    process_economy, EconomicResult, calc_sanctions_coefficient,
    calc_tariff_coefficient, get_market_stress_for_country,
)
from engine.engines.political import (
    StabilityInput, PoliticalSupportInput, WarTirednessInput,
    calc_stability, calc_political_support, update_war_tiredness,
    check_revolution,
)


# ---------------------------------------------------------------------------
# DATA LOADING — from CSV (single source of truth)
# ---------------------------------------------------------------------------

CSV_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..",
    "2 SEED", "C_MECHANICS", "C4_DATA", "countries.csv",
)

def load_countries_from_csv() -> dict[str, dict]:
    """Load all 20 countries from CSV into engine dict format."""
    countries = {}
    with open(CSV_PATH) as f:
        for row in csv.DictReader(f):
            cid = row["id"]
            countries[cid] = {
                "id": cid,
                "sim_name": row["sim_name"],
                "parallel": row["parallel"],
                "regime_type": row["regime_type"],
                "team_type": row["team_type"],
                "economic": {
                    "gdp": float(row["gdp"]),
                    "gdp_growth_rate": float(row["gdp_growth_base"]),
                    "gdp_growth_base": float(row["gdp_growth_base"]),
                    "sectors": {
                        "resources": float(row["sector_resources"]),
                        "industry": float(row["sector_industry"]),
                        "services": float(row["sector_services"]),
                        "technology": float(row["sector_technology"]),
                    },
                    "sector_resources": float(row["sector_resources"]),
                    "sector_industry": float(row["sector_industry"]),
                    "sector_services": float(row["sector_services"]),
                    "sector_technology": float(row["sector_technology"]),
                    "tax_rate": float(row["tax_rate"]),
                    "treasury": float(row["treasury"]),
                    "inflation": float(row["inflation"]),
                    "starting_inflation": float(row["inflation"]),
                    "trade_balance": float(row["trade_balance"]),
                    "oil_producer": row["oil_producer"].lower() == "true",
                    "oil_production_mbpd": float(row["oil_production_mbpd"]),
                    "opec_member": row["opec_member"].lower() == "true",
                    "opec_production": row.get("opec_production", "na"),
                    "formosa_dependency": float(row["formosa_dependency"]),
                    "debt_burden": float(row["debt_burden"]),
                    "social_spending_baseline": float(row["social_baseline"]),
                    "oil_revenue": 0.0,
                    "inflation_revenue_erosion": 0.0,
                    "sanctions_rounds": 0,
                    "sanctions_recovery_rounds": 0,
                    "sanctions_adaptation_rounds": 0,
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
                    "ground": int(float(row["mil_ground"])),
                    "naval": int(float(row["mil_naval"])),
                    "tactical_air": int(float(row["mil_tactical_air"])),
                    "strategic_missile": int(float(row["mil_strategic_missiles"])),
                    "air_defense": int(float(row["mil_air_defense"])),
                    "production_costs": {
                        "ground": float(row["prod_cost_ground"]),
                        "naval": float(row["prod_cost_naval"]),
                        "tactical_air": float(row["prod_cost_tactical"]),
                    },
                    "production_capacity": {
                        "ground": int(float(row["prod_cap_ground"])),
                        "naval": int(float(row["prod_cap_naval"])),
                        "tactical_air": int(float(row["prod_cap_tactical"])),
                    },
                    "maintenance_cost_per_unit": float(row["maintenance_per_unit"]),
                    "strategic_missile_growth": int(float(row["strategic_missile_growth"])),
                    "mobilization_pool": int(float(row["mobilization_pool"])),
                },
                "political": {
                    "stability": float(row["stability"]),
                    "political_support": float(row["political_support"]),
                    "dem_rep_split": {
                        "dem": float(row["dem_rep_split_dem"]),
                        "rep": float(row["dem_rep_split_rep"]),
                    },
                    "war_tiredness": float(row["war_tiredness"]),
                    "regime_type": row["regime_type"],
                    "regime_status": "stable",
                    "protest_risk": False,
                    "coup_risk": False,
                },
                "technology": {
                    "nuclear_level": int(row["nuclear_level"]),
                    "nuclear_rd_progress": float(row["nuclear_rd_progress"]),
                    "nuclear_tested": int(row["nuclear_level"]) >= 1,
                    "ai_level": int(row["ai_level"]),
                    "ai_rd_progress": float(row["ai_rd_progress"]),
                },
                "home_zones": [z.strip() for z in row.get("home_zones", "").strip('"').split(",") if z.strip()],
            }
    return countries


def build_world_state(sanctions: dict = None, tariffs: dict = None) -> dict:
    """Build initial world state."""
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
            {
                "belligerents_a": ["sarmatia"],
                "belligerents_b": ["ruthenia"],
                "theater": "eastern_ereb",
            },
            {
                "belligerents_a": ["columbia", "levantia"],
                "belligerents_b": ["persia"],
                "theater": "mashriq",
            },
        ],
        "active_blockades": {},
        "oil_above_150_rounds": 0,
        "market_indexes": None,
        "rare_earth_restrictions": {},
        "round_num": 1,
        "bilateral": {
            "sanctions": sanctions or {
                "columbia": {"sarmatia": 2, "persia": 3},
                "teutonia": {"sarmatia": 2},
                "gallia": {"sarmatia": 2},
                "albion": {"sarmatia": 2},
                "yamato": {"sarmatia": 1},
            },
            "tariffs": tariffs or {},
        },
        "relationships": {},
    }


# ---------------------------------------------------------------------------
# ROUND PROCESSING — chains economic + political
# ---------------------------------------------------------------------------

def _is_at_war(cid: str, wars: list[dict]) -> bool:
    return any(
        cid in w.get("belligerents_a", []) or cid in w.get("belligerents_b", [])
        for w in wars
    )


def process_full_round(
    countries: dict[str, dict],
    world_state: dict,
    actions: dict,
    round_num: int,
) -> dict:
    """Process one full round: economic → stability → support → revolution check."""
    world_state["round_num"] = round_num

    # Snapshot previous state
    previous_states = {
        cid: {
            "economic_state": c["economic"].get("economic_state", "normal"),
            "gdp": c["economic"]["gdp"],
            "stability": c["political"]["stability"],
            "at_war": _is_at_war(cid, world_state["wars"]),
        }
        for cid, c in countries.items()
    }

    # ECONOMIC ENGINE
    econ_result = process_economy(countries, world_state, actions, previous_states)

    # Sync results back
    for cid, cr in econ_result.countries.items():
        if cid not in countries:
            continue
        eco = countries[cid]["economic"]
        eco["gdp"] = cr.gdp.new_gdp
        eco["gdp_growth_rate"] = cr.gdp.growth_pct
        eco["inflation"] = cr.inflation
        eco["debt_burden"] = cr.debt_burden
        eco["economic_state"] = cr.economic_state.new_state
        eco["momentum"] = cr.momentum.new_momentum
        eco["treasury"] = cr.budget.new_treasury if hasattr(cr, 'budget') else eco["treasury"]

    # Update world state for next round
    world_state["oil_price"] = econ_result.oil_price.price
    world_state["oil_above_150_rounds"] = econ_result.oil_above_150_rounds
    if econ_result.market_indexes:
        world_state["market_indexes"] = {
            "wall_street": econ_result.market_indexes.wall_street.new_value,
            "europa": econ_result.market_indexes.europa.new_value,
            "dragon": econ_result.market_indexes.dragon.new_value,
        }

    # POLITICAL ENGINE — stability + support
    wars = world_state["wars"]
    revolutions = {}

    for cid, c in countries.items():
        eco, pol = c["economic"], c["political"]
        at_war = _is_at_war(cid, wars)

        # War tiredness
        wt = update_war_tiredness(WarTirednessInput(
            country_id=cid, war_tiredness=pol["war_tiredness"], at_war=at_war,
            is_defender=any(cid in w.get("belligerents_b", []) for w in wars),
            is_attacker=any(cid in w.get("belligerents_a", []) for w in wars),
        ))
        pol["war_tiredness"] = wt.new_war_tiredness

        # Market stress from indexes
        mkt_stress = 0.0
        if econ_result.market_indexes:
            mkt_stress = get_market_stress_for_country(cid, econ_result.market_indexes)

        # Stability
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

        # Support
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

        # Revolution check
        rev = check_revolution(cid, pol["stability"], pol["political_support"])
        if rev:
            revolutions[cid] = rev.severity

    return {
        "oil_price": econ_result.oil_price.price,
        "market_indexes": world_state.get("market_indexes"),
        "revolutions": revolutions,
        "log": econ_result.log[:5],  # first 5 log lines
    }


# ---------------------------------------------------------------------------
# SCENARIO DEFINITIONS
# ---------------------------------------------------------------------------

FOCUS_COUNTRIES = [
    "columbia", "cathay", "sarmatia", "ruthenia", "persia",
    "teutonia", "bharata", "formosa", "levantia", "yamato",
]


def scenario_baseline():
    """S1: No player actions — pure engine dynamics."""
    return {
        "name": "S1: Baseline (no intervention)",
        "description": "All countries on autopilot. Tests natural economic trajectories, budget balance, and stability.",
        "rounds": [{} for _ in range(6)],  # empty actions each round
        "sanctions_override": None,
        "tariffs_override": None,
    }


def scenario_economic_pressure():
    """S2: Economic pressure — escalating sanctions + oil disruption."""
    return {
        "name": "S2: Economic Pressure",
        "description": "Columbia escalates sanctions on Sarmatia to L3, full coalition. Gulf Gate blockade R3.",
        "rounds": [
            {},  # R1: status quo
            {"sanction_changes": {"columbia": {"sarmatia": 3}, "hanguk": {"sarmatia": 2}}},  # R2
            {"sanction_changes": {"bharata": {"sarmatia": 1}},
             "blockade_changes": {"gulf_gate_ground": {"status": "blocked", "controller": "persia"}}},  # R3
            {},  # R4
            {},  # R5
            {"sanction_changes": {"columbia": {"sarmatia": 2}}},  # R6: partial relief
        ],
        "sanctions_override": None,
        "tariffs_override": None,
    }


def scenario_tariff_wars():
    """S3: Tariff wars — US-China trade war escalation."""
    return {
        "name": "S3: Tariff Wars (Prisoner's Dilemma)",
        "description": "Columbia imposes L2 tariffs on Cathay R1. Cathay retaliates L2 R2. Full escalation L3 R3. Tests asymmetric impact.",
        "rounds": [
            {"tariff_changes": {"columbia": {"cathay": 2}}},  # R1: Columbia strikes
            {"tariff_changes": {"cathay": {"columbia": 2}}},  # R2: Cathay retaliates
            {"tariff_changes": {"columbia": {"cathay": 3}, "cathay": {"columbia": 3}}},  # R3: full war
            {"tariff_changes": {"teutonia": {"cathay": 1}, "cathay": {"teutonia": 1}}},  # R4: spreads
            {},  # R5: stalemate
            {"tariff_changes": {"columbia": {"cathay": 1}, "cathay": {"columbia": 1}}},  # R6: de-escalation
        ],
        "sanctions_override": None,
        "tariffs_override": None,
    }


def scenario_thucydides_trap():
    """S4: The Thucydides Trap — rising Cathay vs incumbent Columbia."""
    return {
        "name": "S4: Thucydides Trap (Rising Power vs Incumbent)",
        "description": "Cathay builds naval, Columbia responds with tariffs + tech race. Formosa crisis R4. Tests power transition dynamics.",
        "rounds": [
            {"tariff_changes": {"columbia": {"cathay": 1}}},  # R1: opening salvo
            {"tariff_changes": {"cathay": {"columbia": 1}},
             "sanction_changes": {"columbia": {"cathay": 1}}},  # R2: escalation
            {"tariff_changes": {"columbia": {"cathay": 2}, "cathay": {"columbia": 2}}},  # R3: trade war
            {},  # R4: Formosa crisis (blockade)
            {"sanction_changes": {"columbia": {"cathay": 2}, "yamato": {"cathay": 1},
                                  "hanguk": {"cathay": 1}, "albion": {"cathay": 1}}},  # R5: coalition
            {},  # R6: standoff
        ],
        "sanctions_override": None,
        "tariffs_override": None,
        "special": {
            4: {"formosa_blockade": True},  # Cathay blockades Formosa at R4
        },
    }


def scenario_military_escalation():
    """S5: Military escalation — Sarmatia offensive + nuclear crisis."""
    return {
        "name": "S5: Military Escalation + Nuclear Crisis",
        "description": "Sarmatia launches offensive R2. Persia approaches nuclear breakout. Cathay naval buildup. Tests escalation spiral.",
        "rounds": [
            {},  # R1: buildup
            {},  # R2: Sarmatia offensive (simulated via war intensification)
            {"sanction_changes": {"columbia": {"sarmatia": 3}, "teutonia": {"sarmatia": 3},
                                  "gallia": {"sarmatia": 3}, "albion": {"sarmatia": 3}}},  # R3: max sanctions
            {},  # R4: grinding war
            {},  # R5: exhaustion
            {},  # R6: potential ceasefire dynamics
        ],
        "sanctions_override": None,
        "tariffs_override": None,
    }


SCENARIOS = [
    scenario_baseline,
    scenario_economic_pressure,
    scenario_tariff_wars,
    scenario_thucydides_trap,
    scenario_military_escalation,
]


# ---------------------------------------------------------------------------
# RECORDING + ANALYSIS
# ---------------------------------------------------------------------------

def snapshot_countries(countries: dict, focus: list[str]) -> dict:
    """Capture key metrics for focus countries."""
    snap = {}
    for cid in focus:
        if cid not in countries:
            continue
        c = countries[cid]
        eco, pol = c["economic"], c["political"]
        snap[cid] = {
            "gdp": round(eco["gdp"], 2),
            "growth": round(eco.get("gdp_growth_rate", 0), 2),
            "treasury": round(eco.get("treasury", 0), 1),
            "inflation": round(eco["inflation"], 1),
            "debt": round(eco["debt_burden"], 3),
            "sanctions_coeff": round(eco.get("sanctions_coefficient", 1.0), 3),
            "tariff_coeff": round(eco.get("tariff_coefficient", 1.0), 3),
            "stability": round(pol["stability"], 2),
            "support": round(pol["political_support"], 1),
            "war_tiredness": round(pol.get("war_tiredness", 0), 1),
            "eco_state": eco.get("economic_state", "normal"),
        }
    return snap


def run_scenario(scenario_fn) -> dict:
    """Run one scenario: 6 rounds, return all snapshots."""
    scenario = scenario_fn()
    countries = load_countries_from_csv()
    world_state = build_world_state(
        sanctions=scenario.get("sanctions_override"),
        tariffs=scenario.get("tariffs_override"),
    )

    # L0: compute starting coefficients
    for cid, c in countries.items():
        eco = c["economic"]
        eco["sanctions_coefficient"] = calc_sanctions_coefficient(
            cid, countries, world_state["bilateral"]["sanctions"],
        )
        tar_coeff, tar_infl, tar_rev = calc_tariff_coefficient(
            cid, countries, world_state["bilateral"]["tariffs"],
        )
        eco["tariff_coefficient"] = tar_coeff

    # Record R0 (starting state)
    snapshots = [("R0", snapshot_countries(countries, FOCUS_COUNTRIES), 80.0, None)]

    for rnd in range(1, 7):
        actions = scenario["rounds"][rnd - 1]

        # Apply special events (e.g., Formosa blockade)
        specials = scenario.get("special", {})
        if rnd in specials:
            for k, v in specials[rnd].items():
                world_state[k] = v
                if k == "formosa_blockade" and v:
                    # Formosa disruption starts
                    for cid2 in countries:
                        countries[cid2]["economic"]["formosa_disruption_rounds"] = (
                            countries[cid2]["economic"].get("formosa_disruption_rounds", 0) + 1
                        )

        # Apply action mutations to world_state bilateral
        if "tariff_changes" in actions:
            for imp, tgts in actions["tariff_changes"].items():
                for tgt, lvl in tgts.items():
                    world_state["bilateral"]["tariffs"].setdefault(imp, {})[tgt] = lvl
        if "sanction_changes" in actions:
            for imp, tgts in actions["sanction_changes"].items():
                for tgt, lvl in tgts.items():
                    world_state["bilateral"]["sanctions"].setdefault(imp, {})[tgt] = lvl
        if "blockade_changes" in actions:
            for cp, info in actions["blockade_changes"].items():
                world_state["active_blockades"][cp] = info

        result = process_full_round(countries, world_state, actions, rnd)
        snap = snapshot_countries(countries, FOCUS_COUNTRIES)
        snapshots.append((
            f"R{rnd}", snap, result["oil_price"],
            result.get("market_indexes"), result.get("revolutions"),
        ))

    return {
        "name": scenario["name"],
        "description": scenario["description"],
        "snapshots": snapshots,
    }


# ---------------------------------------------------------------------------
# OUTPUT — Markdown Report
# ---------------------------------------------------------------------------

def format_report(results: list[dict]) -> str:
    """Generate markdown analysis report."""
    lines = [
        f"# TTT Scenario Test Results",
        f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**Engine:** economic.py + political.py (direct, no DB)",
        f"**Data:** countries.csv (D1-D18 calibration applied)",
        f"**Scenarios:** {len(results)} × 6 rounds",
        "",
    ]

    for sc in results:
        lines.append(f"---\n## {sc['name']}\n")
        lines.append(f"_{sc['description']}_\n")

        # GDP table
        lines.append("### GDP Trajectories\n")
        header_countries = ["columbia", "cathay", "sarmatia", "ruthenia", "persia", "teutonia", "bharata", "formosa"]
        header = "| Round | Oil$ | " + " | ".join(c.title()[:6] for c in header_countries) + " |"
        sep = "|-------|------|" + "|".join(["------"] * len(header_countries)) + "|"
        lines.append(header)
        lines.append(sep)

        for label, snap, oil, mkt, *rest in sc["snapshots"]:
            row = f"| {label} | ${oil:.0f} |"
            for cid in header_countries:
                if cid in snap:
                    gdp = snap[cid]["gdp"]
                    growth = snap[cid]["growth"]
                    row += f" {gdp:.0f} ({growth:+.1f}%) |"
                else:
                    row += " — |"
            lines.append(row)

        # Stability + Support table
        lines.append("\n### Stability & Support\n")
        header = "| Round | " + " | ".join(f"{c.title()[:6]} S/Sup" for c in header_countries[:6]) + " |"
        sep = "|-------|" + "|".join(["----------"] * 6) + "|"
        lines.append(header)
        lines.append(sep)

        for label, snap, oil, *rest in sc["snapshots"]:
            row = f"| {label} |"
            for cid in header_countries[:6]:
                if cid in snap:
                    s = snap[cid]["stability"]
                    sup = snap[cid]["support"]
                    row += f" {s:.1f}/{sup:.0f}% |"
                else:
                    row += " —/—% |"
            lines.append(row)

        # Market Indexes (last round)
        last_mkt = None
        for entry in sc["snapshots"]:
            if len(entry) > 3 and entry[3]:
                last_mkt = entry[3]
        if last_mkt:
            lines.append(f"\n**Market Indexes (R6):** Wall Street={last_mkt['wall_street']:.0f}, "
                         f"Europa={last_mkt['europa']:.0f}, Dragon={last_mkt['dragon']:.0f}")

        # Sanctions/Tariff coefficients (last round)
        last_snap = sc["snapshots"][-1][1]
        coeff_notes = []
        for cid in header_countries:
            if cid in last_snap:
                sc_coeff = last_snap[cid]["sanctions_coeff"]
                tc_coeff = last_snap[cid]["tariff_coeff"]
                if sc_coeff < 0.99 or tc_coeff < 0.99:
                    coeff_notes.append(f"{cid.title()}: sanctions={sc_coeff:.3f}, tariffs={tc_coeff:.3f}")
        if coeff_notes:
            lines.append(f"\n**Coefficients (R6):** " + " | ".join(coeff_notes))

        # Revolutions
        all_revs = {}
        for entry in sc["snapshots"]:
            if len(entry) > 4 and entry[4]:
                all_revs.update(entry[4])
        if all_revs:
            lines.append(f"\n**Revolutions:** " + ", ".join(f"{k}: {v}" for k, v in all_revs.items()))

        lines.append("")

    # CROSS-SCENARIO ANALYSIS
    lines.append("---\n## Cross-Scenario Analysis\n")

    # Compare final GDPs
    lines.append("### Final GDP Comparison (R6)\n")
    header = "| Country | " + " | ".join(r["name"].split(":")[0] for r in results) + " |"
    sep = "|---------|" + "|".join(["------"] * len(results)) + "|"
    lines.append(header)
    lines.append(sep)

    for cid in ["columbia", "cathay", "sarmatia", "ruthenia", "persia"]:
        row = f"| {cid.title()} |"
        for r in results:
            snap = r["snapshots"][-1][1]
            if cid in snap:
                row += f" {snap[cid]['gdp']:.0f} |"
            else:
                row += " — |"
        lines.append(row)

    # Convergence criteria
    lines.append("\n### Convergence Criteria\n")
    lines.append("| Criterion | Target | " + " | ".join(r["name"].split(":")[0] for r in results) + " |")
    lines.append("|-----------|--------|" + "|".join(["------"] * len(results)) + "|")

    criteria = [
        ("No country GDP < 50% of start by R4", lambda snaps: all(
            snaps[min(4, len(snaps)-1)][1].get(c, {}).get("gdp", 999) >= snaps[0][1].get(c, {}).get("gdp", 1) * 0.5
            for c in FOCUS_COUNTRIES if c in snaps[0][1]
        )),
        ("Columbia GDP > 200 at R6", lambda snaps: snaps[-1][1].get("columbia", {}).get("gdp", 0) > 200),
        ("Cathay GDP > 150 at R6", lambda snaps: snaps[-1][1].get("cathay", {}).get("gdp", 0) > 150),
        ("No stability < 2.0 (baseline)", lambda snaps: all(
            snaps[-1][1].get(c, {}).get("stability", 9) >= 2.0
            for c in FOCUS_COUNTRIES if c in snaps[-1][1]
        )),
        ("Oil $30-$200 range", lambda snaps: all(30 <= s[2] <= 200 for s in snaps[1:])),
        ("Sarmatia GDP declining under sanctions", lambda snaps: (
            snaps[-1][1].get("sarmatia", {}).get("gdp", 999) <
            snaps[0][1].get("sarmatia", {}).get("gdp", 0)
        )),
    ]

    for name, check in criteria:
        row = f"| {name} |  |"
        for r in results:
            try:
                passed = check(r["snapshots"])
                row += f" {'PASS' if passed else 'FAIL'} |"
            except Exception:
                row += " ERR |"
        lines.append(row)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Loading countries from CSV...")
    print(f"CSV path: {CSV_PATH}")
    print(f"Countries loaded: {len(load_countries_from_csv())}")
    print()

    results = []
    for i, sc_fn in enumerate(SCENARIOS):
        sc = sc_fn()
        print(f"Running {sc['name']}...")
        result = run_scenario(sc_fn)
        results.append(result)
        # Quick summary
        last = result["snapshots"][-1][1]
        print(f"  Oil: ${result['snapshots'][-1][2]:.0f}")
        print(f"  Columbia GDP: {last.get('columbia', {}).get('gdp', '?')}")
        print(f"  Cathay GDP:   {last.get('cathay', {}).get('gdp', '?')}")
        print(f"  Sarmatia GDP: {last.get('sarmatia', {}).get('gdp', '?')}")
        print()

    # Generate report
    report = format_report(results)

    # Save
    out_dir = os.path.join(
        os.path.dirname(__file__), "..", "..", "..",
        "10. TESTS", "BUILD TEST", "run_009",
    )
    os.makedirs(out_dir, exist_ok=True)
    report_path = os.path.join(out_dir, "RESULTS.md")
    with open(report_path, "w") as f:
        f.write(report)

    print(f"Report saved: {report_path}")
    print("\n" + "=" * 60)
    print(report)
