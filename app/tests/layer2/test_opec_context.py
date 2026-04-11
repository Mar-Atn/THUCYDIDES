"""Layer 2 — OPEC context assembler (CONTRACT_OPEC v1.0 §3).

Step 5 of the OPEC vertical slice. Verifies that
``engine.services.opec_context.build_opec_context`` produces the correct
decision-specific context payload for an OPEC+ production decision-maker.

Uses rounds 10-12 to avoid collision with other L2 slices.

Run::

    cd app && PYTHONPATH=. python3 -m pytest tests/layer2/test_opec_context.py -v -s
"""
from __future__ import annotations

import logging

import pytest

from engine.services.opec_context import build_opec_context
from engine.services.supabase import get_client

logger = logging.getLogger(__name__)

SCENARIO_CODE = "start_one"
TEST_COUNTRY = "solaria"  # OPEC+ member
TEST_ROUNDS = [10, 11, 12]

EXPECTED_OIL_PRODUCERS = {
    "columbia", "sarmatia", "solaria", "persia", "mirage", "caribe",
}
VALID_PRODUCTION_LEVELS = {"min", "low", "normal", "high", "max"}
VALID_LEVELS_INCL_NA = VALID_PRODUCTION_LEVELS | {"na"}
VALID_CHOKEPOINT_STATUS = {"none", "partial", "full"}


# ---------------------------------------------------------------------------
# Fixtures + helpers
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def client():
    return get_client()


@pytest.fixture(scope="module")
def scenario_id(client):
    res = (
        client.table("sim_scenarios")
        .select("id")
        .eq("code", SCENARIO_CODE)
        .limit(1)
        .execute()
    )
    assert res.data, f"Scenario '{SCENARIO_CODE}' not found"
    return res.data[0]["id"]


def _seed_round_from_r0(client, scenario_id: str, round_num: int) -> None:
    cs0 = (
        client.table("country_states_per_round")
        .select("*")
        .eq("scenario_id", scenario_id)
        .eq("round_num", 0)
        .execute()
    )
    if cs0.data:
        rows = []
        for row in cs0.data:
            new_row = {k: v for k, v in row.items() if k != "id"}
            new_row["round_num"] = round_num
            new_row["opec_decision"] = None
            rows.append(new_row)
        for i in range(0, len(rows), 50):
            client.table("country_states_per_round").insert(rows[i : i + 50]).execute()

    gs0 = (
        client.table("global_state_per_round")
        .select("*")
        .eq("scenario_id", scenario_id)
        .eq("round_num", 0)
        .execute()
    )
    if gs0.data:
        for row in gs0.data:
            new_row = {k: v for k, v in row.items() if k != "id"}
            new_row["round_num"] = round_num
            client.table("global_state_per_round").insert(new_row).execute()


def _cleanup(client, scenario_id: str) -> None:
    for rn in TEST_ROUNDS:
        for table in (
            "observatory_events",
            "country_states_per_round",
            "global_state_per_round",
            "round_states",
            "agent_decisions",
        ):
            client.table(table).delete().eq(
                "scenario_id", scenario_id
            ).eq("round_num", rn).execute()


@pytest.fixture(autouse=True)
def _isolate(client, scenario_id):
    _cleanup(client, scenario_id)
    yield
    _cleanup(client, scenario_id)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_context_has_economic_state(client, scenario_id):
    _seed_round_from_r0(client, scenario_id, 10)

    ctx = build_opec_context(TEST_COUNTRY, SCENARIO_CODE, 10)

    print(f"\n  [economic_state] {ctx['economic_state']}")

    assert ctx["country_code"] == TEST_COUNTRY
    assert ctx["round_num"] == 10

    eco = ctx["economic_state"]
    assert "gdp" in eco and eco["gdp"] > 0
    assert "treasury" in eco
    assert "inflation" in eco
    assert "stability" in eco
    assert "my_oil_production_mbpd" in eco
    assert "my_world_oil_share_pct" in eco
    assert "my_oil_revenue_last_round" in eco
    assert "my_current_production_level" in eco

    # Solaria = 10 mbpd
    assert eco["my_oil_production_mbpd"] == 10.0
    # 10 / 40.8 ≈ 24.5%
    assert 20.0 <= eco["my_world_oil_share_pct"] <= 30.0
    # Solaria current level should be 'normal' at R0 seed
    assert eco["my_current_production_level"] == "normal"
    # Oil revenue = price * mbpd * 0.009 — roughly 80 * 10 * 0.009 ≈ 7.2
    assert eco["my_oil_revenue_last_round"] > 0.0


