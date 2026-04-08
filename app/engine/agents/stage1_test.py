# DEPRECATED (2026-04-06) — replaced by agents/leader_round.py (uses LeaderAgent + llm_tools)
# Kept for reference. Do not add new logic here.
"""Stage 1: Model Literacy Test.

A thin Anthropic tool-use orchestrator. The AI participant is given five
lookup tools (see ``tools.py``) and asked to describe its country's
military posture in its own words. No decisions, no actions — pure data
literacy.

Each test:
  1. Builds a persona-based system prompt (character + title + country).
  2. Exposes 5 tools to Claude (country_code bound as closure).
  3. Loops tool_use -> tool_result until the model emits end_turn.
  4. Captures transcript + final textual assessment + tool call log.

Usage:
    python -m engine.agents.stage1_test          # runs all 5 agents
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Any, Callable

from anthropic import Anthropic

from engine.agents import tools as agent_tools
from engine.config.settings import settings

logger = logging.getLogger(__name__)

# Model: latest Sonnet. See app/config/LLM_MODELS.md
MODEL_ID = "claude-sonnet-4-20250514"  # Sonnet 4.6 — see app/config/LLM_MODELS.md
MAX_TOOL_CALLS = 10
MAX_TOKENS = 2048

RESULTS_DIR = Path(__file__).resolve().parent / "stage1_results"


# ---------------------------------------------------------------------------
# Country roster for tests
# ---------------------------------------------------------------------------

AGENTS = [
    {"country_code": "columbia", "character_name": "Dealer", "title": "President",
     "country_name": "Columbia", "country_parallel": "United States"},
    {"country_code": "sarmatia", "character_name": "Kremlin", "title": "President",
     "country_name": "Sarmatia", "country_parallel": "Russia"},
    {"country_code": "persia", "character_name": "Supreme Leader", "title": "Supreme Leader",
     "country_name": "Persia", "country_parallel": "Iran"},
    {"country_code": "cathay", "character_name": "Helmsman", "title": "President",
     "country_name": "Cathay", "country_parallel": "China"},
    {"country_code": "levantia", "character_name": "Steel", "title": "Prime Minister",
     "country_name": "Levantia", "country_parallel": "Israel"},
]


# ---------------------------------------------------------------------------
# Tool schemas exposed to Claude
# ---------------------------------------------------------------------------

TOOL_SCHEMAS = [
    {
        "name": "get_my_forces",
        "description": (
            "Returns your country's complete force disposition: every unit "
            "with its type, status (active/reserve/embarked), location "
            "(global hex or theater cell), and notes. Call this first to "
            "understand what you have."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_hex_info",
        "description": (
            "Returns information about a specific hex: which units are "
            "present, whether it is a theater-link hex. Scope is either "
            "'global' (1..10 rows x 1..20 cols) or a theater name "
            "('eastern_ereb' or 'mashriq', both 1..10 x 1..10)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "row": {"type": "integer", "description": "1-indexed row"},
                "col": {"type": "integer", "description": "1-indexed column"},
                "scope": {"type": "string", "description": "'global', 'eastern_ereb', or 'mashriq'"},
            },
            "required": ["row", "col", "scope"],
        },
    },
    {
        "name": "get_enemy_forces",
        "description": (
            "Returns observable (active + embarked) forces of another "
            "country. Reserves are NOT visible. Use country codes like "
            "'persia', 'sarmatia', 'cathay', 'ruthenia', etc."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "enemy_country_code": {"type": "string", "description": "Country code of the target (lowercase)"},
            },
            "required": ["enemy_country_code"],
        },
    },
    {
        "name": "get_strategic_context",
        "description": (
            "Returns your strategic context: regime type, GDP, treasury, "
            "stability, war tiredness, who you are at war with, and total "
            "military strength by domain."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_template_info",
        "description": (
            "Returns scenario-level metadata: allowed theaters, round "
            "counts, and the catalog of international organizations "
            "(NATO, BRICS, OPEC, UNSC, EREB_UNION)."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
]


def _build_tool_dispatcher(country_code: str) -> dict[str, Callable[[dict], Any]]:
    """Bind country_code as closure, so the LLM cannot spoof identity."""
    return {
        "get_my_forces": lambda args: agent_tools.get_my_forces(country_code=country_code),
        "get_hex_info": lambda args: agent_tools.get_hex_info(
            row=args["row"], col=args["col"], scope=args.get("scope", "global"),
        ),
        "get_enemy_forces": lambda args: agent_tools.get_enemy_forces(
            country_code=country_code, enemy_country_code=args["enemy_country_code"],
        ),
        "get_strategic_context": lambda args: agent_tools.get_strategic_context(country_code=country_code),
        "get_template_info": lambda args: agent_tools.get_template_info(),
    }


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT_TEMPLATE = """You are {character_name}, {title} of {country_name} ({country_parallel}).

