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
    # All combat loads units from DB deployments table, resolves, and
    # writes results back. Action payload specifies WHO attacks WHERE.
    if action_type == "ground_attack":
        return _resolve_combat(sim_run_id, round_num, "ground", action)

    if action_type == "air_strike":
        return _resolve_combat(sim_run_id, round_num, "air", action)

    if action_type == "naval_combat":
        return _resolve_combat(sim_run_id, round_num, "naval", action)

    if action_type == "naval_bombardment":
        return _resolve_combat(sim_run_id, round_num, "bombardment", action)

    if action_type == "naval_blockade":
        return _resolve_combat(sim_run_id, round_num, "blockade", action)

    if action_type == "launch_missile_conventional":
        return _resolve_combat(sim_run_id, round_num, "missile", action)

    # ── Military: Other ──────���────────────────────────────────────────
    if action_type == "basing_rights":
        from engine.services.basing_rights_engine import grant_basing_rights, revoke_basing_rights
        guest = action.get("guest_country", "")
        if action.get("operation") == "revoke":
            return revoke_basing_rights(
                sim_run_id=sim_run_id, host_country=country_code,
                guest_country=guest, round_num=round_num)
        return grant_basing_rights(
            sim_run_id=sim_run_id, host_country=country_code,
            guest_country=guest, round_num=round_num,
            granted_by_role=role_id)

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
        from engine.services.change_leader import initiate_change_leader
        return initiate_change_leader(sim_run_id, round_num, role_id, country_code)

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
        action["round_num"] = round_num
        return propose_exchange(action, sim_run_id)

    if action_type == "accept_transaction":
        from engine.services.transaction_engine import respond_to_exchange
        return respond_to_exchange(
            transaction_id=action.get("transaction_id", ""),
            response=action.get("response", "accept"),
            sim_run_id=sim_run_id,
            rationale=action.get("rationale", ""),
            counter_offer=action.get("counter_offer"),
        )

    if action_type == "propose_agreement":
        from engine.services.agreement_engine import propose_agreement
        action["round_num"] = round_num
        return propose_agreement(action, sim_run_id)

    if action_type == "sign_agreement":
        from engine.services.agreement_engine import sign_agreement
        return sign_agreement(
            agreement_id=action.get("agreement_id", ""),
            country_code=country_code,
            role_id=role_id,
            confirm=action.get("confirm", True),
            comments=action.get("comments", ""),
        )

    # ── Diplomatic ────────────────────────────────────────────────────
    if action_type == "public_statement":
        return _log_public_statement(sim_run_id, round_num, action)

    # ── Batch Decisions (queued for Phase B, not immediate) ───────────
    if action_type in ("set_budget", "set_tariffs", "set_sanctions", "set_opec"):
        return _queue_batch_decision(sim_run_id, round_num, action_type, action)

    # ── Nuclear Chain (INITIATE → AUTHORIZE → INTERCEPT → RESOLVE) ──
    if action_type == "nuclear_launch_initiate":
        from engine.orchestrators.nuclear_chain import NuclearChainOrchestrator
        orch = NuclearChainOrchestrator()
        return orch.initiate(action, sim_run_id, round_num, initiator_role_id=role_id)

    if action_type == "nuclear_authorize":
        from engine.orchestrators.nuclear_chain import NuclearChainOrchestrator
        orch = NuclearChainOrchestrator()
        action_id = action.get("nuclear_action_id", "")
        confirm = action.get("confirm", True)
        return orch.submit_authorization(action_id, role_id, confirm, action.get("rationale", ""))

    if action_type == "nuclear_intercept":
        from engine.orchestrators.nuclear_chain import NuclearChainOrchestrator
        orch = NuclearChainOrchestrator()
        action_id = action.get("nuclear_action_id", "")
        intercept = action.get("intercept", True)
        return orch.submit_interception(action_id, country_code, intercept, action.get("rationale", ""))

    # ── Not Yet Implemented ───────────────────────────────────────────
    if action_type in ("move_units", "call_org_meeting", "meet_freely"):
        return {"success": True, "narrative": f"{action_type} acknowledged — implementation pending"}

    # ── Unknown ───────────────────────────────────────────────────────
    return {"success": False, "narrative": f"Unknown action_type: {action_type}"}


