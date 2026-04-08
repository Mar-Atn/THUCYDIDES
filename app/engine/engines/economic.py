"""TTT Economic Engine — BUILD port from SEED world_model_engine.py.

Faithful port of ALL economic formulas from the SEED deterministic pass.
Pure functions: no DB calls, no side effects, stateless.
Receives game state as input, returns EconomicResult as output.

Processing sequence (CHAINED, not parallel):
1.  Oil price (global, everything depends on this)
2.  GDP growth per country (additive factor model + crisis multiplier)
3.  Revenue per country (from GDP)
4.  Budget execution (mandatory costs, deficit, money printing)
5.  Military production costs and maintenance
6.  Technology R&D costs
7.  Inflation update
8.  Debt service update
9.  Economic state transitions (crisis ladder)
10. Momentum (confidence variable)
11. Contagion (crisis spreads to trade partners)
12. Sanctions impact (S-curve model)
13. Tariff impact
14. Dollar credibility

Source: 2 SEED/D_ENGINES/world_model_engine.py (v2 + v3 calibration fixes)
"""

from __future__ import annotations

import math
import random
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# CONFIGURABLE CONSTANTS (all from SEED, do not change without calibration)
# ---------------------------------------------------------------------------

# Oil (Cal-10: Marat review)
OIL_BASE_PRICE: float = 80.0
OIL_PRICE_FLOOR: float = 15.0  # Cal-10: was $30
OIL_SOFT_CAP_THRESHOLD: float = 200.0
OIL_SOFT_CAP_SCALE: float = 50.0
OIL_SOFT_CAP_DECAY: float = 100.0
OIL_INERTIA_PREVIOUS: float = 0.3  # Cal-10: was 0.4 (more responsive)
OIL_INERTIA_FORMULA: float = 0.7  # Cal-10: was 0.6
OIL_DEMAND_DESTRUCTION_THRESHOLD: float = 100.0  # Cal-10: was $150
OIL_DEMAND_DESTRUCTION_ROUNDS: int = 3  # rounds above threshold before destruction kicks in
OIL_DEMAND_DESTRUCTION_MIN: float = 0.96  # -4% at $100
OIL_DEMAND_DESTRUCTION_MAX: float = 0.92  # -8% at $150+
OIL_SUPPLY_DEMAND_EXPONENT: float = 2.5  # Cal-10c: Marat wants ~1.5× amplitude on all scenarios
# Chokepoint blockade effects on production (partial/full)
OIL_BLOCKADE_PARTIAL: float = 0.25  # 25% production loss
OIL_BLOCKADE_FULL: float = 0.50  # 50% production loss
# Gulf Gate affects: solaria, mirage (and persia if blocked by non-Persia)
# Caribe Passage affects: caribe
GULF_GATE_PRODUCERS: set = {"solaria", "mirage"}
CARIBE_PASSAGE_PRODUCERS: set = {"caribe"}

# OPEC production multipliers
OPEC_PRODUCTION_MULTIPLIER: dict[str, float] = {
    "min": 0.70, "low": 0.85, "normal": 1.00, "high": 1.15, "max": 1.30,
}

# Crisis states
CRISIS_STATES: tuple[str, ...] = ("normal", "stressed", "crisis", "collapse")

CRISIS_GDP_MULTIPLIER: dict[str, float] = {
    "normal": 1.0,
    "stressed": 0.85,
    "crisis": 0.5,
    "collapse": 0.2,
}

# FIX 9: Crisis amplifier for negative growth (different from multiplier)
CRISIS_NEGATIVE_AMPLIFIER: dict[str, float] = {
    "normal": 1.0,
    "stressed": 1.2,
    "crisis": 1.3,
    "collapse": 2.0,
}

CRISIS_STABILITY_PENALTY: dict[str, float] = {
    "normal": 0.0,
    "stressed": -0.10,
    "crisis": -0.30,
    "collapse": -0.50,
}

# Major economy threshold for contagion
MAJOR_ECONOMY_THRESHOLD: float = 30.0

# Tech boost to growth rate (Cal-3 v3)
# Cal-8: L3=1%, L4=probabilistic 1.5-3.5% (rolled once when achieved)
AI_LEVEL_TECH_FACTOR: dict[int, float] = {0: 0.0, 1: 0.0, 2: 0.003, 3: 0.010, 4: 0.025}  # L4 is avg; actual is rolled

# Sanctions
# Cal-11: Reshaped S-curve. ~40% at 0.50 coverage (current Sarmatia coalition)
# ~80% at 0.80 (Cathay joins), ~95% at 0.95 (full world)
SANCTIONS_S_CURVE: list[tuple[float, float]] = [
    (0.0, 0.0), (0.2, 0.05), (0.4, 0.25),
    (0.5, 0.40), (0.7, 0.70), (0.8, 0.80),
    (0.9, 0.90), (1.0, 1.0),
]
SANCTIONS_MAX_DAMAGE: float = 0.87  # Cal-11b: 1.5× from 0.58. Full world: ~18% Sarmatia, ~45% tech economies
SANCTIONS_ADAPTATION_RATE: float = 0.10  # 10% recovery per round toward adaptation
SANCTIONS_PERMANENT_FRACTION: float = 0.60  # 60% of damage is permanent, 40% recoverable
SANCTIONS_DIMINISHING_THRESHOLD: int = 4  # rounds before diminishing returns
SANCTIONS_DIMINISHING_FACTOR: float = 0.60  # Cal-2 v3: 40% reduction after threshold

# Budget
MONEY_PRINTING_INFLATION_MULTIPLIER: float = 60.0  # F57: was 80, reduced 25%
MAINTENANCE_MULTIPLIER: float = 3.0  # F51: creates budget tension
DEFICIT_TO_DEBT_RATE: float = 0.15
SOCIAL_MANDATORY_FRACTION: float = 0.70
SOCIAL_DISCRETIONARY_FRACTION: float = 0.30

# Inflation
INFLATION_EXCESS_DECAY: float = 0.85  # 15% decay per round on excess
INFLATION_FLOOR: float = 0.0
INFLATION_CEILING: float = 500.0

# GDP
GDP_FLOOR: float = 0.5

# Momentum
MOMENTUM_FLOOR: float = -5.0
MOMENTUM_CEILING: float = 5.0
MOMENTUM_BOOST_CAP: float = 0.3

# Dollar credibility
DOLLAR_CREDIBILITY_EROSION_PER_COIN: float = 2.0
DOLLAR_CREDIBILITY_RECOVERY: float = 1.0
DOLLAR_CREDIBILITY_FLOOR: float = 20.0
DOLLAR_CREDIBILITY_CEILING: float = 100.0

# Market indexes — 3 regional indexes replacing per-country index
MARKET_INDEX_BASELINE: float = 100.0  # starting value (game start = 100)
MARKET_INDEX_FLOOR: float = 0.0
MARKET_INDEX_CEILING: float = 200.0

# Index composition: country -> weight in each index
# Wall Street: US-centric, global trade exposure
WALL_STREET_COMPONENTS: dict[str, float] = {
    "columbia": 0.50, "cathay": 0.15, "teutonia": 0.10,
    "yamato": 0.10, "albion": 0.10, "hanguk": 0.05,
}
# Europa: EU bloc
EUROPA_COMPONENTS: dict[str, float] = {
    "teutonia": 0.30, "gallia": 0.25, "freeland": 0.15,
    "albion": 0.15, "nordostan": 0.10, "levantia": 0.05,
}
# Dragon: Cathay-centric, Asian trade
DRAGON_COMPONENTS: dict[str, float] = {
    "cathay": 0.50, "hanguk": 0.15, "yamato": 0.15,
    "bharata": 0.10, "formosa": 0.10,
}

# Which index each country primarily reads for stability
COUNTRY_PRIMARY_INDEX: dict[str, str] = {
    "columbia": "wall_street", "albion": "wall_street", "yamato": "wall_street",
    "hanguk": "wall_street", "formosa": "dragon",
    "teutonia": "europa", "gallia": "europa", "freeland": "europa",
    "nordostan": "europa", "levantia": "europa", "helvetia": "europa",
    "cathay": "dragon", "bharata": "dragon",
    # Countries with no primary index (minor exposure) — no direct market stress
    "sarmatia": "europa", "persia": "dragon", "solaria": "dragon",
    "mirage": "europa", "caribe": "wall_street", "choson": "dragon",
    "ruthenia": "europa",
}

# Thresholds for stability impact
MARKET_INDEX_STRESS_THRESHOLD: float = 70.0   # below = stress
MARKET_INDEX_CRISIS_THRESHOLD: float = 40.0   # below = crisis

# Production tiers
PRODUCTION_TIER_COST: dict[str, float] = {"normal": 1.0, "accelerated": 2.0, "maximum": 4.0}
PRODUCTION_TIER_OUTPUT: dict[str, float] = {"normal": 1.0, "accelerated": 2.0, "maximum": 3.0}

# R&D
RD_MULTIPLIER: float = 0.8
NUCLEAR_RD_THRESHOLDS: dict[int, float] = {0: 0.60, 1: 0.80, 2: 1.00}
AI_RD_THRESHOLDS: dict[int, float] = {0: 0.20, 1: 0.40, 2: 0.60, 3: 1.00}

# Bilateral GDP dependency pairs (FIX 1)
BILATERAL_PAIRS: dict[tuple[str, str], float] = {
    ("columbia", "cathay"): 0.15,
    ("cathay", "columbia"): 0.12,
    ("teutonia", "cathay"): 0.10,
    ("cathay", "teutonia"): 0.08,
    ("yamato", "cathay"): 0.08,
    ("hanguk", "cathay"): 0.10,
}

# Chokepoints (trade/oil impact fractions)
CHOKEPOINTS: dict[str, dict[str, Any]] = {
    "hormuz": {"zone": "cp_gulf_gate", "oil_impact": 0.35, "trade_impact": 0.10},
    "malacca": {"zone": "w(15,9)", "trade_impact": 0.30, "oil_impact": 0.05},
    "taiwan_strait": {"zone": "w(17,4)", "tech_impact": 0.50, "trade_impact": 0.15},
    "suez": {"zone": "w(10,7)", "trade_impact": 0.15, "oil_impact": 0.05},
    "bosphorus": {"zone": "w(10,3)", "trade_impact": 0.08, "oil_impact": 0.0},
    "giuk": {"zone": "w(6,1)", "trade_impact": 0.02},
    "caribbean": {"zone": "w(4,8)", "trade_impact": 0.05, "oil_impact": 0.02},
    "south_china_sea": {"zone": "w(16,7)", "trade_impact": 0.20, "oil_impact": 0.03},
    "gulf_gate_ground": {"zone": "cp_gulf_gate", "oil_impact": 0.60, "ground_blockade": True},
}

