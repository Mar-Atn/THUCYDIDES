# DEPRECATED (2026-04-06) — replaced by agents/leader_round.py (uses LeaderAgent + llm_tools)
# Kept for reference. Do not add new logic here.
"""Stage 5: Single-Round Closed Loop with Persistent Memory.

Adds 3 memory tools (read_memory, list_my_memories, write_memory) on top of
Stage 4. Each agent begins a round by reading prior memory, then investigates,
commits ONE action, then WRITES reflections for next round.

The orchestrator runs two sequential rounds against the same 5 agents. Round 1
starts with no memory; Round 2 should reference and build on Round 1 memory.

Usage:
    cd app && PYTHONPATH=. python3 -m engine.agents.stage5_test
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Any, Callable

from engine.agents import tools as agent_tools
from engine.agents.stage2_test import load_hos_agents
from engine.agents.stage3_test import TOOL_SCHEMAS as STAGE3_TOOL_SCHEMAS
from engine.agents.stage4_test import COMMIT_ACTION_SCHEMA
from engine.config.settings import LLMProvider, LLMUseCase, settings
from engine.services.llm_tools import call_tool_llm, serialize_assistant_content

logger = logging.getLogger(__name__)

# Provider selection: honor env LLM_AGENT_PROVIDER (anthropic|gemini) or
# fall back to the AGENT_DECISION use-case default from settings.
# Can also be set per-call via run_stage5_test(provider=...).
import os
_env_provider = os.environ.get("LLM_AGENT_PROVIDER", "").strip().lower()
DEFAULT_PROVIDER: LLMProvider | None = (
    LLMProvider(_env_provider) if _env_provider in ("anthropic", "gemini") else None
)
MAX_TOOL_CALLS = 20
MAX_TOKENS = 4000
SCENARIO_CODE = "start_one"

RESULTS_DIR = Path(__file__).resolve().parent / "stage5_results"
COUNTRY_CODES = ["columbia", "sarmatia", "persia", "cathay", "levantia"]


# ---------------------------------------------------------------------------
# Memory tool schemas
# ---------------------------------------------------------------------------

MEMORY_KEYS_HINT = (
    "Suggested keys: 'strategic_plan' (active multi-round plan with stages), "
    "'observations' (journal of what happened / what you learned), "
    "'relationships' (per-country trust/tension notes), "
    "'lessons_learned' (what worked / didn't), "
    "'open_threads' (unresolved situations to track). "
    "You may create additional keys freely."
)

READ_MEMORY_SCHEMA = {
    "name": "read_memory",
    "description": (
        "Read one of your persistent memory entries written in a previous "
        "round. Returns {exists, content, round_num, updated_at}. "
        f"{MEMORY_KEYS_HINT}"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "memory_key": {"type": "string", "description": "Key of the memory to read."},
        },
        "required": ["memory_key"],
    },
}

LIST_MY_MEMORIES_SCHEMA = {
    "name": "list_my_memories",
    "description": (
        "List every memory key you have written, with round_num, updated_at, "
        "and a 200-char preview of each. Call this FIRST to see what prior "
        "thinking you can build on."
    ),
    "input_schema": {"type": "object", "properties": {}, "required": []},
}

WRITE_MEMORY_SCHEMA = {
    "name": "write_memory",
    "description": (
        "UPSERT a persistent memory entry keyed by memory_key. Overwrites "
        "any existing content for that key. Call this AFTER commit_action, "
        "to reflect on this round and leave notes for your future self in "
        f"the next round. {MEMORY_KEYS_HINT}"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "memory_key": {"type": "string", "description": "Key under which to store."},
            "content": {
                "type": "string",
                "description": "Free-form markdown/text content. Be specific and concrete.",
            },
            "round_num": {
                "type": "integer",
                "description": "Round number during which this memory is being written.",
            },
        },
        "required": ["memory_key", "content", "round_num"],
    },
}

TOOL_SCHEMAS = (
    STAGE3_TOOL_SCHEMAS
    + [COMMIT_ACTION_SCHEMA]
    + [READ_MEMORY_SCHEMA, LIST_MY_MEMORIES_SCHEMA, WRITE_MEMORY_SCHEMA]
)


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

def _build_tool_dispatcher(
    country_code: str,
    commit_tracker: dict,
    memory_audit: list[dict],
    round_num: int = 1,
) -> dict[str, Callable[[dict], Any]]:
    base = {
        "get_my_identity": lambda args: agent_tools.get_my_identity(country_code=country_code),
        "get_my_forces": lambda args: agent_tools.get_my_forces(country_code=country_code),
        "get_hex_info": lambda args: agent_tools.get_hex_info(
            row=args["row"], col=args["col"], scope=args.get("scope", "global"),
        ),
        "get_enemy_forces": lambda args: agent_tools.get_enemy_forces(
            country_code=country_code, enemy_country_code=args["enemy_country_code"],
        ),
        "get_strategic_context": lambda args: agent_tools.get_strategic_context(country_code=country_code),
        "get_economic_state": lambda args: agent_tools.get_economic_state(country_code=country_code),
        "get_political_state": lambda args: agent_tools.get_political_state(country_code=country_code),
        "get_tech_state": lambda args: agent_tools.get_tech_state(country_code=country_code),
        "get_template_info": lambda args: agent_tools.get_template_info(),
        "get_relationships": lambda args: agent_tools.get_relationships(country_code=country_code),
        "get_organization_memberships": lambda args: agent_tools.get_organization_memberships(country_code=country_code),
        "get_country_codes_list": lambda args: agent_tools.get_country_codes_list(),
    }

    def _commit(args: dict) -> dict:
        if commit_tracker.get("committed"):
            return {
                "success": False,
                "validation_status": "rejected",
                "validation_notes": "action already committed this round — only ONE commit allowed",
            }
        result = agent_tools.commit_action(
            country_code=country_code,
            scenario_code=SCENARIO_CODE,
            action=args.get("action") or {},
            round_num=round_num,
        )
        if result.get("success"):
            commit_tracker["committed"] = True
            commit_tracker["result"] = result
        return result

    def _read_memory(args: dict) -> dict:
        key = args.get("memory_key", "")
        result = agent_tools.read_memory(
            country_code=country_code,
            scenario_code=SCENARIO_CODE,
            memory_key=key,
        )
        memory_audit.append({
            "op": "read",
            "memory_key": key,
            "exists": result.get("exists"),
            "round_num": result.get("round_num"),
        })
        return result

    def _list_memories(args: dict) -> dict:
        result = agent_tools.list_my_memories(
            country_code=country_code,
            scenario_code=SCENARIO_CODE,
        )
        memory_audit.append({
            "op": "list",
            "count": result.get("memory_count"),
        })
        return result

    def _write_memory(args: dict) -> dict:
        key = args.get("memory_key", "")
        content = args.get("content", "")
        rnum = args.get("round_num")
        result = agent_tools.write_memory(
            country_code=country_code,
            scenario_code=SCENARIO_CODE,
            memory_key=key,
            content=content,
            round_num=rnum,
        )
        memory_audit.append({
            "op": "write",
            "memory_key": key,
            "round_num": rnum,
            "content_len": len(content or ""),
            "success": result.get("success"),
        })
        return result

    base["commit_action"] = _commit
    base["read_memory"] = _read_memory
    base["list_my_memories"] = _list_memories
    base["write_memory"] = _write_memory
    return base


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT_TEMPLATE = """You are {character_name}, {title}.