It is Q1 2026. You are assessing your country's current military situation.

Use the available tools to gather what you need. Do not guess or assume — query the data.

When you have enough information, summarize your country's military posture in YOUR OWN WORDS (not as a data dump):
- What forces do you have, and where are they deployed?
- What are the key strategic features of your current situation?
- What vulnerabilities or strengths do you notice?
- Who are your adversaries, and how are you positioned vs them?

Keep your assessment concise (150-300 words). Be specific. Reference actual units and locations.

No decisions or actions required — just DESCRIBE WHAT YOU SEE."""


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

async def run_stage1_test(
    country_code: str,
    character_name: str,
    title: str,
    country_name: str,
    country_parallel: str,
) -> dict:
    """Run Stage 1 literacy test for one country."""
    start = time.time()
    client = Anthropic(api_key=settings.anthropic_api_key)
    dispatcher = _build_tool_dispatcher(country_code)

    system = SYSTEM_PROMPT_TEMPLATE.format(
        character_name=character_name,
        title=title,
        country_name=country_name,
        country_parallel=country_parallel,
    )

    messages: list[dict] = [
        {"role": "user", "content": "Assess your military posture. Use the tools as needed."},
    ]

    tool_calls_made: list[dict] = []
    final_text = ""
    transcript: list[dict] = []

    for iteration in range(MAX_TOOL_CALLS + 1):
        response = client.messages.create(
            model=MODEL_ID,
            max_tokens=MAX_TOKENS,
            system=system,
            tools=TOOL_SCHEMAS,
            messages=messages,
        )

        # Record turn
        transcript.append({
            "iteration": iteration,
            "stop_reason": response.stop_reason,
            "content_blocks": [
                {"type": b.type, "text": getattr(b, "text", None),
                 "name": getattr(b, "name", None),
                 "input": getattr(b, "input", None)}
                for b in response.content
            ],
        })

        if response.stop_reason == "end_turn":
            # Concatenate any text blocks
            text_parts = [b.text for b in response.content if b.type == "text"]
            final_text = "\n".join(text_parts).strip()
            break

        if response.stop_reason != "tool_use":
            logger.warning("Unexpected stop_reason=%s", response.stop_reason)
            text_parts = [b.text for b in response.content if b.type == "text"]
            final_text = "\n".join(text_parts).strip()
            break

        # Append assistant turn to message history
        messages.append({"role": "assistant", "content": response.content})

        # Execute each tool_use block, collect results
        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            tool_name = block.name
            tool_input = block.input or {}
            logger.info("[%s] tool_use: %s(%s)", country_code, tool_name, tool_input)

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
                "input": tool_input,
                "result_summary": _summarize_result(result),
            })
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(result, default=str),
            })

        messages.append({"role": "user", "content": tool_results})
    else:
        # Loop fell through without end_turn
        final_text = "(terminated: hit MAX_TOOL_CALLS safety bound)"

    return {
        "country": country_code,
        "character_name": character_name,
        "title": title,
        "model": MODEL_ID,
        "duration_s": round(time.time() - start, 2),
        "tool_calls_made": tool_calls_made,
        "tool_call_count": len(tool_calls_made),
        "final_assessment": final_text,
        "transcript": transcript,
    }


def _summarize_result(result: dict) -> dict:
    """Trim a tool result to a summary safe to persist without huge JSON."""
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
        else:
            summary[k] = v
    return summary


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

async def run_all() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    summary_rows = []
    for agent in AGENTS:
        print(f"\n=== Running {agent['country_code']} ({agent['character_name']}) ===")
        result = await run_stage1_test(**agent)

        out_path = RESULTS_DIR / f"{agent['country_code']}.json"
        with out_path.open("w") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"  saved -> {out_path.name}")
        print(f"  tool calls: {result['tool_call_count']} | duration: {result['duration_s']}s")
        print(f"  assessment preview: {result['final_assessment'][:200]}...")
        summary_rows.append({
            "country": result["country"],
            "tool_calls": result["tool_call_count"],
            "duration_s": result["duration_s"],
            "chars": len(result["final_assessment"]),
        })

    print("\n=== Summary ===")
    for r in summary_rows:
        print(f"  {r['country']:10s} calls={r['tool_calls']:2d} duration={r['duration_s']:5.1f}s chars={r['chars']}")


if __name__ == "__main__":
    asyncio.run(run_all())
