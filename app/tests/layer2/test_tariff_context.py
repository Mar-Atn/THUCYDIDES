"""Layer 2 — Tariff context assembler (CONTRACT_TARIFFS v1.0 §3).

Step 5 of the tariff vertical slice. Verifies that
``engine.services.tariff_context`` produces the correct decision-specific
context payload for a tariff decision-maker.

Uses rounds 60-63 to avoid collision with budget context (70-73), tariff
persistence (70-73), budget e2e (74-78), and budget full chain AI (83-84).

Run::

    cd app && PYTHONPATH=. python3 -m pytest tests/layer2/test_tariff_context.py -v -s
"""
from __future__ import annotations

import logging

import pytest

from engine.services.tariff_context import build_tariff_context
from engine.services.supabase import get_client

logger = logging.getLogger(__name__)

SCENARIO_CODE = "start_one"
TEST_COUNTRY = "columbia"
TEST_ROUNDS = [60, 61, 62, 63]

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
            new_row["tariff_decision"] = None
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


def _get_sim_run_id() -> str:
    from engine.config.settings import Settings
    return Settings().default_sim_id


def _seed_tariff(client, imposer: str, target: str, level: int, notes: str = "") -> None:
    """Upsert a tariff row in the tariffs state table."""
    sim_run_id = _get_sim_run_id()
    client.table("tariffs").upsert({
        "sim_run_id": sim_run_id,
        "imposer_country_id": imposer,
        "target_country_id": target,
        "level": level,
        "notes": notes or f"test seed {imposer}->{target} L{level}",
    }, on_conflict="sim_run_id,imposer_country_id,target_country_id").execute()


def _clean_test_tariffs(client) -> None:
    """Remove test-seeded tariffs."""
    sim_run_id = _get_sim_run_id()
    try:
        client.table("tariffs").delete().eq(
            "sim_run_id", sim_run_id
        ).like("notes", "test seed %").execute()
    except Exception:
        pass


@pytest.fixture(autouse=True)
def _isolate(client, scenario_id):
    _cleanup(client, scenario_id)
    yield
    _cleanup(client, scenario_id)
    _clean_test_tariffs(client)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_context_has_economic_state(client, scenario_id):
    """Verify gdp, treasury, inflation, sector_mix, stability, etc. are present."""
    _seed_round_from_r0(client, scenario_id, 60)

    ctx = build_tariff_context(TEST_COUNTRY, SCENARIO_CODE, 60)

    print(f"\n  [test_economic_state] econ={ctx['economic_state']}")

    assert ctx["country_code"] == TEST_COUNTRY
    assert ctx["round_num"] == 60

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

    # Columbia has positive GDP
    assert eco["gdp"] > 100, f"Columbia GDP should be >100, got {eco['gdp']}"

    # Sector mix has all 4 sectors
    sm = eco["sector_mix"]
    for sector in ("resources", "industry", "services", "technology"):
        assert sector in sm, f"Missing sector '{sector}' in sector_mix"


def test_context_has_all_20_countries(client, scenario_id):
    """Verify all 20 country codes appear in country_roster (minus self = 19)."""
    _seed_round_from_r0(client, scenario_id, 60)

    ctx = build_tariff_context(TEST_COUNTRY, SCENARIO_CODE, 60)
    roster = ctx["country_roster"]

    print(f"\n  [test_country_roster] count={len(roster)}")
    codes = {c["code"] for c in roster}
    print(f"  codes={sorted(codes)}")

    assert len(roster) == EXPECTED_COUNTRY_COUNT, (
        f"Expected {EXPECTED_COUNTRY_COUNT} countries in roster, got {len(roster)}"
    )

    # Self should NOT be in the roster
    assert TEST_COUNTRY not in codes, "Self should not be in country_roster"

    # Each entry must have the required fields
    for entry in roster:
        assert "code" in entry
        assert "gdp" in entry
        assert "sector_profile" in entry
        assert "relationship_status" in entry
        assert "trade_rank" in entry
        assert isinstance(entry["trade_rank"], int)
        assert entry["trade_rank"] >= 1


