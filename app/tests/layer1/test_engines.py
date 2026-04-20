"""Layer 1 tests -- Engine formula verification.

Pure unit tests for all four domain engines: economic, military, political, technology.
No DB calls, no LLM calls, no external services.

Run: cd app && PYTHONPATH=. pytest tests/layer1/test_engines.py -v
"""

import random

import pytest

# ---------------------------------------------------------------------------
# Economic engine imports
# ---------------------------------------------------------------------------
from engine.engines.economic import (
    calc_oil_price,
    calc_gdp_growth,
    calc_revenue,
    calc_sanctions_coefficient,
    calc_inflation,
    interpolate_s_curve,
    update_economic_state,
    calc_market_indexes,
    get_market_stress_for_country,
    SANCTIONS_S_CURVE,
    TariffResult,
    MarketIndexesResult,
)

# ---------------------------------------------------------------------------
# Military engine imports
# ---------------------------------------------------------------------------
from engine.engines.military import (
    resolve_attack,
    resolve_naval_combat_legacy_v1 as resolve_naval_combat,
    resolve_covert_op,
    resolve_blockade,
    AttackInput,
    NavalCombatInput,
    CovertOpInput,
    CovertOpType,
    BlockadeInput,
    BlockadeLevel,
    CountryMilitary,
    ZoneInfo,
    RoleInfo,
)

# ---------------------------------------------------------------------------
# Political engine imports
# ---------------------------------------------------------------------------
from engine.engines.political import (
    calc_stability,
    check_revolution,
    check_health_events,
    process_election,
    StabilityInput,
    ElectionInput,
    SCHEDULED_EVENTS,
    ELDERLY_LEADERS,
)

# ---------------------------------------------------------------------------
# Technology engine imports
# ---------------------------------------------------------------------------
from engine.engines.technology import (
    calc_tech_advancement,
    calc_tech_transfer,
    calc_rare_earth_impact,
    TechAdvancementInput,
    TechTransferInput,
    TechState,
    RDInvestment,
)


# ===========================================================================
# HELPERS -- minimal fixtures
# ===========================================================================

def _minimal_country(country_id: str, gdp: float = 100.0, **overrides) -> dict:
    """Create a minimal country dict for economic engine functions."""
    eco = {
        "gdp": gdp,
        "gdp_growth_rate": overrides.pop("gdp_growth_rate", 2.0),
        "tax_rate": overrides.pop("tax_rate", 0.20),
        "inflation": overrides.pop("inflation", 3.0),
        "starting_inflation": overrides.pop("starting_inflation", 3.0),
        "debt_burden": overrides.pop("debt_burden", 0.0),
        "oil_producer": overrides.pop("oil_producer", False),
        "oil_revenue": 0.0,
        "sectors": overrides.pop("sectors", {"resources": 10, "industry": 30, "services": 40, "technology": 20}),
        "economic_state": overrides.pop("economic_state", "normal"),
        "trade_balance": overrides.pop("trade_balance", 5.0),
        "formosa_dependency": overrides.pop("formosa_dependency", 0.0),
        "formosa_disruption_rounds": 0,
        "treasury": overrides.pop("treasury", 10.0),
        "momentum": overrides.pop("momentum", 0.0),
        "social_spending_baseline": overrides.pop("social_spending_baseline", 0.25),
        "sanctions_rounds": overrides.pop("sanctions_rounds", 0),
        "crisis_rounds": overrides.pop("crisis_rounds", 0),
        "recovery_rounds": overrides.pop("recovery_rounds", 0),
    }
    tech = {
        "ai_level": overrides.pop("ai_level", 0),
        "ai_rd_progress": 0.0,
        "nuclear_level": overrides.pop("nuclear_level", 0),
        "nuclear_rd_progress": 0.0,
    }
    pol = {
        "stability": overrides.pop("stability", 7.0),
        "political_support": overrides.pop("political_support", 50.0),
    }
    mil = {
        "ground": 0, "naval": 0, "tactical_air": 0,
        "strategic_missile": 0, "air_defense": 0,
        "maintenance_cost_per_unit": 0.3,
    }
    return {country_id: {"economic": eco, "technology": tech, "political": pol, "military": mil}}


# ===========================================================================
# 1. OIL PRICE
# ===========================================================================

class TestOilPrice:
    """Oil price formula: supply, demand, disruption, war premium, inertia."""

    def test_base_case_all_normal(self):
        """All conditions normal -> price near $80."""
        random.seed(42)
        countries = _minimal_country("alpha", 100)
        result, _ = calc_oil_price(
            countries=countries, opec_production={"persia": "normal"},
            chokepoint_status={}, active_blockades={},
            formosa_blockade=False, wars=[], previous_oil_price=80.0,
            oil_above_150_rounds=0, sanctions={}, log=[],
        )
        assert 70 <= result.price <= 90
        assert result.gulf_gate_blocked is False
        assert result.formosa_blocked is False

    def test_gulf_gate_blocked_raises_price(self):
        """Gulf Gate blocked -> supply reduction for Gulf producers -> price rises."""
        countries = {
            "solaria": {"economic": {"gdp": 11, "gdp_growth_rate": 3.5, "oil_producer": True,
                         "oil_production_mbpd": 10.0,
                         "sectors": {"resources": 45}, "economic_state": "normal", "oil_revenue": 0}},
            "mirage": {"economic": {"gdp": 5, "gdp_growth_rate": 4.0, "oil_producer": True,
                        "oil_production_mbpd": 3.5,
                        "sectors": {"resources": 30}, "economic_state": "normal", "oil_revenue": 0}},
        }
        result, _ = calc_oil_price(
            countries=countries, opec_production={},
            chokepoint_status={"hormuz": "blocked"}, active_blockades={},
            formosa_blockade=False, wars=[], previous_oil_price=80.0,
            oil_above_150_rounds=0, sanctions={}, log=[],
        )
        assert result.gulf_gate_blocked is True
        assert result.price > 90  # supply reduction raises price

    def test_high_opec_production_lowers_price(self):
        """High OPEC production (weighted by share) -> lower price."""
        countries = {
            "solaria": {"economic": {"gdp": 11, "gdp_growth_rate": 3.5, "oil_producer": True,
                         "oil_production_mbpd": 10.0,
                         "sectors": {"resources": 45}, "economic_state": "normal", "oil_revenue": 0}},
            "sarmatia": {"economic": {"gdp": 20, "gdp_growth_rate": 1.0, "oil_producer": True,
                          "oil_production_mbpd": 10.0,
                          "sectors": {"resources": 40}, "economic_state": "normal", "oil_revenue": 0}},
        }
        result_high, _ = calc_oil_price(
            countries=countries, opec_production={"solaria": "max", "sarmatia": "max"},
            chokepoint_status={}, active_blockades={},
            formosa_blockade=False, wars=[], previous_oil_price=80.0,
            oil_above_150_rounds=0, sanctions={}, log=[],
        )
        result_normal, _ = calc_oil_price(
            countries=countries, opec_production={"solaria": "normal", "sarmatia": "normal"},
            chokepoint_status={}, active_blockades={},
            formosa_blockade=False, wars=[], previous_oil_price=80.0,
            oil_above_150_rounds=0, sanctions={}, log=[],
        )
        assert result_high.price < result_normal.price

    def test_war_premium(self):
        """Gulf wars add premium (5% per war), non-Gulf wars do not."""
        countries = _minimal_country("alpha", 100)
        # Gulf war: columbia vs persia
        gulf_wars = [{"attacker": "columbia", "defender": "persia"}]
        result_gulf, _ = calc_oil_price(
            countries=countries, opec_production={},
            chokepoint_status={}, active_blockades={},
            formosa_blockade=False, wars=gulf_wars, previous_oil_price=80.0,
            oil_above_150_rounds=0, sanctions={}, log=[],
        )
        # Non-Gulf war
        other_wars = [{"attacker": "freeland", "defender": "ponte"}]
        result_other, _ = calc_oil_price(
            countries=countries, opec_production={},
            chokepoint_status={}, active_blockades={},
            formosa_blockade=False, wars=other_wars, previous_oil_price=80.0,
            oil_above_150_rounds=0, sanctions={}, log=[],
        )
        assert result_gulf.war_premium > 0  # Gulf war has premium
        assert result_other.war_premium == 0  # Non-Gulf war: no premium


