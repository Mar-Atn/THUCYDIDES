"""Layer 2 — Military Combat Tests.

Tests all combat action types through the AI agent ToolExecutor pipeline:
ground_attack, ground_move, air_strike, naval_combat, naval_bombardment,
launch_missile_conventional.

Verifies the full path: ToolExecutor.execute → Pydantic validation →
dispatch_action → engine → DB.

Run:
    cd "/Users/marat/4. METAGAMES/1. NEW SIMs/THUCYDIDES" && PYTHONPATH=app .venv/bin/python -m pytest app/tests/layer2/test_l2_military_combat.py -v -s
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
def solaria():
    from engine.agents.managed.tool_executor import ToolExecutor
    return ToolExecutor(country_code="solaria", scenario_code="ttt_v1",
                        sim_run_id=SIM_RUN_ID, round_num=1, role_id="solaria_wellspring")


@pytest.fixture(scope="module")
def client():
    from engine.services.supabase import get_client
    return get_client()


@pytest.fixture(scope="module", autouse=True)
def ensure_sim_active(client):
    """Ensure sim is in active Phase A state for testing."""
    run = client.table("sim_runs").select("status,current_phase,current_round").eq("id", SIM_RUN_ID).limit(1).execute()
    if not run.data:
        pytest.skip(f"SimRun {SIM_RUN_ID} not found")
    status = run.data[0]["status"]
    phase = run.data[0]["current_phase"]
    logger.info("SimRun status=%s, phase=%s", status, phase)

    if status == "pre_start":
        from engine.services.sim_run_manager import start_simulation
        start_simulation(SIM_RUN_ID)
        logger.info("Advanced sim from pre_start -> active Phase A")
    elif status == "setup":
        from engine.services.sim_run_manager import start_pre_start, start_simulation
        start_pre_start(SIM_RUN_ID)
        start_simulation(SIM_RUN_ID)
        logger.info("Advanced sim from setup -> active Phase A")
    elif status in ("completed", "aborted"):
        pytest.skip(f"SimRun status={status}, cannot advance")


@pytest.fixture(scope="module")
def ensure_at_war(client, phrygia):
    """Ensure Phrygia and Solaria are at war (declare war if needed)."""
    rels = client.table("relationships").select("relationship") \
        .eq("sim_run_id", SIM_RUN_ID) \
        .or_(
            "and(from_country_code.eq.phrygia,to_country_code.eq.solaria),"
            "and(from_country_code.eq.solaria,to_country_code.eq.phrygia)"
        ).execute().data or []

    at_war = any(r.get("relationship") == "at_war" for r in rels)
    if not at_war:
        result = json.loads(phrygia.execute("submit_action", {
            "action": {
                "action_type": "declare_war",
                "target_country": "solaria",
                "rationale": "L2 test: ensure war state for combat tests",
            }
        }))
        logger.info("declare_war result: %s", result)
    return True


@pytest.fixture(scope="module")
def phrygia_units(client):
    """Load Phrygia's active deployed units with hex coordinates."""
    units = client.table("deployments").select("*") \
        .eq("sim_run_id", SIM_RUN_ID) \
        .eq("country_code", "phrygia") \
        .eq("unit_status", "active") \
        .not_.is_("global_row", "null") \
        .not_.is_("global_col", "null") \
        .execute().data or []
    logger.info("Phrygia has %d deployed units with coordinates", len(units))
    return units


@pytest.fixture(scope="module")
def solaria_units(client):
    """Load Solaria's active deployed units with hex coordinates."""
    units = client.table("deployments").select("*") \
        .eq("sim_run_id", SIM_RUN_ID) \
        .eq("country_code", "solaria") \
        .eq("unit_status", "active") \
        .not_.is_("global_row", "null") \
        .not_.is_("global_col", "null") \
        .execute().data or []
    logger.info("Solaria has %d deployed units with coordinates", len(units))
    return units


def _find_adjacent_pair(atk_units, def_units, atk_type=None, def_type=None):
    """Find an attacker unit adjacent to a defender unit, optionally filtering by type."""
    from engine.config.map_config import hex_neighbors_bounded
    for au in atk_units:
        if atk_type and au.get("unit_type") != atk_type:
            continue
        a_row, a_col = au["global_row"], au["global_col"]
        neighbors = set(hex_neighbors_bounded(a_row, a_col))
        for du in def_units:
            if def_type and du.get("unit_type") != def_type:
                continue
            if (du["global_row"], du["global_col"]) in neighbors:
                return au, du
    return None, None


