"""L2 — Nuclear chain persistence (CONTRACT_NUCLEAR_CHAIN v1.0).

Tests the full 4-phase orchestrator chain with scripted decisions:
  1. Sarmatia initiates underground nuclear test
  2. Ironhand + Compass authorize (scripted confirm)
  3. Engine resolves (deterministic precomputed roll)
  4. Verify: nuclear_actions record, audit JSONB, events, nuclear_confirmed
"""

from __future__ import annotations
import pytest

from engine.orchestrators.nuclear_chain import NuclearChainOrchestrator
from engine.services.supabase import get_client
from tests._sim_run_helper import create_isolated_run

SCENARIO = "start_one"


@pytest.fixture
def client():
    return get_client()


@pytest.fixture
def isolated_run(client):
    sim_run_id, cleanup = create_isolated_run(scenario_code=SCENARIO, test_name="nuclear_chain")
    # Seed R1 from R0
    cs = client.table("country_states_per_round").select("*") \
        .eq("sim_run_id", sim_run_id).eq("round_num", 0).execute()
    if cs.data:
        rows = [{k: v for k, v in r.items() if k != "id"} for r in cs.data]
        for r in rows:
            r["round_num"] = 1
            r["nuclear_test_decision"] = None
            r["nuclear_launch_decision"] = None
        client.table("country_states_per_round").upsert(
            rows, on_conflict="sim_run_id,round_num,country_code"
        ).execute()
    yield sim_run_id
    cleanup()


def test_nuclear_test_full_chain_scripted(client, isolated_run):
    """Sarmatia underground test: initiate → authorize → resolve with deterministic roll."""
    sim_run_id = isolated_run
    orch = NuclearChainOrchestrator()

    # Phase 1: Initiate
    decision = {
        "action_type": "nuclear_test",
        "country_code": "sarmatia",
        "round_num": 1,
        "decision": "change",
        "rationale": "Testing nuclear capability underground at homeland hex for tier confirmation",
        "changes": {
            "test_type": "underground",
            "target_global_row": 2,
            "target_global_col": 16,
        },
    }
    init = orch.initiate(decision, sim_run_id, round_num=1, initiator_role_id="pathfinder")
    assert init["status"] == "awaiting_authorization", init
    action_id = init["action_id"]
    print(f"\n  [initiate] action_id={action_id}")

    # Phase 2: Authorization (scripted confirms)
    r1 = orch.submit_authorization(action_id, "ironhand", confirm=True,
                                     rationale="Military chief confirms: test is strategically necessary")
    print(f"  [auth1] ironhand: {r1}")

    r2 = orch.submit_authorization(action_id, "compass", confirm=True,
                                     rationale="Senior official confirms: test aligned with national doctrine")
    print(f"  [auth2] compass: {r2}")
    assert r2["status"] == "authorized"

    # Phase 4: Resolve (deterministic — 50% roll, below T2 threshold 70% → success)
    # Sarmatia is T3, so success_prob = 95%. Roll 0.50 < 0.95 → success.
    result = orch.resolve(action_id, precomputed_rolls={"test_success_roll": 0.50})
    print(f"  [resolve] outcome={result['outcome']} success={result['success']}")
    assert result["success"] is True
    assert result["outcome"] == "test_success"
    assert result["test_type"] == "underground"

    # Verify DB state
    action = client.table("nuclear_actions").select("*").eq("id", action_id).execute().data[0]
    assert action["status"] == "resolved"
    assert action["authorizer_1_response"] == "confirm"
    assert action["authorizer_2_response"] == "confirm"
    assert action["resolution"]["success"] is True

    # Verify audit JSONB
    row = client.table("country_states_per_round").select("nuclear_test_decision") \
        .eq("sim_run_id", sim_run_id).eq("round_num", 1).eq("country_code", "sarmatia") \
        .limit(1).execute().data[0]
    assert row["nuclear_test_decision"] is not None

    # Verify event
    events = client.table("observatory_events").select("event_type,summary") \
        .eq("sim_run_id", sim_run_id).eq("round_num", 1) \
        .eq("event_type", "nuclear_test").execute().data or []
    assert events, "Expected nuclear_test event"
    print(f"  [event] {events[0]['summary']}")


def test_nuclear_test_authorization_rejected(client, isolated_run):
    """If one authorizer rejects, the action is cancelled."""
    sim_run_id = isolated_run
    orch = NuclearChainOrchestrator()

    decision = {
        "action_type": "nuclear_test",
        "country_code": "sarmatia",
        "round_num": 1,
        "decision": "change",
        "rationale": "Testing nuclear capability - this one should be rejected by compass",
        "changes": {"test_type": "surface", "target_global_row": 2, "target_global_col": 16},
    }
    init = orch.initiate(decision, sim_run_id, round_num=1, initiator_role_id="pathfinder")
    action_id = init["action_id"]

    # Ironhand confirms
    orch.submit_authorization(action_id, "ironhand", confirm=True,
                                rationale="Military chief approves the surface test")

    # Compass rejects
    r = orch.submit_authorization(action_id, "compass", confirm=False,
                                    rationale="Senior official rejects: surface test too provocative at this time")
    assert r["status"] == "cancelled"

    action = client.table("nuclear_actions").select("status").eq("id", action_id).execute().data[0]
    assert action["status"] == "cancelled"
    print(f"\n  [cancelled] compass rejected — action cancelled")


def test_nuclear_test_failure_roll(client, isolated_run):
    """When the test roll fails, nuclear_confirmed stays false."""
    sim_run_id = isolated_run
    orch = NuclearChainOrchestrator()

    # Set choson to unconfirmed T1 for this test
    client.table("country_states_per_round").update({
        "nuclear_confirmed": False,
    }).eq("sim_run_id", sim_run_id).eq("round_num", 1).eq("country_code", "choson").execute()

    decision = {
        "action_type": "nuclear_test",
        "country_code": "choson",
        "round_num": 1,
        "decision": "change",
        "rationale": "Choson tests nuclear capability to confirm tier one nuclear status",
        "changes": {"test_type": "underground", "target_global_row": 3, "target_global_col": 18},
    }
    init = orch.initiate(decision, sim_run_id, round_num=1, initiator_role_id="pyro")
    action_id = init["action_id"]

    # Choson is single-HoS → 1 AI officer
    orch.submit_authorization(action_id, "ai_officer", confirm=True,
                                rationale="AI officer confirms Choson nuclear test")

    # Resolve with a HIGH roll (0.85 > 0.70 threshold for below-T2) → FAILURE
    result = orch.resolve(action_id, precomputed_rolls={"test_success_roll": 0.85})
    assert result["success"] is False
    assert result["outcome"] == "test_failure"
    print(f"\n  [test_failure] roll=0.85 > prob=0.70 → test failed")

    # nuclear_confirmed should still be false
    row = client.table("country_states_per_round").select("nuclear_confirmed") \
        .eq("sim_run_id", sim_run_id).eq("round_num", 1).eq("country_code", "choson") \
        .limit(1).execute().data[0]
    assert row["nuclear_confirmed"] is False
