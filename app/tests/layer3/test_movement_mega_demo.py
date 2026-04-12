"""M1-VIS-MEGA — Big 4-round scripted movement scenario for visual replay.

ONE test, ONE visible sim_run, FOUR rounds, ~80 movement actions across
four countries. The script exercises EVERY movement code path:
deploy from reserve, reposition, naval reposition, tactical-air auto-embark,
ground auto-embark, withdraw to reserve.

  ROUND 1 — MASS MOBILIZATION
    Columbia: deploy 4 reserve grounds to (3,3)
    Cathay:   deploy 3 reserve grounds to (6,16)
    Sarmatia: deploy 1 reserve ground to (4,11)
    Albion:   deploy 2 reserve grounds to (3,8)
    + 6 NAVAL REPOSITIONS (cross-country)

  ROUND 2 — STRATEGIC MISSILE DEPLOYMENT
    Columbia: 2 tactical air auto-embark on col_n_06 at (4,5)
    Cathay:   reposition 2 grounds → (6,15)
    Columbia: deploy ALL 9 reserve missiles to (3,3)
    Cathay:   deploy ALL 2 reserve missiles to (6,15)
    Sarmatia: deploy ALL 7 reserve missiles to (2,16)
    Albion:   deploy ALL 2 reserve missiles to (3,8)
    + 6 NAVAL REPOSITIONS

  ROUND 3 — MISSILES BACK TO BUNKER + GROUND CARRIER OPS
    Columbia: withdraw all 12 active missiles to reserve
    Cathay:   withdraw all 4 active missiles to reserve + embark 4 grounds
              (one per cathay naval) at the carriers' hexes
    Sarmatia: withdraw all 12 active missiles to reserve
    Albion:   withdraw all 2 active missiles to reserve + embark 2 grounds
              (one per albion naval)
    + 6 NAVAL REPOSITIONS (Columbia + Sarmatia, NOT cathay/albion this round)

  ROUND 4 — POST-MISSILE SHUFFLE
    Columbia: withdraw col_g_05 + col_g_06 to reserve
    Sarmatia: withdraw sar_g_05 to reserve
    Cathay:   withdraw cat_g_01 to reserve
    Albion:   no_change
    + 6 NAVAL REPOSITIONS

After running, scrub R0..R4 in the Observatory map. The "Movements This
Round" panel below the map lists every move with full details.

Pure scripted, no AI calls.

Run::

    cd app && PYTHONPATH=. python3 -m pytest tests/layer3/test_movement_mega_demo.py -v -s
"""

from __future__ import annotations

import logging

from engine.round_engine.resolve_round import resolve_round
from engine.services.sim_run_manager import (
    create_run,
    finalize_run,
    seed_round_zero,
)
from engine.services.supabase import get_client

logger = logging.getLogger(__name__)

SCENARIO_CODE = "start_one"
RUN_NAME = "M1-VIS-MEGA · 4 rounds, 4 countries"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _delete_runs_by_name(name: str) -> None:
    client = get_client()
    res = client.table("sim_runs").select("id").eq("name", name).execute()
    for row in (res.data or []):
        try:
            client.table("sim_runs").delete().eq("id", row["id"]).execute()
        except Exception as e:
            logger.warning("failed to delete prior run %s: %s", row["id"], e)


def _make_visible_run() -> str:
    _delete_runs_by_name(RUN_NAME)
    sim_run_id = create_run(
        scenario_code=SCENARIO_CODE,
        name=RUN_NAME,
        description=(
            "4-round scripted movement showcase: Columbia + Cathay + Sarmatia "
            "+ Albion. ~80 movement actions including 6 naval repositions per "
            "round, ALL strategic missile reserves activated in R2 then "
            "withdrawn in R3, and Cathay/Albion ground units embarking on "
            "EACH of their naval carriers in R3."
        ),
    )
    seed_round_zero(sim_run_id)
    return sim_run_id


def _scenario_id_for(client) -> str:
    return client.table("sim_scenarios").select("id").eq("code", SCENARIO_CODE).limit(1).execute().data[0]["id"]


def _commit_decision(
    client,
    sim_run_id: str,
    scenario_id: str,
    round_num: int,
    country: str,
    decision: str,
    rationale: str,
    moves: list[dict] | None = None,
) -> None:
    """Insert one move_units agent_decisions row for resolve_round to process."""
    payload: dict = {
        "action_type": "move_units",
        "country_code": country,
        "round_num": round_num,
        "decision": decision,
        "rationale": rationale,
    }
    if decision == "change":
        payload["changes"] = {"moves": moves or []}

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


