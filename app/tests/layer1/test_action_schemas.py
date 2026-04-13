"""L1 — Action schemas: validation for all 25 action types."""

from __future__ import annotations
import pytest
from pydantic import ValidationError
from engine.agents.action_schemas import (
    ACTION_TYPE_TO_MODEL,
    ArrestOrder, MartialLawOrder, AssassinationOrder, CoupAttemptOrder,
    LeadProtestOrder, ReassignPowersOrder, CallEarlyElectionsOrder,
    SubmitNominationOrder, CastVoteOrder, BasingRightsOrder, BlockadeOrder,
    MissileLaunchOrder, NuclearTestOrder, RespondExchangeOrder, SignAgreementOrder,
)


class TestSchemaCount:
    def test_all_25_types_registered(self):
        assert len(ACTION_TYPE_TO_MODEL) == 25


class TestDomesticSchemas:
    def test_arrest_valid(self):
        o = ArrestOrder(target_role="ironhand", rationale="Threat to regime")
        assert o.action_type == "arrest"
        assert o.target_role == "ironhand"

    def test_arrest_missing_target(self):
        with pytest.raises(ValidationError):
            ArrestOrder(rationale="No target")

    def test_martial_law_valid(self):
        o = MartialLawOrder(rationale="National emergency")
        assert o.action_type == "martial_law"

    def test_assassination_valid(self):
        o = AssassinationOrder(target_role="furnace", domestic=False, rationale="Strategic elimination")
        assert o.action_type == "assassination"
        assert o.domestic is False

    def test_coup_valid(self):
        o = CoupAttemptOrder(co_conspirator_role="compass", rationale="Regime change")
        assert o.action_type == "coup_attempt"

    def test_lead_protest_valid(self):
        o = LeadProtestOrder(rationale="The people demand change")
        assert o.action_type == "lead_protest"

    def test_reassign_powers_valid(self):
        o = ReassignPowersOrder(power_type="military", new_holder_role="shield", rationale="New strategy")
        assert o.action_type == "reassign_powers"

    def test_reassign_powers_invalid_type(self):
        with pytest.raises(ValidationError):
            ReassignPowersOrder(power_type="magic", new_holder_role="shield", rationale="Invalid")


class TestElectionSchemas:
    def test_call_early_elections(self):
        o = CallEarlyElectionsOrder(rationale="Democratic renewal")
        assert o.action_type == "call_early_elections"

    def test_submit_nomination(self):
        o = SubmitNominationOrder(election_type="columbia_midterms", election_round=2, rationale="I represent the people")
        assert o.election_type == "columbia_midterms"
        assert o.election_round == 2

    def test_cast_vote(self):
        o = CastVoteOrder(election_type="columbia_midterms", candidate_role_id="tribune", rationale="Best candidate")
        assert o.candidate_role_id == "tribune"


class TestMilitarySchemas:
    def test_basing_rights_grant(self):
        o = BasingRightsOrder(operation="grant", guest_country="columbia", zone_id="sar_z1", rationale="Alliance")
        assert o.operation == "grant"

    def test_basing_rights_invalid_op(self):
        with pytest.raises(ValidationError):
            BasingRightsOrder(operation="destroy", guest_country="columbia", zone_id="z1", rationale="Bad")

    def test_blockade(self):
        o = BlockadeOrder(zone_id="suez", imposer_units=["alb_n_01", "alb_n_02"], rationale="Control strait")
        assert len(o.imposer_units) == 2

    def test_missile_launch(self):
        o = MissileLaunchOrder(launcher_unit_code="sar_m_01", target_global_row=5, target_global_col=10, rationale="Strike")
        assert o.target_global_row == 5

    def test_nuclear_test(self):
        o = NuclearTestOrder(rationale="Deterrence program")
        assert o.action_type == "nuclear_test"


class TestTransactionResponseSchemas:
    def test_respond_accept(self):
        o = RespondExchangeOrder(transaction_id="tx-123", response="accept", rationale="Good deal")
        assert o.response == "accept"

    def test_respond_counter(self):
        o = RespondExchangeOrder(transaction_id="tx-123", response="counter",
                                  counter_offer={"coins": 50}, rationale="Need more")
        assert o.counter_offer == {"coins": 50}

    def test_respond_invalid_response(self):
        with pytest.raises(ValidationError):
            RespondExchangeOrder(transaction_id="tx-123", response="maybe", rationale="Unsure")

    def test_sign_agreement(self):
        o = SignAgreementOrder(agreement_id="ag-456", rationale="In our interest")
        assert o.action_type == "sign_agreement"
