"""Layer 2 — Sanctions persistence (CONTRACT_SANCTIONS v1.0).

Step 4 of the sanctions vertical slice. Verifies that scripted set_sanctions
decisions flow through resolve_round into:
  - the country_states_per_round.sanction_decision JSONB audit column
  - the sanctions state table (signed-level upserts on change, untouched on
    no_change, rejection path for invalid payloads)

Uses rounds 65-68 to avoid collision with tariff context (60-63), tariff
persistence (70-73), budget e2e (74-78), budget full chain AI (83-84),
tariff full chain AI (85-86).

Run::

    cd app && PYTHONPATH=. python3 -m pytest tests/layer2/test_sanction_persistence.py -v -s
"""

from __future__ import annotations

import logging

import pytest

from engine.round_engine.resolve_round import resolve_round
from engine.services.supabase import get_client

logger = logging.getLogger(__name__)

SCENARIO_CODE = "start_one"
TEST_COUNTRY = "columbia"
TEST_ROUNDS = [65, 66, 67, 68]
# Targets used by this test — cleanup is limited to these to preserve the
# canonical starting-state rows for other targets.
TEST_TARGETS = ("bharata", "phrygia", "yamato", "levantia")


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
    # Clean sanctions rows for test targets ONLY (preserve canonical starting
    # state for other pairs).
    for target in TEST_TARGETS:
        try:
            client.table("sanctions").delete().eq(
                "sim_run_id", sim_run_id
            ).eq("imposer_country_code", TEST_COUNTRY).eq(
                "target_country_code", target
            ).execute()
        except Exception:
            pass


