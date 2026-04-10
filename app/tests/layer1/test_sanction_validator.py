"""Layer 1 tests — sanction decision validator per CONTRACT_SANCTIONS v1.0.

Run:
    cd app && PYTHONPATH=. python3 -m pytest tests/layer1/test_sanction_validator.py -v
"""

from __future__ import annotations

import pytest

from engine.services.sanction_validator import (
    CANONICAL_COUNTRIES,
    LEVEL_MAX,
    LEVEL_MIN,
    RATIONALE_MIN_CHARS,
    validate_sanctions_decision,
)

# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------


VALID_RATIONALE = "Maintaining maximum coalition pressure on Persia during active war."  # 65 chars


def _base(decision: str = "change", **overrides) -> dict:
    """Build a minimal valid payload that we can mutate per test."""
    payload = {
        "action_type": "set_sanctions",
        "country_code": "columbia",
        "round_num": 3,
        "decision": decision,
        "rationale": VALID_RATIONALE,
    }
    if decision == "change":
        payload["changes"] = {"sanctions": {"persia": 3}}
    payload.update(overrides)
    return payload


def _has_code(report: dict, code: str) -> bool:
    return any(e.startswith(code) for e in report["errors"])


# ===========================================================================
# 1. HAPPY PATH — VALID DECISIONS
# ===========================================================================


class TestHappyPath:
    def test_minimal_valid_change(self):
        report = validate_sanctions_decision(_base(decision="change"))
        assert report["valid"], report["errors"]
        assert report["normalized"]["decision"] == "change"
        assert report["normalized"]["changes"]["sanctions"] == {"persia": 3}

    def test_minimal_valid_no_change(self):
        report = validate_sanctions_decision(_base(decision="no_change"))
        assert report["valid"], report["errors"]
        assert report["normalized"]["decision"] == "no_change"
        assert "changes" not in report["normalized"]

    def test_multiple_targets_valid(self):
        payload = _base()
        payload["changes"] = {"sanctions": {
            "persia": 3, "choson": 3, "sarmatia": 2, "bharata": 0,
        }}
        report = validate_sanctions_decision(payload)
        assert report["valid"], report["errors"]
        assert report["normalized"]["changes"]["sanctions"] == {
            "persia": 3, "choson": 3, "sarmatia": 2, "bharata": 0,
        }

    def test_level_zero_means_lift_is_valid(self):
        payload = _base()
        payload["changes"] = {"sanctions": {"persia": 0}}
        report = validate_sanctions_decision(payload)
        assert report["valid"], report["errors"]
        assert report["normalized"]["changes"]["sanctions"]["persia"] == 0

    def test_negative_level_evasion_support_valid(self):
        """Negative levels are explicitly allowed — evasion support."""
        payload = _base(country_code="cathay")
        payload["changes"] = {"sanctions": {"sarmatia": -2}}
        report = validate_sanctions_decision(payload)
        assert report["valid"], report["errors"]
        assert report["normalized"]["changes"]["sanctions"]["sarmatia"] == -2

    def test_mixed_positive_and_negative_levels(self):
        payload = _base(country_code="cathay")
        payload["changes"] = {"sanctions": {
            "sarmatia": -3,   # evasion support for Sarmatia
            "choson": 1,      # light sanctions on Choson
        }}
        report = validate_sanctions_decision(payload)
        assert report["valid"], report["errors"]

    def test_country_code_lowercased(self):
        payload = _base()
        payload["country_code"] = "COLUMBIA"
        payload["changes"] = {"sanctions": {"PERSIA": 3}}
        report = validate_sanctions_decision(payload)
        assert report["valid"], report["errors"]
        assert report["normalized"]["country_code"] == "columbia"
        assert "persia" in report["normalized"]["changes"]["sanctions"]

    def test_rationale_trimmed(self):
        payload = _base()
        payload["rationale"] = "  " + VALID_RATIONALE + "   "
        report = validate_sanctions_decision(payload)
        assert report["valid"]
        assert report["normalized"]["rationale"] == VALID_RATIONALE

    def test_normalized_omits_unknown_fields(self):
        payload = _base()
        report = validate_sanctions_decision(payload)
        assert report["valid"]
        assert set(report["normalized"].keys()) == {
            "action_type", "country_code", "round_num", "decision",
            "rationale", "changes",
        }


# ===========================================================================
# 2. STRUCTURAL ERRORS
# ===========================================================================


class TestInvalidPayload:
    def test_none_payload(self):
        report = validate_sanctions_decision(None)  # type: ignore[arg-type]
        assert not report["valid"]
        assert _has_code(report, "INVALID_PAYLOAD")

    def test_string_payload(self):
        report = validate_sanctions_decision("not a dict")  # type: ignore[arg-type]
        assert not report["valid"]
        assert _has_code(report, "INVALID_PAYLOAD")


