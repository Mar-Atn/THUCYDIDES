"""Layer 1 tests — tariff engine REGRESSION LOCK.

Purpose: pin the current behavior of `calc_tariff_coefficient` (CONTRACT_TARIFFS
v1.0 §6, engine UNCHANGED) so any future change to the formula or its constants
breaks a test loudly. This is a REGRESSION GUARD, not a redesign — we expect
these tests to keep passing as-is unless someone explicitly intends to change
tariff behavior.

Constants locked here (from CARD_FORMULAS A.3 + economic.py):
    TARIFF_K                 = 0.54
    TARIFF_IMPOSER_FRACTION  = 0.50
    TARIFF_REVENUE_RATE      = 0.075
    TARIFF_INFLATION_RATE    = 12.5
    coefficient floor        = 0.80

Run:
    cd app && PYTHONPATH=. python3 -m pytest tests/layer1/test_tariff_engine.py -v
"""

from __future__ import annotations

import pytest

from engine.engines.economic import (
    TARIFF_IMPOSER_FRACTION,
    TARIFF_INFLATION_RATE,
    TARIFF_K,
    TARIFF_REVENUE_RATE,
    _trade_exposure,
    calc_tariff_coefficient,
)


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------


def _country(
    *,
    gdp: float = 280.0,
    trade_balance: float = 0.0,
    starting_gdp: float | None = None,
) -> dict:
    """Minimal country dict in the engine's format."""
    eco = {
        "gdp": gdp,
        "_starting_gdp": starting_gdp if starting_gdp is not None else gdp,
        "trade_balance": trade_balance,
    }
    return {"economic": eco}


def _world() -> dict[str, dict]:
    """Three-country world used for canonical examples.

    Sized to roughly match the relative scale used by the engine in real
    scenarios. Total starting GDP = 600.
    """
    return {
        "columbia": _country(gdp=280, trade_balance=-50),
        "cathay":   _country(gdp=245, trade_balance=+30),
        "bharata":  _country(gdp=75,  trade_balance=-5),
    }


# ===========================================================================
# 1. CONSTANTS LOCKED
# ===========================================================================


class TestConstantsLocked:
    """Pin the constants. Changing any of these is an explicit decision."""

    def test_tariff_k(self):
        assert TARIFF_K == 0.54

    def test_tariff_imposer_fraction(self):
        assert TARIFF_IMPOSER_FRACTION == 0.50

    def test_tariff_revenue_rate(self):
        assert TARIFF_REVENUE_RATE == 0.075

    def test_tariff_inflation_rate(self):
        assert TARIFF_INFLATION_RATE == 12.5


# ===========================================================================
# 2. EMPTY / TRIVIAL CASES
# ===========================================================================


class TestTrivialCases:
    def test_no_tariffs_returns_unity(self):
        countries = _world()
        coef, infl, rev = calc_tariff_coefficient("columbia", countries, {})
        assert coef == 1.0
        assert infl == 0.0
        assert rev == 0.0

    def test_zero_level_treated_as_no_tariff(self):
        countries = _world()
        tariffs = {"columbia": {"cathay": 0}}
        coef, infl, rev = calc_tariff_coefficient("columbia", countries, tariffs)
        assert coef == 1.0
        assert infl == 0.0
        assert rev == 0.0

    def test_other_pair_does_not_affect_me(self):
        countries = _world()
        # Cathay tariffs Bharata — Columbia is bystander
        tariffs = {"cathay": {"bharata": 3}}
        coef, infl, rev = calc_tariff_coefficient("columbia", countries, tariffs)
        assert coef == 1.0
        assert infl == 0.0
        assert rev == 0.0


# ===========================================================================
# 3. SINGLE TARIFF — IMPOSER SIDE (Columbia → Cathay L3)
# ===========================================================================
#
# Hand-computed expected values from CARD_FORMULAS A.3 / economic.py:
#
#   total_gdp           = 280 + 245 + 75 = 600
#   columbia_exposure   = (|−50| + 0.25 × 280) / 280 = (50 + 70) / 280 = 0.4286
#   cathay_exposure     = (|+30| + 0.25 × 245) / 245 = (30 + 61.25) / 245 = 0.3724
#   cathay_market_share = 245 / 600 = 0.4083
#   intensity (L3)      = 3 / 3 = 1.0
#
#   self_damage     = 0.4083 × 0.4286 × 1.0 × 0.54 × 0.5 = 0.04725
#   customs_revenue = 245 × 0.3724 × 1.0 × 0.075 = 6.844
#   inflation_add   = 1.0 × 0.4083 × 12.5 = 5.104
#   coefficient     = max(0.80, 1.0 - 0.04725) = 0.9528
# ---------------------------------------------------------------------------


class TestColumbiaTariffsCathayL3:
    def setup_method(self):
        self.countries = _world()
        self.tariffs = {"columbia": {"cathay": 3}}
        self.coef, self.infl, self.rev = calc_tariff_coefficient(
            "columbia", self.countries, self.tariffs
        )

    def test_coefficient(self):
        assert self.coef == pytest.approx(0.9528, rel=1e-3)

    def test_inflation(self):
        assert self.infl == pytest.approx(5.104, rel=1e-3)

    def test_customs_revenue(self):
        assert self.rev == pytest.approx(6.844, rel=1e-3)

    def test_target_sees_proportional_hit(self):
        """Cathay is the target — should see GDP hit from Columbia's market share."""
        coef_cathay, infl_cathay, rev_cathay = calc_tariff_coefficient(
            "cathay", self.countries, self.tariffs
        )
        # Cathay imposed nothing → no revenue, no inflation
        assert rev_cathay == 0.0
        assert infl_cathay == 0.0
        # But coefficient < 1 because Columbia tariffs Cathay
        assert coef_cathay < 1.0


