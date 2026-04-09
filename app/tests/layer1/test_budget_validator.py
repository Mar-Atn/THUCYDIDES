"""Layer 1 tests for budget_validator — CONTRACT_BUDGET v1.1.

Covers every error code in §4.1 and §4.2 plus the happy path and
normalized-output behavior. Each test is labelled with the error code it
targets so failures point directly at the affected rule.
"""

from __future__ import annotations

import copy

import pytest

from engine.services.budget_validator import validate_budget_decision


# ---------------------------------------------------------------------------
# FIXTURES
# ---------------------------------------------------------------------------


VALID_RATIONALE = (
    "We prioritise ground readiness to deter escalation along the northern border."
)


def _valid_change() -> dict:
    """A fully valid 'change' decision."""
    return {
        "action_type": "set_budget",
        "country_code": "columbia",
        "round_num": 3,
        "decision": "change",
        "rationale": VALID_RATIONALE,
        "changes": {
            "social_pct": 1.0,
            "production": {
                "ground": 1,
                "naval": 0,
                "tactical_air": 2,
                "strategic_missile": 0,
                "air_defense": 1,
            },
            "research": {
                "nuclear_coins": 0,
                "ai_coins": 5,
            },
        },
    }


def _valid_no_change() -> dict:
    """A fully valid 'no_change' decision."""
    return {
        "action_type": "set_budget",
        "country_code": "columbia",
        "round_num": 3,
        "decision": "no_change",
        "rationale": VALID_RATIONALE,
    }


def _assert_error_code(result: dict, code: str) -> None:
    """Fail with a helpful message if the given error code isn't in result."""
    assert not result["valid"], (
        f"expected invalid (error {code}), but valid=True. "
        f"errors={result['errors']}"
    )
    assert any(e.startswith(code) for e in result["errors"]), (
        f"expected error code {code} not found. got: {result['errors']}"
    )


# ===========================================================================
# HAPPY PATH
# ===========================================================================


class TestHappyPath:
    def test_valid_change_decision(self):
        result = validate_budget_decision(_valid_change())
        assert result["valid"] is True
        assert result["errors"] == []
        assert result["normalized"] is not None
        assert result["normalized"]["decision"] == "change"
        assert "changes" in result["normalized"]

    def test_valid_no_change_decision(self):
        result = validate_budget_decision(_valid_no_change())
        assert result["valid"] is True
        assert result["errors"] == []
        assert result["normalized"]["decision"] == "no_change"
        assert "changes" not in result["normalized"]

    def test_social_pct_lower_boundary(self):
        p = _valid_change()
        p["changes"]["social_pct"] = 0.5
        result = validate_budget_decision(p)
        assert result["valid"], f"errors={result['errors']}"

    def test_social_pct_upper_boundary(self):
        p = _valid_change()
        p["changes"]["social_pct"] = 1.5
        result = validate_budget_decision(p)
        assert result["valid"], f"errors={result['errors']}"

    def test_production_level_zero(self):
        p = _valid_change()
        for b in p["changes"]["production"]:
            p["changes"]["production"][b] = 0
        result = validate_budget_decision(p)
        assert result["valid"], f"errors={result['errors']}"

    def test_production_level_three(self):
        p = _valid_change()
        for b in p["changes"]["production"]:
            p["changes"]["production"][b] = 3
        result = validate_budget_decision(p)
        assert result["valid"], f"errors={result['errors']}"

    def test_research_zero_coins(self):
        p = _valid_change()
        p["changes"]["research"]["nuclear_coins"] = 0
        p["changes"]["research"]["ai_coins"] = 0
        result = validate_budget_decision(p)
        assert result["valid"], f"errors={result['errors']}"

    def test_research_large_coins(self):
        p = _valid_change()
        p["changes"]["research"]["nuclear_coins"] = 10_000
        p["changes"]["research"]["ai_coins"] = 999_999
        result = validate_budget_decision(p)
        assert result["valid"], f"errors={result['errors']}"

    def test_no_change_with_null_changes_is_valid(self):
        p = _valid_no_change()
        p["changes"] = None
        result = validate_budget_decision(p)
        assert result["valid"], f"errors={result['errors']}"


