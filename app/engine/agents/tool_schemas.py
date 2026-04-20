"""Canonical tool schemas for AI agent tool-use calls.

Extracted from deprecated stage*_test.py files to break the import dependency.
These schemas define the LLM-facing tool interfaces; the implementations live
in tools.py and are wired up in leader_round.py.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Hints
# ---------------------------------------------------------------------------

_VALID_CODES_HINT = (
    "Valid country codes are: columbia, cathay, sarmatia, ruthenia, persia, "
    "gallia, teutonia, freeland, ponte, albion, bharata, levantia, formosa, "
    "phrygia, yamato, solaria, choson, hanguk, caribe, mirage. Call "
    "get_country_codes_list first if unsure."
)

MEMORY_KEYS_HINT = (
    "Suggested keys: 'strategic_plan' (active multi-round plan with stages), "
    "'observations' (journal of what happened / what you learned), "
    "'relationships' (per-country trust/tension notes), "
    "'lessons_learned' (what worked / didn't), "
    "'open_threads' (unresolved situations to track). "
    "You may create additional keys freely."
)

# ---------------------------------------------------------------------------
# Lookup tools (Stage 3 — 13 tools)
# ---------------------------------------------------------------------------

LOOKUP_TOOL_SCHEMAS: list[dict] = [
    {
        "name": "get_my_identity",
        "description": (
            "Returns your canonical identity: character_name, title, "
            "real-world parallel, objectives, powers, and ticking_clock "
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

# ---------------------------------------------------------------------------
# Action commit tool (Stage 4)
# ---------------------------------------------------------------------------

COMMIT_ACTION_SCHEMA: dict = {
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
                    "  move_units: decision (change|no_change), rationale, changes.moves[] (CONTRACT_MOVEMENT v1.0)\n"
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

# ---------------------------------------------------------------------------
# Memory tools (Stage 5)
# ---------------------------------------------------------------------------

READ_MEMORY_SCHEMA: dict = {
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

LIST_MY_MEMORIES_SCHEMA: dict = {
    "name": "list_my_memories",
    "description": (
        "List every memory key you have written, with round_num, updated_at, "
        "and a 200-char preview of each. Call this FIRST to see what prior "
        "thinking you can build on."
    ),
    "input_schema": {"type": "object", "properties": {}, "required": []},
}

WRITE_MEMORY_SCHEMA: dict = {
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
