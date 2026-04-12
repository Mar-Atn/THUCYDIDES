"""L2 — Nuclear LAUNCH chain persistence (CONTRACT_NUCLEAR_CHAIN v1.0).

Tests the full 4-phase chain for a T3 nuclear salvo:
  1. Sarmatia initiates 3-missile nuclear salvo at Columbia hex (3,3)
  2. Ironhand + Compass authorize (scripted confirm)
  3. Columbia (T3) attempts interception (scripted yes)
  4. Engine resolves: interception rolls, hit rolls, damage, salvo aggregate

All rolls deterministic via precomputed_rolls.
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
    sim_run_id, cleanup = create_isolated_run(scenario_code=SCENARIO, test_name="nuclear_launch")
    # Seed R1
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
    # Seed unit states at R1
    us = client.table("unit_states_per_round").select("*") \
        .eq("sim_run_id", sim_run_id).eq("round_num", 0).execute()
    if us.data:
        rows = [{k: v for k, v in r.items() if k != "id"} for r in us.data]
        for r in rows:
            r["round_num"] = 1
        for i in range(0, len(rows), 200):
            client.table("unit_states_per_round").upsert(
                rows[i:i+200], on_conflict="sim_run_id,round_num,unit_code"
            ).execute()
    yield sim_run_id
    cleanup()


def test_nuclear_launch_t3_salvo_full_chain(client, isolated_run):
    """Sarmatia T3 salvo: 3 missiles at Columbia (3,3).

    Deterministic rolls:
      - Columbia (T3) intercepts: 4 AD units × 25% each
        rolls: [0.10, 0.80, 0.15, 0.90] → 2 intercepts (missiles 1,3 destroyed)
      - 1 missile survives
      - Hit roll: 0.50 < 0.80 → HIT
      - Damage applied: 50% military on hex destroyed
      - Salvo aggregate: global stability -1.5, target -2.5, leader death 1/6
        leader roll: 0.90 > 0.167 → leader survives
    """
    sim_run_id = isolated_run
    orch = NuclearChainOrchestrator()

    # Sarmatia has sar_m_01, sar_m_02, sar_m_03 deployed at (2,16) and (2,12)
    decision = {
        "action_type": "launch_missile",
        "country_code": "sarmatia",
        "round_num": 1,
        "decision": "change",
        "rationale": "Strategic nuclear salvo against Columbia home territory in total war scenario",
        "changes": {
            "warhead": "nuclear",
            "missiles": [
                {"missile_unit_code": "sar_m_05", "target_global_row": 3, "target_global_col": 3},
                {"missile_unit_code": "sar_m_02", "target_global_row": 3, "target_global_col": 3},
                {"missile_unit_code": "sar_m_03", "target_global_row": 3, "target_global_col": 3},
            ],
        },
    }

    # Phase 1: Initiate
    init = orch.initiate(decision, sim_run_id, round_num=1, initiator_role_id="pathfinder")
    assert init["status"] == "awaiting_authorization", f"Initiation failed: {init}"
    action_id = init["action_id"]
    print(f"\n  [initiate] action_id={action_id}")

    # Phase 2: Authorization
    orch.submit_authorization(action_id, "ironhand", confirm=True,
                               rationale="Military chief confirms: strategic necessity in total war")
    r = orch.submit_authorization(action_id, "compass", confirm=True,
                                    rationale="Senior official confirms: all diplomatic options exhausted")
    assert r["status"] == "authorized"
    print(f"  [authorized] both confirmed")

    # Phase 3: Interception — manually set status + submit Columbia's decision
    client.table("nuclear_actions").update(
        {"status": "awaiting_interception"}
    ).eq("id", action_id).execute()

    orch.submit_interception(action_id, "columbia", intercept=True,
                              rationale="Columbia intercepts to defend homeland — last resort defense")
    print(f"  [interception] columbia chooses to intercept")

    # Phase 4: Resolve with deterministic rolls
    result = orch.resolve(action_id, precomputed_rolls={
        "interception_rolls": {
            "target_ad": [],  # target country auto-AD handled separately
            "columbia": [0.10, 0.80, 0.15, 0.90],  # 4 AD → rolls 1,3 succeed (0.10<0.25, 0.15<0.25)
        },
        "hit_rolls": [0.50],  # 1 surviving missile, 0.50 < 0.80 → HIT
        "leader_death_roll": 0.90,  # > 0.167 → leader survives
    })

    print(f"  [resolve] outcome={result['outcome']}")
    print(f"  missiles: launched={result['missiles_launched']} intercepted={result['missiles_intercepted']} hits={result['hits']}")
    print(f"  interception_log: {result['interception_log']}")
    print(f"  destroyed_units: {result['destroyed_units'][:5]}")
    print(f"  salvo_effects: {result['salvo_effects']}")

    assert result["outcome"] == "nuclear_launch_resolved"
    assert result["missiles_launched"] == 3

    # Verify DB state
    action = client.table("nuclear_actions").select("status,resolution") \
        .eq("id", action_id).execute().data[0]
    assert action["status"] == "resolved"
    assert action["resolution"]["outcome"] == "nuclear_launch_resolved"

    # Verify audit JSONB
    row = client.table("country_states_per_round").select("nuclear_launch_decision") \
        .eq("sim_run_id", sim_run_id).eq("round_num", 1).eq("country_code", "sarmatia") \
        .limit(1).execute().data[0]
    assert row["nuclear_launch_decision"] is not None

    # Verify consumed missiles are destroyed
    for code in result["consumed_missiles"]:
        u = client.table("unit_states_per_round").select("status") \
            .eq("sim_run_id", sim_run_id).eq("round_num", 1).eq("unit_code", code) \
            .limit(1).execute().data
        if u:
            assert u[0]["status"] == "destroyed", f"{code} should be destroyed (consumed)"

    # Verify events written
    events = client.table("observatory_events").select("event_type,summary") \
        .eq("sim_run_id", sim_run_id).eq("round_num", 1) \
        .eq("event_type", "nuclear_launch").execute().data or []
    assert events, "Expected nuclear_launch event"
    print(f"  [event] {events[0]['summary']}")

    print(f"\n  [NUCLEAR LAUNCH CHAIN COMPLETE]")


def test_nuclear_launch_all_intercepted(client, isolated_run):
    """When all missiles are intercepted, no damage is applied."""
    sim_run_id = isolated_run
    orch = NuclearChainOrchestrator()

    decision = {
        "action_type": "launch_missile",
        "country_code": "sarmatia",
        "round_num": 1,
        "decision": "change",
        "rationale": "Nuclear launch that should be fully intercepted by Columbia defense shield",
        "changes": {
            "warhead": "nuclear",
            "missiles": [
                {"missile_unit_code": "sar_m_06", "target_global_row": 3, "target_global_col": 3},
            ],
        },
    }

    init = orch.initiate(decision, sim_run_id, round_num=1, initiator_role_id="pathfinder")
    action_id = init["action_id"]

    orch.submit_authorization(action_id, "ironhand", confirm=True, rationale="x" * 30)
    orch.submit_authorization(action_id, "compass", confirm=True, rationale="x" * 30)

    client.table("nuclear_actions").update(
        {"status": "awaiting_interception"}
    ).eq("id", action_id).execute()
    orch.submit_interception(action_id, "columbia", intercept=True, rationale="x" * 30)

    # All interception rolls succeed → missile destroyed before hit
    result = orch.resolve(action_id, precomputed_rolls={
        "interception_rolls": {"columbia": [0.01, 0.01, 0.01, 0.01]},
        "hit_rolls": [],
    })

    assert result["hits"] == 0
    assert result["missiles_intercepted"] >= 1
    print(f"\n  [all_intercepted] {result['missiles_intercepted']} intercepted, 0 hits")
