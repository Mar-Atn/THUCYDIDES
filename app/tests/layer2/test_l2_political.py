"""Level 2 — Political Actions.

Tests arrest, assassination, change_leader, reassign_types through ToolExecutor.

Run:
    cd "/Users/marat/4. METAGAMES/1. NEW SIMs/THUCYDIDES" && PYTHONPATH=app .venv/bin/python -m pytest app/tests/layer2/test_l2_political.py -v -s
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

# Phrygia: vizier is HoS (only role in phrygia)
# Columbia: dealer is HoS, many other roles


@pytest.fixture(scope="module")
def client():
    from engine.services.supabase import get_client
    return get_client()


@pytest.fixture(scope="module")
def phrygia_executor():
    """Vizier — HoS of Phrygia."""
    from engine.agents.managed.tool_executor import ToolExecutor
    return ToolExecutor(
        country_code="phrygia",
        scenario_code=SCENARIO_CODE,
        sim_run_id=SIM_RUN_ID,
        round_num=1,
        role_id="vizier",
    )


@pytest.fixture(scope="module")
def columbia_hos_executor():
    """Dealer — HoS of Columbia."""
    from engine.agents.managed.tool_executor import ToolExecutor
    return ToolExecutor(
        country_code="columbia",
        scenario_code=SCENARIO_CODE,
        sim_run_id=SIM_RUN_ID,
        round_num=1,
        role_id="dealer",
    )


@pytest.fixture(scope="module")
def columbia_opposition_executor():
    """Tribune — opposition role in Columbia (non-HoS)."""
    from engine.agents.managed.tool_executor import ToolExecutor
    return ToolExecutor(
        country_code="columbia",
        scenario_code=SCENARIO_CODE,
        sim_run_id=SIM_RUN_ID,
        round_num=1,
        role_id="tribune",
    )


@pytest.fixture(scope="module", autouse=True)
def ensure_sim_active(client):
    """Ensure sim is in active Phase A state."""
    run = client.table("sim_runs").select("status,current_phase").eq("id", SIM_RUN_ID).limit(1).execute()
    if not run.data:
        pytest.skip(f"SimRun {SIM_RUN_ID} not found")
    status = run.data[0]["status"]
    phase = run.data[0]["current_phase"]

    if status == "pre_start":
        from engine.services.sim_run_manager import start_simulation
        start_simulation(SIM_RUN_ID)
    elif status == "setup":
        from engine.services.sim_run_manager import start_pre_start, start_simulation
        start_pre_start(SIM_RUN_ID)
        start_simulation(SIM_RUN_ID)
    elif status in ("completed", "aborted"):
        pytest.skip(f"SimRun status={status}")
    elif phase != "A":
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


# ---------------------------------------------------------------------------
# Arrest
# ---------------------------------------------------------------------------

class TestArrest:

    def test_arrest_same_country(self, columbia_hos_executor):
        """HoS arrests a team member in same country."""
        result = json.loads(columbia_hos_executor.execute("submit_action", {
            "action": {
                "action_type": "arrest",
                "target_role": "volt",
                "rationale": "L2 test arrest",
            }
        }))
        logger.info("arrest same country: %s", result)
        # Should succeed or produce a meaningful game result (not schema crash)
        assert "validation_status" in result
        # Arrest should dispatch successfully (auto-confirmed in unmanned mode)
        if result.get("success"):
            assert result["validation_status"] in ("executed",)

    def test_arrest_wrong_country(self, columbia_hos_executor):
        """Try to arrest a role in a different country — should fail."""
        result = json.loads(columbia_hos_executor.execute("submit_action", {
            "action": {
                "action_type": "arrest",
                "target_role": "vizier",  # Phrygia role
                "rationale": "L2 test cross-country arrest",
            }
        }))
        logger.info("arrest wrong country: %s", result)
        # Should fail — can't arrest across countries
        notes = str(result.get("result", "")) + str(result.get("validation_notes", ""))
        # Arrest engine should reject cross-country targets
        assert result.get("success") is False or "country" in notes.lower() or "not found" in notes.lower() or "different" in notes.lower(), \
            f"Cross-country arrest should fail: {result}"


# ---------------------------------------------------------------------------
# Assassination
# ---------------------------------------------------------------------------

class TestAssassination:

    def test_assassination_dispatch(self, columbia_hos_executor):
        """Assassination attempt — should not crash."""
        result = json.loads(columbia_hos_executor.execute("submit_action", {
            "action": {
                "action_type": "assassination",
                "target_role": "tribune",
                "domestic": True,
                "rationale": "L2 test assassination",
            }
        }))
        logger.info("assassination: %s", result)
        assert "validation_status" in result
        # Should dispatch without crashing (may fail on game logic)


# ---------------------------------------------------------------------------
# Change Leader
# ---------------------------------------------------------------------------

class TestChangeLeader:

    def test_change_leader_by_non_hos(self, columbia_opposition_executor):
        """Non-HoS tries change_leader. May be rejected if stability too high."""
        result = json.loads(columbia_opposition_executor.execute("submit_action", {
            "action": {
                "action_type": "change_leader",
                "rationale": "L2 test change leader",
            }
        }))
        logger.info("change_leader by non-HoS: %s", result)
        assert "validation_status" in result
        # Expected: either dispatched (stability low enough) or rejected with stability message
        # Either way should not crash


# ---------------------------------------------------------------------------
# Reassign Types (Powers)
# ---------------------------------------------------------------------------

class TestReassignTypes:

    def test_reassign_economy_position(self, columbia_hos_executor):
        """HoS reassigns economy position to a different role."""
        result = json.loads(columbia_hos_executor.execute("submit_action", {
            "action": {
                "action_type": "reassign_types",
                "power_type": "economic",
                "new_holder_role": "anchor",  # diplomat role
                "rationale": "L2 test reassign economy",
            }
        }))
        logger.info("reassign_types economy: %s", result)
        assert "validation_status" in result
        # Should not fail with "Invalid position" (field mapping bug was fixed)
        assert "Invalid position" not in str(result.get("result", "")), \
            f"Field mapping bug: {result}"

    def test_reassign_military_position(self, columbia_hos_executor):
        """HoS reassigns military position."""
        result = json.loads(columbia_hos_executor.execute("submit_action", {
            "action": {
                "action_type": "reassign_types",
                "power_type": "military",
                "new_holder_role": "shadow",  # security role
                "rationale": "L2 test reassign military",
            }
        }))
        logger.info("reassign_types military: %s", result)
        assert "validation_status" in result
        assert "Invalid position" not in str(result.get("result", ""))
