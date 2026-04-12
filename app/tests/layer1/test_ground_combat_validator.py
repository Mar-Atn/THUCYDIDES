"""L1 unit tests for engine/services/ground_combat_validator.py.

Pure tests — no DB. Build context dicts from fixtures and exercise every
error code in CONTRACT_GROUND_COMBAT v1.0 §4.
"""

from __future__ import annotations

import pytest

from engine.services.ground_combat_validator import validate_ground_attack


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _unit(code: str, country: str, utype: str, row: int | None, col: int | None,
          status: str = "active") -> dict:
    return {
        "unit_code": code,
        "country_code": country,
        "unit_type": utype,
        "global_row": row,
        "global_col": col,
        "status": status,
    }


def _zone(zone_type: str, owner: str | None = None) -> dict:
    return {"type": zone_type, "owner": owner}


@pytest.fixture
def base_world() -> dict:
    """Standard 4-country fixture: Cathay attacks Persia at (6,14) from (6,15)."""
    units = {
        # Cathay forces on (6,15)
        "cat_g_01": _unit("cat_g_01", "cathay", "ground", 6, 15),
        "cat_g_02": _unit("cat_g_02", "cathay", "ground", 6, 15),
        "cat_g_03": _unit("cat_g_03", "cathay", "ground", 6, 15),
        # Cathay reserves
        "cat_g_99": _unit("cat_g_99", "cathay", "ground", None, None, status="reserve"),
        # Persia defenders on (6,14)
        "per_g_01": _unit("per_g_01", "persia", "ground", 6, 14),
        "per_g_02": _unit("per_g_02", "persia", "ground", 6, 14),
        "per_a_01": _unit("per_a_01", "persia", "tactical_air", 6, 14),
        # Persia at (5,14) — also adjacent to source
        "per_g_03": _unit("per_g_03", "persia", "ground", 5, 14),
        # Sarmatia somewhere far
        "sar_g_01": _unit("sar_g_01", "sarmatia", "ground", 2, 11),
        # Cathay tactical air at (6,15) — wrong unit type for ground attack
        "cat_a_01": _unit("cat_a_01", "cathay", "tactical_air", 6, 15),
    }
    zones = {
        (6, 15): _zone("land", "cathay"),
        (6, 14): _zone("land", "persia"),
        (5, 14): _zone("land", "persia"),
        (5, 15): _zone("land", "cathay"),
        (7, 15): _zone("land", "cathay"),
        (6, 16): _zone("sea", None),  # sea hex used for SEA test
        (4, 5): _zone("sea", None),
        (2, 11): _zone("land", "sarmatia"),
    }
    country_state = {
        "cathay": {"stability": 7, "ai_level": 2},
        "persia": {"stability": 6, "ai_level": 2},
    }
    return {"units": units, "zones": zones, "country_state": country_state}


def _good_payload() -> dict:
    return {
        "action_type": "attack_ground",
        "country_code": "cathay",
        "round_num": 3,
        "decision": "change",
        "rationale": "Punishing Persian incursion at the eastern border with 3 ground units",
        "changes": {
            "source_global_row": 6,
            "source_global_col": 15,
            "target_global_row": 6,
            "target_global_col": 14,
            "attacker_unit_codes": ["cat_g_01", "cat_g_02", "cat_g_03"],
        },
    }


def _validate(payload: dict, world: dict) -> dict:
    return validate_ground_attack(
        payload, world["units"], world["country_state"], world["zones"]
    )


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


class TestHappyPath:
    def test_valid_change(self, base_world):
        result = _validate(_good_payload(), base_world)
        assert result["valid"], result["errors"]
        norm = result["normalized"]
        assert norm["action_type"] == "attack_ground"
        assert norm["country_code"] == "cathay"
        assert norm["decision"] == "change"
        assert norm["changes"]["attacker_unit_codes"] == ["cat_g_01", "cat_g_02", "cat_g_03"]
        assert norm["changes"]["allow_chain"] is True

    def test_valid_no_change(self, base_world):
        payload = {
            "action_type": "attack_ground",
            "country_code": "cathay",
            "round_num": 3,
            "decision": "no_change",
            "rationale": "Holding the line - not initiating ground combat this round",
        }
        result = _validate(payload, base_world)
        assert result["valid"], result["errors"]
        assert result["normalized"]["decision"] == "no_change"
        assert "changes" not in result["normalized"]

    def test_normalized_dedups_and_sorts_attackers(self, base_world):
        payload = _good_payload()
        payload["changes"]["attacker_unit_codes"] = ["cat_g_03", "cat_g_01", "cat_g_02"]
        result = _validate(payload, base_world)
        assert result["valid"]
        assert result["normalized"]["changes"]["attacker_unit_codes"] == [
            "cat_g_01", "cat_g_02", "cat_g_03"
        ]

    def test_allow_chain_default_true(self, base_world):
        payload = _good_payload()
        # No allow_chain specified
        result = _validate(payload, base_world)
        assert result["normalized"]["changes"]["allow_chain"] is True

    def test_allow_chain_explicit_false(self, base_world):
        payload = _good_payload()
        payload["changes"]["allow_chain"] = False
        result = _validate(payload, base_world)
        assert result["valid"]
        assert result["normalized"]["changes"]["allow_chain"] is False


