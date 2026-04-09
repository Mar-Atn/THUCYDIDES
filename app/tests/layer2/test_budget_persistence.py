"""Layer 2 — Budget persistence vertical slice (CONTRACT_BUDGET v1.1).

End-to-end persistence flow:
  agent_decisions (set_budget v1.1 payload)
    -> resolve_round (validates + writes country_states_per_round columns)
    -> snapshot stores budget_social_pct / budget_production / budget_research
    -> round_tick loads new schema and feeds the economic engine.

Uses rounds 80-82 to avoid conflicts with battery test (90-91) and live runs.

Run::

    cd app && PYTHONPATH=. python3 -m pytest tests/layer2/test_budget_persistence.py -v -s
"""

from __future__ import annotations

import logging

import pytest

from engine.round_engine.resolve_round import resolve_round
from engine.services.supabase import get_client

logger = logging.getLogger(__name__)

SCENARIO_CODE = "start_one"
TEST_COUNTRY = "columbia"
TEST_TAG = "BUDGET_PERSIST_L2"
TEST_ROUNDS = [79, 80, 81, 82]


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


def _seed_baseline_round(client, scenario_id: str, round_num: int) -> None:
    """Clone country_states_per_round + global_state_per_round from R0 → round_num."""
    r0 = (
        client.table("country_states_per_round")
        .select("*")
        .eq("scenario_id", scenario_id)
        .eq("round_num", 0)
        .execute()
    )
    if not r0.data:
        return
    rows = []
    for row in r0.data:
        new_row = {k: v for k, v in row.items() if k != "id"}
        new_row["round_num"] = round_num
        rows.append(new_row)
    if rows:
        client.table("country_states_per_round").insert(rows).execute()


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


