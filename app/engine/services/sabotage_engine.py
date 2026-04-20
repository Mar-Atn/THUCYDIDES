"""Sabotage Engine — covert destructive operations.

50% success. On success: damage applied by target_type.
50% detection: target learns sabotage happened.
50% attribution (if detected): everyone learns who did it.

Detection/attribution are independent of success — a failed attempt
can still be detected.
"""

from __future__ import annotations

import logging
import random

from engine.services.supabase import get_client

logger = logging.getLogger(__name__)

SUCCESS_PROB = 0.50
DETECTION_PROB = 1.0   # always detected (2026-04-20)
ATTRIBUTION_PROB = 0.50

# Damage constants per target_type
INFRASTRUCTURE_COIN_DAMAGE = 1
NUCLEAR_PROGRESS_DAMAGE = 0.30  # -30% of current progress
MILITARY_DESTROY_PROB = 0.50    # 50% chance to destroy 1 unit


def execute_sabotage(
    sim_run_id: str,
    round_num: int,
    attacker_country: str,
    attacker_role: str,
    target_country: str,
    target_type: str,
    precomputed_rolls: dict | None = None,
) -> dict:
    """Execute a sabotage operation.

    Returns ``{success, detected, attributed, damage, narrative}``.
    """
    client = get_client()
    pre = precomputed_rolls or {}

    # --- ROLLS ---
    success_roll = pre.get("success_roll", random.random())
    detection_roll = pre.get("detection_roll", random.random())
    attribution_roll = pre.get("attribution_roll", random.random())

    success = success_roll < SUCCESS_PROB
    detected = detection_roll < DETECTION_PROB
    attributed = detected and (attribution_roll < ATTRIBUTION_PROB)

    damage_description = ""
    damage_value = None

    # --- APPLY DAMAGE (if success) ---
    if success:
        if target_type == "infrastructure":
            damage_value = _damage_infrastructure(client, sim_run_id, round_num, target_country)
            damage_description = "Infrastructure sabotage led to substantial economic losses."

        elif target_type == "nuclear_tech":
            damage_value = _damage_nuclear(client, sim_run_id, round_num, target_country)
            damage_description = "R&D facility destroyed, slowing nuclear technology progress."

        elif target_type == "military":
            mil_roll = pre.get("military_roll", random.random())
            damage_value = _damage_military(client, sim_run_id, round_num, target_country, mil_roll)
            if damage_value:
                damage_description = "One military unit destroyed in covert operation."
            else:
                damage_description = "Military sabotage attempted but failed to destroy any assets."

    # --- NARRATIVE ---
    tc_upper = target_country.upper()
    if success:
        narrative = f"Covert operation against {tc_upper} successful. {damage_description}"
    else:
        narrative = f"Covert operation against {tc_upper} failed. Operatives were unable to complete the mission."

    # --- EVENTS ---
    scenario_id = _get_scenario_id(client, sim_run_id)

    # Always log for attacker (private)
    _write_event(client, sim_run_id, scenario_id, round_num, attacker_country,
                 "sabotage_result",
                 f"[CLASSIFIED] {narrative} (detected={detected}, attributed={attributed})",
                 {"success": success, "target_country": target_country,
                  "target_type": target_type, "detected": detected,
                  "attributed": attributed, "damage": damage_description})

    # If detected: target learns something happened
    if detected:
        if attributed:
            # Public news: everyone knows who did it
            _write_event(client, sim_run_id, scenario_id, round_num, target_country,
                         "sabotage_detected_attributed",
                         f"SABOTAGE {'succeeded' if success else 'attempt failed'}: "
                         f"{attacker_country} targeted {target_country}'s {target_type}"
                         + (f" — {damage_description}" if success else ""),
                         {"attacker": attacker_country, "target": target_country,
                          "target_type": target_type, "success": success,
                          "attributed": True})
        else:
            # Target knows but not who
            _write_event(client, sim_run_id, scenario_id, round_num, target_country,
                         "sabotage_detected_anonymous",
                         f"SABOTAGE {'succeeded' if success else 'attempt failed'}: "
                         f"unknown actor targeted {target_country}'s {target_type}"
                         + (f" — {damage_description}" if success else ""),
                         {"target": target_country, "target_type": target_type,
                          "success": success, "attributed": False})

    logger.info("[sabotage] %s→%s (%s): success=%s detected=%s attributed=%s",
                attacker_country, target_country, target_type, success, detected, attributed)

    return {
        "success": success,
        "detected": detected,
        "attributed": attributed,
        "target_country": target_country,
        "target_type": target_type,
        "damage": damage_description,
        "rolls": {
            "success": round(success_roll, 4),
            "detection": round(detection_roll, 4),
            "attribution": round(attribution_roll, 4),
        },
        "narrative": narrative,
    }


