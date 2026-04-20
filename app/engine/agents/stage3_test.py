# DEPRECATED (2026-04-06) — replaced by agents/leader_round.py (uses LeaderAgent + llm_tools)
# Kept for reference. Do not add new logic here.
"""Stage 3: Strategic Integration Test.

Agents receive all 8 Stage-2 lookup tools PLUS 3 new domain tools
(economic, political, tech) PLUS get_my_identity. They must reason ACROSS
all four domains (military, economic, political, technology) and decide
WHETHER military action is appropriate this round — or whether non-military
tools serve better.

This exposes whether the agent can correctly DECLINE military escalation
when domestic/economic/political constraints dominate.

Usage:
    cd app && PYTHONPATH=. python3 -m engine.agents.stage3_test
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
from engine.agents.stage2_test import load_hos_agents
from engine.config.settings import settings

logger = logging.getLogger(__name__)

# Model: latest Sonnet. See app/config/LLM_MODELS.md
MODEL_ID = "claude-sonnet-4-20250514"  # Sonnet 4.6
MAX_TOOL_CALLS = 16
MAX_TOKENS = 3500

RESULTS_DIR = Path(__file__).resolve().parent / "stage3_results"

COUNTRY_CODES = ["columbia", "sarmatia", "persia", "cathay", "levantia"]

# Country display names for the system prompt (parallel real-world analogs).
COUNTRY_META = {
    "columbia": {"country_name": "Columbia", "country_parallel": "United States"},
    "sarmatia": {"country_name": "Sarmatia", "country_parallel": "Russia"},
    "persia":   {"country_name": "Persia",   "country_parallel": "Iran"},
    "cathay":   {"country_name": "Cathay",   "country_parallel": "China"},
    "levantia": {"country_name": "Levantia", "country_parallel": "Israel"},
}


# ---------------------------------------------------------------------------
# Tool schemas (11 total: 8 from Stage 2 + 3 new domain + identity)
# ---------------------------------------------------------------------------

_VALID_CODES_HINT = (
    "Valid country codes are: columbia, cathay, sarmatia, ruthenia, persia, "
    "gallia, teutonia, freeland, ponte, albion, bharata, levantia, formosa, "
    "phrygia, yamato, solaria, choson, hanguk, caribe, mirage. Call "
    "get_country_codes_list first if unsure."
)

TOOL_SCHEMAS = [
    {
        "name": "get_my_identity",
        "description": (
            "Returns your canonical identity: character_name, title, "
            "real-world parallel, objectives, and powers "
            "(time pressure). Call this first to understand WHO you are "
            "and what you care about."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_my_forces",
        "description": (
            "Returns your country's complete force disposition: every unit "
            "with type, status, location."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_hex_info",
        "description": (
            "Returns info about a specific hex. Scope is 'global' "
            "(1..10 x 1..20) or a theater name ('eastern_ereb' or "
            "'mashriq', both 1..10 x 1..10)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "row": {"type": "integer"},
                "col": {"type": "integer"},
                "scope": {"type": "string"},
            },
            "required": ["row", "col", "scope"],
        },
    },
    {
        "name": "get_enemy_forces",
        "description": (
            "Returns observable (active+embarked) forces of another country. "
            + _VALID_CODES_HINT
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "enemy_country_code": {"type": "string"},
            },
            "required": ["enemy_country_code"],
        },
    },
    {
        "name": "get_strategic_context",
        "description": (
            "Returns your strategic snapshot: regime type, GDP, treasury, "
            "stability, war tiredness, who you are at war with, military "
            "totals by domain, nuclear level."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_economic_state",
        "description": (
            "Returns your ECONOMIC state with risk annotations: gdp, "
            "treasury, inflation, trade_balance, debt_burden, tax_rate, "
            "sector breakdown, oil production, OPEC membership, Formosa "
            "(Taiwan semiconductor) dependency. Returns annotations like "
            "'hyperinflation risk' or 'treasury near-empty'."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_political_state",
        "description": (
            "Returns your POLITICAL state with annotations: stability "
            "(1-10), political_support (0-100%), war_tiredness (0-10), "
            "regime_type, team structure. Flags 'fragile', 'war-weary', "
            "'leader vulnerable' when thresholds are crossed."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_tech_state",
        "description": (
            "Returns your TECHNOLOGICAL state: nuclear_level (0-3), "
            "nuclear R&D progress, ai_level (0-4), ai R&D progress, "
            "strategic missile growth. Flags 'strategic nuclear power' "
            "and 'tech leader' annotations."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_template_info",
        "description": (
            "Returns scenario metadata: theaters, round counts, organizations."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_relationships",
        "description": (
            "Returns your bilateral relationships: who you are at war with "
            "and who is at war with you."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_organization_memberships",
        "description": (
            "Returns international organizations you belong to plus the "
            "full catalog (UNSC, NATO, BRICS, OPEC, EREB_UNION)."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_country_codes_list",
        "description": (
            "Returns authoritative list of valid country codes with SIM "
            "names and real-world parallels."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
]


def _build_tool_dispatcher(country_code: str) -> dict[str, Callable[[dict], Any]]:
    """Bind country_code as closure so the LLM cannot spoof identity."""
    return {
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


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT_TEMPLATE = """You are {character_name}, {title}.

