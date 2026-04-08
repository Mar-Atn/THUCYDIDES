"""Layer 2 Battery Test — Transactions, Agreements, Sanctions, Tariffs.

Scripted decisions through full pipeline, zero LLM cost.
Uses rounds 93-95 to avoid conflicts with test_battery.py (90-91).

Run::

    cd app && PYTHONPATH=. python3 -m pytest tests/layer2/test_battery_transactions.py -v

"""
from __future__ import annotations

import logging
import pytest

from engine.services.supabase import get_client
from engine.round_engine.resolve_round import resolve_round
from engine.engines.round_tick import run_engine_tick

logger = logging.getLogger(__name__)

SCENARIO_CODE = "start_one"
TEST_ROUND = 94
TEST_ROUNDS = [93, 94, 95]
TEST_TAG = "BATTERY_TXN_L2"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_scenario_id(client) -> str:
    res = client.table("sim_scenarios").select("id").eq("code", SCENARIO_CODE).limit(1).execute()
    assert res.data, f"Scenario '{SCENARIO_CODE}' not found"
    return res.data[0]["id"]


def _cleanup_test_data(client, scenario_id: str) -> None:
    from engine.config.settings import Settings
    _sim_run_id = Settings().default_sim_id

    for rn in TEST_ROUNDS:
        client.table("observatory_combat_results").delete().eq("scenario_id", scenario_id).eq("round_num", rn).execute()
        client.table("observatory_events").delete().eq("scenario_id", scenario_id).eq("round_num", rn).execute()
        client.table("exchange_transactions").delete().eq("scenario_id", scenario_id).eq("round_num", rn).execute()
        client.table("unit_states_per_round").delete().eq("scenario_id", scenario_id).eq("round_num", rn).execute()
        client.table("country_states_per_round").delete().eq("scenario_id", scenario_id).eq("round_num", rn).execute()
        client.table("global_state_per_round").delete().eq("scenario_id", scenario_id).eq("round_num", rn).execute()
        client.table("round_states").delete().eq("scenario_id", scenario_id).eq("round_num", rn).execute()
        client.table("agreements").delete().eq("scenario_id", scenario_id).eq("round_num", rn).execute()

    # Clean sanctions/tariffs upserted by this battery
    try:
        for imposer, target in [("columbia", "caribe"), ("columbia", "cathay")]:
            # Don't delete starting sanctions — only delete if notes contain our tag
            pass  # Sanctions cleanup is tricky — skip for now, resolve_round upserts anyway
    except Exception:
        pass

    # Delete test decisions
    for rn in TEST_ROUNDS:
        client.table("agent_decisions").delete().eq("scenario_id", scenario_id).eq("round_num", rn).execute()


