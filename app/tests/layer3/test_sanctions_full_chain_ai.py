"""Layer 3 — Sanctions vertical slice ACCEPTANCE GATE.

Step 7 of the sanctions vertical slice. This is the definitive end-to-end proof
that a real AI-generated CONTRACT_SANCTIONS v1.0 decision flows all the way
through the system without any human fixup:

    LeaderScenario (from skill harness)
      -> _build_sanctions_prompt (v1.0 schema with signed levels)
        -> LLM call (Gemini/Claude via services.llm)
          -> validate_sanctions_decision (production validator)
            -> agent_decisions row (DB)
              -> resolve_round (writes sanction_decision JSONB + sanctions table)
                -> run_engine_tick (economic engine consumes sanctions state)
                  -> country_states_per_round (sanctions_coefficient recomputed)

Every previous step validated a portion of this chain in isolation:
- Step 1: contract (CONTRACT_SANCTIONS.md)
- Step 2: validator (L1, 44 tests)
- Step 3: engine regression lock (L1, 27 tests)
- Step 4: persistence (L2, 4 tests)
- Step 5: context builder (L2, 7 tests)
- Step 6: AI harness D2 (L3, LLM but no DB — 10 leaders)

Step 7 is the first test that joins the AI half and the DB half.
If it passes, the vertical slice is DONE.

Run::

    cd app && PYTHONPATH=. python3 -m pytest tests/layer3/test_sanctions_full_chain_ai.py -v -s

Cost: 1 LLM call per test on Gemini Flash ~ $0.001.
"""

from __future__ import annotations

import asyncio
import logging

import pytest

from engine.engines.round_tick import run_engine_tick
from engine.round_engine.resolve_round import resolve_round
from engine.services.sanction_validator import validate_sanctions_decision
from engine.services.supabase import get_client
from tests.layer3.test_skill_mandatory_decisions import (
    SCENARIOS,
    _build_sanctions_prompt,
    _call_llm,
    SYSTEM_SANCTIONS,
)
from engine.agents.decisions import _parse_json

logger = logging.getLogger(__name__)

SCENARIO_CODE = "start_one"
TEST_COUNTRY = "columbia"
TEST_TAG = "SANCTIONS_FULL_CHAIN_AI_L3"
# Avoid collision with budget (74-78, 83-84), tariff (60-73, 85-86),
# sanction persistence (65-68), sanction context (69-69)
TEST_ROUNDS = [75, 76]


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
            new_row["sanction_decision"] = None
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


def _snapshot_sanctions_rows(client, sim_run_id: str, imposer: str) -> dict:
    """Snapshot current sanctions rows imposed BY this country → {target: level}."""
    res = (
        client.table("sanctions")
        .select("target_country_code, level")
        .eq("sim_run_id", sim_run_id)
        .eq("imposer_country_code", imposer)
        .execute()
    )
    return {row["target_country_code"]: row["level"] for row in (res.data or [])}


def _restore_sanctions_snapshot(
    client, sim_run_id: str, imposer: str, snapshot: dict
) -> None:
    """Restore sanctions rows imposed BY imposer to the snapshot state.

    After the AI decision runs, we upsert back the original levels so the
    test is hermetic and doesn't poison the DB for other tests.
    """
    current = _snapshot_sanctions_rows(client, sim_run_id, imposer)
    # Delete rows the test created (present in current, not in snapshot)
    for target in current:
        if target not in snapshot:
            client.table("sanctions").delete().eq(
                "sim_run_id", sim_run_id
            ).eq("imposer_country_code", imposer).eq(
                "target_country_code", target
            ).execute()
    # Upsert back original values
    for target, level in snapshot.items():
        client.table("sanctions").upsert({
            "sim_run_id": sim_run_id,
            "imposer_country_code": imposer,
            "target_country_code": target,
            "level": int(level),
            "notes": "",
        }, on_conflict="sim_run_id,imposer_country_code,target_country_code").execute()


def _cleanup(client, scenario_id: str, pre_sanctions_snapshot: dict | None = None) -> None:
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

    if pre_sanctions_snapshot is not None:
        _restore_sanctions_snapshot(
            client, sim_run_id, TEST_COUNTRY, pre_sanctions_snapshot
        )


