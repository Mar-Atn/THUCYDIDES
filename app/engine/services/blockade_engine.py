"""Blockade Engine — naval blockade management at chokepoints.

Manages establish / lift / reduce operations on the 3 canonical chokepoints.
Called by action_dispatcher for player actions, and by combat resolution
for automatic integrity checks after unit losses.

All paths write to the `blockades` table.
"""

from __future__ import annotations

import logging

from engine.services.supabase import get_client
from engine.services.common import get_scenario_id, write_event
from engine.config.map_config import CHOKEPOINTS, hex_neighbors_bounded, is_sea_hex

logger = logging.getLogger(__name__)


def _has_naval_at_hex(client, sim_run_id: str, country_code: str, row: int, col: int) -> list[dict]:
    """Return naval deployments for country at the given hex."""
    return client.table("deployments").select("id, unit_id, unit_type") \
        .eq("sim_run_id", sim_run_id) \
        .eq("country_code", country_code) \
        .eq("global_row", row).eq("global_col", col) \
        .eq("unit_type", "naval").eq("unit_status", "active") \
        .execute().data or []


def _has_ground_adjacent(client, sim_run_id: str, country_code: str, row: int, col: int) -> list[dict]:
    """Return ground deployments for country on land hexes adjacent to (row, col)."""
    neighbors = hex_neighbors_bounded(row, col)
    land_neighbors = [(r, c) for r, c in neighbors if not is_sea_hex(r, c)]
    if not land_neighbors:
        return []
    # Query ground units at each adjacent land hex
    results: list[dict] = []
    for nr, nc in land_neighbors:
        units = client.table("deployments").select("id, unit_id, unit_type") \
            .eq("sim_run_id", sim_run_id) \
            .eq("country_code", country_code) \
            .eq("global_row", nr).eq("global_col", nc) \
            .eq("unit_type", "ground").eq("unit_status", "active") \
            .execute().data or []
        results.extend(units)
    return results


def _qualifying_units(client, sim_run_id: str, country_code: str, zone_id: str) -> dict:
    """Return qualifying units for a blockade at the given chokepoint.

    Returns {"naval": [...], "ground": [...]} where ground is only
    populated for chokepoints with ground_ok=True.
    """
    cp = CHOKEPOINTS.get(zone_id)
    if not cp:
        return {"naval": [], "ground": []}

    row, col = cp["hex"]
    naval = _has_naval_at_hex(client, sim_run_id, country_code, row, col)
    ground: list[dict] = []
    if cp.get("ground_ok"):
        ground = _has_ground_adjacent(client, sim_run_id, country_code, row, col)
    return {"naval": naval, "ground": ground}


