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
from engine.services.run_roles import (
    get_run_role, update_role_status,
)
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
    # Verify target exists and is active
    target = get_run_role(sim_run_id, target_role_id)
    if not target:
        return {"success": False, "status": "rejected",
                "message": f"Target role {target_role_id!r} not found in this run"}

    if target["status"] != "active":
        return {"success": False, "status": "rejected",
                "message": f"Target {target_role_id!r} is already {target['status']}"}

    # Verify arrester has authority (checked by validator, but double-check)
    arrester = get_run_role(sim_run_id, arrester_role_id)
    if not arrester:
        return {"success": False, "status": "rejected",
                "message": f"Arrester {arrester_role_id!r} not found"}

    if not (has_position(arrester, "head_of_state") or has_position(arrester, "security")):
        return {"success": False, "status": "rejected",
                "message": f"{arrester_role_id!r} is not HoS or Security — cannot arrest"}

    if arrester["country_code"] != target["country_code"]:
        return {"success": False, "status": "rejected",
                "message": f"Cannot arrest {target_role_id!r} — different country"}

    # Execute arrest
    result = update_role_status(
        sim_run_id, target_role_id, "arrested",
        changed_by=arrester_role_id,
        reason=justification,
        round_num=round_num,
    )

    if not result["success"]:
        return {"success": False, "status": "error", "message": result.get("message", "unknown error")}

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
        update_role_status(
            sim_run_id, rid, "active",
            changed_by="system",
            reason=f"Auto-released at end of round {round_num}",
            round_num=round_num,
        )
        released.append(rid)

    if released:
        logger.info("[arrest] auto-released %d roles at end of R%d: %s",
                    len(released), round_num, released)

    return released
