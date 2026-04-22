"""Tests for async Supabase client migration.

Validates that the EventDispatcher works correctly with the async
Supabase client for queue operations while keeping enqueue() sync
for action_dispatcher compatibility.

Tests:
  1. Async client connects and reads
  2. Enqueue (sync) + dequeue (async) works
  3. Mark processed (async) works
  4. Queue depth (async) works
  5. Clear queue (async) works
  6. Full lifecycle: enqueue → dequeue → mark_processed → verify

Usage:
  cd app && python -m engine.agents.managed.test_async_db
"""

import asyncio
import logging
import sys
import os
import time

# Setup path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Test constants — use the Vizier agent in Test33 sim_run
SIM_RUN_ID = "c954b9b6-35f0-4973-a08b-f38406c524e7"
TEST_ROLE_ID = "test_async_role_" + str(int(time.time()))  # Unique per run


def separator(title: str) -> None:
    """Print a section separator."""
    logger.info("\n" + "=" * 60)
    logger.info(title)
    logger.info("=" * 60)


async def test_1_async_client_connects() -> bool:
    """Test 1: Async client connects and can read from DB."""
    separator("TEST 1: Async client connects and reads")
    try:
        from engine.services.async_db import get_async_client

        db = await get_async_client()
        assert db is not None, "Async client is None"

        # Read sim_runs table — should not raise
        result = await db.table("sim_runs").select("id").limit(1).execute()
        logger.info("  Read sim_runs: got %d rows", len(result.data or []))

        # Verify singleton — second call returns same instance
        db2 = await get_async_client()
        assert db is db2, "Async client is not a singleton"
        logger.info("  Singleton verified")

        logger.info("  PASS")
        return True
    except Exception as e:
        logger.error("  FAIL: %s", e)
        return False


async def test_2_enqueue_sync_dequeue_async() -> bool:
    """Test 2: Enqueue (sync) writes, dequeue (async) reads."""
    separator("TEST 2: Enqueue (sync) + dequeue (async)")
    try:
        from engine.agents.managed.event_dispatcher import EventDispatcher

        dispatcher = EventDispatcher(SIM_RUN_ID)

        # Enqueue — sync (uses sync client)
        event_id = dispatcher.enqueue(
            role_id=TEST_ROLE_ID,
            tier=2,
            event_type="test_async_enqueue",
            message="Testing sync enqueue for async migration",
            metadata={"test": True},
        )
        logger.info("  Enqueued event: %s", event_id)
        assert event_id != "?", "Enqueue returned '?' — insert failed"

        # Dequeue — async (uses async client)
        events = await dispatcher.dequeue(TEST_ROLE_ID, max_tier=3)
        logger.info("  Dequeued %d events for role %s", len(events), TEST_ROLE_ID)
        assert len(events) >= 1, f"Expected at least 1 event, got {len(events)}"

        # Verify the event we just enqueued is in the list
        found = any(e["id"] == event_id for e in events)
        assert found, f"Enqueued event {event_id} not found in dequeue results"
        logger.info("  Found enqueued event in dequeue results")

        # Verify event data
        our_event = next(e for e in events if e["id"] == event_id)
        assert our_event["tier"] == 2
        assert our_event["event_type"] == "test_async_enqueue"
        assert our_event["role_id"] == TEST_ROLE_ID
        logger.info("  Event data verified: tier=%d, type=%s", our_event["tier"], our_event["event_type"])

        logger.info("  PASS")
        return True
    except Exception as e:
        logger.error("  FAIL: %s", e)
        return False


async def test_3_mark_processed_async() -> bool:
    """Test 3: Mark processed (async) works."""
    separator("TEST 3: Mark processed (async)")
    try:
        from engine.agents.managed.event_dispatcher import EventDispatcher

        dispatcher = EventDispatcher(SIM_RUN_ID)

        # Enqueue a test event
        event_id = dispatcher.enqueue(
            role_id=TEST_ROLE_ID,
            tier=3,
            event_type="test_mark_processed",
            message="This event will be marked processed",
        )

        # Verify it appears in dequeue
        events_before = await dispatcher.dequeue(TEST_ROLE_ID, max_tier=3)
        found_before = any(e["id"] == event_id for e in events_before)
        assert found_before, "Event not found before marking processed"

        # Mark processed — async
        await dispatcher.mark_processed([event_id])
        logger.info("  Marked event %s as processed", event_id)

        # Verify it no longer appears in dequeue (unprocessed only)
        events_after = await dispatcher.dequeue(TEST_ROLE_ID, max_tier=3)
        found_after = any(e["id"] == event_id for e in events_after)
        assert not found_after, "Event still appears after marking processed"
        logger.info("  Event correctly filtered out after marking processed")

        logger.info("  PASS")
        return True
    except Exception as e:
        logger.error("  FAIL: %s", e)
        return False


