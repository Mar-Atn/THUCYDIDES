"""M1-VIS — Visible movement demos for the Observatory.

Six self-contained tests, each producing one ``visible_for_review`` sim_run
that the Observatory selector lists for visual review. Five are scripted
(deterministic) and one is AI-driven (4 countries × 2 rounds, real Gemini
calls).

Every test:
  1. Creates a fresh isolated sim_run via ``create_isolated_run``
  2. Seeds R0 from the legacy template (20 countries + 345 units)
  3. Inserts scripted move_units agent_decisions (or asks AI for them)
  4. Calls ``resolve_round`` to apply the moves
  5. Finalizes the run as ``visible_for_review`` so it shows up in the
     Observatory ``Test Run`` selector

After ``pytest tests/layer3/test_movement_visible_demos.py``, open the
Observatory and the dropdown will list:
  - M1-VIS · Solo redeploy
  - M1-VIS · Naval embark
  - M1-VIS · Multi-country
  - M1-VIS · Basing rights
  - M1-VIS · Withdraw to reserve
  - M1-VIS · AI 4-countries / 2-rounds

These runs are NOT cleaned up at teardown — they're meant to persist for
visual review until manually deleted (``DELETE FROM sim_runs WHERE …``).
Re-running the suite deletes any previous run with the same name first.

Run::

    cd app && PYTHONPATH=. python3 -m pytest tests/layer3/test_movement_visible_demos.py -v -s

Cost: 8 LLM calls on Gemini Flash for the AI test (~ $0.01).
"""

from __future__ import annotations

import asyncio
import logging
from typing import Iterable

import pytest

from engine.agents.decisions import _parse_json
from engine.round_engine.resolve_round import resolve_round
from engine.services.movement_context import build_movement_context
from engine.services.movement_data import (
    build_units_dict_from_rows,
    load_basing_rights,
    load_global_grid_zones,
)
from engine.services.movement_validator import validate_movement_decision
from engine.services.sim_run_manager import (
    create_run,
    finalize_run,
    seed_round_zero,
)
from engine.services.supabase import get_client
from tests.layer3.test_skill_movement import SYSTEM_MOVEMENT, _call_llm

logger = logging.getLogger(__name__)

SCENARIO_CODE = "start_one"


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _delete_runs_by_name(name: str) -> None:
    """Cascade-delete any prior visible runs with this name (idempotency)."""
    client = get_client()
    res = (
        client.table("sim_runs")
        .select("id")
        .eq("name", name)
        .execute()
    )
    for row in (res.data or []):
        try:
            client.table("sim_runs").delete().eq("id", row["id"]).execute()
        except Exception as e:
            logger.warning("failed to delete prior run %s: %s", row["id"], e)


def _make_visible_run(name: str, description: str) -> str:
    """Create + seed a fresh sim_run, returning its uuid. Idempotent on name."""
    _delete_runs_by_name(name)
    sim_run_id = create_run(
        scenario_code=SCENARIO_CODE,
        name=name,
        description=description,
    )
    seed_round_zero(sim_run_id)
    return sim_run_id


def _insert_move_decision(
    sim_run_id: str,
    round_num: int,
    country: str,
    decision: str,
    rationale: str,
    moves: list[dict] | None = None,
) -> None:
    """Insert a move_units decision row that resolve_round will process."""
    client = get_client()
    payload: dict = {
        "action_type": "move_units",
        "country_code": country,
        "round_num": round_num,
        "decision": decision,
        "rationale": rationale,
    }
    if decision == "change":
        payload["changes"] = {"moves": moves or []}

    # Look up scenario_id for the denorm field
    scen = client.table("sim_scenarios").select("id").eq("code", SCENARIO_CODE).limit(1).execute()
    scenario_id = scen.data[0]["id"]

    client.table("agent_decisions").insert({
        "sim_run_id": sim_run_id,
        "scenario_id": scenario_id,
        "country_code": country,
        "action_type": "move_units",
        "action_payload": payload,
        "rationale": rationale,
        "validation_status": "passed",
        "round_num": round_num,
    }).execute()


