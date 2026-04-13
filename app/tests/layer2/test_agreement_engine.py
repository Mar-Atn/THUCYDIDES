"""L2 — Agreement engine persistence (CONTRACT_AGREEMENTS v1.0)."""

from __future__ import annotations
import pytest
from engine.services.agreement_engine import (
    propose_agreement, sign_agreement,
    get_pending_agreements, get_active_agreements,
)
from engine.services.supabase import get_client
from tests._sim_run_helper import create_isolated_run

SCENARIO = "start_one"


@pytest.fixture
def client():
    return get_client()


@pytest.fixture
def isolated_run(client):
    sim_run_id, cleanup = create_isolated_run(scenario_code=SCENARIO, test_name="agreements")
    yield sim_run_id
    cleanup()


def test_bilateral_propose_sign_activate(client, isolated_run):
    """Columbia proposes ceasefire with Sarmatia. Both sign → ACTIVE."""
    sim_run_id = isolated_run

    proposal = {
        "action_type": "propose_agreement",
        "proposer_role_id": "dealer",
        "proposer_country_code": "columbia",
        "round_num": 1,
        "agreement_name": "Columbia-Sarmatia Ceasefire",
        "agreement_type": "armistice",
        "visibility": "public",
        "terms": "Both parties cease military operations for 3 rounds.",
        "signatories": ["columbia", "sarmatia"],
    }
    result = propose_agreement(proposal, sim_run_id)
    assert result["status"] == "proposed", result
    agr_id = result["agreement_id"]
    print(f"\n  [proposed] {agr_id}")

    # Proposer auto-signed; Sarmatia needs to sign
    pending = get_pending_agreements("sarmatia", sim_run_id)
    assert any(a["id"] == agr_id for a in pending)

    # Sarmatia signs
    sign_result = sign_agreement(agr_id, "sarmatia", "pathfinder", confirm=True,
                                  comments="Sarmatia agrees to ceasefire")
    assert sign_result["status"] == "active"
    assert sign_result["activated"] is True
    print(f"  [activated] ceasefire is now ACTIVE")

    # Verify DB
    agr = client.table("agreements").select("status,signatures") \
        .eq("id", agr_id).execute().data[0]
    assert agr["status"] == "active"
    assert agr["signatures"]["columbia"]["confirmed"] is True
    assert agr["signatures"]["sarmatia"]["confirmed"] is True

    # Verify active agreements
    active = get_active_agreements("columbia", sim_run_id)
    assert any(a["id"] == agr_id for a in active)


def test_multilateral_needs_all_signatures(client, isolated_run):
    """3-country alliance: not active until all 3 sign."""
    sim_run_id = isolated_run

    proposal = {
        "action_type": "propose_agreement",
        "proposer_role_id": "dealer",
        "proposer_country_code": "columbia",
        "round_num": 1,
        "agreement_name": "Pacific Defense Alliance",
        "agreement_type": "military_alliance",
        "visibility": "public",
        "terms": "Columbia, Cathay, and Yamato commit to mutual defense in the Pacific theater.",
        "signatories": ["columbia", "cathay", "yamato"],
    }
    result = propose_agreement(proposal, sim_run_id)
    agr_id = result["agreement_id"]

    # Cathay signs but Yamato hasn't yet → still proposed
    r1 = sign_agreement(agr_id, "cathay", "helmsman", confirm=True)
    assert r1["status"] == "proposed"
    assert r1["activated"] is False
    print(f"\n  [partial] cathay signed, yamato pending")

    # Yamato signs → ACTIVE
    r2 = sign_agreement(agr_id, "yamato", "sakura", confirm=True)
    assert r2["status"] == "active"
    assert r2["activated"] is True
    print(f"  [activated] all 3 signed")


def test_declined_agreement(client, isolated_run):
    """If one signatory declines, agreement status = declined."""
    sim_run_id = isolated_run

    proposal = {
        "action_type": "propose_agreement",
        "proposer_role_id": "dealer",
        "proposer_country_code": "columbia",
        "round_num": 1,
        "agreement_name": "Failed Arms Control",
        "agreement_type": "arms_control",
        "visibility": "secret",
        "terms": "Both freeze nuclear programs at current level.",
        "signatories": ["columbia", "sarmatia"],
    }
    result = propose_agreement(proposal, sim_run_id)
    agr_id = result["agreement_id"]

    # Sarmatia declines
    r = sign_agreement(agr_id, "sarmatia", "pathfinder", confirm=False,
                        comments="Sarmatia will not freeze its nuclear program")
    assert r["status"] == "declined"
    print(f"\n  [declined] sarmatia refused arms control")

    agr = client.table("agreements").select("status") \
        .eq("id", agr_id).execute().data[0]
    assert agr["status"] == "declined"


def test_secret_agreement(client, isolated_run):
    """Secret agreement: visibility=secret stored correctly."""
    sim_run_id = isolated_run

    proposal = {
        "action_type": "propose_agreement",
        "proposer_role_id": "furnace",
        "proposer_country_code": "persia",
        "round_num": 2,
        "agreement_name": "Persia-Cathay Secret Pact",
        "agreement_type": "sanctions_coordination",
        "visibility": "secret",
        "terms": "Coordinate sanctions on Columbia at L2.",
        "signatories": ["persia", "cathay"],
    }
    result = propose_agreement(proposal, sim_run_id)
    agr_id = result["agreement_id"]

    sign_agreement(agr_id, "cathay", "helmsman", confirm=True)

    agr = client.table("agreements").select("visibility,status") \
        .eq("id", agr_id).execute().data[0]
    assert agr["visibility"] == "secret"
    assert agr["status"] == "active"
    print(f"\n  [secret] Persia-Cathay sanctions coordination — secret and active")
