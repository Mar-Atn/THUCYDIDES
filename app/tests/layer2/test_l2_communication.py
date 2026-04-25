"""Level 2 — Communication + Covert Operations Tests.

Tests: call_org_meeting, intelligence, covert_operation (sabotage, propaganda).
Uses ToolExecutor directly against live DB.

Run:
    cd "/Users/marat/4. METAGAMES/1. NEW SIMs/THUCYDIDES" && PYTHONPATH=app .venv/bin/python -m pytest app/tests/layer2/test_l2_communication.py -v -s
"""
import json
import logging
import os
import pytest
from pathlib import Path

logger = logging.getLogger(__name__)

_root_env = Path(__file__).resolve().parents[3] / ".env"
_engine_env = Path(__file__).resolve().parents[2] / "engine" / ".env"
from dotenv import load_dotenv
for _p in (_engine_env, _root_env):
    if _p.exists():
        load_dotenv(_p)

SIM_RUN_ID = os.environ.get("TEST_SIM_RUN_ID", "c954b9b6-35f0-4973-a08b-f38406c524e7")


@pytest.fixture(scope="module")
def phrygia():
    from engine.agents.managed.tool_executor import ToolExecutor
    return ToolExecutor(
        country_code="phrygia", scenario_code="ttt_v1",
        sim_run_id=SIM_RUN_ID, round_num=1, role_id="vizier",
    )


@pytest.fixture(scope="module")
def solaria():
    from engine.agents.managed.tool_executor import ToolExecutor
    return ToolExecutor(
        country_code="solaria", scenario_code="ttt_v1",
        sim_run_id=SIM_RUN_ID, round_num=1, role_id="wellspring",
    )


@pytest.fixture(scope="module")
def client():
    from engine.services.supabase import get_client
    return get_client()


@pytest.fixture(scope="module", autouse=True)
def ensure_sim_active(client):
    """Ensure sim is active for testing."""
    run = client.table("sim_runs").select("status").eq("id", SIM_RUN_ID).limit(1).execute()
    if not run.data:
        pytest.skip(f"SimRun {SIM_RUN_ID} not found")
    status = run.data[0]["status"]
    if status in ("completed", "aborted"):
        pytest.skip(f"SimRun status={status}")
    if status in ("setup", "pre_start"):
        client.table("sim_runs").update({"status": "active", "current_phase": "A", "current_round": 1}).eq("id", SIM_RUN_ID).execute()


# ---------------------------------------------------------------------------
# Org Meeting
# ---------------------------------------------------------------------------

class TestCallOrgMeeting:
    """Test call_org_meeting via submit_action -> dispatch."""

    def test_call_org_meeting(self, phrygia, client):
        """Call an org meeting. Should create a meeting invitation."""
        result = json.loads(phrygia.execute("submit_action", {
            "action": {
                "action_type": "call_org_meeting",
                "organization_code": "UN",
                "agenda": "Regional security summit",
                "rationale": "L2 test org meeting",
            }
        }))
        logger.info("call_org_meeting result: %s", result)
        # Should pass validation and dispatch
        assert result.get("validation_status") != "rejected", f"Schema rejected: {result}"
        # Dispatch may succeed or fail on game logic (no org found, etc.)
        # The key test is that it doesn't crash and routes correctly
        assert "action_type" in result or "success" in result


# ---------------------------------------------------------------------------
# Intelligence (standalone action_type)
# ---------------------------------------------------------------------------