# ---------------------------------------------------------------------------
# Damage functions
# ---------------------------------------------------------------------------


def _damage_infrastructure(client, sim_run_id, round_num, target_cc) -> float:
    """Remove 1 coin from target treasury."""
    try:
        row = client.table("country_states_per_round").select("treasury") \
            .eq("sim_run_id", sim_run_id).eq("round_num", round_num) \
            .eq("country_code", target_cc).limit(1).execute().data
        if row:
            old = float(row[0].get("treasury") or 0)
            new = max(0, old - INFRASTRUCTURE_COIN_DAMAGE)
            client.table("country_states_per_round").update({"treasury": round(new, 2)}) \
                .eq("sim_run_id", sim_run_id).eq("round_num", round_num) \
                .eq("country_code", target_cc).execute()
            return INFRASTRUCTURE_COIN_DAMAGE
    except Exception as e:
        logger.warning("infrastructure damage failed: %s", e)
    return 0


def _damage_nuclear(client, sim_run_id, round_num, target_cc) -> float:
    """Reduce nuclear R&D progress by 30%."""
    try:
        row = client.table("country_states_per_round").select("nuclear_rd_progress") \
            .eq("sim_run_id", sim_run_id).eq("round_num", round_num) \
            .eq("country_code", target_cc).limit(1).execute().data
        if row:
            old = float(row[0].get("nuclear_rd_progress") or 0)
            reduction = old * NUCLEAR_PROGRESS_DAMAGE
            new = max(0, old - reduction)
            client.table("country_states_per_round").update(
                {"nuclear_rd_progress": round(new, 4)}
            ).eq("sim_run_id", sim_run_id).eq("round_num", round_num) \
             .eq("country_code", target_cc).execute()
            return reduction
    except Exception as e:
        logger.warning("nuclear damage failed: %s", e)
    return 0


def _damage_military(client, sim_run_id, round_num, target_cc, roll) -> str | None:
    """50% chance to destroy 1 random active unit. Returns unit_code or None."""
    if roll >= MILITARY_DESTROY_PROB:
        return None  # roll failed

    try:
        res = client.table("unit_states_per_round").select("unit_code") \
            .eq("sim_run_id", sim_run_id).eq("round_num", round_num) \
            .eq("country_code", target_cc).eq("status", "active") \
            .execute().data or []
        if not res:
            return None
        victim = random.choice(res)
        unit_code = victim["unit_code"]
        client.table("unit_states_per_round").update({
            "status": "destroyed",
            "global_row": None, "global_col": None,
        }).eq("sim_run_id", sim_run_id).eq("round_num", round_num) \
          .eq("unit_code", unit_code).execute()
        return unit_code
    except Exception as e:
        logger.warning("military sabotage failed: %s", e)
    return None


def _get_scenario_id(client, sim_run_id):
    try:
        r = client.table("sim_runs").select("scenario_id").eq("id", sim_run_id).limit(1).execute()
        return r.data[0]["scenario_id"] if r.data else None
    except Exception:
        return None


def _write_event(client, sim_run_id, scenario_id, round_num, country_code, event_type, summary, payload):
    if not scenario_id:
        return
    try:
        client.table("observatory_events").insert({
            "sim_run_id": sim_run_id,
            "scenario_id": scenario_id,
            "round_num": round_num,
            "event_type": event_type,
            "country_code": country_code,
            "summary": summary,
            "payload": payload,
        }).execute()
    except Exception as e:
        logger.debug("event write failed: %s", e)
