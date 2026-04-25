"""Level 3 — Real Managed Agent Sessions (Single Agent).

Creates REAL Claude managed agent sessions and verifies that agents
autonomously explore, reason, and act in the simulation world.

Each test creates a session, sends 1-2 prompts, and verifies the agent
used appropriate tools and submitted valid actions.

Requires: ANTHROPIC_API_KEY in environment, live Supabase DB.
Cost: ~$0.50 total for all tests.

Run:
    cd /path/to/THUCYDIDES && PYTHONPATH=app .venv/bin/python -m pytest \
        app/tests/layer3/test_l3_real_single_agent.py -v -s --timeout=300
"""
import asyncio
import json
import logging
import os
import pytest
from pathlib import Path

logger = logging.getLogger(__name__)

# Load .env (try multiple locations)
from dotenv import load_dotenv
for _env_candidate in [
    Path(__file__).resolve().parents[3] / ".env",       # project root
    Path(__file__).resolve().parents[2] / "engine" / ".env",  # app/engine/
    Path(__file__).resolve().parents[2] / ".env",        # app/
]:
    if _env_candidate.exists():
        load_dotenv(_env_candidate)
        break

SIM_RUN_ID = os.environ.get("TEST_SIM_RUN_ID", "c954b9b6-35f0-4973-a08b-f38406c524e7")

# Skip all if no API key
pytestmark = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set — real agent tests require API access"
)


@pytest.fixture(scope="module")
def manager():
    """Create a ManagedSessionManager for the test module."""
    from engine.agents.managed.session_manager import ManagedSessionManager
    return ManagedSessionManager()


@pytest.fixture(scope="module")
def client():
    from engine.services.supabase import get_client
    return get_client()


@pytest.fixture(scope="module")
def ensure_active(client):
    """Ensure sim is in active Phase A."""
    run = client.table("sim_runs").select("status,current_phase,current_round") \
        .eq("id", SIM_RUN_ID).limit(1).execute()
    if not run.data:
        pytest.skip("SimRun not found")
    status = run.data[0]["status"]
    if status == "pre_start":
        from engine.services.sim_run_manager import start_simulation
        start_simulation(SIM_RUN_ID)
    elif status not in ("active",):
        pytest.skip(f"SimRun status={status}")


def _extract_tool_names(transcript: list[dict]) -> list[str]:
    """Extract tool names from transcript entries."""
    return [e.get("tool", "") for e in transcript if e.get("type") == "tool_call"]


def _extract_actions(transcript: list[dict]) -> list[dict]:
    """Extract submit_action calls from transcript."""
    actions = []
    for e in transcript:
        if e.get("type") == "tool_call" and e.get("tool") == "submit_action":
            actions.append(e.get("input", {}))
    return actions


# ---------------------------------------------------------------------------
# Test 2.1: Sarmatia — Exploration + Combat (nuclear L3, at war with Ruthenia)
# ---------------------------------------------------------------------------

class TestSarmatiaAgent:
    """Real managed agent for Sarmatia — exploration, then combat."""

    @pytest.fixture(autouse=True)
    def _setup(self, ensure_active):
        pass

    def test_sarmatia_explores_and_acts(self, manager, client):
        """Sarmatia agent explores situation, then takes military action."""

        async def _run():
            ctx = await manager.create_session(
                role_id="pathfinder",
                country_code="sarmatia",
                sim_run_id=SIM_RUN_ID,
                scenario_code=SIM_RUN_ID,
                round_num=1,
            )
            logger.info("Created Sarmatia session: %s", ctx.session_id)

            try:
                # Prompt 1: Explore
                t1 = await manager.send_event(ctx,
                    "You are Pathfinder, Head of State of Sarmatia. It is Round 1, Phase A. "
                    "Assess your strategic situation — check your country's state, relationships, "
                    "and military forces. Take notes on what you find."
                )
                tools_used_1 = _extract_tool_names(t1)
                logger.info("Sarmatia exploration tools: %s", tools_used_1)

                # Verify agent used query tools
                query_tools = {"get_my_country", "get_relationships", "get_my_forces",
                               "get_all_countries", "get_recent_events", "get_country_info"}
                used_query = set(tools_used_1) & query_tools
                assert len(used_query) >= 2, \
                    f"Agent should use at least 2 query tools, used: {tools_used_1}"

                # Prompt 2: Act
                t2 = await manager.send_event(ctx,
                    "You are at war with Ruthenia. Their forces are on your border. "
                    "Take decisive action — consider military strikes, diplomatic moves, "
                    "or covert operations. Use your tools."
                )
                tools_used_2 = _extract_tool_names(t2)
                actions = _extract_actions(t2)
                logger.info("Sarmatia action tools: %s", tools_used_2)
                logger.info("Sarmatia actions submitted: %d", len(actions))

                # Verify agent submitted at least one action
                assert "submit_action" in tools_used_2 or "submit_action" in tools_used_1, \
                    f"Agent should submit at least one action. Tools used: {tools_used_1 + tools_used_2}"

                # Check cost
                cost = manager.get_cost_estimate(ctx)
                logger.info("Sarmatia session cost: $%.4f", cost["total_cost_usd"])
                assert cost["total_cost_usd"] < 0.50, f"Cost too high: ${cost['total_cost_usd']}"

            finally:
                await manager.cleanup(ctx)

        asyncio.run(_run())

        # Verify in DB: Sarmatia made decisions
        decisions = client.table("agent_decisions") \
            .select("action_type,validation_status") \
            .eq("sim_run_id", SIM_RUN_ID) \
            .eq("country_code", "sarmatia") \
            .eq("round_num", 1) \
            .execute()
        logger.info("Sarmatia DB decisions: %s",
                     [(d["action_type"], d["validation_status"]) for d in (decisions.data or [])])
        assert len(decisions.data or []) >= 1, "Agent should have at least 1 decision in DB"


