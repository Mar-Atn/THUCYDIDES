"""L2 — Election meddling engine."""

from __future__ import annotations
import pytest
from engine.services.election_meddling_engine import execute_election_meddling
from engine.services.supabase import get_client
from tests._sim_run_helper import create_isolated_run

SCENARIO = "start_one"


@pytest.fixture
def client():
    return get_client()


@pytest.fixture
def isolated_run(client):
    sim_run_id, cleanup = create_isolated_run(scenario_code=SCENARIO, test_name="election_meddling")
    cs = client.table("country_states_per_round").select("*") \
        .eq("sim_run_id", sim_run_id).eq("round_num", 0).execute()
    if cs.data:
        rows = [{k: v for k, v in r.items() if k != "id"} for r in cs.data]
        for r in rows:
            r["round_num"] = 1
        client.table("country_states_per_round").upsert(
            rows, on_conflict="sim_run_id,round_num,country_code"
        ).execute()
    yield sim_run_id
    cleanup()


def test_boost_success(client, isolated_run):
    sim_run_id = isolated_run
    pre = client.table("country_states_per_round").select("political_support") \
        .eq("sim_run_id", sim_run_id).eq("round_num", 1).eq("country_code", "ruthenia") \
        .limit(1).execute().data[0]
    pre_sup = int(pre["political_support"])

    result = execute_election_meddling(
        sim_run_id, 1, "columbia", "shadow", "ruthenia", "boost", candidate="beacon",
        precomputed_rolls={"success_roll": 0.1, "detection_roll": 0.9, "attribution_roll": 0.9, "shift_amount": 4},
    )
    assert result["success"]
    assert result["support_change"] == 4
    assert result["detected"] is False
    print(f"\n  [boost] ruthenia support: {pre_sup} → {pre_sup + 4}")


def test_undermine_success_attributed(client, isolated_run):
    sim_run_id = isolated_run
    result = execute_election_meddling(
        sim_run_id, 1, "columbia", "shadow", "ruthenia", "undermine",
        precomputed_rolls={"success_roll": 0.1, "detection_roll": 0.1, "attribution_roll": 0.1, "shift_amount": 3},
    )
    assert result["success"]
    assert result["support_change"] == -3
    assert result["attributed"] is True

    events = client.table("observatory_events").select("summary") \
        .eq("sim_run_id", sim_run_id).eq("event_type", "election_meddling_detected_attributed") \
        .execute().data or []
    assert events
    assert "columbia" in events[0]["summary"]
    print(f"\n  [undermine attributed] {events[0]['summary']}")


def test_failure(client, isolated_run):
    sim_run_id = isolated_run
    result = execute_election_meddling(
        sim_run_id, 1, "columbia", "shadow", "ruthenia", "boost",
        precomputed_rolls={"success_roll": 0.9},
    )
    assert not result["success"]
    assert result["support_change"] == 0
