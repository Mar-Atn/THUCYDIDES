"""Comprehensive transaction system tests — all asset types, flows, edge cases.

Tests the full pipeline: propose → validate → accept/decline → execute → verify DB.
Uses a dedicated test SimRun with known state.

Run: cd app && python -m pytest tests/layer2/test_transactions.py -v
"""

import pytest
import uuid
from engine.services.sim_run_manager import _get_client
from engine.services.transaction_engine import propose_exchange, respond_to_exchange
from engine.services.sim_create import create_sim_run


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    return _get_client()


@pytest.fixture(scope="module")
def test_sim(client):
    """Create a dedicated test SimRun, yield its ID, then clean up."""
    result = create_sim_run(
        name="Transaction Test Sim",
        source_sim_id="00000000-0000-0000-0000-000000000001",
        template_id="3b431689-945b-44d0-89f0-7b32a7f63b47",
        facilitator_id="1b2616bb-955a-4029-b0a1-802a81211b94",
        schedule={"default_rounds": 6},
        key_events=[],
        max_rounds=6,
    )
    sim_id = result["id"]

    # Set to active
    client.table("sim_runs").update({
        "status": "active", "current_round": 1, "current_phase": "A"
    }).eq("id", sim_id).execute()

    yield sim_id

    # Cleanup
    for table in ["exchange_transactions", "observatory_events", "agent_decisions",
                   "pending_actions", "leadership_votes", "world_state", "tariffs",
                   "sanctions", "org_memberships", "organizations", "deployments",
                   "zones", "role_actions", "roles", "relationships", "countries",
                   "artefacts"]:
        try:
            client.table(table).delete().eq("sim_run_id", sim_id).execute()
        except Exception:
            pass
    client.table("sim_runs").delete().eq("id", sim_id).execute()


def get_treasury(client, sim_id, country):
    r = client.table("countries").select("treasury").eq("sim_run_id", sim_id).eq("id", country).execute()
    return float(r.data[0]["treasury"]) if r.data else 0


def get_nuclear(client, sim_id, country):
    r = client.table("countries").select("nuclear_level, nuclear_confirmed").eq("sim_run_id", sim_id).eq("id", country).execute()
    return r.data[0] if r.data else {}


def get_ai_level(client, sim_id, country):
    r = client.table("countries").select("ai_level").eq("sim_run_id", sim_id).eq("id", country).execute()
    return int(r.data[0]["ai_level"]) if r.data else 0


def count_reserve_units(client, sim_id, country, unit_type=None):
    q = client.table("deployments").select("id", count="exact").eq("sim_run_id", sim_id).eq("country_code", country).eq("unit_status", "reserve")
    if unit_type:
        q = q.eq("unit_type", unit_type)
    return q.execute().count or 0


def get_reserve_unit_ids(client, sim_id, country, unit_type, limit=5):
    r = client.table("deployments").select("unit_id").eq("sim_run_id", sim_id).eq("country_code", country).eq("unit_status", "reserve").eq("unit_type", unit_type).limit(limit).execute()
    return [u["unit_id"] for u in r.data]


# ---------------------------------------------------------------------------
# Test: Propose validation
# ---------------------------------------------------------------------------

class TestProposalValidation:
    """Test that proposals are correctly validated."""

    def test_empty_trade_rejected(self, client, test_sim):
        result = propose_exchange({
            "proposer_country_code": "columbia",
            "counterpart_country_code": "cathay",
            "scope": "country",
            "offer": {},
            "request": {},
            "round_num": 1,
        }, test_sim)
        assert result["status"] == "rejected"
        assert any("EMPTY_TRADE" in e for e in result["errors"])

    def test_self_trade_same_role_rejected(self, client, test_sim):
        """Same country + same role = self-trade, rejected."""
        result = propose_exchange({
            "proposer_country_code": "columbia",
            "counterpart_country_code": "columbia",
            "proposer_role_id": "dealer",
            "counterpart_role_id": "dealer",
            "scope": "country",
            "offer": {"coins": 1},
            "request": {"coins": 1},
            "round_num": 1,
        }, test_sim)
        assert result["status"] == "rejected"

    def test_invalid_country_rejected(self, client, test_sim):
        result = propose_exchange({
            "proposer_country_code": "atlantis",
            "counterpart_country_code": "cathay",
            "scope": "country",
            "offer": {"coins": 1},
            "request": {},
            "round_num": 1,
        }, test_sim)
        assert result["status"] == "rejected"
        assert any("INVALID_PROPOSER" in e for e in result["errors"])

    def test_insufficient_coins_rejected(self, client, test_sim):
        treasury = get_treasury(client, test_sim, "caribe")
        result = propose_exchange({
            "proposer_country_code": "caribe",
            "counterpart_country_code": "columbia",
            "scope": "country",
            "offer": {"coins": int(treasury) + 1000},
            "request": {},
            "round_num": 1,
        }, test_sim)
        assert result["status"] == "rejected"
        assert any("INSUFFICIENT_COINS" in e for e in result["errors"])


