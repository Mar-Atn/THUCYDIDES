"""L2 — Basing rights engine persistence.

Full chain: validate → grant/revoke → DB state + events.
"""

from __future__ import annotations
import pytest

from engine.services.basing_rights_engine import (
    grant_basing_rights, revoke_basing_rights, get_active_basing_rights,
)
from engine.services.basing_rights_validator import validate_basing_rights
from engine.services.supabase import get_client
from tests._sim_run_helper import create_isolated_run

SCENARIO = "start_one"


@pytest.fixture
def client():
    return get_client()


@pytest.fixture
def isolated_run(client):
    sim_run_id, cleanup = create_isolated_run(scenario_code=SCENARIO, test_name="basing_rights")
    yield sim_run_id
    cleanup()


def test_grant_and_query(client, isolated_run):
    """Grant basing rights, then verify it appears in active list."""
    sim_run_id = isolated_run

    result = grant_basing_rights(sim_run_id, "columbia", "teutonia", round_num=1,
                                  granted_by_role="dealer", source="direct")
    assert result["success"]
    assert result["status"] == "active"
    print(f"\n  [granted] {result['message']}")

    # Query
    active = get_active_basing_rights(sim_run_id, "columbia")
    assert any(r["guest_country"] == "teutonia" for r in active)

    # Verify DB row
    row = client.table("basing_rights").select("*") \
        .eq("sim_run_id", sim_run_id).eq("host_country", "columbia") \
        .eq("guest_country", "teutonia").execute().data[0]
    assert row["status"] == "active"
    assert row["source"] == "direct"
    assert row["granted_round"] == 1

    # Verify event written
    events = client.table("observatory_events").select("event_type") \
        .eq("sim_run_id", sim_run_id).eq("event_type", "basing_rights_granted").execute().data
    assert events


def test_revoke(client, isolated_run):
    """Grant then revoke basing rights."""
    sim_run_id = isolated_run

    grant_basing_rights(sim_run_id, "columbia", "albion", round_num=1)

    result = revoke_basing_rights(sim_run_id, "columbia", "albion", round_num=3)
    assert result["success"]
    assert result["status"] == "revoked"
    print(f"\n  [revoked] {result['message']}")

    # No longer in active list
    active = get_active_basing_rights(sim_run_id, "columbia")
    assert not any(r["guest_country"] == "albion" for r in active)

    # DB row shows revoked
    row = client.table("basing_rights").select("status,revoked_round") \
        .eq("sim_run_id", sim_run_id).eq("host_country", "columbia") \
        .eq("guest_country", "albion").execute().data[0]
    assert row["status"] == "revoked"
    assert row["revoked_round"] == 3


def test_regrant_after_revoke(client, isolated_run):
    """Revoked basing can be re-granted (upsert reactivates)."""
    sim_run_id = isolated_run

    grant_basing_rights(sim_run_id, "sarmatia", "persia", round_num=1)
    revoke_basing_rights(sim_run_id, "sarmatia", "persia", round_num=2)
    grant_basing_rights(sim_run_id, "sarmatia", "persia", round_num=3)

    row = client.table("basing_rights").select("status,granted_round,revoked_round") \
        .eq("sim_run_id", sim_run_id).eq("host_country", "sarmatia") \
        .eq("guest_country", "persia").execute().data[0]
    assert row["status"] == "active"
    assert row["granted_round"] == 3
    assert row["revoked_round"] is None
    print(f"\n  [re-granted] sarmatia → persia active again at R3")


def test_validator_blocks_revoke_with_troops(client, isolated_run):
    """Validator rejects revoke when guest has forces on host soil."""
    sim_run_id = isolated_run

    # We need units + zones for the validator
    # Use a simple fixture: teutonia unit at (3,3) which is columbia territory
    units = {
        "teu_g_01": {"unit_code": "teu_g_01", "country_code": "teutonia",
                      "unit_type": "ground", "global_row": 3, "global_col": 3, "status": "active"},
    }
    zones = {(3, 3): {"type": "land", "owner": "columbia"}}

    payload = {
        "action_type": "basing_rights",
        "country_code": "columbia",
        "round_num": 3,
        "decision": "change",
        "rationale": "Attempting to revoke basing rights while Teutonia troops are present",
        "changes": {"counterpart_country": "teutonia", "action": "revoke"},
    }
    report = validate_basing_rights(payload, units, zones)
    assert not report["valid"]
    assert any("GUEST_FORCES_PRESENT" in e for e in report["errors"])
    print(f"\n  [blocked] revoke blocked: {report['errors'][0][:80]}")