UNIT_TYPES: list[str] = ["ground", "naval", "tactical_air", "strategic_missile", "air_defense"]


# ---------------------------------------------------------------------------
# RESULT MODELS
# ---------------------------------------------------------------------------

class OilPriceResult(BaseModel):
    """Global oil price computation result."""
    price: float
    supply: float
    demand: float
    disruption: float
    war_premium: float
    formula_price: float
    previous_price: float
    gulf_gate_blocked: bool
    formosa_blocked: bool


class GdpResult(BaseModel):
    """Per-country GDP growth result."""
    old_gdp: float
    new_gdp: float
    growth_pct: float
    base_growth: float
    tariff_hit: float
    sanctions_hit: float
    oil_shock: float
    semi_hit: float
    war_hit: float
    tech_boost: float
    momentum_effect: float
    blockade_hit: float
    bilateral_drag: float
    crisis_multiplier: float
    economic_state: str


class RevenueResult(BaseModel):
    """Per-country revenue breakdown."""
    total: float
    base_revenue: float
    oil_revenue: float
    debt_cost: float
    inflation_erosion: float
    war_damage_cost: float
    sanctions_cost: float


class BudgetResult(BaseModel):
    """Per-country budget execution result."""
    revenue: float
    mandatory: float
    maintenance: float
    social_baseline_cost: float
    discretionary: float
    social_spending: float
    military_budget: float
    tech_budget: float
    deficit: float
    money_printed: float
    new_treasury: float


class MilitaryProductionResult(BaseModel):
    """Per-country military production result."""
    produced: dict[str, int] = Field(default_factory=dict)


class TechResult(BaseModel):
    """Per-country technology advancement result."""
    nuclear_levelup: bool = False
    ai_levelup: bool = False
    ai_l4_bonus: bool | None = None


class SanctionsResult(BaseModel):
    """Per-country sanctions impact."""
    damage: float
    costs: dict[str, float] = Field(default_factory=dict)


class TariffResult(BaseModel):
    """Per-country tariff impact."""
    cost_as_imposer: float
    revenue_as_imposer: float
    cost_as_target: float
    net_gdp_cost: float


class EconomicStateResult(BaseModel):
    """Per-country economic state transition."""
    old_state: str
    new_state: str
    stress_triggers: int
    crisis_triggers: int
    crisis_rounds: int
    recovery_rounds: int


class MomentumResult(BaseModel):
    """Per-country momentum update."""
    old_momentum: float
    new_momentum: float
    boost: float
    crash: float


class ContagionHit(BaseModel):
    """Single contagion event."""
    source: str
    gdp_hit_pct: float
    momentum_hit: float


class SingleIndexResult(BaseModel):
    """One regional market index."""
    name: str
    old_value: float
    new_value: float
    components: dict[str, float] = Field(default_factory=dict)  # country -> health score


class MarketIndexesResult(BaseModel):
    """All 3 regional market indexes."""
    wall_street: SingleIndexResult
    europa: SingleIndexResult
    dragon: SingleIndexResult


class CountryEconomicResult(BaseModel):
    """Full economic result for a single country."""
    gdp: GdpResult
    revenue: RevenueResult
    budget: BudgetResult
    military_production: MilitaryProductionResult
    tech: TechResult
    inflation: float
    debt_burden: float
    sanctions: SanctionsResult
    tariffs: TariffResult
    economic_state: EconomicStateResult
    momentum: MomentumResult
    contagion: list[ContagionHit] = Field(default_factory=list)


class EconomicResult(BaseModel):
    """Top-level economic engine output."""
    oil_price: OilPriceResult
    countries: dict[str, CountryEconomicResult] = Field(default_factory=dict)
    dollar_credibility: float
    oil_above_150_rounds: int
    market_indexes: MarketIndexesResult | None = None
    log: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# PURE HELPER FUNCTIONS
# ---------------------------------------------------------------------------

def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value between min and max."""
    return max(min_val, min(max_val, value))


def interpolate_s_curve(x: float, curve: list[tuple[float, float]]) -> float:
    """Linear interpolation on a piecewise S-curve."""
    x = clamp(x, curve[0][0], curve[-1][0])
    for i in range(len(curve) - 1):
        x0, y0 = curve[i]
        x1, y1 = curve[i + 1]
        if x0 <= x <= x1:
            t = (x - x0) / (x1 - x0) if x1 != x0 else 0.0
            return y0 + t * (y1 - y0)
    return curve[-1][1]


def derive_trade_weights(countries: dict[str, dict]) -> dict[str, dict[str, float]]:
    """Derive approximate bilateral trade weights from GDP and sector profiles.

    Ported exactly from SEED world_state.py.
    """
    ids = list(countries.keys())
    raw: dict[str, dict[str, float]] = {c: {} for c in ids}
    for a in ids:
        ca = countries[a]
        gdp_a = ca["economic"]["gdp"]
        sec_a = ca["economic"]["sectors"]
        for b in ids:
            if a == b:
                continue
            cb = countries[b]
            gdp_b = cb["economic"]["gdp"]
            sec_b = cb["economic"]["sectors"]
            comp = (
                sec_a.get("industry", 0) * sec_b.get("resources", 0)
                + sec_a.get("resources", 0) * sec_b.get("industry", 0)
                + sec_a.get("technology", 0) * sec_b.get("services", 0)
                + sec_a.get("services", 0) * sec_b.get("technology", 0)
            )
            comp = max(comp, 1.0)
            raw[a][b] = gdp_a * gdp_b * comp
    weights: dict[str, dict[str, float]] = {}
    for a in ids:
        total = sum(raw[a].values())
        if total == 0:
            weights[a] = {b: 0.0 for b in ids if b != a}
        else:
            weights[a] = {b: raw[a][b] / total for b in ids if b != a}
    return weights


# ---------------------------------------------------------------------------
# INTERNAL QUERY HELPERS (stateless, operate on passed-in state dicts)
# ---------------------------------------------------------------------------

def _is_chokepoint_blocked(active_blockades: dict, chokepoint_key: str) -> bool:
    """Check if a chokepoint is in the active blockades dict."""
    return chokepoint_key in active_blockades


def _get_gulf_gate_level(
    chokepoint_status: dict[str, str],
    active_blockades: dict,
) -> str:
    """Determine Gulf Gate blockade level: 'none', 'partial', or 'full'.

    Checks both active_blockades dict and chokepoint_status for any Gulf Gate
    or Hormuz related keys.
    """
    level = "none"
    # Check active_blockades (multiple possible key names)
    for key in ("gulf_gate", "gulf_gate_ground", "hormuz", "cp_gulf_gate"):
        if key in active_blockades:
            bl = active_blockades[key]
            bl_status = bl.get("status", bl.get("level", "full")) if isinstance(bl, dict) else "full"
            if bl_status in ("blocked", "full"):
                return "full"
            if bl_status in ("contested", "partial"):
                level = "partial"
    # Check chokepoint_status
    for cp_name in ("hormuz", "gulf_gate_ground", "cp_gulf_gate"):
        status = chokepoint_status.get(cp_name, "")
        if status == "blocked":
            return "full"
        if status == "contested":
            level = "partial"
    return level


def _is_formosa_blocked(
    chokepoint_status: dict[str, str],
    active_blockades: dict,
    formosa_blockade: bool,
) -> bool:
    """Check if Formosa Strait is blocked."""
    if _is_chokepoint_blocked(active_blockades, "formosa_strait"):
        return True
    if chokepoint_status.get("taiwan_strait") == "blocked":
        return True
    if formosa_blockade:
        return True
    return False


def _is_formosa_disrupted(
    wars: list[dict],
    chokepoint_status: dict[str, str],
    active_blockades: dict,
    formosa_blockade: bool,
) -> bool:
    """Check if Formosa semiconductor production is disrupted."""
    for war in wars:
        if "formosa" in (war.get("attacker"), war.get("defender")):
            return True
    return _is_formosa_blocked(chokepoint_status, active_blockades, formosa_blockade)


def _get_sanctions_on(sanctions: dict[str, dict], target_country: str) -> int:
    """Get maximum sanctions level imposed on target."""
    max_level = 0
    for _sanctioner, targets in sanctions.items():
        level = targets.get(target_country, 0)
        if level > max_level:
            max_level = level
    return max_level


def _count_war_zones(wars: list[dict], country_id: str) -> int:
    """Count occupied zones in wars involving this country."""
    count = 0
    for w in wars:
        if w.get("attacker") == country_id or w.get("defender") == country_id:
            count += len(w.get("occupied_zones", []))
    return count


def _get_infra_damage(wars: list[dict], country_id: str) -> float:
    """Infrastructure damage: defenders lose 5% per occupied zone, capped at 1.0."""
    damage = 0.0
    for w in wars:
        if w.get("defender") == country_id:
            damage += len(w.get("occupied_zones", [])) * 0.05
    return min(damage, 1.0)


def _get_blockade_fraction(
    country_id: str,
    country_eco: dict,
    chokepoint_status: dict[str, str],
) -> float:
    """Blockade fraction for direct GDP impact via trade disruption.

    NOTE (v2 fix): Gulf Gate / Hormuz are EXCLUDED here because their
    economic impact is already fully captured through the oil price channel.
    Only non-oil chokepoints are counted.
    """
    frac = 0.0
    for cp_name, status in chokepoint_status.items():
        if status != "blocked":
            continue
        # Skip Gulf Gate / Hormuz -- impact comes through oil price
        if cp_name in ("hormuz", "gulf_gate_ground"):
            continue
        cp = CHOKEPOINTS.get(cp_name, {})
        impact = cp.get("trade_impact", cp.get("oil_impact", 0.1))
        if cp_name == "malacca" and country_id == "cathay":
            frac += impact * 2.0
        elif cp_name == "taiwan_strait":
            dep = country_eco.get("formosa_dependency", 0)
            frac += cp.get("tech_impact", 0.5) * dep
        else:
            frac += impact * 0.3
    return min(frac, 1.0)


def _calc_rare_earth_impact(
    country_id: str,
    rare_earth_restrictions: dict[str, int],
) -> float:
    """Rare earth restrictions slow R&D. Each level = -15%, floor 40%."""
    if country_id in rare_earth_restrictions:
        restriction_level = rare_earth_restrictions[country_id]
        rd_penalty = 1.0 - (restriction_level * 0.15)
        return max(0.4, rd_penalty)
    return 1.0


def _is_country_at_war(wars: list[dict], country_id: str) -> bool:
    """Check if country is involved in any war."""
    return any(
        w.get("attacker") == country_id
        or w.get("defender") == country_id
        or country_id in w.get("allies", {}).get("attacker", [])
        or country_id in w.get("allies", {}).get("defender", [])
        for w in wars
    )


def _calc_bilateral_dependency(
    country_id: str,
    countries: dict[str, dict],
) -> float:
    """Major trading partners affect each other's GDP. Returns additive drag on growth rate."""
    total_drag = 0.0
    for (a, b), weight in BILATERAL_PAIRS.items():
        if a == country_id:
            partner = countries.get(b, {})
            partner_growth = partner.get("economic", {}).get("gdp_growth_rate", 0)
            if partner_growth < 0:
                total_drag += partner_growth * weight  # negative * positive = negative
    return total_drag  # additive to growth rate


