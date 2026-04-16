"""TTT Political Engine — BUILD port from SEED.

Pure functions, stateless, no DB calls.
Source: 2 SEED/D_ENGINES/world_model_engine.py (_calc_stability, _calc_political_support,
        _process_election, _check_revolution, _check_health_events, _update_war_tiredness,
        _update_threshold_flags, _check_capitulation)
        2 SEED/D_ENGINES/live_action_engine.py (resolve_coup, resolve_assassination)

Every formula preserved exactly from SEED.
"""

from __future__ import annotations

import random
from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

STABILITY_THRESHOLDS = {
    "unstable": 6,
    "protest_probable": 5,
    "protest_automatic": 3,
    "regime_collapse_risk": 2,
    "failed_state": 1,
}

CRISIS_STABILITY_PENALTY: dict[str, float] = {
    "normal": 0.0,
    "stressed": -0.10,
    "crisis": -0.30,
    "collapse": -0.50,
}

# DEPRECATED 2026-04-16: Orchestrator now reads key_events from sim_runs table (M4 Sprint 4.2).
# This hardcoded dict is kept empty for backward compatibility with old test scripts.
# DO NOT ADD EVENTS HERE. Use sim_runs.key_events (JSONB) configured via the wizard.
SCHEDULED_EVENTS: dict[int, list[dict[str, str]]] = {}

# Elderly leaders subject to health events (age, medical quality 0-1)
ELDERLY_LEADERS: dict[str, dict[str, Any]] = {
    "columbia": {"role": "dealer", "age": 80, "medical_quality": 0.9},
    "cathay": {"role": "helmsman", "age": 73, "medical_quality": 0.7},
    "sarmatia": {"role": "pathfinder", "age": 73, "medical_quality": 0.6},
}

# Country-specific assassination bonuses (international only)
ASSASSINATION_COUNTRY_BONUS: dict[str, float] = {
    "levantia": 0.30,  # total 50% (20% + 30%)
    "sarmatia": 0.10,  # total 30% (20% + 10%)
}


# ---------------------------------------------------------------------------
# UTILITY
# ---------------------------------------------------------------------------

