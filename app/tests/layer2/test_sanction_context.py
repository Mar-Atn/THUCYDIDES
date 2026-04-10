"""Layer 2 — Sanctions context assembler (CONTRACT_SANCTIONS v1.0 §3).

Step 5 of the sanctions vertical slice. Verifies that
``engine.services.sanction_context`` produces the correct decision-specific
context payload for a sanctions decision-maker.

Uses rounds 55-58 to avoid collision with tariff context (60-63), sanctions
persistence (65-68), tariff persistence (70-73), budget e2e (74-78),
and the full-chain AI tests (83-86).

Run::

    cd app && PYTHONPATH=. python3 -m pytest tests/layer2/test_sanction_context.py -v -s
"""
from __future__ import annotations

import logging

import pytest

from engine.services.sanction_context import build_sanction_context
from engine.services.supabase import get_client

logger = logging.getLogger(__name__)

SCENARIO_CODE = "start_one"
TEST_COUNTRY = "columbia"
TEST_ROUNDS = [55, 56, 57, 58]

EXPECTED_COUNTRY_COUNT = 19  # 20 minus self


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
            new_row["sanction_decision"] = None
            rows.append(new_row)
        for i in range(0, len(rows), 50):
            client.table("country_states_per_round").insert(rows[i : i + 50]).execute()


