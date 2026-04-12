"""L2 — Ground combat persistence (CONTRACT_GROUND_COMBAT v1.0).

Step 6 of the M2 vertical slice. Scripted (no LLM) DB chain test:

  agent_decisions (attack_ground v1.0 payload)
    -> resolve_round (validates → canonical pure dice → applies losses)
      -> observatory_combat_results row written with per-exchange dice
         + modifier_breakdown JSONB for the visualization
      -> unit_states_per_round losses applied
      -> country_states_per_round.attack_ground_decision JSONB audit
      -> observatory_events row

Uses an isolated sim_run via create_isolated_run so this test never
collides with other slice tests sharing the legacy run.
"""

from __future__ import annotations

import logging

import pytest

from engine.round_engine.resolve_round import resolve_round
from engine.services.supabase import get_client
from tests._sim_run_helper import create_isolated_run

logger = logging.getLogger(__name__)

SCENARIO_CODE = "start_one"
TEST_TAG = "GROUND_COMBAT_L2"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client():
    return get_client()


@pytest.fixture
def isolated_run(client):
    """Fresh sim_run with R0 seeded from the legacy template."""
    sim_run_id, cleanup = create_isolated_run(
        scenario_code=SCENARIO_CODE,
        test_name="ground_combat_persistence",
    )
    yield sim_run_id
    cleanup()


def _scenario_id(client) -> str:
    return client.table("sim_scenarios").select("id").eq("code", SCENARIO_CODE).limit(1).execute().data[0]["id"]


def _commit_attack(
    client, sim_run_id: str, scenario_id: str, round_num: int,
    country: str, source_rc: tuple[int, int], target_rc: tuple[int, int],
    attacker_codes: list[str], allow_chain: bool = True,
    rationale: str = "L2 test scripted attack: punishing the enemy salient with overwhelming force",
) -> None:
    payload = {
        "action_type": "attack_ground",
        "country_code": country,
        "round_num": round_num,
        "decision": "change",
        "rationale": rationale,
        "changes": {
            "source_global_row": source_rc[0],
            "source_global_col": source_rc[1],
            "target_global_row": target_rc[0],
            "target_global_col": target_rc[1],
            "attacker_unit_codes": attacker_codes,
            "allow_chain": allow_chain,
        },
    }
    client.table("agent_decisions").insert({
        "sim_run_id": sim_run_id,
        "scenario_id": scenario_id,
        "country_code": country,
        "action_type": "attack_ground",
        "action_payload": payload,
        "rationale": rationale,
        "validation_status": "passed",
        "round_num": round_num,
    }).execute()


def _seed_round(client, sim_run_id: str, scenario_id: str, round_num: int) -> None:
    """Clone R0 country + unit states into round_num so resolve_round has prior state."""
    cs = client.table("country_states_per_round").select("*") \
        .eq("sim_run_id", sim_run_id).eq("round_num", 0).execute()
    if cs.data:
        rows = []
        for r in cs.data:
            new_row = {k: v for k, v in r.items() if k != "id"}
            new_row["round_num"] = round_num
            new_row["attack_ground_decision"] = None
            rows.append(new_row)
        if rows:
            client.table("country_states_per_round").upsert(
                rows, on_conflict="sim_run_id,round_num,country_code"
            ).execute()
    us = client.table("unit_states_per_round").select("*") \
        .eq("sim_run_id", sim_run_id).eq("round_num", 0).execute()
    if us.data:
        rows = [{k: v for k, v in r.items() if k != "id"} for r in us.data]
        for r in rows:
            r["round_num"] = round_num
        for i in range(0, len(rows), 200):
            client.table("unit_states_per_round").upsert(
                rows[i:i+200], on_conflict="sim_run_id,round_num,unit_code"
            ).execute()


