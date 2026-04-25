"""Layer 2 — Nuclear Chain Tests.

Multi-step ordered test class for the nuclear launch chain:
INITIATE -> AUTHORIZE -> AUTHORIZE (2nd) -> INTERCEPT -> error cases.

Run:
    cd "/Users/marat/4. METAGAMES/1. NEW SIMs/THUCYDIDES" && PYTHONPATH=app .venv/bin/python -m pytest app/tests/layer2/test_l2_nuclear_chain.py -v -s
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
def client():
    from engine.services.supabase import get_client
    return get_client()


@pytest.fixture(scope="module", autouse=True)
def ensure_sim_active(client):
    """Ensure sim is in active state for testing."""
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


def _make_executor(country_code, role_id):
    from engine.agents.managed.tool_executor import ToolExecutor
    return ToolExecutor(country_code=country_code, scenario_code="ttt_v1",
                        sim_run_id=SIM_RUN_ID, round_num=1, role_id=role_id)


def _find_nuclear_country(client):
    """Find a country with nuclear capability.

    Returns (country_code, hos_role_id).
    Known nuclear countries from SEED: persia, choson.
    """
    # Use known nuclear countries from game design
    # Persia and Choson have nuclear programs per SEED data
    return "persia", "persia_supreme_leader"


def _find_authorizer_roles(client, country_code):
    """Find role_ids that can authorize nuclear launches (non-HoS roles with authorization priority)."""
    roles = client.table("roles").select("id,positions") \
        .eq("sim_run_id", SIM_RUN_ID) \
        .eq("country_code", country_code) \
        .eq("status", "active").execute().data or []

    authorizers = []
    for r in roles:
        positions = r.get("positions") or []
        # Non-HoS roles with military or security positions
        if "head_of_state" not in positions:
            authorizers.append(r["id"])
    return authorizers


class TestNuclearChain:
    """Ordered nuclear chain tests. Must run in order."""

    nuclear_action_id = None
    nuclear_country = None
    nuclear_role = None

    def test_01_initiate(self, client):
        """Initiate nuclear launch sequence.

        May fail on game logic (no nuclear capability in test data).
        Pipeline should not crash regardless.
        """
        cc, role = _find_nuclear_country(client)
        TestNuclearChain.nuclear_country = cc
        TestNuclearChain.nuclear_role = role

        # Use correct HoS role from DB
        roles = client.table("roles").select("id,positions") \
            .eq("sim_run_id", SIM_RUN_ID) \
            .eq("country_code", cc) \
            .eq("status", "active").execute().data or []
        hos_role = next((r["id"] for r in roles if "head_of_state" in (r.get("positions") or [])), role)
        TestNuclearChain.nuclear_role = hos_role

        executor = _make_executor(cc, hos_role)
        result = json.loads(executor.execute("submit_action", {
            "action": {
                "action_type": "nuclear_launch_initiate",
                "target_country": "solaria",
                "rationale": "L2 test nuclear launch initiation for pipeline verification",
            }
        }))
        logger.info("nuclear_launch_initiate result: %s", result)
        # Pipeline should not crash — either success or clean rejection
        assert "success" in result or "validation_status" in result

        if not result.get("success"):
            notes = str(result.get("result", "")) + str(result.get("validation_notes", ""))
            logger.info("Nuclear initiate rejected (expected if no nuclear capability): %s", notes)

        # Try to find nuclear_action_id from nuclear_actions table
        nuc = client.table("nuclear_actions") \
            .select("id") \
            .eq("sim_run_id", SIM_RUN_ID) \
            .order("created_at", desc=True) \
            .limit(1).execute().data
        if nuc:
            TestNuclearChain.nuclear_action_id = nuc[0]["id"]
            logger.info("Found nuclear_action_id: %s", TestNuclearChain.nuclear_action_id)

    def test_02_authorize_first(self, client):
        """First authorizer confirms nuclear launch."""
        if not TestNuclearChain.nuclear_action_id:
            pytest.skip("No nuclear_action_id from initiation step (nuclear capability not available)")

        cc = TestNuclearChain.nuclear_country
        authorizers = _find_authorizer_roles(client, cc)
        if not authorizers:
            pytest.skip(f"No authorizer roles found for {cc}")

        executor = _make_executor(cc, authorizers[0])
        result = json.loads(executor.execute("submit_action", {
            "action": {
                "action_type": "nuclear_authorize",
                "nuclear_action_id": TestNuclearChain.nuclear_action_id,
                "authorize": True,
                "rationale": "L2 test first authorization",
            }
        }))
        logger.info("nuclear_authorize (1st) result: %s", result)
        assert "success" in result or "validation_status" in result

    def test_03_authorize_second(self, client):
        """Second authorizer confirms nuclear launch."""
        if not TestNuclearChain.nuclear_action_id:
            pytest.skip("No nuclear_action_id from initiation step")

        cc = TestNuclearChain.nuclear_country
        authorizers = _find_authorizer_roles(client, cc)
        if len(authorizers) < 2:
            pytest.skip(f"Need 2+ authorizer roles for {cc}, found {len(authorizers)}")

        executor = _make_executor(cc, authorizers[1])
        result = json.loads(executor.execute("submit_action", {
            "action": {
                "action_type": "nuclear_authorize",
                "nuclear_action_id": TestNuclearChain.nuclear_action_id,
                "authorize": True,
                "rationale": "L2 test second authorization",
            }
        }))
        logger.info("nuclear_authorize (2nd) result: %s", result)
        assert "success" in result or "validation_status" in result

    def test_04_intercept(self, client):
        """Target country attempts to intercept."""
        if not TestNuclearChain.nuclear_action_id:
            pytest.skip("No nuclear_action_id from initiation step")

        # Target is solaria
        executor = _make_executor("solaria", "solaria_wellspring")
        result = json.loads(executor.execute("submit_action", {
            "action": {
                "action_type": "nuclear_intercept",
                "nuclear_action_id": TestNuclearChain.nuclear_action_id,
                "intercept": True,
                "rationale": "L2 test nuclear intercept",
            }
        }))
        logger.info("nuclear_intercept result: %s", result)
        assert "success" in result or "validation_status" in result

    def test_05_invalid_uuid(self, client):
        """nuclear_authorize with bad UUID should return clean error."""
        cc = TestNuclearChain.nuclear_country or "persia"
        role = TestNuclearChain.nuclear_role or "persia_supreme_leader"
        executor = _make_executor(cc, role)
        result = json.loads(executor.execute("submit_action", {
            "action": {
                "action_type": "nuclear_authorize",
                "nuclear_action_id": "not-a-valid-uuid-at-all",
                "authorize": True,
                "rationale": "L2 test invalid UUID",
            }
        }))
        logger.info("nuclear_authorize invalid UUID: %s", result)
        assert result.get("success") is not True, f"Should fail with invalid UUID: {result}"
