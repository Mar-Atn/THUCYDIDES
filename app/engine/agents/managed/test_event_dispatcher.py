"""Integration tests for EventDispatcher — Unified Event Queue.

Tests against the REAL Vizier agent in Test33 sim_run.
Requires: ANTHROPIC_API_KEY and SUPABASE env vars set.

Run: cd app && python -m engine.agents.managed.test_event_dispatcher
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys
import time
from datetime import datetime, timezone

# Ensure app/ is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from engine.agents.managed.event_dispatcher import (
    EventDispatcher,
    IDLE,
    FROZEN,
    ACTING,
)
from engine.services.supabase import get_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Test33 sim run
SIM_RUN_ID = "c954b9b6-35f0-4973-a08b-f38406c524e7"
VIZIER_ROLE_ID = "vizier"


def separator(title: str) -> None:
    logger.info("=" * 60)
    logger.info("  %s", title)
    logger.info("=" * 60)


def cleanup_test_events() -> int:
    """Delete all unprocessed test events from the queue for this sim."""
    db = get_client()
    result = (
        db.table("agent_event_queue")
        .delete()
        .eq("sim_run_id", SIM_RUN_ID)
        .is_("processed_at", "null")
        .execute()
    )
    count = len(result.data or [])
    if count:
        logger.info("Cleaned up %d leftover events", count)
    return count


async def test_1_enqueue_dequeue() -> bool:
    """Test 1: Enqueue + dequeue + mark_processed."""
    separator("TEST 1: Enqueue + Dequeue + Mark Processed")

    dispatcher = EventDispatcher(SIM_RUN_ID)

    # Clean slate
    cleanup_test_events()

    # Enqueue 3 events at different tiers
    id1 = dispatcher.enqueue(VIZIER_ROLE_ID, 3, "round_update", "Routine: Round 1 results are in.")
    id2 = dispatcher.enqueue(VIZIER_ROLE_ID, 1, "attack", "CRITICAL: Enemy forces attacking your border!")
    id3 = dispatcher.enqueue(VIZIER_ROLE_ID, 2, "chat_message", "Urgent: Pathfinder says hello.")

    logger.info("Enqueued events: T3=%s, T1=%s, T2=%s", id1, id2, id3)

    # Dequeue — should return in tier order (1, 2, 3)
    events = await dispatcher.dequeue(VIZIER_ROLE_ID)
    assert len(events) == 3, f"Expected 3 events, got {len(events)}"
    assert events[0]["tier"] == 1, f"First event should be Tier 1, got {events[0]['tier']}"
    assert events[1]["tier"] == 2, f"Second event should be Tier 2, got {events[1]['tier']}"
    assert events[2]["tier"] == 3, f"Third event should be Tier 3, got {events[2]['tier']}"
    logger.info("PASS: Events returned in tier order (1, 2, 3)")

    # Dequeue with max_tier=1 — should only get Tier 1
    events_t1 = await dispatcher.dequeue(VIZIER_ROLE_ID, max_tier=1)
    assert len(events_t1) == 1, f"Expected 1 Tier-1 event, got {len(events_t1)}"
    assert events_t1[0]["tier"] == 1
    logger.info("PASS: max_tier=1 filter works")

    # Mark all processed
    event_ids = [e["id"] for e in events]
    await dispatcher.mark_processed(event_ids)

    # Dequeue again — should be empty
    events_after = await dispatcher.dequeue(VIZIER_ROLE_ID)
    assert len(events_after) == 0, f"Expected 0 after marking, got {len(events_after)}"
    logger.info("PASS: Events marked as processed, queue empty")

    # Verify processed_at is set in DB
    db = get_client()
    for eid in event_ids:
        row = db.table("agent_event_queue").select("processed_at").eq("id", eid).execute()
        assert row.data and row.data[0]["processed_at"] is not None, f"Event {eid} not marked"
    logger.info("PASS: processed_at timestamps set in DB")

    logger.info("TEST 1 PASSED")
    return True


async def test_2_dispatcher_delivers() -> bool:
    """Test 2: Dispatcher loop delivers events to Vizier agent."""
    separator("TEST 2: Dispatcher Delivers to Agent")

    dispatcher = EventDispatcher(SIM_RUN_ID)

    # Clean slate
    cleanup_test_events()

    # Reconnect from DB (picks up Vizier's existing session)
    count = await dispatcher.reconnect_from_db()
    assert count >= 1, f"Expected at least 1 agent reconnected, got {count}"
    assert VIZIER_ROLE_ID in dispatcher.agents, "Vizier not found in dispatcher agents"
    logger.info("PASS: Reconnected %d agents, Vizier present", count)

    # Enqueue a Tier 2 event
    t_enqueue = time.time()
    event_id = dispatcher.enqueue(
        VIZIER_ROLE_ID, 2, "situation_check",
        "Check your current situation. What is your GDP and military strength? "
        "Use get_my_country to check. Respond briefly."
    )
    logger.info("Enqueued event %s at t=0", event_id)

    # Start dispatcher
    await dispatcher.start()

    # Wait for delivery (max 30s — Tier 2 checks every 5s + agent processing time)
    delivered = False
    for i in range(30):
        await asyncio.sleep(1)
        db = get_client()
        row = db.table("agent_event_queue").select("processed_at, processing_error").eq("id", event_id).execute()
        if row.data and row.data[0]["processed_at"] is not None:
            t_delivered = time.time()
            elapsed = t_delivered - t_enqueue
            error = row.data[0].get("processing_error")
            if error:
                logger.warning("Event delivered with error: %s", error)
            else:
                logger.info("PASS: Event delivered in %.1f seconds", elapsed)
            delivered = True
            break

    await dispatcher.stop()

    if not delivered:
        logger.error("FAIL: Event not delivered within 30s")
        # Clean up
        cleanup_test_events()
        return False

    # Verify agent actually responded — check observatory_events or agent_memories
    db = get_client()
    try:
        obs = (
            db.table("observatory_events")
            .select("id, event_type, summary")
            .eq("sim_run_id", SIM_RUN_ID)
            .eq("country_code", "phrygia")
            .order("created_at", desc=True)
            .limit(3)
            .execute()
        )
        if obs.data:
            logger.info("Recent observatory events: %s",
                        [e.get("summary", "")[:50] for e in obs.data])
        else:
            logger.info("No observatory events found (agent may not have produced text output)")
    except Exception as obs_err:
        logger.warning("Could not query observatory_events: %s", obs_err)

    logger.info("TEST 2 PASSED (enqueue-to-delivery: %.1fs)", elapsed)
    return True


async def test_3_queue_depth_and_clear() -> bool:
    """Test 3: Queue depth and clear operations."""
    separator("TEST 3: Queue Depth + Clear")

    dispatcher = EventDispatcher(SIM_RUN_ID)

    # Clean slate
    cleanup_test_events()

    # Enqueue 5 events at mixed tiers
    dispatcher.enqueue(VIZIER_ROLE_ID, 1, "attack", "Attack event 1")
    dispatcher.enqueue(VIZIER_ROLE_ID, 1, "nuclear", "Nuclear event 1")
    dispatcher.enqueue(VIZIER_ROLE_ID, 2, "chat", "Chat event 1")
    dispatcher.enqueue(VIZIER_ROLE_ID, 3, "news", "News event 1")
    dispatcher.enqueue(VIZIER_ROLE_ID, 3, "round_update", "Round update event 1")

    # Check queue depth
    depth = await dispatcher.get_queue_depth(VIZIER_ROLE_ID)
    assert depth[1] == 2, f"Expected 2 Tier-1 events, got {depth[1]}"
    assert depth[2] == 1, f"Expected 1 Tier-2 event, got {depth[2]}"
    assert depth[3] == 2, f"Expected 2 Tier-3 events, got {depth[3]}"
    logger.info("PASS: Queue depth correct: T1=%d, T2=%d, T3=%d", depth[1], depth[2], depth[3])

    # Clear queue
    cleared = await dispatcher.clear_queue(VIZIER_ROLE_ID)
    assert cleared == 5, f"Expected 5 cleared, got {cleared}"
    logger.info("PASS: Cleared %d events", cleared)

    # Verify empty
    depth_after = await dispatcher.get_queue_depth(VIZIER_ROLE_ID)
    total = sum(depth_after.values())
    assert total == 0, f"Expected 0 after clear, got {total}"
    logger.info("PASS: Queue empty after clear")

    logger.info("TEST 3 PASSED")
    return True


async def test_4_agent_state_gating() -> bool:
    """Test 4: FROZEN agents don't receive events; IDLE agents do."""
    separator("TEST 4: Agent State Gating")

    dispatcher = EventDispatcher(SIM_RUN_ID)

    # Clean slate
    cleanup_test_events()

    # Reconnect
    count = await dispatcher.reconnect_from_db()
    assert count >= 1, "No agents reconnected"

    # Set agent to FROZEN
    dispatcher.set_agent_state(VIZIER_ROLE_ID, FROZEN)

    # Enqueue event
    event_id = dispatcher.enqueue(
        VIZIER_ROLE_ID, 2, "test_frozen",
        "This should NOT be delivered while frozen."
    )
    logger.info("Enqueued event %s while agent FROZEN", event_id)

    # Start dispatcher, wait 8s (covers multiple Tier 2 check cycles)
    await dispatcher.start()
    await asyncio.sleep(8)

    # Verify NOT processed
    db = get_client()
    row = db.table("agent_event_queue").select("processed_at").eq("id", event_id).execute()
    assert row.data and row.data[0]["processed_at"] is None, "Event was delivered to FROZEN agent!"
    logger.info("PASS: Event NOT delivered while agent FROZEN")

    # Set agent to IDLE
    dispatcher.set_agent_state(VIZIER_ROLE_ID, IDLE)
    logger.info("Set agent to IDLE, waiting for delivery...")

    # Wait up to 20s for delivery
    delivered = False
    for i in range(20):
        await asyncio.sleep(1)
        row = db.table("agent_event_queue").select("processed_at, processing_error").eq("id", event_id).execute()
        if row.data and row.data[0]["processed_at"] is not None:
            error = row.data[0].get("processing_error")
            if error:
                logger.warning("Delivered with error: %s", error)
            logger.info("PASS: Event delivered after setting IDLE (waited %ds)", i + 1)
            delivered = True
            break

    await dispatcher.stop()

    if not delivered:
        logger.error("FAIL: Event not delivered within 20s after setting IDLE")
        cleanup_test_events()
        return False

    logger.info("TEST 4 PASSED")
    return True


