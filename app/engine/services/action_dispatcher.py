"""Action Dispatcher — routes submitted actions to their engines.

This is the GLUE between agent/human action submissions and the engine layer.
Every action submitted during Phase A is dispatched here for immediate resolution.

Action type names are CANONICAL — they match role_actions.action_id in the DB.
Source of truth: M9 role_actions table (33 action types as of 2026-04-17).

See CONTRACT_ROUND_FLOW.md for the canonical round flow.
"""

from __future__ import annotations

import logging
import random
from typing import Any

from engine.services.supabase import get_client
from engine.services.common import get_scenario_id, write_event
from engine.config.map_config import hex_neighbors_bounded, GLOBAL_HEX_OWNERS

logger = logging.getLogger(__name__)


def _update_hex_control(
    client, sim_run_id: str, row: int, col: int,
    owner: str, controlled_by: str, round_num: int, action: str,
    theater: str | None = None, theater_row: int | None = None, theater_col: int | None = None,
) -> None:
    """Record hex occupation change in hex_control table (upsert)."""
    client.table("hex_control").upsert({
        "sim_run_id": sim_run_id,
        "global_row": row,
        "global_col": col,
        "owner": owner,
        "controlled_by": controlled_by if controlled_by != owner else None,
        "captured_round": round_num,
        "captured_by_action": action,
        "theater": theater,
        "theater_row": theater_row,
        "theater_col": theater_col,
        "updated_at": "now()",
    }, on_conflict="sim_run_id,global_row,global_col").execute()


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

    # After any action that may destroy units, check blockade integrity
    COMBAT_ACTIONS = {"ground_attack", "ground_move", "air_strike", "naval_combat",
                      "naval_bombardment", "launch_missile_conventional"}
    if action_type in COMBAT_ACTIONS and result.get("success"):
        try:
            from engine.services.blockade_engine import check_blockade_integrity
            blockade_changes = check_blockade_integrity(sim_run_id)
            if blockade_changes:
                result["blockade_changes"] = blockade_changes
                logger.info("[dispatch] Blockade integrity: %s", blockade_changes)
        except Exception as e:
            logger.warning("Blockade integrity check failed: %s", e)

    # Log to observatory
    _log_dispatch(sim_run_id, round_num, action_type, role_id, country_code, result)

    # Enqueue events for AI agents affected by this action
    if result.get("success"):
        _enqueue_for_ai_agents(sim_run_id, round_num, action_type, action, result)

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

    if action_type == "ground_move":
        return _ground_advance(sim_run_id, round_num, action)

    if action_type == "air_strike":
        return _resolve_combat(sim_run_id, round_num, "air", action)

    if action_type == "naval_combat":
        return _resolve_combat(sim_run_id, round_num, "naval", action)

    if action_type == "naval_bombardment":
        return _resolve_combat(sim_run_id, round_num, "bombardment", action)

    if action_type == "naval_blockade":
        from engine.services.blockade_engine import establish_blockade, lift_blockade, reduce_blockade
        operation = action.get("operation", "establish")
        zone_id = action.get("zone_id", "")
        level = action.get("level", "full")
        role_id = action.get("role_id", "")
        country_code = action.get("country_code", "")
        if operation == "establish":
            return establish_blockade(sim_run_id, country_code, zone_id, level, round_num, role_id)
        elif operation == "lift":
            return lift_blockade(sim_run_id, country_code, zone_id, round_num, role_id)
        elif operation == "reduce":
            return reduce_blockade(sim_run_id, country_code, zone_id, round_num, role_id)
        else:
            return {"success": False, "narrative": f"Unknown blockade operation: {operation}"}

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
        return _execute_nuclear_test(sim_run_id, round_num, action)

    # ── Covert Ops ────────────────────────────────���───────────────────
    if action_type == "covert_operation":
        return _dispatch_covert(sim_run_id, round_num, action)

    if action_type == "intelligence":
        from engine.services.intelligence_engine import generate_intelligence_report
        question = action.get("question", "General situation assessment")
        return generate_intelligence_report(
            sim_run_id, round_num, question, country_code, role_id)

    # ── Political ────��────────────────────────────────────────────────
    if action_type == "release_arrest":
        from engine.services.arrest_engine import release_role
        target = (action.get("changes") or {}).get("target_role") or action.get("target_role", "")
        result = release_role(sim_run_id, role_id, target, round_num)
        if result.get("success"):
            scenario_id = get_scenario_id(client, sim_run_id)
            write_event(client, sim_run_id, scenario_id, round_num, country_code,
                        "release_arrest", result.get("message", ""),
                        {"released_role": target, "by": role_id},
                        phase="A", category="political")
        return result

    if action_type == "arrest":
        from engine.services.arrest_engine import request_arrest
        target = (action.get("changes") or {}).get("target_role") or action.get("target_role", "")
        justification = action.get("rationale", "")
        result = request_arrest(sim_run_id, role_id, target, justification, round_num)
        # Write public observatory event on success
        if result.get("success"):
            arrested_name = result.get("arrested_name", target)
            scenario_id = get_scenario_id(client, sim_run_id)
            write_event(client, sim_run_id, scenario_id, round_num, country_code,
                        "arrest", f"{arrested_name} arrested in {country_code.upper()}",
                        {"arrested_role": target, "by": role_id, "justification": justification},
                        phase="A", category="political", role_name=action.get("arrester_name", role_id))
        return result

    if action_type == "assassination":
        from engine.services.assassination_engine import execute_assassination
        target = (action.get("changes") or {}).get("target_role") or action.get("target_role", "")
        return execute_assassination(
            sim_run_id, round_num, role_id, country_code, target)

    if action_type == "change_leader":
        from engine.services.change_leader import initiate_change_leader
        return initiate_change_leader(sim_run_id, round_num, role_id, country_code)

    if action_type == "reassign_types":
        return _reassign_position(sim_run_id, round_num, role_id, country_code, action)

    if action_type == "self_nominate":
        from engine.services.election_engine import submit_nomination
        return submit_nomination(
            sim_run_id, round_num, role_id,
            action.get("election_type"), action.get("election_round"))

    if action_type == "withdraw_nomination":
        from engine.services.election_engine import withdraw_nomination
        return withdraw_nomination(
            sim_run_id, role_id, action.get("election_type"))

    if action_type == "cast_election_vote":
        from engine.services.election_engine import cast_vote
        return cast_vote(
            sim_run_id, round_num, role_id,
            action.get("candidate_role_id"), action.get("election_type"))

    if action_type == "cast_vote":
        from engine.services.election_engine import cast_vote
        return cast_vote(
            sim_run_id, round_num, role_id,
            action.get("candidate_role_id"), action.get("election_type"))

    if action_type == "resolve_election":
        from engine.services.election_engine import resolve_election
        return resolve_election(
            sim_run_id, round_num,
            action.get("election_type"),
            contested_seat_role=action.get("contested_seat_role"))

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
        # Build clean payload matching validator's expected format
        launch_action = {
            "action_type": "launch_missile",
            "country_code": country_code,
            "round_num": round_num,
            "decision": "change",
            "rationale": action.get("rationale") or "Nuclear launch initiated by Head of State",
            "changes": {
                "warhead": "nuclear",
                "missiles": action.get("missiles", []),
            },
        }
        return orch.initiate(launch_action, sim_run_id, round_num, initiator_role_id=role_id)

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

    # ── Declare War ────────────────────────────────────────────────────
    if action_type == "declare_war":
        return _declare_war(sim_run_id, round_num, country_code, role_id, action.get("target_country", ""))

    # ── Movement ─────────────────────────────────────────────────────
    if action_type == "move_units":
        return _process_movement(sim_run_id, round_num, action)

    # ── Not Yet Implemented ───────────────────────────────────────────
    if action_type in ("call_org_meeting", "meet_freely", "invite_to_meet", "set_meetings"):
        return _create_meeting_invitation(sim_run_id, round_num, action)

    if action_type == "respond_meeting":
        return _respond_to_meeting(sim_run_id, action)

    # ── Unknown ───────────────────────────────────────────────────────
    return {"success": False, "narrative": f"Unknown action_type: {action_type}"}


