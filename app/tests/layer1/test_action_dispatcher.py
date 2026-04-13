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
    result = _route("sim1", 1, "covert_op", {"action_type": "covert_op", "op_type": "unknown_op"})
    assert not result["success"]
    assert "Unknown op_type" in result["narrative"]


def test_unknown_attack_type():
    """Unknown attack_type returns error."""
    result = _route("sim1", 1, "declare_attack", {"action_type": "declare_attack", "attack_type": "psychic"})
    assert not result["success"]
    assert "Unknown attack_type" in result["narrative"]


def test_all_action_types_have_routes():
    """Every action type in ACTION_TYPE_TO_MODEL has a route in dispatcher.

    Batch actions (budget, sanctions, tariffs, OPEC, movement) are handled
    by the orchestrator directly, not the Phase A dispatcher. Stubs
    (rd_investment, call_org_meeting) are not yet implemented.
    """
    from engine.agents.action_schemas import ACTION_TYPE_TO_MODEL

    # These are handled by orchestrator batch processing or not yet implemented
    EXCLUDED = {
        "set_sanction", "set_tariff", "move_units",  # batch / inter-round
        "rd_investment", "call_org_meeting",  # stubs, future implementation
    }

    known_types = set(ACTION_TYPE_TO_MODEL.keys()) - EXCLUDED
    unknown_handler_types = set()

    for action_type in known_types:
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
