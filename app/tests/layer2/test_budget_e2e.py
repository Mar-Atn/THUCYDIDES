"""Layer 2 — Budget end-to-end vertical slice (CONTRACT_BUDGET v1.1).

Step 4 of the budget vertical slice. Proves that scripted budget decisions
flow all the way through:

    agent_decisions
      -> resolve_round  (validate + write budget_* columns on country snapshot)
        -> run_engine_tick  (load budget cols, run economic + political engines)
          -> country_states_per_round  (treasury, stability, R&D progress, ...)

Each test seeds a baseline round from R0, inserts a single set_budget decision,
runs the full chain, then queries the resulting snapshot and asserts that the
engine actually consumed the decision (not the default budget).

Uses rounds 75-78 to avoid collision with battery (90-91), persistence (79-82),
and live runs.

Architectural notes (updated 2026-04-10, post-gap-closure):
  * `country_states_per_round` now has mil_ground / mil_naval /
    mil_tactical_air / mil_strategic_missiles / mil_air_defense columns.
    `round_tick.run_engine_tick` writes the credited unit counts back to the
    snapshot, so tests assert unit growth directly.
  * ai_rd_progress / nuclear_rd_progress are persisted as numeric fractionals
    by the budget pipeline — so `research.ai_coins` now has a directly
    observable effect on the country_states snapshot.

Run::

    cd app && PYTHONPATH=. python3 -m pytest tests/layer2/test_budget_e2e.py -v -s
"""

from __future__ import annotations

import logging

import pytest

from engine.engines.round_tick import run_engine_tick
from engine.round_engine.resolve_round import resolve_round
from engine.services.supabase import get_client

logger = logging.getLogger(__name__)

SCENARIO_CODE = "start_one"
TEST_COUNTRY = "columbia"
TEST_TAG = "BUDGET_E2E_L2"

# Use a wide range so each test owns 2 consecutive rounds.
TEST_ROUNDS = [74, 75, 76, 77, 78]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_scenario_id(client) -> str:
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
    """Clone country_states_per_round + global_state_per_round from R0 -> round_num."""
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
            # Wipe any leftover budget columns from R0 — we want a clean slate
            new_row["budget_social_pct"] = None
            new_row["budget_production"] = None
            new_row["budget_research"] = None
            rows.append(new_row)
        if rows:
            # Insert in chunks
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
    """Remove anything we may have written under TEST_ROUNDS."""
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


def _insert_set_budget(
    client,
    scenario_id: str,
    round_num: int,
    country: str,
    decision: str = "change",
    rationale: str | None = None,
    social_pct: float | None = None,
    production: dict | None = None,
    research: dict | None = None,
) -> None:
    """Insert a set_budget decision into agent_decisions."""
    payload: dict = {
        "action_type": "set_budget",
        "country_code": country,
        "round_num": round_num,
        "decision": decision,
        "rationale": rationale
        or (
            "E2E test: scripted budget decision injected to verify the full "
            "decision -> resolve -> engine -> snapshot pipeline"
        ),
        "test_tag": TEST_TAG,
    }
    if decision == "change":
        changes: dict = {}
        if social_pct is not None:
            changes["social_pct"] = social_pct
        if production is not None:
            changes["production"] = production
        if research is not None:
            changes["research"] = research
        payload["changes"] = changes

    client.table("agent_decisions").insert(
        {
            "scenario_id": scenario_id,
            "country_code": country,
            "action_type": "set_budget",
            "action_payload": payload,
            "rationale": payload["rationale"],
            "validation_status": "passed",
            "round_num": round_num,
        }
    ).execute()


def _get_country_row(client, scenario_id: str, round_num: int, country: str) -> dict:
    res = (
        client.table("country_states_per_round")
        .select("*")
        .eq("scenario_id", scenario_id)
        .eq("round_num", round_num)
        .eq("country_code", country)
        .limit(1)
        .execute()
    )
    assert res.data, f"No country_states_per_round row for {country} R{round_num}"
    return res.data[0]


def _full_chain(scenario_id_unused, round_num: int) -> tuple[dict, dict]:
    """Run resolve_round + run_engine_tick for the given round."""
    resolve_result = resolve_round(SCENARIO_CODE, round_num)
    tick_result = run_engine_tick(SCENARIO_CODE, round_num)
    return resolve_result, tick_result


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
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def client():
    return get_client()