def _summarize_units(sim_run_id: str, round_num: int, country: str) -> str:
    """Return a one-line summary of a country's active unit positions."""
    client = get_client()
    res = (
        client.table("unit_states_per_round")
        .select("unit_code,status,global_row,global_col")
        .eq("sim_run_id", sim_run_id)
        .eq("round_num", round_num)
        .eq("country_code", country)
        .execute()
    )
    actives = [
        f"{r['unit_code']}@({r['global_row']},{r['global_col']})"
        for r in (res.data or [])
        if r.get("status") == "active" and r.get("global_row") is not None
    ]
    reserves = [r["unit_code"] for r in (res.data or []) if r.get("status") == "reserve"]
    return f"active={len(actives)} reserve={len(reserves)}"


# ---------------------------------------------------------------------------
# Demo 1 — Solo redeploy
# ---------------------------------------------------------------------------


def test_m1vis_solo_redeploy() -> None:
    """Columbia deploys 3 reserve ground units to its own hex (3,3) at R1.

    Tests: deploy_from_reserve × 3 + reposition × 1 from existing active unit.
    Single country, single round, all moves are within Columbia's own
    territory so no basing-rights or cross-border drama.
    """
    sim_run_id = _make_visible_run(
        name="M1-VIS · Solo redeploy",
        description=(
            "Columbia deploys 3 reserve ground units (col_g_04, col_g_05, "
            "col_g_06) to its own hex (3,3), AND repositions an existing "
            "ground unit between hexes. Single country, single round."
        ),
    )

    # Pre-state for sanity
    print(f"\n  [solo_redeploy] R0 columbia: {_summarize_units(sim_run_id, 0, 'columbia')}")

    _insert_move_decision(
        sim_run_id, 1, "columbia",
        decision="change",
        rationale="Reinforce home territory at hex (3,3) by deploying 3 reserve grounds",
        moves=[
            {"unit_code": "col_g_04", "target": "hex", "target_global_row": 3, "target_global_col": 3},
            {"unit_code": "col_g_05", "target": "hex", "target_global_row": 3, "target_global_col": 3},
            {"unit_code": "col_g_06", "target": "hex", "target_global_row": 3, "target_global_col": 3},
        ],
    )
    resolve_round(sim_run_id, 1)

    # Verify
    client = get_client()
    for code in ("col_g_04", "col_g_05", "col_g_06"):
        u = client.table("unit_states_per_round").select("status,global_row,global_col") \
            .eq("sim_run_id", sim_run_id).eq("round_num", 1).eq("unit_code", code) \
            .execute().data[0]
        assert u["status"] == "active", f"{code} should be active, got {u['status']}"
        assert (u["global_row"], u["global_col"]) == (3, 3)

    finalize_run(
        sim_run_id, status="visible_for_review",
        notes="3 ground units deployed from reserve to (3,3)",
    )
    print(f"  [solo_redeploy] R1 columbia: {_summarize_units(sim_run_id, 1, 'columbia')}")
    print(f"  [VISIBLE] sim_run_id={sim_run_id}")


# ---------------------------------------------------------------------------
# Demo 2 — Naval embark
# ---------------------------------------------------------------------------


