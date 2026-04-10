"""Layer 1 tests — sanctions engine REGRESSION LOCK (CONTRACT_SANCTIONS v1.0).

Purpose: pin the canonical behavior of `calc_sanctions_coefficient` + its
helper `_sanctions_max_damage` so any future change breaks a test loudly.

Canonical model (locked 2026-04-10):
    max_damage_by_sector = tec × 0.25 + svc × 0.25 + ind × 0.125 + res × 0.05
    coverage             = Σ (actor_gdp_share × level/3)    # level ∈ [-3, +3]
    coverage             = clamp(coverage, 0, 1)
    effectiveness        = S_curve(coverage)
    damage               = max_damage × effectiveness
    coefficient          = max(SANCTIONS_FLOOR, 1 - damage)

Run:
    cd app && PYTHONPATH=. python3 -m pytest tests/layer1/test_sanctions_engine.py -v
"""

from __future__ import annotations

import pytest

from engine.engines.economic import (
    SANCTIONS_FLOOR,
    SANCTIONS_S_CURVE,
    SANCTIONS_WEIGHT_IND,
    SANCTIONS_WEIGHT_RES,
    SANCTIONS_WEIGHT_SVC,
    SANCTIONS_WEIGHT_TEC,
    _sanctions_max_damage,
    calc_sanctions_coefficient,
    interpolate_s_curve,
)

# ---------------------------------------------------------------------------
# HELPERS — real DB country data (snapshot 2026-04-10)
# ---------------------------------------------------------------------------

# (gdp, trade_balance, res%, ind%, svc%, tec%)
COUNTRIES_RAW = {
    "albion":   ( 33.0,  -2.0,  5, 17, 60, 18),
    "bharata":  ( 42.0,  -3.0, 10, 25, 48, 17),
    "caribe":   (  2.0,   0.0, 50, 20, 25,  5),
    "cathay":   (190.0,  12.0,  5, 52, 30, 13),
    "choson":   (  0.3,  -0.5, 20, 40, 35,  5),
    "columbia": (280.0, -12.0,  8, 18, 55, 22),
    "formosa":  (  8.0,   4.0,  2, 30, 35, 33),
    "freeland": (  9.0,   0.0,  8, 30, 50, 12),
    "gallia":   ( 34.0,  -1.0,  5, 20, 55, 20),
    "hanguk":   ( 18.0,   3.0,  3, 33, 42, 22),
    "levantia": (  5.0,  -1.0,  3, 15, 50, 32),
    "mirage":   (  5.0,   5.0, 30, 15, 45, 10),
    "persia":   (  5.0,  -1.0, 35, 30, 28,  7),
    "phrygia":  ( 11.0,  -3.0,  8, 30, 50, 12),
    "ponte":    ( 22.0,   0.0,  4, 22, 60, 14),
    "ruthenia": (  2.2,  -0.8, 15, 20, 40, 10),
    "sarmatia": ( 20.0,   2.0, 40, 25, 25, 10),
    "solaria":  ( 11.0,   8.0, 45, 20, 28,  7),
    "teutonia": ( 45.0,   3.0,  3, 28, 50, 19),
    "yamato":   ( 43.0,  -2.0,  2, 28, 50, 20),
}


@pytest.fixture
def countries() -> dict:
    """Full 20-country engine dict in canonical 2026-04-10 state."""
    out = {}
    for code, (gdp, tb, res, ind, svc, tec) in COUNTRIES_RAW.items():
        out[code] = {
            "economic": {
                "gdp": gdp,
                "_starting_gdp": gdp,
                "trade_balance": tb,
                "sectors": {
                    "resources":  res,
                    "industry":   ind,
                    "services":   svc,
                    "technology": tec,
                },
            }
        }
    return out


# ===========================================================================
# 1. CONSTANTS LOCKED
# ===========================================================================


