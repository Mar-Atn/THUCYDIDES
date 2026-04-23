"""Phase 2 — Custom tool JSON schemas for Managed Agent sessions.

Defines 16 game tools that the agent can call. Our code executes them
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
        "Types: move_units, declare_attack, naval_blockade, nuclear_test, "
        "set_budget, set_tariffs, set_sanctions, set_opec, rd_investment, "
        "public_statement, call_org_meeting, covert_operation, propose_transaction, "
        "respond_exchange, basing_rights, change_leader, arrest."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "object",
                "description": (
                    "MILITARY: move_units(decision,rationale,changes.moves[]), "
                    "declare_attack(attacker_unit_codes[],target_global_row,target_global_col), "
                    "naval_blockade(zone_id,level:full|partial), nuclear_test(test_type). "
                    "ECONOMIC: set_budget(social_pct:0.5-1.5,military_coins,tech_coins), "
                    "set_tariffs(target_country,level:0-3), set_sanctions(target_country,level:0-3), "
                    "set_opec(production:cut|maintain|increase). "
                    "TECH: rd_investment(domain:nuclear|ai,amount). "
                    "COMMS: public_statement(content), call_org_meeting(organization_code,agenda). "
                    "COVERT: covert_operation(op_type,target_country). "
                    "TRANSACTION: propose_transaction(counterpart_country_code,offer,request), "
                    "respond_exchange(transaction_id,response:accept|decline)."
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
# New Phase 1B tools (9-16)
# ---------------------------------------------------------------------------

READ_NOTES_SCHEMA: dict = {
    "name": "read_notes",
    "description": (
        "Read a specific note from your private notebook by key, or list all "
        "note keys if no key is provided. If key is given, returns the full "
        "content. If key is omitted, returns all keys with previews."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "key": {
                "type": "string",
                "description": "Note key to read (e.g., 'strategic_plan'). Omit to list all keys.",
            },
        },
        "required": [],
    },
}

GET_COUNTRY_INFO_SCHEMA: dict = {
    "name": "get_country_info",
    "description": (
        "Returns public info about ANY specific country (not just yours): "
        "GDP, treasury, regime type, stability, wars, military totals, "
        "nuclear level. Use get_all_countries first for valid codes."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "country_code": {
                "type": "string",
                "description": "Country code to look up (e.g., 'cathay', 'columbia').",
            },
        },
        "required": ["country_code"],
    },
}

GET_HEX_INFO_SCHEMA: dict = {
    "name": "get_hex_info",
    "description": (
        "Returns info about a specific hex: terrain, units present, theater "
        "link. Scope is 'global' (1..10 x 1..20) or a theater name "
        "('eastern_ereb' or 'mashriq', both 1..10 x 1..10)."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "row": {"type": "integer", "description": "Row coordinate (1-indexed)."},
            "col": {"type": "integer", "description": "Column coordinate (1-indexed)."},
            "scope": {
                "type": "string",
                "description": "Coordinate scope: 'global', 'eastern_ereb', or 'mashriq'.",
            },
        },
        "required": ["row", "col", "scope"],
    },
}

GET_ORGANIZATIONS_SCHEMA: dict = {
    "name": "get_organizations",
    "description": (
        "Returns international organizations you belong to plus the full "
        "catalog (UNSC, NATO, BRICS, OPEC, EREB_UNION) with their members."
    ),
    "input_schema": {"type": "object", "properties": {}, "required": []},
}

GET_MY_ARTEFACTS_SCHEMA: dict = {
    "name": "get_my_artefacts",
    "description": (
        "Returns your role's artefacts: intelligence reports, diplomatic "
        "cables, letters, and other classified documents delivered to you. "
        "These contain asymmetric information only you can see."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "unread_only": {
                "type": "boolean",
                "description": "If true, return only unread artefacts. Default false.",
            },
        },
        "required": [],
    },
}

GET_ACTION_RULES_SCHEMA: dict = {
    "name": "get_action_rules",
    "description": (
        "Returns the rules and required fields for a specific action type. "
        "Call this BEFORE submit_action to understand what fields you need. "
        "Returns field names, types, descriptions, and constraints."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "action_type": {
                "type": "string",
                "description": (
                    "Action type to look up, e.g. 'declare_attack', 'set_tariff', "
                    "'propose_transaction'. Omit to list all available types."
                ),
            },
        },
        "required": [],
    },
}

REQUEST_MEETING_SCHEMA: dict = {
    "name": "request_meeting",
    "description": (
        "Send a meeting invitation to another country's leader. They must "
        "accept before you can talk. Max 2 active invitations at a time. "
        "Expires in 10 minutes if not answered."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "target_country": {
                "type": "string",
                "description": "Country code of the leader you want to meet.",
            },
            "agenda": {
                "type": "string",
                "description": "Brief agenda or message (max 300 chars).",
            },
        },
        "required": ["target_country", "agenda"],
    },
}

RESPOND_TO_INVITATION_SCHEMA: dict = {
    "name": "respond_to_invitation",
    "description": (
        "Accept or decline a meeting invitation you received. Use "
        "get_pending_proposals to see your pending invitations first. "
        "Accepting creates a meeting channel for conversation."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "invitation_id": {
                "type": "string",
                "description": "ID of the invitation to respond to.",
            },
            "decision": {
                "type": "string",
                "description": "Your decision: 'accept' or 'decline'.",
                "enum": ["accept", "decline"],
            },
        },
        "required": ["invitation_id", "decision"],
    },
}


# ---------------------------------------------------------------------------
# All tool schemas for agent creation (16 tools)
# ---------------------------------------------------------------------------

MANAGED_TOOL_SCHEMAS: list[dict] = [
    # Original 8
    GET_MY_COUNTRY_SCHEMA,
    GET_ALL_COUNTRIES_SCHEMA,
    GET_RELATIONSHIPS_SCHEMA,
    GET_RECENT_EVENTS_SCHEMA,
    GET_MY_FORCES_SCHEMA,
    GET_PENDING_PROPOSALS_SCHEMA,
    SUBMIT_ACTION_SCHEMA,
    WRITE_NOTES_SCHEMA,
    # New 8 (Phase 1B)
    READ_NOTES_SCHEMA,
    GET_COUNTRY_INFO_SCHEMA,
    GET_HEX_INFO_SCHEMA,
    GET_ORGANIZATIONS_SCHEMA,
    GET_MY_ARTEFACTS_SCHEMA,
    GET_ACTION_RULES_SCHEMA,
    REQUEST_MEETING_SCHEMA,
    RESPOND_TO_INVITATION_SCHEMA,
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
