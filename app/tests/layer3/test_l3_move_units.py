"""L3 — Move Units: ToolExecutor plumbing + real managed agent behavioral tests.

Tests move_units through both dispatch_action (plumbing) and real managed
agent (behavioral). Covers hex movement, reserve withdrawal, no_change,
invalid targets, and batch moves.

IMPORTANT: move_units is Phase B only. Tests transition sim to Phase B
before submitting, then restore to Phase A after.

Run:
    cd "/Users/marat/4. METAGAMES/1. NEW SIMs/THUCYDIDES" && \
    PYTHONPATH=app .venv/bin/python -m pytest \
        app/tests/layer3/test_l3_move_units.py -v -s --timeout=300

Cost: Part 1 = $0 (no LLM). Part 2 = ~$0.20 (1 managed agent prompt).
"""
import asyncio
import json
import logging
import os
import pytest
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

for _p in [
    Path(__file__).resolve().parents[3] / ".env",
    Path(__file__).resolve().parents[2] / "engine" / ".env",
    Path(__file__).resolve().parents[2] / ".env",
]:
    if _p.exists():
        load_dotenv(_p)
        break

logger = logging.getLogger(__name__)

SIM_RUN_ID = os.environ.get("TEST_SIM_RUN_ID", "c954b9b6-35f0-4973-a08b-f38406c524e7")
SCENARIO_CODE = "ttt_v1"
COUNTRY = "sarmatia"
ROLE_ID = "pathfinder"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    from engine.services.supabase import get_client
    return get_client()


@pytest.fixture(scope="module")
def sarmatia_units(client):
    """Load Sarmatia's active ground units with coordinates."""
    deps = client.table("deployments") \
        .select("unit_id, country_code, unit_type, unit_status, global_row, global_col") \
        .eq("sim_run_id", SIM_RUN_ID) \
        .eq("country_code", COUNTRY) \
        .eq("unit_status", "active") \
        .not_.is_("global_row", "null") \
        .not_.is_("global_col", "null") \
        .execute().data or []
    ground = [d for d in deps if d["unit_type"] == "ground"]
    logger.info("Sarmatia active ground units with coords: %d", len(ground))
    for u in ground[:5]:
        logger.info("  %s at (%s, %s)", u["unit_id"], u["global_row"], u["global_col"])
    if not ground:
        pytest.skip("No Sarmatia ground units with coordinates found")
    return ground


@pytest.fixture(scope="module")
def sim_state(client):
    """Read and return current sim state."""
    run = client.table("sim_runs") \
        .select("status,current_phase,current_round") \
        .eq("id", SIM_RUN_ID).limit(1).execute()
    if not run.data:
        pytest.skip(f"SimRun {SIM_RUN_ID} not found")
    return run.data[0]


