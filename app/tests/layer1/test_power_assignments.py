"""L1 tests for power_assignments — authorization backbone."""

from __future__ import annotations
import pytest
from engine.services.power_assignments import (
    check_authorization, ACTION_TO_POWER, UNRESTRICTED_ACTIONS, DEFAULT_ASSIGNMENTS,
)

ROLES = {
    "dealer": {"is_head_of_state": True, "country_code": "columbia"},
    "shield": {"is_head_of_state": False, "is_military_chief": True, "country_code": "columbia"},
    "volt": {"is_head_of_state": False, "country_code": "columbia"},
    "anchor": {"is_head_of_state": False, "country_code": "columbia"},
    "shadow": {"is_head_of_state": False, "country_code": "columbia"},
}


class TestDefaults:
    def test_canonical_assignments_cover_5_countries(self):
        countries = {a["country_code"] for a in DEFAULT_ASSIGNMENTS}
        assert countries == {"columbia", "cathay", "sarmatia", "ruthenia", "persia"}

    def test_each_country_has_3_power_types(self):
        from collections import Counter
        counts = Counter(a["country_code"] for a in DEFAULT_ASSIGNMENTS)
        for cc, n in counts.items():
            assert n == 3, f"{cc} has {n} assignments, expected 3"

    def test_columbia_assignments(self):
        col = {a["power_type"]: a["assigned_role_id"] for a in DEFAULT_ASSIGNMENTS
               if a["country_code"] == "columbia"}
        assert col == {"military": "shield", "economic": "volt", "foreign_affairs": "anchor"}

    def test_sarmatia_compass_holds_two(self):
        sar = {a["power_type"]: a["assigned_role_id"] for a in DEFAULT_ASSIGNMENTS
               if a["country_code"] == "sarmatia"}
        assert sar["economic"] == "compass"
        assert sar["foreign_affairs"] == "compass"

    def test_ruthenia_foreign_vacant(self):
        rut = {a["power_type"]: a["assigned_role_id"] for a in DEFAULT_ASSIGNMENTS
               if a["country_code"] == "ruthenia"}
        assert rut["foreign_affairs"] is None  # HoS holds
        assert rut["economic"] == "broker"

    def test_persia_economic_vacant(self):
        per = {a["power_type"]: a["assigned_role_id"] for a in DEFAULT_ASSIGNMENTS
               if a["country_code"] == "persia"}
        assert per["economic"] is None  # HoS holds
        assert per["foreign_affairs"] == "dawn"


class TestActionMapping:
    def test_military_actions_mapped(self):
        mil_actions = ["move_units", "attack_ground", "attack_air", "attack_naval",
                       "attack_bombardment", "launch_missile", "blockade", "martial_law"]
        for a in mil_actions:
            assert ACTION_TO_POWER[a] == "military", f"{a} should map to military"

    def test_economic_actions_mapped(self):
        eco_actions = ["set_budget", "set_tariffs", "set_sanctions", "set_opec"]
        for a in eco_actions:
            assert ACTION_TO_POWER[a] == "economic", f"{a} should map to economic"

    def test_foreign_actions_mapped(self):
        assert ACTION_TO_POWER["propose_agreement"] == "foreign_affairs"
        assert ACTION_TO_POWER["propose_transaction"] == "foreign_affairs"

    def test_unrestricted_actions(self):
        for a in ["public_statement", "covert_op", "assassination", "mass_protest"]:
            assert a in UNRESTRICTED_ACTIONS


class TestAuthorizationLogic:
    """These test the logic without DB — using the roles dict only for HoS check."""

    def test_hos_always_authorized(self):
        # HoS should be authorized for ANY action
        for action in ["move_units", "set_budget", "propose_agreement"]:
            result = check_authorization("dealer", action, "fake_run", "columbia", roles=ROLES)
            assert result["authorized"], f"HoS should be authorized for {action}: {result}"

    def test_unrestricted_actions_always_pass(self):
        result = check_authorization("shadow", "public_statement", "fake_run", "columbia", roles=ROLES)
        assert result["authorized"]
        assert "unrestricted" in result["reason"]