class TestInvalidActionType:
    def test_wrong_action_type(self):
        report = validate_sanctions_decision(_base(action_type="set_sanction"))
        assert not report["valid"]
        assert _has_code(report, "INVALID_ACTION_TYPE")

    def test_missing_action_type(self):
        payload = _base()
        del payload["action_type"]
        report = validate_sanctions_decision(payload)
        assert not report["valid"]
        assert _has_code(report, "INVALID_ACTION_TYPE")


class TestInvalidDecision:
    def test_unknown_decision_value(self):
        report = validate_sanctions_decision(_base(decision="maybe"))
        assert not report["valid"]
        assert _has_code(report, "INVALID_DECISION")

    def test_missing_decision(self):
        payload = _base()
        del payload["decision"]
        report = validate_sanctions_decision(payload)
        assert not report["valid"]
        assert _has_code(report, "INVALID_DECISION")


class TestRationale:
    def test_missing_rationale(self):
        payload = _base()
        del payload["rationale"]
        report = validate_sanctions_decision(payload)
        assert not report["valid"]
        assert _has_code(report, "RATIONALE_TOO_SHORT")

    def test_short_rationale(self):
        report = validate_sanctions_decision(_base(rationale="too short"))
        assert not report["valid"]
        assert _has_code(report, "RATIONALE_TOO_SHORT")

    def test_exactly_min_chars_is_valid(self):
        rationale = "x" * RATIONALE_MIN_CHARS
        report = validate_sanctions_decision(_base(rationale=rationale))
        assert report["valid"], report["errors"]

    def test_one_under_min_invalid(self):
        rationale = "x" * (RATIONALE_MIN_CHARS - 1)
        report = validate_sanctions_decision(_base(rationale=rationale))
        assert not report["valid"]
        assert _has_code(report, "RATIONALE_TOO_SHORT")

    def test_non_string_rationale(self):
        report = validate_sanctions_decision(_base(rationale=123))
        assert not report["valid"]
        assert _has_code(report, "RATIONALE_TOO_SHORT")


class TestMissingChanges:
    def test_change_without_changes_field(self):
        payload = _base()
        del payload["changes"]
        report = validate_sanctions_decision(payload)
        assert not report["valid"]
        assert _has_code(report, "MISSING_CHANGES")

    def test_change_with_null_changes(self):
        payload = _base()
        payload["changes"] = None
        report = validate_sanctions_decision(payload)
        assert not report["valid"]
        assert _has_code(report, "MISSING_CHANGES")

    def test_changes_not_a_dict(self):
        payload = _base()
        payload["changes"] = ["persia", 3]
        report = validate_sanctions_decision(payload)
        assert not report["valid"]
        assert _has_code(report, "MISSING_CHANGES")

    def test_changes_sanctions_not_a_dict(self):
        payload = _base()
        payload["changes"] = {"sanctions": [1, 2, 3]}
        report = validate_sanctions_decision(payload)
        assert not report["valid"]
        assert _has_code(report, "MISSING_CHANGES")


class TestUnexpectedChanges:
    def test_no_change_with_changes_field(self):
        payload = _base(decision="no_change")
        payload["changes"] = {"sanctions": {"persia": 2}}
        report = validate_sanctions_decision(payload)
        assert not report["valid"]
        assert _has_code(report, "UNEXPECTED_CHANGES")


class TestEmptyChanges:
    def test_change_with_empty_sanctions(self):
        payload = _base()
        payload["changes"] = {"sanctions": {}}
        report = validate_sanctions_decision(payload)
        assert not report["valid"]
        assert _has_code(report, "EMPTY_CHANGES")


# ===========================================================================
# 3. UNKNOWN FIELDS
# ===========================================================================


class TestUnknownFields:
    def test_extra_top_level_field(self):
        payload = _base()
        payload["extra_thing"] = "nope"
        report = validate_sanctions_decision(payload)
        assert not report["valid"]
        assert _has_code(report, "UNKNOWN_FIELD")

    def test_extra_changes_field(self):
        payload = _base()
        payload["changes"] = {"sanctions": {"persia": 1}, "secret": "x"}
        report = validate_sanctions_decision(payload)
        assert not report["valid"]
        assert _has_code(report, "UNKNOWN_FIELD")


# ===========================================================================
# 4. LEVEL VALIDATION — signed range [-3, +3]
# ===========================================================================


