"""Layer 1: Political engine calibration tests.

No DB, no LLM. Tests stability, political support, war tiredness, elections,
coups against CARD_FORMULAS (section B) and engines/political.py.

Run: cd app && PYTHONPATH=. pytest tests/layer1/test_calibration_political.py -v -s
"""
import random
import pytest
from engine.engines.political import (
    calc_stability,
    calc_political_support,
    update_war_tiredness,
    update_threshold_flags,
    resolve_coup,
    check_revolution,
    StabilityInput,
    PoliticalSupportInput,
    WarTirednessInput,
    CoupInput,
)


# ===========================================================================
# HELPERS
# ===========================================================================

def _default_stability_input(**overrides) -> StabilityInput:
    """Stable democracy baseline: no war, normal budget, mild GDP growth."""
    defaults = dict(
        country_id="columbia",
        stability=7.0,
        regime_type="democracy",
        gdp_growth_rate=2.5,
        economic_state="normal",
        inflation=3.0,
        starting_inflation=2.5,
        sanctions_rounds=0,
        at_war=False,
        is_primary_belligerent=False,
        is_frontline_defender=False,
        war_tiredness=0.0,
        sanctions_level=0,
        sanctions_pain=0.0,
        gdp=500.0,
        market_stress=0.0,
        social_spending_ratio=0.30,
        social_spending_baseline=0.30,
        casualties=0,
        territory_lost=0,
        territory_gained=0,
        mobilization_level=0,
        propaganda_boost=0.0,
    )
    defaults.update(overrides)
    return StabilityInput(**defaults)


def _default_support_input(**overrides) -> PoliticalSupportInput:
    """Stable democracy baseline for political support."""
    defaults = dict(
        country_id="columbia",
        political_support=55.0,
        stability=7.0,
        regime_type="democracy",
        gdp_growth_rate=2.5,
        economic_state="normal",
        oil_price=80.0,
        oil_producer=False,
        round_num=3,
        casualties=0,
        war_tiredness=0.0,
        perceived_weakness=0.0,
        repression_effect=0.0,
        nationalist_rally=0.0,
    )
    defaults.update(overrides)
    return PoliticalSupportInput(**defaults)


# ===========================================================================
# STABILITY FORMULA (CARD_FORMULAS B.1 / political.py calc_stability)
# ===========================================================================

class TestStabilityPeacefulDemocracy:
    """Stable democracy, no war, normal budget, good GDP."""

    def test_stability_peaceful_democracy(self):
        """No shocks -> stability stays same or +1 (positive inertia + mild GDP)."""
        inp = _default_stability_input()
        result = calc_stability(inp)
        print(f"  Peaceful democracy: {result.old_stability} -> {result.new_stability} (delta={result.delta})")
        # With stability=7 (inertia +0.05), GDP 2.5% (slight bonus), normal spending
        # delta should be small positive
        assert result.new_stability >= result.old_stability, (
            f"Peaceful democracy should not lose stability: {result.delta}"
        )
        assert result.new_stability <= 9.0, "Hard cap is 9.0"


class TestStabilityWarPrimaryBelligerent:
    """Country at war as primary belligerent."""

    def test_stability_war_primary_belligerent(self):
        """War friction -0.08/round for primary belligerent per CARD_FORMULAS."""
        inp = _default_stability_input(
            at_war=True,
            is_primary_belligerent=True,
            war_tiredness=2.0,
        )
        result = calc_stability(inp)
        print(f"  Primary belligerent: {result.old_stability} -> {result.new_stability} (delta={result.delta})")
        # War friction -0.08 + war_tiredness penalty + no peaceful dampening
        assert result.new_stability < result.old_stability, (
            f"Primary belligerent should lose stability, got delta={result.delta}"
        )


class TestStabilityAusterity:
    """50% social spending cut."""

    def test_stability_austerity_50pct(self):
        """50% cut -> stability -2.0/round (linear: delta%/25)."""
        inp = _default_stability_input(
            social_spending_ratio=0.15,  # 50% of baseline 0.30
            social_spending_baseline=0.30,
        )
        result = calc_stability(inp)
        print(f"  Austerity 50%: {result.old_stability} -> {result.new_stability} (delta={result.delta})")
        # social_pct = 0.15/0.30 = 0.5, social_delta_pct = -50, delta = -50/25 = -2.0
        # But peaceful non-sanctioned dampening halves negative delta: -2.0 * 0.5 = -1.0 raw
        # Plus positive inertia +0.05 and mild GDP bonus
        # Net should still be meaningfully negative
        assert result.new_stability < result.old_stability, (
            f"Austerity should reduce stability, got delta={result.delta}"
        )
        # The social spending component alone is -2.0 before dampening
        # After dampening (0.5x for peaceful non-sanctioned): ~-1.0
        assert result.delta < -0.5, (
            f"50% austerity should cause significant drop, got delta={result.delta}"
        )