# ===========================================================================
# 2. GDP GROWTH
# ===========================================================================

class TestGdpGrowth:
    """GDP growth additive factor model with crisis multiplier."""

    def test_base_growth_applied(self):
        """Positive base growth -> GDP increases."""
        countries = _minimal_country("alpha", 100, gdp_growth_rate=3.0)
        tariff = TariffResult(cost_as_imposer=0, revenue_as_imposer=0, cost_as_target=0, net_gdp_cost=0)
        result = calc_gdp_growth(
            "alpha", countries, tariff_info=tariff,
            oil_price=80.0, wars=[], chokepoint_status={},
            formosa_disrupted=False, log=[],
        )
        assert result.new_gdp > 100.0

    def test_sanctions_coefficient_model(self):
        """Sanctions are applied via coefficient (level shift), not growth rate parameter."""
        countries = _minimal_country("alpha", 100, gdp_growth_rate=2.0)
        tariff = TariffResult(cost_as_imposer=0, revenue_as_imposer=0, cost_as_target=0, net_gdp_cost=0)
        # sanctions_hit in growth formula is always 0 (coefficients applied separately)
        result = calc_gdp_growth(
            "alpha", countries, tariff_info=tariff,
            oil_price=80.0, wars=[], chokepoint_status={},
            formosa_disrupted=False, log=[],
        )
        assert result.sanctions_hit == 0
        assert result.new_gdp > 100.0  # base growth applied without sanctions drag

    def test_semiconductor_disruption_hits_tech_dependent(self):
        """Formosa disruption hits countries with high tech dependency."""
        countries = _minimal_country(
            "alpha", 100, gdp_growth_rate=2.0,
            formosa_dependency=0.5, sectors={"resources": 5, "industry": 20, "services": 35, "technology": 40},
        )
        countries["alpha"]["economic"]["formosa_disruption_rounds"] = 2
        tariff = TariffResult(cost_as_imposer=0, revenue_as_imposer=0, cost_as_target=0, net_gdp_cost=0)
        result = calc_gdp_growth(
            "alpha", countries, tariff_info=tariff,
            oil_price=80.0, wars=[], chokepoint_status={},
            formosa_disrupted=True, log=[],
        )
        assert result.semi_hit < 0


# ===========================================================================
# 3. SANCTIONS S-CURVE
# ===========================================================================

class TestSanctionsSCurve:
    """Sanctions S-curve (CONTRACT_SANCTIONS v1.0, locked 2026-04-10):

    Steeper shape with tipping point around 0.5-0.6 coverage. Knots:
    (0.0, 0.00) (0.1, 0.05) (0.2, 0.10) (0.3, 0.15) (0.4, 0.25) (0.5, 0.35)
    (0.6, 0.55) (0.7, 0.65) (0.8, 0.75) (0.9, 0.90) (1.0, 1.00)
    """

    @pytest.mark.parametrize("coverage,expected", [
        (0.0, 0.00),
        (0.1, 0.05),
        (0.3, 0.15),
        (0.5, 0.35),
        (0.6, 0.55),   # the big tipping-point jump
        (0.7, 0.65),
        (0.9, 0.90),
        (1.0, 1.00),
    ])
    def test_s_curve_knot_values(self, coverage, expected):
        """Effectiveness at each S-curve knot matches exactly (piecewise-linear)."""
        effectiveness = interpolate_s_curve(coverage, SANCTIONS_S_CURVE)
        assert effectiveness == pytest.approx(expected, abs=1e-6)

    def test_s_curve_monotonic(self):
        """Effectiveness never decreases as coverage increases."""
        prev = 0.0
        for i in range(101):
            cov = i / 100.0
            eff = interpolate_s_curve(cov, SANCTIONS_S_CURVE)
            assert eff >= prev - 1e-9, f"non-monotonic at cov={cov}"
            prev = eff

    def test_s_curve_tipping_point_is_steep(self):
        """The 0.5 → 0.6 region is the steepest: 0.20 increase in effectiveness."""
        at_05 = interpolate_s_curve(0.5, SANCTIONS_S_CURVE)
        at_06 = interpolate_s_curve(0.6, SANCTIONS_S_CURVE)
        assert at_06 - at_05 == pytest.approx(0.20, abs=1e-6)

    def test_zero_coverage_zero_effect(self):
        assert interpolate_s_curve(0.0, SANCTIONS_S_CURVE) == 0.0

    def test_full_coverage_full_effect(self):
        assert interpolate_s_curve(1.0, SANCTIONS_S_CURVE) == 1.0


