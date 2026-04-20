"""Layer 2 — Tariff persistence (CONTRACT_TARIFFS v1.0).

Step 4 of the tariff vertical slice. Verifies that scripted set_tariffs
decisions flow through resolve_round into:
  - the country_states_per_round.tariff_decision JSONB audit column
  - the tariffs state table (level upserts on change, untouched on no_change)

Uses rounds 70-73 to avoid collision with the budget e2e battery (74-78).

Run::

    cd app && PYTHONPATH=. python3 -m pytest tests/layer2/test_tariff_persistence.py -v -s
"""

from __future__ import annotations

import logging

import pytest

from engine.round_engine.resolve_round import resolve_round
from engine.services.supabase import get_client

logger = logging.getLogger(__name__)

SCENARIO_CODE = "start_one"
TEST_COUNTRY = "columbia"
TEST_ROUNDS = [70, 71, 72, 73]


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


def _cleanup(client, scenario_id: str) -> None:
    sim_run_id = _get_sim_run_id()
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
    # Clean any test-imposed tariffs (only the ones that look test-imposed)
    try:
        client.table("tariffs").delete().eq(
            "sim_run_id", sim_run_id
        ).eq("imposer_country_code", TEST_COUNTRY).like(
            "notes", "set_tariffs by %"
        ).execute()
    except Exception:
        pass


