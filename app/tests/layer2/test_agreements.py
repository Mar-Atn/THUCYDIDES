"""Comprehensive agreement system tests — all types, flows, relationship updates.

Run: cd app && python -m pytest tests/layer2/test_agreements.py -v
"""

import pytest
from engine.services.sim_run_manager import _get_client
from engine.services.agreement_engine import propose_agreement, sign_agreement
from engine.services.sim_create import create_sim_run


@pytest.fixture(scope="module")
def client():
    return _get_client()


@pytest.fixture(scope="module")
def test_sim(client):
    result = create_sim_run(
        name="Agreement Test Sim",
        source_sim_id="00000000-0000-0000-0000-000000000001",
        template_id="3b431689-945b-44d0-89f0-7b32a7f63b47",
        facilitator_id="1b2616bb-955a-4029-b0a1-802a81211b94",
        schedule={"default_rounds": 6}, key_events=[], max_rounds=6,
    )
    sim_id = result["id"]
    client.table("sim_runs").update({"status": "active", "current_round": 1, "current_phase": "A"}).eq("id", sim_id).execute()
    yield sim_id
    for table in ["agreements", "exchange_transactions", "observatory_events", "agent_decisions",
                   "pending_actions", "leadership_votes", "world_state", "tariffs", "sanctions",
                   "org_memberships", "organizations", "deployments", "zones", "role_actions",
                   "roles", "relationships", "countries", "artefacts"]:
        try: client.table(table).delete().eq("sim_run_id", sim_id).execute()
        except: pass
    client.table("sim_runs").delete().eq("id", sim_id).execute()


def get_relationship(client, sim_id, from_cc, to_cc):
    r = client.table("relationships").select("relationship").eq("sim_run_id", sim_id).eq("from_country_id", from_cc).eq("to_country_id", to_cc).execute()
    return r.data[0]["relationship"] if r.data else None


class TestProposalValidation:
    def test_valid_proposal(self, client, test_sim):
        r = propose_agreement({
            "action_type": "propose_agreement", "proposer_country_code": "columbia", "proposer_role_id": "dealer",
            "agreement_name": "Test Alliance", "agreement_type": "military_alliance",
            "signatories": ["columbia", "cathay"], "terms": "Mutual defense pact",
            "visibility": "public", "round_num": 1,
        }, test_sim)
        assert r["status"] == "proposed"
        assert r["agreement_id"]

    def test_missing_name_rejected(self, client, test_sim):
        r = propose_agreement({
            "action_type": "propose_agreement", "proposer_country_code": "columbia", "proposer_role_id": "dealer",
            "agreement_name": "", "agreement_type": "trade_agreement",
            "signatories": ["columbia", "cathay"], "terms": "Trade",
            "visibility": "public", "round_num": 1,
        }, test_sim)
        assert r["status"] == "rejected"

    def test_single_signatory_rejected(self, client, test_sim):
        r = propose_agreement({
            "action_type": "propose_agreement", "proposer_country_code": "columbia", "proposer_role_id": "dealer",
            "agreement_name": "Solo", "agreement_type": "trade_agreement",
            "signatories": ["columbia"], "terms": "Just me",
            "visibility": "public", "round_num": 1,
        }, test_sim)
        assert r["status"] == "rejected"


