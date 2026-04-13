"""L2 — Coup engine: success/failure + HoS swap + conspirator arrest."""

from __future__ import annotations
import pytest
from engine.services.coup_engine import execute_coup
from engine.services.run_roles import seed_run_roles, get_run_role
from engine.services.supabase import get_client
from tests._sim_run_helper import create_isolated_run

SCENARIO = "start_one"


@pytest.fixture
def client():
    return get_client()


@pytest.fixture
def isolated_run(client):
    sim_run_id, cleanup = create_isolated_run(scenario_code=SCENARIO, test_name="coup")
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


def test_coup_success(client, isolated_run):
    """Deterministic success: ironhand becomes HoS, pathfinder arrested."""
    sim_run_id = isolated_run

    pre_stab = int(client.table("country_states_per_round").select("stability") \
        .eq("sim_run_id", sim_run_id).eq("round_num", 1).eq("country_code", "sarmatia") \
        .limit(1).execute().data[0]["stability"])

    result = execute_coup(
        sim_run_id, 1, "ironhand", "compass", "sarmatia",
        precomputed_rolls={"success_roll": 0.01},
        co_conspirator_agrees=True,
    )
    assert result["success"]
    assert result["co_conspirator_agreed"]
    print(f"\n  [success] {result['narrative']}")
    print(f"  probability: {result['probability']*100:.0f}%")

    # Verify ironhand is now HoS
    ironhand = get_run_role(sim_run_id, "ironhand")
    assert ironhand["is_head_of_state"] is True

    # Verify pathfinder arrested
    pathfinder = get_run_role(sim_run_id, "pathfinder")
    assert pathfinder["status"] == "arrested"
    assert pathfinder["is_head_of_state"] is False

    # Stability -2
    post_stab = int(client.table("country_states_per_round").select("stability") \
        .eq("sim_run_id", sim_run_id).eq("round_num", 1).eq("country_code", "sarmatia") \
        .limit(1).execute().data[0]["stability"])
    assert post_stab == pre_stab - 2


def test_coup_failure(client, isolated_run):
    """Failed coup: both conspirators arrested, stability -1."""
    sim_run_id = isolated_run

    result = execute_coup(
        sim_run_id, 1, "ironhand", "compass", "sarmatia",
        precomputed_rolls={"success_roll": 0.99},
        co_conspirator_agrees=True,
    )
    assert not result["success"]
    print(f"\n  [failed] {result['narrative']}")

    ironhand = get_run_role(sim_run_id, "ironhand")
    compass = get_run_role(sim_run_id, "compass")
    assert ironhand["status"] == "arrested"
    assert compass["status"] == "arrested"


def test_co_conspirator_refuses(client, isolated_run):
    """Co-conspirator declines: no coup attempt."""
    sim_run_id = isolated_run

    result = execute_coup(
        sim_run_id, 1, "ironhand", "compass", "sarmatia",
        co_conspirator_agrees=False,
    )
    assert not result["success"]
    assert result["co_conspirator_agreed"] is False
    print(f"\n  [refused] {result['narrative']}")

    # Nobody arrested
    ironhand = get_run_role(sim_run_id, "ironhand")
    assert ironhand["status"] == "active"


def test_probability_modifiers(client, isolated_run):
    """Low stability + low support increase coup probability."""
    sim_run_id = isolated_run

    # Set low stability + low support
    client.table("country_states_per_round").update({
        "stability": 2, "political_support": 20,
    }).eq("sim_run_id", sim_run_id).eq("round_num", 1) \
      .eq("country_code", "sarmatia").execute()

    result = execute_coup(
        sim_run_id, 1, "ironhand", "compass", "sarmatia",
        precomputed_rolls={"success_roll": 0.35},  # 35% — would fail at base 15% but succeed with modifiers
        co_conspirator_agrees=True,
    )
    # base 15% + stability<3 +15% + support<30% +10% = 40% → 0.35 < 0.40 → success
    assert result["success"]
    assert result["probability"] >= 0.40
    print(f"\n  [modifiers] probability={result['probability']*100:.0f}% (base 15% + modifiers)")
