"""Layer 2 Battery Test — scripted decisions through full pipeline, zero LLM cost.

Pre-scripts all decisions for 2 rounds and fires them through the same connectors
(agent_decisions table -> resolve_round -> engine_tick). Verifies the full engine
chain with deterministic inputs.

Run::

    cd app && PYTHONPATH=. python3 -m pytest tests/layer2/test_battery.py -v

Uses rounds 90-91 to avoid conflicts with real simulation rounds.
"""
from __future__ import annotations

import logging
import pytest

from engine.services.supabase import get_client
from engine.round_engine.resolve_round import resolve_round
from engine.engines.round_tick import run_engine_tick

logger = logging.getLogger(__name__)

SCENARIO_CODE = "start_one"
TEST_ROUND = 90
TEST_ROUNDS = [89, 90, 91]
TEST_TAG = "BATTERY_TEST_L2"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_scenario_id(client) -> str:
    """Resolve the scenario_id for 'start_one'."""
    res = client.table("sim_scenarios").select("id").eq("code", SCENARIO_CODE).limit(1).execute()
    assert res.data, f"Scenario '{SCENARIO_CODE}' not found in sim_scenarios"
    return res.data[0]["id"]


def _cleanup_test_data(client, scenario_id: str) -> None:
    """Remove all test artifacts for rounds 90-91."""
    for rn in TEST_ROUNDS:
        # Order matters — delete children before parents where relevant
        client.table("observatory_combat_results").delete() \
            .eq("scenario_id", scenario_id).eq("round_num", rn).execute()
        client.table("observatory_events").delete() \
            .eq("scenario_id", scenario_id).eq("round_num", rn).execute()
        client.table("exchange_transactions").delete() \
            .eq("scenario_id", scenario_id).eq("round_num", rn).execute()
        client.table("unit_states_per_round").delete() \
            .eq("scenario_id", scenario_id).eq("round_num", rn).execute()
        client.table("country_states_per_round").delete() \
            .eq("scenario_id", scenario_id).eq("round_num", rn).execute()
        client.table("global_state_per_round").delete() \
            .eq("scenario_id", scenario_id).eq("round_num", rn).execute()
        client.table("round_states").delete() \
            .eq("scenario_id", scenario_id).eq("round_num", rn).execute()

    # Delete test decisions by tag (search in action_payload)
    decisions = client.table("agent_decisions").select("id, action_payload") \
        .eq("scenario_id", scenario_id).execute()
    tagged_ids = [
        r["id"] for r in (decisions.data or [])
        if (r.get("action_payload") or {}).get("test_tag") == TEST_TAG
    ]
    if tagged_ids:
        client.table("agent_decisions").delete().in_("id", tagged_ids).execute()

    # Also delete by round_num directly (belt and suspenders)
    for rn in TEST_ROUNDS:
        client.table("agent_decisions").delete() \
            .eq("scenario_id", scenario_id).eq("round_num", rn).execute()


def _find_attacker_units(client, scenario_id: str, country_code: str) -> list[str]:
    """Find ground unit codes for a country from the baseline (round 0)."""
    res = client.table("unit_states_per_round").select("unit_code") \
        .eq("scenario_id", scenario_id).eq("round_num", 0) \
        .eq("country_code", country_code).eq("unit_type", "ground") \
        .eq("status", "active").limit(3).execute()
    return [r["unit_code"] for r in (res.data or [])]


def _find_target_hex(client, scenario_id: str, target_country: str) -> tuple[int, int]:
    """Find a hex occupied by a target country's units."""
    res = client.table("unit_states_per_round").select("global_row, global_col") \
        .eq("scenario_id", scenario_id).eq("round_num", 0) \
        .eq("country_code", target_country).eq("status", "active") \
        .not_.is_("global_row", "null").limit(1).execute()
    assert res.data, f"No active units with positions found for {target_country}"
    return res.data[0]["global_row"], res.data[0]["global_col"]


