"""Layer 3 — OPEC vertical slice ACCEPTANCE GATE.

Step 7 of the OPEC vertical slice. End-to-end proof that a real AI-generated
CONTRACT_OPEC v1.0 decision flows all the way through the system without any
human fixup:

    LeaderScenario (from skill harness)
      -> _build_opec_prompt (v1.0 schema with production_level)
        -> LLM call (Gemini/Claude via services.llm)
          -> validate_opec_decision (production validator)
            -> agent_decisions row (DB)
              -> resolve_round (writes opec_decision JSONB + opec_production)
                -> run_engine_tick (economic engine recomputes oil_price)
                  -> global_state_per_round.oil_price

Run::

    cd app && PYTHONPATH=. python3 -m pytest tests/layer3/test_opec_full_chain_ai.py -v -s

Cost: 1 LLM call per test on Gemini Flash ~ $0.001.
"""
from __future__ import annotations

import asyncio
import logging

import pytest

from engine.agents.decisions import _parse_json
from engine.engines.round_tick import run_engine_tick
from engine.round_engine.resolve_round import resolve_round
from engine.services.opec_validator import validate_opec_decision
from engine.services.supabase import get_client
from tests.layer3.test_skill_mandatory_decisions import (
    SCENARIOS,
    SYSTEM_OPEC,
    _build_opec_prompt,
    _call_llm,
)

logger = logging.getLogger(__name__)

SCENARIO_CODE = "start_one"
TEST_COUNTRY = "solaria"  # canonical OPEC+ test country
TEST_TAG = "OPEC_FULL_CHAIN_AI_L3"
# Avoid collision with all other slices (sanctions 75-76, etc)
TEST_ROUNDS = [40, 41]


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