def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value to [min_val, max_val]."""
    return max(min_val, min(max_val, value))


# ---------------------------------------------------------------------------
# INPUT / OUTPUT MODELS
# ---------------------------------------------------------------------------

class StabilityInput(BaseModel):
    """All inputs needed for stability calculation."""
    country_id: str
    stability: float
    regime_type: str  # democracy | autocracy | hybrid
    gdp_growth_rate: float
    economic_state: str  # normal | stressed | crisis | collapse
    inflation: float
    starting_inflation: float
    sanctions_rounds: int = 0  # DEPRECATED 2026-04-10 — unused, retained only for backward compat with old callers

    # War context
    at_war: bool = False
    is_primary_belligerent: bool = False
    is_frontline_defender: bool = False
    war_tiredness: float = 0.0

    # Sanctions
    sanctions_level: int = 0
    sanctions_pain: float = 0.0
    gdp: float = 0.0

    # Market index stress (from regional indexes)
    market_stress: float = 0.0  # 0.0, -0.10 (stress), -0.30 (crisis)

    # Events this round
    social_spending_ratio: float = 0.20
    social_spending_baseline: float = 0.30
    casualties: int = 0
    territory_lost: int = 0
    territory_gained: int = 0
    mobilization_level: int = 0
    propaganda_boost: float = 0.0


class StabilityResult(BaseModel):
    """Output of stability calculation."""
    old_stability: float
    new_stability: float
    delta: float


class PoliticalSupportInput(BaseModel):
    """All inputs needed for political support calculation."""
    country_id: str
    political_support: float
    stability: float
    regime_type: str
    gdp_growth_rate: float
    economic_state: str
    oil_price: float = 80.0
    oil_producer: bool = False
    round_num: int = 1

    # War context
    casualties: int = 0
    war_tiredness: float = 0.0

    # Autocracy-specific
    perceived_weakness: float = 0.0
    repression_effect: float = 0.0
    nationalist_rally: float = 0.0


class PoliticalSupportResult(BaseModel):
    """Output of political support calculation."""
    old_support: float
    new_support: float
    delta: float


class ElectionInput(BaseModel):
    """All inputs needed for election processing."""
    country_id: str
    election_type: str  # columbia_midterms | ruthenia_wartime | ruthenia_wartime_runoff | columbia_presidential
    round_num: int
    gdp_growth_rate: float
    stability: float
    economic_state: str
    oil_price: float
    oil_producer: bool = False
    war_tiredness: float = 0.0

    # Wars the country is involved in
    wars: list[dict[str, Any]] = Field(default_factory=list)

    # Event log for political crisis modifiers and foreign policy bonuses
    events_log: list[dict[str, Any]] = Field(default_factory=list)

    # Player vote input
    incumbent_pct: float = 50.0


class ElectionResult(BaseModel):
    """Output of election processing."""
    election_type: str
    country: str
    ai_score: float
    player_score: float
    final_incumbent_pct: float
    incumbent_wins: bool
    crisis_penalty: float
    oil_penalty: float
    parliament_change: Optional[str] = None
    note: str = ""


class RevolutionResult(BaseModel):
    """Output of revolution/protest check."""
    event: str = "mass_protests"
    country: str
    severity: str  # severe | major
    stability: float
    support: float
    elite_can_lead: bool = True
    base_success_probability: float
    note: str


class HealthEventResult(BaseModel):
    """Output of health event check."""
    event: str  # leader_death | leader_incapacitated
    country: str
    role: str
    duration: int = 0
    note: str
    succession_required: bool = False
    effects: str = ""


class WarTirednessInput(BaseModel):
    """All inputs needed for war tiredness update."""
    country_id: str
    war_tiredness: float
    at_war: bool
    is_defender: bool = False
    is_attacker: bool = False
    is_ally: bool = False
    war_duration: int = 0  # rounds at war


class WarTirednessResult(BaseModel):
    """Output of war tiredness update."""
    old_war_tiredness: float
    new_war_tiredness: float


class ThresholdFlagsResult(BaseModel):
    """Output of threshold flag update."""
    protest_risk: bool
    coup_risk: bool
    regime_status: str  # stable | unstable | crisis


class CoupInput(BaseModel):
    """All inputs needed for coup resolution."""
    country_id: str
    plotters: list[str]  # exactly 2 role IDs
    stability: float
    political_support: float
    protest_active: bool = False
    protest_risk: bool = False


class CoupResult(BaseModel):
    """Output of coup resolution."""
    success: bool
    probability: float
    initiator: str
    co_conspirator: str
    stability_change: float
    note: str


class AssassinationInput(BaseModel):
    """All inputs needed for assassination resolution."""
    country_id: str
    target_role: str
    domestic: bool = False


class AssassinationResult(BaseModel):
    """Output of assassination resolution."""
    hit: bool
    detected: bool
    probability: float
    target_survived: Optional[bool] = None
    martyr_effect: int = 0
    note: str


# ---------------------------------------------------------------------------
# POLITICAL ENGINE — PURE FUNCTIONS
# ---------------------------------------------------------------------------

def calc_stability(inp: StabilityInput) -> StabilityResult:
    """V4 stability with crisis state penalty and inflation delta fix.

    Keeps: democratic resilience, siege resilience, society adaptation.
    Adds: crisis state penalty, inflation delta (not absolute), GDP cap.
    Fixes: Sarmatia siege resilience for sanctioned autocracies.
    """
    old_stab = inp.stability
    delta = 0.0

    regime = inp.regime_type
    eco_state = inp.economic_state
    at_war = inp.at_war
    under_heavy_sanctions = inp.sanctions_level >= 2

    # --- POSITIVE INERTIA (only at high stability) ---
    if 7 <= old_stab < 9:
        delta += 0.05

    # --- GDP GROWTH (capped contraction penalty at -0.30) ---
    gdp_growth = inp.gdp_growth_rate
    if gdp_growth > 2:
        delta += min((gdp_growth - 2) * 0.08, 0.15)
    elif gdp_growth < -2:
        # Cap GDP contraction stability penalty at -0.30/round
        delta += max(gdp_growth * 0.15, -0.30)

    # --- SOCIAL SPENDING (linear model, 2026-04-09) ---
    # social_pct = actual spending as fraction of baseline (1.0 = 100% = normal)
    # Linear: delta_from_normal_pct / 25. So 50% cut → -2, 50% increase → +2.
    # This gives meaningful stability impact from budget decisions.
    social_ratio = inp.social_spending_ratio
    baseline = inp.social_spending_baseline
    social_pct = social_ratio / max(baseline, 0.01) if baseline > 0 else 1.0
    social_delta_pct = (social_pct - 1.0) * 100  # e.g., 0.5 → -50, 1.5 → +50
    delta += social_delta_pct / 25.0  # -50% → -2.0, +50% → +2.0

    # --- WAR FRICTION (v4: reduced, with democratic resilience) ---
    if at_war:
        if inp.is_frontline_defender:
            delta -= 0.10
        elif inp.is_primary_belligerent:
            delta -= 0.08
        else:
            delta -= 0.05

        delta -= inp.casualties * 0.2
        delta -= inp.territory_lost * 0.4
        delta += inp.territory_gained * 0.15
        delta -= min(inp.war_tiredness * 0.04, 0.4)

        # Wartime democratic resilience
        if inp.is_frontline_defender and regime in ("democracy", "hybrid"):
            delta += 0.15

    # --- SANCTIONS FRICTION ---
    # (2026-04-10 CONTRACT_SANCTIONS v1.0: "diminishing returns after 4 rounds"
    #  adaptation REMOVED for consistency with the new stateless sanctions model.
    #  sanctions_rounds counter is no longer populated; the full friction applies
    #  whenever sanctions_level > 0.)
    if inp.sanctions_level > 0:
        delta -= 0.1 * inp.sanctions_level

    if under_heavy_sanctions:
        sanc_hit = inp.sanctions_pain
        if inp.gdp > 0:
            sanc_hit = sanc_hit / inp.gdp
        delta -= abs(sanc_hit) * 0.8

    # --- INFLATION FRICTION (DELTA from baseline, not absolute) ---
    # Cal-4 v3: Cap inflation friction at -0.50 per round
    inflation_delta = inp.inflation - inp.starting_inflation
    inflation_friction = 0.0
    if inflation_delta > 3:
        inflation_friction -= (inflation_delta - 3) * 0.05
    if inflation_delta > 20:
        inflation_friction -= (inflation_delta - 20) * 0.03
    inflation_friction = max(inflation_friction, -0.50)  # Cal-4 cap
    delta += inflation_friction

    # --- CRISIS STATE PENALTY ---
    delta += CRISIS_STABILITY_PENALTY.get(eco_state, 0.0)

    # --- MARKET INDEX STRESS (from regional financial indexes) ---
    delta += inp.market_stress

    # --- MOBILIZATION ---
    if inp.mobilization_level > 0:
        delta -= inp.mobilization_level * 0.2

    # --- PROPAGANDA ---
    delta += inp.propaganda_boost

    # --- PEACEFUL NON-SANCTIONED DAMPENING ---
    if not at_war and not under_heavy_sanctions:
        if delta < 0:
            delta *= 0.5

    # --- AUTOCRACY RESILIENCE ---
    if regime == "autocracy":
        if delta < 0:
            delta *= 0.75

    # --- SIEGE RESILIENCE: sanctioned autocracies at war ---
    if regime == "autocracy" and at_war and under_heavy_sanctions:
        delta += 0.10  # institutional adaptation to siege conditions

    # HARD CAP at 9.0, FLOOR at 1.0
    new_stab = clamp(old_stab + delta, 1.0, 9.0)
    new_stab = round(new_stab, 2)

    return StabilityResult(
        old_stability=old_stab,
        new_stability=new_stab,
        delta=round(delta, 4),
    )


def calc_political_support(inp: PoliticalSupportInput) -> PoliticalSupportResult:
    """Support calculation with crisis modifiers and oil penalty.

    Democracy/hybrid: GDP growth, casualties, stability, crisis state, oil, election proximity, war tiredness.
    Autocracy: stability-driven, perceived weakness, repression, nationalism.
    Mean-reversion toward 50%.
    """
    old_sup = inp.political_support
    delta = 0.0

    regime = inp.regime_type
    eco_state = inp.economic_state

    if regime in ("democracy", "hybrid"):
        delta += (inp.gdp_growth_rate - 2.0) * 0.8
        delta -= inp.casualties * 3.0
        delta += (inp.stability - 6.0) * 0.5

        # Crisis penalty on incumbents
        if eco_state == "crisis":
            delta -= 5.0
        elif eco_state == "collapse":
            delta -= 10.0
        elif eco_state == "stressed":
            delta -= 2.0

        # Oil price shock penalty on incumbents
        if inp.oil_price > 150 and not inp.oil_producer:
            delta -= (inp.oil_price - 150) * 0.05  # -2.5 at $200

        # Election proximity effect
        if inp.country_id == "columbia":
            if inp.round_num == 1:
                delta -= 1.0
            elif inp.round_num == 4:
                delta -= 2.0
        elif inp.country_id == "ruthenia":
            if inp.round_num in (2, 3):
                delta -= 1.5

        # War tiredness damages support
        if inp.war_tiredness > 2:
            delta -= (inp.war_tiredness - 2) * 1.0
    else:
        # Autocracy
        delta += (inp.stability - 6.0) * 0.8
        delta -= inp.perceived_weakness * 5.0
        delta += inp.repression_effect
        delta += inp.nationalist_rally

    # Mean-reversion toward 50%
    delta -= (old_sup - 50.0) * 0.05

    new_sup = clamp(old_sup + delta, 5.0, 85.0)
    new_sup = round(new_sup, 2)

    return PoliticalSupportResult(
        old_support=old_sup,
        new_support=new_sup,
        delta=round(delta, 4),
    )


def process_election(inp: ElectionInput) -> ElectionResult:
    """Elections with crisis modifiers, oil penalty, endorsement toxicity.

    AI incumbent score (base) = 50 + econ_perf + stab_factor + war_penalty
        + crisis_penalty + oil_penalty + political_crisis_penalty + foreign_policy_bonus.
    Final = 0.5 * AI score + 0.5 * player incumbent vote.
    """
    gdp_growth = inp.gdp_growth_rate
    stability = inp.stability
    eco_state = inp.economic_state
    oil_price = inp.oil_price

    # AI incumbent score (base)
    econ_perf = gdp_growth * 10.0
    stab_factor = (stability - 5) * 5.0

    # War penalty
    war_penalty = 0.0
    for war in inp.wars:
        if (war.get("attacker") == inp.country_id or
                war.get("defender") == inp.country_id or
                inp.country_id in war.get("allies", {}).get("attacker", []) or
                inp.country_id in war.get("allies", {}).get("defender", [])):
            war_penalty -= 5.0

    # Crisis penalty
    crisis_penalty = 0.0
    if eco_state == "stressed":
        crisis_penalty = -5.0
    elif eco_state == "crisis":
        crisis_penalty = -15.0
    elif eco_state == "collapse":
        crisis_penalty = -25.0

    # Oil penalty for importers
    oil_penalty = 0.0
    if oil_price > 150 and not inp.oil_producer:
        oil_penalty = -(oil_price - 150) * 0.1

    # Political crisis modifiers (arrests/impeachment affect elections)
    political_crisis_penalty = 0.0
    arrests_by_incumbent = sum(
        1 for e in inp.events_log
        if e.get("type") == "arrest" and e.get("country") == inp.country_id
    )
    political_crisis_penalty -= arrests_by_incumbent * 5.0  # -5 per arrest

    impeachment_events = sum(
        1 for e in inp.events_log
        if e.get("type") == "impeachment" and e.get("country") == inp.country_id
    )
    political_crisis_penalty -= impeachment_events * 10.0  # -10 per impeachment

    # Foreign policy SUCCESS bonuses
    foreign_policy_bonus = 0.0
    for e in inp.events_log:
        if e.get("type") in ("ceasefire", "agreement"):
            if inp.country_id in e.get("signatories", []):
                foreign_policy_bonus += 7.0  # peace deal signed
        if e.get("type") == "territory_capture" and e.get("country") == inp.country_id:
            foreign_policy_bonus += 5.0  # territorial gain

    ai_score = clamp(
        50.0 + econ_perf + stab_factor + war_penalty + crisis_penalty +
        oil_penalty + political_crisis_penalty + foreign_policy_bonus,
        0.0, 100.0)

    player_incumbent_pct = inp.incumbent_pct
    final_incumbent = 0.5 * ai_score + 0.5 * player_incumbent_pct
    incumbent_wins = final_incumbent >= 50.0

    result = ElectionResult(
        election_type=inp.election_type,
        country=inp.country_id,
        ai_score=round(ai_score, 2),
        player_score=player_incumbent_pct,
        final_incumbent_pct=round(final_incumbent, 2),
        incumbent_wins=incumbent_wins,
        crisis_penalty=crisis_penalty,
        oil_penalty=round(oil_penalty, 2),
    )

    # Columbia midterms
    if inp.election_type == "columbia_midterms":
        if not incumbent_wins:
            result.parliament_change = "opposition_majority"
            result.note = ("Midterms: Opposition wins. Parliament now 3-2 "
                           "opposition (Tribune + Challenger + NPC Seat 5).")
        else:
            result.parliament_change = "status_quo"
            result.note = "Midterms: President's camp retains majority."

    # Ruthenia wartime election
    elif inp.election_type in ("ruthenia_wartime", "ruthenia_wartime_runoff"):
        territory_factor = 0
        for w in inp.wars:
            if w.get("defender") == "ruthenia":
                territory_factor -= len(w.get("occupied_zones", [])) * 3
        ai_score_adjusted = clamp(
            ai_score + territory_factor - inp.war_tiredness * 2, 0, 100)
        final_incumbent = 0.5 * ai_score_adjusted + 0.5 * player_incumbent_pct
        incumbent_wins = final_incumbent >= 50.0
        result.ai_score = round(ai_score_adjusted, 2)
        result.final_incumbent_pct = round(final_incumbent, 2)
        result.incumbent_wins = incumbent_wins
        if not incumbent_wins:
            result.note = "Ruthenia election: Beacon loses. Bulwark becomes president."
        else:
            result.note = "Ruthenia election: Beacon survives."

    # Columbia presidential
    elif inp.election_type == "columbia_presidential":
        result.note = ("Presidential election. " +
                       ("Incumbent camp wins." if incumbent_wins
                        else "Opposition wins. New president."))

    return result


def check_revolution(country_id: str, stability: float,
                     political_support: float) -> Optional[RevolutionResult]:
    """When stability <= 2 AND support < 20%, mass protests erupt.

    An ELITE participant (non-HoS role) can choose to 'lead the protest'.
    Probabilistic outcome (dice) with risk for BOTH sides:
    - If protest succeeds: HoS removed, protest leader takes power
    - If protest fails: protest leader imprisoned/exiled
    - Base probability: 30% + (20 - support)% + (3 - stability) * 10%
    """
    if stability <= 2 and political_support < 20:
        severity = "severe" if stability <= 1 else "major"
        base_prob = 0.30 + (20 - political_support) / 100 + (3 - stability) * 0.10
        return RevolutionResult(
            event="mass_protests",
            country=country_id,
            severity=severity,
            stability=stability,
            support=political_support,
            elite_can_lead=True,
            base_success_probability=round(base_prob, 4),
            note=("An elite participant can choose to lead the protest. "
                  "Success = regime change. Failure = imprisonment/exile for the leader. "
                  "Risk for BOTH sides."),
        )
    return None


def check_health_events(country_id: str, round_num: int) -> Optional[HealthEventResult]:
    """Leaders 70+ face health risks after Round 2.

    Probability: ~3-5% per round (age-dependent, medical care matters).
    Effects: reduced capacity OR death.
    - Reduced capacity: fewer actions, can't attend meetings, lasts 1-2 rounds
    - Death: permanent removal, succession crisis

    Specific leaders:
    - Dealer (Columbia): age 80, medical 0.9 -> ~7.15%/round
    - Helmsman (Cathay): age 73, medical 0.7 -> ~3.9%/round
    - Pathfinder (Sarmatia): age 73, medical 0.6 -> ~4.2%/round
    """
    if round_num <= 2:
        return None  # allow players to establish themselves

    if country_id not in ELDERLY_LEADERS:
        return None

    leader = ELDERLY_LEADERS[country_id]

    # Base probability: 3% at 70, +1% per year over 70, reduced by medical quality
    base_prob = 0.03 + (leader["age"] - 70) * 0.01
    prob = base_prob * (1 - leader["medical_quality"] * 0.5)

    roll = random.random()
    if roll < prob:
        severity_roll = random.random()
        if severity_roll < 0.15:
            # Death (15% of health events)
            return HealthEventResult(
                event="leader_death",
                country=country_id,
                role=leader["role"],
                note=f"Leader of {country_id} has died. Succession crisis.",
                succession_required=True,
            )
        else:
            # Incapacitation (85% of health events)
            duration = random.choice([1, 1, 2])  # 1-2 rounds
            return HealthEventResult(
                event="leader_incapacitated",
                country=country_id,
                role=leader["role"],
                duration=duration,
                note=f"Leader of {country_id} incapacitated for {duration} round(s). Reduced capacity.",
                effects="Cannot attend meetings. Fewer actions. Deputy acts.",
            )

    return None


def update_war_tiredness(inp: WarTirednessInput) -> WarTirednessResult:
    """War tiredness: defenders +0.2/round, attackers +0.15/round.

    Society adaptation: after 3+ rounds at war, growth rate halves.
    Peacetime: 20% decay per round.
    """
    old_wt = inp.war_tiredness
    new_wt = old_wt

    if inp.at_war:
        if inp.is_defender:
            base_increase = 0.20
        elif inp.is_attacker:
            base_increase = 0.15
        else:
            base_increase = 0.10  # ally

        # Society adaptation: after 3+ rounds at war, tiredness growth halves
        if inp.war_duration >= 3:
            base_increase *= 0.5

        new_wt = min(old_wt + base_increase, 10.0)
    else:
        new_wt = max(old_wt * 0.80, 0)

    return WarTirednessResult(
        old_war_tiredness=old_wt,
        new_war_tiredness=round(new_wt, 4),
    )


def update_threshold_flags(stability: float) -> ThresholdFlagsResult:
    """Update protest_risk, coup_risk, regime_status based on stability thresholds."""
    protest_risk = stability < STABILITY_THRESHOLDS["protest_probable"]
    coup_risk = stability < STABILITY_THRESHOLDS["unstable"]

    if stability < STABILITY_THRESHOLDS["protest_automatic"]:
        regime_status = "crisis"
    elif stability < STABILITY_THRESHOLDS["unstable"]:
        regime_status = "unstable"
    else:
        regime_status = "stable"

    return ThresholdFlagsResult(
        protest_risk=protest_risk,
        coup_risk=coup_risk,
        regime_status=regime_status,
    )


def check_capitulation(economic_state: str, crisis_rounds: int) -> bool:
    """Country under sustained blockade + economic crisis may capitulate.

    Returns True when economic_state == 'crisis' and crisis_rounds >= 3,
    flagging for AI agent to consider capitulation.
    """
    return economic_state == "crisis" and crisis_rounds >= 3


def resolve_coup(inp: CoupInput) -> CoupResult:
    """Coup attempt resolution.

    Two conspirators required: initiator + co-conspirator.
    Base 15%
    + active_protest: +25%
    + stability < 3: +15%
    + stability 3-4: +5%
    + support < 30%: +10%
    Success: initiator becomes HoS, old HoS arrested. Stability -2.
    Failure: both exposed. Stability -1.
    """
    if len(inp.plotters) < 2:
        return CoupResult(
            success=False,
            probability=0.0,
            initiator=inp.plotters[0] if inp.plotters else "",
            co_conspirator="",
            stability_change=0.0,
            note="Coup requires two conspirators (initiator + co-conspirator)",
        )

    stability = inp.stability
    support = inp.political_support

    # Base probability
    prob = 0.15

    # Active protest bonus
    if inp.protest_risk or inp.protest_active:
        prob += 0.25

    # Stability bonuses
    if stability < 3:
        prob += 0.15
    elif stability <= 4:
        prob += 0.05

    # Low support bonus
    if support < 30:
        prob += 0.10

    prob = clamp(prob, 0.0, 0.90)

    success = random.random() < prob

    initiator_id = inp.plotters[0]
    co_conspirator_id = inp.plotters[1]

    if success:
        stability_change = -2.0
        note = (
            f"Coup successful. {initiator_id} takes power. "
            f"Former leader arrested."
        )
    else:
        stability_change = -1.0
        note = (
            f"Coup failed. {initiator_id} and {co_conspirator_id} exposed. "
            "Ruler and world learn of the attempt."
        )

    return CoupResult(
        success=success,
        probability=round(prob, 3),
        initiator=initiator_id,
        co_conspirator=co_conspirator_id,
        stability_change=stability_change,
        note=note,
    )


def resolve_assassination(inp: AssassinationInput) -> AssassinationResult:
    """Assassination resolution.

    1 card per game per eligible role.
    Domestic: 60% base hit.
    International: 20% base + country-specific bonuses.
    No AI tech or intel chief modifiers. Raw probability.
    Hit = 50% kill, 50% survive (injured + martyr effect).
    International: higher chance of being revealed if failed.
    """
    # Base probability -- domestic vs international
    if inp.domestic:
        prob = 0.60
    else:
        prob = 0.20
        # Country-specific bonuses (international only)
        prob += ASSASSINATION_COUNTRY_BONUS.get(inp.country_id, 0.0)

    hit = random.random() < prob

    # Detection: international failures have higher reveal chance
    if inp.domestic:
        detected = random.random() < 0.50
    else:
        detected = random.random() < (0.70 if not hit else 0.40)

    target_survived: Optional[bool] = None
    martyr_effect = 0
    note = ""

    if hit:
        # 50/50 kill or survive
        if random.random() < 0.50:
            target_survived = False
            martyr_effect = 15
            note = f"Target killed. Martyr effect boosts support by {martyr_effect}."
        else:
            target_survived = True
            martyr_effect = 10
            note = (
                "Target survived -- injured. "
                f"Martyr effect boosts support by {martyr_effect}."
            )
    else:
        note = "Assassination attempt failed"

    return AssassinationResult(
        hit=hit,
        detected=detected,
        probability=round(prob, 3),
        target_survived=target_survived,
        martyr_effect=martyr_effect,
        note=note,
    )