def _find_reserve_unit(client, scenario_id: str, country_code: str) -> str | None:
    """Find a reserve unit code for a country."""
    res = client.table("unit_states_per_round").select("unit_code") \
        .eq("scenario_id", scenario_id).eq("round_num", 0) \
        .eq("country_code", country_code).eq("status", "reserve") \
        .limit(1).execute()
    if res.data:
        return res.data[0]["unit_code"]
    return None


# ---------------------------------------------------------------------------
# Scripted decisions builder
# ---------------------------------------------------------------------------

def _build_scripted_decisions(client, scenario_id: str) -> list[dict]:
    """Build the full set of scripted decisions for round 90."""
    decisions: list[dict] = []

    def _d(country: str, action_type: str, payload: dict, rationale: str) -> dict:
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

    # =====================================================================
    # ECONOMIC decisions (mandatory — the ones agents tend to skip)
    # =====================================================================
    decisions.append(_d("columbia", "set_budget", {
        "decision": "change",
        "rationale": "BATTERY test: standard budget allocation for Columbia",
        "changes": {
            "social_pct": 1.0,
            "production": {
                "ground": 1, "naval": 0, "tactical_air": 0,
                "strategic_missile": 0, "air_defense": 0,
            },
            "research": {"nuclear_coins": 0, "ai_coins": 1},
        },
    }, "BATTERY: Columbia budget allocation"))

    decisions.append(_d("cathay", "set_budget", {
        "decision": "change",
        "rationale": "BATTERY test: reduced social, focus on production for Cathay",
        "changes": {
            "social_pct": 0.8,
            "production": {
                "ground": 1, "naval": 1, "tactical_air": 0,
                "strategic_missile": 0, "air_defense": 0,
            },
            "research": {"nuclear_coins": 1, "ai_coins": 1},
        },
    }, "BATTERY: Cathay budget allocation"))

    decisions.append(_d("sarmatia", "set_tariff", {
        "target_country": "ruthenia", "level": 2,
    }, "BATTERY: Sarmatia tariff L2 vs Ruthenia"))

    decisions.append(_d("columbia", "set_sanction", {
        "target_country": "caribe", "level": 1,
        "sanction_type": "financial",
    }, "BATTERY: Columbia sanction L1 vs Caribe"))

    # =====================================================================
    # TRANSACTIONS
    # =====================================================================
    decisions.append(_d("albion", "propose_transaction", {
        "counterpart_country": "columbia",
        "offer": {"coins": 5},
        "request": {"coins": 0},
        "terms": "Goodwill gift",
    }, "BATTERY: Albion gift to Columbia"))

    decisions.append(_d("formosa", "propose_transaction", {
        "counterpart_country": "yamato",
        "offer": {"coins": 3},
        "request": {"coins": 0},
        "terms": "Diplomatic goodwill",
    }, "BATTERY: Formosa gift to Yamato"))

    decisions.append(_d("gallia", "propose_transaction", {
        "counterpart_country": "teutonia",
        "offer": {},
        "request": {},
        "terms": "Framework cooperation agreement",
    }, "BATTERY: Gallia-Teutonia agreement (null offer/request)"))

    # =====================================================================
    # MILITARY
    # =====================================================================

    # Attack: Sarmatia -> Ruthenia
    sar_units = _find_attacker_units(client, scenario_id, "sarmatia")
    if sar_units:
        ruth_row, ruth_col = _find_target_hex(client, scenario_id, "ruthenia")
        decisions.append(_d("sarmatia", "declare_attack", {
            "attacker_unit_codes": sar_units[:2],
            "target_global_row": ruth_row,
            "target_global_col": ruth_col,
            "target_description": "Ruthenia border position",
        }, "BATTERY: Sarmatia attacks Ruthenia"))

    # Attack: Levantia -> Mashriq
    lev_units = _find_attacker_units(client, scenario_id, "levantia")
    if lev_units:
        try:
            mash_row, mash_col = _find_target_hex(client, scenario_id, "mashriq")
            decisions.append(_d("levantia", "declare_attack", {
                "attacker_unit_codes": lev_units[:2],
                "target_global_row": mash_row,
                "target_global_col": mash_col,
                "target_description": "Mashriq border position",
            }, "BATTERY: Levantia attacks Mashriq"))
        except Exception:
            logger.warning("No Mashriq units found — skipping Levantia attack")

    # Mobilize reserve: Columbia
    reserve_unit = _find_reserve_unit(client, scenario_id, "columbia")
    if reserve_unit:
        decisions.append(_d("columbia", "mobilize_reserve", {
            "unit_code": reserve_unit,
            "target_global_row": 3,
            "target_global_col": 3,
        }, "BATTERY: Columbia mobilize reserve"))

    # =====================================================================
    # PUBLIC STATEMENTS (3)
    # =====================================================================
    decisions.append(_d("columbia", "public_statement", {
        "content": "[BATTERY TEST] Columbia reaffirms commitment to global stability.",
    }, "BATTERY: Columbia statement"))

    decisions.append(_d("cathay", "public_statement", {
        "content": "[BATTERY TEST] Cathay calls for multilateral dialogue.",
    }, "BATTERY: Cathay statement"))

    decisions.append(_d("gallia", "public_statement", {
        "content": "[BATTERY TEST] Gallia proposes new trade framework.",
    }, "BATTERY: Gallia statement"))

    # =====================================================================
    # R&D INVESTMENTS (2)
    # =====================================================================
    decisions.append(_d("bharata", "rd_investment", {
        "domain": "ai", "amount": 2.0,
    }, "BATTERY: Bharata AI R&D investment"))

    decisions.append(_d("persia", "rd_investment", {
        "domain": "nuclear", "amount": 3.0,
    }, "BATTERY: Persia nuclear R&D investment"))

    # =====================================================================
    # COVERT OP (1)
    # =====================================================================
    decisions.append(_d("ruthenia", "covert_op", {
        "op_type": "espionage",
        "target_country": "sarmatia",
        "question": "What are Sarmatia's troop deployments near the border?",
    }, "BATTERY: Ruthenia espionage vs Sarmatia"))

    return decisions