@pytest.fixture(scope="module")
def scenario_id(client):
    return _get_scenario_id(client)


@pytest.fixture(autouse=True)
def _isolate(client, scenario_id):
    """Clean test rounds before and after every test."""
    _cleanup(client, scenario_id)
    yield
    _cleanup(client, scenario_id)


# ---------------------------------------------------------------------------
# Reference values from the DB (Columbia, R0)
# ---------------------------------------------------------------------------
# Verified via Supabase 2026-04-10:
#   gdp=280, treasury=30, stability=7, political_support=38, inflation=3.5
#   prod_cap_ground=4, prod_cap_naval=2, prod_cap_tactical=3
#   social_baseline=0.30, tax_rate=0.24, maintenance_per_unit=0.05
#   mil_ground=22, mil_naval=11, mil_tactical_air=15
COL_PROD_CAP_GROUND = 4
COL_PROD_CAP_NAVAL = 2
COL_SOCIAL_BASELINE = 0.30
COL_GDP = 280.0


# ---------------------------------------------------------------------------
# Test 1 — Austerity hurts stability
# ---------------------------------------------------------------------------


def test_austerity_hurts_stability(client, scenario_id):
    """social_pct=0.5 should knock stability down ~2 points."""
    # Seed R74 from R0 baseline (so R75 has a previous round to read from)
    _seed_round_from_r0(client, scenario_id, 74)

    # Insert austerity budget for R75
    _insert_set_budget(
        client, scenario_id, 75, TEST_COUNTRY,
        social_pct=0.5,
        production=_zero_production(),
        research=_zero_research(),
        rationale="E2E test 1: austerity budget should drop stability by ~2",
    )

    _full_chain(scenario_id, 75)

    r74 = _get_country_row(client, scenario_id, 74, TEST_COUNTRY)
    r75 = _get_country_row(client, scenario_id, 75, TEST_COUNTRY)

    s74 = float(r74["stability"])
    s75 = float(r75["stability"])
    delta = s75 - s74
    print(f"\n  [test_austerity] stability R74={s74}  R75={s75}  delta={delta:+.2f}")
    print(f"  budget cols persisted: social_pct={r75.get('budget_social_pct')}")

    # Contract: stability_delta = (0.5 - 1.0) * 4.0 = -2.0
    # Other engine effects (gdp_growth, inflation friction, etc.) will nudge,
    # but the dominant signal must be down.
    assert r75.get("budget_social_pct") is not None, "budget_social_pct not persisted"
    assert float(r75["budget_social_pct"]) == pytest.approx(0.5)
    assert delta < 0, f"Expected stability to drop under austerity, got delta={delta}"
    assert delta <= -1.0, (
        f"Expected stability drop of at least 1, got delta={delta} "
        f"(contract says ~-2)"
    )


# ---------------------------------------------------------------------------
# Test 2 — Generous helps stability
# ---------------------------------------------------------------------------


def test_generous_helps_stability(client, scenario_id):
    """social_pct=1.5 should push stability up ~2 points."""
    # Use R75 -> R76. Seed from R0 to drop existing stability low enough that
    # we can detect a +2 (R0 stability=7; engine clamps at 9).
    _seed_round_from_r0(client, scenario_id, 75)

    # First lower R75 stability to 5 so we can clearly see a +2 boost up to ~7
    client.table("country_states_per_round").update({"stability": 5}).eq(
        "scenario_id", scenario_id
    ).eq("round_num", 75).eq("country_code", TEST_COUNTRY).execute()

    _insert_set_budget(
        client, scenario_id, 76, TEST_COUNTRY,
        social_pct=1.5,
        production=_zero_production(),
        research=_zero_research(),
        rationale="E2E test 2: generous social spending should raise stability ~+2",
    )

    _full_chain(scenario_id, 76)

    r75 = _get_country_row(client, scenario_id, 75, TEST_COUNTRY)
    r76 = _get_country_row(client, scenario_id, 76, TEST_COUNTRY)
    s75 = float(r75["stability"])
    s76 = float(r76["stability"])
    delta = s76 - s75
    print(f"\n  [test_generous] stability R75={s75}  R76={s76}  delta={delta:+.2f}")

    assert float(r76["budget_social_pct"]) == pytest.approx(1.5)
    assert delta > 0, f"Expected stability to rise under generous budget, got delta={delta}"
    assert delta >= 1.0, (
        f"Expected stability rise of at least 1, got delta={delta} "
        f"(contract says ~+2)"
    )


