"""Judgment input/output schemas — Pydantic models for structured LLM output.

Source: SEED_D10_ENGINE_JUDGMENT_v1.md (Section 3.3: Output Schema)
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class CrisisDeclaration(BaseModel):
    """AI determines a country enters or exits crisis."""
    country: str
    crisis_state: str = Field(description="'crisis' or 'normal' (exiting crisis)")
    gdp_penalty_pct: float = Field(ge=-2.0, le=0.0, description="-1% to -2% GDP penalty")
    argument: str = Field(description="Compact reasoning for this declaration")


class ContagionEffect(BaseModel):
    """Crisis spreading from one country to another."""
    from_country: str
    to_country: str
    channel: str = Field(description="Energy, trade, financial, confidence")
    gdp_impact_pct: float = Field(ge=-2.0, le=0.0)
    argument: str


class StabilityAdjustment(BaseModel):
    """Stability nudge beyond formula capture."""
    country: str
    delta: float = Field(ge=-0.5, le=0.5)
    argument: str


class SupportAdjustment(BaseModel):
    """Political support nudge beyond formula capture."""
    country: str
    delta: float = Field(ge=-5.0, le=5.0)
    argument: str


class MarketIndexNudge(BaseModel):
    """Market index adjustment for sentiment."""
    index: str = Field(description="wall_street, europa, or dragon")
    delta: float = Field(ge=-10.0, le=10.0)
    argument: str


class CapitulationRecommendation(BaseModel):
    """Recommendation that a country might surrender or seek ceasefire."""
    country: str
    likelihood: str = Field(description="low, medium, high")
    argument: str


class JudgmentResult(BaseModel):
    """Complete output of one Pass 2 judgment call.

    Every field has explicit bounds. The orchestrator validates before applying.
    """
    round_num: int
    crisis_declarations: list[CrisisDeclaration] = Field(default_factory=list)
    contagion_effects: list[ContagionEffect] = Field(default_factory=list)
    stability_adjustments: list[StabilityAdjustment] = Field(default_factory=list)
    support_adjustments: list[SupportAdjustment] = Field(default_factory=list)
    market_index_nudges: list[MarketIndexNudge] = Field(default_factory=list)
    capitulation_recommendations: list[CapitulationRecommendation] = Field(default_factory=list)
    flags: list[str] = Field(default_factory=list, description="Warning flags for moderator attention")
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    reasoning_summary: str = ""


# ---------------------------------------------------------------------------
# BOUNDS (for validation before applying)
# ---------------------------------------------------------------------------

JUDGMENT_BOUNDS = {
    "stability_delta": (-0.5, 0.5),
    "support_delta": (-5.0, 5.0),
    "gdp_crisis_penalty": (-2.0, -1.0),
    "contagion_gdp_impact": (-2.0, 0.0),
    "market_index_nudge": (-10.0, 10.0),
    "max_contagion_countries": 5,
    "max_crisis_declarations": 5,
}


def validate_and_clamp(result: JudgmentResult) -> tuple[JudgmentResult, list[str]]:
    """Validate bounds and clamp any out-of-range values. Returns (result, warnings)."""
    warnings = []

    for adj in result.stability_adjustments:
        lo, hi = JUDGMENT_BOUNDS["stability_delta"]
        if not (lo <= adj.delta <= hi):
            warnings.append(f"Stability adj for {adj.country} clamped: {adj.delta} → [{lo}, {hi}]")
            adj.delta = max(lo, min(hi, adj.delta))

    for adj in result.support_adjustments:
        lo, hi = JUDGMENT_BOUNDS["support_delta"]
        if not (lo <= adj.delta <= hi):
            warnings.append(f"Support adj for {adj.country} clamped: {adj.delta} → [{lo}, {hi}]")
            adj.delta = max(lo, min(hi, adj.delta))

    for decl in result.crisis_declarations:
        lo, hi = JUDGMENT_BOUNDS["gdp_crisis_penalty"]
        if not (lo <= decl.gdp_penalty_pct <= 0):
            warnings.append(f"Crisis penalty for {decl.country} clamped: {decl.gdp_penalty_pct}")
            decl.gdp_penalty_pct = max(lo, min(0, decl.gdp_penalty_pct))

    for eff in result.contagion_effects:
        lo, hi = JUDGMENT_BOUNDS["contagion_gdp_impact"]
        if not (lo <= eff.gdp_impact_pct <= 0):
            warnings.append(f"Contagion for {eff.to_country} clamped: {eff.gdp_impact_pct}")
            eff.gdp_impact_pct = max(lo, min(0, eff.gdp_impact_pct))

    for nudge in result.market_index_nudges:
        lo, hi = JUDGMENT_BOUNDS["market_index_nudge"]
        if not (lo <= nudge.delta <= hi):
            warnings.append(f"Market nudge for {nudge.index} clamped: {nudge.delta}")
            nudge.delta = max(lo, min(hi, nudge.delta))

    max_cont = JUDGMENT_BOUNDS["max_contagion_countries"]
    if len(result.contagion_effects) > max_cont:
        warnings.append(f"Contagion effects truncated: {len(result.contagion_effects)} → {max_cont}")
        result.contagion_effects = result.contagion_effects[:max_cont]

    return result, warnings
