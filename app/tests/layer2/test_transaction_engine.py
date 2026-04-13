"""L2 — Transaction engine persistence (CONTRACT_TRANSACTIONS v1.0).

Tests the full propose → respond → execute chain against the live DB.
"""

from __future__ import annotations
import pytest

from engine.services.transaction_engine import propose_exchange, respond_to_exchange, get_pending_proposals
from engine.services.supabase import get_client
from tests._sim_run_helper import create_isolated_run

SCENARIO = "start_one"


@pytest.fixture
def client():
    return get_client()


@pytest.fixture
def isolated_run(client):
    sim_run_id, cleanup = create_isolated_run(scenario_code=SCENARIO, test_name="transactions")
    # Seed R1
    cs = client.table("country_states_per_round").select("*") \
        .eq("sim_run_id", sim_run_id).eq("round_num", 0).execute()
    if cs.data:
        rows = [{k: v for k, v in r.items() if k != "id"} for r in cs.data]
        for r in rows:
            r["round_num"] = 1
        client.table("country_states_per_round").upsert(
            rows, on_conflict="sim_run_id,round_num,country_code"
        ).execute()
    us = client.table("unit_states_per_round").select("*") \
        .eq("sim_run_id", sim_run_id).eq("round_num", 0).execute()
    if us.data:
        rows = [{k: v for k, v in r.items() if k != "id"} for r in us.data]
        for r in rows:
            r["round_num"] = 1
        for i in range(0, len(rows), 200):
            client.table("unit_states_per_round").upsert(
                rows[i:i+200], on_conflict="sim_run_id,round_num,unit_code"
            ).execute()
    yield sim_run_id
    cleanup()


def test_coin_transfer_full_chain(client, isolated_run):
    """Columbia sends 5 coins to Sarmatia. Full propose → accept → execute."""
    sim_run_id = isolated_run

    # Get baseline treasuries
    col_pre = client.table("country_states_per_round").select("treasury") \
        .eq("sim_run_id", sim_run_id).eq("round_num", 1).eq("country_code", "columbia") \
        .limit(1).execute().data[0]
    sar_pre = client.table("country_states_per_round").select("treasury") \
        .eq("sim_run_id", sim_run_id).eq("round_num", 1).eq("country_code", "sarmatia") \
        .limit(1).execute().data[0]
    col_treasury_before = float(col_pre["treasury"])
    sar_treasury_before = float(sar_pre["treasury"])
    print(f"\n  [pre] columbia={col_treasury_before} sarmatia={sar_treasury_before}")

    # Propose
    proposal = {
        "action_type": "propose_transaction",
        "proposer_role_id": "dealer",
        "proposer_country_code": "columbia",
        "scope": "country",
        "counterpart_role_id": "pathfinder",
        "counterpart_country_code": "sarmatia",
        "round_num": 1,
        "offer": {"coins": 5},
        "request": {"basing_rights": True},
        "rationale": "5 coins for basing rights on Sarmatia territory",
    }
    result = propose_exchange(proposal, sim_run_id)
    assert result["status"] == "pending", result
    txn_id = result["transaction_id"]
    print(f"  [proposed] txn_id={txn_id}")

    # Check pending
    pending = get_pending_proposals("sarmatia", sim_run_id)
    assert any(p["id"] == txn_id for p in pending)

    # Accept
    accept_result = respond_to_exchange(txn_id, "accept", sim_run_id, rationale="Fair deal")
    assert accept_result["status"] == "executed", accept_result
    print(f"  [executed] changes={accept_result.get('changes')}")

    # Verify coins moved
    col_post = client.table("country_states_per_round").select("treasury") \
        .eq("sim_run_id", sim_run_id).eq("round_num", 1).eq("country_code", "columbia") \
        .limit(1).execute().data[0]
    sar_post = client.table("country_states_per_round").select("treasury") \
        .eq("sim_run_id", sim_run_id).eq("round_num", 1).eq("country_code", "sarmatia") \
        .limit(1).execute().data[0]
    assert float(col_post["treasury"]) == pytest.approx(col_treasury_before - 5)
    assert float(sar_post["treasury"]) == pytest.approx(sar_treasury_before + 5)
    print(f"  [post] columbia={col_post['treasury']} sarmatia={sar_post['treasury']}")

    # Verify transaction record
    txn = client.table("exchange_transactions").select("status") \
        .eq("id", txn_id).execute().data[0]
    assert txn["status"] == "executed"