class TestStabilityGenerous:
    """150% social spending."""

    def test_stability_generous_150pct(self):
        """150% spending -> stability +2.0/round (linear: +50%/25)."""
        inp = _default_stability_input(
            social_spending_ratio=0.45,  # 150% of baseline 0.30
            social_spending_baseline=0.30,
        )
        result = calc_stability(inp)
        print(f"  Generous 150%: {result.old_stability} -> {result.new_stability} (delta={result.delta})")
        # social_pct = 0.45/0.30 = 1.5, social_delta_pct = +50, delta = +50/25 = +2.0
        # Plus positive inertia +0.05 and mild GDP bonus
        assert result.new_stability > result.old_stability, (
            f"Generous spending should increase stability, got delta={result.delta}"
        )
        assert result.delta > 1.5, (
            f"150% spending should add ~+2.0, got delta={result.delta}"
        )


class TestStabilityGDPCrash:
    """GDP contracted 10%."""

    def test_stability_gdp_crash(self):
        """GDP -10% -> contraction penalty (max capped at -0.30/round)."""
        inp = _default_stability_input(
            gdp_growth_rate=-10.0,
        )
        result = calc_stability(inp)
        print(f"  GDP crash -10%: {result.old_stability} -> {result.new_stability} (delta={result.delta})")
        # GDP penalty: max(-10 * 0.15, -0.30) = max(-1.5, -0.30) = -0.30
        # But peaceful dampening halves it: -0.30 * 0.5 = -0.15
        assert result.new_stability < result.old_stability, (
            f"GDP crash should reduce stability, got delta={result.delta}"
        )


class TestStabilityGDPBoom:
    """GDP grew 5%."""

    def test_stability_gdp_boom(self):
        """GDP +5% -> small stability bonus."""
        inp = _default_stability_input(
            gdp_growth_rate=5.0,
        )
        result = calc_stability(inp)
        print(f"  GDP boom +5%: {result.old_stability} -> {result.new_stability} (delta={result.delta})")
        # GDP bonus: min((5-2)*0.08, 0.15) = min(0.24, 0.15) = 0.15
        assert result.new_stability > result.old_stability, (
            f"GDP boom should increase stability, got delta={result.delta}"
        )
        assert result.delta > 0.1, (
            f"5% GDP growth should give meaningful bonus, got delta={result.delta}"
        )


class TestStabilityHighInflation:
    """Inflation > 20% above starting."""

    def test_stability_high_inflation(self):
        """Inflation spike -> stability penalty from inflation friction."""
        inp = _default_stability_input(
            inflation=30.0,
            starting_inflation=3.0,
        )
        result = calc_stability(inp)
        print(f"  High inflation 30%: {result.old_stability} -> {result.new_stability} (delta={result.delta})")
        # inflation_delta = 30 - 3 = 27
        # friction: -(27-3)*0.05 = -1.2, plus -(27-20)*0.03 = -0.21, total = -1.41
        # capped at -0.50
        # After peaceful dampening: -0.50 * 0.5 = -0.25
        assert result.new_stability < result.old_stability, (
            f"High inflation should reduce stability, got delta={result.delta}"
        )


class TestStabilityNuclearTestGlobal:
    """Nuclear test -> small global stability decrease via market_stress."""

    def test_stability_nuclear_test_global(self):
        """Nuclear test modelled as market_stress -> small stability hit."""
        inp = _default_stability_input(
            market_stress=-0.20,
        )
        result = calc_stability(inp)
        print(f"  Nuclear test (market_stress -0.2): {result.old_stability} -> {result.new_stability} (delta={result.delta})")
        # market_stress = -0.20, after peaceful dampening: -0.20 * 0.5 = -0.10
        # But there's also positive inertia +0.05 and GDP bonus
        # Net should be slightly negative or near zero
        assert result.delta < 0.15, (
            f"Market stress should offset positive inertia, got delta={result.delta}"
        )


