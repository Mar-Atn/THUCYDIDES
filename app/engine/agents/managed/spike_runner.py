"""Phase 5 — M5 Spike experiment runner.

Runs the Managed Agent spike: creates a fresh sim_run, initializes a
Dealer/Columbia agent session, sends a sequence of round events, and
measures the results.

Usage:
    cd app && python -m engine.agents.managed.spike_runner

Requires:
    ANTHROPIC_API_KEY in environment
    SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY in environment
"""
from __future__ import annotations

import json
import logging
import os
import sys
import time
from datetime import datetime, timezone

# Ensure engine is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from engine.agents.managed.session_manager import ManagedSessionManager
from engine.agents.managed.event_handler import (
    format_transcript_text,
    log_transcript_to_observatory,
    extract_actions_from_transcript,
)
from engine.services.supabase import get_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ROLE_ID = "dealer"           # Columbia Head of State
COUNTRY_CODE = "columbia"
MODEL = "claude-sonnet-4-6"

# Experiment events — the script sends these in sequence
EXPERIMENT_EVENTS = [
    {
        "label": "Round 1 Start",
        "message": (
            "Round 1 has started. You are in Phase A (45 minutes of active play).\n\n"
            "This is the beginning of the simulation. Explore your situation — "
            "review your country's state, check your forces, understand your "
            "relationships, and decide what to do.\n\n"
            "You have up to 3 actions this round. Choose wisely."
        ),
    },
    {
        "label": "Military Alert",
        "message": (
            "ALERT: Intelligence reports that Sarmatia has moved 3 ground units "
            "to the Eastern Ereb theater, closer to Ruthenia's border. This is "
            "a significant escalation.\n\n"
            "How does this affect your strategic calculus? Consider your "
            "alliances, your forces in the region, and your diplomatic options."
        ),
    },
    {
        "label": "Trade Proposal",
        "message": (
            "DIPLOMATIC INCOMING: Cathay's leader Helmsman has proposed a "
            "bilateral trade agreement. The terms include reduced tariffs on "
            "technology exports in exchange for Columbia lowering agricultural "
            "tariffs.\n\n"
            "Review with get_pending_proposals and decide how to respond."
        ),
    },
    {
        "label": "Round 1 Mandatory",
        "message": (
            "Round 1 is ending. You MUST submit mandatory inputs before the "
            "round closes:\n\n"
            "1. Budget allocation (set_budget): social spending multiplier, "
            "military coins, tech coins\n"
            "2. Tariff levels (set_tariff): review and adjust if needed\n\n"
            "If you do not submit these, your parliament will impose defaults.\n\n"
            "After mandatory inputs, write your notes — record your strategic "
            "plan, observations, and relationship notes for Round 2."
        ),
    },
    {
        "label": "Round 2 Start",
        "message": (
            "Round 2 has started. Six months have passed.\n\n"
            "Check your notes from Round 1 — do you remember your plan? "
            "Review what happened last round using get_recent_events.\n\n"
            "New developments may have occurred. Assess and act."
        ),
    },
]


# ---------------------------------------------------------------------------
# Sim Run creation (simplified — uses existing sim_run or creates one)
# ---------------------------------------------------------------------------