class TestInvalidLevel:
    def test_level_too_high(self):
        payload = _base()
        payload["changes"] = {"sanctions": {"persia": 5}}
        report = validate_sanctions_decision(payload)
        assert not report["valid"]
        assert _has_code(report, "INVALID_LEVEL")

    def test_level_too_low(self):
        payload = _base()
        payload["changes"] = {"sanctions": {"persia": -5}}
        report = validate_sanctions_decision(payload)
        assert not report["valid"]
        assert _has_code(report, "INVALID_LEVEL")

    def test_level_string(self):
        payload = _base()
        payload["changes"] = {"sanctions": {"persia": "high"}}
        report = validate_sanctions_decision(payload)
        assert not report["valid"]
        assert _has_code(report, "INVALID_LEVEL")

    def test_level_float(self):
        payload = _base()
        payload["changes"] = {"sanctions": {"persia": 2.5}}
        report = validate_sanctions_decision(payload)
        assert not report["valid"]
        assert _has_code(report, "INVALID_LEVEL")

    def test_level_bool_rejected(self):
        payload = _base()
        payload["changes"] = {"sanctions": {"persia": True}}
        report = validate_sanctions_decision(payload)
        assert not report["valid"]
        assert _has_code(report, "INVALID_LEVEL")

    def test_all_levels_minus3_to_plus3_valid(self):
        for lvl in (LEVEL_MIN, -2, -1, 0, 1, 2, LEVEL_MAX):
            payload = _base()
            payload["changes"] = {"sanctions": {"persia": lvl}}
            report = validate_sanctions_decision(payload)
            assert report["valid"], f"level {lvl}: {report['errors']}"


# ===========================================================================
# 5. UNKNOWN TARGET
# ===========================================================================


class TestUnknownTarget:
    def test_unknown_country(self):
        payload = _base()
        payload["changes"] = {"sanctions": {"atlantis": 2}}
        report = validate_sanctions_decision(payload)
        assert not report["valid"]
        assert _has_code(report, "UNKNOWN_TARGET")

    def test_empty_target_string(self):
        payload = _base()
        payload["changes"] = {"sanctions": {"": 2}}
        report = validate_sanctions_decision(payload)
        assert not report["valid"]
        assert _has_code(report, "UNKNOWN_TARGET")

    def test_all_canonical_countries_accepted(self):
        for cc in CANONICAL_COUNTRIES:
            if cc == "columbia":
                continue  # self-sanction
            payload = _base()
            payload["changes"] = {"sanctions": {cc: 1}}
            report = validate_sanctions_decision(payload)
            assert report["valid"], f"{cc}: {report['errors']}"


# ===========================================================================
# 6. SELF-SANCTION
# ===========================================================================


class TestSelfSanction:
    def test_self_sanction_rejected(self):
        payload = _base()  # actor=columbia
        payload["changes"] = {"sanctions": {"columbia": 2}}
        report = validate_sanctions_decision(payload)
        assert not report["valid"]
        assert _has_code(report, "SELF_SANCTION")

    def test_self_evasion_also_rejected(self):
        payload = _base()
        payload["changes"] = {"sanctions": {"columbia": -2}}
        report = validate_sanctions_decision(payload)
        assert not report["valid"]
        assert _has_code(report, "SELF_SANCTION")

    def test_self_in_mixed_targets(self):
        payload = _base()
        payload["changes"] = {"sanctions": {"persia": 3, "columbia": 1}}
        report = validate_sanctions_decision(payload)
        assert not report["valid"]
        assert _has_code(report, "SELF_SANCTION")


# ===========================================================================
# 7. ERROR ACCUMULATION — multiple errors in one pass
# ===========================================================================


class TestErrorAccumulation:
    def test_multiple_errors_collected(self):
        payload = {
            "action_type": "wrong",
            "country_code": "columbia",
            "round_num": 3,
            "decision": "maybe",
            "rationale": "short",
            "changes": {"sanctions": {"atlantis": 99, "columbia": 2}},
            "garbage": "x",
        }
        report = validate_sanctions_decision(payload)
        assert not report["valid"]
        codes = {e.split(":", 1)[0] for e in report["errors"]}
        expected = {
            "INVALID_ACTION_TYPE",
            "INVALID_DECISION",
            "RATIONALE_TOO_SHORT",
            "UNKNOWN_FIELD",
            "UNKNOWN_TARGET",
            "INVALID_LEVEL",
            "SELF_SANCTION",
        }
        missing = expected - codes
        assert not missing, f"Missing codes from accumulated report: {missing}"


# ===========================================================================
# 8. NORMALIZED OUTPUT INTEGRITY
# ===========================================================================


class TestNormalized:
    def test_normalized_omits_changes_on_no_change(self):
        payload = _base(decision="no_change")
        report = validate_sanctions_decision(payload)
        assert report["valid"]
        assert "changes" not in report["normalized"]

    def test_normalized_levels_are_ints(self):
        payload = _base()
        payload["changes"] = {"sanctions": {"persia": 2, "sarmatia": -1}}
        report = validate_sanctions_decision(payload)
        assert report["valid"]
        for v in report["normalized"]["changes"]["sanctions"].values():
            assert isinstance(v, int)

    def test_normalized_round_num_preserved(self):
        report = validate_sanctions_decision(_base(round_num=42))
        assert report["valid"]
        assert report["normalized"]["round_num"] == 42
