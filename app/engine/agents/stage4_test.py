# DEPRECATED (2026-04-06) — replaced by agents/leader_round.py (uses LeaderAgent + llm_tools)
# Kept for reference. Do not add new logic here.
"""Stage 4: Action Precision Test.

Tests whether agents can commit prose recommendations as STRUCTURED DB WRITES.
Agent reasons across 4 domains (Stage 3), then calls ``commit_action`` with a
typed payload — this writes to ``agent_decisions``.

Architecture: Anthropic tool-use. All 12 read-only tools from Stage 3 plus the
commit_action WRITE tool. Agent investigates, then commits ONCE.

Usage:
    cd app && PYTHONPATH=. python3 -m engine.agents.stage4_test
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
from engine.agents.stage3_test import TOOL_SCHEMAS as STAGE3_TOOL_SCHEMAS
from engine.config.settings import settings

logger = logging.getLogger(__name__)

# Model: latest Sonnet. See app/config/LLM_MODELS.md
MODEL_ID = "claude-sonnet-4-20250514"  # Sonnet 4.6
MAX_TOOL_CALLS = 20
MAX_TOKENS = 4000
SCENARIO_CODE = "start_one"

RESULTS_DIR = Path(__file__).resolve().parent / "stage4_results"

COUNTRY_CODES = ["columbia", "sarmatia", "persia", "cathay", "levantia"]


# ---------------------------------------------------------------------------
# commit_action tool schema (13th tool, WRITE)
# ---------------------------------------------------------------------------

COMMIT_ACTION_SCHEMA = {
    "name": "commit_action",
    "description": (
        "COMMIT your primary action for this round. REAL WRITE — call ONCE. "
        "The 'action' object must include 'action_type' + 'rationale' + type-specific fields."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "object",
                "description": (
                    "Structured action payload. Required: action_type + rationale.\n\n"
                    "MILITARY:\n"
                    "  move_unit: unit_code, target_global_row, target_global_col\n"
                    "  mobilize_reserve: unit_code, target_global_row, target_global_col\n"
                    "  declare_attack: attacker_unit_codes (list), target_global_row, target_global_col, target_description\n"
                    "  naval_bombardment: naval_unit_codes (list), target_global_row, target_global_col\n"
                    "  declare_blockade: zone_id (chokepoint name), level (full|partial)\n"
                    "  nuclear_test: test_type (underground|overground)\n"
                    "\n"
                    "ECONOMIC:\n"
                    "  set_budget: social_pct (0.5-1.5), military_coins, tech_coins\n"
                    "  set_tariff: target_country, level (0-3)\n"
                    "  set_sanction: target_country, level (0-3)\n"
                    "  set_opec: production (cut|maintain|increase) — OPEC members only\n"
                    "\n"
                    "TECHNOLOGY:\n"
                    "  rd_investment: domain (nuclear|ai), amount (coins to invest)\n"
                    "\n"
                    "COMMUNICATION:\n"
                    "  public_statement: content (free text — covers war declarations, peace "
                    "offers, territorial claims, speeches, threats, anything public)\n"
                    "  call_org_meeting: organization_code, agenda (free text)\n"
                    "\n"
                    "COVERT:\n"
                    "  covert_op: op_type (espionage|sabotage|cyber|disinformation|election_meddling), "
                    "target_country\n"
                    "\n"
                    "TRANSACTIONS (bilateral — counterpart must confirm):\n"
                    "  propose_transaction: counterpart_country, terms (free text — ceasefire, "
                    "arms sale, coin transfer, tech transfer, treaty, basing rights, alliance, "
                    "trade deal, or any other agreement)\n"
                ),
            },
        },
        "required": ["action"],
    },
}

TOOL_SCHEMAS = STAGE3_TOOL_SCHEMAS + [COMMIT_ACTION_SCHEMA]


def _build_tool_dispatcher(
    country_code: str,
    commit_tracker: dict,
) -> dict[str, Callable[[dict], Any]]:
    """Bind country_code as closure. commit_tracker records the write."""
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
        )
        if result.get("success"):
            commit_tracker["committed"] = True
            commit_tracker["result"] = result
        return result

    base["commit_action"] = _commit
    return base


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT_TEMPLATE = """You are {character_name}, {title}.

