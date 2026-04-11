"""Layer 3 — Movement vertical slice ACCEPTANCE GATE.

Step 7 of the M1 movement vertical slice. End-to-end proof that a real
AI-generated CONTRACT_MOVEMENT v1.0 decision flows all the way through the
system without any human fixup:

    MovementScenario (from skill harness)
      -> _build_movement_prompt
        -> LLM call (Gemini/Claude)
          -> validate_movement_decision (production validator)
            -> agent_decisions row (DB)
              -> resolve_round (writes movement_decision JSONB +
                                 mutates unit_states_per_round)
                -> verify snapshot reflects intent

IMPORTANT — visual demo: this test deliberately leaves rounds 200 and 201
in the DB after the run for Marat's Observatory review. There is NO cleanup
fixture that wipes the rows on tear-down (unlike the L2 persistence tests).
Re-running the test will overwrite the rows in place via upsert.

Run::

    cd app && PYTHONPATH=. python3 -m pytest tests/layer3/test_movement_full_chain_ai.py -v -s

Cost: 1 LLM call on Gemini Flash ~ $0.001.
"""
from __future__ import annotations

import asyncio
import logging

import pytest

from engine.agents.decisions import _parse_json
from engine.round_engine.resolve_round import resolve_round
from engine.services.movement_data import (
    build_units_dict_from_rows,
    load_basing_rights,
    load_global_grid_zones,
)
from engine.services.movement_validator import validate_movement_decision
from engine.services.supabase import get_client
from tests.layer3.test_skill_movement import (
    MOVEMENT_ROUND_NUM,
    SYSTEM_MOVEMENT,
    _build_movement_prompt,
    _call_llm,
    _columbia_reference,
)

logger = logging.getLogger(__name__)

SCENARIO_CODE = "start_one"
TEST_COUNTRY = "columbia"
TEST_TAG = "MOVEMENT_FULL_CHAIN_AI_L3"
# Visual demo rounds — NOT cleaned up at end of test
DEMO_ROUNDS = [200, 201]


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
            new_row["movement_decision"] = None
            rows.append(new_row)
        for i in range(0, len(rows), 50):
            client.table("country_states_per_round").upsert(
                rows[i : i + 50],
                on_conflict="scenario_id,round_num,country_code",
            ).execute()

    us0 = (
        client.table("unit_states_per_round")
        .select("*")
        .eq("scenario_id", scenario_id)
        .eq("round_num", 0)
        .execute()
    )
    if us0.data:
        rows = []
        for row in us0.data:
            new_row = {k: v for k, v in row.items() if k != "id"}
            new_row["round_num"] = round_num
            rows.append(new_row)
        for i in range(0, len(rows), 200):
            client.table("unit_states_per_round").upsert(
                rows[i : i + 200],
                on_conflict="scenario_id,round_num,unit_code",
            ).execute()


def _persist_ai_decision(
    client, scenario_id: str, round_num: int, country: str, decision: dict,
) -> None:
    payload = dict(decision)
    payload.setdefault("action_type", "move_units")
    payload.setdefault("country_code", country)
    payload.setdefault("round_num", round_num)
    payload["test_tag"] = TEST_TAG

    client.table("agent_decisions").insert({
        "scenario_id": scenario_id,
        "country_code": country,
        "action_type": "move_units",
        "action_payload": payload,
        "rationale": payload.get("rationale", ""),
        "validation_status": "passed",
        "round_num": round_num,
    }).execute()


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