def test_context_has_oil_market_state(client, scenario_id):
    _seed_round_from_r0(client, scenario_id, 10)

    ctx = build_opec_context(TEST_COUNTRY, SCENARIO_CODE, 10)
    mkt = ctx["oil_market_state"]

    print(f"\n  [oil_market_state] {mkt}")

    assert "current_oil_price" in mkt
    assert mkt["current_oil_price"] > 0
    assert "total_world_mbpd" in mkt
    # 13 + 10 + 10 + 3.5 + 3.5 + 0.8 = 40.8
    assert 40.0 <= mkt["total_world_mbpd"] <= 41.0
    assert "opec_share_pct" in mkt
    # 5 OPEC members: 10 + 10 + 3.5 + 3.5 + 0.8 = 27.8 → 68%
    assert 60.0 <= mkt["opec_share_pct"] <= 75.0


def test_context_has_oil_price_history(client, scenario_id):
    _seed_round_from_r0(client, scenario_id, 10)

    ctx = build_opec_context(TEST_COUNTRY, SCENARIO_CODE, 10)
    history = ctx["oil_price_history"]

    print(f"\n  [oil_price_history] len={len(history)} sample={history[:3]}")
    assert isinstance(history, list)
    # We seeded R0 → R10 expects history for rounds [0..9] for any already
    # persisted rounds. At minimum R0 should be present (we just seeded it).
    for entry in history:
        assert "round" in entry
        assert "oil_price" in entry
        assert entry["round"] < 10
        assert entry["oil_price"] > 0
    # Must be sorted ascending
    if len(history) > 1:
        rounds = [e["round"] for e in history]
        assert rounds == sorted(rounds)


def test_context_has_all_6_oil_producers(client, scenario_id):
    _seed_round_from_r0(client, scenario_id, 10)

    ctx = build_opec_context(TEST_COUNTRY, SCENARIO_CODE, 10)
    table = ctx["oil_producers_table"]

    print(f"\n  [oil_producers_table] count={len(table)}")
    for row in table:
        print(f"    {row}")

    codes = {r["code"] for r in table}
    assert codes == EXPECTED_OIL_PRODUCERS, (
        f"Expected {EXPECTED_OIL_PRODUCERS}, got {codes}"
    )
    # Sorted by mbpd desc — first should be columbia (13 mbpd)
    assert table[0]["code"] == "columbia"
    mbpds = [r["mbpd"] for r in table]
    assert mbpds == sorted(mbpds, reverse=True)
    for row in table:
        assert row["current_level"] in VALID_LEVELS_INCL_NA
    # Non-member columbia must show 'na'
    columbia_row = next(r for r in table if r["code"] == "columbia")
    assert columbia_row["current_level"] == "na"


def test_context_current_level_reflects_snapshot(client, scenario_id):
    """Override Solaria opec_production to 'min' and verify it propagates."""
    _seed_round_from_r0(client, scenario_id, 11)

    client.table("country_states_per_round").update({
        "opec_production": "min"
    }).eq("scenario_id", scenario_id).eq("round_num", 11).eq(
        "country_code", "solaria"
    ).execute()

    ctx = build_opec_context(TEST_COUNTRY, SCENARIO_CODE, 11)

    print(f"\n  [override test] own={ctx['economic_state']['my_current_production_level']}")

    assert ctx["economic_state"]["my_current_production_level"] == "min"
    solaria_row = next(
        r for r in ctx["oil_producers_table"] if r["code"] == "solaria"
    )
    assert solaria_row["current_level"] == "min"