It is Q1 2026, ROUND {round_num} of the simulation.

BEFORE reasoning, CHECK YOUR MEMORY. You may have written plans, observations, or lessons from prior rounds. Read them FIRST to maintain continuity.

Tools available:
- list_my_memories() -- see what you've written before
- read_memory(memory_key) -- read a specific memory entry
- Domain tools: get_my_identity, get_my_forces, get_enemy_forces, get_hex_info, get_strategic_context, get_economic_state, get_political_state, get_tech_state, get_relationships, get_organization_memberships, get_template_info, get_country_codes_list
- commit_action(action) -- commit your ONE action for this round
- write_memory(memory_key, content, round_num) -- UPDATE your memory for next round

YOUR WORKFLOW:
1. list_my_memories() and read any relevant prior memories
2. Investigate current situation using domain tools (as needed)
3. Assess whether your prior plan (if any) still holds, or needs adjustment
4. COMMIT your primary action for this round via commit_action
5. WRITE reflections to memory for next round:
   - Update 'strategic_plan' with current stage + next intended stage
   - Update 'observations' with what you noticed this round
   - Create/update other memory keys as useful (relationships, lessons_learned, open_threads, ...)

Remember: in Round 1 you have no memory yet. In Round 2+ you SHOULD reference and build on what you wrote previously. Your strategic plan should span multiple rounds (e.g., "Round 1: position forces. Round 2: deliver ultimatum. Round 3: strike if refused").

