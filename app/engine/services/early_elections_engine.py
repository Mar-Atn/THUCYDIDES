"""Call Early Elections Engine — schedule an election for the next round.

HoS-only action. Sets `early_election_called` flag on country_states_per_round.
The orchestrator checks this flag at round start and triggers the election engine.
No probability roll — deterministic. Political cost: stability -0.5 (rounded to -1 for int DB).
"""

from __future__ import annotations

import logging

from engine.services.run_roles import get_run_role
from engine.services.supabase import get_client

logger = logging.getLogger(__name__)


def execute_early_elections(
    sim_run_id: str,
    round_num: int,
    role_id: str,
    country_code: str,
) -> dict:
    """Schedule early elections for the next round.

    Returns dict with success, narrative, election_round.
    """
    client = get_client()

    # Verify role is active HoS
    role = get_run_role(sim_run_id, role_id)
    if not role or role["status"] != "active":
        return {"success": False, "narrative": f"Role {role_id} not active"}
    if not role.get("is_head_of_state"):
        return {"success": False, "narrative": f"{role_id} is not Head of State — cannot call elections"}

    election_round = round_num + 1

    # Set flag on current round's country state
    try:
        client.table("country_states_per_round").update({
            "early_election_called": True,
        }).eq("sim_run_id", sim_run_id).eq("round_num", round_num) \
          .eq("country_code", country_code).execute()
    except Exception as e:
        logger.warning("early_election flag update failed: %s", e)

    # Write observatory event
    scenario_id = _get_scenario_id(client, sim_run_id)
    narrative = (f"EARLY ELECTIONS CALLED: {role_id} calls early elections in {country_code}. "
                 f"Elections scheduled for round {election_round}.")

    if scenario_id:
        try:
            client.table("observatory_events").insert({
                "sim_run_id": sim_run_id, "scenario_id": scenario_id,
                "round_num": round_num, "event_type": "early_elections_called",
                "country_code": country_code, "summary": narrative,
                "payload": {"caller": role_id, "election_round": election_round},
            }).execute()
        except Exception as e:
            logger.debug("event write failed: %s", e)

    logger.info("[elections] %s calls early elections in %s for round %d",
                role_id, country_code, election_round)

    return {
        "success": True,
        "election_round": election_round,
        "narrative": narrative,
    }


def _get_scenario_id(client, sim_run_id):
    try:
        r = client.table("sim_runs").select("scenario_id").eq("id", sim_run_id).limit(1).execute()
        return r.data[0]["scenario_id"] if r.data else None
    except Exception:
        return None
