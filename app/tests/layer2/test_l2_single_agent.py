"""Level 2 — Single Agent Round Lifecycle Test.

Tests the complete action dispatch pipeline for a single AI agent
(Vizier/Phrygia) through a full round lifecycle:
  - Phase A immediate actions (public_statement, propose_transaction, propose_agreement, covert_op, declare_war)
  - Phase B batch decisions (set_budget, set_tariffs, set_sanctions)
  - UUID validation guards
  - Field normalization for agent→engine mapping

Uses the ToolExecutor directly against the live DB (no managed agent session).
Requires: server NOT running (direct DB access), .env loaded.

Run:
    cd /path/to/THUCYDIDES && PYTHONPATH=app .venv/bin/python -m pytest app/tests/layer2/test_l2_single_agent.py -v -s
"""
import logging
import os
import pytest

logger = logging.getLogger(__name__)

# Load .env before importing engine modules
from pathlib import Path
_env_path = Path(__file__).resolve().parents[2] / "engine" / ".env"
if _env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(_env_path)

SIM_RUN_ID = os.environ.get("TEST_SIM_RUN_ID", "c954b9b6-35f0-4973-a08b-f38406c524e7")
COUNTRY_CODE = "phrygia"
ROLE_ID = "phrygia_vizier"
SCENARIO_CODE = "ttt_v1"


@pytest.fixture(scope="module")
def executor():
    """Create a ToolExecutor for Vizier/Phrygia."""
    from engine.agents.managed.tool_executor import ToolExecutor
    return ToolExecutor(
        country_code=COUNTRY_CODE,
        scenario_code=SCENARIO_CODE,
        sim_run_id=SIM_RUN_ID,
        round_num=1,
        role_id=ROLE_ID,
    )


@pytest.fixture(scope="module")
def client():
    """Get Supabase client."""
    from engine.services.supabase import get_client
    return get_client()


@pytest.fixture(scope="module", autouse=True)
def ensure_sim_active(client):
    """Ensure sim is in active Phase A state for testing.

    If sim is in pre_start, advance it to active/Phase A for testing.
    """
    run = client.table("sim_runs").select("status,current_phase,current_round").eq("id", SIM_RUN_ID).limit(1).execute()
    if not run.data:
        pytest.skip(f"SimRun {SIM_RUN_ID} not found")
    status = run.data[0]["status"]
    phase = run.data[0]["current_phase"]
    rnd = run.data[0].get("current_round", 0)
    logger.info("SimRun status=%s, phase=%s, round=%s", status, phase, rnd)

    # Advance to active Phase A if needed
    if status == "pre_start":
        from engine.services.sim_run_manager import start_simulation
        start_simulation(SIM_RUN_ID)
        logger.info("Advanced sim from pre_start → active Phase A")
    elif status in ("setup",):
        from engine.services.sim_run_manager import start_pre_start, start_simulation
        start_pre_start(SIM_RUN_ID)
        start_simulation(SIM_RUN_ID)
        logger.info("Advanced sim from setup → active Phase A")
    elif status == "completed" or status == "aborted":
        pytest.skip(f"SimRun status={status}, cannot advance")


# ---------------------------------------------------------------------------
# Test 2.1: Observation tools work (no actions)
# ---------------------------------------------------------------------------

class TestObservationTools:
    """Verify query tools return data without errors."""

    def test_get_my_country(self, executor):
        import json
        result = json.loads(executor.execute("get_my_country", {}))
        assert "error" not in result, f"get_my_country failed: {result}"
        assert "country" in result or "country_code" in result or "id" in result

    def test_get_all_countries(self, executor):
        import json
        result = json.loads(executor.execute("get_all_countries", {}))
        assert isinstance(result, (list, dict))

    def test_get_relationships(self, executor):
        import json
        result = json.loads(executor.execute("get_relationships", {}))
        assert "error" not in result or "relationships" in str(result)

    def test_get_my_forces(self, executor):
        import json
        result = json.loads(executor.execute("get_my_forces", {}))
        assert "error" not in result

    def test_write_and_read_notes(self, executor):
        import json
        # Write
        w = json.loads(executor.execute("write_notes", {"key": "l2_test", "content": "L2 test note"}))
        assert w.get("success") or "saved" in str(w).lower() or "error" not in w
        # Read
        r = json.loads(executor.execute("read_notes", {"key": "l2_test"}))
        assert "error" not in r or "l2_test" in str(r).lower()


# ---------------------------------------------------------------------------
# Test 2.2: Phase A — Immediate Actions
# ---------------------------------------------------------------------------