# ---------------------------------------------------------------------------
# STEP FUNCTIONS (pure, stateless — operate on mutable state dicts)
# ---------------------------------------------------------------------------

def calc_oil_price(
    countries: dict[str, dict],
    opec_production: dict[str, str],
    chokepoint_status: dict[str, str],
    active_blockades: dict,
    formosa_blockade: bool,
    wars: list[dict],
    previous_oil_price: float,
    oil_above_150_rounds: int,
    sanctions: dict[str, dict],
    log: list[str],
) -> tuple[OilPriceResult, int]:
    """Oil price with supply/demand/disruption/war factors.

    Returns (OilPriceResult, updated_oil_above_150_rounds).
    """
    base_price = OIL_BASE_PRICE

    # --- SUPPLY SIDE (Cal-10: mbpd-based production shares for OPEC + blockade) ---
    total_production = 0.0
    producer_output: dict[str, float] = {}
    for cid, c in countries.items():
        eco = c.get("economic", {})
        mbpd = eco.get("oil_production_mbpd", 0.0)
        if eco.get("oil_producer") and mbpd > 0:
            producer_output[cid] = mbpd
            total_production += mbpd

    # OPEC production decisions (weighted by actual production share)
    # OPEC controls ~40-50% of global oil — their decisions move markets significantly
    supply = 1.0
    if total_production > 0:
        for member, decision in opec_production.items():
            if member in producer_output:
                share = producer_output[member] / total_production
                multiplier = OPEC_PRODUCTION_MULTIPLIER.get(decision, 1.0)
                # 2× amplifier: OPEC decisions have outsized market impact (cartel leverage)
                supply += (multiplier - 1.0) * share * 2.0

    # Sanctions on oil producers reduce supply (weighted)
    if total_production > 0:
        for producer in producer_output:
            sanc_level = _get_sanctions_on(sanctions, producer)
            if sanc_level >= 2:
                share = producer_output[producer] / total_production
                supply -= 0.10 * share  # L2+ sanctions reduce that producer's output by 10%

    # --- CHOKEPOINT BLOCKADES → ACTUAL SUPPLY REDUCTION (Cal-10) ---
    gulf_gate_level = _get_gulf_gate_level(chokepoint_status, active_blockades)

    if gulf_gate_level != "none" and total_production > 0:
        blockade_pct = OIL_BLOCKADE_FULL if gulf_gate_level == "full" else OIL_BLOCKADE_PARTIAL
        for affected in GULF_GATE_PRODUCERS:
            if affected in producer_output:
                share = producer_output[affected] / total_production
                supply -= blockade_pct * share
        # Persia also loses if blocked by non-Persia
        blocker = active_blockades.get("cp_gulf_gate", {}).get("controller", "")
        if blocker and blocker != "persia" and "persia" in producer_output:
            share = producer_output["persia"] / total_production
            supply -= blockade_pct * share

    # Caribe Passage blockade
    caribe_blocked = False
    caribe_level = "none"
    for cp_name, status in chokepoint_status.items():
        if cp_name in ("caribbean", "cp_caribe_passage"):
            if status == "blocked":
                caribe_level = "full"
                caribe_blocked = True
            elif status == "contested":
                caribe_level = "partial"
                caribe_blocked = True
    # Starting state: Columbia has partial blockade on Caribe
    if not caribe_blocked:
        # Check active_blockades for caribe passage
        cb = active_blockades.get("cp_caribe_passage", active_blockades.get("caribe", {}))
        if cb:
            caribe_level = cb.get("level", "partial")
            caribe_blocked = True

    if caribe_blocked and total_production > 0:
        blockade_pct = OIL_BLOCKADE_FULL if caribe_level == "full" else OIL_BLOCKADE_PARTIAL
        for affected in CARIBE_PASSAGE_PRODUCERS:
            if affected in producer_output:
                share = producer_output[affected] / total_production
                supply -= blockade_pct * share

    supply = max(0.3, supply)

    # --- DEMAND SIDE ---
    demand = 1.0
    for cid, c in countries.items():
        econ = c.get("economic", {})
        state = econ.get("economic_state", "normal")
        gdp = econ.get("gdp", 0)
        if state == "stressed" and gdp > 20:
            demand -= 0.03
        elif state == "crisis" and gdp > 20:
            demand -= 0.06
        elif state == "collapse" and gdp > 20:
            demand -= 0.10
        growth = econ.get("gdp_growth_rate", 0)
        if growth < -2 and gdp > 30:
            demand -= 0.02

    n_countries = len(countries)
    if n_countries > 0:
        gdp_growth_avg = sum(
            c["economic"].get("gdp_growth_rate", 0)
            for c in countries.values()
        ) / n_countries
        demand += (gdp_growth_avg - 2.0) * 0.03

    # --- DEMAND DESTRUCTION (Cal-10c: cumulative, applied to demand not price) ---
    # Each round above $100 threshold reduces demand further (consumers adapt, switch fuels)
    if oil_above_150_rounds >= OIL_DEMAND_DESTRUCTION_ROUNDS:
        extra_rounds = oil_above_150_rounds - OIL_DEMAND_DESTRUCTION_ROUNDS + 1  # 1, 2, 3, ...
        # Each extra round destroys 5% of demand, compounding
        # At 5%: after 3 extra rounds demand = 0.86, after 5 = 0.77
        demand *= (1.0 - 0.05) ** extra_rounds

    demand = max(0.4, demand)  # floor: demand can't drop below 40% of normal

    # --- WAR PREMIUM (Cal-10: Gulf region wars only) ---
    war_premium = 0.0
    gulf_countries = {"columbia", "persia", "levantia", "solaria", "mirage", "sarmatia"}
    for w in wars:
        belligerents = set()
        belligerents.add(w.get("attacker", ""))
        belligerents.add(w.get("defender", ""))
        if belligerents & gulf_countries:
            war_premium += 0.05
    war_premium = min(war_premium, 0.15)

    # --- COMPUTE PRICE (Cal-10: non-linear supply/demand) ---
    ratio = demand / supply
    raw_price = base_price * (ratio ** OIL_SUPPLY_DEMAND_EXPONENT) * (1 + war_premium)

    # Soft cap: asymptotic above $200
    if raw_price <= OIL_SOFT_CAP_THRESHOLD:
        formula_price = raw_price
    else:
        formula_price = (
            OIL_SOFT_CAP_THRESHOLD
            + OIL_SOFT_CAP_SCALE * (1 - math.exp(-(raw_price - OIL_SOFT_CAP_THRESHOLD) / OIL_SOFT_CAP_DECAY))
        )

    formula_price = max(OIL_PRICE_FLOOR, formula_price)

    # --- INERTIA (Cal-10: 30/70) ---
    price = previous_oil_price * OIL_INERTIA_PREVIOUS + formula_price * OIL_INERTIA_FORMULA
    price = max(OIL_PRICE_FLOOR, price)

    # --- TRACK ROUNDS ABOVE THRESHOLD (for cumulative demand destruction) ---
    if price > OIL_DEMAND_DESTRUCTION_THRESHOLD:
        oil_above_150_rounds += 1
    else:
        oil_above_150_rounds = max(0, oil_above_150_rounds - 1)  # slow recovery when price drops

    price = max(OIL_PRICE_FLOOR, price)

    # --- OIL REVENUE TO PRODUCERS (F46: mbpd-based, blockade reduces exports) ---
    for cid, country in countries.items():
        eco = country["economic"]
        mbpd = eco.get("oil_production_mbpd", 0.0)
        if eco.get("oil_producer") and mbpd > 0:
            effective_mbpd = mbpd
            # Gulf Gate blockade reduces Gulf producers' export revenue
            if cid in GULF_GATE_PRODUCERS or (
                cid == "persia" and gulf_gate_level != "none"
                and active_blockades.get("gulf_gate_ground", active_blockades.get("cp_gulf_gate", {})).get("controller", "") != "persia"
            ):
                if gulf_gate_level == "full":
                    effective_mbpd *= (1.0 - OIL_BLOCKADE_FULL)
                elif gulf_gate_level == "partial":
                    effective_mbpd *= (1.0 - OIL_BLOCKADE_PARTIAL)
            # Caribe Passage blockade reduces Caribe export revenue
            if cid in CARIBE_PASSAGE_PRODUCERS and caribe_blocked:
                if caribe_level == "full":
                    effective_mbpd *= (1.0 - OIL_BLOCKADE_FULL)
                elif caribe_level == "partial":
                    effective_mbpd *= (1.0 - OIL_BLOCKADE_PARTIAL)
            oil_revenue = price * effective_mbpd * 0.009
            eco["oil_revenue"] = round(max(oil_revenue, 0.0), 2)
        else:
            eco["oil_revenue"] = 0.0

    price = round(price, 1)

    log.append(
        f"  Oil: ${price:.1f} (supply={supply:.2f} demand={demand:.2f} "
        f"ratio^1.5={ratio**OIL_SUPPLY_DEMAND_EXPONENT:.2f} war={war_premium:.2f} "
        f"gulf_gate={gulf_gate_level} caribe={caribe_level})"
    )

    result = OilPriceResult(
        price=price,
        supply=supply,
        demand=demand,
        disruption=1.0,  # Cal-10: disruption now modeled as supply reduction
        war_premium=war_premium,
        formula_price=round(formula_price, 1),
        previous_price=previous_oil_price,
        gulf_gate_blocked=(gulf_gate_level != "none"),
        formosa_blocked=False,  # Cal-10: Formosa doesn't affect oil supply
    )
    return result, oil_above_150_rounds


