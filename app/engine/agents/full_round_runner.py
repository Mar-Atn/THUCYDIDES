"""Full Round Runner — 20 HoS agents in parallel.

Runs all 20 Head-of-State agents concurrently for a single round, each
executing Stage-5 style logic (read memory, investigate, commit ONE action,
reflect). After all 20 have committed (or timed-out / failed), hands off to
the round resolver for combat/movement/economy resolution.

Design notes:
  * Uses ``asyncio.gather(..., return_exceptions=True)`` — a single agent
    crash never fails the whole batch.
  * Uses an ``asyncio.Semaphore(MAX_CONCURRENCY)`` to stay under Anthropic
    rate limits (10 concurrent by default).
  * Each agent has a 90s hard timeout.
  * Anthropic SDK is sync, so each agent runs inside ``asyncio.to_thread``
    — that gives true parallel I/O across agents.
  * On HTTP 429 / rate-limit errors from Anthropic, retry with exponential
    backoff (5s, 10s, 20s — max 3 attempts).

Usage:
    from engine.agents.full_round_runner import run_full_round, run_auto_advance
    await run_full_round("start_one", round_num=1)
    await run_auto_advance("start_one", max_rounds=6, delay_s=15)
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Any

from engine.agents.stage2_test import load_hos_agents
from engine.agents.leader_round import run_leader_round
from engine.config.map_config import COUNTRY_CODES as ALL_COUNTRY_CODES

logger = logging.getLogger(__name__)


def _emit_event(scenario_code: str, round_num: int, event_type: str, country_code: str | None, summary: str, payload: dict | None = None) -> None:
    """Insert a row into observatory_events table (fire-and-forget)."""
    try:
        from engine.services.supabase import get_client
        client = get_client()
        scen = client.table("sim_scenarios").select("id").eq("code", scenario_code).limit(1).execute()
        if not scen.data:
            return
        client.table("observatory_events").insert({
            "scenario_id": scen.data[0]["id"],
            "round_num": round_num,
            "event_type": event_type,
            "country_code": country_code,
            "summary": summary,
            "payload": payload or {},
        }).execute()
    except Exception as e:
        logger.debug("_emit_event failed: %s", e)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SCENARIO_CODE_DEFAULT = "start_one"
MAX_CONCURRENCY = 10           # Anthropic rate-limit safety
PER_AGENT_TIMEOUT_S = 90.0     # hard ceiling per agent
MAX_RETRIES_ON_429 = 3
BACKOFF_BASE_S = 5.0           # 5s, 10s, 20s

RESULTS_DIR = Path(__file__).resolve().parent / "full_round_results"


# ---------------------------------------------------------------------------
# Single-agent runner with retry + timeout
# ---------------------------------------------------------------------------

# Shared stop flag — observatory server sets this to True to halt all agents
_GLOBAL_STOP = False


def set_global_stop(val: bool = True):
    global _GLOBAL_STOP
    _GLOBAL_STOP = val


async def _run_one_agent(
    agent: dict,
    round_num: int,
    semaphore: asyncio.Semaphore,
) -> dict:
    """Run one agent's Stage-5 loop with timeout, retry on 429, semaphore.

    Returns a summary dict (never raises). On fatal failure, the summary
    contains ``error`` and ``committed=False``.
    """
    cc = agent["country_code"]
    name = agent["character_name"]
    title = agent["title"]
    started = time.time()

    async with semaphore:
        # Check global stop BEFORE starting this agent
        if _GLOBAL_STOP:
            return {
                "country_code": cc, "character_name": name, "title": title,
                "committed": False, "action_type": None, "validation_status": None,
                "duration_s": 0, "tool_calls": 0, "memory_reads": 0, "memory_writes": 0,
                "full_result": None, "error": "stopped by user",
            }
        attempt = 0
        last_err: Exception | None = None
        while attempt <= MAX_RETRIES_ON_429:
            attempt += 1
            try:
                logger.info(
                    "[R%d %s] start (attempt %d/%d)",
                    round_num, cc, attempt, MAX_RETRIES_ON_429 + 1,
                )
                if attempt == 1:
                    _emit_event(SCENARIO_CODE_DEFAULT, round_num, "agent_started", cc, f"{name} ({cc}) reasoning...")
                # run the sync Anthropic client inside a thread to get
                # true I/O-parallelism across agents.
                result = await asyncio.wait_for(
                    asyncio.to_thread(
                        _run_leader_sync,
                        cc, name, title, round_num,
                    ),
                    timeout=PER_AGENT_TIMEOUT_S,
                )
                cr = result.get("commit_result") or {}
                logger.info(
                    "[R%d %s] done: committed=%s type=%s duration=%.1fs calls=%d",
                    round_num, cc, result.get("committed"),
                    cr.get("action_type"), result.get("duration_s", 0),
                    result.get("tool_call_count", 0),
                )
                action_type = cr.get("action_type") or "none"
                if result.get("committed"):
                    _emit_event(SCENARIO_CODE_DEFAULT, round_num, "agent_committed", cc, f"{name} committed {action_type}")
                else:
                    _emit_event(SCENARIO_CODE_DEFAULT, round_num, "agent_no_commit", cc, f"{name} failed to commit")
                return {
                    "country_code": cc,
                    "character_name": name,
                    "title": title,
                    "committed": bool(result.get("committed")),
                    "action_type": cr.get("action_type"),
                    "validation_status": cr.get("validation_status"),
                    "duration_s": result.get("duration_s"),
                    "tool_calls": result.get("tool_call_count"),
                    "memory_reads": result.get("memory_reads"),
                    "memory_writes": result.get("memory_writes"),
                    "full_result": result,
                    "error": None,
                }

            except asyncio.TimeoutError:
                last_err = TimeoutError(
                    f"agent exceeded {PER_AGENT_TIMEOUT_S}s timeout")
                logger.warning("[R%d %s] TIMEOUT after %.1fs",
                               round_num, cc, PER_AGENT_TIMEOUT_S)
                break  # do not retry on timeout

            except Exception as e:  # noqa: BLE001
                last_err = e
                msg = str(e).lower()
                is_rate_limit = (
                    "429" in msg or "rate" in msg or "overloaded" in msg
                    or "rate_limit" in msg
                )
                if is_rate_limit and attempt <= MAX_RETRIES_ON_429:
                    backoff = BACKOFF_BASE_S * (2 ** (attempt - 1))
                    logger.warning(
                        "[R%d %s] rate-limit (attempt %d): %s -- backoff %.1fs",
                        round_num, cc, attempt, e, backoff,
                    )
                    await asyncio.sleep(backoff)
                    continue
                logger.exception("[R%d %s] fatal error", round_num, cc)
                break

    return {
        "country_code": cc,
        "character_name": name,
        "title": title,
        "committed": False,
        "action_type": None,
        "validation_status": None,
        "duration_s": round(time.time() - started, 2),
        "tool_calls": 0,
        "memory_reads": 0,
        "memory_writes": 0,
        "full_result": None,
        "error": f"{type(last_err).__name__}: {last_err}" if last_err else "unknown",
    }


def _run_leader_sync(cc: str, name: str, title: str, round_num: int) -> dict:
    """Thin bridge: run the async ``run_leader_round`` from a worker thread.

    The async function performs blocking LLM I/O under the hood. Wrapping
    it in its own event loop inside a worker thread gives clean parallelism.

    (Migrated 2026-04-06 — replaces stage5_test.run_stage5_test as part
    of the Architectural Reunification Sprint. See
    ``3 DETAILED DESIGN/REUNIFICATION_AUDIT_2026-04-06.md`` Phase 2.)
    """
    return asyncio.run(
        run_leader_round(
            country_code=cc,
            round_num=round_num,
        )
    )


# ---------------------------------------------------------------------------
# Round resolver handoff (graceful if resolver not yet built)
# ---------------------------------------------------------------------------

def _try_run_conversations(
    scenario_code: str, round_num: int,
    hos_agents: list[dict], agent_results: list[dict],
) -> list[dict]:
    """Run bilateral conversations between agents who should talk.

    Sprint B2: After agents commit their primary actions, identify
    strategically relevant pairs and run 8-turn bilateral conversations.

    Pairing logic:
    - Agents who targeted each other (attacks, sanctions, transactions)
    - Countries at war (peace talks potential)
    - Agents who proposed transactions (need counterpart response)
    Max 3 conversations per round (cost control).
    """
    MAX_CONVERSATIONS = 3

    # Find conversation pairs from agent decisions
    pairs = _identify_conversation_pairs(agent_results, hos_agents, MAX_CONVERSATIONS)
    if not pairs:
        logger.info("[R%d] no conversation pairs identified", round_num)
        return []

    results = []
    for agent_a_info, agent_b_info, topic in pairs:
        if _GLOBAL_STOP:
            break
        try:
            logger.info("[R%d] bilateral: %s <-> %s (%s)",
                        round_num, agent_a_info["country_code"],
                        agent_b_info["country_code"], topic)
            result = asyncio.run(_run_one_conversation(
                agent_a_info, agent_b_info, round_num, topic))
            results.append(result)
            # Persist transcript to observatory_events
            try:
                from engine.services.supabase import get_client
                client = get_client()
                scen = client.table("sim_scenarios").select("id").eq("code", scenario_code).limit(1).execute()
                if scen.data:
                    client.table("observatory_events").insert({
                        "scenario_id": scen.data[0]["id"],
                        "round_num": round_num,
                        "event_type": "bilateral_conversation",
                        "country_code": agent_a_info["country_code"],
                        "summary": f"💬 {agent_a_info['character_name']} ↔ {agent_b_info['character_name']}: "
                                   f"{result.get('turns', 0)} turns — {topic}",
                        "payload": {
                            "participants": [agent_a_info["country_code"], agent_b_info["country_code"]],
                            "topic": topic,
                            "turns": result.get("turns", 0),
                            "ended_by": result.get("ended_by"),
                        },
                    }).execute()
            except Exception:
                pass  # fire-and-forget
        except Exception as e:
            logger.warning("[R%d] conversation %s<->%s failed: %s",
                           round_num, agent_a_info["country_code"],
                           agent_b_info["country_code"], e)
    return results


def _identify_conversation_pairs(
    agent_results: list[dict], hos_agents: list[dict], max_pairs: int,
) -> list[tuple[dict, dict, str]]:
    """Identify which agents should talk based on their committed actions."""
    agent_by_cc = {a["country_code"]: a for a in hos_agents}
    pairs: list[tuple[dict, dict, str]] = []
    seen = set()

    for r in agent_results:
        if not r.get("committed"):
            continue
        cc = r.get("country_code", "")
        fr = r.get("full_result") or {}

        # Check each tool call for targeting another country
        for tc in (fr.get("tool_calls") or fr.get("tool_calls_made") or []):
            inp = tc.get("input") or {}
            action = inp.get("action") or {}
            target = (action.get("counterpart_country") or
                      action.get("target_country") or "")
            action_type = action.get("action_type", "")

            if target and target in agent_by_cc and target != cc:
                pair_key = tuple(sorted([cc, target]))
                if pair_key not in seen:
                    seen.add(pair_key)
                    topic = f"{action_type} from {cc}"
                    pairs.append((agent_by_cc[cc], agent_by_cc[target], topic))
                    if len(pairs) >= max_pairs:
                        return pairs

    return pairs


async def _run_one_conversation(
    agent_a_info: dict, agent_b_info: dict, round_num: int, topic: str,
) -> dict:
    """Run one bilateral conversation + transaction flow between two agents.

    After conversation + reflection:
    1. Persists memory updates to agent_memories (Sprint B3)
    2. If conversation was triggered by a transaction proposal, runs the
       designed transaction flow: propose → evaluate → execute (Sprint B/transactions)
       Uses `agents/transactions.run_transaction_flow()` — the designed module.
    """
    from engine.agents.leader import LeaderAgent
    from engine.agents.conversations import ConversationEngine
    from engine.agents import tools as agent_tools

    # Initialize both leaders
    leader_a = LeaderAgent(role_id=_resolve_role_id(agent_a_info["country_code"]))
    leader_a.initialize_sync()
    leader_b = LeaderAgent(role_id=_resolve_role_id(agent_b_info["country_code"]))
    leader_b.initialize_sync()

    engine = ConversationEngine()
    result = await engine.run_bilateral(leader_a, leader_b, max_turns=8, topic=topic)

    # If this conversation was triggered by a transaction proposal,
    # run the designed transaction flow (propose → evaluate → execute)
    transaction_result = None
    if "propose_transaction" in topic:
        try:
            from engine.agents.transactions import run_transaction_flow
            txn_type = None  # let the LLM decide based on conversation context
            if "arms" in topic.lower():
                txn_type = "arms_sale"
            elif "tech" in topic.lower():
                txn_type = "tech_transfer"
            elif "coin" in topic.lower():
                txn_type = "coin_transfer"
            elif "basing" in topic.lower():
                txn_type = "basing_rights"

            proposal = await run_transaction_flow(
                proposer_agent=leader_a,
                counterpart_agent=leader_b,
                world_state={},  # simplified — full world_state wiring in Sprint C
                countries={
                    agent_a_info["country_code"]: leader_a.country,
                    agent_b_info["country_code"]: leader_b.country,
                },
                transaction_type=txn_type,
            )
            transaction_result = {
                "id": proposal.id,
                "type": proposal.type,
                "status": proposal.status,  # accepted | rejected | countered
                "terms": proposal.terms,
                "reasoning": proposal.reasoning,
                "evaluation": proposal.evaluation_reasoning,
            }
            logger.info("[R%d] Transaction %s: %s → %s = %s",
                        round_num, proposal.type,
                        agent_a_info["country_code"],
                        agent_b_info["country_code"],
                        proposal.status)
        except Exception as e:
            logger.warning("Transaction flow failed: %s", e)
            transaction_result = {"error": str(e)}

    # Persist conversation reflections to agent_memories (Sprint B3)
    for leader, info in [(leader_a, agent_a_info), (leader_b, agent_b_info)]:
        cc = info["country_code"]
        reflection = result.reflections.get(leader.role_id, {})
        details = reflection.get("details", {})
        memory_update = details.get("memory_update")
        if memory_update:
            try:
                # Write conversation summary to persistent memory
                existing = agent_tools.read_memory(
                    country_code=cc, scenario_code="start_one",
                    memory_key="conversations",
                )
                prev = existing.get("content", "") if existing.get("exists") else ""
                new_content = (
                    f"{prev}\n\n[R{round_num}] Bilateral with "
                    f"{agent_b_info['character_name'] if cc == agent_a_info['country_code'] else agent_a_info['character_name']}: "
                    f"{memory_update}"
                ).strip()
                agent_tools.write_memory(
                    country_code=cc, scenario_code="start_one",
                    memory_key="conversations", content=new_content,
                    round_num=round_num,
                )
                # Also persist relationship assessment
                rel_change = details.get("relationship_change", 0)
                if abs(rel_change) > 0.05:
                    rel_existing = agent_tools.read_memory(
                        country_code=cc, scenario_code="start_one",
                        memory_key="relationships",
                    )
                    rel_prev = rel_existing.get("content", "") if rel_existing.get("exists") else ""
                    counterpart_name = agent_b_info['character_name'] if cc == agent_a_info['country_code'] else agent_a_info['character_name']
                    rel_new = (
                        f"{rel_prev}\n[R{round_num}] {counterpart_name}: trust {rel_change:+.1f}"
                    ).strip()
                    agent_tools.write_memory(
                        country_code=cc, scenario_code="start_one",
                        memory_key="relationships", content=rel_new,
                        round_num=round_num,
                    )
            except Exception as e:
                logger.warning("conversation memory persist failed for %s: %s", cc, e)

    # Persist transaction result to DB if executed
    if transaction_result and transaction_result.get("status") == "accepted":
        try:
            from engine.services.supabase import get_client
            client = get_client()
            scen = client.table("sim_scenarios").select("id").eq("code", "start_one").limit(1).execute()
            if scen.data:
                client.table("exchange_transactions").insert({
                    "scenario_id": scen.data[0]["id"],
                    "round_num": round_num,
                    "proposer": agent_a_info["country_code"],
                    "counterpart": agent_b_info["country_code"],
                    "offer": transaction_result.get("terms", {}).get("gives", {}),
                    "request": transaction_result.get("terms", {}).get("receives", {}),
                    "status": "executed",
                }).execute()
                _emit_event("start_one", round_num, "transaction_executed", agent_a_info["country_code"],
                           f"💰 {agent_a_info['country_code']} ↔ {agent_b_info['country_code']}: "
                           f"{transaction_result.get('type', '?')} executed",
                           transaction_result)
        except Exception as e:
            logger.warning("transaction DB persist failed: %s", e)

    return {
        "participants": [agent_a_info["country_code"], agent_b_info["country_code"]],
        "topic": topic,
        "turns": result.turns,
        "ended_by": result.ended_by,
        "transcript": result.transcript,
        "reflections": {k: v.get("details", {}) for k, v in result.reflections.items()},
        "transaction": transaction_result,
    }


def _resolve_role_id(country_code: str) -> str:
    """Get HoS role_id for a country_code."""
    from engine.agents.profiles import load_heads_of_state
    hos = load_heads_of_state()
    for rid, role in hos.items():
        if role.get("country_id") == country_code:
            return rid
    return ""


def _try_engine_tick(scenario_code: str, round_num: int) -> dict:
    """Run the economic + political engine tick after combat resolution.

    Graceful fallback if engines not available.
    """
    try:
        from engine.engines.round_tick import run_engine_tick
    except ImportError:
        logger.warning("round_tick.run_engine_tick not available — skipping engine tick")
        return {"success": False, "reason": "round_tick not available"}
    try:
        logger.info("[R%d] running engine tick...", round_num)
        result = run_engine_tick(scenario_code, round_num)
        logger.info("[R%d] engine tick: %s", round_num, result)
        return result
    except Exception as e:
        logger.exception("[R%d] engine tick failed", round_num)
        return {"success": False, "reason": f"{type(e).__name__}: {e}"}


def _try_resolve_round(scenario_code: str, round_num: int) -> dict:
    """Call resolve_round from round_engine if available.

    The round_engine package is built in Sub-Sprint B of the Observatory.
    While it is missing this function is a no-op returning
    ``{"resolved": False, "reason": "round_engine not available"}``.
    """
    try:
        from engine.round_engine import resolve_round  # type: ignore
    except ImportError:
        logger.warning(
            "round_engine.resolve_round not available — skipping resolution phase"
        )
        return {"resolved": False, "reason": "round_engine not available"}

    try:
        logger.info("[R%d] handing off to resolve_round...", round_num)
        result = resolve_round(scenario_code, round_num)
        return {"resolved": True, "result": result}
    except Exception as e:  # noqa: BLE001
        logger.exception("[R%d] resolve_round failed", round_num)
        return {"resolved": False, "reason": f"{type(e).__name__}: {e}"}


# ---------------------------------------------------------------------------
# Full round runner
# ---------------------------------------------------------------------------

async def run_full_round(
    scenario_code: str,
    round_num: int,
    country_codes: list[str] | None = None,
) -> dict:
    """Run all HoS agents (default: all 20) in parallel for one round.

    Args:
        scenario_code: DB scenario code, e.g. ``"start_one"``.
        round_num: integer round number (>=1).
        country_codes: override for testing with a subset. Default = all 20.

    Returns a summary dict::

        {
          "round_num", "scenario_code",
          "agents": [{country_code, character_name, committed,
                      action_type, duration_s, tool_calls, ...}, ...],
          "total_duration_s", "successes", "failures",
          "resolution": {...},
        }
    """
    codes = country_codes or list(ALL_COUNTRY_CODES)
    round_started = time.time()

    _emit_event(SCENARIO_CODE_DEFAULT, round_num, "round_started", None, f"🌍 Round {round_num} started — mobilizing {len(codes)} agents")
    logger.info("[R%d] loading %d HoS agents from DB...", round_num, len(codes))
    hos_agents = load_hos_agents(codes)
    loaded_codes = {a["country_code"] for a in hos_agents}
    missing = [c for c in codes if c not in loaded_codes]
    if missing:
        logger.warning("[R%d] no HoS role found for: %s", round_num, missing)
    logger.info("[R%d] launching %d agents in parallel (max %d concurrent)...",
                round_num, len(hos_agents), MAX_CONCURRENCY)

    semaphore = asyncio.Semaphore(MAX_CONCURRENCY)
    tasks = [
        _run_one_agent(agent, round_num, semaphore)
        for agent in hos_agents
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # normalize: asyncio.gather(return_exceptions=True) can still surface
    # unexpected exceptions if our inner catch missed anything.
    normalized: list[dict] = []
    for agent, res in zip(hos_agents, results):
        if isinstance(res, BaseException):
            logger.error("[R%d %s] uncaught exception: %s",
                         round_num, agent["country_code"], res)
            normalized.append({
                "country_code": agent["country_code"],
                "character_name": agent["character_name"],
                "title": agent["title"],
                "committed": False,
                "action_type": None,
                "validation_status": None,
                "duration_s": None,
                "tool_calls": 0,
                "memory_reads": 0,
                "memory_writes": 0,
                "full_result": None,
                "error": f"{type(res).__name__}: {res}",
            })
        else:
            normalized.append(res)

    total_duration = round(time.time() - round_started, 2)
    successes = sum(1 for r in normalized if r.get("committed"))
    failures = len(normalized) - successes

    logger.info(
        "[R%d] agent phase complete: %d/%d committed, total %.1fs",
        round_num, successes, len(normalized), total_duration,
    )
    _emit_event(SCENARIO_CODE_DEFAULT, round_num, "round_resolving", None, f"⚙ Round {round_num}: {successes}/{len(normalized)} agents committed, resolving actions...")

    # ---- CONVERSATION PHASE (Sprint B2) ----
    try:
        conversation_results = await asyncio.to_thread(
            _try_run_conversations, scenario_code, round_num, hos_agents, normalized)
        if conversation_results:
            _emit_event(SCENARIO_CODE_DEFAULT, round_num, "conversations_complete", None,
                        f"💬 {len(conversation_results)} bilateral conversations completed")
    except Exception as e:
        logger.warning("[R%d] conversation phase failed: %s", round_num, e)

    # ---- handoff to round resolver (combat, movement, trophies) ----
    resolution = await asyncio.to_thread(
        _try_resolve_round, scenario_code, round_num)

    # ---- engine tick: economic + political + technology ----
    engine_tick = await asyncio.to_thread(
        _try_engine_tick, scenario_code, round_num)

    res_result = (resolution or {}).get("result") or {}
    combats = res_result.get("combats", 0)
    tick_oil = (engine_tick or {}).get("oil_price", "?")
    _emit_event(SCENARIO_CODE_DEFAULT, round_num, "round_completed", None,
                f"✅ Round {round_num} complete — {combats} combats, "
                f"{res_result.get('decisions_processed', 0)} actions resolved, "
                f"engine tick: oil=${tick_oil}")

    summary = {
        "round_num": round_num,
        "scenario_code": scenario_code,
        "agents": normalized,
        "total_duration_s": total_duration,
        "successes": successes,
        "failures": failures,
        "resolution": resolution,
        "engine_tick": engine_tick,
    }

    # write snapshot for later inspection
    try:
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        snapshot_path = RESULTS_DIR / f"round_{round_num:02d}_summary.json"
        with snapshot_path.open("w") as f:
            json.dump(_strip_transcripts(summary), f, indent=2, default=str)
        logger.info("[R%d] summary saved -> %s", round_num, snapshot_path.name)
    except Exception:  # noqa: BLE001
        logger.exception("[R%d] failed to write snapshot", round_num)

    return summary


def _strip_transcripts(summary: dict) -> dict:
    """Produce a lightweight copy of the summary for on-disk snapshots.

    Full agent transcripts live in the stage5_results tree already, so the
    round-level snapshot keeps only compact per-agent stats.
    """
    compact = dict(summary)
    compact["agents"] = [
        {k: v for k, v in a.items() if k != "full_result"}
        for a in summary.get("agents", [])
    ]
    return compact


# ---------------------------------------------------------------------------
# Auto-advance loop (pause/resume aware)
# ---------------------------------------------------------------------------

async def run_auto_advance(
    scenario_code: str,
    max_rounds: int = 6,
    delay_s: int = 15,
    pause_event: asyncio.Event | None = None,
    start_round: int = 1,
) -> list[dict]:
    """Run rounds sequentially with an auto-advance delay.

    Args:
        scenario_code: DB scenario code.
        max_rounds: inclusive upper bound on round numbers to run.
        delay_s: seconds to sleep between rounds.
        pause_event: optional ``asyncio.Event``. When the event is CLEARED
            the loop pauses (waits for it to be SET). When None, the loop
            never pauses.
        start_round: first round number to run (default 1).

    Returns the list of per-round summary dicts.
    """
    summaries: list[dict] = []
    for round_num in range(start_round, max_rounds + 1):
        # honor pause signal BEFORE starting the round
        if pause_event is not None and not pause_event.is_set():
            logger.info("[auto-advance] paused — waiting for resume...")
            await pause_event.wait()
            logger.info("[auto-advance] resumed")

        logger.info("[auto-advance] ====== starting round %d/%d ======",
                    round_num, max_rounds)
        summary = await run_full_round(scenario_code, round_num)
        summaries.append(summary)

        # honor pause again mid-loop, and skip the delay if we're done
        if round_num >= max_rounds:
            break
        if pause_event is not None and not pause_event.is_set():
            logger.info("[auto-advance] paused after round %d", round_num)
            await pause_event.wait()
            logger.info("[auto-advance] resumed")

        logger.info("[auto-advance] sleeping %ds before round %d",
                    delay_s, round_num + 1)
        await asyncio.sleep(delay_s)

    return summaries