async def test_4_queue_depth_async() -> bool:
    """Test 4: Queue depth (async) returns correct tier counts."""
    separator("TEST 4: Queue depth (async)")
    try:
        from engine.agents.managed.event_dispatcher import EventDispatcher

        dispatcher = EventDispatcher(SIM_RUN_ID)

        # First clear any existing events for our test role
        await dispatcher.clear_queue(TEST_ROLE_ID)

        # Enqueue events at different tiers
        dispatcher.enqueue(TEST_ROLE_ID, 1, "test_t1", "Tier 1 event")
        dispatcher.enqueue(TEST_ROLE_ID, 2, "test_t2a", "Tier 2 event A")
        dispatcher.enqueue(TEST_ROLE_ID, 2, "test_t2b", "Tier 2 event B")
        dispatcher.enqueue(TEST_ROLE_ID, 3, "test_t3", "Tier 3 event")

        # Check depth — async
        depth = await dispatcher.get_queue_depth(TEST_ROLE_ID)
        logger.info("  Queue depth: %s", depth)

        assert depth[1] == 1, f"Expected 1 Tier-1 event, got {depth[1]}"
        assert depth[2] == 2, f"Expected 2 Tier-2 events, got {depth[2]}"
        assert depth[3] == 1, f"Expected 1 Tier-3 event, got {depth[3]}"
        logger.info("  Tier counts verified: T1=%d, T2=%d, T3=%d", depth[1], depth[2], depth[3])

        logger.info("  PASS")
        return True
    except Exception as e:
        logger.error("  FAIL: %s", e)
        return False


async def test_5_clear_queue_async() -> bool:
    """Test 5: Clear queue (async) removes unprocessed events."""
    separator("TEST 5: Clear queue (async)")
    try:
        from engine.agents.managed.event_dispatcher import EventDispatcher

        dispatcher = EventDispatcher(SIM_RUN_ID)

        # Ensure there are events (from test 4 or add more)
        dispatcher.enqueue(TEST_ROLE_ID, 2, "test_clear", "Event to clear")

        depth_before = await dispatcher.get_queue_depth(TEST_ROLE_ID)
        total_before = sum(depth_before.values())
        logger.info("  Events before clear: %d", total_before)
        assert total_before >= 1, "Expected at least 1 event before clear"

        # Clear — async
        cleared = await dispatcher.clear_queue(TEST_ROLE_ID)
        logger.info("  Cleared %d events", cleared)
        assert cleared >= 1, f"Expected to clear at least 1 event, cleared {cleared}"

        # Verify queue is empty
        depth_after = await dispatcher.get_queue_depth(TEST_ROLE_ID)
        total_after = sum(depth_after.values())
        assert total_after == 0, f"Expected 0 events after clear, got {total_after}"
        logger.info("  Queue empty after clear: confirmed")

        logger.info("  PASS")
        return True
    except Exception as e:
        logger.error("  FAIL: %s", e)
        return False


async def test_6_full_lifecycle() -> bool:
    """Test 6: Full lifecycle — enqueue -> dequeue -> process -> verify clean."""
    separator("TEST 6: Full lifecycle")
    try:
        from engine.agents.managed.event_dispatcher import EventDispatcher

        dispatcher = EventDispatcher(SIM_RUN_ID)

        # Clean start
        await dispatcher.clear_queue(TEST_ROLE_ID)

        # Step 1: Enqueue 3 events (sync)
        ids = []
        for i, (tier, etype) in enumerate([(1, "critical_test"), (2, "urgent_test"), (3, "routine_test")]):
            eid = dispatcher.enqueue(
                TEST_ROLE_ID, tier, etype,
                f"Lifecycle test event {i+1}",
            )
            ids.append(eid)
        logger.info("  Step 1: Enqueued %d events: %s", len(ids), ids)

        # Step 2: Dequeue (async) — should get all 3, ordered by tier
        events = await dispatcher.dequeue(TEST_ROLE_ID, max_tier=3)
        assert len(events) == 3, f"Expected 3 events, got {len(events)}"
        assert events[0]["tier"] == 1, "First event should be Tier 1 (critical)"
        assert events[1]["tier"] == 2, "Second event should be Tier 2 (urgent)"
        assert events[2]["tier"] == 3, "Third event should be Tier 3 (routine)"
        logger.info("  Step 2: Dequeued %d events, ordered by tier correctly", len(events))

        # Step 3: Mark processed (async)
        await dispatcher.mark_processed(ids)
        logger.info("  Step 3: Marked all %d events as processed", len(ids))

        # Step 4: Verify queue is empty
        depth = await dispatcher.get_queue_depth(TEST_ROLE_ID)
        total = sum(depth.values())
        assert total == 0, f"Expected 0 unprocessed events, got {total}"
        logger.info("  Step 4: Queue empty after processing — verified")

        # Step 5: Verify dequeue returns nothing
        events_after = await dispatcher.dequeue(TEST_ROLE_ID, max_tier=3)
        assert len(events_after) == 0, f"Expected 0 events, got {len(events_after)}"
        logger.info("  Step 5: Dequeue returns empty — confirmed")

        logger.info("  PASS")
        return True
    except Exception as e:
        logger.error("  FAIL: %s", e)
        return False


