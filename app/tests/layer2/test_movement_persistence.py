"""Layer 2 — Movement persistence (CONTRACT_MOVEMENT v1.0).

Step 4 of the M1 movement vertical slice. Verifies that scripted move_units
decisions flow through resolve_round into:
  - country_states_per_round.movement_decision JSONB audit column
  - unit_states_per_round (the OUTCOME — positions/status reflect the move)
  - observatory_events (movement_applied / movement_rejected / movement_no_change)
  - last-submission-wins on duplicate move_units in the same round

Uses rounds 55-58 to avoid collision with sanctions persistence (65-68),
budget e2e (74-78), tariff context (60-63), tariff persistence (70-73), opec
context (10-12).

Run::

    cd app && PYTHONPATH=. python3 -m pytest tests/layer2/test_movement_persistence.py -v -s
"""
from __future__ import annotations

import logging

import pytest

from engine.round_engine.resolve_round import resolve_round
from engine.services.supabase import get_client

logger = logging.getLogger(__name__)

SCENARIO_CODE = "start_one"
TEST_COUNTRY = "columbia"
TEST_ROUNDS = [55, 56, 57, 58]
# Columbia has reserve ground units col_g_04..col_g_06 in seed data; deploy
# them onto its own hex (3, 3) which is owned territory.
TEST_RESERVE_UNIT = "col_g_04"
TEST_RESERVE_UNIT_2 = "col_g_05"
TEST_TARGET_HEX = (3, 3)


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
    """Copy R0 country snapshots and unit_states into the test round."""
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
            client.table("country_states_per_round").insert(rows[i : i + 50]).execute()

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
            client.table("unit_states_per_round").insert(rows[i : i + 200]).execute()


def _cleanup(client, scenario_id: str) -> None:
    for rn in TEST_ROUNDS:
        for table in (
            "observatory_events",
            "unit_states_per_round",
            "country_states_per_round",
            "round_states",
            "agent_decisions",
        ):
            client.table(table).delete().eq(
                "scenario_id", scenario_id
            ).eq("round_num", rn).execute()


