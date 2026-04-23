"""TTT BUILD — Military / Combat Engine
==========================================
Ported from: 2 SEED/D_ENGINES/live_action_engine.py
Sprint: 2 (Engines + Public Display Light)

Stateless pure-function engine. NO database calls. NO world-state mutation.
All functions receive typed inputs and return typed Pydantic result models.
The orchestrator is responsible for applying results to the world state.

Author: BACKEND agent (ported from ATLAS SEED code)
"""

from __future__ import annotations

import math
import random
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ===========================================================================
# CONSTANTS & PROBABILITY TABLES
# ===========================================================================

# --- Unit types ---
UNIT_TYPES: list[str] = [
    "ground", "naval", "tactical_air", "strategic_missile", "air_defense",
]

# --- Chokepoints ---
CHOKEPOINTS: dict[str, dict] = {
    "hormuz":           {"zone": "cp_gulf_gate", "oil_impact": 0.35, "trade_impact": 0.10},
    "malacca":          {"zone": "w(15,9)",      "trade_impact": 0.30, "oil_impact": 0.05},
    "taiwan_strait":    {"zone": "w(17,4)",      "tech_impact": 0.50, "trade_impact": 0.15},
    "suez":             {"zone": "w(10,7)",      "trade_impact": 0.15, "oil_impact": 0.05},
    "bosphorus":        {"zone": "w(10,3)",      "trade_impact": 0.08, "oil_impact": 0.0},
    "giuk":             {"zone": "w(6,1)",       "detection": True, "trade_impact": 0.02},
    "caribbean":        {"zone": "w(4,8)",       "trade_impact": 0.05, "oil_impact": 0.02},
    "south_china_sea":  {"zone": "w(16,7)",      "trade_impact": 0.20, "oil_impact": 0.03},
    "gulf_gate_ground": {"zone": "cp_gulf_gate", "oil_impact": 0.60, "ground_blockade": True},
}

# --- Formosa encirclement ---
# Full blockade requires naval presence in 3+ of these zones.
# 1 friendly ship in any of these zones = instant downgrade to partial.
FORMOSA_SURROUNDING_ZONES: list[str] = [
    "w(16,7)",  # South China Sea (west approach)
    "w(17,7)",  # Formosa Strait
    "w(18,7)",  # East China Sea (north approach)
    "w(17,8)",  # Pacific east approach
    "w(16,8)",  # South approach
    "w(18,8)",  # Northeast approach
]

# --- AI combat bonus (from SEED world_state.py) ---
AI_LEVEL_COMBAT_BONUS: dict[int, int] = {0: 0, 1: 0, 2: 0, 3: 0, 4: 1}

# --- Covert ops probability tables ---
COVERT_BASE_PROBABILITY: dict[str, float] = {
    "sabotage":          0.45,
    "propaganda":        0.55,
}

COVERT_DETECTION_BASE: dict[str, float] = {
    "sabotage":          0.40,
    "propaganda":        0.25,
}

COVERT_ATTRIBUTION_PROBABILITY: dict[str, float] = {
    "sabotage":          0.50,
    "propaganda":        0.20,
}

# Countries with enhanced covert capabilities
INTELLIGENCE_POWERS: set[str] = {"columbia", "cathay", "levantia", "albion", "sarmatia"}

MAX_COVERT_OPS_PER_ROUND: dict[str, int] = {
    "default": 2,
    "intelligence_power": 3,
}

# Covert-op card field mapping (role field name per op type)
COVERT_CARD_FIELD_MAP: dict[str, str] = {
    "sabotage":          "sabotage_cards",
    "propaganda":        "disinfo_cards",
}

# --- Amphibious assault ---
AMPHIBIOUS_RATIO_DEFAULT: int = 3   # 3:1 needed
AMPHIBIOUS_RATIO_FORMOSA: int = 3   # 3:1 for Formosa

# --- Naval bombardment ---
NAVAL_BOMBARDMENT_HIT_PROB: float = 0.10

# --- Air strike ---
AIR_STRIKE_HIT_PROB: float = 0.15
AIRFIELD_VULNERABILITY_PROB: float = 0.20

# --- Assassination country-specific bonuses (international only) ---
ASSASSINATION_COUNTRY_BONUS: dict[str, float] = {
    "levantia": 0.30,  # total 50% (20% base + 30%)
    "sarmatia": 0.10,  # total 30% (20% base + 10%)
}

# --- Production tier tables (from SEED world_state.py) ---
PRODUCTION_TIER_COST: dict[str, float] = {
    "normal": 1.0,
    "accelerated": 2.0,
    "maximum": 4.0,
}
PRODUCTION_TIER_OUTPUT: dict[str, float] = {
    "normal": 1.0,
    "accelerated": 2.0,
    "maximum": 3.0,
}

# --- Missile interception (LEGACY v1 — conventional missiles only) ---
# Nuclear interception uses nuclear_chain.py constants:
#   TARGET_AD_INTERCEPT_PROB = 0.50 (target's own AD)
#   T3_INTERCEPT_PROB_PER_AD = 0.25 (other T3+ countries)
MISSILE_INTERCEPT_PROB: float = 0.30  # conventional missile AD interception (legacy v1)
MISSILE_AD_MAX_ATTEMPTS: int = 5  # max intercept attempts per missile


# ===========================================================================
# ENUMS
# ===========================================================================

class WarheadType(str, Enum):
    """Binary warhead classification (Marat 2026-04-06 — simplified).

    Damage depends on warhead + attack-type-tier (see StrategicAttackTier).
    Legacy NUCLEAR_L1 / NUCLEAR_L2 removed — damage profile is now
    derived from the attack tier + salvo context.
    """
    CONVENTIONAL = "conventional"
    NUCLEAR = "nuclear"


class StrategicAttackTier(str, Enum):
    """Launcher's strategic-attack capability (derived from country nuclear_level).

    * T1_MIDRANGE — ≤3 hex range, single missile, AD-in-zone halves hit
    * T2_STRATEGIC_SINGLE — global range, single missile, intercepted by T3+
    * T3_STRATEGIC_SALVO — global range, 3+ missiles, intercepted by T3+
    """
    T1_MIDRANGE = "t1_midrange"
    T2_STRATEGIC_SINGLE = "t2_strategic_single"
    T3_STRATEGIC_SALVO = "t3_strategic_salvo"


class BlockadeLevel(str, Enum):
    FULL = "full"
    PARTIAL = "partial"


class CovertOpType(str, Enum):
    SABOTAGE = "sabotage"
    PROPAGANDA = "propaganda"


class NuclearTestType(str, Enum):
    UNDERGROUND = "underground"
    OVERGROUND = "overground"


# ===========================================================================
# INPUT MODELS
# ===========================================================================

class CountryMilitary(BaseModel):
    """Snapshot of a single country's military state (read-only input)."""
    country_id: str
    ground: int = 0
    naval: int = 0
    tactical_air: int = 0
    strategic_missile: int = 0
    air_defense: int = 0
    ai_level: int = 0
    ai_l4_bonus: bool = False
    stability: float = 5.0
    nuclear_level: int = 0
    nuclear_tested: bool = False
    mobilization_pool: int = 0
    # Production
    prod_cost_ground: float = 3.0
    prod_cost_naval: float = 5.0
    prod_cost_tactical: float = 4.0
    prod_cap_ground: int = 2
    prod_cap_naval: int = 1
    prod_cap_tactical: int = 1
    strategic_missile_growth: int = 0
    maintenance_cost_per_unit: float = 0.3
    treasury: float = 0.0
    gdp: float = 0.0
    political_support: float = 50.0


class ZoneInfo(BaseModel):
    """Snapshot of a zone (read-only input)."""
    zone_id: str
    zone_type: str = "land_home"  # land_home | land_contested | sea | chokepoint | chokepoint_sea
    owner: str = "none"
    die_hard: bool = False
    forces: dict[str, dict[str, int]] = Field(default_factory=dict)
    # forces: {country_id: {unit_type: count}}


class AdjacencyInfo(BaseModel):
    """Connection between two zones."""
    zone_id: str
    connection_type: str = "land_land"  # land_land | land_sea | sea_sea


class RoleInfo(BaseModel):
    """Snapshot of a role for covert-ops / assassination / coup checks."""
    role_id: str
    country_id: str
    character_name: str = ""
    is_head_of_state: bool = False
    is_military_chief: bool = False
    status: str = "active"
    intelligence_pool: int = 0
    sabotage_cards: int = 0
    disinfo_cards: int = 0
    assassination_cards: int = 0


class AttackInput(BaseModel):
    """Input for resolve_attack."""
    attacker_country: str
    defender_country: str
    zone_id: str
    units_committed: int
    origin_zone_id: Optional[str] = None
    attacker: CountryMilitary
    defender: CountryMilitary
    zone: ZoneInfo
    origin_zone: Optional[ZoneInfo] = None
    origin_adjacency: list[AdjacencyInfo] = Field(default_factory=list)


class NavalCombatInput(BaseModel):
    """Input for resolve_naval_combat."""
    attacker_country: str
    defender_country: str
    sea_zone_id: str
    attacker: CountryMilitary
    defender: CountryMilitary
    zone: ZoneInfo


class AirStrikeInput(BaseModel):
    """Input for resolve_air_strike."""
    country_id: str
    target_zone_id: str
    air_units_sent: Optional[int] = None
    attacker: CountryMilitary
    target_zone: ZoneInfo
    adjacent_zones: list[ZoneInfo] = Field(default_factory=list)


class MissileStrikeInput(BaseModel):
    """Input for resolve_missile_strike."""
    launcher_country: str
    target_zone_id: str
    warhead_type: WarheadType = WarheadType.CONVENTIONAL
    launcher: CountryMilitary
    target_zone: ZoneInfo
    all_countries: list[CountryMilitary] = Field(default_factory=list)


class BlockadeInput(BaseModel):
    """Input for resolve_blockade."""
    country_id: str
    zone_id: str
    level: BlockadeLevel = BlockadeLevel.FULL
    zone: ZoneInfo
    # For Formosa: adjacent sea zones with forces
    adjacent_sea_zones: list[ZoneInfo] = Field(default_factory=list)
    formosa_owner: str = "formosa"


class NavalBombardmentInput(BaseModel):
    """Input for resolve_naval_bombardment."""
    country_id: str
    sea_zone_id: str
    target_land_zone_id: str
    naval_units_in_zone: int
    target_zone: ZoneInfo
    is_adjacent: bool = True


class CovertOpInput(BaseModel):
    """Input for resolve_covert_op."""
    country_id: str
    op_type: CovertOpType
    target_country_code: str
    role_id: Optional[str] = None
    role: Optional[RoleInfo] = None
    target_country: CountryMilitary
    ai_level: int = 0
    prev_ops_against_target: int = 0
    covert_ops_this_round: int = 0


class AssassinationInput(BaseModel):
    """Input for resolve_assassination."""
    country_id: str
    target_role_id: str
    domestic: bool = False
    target_role: RoleInfo


class CoupInput(BaseModel):
    """Input for resolve_coup."""
    country_id: str
    plotter_role_ids: list[str]
    plotter_roles: list[RoleInfo]
    stability: float = 5.0
    political_support: float = 50.0
    protest_active: bool = False
    head_of_state_role_id: Optional[str] = None


class ProductionOrderInput(BaseModel):
    """Input for validate_production_order."""
    country_id: str
    unit_type: str  # ground | naval | tactical_air
    quantity: int
    tier: str = "normal"  # normal | accelerated | maximum
    country: CountryMilitary


class MartialLawInput(BaseModel):
    """Input for resolve_martial_law (martial-law conscription pool).

    Renamed 2026-04-11 from MobilizationInput to eliminate the naming
    collision with the deprecated round_engine/movement.py:resolve_mobilization
    (deploy-from-reserve mechanic). Per CONTRACT_MOVEMENT v1.0 closing step.
    """
    country_id: str
    units_to_mobilize: int
    country: CountryMilitary


class DeploymentValidationInput(BaseModel):
    """Input for validate_deployment."""
    country_id: str
    unit_type: str
    count: int
    target_zone_id: str
    origin_zone_id: Optional[str] = None
    country: CountryMilitary
    target_zone: ZoneInfo
    origin_zone: Optional[ZoneInfo] = None
    origin_adjacency: list[AdjacencyInfo] = Field(default_factory=list)
    target_adjacency: list[AdjacencyInfo] = Field(default_factory=list)


class NuclearTestInput(BaseModel):
    """Input for resolve_nuclear_test."""
    country_id: str
    test_type: NuclearTestType = NuclearTestType.UNDERGROUND
    country: CountryMilitary
    all_countries: list[CountryMilitary] = Field(default_factory=list)


class AirfieldVulnerabilityInput(BaseModel):
    """Input for resolve_airfield_vulnerability."""
    target_zone_id: str
    attacking_country_id: str
    target_zone: ZoneInfo


# ===========================================================================
# RESULT MODELS
# ===========================================================================

class CombatModifiers(BaseModel):
    """Breakdown of all modifiers applied during ground combat."""
    attacker_ai_l4: int = 0
    attacker_morale: int = 0
    amphibious_penalty: int = 0
    defender_ai_l4: int = 0
    defender_morale: int = 0
    die_hard: int = 0
    air_support_raw: int = 0
    positional_bonus: int = 0   # max(die_hard, air_support) -- they DON'T stack
    attacker_total: int = 0
    defender_total: int = 0


