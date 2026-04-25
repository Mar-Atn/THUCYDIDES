"""Level 2 — Columbia Elections.

Tests self_nominate and cast_vote through ToolExecutor.
Columbia-specific: dealer (HoS), tribune/challenger (opposition), volt, anchor, shadow, shield.

Run:
    cd "/Users/marat/4. METAGAMES/1. NEW SIMs/THUCYDIDES" && PYTHONPATH=app .venv/bin/python -m pytest app/tests/layer2/test_l2_elections.py -v -s
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
def columbia_hos():
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
def columbia_tribune():
    """Tribune — opposition role."""
    from engine.agents.managed.tool_executor import ToolExecutor
    return ToolExecutor(
        country_code="columbia",
        scenario_code=SCENARIO_CODE,
        sim_run_id=SIM_RUN_ID,
        round_num=1,
        role_id="tribune",
    )


@pytest.fixture(scope="module")
def phrygia_executor():
    """Vizier — non-Columbia role."""
    from engine.agents.managed.tool_executor import ToolExecutor
    return ToolExecutor(
        country_code="phrygia",
        scenario_code=SCENARIO_CODE,
        sim_run_id=SIM_RUN_ID,
        round_num=1,
        role_id="vizier",
    )


@pytest.fixture(scope="module", autouse=True)
def ensure_sim_active(client):
    """Ensure sim is in active Phase A."""
    run = client.table("sim_runs").select("status,current_phase").eq("id", SIM_RUN_ID).limit(1).execute()
    if not run.data:
        pytest.skip(f"SimRun {SIM_RUN_ID} not found")
    status = run.data[0]["status"]
    if status == "pre_start":
        from engine.services.sim_run_manager import start_simulation
        start_simulation(SIM_RUN_ID)
    elif status in ("completed", "aborted"):
        pytest.skip(f"SimRun status={status}")
    phase = run.data[0]["current_phase"]
    if phase != "A":
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
# Self Nominate
# ---------------------------------------------------------------------------

class TestSelfNominate:

    def test_self_nominate_round_1_for_round_2(self, columbia_tribune):
        """Nominate in round 1 for election in round 2 — timing should be valid."""
        result = json.loads(columbia_tribune.execute("submit_action", {
            "action": {
                "action_type": "self_nominate",
                "election_type": "columbia_midterms",
                "election_round": 2,
                "rationale": "L2 test nomination",
            }
        }))
        logger.info("self_nominate R1 for R2: %s", result)
        assert "validation_status" in result
        # Should succeed (round 1 = election_round 2 - 1)
        if not result.get("success"):
            # May fail for other reasons (duplicate, etc.) but not timing
            notes = str(result.get("result", "")) + str(result.get("validation_notes", ""))
            assert "round" not in notes.lower() or "must be submitted" not in notes.lower(), \
                f"Timing validation wrong: {result}"

    def test_self_nominate_wrong_timing(self, columbia_tribune):
        """Nominate in round 1 for election in round 5 — timing mismatch."""
        result = json.loads(columbia_tribune.execute("submit_action", {
            "action": {
                "action_type": "self_nominate",
                "election_type": "columbia_midterms",
                "election_round": 5,
                "rationale": "L2 test wrong timing",
            }
        }))
        logger.info("self_nominate wrong timing: %s", result)
        # Should fail — round 1 != 5 - 1
        notes = str(result.get("result", "")) + str(result.get("validation_notes", ""))
        assert result.get("success") is False or "round" in notes.lower(), \
            f"Should reject wrong timing: {result}"

    def test_self_nominate_non_columbia(self, phrygia_executor):
        """Non-Columbia role tries to nominate — should be rejected."""
        result = json.loads(phrygia_executor.execute("submit_action", {
            "action": {
                "action_type": "self_nominate",
                "election_type": "columbia_midterms",
                "election_round": 2,
                "rationale": "L2 test non-Columbia nomination",
            }
        }))
        logger.info("self_nominate non-Columbia: %s", result)
        assert result.get("success") is False, f"Non-Columbia should be rejected: {result}"


# ---------------------------------------------------------------------------
# Cast Vote
# ---------------------------------------------------------------------------

class TestCastVote:

    def test_cast_vote_no_election_open(self, columbia_tribune):
        """Vote when no election is open — should fail cleanly."""
        result = json.loads(columbia_tribune.execute("submit_action", {
            "action": {
                "action_type": "cast_vote",
                "election_type": "columbia_midterms",
                "candidate_role_id": "dealer",
                "rationale": "L2 test vote no election",
            }
        }))
        logger.info("cast_vote no election: %s", result)
        # Should fail — no election is open in round 1
        assert result.get("success") is False or "election" in str(result.get("result", "")).lower() or \
            "not open" in str(result.get("result", "")).lower(), \
            f"Should fail when no election open: {result}"

    def test_cast_vote_non_columbia(self, phrygia_executor):
        """Non-Columbia role tries to vote — should fail."""
        result = json.loads(phrygia_executor.execute("submit_action", {
            "action": {
                "action_type": "cast_vote",
                "election_type": "columbia_midterms",
                "candidate_role_id": "dealer",
                "rationale": "L2 test non-Columbia vote",
            }
        }))
        logger.info("cast_vote non-Columbia: %s", result)
        assert result.get("success") is False, f"Non-Columbia vote should be rejected: {result}"
