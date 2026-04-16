"""Action Dispatcher — routes submitted actions to their engines.

This is the GLUE between agent/human action submissions and the engine layer.
Every action submitted during Phase A is dispatched here for immediate resolution.

Action type names are CANONICAL — they match role_actions.action_id in the DB.
Source of truth: M9 role_actions table (32 action types as of 2026-04-16).

See CONTRACT_ROUND_FLOW.md for the canonical round flow.
"""

from __future__ import annotations

import logging
from typing import Any

from engine.services.supabase import get_client
from engine.services.common import get_scenario_id, write_event

logger = logging.getLogger(__name__)


def dispatch_action(
    sim_run_id: str,
    round_num: int,
    action: dict[str, Any],
) -> dict[str, Any]:
    """Dispatch a single action to its engine and return the result.

    Args:
        sim_run_id: Active sim run
        round_num: Current round number
        action: Action payload with at minimum {action_type, role_id, ...}

    Returns:
        Engine result dict with at minimum {success: bool, narrative: str}
    """
    action_type = action.get("action_type", "")
    role_id = action.get("role_id", "")
    country_code = action.get("country_code", "")

    logger.info("[dispatch] %s by %s (%s) in round %d",
                action_type, role_id, country_code, round_num)

    try:
        result = _route(sim_run_id, round_num, action_type, action)
    except Exception as e:
        logger.exception("[dispatch] %s failed: %s", action_type, e)
        result = {"success": False, "narrative": f"Engine error: {e}"}

    # Log to observatory
    _log_dispatch(sim_run_id, round_num, action_type, role_id, country_code, result)

    return result


