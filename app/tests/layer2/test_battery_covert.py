"""Layer 2 Battery Test — Covert Ops + Communication.

Scripted decisions through full pipeline, zero LLM cost.
Uses rounds 96-97 to avoid conflicts.

Run::
    cd app && PYTHONPATH=. python3 -m pytest tests/layer2/test_battery_covert.py -v
"""
from __future__ import annotations
import logging
import pytest
from engine.services.supabase import get_client
from engine.round_engine.resolve_round import resolve_round
from engine.engines.round_tick import run_engine_tick

logger = logging.getLogger(__name__)
SCENARIO_CODE = "start_one"
TEST_ROUND = 97
TEST_ROUNDS = [96, 97]
TEST_TAG = "BATTERY_COV_L2"


def _get_scenario_id(client) -> str:
    res = client.table("sim_scenarios").select("id").eq("code", SCENARIO_CODE).limit(1).execute()
    assert res.data
    return res.data[0]["id"]


def _cleanup(client, scenario_id):
    for rn in TEST_ROUNDS:
        client.table("observatory_combat_results").delete().eq("scenario_id", scenario_id).eq("round_num", rn).execute()
        client.table("observatory_events").delete().eq("scenario_id", scenario_id).eq("round_num", rn).execute()
        client.table("exchange_transactions").delete().eq("scenario_id", scenario_id).eq("round_num", rn).execute()
        client.table("unit_states_per_round").delete().eq("scenario_id", scenario_id).eq("round_num", rn).execute()
        client.table("country_states_per_round").delete().eq("scenario_id", scenario_id).eq("round_num", rn).execute()
        client.table("global_state_per_round").delete().eq("scenario_id", scenario_id).eq("round_num", rn).execute()
        client.table("round_states").delete().eq("scenario_id", scenario_id).eq("round_num", rn).execute()
        client.table("agent_decisions").delete().eq("scenario_id", scenario_id).eq("round_num", rn).execute()


@pytest.fixture(scope="module")
def client():
    return get_client()

@pytest.fixture(scope="module")
def scenario_id(client):
    return _get_scenario_id(client)

@pytest.fixture(scope="module", autouse=True)
def battery_run(client, scenario_id):
    _cleanup(client, scenario_id)

    prev = TEST_ROUND - 1
    r0 = client.table("country_states_per_round").select("*").eq("scenario_id", scenario_id).eq("round_num", 0).execute()
    for row in (r0.data or []):
        nr = {k: v for k, v in row.items() if k != "id"}
        nr["round_num"] = prev
        client.table("country_states_per_round").insert(nr).execute()

    r0g = client.table("global_state_per_round").select("*").eq("scenario_id", scenario_id).eq("round_num", 0).execute()
    for row in (r0g.data or []):
        nr = {k: v for k, v in row.items() if k != "id"}
        nr["round_num"] = prev
        client.table("global_state_per_round").insert(nr).execute()

    r0u = client.table("unit_states_per_round").select("*").eq("scenario_id", scenario_id).eq("round_num", 0).execute()
    if r0u.data:
        batch = [{k: v for k, v in row.items() if k != "id"} | {"round_num": prev} for row in r0u.data]
        for i in range(0, len(batch), 100):
            client.table("unit_states_per_round").insert(batch[i:i+100]).execute()

    decisions = []

    def _d(country, action_type, payload, rationale):
        payload["test_tag"] = TEST_TAG
        return {"scenario_id": scenario_id, "country_code": country, "action_type": action_type,
                "action_payload": payload, "rationale": rationale, "validation_status": "passed", "round_num": TEST_ROUND}

    # 1. Intelligence (espionage)
    decisions.append(_d("ruthenia", "covert_op", {
        "op_type": "intelligence", "target_country": "sarmatia",
        "question": "What are Sarmatia's troop deployments near the border?",
    }, "COV_BATTERY: espionage"))

    # 2. Sabotage
    decisions.append(_d("solaria", "covert_op", {
        "op_type": "sabotage", "target_country": "persia", "target_type": "infrastructure",
    }, "COV_BATTERY: sabotage"))

    # 3. Propaganda / disinformation
    decisions.append(_d("cathay", "covert_op", {
        "op_type": "disinformation", "target_country": "formosa",
        "intent": "undermine government legitimacy",
    }, "COV_BATTERY: disinfo"))

    # 4. Election meddling
    decisions.append(_d("columbia", "covert_op", {
        "op_type": "election_meddling", "target_country": "ponte",
    }, "COV_BATTERY: election meddling"))

    # 5. Cyber
    decisions.append(_d("hanguk", "covert_op", {
        "op_type": "cyber", "target_country": "choson",
    }, "COV_BATTERY: cyber"))

    # 6. Additional ops for volume
    decisions.append(_d("yamato", "covert_op", {
        "op_type": "intelligence", "target_country": "cathay",
        "question": "Cathay naval movements near Formosa?",
    }, "COV_BATTERY: yamato intel"))

    # 7. Public statements (3)
    decisions.append(_d("bharata", "public_statement", {
        "content": "Bharata reaffirms commitment to non-alignment.",
    }, "COV_BATTERY: statement 1"))
    decisions.append(_d("yamato", "public_statement", {
        "content": "Yamato stands with its Pacific allies.",
    }, "COV_BATTERY: statement 2"))
    decisions.append(_d("teutonia", "public_statement", {
        "content": "Teutonia calls for diplomatic solutions in Eastern Ereb.",
    }, "COV_BATTERY: statement 3"))

    # 8. Org meeting
    decisions.append(_d("gallia", "call_org_meeting", {
        "org_code": "ereb_union", "agenda": "Discuss Erebian security and economic resilience.",
    }, "COV_BATTERY: org meeting"))

    # Budget for engine tick
    decisions.append(_d("columbia", "set_budget", {
        "social_pct": 1.0, "military_coins": 2, "tech_coins": 1,
    }, "COV_BATTERY: budget"))

    inserted = client.table("agent_decisions").insert(decisions).execute()
    decision_ids = [r["id"] for r in (inserted.data or [])]

    resolve_result = resolve_round(SCENARIO_CODE, TEST_ROUND)
    tick_result = run_engine_tick(SCENARIO_CODE, TEST_ROUND)

    yield {
        "decision_ids": decision_ids, "resolve_result": resolve_result,
        "tick_result": tick_result, "decision_count": len(decisions),
    }

    _cleanup(client, scenario_id)


