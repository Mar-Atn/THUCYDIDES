"""Arrest Engine — CONTRACT for arrest action.

Flow:
  1. Initiator submits arrest request (target + justification)
  2. Moderator confirms or declines
  3. If confirmed: target status → arrested in run_roles
  4. Target cannot act for remainder of round
  5. At round end: target auto-released (status → active)

In unmanned mode: moderator confirmation is auto-approved (no moderator).
"""

from __future__ import annotations

import logging
from typing import Optional

from engine.config.position_actions import has_position
from engine.services.run_roles import update_role_status
from engine.services.supabase import get_client

logger = logging.getLogger(__name__)


def request_arrest(
    sim_run_id: str,
    arrester_role_id: str,
    target_role_id: str,
    justification: str,
    round_num: int,
) -> dict:
    """Submit an arrest request. In unmanned mode, auto-confirms.

    Returns ``{success, status, message}``.
    """
    client = get_client()

    # Verify target exists and is active (query roles table, not run_roles)
    target_data = client.table("roles") \
        .select("id, character_name, status, positions, country_code") \
        .eq("sim_run_id", sim_run_id).eq("id", target_role_id).limit(1).execute().data
    if not target_data:
        return {"success": False, "status": "rejected",
                "message": f"Target role {target_role_id!r} not found"}
    target = target_data[0]

    if target["status"] != "active":
        return {"success": False, "status": "rejected",
                "message": f"Target {target_role_id!r} is already {target['status']}"}

    # Verify arrester has authority
    arrester_data = client.table("roles") \
        .select("id, character_name, positions, country_code") \
        .eq("sim_run_id", sim_run_id).eq("id", arrester_role_id).limit(1).execute().data
    if not arrester_data:
        return {"success": False, "status": "rejected",
                "message": f"Arrester {arrester_role_id!r} not found"}
    arrester = arrester_data[0]

    if not (has_position(arrester, "head_of_state") or has_position(arrester, "security")):
        return {"success": False, "status": "rejected",
                "message": f"{arrester_role_id!r} is not HoS or Security — cannot arrest"}

    if arrester["country_code"] != target["country_code"]:
        return {"success": False, "status": "rejected",
                "message": f"Cannot arrest {target_role_id!r} — different country"}

    if has_position(target, "head_of_state"):
        return {"success": False, "status": "rejected",
                "message": "Cannot arrest the Head of State"}

    # Execute arrest — update roles table (primary, frontend reads this)
    # Store arrest metadata so the banner can display who/why
    arrester_name = arrester.get("character_name", arrester_role_id)
    client.table("roles").update({
        "status": "arrested",
        "status_detail": {
            "arrested_by": arrester_role_id,
            "arrested_by_name": arrester_name,
            "justification": justification,
            "round": round_num,
        },
    }).eq("sim_run_id", sim_run_id).eq("id", target_role_id).execute()

    # Also update run_roles if it exists (legacy system, may not be seeded)
    try:
        update_role_status(
            sim_run_id, target_role_id, "arrested",
            changed_by=arrester_role_id,
            reason=justification,
            round_num=round_num,
        )
    except Exception as e:
        logger.debug("[arrest] run_roles update skipped: %s", e)

    logger.info("[arrest] %s arrested %s in round %d: %s",
                arrester_role_id, target_role_id, round_num, justification)

    return {
        "success": True,
        "status": "arrested",
        "arrested_role": target_role_id,
        "arrested_name": target.get("character_name", ""),
        "by": arrester_role_id,
        "round": round_num,
        "message": f"{target_role_id} arrested by {arrester_role_id}. Released at round end.",
    }


def release_role(
    sim_run_id: str,
    releaser_role_id: str,
    target_role_id: str,
    round_num: int,
) -> dict:
    """Manually release an arrested role (by HoS or Security). No limit."""
    client = get_client()

    target_data = client.table("roles") \
        .select("id, character_name, status, country_code") \
        .eq("sim_run_id", sim_run_id).eq("id", target_role_id).limit(1).execute().data
    if not target_data:
        return {"success": False, "message": f"Role {target_role_id} not found"}
    target = target_data[0]

    if target["status"] != "arrested":
        return {"success": False, "message": f"{target['character_name']} is not arrested"}

    releaser_data = client.table("roles") \
        .select("id, character_name, positions, country_code") \
        .eq("sim_run_id", sim_run_id).eq("id", releaser_role_id).limit(1).execute().data
    if not releaser_data:
        return {"success": False, "message": f"Releaser {releaser_role_id} not found"}
    releaser = releaser_data[0]

    if not (has_position(releaser, "head_of_state") or has_position(releaser, "security")):
        return {"success": False, "message": "Only HoS or Security can release arrested roles"}

    if releaser["country_code"] != target["country_code"]:
        return {"success": False, "message": "Can only release roles in your own country"}

    # Release
    client.table("roles").update({"status": "active", "status_detail": None}) \
        .eq("sim_run_id", sim_run_id).eq("id", target_role_id).execute()

    logger.info("[arrest] %s released %s in round %d", releaser_role_id, target_role_id, round_num)

    return {
        "success": True,
        "released_role": target_role_id,
        "released_name": target["character_name"],
        "message": f"{target['character_name']} released from arrest by {releaser['character_name']}",
    }


def release_arrested_roles(sim_run_id: str, round_num: int) -> list[str]:
    """Auto-release all arrested roles at round end.

    Called by resolve_round or the round orchestrator at the end of each
    round. Returns list of role_ids that were released.

    Args:
        sim_run_id: The current run.
        round_num: The round that just ended (arrested in this round → released now).
    """
    client = get_client()

    res = client.table("run_roles").select("role_id,character_name") \
        .eq("sim_run_id", sim_run_id) \
        .eq("status", "arrested") \
        .execute()

    released = []
    for row in (res.data or []):
        rid = row["role_id"]
        try:
            update_role_status(
                sim_run_id, rid, "active",
                changed_by="system",
                reason=f"Auto-released at end of round {round_num}",
                round_num=round_num,
            )
        except Exception:
            pass
        # Restore roles table status + clear arrest metadata
        client.table("roles").update({"status": "active", "status_detail": None}).eq("sim_run_id", sim_run_id).eq("id", rid).execute()
        released.append(rid)

    # Also release from roles table directly (in case run_roles was not seeded)
    arrested_roles = client.table("roles").select("id") \
        .eq("sim_run_id", sim_run_id).eq("status", "arrested").execute().data or []
    for r in arrested_roles:
        if r["id"] not in released:
            client.table("roles").update({"status": "active", "status_detail": None}).eq("sim_run_id", sim_run_id).eq("id", r["id"]).execute()
            released.append(r["id"])

    if released:
        logger.info("[arrest] auto-released %d roles at end of R%d: %s",
                    len(released), round_num, released)

    return released
