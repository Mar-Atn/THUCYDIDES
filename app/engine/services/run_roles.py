"""Run Roles — per-run mutable role state.

ARCHITECTURE NOTE (2026-04-19):
The ``roles`` table is the single source of truth for per-run role state.
It stores: id, character_name, status, positions[], country_id, etc.

The old ``run_roles`` table was designed as a separate mutable copy but
was never reliably seeded. All code now reads/writes ``roles`` directly.
The ``run_roles`` table is kept in DB for backward compatibility but
is not read by any active code path.

Functions:
  get_run_role(sim_run_id, role_id)    — get role from roles table
  get_run_roles(sim_run_id, ...)       — query roles with filters
  update_role_status(...)              — update status + status_detail on roles
  seed_run_roles(sim_run_id)           — DEPRECATED (no-op)
"""

from __future__ import annotations

from engine.services.common import get_scenario_id, write_event

import logging
from typing import Optional

from engine.services.supabase import get_client

logger = logging.getLogger(__name__)


def seed_run_roles(sim_run_id: str) -> int:
    """DEPRECATED — roles table is used directly. No-op."""
    logger.debug("[run_roles] seed_run_roles is deprecated — roles table is primary")
    return 0


def get_run_role(sim_run_id: str, role_id: str) -> Optional[dict]:
    """Get one role's current state from the roles table.

    Returns dict with keys mapped for backward compatibility:
    role_id, character_name, status, country_code, positions, is_head_of_state.
    """
    client = get_client()
    res = client.table("roles") \
        .select("id, character_name, status, country_id, positions, position_type, status_detail") \
        .eq("sim_run_id", sim_run_id) \
        .eq("id", role_id) \
        .limit(1).execute()

    if not res.data:
        return None

    r = res.data[0]
    positions = r.get("positions") or []
    return {
        "role_id": r["id"],
        "character_name": r["character_name"],
        "status": r.get("status", "active"),
        "country_code": r["country_id"],
        "country_id": r["country_id"],
        "positions": positions,
        "position_type": r.get("position_type"),
        "is_head_of_state": "head_of_state" in positions,
        "is_military_chief": "military" in positions,
        "is_diplomat": "diplomat" in positions,
        "status_detail": r.get("status_detail"),
    }


def get_run_roles(
    sim_run_id: str,
    country_code: Optional[str] = None,
    status: Optional[str] = None,
) -> list[dict]:
    """Query roles with optional filters. Returns list of role dicts."""
    client = get_client()
    q = client.table("roles") \
        .select("id, character_name, status, country_id, positions, position_type") \
        .eq("sim_run_id", sim_run_id)
    if country_code:
        q = q.eq("country_id", country_code)
    if status:
        q = q.eq("status", status)
    rows = q.order("country_id").execute().data or []

    return [{
        "role_id": r["id"],
        "character_name": r["character_name"],
        "status": r.get("status", "active"),
        "country_code": r["country_id"],
        "country_id": r["country_id"],
        "positions": r.get("positions") or [],
        "position_type": r.get("position_type"),
        "is_head_of_state": "head_of_state" in (r.get("positions") or []),
    } for r in rows]


def update_role_status(
    sim_run_id: str,
    role_id: str,
    new_status: str,
    changed_by: str,
    reason: str,
    round_num: int,
) -> dict:
    """Update a role's status (arrest, kill, depose, reactivate).

    Updates the roles table directly (single source of truth).
    Returns ``{success, previous_status, new_status}``.
    """
    client = get_client()

    current = get_run_role(sim_run_id, role_id)
    if not current:
        return {"success": False, "message": f"role {role_id} not found"}

    prev_status = current["status"]

    # Update roles table (primary)
    try:
        update_data: dict = {
            "status": new_status,
            "status_detail": {
                "changed_by": changed_by,
                "reason": reason,
                "round": round_num,
                "previous": prev_status,
            },
        }
        if new_status == "active":
            update_data["status_detail"] = None  # clear on release/reactivate

        client.table("roles").update(update_data) \
            .eq("sim_run_id", sim_run_id) \
            .eq("id", role_id).execute()
    except Exception as e:
        return {"success": False, "message": str(e)}

    # Write observatory event
    scenario_id = get_scenario_id(client, sim_run_id)
    write_event(client, sim_run_id, scenario_id, round_num, current["country_code"],
                f"role_status_{new_status}",
                f"{role_id} ({current.get('character_name', '?')}): "
                f"{prev_status} → {new_status} by {changed_by} — {reason}",
                {"role_id": role_id, "previous": prev_status,
                 "new": new_status, "by": changed_by},
                category="political")

    logger.info("[roles] %s: %s → %s (by %s)", role_id, prev_status, new_status, changed_by)

    return {"success": True, "previous_status": prev_status, "new_status": new_status}