def _insert_decision(
    client, scenario_id: str, round_num: int, country: str, payload: dict
) -> None:
    payload = dict(payload)
    payload["test_tag"] = TEST_TAG
    client.table("agent_decisions").insert(
        {
            "scenario_id": scenario_id,
            "country_code": country,
            "action_type": "set_budget",
            "action_payload": payload,
            "rationale": payload.get("rationale", "test"),
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
    assert res.data, f"No country_states row for {country} R{round_num}"
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
    """Clean test rounds before and after every test."""
    _cleanup(client, scenario_id)
    yield
    _cleanup(client, scenario_id)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_budget_decision_persisted_and_read(client, scenario_id):
    """A 'change' decision flows through resolve_round and lands in the new columns."""
    # Seed previous round (79) so resolve_round can fall back when loading state
    _seed_baseline_round(client, scenario_id, 79)

    payload = {
        "action_type": "set_budget",
        "country_code": TEST_COUNTRY,
        "round_num": 80,
        "decision": "change",
        "rationale": (
            "Persistence test: Columbia raises social spending and starts "
            "ground production with light AI research."
        ),
        "changes": {
            "social_pct": 0.8,
            "production": {
                "ground": 2,
                "naval": 0,
                "tactical_air": 0,
                "strategic_missile": 0,
                "air_defense": 0,
            },
            "research": {"nuclear_coins": 3, "ai_coins": 0},
        },
    }
    _insert_decision(client, scenario_id, 80, TEST_COUNTRY, payload)

    result = resolve_round(SCENARIO_CODE, 80)
    print(f"  resolve_round(R80): {result}")

    row = _get_country_row(client, scenario_id, 80, TEST_COUNTRY)
    print(
        f"  Columbia R80 budget cols: social={row.get('budget_social_pct')} "
        f"production={row.get('budget_production')} "
        f"research={row.get('budget_research')}"
    )

    assert float(row["budget_social_pct"]) == pytest.approx(0.8)
    assert row["budget_production"] == {
        "ground": 2,
        "naval": 0,
        "tactical_air": 0,
        "strategic_missile": 0,
        "air_defense": 0,
    }
    assert row["budget_research"] == {"nuclear_coins": 3, "ai_coins": 0}


def test_budget_no_change_carries_forward(client, scenario_id):
    """A 'no_change' decision in R81 preserves R80's explicit budget into R81."""
    # Seed R79 baseline (so R80 can resolve from a previous round)
    _seed_baseline_round(client, scenario_id, 79)

    # R80: explicit change to known values
    r80_payload = {
        "action_type": "set_budget",
        "country_code": TEST_COUNTRY,
        "round_num": 80,
        "decision": "change",
        "rationale": "Persistence test: set explicit baseline budget for carry-forward test",
        "changes": {
            "social_pct": 1.2,
            "production": {
                "ground": 1,
                "naval": 1,
                "tactical_air": 0,
                "strategic_missile": 0,
                "air_defense": 0,
            },
            "research": {"nuclear_coins": 0, "ai_coins": 4},
        },
    }
    _insert_decision(client, scenario_id, 80, TEST_COUNTRY, r80_payload)
    resolve_round(SCENARIO_CODE, 80)

    r80_row = _get_country_row(client, scenario_id, 80, TEST_COUNTRY)
    assert float(r80_row["budget_social_pct"]) == pytest.approx(1.2)

    # R81: no_change
    r81_payload = {
        "action_type": "set_budget",
        "country_code": TEST_COUNTRY,
        "round_num": 81,
        "decision": "no_change",
        "rationale": "Persistence test: maintaining the previous round's allocation",
    }
    _insert_decision(client, scenario_id, 81, TEST_COUNTRY, r81_payload)
    resolve_round(SCENARIO_CODE, 81)

    r81_row = _get_country_row(client, scenario_id, 81, TEST_COUNTRY)
    print(
        f"  Columbia R81 (no_change) social={r81_row.get('budget_social_pct')} "
        f"production={r81_row.get('budget_production')} "
        f"research={r81_row.get('budget_research')}"
    )

    assert float(r81_row["budget_social_pct"]) == pytest.approx(1.2)
    assert r81_row["budget_production"] == {
        "ground": 1,
        "naval": 1,
        "tactical_air": 0,
        "strategic_missile": 0,
        "air_defense": 0,
    }
    assert r81_row["budget_research"] == {"nuclear_coins": 0, "ai_coins": 4}


def test_invalid_budget_rejected(client, scenario_id):
    """An out-of-range social_pct is rejected and surfaces a budget_rejected event."""
    _seed_baseline_round(client, scenario_id, 79)

    bad_payload = {
        "action_type": "set_budget",
        "country_code": TEST_COUNTRY,
        "round_num": 80,
        "decision": "change",
        "rationale": "Persistence test: deliberately invalid social_pct above max",
        "changes": {
            "social_pct": 2.5,  # out of [0.5, 1.5]
            "production": {
                "ground": 0,
                "naval": 0,
                "tactical_air": 0,
                "strategic_missile": 0,
                "air_defense": 0,
            },
            "research": {"nuclear_coins": 0, "ai_coins": 0},
        },
    }
    _insert_decision(client, scenario_id, 80, TEST_COUNTRY, bad_payload)
    resolve_round(SCENARIO_CODE, 80)

    # Verify a rejection event was logged
    res = (
        client.table("observatory_events")
        .select("event_type, country_code, payload")
        .eq("scenario_id", scenario_id)
        .eq("round_num", 80)
        .eq("event_type", "budget_rejected")
        .execute()
    )
    rejections = res.data or []
    print(f"  budget_rejected events: {len(rejections)}")
    assert len(rejections) >= 1, "Expected at least one budget_rejected event"
    assert any(r["country_code"] == TEST_COUNTRY for r in rejections)

    # Country snapshot should NOT carry the bogus social_pct
    row = _get_country_row(client, scenario_id, 80, TEST_COUNTRY)
    social = row.get("budget_social_pct")
    if social is not None:
        assert float(social) <= 1.5, (
            f"Invalid social_pct leaked into snapshot: {social}"
        )
