"""SimRun creation — copies all template data from a source sim into a new SimRun.

This is the server-side counterpart to the SimRunWizard. It handles:
1. Creating the sim_runs row
2. Copying all 11 inherited tables (countries, roles, zones, etc.)
3. Applying wizard customizations (active/inactive roles, human/AI flags)

Tables copied (re-keyed by new sim_run_id):
  countries, roles, role_actions, relationships, zones, deployments,
  organizations, org_memberships, sanctions, tariffs, world_state (round 0 only)
"""

import logging
import uuid
from datetime import datetime, timezone

from engine.config.settings import settings

logger = logging.getLogger(__name__)


def _get_client():
    """Get Supabase service-role client."""
    from supabase import create_client
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def create_sim_run(
    *,
    name: str,
    source_sim_id: str,
    template_id: str,
    facilitator_id: str,
    schedule: dict,
    key_events: list,
    max_rounds: int,
    description: str | None = None,
    logo_url: str | None = None,
    role_customizations: list[dict] | None = None,
) -> dict:
    """Create a new SimRun with full data inheritance from source.

    Args:
        name: Display name for the new sim run.
        source_sim_id: Sim to copy template data from (default sim).
        template_id: Template reference ID.
        facilitator_id: User ID of the moderator creating this sim.
        schedule: Phase timing configuration.
        key_events: Scheduled events (elections, meetings, etc.).
        max_rounds: Number of rounds.
        description: Optional description.
        logo_url: Optional logo URL.
        role_customizations: List of {role_id, active, is_ai_operated} dicts.

    Returns:
        The created sim_runs row as dict.
    """
    client = _get_client()
    new_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    # Build role customization lookup
    custom_map: dict[str, dict] = {}
    if role_customizations:
        for rc in role_customizations:
            custom_map[rc["role_id"]] = rc

    # ── 1. Create sim_runs row ────────────────────────────────────────────
    logger.info("Creating SimRun %s (%s) from source %s", new_id, name, source_sim_id)

    # Get scenario_id from source
    source = client.table("sim_runs").select("scenario_id").eq("id", source_sim_id).single().execute()
    scenario_id = source.data.get("scenario_id") if source.data else None

    sim_run = {
        "id": new_id,
        "name": name,
        "template_id": template_id,
        "scenario_id": scenario_id,
        "facilitator_id": facilitator_id,
        "status": "setup",
        "current_round": 0,
        "current_phase": "pre",
        "schedule": schedule,
        "key_events": key_events,
        "max_rounds": max_rounds,
        "description": description,
        "logo_url": logo_url,
        "run_config": {},
        "auto_advance": False,
        "auto_approve": False,
        "created_at": now,
        "updated_at": now,
    }

    result = client.table("sim_runs").insert(sim_run).execute()
    if not result.data:
        raise ValueError("Failed to create sim_runs row")

    logger.info("SimRun row created: %s", new_id)

    # ── 2. Copy countries ─────────────────────────────────────────────────
    _copy_table(client, "countries", source_sim_id, new_id,
                id_field="id", id_is_text=True,
                exclude_cols=["created_at"])

    # ── 3. Copy roles (with customizations) ───────────────────────────────
    _copy_roles(client, source_sim_id, new_id, custom_map)

    # ── 4. Copy role_actions (only for active roles) ──────────────────────
    _copy_role_actions(client, source_sim_id, new_id, custom_map)

    # ── 5. Copy relationships (uuid id → regenerate) ───────────────────
    _copy_table(client, "relationships", source_sim_id, new_id,
                id_field="id", id_is_text=False,
                exclude_cols=["created_at"])

    # ── 6. Copy zones (text id → keep) ───────────────────────────────
    _copy_table(client, "zones", source_sim_id, new_id,
                id_field="id", id_is_text=True,
                exclude_cols=["created_at"])

    # ── 7. Copy deployments (uuid id → regenerate) ───────────────────
    _copy_table(client, "deployments", source_sim_id, new_id,
                id_field="id", id_is_text=False,
                exclude_cols=["created_at"])

    # ── 8. Copy organizations (text id → keep) ──────────────────────
    _copy_table(client, "organizations", source_sim_id, new_id,
                id_field="id", id_is_text=True,
                exclude_cols=["created_at"])

    # ── 9. Copy org_memberships (uuid id → regenerate) ───────────────
    _copy_table(client, "org_memberships", source_sim_id, new_id,
                id_field="id", id_is_text=False,
                exclude_cols=["created_at"])

    # ── 10. Copy sanctions (uuid id → regenerate) ────────────────────
    _copy_table(client, "sanctions", source_sim_id, new_id,
                id_field="id", id_is_text=False,
                exclude_cols=["created_at"])

    # ── 11. Copy tariffs (uuid id → regenerate) ─────────────────────
    _copy_table(client, "tariffs", source_sim_id, new_id,
                id_field="id", id_is_text=False,
                exclude_cols=["created_at"])

    # ── 12. Copy artefacts (text id → keep role_id references)
    _copy_table(client, "artefacts", source_sim_id, new_id,
                id_field="id", id_is_text=True,
                exclude_cols=["created_at"])

    # ── 13. Copy world_state (round 0 only) ──────────────────────────────
    _copy_world_state(client, source_sim_id, new_id)

    # ── 13. Count what we copied ─────────────────────────────────────────
    active_roles = [r for r in custom_map.values() if r.get("active", True)] if custom_map else []
    human_count = sum(1 for r in active_roles if not r.get("is_ai_operated", True))
    ai_count = sum(1 for r in active_roles if r.get("is_ai_operated", True))

    # If no customizations provided, count from copied roles
    if not custom_map:
        roles_data = client.table("roles").select("is_ai_operated").eq("sim_run_id", new_id).eq("status", "active").execute()
        human_count = sum(1 for r in roles_data.data if not r["is_ai_operated"])
        ai_count = sum(1 for r in roles_data.data if r["is_ai_operated"])

    # Update participant counts
    client.table("sim_runs").update({
        "human_participants": human_count,
        "ai_participants": ai_count,
    }).eq("id", new_id).execute()

    logger.info("SimRun %s fully created: %d human, %d AI participants", new_id, human_count, ai_count)

    # Return the full sim run
    final = client.table("sim_runs").select("*").eq("id", new_id).single().execute()
    return final.data