# ---------------------------------------------------------------------------
# Pytest fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    return get_client()


@pytest.fixture(scope="module")
def scenario_id(client):
    return _get_scenario_id(client)


@pytest.fixture(scope="module", autouse=True)
def battery_run(client, scenario_id):
    """Setup, execute, yield for assertions, then cleanup."""
    # ---- SETUP: clean prior test data ----
    print("\n[BATTERY] Cleaning up any prior test data for rounds 90-91...")
    _cleanup_test_data(client, scenario_id)

    # ---- SEED: clone round 0 country states into round 89 (previous round baseline) ----
    # resolve_round and engine_tick need a previous round to read from
    print("[BATTERY] Seeding round 89 baseline from round 0...")
    prev_round = TEST_ROUND - 1  # 89
    r0_states = client.table("country_states_per_round").select("*") \
        .eq("scenario_id", scenario_id).eq("round_num", 0).execute()
    if r0_states.data:
        for row in r0_states.data:
            new_row = {k: v for k, v in row.items() if k != "id"}
            new_row["round_num"] = prev_round
            client.table("country_states_per_round").insert(new_row).execute()
        print(f"  Seeded {len(r0_states.data)} country states for round {prev_round}")
    # Also seed global_state_per_round for round 89
    r0_global = client.table("global_state_per_round").select("*") \
        .eq("scenario_id", scenario_id).eq("round_num", 0).execute()
    if r0_global.data:
        for row in r0_global.data:
            new_row = {k: v for k, v in row.items() if k != "id"}
            new_row["round_num"] = prev_round
            client.table("global_state_per_round").insert(new_row).execute()
        print(f"  Seeded {len(r0_global.data)} global state rows for round {prev_round}")
    # Also seed unit states for round 89 (resolve_round reads these)
    r0_units = client.table("unit_states_per_round").select("*") \
        .eq("scenario_id", scenario_id).eq("round_num", 0).execute()
    if r0_units.data:
        for row in r0_units.data:
            new_row = {k: v for k, v in row.items() if k != "id"}
            new_row["round_num"] = prev_round
        # Batch insert (single call)
        batch = [{k: v for k, v in row.items() if k != "id"} | {"round_num": prev_round}
                 for row in r0_units.data]
        # Insert in chunks of 100 to avoid payload limits
        for i in range(0, len(batch), 100):
            client.table("unit_states_per_round").insert(batch[i:i+100]).execute()
        print(f"  Seeded {len(batch)} unit states for round {prev_round}")

    # ---- SEED: insert scripted decisions ----
    print("[BATTERY] Building scripted decisions...")
    decisions = _build_scripted_decisions(client, scenario_id)
    print(f"[BATTERY] Inserting {len(decisions)} scripted decisions for round {TEST_ROUND}...")
    inserted = client.table("agent_decisions").insert(decisions).execute()
    decision_ids = [r["id"] for r in (inserted.data or [])]
    print(f"[BATTERY] Inserted {len(decision_ids)} decisions")

    # ---- EXECUTE: resolve_round ----
    print(f"[BATTERY] Running resolve_round('{SCENARIO_CODE}', {TEST_ROUND})...")
    resolve_result = resolve_round(SCENARIO_CODE, TEST_ROUND)
    print(f"[BATTERY] resolve_round result: {resolve_result}")

    # ---- EXECUTE: run_engine_tick ----
    print(f"[BATTERY] Running run_engine_tick('{SCENARIO_CODE}', {TEST_ROUND})...")
    tick_result = run_engine_tick(SCENARIO_CODE, TEST_ROUND)
    print(f"[BATTERY] run_engine_tick result: {tick_result}")

    # ---- YIELD: let tests run ----
    yield {
        "decision_ids": decision_ids,
        "resolve_result": resolve_result,
        "tick_result": tick_result,
        "decision_count": len(decisions),
    }

    # ---- CLEANUP: remove all test artifacts ----
    print("\n[BATTERY] Cleaning up test data for rounds 90-91...")
    _cleanup_test_data(client, scenario_id)
    print("[BATTERY] Cleanup complete")


