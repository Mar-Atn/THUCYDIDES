"""L1 unit tests for engine/services/air_strike_validator.py — CONTRACT_AIR_STRIKES v1.0."""

from __future__ import annotations

import pytest

from engine.services.air_strike_validator import validate_air_strike


def _unit(code, country, utype, row, col, status="active"):
    return {
        "unit_code": code,
        "country_code": country,
        "unit_type": utype,
        "global_row": row,
        "global_col": col,
        "status": status,
    }


@pytest.fixture
def base_world():
    units = {
        # Cathay tactical_air on (6,15)
        "cat_a_05": _unit("cat_a_05", "cathay", "tactical_air", 6, 15),
        "cat_a_06": _unit("cat_a_06", "cathay", "tactical_air", 6, 15),
        # Cathay ground on same hex (wrong type)
        "cat_g_01": _unit("cat_g_01", "cathay", "ground", 6, 15),
        # Cathay reserve air
        "cat_a_99": _unit("cat_a_99", "cathay", "tactical_air", None, None, status="reserve"),
        # Persia targets at (7,15) — distance 1
        "per_g_01": _unit("per_g_01", "persia", "ground", 7, 15),
        "per_g_02": _unit("per_g_02", "persia", "ground", 7, 15),
        # Persia at (8,15) — distance 2
        "per_g_03": _unit("per_g_03", "persia", "ground", 8, 15),
        # Sarmatia far away
        "sar_g_01": _unit("sar_g_01", "sarmatia", "ground", 1, 1),
    }
    zones = {(r, c): {"type": "land", "owner": None} for r in range(1, 11) for c in range(1, 21)}
    country_state = {
        "cathay": {"stability": 7, "ai_level": 2},
        "persia": {"stability": 6, "ai_level": 2},
    }
    return {"units": units, "zones": zones, "country_state": country_state}


def _good_payload():
    return {
        "action_type": "attack_air",
        "country_code": "cathay",
        "round_num": 3,
        "decision": "change",
        "rationale": "Striking persian ground forces with tactical air superiority",
        "changes": {
            "source_global_row": 6,
            "source_global_col": 15,
            "target_global_row": 7,
            "target_global_col": 15,
            "attacker_unit_codes": ["cat_a_05", "cat_a_06"],
        },
    }


