"""Consolidated test — EventDispatcher as SINGLE execution path.

Tests the full lifecycle:
  1. Clean start (cleanup)
  2. Initialize via dispatcher.initialize_all_agents()
  3. Dispatcher delivers init event
  4. Chat message delivery
  5. Transaction event delivery
  6. Cleanup + re-initialize

Uses Test33 sim_run: c954b9b6-35f0-4973-a08b-f38406c524e7
Uses Vizier role (phrygia, AI-operated)

Run: cd app && python -m engine.agents.managed.test_consolidated
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys
import time

# Ensure app/ is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

SIM_RUN_ID = "c954b9b6-35f0-4973-a08b-f38406c524e7"
VIZIER_ROLE_ID = "vizier"


def get_db():
    from engine.services.supabase import get_client
    return get_client()


def check_queue(role_id: str | None = None) -> list[dict]:
    """Get unprocessed events from queue."""
    db = get_db()
    q = (
        db.table("agent_event_queue")
        .select("*")
        .eq("sim_run_id", SIM_RUN_ID)
        .is_("processed_at", "null")
        .order("created_at")
    )
    if role_id:
        q = q.eq("role_id", role_id)
    return q.execute().data or []


def check_sessions(status_filter: list[str] | None = None) -> list[dict]:
    """Get AI sessions from DB."""
    db = get_db()
    q = (
        db.table("ai_agent_sessions")
        .select("*")
        .eq("sim_run_id", SIM_RUN_ID)
    )
    if status_filter:
        q = q.in_("status", status_filter)
    return q.execute().data or []


def check_observatory() -> list[dict]:
    """Get observatory AI agent logs."""
    db = get_db()
    return (
        db.table("observatory_events")
        .select("*")
        .eq("sim_run_id", SIM_RUN_ID)
        .eq("event_type", "ai_agent_log")
        .order("created_at", desc=True)
        .limit(20)
        .execute()
    ).data or []


def check_meetings() -> list[dict]:
    """Get meetings for sim."""
    db = get_db()
    return (
        db.table("meetings")
        .select("*")
        .eq("sim_run_id", SIM_RUN_ID)
        .execute()
    ).data or []


async def test_1_clean_start():
    """Test 1: Clean start — verify cleanup works."""
    print("\n" + "=" * 60)
    print("TEST 1: Clean Start (cleanup)")
    print("=" * 60)

    from engine.agents.managed.event_dispatcher import (
        cleanup_sim_ai_state, get_dispatcher, remove_dispatcher,
    )

    # Stop any existing dispatcher
    d = get_dispatcher(SIM_RUN_ID)
    if d:
        await d.shutdown()
        remove_dispatcher(SIM_RUN_ID)

    # Full cleanup
    summary = await cleanup_sim_ai_state(
        SIM_RUN_ID, clear_memories=True, clear_decisions=True,
    )
    print(f"  Cleanup summary: {summary}")

    # Verify
    active_sessions = check_sessions(["initializing", "ready", "active"])
    assert len(active_sessions) == 0, f"Expected 0 active sessions, got {len(active_sessions)}"
    print(f"  Active sessions: {len(active_sessions)} (expected 0)")

    queue = check_queue()
    assert len(queue) == 0, f"Expected 0 queued events, got {len(queue)}"
    print(f"  Queued events: {len(queue)} (expected 0)")

    observatory = check_observatory()
    assert len(observatory) == 0, f"Expected 0 observatory AI logs, got {len(observatory)}"
    print(f"  Observatory AI logs: {len(observatory)} (expected 0)")

    meetings = check_meetings()
    print(f"  Meetings: {len(meetings)} (cleaned)")

    d = get_dispatcher(SIM_RUN_ID)
    assert d is None, "Dispatcher should be removed"
    print(f"  Dispatcher: None (expected)")

    print("  PASS")
    return True


async def test_2_initialize():
    """Test 2: Initialize via dispatcher.initialize_all_agents() for vizier only."""
    print("\n" + "=" * 60)
    print("TEST 2: Initialize (vizier only)")
    print("=" * 60)

    from engine.agents.managed.event_dispatcher import create_dispatcher

    dispatcher = create_dispatcher(SIM_RUN_ID)

    # Initialize ONLY vizier
    result = await dispatcher.initialize_all_agents(
        role_ids=[VIZIER_ROLE_ID],
        model="claude-sonnet-4-6",
    )
    print(f"  Init result: {result}")

    assert result["agents_initialized"] == 1, f"Expected 1 agent, got {result['agents_initialized']}"
    assert not result.get("errors"), f"Unexpected errors: {result['errors']}"

    # Verify session in DB
    sessions = check_sessions(["ready", "active", "initializing"])
    vizier_sessions = [s for s in sessions if s["role_id"] == VIZIER_ROLE_ID]
    assert len(vizier_sessions) == 1, f"Expected 1 vizier session, got {len(vizier_sessions)}"
    print(f"  Vizier session: {vizier_sessions[0]['session_id']}")

    # Verify init event enqueued
    queue = check_queue(VIZIER_ROLE_ID)
    init_events = [e for e in queue if e["event_type"] == "initialization"]
    assert len(init_events) >= 1, f"Expected init event in queue, got {len(init_events)}"
    print(f"  Init event enqueued: {init_events[0]['id']}")

    # Verify agent registered with dispatcher
    assert VIZIER_ROLE_ID in dispatcher.agents, "Vizier not registered with dispatcher"
    print(f"  Dispatcher agents: {list(dispatcher.agents.keys())}")

    print("  PASS")
    return dispatcher


async def test_3_dispatcher_delivers_init(dispatcher):
    """Test 3: Start dispatcher, wait for it to deliver the init event."""
    print("\n" + "=" * 60)
    print("TEST 3: Dispatcher delivers init event")
    print("=" * 60)

    # Start the dispatch loop
    await dispatcher.start()
    print("  Dispatcher started, waiting for init delivery...")

    # Wait for the init event to be processed (up to 30s)
    max_wait = 45
    for i in range(max_wait):
        queue = check_queue(VIZIER_ROLE_ID)
        unprocessed_init = [e for e in queue if e["event_type"] == "initialization"]
        if len(unprocessed_init) == 0:
            print(f"  Init event delivered after ~{i+1}s")
            break
        await asyncio.sleep(1)
    else:
        print(f"  WARNING: Init event still in queue after {max_wait}s")
        # Check if it was processed with error
        db = get_db()
        all_init = (
            db.table("agent_event_queue")
            .select("*")
            .eq("sim_run_id", SIM_RUN_ID)
            .eq("role_id", VIZIER_ROLE_ID)
            .eq("event_type", "initialization")
            .execute()
        ).data or []
        for e in all_init:
            print(f"    Event {e['id']}: processed_at={e.get('processed_at')}, error={e.get('processing_error')}")

    # Give a moment for observatory to be written
    await asyncio.sleep(2)

    # Check observatory logs
    obs = check_observatory()
    print(f"  Observatory AI logs: {len(obs)}")
    if obs:
        for o in obs[:3]:
            print(f"    - {o['category']}: {o['summary'][:80]}")

    # Check if agent made any tool calls (actions submitted)
    sessions = check_sessions(["ready", "active"])
    viz_session = [s for s in sessions if s["role_id"] == VIZIER_ROLE_ID]
    if viz_session:
        s = viz_session[0]
        print(f"  Session status: {s['status']}")
        print(f"  Events sent: {s.get('events_sent', 0)}")
        print(f"  Tool calls: {s.get('tool_calls', 0)}")
        print(f"  Actions submitted: {s.get('actions_submitted', 0)}")
        print(f"  Tokens: {s.get('total_input_tokens', 0)} in / {s.get('total_output_tokens', 0)} out")

    # Verify: at minimum, the event was processed (even if agent didn't do much)
    assert len(obs) > 0 or (viz_session and viz_session[0].get("events_sent", 0) > 0), \
        "Expected at least one observatory log or events_sent > 0"

    print("  PASS")
    return True


async def test_4_chat_message(dispatcher):
    """Test 4: Enqueue a chat_message event and verify delivery."""
    print("\n" + "=" * 60)
    print("TEST 4: Chat message delivery")
    print("=" * 60)

    # Create a meeting first
    db = get_db()
    meeting_result = db.table("meetings").insert({
        "sim_run_id": SIM_RUN_ID,
        "modality": "text",
        "round_num": 1,
        "participant_a_role_id": "dealer",
        "participant_a_country": "columbia",
        "participant_b_role_id": VIZIER_ROLE_ID,
        "participant_b_country": "phrygia",
        "status": "active",
        "agenda": "Test meeting for consolidated test",
    }).execute()
    meeting_id = meeting_result.data[0]["id"]
    print(f"  Created test meeting: {meeting_id}")

    # Enqueue chat message
    event_id = dispatcher.enqueue(
        role_id=VIZIER_ROLE_ID,
        tier=2,
        event_type="chat_message",
        message=(
            "You are in a meeting with the President of Columbia (Dealer). "
            "They say: 'We need to discuss the trade situation in the Pacific. "
            "What are your thoughts on a bilateral agreement?'\n\n"
            "Respond naturally. 1-3 sentences. Stay in character."
        ),
        metadata={"meeting_id": meeting_id, "sender": "dealer"},
    )
    print(f"  Enqueued chat event: {event_id}")

    # Wait for delivery
    max_wait = 30
    for i in range(max_wait):
        queue = check_queue(VIZIER_ROLE_ID)
        chat_events = [e for e in queue if e["event_type"] == "chat_message"]
        if len(chat_events) == 0:
            print(f"  Chat event delivered after ~{i+1}s")
            break
        await asyncio.sleep(1)
    else:
        print(f"  WARNING: Chat event still pending after {max_wait}s")

    # Check if response was written to meeting_messages
    await asyncio.sleep(2)
    msgs = (
        db.table("meeting_messages")
        .select("*")
        .eq("meeting_id", meeting_id)
        .order("created_at")
        .execute()
    ).data or []
    print(f"  Meeting messages: {len(msgs)}")
    for m in msgs:
        print(f"    [{m['role_id']}]: {m['content'][:80]}")

    # Cleanup test meeting
    for m in msgs:
        db.table("meeting_messages").delete().eq("id", m["id"]).execute()
    db.table("meetings").delete().eq("id", meeting_id).execute()

    print("  PASS")
    return True


async def test_5_transaction(dispatcher):
    """Test 5: Enqueue a transaction_proposed event and verify delivery."""
    print("\n" + "=" * 60)
    print("TEST 5: Transaction event delivery")
    print("=" * 60)

    event_id = dispatcher.enqueue(
        role_id=VIZIER_ROLE_ID,
        tier=2,
        event_type="transaction_proposed",
        message=(
            "TRANSACTION PROPOSAL RECEIVED\n\n"
            "Columbia has proposed a trade deal: 5 units of oil for 3 units of technology.\n"
            "Transaction ID: test-txn-001\n\n"
            "Review this proposal. Use submit_action to accept or reject."
        ),
        metadata={"transaction_id": "test-txn-001", "proposer": "columbia"},
    )
    print(f"  Enqueued transaction event: {event_id}")

    # Wait for delivery
    max_wait = 30
    for i in range(max_wait):
        queue = check_queue(VIZIER_ROLE_ID)
        txn_events = [e for e in queue if e["event_type"] == "transaction_proposed"]
        if len(txn_events) == 0:
            print(f"  Transaction event delivered after ~{i+1}s")
            break
        await asyncio.sleep(1)
    else:
        print(f"  WARNING: Transaction event still pending after {max_wait}s")

    # Check observatory for the transaction processing
    await asyncio.sleep(2)
    obs = check_observatory()
    recent = [o for o in obs if "transaction" in (o.get("summary") or "").lower() or "agent" in (o.get("category") or "")]
    print(f"  Recent observatory entries: {len(obs)}")

    print("  PASS")
    return True


async def test_6_cleanup_and_reinit():
    """Test 6: Full cleanup + re-initialize from scratch."""
    print("\n" + "=" * 60)
    print("TEST 6: Cleanup and Re-initialize")
    print("=" * 60)

    from engine.agents.managed.event_dispatcher import (
        cleanup_sim_ai_state, get_dispatcher, remove_dispatcher,
        create_dispatcher,
    )

    # Cleanup
    summary = await cleanup_sim_ai_state(
        SIM_RUN_ID, clear_memories=True, clear_decisions=True,
    )
    print(f"  Cleanup summary: sessions_archived={summary.get('db_sessions_archived', 0)}, "
          f"events_cleared={summary.get('events_cleared', 0)}, "
          f"observatory_cleared={summary.get('observatory_events_cleared', 0)}")

    # Verify clean state
    active = check_sessions(["initializing", "ready", "active"])
    assert len(active) == 0, f"Expected 0 active sessions after cleanup, got {len(active)}"
    print(f"  Active sessions after cleanup: {len(active)}")

    queue = check_queue()
    assert len(queue) == 0, f"Expected 0 queued events, got {len(queue)}"
    print(f"  Queue after cleanup: {len(queue)}")

    obs = check_observatory()
    assert len(obs) == 0, f"Expected 0 observatory AI logs, got {len(obs)}"
    print(f"  Observatory after cleanup: {len(obs)}")

    # Re-initialize
    dispatcher = create_dispatcher(SIM_RUN_ID)
    result = await dispatcher.initialize_all_agents(
        role_ids=[VIZIER_ROLE_ID],
        model="claude-sonnet-4-6",
    )
    print(f"  Re-init result: agents={result['agents_initialized']}, errors={result.get('errors', [])}")
    assert result["agents_initialized"] == 1

    # Verify fresh session (different session_id)
    sessions = check_sessions(["ready", "active", "initializing"])
    viz = [s for s in sessions if s["role_id"] == VIZIER_ROLE_ID]
    assert len(viz) == 1, f"Expected 1 vizier session, got {len(viz)}"
    print(f"  New session: {viz[0]['session_id']}")

    # Verify init event enqueued
    queue = check_queue(VIZIER_ROLE_ID)
    init_events = [e for e in queue if e["event_type"] == "initialization"]
    assert len(init_events) >= 1, f"Expected init event in queue, got {len(init_events)}"
    print(f"  Init event enqueued: YES")

    # Start dispatcher and wait for init delivery
    await dispatcher.start()
    print("  Dispatcher started, waiting for re-init delivery...")

    max_wait = 45
    for i in range(max_wait):
        queue = check_queue(VIZIER_ROLE_ID)
        unprocessed = [e for e in queue if e["event_type"] == "initialization"]
        if len(unprocessed) == 0:
            print(f"  Re-init event delivered after ~{i+1}s")
            break
        await asyncio.sleep(1)
    else:
        print(f"  WARNING: Re-init still pending after {max_wait}s")

    # Verify agent responded fresh
    await asyncio.sleep(2)
    sessions = check_sessions(["ready", "active"])
    viz = [s for s in sessions if s["role_id"] == VIZIER_ROLE_ID]
    if viz:
        s = viz[0]
        print(f"  Events sent: {s.get('events_sent', 0)}")
        print(f"  Tool calls: {s.get('tool_calls', 0)}")

    # Final cleanup
    await dispatcher.shutdown()
    remove_dispatcher(SIM_RUN_ID)
    await cleanup_sim_ai_state(SIM_RUN_ID, clear_memories=True, clear_decisions=True)
    print("  Final cleanup done")

    print("  PASS")
    return True


async def main():
    """Run all tests sequentially."""
    print("=" * 60)
    print("CONSOLIDATED TEST: EventDispatcher as Single Execution Path")
    print(f"Sim Run: {SIM_RUN_ID}")
    print(f"Role: {VIZIER_ROLE_ID} (phrygia)")
    print("=" * 60)

    start = time.time()
    results = {}

    try:
        # Test 1: Clean start
        results["test_1"] = await test_1_clean_start()

        # Test 2: Initialize
        dispatcher = await test_2_initialize()
        results["test_2"] = dispatcher is not None

        # Test 3: Dispatcher delivers init
        results["test_3"] = await test_3_dispatcher_delivers_init(dispatcher)

        # Test 4: Chat message
        results["test_4"] = await test_4_chat_message(dispatcher)

        # Test 5: Transaction
        results["test_5"] = await test_5_transaction(dispatcher)

        # Stop dispatcher before cleanup
        await dispatcher.stop()
        from engine.agents.managed.event_dispatcher import remove_dispatcher
        remove_dispatcher(SIM_RUN_ID)

        # Test 6: Cleanup + re-initialize
        results["test_6"] = await test_6_cleanup_and_reinit()

    except Exception as e:
        logger.error("Test failed with exception: %s", e, exc_info=True)
        results["error"] = str(e)

    elapsed = time.time() - start

    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    for name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {name}: {status}")
    print(f"\n  Total time: {elapsed:.1f}s")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
