"""Layer 2 — OPEC persistence (CONTRACT_OPEC v1.0).

Step 4 of the OPEC vertical slice. Verifies scripted set_opec decisions flow
through resolve_round into:
  - country_states_per_round.opec_decision JSONB (audit column)
  - country_states_per_round.opec_production (live value)

Uses rounds 50-53 to avoid collision with other slices.

Run::

    cd app && PYTHONPATH=. python3 -m pytest tests/layer2/test_opec_persistence.py -v
"""

from __future__ import annotations

import logging

import pytest

from engine.round_engine.resolve_round import resolve_round
from engine.services.supabase import get_client

logger = logging.getLogger(__name__)

SCENARIO_CODE = "start_one"
TEST_COUNTRY = "solaria"   # OPEC+ member
TEST_ROUNDS = [50, 51, 52, 53]


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


def _cleanup(client, scenario_id: str) -> None:
    for rn in TEST_ROUNDS:
        for table in (
            "observatory_events",
            "country_states_per_round",
            "round_states",
            "agent_decisions",
        ):
            client.table(table).delete().eq(
                "scenario_id", scenario_id
            ).eq("round_num", rn).execute()


def _insert_set_opec(
    client,
    scenario_id: str,
    round_num: int,
    country: str,
    decision: str = "change",
    production_level: str | None = None,
    rationale: str | None = None,
) -> None:
    payload: dict = {
        "action_type": "set_opec",
        "country_code": country,
        "round_num": round_num,
        "decision": decision,
        "rationale": rationale or (
            "L2 test: scripted OPEC decision injected to verify the validator "
            "-> persistence -> audit -> live value chain"
        ),
    }
    if decision == "change":
        payload["changes"] = {"production_level": production_level or "normal"}

    client.table("agent_decisions").insert(
        {
            "scenario_id": scenario_id,
            "country_code": country,
            "action_type": "set_opec",
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


def test_change_decision_persisted(client, scenario_id):
    """Solaria submits change min → opec_production=min, opec_decision matches."""
    _seed_round_from_r0(client, scenario_id, 50)

    _insert_set_opec(
        client, scenario_id, 50, TEST_COUNTRY,
        decision="change",
        production_level="min",
        rationale="L2 test: Solaria cuts to min to push oil price toward 120 this round.",
    )

    resolve_round(SCENARIO_CODE, 50)

    row = _get_country_row(client, scenario_id, 50, TEST_COUNTRY)
    assert row.get("opec_production") == "min", (
        f"opec_production should be 'min', got {row.get('opec_production')}"
    )
    assert row.get("opec_decision") is not None, "opec_decision JSONB should be populated"
    audit = row["opec_decision"]
    assert audit["decision"] == "change"
    assert audit["changes"]["production_level"] == "min"
    print(f"\n  [test_change] opec_production={row['opec_production']}  audit={audit}")


def test_no_change_writes_audit_preserves_live_value(client, scenario_id):
    """no_change → audit JSONB written, opec_production unchanged (carry-forward)."""
    _seed_round_from_r0(client, scenario_id, 51)

    # Confirm starting state is 'normal' for Solaria (from R0 seed)
    pre = _get_country_row(client, scenario_id, 51, TEST_COUNTRY)
    assert pre.get("opec_production") == "normal"

    _insert_set_opec(
        client, scenario_id, 51, TEST_COUNTRY,
        decision="no_change",
        rationale="L2 test: current normal production still matches our fiscal strategy this round.",
    )

    resolve_round(SCENARIO_CODE, 51)

    row = _get_country_row(client, scenario_id, 51, TEST_COUNTRY)
    audit = row.get("opec_decision")
    assert audit is not None
    assert audit["decision"] == "no_change"
    assert "changes" not in audit
    # Live value unchanged
    assert row.get("opec_production") == "normal"
    print(f"\n  [test_no_change] audit={audit}  live={row['opec_production']}")


def test_invalid_decision_rejected_and_event_emitted(client, scenario_id):
    """Invalid payload (non-member Columbia) → opec_rejected event, no state change."""
    _seed_round_from_r0(client, scenario_id, 52)

    # Insert deliberately invalid decision (Columbia is NOT OPEC+)
    client.table("agent_decisions").insert(
        {
            "scenario_id": scenario_id,
            "country_code": "columbia",
            "action_type": "set_opec",
            "action_payload": {
                "action_type": "set_opec",
                "country_code": "columbia",
                "round_num": 52,
                "decision": "change",
                "rationale": "L2 test: Columbia tries to set OPEC level but is not a member.",
                "changes": {"production_level": "max"},
            },
            "rationale": "deliberate invalid non-member",
            "validation_status": "passed",
            "round_num": 52,
        }
    ).execute()

    resolve_round(SCENARIO_CODE, 52)

    # Columbia's opec_production should remain 'na' (from R0 post-migration)
    col = _get_country_row(client, scenario_id, 52, "columbia")
    assert col.get("opec_production") == "na", (
        f"Non-member opec_production should be 'na', got {col.get('opec_production')}"
    )
    assert col.get("opec_decision") is None, "Invalid decision must not write audit"

    # Rejection event logged
    rej = (
        client.table("observatory_events")
        .select("event_type, country_code, payload")
        .eq("scenario_id", scenario_id)
        .eq("round_num", 52)
        .eq("event_type", "opec_rejected")
        .execute()
    )
    rejections = rej.data or []
    assert any(r["country_code"] == "columbia" for r in rejections), (
        "Expected an opec_rejected event for columbia"
    )
    print(f"\n  [test_invalid] rejected events: {len(rejections)}  columbia unchanged")


def test_invalid_level_rejected(client, scenario_id):
    """Invalid production_level ('flood') → opec_rejected event, Solaria unchanged."""
    _seed_round_from_r0(client, scenario_id, 53)

    client.table("agent_decisions").insert(
        {
            "scenario_id": scenario_id,
            "country_code": TEST_COUNTRY,
            "action_type": "set_opec",
            "action_payload": {
                "action_type": "set_opec",
                "country_code": TEST_COUNTRY,
                "round_num": 53,
                "decision": "change",
                "rationale": "L2 test: deliberate invalid production_level to verify rejection path.",
                "changes": {"production_level": "flood"},
            },
            "rationale": "invalid level",
            "validation_status": "passed",
            "round_num": 53,
        }
    ).execute()

    resolve_round(SCENARIO_CODE, 53)

    row = _get_country_row(client, scenario_id, 53, TEST_COUNTRY)
    # Solaria should stay at its seeded value (normal)
    assert row.get("opec_production") == "normal"
    assert row.get("opec_decision") is None

    rej = (
        client.table("observatory_events")
        .select("event_type, country_code")
        .eq("scenario_id", scenario_id)
        .eq("round_num", 53)
        .eq("event_type", "opec_rejected")
        .execute()
    )
    assert any(r["country_code"] == TEST_COUNTRY for r in (rej.data or []))
    print(f"\n  [test_invalid_level] Solaria level stayed at 'normal'; event emitted")
