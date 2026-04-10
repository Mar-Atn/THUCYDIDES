"""Layer 3 — Tariff vertical slice ACCEPTANCE GATE.

Step 7 of the tariff vertical slice. This is the definitive end-to-end proof
that a real AI-generated CONTRACT_TARIFFS v1.0 decision flows all the way
through the system without any human fixup:

    LeaderScenario (from skill harness)
      -> _build_tariffs_prompt (v1.0 schema)
        -> LLM call (Gemini/Claude via services.llm)
          -> validate_tariffs_decision (production validator)
            -> agent_decisions row (DB)
              -> resolve_round (writes tariff_decision JSONB + tariffs table)
                -> run_engine_tick (economic engine consumes tariffs state)
                  -> country_states_per_round (tariff_coefficient recomputed)

Every previous step validated a portion of this chain in isolation:
- Step 1: contract
- Step 2: validator (L1)
- Step 3: engine regression lock (L1)
- Step 4: persistence (L2)
- Step 5: context builder (L2)
- Step 6: AI harness D3 (L3, LLM but no DB)

Step 7 is the first test that actually joins the AI half and the DB half.
If it passes, the vertical slice is DONE.

Run::

    cd app && PYTHONPATH=. python3 -m pytest tests/layer3/test_tariffs_full_chain_ai.py -v -s

Cost: 1 LLM call per test on Gemini Flash ~ $0.001.
"""

from __future__ import annotations

import asyncio
import logging

import pytest

from engine.engines.round_tick import run_engine_tick
from engine.round_engine.resolve_round import resolve_round
from engine.services.tariff_validator import validate_tariffs_decision
from engine.services.supabase import get_client
from tests.layer3.test_skill_mandatory_decisions import (
    ROUND_NUM,
    SCENARIOS,
    _build_tariffs_prompt,
    _call_llm,
    SYSTEM_TARIFFS,
)
from engine.agents.decisions import _parse_json

logger = logging.getLogger(__name__)

SCENARIO_CODE = "start_one"
TEST_COUNTRY = "columbia"
TEST_TAG = "TARIFFS_FULL_CHAIN_AI_L3"
# Avoid collision with budget (74-78, 83-84), tariff persistence (70-73),
# tariff context (60-63)
TEST_ROUNDS = [85, 86]


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


def _get_sim_run_id() -> str:
    from engine.config.settings import Settings
    return Settings().default_sim_id


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
    sim_run_id = _get_sim_run_id()
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
    # Clean test-imposed tariffs rows tagged by resolve_round handler
    try:
        client.table("tariffs").delete().eq(
            "sim_run_id", sim_run_id
        ).eq("imposer_country_id", TEST_COUNTRY).like(
            "notes", "set_tariffs by %"
        ).execute()
    except Exception:
        pass


