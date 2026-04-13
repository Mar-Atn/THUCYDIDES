"""Mass Protest Engine — revolution attempt.

Probability: 30% base + (20-support)/100 + (3-stability)×10%. Clamp [15%,80%].
Prerequisite: stability ≤ 2 AND support < 20%.
Success: protest leader becomes HoS, old HoS deposed, stability +1, support +20.
Failure: leader imprisoned, stability -1, support -5.
"""

from __future__ import annotations

import logging
import random

from engine.services.run_roles import get_run_role, update_role_status
from engine.services.supabase import get_client

logger = logging.getLogger(__name__)

STABILITY_THRESHOLD = 2
SUPPORT_THRESHOLD = 20


def execute_mass_protest(
    sim_run_id: str,
    round_num: int,
    leader_role: str,
    country_code: str,
    precomputed_rolls: dict | None = None,
) -> dict:
    """Execute a mass protest / revolution attempt."""
    client = get_client()
    pre = precomputed_rolls or {}

    leader = get_run_role(sim_run_id, leader_role)
    if not leader or leader["status"] != "active":
        return {"success": False, "narrative": f"Leader {leader_role} not active"}

    # Load country state
    cs = client.table("country_states_per_round").select("stability,political_support") \
        .eq("sim_run_id", sim_run_id).eq("round_num", round_num) \
        .eq("country_code", country_code).limit(1).execute().data
    raw = (cs[0] if cs else {})
    stability = int(raw["stability"]) if raw.get("stability") is not None else 5
    support = int(raw["political_support"]) if raw.get("political_support") is not None else 50

    # Check prerequisites
    if stability > STABILITY_THRESHOLD:
        return {"success": False, "narrative": f"Stability {stability} > {STABILITY_THRESHOLD} — protest conditions not met"}
    if support >= SUPPORT_THRESHOLD:
        return {"success": False, "narrative": f"Support {support}% >= {SUPPORT_THRESHOLD}% — protest conditions not met"}

    # Calculate probability
    prob = 0.30 + (20 - support) / 100.0 + (3 - stability) * 0.10
    prob = max(0.15, min(0.80, prob))

    success_roll = pre.get("success_roll", random.random())
    success = success_roll < prob

    scenario_id = _get_scenario_id(client, sim_run_id)

    if success:
        # Find current HoS
        hos_roles = client.table("run_roles").select("role_id,character_name") \
            .eq("sim_run_id", sim_run_id).eq("country_code", country_code) \
            .eq("is_head_of_state", True).eq("status", "active").execute().data or []

        if hos_roles:
            old_hos = hos_roles[0]
            client.table("run_roles").update({"is_head_of_state": False}) \
                .eq("sim_run_id", sim_run_id).eq("role_id", old_hos["role_id"]).execute()
            update_role_status(sim_run_id, old_hos["role_id"], "deposed",
                               changed_by=leader_role, reason="Deposed by mass protest", round_num=round_num)

        # Leader becomes HoS
        client.table("run_roles").update({"is_head_of_state": True}) \
            .eq("sim_run_id", sim_run_id).eq("role_id", leader_role).execute()

        # Stability +1, support +20
        _update_country(client, sim_run_id, round_num, country_code,
                        stability_delta=1, support_delta=20)

        narrative = (f"REVOLUTION SUCCESS: {leader_role} leads mass protest in {country_code}. "
                     f"Regime toppled. Stability +1, support +20.")

        _write_event(client, sim_run_id, scenario_id, round_num, country_code,
                     "mass_protest_success", narrative,
                     {"leader": leader_role, "probability": round(prob, 3),
                      "deposed": hos_roles[0]["role_id"] if hos_roles else None})
    else:
        # Leader imprisoned
        update_role_status(sim_run_id, leader_role, "arrested",
                           changed_by="system", reason="Protest crushed, leader imprisoned",
                           round_num=round_num)

        # Stability -1, support -5
        _update_country(client, sim_run_id, round_num, country_code,
                        stability_delta=-1, support_delta=-5)

        narrative = (f"PROTEST CRUSHED: {leader_role}'s mass protest in {country_code} fails. "
                     f"Leader imprisoned. Stability -1, support -5.")

        _write_event(client, sim_run_id, scenario_id, round_num, country_code,
                     "mass_protest_failed", narrative,
                     {"leader": leader_role, "probability": round(prob, 3)})

    logger.info("[protest] %s in %s: prob=%.0f%% success=%s", leader_role, country_code, prob*100, success)

    return {
        "success": success,
        "probability": round(prob, 3),
        "narrative": narrative,
    }


def _update_country(client, sim_run_id, round_num, cc, stability_delta, support_delta):
    try:
        row = client.table("country_states_per_round").select("stability,political_support") \
            .eq("sim_run_id", sim_run_id).eq("round_num", round_num) \
            .eq("country_code", cc).limit(1).execute().data
        if row:
            old_s = int(row[0]["stability"]) if row[0].get("stability") is not None else 5
            old_p = int(row[0]["political_support"]) if row[0].get("political_support") is not None else 50
            client.table("country_states_per_round").update({
                "stability": max(0, min(10, old_s + stability_delta)),
                "political_support": max(0, min(100, old_p + support_delta)),
            }).eq("sim_run_id", sim_run_id).eq("round_num", round_num) \
              .eq("country_code", cc).execute()
    except Exception as e:
        logger.warning("country update failed: %s", e)


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