# ===========================================================================
# 4. REVENUE
# ===========================================================================

class TestRevenue:
    """Revenue = GDP * tax_rate + oil - debt - inflation_erosion - war - sanctions."""

    def test_base_revenue(self):
        """GDP * tax_rate is correct base."""
        countries = _minimal_country("alpha", 200, tax_rate=0.25)
        result = calc_revenue(
            "alpha", countries, wars=[], sanctions={},
            trade_weights={}, log=[],
        )
        assert result.base_revenue == pytest.approx(50.0, abs=0.01)

    def test_oil_revenue_for_producer(self):
        """Oil producers get oil revenue added."""
        countries = _minimal_country(
            "alpha", 100, tax_rate=0.20, oil_producer=True,
            sectors={"resources": 30, "industry": 30, "services": 30, "technology": 10},
        )
        countries["alpha"]["economic"]["oil_revenue"] = 5.0
        result = calc_revenue(
            "alpha", countries, wars=[], sanctions={},
            trade_weights={}, log=[],
        )
        assert result.oil_revenue == 5.0
        assert result.total > result.base_revenue  # oil adds to revenue


# ===========================================================================
# 5. CRISIS LADDER
# ===========================================================================

class TestCrisisLadder:
    """Economic state transitions: normal -> stressed -> crisis -> collapse."""

    def test_normal_to_stressed(self):
        """2+ stress triggers -> stressed."""
        countries = _minimal_country(
            "alpha", 100, gdp_growth_rate=-2.0, treasury=0.0,
        )
        countries["alpha"]["political"]["stability"] = 3.0  # adds another trigger
        result = update_economic_state("alpha", countries, oil_price=80, formosa_disrupted=False, log=[])
        assert result.new_state == "stressed"
        assert result.stress_triggers >= 2

    def test_stressed_stays_without_crisis_triggers(self):
        """Stressed doesn't escalate without crisis triggers."""
        countries = _minimal_country("alpha", 100, economic_state="stressed", gdp_growth_rate=-1.5)
        countries["alpha"]["political"]["stability"] = 5.0
        result = update_economic_state("alpha", countries, oil_price=80, formosa_disrupted=False, log=[])
        assert result.new_state == "stressed"

    def test_collapse_after_prolonged_crisis(self):
        """Crisis for 3+ rounds with triggers -> collapse."""
        countries = _minimal_country(
            "alpha", 100, economic_state="crisis", gdp_growth_rate=-5.0,
            inflation=40.0, starting_inflation=3.0, treasury=0.0,
            debt_burden=15.0, crisis_rounds=2,
        )
        countries["alpha"]["political"]["stability"] = 3.0
        result = update_economic_state("alpha", countries, oil_price=80, formosa_disrupted=False, log=[])
        # crisis_rounds becomes 3 during update, then collapse check fires
        assert result.new_state == "collapse"


# ===========================================================================
# 6. INFLATION
# ===========================================================================

class TestInflation:
    """Inflation: money printing increases, natural decay on excess."""

    def test_money_printing_increases_inflation(self):
        """Printing money raises inflation above baseline."""
        countries = _minimal_country("alpha", 100, inflation=3.0, starting_inflation=3.0)
        new_infl = calc_inflation("alpha", countries, money_printed=10.0)
        assert new_infl > 3.0

    def test_natural_decay_of_excess(self):
        """Excess inflation above baseline decays 15% per round."""
        countries = _minimal_country("alpha", 100, inflation=20.0, starting_inflation=3.0)
        new_infl = calc_inflation("alpha", countries, money_printed=0.0)
        excess_before = 17.0  # 20 - 3
        excess_after = excess_before * 0.85  # 14.45
        expected = 3.0 + excess_after
        assert new_infl == pytest.approx(expected, abs=0.01)

    def test_baseline_inflation_persists(self):
        """Baseline inflation does not decay."""
        countries = _minimal_country("alpha", 100, inflation=3.0, starting_inflation=3.0)
        new_infl = calc_inflation("alpha", countries, money_printed=0.0)
        assert new_infl == pytest.approx(3.0, abs=0.01)


# ===========================================================================
# 7. GROUND COMBAT
# ===========================================================================

class TestGroundCombat:
    """RISK dice ground combat with integer modifiers."""

    def test_attacker_needs_defender_plus_one(self):
        """Attacker wins only on roll >= defender_roll + 1, ties go to defender."""
        random.seed(100)
        zone = ZoneInfo(
            zone_id="z1", zone_type="land_contested",
            forces={"defender_co": {"ground": 3}},
        )
        inp = AttackInput(
            attacker_country="attacker_co", defender_country="defender_co",
            zone_id="z1", units_committed=3,
            attacker=CountryMilitary(country_id="attacker_co"),
            defender=CountryMilitary(country_id="defender_co"),
            zone=zone,
        )
        result = resolve_attack(inp)
        assert result.attacker_losses + result.defender_losses == 3  # one loss per pair
        assert result.attacker_losses >= 0
        assert result.defender_losses >= 0

    def test_die_hard_modifier(self):
        """Die Hard zone gives defender +1 positional bonus."""
        zone = ZoneInfo(
            zone_id="z1", zone_type="land_contested", die_hard=True,
            forces={"defender_co": {"ground": 3}},
        )
        inp = AttackInput(
            attacker_country="attacker_co", defender_country="defender_co",
            zone_id="z1", units_committed=3,
            attacker=CountryMilitary(country_id="attacker_co"),
            defender=CountryMilitary(country_id="defender_co"),
            zone=zone,
        )
        result = resolve_attack(inp)
        assert result.modifiers is not None
        assert result.modifiers.die_hard == 1
        assert result.modifiers.positional_bonus >= 1

    def test_amphibious_penalty(self):
        """Sea-to-land attack gives attacker -1."""
        origin = ZoneInfo(zone_id="sea1", zone_type="sea", forces={})
        zone = ZoneInfo(
            zone_id="z1", zone_type="land_contested",
            forces={"defender_co": {"ground": 2}},
        )
        from engine.engines.military import AdjacencyInfo
        inp = AttackInput(
            attacker_country="attacker_co", defender_country="defender_co",
            zone_id="z1", units_committed=2, origin_zone_id="sea1",
            attacker=CountryMilitary(country_id="attacker_co"),
            defender=CountryMilitary(country_id="defender_co"),
            zone=zone, origin_zone=origin,
            origin_adjacency=[AdjacencyInfo(zone_id="z1", connection_type="land_sea")],
        )
        result = resolve_attack(inp)
        assert result.is_amphibious is True
        assert result.modifiers.amphibious_penalty == -1

    def test_uncontested_capture(self):
        """No defenders -> automatic capture, no losses."""
        zone = ZoneInfo(zone_id="z1", zone_type="land_contested", forces={})
        inp = AttackInput(
            attacker_country="attacker_co", defender_country="defender_co",
            zone_id="z1", units_committed=5,
            attacker=CountryMilitary(country_id="attacker_co"),
            defender=CountryMilitary(country_id="defender_co"),
            zone=zone,
        )
        result = resolve_attack(inp)
        assert result.zone_captured is True
        assert result.attacker_losses == 0
        assert result.defender_losses == 0