def test_unit_transfer(client, isolated_run):
    """Columbia trades col_g_05 to Sarmatia for 3 coins."""
    sim_run_id = isolated_run

    proposal = {
        "action_type": "propose_transaction",
        "proposer_role_id": "dealer",
        "proposer_country_code": "columbia",
        "scope": "country",
        "counterpart_role_id": "pathfinder",
        "counterpart_country_code": "sarmatia",
        "round_num": 1,
        "offer": {"units": ["col_g_05"]},
        "request": {"coins": 3},
        "rationale": "Trading a ground unit for 3 coins",
    }
    result = propose_exchange(proposal, sim_run_id)
    assert result["status"] == "pending"
    txn_id = result["transaction_id"]

    accept = respond_to_exchange(txn_id, "accept", sim_run_id)
    assert accept["status"] == "executed", accept
    print(f"\n  [executed] {accept.get('changes')}")

    # Verify unit ownership changed
    u = client.table("unit_states_per_round").select("country_code,status") \
        .eq("sim_run_id", sim_run_id).eq("round_num", 1).eq("unit_code", "col_g_05") \
        .limit(1).execute().data[0]
    assert u["country_code"] == "sarmatia"
    assert u["status"] == "reserve"


def test_declined_transaction(client, isolated_run):
    """Declined proposal is recorded but no assets move."""
    sim_run_id = isolated_run

    proposal = {
        "action_type": "propose_transaction",
        "proposer_role_id": "dealer",
        "proposer_country_code": "columbia",
        "scope": "country",
        "counterpart_role_id": "pathfinder",
        "counterpart_country_code": "sarmatia",
        "round_num": 1,
        "offer": {"coins": 10},
        "request": {"coins": 5},
        "rationale": "A deal that will be declined",
    }
    result = propose_exchange(proposal, sim_run_id)
    txn_id = result["transaction_id"]

    decline = respond_to_exchange(txn_id, "decline", sim_run_id, rationale="Not interested")
    assert decline["status"] == "declined"

    txn = client.table("exchange_transactions").select("status") \
        .eq("id", txn_id).execute().data[0]
    assert txn["status"] == "declined"


def test_counter_offer_chain(client, isolated_run):
    """Propose → counter → accept the counter."""
    sim_run_id = isolated_run

    proposal = {
        "action_type": "propose_transaction",
        "proposer_role_id": "dealer",
        "proposer_country_code": "columbia",
        "scope": "country",
        "counterpart_role_id": "pathfinder",
        "counterpart_country_code": "sarmatia",
        "round_num": 1,
        "offer": {"coins": 10},
        "request": {"coins": 5},
        "rationale": "Initial offer",
    }
    result = propose_exchange(proposal, sim_run_id)
    txn_id = result["transaction_id"]

    # Counter: sarmatia wants 8 coins instead of 10
    counter = respond_to_exchange(
        txn_id, "counter", sim_run_id,
        rationale="I want 8 coins not 10",
        counter_offer={"coins": 8},
        counter_request={"coins": 5},
    )
    assert counter["status"] == "countered"

    # Proposer accepts the counter
    accept = respond_to_exchange(txn_id, "accept", sim_run_id, rationale="OK deal")
    assert accept["status"] == "executed"
    print(f"\n  [counter→accept] {accept.get('changes')}")