async def test_7_simultaneous_operations() -> bool:
    """Test 7: Simultaneous async operations — no [Errno 35]."""
    separator("TEST 7: Simultaneous async operations")
    try:
        from engine.agents.managed.event_dispatcher import EventDispatcher
        from engine.services.async_db import get_async_client

        dispatcher = EventDispatcher(SIM_RUN_ID)

        # Clean start
        await dispatcher.clear_queue(TEST_ROLE_ID)

        # Enqueue several events
        for i in range(5):
            dispatcher.enqueue(TEST_ROLE_ID, 2, f"sim_test_{i}", f"Simultaneous event {i}")

        # Run multiple async operations simultaneously
        # This is the scenario that caused [Errno 35] with sync client
        results = await asyncio.gather(
            dispatcher.dequeue(TEST_ROLE_ID, max_tier=3),
            dispatcher.get_queue_depth(TEST_ROLE_ID),
            get_async_client(),  # Concurrent client access
            return_exceptions=True,
        )

        # Check no exceptions
        for i, r in enumerate(results):
            if isinstance(r, Exception):
                raise r
            logger.info("  Concurrent operation %d: OK", i + 1)

        events = results[0]
        depth = results[1]
        logger.info("  Dequeued %d events, depth: %s", len(events), depth)

        # Clean up
        await dispatcher.clear_queue(TEST_ROLE_ID)

        logger.info("  PASS — no [Errno 35] or resource exhaustion")
        return True
    except Exception as e:
        logger.error("  FAIL: %s", e)
        return False


async def cleanup_test_data() -> None:
    """Remove all test data created during tests."""
    try:
        from engine.services.async_db import get_async_client
        db = await get_async_client()

        # Delete test events
        result = await (
            db.table("agent_event_queue")
            .delete()
            .eq("sim_run_id", SIM_RUN_ID)
            .eq("role_id", TEST_ROLE_ID)
            .execute()
        )
        logger.info("[cleanup] Removed %d test events", len(result.data or []))
    except Exception as e:
        logger.warning("[cleanup] Failed: %s", e)


async def main() -> None:
    """Run all async DB migration tests."""
    separator("ASYNC SUPABASE CLIENT MIGRATION TESTS")
    logger.info("SIM_RUN_ID: %s", SIM_RUN_ID)
    logger.info("TEST_ROLE_ID: %s", TEST_ROLE_ID)

    results: dict[str, bool] = {}

    # Test 1: Async client connects
    try:
        results["1: Async client connects"] = await test_1_async_client_connects()
    except Exception as e:
        logger.error("Test 1 crashed: %s", e)
        results["1: Async client connects"] = False

    # Test 2: Enqueue sync + dequeue async
    try:
        results["2: Enqueue sync + dequeue async"] = await test_2_enqueue_sync_dequeue_async()
    except Exception as e:
        logger.error("Test 2 crashed: %s", e)
        results["2: Enqueue sync + dequeue async"] = False

    # Test 3: Mark processed async
    try:
        results["3: Mark processed async"] = await test_3_mark_processed_async()
    except Exception as e:
        logger.error("Test 3 crashed: %s", e)
        results["3: Mark processed async"] = False

    # Test 4: Queue depth async
    try:
        results["4: Queue depth async"] = await test_4_queue_depth_async()
    except Exception as e:
        logger.error("Test 4 crashed: %s", e)
        results["4: Queue depth async"] = False

    # Test 5: Clear queue async
    try:
        results["5: Clear queue async"] = await test_5_clear_queue_async()
    except Exception as e:
        logger.error("Test 5 crashed: %s", e)
        results["5: Clear queue async"] = False

    # Test 6: Full lifecycle
    try:
        results["6: Full lifecycle"] = await test_6_full_lifecycle()
    except Exception as e:
        logger.error("Test 6 crashed: %s", e)
        results["6: Full lifecycle"] = False

    # Test 7: Simultaneous operations
    try:
        results["7: Simultaneous operations"] = await test_7_simultaneous_operations()
    except Exception as e:
        logger.error("Test 7 crashed: %s", e)
        results["7: Simultaneous operations"] = False

    # Cleanup test data
    await cleanup_test_data()

    # Summary
    separator("TEST RESULTS")
    passed = 0
    failed = 0
    for name, result in results.items():
        status = "PASS" if result else "FAIL"
        logger.info("  %s: %s", name, status)
        if result:
            passed += 1
        else:
            failed += 1

    logger.info("\n  Total: %d passed, %d failed out of %d", passed, failed, len(results))

    if failed > 0:
        logger.error("\n  SOME TESTS FAILED")
        sys.exit(1)
    else:
        logger.info("\n  ALL TESTS PASSED")


if __name__ == "__main__":
    asyncio.run(main())
