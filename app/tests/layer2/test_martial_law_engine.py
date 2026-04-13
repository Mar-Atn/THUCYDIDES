"""L2 — Martial law engine: spawn conscripts + costs + one-time flag."""

from __future__ import annotations
import pytest

from engine.services.martial_law_engine import execute_martial_law
from engine.services.supabase import get_client
from tests._sim_run_helper import create_isolated_run

SCENARIO = "start_one"


@pytest.fixture
def client():
    return get_client()


@pytest.fixture
def isolated_run(client):
    sim_run_id, cleanup = create_isolated_run(scenario_code=SCENARIO, test_name="martial_law")
    # Seed R1 country states
    cs = client.table("country_states_per_round").select("*") \
        .eq("sim_run_id", sim_run_id).eq("round_num", 0).execute()
    if cs.data:
        rows = [{k: v for k, v in r.items() if k != "id"} for r in cs.data]
        for r in rows:
            r["round_num"] = 1
            r["martial_law_declared"] = False
        client.table("country_states_per_round").upsert(
            rows, on_conflict="sim_run_id,round_num,country_code"
        ).execute()
    yield sim_run_id
    cleanup()


def test_martial_law_spawns_units(client, isolated_run):
    """Sarmatia declares martial law: 10 conscripts spawned as reserve."""
    sim_run_id = isolated_run

    result = execute_martial_law(sim_run_id, "sarmatia", round_num=1)
    assert result["success"]
    assert result["units_spawned"] == 10
    assert len(result["unit_codes"]) == 10
    print(f"\n  [spawned] {result['units_spawned']} units: {result['unit_codes'][:3]}...")

    # Verify units exist in DB
    conscripts = client.table("unit_states_per_round").select("unit_code,status,country_code") \
        .eq("sim_run_id", sim_run_id).eq("round_num", 1) \
        .like("unit_code", "sar_conscript_%").execute().data or []
    assert len(conscripts) == 10
    assert all(c["status"] == "reserve" for c in conscripts)
    assert all(c["country_code"] == "sarmatia" for c in conscripts)


def test_martial_law_applies_costs(client, isolated_run):
    """Stability -1.0 and war tiredness +1.0 applied."""
    sim_run_id = isolated_run

    # Get baseline
    pre = client.table("country_states_per_round").select("stability,war_tiredness") \
        .eq("sim_run_id", sim_run_id).eq("round_num", 1).eq("country_code", "sarmatia") \
        .limit(1).execute().data[0]
    pre_stab = float(pre["stability"])
    pre_wt = float(pre["war_tiredness"])

    execute_martial_law(sim_run_id, "sarmatia", round_num=1)

    post = client.table("country_states_per_round").select("stability,war_tiredness,martial_law_declared") \
        .eq("sim_run_id", sim_run_id).eq("round_num", 1).eq("country_code", "sarmatia") \
        .limit(1).execute().data[0]

    assert float(post["stability"]) == pytest.approx(pre_stab - 1.0)
    assert float(post["war_tiredness"]) == pytest.approx(pre_wt + 1.0)
    assert post["martial_law_declared"] is True
    print(f"\n  [costs] stability: {pre_stab}→{post['stability']}, "
          f"war_tiredness: {pre_wt}→{post['war_tiredness']}, declared=True")


def test_martial_law_event_written(client, isolated_run):
    """Event logged as martial_law_declared."""
    sim_run_id = isolated_run

    execute_martial_law(sim_run_id, "sarmatia", round_num=1)

    events = client.table("observatory_events").select("event_type,summary") \
        .eq("sim_run_id", sim_run_id).eq("event_type", "martial_law_declared").execute().data or []
    assert events
    assert "10 conscript" in events[0]["summary"]
    print(f"\n  [event] {events[0]['summary']}")
