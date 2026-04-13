"""L2 — Arrest engine: request → execute → auto-release at round end."""

from __future__ import annotations
import pytest

from engine.services.arrest_engine import request_arrest, release_arrested_roles
from engine.services.run_roles import seed_run_roles, get_run_role
from engine.services.supabase import get_client
from tests._sim_run_helper import create_isolated_run

SCENARIO = "start_one"


@pytest.fixture
def client():
    return get_client()


@pytest.fixture
def isolated_run(client):
    sim_run_id, cleanup = create_isolated_run(scenario_code=SCENARIO, test_name="arrest")
    seed_run_roles(sim_run_id)
    yield sim_run_id
    cleanup()


def test_arrest_full_chain(client, isolated_run):
    """HoS arrests a role → status=arrested → auto-release at round end."""
    sim_run_id = isolated_run

    # Arrest shadow
    result = request_arrest(
        sim_run_id, "dealer", "shadow",
        justification="Suspected of leaking classified intelligence to foreign agents",
        round_num=2,
    )
    assert result["success"]
    assert result["status"] == "arrested"
    print(f"\n  [arrested] {result['arrested_role']}: {result['message']}")

    # Verify in DB
    shadow = get_run_role(sim_run_id, "shadow")
    assert shadow["status"] == "arrested"
    assert shadow["status_changed_by"] == "dealer"

    # Auto-release at round end
    released = release_arrested_roles(sim_run_id, round_num=2)
    assert "shadow" in released
    print(f"  [released] {released}")

    # Verify released
    shadow2 = get_run_role(sim_run_id, "shadow")
    assert shadow2["status"] == "active"


def test_arrest_non_hos_rejected(client, isolated_run):
    """Non-HoS cannot arrest."""
    sim_run_id = isolated_run

    result = request_arrest(sim_run_id, "shield", "shadow",
                             justification="x" * 30, round_num=2)
    assert not result["success"]
    assert "not HoS" in result["message"]
    print(f"\n  [blocked] shield cannot arrest: {result['message']}")


def test_arrest_wrong_country_rejected(client, isolated_run):
    """Cannot arrest someone from another country."""
    sim_run_id = isolated_run

    result = request_arrest(sim_run_id, "dealer", "ironhand",
                             justification="x" * 30, round_num=2)
    assert not result["success"]
    assert "different country" in result["message"]


def test_arrest_already_arrested(client, isolated_run):
    """Cannot arrest someone already arrested."""
    sim_run_id = isolated_run

    request_arrest(sim_run_id, "dealer", "shadow",
                    justification="First arrest", round_num=2)

    result = request_arrest(sim_run_id, "dealer", "shadow",
                             justification="Second arrest attempt", round_num=2)
    assert not result["success"]
    assert "already arrested" in result["message"]
    print(f"\n  [blocked] already arrested: {result['message']}")


def test_release_only_arrested(client, isolated_run):
    """Release only releases arrested roles, not active ones."""
    sim_run_id = isolated_run

    request_arrest(sim_run_id, "dealer", "shadow",
                    justification="Testing release scope", round_num=3)

    released = release_arrested_roles(sim_run_id, round_num=3)
    assert "shadow" in released
    assert "dealer" not in released  # dealer was never arrested