def _cleanup(client, scenario_id: str) -> None:
    for rn in TEST_ROUNDS:
        for table in (
            "country_states_per_round",
            "global_state_per_round",
            "round_states",
            "agent_decisions",
            "observatory_events",
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
    """Verify gdp, treasury, sector_mix, my_max_damage_pct present."""
    _seed_round_from_r0(client, scenario_id, 55)

    ctx = build_sanction_context(TEST_COUNTRY, SCENARIO_CODE, 55)

    print(f"\n  [test_economic_state] econ={ctx['economic_state']}")

    assert ctx["country_code"] == TEST_COUNTRY
    assert ctx["round_num"] == 55

    eco = ctx["economic_state"]
    assert "gdp" in eco and eco["gdp"] > 0
    assert "treasury" in eco
    assert "inflation" in eco
    assert "sector_mix" in eco
    assert "trade_balance" in eco
    assert "oil_producer" in eco
    assert "stability" in eco
    assert "political_support" in eco
    assert "snapshot_round" in eco

    # KEY: self-vulnerability ceiling must be present
    assert "my_max_damage_pct" in eco, (
        "economic_state must include my_max_damage_pct so the participant "
        "knows their own vulnerability"
    )
    # Columbia (tec22 svc55 ind18 res8) => ~21.9% ceiling
    assert 15.0 <= eco["my_max_damage_pct"] <= 30.0, (
        f"Columbia my_max_damage_pct out of expected band: {eco['my_max_damage_pct']}"
    )


def test_context_has_all_20_countries(client, scenario_id):
    """Verify all 20 country codes appear in country_roster (minus self = 19)."""
    _seed_round_from_r0(client, scenario_id, 55)

    ctx = build_sanction_context(TEST_COUNTRY, SCENARIO_CODE, 55)
    roster = ctx["country_roster"]

    print(f"\n  [test_country_roster] count={len(roster)}")
    codes = {c["code"] for c in roster}
    print(f"  codes={sorted(codes)}")

    assert len(roster) == EXPECTED_COUNTRY_COUNT, (
        f"Expected {EXPECTED_COUNTRY_COUNT} countries in roster, got {len(roster)}"
    )

    assert TEST_COUNTRY not in codes, "Self should not be in country_roster"

    for entry in roster:
        assert "code" in entry
        assert "gdp" in entry
        assert "sector_profile" in entry
        assert "relationship_status" in entry
        assert "coalition_coverage" in entry
        assert "max_damage_pct" in entry
        assert "current_gdp_loss_pct" in entry
        assert 0.0 <= entry["coalition_coverage"] <= 1.0
        assert 0.0 <= entry["max_damage_pct"] <= 30.0


def test_context_has_coalition_coverage_per_target(client, scenario_id):
    """Coverage on Sarmatia must be >0 (real DB has a coalition) and sane.

    Computed against the canonical starting-state sanctions table.
    """
    _seed_round_from_r0(client, scenario_id, 55)

    ctx = build_sanction_context(TEST_COUNTRY, SCENARIO_CODE, 55)
    sarmatia = next(c for c in ctx["country_roster"] if c["code"] == "sarmatia")

    print(f"\n  [test_coverage] sarmatia entry={sarmatia}")

    # Sarmatia has ~12 actors sanctioning it (incl. Cathay L-1 evasion) —
    # canonical L1 regression anchor locks coverage at ~0.509 and GDP loss
    # at ~5.10% (see CONTRACT_SANCTIONS §6.8).
    assert sarmatia["coalition_coverage"] > 0.0, (
        "sarmatia should have some coalition coverage from starting state"
    )
    # Expected around 0.5 given the locked anchor. Tolerance generous.
    assert 0.3 <= sarmatia["coalition_coverage"] <= 0.75, (
        f"sarmatia coverage out of expected band: {sarmatia['coalition_coverage']}"
    )
    # And current_gdp_loss_pct should be in the anchor ballpark (~5%)
    assert 2.0 <= sarmatia["current_gdp_loss_pct"] <= 12.0, (
        f"sarmatia current_gdp_loss_pct unexpected: {sarmatia['current_gdp_loss_pct']}"
    )


def test_context_has_my_sanctions(client, scenario_id):
    """Columbia's existing sanctions appear in my_sanctions list."""
    _seed_round_from_r0(client, scenario_id, 55)

    ctx = build_sanction_context(TEST_COUNTRY, SCENARIO_CODE, 55)
    my = ctx["my_sanctions"]

    print(f"\n  [test_my_sanctions] {my}")

    targets = {s["target"]: s for s in my}
    # Columbia currently sanctions persia, sarmatia, choson at L3
    for t in ("persia", "sarmatia", "choson"):
        assert t in targets, f"Expected {t} in my_sanctions, got {list(targets)}"
        assert targets[t]["level"] == 3, (
            f"Expected {t} level 3, got {targets[t]}"
        )
        assert "sanction" in targets[t]["label"].lower()


def test_context_has_sanctions_on_me(client, scenario_id):
    """Inbound sanctions against columbia appear in sanctions_on_me."""
    _seed_round_from_r0(client, scenario_id, 55)

    ctx = build_sanction_context(TEST_COUNTRY, SCENARIO_CODE, 55)
    on_me = ctx["sanctions_on_me"]

    print(f"\n  [test_sanctions_on_me] {on_me}")

    imposers = {s["imposer"]: s for s in on_me}
    # sarmatia, caribe, choson, persia all L1 against columbia
    for im in ("sarmatia", "caribe", "persia"):
        assert im in imposers, f"Expected {im} in sanctions_on_me, got {list(imposers)}"
        assert imposers[im]["level"] == 1


def test_context_has_decision_rules(client, scenario_id):
    """Verify decision_rules text block has no_change reminder + signed range."""
    _seed_round_from_r0(client, scenario_id, 55)

    ctx = build_sanction_context(TEST_COUNTRY, SCENARIO_CODE, 55)
    rules = ctx["decision_rules"]

    print(f"\n  [test_decision_rules] length={len(rules)}")

    assert "no_change" in rules, "Decision rules must mention no_change"
    assert "-3" in rules and "+3" in rules, (
        "Decision rules must mention the signed level range [-3, +3]"
    )
    assert "evasion" in rules.lower(), (
        "Decision rules must explain evasion support"
    )
    assert "coverage" in rules.lower(), (
        "Decision rules must explain coalition coverage"
    )
    assert "legitimate" in rules.lower(), (
        "Decision rules must remind no_change is legitimate"
    )
    # imposer cost reminder
    assert "no imposer cost" in rules.lower() or "no mechanical fee" in rules.lower() \
        or "do not pay" in rules.lower()

    assert ctx["instruction"], "Instruction must be present"
    assert "JSON" in ctx["instruction"]


def test_context_supports_negative_levels_display(client, scenario_id):
    """Cathay -> Sarmatia L=-1 (evasion support) must appear in cathay's my_sanctions."""
    _seed_round_from_r0(client, scenario_id, 55)

    ctx = build_sanction_context("cathay", SCENARIO_CODE, 55)
    my = ctx["my_sanctions"]

    print(f"\n  [test_negative_levels] cathay my_sanctions={my}")

    sarmatia_entry = next(
        (s for s in my if s["target"] == "sarmatia"), None
    )
    assert sarmatia_entry is not None, (
        f"Expected cathay -> sarmatia L-1 evasion row in my_sanctions; got {my}"
    )
    assert sarmatia_entry["level"] == -1, (
        f"Expected level -1, got {sarmatia_entry}"
    )
    assert "evasion" in sarmatia_entry["label"].lower(), (
        f"Expected 'evasion' in label, got {sarmatia_entry['label']!r}"
    )
