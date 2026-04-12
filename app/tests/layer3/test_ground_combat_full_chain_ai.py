"""L3 — Ground combat ACCEPTANCE GATE (CONTRACT_GROUND_COMBAT v1.0).

Step 7 of the M2 vertical slice. End-to-end proof:

  build_ground_combat_context (live state)
    -> compact prompt
      -> Gemini Flash AI decision
        -> validate_ground_attack (production validator)
          -> agent_decisions row
            -> resolve_round (canonical pure dice + modifier breakdown)
              -> observatory_combat_results row
              -> unit_states_per_round losses
              -> attack_ground_decision audit JSONB
              -> finalize_run as visible_for_review

The run is left in the DB for visual review in the Observatory.

Cost: 1 LLM call on Gemini Flash ~ $0.001.
"""

from __future__ import annotations

import asyncio
import json
import logging

import pytest

from engine.agents.decisions import _parse_json
from engine.round_engine.resolve_round import resolve_round
from engine.services.combat_context import build_ground_combat_context
from engine.services.ground_combat_validator import validate_ground_attack
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
RUN_NAME = "M2-VIS · AI ground combat acceptance gate"

SYSTEM_GROUND_COMBAT = (
    "You are an AI head of state reviewing ground attack opportunities per "
    "CONTRACT_GROUND_COMBAT v1.0. Return ONLY JSON matching the attack_ground "
    "schema. Rationale >= 30 chars mandatory in both decision values. "
    "On no_change: OMIT the changes field entirely. "
    "On change: pick exactly ONE source/target pair and 1-3 attacker_unit_codes."
)


def _build_prompt(country_code: str, round_num: int, ctx: dict) -> str:
    eco = ctx.get("economic_state", {})

    forces_lines = []
    for hex_key, units in (ctx.get("my_ground_forces_by_hex") or {}).items():
        forces_lines.append(f"  hex ({hex_key}) — {len(units)} ground units:")
        for u in units[:6]:
            forces_lines.append(f"    {u['unit_code']}")
    forces_block = "\n".join(forces_lines) or "  (no ground forces)"

    aeh_lines = []
    for aeh in (ctx.get("adjacent_enemy_hexes") or [])[:10]:
        s = aeh["source"]
        t = aeh["target"]
        defs = ", ".join(f"{k}×{v}" for k, v in aeh.get("defenders", {}).items())
        mods_text = (
            ", ".join(f"{m['side']}{m['value']:+d} ({m['reason']})"
                      for m in aeh.get("modifiers_preview", []))
            or "no modifiers"
        )
        aeh_lines.append(
            f"  source ({s['global_row']},{s['global_col']}) → target "
            f"({t['global_row']},{t['global_col']}) "
            f"enemy={aeh['enemy_country']}  defenders={{{defs}}}  modifiers={mods_text}"
        )
    aeh_block = "\n".join(aeh_lines) or "  (no adjacent enemy hexes — no attack possible)"

    return f"""You are the head of state of {country_code.upper()}.

## D6 — GROUND COMBAT REVIEW (Round {round_num}) — CONTRACT_GROUND_COMBAT v1.0

[ECONOMIC STATE]
  GDP:           {eco.get('gdp', 0):.0f}
  Treasury:      {eco.get('treasury', 0):.0f}
  Stability:     {eco.get('stability', 5)}/10
  War tiredness: {eco.get('war_tiredness', 0)}
  At war with:   {', '.join(eco.get('at_war_with') or []) or 'nobody'}

[MY GROUND FORCES BY SOURCE HEX]
{forces_block}

[ADJACENT ENEMY HEXES] (your only legal attack targets)
{aeh_block}

{ctx.get('decision_rules', '')}

[INSTRUCTION]
{ctx.get('instruction', '')}

Respond with JSON ONLY matching CONTRACT_GROUND_COMBAT §2:
{{
  "action_type": "attack_ground",
  "country_code": "{country_code}",
  "round_num": {round_num},
  "decision": "change" | "no_change",
  "rationale": "string >= 30 chars",
  "changes": {{
    "source_global_row": int,
    "source_global_col": int,
    "target_global_row": int,
    "target_global_col": int,
    "attacker_unit_codes": ["unit_code", ...],
    "allow_chain": true
  }}
}}
"""


def _seed_round(client, sim_run_id: str, round_num: int) -> None:
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


