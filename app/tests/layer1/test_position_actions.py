"""Layer 1 tests for position_actions rules engine.

Verifies compute_actions() against DESIGN_ACTIONS_TAB.md §3.2.
"""

import pytest
from engine.config.position_actions import (
    compute_actions, has_position, get_positions,
    UNIVERSAL_ACTIONS, POSITION_ACTIONS, REACTIVE_ACTIONS,
    INTEL_LIMITS, OPEC_MEMBERS, MARTIAL_LAW_ELIGIBLE,
    ORG_MEMBER_ACTIONS, ORG_CHAIRMAN_ACTIONS,
)


# ---------------------------------------------------------------------------
# Universal actions
# ---------------------------------------------------------------------------

class TestUniversalActions:
    """All roles get universal actions regardless of position."""

    def test_citizen_gets_universal(self):
        actions = compute_actions([], "ruthenia", {})
        for a in UNIVERSAL_ACTIONS:
            assert a in actions, f"Citizen missing universal action: {a}"

    def test_hos_gets_universal(self):
        actions = compute_actions(["head_of_state"], "columbia", {})
        for a in UNIVERSAL_ACTIONS:
            assert a in actions, f"HoS missing universal action: {a}"

    def test_universal_includes_change_leader(self):
        """HoS can voluntarily step down via change_leader."""
        actions = compute_actions(["head_of_state"], "cathay", {})
        assert "change_leader" in actions

    def test_universal_has_invite_not_meet_freely(self):
        actions = compute_actions([], "columbia", {})
        assert "invite_to_meet" in actions
        assert "meet_freely" not in actions


# ---------------------------------------------------------------------------
# Reactive actions NEVER in output
# ---------------------------------------------------------------------------

class TestReactiveExclusion:
    """Reactive actions must never appear in compute_actions output."""

    @pytest.mark.parametrize("reactive", sorted(REACTIVE_ACTIONS))
    def test_reactive_not_in_hos(self, reactive):
        actions = compute_actions(["head_of_state"], "columbia",
                                  {"nuclear_level": 3, "nuclear_confirmed": True})
        assert reactive not in actions, f"Reactive action {reactive} found in HoS actions"

    @pytest.mark.parametrize("reactive", sorted(REACTIVE_ACTIONS))
    def test_reactive_not_in_military(self, reactive):
        actions = compute_actions(["military"], "sarmatia",
                                  {"nuclear_level": 3, "nuclear_confirmed": True})
        assert reactive not in actions

    @pytest.mark.parametrize("reactive", sorted(REACTIVE_ACTIONS))
    def test_reactive_not_in_diplomat(self, reactive):
        actions = compute_actions(["diplomat"], "cathay", {})
        assert reactive not in actions


# ---------------------------------------------------------------------------
# Position-specific actions
# ---------------------------------------------------------------------------

class TestHeadOfState:
    def test_hos_gets_military(self):
        actions = compute_actions(["head_of_state"], "columbia", {})
        for a in ["ground_attack", "air_strike", "naval_combat", "move_units"]:
            assert a in actions

    def test_hos_gets_economic(self):
        actions = compute_actions(["head_of_state"], "columbia", {})
        for a in ["set_budget", "set_tariffs", "set_sanctions"]:
            assert a in actions

    def test_hos_gets_diplomatic(self):
        actions = compute_actions(["head_of_state"], "columbia", {})
        for a in ["propose_transaction", "propose_agreement", "basing_rights"]:
            assert a in actions

    def test_hos_gets_political(self):
        actions = compute_actions(["head_of_state"], "columbia", {})
        for a in ["declare_war", "arrest", "reassign_types"]:
            assert a in actions

    def test_hos_no_accept_transaction(self):
        """accept_transaction is reactive, not in role_actions."""
        actions = compute_actions(["head_of_state"], "columbia", {})
        assert "accept_transaction" not in actions

    def test_hos_no_sign_agreement(self):
        """sign_agreement is reactive, not in role_actions."""
        actions = compute_actions(["head_of_state"], "columbia", {})
        assert "sign_agreement" not in actions


class TestMilitary:
    def test_military_gets_combat(self):
        actions = compute_actions(["military"], "sarmatia", {})
        for a in ["ground_attack", "air_strike", "naval_combat", "naval_bombardment",
                   "launch_missile_conventional", "naval_blockade", "move_units"]:
            assert a in actions

    def test_military_gets_covert(self):
        actions = compute_actions(["military"], "sarmatia", {})
        for a in ["intelligence", "covert_operation", "assassination"]:
            assert a in actions

    def test_military_no_economic(self):
        actions = compute_actions(["military"], "sarmatia", {})
        assert "set_budget" not in actions
        assert "set_tariffs" not in actions

    def test_military_no_nuclear_authorize(self):
        """nuclear_authorize is reactive."""
        actions = compute_actions(["military"], "sarmatia",
                                  {"nuclear_level": 3, "nuclear_confirmed": True})
        assert "nuclear_authorize" not in actions


