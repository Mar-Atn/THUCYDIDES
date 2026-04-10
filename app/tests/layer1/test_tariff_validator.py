"""Layer 1 tests — tariff decision validator per CONTRACT_TARIFFS v1.0.

Run:
    cd app && PYTHONPATH=. python3 -m pytest tests/layer1/test_tariff_validator.py -v
"""

from __future__ import annotations

import pytest

from engine.services.tariff_validator import (
    CANONICAL_COUNTRIES,
    LEVEL_MAX,
    LEVEL_MIN,
    RATIONALE_MIN_CHARS,
    validate_tariffs_decision,
)

# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------


VALID_RATIONALE = "Escalating economic pressure on Cathay in coordination with EU."  # 65 chars


def _base(decision: str = "change", **overrides) -> dict:
    """Build a minimal valid payload that we can mutate per test."""
    payload = {
        "action_type": "set_tariffs",
        "country_code": "columbia",
        "round_num": 3,
        "decision": decision,
        "rationale": VALID_RATIONALE,
    }
    if decision == "change":
        payload["changes"] = {"tariffs": {"cathay": 3}}
    payload.update(overrides)
    return payload


def _has_code(report: dict, code: str) -> bool:
    return any(e.startswith(code) for e in report["errors"])


# ===========================================================================
# 1. HAPPY PATH — VALID DECISIONS
# ===========================================================================


class TestHappyPath:
    def test_minimal_valid_change(self):
        report = validate_tariffs_decision(_base(decision="change"))
        assert report["valid"], report["errors"]
        assert report["normalized"]["decision"] == "change"
        assert report["normalized"]["changes"]["tariffs"] == {"cathay": 3}

    def test_minimal_valid_no_change(self):
        payload = _base(decision="no_change")
        # _base() omits 'changes' for no_change — that is the valid shape
        report = validate_tariffs_decision(payload)
        assert report["valid"], report["errors"]
        assert report["normalized"]["decision"] == "no_change"
        assert "changes" not in report["normalized"]

    def test_multiple_targets_valid(self):
        payload = _base()
        payload["changes"] = {"tariffs": {
            "cathay": 3, "persia": 2, "caribe": 0, "sarmatia": 1,
        }}
        report = validate_tariffs_decision(payload)
        assert report["valid"], report["errors"]
        assert report["normalized"]["changes"]["tariffs"] == {
            "cathay": 3, "persia": 2, "caribe": 0, "sarmatia": 1,
        }

    def test_level_zero_means_lift_is_valid(self):
        payload = _base()
        payload["changes"] = {"tariffs": {"cathay": 0}}
        report = validate_tariffs_decision(payload)
        assert report["valid"], report["errors"]
        assert report["normalized"]["changes"]["tariffs"]["cathay"] == 0

    def test_country_code_lowercased(self):
        payload = _base()
        payload["country_code"] = "COLUMBIA"
        payload["changes"] = {"tariffs": {"CATHAY": 2}}
        report = validate_tariffs_decision(payload)
        assert report["valid"], report["errors"]
        assert report["normalized"]["country_code"] == "columbia"
        assert "cathay" in report["normalized"]["changes"]["tariffs"]

    def test_rationale_trimmed(self):
        payload = _base()
        payload["rationale"] = "  " + VALID_RATIONALE + "   "
        report = validate_tariffs_decision(payload)
        assert report["valid"]
        assert report["normalized"]["rationale"] == VALID_RATIONALE

    def test_normalized_omits_unknown_fields(self):
        payload = _base()
        # only allowed fields produce a clean normalized; unknown fields are
        # rejected (verified in error tests). Verify normalized has only the
        # canonical keys.
        report = validate_tariffs_decision(payload)
        assert report["valid"]
        assert set(report["normalized"].keys()) == {
            "action_type", "country_code", "round_num", "decision",
            "rationale", "changes",
        }


# ===========================================================================
# 2. STRUCTURAL ERRORS (codes 1-7)
# ===========================================================================


class TestInvalidPayload:
    def test_none_payload(self):
        report = validate_tariffs_decision(None)  # type: ignore[arg-type]
        assert not report["valid"]
        assert _has_code(report, "INVALID_PAYLOAD")

    def test_string_payload(self):
        report = validate_tariffs_decision("not a dict")  # type: ignore[arg-type]
        assert not report["valid"]
        assert _has_code(report, "INVALID_PAYLOAD")


class TestInvalidActionType:
    def test_wrong_action_type(self):
        report = validate_tariffs_decision(_base(action_type="set_tariff"))
        assert not report["valid"]
        assert _has_code(report, "INVALID_ACTION_TYPE")

    def test_missing_action_type(self):
        payload = _base()
        del payload["action_type"]
        report = validate_tariffs_decision(payload)
        assert not report["valid"]
        assert _has_code(report, "INVALID_ACTION_TYPE")