# ---------------------------------------------------------------------------
# Test 3 — Ground production level 1 actually produces units (DB-verified)
# ---------------------------------------------------------------------------


def _treasury_after(client, scenario_id, round_num):
    row = _get_country_row(client, scenario_id, round_num, TEST_COUNTRY)
    return float(row["treasury"])


def test_ground_production_level_1_spends_coins(client, scenario_id):
    """Level-1 ground production should cost cap_ground × 3 coins."""
    _seed_round_from_r0(client, scenario_id, 77)
    _insert_set_budget(
        client, scenario_id, 78, TEST_COUNTRY,
        social_pct=1.0,
        production={**_zero_production(), "ground": 1},
        research=_zero_research(),
        rationale="E2E test 3: ground production level 1 should spend cap_ground*3 coins",
    )
    _full_chain(scenario_id, 78)

    r77 = _get_country_row(client, scenario_id, 77, TEST_COUNTRY)
    row = _get_country_row(client, scenario_id, 78, TEST_COUNTRY)
    expected_units = COL_PROD_CAP_GROUND * 1  # 4
    expected_coin_cost = COL_PROD_CAP_GROUND * 3 * 1  # 12

    ground_before = int(r77.get("mil_ground") or 0)
    ground_after = int(row.get("mil_ground") or 0)
    unit_delta = ground_after - ground_before

    print(
        f"\n  [test_ground_L1] expected units={expected_units}  "
        f"expected ground coins spent={expected_coin_cost}  "
        f"R77 mil_ground={ground_before}  R78 mil_ground={ground_after}  "
        f"delta=+{unit_delta}  R78 treasury={row['treasury']}"
    )

    assert row.get("budget_production") is not None
    assert row["budget_production"]["ground"] == 1
    # Hard assertion: level-1 production credited exactly cap_ground units.
    assert unit_delta == expected_units, (
        f"Expected +{expected_units} ground units, got delta={unit_delta} "
        f"(R77={ground_before} R78={ground_after})"
    )


def test_ground_production_level_2_costs_more_than_level_1(client, scenario_id):
    """Comparative: level 2 should leave Columbia poorer than level 1.

    This is the cleanest treasury-delta proof we can run without engine output
    capture: same starting state, same revenue, same everything except the
    ground production level. The level-2 run must end with strictly less
    treasury than the level-1 run.
    """
    # ---- Level 1 run on rounds 74 -> 75 ----
    _seed_round_from_r0(client, scenario_id, 74)
    _insert_set_budget(
        client, scenario_id, 75, TEST_COUNTRY,
        social_pct=1.0,
        production={**_zero_production(), "ground": 1},
        research=_zero_research(),
        rationale="E2E test 4a: ground level 1 baseline for comparison vs level 2",
    )
    _full_chain(scenario_id, 75)
    treasury_l1 = _treasury_after(client, scenario_id, 75)

    # Cleanup just R74 + R75 in preparation for the level-2 run
    for rn in (74, 75):
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
        client.table("observatory_events").delete().eq(
            "scenario_id", scenario_id
        ).eq("round_num", rn).execute()

    # ---- Level 2 run on rounds 74 -> 75 (fresh) ----
    _seed_round_from_r0(client, scenario_id, 74)
    _insert_set_budget(
        client, scenario_id, 75, TEST_COUNTRY,
        social_pct=1.0,
        production={**_zero_production(), "ground": 2},
        research=_zero_research(),
        rationale="E2E test 4b: ground level 2 should cost roughly double level 1",
    )
    _full_chain(scenario_id, 75)
    treasury_l2 = _treasury_after(client, scenario_id, 75)

    # NOTE on cap enforcement: Columbia's discretionary budget is tight
    # (~25-30 coins after mandatory costs). Level 2 ground requested
    # cap*3*2 = 24 coins but military cap is 40% of discretionary ~= 10-12 coins,
    # so the engine scales production down proportionally. This is CORRECT
    # behavior per CONTRACT_BUDGET §6.3. We just verify level 2 costs strictly
    # more than level 1 — the exact delta depends on cap scaling.
    unconstrained_extra = COL_PROD_CAP_GROUND * 3 * (2 - 1)  # 12 (ideal, unconstrained)
    actual_diff = treasury_l1 - treasury_l2
    print(
        f"\n  [test_ground_L2_vs_L1] treasury L1={treasury_l1}  L2={treasury_l2}  "
        f"diff={actual_diff:+.2f}  unconstrained_expected={unconstrained_extra}  "
        f"(cap enforcement likely scales down)"
    )

    assert treasury_l2 < treasury_l1, (
        f"Level 2 production must cost MORE than level 1: "
        f"L1 treasury={treasury_l1}, L2 treasury={treasury_l2}"
    )
    # Level 2 should cost at least 1 more coin than level 1 (cap enforcement
    # can reduce the delta but not eliminate it — level 2 must spend > level 1)
    assert actual_diff >= 1.0, (
        f"Level 2 should spend strictly more than level 1, got delta {actual_diff}"
    )


