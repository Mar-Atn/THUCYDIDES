"""L2 — run_roles: seed, query, status changes, personal coins."""

from __future__ import annotations
import pytest

from engine.services.run_roles import (
    seed_run_roles, get_run_role, get_run_roles,
    update_role_status, update_personal_coins,
)
from engine.services.supabase import get_client
from tests._sim_run_helper import create_isolated_run

SCENARIO = "start_one"


@pytest.fixture
def client():
    return get_client()


@pytest.fixture
def isolated_run(client):
    sim_run_id, cleanup = create_isolated_run(scenario_code=SCENARIO, test_name="run_roles")
    yield sim_run_id
    cleanup()


def test_seed_clones_template_roles(client, isolated_run):
    """seed_run_roles copies all template roles into run_roles."""
    sim_run_id = isolated_run
    count = seed_run_roles(sim_run_id)
    assert count > 0
    print(f"\n  [seeded] {count} roles")

    # Check a known role exists
    dealer = get_run_role(sim_run_id, "dealer")
    assert dealer is not None
    assert dealer["country_code"] == "columbia"
    assert dealer["is_head_of_state"] is True
    assert dealer["status"] == "active"
    assert dealer["personal_coins"] >= 0
    print(f"  [dealer] coins={dealer['personal_coins']} status={dealer['status']}")

    # Check multiple countries present
    all_roles = get_run_roles(sim_run_id)
    countries = {r["country_code"] for r in all_roles}
    assert "columbia" in countries
    assert "sarmatia" in countries
    assert "cathay" in countries
    print(f"  [countries] {len(countries)} countries, {len(all_roles)} roles total")


def test_arrest_and_release(client, isolated_run):
    """Arrest a role → status=arrested. Then release → status=active."""
    sim_run_id = isolated_run
    seed_run_roles(sim_run_id)

    # Arrest shadow
    result = update_role_status(
        sim_run_id, "shadow", "arrested",
        changed_by="dealer", reason="Suspected espionage", round_num=2,
    )
    assert result["success"]
    assert result["previous_status"] == "active"
    assert result["new_status"] == "arrested"
    print(f"\n  [arrested] shadow: {result}")

    # Verify
    shadow = get_run_role(sim_run_id, "shadow")
    assert shadow["status"] == "arrested"
    assert shadow["status_changed_round"] == 2
    assert shadow["status_changed_by"] == "dealer"

    # Release at round end
    result2 = update_role_status(
        sim_run_id, "shadow", "active",
        changed_by="system", reason="Released at round end", round_num=2,
    )
    assert result2["success"]
    assert result2["new_status"] == "active"

    shadow2 = get_run_role(sim_run_id, "shadow")
    assert shadow2["status"] == "active"
    print(f"  [released] shadow: active again")


def test_kill_role(client, isolated_run):
    """Assassination success → status=killed."""
    sim_run_id = isolated_run
    seed_run_roles(sim_run_id)

    result = update_role_status(
        sim_run_id, "furnace", "killed",
        changed_by="shadow", reason="Assassination operation successful", round_num=4,
    )
    assert result["success"]
    assert result["new_status"] == "killed"

    furnace = get_run_role(sim_run_id, "furnace")
    assert furnace["status"] == "killed"
    print(f"\n  [killed] furnace: {furnace['status_change_reason']}")


def test_personal_coins(client, isolated_run):
    """Add and spend personal coins."""
    sim_run_id = isolated_run
    seed_run_roles(sim_run_id)

    dealer = get_run_role(sim_run_id, "dealer")
    start_coins = dealer["personal_coins"]

    # Add coins
    result = update_personal_coins(sim_run_id, "dealer", +10)
    assert result["success"]
    assert result["new_balance"] == start_coins + 10

    # Spend coins
    result2 = update_personal_coins(sim_run_id, "dealer", -3)
    assert result2["success"]
    assert result2["new_balance"] == start_coins + 7

    # Cannot go below 0
    result3 = update_personal_coins(sim_run_id, "dealer", -9999)
    assert result3["new_balance"] == 0
    print(f"\n  [coins] dealer: {start_coins} → +10 → -3 → floor 0")


def test_query_by_country(client, isolated_run):
    """Query roles filtered by country."""
    sim_run_id = isolated_run
    seed_run_roles(sim_run_id)

    columbia_roles = get_run_roles(sim_run_id, country_code="columbia")
    assert len(columbia_roles) >= 3  # dealer, shield, shadow, etc.
    assert all(r["country_code"] == "columbia" for r in columbia_roles)


def test_query_by_status(client, isolated_run):
    """Query only active roles after arresting one."""
    sim_run_id = isolated_run
    seed_run_roles(sim_run_id)

    update_role_status(sim_run_id, "shadow", "arrested",
                       changed_by="dealer", reason="test", round_num=1)

    active = get_run_roles(sim_run_id, country_code="columbia", status="active")
    assert not any(r["role_id"] == "shadow" for r in active)
    assert any(r["role_id"] == "dealer" for r in active)