def _find_empty_adjacent_hex(units, client, sim_run_id, country_code, unit_type=None):
    """Find a unit with an adjacent empty hex (no enemy units)."""
    from engine.config.map_config import hex_neighbors_bounded
    for u in units:
        if unit_type and u.get("unit_type") != unit_type:
            continue
        row, col = u["global_row"], u["global_col"]
        for nr, nc in hex_neighbors_bounded(row, col):
            enemy = client.table("deployments").select("id") \
                .eq("sim_run_id", sim_run_id) \
                .eq("global_row", nr).eq("global_col", nc) \
                .neq("country_code", country_code) \
                .eq("unit_status", "active").limit(1).execute().data
            if not enemy:
                return u, nr, nc
    return None, None, None


class TestGroundAttack:

    def test_ground_attack_valid(self, phrygia, phrygia_units, solaria_units, ensure_at_war):
        atk, defn = _find_adjacent_pair(phrygia_units, solaria_units, atk_type="ground")
        if not atk or not defn:
            pytest.skip("No Phrygia ground unit adjacent to Solaria unit")

        result = json.loads(phrygia.execute("submit_action", {
            "action": {
                "action_type": "ground_attack",
                "attacker_unit_codes": [atk["unit_id"]],
                "target_global_row": defn["global_row"],
                "target_global_col": defn["global_col"],
                "target_description": f"Solaria unit at ({defn['global_row']},{defn['global_col']})",
                "rationale": "L2 test ground attack",
            }
        }))
        logger.info("ground_attack result: %s", result)
        assert "success" in result, f"No success field: {result}"
        assert result.get("validation_status") != "rejected", f"Rejected: {result}"

    def test_ground_attack_no_attacker_units(self, phrygia, solaria_units, ensure_at_war):
        if not solaria_units:
            pytest.skip("No Solaria units to target")
        target = solaria_units[0]
        result = json.loads(phrygia.execute("submit_action", {
            "action": {
                "action_type": "ground_attack",
                "attacker_unit_codes": ["NONEXISTENT_UNIT_999"],
                "target_global_row": target["global_row"],
                "target_global_col": target["global_col"],
                "target_description": "Test with bad unit codes",
                "rationale": "L2 test invalid attacker",
            }
        }))
        logger.info("ground_attack bad units: %s", result)
        # Should not crash — either dispatch_failed or a clean error
        assert "success" in result or "validation_status" in result


class TestGroundMove:

    def test_ground_move_to_empty_hex(self, phrygia, client, phrygia_units, ensure_at_war):
        unit, nr, nc = _find_empty_adjacent_hex(
            phrygia_units, client, SIM_RUN_ID, "phrygia", unit_type="ground")
        if not unit:
            pytest.skip("No Phrygia ground unit with empty adjacent hex")

        result = json.loads(phrygia.execute("submit_action", {
            "action": {
                "action_type": "ground_move",
                "attacker_unit_codes": [unit["unit_id"]],
                "target_global_row": nr,
                "target_global_col": nc,
                "target_description": f"Move to empty hex ({nr},{nc})",
                "rationale": "L2 test ground move",
            }
        }))
        logger.info("ground_move result: %s", result)
        assert result.get("validation_status") != "rejected", f"Rejected: {result}"
        # Verify unit position updated
        if result.get("success"):
            dep = client.table("deployments").select("global_row,global_col") \
                .eq("sim_run_id", SIM_RUN_ID) \
                .eq("unit_id", unit["unit_id"]).limit(1).execute().data
            if dep:
                assert dep[0]["global_row"] == nr, f"Row not updated: {dep[0]}"
                assert dep[0]["global_col"] == nc, f"Col not updated: {dep[0]}"


