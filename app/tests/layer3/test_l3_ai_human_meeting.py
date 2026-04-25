"""Level 3 — AI-Human bilateral meeting emulation.

Two scenarios:
1. Human (Phrygia/Vizier) invites AI (Columbia/Dealer) — human emulated via ToolExecutor
2. AI (Columbia/Dealer) invites Human (Phrygia/Vizier) — AI via ManagedSessionManager

The "human" side is emulated by inserting messages directly via meeting_service.
The AI side uses a real Claude managed agent session.

Requires: ANTHROPIC_API_KEY, live Supabase DB.
Cost: ~$0.20-$0.40

Run:
    cd /path/to/THUCYDIDES && PYTHONPATH=app .venv/bin/python -m pytest \
        app/tests/layer3/test_l3_ai_human_meeting.py -v -s
"""
import asyncio
import json
import logging
import os
import pytest
from pathlib import Path

logger = logging.getLogger(__name__)

from dotenv import load_dotenv
for _env_candidate in [
    Path(__file__).resolve().parents[3] / ".env",
    Path(__file__).resolve().parents[2] / "engine" / ".env",
]:
    if _env_candidate.exists():
        load_dotenv(_env_candidate)
        break

SIM_RUN_ID = os.environ.get("TEST_SIM_RUN_ID", "c954b9b6-35f0-4973-a08b-f38406c524e7")

pytestmark = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set"
)


def _get_round_num():
    """Fetch current round from sim_runs."""
    from engine.services.supabase import get_client
    client = get_client()
    run = client.table("sim_runs").select("status,current_round") \
        .eq("id", SIM_RUN_ID).limit(1).execute()
    if not run.data or run.data[0]["status"] != "active":
        pytest.skip("Sim not active")
    return run.data[0]["current_round"]


class TestHumanInvitesAI:
    """Human (Phrygia/Vizier) invites AI (Columbia/Dealer) to a meeting."""

    def test_human_invites_ai_to_meeting(self):
        async def _run():
            from engine.agents.managed.session_manager import ManagedSessionManager
            from engine.agents.managed.tool_executor import ToolExecutor
            from engine.services.meeting_service import send_message, end_meeting
            from engine.services.supabase import get_client

            client = get_client()
            manager = ManagedSessionManager()
            round_num = _get_round_num()

            # Step 1: Human creates invitation via ToolExecutor
            human = ToolExecutor(
                country_code="phrygia", scenario_code="ttt_v1",
                sim_run_id=SIM_RUN_ID, round_num=round_num, role_id="vizier",
            )
            invite_result = json.loads(human.execute("request_meeting", {
                "target_country": "columbia",
                "agenda": "Security partnership proposal for Eastern Mediterranean",
            }))
            logger.info("Invitation result: %s", invite_result)
            invitation_id = invite_result.get("invitation_id")
            assert invitation_id, f"Failed to create invitation: {invite_result}"

            # Step 2: AI accepts via ToolExecutor (simulating what the AI agent would do)
            ai_tool = ToolExecutor(
                country_code="columbia", scenario_code="ttt_v1",
                sim_run_id=SIM_RUN_ID, round_num=round_num, role_id="dealer",
            )
            accept_result = json.loads(ai_tool.execute("respond_to_invitation", {
                "invitation_id": invitation_id,
                "decision": "accept",
            }))
            logger.info("Accept result: %s", accept_result)
            meeting_id = accept_result.get("meeting_id")
            assert meeting_id, f"Failed to create meeting: {accept_result}"

            # Step 3: Create AI managed session for Columbia
            ctx = await manager.create_session(
                role_id="dealer", country_code="columbia",
                sim_run_id=SIM_RUN_ID, scenario_code=SIM_RUN_ID,
                round_num=round_num,
            )
            logger.info("Created AI session: %s", ctx.session_id)

            try:
                # Step 4: Human speaks first, AI responds
                human_msg_1 = (
                    "President Dealer, thank you for meeting. We need to discuss "
                    "a joint security framework for the Eastern Mediterranean. "
                    "Our alliance needs teeth, not just words."
                )

                # Write human message to DB
                result = send_message(
                    meeting_id=meeting_id, role_id="vizier",
                    country_code="phrygia", content=human_msg_1,
                )
                assert result["success"], f"Failed to send human message: {result}"
                logger.info("Human (Phrygia) says: %s", human_msg_1[:100])

                # Tell AI about the meeting and human's message
                t1 = await manager.send_event(ctx,
                    "A bilateral meeting has started with Phrygia (Vizier).\n"
                    "Agenda: Security partnership proposal for Eastern Mediterranean\n"
                    "You are responding to their opening statement.\n\n"
                    f"Phrygia says: '{human_msg_1}'\n\n"
                    "Respond naturally as Columbia's leader. 1-3 sentences."
                )

                # Extract AI response
                ai_messages = [e for e in t1 if e.get("type") == "agent_message"]
                ai_text_1 = ai_messages[-1]["content"] if ai_messages else "No response"
                logger.info("AI (Columbia) says: %s", ai_text_1[:200])

                # Write AI message to DB
                result = send_message(
                    meeting_id=meeting_id, role_id="dealer",
                    country_code="columbia", content=ai_text_1[:500],
                )
                assert result["success"], f"Failed to send AI message: {result}"

                # Step 5: Human responds, AI replies again
                human_msg_2 = (
                    "Agreed. I propose we start with joint naval patrols "
                    "in the Eastern Med. Our fleets can coordinate through "
                    "a shared command channel."
                )

                result = send_message(
                    meeting_id=meeting_id, role_id="vizier",
                    country_code="phrygia", content=human_msg_2,
                )
                assert result["success"], f"Failed to send human message 2: {result}"
                logger.info("Human (Phrygia) says: %s", human_msg_2[:100])

                t2 = await manager.send_event(ctx,
                    f"Phrygia says: '{human_msg_2}'\n\n"
                    "Respond naturally. 1-3 sentences."
                )

                ai_messages_2 = [e for e in t2 if e.get("type") == "agent_message"]
                ai_text_2 = ai_messages_2[-1]["content"] if ai_messages_2 else "No response"
                logger.info("AI (Columbia) says: %s", ai_text_2[:200])

                result = send_message(
                    meeting_id=meeting_id, role_id="dealer",
                    country_code="columbia", content=ai_text_2[:500],
                )
                assert result["success"], f"Failed to send AI message 2: {result}"

                # Step 6: End meeting
                end_result = end_meeting(meeting_id=meeting_id, role_id="vizier")
                logger.info("End meeting result: %s", end_result)

                # Step 7: Verify messages in DB
                msgs = client.table("meeting_messages") \
                    .select("country_code,role_id,content,turn_number,channel") \
                    .eq("meeting_id", meeting_id) \
                    .order("turn_number") \
                    .execute()

                text_msgs = [m for m in (msgs.data or []) if m.get("channel") != "system"]
                logger.info("Messages in DB: %d text + system", len(text_msgs))

                assert len(text_msgs) >= 4, \
                    f"Expected 4+ text messages, got {len(text_msgs)}"

                # Verify both countries spoke
                speakers = {m["country_code"] for m in text_msgs}
                assert speakers == {"phrygia", "columbia"}, \
                    f"Expected both countries, got: {speakers}"

                # Verify messages have real content
                for m in text_msgs:
                    assert len(m.get("content", "")) > 3, \
                        f"Message too short: {m.get('content')!r}"

                # Report costs
                cost = manager.get_cost_estimate(ctx)
                logger.info("Cost: $%.4f (in=%d, out=%d)",
                            cost["total_cost_usd"],
                            cost["input_tokens"],
                            cost["output_tokens"])

            finally:
                await manager.cleanup(ctx)

        asyncio.run(_run())