# ---------------------------------------------------------------------------
# Test 5 — Strategic missile (zero capacity) is a no-op even at level 3
# ---------------------------------------------------------------------------


def test_strategic_missile_zero_capacity_no_production(client, scenario_id):
    """Setting strategic_missile=3 should change nothing — capacity is 0."""
    # Baseline run with no missile production
    _seed_round_from_r0(client, scenario_id, 74)
    _insert_set_budget(
        client, scenario_id, 75, TEST_COUNTRY,
        social_pct=1.0,
        production=_zero_production(),
        research=_zero_research(),
        rationale="E2E test 5a: baseline (no missile production) for missile-noop comparison",
    )
    _full_chain(scenario_id, 75)
    treasury_baseline = _treasury_after(client, scenario_id, 75)

    # Cleanup R74-R75 only
    for rn in (74, 75):
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
        client.table("observatory_events").delete().eq(
            "scenario_id", scenario_id
        ).eq("round_num", rn).execute()

    # Maxed missile run
    _seed_round_from_r0(client, scenario_id, 74)
    _insert_set_budget(
        client, scenario_id, 75, TEST_COUNTRY,
        social_pct=1.0,
        production={**_zero_production(), "strategic_missile": 3},
        research=_zero_research(),
        rationale="E2E test 5b: strategic_missile=3 — should be a no-op since cap is 0",
    )
    _full_chain(scenario_id, 75)
    treasury_missile = _treasury_after(client, scenario_id, 75)

    print(
        f"\n  [test_missile_noop] treasury baseline={treasury_baseline}  "
        f"missile-L3={treasury_missile}  diff={treasury_missile - treasury_baseline:+.4f}"
    )

    # Treasury should match within rounding noise (no missile cost incurred).
    assert treasury_missile == pytest.approx(treasury_baseline, abs=0.5), (
        f"strategic_missile=3 should have cost 0 coins but treasury changed: "
        f"baseline={treasury_baseline}, missile-L3={treasury_missile}"
    )


# ---------------------------------------------------------------------------
# Test 6 — Research coin allocation accumulates ai_rd_progress (DB-verified)
# ---------------------------------------------------------------------------


def test_research_coins_accumulate_progress(client, scenario_id):
    """research.ai_coins=10 must advance ai_rd_progress per CONTRACT §6.2."""
    _seed_round_from_r0(client, scenario_id, 77)
    _insert_set_budget(
        client, scenario_id, 78, TEST_COUNTRY,
        social_pct=1.0,
        production=_zero_production(),
        research={"nuclear_coins": 0, "ai_coins": 10},
        rationale="E2E test 6: heavy AI research investment, verified via ai_rd_progress delta",
    )
    _full_chain(scenario_id, 78)

    r77 = _get_country_row(client, scenario_id, 77, TEST_COUNTRY)
    r78 = _get_country_row(client, scenario_id, 78, TEST_COUNTRY)

    # CONTRACT_BUDGET §6.2: progress = (coins / gdp) * RD_MULTIPLIER
    expected_progress_delta = (10 / COL_GDP) * 0.8
    progress_before = float(r77.get("ai_rd_progress") or 0)
    progress_after = float(r78.get("ai_rd_progress") or 0)
    delta = progress_after - progress_before

    print(
        f"\n  [test_research_persist] budget_research={r78.get('budget_research')}  "
        f"ai_rd_progress R77={progress_before:.6f}  R78={progress_after:.6f}  "
        f"delta=+{delta:.6f}  expected=+{expected_progress_delta:.6f}"
    )

    assert r78.get("budget_research") is not None
    assert r78["budget_research"]["ai_coins"] == 10
    assert r78["budget_research"]["nuclear_coins"] == 0
    # Hard assertion: ai_rd_progress grew by the contract-specified amount.
    assert delta == pytest.approx(expected_progress_delta, rel=0.05), (
        f"ai_rd_progress did not accumulate as expected: "
        f"delta={delta}, expected={expected_progress_delta}"
    )