class CombatResult(BaseModel):
    """Result of ground combat (resolve_attack)."""
    type: str = "attack"
    attacker: str
    defender: str
    zone: str
    origin_zone: Optional[str] = None
    attacker_units_committed: int
    success: bool = False
    zone_captured: bool = False
    attacker_losses: int = 0
    defender_losses: int = 0
    attacker_remaining: int = 0
    defender_remaining: int = 0
    is_amphibious: bool = False
    modifiers: Optional[CombatModifiers] = None
    war_tiredness_attacker: float = 0.5
    war_tiredness_defender: float = 0.5
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# M2 — Ground Combat (CONTRACT_GROUND_COMBAT v1.0) — canonical pure dice fn
# ---------------------------------------------------------------------------


class GroundCombatModifier(BaseModel):
    """A single modifier applied to a ground combat exchange."""
    side: str  # "attacker" | "defender"
    value: int  # +1, -1, etc.
    reason: str  # human-readable explanation for the visualization


class GroundCombatResult(BaseModel):
    """M2 — pure RISK ground combat result. CONTRACT_GROUND_COMBAT v1.0 §5."""
    combat_type: str = "ground"
    attacker_rolls: list[list[int]] = Field(default_factory=list)
    defender_rolls: list[list[int]] = Field(default_factory=list)
    attacker_losses: list[str] = Field(default_factory=list)
    defender_losses: list[str] = Field(default_factory=list)
    modifier_breakdown: list[GroundCombatModifier] = Field(default_factory=list)
    summed_attacker_bonus: int = 0
    summed_defender_bonus: int = 0
    exchanges: int = 0
    rolls_source: str = "random"
    narrative: str = ""
    success: bool = False  # True iff attacker won


def resolve_ground_combat(
    attackers: list[dict],
    defenders: list[dict],
    modifiers: list[dict] | None = None,
    precomputed_rolls: dict | None = None,
    max_exchanges: int = 50,
) -> GroundCombatResult:
    """Resolve a single ground engagement — RISK iterative dice.

    Per CONTRACT_GROUND_COMBAT v1.0 §5:
      - Attacker rolls min(3, len(attackers_alive)) dice each exchange
      - Defender rolls min(2, len(defenders_alive)) dice each exchange
      - Sort each list descending, apply highest-die modifiers (cap at 6)
      - Re-sort, compare highest-vs-highest then second-vs-second
      - Ties go to defender
      - Loop until one side has zero units
      - Per-exchange dice stored as list-of-lists (NOT flattened) for replay

    ``modifiers`` is a list of ``{side, value, reason}`` dicts. Sums are
    applied to the highest die per side per exchange. The full list is
    echoed in the result for the visualization.

    ``precomputed_rolls`` (optional) lets a moderator (or unit test) supply
    deterministic dice instead of random. Shape:
        {"attacker": [[5,3,2], [6,4]], "defender": [[6,2], [4,1]]}
    Each inner list is one exchange. If the precomputed list runs out
    before combat ends, remaining exchanges fall back to random.

    Returns ``GroundCombatResult`` with full per-exchange dice + modifier
    breakdown for the Observatory combat panel.
    """
    import random as _random

    modifiers = modifiers or []
    breakdown = [GroundCombatModifier(**m) for m in modifiers]
    sum_atk = sum(m.value for m in breakdown if m.side == "attacker")
    sum_def = sum(m.value for m in breakdown if m.side == "defender")

    if not attackers or not defenders:
        return GroundCombatResult(
            modifier_breakdown=breakdown,
            summed_attacker_bonus=sum_atk,
            summed_defender_bonus=sum_def,
            narrative="No combat: one side has zero units.",
            success=False,
        )

    pre_atk = (precomputed_rolls or {}).get("attacker") or []
    pre_def = (precomputed_rolls or {}).get("defender") or []
    rolls_source = "moderator" if (pre_atk or pre_def) else "random"

    attackers_alive = list(attackers)
    defenders_alive = list(defenders)
    attacker_losses: list[str] = []
    defender_losses: list[str] = []
    all_a_rolls: list[list[int]] = []
    all_d_rolls: list[list[int]] = []
    exchanges = 0

    while attackers_alive and defenders_alive:
        exchanges += 1
        a_n = min(len(attackers_alive), 3)
        d_n = min(len(defenders_alive), 2)

        # Source dice from precomputed if available, else random
        if exchanges - 1 < len(pre_atk) and pre_atk[exchanges - 1] is not None:
            a_rolls = list(pre_atk[exchanges - 1])[:a_n]
            # If precomputed is short, top up with random
            while len(a_rolls) < a_n:
                a_rolls.append(_random.randint(1, 6))
        else:
            a_rolls = [_random.randint(1, 6) for _ in range(a_n)]

        if exchanges - 1 < len(pre_def) and pre_def[exchanges - 1] is not None:
            d_rolls = list(pre_def[exchanges - 1])[:d_n]
            while len(d_rolls) < d_n:
                d_rolls.append(_random.randint(1, 6))
        else:
            d_rolls = [_random.randint(1, 6) for _ in range(d_n)]

        a_rolls.sort(reverse=True)
        d_rolls.sort(reverse=True)
        all_a_rolls.append(list(a_rolls))
        all_d_rolls.append(list(d_rolls))

        # Apply modifiers to the highest die of each side (cap at 6, floor at 1)
        a_mod = list(a_rolls)
        d_mod = list(d_rolls)
        if a_mod and sum_atk:
            a_mod[0] = max(1, min(6, a_mod[0] + sum_atk))
            a_mod.sort(reverse=True)
        if d_mod and sum_def:
            d_mod[0] = max(1, min(6, d_mod[0] + sum_def))
            d_mod.sort(reverse=True)

        pairs = min(len(a_mod), len(d_mod))
        for i in range(pairs):
            if a_mod[i] > d_mod[i]:
                # defender loses one unit (last one out for stable removal)
                lost = defenders_alive.pop()
                defender_losses.append(lost["unit_code"])
            else:
                # attacker loses (defender wins ties)
                lost = attackers_alive.pop()
                attacker_losses.append(lost["unit_code"])

        if exchanges >= max_exchanges:
            break

    success = (len(defenders_alive) == 0)
    narrative = (
        f"Ground combat ({exchanges} exchanges, "
        f"atk_bonus={sum_atk:+d}, def_bonus={sum_def:+d}): "
        f"attackers -{len(attacker_losses)}, defenders -{len(defender_losses)}. "
        f"{'ATTACKER WINS' if success else 'DEFENDER HOLDS'}"
    )

    return GroundCombatResult(
        attacker_rolls=all_a_rolls,
        defender_rolls=all_d_rolls,
        attacker_losses=attacker_losses,
        defender_losses=defender_losses,
        modifier_breakdown=breakdown,
        summed_attacker_bonus=sum_atk,
        summed_defender_bonus=sum_def,
        exchanges=exchanges,
        rolls_source=rolls_source,
        narrative=narrative,
        success=success,
    )


# ---------------------------------------------------------------------------
# M3 — Air Strikes (CONTRACT_AIR_STRIKES v1.0) — canonical pure function
# ---------------------------------------------------------------------------


class AirStrikeShot(BaseModel):
    """One per-attacker outcome in an air strike batch."""
    attacker_code: str
    hit_probability: float
    hit_roll: float
    hit: bool
    downed_probability: float
    downed_roll: float
    downed: bool
    target_destroyed: Optional[str] = None


class AirStrikeResult(BaseModel):
    """M3 — air strike result. CONTRACT_AIR_STRIKES v1.0 §4."""
    combat_type: str = "air_strike"
    shots: list[AirStrikeShot] = Field(default_factory=list)
    attacker_losses: list[str] = Field(default_factory=list)
    defender_losses: list[str] = Field(default_factory=list)
    modifier_breakdown: list["GroundCombatModifier"] = Field(default_factory=list)
    rolls_source: str = "random"
    narrative: str = ""
    success: bool = False  # True iff at least one hit


def resolve_air_strike(
    attackers: list[dict],
    defenders: list[dict],
    ad_units: Optional[list[dict]] = None,
    air_superiority_count: int = 0,
    precomputed_rolls: Optional[dict] = None,
) -> AirStrikeResult:
    """Resolve a tactical air strike batch — CONTRACT_AIR_STRIKES v1.0 §4.

    Each attacker rolls independently:
      - hit_prob = clamp([3%, 20%], 0.12 + 0.02 * air_sup) * (0.5 if AD else 1)
      - downed_prob = 0.15 if AD present else 0
    """
    import random as _random

    ad_units = ad_units or []
    ad_present = any((u.get("status") or "").lower() != "destroyed" for u in ad_units)

    # Per CARD_FORMULAS D.2: 12% base, 6% with AD (halved). No air superiority
    # bonus. No clamp. All probabilities Template-customizable.
    # NOTE: air_superiority_count parameter is KEPT in the signature for future
    # Template customization but has zero effect per canonical CARD.
    base_hit = 0.12
    hit_prob = base_hit * 0.5 if ad_present else base_hit
    downed_prob = 0.15 if ad_present else 0.0

    # Modifier breakdown for the visualization (informational, not arithmetic)
    breakdown: list[GroundCombatModifier] = []
    if ad_present:
        breakdown.append(GroundCombatModifier(
            side="defender", value=-50,
            reason=f"AD coverage halves hit probability ({len(ad_units)} AD units)",
        ))
        breakdown.append(GroundCombatModifier(
            side="defender", value=15,
            reason="AD downs attacker (15% per shot if AD covers)",
        ))

    pre_shots = (precomputed_rolls or {}).get("shots") or []
    rolls_source = "moderator" if pre_shots else "random"

    shots: list[AirStrikeShot] = []
    attacker_losses: list[str] = []
    defender_losses: list[str] = []
    living_defenders = list(defenders)

    for i, au in enumerate(attackers):
        # hit roll
        if i < len(pre_shots) and "hit_roll" in (pre_shots[i] or {}):
            hit_roll = float(pre_shots[i]["hit_roll"])
        else:
            hit_roll = _random.random()
        hit = hit_roll < hit_prob

        target_code: Optional[str] = None
        if hit and living_defenders:
            tgt = next(
                (d for d in living_defenders
                 if (d.get("unit_type") or "").lower() != "air_defense"),
                living_defenders[0],
            )
            target_code = tgt["unit_code"]
            defender_losses.append(target_code)
            living_defenders = [d for d in living_defenders if d["unit_code"] != target_code]

        # downed roll
        if i < len(pre_shots) and "downed_roll" in (pre_shots[i] or {}):
            downed_roll = float(pre_shots[i]["downed_roll"])
        else:
            downed_roll = _random.random() if ad_present else 1.0
        downed = ad_present and downed_roll < downed_prob

        if downed:
            attacker_losses.append(au["unit_code"])

        shots.append(AirStrikeShot(
            attacker_code=au["unit_code"],
            hit_probability=round(hit_prob, 4),
            hit_roll=round(hit_roll, 4),
            hit=hit,
            downed_probability=round(downed_prob, 4),
            downed_roll=round(downed_roll, 4),
            downed=downed,
            target_destroyed=target_code,
        ))

    n_hit = sum(1 for s in shots if s.hit)
    n_down = len(attacker_losses)
    narrative = (
        f"Air strike: {len(shots)} sorties, {n_hit} hits, "
        f"{n_down} attacker losses to AD"
        + (f" (AD covers target zone, hit_prob={hit_prob:.2f})" if ad_present
           else f" (no AD, hit_prob={hit_prob:.2f})")
    )

    return AirStrikeResult(
        shots=shots,
        attacker_losses=attacker_losses,
        defender_losses=defender_losses,
        modifier_breakdown=breakdown,
        rolls_source=rolls_source,
        narrative=narrative,
        success=(n_hit > 0),
    )


# ---------------------------------------------------------------------------
# M4 — Naval Combat (CONTRACT_NAVAL_COMBAT v1.0) — canonical 1v1 dice
# ---------------------------------------------------------------------------


class NavalCombatResultM4(BaseModel):
    """M4 — 1v1 naval combat result. CONTRACT_NAVAL_COMBAT v1.0 §4."""
    combat_type: str = "naval"
    attacker_code: str
    defender_code: str
    attacker_roll: int
    defender_roll: int
    attacker_modified: int
    defender_modified: int
    winner: str  # "attacker" | "defender"
    destroyed_unit: str
    modifier_breakdown: list[GroundCombatModifier] = Field(default_factory=list)
    rolls_source: str = "random"
    narrative: str = ""


def resolve_naval_combat(
    attacker: dict,
    defender: dict,
    modifiers: list[dict] | None = None,
    precomputed_rolls: dict | None = None,
) -> NavalCombatResultM4:
    """Resolve a 1v1 naval engagement — CONTRACT_NAVAL_COMBAT v1.0 §4.

    Each side rolls 1d6 + modifiers. Higher wins. Ties → defender.
    Loser destroyed.

    ``precomputed_rolls``: ``{"attacker": 5, "defender": 3}`` — single
    int per side. Default ``None`` = random.
    """
    import random as _random

    modifiers = modifiers or []
    breakdown = [GroundCombatModifier(**m) for m in modifiers]
    sum_atk = sum(m.value for m in breakdown if m.side == "attacker")
    sum_def = sum(m.value for m in breakdown if m.side == "defender")

    pre = precomputed_rolls or {}
    rolls_source = "moderator" if ("attacker" in pre or "defender" in pre) else "random"

    a_roll = pre.get("attacker") if isinstance(pre.get("attacker"), int) else _random.randint(1, 6)
    d_roll = pre.get("defender") if isinstance(pre.get("defender"), int) else _random.randint(1, 6)

    a_mod = max(1, min(6, a_roll + sum_atk))
    d_mod = max(1, min(6, d_roll + sum_def))

    # Higher wins. Ties → defender.
    if a_mod > d_mod:
        winner = "attacker"
        destroyed = defender["unit_code"]
    else:
        winner = "defender"
        destroyed = attacker["unit_code"]

    narrative = (
        f"Naval 1v1: {attacker['unit_code']} ({a_roll}"
        + (f"{sum_atk:+d}={a_mod}" if sum_atk else "")
        + f") vs {defender['unit_code']} ({d_roll}"
        + (f"{sum_def:+d}={d_mod}" if sum_def else "")
        + f") → {winner} wins, {destroyed} destroyed"
    )

    return NavalCombatResultM4(
        attacker_code=attacker["unit_code"],
        defender_code=defender["unit_code"],
        attacker_roll=a_roll,
        defender_roll=d_roll,
        attacker_modified=a_mod,
        defender_modified=d_mod,
        winner=winner,
        destroyed_unit=destroyed,
        modifier_breakdown=breakdown,
        rolls_source=rolls_source,
        narrative=narrative,
    )


