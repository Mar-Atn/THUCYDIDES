"""Layer 1 tests — OPEC production decision validator per CONTRACT_OPEC v1.0."""

from __future__ import annotations

import pytest

from engine.services.opec_validator import (
    CANONICAL_OPEC_MEMBERS,
    RATIONALE_MIN_CHARS,
    VALID_PRODUCTION_LEVELS,
    validate_opec_decision,
)


VALID_RATIONALE = "Cutting production to push oil price toward 120 for wartime revenue."  # 65 chars


def _base(decision: str = "change", country: str = "solaria", **overrides) -> dict:
    payload = {
        "action_type": "set_opec",
        "country_code": country,
        "round_num": 3,
        "decision": decision,
        "rationale": VALID_RATIONALE,
    }
    if decision == "change":
        payload["changes"] = {"production_level": "min"}
    payload.update(overrides)
    return payload


def _has_code(report: dict, code: str) -> bool:
    return any(e.startswith(code) for e in report["errors"])


# ---------------------------------------------------------------------------
# Canonical roster
# ---------------------------------------------------------------------------


class TestCanonicalRoster:
    def test_5_members_exactly(self):
        assert CANONICAL_OPEC_MEMBERS == frozenset(
            {"caribe", "mirage", "persia", "sarmatia", "solaria"}
        )

    def test_sarmatia_included(self):
        assert "sarmatia" in CANONICAL_OPEC_MEMBERS

    def test_caribe_included(self):
        assert "caribe" in CANONICAL_OPEC_MEMBERS

    def test_columbia_not_a_member(self):
        assert "columbia" not in CANONICAL_OPEC_MEMBERS


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


class TestHappyPath:
    def test_minimal_valid_change(self):
        report = validate_opec_decision(_base())
        assert report["valid"], report["errors"]
        assert report["normalized"]["decision"] == "change"
        assert report["normalized"]["changes"]["production_level"] == "min"

    def test_minimal_valid_no_change(self):
        report = validate_opec_decision(_base(decision="no_change"))
        assert report["valid"], report["errors"]
        assert report["normalized"]["decision"] == "no_change"
        assert "changes" not in report["normalized"]

    @pytest.mark.parametrize("level", ["min", "low", "normal", "high", "max"])
    def test_all_levels_valid(self, level):
        payload = _base()
        payload["changes"] = {"production_level": level}
        report = validate_opec_decision(payload)
        assert report["valid"], report["errors"]
        assert report["normalized"]["changes"]["production_level"] == level

    @pytest.mark.parametrize("country", ["caribe", "mirage", "persia", "sarmatia", "solaria"])
    def test_all_5_opec_members_accepted(self, country):
        report = validate_opec_decision(_base(country=country))
        assert report["valid"], report["errors"]
        assert report["normalized"]["country_code"] == country

    def test_country_code_lowercased(self):
        report = validate_opec_decision(_base(country="SOLARIA"))
        assert report["valid"], report["errors"]
        assert report["normalized"]["country_code"] == "solaria"

    def test_level_lowercased(self):
        payload = _base()
        payload["changes"] = {"production_level": "MAX"}
        report = validate_opec_decision(payload)
        assert report["valid"], report["errors"]
        assert report["normalized"]["changes"]["production_level"] == "max"

    def test_rationale_trimmed(self):
        payload = _base()
        payload["rationale"] = "  " + VALID_RATIONALE + "   "
        report = validate_opec_decision(payload)
        assert report["valid"]
        assert report["normalized"]["rationale"] == VALID_RATIONALE


# ---------------------------------------------------------------------------
# Structural errors
# ---------------------------------------------------------------------------


class TestInvalidPayload:
    def test_none(self):
        report = validate_opec_decision(None)  # type: ignore[arg-type]
        assert _has_code(report, "INVALID_PAYLOAD")

    def test_string(self):
        report = validate_opec_decision("nope")  # type: ignore[arg-type]
        assert _has_code(report, "INVALID_PAYLOAD")


class TestInvalidActionType:
    def test_wrong(self):
        assert _has_code(validate_opec_decision(_base(action_type="set_oil")), "INVALID_ACTION_TYPE")

    def test_missing(self):
        payload = _base()
        del payload["action_type"]
        assert _has_code(validate_opec_decision(payload), "INVALID_ACTION_TYPE")


class TestInvalidDecision:
    def test_unknown_value(self):
        assert _has_code(validate_opec_decision(_base(decision="maybe")), "INVALID_DECISION")

    def test_missing(self):
        payload = _base()
        del payload["decision"]
        assert _has_code(validate_opec_decision(payload), "INVALID_DECISION")


class TestRationale:
    def test_missing(self):
        payload = _base()
        del payload["rationale"]
        assert _has_code(validate_opec_decision(payload), "RATIONALE_TOO_SHORT")

    def test_short(self):
        assert _has_code(validate_opec_decision(_base(rationale="too short")), "RATIONALE_TOO_SHORT")

    def test_exactly_min_is_valid(self):
        report = validate_opec_decision(_base(rationale="x" * RATIONALE_MIN_CHARS))
        assert report["valid"], report["errors"]

    def test_one_under_min_invalid(self):
        assert _has_code(
            validate_opec_decision(_base(rationale="x" * (RATIONALE_MIN_CHARS - 1))),
            "RATIONALE_TOO_SHORT",
        )

    def test_non_string(self):
        assert _has_code(validate_opec_decision(_base(rationale=123)), "RATIONALE_TOO_SHORT")