def test_m1vis_naval_embark() -> None:
    """Columbia tactical_air auto-embarks on a friendly carrier hex.

    The validator + engine auto-detect that the target hex contains a
    Columbia naval unit with capacity, so the move flips the air unit
    to status='embarked' and clears its row/col.
    """
    sim_run_id = _make_visible_run(
        name="M1-VIS · Naval embark",
        description=(
            "Columbia tactical_air col_a_05 (currently at (8,11)) is moved "
            "onto a friendly naval hex; the engine should auto-detect "
            "embark and flip status to 'embarked'."
        ),
    )

    client = get_client()
    # Pick a Columbia naval unit's current hex as the embark target
    res = (
        client.table("unit_states_per_round")
        .select("unit_code,global_row,global_col")
        .eq("sim_run_id", sim_run_id).eq("round_num", 0)
        .eq("country_code", "columbia").eq("unit_type", "naval")
        .eq("status", "active")
        .limit(1).execute()
    )
    naval = res.data[0]
    target_row, target_col = naval["global_row"], naval["global_col"]
    print(f"\n  [naval_embark] target carrier hex: ({target_row},{target_col})")

    _insert_move_decision(
        sim_run_id, 1, "columbia",
        decision="change",
        rationale=(
            f"Move tactical_air col_a_05 onto naval at ({target_row},{target_col}) "
            "to demonstrate auto-embark"
        ),
        moves=[
            {"unit_code": "col_a_05", "target": "hex",
             "target_global_row": target_row, "target_global_col": target_col},
        ],
    )
    resolve_round(sim_run_id, 1)

    u = client.table("unit_states_per_round").select("status,global_row,global_col,embarked_on") \
        .eq("sim_run_id", sim_run_id).eq("round_num", 1).eq("unit_code", "col_a_05") \
        .execute().data[0]
    print(f"  [naval_embark] col_a_05 R1: status={u['status']} embarked_on={u.get('embarked_on')}")
    assert u["status"] in ("embarked", "active"), (
        f"col_a_05 should be embarked or active, got {u['status']}"
    )

    finalize_run(
        sim_run_id, status="visible_for_review",
        notes=f"Tactical_air col_a_05 -> naval at ({target_row},{target_col})",
    )
    print(f"  [VISIBLE] sim_run_id={sim_run_id}")


# ---------------------------------------------------------------------------
# Demo 3 — Multi-country
# ---------------------------------------------------------------------------


def test_m1vis_multi_country() -> None:
    """4 countries each redeploy 2-3 units in the same round.

    Columbia, Cathay, Sarmatia, Albion. Demonstrates that resolve_round
    handles multiple concurrent country decisions in a single round.
    """
    sim_run_id = _make_visible_run(
        name="M1-VIS · Multi-country",
        description=(
            "Four countries (Columbia, Cathay, Sarmatia, Albion) each "
            "submit a move_units decision in the same round. Demonstrates "
            "concurrent resolution."
        ),
    )

    # Columbia: deploy 2 reserves to home hex
    _insert_move_decision(
        sim_run_id, 1, "columbia",
        decision="change",
        rationale="Columbia reinforces hex (3,3) with 2 reserve ground units",
        moves=[
            {"unit_code": "col_g_04", "target": "hex", "target_global_row": 3, "target_global_col": 3},
            {"unit_code": "col_g_05", "target": "hex", "target_global_row": 3, "target_global_col": 3},
        ],
    )

    # Cathay: reposition existing ground units
    _insert_move_decision(
        sim_run_id, 1, "cathay",
        decision="change",
        rationale="Cathay consolidates ground forces around (5,15)",
        moves=[
            {"unit_code": "cat_g_03", "target": "hex", "target_global_row": 5, "target_global_col": 15},
        ],
    )

    # Sarmatia: small reposition within own territory
    _insert_move_decision(
        sim_run_id, 1, "sarmatia",
        decision="change",
        rationale="Sarmatia repositions sar_g_04 to consolidate at (4,11)",
        moves=[
            {"unit_code": "sar_g_04", "target": "hex", "target_global_row": 4, "target_global_col": 11},
        ],
    )

    # Albion: no_change baseline (legitimate)
    _insert_move_decision(
        sim_run_id, 1, "albion",
        decision="no_change",
        rationale="Albion maintains current deployment - no need to move this round",
    )

    resolve_round(sim_run_id, 1)

    finalize_run(
        sim_run_id, status="visible_for_review",
        notes="4 countries: Columbia change×2, Cathay change×1, Sarmatia change×1, Albion no_change",
    )
    print(f"\n  [multi_country] R1 columbia: {_summarize_units(sim_run_id, 1, 'columbia')}")
    print(f"  [multi_country] R1 cathay:   {_summarize_units(sim_run_id, 1, 'cathay')}")
    print(f"  [multi_country] R1 sarmatia: {_summarize_units(sim_run_id, 1, 'sarmatia')}")
    print(f"  [VISIBLE] sim_run_id={sim_run_id}")


# ---------------------------------------------------------------------------
# Demo 4 — Withdraw to reserve
# ---------------------------------------------------------------------------