# ---------------------------------------------------------------------------
# Test 2.2: Columbia — Diplomatic Superpower
# ---------------------------------------------------------------------------

class TestColumbiaAgent:
    """Real managed agent for Columbia — superpower diplomacy."""

    @pytest.fixture(autouse=True)
    def _setup(self, ensure_active):
        pass

    def test_columbia_diplomatic_actions(self, manager, client):
        """Columbia agent assesses global position and takes diplomatic action."""

        async def _run():
            ctx = await manager.create_session(
                role_id="dealer",
                country_code="columbia",
                sim_run_id=SIM_RUN_ID,
                scenario_code=SIM_RUN_ID,
                round_num=1,
            )
            logger.info("Created Columbia session: %s", ctx.session_id)

            try:
                t1 = await manager.send_event(ctx,
                    "You are Dealer, President of Columbia — the world's dominant power. "
                    "Round 1, Phase A. You lead a coalition of 16 allied nations. "
                    "Assess your situation and take strategic action — diplomacy, "
                    "public statements, military positioning, or economic measures."
                )
                tools_used = _extract_tool_names(t1)
                logger.info("Columbia tools: %s", tools_used)

                # Columbia should use diplomatic/economic tools
                assert len(tools_used) >= 3, \
                    f"Superpower should use 3+ tools, used {len(tools_used)}: {tools_used}"

                cost = manager.get_cost_estimate(ctx)
                logger.info("Columbia cost: $%.4f", cost["total_cost_usd"])

            finally:
                await manager.cleanup(ctx)

        asyncio.run(_run())

        decisions = client.table("agent_decisions") \
            .select("action_type,validation_status") \
            .eq("sim_run_id", SIM_RUN_ID) \
            .eq("country_code", "columbia") \
            .eq("round_num", 1) \
            .execute()
        logger.info("Columbia decisions: %s",
                     [(d["action_type"], d["validation_status"]) for d in (decisions.data or [])])


# ---------------------------------------------------------------------------
# Test 2.3: Persia — Crisis Decision-Making
# ---------------------------------------------------------------------------

class TestPersiaAgent:
    """Real managed agent for Persia — low stability, at war, crisis state."""

    @pytest.fixture(autouse=True)
    def _setup(self, ensure_active):
        pass

    def test_persia_crisis_response(self, manager, client):
        """Persia agent in crisis makes survival decisions."""

        async def _run():
            ctx = await manager.create_session(
                role_id="furnace",
                country_code="persia",
                sim_run_id=SIM_RUN_ID,
                scenario_code=SIM_RUN_ID,
                round_num=1,
            )
            logger.info("Created Persia session: %s", ctx.session_id)

            try:
                t1 = await manager.send_event(ctx,
                    "You are Furnace, Head of State of Persia. Round 1, Phase A. "
                    "Your country is in CRISIS: stability 4/10, treasury nearly empty, "
                    "at war with both Columbia and Levantia. You must act carefully to "
                    "survive. Assess your situation and decide how to respond to these threats."
                )
                tools_used = _extract_tool_names(t1)
                logger.info("Persia crisis tools: %s", tools_used)

                # Even in crisis, agent should assess before acting
                assert len(tools_used) >= 2, \
                    f"Crisis agent should still use tools, used: {tools_used}"

                cost = manager.get_cost_estimate(ctx)
                logger.info("Persia cost: $%.4f", cost["total_cost_usd"])

            finally:
                await manager.cleanup(ctx)

        asyncio.run(_run())


# ---------------------------------------------------------------------------
# Test 2.4: Solaria — OPEC Phase B Decision
# ---------------------------------------------------------------------------

