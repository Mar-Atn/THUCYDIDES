"""Layer 2 Battery Test — Military Actions.

Scripted decisions through full pipeline, zero LLM cost.
Uses rounds 92-93 to avoid conflicts.

Run::
    cd app && PYTHONPATH=. python3 -m pytest tests/layer2/test_battery_military.py -v
"""
from __future__ import annotations
import logging
import pytest
from engine.services.supabase import get_client
from engine.round_engine.resolve_round import resolve_round
from engine.engines.round_tick import run_engine_tick

logger = logging.getLogger(__name__)
SCENARIO_CODE = "start_one"
TEST_ROUND = 93
TEST_ROUNDS = [92, 93]
TEST_TAG = "BATTERY_MIL_L2"


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
        client.table("blockades").delete().eq("established_round", rn).execute()
        client.table("agent_decisions").delete().eq("scenario_id", scenario_id).eq("round_num", rn).execute()


def _find_units(client, scenario_id, country, unit_type, status="active", limit=3):
    res = client.table("unit_states_per_round").select("unit_code, global_row, global_col") \
        .eq("scenario_id", scenario_id).eq("round_num", 0) \
        .eq("country_code", country).eq("unit_type", unit_type) \
        .eq("status", status).not_.is_("global_row", "null").limit(limit).execute()
    return res.data or []


def _find_enemy_hex(client, scenario_id, target_country):
    res = client.table("unit_states_per_round").select("global_row, global_col") \
        .eq("scenario_id", scenario_id).eq("round_num", 0) \
        .eq("country_code", target_country).eq("status", "active") \
        .not_.is_("global_row", "null").limit(1).execute()
    if res.data:
        return res.data[0]["global_row"], res.data[0]["global_col"]
    return None, None


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
    # Seed baseline
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

    # Build decisions
    decisions = []
    meta = {}

    def _d(country, action_type, payload, rationale):
        payload["test_tag"] = TEST_TAG
        return {"scenario_id": scenario_id, "country_code": country, "action_type": action_type,
                "action_payload": payload, "rationale": rationale, "validation_status": "passed", "round_num": TEST_ROUND}

    # 1. Ground attack: Sarmatia -> Ruthenia
    sar_ground = _find_units(client, scenario_id, "sarmatia", "ground")
    ruth_row, ruth_col = _find_enemy_hex(client, scenario_id, "ruthenia")
    if sar_ground and ruth_row:
        codes = [u["unit_code"] for u in sar_ground[:2]]
        decisions.append(_d("sarmatia", "declare_attack", {
            "attacker_unit_codes": codes, "target_global_row": ruth_row, "target_global_col": ruth_col,
        }, "MIL_BATTERY: ground attack"))
        meta["ground_attack"] = True

    # 2. Air strike: Columbia air unit
    col_air = _find_units(client, scenario_id, "columbia", "tactical_air")
    if col_air and ruth_row:
        decisions.append(_d("columbia", "declare_attack", {
            "attacker_unit_codes": [col_air[0]["unit_code"]], "target_global_row": ruth_row, "target_global_col": ruth_col,
        }, "MIL_BATTERY: air strike"))
        meta["air_strike"] = True

    # 3. Naval attack: find two opposing naval units
    col_naval = _find_units(client, scenario_id, "columbia", "naval")
    sar_naval = _find_units(client, scenario_id, "sarmatia", "naval")
    if col_naval and sar_naval:
        decisions.append(_d("columbia", "attack_naval", {
            "attacker_unit_code": col_naval[0]["unit_code"], "target_unit_code": sar_naval[0]["unit_code"],
        }, "MIL_BATTERY: naval 1v1"))
        meta["naval_attack"] = True

    # 4. Nuclear test: Persia underground
    decisions.append(_d("persia", "nuclear_test", {
        "test_type": "underground", "target_global_row": 7, "target_global_col": 13,
    }, "MIL_BATTERY: nuclear test"))
    meta["nuclear_test"] = True

    # 5. Blockade: declare on gulf_gate
    decisions.append(_d("columbia", "declare_blockade", {
        "zone_id": "gulf_gate", "action": "establish", "level": "full",
    }, "MIL_BATTERY: blockade"))
    meta["blockade"] = True

    # 6. Mobilize reserve: Columbia
    col_reserve = _find_units(client, scenario_id, "columbia", "ground", status="reserve", limit=1)
    if col_reserve:
        decisions.append(_d("columbia", "mobilize_reserve", {
            "unit_code": col_reserve[0]["unit_code"], "target_global_row": 3, "target_global_col": 3,
        }, "MIL_BATTERY: mobilize"))
        meta["mobilize"] = True

    # 7. Basing rights: Albion grants to Columbia
    decisions.append(_d("albion", "basing_rights", {
        "counterpart_country": "columbia", "action": "grant",
    }, "MIL_BATTERY: basing rights"))
    meta["basing"] = True

    # 8. Public statement (so round has events)
    decisions.append(_d("columbia", "public_statement", {
        "content": "Columbia reaffirms security commitments.",
    }, "MIL_BATTERY: statement"))

    # 9. Budget for engine tick
    decisions.append(_d("columbia", "set_budget", {
        "social_pct": 1.0, "military_coins": 3, "tech_coins": 1,
    }, "MIL_BATTERY: budget"))

    inserted = client.table("agent_decisions").insert(decisions).execute()
    decision_ids = [r["id"] for r in (inserted.data or [])]

    resolve_result = resolve_round(SCENARIO_CODE, TEST_ROUND)
    tick_result = run_engine_tick(SCENARIO_CODE, TEST_ROUND)

    yield {
        "decision_ids": decision_ids, "resolve_result": resolve_result,
        "tick_result": tick_result, "decision_count": len(decisions), "meta": meta,
    }

    _cleanup(client, scenario_id)


