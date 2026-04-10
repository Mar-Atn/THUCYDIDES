"""Layer 3 — Budget vertical slice ACCEPTANCE GATE.

Step 7 of the budget vertical slice. This is the definitive end-to-end proof
that a real AI-generated CONTRACT_BUDGET v1.1 decision flows all the way
through the system without any human fixup:

    LeaderScenario (from skill harness)
      -> _build_budget_prompt (v1.1 schema)
        -> LLM call (Gemini/Claude via services.llm)
          -> validate_budget_decision (production validator)
            -> agent_decisions row (DB)
              -> resolve_round (writes budget_* cols on country snapshot)
                -> run_engine_tick (economic engine consumes v1.1 budget)
                  -> country_states_per_round (treasury, stability, ...)

Every previous step validated a portion of this chain in isolation:
- Step 1: validator (L1)
- Step 2: economic engine (L1)
- Step 3: persistence (L2)
- Step 4: scripted e2e (L2)
- Step 5: context + dry-run (L2)
- Step 6: AI harness (L3, LLM but no DB)

Step 7 is the first test that actually joins the AI half and the DB half.
If it passes, the vertical slice is DONE.

Run::

    cd app && PYTHONPATH=. python3 -m pytest tests/layer3/test_budget_full_chain_ai.py -v -s

Cost: 1 LLM call per test on Gemini Flash ~ $0.001.
"""

from __future__ import annotations

import asyncio
import logging

import pytest

from engine.engines.round_tick import run_engine_tick
from engine.round_engine.resolve_round import resolve_round
from engine.services.budget_validator import validate_budget_decision
from engine.services.supabase import get_client
from tests.layer3.test_skill_mandatory_decisions import (
    ROUND_NUM,
    SCENARIOS,
    _build_budget_prompt,
    _call_llm,
    SYSTEM_BUDGET,
)
from engine.agents.decisions import _parse_json

logger = logging.getLogger(__name__)

SCENARIO_CODE = "start_one"
TEST_COUNTRY = "columbia"
TEST_TAG = "BUDGET_FULL_CHAIN_AI_L3"
TEST_ROUNDS = [83, 84]  # above the e2e battery window


# ---------------------------------------------------------------------------
# Helpers — mirror test_budget_e2e.py patterns
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


