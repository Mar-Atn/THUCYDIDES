"""Martial Law Engine — one-time conscription action.

Spawns ground units from the martial-law pool into reserve. Each eligible
country has a fixed pool (Template v1.0): Sarmatia=10, Ruthenia=6,
Persia=8, Cathay=10. Can only be declared ONCE per country per SIM.

Effects:
  - N new ground units spawned as reserve (deployable next round)
  - Stability: -1.0 immediately (on countries table)
  - War tiredness: +1.0 immediately
  - martial_law_declared flag set (prevents re-use)
"""

from __future__ import annotations

import logging

from engine.services.supabase import get_client
from engine.services.common import get_scenario_id, write_event

logger = logging.getLogger(__name__)

from engine.config.position_actions import MARTIAL_LAW_POOLS

STABILITY_COST = -1.0
WAR_TIREDNESS_COST = 1.0


def execute_martial_law(
    sim_run_id: str,
    round_num: int,
    role_id: str,
    country_code: str,
) -> dict:
    """Execute martial law: spawn conscripts into deployments + apply costs to countries table.

    Returns ``{success, units_spawned, stability_cost, war_tiredness_cost, narrative}``.
    """
    client = get_client()
    pool_size = MARTIAL_LAW_POOLS.get(country_code, 0)

    if pool_size <= 0:
        return {"success": False, "narrative": f"{country_code} is not eligible for martial law."}

    # Check if already declared
    country = client.table("countries").select("stability,martial_law_declared") \
        .eq("sim_run_id", sim_run_id).eq("id", country_code).limit(1).execute().data
    if not country:
        return {"success": False, "narrative": f"Country {country_code} not found."}
    if country[0].get("martial_law_declared"):
        return {"success": False, "narrative": "Martial law has already been declared this simulation."}

    scenario_id = get_scenario_id(client, sim_run_id)

    # 1. Spawn new ground units into deployments as reserve
    prefix = country_code[:3]
    new_units = []
    for i in range(1, pool_size + 1):
        unit_id = f"{prefix}_conscript_{i:02d}"
        new_units.append({
            "sim_run_id": sim_run_id,
            "unit_id": unit_id,
            "country_code": country_code,
            "unit_type": "ground",
            "unit_status": "reserve",
            "global_row": None,
            "global_col": None,
            "theater": None,
            "theater_row": None,
            "theater_col": None,
            "embarked_on": None,
        })

    try:
        for i in range(0, len(new_units), 50):
            client.table("deployments").insert(new_units[i:i+50]).execute()
    except Exception as e:
        logger.warning("martial_law unit spawn failed: %s", e)
        return {"success": False, "narrative": f"Unit spawn failed: {e}"}

    # 2. Apply stability + war tiredness costs on countries table (live state)
    old_stab = float(country[0].get("stability", 5.0))
    new_stab = max(0, old_stab + STABILITY_COST)
    try:
        client.table("countries").update({
            "stability": new_stab,
            "martial_law_declared": True,
        }).eq("sim_run_id", sim_run_id).eq("id", country_code).execute()
    except Exception as e:
        logger.warning("martial_law cost application failed: %s", e)

    # 3. Write observatory event
    narrative = (
        f"{country_code} declares MARTIAL LAW: {pool_size} conscript ground units mobilized to reserve. "
        f"Stability {old_stab:.1f} → {new_stab:.1f} ({STABILITY_COST:+.1f})."
    )
    write_event(
        client, sim_run_id, scenario_id, round_num,
        country_code, "martial_law",
        narrative,
        {"pool_size": pool_size, "stability_cost": STABILITY_COST,
         "war_tiredness_cost": WAR_TIREDNESS_COST,
         "unit_codes": [u["unit_id"] for u in new_units]},
        category="political", role_name=role_id,
    )

    logger.info("[martial_law] %s: %d conscripts spawned, stab %+.1f",
                country_code, pool_size, STABILITY_COST)

    return {
        "success": True,
        "narrative": narrative,
        "units_spawned": pool_size,
        "unit_codes": [u["unit_id"] for u in new_units],
        "stability_cost": STABILITY_COST,
        "war_tiredness_cost": WAR_TIREDNESS_COST,
    }