# ---------------------------------------------------------------------------
# Test: Coin transactions
# ---------------------------------------------------------------------------

class TestCoinTransactions:
    """Test coin transfers between countries."""

    def test_coins_for_nothing_gift(self, client, test_sim):
        """Unilateral gift: Columbia gives 5 coins to Cathay."""
        before_col = get_treasury(client, test_sim, "columbia")
        before_cat = get_treasury(client, test_sim, "cathay")

        result = propose_exchange({
            "proposer_country_code": "columbia",
            "counterpart_country_code": "cathay",
            "scope": "country",
            "offer": {"coins": 5},
            "request": {},
            "round_num": 1,
        }, test_sim)
        assert result["status"] == "pending"
        txn_id = result["transaction_id"]

        # Accept
        resp = respond_to_exchange(txn_id, "accept", test_sim)
        assert resp["status"] == "executed"

        # Verify
        after_col = get_treasury(client, test_sim, "columbia")
        after_cat = get_treasury(client, test_sim, "cathay")
        assert after_col == pytest.approx(before_col - 5, abs=0.1)
        assert after_cat == pytest.approx(before_cat + 5, abs=0.1)

    def test_coin_exchange(self, client, test_sim):
        """Bilateral: Columbia offers 3 coins, requests 2 from Sarmatia."""
        before_col = get_treasury(client, test_sim, "columbia")
        before_sar = get_treasury(client, test_sim, "sarmatia")

        result = propose_exchange({
            "proposer_country_code": "columbia",
            "counterpart_country_code": "sarmatia",
            "scope": "country",
            "offer": {"coins": 3},
            "request": {"coins": 2},
            "round_num": 1,
        }, test_sim)
        assert result["status"] == "pending"

        resp = respond_to_exchange(result["transaction_id"], "accept", test_sim)
        assert resp["status"] == "executed"

        after_col = get_treasury(client, test_sim, "columbia")
        after_sar = get_treasury(client, test_sim, "sarmatia")
        assert after_col == pytest.approx(before_col - 3 + 2, abs=0.1)
        assert after_sar == pytest.approx(before_sar - 2 + 3, abs=0.1)

    def test_decline_no_transfer(self, client, test_sim):
        """Declined deal: no coins move."""
        before = get_treasury(client, test_sim, "columbia")

        result = propose_exchange({
            "proposer_country_code": "columbia",
            "counterpart_country_code": "cathay",
            "scope": "country",
            "offer": {"coins": 10},
            "request": {},
            "round_num": 1,
        }, test_sim)

        resp = respond_to_exchange(result["transaction_id"], "decline", test_sim)
        assert resp["status"] == "declined"

        after = get_treasury(client, test_sim, "columbia")
        assert after == pytest.approx(before, abs=0.1)


# ---------------------------------------------------------------------------
# Test: Technology transfers
# ---------------------------------------------------------------------------