class TestConstantsLocked:
    """Pin the canonical v1.0 constants. Any change requires explicit ticket."""

    def test_weight_tec(self):
        assert SANCTIONS_WEIGHT_TEC == 0.25

    def test_weight_svc(self):
        assert SANCTIONS_WEIGHT_SVC == 0.25

    def test_weight_ind(self):
        assert SANCTIONS_WEIGHT_IND == 0.125

    def test_weight_res(self):
        assert SANCTIONS_WEIGHT_RES == 0.05

    def test_floor(self):
        assert SANCTIONS_FLOOR == 0.15

    def test_s_curve_shape(self):
        assert SANCTIONS_S_CURVE == [
            (0.0, 0.00), (0.1, 0.05), (0.2, 0.10), (0.3, 0.15),
            (0.4, 0.25), (0.5, 0.35), (0.6, 0.55), (0.7, 0.65),
            (0.8, 0.75), (0.9, 0.90), (1.0, 1.00),
        ]


# ===========================================================================
# 2. MAX DAMAGE BY SECTOR — per country
# ===========================================================================


class TestMaxDamageBySector:
    """max_damage ceiling derived from sector mix."""

    def test_sarmatia_resource_heavy(self, countries):
        """Sarmatia: res40 ind25 svc25 tec10 → 0.1388 (13.88% ceiling)."""
        md = _sanctions_max_damage(countries["sarmatia"]["economic"])
        # 0.25×0.10 + 0.25×0.25 + 0.125×0.25 + 0.05×0.40
        # = 0.0250 + 0.0625 + 0.03125 + 0.0200 = 0.13875
        assert md == pytest.approx(0.13875, abs=1e-5)

    def test_columbia_tech_services_heavy(self, countries):
        """Columbia: res8 ind18 svc55 tec22 → 0.219 (21.9% ceiling)."""
        md = _sanctions_max_damage(countries["columbia"]["economic"])
        # 0.25×0.22 + 0.25×0.55 + 0.125×0.18 + 0.05×0.08
        # = 0.0550 + 0.1375 + 0.0225 + 0.0040 = 0.2190
        assert md == pytest.approx(0.2190, abs=1e-5)

    def test_caribe_pure_resource(self, countries):
        """Caribe: res50 ind20 svc25 tec5 → 0.1250 (12.5% — lowest ceiling)."""
        md = _sanctions_max_damage(countries["caribe"]["economic"])
        # 0.25×0.05 + 0.25×0.25 + 0.125×0.20 + 0.05×0.50
        # = 0.0125 + 0.0625 + 0.025 + 0.025 = 0.1250
        assert md == pytest.approx(0.1250, abs=1e-5)

    def test_levantia_highest_ceiling(self, countries):
        """Levantia: res3 ind15 svc50 tec32 → 0.2253 (22.53% — highest ceiling)."""
        md = _sanctions_max_damage(countries["levantia"]["economic"])
        # 0.25×0.32 + 0.25×0.50 + 0.125×0.15 + 0.05×0.03
        # = 0.0800 + 0.1250 + 0.01875 + 0.0015 = 0.22525
        assert md == pytest.approx(0.22525, abs=1e-5)

    def test_max_damage_ordering_by_sector_profile(self, countries):
        """Tech/services heavy economies have higher ceilings than resource economies."""
        md_levantia = _sanctions_max_damage(countries["levantia"]["economic"])  # tech heavy
        md_columbia = _sanctions_max_damage(countries["columbia"]["economic"])  # services
        md_cathay   = _sanctions_max_damage(countries["cathay"]["economic"])    # industrial
        md_sarmatia = _sanctions_max_damage(countries["sarmatia"]["economic"])  # resource
        md_caribe   = _sanctions_max_damage(countries["caribe"]["economic"])    # pure resource
        assert md_levantia > md_columbia > md_cathay > md_sarmatia > md_caribe


# ===========================================================================
# 3. TRIVIAL CASES
# ===========================================================================


class TestTrivialCases:
    def test_no_sanctions_anywhere(self, countries):
        """Clean world → coefficient = 1.0."""
        coef = calc_sanctions_coefficient("sarmatia", countries, {})
        assert coef == 1.0

    def test_zero_level_is_noop(self, countries):
        """level=0 entries are ignored."""
        coef = calc_sanctions_coefficient(
            "sarmatia", countries, {"columbia": {"sarmatia": 0}}
        )
        assert coef == 1.0

    def test_sanctions_against_others_dont_affect_me(self, countries):
        """Columbia sanctions Persia → Sarmatia unaffected."""
        coef = calc_sanctions_coefficient(
            "sarmatia", countries, {"columbia": {"persia": 3}}
        )
        assert coef == 1.0


