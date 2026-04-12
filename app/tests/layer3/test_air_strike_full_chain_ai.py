"""L3 — Air strike ACCEPTANCE GATE (CONTRACT_AIR_STRIKES v1.0).

End-to-end M3 proof:
  build_air_strike_context (live)
    -> compact prompt
      -> Gemini Flash AI decision
        -> validate_air_strike (production validator)
          -> agent_decisions row
            -> resolve_round (canonical M3 air engine)
              -> observatory_combat_results row (per-shot list)
              -> attack_air_decision audit JSONB
              -> finalize_run as visible_for_review

Run is left in DB for visual review.
"""

from __future__ import annotations

import asyncio
import logging

import pytest

from engine.agents.decisions import _parse_json
from engine.round_engine.resolve_round import resolve_round
from engine.services.air_strike_validator import validate_air_strike
from engine.services.combat_context import build_air_strike_context
from engine.services.sim_run_manager import (
    create_run,
    finalize_run,
    seed_round_zero,
)
from engine.services.supabase import get_client
from tests.layer3.test_skill_movement import _call_llm

logger = logging.getLogger(__name__)

SCENARIO_CODE = "start_one"
TEST_COUNTRY = "cathay"
RUN_NAME = "M3-VIS · AI air strike acceptance gate"

SYSTEM_AIR_STRIKE = (
    "You are an AI head of state reviewing tactical air strike "
    "opportunities per CONTRACT_AIR_STRIKES v1.0. Return ONLY JSON "
    "matching the attack_air schema. Rationale >= 30 chars mandatory. "
    "On no_change: OMIT the changes field entirely. "
    "On change: pick exactly ONE source/target pair within 2 hexes."
)


def _build_prompt(country_code: str, round_num: int, ctx: dict) -> str:
    eco = ctx.get("economic_state", {})

    forces_lines = []
    for hex_key, units in (ctx.get("my_air_forces_by_hex") or {}).items():
        forces_lines.append(f"  hex ({hex_key}) — {len(units)} tactical_air units:")
        for u in units[:6]:
            forces_lines.append(f"    {u['unit_code']}")
    forces_block = "\n".join(forces_lines) or "  (no air forces)"

    targets_lines = []
    for t in (ctx.get("targetable_enemy_hexes") or [])[:10]:
        s = t["source"]
        tg = t["target"]
        defs = ", ".join(f"{k}×{v}" for k, v in t.get("defenders", {}).items())
        ad = "AD-COVERED" if t.get("ad_coverage") else "no AD"
        targets_lines.append(
            f"  source ({s['global_row']},{s['global_col']}) → target "
            f"({tg['global_row']},{tg['global_col']}) dist={t.get('distance')} "
            f"enemy={t['enemy_country']}  defenders={{{defs}}}  {ad}  "
            f"hit_prob={t.get('hit_prob_preview')}  downed_prob={t.get('downed_prob_preview')}"
        )
    targets_block = "\n".join(targets_lines) or "  (no targetable enemy hexes — no strike possible)"

    return f"""You are the head of state of {country_code.upper()}.

## D7 — AIR STRIKE REVIEW (Round {round_num}) — CONTRACT_AIR_STRIKES v1.0

[ECONOMIC STATE]
  GDP:           {eco.get('gdp', 0):.0f}
  Treasury:      {eco.get('treasury', 0):.0f}
  Stability:     {eco.get('stability', 5)}/10
  At war with:   {', '.join(eco.get('at_war_with') or []) or 'nobody'}

[MY TACTICAL AIR FORCES BY SOURCE HEX]
{forces_block}

[TARGETABLE ENEMY HEXES] (within 2 cardinal hexes — your only legal targets)
{targets_block}

{ctx.get('decision_rules', '')}

[INSTRUCTION]
{ctx.get('instruction', '')}

Respond with JSON ONLY matching CONTRACT_AIR_STRIKES §2:
{{
  "action_type": "attack_air",
  "country_code": "{country_code}",
  "round_num": {round_num},
  "decision": "change" | "no_change",
  "rationale": "string >= 30 chars",
  "changes": {{
    "source_global_row": int,
    "source_global_col": int,
    "target_global_row": int,
    "target_global_col": int,
    "attacker_unit_codes": ["unit_code", ...]
  }}
}}
"""


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