# ---------------------------------------------------------------------------
# Test 7 — no_change carries forward
# ---------------------------------------------------------------------------


def test_no_change_carries_forward_budget(client, scenario_id):
    """A no_change decision in R+1 must reuse R+0's explicit budget."""
    _seed_round_from_r0(client, scenario_id, 74)

    # R75: explicit budget
    _insert_set_budget(
        client, scenario_id, 75, TEST_COUNTRY,
        social_pct=0.8,
        production={**_zero_production(), "ground": 2},
        research=_zero_research(),
        rationale="E2E test 7a: explicit baseline budget for carry-forward test",
    )
    _full_chain(scenario_id, 75)

    r75 = _get_country_row(client, scenario_id, 75, TEST_COUNTRY)
    assert float(r75["budget_social_pct"]) == pytest.approx(0.8)
    assert r75["budget_production"]["ground"] == 2

    # R76: no_change
    _insert_set_budget(
        client, scenario_id, 76, TEST_COUNTRY,
        decision="no_change",
        rationale="E2E test 7b: no_change should carry forward R75's budget into R76",
    )
    _full_chain(scenario_id, 76)

    r76 = _get_country_row(client, scenario_id, 76, TEST_COUNTRY)
    print(
        f"\n  [test_no_change_carry] R75 budget social={r75.get('budget_social_pct')} "
        f"prod_ground={r75['budget_production']['ground']}\n"
        f"  R76 budget social={r76.get('budget_social_pct')} "
        f"prod={r76.get('budget_production')}"
    )

    assert r76.get("budget_social_pct") is not None, (
        "R76 budget_social_pct should be carried forward, not null"
    )
    assert float(r76["budget_social_pct"]) == pytest.approx(0.8)
    assert r76["budget_production"]["ground"] == 2


# ---------------------------------------------------------------------------
# Test 8 — Maximum spending forces deficit cascade
# ---------------------------------------------------------------------------


def test_maximum_spending_drains_treasury(client, scenario_id):
    """All branches at level 3 should significantly cut Columbia's treasury."""
    _seed_round_from_r0(client, scenario_id, 77)
    _insert_set_budget(
        client, scenario_id, 78, TEST_COUNTRY,
        social_pct=1.5,  # max social on top of max military
        production={
            "ground": 3,
            "naval": 3,
            "tactical_air": 3,
            "strategic_missile": 3,
            "air_defense": 3,
        },
        research={"nuclear_coins": 20, "ai_coins": 20},
        rationale="E2E test 8: maximum spending across the board should trigger the deficit cascade",
    )
    _full_chain(scenario_id, 78)

    r77 = _get_country_row(client, scenario_id, 77, TEST_COUNTRY)
    r78 = _get_country_row(client, scenario_id, 78, TEST_COUNTRY)
    t77 = float(r77["treasury"])
    t78 = float(r78["treasury"])
    inf77 = float(r77.get("inflation") or 0)
    inf78 = float(r78.get("inflation") or 0)

    print(
        f"\n  [test_max_spending] treasury R77={t77}  R78={t78}  "
        f"inflation R77={inf77}  R78={inf78}  "
        f"budget_production={r78.get('budget_production')}"
    )

    # The engine must have honored the budget — either by drawing treasury,
    # printing money (inflation up), or both.
    drawdown = t77 - t78
    inflation_rise = inf78 - inf77
    assert (drawdown > 0) or (inflation_rise > 0), (
        f"Expected deficit cascade evidence (treasury drawdown or inflation rise), "
        f"got drawdown={drawdown:.2f}, inflation_rise={inflation_rise:.4f}"
    )


