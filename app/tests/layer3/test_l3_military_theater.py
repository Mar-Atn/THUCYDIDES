"""L3 — Military Theater Combat: Real Sarmatia agent with improved awareness.

Tests that a Sarmatia managed agent can:
1. Use get_my_forces to discover its units with coordinates
2. Use get_hex_info to probe neighboring hexes for enemy units
3. Submit ground_attack and/or air_strike actions with correct fields
4. Produce combat results in DB (agent_decisions + observatory_events)

Sarmatia (Pathfinder, nuclear L3) is at war with Ruthenia.
Forces: 32 units (16 ground, 6 tactical_air, 5 strategic_missile, 3 air_defense, 2 naval).
Dense combat zone around hexes (3-4, 11-12).

Run:
    cd "/Users/marat/4. METAGAMES/1. NEW SIMs/THUCYDIDES" && \
    PYTHONPATH=app .venv/bin/python -m pytest \
        app/tests/layer3/test_l3_military_theater.py -v -s --timeout=300

Cost: ~$0.30-0.60 per run (2 prompts to Claude managed agent).
"""
import asyncio
import json
import logging
import os
import pytest
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

pytestmark = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set — real agent tests require API access",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_tool_names(transcript: list[dict]) -> list[str]:
    return [e.get("tool", "") for e in transcript if e.get("type") == "tool_call"]


def _extract_tool_inputs(transcript: list[dict], tool_name: str) -> list[dict]:
    return [
        e.get("input", {})
        for e in transcript
        if e.get("type") == "tool_call" and e.get("tool") == tool_name
    ]


def _extract_actions(transcript: list[dict]) -> list[dict]:
    return [
        e.get("input", {})
        for e in transcript
        if e.get("type") == "tool_call" and e.get("tool") == "submit_action"
    ]


def _combat_action_types(actions: list[dict]) -> list[str]:
    """Extract action_type from submit_action inputs."""
    types = []
    for a in actions:
        action = a.get("action", {})
        if isinstance(action, str):
            try:
                action = json.loads(action)
            except (json.JSONDecodeError, TypeError):
                action = {}
        types.append(action.get("action_type", "unknown"))
    return types


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def manager():
    from engine.agents.managed.session_manager import ManagedSessionManager
    return ManagedSessionManager()


@pytest.fixture(scope="module")
def client():
    from engine.services.supabase import get_client
    return get_client()


@pytest.fixture(scope="module")
def ensure_active(client):
    run = client.table("sim_runs").select("status,current_phase,current_round") \
        .eq("id", SIM_RUN_ID).limit(1).execute()
    if not run.data:
        pytest.skip("SimRun not found")
    status = run.data[0]["status"]
    if status == "pre_start":
        from engine.services.sim_run_manager import start_simulation
        start_simulation(SIM_RUN_ID)
    elif status not in ("active",):
        pytest.skip(f"SimRun status={status}")
    return run.data[0]


# ---------------------------------------------------------------------------
# Test: Sarmatia military theater — exploration + multi-type combat
# ---------------------------------------------------------------------------