class TestStabilitySanctionsReceived:
    """Under heavy sanctions (level 2+)."""

    def test_stability_sanctions_received(self):
        """Heavy sanctions -> stability penalty."""
        inp = _default_stability_input(
            sanctions_level=3,
            sanctions_rounds=2,
            sanctions_pain=50.0,
            gdp=500.0,
            # At war to avoid peaceful dampening
            at_war=True,
            is_primary_belligerent=True,
        )
        result = calc_stability(inp)
        print(f"  Heavy sanctions: {result.old_stability} -> {result.new_stability} (delta={result.delta})")
        # sanctions friction: -0.1 * 3 * 1.0 = -0.30
        # heavy sanctions: -(50/500)*0.8 = -0.08
        # plus war friction: -0.08
        assert result.new_stability < result.old_stability, (
            f"Sanctions should reduce stability, got delta={result.delta}"
        )


class TestStabilityClamp:
    """Stability always clamped 1.0 to 9.0."""

    def test_stability_clamped_floor(self):
        """Extreme negative inputs -> stability floored at 1.0."""
        inp = _default_stability_input(
            stability=2.0,
            gdp_growth_rate=-10.0,
            social_spending_ratio=0.0,
            social_spending_baseline=0.30,
            at_war=True,
            is_frontline_defender=True,
            war_tiredness=8.0,
            casualties=5,
            territory_lost=3,
            economic_state="collapse",
            inflation=50.0,
            starting_inflation=3.0,
            sanctions_level=3,
            sanctions_pain=200.0,
            gdp=300.0,
        )
        result = calc_stability(inp)
        print(f"  Extreme negative: {result.old_stability} -> {result.new_stability} (delta={result.delta})")
        assert result.new_stability >= 1.0, f"Floor violated: {result.new_stability}"

    def test_stability_clamped_ceiling(self):
        """Extreme positive inputs -> stability capped at 9.0."""
        inp = _default_stability_input(
            stability=8.5,
            gdp_growth_rate=8.0,
            social_spending_ratio=0.90,
            social_spending_baseline=0.30,
            propaganda_boost=1.0,
        )
        result = calc_stability(inp)
        print(f"  Extreme positive: {result.old_stability} -> {result.new_stability} (delta={result.delta})")
        assert result.new_stability <= 9.0, f"Cap violated: {result.new_stability}"


# ===========================================================================
# POLITICAL SUPPORT (CARD_FORMULAS B.2 / political.py calc_political_support)
# ===========================================================================

class TestSupportStableConditions:
    """No major events -> support drifts toward 50%."""

    def test_support_stable_conditions(self):
        """Stable conditions, support at 55 -> slight drift toward 50."""
        inp = _default_support_input()
        result = calc_political_support(inp)
        print(f"  Stable conditions: {result.old_support} -> {result.new_support} (delta={result.delta})")
        # GDP 2.5% -> (2.5-2)*0.8 = +0.4
        # stability 7 -> (7-6)*0.5 = +0.5
        # mean-reversion: -(55-50)*0.05 = -0.25
        # Net ~ +0.65
        assert abs(result.delta) < 5.0, (
            f"Stable conditions should not swing wildly, got delta={result.delta}"
        )


class TestSupportWarErodes:
    """Country at war -> support drops from war tiredness."""

    def test_support_war_erodes(self):
        """War tiredness > 2 damages support."""
        inp = _default_support_input(
            war_tiredness=5.0,
            casualties=2,
        )
        result = calc_political_support(inp)
        print(f"  War erodes support: {result.old_support} -> {result.new_support} (delta={result.delta})")
        # war_tiredness: -(5-2)*1.0 = -3.0
        # casualties: -2*3.0 = -6.0
        # GDP + stability still positive but offset
        assert result.new_support < result.old_support, (
            f"War should erode support, got delta={result.delta}"
        )


class TestSupportHighStabilityHelps:
    """Stability 9 -> support maintained or grows."""

    def test_support_high_stability_helps(self):
        """High stability boosts support."""
        inp = _default_support_input(
            stability=9.0,
        )
        result = calc_political_support(inp)
        print(f"  High stability (9): {result.old_support} -> {result.new_support} (delta={result.delta})")
        # stability factor: (9-6)*0.5 = +1.5
        assert result.delta > 0.5, (
            f"High stability should boost support, got delta={result.delta}"
        )


class TestSupportLowStabilityHurts:
    """Stability 3 -> support drops."""

    def test_support_low_stability_hurts(self):
        """Low stability damages support."""
        inp = _default_support_input(
            stability=3.0,
        )
        result = calc_political_support(inp)
        print(f"  Low stability (3): {result.old_support} -> {result.new_support} (delta={result.delta})")
        # stability factor: (3-6)*0.5 = -1.5
        # GDP: +0.4, mean reversion: -0.25
        # Net should be negative
        assert result.new_support < result.old_support, (
            f"Low stability should hurt support, got delta={result.delta}"
        )


# ===========================================================================
# WAR TIREDNESS (CARD_FORMULAS B.3 / political.py update_war_tiredness)
# ===========================================================================

