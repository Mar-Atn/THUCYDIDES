"""L1 tests for basing_rights validator."""

from __future__ import annotations
import pytest
from engine.services.basing_rights_validator import validate_basing_rights


def _unit(code, country, row, col, status="active"):
    return {"unit_code": code, "country_code": country, "unit_type": "ground",
            "global_row": row, "global_col": col, "status": status}


@pytest.fixture
def world():
    units = {
        "teu_g_01": _unit("teu_g_01", "teutonia", 3, 8),  # teutonia unit on columbia hex
        "col_g_01": _unit("col_g_01", "columbia", 3, 3),
    }
    zones = {
        (3, 3): {"type": "land", "owner": "columbia"},
        (3, 8): {"type": "land", "owner": "columbia"},  # columbia territory with teutonia unit
        (4, 11): {"type": "land", "owner": "sarmatia"},
    }
    return {"units": units, "zones": zones}


def _good():
    return {
        "action_type": "basing_rights",
        "country_code": "columbia",
        "round_num": 3,
        "decision": "change",
        "rationale": "Granting basing rights to Teutonia as part of our alliance commitment",
        "changes": {"counterpart_country": "teutonia", "action": "grant"},
    }


def _v(p, w):
    return validate_basing_rights(p, w["units"], w["zones"])


class TestHappy:
    def test_valid_grant(self, world):
        r = _v(_good(), world)
        assert r["valid"], r["errors"]
        assert r["normalized"]["changes"]["action"] == "grant"

    def test_valid_revoke_no_troops(self, world):
        p = _good()
        p["changes"]["action"] = "revoke"
        p["changes"]["counterpart_country"] = "sarmatia"  # sarmatia has no units on columbia
        p["rationale"] = "Revoking basing rights from Sarmatia — no troops present on our soil"
        r = _v(p, world)
        assert r["valid"], r["errors"]

    def test_valid_no_change(self, world):
        p = {"action_type": "basing_rights", "country_code": "columbia", "round_num": 3,
             "decision": "no_change", "rationale": "Maintaining current basing rights arrangements this round"}
        r = _v(p, world)
        assert r["valid"], r["errors"]


class TestErrors:
    def test_revoke_blocked_by_troops(self, world):
        """Cannot revoke Teutonia's basing — they have teu_g_01 on columbia hex (3,8)."""
        p = _good()
        p["changes"]["action"] = "revoke"
        p["rationale"] = "Trying to revoke but Teutonia has forces on our soil"
        r = _v(p, world)
        assert not r["valid"]
        assert any("GUEST_FORCES_PRESENT" in e for e in r["errors"])

    def test_self_basing(self, world):
        p = _good()
        p["changes"]["counterpart_country"] = "columbia"
        assert any("SELF_BASING" in e for e in _v(p, world)["errors"])

    def test_invalid_action(self, world):
        p = _good()
        p["changes"]["action"] = "suspend"
        assert any("INVALID_ACTION" in e for e in _v(p, world)["errors"])

    def test_invalid_guest(self, world):
        p = _good()
        p["changes"]["counterpart_country"] = "atlantis"
        assert any("INVALID_GUEST" in e for e in _v(p, world)["errors"])