# ---------------------------------------------------------------------------
# Top-level structural errors
# ---------------------------------------------------------------------------


class TestStructural:
    def test_invalid_payload_type(self, base_world):
        result = _validate("not a dict", base_world)  # type: ignore
        assert not result["valid"]
        assert any("INVALID_PAYLOAD" in e for e in result["errors"])

    def test_invalid_action_type(self, base_world):
        p = _good_payload()
        p["action_type"] = "move_units"
        assert any("INVALID_ACTION_TYPE" in e for e in _validate(p, base_world)["errors"])

    def test_invalid_decision(self, base_world):
        p = _good_payload()
        p["decision"] = "maybe"
        assert any("INVALID_DECISION" in e for e in _validate(p, base_world)["errors"])

    def test_rationale_too_short(self, base_world):
        p = _good_payload()
        p["rationale"] = "too short"
        assert any("RATIONALE_TOO_SHORT" in e for e in _validate(p, base_world)["errors"])

    def test_unknown_top_field(self, base_world):
        p = _good_payload()
        p["mystery"] = "field"
        assert any("UNKNOWN_FIELD" in e for e in _validate(p, base_world)["errors"])

    def test_unknown_country(self, base_world):
        p = _good_payload()
        p["country_code"] = "atlantis"
        assert any("UNKNOWN_FIELD" in e for e in _validate(p, base_world)["errors"])


# ---------------------------------------------------------------------------
# Decision branch errors
# ---------------------------------------------------------------------------


class TestDecisionBranches:
    def test_change_missing_changes(self, base_world):
        p = _good_payload()
        del p["changes"]
        assert any("MISSING_CHANGES" in e for e in _validate(p, base_world)["errors"])

    def test_no_change_with_changes(self, base_world):
        p = {
            "action_type": "attack_ground",
            "country_code": "cathay",
            "round_num": 3,
            "decision": "no_change",
            "rationale": "Not attacking this round, but here's some bogus changes data",
            "changes": {"target_global_row": 6, "target_global_col": 14},
        }
        assert any("UNEXPECTED_CHANGES" in e for e in _validate(p, base_world)["errors"])

    def test_unknown_changes_field(self, base_world):
        p = _good_payload()
        p["changes"]["mystery"] = 42
        assert any("UNKNOWN_FIELD" in e for e in _validate(p, base_world)["errors"])


# ---------------------------------------------------------------------------
# Coordinate errors
# ---------------------------------------------------------------------------


class TestCoordinates:
    def test_missing_coords(self, base_world):
        p = _good_payload()
        del p["changes"]["target_global_row"]
        assert any("MISSING_COORDS" in e for e in _validate(p, base_world)["errors"])

    def test_bad_coords_out_of_range(self, base_world):
        p = _good_payload()
        p["changes"]["target_global_row"] = 99
        assert any("BAD_COORDS" in e for e in _validate(p, base_world)["errors"])

    def test_bad_coords_negative(self, base_world):
        p = _good_payload()
        p["changes"]["source_global_col"] = -1
        assert any("BAD_COORDS" in e for e in _validate(p, base_world)["errors"])

    def test_bad_coords_bool(self, base_world):
        p = _good_payload()
        p["changes"]["target_global_row"] = True  # bool is not int per validator
        assert any("BAD_COORDS" in e for e in _validate(p, base_world)["errors"])

    def test_same_hex(self, base_world):
        p = _good_payload()
        p["changes"]["target_global_row"] = 6
        p["changes"]["target_global_col"] = 15
        assert any("SAME_HEX" in e for e in _validate(p, base_world)["errors"])

    def test_not_adjacent(self, base_world):
        p = _good_payload()
        p["changes"]["target_global_row"] = 2
        p["changes"]["target_global_col"] = 11
        assert any("NOT_ADJACENT" in e for e in _validate(p, base_world)["errors"])

    def test_diagonal_not_adjacent(self, base_world):
        p = _good_payload()
        # (6,15) → (7,14) is diagonal, NOT cardinal
        p["changes"]["target_global_row"] = 7
        p["changes"]["target_global_col"] = 14
        assert any("NOT_ADJACENT" in e for e in _validate(p, base_world)["errors"])


# ---------------------------------------------------------------------------
# Attacker list errors
# ---------------------------------------------------------------------------


