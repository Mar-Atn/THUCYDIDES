"""Coup Engine — regime change attempt.

Two conspirators required. Co-conspirator must independently agree.
Probability: base 15% + modifiers (protest, stability, support).
Success: initiator becomes HoS, old HoS arrested, stability -2.
Failure: both conspirators arrested, stability -1.
"""

from __future__ import annotations

import asyncio
import logging
import random

from engine.services.run_roles import get_run_role, update_role_status
from engine.services.supabase import get_client

logger = logging.getLogger(__name__)

BASE_PROB = 0.15
PROTEST_BONUS = 0.25
LOW_STABILITY_BONUS = 0.15  # stability < 3
MED_STABILITY_BONUS = 0.05  # stability 3-4
LOW_SUPPORT_BONUS = 0.10    # support < 30%
PROB_MIN = 0.0
PROB_MAX = 0.90

SUCCESS_STABILITY_COST = -2
FAILURE_STABILITY_COST = -1


def execute_coup(
    sim_run_id: str,
    round_num: int,
    initiator_role: str,
    co_conspirator_role: str,
    country_code: str,
    precomputed_rolls: dict | None = None,
    co_conspirator_agrees: bool | None = None,
) -> dict:
    """Execute a coup attempt.

    If ``co_conspirator_agrees`` is None, asks the AI co-conspirator
    via LLM call. If explicitly True/False, skips the LLM call.

    Returns ``{success, probability, co_conspirator_agreed, stability_change, narrative}``.
    """
    client = get_client()
    pre = precomputed_rolls or {}

    # Verify both roles exist and are active
    initiator = get_run_role(sim_run_id, initiator_role)
    co_con = get_run_role(sim_run_id, co_conspirator_role)
    if not initiator or initiator["status"] != "active":
        return {"success": False, "narrative": f"Initiator {initiator_role} not active"}
    if not co_con or co_con["status"] != "active":
        return {"success": False, "narrative": f"Co-conspirator {co_conspirator_role} not active"}
    if initiator["country_code"] != country_code or co_con["country_code"] != country_code:
        return {"success": False, "narrative": "Both conspirators must be same country"}

    # Find current HoS
    hos_roles = client.table("run_roles").select("role_id,character_name") \
        .eq("sim_run_id", sim_run_id).eq("country_code", country_code) \
        .eq("is_head_of_state", True).eq("status", "active").execute().data or []
    if not hos_roles:
        return {"success": False, "narrative": f"No active HoS found for {country_code}"}
    current_hos = hos_roles[0]

    # Co-conspirator agreement
    if co_conspirator_agrees is None:
        co_conspirator_agrees = _ask_co_conspirator(
            sim_run_id, round_num, initiator_role, co_conspirator_role,
            country_code, current_hos["role_id"],
        )

    if not co_conspirator_agrees:
        scenario_id = _get_scenario_id(client, sim_run_id)
        _write_event(client, sim_run_id, scenario_id, round_num, country_code,
                     "coup_refused",
                     f"Coup attempt by {initiator_role} refused by co-conspirator {co_conspirator_role}",
                     {"initiator": initiator_role, "co_conspirator": co_conspirator_role})
        return {
            "success": False,
            "co_conspirator_agreed": False,
            "narrative": f"{co_conspirator_role} refused to participate in coup",
        }

    # Calculate probability with modifiers
    prob = BASE_PROB

    # Load country state for modifiers
    cs = client.table("country_states_per_round").select("stability,political_support") \
        .eq("sim_run_id", sim_run_id).eq("round_num", round_num) \
        .eq("country_code", country_code).limit(1).execute().data
    raw = (cs[0] if cs else {})
    stability = int(raw["stability"]) if raw.get("stability") is not None else 5
    support = int(raw["political_support"]) if raw.get("political_support") is not None else 50

    # Check for active protests (look for recent protest events)
    protest_events = client.table("observatory_events").select("id", count="exact") \
        .eq("sim_run_id", sim_run_id).eq("country_code", country_code) \
        .eq("event_type", "mass_protest").eq("round_num", round_num).execute()
    active_protest = (protest_events.count or 0) > 0

    if active_protest:
        prob += PROTEST_BONUS
    if stability < 3:
        prob += LOW_STABILITY_BONUS
    elif stability <= 4:
        prob += MED_STABILITY_BONUS
    if support < 30:
        prob += LOW_SUPPORT_BONUS

    prob = max(PROB_MIN, min(PROB_MAX, prob))

    # Roll
    success_roll = pre.get("success_roll", random.random())
    success = success_roll < prob

    scenario_id = _get_scenario_id(client, sim_run_id)

    if success:
        # Initiator becomes HoS, old HoS arrested
        # Remove HoS flag from old
        client.table("run_roles").update({"is_head_of_state": False}) \
            .eq("sim_run_id", sim_run_id).eq("role_id", current_hos["role_id"]).execute()
        update_role_status(sim_run_id, current_hos["role_id"], "arrested",
                           changed_by=initiator_role, reason="Deposed in coup", round_num=round_num)

        # Set HoS flag on initiator
        client.table("run_roles").update({"is_head_of_state": True}) \
            .eq("sim_run_id", sim_run_id).eq("role_id", initiator_role).execute()

        # Stability -2
        _apply_stability_change(client, sim_run_id, round_num, country_code, SUCCESS_STABILITY_COST)

        narrative = (f"COUP SUCCESS: {initiator_role} seizes power in {country_code}. "
                     f"{current_hos['role_id']} ({current_hos.get('character_name', '?')}) arrested. "
                     f"Stability {SUCCESS_STABILITY_COST:+d}.")

        _write_event(client, sim_run_id, scenario_id, round_num, country_code,
                     "coup_success",
                     narrative,
                     {"initiator": initiator_role, "co_conspirator": co_conspirator_role,
                      "deposed": current_hos["role_id"], "probability": round(prob, 3),
                      "stability_change": SUCCESS_STABILITY_COST})
    else:
        # Both conspirators arrested
        update_role_status(sim_run_id, initiator_role, "arrested",
                           changed_by="system", reason="Failed coup attempt", round_num=round_num)
        update_role_status(sim_run_id, co_conspirator_role, "arrested",
                           changed_by="system", reason="Failed coup co-conspirator", round_num=round_num)

        # Stability -1
        _apply_stability_change(client, sim_run_id, round_num, country_code, FAILURE_STABILITY_COST)

        narrative = (f"COUP FAILED: {initiator_role} + {co_conspirator_role} attempted coup in {country_code}. "
                     f"Both arrested. Stability {FAILURE_STABILITY_COST:+d}.")

        _write_event(client, sim_run_id, scenario_id, round_num, country_code,
                     "coup_failed",
                     narrative,
                     {"initiator": initiator_role, "co_conspirator": co_conspirator_role,
                      "probability": round(prob, 3), "stability_change": FAILURE_STABILITY_COST})

    logger.info("[coup] %s in %s: prob=%.0f%% success=%s", initiator_role, country_code, prob*100, success)

    return {
        "success": success,
        "co_conspirator_agreed": True,
        "probability": round(prob, 3),
        "stability_change": SUCCESS_STABILITY_COST if success else FAILURE_STABILITY_COST,
        "narrative": narrative,
        "modifiers": {
            "base": BASE_PROB,
            "active_protest": active_protest,
            "stability": stability,
            "support": support,
        },
    }


