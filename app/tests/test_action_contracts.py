"""Contract tests — verify action naming consistency across all surfaces.

These tests ensure that the canonical action names in MODULE_REGISTRY
are correctly implemented in the action dispatcher, Pydantic schemas,
and AI agent tool definitions. If any surface drifts, these tests fail.

Run: pytest tests/test_action_contracts.py -v
"""
import re
import pytest


# -- Canonical action names (from MODULE_REGISTRY) --------------------------
# This is the SINGLE SOURCE OF TRUTH. All other surfaces must match.

CANONICAL_PLAYER_ACTIONS = {
    # Military — Combat
    "ground_attack", "ground_move", "air_strike", "naval_combat",
    "naval_bombardment", "launch_missile_conventional",
    # Military — Non-Combat
    "move_units", "naval_blockade", "basing_rights", "martial_law",
    "nuclear_test", "nuclear_launch_initiate", "nuclear_authorize", "nuclear_intercept",
    # Economic
    "set_budget", "set_tariffs", "set_sanctions", "set_opec",
    "propose_transaction", "accept_transaction",
    # Communication
    "public_statement", "call_org_meeting",
    # Diplomatic
    "declare_war", "propose_agreement", "sign_agreement",
    # Covert
    "covert_operation", "intelligence",
    # Political
    "arrest", "assassination", "change_leader", "reassign_types",
    "self_nominate", "cast_vote",
}

REACTIVE_ACTIONS = {
    "release_arrest", "respond_meeting", "set_meetings",
    "meet_freely", "withdraw_nomination", "cast_election_vote", "resolve_election",
}

# Schema-only entries: previously in ACTION_TYPE_TO_MODEL for documentation
# but not standalone dispatched actions. rd_investment removed (part of set_budget).
SCHEMA_ONLY: set[str] = set()

# Tool-routed actions: player-initiated but handled by dedicated tools,
# not through submit_action → dispatcher. No Pydantic schema needed.
TOOL_ROUTED = {"invite_to_meet"}

ALL_CANONICAL = CANONICAL_PLAYER_ACTIONS | REACTIVE_ACTIONS | SCHEMA_ONLY | TOOL_ROUTED


# -- Test 1: Every canonical action is handled by the dispatcher ------------

def test_dispatcher_handles_all_canonical_actions():
    """Every canonical action name must appear in action_dispatcher._route()."""
    import inspect
    from engine.services import action_dispatcher

    source = inspect.getsource(action_dispatcher._route)

    missing = []
    for action in (CANONICAL_PLAYER_ACTIONS | REACTIVE_ACTIONS):
        # Check that the action_type string appears in the _route function
        if f'"{action}"' not in source and f"'{action}'" not in source:
            missing.append(action)

    assert not missing, (
        f"Actions missing from action_dispatcher._route(): {sorted(missing)}"
    )


# -- Test 2: Every canonical player action has a Pydantic schema -----------

def test_schemas_cover_all_player_actions():
    """Every canonical player action must have an entry in ACTION_TYPE_TO_MODEL."""
    from engine.agents.action_schemas import ACTION_TYPE_TO_MODEL

    missing = []
    for action in CANONICAL_PLAYER_ACTIONS:
        if action not in ACTION_TYPE_TO_MODEL:
            missing.append(action)

    assert not missing, (
        f"Actions missing from ACTION_TYPE_TO_MODEL: {sorted(missing)}"
    )


# -- Test 3: No stale names in ACTION_TYPE_TO_MODEL -------------------------

STALE_NAMES = {
    "declare_attack", "launch_missile", "blockade", "covert_op",
    "reassign_powers", "submit_nomination", "call_early_elections",
    "propose_exchange", "respond_exchange", "set_tariff", "set_sanction",
    "set_opec_production", "accept_meeting",
}


def test_no_stale_names_in_schemas():
    """ACTION_TYPE_TO_MODEL must not contain any stale/removed action names."""
    from engine.agents.action_schemas import ACTION_TYPE_TO_MODEL

    found_stale = []
    for name in ACTION_TYPE_TO_MODEL:
        if name in STALE_NAMES:
            found_stale.append(name)

    assert not found_stale, (
        f"Stale action names found in ACTION_TYPE_TO_MODEL: {sorted(found_stale)}"
    )


# -- Test 4: Schema action_type Literal matches canonical name ---------------

def test_schema_literals_use_canonical_names():
    """Each Pydantic model's action_type Literal must only contain canonical names."""
    from engine.agents.action_schemas import ACTION_TYPE_TO_MODEL

    for action_name, model_cls in ACTION_TYPE_TO_MODEL.items():
        # Get the Literal values from the action_type field
        field_info = model_cls.model_fields.get("action_type")
        if field_info is None:
            continue

        annotation = field_info.annotation
        if annotation is None:
            continue

        # Extract Literal values
        if hasattr(annotation, "__args__"):
            literal_values = set(annotation.__args__)
            for val in literal_values:
                assert val in ALL_CANONICAL or val in CANONICAL_PLAYER_ACTIONS, (
                    f"Model {model_cls.__name__} has stale Literal value "
                    f"'{val}' for action_type. Canonical name is '{action_name}'."
                )


# -- Test 5: Dispatcher + schema round-trip for key actions ------------------

@pytest.mark.parametrize("action_type", [
    "public_statement", "set_budget", "declare_war",
])
def test_schema_validates_sample_payload(action_type):
    """Sample payloads for key actions must pass schema validation."""
    from engine.agents.action_schemas import ACTION_TYPE_TO_MODEL

    model_cls = ACTION_TYPE_TO_MODEL[action_type]

    samples = {
        "public_statement": {
            "action_type": "public_statement",
            "content": "Test statement",
            "rationale": "Testing",
        },
        "set_budget": {
            "action_type": "set_budget",
            "social_pct": 1.0,
            "military_coins": 5.0,
            "tech_coins": 3.0,
            "rationale": "Testing",
        },
        "declare_war": {
            "action_type": "declare_war",
            "target_country": "test",
            "rationale": "Testing",
        },
    }

    payload = samples[action_type]
    # Should not raise
    validated = model_cls.model_validate(payload)
    assert validated.action_type == action_type