def _route(sim_run_id: str, round_num: int, action_type: str, action: dict) -> dict:
    """Route to the correct engine based on action_type.

    Action type names are CANONICAL DB names from role_actions.action_id.
    """
    role_id = action.get("role_id", "")
    country_code = action.get("country_code", "")

    # ── Military: Combat ──────────────────────────────────────────────
    if action_type == "ground_attack":
        from engine.engines.military import resolve_ground_combat
        return resolve_ground_combat(
            attacker_units=action.get("attacker_units", []),
            defender_units=action.get("defender_units", []),
            terrain=action.get("terrain", "open"),
            modifiers=action.get("modifiers", {}),
            precomputed_rolls=action.get("precomputed_rolls"),
        ).__dict__

    if action_type == "air_strike":
        from engine.engines.military import resolve_air_strike
        return resolve_air_strike(
            attacker_units=action.get("attacker_units", []),
            target_units=action.get("target_units", []),
            ad_units=action.get("ad_units", []),
            precomputed_rolls=action.get("precomputed_rolls"),
        ).__dict__

    if action_type == "naval_combat":
        from engine.engines.military import resolve_naval_combat
        return resolve_naval_combat(
            attacker_units=action.get("attacker_units", []),
            defender_units=action.get("defender_units", []),
            modifiers=action.get("modifiers", {}),
            precomputed_rolls=action.get("precomputed_rolls"),
        ).__dict__

    if action_type == "naval_bombardment":
        from engine.engines.military import resolve_naval_bombardment
        return resolve_naval_bombardment(
            naval_units=action.get("naval_units", []),
            target_units=action.get("target_units", []),
            precomputed_rolls=action.get("precomputed_rolls"),
        ).__dict__

    if action_type == "naval_blockade":
        from engine.engines.military import resolve_blockade
        return resolve_blockade(
            imposer_units=action.get("imposer_units", []),
            zone_id=action.get("zone_id", ""),
            precomputed_rolls=action.get("precomputed_rolls"),
        ).__dict__

    if action_type == "launch_missile_conventional":
        from engine.engines.military import resolve_missile_strike
        return resolve_missile_strike(
            launcher_unit=action.get("launcher_unit", {}),
            target_units=action.get("target_units", []),
            precomputed_rolls=action.get("precomputed_rolls"),
        ).__dict__

    # ── Military: Other ──────���────────────────────────────────────────
    if action_type == "basing_rights":
        from engine.services.basing_rights_engine import grant_basing_rights, revoke_basing_rights
        if action.get("operation") == "revoke":
            return revoke_basing_rights(
                sim_run_id, round_num, role_id, country_code,
                action.get("guest_country"), action.get("zone_id"))
        return grant_basing_rights(
            sim_run_id, round_num, role_id, country_code,
            action.get("guest_country"), action.get("zone_id"))

    if action_type == "martial_law":
        from engine.services.martial_law_engine import execute_martial_law
        return execute_martial_law(sim_run_id, round_num, role_id, country_code)

    if action_type == "nuclear_test":
        from engine.engines.military import resolve_nuclear_test
        return resolve_nuclear_test(
            country_code=country_code,
            nuclear_level=action.get("nuclear_level", 0),
            precomputed_rolls=action.get("precomputed_rolls"),
        ).__dict__

    # ── Covert Ops ────────────────────────────────���───────────────────
    if action_type == "covert_operation":
        return _dispatch_covert(sim_run_id, round_num, action)

    if action_type == "intelligence":
        from engine.services.intelligence_engine import generate_intelligence_report
        return generate_intelligence_report(
            sim_run_id, round_num, role_id, country_code,
            action.get("target_country"))

    # ── Political ────��────────────────────────────────────────────────
    if action_type == "arrest":
        from engine.services.arrest_engine import request_arrest
        return request_arrest(
            sim_run_id, round_num, role_id, action.get("target_role"),
            country_code)

    if action_type == "assassination":
        from engine.services.assassination_engine import execute_assassination
        return execute_assassination(
            sim_run_id, round_num, role_id, country_code,
            action.get("target_role"),
            domestic=action.get("domestic", True))

    if action_type == "change_leader":
        logger.info("change_leader initiated by %s in %s — requires M4 for vote phases",
                     role_id, country_code)
        return {"success": True, "narrative": f"Change of leader initiated by {role_id} in {country_code}. Voting phase required."}

    if action_type == "reassign_types":
        from engine.services.power_assignments import reassign_power
        return reassign_power(
            sim_run_id, role_id, country_code,
            action.get("power_type"), action.get("new_holder_role"))

    if action_type == "self_nominate":
        from engine.services.election_engine import submit_nomination
        return submit_nomination(
            sim_run_id, round_num, role_id,
            action.get("election_type"), action.get("election_round"))

    if action_type == "cast_vote":
        from engine.services.election_engine import cast_vote
        return cast_vote(
            sim_run_id, round_num, role_id,
            action.get("candidate_role_id"), action.get("election_type"))

    # ── Transactions / Agreements ──────────────────���──────────────────
    if action_type == "propose_transaction":
        from engine.services.transaction_engine import propose_exchange
        return propose_exchange(sim_run_id, round_num, action)

    if action_type == "accept_transaction":
        from engine.services.transaction_engine import respond_to_exchange
        return respond_to_exchange(
            sim_run_id, action.get("transaction_id"),
            action.get("response", "accept"), action.get("counter_offer"))

    if action_type == "propose_agreement":
        from engine.services.agreement_engine import propose_agreement
        return propose_agreement(sim_run_id, round_num, action)

    if action_type == "sign_agreement":
        from engine.services.agreement_engine import sign_agreement
        return sign_agreement(
            sim_run_id, action.get("agreement_id"), role_id)

    # ── Diplomatic ────────────────────────────────────────────────────
    if action_type == "public_statement":
        return _log_public_statement(sim_run_id, round_num, action)

    # ── Batch Decisions (queued for Phase B, not immediate) ───────────
    if action_type in ("set_budget", "set_tariffs", "set_sanctions", "set_opec"):
        return _queue_batch_decision(sim_run_id, round_num, action_type, action)

    # ── Not Yet Implemented (M4 Phase 4+) ���────────────────────────��───
    if action_type in ("move_units", "call_org_meeting", "meet_freely",
                        "nuclear_authorize", "nuclear_intercept", "nuclear_launch_initiate"):
        return {"success": True, "narrative": f"{action_type} acknowledged — full implementation in M4 Phase 4"}

    # ── Unknown ───────────────────────────────────────────────────────
    return {"success": False, "narrative": f"Unknown action_type: {action_type}"}