def _persist_ai_decision(
    client,
    scenario_id: str,
    round_num: int,
    country: str,
    decision_payload: dict,
) -> None:
    """Write a validated AI budget decision to agent_decisions."""
    envelope_payload = dict(decision_payload)
    envelope_payload.setdefault("action_type", "set_budget")
    envelope_payload.setdefault("country_code", country)
    envelope_payload.setdefault("round_num", round_num)
    envelope_payload["test_tag"] = TEST_TAG

    client.table("agent_decisions").insert(
        {
            "scenario_id": scenario_id,
            "country_code": country,
            "action_type": "set_budget",
            "action_payload": envelope_payload,
            "rationale": envelope_payload.get("rationale", ""),
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
    _cleanup(client, scenario_id)
    yield
    _cleanup(client, scenario_id)


# ---------------------------------------------------------------------------
# Acceptance gate
# ---------------------------------------------------------------------------


def _get_columbia_scenario():
    for s in SCENARIOS:
        if s.country_code == TEST_COUNTRY:
            return s
    raise RuntimeError(f"No scenario for {TEST_COUNTRY} in SCENARIOS roster")


def test_budget_vertical_slice_ai_full_chain(client, scenario_id):
    """THE acceptance gate: AI decision → validator → DB → engine → snapshot.

    This test proves the vertical slice holds end-to-end with no human
    fixup of the AI output. Every assertion traces back to a CONTRACT_BUDGET
    v1.1 clause.
    """
    # ---- 1. AI makes a budget decision -----------------------------------
    scenario = _get_columbia_scenario()
    prompt = _build_budget_prompt(scenario)

    raw_text = asyncio.run(_call_llm(prompt, SYSTEM_BUDGET))
    parsed = _parse_json(raw_text)
    assert parsed is not None, f"LLM returned unparseable JSON: {raw_text!r}"

    # Communication layer would normally inject envelope fields.
    parsed.setdefault("action_type", "set_budget")
    parsed.setdefault("country_code", TEST_COUNTRY)
    parsed.setdefault("round_num", 84)  # we resolve into round 84

    print(f"\n  [AI decision] {parsed.get('decision')}")
    print(f"  [AI rationale] {(parsed.get('rationale') or '')[:200]}")
    if parsed.get("decision") == "change":
        print(f"  [AI changes] {parsed.get('changes')}")

    # ---- 2. Production validator accepts it ------------------------------
    report = validate_budget_decision(parsed)
    assert report["valid"], (
        f"Production validator rejected AI decision: {report['errors']}\n"
        f"payload: {parsed}"
    )
    normalized = report["normalized"]
    assert normalized is not None

    # ---- 3. Seed R83 from R0 and persist AI decision for R84 -------------
    _seed_round_from_r0(client, scenario_id, 83)
    _persist_ai_decision(client, scenario_id, 84, TEST_COUNTRY, normalized)

    # ---- 4. Run the full chain -------------------------------------------
    resolve_result = resolve_round(SCENARIO_CODE, 84)
    tick_result = run_engine_tick(SCENARIO_CODE, 84)
    assert tick_result.get("success") is True, f"Engine tick failed: {tick_result}"

    # ---- 5. Verify snapshot matches the AI's intent ----------------------
    r83 = _get_country_row(client, scenario_id, 83, TEST_COUNTRY)
    r84 = _get_country_row(client, scenario_id, 84, TEST_COUNTRY)

    print(f"\n  [snapshot R83] treasury={r83['treasury']} stability={r83['stability']}")
    print(f"  [snapshot R84] treasury={r84['treasury']} stability={r84['stability']}")
    print(f"  [persisted social_pct] {r84.get('budget_social_pct')}")
    print(f"  [persisted production] {r84.get('budget_production')}")
    print(f"  [persisted research]   {r84.get('budget_research')}")

    decision = normalized["decision"]
    if decision == "change":
        changes = normalized["changes"]
        # social_pct persisted exactly
        assert float(r84["budget_social_pct"]) == pytest.approx(
            changes["social_pct"]
        ), "budget_social_pct did not match AI decision"
        # production persisted exactly (all 5 branches)
        assert r84["budget_production"] == changes["production"], (
            f"budget_production mismatch: "
            f"expected {changes['production']}, got {r84['budget_production']}"
        )
        # research persisted exactly
        assert r84["budget_research"] == changes["research"], (
            f"budget_research mismatch: "
            f"expected {changes['research']}, got {r84['budget_research']}"
        )
    else:
        # no_change should carry R83's (empty) baseline — columns may be null
        # since R83 was seeded from R0 with no explicit budget. The important
        # thing is that resolve_round did not crash.
        print("  [no_change path] — no assertions on persisted columns")

    # ---- 6. Engine actually ran (treasury or stability moved) ------------
    moved = (
        float(r84["treasury"]) != float(r83["treasury"])
        or float(r84["stability"]) != float(r83["stability"])
    )
    assert moved, (
        "Engine did not run: both treasury and stability unchanged between "
        "R83 and R84. The budget was written but not consumed."
    )

    # ---- 7. Contract-derived stability check -----------------------------
    # stability_delta_from_social = (social_pct - 1.0) * 4.0
    # Other engine effects nudge, so we only check directionality.
    if decision == "change":
        social = float(normalized["changes"]["social_pct"])
        if social < 1.0 - 0.05:
            assert float(r84["stability"]) <= float(r83["stability"]) + 0.1, (
                f"social_pct {social} < 1.0 but stability rose: "
                f"R83={r83['stability']} R84={r84['stability']}"
            )
        elif social > 1.0 + 0.05:
            assert float(r84["stability"]) >= float(r83["stability"]) - 0.1, (
                f"social_pct {social} > 1.0 but stability dropped: "
                f"R83={r83['stability']} R84={r84['stability']}"
            )

    print("\n  [ACCEPTANCE GATE PASSED] AI decision persisted and consumed correctly.")
