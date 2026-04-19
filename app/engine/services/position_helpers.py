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

from engine.config.position_actions import compute_actions

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

    Keeps backward compatibility while positions array is the source of truth.
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