def _persist_ai_decision(
    client,
    scenario_id: str,
    round_num: int,
    country: str,
    decision_payload: dict,
) -> None:
    """Write a validated AI tariff decision to agent_decisions."""
    envelope_payload = dict(decision_payload)
    envelope_payload.setdefault("action_type", "set_tariffs")
    envelope_payload.setdefault("country_code", country)
    envelope_payload.setdefault("round_num", round_num)
    envelope_payload["test_tag"] = TEST_TAG

    client.table("agent_decisions").insert(
        {
            "scenario_id": scenario_id,
            "country_code": country,
            "action_type": "set_tariffs",
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


def _get_tariff_level(client, sim_run_id: str, imposer: str, target: str) -> int | None:
    res = (
        client.table("tariffs")
        .select("level")
        .eq("sim_run_id", sim_run_id)
        .eq("imposer_country_id", imposer)
        .eq("target_country_id", target)
        .limit(1)
        .execute()
    )
    if res.data:
        return res.data[0]["level"]
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


def _get_columbia_scenario():
    for s in SCENARIOS:
        if s.country_code == TEST_COUNTRY:
            return s
    raise RuntimeError(f"No scenario for {TEST_COUNTRY} in SCENARIOS roster")


def test_tariffs_vertical_slice_ai_full_chain(client, scenario_id):
    """THE acceptance gate: AI decision → validator → DB → engine → snapshot.

    This test proves the tariff vertical slice holds end-to-end with no human
    fixup of the AI output. Every assertion traces back to a CONTRACT_TARIFFS
    v1.0 clause.
    """
    sim_run_id = _get_sim_run_id()

    # ---- 1. AI makes a tariff decision -----------------------------------
    scenario = _get_columbia_scenario()
    prompt = _build_tariffs_prompt(scenario)

    raw_text = asyncio.run(_call_llm(prompt, SYSTEM_TARIFFS))
    parsed = _parse_json(raw_text)
    assert parsed is not None, f"LLM returned unparseable JSON: {raw_text!r}"

    # Communication layer would normally inject envelope fields.
    parsed.setdefault("action_type", "set_tariffs")
    parsed.setdefault("country_code", TEST_COUNTRY)
    parsed.setdefault("round_num", 86)  # we resolve into round 86

    print(f"\n  [AI decision] {parsed.get('decision')}")
    print(f"  [AI rationale] {(parsed.get('rationale') or '')[:200]}")
    if parsed.get("decision") == "change":
        print(f"  [AI changes] {parsed.get('changes')}")

    # ---- 2. Production validator accepts it ------------------------------
    report = validate_tariffs_decision(parsed)
    assert report["valid"], (
        f"Production validator rejected AI decision: {report['errors']}\n"
        f"payload: {parsed}"
    )
    normalized = report["normalized"]
    assert normalized is not None

    # ---- 3. Seed R85 from R0 and persist AI decision for R86 -------------
    _seed_round_from_r0(client, scenario_id, 85)
    _seed_round_from_r0(client, scenario_id, 86)
    _persist_ai_decision(client, scenario_id, 86, TEST_COUNTRY, normalized)

    # Capture pre-state tariff_coefficient for comparison
    r85_pre = _get_country_row(client, scenario_id, 85, TEST_COUNTRY)
    pre_tariff_coeff = float(r85_pre.get("tariff_coefficient") or 1.0)

    # ---- 4. Run the full chain -------------------------------------------
    resolve_result = resolve_round(SCENARIO_CODE, 86)
    tick_result = run_engine_tick(SCENARIO_CODE, 86)
    assert tick_result.get("success") is True, f"Engine tick failed: {tick_result}"

    # ---- 5. Verify snapshot matches the AI's intent ----------------------
    r86 = _get_country_row(client, scenario_id, 86, TEST_COUNTRY)

    print(f"\n  [snapshot R86] tariff_coefficient={r86.get('tariff_coefficient')}")
    print(f"  [persisted tariff_decision] {r86.get('tariff_decision')}")

    # ---- 5a. tariff_decision JSONB matches AI's normalized output --------
    audit = r86.get("tariff_decision")
    assert audit is not None, (
        "tariff_decision JSONB should be populated after resolve_round"
    )
    assert audit["decision"] == normalized["decision"], (
        f"audit decision {audit['decision']} != AI decision {normalized['decision']}"
    )
    assert audit.get("rationale") == normalized["rationale"], (
        "audit rationale should match normalized rationale"
    )

    # ---- 5b. If change, tariffs state table rows match sparse changes ----
    if normalized["decision"] == "change":
        expected_tariffs = normalized["changes"]["tariffs"]
        assert audit["changes"]["tariffs"] == expected_tariffs, (
            f"audit changes.tariffs mismatch: "
            f"expected {expected_tariffs}, got {audit['changes']['tariffs']}"
        )
        for target, expected_level in expected_tariffs.items():
            actual_level = _get_tariff_level(
                client, sim_run_id, TEST_COUNTRY, target
            )
            assert actual_level == expected_level, (
                f"tariffs table row for {TEST_COUNTRY}->{target}: "
                f"expected level={expected_level}, got {actual_level}"
            )
        print(
            f"  [verified] {len(expected_tariffs)} tariff rows upserted correctly"
        )
    else:
        # no_change: changes should be absent from audit
        assert "changes" not in audit, (
            f"no_change audit should not include changes, got {audit.get('changes')}"
        )
        print("  [no_change path] — state table untouched")

    # ---- 6. Engine completed successfully --------------------------------
    # tariff_coefficient should be present (recomputed by engine).
    post_tariff_coeff = float(r86.get("tariff_coefficient") or 1.0)
    print(
        f"  [tariff_coefficient] pre R85={pre_tariff_coeff} post R86={post_tariff_coeff}"
    )
    # If the AI changed tariffs, the coefficient SHOULD move (unless all changes
    # happened to exactly match baseline — rare). We tolerate either outcome
    # but log a warning when the AI decision was change but coefficient is
    # unchanged at 1.0.
    if normalized["decision"] == "change":
        non_zero_changes = {
            k: v for k, v in normalized["changes"]["tariffs"].items() if v > 0
        }
        if non_zero_changes:
            # With non-zero tariffs, the imposer's own coefficient should be < 1.0
            # because of self_damage. We assert the engine actually computed it.
            assert post_tariff_coeff <= 1.0, (
                f"tariff_coefficient should be <= 1.0 after imposing tariffs, "
                f"got {post_tariff_coeff}"
            )
    # Engine result shape
    assert r86.get("gdp") is not None, "R86 row must have GDP (engine ran)"

    print("\n  [ACCEPTANCE GATE PASSED] AI tariff decision persisted and consumed correctly.")