def test_context_has_chokepoint_blockades(client, scenario_id):
    _seed_round_from_r0(client, scenario_id, 10)

    ctx = build_opec_context(TEST_COUNTRY, SCENARIO_CODE, 10)
    blockades = ctx["chokepoint_blockades"]

    print(f"\n  [chokepoint_blockades] {blockades}")

    assert set(blockades.keys()) == {
        "gulf_gate", "caribe_passage", "formosa_strait"
    }
    for key, status in blockades.items():
        assert status in VALID_CHOKEPOINT_STATUS, (
            f"{key} has invalid status {status!r}"
        )


def test_context_has_sanctions_on_producers(client, scenario_id):
    _seed_round_from_r0(client, scenario_id, 10)

    ctx = build_opec_context(TEST_COUNTRY, SCENARIO_CODE, 10)
    sanc = ctx["sanctions_on_producers"]

    print(f"\n  [sanctions_on_producers] {sanc}")

    assert isinstance(sanc, list)
    # Must have one row per producer (6)
    codes = {s["code"] for s in sanc}
    assert codes == EXPECTED_OIL_PRODUCERS
    for row in sanc:
        assert "max_level" in row
        assert "num_sanctioners" in row
        assert "triggers_supply_penalty" in row
        assert row["max_level"] >= 0
        assert row["num_sanctioners"] >= 0
    # Sarmatia and Persia should be sanctioned at starting state (L2+)
    sarmatia = next(s for s in sanc if s["code"] == "sarmatia")
    persia = next(s for s in sanc if s["code"] == "persia")
    assert sarmatia["max_level"] >= 2, f"Expected Sarmatia >= L2, got {sarmatia}"
    assert persia["max_level"] >= 2, f"Expected Persia >= L2, got {persia}"
    assert sarmatia["triggers_supply_penalty"] is True
    assert persia["triggers_supply_penalty"] is True
    assert sarmatia["num_sanctioners"] > 0


def test_context_has_tariffs_on_producers(client, scenario_id):
    _seed_round_from_r0(client, scenario_id, 10)

    ctx = build_opec_context(TEST_COUNTRY, SCENARIO_CODE, 10)
    tariffs = ctx["tariffs_on_producers"]

    print(f"\n  [tariffs_on_producers] count={len(tariffs)}")
    for row in tariffs[:5]:
        print(f"    {row}")

    assert isinstance(tariffs, list)
    # At least one tariff involving an oil producer should exist at
    # starting state (columbia->persia etc).
    assert len(tariffs) >= 1
    for row in tariffs:
        assert "imposer" in row
        assert "target" in row
        assert "level" in row
        # Either side must be a producer
        assert row["imposer"] in EXPECTED_OIL_PRODUCERS or \
               row["target"] in EXPECTED_OIL_PRODUCERS


def test_context_has_decision_rules(client, scenario_id):
    _seed_round_from_r0(client, scenario_id, 10)

    ctx = build_opec_context(TEST_COUNTRY, SCENARIO_CODE, 10)
    rules = ctx["decision_rules"]

    print(f"\n  [decision_rules] length={len(rules)}")

    assert "no_change" in rules
    assert "legitimate" in rules.lower()
    assert "min" in rules and "max" in rules
    assert "2x" in rules.lower() or "cartel" in rules.lower()

    assert ctx["instruction"], "Instruction must be present"
    assert "JSON" in ctx["instruction"]
    assert "30" in ctx["instruction"]


def test_context_rejects_non_opec_member(client, scenario_id):
    """Non-OPEC members must be rejected — matches validator's NOT_OPEC_MEMBER."""
    _seed_round_from_r0(client, scenario_id, 10)

    with pytest.raises(ValueError, match="NOT_OPEC_MEMBER"):
        build_opec_context("columbia", SCENARIO_CODE, 10)