def _get_unit(client, scenario_id: str, round_num: int, unit_code: str) -> dict | None:
    res = (
        client.table("unit_states_per_round")
        .select("*")
        .eq("scenario_id", scenario_id)
        .eq("round_num", round_num)
        .eq("unit_code", unit_code)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


# ---------------------------------------------------------------------------
# Fixtures (no cleanup — visual demo persists)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def client():
    return get_client()


@pytest.fixture(scope="module")
def scenario_id(client):
    return _get_scenario_id(client)


# ---------------------------------------------------------------------------
# Acceptance gate
# ---------------------------------------------------------------------------


def test_movement_vertical_slice_ai_full_chain(client, scenario_id):
    """THE acceptance gate: AI decision → validator → DB → engine → snapshot.

    Proves the M1 movement vertical slice holds end-to-end with no human
    fixup. Every assertion traces back to a CONTRACT_MOVEMENT v1.0 clause.

    Visual demo: rounds 200-201 are LEFT IN THE DB after the run for Marat's
    Observatory review.
    """
    # ---- 1. AI makes a movement decision ----------------------------------
    s = _columbia_reference()
    prompt = _build_movement_prompt(s)
    raw_text = asyncio.run(_call_llm(prompt, SYSTEM_MOVEMENT, max_tokens=600))
    parsed = _parse_json(raw_text)
    assert parsed is not None, f"LLM returned unparseable JSON: {raw_text!r}"

    # Communication-layer envelope injection (matches Step 6 harness)
    parsed.setdefault("action_type", "move_units")
    parsed.setdefault("country_code", TEST_COUNTRY)
    parsed.setdefault("round_num", 201)

    print(f"\n  [AI decision] {parsed.get('decision')}")
    print(f"  [AI rationale] {(parsed.get('rationale') or '')[:220]}")
    if parsed.get("decision") == "change":
        print(f"  [AI changes] {parsed.get('changes')}")

    # ---- 2. Production validator accepts it -------------------------------
    # The harness scenario was tiny (only 3 units) — for the production
    # validator we feed the REAL Columbia state from R0, so any unit_code
    # the LLM picks must exist in the seed inventory.
    real_units_res = (
        client.table("unit_states_per_round")
        .select("*")
        .eq("scenario_id", scenario_id)
        .eq("round_num", 0)
        .execute()
    )
    real_units = build_units_dict_from_rows(real_units_res.data or [])
    real_zones = load_global_grid_zones()
    real_basing = load_basing_rights(client)

    report = validate_movement_decision(
        parsed, real_units, real_zones, real_basing,
    )
    assert report["valid"], (
        f"Production validator rejected AI decision: {report['errors']}\n"
        f"payload: {parsed}"
    )
    normalized = report["normalized"]
    assert normalized is not None

    # ---- 3. Seed the demo rounds ------------------------------------------
    _seed_round_from_r0(client, scenario_id, 200)
    _seed_round_from_r0(client, scenario_id, 201)

    # Pre-state for one of the AI's chosen units (if change), or any unit.
    if normalized["decision"] == "change":
        first_move = normalized["changes"]["moves"][0]
        sample_code = first_move["unit_code"]
    else:
        sample_code = "col_g_04"

    pre = _get_unit(client, scenario_id, 200, sample_code)
    print(
        f"  [pre R200] {sample_code}: status={pre.get('status') if pre else '?'} "
        f"pos=({pre.get('global_row') if pre else '?'},{pre.get('global_col') if pre else '?'})"
    )

    # ---- 4. Persist AI decision and run resolve_round ---------------------
    _persist_ai_decision(client, scenario_id, 201, TEST_COUNTRY, normalized)
    resolve_round(SCENARIO_CODE, 201)

    # ---- 5. Verify snapshot matches AI's intent ---------------------------
    row = _get_country_row(client, scenario_id, 201, TEST_COUNTRY)
    audit = row.get("movement_decision")
    assert audit is not None, (
        "movement_decision JSONB should be populated after resolve_round"
    )
    assert audit["decision"] == normalized["decision"]
    assert audit["action_type"] == "move_units"
    assert audit["country_code"] == TEST_COUNTRY
    assert audit.get("rationale") == normalized["rationale"]

    if normalized["decision"] == "change":
        assert audit["changes"]["moves"] == normalized["changes"]["moves"]

        # Verify at least the first move took effect in unit_states_per_round.
        post = _get_unit(client, scenario_id, 201, sample_code)
        assert post is not None, f"unit {sample_code} missing from R201 snapshot"
        first = normalized["changes"]["moves"][0]
        if first["target"] == "hex":
            assert post["status"] in ("active", "embarked"), (
                f"unit {sample_code} should be active or embarked, got {post['status']}"
            )
            if post["status"] == "active":
                assert (post["global_row"], post["global_col"]) == (
                    first["target_global_row"], first["target_global_col"],
                ), (
                    f"unit {sample_code} should be at "
                    f"({first['target_global_row']},{first['target_global_col']}), "
                    f"got ({post['global_row']},{post['global_col']})"
                )
        elif first["target"] == "reserve":
            assert post["status"] == "reserve"
            assert post["global_row"] is None
        print(
            f"  [post R201] {sample_code}: status={post['status']} "
            f"pos=({post.get('global_row')},{post.get('global_col')})"
        )
    else:
        assert "changes" not in audit, (
            f"no_change audit should not include changes, got {audit.get('changes')}"
        )
        # no_change path — sample unit unchanged
        post = _get_unit(client, scenario_id, 201, sample_code)
        assert post["status"] == (pre["status"] if pre else "reserve")
        print(f"  [no_change path] {sample_code} preserved")

    print(
        "\n  [ACCEPTANCE GATE PASSED] "
        "AI movement decision persisted and unit_states updated.\n"
        f"  Visual demo rounds {DEMO_ROUNDS} left in DB for Observatory review."
    )