# ── Sub-dispatchers ──────────────────────────────────────────────────────

def _resolve_combat(sim_run_id: str, round_num: int, combat_type: str, action: dict) -> dict:
    """Load units from DB by hex coordinates, resolve combat, write losses back.

    Action payload expected:
        country_code: str (attacker)
        target_row: int, target_col: int (hex coordinates where combat happens)
        target_country: str (optional — auto-detected from hex)
        precomputed_rolls: dict (optional — moderator dice)
    """
    from engine.services.supabase import get_client

    client = get_client()
    attacker = action.get("country_code", "")
    target_row = action.get("target_row")
    target_col = action.get("target_col")
    target = action.get("target_country", "")
    precomputed_rolls = action.get("precomputed_rolls")

    if target_row is None or target_col is None:
        return {"success": False, "narrative": f"No target hex specified for {combat_type} (need target_row, target_col)"}

    hex_label = f"({target_row},{target_col})"

    # Load attacker units at this hex
    atk_units = client.table("deployments") \
        .select("*") \
        .eq("sim_run_id", sim_run_id) \
        .eq("country_id", attacker) \
        .eq("global_row", target_row) \
        .eq("global_col", target_col) \
        .eq("unit_status", "active") \
        .execute().data or []

    # Load all units at this hex (for defenders)
    all_units_at_hex = client.table("deployments") \
        .select("*") \
        .eq("sim_run_id", sim_run_id) \
        .eq("global_row", target_row) \
        .eq("global_col", target_col) \
        .eq("unit_status", "active") \
        .execute().data or []
    def_units = [u for u in all_units_at_hex if u["country_id"] != attacker]

    if not atk_units:
        return {"success": False, "narrative": f"No {attacker} units at hex {hex_label}"}

    # Convert DB rows to engine format — each DB row = 1 unit (individual unit model)
    def to_unit_list(units: list) -> list[dict]:
        return [{
            "unit_code": u.get("unit_id") or u["id"],
            "type": u["unit_type"],
            "country": u["country_id"],
            "deployment_id": u["id"],
        } for u in units]

    atk_list = to_unit_list(atk_units)
    def_list = to_unit_list(def_units)

    # Filter units by combat type — only relevant unit types participate
    GROUND_TYPES = {"ground"}
    AIR_TYPES = {"tactical_air"}
    NAVAL_TYPES = {"naval"}
    AD_TYPES = {"air_defense"}

    # Resolve based on combat type
    try:
        if combat_type == "ground":
            from engine.engines.military import resolve_ground_combat
            ground_atk = [u for u in atk_list if u["type"] in GROUND_TYPES]
            ground_def = [u for u in def_list if u["type"] in GROUND_TYPES]
            if not ground_atk:
                return {"success": False, "narrative": f"No ground units to attack with at {hex_label}"}
            result = resolve_ground_combat(
                attackers=ground_atk,
                defenders=ground_def,
                modifiers=action.get("modifiers"),
                precomputed_rolls=precomputed_rolls,
            )
            # Only apply losses to ground deployment rows
            ground_atk_deps = [u for u in atk_units if u["unit_type"] in GROUND_TYPES]
            ground_def_deps = [u for u in def_units if u["unit_type"] in GROUND_TYPES]
            return _apply_combat_losses(client, sim_run_id, result.__dict__, ground_atk_deps, ground_def_deps, hex_label, combat_type)

        if combat_type == "air":
            from engine.engines.military import resolve_air_strike
            air_atk = [u for u in atk_list if u["type"] in AIR_TYPES]
            air_def = [u for u in def_list if u["type"] in GROUND_TYPES | NAVAL_TYPES]  # air strikes ground/naval
            ad_list = [u for u in def_list if u["type"] in AD_TYPES]
            result = resolve_air_strike(
                attackers=air_atk,
                defenders=air_def,
                ad_units=ad_list,
                precomputed_rolls=precomputed_rolls,
            )
            return _apply_combat_losses(client, sim_run_id, result.__dict__, atk_units, def_units, hex_label, combat_type)

        if combat_type == "naval":
            from engine.engines.military import resolve_naval_combat
            naval_atk = [u for u in atk_list if u["type"] in NAVAL_TYPES]
            naval_def = [u for u in def_list if u["type"] in NAVAL_TYPES]
            result = resolve_naval_combat(
                attacker={"units": len(naval_atk), "country": attacker},
                defender={"units": len(naval_def), "country": target or "unknown"},
                modifiers=action.get("modifiers"),
                precomputed_rolls=precomputed_rolls,
            )
            naval_atk_deps = [u for u in atk_units if u["unit_type"] in NAVAL_TYPES]
            naval_def_deps = [u for u in def_units if u["unit_type"] in NAVAL_TYPES]
            return _apply_combat_losses(client, sim_run_id, result.__dict__, naval_atk_deps, naval_def_deps, hex_label, combat_type)

        # For bombardment, blockade, missile — these need complex Input objects
        # For now, return acknowledged with unit counts
        if combat_type in ("bombardment", "blockade", "missile"):
            return {
                "success": True,
                "narrative": f"{combat_type} at hex {hex_label}: {len(atk_list)} attacker units vs {len(def_list)} defender units. Full resolution wiring in progress.",
                "attacker_units": len(atk_list),
                "defender_units": len(def_list),
            }

    except Exception as e:
        logger.exception("Combat resolution failed: %s", e)
        return {"success": False, "narrative": f"Combat engine error: {e}"}

    return {"success": False, "narrative": f"Unknown combat type: {combat_type}"}


