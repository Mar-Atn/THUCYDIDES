#!/usr/bin/env python3
"""
TTT SEED — Main Test Runner
=============================
Runs the complete 3-engine system with AI agents for the SEED-level simulation.

Usage:
    python run_seed_test.py                    # runs test_1_generic
    python run_seed_test.py test_2_aggressive_nordostan
    python run_seed_test.py all                # runs all tests

Author: ATLAS (World Model Engineer)
Version: 2.0 (SEED)
"""

import sys
import os
import random
import json
import time

# Ensure engine modules are importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from world_state import WorldState
from transaction_engine import TransactionEngine
from live_action_engine import LiveActionEngine
from world_model_engine import WorldModelEngine
from ai_agent import load_agents_from_seeds
from test_orchestrator import TestOrchestrator


# ---------------------------------------------------------------------------
# TEST CONFIGURATIONS
# ---------------------------------------------------------------------------

TESTS = {
    "test_1_generic": {
        "rounds": 8,
        "seed": 100,
        "name": "Full Generic Run",
        "description": "Baseline simulation with all agents at default settings.",
        "overrides": {},
    },
    "test_2_aggressive_nordostan": {
        "rounds": 8,
        "seed": 200,
        "name": "Aggressive Nordostan",
        "description": "Pathfinder pushes for military victory, Ironhand follows.",
        "overrides": {
            "pathfinder": {"aggression": 0.9, "risk_tolerance": 0.8, "deal_seeking": 0.3},
            "ironhand": {"aggression": 0.6, "resentment": 0.3},
        },
    },
    "test_3_formosa_crisis": {
        "rounds": 8,
        "seed": 300,
        "name": "Cathay Formosa Push",
        "description": "Helmsman pushes for Formosa resolution with high urgency.",
        "overrides": {
            "helmsman": {"aggression": 0.7, "formosa_urgency": 0.9, "risk_tolerance": 0.6},
            "rampart": {"caution_level": 0.4, "slow_walk_probability": 0.1},
        },
    },
    "test_4_oil_cartel": {
        "rounds": 8,
        "seed": 400,
        "name": "Oil Cartel Stress",
        "description": "OPEC+ coordination breaks down. Oil price volatility test.",
        "overrides": {
            "wellspring": {"aggression": 0.5, "deal_seeking": 0.4},
        },
    },
    "test_5_columbia_politics": {
        "rounds": 8,
        "seed": 500,
        "name": "Columbia Internal",
        "description": "Aggressive opposition, political turmoil in Columbia.",
        "overrides": {
            "tribune": {"aggression": 0.8},
            "challenger": {"aggression": 0.7, "deal_seeking": 0.8},
            "dealer": {"risk_tolerance": 0.7, "aggression": 0.7},
        },
    },
    "test_6_alliance_cohesion": {
        "rounds": 8,
        "seed": 600,
        "name": "NATO Fracture Test",
        "description": "European allies drift apart. Ponte and Lumiere pursue independent agendas.",
        "overrides": {
            "ponte_role": {"deal_seeking": 0.9, "aggression": 0.1},
            "lumiere": {"deal_seeking": 0.8, "aggression": 0.5},
            "sentinel": {"aggression": 0.7},
            "forge": {"deal_seeking": 0.9, "aggression": 0.1},
        },
    },
    "test_7_gulf_gate_escalation": {
        "rounds": 8,
        "seed": 700,
        "name": "Gulf Gate Escalation",
        "description": "Persia maintains ground blockade of Gulf Gate. Oil crisis test.",
        "overrides": {
            "anvil": {"gulf_gate_leverage": 1.0, "aggression": 0.6},
            "furnace": {"aggression": 0.7, "risk_tolerance": 0.6},
        },
    },
    "test_8_peace_scenario": {
        "rounds": 8,
        "seed": 800,
        "name": "Maximum Deal-Seeking",
        "description": "All major leaders push for deals. Can diplomacy avert escalation?",
        "overrides": {
            "dealer": {"deal_seeking": 1.0, "aggression": 0.2},
            "pathfinder": {"deal_seeking": 0.9, "aggression": 0.3},
            "helmsman": {"deal_seeking": 0.6, "aggression": 0.3},
            "beacon": {"deal_seeking": 0.7},
            "anvil": {"deal_seeking": 0.8},
        },
    },
}