# ── Sub-dispatchers ──────────────────────────────────────────────────────

def _dispatch_covert(sim_run_id: str, round_num: int, action: dict) -> dict:
    """Dispatch covert operation to the correct engine based on op_type."""
    op_type = action.get("op_type", "")
    role_id = action.get("role_id", "")
    country_code = action.get("country_code", "")

    if op_type == "intelligence":
        from engine.services.intelligence_engine import generate_intelligence_report
        return generate_intelligence_report(
            sim_run_id, round_num, role_id, country_code,
            action.get("target_country"))

    if op_type == "sabotage":
        from engine.services.sabotage_engine import execute_sabotage
        return execute_sabotage(
            sim_run_id, round_num, role_id, country_code,
            action.get("target_country"), action.get("target_type", "infrastructure"))

    if op_type == "propaganda":
        from engine.services.propaganda_engine import execute_propaganda
        return execute_propaganda(
            sim_run_id, round_num, role_id, country_code,
            action.get("target_country"), action.get("intent", "destabilize"),
            action.get("content", ""))

    if op_type == "election_meddling":
        from engine.services.election_meddling_engine import execute_election_meddling
        return execute_election_meddling(
            sim_run_id, round_num, role_id, country_code,
            action.get("target_country"), action.get("direction", "boost"),
            action.get("candidate", ""))

    return {"success": False, "narrative": f"Unknown covert op_type: {op_type}"}


def _queue_batch_decision(sim_run_id: str, round_num: int, action_type: str, action: dict) -> dict:
    """Queue a batch decision for Phase B processing.

    Batch decisions (budget, tariffs, sanctions, OPEC) are submitted during Phase A
    but only processed by the economic engine during Phase B.
    """
    role_id = action.get("role_id", "")
    country_code = action.get("country_code", "")

    # Store in agent_decisions table for Phase B pickup
    try:
        client = get_client()
        client.table("agent_decisions").insert({
            "sim_run_id": sim_run_id,
            "round_num": round_num,
            "country_code": country_code,
            "action_type": action_type,
            "action_payload": action,
            "validation_status": "valid",
        }).execute()
    except Exception as e:
        logger.warning("Failed to queue batch decision %s: %s", action_type, e)
        return {"success": True, "narrative": f"{action_type} recorded (queue write failed: {e})"}

    return {"success": True, "narrative": f"{action_type} by {role_id} ({country_code}) queued for Phase B processing"}


def _log_public_statement(sim_run_id: str, round_num: int, action: dict) -> dict:
    """Log a public statement to observatory (no engine processing)."""
    client = get_client()
    scenario_id = get_scenario_id(client, sim_run_id)
    role_id = action.get("role_id", "unknown")
    statement = action.get("content", "")
    country_code = action.get("country_code", "")

    narrative = f"PUBLIC STATEMENT by {role_id}: {statement[:200]}"
    write_event(client, sim_run_id, scenario_id, round_num, country_code,
                "public_statement", narrative,
                {"role_id": role_id, "content": statement},
                phase="A", category="diplomatic", role_name=role_id)

    return {"success": True, "narrative": narrative}


def _log_dispatch(sim_run_id, round_num, action_type, role_id, country_code, result):
    """Log action dispatch result for audit trail."""
    success = result.get("success", False)
    level = logging.INFO if success else logging.WARNING
    logger.log(level, "[dispatch] %s by %s → %s",
               action_type, role_id, "OK" if success else "FAILED")