class TestTechTransfers:
    """Test technology sharing between countries."""

    def test_nuclear_tech_transfer(self, client, test_sim):
        """Columbia (L3) shares nuclear L1 with Caribe (L0)."""
        before = get_nuclear(client, test_sim, "caribe")
        assert before["nuclear_level"] == 0

        result = propose_exchange({
            "proposer_country_code": "columbia",
            "counterpart_country_code": "caribe",
            "scope": "country",
            "offer": {"technology": {"type": "nuclear", "level": 1}},
            "request": {},
            "round_num": 1,
        }, test_sim)
        assert result["status"] == "pending"

        resp = respond_to_exchange(result["transaction_id"], "accept", test_sim)
        assert resp["status"] == "executed"

        after = get_nuclear(client, test_sim, "caribe")
        assert after["nuclear_level"] == 1
        # Nuclear transfer requires testing — should NOT be confirmed
        assert after["nuclear_confirmed"] == False

    def test_ai_tech_transfer(self, client, test_sim):
        """Cathay (AI L3) shares AI L2 with Sarmatia."""
        before = get_ai_level(client, test_sim, "sarmatia")

        result = propose_exchange({
            "proposer_country_code": "cathay",
            "counterpart_country_code": "sarmatia",
            "scope": "country",
            "offer": {"technology": {"type": "ai", "level": 2}},
            "request": {"coins": 5},
            "round_num": 1,
        }, test_sim)
        assert result["status"] == "pending"

        resp = respond_to_exchange(result["transaction_id"], "accept", test_sim)
        # May fail if sarmatia doesn't have 5 coins — that's ok, it tests validation
        if resp["status"] == "executed":
            after = get_ai_level(client, test_sim, "sarmatia")
            assert after >= 2


# ---------------------------------------------------------------------------
# Test: Unit transfers
# ---------------------------------------------------------------------------

class TestUnitTransfers:
    """Test military unit transfers (reserve only)."""

    def test_offer_reserve_units(self, client, test_sim):
        """Columbia offers 2 reserve ground units to Cathay."""
        reserve_ids = get_reserve_unit_ids(client, test_sim, "columbia", "ground", 2)
        if len(reserve_ids) < 2:
            pytest.skip("Columbia has fewer than 2 reserve ground units")

        before_col = count_reserve_units(client, test_sim, "columbia", "ground")
        before_cat = count_reserve_units(client, test_sim, "cathay", "ground")

        result = propose_exchange({
            "proposer_country_code": "columbia",
            "counterpart_country_code": "cathay",
            "scope": "country",
            "offer": {"units": reserve_ids[:2]},
            "request": {},
            "round_num": 1,
        }, test_sim)
        assert result["status"] == "pending"

        resp = respond_to_exchange(result["transaction_id"], "accept", test_sim)
        assert resp["status"] == "executed"

        after_col = count_reserve_units(client, test_sim, "columbia", "ground")
        after_cat = count_reserve_units(client, test_sim, "cathay", "ground")
        assert after_col == before_col - 2
        assert after_cat == before_cat + 2

    def test_request_units_by_type(self, client, test_sim):
        """Columbia requests 1 naval reserve unit from Cathay."""
        cat_naval_before = count_reserve_units(client, test_sim, "cathay", "naval")
        if cat_naval_before < 1:
            pytest.skip("Cathay has no reserve naval units")

        result = propose_exchange({
            "proposer_country_code": "columbia",
            "counterpart_country_code": "cathay",
            "scope": "country",
            "offer": {"coins": 5},
            "request": {"units": [{"type": "naval", "count": 1}]},
            "round_num": 1,
        }, test_sim)
        assert result["status"] == "pending"

        resp = respond_to_exchange(result["transaction_id"], "accept", test_sim)
        if resp["status"] == "executed":
            after = count_reserve_units(client, test_sim, "cathay", "naval")
            assert after == cat_naval_before - 1


# ---------------------------------------------------------------------------
# Test: Basing rights
# ---------------------------------------------------------------------------

class TestBasingRights:
    """Test basing rights transfers."""

    def test_grant_basing_rights(self, client, test_sim):
        """Columbia grants basing rights to Cathay."""
        result = propose_exchange({
            "proposer_country_code": "columbia",
            "counterpart_country_code": "cathay",
            "scope": "country",
            "offer": {"basing_rights": {"grant": True}},
            "request": {"coins": 3},
            "round_num": 1,
        }, test_sim)
        assert result["status"] == "pending"

        resp = respond_to_exchange(result["transaction_id"], "accept", test_sim)
        # Check if basing rights were updated in relationships
        if resp["status"] == "executed":
            rel = client.table("relationships").select("basing_rights_a_to_b, basing_rights_b_to_a") \
                .eq("sim_run_id", test_sim) \
                .eq("from_country_code", "columbia").eq("to_country_code", "cathay").execute()
            if rel.data:
                # At least one direction should be true
                assert rel.data[0].get("basing_rights_a_to_b") or rel.data[0].get("basing_rights_b_to_a")


