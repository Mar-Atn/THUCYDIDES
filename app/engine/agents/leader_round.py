"""Leader Round Runner — single-agent-round flow using LeaderAgent + llm_tools.

This is the canonical Phase 2 bridge between:
  * the DESIGNED LeaderAgent (4-block cognitive model, DET_C1 interface)
  * the CALIBRATED tool-use loop (stage5_test's investigate → commit → reflect)
  * the DB persistence layer (agent_decisions, agent_memories)
  * the DUAL-PROVIDER LLM wrapper (llm_tools.call_tool_llm)

Replaces ``stage5_test.run_stage5_test`` as the canonical single-agent
round function. ``full_round_runner`` will be rewired to call this.

Cost model: one tool-use loop per agent per round (matches stage5 cost).
The designed multi-phase flow (budget/tariffs/sanctions × decide_action ×
conversations) is the target for a later phase; for now we keep the
single-commit loop to stay cost-controlled while upgrading the
cognitive foundation.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from typing import Any, Callable, Optional

from engine.agents import tools as agent_tools
from engine.agents.leader import LeaderAgent
from engine.agents.tool_schemas import (
    LOOKUP_TOOL_SCHEMAS,
    COMMIT_ACTION_SCHEMA,
    READ_MEMORY_SCHEMA,
    LIST_MY_MEMORIES_SCHEMA,
    WRITE_MEMORY_SCHEMA,
)
from engine.config.settings import LLMProvider, LLMUseCase, settings
from engine.services.llm_tools import call_tool_llm, serialize_assistant_content

logger = logging.getLogger(__name__)

MAX_TOOL_CALLS = 30   # Sprint B: more calls for multi-action rounds
MAX_TOKENS = 4000

TOOL_SCHEMAS = (
    LOOKUP_TOOL_SCHEMAS
    + [COMMIT_ACTION_SCHEMA]
    + [READ_MEMORY_SCHEMA, LIST_MY_MEMORIES_SCHEMA, WRITE_MEMORY_SCHEMA]
)

# Provider selection: env default, per-call override
_env_provider = os.environ.get("LLM_AGENT_PROVIDER", "").strip().lower()
DEFAULT_PROVIDER: Optional[LLMProvider] = (
    LLMProvider(_env_provider) if _env_provider in ("anthropic", "gemini") else None
)


# ---------------------------------------------------------------------------
# System prompt from LeaderAgent cognitive blocks
# ---------------------------------------------------------------------------

def build_system_prompt_from_leader(leader: LeaderAgent, round_num: int) -> str:
    """Assemble the system prompt from leader's 4 cognitive blocks.

    Block layout matches SEED_E5 4-block model:
      Block 1 — RULES (game mechanics, powers, actions)
      Block 2 — IDENTITY (character persona)
      Block 4 — GOALS (objectives + strategic plan)
      Block 3 — MEMORY (compressed highlights)
    """
    role = leader.role
    country = leader.country
    cog = leader.cognitive

    # Workflow preamble — orients agent for multi-action round (Sprint B)
    preamble = (
        f"It is Q1 2026, ROUND {round_num} of the simulation.\n\n"
        f"You are {role['character_name']}, {role['title']} of {country['sim_name']}. "
        f"You can commit UP TO 3 ACTIONS this round.\n\n"
        f"YOUR WORKFLOW:\n"
        f"1. list_my_memories() — read what you've noted in prior rounds (skip if round 1)\n"
        f"2. Investigate current situation using domain tools\n"
        f"3. Commit your PRIMARY action via commit_action (military, economic, diplomatic, covert, transaction)\n"
        f"4. Consider: is there a SECOND action worth taking? (public statement, covert op, transaction proposal, org meeting, another military move)\n"
        f"5. If yes — commit a second action. If not, proceed to step 6.\n"
        f"6. Consider a THIRD action if strategically valuable.\n"
        f"7. Update your memory via write_memory — record your strategic plan, observations, "
        f"relationship notes, and anything important for your future self.\n\n"
        f"IMPORTANT: Quality over quantity. One well-chosen action is better than three mediocre ones.\n"
        f"Use ONLY SIM names (never real-world names). Refer to other leaders by "
        f"their character names (Dealer, Helmsman, Pathfinder, Beacon, etc.).\n"
    )

    blocks = [
        preamble,
        "# BLOCK 1 — RULES (game mechanics, your powers, action space)\n" + (cog.block1_rules or "(empty)"),
        "# BLOCK 2 — IDENTITY (who you are)\n" + (cog.block2_identity or "(empty)"),
        "# BLOCK 4 — GOALS & STRATEGY\n" + cog.get_goals_text(),
        "# BLOCK 3 — MEMORY HIGHLIGHTS\n" + cog.get_memory_text(),
    ]
    return "\n\n".join(blocks)


# ---------------------------------------------------------------------------
# Tool dispatcher (reuses agents/tools.py + DB memory)
# ---------------------------------------------------------------------------

def _build_tool_dispatcher(
    country_code: str,
    scenario_code: str,
    round_num: int,
    commit_tracker: dict,
    memory_audit: list[dict],
) -> dict[str, Callable[[dict], Any]]:
    base = {
        "get_my_identity": lambda a: agent_tools.get_my_identity(country_code=country_code),
        "get_my_forces": lambda a: agent_tools.get_my_forces(
            country_code=country_code, scenario_code=scenario_code, round_num=round_num,
        ),
        "get_hex_info": lambda a: agent_tools.get_hex_info(
            row=a["row"], col=a["col"], scope=a.get("scope", "global"),
            scenario_code=scenario_code, round_num=round_num,
        ),
        "get_enemy_forces": lambda a: agent_tools.get_enemy_forces(
            country_code=country_code, enemy_country_code=a["enemy_country_code"],
            scenario_code=scenario_code, round_num=round_num,
        ),
        "get_strategic_context": lambda a: agent_tools.get_strategic_context(
            country_code=country_code, scenario_code=scenario_code, round_num=round_num,
        ),
        "get_economic_state": lambda a: agent_tools.get_economic_state(
            country_code=country_code, scenario_code=scenario_code, round_num=round_num,
        ),
        "get_political_state": lambda a: agent_tools.get_political_state(
            country_code=country_code, scenario_code=scenario_code, round_num=round_num,
        ),
        "get_tech_state": lambda a: agent_tools.get_tech_state(
            country_code=country_code, scenario_code=scenario_code, round_num=round_num,
        ),
        "get_template_info": lambda a: agent_tools.get_template_info(),
        "get_relationships": lambda a: agent_tools.get_relationships(
            country_code=country_code, scenario_code=scenario_code, round_num=round_num,
        ),
        "get_organization_memberships": lambda a: agent_tools.get_organization_memberships(country_code=country_code),
        "get_country_codes_list": lambda a: agent_tools.get_country_codes_list(),
    }

    MAX_COMMITS_PER_ROUND = 3  # Sprint B: agents can commit multiple actions

    def _commit(args: dict) -> dict:
        commits_so_far = commit_tracker.get("commit_count", 0)
        if commits_so_far >= MAX_COMMITS_PER_ROUND:
            return {
                "success": False,
                "validation_status": "rejected",
                "validation_notes": f"max {MAX_COMMITS_PER_ROUND} commits per round reached",
            }
        result = agent_tools.commit_action(
            country_code=country_code, scenario_code=scenario_code,
            action=args.get("action") or {}, round_num=round_num,
        )
        if result.get("success"):
            commit_tracker["commit_count"] = commits_so_far + 1
            commit_tracker["committed"] = True
            commit_tracker["result"] = result
            commit_tracker.setdefault("all_results", []).append(result)
        return result

    def _read_memory(args: dict) -> dict:
        key = args.get("memory_key", "")
        result = agent_tools.read_memory(
            country_code=country_code, scenario_code=scenario_code, memory_key=key,
        )
        memory_audit.append({"op": "read", "key": key, "exists": result.get("exists")})
        return result

    def _list_memories(args: dict) -> dict:
        result = agent_tools.list_my_memories(
            country_code=country_code, scenario_code=scenario_code,
        )
        memory_audit.append({"op": "list", "count": result.get("memory_count")})
        return result

    def _write_memory(args: dict) -> dict:
        key = args.get("memory_key", "")
        content = args.get("content", "")
        rnum = args.get("round_num") or round_num
        result = agent_tools.write_memory(
            country_code=country_code, scenario_code=scenario_code,
            memory_key=key, content=content, round_num=rnum,
        )
        memory_audit.append({
            "op": "write", "key": key, "len": len(content or ""), "success": result.get("success"),
        })
        return result

    base["commit_action"] = _commit
    base["read_memory"] = _read_memory
    base["list_my_memories"] = _list_memories
    base["write_memory"] = _write_memory
    return base


# ---------------------------------------------------------------------------
# Single-agent round runner
# ---------------------------------------------------------------------------

def _get_events_affecting_country(
    country_code: str, scenario_code: str, round_num: int,
) -> str:
    """Fetch events from the previous round that affected this country.

    Sprint B4: agents react to what happened to them. Returns a brief
    text summary injected into the agent's opening message.
    """
    if round_num <= 1:
        return ""  # no prior events in round 1
    prev_round = round_num - 1
    try:
        from engine.services.supabase import get_client
        from engine.services.sim_run_manager import resolve_sim_run_id
        client = get_client()
        try:
            sim_run_id = resolve_sim_run_id(scenario_code)
        except ValueError:
            return ""

        # Get events mentioning this country (as target or in payload)
        res = client.table("observatory_events") \
            .select("event_type, country_code, summary") \
            .eq("sim_run_id", sim_run_id) \
            .eq("round_num", prev_round) \
            .execute()

        relevant = []
        for ev in (res.data or []):
            summary = ev.get("summary", "")
            ev_country = ev.get("country_code", "")
            ev_type = ev.get("event_type", "")
            # Events BY others that mention this country
            if ev_country != country_code and country_code in summary.lower():
                relevant.append(f"• {summary}")
            # Combats where this country was attacked
            if ev_type in ("ground", "air", "missile", "naval_bombardment", "occupation"):
                if country_code in summary.lower() and ev_country != country_code:
                    relevant.append(f"• {summary}")
            # Sanctions/tariffs targeting this country
            if ev_type in ("set_sanction", "set_tariff") and country_code in summary.lower():
                relevant.append(f"• {summary}")
            # Bilateral conversations involving this country
            if ev_type == "bilateral_conversation" and country_code in summary.lower():
                relevant.append(f"• {summary}")

        if not relevant:
            return ""
        # Deduplicate and limit
        seen = set()
        unique = []
        for r in relevant:
            if r not in seen:
                seen.add(r)
                unique.append(r)
        return "\n".join(unique[:10])  # max 10 events
    except Exception as e:
        logger.warning("event fetch for %s failed: %s", country_code, e)
        return ""


def _resolve_role_id_by_country(country_code: str) -> Optional[str]:
    """Return the HoS role_id for a given country_code from the roles CSV."""
    from engine.agents.profiles import load_heads_of_state
    hos = load_heads_of_state()
    for rid, role in hos.items():
        if role.get("country_id") == country_code:
            return rid
    return None


async def run_leader_round(
    *,
    round_num: int,
    role_id: Optional[str] = None,
    country_code: Optional[str] = None,
    scenario_code: str = "start_one",
    provider: Optional[LLMProvider] = None,
    world_state: Optional[dict] = None,
) -> dict:
    """Run one leader agent's decision loop for one round.

    Pass EITHER ``role_id`` (UUID in roles table) OR ``country_code``
    (resolves to that country's head-of-state role).

    Returns a result dict with cognitive-state snapshot, tool calls,
    commit result, memory updates, and LLM metadata.
    """
    start = time.time()

    # Resolve role_id from country_code if needed
    if role_id is None:
        if not country_code:
            return {"error": "either role_id or country_code required", "committed": False}
        role_id = _resolve_role_id_by_country(country_code)
        if not role_id:
            return {"error": f"no HoS role found for country {country_code}", "committed": False}

    # 1. Initialize leader (sync — no LLM call for identity/goals at this stage)
    leader = LeaderAgent(role_id=role_id)
    leader.initialize_sync(world_state=world_state)

    country_code = leader.country.get("country_id") or leader.role.get("country_id")
    if not country_code:
        return {"error": f"role {role_id} has no country_id", "committed": False}

    # 2. Build system prompt from cognitive blocks
    system = build_system_prompt_from_leader(leader, round_num)

    # 3. Set up tool dispatcher
    commit_tracker: dict = {"committed": False, "result": None}
    memory_audit: list[dict] = []
    dispatcher = _build_tool_dispatcher(
        country_code=country_code, scenario_code=scenario_code,
        round_num=round_num, commit_tracker=commit_tracker,
        memory_audit=memory_audit,
    )

    # 4. Fetch events that affected this country last round (B4: event reactions)
    event_summary = _get_events_affecting_country(country_code, scenario_code, round_num)

    # 5. Run tool-use loop
    opening = (
        f"Begin Round {round_num}. Check your memory, investigate as needed, "
        f"commit your actions (up to 3), then update memory for next round."
    )
    if event_summary:
        opening += f"\n\nEVENTS THAT AFFECTED YOU SINCE LAST ROUND:\n{event_summary}"

    messages: list[dict] = [
        {"role": "user", "content": opening},
    ]
    tool_calls_made: list[dict] = []
    transcript: list[dict] = []
    final_text = ""
    model_used = ""
    provider_used = ""
    selected_provider = provider or DEFAULT_PROVIDER

    for iteration in range(MAX_TOOL_CALLS + 1):
        response = call_tool_llm(
            system=system, messages=messages, tools=TOOL_SCHEMAS,
            max_tokens=MAX_TOKENS, use_case=LLMUseCase.AGENT_DECISION,
            provider_override=selected_provider,
        )
        model_used = response.model
        provider_used = response.provider

        transcript.append({
            "iteration": iteration,
            "stop_reason": response.stop_reason,
            "provider": response.provider, "model": response.model,
            "content_blocks": [
                {"type": b.type, "text": b.text, "name": b.name, "input": b.input}
                for b in response.content
            ],
        })

        if response.stop_reason == "end_turn":
            final_text = "\n".join(
                b.text for b in response.content if b.type == "text" and b.text
            ).strip()
            break

        if response.stop_reason != "tool_use":
            logger.warning("[leader %s r%d] unexpected stop_reason=%s",
                           country_code, round_num, response.stop_reason)
            final_text = "\n".join(
                b.text for b in response.content if b.type == "text" and b.text
            ).strip()
            break

        messages.append({
            "role": "assistant",
            "content": serialize_assistant_content(response.content),
        })

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            tool_name = block.name or ""
            tool_input = block.input or {}
            logger.info("[leader %s r%d] tool_use: %s", country_code, round_num, tool_name)
            if tool_name not in dispatcher:
                result = {"error": f"Unknown tool: {tool_name}"}
            else:
                try:
                    result = dispatcher[tool_name](tool_input)
                except Exception as e:
                    logger.exception("Tool %s raised", tool_name)
                    result = {"error": str(e)}
            tool_calls_made.append({
                "iteration": iteration, "tool": tool_name,
                "input": tool_input if tool_name in (
                    "commit_action", "write_memory", "read_memory"
                ) else None,
            })
            tool_results.append({
                "type": "tool_result", "tool_use_id": block.id,
                "content": json.dumps(result, default=str),
            })
        messages.append({"role": "user", "content": tool_results})
    else:
        final_text = "(terminated: hit MAX_TOOL_CALLS safety bound)"

    return {
        "role_id": role_id,
        "country_code": country_code,
        "character_name": leader.role.get("character_name", ""),
        "title": leader.role.get("title", ""),
        "round_num": round_num,
        "model": model_used,
        "provider": provider_used,
        "duration_s": round(time.time() - start, 2),
        "tool_calls": tool_calls_made,
        "tool_call_count": len(tool_calls_made),
        "memory_audit": memory_audit,
        "memory_reads": sum(1 for m in memory_audit if m["op"] in ("read", "list")),
        "memory_writes": sum(1 for m in memory_audit if m["op"] == "write"),
        "committed": commit_tracker["committed"],
        "commit_result": commit_tracker["result"],
        "final_text": final_text,
        "transcript": transcript,
        "cognitive_snapshot": leader.get_cognitive_state(),
    }
