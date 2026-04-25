"""Layer 2 — Military Non-Combat Tests.

Tests non-combat military actions through the ToolExecutor pipeline:
naval_blockade, basing_rights, martial_law, nuclear_test.

Run:
    cd "/Users/marat/4. METAGAMES/1. NEW SIMs/THUCYDIDES" && PYTHONPATH=app .venv/bin/python -m pytest app/tests/layer2/test_l2_military_noncombat.py -v -s
"""
import json
import logging
import os
import pytest

logger = logging.getLogger(__name__)

from pathlib import Path
_env_path = Path(__file__).resolve().parents[2] / "engine" / ".env"
if _env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(_env_path)

SIM_RUN_ID = os.environ.get("TEST_SIM_RUN_ID", "c954b9b6-35f0-4973-a08b-f38406c524e7")


@pytest.fixture(scope="module")
def phrygia():
    from engine.agents.managed.tool_executor import ToolExecutor
    return ToolExecutor(country_code="phrygia", scenario_code="ttt_v1",
                        sim_run_id=SIM_RUN_ID, round_num=1, role_id="phrygia_vizier")


@pytest.fixture(scope="module")
def persia():
    """Persia executor — needed for nuclear tests (Persia has nuclear program)."""
    from engine.agents.managed.tool_executor import ToolExecutor
    return ToolExecutor(country_code="persia", scenario_code="ttt_v1",
                        sim_run_id=SIM_RUN_ID, round_num=1, role_id="persia_supreme_leader")


@pytest.fixture(scope="module")
def client():
    from engine.services.supabase import get_client
    return get_client()


@pytest.fixture(scope="module", autouse=True)
def ensure_sim_active(client):
    """Ensure sim is in active Phase A state for testing."""
    run = client.table("sim_runs").select("status,current_phase").eq("id", SIM_RUN_ID).limit(1).execute()
    if not run.data:
        pytest.skip(f"SimRun {SIM_RUN_ID} not found")
    status = run.data[0]["status"]
    if status == "pre_start":
        from engine.services.sim_run_manager import start_simulation
        start_simulation(SIM_RUN_ID)
    elif status == "setup":
        from engine.services.sim_run_manager import start_pre_start, start_simulation
        start_pre_start(SIM_RUN_ID)
        start_simulation(SIM_RUN_ID)
    elif status in ("completed", "aborted"):
        pytest.skip(f"SimRun status={status}, cannot advance")


class TestNavalBlockade:

    def test_establish_blockade(self, phrygia, client):
        """Establish a naval blockade at a chokepoint.

        Note: BlockadeOrder schema has no 'operation' field, so the dispatcher
        defaults to "establish". We submit with the schema fields only.
        """
        from engine.config.map_config import CHOKEPOINTS
        zone_id = list(CHOKEPOINTS.keys())[0]  # e.g. cp_caribe

        # Find Phrygia naval units
        naval = client.table("deployments").select("unit_id") \
            .eq("sim_run_id", SIM_RUN_ID) \
            .eq("country_code", "phrygia") \
            .eq("unit_type", "naval") \
            .eq("unit_status", "active") \
            .limit(2).execute().data or []
        if not naval:
            pytest.skip("No Phrygia naval units for blockade")

        unit_codes = [u["unit_id"] for u in naval[:2]]
        result = json.loads(phrygia.execute("submit_action", {
            "action": {
                "action_type": "naval_blockade",
                "zone_id": zone_id,
                "imposer_units": unit_codes,
                "rationale": "L2 test blockade",
            }
        }))
        logger.info("establish_blockade result: %s", result)
        assert "success" in result or "validation_status" in result
        # May fail on game logic (units not at chokepoint) but should not crash

    def test_lift_blockade(self, phrygia, client):
        """Lift a blockade — requires direct dispatcher call since schema lacks 'operation'.

        This tests the dispatcher path directly.
        """
        from engine.config.map_config import CHOKEPOINTS
        from engine.services.action_dispatcher import dispatch_action

        zone_id = list(CHOKEPOINTS.keys())[0]
        result = dispatch_action(
            sim_run_id=SIM_RUN_ID,
            round_num=1,
            action={
                "action_type": "naval_blockade",
                "operation": "lift",
                "zone_id": zone_id,
                "country_code": "phrygia",
                "role_id": "phrygia_vizier",
            }
        )
        logger.info("lift_blockade result: %s", result)
        assert "success" in result or "narrative" in result


class TestBasingRights:

    def test_grant_basing_rights(self, phrygia, client):
        result = json.loads(phrygia.execute("submit_action", {
            "action": {
                "action_type": "basing_rights",
                "operation": "grant",
                "guest_country": "cathay",
                "zone_id": "eastern_ereb",
                "rationale": "L2 test grant basing",
            }
        }))
        logger.info("grant_basing result: %s", result)
        assert "success" in result or "validation_status" in result

    def test_revoke_basing_rights(self, phrygia, client):
        result = json.loads(phrygia.execute("submit_action", {
            "action": {
                "action_type": "basing_rights",
                "operation": "revoke",
                "guest_country": "cathay",
                "zone_id": "eastern_ereb",
                "rationale": "L2 test revoke basing",
            }
        }))
        logger.info("revoke_basing result: %s", result)
        assert "success" in result or "validation_status" in result


class TestMartialLaw:

    def test_martial_law(self, client):
        """Test martial_law — check which countries are eligible.

        Martial law requires specific conditions. We try Phrygia first,
        then fall back to other countries.
        """
        from engine.agents.managed.tool_executor import ToolExecutor

        # Try Phrygia first
        executor = ToolExecutor(country_code="phrygia", scenario_code="ttt_v1",
                                sim_run_id=SIM_RUN_ID, round_num=1, role_id="phrygia_vizier")
        result = json.loads(executor.execute("submit_action", {
            "action": {
                "action_type": "martial_law",
                "rationale": "L2 test martial law",
            }
        }))
        logger.info("martial_law result: %s", result)
        # May fail on eligibility but should not crash
        assert "success" in result or "validation_status" in result


class TestNuclearTest:

    def test_nuclear_test(self, persia, client):
        """Nuclear test — tests the pipeline doesn't crash.

        Persia may not have nuclear_level >= 1 in test data, so dispatch
        may fail on game logic. We verify: no crash, clean error or success.
        """
        result = json.loads(persia.execute("submit_action", {
            "action": {
                "action_type": "nuclear_test",
                "rationale": "L2 test nuclear test for validation pipeline",
            }
        }))
        logger.info("nuclear_test result: %s", result)
        assert "success" in result or "validation_status" in result
        # If rejected on eligibility, that's valid game logic — not a bug
        if not result.get("success"):
            notes = str(result.get("result", "")) + str(result.get("validation_notes", ""))
            logger.info("nuclear_test rejected (expected if no nuclear capability): %s", notes)
        # Check for observatory event if successful
        if result.get("success"):
            events = client.table("observatory_events") \
                .select("id,event_type") \
                .eq("sim_run_id", SIM_RUN_ID) \
                .eq("event_type", "nuclear_test") \
                .order("created_at", desc=True) \
                .limit(1).execute().data or []
            assert len(events) > 0, "No nuclear_test event found in observatory"