class TestWarTirednessIncreasesAtWar:
    """Country fighting -> war tiredness increases."""

    def test_war_tiredness_defender(self):
        """Defender: +0.20 per round."""
        inp = WarTirednessInput(
            country_id="ruthenia",
            war_tiredness=1.0,
            at_war=True,
            is_defender=True,
            is_attacker=False,
            war_duration=1,
        )
        result = update_war_tiredness(inp)
        print(f"  Defender tiredness: {result.old_war_tiredness} -> {result.new_war_tiredness}")
        assert result.new_war_tiredness == pytest.approx(1.20, abs=0.01), (
            f"Defender should gain +0.20, got {result.new_war_tiredness}"
        )

    def test_war_tiredness_attacker(self):
        """Attacker: +0.15 per round."""
        inp = WarTirednessInput(
            country_id="sarmatia",
            war_tiredness=1.0,
            at_war=True,
            is_defender=False,
            is_attacker=True,
            war_duration=1,
        )
        result = update_war_tiredness(inp)
        print(f"  Attacker tiredness: {result.old_war_tiredness} -> {result.new_war_tiredness}")
        assert result.new_war_tiredness == pytest.approx(1.15, abs=0.01), (
            f"Attacker should gain +0.15, got {result.new_war_tiredness}"
        )

    def test_war_tiredness_ally(self):
        """Ally: +0.10 per round."""
        inp = WarTirednessInput(
            country_id="columbia",
            war_tiredness=0.5,
            at_war=True,
            is_defender=False,
            is_attacker=False,
            is_ally=True,
            war_duration=1,
        )
        result = update_war_tiredness(inp)
        print(f"  Ally tiredness: {result.old_war_tiredness} -> {result.new_war_tiredness}")
        assert result.new_war_tiredness == pytest.approx(0.60, abs=0.01), (
            f"Ally should gain +0.10, got {result.new_war_tiredness}"
        )

    def test_war_tiredness_society_adaptation(self):
        """After 3+ rounds at war, tiredness growth halves."""
        inp = WarTirednessInput(
            country_id="ruthenia",
            war_tiredness=3.0,
            at_war=True,
            is_defender=True,
            war_duration=4,
        )
        result = update_war_tiredness(inp)
        print(f"  Society adaptation (4 rounds): {result.old_war_tiredness} -> {result.new_war_tiredness}")
        # 0.20 * 0.5 = 0.10
        assert result.new_war_tiredness == pytest.approx(3.10, abs=0.01), (
            f"After 3+ rounds, growth should halve: +0.10, got {result.new_war_tiredness}"
        )


class TestWarTirednessDecreasesAtPeace:
    """Not at war -> war tiredness decays 20% per round."""

    def test_war_tiredness_peace_decay(self):
        """Peace: 20% decay per round."""
        inp = WarTirednessInput(
            country_id="columbia",
            war_tiredness=5.0,
            at_war=False,
        )
        result = update_war_tiredness(inp)
        print(f"  Peace decay: {result.old_war_tiredness} -> {result.new_war_tiredness}")
        # 5.0 * 0.80 = 4.0
        assert result.new_war_tiredness == pytest.approx(4.0, abs=0.01), (
            f"Peace decay should be 20%, got {result.new_war_tiredness}"
        )

    def test_war_tiredness_peace_from_zero(self):
        """Already at 0 -> stays 0."""
        inp = WarTirednessInput(
            country_id="columbia",
            war_tiredness=0.0,
            at_war=False,
        )
        result = update_war_tiredness(inp)
        assert result.new_war_tiredness == 0.0


# ===========================================================================
# THRESHOLD FLAGS (CARD_FORMULAS B.4 / political.py update_threshold_flags)
# ===========================================================================

class TestThresholdFlags:
    """Protest/coup risk thresholds."""

    def test_stable_high(self):
        """Stability 7 -> stable, no risks."""
        result = update_threshold_flags(7.0)
        print(f"  Stability 7: regime={result.regime_status}, protest={result.protest_risk}, coup={result.coup_risk}")
        assert result.regime_status == "stable"
        assert result.protest_risk is False
        assert result.coup_risk is False

    def test_unstable_zone(self):
        """Stability 5.5 -> unstable, protest risk, coup risk."""
        result = update_threshold_flags(5.5)
        print(f"  Stability 5.5: regime={result.regime_status}, protest={result.protest_risk}, coup={result.coup_risk}")
        assert result.regime_status == "unstable"
        assert result.protest_risk is False  # protest_probable threshold is 5
        assert result.coup_risk is True  # unstable threshold is 6

    def test_protest_zone(self):
        """Stability 4.0 -> unstable, protest probable."""
        result = update_threshold_flags(4.0)
        print(f"  Stability 4.0: regime={result.regime_status}, protest={result.protest_risk}, coup={result.coup_risk}")
        assert result.protest_risk is True  # below 5
        assert result.coup_risk is True  # below 6

    def test_crisis_zone(self):
        """Stability 2.5 -> crisis, all flags."""
        result = update_threshold_flags(2.5)
        print(f"  Stability 2.5: regime={result.regime_status}, protest={result.protest_risk}, coup={result.coup_risk}")
        assert result.regime_status == "crisis"
        assert result.protest_risk is True
        assert result.coup_risk is True


