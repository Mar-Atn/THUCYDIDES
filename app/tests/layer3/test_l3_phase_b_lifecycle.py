"""Level 3 — Phase B Full Lifecycle Test.

Tests the complete round lifecycle: Phase A actions -> end Phase A -> Phase B batch ->
end Phase B -> inter_round -> advance to Round 2 -> Round 2 actions.

IMPORTANT: This test modifies sim state (advances rounds). Other tests must account
for the sim potentially being in Round 2 after this runs.

Run:
    cd "/Users/marat/4. METAGAMES/1. NEW SIMs/THUCYDIDES" && PYTHONPATH=app .venv/bin/python -m pytest app/tests/layer3/test_l3_phase_b_lifecycle.py -v -s
"""
import json
import logging
import os
import pytest
from pathlib import Path

logger = logging.getLogger(__name__)

_env_path = Path(__file__).resolve().parents[2] / "engine" / ".env"
if _env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(_env_path)

SIM_RUN_ID = os.environ.get("TEST_SIM_RUN_ID", "c954b9b6-35f0-4973-a08b-f38406c524e7")
SCENARIO_CODE = "ttt_v1"


@pytest.fixture(scope="module")
def client():
    from engine.services.supabase import get_client
    return get_client()


@pytest.fixture(scope="module")
def phrygia_executor():
    from engine.agents.managed.tool_executor import ToolExecutor
    return ToolExecutor(
        country_code="phrygia",
        scenario_code=SCENARIO_CODE,
        sim_run_id=SIM_RUN_ID,
        round_num=1,
        role_id="vizier",
    )


@pytest.fixture(scope="module")
def solaria_executor():
    from engine.agents.managed.tool_executor import ToolExecutor
    return ToolExecutor(
        country_code="solaria",
        scenario_code=SCENARIO_CODE,
        sim_run_id=SIM_RUN_ID,
        round_num=1,
        role_id="wellspring",
    )


def _get_sim_state(client):
    """Helper to read current sim state."""
    run = client.table("sim_runs").select("status,current_phase,current_round").eq("id", SIM_RUN_ID).limit(1).execute()
    return run.data[0] if run.data else {}


@pytest.fixture(scope="module", autouse=True)
def ensure_round_1_phase_a(client):
    """Start from Round 1 Phase A. Restore after all tests."""
    state = _get_sim_state(client)
    if not state:
        pytest.skip(f"SimRun {SIM_RUN_ID} not found")

    status = state["status"]
    if status in ("completed", "aborted"):
        pytest.skip(f"SimRun status={status}")

    # Get to active Phase A Round 1
    if status == "pre_start":
        from engine.services.sim_run_manager import start_simulation
        start_simulation(SIM_RUN_ID)
    elif status == "setup":
        from engine.services.sim_run_manager import start_pre_start, start_simulation
        start_pre_start(SIM_RUN_ID)
        start_simulation(SIM_RUN_ID)
    elif state.get("current_phase") != "A":
        from engine.services.sim_run_manager import go_back_to_phase_a
        try:
            go_back_to_phase_a(SIM_RUN_ID)
        except Exception:
            from datetime import datetime, timezone
            client.table("sim_runs").update({
                "status": "active",
                "current_phase": "A",
                "current_round": 1,
                "phase_started_at": datetime.now(timezone.utc).isoformat(),
            }).eq("id", SIM_RUN_ID).execute()

    yield

    # Restore to Round 1 Phase A after all lifecycle tests
    from datetime import datetime, timezone
    client.table("sim_runs").update({
        "status": "active",
        "current_phase": "A",
        "current_round": 1,
        "phase_started_at": datetime.now(timezone.utc).isoformat(),
        "phase_duration_seconds": 3600,
    }).eq("id", SIM_RUN_ID).execute()
    logger.info("Restored sim to Round 1 Phase A")


# ---------------------------------------------------------------------------
# Ordered lifecycle steps (must run in order)
# ---------------------------------------------------------------------------