def _hex_move(unit_code: str, row: int, col: int) -> dict:
    return {"unit_code": unit_code, "target": "hex",
            "target_global_row": row, "target_global_col": col}


def _to_reserve(unit_code: str) -> dict:
    return {"unit_code": unit_code, "target": "reserve"}


def _summarize(sim_run_id: str, round_num: int, country: str) -> str:
    client = get_client()
    res = (
        client.table("unit_states_per_round")
        .select("status,unit_type")
        .eq("sim_run_id", sim_run_id)
        .eq("round_num", round_num)
        .eq("country_code", country)
        .execute()
    )
    rows = res.data or []
    active = sum(1 for r in rows if r.get("status") == "active")
    embarked = sum(1 for r in rows if r.get("status") == "embarked")
    reserve = sum(1 for r in rows if r.get("status") == "reserve")
    return f"active={active} embarked={embarked} reserve={reserve}"


def _print_round_summary(sim_run_id: str, round_num: int) -> None:
    print(f"\n  ===== AFTER ROUND {round_num} =====")
    for cc in ("columbia", "cathay", "sarmatia", "albion"):
        print(f"    {cc:10} {_summarize(sim_run_id, round_num, cc)}")


# ---------------------------------------------------------------------------
# Naval move tables (6 per round, all targeting known sea hexes from R0)
# ---------------------------------------------------------------------------

# Each entry: (country, unit_code, row, col)
# Targets are taken from existing R0 naval positions to guarantee they are
# valid sea hexes the validator will accept.

R1_NAVAL: list[tuple[str, str, int, int]] = [
    ("columbia", "col_n_01", 9, 6),    # (8,4) → (9,6) — swap with col_n_02
    ("columbia", "col_n_02", 8, 4),    # (9,6) → (8,4)
    ("columbia", "col_n_03", 9, 13),   # (10,12) → (9,13)
    ("columbia", "col_n_04", 8, 12),   # (9,12) → (8,12)
    ("cathay",   "cat_n_01", 6, 17),   # (7,17) → (6,17)
    ("albion",   "alb_n_01", 9, 11),   # (7,10) → (9,11)
]

R2_NAVAL: list[tuple[str, str, int, int]] = [
    ("columbia", "col_n_01", 8, 4),    # back to home
    ("columbia", "col_n_02", 9, 6),
    ("columbia", "col_n_03", 10, 12),
    ("columbia", "col_n_04", 9, 12),
    ("cathay",   "cat_n_01", 7, 17),
    ("albion",   "alb_n_01", 7, 10),
]

# R3: avoid moving cathay/albion naval — their grounds are embarking THIS round
R3_NAVAL: list[tuple[str, str, int, int]] = [
    ("columbia", "col_n_01", 9, 6),
    ("columbia", "col_n_02", 8, 4),
    ("columbia", "col_n_03", 9, 13),
    ("columbia", "col_n_04", 8, 12),
    ("columbia", "col_n_05", 10, 12),  # (9,13) → (10,12)
    ("sarmatia", "sar_n_01", 2, 17),   # (5,12) → (2,17) — same hex as sar_n_02
]

R4_NAVAL: list[tuple[str, str, int, int]] = [
    ("columbia", "col_n_07", 8, 18),   # (9,18) → (8,18)
    ("columbia", "col_n_08", 9, 18),
    ("columbia", "col_n_09", 9, 18),   # (5,20) → (9,18) — long-range
    ("columbia", "col_n_10", 9, 12),   # (8,12) → (9,12)
    ("cathay",   "cat_n_05", 8, 16),
    ("albion",   "alb_n_01", 9, 11),
]


def _commit_naval_moves(
    client, sim_run_id: str, scenario_id: str, round_num: int,
    naval_table: list[tuple[str, str, int, int]],
) -> None:
    """Group naval moves by country and submit one decision per country.

    Note: naval moves are merged with any other moves for that country
    via _commit_combined() — this helper is only for rounds where naval
    is the ONLY thing the country does.
    """
    by_country: dict[str, list[dict]] = {}
    for cc, code, r, c in naval_table:
        by_country.setdefault(cc, []).append(_hex_move(code, r, c))
    for cc, moves in by_country.items():
        _commit_decision(
            client, sim_run_id, scenario_id, round_num, cc,
            decision="change",
            rationale=f"R{round_num} naval reposition: {len(moves)} naval units repositioning",
            moves=moves,
        )


