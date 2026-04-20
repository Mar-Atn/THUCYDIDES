# DEPRECATED (2026-04-06) — replaced by agents/leader_round.py (uses LeaderAgent + llm_tools)
# Kept for reference. Do not add new logic here.
"""Stage 2: Objective Setting Test.

Agents receive ALL 8 lookup tools (5 original + 3 new: relationships,
organization memberships, country codes list) and are asked to produce
3 TOP MILITARY PRIORITIES for the round, with reasoning and specific
unit/hex-level actions.

This is the first test that requires DECISION-MAKING, not just data
recall. It exposes gaps in strategic coherence across what the agent
learns from the tools.

Usage:
    cd app && PYTHONPATH=. python3 -m engine.agents.stage2_test
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
from engine.services.supabase import get_client


def load_hos_agents(country_codes: list[str]) -> list[dict]:
    """Load canonical HoS character data from DB for given countries.

    Returns a list of dicts keyed by country_code with character_name and title
    pulled from the ``roles`` table. This replaces hardcoded identity data.
    """
    client = get_client()
    result = (
        client.table("roles")
        .select("country_code, character_name, title")
        .eq("is_head_of_state", True)
        .in_("country_code", country_codes)
        .execute()
    )
    # dedup by country_code (first match wins)
    seen: dict[str, dict] = {}
    for r in result.data or []:
        cid = r["country_code"]
        if cid not in seen:
            seen[cid] = {
                "country_code": cid,
                "character_name": r["character_name"],
                "title": r["title"],
            }
    return [seen[c] for c in country_codes if c in seen]

logger = logging.getLogger(__name__)

# Model: latest Sonnet. See app/config/LLM_MODELS.md
MODEL_ID = "claude-sonnet-4-20250514"  # Sonnet 4.6
MAX_TOOL_CALLS = 14
MAX_TOKENS = 3072

RESULTS_DIR = Path(__file__).resolve().parent / "stage2_results"


# ---------------------------------------------------------------------------
# Country roster (same 5 countries as Stage 1 for direct comparison)
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
# Tool schemas exposed to Claude (8 total)
# ---------------------------------------------------------------------------

_VALID_CODES_HINT = (
    "Valid country codes are: columbia, cathay, sarmatia, ruthenia, persia, "
    "gallia, teutonia, freeland, ponte, albion, bharata, levantia, formosa, "
    "phrygia, yamato, solaria, choson, hanguk, caribe, mirage. Call "
    "get_country_codes_list first if unsure."
)

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
            "country. Reserves are NOT visible. "
            + _VALID_CODES_HINT
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
    {
        "name": "get_relationships",
        "description": (
            "Returns your bilateral relationships: countries you are at "
            "war with, and countries at war with you (reverse lookup). "
            "Full bilateral tension matrix is deferred."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_organization_memberships",
        "description": (
            "Returns international organizations your country belongs to "
            "(UNSC, NATO, BRICS, OPEC, EREB_UNION, etc.) and the full "
            "catalog of all organizations with their current membership "
            "lists."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_country_codes_list",
        "description": (
            "Returns the authoritative list of valid country codes with "
            "their SIM names and real-world parallels. Call this to avoid "
            "guessing or hallucinating country identifiers."
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
        "get_relationships": lambda args: agent_tools.get_relationships(country_code=country_code),
        "get_organization_memberships": lambda args: agent_tools.get_organization_memberships(country_code=country_code),
        "get_country_codes_list": lambda args: agent_tools.get_country_codes_list(),
    }


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT_TEMPLATE = """You are {character_name}, {title} of {country_name} ({country_parallel}).

It is Q1 2026. You are assessing your country's military situation AND deciding on priorities for this round of the simulation.

Use the available tools to gather what you need.

DELIVER: Your 3 TOP MILITARY PRIORITIES for this round, with clear reasoning.

For each priority:
- What is the priority? (e.g., "Reinforce Fortress Belt defense", "Project carrier power near Persia", "Maintain nuclear deterrent")
- WHY is it a priority? (strategic reasoning grounded in the situation)
- What SPECIFIC action(s) would advance it? (e.g., "Move col_g_09 from reserve to freeland hex", "Position second CSG in Arabian Sea")

Keep each priority concise (3-4 sentences). Be specific — reference actual units, countries, hexes.

End with a 1-sentence overall strategic intent."""


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

async def run_stage2_test(
    country_code: str,
    character_name: str,
    title: str,
    country_name: str,
    country_parallel: str,
) -> dict:
    """Run Stage 2 objective-setting test for one country."""
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
        {"role": "user", "content": "Set your 3 top military priorities for this round. Use the tools as needed."},
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

    summary_rows = []
    for agent in AGENTS:
        print(f"\n=== Running {agent['country_code']} ({agent['character_name']}) ===")
        result = await run_stage2_test(**agent)

        out_path = RESULTS_DIR / f"{agent['country_code']}.json"
        with out_path.open("w") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"  saved -> {out_path.name}")
        print(f"  tool calls: {result['tool_call_count']} | duration: {result['duration_s']}s")
        print(f"  assessment preview: {result['final_assessment'][:240]}...")
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