def test_air_strike_full_chain_ai_acceptance_gate():
    """M3 acceptance gate. AI → validator → engine → snapshot."""
    client = get_client()

    # Idempotency: delete prior run with same name
    prior = client.table("sim_runs").select("id").eq("name", RUN_NAME).execute().data or []
    for p in prior:
        client.table("sim_runs").delete().eq("id", p["id"]).execute()

    sim_run_id = create_run(
        scenario_code=SCENARIO_CODE,
        name=RUN_NAME,
        description=(
            "M3 acceptance gate: AI head of state of Cathay reviews air strike "
            "opportunities and decides via Gemini Flash. Decision is validated, "
            "persisted, and resolved through the canonical M3 engine with full "
            "per-shot dice + modifier breakdown."
        ),
    )
    seed_round_zero(sim_run_id)
    _seed_round(client, sim_run_id, 1)

    print(f"\n  [acceptance] sim_run_id={sim_run_id}")

    ctx = build_air_strike_context(
        country_code=TEST_COUNTRY,
        scenario_code=SCENARIO_CODE,
        round_num=1,
        sim_run_id=sim_run_id,
    )
    print(f"  [context] my air hexes={len(ctx['my_air_forces_by_hex'])} "
          f"targetable={len(ctx['targetable_enemy_hexes'])}")
    if not ctx["targetable_enemy_hexes"]:
        pytest.skip("No targetable enemy hexes — Cathay has no legal air targets")

    prompt = _build_prompt(TEST_COUNTRY, 1, ctx)
    raw = asyncio.run(_call_llm(prompt, SYSTEM_AIR_STRIKE, max_tokens=600))
    parsed = _parse_json(raw)
    assert parsed is not None, f"AI returned unparseable JSON: {raw!r}"

    parsed.setdefault("action_type", "attack_air")
    parsed.setdefault("country_code", TEST_COUNTRY)
    parsed.setdefault("round_num", 1)

    print(f"  [AI decision] {parsed.get('decision')}")
    print(f"  [AI rationale] {(parsed.get('rationale') or '')[:150]}")
    if parsed.get("decision") == "change":
        ch = parsed.get("changes", {})
        print(f"  [AI strike] ({ch.get('source_global_row')},{ch.get('source_global_col')}) → "
              f"({ch.get('target_global_row')},{ch.get('target_global_col')}) "
              f"with {ch.get('attacker_unit_codes')}")

    # Validate
    units_rows = client.table("unit_states_per_round").select("*") \
        .eq("sim_run_id", sim_run_id).eq("round_num", 1).execute().data or []
    units_dict = {u["unit_code"]: u for u in units_rows}
    cs_rows = client.table("country_states_per_round").select("*") \
        .eq("sim_run_id", sim_run_id).eq("round_num", 1).execute().data or []
    country_state = {r["country_code"]: r for r in cs_rows}
    zones: dict = {}
    for u in units_rows:
        r, c = u.get("global_row"), u.get("global_col")
        if r is not None and c is not None:
            zones.setdefault((r, c), {"type": "land", "owner": u.get("country_code")})

    report = validate_air_strike(parsed, units_dict, country_state, zones)
    assert report["valid"], f"Validator rejected AI decision: {report['errors']}\npayload: {parsed}"
    normalized = report["normalized"]

    # Persist + resolve
    sci = client.table("sim_scenarios").select("id").eq("code", SCENARIO_CODE).limit(1).execute().data[0]["id"]
    client.table("agent_decisions").insert({
        "sim_run_id": sim_run_id,
        "scenario_id": sci,
        "country_code": TEST_COUNTRY,
        "action_type": "attack_air",
        "action_payload": normalized,
        "rationale": normalized.get("rationale", ""),
        "validation_status": "passed",
        "round_num": 1,
    }).execute()

    resolve_round(sim_run_id, 1)

    if normalized["decision"] == "change":
        combats = client.table("observatory_combat_results").select("*") \
            .eq("sim_run_id", sim_run_id).eq("round_num", 1) \
            .eq("attacker_country", TEST_COUNTRY) \
            .eq("combat_type", "air_strike").execute().data or []
        assert combats, "Expected at least one air_strike row"
        cb = combats[0]
        n_shots = len(cb["attacker_rolls"])
        n_hits = sum(1 for s in cb["attacker_rolls"] if s.get("hit"))
        print(f"  [combat] {n_shots} sorties, {n_hits} hits, "
              f"ATK losses={len(cb['attacker_losses'])} DEF losses={len(cb['defender_losses'])}")
        print(f"  [narrative] {cb['narrative']}")

        # M3 shape: per-shot dicts in attacker_rolls
        assert isinstance(cb["attacker_rolls"], list)
        if cb["attacker_rolls"]:
            first = cb["attacker_rolls"][0]
            assert isinstance(first, dict)
            assert "hit_probability" in first
            assert "hit_roll" in first
            assert "hit" in first
        # modifier_breakdown column populated
        assert "modifier_breakdown" in cb

    # Audit JSONB
    row = client.table("country_states_per_round").select("attack_air_decision") \
        .eq("sim_run_id", sim_run_id).eq("round_num", 1).eq("country_code", TEST_COUNTRY) \
        .limit(1).execute().data[0]
    assert row["attack_air_decision"] is not None

    finalize_run(
        sim_run_id, status="visible_for_review",
        notes=f"M3 acceptance gate: {normalized.get('decision')} — "
              f"{(normalized.get('rationale') or '')[:80]}",
    )
    print(f"\n  [ACCEPTANCE GATE PASSED] sim_run_id={sim_run_id}")
