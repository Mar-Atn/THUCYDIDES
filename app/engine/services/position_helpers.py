"""Position-based action helpers — recompute and sync role_actions.

Source of truth: engine/config/position_actions.py (rules engine)
This module bridges the rules engine to the DB:
  - Reads positions + country state from DB
  - Calls compute_actions() to derive the action set
  - Syncs role_actions table (add missing, remove stale)
"""

import logging
from typing import Optional

from supabase import Client

from engine.config.position_actions import (
    compute_actions, REACTIVE_ACTIONS, ACTION_LIMITS, LIMITED_ACTIONS,
    ORG_MEMBER_ACTIONS, ORG_CHAIRMAN_ACTIONS,
)

logger = logging.getLogger(__name__)


def recompute_role_actions(
    client: Client,
    sim_run_id: str,
    role_id: str,
) -> dict:
    """Recompute role_actions from positions + country state.

    Reads the role's positions array and country state from DB,
    computes the correct action set, and syncs the role_actions table.

    Returns:
        {
            "added": [...],    # actions that were added
            "removed": [...],  # actions that were removed
            "unchanged": [...] # actions that stayed the same
        }
    """
    # Load role
    role_data = (
        client.table("roles")
        .select("id, country_id, positions")
        .eq("sim_run_id", sim_run_id)
        .eq("id", role_id)
        .execute()
    ).data
    if not role_data:
        logger.warning("recompute_role_actions: role %s not found", role_id)
        return {"added": [], "removed": [], "unchanged": []}

    role = role_data[0]
    country_code = role["country_id"]
    positions = role.get("positions") or []

    # Load country state for dynamic conditions
    country_data = (
        client.table("countries")
        .select("nuclear_level, nuclear_confirmed, opec_member")
        .eq("sim_run_id", sim_run_id)
        .eq("id", country_code)
        .execute()
    ).data
    if not country_data:
        logger.warning("recompute_role_actions: country %s not found", country_code)
        return {"added": [], "removed": [], "unchanged": []}

    country_state = country_data[0]

    # Compute the correct action set
    computed = compute_actions(positions, country_code, country_state)

    # Load current role_actions from DB
    current_rows = (
        client.table("role_actions")
        .select("action_id")
        .eq("sim_run_id", sim_run_id)
        .eq("role_id", role_id)
        .execute()
    ).data or []
    current = {row["action_id"] for row in current_rows}

    # Diff
    to_add = computed - current
    to_remove = current - computed
    unchanged = current & computed

    # Apply changes
    if to_add:
        client.table("role_actions").insert([
            {"sim_run_id": sim_run_id, "role_id": role_id, "action_id": aid}
            for aid in sorted(to_add)
        ]).execute()
        logger.info("recompute_role_actions: %s +%d actions: %s",
                     role_id, len(to_add), sorted(to_add))

    if to_remove:
        for aid in to_remove:
            client.table("role_actions").delete().eq(
                "sim_run_id", sim_run_id
            ).eq("role_id", role_id).eq("action_id", aid).execute()
        logger.info("recompute_role_actions: %s -%d actions: %s",
                     role_id, len(to_remove), sorted(to_remove))

    return {
        "added": sorted(to_add),
        "removed": sorted(to_remove),
        "unchanged": sorted(unchanged),
    }


def recompute_country_actions(
    client: Client,
    sim_run_id: str,
    country_code: str,
) -> dict[str, dict]:
    """Recompute role_actions for ALL active roles in a country.

    Useful when country state changes (nuclear upgrade, OPEC join/leave).

    Returns:
        {role_id: {"added": [...], "removed": [...], "unchanged": [...]}, ...}
    """
    roles = (
        client.table("roles")
        .select("id")
        .eq("sim_run_id", sim_run_id)
        .eq("country_id", country_code)
        .eq("status", "active")
        .execute()
    ).data or []

    results = {}
    for role in roles:
        results[role["id"]] = recompute_role_actions(client, sim_run_id, role["id"])

    return results


