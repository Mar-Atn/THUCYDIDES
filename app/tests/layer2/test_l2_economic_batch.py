"""Level 2 — Economic Batch Actions (Phase B).

Tests set_budget, set_tariffs, set_sanctions, set_opec through ToolExecutor
during Phase B. Verifies batch actions are queued correctly and rejected
during Phase A.

Run:
    cd "/Users/marat/4. METAGAMES/1. NEW SIMs/THUCYDIDES" && PYTHONPATH=app .venv/bin/python -m pytest app/tests/layer2/test_l2_economic_batch.py -v -s
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
COUNTRY_CODE = "phrygia"
ROLE_ID = "vizier"
SCENARIO_CODE = "ttt_v1"


@pytest.fixture(scope="module")
def client():
    from engine.services.supabase import get_client
    return get_client()


@pytest.fixture(scope="module")
def executor():
    from engine.agents.managed.tool_executor import ToolExecutor
    return ToolExecutor(
        country_code=COUNTRY_CODE,
        scenario_code=SCENARIO_CODE,
        sim_run_id=SIM_RUN_ID,
        round_num=1,
        role_id=ROLE_ID,
    )


@pytest.fixture(scope="module")
def solaria_executor():
    """Executor for Solaria (OPEC member via the_cartel)."""
    from engine.agents.managed.tool_executor import ToolExecutor
    return ToolExecutor(
        country_code="solaria",
        scenario_code=SCENARIO_CODE,
        sim_run_id=SIM_RUN_ID,
        round_num=1,
        role_id="wellspring",
    )


@pytest.fixture(scope="module")
def original_state(client):
    """Capture sim state before module runs."""
    run = client.table("sim_runs").select("status,current_phase,current_round").eq("id", SIM_RUN_ID).limit(1).execute()
    if not run.data:
        pytest.skip(f"SimRun {SIM_RUN_ID} not found")
    return run.data[0]


@pytest.fixture(scope="module")
def phase_b_context(client, original_state):
    """Transition sim to Phase B for batch action testing, restore after."""
    status = original_state["status"]
    phase = original_state["current_phase"]

    # Ensure we're in active Phase A first
    if status == "pre_start":
        from engine.services.sim_run_manager import start_simulation
        start_simulation(SIM_RUN_ID)
    elif status in ("setup",):
        from engine.services.sim_run_manager import start_pre_start, start_simulation
        start_pre_start(SIM_RUN_ID)
        start_simulation(SIM_RUN_ID)
    elif status in ("completed", "aborted"):
        pytest.skip(f"SimRun status={status}")

    # Now transition to Phase B
    from engine.services.sim_run_manager import end_phase_a
    try:
        end_phase_a(SIM_RUN_ID)
        logger.info("Transitioned to Phase B for batch testing")
    except ValueError as e:
        # Already in Phase B or inter_round — check
        run = client.table("sim_runs").select("current_phase").eq("id", SIM_RUN_ID).limit(1).execute()
        if run.data and run.data[0]["current_phase"] == "B":
            logger.info("Already in Phase B")
        else:
            raise

    yield

    # Restore: go back to Phase A
    from engine.services.sim_run_manager import go_back_to_phase_a
    try:
        go_back_to_phase_a(SIM_RUN_ID)
        logger.info("Restored to Phase A after batch testing")
    except Exception as e:
        logger.warning("Failed to restore Phase A: %s — manually fixing", e)
        from datetime import datetime, timezone
        client.table("sim_runs").update({
            "status": "active",
            "current_phase": "A",
            "phase_started_at": datetime.now(timezone.utc).isoformat(),
            "phase_duration_seconds": 3600,
        }).eq("id", SIM_RUN_ID).execute()


# ---------------------------------------------------------------------------
# Economic Batch in Phase B
# ---------------------------------------------------------------------------

class TestEconomicBatchPhaseB:
    """Submit batch actions during Phase B — should succeed."""

    def test_set_budget_in_phase_b(self, phase_b_context, executor):
        result = json.loads(executor.execute("submit_action", {
            "action": {
                "action_type": "set_budget",
                "social_pct": 1.2,
                "military_coins": 5.0,
                "tech_coins": 3.0,
                "rationale": "L2 batch test budget",
            }
        }))
        logger.info("set_budget Phase B: %s", result)
        assert result.get("success") is True, f"set_budget failed in Phase B: {result}"

    def test_set_tariffs_in_phase_b(self, phase_b_context, executor):
        result = json.loads(executor.execute("submit_action", {
            "action": {
                "action_type": "set_tariffs",
                "target_country": "solaria",
                "level": 2,
                "rationale": "L2 batch test tariffs",
            }
        }))
        logger.info("set_tariffs Phase B: %s", result)
        assert result.get("success") is True, f"set_tariffs failed in Phase B: {result}"

    def test_set_sanctions_in_phase_b(self, phase_b_context, executor):
        result = json.loads(executor.execute("submit_action", {
            "action": {
                "action_type": "set_sanctions",
                "target_country": "solaria",
                "sanction_type": "oil_export_ban",
                "level": 2,
                "rationale": "L2 batch test sanctions",
            }
        }))
        logger.info("set_sanctions Phase B: %s", result)
        assert result.get("success") is True, f"set_sanctions failed in Phase B: {result}"

    def test_set_opec_member_in_phase_b(self, phase_b_context, solaria_executor):
        """Solaria is an OPEC/cartel member — set_opec should succeed."""
        result = json.loads(solaria_executor.execute("submit_action", {
            "action": {
                "action_type": "set_opec",
                "production": "low",
                "rationale": "L2 batch test OPEC member",
            }
        }))
        logger.info("set_opec (Solaria/member) Phase B: %s", result)
        assert result.get("success") is True, f"set_opec failed for OPEC member: {result}"

    def test_set_opec_non_member_in_phase_b(self, phase_b_context, executor):
        """Phrygia is NOT an OPEC/cartel member — set_opec queues anyway (engine handles eligibility)."""
        result = json.loads(executor.execute("submit_action", {
            "action": {
                "action_type": "set_opec",
                "production": "normal",
                "rationale": "L2 batch test OPEC non-member",
            }
        }))
        logger.info("set_opec (Phrygia/non-member) Phase B: %s", result)
        # Should queue without error — engine handles eligibility during processing
        assert result.get("success") is True, f"set_opec should queue for non-member: {result}"

    def test_batch_decision_stored_in_agent_decisions(self, phase_b_context, executor, client):
        """Verify batch decisions are stored in agent_decisions table."""
        # Submit a budget to verify storage
        json.loads(executor.execute("submit_action", {
            "action": {
                "action_type": "set_budget",
                "social_pct": 1.0,
                "military_coins": 2.0,
                "tech_coins": 1.0,
                "rationale": "L2 storage verification",
            }
        }))
        # Check agent_decisions table
        rows = client.table("agent_decisions").select("id,action_type,validation_status") \
            .eq("sim_run_id", SIM_RUN_ID) \
            .eq("country_code", COUNTRY_CODE) \
            .eq("action_type", "set_budget") \
            .eq("round_num", 1) \
            .order("created_at", desc=True) \
            .limit(1).execute().data
        assert rows, "No agent_decisions row found for set_budget"
        logger.info("agent_decisions row: %s", rows[0])


# ---------------------------------------------------------------------------
# Phase A Rejection (confirm batch still blocked)
# ---------------------------------------------------------------------------

class TestBatchRejectedInPhaseA:
    """Verify batch actions are blocked during Phase A (no Phase B fixture)."""

    @pytest.fixture(autouse=True)
    def ensure_phase_a(self, client):
        """Make sure we're back in Phase A."""
        run = client.table("sim_runs").select("status,current_phase").eq("id", SIM_RUN_ID).limit(1).execute()
        if run.data and run.data[0].get("current_phase") != "A":
            from engine.services.sim_run_manager import go_back_to_phase_a
            try:
                go_back_to_phase_a(SIM_RUN_ID)
            except Exception:
                from datetime import datetime, timezone
                client.table("sim_runs").update({
                    "status": "active",
                    "current_phase": "A",
                    "phase_started_at": datetime.now(timezone.utc).isoformat(),
                }).eq("id", SIM_RUN_ID).execute()

    def test_set_budget_rejected_in_phase_a(self, executor):
        result = json.loads(executor.execute("submit_action", {
            "action": {
                "action_type": "set_budget",
                "social_pct": 1.0,
                "military_coins": 5.0,
                "tech_coins": 3.0,
                "rationale": "Should be rejected in Phase A",
            }
        }))
        assert result.get("success") is False
        assert "Phase B" in str(result.get("validation_notes", ""))

    def test_set_tariffs_rejected_in_phase_a(self, executor):
        result = json.loads(executor.execute("submit_action", {
            "action": {
                "action_type": "set_tariffs",
                "target_country": "solaria",
                "level": 1,
                "rationale": "Should be rejected in Phase A",
            }
        }))
        assert result.get("success") is False

    def test_move_units_rejected_in_phase_a(self, executor):
        result = json.loads(executor.execute("submit_action", {
            "action": {
                "action_type": "move_units",
                "decision": "no_change",
                "rationale": "Should be rejected in Phase A",
            }
        }))
        assert result.get("success") is False
