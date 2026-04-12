"""L1 tests for nuclear validators — CONTRACT_NUCLEAR_CHAIN v1.0."""

from __future__ import annotations
import pytest
from engine.services.nuclear_validator import validate_nuclear_test, validate_nuclear_launch


def _unit(code, country, utype, row, col, status="active"):
    return {"unit_code": code, "country_code": country, "unit_type": utype,
            "global_row": row, "global_col": col, "status": status}


@pytest.fixture
def world():
    units = {
        "sar_m_01": _unit("sar_m_01", "sarmatia", "strategic_missile", 2, 16),
        "sar_m_02": _unit("sar_m_02", "sarmatia", "strategic_missile", 2, 16),
        "sar_m_03": _unit("sar_m_03", "sarmatia", "strategic_missile", 2, 12),
        "sar_m_99": _unit("sar_m_99", "sarmatia", "strategic_missile", None, None, status="reserve"),
        "per_m_01": _unit("per_m_01", "persia", "strategic_missile", 7, 13),
        "col_g_01": _unit("col_g_01", "columbia", "ground", 3, 3),
    }
    cs = {
        "sarmatia": {"nuclear_level": 3, "nuclear_confirmed": True, "stability": 6},
        "columbia": {"nuclear_level": 3, "nuclear_confirmed": True, "stability": 7},
        "persia": {"nuclear_level": 1, "nuclear_confirmed": True, "stability": 5},
        "cathay": {"nuclear_level": 2, "nuclear_confirmed": True, "stability": 8},
        "choson": {"nuclear_level": 1, "nuclear_confirmed": False, "stability": 4},  # unconfirmed!
        "mirage": {"nuclear_level": 0, "nuclear_confirmed": False, "stability": 5},  # no capability
    }
    zones = {(r, c): {"type": "land", "owner": None} for r in range(1, 11) for c in range(1, 21)}
    zones[(2, 16)] = {"type": "land", "owner": "sarmatia"}
    zones[(2, 12)] = {"type": "land", "owner": "sarmatia"}
    zones[(7, 13)] = {"type": "land", "owner": "persia"}
    zones[(3, 3)] = {"type": "land", "owner": "columbia"}
    return {"units": units, "cs": cs, "zones": zones}


# ===================== NUCLEAR TEST =====================

class TestNuclearTestHappy:
    def test_valid_underground(self, world):
        p = {"action_type": "nuclear_test", "country_code": "sarmatia", "round_num": 3,
             "decision": "change", "rationale": "Testing our nuclear capability underground at home territory hex",
             "changes": {"test_type": "underground", "target_global_row": 2, "target_global_col": 16}}
        r = validate_nuclear_test(p, world["units"], world["cs"], world["zones"])
        assert r["valid"], r["errors"]
        assert r["normalized"]["changes"]["test_type"] == "underground"

    def test_valid_surface(self, world):
        p = {"action_type": "nuclear_test", "country_code": "sarmatia", "round_num": 3,
             "decision": "change", "rationale": "Conducting a surface nuclear test to demonstrate capability to the world",
             "changes": {"test_type": "surface", "target_global_row": 2, "target_global_col": 12}}
        r = validate_nuclear_test(p, world["units"], world["cs"], world["zones"])
        assert r["valid"], r["errors"]

    def test_valid_no_change(self, world):
        p = {"action_type": "nuclear_test", "country_code": "sarmatia", "round_num": 3,
             "decision": "no_change", "rationale": "No nuclear test planned this round — maintaining strategic ambiguity"}
        r = validate_nuclear_test(p, world["units"], world["cs"], world["zones"])
        assert r["valid"], r["errors"]


class TestNuclearTestErrors:
    def test_no_capability(self, world):
        p = {"action_type": "nuclear_test", "country_code": "mirage", "round_num": 3,
             "decision": "change", "rationale": "x" * 30,
             "changes": {"test_type": "underground", "target_global_row": 5, "target_global_col": 10}}
        assert any("NO_NUCLEAR_CAPABILITY" in e for e in validate_nuclear_test(p, world["units"], world["cs"], world["zones"])["errors"])

    def test_not_own_territory(self, world):
        p = {"action_type": "nuclear_test", "country_code": "sarmatia", "round_num": 3,
             "decision": "change", "rationale": "x" * 30,
             "changes": {"test_type": "underground", "target_global_row": 3, "target_global_col": 3}}
        assert any("NOT_OWN_TERRITORY" in e for e in validate_nuclear_test(p, world["units"], world["cs"], world["zones"])["errors"])

    def test_invalid_test_type(self, world):
        p = {"action_type": "nuclear_test", "country_code": "sarmatia", "round_num": 3,
             "decision": "change", "rationale": "x" * 30,
             "changes": {"test_type": "orbital", "target_global_row": 2, "target_global_col": 16}}
        assert any("INVALID_TEST_TYPE" in e for e in validate_nuclear_test(p, world["units"], world["cs"], world["zones"])["errors"])


# ===================== NUCLEAR LAUNCH =====================