# ===========================================================================
# 4. THE 4 CANONICAL SARMATIA SCENARIOS (calibration anchors)
# ===========================================================================

# These numbers are the calibration anchors locked in with Marat 2026-04-10.
# Any drift here means the engine behavior has changed and requires explicit
# review. Values computed during calibration and verified against hand math.


class TestSarmatiaScenarios:
    """The 4 canonical Sarmatia calibration scenarios."""

    def test_1_real_db_starting_config(self, countries):
        """Starting DB config: 12 actors (incl. Cathay L-1 evasion) → coef ≈ 0.9490."""
        sanctions = {
            "albion":   {"sarmatia":  3},
            "cathay":   {"sarmatia": -1},   # evasion support
            "columbia": {"sarmatia":  3},
            "formosa":  {"sarmatia":  1},
            "freeland": {"sarmatia":  3},
            "gallia":   {"sarmatia":  3},
            "hanguk":   {"sarmatia":  2},
            "levantia": {"sarmatia":  1},
            "ponte":    {"sarmatia":  2},
            "ruthenia": {"sarmatia":  3},
            "teutonia": {"sarmatia":  3},
            "yamato":   {"sarmatia":  2},
        }
        coef = calc_sanctions_coefficient("sarmatia", countries, sanctions)
        assert coef == pytest.approx(0.9490, abs=1e-3)
        gdp_loss = (1 - coef) * 100
        assert 4.8 <= gdp_loss <= 5.5  # ~5.10% canonical

    def test_2_columbia_alone_l3(self, countries):
        """Columbia alone at L3 → Sarmatia coef ≈ 0.9714 (−2.86%)."""
        coef = calc_sanctions_coefficient(
            "sarmatia", countries, {"columbia": {"sarmatia": 3}}
        )
        assert coef == pytest.approx(0.9714, abs=1e-3)

    def test_3_teutonia_alone_l3(self, countries):
        """Teutonia alone at L3 → Sarmatia coef ≈ 0.9960 (−0.40%, noise floor)."""
        coef = calc_sanctions_coefficient(
            "sarmatia", countries, {"teutonia": {"sarmatia": 3}}
        )
        assert coef == pytest.approx(0.9960, abs=1e-3)

    def test_4_cathay_flips_from_evasion_to_sanctioning(self, countries):
        """Starting config, Cathay flips L-1 → L+2 → coef ≈ 0.9028 (−9.72%, pivotal)."""
        sanctions = {
            "albion":   {"sarmatia":  3},
            "cathay":   {"sarmatia":  2},   # flipped from -1 to +2
            "columbia": {"sarmatia":  3},
            "formosa":  {"sarmatia":  1},
            "freeland": {"sarmatia":  3},
            "gallia":   {"sarmatia":  3},
            "hanguk":   {"sarmatia":  2},
            "levantia": {"sarmatia":  1},
            "ponte":    {"sarmatia":  2},
            "ruthenia": {"sarmatia":  3},
            "teutonia": {"sarmatia":  3},
            "yamato":   {"sarmatia":  2},
        }
        coef = calc_sanctions_coefficient("sarmatia", countries, sanctions)
        assert coef == pytest.approx(0.9028, abs=1e-3)


# ===========================================================================
# 5. SIGNED COVERAGE (evasion support)
# ===========================================================================


class TestSignedCoverage:
    """Level ∈ [-3, +3]; negative contributes negatively to coverage; clamp at 0."""

    def test_evasion_cancels_small_sanction(self, countries):
        """Small sanction (Teutonia L1) + equal evasion → coefficient ≈ 1.0."""
        sanctions = {
            "teutonia": {"sarmatia":  1},
            "cathay":   {"sarmatia": -1},   # bigger economy; should more than cancel
        }
        coef = calc_sanctions_coefficient("sarmatia", countries, sanctions)
        # Coverage goes negative pre-clamp; clamped at 0 → no damage
        assert coef == 1.0

    def test_evasion_cannot_produce_bonus(self, countries):
        """Pure evasion (no sanctions) → coefficient = 1.0, not > 1.0."""
        sanctions = {"cathay": {"sarmatia": -3}}
        coef = calc_sanctions_coefficient("sarmatia", countries, sanctions)
        assert coef == 1.0

    def test_evasion_reduces_but_not_zero(self, countries):
        """Strong sanction + moderate evasion → partially reduced damage."""
        full_sanction_coef = calc_sanctions_coefficient(
            "sarmatia", countries, {"columbia": {"sarmatia": 3}}
        )
        with_evasion_coef = calc_sanctions_coefficient(
            "sarmatia", countries,
            {"columbia": {"sarmatia": 3}, "cathay": {"sarmatia": -1}},
        )
        # Evasion should lift the coefficient (reduce damage) but not to 1.0
        assert full_sanction_coef < with_evasion_coef < 1.0