class TestAIInvitesHuman:
    """AI (Columbia/Dealer) invites Human (Phrygia/Vizier) to a meeting."""

    def test_ai_invites_human_to_meeting(self):
        async def _run():
            from engine.agents.managed.session_manager import ManagedSessionManager
            from engine.agents.managed.tool_executor import ToolExecutor
            from engine.services.meeting_service import send_message, end_meeting
            from engine.services.supabase import get_client

            client = get_client()
            manager = ManagedSessionManager()
            round_num = _get_round_num()

            # Step 1: AI creates invitation via ToolExecutor (acting for Columbia)
            ai_tool = ToolExecutor(
                country_code="columbia", scenario_code="ttt_v1",
                sim_run_id=SIM_RUN_ID, round_num=round_num, role_id="dealer",
            )
            invite_result = json.loads(ai_tool.execute("request_meeting", {
                "target_country": "phrygia",
                "agenda": "Trade agreement and economic cooperation",
            }))
            logger.info("AI invitation result: %s", invite_result)
            invitation_id = invite_result.get("invitation_id")
            assert invitation_id, f"Failed to create invitation: {invite_result}"

            # Step 2: Human accepts via ToolExecutor
            human_tool = ToolExecutor(
                country_code="phrygia", scenario_code="ttt_v1",
                sim_run_id=SIM_RUN_ID, round_num=round_num, role_id="vizier",
            )
            accept_result = json.loads(human_tool.execute("respond_to_invitation", {
                "invitation_id": invitation_id,
                "decision": "accept",
            }))
            logger.info("Human accept result: %s", accept_result)
            meeting_id = accept_result.get("meeting_id")
            assert meeting_id, f"Failed to create meeting: {accept_result}"

            # Step 3: Create AI managed session for Columbia
            ctx = await manager.create_session(
                role_id="dealer", country_code="columbia",
                sim_run_id=SIM_RUN_ID, scenario_code=SIM_RUN_ID,
                round_num=round_num,
            )
            logger.info("Created AI session: %s", ctx.session_id)

            try:
                # Step 4: AI speaks first (it initiated the meeting)
                t1 = await manager.send_event(ctx,
                    "You have initiated a bilateral meeting with Phrygia (Vizier).\n"
                    "Agenda: Trade agreement and economic cooperation\n"
                    "You are the initiator — make your opening statement.\n\n"
                    "Speak naturally as Columbia's leader. 1-3 sentences."
                )

                ai_messages = [e for e in t1 if e.get("type") == "agent_message"]
                ai_text_1 = ai_messages[-1]["content"] if ai_messages else "No response"
                logger.info("AI (Columbia) opens: %s", ai_text_1[:200])

                # Write AI message to DB
                result = send_message(
                    meeting_id=meeting_id, role_id="dealer",
                    country_code="columbia", content=ai_text_1[:500],
                )
                assert result["success"], f"Failed to send AI message: {result}"

                # Step 5: Human responds
                human_msg_1 = (
                    "Thank you for the invitation, President Dealer. "
                    "Phrygia is open to deepening trade ties. "
                    "What specific sectors are you looking to expand cooperation in?"
                )

                result = send_message(
                    meeting_id=meeting_id, role_id="vizier",
                    country_code="phrygia", content=human_msg_1,
                )
                assert result["success"], f"Failed to send human message: {result}"
                logger.info("Human (Phrygia) says: %s", human_msg_1[:100])

                # AI responds to human
                t2 = await manager.send_event(ctx,
                    f"Phrygia says: '{human_msg_1}'\n\n"
                    "Respond naturally. 1-3 sentences."
                )

                ai_messages_2 = [e for e in t2 if e.get("type") == "agent_message"]
                ai_text_2 = ai_messages_2[-1]["content"] if ai_messages_2 else "No response"
                logger.info("AI (Columbia) says: %s", ai_text_2[:200])

                result = send_message(
                    meeting_id=meeting_id, role_id="dealer",
                    country_code="columbia", content=ai_text_2[:500],
                )
                assert result["success"], f"Failed to send AI message 2: {result}"

                # Step 6: One more exchange
                human_msg_2 = (
                    "Energy and agriculture sound promising. "
                    "Let's have our trade ministers draft a framework by next round."
                )

                result = send_message(
                    meeting_id=meeting_id, role_id="vizier",
                    country_code="phrygia", content=human_msg_2,
                )
                assert result["success"], f"Failed to send human message 2: {result}"
                logger.info("Human (Phrygia) says: %s", human_msg_2[:100])

                t3 = await manager.send_event(ctx,
                    f"Phrygia says: '{human_msg_2}'\n\n"
                    "Respond naturally. 1-3 sentences. This will be the final exchange."
                )

                ai_messages_3 = [e for e in t3 if e.get("type") == "agent_message"]
                ai_text_3 = ai_messages_3[-1]["content"] if ai_messages_3 else "No response"
                logger.info("AI (Columbia) says: %s", ai_text_3[:200])

                result = send_message(
                    meeting_id=meeting_id, role_id="dealer",
                    country_code="columbia", content=ai_text_3[:500],
                )
                assert result["success"], f"Failed to send AI message 3: {result}"

                # Step 7: End meeting
                end_result = end_meeting(meeting_id=meeting_id, role_id="dealer")
                logger.info("End meeting result: %s", end_result)

                # Step 8: Verify messages in DB
                msgs = client.table("meeting_messages") \
                    .select("country_code,role_id,content,turn_number,channel") \
                    .eq("meeting_id", meeting_id) \
                    .order("turn_number") \
                    .execute()

                text_msgs = [m for m in (msgs.data or []) if m.get("channel") != "system"]
                logger.info("Messages in DB: %d text + system", len(text_msgs))

                assert len(text_msgs) >= 5, \
                    f"Expected 5+ text messages, got {len(text_msgs)}"

                # Verify both countries spoke
                speakers = {m["country_code"] for m in text_msgs}
                assert speakers == {"phrygia", "columbia"}, \
                    f"Expected both countries, got: {speakers}"

                # Verify alternating pattern (AI first in this case)
                first_speaker = text_msgs[0]["country_code"]
                assert first_speaker == "columbia", \
                    f"AI should speak first (initiated), got: {first_speaker}"

                # Verify messages have real content
                for m in text_msgs:
                    assert len(m.get("content", "")) > 3, \
                        f"Message too short: {m.get('content')!r}"

                # Report costs
                cost = manager.get_cost_estimate(ctx)
                logger.info("Cost: $%.4f (in=%d, out=%d)",
                            cost["total_cost_usd"],
                            cost["input_tokens"],
                            cost["output_tokens"])

            finally:
                await manager.cleanup(ctx)

        asyncio.run(_run())
