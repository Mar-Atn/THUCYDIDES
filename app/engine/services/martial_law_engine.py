"""Martial Law Engine — one-time conscription action.

Spawns ground units from the martial-law pool into reserve. Each eligible
country has a fixed pool (Template v1.0): Sarmatia=10, Ruthenia=6,
Persia=8, Cathay=10. Can only be declared ONCE per country per SIM.

Effects:
  - N new ground units spawned as reserve (deployable next round)
  - Stability: -1.0 immediately
  - War tiredness: +1.0 immediately
  - martial_law_declared flag set (prevents re-use)
"""

from __future__ import annotations

import logging

from engine.services.supabase import get_client

logger = logging.getLogger(__name__)

MARTIAL_LAW_POOLS: dict[str, int] = {
    "sarmatia": 10,
    "ruthenia": 6,
    "persia": 8,
    "cathay": 10,
}

STABILITY_COST = -1.0
WAR_TIREDNESS_COST = 1.0


def execute_martial_law(
    sim_run_id: str,
    country_code: str,
    round_num: int,
    declared_by_role: str = "hos",
) -> dict:
    """Execute martial law: spawn conscripts + apply costs.

    Caller MUST have validated eligibility via domestic_validator first.

    Returns ``{success, units_spawned, stability_cost, war_tiredness_cost}``.
    """
    client = get_client()
    pool_size = MARTIAL_LAW_POOLS.get(country_code, 0)

    if pool_size <= 0:
        return {"success": False, "message": f"{country_code} has no martial law pool"}

    # 1. Spawn new ground units into unit_states_per_round as reserve
    new_units = []
    for i in range(1, pool_size + 1):
        unit_code = f"{country_code[:3]}_conscript_{i:02d}"
        new_units.append({
            "sim_run_id": sim_run_id,
            "round_num": round_num,
            "unit_code": unit_code,
            "country_code": country_code,
            "unit_type": "ground",
            "status": "reserve",
            "global_row": None,
            "global_col": None,
            "theater": None,
            "theater_row": None,
            "theater_col": None,
            "embarked_on": None,
            "notes": f"Martial law conscript R{round_num}",
        })

    try:
        # Also need scenario_id for the denorm column
        run = client.table("sim_runs").select("scenario_id").eq("id", sim_run_id).limit(1).execute()
        scenario_id = run.data[0]["scenario_id"] if run.data else None
        for u in new_units:
            u["scenario_id"] = scenario_id

        for i in range(0, len(new_units), 50):
            client.table("unit_states_per_round").insert(new_units[i:i+50]).execute()
    except Exception as e:
        logger.warning("martial_law unit spawn failed: %s", e)
        return {"success": False, "message": f"Unit spawn failed: {e}"}

    # 2. Apply stability + war tiredness costs
    try:
        row = client.table("country_states_per_round").select("stability,war_tiredness") \
            .eq("sim_run_id", sim_run_id).eq("round_num", round_num) \
            .eq("country_code", country_code).limit(1).execute().data
        if row:
            old_stab = float(row[0].get("stability", 5) or 5)
            old_wt = float(row[0].get("war_tiredness", 0) or 0)
            client.table("country_states_per_round").update({
                "stability": int(max(0, old_stab + STABILITY_COST)),
                "war_tiredness": int(old_wt + WAR_TIREDNESS_COST),
                "martial_law_declared": True,
            }).eq("sim_run_id", sim_run_id).eq("round_num", round_num) \
              .eq("country_code", country_code).execute()
    except Exception as e:
        logger.warning("martial_law cost application failed: %s", e)

    # 3. Event
    _write_event(client, sim_run_id, scenario_id, round_num, country_code,
                 "martial_law_declared",
                 f"{country_code} declares martial law: {pool_size} conscript units mobilized, "
                 f"stability {STABILITY_COST:+.1f}, war tiredness {WAR_TIREDNESS_COST:+.1f}",
                 {"pool_size": pool_size, "stability_cost": STABILITY_COST,
                  "war_tiredness_cost": WAR_TIREDNESS_COST,
                  "unit_codes": [u["unit_code"] for u in new_units]})

    logger.info("[martial_law] %s: %d conscripts spawned, stab %+.1f, wt %+.1f",
                country_code, pool_size, STABILITY_COST, WAR_TIREDNESS_COST)

    return {
        "success": True,
        "units_spawned": pool_size,
        "unit_codes": [u["unit_code"] for u in new_units],
        "stability_cost": STABILITY_COST,
        "war_tiredness_cost": WAR_TIREDNESS_COST,
    }


def _write_event(client, sim_run_id, scenario_id, round_num, country_code, event_type, summary, payload):
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