# ── Private helpers ───────────────────────────────────────────────────────────

def _copy_table(
    client,
    table: str,
    source_id: str,
    new_id: str,
    *,
    id_field: str | None = None,
    id_is_text: bool = False,
    exclude_cols: list[str] | None = None,
) -> int:
    """Copy all rows from source sim to new sim, re-keying sim_run_id.

    Args:
        table: Table name.
        source_id: Source sim_run_id.
        new_id: New sim_run_id.
        id_field: If the table has its own id column, regenerate it (uuid) or keep (text).
        id_is_text: If True, keep the id value as-is (e.g. country codes). If False, generate new UUID.
        exclude_cols: Columns to drop before insert (e.g. auto-generated timestamps).

    Returns:
        Number of rows copied.
    """
    exclude = set(exclude_cols or [])

    rows = client.table(table).select("*").eq("sim_run_id", source_id).execute()
    if not rows.data:
        logger.debug("No rows to copy for %s", table)
        return 0

    new_rows = []
    for row in rows.data:
        new_row = {k: v for k, v in row.items() if k not in exclude}
        new_row["sim_run_id"] = new_id

        # Handle id column
        if id_field and id_field in new_row:
            if not id_is_text:
                new_row[id_field] = str(uuid.uuid4())
            # If id_is_text, keep original value (e.g. "cathay", "zone_3_5")

        new_rows.append(new_row)

    # Batch insert (Supabase handles up to ~1000 rows per call)
    client.table(table).insert(new_rows).execute()
    logger.info("Copied %d rows to %s for sim %s", len(new_rows), table, new_id)
    return len(new_rows)


def _copy_roles(client, source_id: str, new_id: str, custom_map: dict) -> int:
    """Copy roles with wizard customizations applied.

    Customizations:
    - active: False → role gets status='inactive'
    - is_ai_operated: set per wizard choice
    """
    rows = client.table("roles").select("*").eq("sim_run_id", source_id).execute()
    if not rows.data:
        return 0

    new_rows = []
    for row in rows.data:
        new_row = {k: v for k, v in row.items() if k != "created_at"}
        new_row["sim_run_id"] = new_id
        # Keep role id as-is (text ids like "rampart", "ironhand")

        # Apply customizations
        role_id = row["id"]
        if role_id in custom_map:
            custom = custom_map[role_id]
            if not custom.get("active", True):
                new_row["status"] = "inactive"
            new_row["is_ai_operated"] = custom.get("is_ai_operated", row["is_ai_operated"])

        # Clear user assignment (fresh sim)
        new_row["user_id"] = None

        new_rows.append(new_row)

    client.table("roles").insert(new_rows).execute()
    active_count = sum(1 for r in new_rows if r.get("status") != "inactive")
    logger.info("Copied %d roles (%d active) for sim %s", len(new_rows), active_count, new_id)
    return len(new_rows)


def _copy_role_actions(client, source_id: str, new_id: str, custom_map: dict) -> int:
    """Copy role_actions, skipping inactive roles."""
    # Determine which roles are inactive
    inactive_roles = set()
    if custom_map:
        inactive_roles = {rid for rid, rc in custom_map.items() if not rc.get("active", True)}

    rows = client.table("role_actions").select("*").eq("sim_run_id", source_id).execute()
    if not rows.data:
        return 0

    new_rows = []
    for row in rows.data:
        if row["role_id"] in inactive_roles:
            continue  # Skip actions for inactive roles

        new_row = {k: v for k, v in row.items()}
        new_row["sim_run_id"] = new_id
        new_row["id"] = str(uuid.uuid4())  # New UUID for each role_action
        new_rows.append(new_row)

    if new_rows:
        # Batch in chunks of 500 to avoid payload limits
        for i in range(0, len(new_rows), 500):
            chunk = new_rows[i:i+500]
            client.table("role_actions").insert(chunk).execute()

    logger.info("Copied %d role_actions for sim %s (skipped %d inactive)",
                len(new_rows), new_id, len(rows.data) - len(new_rows))
    return len(new_rows)


def _copy_world_state(client, source_id: str, new_id: str) -> int:
    """Copy only round 0 world state as starting state."""
    rows = client.table("world_state").select("*").eq("sim_run_id", source_id).eq("round_num", 0).execute()
    if not rows.data:
        # If no round 0, copy the lowest round available
        rows = client.table("world_state").select("*").eq("sim_run_id", source_id).order("round_num").limit(1).execute()

    if not rows.data:
        logger.warning("No world_state to copy for sim %s", source_id)
        return 0

    new_row = {k: v for k, v in rows.data[0].items() if k != "created_at"}
    new_row["sim_run_id"] = new_id
    new_row["round_num"] = 0
    new_row["id"] = str(uuid.uuid4())

    client.table("world_state").insert(new_row).execute()
    logger.info("Copied world_state round 0 for sim %s", new_id)
    return 1