# --- Tests ---

class TestIntelligence:
    def test_espionage_event(self, client, scenario_id, battery_run):
        res = client.table("observatory_events").select("id, summary, country_code") \
            .eq("scenario_id", scenario_id).eq("round_num", TEST_ROUND) \
            .eq("event_type", "covert_op").execute()
        intel = [e for e in (res.data or []) if "ruthenia" in (e.get("country_code") or "")]
        print(f"  Ruthenia covert events: {len(intel)}")
        assert len(intel) >= 1, "Expected espionage event for Ruthenia"

class TestSabotage:
    def test_sabotage_event(self, client, scenario_id, battery_run):
        res = client.table("observatory_events").select("id, summary, country_code") \
            .eq("scenario_id", scenario_id).eq("round_num", TEST_ROUND) \
            .eq("event_type", "covert_op").execute()
        sab = [e for e in (res.data or []) if "solaria" in (e.get("country_code") or "")]
        print(f"  Solaria covert events: {len(sab)}")
        assert len(sab) >= 1, "Expected sabotage event for Solaria"

class TestDisinformation:
    def test_disinfo_event(self, client, scenario_id, battery_run):
        res = client.table("observatory_events").select("id, summary, country_code") \
            .eq("scenario_id", scenario_id).eq("round_num", TEST_ROUND) \
            .eq("event_type", "covert_op").execute()
        dis = [e for e in (res.data or []) if "cathay" in (e.get("country_code") or "")]
        print(f"  Cathay covert events: {len(dis)}")
        assert len(dis) >= 1, "Expected disinformation event for Cathay"

class TestElectionMeddling:
    def test_meddling_event(self, client, scenario_id, battery_run):
        res = client.table("observatory_events").select("id, summary, country_code") \
            .eq("scenario_id", scenario_id).eq("round_num", TEST_ROUND) \
            .eq("event_type", "covert_op").execute()
        med = [e for e in (res.data or []) if "columbia" in (e.get("country_code") or "")]
        print(f"  Columbia covert events: {len(med)}")
        assert len(med) >= 1, "Expected election meddling event for Columbia"

class TestCyber:
    def test_cyber_event(self, client, scenario_id, battery_run):
        res = client.table("observatory_events").select("id, summary, country_code") \
            .eq("scenario_id", scenario_id).eq("round_num", TEST_ROUND) \
            .eq("event_type", "covert_op").execute()
        cyb = [e for e in (res.data or []) if "hanguk" in (e.get("country_code") or "")]
        print(f"  Hanguk covert events: {len(cyb)}")
        assert len(cyb) >= 1, "Expected cyber event for Hanguk"

class TestMultipleCovertOps:
    def test_all_six_ops_logged(self, client, scenario_id, battery_run):
        res = client.table("observatory_events").select("id, country_code") \
            .eq("scenario_id", scenario_id).eq("round_num", TEST_ROUND) \
            .eq("event_type", "covert_op").execute()
        countries = [e["country_code"] for e in (res.data or [])]
        print(f"  Total covert ops: {len(countries)}, countries: {sorted(set(countries))}")
        assert len(res.data or []) >= 6, f"Expected 6 covert ops, got {len(res.data or [])}"

class TestPublicStatements:
    def test_three_statements(self, client, scenario_id, battery_run):
        res = client.table("observatory_events").select("id, country_code") \
            .eq("scenario_id", scenario_id).eq("round_num", TEST_ROUND) \
            .eq("event_type", "public_statement").execute()
        print(f"  Public statements: {len(res.data or [])}")
        assert len(res.data or []) >= 3, "Expected at least 3 public statements"

class TestOrgMeeting:
    def test_org_meeting_event(self, client, scenario_id, battery_run):
        res = client.table("observatory_events").select("id, summary") \
            .eq("scenario_id", scenario_id).eq("round_num", TEST_ROUND) \
            .eq("event_type", "call_org_meeting").execute()
        print(f"  Org meeting events: {len(res.data or [])}")
        assert len(res.data or []) >= 1, "Expected org meeting event"

class TestCovertBatteryEndToEnd:
    def test_resolve_succeeded(self, battery_run):
        assert battery_run["resolve_result"].get("decisions_processed", 0) > 0

    def test_engine_tick_succeeded(self, battery_run):
        assert battery_run["tick_result"].get("success") is True

    def test_all_processed(self, battery_run):
        assert battery_run["resolve_result"].get("decisions_processed", 0) == battery_run["decision_count"]
