"""Assassination Engine — covert targeted killing.

Approved design (2026-04-20):
  - Who: Security position only. 3 attempts per SIM.
  - Target: Any active role, any country (domestic + international). HoS can be targeted.
  - Success: 20% flat. Levantia bonus: 50%.
  - Outcome: Success = target killed (out for rest of SIM). No survive/injured.
  - Detection: Always 100% — public knows it happened.
  - Attribution: 50% chance attacker is identified.
  - Kill effect: Target status → killed. Country stability +1.5 (martyr).
  - Failed: No status change, no stability effect.
  - Moderator: Confirmation required (unless auto-approve).
"""

from __future__ import annotations

from engine.services.common import get_scenario_id, write_event

import logging
import random

from engine.config.position_actions import has_position
from engine.services.supabase import get_client

logger = logging.getLogger(__name__)

from engine.config.probabilities import (
    ASSASSINATION_SUCCESS as SUCCESS_PROB,
    ASSASSINATION_SUCCESS_LEVANTIA as SUCCESS_PROB_LEVANTIA,
    ASSASSINATION_ATTRIBUTION as ATTRIBUTION_PROB,
    ASSASSINATION_MARTYR_STABILITY as MARTYR_STABILITY_BOOST,
)


def execute_assassination(
    sim_run_id: str,
    round_num: int,
    attacker_role: str,
    attacker_country: str,
    target_role: str,
    precomputed_rolls: dict | None = None,
) -> dict:
    """Execute an assassination attempt.

    Returns ``{success, killed, detected, attributed, narrative}``.
    """
    client = get_client()
    pre = precomputed_rolls or {}

    # Validate attacker has security position
    attacker_data = client.table("roles") \
        .select("id, character_name, positions, country_code") \
        .eq("sim_run_id", sim_run_id).eq("id", attacker_role).limit(1).execute().data
    if not attacker_data:
        return {"success": False, "narrative": f"Attacker {attacker_role} not found"}
    attacker = attacker_data[0]
    if not has_position(attacker, "security"):
        return {"success": False, "narrative": f"{attacker_role} does not have security position — cannot assassinate"}

    attacker_name = attacker["character_name"]
    attacker_cc = attacker["country_code"]

    # Get target info
    target_data = client.table("roles") \
        .select("id, character_name, status, country_code") \
        .eq("sim_run_id", sim_run_id).eq("id", target_role).limit(1).execute().data
    if not target_data:
        return {"success": False, "narrative": f"Target {target_role} not found"}
    target = target_data[0]

    if target["status"] != "active":
        return {"success": False, "narrative": f"Target {target_role} is already {target['status']}"}

    target_name = target["character_name"]
    target_cc = target["country_code"]

    # Determine success probability
    if attacker_cc == "levantia" or target_cc == "levantia":
        success_prob = SUCCESS_PROB_LEVANTIA
    else:
        success_prob = SUCCESS_PROB

    # Rolls
    success_roll = pre.get("success_roll", random.random())
    attribution_roll = pre.get("attribution_roll", random.random())

    success = success_roll < success_prob
    attributed = attribution_roll < ATTRIBUTION_PROB

    if success:
        # Target killed — out for rest of SIM
        client.table("roles").update({
            "status": "killed",
            "status_detail": {
                "killed_by": attacker_role if attributed else "unknown",
                "killed_by_name": attacker_name if attributed else "unknown",
                "killed_by_country": attacker_cc if attributed else "unknown",
                "round": round_num,
                "attributed": attributed,
            },
        }).eq("sim_run_id", sim_run_id).eq("id", target_role).execute()

        # Martyr effect — target country stability +1.5
        _apply_stability_change(client, sim_run_id, target_cc, MARTYR_STABILITY_BOOST)

        if attributed:
            narrative = (f"There is sufficient evidence {attacker_name} ({attacker_cc.upper()}) was behind "
                         f"the successful attempt to assassinate {target_name}.")
        else:
            narrative = (f"{target_name} has been assassinated in {target_cc.upper()}. "
                         f"Perpetrators unknown.")
    else:
        # Failed attempt
        if attributed:
            narrative = (f"There is sufficient evidence {attacker_name} ({attacker_cc.upper()}) was behind "
                         f"an unsuccessful attempt to assassinate {target_name}.")
        else:
            narrative = (f"An unsuccessful assassination attempt on {target_name} in {target_cc.upper()}. "
                         f"Perpetrators unknown.")

    # Events — ALWAYS public (detection = 100%)
    scenario_id = get_scenario_id(client, sim_run_id)
    event_type = "assassination_attributed" if attributed else "assassination_anonymous"
    payload = {
        "target_role": target_role,
        "target_name": target_name,
        "target_country": target_cc,
        "success": success,
        "attributed": attributed,
        "category": "political",
    }
    if attributed:
        payload["attacker_role"] = attacker_role
        payload["attacker_name"] = attacker_name
        payload["attacker_country"] = attacker_cc

    write_event(client, sim_run_id, scenario_id, round_num, target_cc,
                 event_type, narrative, payload, category="political")

    logger.info("[assassination] %s(%s)→%s(%s): success=%s attributed=%s",
                attacker_role, attacker_cc, target_role, target_cc, success, attributed)

    return {
        "success": True,  # action executed (not whether target died)
        "killed": success,
        "detected": True,
        "attributed": attributed,
        "target_role": target_role,
        "target_name": target_name,
        "target_country": target_cc,
        "narrative": narrative,
    }


def _apply_stability_change(client, sim_run_id, country_code, change):
    """Apply stability change to country (martyr effect)."""
    try:
        row = client.table("countries").select("stability") \
            .eq("sim_run_id", sim_run_id).eq("id", country_code).limit(1).execute().data
        if row:
            old = float(row[0]["stability"]) if row[0].get("stability") is not None else 5.0
            new = max(0.0, min(10.0, old + change))
            client.table("countries").update({"stability": new}) \
                .eq("sim_run_id", sim_run_id).eq("id", country_code).execute()
            logger.info("[assassination] %s stability: %.1f → %.1f (+%.1f martyr)",
                        country_code, old, new, change)
    except Exception as e:
        logger.warning("stability change failed: %s", e)


