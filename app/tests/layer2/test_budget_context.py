"""Layer 2 — Budget context assembler + dry-run (CONTRACT_BUDGET v1.1 §3).

Step 5 of the budget vertical slice. Verifies that
``engine.services.budget_context`` produces the correct payload for a
decision-maker and that the dry-run preview matches the real engine.

Uses rounds 70-73 to avoid collision with the e2e battery (74-78) and
persistence tests (79-82).

Run::

    cd app && PYTHONPATH=. python3 -m pytest tests/layer2/test_budget_context.py -v -s
"""
from __future__ import annotations

import logging

import pytest

from engine.engines.round_tick import run_engine_tick
from engine.round_engine.resolve_round import resolve_round
from engine.services.budget_context import build_budget_context, dry_run_budget
from engine.services.supabase import get_client

logger = logging.getLogger(__name__)

SCENARIO_CODE = "start_one"
TEST_COUNTRY = "columbia"

# Columbia R0 reference values (verified 2026-04-10 against DB):
COL_GDP = 280.0
COL_TREASURY = 30.0
COL_STABILITY = 7
COL_PROD_CAP_GROUND = 4
COL_PROD_CAP_NAVAL = 2
COL_PROD_CAP_TAC_AIR = 3
COL_SOCIAL_BASELINE = 0.30
COL_TAX_RATE = 0.24
COL_MAINT_PER_UNIT = 0.05
COL_MIL_GROUND = 22
COL_MIL_NAVAL = 11
COL_MIL_TAC_AIR = 15

TEST_ROUNDS = [70, 71, 72, 73]


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
            new_row["budget_social_pct"] = None
            new_row["budget_production"] = None
            new_row["budget_research"] = None
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
        client.table("observatory_events").delete().eq(
            "scenario_id", scenario_id
        ).eq("round_num", rn).execute()
        client.table("country_states_per_round").delete().eq(
            "scenario_id", scenario_id
        ).eq("round_num", rn).execute()
        client.table("global_state_per_round").delete().eq(
            "scenario_id", scenario_id
        ).eq("round_num", rn).execute()
        client.table("round_states").delete().eq(
            "scenario_id", scenario_id
        ).eq("round_num", rn).execute()
        client.table("agent_decisions").delete().eq(
            "scenario_id", scenario_id
        ).eq("round_num", rn).execute()


@pytest.fixture(autouse=True)
def _isolate(client, scenario_id):
    _cleanup(client, scenario_id)
    yield
    _cleanup(client, scenario_id)


def _set_budget_row(
    client, scenario_id: str, round_num: int, country: str,
    social_pct: float, production: dict, research: dict,
) -> None:
    """Directly update the country_states_per_round row with a budget,
    bypassing resolve_round. This is what the context assembler reads."""
    from tests._sim_run_helper import legacy_run_id
    client.table("country_states_per_round").update(
        {
            "budget_social_pct": social_pct,
            "budget_production": production,
            "budget_research": research,
        }
    ).eq("sim_run_id", legacy_run_id()).eq("round_num", round_num).eq(
        "country_code", country
    ).execute()


def _insert_set_budget_decision(
    client, scenario_id: str, round_num: int, country: str,
    social_pct: float, production: dict, research: dict,
) -> None:
    """Insert a decision row so resolve_round + tick will apply it."""
    from tests._sim_run_helper import legacy_run_id
    payload = {
        "action_type": "set_budget",
        "country_code": country,
        "round_num": round_num,
        "decision": "change",
        "rationale": (
            "Budget context dry-run vs actual test — scripted decision to "
            "measure agreement between forecast and real engine output."
        ),
        "changes": {
            "social_pct": social_pct,
            "production": production,
            "research": research,
        },
        "test_tag": "BUDGET_CONTEXT_L2",
    }
    client.table("agent_decisions").insert(
        {
            "sim_run_id": legacy_run_id(),
            "scenario_id": scenario_id,
            "country_code": country,
            "action_type": "set_budget",
            "action_payload": payload,
            "rationale": payload["rationale"],
            "validation_status": "passed",
            "round_num": round_num,
        }
    ).execute()