def _insert_set_tariffs(
    client,
    scenario_id: str,
    round_num: int,
    country: str,
    decision: str = "change",
    rationale: str | None = None,
    tariffs: dict | None = None,
) -> None:
    """Insert a set_tariffs (plural) decision into agent_decisions."""
    payload: dict = {
        "action_type": "set_tariffs",
        "country_code": country,
        "round_num": round_num,
        "decision": decision,
        "rationale": rationale or (
            "L2 test: scripted set_tariffs decision injected to verify the "
            "validator -> persistence -> audit -> state table chain"
        ),
    }
    if decision == "change":
        payload["changes"] = {"tariffs": tariffs or {}}

    client.table("agent_decisions").insert(
        {
            "scenario_id": scenario_id,
            "country_code": country,
            "action_type": "set_tariffs",
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


def _get_tariff_level(client, sim_run_id: str, imposer: str, target: str) -> int | None:
    res = (
        client.table("tariffs")
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


@pytest.fixture(autouse=True)
def _isolate(client, scenario_id):
    _cleanup(client, scenario_id)
    yield
    _cleanup(client, scenario_id)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_change_decision_persisted_and_state_upserted(client, scenario_id):
    """change with two targets → both upserted in tariffs table + audit JSONB."""
    sim_run_id = _get_sim_run_id()
    _seed_round_from_r0(client, scenario_id, 70)

    _insert_set_tariffs(
        client, scenario_id, 70, TEST_COUNTRY,
        decision="change",
        tariffs={"bharata": 2, "phrygia": 1},
        rationale="L2 test 1: change two targets, verify both upserted and audit persists",
    )

    resolve_round(SCENARIO_CODE, 70)

    row = _get_country_row(client, scenario_id, 70, TEST_COUNTRY)
    assert row.get("tariff_decision") is not None, "tariff_decision JSONB should be populated"
    audit = row["tariff_decision"]
    assert audit["decision"] == "change"
    assert audit["changes"]["tariffs"] == {"bharata": 2, "phrygia": 1}

    # State table updated for both targets
    assert _get_tariff_level(client, sim_run_id, TEST_COUNTRY, "bharata") == 2
    assert _get_tariff_level(client, sim_run_id, TEST_COUNTRY, "phrygia") == 1

    print(
        f"\n  [test_change_persisted] tariff_decision={audit}\n"
        f"  bharata level={_get_tariff_level(client, sim_run_id, TEST_COUNTRY, 'bharata')}\n"
        f"  phrygia level={_get_tariff_level(client, sim_run_id, TEST_COUNTRY, 'phrygia')}"
    )


def test_no_change_writes_audit_does_not_touch_state(client, scenario_id):
    """no_change → only audit JSONB written, tariffs state table untouched."""
    sim_run_id = _get_sim_run_id()
    _seed_round_from_r0(client, scenario_id, 71)

    # Establish a baseline existing tariff to ensure carry-forward
    client.table("tariffs").upsert({
        "sim_run_id": sim_run_id,
        "imposer_country_code": TEST_COUNTRY,
        "target_country_code": "bharata",
        "level": 2,
        "notes": "set_tariffs by columbia in round 0 (test baseline)",
    }, on_conflict="sim_run_id,imposer_country_code,target_country_code").execute()

    _insert_set_tariffs(
        client, scenario_id, 71, TEST_COUNTRY,
        decision="no_change",
        rationale="L2 test 2: no_change should write audit but leave tariffs table alone",
    )

    resolve_round(SCENARIO_CODE, 71)

    row = _get_country_row(client, scenario_id, 71, TEST_COUNTRY)
    audit = row.get("tariff_decision")
    assert audit is not None, "tariff_decision JSONB should be populated even for no_change"
    assert audit["decision"] == "no_change"
    assert "changes" not in audit

    # tariffs state table untouched — bharata still at level 2
    assert _get_tariff_level(client, sim_run_id, TEST_COUNTRY, "bharata") == 2

    print(
        f"\n  [test_no_change] audit={audit}\n"
        f"  bharata level (should be unchanged 2)={_get_tariff_level(client, sim_run_id, TEST_COUNTRY, 'bharata')}"
    )


def test_level_zero_lifts_target_in_state_table(client, scenario_id):
    """change with level=0 → tariffs row upserted to 0 (engine treats as lifted)."""
    sim_run_id = _get_sim_run_id()
    _seed_round_from_r0(client, scenario_id, 72)

    # Pre-existing tariff at level 2
    client.table("tariffs").upsert({
        "sim_run_id": sim_run_id,
        "imposer_country_code": TEST_COUNTRY,
        "target_country_code": "bharata",
        "level": 2,
        "notes": "set_tariffs by columbia in round 0 (test baseline for lift)",
    }, on_conflict="sim_run_id,imposer_country_code,target_country_code").execute()

    _insert_set_tariffs(
        client, scenario_id, 72, TEST_COUNTRY,
        decision="change",
        tariffs={"bharata": 0},
        rationale="L2 test 3: setting level=0 should lift the existing bharata tariff",
    )

    resolve_round(SCENARIO_CODE, 72)

    assert _get_tariff_level(client, sim_run_id, TEST_COUNTRY, "bharata") == 0

    row = _get_country_row(client, scenario_id, 72, TEST_COUNTRY)
    audit = row["tariff_decision"]
    assert audit["changes"]["tariffs"]["bharata"] == 0

    print(
        f"\n  [test_lift] bharata level after lift=0 (was 2): "
        f"{_get_tariff_level(client, sim_run_id, TEST_COUNTRY, 'bharata')}"
    )


def test_invalid_decision_rejected_and_event_emitted(client, scenario_id):
    """Invalid set_tariffs (level 5, self-tariff) → tariff_rejected event,
    no JSONB write, state table untouched."""
    sim_run_id = _get_sim_run_id()
    _seed_round_from_r0(client, scenario_id, 73)

    # Insert deliberately invalid payload directly (bypass validator)
    client.table("agent_decisions").insert(
        {
            "scenario_id": scenario_id,
            "country_code": TEST_COUNTRY,
            "action_type": "set_tariffs",
            "action_payload": {
                "action_type": "set_tariffs",
                "country_code": TEST_COUNTRY,
                "round_num": 73,
                "decision": "change",
                "rationale": (
                    "L2 test 4: deliberately invalid (level 5, self-tariff) "
                    "to verify rejection path"
                ),
                "changes": {"tariffs": {
                    "columbia": 2,   # SELF_TARIFF
                    "cathay": 5,     # INVALID_LEVEL
                }},
            },
            "rationale": "deliberate invalid",
            "validation_status": "passed",
            "round_num": 73,
        }
    ).execute()

    resolve_round(SCENARIO_CODE, 73)

    # tariff_decision should remain NULL
    row = _get_country_row(client, scenario_id, 73, TEST_COUNTRY)
    assert row.get("tariff_decision") is None, (
        f"Invalid decision should not have written tariff_decision; got {row.get('tariff_decision')}"
    )

    # Rejection event logged
    rej = (
        client.table("observatory_events")
        .select("event_type, country_code, payload")
        .eq("scenario_id", scenario_id)
        .eq("round_num", 73)
        .eq("event_type", "tariff_rejected")
        .execute()
    )
    rejections = rej.data or []
    assert any(r["country_code"] == TEST_COUNTRY for r in rejections), (
        "Expected at least one tariff_rejected event for columbia"
    )

    # tariffs state table not touched for cathay (level should remain whatever it was)
    cathay_lvl = _get_tariff_level(client, sim_run_id, TEST_COUNTRY, "cathay")
    print(
        f"\n  [test_invalid_rejected] tariff_rejected events: {len(rejections)}\n"
        f"  cathay level (should NOT be 5): {cathay_lvl}"
    )
    assert cathay_lvl != 5, "Invalid level 5 must not have leaked into the state table"