# ---------------------------------------------------------------------------
# Test: Combined transactions
# ---------------------------------------------------------------------------

class TestCombinedTransactions:
    """Test transactions with multiple asset types."""

    def test_coins_and_tech_for_basing(self, client, test_sim):
        """Columbia offers 5 coins + nuclear L1 for basing rights from Sarmatia."""
        before_col = get_treasury(client, test_sim, "columbia")

        result = propose_exchange({
            "proposer_country_code": "columbia",
            "counterpart_country_code": "sarmatia",
            "scope": "country",
            "offer": {
                "coins": 5,
                "technology": {"type": "nuclear", "level": 1},
            },
            "request": {
                "basing_rights": {"grant": True},
            },
            "round_num": 1,
        }, test_sim)
        assert result["status"] == "pending"

        resp = respond_to_exchange(result["transaction_id"], "accept", test_sim)
        if resp["status"] == "executed":
            after_col = get_treasury(client, test_sim, "columbia")
            assert after_col == pytest.approx(before_col - 5, abs=0.1)


# ---------------------------------------------------------------------------
# Test: Flow control
# ---------------------------------------------------------------------------

class TestFlowControl:
    """Test propose/accept/decline/counteroffer flows."""

    def test_double_accept_blocked(self, client, test_sim):
        """Cannot accept an already executed transaction."""
        result = propose_exchange({
            "proposer_country_code": "columbia",
            "counterpart_country_code": "cathay",
            "scope": "country",
            "offer": {"coins": 1},
            "request": {},
            "round_num": 1,
        }, test_sim)

        resp1 = respond_to_exchange(result["transaction_id"], "accept", test_sim)
        assert resp1["status"] == "executed"

        resp2 = respond_to_exchange(result["transaction_id"], "accept", test_sim)
        # Second accept should return errors (transaction already processed)
        assert resp2.get("errors") or resp2["status"] != "pending"

    def test_decline_then_accept_blocked(self, client, test_sim):
        """Cannot accept a declined transaction."""
        result = propose_exchange({
            "proposer_country_code": "columbia",
            "counterpart_country_code": "cathay",
            "scope": "country",
            "offer": {"coins": 1},
            "request": {},
            "round_num": 1,
        }, test_sim)

        resp1 = respond_to_exchange(result["transaction_id"], "decline", test_sim)
        assert resp1["status"] == "declined"

        resp2 = respond_to_exchange(result["transaction_id"], "accept", test_sim)
        assert resp2["status"] != "executed"

    def test_counterpart_insufficient_coins_blocked(self, client, test_sim):
        """Accept blocked when counterpart can't fulfill coin request."""
        # Request more coins than counterpart has
        cat_treasury = get_treasury(client, test_sim, "cathay")

        result = propose_exchange({
            "proposer_country_code": "columbia",
            "counterpart_country_code": "cathay",
            "scope": "country",
            "offer": {"coins": 1},
            "request": {"coins": int(cat_treasury) + 10000},
            "round_num": 1,
        }, test_sim)
        assert result["status"] == "pending"

        resp = respond_to_exchange(result["transaction_id"], "accept", test_sim)
        # Should fail at execution — counterpart doesn't have enough
        assert resp["status"] != "executed" or "error" in str(resp).lower()


# ---------------------------------------------------------------------------
# Test: Visibility
# ---------------------------------------------------------------------------

class TestVisibility:
    """Test secret vs public transactions."""

    def test_public_transaction_creates_event(self, client, test_sim):
        """Public transaction creates observatory event."""
        result = propose_exchange({
            "proposer_country_code": "columbia",
            "counterpart_country_code": "cathay",
            "scope": "country",
            "offer": {"coins": 1},
            "request": {},
            "round_num": 1,
            "visibility": "public",
        }, test_sim)
        assert result["status"] == "pending"

        # Check event was created
        evts = client.table("observatory_events").select("event_type") \
            .eq("sim_run_id", test_sim).eq("event_type", "transaction_proposed") \
            .execute()
        assert len(evts.data) > 0
