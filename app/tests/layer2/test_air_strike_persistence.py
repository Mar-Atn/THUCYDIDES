"""L2 — Air strike persistence (CONTRACT_AIR_STRIKES v1.0).

Scripted (no LLM) DB chain test:
  agent_decisions (attack_air payload)
    -> resolve_round (validates → canonical M3 fn → applies losses)
      -> observatory_combat_results row with per-shot list in attacker_rolls
         + modifier_breakdown JSONB
      -> unit_states_per_round losses
      -> country_states_per_round.attack_air_decision JSONB audit
      -> observatory_events row
"""

from __future__ import annotations

import logging

import pytest

from engine.round_engine.resolve_round import resolve_round
from engine.services.supabase import get_client
from tests._sim_run_helper import create_isolated_run

logger = logging.getLogger(__name__)

SCENARIO_CODE = "start_one"


@pytest.fixture
def client():
    return get_client()


@pytest.fixture
def isolated_run(client):
    sim_run_id, cleanup = create_isolated_run(
        scenario_code=SCENARIO_CODE,
        test_name="air_strike_persistence",
    )
    yield sim_run_id
    cleanup()


def _scenario_id(client) -> str:
    return client.table("sim_scenarios").select("id").eq("code", SCENARIO_CODE).limit(1).execute().data[0]["id"]


def _seed_round(client, sim_run_id: str, round_num: int) -> None:
    cs = client.table("country_states_per_round").select("*") \
        .eq("sim_run_id", sim_run_id).eq("round_num", 0).execute()
    if cs.data:
        rows = []
        for r in cs.data:
            new_row = {k: v for k, v in r.items() if k != "id"}
            new_row["round_num"] = round_num
            new_row["attack_air_decision"] = None
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


def _commit_air_strike(
    client, sim_run_id, scenario_id, round_num, country,
    src_rc, tgt_rc, attacker_codes, rationale="L2 air strike test: tactical strike on enemy concentration",
):
    payload = {
        "action_type": "attack_air",
        "country_code": country,
        "round_num": round_num,
        "decision": "change",
        "rationale": rationale,
        "changes": {
            "source_global_row": src_rc[0],
            "source_global_col": src_rc[1],
            "target_global_row": tgt_rc[0],
            "target_global_col": tgt_rc[1],
            "attacker_unit_codes": attacker_codes,
        },
    }
    client.table("agent_decisions").insert({
        "sim_run_id": sim_run_id,
        "scenario_id": scenario_id,
        "country_code": country,
        "action_type": "attack_air",
        "action_payload": payload,
        "rationale": rationale,
        "validation_status": "passed",
        "round_num": round_num,
    }).execute()


