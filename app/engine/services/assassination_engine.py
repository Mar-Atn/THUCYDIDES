"""Assassination Engine — card-based targeted killing.

Success: domestic 30%, international 20%, Levantia 50%.
Detection: 100% (always). Attribution: 50%.
Outcome on success: 50/50 kill vs survive-injured.
  Kill: target status='killed' + martyr effect (+15 support)
  Survive: sympathy effect (+10 support)
"""

from __future__ import annotations

import logging
import random

from engine.services.run_roles import get_run_role, update_role_status
from engine.services.supabase import get_client

logger = logging.getLogger(__name__)

SUCCESS_PROB_DOMESTIC = 0.30
SUCCESS_PROB_INTERNATIONAL = 0.20
SUCCESS_PROB_LEVANTIA = 0.50
KILL_VS_SURVIVE_PROB = 0.50  # <0.5 = kill, >=0.5 = survive
ATTRIBUTION_PROB = 0.50
MARTYR_SUPPORT_BOOST = 15
SYMPATHY_SUPPORT_BOOST = 10


def execute_assassination(
    sim_run_id: str,
    round_num: int,
    attacker_role: str,
    attacker_country: str,
    target_role: str,
    domestic: bool = False,
    precomputed_rolls: dict | None = None,
) -> dict:
    """Execute an assassination attempt.

    Returns ``{success, killed, detected, attributed, support_change, narrative}``.
    """
    client = get_client()
    pre = precomputed_rolls or {}

    # Get target info
    target = get_run_role(sim_run_id, target_role)
    if not target:
        return {"success": False, "narrative": f"Target {target_role} not found"}
    if target["status"] != "active":
        return {"success": False, "narrative": f"Target {target_role} is already {target['status']}"}

    target_country = target["country_code"]

    # Determine success probability
    if attacker_country == "levantia" or target_country == "levantia":
        success_prob = SUCCESS_PROB_LEVANTIA
    elif domestic:
        success_prob = SUCCESS_PROB_DOMESTIC
    else:
        success_prob = SUCCESS_PROB_INTERNATIONAL

    # Rolls
    success_roll = pre.get("success_roll", random.random())
    kill_roll = pre.get("kill_roll", random.random())
    attribution_roll = pre.get("attribution_roll", random.random())

    success = success_roll < success_prob
    attributed = attribution_roll < ATTRIBUTION_PROB
    # Detection is ALWAYS 100%
    detected = True

    killed = False
    support_change = 0
    narrative = ""

    if success:
        killed = kill_roll < KILL_VS_SURVIVE_PROB

        if killed:
            # Target killed
            update_role_status(sim_run_id, target_role, "killed",
                               changed_by=attacker_role,
                               reason=f"Assassinated in round {round_num}",
                               round_num=round_num)
            support_change = MARTYR_SUPPORT_BOOST
            narrative = f"ASSASSINATION: {target_role} ({target.get('character_name', '?')}) KILLED — martyr effect +{MARTYR_SUPPORT_BOOST} support"
        else:
            # Target survives injured
            support_change = SYMPATHY_SUPPORT_BOOST
            narrative = f"ASSASSINATION ATTEMPT: {target_role} ({target.get('character_name', '?')}) SURVIVED (injured) — sympathy +{SYMPATHY_SUPPORT_BOOST} support"

        # Apply support boost to target's country
        _apply_support_change(client, sim_run_id, round_num, target_country, support_change)
    else:
        narrative = f"ASSASSINATION ATTEMPT FAILED: attack on {target_role} ({target.get('character_name', '?')}) unsuccessful"

    # Events — ALWAYS public (detection = 100%)
    scenario_id = _get_scenario_id(client, sim_run_id)

    if attributed:
        _write_event(client, sim_run_id, scenario_id, round_num, target_country,
                     "assassination_attributed",
                     f"{narrative} — ordered by {attacker_country} ({attacker_role})",
                     {"attacker": attacker_country, "attacker_role": attacker_role,
                      "target_role": target_role, "killed": killed, "success": success,
                      "support_change": support_change, "attributed": True})
    else:
        _write_event(client, sim_run_id, scenario_id, round_num, target_country,
                     "assassination_anonymous",
                     f"{narrative} — perpetrator unknown",
                     {"target_role": target_role, "killed": killed, "success": success,
                      "support_change": support_change, "attributed": False})

    logger.info("[assassination] %s→%s: success=%s killed=%s attributed=%s support=%+d",
                attacker_role, target_role, success, killed, attributed, support_change)

    return {
        "success": success,
        "killed": killed,
        "detected": True,
        "attributed": attributed,
        "target_role": target_role,
        "target_country": target_country,
        "support_change": support_change,
        "narrative": narrative,
    }


def _apply_support_change(client, sim_run_id, round_num, target_cc, change):
    try:
        row = client.table("country_states_per_round").select("political_support") \
            .eq("sim_run_id", sim_run_id).eq("round_num", round_num) \
            .eq("country_code", target_cc).limit(1).execute().data
        if row:
            old = int(row[0]["political_support"]) if row[0].get("political_support") is not None else 50
            new = max(0, min(100, old + change))
            client.table("country_states_per_round").update({"political_support": new}) \
                .eq("sim_run_id", sim_run_id).eq("round_num", round_num) \
                .eq("country_code", target_cc).execute()
    except Exception as e:
        logger.warning("support change failed: %s", e)


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
            "sim_run_id": sim_run_id, "scenario_id": scenario_id,
            "round_num": round_num, "event_type": event_type,
            "country_code": country_code, "summary": summary, "payload": payload,
        }).execute()
    except Exception as e:
        logger.debug("event write failed: %s", e)