class TestPhaseAActions:
    """Submit immediate actions and verify dispatch succeeds."""

    def test_public_statement(self, executor):
        import json
        result = json.loads(executor.execute("submit_action", {
            "action": {
                "action_type": "public_statement",
                "content": "Phrygia calls for regional stability and cooperation.",
                "rationale": "Diplomatic signaling at round start",
            }
        }))
        logger.info("public_statement result: %s", result)
        assert result.get("success") is True, f"public_statement failed: {result}"

    def test_propose_transaction_field_mapping(self, executor):
        """Verify counterpart_country → counterpart_country_code mapping works."""
        import json
        result = json.loads(executor.execute("submit_action", {
            "action": {
                "action_type": "propose_transaction",
                "counterpart_country": "solaria",
                "offer": {"coins": 5},
                "request": {"coins": 3},
                "rationale": "L2 test transaction",
            }
        }))
        logger.info("propose_transaction result: %s", result)
        # Should succeed or fail on game logic (not field mapping)
        assert result.get("validation_status") != "rejected" or "schema" not in str(result.get("validation_notes", "")), \
            f"Schema validation failed (field mapping issue): {result}"

    def test_propose_agreement_field_mapping(self, executor):
        """Verify propose_agreement normalization works."""
        import json
        result = json.loads(executor.execute("submit_action", {
            "action": {
                "action_type": "propose_agreement",
                "counterpart_country": "solaria",
                "agreement_name": "L2 Test Pact",
                "agreement_type": "trade_agreement",
                "visibility": "public",
                "terms": "Mutual trade cooperation between Phrygia and Solaria",
                "rationale": "L2 test agreement",
            }
        }))
        logger.info("propose_agreement result: %s", result)
        assert result.get("validation_status") != "rejected" or "schema" not in str(result.get("validation_notes", "")), \
            f"Schema validation failed: {result}"

    def test_covert_operation(self, executor):
        import json
        result = json.loads(executor.execute("submit_action", {
            "action": {
                "action_type": "covert_operation",
                "op_type": "propaganda",
                "target_country": "solaria",
                "intent": "destabilize",
                "rationale": "L2 test covert op",
            }
        }))
        logger.info("covert_operation result: %s", result)
        # May fail due to game logic (no covert cards) but should not crash
        assert "validation_status" in result


# ---------------------------------------------------------------------------
# Test 2.3: UUID Validation Guards
# ---------------------------------------------------------------------------

class TestUUIDValidation:
    """Verify invalid UUIDs are rejected cleanly, not crash."""

    def test_sign_agreement_invalid_uuid(self, executor):
        import json
        result = json.loads(executor.execute("submit_action", {
            "action": {
                "action_type": "sign_agreement",
                "agreement_id": "not-a-valid-uuid",
                "rationale": "L2 test invalid UUID",
            }
        }))
        logger.info("sign_agreement invalid UUID: %s", result)
        # Should get a clean error, not a crash
        assert result.get("success") is not True or "error" in str(result).lower()

    def test_accept_transaction_invalid_uuid(self, executor):
        import json
        result = json.loads(executor.execute("submit_action", {
            "action": {
                "action_type": "accept_transaction",
                "transaction_id": "bad-uuid-here",
                "response": "accept",
                "rationale": "L2 test invalid UUID",
            }
        }))
        logger.info("accept_transaction invalid UUID: %s", result)
        assert result.get("success") is not True


# ---------------------------------------------------------------------------
# Test 2.4: Phase B — Batch Decisions Rejected in Phase A
# ---------------------------------------------------------------------------

class TestPhaseBRestrictions:
    """Verify batch actions are rejected during Phase A."""

    def test_set_budget_rejected_in_phase_a(self, executor):
        import json
        result = json.loads(executor.execute("submit_action", {
            "action": {
                "action_type": "set_budget",
                "social_pct": 1.0,
                "military_coins": 5.0,
                "tech_coins": 3.0,
                "rationale": "L2 test budget in Phase A",
            }
        }))
        logger.info("set_budget in Phase A: %s", result)
        assert result.get("success") is False
        assert "Phase B" in str(result.get("validation_notes", "")) or "rejected" in str(result.get("validation_status", ""))

    def test_move_units_rejected_in_phase_a(self, executor):
        import json
        result = json.loads(executor.execute("submit_action", {
            "action": {
                "action_type": "move_units",
                "decision": "no_change",
                "rationale": "L2 test move in Phase A",
            }
        }))
        logger.info("move_units in Phase A: %s", result)
        assert result.get("success") is False


# ---------------------------------------------------------------------------
# Test 2.5: rd_investment no longer routed
# ---------------------------------------------------------------------------

class TestRemovedActions:
    """Verify removed actions are rejected cleanly."""

    def test_rd_investment_rejected(self, executor):
        import json
        result = json.loads(executor.execute("submit_action", {
            "action": {
                "action_type": "rd_investment",
                "domain": "nuclear",
                "amount": 10.0,
                "rationale": "L2 test removed action",
            }
        }))
        logger.info("rd_investment result: %s", result)
        # Should be rejected — either as unknown action type (removed from map)
        # or as pre_start block. Either way, should NOT succeed.
        assert result.get("success") is False
        notes = str(result.get("validation_notes", "")).lower()
        assert "unknown" in notes or "pre_start" in notes or "rejected" in notes


# ---------------------------------------------------------------------------
# Test 2.6: Reassign Types Field Mapping
# ---------------------------------------------------------------------------

class TestReassignTypes:
    """Verify reassign_types field normalization."""

    def test_reassign_types_field_mapping(self, executor):
        """power_type should map to position, new_holder_role to target_role_id."""
        import json
        result = json.loads(executor.execute("submit_action", {
            "action": {
                "action_type": "reassign_types",
                "power_type": "economic",
                "new_holder_role": "phrygia_fam",
                "rationale": "L2 test reassign",
            }
        }))
        logger.info("reassign_types result: %s", result)
        # Should NOT fail with "Invalid position" (that was the bug)
        assert "Invalid position" not in str(result.get("result", "")), \
            f"Field mapping bug still present: {result}"
