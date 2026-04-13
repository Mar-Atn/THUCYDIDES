"""L1 tests for agreement_validator — CONTRACT_AGREEMENTS v1.0."""

from __future__ import annotations
import pytest
from engine.services.agreement_validator import validate_agreement_proposal


def _good():
    return {
        "action_type": "propose_agreement",
        "proposer_role_id": "dealer",
        "proposer_country_code": "columbia",
        "round_num": 3,
        "agreement_name": "Columbia-Sarmatia Ceasefire",
        "agreement_type": "armistice",
        "visibility": "public",
        "terms": "Both parties cease all military operations for 3 rounds.",
        "signatories": ["columbia", "sarmatia"],
        "rationale": "De-escalation",
    }


ROLES = {
    "dealer": {"is_head_of_state": True, "is_diplomat": False},
    "shadow": {"is_head_of_state": False, "is_diplomat": False, "powers": "intelligence"},
    "anchor": {"is_head_of_state": False, "is_diplomat": True},
}


def _v(p, roles=ROLES):
    return validate_agreement_proposal(p, roles)


class TestHappy:
    def test_valid_bilateral(self):
        r = _v(_good())
        assert r["valid"], r["errors"]
        assert r["normalized"]["agreement_type"] == "armistice"
        assert r["normalized"]["signatories"] == ["columbia", "sarmatia"]

    def test_valid_multilateral(self):
        p = _good()
        p["signatories"] = ["columbia", "sarmatia", "cathay"]
        r = _v(p)
        assert r["valid"], r["errors"]
        assert len(r["normalized"]["signatories"]) == 3

    def test_valid_secret(self):
        p = _good()
        p["visibility"] = "secret"
        r = _v(p)
        assert r["valid"], r["errors"]
        assert r["normalized"]["visibility"] == "secret"

    def test_valid_custom_type(self):
        p = _good()
        p["agreement_type"] = "semiconductor_sharing"
        r = _v(p)
        assert r["valid"], r["errors"]

    def test_diplomat_can_sign(self):
        p = _good()
        p["proposer_role_id"] = "anchor"
        r = _v(p)
        assert r["valid"], r["errors"]


class TestErrors:
    def test_missing_name(self):
        p = _good()
        p["agreement_name"] = ""
        assert any("MISSING_NAME" in e for e in _v(p)["errors"])

    def test_missing_terms(self):
        p = _good()
        p["terms"] = ""
        assert any("MISSING_TERMS" in e for e in _v(p)["errors"])

    def test_invalid_visibility(self):
        p = _good()
        p["visibility"] = "classified"
        assert any("INVALID_VISIBILITY" in e for e in _v(p)["errors"])

    def test_too_few_signatories(self):
        p = _good()
        p["signatories"] = ["columbia"]
        assert any("MISSING_SIGNATORIES" in e for e in _v(p)["errors"])

    def test_invalid_signatory(self):
        p = _good()
        p["signatories"] = ["columbia", "atlantis"]
        assert any("INVALID_SIGNATORY" in e for e in _v(p)["errors"])

    def test_proposer_not_signatory(self):
        p = _good()
        p["signatories"] = ["sarmatia", "cathay"]
        assert any("PROPOSER_NOT_SIGNATORY" in e for e in _v(p)["errors"])

    def test_unauthorized_role(self):
        p = _good()
        p["proposer_role_id"] = "shadow"  # not HoS, not diplomat
        assert any("UNAUTHORIZED_ROLE" in e for e in _v(p)["errors"])