It is Q1 2026. You must issue ONE concrete action this round.

STEP 1: Assess your situation using tools (military, economic, political, tech).
STEP 2: Decide on your PRIMARY action for this round.
STEP 3: Commit that action using the commit_action tool with a structured payload.

The commit_action tool accepts these action types:
- move_unit: reposition an existing unit
- mobilize_reserve: activate a reserve unit to a location
- declare_attack: declare attack against an enemy position
- naval_bombardment: bombard a land hex from adjacent sea
- declare_blockade: blockade a chokepoint or sea zone
- nuclear_test: conduct a nuclear test (underground/overground)
- set_budget: allocate national budget (social/military/tech)
- set_sanction: impose sanctions on another country
- set_tariff: impose tariffs on another country
- set_opec: set OPEC production level (OPEC members only)
- rd_investment: invest in nuclear/ai R&D
- public_statement: free-text public communication (war declarations, peace offers, threats, speeches)
- call_org_meeting: call a meeting of an organization you belong to
- covert_op: espionage/sabotage/cyber/disinformation/election_meddling against a target
- propose_transaction: propose a bilateral deal (any terms — arms, coins, tech, treaty, basing, ceasefire)

Reason briefly, then CALL commit_action with your decision. This is a REAL COMMIT — it writes to the database and represents your country's action for this round.

You have ONE commit. Choose carefully."""


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

async def run_stage4_test(
    country_code: str,
    character_name: str,
    title: str,
) -> dict:
    start = time.time()
    client = Anthropic(api_key=settings.anthropic_api_key)
    commit_tracker: dict = {"committed": False, "result": None}
    dispatcher = _build_tool_dispatcher(country_code, commit_tracker)

    system = SYSTEM_PROMPT_TEMPLATE.format(
        character_name=character_name, title=title,
    )

    messages: list[dict] = [
        {"role": "user", "content": (
            "Assess your situation across the four domains, decide your "
            "primary action for Q1 2026, and commit it via commit_action. "
            "Use read tools as needed first, then commit ONCE."
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
            logger.info("[%s] tool_use: %s", country_code, tool_name)

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
                "input": tool_input if tool_name == "commit_action" else None,
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
        result = await run_stage4_test(
            country_code=agent["country_code"],
            character_name=agent["character_name"],
            title=agent["title"],
        )

        out_path = RESULTS_DIR / f"{agent['country_code']}.json"
        with out_path.open("w") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"  saved -> {out_path.name}")
        print(f"  tool calls: {result['tool_call_count']} | duration: {result['duration_s']}s")
        cr = result.get("commit_result") or {}
        print(f"  committed: {result['committed']} | type: {cr.get('action_type')} "
              f"| status: {cr.get('validation_status')} | id: {cr.get('action_id')}")
        if cr.get("validation_notes"):
            print(f"  notes: {cr['validation_notes']}")
        summary_rows.append({
            "country": result["country"],
            "committed": result["committed"],
            "action_type": cr.get("action_type"),
            "validation_status": cr.get("validation_status"),
            "tool_calls": result["tool_call_count"],
            "duration_s": result["duration_s"],
        })

    print("\n=== Summary ===")
    for r in summary_rows:
        print(
            f"  {r['country']:10s} committed={r['committed']!s:5s} "
            f"type={str(r['action_type'] or '-'):20s} "
            f"status={str(r['validation_status'] or '-'):8s} "
            f"calls={r['tool_calls']:2d} duration={r['duration_s']:5.1f}s"
        )


if __name__ == "__main__":
    asyncio.run(run_all())