class TestSigningFlow:
    def test_two_party_sign_activates(self, client, test_sim):
        """Two-party agreement: propose → second signs → active."""
        r = propose_agreement({
            "action_type": "propose_agreement", "proposer_country_code": "sarmatia", "proposer_role_id": "pathfinder",
            "agreement_name": "Sarmatia-Persia Ceasefire", "agreement_type": "ceasefire",
            "signatories": ["sarmatia", "persia"], "terms": "Stop fighting",
            "visibility": "public", "round_num": 1,
        }, test_sim)
        assert r["status"] == "proposed"
        agr_id = r["agreement_id"]

        # Persia signs
        s = sign_agreement(agr_id, "persia", "furnace", True)
        assert s["status"] == "active"
        assert s["activated"] == True

    def test_three_party_needs_all(self, client, test_sim):
        """Three-party: first two sign → still proposed. Third signs → active."""
        r = propose_agreement({
            "action_type": "propose_agreement", "proposer_country_code": "columbia", "proposer_role_id": "dealer",
            "agreement_name": "Trilateral Trade", "agreement_type": "trade_agreement",
            "signatories": ["columbia", "cathay", "teutonia"], "terms": "Free trade zone",
            "visibility": "public", "round_num": 1,
        }, test_sim)
        agr_id = r["agreement_id"]

        # Cathay signs — not yet active (need teutonia)
        s1 = sign_agreement(agr_id, "cathay", "helmsman", True)
        assert s1["status"] == "proposed"
        assert s1["activated"] == False

        # Teutonia signs — NOW active
        s2 = sign_agreement(agr_id, "teutonia", "forge", True)
        assert s2["status"] == "active"
        assert s2["activated"] == True

    def test_decline_kills_agreement(self, client, test_sim):
        """Any signatory declining kills the agreement."""
        r = propose_agreement({
            "action_type": "propose_agreement", "proposer_country_code": "columbia", "proposer_role_id": "dealer",
            "agreement_name": "Failed Pact", "agreement_type": "peace_treaty",
            "signatories": ["columbia", "cathay"], "terms": "Peace",
            "visibility": "public", "round_num": 1,
        }, test_sim)
        agr_id = r["agreement_id"]

        s = sign_agreement(agr_id, "cathay", "helmsman", False)
        assert s["status"] == "declined"

        # Can't sign after decline
        s2 = sign_agreement(agr_id, "cathay", "helmsman", True)
        assert s2["status"] != "active"

    def test_non_signatory_blocked(self, client, test_sim):
        """Country not in signatories list can't sign."""
        r = propose_agreement({
            "action_type": "propose_agreement", "proposer_country_code": "columbia", "proposer_role_id": "dealer",
            "agreement_name": "Exclusive Deal", "agreement_type": "military_alliance",
            "signatories": ["columbia", "cathay"], "terms": "Alliance",
            "visibility": "public", "round_num": 1,
        }, test_sim)
        agr_id = r["agreement_id"]

        s = sign_agreement(agr_id, "sarmatia", "pathfinder", True)
        assert s["status"] == "error"
        assert any("not a signatory" in e for e in s.get("errors", []))


