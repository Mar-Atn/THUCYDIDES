"""L1 tests for M5 validators: bombardment, blockade, conventional missile."""

from __future__ import annotations
import pytest
from engine.services.bombardment_validator import validate_bombardment
from engine.services.blockade_validator import validate_blockade
from engine.services.missile_validator import validate_missile_launch


def _unit(code, country, utype, row, col, status="active"):
    return {"unit_code": code, "country_code": country, "unit_type": utype,
            "global_row": row, "global_col": col, "status": status}


@pytest.fixture
def world():
    units = {
        "col_n_01": _unit("col_n_01", "columbia", "naval", 4, 5),   # sea hex adjacent to (3,5) land
        "col_n_02": _unit("col_n_02", "columbia", "naval", 9, 6),
        "col_m_01": _unit("col_m_01", "columbia", "strategic_missile", 3, 3),
        "col_m_99": _unit("col_m_99", "columbia", "strategic_missile", None, None, status="reserve"),
        "col_g_01": _unit("col_g_01", "columbia", "ground", 3, 3),
        "per_g_01": _unit("per_g_01", "persia", "ground", 3, 5),    # enemy ground on adjacent land
        "per_g_02": _unit("per_g_02", "persia", "ground", 6, 12),
    }
    zones = {(r, c): {"type": "land", "owner": None} for r in range(1, 11) for c in range(1, 21)}
    zones[(4, 5)] = {"type": "sea", "owner": None}
    zones[(9, 6)] = {"type": "sea", "owner": None}
    cs = {"columbia": {"stability": 7, "ai_level": 2}}
    return {"units": units, "zones": zones, "cs": cs}


# ===================== BOMBARDMENT =====================

class TestBombardmentHappy:
    def test_valid_change(self, world):
        p = {"action_type": "attack_bombardment", "country_code": "columbia", "round_num": 3,
             "decision": "change", "rationale": "Softening Persian ground defenses before amphibious landing attempt",
             "changes": {"naval_unit_codes": ["col_n_01"], "target_global_row": 3, "target_global_col": 5}}
        r = validate_bombardment(p, world["units"], world["zones"])
        assert r["valid"], r["errors"]

    def test_valid_no_change(self, world):
        p = {"action_type": "attack_bombardment", "country_code": "columbia", "round_num": 3,
             "decision": "no_change", "rationale": "No bombardment targets worth the expenditure this round"}
        r = validate_bombardment(p, world["units"], world["zones"])
        assert r["valid"], r["errors"]


class TestBombardmentErrors:
    def test_wrong_action_type(self, world):
        p = {"action_type": "attack_naval", "country_code": "columbia", "round_num": 3,
             "decision": "change", "rationale": "x" * 30,
             "changes": {"naval_unit_codes": ["col_n_01"], "target_global_row": 3, "target_global_col": 5}}
        assert any("INVALID_ACTION_TYPE" in e for e in validate_bombardment(p, world["units"], world["zones"])["errors"])

    def test_empty_naval_list(self, world):
        p = {"action_type": "attack_bombardment", "country_code": "columbia", "round_num": 3,
             "decision": "change", "rationale": "x" * 30,
             "changes": {"naval_unit_codes": [], "target_global_row": 3, "target_global_col": 5}}
        assert any("EMPTY_NAVAL_LIST" in e for e in validate_bombardment(p, world["units"], world["zones"])["errors"])

    def test_wrong_unit_type(self, world):
        p = {"action_type": "attack_bombardment", "country_code": "columbia", "round_num": 3,
             "decision": "change", "rationale": "x" * 30,
             "changes": {"naval_unit_codes": ["col_g_01"], "target_global_row": 3, "target_global_col": 5}}
        assert any("WRONG_UNIT_TYPE" in e for e in validate_bombardment(p, world["units"], world["zones"])["errors"])

    def test_not_adjacent(self, world):
        p = {"action_type": "attack_bombardment", "country_code": "columbia", "round_num": 3,
             "decision": "change", "rationale": "x" * 30,
             "changes": {"naval_unit_codes": ["col_n_02"], "target_global_row": 3, "target_global_col": 5}}
        assert any("NOT_ADJACENT" in e for e in validate_bombardment(p, world["units"], world["zones"])["errors"])

    def test_target_sea(self, world):
        p = {"action_type": "attack_bombardment", "country_code": "columbia", "round_num": 3,
             "decision": "change", "rationale": "x" * 30,
             "changes": {"naval_unit_codes": ["col_n_01"], "target_global_row": 4, "target_global_col": 5}}
        assert any("TARGET_NOT_LAND" in e for e in validate_bombardment(p, world["units"], world["zones"])["errors"])

    def test_no_ground_targets(self, world):
        p = {"action_type": "attack_bombardment", "country_code": "columbia", "round_num": 3,
             "decision": "change", "rationale": "x" * 30,
             "changes": {"naval_unit_codes": ["col_n_01"], "target_global_row": 4, "target_global_col": 4}}
        # (4,4) is land but has no enemy ground
        assert any("NO_GROUND_TARGETS" in e for e in validate_bombardment(p, world["units"], world["zones"])["errors"])


# ===================== BLOCKADE =====================

