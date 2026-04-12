"""Test helpers for F1 sim_run lifecycle.

Every per-round DB row is now keyed by ``sim_run_id`` (NOT NULL). Tests
that insert directly into ``agent_decisions``, ``country_states_per_round``,
``unit_states_per_round``, ``global_state_per_round``, ``observatory_events``,
etc. MUST provide a sim_run_id or the insert will fail the NOT NULL
constraint.

Two canonical ways to get one:

1. ``legacy_run_id(scenario_code)`` — returns the archived "legacy" run
   for the given scenario. Every pre-F1 snapshot row lives under this
   run. Use this when you want the existing test data as-is (fast).

2. ``create_isolated_run(scenario_code, test_name)`` — creates a fresh
   sim_run and seeds its R0 from the legacy template. Use this when the
   test mutates per-round state and needs isolation from other tests.
   Returns (sim_run_id, cleanup_callable).

See PHASES/UNMANNED_SPACECRAFT/PLAN_F1_SIM_RUNS.md for the full story.
"""

from __future__ import annotations

from typing import Callable

from engine.services.sim_run_manager import (
    create_run,
    resolve_sim_run_id,
    seed_round_zero,
)
from engine.services.supabase import get_client


def legacy_run_id(scenario_code: str = "start_one") -> str:
    """Return the archived legacy run id for the given scenario.

    This is the bucket where every pre-F1 per-round row landed during
    the ``sim_run_foundation_v1`` migration. Use when a test just needs
    SOME sim_run_id to satisfy NOT NULL on direct inserts.
    """
    return resolve_sim_run_id(scenario_code)


def create_isolated_run(
    scenario_code: str = "start_one",
    test_name: str = "unnamed",
    seed_r0: bool = True,
) -> tuple[str, Callable[[], None]]:
    """Create a fresh sim_run seeded from scenario template R0.

    Returns ``(sim_run_id, cleanup)``. Call ``cleanup()`` at test teardown
    (or register it as a pytest fixture finalizer) to cascade-delete all
    per-round rows that belong to the run.
    """
    sim_run_id = create_run(
        scenario_code=scenario_code,
        name=f"test_{test_name}",
        description=f"F1 isolated test run: {test_name}",
    )
    if seed_r0:
        seed_round_zero(sim_run_id)

    def _cleanup() -> None:
        try:
            get_client().table("sim_runs").delete().eq("id", sim_run_id).execute()
        except Exception:
            pass

    return sim_run_id, _cleanup
