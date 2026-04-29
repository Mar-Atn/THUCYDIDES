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
        "Execute a game action. The 'action' parameter MUST be a JSON object "
        "(not a string). Every action requires 'action_type' and 'rationale'.\n\n"
        "Use get_action_rules(action_type) FIRST to see exact fields for any action.\n\n"
        "EXAMPLES of correct format:\n"
        '  {"action_type":"public_statement","content":"Your message","rationale":"Why"}\n'
        '  {"action_type":"declare_war","target_country":"persia","rationale":"Why"}\n'
        '  {"action_type":"intelligence","question":"What is X doing?","target_country":"cathay","rationale":"Why"}\n'
        '  {"action_type":"set_tariffs","target_country":"columbia","level":2,"rationale":"Why"}\n'
        '  {"action_type":"covert_operation","op_type":"sabotage","target_country":"persia","rationale":"Why"}\n'
        '  {"action_type":"ground_attack","attacker_unit_codes":["SAR-G1"],"target_global_row":4,"target_global_col":11,"target_description":"Ruthenia position","rationale":"Why"}\n\n'
        "AVAILABLE TYPES: ground_attack, air_strike, naval_combat, naval_bombardment, "
        "ground_move, move_units, naval_blockade, basing_rights, martial_law, "
        "nuclear_test, nuclear_launch_initiate, set_budget, set_tariffs, set_sanctions, "
        "set_opec, public_statement, call_org_meeting, declare_war, propose_agreement, "
        "sign_agreement, propose_transaction, accept_transaction, covert_operation, "
        "intelligence, arrest, assassination, change_leader, reassign_types, "
        "self_nominate, cast_vote."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "object",
                "description": (
                    "A JSON object with action_type, rationale, and type-specific fields. "
                    "ALWAYS use get_action_rules(action_type) first to see required fields."
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
        "Expires in 10 minutes if not answered.\n\n"
        "IMPORTANT: Include an intent_note — your conversation avatar has "
        "ONLY two sources of context: your Avatar Identity document and this "
        "Intent Note. The avatar does not know who it is meeting unless you "
        "say so here. Include: who you are meeting (name, country, title), "
        "objective, approach, boundaries, tone, and any relevant context "
        "about the counterpart."
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
            "intent_note": {
                "type": "string",
                "description": (
                    "Your Intent Note for this meeting. Your avatar has ONLY "
                    "your Avatar Identity and this note — nothing else. "
                    "Include: WHO you are meeting (name, country), objective, "
                    "approach (tactics, arguments, questions to ask), "
                    "boundaries (what NOT to reveal or agree to), tone, "
                    "and key context about the counterpart."
                ),
            },
        },
        "required": ["target_country", "agenda", "intent_note"],
    },
}

RESPOND_TO_INVITATION_SCHEMA: dict = {
    "name": "respond_to_invitation",
    "description": (
        "Accept or decline a meeting invitation you received. Use "
        "get_pending_proposals to see your pending invitations first.\n\n"
        "When ACCEPTING: include an intent_note — your conversation avatar "
        "has ONLY your Avatar Identity and this note. The avatar does not "
        "know who it is meeting unless you say so here. Write it carefully."
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
            "intent_note": {
                "type": "string",
                "description": (
                    "Your Intent Note for this meeting (required when accepting). "
                    "Your avatar has ONLY your Avatar Identity and this note. "
                    "Include: WHO you are meeting (name, country), objective, "
                    "approach, boundaries, tone, and counterpart context."
                ),
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