def recompute_all_role_actions(
    client: Client,
    sim_run_id: str,
) -> dict:
    """Recompute role_actions for ALL active roles in a sim.

    - Computes actions from positions + country state via compute_actions()
    - Adds org-based actions (call_org_meeting for members, publish_org_decision for chairmen)
    - Preserves rows with notes='manual_override'
    - Sets uses_total for intel/covert/assassination per INTEL_LIMITS
    - Removes any reactive actions that shouldn't be in role_actions

    Returns:
        {
            "total_roles": int,
            "changes": [{role_id, added: [...], removed: [...]}],
            "manual_preserved": int,
        }
    """
    # Load all active roles
    roles = (
        client.table("roles")
        .select("id, country_id, positions")
        .eq("sim_run_id", sim_run_id)
        .eq("status", "active")
        .execute()
    ).data or []

    # Load all country states
    countries = (
        client.table("countries")
        .select("id, nuclear_level, nuclear_confirmed")
        .eq("sim_run_id", sim_run_id)
        .execute()
    ).data or []
    cs_map = {c["id"]: c for c in countries}

    # Load org memberships for org-based actions
    org_members_raw = (
        client.table("org_memberships")
        .select("country_id, role_in_org")
        .eq("sim_run_id", sim_run_id)
        .execute()
    ).data or []
    # Build set of country_ids that are org members, and chairmen
    org_member_countries: set[str] = set()
    org_chairman_countries: set[str] = set()
    for m in org_members_raw:
        org_member_countries.add(m["country_id"])
        if m.get("role_in_org") in ("chairman", "president", "secretary_general"):
            org_chairman_countries.add(m["country_id"])

    # Load ALL current role_actions (one query instead of N)
    all_ra = (
        client.table("role_actions")
        .select("role_id, action_id, notes")
        .eq("sim_run_id", sim_run_id)
        .execute()
    ).data or []

    # Index: role_id -> {action_id: notes}
    current_by_role: dict[str, dict[str, str]] = {}
    for ra in all_ra:
        rid = ra["role_id"]
        if rid not in current_by_role:
            current_by_role[rid] = {}
        current_by_role[rid][ra["action_id"]] = ra.get("notes") or ""

    changes = []
    manual_preserved = 0
    rows_to_insert = []
    rows_to_delete = []

    for role in roles:
        rid = role["id"]
        country = role["country_id"]
        positions = role.get("positions") or []
        cs = cs_map.get(country, {})

        # Compute actions from rules engine
        computed = compute_actions(positions, country, cs)

        # Add org-based actions
        if country in org_member_countries:
            computed.update(ORG_MEMBER_ACTIONS)
        if country in org_chairman_countries and positions:
            # Only roles with positions (not citizens) get chairman actions
            # In practice, HoS typically represents the country in orgs
            if "head_of_state" in positions:
                computed.update(ORG_CHAIRMAN_ACTIONS)

        # Remove any reactive actions (should never be in role_actions)
        computed -= REACTIVE_ACTIONS

        current = current_by_role.get(rid, {})
        current_actions = set(current.keys())

        to_add = computed - current_actions
        to_remove = current_actions - computed

        # Preserve manual overrides
        preserved_remove = set()
        for aid in to_remove:
            if current.get(aid) == "manual_override":
                preserved_remove.add(aid)
                manual_preserved += 1
        to_remove -= preserved_remove

        if to_add or to_remove:
            changes.append({
                "role_id": rid,
                "added": sorted(to_add),
                "removed": sorted(to_remove),
            })

        # Prepare batch operations
        for aid in to_add:
            row = {"sim_run_id": sim_run_id, "role_id": rid, "action_id": aid}
            # Set action limits (uses_total + uses_remaining)
            for pos in positions:
                limits = ACTION_LIMITS.get(pos, {})
                if aid in limits:
                    row["uses_total"] = limits[aid]
                    row["uses_remaining"] = limits[aid]
                    break
            rows_to_insert.append(row)

        for aid in to_remove:
            rows_to_delete.append((rid, aid))

    # Apply inserts in batches
    if rows_to_insert:
        batch_size = 500
        for i in range(0, len(rows_to_insert), batch_size):
            batch = rows_to_insert[i:i + batch_size]
            client.table("role_actions").insert(batch).execute()

    # Apply deletes
    for rid, aid in rows_to_delete:
        client.table("role_actions").delete().eq(
            "sim_run_id", sim_run_id
        ).eq("role_id", rid).eq("action_id", aid).execute()

    total_added = sum(len(c["added"]) for c in changes)
    total_removed = sum(len(c["removed"]) for c in changes)
    logger.info(
        "recompute_all: %d roles, +%d -%d actions, %d manual preserved",
        len(roles), total_added, total_removed, manual_preserved,
    )

    return {
        "total_roles": len(roles),
        "changes": changes,
        "manual_preserved": manual_preserved,
        "total_added": total_added,
        "total_removed": total_removed,
    }


