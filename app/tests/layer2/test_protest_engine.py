"""L2 — Mass protest engine: success/failure + HoS swap + leader arrest."""

from __future__ import annotations
import pytest
from engine.services.protest_engine import execute_mass_protest
from engine.services.run_roles import seed_run_roles, get_run_role
from engine.services.supabase import get_client
from tests._sim_run_helper import create_isolated_run

SCENARIO = "start_one"


@pytest.fixture
def client():
    return get_client()


@pytest.fixture
def isolated_run(client):
    sim_run_id, cleanup = create_isolated_run(scenario_code=SCENARIO, test_name="protest")
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


def _set_country_conditions(client, sim_run_id, country_code, stability, support):
    """Set stability + support to enable/disable protest prerequisites."""
    client.table("country_states_per_round").update({
        "stability": stability,
        "political_support": support,
    }).eq("sim_run_id", sim_run_id).eq("round_num", 1) \
      .eq("country_code", country_code).execute()


def test_protest_success(client, isolated_run):
    """Deterministic success: leader becomes HoS, old HoS deposed."""
    sim_run_id = isolated_run

    # Set conditions to meet prerequisites: stability ≤ 2 AND support < 20
    _set_country_conditions(client, sim_run_id, "sarmatia", stability=1, support=10)

    pre_stab = 1
    pre_sup = 10

    result = execute_mass_protest(
        sim_run_id, 1, "ironhand", "sarmatia",
        precomputed_rolls={"success_roll": 0.01},
    )
    assert result["success"]
    print(f"\n  [success] {result['narrative']}")
    print(f"  probability: {result['probability']*100:.0f}%")

    # Verify ironhand is now HoS
    ironhand = get_run_role(sim_run_id, "ironhand")
    assert ironhand["is_head_of_state"] is True

    # Verify pathfinder (old HoS) deposed
    pathfinder = get_run_role(sim_run_id, "pathfinder")
    assert pathfinder["status"] == "deposed"
    assert pathfinder["is_head_of_state"] is False

    # Stability +1, support +20
    row = client.table("country_states_per_round").select("stability,political_support") \
        .eq("sim_run_id", sim_run_id).eq("round_num", 1).eq("country_code", "sarmatia") \
        .limit(1).execute().data[0]
    assert int(row["stability"]) == pre_stab + 1
    assert int(row["political_support"]) == pre_sup + 20


def test_protest_failure(client, isolated_run):
    """Failed protest: leader imprisoned, stability -1, support -5."""
    sim_run_id = isolated_run

    _set_country_conditions(client, sim_run_id, "sarmatia", stability=2, support=15)

    result = execute_mass_protest(
        sim_run_id, 1, "ironhand", "sarmatia",
        precomputed_rolls={"success_roll": 0.99},
    )
    assert not result["success"]
    print(f"\n  [failed] {result['narrative']}")

    # Leader arrested
    ironhand = get_run_role(sim_run_id, "ironhand")
    assert ironhand["status"] == "arrested"

    # Stability -1, support -5
    row = client.table("country_states_per_round").select("stability,political_support") \
        .eq("sim_run_id", sim_run_id).eq("round_num", 1).eq("country_code", "sarmatia") \
        .limit(1).execute().data[0]
    assert int(row["stability"]) == 2 - 1  # was 2, now 1
    assert int(row["political_support"]) == 15 - 5  # was 15, now 10


def test_protest_blocked_high_stability(client, isolated_run):
    """Stability > 2 blocks protest."""
    sim_run_id = isolated_run

    _set_country_conditions(client, sim_run_id, "sarmatia", stability=5, support=10)

    result = execute_mass_protest(
        sim_run_id, 1, "ironhand", "sarmatia",
    )
    assert not result["success"]
    assert "stability" in result["narrative"].lower() or "Stability" in result["narrative"]
    print(f"\n  [blocked] {result['narrative']}")


def test_protest_blocked_high_support(client, isolated_run):
    """Support >= 20% blocks protest."""
    sim_run_id = isolated_run

    _set_country_conditions(client, sim_run_id, "sarmatia", stability=1, support=25)

    result = execute_mass_protest(
        sim_run_id, 1, "ironhand", "sarmatia",
    )
    assert not result["success"]
    assert "support" in result["narrative"].lower() or "Support" in result["narrative"]
    print(f"\n  [blocked] {result['narrative']}")


def test_protest_probability_calculation(client, isolated_run):
    """Verify probability formula: 30% + (20-support)/100 + (3-stability)*10%."""
    sim_run_id = isolated_run

    # stability=0, support=0 → 0.30 + 0.20 + 0.30 = 0.80 (max clamp)
    _set_country_conditions(client, sim_run_id, "sarmatia", stability=0, support=0)

    result = execute_mass_protest(
        sim_run_id, 1, "ironhand", "sarmatia",
        precomputed_rolls={"success_roll": 0.79},
    )
    assert result["success"]
    assert result["probability"] == 0.80  # clamped at max
    print(f"\n  [max prob] probability={result['probability']*100:.0f}%")
