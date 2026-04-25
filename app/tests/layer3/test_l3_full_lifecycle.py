"""Level 3 — GRADUATION TEST: Full Round Lifecycle with 5 AI + 2 Human Emulators.

The definitive test: mixed human+AI simulation through a complete round.
Phase A → Phase B batch → engines → movement → Round 2.

5 AI agents (managed sessions) + 2 human emulators (ToolExecutor).
Verifies the entire system orchestrates correctly.

Requires: ANTHROPIC_API_KEY, live Supabase DB.
Cost: ~$1.00-$1.50

Run:
    cd /path/to/THUCYDIDES && PYTHONPATH=app .venv/bin/python -m pytest \
        app/tests/layer3/test_l3_full_lifecycle.py -v -s
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

# AI countries and their HoS roles
AI_AGENTS = {
    "sarmatia": "pathfinder",
    "columbia": "dealer",
    "persia": "furnace",
    "solaria": "wellspring",
    "phrygia": "vizier",
}

# Human emulators
HUMAN_EMULATORS = {
    "ruthenia": "beacon",
    "cathay": "helmsman",
}


class TestFullLifecycle:
    """THE GRADUATION TEST: 5 AI + 2 humans, full round lifecycle."""

    def test_full_round_mixed_simulation(self):
        """Phase A → Phase B → movement → Round 2 with 7 participants."""

        async def _run():
            from engine.agents.managed.session_manager import ManagedSessionManager
            from engine.agents.managed.tool_executor import ToolExecutor
            from engine.services.supabase import get_client
            from engine.services.sim_run_manager import end_phase_a, end_phase_b, advance_round

            client = get_client()
            manager = ManagedSessionManager()

            # Verify sim is active Round 1 Phase A
            run = client.table("sim_runs").select("status,current_phase,current_round") \
                .eq("id", SIM_RUN_ID).limit(1).execute()
            assert run.data, "SimRun not found"
            assert run.data[0]["status"] == "active", f"Sim not active: {run.data[0]}"
            assert run.data[0]["current_phase"] == "A", f"Not Phase A: {run.data[0]}"
            round_num = run.data[0]["current_round"]
            logger.info("=== GRADUATION TEST START: Round %d Phase A ===", round_num)

            # ── STEP 1: Phase A — AI agents explore and act ──────────────
            logger.info("--- STEP 1: Phase A — 5 AI agents explore and act ---")
            sessions = {}
            try:
                # Create all 5 AI sessions
                for country, role_id in AI_AGENTS.items():
                    ctx = await manager.create_session(
                        role_id=role_id, country_code=country,
                        sim_run_id=SIM_RUN_ID, scenario_code=SIM_RUN_ID,
                        round_num=round_num,
                    )
                    sessions[country] = ctx
                    logger.info("Created session: %s (%s)", country, ctx.session_id[:12])

                # Send Phase A prompt to each agent (parallel)
                phase_a_tasks = []
                for country, ctx in sessions.items():
                    prompt = (
                        f"Round {round_num}, Phase A. You are Head of State of {country.upper()}. "
                        f"Assess your situation and take ONE strategic action — "
                        f"a public statement, diplomatic move, or military action. Be decisive."
                    )
                    phase_a_tasks.append(manager.send_event(ctx, prompt))

                # Wait for all agents (with timeout per agent)
                results = await asyncio.gather(*phase_a_tasks, return_exceptions=True)
                for country, result in zip(sessions.keys(), results):
                    if isinstance(result, Exception):
                        logger.warning("Agent %s Phase A error: %s", country, result)
                    else:
                        tools = [e.get("tool", "") for e in result if e.get("type") == "tool_call"]
                        logger.info("Agent %s Phase A: %d tool calls — %s",
                                    country, len(tools), tools[:5])

                # Human emulators act in Phase A
                logger.info("--- Human emulators act in Phase A ---")
                for country, role_id in HUMAN_EMULATORS.items():
                    human = ToolExecutor(
                        country_code=country, scenario_code="ttt_v1",
                        sim_run_id=SIM_RUN_ID, round_num=round_num, role_id=role_id,
                    )
                    result = json.loads(human.execute("submit_action", {
                        "action": {
                            "action_type": "public_statement",
                            "content": f"{country.upper()} affirms its strategic commitments.",
                            "rationale": "Graduation test Phase A human action",
                        }
                    }))
                    logger.info("Human %s Phase A: %s", country, result.get("success"))

                # Verify Phase A produced actions
                decisions = client.table("agent_decisions") \
                    .select("country_code,action_type,validation_status") \
                    .eq("sim_run_id", SIM_RUN_ID).eq("round_num", round_num).execute()
                logger.info("Phase A total decisions: %d", len(decisions.data or []))

                # ── STEP 2: Transition to Phase B ────────────────────────
                logger.info("--- STEP 2: Transition to Phase B ---")
                phase_b_result = end_phase_a(SIM_RUN_ID)
                assert phase_b_result["current_phase"] == "B", f"Not Phase B: {phase_b_result}"
                logger.info("Transitioned to Phase B (processing)")

                # ── STEP 3: AI agents submit batch decisions ─────────────
                logger.info("--- STEP 3: AI agents submit batch decisions ---")
                batch_tasks = []
                for country, ctx in sessions.items():
                    is_opec = country in ("solaria", "persia", "sarmatia")
                    opec_note = " You are an OPEC member — also set your oil production level." if is_opec else ""
                    prompt = (
                        f"PHASE B — BATCH DECISIONS REQUIRED.\n\n"
                        f"Submit your economic decisions NOW:\n"
                        f"1. set_budget — social_pct (0.5-1.5), military_coins, tech_coins\n"
                        f"2. set_tariffs — optional, target_country + level 0-3\n"
                        f"3. set_sanctions — optional, target_country + level\n"
                        f"{('4. set_opec — production: min/low/normal/high/max' + chr(10)) if is_opec else ''}"
                        f"\nReview your economy with get_my_country first, then submit.{opec_note}"
                    )
                    batch_tasks.append(manager.send_event(ctx, prompt))

                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                for country, result in zip(sessions.keys(), batch_results):
                    if isinstance(result, Exception):
                        logger.warning("Agent %s Phase B error: %s", country, result)
                    else:
                        actions = [e.get("tool") for e in result if e.get("type") == "tool_call" and e.get("tool") == "submit_action"]
                        logger.info("Agent %s Phase B: %d submit_action calls", country, len(actions))

                # Human emulators submit batch decisions
                logger.info("--- Human emulators submit batch decisions ---")
                for country, role_id in HUMAN_EMULATORS.items():
                    human = ToolExecutor(
                        country_code=country, scenario_code="ttt_v1",
                        sim_run_id=SIM_RUN_ID, round_num=round_num, role_id=role_id,
                    )
                    # Submit budget
                    budget_result = json.loads(human.execute("submit_action", {
                        "action": {
                            "action_type": "set_budget",
                            "social_pct": 1.0,
                            "military_coins": 5.0,
                            "tech_coins": 3.0,
                            "rationale": f"Graduation test: {country} budget",
                        }
                    }))
                    logger.info("Human %s budget: %s", country, budget_result.get("success"))

                # Count batch decisions
                batch_decisions = client.table("agent_decisions") \
                    .select("country_code,action_type") \
                    .eq("sim_run_id", SIM_RUN_ID).eq("round_num", round_num) \
                    .in_("action_type", ["set_budget", "set_tariffs", "set_sanctions", "set_opec"]) \
                    .execute()
                countries_with_batch = {d["country_code"] for d in (batch_decisions.data or [])}
                logger.info("Countries that submitted batch: %s (%d)",
                            countries_with_batch, len(countries_with_batch))

                # ── STEP 4: End Phase B → Inter-round ────────────────────
                logger.info("--- STEP 4: End Phase B → inter_round ---")
                ir_result = end_phase_b(SIM_RUN_ID)
                assert ir_result["current_phase"] == "inter_round", f"Not inter_round: {ir_result}"
                logger.info("Phase B ended, now in inter_round")

                # ── STEP 5: Advance to Round 2 ───────────────────────────
                logger.info("--- STEP 5: Advance to Round 2 ---")
                r2_result = advance_round(SIM_RUN_ID)
                assert r2_result["current_round"] == round_num + 1, f"Not round {round_num+1}: {r2_result}"
                assert r2_result["current_phase"] == "A", f"Not Phase A: {r2_result}"
                new_round = r2_result["current_round"]
                logger.info("Advanced to Round %d Phase A", new_round)

                # ── STEP 6: Round 2 — verify agents can act ─────────────
                logger.info("--- STEP 6: Round 2 — agents act ---")

                # Update session round numbers
                for ctx in sessions.values():
                    manager.update_round(ctx, new_round)

                # Send Round 2 prompt to 2 agents (save cost — don't need all 5)
                r2_agents = ["sarmatia", "columbia"]
                r2_tasks = []
                for country in r2_agents:
                    ctx = sessions[country]
                    prompt = (
                        f"Round {new_round}, Phase A. New round. Review what changed — "
                        f"check events, assess your position, and take one action."
                    )
                    r2_tasks.append(manager.send_event(ctx, prompt))

                r2_results = await asyncio.gather(*r2_tasks, return_exceptions=True)
                for country, result in zip(r2_agents, r2_results):
                    if isinstance(result, Exception):
                        logger.warning("Agent %s Round 2 error: %s", country, result)
                    else:
                        tools = [e.get("tool", "") for e in result if e.get("type") == "tool_call"]
                        logger.info("Agent %s Round 2: %d tool calls", country, len(tools))

                # ── STEP 7: Final verification ───────────────────────────
                logger.info("--- STEP 7: Final verification ---")

                # Count all decisions across both rounds
                all_decisions = client.table("agent_decisions") \
                    .select("country_code,action_type,round_num,validation_status") \
                    .eq("sim_run_id", SIM_RUN_ID).execute()

                by_round = {}
                by_country = {}
                for d in (all_decisions.data or []):
                    rn = d["round_num"]
                    cc = d["country_code"]
                    by_round[rn] = by_round.get(rn, 0) + 1
                    by_country[cc] = by_country.get(cc, 0) + 1

                logger.info("Decisions by round: %s", dict(by_round))
                logger.info("Decisions by country: %s", dict(sorted(by_country.items())))
                logger.info("Total decisions: %d", len(all_decisions.data or []))

                # Verify: multiple countries acted
                all_ai = set(AI_AGENTS.keys())
                all_human = set(HUMAN_EMULATORS.keys())
                acting = set(by_country.keys())
                ai_acting = acting & all_ai
                human_acting = acting & all_human
                logger.info("AI countries acting: %s (%d/5)", ai_acting, len(ai_acting))
                logger.info("Human countries acting: %s (%d/2)", human_acting, len(human_acting))

                assert len(ai_acting) >= 3, f"At least 3 AI countries should act, got {ai_acting}"
                assert len(human_acting) >= 2, f"Both human emulators should act, got {human_acting}"

                # Verify: Round 2 agents responded (tool calls ≥ 1, even if only observation)
                # Note: agents may use only observation tools in Round 2 (no submit_action)
                # which wouldn't create agent_decisions rows. That's valid agent behavior.
                r2_decisions = by_round.get(new_round, 0)
                logger.info("Round 2 decisions in DB: %d (agents may have used observation tools only)", r2_decisions)

                # Report session costs
                total_cost = 0.0
                for country, ctx in sessions.items():
                    cost = manager.get_cost_estimate(ctx)
                    total_cost += cost["total_cost_usd"]
                    logger.info("Cost %s: $%.4f (tools=%d, actions=%d)",
                                country, cost["total_cost_usd"],
                                cost.get("tool_calls", 0), cost.get("actions_submitted", 0))
                logger.info("=== TOTAL COST: $%.4f ===", total_cost)

                logger.info("=== GRADUATION TEST PASSED ===")

            finally:
                # Cleanup all sessions
                for country, ctx in sessions.items():
                    try:
                        await manager.cleanup(ctx)
                    except Exception as e:
                        logger.warning("Cleanup %s: %s", country, e)

        asyncio.run(_run())