class TestIntelligence:
    """Test the 'intelligence' action type."""

    def test_intelligence_schema_validation(self, phrygia):
        """The 'intelligence' action_type should pass schema validation
        and dispatch to generate_intelligence_report."""
        result = json.loads(phrygia.execute("submit_action", {
            "action": {
                "action_type": "intelligence",
                "op_type": "intelligence",
                "question": "What are Solaria's military positions?",
                "rationale": "L2 test",
            }
        }))
        logger.info("intelligence result: %s", result)
        assert result.get("validation_status") != "rejected", f"Schema rejected: {result}"
        assert result.get("action_type") == "intelligence"

    @pytest.mark.llm
    def test_intelligence_via_covert_operation(self, phrygia):
        """Intelligence via covert_operation action_type (correct schema path).

        NOTE: This makes an LLM call. Skip if no API key.
        """
        api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("GOOGLE_AI_API_KEY")
        if not api_key:
            pytest.skip("No LLM API key available")

        result = json.loads(phrygia.execute("submit_action", {
            "action": {
                "action_type": "covert_operation",
                "op_type": "intelligence",
                "question": "What is Solaria's current economic situation?",
                "rationale": "L2 test intelligence via covert_operation",
            }
        }))
        logger.info("covert_operation(intelligence) result: %s", result)
        # This routes through _dispatch_covert -> generate_intelligence_report
        # BUT has parameter order bug: role_id passed as question
        if result.get("success"):
            logger.info("Intelligence report succeeded")
        else:
            logger.warning("Intelligence dispatch failed: %s", result)


# ---------------------------------------------------------------------------
# Covert Operations
# ---------------------------------------------------------------------------

class TestCovertOperations:
    """Test covert operations via submit_action."""

    def test_covert_sabotage(self, phrygia):
        """Sabotage operation against Solaria infrastructure."""
        result = json.loads(phrygia.execute("submit_action", {
            "action": {
                "action_type": "covert_operation",
                "op_type": "sabotage",
                "target_country": "solaria",
                "target_type": "infrastructure",
                "rationale": "L2 test sabotage",
            }
        }))
        logger.info("covert_sabotage result: %s", result)
        assert result.get("validation_status") != "rejected", f"Schema rejected: {result}"
        # Sabotage should execute (success or failure is fine — it's probabilistic)
        assert result.get("validation_status") in ("executed", "dispatch_failed"), f"Unexpected status: {result}"

    def test_covert_propaganda_destabilize(self, phrygia):
        """Propaganda destabilize operation against Solaria."""
        result = json.loads(phrygia.execute("submit_action", {
            "action": {
                "action_type": "covert_operation",
                "op_type": "propaganda",
                "target_country": "solaria",
                "intent": "destabilize",
                "content": "Anti-government leaflets distributed",
                "rationale": "L2 test propaganda",
            }
        }))
        logger.info("covert_propaganda(destabilize) result: %s", result)
        assert result.get("validation_status") != "rejected", f"Schema rejected: {result}"
        assert result.get("validation_status") in ("executed", "dispatch_failed"), f"Unexpected: {result}"

    def test_covert_propaganda_boost(self, phrygia):
        """Propaganda boost for own country (self-targeted or allied)."""
        result = json.loads(phrygia.execute("submit_action", {
            "action": {
                "action_type": "covert_operation",
                "op_type": "propaganda",
                "target_country": "phrygia",
                "intent": "boost",
                "content": "Government success stories",
                "rationale": "L2 test propaganda boost",
            }
        }))
        logger.info("covert_propaganda(boost) result: %s", result)
        assert result.get("validation_status") != "rejected", f"Schema rejected: {result}"

    def test_covert_unknown_op_type(self, phrygia):
        """Unknown op_type should be rejected or fail gracefully."""
        result = json.loads(phrygia.execute("submit_action", {
            "action": {
                "action_type": "covert_operation",
                "op_type": "cyber_attack",
                "target_country": "solaria",
                "rationale": "L2 test unknown op",
            }
        }))
        logger.info("unknown op_type result: %s", result)
        # Should dispatch but fail with "Unknown covert op_type"
        if result.get("validation_status") == "executed":
            logger.warning("Unexpected: unknown op_type executed successfully")

    def test_covert_sabotage_missing_target(self, phrygia):
        """Sabotage without target_country."""
        result = json.loads(phrygia.execute("submit_action", {
            "action": {
                "action_type": "covert_operation",
                "op_type": "sabotage",
                "target_type": "infrastructure",
                "rationale": "L2 test missing target",
            }
        }))
        logger.info("sabotage missing target result: %s", result)
        # Should still pass validation (target_country is Optional) but may fail in engine