def _find_adjacent_enemy_pair(client, sim_run_id: str, country: str) -> tuple[tuple[int, int], tuple[int, int], list[str]] | None:
    """Find the first (source, target, attacker_codes) tuple where ``country`` has
    ground units adjacent to an enemy hex with ground defenders.
    """
    res = client.table("unit_states_per_round").select(
        "unit_code,country_code,unit_type,status,global_row,global_col"
    ).eq("sim_run_id", sim_run_id).eq("round_num", 0).execute()
    units = res.data or []

    own_grounds = [u for u in units
                   if u.get("country_code") == country
                   and u.get("unit_type") == "ground"
                   and u.get("status") == "active"]
    by_hex: dict[tuple[int, int], list[dict]] = {}
    for u in own_grounds:
        by_hex.setdefault((u["global_row"], u["global_col"]), []).append(u)

    for (sr, sc), us in sorted(by_hex.items()):
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = sr + dr, sc + dc
            if not (1 <= nr <= 10 and 1 <= nc <= 20):
                continue
            enemies = [u for u in units
                       if u.get("global_row") == nr and u.get("global_col") == nc
                       and u.get("country_code") not in (None, country)
                       and u.get("status") == "active"
                       and u.get("unit_type") == "ground"]
            if enemies:
                return (sr, sc), (nr, nc), [u["unit_code"] for u in us[:2]]
    return None


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_ground_attack_persisted_and_combat_row_written(client, isolated_run):
    """change → resolve_round → audit JSONB + observatory_combat_results row + losses applied."""
    sim_run_id = isolated_run
    scenario_id = _scenario_id(client)

    # Need to seed R1 from R0 so resolve_round can fall back
    _seed_round(client, sim_run_id, scenario_id, 1)

    # Find a real attacker→defender pair from the seed map
    pair = _find_adjacent_enemy_pair(client, sim_run_id, "cathay")
    if not pair:
        pytest.skip("No adjacent cathay→enemy ground pair in seed data")
    src, tgt, codes = pair
    print(f"\n  [pair] cathay {src} → {tgt}, attackers={codes}")

    _commit_attack(client, sim_run_id, scenario_id, 1, "cathay", src, tgt, codes,
                   allow_chain=False)
    resolve_round(sim_run_id, 1)

    # 1. Combat row exists
    combats = client.table("observatory_combat_results").select("*") \
        .eq("sim_run_id", sim_run_id).eq("round_num", 1).execute().data or []
    assert combats, "Expected at least 1 combat row in observatory_combat_results"
    cb = combats[0]
    assert cb["combat_type"] == "ground"
    assert cb["attacker_country"] == "cathay"
    assert (cb["location_global_row"], cb["location_global_col"]) == tgt
    print(f"  [combat] {cb['attacker_country']}→{cb['defender_country']} losses=ATK{len(cb['attacker_losses'])}/DEF{len(cb['defender_losses'])}")
    print(f"  [rolls] ATK={cb['attacker_rolls']} DEF={cb['defender_rolls']}")

    # 2. Per-exchange dice are list-of-lists (M2 enrichment)
    assert isinstance(cb["attacker_rolls"], list), "attacker_rolls must be a list"
    if cb["attacker_rolls"]:
        assert isinstance(cb["attacker_rolls"][0], list), \
            "attacker_rolls[0] must be a list (per-exchange), not flat"

    # 3. modifier_breakdown column exists and is a list
    assert "modifier_breakdown" in cb
    assert isinstance(cb["modifier_breakdown"], list)

    # 4. Audit JSONB on country_states_per_round
    row = client.table("country_states_per_round").select("attack_ground_decision") \
        .eq("sim_run_id", sim_run_id).eq("round_num", 1).eq("country_code", "cathay") \
        .limit(1).execute().data[0]
    assert row["attack_ground_decision"] is not None
    assert row["attack_ground_decision"]["action_type"] == "attack_ground"
    assert row["attack_ground_decision"]["changes"]["target_global_row"] == tgt[0]


def test_no_change_writes_no_combat(client, isolated_run):
    """no_change decision skips combat entirely."""
    sim_run_id = isolated_run
    scenario_id = _scenario_id(client)
    _seed_round(client, sim_run_id, scenario_id, 1)

    payload = {
        "action_type": "attack_ground",
        "country_code": "cathay",
        "round_num": 1,
        "decision": "no_change",
        "rationale": "Holding the line - not initiating ground combat this round",
    }
    client.table("agent_decisions").insert({
        "sim_run_id": sim_run_id,
        "scenario_id": scenario_id,
        "country_code": "cathay",
        "action_type": "attack_ground",
        "action_payload": payload,
        "rationale": payload["rationale"],
        "validation_status": "passed",
        "round_num": 1,
    }).execute()

    resolve_round(sim_run_id, 1)

    combats = client.table("observatory_combat_results").select("*") \
        .eq("sim_run_id", sim_run_id).eq("round_num", 1) \
        .eq("attacker_country", "cathay").execute().data or []
    assert not combats, f"Expected zero combats for no_change, got {len(combats)}"


def test_precomputed_rolls_engine_smoke(client):
    """Direct engine smoke test of the precomputed_rolls hook."""
    from engine.engines.military import resolve_ground_combat
    attackers = [{"unit_code": "a1"}, {"unit_code": "a2"}, {"unit_code": "a3"}]
    defenders = [{"unit_code": "d1"}, {"unit_code": "d2"}]
    # All attacker dice are 6, all defender dice are 1 → attacker should annihilate
    result = resolve_ground_combat(
        attackers, defenders, modifiers=[],
        precomputed_rolls={"attacker": [[6, 6, 6]], "defender": [[1, 1]]},
    )
    assert result.success is True
    assert len(result.attacker_losses) == 0
    assert len(result.defender_losses) == 2
    assert result.rolls_source == "moderator"
    assert result.attacker_rolls == [[6, 6, 6]]
    assert result.defender_rolls == [[1, 1]]


def test_modifier_breakdown_passed_through(client):
    """Engine accepts modifier list and echoes it in the result."""
    from engine.engines.military import resolve_ground_combat
    mods = [
        {"side": "defender", "value": 1, "reason": "die_hard terrain"},
        {"side": "defender", "value": 1, "reason": "air_support: per_a_01"},
        {"side": "attacker", "value": -1, "reason": "amphibious assault"},
    ]
    result = resolve_ground_combat(
        attackers=[{"unit_code": "a1"}, {"unit_code": "a2"}],
        defenders=[{"unit_code": "d1"}],
        modifiers=mods,
        precomputed_rolls={"attacker": [[3, 2]], "defender": [[3]]},
    )
    assert result.summed_attacker_bonus == -1
    assert result.summed_defender_bonus == 2
    assert len(result.modifier_breakdown) == 3
    reasons = [m.reason for m in result.modifier_breakdown]
    assert "die_hard terrain" in reasons
    assert "amphibious assault" in reasons