# ── Reassign Position ───────────────────────────────────────────────────

def _create_meeting_invitation(sim_run_id: str, round_num: int, action: dict) -> dict:
    """Create a meeting invitation (1:1 or org meeting). Expires in 10 minutes."""
    from datetime import datetime, timezone, timedelta
    client = get_client()
    role_id = action.get("role_id", "")
    country_code = action.get("country_code", "")
    inv_type = action.get("invitation_type", "one_on_one")
    message = action.get("message", "")[:300]

    # Check limit: max 2 active (non-expired) invitations per role
    from datetime import datetime, timezone as tz
    now_iso = datetime.now(tz.utc).isoformat()
    active = client.table("meeting_invitations").select("id") \
        .eq("sim_run_id", sim_run_id).eq("inviter_role_id", role_id) \
        .eq("status", "pending").gte("expires_at", now_iso).execute().data or []
    if len(active) >= 2:
        return {"success": False, "narrative": "You already have 2 active invitations. Wait for them to expire or be answered."}

    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()

    row = {
        "sim_run_id": sim_run_id,
        "invitation_type": inv_type,
        "inviter_role_id": role_id,
        "inviter_country_code": country_code,
        "message": message,
        "expires_at": expires_at,
        "status": "pending",
        "responses": {},
    }

    if inv_type == "one_on_one":
        row["invitee_role_id"] = action.get("invitee_role_id", "")
    elif inv_type == "organization":
        row["org_id"] = action.get("org_id", "")
        row["org_name"] = action.get("org_name", "")
        row["theme"] = action.get("theme", "")

    result = client.table("meeting_invitations").insert(row).execute()
    inv_id = result.data[0]["id"] if result.data else None

    if inv_type == "one_on_one":
        target = action.get("invitee_role_id", "?")
        narrative = f"Meeting invitation sent to {target}"
    else:
        org_name = action.get("org_name", action.get("org_id", "?"))
        narrative = f"Meeting invitation sent to all members of {org_name}"

    logger.info("[meeting] %s invited %s (type=%s, id=%s)", role_id,
                action.get("invitee_role_id") or action.get("org_id"), inv_type, inv_id)

    return {"success": True, "narrative": narrative, "invitation_id": inv_id}


def _respond_to_meeting(sim_run_id: str, action: dict) -> dict:
    """Respond to a meeting invitation.

    When response is 'accept', creates a meetings record and links it
    back to the invitation via meeting_id.
    """
    from engine.services.meeting_service import create_meeting

    client = get_client()
    inv_id = action.get("invitation_id", "")
    role_id = action.get("role_id", "")
    response = action.get("response", "reject")  # accept, reject, later
    message = action.get("message", "")[:300]

    inv = client.table("meeting_invitations").select("*") \
        .eq("id", inv_id).limit(1).execute().data
    if not inv:
        return {"success": False, "narrative": "Invitation not found"}
    inv = inv[0]

    if inv["status"] != "pending":
        return {"success": False, "narrative": "Invitation has expired"}

    # If invitation already has a meeting_id, don't create a duplicate
    if inv.get("meeting_id"):
        return {
            "success": True,
            "narrative": "Meeting already exists for this invitation.",
            "meeting_id": inv["meeting_id"],
        }

    responses = inv.get("responses") or {}
    responses[role_id] = {"response": response, "message": message}
    update_payload: dict = {"responses": responses}

    # On accept: create a meeting record and link it to the invitation
    meeting_id = None
    if response == "accept":
        try:
            # Determine participant countries
            inviter_role_id = inv.get("inviter_role_id", "")
            inviter_country = inv.get("inviter_country_code", "")
            accepter_country = action.get("country_code", "")

            meeting = create_meeting(
                sim_run_id=sim_run_id,
                invitation_id=inv_id,
                participant_a_role_id=inviter_role_id,
                participant_a_country=inviter_country,
                participant_b_role_id=role_id,
                participant_b_country=accepter_country,
                agenda=inv.get("message"),
                round_num=inv.get("round_num"),
            )
            if not meeting.get("id"):
                logger.error("[meeting] Failed to create meeting for invitation %s: %s",
                             inv_id, meeting.get("error", "unknown"))
                return {"success": False, "narrative": "Accepted, but failed to create meeting channel."}
            meeting_id = meeting["id"]
            update_payload["status"] = "accepted"
            update_payload["meeting_id"] = meeting_id
            logger.info("[meeting] Invitation %s accepted → meeting %s", inv_id, meeting_id)
        except Exception as exc:
            logger.error("[meeting] Failed to create meeting for invitation %s: %s", inv_id, exc)
            return {"success": False, "narrative": "Accepted, but failed to create meeting channel."}
    elif response == "reject":
        update_payload["status"] = "rejected"

    client.table("meeting_invitations").update(update_payload).eq("id", inv_id).execute()

    label = {"accept": "accepted", "reject": "declined", "later": "asked to meet later"}.get(response, response)
    result = {"success": True, "narrative": f"You {label} the meeting invitation."}
    if meeting_id:
        result["meeting_id"] = meeting_id
    return result