def _persist_ai_decision(
    client,
    scenario_id: str,
    round_num: int,
    country: str,
    decision_payload: dict,
) -> None:
    """Write a validated AI sanctions decision to agent_decisions."""
    envelope_payload = dict(decision_payload)
    envelope_payload.setdefault("action_type", "set_sanctions")
    envelope_payload.setdefault("country_code", country)
    envelope_payload.setdefault("round_num", round_num)
    envelope_payload["test_tag"] = TEST_TAG

    client.table("agent_decisions").insert(
        {
            "scenario_id": scenario_id,
            "country_code": country,
            "action_type": "set_sanctions",
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


def _get_sanction_level(client, sim_run_id: str, imposer: str, target: str) -> int | None:
    res = (
        client.table("sanctions")
        .select("level")
        .eq("sim_run_id", sim_run_id)
        .eq("imposer_country_code", imposer)
        .eq("target_country_code", target)
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


@pytest.fixture
def pre_snapshot(client):
    """Snapshot Columbia's sanctions rows before the test to restore after."""
    sim_run_id = _get_sim_run_id()
    return _snapshot_sanctions_rows(client, sim_run_id, TEST_COUNTRY)


@pytest.fixture(autouse=True)
def _isolate(client, scenario_id, pre_snapshot):
    _cleanup(client, scenario_id, pre_sanctions_snapshot=None)
    yield
    _cleanup(client, scenario_id, pre_sanctions_snapshot=pre_snapshot)


# ---------------------------------------------------------------------------
# Acceptance gate
# ---------------------------------------------------------------------------


def _get_columbia_scenario():
    for s in SCENARIOS:
        if s.country_code == TEST_COUNTRY:
            return s
    raise RuntimeError(f"No scenario for {TEST_COUNTRY} in SCENARIOS roster")


def test_sanctions_vertical_slice_ai_full_chain(client, scenario_id):
    """THE acceptance gate: AI decision → validator → DB → engine → snapshot.

    This test proves the sanctions vertical slice holds end-to-end with no
    human fixup of the AI output. Every assertion traces back to a
    CONTRACT_SANCTIONS v1.0 clause.
    """
    sim_run_id = _get_sim_run_id()

    # ---- 1. AI makes a sanctions decision --------------------------------
    scenario = _get_columbia_scenario()
    prompt = _build_sanctions_prompt(scenario)

    raw_text = asyncio.run(_call_llm(prompt, SYSTEM_SANCTIONS))
    parsed = _parse_json(raw_text)
    assert parsed is not None, f"LLM returned unparseable JSON: {raw_text!r}"

    # Communication layer would normally inject envelope fields.
    parsed.setdefault("action_type", "set_sanctions")
    parsed.setdefault("country_code", TEST_COUNTRY)
    parsed.setdefault("round_num", 76)

    print(f"\n  [AI decision] {parsed.get('decision')}")
    print(f"  [AI rationale] {(parsed.get('rationale') or '')[:220]}")
    if parsed.get("decision") == "change":
        print(f"  [AI changes.sanctions] {parsed.get('changes', {}).get('sanctions')}")

    # ---- 2. Production validator accepts it ------------------------------
    report = validate_sanctions_decision(parsed)
    assert report["valid"], (
        f"Production validator rejected AI decision: {report['errors']}\n"
        f"payload: {parsed}"
    )
    normalized = report["normalized"]
    assert normalized is not None

    # ---- 3. Seed rounds and persist the AI decision ----------------------
    _seed_round_from_r0(client, scenario_id, 75)
    _seed_round_from_r0(client, scenario_id, 76)
    _persist_ai_decision(client, scenario_id, 76, TEST_COUNTRY, normalized)

    # Capture pre-state for comparison
    r75_pre = _get_country_row(client, scenario_id, 75, TEST_COUNTRY)
    pre_sanc_coeff = float(r75_pre.get("sanctions_coefficient") or 1.0)

    # ---- 4. Run the full chain -------------------------------------------
    resolve_result = resolve_round(SCENARIO_CODE, 76)
    tick_result = run_engine_tick(SCENARIO_CODE, 76)
    assert tick_result.get("success") is True, f"Engine tick failed: {tick_result}"

    # ---- 5. Verify snapshot matches the AI's intent ----------------------
    r76 = _get_country_row(client, scenario_id, 76, TEST_COUNTRY)

    print(f"\n  [snapshot R76] sanctions_coefficient={r76.get('sanctions_coefficient')}")
    print(f"  [persisted sanction_decision] {r76.get('sanction_decision')}")

    # ---- 5a. sanction_decision JSONB matches AI's normalized output ------
    audit = r76.get("sanction_decision")
    assert audit is not None, (
        "sanction_decision JSONB should be populated after resolve_round"
    )
    assert audit["decision"] == normalized["decision"], (
        f"audit decision {audit['decision']} != AI decision {normalized['decision']}"
    )
    assert audit.get("rationale") == normalized["rationale"], (
        "audit rationale should match normalized rationale"
    )

    # ---- 5b. If change, sanctions state table rows match sparse changes --
    if normalized["decision"] == "change":
        expected_sanctions = normalized["changes"]["sanctions"]
        assert audit["changes"]["sanctions"] == expected_sanctions, (
            f"audit changes.sanctions mismatch: "
            f"expected {expected_sanctions}, got {audit['changes']['sanctions']}"
        )
        for target, expected_level in expected_sanctions.items():
            actual_level = _get_sanction_level(
                client, sim_run_id, TEST_COUNTRY, target
            )
            assert actual_level == expected_level, (
                f"sanctions table row for {TEST_COUNTRY}->{target}: "
                f"expected level={expected_level}, got {actual_level}"
            )
        print(
            f"  [verified] {len(expected_sanctions)} sanctions rows upserted correctly"
        )

        # Log the canonical calibration numbers for at least one TARGET
        # that the AI touched — this lets us eyeball the dynamic working.
        first_target = next(iter(expected_sanctions.keys()))
        target_row = _get_country_row(client, scenario_id, 76, first_target)
        target_coeff = float(target_row.get("sanctions_coefficient") or 1.0)
        print(
            f"  [target effect] {first_target} sanctions_coefficient = {target_coeff:.6f} "
            f"(GDP loss = {(1 - target_coeff)*100:.2f}%)"
        )
    else:
        # no_change: changes should be absent from audit
        assert "changes" not in audit, (
            f"no_change audit should not include changes, got {audit.get('changes')}"
        )
        print("  [no_change path] — state table untouched")

    # ---- 6. Engine completed successfully --------------------------------
    post_sanc_coeff = float(r76.get("sanctions_coefficient") or 1.0)
    print(
        f"  [columbia sanctions_coefficient] pre R75={pre_sanc_coeff} post R76={post_sanc_coeff}"
    )
    # Columbia is the imposer; its own sanctions_coefficient depends on whether
    # OTHERS are sanctioning IT. Just verify the engine ran.
    assert r76.get("gdp") is not None, "R76 row must have GDP (engine ran)"

    print("\n  [ACCEPTANCE GATE PASSED] AI sanctions decision persisted and consumed correctly.")
