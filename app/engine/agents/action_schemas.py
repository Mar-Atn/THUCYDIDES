"""Pydantic v2 schemas for Stage 4 agent action commits.

Seven structured action types covering the four domains (military, economic,
political, technological). Agents emit one of these via the ``commit_action``
tool; the payload is validated and persisted to ``agent_decisions``.
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
]

ACTION_TYPE_TO_MODEL: dict[str, type[BaseModel]] = {
    "move_units": MoveUnitsOrder,
    "declare_attack": AttackDeclarationOrder,
    "set_sanction": SanctionOrder,
    "set_tariff": TariffOrder,
    "rd_investment": RDInvestmentOrder,
    "public_statement": PublicStatementOrder,
    "call_org_meeting": OrgMeetingOrder,
    "covert_op": CovertOpOrder,
    "propose_transaction": TransactionOrder,
    "propose_agreement": TransactionOrder,
}


__all__ = [
    "MoveUnitsOrder",
    "AttackDeclarationOrder",
    "SanctionOrder",
    "TariffOrder",
    "RDInvestmentOrder",
    "AnyAction",
    "ACTION_TYPE_TO_MODEL",
]