You have ONE commit this round. Choose carefully, and leave clear notes for your future self."""


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

async def run_stage5_test(
    country_code: str,
    character_name: str,
    title: str,
    round_num: int,
    provider: LLMProvider | None = None,
) -> dict:
    start = time.time()
    commit_tracker: dict = {"committed": False, "result": None}
    memory_audit: list[dict] = []
    dispatcher = _build_tool_dispatcher(country_code, commit_tracker, memory_audit, round_num=round_num)

    system = SYSTEM_PROMPT_TEMPLATE.format(
        character_name=character_name, title=title, round_num=round_num,
    )

    messages: list[dict] = [
        {"role": "user", "content": (
            f"Begin Round {round_num}. Start by checking your memory "
            f"(list_my_memories), then investigate, commit your action, "
            f"then update your memory for next round."
        )},
    ]

    tool_calls_made: list[dict] = []
    final_text = ""
    transcript: list[dict] = []
    model_used = ""
    provider_used = ""
    selected_provider = provider or DEFAULT_PROVIDER

    for iteration in range(MAX_TOOL_CALLS + 1):
        response = call_tool_llm(
            system=system,
            messages=messages,
            tools=TOOL_SCHEMAS,
            max_tokens=MAX_TOKENS,
            use_case=LLMUseCase.AGENT_DECISION,
            provider_override=selected_provider,
        )
        model_used = response.model
        provider_used = response.provider

        transcript.append({
            "iteration": iteration,
            "stop_reason": response.stop_reason,
            "provider": response.provider,
            "model": response.model,
            "content_blocks": [
                {"type": b.type, "text": b.text, "name": b.name, "input": b.input}
                for b in response.content
            ],
        })

        if response.stop_reason == "end_turn":
            text_parts = [b.text for b in response.content if b.type == "text" and b.text]
            final_text = "\n".join(text_parts).strip()
            break

        if response.stop_reason != "tool_use":
            logger.warning("Unexpected stop_reason=%s", response.stop_reason)
            text_parts = [b.text for b in response.content if b.type == "text" and b.text]
            final_text = "\n".join(text_parts).strip()
            break

        messages.append({"role": "assistant", "content": serialize_assistant_content(response.content)})

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            tool_name = block.name or ""
            tool_input = block.input or {}
            logger.info("[%s r%d] tool_use: %s", country_code, round_num, tool_name)

            if tool_name not in dispatcher:
                result = {"error": f"Unknown tool: {tool_name}"}
            else:
                try:
                    result = dispatcher[tool_name](tool_input)
                except Exception as e:
                    logger.exception("Tool %s raised", tool_name)
                    result = {"error": str(e)}

            tool_calls_made.append({
                "iteration": iteration,
                "tool": tool_name,
                "input": tool_input if tool_name in ("commit_action", "write_memory", "read_memory") else None,
                "result_summary": _summarize_result(result),
            })
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(result, default=str),
            })

        messages.append({"role": "user", "content": tool_results})
    else:
        final_text = "(terminated: hit MAX_TOOL_CALLS safety bound)"

    return {
        "country": country_code,
        "character_name": character_name,
        "title": title,
        "round_num": round_num,
        "model": model_used,
        "provider": provider_used,
        "duration_s": round(time.time() - start, 2),
        "tool_calls_made": tool_calls_made,
        "tool_call_count": len(tool_calls_made),
        "memory_audit": memory_audit,
        "memory_reads": sum(1 for m in memory_audit if m["op"] in ("read", "list")),
        "memory_writes": sum(1 for m in memory_audit if m["op"] == "write"),
        "committed": commit_tracker["committed"],
        "commit_result": commit_tracker["result"],
        "final_text": final_text,
        "transcript": transcript,
    }


def _summarize_result(result: dict) -> dict:
    if not isinstance(result, dict):
        return {"raw": str(result)[:200]}
    if "error" in result:
        return {"error": result["error"]}
    summary: dict[str, Any] = {}
    for k, v in result.items():
        if isinstance(v, list):
            summary[k] = f"list[{len(v)}]"
        elif isinstance(v, dict):
            summary[k] = f"dict[{len(v)} keys]"
        elif isinstance(v, str) and len(v) > 120:
            summary[k] = v[:120] + "..."
        else:
            summary[k] = v
    return summary


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

async def run_round(round_num: int, agents: list[dict]) -> list[dict]:
    round_dir = RESULTS_DIR / f"round_{round_num}"
    round_dir.mkdir(parents=True, exist_ok=True)

    summary_rows = []
    for agent in agents:
        print(f"\n--- R{round_num} {agent['country_code']} "
              f"({agent['character_name']}, {agent['title']}) ---")
        result = await run_stage5_test(
            country_code=agent["country_code"],
            character_name=agent["character_name"],
            title=agent["title"],
            round_num=round_num,
        )
        out_path = round_dir / f"{agent['country_code']}.json"
        with out_path.open("w") as f:
            json.dump(result, f, indent=2, default=str)
        cr = result.get("commit_result") or {}
        print(f"  saved -> {out_path.name}")
        print(f"  tool calls: {result['tool_call_count']} | "
              f"mem reads: {result['memory_reads']} | "
              f"mem writes: {result['memory_writes']} | "
              f"duration: {result['duration_s']}s")
        print(f"  committed: {result['committed']} | "
              f"type: {cr.get('action_type')} | "
              f"status: {cr.get('validation_status')}")
        summary_rows.append({
            "country": result["country"],
            "round": round_num,
            "committed": result["committed"],
            "action_type": cr.get("action_type"),
            "mem_reads": result["memory_reads"],
            "mem_writes": result["memory_writes"],
            "tool_calls": result["tool_call_count"],
            "duration_s": result["duration_s"],
        })
    return summary_rows


async def run_all() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    agents = load_hos_agents(COUNTRY_CODES)
    if not agents:
        print("ERROR: no HoS agents loaded from DB")
        return
    loaded_codes = {a["country_code"] for a in agents}
    missing = [c for c in COUNTRY_CODES if c not in loaded_codes]
    if missing:
        print(f"WARNING: no HoS role found in DB for: {missing}")

    print(f"\n========== ROUND 1 ==========")
    r1_summary = await run_round(1, agents)

    print(f"\n========== ROUND 2 ==========")
    r2_summary = await run_round(2, agents)

    print("\n=== Summary ===")
    for r in r1_summary + r2_summary:
        print(
            f"  R{r['round']} {r['country']:10s} committed={r['committed']!s:5s} "
            f"type={str(r['action_type'] or '-'):20s} "
            f"reads={r['mem_reads']:2d} writes={r['mem_writes']:2d} "
            f"calls={r['tool_calls']:2d} duration={r['duration_s']:5.1f}s"
        )


if __name__ == "__main__":
    asyncio.run(run_all())