@pytest.fixture(scope="module")
def ensure_phase_b(client, sim_state):
    """Transition to Phase B for move_units tests, restore Phase A after."""
    from engine.services.sim_run_manager import end_phase_a

    original_phase = sim_state.get("current_phase", "A")
    original_round = sim_state.get("current_round", 1)
    status = sim_state.get("status", "")

    if status == "pre_start":
        from engine.services.sim_run_manager import start_simulation
        start_simulation(SIM_RUN_ID)

    # Transition to Phase B if needed
    current = client.table("sim_runs").select("current_phase") \
        .eq("id", SIM_RUN_ID).limit(1).execute()
    phase = current.data[0]["current_phase"] if current.data else "A"

    if phase == "A":
        result = end_phase_a(SIM_RUN_ID)
        logger.info("Transitioned to Phase B: %s", result)
    elif phase in ("inter_round",):
        # Already past B, force to B
        client.table("sim_runs").update({
            "current_phase": "B",
            "status": "processing",
            "phase_started_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", SIM_RUN_ID).execute()

    yield

    # Restore to original state
    client.table("sim_runs").update({
        "status": "active",
        "current_phase": original_phase,
        "current_round": original_round,
        "phase_started_at": datetime.now(timezone.utc).isoformat(),
        "phase_duration_seconds": 3600,
    }).eq("id", SIM_RUN_ID).execute()
    logger.info("Restored sim to Round %d Phase %s", original_round, original_phase)


def _find_adjacent_own_hex(unit, client):
    """Find an adjacent hex that's in Sarmatia's own territory or already occupied."""
    from engine.config.map_config import hex_neighbors_bounded
    row, col = unit["global_row"], unit["global_col"]
    neighbors = hex_neighbors_bounded(row, col)

    # Check which neighbors have friendly units (previously occupied)
    for nr, nc in neighbors:
        deps = client.table("deployments") \
            .select("unit_id") \
            .eq("sim_run_id", SIM_RUN_ID) \
            .eq("country_code", COUNTRY) \
            .eq("unit_status", "active") \
            .eq("global_row", nr) \
            .eq("global_col", nc) \
            .execute().data or []
        if deps:
            return (nr, nc)

    # Fall back: just use first neighbor (may fail validation but tests should handle)
    return neighbors[0] if neighbors else None


# ---------------------------------------------------------------------------
# Part 1: Plumbing tests (no LLM) — uses dispatch_action directly
# ---------------------------------------------------------------------------

class TestMoveUnitsPlumbing:
    """Test move_units through dispatch_action (bypasses ToolExecutor).

    NOTE: dispatch_action expects `moves` at top level of the action dict,
    NOT nested under `changes.moves`. The ToolExecutor has a known issue
    where MoveUnitsOrder.model_dump() produces `changes: {moves: [...]}`,
    but _process_movement reads `action.get("moves", [])`.
    """

    @pytest.fixture(autouse=True)
    def _setup(self, ensure_phase_b):
        pass

    def test_move_unit_to_adjacent_hex(self, client, sarmatia_units):
        """Move a ground unit to an adjacent hex with a friendly unit."""
        from engine.services.action_dispatcher import dispatch_action

        unit = sarmatia_units[0]
        unit_code = unit["unit_id"]
        orig_row, orig_col = unit["global_row"], unit["global_col"]

        target = _find_adjacent_own_hex(unit, client)
        if target is None:
            pytest.skip("No adjacent hex found for unit")
        tgt_row, tgt_col = target

        logger.info("Moving %s from (%d,%d) to (%d,%d)",
                     unit_code, orig_row, orig_col, tgt_row, tgt_col)

        result = dispatch_action(SIM_RUN_ID, 1, {
            "action_type": "move_units",
            "country_code": COUNTRY,
            "role_id": ROLE_ID,
            "moves": [{
                "unit_code": unit_code,
                "target": "hex",
                "target_global_row": tgt_row,
                "target_global_col": tgt_col,
            }],
            "rationale": "Tactical repositioning to strengthen the defensive line along the border",
        })

        logger.info("Move result: %s", result)
        assert result["success"], f"Move failed: {result}"
        assert result.get("moved_count", 0) >= 1

        # Verify DB update
        dep = client.table("deployments") \
            .select("global_row,global_col,unit_status") \
            .eq("sim_run_id", SIM_RUN_ID) \
            .eq("unit_id", unit_code) \
            .limit(1).execute()
        assert dep.data, f"Unit {unit_code} not found in DB"
        assert dep.data[0]["global_row"] == tgt_row, \
            f"Expected row {tgt_row}, got {dep.data[0]['global_row']}"
        assert dep.data[0]["global_col"] == tgt_col, \
            f"Expected col {tgt_col}, got {dep.data[0]['global_col']}"
        assert dep.data[0]["unit_status"] == "active"
        logger.info("PASS: Unit %s moved to (%d,%d) in DB", unit_code, tgt_row, tgt_col)

        # Move back to original position
        dispatch_action(SIM_RUN_ID, 1, {
            "action_type": "move_units",
            "country_code": COUNTRY,
            "role_id": ROLE_ID,
            "moves": [{
                "unit_code": unit_code,
                "target": "hex",
                "target_global_row": orig_row,
                "target_global_col": orig_col,
            }],
            "rationale": "Returning unit to original position after test movement validation",
        })

    def test_withdraw_to_reserve(self, client, sarmatia_units):
        """Withdraw a unit to reserve — status should change, coords cleared."""
        from engine.services.action_dispatcher import dispatch_action

        # Use the last unit to avoid interfering with test_move_unit_to_adjacent_hex
        unit = sarmatia_units[-1]
        unit_code = unit["unit_id"]
        orig_row, orig_col = unit["global_row"], unit["global_col"]

        logger.info("Withdrawing %s from (%d,%d) to reserve",
                     unit_code, orig_row, orig_col)

        result = dispatch_action(SIM_RUN_ID, 1, {
            "action_type": "move_units",
            "country_code": COUNTRY,
            "role_id": ROLE_ID,
            "moves": [{
                "unit_code": unit_code,
                "target": "reserve",
            }],
            "rationale": "Withdrawing unit to strategic reserve for redeployment later",
        })

        logger.info("Reserve result: %s", result)
        assert result["success"], f"Withdraw failed: {result}"

        # Verify DB: status=reserve, coords cleared
        dep = client.table("deployments") \
            .select("global_row,global_col,unit_status") \
            .eq("sim_run_id", SIM_RUN_ID) \
            .eq("unit_id", unit_code) \
            .limit(1).execute()
        assert dep.data, f"Unit {unit_code} not found"
        assert dep.data[0]["unit_status"] == "reserve"
        assert dep.data[0]["global_row"] is None
        assert dep.data[0]["global_col"] is None
        logger.info("PASS: Unit %s withdrawn to reserve in DB", unit_code)

        # Restore: redeploy to original hex
        dispatch_action(SIM_RUN_ID, 1, {
            "action_type": "move_units",
            "country_code": COUNTRY,
            "role_id": ROLE_ID,
            "moves": [{
                "unit_code": unit_code,
                "target": "hex",
                "target_global_row": orig_row,
                "target_global_col": orig_col,
            }],
            "rationale": "Restoring unit to original position after reserve test completed",
        })

    def test_no_change(self, client):
        """Submit decision=no_change — should succeed with no DB changes."""
        from engine.services.action_dispatcher import dispatch_action

        # no_change doesn't go through _process_movement (it needs "moves")
        # The dispatcher routes to _process_movement which checks moves first.
        # With no moves, it returns "No moves provided".
        # We test at the validator level instead.
        from engine.services.movement_validator import validate_movement_decision

        payload = {
            "action_type": "move_units",
            "country_code": COUNTRY,
            "decision": "no_change",
            "rationale": "Maintaining current defensive positions, no repositioning needed this round",
        }
        result = validate_movement_decision(payload, {}, {}, {})
        assert result["valid"], f"no_change validation failed: {result['errors']}"
        assert result["normalized"]["decision"] == "no_change"
        logger.info("PASS: no_change validated successfully")

    def test_invalid_target_wrong_territory(self, client, sarmatia_units):
        """Move to a hex in enemy territory without occupation — should fail."""
        from engine.services.action_dispatcher import dispatch_action

        unit = sarmatia_units[0]
        unit_code = unit["unit_id"]

        # Try to move to a hex far away in enemy territory (Columbia at col 3)
        result = dispatch_action(SIM_RUN_ID, 1, {
            "action_type": "move_units",
            "country_code": COUNTRY,
            "role_id": ROLE_ID,
            "moves": [{
                "unit_code": unit_code,
                "target": "hex",
                "target_global_row": 3,
                "target_global_col": 3,
            }],
            "rationale": "Attempting to move into enemy territory to test validation rules",
        })

        logger.info("Invalid target result: %s", result)
        assert not result["success"], "Should have failed — enemy territory"
        assert "errors" in result or "narrative" in result
        logger.info("PASS: Invalid territory move correctly rejected")

    def test_batch_moves(self, client, sarmatia_units):
        """Move 2+ units in one action."""
        from engine.services.action_dispatcher import dispatch_action

        if len(sarmatia_units) < 2:
            pytest.skip("Need at least 2 Sarmatia ground units")

        u1 = sarmatia_units[0]
        u2 = sarmatia_units[1]
        u1_orig = (u1["global_row"], u1["global_col"])
        u2_orig = (u2["global_row"], u2["global_col"])

        t1 = _find_adjacent_own_hex(u1, client)
        t2 = _find_adjacent_own_hex(u2, client)
        if t1 is None or t2 is None:
            pytest.skip("No adjacent hexes found for batch test")

        logger.info("Batch move: %s->(%d,%d), %s->(%d,%d)",
                     u1["unit_id"], t1[0], t1[1], u2["unit_id"], t2[0], t2[1])

        result = dispatch_action(SIM_RUN_ID, 1, {
            "action_type": "move_units",
            "country_code": COUNTRY,
            "role_id": ROLE_ID,
            "moves": [
                {"unit_code": u1["unit_id"], "target": "hex",
                 "target_global_row": t1[0], "target_global_col": t1[1]},
                {"unit_code": u2["unit_id"], "target": "hex",
                 "target_global_row": t2[0], "target_global_col": t2[1]},
            ],
            "rationale": "Coordinated repositioning of two ground units for tactical advantage",
        })

        logger.info("Batch result: %s", result)
        assert result["success"], f"Batch move failed: {result}"
        assert result.get("moved_count", 0) >= 2
        logger.info("PASS: Batch move of %d units succeeded", result.get("moved_count", 0))

        # Restore both units
        dispatch_action(SIM_RUN_ID, 1, {
            "action_type": "move_units",
            "country_code": COUNTRY,
            "role_id": ROLE_ID,
            "moves": [
                {"unit_code": u1["unit_id"], "target": "hex",
                 "target_global_row": u1_orig[0], "target_global_col": u1_orig[1]},
                {"unit_code": u2["unit_id"], "target": "hex",
                 "target_global_row": u2_orig[0], "target_global_col": u2_orig[1]},
            ],
            "rationale": "Restoring both units to original positions after batch movement test",
        })

    def test_toolexecutor_move_units_bug(self, client, sarmatia_units):
        """Demonstrate ToolExecutor bug: changes.moves not extracted to top-level moves.

        _process_movement reads action.get("moves", []) but ToolExecutor passes
        MoveUnitsOrder.model_dump() which has changes: {moves: [...]}.
        This test documents the bug — it should fail until the ToolExecutor or
        dispatcher is fixed to normalize the field.
        """
        from engine.agents.managed.tool_executor import ToolExecutor

        executor = ToolExecutor(
            country_code=COUNTRY,
            scenario_code=SCENARIO_CODE,
            sim_run_id=SIM_RUN_ID,
            round_num=1,
            role_id=ROLE_ID,
        )

        unit = sarmatia_units[0]
        target = _find_adjacent_own_hex(unit, client)
        if target is None:
            pytest.skip("No adjacent hex")

        result_str = executor.execute("submit_action", {"action": {
            "action_type": "move_units",
            "decision": "change",
            "rationale": "Testing ToolExecutor path for move_units action submission flow",
            "changes": {"moves": [{
                "unit_code": unit["unit_id"],
                "target": "hex",
                "target_global_row": target[0],
                "target_global_col": target[1],
            }]},
        }})
        result = json.loads(result_str)
        logger.info("ToolExecutor move_units result: %s", result)

        # This documents the bug: ToolExecutor path fails because
        # _process_movement reads action.get("moves") but gets changes.moves
        if not result.get("success"):
            logger.warning(
                "BUG CONFIRMED: ToolExecutor move_units fails. "
                "Cause: _process_movement reads action.get('moves') but "
                "MoveUnitsOrder.model_dump() puts moves under 'changes'. "
                "Fix: add field normalization in ToolExecutor or _process_movement."
            )
            pytest.xfail(
                "Known bug: ToolExecutor doesn't normalize changes.moves -> moves"
            )
        else:
            logger.info("ToolExecutor move_units succeeded (bug may be fixed)")


# ---------------------------------------------------------------------------
# Part 2: Real agent test (LLM, ~$0.20)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set — real agent tests require API access",
)
class TestRealAgentMoveUnits:
    """Real managed agent: Sarmatia agent submits troop movements."""

    @pytest.fixture(autouse=True)
    def _setup(self, ensure_phase_b):
        pass

    def test_real_agent_moves_units(self, client):
        """Create Sarmatia managed session, prompt for troop movements."""
        from engine.agents.managed.session_manager import ManagedSessionManager

        manager = ManagedSessionManager()
        all_tools = []
        all_actions = []

        async def _run():
            ctx = await manager.create_session(
                role_id=ROLE_ID,
                country_code=COUNTRY,
                sim_run_id=SIM_RUN_ID,
                scenario_code=SIM_RUN_ID,
                round_num=1,
            )
            logger.info("Created Sarmatia session: %s", ctx.session_id)

            try:
                transcript = await manager.send_event(ctx,
                    "You are Pathfinder, Head of State of Sarmatia. "
                    "It is Phase B — time to submit your troop movements.\n\n"
                    "INSTRUCTIONS:\n"
                    "1. Use get_my_forces to see ALL your military units with coordinates.\n"
                    "2. Pick at least one ground unit that has coordinates (global_row, global_col).\n"
                    "3. Submit a move_units action via submit_action. The format is:\n"
                    "   {\"action\": {\"action_type\": \"move_units\", \"decision\": \"change\", "
                    "\"rationale\": \"<30+ chars explaining your move>\", "
                    "\"changes\": {\"moves\": [{\"unit_code\": \"<unit_id>\", \"target\": \"reserve\"}]}}}\n\n"
                    "You can move units to 'reserve' (withdraw) or keep them where they are "
                    "with decision='no_change'.\n\n"
                    "Do this NOW. Use get_my_forces first, then submit_action."
                )

                tools = [e.get("tool", "") for e in transcript if e.get("type") == "tool_call"]
                actions = [
                    e.get("input", {}) for e in transcript
                    if e.get("type") == "tool_call" and e.get("tool") == "submit_action"
                ]
                all_tools.extend(tools)
                all_actions.extend(actions)

                logger.info("Agent tools used: %s", tools)
                logger.info("Agent actions: %d", len(actions))
                for i, a in enumerate(actions):
                    logger.info("  Action %d: %s", i, json.dumps(a)[:500])

                cost = manager.get_cost_estimate(ctx)
                logger.info("Session cost: $%.4f", cost["total_cost_usd"])
                assert cost["total_cost_usd"] < 0.50

            finally:
                await manager.cleanup(ctx)

        asyncio.run(_run())

        # Assertions
        assert "get_my_forces" in all_tools, \
            f"Agent must use get_my_forces. Tools: {all_tools}"
        assert "submit_action" in all_tools, \
            f"Agent must submit an action. Tools: {all_tools}"

        # Check that at least one action was move_units
        move_actions = []
        for a in all_actions:
            action_data = a.get("action", {})
            if isinstance(action_data, str):
                try:
                    action_data = json.loads(action_data)
                except (json.JSONDecodeError, TypeError):
                    continue
            if action_data.get("action_type") == "move_units":
                move_actions.append(action_data)

        logger.info("move_units actions submitted: %d", len(move_actions))
        assert len(move_actions) >= 1, \
            f"Agent should submit at least 1 move_units action. Actions: {all_actions}"

        logger.info("PASS: Real agent submitted %d move_units action(s)", len(move_actions))
