"""Action Dispatcher — routes submitted actions to their engines.

This is the GLUE between agent/human action submissions and the engine layer.
Every action submitted during Phase A is dispatched here for immediate resolution.

Action type names are CANONICAL — they match role_actions.action_id in the DB.
Source of truth: M9 role_actions table (33 action types as of 2026-04-17).

See CONTRACT_ROUND_FLOW.md for the canonical round flow.
"""

from __future__ import annotations

import logging
from typing import Any

from engine.services.supabase import get_client
from engine.services.common import get_scenario_id, write_event

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

    if action_type == "ground_move":
        return _ground_advance(sim_run_id, round_num, action)

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

    # ── Declare War ────────────────────────────────────────────────────
    if action_type == "declare_war":
        return _declare_war(sim_run_id, round_num, country_code, role_id, action.get("target_country", ""))

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
            .eq("country_id", attacker) \
            .in_("unit_status", ["active", "embarked"]) \
            .in_("unit_id", attacker_unit_codes) \
            .execute().data or []
    else:
        # Fallback: load all attacker units at source hex
        atk_units = client.table("deployments") \
            .select("*") \
            .eq("sim_run_id", sim_run_id) \
            .eq("country_id", attacker) \
            .eq("global_row", src_row) \
            .eq("global_col", src_col) \
            .eq("unit_status", "active") \
            .execute().data or []

    # Load defender units at target hex
    all_units_at_target = client.table("deployments") \
        .select("*") \
        .eq("sim_run_id", sim_run_id) \
        .eq("global_row", target_row) \
        .eq("global_col", target_col) \
        .eq("unit_status", "active") \
        .execute().data or []
    def_units = [u for u in all_units_at_target if u["country_id"] != attacker]

    if not atk_units:
        return {"success": False, "narrative": f"No {attacker} units found for attack at {hex_label}"}

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
                    t_row = action.get("theater_row")
                    t_col = action.get("theater_col")
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
                        "country_id": attacker,
                        "unit_status": "reserve",
                        "global_row": None, "global_col": None,
                        "theater": None, "theater_row": None, "theater_col": None,
                        "embarked_on": None,
                    }).eq("id", dep["id"]).execute()
                    captured.append({"unit_id": dep.get("unit_id") or dep["id"], "type": dep["unit_type"],
                                     "from": dep["country_id"]})
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
            from engine.engines.military import resolve_missile_strike_units, UnitMissileStrikeInput, UnitSnapshot, WarheadType, StrategicAttackTier
            missile_atk = [u for u in atk_list if u["type"] == "strategic_missile"]
            if not missile_atk:
                return {"success": False, "narrative": "No missile units to launch"}
            missile = missile_atk[0]
            ad_at_target = [u for u in def_list if u["type"] in AD_TYPES]
            def_countries = list(set(u["country"] for u in def_list))
            inp = UnitMissileStrikeInput(
                missile_unit=UnitSnapshot(unit_code=missile["unit_code"], country_code=attacker, unit_type="strategic_missile"),
                target_global_row=target_row,
                target_global_col=target_col,
                warhead_type=WarheadType.CONVENTIONAL,
                attack_tier=StrategicAttackTier.T1_MIDRANGE,
                defender_units=[UnitSnapshot(unit_code=u["unit_code"], country_code=u["country"], unit_type=u["type"]) for u in def_list],
                ad_units_covering_zone=[UnitSnapshot(unit_code=u["unit_code"], country_code=u["country"], unit_type="air_defense") for u in ad_at_target],
                target_country=def_countries[0] if def_countries else "",
            )
            result = resolve_missile_strike_units(inp)
            r = result.model_dump()
            # Missile is always consumed
            r["attacker_losses"] = [missile["unit_code"]]
            r["success"] = True
            r["attacker_won"] = result.success
            # Delete the missile unit
            missile_dep = next((d for d in atk_units if (d.get("unit_id") or d["id"]) == missile["unit_code"]), None)
            if missile_dep:
                client.table("deployments").delete().eq("id", missile_dep["id"]).execute()
            # Apply defender losses
            for code in r.get("defender_losses", []):
                dep_match = next((d for d in def_units if (d.get("unit_id") or d["id"]) == code), None)
                if dep_match:
                    client.table("deployments").delete().eq("id", dep_match["id"]).execute()
            r["losses_applied"] = True
            def_losses = len(r.get("defender_losses", []))
            r["narrative"] = result.narrative + f" | Missile consumed. Defender losses: {def_losses}."
            logger.info("Missile at %s: hit=%s, def_losses=%d", hex_label, result.success, def_losses)
            return r

        if combat_type == "blockade":
            return {
                "success": True,
                "narrative": f"Blockade at {hex_label}: implementation pending (chokepoint mechanics).",
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
        .eq("sim_run_id", sim_run_id).eq("country_id", country) \
        .in_("unit_status", ["active", "embarked"]).in_("unit_id", unit_codes).execute().data or []

    if not units:
        return {"success": False, "narrative": "Units not found"}

    # Resolve theater target coords if provided
    theater_row = action.get("theater_row")
    theater_col = action.get("theater_col")
    theater = action.get("theater") or units[0].get("theater")

    # Check for non-ground enemy units at target hex (trophies to capture)
    enemy_at_target = client.table("deployments") \
        .select("id, unit_id, unit_type, country_id") \
        .eq("sim_run_id", sim_run_id) \
        .eq("global_row", target_row).eq("global_col", target_col) \
        .neq("country_id", country).eq("unit_status", "active") \
        .execute().data or []

    # Capture non-ground enemies: change owner to attacker, set to reserve
    captured = []
    for enemy in enemy_at_target:
        if enemy["unit_type"] != "ground":
            client.table("deployments").update({
                "country_id": country,
                "unit_status": "reserve",
                "global_row": None, "global_col": None,
                "theater": None, "theater_row": None, "theater_col": None,
                "embarked_on": None,
            }).eq("id", enemy["id"]).execute()
            captured.append({"unit_id": enemy["unit_id"], "type": enemy["unit_type"], "from": enemy["country_id"]})

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
            .or_(f"and(from_country_id.eq.{owner},to_country_id.eq.{country}),and(from_country_id.eq.{country},to_country_id.eq.{owner})") \
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
        .eq("from_country_id", country_code).eq("to_country_id", target_country) \
        .execute()
    current = rel.data[0]["relationship"] if rel.data else "neutral"

    if current == "at_war":
        return {"success": False, "narrative": f"Already at war with {target_country}"}

    # Set both directions to at_war
    client.table("relationships").update({"relationship": "at_war"}) \
        .eq("sim_run_id", sim_run_id) \
        .eq("from_country_id", country_code).eq("to_country_id", target_country).execute()
    client.table("relationships").update({"relationship": "at_war"}) \
        .eq("sim_run_id", sim_run_id) \
        .eq("from_country_id", target_country).eq("to_country_id", country_code).execute()

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