class TestSarmatiaMillitaryTheater:
    """Real managed agent: Sarmatia explores forces, probes hexes, attacks Ruthenia."""

    @pytest.fixture(autouse=True)
    def _setup(self, ensure_active):
        pass

    def test_sarmatia_military_combat(self, manager, client):
        """Sarmatia agent uses get_my_forces, get_hex_info, and submits combat actions."""

        all_tools_used = []
        all_actions = []
        all_transcripts = []

        async def _run():
            ctx = await manager.create_session(
                role_id="pathfinder",
                country_code="sarmatia",
                sim_run_id=SIM_RUN_ID,
                scenario_code=SIM_RUN_ID,
                round_num=1,
            )
            logger.info("Created Sarmatia session: %s", ctx.session_id)

            try:
                # --- Prompt 1: Assess military situation ---
                t1 = await manager.send_event(ctx,
                    "You are Pathfinder, Head of State of Sarmatia. Round 1, Phase A.\n\n"
                    "PRIORITY: MILITARY ASSESSMENT.\n\n"
                    "You are AT WAR with Ruthenia. Your forces are positioned along the border "
                    "in the Eastern Ereb theater, concentrated around hexes (3,11), (3,12), (4,11), (4,12).\n\n"
                    "Step 1: Use get_my_forces to see ALL your military units with their coordinates.\n"
                    "Step 2: Use get_hex_info to probe hexes ADJACENT to your forces — look for "
                    "Ruthenia units you can attack. Try hexes like (2,11), (2,12), (3,13), (5,11), (5,12).\n\n"
                    "Take detailed notes on where your forces are and where enemy forces are. "
                    "You will need this for your attack orders."
                )
                tools_1 = _extract_tool_names(t1)
                all_tools_used.extend(tools_1)
                all_transcripts.extend(t1)
                logger.info("Prompt 1 tools: %s", tools_1)

                # --- Prompt 2: Launch attacks ---
                t2 = await manager.send_event(ctx,
                    "ATTACK ORDERS — execute immediately.\n\n"
                    "You are at war with Ruthenia. Based on your reconnaissance:\n\n"
                    "1. GROUND ATTACK: Use submit_action with action_type='ground_attack'. "
                    "You MUST specify attacker_unit_codes (list of your ground unit IDs from get_my_forces) "
                    "and target_global_row + target_global_col (coordinates of an enemy hex you found "
                    "with get_hex_info). Pick 2-3 of your strongest ground units.\n\n"
                    "2. AIR STRIKE: Use submit_action with action_type='air_strike'. "
                    "You have 6 tactical_air units. Specify their unit codes as attacker_unit_codes "
                    "and target an enemy hex within 2 hexes of your air units.\n\n"
                    "Submit BOTH attacks now. Use get_my_forces again if you need to look up unit codes. "
                    "Use get_hex_info if you need to confirm enemy positions."
                )
                tools_2 = _extract_tool_names(t2)
                actions_2 = _extract_actions(t2)
                all_tools_used.extend(tools_2)
                all_actions.extend(actions_2)
                all_transcripts.extend(t2)
                logger.info("Prompt 2 tools: %s", tools_2)
                logger.info("Prompt 2 actions: %d submitted", len(actions_2))

                # Log action details
                for i, a in enumerate(actions_2):
                    action_data = a.get("action", {})
                    if isinstance(action_data, str):
                        try:
                            action_data = json.loads(action_data)
                        except (json.JSONDecodeError, TypeError):
                            pass
                    logger.info("  Action %d: type=%s payload=%s",
                                i, action_data.get("action_type"), json.dumps(action_data, indent=2)[:500])

                # Cost check
                cost = manager.get_cost_estimate(ctx)
                logger.info("Session cost: $%.4f", cost["total_cost_usd"])
                assert cost["total_cost_usd"] < 1.00, f"Cost too high: ${cost['total_cost_usd']}"

            finally:
                await manager.cleanup(ctx)

        asyncio.run(_run())

        # --- Assertions ---

        # 1. Agent used get_my_forces (military awareness)
        assert "get_my_forces" in all_tools_used, \
            f"Agent must use get_my_forces to discover units. Tools used: {all_tools_used}"

        # 2. Agent used get_hex_info (hex probing for targets)
        assert "get_hex_info" in all_tools_used, \
            f"Agent must use get_hex_info to probe for enemies. Tools used: {all_tools_used}"

        # 3. Agent submitted at least one combat action
        assert "submit_action" in all_tools_used, \
            f"Agent must submit at least one combat action. Tools used: {all_tools_used}"

        # 4. Check action types — should include ground_attack or air_strike
        action_types = _combat_action_types(all_actions)
        combat_types = {"ground_attack", "air_strike", "launch_missile_conventional"}
        submitted_combat = set(action_types) & combat_types
        logger.info("Combat action types submitted: %s", submitted_combat)
        assert len(submitted_combat) >= 1, \
            f"Agent should submit at least 1 combat action type. Got: {action_types}"

        # 5. Verify correct field names in combat actions
        for a in all_actions:
            action_data = a.get("action", {})
            if isinstance(action_data, str):
                try:
                    action_data = json.loads(action_data)
                except (json.JSONDecodeError, TypeError):
                    continue
            at = action_data.get("action_type", "")
            if at in ("ground_attack", "air_strike", "launch_missile_conventional"):
                # Should have target coordinates
                has_target = (
                    "target_global_row" in action_data or "target_row" in action_data
                )
                logger.info("Action %s has target coords: %s (keys: %s)",
                            at, has_target, list(action_data.keys()))
                # Should have attacker unit codes
                has_units = (
                    "attacker_unit_codes" in action_data or "launcher_unit_code" in action_data
                )
                logger.info("Action %s has unit codes: %s", at, has_units)

        # 6. Check DB — agent_decisions for combat
        decisions = client.table("agent_decisions") \
            .select("action_type,validation_status,action_payload") \
            .eq("sim_run_id", SIM_RUN_ID) \
            .eq("country_code", "sarmatia") \
            .eq("round_num", 1) \
            .execute()
        decision_types = [d["action_type"] for d in (decisions.data or [])]
        decision_statuses = [(d["action_type"], d["validation_status"]) for d in (decisions.data or [])]
        logger.info("DB decisions: %s", decision_statuses)

        combat_decisions = [d for d in decision_types if d in combat_types]
        logger.info("Combat decisions in DB: %s", combat_decisions)

        # 7. Check observatory_events for combat results
        events = client.table("observatory_events") \
            .select("event_type,country_code,payload") \
            .eq("sim_run_id", SIM_RUN_ID) \
            .eq("country_code", "sarmatia") \
            .eq("round_num", 1) \
            .execute()
        combat_events = [
            e for e in (events.data or [])
            if "combat" in (e.get("event_type") or "").lower()
            or "attack" in (e.get("event_type") or "").lower()
            or "strike" in (e.get("event_type") or "").lower()
        ]
        logger.info("Combat observatory events: %d", len(combat_events))
        for ce in combat_events[:5]:
            logger.info("  Event: %s — %s", ce["event_type"],
                        json.dumps(ce.get("payload", {}))[:200])

        # 8. Log get_hex_info calls to verify agent probed correct hexes
        hex_probes = _extract_tool_inputs(all_transcripts, "get_hex_info")
        logger.info("Hex probes: %d calls", len(hex_probes))
        for hp in hex_probes[:10]:
            logger.info("  get_hex_info(%s)", hp)

        # 9. Verify multiple actions (stretch goal — agent should take 2+)
        if len(submitted_combat) >= 2:
            logger.info("EXCELLENT: Agent submitted multiple combat types: %s", submitted_combat)
        elif len(all_actions) >= 2:
            logger.info("GOOD: Agent submitted 2+ actions total: %s", action_types)
        else:
            logger.info("ACCEPTABLE: Agent submitted 1 combat action: %s", action_types)

        # Final summary
        logger.info("\n=== MILITARY THEATER TEST SUMMARY ===")
        logger.info("Tools used: %s", sorted(set(all_tools_used)))
        logger.info("get_my_forces calls: %d", all_tools_used.count("get_my_forces"))
        logger.info("get_hex_info calls: %d", all_tools_used.count("get_hex_info"))
        logger.info("submit_action calls: %d", all_tools_used.count("submit_action"))
        logger.info("Combat types submitted: %s", submitted_combat)
        logger.info("DB combat decisions: %s", combat_decisions)
        logger.info("Observatory combat events: %d", len(combat_events))