def _validate(payload, world):
    return validate_air_strike(
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
        assert norm["action_type"] == "attack_air"
        assert norm["changes"]["attacker_unit_codes"] == ["cat_a_05", "cat_a_06"]

    def test_valid_no_change(self, base_world):
        payload = {
            "action_type": "attack_air",
            "country_code": "cathay",
            "round_num": 3,
            "decision": "no_change",
            "rationale": "Holding air assets in reserve - no priority targets visible this round",
        }
        result = _validate(payload, base_world)
        assert result["valid"], result["errors"]
        assert "changes" not in result["normalized"]

    def test_distance_2_hexes_allowed(self, base_world):
        p = _good_payload()
        p["changes"]["target_global_row"] = 8  # distance = 2
        p["changes"]["target_global_col"] = 15
        result = _validate(p, base_world)
        assert result["valid"], result["errors"]

    def test_dedup_attackers(self, base_world):
        p = _good_payload()
        p["changes"]["attacker_unit_codes"] = ["cat_a_06", "cat_a_05", "cat_a_06"]
        result = _validate(p, base_world)
        # Will have a DUPLICATE_ATTACKER error
        assert not result["valid"]
        assert any("DUPLICATE_ATTACKER" in e for e in result["errors"])


# ---------------------------------------------------------------------------
# Structural
# ---------------------------------------------------------------------------


class TestStructural:
    def test_invalid_payload(self, base_world):
        assert any("INVALID_PAYLOAD" in e for e in _validate("nope", base_world)["errors"])  # type: ignore

    def test_invalid_action_type(self, base_world):
        p = _good_payload()
        p["action_type"] = "attack_ground"
        assert any("INVALID_ACTION_TYPE" in e for e in _validate(p, base_world)["errors"])

    def test_invalid_decision(self, base_world):
        p = _good_payload()
        p["decision"] = "fire_at_will"
        assert any("INVALID_DECISION" in e for e in _validate(p, base_world)["errors"])

    def test_rationale_too_short(self, base_world):
        p = _good_payload()
        p["rationale"] = "short"
        assert any("RATIONALE_TOO_SHORT" in e for e in _validate(p, base_world)["errors"])

    def test_unknown_country(self, base_world):
        p = _good_payload()
        p["country_code"] = "atlantis"
        assert any("UNKNOWN_FIELD" in e for e in _validate(p, base_world)["errors"])


class TestDecisionBranches:
    def test_change_missing_changes(self, base_world):
        p = _good_payload()
        del p["changes"]
        assert any("MISSING_CHANGES" in e for e in _validate(p, base_world)["errors"])

    def test_no_change_with_changes(self, base_world):
        p = {
            "action_type": "attack_air",
            "country_code": "cathay",
            "round_num": 3,
            "decision": "no_change",
            "rationale": "Some legitimate sounding rationale that is more than thirty chars",
            "changes": {"source_global_row": 6, "source_global_col": 15},
        }
        assert any("UNEXPECTED_CHANGES" in e for e in _validate(p, base_world)["errors"])


class TestCoordinates:
    def test_missing_coords(self, base_world):
        p = _good_payload()
        del p["changes"]["target_global_row"]
        assert any("MISSING_COORDS" in e for e in _validate(p, base_world)["errors"])

    def test_bad_coords(self, base_world):
        p = _good_payload()
        p["changes"]["target_global_col"] = 99
        assert any("BAD_COORDS" in e for e in _validate(p, base_world)["errors"])

    def test_same_hex(self, base_world):
        p = _good_payload()
        p["changes"]["target_global_row"] = 6
        p["changes"]["target_global_col"] = 15
        assert any("SAME_HEX" in e for e in _validate(p, base_world)["errors"])

    def test_out_of_range(self, base_world):
        p = _good_payload()
        p["changes"]["target_global_row"] = 9  # distance 3 from (6,15)
        p["changes"]["target_global_col"] = 15
        assert any("OUT_OF_RANGE" in e for e in _validate(p, base_world)["errors"])

    def test_diagonal_within_range(self, base_world):
        # (6,15) → (7,16) is distance 2 (Manhattan)
        p = _good_payload()
        p["changes"]["target_global_row"] = 7
        p["changes"]["target_global_col"] = 16
        # Need an enemy at (7,16)
        base_world["units"]["per_g_x"] = _unit("per_g_x", "persia", "ground", 7, 16)
        result = _validate(p, base_world)
        assert result["valid"], result["errors"]


class TestAttackers:
    def test_empty_attacker_list(self, base_world):
        p = _good_payload()
        p["changes"]["attacker_unit_codes"] = []
        assert any("EMPTY_ATTACKER_LIST" in e for e in _validate(p, base_world)["errors"])

    def test_unknown_unit(self, base_world):
        p = _good_payload()
        p["changes"]["attacker_unit_codes"] = ["cat_a_05", "ghost_a_99"]
        assert any("UNKNOWN_UNIT" in e for e in _validate(p, base_world)["errors"])

    def test_not_own_unit(self, base_world):
        p = _good_payload()
        p["changes"]["attacker_unit_codes"] = ["cat_a_05", "per_g_01"]
        assert any("NOT_OWN_UNIT" in e for e in _validate(p, base_world)["errors"])

    def test_wrong_unit_type(self, base_world):
        p = _good_payload()
        p["changes"]["attacker_unit_codes"] = ["cat_a_05", "cat_g_01"]
        assert any("WRONG_UNIT_TYPE" in e for e in _validate(p, base_world)["errors"])

    def test_unit_not_active(self, base_world):
        p = _good_payload()
        p["changes"]["attacker_unit_codes"] = ["cat_a_99"]  # status=reserve
        assert any("UNIT_NOT_ACTIVE" in e for e in _validate(p, base_world)["errors"])

    def test_unit_not_on_source(self, base_world):
        base_world["units"]["cat_a_06"]["global_row"] = 5
        p = _good_payload()
        assert any("UNIT_NOT_ON_SOURCE" in e for e in _validate(p, base_world)["errors"])

    def test_target_friendly(self, base_world):
        p = _good_payload()
        p["changes"]["target_global_row"] = 5
        p["changes"]["target_global_col"] = 15  # no enemies there
        assert any("TARGET_FRIENDLY" in e for e in _validate(p, base_world)["errors"])