# ===========================================================================
# 4. LEVEL SCALING — same target, increasing level
# ===========================================================================


class TestLevelScaling:
    def test_higher_level_more_revenue(self):
        countries = _world()
        revs = []
        for lvl in (1, 2, 3):
            _, _, rev = calc_tariff_coefficient(
                "columbia", countries, {"columbia": {"cathay": lvl}}
            )
            revs.append(rev)
        assert revs[0] < revs[1] < revs[2]

    def test_higher_level_more_self_damage(self):
        countries = _world()
        coefs = []
        for lvl in (1, 2, 3):
            coef, _, _ = calc_tariff_coefficient(
                "columbia", countries, {"columbia": {"cathay": lvl}}
            )
            coefs.append(coef)
        # Higher level = more self-damage = lower coefficient
        assert coefs[0] > coefs[1] > coefs[2]

    def test_higher_level_more_inflation(self):
        countries = _world()
        infls = []
        for lvl in (1, 2, 3):
            _, infl, _ = calc_tariff_coefficient(
                "columbia", countries, {"columbia": {"cathay": lvl}}
            )
            infls.append(infl)
        assert infls[0] < infls[1] < infls[2]

    def test_l3_revenue_is_3x_l1(self):
        """Intensity is linear in level, so L3 revenue should be 3× L1 revenue."""
        countries = _world()
        _, _, rev_l1 = calc_tariff_coefficient(
            "columbia", countries, {"columbia": {"cathay": 1}}
        )
        _, _, rev_l3 = calc_tariff_coefficient(
            "columbia", countries, {"columbia": {"cathay": 3}}
        )
        assert rev_l3 == pytest.approx(3 * rev_l1, rel=1e-6)


# ===========================================================================
# 5. ASYMMETRY — imposer self-damage vs target damage
# ===========================================================================


class TestImposerVsTargetAsymmetry:
    def test_target_takes_more_hit_than_imposer(self):
        """TARIFF_IMPOSER_FRACTION = 0.5: imposer eats half what target eats."""
        countries = _world()
        tariffs = {"columbia": {"cathay": 3}}

        coef_imposer, _, _ = calc_tariff_coefficient(
            "columbia", countries, tariffs
        )
        coef_target, _, _ = calc_tariff_coefficient(
            "cathay", countries, tariffs
        )

        damage_imposer = 1.0 - coef_imposer
        damage_target = 1.0 - coef_target

        assert damage_target > damage_imposer
        # Approximately 2:1 ratio (modulo exposure differences)
        ratio = damage_target / damage_imposer
        assert 1.5 < ratio < 3.0


# ===========================================================================
# 6. COEFFICIENT FLOOR
# ===========================================================================


class TestCoefficientFloor:
    def test_extreme_pile_on_clamped_to_floor(self):
        """All countries L3 against Columbia simultaneously → coef floor = 0.80."""
        countries = {
            "columbia": _country(gdp=100, trade_balance=-100),  # very exposed
            "cathay":   _country(gdp=400, trade_balance=0),
            "bharata":  _country(gdp=400, trade_balance=0),
            "teutonia": _country(gdp=400, trade_balance=0),
        }
        tariffs = {
            "cathay":   {"columbia": 3},
            "bharata":  {"columbia": 3},
            "teutonia": {"columbia": 3},
        }
        coef, _, _ = calc_tariff_coefficient("columbia", countries, tariffs)
        assert coef == pytest.approx(0.80, abs=1e-9)


# ===========================================================================
# 7. MULTIPLE TARGETS — additive
# ===========================================================================


class TestMultipleTargetsAdditive:
    def test_two_targets_more_revenue_than_one(self):
        countries = _world()
        _, _, rev_one = calc_tariff_coefficient(
            "columbia", countries, {"columbia": {"cathay": 2}}
        )
        _, _, rev_two = calc_tariff_coefficient(
            "columbia", countries,
            {"columbia": {"cathay": 2, "bharata": 2}},
        )
        assert rev_two > rev_one

    def test_multiple_imposers_against_me_compound(self):
        countries = _world()
        coef_one, _, _ = calc_tariff_coefficient(
            "columbia", countries, {"cathay": {"columbia": 2}}
        )
        coef_two, _, _ = calc_tariff_coefficient(
            "columbia", countries,
            {"cathay": {"columbia": 2}, "bharata": {"columbia": 2}},
        )
        # More imposers = more damage = lower coefficient
        assert coef_two < coef_one


# ===========================================================================
# 8. TRADE EXPOSURE HELPER
# ===========================================================================


class TestTradeExposure:
    def test_balanced_economy(self):
        eco = {"gdp": 100, "trade_balance": 0}
        # (0 + 25) / 100 = 0.25
        assert _trade_exposure(eco) == pytest.approx(0.25)

    def test_high_exposure_economy(self):
        eco = {"gdp": 100, "trade_balance": 50}
        # (50 + 25) / 100 = 0.75
        assert _trade_exposure(eco) == pytest.approx(0.75)

    def test_negative_balance_uses_absolute(self):
        eco = {"gdp": 100, "trade_balance": -50}
        assert _trade_exposure(eco) == pytest.approx(0.75)
