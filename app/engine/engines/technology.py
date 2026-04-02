"""TTT Technology Engine — BUILD port from SEED.

Pure functions, stateless, no DB calls.
Source: 2 SEED/D_ENGINES/world_model_engine.py (_calc_tech_advancement, _calc_rare_earth_impact)
        2 SEED/D_ENGINES/world_state.py (NUCLEAR_RD_THRESHOLDS, AI_RD_THRESHOLDS, AI_LEVEL_TECH_FACTOR)

Every formula preserved exactly from SEED.
"""

from __future__ import annotations

import random
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

# R&D multiplier (SEED fix: 0.5 -> 0.8)
RD_MULTIPLIER: float = 0.8

# Nuclear progression: 5-tier system
# L0 -> L1: subsurface test (threshold 0.60)
# L1 -> L2: open test (threshold 0.80)
# L2 -> L3: conventional missile -> single nuclear -> massive (threshold 1.00)
# L3 is max level for nuclear R&D progression
NUCLEAR_RD_THRESHOLDS: dict[int, float] = {
    0: 0.60,
    1: 0.80,
    2: 1.00,
}

# AI progression: 4 levels
# L0 -> L1 (threshold 0.20)
# L1 -> L2 (threshold 0.40)
# L2 -> L3 (threshold 0.60)
# L3 -> L4 (threshold 1.00)
AI_RD_THRESHOLDS: dict[int, float] = {
    0: 0.20,
    1: 0.40,
    2: 0.60,
    3: 1.00,
}

# Cal-3 v3: Tech boost applied to GROWTH RATE, not GDP multiplier.
# L3 adds +1.5 percentage points to growth rate (not x1.15 to GDP).
# L4 adds +3.0pp. This prevents unrealistic GDP doubling over 8 rounds.
AI_LEVEL_TECH_FACTOR: dict[int, float] = {
    0: 0.0,
    1: 0.0,
    2: 0.005,
    3: 0.015,
    4: 0.030,
}

# Combat bonus from AI level
AI_LEVEL_COMBAT_BONUS: dict[int, int] = {
    0: 0,
    1: 0,
    2: 0,
    3: 1,
    4: 2,
}

# Rare earth restriction: each level = -15% R&D efficiency, floor at 40%
RARE_EARTH_PENALTY_PER_LEVEL: float = 0.15
RARE_EARTH_FLOOR: float = 0.40


# ---------------------------------------------------------------------------
# UTILITY
# ---------------------------------------------------------------------------