def _ask_co_conspirator(sim_run_id, round_num, initiator, co_con, country_code, current_hos) -> bool:
    """Ask the AI co-conspirator whether to join the coup."""
    try:
        from engine.services.llm import call_llm
        from engine.config.settings import LLMUseCase
        from engine.agents.decisions import _parse_json

        prompt = (
            f"You are {co_con}, a senior official in {country_code.upper()}.\n\n"
            f"{initiator} has approached you in secret to propose a COUP against "
            f"the current head of state ({current_hos}).\n\n"
            f"If you agree: you both attempt to seize power. Success is not guaranteed.\n"
            f"If you refuse: nothing happens (for now). {initiator} may try to find another partner.\n\n"
            f"Consider: your loyalty, your ambition, the current regime's performance, "
            f"the risk of failure (arrest if caught).\n\n"
            f"Respond with JSON ONLY:\n"
            f'{{"agree": true|false, "rationale": "string >= 30 chars"}}'
        )

        raw = asyncio.run(call_llm(
            use_case=LLMUseCase.AGENT_DECISION,
            messages=[{"role": "user", "content": prompt}],
            system="You are a senior official deciding whether to join a coup. Be concise.",
            max_tokens=200,
            temperature=0.5,
        ))
        parsed = _parse_json(raw.text)
        if parsed and isinstance(parsed.get("agree"), bool):
            logger.info("[coup] co-conspirator %s: agree=%s — %s",
                        co_con, parsed["agree"], parsed.get("rationale", "")[:80])
            return parsed["agree"]
    except Exception as e:
        logger.warning("[coup] AI co-conspirator call failed: %s — defaulting to agree", e)

    return True  # fallback: agree


def _apply_stability_change(client, sim_run_id, round_num, country_code, change):
    try:
        row = client.table("country_states_per_round").select("stability") \
            .eq("sim_run_id", sim_run_id).eq("round_num", round_num) \
            .eq("country_code", country_code).limit(1).execute().data
        if row:
            old = int(row[0]["stability"]) if row[0].get("stability") is not None else 5
            new = max(0, min(10, old + change))
            client.table("country_states_per_round").update({"stability": new}) \
                .eq("sim_run_id", sim_run_id).eq("round_num", round_num) \
                .eq("country_code", country_code).execute()
    except Exception as e:
        logger.warning("stability change failed: %s", e)


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