# ===========================================================================
# STRUCTURAL ERRORS (§4.1)
# ===========================================================================


class TestStructuralErrors:
    def test_missing_action_type(self):
        p = _valid_change()
        del p["action_type"]
        _assert_error_code(validate_budget_decision(p), "INVALID_ACTION_TYPE")

    def test_wrong_action_type(self):
        p = _valid_change()
        p["action_type"] = "set_tariff"
        _assert_error_code(validate_budget_decision(p), "INVALID_ACTION_TYPE")

    def test_missing_decision(self):
        p = _valid_change()
        del p["decision"]
        _assert_error_code(validate_budget_decision(p), "INVALID_DECISION")

    def test_wrong_decision(self):
        p = _valid_change()
        p["decision"] = "maybe"
        _assert_error_code(validate_budget_decision(p), "INVALID_DECISION")

    def test_missing_rationale(self):
        p = _valid_change()
        del p["rationale"]
        _assert_error_code(validate_budget_decision(p), "RATIONALE_TOO_SHORT")

    def test_short_rationale(self):
        p = _valid_change()
        p["rationale"] = "too short"  # 9 chars
        _assert_error_code(validate_budget_decision(p), "RATIONALE_TOO_SHORT")

    def test_change_missing_changes(self):
        p = _valid_change()
        del p["changes"]
        _assert_error_code(validate_budget_decision(p), "MISSING_CHANGES")

    def test_no_change_with_changes_present(self):
        p = _valid_no_change()
        p["changes"] = _valid_change()["changes"]
        _assert_error_code(validate_budget_decision(p), "UNEXPECTED_CHANGES")


# ===========================================================================
# RANGE ERRORS (§4.2)
# ===========================================================================


class TestSocialPctErrors:
    def test_social_pct_below_min(self):
        p = _valid_change()
        p["changes"]["social_pct"] = 0.3
        _assert_error_code(validate_budget_decision(p), "INVALID_SOCIAL_PCT")

    def test_social_pct_above_max(self):
        p = _valid_change()
        p["changes"]["social_pct"] = 2.0
        _assert_error_code(validate_budget_decision(p), "INVALID_SOCIAL_PCT")

    def test_social_pct_wrong_type(self):
        p = _valid_change()
        p["changes"]["social_pct"] = "high"
        _assert_error_code(validate_budget_decision(p), "INVALID_SOCIAL_PCT")


class TestProductionBranchErrors:
    def test_missing_ground(self):
        p = _valid_change()
        del p["changes"]["production"]["ground"]
        _assert_error_code(validate_budget_decision(p), "MISSING_PRODUCTION_BRANCH")

    def test_missing_air_defense(self):
        p = _valid_change()
        del p["changes"]["production"]["air_defense"]
        _assert_error_code(validate_budget_decision(p), "MISSING_PRODUCTION_BRANCH")


class TestProductionLevelErrors:
    def test_ground_level_too_high(self):
        p = _valid_change()
        p["changes"]["production"]["ground"] = 5
        _assert_error_code(validate_budget_decision(p), "INVALID_PRODUCTION_LEVEL")

    def test_naval_level_negative(self):
        p = _valid_change()
        p["changes"]["production"]["naval"] = -1
        _assert_error_code(validate_budget_decision(p), "INVALID_PRODUCTION_LEVEL")

    def test_tactical_air_level_float(self):
        p = _valid_change()
        p["changes"]["production"]["tactical_air"] = 1.5
        _assert_error_code(validate_budget_decision(p), "INVALID_PRODUCTION_LEVEL")


