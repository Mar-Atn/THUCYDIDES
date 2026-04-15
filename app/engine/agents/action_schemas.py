"""Pydantic v2 schemas for agent action commits.

25+ structured action types covering all domains (military, economic,
political, technological, covert, domestic, transactions). Agents emit
one of these via the ``commit_action`` tool; the payload is validated
and persisted to ``agent_decisions``, then dispatched via
``action_dispatcher.dispatch_action()`` for engine resolution.
"""
from __future__ import annotations

from typing import Literal, Optional, Union

from pydantic import BaseModel, Field


class MoveUnitsOrder(BaseModel):
    """Batch movement order — CONTRACT_MOVEMENT v1.0.

    The full schema is defined in ``engine/services/movement_validator.py``;
    this Pydantic shim only validates that ``action_type == "move_units"``
    and the envelope fields are present so that legacy ``commit_action``
    callers don't crash. The real validation lives in the validator.
    """

    action_type: Literal["move_units"] = "move_units"
    decision: Literal["change", "no_change"] = "change"
    rationale: str
    changes: Optional[dict] = None


class AttackDeclarationOrder(BaseModel):
    """Declare attack against an enemy position."""

    action_type: Literal["declare_attack"] = "declare_attack"
    attacker_unit_codes: list[str]
    target_global_row: int
    target_global_col: int
    target_theater: Optional[str] = None
    target_theater_row: Optional[int] = None
    target_theater_col: Optional[int] = None
    target_description: str  # who/what is being hit
    rationale: str


class SanctionOrder(BaseModel):
    """Impose (or relax) sanctions on another country."""

    action_type: Literal["set_sanction"] = "set_sanction"
    target_country: str
    sanction_type: str  # e.g. "oil_export_ban", "financial", "tech_export"
    level: int = Field(..., ge=-3, le=3)
    rationale: str


class TariffOrder(BaseModel):
    """Impose tariffs on another country."""

    action_type: Literal["set_tariff"] = "set_tariff"
    target_country: str
    level: int = Field(..., ge=0, le=3)
    rationale: str


class RDInvestmentOrder(BaseModel):
    """Invest in an R&D track (nuclear, AI, or strategic missile)."""

    action_type: Literal["rd_investment"] = "rd_investment"
    domain: Literal["nuclear", "ai", "strategic_missile"]
    amount: float  # coins
    rationale: str


class PublicStatementOrder(BaseModel):
    """Public statement: free text, visible to all, attributed."""
    action_type: Literal["public_statement"] = "public_statement"
    content: str
    rationale: str


class OrgMeetingOrder(BaseModel):
    """Call an organization meeting."""
    action_type: Literal["call_org_meeting"] = "call_org_meeting"
    organization_code: str
    agenda: str
    rationale: str


class CovertOpOrder(BaseModel):
    """Covert operation."""
    action_type: Literal["covert_op"] = "covert_op"
    op_type: str  # intelligence | sabotage | propaganda | election_meddling
    target_country: Optional[str] = None
    target_type: Optional[str] = None  # infrastructure | nuclear_tech | military (sabotage)
    intent: Optional[str] = None  # boost | destabilize (propaganda)
    question: Optional[str] = None  # free text (intelligence)
    content: Optional[str] = None  # narrative (propaganda)
    rationale: str


class TransactionOrder(BaseModel):
    """Propose exchange transaction or agreement."""
    action_type: Literal["propose_transaction", "propose_agreement"]
    counterpart_country: str
    terms: Optional[str] = None
    offer: Optional[dict] = None
    request: Optional[dict] = None
    agreement_name: Optional[str] = None
    agreement_type: Optional[str] = None
    visibility: Optional[str] = "public"
    rationale: str


class RespondExchangeOrder(BaseModel):
    """Respond to a proposed transaction (accept/decline/counter)."""
    action_type: Literal["respond_exchange"] = "respond_exchange"
    transaction_id: str
    response: Literal["accept", "decline", "counter"]
    counter_offer: Optional[dict] = None
    rationale: str


class SignAgreementOrder(BaseModel):
    """Sign a proposed agreement."""
    action_type: Literal["sign_agreement"] = "sign_agreement"
    agreement_id: str
    rationale: str


# ── Domestic / Political ──────────────────────────────────────────────────

class ArrestOrder(BaseModel):
    """Request arrest of a role in your country (HoS only)."""
    action_type: Literal["arrest"] = "arrest"
    target_role: str
    rationale: str


class MartialLawOrder(BaseModel):
    """Declare martial law (HoS only, one-time per country per SIM)."""
    action_type: Literal["martial_law"] = "martial_law"
    rationale: str


class AssassinationOrder(BaseModel):
    """Assassination attempt against a target role."""
    action_type: Literal["assassination"] = "assassination"
    target_role: str
    domestic: bool = True
    rationale: str


# DEPRECATED 2026-04-15: replaced by ChangeLeaderOrder (CONTRACT_CHANGE_LEADER.md)
# class CoupAttemptOrder — removed
# class LeadProtestOrder — removed