def establish_blockade(
    sim_run_id: str,
    country_code: str,
    zone_id: str,
    level: str,
    round_num: int,
    role_id: str,
) -> dict:
    """Establish a blockade at a chokepoint.

    Requires the country to have a naval unit at the chokepoint hex.
    Gulf Gate also accepts a ground unit on an adjacent land hex.
    """
    if zone_id not in CHOKEPOINTS:
        return {"success": False, "narrative": f"Unknown chokepoint: {zone_id}"}

    if level not in ("partial", "full"):
        return {"success": False, "narrative": f"Invalid blockade level: {level}. Must be 'partial' or 'full'."}

    cp = CHOKEPOINTS[zone_id]
    client = get_client()

    # Check for existing active blockade at this chokepoint
    existing = client.table("blockades").select("id, imposer_country_code, level") \
        .eq("sim_run_id", sim_run_id) \
        .eq("zone_id", zone_id) \
        .eq("status", "active") \
        .execute().data or []
    if existing:
        imposer = existing[0]["imposer_country_code"]
        if imposer == country_code:
            return {"success": False, "narrative": f"You already have an active blockade at {cp['name']}."}
        return {"success": False, "narrative": f"{cp['name']} is already blockaded by {imposer}. Use attack to break it."}

    # Check qualifying units
    units = _qualifying_units(client, sim_run_id, country_code, zone_id)
    if not units["naval"] and not units["ground"]:
        return {"success": False, "narrative": f"No qualifying units at {cp['name']}. Need a naval unit at hex {cp['hex']}" +
                (f" or a ground unit on adjacent land." if cp.get("ground_ok") else ".")}

    # Insert blockade
    try:
        client.table("blockades").insert({
            "sim_run_id": sim_run_id,
            "zone_id": zone_id,
            "imposer_country_code": country_code,
            "status": "active",
            "level": level,
            "established_round": round_num,
            "notes": f"Established by {role_id}",
        }).execute()
    except Exception as e:
        logger.warning("blockade insert failed: %s", e)
        return {"success": False, "narrative": f"Database error: {e}"}

    # Write observatory event
    scenario_id = get_scenario_id(client, sim_run_id)
    write_event(
        client, sim_run_id, scenario_id, round_num,
        country_code, "naval_blockade",
        f"{country_code} establishes {level} blockade at {cp['name']}",
        {"zone_id": zone_id, "level": level, "operation": "establish"},
        category="military", role_name=role_id,
    )

    logger.info("[blockade] ESTABLISHED: %s at %s (%s)", country_code, cp["name"], level)
    return {
        "success": True,
        "narrative": f"{level.title()} blockade established at {cp['name']}.",
    }


def lift_blockade(
    sim_run_id: str,
    country_code: str,
    zone_id: str,
    round_num: int,
    role_id: str,
) -> dict:
    """Lift an active blockade. Only the imposer can lift voluntarily."""
    if zone_id not in CHOKEPOINTS:
        return {"success": False, "narrative": f"Unknown chokepoint: {zone_id}"}

    cp = CHOKEPOINTS[zone_id]
    client = get_client()

    existing = client.table("blockades").select("id, imposer_country_code") \
        .eq("sim_run_id", sim_run_id) \
        .eq("zone_id", zone_id) \
        .eq("status", "active") \
        .execute().data or []

    if not existing:
        return {"success": False, "narrative": f"No active blockade at {cp['name']}."}

    blockade = existing[0]
    if blockade["imposer_country_code"] != country_code:
        return {"success": False, "narrative": f"Only {blockade['imposer_country_code']} can lift the blockade at {cp['name']}."}

    try:
        client.table("blockades").update({
            "status": "lifted",
            "lifted_round": round_num,
        }).eq("id", blockade["id"]).execute()
    except Exception as e:
        logger.warning("blockade lift failed: %s", e)
        return {"success": False, "narrative": f"Database error: {e}"}

    scenario_id = get_scenario_id(client, sim_run_id)
    write_event(
        client, sim_run_id, scenario_id, round_num,
        country_code, "naval_blockade",
        f"{country_code} lifts blockade at {cp['name']}",
        {"zone_id": zone_id, "operation": "lift"},
        category="military", role_name=role_id,
    )

    logger.info("[blockade] LIFTED: %s at %s", country_code, cp["name"])
    return {
        "success": True,
        "narrative": f"Blockade at {cp['name']} lifted.",
    }


