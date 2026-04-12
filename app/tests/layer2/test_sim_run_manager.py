"""L2 tests for engine/services/sim_run_manager.py.

These are integration tests — they hit the real Supabase DB because the
service's whole purpose is to own DB lifecycle. Each test creates and
cascade-deletes its own sim_run so the suite is self-cleaning.
"""

from __future__ import annotations

import pytest

from engine.services.supabase import get_client
from engine.services.sim_run_manager import (
    create_run,
    finalize_run,
    get_run,
    list_runs,
    seed_round_zero,
)


SCENARIO = "start_one"
EXPECTED_COUNTRIES = 20
EXPECTED_UNITS = 345  # per SEED_C_MAP_UNITS_MASTER_v1


@pytest.fixture
def client():
    return get_client()


@pytest.fixture
def run_id(client):
    """Create a fresh run, yield its id, then cascade-delete it."""
    rid = create_run(
        scenario_code=SCENARIO,
        name="L2 test fixture",
        description="sim_run_manager test",
        seed=1234,
    )
    yield rid
    client.table("sim_runs").delete().eq("id", rid).execute()


# ---------------------------------------------------------------------------
# create_run
# ---------------------------------------------------------------------------


def test_create_run_binds_scenario_and_defaults(client, run_id):
    row = get_run(run_id)
    assert row["name"] == "L2 test fixture"
    assert row["status"] == "setup"
    assert row["current_round"] == 0
    assert row["current_phase"] == "pre"
    assert row["seed"] == 1234
    # Scenario FK should resolve to start_one
    sc = client.table("sim_scenarios").select("code").eq("id", row["scenario_id"]).execute()
    assert sc.data and sc.data[0]["code"] == SCENARIO


def test_create_run_rejects_unknown_scenario():
    with pytest.raises(ValueError, match="not found"):
        create_run(scenario_code="no_such_scenario", name="bad")


# ---------------------------------------------------------------------------
# seed_round_zero
# ---------------------------------------------------------------------------


def test_seed_round_zero_copies_template_state(client, run_id):
    counts = seed_round_zero(run_id)
    assert counts["country_states"] == EXPECTED_COUNTRIES
    assert counts["unit_states"] == EXPECTED_UNITS
    assert counts["global_state"] == 1

    # DB reflects the copies, scoped to this run
    n_country = (
        client.table("country_states_per_round")
        .select("id", count="exact")
        .eq("sim_run_id", run_id).eq("round_num", 0)
        .execute().count
    )
    n_units = (
        client.table("unit_states_per_round")
        .select("id", count="exact")
        .eq("sim_run_id", run_id).eq("round_num", 0)
        .execute().count
    )
    assert n_country == EXPECTED_COUNTRIES
    assert n_units == EXPECTED_UNITS


def test_seed_round_zero_is_isolated_from_legacy(client, run_id):
    """The new run's R0 rows must NOT share ids with the legacy run's rows."""
    seed_round_zero(run_id)
    legacy_run_id = "00000000-0000-0000-0000-000000000001"
    # Same (round_num, country_code) can exist under both runs — that's the point
    legacy_count = (
        client.table("country_states_per_round")
        .select("id", count="exact")
        .eq("sim_run_id", legacy_run_id).eq("round_num", 0)
        .execute().count
    )
    new_count = (
        client.table("country_states_per_round")
        .select("id", count="exact")
        .eq("sim_run_id", run_id).eq("round_num", 0)
        .execute().count
    )
    assert legacy_count == EXPECTED_COUNTRIES
    assert new_count == EXPECTED_COUNTRIES


def test_seed_round_zero_rejects_self_source(run_id):
    with pytest.raises(ValueError, match="must differ"):
        seed_round_zero(run_id, source_run_id=run_id)


# ---------------------------------------------------------------------------
# finalize_run / get_run / list_runs
# ---------------------------------------------------------------------------


def test_finalize_sets_status_and_timestamp(run_id):
    finalize_run(run_id, status="visible_for_review", notes="slice smoke")
    row = get_run(run_id)
    assert row["status"] == "visible_for_review"
    assert row["finalized_at"] is not None
    assert "slice smoke" in (row["description"] or "")


def test_finalize_rejects_invalid_status(run_id):
    with pytest.raises(ValueError, match="Invalid status"):
        finalize_run(run_id, status="not_a_status")


def test_list_runs_filters_by_status(run_id):
    finalize_run(run_id, status="visible_for_review")
    rows = list_runs(scenario_code=SCENARIO, status="visible_for_review", limit=50)
    assert any(r["id"] == run_id for r in rows)
    # And the opposite filter should NOT include it
    rows_other = list_runs(scenario_code=SCENARIO, status="aborted", limit=50)
    assert all(r["id"] != run_id for r in rows_other)


def test_cascade_delete_removes_child_rows(client):
    """Deleting a sim_run must cascade to per-round snapshots."""
    rid = create_run(scenario_code=SCENARIO, name="cascade test")
    seed_round_zero(rid)
    assert (
        client.table("country_states_per_round")
        .select("id", count="exact")
        .eq("sim_run_id", rid).execute().count
    ) == EXPECTED_COUNTRIES
    client.table("sim_runs").delete().eq("id", rid).execute()
    # Cascade should leave zero children
    assert (
        client.table("country_states_per_round")
        .select("id", count="exact")
        .eq("sim_run_id", rid).execute().count
    ) == 0
    assert (
        client.table("unit_states_per_round")
        .select("id", count="exact")
        .eq("sim_run_id", rid).execute().count
    ) == 0