def calc_sanctions_coefficient(
    target_id: str,
    countries: dict[str, dict],
    sanctions: dict[str, dict],
) -> float:
    """Calculate the GDP sanctions coefficient for a target country.

    Returns a value between 0.50 and 1.0.
    1.0 = no sanctions. Lower = more GDP suppression.
    ~0.88 = full world sanctions on resources-heavy country (12% GDP loss).
    ~0.65 = full world sanctions on tech/services-heavy country (35% GDP loss).

    Uses STARTING GDP (stored as _starting_gdp in eco dict) for market share
    calculation to prevent coefficient drift from round-to-round GDP changes.
    If _starting_gdp not available, falls back to current GDP.
    """
    # Step 1: Total world economic weight — use STARTING GDP for stability
    # This ensures the coefficient is deterministic when sanctions don't change.
    total_gdp = sum(c["economic"].get("_starting_gdp", c["economic"]["gdp"]) for c in countries.values())
    if total_gdp <= 0:
        return 1.0

    # Step 2: Coverage = fraction of world economy sanctioning the target
    coverage = 0.0
    for sanctioner_id, targets in sanctions.items():
        if sanctioner_id.startswith("_"):
            continue
        level = targets.get(target_id, 0)
        if level <= 0:
            continue
        s_eco = countries.get(sanctioner_id, {}).get("economic", {})
        sanctioner_gdp = s_eco.get("_starting_gdp", s_eco.get("gdp", 0))
        coverage += (sanctioner_gdp / total_gdp) * (level / 3.0)

    coverage = clamp(coverage, 0.0, 1.0)

    # Step 3: S-curve — non-linear effectiveness
    effectiveness = interpolate_s_curve(coverage, SANCTIONS_S_CURVE)

    # Step 4: Target vulnerability (sector-based)
    target_eco = countries.get(target_id, {}).get("economic", {})
    resource_pct = target_eco.get("sectors", {}).get("resources", 0) / 100.0
    tech_pct = target_eco.get("sectors", {}).get("technology", 0) / 100.0
    services_pct = target_eco.get("sectors", {}).get("services", 0) / 100.0
    sector_vulnerability = clamp(
        0.5 + (services_pct + tech_pct) * 0.8 - resource_pct * 0.6,
        0.3, 1.2,
    )

    # Step 5: Trade openness
    trade_bal = abs(target_eco.get("trade_balance", 0))
    target_gdp = max(target_eco.get("gdp", 1), 1)
    trade_openness = clamp(trade_bal / target_gdp + 0.3, 0.0, 1.0)

    # Step 6: Compute coefficient
    damage = SANCTIONS_MAX_DAMAGE * effectiveness * trade_openness * sector_vulnerability
    damage = min(damage, SANCTIONS_MAX_DAMAGE)
    coefficient = max(0.50, 1.0 - damage)

    return coefficient


# Tariff model constants (Cal-11c)
TARIFF_K: float = 0.54  # calibrated for Columbia L3 on Cathay = ~4% GDP hit
TARIFF_IMPOSER_FRACTION: float = 0.5  # imposer self-damage = 50% of target formula
TARIFF_REVENUE_RATE: float = 0.075  # revenue rate (coins)
TARIFF_INFLATION_RATE: float = 12.5  # inflation points per unit of tariff × partner share


def _trade_exposure(eco: dict) -> float:
    """How trade-dependent is this economy? 0.25 (large/diverse) to 0.50+ (very open)."""
    gdp = max(eco.get("gdp", 1), 1)
    trade_bal = abs(eco.get("trade_balance", 0))
    return (trade_bal + 0.25 * gdp) / gdp


def calc_tariff_coefficient(
    country_id: str,
    countries: dict[str, dict],
    tariffs: dict[str, dict],
) -> tuple[float, float, float]:
    """Calculate tariff GDP coefficient, inflation impact, and customs revenue.

    Prisoner's dilemma model:
    - Imposer gets: revenue (positive) + self-damage (small) + inflation
    - Target gets: GDP hit proportional to imposer's market power
    - Retaliation escalates damage for both

    Returns (coefficient, inflation_add, customs_revenue_coins).
    """
    my_c = countries.get(country_id, {})
    my_eco = my_c.get("economic", {})
    my_gdp = max(my_eco.get("_starting_gdp", my_eco.get("gdp", 1)), 1)
    my_exposure = _trade_exposure(my_eco)
    # Use STARTING GDP for market share to prevent coefficient drift
    total_gdp = sum(c["economic"].get("_starting_gdp", c["economic"]["gdp"]) for c in countries.values())
    if total_gdp <= 0:
        return 1.0, 0.0, 0.0

    total_gdp_hit = 0.0  # accumulate all GDP damage to this country
    customs_revenue = 0.0
    inflation_add = 0.0

    # --- Tariffs I IMPOSE on others ---
    # I get: revenue (good) + self-damage (bad) + inflation (bad)
    my_tariffs = tariffs.get(country_id, {})
    for target_id, tariff_data in my_tariffs.items():
        level = int(tariff_data) if not isinstance(tariff_data, dict) else max(tariff_data.values(), default=0)
        if level <= 0:
            continue
        target_c = countries.get(target_id, {})
        target_eco = target_c.get("economic", {})
        target_gdp = max(target_eco.get("gdp", 1), 1)
        target_exposure = _trade_exposure(target_eco)
        target_market_share = target_gdp / total_gdp
        intensity = level / 3.0

        # My self-damage as imposer (disrupted imports, inefficiency)
        self_damage = target_market_share * my_exposure * intensity * TARIFF_K * TARIFF_IMPOSER_FRACTION
        total_gdp_hit += self_damage

        # My customs revenue (coins)
        revenue = target_gdp * target_exposure * intensity * TARIFF_REVENUE_RATE
        customs_revenue += revenue

        # My inflation (one-off import cost increase)
        infl = intensity * target_market_share * TARIFF_INFLATION_RATE
        inflation_add += infl

    # --- Tariffs others IMPOSE on me ---
    # I lose access to their market — the bigger they are, the more it hurts
    for imposer_id, targets in tariffs.items():
        if imposer_id == country_id or imposer_id.startswith("_"):
            continue
        tariff_data = targets.get(country_id)
        if tariff_data is None:
            continue
        level = int(tariff_data) if not isinstance(tariff_data, dict) else max(tariff_data.values(), default=0)
        if level <= 0:
            continue
        imposer_eco = countries.get(imposer_id, {}).get("economic", {})
        imposer_gdp = max(imposer_eco.get("_starting_gdp", imposer_eco.get("gdp", 1)), 1)
        imposer_market_share = imposer_gdp / total_gdp
        intensity = level / 3.0

        # Damage to me = imposer's market power × my trade exposure
        target_damage = imposer_market_share * my_exposure * intensity * TARIFF_K
        total_gdp_hit += target_damage

    # Coefficient
    coefficient = max(0.80, 1.0 - total_gdp_hit)

    return coefficient, inflation_add, customs_revenue