class TestInvalidDecision:
    def test_unknown_decision_value(self):
        report = validate_tariffs_decision(_base(decision="maybe"))
        assert not report["valid"]
        assert _has_code(report, "INVALID_DECISION")

    def test_missing_decision(self):
        payload = _base()
        del payload["decision"]
        report = validate_tariffs_decision(payload)
        assert not report["valid"]
        assert _has_code(report, "INVALID_DECISION")


class TestRationale:
    def test_missing_rationale(self):
        payload = _base()
        del payload["rationale"]
        report = validate_tariffs_decision(payload)
        assert not report["valid"]
        assert _has_code(report, "RATIONALE_TOO_SHORT")

    def test_short_rationale(self):
        report = validate_tariffs_decision(_base(rationale="too short"))
        assert not report["valid"]
        assert _has_code(report, "RATIONALE_TOO_SHORT")

    def test_exactly_min_chars_is_valid(self):
        rationale = "x" * RATIONALE_MIN_CHARS
        report = validate_tariffs_decision(_base(rationale=rationale))
        assert report["valid"], report["errors"]

    def test_one_under_min_invalid(self):
        rationale = "x" * (RATIONALE_MIN_CHARS - 1)
        report = validate_tariffs_decision(_base(rationale=rationale))
        assert not report["valid"]
        assert _has_code(report, "RATIONALE_TOO_SHORT")

    def test_non_string_rationale(self):
        report = validate_tariffs_decision(_base(rationale=123))
        assert not report["valid"]
        assert _has_code(report, "RATIONALE_TOO_SHORT")


class TestMissingChanges:
    def test_change_without_changes_field(self):
        payload = _base()
        del payload["changes"]
        report = validate_tariffs_decision(payload)
        assert not report["valid"]
        assert _has_code(report, "MISSING_CHANGES")

    def test_change_with_null_changes(self):
        payload = _base()
        payload["changes"] = None
        report = validate_tariffs_decision(payload)
        assert not report["valid"]
        assert _has_code(report, "MISSING_CHANGES")

    def test_changes_not_a_dict(self):
        payload = _base()
        payload["changes"] = ["cathay", 3]
        report = validate_tariffs_decision(payload)
        assert not report["valid"]
        assert _has_code(report, "MISSING_CHANGES")

    def test_changes_tariffs_not_a_dict(self):
        payload = _base()
        payload["changes"] = {"tariffs": [1, 2, 3]}
        report = validate_tariffs_decision(payload)
        assert not report["valid"]
        assert _has_code(report, "MISSING_CHANGES")


class TestUnexpectedChanges:
    def test_no_change_with_changes_field(self):
        payload = _base(decision="no_change")
        # Deliberately add a changes field — this is the violation
        payload["changes"] = {"tariffs": {"cathay": 2}}
        report = validate_tariffs_decision(payload)
        assert not report["valid"]
        assert _has_code(report, "UNEXPECTED_CHANGES")


class TestEmptyChanges:
    def test_change_with_empty_tariffs(self):
        payload = _base()
        payload["changes"] = {"tariffs": {}}
        report = validate_tariffs_decision(payload)
        assert not report["valid"]
        assert _has_code(report, "EMPTY_CHANGES")


# ===========================================================================
# 3. UNKNOWN FIELDS
# ===========================================================================


class TestUnknownFields:
    def test_extra_top_level_field(self):
        payload = _base()
        payload["extra_thing"] = "nope"
        report = validate_tariffs_decision(payload)
        assert not report["valid"]
        assert _has_code(report, "UNKNOWN_FIELD")

    def test_extra_changes_field(self):
        payload = _base()
        payload["changes"] = {"tariffs": {"cathay": 1}, "secret": "x"}
        report = validate_tariffs_decision(payload)
        assert not report["valid"]
        assert _has_code(report, "UNKNOWN_FIELD")


# ===========================================================================
# 4. LEVEL VALIDATION
# ===========================================================================


