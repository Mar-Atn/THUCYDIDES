"""L3 — Nuclear chain ACCEPTANCE GATE.

Tests run_unmanned(): the full 4-phase chain with AI officers making
authorization + interception decisions via Gemini Flash.

Scenario: Sarmatia (T3) initiates underground nuclear test.
  → AI officers (ironhand + compass) authorize
  → Engine resolves test success/failure
  → Run finalized as visible_for_review

Cost: ~2-3 LLM calls on Gemini Flash (~ $0.003).
"""

from __future__ import annotations
import pytest

from engine.orchestrators.nuclear_chain import NuclearChainOrchestrator
from engine.services.sim_run_manager import create_run, finalize_run, seed_round_zero
from engine.services.supabase import get_client

SCENARIO = "start_one"
RUN_NAME = "M6-VIS · Nuclear test acceptance gate"


def _seed_round(client, sim_run_id, round_num):
    cs = client.table("country_states_per_round").select("*") \
        .eq("sim_run_id", sim_run_id).eq("round_num", 0).execute()
    if cs.data:
        rows = [{k: v for k, v in r.items() if k != "id"} for r in cs.data]
        for r in rows:
            r["round_num"] = round_num
            r["nuclear_test_decision"] = None
            r["nuclear_launch_decision"] = None
        client.table("country_states_per_round").upsert(
            rows, on_conflict="sim_run_id,round_num,country_code"
        ).execute()


def test_nuclear_test_run_unmanned_ai():
    """Full unmanned chain: AI officers authorize a Sarmatia nuclear test."""
    client = get_client()

    # Idempotency
    prior = client.table("sim_runs").select("id").eq("name", RUN_NAME).execute().data or []
    for p in prior:
        client.table("sim_runs").delete().eq("id", p["id"]).execute()

    sim_run_id = create_run(scenario_code=SCENARIO, name=RUN_NAME,
                             description="M6 acceptance gate: Sarmatia underground nuclear test via run_unmanned")
    seed_round_zero(sim_run_id)
    _seed_round(client, sim_run_id, 1)

    print(f"\n  [acceptance] sim_run_id={sim_run_id}")

    decision = {
        "action_type": "nuclear_test",
        "country_code": "sarmatia",
        "round_num": 1,
        "decision": "change",
        "rationale": "Sarmatia confirms nuclear capability with underground test at homeland missile silo",
        "changes": {
            "test_type": "underground",
            "target_global_row": 2,
            "target_global_col": 16,
        },
    }

    orch = NuclearChainOrchestrator()
    result = orch.run_unmanned(
        decision, sim_run_id, round_num=1,
        initiator_role_id="pathfinder",
        precomputed_rolls={"test_success_roll": 0.10},  # 0.10 < 0.95 → success
    )

    print(f"  [result] outcome={result.get('outcome')}")
    print(f"  success={result.get('success')} test_type={result.get('test_type')}")

    assert result.get("outcome") in ("test_success", "test_failure", "cancelled"), \
        f"Unexpected outcome: {result}"

    if result.get("outcome") == "cancelled":
        print(f"  [NOTE] AI officer rejected — that's a valid outcome")
        print(f"  cancelled_by={result.get('cancelled_by')} rationale={result.get('rationale')}")
    else:
        print(f"  [test resolved] success={result.get('success')}")

        # Verify DB
        actions = client.table("nuclear_actions").select("status,resolution") \
            .eq("sim_run_id", sim_run_id).execute().data or []
        assert actions, "Expected nuclear_actions record"
        assert actions[0]["status"] == "resolved"

    finalize_run(sim_run_id, status="visible_for_review",
                  notes=f"M6 acceptance: {result.get('outcome')}")
    print(f"\n  [ACCEPTANCE GATE PASSED] sim_run_id={sim_run_id}")