It is Q1 2026. You are assessing what your country should do THIS ROUND.

You have FOUR domains of action: MILITARY, ECONOMIC, POLITICAL, TECHNOLOGICAL.
Military action is ONE option — not always the right one. Often economic pressure, diplomatic maneuvering, or strategic patience serves better.

Use the available tools to understand your situation across all four domains.

DELIVER your analysis in this format:

## SITUATION ACROSS 4 DOMAINS
- MILITARY: [brief: key military facts]
- ECONOMIC: [brief: GDP, treasury, inflation, key constraints]
- POLITICAL: [brief: stability, support, war tiredness]
- TECHNOLOGICAL: [brief: nuclear/AI levels, trajectory]

## SHOULD YOU ACT MILITARILY THIS ROUND?
[YES / NO / CONDITIONAL] — with 2-3 sentences of reasoning grounded in ALL four domains, not just military.

## RECOMMENDED PRIMARY ACTION (whichever domain)
[Specific proposed action in the most-appropriate domain. If military: name units + destination. If economic: specify sanctions/tariffs. If political: specify diplomatic move. If tech: specify R&D investment.]

## SECONDARY SUPPORTING ACTIONS
[2 backup actions in different domains that reinforce the primary]

## WHAT YOU WILL NOT DO (and why)
[1-2 actions you deliberately REJECT this round, with reasoning]"""


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

async def run_stage3_test(
    country_code: str,
    character_name: str,
    title: str,
) -> dict:
    """Run Stage 3 cross-domain strategic test for one country."""
    start = time.time()
    client = Anthropic(api_key=settings.anthropic_api_key)
    dispatcher = _build_tool_dispatcher(country_code)

    system = SYSTEM_PROMPT_TEMPLATE.format(
        character_name=character_name,
        title=title,
    )

    messages: list[dict] = [
        {"role": "user", "content": (
            "Assess your situation across all four domains and deliver your "
            "round-1 action plan using the format in your instructions. "
            "Use the tools as needed."
        )},
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
            text_parts = [b.text for b in response.content if b.type == "text"]
            final_text = "\n".join(text_parts).strip()
            break

        if response.stop_reason != "tool_use":
            logger.warning("Unexpected stop_reason=%s", response.stop_reason)
            text_parts = [b.text for b in response.content if b.type == "text"]
            final_text = "\n".join(text_parts).strip()
            break

        messages.append({"role": "assistant", "content": response.content})

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

    agents = load_hos_agents(COUNTRY_CODES)
    if not agents:
        print("ERROR: no HoS agents loaded from DB")
        return
    loaded_codes = {a["country_code"] for a in agents}
    missing = [c for c in COUNTRY_CODES if c not in loaded_codes]
    if missing:
        print(f"WARNING: no HoS role found in DB for: {missing}")

    summary_rows = []
    for agent in agents:
        print(f"\n=== Running {agent['country_code']} ({agent['character_name']}, {agent['title']}) ===")
        result = await run_stage3_test(
            country_code=agent["country_code"],
            character_name=agent["character_name"],
            title=agent["title"],
        )

        out_path = RESULTS_DIR / f"{agent['country_code']}.json"
        with out_path.open("w") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"  saved -> {out_path.name}")
        print(f"  tool calls: {result['tool_call_count']} | duration: {result['duration_s']}s")
        print(f"  assessment preview: {result['final_assessment'][:280]}...")
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
