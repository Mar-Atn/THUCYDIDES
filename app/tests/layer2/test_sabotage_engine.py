"""L2 — Sabotage engine: success/fail + damage + detection/attribution."""

from __future__ import annotations
import pytest

from engine.services.sabotage_engine import execute_sabotage
from engine.services.supabase import get_client
from tests._sim_run_helper import create_isolated_run

SCENARIO = "start_one"


@pytest.fixture
def client():
    return get_client()


@pytest.fixture
def isolated_run(client):
    sim_run_id, cleanup = create_isolated_run(scenario_code=SCENARIO, test_name="sabotage")
    cs = client.table("country_states_per_round").select("*") \
        .eq("sim_run_id", sim_run_id).eq("round_num", 0).execute()
    if cs.data:
        rows = [{k: v for k, v in r.items() if k != "id"} for r in cs.data]
        for r in rows:
            r["round_num"] = 1
        client.table("country_states_per_round").upsert(
            rows, on_conflict="sim_run_id,round_num,country_code"
        ).execute()
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


def test_infrastructure_sabotage_success(client, isolated_run):
    """Deterministic success: target loses 1 coin, detected + attributed."""
    sim_run_id = isolated_run

    pre = client.table("country_states_per_round").select("treasury") \
        .eq("sim_run_id", sim_run_id).eq("round_num", 1).eq("country_code", "sarmatia") \
        .limit(1).execute().data[0]
    pre_treasury = float(pre["treasury"])

    result = execute_sabotage(
        sim_run_id, 1, "columbia", "shadow", "sarmatia", "infrastructure",
        precomputed_rolls={"success_roll": 0.1, "detection_roll": 0.1, "attribution_roll": 0.1},
    )
    assert result["success"] is True
    assert result["detected"] is True
    assert result["attributed"] is True
    assert "coin" in result["damage"]
    print(f"\n  [infra] {result['narrative']}")

    post = client.table("country_states_per_round").select("treasury") \
        .eq("sim_run_id", sim_run_id).eq("round_num", 1).eq("country_code", "sarmatia") \
        .limit(1).execute().data[0]
    assert float(post["treasury"]) == pytest.approx(pre_treasury - 1)


def test_sabotage_failure_undetected(client, isolated_run):
    """Deterministic failure + not detected: nothing happens, no events for target."""
    sim_run_id = isolated_run

    result = execute_sabotage(
        sim_run_id, 1, "columbia", "shadow", "sarmatia", "infrastructure",
        precomputed_rolls={"success_roll": 0.9, "detection_roll": 0.9, "attribution_roll": 0.9},
    )
    assert result["success"] is False
    assert result["detected"] is False
    assert result["attributed"] is False
    print(f"\n  [fail+hidden] {result['narrative']}")

    # No target event
    events = client.table("observatory_events").select("event_type") \
        .eq("sim_run_id", sim_run_id).eq("country_code", "sarmatia") \
        .like("event_type", "sabotage%").execute().data or []
    assert not events


def test_sabotage_detected_anonymous(client, isolated_run):
    """Success + detected but NOT attributed: target sees 'unknown actor'."""
    sim_run_id = isolated_run

    result = execute_sabotage(
        sim_run_id, 1, "columbia", "shadow", "persia", "nuclear_tech",
        precomputed_rolls={"success_roll": 0.1, "detection_roll": 0.1, "attribution_roll": 0.9},
    )
    assert result["success"] is True
    assert result["detected"] is True
    assert result["attributed"] is False
    print(f"\n  [detected anonymous] {result['narrative']}")

    events = client.table("observatory_events").select("event_type,summary") \
        .eq("sim_run_id", sim_run_id).eq("country_code", "persia") \
        .eq("event_type", "sabotage_detected_anonymous").execute().data or []
    assert events
    assert "unknown actor" in events[0]["summary"]


def test_military_sabotage_destroys_unit(client, isolated_run):
    """Military sabotage: 50% chance to destroy 1 unit (deterministic roll)."""
    sim_run_id = isolated_run

    result = execute_sabotage(
        sim_run_id, 1, "columbia", "shadow", "sarmatia", "military",
        precomputed_rolls={"success_roll": 0.1, "detection_roll": 0.9,
                          "attribution_roll": 0.9, "military_roll": 0.1},
    )
    assert result["success"] is True
    assert result["damage"]  # unit was destroyed
    assert "destroyed" in result["damage"]
    print(f"\n  [military] {result['damage']}")