def calc_gdp_growth(
    country_id: str,
    countries: dict[str, dict],
    tariff_info: TariffResult,
    oil_price: float,
    wars: list[dict],
    chokepoint_status: dict[str, str],
    formosa_disrupted: bool,
    log: list[str],
) -> GdpResult:
    """Additive factor model with crisis multiplier. SEED Step 2.

    Cal-7 redesign: structural base_growth is PROTECTED from shocks.
    Negative factors are scaled by shock_absorb (inverse of maturity dampener) so
    large mature economies absorb shocks easily while small emerging ones are more
    vulnerable — but not so vulnerable that their structural growth disappears.
    Crisis multiplier applies ONLY to the cyclical component (shocks + bonuses),
    never to the structural base rate.
    """
    c = countries[country_id]
    eco = c["economic"]
    old_gdp = eco["gdp"]
    # Use structural base rate (immutable), not last round's actual growth result
    structural_rate = eco.get("gdp_growth_base", eco["gdp_growth_rate"])
    base_growth = structural_rate / 100.0 / 2.0

    # --- Cal-7: SHOCK ABSORPTION ---
    # Larger economies absorb trade shocks better (deeper markets, diversification).
    # shock_absorb ranges from 0.5 (tiny GDP ~20) to 1.0 (GDP ~80+).
    # This caps how much tariffs/sanctions/oil can hurt relative to GDP.
    # Small emerging economies (Bharata GDP 42, Hanguk GDP 20) get partial protection.
    # Medium+ economies (GDP 80+) get full shock impact — no change from Cal-6.
    shock_absorb = clamp(old_gdp / 80.0, 0.5, 1.0)

    # Tariffs: handled via coefficient (level adjustment), not growth rate
    tariff_hit = 0.0

    # Sanctions: handled via coefficient (level adjustment), not growth rate
    sanctions_hit = 0.0

    # --- OIL SHOCK (Cal-9+10: delta from baseline, scaled by resource sector size) ---
    starting_oil = eco.get("starting_oil_price", 80.0)
    oil_shock = 0.0
    resource_pct = eco["sectors"].get("resources", 0) / 100.0  # Cal-10: sector size matters
    is_oil_importer = not eco.get("oil_producer", False)
    price_delta = oil_price - starting_oil
    if is_oil_importer:
        # Importers: hurt by price increase, helped by decrease
        # Impact scaled by how NON-resource the economy is (services/tech economies hurt more)
        import_exposure = 1.0 - resource_pct  # high for Japan (0.98), low for... no importers have high resources
        oil_shock = -0.02 * price_delta / 50 * import_exposure
    else:
        # Producers: benefit from price increase, hurt by decrease
        # Impact scaled by resource sector size (Saudi 45% much more than Columbia 8%)
        oil_shock = 0.01 * price_delta / 50 * (resource_pct * 3)  # 3× weight so 45% resources → 1.35× sensitivity

    # --- SEMICONDUCTOR DISRUPTION ---
    semi_hit = 0.0
    dep = eco.get("formosa_dependency", 0)
    if formosa_disrupted and dep > 0:
        rounds_disrupted = eco.get("formosa_disruption_rounds", 0)
        severity = min(1.0, 0.3 + 0.2 * max(0, rounds_disrupted - 1))
        tech_sector_pct = eco["sectors"].get("technology", 0) / 100.0
        semi_hit = max(-0.10, -dep * severity * tech_sector_pct)  # H7 fix: cap at -10%

    # --- WAR DAMAGE ---
    war_zones = _count_war_zones(wars, country_id)
    infra_damage = _get_infra_damage(wars, country_id)
    war_hit = -(war_zones * 0.03 + infra_damage * 0.05)

    # --- TECH FACTOR (Cal-7: maturity-aware diminishing returns) ---
    ai_level = c["technology"]["ai_level"]
    raw_tech = AI_LEVEL_TECH_FACTOR.get(ai_level, 0)
    # Cal-7: Two-factor dampener — economy SIZE and MATURITY.
    # Mature/slow-growth economies (USA, Japan, France) get strong dampening.
    # Emerging/fast-growth economies (China, India) retain more of their bonus.
    # maturity: 0.3 (mature, <1.8% base) to 1.0 (emerging, >=6% base), continuous.
    maturity = clamp(structural_rate / 6.0, 0.3, 1.0)
    # Size still matters (larger GDP = less marginal impact from tech/momentum)
    # but the threshold is higher for high-growth economies.
    gdp_scale = maturity / (1.0 + old_gdp / 200.0)
    tech_boost = raw_tech * gdp_scale

    # --- MOMENTUM REMOVED (Cal-8: AI Pass 2 handles confidence effects) ---
    momentum_effect = 0.0

    # --- CRISIS STATE MULTIPLIER ---
    eco_state = eco.get("economic_state", "normal")
    crisis_mult = CRISIS_GDP_MULTIPLIER.get(eco_state, 1.0)

    # --- BLOCKADE FACTOR ---
    blockade_frac = _get_blockade_fraction(country_id, eco, chokepoint_status)
    blockade_hit = -blockade_frac * 0.4

    # --- BILATERAL DEPENDENCY (FIX 1) ---
    bilateral_drag = _calc_bilateral_dependency(country_id, countries) / 100.0

    # --- COMPUTE GROWTH (Cal-7: separate structural from cyclical) ---
    # Cyclical component: all shocks and bonuses (NOT base_growth).
    # Negative shocks are dampened by shock_absorb for small economies.
    negative_shocks = tariff_hit + sanctions_hit + oil_shock + semi_hit + war_hit + blockade_hit + bilateral_drag
    positive_bonuses = tech_boost + momentum_effect
    # Cal-7: small economies partially absorb negative shocks
    dampened_shocks = negative_shocks * shock_absorb
    cyclical = dampened_shocks + positive_bonuses

    # --- Cal-7: CRISIS MULTIPLIER ON CYCLICAL ONLY ---
    # Structural growth persists through crises (factories don't vanish).
    # Crisis multiplier only amplifies the cyclical swing.
    if cyclical < 0:
        crisis_amp = CRISIS_NEGATIVE_AMPLIFIER.get(eco_state, 1.0)
        effective_cyclical = cyclical * crisis_amp
    else:
        effective_cyclical = cyclical * crisis_mult

    # Cal-7: Total growth = protected structural base + crisis-adjusted cyclical
    effective_growth = base_growth + effective_cyclical

    # Grow GDP from base + cyclical factors
    gdp_after_growth = old_gdp * (1.0 + effective_growth)

    # Cal-11: Apply sanctions + tariff coefficients (level adjustments)
    # GDP_actual = GDP_after_growth × (new_sanc_coeff / old_sanc_coeff) × (new_tar_coeff / old_tar_coeff)
    old_sanc = eco.get("sanctions_coefficient", 1.0)
    new_sanc = eco.get("_new_sanctions_coefficient", old_sanc)
    sanc_ratio = new_sanc / max(old_sanc, 0.01)

    old_tar = eco.get("tariff_coefficient", 1.0)
    new_tar = eco.get("_new_tariff_coefficient", old_tar)
    tar_ratio = new_tar / max(old_tar, 0.01)

    new_gdp = gdp_after_growth * sanc_ratio * tar_ratio
    eco["sanctions_coefficient"] = new_sanc
    eco["tariff_coefficient"] = new_tar

    new_gdp = max(GDP_FLOOR, new_gdp)
    growth_pct = ((new_gdp / old_gdp) - 1.0) * 100.0  # actual total change

    log.append(
        f"  GDP {country_id}: {old_gdp:.2f}->{new_gdp:.2f} "
        f"(growth {growth_pct:+.2f}% | base={base_growth*100:.1f} "
        f"tariff={tariff_hit*100:+.1f} sanc={sanctions_hit*100:+.1f} "
        f"oil={oil_shock*100:+.1f} semi={semi_hit*100:+.1f} "
        f"war={war_hit*100:+.1f} tech={tech_boost*100:+.1f} "
        f"momentum={momentum_effect*100:+.1f} blockade={blockade_hit*100:+.1f} "
        f"bilateral={bilateral_drag*100:+.1f} "
        f"crisis_mult={crisis_mult:.2f} state={eco_state} "
        f"gdp_scale={gdp_scale:.3f} maturity={maturity:.2f} "
        f"shock_absorb={shock_absorb:.2f})"
    )

    return GdpResult(
        old_gdp=old_gdp, new_gdp=round(new_gdp, 2),
        growth_pct=round(growth_pct, 2), base_growth=round(base_growth * 100, 2),
        tariff_hit=round(tariff_hit * 100, 2),
        sanctions_hit=round(sanctions_hit * 100, 2),
        oil_shock=round(oil_shock * 100, 2),
        semi_hit=round(semi_hit * 100, 2),
        war_hit=round(war_hit * 100, 2),
        tech_boost=round(tech_boost * 100, 2),
        momentum_effect=round(momentum_effect * 100, 2),
        blockade_hit=round(blockade_hit * 100, 2),
        bilateral_drag=round(bilateral_drag * 100, 2),
        crisis_multiplier=crisis_mult,
        economic_state=eco_state,
    )


def calc_revenue(
    country_id: str,
    countries: dict[str, dict],
    wars: list[dict],
    sanctions: dict[str, dict],
    trade_weights: dict[str, dict[str, float]],
    log: list[str],
) -> RevenueResult:
    """Revenue = GDP * tax_rate + oil_revenue - debt - inflation_erosion - war - sanctions."""
    c = countries[country_id]
    eco = c["economic"]
    gdp = eco["gdp"]
    tax_rate = eco["tax_rate"]

    base_rev = gdp * tax_rate
    oil_rev = eco.get("oil_revenue", 0.0)

    debt = eco["debt_burden"]

    starting_infl = eco.get("starting_inflation", 0)
    inflation_delta = max(0, eco["inflation"] - starting_infl)
    inflation_erosion = inflation_delta * 0.03 * gdp / 100.0
    eco["inflation_revenue_erosion"] = round(inflation_erosion, 2)

    war_damage = _get_infra_damage(wars, country_id) * 0.02 * gdp

    sanc_cost = 0.0
    for sanctioner, targets in sanctions.items():
        level = targets.get(country_id, 0)
        if level > 0:
            bw = trade_weights.get(sanctioner, {}).get(country_id, 0)
            sanc_cost += level * bw * 0.015 * gdp

    revenue = base_rev + oil_rev - debt - inflation_erosion - war_damage - sanc_cost
    revenue = max(revenue, 0.0)

    log.append(
        f"  Revenue {country_id}: {revenue:.2f} "
        f"(base={base_rev:.2f} oil={oil_rev:.2f} debt=-{debt:.2f} "
        f"infl_erosion=-{inflation_erosion:.2f} war=-{war_damage:.2f} "
        f"sanc=-{sanc_cost:.2f})"
    )

    return RevenueResult(
        total=round(revenue, 2),
        base_revenue=round(base_rev, 2),
        oil_revenue=round(oil_rev, 2),
        debt_cost=round(debt, 2),
        inflation_erosion=round(inflation_erosion, 2),
        war_damage_cost=round(war_damage, 2),
        sanctions_cost=round(sanc_cost, 2),
    )


def calc_budget_execution(
    country_id: str,
    countries: dict[str, dict],
    budget: dict,
    revenue: float,
    log: list[str],
) -> BudgetResult:
    """Budget execution with deficit -> money printing -> inflation chain."""
    c = countries[country_id]
    mil = c["military"]
    eco = c["economic"]

    # --- Fixed costs (F51: ×3 multiplier creates budget tension) ---
    maint_rate = mil.get("maintenance_cost_per_unit", 0.02)
    total_units = sum(mil.get(ut, 0) for ut in UNIT_TYPES)
    maintenance = total_units * maint_rate * MAINTENANCE_MULTIPLIER

    # --- Social spending: flat coins/round, decision is % of baseline ---
    # social_spending_baseline is a % of GDP, but actual coins = baseline% × revenue
    # (governments spend from revenue, not GDP — this ensures budget balance)
    social_baseline_pct = eco.get("social_spending_baseline", 0.25)
    social_base_coins = social_baseline_pct * max(revenue, 0)
    # Player/AI sets spending level (default 100% = normal). Range: 50%-150%.
    social_pct = budget.get("social_pct", 1.0)  # 1.0 = 100% of baseline
    social_spending = social_base_coins * social_pct

    # --- Discretionary allocation (military production, tech R&D) ---
    remaining_after_fixed = revenue - maintenance - social_spending
    mil_budget = budget.get("military_total", max(remaining_after_fixed * 0.4, 0))
    mil_budget = max(0, min(mil_budget, max(remaining_after_fixed, 0)))
    remaining_after_mil = max(remaining_after_fixed - mil_budget, 0)
    tech_budget = budget.get("tech_total", remaining_after_mil * 0.3)
    tech_budget = max(0, min(tech_budget, remaining_after_mil))

    total_spending = maintenance + social_spending + mil_budget + tech_budget

    # --- Deficit / surplus handling ---
    money_printed = 0.0
    deficit = 0.0

    if total_spending > revenue:
        deficit = total_spending - revenue

        if eco["treasury"] >= deficit:
            eco["treasury"] -= deficit
        else:
            money_printed = deficit - eco["treasury"]
            eco["treasury"] = 0

            if eco["gdp"] > 0:
                eco["inflation"] += money_printed / eco["gdp"] * MONEY_PRINTING_INFLATION_MULTIPLIER

            eco["debt_burden"] += deficit * DEFICIT_TO_DEBT_RATE

            log.append(
                f"  DEFICIT {country_id}: printed {money_printed:.2f} coins, "
                f"inflation +{money_printed / max(eco['gdp'], 0.01) * MONEY_PRINTING_INFLATION_MULTIPLIER:.1f}%"
            )
    else:
        surplus = revenue - total_spending
        eco["treasury"] += surplus

    # Track social spending ratio for stability formula
    # Cal-5 fix: pass baseline * decision_pct so stability compares apples-to-apples.
    # Previously this was social_spending/gdp, but social_spending is funded from
    # REVENUE (a fraction of GDP), so the ratio was always < baseline, falsely
    # triggering severe austerity penalties for fully-funded social programs.
    gdp = eco["gdp"]
    actual_social_ratio = social_baseline_pct * social_pct
    eco["_actual_social_ratio"] = round(actual_social_ratio, 4)
    eco["_social_pct"] = social_pct  # for stability formula to read

    mandatory_total = maintenance + social_spending
    discretionary_total = max(revenue - mandatory_total, 0)

    return BudgetResult(
        revenue=revenue,
        mandatory=round(mandatory_total, 2),
        maintenance=round(maintenance, 2),
        social_baseline_cost=round(social_base_coins, 2),
        discretionary=round(discretionary_total, 2),
        social_spending=round(social_spending, 2),
        military_budget=round(mil_budget, 2),
        tech_budget=round(tech_budget, 2),
        deficit=round(deficit, 2),
        money_printed=round(money_printed, 2),
        new_treasury=round(eco["treasury"], 2),
    )