class TestAirStrike:

    def test_air_strike_valid(self, phrygia, phrygia_units, solaria_units, ensure_at_war):
        atk, defn = _find_adjacent_pair(phrygia_units, solaria_units, atk_type="air")
        if not atk or not defn:
            pytest.skip("No Phrygia air unit adjacent to Solaria unit")

        result = json.loads(phrygia.execute("submit_action", {
            "action": {
                "action_type": "air_strike",
                "attacker_unit_codes": [atk["unit_id"]],
                "target_global_row": defn["global_row"],
                "target_global_col": defn["global_col"],
                "target_description": f"Air strike on Solaria at ({defn['global_row']},{defn['global_col']})",
                "rationale": "L2 test air strike",
            }
        }))
        logger.info("air_strike result: %s", result)
        assert "success" in result, f"No success field: {result}"
        assert result.get("validation_status") != "rejected", f"Rejected: {result}"


class TestNavalCombat:

    def test_naval_combat_valid(self, phrygia, phrygia_units, solaria_units, ensure_at_war):
        atk, defn = _find_adjacent_pair(phrygia_units, solaria_units, atk_type="naval", def_type="naval")
        if not atk or not defn:
            pytest.skip("No Phrygia naval unit adjacent to Solaria naval unit")

        result = json.loads(phrygia.execute("submit_action", {
            "action": {
                "action_type": "naval_combat",
                "attacker_unit_codes": [atk["unit_id"]],
                "target_global_row": defn["global_row"],
                "target_global_col": defn["global_col"],
                "target_description": f"Naval combat at ({defn['global_row']},{defn['global_col']})",
                "rationale": "L2 test naval combat",
            }
        }))
        logger.info("naval_combat result: %s", result)
        assert "success" in result, f"No success field: {result}"
        assert result.get("validation_status") != "rejected", f"Rejected: {result}"


class TestNavalBombardment:

    def test_naval_bombardment_valid(self, phrygia, phrygia_units, solaria_units, ensure_at_war):
        atk, defn = _find_adjacent_pair(phrygia_units, solaria_units, atk_type="naval", def_type="ground")
        if not atk or not defn:
            pytest.skip("No Phrygia naval unit adjacent to Solaria ground unit")

        result = json.loads(phrygia.execute("submit_action", {
            "action": {
                "action_type": "naval_bombardment",
                "attacker_unit_codes": [atk["unit_id"]],
                "target_global_row": defn["global_row"],
                "target_global_col": defn["global_col"],
                "target_description": f"Bombardment at ({defn['global_row']},{defn['global_col']})",
                "rationale": "L2 test naval bombardment",
            }
        }))
        logger.info("naval_bombardment result: %s", result)
        assert "success" in result, f"No success field: {result}"
        assert result.get("validation_status") != "rejected", f"Rejected: {result}"


class TestMissileLaunch:

    def test_missile_launch_valid(self, phrygia, phrygia_units, solaria_units, ensure_at_war):
        missile_units = [u for u in phrygia_units if u.get("unit_type") == "strategic_missile"]
        if not missile_units:
            pytest.skip("No Phrygia missile units deployed")
        if not solaria_units:
            pytest.skip("No Solaria units to target")

        target = solaria_units[0]
        result = json.loads(phrygia.execute("submit_action", {
            "action": {
                "action_type": "launch_missile_conventional",
                "launcher_unit_code": missile_units[0]["unit_id"],
                "target_global_row": target["global_row"],
                "target_global_col": target["global_col"],
                "rationale": "L2 test missile launch",
            }
        }))
        logger.info("missile_launch result: %s", result)
        assert "success" in result, f"No success field: {result}"
        assert result.get("validation_status") != "rejected", f"Rejected: {result}"

    def test_missile_out_of_range(self, phrygia, phrygia_units, ensure_at_war):
        missile_units = [u for u in phrygia_units if u.get("unit_type") == "strategic_missile"]
        if not missile_units:
            pytest.skip("No Phrygia missile units deployed")

        # Target hex at extreme corner of map — likely out of range
        result = json.loads(phrygia.execute("submit_action", {
            "action": {
                "action_type": "launch_missile_conventional",
                "launcher_unit_code": missile_units[0]["unit_id"],
                "target_global_row": 1,
                "target_global_col": 20,
                "rationale": "L2 test missile out of range",
            }
        }))
        logger.info("missile_out_of_range result: %s", result)
        # Should either fail with range error or succeed (if in range) — should not crash
        assert "success" in result or "validation_status" in result