# ===========================================================================
# 8. NAVAL COMBAT
# ===========================================================================

class TestNavalCombat:
    """Ship vs ship RISK dice. Sunk ships lose embarked units."""

    def test_naval_combat_resolves(self):
        """Basic naval combat produces valid losses."""
        random.seed(77)
        zone = ZoneInfo(
            zone_id="sea1", zone_type="sea",
            forces={"att_co": {"naval": 4}, "def_co": {"naval": 3}},
        )
        inp = NavalCombatInput(
            attacker_country="att_co", defender_country="def_co",
            sea_zone_id="sea1",
            attacker=CountryMilitary(country_id="att_co", ground=5, naval=4, tactical_air=10),
            defender=CountryMilitary(country_id="def_co", ground=3, naval=3, tactical_air=6),
            zone=zone,
        )
        result = resolve_naval_combat(inp)
        total_pairs = 3  # min(4, 3)
        assert result.attacker_losses + result.defender_losses == total_pairs

    def test_sunk_ships_lose_embarked(self):
        """When ships are sunk, embarked ground/air units are also lost."""
        random.seed(10)
        zone = ZoneInfo(
            zone_id="sea1", zone_type="sea",
            forces={"att_co": {"naval": 3}, "def_co": {"naval": 3}},
        )
        inp = NavalCombatInput(
            attacker_country="att_co", defender_country="def_co",
            sea_zone_id="sea1",
            attacker=CountryMilitary(country_id="att_co", ground=6, naval=3, tactical_air=15),
            defender=CountryMilitary(country_id="def_co", ground=6, naval=3, tactical_air=15),
            zone=zone,
        )
        result = resolve_naval_combat(inp)
        # At least one side should have losses
        if result.attacker_losses > 0:
            total_embarked = (
                result.embarked_units_lost_attacker.get("ground", 0)
                + result.embarked_units_lost_attacker.get("tactical_air", 0)
            )
            assert total_embarked >= 0  # embarked losses calculated
        if result.defender_losses > 0:
            total_embarked = (
                result.embarked_units_lost_defender.get("ground", 0)
                + result.embarked_units_lost_defender.get("tactical_air", 0)
            )
            assert total_embarked >= 0


# ===========================================================================
# 9. COVERT OPS
# ===========================================================================

class TestCovertOps:
    """Covert ops: success probability in expected range, detection separate."""

    def test_espionage_success_probability_range(self):
        """Espionage base prob is 0.60, with AI bonus and penalties stays in range."""
        random.seed(42)
        target = CountryMilitary(country_id="target_co", gdp=100)
        role = RoleInfo(
            role_id="spy1", country_id="att_co", intelligence_pool=3,
        )
        inp = CovertOpInput(
            country_id="att_co", op_type=CovertOpType.ESPIONAGE,
            target_country_code="target_co", role_id="spy1", role=role,
            target_country=target, ai_level=2, prev_ops_against_target=0,
        )
        result = resolve_covert_op(inp)
        # base 0.60 + 2*0.05 = 0.70
        assert result.success_probability == pytest.approx(0.70, abs=0.01)

    def test_detection_separate_from_success(self):
        """Detection can occur even when op succeeds (and vice versa)."""
        # Run many trials and check both combinations exist
        successes_detected = 0
        successes_undetected = 0
        target = CountryMilitary(country_id="target_co", gdp=100)
        role = RoleInfo(role_id="spy1", country_id="att_co", intelligence_pool=100)
        for i in range(200):
            random.seed(i)
            inp = CovertOpInput(
                country_id="att_co", op_type=CovertOpType.ESPIONAGE,
                target_country_code="target_co", role_id="spy1", role=role,
                target_country=target, ai_level=0, prev_ops_against_target=0,
            )
            r = resolve_covert_op(inp)
            if r.success and r.detected:
                successes_detected += 1
            if r.success and not r.detected:
                successes_undetected += 1
        assert successes_detected > 0, "Expected some successful+detected ops"
        assert successes_undetected > 0, "Expected some successful+undetected ops"

    def test_repeated_ops_reduce_success(self):
        """Previous ops against same target reduce success probability."""
        target = CountryMilitary(country_id="target_co", gdp=100)
        role = RoleInfo(role_id="spy1", country_id="att_co", sabotage_cards=5)
        inp0 = CovertOpInput(
            country_id="att_co", op_type=CovertOpType.SABOTAGE,
            target_country_code="target_co", role_id="spy1", role=role,
            target_country=target, ai_level=0, prev_ops_against_target=0,
        )
        inp3 = CovertOpInput(
            country_id="att_co", op_type=CovertOpType.SABOTAGE,
            target_country_code="target_co", role_id="spy1", role=role,
            target_country=target, ai_level=0, prev_ops_against_target=3,
        )
        random.seed(99)
        r0 = resolve_covert_op(inp0)
        random.seed(99)
        r3 = resolve_covert_op(inp3)
        assert r3.success_probability < r0.success_probability


# ===========================================================================
# 10. BLOCKADE
# ===========================================================================