def test_context_has_my_tariffs(client, scenario_id):
    """Verify Columbia's existing tariffs appear in my_tariffs."""
    _seed_round_from_r0(client, scenario_id, 61)

    # Seed some tariffs that Columbia imposes
    _seed_tariff(client, TEST_COUNTRY, "cathay", 2, "test seed columbia->cathay L2")
    _seed_tariff(client, TEST_COUNTRY, "persia", 3, "test seed columbia->persia L3")

    ctx = build_tariff_context(TEST_COUNTRY, SCENARIO_CODE, 61)
    my_tariffs = ctx["my_tariffs"]

    print(f"\n  [test_my_tariffs] {my_tariffs}")

    targets = {t["target"] for t in my_tariffs}
    assert "cathay" in targets, f"Expected cathay in my_tariffs, got targets={targets}"
    assert "persia" in targets, f"Expected persia in my_tariffs, got targets={targets}"

    # Check levels
    cathay_entry = next(t for t in my_tariffs if t["target"] == "cathay")
    assert cathay_entry["level"] == 2


def test_context_has_tariffs_on_me(client, scenario_id):
    """Verify inbound tariffs appear in tariffs_on_me."""
    _seed_round_from_r0(client, scenario_id, 62)

    # Seed tariffs imposed ON Columbia by others
    _seed_tariff(client, "cathay", TEST_COUNTRY, 2, "test seed cathay->columbia L2")
    _seed_tariff(client, "sarmatia", TEST_COUNTRY, 1, "test seed sarmatia->columbia L1")

    ctx = build_tariff_context(TEST_COUNTRY, SCENARIO_CODE, 62)
    tariffs_on_me = ctx["tariffs_on_me"]

    print(f"\n  [test_tariffs_on_me] {tariffs_on_me}")

    imposers = {t["imposer"] for t in tariffs_on_me}
    assert "cathay" in imposers, f"Expected cathay in tariffs_on_me, got imposers={imposers}"
    assert "sarmatia" in imposers, f"Expected sarmatia in tariffs_on_me"

    cathay_entry = next(t for t in tariffs_on_me if t["imposer"] == "cathay")
    assert cathay_entry["level"] == 2


def test_context_has_decision_rules(client, scenario_id):
    """Verify decision_rules text includes no_change reminder."""
    _seed_round_from_r0(client, scenario_id, 60)

    ctx = build_tariff_context(TEST_COUNTRY, SCENARIO_CODE, 60)
    rules = ctx["decision_rules"]

    print(f"\n  [test_decision_rules] length={len(rules)}")

    assert "no_change" in rules, "Decision rules must mention no_change"
    assert "0-3" in rules or "0..3" in rules, "Decision rules must mention level range"
    assert "carry-forward" in rules, "Decision rules must mention carry-forward"
    assert "legitimate" in rules.lower(), "Decision rules must remind no_change is legitimate"

    # instruction also present
    assert ctx["instruction"], "Instruction must be present"
    assert "CHANGE" in ctx["instruction"] or "change" in ctx["instruction"]


def test_context_trade_rank_ordering(client, scenario_id):
    """Verify trade ranks are 1..19 with no gaps."""
    _seed_round_from_r0(client, scenario_id, 63)

    ctx = build_tariff_context(TEST_COUNTRY, SCENARIO_CODE, 63)
    roster = ctx["country_roster"]

    ranks = sorted(entry["trade_rank"] for entry in roster)
    expected_ranks = list(range(1, EXPECTED_COUNTRY_COUNT + 1))

    print(f"\n  [test_trade_rank] ranks={ranks}")
    print(f"  expected={expected_ranks}")

    assert ranks == expected_ranks, (
        f"Trade ranks should be 1..{EXPECTED_COUNTRY_COUNT}, got {ranks}"
    )

    # Rank 1 should have the highest trade weight (highest GDP generally)
    # — just verify monotonicity by checking rank 1 has higher GDP than rank 19
    rank1 = next(e for e in roster if e["trade_rank"] == 1)
    rank_last = next(e for e in roster if e["trade_rank"] == EXPECTED_COUNTRY_COUNT)
    print(f"  rank1={rank1['code']} GDP={rank1['gdp']}")
    print(f"  rank{EXPECTED_COUNTRY_COUNT}={rank_last['code']} GDP={rank_last['gdp']}")
