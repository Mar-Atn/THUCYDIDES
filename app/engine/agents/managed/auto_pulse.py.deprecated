"""Auto-pulse service — delivers game events to AI agents in real-time.

When a game event affects an AI participant, this service automatically
sends a pulse to their managed agent session so they can respond.
Fire-and-forget safe — all functions catch exceptions internally.

Events handled:
  1. Chat message received in meeting (moved from main.py)
  2. Meeting invitation received
  3. Meeting accepted (inviter is AI)
  4. Transaction/exchange proposed
  5. Agreement proposed
  6. Attack declared (ground, air, naval, bombardment, missile)
  7. Nuclear events (authorize request, launch against territory)
  8. War declared against AI country

Integration points:
  - action_dispatcher.py calls on_* after dispatching relevant actions
  - main.py send_meeting_message calls on_chat_message
  - All calls are fire-and-forget via asyncio.create_task

Dependencies: session_manager (async), supabase (sync for DB lookups).
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from engine.agents.managed.event_handler import write_agent_log_event
from engine.services.supabase import get_client

logger = logging.getLogger(__name__)


# ── Core pulse infrastructure ─────────────────────────────────────────

def _get_ai_session(sim_run_id: str, role_id: str) -> dict | None:
    """Look up an active AI agent session from DB. Returns row or None."""
    try:
        db = get_client()
        result = (
            db.table("ai_agent_sessions")
            .select("*")
            .eq("sim_run_id", sim_run_id)
            .eq("role_id", role_id)
            .in_("status", ["ready", "active"])
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None
    except Exception as e:
        logger.warning("Failed to look up AI session for %s: %s", role_id, e)
        return None


def _is_ai_role(sim_run_id: str, role_id: str) -> bool:
    """Check if a role is AI-operated."""
    try:
        db = get_client()
        result = (
            db.table("roles")
            .select("is_ai_operated")
            .eq("sim_run_id", sim_run_id)
            .eq("id", role_id)
            .limit(1)
            .execute()
        )
        return bool(result.data and result.data[0].get("is_ai_operated"))
    except Exception as e:
        logger.warning("Failed to check AI status for %s: %s", role_id, e)
        return False


def _find_hos_role_id(sim_run_id: str, country_code: str) -> str | None:
    """Find the Head of State role_id for a country."""
    try:
        db = get_client()
        result = (
            db.table("roles")
            .select("id, is_ai_operated, positions")
            .eq("sim_run_id", sim_run_id)
            .eq("country_code", country_code)
            .eq("status", "active")
            .execute()
        )
        for role in result.data or []:
            positions = role.get("positions") or []
            if "head_of_state" in positions:
                return role["id"] if role.get("is_ai_operated") else None
        return None
    except Exception as e:
        logger.warning("Failed to find HoS for %s: %s", country_code, e)
        return None


def _build_session_context(session_row: dict, sim_run_id: str):
    """Reconstruct a SessionContext from a DB row."""
    from engine.agents.managed.session_manager import SessionContext
    from engine.agents.managed.tool_executor import ToolExecutor

    role_id = session_row["role_id"]
    country_code = session_row["country_code"]

    executor = ToolExecutor(
        country_code=country_code,
        scenario_code=sim_run_id,
        sim_run_id=sim_run_id,
        round_num=session_row.get("round_num", 1),
        role_id=role_id,
    )

    return SessionContext(
        agent_id=session_row["agent_id"],
        agent_version=1,
        environment_id=session_row["environment_id"],
        session_id=session_row["session_id"],
        role_id=role_id,
        country_code=country_code,
        sim_run_id=sim_run_id,
        scenario_code=sim_run_id,
        model=session_row.get("model", "claude-sonnet-4-6"),
        round_num=session_row.get("round_num", 1),
        tool_executor=executor,
    )


async def pulse_ai_agent(
    sim_run_id: str,
    role_id: str,
    message: str,
    event_type: str = "auto_pulse",
) -> bool:
    """Send a pulse to an AI agent if they have an active session.

    Returns True if pulse was sent, False if agent is not AI or no session.
    Fire-and-forget safe — catches all exceptions.
    """
    try:
        if not _is_ai_role(sim_run_id, role_id):
            return False

        session_row = _get_ai_session(sim_run_id, role_id)
        if not session_row:
            logger.debug("No active AI session for %s — skipping pulse", role_id)
            return False

        from engine.agents.managed.session_manager import ManagedSessionManager

        ctx = _build_session_context(session_row, sim_run_id)
        mgr = ManagedSessionManager()

        logger.info(
            "[auto-pulse] Sending %s to %s (%s): %s",
            event_type, role_id, session_row["country_code"], message[:100],
        )

        transcript = await mgr.send_event(ctx, message)

        # Log pulse to observatory
        write_agent_log_event(
            sim_run_id=sim_run_id,
            country_code=session_row["country_code"],
            round_num=session_row.get("round_num", 1),
            event_type=f"auto_pulse_{event_type}",
            title=f"Auto-pulse ({event_type}) → {role_id}",
            description=message[:500],
            metadata={
                "role_id": role_id,
                "transcript_entries": len(transcript),
                "event_type": event_type,
            },
        )

        logger.info(
            "[auto-pulse] %s responded with %d entries",
            role_id, len(transcript),
        )
        return True

    except Exception as e:
        logger.warning("[auto-pulse] Failed for %s (%s): %s", role_id, event_type, e)
        return False


async def pulse_ai_for_country(
    sim_run_id: str,
    country_code: str,
    message: str,
    event_type: str = "auto_pulse",
) -> bool:
    """Find the AI HoS for a country and pulse them."""
    hos_role_id = _find_hos_role_id(sim_run_id, country_code)
    if not hos_role_id:
        return False
    return await pulse_ai_agent(sim_run_id, hos_role_id, message, event_type)


# ── Fire-and-forget wrapper ───────────────────────────────────────────

def fire_pulse(coro) -> None:
    """Schedule a coroutine as a fire-and-forget task.

    Safe to call from sync or async context, including from threads
    spawned by asyncio.to_thread (which is how dispatch_action runs).
    Never blocks the caller. Exceptions are caught by the pulse functions.
    """
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(coro)
    except RuntimeError:
        # Called from a non-async thread (e.g., asyncio.to_thread).
        # Use call_soon_threadsafe to schedule on the main event loop.
        try:
            import threading
            # In FastAPI + uvicorn, there's typically one event loop
            # accessible via asyncio internals. We need a reference to it.
            # The safest approach: store a reference when the module loads in async context.
            loop = _get_main_loop()
            if loop and loop.is_running():
                loop.call_soon_threadsafe(loop.create_task, coro)
            else:
                logger.warning("[auto-pulse] No running event loop for fire-and-forget pulse")
        except Exception as e:
            logger.warning("[auto-pulse] Failed to schedule pulse from thread: %s", e)


# Module-level event loop reference for cross-thread scheduling
_main_event_loop: asyncio.AbstractEventLoop | None = None


def register_event_loop(loop: asyncio.AbstractEventLoop) -> None:
    """Register the main event loop for cross-thread pulse scheduling.

    Called once during FastAPI startup (lifespan).
    """
    global _main_event_loop
    _main_event_loop = loop
    logger.info("[auto-pulse] Registered main event loop for cross-thread scheduling")


def _get_main_loop() -> asyncio.AbstractEventLoop | None:
    """Get the registered main event loop."""
    return _main_event_loop


# ── Event-specific pulse functions ────────────────────────────────────


async def on_chat_message(
    sim_run_id: str,
    meeting_id: str,
    sender_role_id: str,
    sender_country: str,
    other_role_id: str,
) -> bool:
    """Called when a human sends a chat message to an AI agent.

    Fetches recent conversation context, pulses the AI, and writes
    the AI's response back to meeting_messages.
    """
    try:
        if not _is_ai_role(sim_run_id, other_role_id):
            return False

        session_row = _get_ai_session(sim_run_id, other_role_id)
        if not session_row:
            return False

        from engine.agents.managed.session_manager import ManagedSessionManager
        from engine.services.meeting_service import send_message

        ctx = _build_session_context(session_row, sim_run_id)
        mgr = ManagedSessionManager()
        db = get_client()

        # Get conversation context (last 6 messages)
        all_msgs = (
            db.table("meeting_messages")
            .select("role_id,content")
            .eq("meeting_id", meeting_id)
            .order("created_at")
            .execute()
        )

        chat_lines = []
        for m in all_msgs.data or []:
            chat_lines.append(f'{m["role_id"]}: "{m["content"]}"')
        chat_text = "\n".join(chat_lines[-6:])

        # Pulse the AI agent
        transcript = await mgr.send_event(
            ctx,
            f"You are in a meeting (meeting_id: {meeting_id}). "
            f"Here is the conversation:\n\n{chat_text}\n\n"
            f"Respond naturally. 1-3 sentences. Stay in character. "
            f"Use the send_message tool with meeting_id='{meeting_id}' to reply.",
        )

        # Fallback: if AI responded with agent_message but didn't use send_message tool,
        # write the response directly to meeting_messages
        used_send_message = any(
            e.get("type") == "tool_call" and e.get("tool") == "send_message"
            for e in transcript
        )

        if not used_send_message:
            for entry in transcript:
                if entry.get("type") == "agent_message" and entry.get("content"):
                    text = entry["content"].strip()
                    # Remove any role-prefix the agent might add
                    for prefix in [
                        f"**{other_role_id.upper()}:**",
                        f"{other_role_id.upper()}:",
                        f"**{session_row['country_code'].upper()}:**",
                    ]:
                        if text.startswith(prefix):
                            text = text[len(prefix):].strip()
                    if text and len(text) > 3:
                        send_message(
                            meeting_id, other_role_id,
                            session_row["country_code"], text[:500],
                        )
                        break

        # Log to observatory
        write_agent_log_event(
            sim_run_id=sim_run_id,
            country_code=session_row["country_code"],
            round_num=session_row.get("round_num", 1),
            event_type="auto_pulse_chat",
            title=f"Auto-pulse chat → {other_role_id}",
            description=f"Responded in meeting {meeting_id[:8]}",
            metadata={"meeting_id": meeting_id, "sender": sender_role_id},
        )

        logger.info(
            "[auto-pulse] Chat: %s responded in meeting %s",
            other_role_id, meeting_id[:8],
        )
        return True

    except Exception as e:
        logger.warning("[auto-pulse] Chat failed for %s: %s", other_role_id, e)
        return False


async def on_meeting_invitation(
    sim_run_id: str,
    invitee_role_id: str,
    inviter_name: str,
    invitation_id: str,
    agenda: str = "",
) -> bool:
    """Called when someone invites an AI agent to a meeting.

    Pulses them to accept/decline via respond_to_invitation tool.
    """
    msg = (
        f"📬 MEETING INVITATION RECEIVED\n\n"
        f"You have received a meeting invitation from {inviter_name}.\n"
        f"Agenda: {agenda or 'No agenda specified'}\n"
        f"Invitation ID: {invitation_id}\n\n"
        f"Decide whether to accept or decline this meeting. "
        f"Use the respond_to_invitation tool with invitation_id='{invitation_id}' "
        f"and your decision ('accept' or 'reject').\n\n"
        f"Consider: Is this meeting useful for your strategy? "
        f"Do you have time? Is this person trustworthy?"
    )
    return await pulse_ai_agent(sim_run_id, invitee_role_id, msg, "meeting_invitation")


async def on_meeting_accepted(
    sim_run_id: str,
    inviter_role_id: str,
    accepter_name: str,
    meeting_id: str,
    agenda: str = "",
) -> bool:
    """Called when a meeting invitation is accepted — notify the inviter if AI.

    The AI inviter should speak first since they requested the meeting.
    """
    msg = (
        f"📩 MEETING STARTED\n\n"
        f"Your meeting with {accepter_name} has been accepted and is now active.\n"
        f"Meeting ID: {meeting_id}\n"
        f"Agenda: {agenda or 'General discussion'}\n\n"
        f"You initiated this meeting, so you speak first. "
        f"Use the send_message tool with meeting_id='{meeting_id}' to begin the conversation.\n\n"
        f"Keep your opening message focused — state what you want to discuss. "
        f"1-3 sentences, stay in character."
    )
    return await pulse_ai_agent(sim_run_id, inviter_role_id, msg, "meeting_accepted")


async def on_transaction_proposed(
    sim_run_id: str,
    target_country: str,
    proposer_country: str,
    terms_summary: str,
    transaction_id: str,
) -> bool:
    """Called when someone proposes a transaction to an AI country."""
    msg = (
        f"📦 TRANSACTION PROPOSAL RECEIVED\n\n"
        f"{proposer_country.upper()} has proposed a transaction to your country.\n"
        f"Terms: {terms_summary}\n"
        f"Transaction ID: {transaction_id}\n\n"
        f"Review this proposal carefully. You can accept, reject, or counter-offer.\n"
        f"Use submit_action with action_type='accept_transaction', "
        f"transaction_id='{transaction_id}', and response='accept' or 'reject'.\n\n"
        f"Consider: Is this deal fair? What do you gain? What do you lose? "
        f"Does this serve your strategic interests?"
    )
    return await pulse_ai_for_country(sim_run_id, target_country, msg, "transaction_proposed")


async def on_agreement_proposed(
    sim_run_id: str,
    target_country: str,
    proposer_country: str,
    agreement_type: str,
    agreement_id: str,
) -> bool:
    """Called when someone proposes a formal agreement to an AI country."""
    msg = (
        f"📜 AGREEMENT PROPOSAL RECEIVED\n\n"
        f"{proposer_country.upper()} proposes a {agreement_type} agreement.\n"
        f"Agreement ID: {agreement_id}\n\n"
        f"Review this agreement. You can sign or decline.\n"
        f"Use submit_action with action_type='sign_agreement', "
        f"agreement_id='{agreement_id}', and confirm=true (to sign) or confirm=false (to decline).\n\n"
        f"Consider: Does this agreement benefit your country? "
        f"What obligations does it impose? Can you trust the other party?"
    )
    return await pulse_ai_for_country(sim_run_id, target_country, msg, "agreement_proposed")


async def on_attack_declared(
    sim_run_id: str,
    target_country: str,
    attacker_country: str,
    attack_type: str,
    details: str,
) -> bool:
    """Called when an attack is declared against an AI country.

    This is a CRITICAL interrupt — bypasses normal pulse schedule.
    """
    msg = (
        f"🚨 ALERT: MILITARY ATTACK\n\n"
        f"{attacker_country.upper()} has launched a {attack_type} attack "
        f"against your territory!\n"
        f"Details: {details}\n\n"
        f"This requires immediate response. Assess the situation:\n"
        f"1. Use get_my_forces to check your military position\n"
        f"2. Consider retaliatory strikes or defensive repositioning\n"
        f"3. Consider diplomatic responses (public statement, request allies)\n"
        f"4. Update your strategic notes with write_notes\n\n"
        f"Act decisively — your nation is under attack."
    )
    return await pulse_ai_for_country(sim_run_id, target_country, msg, "attack_declared")


async def on_war_declared(
    sim_run_id: str,
    target_country: str,
    declarer_country: str,
) -> bool:
    """Called when war is declared against an AI country."""
    msg = (
        f"⚔️ WAR DECLARED\n\n"
        f"{declarer_country.upper()} has declared WAR on your country!\n\n"
        f"This is a critical moment. You must:\n"
        f"1. Assess your military readiness (get_my_forces)\n"
        f"2. Review your alliances (get_relationships)\n"
        f"3. Consider requesting emergency meetings with allies\n"
        f"4. Issue a public statement responding to the declaration\n"
        f"5. Prepare defensive or offensive military plans\n\n"
        f"Your nation's survival may depend on your next decisions."
    )
    return await pulse_ai_for_country(sim_run_id, target_country, msg, "war_declared")


async def on_nuclear_authorize_request(
    sim_run_id: str,
    authorizer_role_id: str,
    initiator_name: str,
    nuclear_action_id: str,
    target_description: str,
) -> bool:
    """Called when a nuclear launch needs authorization from an AI role.

    In most countries, the military chief initiates and the HoS authorizes.
    """
    msg = (
        f"☢️ NUCLEAR AUTHORIZATION REQUEST\n\n"
        f"{initiator_name} has initiated a nuclear launch and requires your authorization.\n"
        f"Target: {target_description}\n"
        f"Nuclear Action ID: {nuclear_action_id}\n\n"
        f"This is the most consequential decision you can make. "
        f"You must authorize or refuse.\n"
        f"Use submit_action with action_type='nuclear_authorize', "
        f"nuclear_action_id='{nuclear_action_id}', and confirm=true or confirm=false.\n\n"
        f"Consider the consequences carefully. A nuclear strike will "
        f"cause massive destruction and reshape all international relationships."
    )
    return await pulse_ai_agent(sim_run_id, authorizer_role_id, msg, "nuclear_authorize")


async def on_nuclear_launch_against(
    sim_run_id: str,
    target_country: str,
    attacker_country: str,
    target_description: str,
) -> bool:
    """Called when a nuclear weapon is launched against an AI country."""
    msg = (
        f"☢️ NUCLEAR STRIKE INCOMING\n\n"
        f"{attacker_country.upper()} has launched a NUCLEAR STRIKE against your territory!\n"
        f"Target: {target_description}\n\n"
        f"This is an existential crisis. Immediate actions:\n"
        f"1. Assess damage potential and your nuclear capability\n"
        f"2. Consider retaliatory nuclear strike if you have the capability\n"
        f"3. Issue an emergency public statement\n"
        f"4. Request emergency allied support\n"
        f"5. Record this moment in your notes\n\n"
        f"The world is watching. Every decision matters."
    )
    return await pulse_ai_for_country(sim_run_id, target_country, msg, "nuclear_incoming")