def _commit_combined(
    client, sim_run_id: str, scenario_id: str, round_num: int,
    country: str, rationale: str, moves: list[dict],
    naval_table: list[tuple[str, str, int, int]] | None = None,
) -> None:
    """Submit a single decision for one country combining its specific moves
    with any naval moves it owns from the round's naval table."""
    combined = list(moves)
    if naval_table:
        for cc, code, r, c in naval_table:
            if cc == country:
                combined.append(_hex_move(code, r, c))
    _commit_decision(
        client, sim_run_id, scenario_id, round_num, country,
        decision="change",
        rationale=rationale,
        moves=combined,
    )


def _countries_with_naval_in_round(naval_table: list[tuple[str, str, int, int]]) -> set[str]:
    return {cc for cc, _, _, _ in naval_table}


# ---------------------------------------------------------------------------
# THE TEST
# ---------------------------------------------------------------------------


def test_m1vis_mega_4round_scripted_demo() -> None:
    """4-round scripted demo with naval shuffles, missile mobilization &
    bunker, and ground carrier embarks."""
    client = get_client()
    sim_run_id = _make_visible_run()
    scenario_id = _scenario_id_for(client)
    print(f"\n  [mega] sim_run_id={sim_run_id}")
    _print_round_summary(sim_run_id, 0)

    # ====================================================================
    # ROUND 1 — MASS MOBILIZATION + 6 naval shuffles
    # ====================================================================
    print("\n  ===== SUBMIT ROUND 1 — MASS MOBILIZATION + NAVAL SHUFFLES =====")

    # Columbia: 4 ground deploys + naval shuffles
    _commit_combined(
        client, sim_run_id, scenario_id, 1, "columbia",
        rationale=(
            "R1 mobilization: Columbia activates 4 ground reserves at home "
            "hex (3,3) AND repositions 4 naval units across the Caribbean"
        ),
        moves=[
            _hex_move("col_g_05", 3, 3),
            _hex_move("col_g_06", 3, 3),
            _hex_move("col_g_09", 3, 3),
            _hex_move("col_g_10", 3, 3),
        ],
        naval_table=R1_NAVAL,
    )

    # Cathay: 3 ground deploys + 1 naval shuffle
    _commit_combined(
        client, sim_run_id, scenario_id, 1, "cathay",
        rationale="R1 mobilization: Cathay activates 3 ground reserves at (6,16) and shifts cat_n_01",
        moves=[
            _hex_move("cat_g_06", 6, 16),
            _hex_move("cat_g_07", 6, 16),
            _hex_move("cat_g_08", 6, 16),
        ],
        naval_table=R1_NAVAL,
    )

    # Sarmatia: 1 ground deploy (no naval this round)
    _commit_combined(
        client, sim_run_id, scenario_id, 1, "sarmatia",
        rationale="R1 mobilization: Sarmatia activates sar_g_17 reserve at (4,11) to thicken the line",
        moves=[_hex_move("sar_g_17", 4, 11)],
    )

    # Albion: 2 ground deploys + 1 naval shuffle
    _commit_combined(
        client, sim_run_id, scenario_id, 1, "albion",
        rationale="R1 mobilization: Albion activates 2 reserve grounds at (3,8) and shifts alb_n_01",
        moves=[
            _hex_move("alb_g_03", 3, 8),
            _hex_move("alb_g_04", 3, 8),
        ],
        naval_table=R1_NAVAL,
    )

    resolve_round(sim_run_id, 1)
    _print_round_summary(sim_run_id, 1)

    # ====================================================================
    # ROUND 2 — STRATEGIC MISSILE DEPLOYMENT + naval shuffles
    # ====================================================================
    print("\n  ===== SUBMIT ROUND 2 — ALL MISSILES OUT + NAVAL SHUFFLES =====")

    # Columbia: 2 tactical air auto-embark + ALL 9 missile reserves to (3,3) + naval
    _commit_combined(
        client, sim_run_id, scenario_id, 2, "columbia",
        rationale=(
            "R2 strategic: Columbia 2 tac-air auto-embark on col_n_06 at (4,5), "
            "ALL 9 strategic missile reserves activate at (3,3), naval reposition"
        ),
        moves=[
            _hex_move("col_a_06", 4, 5),
            _hex_move("col_a_07", 4, 5),
            _hex_move("col_m_04", 3, 3),
            _hex_move("col_m_05", 3, 3),
            _hex_move("col_m_06", 3, 3),
            _hex_move("col_m_07", 3, 3),
            _hex_move("col_m_08", 3, 3),
            _hex_move("col_m_09", 3, 3),
            _hex_move("col_m_10", 3, 3),
            _hex_move("col_m_11", 3, 3),
            _hex_move("col_m_12", 3, 3),
        ],
        naval_table=R2_NAVAL,
    )

    # Cathay: reposition 2 grounds + ALL 2 missile reserves + naval
    _commit_combined(
        client, sim_run_id, scenario_id, 2, "cathay",
        rationale=(
            "R2 strategic: Cathay reposition cat_g_03 + cat_g_04 to (6,15), "
            "ALL strategic missile reserves activate at (6,15), naval reposition"
        ),
        moves=[
            _hex_move("cat_g_03", 6, 15),
            _hex_move("cat_g_04", 6, 15),
            _hex_move("cat_m_03", 6, 15),
            _hex_move("cat_m_r1", 6, 15),
        ],
        naval_table=R2_NAVAL,
    )

    # Sarmatia: ALL 7 missile reserves to (2,16)
    _commit_combined(
        client, sim_run_id, scenario_id, 2, "sarmatia",
        rationale=(
            "R2 strategic: Sarmatia activates ALL 7 strategic missile reserves "
            "at (2,16), the existing missile silo cluster"
        ),
        moves=[
            _hex_move("sar_m_01", 2, 16),
            _hex_move("sar_m_07", 2, 16),
            _hex_move("sar_m_08", 2, 16),
            _hex_move("sar_m_09", 2, 16),
            _hex_move("sar_m_10", 2, 16),
            _hex_move("sar_m_11", 2, 16),
            _hex_move("sar_m_r1", 2, 16),
        ],
    )

    # Albion: ALL 2 missile reserves + naval
    _commit_combined(
        client, sim_run_id, scenario_id, 2, "albion",
        rationale="R2 strategic: Albion activates ALL strategic missile reserves at (3,8), naval reposition",
        moves=[
            _hex_move("alb_m_01", 3, 8),
            _hex_move("alb_m_02", 3, 8),
        ],
        naval_table=R2_NAVAL,
    )

    resolve_round(sim_run_id, 2)
    _print_round_summary(sim_run_id, 2)

    # ====================================================================
    # ROUND 3 — ALL MISSILES BACK TO BUNKER + GROUND CARRIER EMBARK
    # ====================================================================
    print("\n  ===== SUBMIT ROUND 3 — MISSILES BACK + GROUND EMBARK + NAVAL SHUFFLES =====")

    # Columbia: withdraw all 12 active missiles + naval shuffle (NO ground embark)
    _commit_combined(
        client, sim_run_id, scenario_id, 3, "columbia",
        rationale=(
            "R3 bunker: Columbia withdraws ALL 12 active strategic missiles "
            "to reserve (3 R0-active + 9 R2-deployed), naval reposition"
        ),
        moves=[
            _to_reserve("col_m_01"),
            _to_reserve("col_m_02"),
            _to_reserve("col_m_03"),
            _to_reserve("col_m_04"),
            _to_reserve("col_m_05"),
            _to_reserve("col_m_06"),
            _to_reserve("col_m_07"),
            _to_reserve("col_m_08"),
            _to_reserve("col_m_09"),
            _to_reserve("col_m_10"),
            _to_reserve("col_m_11"),
            _to_reserve("col_m_12"),
        ],
        naval_table=R3_NAVAL,
    )

    # Cathay: withdraw all 4 active missiles + 4 ground embarks (one per cathay naval)
    # Cathay naval positions (unchanged in R3): cat_n_01@(7,17), cat_n_02@(6,17),
    # cat_n_05@(7,17), cat_n_06@(8,16). (7,17) has 2 carriers → cap 2 grounds.
    _commit_combined(
        client, sim_run_id, scenario_id, 3, "cathay",
        rationale=(
            "R3 bunker + carrier ops: Cathay withdraws ALL 4 active strategic "
            "missiles AND deploys 4 ground reserves directly onto carriers — "
            "1 ground per naval (cat_n_01, cat_n_02, cat_n_05, cat_n_06)"
        ),
        moves=[
            _to_reserve("cat_m_01"),
            _to_reserve("cat_m_02"),
            _to_reserve("cat_m_03"),
            _to_reserve("cat_m_r1"),
            # Embarks: ground deploys to the naval hex → auto-embark
            _hex_move("cat_g_12", 7, 17),  # → embarks on cat_n_01 (or cat_n_05)
            _hex_move("cat_g_13", 7, 17),  # → embarks on the other naval at (7,17)
            _hex_move("cat_g_14", 6, 17),  # → embarks on cat_n_02
            _hex_move("cat_g_15", 8, 16),  # → embarks on cat_n_06
        ],
    )

    # Sarmatia: withdraw all 12 active missiles + naval shuffle
    _commit_combined(
        client, sim_run_id, scenario_id, 3, "sarmatia",
        rationale=(
            "R3 bunker: Sarmatia withdraws ALL 12 active strategic missiles "
            "to reserve (5 R0-active + 7 R2-deployed), sar_n_01 reposition"
        ),
        moves=[
            _to_reserve("sar_m_02"),
            _to_reserve("sar_m_03"),
            _to_reserve("sar_m_04"),
            _to_reserve("sar_m_05"),
            _to_reserve("sar_m_06"),
            _to_reserve("sar_m_01"),
            _to_reserve("sar_m_07"),
            _to_reserve("sar_m_08"),
            _to_reserve("sar_m_09"),
            _to_reserve("sar_m_10"),
            _to_reserve("sar_m_11"),
            _to_reserve("sar_m_r1"),
        ],
        naval_table=R3_NAVAL,
    )

    # Albion: withdraw 2 missiles + embark 1 ground (alb_n_02 already carries alb_g_02 from R0)
    # Albion naval positions (unchanged in R3): alb_n_01@(7,10), alb_n_02@(9,11)
    # alb_n_02 already has alb_g_02 embarked at R0 → 1/1 ground capacity FULL
    # alb_n_01 has only alb_a_03 (tac_air) embarked → 0/1 ground capacity AVAILABLE
    # So Albion's "1 ground per naval" requirement only needs alb_n_01 topped up.
    _commit_combined(
        client, sim_run_id, scenario_id, 3, "albion",
        rationale=(
            "R3 bunker + carrier ops: Albion withdraws ALL 2 active missiles. "
            "alb_g_03 repositions onto alb_n_01 at (7,10) — auto-embark. "
            "alb_n_02 already carries alb_g_02 from initial deployment, so "
            "the 1-ground-per-naval requirement is met for both Albion carriers."
        ),
        moves=[
            _to_reserve("alb_m_01"),
            _to_reserve("alb_m_02"),
            _hex_move("alb_g_03", 7, 10),  # repositions from (3,8) → embark on alb_n_01
        ],
    )

    resolve_round(sim_run_id, 3)
    _print_round_summary(sim_run_id, 3)

    # ====================================================================
    # ROUND 4 — POST-MISSILE SHUFFLE + naval shuffles
    # ====================================================================
    print("\n  ===== SUBMIT ROUND 4 — STRATEGIC WITHDRAWAL + NAVAL SHUFFLES =====")

    # Columbia: withdraw 2 grounds + naval
    _commit_combined(
        client, sim_run_id, scenario_id, 4, "columbia",
        rationale="R4 shuffle: Columbia withdraws col_g_05 + col_g_06 from (3,3) to reserve, naval reposition",
        moves=[
            _to_reserve("col_g_05"),
            _to_reserve("col_g_06"),
        ],
        naval_table=R4_NAVAL,
    )

    # Cathay: withdraw 1 ground + naval
    _commit_combined(
        client, sim_run_id, scenario_id, 4, "cathay",
        rationale="R4 shuffle: Cathay withdraws cat_g_01 from (6,16) to reserve, cat_n_05 reposition",
        moves=[_to_reserve("cat_g_01")],
        naval_table=R4_NAVAL,
    )

    # Sarmatia: withdraw 1 ground (no naval this round)
    _commit_combined(
        client, sim_run_id, scenario_id, 4, "sarmatia",
        rationale="R4 shuffle: Sarmatia withdraws sar_g_05 from (4,11) to reserve",
        moves=[_to_reserve("sar_g_05")],
    )

    # Albion: just naval reposition, no ground changes
    _commit_combined(
        client, sim_run_id, scenario_id, 4, "albion",
        rationale="R4 hold: Albion holds ground posture; alb_n_01 minor reposition",
        moves=[],
        naval_table=R4_NAVAL,
    )

    resolve_round(sim_run_id, 4)
    _print_round_summary(sim_run_id, 4)

    # ====================================================================
    # FINALIZE
    # ====================================================================
    finalize_run(
        sim_run_id,
        status="visible_for_review",
        notes=(
            "4-round scripted demo: ~80 movement actions across Columbia, "
            "Cathay, Sarmatia, Albion. Naval shuffles every round (6 units), "
            "ALL strategic missile reserves deployed in R2 then withdrawn in "
            "R3, Cathay/Albion ground units embark on EACH of their naval "
            "carriers in R3."
        ),
    )
    print(f"\n  [VISIBLE] '{RUN_NAME}' sim_run_id={sim_run_id}")
    print(f"  Hard-reload Observatory and pick this run from the Test Run dropdown.")
