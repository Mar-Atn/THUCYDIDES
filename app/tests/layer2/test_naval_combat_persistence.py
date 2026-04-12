"""L2 — Naval combat persistence (CONTRACT_NAVAL_COMBAT v1.0)."""

from __future__ import annotations
import pytest
from engine.round_engine.resolve_round import resolve_round
from engine.services.supabase import get_client
from tests._sim_run_helper import create_isolated_run

SCENARIO_CODE = "start_one"


@pytest.fixture
def client():
    return get_client()


@pytest.fixture
def isolated_run(client):
    sim_run_id, cleanup = create_isolated_run(scenario_code=SCENARIO_CODE, test_name="naval_combat")
    yield sim_run_id
    cleanup()


def _scenario_id(client):
    return client.table("sim_scenarios").select("id").eq("code", SCENARIO_CODE).limit(1).execute().data[0]["id"]


def _seed_round(client, sim_run_id, round_num):
    cs = client.table("country_states_per_round").select("*").eq("sim_run_id", sim_run_id).eq("round_num", 0).execute()
    if cs.data:
        rows = [{k: v for k, v in r.items() if k != "id"} for r in cs.data]
        for r in rows: r["round_num"] = round_num; r["attack_naval_decision"] = None
        client.table("country_states_per_round").upsert(rows, on_conflict="sim_run_id,round_num,country_code").execute()
    us = client.table("unit_states_per_round").select("*").eq("sim_run_id", sim_run_id).eq("round_num", 0).execute()
    if us.data:
        rows = [{k: v for k, v in r.items() if k != "id"} for r in us.data]
        for r in rows: r["round_num"] = round_num
        for i in range(0, len(rows), 200):
            client.table("unit_states_per_round").upsert(rows[i:i+200], on_conflict="sim_run_id,round_num,unit_code").execute()


def _find_naval_pair(client, sim_run_id, country):
    """Find (attacker_code, target_code) where country has a naval adjacent to an enemy naval."""
    res = client.table("unit_states_per_round").select(
        "unit_code,country_code,unit_type,status,global_row,global_col"
    ).eq("sim_run_id", sim_run_id).eq("round_num", 0).execute()
    units = res.data or []
    own = [u for u in units if u["country_code"] == country and u["unit_type"] == "naval" and u["status"] == "active"]
    for u in own:
        r, c = u["global_row"], u["global_col"]
        if r is None: continue
        for e in units:
            if e["country_code"] == country or e["unit_type"] != "naval" or e["status"] != "active": continue
            er, ec = e.get("global_row"), e.get("global_col")
            if er is None: continue
            if abs(r - er) + abs(c - ec) <= 1:
                return u["unit_code"], e["unit_code"]
    return None


def test_naval_combat_persisted(client, isolated_run):
    sim_run_id = isolated_run
    scenario_id = _scenario_id(client)
    _seed_round(client, sim_run_id, 1)

    pair = _find_naval_pair(client, sim_run_id, "columbia")
    if not pair:
        pytest.skip("No adjacent columbia/enemy naval pair in seed data")
    atk, tgt = pair
    print(f"\n  [pair] columbia {atk} vs {tgt}")

    payload = {
        "action_type": "attack_naval",
        "country_code": "columbia",
        "round_num": 1,
        "decision": "change",
        "rationale": "L2 test: engaging enemy naval at adjacent hex to control the seaway",
        "changes": {"attacker_unit_code": atk, "target_unit_code": tgt},
    }
    client.table("agent_decisions").insert({
        "sim_run_id": sim_run_id,
        "scenario_id": scenario_id,
        "country_code": "columbia",
        "action_type": "attack_naval",
        "action_payload": payload,
        "rationale": payload["rationale"],
        "validation_status": "passed",
        "round_num": 1,
    }).execute()

    resolve_round(sim_run_id, 1)

    combats = client.table("observatory_combat_results").select("*") \
        .eq("sim_run_id", sim_run_id).eq("round_num", 1).eq("combat_type", "naval").execute().data or []
    assert combats, "Expected naval combat row"
    cb = combats[0]
    print(f"  [combat] rolls ATK={cb['attacker_rolls']} DEF={cb['defender_rolls']}")
    print(f"  [narrative] {cb['narrative']}")

    # M4 shape: attacker_rolls is a list of {roll, modified} dicts
    assert isinstance(cb["attacker_rolls"], list)
    if cb["attacker_rolls"]:
        assert isinstance(cb["attacker_rolls"][0], dict)
        assert "roll" in cb["attacker_rolls"][0]

    assert isinstance(cb["modifier_breakdown"], list)

    # Audit JSONB
    row = client.table("country_states_per_round").select("attack_naval_decision") \
        .eq("sim_run_id", sim_run_id).eq("round_num", 1).eq("country_code", "columbia") \
        .limit(1).execute().data[0]
    assert row["attack_naval_decision"] is not None


def test_precomputed_rolls_engine():
    from engine.engines.military import resolve_naval_combat
    r = resolve_naval_combat(
        {"unit_code": "a1"}, {"unit_code": "d1"},
        modifiers=[{"side": "attacker", "value": 1, "reason": "ai_l4"}],
        precomputed_rolls={"attacker": 4, "defender": 5},
    )
    # ATK 4+1=5, DEF 5 → tie → defender wins
    assert r.winner == "defender"
    assert r.destroyed_unit == "a1"
    assert r.attacker_modified == 5
    assert r.defender_modified == 5
    assert r.rolls_source == "moderator"

    r2 = resolve_naval_combat(
        {"unit_code": "a1"}, {"unit_code": "d1"},
        precomputed_rolls={"attacker": 6, "defender": 5},
    )
    assert r2.winner == "attacker"
    assert r2.destroyed_unit == "d1"