class TestBlockadeHappy:
    def test_valid_establish(self, world):
        p = {"action_type": "blockade", "country_code": "columbia", "round_num": 3,
             "decision": "change", "rationale": "Establishing full blockade of the Gulf Gate chokepoint",
             "changes": {"zone_id": "cp_gulf_gate", "action": "establish", "level": "full"}}
        r = validate_blockade(p, world["units"], world["zones"])
        assert r["valid"], r["errors"]

    def test_valid_lift(self, world):
        p = {"action_type": "blockade", "country_code": "columbia", "round_num": 3,
             "decision": "change", "rationale": "Lifting blockade in response to diplomatic pressure from allies",
             "changes": {"zone_id": "cp_caribe", "action": "lift"}}
        r = validate_blockade(p, world["units"], world["zones"])
        assert r["valid"], r["errors"]

    def test_valid_no_change(self, world):
        p = {"action_type": "blockade", "country_code": "columbia", "round_num": 3,
             "decision": "no_change", "rationale": "No blockade action needed - maintaining current maritime posture"}
        r = validate_blockade(p, world["units"], world["zones"])
        assert r["valid"], r["errors"]


class TestBlockadeErrors:
    def test_invalid_zone(self, world):
        p = {"action_type": "blockade", "country_code": "columbia", "round_num": 3,
             "decision": "change", "rationale": "x" * 30,
             "changes": {"zone_id": "cp_atlantis", "action": "establish", "level": "full"}}
        assert any("INVALID_ZONE" in e for e in validate_blockade(p, world["units"], world["zones"])["errors"])

    def test_invalid_action(self, world):
        p = {"action_type": "blockade", "country_code": "columbia", "round_num": 3,
             "decision": "change", "rationale": "x" * 30,
             "changes": {"zone_id": "cp_caribe", "action": "destroy", "level": "full"}}
        assert any("INVALID_ACTION" in e for e in validate_blockade(p, world["units"], world["zones"])["errors"])

    def test_invalid_level(self, world):
        p = {"action_type": "blockade", "country_code": "columbia", "round_num": 3,
             "decision": "change", "rationale": "x" * 30,
             "changes": {"zone_id": "cp_caribe", "action": "establish", "level": "maximum"}}
        assert any("INVALID_LEVEL" in e for e in validate_blockade(p, world["units"], world["zones"])["errors"])


# ===================== CONVENTIONAL MISSILE =====================

class TestMissileHappy:
    def test_valid_change(self, world):
        p = {"action_type": "launch_missile", "country_code": "columbia", "round_num": 3,
             "decision": "change", "rationale": "Launching conventional strike against Persian military concentration",
             "changes": {"missile_unit_code": "col_m_01", "warhead": "conventional",
                         "target_global_row": 6, "target_global_col": 3, "target_choice": "military"}}
        r = validate_missile_launch(p, world["units"], world["cs"], world["zones"])
        assert r["valid"], r["errors"]

    def test_valid_no_change(self, world):
        p = {"action_type": "launch_missile", "country_code": "columbia", "round_num": 3,
             "decision": "no_change", "rationale": "Holding missile assets in reserve — no high-value targets identified"}
        r = validate_missile_launch(p, world["units"], world["cs"], world["zones"])
        assert r["valid"], r["errors"]


class TestMissileErrors:
    def test_nuclear_rejected(self, world):
        p = {"action_type": "launch_missile", "country_code": "columbia", "round_num": 3,
             "decision": "change", "rationale": "x" * 30,
             "changes": {"missile_unit_code": "col_m_01", "warhead": "nuclear",
                         "target_global_row": 6, "target_global_col": 3, "target_choice": "military"}}
        assert any("INVALID_WARHEAD" in e for e in validate_missile_launch(p, world["units"], world["cs"], world["zones"])["errors"])

    def test_wrong_unit_type(self, world):
        p = {"action_type": "launch_missile", "country_code": "columbia", "round_num": 3,
             "decision": "change", "rationale": "x" * 30,
             "changes": {"missile_unit_code": "col_g_01", "warhead": "conventional",
                         "target_global_row": 6, "target_global_col": 3, "target_choice": "military"}}
        assert any("WRONG_UNIT_TYPE" in e for e in validate_missile_launch(p, world["units"], world["cs"], world["zones"])["errors"])

    def test_unit_not_active(self, world):
        p = {"action_type": "launch_missile", "country_code": "columbia", "round_num": 3,
             "decision": "change", "rationale": "x" * 30,
             "changes": {"missile_unit_code": "col_m_99", "warhead": "conventional",
                         "target_global_row": 3, "target_global_col": 3, "target_choice": "military"}}
        assert any("UNIT_NOT_ACTIVE" in e for e in validate_missile_launch(p, world["units"], world["cs"], world["zones"])["errors"])

    def test_out_of_range(self, world):
        p = {"action_type": "launch_missile", "country_code": "columbia", "round_num": 3,
             "decision": "change", "rationale": "x" * 30,
             "changes": {"missile_unit_code": "col_m_01", "warhead": "conventional",
                         "target_global_row": 10, "target_global_col": 20, "target_choice": "military"}}
        assert any("OUT_OF_RANGE" in e for e in validate_missile_launch(p, world["units"], world["cs"], world["zones"])["errors"])

    def test_invalid_target_choice(self, world):
        p = {"action_type": "launch_missile", "country_code": "columbia", "round_num": 3,
             "decision": "change", "rationale": "x" * 30,
             "changes": {"missile_unit_code": "col_m_01", "warhead": "conventional",
                         "target_global_row": 3, "target_global_col": 3, "target_choice": "civilians"}}
        assert any("INVALID_TARGET_CHOICE" in e for e in validate_missile_launch(p, world["units"], world["cs"], world["zones"])["errors"])