def _build_scripted_decisions(client, scenario_id: str) -> list[dict]:
    decisions = []

    def _d(country, action_type, payload, rationale):
        payload["test_tag"] = TEST_TAG
        return {
            "scenario_id": scenario_id,
            "country_code": country,
            "action_type": action_type,
            "action_payload": payload,
            "rationale": rationale,
            "validation_status": "passed",
            "round_num": TEST_ROUND,
        }

    # 1. Coin gift: Albion -> Columbia
    decisions.append(_d("albion", "propose_transaction", {
        "counterpart_country": "columbia",
        "offer": {"coins": 5}, "request": {"coins": 0},
        "terms": "Goodwill gift",
    }, "TXN_BATTERY: Albion coins gift"))

    # 2. Unit trade: Sarmatia -> Cathay
    decisions.append(_d("sarmatia", "propose_transaction", {
        "counterpart_country": "cathay",
        "offer": {"ground_units": 2}, "request": {"coins": 10},
        "terms": "2 ground for 10 coins",
    }, "TXN_BATTERY: Sarmatia unit trade"))

    # 3. Empty offer: Gallia -> Teutonia
    decisions.append(_d("gallia", "propose_transaction", {
        "counterpart_country": "teutonia",
        "offer": {}, "request": {},
        "terms": "Framework cooperation",
    }, "TXN_BATTERY: Gallia empty offer"))

    # 4. Ceasefire agreement: Ruthenia <-> Sarmatia
    decisions.append(_d("ruthenia", "propose_agreement", {
        "counterpart_country": "sarmatia",
        "agreement_name": "Ruthenia-Sarmatia Ceasefire",
        "agreement_type": "ceasefire",
        "signatories": ["ruthenia", "sarmatia"],
        "visibility": "public",
        "terms": "Immediate cessation of hostilities.",
    }, "TXN_BATTERY: ceasefire"))

    # 5. Alliance: Columbia <-> Yamato
    decisions.append(_d("columbia", "propose_agreement", {
        "counterpart_country": "yamato",
        "agreement_name": "Columbia-Yamato Alliance",
        "agreement_type": "military_alliance",
        "signatories": ["columbia", "yamato"],
        "visibility": "public",
        "terms": "Full military cooperation.",
    }, "TXN_BATTERY: alliance"))

    # 6. Trade agreement: Bharata <-> Cathay
    decisions.append(_d("bharata", "propose_agreement", {
        "counterpart_country": "cathay",
        "agreement_name": "Bharata-Cathay Trade Accord",
        "agreement_type": "trade_agreement",
        "signatories": ["bharata", "cathay"],
        "visibility": "public",
        "terms": "Mutual tariff reduction.",
    }, "TXN_BATTERY: trade agreement"))

    # 8. Sanction: Columbia L2 on Caribe
    decisions.append(_d("columbia", "set_sanction", {
        "target_country": "caribe", "level": 2, "sanction_type": "financial",
    }, "TXN_BATTERY: sanction"))

    # 9. Tariff: Columbia L3 on Cathay
    decisions.append(_d("columbia", "set_tariff", {
        "target_country": "cathay", "level": 3,
    }, "TXN_BATTERY: tariff"))

    # 10. Lift sanction: Columbia lifts on Caribe
    decisions.append(_d("columbia", "lift_sanction", {
        "target_country": "caribe",
    }, "TXN_BATTERY: lift sanction"))

    # Budget for engine tick
    decisions.append(_d("columbia", "set_budget", {
        "social_pct": 1.0, "military_coins": 2, "tech_coins": 1,
    }, "TXN_BATTERY: budget"))

    return decisions


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    return get_client()

@pytest.fixture(scope="module")
def scenario_id(client):
    return _get_scenario_id(client)

@pytest.fixture(scope="module", autouse=True)
def battery_run(client, scenario_id):
    print("\n[TXN_BATTERY] Setup...")
    _cleanup_test_data(client, scenario_id)

    # Seed baseline from R0
    prev = TEST_ROUND - 1
    r0 = client.table("country_states_per_round").select("*").eq("scenario_id", scenario_id).eq("round_num", 0).execute()
    if r0.data:
        for row in r0.data:
            nr = {k: v for k, v in row.items() if k != "id"}
            nr["round_num"] = prev
            client.table("country_states_per_round").insert(nr).execute()

    r0g = client.table("global_state_per_round").select("*").eq("scenario_id", scenario_id).eq("round_num", 0).execute()
    if r0g.data:
        for row in r0g.data:
            nr = {k: v for k, v in row.items() if k != "id"}
            nr["round_num"] = prev
            client.table("global_state_per_round").insert(nr).execute()

    r0u = client.table("unit_states_per_round").select("*").eq("scenario_id", scenario_id).eq("round_num", 0).execute()
    if r0u.data:
        batch = [{k: v for k, v in row.items() if k != "id"} | {"round_num": prev} for row in r0u.data]
        for i in range(0, len(batch), 100):
            client.table("unit_states_per_round").insert(batch[i:i+100]).execute()

    # Insert decisions
    decisions = _build_scripted_decisions(client, scenario_id)
    inserted = client.table("agent_decisions").insert(decisions).execute()
    decision_ids = [r["id"] for r in (inserted.data or [])]

    # Execute pipeline
    resolve_result = resolve_round(SCENARIO_CODE, TEST_ROUND)
    tick_result = run_engine_tick(SCENARIO_CODE, TEST_ROUND)

    yield {
        "decision_ids": decision_ids,
        "resolve_result": resolve_result,
        "tick_result": tick_result,
        "decision_count": len(decisions),
    }

    print("\n[TXN_BATTERY] Cleanup...")
    _cleanup_test_data(client, scenario_id)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestTransactionCoins:
    def test_albion_columbia_exists(self, client, scenario_id, battery_run):
        res = client.table("exchange_transactions").select("*") \
            .eq("scenario_id", scenario_id).eq("round_num", TEST_ROUND) \
            .eq("proposer", "albion").eq("counterpart", "columbia").execute()
        assert len(res.data or []) >= 1, "No exchange_transaction for Albion->Columbia"
        assert (res.data[0].get("offer") or {}).get("coins") == 5

