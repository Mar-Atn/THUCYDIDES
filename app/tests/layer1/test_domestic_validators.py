"""L1 tests for domestic validators: fire_role, arrest, martial_law."""

from __future__ import annotations
import pytest
from engine.services.domestic_validator import (
    validate_fire_role, validate_arrest, validate_martial_law,
)

ROLES = {
    "dealer": {"is_head_of_state": True, "country_id": "columbia"},
    "shield": {"is_head_of_state": False, "is_military_chief": True, "country_id": "columbia"},
    "shadow": {"is_head_of_state": False, "country_id": "columbia"},
    "pathfinder": {"is_head_of_state": True, "country_id": "sarmatia"},
    "ironhand": {"is_head_of_state": False, "country_id": "sarmatia"},
}


# ========== FIRE / REASSIGN ==========

class TestFireRole:
    def test_valid_fire(self):
        p = {"action_type": "fire_role", "role_id": "dealer", "round_num": 3,
             "rationale": "Removing Shield from Defense Secretary position due to incompetence",
             "changes": {"target_role": "shield"}}
        r = validate_fire_role(p, ROLES)
        assert r["valid"], r["errors"]

    def test_non_hos_cannot_fire(self):
        p = {"action_type": "fire_role", "role_id": "shield", "round_num": 3,
             "rationale": "x" * 30, "changes": {"target_role": "shadow"}}
        assert any("UNAUTHORIZED" in e for e in validate_fire_role(p, ROLES)["errors"])

    def test_wrong_country(self):
        p = {"action_type": "fire_role", "role_id": "dealer", "round_num": 3,
             "rationale": "x" * 30, "changes": {"target_role": "ironhand"}}
        assert any("WRONG_COUNTRY" in e for e in validate_fire_role(p, ROLES)["errors"])

    def test_self_fire(self):
        p = {"action_type": "fire_role", "role_id": "dealer", "round_num": 3,
             "rationale": "x" * 30, "changes": {"target_role": "dealer"}}
        assert any("SELF_FIRE" in e for e in validate_fire_role(p, ROLES)["errors"])


# ========== ARREST ==========

class TestArrest:
    def test_valid_arrest(self):
        p = {"action_type": "arrest", "role_id": "dealer", "round_num": 3,
             "rationale": "Arresting Shadow for alleged espionage and treasonous activity",
             "changes": {"target_role": "shadow"}}
        r = validate_arrest(p, ROLES)
        assert r["valid"], r["errors"]

    def test_non_hos_cannot_arrest(self):
        p = {"action_type": "arrest", "role_id": "shield", "round_num": 3,
             "rationale": "x" * 30, "changes": {"target_role": "shadow"}}
        assert any("UNAUTHORIZED" in e for e in validate_arrest(p, ROLES)["errors"])

    def test_self_arrest(self):
        p = {"action_type": "arrest", "role_id": "dealer", "round_num": 3,
             "rationale": "x" * 30, "changes": {"target_role": "dealer"}}
        assert any("SELF_ARREST" in e for e in validate_arrest(p, ROLES)["errors"])


# ========== MARTIAL LAW ==========

class TestMartialLaw:
    def test_valid_martial_law(self):
        cs = {"sarmatia": {"stability": 5, "martial_law_declared": False}}
        p = {"action_type": "martial_law", "country_code": "sarmatia", "round_num": 3,
             "decision": "change",
             "rationale": "Declaring martial law to mobilize full conscription pool for war effort"}
        r = validate_martial_law(p, cs)
        assert r["valid"], r["errors"]
        assert r["normalized"]["changes"]["conscription_pool"] == 10

    def test_already_declared(self):
        cs = {"sarmatia": {"stability": 5, "martial_law_declared": True}}
        p = {"action_type": "martial_law", "country_code": "sarmatia", "round_num": 3,
             "decision": "change", "rationale": "x" * 30}
        assert any("ALREADY_DECLARED" in e for e in validate_martial_law(p, cs)["errors"])

    def test_not_eligible_country(self):
        cs = {"columbia": {"stability": 7}}
        p = {"action_type": "martial_law", "country_code": "columbia", "round_num": 3,
             "decision": "change", "rationale": "x" * 30}
        assert any("NOT_ELIGIBLE" in e for e in validate_martial_law(p, cs)["errors"])

    def test_valid_no_change(self):
        cs = {"sarmatia": {"stability": 5}}
        p = {"action_type": "martial_law", "country_code": "sarmatia", "round_num": 3,
             "decision": "no_change",
             "rationale": "Not declaring martial law this round — holding conscription in reserve"}
        r = validate_martial_law(p, cs)
        assert r["valid"], r["errors"]
