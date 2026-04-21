"""Phase 2 — Custom tool JSON schemas for Managed Agent sessions.

Defines 8 game tools that the agent can call. Our code executes them
against the real DB via tool_executor.py.

Tool design: composite tools that bundle related queries (e.g.,
get_my_country = economic + political + strategic) to reduce round-trips,
plus granular tools for specific needs.
"""
from __future__ import annotations

from engine.agents.tool_schemas import (
    LOOKUP_TOOL_SCHEMAS,
    COMMIT_ACTION_SCHEMA,
    READ_MEMORY_SCHEMA,
    LIST_MY_MEMORIES_SCHEMA,
    WRITE_MEMORY_SCHEMA,
)


# ---------------------------------------------------------------------------
# Composite tools (new for managed agent — fewer calls, richer context)
# ---------------------------------------------------------------------------

GET_MY_COUNTRY_SCHEMA: dict = {
    "name": "get_my_country",
    "description": (
        "Returns a FULL snapshot of your country: economic state (GDP, treasury, "
        "inflation, trade balance, debt, sectors, oil, OPEC), political state "
        "(stability, support, war tiredness, regime), tech state (nuclear level, "
        "AI level, R&D progress), and strategic overview (wars, military totals). "
        "Call this first to understand your situation."
    ),
    "input_schema": {"type": "object", "properties": {}, "required": []},
}

GET_ALL_COUNTRIES_SCHEMA: dict = {
    "name": "get_all_countries",
    "description": (
        "Returns overview of all 20 countries: country codes, SIM names, "
        "real-world parallels. Use this to learn who the players are and "
        "get valid country codes for other tools."
    ),
    "input_schema": {"type": "object", "properties": {}, "required": []},
}

GET_RECENT_EVENTS_SCHEMA: dict = {
    "name": "get_recent_events",
    "description": (
        "Returns recent observatory events for this simulation — what happened "
        "this round. Includes military actions, diplomatic moves, economic changes, "
        "public statements, and alerts. Optional: filter by event_type or country."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "event_type": {
                "type": "string",
                "description": "Filter by event type (e.g., 'military', 'economic', 'diplomatic'). Omit for all.",
            },
            "limit": {
                "type": "integer",
                "description": "Max events to return (default 20).",
            },
        },
        "required": [],
    },
}

GET_PENDING_PROPOSALS_SCHEMA: dict = {
    "name": "get_pending_proposals",
    "description": (
        "Returns pending proposals and transactions awaiting your response: "
        "trade deals, treaties, alliances, arms sales, basing rights, etc. "
        "Also includes agreements you've proposed that are awaiting counterpart confirmation."
    ),
    "input_schema": {"type": "object", "properties": {}, "required": []},
}


# ---------------------------------------------------------------------------
# Direct reuse tools (same as leader_round.py but with managed agent wrapping)
# ---------------------------------------------------------------------------

# get_relationships — direct reuse from tool_schemas
GET_RELATIONSHIPS_SCHEMA: dict = {
    "name": "get_relationships",
    "description": (
        "Returns your bilateral relationships: who you are at war with, "
        "who is at war with you, and your allies."
    ),
    "input_schema": {"type": "object", "properties": {}, "required": []},
}

# get_my_forces — direct reuse
GET_MY_FORCES_SCHEMA: dict = {
    "name": "get_my_forces",
    "description": (
        "Returns your country's complete force disposition: every unit "
        "with type (ground, naval, tactical_air, strategic_missile, air_defense), "
        "status (active, reserve, embarked, destroyed), and location (global + theater coords)."
    ),
    "input_schema": {"type": "object", "properties": {}, "required": []},
}

# submit_action — wraps commit_action
SUBMIT_ACTION_SCHEMA: dict = {
    "name": "submit_action",
    "description": (
        "Execute a game action (REAL WRITE). Up to 3 per round. "
        "action_type + rationale required. "
        "Types: move_units, declare_attack, naval_bombardment, declare_blockade, nuclear_test, "
        "set_budget, set_tariff, set_sanction, set_opec, rd_investment, "
        "public_statement, call_org_meeting, covert_op, propose_transaction."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "object",
                "description": (
                    "MILITARY: move_units(decision,rationale,changes.moves[]), "
                    "declare_attack(attacker_unit_codes[],target_global_row,target_global_col), "
                    "naval_bombardment(naval_unit_codes[],target_global_row,target_global_col), "
                    "declare_blockade(zone_id,level:full|partial), nuclear_test(test_type). "
                    "ECONOMIC: set_budget(social_pct:0.5-1.5,military_coins,tech_coins), "
                    "set_tariff(target_country,level:0-3), set_sanction(target_country,level:0-3), "
                    "set_opec(production:cut|maintain|increase). "
                    "TECH: rd_investment(domain:nuclear|ai,amount). "
                    "COMMS: public_statement(content), call_org_meeting(organization_code,agenda). "
                    "COVERT: covert_op(op_type,target_country). "
                    "TRANSACTION: propose_transaction(counterpart_country,terms)."
                ),
            },
        },
        "required": ["action"],
    },
}

# write_notes — wraps write_memory
WRITE_NOTES_SCHEMA: dict = {
    "name": "write_notes",
    "description": (
        "Save a note to your private notebook. These persist across rounds. "
        "What you don't write down, you WILL forget.\n\n"
        "Suggested keys: 'strategic_plan', 'observations', 'relationships', "
        "'lessons_learned', 'open_threads'. You may create additional keys freely."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "key": {
                "type": "string",
                "description": "Note key (e.g., 'strategic_plan', 'observations').",
            },
            "content": {
                "type": "string",
                "description": "Free-form text. Be specific and concrete.",
            },
        },
        "required": ["key", "content"],
    },
}


# ---------------------------------------------------------------------------
# All tool schemas for agent creation
# ---------------------------------------------------------------------------

MANAGED_TOOL_SCHEMAS: list[dict] = [
    GET_MY_COUNTRY_SCHEMA,
    GET_ALL_COUNTRIES_SCHEMA,
    GET_RELATIONSHIPS_SCHEMA,
    GET_RECENT_EVENTS_SCHEMA,
    GET_MY_FORCES_SCHEMA,
    GET_PENDING_PROPOSALS_SCHEMA,
    SUBMIT_ACTION_SCHEMA,
    WRITE_NOTES_SCHEMA,
]


def get_custom_tools_for_agent() -> list[dict]:
    """Return tool definitions formatted for Managed Agent creation.

    Wraps each schema as a custom tool type for the managed agents API.
    """
    return [
        {
            "type": "custom",
            "name": schema["name"],
            "description": schema["description"],
            "input_schema": schema["input_schema"],
        }
        for schema in MANAGED_TOOL_SCHEMAS
    ]