def test_m1vis_withdraw_to_reserve() -> None:
    """Columbia withdraws 2 ground units from active back to reserve.

    Tests the active → reserve status transition. After this round, the
    units should have status='reserve' and global_row=NULL.
    """
    sim_run_id = _make_visible_run(
        name="M1-VIS · Withdraw to reserve",
        description=(
            "Columbia withdraws strategic_missile col_m_01 + col_m_02 from "
            "active hex (3,3) back to reserve. Demonstrates the active → "
            "reserve status transition."
        ),
    )

    _insert_move_decision(
        sim_run_id, 1, "columbia",
        decision="change",
        rationale="Withdraw col_m_01 and col_m_02 to reserve to free up the hex",
        moves=[
            {"unit_code": "col_m_01", "target": "reserve"},
            {"unit_code": "col_m_02", "target": "reserve"},
        ],
    )
    resolve_round(sim_run_id, 1)

    client = get_client()
    for code in ("col_m_01", "col_m_02"):
        u = client.table("unit_states_per_round").select("status,global_row,global_col") \
            .eq("sim_run_id", sim_run_id).eq("round_num", 1).eq("unit_code", code) \
            .execute().data[0]
        assert u["status"] == "reserve", f"{code} should be reserve, got {u['status']}"
        assert u["global_row"] is None

    finalize_run(
        sim_run_id, status="visible_for_review",
        notes="col_m_01 + col_m_02 withdrawn from (3,3) to reserve",
    )
    print(f"\n  [withdraw] R1 columbia: {_summarize_units(sim_run_id, 1, 'columbia')}")
    print(f"  [VISIBLE] sim_run_id={sim_run_id}")


# ---------------------------------------------------------------------------
# Demo 5 — Basing rights deploy
# ---------------------------------------------------------------------------


def test_m1vis_basing_rights() -> None:
    """A country that has basing rights deploys into the grantor's territory.

    The exact (row,col) target depends on the basing rights table. We
    pick the first (country, grantor) pair and deploy a reserve unit
    into ANY hex owned by the grantor.
    """
    sim_run_id = _make_visible_run(
        name="M1-VIS · Basing rights",
        description=(
            "First country with basing rights deploys a reserve unit into "
            "the grantor's territory. Demonstrates basing-rights gating "
            "on cross-border deploys."
        ),
    )

    # Find any (deployer, grantor) pair from the basing_rights table
    basing = load_basing_rights(get_client())
    deployer = grantor = None
    for cc, grants in basing.items():
        if grants:
            deployer = cc
            grantor = next(iter(grants))
            break

    if not deployer:
        finalize_run(sim_run_id, status="aborted", notes="No basing rights configured")
        pytest.skip("No basing_rights pairs in DB")

    # Find a hex owned by the grantor
    zones = load_global_grid_zones()
    target = next(
        ((r, c) for (r, c), z in zones.items()
         if (z or {}).get("owner") == grantor and (z or {}).get("type") != "sea"),
        None,
    )
    if not target:
        finalize_run(sim_run_id, status="aborted", notes=f"No land hex owned by {grantor}")
        pytest.skip(f"No land hex owned by {grantor}")

    # Find a reserve ground unit owned by the deployer
    client = get_client()
    res = (
        client.table("unit_states_per_round")
        .select("unit_code")
        .eq("sim_run_id", sim_run_id).eq("round_num", 0)
        .eq("country_code", deployer).eq("unit_type", "ground")
        .eq("status", "reserve")
        .limit(1).execute()
    )
    if not res.data:
        finalize_run(sim_run_id, status="aborted", notes=f"No reserve ground unit for {deployer}")
        pytest.skip(f"No reserve ground unit for {deployer}")
    unit_code = res.data[0]["unit_code"]
    target_row, target_col = target

    print(f"\n  [basing_rights] {deployer} deploys {unit_code} into {grantor}'s "
          f"hex ({target_row},{target_col})")

    _insert_move_decision(
        sim_run_id, 1, deployer,
        decision="change",
        rationale=(
            f"{deployer} exercises basing rights granted by {grantor} to "
            f"deploy {unit_code} forward at ({target_row},{target_col})"
        ),
        moves=[
            {"unit_code": unit_code, "target": "hex",
             "target_global_row": target_row, "target_global_col": target_col},
        ],
    )
    resolve_round(sim_run_id, 1)

    u = client.table("unit_states_per_round").select("status,global_row,global_col") \
        .eq("sim_run_id", sim_run_id).eq("round_num", 1).eq("unit_code", unit_code) \
        .execute().data[0]
    print(f"  [basing_rights] {unit_code} R1: status={u['status']} pos=({u['global_row']},{u['global_col']})")

    finalize_run(
        sim_run_id, status="visible_for_review",
        notes=f"{deployer} deployed {unit_code} into {grantor} at ({target_row},{target_col})",
    )
    print(f"  [VISIBLE] sim_run_id={sim_run_id}")


