"""Election Meddling Engine — covert support manipulation.

40% success. Shifts political_support ±2-5%. Detection 45%, attribution 50%.
Only meaningful when elections are scheduled — but the engine applies the
shift regardless (election timing gate is a future enhancement).
"""

from __future__ import annotations

import logging
import random

from engine.services.common import get_scenario_id, write_event
from engine.services.supabase import get_client

logger = logging.getLogger(__name__)

SUCCESS_PROB = 0.40
DETECTION_PROB = 0.45
ATTRIBUTION_PROB = 0.50
SUPPORT_SHIFT_MIN = 2
SUPPORT_SHIFT_MAX = 5


def execute_election_meddling(
    sim_run_id: str,
    round_num: int,
    attacker_country: str,
    attacker_role: str,
    target_country: str,
    direction: str,  # "boost" or "undermine"
    candidate: str = "",
    precomputed_rolls: dict | None = None,
) -> dict:
    """Execute election meddling.

    Returns ``{success, support_change, detected, attributed, narrative}``.
    """
    client = get_client()
    pre = precomputed_rolls or {}

    success_roll = pre.get("success_roll", random.random())
    detection_roll = pre.get("detection_roll", random.random())
    attribution_roll = pre.get("attribution_roll", random.random())
    shift_roll = pre.get("shift_amount", random.randint(SUPPORT_SHIFT_MIN, SUPPORT_SHIFT_MAX))

    success = success_roll < SUCCESS_PROB
    detected = detection_roll < DETECTION_PROB
    attributed = detected and (attribution_roll < ATTRIBUTION_PROB)

    support_change = 0

    if success:
        support_change = shift_roll if direction == "boost" else -shift_roll
        _apply_stability_change(client, sim_run_id, round_num, target_country, support_change)

    scenario_id = get_scenario_id(client, sim_run_id)
    candidate_label = f" (candidate: {candidate})" if candidate else ""

    # Attacker sees full result
    write_event(client, sim_run_id, scenario_id, round_num, attacker_country,
                 "election_meddling_result",
                 f"[CLASSIFIED] Election meddling {direction} on {target_country}{candidate_label}: "
                 f"{'SUCCESS' if success else 'FAILED'}"
                 + (f" (support {support_change:+d}%)" if success else ""),
                 {"success": success, "target": target_country, "direction": direction,
                  "candidate": candidate, "support_change": support_change,
                  "detected": detected, "attributed": attributed})

    if detected:
        if attributed:
            write_event(client, sim_run_id, scenario_id, round_num, target_country,
                         "election_meddling_detected_attributed",
                         f"ELECTION MEDDLING: {attacker_country} interfered in {target_country}'s elections"
                         + (f" — support shifted {support_change:+d}%" if success else " — attempt failed"),
                         {"attacker": attacker_country, "target": target_country,
                          "direction": direction, "success": success, "attributed": True})
        else:
            write_event(client, sim_run_id, scenario_id, round_num, target_country,
                         "election_meddling_detected_anonymous",
                         f"ELECTION MEDDLING: unknown actor interfered in {target_country}'s elections"
                         + (f" — support shifted {support_change:+d}%" if success else " — attempt failed"),
                         {"target": target_country, "direction": direction,
                          "success": success, "attributed": False})

    logger.info("[election_meddling] %s→%s (%s): success=%s change=%+d%%",
                attacker_country, target_country, direction, success, support_change)

    return {
        "success": success,
        "target_country": target_country,
        "direction": direction,
        "candidate": candidate,
        "support_change": support_change,
        "detected": detected,
        "attributed": attributed,
        "narrative": f"Election meddling {direction} on {target_country}: "
                     f"{'SUCCESS' if success else 'FAILED'}"
                     + (f" ({support_change:+d}%)" if success else ""),
    }


def _apply_stability_change(client, sim_run_id, round_num, target_cc, change):
    """Apply stability change (replaces old political_support change). 2026-04-15 simplification."""
    try:
        row = client.table("country_states_per_round").select("stability") \
            .eq("sim_run_id", sim_run_id).eq("round_num", round_num) \
            .eq("country_code", target_cc).limit(1).execute().data
        if row:
            old = float(row[0]["stability"]) if row[0].get("stability") is not None else 5.0
            # Convert support-scale change (±2-5) to stability-scale (±0.2-0.5)
            stab_change = change / 10.0
            new = max(0.0, min(10.0, old + stab_change))
            client.table("country_states_per_round").update({"stability": new}) \
                .eq("sim_run_id", sim_run_id).eq("round_num", round_num) \
                .eq("country_code", target_cc).execute()
    except Exception as e:
        logger.warning("stability change failed: %s", e)