class ChangeLeaderOrder(BaseModel):
    """Initiate leadership change vote (replaces coup_attempt + lead_protest).

    Requires: country stability ≤ threshold, non-HoS role, 3+ team members.
    Triggers: Phase 2 (removal vote) → Phase 3 (election vote).
    See CONTRACT_CHANGE_LEADER.md for full specification.
    """
    action_type: Literal["change_leader"] = "change_leader"
    rationale: str = ""


class ReassignPowersOrder(BaseModel):
    """Reassign power category to a different role (HoS only)."""
    action_type: Literal["reassign_powers"] = "reassign_powers"
    power_type: Literal["military", "economic", "foreign_affairs"]
    new_holder_role: str
    rationale: str


class CallEarlyElectionsOrder(BaseModel):
    """Call early elections (HoS only)."""
    action_type: Literal["call_early_elections"] = "call_early_elections"
    rationale: str


class SubmitNominationOrder(BaseModel):
    """Self-nominate for an upcoming election (Columbia only)."""
    action_type: Literal["submit_nomination"] = "submit_nomination"
    election_type: str  # columbia_midterms | columbia_presidential
    election_round: int  # the round the election happens
    rationale: str


class CastVoteOrder(BaseModel):
    """Cast a secret vote in an election (Columbia only)."""
    action_type: Literal["cast_vote"] = "cast_vote"
    election_type: str
    candidate_role_id: str
    rationale: str


class BasingRightsOrder(BaseModel):
    """Grant or revoke basing rights."""
    action_type: Literal["basing_rights"] = "basing_rights"
    operation: Literal["grant", "revoke"]
    guest_country: str
    zone_id: str
    rationale: str


class BlockadeOrder(BaseModel):
    """Impose a naval blockade on a chokepoint."""
    action_type: Literal["blockade"] = "blockade"
    zone_id: str  # chokepoint zone
    imposer_units: list[str]  # unit codes
    rationale: str


class MissileLaunchOrder(BaseModel):
    """Launch conventional missile strike."""
    action_type: Literal["launch_missile"] = "launch_missile"
    launcher_unit_code: str
    target_global_row: int
    target_global_col: int
    rationale: str


class NuclearTestOrder(BaseModel):
    """Conduct a nuclear test."""
    action_type: Literal["nuclear_test"] = "nuclear_test"
    rationale: str


AnyAction = Union[
    MoveUnitsOrder,
    AttackDeclarationOrder,
    SanctionOrder,
    TariffOrder,
    RDInvestmentOrder,
    PublicStatementOrder,
    OrgMeetingOrder,
    CovertOpOrder,
    TransactionOrder,
    RespondExchangeOrder,
    SignAgreementOrder,
    ArrestOrder,
    MartialLawOrder,
    AssassinationOrder,
    ChangeLeaderOrder,
    ReassignPowersOrder,
    CallEarlyElectionsOrder,
    SubmitNominationOrder,
    CastVoteOrder,
    BasingRightsOrder,
    BlockadeOrder,
    MissileLaunchOrder,
    NuclearTestOrder,
]

ACTION_TYPE_TO_MODEL: dict[str, type[BaseModel]] = {
    # Military
    "move_units": MoveUnitsOrder,
    "declare_attack": AttackDeclarationOrder,
    "blockade": BlockadeOrder,
    "launch_missile": MissileLaunchOrder,
    "nuclear_test": NuclearTestOrder,
    "basing_rights": BasingRightsOrder,
    "martial_law": MartialLawOrder,
    # Economic
    "set_sanction": SanctionOrder,
    "set_tariff": TariffOrder,
    "rd_investment": RDInvestmentOrder,
    # Covert
    "covert_op": CovertOpOrder,
    # Transactions
    "propose_transaction": TransactionOrder,
    "propose_agreement": TransactionOrder,
    "respond_exchange": RespondExchangeOrder,
    "sign_agreement": SignAgreementOrder,
    # Domestic / Political
    "arrest": ArrestOrder,
    "assassination": AssassinationOrder,
    "change_leader": ChangeLeaderOrder,
    "reassign_powers": ReassignPowersOrder,
    "call_early_elections": CallEarlyElectionsOrder,
    "submit_nomination": SubmitNominationOrder,
    "cast_vote": CastVoteOrder,
    # Communications
    "public_statement": PublicStatementOrder,
    "call_org_meeting": OrgMeetingOrder,
}


__all__ = [
    "AnyAction",
    "ACTION_TYPE_TO_MODEL",
    "MoveUnitsOrder",
    "AttackDeclarationOrder",
    "SanctionOrder",
    "TariffOrder",
    "RDInvestmentOrder",
    "PublicStatementOrder",
    "OrgMeetingOrder",
    "CovertOpOrder",
    "TransactionOrder",
    "RespondExchangeOrder",
    "SignAgreementOrder",
    "ArrestOrder",
    "MartialLawOrder",
    "AssassinationOrder",
    "ChangeLeaderOrder",
    "ReassignPowersOrder",
    "CallEarlyElectionsOrder",
    "SubmitNominationOrder",
    "CastVoteOrder",
    "BasingRightsOrder",
    "BlockadeOrder",
    "MissileLaunchOrder",
    "NuclearTestOrder",
]