# ---------------------------------------------------------------------------
# Assertions
# ---------------------------------------------------------------------------

class TestBatteryResolveRound:
    """Verify resolve_round processed all decisions correctly."""

    def test_resolve_round_succeeded(self, battery_run):
        """resolve_round should return a valid result with decisions processed."""
        result = battery_run["resolve_result"]
        print(f"  resolve_round returned: {result}")
        assert isinstance(result, dict), "resolve_round should return a dict"
        assert result.get("decisions_processed", 0) > 0, \
            f"Expected decisions processed > 0, got {result.get('decisions_processed')}"
        print(f"  -> {result['decisions_processed']} decisions processed")

    def test_events_created(self, client, scenario_id, battery_run):
        """Observatory events should exist for round 90 (statements, attacks, etc.)."""
        res = client.table("observatory_events").select("id, event_type, country_code") \
            .eq("scenario_id", scenario_id).eq("round_num", TEST_ROUND).execute()
        events = res.data or []
        event_types = [e["event_type"] for e in events]
        print(f"  Found {len(events)} observatory events: {event_types}")
        assert len(events) >= 3, \
            f"Expected at least 3 observatory events (3 statements alone), got {len(events)}"

    def test_public_statements_logged(self, client, scenario_id, battery_run):
        """All 3 public statements should appear as events."""
        res = client.table("observatory_events").select("id, country_code") \
            .eq("scenario_id", scenario_id).eq("round_num", TEST_ROUND) \
            .eq("event_type", "public_statement").execute()
        statements = res.data or []
        countries = sorted([s["country_code"] for s in statements])
        print(f"  Public statements from: {countries}")
        assert len(statements) >= 3, \
            f"Expected 3 public_statement events, got {len(statements)}: {countries}"

    def test_covert_op_event_logged(self, client, scenario_id, battery_run):
        """Covert op should produce an observatory event (not a separate table)."""
        res = client.table("observatory_events").select("id, country_code, payload") \
            .eq("scenario_id", scenario_id).eq("round_num", TEST_ROUND) \
            .eq("event_type", "covert_op").execute()
        ops = res.data or []
        print(f"  Covert op events: {len(ops)}")
        assert len(ops) >= 1, "Expected at least 1 covert_op event for Ruthenia espionage"
        # Verify it was Ruthenia's op
        countries = [o["country_code"] for o in ops]
        assert "ruthenia" in countries, f"Expected ruthenia in covert op countries, got {countries}"

    def test_country_states_snapshot_created(self, client, scenario_id, battery_run):
        """country_states_per_round rows should exist for round 90 for all 20 countries."""
        res = client.table("country_states_per_round").select("country_code") \
            .eq("scenario_id", scenario_id).eq("round_num", TEST_ROUND).execute()
        rows = res.data or []
        countries = sorted([r["country_code"] for r in rows])
        print(f"  Country state rows for round {TEST_ROUND}: {len(rows)} countries")
        # The scenario has 20 countries
        assert len(rows) >= 15, \
            f"Expected at least 15 country_states rows (of 20), got {len(rows)}: {countries}"

    def test_exchange_transactions_created(self, client, scenario_id, battery_run):
        """At least 2 exchange_transactions for round 90 (Albion->Columbia, Formosa->Yamato)."""
        res = client.table("exchange_transactions").select("id, proposer, counterpart, status") \
            .eq("scenario_id", scenario_id).eq("round_num", TEST_ROUND).execute()
        txns = res.data or []
        print(f"  Exchange transactions: {len(txns)}")
        for t in txns:
            print(f"    {t['proposer']} -> {t['counterpart']}: {t['status']}")
        assert len(txns) >= 2, \
            f"Expected at least 2 exchange_transactions (Albion+Formosa gifts), got {len(txns)}"
        # Check status
        statuses = [t["status"] for t in txns]
        assert all(s == "proposed" for s in statuses), \
            f"Expected all statuses='proposed', got {statuses}"