def transfer_position(
    client: Client,
    sim_run_id: str,
    from_role_id: str,
    to_role_id: str,
    position: str,
) -> None:
    """Transfer a position from one role to another.

    Removes the position from from_role's positions array,
    adds it to to_role's positions array, then recomputes
    actions for both roles.
    """
    # Load both roles
    from_role = (
        client.table("roles")
        .select("id, positions")
        .eq("sim_run_id", sim_run_id)
        .eq("id", from_role_id)
        .execute()
    ).data
    to_role = (
        client.table("roles")
        .select("id, positions")
        .eq("sim_run_id", sim_run_id)
        .eq("id", to_role_id)
        .execute()
    ).data

    if not from_role or not to_role:
        logger.warning("transfer_position: role not found (from=%s, to=%s)",
                       from_role_id, to_role_id)
        return

    # Remove position from source
    from_positions = list(from_role[0].get("positions") or [])
    if position in from_positions:
        from_positions.remove(position)
    client.table("roles").update({"positions": from_positions}).eq(
        "sim_run_id", sim_run_id
    ).eq("id", from_role_id).execute()

    # Add position to target (avoid duplicates)
    to_positions = list(to_role[0].get("positions") or [])
    if position not in to_positions:
        to_positions.append(position)
    client.table("roles").update({"positions": to_positions}).eq(
        "sim_run_id", sim_run_id
    ).eq("id", to_role_id).execute()

    # Also sync legacy fields for backward compatibility
    _sync_legacy_fields(client, sim_run_id, from_role_id, from_positions)
    _sync_legacy_fields(client, sim_run_id, to_role_id, to_positions)

    # Transfer remaining usage for limited actions before recomputing
    # (recompute will set fresh uses_total, but we need to preserve uses_remaining)
    for action_id in LIMITED_ACTIONS:
        transfer_action_usage(client, sim_run_id, from_role_id, to_role_id, action_id)

    # Recompute actions for both
    recompute_role_actions(client, sim_run_id, from_role_id)
    recompute_role_actions(client, sim_run_id, to_role_id)

    logger.info("transfer_position: %s moved from %s to %s",
                position, from_role_id, to_role_id)


def _sync_legacy_fields(
    client: Client,
    sim_run_id: str,
    role_id: str,
    positions: list[str],
) -> None:
    """Sync legacy boolean fields (is_head_of_state, etc.) from positions array.

    DEPRECATED: This function will be removed when legacy boolean columns
    (is_head_of_state, is_military_chief, is_economy_officer, is_diplomat)
    are dropped from the DB schema via a Supabase migration. Until then,
    it keeps backward compatibility while positions[] is the source of truth.
    """
    update = {
        "is_head_of_state": "head_of_state" in positions,
        "is_military_chief": "military" in positions,
        "is_economy_officer": "economy" in positions,
        "is_diplomat": "diplomat" in positions,
    }
    client.table("roles").update(update).eq(
        "sim_run_id", sim_run_id
    ).eq("id", role_id).execute()


# ---------------------------------------------------------------------------
# Action usage tracking — limited actions (arrest, intel, covert, assassination)
# ---------------------------------------------------------------------------