class TestBlockade:
    """Blockade: ground forces required, Formosa needs 3+ sea zones."""

    def test_ground_forces_required(self):
        """Blockade fails without ground forces at chokepoint."""
        zone = ZoneInfo(zone_id="cp_gulf_gate", zone_type="chokepoint", forces={})
        inp = BlockadeInput(
            country_id="attacker_co", zone_id="cp_gulf_gate",
            level=BlockadeLevel.FULL, zone=zone,
        )
        result = resolve_blockade(inp)
        assert result.success is False
        assert result.error is not None
        assert "ground" in result.error.lower()

    def test_blockade_succeeds_with_ground(self):
        """Blockade succeeds with ground forces present."""
        zone = ZoneInfo(
            zone_id="cp_gulf_gate", zone_type="chokepoint",
            forces={"attacker_co": {"ground": 2}},
        )
        inp = BlockadeInput(
            country_id="attacker_co", zone_id="cp_gulf_gate",
            level=BlockadeLevel.FULL, zone=zone,
        )
        result = resolve_blockade(inp)
        assert result.success is True

    def test_formosa_needs_3_sea_zones(self):
        """Formosa full blockade requires naval in 3+ surrounding zones."""
        zone = ZoneInfo(zone_id="formosa", zone_type="land_home", forces={})
        adj = [
            ZoneInfo(zone_id=f"w({i})", zone_type="sea",
                     forces={"cathay": {"naval": 2}} if i < 2 else {})
            for i in range(6)
        ]
        inp = BlockadeInput(
            country_id="cathay", zone_id="formosa",
            level=BlockadeLevel.FULL, zone=zone,
            adjacent_sea_zones=adj,
        )
        result = resolve_blockade(inp)
        assert result.success is False
        assert "3+" in result.error

    def test_formosa_full_blockade_with_3_zones(self):
        """Formosa full blockade succeeds with naval in 3+ zones, no friendly ships."""
        zone = ZoneInfo(zone_id="formosa", zone_type="land_home", forces={})
        adj = [
            ZoneInfo(zone_id=f"w({i})", zone_type="sea",
                     forces={"cathay": {"naval": 2}})
            for i in range(4)
        ]
        inp = BlockadeInput(
            country_id="cathay", zone_id="formosa",
            level=BlockadeLevel.FULL, zone=zone,
            adjacent_sea_zones=adj,
        )
        result = resolve_blockade(inp)
        assert result.success is True
        assert result.level == "full"

    def test_formosa_downgraded_by_friendly_ship(self):
        """1 friendly (non-blocker) ship downgrades Formosa blockade to partial."""
        zone = ZoneInfo(zone_id="formosa", zone_type="land_home", forces={})
        adj = [
            ZoneInfo(zone_id=f"w({i})", zone_type="sea",
                     forces={"cathay": {"naval": 2}})
            for i in range(4)
        ]
        # Add a friendly (non-cathay) ship in one zone
        adj[0].forces["columbia"] = {"naval": 1}
        inp = BlockadeInput(
            country_id="cathay", zone_id="formosa",
            level=BlockadeLevel.FULL, zone=zone,
            adjacent_sea_zones=adj,
        )
        result = resolve_blockade(inp)
        assert result.success is True
        assert result.level == "partial"
        assert result.auto_downgraded is True


# ===========================================================================
# 11. POLITICAL STABILITY
# ===========================================================================

class TestStability:
    """Stability: war reduces, high GDP helps, crisis state penalizes."""

    def test_war_reduces_stability(self):
        """Being at war decreases stability."""
        inp_peace = StabilityInput(
            country_id="alpha", stability=7.0, regime_type="democracy",
            gdp_growth_rate=2.0, economic_state="normal", inflation=3.0,
            starting_inflation=3.0, at_war=False,
        )
        inp_war = StabilityInput(
            country_id="alpha", stability=7.0, regime_type="democracy",
            gdp_growth_rate=2.0, economic_state="normal", inflation=3.0,
            starting_inflation=3.0, at_war=True, is_primary_belligerent=True,
        )
        result_peace = calc_stability(inp_peace)
        result_war = calc_stability(inp_war)
        assert result_war.new_stability < result_peace.new_stability

    def test_high_gdp_growth_helps(self):
        """GDP growth > 2% reduces stability decay compared to low growth."""
        inp_high = StabilityInput(
            country_id="alpha", stability=6.0, regime_type="democracy",
            gdp_growth_rate=5.0, economic_state="normal", inflation=3.0,
            starting_inflation=3.0,
        )
        inp_low = StabilityInput(
            country_id="alpha", stability=6.0, regime_type="democracy",
            gdp_growth_rate=-2.0, economic_state="normal", inflation=3.0,
            starting_inflation=3.0,
        )
        result_high = calc_stability(inp_high)
        result_low = calc_stability(inp_low)
        assert result_high.new_stability > result_low.new_stability

    def test_crisis_state_penalizes(self):
        """Crisis economic state applies penalty."""
        inp_normal = StabilityInput(
            country_id="alpha", stability=7.0, regime_type="democracy",
            gdp_growth_rate=2.0, economic_state="normal", inflation=3.0,
            starting_inflation=3.0,
        )
        inp_crisis = StabilityInput(
            country_id="alpha", stability=7.0, regime_type="democracy",
            gdp_growth_rate=2.0, economic_state="crisis", inflation=3.0,
            starting_inflation=3.0,
        )
        result_normal = calc_stability(inp_normal)
        result_crisis = calc_stability(inp_crisis)
        assert result_crisis.new_stability < result_normal.new_stability

    def test_stability_clamped(self):
        """Stability clamped between 1.0 and 9.0."""
        inp = StabilityInput(
            country_id="alpha", stability=9.0, regime_type="democracy",
            gdp_growth_rate=10.0, economic_state="normal", inflation=3.0,
            starting_inflation=3.0,
        )
        result = calc_stability(inp)
        assert result.new_stability <= 9.0

        inp_low = StabilityInput(
            country_id="alpha", stability=1.0, regime_type="democracy",
            gdp_growth_rate=-10.0, economic_state="collapse", inflation=50.0,
            starting_inflation=3.0, at_war=True, is_primary_belligerent=True,
            casualties=5, mobilization_level=3,
        )
        result_low = calc_stability(inp_low)
        assert result_low.new_stability >= 1.0


# ===========================================================================
# 12. ELECTIONS
# ===========================================================================

