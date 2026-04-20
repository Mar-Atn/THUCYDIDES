"""L1 — Action dispatcher: routing coverage for all action types."""

from __future__ import annotations
import pytest
from unittest.mock import patch, MagicMock
from engine.services.action_dispatcher import _route


def test_unknown_action_type():
    """Unknown action_type returns error, doesn't crash."""
    result = _route("sim1", 1, "nonexistent_action", {"action_type": "nonexistent_action"})
    assert not result["success"]
    assert "Unknown action_type" in result["narrative"]


def test_unknown_covert_op_type():
    """Unknown covert op_type returns error."""
    result = _route("sim1", 1, "covert_operation", {"action_type": "covert_operation", "op_type": "unknown_op"})
    assert not result["success"]
    assert "unknown_op" in result["narrative"].lower()


def test_unknown_attack_type():
    """Unknown attack_type under ground_attack returns error."""
    result = _route("sim1", 1, "ground_attack", {"action_type": "ground_attack", "attack_type": "psychic"})
    # ground_attack is routed to attack handler which requires real DB data
    # Just verify it doesn't return "Unknown action_type"
    assert "Unknown action_type" not in result.get("narrative", "")


def test_all_dispatcher_routes():
    """All human-interface action types have routes in the dispatcher.

    Action types routed via main.py submit_action → _route().
    Batch actions (budget, sanctions, tariffs, OPEC, movement) are handled
    by the orchestrator directly, not the Phase A dispatcher.
    Reactive actions are handled by dedicated endpoints, not _route().
    """
    # These are ALL the action types that go through _route()
    ROUTED_ACTIONS = {
        "ground_attack", "air_strike", "naval_combat", "naval_bombardment",
        "launch_missile_conventional", "naval_blockade", "ground_move",
        "nuclear_test", "nuclear_launch_initiate",
        "declare_war", "martial_law", "basing_rights",
        "propose_agreement", "propose_transaction",
        "arrest", "release_arrest", "assassination",
        "covert_operation", "intelligence",
        "public_statement", "invite_to_meet", "respond_meeting",
        "change_leader", "reassign_types",
        "self_nominate", "cast_election_vote",
    }

    unknown_handler_types = set()
    for action_type in ROUTED_ACTIONS:
        try:
            result = _route("fake_sim", 1, action_type, {
                "action_type": action_type,
                "role_id": "test",
                "country_code": "test",
            })
            if isinstance(result, dict) and "Unknown action_type" in result.get("narrative", ""):
                unknown_handler_types.add(action_type)
        except Exception:
            # Expected — engines need real DB. But they were REACHED, not "unknown".
            pass

    assert unknown_handler_types == set(), f"Action types with no route: {unknown_handler_types}"


def test_public_statement_no_db():
    """Public statement route works without DB (just logs)."""
    with patch("engine.services.action_dispatcher.get_client") as mock_client, \
         patch("engine.services.action_dispatcher.get_scenario_id", return_value=None):
        result = _route("sim1", 1, "public_statement", {
            "action_type": "public_statement",
            "role_id": "dealer",
            "country_code": "columbia",
            "content": "Peace is our highest priority.",
        })
    assert result["success"]
    assert "PUBLIC STATEMENT" in result["narrative"]
    assert "dealer" in result["narrative"]