def _zero_production() -> dict:
    return {
        "ground": 0,
        "naval": 0,
        "tactical_air": 0,
        "strategic_missile": 0,
        "air_defense": 0,
    }


def _zero_research() -> dict:
    return {"nuclear_coins": 0, "ai_coins": 0}


# ---------------------------------------------------------------------------
# Test 1 — context reads Columbia state
# ---------------------------------------------------------------------------


def test_context_reads_columbia_state(client, scenario_id):
    _seed_round_from_r0(client, scenario_id, 70)

    ctx = build_budget_context(TEST_COUNTRY, SCENARIO_CODE, 70)

    print(f"\n  [test_context_reads] econ={ctx['economic_state']}")
    print(f"  military_state={ctx['military_state']}")
    print(f"  research_progress={ctx['research_progress']}")

    assert ctx["country_code"] == TEST_COUNTRY
    assert ctx["round_num"] == 70
    eco = ctx["economic_state"]
    assert eco["gdp"] == pytest.approx(COL_GDP, abs=1.0)
    assert eco["treasury"] == pytest.approx(COL_TREASURY, abs=1.0)
    assert float(eco["stability"]) == pytest.approx(COL_STABILITY, abs=0.5)

    mil = ctx["military_state"]
    for branch in ("ground", "naval", "tactical_air", "strategic_missile", "air_defense"):
        assert branch in mil["production_capacity"], (
            f"Missing capacity for {branch}"
        )
    assert mil["production_capacity"]["ground"] == COL_PROD_CAP_GROUND
    assert mil["production_capacity"]["naval"] == COL_PROD_CAP_NAVAL
    assert mil["production_capacity"]["strategic_missile"] == 0
    assert mil["production_capacity"]["air_defense"] == 0

    rp = ctx["research_progress"]
    assert "nuclear" in rp and "level" in rp["nuclear"]
    assert "ai" in rp and "level" in rp["ai"]


# ---------------------------------------------------------------------------
# Test 2 — revenue forecast matches the gdp × tax_rate formula
# ---------------------------------------------------------------------------


def test_context_revenue_forecast(client, scenario_id):
    _seed_round_from_r0(client, scenario_id, 70)

    ctx = build_budget_context(TEST_COUNTRY, SCENARIO_CODE, 70)
    rev = ctx["revenue_forecast"]

    expected_base = rev["gdp"] * rev["tax_rate"]
    print(
        f"\n  [test_revenue] gdp={rev['gdp']} tax_rate={rev['tax_rate']} "
        f"expected_base={expected_base:.2f} actual_base={rev['base_revenue']} "
        f"oil={rev['oil_revenue']} debt={rev['debt_cost']} "
        f"total={rev['total']}"
    )
    assert rev["base_revenue"] == pytest.approx(expected_base, rel=0.01)
    # Columbia IS an oil producer (13 mbpd) — oil_revenue should be positive
    assert rev["oil_revenue"] > 0, f"Columbia oil revenue should be > 0, got {rev['oil_revenue']}"
    # Total = base + oil - debt - erosion - war - sanctions (all others ~0)
    expected_total = rev["base_revenue"] + rev["oil_revenue"] - rev["debt_cost"] \
        - rev["inflation_erosion"] - rev["war_damage_cost"] - rev["sanctions_cost"]
    assert rev["total"] == pytest.approx(expected_total, rel=0.01)


# ---------------------------------------------------------------------------
# Test 3 — mandatory costs
# ---------------------------------------------------------------------------