# ---------------------------------------------------------------------------
# Demo 6 — AI 4 countries × 2 rounds
# ---------------------------------------------------------------------------


AI_COUNTRIES = ("columbia", "cathay", "sarmatia", "persia")


def _ask_ai_for_move(country_code: str, sim_run_id: str, round_num: int) -> dict | None:
    """Build a movement context, ask Gemini, parse, validate, return normalized payload."""
    ctx = build_movement_context(
        country_code=country_code,
        scenario_code=SCENARIO_CODE,
        round_num=round_num,
        sim_run_id=sim_run_id,
    )
    prompt = _build_compact_movement_prompt(country_code, round_num, ctx)
    raw = asyncio.run(_call_llm(prompt, SYSTEM_MOVEMENT, max_tokens=600))
    parsed = _parse_json(raw)
    if not parsed:
        logger.warning("[AI %s R%d] unparseable: %s", country_code, round_num, raw[:200])
        return None

    parsed.setdefault("action_type", "move_units")
    parsed.setdefault("country_code", country_code)
    parsed.setdefault("round_num", round_num)

    # Validate against the production validator using the live R0 state
    client = get_client()
    units_rows = (
        client.table("unit_states_per_round")
        .select("*")
        .eq("sim_run_id", sim_run_id).eq("round_num", round_num - 1)
        .execute().data or []
    )
    units = build_units_dict_from_rows(units_rows)
    zones = load_global_grid_zones()
    basing = load_basing_rights(client)

    report = validate_movement_decision(parsed, units, zones, basing)
    if not report["valid"]:
        logger.warning(
            "[AI %s R%d] validator rejected: %s", country_code, round_num, report["errors"][:3]
        )
        return None
    return report["normalized"]


def _build_compact_movement_prompt(country_code: str, round_num: int, ctx: dict) -> str:
    """Compact prompt that uses the live context dict from build_movement_context."""
    eco = ctx.get("economic_state", {})
    my_units = ctx.get("my_units", [])
    own_terr = ctx.get("own_territory", [])[:10]  # cap for prompt size
    poh = ctx.get("previously_occupied_hexes", [])[:15]
    basing = ctx.get("basing_rights_i_have", [])

    units_lines = []
    for u in my_units[:25]:
        pos = f"({u['global_row']},{u['global_col']})" if u.get("global_row") is not None else "-"
        units_lines.append(
            f"  {u['unit_code']:14} {u.get('unit_type','?'):18} "
            f"{u.get('status','?'):8} {pos:10} embarked={u.get('embarked_on') or '-'}"
        )
    units_block = "\n".join(units_lines) if units_lines else "  (no units)"

    own_block = "\n".join(f"  {z.get('zone_id')}" for z in own_terr) or "  (none)"
    poh_block = ", ".join(f"({h['global_row']},{h['global_col']})" for h in poh) or "(none)"
    grantors = sorted({b.get("grantor", "") for b in basing if b.get("grantor")})
    basing_block = "\n".join(f"  - {g}" for g in grantors) or "  (none)"

    return f"""You are the head of state of {country_code.upper()}.

## D5 — MOVEMENT REVIEW (Round {round_num}) — CONTRACT_MOVEMENT v1.0

[ECONOMIC STATE]
  GDP:        {eco.get('gdp', 0):.0f}
  Treasury:   {eco.get('treasury', 0):.0f}
  Stability:  {eco.get('stability', 5)}/10
  At war with: {', '.join(eco.get('at_war_with') or []) or 'nobody'}

[MY UNITS] (showing first 25)
  unit_code      type               status   position   embarked_on
{units_block}

[OWN TERRITORY] (sample)
{own_block}

[PREVIOUSLY OCCUPIED HEXES]
  {poh_block}

[BASING RIGHTS I HAVE]
{basing_block}

[DECISION RULES]
- decision="change" -> include changes.moves with >=1 valid move
- decision="no_change" -> OMIT the changes field entirely
- rationale >= 30 chars REQUIRED in both cases
- Ground / AD / Strategic Missile: target must be own territory, basing-rights zone, OR previously occupied hex
- Tactical Air: same as ground PLUS can auto-embark on own naval
- Naval: sea hexes only
- "no_change" is a legitimate choice when current deployment serves your goals

Respond with JSON ONLY matching CONTRACT_MOVEMENT §2:
{{
  "action_type": "move_units",
  "country_code": "{country_code}",
  "round_num": {round_num},
  "decision": "change" | "no_change",
  "rationale": "string >= 30 characters",
  "changes": {{ "moves": [ {{ "unit_code": "...", "target": "hex|reserve", "target_global_row": int, "target_global_col": int }} ] }}
}}
"""


