"""Level 3 — Real AI-AI Meeting via ConversationRouter.

Two real Claude managed agent sessions hold a bilateral meeting.
Tests the full flow: invite → accept → ConversationRouter relay → messages in DB.

Requires: ANTHROPIC_API_KEY, live Supabase DB.
Cost: ~$0.30-$0.50

Run:
    cd /path/to/THUCYDIDES && PYTHONPATH=app .venv/bin/python -m pytest \
        app/tests/layer3/test_l3_ai_ai_meeting.py -v -s
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


class TestAIAIMeeting:
    """Two real agents hold a bilateral meeting via ConversationRouter."""

    def test_full_meeting_flow(self):
        """Phrygia invites Solaria → Solaria accepts → 4-turn conversation."""

        async def _run():
            from engine.agents.managed.session_manager import ManagedSessionManager
            from engine.agents.managed.conversations import ConversationRouter
            from engine.agents.managed.tool_executor import ToolExecutor
            from engine.services.supabase import get_client

            client = get_client()
            manager = ManagedSessionManager()

            # Verify sim is active
            run = client.table("sim_runs").select("status,current_round") \
                .eq("id", SIM_RUN_ID).limit(1).execute()
            if not run.data or run.data[0]["status"] != "active":
                pytest.skip("Sim not active")
            round_num = run.data[0]["current_round"]

            # Step 1: Create invitation using ToolExecutor (sync, no LLM)
            phrygia_tool = ToolExecutor(
                country_code="phrygia", scenario_code="ttt_v1",
                sim_run_id=SIM_RUN_ID, round_num=round_num, role_id="vizier",
            )
            invite_result = json.loads(phrygia_tool.execute("request_meeting", {
                "target_country": "solaria",
                "agenda": "Alliance coordination and trade discussion",
            }))
            logger.info("Invitation result: %s", invite_result)
            invitation_id = invite_result.get("invitation_id")
            assert invitation_id, f"Failed to create invitation: {invite_result}"

            # Step 2: Accept invitation using ToolExecutor (sync, no LLM)
            solaria_tool = ToolExecutor(
                country_code="solaria", scenario_code="ttt_v1",
                sim_run_id=SIM_RUN_ID, round_num=round_num, role_id="wellspring",
            )
            accept_result = json.loads(solaria_tool.execute("respond_to_invitation", {
                "invitation_id": invitation_id,
                "decision": "accept",
            }))
            logger.info("Accept result: %s", accept_result)
            meeting_id = accept_result.get("meeting_id")
            assert meeting_id, f"Failed to create meeting: {accept_result}"

            # Step 3: Create real managed agent sessions
            ctx_a = await manager.create_session(
                role_id="vizier", country_code="phrygia",
                sim_run_id=SIM_RUN_ID, scenario_code=SIM_RUN_ID,
                round_num=round_num,
            )
            ctx_b = await manager.create_session(
                role_id="wellspring", country_code="solaria",
                sim_run_id=SIM_RUN_ID, scenario_code=SIM_RUN_ID,
                round_num=round_num,
            )
            logger.info("Created sessions: Phrygia=%s, Solaria=%s",
                        ctx_a.session_id, ctx_b.session_id)

            try:
                # Step 4: Run meeting via ConversationRouter
                router = ConversationRouter(
                    session_manager=manager,
                    sim_run_id=SIM_RUN_ID,
                )
                agent_states = {"vizier": "IDLE", "wellspring": "IDLE"}

                summary = await router.run_meeting(
                    meeting_id=meeting_id,
                    agent_a=ctx_a,
                    agent_b=ctx_b,
                    agent_states=agent_states,
                    round_num=round_num,
                    max_turns=4,  # Keep short for testing cost
                )

                logger.info("Meeting summary:")
                logger.info("  Turns: %d (A=%d, B=%d)",
                            summary.get("turns", 0),
                            summary.get("turns_a", 0),
                            summary.get("turns_b", 0))
                logger.info("  End reason: %s", summary.get("end_reason", "?"))

                # Log conversation
                for msg in summary.get("messages", []):
                    logger.info("  [%s] %s: %s",
                                msg.get("turn_num", "?"),
                                msg.get("role_id", "?"),
                                (msg.get("content") or "")[:100])

                # Verify: at least 2 turns happened
                turns = summary.get("turns", 0)
                assert turns >= 2, f"Meeting should have 2+ turns, had {turns}"

                # Verify: messages in DB
                msgs = client.table("meeting_messages") \
                    .select("country_code,content,turn_number") \
                    .eq("meeting_id", meeting_id) \
                    .order("created_at").execute()
                logger.info("Messages in DB: %d", len(msgs.data or []))
                assert len(msgs.data or []) >= 2, \
                    f"Meeting should have 2+ messages in DB, found {len(msgs.data or [])}"

                # Verify: messages have real content (not empty)
                for m in (msgs.data or []):
                    assert len(m.get("content", "")) > 3, \
                        f"Message too short: {m.get('content')!r}"

                # Verify: both countries spoke
                speakers = {m["country_code"] for m in (msgs.data or [])}
                logger.info("Speakers: %s", speakers)
                assert len(speakers) >= 2, f"Both countries should speak, got: {speakers}"

                # Report costs
                cost_a = manager.get_cost_estimate(ctx_a)
                cost_b = manager.get_cost_estimate(ctx_b)
                logger.info("Costs: Phrygia=$%.4f, Solaria=$%.4f, Total=$%.4f",
                            cost_a["total_cost_usd"], cost_b["total_cost_usd"],
                            cost_a["total_cost_usd"] + cost_b["total_cost_usd"])

            finally:
                await manager.cleanup(ctx_a)
                await manager.cleanup(ctx_b)

        asyncio.run(_run())