def test_ground_combat_full_chain_ai_acceptance_gate():
    """The M2 acceptance gate. AI → validator → engine → snapshot.

    The resulting run is finalized as visible_for_review so it shows up
    in the Observatory selector for visual inspection.
    """
    client = get_client()

    # Idempotency: delete any prior run with the same name
    prior = client.table("sim_runs").select("id").eq("name", RUN_NAME).execute().data or []
    for p in prior:
        client.table("sim_runs").delete().eq("id", p["id"]).execute()

    sim_run_id = create_run(
        scenario_code=SCENARIO_CODE,
        name=RUN_NAME,
        description=(
            "M2 acceptance gate: AI head of state of Cathay reviews attack "
            "opportunities and decides via Gemini Flash. Decision is "
            "validated, persisted, and resolved through the canonical pure "
            "dice function with full modifier breakdown."
        ),
    )
    seed_round_zero(sim_run_id)
    _seed_round(client, sim_run_id, 1)

    print(f"\n  [acceptance] sim_run_id={sim_run_id}")

    # 1. Build the context (live, from the run we just seeded)
    ctx = build_ground_combat_context(
        country_code=TEST_COUNTRY,
        scenario_code=SCENARIO_CODE,
        round_num=1,
        sim_run_id=sim_run_id,
    )
    print(f"  [context] my hexes={len(ctx['my_ground_forces_by_hex'])} "
          f"adjacent_enemy_hexes={len(ctx['adjacent_enemy_hexes'])}")
    if not ctx["adjacent_enemy_hexes"]:
        pytest.skip("No adjacent enemy hexes — Cathay has no legal attack targets in seed data")

    # 2. Ask the AI
    prompt = _build_prompt(TEST_COUNTRY, 1, ctx)
    raw = asyncio.run(_call_llm(prompt, SYSTEM_GROUND_COMBAT, max_tokens=600))
    parsed = _parse_json(raw)
    assert parsed is not None, f"AI returned unparseable JSON: {raw!r}"

    parsed.setdefault("action_type", "attack_ground")
    parsed.setdefault("country_code", TEST_COUNTRY)
    parsed.setdefault("round_num", 1)

    print(f"  [AI decision] {parsed.get('decision')}")
    print(f"  [AI rationale] {(parsed.get('rationale') or '')[:150]}")
    if parsed.get("decision") == "change":
        ch = parsed.get("changes", {})
        print(f"  [AI attack] ({ch.get('source_global_row')},{ch.get('source_global_col')}) → "
              f"({ch.get('target_global_row')},{ch.get('target_global_col')}) "
              f"with {ch.get('attacker_unit_codes')}")

    # 3. Validate with the production validator
    units_rows = client.table("unit_states_per_round").select("*") \
        .eq("sim_run_id", sim_run_id).eq("round_num", 1).execute().data or []
    units_dict = {u["unit_code"]: u for u in units_rows}
    cs_rows = client.table("country_states_per_round").select("*") \
        .eq("sim_run_id", sim_run_id).eq("round_num", 1).execute().data or []
    country_state = {r["country_code"]: r for r in cs_rows}

    # Build a minimal zones dict — for the validator we just need (row,col) -> {type, owner}
    # In M2 we don't have a hex-level zones table; use the country_state to infer owner per
    # current unit positions and assume land for tested hexes. For the acceptance gate this
    # is sufficient because we only check sea-hex rejection on the target.
    zones: dict[tuple[int, int], dict] = {}
    for u in units_rows:
        r, c = u.get("global_row"), u.get("global_col")
        if r is not None and c is not None:
            zones.setdefault((r, c), {"type": "land", "owner": u.get("country_code")})

    report = validate_ground_attack(parsed, units_dict, country_state, zones)
    assert report["valid"], f"Validator rejected AI decision: {report['errors']}\npayload: {parsed}"
    normalized = report["normalized"]

    # 4. Persist the decision and run resolve_round
    sci = client.table("sim_scenarios").select("id").eq("code", SCENARIO_CODE).limit(1).execute().data[0]["id"]
    client.table("agent_decisions").insert({
        "sim_run_id": sim_run_id,
        "scenario_id": sci,
        "country_code": TEST_COUNTRY,
        "action_type": "attack_ground",
        "action_payload": normalized,
        "rationale": normalized.get("rationale", ""),
        "validation_status": "passed",
        "round_num": 1,
    }).execute()

    resolve_round(sim_run_id, 1)

    # 5. Verify outcomes
    if normalized["decision"] == "change":
        # Combat row written
        combats = client.table("observatory_combat_results").select("*") \
            .eq("sim_run_id", sim_run_id).eq("round_num", 1) \
            .eq("attacker_country", TEST_COUNTRY).execute().data or []
        assert combats, "Expected at least one combat row from AI's attack"
        cb = combats[0]
        print(f"  [combat] losses ATK={len(cb['attacker_losses'])} "
              f"DEF={len(cb['defender_losses'])} narrative={cb['narrative'][:80]}")

        # Modifier breakdown column populated (may be empty list, but must exist)
        assert "modifier_breakdown" in cb
        assert isinstance(cb["modifier_breakdown"], list)

        # Per-exchange dice (list of lists)
        assert isinstance(cb["attacker_rolls"], list)
        if cb["attacker_rolls"]:
            assert isinstance(cb["attacker_rolls"][0], list), \
                "attacker_rolls must be list-of-lists (per exchange)"
    else:
        print(f"  [no_change] AI declined to attack — checking no combat row written")
        combats = client.table("observatory_combat_results").select("id") \
            .eq("sim_run_id", sim_run_id).eq("round_num", 1) \
            .eq("attacker_country", TEST_COUNTRY).execute().data or []
        assert not combats, f"no_change should produce zero combat rows, got {len(combats)}"

    # 6. Audit JSONB written
    row = client.table("country_states_per_round").select("attack_ground_decision") \
        .eq("sim_run_id", sim_run_id).eq("round_num", 1).eq("country_code", TEST_COUNTRY) \
        .limit(1).execute().data[0]
    assert row["attack_ground_decision"] is not None

    # 7. Finalize as visible_for_review for Observatory inspection
    finalize_run(
        sim_run_id, status="visible_for_review",
        notes=f"M2 acceptance gate AI decision: {normalized.get('decision')} — "
              f"{(normalized.get('rationale') or '')[:80]}",
    )
    print(f"\n  [ACCEPTANCE GATE PASSED] sim_run_id={sim_run_id}")
    print(f"  Pick this run from the Observatory selector to inspect the combat visualization.")