def calc_military_production(
    country_id: str,
    countries: dict[str, dict],
    military_alloc: dict,
    round_num: int,
    log: list[str],
) -> MilitaryProductionResult:
    """Produce units. Includes naval auto-production fix."""
    c = countries[country_id]
    mil = c["military"]
    cap = mil.get("production_capacity", {})
    costs = mil.get("production_costs", {})
    produced: dict[str, int] = {}

    for utype in ("ground", "naval", "tactical_air"):
        alloc = military_alloc.get(utype, {})
        coins = alloc.get("coins", 0)
        tier = alloc.get("tier", "normal")
        if coins <= 0:
            produced[utype] = 0
            continue

        unit_cost = costs.get(utype, 3) * PRODUCTION_TIER_COST.get(tier, 1.0)
        max_cap = cap.get(utype, 0) * PRODUCTION_TIER_OUTPUT.get(tier, 1.0)

        units = min(int(coins / unit_cost), int(max_cap)) if unit_cost > 0 else 0
        units = max(units, 0)
        mil[utype] = mil.get(utype, 0) + units
        produced[utype] = units

    # Naval auto-production: 1 per 2 rounds for countries with naval >= 5
    if mil.get("naval", 0) >= 5 and round_num % 2 == 0:
        if produced.get("naval", 0) == 0:
            mil["naval"] = mil.get("naval", 0) + 1
            produced["naval"] = produced.get("naval", 0) + 1
            log.append(
                f"  Naval auto-production {country_id}: +1 "
                f"(maintenance replacement, total={mil['naval']})"
            )

    # Cathay strategic missile growth
    if country_id == "cathay" and mil.get("strategic_missile_growth", 0) > 0:
        mil["strategic_missile"] = mil.get("strategic_missile", 0) + 1
        produced["strategic_missile"] = 1
        log.append("  Cathay strategic missile: +1")

    if any(v > 0 for v in produced.values()):
        log.append(f"  Production {country_id}: {produced}")

    return MilitaryProductionResult(produced=produced)


def calc_tech_advancement(
    country_id: str,
    countries: dict[str, dict],
    rd_investment: dict,
    rare_earth_restrictions: dict[str, int],
    log: list[str],
) -> TechResult:
    """R&D with fixed multiplier 0.8 and rare earth impact."""
    c = countries[country_id]
    tech = c["technology"]
    gdp = c["economic"]["gdp"]
    result_nuclear = False
    result_ai = False
    result_l4_bonus: bool | None = None

    rare_earth_factor = _calc_rare_earth_impact(country_id, rare_earth_restrictions)

    # Nuclear R&D
    nuc_invest = rd_investment.get("nuclear", 0)
    if nuc_invest > 0 and gdp > 0:
        nuc_progress = (nuc_invest / max(gdp, 0.01)) * RD_MULTIPLIER * rare_earth_factor
        tech["nuclear_rd_progress"] += nuc_progress
    nuc_threshold = NUCLEAR_RD_THRESHOLDS.get(tech["nuclear_level"], 999.0)
    if tech["nuclear_rd_progress"] >= nuc_threshold and tech["nuclear_level"] < 3:
        tech["nuclear_level"] += 1
        tech["nuclear_rd_progress"] = 0.0
        result_nuclear = True
        log.append(f"  TECH BREAKTHROUGH: {country_id} nuclear->L{tech['nuclear_level']}")

    # AI R&D
    ai_invest = rd_investment.get("ai", 0)
    if ai_invest > 0 and gdp > 0:
        ai_progress = (ai_invest / max(gdp, 0.01)) * RD_MULTIPLIER * rare_earth_factor
        tech["ai_rd_progress"] += ai_progress
    ai_threshold = AI_RD_THRESHOLDS.get(tech["ai_level"], 999.0)
    if tech["ai_rd_progress"] >= ai_threshold and tech["ai_level"] < 4:
        tech["ai_level"] += 1
        tech["ai_rd_progress"] = 0.0
        result_ai = True
        if tech["ai_level"] == 4:
            tech["ai_l4_bonus"] = random.random() < 0.50
            result_l4_bonus = tech["ai_l4_bonus"]
            log.append(
                f"  AI L4 COMBAT BONUS: {country_id} "
                f"{'GRANTED (+1)' if tech['ai_l4_bonus'] else 'NOT GRANTED'}"
            )
        log.append(f"  TECH BREAKTHROUGH: {country_id} AI->L{tech['ai_level']}")

    if rare_earth_factor < 1.0:
        log.append(f"  Rare earth restriction on {country_id}: R&D factor={rare_earth_factor:.2f}")

    return TechResult(nuclear_levelup=result_nuclear, ai_levelup=result_ai, ai_l4_bonus=result_l4_bonus)


def calc_inflation(
    country_id: str,
    countries: dict[str, dict],
    money_printed: float,
) -> float:
    """Inflation with 15% natural decay on EXCESS above baseline only.

    Structural/baseline inflation persists. Only crisis-induced excess decays.
    """
    c = countries[country_id]
    prev = c["economic"]["inflation"]
    gdp = c["economic"]["gdp"]
    baseline = c["economic"].get("starting_inflation", 0)

    excess = max(0, prev - baseline)
    new_excess = excess * INFLATION_EXCESS_DECAY

    if gdp > 0 and money_printed > 0:
        new_excess += (money_printed / gdp) * MONEY_PRINTING_INFLATION_MULTIPLIER

    new_infl = baseline + new_excess
    new_infl = clamp(new_infl, INFLATION_FLOOR, INFLATION_CEILING)
    return round(new_infl, 2)


def calc_debt_service(
    country_id: str,
    countries: dict[str, dict],
    deficit: float,
) -> float:
    """Deficits become 15% permanent debt burden."""
    c = countries[country_id]
    old_debt = c["economic"]["debt_burden"]
    new_debt = old_debt
    if deficit > 0:
        new_debt = old_debt + deficit * DEFICIT_TO_DEBT_RATE
    return round(max(new_debt, 0.0), 2)


def update_economic_state(
    country_id: str,
    countries: dict[str, dict],
    oil_price: float,
    formosa_disrupted: bool,
    log: list[str],
) -> EconomicStateResult:
    """Transition between NORMAL/STRESSED/CRISIS/COLLAPSE.

    Downward transitions are fast (immediate).
    Upward transitions are slow (2-3 rounds of positive indicators).
    """
    c = countries[country_id]
    eco = c["economic"]
    state = eco.get("economic_state", "normal")
    old_state = state

    is_oil_importer = not eco.get("oil_producer", False)
    starting_infl = eco.get("starting_inflation", 0)
    gdp_growth = eco.get("gdp_growth_rate", 0)
    dep = eco.get("formosa_dependency", 0)
    disruption_rounds = eco.get("formosa_disruption_rounds", 0)

    # --- COUNT STRESS TRIGGERS ---
    stress_triggers = 0
    if oil_price > 150 and is_oil_importer:
        stress_triggers += 1
    if eco["inflation"] > starting_infl + 15:
        stress_triggers += 1
    if gdp_growth < -1:
        stress_triggers += 1
    if eco["treasury"] <= 0:
        stress_triggers += 1
    if c["political"]["stability"] < 4:
        stress_triggers += 1
    if formosa_disrupted and dep > 0.3:
        stress_triggers += 1

    # --- COUNT CRISIS TRIGGERS ---
    crisis_triggers = 0
    if oil_price > 200 and is_oil_importer:
        crisis_triggers += 1
    if eco["inflation"] > starting_infl + 30:
        crisis_triggers += 1
    if gdp_growth < -3:
        crisis_triggers += 1
    if eco["treasury"] <= 0 and eco["debt_burden"] > eco["gdp"] * 0.1:
        crisis_triggers += 1
    if disruption_rounds >= 3 and dep > 0.5:
        crisis_triggers += 1

    # --- DOWNWARD TRANSITIONS (fast) ---
    if state == "normal" and stress_triggers >= 2:
        state = "stressed"
    if state == "stressed" and crisis_triggers >= 2:
        state = "crisis"
        eco["crisis_rounds"] = 0
    if state in ("crisis", "collapse"):
        eco["crisis_rounds"] = eco.get("crisis_rounds", 0) + 1
    if state == "crisis" and eco["crisis_rounds"] >= 3 and crisis_triggers >= 2:
        state = "collapse"

    # --- UPWARD TRANSITIONS (slow) ---
    if state == "collapse" and crisis_triggers == 0:
        eco["recovery_rounds"] = eco.get("recovery_rounds", 0) + 1
        if eco["recovery_rounds"] >= 3:
            state = "crisis"
            eco["recovery_rounds"] = 0
    elif state == "crisis" and stress_triggers <= 1:
        eco["recovery_rounds"] = eco.get("recovery_rounds", 0) + 1
        if eco["recovery_rounds"] >= 2:
            state = "stressed"
            eco["recovery_rounds"] = 0
    elif state == "stressed" and stress_triggers == 0:
        eco["recovery_rounds"] = eco.get("recovery_rounds", 0) + 1
        if eco["recovery_rounds"] >= 2:
            state = "normal"
            eco["recovery_rounds"] = 0
    else:
        eco["recovery_rounds"] = 0

    eco["economic_state"] = state

    if state != old_state:
        log.append(
            f"  ECONOMIC STATE {country_id}: {old_state} -> {state} "
            f"(stress={stress_triggers} crisis={crisis_triggers})"
        )

    return EconomicStateResult(
        old_state=old_state, new_state=state,
        stress_triggers=stress_triggers, crisis_triggers=crisis_triggers,
        crisis_rounds=eco.get("crisis_rounds", 0),
        recovery_rounds=eco.get("recovery_rounds", 0),
    )


