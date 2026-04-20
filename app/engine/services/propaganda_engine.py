"""Propaganda Engine — stability manipulation via disinformation.

55% success. Two modes: boost own stability (+0.3) or destabilize
target (-0.3). Diminishing returns per successive use against same
target. Detection 25%, attribution 20%.
"""

from __future__ import annotations

import logging
import random

from engine.services.common import get_scenario_id, write_event
from engine.services.supabase import get_client

logger = logging.getLogger(__name__)

SUCCESS_PROB = 0.55
DETECTION_PROB = 1.0   # always detected (2026-04-20)
ATTRIBUTION_PROB = 0.20
BASE_EFFECT = 0.3  # stability change
DIMINISHING_FACTOR = 0.5  # each repeat halves the effect


def execute_propaganda(
    sim_run_id: str,
    round_num: int,
    attacker_country: str,
    attacker_role: str,
    target_country: str,
    intent: str,  # "boost" or "destabilize"
    content: str = "",
    precomputed_rolls: dict | None = None,
) -> dict:
    """Execute propaganda operation.

    Returns ``{success, stability_change, detected, attributed, narrative}``.
    """
    client = get_client()
    pre = precomputed_rolls or {}

    success_roll = pre.get("success_roll", random.random())
    detection_roll = pre.get("detection_roll", random.random())
    attribution_roll = pre.get("attribution_roll", random.random())

    success = success_roll < SUCCESS_PROB
    detected = detection_roll < DETECTION_PROB
    attributed = detected and (attribution_roll < ATTRIBUTION_PROB)

    stability_change = 0.0

    if success:
        # Calculate effect with diminishing returns
        prior_uses = _count_prior_uses(client, sim_run_id, attacker_country, target_country)
        effect = BASE_EFFECT * (DIMINISHING_FACTOR ** prior_uses)

        if intent == "boost":
            stability_change = effect
        else:  # destabilize
            stability_change = -effect

        # Apply to target country's stability
        _apply_stability_change(client, sim_run_id, round_num, target_country, stability_change)

    # Events
    scenario_id = get_scenario_id(client, sim_run_id)

    # Attacker always sees result
    write_event(client, sim_run_id, scenario_id, round_num, attacker_country,
                 "propaganda_result",
                 f"[CLASSIFIED] Propaganda {intent} on {target_country}: "
                 f"{'SUCCESS' if success else 'FAILED'}"
                 + (f" (stability {stability_change:+.2f})" if success else ""),
                 {"success": success, "target": target_country, "intent": intent,
                  "stability_change": stability_change, "detected": detected,
                  "attributed": attributed})

    if detected:
        if attributed:
            write_event(client, sim_run_id, scenario_id, round_num, target_country,
                         "propaganda_detected_attributed",
                         f"PROPAGANDA: {attacker_country} ran {intent} campaign against {target_country}"
                         + (f" — stability {stability_change:+.2f}" if success else " — failed"),
                         {"attacker": attacker_country, "target": target_country,
                          "intent": intent, "success": success, "attributed": True})
        else:
            write_event(client, sim_run_id, scenario_id, round_num, target_country,
                         "propaganda_detected_anonymous",
                         f"PROPAGANDA: unknown actor ran {intent} campaign against {target_country}"
                         + (f" — stability {stability_change:+.2f}" if success else " — failed"),
                         {"target": target_country, "intent": intent,
                          "success": success, "attributed": False})

    # Log the use for diminishing returns tracking
    if success:
        _log_use(client, sim_run_id, scenario_id, round_num, attacker_country, target_country, intent)

    logger.info("[propaganda] %s→%s (%s): success=%s change=%+.2f",
                attacker_country, target_country, intent, success, stability_change)

    return {
        "success": success,
        "target_country": target_country,
        "intent": intent,
        "stability_change": round(stability_change, 3),
        "detected": detected,
        "attributed": attributed,
        "narrative": f"Propaganda {intent} on {target_country}: "
                     f"{'SUCCESS' if success else 'FAILED'}"
                     + (f" (stability {stability_change:+.2f})" if success else ""),
    }


def _count_prior_uses(client, sim_run_id, attacker_cc, target_cc) -> int:
    """Count prior successful propaganda uses by this attacker against this target."""
    try:
        res = client.table("observatory_events").select("id", count="exact") \
            .eq("sim_run_id", sim_run_id) \
            .eq("country_code", attacker_cc) \
            .eq("event_type", "propaganda_use_logged") \
            .execute()
        # Filter by target in payload (can't do nested JSON filter easily)
        # Simplified: count all propaganda_use_logged by this attacker
        return res.count or 0
    except Exception:
        return 0


def _apply_stability_change(client, sim_run_id, round_num, target_cc, change):
    try:
        row = client.table("country_states_per_round").select("stability") \
            .eq("sim_run_id", sim_run_id).eq("round_num", round_num) \
            .eq("country_code", target_cc).limit(1).execute().data
        if row:
            old = int(row[0]["stability"]) if row[0].get("stability") is not None else 5
            new = max(0, min(10, old + int(round(change))))
            if new != old:
                client.table("country_states_per_round").update({"stability": new}) \
                    .eq("sim_run_id", sim_run_id).eq("round_num", round_num) \
                    .eq("country_code", target_cc).execute()
    except Exception as e:
        logger.warning("stability change failed: %s", e)


def _log_use(client, sim_run_id, scenario_id, round_num, attacker_cc, target_cc, intent):
    """Log successful use for diminishing returns tracking."""
    write_event(client, sim_run_id, scenario_id, round_num, attacker_cc,
                 "propaganda_use_logged",
                 f"Propaganda {intent} use logged: {attacker_cc}→{target_cc}",
                 {"target": target_cc, "intent": intent})