class NavalCombatResult(BaseModel):
    """[LEGACY v1] Result of ship-vs-ship naval combat."""
    type: str = "naval_combat"
    attacker: str
    defender: str
    sea_zone: str
    attacker_ships_committed: int = 0
    attacker_losses: int = 0
    defender_losses: int = 0
    embarked_units_lost_attacker: dict[str, int] = Field(default_factory=dict)
    embarked_units_lost_defender: dict[str, int] = Field(default_factory=dict)
    success: bool = False  # attacker "wins" if they sank more
    error: Optional[str] = None


class AirStrikeResultLegacyV1(BaseModel):
    """[LEGACY v1, used by resolve_air_strike_legacy_v1] Country-level result.

    Renamed in M3 (2026-04-12) to free up `AirStrikeResult` for the
    canonical M3 unit-level shape.
    """
    type: str = "air_strike"
    country: str
    target_zone: str
    air_sent: int = 0
    intercepted_destroyed: int = 0
    strikes_landed: int = 0
    ground_units_destroyed: int = 0
    air_returned: int = 0
    error: Optional[str] = None


class AirfieldVulnerabilityResult(BaseModel):
    """Result of airfield vulnerability check."""
    type: str = "airfield_vulnerability"
    zone: str
    destroyed: int = 0
    # per-country breakdown
    losses_by_country: dict[str, int] = Field(default_factory=dict)


class MissileStrikeResult(BaseModel):
    """Result of strategic missile strike."""
    type: str = "missile_strike"
    launcher: str
    target_zone: str
    warhead_type: str
    success: bool = False
    intercepted: bool = False
    # Conventional
    ground_destroyed: int = 0
    # Nuclear L1
    nuclear_level: Optional[int] = None
    affected_countries: list[str] = Field(default_factory=list)
    treasury_losses: dict[str, float] = Field(default_factory=dict)
    # Nuclear L2
    gdp_multiplier: Optional[float] = None  # 0.70 for L2
    military_losses_by_country: dict[str, dict[str, int]] = Field(default_factory=dict)
    leaders_killed: list[str] = Field(default_factory=list)
    leader_survival_rolls: dict[str, bool] = Field(default_factory=dict)
    global_stability_shock: bool = False
    global_stability_loss: float = 0.0
    nuclear_used: bool = False
    note: Optional[str] = None
    error: Optional[str] = None


class BlockadeResult(BaseModel):
    """Result of blockade establishment."""
    type: str = "blockade"
    country: str
    zone: str
    level: str  # full | partial
    success: bool = False
    blockade_type: Optional[str] = None  # ground | naval
    chokepoint: Optional[str] = None
    auto_downgraded: bool = False
    downgrade_reason: Optional[str] = None
    note: Optional[str] = None
    error: Optional[str] = None


class NavalBombardmentResult(BaseModel):
    """Result of naval bombardment."""
    type: str = "naval_bombardment"
    country: str
    sea_zone: str
    target_zone: str
    units_destroyed: int = 0
    error: Optional[str] = None


class IntelligenceReport(BaseModel):
    """Intelligence report — accuracy varies but format is constant."""
    gdp_estimate: float = 0.0
    treasury_estimate: float = 0.0
    stability_estimate: float = 0.0
    support_estimate: float = 0.0
    military_ground_estimate: int = 0
    military_naval_estimate: int = 0
    military_air_estimate: int = 0
    nuclear_level: int = 0
    nuclear_progress_estimate: float = 0.0
    ai_level: int = 0
    mobilization_pool_estimate: int = 0


class CovertOpResult(BaseModel):
    """Result of covert operation."""
    type: str = "covert_op"
    op_type: str
    country: str
    target: str
    role_id: Optional[str] = None
    success: bool = False
    detected: bool = False
    attributed: bool = False
    success_probability: float = 0.0
    detection_probability: float = 0.0
    # Sabotage
    gdp_damage: Optional[float] = None
    # Propaganda
    stability_impact: Optional[float] = None
    support_impact: Optional[float] = None
    # Card consumed
    card_consumed: bool = False
    card_field: Optional[str] = None
    error: Optional[str] = None


class AssassinationResult(BaseModel):
    """Result of assassination attempt."""
    type: str = "assassination"
    country: str
    target_role: str
    domestic: bool = False
    hit: bool = False
    target_survived: Optional[bool] = None
    detected: bool = False
    probability: float = 0.0
    success: bool = False
    martyr_effect: int = 0  # political support boost to target country
    new_target_status: Optional[str] = None  # dead | active (survived)
    note: Optional[str] = None
    error: Optional[str] = None


class CoupResult(BaseModel):
    """Result of coup attempt."""
    type: str = "coup"
    country: str
    plotters: list[str] = Field(default_factory=list)
    success: bool = False
    probability: float = 0.0
    new_leader: Optional[str] = None
    old_leader_status: Optional[str] = None  # arrested (success) | None (fail)
    plotter_status: Optional[str] = None     # exposed (failure) | None (success)
    stability_change: float = 0.0
    note: Optional[str] = None
    error: Optional[str] = None


class ProductionResult(BaseModel):
    """Result of production order validation and cost calculation."""
    type: str = "production"
    country_id: str
    unit_type: str
    quantity: int
    tier: str
    valid: bool = False
    total_cost: float = 0.0
    units_produced: int = 0
    error: Optional[str] = None


class MartialLawResult(BaseModel):
    """Result of resolve_martial_law (renamed 2026-04-11 from MobilizationResult)."""
    type: str = "martial_law"
    country_id: str
    units_mobilized: int = 0
    pool_remaining: int = 0
    error: Optional[str] = None


class DeploymentValidationResult(BaseModel):
    """Result of deployment validation."""
    type: str = "deployment_validation"
    valid: bool = False
    country_id: str
    unit_type: str
    count: int
    target_zone_id: str
    error: Optional[str] = None


class NuclearTestResult(BaseModel):
    """Result of nuclear test."""
    type: str = "nuclear_test"
    country_id: str
    test_type: str
    success: bool = False
    global_stability_loss: float = 0.0
    tester_stability_loss: float = 0.0
    tester_support_boost: float = 0.0
    note: Optional[str] = None
    error: Optional[str] = None


# ===========================================================================
# HELPER: clamp (from SEED world_state.py)
# ===========================================================================