class TestInvalidLevel:
    def test_level_too_high(self):
        payload = _base()
        payload["changes"] = {"tariffs": {"cathay": 5}}
        report = validate_tariffs_decision(payload)
        assert not report["valid"]
        assert _has_code(report, "INVALID_LEVEL")

    def test_level_negative(self):
        payload = _base()
        payload["changes"] = {"tariffs": {"cathay": -1}}
        report = validate_tariffs_decision(payload)
        assert not report["valid"]
        assert _has_code(report, "INVALID_LEVEL")

    def test_level_string(self):
        payload = _base()
        payload["changes"] = {"tariffs": {"cathay": "high"}}
        report = validate_tariffs_decision(payload)
        assert not report["valid"]
        assert _has_code(report, "INVALID_LEVEL")

    def test_level_float(self):
        payload = _base()
        payload["changes"] = {"tariffs": {"cathay": 2.5}}
        report = validate_tariffs_decision(payload)
        assert not report["valid"]
        assert _has_code(report, "INVALID_LEVEL")

    def test_level_bool_rejected(self):
        # bool is a subclass of int — must be rejected explicitly
        payload = _base()
        payload["changes"] = {"tariffs": {"cathay": True}}
        report = validate_tariffs_decision(payload)
        assert not report["valid"]
        assert _has_code(report, "INVALID_LEVEL")

    def test_all_levels_0_3_valid(self):
        for lvl in (LEVEL_MIN, 1, 2, LEVEL_MAX):
            payload = _base()
            payload["changes"] = {"tariffs": {"cathay": lvl}}
            report = validate_tariffs_decision(payload)
            assert report["valid"], f"level {lvl}: {report['errors']}"


# ===========================================================================
# 5. UNKNOWN TARGET
# ===========================================================================


class TestUnknownTarget:
    def test_unknown_country(self):
        payload = _base()
        payload["changes"] = {"tariffs": {"atlantis": 2}}
        report = validate_tariffs_decision(payload)
        assert not report["valid"]
        assert _has_code(report, "UNKNOWN_TARGET")

    def test_empty_target_string(self):
        payload = _base()
        payload["changes"] = {"tariffs": {"": 2}}
        report = validate_tariffs_decision(payload)
        assert not report["valid"]
        assert _has_code(report, "UNKNOWN_TARGET")

    def test_all_canonical_countries_accepted(self):
        for cc in CANONICAL_COUNTRIES:
            if cc == "columbia":
                continue  # self-tariff
            payload = _base()
            payload["changes"] = {"tariffs": {cc: 1}}
            report = validate_tariffs_decision(payload)
            assert report["valid"], f"{cc}: {report['errors']}"


# ===========================================================================
# 6. SELF-TARIFF
# ===========================================================================


class TestSelfTariff:
    def test_self_tariff_rejected(self):
        payload = _base()  # imposer=columbia
        payload["changes"] = {"tariffs": {"columbia": 2}}
        report = validate_tariffs_decision(payload)
        assert not report["valid"]
        assert _has_code(report, "SELF_TARIFF")

    def test_self_in_mixed_targets(self):
        payload = _base()
        payload["changes"] = {"tariffs": {"cathay": 2, "columbia": 1}}
        report = validate_tariffs_decision(payload)
        assert not report["valid"]
        assert _has_code(report, "SELF_TARIFF")
        # cathay portion would be valid but normalized is None on any error


# ===========================================================================
# 7. ACCUMULATION — multiple errors in one pass
# ===========================================================================


class TestErrorAccumulation:
    def test_multiple_errors_collected(self):
        payload = {
            "action_type": "wrong",
            "country_code": "columbia",
            "round_num": 3,
            "decision": "maybe",
            "rationale": "short",
            "changes": {"tariffs": {"atlantis": 5, "columbia": 2}},
            "garbage": "x",
        }
        report = validate_tariffs_decision(payload)
        assert not report["valid"]
        codes = {e.split(":", 1)[0] for e in report["errors"]}
        # Expect multiple distinct error codes in one pass
        expected = {
            "INVALID_ACTION_TYPE",
            "INVALID_DECISION",
            "RATIONALE_TOO_SHORT",
            "UNKNOWN_FIELD",
            "UNKNOWN_TARGET",
            "INVALID_LEVEL",
            "SELF_TARIFF",
        }
        missing = expected - codes
        assert not missing, f"Missing codes from accumulated report: {missing}"


# ===========================================================================
# 8. NORMALIZED OUTPUT INTEGRITY
# ===========================================================================


class TestNormalized:
    def test_normalized_omits_changes_on_no_change(self):
        payload = _base(decision="no_change")
        report = validate_tariffs_decision(payload)
        assert report["valid"]
        assert "changes" not in report["normalized"]

    def test_normalized_levels_are_ints(self):
        payload = _base()
        payload["changes"] = {"tariffs": {"cathay": 2}}
        report = validate_tariffs_decision(payload)
        assert report["valid"]
        assert isinstance(report["normalized"]["changes"]["tariffs"]["cathay"], int)

    def test_normalized_round_num_preserved(self):
        report = validate_tariffs_decision(_base(round_num=42))
        assert report["valid"]
        assert report["normalized"]["round_num"] == 42