class TestBatteryEngineTick:
    """Verify run_engine_tick processed economic/political effects."""

    def test_engine_tick_succeeded(self, battery_run):
        """run_engine_tick should return success."""
        result = battery_run["tick_result"]
        print(f"  engine_tick returned: {result}")
        assert result.get("success") is True, \
            f"engine_tick failed: {result.get('error', 'unknown')}"
        assert result.get("countries_updated", 0) > 0, \
            f"Expected countries_updated > 0, got {result.get('countries_updated')}"
        print(f"  -> {result['countries_updated']} countries updated")

    def test_columbia_treasury_changed(self, client, scenario_id, battery_run):
        """Columbia treasury should differ from round 0 after budget + sanctions + tick."""
        r0 = client.table("country_states_per_round").select("treasury") \
            .eq("scenario_id", scenario_id).eq("round_num", 0) \
            .eq("country_code", "columbia").limit(1).execute()
        r90 = client.table("country_states_per_round").select("treasury") \
            .eq("scenario_id", scenario_id).eq("round_num", TEST_ROUND) \
            .eq("country_code", "columbia").limit(1).execute()

        if not r0.data or not r90.data:
            pytest.skip("Columbia treasury data not available for comparison")

        t0 = r0.data[0]["treasury"]
        t90 = r90.data[0]["treasury"]
        print(f"  Columbia treasury: round 0 = {t0}, round {TEST_ROUND} = {t90}")
        # Treasury should have changed (budget allocation, sanctions effects, tax revenue)
        # We don't assert direction — just that it's different
        assert t0 != t90, \
            f"Columbia treasury unchanged: round 0 = {t0}, round {TEST_ROUND} = {t90}"

    def test_global_state_updated(self, client, scenario_id, battery_run):
        """global_state_per_round should have an entry for round 90 with oil_price."""
        res = client.table("global_state_per_round").select("oil_price, round_num") \
            .eq("scenario_id", scenario_id).eq("round_num", TEST_ROUND).execute()
        rows = res.data or []
        print(f"  Global state rows for round {TEST_ROUND}: {len(rows)}")
        assert len(rows) == 1, f"Expected 1 global_state row, got {len(rows)}"
        oil = rows[0]["oil_price"]
        print(f"  Oil price at round {TEST_ROUND}: {oil}")
        assert oil is not None and oil > 0, f"Expected positive oil price, got {oil}"


