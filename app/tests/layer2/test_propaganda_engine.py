"""L2 — Propaganda engine: boost/destabilize + detection + diminishing returns."""

from __future__ import annotations
import pytest
from engine.services.propaganda_engine import execute_propaganda
from engine.services.supabase import get_client
from tests._sim_run_helper import create_isolated_run

SCENARIO = "start_one"


@pytest.fixture
def client():
    return get_client()


@pytest.fixture
def isolated_run(client):
    sim_run_id, cleanup = create_isolated_run(scenario_code=SCENARIO, test_name="propaganda")
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


def test_destabilize_success(client, isolated_run):
    """Destabilize foreign country: stability drops."""
    sim_run_id = isolated_run

    pre = client.table("country_states_per_round").select("stability") \
        .eq("sim_run_id", sim_run_id).eq("round_num", 1).eq("country_code", "sarmatia") \
        .limit(1).execute().data[0]
    pre_stab = int(pre["stability"])

    result = execute_propaganda(
        sim_run_id, 1, "columbia", "shadow", "sarmatia", "destabilize",
        precomputed_rolls={"success_roll": 0.1, "detection_roll": 0.9, "attribution_roll": 0.9},
    )
    assert result["success"] is True
    assert result["stability_change"] < 0
    assert result["detected"] is False
    print(f"\n  [destabilize] sarmatia stability: {pre_stab} → {pre_stab + int(round(result['stability_change']))}")


def test_boost_own_stability(client, isolated_run):
    """Boost own country: stability rises."""
    sim_run_id = isolated_run

    result = execute_propaganda(
        sim_run_id, 1, "columbia", "shadow", "columbia", "boost",
        precomputed_rolls={"success_roll": 0.1, "detection_roll": 0.9, "attribution_roll": 0.9},
    )
    assert result["success"] is True
    assert result["stability_change"] > 0
    print(f"\n  [boost] columbia stability change: {result['stability_change']:+.2f}")


def test_failure_no_change(client, isolated_run):
    """Failed propaganda: no stability change."""
    sim_run_id = isolated_run

    result = execute_propaganda(
        sim_run_id, 1, "columbia", "shadow", "sarmatia", "destabilize",
        precomputed_rolls={"success_roll": 0.9},
    )
    assert result["success"] is False
    assert result["stability_change"] == 0


def test_detected_attributed(client, isolated_run):
    """Success + detected + attributed: public event with attacker name."""
    sim_run_id = isolated_run

    result = execute_propaganda(
        sim_run_id, 1, "columbia", "shadow", "sarmatia", "destabilize",
        precomputed_rolls={"success_roll": 0.1, "detection_roll": 0.1, "attribution_roll": 0.1},
    )
    assert result["detected"] is True
    assert result["attributed"] is True

    events = client.table("observatory_events").select("event_type,summary") \
        .eq("sim_run_id", sim_run_id).eq("country_code", "sarmatia") \
        .eq("event_type", "propaganda_detected_attributed").execute().data or []
    assert events
    assert "columbia" in events[0]["summary"]
    print(f"\n  [attributed] {events[0]['summary']}")