# ===========================================================================
# REVOLUTION CHECK (CARD_FORMULAS B.5 / political.py check_revolution)
# ===========================================================================

class TestRevolutionCheck:
    """Revolution triggers when stability <= 2 AND support < 20%."""

    def test_revolution_triggers(self):
        """Stability 1.5, support 10% -> mass protests."""
        result = check_revolution("sarmatia", 1.5, 10.0)
        print(f"  Revolution check (1.5/10%): {result}")
        assert result is not None
        assert result.event == "mass_protests"
        assert result.severity == "major"
        assert result.base_success_probability > 0.30

    def test_revolution_severe(self):
        """Stability 1.0 -> severe protests."""
        result = check_revolution("sarmatia", 1.0, 5.0)
        print(f"  Revolution severe (1.0/5%): {result}")
        assert result is not None
        assert result.severity == "severe"

    def test_no_revolution_high_support(self):
        """Stability 1.5 but support 25% -> no revolution."""
        result = check_revolution("sarmatia", 1.5, 25.0)
        assert result is None

    def test_no_revolution_high_stability(self):
        """Stability 5.0, support 10% -> no revolution."""
        result = check_revolution("sarmatia", 5.0, 10.0)
        assert result is None


# ===========================================================================
# COUP RESOLUTION (CARD_FORMULAS B.6 / political.py resolve_coup)
# ===========================================================================

class TestCoupResolution:
    """Coup probability calculations (deterministic part)."""

    def test_coup_base_probability(self):
        """Base 15% with stable conditions."""
        random.seed(999)  # deterministic
        inp = CoupInput(
            country_id="sarmatia",
            plotters=["general", "spymaster"],
            stability=7.0,
            political_support=60.0,
        )
        result = resolve_coup(inp)
        print(f"  Coup base: prob={result.probability}, success={result.success}")
        assert result.probability == pytest.approx(0.15, abs=0.01), (
            f"Base probability should be 15%, got {result.probability}"
        )

    def test_coup_high_probability(self):
        """Low stability + low support + protests -> high probability."""
        random.seed(999)
        inp = CoupInput(
            country_id="sarmatia",
            plotters=["general", "spymaster"],
            stability=2.5,
            political_support=20.0,
            protest_active=True,
        )
        result = resolve_coup(inp)
        print(f"  Coup high prob: prob={result.probability}, success={result.success}")
        # base 15% + protest 25% + stability<3: 15% + support<30: 10% = 65%
        assert result.probability == pytest.approx(0.65, abs=0.01), (
            f"Expected ~65%, got {result.probability}"
        )

    def test_coup_needs_two_plotters(self):
        """Single plotter -> fails immediately."""
        inp = CoupInput(
            country_id="sarmatia",
            plotters=["general"],
            stability=2.0,
            political_support=10.0,
        )
        result = resolve_coup(inp)
        print(f"  Coup single plotter: prob={result.probability}, success={result.success}")
        assert result.success is False
        assert result.probability == 0.0

    def test_coup_stability_change(self):
        """Verify stability change: -2 on success, -1 on failure."""
        # Force success
        random.seed(0)
        inp = CoupInput(
            country_id="sarmatia",
            plotters=["general", "spymaster"],
            stability=2.0,
            political_support=10.0,
            protest_active=True,
        )
        # Run multiple times to get both outcomes
        success_change = None
        failure_change = None
        for seed in range(100):
            random.seed(seed)
            result = resolve_coup(inp)
            if result.success and success_change is None:
                success_change = result.stability_change
            elif not result.success and failure_change is None:
                failure_change = result.stability_change
            if success_change is not None and failure_change is not None:
                break

        print(f"  Coup stability changes: success={success_change}, failure={failure_change}")
        assert success_change == -2.0, f"Success should cost -2 stability, got {success_change}"
        assert failure_change == -1.0, f"Failure should cost -1 stability, got {failure_change}"