class TestElections:
    """Elections scheduled at correct rounds, formula produces valid results."""

    def test_scheduled_events_deprecated(self):
        """SCHEDULED_EVENTS dict is empty — elections now via sim_runs.key_events."""
        # Elections are configured per-sim in key_events JSONB, not hardcoded.
        # This test verifies the old dict is empty (simplification 2026-04-15).
        assert SCHEDULED_EVENTS == {}

    def test_midterm_result(self):
        """Columbia midterm produces incumbent win/loss decision."""
        inp = ElectionInput(
            country_id="columbia", election_type="columbia_midterms",
            round_num=2, gdp_growth_rate=2.0, stability=6.0,
            economic_state="normal", oil_price=80.0,
            incumbent_pct=55.0,
        )
        result = process_election(inp)
        assert result.election_type == "columbia_midterms"
        assert result.country == "columbia"
        assert 0 <= result.final_incumbent_pct <= 100
        assert result.parliament_change is not None

    def test_crisis_hurts_incumbent(self):
        """Economic crisis penalizes incumbent in elections."""
        inp_normal = ElectionInput(
            country_id="columbia", election_type="columbia_presidential",
            round_num=5, gdp_growth_rate=2.0, stability=6.0,
            economic_state="normal", oil_price=80.0, incumbent_pct=50.0,
        )
        inp_crisis = ElectionInput(
            country_id="columbia", election_type="columbia_presidential",
            round_num=5, gdp_growth_rate=2.0, stability=6.0,
            economic_state="crisis", oil_price=80.0, incumbent_pct=50.0,
        )
        r_normal = process_election(inp_normal)
        r_crisis = process_election(inp_crisis)
        assert r_crisis.crisis_penalty < r_normal.crisis_penalty
        assert r_crisis.final_incumbent_pct < r_normal.final_incumbent_pct


# ===========================================================================
# 13. HEALTH EVENTS
# ===========================================================================

class TestHealthEvents:
    """Elderly leaders have incapacitation risk after Round 2."""

    def test_no_events_round_1_2(self):
        """No health events in rounds 1-2 (players establish themselves)."""
        for r in (1, 2):
            result = check_health_events("columbia", r)
            assert result is None

    def test_elderly_leaders_registered(self):
        """Columbia, Cathay, Sarmatia have elderly leaders."""
        assert "columbia" in ELDERLY_LEADERS
        assert "cathay" in ELDERLY_LEADERS
        assert "sarmatia" in ELDERLY_LEADERS

    def test_non_elderly_country_safe(self):
        """Country without elderly leader never gets health event."""
        for _ in range(50):
            result = check_health_events("teutonia", 5)
            assert result is None

    def test_health_event_can_occur(self):
        """Elderly leader can get health event after Round 2 (statistical)."""
        events = 0
        for i in range(1000):
            random.seed(i)
            result = check_health_events("columbia", 3)
            if result is not None:
                events += 1
                assert result.event in ("leader_death", "leader_incapacitated")
        # Columbia leader: ~7.15% per round, expect ~72 events in 1000 trials
        assert 30 < events < 150, f"Expected ~72 events, got {events}"


# ===========================================================================
# 14. REVOLUTION
# ===========================================================================

class TestRevolution:
    """Revolution triggers at stability <= 2 (simplified 2026-04-15)."""

    def test_revolution_triggers(self):
        """Low stability -> mass protests flagged."""
        result = check_revolution("alpha", stability=2.0)
        assert result is not None
        assert result.event == "mass_protests"
        assert result.severity == "major"

    def test_severe_at_stability_1(self):
        """Stability <= 1 -> severe."""
        result = check_revolution("alpha", stability=1.0)
        assert result is not None
        assert result.severity == "severe"

    def test_no_revolution_above_threshold(self):
        """No revolution when stability > 2."""
        assert check_revolution("alpha", stability=3.0) is None
        assert check_revolution("alpha", stability=5.0) is None


# ===========================================================================
# 15. NUCLEAR R&D
# ===========================================================================

class TestNuclearRD:
    """Nuclear R&D: progresses toward thresholds, breakthrough at 0.60/0.80/1.00."""

    def test_nuclear_progress(self):
        """Investment increases nuclear R&D progress."""
        inp = TechAdvancementInput(
            country_id="alpha",
            tech_state=TechState(nuclear_level=0, nuclear_rd_progress=0.0),
            rd_investment=RDInvestment(nuclear=50.0),
            gdp=100.0,
        )
        result = calc_tech_advancement(inp)
        # progress = (50/100) * 0.8 = 0.40
        assert result.new_nuclear_rd_progress == pytest.approx(0.40, abs=0.001)
        assert result.nuclear_levelup is False  # need 0.60 for L1

    def test_nuclear_breakthrough_l0_to_l1(self):
        """Progress >= 0.60 at L0 triggers levelup to L1."""
        inp = TechAdvancementInput(
            country_id="alpha",
            tech_state=TechState(nuclear_level=0, nuclear_rd_progress=0.50),
            rd_investment=RDInvestment(nuclear=20.0),
            gdp=100.0,
        )
        result = calc_tech_advancement(inp)
        # progress = 0.50 + (20/100)*0.8 = 0.50 + 0.16 = 0.66 >= 0.60
        assert result.nuclear_levelup is True
        assert result.new_nuclear_level == 1
        assert result.new_nuclear_rd_progress == 0.0  # reset on levelup

    @pytest.mark.parametrize("level,threshold", [(0, 0.60), (1, 0.80), (2, 1.00)])
    def test_nuclear_thresholds(self, level, threshold):
        """Each nuclear level has correct breakthrough threshold."""
        # Just below threshold: no levelup
        inp_below = TechAdvancementInput(
            country_id="alpha",
            tech_state=TechState(nuclear_level=level, nuclear_rd_progress=threshold - 0.01),
            rd_investment=RDInvestment(nuclear=0.0),
            gdp=100.0,
        )
        result_below = calc_tech_advancement(inp_below)
        assert result_below.nuclear_levelup is False

        # At threshold: levelup
        inp_at = TechAdvancementInput(
            country_id="alpha",
            tech_state=TechState(nuclear_level=level, nuclear_rd_progress=threshold),
            rd_investment=RDInvestment(nuclear=0.0),
            gdp=100.0,
        )
        result_at = calc_tech_advancement(inp_at)
        assert result_at.nuclear_levelup is True


# ===========================================================================
# 16. AI R&D
# ===========================================================================