def _insert_move_units(
    client,
    scenario_id: str,
    round_num: int,
    country: str,
    decision: str,
    rationale: str,
    moves: list[dict] | None = None,
) -> None:
    payload: dict = {
        "action_type": "move_units",
        "country_code": country,
        "round_num": round_num,
        "decision": decision,
        "rationale": rationale,
    }
    if decision == "change":
        payload["changes"] = {"moves": moves or []}

    client.table("agent_decisions").insert(
        {
            "scenario_id": scenario_id,
            "country_code": country,
            "action_type": "move_units",
            "action_payload": payload,
            "rationale": rationale,
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
# Tests
# ---------------------------------------------------------------------------


def test_change_decision_persisted_and_unit_moves(client, scenario_id):
    """change with two reserve deploys → audit JSONB + unit_states updated."""
    _seed_round_from_r0(client, scenario_id, 55)

    moves = [
        {"unit_code": TEST_RESERVE_UNIT, "target": "hex",
         "target_global_row": TEST_TARGET_HEX[0],
         "target_global_col": TEST_TARGET_HEX[1]},
        {"unit_code": TEST_RESERVE_UNIT_2, "target": "hex",
         "target_global_row": TEST_TARGET_HEX[0],
         "target_global_col": TEST_TARGET_HEX[1]},
    ]
    _insert_move_units(
        client, scenario_id, 55, TEST_COUNTRY,
        decision="change",
        rationale=(
            "L2 test: deploy two reserve ground units to Columbia home "
            "territory hex (3,3); verifies audit + unit_states update"
        ),
        moves=moves,
    )

    resolve_round(SCENARIO_CODE, 55)

    row = _get_country_row(client, scenario_id, 55, TEST_COUNTRY)
    audit = row.get("movement_decision")
    assert audit is not None, "movement_decision JSONB should be populated"
    assert audit["decision"] == "change"
    assert audit["action_type"] == "move_units"
    assert len(audit["changes"]["moves"]) == 2

    # Verify unit positions on round 55 reflect the deploy
    u1 = _get_unit(client, scenario_id, 55, TEST_RESERVE_UNIT)
    u2 = _get_unit(client, scenario_id, 55, TEST_RESERVE_UNIT_2)
    assert u1 is not None, f"unit {TEST_RESERVE_UNIT} missing"
    assert u2 is not None, f"unit {TEST_RESERVE_UNIT_2} missing"
    assert u1["status"] == "active"
    assert u2["status"] == "active"
    assert (u1["global_row"], u1["global_col"]) == TEST_TARGET_HEX
    assert (u2["global_row"], u2["global_col"]) == TEST_TARGET_HEX

    print(
        f"\n  [test_change_persisted] audit moves={len(audit['changes']['moves'])}\n"
        f"  {TEST_RESERVE_UNIT}: status={u1['status']} pos=({u1['global_row']},{u1['global_col']})\n"
        f"  {TEST_RESERVE_UNIT_2}: status={u2['status']} pos=({u2['global_row']},{u2['global_col']})"
    )


def test_no_change_writes_audit_preserves_units(client, scenario_id):
    """no_change → audit JSONB written, unit_states unchanged."""
    _seed_round_from_r0(client, scenario_id, 56)

    _insert_move_units(
        client, scenario_id, 56, TEST_COUNTRY,
        decision="no_change",
        rationale="L2 test: no_change should write audit but leave unit positions unchanged",
    )

    resolve_round(SCENARIO_CODE, 56)

    row = _get_country_row(client, scenario_id, 56, TEST_COUNTRY)
    audit = row.get("movement_decision")
    assert audit is not None
    assert audit["decision"] == "no_change"
    assert "changes" not in audit

    # Reserve unit must still be in reserve (no deploy happened)
    u = _get_unit(client, scenario_id, 56, TEST_RESERVE_UNIT)
    assert u is not None
    assert u["status"] == "reserve"
    assert u["global_row"] is None

    print(
        f"\n  [test_no_change] audit decision=no_change\n"
        f"  {TEST_RESERVE_UNIT} status={u['status']} (still reserve, correct)"
    )


def test_invalid_rejected_emits_event(client, scenario_id):
    """Invalid move (foreign-territory deploy) → rejected, audit NULL."""
    _seed_round_from_r0(client, scenario_id, 57)

    # Deploy a Columbia reserve unit onto a hex Columbia doesn't own and
    # has no basing rights or prior occupation on. (4, 17) is hanguk
    # territory — no carrier, no rights → NOT_ALLOWED_TERRITORY.
    moves = [
        {"unit_code": TEST_RESERVE_UNIT, "target": "hex",
         "target_global_row": 4, "target_global_col": 17},
    ]
    _insert_move_units(
        client, scenario_id, 57, TEST_COUNTRY,
        decision="change",
        rationale=(
            "L2 test: deliberate invalid deploy to foreign territory "
            "to verify the rejection path emits an event"
        ),
        moves=moves,
    )

    resolve_round(SCENARIO_CODE, 57)

    row = _get_country_row(client, scenario_id, 57, TEST_COUNTRY)
    assert row.get("movement_decision") is None, (
        f"Invalid decision must not write movement_decision; "
        f"got {row.get('movement_decision')}"
    )

    rej = (
        client.table("observatory_events")
        .select("event_type, country_code, payload")
        .eq("scenario_id", scenario_id)
        .eq("round_num", 57)
        .eq("event_type", "movement_rejected")
        .execute()
    )
    rejections = rej.data or []
    assert any(r["country_code"] == TEST_COUNTRY for r in rejections), (
        "Expected at least one movement_rejected event for columbia"
    )

    # Reserve unit unchanged (still in reserve, no coords)
    u = _get_unit(client, scenario_id, 57, TEST_RESERVE_UNIT)
    assert u["status"] == "reserve"
    assert u["global_row"] is None

    print(
        f"\n  [test_invalid_rejected] rejection events: {len(rejections)}\n"
        f"  {TEST_RESERVE_UNIT} unchanged (still reserve)"
    )


def test_last_submission_wins(client, scenario_id):
    """Two move_units submissions in the same round → second wins."""
    _seed_round_from_r0(client, scenario_id, 58)

    # First submission: deploy col_g_04
    _insert_move_units(
        client, scenario_id, 58, TEST_COUNTRY,
        decision="change",
        rationale="L2 first submission: deploy col_g_04 to (3, 3) — should be replaced",
        moves=[{"unit_code": TEST_RESERVE_UNIT, "target": "hex",
                "target_global_row": 3, "target_global_col": 3}],
    )
    # Second submission: deploy col_g_05 (different unit, different intent)
    _insert_move_units(
        client, scenario_id, 58, TEST_COUNTRY,
        decision="change",
        rationale="L2 second submission: deploy col_g_05 to (4, 3) — this one wins",
        moves=[{"unit_code": TEST_RESERVE_UNIT_2, "target": "hex",
                "target_global_row": 4, "target_global_col": 3}],
    )

    resolve_round(SCENARIO_CODE, 58)

    row = _get_country_row(client, scenario_id, 58, TEST_COUNTRY)
    audit = row.get("movement_decision")
    assert audit is not None
    # The audit must reflect the second submission's moves
    moves = audit["changes"]["moves"]
    assert len(moves) == 1
    assert moves[0]["unit_code"] == TEST_RESERVE_UNIT_2
    assert (moves[0]["target_global_row"], moves[0]["target_global_col"]) == (4, 3)

    # And col_g_05 actually got deployed
    u2 = _get_unit(client, scenario_id, 58, TEST_RESERVE_UNIT_2)
    assert u2["status"] == "active"
    assert (u2["global_row"], u2["global_col"]) == (4, 3)

    # col_g_04 should still be in reserve (first submission's move discarded)
    u1 = _get_unit(client, scenario_id, 58, TEST_RESERVE_UNIT)
    assert u1["status"] == "reserve"

    print(
        f"\n  [test_last_submission_wins] audit reflects 2nd submission\n"
        f"  {TEST_RESERVE_UNIT_2} active at (4, 3) — winner\n"
        f"  {TEST_RESERVE_UNIT} still reserve — discarded"
    )
