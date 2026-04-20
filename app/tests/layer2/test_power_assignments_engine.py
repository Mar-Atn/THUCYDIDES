"""L2 — Power assignments engine: seed, check, reassign against live DB."""

from __future__ import annotations
import pytest

from engine.services.power_assignments import (
    seed_defaults, check_authorization, reassign_power, get_assignments,
)
from engine.services.supabase import get_client
from tests._sim_run_helper import create_isolated_run

SCENARIO = "start_one"

ROLES = {
    "dealer": {"is_head_of_state": True, "country_code": "columbia"},
    "shield": {"is_head_of_state": False, "is_military_chief": True, "country_code": "columbia"},
    "volt": {"is_head_of_state": False, "country_code": "columbia"},
    "anchor": {"is_head_of_state": False, "country_code": "columbia"},
    "shadow": {"is_head_of_state": False, "country_code": "columbia"},
    "pathfinder": {"is_head_of_state": True, "country_code": "sarmatia"},
}


@pytest.fixture
def client():
    return get_client()


@pytest.fixture
def isolated_run(client):
    sim_run_id, cleanup = create_isolated_run(scenario_code=SCENARIO, test_name="power_assignments")
    yield sim_run_id
    cleanup()


def test_seed_and_query(client, isolated_run):
    """Seed defaults and verify all 15 assignments exist."""
    sim_run_id = isolated_run
    count = seed_defaults(sim_run_id)
    assert count == 15
    print(f"\n  [seeded] {count} power assignments")

    # Query columbia
    col = get_assignments(sim_run_id, "columbia")
    assert len(col) == 3
    by_type = {a["power_type"]: a["assigned_role_id"] for a in col}
    assert by_type == {"military": "shield", "economic": "volt", "foreign_affairs": "anchor"}
    print(f"  [columbia] {by_type}")


def test_authorization_military_correct_role(client, isolated_run):
    """Shield (military power holder) can move_units."""
    sim_run_id = isolated_run
    seed_defaults(sim_run_id)

    result = check_authorization("shield", "move_units", sim_run_id, "columbia", roles=ROLES)
    assert result["authorized"], result
    print(f"\n  [shield → move_units] {result['reason']}")


def test_authorization_military_wrong_role(client, isolated_run):
    """Volt (economic) cannot move_units."""
    sim_run_id = isolated_run
    seed_defaults(sim_run_id)

    result = check_authorization("volt", "move_units", sim_run_id, "columbia", roles=ROLES)
    assert not result["authorized"]
    assert "shield" in result["reason"]  # tells who actually has the power
    print(f"\n  [volt → move_units] BLOCKED: {result['reason']}")


def test_authorization_economic_correct_role(client, isolated_run):
    """Volt (economic power holder) can set_budget."""
    sim_run_id = isolated_run
    seed_defaults(sim_run_id)

    result = check_authorization("volt", "set_budget", sim_run_id, "columbia", roles=ROLES)
    assert result["authorized"]


def test_authorization_hos_overrides_all(client, isolated_run):
    """Dealer (HoS) can do anything — military, economic, foreign."""
    sim_run_id = isolated_run
    seed_defaults(sim_run_id)

    for action in ["move_units", "set_budget", "propose_agreement"]:
        result = check_authorization("dealer", action, sim_run_id, "columbia", roles=ROLES)
        assert result["authorized"], f"HoS should be authorized for {action}"


def test_reassign_power(client, isolated_run):
    """HoS reassigns military from shield to shadow."""
    sim_run_id = isolated_run
    seed_defaults(sim_run_id)

    result = reassign_power(
        sim_run_id, "columbia", "military",
        new_role_id="shadow",
        by_role_id="dealer",
        round_num=3,
        roles=ROLES,
    )
    assert result["success"]
    assert result["previous_role"] == "shield"
    assert result["new_role"] == "shadow"
    print(f"\n  [reassigned] military: shield → shadow")

    # Now shadow is authorized for military, shield is not
    assert check_authorization("shadow", "move_units", sim_run_id, "columbia", roles=ROLES)["authorized"]
    assert not check_authorization("shield", "move_units", sim_run_id, "columbia", roles=ROLES)["authorized"]


def test_reassign_non_hos_blocked(client, isolated_run):
    """Non-HoS cannot reassign powers."""
    sim_run_id = isolated_run
    seed_defaults(sim_run_id)

    result = reassign_power(
        sim_run_id, "columbia", "military",
        new_role_id="shadow",
        by_role_id="shield",  # not HoS
        round_num=3,
        roles=ROLES,
    )
    assert not result["success"]
    assert "not HoS" in result["message"]


def test_vacate_power(client, isolated_run):
    """HoS vacates a power slot (takes it back)."""
    sim_run_id = isolated_run
    seed_defaults(sim_run_id)

    result = reassign_power(
        sim_run_id, "columbia", "economic",
        new_role_id=None,  # vacate
        by_role_id="dealer",
        round_num=2,
        roles=ROLES,
    )
    assert result["success"]
    assert result["new_role"] is None
    print(f"\n  [vacated] economic: volt → HoS holds")

    # Volt no longer authorized for budget
    assert not check_authorization("volt", "set_budget", sim_run_id, "columbia", roles=ROLES)["authorized"]
    # HoS still can
    assert check_authorization("dealer", "set_budget", sim_run_id, "columbia", roles=ROLES)["authorized"]