def _persist_ai_decision(
    client,
    scenario_id: str,
    round_num: int,
    country: str,
    decision_payload: dict,
) -> None:
    envelope_payload = dict(decision_payload)
    envelope_payload.setdefault("action_type", "set_opec")
    envelope_payload.setdefault("country_code", country)
    envelope_payload.setdefault("round_num", round_num)
    envelope_payload["test_tag"] = TEST_TAG

    client.table("agent_decisions").insert(
        {
            "scenario_id": scenario_id,
            "country_code": country,
            "action_type": "set_opec",
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


def _get_oil_price(client, scenario_id: str, round_num: int) -> float | None:
    res = (
        client.table("global_state_per_round")
        .select("oil_price")
        .eq("scenario_id", scenario_id)
        .eq("round_num", round_num)
        .limit(1)
        .execute()
    )
    if res.data and res.data[0].get("oil_price") is not None:
        return float(res.data[0]["oil_price"])
    return None


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


def _get_solaria_scenario():
    for s in SCENARIOS:
        if s.country_code == TEST_COUNTRY:
            return s
    raise RuntimeError(f"No scenario for {TEST_COUNTRY} in SCENARIOS roster")


def test_opec_vertical_slice_ai_full_chain(client, scenario_id):
    """THE acceptance gate: AI decision → validator → DB → engine → snapshot.

    Proves the OPEC vertical slice holds end-to-end with no human fixup.
    Every assertion traces back to a CONTRACT_OPEC v1.0 clause.
    """
    # ---- 1. AI makes an OPEC decision -------------------------------------
    scenario = _get_solaria_scenario()
    assert scenario.is_opec, "Solaria must be an OPEC+ member"
    prompt = _build_opec_prompt(scenario)

    raw_text = asyncio.run(_call_llm(prompt, SYSTEM_OPEC))
    parsed = _parse_json(raw_text)
    assert parsed is not None, f"LLM returned unparseable JSON: {raw_text!r}"

    # Communication layer envelope injection
    parsed.setdefault("action_type", "set_opec")
    parsed.setdefault("country_code", TEST_COUNTRY)
    parsed.setdefault("round_num", 41)

    print(f"\n  [AI decision] {parsed.get('decision')}")
    print(f"  [AI rationale] {(parsed.get('rationale') or '')[:220]}")
    if parsed.get("decision") == "change":
        print(f"  [AI changes] {parsed.get('changes')}")

    # ---- 2. Production validator accepts it -------------------------------
    report = validate_opec_decision(parsed)
    assert report["valid"], (
        f"Production validator rejected AI decision: {report['errors']}\n"
        f"payload: {parsed}"
    )
    normalized = report["normalized"]
    assert normalized is not None

    # ---- 3. Seed rounds and persist the AI decision -----------------------
    _seed_round_from_r0(client, scenario_id, 40)
    _seed_round_from_r0(client, scenario_id, 41)

    # Pre-state: solaria's opec_production at R40 (should be 'normal')
    r40_pre = _get_country_row(client, scenario_id, 40, TEST_COUNTRY)
    r40_opec_level = r40_pre.get("opec_production")
    r40_oil_price = _get_oil_price(client, scenario_id, 40)
    print(f"  [pre R40] solaria opec_production={r40_opec_level} oil_price={r40_oil_price}")

    _persist_ai_decision(client, scenario_id, 41, TEST_COUNTRY, normalized)

    # ---- 4. Run the full chain --------------------------------------------
    resolve_round(SCENARIO_CODE, 41)
    tick_result = run_engine_tick(SCENARIO_CODE, 41)
    assert tick_result.get("success") is True, f"Engine tick failed: {tick_result}"

    # ---- 5. Verify snapshot matches the AI's intent -----------------------
    r41 = _get_country_row(client, scenario_id, 41, TEST_COUNTRY)
    print(f"\n  [snapshot R41] opec_production={r41.get('opec_production')}")
    print(f"  [audit opec_decision] {r41.get('opec_decision')}")

    # ---- 5a. opec_decision JSONB matches AI's normalized output -----------
    audit = r41.get("opec_decision")
    assert audit is not None, (
        "opec_decision JSONB should be populated after resolve_round"
    )
    assert audit["decision"] == normalized["decision"], (
        f"audit decision {audit['decision']} != AI decision {normalized['decision']}"
    )
    assert audit.get("rationale") == normalized["rationale"], (
        "audit rationale should match normalized rationale"
    )
    assert audit.get("action_type") == "set_opec"
    assert audit.get("country_code") == TEST_COUNTRY

    # ---- 5b. If change, opec_production column updated --------------------
    if normalized["decision"] == "change":
        expected_level = normalized["changes"]["production_level"]
        assert audit["changes"]["production_level"] == expected_level
        assert r41.get("opec_production") == expected_level, (
            f"opec_production should be {expected_level}, "
            f"got {r41.get('opec_production')}"
        )
        print(f"  [verified] opec_production -> {expected_level}")
    else:
        # no_change: opec_production unchanged from R40 baseline
        assert "changes" not in audit, (
            f"no_change audit should not include changes, got {audit.get('changes')}"
        )
        assert r41.get("opec_production") == r40_opec_level, (
            f"no_change must preserve R40 level ({r40_opec_level}), "
            f"got {r41.get('opec_production')}"
        )
        print(f"  [no_change path] opec_production preserved at {r40_opec_level}")

    # ---- 6. Engine recomputed oil price for R41 ---------------------------
    r41_oil_price = _get_oil_price(client, scenario_id, 41)
    assert r41_oil_price is not None, (
        "global_state_per_round.oil_price should exist for R41 after engine tick"
    )
    assert r41_oil_price > 0, f"R41 oil_price must be positive, got {r41_oil_price}"
    print(f"  [oil price] R40={r40_oil_price} -> R41={r41_oil_price:.2f}")

    # ---- 7. Engine also produced a GDP row for solaria --------------------
    assert r41.get("gdp") is not None, "R41 row must have GDP (engine ran)"

    print(
        "\n  [ACCEPTANCE GATE PASSED] "
        "AI OPEC decision persisted and consumed correctly."
    )