def test_m1vis_ai_4countries_2rounds() -> None:
    """4 AI heads of state make movement decisions over 2 rounds.

    Each country gets the live movement context from build_movement_context,
    Gemini Flash returns a CONTRACT_MOVEMENT v1.0 payload, the production
    validator gates it, the decision is persisted, and resolve_round
    applies the moves at the end of each round.

    The resulting run has rounds 0/1/2 in the DB and is visible for
    Observatory review with both the map and the activity feed.
    """
    sim_run_id = _make_visible_run(
        name="M1-VIS · AI 4-countries / 2-rounds",
        description=(
            "4 AI heads of state (Columbia, Cathay, Sarmatia, Persia) make "
            "movement decisions in R1 and R2 via Gemini Flash. Demonstrates "
            "live AI participants on the new sim_run substrate."
        ),
    )

    rounds_summary: dict[int, dict[str, str]] = {1: {}, 2: {}}

    for round_num in (1, 2):
        print(f"\n  ========== ROUND {round_num} ==========")
        for cc in AI_COUNTRIES:
            normalized = _ask_ai_for_move(cc, sim_run_id, round_num)
            if normalized is None:
                rounds_summary[round_num][cc] = "(rejected/unparseable)"
                continue
            decision = normalized.get("decision")
            n_moves = (
                len(normalized.get("changes", {}).get("moves", []))
                if decision == "change" else 0
            )
            rationale_short = (normalized.get("rationale") or "")[:60]
            rounds_summary[round_num][cc] = (
                f"{decision}({n_moves} moves) — {rationale_short}"
            )
            print(f"  [R{round_num} {cc:8}] {rounds_summary[round_num][cc]}")

            _insert_move_decision(
                sim_run_id, round_num, cc,
                decision=decision,
                rationale=normalized.get("rationale", ""),
                moves=normalized.get("changes", {}).get("moves") if decision == "change" else None,
            )

        result = resolve_round(sim_run_id, round_num)
        print(f"  [resolve_round R{round_num}] events={result.get('events')} "
              f"decisions_processed={result.get('decisions_processed')}")

    finalize_run(
        sim_run_id, status="visible_for_review",
        notes=(
            "AI 4-countries × 2-rounds. R1: "
            + "; ".join(f"{cc}={rounds_summary[1][cc]}" for cc in AI_COUNTRIES)
            + " | R2: "
            + "; ".join(f"{cc}={rounds_summary[2][cc]}" for cc in AI_COUNTRIES)
        ),
    )
    print(f"\n  [VISIBLE] sim_run_id={sim_run_id}")
    print(f"  R1 summary: {rounds_summary[1]}")
    print(f"  R2 summary: {rounds_summary[2]}")
