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

    action_type: Literal["ground_attack", "air_strike", "naval_combat", "naval_bombardment", "ground_move"] = "ground_attack"
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

    action_type: Literal["set_sanctions"] = "set_sanctions"
    target_country: str
    sanction_type: str  # e.g. "oil_export_ban", "financial", "tech_export"
    level: int = Field(..., ge=-3, le=3)
    rationale: str


class TariffOrder(BaseModel):
    """Impose tariffs on another country."""

    action_type: Literal["set_tariffs"] = "set_tariffs"
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


class DeclareWarOrder(BaseModel):
    """Declare war on another country."""
    action_type: Literal["declare_war"] = "declare_war"
    target_country: str
    rationale: str


class OrgMeetingOrder(BaseModel):
    """Call an organization meeting."""
    action_type: Literal["call_org_meeting"] = "call_org_meeting"
    organization_code: str
    agenda: str
    rationale: str


class CovertOpOrder(BaseModel):
    """Covert operation."""
    action_type: Literal["covert_operation"] = "covert_operation"
    op_type: str  # intelligence | sabotage | propaganda
    target_country: Optional[str] = None
    target_type: Optional[str] = None  # infrastructure | nuclear_tech | military (sabotage)
    intent: Optional[str] = None  # boost | destabilize (propaganda)
    question: Optional[str] = None  # free text (intelligence)
    content: Optional[str] = None  # narrative (propaganda)
    rationale: str


class IntelligenceOrder(BaseModel):
    """Standalone intelligence report request."""
    action_type: Literal["intelligence"] = "intelligence"
    op_type: str = "intelligence"
    question: Optional[str] = None
    target_country: Optional[str] = None
    rationale: str


class TransactionOrder(BaseModel):
    """Propose exchange transaction or agreement.

    For propose_transaction: offer and request use ONLY these asset keys:
    - coins: integer (treasury amount)
    - units: list of unit_code strings to transfer
    - technology: dict like {"ai": true} or {"nuclear": true}
    - basing_rights: dict like {"zone_id": "zone_name", "guest_country": "code"}

    For propose_agreement: use terms (free text) + agreement_name + agreement_type.
    Agreements are diplomatic (no asset transfer), transactions are economic (real assets).
    """
    action_type: Literal["propose_transaction", "propose_agreement"]
    counterpart_country: str
    terms: Optional[str] = Field(None, description="Free-text terms (especially for propose_agreement)")
    offer: Optional[dict] = Field(None, description="Assets you offer. Keys: coins, units, technology, basing_rights ONLY")
    request: Optional[dict] = Field(None, description="Assets you request. Keys: coins, units, technology, basing_rights ONLY")
    agreement_name: Optional[str] = Field(None, description="Name for the agreement (propose_agreement only)")
    agreement_type: Optional[str] = Field(None, description="Type: diplomatic, trade, military, ceasefire (propose_agreement only)")
    visibility: Optional[str] = "public"
    rationale: str


class RespondExchangeOrder(BaseModel):
    """Respond to a proposed transaction (accept/decline/counter)."""
    action_type: Literal["accept_transaction"] = "accept_transaction"
    transaction_id: str
    response: Literal["accept", "decline", "counter"]
    counter_offer: Optional[dict] = None
    rationale: str


class SignAgreementOrder(BaseModel):
    """Sign or decline a proposed agreement."""
    action_type: Literal["sign_agreement"] = "sign_agreement"
    agreement_id: str
    confirm: bool = True  # True = sign, False = decline
    comments: str = ""
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
    action_type: Literal["reassign_types"] = "reassign_types"
    power_type: Literal["military", "economic", "foreign_affairs"]
    new_holder_role: str
    rationale: str


class CallEarlyElectionsOrder(BaseModel):
    """Call early elections (HoS only)."""
    action_type: Literal["call_early_elections"] = "call_early_elections"
    rationale: str


class SubmitNominationOrder(BaseModel):
    """Self-nominate for an upcoming election (Columbia only)."""
    action_type: Literal["self_nominate"] = "self_nominate"
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
    """Impose, lift, or reduce a naval blockade on a chokepoint."""
    action_type: Literal["naval_blockade"] = "naval_blockade"
    operation: Literal["establish", "lift", "reduce"] = "establish"
    zone_id: str  # chokepoint zone
    level: Literal["full", "partial"] = "full"
    imposer_units: list[str] = Field(default_factory=list)  # unit codes (for establish)
    rationale: str


class MissileLaunchOrder(BaseModel):
    """Launch conventional missile strike.

    target_type selects what the missile aims at:
    - military: enemy units
    - infrastructure: GDP damage
    - nuclear_site: damage nuclear R&D
    - ad: destroy air defense
    """
    action_type: Literal["launch_missile_conventional"] = "launch_missile_conventional"
    launcher_unit_code: str
    target_global_row: int
    target_global_col: int
    target_type: Literal["military", "infrastructure", "nuclear_site", "ad"] = "military"
    rationale: str