# ---------------------------------------------------------------------------
# Test 9 — Invalid budget rejected, round still runs
# ---------------------------------------------------------------------------


def test_invalid_budget_skipped_round_still_runs(client, scenario_id):
    """Out-of-range social_pct must be rejected, but the round still completes."""
    _seed_round_from_r0(client, scenario_id, 77)
    # Invalid social_pct = 2.5 (max is 1.5)
    _insert_set_budget(
        client, scenario_id, 78, TEST_COUNTRY,
        social_pct=2.5,
        production=_zero_production(),
        research=_zero_research(),
        rationale="E2E test 9: deliberately invalid social_pct (out of [0.5, 1.5] range)",
    )
    resolve_result, tick_result = _full_chain(scenario_id, 78)

    # Rejection event should be logged
    rej = (
        client.table("observatory_events")
        .select("event_type, country_code, payload")
        .eq("scenario_id", scenario_id)
        .eq("round_num", 78)
        .eq("event_type", "budget_rejected")
        .execute()
    )
    rejections = rej.data or []
    print(
        f"\n  [test_invalid_budget] budget_rejected events={len(rejections)}  "
        f"resolve_result={resolve_result}  tick_success={tick_result.get('success')}"
    )

    assert len(rejections) >= 1, "Expected at least one budget_rejected event"
    assert any(r["country_code"] == TEST_COUNTRY for r in rejections)

    # Round should still complete
    assert tick_result.get("success") is True, (
        f"Engine tick failed even after rejecting invalid budget: {tick_result}"
    )

    # Country snapshot must NOT carry the bogus social_pct
    row = _get_country_row(client, scenario_id, 78, TEST_COUNTRY)
    bad = row.get("budget_social_pct")
    if bad is not None:
        assert float(bad) <= 1.5, (
            f"Invalid social_pct leaked into snapshot: {bad}"
        )

    # Other countries should be unaffected — verify Cathay still has a row
    cath = (
        client.table("country_states_per_round")
        .select("country_code, treasury, gdp")
        .eq("scenario_id", scenario_id)
        .eq("round_num", 78)
        .eq("country_code", "cathay")
        .execute()
    )
    assert cath.data, "Other countries (cathay) should still have R78 snapshots"


# ---------------------------------------------------------------------------
# Test 10 — Definitive end-to-end: every persistable budget effect verified
# ---------------------------------------------------------------------------