def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value between min_val and max_val."""
    return max(min_val, min(max_val, value))


# ===========================================================================
# 1. GROUND COMBAT — RISK dice + modifiers
# ===========================================================================

def _build_combat_modifiers(
    attacker: CountryMilitary,
    defender: CountryMilitary,
    zone: ZoneInfo,
    is_amphibious: bool,
) -> CombatModifiers:
    """Simplified integer-only modifiers (ACTION REVIEW 2026-03-30).

    Modifiers kept:
    - AI L4: +1 if country has ai_level==4 AND ai_l4_bonus flag set
    - Low morale: -1 if stability <= 3
    - Die Hard: +1 defender if zone has die_hard flag
    - Amphibious: -1 attacker
    - Air support: +1 defender if ANY tactical_air > 0 in zone (binary)

    Die Hard and air support DON'T stack — max positional bonus = +1.

    REMOVED (per ACTION REVIEW 2026-03-30): naval support, militia modifier,
    home territory, capital, scaled air support, proportional morale.
    """
    # AI L4 bonus: +1 if ai_level==4 and random flag was set when L4 reached
    att_ai_bonus = 1 if (attacker.ai_level == 4 and attacker.ai_l4_bonus) else 0
    def_ai_bonus = 1 if (defender.ai_level == 4 and defender.ai_l4_bonus) else 0

    # Low morale: -1 if stability <= 3
    att_morale = -1 if attacker.stability <= 3 else 0
    def_morale = -1 if defender.stability <= 3 else 0

    # Die Hard: +1 defender if zone has die_hard flag
    die_hard = 1 if zone.die_hard else 0

    # Amphibious: -1 attacker
    amphibious_penalty = -1 if is_amphibious else 0

    # Air support: +1 defender if any defender tactical_air > 0 in zone (binary)
    def_air_in_zone = zone.forces.get(defender.country_id, {}).get("tactical_air", 0)
    air_support = 1 if def_air_in_zone > 0 else 0

    # Die Hard and air support DON'T stack — max positional bonus = +1
    positional_bonus = max(die_hard, air_support)

    att_total = att_ai_bonus + att_morale + amphibious_penalty
    def_total = def_ai_bonus + def_morale + positional_bonus

    return CombatModifiers(
        attacker_ai_l4=att_ai_bonus,
        attacker_morale=att_morale,
        amphibious_penalty=amphibious_penalty,
        defender_ai_l4=def_ai_bonus,
        defender_morale=def_morale,
        die_hard=die_hard,
        air_support_raw=air_support,
        positional_bonus=positional_bonus,
        attacker_total=att_total,
        defender_total=def_total,
    )


def _is_amphibious_attack(
    origin_zone: Optional[ZoneInfo],
    target_zone: ZoneInfo,
    origin_adjacency: list[AdjacencyInfo],
) -> bool:
    """Determine if an attack is amphibious (sea-to-land)."""
    if origin_zone is None:
        return False
    # If origin is sea type and target is not sea
    if origin_zone.zone_type.startswith("sea") and not target_zone.zone_type.startswith("sea"):
        return True
    # Check if connection type is land_sea and origin is sea
    for adj in origin_adjacency:
        if adj.zone_id == target_zone.zone_id and adj.connection_type == "land_sea":
            if origin_zone.zone_type.startswith("sea"):
                return True
    return False


def resolve_attack(inp: AttackInput) -> CombatResult:
    """RISK combat with simplified integer modifiers (ACTION REVIEW 2026-03-30).

    Rules:
    - Each unit pair rolls 1d6 + modifiers
    - Attacker needs >= defender + 1 to win (ties = defender holds)
    - Simplified modifiers: AI L4 (+1 random), low morale (-1),
      die hard (+1 def), amphibious (-1 att), air support (+1 def binary)
    - Die Hard and air support DON'T stack, max positional +1

    Returns a CombatResult. The orchestrator applies losses and zone control
    changes to the world state.
    """
    # Validate zone exists (caller should have checked, but be safe)
    zone = inp.zone
    attacker = inp.attacker
    defender = inp.defender
    units = inp.units_committed

    # Get defender ground forces in zone
    def_forces = zone.forces.get(inp.defender_country, {})
    def_ground = def_forces.get("ground", 0)

    # Check for amphibious assault
    is_amphibious = _is_amphibious_attack(inp.origin_zone, zone, inp.origin_adjacency)

    # Uncontested capture
    if def_ground == 0:
        return CombatResult(
            attacker=inp.attacker_country,
            defender=inp.defender_country,
            zone=inp.zone_id,
            origin_zone=inp.origin_zone_id,
            attacker_units_committed=units,
            success=True,
            zone_captured=True,
            attacker_losses=0,
            defender_losses=0,
            attacker_remaining=units,
            defender_remaining=0,
            is_amphibious=is_amphibious,
        )

    # Build modifiers
    modifiers = _build_combat_modifiers(attacker, defender, zone, is_amphibious)

    # Execute RISK dice combat
    a_losses = 0
    d_losses = 0
    pairs = min(units, def_ground)

    for _ in range(pairs):
        a_roll = random.randint(1, 6) + modifiers.attacker_total
        d_roll = random.randint(1, 6) + modifiers.defender_total
        if a_roll >= d_roll + 1:  # attacker needs >= defender + 1
            d_losses += 1
        else:
            a_losses += 1  # defender wins ties and +0 draws

    att_remaining = units - a_losses
    def_remaining = def_ground - d_losses
    zone_captured = def_remaining <= 0 and att_remaining > 0

    return CombatResult(
        attacker=inp.attacker_country,
        defender=inp.defender_country,
        zone=inp.zone_id,
        origin_zone=inp.origin_zone_id,
        attacker_units_committed=units,
        success=True,
        zone_captured=zone_captured,
        attacker_losses=a_losses,
        defender_losses=d_losses,
        attacker_remaining=att_remaining,
        defender_remaining=max(def_remaining, 0),
        is_amphibious=is_amphibious,
        modifiers=modifiers,
        war_tiredness_attacker=0.5,
        war_tiredness_defender=0.5,
    )


# ===========================================================================
# 2. NAVAL COMBAT — ship vs ship RISK dice
# ===========================================================================

def resolve_naval_combat_legacy_v1(inp: NavalCombatInput) -> NavalCombatResult:
    """[LEGACY v1, unused after M4 2026-04-12] Country-level naval combat.

    Renamed in M4 to free up ``resolve_naval_combat`` for the canonical
    M4 1v1 unit-level function. No callers in production code.

    Original: Ship vs ship combat in a sea zone.
    Same RISK dice as ground: 1d6 per pair, attacker needs >= defender + 1.
    No terrain modifiers (open sea). Carrier air support applies (+1).
    Sunk ship = all embarked units (ground + air) also lost.

    Embarked unit loss formula (from SEED):
    - ground per ship = min(1, country_ground // max(ships_in_zone, 1))
    - air per ship = min(5, country_air // max(ships_in_zone, 1))
    """
    att_naval = inp.zone.forces.get(inp.attacker_country, {}).get("naval", 0)
    def_naval = inp.zone.forces.get(inp.defender_country, {}).get("naval", 0)

    if att_naval <= 0:
        return NavalCombatResult(
            attacker=inp.attacker_country,
            defender=inp.defender_country,
            sea_zone=inp.sea_zone_id,
            error=f"{inp.attacker_country} has no ships in {inp.sea_zone_id}",
        )
    if def_naval <= 0:
        return NavalCombatResult(
            attacker=inp.attacker_country,
            defender=inp.defender_country,
            sea_zone=inp.sea_zone_id,
            error=f"{inp.defender_country} has no ships in {inp.sea_zone_id}",
        )

    att_c = inp.attacker
    def_c = inp.defender

    # AI L4 bonus (SEED uses ai_l4_bonus flag, not AI_LEVEL_COMBAT_BONUS table)
    att_mod = 1 if att_c.ai_l4_bonus else 0
    def_mod = 1 if def_c.ai_l4_bonus else 0

    # Low morale: -1 if stability <= 3
    if att_c.stability <= 3:
        att_mod -= 1
    if def_c.stability <= 3:
        def_mod -= 1

    # Carrier air support: +1 if any tactical_air > 0 (country total in SEED)
    if att_c.tactical_air > 0:
        att_mod += 1
    if def_c.tactical_air > 0:
        def_mod += 1

    # RISK dice combat
    a_losses = 0
    d_losses = 0
    pairs = min(att_naval, def_naval)

    for _ in range(pairs):
        a_roll = random.randint(1, 6) + att_mod
        d_roll = random.randint(1, 6) + def_mod
        if a_roll >= d_roll + 1:
            d_losses += 1
        else:
            a_losses += 1

    # Compute embarked unit losses (SEED formula exactly)
    att_embarked_lost: dict[str, int] = {"ground": 0, "tactical_air": 0}
    def_embarked_lost: dict[str, int] = {"ground": 0, "tactical_air": 0}

    if a_losses > 0:
        ground_per_ship = min(1, att_c.ground // max(att_naval, 1))
        air_per_ship = min(5, att_c.tactical_air // max(att_naval, 1))
        att_ground_lost = min(a_losses * ground_per_ship, att_c.ground)
        att_air_lost = min(a_losses * air_per_ship, att_c.tactical_air)
        att_embarked_lost = {"ground": att_ground_lost, "tactical_air": att_air_lost}

    if d_losses > 0:
        ground_per_ship = min(1, def_c.ground // max(def_naval, 1))
        air_per_ship = min(5, def_c.tactical_air // max(def_naval, 1))
        def_ground_lost = min(d_losses * ground_per_ship, def_c.ground)
        def_air_lost = min(d_losses * air_per_ship, def_c.tactical_air)
        def_embarked_lost = {"ground": def_ground_lost, "tactical_air": def_air_lost}

    return NavalCombatResult(
        attacker=inp.attacker_country,
        defender=inp.defender_country,
        sea_zone=inp.sea_zone_id,
        attacker_ships_committed=att_naval,
        attacker_losses=a_losses,
        defender_losses=d_losses,
        embarked_units_lost_attacker=att_embarked_lost,
        embarked_units_lost_defender=def_embarked_lost,
        success=d_losses > a_losses,
    )


# ===========================================================================
# 3. AIR COMBAT — AD interception, carrier ops, airfield vulnerability
# ===========================================================================

def resolve_air_strike_legacy_v1(inp: AirStrikeInput) -> "AirStrikeResultLegacyV1":
    """[LEGACY v1, unused after M3 2026-04-12] Country-level air combat.

    Renamed in M3 (2026-04-12) to avoid collision with the canonical
    M3 ``resolve_air_strike(attackers, defenders, ad_units, …)``.
    Kept here for reference; no callers in production code.

    Original docstring:
    Air units strike a target zone. Defender's air defense intercepts with
    degrading probability per AD unit. Intercepted air units are DESTROYED.
    Surviving air units strike at 15% hit rate per unit.

    AD interception model (from SEED):
    - Round-robin: each incoming air unit faces one AD unit
    - Degrading rate per attempt: 1st=95%, 2nd=80%, then max(60%, 75% - (n-3)*5%)
    - Intercept = air unit destroyed; miss = air unit gets through
    """
    available_air = inp.attacker.tactical_air
    if available_air <= 0:
        return AirStrikeResultLegacyV1(
            country=inp.country_id,
            target_zone=inp.target_zone_id,
            error=f"{inp.country_id} has no tactical air units",
        )

    air_sent = min(inp.air_units_sent or available_air, available_air)

    # Collect AD units in target zone + adjacent zones
    defender_ad = 0
    for cid, forces in inp.target_zone.forces.items():
        if cid != inp.country_id:
            defender_ad += forces.get("air_defense", 0)
    for adj_zone in inp.adjacent_zones:
        for cid, forces in adj_zone.forces.items():
            if cid != inp.country_id:
                defender_ad += forces.get("air_defense", 0)

    # AD interception: round-robin with degrading rate
    intercepted = 0
    if defender_ad > 0:
        for i in range(air_sent):
            # Which AD unit handles this? Round-robin.
            # ad_idx = i % defender_ad  -- not needed for calculation
            attempt_num = (i // defender_ad) + 1
            # Degrading rate per attempt number for this AD unit
            if attempt_num == 1:
                rate = 0.95
            elif attempt_num == 2:
                rate = 0.80
            else:
                rate = max(0.60, 0.75 - (attempt_num - 3) * 0.05)

            if random.random() < rate:
                intercepted += 1

    survivors = air_sent - intercepted

    # Surviving air units strike at 15% hit rate
    ground_destroyed = 0
    for _ in range(survivors):
        if random.random() < AIR_STRIKE_HIT_PROB:
            ground_destroyed += 1

    return AirStrikeResultLegacyV1(
        country=inp.country_id,
        target_zone=inp.target_zone_id,
        air_sent=air_sent,
        intercepted_destroyed=intercepted,
        strikes_landed=survivors,
        ground_units_destroyed=ground_destroyed,
        air_returned=survivors,
    )


def resolve_airfield_vulnerability(inp: AirfieldVulnerabilityInput) -> AirfieldVulnerabilityResult:
    """When a zone is attacked, stationed air units risk destruction on the ground.

    20% chance per air unit of being destroyed (parked aircraft, airfield damage,
    carrier strikes on ports). Called BEFORE ground combat or air defense.
    """
    total_destroyed = 0
    losses_by_country: dict[str, int] = {}

    for cid, forces in inp.target_zone.forces.items():
        if cid == inp.attacking_country_id:
            continue
        air_in_zone = forces.get("tactical_air", 0)
        destroyed = 0
        for _ in range(air_in_zone):
            if random.random() < AIRFIELD_VULNERABILITY_PROB:
                destroyed += 1
        if destroyed > 0:
            losses_by_country[cid] = destroyed
            total_destroyed += destroyed

    return AirfieldVulnerabilityResult(
        zone=inp.target_zone_id,
        destroyed=total_destroyed,
        losses_by_country=losses_by_country,
    )


# ===========================================================================
# 4. BLOCKADE MECHANICS
# ===========================================================================

def resolve_blockade(inp: BlockadeInput) -> BlockadeResult:
    """Ground-force blockade at chokepoints (ACTION REVIEW 2026-03-30).

    - Blockade requires GROUND FORCES at chokepoint (not naval superiority)
    - Formosa special: full requires naval in 3+ surrounding sea zones.
      1 friendly ship at any adjacent zone = automatic downgrade to partial.
    - Breaking a blockade: destroy ALL military units at chokepoint,
      or blocker lifts voluntarily.
    """
    level = inp.level.value

    if level not in ("full", "partial"):
        return BlockadeResult(
            country=inp.country_id,
            zone=inp.zone_id,
            level=level,
            error=f"Invalid blockade level: {level}. Must be 'full' or 'partial'.",
        )

    # --- FORMOSA SPECIAL BLOCKADE ---
    if inp.zone_id in ("formosa", "g_formosa"):
        return _resolve_formosa_blockade(inp, level)

    # --- STANDARD CHOKEPOINT BLOCKADE (ground forces required) ---
    country_forces = inp.zone.forces.get(inp.country_id, {})
    ground = country_forces.get("ground", 0)

    if ground < 1:
        return BlockadeResult(
            country=inp.country_id,
            zone=inp.zone_id,
            level=level,
            error=(
                f"{inp.country_id} has no ground forces at {inp.zone_id}. "
                "Ground forces required for blockade."
            ),
        )

    # Find matching chokepoint name
    chokepoint_name: Optional[str] = None
    for cp_name, cp_data in CHOKEPOINTS.items():
        if cp_data["zone"] == inp.zone_id:
            chokepoint_name = cp_name
            break

    return BlockadeResult(
        country=inp.country_id,
        zone=inp.zone_id,
        level=level,
        success=True,
        blockade_type="ground",
        chokepoint=chokepoint_name,
        note=(
            f"Ground blockade at {inp.zone_id} ({level}). "
            "Air strikes cannot break -- requires ground invasion or voluntary lift."
        ),
    )


def _resolve_formosa_blockade(inp: BlockadeInput, level: str) -> BlockadeResult:
    """Formosa special blockade rules.

    Full blockade: requires naval units in 3+ surrounding sea zones.
    Any 1 friendly (to Formosa) ship at any adjacent zone = automatic
    downgrade to partial. Partial = strait only.
    """
    # Count how many adjacent sea zones the blocker has naval presence in
    zones_with_naval = 0
    for sz in inp.adjacent_sea_zones:
        blocker_naval = sz.forces.get(inp.country_id, {}).get("naval", 0)
        if blocker_naval > 0:
            zones_with_naval += 1

    auto_downgraded = False
    downgrade_reason: Optional[str] = None

    if level == "full":
        if zones_with_naval < 3:
            return BlockadeResult(
                country=inp.country_id,
                zone=inp.zone_id,
                level=level,
                error=(
                    f"Formosa full blockade requires naval in 3+ surrounding zones. "
                    f"{inp.country_id} has naval in {zones_with_naval} zones."
                ),
            )

        # Check for any friendly (non-blocker) ship in adjacent zones
        friendly_ship_present = False
        for sz in inp.adjacent_sea_zones:
            for cid, forces in sz.forces.items():
                if cid == inp.country_id:
                    continue
                naval = forces.get("naval", 0)
                if naval > 0:
                    friendly_ship_present = True
                    break
            if friendly_ship_present:
                break

        if friendly_ship_present:
            level = "partial"
            auto_downgraded = True
            downgrade_reason = (
                "Friendly ship detected at adjacent zone -- "
                "full blockade automatically downgraded to partial"
            )

    return BlockadeResult(
        country=inp.country_id,
        zone=inp.zone_id,
        level=level,
        success=True,
        blockade_type="naval",
        chokepoint="taiwan_strait",
        auto_downgraded=auto_downgraded,
        downgrade_reason=downgrade_reason,
        note=(
            f"Formosa blockade ({level}). "
            + ("Strait only -- partial." if level == "partial"
               else "Full naval encirclement.")
        ),
    )


# ===========================================================================
# 4b. NAVAL BOMBARDMENT
# ===========================================================================

def resolve_naval_bombardment(inp: NavalBombardmentInput) -> NavalBombardmentResult:
    """Each naval unit adjacent to land can bombard once per round.
    10% chance per unit of destroying one random ground unit."""
    if not inp.is_adjacent:
        return NavalBombardmentResult(
            country=inp.country_id,
            sea_zone=inp.sea_zone_id,
            target_zone=inp.target_land_zone_id,
            error=f"{inp.sea_zone_id} not adjacent to {inp.target_land_zone_id}",
        )

    if inp.naval_units_in_zone <= 0:
        return NavalBombardmentResult(
            country=inp.country_id,
            sea_zone=inp.sea_zone_id,
            target_zone=inp.target_land_zone_id,
            error=f"{inp.country_id} has no naval units in {inp.sea_zone_id}",
        )

    destroyed = 0
    for _ in range(inp.naval_units_in_zone):
        if random.random() < NAVAL_BOMBARDMENT_HIT_PROB:
            destroyed += 1

    return NavalBombardmentResult(
        country=inp.country_id,
        sea_zone=inp.sea_zone_id,
        target_zone=inp.target_land_zone_id,
        units_destroyed=destroyed,
    )


# ===========================================================================
# 5. MISSILE STRIKE — conventional and nuclear
# ===========================================================================

def resolve_missile_strike(inp: MissileStrikeInput) -> MissileStrikeResult:
    """Strategic missile -- global alert, 3 confirmations for nuclear.

    Warhead types:
    - conventional: 10% of ground units destroyed (min 1)
    - nuclear_l1: 50% troops destroyed, economy -2 coins per affected country
    - nuclear_l2: 30% economic capacity destroyed, 50% military,
                  leader survival 1/6 (survives on 2-6), global stability shock (-2 all)

    Air defense interception: each AD unit can attempt up to 3 intercepts,
    max 5 attempts total, 30% intercept probability per attempt.
    """
    launcher = inp.launcher

    if launcher.strategic_missile <= 0:
        return MissileStrikeResult(
            launcher=inp.launcher_country,
            target_zone=inp.target_zone_id,
            warhead_type=inp.warhead_type.value,
            error=f"{inp.launcher_country} has no strategic missiles",
        )

    is_nuclear = inp.warhead_type in (WarheadType.NUCLEAR_L1, WarheadType.NUCLEAR_L2)
    if is_nuclear and launcher.nuclear_level < 1:
        return MissileStrikeResult(
            launcher=inp.launcher_country,
            target_zone=inp.target_zone_id,
            warhead_type=inp.warhead_type.value,
            error=f"{inp.launcher_country} lacks nuclear capability (L{launcher.nuclear_level})",
        )

    # Air defense interception
    total_ad = sum(
        forces.get("air_defense", 0)
        for cid, forces in inp.target_zone.forces.items()
        if cid != inp.launcher_country
    )
    intercept_attempts = min(total_ad * 3, MISSILE_AD_MAX_ATTEMPTS)
    intercepted = False
    for _ in range(intercept_attempts):
        if random.random() < MISSILE_INTERCEPT_PROB:
            intercepted = True
            break

    if intercepted:
        return MissileStrikeResult(
            launcher=inp.launcher_country,
            target_zone=inp.target_zone_id,
            warhead_type=inp.warhead_type.value,
            success=False,
            intercepted=True,
            note="Missile intercepted by air defense",
        )

    # --- Apply damage ---
    result = MissileStrikeResult(
        launcher=inp.launcher_country,
        target_zone=inp.target_zone_id,
        warhead_type=inp.warhead_type.value,
        success=True,
        intercepted=False,
    )

    if inp.warhead_type == WarheadType.NUCLEAR_L2 or (
        is_nuclear and launcher.nuclear_level >= 2
    ):
        _apply_nuclear_l2(inp, result)
    elif inp.warhead_type == WarheadType.NUCLEAR_L1 or is_nuclear:
        _apply_nuclear_l1(inp, result)
    else:
        _apply_conventional_strike(inp, result)

    return result


def _apply_conventional_strike(inp: MissileStrikeInput, result: MissileStrikeResult) -> None:
    """Conventional: 10% of ground units destroyed (min 1 per country in zone)."""
    total_destroyed = 0
    for cid, forces in inp.target_zone.forces.items():
        if cid == inp.launcher_country:
            continue
        ground = forces.get("ground", 0)
        if ground > 0:
            losses = max(1, int(ground * 0.10))
            total_destroyed += losses
    result.ground_destroyed = total_destroyed


def _apply_nuclear_l1(inp: MissileStrikeInput, result: MissileStrikeResult) -> None:
    """Tactical nuclear: 50% troops destroyed, economy -2 coins per affected country."""
    result.nuclear_used = True
    result.nuclear_level = 1
    total_destroyed = 0
    affected: list[str] = []
    treasury_losses: dict[str, float] = {}

    for cid, forces in inp.target_zone.forces.items():
        if cid == inp.launcher_country:
            continue
        ground = forces.get("ground", 0)
        losses = int(ground * 0.50)
        total_destroyed += losses
        affected.append(cid)
        treasury_losses[cid] = 2.0

    result.ground_destroyed = total_destroyed
    result.affected_countries = affected
    result.treasury_losses = treasury_losses


def _apply_nuclear_l2(inp: MissileStrikeInput, result: MissileStrikeResult) -> None:
    """Strategic nuclear: 30% economic capacity, 50% military, leader survival 1/6.

    Leader survives on roll 2-6 (i.e. 1/6 chance of death).
    Global stability shock: every country loses 2 stability.
    """
    result.nuclear_used = True
    result.nuclear_level = 2
    result.global_stability_shock = True
    result.global_stability_loss = 2.0
    result.gdp_multiplier = 0.70
    affected: list[str] = []
    mil_losses: dict[str, dict[str, int]] = {}
    leaders_killed: list[str] = []
    leader_rolls: dict[str, bool] = {}

    for cid, forces in inp.target_zone.forces.items():
        if cid == inp.launcher_country:
            continue
        affected.append(cid)
        # 50% military destroyed per unit type
        country_mil_losses: dict[str, int] = {}
        for ut in ["ground", "naval", "tactical_air"]:
            current = forces.get(ut, 0)
            losses = int(current * 0.50)
            country_mil_losses[ut] = losses
        mil_losses[cid] = country_mil_losses

        # Leader survival: survives on 2-6 (1/6 death chance)
        survives = random.randint(1, 6) >= 2
        leader_rolls[cid] = survives
        if not survives:
            leaders_killed.append(cid)

    result.affected_countries = affected
    result.military_losses_by_country = mil_losses
    result.leaders_killed = leaders_killed
    result.leader_survival_rolls = leader_rolls


# ===========================================================================
# 6. COVERT OPERATIONS
# ===========================================================================

def resolve_covert_op(inp: CovertOpInput) -> CovertOpResult:
    """Intelligence, sabotage, cyber, disinformation, election meddling.

    Rules (updated 2026-03-30 per action review):
    - Per-INDIVIDUAL card pools (from roles.csv: intelligence_pool, sabotage_cards, etc.)
    - Each card consumed permanently -- never recovers
    - Intelligence requests ALWAYS return an answer (accuracy varies)
    - Failed ops return low-accuracy info (not nothing)
    - Detection and attribution are SEPARATE events
    """
    op_type = inp.op_type.value
    card_field = COVERT_CARD_FIELD_MAP.get(op_type, "intelligence_pool")

    # Check per-individual card pool
    card_consumed = False
    if inp.role_id and inp.role:
        remaining = getattr(inp.role, card_field, 0)
        if remaining <= 0:
            return CovertOpResult(
                op_type=op_type,
                country=inp.country_id,
                target=inp.target_country_code,
                role_id=inp.role_id,
                error=f"{inp.role_id} has no {op_type} cards remaining",
            )
        card_consumed = True
    else:
        # Fallback: country-level limit (legacy compatibility)
        max_ops = 3
        if inp.covert_ops_this_round >= max_ops:
            return CovertOpResult(
                op_type=op_type,
                country=inp.country_id,
                target=inp.target_country_code,
                error=f"{inp.country_id} has reached covert op limit this round",
            )

    # Calculate success probability
    base_prob = COVERT_BASE_PROBABILITY.get(op_type, 0.50)
    prob = base_prob + inp.ai_level * 0.05

    # Repeated ops penalty
    prob -= inp.prev_ops_against_target * 0.05
    prob = clamp(prob, 0.05, 0.95)

    # Roll for success
    success = random.random() < prob

    # Roll for detection (target learns SOMETHING happened)
    detect_base = COVERT_DETECTION_BASE.get(op_type, 0.40)
    detect_prob = detect_base + inp.prev_ops_against_target * 0.10
    detect_prob = clamp(detect_prob, 0.10, 0.90)
    detected = random.random() < detect_prob

    # Roll for attribution SEPARATELY (target learns WHO did it)
    attributed = False
    if detected:
        attribution_prob = COVERT_ATTRIBUTION_PROBABILITY.get(op_type, 0.30)
        attributed = random.random() < attribution_prob

    result = CovertOpResult(
        op_type=op_type,
        country=inp.country_id,
        target=inp.target_country_code,
        role_id=inp.role_id,
        success=success,
        detected=detected,
        attributed=attributed,
        success_probability=round(prob, 3),
        detection_probability=round(detect_prob, 3),
        card_consumed=card_consumed,
        card_field=card_field if card_consumed else None,
    )

    # Apply effects
    tc = inp.target_country

    if op_type == "sabotage" and success:
        damage = tc.gdp * 0.02
        result.gdp_damage = round(damage, 2)

    elif op_type == "propaganda" and success:
        result.stability_impact = -0.3
        result.support_impact = -3.0

    return result


def _gather_intelligence(target: CountryMilitary, accuracy: float) -> IntelligenceReport:
    """Generate intelligence report -- ALWAYS returns data, accuracy varies.

    High accuracy (>=0.75): data is +/-5% of real values
    Medium accuracy (>=0.50): data is +/-15%
    Low accuracy (<0.50): data is +/-30% -- seriously unreliable

    The recipient does NOT know the accuracy level -- report looks the same.
    """
    if accuracy >= 0.75:
        noise_range = 0.05
    elif accuracy >= 0.50:
        noise_range = 0.15
    else:
        noise_range = 0.30

    def noisy(value: float, is_int: bool = False) -> float | int:
        noise = random.uniform(1.0 - noise_range, 1.0 + noise_range)
        r = value * noise
        return int(round(r)) if is_int else round(r, 1)

    return IntelligenceReport(
        gdp_estimate=noisy(target.gdp),
        treasury_estimate=noisy(target.treasury),
        stability_estimate=noisy(target.stability),
        support_estimate=noisy(target.political_support),
        military_ground_estimate=noisy(target.ground, True),
        military_naval_estimate=noisy(target.naval, True),
        military_air_estimate=noisy(target.tactical_air, True),
        nuclear_level=target.nuclear_level,
        nuclear_progress_estimate=noisy(0.0),  # orchestrator must supply actual progress
        ai_level=target.ai_level,
        mobilization_pool_estimate=noisy(target.mobilization_pool, True),
    )


# ===========================================================================
# 6b. ASSASSINATION
# ===========================================================================

def resolve_assassination(inp: AssassinationInput) -> AssassinationResult:
    """Assassination (ACTION REVIEW 2026-03-30).

    1 card per game per eligible role.
    Domestic: 60% base hit.
    International: 20% base + country-specific bonuses.
    No AI tech or intel chief modifiers. Raw probability.
    Hit = 50% kill, 50% survive (injured + martyr effect).
    International: higher chance of being revealed if failed.
    """
    role = inp.target_role

    # Base probability -- domestic vs international
    if inp.domestic:
        prob = 0.60
    else:
        prob = 0.20
        prob += ASSASSINATION_COUNTRY_BONUS.get(inp.country_id, 0.0)

    hit = random.random() < prob

    # Detection: international failures have higher reveal chance
    if inp.domestic:
        detected = random.random() < 0.50
    else:
        detected = random.random() < (0.70 if not hit else 0.40)

    result = AssassinationResult(
        country=inp.country_id,
        target_role=inp.target_role_id,
        domestic=inp.domestic,
        hit=hit,
        detected=detected,
        probability=round(prob, 3),
    )

    if hit:
        # 50/50 kill or survive
        if random.random() < 0.50:
            result.success = True
            result.target_survived = False
            result.new_target_status = "dead"
            result.note = f"{role.character_name} killed"
            # Martyr effect: +15 political support to target's country
            result.martyr_effect = 15
        else:
            result.success = True
            result.target_survived = True
            result.new_target_status = "active"
            result.note = (
                f"{role.character_name} survived -- injured. "
                "Martyr effect boosts support."
            )
            # Survived assassination: +10 political support
            result.martyr_effect = 10
    else:
        result.success = False
        result.note = "Assassination attempt failed"

    return result


# ===========================================================================
# 6c. COUP ATTEMPT
# ===========================================================================

def resolve_coup(inp: CoupInput) -> CoupResult:
    """Coup attempt (ACTION REVIEW 2026-03-30).

    Two conspirators required: initiator + co-conspirator.
    Base 15%
    + active_protest: +25%
    + stability < 3: +15%
    + stability 3-4: +5%
    + support < 30%: +10%
    Success: initiator becomes HoS, old HoS arrested.
    Failure: both exposed (arrested, world learns).
    """
    if len(inp.plotter_role_ids) < 2:
        return CoupResult(
            country=inp.country_id,
            plotters=inp.plotter_role_ids,
            error="Coup requires two conspirators (initiator + co-conspirator)",
        )

    # Verify plotters are in the same country
    for role in inp.plotter_roles[:2]:
        if role.country_id != inp.country_id:
            return CoupResult(
                country=inp.country_id,
                plotters=inp.plotter_role_ids,
                error=f"Role {role.role_id} is not in {inp.country_id}",
            )

    stability = inp.stability
    support = inp.political_support

    # Base probability
    prob = 0.15

    # Active protest bonus
    if inp.protest_active:
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

    initiator_id = inp.plotter_role_ids[0]
    co_conspirator_id = inp.plotter_role_ids[1]

    if success:
        return CoupResult(
            country=inp.country_id,
            plotters=inp.plotter_role_ids[:2],
            success=True,
            probability=round(prob, 3),
            new_leader=initiator_id,
            old_leader_status="arrested",
            stability_change=-2.0,
            note=(
                f"Coup successful. {initiator_id} takes power. "
                "Former leader arrested."
            ),
        )
    else:
        return CoupResult(
            country=inp.country_id,
            plotters=inp.plotter_role_ids[:2],
            success=False,
            probability=round(prob, 3),
            plotter_status="exposed",
            stability_change=-1.0,
            note=(
                f"Coup failed. {initiator_id} and {co_conspirator_id} exposed. "
                "Ruler and world learn of the attempt."
            ),
        )


# ===========================================================================
# 7. MILITARY PRODUCTION & MOBILIZATION
# ===========================================================================

def validate_production_order(inp: ProductionOrderInput) -> ProductionResult:
    """Validate and cost a military production order.

    Production uses finite depletable pools:
    - Each country has production_capacity per unit type (units/round)
    - Tiers: normal (1x cost, 1x output), accelerated (2x cost, 2x output),
             maximum (4x cost, 3x output)
    - Cost = base_cost * quantity * tier_cost_multiplier
    - Output = min(quantity, capacity * tier_output_multiplier)
    - Treasury must cover cost.
    """
    c = inp.country

    if inp.unit_type not in ("ground", "naval", "tactical_air"):
        return ProductionResult(
            country_id=inp.country_id,
            unit_type=inp.unit_type,
            quantity=inp.quantity,
            tier=inp.tier,
            error=f"Invalid unit type for production: {inp.unit_type}",
        )

    if inp.tier not in PRODUCTION_TIER_COST:
        return ProductionResult(
            country_id=inp.country_id,
            unit_type=inp.unit_type,
            quantity=inp.quantity,
            tier=inp.tier,
            error=f"Invalid production tier: {inp.tier}",
        )

    # Get base cost and capacity
    cost_map = {
        "ground": c.prod_cost_ground,
        "naval": c.prod_cost_naval,
        "tactical_air": c.prod_cost_tactical,
    }
    cap_map = {
        "ground": c.prod_cap_ground,
        "naval": c.prod_cap_naval,
        "tactical_air": c.prod_cap_tactical,
    }

    base_cost = cost_map[inp.unit_type]
    capacity = cap_map[inp.unit_type]

    tier_cost_mult = PRODUCTION_TIER_COST[inp.tier]
    tier_output_mult = PRODUCTION_TIER_OUTPUT[inp.tier]

    # Max units this round = capacity * tier output multiplier
    max_units = int(capacity * tier_output_mult)
    actual_units = min(inp.quantity, max_units)

    # Total cost
    total_cost = base_cost * actual_units * tier_cost_mult

    if total_cost > c.treasury:
        return ProductionResult(
            country_id=inp.country_id,
            unit_type=inp.unit_type,
            quantity=inp.quantity,
            tier=inp.tier,
            error=(
                f"Insufficient treasury: need {total_cost:.1f}, "
                f"have {c.treasury:.1f}"
            ),
        )

    return ProductionResult(
        country_id=inp.country_id,
        unit_type=inp.unit_type,
        quantity=inp.quantity,
        tier=inp.tier,
        valid=True,
        total_cost=round(total_cost, 2),
        units_produced=actual_units,
    )


def resolve_martial_law(inp: MartialLawInput) -> MartialLawResult:
    """Mobilize ground units from the finite martial-law pool.

    Renamed 2026-04-11 from resolve_mobilization to eliminate the naming
    collision with the deprecated round_engine/movement.py:resolve_mobilization
    (deploy-from-reserve mechanic). Per CONTRACT_MOVEMENT v1.0 closing step.

    The martial-law pool is set at game start and never replenishes.
    Units mobilized are added to ground forces; pool is reduced.
    """
    pool = inp.country.mobilization_pool
    if pool <= 0:
        return MartialLawResult(
            country_id=inp.country_id,
            error=f"{inp.country_id} has no martial-law pool remaining",
        )

    actual = min(inp.units_to_mobilize, pool)
    return MartialLawResult(
        country_id=inp.country_id,
        units_mobilized=actual,
        pool_remaining=pool - actual,
    )


# ===========================================================================
# 8. DEPLOYMENT VALIDATION
# ===========================================================================

def validate_deployment(inp: DeploymentValidationInput) -> DeploymentValidationResult:
    """Validate a unit deployment/movement order.

    Checks:
    - Country has enough units of the specified type
    - Target zone exists (caller provides ZoneInfo)
    - Units can reach the target (adjacency check via origin)
    - Naval units can only go to sea/chokepoint_sea zones
    - Ground units cannot move through sea without naval transport
    """
    c = inp.country
    unit_counts = {
        "ground": c.ground,
        "naval": c.naval,
        "tactical_air": c.tactical_air,
        "strategic_missile": c.strategic_missile,
        "air_defense": c.air_defense,
    }

    if inp.unit_type not in unit_counts:
        return DeploymentValidationResult(
            country_id=inp.country_id,
            unit_type=inp.unit_type,
            count=inp.count,
            target_zone_id=inp.target_zone_id,
            error=f"Invalid unit type: {inp.unit_type}",
        )

    # Check unit availability (country-level total)
    available = unit_counts[inp.unit_type]
    if inp.count > available:
        return DeploymentValidationResult(
            country_id=inp.country_id,
            unit_type=inp.unit_type,
            count=inp.count,
            target_zone_id=inp.target_zone_id,
            error=(
                f"Insufficient {inp.unit_type}: need {inp.count}, "
                f"have {available}"
            ),
        )

    # Naval units: target must be sea or chokepoint_sea
    target_type = inp.target_zone.zone_type
    if inp.unit_type == "naval" and not target_type.startswith("sea") and target_type != "chokepoint_sea":
        return DeploymentValidationResult(
            country_id=inp.country_id,
            unit_type=inp.unit_type,
            count=inp.count,
            target_zone_id=inp.target_zone_id,
            error=f"Naval units cannot deploy to {target_type} zone {inp.target_zone_id}",
        )

    # Adjacency check: if origin provided, target must be adjacent to origin
    if inp.origin_zone_id and inp.origin_zone:
        is_adj = any(
            adj.zone_id == inp.target_zone_id
            for adj in inp.origin_adjacency
        )
        if not is_adj:
            return DeploymentValidationResult(
                country_id=inp.country_id,
                unit_type=inp.unit_type,
                count=inp.count,
                target_zone_id=inp.target_zone_id,
                error=(
                    f"Target zone {inp.target_zone_id} is not adjacent to "
                    f"origin {inp.origin_zone_id}"
                ),
            )

        # Ground units crossing sea need naval transport
        if inp.unit_type == "ground":
            for adj in inp.origin_adjacency:
                if adj.zone_id == inp.target_zone_id and adj.connection_type == "land_sea":
                    # Need to verify naval transport is available
                    # (orchestrator handles actual transport -- we just flag it)
                    pass

    return DeploymentValidationResult(
        valid=True,
        country_id=inp.country_id,
        unit_type=inp.unit_type,
        count=inp.count,
        target_zone_id=inp.target_zone_id,
    )


# ===========================================================================
# 9. NUCLEAR TEST
# ===========================================================================

def resolve_nuclear_test(inp: NuclearTestInput) -> NuclearTestResult:
    """Nuclear test -- a SIGNAL to the world + tech development milestone.

    - underground: less provocative, -0.2 stability to tester, -0.3 global
    - overground: maximum signal, -0.5 stability to tester, -0.3 global to ALL

    NOT required to advance nuclear tech -- R&D investment is the path.
    But test CONFIRMS capability (makes deterrent credible).
    Domestic political support boost: +5 (nationalist rally).
    """
    if inp.country.nuclear_level < 1:
        return NuclearTestResult(
            country_id=inp.country_id,
            test_type=inp.test_type.value,
            error="Must have at least L1 nuclear to test",
        )

    if inp.test_type == NuclearTestType.OVERGROUND:
        global_loss = 0.3
        tester_loss = 0.5
        note = f"{inp.country_id} conducts overground nuclear test -- global shock"
    else:
        global_loss = 0.0  # underground: no global shock (just tester)
        # NOTE: SEED applies -0.3 to all countries for overground only.
        # Underground: only tester pays. This matches SEED exactly.
        tester_loss = 0.2
        note = f"{inp.country_id} conducts underground nuclear test -- detected by intelligence"

    return NuclearTestResult(
        country_id=inp.country_id,
        test_type=inp.test_type.value,
        success=True,
        global_stability_loss=global_loss,
        tester_stability_loss=tester_loss,
        tester_support_boost=5.0,
        note=note,
    )


# ===========================================================================
# UNIT-LEVEL COMBAT (v2, 2026-04-06) — CALIBRATED, CANONICAL
# ===========================================================================
#
# This subsystem replaces the zone+count combat model (resolve_attack,
# resolve_air_strike, resolve_missile_strike, resolve_naval_combat,
# resolve_naval_bombardment) with unit-level functions that operate on
# UnitSnapshot instances and match the calibration decisions Marat made
# during Observatory testing (2026-04-05 / 2026-04-06).
#
# CALIBRATED RULES (see CHANGES_LOG 2026-04-05 / 2026-04-06 sections):
#   * Ground combat: iterative RISK dice (3 att vs 2 def), ties defender,
#     loop until one side zero. Defenders = ground on target hex +
#     naval on adjacent sea hexes (naval equal strength).
#   * Trophy capture: on ground-attack win, all non-ground non-naval
#     enemy units on the target hex flip to attacker's reserve
#     (tactical_air, air_defense, strategic_missile).
#   * Source minimum: 1+ ground stays on captured foreign hex before
#     chaining (caller enforces — pure combat only computes).
#   * Air strike: 12% base hit if no AD covers zone, 6% (halved) if
#     AD present. +2% per air-superiority unit, cap +4%.
#     Clamp [3%, 20%]. Range: hex distance ≤ 2 from launcher.
#   * Missile strike: 80% base, 30% if AD present. Missile is CONSUMED
#     on fire (disposable). Nuclear L1/L2 warheads preserved from
#     designed model.
#   * AD coverage zone: the global hex PLUS all theater hexes linked
#     to it (per map_config.theater_link_hexes).
#
# STATELESS DISCIPLINE: these functions MUTATE NOTHING. They read
# inputs and return typed results. The orchestrator applies state
# changes (flip ownership for trophies, move units forward, destroy
# consumed missiles, etc).
#
# Port origin: engine/round_engine/combat.py (round_engine to be
# decommissioned in Phase 4 of reunification).
# ===========================================================================

# ---------------------------------------------------------------------------
# CALIBRATION CONSTANTS
# ---------------------------------------------------------------------------

AIR_STRIKE_BASE_HIT_PROB_V2: float = 0.12          # was 0.15 in v1
AIR_STRIKE_AD_MULTIPLIER: float = 0.50              # halving
AIR_STRIKE_SUPERIORITY_BONUS: float = 0.02          # per unit
AIR_STRIKE_SUPERIORITY_CAP: float = 0.04
AIR_STRIKE_CLAMP_LOW: float = 0.03
AIR_STRIKE_CLAMP_HIGH: float = 0.20
AIR_STRIKE_MAX_RANGE: int = 2                       # hex distance

# Conventional missile: flat 75% hit (after surviving AD interception)
MISSILE_HIT_PROB: float = 0.75
# AD interception: 50% per AD unit, rolled BEFORE hit (two-phase model)
MISSILE_AD_INTERCEPT_PROB: float = 0.50
# Legacy aliases (referenced by v1 code)
MISSILE_BASE_HIT_PROB_V2: float = MISSILE_HIT_PROB
MISSILE_AD_HIT_PROB_V2: float = MISSILE_HIT_PROB  # no longer reduced by AD

GROUND_COMBAT_MAX_EXCHANGES: int = 50               # safety bound


# ---------------------------------------------------------------------------
# UNIT-LEVEL INPUT / RESULT MODELS
# ---------------------------------------------------------------------------

class UnitSnapshot(BaseModel):
    """One unit's state at combat time (read-only input).

    Mirrors the shape of unit_states_per_round rows.
    """
    unit_code: str
    country_code: str
    unit_type: str                     # ground|naval|tactical_air|strategic_missile|air_defense
    status: str = "active"             # active|reserve|embarked|destroyed
    global_row: Optional[int] = None
    global_col: Optional[int] = None
    theater: Optional[str] = None
    theater_row: Optional[int] = None
    theater_col: Optional[int] = None
    embarked_on: Optional[str] = None


class UnitGroundAttackInput(BaseModel):
    """Ground attack on a target hex (unit-level)."""
    attacker_country: str
    defender_country: str
    target_global_row: int
    target_global_col: int
    attacker_units: list[UnitSnapshot]    # ground units committed
    defender_ground_units: list[UnitSnapshot]    # enemy ground on target hex
    adjacent_naval_defenders: list[UnitSnapshot] = Field(default_factory=list)
    trophies_on_hex: list[UnitSnapshot] = Field(default_factory=list)  # non-ground non-naval
    # Optional modifiers
    air_superiority: bool = False
    amphibious_3to1: bool = False
    die_hard_terrain: bool = False


class UnitGroundAttackResult(BaseModel):
    """Ground attack outcome (unit-level, caller applies state)."""
    attacker_country: str
    defender_country: str
    target_global_row: int
    target_global_col: int
    success: bool                                  # attacker captured the hex
    exchanges: int                                 # number of dice rounds
    attacker_losses: list[str] = Field(default_factory=list)   # unit_codes
    defender_losses: list[str] = Field(default_factory=list)
    attacker_rolls: list[int] = Field(default_factory=list)    # all rolls flattened
    defender_rolls: list[int] = Field(default_factory=list)
    attackers_move_forward: list[str] = Field(default_factory=list)   # survivors to move
    trophies_captured: list[str] = Field(default_factory=list)         # unit_codes
    narrative: str = ""


class UnitAirStrikeInput(BaseModel):
    """Tactical air strike on a target hex (unit-level)."""
    attacker_unit: UnitSnapshot
    target_global_row: int
    target_global_col: int
    defender_units: list[UnitSnapshot]            # units on target hex (ground + AD + etc.)
    ad_units_covering_zone: list[UnitSnapshot] = Field(default_factory=list)
    air_superiority_count: int = 0


class UnitAirStrikeResult(BaseModel):
    attacker_unit_code: str
    target_global_row: int
    target_global_col: int
    success: bool
    probability: float
    roll: float
    ad_present: bool
    defender_losses: list[str] = Field(default_factory=list)
    out_of_range: bool = False
    distance: Optional[int] = None
    narrative: str = ""


class UnitMissileStrikeInput(BaseModel):
    """Per-missile strike input (unit-level). One call per missile.

    Tier semantics (Marat 2026-04-06):
      * T1_MIDRANGE: intercepted by AD-in-zone halving (handled here)
      * T2_STRATEGIC_SINGLE / T3_STRATEGIC_SALVO: intercepted by T3+
        nations via resolve_nuclear_interceptions_salvo() BEFORE this
        function is called. Surviving missiles call this per hex.
        No AD-in-zone halving applied.

    For nuclear warheads, caller provides ``target_country`` +
    ``target_country_hex_count`` so the engine can report economic
    damage as a % of GDP (pro-rated by the target hex's share).
    """
    missile_unit: UnitSnapshot
    target_global_row: int
    target_global_col: int
    warhead_type: WarheadType = WarheadType.CONVENTIONAL
    attack_tier: StrategicAttackTier = StrategicAttackTier.T1_MIDRANGE
    defender_units: list[UnitSnapshot]            # all units on target hex
    ad_units_covering_zone: list[UnitSnapshot] = Field(default_factory=list)
    # For nuclear warheads (damage scaling):
    target_country: str = ""                      # owner of the target hex
    target_country_hex_count: int = 0              # total land hexes owned (>=1)


class UnitMissileStrikeResult(BaseModel):
    missile_unit_code: str                         # consumed on fire
    target_global_row: int
    target_global_col: int
    warhead_type: str
    success: bool
    probability: float
    roll: float
    ad_present: bool
    defender_losses: list[str] = Field(default_factory=list)
    missile_consumed: bool = True                  # always True (disposable)
    # Nuclear-only fields (per-missile/per-hex):
    nuclear_used: bool = False
    nuclear_level: int = 0
    target_country: str = ""                       # owner of the hit hex
    economic_damage_pct: float = 0.0               # of target country GDP
    military_destroyed_pct: float = 0.0            # fraction of units on hex killed
    narrative: str = ""


class UnitNavalCombatInput(BaseModel):
    """Ship vs ship combat at a sea hex (unit-level)."""
    attacker_country: str
    defender_country: str
    sea_global_row: int
    sea_global_col: int
    attacker_fleet: list[UnitSnapshot]
    defender_fleet: list[UnitSnapshot]


class UnitNavalCombatResult(BaseModel):
    attacker_country: str
    defender_country: str
    sea_global_row: int
    sea_global_col: int
    exchanges: int
    attacker_losses: list[str] = Field(default_factory=list)
    defender_losses: list[str] = Field(default_factory=list)
    attacker_rolls: list[int] = Field(default_factory=list)
    defender_rolls: list[int] = Field(default_factory=list)
    success: bool = False
    narrative: str = ""


class UnitNavalBombardmentInput(BaseModel):
    """Naval units shelling a land hex (unit-level)."""
    attacker_country: str
    defender_country: str
    target_global_row: int
    target_global_col: int
    naval_units: list[UnitSnapshot]                # each bombards once per round
    defender_ground_units: list[UnitSnapshot]


class UnitNavalBombardmentResult(BaseModel):
    attacker_country: str
    defender_country: str
    target_global_row: int
    target_global_col: int
    shots_fired: int
    defender_losses: list[str] = Field(default_factory=list)
    rolls: list[float] = Field(default_factory=list)
    narrative: str = ""


# ---------------------------------------------------------------------------
# HELPERS (hex geometry + AD zone + naval-adjacent)
# ---------------------------------------------------------------------------



def _hex_neighbors_v2(row: int, col: int) -> list[tuple[int, int]]:
    """6 pointy-top odd-r offset neighbors (1-indexed)."""
    even_row = (row % 2 == 0)   # 1-indexed even == 0-indexed odd
    deltas = (
        [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, 0), (1, 1)] if even_row
        else [(-1, -1), (-1, 0), (0, -1), (0, 1), (1, -1), (1, 0)]
    )
    return [(row + dr, col + dc) for dr, dc in deltas]


def collect_ad_units_in_zone(
    all_units: list[UnitSnapshot],
    defender_country: str,
    tgt_global_row: int,
    tgt_global_col: int,
) -> list[UnitSnapshot]:
    """Return active AD units of ``defender_country`` covering the zone.

    Zone = the global hex + every theater hex that links back to it
    (per canonical theater↔global linkage table in map_config).
    """
    from engine.config.map_config import (
        global_hex_for_theater_cell, hex_distance, theater_for_global_hex,
    )
    zone_key = (tgt_global_row, tgt_global_col)
    linked_theater = theater_for_global_hex(tgt_global_row, tgt_global_col)
    out: list[UnitSnapshot] = []
    for u in all_units:
        if u.country_code != defender_country:
            continue
        if u.unit_type != "air_defense":
            continue
        if u.status == "destroyed":
            continue
        # Case A: AD on target global hex
        if (u.global_row, u.global_col) == zone_key:
            out.append(u); continue
        # Case B: AD on theater hex that maps to target zone
        if u.theater and u.theater_row is not None and u.theater_col is not None:
            mapped = global_hex_for_theater_cell(
                u.theater, u.theater_row, u.theater_col, defender_country,
            )
            if mapped == zone_key:
                out.append(u); continue
            # Case C safety-net: AD in the SAME linked theater
            if linked_theater and u.theater == linked_theater:
                out.append(u)
    return out


def collect_adjacent_naval_defenders(
    all_units: list[UnitSnapshot],
    defender_country: str,
    tgt_global_row: int,
    tgt_global_col: int,
) -> list[UnitSnapshot]:
    """Active enemy naval in the 6 hex-neighbors of target land hex."""
    neighbors = set(_hex_neighbors_v2(tgt_global_row, tgt_global_col))
    out: list[UnitSnapshot] = []
    for u in all_units:
        if u.country_code != defender_country:
            continue
        if u.unit_type != "naval":
            continue
        if u.status == "destroyed":
            continue
        if (u.global_row, u.global_col) in neighbors:
            out.append(u)
    return out


# ---------------------------------------------------------------------------
# GROUND ATTACK (unit-level, iterative RISK + naval-adjacent + trophies)
# ---------------------------------------------------------------------------

def _roll_dice(n: int) -> list[int]:
    rolls = [random.randint(1, 6) for _ in range(n)]
    rolls.sort(reverse=True)
    return rolls


def resolve_ground_attack_units(inp: UnitGroundAttackInput) -> UnitGroundAttackResult:
    """Iterative RISK ground combat, unit-level.

    Defenders in combat = ``defender_ground_units`` + ``adjacent_naval_defenders``.
    Continues until one side has 0 units remaining.

    Dice: attacker min(3, N_attackers_alive), defender min(2, N_defenders_alive).
    Highest-vs-highest; ties defender wins. Modifiers +1 to highest die on each
    side as applicable.

    Returns losses (unit_codes) + the trophies to capture if won + the
    attackers to move forward. Caller mutates state.
    """
    # Validate
    if not inp.attacker_units:
        return UnitGroundAttackResult(
            attacker_country=inp.attacker_country, defender_country=inp.defender_country,
            target_global_row=inp.target_global_row, target_global_col=inp.target_global_col,
            success=False, exchanges=0,
            narrative="No attackers — cannot resolve.",
        )

    defenders_pool = list(inp.defender_ground_units) + list(inp.adjacent_naval_defenders)

    # Unopposed occupation (no ground + no adjacent naval)
    if not defenders_pool:
        return UnitGroundAttackResult(
            attacker_country=inp.attacker_country, defender_country=inp.defender_country,
            target_global_row=inp.target_global_row, target_global_col=inp.target_global_col,
            success=True, exchanges=0,
            attackers_move_forward=[u.unit_code for u in inp.attacker_units],
            trophies_captured=[u.unit_code for u in inp.trophies_on_hex],
            narrative=(
                f"Unopposed occupation at ({inp.target_global_row},{inp.target_global_col}): "
                f"{len(inp.trophies_on_hex)} trophies captured."
            ),
        )

    attacker_bonus = 0
    if inp.air_superiority: attacker_bonus += 1
    if inp.amphibious_3to1: attacker_bonus += 1
    defender_bonus = 1 if inp.die_hard_terrain else 0

    attackers = list(inp.attacker_units)
    defenders = list(defenders_pool)
    att_losses: list[str] = []
    def_losses: list[str] = []
    all_a_rolls: list[int] = []
    all_d_rolls: list[int] = []
    exchanges = 0

    while attackers and defenders and exchanges < GROUND_COMBAT_MAX_EXCHANGES:
        exchanges += 1
        a_n = min(len(attackers), 3)
        d_n = min(len(defenders), 2)
        a_rolls = _roll_dice(a_n)
        d_rolls = _roll_dice(d_n)
        a_mod = a_rolls.copy()
        d_mod = d_rolls.copy()
        if a_mod and attacker_bonus:
            a_mod[0] = min(6, a_mod[0] + attacker_bonus); a_mod.sort(reverse=True)
        if d_mod and defender_bonus:
            d_mod[0] = min(6, d_mod[0] + defender_bonus); d_mod.sort(reverse=True)
        pairs = min(len(a_mod), len(d_mod))
        for i in range(pairs):
            if a_mod[i] > d_mod[i]:
                lost = defenders.pop()
                def_losses.append(lost.unit_code)
            else:
                lost = attackers.pop()
                att_losses.append(lost.unit_code)
        all_a_rolls.extend(a_rolls)
        all_d_rolls.extend(d_rolls)

    won = (len(defenders) == 0)
    move_forward: list[str] = []
    trophies: list[str] = []
    if won:
        move_forward = [u.unit_code for u in attackers]
        trophies = [u.unit_code for u in inp.trophies_on_hex]

    narrative = (
        f"Ground combat ({exchanges} exchanges): "
        f"attackers -{len(att_losses)}, defenders -{len(def_losses)}. "
        f"{'Attacker wins.' if won else 'Defender holds.'}"
    )
    if won and trophies:
        narrative += f" Trophies: {trophies}."

    return UnitGroundAttackResult(
        attacker_country=inp.attacker_country, defender_country=inp.defender_country,
        target_global_row=inp.target_global_row, target_global_col=inp.target_global_col,
        success=won, exchanges=exchanges,
        attacker_losses=att_losses, defender_losses=def_losses,
        attacker_rolls=all_a_rolls, defender_rolls=all_d_rolls,
        attackers_move_forward=move_forward, trophies_captured=trophies,
        narrative=narrative,
    )


# ---------------------------------------------------------------------------
# AIR STRIKE (unit-level, halving + range)
# ---------------------------------------------------------------------------

def resolve_air_strike_units(inp: UnitAirStrikeInput) -> UnitAirStrikeResult:
    """Tactical air strike, halving AD rule, range ≤ AIR_STRIKE_MAX_RANGE."""
    au = inp.attacker_unit
    # Range check
    distance = None
    if au.global_row is not None and au.global_col is not None:
        distance = hex_distance(
            au.global_row, au.global_col, inp.target_global_row, inp.target_global_col,
        )
        if distance > AIR_STRIKE_MAX_RANGE:
            return UnitAirStrikeResult(
                attacker_unit_code=au.unit_code,
                target_global_row=inp.target_global_row,
                target_global_col=inp.target_global_col,
                success=False, probability=0.0, roll=0.0, ad_present=False,
                out_of_range=True, distance=distance,
                narrative=(
                    f"{au.unit_code} OUT OF RANGE ({distance} hexes, "
                    f"max {AIR_STRIKE_MAX_RANGE})"
                ),
            )

    ad_present = any(ad.status != "destroyed" for ad in inp.ad_units_covering_zone)
    p = AIR_STRIKE_BASE_HIT_PROB_V2
    p += min(AIR_STRIKE_SUPERIORITY_CAP,
             AIR_STRIKE_SUPERIORITY_BONUS * inp.air_superiority_count)
    if ad_present:
        p *= AIR_STRIKE_AD_MULTIPLIER
    p = max(AIR_STRIKE_CLAMP_LOW, min(AIR_STRIKE_CLAMP_HIGH, p))

    roll = random.random()
    success = roll < p
    losses: list[str] = []
    if success and inp.defender_units:
        target = next(
            (u for u in inp.defender_units if u.unit_type != "air_defense"),
            inp.defender_units[0],
        )
        losses.append(target.unit_code)

    return UnitAirStrikeResult(
        attacker_unit_code=au.unit_code,
        target_global_row=inp.target_global_row,
        target_global_col=inp.target_global_col,
        success=success, probability=p, roll=roll, ad_present=ad_present,
        defender_losses=losses, distance=distance,
        narrative=(
            f"Air strike {au.unit_code}: AD={'yes' if ad_present else 'no'}, "
            f"p={p:.2f}, roll={roll:.2f} -> {'HIT' if success else 'MISS'}"
        ),
    )


# ---------------------------------------------------------------------------
# MISSILE STRIKE (unit-level, 80/30, disposable + Nuclear L1/L2)
# ---------------------------------------------------------------------------

def resolve_missile_strike_units(inp: UnitMissileStrikeInput) -> UnitMissileStrikeResult:
    """Per-missile strike resolution (unit-level).

    Accuracy (Marat 2026-04-06):
      * Base hit probability: 80% (missile accuracy)
      * T1_MIDRANGE attacks: halved to 30% if AD covers target zone
      * T2/T3 STRATEGIC attacks: no AD-in-zone halving (strategic missiles
        are intercepted by T3+ nations in the pre-flight salvo phase)

    Missile is CONSUMED on fire (``missile_consumed=True`` always).
    Caller must mark the missile unit destroyed.

    Nuclear damage (per hit, Marat 2026-04-06):
      * 50% of military units on target hex destroyed
      * 30% of target country's hex-share of GDP destroyed
        (= 0.30 / target_country_hex_count)
      * T3 salvo aggregate effects (global stab + leader roll) applied
        by caller via resolve_nuclear_salvo_aggregate(), NOT here.
    """
    ad_present = any(ad.status != "destroyed" for ad in inp.ad_units_covering_zone)
    if inp.attack_tier == StrategicAttackTier.T1_MIDRANGE:
        p = MISSILE_AD_HIT_PROB_V2 if ad_present else MISSILE_BASE_HIT_PROB_V2
    else:
        # T2/T3 strategic: no AD-halving at target zone
        p = MISSILE_BASE_HIT_PROB_V2
    roll = random.random()
    success = roll < p

    result = UnitMissileStrikeResult(
        missile_unit_code=inp.missile_unit.unit_code,
        target_global_row=inp.target_global_row,
        target_global_col=inp.target_global_col,
        warhead_type=inp.warhead_type.value,
        success=success, probability=p, roll=roll, ad_present=ad_present,
        missile_consumed=True,
        narrative="",
    )

    if not success:
        result.narrative = (
            f"Missile {inp.missile_unit.unit_code} -> "
            f"({inp.target_global_row},{inp.target_global_col}): "
            f"AD={'yes' if ad_present else 'no'}, p={p:.2f}, roll={roll:.2f} MISS"
        )
        return result

    # --- Apply damage by warhead type (Marat 2026-04-06 simplified) ---
    if inp.warhead_type == WarheadType.CONVENTIONAL:
        # Destroy one defender unit (prefer non-AD, non-own)
        target = None
        for u in inp.defender_units:
            if u.country_code == inp.missile_unit.country_code:
                continue
            if u.unit_type != "air_defense":
                target = u; break
        if target is None and inp.defender_units:
            target = inp.defender_units[0]
        if target:
            result.defender_losses.append(target.unit_code)
        result.narrative = (
            f"Missile {inp.missile_unit.unit_code} HIT conventional "
            f"({inp.attack_tier.value}): 1 unit destroyed at "
            f"({inp.target_global_row},{inp.target_global_col})."
        )
    else:
        # NUCLEAR warhead — uniform damage profile (simplified binary model)
        # Marat 2026-04-06:
        #   * 50% of ALL military units on target hex destroyed (incl. own)
        #   * 30% × (1/country_hex_count) of target country GDP
        #   * T3 salvo aggregate (global stab, leader roll) is applied
        #     externally by resolve_nuclear_salvo_aggregate().
        result.nuclear_used = True
        result.nuclear_level = 1   # kept for back-compat; no longer meaningful
        result.target_country = inp.target_country
        military = [u for u in inp.defender_units
                    if u.unit_type in ("ground", "naval", "tactical_air",
                                        "strategic_missile", "air_defense")]
        kill_count = len(military) // 2
        if military and kill_count == 0:
            kill_count = 1   # at least 1 destroyed if any present
        kill_list = [u.unit_code for u in military[:kill_count]]
        result.defender_losses = kill_list
        result.military_destroyed_pct = (len(kill_list) / len(military)) if military else 0.0
        hex_count = max(1, inp.target_country_hex_count)
        result.economic_damage_pct = 0.30 / hex_count
        result.narrative = (
            f"NUCLEAR detonation ({inp.attack_tier.value}) at "
            f"({inp.target_global_row},{inp.target_global_col}): "
            f"{len(kill_list)}/{len(military)} military destroyed, "
            f"economic loss {result.economic_damage_pct*100:.1f}% of "
            f"{inp.target_country or '?'} GDP."
        )

    return result


# ---------------------------------------------------------------------------
# T3 NUCLEAR SALVO AGGREGATE (applied ONCE per salvo if ≥1 nuclear hit)
# ---------------------------------------------------------------------------

class NuclearSalvoAggregateInput(BaseModel):
    """Inputs for the once-per-T3-salvo aggregate effects."""
    target_country: str               # country with the most nuclear hits
    missiles_launched: int            # must be >= 3 for T3 salvo to be valid
    nuclear_hits_landed: int          # successful nuclear hits across salvo


class NuclearSalvoAggregateResult(BaseModel):
    target_country: str
    valid: bool                       # False if fewer than 3 missiles launched
    global_stability_loss: float = 0.0
    target_stability_loss: float = 0.0
    leader_killed: bool = False
    leader_roll: int = 0              # 1-6 d6 result; 1 = killed
    narrative: str = ""


def resolve_nuclear_salvo_aggregate(inp: NuclearSalvoAggregateInput) -> NuclearSalvoAggregateResult:
    """Apply the once-per-T3-salvo effects: global stab, target stab, leader roll.

    Requires ≥3 missiles launched in the salvo. If fewer, marked invalid.
    No aggregate effects applied if no nuclear hits landed (all missiles
    intercepted or missed their targets).
    """
    if inp.missiles_launched < 3:
        return NuclearSalvoAggregateResult(
            target_country=inp.target_country, valid=False,
            narrative=(
                f"T3 salvo INVALID — only {inp.missiles_launched} "
                f"missile(s) launched (min 3 required)."
            ),
        )
    if inp.nuclear_hits_landed == 0:
        return NuclearSalvoAggregateResult(
            target_country=inp.target_country, valid=True,
            narrative="T3 salvo: all missiles intercepted/missed — no aggregate effects.",
        )
    roll = random.randint(1, 6)
    killed = (roll == 1)   # 1/6 chance
    return NuclearSalvoAggregateResult(
        target_country=inp.target_country, valid=True,
        global_stability_loss=1.5,
        target_stability_loss=2.5,
        leader_killed=killed, leader_roll=roll,
        narrative=(
            f"T3 STRATEGIC aftermath vs {inp.target_country}: "
            f"global stability -1.5, target stability -2.5, "
            f"leader roll={roll} -> {'KILLED' if killed else 'survives'}."
        ),
    )


# ---------------------------------------------------------------------------
# T3+ NUCLEAR INTERCEPTION (salvo-level, all T3+ nations roll)
# ---------------------------------------------------------------------------

class NuclearSalvoInterceptionInput(BaseModel):
    """Interception attempt against an incoming T2/T3 strategic salvo.

    For each T3+ nation (except launcher), each active AD unit they own
    grants 1 interception roll at 25% success. Each success destroys
    one missile from the salvo.
    """
    launcher_country: str
    missiles_in_salvo: int
    t3_nations: list[dict]   # [{country_code, nuclear_level, ad_unit_count}, ...]


class InterceptorReport(BaseModel):
    country: str
    ad_units: int
    rolls: list[float] = Field(default_factory=list)
    intercepts_made: int = 0


class NuclearSalvoInterceptionResult(BaseModel):
    launcher_country: str
    missiles_in_salvo: int
    missiles_intercepted: int
    missiles_surviving: int
    interceptor_reports: list[InterceptorReport] = Field(default_factory=list)
    narrative: str = ""


NUCLEAR_INTERCEPTION_PROB: float = 0.25   # Marat 2026-04-06 calibration


def resolve_nuclear_salvo_interception(
    inp: NuclearSalvoInterceptionInput,
) -> NuclearSalvoInterceptionResult:
    """Run all T3+ nations' interception attempts against an incoming salvo.

    Each T3+ nation (≠ launcher) rolls 1 d(25%) per active AD unit.
    Each success cancels one missile. Missiles cancelled are capped at
    the salvo size.

    Caller must ensure ``t3_nations`` excludes the launcher and only
    contains countries with nuclear_level >= 3.
    """
    total_intercepts = 0
    reports: list[InterceptorReport] = []
    for nation in inp.t3_nations:
        cc = nation.get("country_code", "?")
        if cc == inp.launcher_country:
            continue
        level = int(nation.get("nuclear_level", 0))
        if level < 3:
            continue
        ad = int(nation.get("ad_unit_count", 0))
        if ad <= 0:
            reports.append(InterceptorReport(country=cc, ad_units=0))
            continue
        rolls: list[float] = []
        intercepts = 0
        for _ in range(ad):
            r = random.random()
            rolls.append(r)
            if r < NUCLEAR_INTERCEPTION_PROB:
                intercepts += 1
        total_intercepts += intercepts
        reports.append(InterceptorReport(
            country=cc, ad_units=ad, rolls=rolls, intercepts_made=intercepts,
        ))
    missiles_intercepted = min(total_intercepts, inp.missiles_in_salvo)
    surviving = inp.missiles_in_salvo - missiles_intercepted
    return NuclearSalvoInterceptionResult(
        launcher_country=inp.launcher_country,
        missiles_in_salvo=inp.missiles_in_salvo,
        missiles_intercepted=missiles_intercepted,
        missiles_surviving=surviving,
        interceptor_reports=reports,
        narrative=(
            f"T3+ interception vs {inp.launcher_country}: "
            f"{missiles_intercepted}/{inp.missiles_in_salvo} missiles "
            f"intercepted by {sum(1 for r in reports if r.intercepts_made > 0)} nation(s)."
        ),
    )


# ---------------------------------------------------------------------------
# NAVAL COMBAT (unit-level)
# ---------------------------------------------------------------------------

def resolve_naval_combat_units(inp: UnitNavalCombatInput) -> UnitNavalCombatResult:
    """Ship-vs-ship iterative combat (same iterative RISK as ground)."""
    if not inp.attacker_fleet or not inp.defender_fleet:
        return UnitNavalCombatResult(
            attacker_country=inp.attacker_country, defender_country=inp.defender_country,
            sea_global_row=inp.sea_global_row, sea_global_col=inp.sea_global_col,
            exchanges=0, success=False,
            narrative="No combat: one side has zero ships.",
        )
    attackers = list(inp.attacker_fleet)
    defenders = list(inp.defender_fleet)
    att_losses: list[str] = []
    def_losses: list[str] = []
    all_a_rolls: list[int] = []
    all_d_rolls: list[int] = []
    exchanges = 0
    # Advantage bonus: larger fleet +1 on highest die, cap ±3
    advantage = len(attackers) - len(defenders)
    adv_bonus = max(-3, min(3, advantage))

    while attackers and defenders and exchanges < GROUND_COMBAT_MAX_EXCHANGES:
        exchanges += 1
        a_n = min(len(attackers), 3)
        d_n = min(len(defenders), 3)
        a_rolls = _roll_dice(a_n)
        d_rolls = _roll_dice(d_n)
        a_mod = a_rolls.copy(); d_mod = d_rolls.copy()
        if adv_bonus > 0 and a_mod:
            a_mod[0] = min(6, a_mod[0] + adv_bonus); a_mod.sort(reverse=True)
        elif adv_bonus < 0 and d_mod:
            d_mod[0] = min(6, d_mod[0] + abs(adv_bonus)); d_mod.sort(reverse=True)
        pairs = min(len(a_mod), len(d_mod))
        for i in range(pairs):
            if a_mod[i] > d_mod[i]:
                lost = defenders.pop()
                def_losses.append(lost.unit_code)
            else:
                lost = attackers.pop()
                att_losses.append(lost.unit_code)
        all_a_rolls.extend(a_rolls)
        all_d_rolls.extend(d_rolls)

    won = (len(defenders) == 0)
    return UnitNavalCombatResult(
        attacker_country=inp.attacker_country, defender_country=inp.defender_country,
        sea_global_row=inp.sea_global_row, sea_global_col=inp.sea_global_col,
        exchanges=exchanges, success=won,
        attacker_losses=att_losses, defender_losses=def_losses,
        attacker_rolls=all_a_rolls, defender_rolls=all_d_rolls,
        narrative=(
            f"Naval combat ({exchanges} exchanges): "
            f"attackers -{len(att_losses)}, defenders -{len(def_losses)}. "
            f"{'Attacker wins.' if won else 'Defender holds.'}"
        ),
    )


# ---------------------------------------------------------------------------
# NAVAL BOMBARDMENT (unit-level, 10% per shot per CON_C2)
# ---------------------------------------------------------------------------

NAVAL_BOMBARDMENT_HIT_PROB: float = 0.10


def resolve_naval_bombardment_units(inp: UnitNavalBombardmentInput) -> UnitNavalBombardmentResult:
    """Each naval unit bombards once per round at 10% chance to kill one
    random ground unit on the target hex.

    (No AD halving for bombardment per current design — decision deferred.)
    """
    rolls: list[float] = []
    losses: list[str] = []
    targets = list(inp.defender_ground_units)
    for _ in inp.naval_units:
        if not targets:
            break
        r = random.random()
        rolls.append(r)
        if r < NAVAL_BOMBARDMENT_HIT_PROB:
            # Destroy one random ground unit
            idx = random.randint(0, len(targets) - 1)
            killed = targets.pop(idx)
            losses.append(killed.unit_code)
    return UnitNavalBombardmentResult(
        attacker_country=inp.attacker_country, defender_country=inp.defender_country,
        target_global_row=inp.target_global_row,
        target_global_col=inp.target_global_col,
        shots_fired=len(inp.naval_units),
        defender_losses=losses, rolls=rolls,
        narrative=(
            f"Naval bombardment: {len(inp.naval_units)} shots, "
            f"{len(losses)} units destroyed."
        ),
    )