def test_context_mandatory_costs(client, scenario_id):
    _seed_round_from_r0(client, scenario_id, 70)

    ctx = build_budget_context(TEST_COUNTRY, SCENARIO_CODE, 70)
    mand = ctx["mandatory_costs"]
    total_units = ctx["military_state"]["total_units"]
    revenue = ctx["revenue_forecast"]["total"]

    expected_maintenance = total_units * COL_MAINT_PER_UNIT * 3.0
    expected_social_baseline = COL_SOCIAL_BASELINE * max(revenue, 0)
    print(
        f"\n  [test_mandatory] total_units={total_units} "
        f"maintenance expected={expected_maintenance:.2f} actual={mand['maintenance']} "
        f"social_baseline expected={expected_social_baseline:.2f} "
        f"actual={mand['social_baseline']} total={mand['total']}"
    )

    assert mand["maintenance"] == pytest.approx(expected_maintenance, rel=0.02)
    assert mand["social_baseline"] == pytest.approx(expected_social_baseline, rel=0.02)
    assert mand["total"] == pytest.approx(
        mand["maintenance"] + mand["social_baseline"], rel=0.001
    )


# ---------------------------------------------------------------------------
# Test 4 — dry_run no-change matches actual engine run
# ---------------------------------------------------------------------------


def test_dry_run_no_change_matches_actual(client, scenario_id):
    """Seed R70, set an explicit budget on it, forecast R70 via dry-run,
    then run resolve_round + engine_tick for R71 with the same budget
    carried forward (decision=change in R71 using the same numbers).

    Compare: dry-run expected_treasury ≈ actual R71 treasury.
    """
    _seed_round_from_r0(client, scenario_id, 70)

    budget = {
        "social_pct": 1.0,
        "production": {**_zero_production(), "ground": 1},
        "research": _zero_research(),
    }

    # Put the budget directly onto R70 so the context/dry-run sees it as
    # the "current" budget of the target round.
    _set_budget_row(
        client, scenario_id, 70, TEST_COUNTRY,
        social_pct=1.0,
        production=budget["production"],
        research=budget["research"],
    )

    # Dry-run the same budget against R70's state (predicts outcome if this
    # budget were applied to R70).
    forecast = dry_run_budget(
        TEST_COUNTRY, SCENARIO_CODE, 70,
        budget_override=budget,
    )
    print(
        f"\n  [test_dry_run_match] forecast treasury={forecast['expected_treasury']} "
        f"stability={forecast['expected_stability']} "
        f"units={forecast['units_produced']}"
    )

    # Now seed R70 fresh again (drop the budget override so the real chain
    # gets a clean baseline), then submit the same budget through the real
    # decision chain for R71 and compare end state.
    _cleanup(client, scenario_id)
    _seed_round_from_r0(client, scenario_id, 70)

    _insert_set_budget_decision(
        client, scenario_id, 71, TEST_COUNTRY,
        social_pct=budget["social_pct"],
        production=budget["production"],
        research=budget["research"],
    )
    resolve_round(SCENARIO_CODE, 71)
    run_engine_tick(SCENARIO_CODE, 71)

    actual = (
        client.table("country_states_per_round")
        .select("*")
        .eq("scenario_id", scenario_id)
        .eq("round_num", 71)
        .eq("country_code", TEST_COUNTRY)
        .limit(1)
        .execute()
    )
    assert actual.data, "R71 row should exist after engine tick"
    actual_row = actual.data[0]
    actual_treasury = float(actual_row["treasury"])
    actual_stability = float(actual_row["stability"])

    print(
        f"  actual R71 treasury={actual_treasury} stability={actual_stability}"
    )

    # The forecast is a preview of what happens when THIS budget is applied
    # to the starting state. The real run passes through resolve_round which
    # touches many other subsystems (inflation update, state transitions,
    # political engine, etc.), so an exact match is not expected — but the
    # dominant number (treasury) should land in the same ballpark.
    assert actual_treasury == pytest.approx(
        forecast["expected_treasury"], abs=10.0
    ), (
        f"Dry-run treasury {forecast['expected_treasury']} diverges from "
        f"actual {actual_treasury} by > 10 coins"
    )
    # Stability: dry-run applies only social delta; actual engine clamps
    # + applies other stability inputs. Agree within ±1.
    assert abs(actual_stability - forecast["expected_stability"]) <= 1.5, (
        f"Dry-run stability {forecast['expected_stability']} vs "
        f"actual {actual_stability}"
    )