class BudgetOrder(BaseModel):
    """Set budget allocations — CONTRACT_BUDGET v1.1.

    Batch action queued for Phase B engine processing.

    Fields:
        social_pct: Social spending multiplier (0.5-1.5× baseline).
            1.0 = baseline. <1.0 = cut (damages stability/support). >1.0 = boost.
        production: Per-branch military production levels (0-4).
            0=none, 1=standard, 2=accelerated (2× cost), 3=surge (3× cost), 4=max (4× cost).
            Branches: ground, naval, tactical_air, strategic_missile, air_defense.
        research: R&D coin allocation split between nuclear and AI tracks.
            nuclear_coins: coins for nuclear R&D (progress = coins/GDP × 0.8).
            ai_coins: coins for AI R&D.
    """
    action_type: Literal["set_budget"] = "set_budget"
    social_pct: float = Field(1.0, ge=0.5, le=1.5, description="Social spending multiplier (0.5-1.5× baseline)")
    production: Optional[dict] = Field(default_factory=dict, description="Per-branch production levels: {ground: 0-4, naval: 0-4, tactical_air: 0-4, strategic_missile: 0-4, air_defense: 0-4}")
    research: Optional[dict] = Field(default_factory=dict, description="R&D allocation: {nuclear_coins: int, ai_coins: int}")
    rationale: str


class SetOpecOrder(BaseModel):
    """Set OPEC production level."""
    action_type: Literal["set_opec"] = "set_opec"
    production: str  # min | low | normal | high | max
    rationale: str


class NuclearTestOrder(BaseModel):
    """Conduct a nuclear test.

    test_type: underground (lower risk, -0.2 stability) or surface (higher impact,
    -0.4 global stability, -0.6 adjacent, -5% own GDP, +5 support).
    """
    action_type: Literal["nuclear_test"] = "nuclear_test"
    test_type: Literal["underground", "surface"] = "underground"
    rationale: str


class NuclearLaunchOrder(BaseModel):
    """Initiate nuclear launch sequence.

    missiles: list of strategic_missile unit_ids to launch (from get_my_forces).
    """
    action_type: Literal["nuclear_launch_initiate"] = "nuclear_launch_initiate"
    target_country: str
    missiles: list[str] = Field(default_factory=list, description="Unit IDs of missiles to launch")
    target_global_row: Optional[int] = None
    target_global_col: Optional[int] = None
    rationale: str


class NuclearAuthorizeOrder(BaseModel):
    """Authorize or deny a nuclear launch (co-authorization step)."""
    action_type: Literal["nuclear_authorize"] = "nuclear_authorize"
    nuclear_action_id: str
    authorize: bool = True
    rationale: str


class NuclearInterceptOrder(BaseModel):
    """Attempt to intercept an incoming nuclear strike."""
    action_type: Literal["nuclear_intercept"] = "nuclear_intercept"
    nuclear_action_id: str
    intercept: bool = True
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
    BudgetOrder,
]

ACTION_TYPE_TO_MODEL: dict[str, type[BaseModel]] = {
    # Military
    "move_units": MoveUnitsOrder,
    "ground_attack": AttackDeclarationOrder,
    "air_strike": AttackDeclarationOrder,
    "naval_combat": AttackDeclarationOrder,
    "naval_bombardment": AttackDeclarationOrder,
    "ground_move": AttackDeclarationOrder,
    "naval_blockade": BlockadeOrder,
    "launch_missile_conventional": MissileLaunchOrder,
    "nuclear_test": NuclearTestOrder,
    "nuclear_launch_initiate": NuclearLaunchOrder,
    "nuclear_authorize": NuclearAuthorizeOrder,
    "nuclear_intercept": NuclearInterceptOrder,
    "basing_rights": BasingRightsOrder,
    "martial_law": MartialLawOrder,
    # Economic
    "set_budget": BudgetOrder,
    "set_sanctions": SanctionOrder,
    "set_tariffs": TariffOrder,
    "set_opec": SetOpecOrder,
    # rd_investment is part of set_budget, not a standalone action
    # Covert
    "covert_operation": CovertOpOrder,
    "intelligence": IntelligenceOrder,
    # Transactions
    "propose_transaction": TransactionOrder,
    "accept_transaction": RespondExchangeOrder,
    "sign_agreement": SignAgreementOrder,
    # Domestic / Political
    "arrest": ArrestOrder,
    "assassination": AssassinationOrder,
    "change_leader": ChangeLeaderOrder,
    "reassign_types": ReassignPowersOrder,
    "self_nominate": SubmitNominationOrder,
    "cast_vote": CastVoteOrder,
    # Communications
    "public_statement": PublicStatementOrder,
    "declare_war": DeclareWarOrder,
    "propose_agreement": TransactionOrder,
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
    "BudgetOrder",
]
