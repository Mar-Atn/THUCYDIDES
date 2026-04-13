"""L1 tests for transaction_validator — CONTRACT_TRANSACTIONS v1.0."""

from __future__ import annotations
import pytest
from engine.services.transaction_validator import validate_proposal, validate_execution


def _unit(code, country, utype="ground", status="active"):
    return {"unit_code": code, "country_code": country, "unit_type": utype, "status": status}


@pytest.fixture
def world():
    units = {
        "col_g_01": _unit("col_g_01", "columbia"),
        "col_g_02": _unit("col_g_02", "columbia"),
        "col_g_99": _unit("col_g_99", "columbia", status="destroyed"),
        "sar_m_01": _unit("sar_m_01", "sarmatia", "strategic_missile"),
    }
    cs = {
        "columbia": {"treasury": 30.0, "nuclear_rd_progress": 0.5, "ai_rd_progress": 0.3},
        "sarmatia": {"treasury": 20.0, "nuclear_rd_progress": 0.2, "ai_rd_progress": 0.1},
    }
    roles = {
        "dealer": {"is_head_of_state": True, "is_military_chief": False, "personal_coins": 5},
        "shield": {"is_head_of_state": False, "is_military_chief": True, "personal_coins": 2},
        "shadow": {"is_head_of_state": False, "is_military_chief": False, "personal_coins": 2},
        "pathfinder": {"is_head_of_state": True, "is_military_chief": False, "personal_coins": 3},
    }
    return {"units": units, "cs": cs, "roles": roles}


def _good():
    return {
        "action_type": "propose_transaction",
        "proposer_role_id": "dealer",
        "proposer_country_code": "columbia",
        "scope": "country",
        "counterpart_role_id": "pathfinder",
        "counterpart_country_code": "sarmatia",
        "round_num": 3,
        "offer": {"coins": 5, "units": ["col_g_01"]},
        "request": {"coins": 0, "basing_rights": True},
        "rationale": "Trade ground unit + coins for basing rights",
    }


def _v(p, w):
    return validate_proposal(p, w["units"], w["cs"], w["roles"])


class TestHappy:
    def test_valid_country_trade(self, world):
        r = _v(_good(), world)
        assert r["valid"], r["errors"]
        assert r["normalized"]["offer"]["coins"] == 5
        assert r["normalized"]["offer"]["units"] == ["col_g_01"]

    def test_valid_personal_coins(self, world):
        p = _good()
        p["scope"] = "personal"
        p["offer"] = {"coins": 3}
        p["request"] = {"coins": 2}
        r = _v(p, world)
        assert r["valid"], r["errors"]

    def test_valid_tech_transfer(self, world):
        p = _good()
        p["offer"] = {"technology": {"nuclear": True}}
        p["request"] = {"technology": {"ai": True}}
        r = _v(p, world)
        assert r["valid"], r["errors"]


class TestErrors:
    def test_insufficient_coins(self, world):
        p = _good()
        p["offer"]["coins"] = 999
        assert any("INSUFFICIENT_COINS" in e for e in _v(p, world)["errors"])

    def test_unknown_unit(self, world):
        p = _good()
        p["offer"]["units"] = ["ghost_99"]
        assert any("UNKNOWN_UNIT" in e for e in _v(p, world)["errors"])

    def test_not_own_unit(self, world):
        p = _good()
        p["offer"]["units"] = ["sar_m_01"]
        assert any("NOT_OWN_UNIT" in e for e in _v(p, world)["errors"])

    def test_destroyed_unit(self, world):
        p = _good()
        p["offer"]["units"] = ["col_g_99"]
        assert any("UNIT_DESTROYED" in e for e in _v(p, world)["errors"])

    def test_self_trade(self, world):
        p = _good()
        p["counterpart_country_code"] = "columbia"
        p["counterpart_role_id"] = "dealer"
        assert any("SELF_TRADE" in e for e in _v(p, world)["errors"])

    def test_empty_trade(self, world):
        p = _good()
        p["offer"] = {}
        p["request"] = {}
        assert any("EMPTY_TRADE" in e for e in _v(p, world)["errors"])

    def test_personal_scope_no_units(self, world):
        p = _good()
        p["scope"] = "personal"
        p["offer"] = {"coins": 1, "units": ["col_g_01"]}
        assert any("PERSONAL_SCOPE_LIMIT" in e for e in _v(p, world)["errors"])

    def test_unauthorized_military_chief_tech(self, world):
        p = _good()
        p["proposer_role_id"] = "shield"  # military chief
        p["offer"] = {"technology": {"nuclear": True}}
        assert any("UNAUTHORIZED_ROLE" in e for e in _v(p, world)["errors"])

    def test_military_chief_can_trade_units(self, world):
        p = _good()
        p["proposer_role_id"] = "shield"
        p["offer"] = {"units": ["col_g_01"]}
        p["request"] = {"coins": 5}
        r = _v(p, world)
        assert r["valid"], r["errors"]


class TestExecutionValidation:
    def test_both_sides_valid(self, world):
        deal = {
            "proposer_country_code": "columbia",
            "counterpart_country_code": "sarmatia",
            "scope": "country",
            "offer": {"coins": 5},
            "request": {"coins": 3},
        }
        r = validate_execution(deal, world["units"], world["cs"])
        assert r["valid"], r["errors"]

    def test_counterpart_insufficient(self, world):
        deal = {
            "proposer_country_code": "columbia",
            "counterpart_country_code": "sarmatia",
            "scope": "country",
            "offer": {"coins": 5},
            "request": {"coins": 999},
        }
        r = validate_execution(deal, world["units"], world["cs"])
        assert not r["valid"]
        assert any("COUNTERPART_INSUFFICIENT_COINS" in e for e in r["errors"])