class TestNuclearLaunchHappy:
    def test_valid_t3_salvo(self, world):
        p = {"action_type": "launch_missile", "country_code": "sarmatia", "round_num": 5,
             "decision": "change", "rationale": "Launching nuclear salvo against Columbia home territory in retaliation",
             "changes": {"warhead": "nuclear", "missiles": [
                 {"missile_unit_code": "sar_m_01", "target_global_row": 3, "target_global_col": 3},
                 {"missile_unit_code": "sar_m_02", "target_global_row": 3, "target_global_col": 3},
                 {"missile_unit_code": "sar_m_03", "target_global_row": 3, "target_global_col": 3},
             ]}}
        r = validate_nuclear_launch(p, world["units"], world["cs"], world["zones"])
        assert r["valid"], r["errors"]
        assert len(r["normalized"]["changes"]["missiles"]) == 3

    def test_valid_t1_single(self, world):
        p = {"action_type": "launch_missile", "country_code": "persia", "round_num": 5,
             "decision": "change", "rationale": "Launching single nuclear missile at nearby target as tactical strike",
             "changes": {"warhead": "nuclear", "missiles": [
                 {"missile_unit_code": "per_m_01", "target_global_row": 8, "target_global_col": 13},
             ]}}
        r = validate_nuclear_launch(p, world["units"], world["cs"], world["zones"])
        assert r["valid"], r["errors"]

    def test_valid_no_change(self, world):
        p = {"action_type": "launch_missile", "country_code": "sarmatia", "round_num": 5,
             "decision": "no_change", "rationale": "Holding nuclear option in reserve — deterrence through ambiguity"}
        r = validate_nuclear_launch(p, world["units"], world["cs"], world["zones"])
        assert r["valid"], r["errors"]


class TestNuclearLaunchErrors:
    def test_not_confirmed(self, world):
        p = {"action_type": "launch_missile", "country_code": "choson", "round_num": 5,
             "decision": "change", "rationale": "x" * 30,
             "changes": {"warhead": "nuclear", "missiles": [
                 {"missile_unit_code": "sar_m_01", "target_global_row": 3, "target_global_col": 3}
             ]}}
        assert any("NUCLEAR_NOT_CONFIRMED" in e for e in validate_nuclear_launch(p, world["units"], world["cs"], world["zones"])["errors"])

    def test_no_capability(self, world):
        p = {"action_type": "launch_missile", "country_code": "mirage", "round_num": 5,
             "decision": "change", "rationale": "x" * 30,
             "changes": {"warhead": "nuclear", "missiles": [
                 {"missile_unit_code": "sar_m_01", "target_global_row": 3, "target_global_col": 3}
             ]}}
        assert any("NO_NUCLEAR_CAPABILITY" in e for e in validate_nuclear_launch(p, world["units"], world["cs"], world["zones"])["errors"])

    def test_t1_too_many_missiles(self, world):
        p = {"action_type": "launch_missile", "country_code": "persia", "round_num": 5,
             "decision": "change", "rationale": "x" * 30,
             "changes": {"warhead": "nuclear", "missiles": [
                 {"missile_unit_code": "per_m_01", "target_global_row": 8, "target_global_col": 13},
                 {"missile_unit_code": "per_m_01", "target_global_row": 7, "target_global_col": 13},
             ]}}
        r = validate_nuclear_launch(p, world["units"], world["cs"], world["zones"])
        assert any("TOO_MANY_MISSILES" in e for e in r["errors"])

    def test_missile_not_active(self, world):
        p = {"action_type": "launch_missile", "country_code": "sarmatia", "round_num": 5,
             "decision": "change", "rationale": "x" * 30,
             "changes": {"warhead": "nuclear", "missiles": [
                 {"missile_unit_code": "sar_m_99", "target_global_row": 3, "target_global_col": 3},
             ]}}
        assert any("UNIT_NOT_ACTIVE" in e for e in validate_nuclear_launch(p, world["units"], world["cs"], world["zones"])["errors"])

    def test_wrong_unit_type(self, world):
        p = {"action_type": "launch_missile", "country_code": "columbia", "round_num": 5,
             "decision": "change", "rationale": "x" * 30,
             "changes": {"warhead": "nuclear", "missiles": [
                 {"missile_unit_code": "col_g_01", "target_global_row": 5, "target_global_col": 5},
             ]}}
        assert any("WRONG_UNIT_TYPE" in e for e in validate_nuclear_launch(p, world["units"], world["cs"], world["zones"])["errors"])

    def test_out_of_range_t1(self, world):
        # Persia is T1, max range 2. Missile at (7,13), target at (3,3) = distance 14
        p = {"action_type": "launch_missile", "country_code": "persia", "round_num": 5,
             "decision": "change", "rationale": "x" * 30,
             "changes": {"warhead": "nuclear", "missiles": [
                 {"missile_unit_code": "per_m_01", "target_global_row": 3, "target_global_col": 3},
             ]}}
        assert any("OUT_OF_RANGE" in e for e in validate_nuclear_launch(p, world["units"], world["cs"], world["zones"])["errors"])

    def test_t3_global_range(self, world):
        # Sarmatia is T3, missiles at (2,16), target at (10,1) = distance 23 — T3 allows global
        p = {"action_type": "launch_missile", "country_code": "sarmatia", "round_num": 5,
             "decision": "change", "rationale": "Long range strategic nuclear strike across the globe for maximum effect",
             "changes": {"warhead": "nuclear", "missiles": [
                 {"missile_unit_code": "sar_m_01", "target_global_row": 10, "target_global_col": 1},
             ]}}
        r = validate_nuclear_launch(p, world["units"], world["cs"], world["zones"])
        assert r["valid"], r["errors"]

    def test_conventional_warhead_rejected(self, world):
        p = {"action_type": "launch_missile", "country_code": "sarmatia", "round_num": 5,
             "decision": "change", "rationale": "x" * 30,
             "changes": {"warhead": "conventional", "missiles": [
                 {"missile_unit_code": "sar_m_01", "target_global_row": 3, "target_global_col": 3},
             ]}}
        assert any("INVALID_WARHEAD" in e for e in validate_nuclear_launch(p, world["units"], world["cs"], world["zones"])["errors"])