class TestPhaseLifecycle:
    """Full round lifecycle — tests run in definition order."""

    def test_step_1_verify_phase_a(self, client):
        """Verify sim starts in active Phase A Round 1."""
        state = _get_sim_state(client)
        assert state["status"] == "active", f"Expected active, got {state['status']}"
        assert state["current_phase"] == "A", f"Expected Phase A, got {state['current_phase']}"
        assert state["current_round"] == 1, f"Expected Round 1, got {state['current_round']}"
        logger.info("Step 1: Confirmed Phase A Round 1")

    def test_step_2_phase_a_action(self, phrygia_executor):
        """Submit a Phase A action (public_statement)."""
        result = json.loads(phrygia_executor.execute("submit_action", {
            "action": {
                "action_type": "public_statement",
                "content": "Phrygia announces lifecycle test round 1",
                "rationale": "L3 lifecycle Phase A action",
            }
        }))
        assert result.get("success") is True, f"Phase A action failed: {result}"
        logger.info("Step 2: Phase A action submitted")

    def test_step_3_end_phase_a(self, client):
        """End Phase A -> Phase B (processing)."""
        from engine.services.sim_run_manager import end_phase_a
        result = end_phase_a(SIM_RUN_ID)
        assert result["status"] == "processing"
        assert result["current_phase"] == "B"
        logger.info("Step 3: Phase A ended, now in Phase B")

    def test_step_4_submit_batch_in_phase_b(self, phrygia_executor, solaria_executor, client):
        """Submit batch actions during Phase B."""
        # Phrygia budget
        r1 = json.loads(phrygia_executor.execute("submit_action", {
            "action": {
                "action_type": "set_budget",
                "social_pct": 1.1,
                "military_coins": 4.0,
                "tech_coins": 2.0,
                "rationale": "L3 lifecycle Phrygia budget",
            }
        }))
        assert r1.get("success") is True, f"Phrygia budget failed: {r1}"

        # Solaria budget
        r2 = json.loads(solaria_executor.execute("submit_action", {
            "action": {
                "action_type": "set_budget",
                "social_pct": 0.9,
                "military_coins": 3.0,
                "tech_coins": 5.0,
                "rationale": "L3 lifecycle Solaria budget",
            }
        }))
        assert r2.get("success") is True, f"Solaria budget failed: {r2}"
        logger.info("Step 4: Batch actions submitted in Phase B")

    def test_step_5_end_phase_b(self, client):
        """End Phase B -> inter_round."""
        from engine.services.sim_run_manager import end_phase_b
        result = end_phase_b(SIM_RUN_ID)
        assert result["status"] == "inter_round"
        assert result["current_phase"] == "inter_round"
        logger.info("Step 5: Phase B ended, now in inter_round")

    def test_step_6_advance_round(self, client):
        """Advance from inter_round to Round 2 Phase A."""
        from engine.services.sim_run_manager import advance_round
        result = advance_round(SIM_RUN_ID)
        assert result["status"] == "active"
        assert result["current_phase"] == "A"
        assert result["current_round"] == 2
        logger.info("Step 6: Advanced to Round 2 Phase A")

    def test_step_7_round_2_action(self, client):
        """Submit an action in Round 2 to verify it works."""
        from engine.agents.managed.tool_executor import ToolExecutor
        executor_r2 = ToolExecutor(
            country_code="phrygia",
            scenario_code=SCENARIO_CODE,
            sim_run_id=SIM_RUN_ID,
            round_num=2,
            role_id="vizier",
        )
        result = json.loads(executor_r2.execute("submit_action", {
            "action": {
                "action_type": "public_statement",
                "content": "Phrygia announces round 2 is live!",
                "rationale": "L3 lifecycle Round 2 verification",
            }
        }))
        assert result.get("success") is True, f"Round 2 action failed: {result}"
        logger.info("Step 7: Round 2 action verified")