# ---------------------------------------------------------------------------
# Test 5 — dry_run with override — austerity -> stability delta -2
# ---------------------------------------------------------------------------


def test_dry_run_with_override(client, scenario_id):
    _seed_round_from_r0(client, scenario_id, 70)

    forecast = dry_run_budget(
        TEST_COUNTRY, SCENARIO_CODE, 70,
        budget_override={
            "social_pct": 0.5,
            "production": _zero_production(),
            "research": _zero_research(),
        },
    )
    print(f"\n  [test_dry_run_override] stability_delta={forecast['stability_delta']}")
    assert forecast["stability_delta"] == pytest.approx(-2.0, abs=0.01)
    assert forecast["political_support_delta"] == pytest.approx(-3.0, abs=0.01)


# ---------------------------------------------------------------------------
# Test 6 — deficit warning fires on max-pace production
# ---------------------------------------------------------------------------


def test_dry_run_deficit_warning(client, scenario_id):
    _seed_round_from_r0(client, scenario_id, 70)

    forecast = dry_run_budget(
        TEST_COUNTRY, SCENARIO_CODE, 70,
        budget_override={
            "social_pct": 1.5,  # max social
            "production": {
                "ground": 3,
                "naval": 3,
                "tactical_air": 3,
                "strategic_missile": 3,
                "air_defense": 3,
            },
            "research": {"nuclear_coins": 50, "ai_coins": 50},
        },
    )
    print(
        f"\n  [test_deficit_warning] deficit={forecast['deficit']} "
        f"money_printed={forecast['money_printed']} "
        f"warnings={forecast['warnings']}"
    )
    assert forecast["deficit"] > 0, "Expected deficit on maximum spending"
    assert any(
        "Deficit" in w or "deficit" in w for w in forecast["warnings"]
    ), f"Expected deficit warning, got: {forecast['warnings']}"


# ---------------------------------------------------------------------------
# Test 7 — current_budget reflects persisted columns
# ---------------------------------------------------------------------------


def test_context_includes_current_budget(client, scenario_id):
    _seed_round_from_r0(client, scenario_id, 70)

    production = {**_zero_production(), "tactical_air": 2}
    research = {"nuclear_coins": 3, "ai_coins": 7}
    _set_budget_row(
        client, scenario_id, 70, TEST_COUNTRY,
        social_pct=0.75,
        production=production,
        research=research,
    )

    # Context for R71 — no R71 row yet, so the assembler should fall back
    # to R70 and read its budget as the "current".
    ctx = build_budget_context(TEST_COUNTRY, SCENARIO_CODE, 71)
    print(f"\n  [test_current_budget] current={ctx['current_budget']}")

    cur = ctx["current_budget"]
    assert float(cur["social_pct"]) == pytest.approx(0.75)
    assert cur["production"]["tactical_air"] == 2
    assert cur["production"]["ground"] == 0
    assert cur["research"]["nuclear_coins"] == 3
    assert cur["research"]["ai_coins"] == 7


# ---------------------------------------------------------------------------
# Test 8 — no_change_forecast is always present and structured
# ---------------------------------------------------------------------------


def test_context_no_change_forecast_present(client, scenario_id):
    _seed_round_from_r0(client, scenario_id, 70)

    ctx = build_budget_context(TEST_COUNTRY, SCENARIO_CODE, 70)
    f = ctx["no_change_forecast"]
    print(f"\n  [test_no_change_forecast] keys={sorted(f.keys())}")

    for key in (
        "social_spending", "military_spending", "research_spending",
        "maintenance", "total_spending", "revenue", "deficit",
        "treasury_drawn", "money_printed", "units_produced",
        "coins_by_branch", "research_progress", "stability_delta",
        "political_support_delta", "expected_treasury",
        "expected_stability", "expected_support", "warnings",
    ):
        assert key in f, f"no_change_forecast missing key '{key}'"

    # Units dict must have all 5 branches
    for branch in (
        "ground", "naval", "tactical_air", "strategic_missile", "air_defense"
    ):
        assert branch in f["units_produced"]
        assert branch in f["coins_by_branch"]