def _insert_set_sanctions(
    client,
    scenario_id: str,
    round_num: int,
    country: str,
    decision: str = "change",
    rationale: str | None = None,
    sanctions: dict | None = None,
) -> None:
    """Insert a set_sanctions decision into agent_decisions."""
    payload: dict = {
        "action_type": "set_sanctions",
        "country_code": country,
        "round_num": round_num,
        "decision": decision,
        "rationale": rationale or (
            "L2 test: scripted set_sanctions decision injected to verify the "
            "validator -> persistence -> audit -> state table chain"
        ),
    }
    if decision == "change":
        payload["changes"] = {"sanctions": sanctions or {}}

    client.table("agent_decisions").insert(
        {
            "scenario_id": scenario_id,
            "country_code": country,
            "action_type": "set_sanctions",
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


def _get_sanction_level(
    client, sim_run_id: str, imposer: str, target: str
) -> int | None:
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


@pytest.fixture(autouse=True)
def _isolate(client, scenario_id):
    _cleanup(client, scenario_id)
    yield
    _cleanup(client, scenario_id)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_change_decision_persisted_and_state_upserted(client, scenario_id):
    """change with two targets → both upserted in sanctions table + audit JSONB."""
    sim_run_id = _get_sim_run_id()
    _seed_round_from_r0(client, scenario_id, 65)

    _insert_set_sanctions(
        client, scenario_id, 65, TEST_COUNTRY,
        decision="change",
        sanctions={"bharata": 2, "phrygia": 1},
        rationale="L2 test 1: change two targets, verify both upserted and audit persists",
    )

    resolve_round(SCENARIO_CODE, 65)

    row = _get_country_row(client, scenario_id, 65, TEST_COUNTRY)
    assert row.get("sanction_decision") is not None, (
        "sanction_decision JSONB should be populated"
    )
    audit = row["sanction_decision"]
    assert audit["decision"] == "change"
    assert audit["changes"]["sanctions"] == {"bharata": 2, "phrygia": 1}

    # State table updated for both targets
    assert _get_sanction_level(client, sim_run_id, TEST_COUNTRY, "bharata") == 2
    assert _get_sanction_level(client, sim_run_id, TEST_COUNTRY, "phrygia") == 1

    print(
        f"\n  [test_change_persisted] sanction_decision={audit}\n"
        f"  bharata level={_get_sanction_level(client, sim_run_id, TEST_COUNTRY, 'bharata')}\n"
        f"  phrygia level={_get_sanction_level(client, sim_run_id, TEST_COUNTRY, 'phrygia')}"
    )


def test_no_change_writes_audit_does_not_touch_state(client, scenario_id):
    """no_change → only audit JSONB written, sanctions state table untouched."""
    sim_run_id = _get_sim_run_id()
    _seed_round_from_r0(client, scenario_id, 66)

    # Establish a baseline existing sanction to ensure carry-forward
    client.table("sanctions").upsert({
        "sim_run_id": sim_run_id,
        "imposer_country_code": TEST_COUNTRY,
        "target_country_code": "bharata",
        "level": 2,
        "notes": "",
    }, on_conflict="sim_run_id,imposer_country_code,target_country_code").execute()

    _insert_set_sanctions(
        client, scenario_id, 66, TEST_COUNTRY,
        decision="no_change",
        rationale="L2 test 2: no_change should write audit but leave sanctions table alone",
    )

    resolve_round(SCENARIO_CODE, 66)

    row = _get_country_row(client, scenario_id, 66, TEST_COUNTRY)
    audit = row.get("sanction_decision")
    assert audit is not None, (
        "sanction_decision JSONB should be populated even for no_change"
    )
    assert audit["decision"] == "no_change"
    assert "changes" not in audit

    # sanctions state table untouched — bharata still at level 2
    assert _get_sanction_level(client, sim_run_id, TEST_COUNTRY, "bharata") == 2

    print(
        f"\n  [test_no_change] audit={audit}\n"
        f"  bharata level (should be unchanged 2)="
        f"{_get_sanction_level(client, sim_run_id, TEST_COUNTRY, 'bharata')}"
    )


def test_negative_level_evasion_support_persists(client, scenario_id):
    """change with L=-2 (evasion support) → stored as signed negative level."""
    sim_run_id = _get_sim_run_id()
    _seed_round_from_r0(client, scenario_id, 67)

    _insert_set_sanctions(
        client, scenario_id, 67, TEST_COUNTRY,
        decision="change",
        sanctions={"yamato": -2},
        rationale=(
            "L2 test 3: negative level evasion support must persist to the "
            "sanctions state table as a signed integer per CONTRACT_SANCTIONS v1.0"
        ),
    )

    resolve_round(SCENARIO_CODE, 67)

    assert _get_sanction_level(client, sim_run_id, TEST_COUNTRY, "yamato") == -2

    row = _get_country_row(client, scenario_id, 67, TEST_COUNTRY)
    audit = row["sanction_decision"]
    assert audit["changes"]["sanctions"]["yamato"] == -2

    print(
        f"\n  [test_negative_evasion] yamato level (should be -2): "
        f"{_get_sanction_level(client, sim_run_id, TEST_COUNTRY, 'yamato')}\n"
        f"  audit={audit}"
    )


def test_invalid_decision_rejected_and_event_emitted(client, scenario_id):
    """Invalid set_sanctions (self-sanction + out-of-range) → sanction_rejected
    event, no JSONB write, state table untouched."""
    sim_run_id = _get_sim_run_id()
    _seed_round_from_r0(client, scenario_id, 68)

    # Insert deliberately invalid payload directly (bypass validator at
    # insert time; the resolve handler should reject it)
    client.table("agent_decisions").insert(
        {
            "scenario_id": scenario_id,
            "country_code": TEST_COUNTRY,
            "action_type": "set_sanctions",
            "action_payload": {
                "action_type": "set_sanctions",
                "country_code": TEST_COUNTRY,
                "round_num": 68,
                "decision": "change",
                "rationale": (
                    "L2 test 4: deliberately invalid (self-sanction + out-of-range) "
                    "to verify rejection path"
                ),
                "changes": {"sanctions": {
                    TEST_COUNTRY: 2,   # SELF_SANCTION
                    "levantia": 7,     # INVALID_LEVEL (out of [-3, +3])
                }},
            },
            "rationale": "deliberate invalid",
            "validation_status": "passed",
            "round_num": 68,
        }
    ).execute()

    resolve_round(SCENARIO_CODE, 68)

    # sanction_decision should remain NULL
    row = _get_country_row(client, scenario_id, 68, TEST_COUNTRY)
    assert row.get("sanction_decision") is None, (
        f"Invalid decision should not have written sanction_decision; "
        f"got {row.get('sanction_decision')}"
    )

    # Rejection event logged
    rej = (
        client.table("observatory_events")
        .select("event_type, country_code, payload")
        .eq("scenario_id", scenario_id)
        .eq("round_num", 68)
        .eq("event_type", "sanction_rejected")
        .execute()
    )
    rejections = rej.data or []
    assert any(r["country_code"] == TEST_COUNTRY for r in rejections), (
        "Expected at least one sanction_rejected event for columbia"
    )

    # sanctions state table not touched for levantia (level must NOT be 7)
    levantia_lvl = _get_sanction_level(
        client, sim_run_id, TEST_COUNTRY, "levantia"
    )
    print(
        f"\n  [test_invalid_rejected] sanction_rejected events: {len(rejections)}\n"
        f"  levantia level (must NOT be 7): {levantia_lvl}"
    )
    assert levantia_lvl != 7, (
        "Invalid level 7 must not have leaked into the state table"
    )