# ---------------------------------------------------------------------------
# Changes presence rules
# ---------------------------------------------------------------------------


class TestChangesRules:
    def test_change_without_changes(self):
        payload = _base()
        del payload["changes"]
        assert _has_code(validate_opec_decision(payload), "MISSING_CHANGES")

    def test_change_with_null_changes(self):
        payload = _base()
        payload["changes"] = None
        assert _has_code(validate_opec_decision(payload), "MISSING_CHANGES")

    def test_changes_not_a_dict(self):
        payload = _base()
        payload["changes"] = "min"
        assert _has_code(validate_opec_decision(payload), "MISSING_CHANGES")

    def test_no_change_with_changes(self):
        payload = _base(decision="no_change")
        payload["changes"] = {"production_level": "min"}
        assert _has_code(validate_opec_decision(payload), "UNEXPECTED_CHANGES")


# ---------------------------------------------------------------------------
# Unknown fields
# ---------------------------------------------------------------------------


class TestUnknownFields:
    def test_extra_top_level(self):
        payload = _base()
        payload["garbage"] = "x"
        assert _has_code(validate_opec_decision(payload), "UNKNOWN_FIELD")

    def test_extra_changes_field(self):
        payload = _base()
        payload["changes"] = {"production_level": "min", "secret": "x"}
        assert _has_code(validate_opec_decision(payload), "UNKNOWN_FIELD")


# ---------------------------------------------------------------------------
# Invalid level
# ---------------------------------------------------------------------------


class TestInvalidLevel:
    def test_unknown_value(self):
        payload = _base()
        payload["changes"] = {"production_level": "flood"}
        assert _has_code(validate_opec_decision(payload), "INVALID_LEVEL")

    def test_numeric_level(self):
        payload = _base()
        payload["changes"] = {"production_level": 3}
        assert _has_code(validate_opec_decision(payload), "INVALID_LEVEL")

    def test_missing_level(self):
        payload = _base()
        payload["changes"] = {}
        assert _has_code(validate_opec_decision(payload), "INVALID_LEVEL")


# ---------------------------------------------------------------------------
# NOT_OPEC_MEMBER
# ---------------------------------------------------------------------------


class TestNotOpecMember:
    def test_columbia_rejected(self):
        assert _has_code(validate_opec_decision(_base(country="columbia")), "NOT_OPEC_MEMBER")

    def test_cathay_rejected(self):
        assert _has_code(validate_opec_decision(_base(country="cathay")), "NOT_OPEC_MEMBER")

    def test_missing_country_code(self):
        payload = _base()
        del payload["country_code"]
        assert _has_code(validate_opec_decision(payload), "NOT_OPEC_MEMBER")

    def test_all_non_members_rejected(self):
        non_members = {
            "albion", "bharata", "cathay", "choson", "columbia", "formosa",
            "freeland", "gallia", "hanguk", "levantia", "phrygia", "ponte",
            "ruthenia", "teutonia", "yamato",
        }
        for code in non_members:
            report = validate_opec_decision(_base(country=code))
            assert _has_code(report, "NOT_OPEC_MEMBER"), f"{code} should be rejected"


# ---------------------------------------------------------------------------
# Error accumulation
# ---------------------------------------------------------------------------


class TestErrorAccumulation:
    def test_multiple_errors_in_one_pass(self):
        payload = {
            "action_type": "wrong",
            "country_code": "columbia",
            "round_num": 3,
            "decision": "maybe",
            "rationale": "short",
            "changes": {"production_level": "flood", "extra": "x"},
            "junk": True,
        }
        report = validate_opec_decision(payload)
        codes = {e.split(":", 1)[0] for e in report["errors"]}
        assert {"INVALID_ACTION_TYPE", "NOT_OPEC_MEMBER", "INVALID_DECISION",
                "RATIONALE_TOO_SHORT", "UNKNOWN_FIELD", "INVALID_LEVEL"} <= codes


# ---------------------------------------------------------------------------
# Normalized output
# ---------------------------------------------------------------------------


class TestNormalized:
    def test_normalized_shape_change(self):
        report = validate_opec_decision(_base())
        assert set(report["normalized"].keys()) == {
            "action_type", "country_code", "round_num",
            "decision", "rationale", "changes",
        }

    def test_normalized_shape_no_change(self):
        report = validate_opec_decision(_base(decision="no_change"))
        assert set(report["normalized"].keys()) == {
            "action_type", "country_code", "round_num",
            "decision", "rationale",
        }
        assert "changes" not in report["normalized"]

    def test_valid_production_levels_constant(self):
        assert VALID_PRODUCTION_LEVELS == frozenset({"min", "low", "normal", "high", "max"})