def find_or_create_sim_run() -> tuple[str, str]:
    """Find an existing spike sim_run or create a fresh one.

    Returns:
        (sim_run_id, scenario_code) tuple.
    """
    client = get_client()

    # Look for an existing spike run first
    existing = (
        client.table("sim_runs")
        .select("id,scenario_id")
        .eq("name", "M5_SPIKE_MANAGED_AGENT")
        .eq("status", "active")
        .limit(1)
        .execute()
    )
    if existing.data:
        row = existing.data[0]
        logger.info("Found existing spike sim_run: %s", row["id"])
        return row["id"], row["id"]

    # Reuse the latest active sim_run for the spike (read-only from agent's
    # perspective — actions write to agent_decisions, not game state).
    active_run = (
        client.table("sim_runs")
        .select("id,name")
        .eq("status", "active")
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if active_run.data:
        row = active_run.data[0]
        logger.info("Reusing active sim_run '%s' (%s) for spike", row["name"], row["id"])
        return row["id"], row["id"]

    raise RuntimeError("No active sim_run found in the database. Create one via the UI first.")


# ---------------------------------------------------------------------------
# Main experiment
# ---------------------------------------------------------------------------

def run_spike() -> dict:
    """Run the M5 managed agent spike experiment.

    Returns:
        Results dict with measurements, transcript, and cost.
    """
    logger.info("=" * 70)
    logger.info("M5 SPIKE — Persistent AI Participant via Managed Agents")
    logger.info("=" * 70)

    start_time = time.time()
    results: dict = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "role_id": ROLE_ID,
        "country_code": COUNTRY_CODE,
        "model": MODEL,
        "events": [],
        "errors": [],
    }

    # 1. Find or create sim_run
    logger.info("Step 1: Finding/creating sim_run...")
    try:
        sim_run_id, scenario_code = find_or_create_sim_run()
        results["sim_run_id"] = sim_run_id
        results["scenario_code"] = scenario_code
        logger.info("Using sim_run: %s (scenario: %s)", sim_run_id, scenario_code)
    except Exception as e:
        logger.error("Failed to create sim_run: %s", e)
        results["errors"].append(f"sim_run creation failed: {e}")
        return results

    # 2. Create managed agent session
    logger.info("Step 2: Creating managed agent session...")
    manager = ManagedSessionManager()
    try:
        ctx = manager.create_session(
            role_id=ROLE_ID,
            country_code=COUNTRY_CODE,
            sim_run_id=sim_run_id,
            scenario_code=scenario_code,
            round_num=1,
            model=MODEL,
        )
        results["session_id"] = ctx.session_id
        results["agent_id"] = ctx.agent_id
        logger.info("Session created: %s (agent: %s)", ctx.session_id, ctx.agent_id)
    except Exception as e:
        logger.error("Failed to create session: %s", e)
        results["errors"].append(f"session creation failed: {e}")
        return results

    # 3. Send experiment events
    logger.info("Step 3: Running experiment events...")
    for i, event_spec in enumerate(EXPERIMENT_EVENTS):
        label = event_spec["label"]
        message = event_spec["message"]

        # Update round number for round transitions
        if "Round 2" in label:
            manager.update_round(ctx, 2)

        logger.info("\n--- Event %d/%d: %s ---", i + 1, len(EXPERIMENT_EVENTS), label)
        event_start = time.time()

        try:
            transcript = manager.send_event(ctx, message)
            event_elapsed = time.time() - event_start

            # Log to observatory
            log_transcript_to_observatory(
                sim_run_id, COUNTRY_CODE, ctx.round_num, transcript,
            )

            # Extract actions
            actions = extract_actions_from_transcript(transcript)

            event_result = {
                "label": label,
                "elapsed_seconds": round(event_elapsed, 1),
                "transcript_entries": len(transcript),
                "actions_submitted": len(actions),
                "actions": actions,
                "transcript_text": format_transcript_text(transcript),
            }
            results["events"].append(event_result)

            # Print transcript for live observation
            print(f"\n{'='*70}")
            print(f"EVENT: {label} ({event_elapsed:.1f}s)")
            print(f"{'='*70}")
            print(format_transcript_text(transcript))

        except Exception as e:
            logger.error("Event '%s' failed: %s", label, e)
            results["errors"].append(f"Event '{label}' failed: {e}")
            results["events"].append({
                "label": label,
                "error": str(e),
            })

    # 4. Collect measurements
    total_elapsed = time.time() - start_time
    cost = manager.get_cost_estimate(ctx)

    results["measurements"] = {
        "total_elapsed_seconds": round(total_elapsed, 1),
        "total_events": len(EXPERIMENT_EVENTS),
        "total_actions_submitted": ctx.actions_submitted,
        "token_usage": cost,
        "tool_calls": ctx.tool_executor.call_log if ctx.tool_executor else [],
    }

    # 5. Print summary
    print(f"\n{'='*70}")
    print("EXPERIMENT COMPLETE")
    print(f"{'='*70}")
    print(f"Duration: {total_elapsed:.1f}s")
    print(f"Actions submitted: {ctx.actions_submitted}")
    print(f"Input tokens: {cost['input_tokens']:,}")
    print(f"Output tokens: {cost['output_tokens']:,}")
    print(f"Estimated cost: ${cost['total_cost_usd']:.4f}")
    print(f"Errors: {len(results['errors'])}")
    if results["errors"]:
        for err in results["errors"]:
            print(f"  - {err}")

    # 6. Save results
    results_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "..",
        "MODULES", "M5_AI_PARTICIPANT", "SPIKE",
    )
    os.makedirs(results_path, exist_ok=True)
    results_file = os.path.join(results_path, "spike_results.json")
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    logger.info("Results saved to %s", results_file)

    # 7. Cleanup
    logger.info("Cleaning up session...")
    manager.cleanup(ctx)

    return results


if __name__ == "__main__":
    run_spike()
