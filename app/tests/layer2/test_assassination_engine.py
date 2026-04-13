"""L2 — Assassination engine: success/kill/survive + attribution."""

from __future__ import annotations
import pytest
from engine.services.assassination_engine import execute_assassination
from engine.services.run_roles import seed_run_roles, get_run_role
from engine.services.supabase import get_client
from tests._sim_run_helper import create_isolated_run

SCENARIO = "start_one"


@pytest.fixture
def client():
    return get_client()


@pytest.fixture
def isolated_run(client):
    sim_run_id, cleanup = create_isolated_run(scenario_code=SCENARIO, test_name="assassination")
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


def test_assassination_kill(client, isolated_run):
    """Deterministic success + kill: target status=killed, support +15."""
    sim_run_id = isolated_run

    pre_sup = int(client.table("country_states_per_round").select("political_support") \
        .eq("sim_run_id", sim_run_id).eq("round_num", 1).eq("country_code", "persia") \
        .limit(1).execute().data[0]["political_support"])

    result = execute_assassination(
        sim_run_id, 1, "shadow", "columbia", "furnace", domestic=False,
        precomputed_rolls={"success_roll": 0.05, "kill_roll": 0.1, "attribution_roll": 0.1},
    )
    assert result["success"]
    assert result["killed"]
    assert result["attributed"]
    assert result["support_change"] == 15
    print(f"\n  [killed] {result['narrative']}")

    # Verify role status
    furnace = get_run_role(sim_run_id, "furnace")
    assert furnace["status"] == "killed"

    # Verify support boost
    post_sup = int(client.table("country_states_per_round").select("political_support") \
        .eq("sim_run_id", sim_run_id).eq("round_num", 1).eq("country_code", "persia") \
        .limit(1).execute().data[0]["political_support"])
    assert post_sup == pre_sup + 15


def test_assassination_survive(client, isolated_run):
    """Success but survive: target alive, support +10."""
    sim_run_id = isolated_run

    result = execute_assassination(
        sim_run_id, 1, "shadow", "columbia", "anvil", domestic=False,
        precomputed_rolls={"success_roll": 0.05, "kill_roll": 0.9, "attribution_roll": 0.9},
    )
    assert result["success"]
    assert not result["killed"]
    assert not result["attributed"]
    assert result["support_change"] == 10
    print(f"\n  [survived] {result['narrative']}")

    anvil = get_run_role(sim_run_id, "anvil")
    assert anvil["status"] == "active"  # survived


def test_assassination_failure(client, isolated_run):
    """Failed attempt: no damage, still detected (100%)."""
    sim_run_id = isolated_run

    result = execute_assassination(
        sim_run_id, 1, "shadow", "columbia", "furnace", domestic=False,
        precomputed_rolls={"success_roll": 0.9},
    )
    assert not result["success"]
    assert result["detected"]  # always 100%
    assert result["support_change"] == 0
    print(f"\n  [failed] {result['narrative']}")


def test_domestic_higher_probability(client, isolated_run):
    """Domestic attempt uses 30% probability (higher than international 20%)."""
    sim_run_id = isolated_run

    # Roll 0.25: fails international (0.25 > 0.20) but succeeds domestic (0.25 < 0.30)
    result = execute_assassination(
        sim_run_id, 1, "dealer", "columbia", "shadow", domestic=True,
        precomputed_rolls={"success_roll": 0.25, "kill_roll": 0.9, "attribution_roll": 0.9},
    )
    assert result["success"]  # 0.25 < 0.30 domestic threshold
    print(f"\n  [domestic] {result['narrative']}")