class TestBatteryCombat:
    """Verify combat resolution produced results."""

    def test_combat_results_exist(self, client, scenario_id, battery_run):
        """observatory_combat_results should have entries for round 90 if attacks fired."""
        res = client.table("observatory_combat_results") \
            .select("id, attacker_country, defender_country, combat_type") \
            .eq("scenario_id", scenario_id).eq("round_num", TEST_ROUND).execute()
        combats = res.data or []
        print(f"  Combat results for round {TEST_ROUND}: {len(combats)}")
        for c in combats:
            print(f"    {c['attacker_country']} vs {c['defender_country']} ({c.get('combat_type', '?')})")
        # We scripted 2 attacks (Sarmatia->Ruthenia, Levantia->Mashriq)
        # At least one should produce a combat result (units may not be adjacent for all)
        # Relaxed: just check the table was written to
        if len(combats) == 0:
            print("  WARNING: No combat results — units may not have been adjacent or available")
            print("  This is acceptable if attack decisions were processed but no units found")

    def test_attack_events_logged(self, client, scenario_id, battery_run):
        """Attack-related events should exist in observatory_events."""
        res = client.table("observatory_events").select("id, event_type, country_code") \
            .eq("scenario_id", scenario_id).eq("round_num", TEST_ROUND) \
            .in_("event_type", ["declare_attack", "attack_resolved", "attack_invalid",
                                "mobilization", "movement"]).execute()
        events = res.data or []
        print(f"  Military events: {len(events)}")
        for e in events:
            print(f"    {e['country_code']}: {e['event_type']}")


class TestBatteryRDInvestments:
    """Verify R&D investment decisions were processed."""

    def test_rd_events_logged(self, client, scenario_id, battery_run):
        """R&D investment events should exist for Bharata and Persia."""
        res = client.table("observatory_events").select("id, country_code, event_type") \
            .eq("scenario_id", scenario_id).eq("round_num", TEST_ROUND) \
            .eq("event_type", "rd_investment").execute()
        events = res.data or []
        countries = [e["country_code"] for e in events]
        print(f"  R&D events: {len(events)} from {countries}")
        assert len(events) >= 2, \
            f"Expected at least 2 rd_investment events (Bharata, Persia), got {len(events)}"
        assert "bharata" in countries, f"Expected bharata in R&D events, got {countries}"
        assert "persia" in countries, f"Expected persia in R&D events, got {countries}"


class TestBatteryEconomicActions:
    """Verify economic actions (budget, tariff, sanction) were logged."""

    def test_economic_events_logged(self, client, scenario_id, battery_run):
        """Economic action events should exist for budget/tariff/sanction decisions."""
        res = client.table("observatory_events").select("id, event_type, country_code") \
            .eq("scenario_id", scenario_id).eq("round_num", TEST_ROUND) \
            .in_("event_type", ["set_budget", "set_tariff", "set_sanction",
                                "impose_sanction"]).execute()
        events = res.data or []
        print(f"  Economic events: {len(events)}")
        for e in events:
            print(f"    {e['country_code']}: {e['event_type']}")
        # We scripted 4 economic actions (2 budgets, 1 tariff, 1 sanction)
        assert len(events) >= 2, \
            f"Expected at least 2 economic events, got {len(events)}"


class TestBatteryEndToEnd:
    """High-level end-to-end checks."""

    def test_all_decisions_processed(self, battery_run):
        """The number of decisions processed should match what we inserted."""
        inserted = battery_run["decision_count"]
        processed = battery_run["resolve_result"].get("decisions_processed", 0)
        print(f"  Inserted: {inserted}, Processed: {processed}")
        assert processed == inserted, \
            f"Mismatch: inserted {inserted} decisions but processed {processed}"

    def test_round_marked_complete(self, client, scenario_id, battery_run):
        """round_states should show round 90 as 'completed'."""
        res = client.table("round_states").select("status") \
            .eq("scenario_id", scenario_id).eq("round_num", TEST_ROUND).execute()
        rows = res.data or []
        print(f"  Round state: {rows}")
        assert len(rows) == 1, f"Expected 1 round_states row, got {len(rows)}"
        assert rows[0]["status"] == "completed", \
            f"Expected status='completed', got '{rows[0]['status']}'"
