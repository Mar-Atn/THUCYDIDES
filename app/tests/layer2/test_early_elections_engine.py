"""L2 — Early elections engine: HoS calls elections for next round."""

from __future__ import annotations
import pytest
from engine.services.early_elections_engine import execute_early_elections
from engine.services.run_roles import seed_run_roles, get_run_role
from engine.services.supabase import get_client
from tests._sim_run_helper import create_isolated_run

SCENARIO = "start_one"


@pytest.fixture
def client():
    return get_client()


@pytest.fixture
def isolated_run(client):
    sim_run_id, cleanup = create_isolated_run(scenario_code=SCENARIO, test_name="elections")
    seed_run_roles(sim_run_id)
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


def test_hos_calls_early_elections(client, isolated_run):
    """HoS successfully calls early elections — flag set, event written."""
    sim_run_id = isolated_run

    # pathfinder is HoS of sarmatia
    result = execute_early_elections(sim_run_id, 1, "pathfinder", "sarmatia")
    assert result["success"]
    assert result["election_round"] == 2
    print(f"\n  [called] {result['narrative']}")

    # Verify flag in DB
    row = client.table("country_states_per_round").select("early_election_called") \
        .eq("sim_run_id", sim_run_id).eq("round_num", 1).eq("country_code", "sarmatia") \
        .limit(1).execute().data
    assert row and row[0]["early_election_called"] is True

    # Verify observatory event
    events = client.table("observatory_events").select("event_type,summary") \
        .eq("sim_run_id", sim_run_id).eq("event_type", "early_elections_called").execute().data
    assert len(events) >= 1
    print(f"  event: {events[0]['summary']}")


def test_non_hos_blocked(client, isolated_run):
    """Non-HoS role cannot call early elections."""
    sim_run_id = isolated_run

    # ironhand is NOT HoS of sarmatia
    result = execute_early_elections(sim_run_id, 1, "ironhand", "sarmatia")
    assert not result["success"]
    assert "not Head of State" in result["narrative"]
    print(f"\n  [blocked] {result['narrative']}")


def test_inactive_role_blocked(client, isolated_run):
    """Arrested/killed role cannot call elections."""
    sim_run_id = isolated_run

    # Arrest pathfinder first
    from engine.services.run_roles import update_role_status
    update_role_status(sim_run_id, "pathfinder", "arrested",
                       changed_by="test", reason="test arrest", round_num=1)

    result = execute_early_elections(sim_run_id, 1, "pathfinder", "sarmatia")
    assert not result["success"]
    assert "not active" in result["narrative"]
    print(f"\n  [blocked] {result['narrative']}")
