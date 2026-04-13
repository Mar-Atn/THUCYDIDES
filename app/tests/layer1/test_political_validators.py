"""L1 tests for political validators: assassination, coup, mass_protest, early_elections."""

from __future__ import annotations
import pytest
from engine.services.political_validator import (
    validate_assassination, validate_coup, validate_mass_protest, validate_early_elections,
)

ROLES = {
    "dealer": {"is_head_of_state": True, "country_id": "columbia",
               "assassination_cards": 0, "protest_stim_cards": 0},
    "shadow": {"is_head_of_state": False, "country_id": "columbia",
               "assassination_cards": 1, "protest_stim_cards": 0, "powers": "intelligence"},
    "ironhand": {"is_head_of_state": False, "is_military_chief": True,
                 "country_id": "sarmatia", "powers": "coup_potential"},
    "compass": {"is_head_of_state": False, "country_id": "sarmatia",
                "protest_stim_cards": 1, "powers": ""},
}


class TestAssassination:
    def test_valid(self):
        p = {"action_type": "assassination", "role_id": "shadow", "country_code": "columbia",
             "round_num": 3, "rationale": "Eliminating enemy intelligence director as strategic target",
             "target_role": "furnace", "domestic": False}
        r = validate_assassination(p, ROLES)
        assert r["valid"], r["errors"]

    def test_no_cards(self):
        p = {"action_type": "assassination", "role_id": "dealer", "round_num": 3,
             "rationale": "x" * 30, "target_role": "furnace"}
        assert any("NO_CARDS" in e for e in validate_assassination(p, ROLES)["errors"])

    def test_self_assassination(self):
        p = {"action_type": "assassination", "role_id": "shadow", "round_num": 3,
             "rationale": "x" * 30, "target_role": "shadow"}
        assert any("SELF_ASSASSINATION" in e for e in validate_assassination(p, ROLES)["errors"])


class TestCoup:
    def test_valid_military_chief(self):
        p = {"action_type": "coup_attempt", "role_id": "ironhand", "country_code": "sarmatia",
             "round_num": 3, "rationale": "Military seizure of power due to incompetent civilian leadership"}
        r = validate_coup(p, ROLES)
        assert r["valid"], r["errors"]

    def test_unauthorized(self):
        p = {"action_type": "coup_attempt", "role_id": "compass", "country_code": "sarmatia",
             "round_num": 3, "rationale": "x" * 30}
        assert any("UNAUTHORIZED" in e for e in validate_coup(p, ROLES)["errors"])


class TestMassProtest:
    def test_valid(self):
        p = {"action_type": "mass_protest", "role_id": "compass", "country_code": "sarmatia",
             "round_num": 3, "rationale": "Leading mass protests against the regime's failed war policy"}
        r = validate_mass_protest(p, ROLES)
        assert r["valid"], r["errors"]

    def test_no_cards(self):
        p = {"action_type": "mass_protest", "role_id": "dealer", "country_code": "columbia",
             "round_num": 3, "rationale": "x" * 30}
        assert any("NO_CARDS" in e for e in validate_mass_protest(p, ROLES)["errors"])


class TestEarlyElections:
    def test_valid(self):
        p = {"action_type": "call_early_elections", "role_id": "dealer", "country_code": "columbia",
             "round_num": 3, "rationale": "Calling snap elections to secure mandate for war policy"}
        r = validate_early_elections(p, ROLES)
        assert r["valid"], r["errors"]

    def test_non_hos(self):
        p = {"action_type": "call_early_elections", "role_id": "shadow", "country_code": "columbia",
             "round_num": 3, "rationale": "x" * 30}
        assert any("UNAUTHORIZED" in e for e in validate_early_elections(p, ROLES)["errors"])