def _reassign_position(sim_run_id: str, round_num: int, role_id: str, country_code: str, action: dict) -> dict:
    """HoS reassigns a position to another role in the country.

    Can assign (move position to target role) or vacate (remove position
    from current holder without assigning to anyone).

    Payload:
        position: str — e.g. 'military', 'economy', 'diplomat', 'security'
        target_role_id: str | null — who gets it (null = vacate)
    """
    from engine.config.position_actions import has_position
    from engine.services.position_helpers import transfer_position, recompute_role_actions
    from engine.services.common import write_event, get_scenario_id

    client = get_client()
    position = action.get("position", "")
    target_role_id = action.get("target_role_id")

    # Validate position
    valid_positions = {"military", "economy", "diplomat", "security", "opposition"}
    if position not in valid_positions:
        return {"success": False, "narrative": f"Invalid position: {position}. Must be one of: {sorted(valid_positions)}"}

    # Cannot reassign head_of_state (use change_leader for that)
    if position == "head_of_state":
        return {"success": False, "narrative": "Cannot reassign Head of State — use Change Leader instead"}

    # Validate initiator is HoS
    initiator = client.table("roles").select("id,character_name,positions,country_code") \
        .eq("sim_run_id", sim_run_id).eq("id", role_id).limit(1).execute().data
    if not initiator or not has_position(initiator[0], "head_of_state"):
        return {"success": False, "narrative": "Only Head of State can reassign positions"}
    if initiator[0]["country_code"] != country_code:
        return {"success": False, "narrative": "Can only reassign positions in your own country"}

    initiator_name = initiator[0]["character_name"]

    # Find who currently holds this position
    country_roles = client.table("roles").select("id,character_name,positions") \
        .eq("sim_run_id", sim_run_id).eq("country_code", country_code).eq("status", "active").execute().data or []

    current_holder = None
    for r in country_roles:
        if position in (r.get("positions") or []):
            current_holder = r
            break

    scenario_id = get_scenario_id(client, sim_run_id)

    if target_role_id:
        # Validate target exists in same country
        target = next((r for r in country_roles if r["id"] == target_role_id), None)
        if not target:
            return {"success": False, "narrative": f"Role {target_role_id} not found in {country_code}"}

        target_name = target["character_name"]

        if current_holder and current_holder["id"] == target_role_id:
            return {"success": False, "narrative": f"{target_name} already holds {position}"}

        if current_holder:
            # Transfer: remove from current, add to target
            transfer_position(client, sim_run_id, current_holder["id"], target_role_id, position)
            prev_name = current_holder["character_name"]
            narrative = f"{position.capitalize()} position transferred from {prev_name} to {target_name}"
        else:
            # Assign to target (position was vacant)
            target_positions = list(target.get("positions") or [])
            if position not in target_positions:
                target_positions.append(position)
            client.table("roles").update({"positions": target_positions}).eq("sim_run_id", sim_run_id).eq("id", target_role_id).execute()
            recompute_role_actions(client, sim_run_id, target_role_id)
            narrative = f"{target_name} assigned {position.capitalize()} position"

        write_event(client, sim_run_id, scenario_id, round_num, country_code,
                    "reassign_types", narrative,
                    {"position": position, "previous": current_holder["id"] if current_holder else None,
                     "new": target_role_id, "by": role_id},
                    phase="A", category="political", role_name=initiator_name)

        logger.info("[reassign] %s: %s -> %s (by %s)", position, current_holder["id"] if current_holder else "vacant", target_role_id, role_id)
        return {"success": True, "narrative": narrative}

    else:
        # Vacate: remove position from current holder
        if not current_holder:
            return {"success": False, "narrative": f"No one holds {position} — nothing to vacate"}

        prev_name = current_holder["character_name"]
        holder_positions = [p for p in (current_holder.get("positions") or []) if p != position]
        client.table("roles").update({"positions": holder_positions}).eq("sim_run_id", sim_run_id).eq("id", current_holder["id"]).execute()
        recompute_role_actions(client, sim_run_id, current_holder["id"])

        narrative = f"{prev_name} removed from {position.capitalize()} position (vacant)"

        write_event(client, sim_run_id, scenario_id, round_num, country_code,
                    "reassign_types", narrative,
                    {"position": position, "previous": current_holder["id"], "new": None, "by": role_id},
                    phase="A", category="political", role_name=initiator_name)

        logger.info("[reassign] %s vacated from %s (by %s)", position, current_holder["id"], role_id)
        return {"success": True, "narrative": narrative}


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

    # Attacker source hex: ground/air/bombardment attack FROM a different hex
    # Naval attacks may be at same hex. Missiles are global.
    src_row = action.get("source_global_row", target_row)
    src_col = action.get("source_global_col", target_col)

    # CANONICAL: attacker_unit_codes is always a string[] (standardized in frontend)
    # Legacy fallback handles older payloads with singular/alternate keys
    attacker_unit_codes = action.get("attacker_unit_codes") or []
    if not attacker_unit_codes:
        legacy = action.get("attacker_unit_code") or action.get("naval_unit_codes")
        if isinstance(legacy, str):
            attacker_unit_codes = [legacy]
        elif isinstance(legacy, list):
            attacker_unit_codes = legacy

    # Load attacker units — from source hex, or by specific unit_ids
    if attacker_unit_codes:
        # Load specific units by unit_id
        atk_units = client.table("deployments") \
            .select("*") \
            .eq("sim_run_id", sim_run_id) \
            .eq("country_code", attacker) \
            .in_("unit_status", ["active", "embarked"]) \
            .in_("unit_id", attacker_unit_codes) \
            .execute().data or []
    else:
        # Fallback: load all attacker units at source hex
        atk_units = client.table("deployments") \
            .select("*") \
            .eq("sim_run_id", sim_run_id) \
            .eq("country_code", attacker) \
            .eq("global_row", src_row) \
            .eq("global_col", src_col) \
            .eq("unit_status", "active") \
            .execute().data or []

    # Load defender units at target hex
    # Theater mode: use theater coords (multiple theater cells share same global hex)
    theater = action.get("theater")
    target_theater_row = action.get("target_theater_row")
    target_theater_col = action.get("target_theater_col")

    if theater and target_theater_row is not None and target_theater_col is not None:
        all_units_at_target = client.table("deployments") \
            .select("*") \
            .eq("sim_run_id", sim_run_id) \
            .eq("theater", theater) \
            .eq("theater_row", target_theater_row) \
            .eq("theater_col", target_theater_col) \
            .eq("unit_status", "active") \
            .execute().data or []
    else:
        all_units_at_target = client.table("deployments") \
            .select("*") \
            .eq("sim_run_id", sim_run_id) \
            .eq("global_row", target_row) \
            .eq("global_col", target_col) \
            .eq("unit_status", "active") \
            .execute().data or []
    def_units = [u for u in all_units_at_target if u["country_code"] != attacker]

    if not atk_units:
        return {"success": False, "narrative": f"No {attacker} units found for attack at {hex_label}"}

    # Convert DB rows to engine format — each DB row = 1 unit (individual unit model)
    def to_unit_list(units: list) -> list[dict]:
        return [{
            "unit_code": u.get("unit_id") or u["id"],
            "type": u["unit_type"],
            "country": u["country_code"],
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
            # When dice are provided, resolve only 1 exchange (moderator controls pace)
            max_ex = 1 if precomputed_rolls else 50
            result = resolve_ground_combat(
                attackers=ground_atk,
                defenders=ground_def,
                modifiers=action.get("modifiers"),
                precomputed_rolls=precomputed_rolls,
                max_exchanges=max_ex,
            )
            # Only apply losses to ground deployment rows
            ground_atk_deps = [u for u in atk_units if u["unit_type"] in GROUND_TYPES]
            ground_def_deps = [u for u in def_units if u["unit_type"] in GROUND_TYPES]
            combat_result = _apply_combat_losses(client, sim_run_id, result.model_dump(), ground_atk_deps, ground_def_deps, hex_label, combat_type)

            # If attacker won: move survivors forward, capture non-ground, occupy territory
            if combat_result.get("attacker_won"):
                # 1. Move surviving attacker ground units to captured hex
                atk_losses = set(combat_result.get("attacker_losses", []))
                survivors = [d for d in ground_atk_deps if (d.get("unit_id") or d["id"]) not in atk_losses]
                moved_units = []
                src_row = action.get("source_global_row", target_row)
                src_col = action.get("source_global_col", target_col)
                for dep in survivors:
                    update: dict = {"global_row": target_row, "global_col": target_col}
                    # Theater coords: use target's theater position if available from action
                    t_row = action.get("target_theater_row") or action.get("theater_row")
                    t_col = action.get("target_theater_col") or action.get("theater_col")
                    if t_row and t_col:
                        update["theater_row"] = t_row
                        update["theater_col"] = t_col
                    client.table("deployments").update(update).eq("id", dep["id"]).execute()
                    moved_units.append(dep.get("unit_id") or dep["id"])
                if moved_units:
                    combat_result["narrative"] += f" | {len(moved_units)} unit(s) advance to {hex_label}"
                    combat_result["moved_forward"] = moved_units

                # 2. Capture non-ground enemy units as trophies
                non_ground_def = [u for u in def_units if u["unit_type"] not in GROUND_TYPES]
                captured = []
                for dep in non_ground_def:
                    client.table("deployments").update({
                        "country_code": attacker,
                        "unit_status": "reserve",
                        "global_row": None, "global_col": None,
                        "theater": None, "theater_row": None, "theater_col": None,
                        "embarked_on": None,
                    }).eq("id", dep["id"]).execute()
                    captured.append({"unit_id": dep.get("unit_id") or dep["id"], "type": dep["unit_type"],
                                     "from": dep["country_code"]})
                if captured:
                    cap_desc = ", ".join(f"{c['type']} from {c['from']}" for c in captured)
                    combat_result["captured"] = captured
                    combat_result["narrative"] += f" | Captured: {cap_desc}"
                    logger.info("Ground victory at %s: captured %d trophies", hex_label, len(captured))

                # 3. Record hex occupation
                from engine.config.map_config import hex_owner as get_hex_owner
                owner = get_hex_owner(target_row, target_col)
                if owner != "sea" and owner != attacker:
                    _update_hex_control(client, sim_run_id, target_row, target_col,
                                        owner, attacker, round_num, "ground_attack")

            return combat_result

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
            return _apply_combat_losses(client, sim_run_id, result.model_dump(), atk_units, def_units, hex_label, combat_type)

        if combat_type == "naval":
            from engine.engines.military import resolve_naval_combat
            naval_atk = [u for u in atk_list if u["type"] in NAVAL_TYPES]
            naval_def = [u for u in def_list if u["type"] in NAVAL_TYPES]
            if not naval_atk:
                return {"success": False, "narrative": f"No naval units to attack with"}
            if not naval_def:
                return {"success": False, "narrative": f"No enemy naval units at {hex_label}"}
            # 1v1: pick specific target or first available
            target_unit_code = action.get("target_unit_code")
            atk_unit = naval_atk[0]
            def_unit = next((u for u in naval_def if u["unit_code"] == target_unit_code), naval_def[0]) if target_unit_code else naval_def[0]
            result = resolve_naval_combat(
                attacker=atk_unit,
                defender=def_unit,
                modifiers=action.get("modifiers"),
                precomputed_rolls=precomputed_rolls,
            )
            # Convert naval result format: {winner, destroyed_unit} → {attacker_losses, defender_losses}
            r = result.model_dump()
            destroyed = r.get("destroyed_unit", "")
            if r.get("winner") == "attacker":
                r["attacker_losses"] = []
                r["defender_losses"] = [destroyed]
            else:
                r["attacker_losses"] = [destroyed]
                r["defender_losses"] = []
            naval_atk_deps = [u for u in atk_units if u["unit_type"] in NAVAL_TYPES]
            naval_def_deps = [u for u in def_units if u["unit_type"] in NAVAL_TYPES]
            return _apply_combat_losses(client, sim_run_id, r, naval_atk_deps, naval_def_deps, hex_label, combat_type)

        if combat_type == "bombardment":
            from engine.engines.military import resolve_naval_bombardment_units, UnitNavalBombardmentInput, UnitSnapshot
            naval_atk = [u for u in atk_list if u["type"] in NAVAL_TYPES]
            ground_def = [u for u in def_list if u["type"] in GROUND_TYPES]
            if not naval_atk:
                return {"success": False, "narrative": f"No naval units to bombard with"}
            if not ground_def:
                return {"success": False, "narrative": f"No enemy ground units at {hex_label}"}
            def_countries = list(set(u["country"] for u in ground_def))
            inp = UnitNavalBombardmentInput(
                attacker_country=attacker,
                defender_country=def_countries[0] if def_countries else "unknown",
                target_global_row=target_row,
                target_global_col=target_col,
                naval_units=[UnitSnapshot(unit_code=u["unit_code"], country_code=attacker, unit_type="naval") for u in naval_atk],
                defender_ground_units=[UnitSnapshot(unit_code=u["unit_code"], country_code=u["country"], unit_type="ground") for u in ground_def],
            )
            result = resolve_naval_bombardment_units(inp)
            r = result.model_dump()
            r["attacker_losses"] = []
            r["success"] = True
            r["attacker_won"] = len(r.get("defender_losses", [])) > 0
            # Apply defender losses
            for code in r.get("defender_losses", []):
                dep_match = next((d for d in def_units if (d.get("unit_id") or d["id"]) == code), None)
                if dep_match:
                    client.table("deployments").delete().eq("id", dep_match["id"]).execute()
            r["losses_applied"] = True
            r["narrative"] = result.narrative + f" | Losses: defender -{len(r.get('defender_losses', []))}."
            logger.info("Bombardment at %s: %d shots, %d destroyed", hex_label, result.shots_fired, len(result.defender_losses))
            return r

        if combat_type == "missile":
            import random as _random
            from engine.engines.military import MISSILE_HIT_PROB, MISSILE_AD_INTERCEPT_PROB
            missile_atk = [u for u in atk_list if u["type"] == "strategic_missile"]
            if not missile_atk:
                return {"success": False, "narrative": "No missile units to launch"}
            missile = missile_atk[0]
            ad_at_target = [u for u in def_list if u["type"] in AD_TYPES]
            target_choice = action.get("target_choice", "military")

            # --- Phase 1: AD Interception (50% per AD unit, independent rolls) ---
            intercepted = False
            intercept_rolls = []
            for ad in ad_at_target:
                roll = _random.random()
                intercept_rolls.append({"ad_unit": ad["unit_code"], "roll": round(roll, 3), "intercepted": roll < MISSILE_AD_INTERCEPT_PROB})
                if roll < MISSILE_AD_INTERCEPT_PROB:
                    intercepted = True
                    break  # first successful intercept stops the missile

            # --- Missile always consumed ---
            missile_dep = next((d for d in atk_units if (d.get("unit_id") or d["id"]) == missile["unit_code"]), None)
            if missile_dep:
                client.table("deployments").delete().eq("id", missile_dep["id"]).execute()

            if intercepted:
                narrative = (f"Missile {missile['unit_code']} INTERCEPTED by AD at {hex_label}. "
                             f"Missile consumed. {len(intercept_rolls)} AD roll(s).")
                logger.info("Missile at %s: INTERCEPTED by AD", hex_label)
                return {
                    "success": True, "attacker_won": False, "losses_applied": True,
                    "attacker_losses": [missile["unit_code"]], "defender_losses": [],
                    "intercepted": True, "intercept_rolls": intercept_rolls,
                    "narrative": narrative,
                }

            # --- Phase 2: Hit Roll (flat 75%, same for all target choices) ---
            hit_roll = _random.random()
            hit = hit_roll < MISSILE_HIT_PROB

            if not hit:
                narrative = (f"Missile {missile['unit_code']} → {hex_label}: MISSED "
                             f"(roll {hit_roll:.2f} vs {MISSILE_HIT_PROB:.0%}). Missile consumed.")
                logger.info("Missile at %s: MISSED", hex_label)
                return {
                    "success": True, "attacker_won": False, "losses_applied": True,
                    "attacker_losses": [missile["unit_code"]], "defender_losses": [],
                    "intercepted": False, "hit": False, "hit_roll": round(hit_roll, 3),
                    "narrative": narrative,
                }

            # --- Hit: apply damage per target_choice ---
            defender_losses = []
            damage_desc = ""
            def_countries = list(set(u["country"] for u in def_list))
            target_country = def_countries[0] if def_countries else ""

            if target_choice == "military":
                # Destroy 1 military unit (prefer non-AD, random)
                targets = [u for u in def_list if u["type"] != "air_defense"] or list(def_list)
                if targets:
                    victim = _random.choice(targets)
                    defender_losses.append(victim["unit_code"])
                    damage_desc = f"1 {victim['type']} destroyed"

            elif target_choice == "ad":
                # Destroy 1 AD unit
                if ad_at_target:
                    victim = ad_at_target[0]
                    defender_losses.append(victim["unit_code"])
                    damage_desc = "1 air_defense destroyed"

            elif target_choice == "infrastructure":
                # -2% GDP
                if target_country:
                    country_data = client.table("countries").select("gdp").eq("sim_run_id", sim_run_id).eq("id", target_country).limit(1).execute().data
                    if country_data:
                        old_gdp = country_data[0]["gdp"]
                        new_gdp = round(old_gdp * 0.98, 2)
                        client.table("countries").update({"gdp": new_gdp}).eq("sim_run_id", sim_run_id).eq("id", target_country).execute()
                        damage_desc = f"Infrastructure hit: {target_country} GDP {old_gdp:.1f} → {new_gdp:.1f} (-2%)"

            elif target_choice == "nuclear_site":
                # Halve nuclear R&D progress
                if target_country:
                    country_data = client.table("countries").select("nuclear_rd_progress").eq("sim_run_id", sim_run_id).eq("id", target_country).limit(1).execute().data
                    if country_data:
                        old_prog = country_data[0].get("nuclear_rd_progress", 0)
                        new_prog = round(old_prog / 2, 2)
                        client.table("countries").update({"nuclear_rd_progress": new_prog}).eq("sim_run_id", sim_run_id).eq("id", target_country).execute()
                        damage_desc = f"Nuclear site hit: {target_country} R&D {old_prog:.0%} → {new_prog:.0%}"

            # Delete destroyed defender units
            for code in defender_losses:
                dep_match = next((d for d in def_units if (d.get("unit_id") or d["id"]) == code), None)
                if dep_match:
                    client.table("deployments").delete().eq("id", dep_match["id"]).execute()

            narrative = (f"Missile {missile['unit_code']} → {hex_label}: HIT ({target_choice}). "
                         f"{damage_desc or 'No valid target found'}. Missile consumed.")
            logger.info("Missile at %s: HIT (%s), %s", hex_label, target_choice, damage_desc)
            return {
                "success": True, "attacker_won": True, "losses_applied": True,
                "attacker_losses": [missile["unit_code"]], "defender_losses": defender_losses,
                "intercepted": False, "hit": True, "hit_roll": round(hit_roll, 3),
                "target_choice": target_choice, "damage": damage_desc,
                "narrative": narrative,
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
    # Preserve the engine's attacker_won verdict; success=True means "resolved without error"
    result["resolved"] = True
    result["attacker_won"] = result.get("success", def_total > 0 and atk_total == 0)
    result["success"] = True  # engine executed ok
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


def _ground_advance(sim_run_id: str, round_num: int, action: dict) -> dict:
    """Move ground units to an adjacent hex — capture any unprotected non-ground enemy units.

    CONTRACT_GROUND_COMBAT §unattended:
    - No enemy ground → walk in without dice
    - Non-ground enemies (air, AD, missiles) become attacker's RESERVE (trophies)
    - Original unit type preserved
    """
    client = get_client()
    country = action.get("country_code", "")
    target_row = action.get("target_row")
    target_col = action.get("target_col")
    unit_codes = action.get("attacker_unit_codes") or []
    if not unit_codes:
        legacy = action.get("attacker_unit_code")
        if isinstance(legacy, str):
            unit_codes = [legacy]

    if not unit_codes or target_row is None or target_col is None:
        return {"success": False, "narrative": "Missing units or target hex"}

    # Load attacker units (active or embarked — landing from carrier)
    units = client.table("deployments").select("id, unit_id, global_row, global_col, theater, theater_row, theater_col, unit_status, embarked_on") \
        .eq("sim_run_id", sim_run_id).eq("country_code", country) \
        .in_("unit_status", ["active", "embarked"]).in_("unit_id", unit_codes).execute().data or []

    if not units:
        return {"success": False, "narrative": "Units not found"}

    # Resolve theater target coords if provided
    theater_row = action.get("target_theater_row") or action.get("theater_row")
    theater_col = action.get("target_theater_col") or action.get("theater_col")
    theater = action.get("theater") or units[0].get("theater")

    # Check for non-ground enemy units at target hex (trophies to capture)
    enemy_at_target = client.table("deployments") \
        .select("id, unit_id, unit_type, country_code") \
        .eq("sim_run_id", sim_run_id) \
        .eq("global_row", target_row).eq("global_col", target_col) \
        .neq("country_code", country).eq("unit_status", "active") \
        .execute().data or []

    # Capture non-ground enemies: change owner to attacker, set to reserve
    captured = []
    for enemy in enemy_at_target:
        if enemy["unit_type"] != "ground":
            client.table("deployments").update({
                "country_code": country,
                "unit_status": "reserve",
                "global_row": None, "global_col": None,
                "theater": None, "theater_row": None, "theater_col": None,
                "embarked_on": None,
            }).eq("id", enemy["id"]).execute()
            captured.append({"unit_id": enemy["unit_id"], "type": enemy["unit_type"], "from": enemy["country_code"]})

    # Move attacker units to target hex (disembark if embarked)
    for u in units:
        update: dict = {
            "global_row": target_row, "global_col": target_col,
            "unit_status": "active", "embarked_on": None,
        }
        if theater_row and theater_col:
            update["theater_row"] = theater_row
            update["theater_col"] = theater_col
        client.table("deployments").update(update).eq("id", u["id"]).execute()

    # Build narrative
    parts = [f"{country} advances {len(units)} unit(s) to ({target_row},{target_col})"]
    if captured:
        cap_desc = ", ".join(f"{c['type']} from {c['from']}" for c in captured)
        parts.append(f"Captured: {cap_desc}")

    # Write event
    scenario_id = get_scenario_id(client, sim_run_id)
    write_event(
        client, sim_run_id, scenario_id, round_num,
        country, "ground_move",
        " | ".join(parts),
        {"units": unit_codes, "target_row": target_row, "target_col": target_col,
         "captured": captured},
        category="military", role_name=action.get("role_id"),
    )

    # Record hex occupation (only if this is foreign territory, not basing)
    from engine.config.map_config import hex_owner as get_hex_owner
    owner = get_hex_owner(target_row, target_col)
    if owner != "sea" and owner != country:
        # Check if we have basing rights (guests don't occupy)
        has_basing = client.table("relationships") \
            .select("basing_rights_a_to_b,basing_rights_b_to_a") \
            .eq("sim_run_id", sim_run_id) \
            .or_(f"and(from_country_code.eq.{owner},to_country_code.eq.{country}),and(from_country_code.eq.{country},to_country_code.eq.{owner})") \
            .limit(1).execute().data
        is_guest = False
        if has_basing:
            r = has_basing[0]
            is_guest = r.get("basing_rights_a_to_b") or r.get("basing_rights_b_to_a")
        if not is_guest:
            _update_hex_control(client, sim_run_id, target_row, target_col,
                                owner, country, round_num, "ground_move",
                                theater, theater_row, theater_col)

    logger.info("[dispatch] %s advances %d units to (%s,%s), captured %d trophies",
                country, len(units), target_row, target_col, len(captured))
    return {
        "success": True, "attacker_won": True,
        "narrative": " | ".join(parts),
        "attacker_losses": [], "defender_losses": [],
        "captured": captured,
    }


def _declare_war(sim_run_id: str, round_num: int, country_code: str, role_id: str, target_country: str) -> dict:
    """Declare war — unilateral, sets both directions to at_war."""
    if not target_country:
        return {"success": False, "narrative": "No target country specified"}
    if target_country == country_code:
        return {"success": False, "narrative": "Cannot declare war on yourself"}

    client = get_client()

    # Check current relationship
    rel = client.table("relationships").select("relationship") \
        .eq("sim_run_id", sim_run_id) \
        .eq("from_country_code", country_code).eq("to_country_code", target_country) \
        .execute()
    current = rel.data[0]["relationship"] if rel.data else "neutral"

    if current == "at_war":
        return {"success": False, "narrative": f"Already at war with {target_country}"}

    # Set both directions to at_war
    client.table("relationships").update({"relationship": "at_war"}) \
        .eq("sim_run_id", sim_run_id) \
        .eq("from_country_code", country_code).eq("to_country_code", target_country).execute()
    client.table("relationships").update({"relationship": "at_war"}) \
        .eq("sim_run_id", sim_run_id) \
        .eq("from_country_code", target_country).eq("to_country_code", country_code).execute()

    # Write observatory event
    scenario_id = get_scenario_id(client, sim_run_id)
    write_event(
        client, sim_run_id, scenario_id, round_num,
        country_code, "declare_war",
        f"{country_code} declares WAR on {target_country}",
        {"target": target_country, "previous_relationship": current},
        category="diplomatic", role_name=role_id,
    )

    logger.info("[dispatch] %s declares war on %s (was %s)", country_code, target_country, current)
    return {"success": True, "narrative": f"War declared on {target_country}. Previous relationship: {current}"}


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
    """Log a public statement or official org decision to observatory."""
    client = get_client()
    scenario_id = get_scenario_id(client, sim_run_id)
    role_id = action.get("role_id", "unknown")
    statement = action.get("content", "")
    country_code = action.get("country_code", "")
    org_id = action.get("org_id")
    org_name = action.get("org_name")
    statement_type = action.get("statement_type", "personal")

    if statement_type == "org_decision" and org_name:
        narrative = f"OFFICIAL DECISION of {org_name}: {statement[:200]}"
        event_type = "org_decision"
        payload = {"role_id": role_id, "content": statement, "org_id": org_id, "org_name": org_name}
    else:
        narrative = f"PUBLIC STATEMENT by {role_id}: {statement[:200]}"
        event_type = "public_statement"
        payload = {"role_id": role_id, "content": statement}

    write_event(client, sim_run_id, scenario_id, round_num, country_code,
                event_type, narrative, payload,
                phase="A", category="diplomatic", role_name=role_id)

    return {"success": True, "narrative": narrative}


def _dep_to_unit(dep: dict) -> dict:
    """Convert a deployments DB row to the in-memory unit dict shape the movement engine expects."""
    return {
        **dep,
        "unit_code": dep["unit_id"],
        "country_code": dep["country_code"],
        "status": dep["unit_status"],
    }


def _process_movement(sim_run_id: str, round_num: int, action: dict) -> dict:
    """Validate and apply a batch of unit moves.

    Loads units from deployments, converts field names for the in-memory engine,
    runs validation + processing, then writes updated positions back to DB.
    """
    from engine.engines.movement import process_movements
    from engine.services.movement_validator import validate_movement_decision
    from engine.services.movement_data import load_global_grid_zones, load_basing_rights

    client = get_client()
    country_code = action.get("country_code", "")
    role_id = action.get("role_id", "")
    moves = action.get("moves", [])

    if not moves:
        return {"success": False, "narrative": "No moves provided"}

    # 1. Load all country's units from deployments
    deps = client.table("deployments") \
        .select("unit_id, country_code, unit_type, unit_status, global_row, global_col, "
                "theater, theater_row, theater_col, embarked_on") \
        .eq("sim_run_id", sim_run_id) \
        .eq("country_code", country_code) \
        .execute().data or []

    if not deps:
        return {"success": False, "narrative": f"No units found for {country_code}"}

    # 2. Convert to in-memory dict (unit_code keyed)
    units: dict[str, dict] = {}
    for dep in deps:
        u = _dep_to_unit(dep)
        units[u["unit_code"]] = u

    # 3. Load zones and basing rights
    zones = load_global_grid_zones()
    basing_rights = load_basing_rights(client, sim_run_id)

    # 4. Build validator payload
    payload = {
        "action_type": "move_units",
        "country_code": country_code,
        "round_num": round_num,
        "decision": "change",
        "rationale": action.get("rationale", "Player-submitted unit movement batch"),
        "changes": {"moves": moves},
    }

    # 5. Validate
    vr = validate_movement_decision(payload, units, zones, basing_rights)
    if not vr["valid"]:
        return {
            "success": False,
            "narrative": f"Movement validation failed: {'; '.join(vr['errors'])}",
            "errors": vr["errors"],
            "warnings": vr.get("warnings", []),
        }

    # 6. Apply moves (mutates units dict in place)
    normalized = vr["normalized"]
    norm_moves = normalized["changes"]["moves"]
    results = process_movements(norm_moves, country_code, units, zones)

    # 7. Write back to deployments for each moved unit
    moved_count = 0
    for move_result in results:
        uc = move_result["unit_code"]
        u = units.get(uc)
        if u is None:
            continue
        update = {
            "global_row": u.get("global_row"),
            "global_col": u.get("global_col"),
            "unit_status": u["status"],
            "embarked_on": u.get("embarked_on"),
            "theater": u.get("theater"),
            "theater_row": u.get("theater_row"),
            "theater_col": u.get("theater_col"),
        }
        client.table("deployments").update(update) \
            .eq("sim_run_id", sim_run_id) \
            .eq("unit_id", uc) \
            .execute()
        moved_count += 1

    # 8. Write observatory event
    scenario_id = get_scenario_id(client, sim_run_id)
    summary_parts = []
    for r in results:
        summary_parts.append(f"{r['unit_code']}: {r['action']}")
    summary = f"{country_code} moves {moved_count} unit(s): {', '.join(summary_parts[:5])}"
    if len(summary_parts) > 5:
        summary += f" (+{len(summary_parts)-5} more)"

    write_event(
        client, sim_run_id, scenario_id, round_num, country_code,
        "move_units", summary,
        {"action": action, "results": results, "moved_count": moved_count},
        category="military", role_name=role_id,
    )

    logger.info("[dispatch] move_units: %s moved %d units", country_code, moved_count)
    return {
        "success": True,
        "narrative": summary,
        "moved_count": moved_count,
        "results": results,
        "warnings": vr.get("warnings", []),
    }


# ---------------------------------------------------------------------------
# Nuclear Test — HoS-only, no authorization chain (simplified)
# ---------------------------------------------------------------------------

# Success probabilities (CARD_FORMULAS D.7)
_NUKE_TEST_PROB_L1 = 0.70
_NUKE_TEST_PROB_L2_PLUS = 0.95

# Stability / GDP costs
_NUKE_STAB_UNDERGROUND = -0.2
_NUKE_STAB_SURFACE_GLOBAL = -0.4
_NUKE_STAB_SURFACE_ADJACENT = -0.6
_NUKE_GDP_SURFACE = -0.05  # -5%


def _execute_nuclear_test(sim_run_id: str, round_num: int, action: dict) -> dict:
    """Execute a nuclear test directly (HoS decides alone, no chain).

    Reads country's nuclear_level and nuclear_confirmed from countries table.
    Validates, rolls for success, applies effects, writes events + artefacts.
    """
    client = get_client()
    country_code = action.get("country_code", "")
    role_id = action.get("role_id", "")
    test_type = action.get("test_type", "underground")  # "underground" or "surface"
    target_row = action.get("target_row")
    target_col = action.get("target_col")

    # 1. Read country state
    cs_rows = client.table("countries").select(
        "nuclear_level, nuclear_confirmed"
    ).eq("sim_run_id", sim_run_id).eq("id", country_code).limit(1).execute().data
    if not cs_rows:
        return {"success": False, "narrative": f"Country {country_code} not found"}

    cs = cs_rows[0]
    nuclear_level = int(cs.get("nuclear_level") or 0)
    nuclear_confirmed = cs.get("nuclear_confirmed", False)

    # 2. Validate
    if nuclear_level < 1:
        return {"success": False, "narrative": "Must have nuclear_level >= 1 to test"}
    # Confirmed countries CAN still test as a political signal (stability effects apply)

    # 3. Roll for success
    prob = _NUKE_TEST_PROB_L2_PLUS if nuclear_level >= 2 else _NUKE_TEST_PROB_L1
    precomputed = action.get("precomputed_rolls") or {}
    roll = precomputed.get("test_success_roll", random.random())
    test_success = roll < prob

    # 4. On success: set nuclear_confirmed = true
    if test_success:
        try:
            client.table("countries").update({
                "nuclear_confirmed": True,
            }).eq("sim_run_id", sim_run_id).eq("id", country_code).execute()
        except Exception as e:
            logger.warning("nuclear_confirmed update failed: %s", e)

    # 5. Apply stability effects to ALL countries
    stability_effects: dict[str, float] = {}
    gdp_effects: dict[str, float] = {}

    try:
        all_countries = client.table("countries").select(
            "id, stability, gdp"
        ).eq("sim_run_id", sim_run_id).execute().data or []
    except Exception as e:
        logger.warning("Failed to load countries for nuclear effects: %s", e)
        all_countries = []

    if test_type == "underground":
        # Global stability -0.2
        for c in all_countries:
            cc = c["id"]
            new_stab = max(0.0, (c.get("stability") or 5.0) + _NUKE_STAB_UNDERGROUND)
            stability_effects[cc] = _NUKE_STAB_UNDERGROUND
            try:
                client.table("countries").update({
                    "stability": round(new_stab, 2),
                }).eq("sim_run_id", sim_run_id).eq("id", cc).execute()
            except Exception as e:
                logger.warning("stability update failed for %s: %s", cc, e)
    else:
        # Surface: global stability -0.4, own GDP -5%
        adjacent_countries: set[str] = set()
        if target_row is not None and target_col is not None:
            adj_hexes = hex_neighbors_bounded(int(target_row), int(target_col))
            for r, c in adj_hexes:
                owner = GLOBAL_HEX_OWNERS.get((r, c))
                if owner and owner != country_code and owner != "sea":
                    adjacent_countries.add(owner)

        for c in all_countries:
            cc = c["id"]
            stab_delta = _NUKE_STAB_SURFACE_GLOBAL
            if cc in adjacent_countries:
                stab_delta += _NUKE_STAB_SURFACE_ADJACENT
            new_stab = max(0.0, (c.get("stability") or 5.0) + stab_delta)
            stability_effects[cc] = stab_delta
            updates: dict[str, Any] = {"stability": round(new_stab, 2)}

            # Own GDP -5%
            if cc == country_code:
                old_gdp = c.get("gdp") or 0
                new_gdp = round(old_gdp * (1.0 + _NUKE_GDP_SURFACE), 2)
                updates["gdp"] = new_gdp
                gdp_effects[cc] = _NUKE_GDP_SURFACE

            try:
                client.table("countries").update(updates).eq(
                    "sim_run_id", sim_run_id
                ).eq("id", cc).execute()
            except Exception as e:
                logger.warning("nuclear surface effects update failed for %s: %s", cc, e)

    # 6. Build result
    result = {
        "success": True,
        "test_success": test_success,
        "test_type": test_type,
        "nuclear_level": nuclear_level,
        "success_probability": prob,
        "success_roll": round(roll, 4),
        "stability_effects": stability_effects,
        "gdp_effects": gdp_effects,
        "narrative": (
            f"{country_code} {test_type} nuclear test: "
            f"{'SUCCESS — Level {0} CONFIRMED'.format(nuclear_level) if test_success else 'FAILURE — level not confirmed'} "
            f"(prob={prob}, roll={roll:.4f})"
        ),
    }
    if test_type == "surface" and target_row is not None:
        result["target_row"] = target_row
        result["target_col"] = target_col

    # 7. Write observatory event
    scenario_id = get_scenario_id(client, sim_run_id)
    write_event(
        client, sim_run_id, scenario_id, round_num, country_code,
        "nuclear_test", result["narrative"],
        {
            "test_type": test_type,
            "test_success": test_success,
            "nuclear_level": nuclear_level,
            "success_probability": prob,
            "success_roll": round(roll, 4),
            "target_row": target_row,
            "target_col": target_col,
            "stability_effects": stability_effects,
            "gdp_effects": gdp_effects,
        },
        category="military", role_name=role_id,
    )

    # 8. Generate classified artefacts for T3+ countries
    _generate_nuclear_test_artefacts(
        client, sim_run_id, round_num, country_code, test_type, test_success, nuclear_level,
    )

    logger.info("[dispatch] nuclear_test by %s (%s): %s",
                role_id, country_code, "SUCCESS" if test_success else "FAILURE")
    return result


def _generate_nuclear_test_artefacts(
    client, sim_run_id: str, round_num: int,
    testing_country: str, test_type: str, test_success: bool, nuclear_level: int,
) -> None:
    """Insert classified artefacts for T3+ countries' HoS and military roles."""
    try:
        # Find T3+ countries (nuclear_level >= 3 AND confirmed)
        t3_rows = client.table("countries").select(
            "id, nuclear_level, nuclear_confirmed"
        ).eq("sim_run_id", sim_run_id).execute().data or []

        t3_countries = [
            r["id"] for r in t3_rows
            if int(r.get("nuclear_level") or 0) >= 3
            and r.get("nuclear_confirmed")
            and r["id"] != testing_country
        ]

        if not t3_countries:
            return

        # Find HoS + military roles for these countries
        from engine.config.position_actions import has_position
        roles_rows = client.table("roles").select(
            "id, country_code, positions, position_type"
        ).eq("sim_run_id", sim_run_id).eq("status", "active").in_(
            "country_code", t3_countries
        ).execute().data or []

        target_role_ids: list[str] = []
        for r in roles_rows:
            if has_position(r, "head_of_state") or has_position(r, "military"):
                target_role_ids.append(r["id"])

        if not target_role_ids:
            return

        import uuid
        outcome_word = "SUCCESSFUL" if test_success else "FAILED"
        artefacts = []
        for rid in target_role_ids:
            artefacts.append({
                "id": f"nuke_alert_{testing_country}_{round_num}_{rid}_{uuid.uuid4().hex[:8]}",
                "sim_run_id": sim_run_id,
                "role_id": rid,
                "artefact_type": "classified_report",
                "title": "NUCLEAR TEST ALERT",
                "subtitle": f"Detected: {test_type} nuclear test",
                "classification": "TOP SECRET",
                "from_entity": "Global Monitoring Systems",
                "date_label": f"Round {round_num}",
                "content_html": (
                    f"<p>Global nuclear monitoring systems have detected a <strong>{test_type}</strong> "
                    f"nuclear detonation originating from <strong>{testing_country.upper()}</strong>.</p>"
                    f"<p>Assessment: Test appears <strong>{outcome_word}</strong>. "
                    f"Estimated nuclear capability: Level {nuclear_level}.</p>"
                    f"<p>Recommend immediate strategic review and intelligence briefing.</p>"
                ),
                "round_delivered": round_num,
                "is_read": False,
            })

        if artefacts:
            client.table("artefacts").insert(artefacts).execute()
            logger.info("[nuclear_test] Generated %d artefacts for T3+ countries", len(artefacts))

    except Exception as e:
        logger.warning("Nuclear test artefact generation failed: %s", e)


def _lookup_character_name(sim_run_id: str, role_id: str, fallback: str = "") -> str:
    """Look up character_name for a role. Returns fallback on failure."""
    try:
        db = get_client()
        r = db.table("roles").select("character_name").eq(
            "sim_run_id", sim_run_id
        ).eq("id", role_id).limit(1).execute()
        if r.data:
            return r.data[0].get("character_name", fallback)
    except Exception:
        pass
    return fallback or role_id


def _log_dispatch(sim_run_id, round_num, action_type, role_id, country_code, result):
    """Log action dispatch result for audit trail."""
    success = result.get("success", False)
    level = logging.INFO if success else logging.WARNING
    logger.log(level, "[dispatch] %s by %s → %s",
               action_type, role_id, "OK" if success else "FAILED")


# ── Enqueue events for AI agents ─────────────────────────────────────

def _enqueue_for_ai_agents(
    sim_run_id: str,
    round_num: int,
    action_type: str,
    action: dict,
    result: dict,
) -> None:
    """Check if a dispatched action affects an AI agent and enqueue an event.

    Called after every successful action dispatch. Uses the EventDispatcher
    to write events to the unified queue. The dispatcher loop delivers them.
    """
    from engine.agents.managed.event_dispatcher import get_dispatcher

    try:
        dispatcher = get_dispatcher(sim_run_id)
        if not dispatcher:
            return  # No active dispatcher — AI not initialized for this sim

        country_code = action.get("country_code", "")

        # ── Meeting invitations ──────────────────────────────────────
        if action_type in ("invite_to_meet", "set_meetings", "call_org_meeting", "meet_freely"):
            invitee = action.get("invitee_role_id", "")
            inv_id = result.get("invitation_id", "")
            inviter_name = _lookup_character_name(sim_run_id, action.get("role_id", ""), country_code)
            agenda = action.get("message", "")
            if invitee and inv_id:
                dispatcher.enqueue(
                    role_id=invitee,
                    tier=2,
                    event_type="meeting_invitation",
                    message=(
                        f"MEETING INVITATION RECEIVED\n\n"
                        f"You have received a meeting invitation from {inviter_name}.\n"
                        f"Agenda: {agenda or 'No agenda specified'}\n"
                        f"Invitation ID: {inv_id}\n\n"
                        f"Decide whether to accept or decline this meeting. "
                        f"Use the respond_to_invitation tool with invitation_id='{inv_id}' "
                        f"and your decision ('accept' or 'reject').\n\n"
                        f"Consider: Is this meeting useful for your strategy? "
                        f"Do you have time? Is this person trustworthy?"
                    ),
                    metadata={"inviter": inviter_name, "invitation_id": inv_id, "agenda": agenda},
                )

        # ── Meeting accepted (notify AI inviter) ─────────────────────
        elif action_type == "respond_meeting":
            response = action.get("response", "")
            meeting_id = result.get("meeting_id", "")
            if response == "accept" and meeting_id:
                try:
                    inv_id = action.get("invitation_id", "")
                    if inv_id:
                        db = get_client()
                        inv = db.table("meeting_invitations").select(
                            "inviter_role_id, message"
                        ).eq("id", inv_id).limit(1).execute()
                        if inv.data:
                            inviter = inv.data[0]["inviter_role_id"]
                            agenda = inv.data[0].get("message", "")
                            accepter_name = action.get("role_id", country_code)
                            dispatcher.enqueue(
                                role_id=inviter,
                                tier=2,
                                event_type="meeting_accepted",
                                message=(
                                    f"MEETING STARTED\n\n"
                                    f"Your meeting with {accepter_name} has been accepted and is now active.\n"
                                    f"Meeting ID: {meeting_id}\n"
                                    f"Agenda: {agenda or 'General discussion'}\n\n"
                                    f"You initiated this meeting, so you speak first. "
                                    f"Use the send_message tool with meeting_id='{meeting_id}' "
                                    f"to begin the conversation.\n\n"
                                    f"Keep your opening message focused — state what you want to discuss. "
                                    f"1-3 sentences, stay in character."
                                ),
                                metadata={"meeting_id": meeting_id, "accepter": accepter_name, "agenda": agenda},
                            )
                except Exception as e:
                    logger.warning("[enqueue] Failed to notify inviter: %s", e)

        # ── Transaction proposed ─────────────────────────────────────
        elif action_type == "propose_transaction":
            target = action.get("target_country", action.get("to_country", ""))
            transaction_id = result.get("transaction_id", result.get("id", ""))
            terms = result.get("narrative", "Trade proposal")
            if target and transaction_id:
                dispatcher.enqueue_for_country(
                    country_code=target,
                    tier=2,
                    event_type="transaction_proposed",
                    message=(
                        f"TRANSACTION PROPOSAL RECEIVED\n\n"
                        f"{country_code.upper()} has proposed a transaction to your country.\n"
                        f"Terms: {terms}\n"
                        f"Transaction ID: {transaction_id}\n\n"
                        f"Review this proposal carefully. You can accept, reject, or counter-offer.\n"
                        f"Use submit_action with action_type='accept_transaction', "
                        f"transaction_id='{transaction_id}', and response='accept' or 'reject'.\n\n"
                        f"Consider: Is this deal fair? What do you gain? What do you lose? "
                        f"Does this serve your strategic interests?"
                    ),
                    metadata={"transaction_id": transaction_id, "proposer": country_code, "terms": terms},
                )

        # ── Agreement proposed ───────────────────────────────────────
        elif action_type == "propose_agreement":
            target = action.get("target_country", action.get("to_country", ""))
            agreement_id = result.get("agreement_id", result.get("id", ""))
            agreement_type = action.get("agreement_type", "general")
            if target and agreement_id:
                dispatcher.enqueue_for_country(
                    country_code=target,
                    tier=2,
                    event_type="agreement_proposed",
                    message=(
                        f"AGREEMENT PROPOSAL RECEIVED\n\n"
                        f"{country_code.upper()} proposes a {agreement_type} agreement.\n"
                        f"Agreement ID: {agreement_id}\n\n"
                        f"Review this agreement. You can sign or decline.\n"
                        f"Use submit_action with action_type='sign_agreement', "
                        f"agreement_id='{agreement_id}', and confirm=true (to sign) or confirm=false (to decline).\n\n"
                        f"Consider: Does this agreement benefit your country? "
                        f"What obligations does it impose? Can you trust the other party?"
                    ),
                    metadata={"agreement_id": agreement_id, "proposer": country_code, "type": agreement_type},
                )

        # ── Combat: attack against a country ─────────────────────────
        elif action_type in ("ground_attack", "air_strike", "naval_combat",
                             "naval_bombardment", "launch_missile_conventional"):
            target_country = action.get("target_country", "")
            target_row = action.get("target_row", "?")
            target_col = action.get("target_col", "?")
            details = result.get("narrative", f"Attack at ({target_row},{target_col})")
            if target_country and target_country != country_code:
                dispatcher.enqueue_for_country(
                    country_code=target_country,
                    tier=1,
                    event_type="attack_declared",
                    message=(
                        f"ALERT: MILITARY ATTACK\n\n"
                        f"{country_code.upper()} has launched a {action_type} attack "
                        f"against your territory!\n"
                        f"Details: {details}\n\n"
                        f"This requires immediate response. Assess the situation:\n"
                        f"1. Use get_my_forces to check your military position\n"
                        f"2. Consider retaliatory strikes or defensive repositioning\n"
                        f"3. Consider diplomatic responses (public statement, request allies)\n"
                        f"4. Update your strategic notes with write_notes\n\n"
                        f"Act decisively — your nation is under attack."
                    ),
                    metadata={"attacker": country_code, "attack_type": action_type, "details": details},
                )

        # ── War declared ─────────────────────────────────────────────
        elif action_type == "declare_war":
            target = action.get("target_country", "")
            if target:
                dispatcher.enqueue_for_country(
                    country_code=target,
                    tier=1,
                    event_type="war_declared",
                    message=(
                        f"WAR DECLARED\n\n"
                        f"{country_code.upper()} has declared WAR on your country!\n\n"
                        f"This is a critical moment. You must:\n"
                        f"1. Assess your military readiness (get_my_forces)\n"
                        f"2. Review your alliances (get_relationships)\n"
                        f"3. Consider requesting emergency meetings with allies\n"
                        f"4. Issue a public statement responding to the declaration\n"
                        f"5. Prepare defensive or offensive military plans\n\n"
                        f"Your nation's survival may depend on your next decisions."
                    ),
                    metadata={"declarer": country_code},
                )

        # ── Nuclear chain ────────────────────────────────────────────
        elif action_type == "nuclear_launch_initiate":
            authorizer = result.get("authorizer_role_id", "")
            nuclear_action_id = result.get("nuclear_action_id", result.get("action_id", ""))
            initiator_name = action.get("role_id", country_code)
            target_desc = result.get("target_description", "multiple targets")
            if authorizer and nuclear_action_id:
                dispatcher.enqueue(
                    role_id=authorizer,
                    tier=1,
                    event_type="nuclear_authorize_request",
                    message=(
                        f"NUCLEAR AUTHORIZATION REQUEST\n\n"
                        f"{initiator_name} has initiated a nuclear launch and requires your authorization.\n"
                        f"Target: {target_desc}\n"
                        f"Nuclear Action ID: {nuclear_action_id}\n\n"
                        f"This is the most consequential decision you can make. "
                        f"You must authorize or refuse.\n"
                        f"Use submit_action with action_type='nuclear_authorize', "
                        f"nuclear_action_id='{nuclear_action_id}', and confirm=true or confirm=false.\n\n"
                        f"Consider the consequences carefully. A nuclear strike will "
                        f"cause massive destruction and reshape all international relationships."
                    ),
                    metadata={"nuclear_action_id": nuclear_action_id, "initiator": initiator_name, "target": target_desc},
                )

        elif action_type == "nuclear_authorize":
            if result.get("launched") or result.get("status") == "launched":
                target_countries = result.get("target_countries", [])
                target_desc = result.get("target_description", "your territory")
                for tgt in target_countries:
                    dispatcher.enqueue_for_country(
                        country_code=tgt,
                        tier=1,
                        event_type="nuclear_launch_against",
                        message=(
                            f"NUCLEAR STRIKE INCOMING\n\n"
                            f"{country_code.upper()} has launched a NUCLEAR STRIKE against your territory!\n"
                            f"Target: {target_desc}\n\n"
                            f"This is an existential crisis. Immediate actions:\n"
                            f"1. Assess damage potential and your nuclear capability\n"
                            f"2. Consider retaliatory nuclear strike if you have the capability\n"
                            f"3. Issue an emergency public statement\n"
                            f"4. Request emergency allied support\n"
                            f"5. Record this moment in your notes\n\n"
                            f"The world is watching. Every decision matters."
                        ),
                        metadata={"attacker": country_code, "target": target_desc},
                    )

    except Exception as e:
        logger.warning("[enqueue] Error in _enqueue_for_ai_agents: %s", e)
