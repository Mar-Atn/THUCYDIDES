"""Phase 4+5 Test: Multi-agent execution with optional conversations.

Runs 3 agents (Dealer, Helmsman, Pathfinder) through 1 round with 3
pulses. Agents explore game state, submit actions, and may request
meetings. The orchestrator processes accepted meetings between pulses.

Usage:
    cd /Users/marat/4. METAGAMES/1. NEW SIMs/THUCYDIDES/app
    python -m engine.agents.managed.test_multi_agent

Requires:
    - ANTHROPIC_API_KEY in environment
    - Supabase DB with a valid sim_run containing the test roles
    - Roles: dealer, helmsman, pathfinder (or matching role IDs)

Configuration:
    - SIM_ID: Set to a valid sim_run UUID from your DB
    - ROLE_IDS: The role IDs to initialize (must exist in the roles table)
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import time

# Ensure engine package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from engine.agents.managed.orchestrator import AIOrchestrator, OrchestratorConfig

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)-30s %(levelname)-7s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────
# Set SIM_ID to your test sim_run UUID. The roles must exist in the
# roles table for this sim_run.
SIM_ID = os.environ.get(
    "TTT_TEST_SIM_ID",
    "00000000-0000-0000-0000-000000000000",  # placeholder — set your own
)

ROLE_IDS = ["dealer", "helmsman", "pathfinder"]


async def test_multi_agent() -> dict:
    """Run 3 agents through 1 round with 3 pulses.

    Returns:
        Round summary dict with per-agent stats, costs, and meeting results.
    """
    config = OrchestratorConfig(
        pulses_per_round=3,
        model="claude-sonnet-4-6",
        auto_advance=True,
        round_duration_seconds=90,
        assertiveness=6,
        max_turns_per_meeting=8,
        total_rounds=6,
    )

    logger.info("=" * 60)
    logger.info("MULTI-AGENT TEST: %d agents, %d pulses", len(ROLE_IDS), config.pulses_per_round)
    logger.info("SIM_ID: %s", SIM_ID)
    logger.info("Model: %s", config.model)
    logger.info("=" * 60)

    orch = AIOrchestrator(SIM_ID, config)

    # Phase 1: Initialize agents
    logger.info("\n--- PHASE 1: Initializing agents ---")
    start = time.time()
    init_result = await orch.initialize_agents(role_ids=ROLE_IDS)
    init_elapsed = time.time() - start

    logger.info(
        "Initialized %d agents in %.1fs",
        init_result.get("agents_initialized", 0),
        init_elapsed,
    )

    if init_result.get("errors"):
        for err in init_result["errors"]:
            logger.error("Init error: %s", err)

    if init_result.get("agents_initialized", 0) == 0:
        logger.error("No agents initialized — aborting test.")
        return init_result

    # Phase 2: Run round 1
    logger.info("\n--- PHASE 2: Running round 1 ---")
    start = time.time()
    result = await orch.run_round(round_num=1)
    round_elapsed = time.time() - start

    logger.info("Round 1 complete in %.1fs", round_elapsed)

    # Phase 3: Status check
    logger.info("\n--- PHASE 3: Status check ---")
    status = orch.get_status()

    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("ROUND SUMMARY")
    logger.info("=" * 60)
    logger.info("Total actions: %d", result.get("total_actions", 0))
    logger.info("Total meetings: %d", result.get("total_meetings", 0))
    logger.info("Total errors: %d", result.get("total_errors", 0))
    logger.info("Total cost: $%.2f", result.get("total_cost_usd", 0))

    for role_id, agent_stats in result.get("agents", {}).items():
        logger.info(
            "  %s: %d actions, %d tools, %d meetings, %d errors, $%.2f",
            role_id,
            agent_stats.get("actions", 0),
            agent_stats.get("tool_calls", 0),
            agent_stats.get("meetings_used", 0),
            agent_stats.get("errors", 0),
            agent_stats.get("cost_usd", 0),
        )

    logger.info("\nAgent states: %s", {
        r: s for r, s in orch.agent_states.items()
    })

    # Phase 4: Shutdown
    logger.info("\n--- PHASE 4: Shutdown ---")
    await orch.shutdown()
    logger.info("Orchestrator shut down cleanly.")

    # Full result dump
    full_result = {
        "init": init_result,
        "round_summary": result,
        "status_at_end": status,
        "timing": {
            "init_seconds": round(init_elapsed, 1),
            "round_seconds": round(round_elapsed, 1),
        },
    }

    print("\n--- FULL RESULT (JSON) ---")
    print(json.dumps(full_result, indent=2, default=str))

    return full_result


if __name__ == "__main__":
    asyncio.run(test_multi_agent())