def update_momentum(
    country_id: str,
    countries: dict[str, dict],
    oil_price: float,
    formosa_disrupted: bool,
    wars: list[dict],
    previous_states: dict[str, dict],
    log: list[str],
) -> MomentumResult:
    """Economic confidence. Builds slowly (+0.3/round max), crashes fast (-2.0/round)."""
    c = countries[country_id]
    eco = c["economic"]
    old_m = eco.get("momentum", 0.0)

    gdp_growth = eco.get("gdp_growth_rate", 0)
    eco_state = eco.get("economic_state", "normal")
    is_oil_importer = not eco.get("oil_producer", False)
    dep = eco.get("formosa_dependency", 0)

    # --- POSITIVE SIGNALS ---
    boost = 0.0
    if gdp_growth > 2:
        boost += 0.15
    if eco_state == "normal":
        boost += 0.15
    if c["political"]["stability"] > 6:
        boost += 0.15
    boost = min(MOMENTUM_BOOST_CAP, boost)

    # --- NEGATIVE SIGNALS ---
    crash = 0.0
    if eco_state == "crisis":
        crash -= 1.0
    if eco_state == "collapse":
        crash -= 2.0
    if gdp_growth < -2:
        crash -= 0.5
    if oil_price > 200 and is_oil_importer:
        crash -= 0.5
    if formosa_disrupted and dep > 0.3:
        crash -= 0.5

    # Just entered war this round
    prev = previous_states.get(country_id, {})
    at_war_now = _is_country_at_war(wars, country_id)
    was_at_war = prev.get("at_war", False)
    if at_war_now and not was_at_war:
        crash -= 1.0

    # Natural decay toward zero (10% per round — momentum is temporary)
    decay = -old_m * 0.10
    new_m = clamp(old_m + boost + crash + decay, MOMENTUM_FLOOR, MOMENTUM_CEILING)
    eco["momentum"] = round(new_m, 2)

    if abs(new_m - old_m) > 0.05:
        log.append(
            f"  Momentum {country_id}: {old_m:+.2f} -> {new_m:+.2f} "
            f"(boost={boost:+.2f} crash={crash:+.2f})"
        )

    return MomentumResult(
        old_momentum=old_m, new_momentum=round(new_m, 2),
        boost=round(boost, 2), crash=round(crash, 2),
    )


def apply_contagion(
    countries: dict[str, dict],
    trade_weights: dict[str, dict[str, float]],
    log: list[str],
) -> dict[str, list[ContagionHit]]:
    """When major economies enter crisis, trade partners feel it."""
    contagion_hits: dict[str, list[ContagionHit]] = {}

    for cid, c in countries.items():
        eco_state = c["economic"].get("economic_state", "normal")
        gdp = c["economic"]["gdp"]

        if eco_state in ("crisis", "collapse") and gdp >= MAJOR_ECONOMY_THRESHOLD:
            severity = 1.0 if eco_state == "crisis" else 2.0

            tw = trade_weights.get(cid, {})
            for partner_id, trade_weight in tw.items():
                if trade_weight > 0.10:
                    partner = countries.get(partner_id)
                    if not partner:
                        continue
                    hit = severity * trade_weight * 0.02
                    partner["economic"]["gdp"] *= (1 - hit)
                    partner["economic"]["gdp"] = max(GDP_FLOOR, partner["economic"]["gdp"])
                    partner["economic"]["momentum"] = max(
                        MOMENTUM_FLOOR,
                        partner["economic"].get("momentum", 0) - 0.3,
                    )

                    if partner_id not in contagion_hits:
                        contagion_hits[partner_id] = []
                    contagion_hits[partner_id].append(ContagionHit(
                        source=cid,
                        gdp_hit_pct=round(hit * 100, 2),
                        momentum_hit=-0.3,
                    ))
                    log.append(
                        f"  CONTAGION: {cid} crisis -> {partner_id} "
                        f"GDP -{hit*100:.1f}%, momentum -0.3"
                    )

    return contagion_hits


def update_dollar_credibility(
    countries: dict[str, dict],
    dollar_credibility: float,
    log: list[str],
) -> float:
    """Columbia money printing -> dollar weakens -> sanctions less effective."""
    col = countries.get("columbia", {})
    printed = col.get("economic", {}).get("money_printed_this_round", 0)

    credibility = dollar_credibility

    if printed > 0:
        credibility -= printed * DOLLAR_CREDIBILITY_EROSION_PER_COIN
    else:
        credibility = min(DOLLAR_CREDIBILITY_CEILING, credibility + DOLLAR_CREDIBILITY_RECOVERY)

    credibility = max(DOLLAR_CREDIBILITY_FLOOR, credibility)

    if credibility < 90:
        log.append(f"  Dollar credibility: {credibility:.0f}/100 (printed={printed:.1f})")

    return credibility


def _country_health_score(c: dict, oil_price: float) -> float:
    """Compute a single country's health score for market index composition.

    Returns a value centered on 100 (healthy). Range roughly 0-200.
    Drivers: GDP growth, inflation delta, sanctions, war, economic state.
    """
    eco = c["economic"]
    score = 100.0

    # GDP growth: +5 per 1% above 2%, -8 per 1% below 0%
    gdp_g = eco.get("gdp_growth_rate", 0.0)
    if gdp_g > 2.0:
        score += (gdp_g - 2.0) * 5.0
    elif gdp_g < 0.0:
        score += gdp_g * 8.0  # negative growth → big negative

    # Inflation delta from baseline
    infl_delta = eco["inflation"] - eco.get("starting_inflation", 0.0)
    if infl_delta > 5:
        score -= (infl_delta - 5) * 1.5
    if infl_delta > 20:
        score -= (infl_delta - 20) * 1.0  # accelerating penalty

    # Sanctions coefficient: 1.0 = no sanctions, 0.5 = heavy
    sanc_coeff = eco.get("sanctions_coefficient", 1.0)
    if sanc_coeff < 1.0:
        score -= (1.0 - sanc_coeff) * 40.0  # 10% suppression = -4 points

    # Economic state
    state_penalties = {"normal": 0, "stressed": -5, "crisis": -15, "collapse": -30}
    score += state_penalties.get(eco.get("economic_state", "normal"), 0)

    # War penalty
    if c.get("_at_war", False):
        score -= 10.0

    # Oil shock (global, affects all indexes)
    if oil_price > 150:
        score -= (oil_price - 150) * 0.1

    # Deficit ratio penalty
    debt_ratio = eco.get("debt_burden", 0.0)
    if debt_ratio > 1.0:
        score -= (debt_ratio - 1.0) * 15.0  # each 10% over 100% = -1.5

    return max(0.0, min(200.0, score))


def calc_market_indexes(
    countries: dict[str, dict],
    oil_price: float,
    previous_indexes: dict[str, float] | None,
    log: list[str],
) -> MarketIndexesResult:
    """Compute 3 regional market indexes from component country health scores.

    Each index = weighted average of component country health scores.
    Inertia: 70% previous value, 30% new calculation (smooth, not jumpy).
    Returns MarketIndexesResult with all 3 indexes.
    """
    if previous_indexes is None:
        previous_indexes = {
            "wall_street": MARKET_INDEX_BASELINE,
            "europa": MARKET_INDEX_BASELINE,
            "dragon": MARKET_INDEX_BASELINE,
        }

    # Compute health scores for all countries (once)
    health: dict[str, float] = {}
    for cid, c in countries.items():
        health[cid] = _country_health_score(c, oil_price)

    def _calc_one(name: str, components: dict[str, float], prev: float) -> SingleIndexResult:
        weighted_sum = 0.0
        total_weight = 0.0
        comp_scores: dict[str, float] = {}
        for cid, weight in components.items():
            if cid in health:
                comp_scores[cid] = round(health[cid], 1)
                weighted_sum += health[cid] * weight
                total_weight += weight
        raw = weighted_sum / max(total_weight, 0.01)
        # Inertia: 70% previous, 30% new (prevents wild swings)
        smoothed = prev * 0.7 + raw * 0.3
        final = max(MARKET_INDEX_FLOOR, min(MARKET_INDEX_CEILING, round(smoothed, 1)))
        return SingleIndexResult(
            name=name, old_value=prev, new_value=final, components=comp_scores,
        )

    ws = _calc_one("wall_street", WALL_STREET_COMPONENTS, previous_indexes.get("wall_street", 100.0))
    eu = _calc_one("europa", EUROPA_COMPONENTS, previous_indexes.get("europa", 100.0))
    dr = _calc_one("dragon", DRAGON_COMPONENTS, previous_indexes.get("dragon", 100.0))

    log.append(f"  Market indexes: Wall Street={ws.new_value:.0f}, Europa={eu.new_value:.0f}, Dragon={dr.new_value:.0f}")

    return MarketIndexesResult(wall_street=ws, europa=eu, dragon=dr)