def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value to [min_val, max_val]."""
    return max(min_val, min(max_val, value))


# ---------------------------------------------------------------------------
# INPUT / OUTPUT MODELS
# ---------------------------------------------------------------------------

class TechState(BaseModel):
    """Current technology state for a country."""
    nuclear_level: int = 0
    nuclear_rd_progress: float = 0.0
    ai_level: int = 0
    ai_rd_progress: float = 0.0


class RDInvestment(BaseModel):
    """R&D investment amounts for a single round."""
    nuclear: float = 0.0
    ai: float = 0.0


class TechAdvancementInput(BaseModel):
    """All inputs needed for tech advancement calculation."""
    country_id: str
    tech_state: TechState
    rd_investment: RDInvestment
    gdp: float
    rare_earth_restriction_level: int = 0  # 0 = none, 1-3 = increasing restriction


class TechAdvancementResult(BaseModel):
    """Output of tech advancement calculation."""
    nuclear_levelup: bool = False
    ai_levelup: bool = False
    new_nuclear_level: int
    new_nuclear_rd_progress: float
    new_ai_level: int
    new_ai_rd_progress: float
    rare_earth_factor: float = 1.0
    ai_l4_bonus: Optional[bool] = None  # only set when reaching L4


class RareEarthImpactResult(BaseModel):
    """Output of rare earth impact calculation."""
    factor: float
    restriction_level: int


class TechTransferInput(BaseModel):
    """Inputs for tech transfer between allies."""
    donor_country_id: str
    recipient_country_id: str
    donor_tech_state: TechState
    recipient_tech_state: TechState
    transfer_type: str  # "nuclear" | "ai"


class TechTransferResult(BaseModel):
    """Output of tech transfer."""
    success: bool
    transfer_type: str
    new_recipient_rd_progress: float
    progress_added: float
    note: str


class PersonalTechInvestmentInput(BaseModel):
    """Input for personal tech investment by specific roles (Pioneer, Circuit, etc.)."""
    country_id: str
    role_id: str
    investment_amount: float
    personal_coins: float
    gdp: float
    current_ai_rd_progress: float


class PersonalTechInvestmentResult(BaseModel):
    """Output of personal tech investment."""
    applied: bool
    coins_spent: float = 0.0
    progress_boost: float = 0.0
    new_ai_rd_progress: float
    note: str = ""


# ---------------------------------------------------------------------------
# TECHNOLOGY ENGINE — PURE FUNCTIONS
# ---------------------------------------------------------------------------

def calc_rare_earth_impact(restriction_level: int) -> RareEarthImpactResult:
    """Rare earth restrictions slow R&D. Each level = -15%, floor 40%.

    restriction_level 0: factor = 1.0 (no restriction)
    restriction_level 1: factor = 0.85
    restriction_level 2: factor = 0.70
    restriction_level 3: factor = 0.55
    restriction_level 4: factor = 0.40 (floor)
    """
    if restriction_level <= 0:
        return RareEarthImpactResult(factor=1.0, restriction_level=0)

    rd_penalty = 1.0 - (restriction_level * RARE_EARTH_PENALTY_PER_LEVEL)
    factor = max(RARE_EARTH_FLOOR, rd_penalty)

    return RareEarthImpactResult(factor=factor, restriction_level=restriction_level)


def calc_tech_advancement(inp: TechAdvancementInput) -> TechAdvancementResult:
    """R&D with fixed multiplier 0.8 and rare earth impact.

    Nuclear R&D: (investment / GDP) * RD_MULTIPLIER * rare_earth_factor -> progress.
    When progress >= threshold for current level, level up and reset progress to 0.

    AI R&D: same formula. At L4, 50% chance of combat bonus (determined once).

    Nuclear max level: 3.
    AI max level: 4.
    """
    tech = inp.tech_state.model_copy()
    gdp = inp.gdp
    result_nuclear_levelup = False
    result_ai_levelup = False
    ai_l4_bonus: Optional[bool] = None

    # Rare earth impact on R&D
    rare_earth = calc_rare_earth_impact(inp.rare_earth_restriction_level)
    rare_earth_factor = rare_earth.factor

    # --- Nuclear R&D ---
    nuc_invest = inp.rd_investment.nuclear
    if nuc_invest > 0 and gdp > 0:
        nuc_progress = (nuc_invest / max(gdp, 0.01)) * RD_MULTIPLIER * rare_earth_factor
        tech.nuclear_rd_progress += nuc_progress

    nuc_threshold = NUCLEAR_RD_THRESHOLDS.get(tech.nuclear_level, 999.0)
    if tech.nuclear_rd_progress >= nuc_threshold and tech.nuclear_level < 3:
        tech.nuclear_level += 1
        tech.nuclear_rd_progress = 0.0
        result_nuclear_levelup = True

    # --- AI R&D ---
    ai_invest = inp.rd_investment.ai
    if ai_invest > 0 and gdp > 0:
        ai_progress = (ai_invest / max(gdp, 0.01)) * RD_MULTIPLIER * rare_earth_factor
        tech.ai_rd_progress += ai_progress

    ai_threshold = AI_RD_THRESHOLDS.get(tech.ai_level, 999.0)
    if tech.ai_rd_progress >= ai_threshold and tech.ai_level < 4:
        tech.ai_level += 1
        tech.ai_rd_progress = 0.0
        result_ai_levelup = True
        # When reaching L4, randomly determine if country gets combat bonus
        # (determined once, never changes -- per ACTION REVIEW 2026-03-30)
        if tech.ai_level == 4:
            ai_l4_bonus = random.random() < 0.50

    return TechAdvancementResult(
        nuclear_levelup=result_nuclear_levelup,
        ai_levelup=result_ai_levelup,
        new_nuclear_level=tech.nuclear_level,
        new_nuclear_rd_progress=round(tech.nuclear_rd_progress, 6),
        new_ai_level=tech.ai_level,
        new_ai_rd_progress=round(tech.ai_rd_progress, 6),
        rare_earth_factor=rare_earth_factor,
        ai_l4_bonus=ai_l4_bonus,
    )


def get_ai_tech_growth_bonus(ai_level: int) -> float:
    """Return GDP growth rate bonus from AI level.

    L0-L1: 0.0
    L2: +0.5pp
    L3: +1.5pp
    L4: +3.0pp
    """
    return AI_LEVEL_TECH_FACTOR.get(ai_level, 0.0)


def get_ai_combat_bonus(ai_level: int) -> int:
    """Return combat die bonus from AI level.

    L0-L2: 0
    L3: +1
    L4: +2
    """
    return AI_LEVEL_COMBAT_BONUS.get(ai_level, 0)


def calc_tech_transfer(inp: TechTransferInput) -> TechTransferResult:
    """Tech transfer between allies.

    Donor must be at least 1 level ahead in the transfer domain.
    Transfer adds a fixed progress boost to recipient (does NOT level up directly).
    Nuclear transfer: +0.20 progress.
    AI transfer: +0.15 progress.
    """
    if inp.transfer_type == "nuclear":
        donor_level = inp.donor_tech_state.nuclear_level
        recipient_level = inp.recipient_tech_state.nuclear_level
        recipient_progress = inp.recipient_tech_state.nuclear_rd_progress
        progress_boost = 0.20
    elif inp.transfer_type == "ai":
        donor_level = inp.donor_tech_state.ai_level
        recipient_level = inp.recipient_tech_state.ai_level
        recipient_progress = inp.recipient_tech_state.ai_rd_progress
        progress_boost = 0.15
    else:
        return TechTransferResult(
            success=False,
            transfer_type=inp.transfer_type,
            new_recipient_rd_progress=0.0,
            progress_added=0.0,
            note=f"Unknown transfer type: {inp.transfer_type}",
        )

    # Donor must be at least 1 level ahead
    if donor_level <= recipient_level:
        return TechTransferResult(
            success=False,
            transfer_type=inp.transfer_type,
            new_recipient_rd_progress=recipient_progress,
            progress_added=0.0,
            note=(f"Transfer failed: {inp.donor_country_id} ({inp.transfer_type} "
                  f"L{donor_level}) not ahead of {inp.recipient_country_id} (L{recipient_level})."),
        )

    new_progress = recipient_progress + progress_boost

    return TechTransferResult(
        success=True,
        transfer_type=inp.transfer_type,
        new_recipient_rd_progress=round(new_progress, 6),
        progress_added=progress_boost,
        note=(f"Tech transfer: {inp.donor_country_id} -> {inp.recipient_country_id} "
              f"({inp.transfer_type} +{progress_boost})."),
    )


def calc_personal_tech_investment(inp: PersonalTechInvestmentInput) -> PersonalTechInvestmentResult:
    """Personal tech investment by specific roles (Pioneer, Circuit, Dealer).

    Personal investment is 50% as efficient as government R&D.
    Efficiency factor: 0.4 (investment / GDP * 0.4 -> progress boost).
    Only applies to AI R&D.
    """
    if inp.investment_amount <= 0:
        return PersonalTechInvestmentResult(
            applied=False,
            new_ai_rd_progress=inp.current_ai_rd_progress,
            note="No investment amount.",
        )

    if inp.personal_coins < inp.investment_amount:
        return PersonalTechInvestmentResult(
            applied=False,
            new_ai_rd_progress=inp.current_ai_rd_progress,
            note=f"Insufficient coins: {inp.personal_coins} < {inp.investment_amount}.",
        )

    if inp.gdp <= 0:
        return PersonalTechInvestmentResult(
            applied=False,
            new_ai_rd_progress=inp.current_ai_rd_progress,
            note="GDP is zero or negative.",
        )

    # Personal investment is 50% as efficient as government R&D
    progress_boost = (inp.investment_amount / inp.gdp) * 0.4
    new_progress = inp.current_ai_rd_progress + progress_boost

    return PersonalTechInvestmentResult(
        applied=True,
        coins_spent=inp.investment_amount,
        progress_boost=round(progress_boost, 6),
        new_ai_rd_progress=round(new_progress, 6),
        note=(f"{inp.role_id} invested {inp.investment_amount} personal coins in "
              f"{inp.country_id} AI R&D (+{progress_boost:.4f} progress)."),
    )