class TestEconomy:
    def test_economy_gets_budget(self):
        actions = compute_actions(["economy"], "cathay", {})
        for a in ["set_budget", "set_tariffs", "set_sanctions"]:
            assert a in actions

    def test_economy_no_combat(self):
        actions = compute_actions(["economy"], "cathay", {})
        assert "ground_attack" not in actions


class TestDiplomat:
    def test_diplomat_gets_agreements(self):
        actions = compute_actions(["diplomat"], "cathay", {})
        for a in ["propose_transaction", "propose_agreement", "basing_rights"]:
            assert a in actions

    def test_diplomat_gets_intelligence(self):
        actions = compute_actions(["diplomat"], "cathay", {})
        assert "intelligence" in actions

    def test_diplomat_no_declare_war(self):
        actions = compute_actions(["diplomat"], "cathay", {})
        assert "declare_war" not in actions


class TestSecurity:
    def test_security_gets_covert(self):
        actions = compute_actions(["security"], "sarmatia", {})
        for a in ["intelligence", "covert_operation", "assassination"]:
            assert a in actions

    def test_security_gets_arrest(self):
        """Design decision: security can arrest (alongside HoS)."""
        actions = compute_actions(["security"], "sarmatia", {})
        assert "arrest" in actions

    def test_security_no_nuclear_authorize(self):
        actions = compute_actions(["security"], "sarmatia", {})
        assert "nuclear_authorize" not in actions


class TestOpposition:
    def test_opposition_gets_intelligence(self):
        actions = compute_actions(["opposition"], "ruthenia", {})
        assert "intelligence" in actions

    def test_opposition_gets_universal(self):
        actions = compute_actions(["opposition"], "ruthenia", {})
        assert "public_statement" in actions
        assert "change_leader" in actions

    def test_opposition_no_combat(self):
        actions = compute_actions(["opposition"], "ruthenia", {})
        assert "ground_attack" not in actions

    def test_columbia_opposition_gets_self_nominate(self):
        actions = compute_actions(["opposition"], "columbia", {})
        assert "self_nominate" in actions

    def test_non_columbia_opposition_no_self_nominate(self):
        actions = compute_actions(["opposition"], "ruthenia", {})
        assert "self_nominate" not in actions


class TestCitizen:
    """Citizen = no positions at all (not even opposition)."""

    def test_citizen_gets_only_universal(self):
        actions = compute_actions([], "ruthenia", {})
        assert actions == UNIVERSAL_ACTIONS

    def test_citizen_no_intelligence(self):
        actions = compute_actions([], "ruthenia", {})
        assert "intelligence" not in actions

    def test_citizen_no_combat(self):
        actions = compute_actions([], "ruthenia", {})
        assert "ground_attack" not in actions


# ---------------------------------------------------------------------------
# Dynamic conditions
# ---------------------------------------------------------------------------

class TestNuclearDynamic:
    def test_hos_nuclear_l0_no_test(self):
        actions = compute_actions(["head_of_state"], "persia", {"nuclear_level": 0})
        assert "nuclear_test" not in actions

    def test_hos_nuclear_l1_gets_test(self):
        actions = compute_actions(["head_of_state"], "persia", {"nuclear_level": 1})
        assert "nuclear_test" in actions

    def test_hos_not_confirmed_no_launch(self):
        actions = compute_actions(["head_of_state"], "persia",
                                  {"nuclear_level": 2, "nuclear_confirmed": False})
        assert "nuclear_launch_initiate" not in actions

    def test_hos_confirmed_gets_launch(self):
        actions = compute_actions(["head_of_state"], "sarmatia",
                                  {"nuclear_level": 3, "nuclear_confirmed": True})
        assert "nuclear_launch_initiate" in actions

    def test_military_no_nuclear_test(self):
        """Only HoS gets nuclear_test, not military."""
        actions = compute_actions(["military"], "sarmatia",
                                  {"nuclear_level": 3, "nuclear_confirmed": True})
        assert "nuclear_test" not in actions