class TestTransactionUnits:
    def test_sarmatia_cathay_exists(self, client, scenario_id, battery_run):
        res = client.table("exchange_transactions").select("*") \
            .eq("scenario_id", scenario_id).eq("round_num", TEST_ROUND) \
            .eq("proposer", "sarmatia").eq("counterpart", "cathay").execute()
        assert len(res.data or []) >= 1
        assert (res.data[0].get("offer") or {}).get("ground_units") == 2

class TestTransactionEmpty:
    def test_gallia_teutonia_exists(self, client, scenario_id, battery_run):
        res = client.table("exchange_transactions").select("*") \
            .eq("scenario_id", scenario_id).eq("round_num", TEST_ROUND) \
            .eq("proposer", "gallia").eq("counterpart", "teutonia").execute()
        assert len(res.data or []) >= 1

class TestAgreementCeasefire:
    def test_ceasefire_exists(self, client, scenario_id, battery_run):
        res = client.table("agreements").select("*") \
            .eq("scenario_id", scenario_id).eq("round_num", TEST_ROUND) \
            .eq("agreement_type", "ceasefire").execute()
        assert len(res.data or []) >= 1
        assert "ruthenia" in (res.data[0].get("signatories") or [])

class TestAgreementAlliance:
    def test_alliance_exists(self, client, scenario_id, battery_run):
        res = client.table("agreements").select("*") \
            .eq("scenario_id", scenario_id).eq("round_num", TEST_ROUND) \
            .eq("agreement_type", "military_alliance").execute()
        assert len(res.data or []) >= 1

class TestAgreementTrade:
    def test_trade_agreement_exists(self, client, scenario_id, battery_run):
        res = client.table("agreements").select("*") \
            .eq("scenario_id", scenario_id).eq("round_num", TEST_ROUND) \
            .eq("agreement_type", "trade_agreement").execute()
        assert len(res.data or []) >= 1

class TestMultipleTransactions:
    def test_three_rows_no_dupes(self, client, scenario_id, battery_run):
        res = client.table("exchange_transactions").select("proposer, counterpart") \
            .eq("scenario_id", scenario_id).eq("round_num", TEST_ROUND).execute()
        assert len(res.data or []) == 3

class TestSanction:
    def test_sanction_event_logged(self, client, scenario_id, battery_run):
        res = client.table("observatory_events").select("id") \
            .eq("scenario_id", scenario_id).eq("round_num", TEST_ROUND) \
            .eq("event_type", "set_sanction").execute()
        assert len(res.data or []) >= 1

class TestTariff:
    def test_tariff_event_logged(self, client, scenario_id, battery_run):
        res = client.table("observatory_events").select("id") \
            .eq("scenario_id", scenario_id).eq("round_num", TEST_ROUND) \
            .eq("event_type", "set_tariff").execute()
        assert len(res.data or []) >= 1

class TestLiftSanction:
    def test_lift_event_logged(self, client, scenario_id, battery_run):
        res = client.table("observatory_events").select("id") \
            .eq("scenario_id", scenario_id).eq("round_num", TEST_ROUND) \
            .eq("event_type", "lift_sanction").execute()
        assert len(res.data or []) >= 1

class TestTxnBatteryEndToEnd:
    def test_resolve_succeeded(self, battery_run):
        assert battery_run["resolve_result"].get("decisions_processed", 0) > 0

    def test_engine_tick_succeeded(self, battery_run):
        assert battery_run["tick_result"].get("success") is True

    def test_all_processed(self, battery_run):
        assert battery_run["resolve_result"].get("decisions_processed", 0) == battery_run["decision_count"]