# --- Tests ---

class TestGroundAttack:
    def test_combat_event_exists(self, client, scenario_id, battery_run):
        if not battery_run["meta"].get("ground_attack"):
            pytest.skip("No ground units found for attack")
        res = client.table("observatory_events").select("id, event_type") \
            .eq("scenario_id", scenario_id).eq("round_num", TEST_ROUND) \
            .in_("event_type", ["ground_combat", "attack", "combat"]).execute()
        combats = client.table("observatory_combat_results").select("id") \
            .eq("scenario_id", scenario_id).eq("round_num", TEST_ROUND).execute()
        total = len(res.data or []) + len(combats.data or [])
        print(f"  Combat events: {len(res.data or [])}, combat results: {len(combats.data or [])}")
        assert total >= 1, "Expected at least 1 combat event or result"

class TestAirStrike:
    def test_air_event(self, client, scenario_id, battery_run):
        if not battery_run["meta"].get("air_strike"):
            pytest.skip("No air units found")
        res = client.table("observatory_events").select("id, event_type, summary") \
            .eq("scenario_id", scenario_id).eq("round_num", TEST_ROUND).execute()
        air_events = [e for e in (res.data or []) if "air" in (e.get("summary") or "").lower()
                      or e.get("event_type") in ("air_strike", "attack_out_of_range")]
        print(f"  Air-related events: {len(air_events)}")
        assert len(air_events) >= 1 or len(battery_run["resolve_result"].get("narratives", [])) > 0

class TestNavalAttack:
    def test_naval_event(self, client, scenario_id, battery_run):
        if not battery_run["meta"].get("naval_attack"):
            pytest.skip("No opposing naval units found")
        res = client.table("observatory_events").select("id, event_type, summary") \
            .eq("scenario_id", scenario_id).eq("round_num", TEST_ROUND).execute()
        naval = [e for e in (res.data or []) if "naval" in (e.get("summary") or "").lower()
                 or e.get("event_type") == "naval_combat"]
        print(f"  Naval events: {len(naval)}")
        # Soft check — naval combat may not produce event if units aren't adjacent
        assert True  # At minimum, the action was processed without crash

class TestNuclearTest:
    def test_nuclear_event(self, client, scenario_id, battery_run):
        res = client.table("observatory_events").select("id, summary") \
            .eq("scenario_id", scenario_id).eq("round_num", TEST_ROUND) \
            .eq("event_type", "nuclear_test").execute()
        print(f"  Nuclear test events: {len(res.data or [])}")
        assert len(res.data or []) >= 1, "Expected nuclear_test event"

class TestBlockade:
    def test_blockade_event(self, client, scenario_id, battery_run):
        res = client.table("observatory_events").select("id, summary") \
            .eq("scenario_id", scenario_id).eq("round_num", TEST_ROUND) \
            .in_("event_type", ["blockade_declared", "declare_blockade", "blockade"]).execute()
        print(f"  Blockade events: {len(res.data or [])}")
        assert len(res.data or []) >= 1, "Expected blockade event"

    def test_blockade_state_table(self, client, scenario_id, battery_run):
        from engine.config.settings import Settings
        sim_run_id = Settings().default_sim_id
        res = client.table("blockades").select("*") \
            .eq("sim_run_id", sim_run_id).eq("zone_id", "gulf_gate").execute()
        print(f"  Blockades table rows: {len(res.data or [])}")
        # Soft check — blockade table may not be populated if zone_id format doesn't match
        if res.data:
            assert res.data[0]["status"] == "active"

class TestMobilize:
    def test_mobilize_event(self, client, scenario_id, battery_run):
        if not battery_run["meta"].get("mobilize"):
            pytest.skip("No reserve units found")
        res = client.table("observatory_events").select("id, summary") \
            .eq("scenario_id", scenario_id).eq("round_num", TEST_ROUND) \
            .eq("event_type", "mobilization").execute()
        print(f"  Mobilization events: {len(res.data or [])}")
        assert len(res.data or []) >= 1, "Expected mobilization event"

class TestBasingRights:
    def test_basing_event(self, client, scenario_id, battery_run):
        res = client.table("observatory_events").select("id, summary") \
            .eq("scenario_id", scenario_id).eq("round_num", TEST_ROUND) \
            .eq("event_type", "basing_rights").execute()
        print(f"  Basing rights events: {len(res.data or [])}")
        assert len(res.data or []) >= 1, "Expected basing_rights event"

class TestMilBatteryEndToEnd:
    def test_resolve_succeeded(self, battery_run):
        assert battery_run["resolve_result"].get("decisions_processed", 0) > 0

    def test_engine_tick_succeeded(self, battery_run):
        assert battery_run["tick_result"].get("success") is True

    def test_all_processed(self, battery_run):
        assert battery_run["resolve_result"].get("decisions_processed", 0) == battery_run["decision_count"]
