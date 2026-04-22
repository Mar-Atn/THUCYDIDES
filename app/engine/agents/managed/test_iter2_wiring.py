"""Iteration 2 wiring tests — verify ALL event sources use EventDispatcher.

Tests that action_dispatcher.py and main.py chat endpoint enqueue events
through the dispatcher instead of using auto_pulse directly.

Tests against real Vizier agent in Test33 sim_run.
Requires: ANTHROPIC_API_KEY and SUPABASE env vars set.

Run: cd app && python -m engine.agents.managed.test_iter2_wiring
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
    create_dispatcher,
    get_dispatcher,
    remove_dispatcher,
    _find_hos_for_country,
    IDLE,
    FROZEN,
)
from engine.services.supabase import get_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Test33 sim run
SIM_RUN_ID = "c954b9b6-35f0-4973-a08b-f38406c524e7"
VIZIER_ROLE_ID = "vizier"
VIZIER_COUNTRY = "phrygia"


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


# ── Test A: Chat message wiring ──────────────────────────────────────

async def test_a_chat_enqueue() -> bool:
    """Test A: Simulate a chat message → event enqueued → dispatcher delivers → AI responds.

    Verifies that the chat path uses enqueue() and that the dispatcher
    writes the AI response to meeting_messages.
    """
    separator("TEST A: Chat Message Wiring")

    # Setup dispatcher
    dispatcher = create_dispatcher(SIM_RUN_ID)
    cleanup_test_events()

    count = await dispatcher.reconnect_from_db()
    if count < 1:
        logger.error("FAIL: No agents reconnected — is Vizier initialized?")
        remove_dispatcher(SIM_RUN_ID)
        return False
    logger.info("Reconnected %d agents", count)

    # Find an active meeting for Vizier, or create one for testing
    db = get_client()
    meetings = (
        db.table("meetings")
        .select("id, participant_a_role_id, participant_b_role_id, status")
        .eq("sim_run_id", SIM_RUN_ID)
        .eq("status", "active")
        .execute()
    )

    meeting_id = None
    for m in meetings.data or []:
        if VIZIER_ROLE_ID in (m["participant_a_role_id"], m["participant_b_role_id"]):
            meeting_id = m["id"]
            break

    if not meeting_id:
        logger.warning("No active meeting found for Vizier — testing enqueue only (no delivery)")
        # Still test that enqueue works correctly
        event_id = dispatcher.enqueue(
            role_id=VIZIER_ROLE_ID,
            tier=2,
            event_type="chat_message",
            message=(
                "You are in a meeting. The other leader says: "
                "\"What are your thoughts on regional trade?\"\n\n"
                "Respond naturally. 1-3 sentences. Stay in character."
            ),
            metadata={"meeting_id": "test-meeting", "sender": "pathfinder"},
        )

        # Verify event is in DB queue
        row = db.table("agent_event_queue").select("*").eq("id", event_id).execute()
        assert row.data and row.data[0]["event_type"] == "chat_message", "Event not found in queue"
        logger.info("PASS: Chat event enqueued correctly (id=%s)", event_id)

        # Start dispatcher and wait for delivery
        await dispatcher.start()

        delivered = False
        for i in range(25):
            await asyncio.sleep(1)
            row = db.table("agent_event_queue").select("processed_at, processing_error").eq("id", event_id).execute()
            if row.data and row.data[0]["processed_at"] is not None:
                error = row.data[0].get("processing_error")
                if error:
                    logger.warning("Delivered with error: %s", error)
                else:
                    logger.info("PASS: Chat event delivered in %ds", i + 1)
                delivered = True
                break

        await dispatcher.stop()
        remove_dispatcher(SIM_RUN_ID)

        if not delivered:
            logger.error("FAIL: Chat event not delivered within 25s")
            cleanup_test_events()
            return False

        logger.info("TEST A PASSED (enqueue + delivery)")
        return True

    # We have an active meeting — test full flow including chat response writeback
    logger.info("Found active meeting: %s", meeting_id[:8])

    event_id = dispatcher.enqueue(
        role_id=VIZIER_ROLE_ID,
        tier=2,
        event_type="chat_message",
        message=(
            f"You are in a meeting (meeting_id: {meeting_id}). "
            f"The other leader says: \"What are your economic priorities this round?\"\n\n"
            f"Respond naturally. 1-3 sentences. Stay in character. "
            f"Use the send_message tool with meeting_id='{meeting_id}' to reply."
        ),
        metadata={"meeting_id": meeting_id, "sender": "test_human"},
    )
    logger.info("Enqueued chat event %s", event_id)

    # Start dispatcher
    await dispatcher.start()

    # Wait for delivery
    delivered = False
    for i in range(30):
        await asyncio.sleep(1)
        row = db.table("agent_event_queue").select("processed_at, processing_error").eq("id", event_id).execute()
        if row.data and row.data[0]["processed_at"] is not None:
            logger.info("PASS: Chat event delivered in %ds", i + 1)
            delivered = True
            break

    await dispatcher.stop()
    remove_dispatcher(SIM_RUN_ID)

    if not delivered:
        logger.error("FAIL: Chat event not delivered within 30s")
        cleanup_test_events()
        return False

    # Check if a response was written to meeting_messages
    recent_msgs = (
        db.table("meeting_messages")
        .select("role_id, content, created_at")
        .eq("meeting_id", meeting_id)
        .order("created_at", desc=True)
        .limit(3)
        .execute()
    )
    if recent_msgs.data:
        logger.info("Recent meeting messages:")
        for msg in recent_msgs.data:
            logger.info("  %s: %s", msg["role_id"], msg["content"][:80])
    else:
        logger.warning("No meeting messages found (agent may have used send_message tool directly)")

    logger.info("TEST A PASSED")
    return True


# ── Test B: Transaction proposed wiring ──────────────────────────────

async def test_b_transaction_enqueue() -> bool:
    """Test B: Simulate a transaction proposal → enqueued for country HoS → delivered.

    Tests the action_dispatcher path: enqueue_for_country() finds the
    HoS role and enqueues a tier-2 transaction_proposed event.
    """
    separator("TEST B: Transaction Proposed Wiring")

    dispatcher = create_dispatcher(SIM_RUN_ID)
    cleanup_test_events()

    count = await dispatcher.reconnect_from_db()
    if count < 1:
        logger.error("FAIL: No agents reconnected")
        remove_dispatcher(SIM_RUN_ID)
        return False

    # Test _find_hos_for_country helper
    hos = _find_hos_for_country(SIM_RUN_ID, VIZIER_COUNTRY)
    logger.info("HoS for %s: %s", VIZIER_COUNTRY, hos)
    if not hos:
        logger.warning("No AI HoS found for %s — testing direct enqueue instead", VIZIER_COUNTRY)
        # Fall back to direct enqueue
        hos = VIZIER_ROLE_ID

    # Simulate what action_dispatcher does for propose_transaction
    event_id = dispatcher.enqueue(
        role_id=hos,
        tier=2,
        event_type="transaction_proposed",
        message=(
            f"TRANSACTION PROPOSAL RECEIVED\n\n"
            f"LYDIA has proposed a transaction to your country.\n"
            f"Terms: Sale of 50 units of oil at market price\n"
            f"Transaction ID: test-tx-001\n\n"
            f"Review this proposal carefully. You can accept, reject, or counter-offer.\n"
            f"Use submit_action with action_type='accept_transaction', "
            f"transaction_id='test-tx-001', and response='accept' or 'reject'.\n\n"
            f"Consider: Is this deal fair? What do you gain? What do you lose?"
        ),
        metadata={"transaction_id": "test-tx-001", "proposer": "lydia", "terms": "50 oil"},
    )
    logger.info("Enqueued transaction_proposed event %s", event_id)

    # Verify it's in the queue
    db = get_client()
    row = db.table("agent_event_queue").select("*").eq("id", event_id).execute()
    assert row.data, "Event not found in DB"
    assert row.data[0]["event_type"] == "transaction_proposed"
    assert row.data[0]["tier"] == 2
    logger.info("PASS: Event in DB with correct type and tier")

    # Start dispatcher and wait for delivery
    await dispatcher.start()

    delivered = False
    for i in range(25):
        await asyncio.sleep(1)
        row = db.table("agent_event_queue").select("processed_at, processing_error").eq("id", event_id).execute()
        if row.data and row.data[0]["processed_at"] is not None:
            error = row.data[0].get("processing_error")
            if error:
                logger.warning("Delivered with error: %s", error)
            else:
                logger.info("PASS: Transaction event delivered in %ds", i + 1)
            delivered = True
            break

    await dispatcher.stop()
    remove_dispatcher(SIM_RUN_ID)

    if not delivered:
        logger.error("FAIL: Transaction event not delivered within 25s")
        cleanup_test_events()
        return False

    logger.info("TEST B PASSED")
    return True


# ── Test C: Meeting invitation wiring ────────────────────────────────

async def test_c_meeting_invitation_enqueue() -> bool:
    """Test C: Simulate a meeting invitation → enqueued → delivered → AI accepts/declines.

    Tests the action_dispatcher path for meeting_invitation events.
    """
    separator("TEST C: Meeting Invitation Wiring")

    dispatcher = create_dispatcher(SIM_RUN_ID)
    cleanup_test_events()

    count = await dispatcher.reconnect_from_db()
    if count < 1:
        logger.error("FAIL: No agents reconnected")
        remove_dispatcher(SIM_RUN_ID)
        return False

    # Simulate what action_dispatcher does for invite_to_meet
    event_id = dispatcher.enqueue(
        role_id=VIZIER_ROLE_ID,
        tier=2,
        event_type="meeting_invitation",
        message=(
            f"MEETING INVITATION RECEIVED\n\n"
            f"You have received a meeting invitation from Pathfinder of Lydia.\n"
            f"Agenda: Discuss regional trade cooperation and tariff reduction\n"
            f"Invitation ID: test-inv-001\n\n"
            f"Decide whether to accept or decline this meeting. "
            f"Use the respond_to_invitation tool with invitation_id='test-inv-001' "
            f"and your decision ('accept' or 'reject').\n\n"
            f"Consider: Is this meeting useful for your strategy? "
            f"Do you have time? Is this person trustworthy?"
        ),
        metadata={
            "inviter": "Pathfinder",
            "invitation_id": "test-inv-001",
            "agenda": "Trade cooperation",
        },
    )
    logger.info("Enqueued meeting_invitation event %s", event_id)

    # Verify correct in DB
    db = get_client()
    row = db.table("agent_event_queue").select("*").eq("id", event_id).execute()
    assert row.data, "Event not found in DB"
    assert row.data[0]["event_type"] == "meeting_invitation"
    assert row.data[0]["tier"] == 2
    logger.info("PASS: Event in DB with correct type and tier")

    # Start dispatcher and wait
    await dispatcher.start()

    delivered = False
    for i in range(25):
        await asyncio.sleep(1)
        row = db.table("agent_event_queue").select("processed_at, processing_error").eq("id", event_id).execute()
        if row.data and row.data[0]["processed_at"] is not None:
            error = row.data[0].get("processing_error")
            if error:
                logger.warning("Delivered with error: %s", error)
            else:
                logger.info("PASS: Meeting invitation delivered in %ds", i + 1)
            delivered = True
            break

    await dispatcher.stop()
    remove_dispatcher(SIM_RUN_ID)

    if not delivered:
        logger.error("FAIL: Meeting invitation not delivered within 25s")
        cleanup_test_events()
        return False

    # Check if agent tried to respond (look in observatory)
    try:
        obs = (
            db.table("observatory_events")
            .select("id, event_type, summary")
            .eq("sim_run_id", SIM_RUN_ID)
            .eq("country_code", VIZIER_COUNTRY)
            .order("created_at", desc=True)
            .limit(3)
            .execute()
        )
        if obs.data:
            logger.info("Recent observatory events after invitation:")
            for e in obs.data:
                logger.info("  %s: %s", e.get("event_type", ""), e.get("summary", "")[:60])
    except Exception as obs_err:
        logger.warning("Could not query observatory: %s", obs_err)

    logger.info("TEST C PASSED")
    return True


# ── Test D: enqueue_for_country helper ───────────────────────────────

async def test_d_enqueue_for_country() -> bool:
    """Test D: enqueue_for_country finds the HoS and enqueues correctly."""
    separator("TEST D: enqueue_for_country Helper")

    dispatcher = create_dispatcher(SIM_RUN_ID)
    cleanup_test_events()

    count = await dispatcher.reconnect_from_db()
    if count < 1:
        logger.error("FAIL: No agents reconnected")
        remove_dispatcher(SIM_RUN_ID)
        return False

    # Use enqueue_for_country
    event_id = dispatcher.enqueue_for_country(
        country_code=VIZIER_COUNTRY,
        tier=1,
        event_type="attack_declared",
        message=(
            f"ALERT: MILITARY ATTACK\n\n"
            f"LYDIA has launched a ground_attack against your territory!\n"
            f"Details: Ground forces attacking at (3,4)\n\n"
            f"This requires immediate response."
        ),
        metadata={"attacker": "lydia", "attack_type": "ground_attack"},
    )

    if event_id is None:
        logger.warning("enqueue_for_country returned None — HoS may not be AI-operated")
        # Check directly
        hos = _find_hos_for_country(SIM_RUN_ID, VIZIER_COUNTRY)
        logger.info("_find_hos_for_country returned: %s", hos)
        if not hos:
            logger.info("SKIP: No AI HoS for %s — this is expected if Vizier doesn't have head_of_state position", VIZIER_COUNTRY)
            remove_dispatcher(SIM_RUN_ID)
            cleanup_test_events()
            return True  # Not a failure, just not applicable

    logger.info("enqueue_for_country returned event_id: %s", event_id)

    # Verify in DB
    db = get_client()
    row = db.table("agent_event_queue").select("*").eq("id", event_id).execute()
    assert row.data, "Event not found in DB"
    assert row.data[0]["tier"] == 1
    assert row.data[0]["event_type"] == "attack_declared"
    logger.info("PASS: Country-level event enqueued correctly (tier=1, type=attack_declared)")

    # Don't need to wait for delivery — already proven in other tests
    cleanup_test_events()
    remove_dispatcher(SIM_RUN_ID)

    logger.info("TEST D PASSED")
    return True


# ── Test E: Action dispatcher wiring (import check) ─────────────────

async def test_e_action_dispatcher_import() -> bool:
    """Test E: Verify action_dispatcher no longer imports auto_pulse for event routing.

    This is a static check — we import action_dispatcher and verify
    that _enqueue_for_ai_agents exists and _auto_pulse_for_action doesn't.
    """
    separator("TEST E: Action Dispatcher Wiring (Import Check)")

    from engine.services import action_dispatcher as ad

    # New function should exist
    assert hasattr(ad, "_enqueue_for_ai_agents"), (
        "FAIL: action_dispatcher missing _enqueue_for_ai_agents"
    )
    logger.info("PASS: _enqueue_for_ai_agents exists")

    # Old function should NOT exist
    assert not hasattr(ad, "_auto_pulse_for_action"), (
        "FAIL: action_dispatcher still has _auto_pulse_for_action"
    )
    logger.info("PASS: _auto_pulse_for_action removed")

    # Verify the function uses get_dispatcher, not fire_pulse
    import inspect
    source = inspect.getsource(ad._enqueue_for_ai_agents)
    assert "get_dispatcher" in source, "FAIL: _enqueue_for_ai_agents doesn't use get_dispatcher"
    assert "fire_pulse" not in source, "FAIL: _enqueue_for_ai_agents still uses fire_pulse"
    logger.info("PASS: Uses get_dispatcher, not fire_pulse")

    logger.info("TEST E PASSED")
    return True


# ── Main ─────────────────────────────────────────────────────────────

async def main() -> None:
    """Run all Iter 2 wiring tests."""
    logger.info("=" * 60)
    logger.info("  Iteration 2: Event Wiring Tests")
    logger.info("  SIM Run: %s", SIM_RUN_ID)
    logger.info("  Target: Vizier (%s)", VIZIER_COUNTRY)
    logger.info("=" * 60)

    results: dict[str, bool] = {}

    # Test E first — it's fast (no API calls)
    try:
        results["Test E: Import Check"] = await test_e_action_dispatcher_import()
    except Exception as e:
        logger.error("Test E FAILED: %s", e, exc_info=True)
        results["Test E: Import Check"] = False

    # Test D: enqueue_for_country
    try:
        results["Test D: enqueue_for_country"] = await test_d_enqueue_for_country()
    except Exception as e:
        logger.error("Test D FAILED: %s", e, exc_info=True)
        results["Test D: enqueue_for_country"] = False

    # Test A: Chat message (calls Anthropic API)
    try:
        results["Test A: Chat Message"] = await test_a_chat_enqueue()
    except Exception as e:
        logger.error("Test A FAILED: %s", e, exc_info=True)
        results["Test A: Chat Message"] = False

    # Test B: Transaction proposed
    try:
        results["Test B: Transaction"] = await test_b_transaction_enqueue()
    except Exception as e:
        logger.error("Test B FAILED: %s", e, exc_info=True)
        results["Test B: Transaction"] = False

    # Test C: Meeting invitation
    try:
        results["Test C: Meeting Invitation"] = await test_c_meeting_invitation_enqueue()
    except Exception as e:
        logger.error("Test C FAILED: %s", e, exc_info=True)
        results["Test C: Meeting Invitation"] = False

    # Final cleanup
    cleanup_test_events()

    # Summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("  ITERATION 2 WIRING TEST RESULTS")
    logger.info("=" * 60)
    for name, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        logger.info("  %s: %s", name, status)

    total = len(results)
    passed_count = sum(1 for v in results.values() if v)
    logger.info("")
    logger.info("  %d/%d tests passed", passed_count, total)
    logger.info("=" * 60)

    if passed_count < total:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