class TestResearchErrors:
    def test_nuclear_coins_negative(self):
        p = _valid_change()
        p["changes"]["research"]["nuclear_coins"] = -5
        _assert_error_code(validate_budget_decision(p), "INVALID_RESEARCH_COINS")

    def test_ai_coins_wrong_type(self):
        p = _valid_change()
        p["changes"]["research"]["ai_coins"] = "lots"
        _assert_error_code(validate_budget_decision(p), "INVALID_RESEARCH_COINS")

    def test_missing_nuclear_coins(self):
        p = _valid_change()
        del p["changes"]["research"]["nuclear_coins"]
        _assert_error_code(validate_budget_decision(p), "INVALID_RESEARCH_COINS")


class TestUnknownFieldErrors:
    def test_unknown_change_field(self):
        p = _valid_change()
        p["changes"]["tariffs"] = {"steel": 0.1}
        _assert_error_code(validate_budget_decision(p), "UNKNOWN_FIELD")

    def test_unknown_top_level_field(self):
        p = _valid_change()
        p["extra_field"] = "nope"
        _assert_error_code(validate_budget_decision(p), "UNKNOWN_FIELD")


# ===========================================================================
# NORMALIZED OUTPUT
# ===========================================================================


class TestNormalizedOutput:
    def test_rationale_is_trimmed(self):
        p = _valid_change()
        p["rationale"] = "   " + VALID_RATIONALE + "   \n"
        result = validate_budget_decision(p)
        assert result["valid"]
        assert result["normalized"]["rationale"] == VALID_RATIONALE
        assert not result["normalized"]["rationale"].startswith(" ")
        assert not result["normalized"]["rationale"].endswith(" ")

    def test_production_levels_preserved_as_int(self):
        p = _valid_change()
        result = validate_budget_decision(p)
        assert result["valid"]
        prod = result["normalized"]["changes"]["production"]
        for branch, level in prod.items():
            assert isinstance(level, int), f"{branch}={level!r} is not int"
            assert not isinstance(level, bool)

    def test_social_pct_preserved_as_float(self):
        p = _valid_change()
        p["changes"]["social_pct"] = 1  # int on input
        result = validate_budget_decision(p)
        assert result["valid"]
        assert isinstance(result["normalized"]["changes"]["social_pct"], float)
        assert result["normalized"]["changes"]["social_pct"] == 1.0

    def test_normalized_has_no_extras_on_valid(self):
        p = _valid_change()
        result = validate_budget_decision(p)
        assert result["valid"]
        assert set(result["normalized"]["changes"].keys()) == {
            "social_pct",
            "production",
            "research",
        }

    def test_normalized_is_none_on_invalid(self):
        p = _valid_change()
        p["changes"]["social_pct"] = 99
        result = validate_budget_decision(p)
        assert not result["valid"]
        assert result["normalized"] is None


# ===========================================================================
# MULTIPLE ERRORS ACCUMULATED
# ===========================================================================


class TestMultipleErrors:
    def test_collects_all_errors_not_just_first(self):
        p = {
            "action_type": "wrong",
            "decision": "maybe",
            "rationale": "x",
            "changes": {
                "social_pct": 99,
                "production": {"ground": 9},  # missing 4 branches + bad level
                "research": {"nuclear_coins": -1},  # missing ai_coins
            },
        }
        result = validate_budget_decision(p)
        assert not result["valid"]
        codes = {e.split(":")[0] for e in result["errors"]}
        # Should see multiple distinct error codes, not stop at first
        assert "INVALID_ACTION_TYPE" in codes
        assert "INVALID_DECISION" in codes
        assert "RATIONALE_TOO_SHORT" in codes
        assert "INVALID_SOCIAL_PCT" in codes
        assert "MISSING_PRODUCTION_BRANCH" in codes
        assert "INVALID_PRODUCTION_LEVEL" in codes
        assert "INVALID_RESEARCH_COINS" in codes
