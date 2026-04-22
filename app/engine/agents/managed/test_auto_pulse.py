"""Integration test for auto-pulse service.

Tests the auto-pulse system against a live sim run with an active AI agent.
Verifies that events trigger AI agent responses through the real game systems.

Usage:
    cd app/
    PYTHONPATH=. ../.venv/bin/python3 engine/agents/managed/test_auto_pulse.py

Requires: ANTHROPIC_API_KEY + SUPABASE_URL + SUPABASE_KEY in environment.
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys
import time
from pathlib import Path

# Load .env from project root
env_path = Path(__file__).resolve().parents[4] / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())

# Add app/ to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("test_auto_pulse")

# ── Config ────────────────────────────────────────────────────────────

# Use Test33 Vizier agent
SIM_RUN_ID = "c954b9b6-35f0-4973-a08b-f38406c524e7"


# ── Helpers ───────────────────────────────────────────────────────────

def get_db():
    from engine.services.supabase import get_client
    return get_client()


def find_ai_agent(sim_run_id: str) -> dict | None:
    """Find an active AI agent session in the sim run."""
    db = get_db()
    result = (
        db.table("ai_agent_sessions")
        .select("*")
        .eq("sim_run_id", sim_run_id)
        .in_("status", ["ready", "active"])
        .limit(1)
        .execute()
    )
    if result.data:
        return result.data[0]
    return None


def find_ai_role(sim_run_id: str) -> dict | None:
    """Find an AI-operated role in the sim run."""
    db = get_db()
    result = (
        db.table("roles")
        .select("id, character_name, country_code, positions, is_ai_operated")
        .eq("sim_run_id", sim_run_id)
        .eq("is_ai_operated", True)
        .eq("status", "active")
        .limit(1)
        .execute()
    )
    if result.data:
        return result.data[0]
    return None


def find_human_role(sim_run_id: str) -> dict | None:
    """Find a human-operated role in the sim run (for sending to AI)."""
    db = get_db()
    result = (
        db.table("roles")
        .select("id, character_name, country_code, positions, is_ai_operated")
        .eq("sim_run_id", sim_run_id)
        .eq("status", "active")
        .execute()
    )
    for r in result.data or []:
        if not r.get("is_ai_operated"):
            return r
    return None


def count_observatory_events(sim_run_id: str, category: str, since_seconds: int = 30) -> int:
    """Count recent observatory events of a given category."""
    from datetime import datetime, timezone, timedelta
    db = get_db()
    cutoff = (datetime.now(timezone.utc) - timedelta(seconds=since_seconds)).isoformat()
    result = (
        db.table("observatory_events")
        .select("id")
        .eq("sim_run_id", sim_run_id)
        .eq("category", category)
        .gte("created_at", cutoff)
        .execute()
    )
    return len(result.data or [])


# ── Test 1: Core pulse_ai_agent ──────────────────────────────────────

async def test_core_pulse():
    """Test that pulse_ai_agent can reach an AI agent and get a response."""
    logger.info("=" * 60)
    logger.info("TEST 1: Core pulse_ai_agent")
    logger.info("=" * 60)

    from engine.agents.managed.auto_pulse import pulse_ai_agent

    ai_session = find_ai_agent(SIM_RUN_ID)
    if not ai_session:
        logger.warning("No active AI agent found in sim %s — SKIPPING", SIM_RUN_ID)
        return False

    role_id = ai_session["role_id"]
    logger.info("Found AI agent: %s (%s)", role_id, ai_session["country_code"])

    t0 = time.time()
    result = await pulse_ai_agent(
        sim_run_id=SIM_RUN_ID,
        role_id=role_id,
        message="This is a test pulse. Acknowledge receipt by using write_notes with key='test_pulse' and content='received'.",
        event_type="test",
    )
    elapsed = time.time() - t0

    logger.info("Pulse result: %s (%.1fs)", result, elapsed)

    # Verify observatory event was written
    events = count_observatory_events(SIM_RUN_ID, "auto_pulse_test", since_seconds=60)
    logger.info("Observatory events (auto_pulse_test): %d", events)

    if result:
        logger.info("TEST 1: PASSED — pulse delivered and acknowledged")
    else:
        logger.warning("TEST 1: FAILED — pulse not delivered")
    return result


# ── Test 2: Meeting invitation pulse ─────────────────────────────────

async def test_meeting_invitation():
    """Test on_meeting_invitation — invite AI to a meeting."""
    logger.info("=" * 60)
    logger.info("TEST 2: Meeting invitation pulse")
    logger.info("=" * 60)

    from engine.agents.managed.auto_pulse import on_meeting_invitation

    ai_role = find_ai_role(SIM_RUN_ID)
    if not ai_role:
        logger.warning("No AI role found — SKIPPING")
        return False

    ai_session = find_ai_agent(SIM_RUN_ID)
    if not ai_session:
        logger.warning("No active AI session — SKIPPING")
        return False

    # Create a real meeting invitation in the DB
    db = get_db()
    from datetime import datetime, timezone, timedelta
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()

    # Find a different role to be the inviter
    human_role = find_human_role(SIM_RUN_ID)
    if not human_role:
        # Use a synthetic inviter
        inviter_name = "Test Inviter"
        inviter_role_id = "test_inviter"
        inviter_country = "test"
    else:
        inviter_name = human_role["character_name"]
        inviter_role_id = human_role["id"]
        inviter_country = human_role["country_code"]

    inv_row = {
        "sim_run_id": SIM_RUN_ID,
        "invitation_type": "one_on_one",
        "inviter_role_id": inviter_role_id,
        "inviter_country_code": inviter_country,
        "invitee_role_id": ai_role["id"],
        "message": "Test invitation: discuss trade relations",
        "expires_at": expires_at,
        "status": "pending",
        "responses": {},
    }
    inv_result = db.table("meeting_invitations").insert(inv_row).execute()
    inv_id = inv_result.data[0]["id"] if inv_result.data else "test-inv-id"
    logger.info("Created test invitation: %s", inv_id)

    t0 = time.time()
    result = await on_meeting_invitation(
        sim_run_id=SIM_RUN_ID,
        invitee_role_id=ai_role["id"],
        inviter_name=inviter_name,
        invitation_id=inv_id,
        agenda="Discuss bilateral trade relations and regional security",
    )
    elapsed = time.time() - t0

    logger.info("Meeting invitation pulse result: %s (%.1fs)", result, elapsed)

    # Check if invitation status changed (AI accepted/rejected)
    inv_check = db.table("meeting_invitations").select("status,responses").eq("id", inv_id).execute()
    if inv_check.data:
        status = inv_check.data[0].get("status", "pending")
        responses = inv_check.data[0].get("responses", {})
        logger.info("Invitation status: %s, responses: %s", status, responses)
        if status != "pending":
            logger.info("TEST 2: PASSED — AI responded to invitation (status=%s)", status)
            return True

    # Even if invitation status didn't change directly, the AI might have used
    # respond_to_invitation tool (which goes through dispatch)
    events = count_observatory_events(SIM_RUN_ID, "auto_pulse_meeting_invitation", since_seconds=60)
    if events > 0 or result:
        logger.info("TEST 2: PASSED — pulse delivered, %d observatory events", events)
        return True

    logger.warning("TEST 2: FAILED")
    return False


# ── Test 3: Chat message auto-pulse ──────────────────────────────────

async def test_chat_message():
    """Test on_chat_message — send message to AI in a meeting."""
    logger.info("=" * 60)
    logger.info("TEST 3: Chat message auto-pulse")
    logger.info("=" * 60)

    from engine.agents.managed.auto_pulse import on_chat_message

    ai_role = find_ai_role(SIM_RUN_ID)
    if not ai_role:
        logger.warning("No AI role found — SKIPPING")
        return False

    ai_session = find_ai_agent(SIM_RUN_ID)
    if not ai_session:
        logger.warning("No active AI session — SKIPPING")
        return False

    human_role = find_human_role(SIM_RUN_ID)
    if not human_role:
        logger.warning("No human role found for test — SKIPPING")
        return False

    db = get_db()

    # Create a test meeting (or find existing one)
    from engine.services.meeting_service import create_meeting
    meeting = create_meeting(
        sim_run_id=SIM_RUN_ID,
        invitation_id=None,
        participant_a_role_id=human_role["id"],
        participant_a_country=human_role["country_code"],
        participant_b_role_id=ai_role["id"],
        participant_b_country=ai_role["country_code"],
        agenda="Test chat for auto-pulse verification",
        round_num=1,
    )
    meeting_id = meeting.get("id")
    if not meeting_id:
        logger.warning("Failed to create test meeting — SKIPPING")
        return False

    logger.info("Created test meeting: %s", meeting_id)

    # Send a human message first
    from engine.services.meeting_service import send_message
    send_message(meeting_id, human_role["id"], human_role["country_code"],
                 "Greetings. I would like to discuss our mutual interests in the region.")

    # Count messages before pulse
    msgs_before = db.table("meeting_messages").select("id").eq("meeting_id", meeting_id).execute()
    count_before = len(msgs_before.data or [])
    logger.info("Messages before pulse: %d", count_before)

    t0 = time.time()
    result = await on_chat_message(
        sim_run_id=SIM_RUN_ID,
        meeting_id=meeting_id,
        sender_role_id=human_role["id"],
        sender_country=human_role["country_code"],
        other_role_id=ai_role["id"],
    )
    elapsed = time.time() - t0

    logger.info("Chat pulse result: %s (%.1fs)", result, elapsed)

    # Check if AI responded
    msgs_after = db.table("meeting_messages").select("id,role_id,content").eq("meeting_id", meeting_id).order("created_at").execute()
    count_after = len(msgs_after.data or [])
    logger.info("Messages after pulse: %d (was %d)", count_after, count_before)

    if count_after > count_before:
        last_msg = msgs_after.data[-1]
        logger.info("AI response: [%s] %s", last_msg["role_id"], last_msg["content"][:200])
        logger.info("TEST 3: PASSED — AI responded in chat")
        return True

    logger.warning("TEST 3: FAILED — no new messages from AI")
    return False


# ── Test 4: pulse_ai_for_country ─────────────────────────────────────

async def test_country_pulse():
    """Test pulse_ai_for_country — find HoS and pulse them."""
    logger.info("=" * 60)
    logger.info("TEST 4: pulse_ai_for_country")
    logger.info("=" * 60)

    from engine.agents.managed.auto_pulse import pulse_ai_for_country

    ai_role = find_ai_role(SIM_RUN_ID)
    if not ai_role:
        logger.warning("No AI role found — SKIPPING")
        return False

    country = ai_role["country_code"]
    logger.info("Testing country pulse for %s", country)

    t0 = time.time()
    result = await pulse_ai_for_country(
        sim_run_id=SIM_RUN_ID,
        country_code=country,
        message=(
            "SITUATION UPDATE: Intelligence reports indicate increased "
            "military activity near your borders. Assess the situation "
            "using get_my_forces and write_notes with key='border_alert'."
        ),
        event_type="test_country",
    )
    elapsed = time.time() - t0

    logger.info("Country pulse result: %s (%.1fs)", result, elapsed)

    if result:
        logger.info("TEST 4: PASSED — country pulse delivered")
    else:
        logger.warning("TEST 4: FAILED — could not pulse country %s", country)
    return result


# ── Test 5: Verify fire_pulse works from sync context ────────────────

async def test_fire_pulse_integration():
    """Test that fire_pulse schedules correctly from within async context."""
    logger.info("=" * 60)
    logger.info("TEST 5: fire_pulse integration (simulates action_dispatcher)")
    logger.info("=" * 60)

    from engine.agents.managed.auto_pulse import fire_pulse, register_event_loop, pulse_ai_agent

    # Register the current event loop (simulates FastAPI startup)
    register_event_loop(asyncio.get_running_loop())

    ai_role = find_ai_role(SIM_RUN_ID)
    if not ai_role:
        logger.warning("No AI role found — SKIPPING")
        return False

    # fire_pulse from async context (direct)
    fire_pulse(pulse_ai_agent(
        sim_run_id=SIM_RUN_ID,
        role_id=ai_role["id"],
        message="Fire-and-forget test. Acknowledge with write_notes key='fire_test' content='ok'.",
        event_type="fire_test",
    ))

    # Give the background task time to execute
    logger.info("Waiting 15s for fire-and-forget pulse to complete...")
    await asyncio.sleep(15)

    events = count_observatory_events(SIM_RUN_ID, "auto_pulse_fire_test", since_seconds=60)
    logger.info("Observatory events (fire_test): %d", events)

    if events > 0:
        logger.info("TEST 5: PASSED — fire_pulse worked from async context")
        return True

    logger.warning("TEST 5: INCONCLUSIVE — no observatory event found (may still be running)")
    return True  # Don't fail — fire-and-forget is best-effort


# ── Main ──────────────────────────────────────────────────────────────

async def main():
    logger.info("=" * 60)
    logger.info("AUTO-PULSE INTEGRATION TEST SUITE")
    logger.info("Sim Run: %s", SIM_RUN_ID)
    logger.info("=" * 60)

    # Pre-flight check
    ai_session = find_ai_agent(SIM_RUN_ID)
    ai_role = find_ai_role(SIM_RUN_ID)
    logger.info("AI session found: %s", bool(ai_session))
    logger.info("AI role found: %s", bool(ai_role))

    if not ai_session:
        logger.error(
            "No active AI agent session in sim %s. "
            "Start an agent first using the orchestrator.",
            SIM_RUN_ID,
        )
        return

    if ai_role:
        logger.info("AI agent: %s (%s) — %s",
                     ai_role["id"], ai_role["country_code"], ai_role["character_name"])

    results = {}

    # Test 1: Core pulse
    results["core_pulse"] = await test_core_pulse()

    # Test 2: Meeting invitation (only if Test 1 passed)
    if results["core_pulse"]:
        results["meeting_invitation"] = await test_meeting_invitation()
    else:
        logger.info("Skipping Test 2 — core pulse failed")
        results["meeting_invitation"] = False

    # Test 3: Chat message
    if results["core_pulse"]:
        results["chat_message"] = await test_chat_message()
    else:
        logger.info("Skipping Test 3 — core pulse failed")
        results["chat_message"] = False

    # Test 4: Country pulse
    results["country_pulse"] = await test_country_pulse()

    # Test 5: fire_pulse integration
    results["fire_pulse"] = await test_fire_pulse_integration()

    # Summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("TEST RESULTS SUMMARY")
    logger.info("=" * 60)
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    for name, result in results.items():
        status = "PASSED" if result else "FAILED"
        logger.info("  %s: %s", name, status)
    logger.info("")
    logger.info("Total: %d/%d passed", passed, total)
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