class TestRelationshipUpdate:
    """Test that agreement activation auto-updates relationships."""

    def test_military_alliance_sets_alliance(self, client, test_sim):
        before = get_relationship(client, test_sim, "bharata", "formosa")

        r = propose_agreement({
            "action_type": "propose_agreement", "proposer_country_code": "bharata", "proposer_role_id": "scales",
            "agreement_name": "Bharata-Formosa Defense Pact", "agreement_type": "military_alliance",
            "signatories": ["bharata", "formosa"], "terms": "Mutual defense",
            "visibility": "public", "round_num": 1,
        }, test_sim)
        sign_agreement(r["agreement_id"], "formosa", "chip", True)

        after = get_relationship(client, test_sim, "bharata", "formosa")
        assert after == "alliance"

    def test_trade_agreement_sets_partnership(self, client, test_sim):
        r = propose_agreement({
            "action_type": "propose_agreement", "proposer_country_code": "hanguk", "proposer_role_id": "vanguard",
            "agreement_name": "Hanguk-Yamato Trade", "agreement_type": "trade_agreement",
            "signatories": ["hanguk", "yamato"], "terms": "Semiconductor trade",
            "visibility": "public", "round_num": 1,
        }, test_sim)
        sign_agreement(r["agreement_id"], "yamato", "sakura", True)

        after = get_relationship(client, test_sim, "hanguk", "yamato")
        assert after == "economic_partnership"

    def test_ceasefire_sets_hostile(self, client, test_sim):
        # First set to at_war
        client.table("relationships").update({"relationship": "at_war"}).eq("sim_run_id", test_sim).eq("from_country_id", "levantia").eq("to_country_id", "persia").execute()
        client.table("relationships").update({"relationship": "at_war"}).eq("sim_run_id", test_sim).eq("from_country_id", "persia").eq("to_country_id", "levantia").execute()

        r = propose_agreement({
            "action_type": "propose_agreement", "proposer_country_code": "levantia", "proposer_role_id": "citadel",
            "agreement_name": "Mashriq Ceasefire", "agreement_type": "ceasefire",
            "signatories": ["levantia", "persia"], "terms": "Stop hostilities",
            "visibility": "public", "round_num": 1,
        }, test_sim)
        sign_agreement(r["agreement_id"], "persia", "furnace", True)

        after = get_relationship(client, test_sim, "levantia", "persia")
        assert after == "hostile"

    def test_peace_treaty_sets_neutral(self, client, test_sim):
        r = propose_agreement({
            "action_type": "propose_agreement", "proposer_country_code": "albion", "proposer_role_id": "mariner",
            "agreement_name": "Albion-Phrygia Peace", "agreement_type": "peace_treaty",
            "signatories": ["albion", "phrygia"], "terms": "Lasting peace",
            "visibility": "public", "round_num": 1,
        }, test_sim)
        sign_agreement(r["agreement_id"], "phrygia", "vizier", True)

        after = get_relationship(client, test_sim, "albion", "phrygia")
        assert after == "neutral"

    def test_higher_priority_not_downgraded(self, client, test_sim):
        """Alliance should not be downgraded by trade agreement."""
        # Set alliance first
        client.table("relationships").update({"relationship": "alliance"}).eq("sim_run_id", test_sim).eq("from_country_id", "caribe").eq("to_country_id", "mirage").execute()
        client.table("relationships").update({"relationship": "alliance"}).eq("sim_run_id", test_sim).eq("from_country_id", "mirage").eq("to_country_id", "caribe").execute()

        r = propose_agreement({
            "action_type": "propose_agreement", "proposer_country_code": "caribe", "proposer_role_id": "havana",
            "agreement_name": "Caribe-Mirage Trade", "agreement_type": "trade_agreement",
            "signatories": ["caribe", "mirage"], "terms": "Oil trade",
            "visibility": "public", "round_num": 1,
        }, test_sim)
        sign_agreement(r["agreement_id"], "mirage", "spire", True)

        after = get_relationship(client, test_sim, "caribe", "mirage")
        # Should still be alliance (higher priority than economic_partnership)
        assert after == "alliance"


class TestVisibility:
    def test_public_agreement_creates_event(self, client, test_sim):
        r = propose_agreement({
            "action_type": "propose_agreement", "proposer_country_code": "columbia", "proposer_role_id": "dealer",
            "agreement_name": "Public Deal", "agreement_type": "trade_agreement",
            "signatories": ["columbia", "persia"], "terms": "Public terms",
            "visibility": "public", "round_num": 1,
        }, test_sim)
        assert r["status"] == "proposed"

        evts = client.table("observatory_events").select("event_type").eq("sim_run_id", test_sim).eq("event_type", "agreement_proposed").execute()
        assert len(evts.data) > 0

    def test_secret_agreement_stored(self, client, test_sim):
        r = propose_agreement({
            "action_type": "propose_agreement", "proposer_country_code": "columbia", "proposer_role_id": "dealer",
            "agreement_name": "Secret Deal", "agreement_type": "military_alliance",
            "signatories": ["columbia", "sarmatia"], "terms": "Secret alliance",
            "visibility": "secret", "round_num": 1,
        }, test_sim)
        assert r["status"] == "proposed"

        agr = client.table("agreements").select("visibility").eq("id", r["agreement_id"]).execute()
        assert agr.data[0]["visibility"] == "secret"