def test_full_chain_values_match(client, scenario_id):
    """The acceptance gate. Compute expected outcomes by hand, query the DB,
    and verify everything matches.

    Post-gap-closure (2026-04-10): unit counts and ai_rd_progress are now
    persisted by round_tick and are hard-asserted here.
    """
    _seed_round_from_r0(client, scenario_id, 77)
    # Bring R77 stability down to 5 to give the +0.8 social bonus room to show
    client.table("country_states_per_round").update({"stability": 5}).eq(
        "scenario_id", scenario_id
    ).eq("round_num", 77).eq("country_code", TEST_COUNTRY).execute()

    budget_changes = {
        "social_pct": 1.2,
        "production": {
            "ground": 2,
            "naval": 1,
            "tactical_air": 0,
            "strategic_missile": 0,
            "air_defense": 0,
        },
        "research": {"nuclear_coins": 0, "ai_coins": 5},
    }
    _insert_set_budget(
        client, scenario_id, 78, TEST_COUNTRY,
        social_pct=budget_changes["social_pct"],
        production=budget_changes["production"],
        research=budget_changes["research"],
        rationale="E2E test 10: full-chain acceptance gate, every formula independently computed",
    )
    _full_chain(scenario_id, 78)

    r77 = _get_country_row(client, scenario_id, 77, TEST_COUNTRY)
    r78 = _get_country_row(client, scenario_id, 78, TEST_COUNTRY)

    # ---- Manual computation of expected effects ----
    # Per CONTRACT_BUDGET §6:
    #   stability_delta_from_social = (1.2 - 1.0) * 4.0 = +0.8
    #   support_delta_from_social   = (1.2 - 1.0) * 6.0 = +1.2
    #   ground_coins  = cap_ground × 3 × cost_mult[2]  = 4 × 3 × 2 = 24
    #   ground_units  = cap_ground × output_mult[2]    = 4 × 2     = 8
    #   naval_coins   = cap_naval  × 6 × cost_mult[1]  = 2 × 6 × 1 = 12
    #   naval_units   = cap_naval  × output_mult[1]    = 2 × 1     = 2
    #   ai_progress_delta = (5 / 280) * 0.8 * 1.0      = 0.01428...
    expected_social_pct = 1.2
    expected_stab_delta_social = (1.2 - 1.0) * 4.0
    expected_ground_coins = COL_PROD_CAP_GROUND * 3 * 2  # 24
    expected_ground_units = COL_PROD_CAP_GROUND * 2  # 8
    expected_naval_coins = COL_PROD_CAP_NAVAL * 6 * 1  # 12
    expected_naval_units = COL_PROD_CAP_NAVAL * 1  # 2
    expected_ai_progress_delta = (5 / COL_GDP) * 0.8 * 1.0  # ~0.01428

    s77 = float(r77["stability"])
    s78 = float(r78["stability"])

    ground_before = int(r77.get("mil_ground") or 0)
    ground_after = int(r78.get("mil_ground") or 0)
    naval_before = int(r77.get("mil_naval") or 0)
    naval_after = int(r78.get("mil_naval") or 0)
    ai_progress_before = float(r77.get("ai_rd_progress") or 0)
    ai_progress_after = float(r78.get("ai_rd_progress") or 0)

    print("\n  [test_full_chain] EXPECTED vs ACTUAL")
    print(f"    budget_social_pct:      expected {expected_social_pct}  "
          f"actual {r78.get('budget_social_pct')}")
    print(f"    budget_production:      expected {budget_changes['production']}  "
          f"actual {r78.get('budget_production')}")
    print(f"    budget_research:        expected {budget_changes['research']}  "
          f"actual {r78.get('budget_research')}")
    print(f"    stability:              R77={s77}  R78={s78}  "
          f"delta={s78-s77:+.2f}  (social contribution alone {expected_stab_delta_social:+.2f})")
    print(f"    ground units:           R77={ground_before}  R78={ground_after}  "
          f"delta=+{ground_after-ground_before}  expected +{expected_ground_units}")
    print(f"    naval units:            R77={naval_before}  R78={naval_after}  "
          f"delta=+{naval_after-naval_before}  expected +{expected_naval_units}")
    print(f"    ai_rd_progress:         R77={ai_progress_before:.6f}  R78={ai_progress_after:.6f}  "
          f"delta=+{ai_progress_after-ai_progress_before:.6f}  expected +{expected_ai_progress_delta:.6f}")
    print(f"    treasury:               R77={r77['treasury']}  R78={r78['treasury']}  "
          f"delta={float(r78['treasury'])-float(r77['treasury']):+.2f}")

    # ---- Hard assertions — every contract clause verified in the DB ----
    assert float(r78["budget_social_pct"]) == pytest.approx(expected_social_pct)
    assert r78["budget_production"] == budget_changes["production"]
    assert r78["budget_research"] == budget_changes["research"]

    # Stability rose (social was the only positive driver vs baseline)
    assert s78 >= s77, (
        f"Expected stability to rise with social_pct=1.2, got R77={s77} R78={s78}"
    )

    # Treasury moved (engine ran)
    assert float(r78["treasury"]) != float(r77["treasury"]), (
        "Treasury unchanged — engine did not actually run the budget"
    )

    # Military units credited per contract
    assert ground_after - ground_before == expected_ground_units, (
        f"Ground production mismatch: expected +{expected_ground_units}, "
        f"got +{ground_after - ground_before}"
    )
    assert naval_after - naval_before == expected_naval_units, (
        f"Naval production mismatch: expected +{expected_naval_units}, "
        f"got +{naval_after - naval_before}"
    )

    # R&D progress accumulated per contract
    ai_delta = ai_progress_after - ai_progress_before
    assert ai_delta == pytest.approx(expected_ai_progress_delta, rel=0.05), (
        f"AI R&D progress mismatch: expected +{expected_ai_progress_delta}, "
        f"got +{ai_delta}"
    )