def check_and_decrement_usage(
    client: Client,
    sim_run_id: str,
    role_id: str,
    action_id: str,
) -> dict:
    """Check if a limited action has remaining uses and decrement.

    Returns:
        {"allowed": True, "remaining": N} if action can proceed
        {"allowed": False, "remaining": 0, "message": "..."} if exhausted
        {"allowed": True, "remaining": None} if action has no limit
    """
    if action_id not in LIMITED_ACTIONS:
        return {"allowed": True, "remaining": None}

    row = (
        client.table("role_actions")
        .select("uses_total, uses_remaining")
        .eq("sim_run_id", sim_run_id)
        .eq("role_id", role_id)
        .eq("action_id", action_id)
        .limit(1)
        .execute()
    ).data

    if not row:
        return {"allowed": False, "remaining": 0, "message": f"Action {action_id} not available"}

    uses_total = row[0].get("uses_total")
    uses_remaining = row[0].get("uses_remaining")

    # No limit set
    if uses_total is None:
        return {"allowed": True, "remaining": None}

    # Check remaining
    if uses_remaining is None:
        uses_remaining = uses_total  # not yet initialized

    if uses_remaining <= 0:
        return {"allowed": False, "remaining": 0,
                "message": f"No {action_id} actions remaining (used all {uses_total})"}

    # Decrement
    new_remaining = uses_remaining - 1
    client.table("role_actions").update({"uses_remaining": new_remaining}).eq(
        "sim_run_id", sim_run_id
    ).eq("role_id", role_id).eq("action_id", action_id).execute()

    logger.info("[usage] %s:%s decremented: %d → %d", role_id, action_id, uses_remaining, new_remaining)
    return {"allowed": True, "remaining": new_remaining}


def get_action_usage(
    client: Client,
    sim_run_id: str,
    role_id: str,
    action_id: str,
) -> dict:
    """Get current usage info for a limited action (without decrementing).

    Returns {"uses_total": N, "uses_remaining": M} or {"uses_total": None}
    """
    if action_id not in LIMITED_ACTIONS:
        return {"uses_total": None, "uses_remaining": None}

    row = (
        client.table("role_actions")
        .select("uses_total, uses_remaining")
        .eq("sim_run_id", sim_run_id)
        .eq("role_id", role_id)
        .eq("action_id", action_id)
        .limit(1)
        .execute()
    ).data

    if not row:
        return {"uses_total": None, "uses_remaining": None}

    return {
        "uses_total": row[0].get("uses_total"),
        "uses_remaining": row[0].get("uses_remaining"),
    }


def transfer_action_usage(
    client: Client,
    sim_run_id: str,
    from_role_id: str,
    to_role_id: str,
    action_id: str,
) -> None:
    """Transfer remaining usage of a limited action from one role to another.

    Called during position reassignment. The new holder gets the remaining
    count from the old holder (not a fresh allocation).
    """
    if action_id not in LIMITED_ACTIONS:
        return

    # Get old holder's remaining
    old = (
        client.table("role_actions")
        .select("uses_remaining, uses_total")
        .eq("sim_run_id", sim_run_id)
        .eq("role_id", from_role_id)
        .eq("action_id", action_id)
        .limit(1)
        .execute()
    ).data

    if not old:
        return

    remaining = old[0].get("uses_remaining")
    if remaining is None:
        remaining = old[0].get("uses_total")

    # Set on new holder
    new = (
        client.table("role_actions")
        .select("id")
        .eq("sim_run_id", sim_run_id)
        .eq("role_id", to_role_id)
        .eq("action_id", action_id)
        .limit(1)
        .execute()
    ).data

    if new:
        client.table("role_actions").update({"uses_remaining": remaining}).eq(
            "sim_run_id", sim_run_id
        ).eq("role_id", to_role_id).eq("action_id", action_id).execute()
        logger.info("[usage] transferred %s %d remaining from %s to %s",
                    action_id, remaining or 0, from_role_id, to_role_id)
