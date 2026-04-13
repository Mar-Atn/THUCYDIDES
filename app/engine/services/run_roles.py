"""Run Roles — per-run mutable role state.

Follows the same pattern as country_states_per_round: template-level
``roles`` table stays frozen; ``run_roles`` is cloned at run start and
mutated during the run (arrest, kill, coin changes, etc.).

Architecture (matching KING):
  roles (template)          ← canonical character definitions (frozen)
       ↓ seed_run_roles()
  run_roles (per-run)       ← mutable copy per sim_run

Functions:
  seed_run_roles(sim_run_id)         — clone template roles into run_roles
  get_run_role(sim_run_id, role_id)  — get one role's current state
  get_run_roles(sim_run_id, ...)     — query with filters
  update_role_status(sim_run_id, role_id, new_status, by, reason, round)
  update_personal_coins(sim_run_id, role_id, delta)
"""

from __future__ import annotations

import logging
from typing import Optional

from engine.services.supabase import get_client

logger = logging.getLogger(__name__)


def seed_run_roles(sim_run_id: str) -> int:
    """Clone template roles into run_roles for a new sim_run.

    Reads from the template-level ``roles`` table and creates one
    ``run_roles`` row per role with status='active' and starting
    personal_coins from the template.

    Returns the number of roles seeded.
    """
    client = get_client()

    # Read template roles
    res = client.table("roles").select(
        "id,character_name,country_id,title,is_head_of_state,"
        "is_military_chief,is_diplomat,personal_coins,powers"
    ).execute()
    template_roles = res.data or []

    if not template_roles:
        logger.warning("[run_roles] no template roles found — nothing to seed")
        return 0

    rows = []
    for r in template_roles:
        role_id = r.get("id") or r.get("role_id", "")
        if not role_id:
            continue
        rows.append({
            "sim_run_id": sim_run_id,
            "role_id": role_id,
            "country_code": r.get("country_id", ""),
            "character_name": r.get("character_name", ""),
            "title": r.get("title", ""),
            "is_head_of_state": bool(r.get("is_head_of_state")),
            "is_military_chief": bool(r.get("is_military_chief")),
            "is_diplomat": bool(r.get("is_diplomat")),
            "status": "active",
            "personal_coins": int(r.get("personal_coins") or 0),
            "powers": r.get("powers", ""),
        })

    if rows:
        try:
            client.table("run_roles").upsert(
                rows, on_conflict="sim_run_id,role_id"
            ).execute()
        except Exception as e:
            logger.warning("[run_roles] seed failed: %s", e)
            return 0

    logger.info("[run_roles] seeded %d roles for run %s", len(rows), sim_run_id)
    return len(rows)


def get_run_role(sim_run_id: str, role_id: str) -> Optional[dict]:
    """Get one role's current per-run state. Returns None if not found."""
    client = get_client()
    res = client.table("run_roles").select("*") \
        .eq("sim_run_id", sim_run_id) \
        .eq("role_id", role_id) \
        .limit(1).execute()
    return res.data[0] if res.data else None


def get_run_roles(
    sim_run_id: str,
    country_code: Optional[str] = None,
    status: Optional[str] = None,
) -> list[dict]:
    """Query run_roles with optional filters."""
    client = get_client()
    q = client.table("run_roles").select("*").eq("sim_run_id", sim_run_id)
    if country_code:
        q = q.eq("country_code", country_code)
    if status:
        q = q.eq("status", status)
    return q.order("country_code").execute().data or []


def update_role_status(
    sim_run_id: str,
    role_id: str,
    new_status: str,
    changed_by: str,
    reason: str,
    round_num: int,
) -> dict:
    """Update a role's status (arrest, kill, depose, reactivate).

    Returns ``{success, previous_status, new_status}``.
    """
    client = get_client()

    current = get_run_role(sim_run_id, role_id)
    if not current:
        return {"success": False, "message": f"role {role_id} not found in run"}

    prev_status = current["status"]

    try:
        client.table("run_roles").update({
            "status": new_status,
            "status_changed_round": round_num,
            "status_changed_by": changed_by,
            "status_change_reason": reason,
        }).eq("sim_run_id", sim_run_id) \
          .eq("role_id", role_id).execute()
    except Exception as e:
        return {"success": False, "message": str(e)}

    # Write event
    _write_event(client, sim_run_id, round_num, current["country_code"],
                 f"role_status_{new_status}",
                 f"{role_id} ({current.get('character_name', '?')}): "
                 f"{prev_status} → {new_status} by {changed_by} — {reason}",
                 {"role_id": role_id, "previous": prev_status,
                  "new": new_status, "by": changed_by})

    logger.info("[run_roles] %s: %s → %s (by %s)", role_id, prev_status, new_status, changed_by)
    return {"success": True, "previous_status": prev_status, "new_status": new_status}


def update_personal_coins(
    sim_run_id: str,
    role_id: str,
    delta: int,
) -> dict:
    """Adjust a role's personal coins by delta (positive or negative).

    Returns ``{success, new_balance}``.
    """
    client = get_client()

    current = get_run_role(sim_run_id, role_id)
    if not current:
        return {"success": False, "message": f"role {role_id} not found"}

    old_balance = int(current.get("personal_coins", 0))
    new_balance = max(0, old_balance + delta)

    try:
        client.table("run_roles").update({
            "personal_coins": new_balance,
        }).eq("sim_run_id", sim_run_id) \
          .eq("role_id", role_id).execute()
    except Exception as e:
        return {"success": False, "message": str(e)}

    return {"success": True, "previous_balance": old_balance, "new_balance": new_balance}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_event(client, sim_run_id, round_num, country_code, event_type, summary, payload):
    scenario_id = None
    try:
        r = client.table("sim_runs").select("scenario_id").eq("id", sim_run_id).limit(1).execute()
        if r.data:
            scenario_id = r.data[0].get("scenario_id")
    except Exception:
        pass
    if not scenario_id:
        return
    try:
        client.table("observatory_events").insert({
            "sim_run_id": sim_run_id,
            "scenario_id": scenario_id,
            "round_num": round_num,
            "event_type": event_type,
            "country_code": country_code,
            "summary": summary,
            "payload": payload,
        }).execute()
    except Exception as e:
        logger.debug("event write failed: %s", e)