def _apply_combat_losses(client, sim_run_id: str, result: dict, atk_deployments: list, def_deployments: list, hex_label: str, combat_type: str) -> dict:
    """Apply combat losses to the deployments table.

    Individual unit model: each lost unit_code maps to a deployment row → delete it.
    Engine returns attacker_losses and defender_losses as lists of unit_code strings.
    """
    atk_loss_codes = result.get("attacker_losses", [])
    def_loss_codes = result.get("defender_losses", [])
    all_losses = set(atk_loss_codes if isinstance(atk_loss_codes, list) else []) | \
                 set(def_loss_codes if isinstance(def_loss_codes, list) else [])

    # Build unit_code → deployment_id map
    all_deps = atk_deployments + def_deployments
    code_to_dep: dict[str, str] = {}
    for dep in all_deps:
        code = dep.get("unit_id") or dep["id"]
        code_to_dep[code] = dep["id"]

    # Delete destroyed units
    deleted = 0
    for code in all_losses:
        dep_id = code_to_dep.get(code)
        if dep_id:
            client.table("deployments").delete().eq("id", dep_id).execute()
            deleted += 1

    atk_total = len(atk_loss_codes) if isinstance(atk_loss_codes, list) else 0
    def_total = len(def_loss_codes) if isinstance(def_loss_codes, list) else 0

    narrative = result.get("narrative", f"{combat_type} at {hex_label}")
    result["success"] = True
    result["losses_applied"] = True
    result["attacker_losses_count"] = atk_total
    result["defender_losses_count"] = def_total
    result["narrative"] = f"{narrative} | Losses: attacker -{atk_total}, defender -{def_total}."

    logger.info("Combat %s at %s: atk_losses=%d def_losses=%d (deleted %d rows)",
                combat_type, hex_label, atk_total, def_total, deleted)
    return result


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
    # Delete previous decision of same type for same country+round (last submission wins)
    try:
        client = get_client()
        client.table("agent_decisions").delete() \
            .eq("sim_run_id", sim_run_id) \
            .eq("round_num", round_num) \
            .eq("country_code", country_code) \
            .eq("action_type", action_type) \
            .is_("processed_at", "null") \
            .execute()
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