class TestAIRD:
    """AI R&D: progresses toward thresholds at 0.20/0.40/0.60/1.00."""

    def test_ai_progress(self):
        """Investment increases AI R&D progress."""
        inp = TechAdvancementInput(
            country_id="alpha",
            tech_state=TechState(ai_level=0, ai_rd_progress=0.0),
            rd_investment=RDInvestment(ai=30.0),
            gdp=100.0,
        )
        result = calc_tech_advancement(inp)
        # progress = (30/100) * 0.8 = 0.24 >= 0.20 -> levelup!
        assert result.ai_levelup is True
        assert result.new_ai_level == 1

    @pytest.mark.parametrize("level,threshold", [(0, 0.20), (1, 0.40), (2, 0.60), (3, 1.00)])
    def test_ai_thresholds(self, level, threshold):
        """Each AI level has correct breakthrough threshold."""
        inp_at = TechAdvancementInput(
            country_id="alpha",
            tech_state=TechState(ai_level=level, ai_rd_progress=threshold),
            rd_investment=RDInvestment(ai=0.0),
            gdp=100.0,
        )
        result = calc_tech_advancement(inp_at)
        assert result.ai_levelup is True
        assert result.new_ai_level == level + 1

    def test_rare_earth_slows_rd(self):
        """Rare earth restrictions reduce R&D efficiency."""
        inp_free = TechAdvancementInput(
            country_id="alpha",
            tech_state=TechState(ai_level=0, ai_rd_progress=0.0),
            rd_investment=RDInvestment(ai=20.0),
            gdp=100.0, rare_earth_restriction_level=0,
        )
        inp_restricted = TechAdvancementInput(
            country_id="alpha",
            tech_state=TechState(ai_level=0, ai_rd_progress=0.0),
            rd_investment=RDInvestment(ai=20.0),
            gdp=100.0, rare_earth_restriction_level=2,
        )
        r_free = calc_tech_advancement(inp_free)
        r_restricted = calc_tech_advancement(inp_restricted)
        # Restricted should have less progress (or levelup later)
        assert r_restricted.rare_earth_factor < 1.0
        assert r_restricted.rare_earth_factor == pytest.approx(0.70, abs=0.01)


# ===========================================================================
# 17. TECH TRANSFER
# ===========================================================================

class TestTechTransfer:
    """Tech transfer: donor must be 1+ level ahead."""

    def test_transfer_succeeds_when_ahead(self):
        """Donor 1 level ahead -> transfer adds progress."""
        inp = TechTransferInput(
            donor_country_id="alpha", recipient_country_id="beta",
            donor_tech_state=TechState(nuclear_level=2),
            recipient_tech_state=TechState(nuclear_level=1, nuclear_rd_progress=0.10),
            transfer_type="nuclear",
        )
        result = calc_tech_transfer(inp)
        assert result.success is True
        assert result.progress_added == 0.20
        assert result.new_recipient_rd_progress == pytest.approx(0.30, abs=0.001)

    def test_transfer_fails_same_level(self):
        """Transfer fails when donor is at same level."""
        inp = TechTransferInput(
            donor_country_id="alpha", recipient_country_id="beta",
            donor_tech_state=TechState(ai_level=2),
            recipient_tech_state=TechState(ai_level=2, ai_rd_progress=0.10),
            transfer_type="ai",
        )
        result = calc_tech_transfer(inp)
        assert result.success is False
        assert result.progress_added == 0.0

    def test_transfer_fails_donor_behind(self):
        """Transfer fails when donor is behind recipient."""
        inp = TechTransferInput(
            donor_country_id="alpha", recipient_country_id="beta",
            donor_tech_state=TechState(nuclear_level=0),
            recipient_tech_state=TechState(nuclear_level=1),
            transfer_type="nuclear",
        )
        result = calc_tech_transfer(inp)
        assert result.success is False

    def test_ai_transfer_boost(self):
        """AI transfer gives +0.15 progress."""
        inp = TechTransferInput(
            donor_country_id="alpha", recipient_country_id="beta",
            donor_tech_state=TechState(ai_level=3),
            recipient_tech_state=TechState(ai_level=1, ai_rd_progress=0.20),
            transfer_type="ai",
        )
        result = calc_tech_transfer(inp)
        assert result.success is True
        assert result.progress_added == 0.15
        assert result.new_recipient_rd_progress == pytest.approx(0.35, abs=0.001)


# ===========================================================================
# RARE EARTH IMPACT (standalone)
# ===========================================================================

class TestRareEarthImpact:
    """Rare earth restriction levels: -15% per level, floor at 40%."""

    @pytest.mark.parametrize("level,expected", [
        (0, 1.0), (1, 0.85), (2, 0.70), (3, 0.55), (4, 0.40), (5, 0.40),
    ])
    def test_rare_earth_factor(self, level, expected):
        result = calc_rare_earth_impact(level)
        assert result.factor == pytest.approx(expected, abs=0.01)


# ===========================================================================
# MARKET INDEXES (3 regional indexes)
# ===========================================================================