# ---------------------------------------------------------------------------
# MAIN RUNNER
# ---------------------------------------------------------------------------

def run_test(test_config: dict, output_dir: str) -> dict:
    """Run a single test configuration."""

    # Set random seed for reproducibility
    seed = test_config.get("seed", 42)
    random.seed(seed)

    print(f"\nInitializing test: {test_config['name']}")
    print(f"  Seed: {seed}")
    print(f"  Output: {output_dir}")

    # Determine data directory
    engine_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(engine_dir, "..", "data")
    data_dir = os.path.normpath(data_dir)

    if not os.path.exists(data_dir):
        print(f"ERROR: Data directory not found: {data_dir}")
        sys.exit(1)

    # Load world state from CSVs
    print("  Loading world state from CSVs...")
    world_state = WorldState()
    world_state.load_from_csvs(data_dir)
    print(f"    Loaded {len(world_state.countries)} countries, "
          f"{len(world_state.zones)} zones, "
          f"{len(world_state.roles)} roles, "
          f"{len(world_state.wars)} active wars")

    # Initialize engines
    print("  Initializing engines...")
    engines = {
        "transaction": TransactionEngine(world_state),
        "live_action": LiveActionEngine(world_state),
        "world_model": WorldModelEngine(world_state),
    }

    # Initialize AI agents from role seeds with test overrides
    print("  Loading AI agents from role seeds...")
    overrides = test_config.get("overrides", {})
    agents = load_agents_from_seeds(world_state, overrides)
    print(f"    Loaded {len(agents)} agents")

    # Count by type
    team_agents = sum(1 for a in agents.values()
                      if world_state.countries.get(a.country_id, {}).get("team_type") == "team")
    solo_agents = len(agents) - team_agents
    print(f"    Team roles: {team_agents}, Solo roles: {solo_agents}")

    # Create orchestrator
    test_config["output_dir"] = output_dir
    orchestrator = TestOrchestrator(world_state, engines, agents, test_config)

    # Run simulation
    rounds = test_config.get("rounds", 8)
    report = orchestrator.run_simulation(num_rounds=rounds)

    return report


def run_all_tests() -> None:
    """Run all test configurations."""
    results = {}
    for test_name, config in TESTS.items():
        output_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "test_results", test_name
        )
        try:
            report = run_test(config, output_dir)
            results[test_name] = {
                "status": "completed",
                "rounds": report.get("rounds_played", 0),
                "time": report.get("total_time_seconds", 0),
                "nuclear": report.get("nuclear_used", False),
            }
            print(f"\n  {test_name}: COMPLETED "
                  f"({report['rounds_played']} rounds, "
                  f"{report['total_time_seconds']:.1f}s)")
        except Exception as e:
            results[test_name] = {"status": "failed", "error": str(e)}
            print(f"\n  {test_name}: FAILED - {e}")
            import traceback
            traceback.print_exc()

    # Summary
    print(f"\n{'='*60}")
    print("  ALL TESTS SUMMARY")
    print(f"{'='*60}")
    for name, r in results.items():
        status = r["status"]
        if status == "completed":
            print(f"  {name:40s} OK  ({r['rounds']}R, {r['time']:.1f}s"
                  f"{', NUCLEAR' if r.get('nuclear') else ''})")
        else:
            print(f"  {name:40s} FAIL ({r.get('error', '?')})")

    # Save summary
    summary_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "test_results", "all_tests_summary.json"
    )
    os.makedirs(os.path.dirname(summary_path), exist_ok=True)
    with open(summary_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n  Summary saved to: {summary_path}")


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_name = sys.argv[1]

        if test_name == "all":
            run_all_tests()
        elif test_name in TESTS:
            output_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "test_results", test_name
            )
            run_test(TESTS[test_name], output_dir)
        else:
            print(f"Unknown test: {test_name}")
            print(f"Available tests: {', '.join(TESTS.keys())}")
            print(f"Or use 'all' to run all tests.")
            sys.exit(1)
    else:
        # Default: run generic test
        output_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "test_results", "test_1_generic"
        )
        run_test(TESTS["test_1_generic"], output_dir)