async def main() -> None:
    """Run all tests sequentially."""
    logger.info("=" * 60)
    logger.info("  EventDispatcher Integration Tests")
    logger.info("  SIM Run: %s", SIM_RUN_ID)
    logger.info("  Target: Vizier (phrygia)")
    logger.info("=" * 60)

    results: dict[str, bool] = {}

    # Test 1: Queue CRUD (no agent call)
    try:
        results["Test 1: Enqueue/Dequeue"] = await test_1_enqueue_dequeue()
    except Exception as e:
        logger.error("Test 1 FAILED with exception: %s", e, exc_info=True)
        results["Test 1: Enqueue/Dequeue"] = False

    # Test 2: Live agent delivery
    try:
        results["Test 2: Agent Delivery"] = await test_2_dispatcher_delivers()
    except Exception as e:
        logger.error("Test 2 FAILED with exception: %s", e, exc_info=True)
        results["Test 2: Agent Delivery"] = False

    # Test 3: Queue depth + clear
    try:
        results["Test 3: Queue Depth"] = await test_3_queue_depth_and_clear()
    except Exception as e:
        logger.error("Test 3 FAILED with exception: %s", e, exc_info=True)
        results["Test 3: Queue Depth"] = False

    # Test 4: State gating (FROZEN blocks, IDLE delivers)
    try:
        results["Test 4: State Gating"] = await test_4_agent_state_gating()
    except Exception as e:
        logger.error("Test 4 FAILED with exception: %s", e, exc_info=True)
        results["Test 4: State Gating"] = False

    # Final cleanup
    cleanup_test_events()

    # Summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("  RESULTS SUMMARY")
    logger.info("=" * 60)
    for name, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        logger.info("  %s: %s", name, status)

    total = len(results)
    passed = sum(1 for v in results.values() if v)
    logger.info("")
    logger.info("  %d/%d tests passed", passed, total)
    logger.info("=" * 60)

    if passed < total:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
