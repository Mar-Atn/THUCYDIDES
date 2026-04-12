"""L1 unit tests for naval combat validator — CONTRACT_NAVAL_COMBAT v1.0."""

from __future__ import annotations
import pytest
from engine.services.naval_combat_validator import validate_naval_attack


def _unit(code, country, utype, row, col, status="active"):
    return {"unit_code": code, "country_code": country, "unit_type": utype,
            "global_row": row, "global_col": col, "status": status}


@pytest.fixture
def world():
    units = {
        "col_n_01": _unit("col_n_01", "columbia", "naval", 8, 4),
        "col_n_02": _unit("col_n_02", "columbia", "naval", 9, 6),
        "sar_n_01": _unit("sar_n_01", "sarmatia", "naval", 8, 5),  # adjacent to col_n_01
        "sar_n_02": _unit("sar_n_02", "sarmatia", "naval", 2, 17),  # far away
        "col_g_01": _unit("col_g_01", "columbia", "ground", 3, 3),  # wrong type
        "col_n_99": _unit("col_n_99", "columbia", "naval", None, None, status="reserve"),
    }
    cs = {"columbia": {"stability": 7, "ai_level": 2}, "sarmatia": {"stability": 5, "ai_level": 1}}
    return {"units": units, "cs": cs}


def _good():
    return {
        "action_type": "attack_naval",
        "country_code": "columbia",
        "round_num": 3,
        "decision": "change",
        "rationale": "Engaging enemy Sarmatian frigate at adjacent hex to control the strait",
        "changes": {"attacker_unit_code": "col_n_01", "target_unit_code": "sar_n_01"},
    }


def _v(payload, w):
    return validate_naval_attack(payload, w["units"], w["cs"])


class TestHappy:
    def test_valid_change(self, world):
        r = _v(_good(), world)
        assert r["valid"], r["errors"]
        assert r["normalized"]["changes"]["attacker_unit_code"] == "col_n_01"

    def test_valid_no_change(self, world):
        p = {"action_type": "attack_naval", "country_code": "columbia", "round_num": 3,
             "decision": "no_change", "rationale": "Holding naval forces — no enemy ships within engagement range this round"}
        r = _v(p, world)
        assert r["valid"], r["errors"]


class TestStructural:
    def test_invalid_action_type(self, world):
        p = _good(); p["action_type"] = "attack_air"
        assert any("INVALID_ACTION_TYPE" in e for e in _v(p, world)["errors"])

    def test_rationale_too_short(self, world):
        p = _good(); p["rationale"] = "short"
        assert any("RATIONALE_TOO_SHORT" in e for e in _v(p, world)["errors"])

    def test_no_change_with_changes(self, world):
        p = {"action_type": "attack_naval", "country_code": "columbia", "round_num": 3,
             "decision": "no_change", "rationale": "Some long enough rationale for this no-change decision here",
             "changes": {"attacker_unit_code": "col_n_01"}}
        assert any("UNEXPECTED_CHANGES" in e for e in _v(p, world)["errors"])


class TestUnits:
    def test_unknown_attacker(self, world):
        p = _good(); p["changes"]["attacker_unit_code"] = "ghost_n_99"
        assert any("UNKNOWN_UNIT" in e for e in _v(p, world)["errors"])

    def test_not_own_unit(self, world):
        p = _good(); p["changes"]["attacker_unit_code"] = "sar_n_01"
        assert any("NOT_OWN_UNIT" in e for e in _v(p, world)["errors"])

    def test_wrong_type_attacker(self, world):
        p = _good(); p["changes"]["attacker_unit_code"] = "col_g_01"
        assert any("WRONG_UNIT_TYPE" in e for e in _v(p, world)["errors"])

    def test_wrong_type_target(self, world):
        p = _good(); p["changes"]["target_unit_code"] = "col_g_01"
        assert any("WRONG_UNIT_TYPE" in e for e in _v(p, world)["errors"])

    def test_target_friendly(self, world):
        p = _good(); p["changes"]["target_unit_code"] = "col_n_02"
        assert any("TARGET_FRIENDLY" in e for e in _v(p, world)["errors"])

    def test_unit_not_active(self, world):
        p = _good(); p["changes"]["attacker_unit_code"] = "col_n_99"
        assert any("UNIT_NOT_ACTIVE" in e for e in _v(p, world)["errors"])

    def test_same_unit(self, world):
        p = _good(); p["changes"]["target_unit_code"] = "col_n_01"
        assert any("SAME_UNIT" in e for e in _v(p, world)["errors"])

    def test_not_adjacent(self, world):
        p = _good(); p["changes"]["target_unit_code"] = "sar_n_02"  # (2,17) far from (8,4)
        assert any("NOT_ADJACENT_OR_SAME" in e for e in _v(p, world)["errors"])

    def test_same_hex_allowed(self, world):
        world["units"]["sar_n_same"] = _unit("sar_n_same", "sarmatia", "naval", 8, 4)
        p = _good(); p["changes"]["target_unit_code"] = "sar_n_same"
        r = _v(p, world)
        assert r["valid"], r["errors"]