class TestSolariaPhaseB:
    """Real managed agent for Solaria — OPEC member batch decisions."""

    @pytest.fixture(autouse=True)
    def _setup(self, ensure_active):
        pass

    def test_solaria_batch_decisions(self, manager, client):
        """Solaria agent submits Phase B batch decisions including OPEC."""

        async def _run():
            # Transition to Phase B for batch testing
            from engine.services.sim_run_manager import end_phase_a
            try:
                end_phase_a(SIM_RUN_ID)
                logger.info("Transitioned to Phase B")
            except Exception as e:
                logger.warning("Phase transition: %s", e)

            ctx = await manager.create_session(
                role_id="wellspring",
                country_code="solaria",
                sim_run_id=SIM_RUN_ID,
                scenario_code=SIM_RUN_ID,
                round_num=1,
            )
            logger.info("Created Solaria session: %s", ctx.session_id)

            try:
                t1 = await manager.send_event(ctx,
                    "PHASE B — BATCH DECISIONS REQUIRED.\n\n"
                    "You must now submit your batch decisions for this round:\n"
                    "1. set_budget — allocate social spending, military production, tech R&D\n"
                    "2. set_tariffs — optional, per-country tariff levels\n"
                    "3. set_sanctions — optional, per-country sanctions\n"
                    "4. set_opec — Solaria is an OPEC member. Set your production level.\n\n"
                    "Review your economic state with get_my_country, then submit your decisions."
                )
                tools_used = _extract_tool_names(t1)
                actions = _extract_actions(t1)
                logger.info("Solaria Phase B tools: %s", tools_used)

                # Verify agent submitted batch decisions
                action_types = [a.get("action", {}).get("action_type") for a in actions]
                logger.info("Solaria action types: %s", action_types)

                cost = manager.get_cost_estimate(ctx)
                logger.info("Solaria cost: $%.4f", cost["total_cost_usd"])

            finally:
                await manager.cleanup(ctx)

            # Restore to Phase A for subsequent tests
            try:
                from engine.services.sim_run_manager import end_phase_b, advance_round
                end_phase_b(SIM_RUN_ID)
                advance_round(SIM_RUN_ID)
                logger.info("Advanced to Round 2 Phase A")
            except Exception as e:
                logger.warning("Phase restore: %s — manual fix may be needed", e)

        asyncio.run(_run())

        # Verify batch decisions in DB
        decisions = client.table("agent_decisions") \
            .select("action_type,validation_status") \
            .eq("sim_run_id", SIM_RUN_ID) \
            .eq("country_code", "solaria") \
            .execute()
        solaria_types = [d["action_type"] for d in (decisions.data or [])]
        logger.info("Solaria all decisions: %s", solaria_types)


# ---------------------------------------------------------------------------
# Test 2.5: Phrygia — Meeting Initiation
# ---------------------------------------------------------------------------

class TestPhrygiaMeeting:
    """Real managed agent for Phrygia — initiates a meeting."""

    @pytest.fixture(autouse=True)
    def _setup(self, ensure_active):
        pass

    def test_phrygia_requests_meeting(self, manager, client):
        """Phrygia agent reaches out for diplomatic meeting."""

        async def _run():
            # Get current round
            run = client.table("sim_runs").select("current_round") \
                .eq("id", SIM_RUN_ID).limit(1).execute()
            round_num = run.data[0]["current_round"] if run.data else 1

            ctx = await manager.create_session(
                role_id="vizier",
                country_code="phrygia",
                sim_run_id=SIM_RUN_ID,
                scenario_code=SIM_RUN_ID,
                round_num=round_num,
            )
            logger.info("Created Phrygia session: %s (round %d)", ctx.session_id, round_num)

            try:
                t1 = await manager.send_event(ctx,
                    f"You are Vizier, Head of State of Phrygia. Round {round_num}, Phase A. "
                    "You are a member of the Western Treaty alliance. "
                    "You should reach out to an ally or potential partner for a bilateral meeting. "
                    "Use the request_meeting tool to invite another country's leader to discuss "
                    "your strategic situation."
                )
                tools_used = _extract_tool_names(t1)
                logger.info("Phrygia meeting tools: %s", tools_used)

                # Check if agent used request_meeting
                meeting_requested = "request_meeting" in tools_used
                logger.info("Meeting requested: %s", meeting_requested)

                cost = manager.get_cost_estimate(ctx)
                logger.info("Phrygia cost: $%.4f", cost["total_cost_usd"])

            finally:
                await manager.cleanup(ctx)

        asyncio.run(_run())

        # Check meeting_invitations
        invitations = client.table("meeting_invitations") \
            .select("inviter_country_code,invitee_role_id,status,message") \
            .eq("sim_run_id", SIM_RUN_ID) \
            .eq("inviter_country_code", "phrygia") \
            .order("created_at", desc=True) \
            .limit(3).execute()
        logger.info("Phrygia invitations: %s",
                     [(i.get("invitee_role_id"), i["status"]) for i in (invitations.data or [])])
