"""L1 tests for covert_ops validator — CARD_ACTIONS §4.1-4.4."""

from __future__ import annotations
import pytest
from engine.services.covert_ops_validator import validate_covert_op

ROLES = {
    "shadow": {"intelligence_pool": 8, "sabotage_cards": 3, "disinfo_cards": 3,
               "election_meddling_cards": 1, "country_id": "columbia"},
    "dealer": {"intelligence_pool": 0, "sabotage_cards": 0, "disinfo_cards": 0,
               "election_meddling_cards": 0, "country_id": "columbia"},
}


class TestIntelligence:
    def test_valid(self):
        p = {"action_type": "covert_op", "op_type": "intelligence", "country_code": "columbia",
             "role_id": "shadow", "round_num": 3,
             "rationale": "Gathering intelligence on Persia's nuclear capability status",
             "question": "What is Persia's current nuclear technology level and R&D progress?"}
        r = validate_covert_op(p, ROLES)
        assert r["valid"], r["errors"]
        assert r["normalized"]["question"] == "What is Persia's current nuclear technology level and R&D progress?"

    def test_missing_question(self):
        p = {"action_type": "covert_op", "op_type": "intelligence", "country_code": "columbia",
             "role_id": "shadow", "round_num": 3, "rationale": "x" * 30, "question": "hi"}
        assert any("MISSING_QUESTION" in e for e in validate_covert_op(p, ROLES)["errors"])

    def test_no_card_needed_for_intelligence(self):
        """Intelligence uses replenishing pool — even dealer with 0 pool should work (pool ≠ card)."""
        p = {"action_type": "covert_op", "op_type": "intelligence", "country_code": "columbia",
             "role_id": "dealer", "round_num": 3, "rationale": "x" * 30,
             "question": "What is the current state of the world economy?"}
        r = validate_covert_op(p, ROLES)
        assert r["valid"], r["errors"]  # intelligence skips card check


class TestSabotage:
    def test_valid(self):
        p = {"action_type": "covert_op", "op_type": "sabotage", "country_code": "columbia",
             "role_id": "shadow", "round_num": 3,
             "rationale": "Sabotaging Persia's nuclear development program infrastructure",
             "target_country": "persia", "target_type": "nuclear_tech"}
        r = validate_covert_op(p, ROLES)
        assert r["valid"], r["errors"]

    def test_no_cards(self):
        p = {"action_type": "covert_op", "op_type": "sabotage", "country_code": "columbia",
             "role_id": "dealer", "round_num": 3, "rationale": "x" * 30,
             "target_country": "persia", "target_type": "infrastructure"}
        assert any("NO_CARDS" in e for e in validate_covert_op(p, ROLES)["errors"])

    def test_self_sabotage(self):
        p = {"action_type": "covert_op", "op_type": "sabotage", "country_code": "columbia",
             "role_id": "shadow", "round_num": 3, "rationale": "x" * 30,
             "target_country": "columbia", "target_type": "infrastructure"}
        assert any("SELF_SABOTAGE" in e for e in validate_covert_op(p, ROLES)["errors"])

    def test_invalid_target_type(self):
        p = {"action_type": "covert_op", "op_type": "sabotage", "country_code": "columbia",
             "role_id": "shadow", "round_num": 3, "rationale": "x" * 30,
             "target_country": "persia", "target_type": "population"}
        assert any("INVALID_TARGET_TYPE" in e for e in validate_covert_op(p, ROLES)["errors"])


class TestPropaganda:
    def test_valid_boost_own(self):
        p = {"action_type": "covert_op", "op_type": "propaganda", "country_code": "columbia",
             "role_id": "shadow", "round_num": 3,
             "rationale": "Boosting domestic support through coordinated media campaign",
             "target": "columbia", "intent": "boost", "content": "Victory is near!"}
        r = validate_covert_op(p, ROLES)
        assert r["valid"], r["errors"]

    def test_valid_destabilize_foreign(self):
        p = {"action_type": "covert_op", "op_type": "propaganda", "country_code": "columbia",
             "role_id": "shadow", "round_num": 3,
             "rationale": "Destabilizing Sarmatia through disinformation about leadership",
             "target": "sarmatia", "intent": "destabilize"}
        r = validate_covert_op(p, ROLES)
        assert r["valid"], r["errors"]

    def test_invalid_intent(self):
        p = {"action_type": "covert_op", "op_type": "propaganda", "country_code": "columbia",
             "role_id": "shadow", "round_num": 3, "rationale": "x" * 30,
             "target": "sarmatia", "intent": "confuse"}
        assert any("INVALID_INTENT" in e for e in validate_covert_op(p, ROLES)["errors"])


class TestElectionMeddling:
    def test_valid(self):
        p = {"action_type": "covert_op", "op_type": "election_meddling", "country_code": "columbia",
             "role_id": "shadow", "round_num": 3,
             "rationale": "Meddling in Ruthenia elections to boost our preferred candidate",
             "target_country": "ruthenia", "direction": "boost", "candidate": "beacon"}
        r = validate_covert_op(p, ROLES)
        assert r["valid"], r["errors"]

    def test_invalid_direction(self):
        p = {"action_type": "covert_op", "op_type": "election_meddling", "country_code": "columbia",
             "role_id": "shadow", "round_num": 3, "rationale": "x" * 30,
             "target_country": "ruthenia", "direction": "rig"}
        assert any("INVALID_DIRECTION" in e for e in validate_covert_op(p, ROLES)["errors"])


class TestGeneral:
    def test_invalid_op_type(self):
        p = {"action_type": "covert_op", "op_type": "hacking", "country_code": "columbia",
             "role_id": "shadow", "round_num": 3, "rationale": "x" * 30}
        assert any("INVALID_OP_TYPE" in e for e in validate_covert_op(p, ROLES)["errors"])