def reduce_blockade(
    sim_run_id: str,
    country_code: str,
    zone_id: str,
    round_num: int,
    role_id: str,
) -> dict:
    """Reduce a full blockade to partial. Only the imposer can reduce."""
    if zone_id not in CHOKEPOINTS:
        return {"success": False, "narrative": f"Unknown chokepoint: {zone_id}"}

    cp = CHOKEPOINTS[zone_id]
    client = get_client()

    existing = client.table("blockades").select("id, imposer_country_code, level") \
        .eq("sim_run_id", sim_run_id) \
        .eq("zone_id", zone_id) \
        .eq("status", "active") \
        .execute().data or []

    if not existing:
        return {"success": False, "narrative": f"No active blockade at {cp['name']}."}

    blockade = existing[0]
    if blockade["imposer_country_code"] != country_code:
        return {"success": False, "narrative": f"Only {blockade['imposer_country_code']} can modify the blockade at {cp['name']}."}

    if blockade["level"] == "partial":
        return {"success": False, "narrative": f"Blockade at {cp['name']} is already partial."}

    try:
        client.table("blockades").update({
            "level": "partial",
        }).eq("id", blockade["id"]).execute()
    except Exception as e:
        logger.warning("blockade reduce failed: %s", e)
        return {"success": False, "narrative": f"Database error: {e}"}

    scenario_id = get_scenario_id(client, sim_run_id)
    write_event(
        client, sim_run_id, scenario_id, round_num,
        country_code, "naval_blockade",
        f"{country_code} reduces blockade at {cp['name']} to partial",
        {"zone_id": zone_id, "operation": "reduce"},
        category="military", role_name=role_id,
    )

    logger.info("[blockade] REDUCED: %s at %s → partial", country_code, cp["name"])
    return {
        "success": True,
        "narrative": f"Blockade at {cp['name']} reduced to partial.",
    }


def get_blockade_status(sim_run_id: str) -> list[dict]:
    """Return all active blockades for a sim run."""
    client = get_client()
    result = client.table("blockades").select("*") \
        .eq("sim_run_id", sim_run_id) \
        .eq("status", "active") \
        .execute()
    return result.data or []


def check_blockade_integrity(sim_run_id: str) -> list[dict]:
    """Check all active blockades — auto-lift/reduce if units are gone.

    Called after combat resolution. For each active blockade:
    - If imposer has NO qualifying units at the chokepoint → auto-lift
    - If imposer has reduced units (some but fewer) → auto-reduce to partial
    Returns a list of changes made.
    """
    client = get_client()
    active = client.table("blockades").select("*") \
        .eq("sim_run_id", sim_run_id) \
        .eq("status", "active") \
        .execute().data or []

    if not active:
        return []

    changes: list[dict] = []

    for blockade in active:
        zone_id = blockade["zone_id"]
        imposer = blockade["imposer_country_code"]
        cp = CHOKEPOINTS.get(zone_id)
        if not cp:
            continue

        units = _qualifying_units(client, sim_run_id, imposer, zone_id)
        total_units = len(units["naval"]) + len(units["ground"])

        if total_units == 0:
            # Auto-lift: no qualifying units remain
            try:
                client.table("blockades").update({
                    "status": "lifted",
                    "lifted_round": blockade.get("established_round"),
                    "notes": (blockade.get("notes", "") or "") + " | Auto-lifted: no qualifying units.",
                }).eq("id", blockade["id"]).execute()
            except Exception as e:
                logger.warning("blockade auto-lift failed: %s", e)
                continue

            changes.append({
                "zone_id": zone_id,
                "chokepoint": cp["name"],
                "imposer": imposer,
                "action": "auto_lifted",
                "reason": "No qualifying units at chokepoint.",
            })
            logger.info("[blockade] AUTO-LIFTED: %s at %s — no units", imposer, cp["name"])

        elif blockade["level"] == "full" and len(units["naval"]) == 0:
            # Only ground support remains (Gulf Gate) — reduce to partial
            try:
                client.table("blockades").update({
                    "level": "partial",
                    "notes": (blockade.get("notes", "") or "") + " | Auto-reduced: naval units lost.",
                }).eq("id", blockade["id"]).execute()
            except Exception as e:
                logger.warning("blockade auto-reduce failed: %s", e)
                continue

            changes.append({
                "zone_id": zone_id,
                "chokepoint": cp["name"],
                "imposer": imposer,
                "action": "auto_reduced",
                "reason": "Naval units lost; ground-only support reduces to partial.",
            })
            logger.info("[blockade] AUTO-REDUCED: %s at %s → partial (no naval)", imposer, cp["name"])

    return changes