def _find_air_target_pair(client, sim_run_id, country: str):
    """Find a (source, target, attacker_codes) where the country has air units in
    range of an enemy hex with defenders.
    """
    res = client.table("unit_states_per_round").select(
        "unit_code,country_code,unit_type,status,global_row,global_col"
    ).eq("sim_run_id", sim_run_id).eq("round_num", 0).execute()
    units = res.data or []

    own_air = [u for u in units
               if u.get("country_code") == country
               and u.get("unit_type") == "tactical_air"
               and u.get("status") == "active"]
    by_hex: dict[tuple[int, int], list[dict]] = {}
    for u in own_air:
        by_hex.setdefault((u["global_row"], u["global_col"]), []).append(u)

    for (sr, sc), aus in sorted(by_hex.items()):
        for tr in range(max(1, sr - 2), min(10, sr + 2) + 1):
            for tc in range(max(1, sc - 2), min(20, sc + 2) + 1):
                if (tr, tc) == (sr, sc):
                    continue
                if abs(tr - sr) + abs(tc - sc) > 2:
                    continue
                enemies = [u for u in units
                           if u.get("global_row") == tr and u.get("global_col") == tc
                           and u.get("country_code") not in (None, country)
                           and u.get("status") == "active"]
                if enemies:
                    return (sr, sc), (tr, tc), [u["unit_code"] for u in aus[:2]]
    return None


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_air_strike_persisted_and_combat_row_written(client, isolated_run):
    sim_run_id = isolated_run
    scenario_id = _scenario_id(client)
    _seed_round(client, sim_run_id, 1)

    pair = _find_air_target_pair(client, sim_run_id, "cathay")
    if not pair:
        pytest.skip("No air → enemy pair in cathay seed data")
    src, tgt, codes = pair
    print(f"\n  [pair] cathay {src} → {tgt}, attackers={codes}")

    _commit_air_strike(client, sim_run_id, scenario_id, 1, "cathay", src, tgt, codes)
    resolve_round(sim_run_id, 1)

    combats = client.table("observatory_combat_results").select("*") \
        .eq("sim_run_id", sim_run_id).eq("round_num", 1) \
        .eq("combat_type", "air_strike").execute().data or []
    assert combats, "Expected at least 1 air_strike combat row"
    cb = combats[0]
    assert cb["attacker_country"] == "cathay"
    print(f"  [combat] losses ATK={len(cb['attacker_losses'])} DEF={len(cb['defender_losses'])}")
    print(f"  [shots] {len(cb['attacker_rolls'])} sortie records")

    # M3 shape: attacker_rolls is a LIST of dicts (one per shot)
    assert isinstance(cb["attacker_rolls"], list)
    if cb["attacker_rolls"]:
        first = cb["attacker_rolls"][0]
        assert isinstance(first, dict), f"M3 shot record must be dict, got {type(first)}"
        for k in ("attacker_code", "hit_probability", "hit_roll", "hit", "downed_probability", "downed_roll", "downed"):
            assert k in first, f"shot record missing key: {k}"

    # Defender rolls should be empty for air strikes
    assert cb["defender_rolls"] == []

    # Modifier breakdown column populated
    assert "modifier_breakdown" in cb
    assert isinstance(cb["modifier_breakdown"], list)

    # Audit JSONB
    row = client.table("country_states_per_round").select("attack_air_decision") \
        .eq("sim_run_id", sim_run_id).eq("round_num", 1).eq("country_code", "cathay") \
        .limit(1).execute().data[0]
    assert row["attack_air_decision"] is not None
    assert row["attack_air_decision"]["action_type"] == "attack_air"


def test_no_change_writes_no_combat(client, isolated_run):
    sim_run_id = isolated_run
    scenario_id = _scenario_id(client)
    _seed_round(client, sim_run_id, 1)

    payload = {
        "action_type": "attack_air",
        "country_code": "cathay",
        "round_num": 1,
        "decision": "no_change",
        "rationale": "Holding air assets in reserve - no high-value targets in range this round",
    }
    client.table("agent_decisions").insert({
        "sim_run_id": sim_run_id,
        "scenario_id": scenario_id,
        "country_code": "cathay",
        "action_type": "attack_air",
        "action_payload": payload,
        "rationale": payload["rationale"],
        "validation_status": "passed",
        "round_num": 1,
    }).execute()

    resolve_round(sim_run_id, 1)

    combats = client.table("observatory_combat_results").select("id") \
        .eq("sim_run_id", sim_run_id).eq("round_num", 1) \
        .eq("attacker_country", "cathay").eq("combat_type", "air_strike").execute().data or []
    assert not combats, f"Expected zero air_strike combats for no_change, got {len(combats)}"


def test_precomputed_rolls_engine_smoke():
    from engine.engines.military import resolve_air_strike
    attackers = [{"unit_code": "a1"}, {"unit_code": "a2"}, {"unit_code": "a3"}]
    defenders = [{"unit_code": "d1", "unit_type": "ground"}]
    result = resolve_air_strike(
        attackers, defenders,
        ad_units=[{"unit_code": "ad1", "unit_type": "air_defense", "status": "active"}],
        air_superiority_count=1,
        precomputed_rolls={"shots": [
            {"hit_roll": 0.01, "downed_roll": 0.99},  # hit + alive
            {"hit_roll": 0.99, "downed_roll": 0.01},  # miss + downed
            {"hit_roll": 0.05, "downed_roll": 0.50},  # hit + alive
        ]},
    )
    assert result.rolls_source == "moderator"
    assert len(result.shots) == 3
    # Shots 0 and 2 hit; shot 1 misses
    assert result.shots[0].hit is True
    assert result.shots[1].hit is False
    assert result.shots[2].hit is True
    # Shot 1 was downed
    assert "a2" in result.attacker_losses
    # Total hits → defender_losses
    assert len(result.defender_losses) == 1  # Only 1 defender, killed by first hit