class TestAttackerList:
    def test_empty_attacker_list(self, base_world):
        p = _good_payload()
        p["changes"]["attacker_unit_codes"] = []
        assert any("EMPTY_ATTACKER_LIST" in e for e in _validate(p, base_world)["errors"])

    def test_unknown_unit(self, base_world):
        p = _good_payload()
        p["changes"]["attacker_unit_codes"] = ["cat_g_01", "cat_unknown"]
        assert any("UNKNOWN_UNIT" in e for e in _validate(p, base_world)["errors"])

    def test_not_own_unit(self, base_world):
        p = _good_payload()
        p["changes"]["attacker_unit_codes"] = ["cat_g_01", "per_g_01"]
        assert any("NOT_OWN_UNIT" in e for e in _validate(p, base_world)["errors"])

    def test_wrong_unit_type(self, base_world):
        p = _good_payload()
        p["changes"]["attacker_unit_codes"] = ["cat_g_01", "cat_a_01"]
        assert any("WRONG_UNIT_TYPE" in e for e in _validate(p, base_world)["errors"])

    def test_unit_not_active(self, base_world):
        p = _good_payload()
        p["changes"]["attacker_unit_codes"] = ["cat_g_99"]  # status=reserve
        assert any("UNIT_NOT_ACTIVE" in e for e in _validate(p, base_world)["errors"])

    def test_unit_not_on_source(self, base_world):
        # Move cat_g_03 to a different hex
        base_world["units"]["cat_g_03"]["global_row"] = 5
        base_world["units"]["cat_g_03"]["global_col"] = 15
        p = _good_payload()
        assert any("UNIT_NOT_ON_SOURCE" in e for e in _validate(p, base_world)["errors"])

    def test_duplicate_attacker(self, base_world):
        p = _good_payload()
        p["changes"]["attacker_unit_codes"] = ["cat_g_01", "cat_g_01", "cat_g_02"]
        assert any("DUPLICATE_ATTACKER" in e for e in _validate(p, base_world)["errors"])


# ---------------------------------------------------------------------------
# Target hex errors
# ---------------------------------------------------------------------------


class TestTargetHex:
    def test_target_hex_sea(self, base_world):
        p = _good_payload()
        # Re-route attack to (6,16) which is sea
        p["changes"]["target_global_row"] = 6
        p["changes"]["target_global_col"] = 16
        assert any("TARGET_HEX_SEA" in e for e in _validate(p, base_world)["errors"])

    def test_target_friendly_no_enemies(self, base_world):
        p = _good_payload()
        # Re-route to (5,15) which is land/cathay-owned but has no units
        p["changes"]["target_global_row"] = 5
        p["changes"]["target_global_col"] = 15
        assert any("TARGET_FRIENDLY" in e for e in _validate(p, base_world)["errors"])


# ---------------------------------------------------------------------------
# Min-leave-behind on foreign source hex
# ---------------------------------------------------------------------------


class TestMinLeaveBehind:
    def test_foreign_source_must_leave_one(self, base_world):
        # Move cat_g_01..03 onto sarmatia's hex (2,11) — foreign for cathay
        for code in ("cat_g_01", "cat_g_02", "cat_g_03"):
            base_world["units"][code]["global_row"] = 2
            base_world["units"][code]["global_col"] = 11
        # Add target enemy at adjacent (2,12)
        base_world["units"]["sar_g_02"] = _unit("sar_g_02", "sarmatia", "ground", 2, 12)
        base_world["zones"][(2, 12)] = _zone("land", "sarmatia")
        # Source (2,11) is sarmatia owned (foreign for cathay), all 3 grounds committed → leaves 0
        p = _good_payload()
        p["changes"]["source_global_row"] = 2
        p["changes"]["source_global_col"] = 11
        p["changes"]["target_global_row"] = 2
        p["changes"]["target_global_col"] = 12
        assert any("MIN_LEAVE_BEHIND" in e for e in _validate(p, base_world)["errors"])

    def test_own_source_can_be_emptied(self, base_world):
        # cathay attacks from own (6,15) committing all 3 grounds; remaining 0 is OK on own land
        p = _good_payload()
        result = _validate(p, base_world)
        assert result["valid"], result["errors"]


# ---------------------------------------------------------------------------
# Multiple errors collected
# ---------------------------------------------------------------------------


def test_multiple_errors_collected_in_one_pass(base_world):
    """Validator collects ALL errors, not just the first."""
    p = _good_payload()
    p["action_type"] = "wrong_action"  # err 1
    p["rationale"] = "x"  # err 2
    p["changes"]["attacker_unit_codes"] = []  # err 3
    result = _validate(p, base_world)
    assert not result["valid"]
    assert len(result["errors"]) >= 3