def get_market_stress_for_country(
    country_id: str,
    indexes: MarketIndexesResult,
) -> float:
    """Return stability penalty from market index for a given country.

    Returns: 0.0 (no stress), -0.10 (stress), -0.30 (crisis).
    """
    primary = COUNTRY_PRIMARY_INDEX.get(country_id)
    if primary is None:
        return 0.0
    idx_val = getattr(indexes, primary).new_value
    if idx_val < MARKET_INDEX_CRISIS_THRESHOLD:
        return -0.30
    if idx_val < MARKET_INDEX_STRESS_THRESHOLD:
        return -0.10
    return 0.0


def update_sanctions_rounds(
    countries: dict[str, dict],
    sanctions: dict[str, dict],
) -> None:
    """Track how many consecutive rounds each country is under L2+ sanctions."""
    for cid, c in countries.items():
        level = _get_sanctions_on(sanctions, cid)
        if level >= 2:
            c["economic"]["sanctions_rounds"] = c["economic"].get("sanctions_rounds", 0) + 1
        else:
            c["economic"]["sanctions_rounds"] = 0


def update_formosa_disruption_rounds(
    countries: dict[str, dict],
    formosa_disrupted: bool,
) -> None:
    """Track consecutive rounds of Formosa semiconductor disruption."""
    for cid, c in countries.items():
        dep = c["economic"].get("formosa_dependency", 0)
        if formosa_disrupted and dep > 0:
            c["economic"]["formosa_disruption_rounds"] = (
                c["economic"].get("formosa_disruption_rounds", 0) + 1
            )
        else:
            c["economic"]["formosa_disruption_rounds"] = 0


def auto_produce_military(
    country_id: str,
    countries: dict[str, dict],
    wars: list[dict],
    log: list[str],
) -> None:
    """Auto-production: war countries produce ground units from treasury."""
    c = countries[country_id]
    eco = c["economic"]

    if _is_country_at_war(wars, country_id):
        cap = int(c.get("military", {}).get("production_capacity", {}).get("ground", 0))
        cost = float(c.get("military", {}).get("production_costs", {}).get("ground", 0))
        if cap > 0 and eco.get("treasury", 0) >= cost:
            c["military"]["ground"] = int(c["military"]["ground"]) + 1
            eco["treasury"] -= cost
            log.append(
                f"  Auto-production {country_id}: +1 ground (war), "
                f"cost={cost:.1f}, treasury={eco['treasury']:.1f}"
            )


# ---------------------------------------------------------------------------
# MAIN ENTRY POINT
# ---------------------------------------------------------------------------

def process_economy(
    countries: dict[str, dict],
    world_state: dict,
    actions: dict,
    previous_states: dict[str, dict] | None = None,
) -> EconomicResult:
    """Pure function: processes one round of economic calculations.

    Args:
        countries: Full country state dicts (MUTATED in place with new values).
        world_state: Global state dict with keys:
            - oil_price (float)
            - opec_production (dict)
            - chokepoint_status (dict)
            - active_blockades (dict)
            - formosa_blockade (bool)
            - wars (list[dict])
            - dollar_credibility (float)
            - oil_above_150_rounds (int)
            - rare_earth_restrictions (dict)
            - round_num (int)
        actions: Player/AI actions dict with keys:
            - budgets (dict[country_id, budget_dict])
            - tech_rd (dict[country_id, {nuclear: float, ai: float}])
            - opec_production (dict) — already applied before calling this
            - tariff_changes, sanction_changes — already applied before calling this
        previous_states: Snapshot of previous round for transition detection.
            Dict of country_id -> {economic_state, gdp, stability, at_war}.

    Returns:
        EconomicResult with all per-country results and global values.
    """
    log: list[str] = []
    log.append(f"=== ECONOMIC ENGINE — ROUND {world_state.get('round_num', 0)} ===")

    if previous_states is None:
        previous_states = {}

    sanctions = world_state.get("bilateral", {}).get("sanctions", {})
    tariffs = world_state.get("bilateral", {}).get("tariffs", {})
    wars = world_state.get("wars", [])
    round_num = world_state.get("round_num", 0)
    rare_earth_restrictions = world_state.get("rare_earth_restrictions", {})

    # Compute trade weights
    trade_weights = derive_trade_weights(countries)

    # Update duration trackers
    update_sanctions_rounds(countries, sanctions)
    formosa_disrupted = _is_formosa_disrupted(
        wars,
        world_state.get("chokepoint_status", {}),
        world_state.get("active_blockades", {}),
        world_state.get("formosa_blockade", False),
    )
    update_formosa_disruption_rounds(countries, formosa_disrupted)

    # --- STEP 1: Oil price ---
    oil_result, new_oil_above_150 = calc_oil_price(
        countries=countries,
        opec_production=world_state.get("opec_production", {}),
        chokepoint_status=world_state.get("chokepoint_status", {}),
        active_blockades=world_state.get("active_blockades", {}),
        formosa_blockade=world_state.get("formosa_blockade", False),
        wars=wars,
        previous_oil_price=world_state.get("oil_price", OIL_BASE_PRICE),
        oil_above_150_rounds=world_state.get("oil_above_150_rounds", 0),
        sanctions=sanctions,
        log=log,
    )
    oil_price = oil_result.price

    # --- PER-COUNTRY CHAINED PROCESSING ---
    country_results: dict[str, CountryEconomicResult] = {}
    dollar_credibility = world_state.get("dollar_credibility", DOLLAR_CREDIBILITY_CEILING)

    sanctions_affected = world_state.get("_sanctions_affected", set())

    for cid in list(countries.keys()):
        c = countries[cid]

        # Cal-11: Sanctions coefficient — recomputed every round
        new_coeff = calc_sanctions_coefficient(cid, countries, sanctions)
        c["economic"]["_new_sanctions_coefficient"] = new_coeff

        # Cal-11b: Tariff coefficient (same pattern as sanctions)
        tariff_coeff, tariff_inflation, tariff_revenue = calc_tariff_coefficient(cid, countries, tariffs)
        c["economic"]["_new_tariff_coefficient"] = tariff_coeff
        # Tariff inflation: set as a LEVEL, not additive per round
        # Only the CHANGE in tariff inflation matters (like the coefficient)
        old_tariff_inflation = c["economic"].get("_tariff_inflation_level", 0.0)
        inflation_delta = tariff_inflation - old_tariff_inflation
        c["economic"]["inflation"] += inflation_delta  # only add the change
        c["economic"]["_tariff_inflation_level"] = tariff_inflation
        # Customs revenue: add to treasury
        c["economic"]["treasury"] += tariff_revenue

        # STEP 2: GDP growth (sanctions/tariffs now via coefficients, pass dummies)
        tariff_result = TariffResult(cost_as_imposer=0, revenue_as_imposer=tariff_revenue,
                                      cost_as_target=0, net_gdp_cost=0)
        gdp_result = calc_gdp_growth(
            cid, countries, tariff_result,
            oil_price, wars, world_state.get("chokepoint_status", {}),
            formosa_disrupted, log,
        )
        c["economic"]["gdp"] = gdp_result.new_gdp
        c["economic"]["gdp_growth_rate"] = gdp_result.growth_pct

        # STEP 3: Revenue
        rev_result = calc_revenue(cid, countries, wars, sanctions, trade_weights, log)

        # STEP 4: Budget execution
        budget = actions.get("budgets", {}).get(cid, {})
        bud_result = calc_budget_execution(cid, countries, budget, rev_result.total, log)

        # STEP 5: Military production
        mil_alloc = budget.get("military", {})
        prod_result = calc_military_production(cid, countries, mil_alloc, round_num, log)

        # STEP 6: Technology advancement
        rd = actions.get("tech_rd", {}).get(cid, {"nuclear": 0, "ai": 0})
        tech_result = calc_tech_advancement(cid, countries, rd, rare_earth_restrictions, log)

        # STEP 7: Inflation update
        money_printed = bud_result.money_printed
        new_inflation = calc_inflation(cid, countries, money_printed)
        c["economic"]["inflation"] = new_inflation

        # Track money printed for dollar credibility
        c["economic"]["money_printed_this_round"] = bud_result.money_printed

        # STEP 8: Debt service
        deficit = bud_result.deficit
        new_debt = calc_debt_service(cid, countries, max(deficit, 0))
        c["economic"]["debt_burden"] = new_debt

        country_results[cid] = CountryEconomicResult(
            gdp=gdp_result,
            revenue=rev_result,
            budget=bud_result,
            military_production=prod_result,
            tech=tech_result,
            inflation=new_inflation,
            debt_burden=new_debt,
            sanctions=SanctionsResult(damage=1.0 - new_coeff, costs={}),
            tariffs=tariff_result,
            # Placeholder — filled in below
            economic_state=EconomicStateResult(
                old_state="", new_state="", stress_triggers=0,
                crisis_triggers=0, crisis_rounds=0, recovery_rounds=0,
            ),
            momentum=MomentumResult(
                old_momentum=0, new_momentum=0, boost=0, crash=0,
            ),
        )

    # --- Dollar credibility (global) ---
    dollar_credibility = update_dollar_credibility(countries, dollar_credibility, log)

    # --- Auto-produce military for war countries (FIX 4) ---
    for cid in countries:
        auto_produce_military(cid, countries, wars, log)

    # --- STEP 9: Economic state transitions ---
    for cid in countries:
        state_result = update_economic_state(cid, countries, oil_price, formosa_disrupted, log)
        country_results[cid].economic_state = state_result

    # --- STEP 10: Momentum ---
    for cid in countries:
        momentum_result = update_momentum(
            cid, countries, oil_price, formosa_disrupted, wars, previous_states, log,
        )
        country_results[cid].momentum = momentum_result

    # --- STEP 11: Contagion ---
    contagion_map = apply_contagion(countries, trade_weights, log)
    for cid, hits in contagion_map.items():
        if cid in country_results:
            country_results[cid].contagion = hits

    # --- Market indexes (3 regional) ---
    # Tag war status for health score calculation
    for cid, c in countries.items():
        c["_at_war"] = any(
            cid in w.get("belligerents_a", []) or cid in w.get("belligerents_b", [])
            for w in wars
        )
    previous_indexes = world_state.get("market_indexes")
    market_indexes = calc_market_indexes(countries, oil_price, previous_indexes, log)
    # Clean up temp flag
    for c in countries.values():
        c.pop("_at_war", None)

    return EconomicResult(
        oil_price=oil_result,
        countries=country_results,
        dollar_credibility=dollar_credibility,
        oil_above_150_rounds=new_oil_above_150,
        market_indexes=market_indexes,
        log=log,
    )