class TestOPEC:
    def test_opec_hos_gets_set_opec(self):
        for cc in sorted(OPEC_MEMBERS):
            actions = compute_actions(["head_of_state"], cc, {})
            assert "set_opec" in actions, f"OPEC HoS {cc} missing set_opec"

    def test_opec_economy_gets_set_opec(self):
        actions = compute_actions(["economy"], "persia", {})
        assert "set_opec" in actions

    def test_non_opec_hos_no_set_opec(self):
        actions = compute_actions(["head_of_state"], "columbia", {})
        assert "set_opec" not in actions


class TestMartialLaw:
    def test_eligible_hos_gets_martial_law(self):
        for cc in sorted(MARTIAL_LAW_ELIGIBLE):
            actions = compute_actions(["head_of_state"], cc, {})
            assert "martial_law" in actions, f"Eligible HoS {cc} missing martial_law"

    def test_non_eligible_hos_no_martial_law(self):
        actions = compute_actions(["head_of_state"], "columbia", {})
        assert "martial_law" not in actions


# ---------------------------------------------------------------------------
# Multi-position combos
# ---------------------------------------------------------------------------

class TestPositionCombos:
    def test_hos_plus_security(self):
        """Furnace/Scales/Citadel pattern."""
        actions = compute_actions(["head_of_state", "security"], "persia",
                                  {"nuclear_level": 1})
        # Gets HoS actions
        assert "declare_war" in actions
        assert "set_budget" in actions
        # Gets security actions
        assert "assassination" in actions
        assert "covert_operation" in actions
        # Gets HoS nuclear
        assert "nuclear_test" in actions

    def test_economy_plus_diplomat(self):
        """Dawn pattern."""
        actions = compute_actions(["economy", "diplomat"], "persia", {})
        # Gets economy
        assert "set_budget" in actions
        assert "set_opec" in actions  # Persia is OPEC
        # Gets diplomat
        assert "propose_agreement" in actions
        assert "intelligence" in actions

    def test_military_plus_diplomat(self):
        """Sabre pattern."""
        actions = compute_actions(["military", "diplomat"], "levantia", {})
        assert "ground_attack" in actions
        assert "propose_agreement" in actions
        assert "intelligence" in actions


# ---------------------------------------------------------------------------
# Intel limits
# ---------------------------------------------------------------------------

class TestIntelLimits:
    def test_security_limits(self):
        assert INTEL_LIMITS["security"]["intelligence"] == 5
        assert INTEL_LIMITS["security"]["covert_operation"] == 5
        assert INTEL_LIMITS["security"]["assassination"] == 3

    def test_military_limits(self):
        assert INTEL_LIMITS["military"]["assassination"] == 2

    def test_diplomat_limits(self):
        assert INTEL_LIMITS["diplomat"]["intelligence"] == 1
        assert "covert_operation" not in INTEL_LIMITS["diplomat"]

    def test_opposition_limits(self):
        assert INTEL_LIMITS["opposition"]["intelligence"] == 2

    def test_citizen_no_limits(self):
        assert INTEL_LIMITS[None] == {}


# ---------------------------------------------------------------------------
# Org and reactive constants
# ---------------------------------------------------------------------------

class TestConstants:
    def test_org_actions_defined(self):
        assert "call_org_meeting" in ORG_MEMBER_ACTIONS
        assert "publish_org_decision" in ORG_CHAIRMAN_ACTIONS

    def test_reactive_actions_complete(self):
        assert "nuclear_authorize" in REACTIVE_ACTIONS
        assert "nuclear_intercept" in REACTIVE_ACTIONS
        assert "accept_transaction" in REACTIVE_ACTIONS
        assert "sign_agreement" in REACTIVE_ACTIONS
        assert "cast_vote" in REACTIVE_ACTIONS
        assert "accept_meeting" in REACTIVE_ACTIONS


# ---------------------------------------------------------------------------
# Legacy fallback
# ---------------------------------------------------------------------------

class TestLegacyFallback:
    def test_has_position_from_array(self):
        role = {"positions": ["head_of_state", "security"]}
        assert has_position(role, "head_of_state")
        assert has_position(role, "security")
        assert not has_position(role, "military")

    def test_has_position_legacy_boolean(self):
        role = {"positions": None, "is_head_of_state": True}
        assert has_position(role, "head_of_state")

    def test_get_positions_from_array(self):
        role = {"positions": ["military", "diplomat"]}
        assert get_positions(role) == ["military", "diplomat"]

    def test_get_positions_legacy(self):
        role = {"positions": None, "is_head_of_state": True, "is_military_chief": False,
                "is_economy_officer": False, "is_diplomat": False, "position_type": "head_of_state"}
        assert get_positions(role) == ["head_of_state"]