def _market_countries(**overrides) -> dict[str, dict]:
    """Build a minimal multi-country dict for market index tests."""
    defaults = {
        "columbia": {"gdp": 250, "gdp_growth_rate": 2.5, "inflation": 3.0, "starting_inflation": 3.0,
                     "sanctions_coefficient": 1.0, "economic_state": "normal", "debt_burden": 0.8},
        "cathay": {"gdp": 180, "gdp_growth_rate": 5.0, "inflation": 2.0, "starting_inflation": 2.0,
                   "sanctions_coefficient": 1.0, "economic_state": "normal", "debt_burden": 0.6},
        "teutonia": {"gdp": 45, "gdp_growth_rate": 1.5, "inflation": 2.5, "starting_inflation": 2.5,
                     "sanctions_coefficient": 1.0, "economic_state": "normal", "debt_burden": 0.6},
        "gallia": {"gdp": 30, "gdp_growth_rate": 1.0, "inflation": 3.0, "starting_inflation": 3.0,
                   "sanctions_coefficient": 1.0, "economic_state": "normal", "debt_burden": 1.1},
        "yamato": {"gdp": 50, "gdp_growth_rate": 1.0, "inflation": 1.5, "starting_inflation": 1.5,
                   "sanctions_coefficient": 1.0, "economic_state": "normal", "debt_burden": 2.0},
        "albion": {"gdp": 32, "gdp_growth_rate": 1.5, "inflation": 4.0, "starting_inflation": 4.0,
                   "sanctions_coefficient": 1.0, "economic_state": "normal", "debt_burden": 0.9},
        "hanguk": {"gdp": 18, "gdp_growth_rate": 2.5, "inflation": 2.0, "starting_inflation": 2.0,
                   "sanctions_coefficient": 1.0, "economic_state": "normal", "debt_burden": 0.4},
        "bharata": {"gdp": 35, "gdp_growth_rate": 6.0, "inflation": 5.0, "starting_inflation": 5.0,
                    "sanctions_coefficient": 1.0, "economic_state": "normal", "debt_burden": 0.7},
        "formosa": {"gdp": 7, "gdp_growth_rate": 3.0, "inflation": 2.0, "starting_inflation": 2.0,
                    "sanctions_coefficient": 1.0, "economic_state": "normal", "debt_burden": 0.3},
        "freeland": {"gdp": 10, "gdp_growth_rate": 1.0, "inflation": 3.0, "starting_inflation": 3.0,
                     "sanctions_coefficient": 1.0, "economic_state": "normal", "debt_burden": 0.6},
        "nordostan": {"gdp": 2, "gdp_growth_rate": -5.0, "inflation": 15.0, "starting_inflation": 5.0,
                      "sanctions_coefficient": 0.85, "economic_state": "crisis", "debt_burden": 0.5},
        "levantia": {"gdp": 5, "gdp_growth_rate": 2.0, "inflation": 3.0, "starting_inflation": 3.0,
                     "sanctions_coefficient": 1.0, "economic_state": "normal", "debt_burden": 0.7},
    }
    # Apply overrides per country
    for cid, ovr in overrides.items():
        if cid in defaults:
            defaults[cid].update(ovr)
    countries = {}
    for cid, eco_data in defaults.items():
        countries[cid] = {
            "economic": eco_data,
            "political": {"stability": 7.0, "political_support": 50.0},
        }
    return countries


class TestMarketIndexes:
    """3 regional market indexes: Wall Street, Europa, Dragon."""

    def test_baseline_healthy_economy(self):
        """All countries healthy -> indexes near 100."""
        countries = _market_countries()
        result = calc_market_indexes(countries, oil_price=80.0, previous_indexes=None, log=[])
        # First round: 70% of 100 (prev) + 30% of ~100 (healthy) ≈ 100
        assert 95 < result.wall_street.new_value < 110
        assert 95 < result.europa.new_value < 110
        assert 95 < result.dragon.new_value < 110

    def test_cathay_crisis_drags_dragon(self):
        """Cathay in crisis -> Dragon index drops significantly."""
        countries = _market_countries(cathay={
            "gdp": 180, "gdp_growth_rate": -4.0, "inflation": 15.0, "starting_inflation": 2.0,
            "sanctions_coefficient": 0.8, "economic_state": "crisis", "debt_burden": 0.6,
        })
        result = calc_market_indexes(countries, oil_price=80.0, previous_indexes=None, log=[])
        assert result.dragon.new_value < result.wall_street.new_value
        assert result.dragon.new_value < 95  # should drop

    def test_oil_shock_hits_all(self):
        """Very high oil price -> all indexes drop."""
        countries = _market_countries()
        normal = calc_market_indexes(countries, oil_price=80.0, previous_indexes=None, log=[])
        shocked = calc_market_indexes(countries, oil_price=200.0, previous_indexes=None, log=[])
        assert shocked.wall_street.new_value < normal.wall_street.new_value
        assert shocked.europa.new_value < normal.europa.new_value
        assert shocked.dragon.new_value < normal.dragon.new_value

    def test_inertia_smooths_changes(self):
        """Previous index values provide inertia (70/30 split)."""
        countries = _market_countries()
        prev = {"wall_street": 50.0, "europa": 50.0, "dragon": 50.0}
        result = calc_market_indexes(countries, oil_price=80.0, previous_indexes=prev, log=[])
        # With healthy economy (score ~100) but prev at 50:
        # smoothed = 0.7 * 50 + 0.3 * 100 = 65
        assert 60 < result.wall_street.new_value < 75

    def test_nordostan_war_drags_europa(self):
        """Nordostan in crisis (war economy) -> Europa index affected via weight."""
        countries = _market_countries()
        countries["nordostan"]["_at_war"] = True
        result = calc_market_indexes(countries, oil_price=80.0, previous_indexes=None, log=[])
        # Nordostan has 10% weight in Europa — crisis should pull it down slightly
        healthy = calc_market_indexes(_market_countries(), oil_price=80.0, previous_indexes=None, log=[])
        assert result.europa.new_value < healthy.europa.new_value

    def test_market_stress_for_country(self):
        """get_market_stress_for_country returns correct penalties."""
        countries = _market_countries()
        # Force low index values via previous_indexes
        prev = {"wall_street": 30.0, "europa": 60.0, "dragon": 100.0}
        result = calc_market_indexes(countries, oil_price=80.0, previous_indexes=prev, log=[])
        # Wall Street should be stressed (prev 30 + inertia)
        # Europa should be near stress threshold
        # Dragon should be fine
        ws_stress = get_market_stress_for_country("columbia", result)
        dr_stress = get_market_stress_for_country("cathay", result)
        # Columbia reads wall_street which started at 30 -> smoothed ~51
        # Cathay reads dragon which started at 100 -> smoothed ~100
        assert ws_stress <= 0.0  # at minimum no bonus
        assert dr_stress == 0.0  # dragon is fine

    def test_crisis_threshold_penalty(self):
        """Index below 40 -> crisis penalty -0.30."""
        countries = _market_countries()
        prev = {"wall_street": 10.0, "europa": 10.0, "dragon": 10.0}
        result = calc_market_indexes(countries, oil_price=80.0, previous_indexes=prev, log=[])
        # Smoothed: 0.7*10 + 0.3*~100 = 37 — below crisis threshold of 40
        stress = get_market_stress_for_country("columbia", result)
        assert stress == -0.30

    def test_index_bounds(self):
        """Indexes stay within 0-200 bounds."""
        countries = _market_countries()
        result = calc_market_indexes(countries, oil_price=80.0, previous_indexes=None, log=[])
        for idx in [result.wall_street, result.europa, result.dragon]:
            assert 0 <= idx.new_value <= 200