# ===========================================================================
# 6. LEVEL LADDER (monotonic scaling)
# ===========================================================================


class TestLevelLadder:
    def test_higher_level_more_damage(self, countries):
        """L1 < L2 < L3 damage for same sanctioner."""
        c1 = calc_sanctions_coefficient(
            "sarmatia", countries, {"columbia": {"sarmatia": 1}}
        )
        c2 = calc_sanctions_coefficient(
            "sarmatia", countries, {"columbia": {"sarmatia": 2}}
        )
        c3 = calc_sanctions_coefficient(
            "sarmatia", countries, {"columbia": {"sarmatia": 3}}
        )
        assert c1 > c2 > c3   # higher level = lower coefficient = more damage

    def test_larger_sanctioner_more_damage(self, countries):
        """At same level, a bigger economy inflicts more damage (S-curve amplification)."""
        col_l3 = calc_sanctions_coefficient(
            "sarmatia", countries, {"columbia": {"sarmatia": 3}}
        )
        teu_l3 = calc_sanctions_coefficient(
            "sarmatia", countries, {"teutonia": {"sarmatia": 3}}
        )
        assert col_l3 < teu_l3   # Columbia hurts more


# ===========================================================================
# 7. MAX POSSIBLE DAMAGE (all world sanctions Sarmatia at L3)
# ===========================================================================


class TestMaxPossibleDamage:
    def test_full_world_l3_on_sarmatia_approaches_sector_ceiling(self, countries):
        """Everyone except Sarmatia at L3 → damage approaches Sarmatia's sector ceiling."""
        sanctions = {
            code: {"sarmatia": 3}
            for code in countries
            if code != "sarmatia"
        }
        coef = calc_sanctions_coefficient("sarmatia", countries, sanctions)
        # Sarmatia max_damage = 0.1388 → coefficient floor ≈ 0.86
        # Full world coverage ~0.975, S-curve eff ~0.975 → damage ~0.135
        assert 0.85 < coef < 0.88

    def test_floor_clamp_never_breached(self, countries):
        """Even theoretical max damage cannot drive coefficient below SANCTIONS_FLOOR."""
        # Levantia has the highest ceiling (22.5%) — still well above 0.15 floor.
        # But the floor is a safety rail in case future changes push damage > 0.85.
        sanctions = {code: {"levantia": 3} for code in countries if code != "levantia"}
        coef = calc_sanctions_coefficient("levantia", countries, sanctions)
        assert coef >= SANCTIONS_FLOOR


# ===========================================================================
# 8. UNDERLYING S-CURVE SHAPE (sanity — full set pinned in test_engines.py)
# ===========================================================================


class TestSCurveKnotsSanity:
    """Spot checks on the new steeper curve — full set in test_engines.py."""

    def test_tipping_point_jump(self):
        """The 0.5 → 0.6 jump is 0.20, the steepest segment."""
        e05 = interpolate_s_curve(0.5, SANCTIONS_S_CURVE)
        e06 = interpolate_s_curve(0.6, SANCTIONS_S_CURVE)
        assert e06 - e05 == pytest.approx(0.20, abs=1e-6)

    def test_low_coverage_soft_tail(self):
        """Below 0.4 the curve is very flat (discourages solo action)."""
        assert interpolate_s_curve(0.1, SANCTIONS_S_CURVE) == pytest.approx(0.05)
        assert interpolate_s_curve(0.2, SANCTIONS_S_CURVE) == pytest.approx(0.10)
        assert interpolate_s_curve(0.3, SANCTIONS_S_CURVE) == pytest.approx(0.15)
