"""Layer 1 tests — OPEC engine REGRESSION LOCK (CONTRACT_OPEC v1.0).

Purpose: pin the existing behavior of `calc_oil_price` OPEC production logic
(lines ~650-659 of economic.py) so any future change to the constants or the
2× cartel leverage breaks a test loudly.

Canonical constants locked here:
    OPEC_PRODUCTION_MULTIPLIER = {
        "min":    0.70,
        "low":    0.85,
        "normal": 1.00,
        "high":   1.15,
        "max":    1.30,
    }
    2× cartel leverage applied as:
        supply += (multiplier - 1.0) × share × 2.0

This is a REGRESSION GUARD, not a redesign. The OPEC section of the engine is
UNCHANGED by the OPEC slice — we're locking a contract around existing behavior.

Run:
    cd app && PYTHONPATH=. python3 -m pytest tests/layer1/test_opec_engine.py -v
"""

from __future__ import annotations

import pytest

from engine.engines.economic import (
    OPEC_PRODUCTION_MULTIPLIER,
    calc_oil_price,
)


# ---------------------------------------------------------------------------
# HELPERS — real DB snapshot of 6 oil producers + a minimal world
# ---------------------------------------------------------------------------


def _country(gdp: float, mbpd: float, opec_member: bool = False,
             trade_balance: float = 0.0) -> dict:
    """Minimal country dict with oil production fields."""
    return {
        "economic": {
            "gdp": gdp,
            "_starting_gdp": gdp,
            "trade_balance": trade_balance,
            "oil_producer": mbpd > 0,
            "oil_production_mbpd": mbpd,
            "opec_member": opec_member,
            "formosa_dependency": 0,
            "oil_revenue": 0.0,
            "sectors": {
                "resources": 20,
                "industry": 30,
                "services": 40,
                "technology": 10,
            },
            "starting_oil_price": 80.0,
            "economic_state": "normal",
            "gdp_growth_rate": 0.02,
        }
    }


@pytest.fixture
def world():
    """20-country world with real DB oil data (2026-04-10)."""
    return {
        # 5 OPEC+ members
        "caribe":   _country(  2.0,  0.8, opec_member=True),
        "mirage":   _country(  5.0,  3.5, opec_member=True, trade_balance=5),
        "persia":   _country(  5.0,  3.5, opec_member=True),
        "sarmatia": _country( 20.0, 10.0, opec_member=True, trade_balance=2),
        "solaria":  _country( 11.0, 10.0, opec_member=True, trade_balance=8),
        # Non-OPEC producer
        "columbia": _country(280.0, 13.0, trade_balance=-12),
        # Importers (filler for world_state demand side)
        "albion":   _country( 33.0, 0),
        "bharata":  _country( 42.0, 0),
        "cathay":   _country(190.0, 0),
        "gallia":   _country( 34.0, 0),
        "teutonia": _country( 45.0, 0),
        "yamato":   _country( 43.0, 0),
    }


# ===========================================================================
# 1. CONSTANTS LOCKED
# ===========================================================================


class TestConstantsLocked:
    def test_multipliers(self):
        assert OPEC_PRODUCTION_MULTIPLIER == {
            "min": 0.70,
            "low": 0.85,
            "normal": 1.00,
            "high": 1.15,
            "max": 1.30,
        }

    def test_min_is_70_percent(self):
        assert OPEC_PRODUCTION_MULTIPLIER["min"] == 0.70

    def test_max_is_130_percent(self):
        assert OPEC_PRODUCTION_MULTIPLIER["max"] == 1.30

    def test_normal_is_unity(self):
        assert OPEC_PRODUCTION_MULTIPLIER["normal"] == 1.00


# ===========================================================================
# 2. OIL PRICE — baseline
# ===========================================================================


def _run(world, opec_production):
    """Call calc_oil_price with common defaults, return (price, supply_implied)."""
    result, _ = calc_oil_price(
        countries=world,
        opec_production=opec_production,
        chokepoint_status={},
        active_blockades={},
        formosa_blockade=False,
        wars=[],
        previous_oil_price=80.0,
        oil_above_150_rounds=0,
        sanctions={},
        log=[],
    )
    return result.price, result.supply


class TestBaselineOil:
    def test_no_opec_decisions_at_starting_state(self, world):
        """No explicit OPEC decisions → supply stays at baseline (~1.0), price near $80."""
        price, supply = _run(world, {})
        assert 70.0 < price < 90.0, f"baseline oil out of expected range: {price}"
        assert 0.9 < supply < 1.1

    def test_all_normal_same_as_no_decision(self, world):
        """All OPEC members at 'normal' is equivalent to no decisions (zero contribution)."""
        price_no_decisions, supply_no = _run(world, {})
        price_all_normal, supply_all_normal = _run(
            world,
            {m: "normal" for m in ("caribe", "mirage", "persia", "sarmatia", "solaria")},
        )
        assert price_no_decisions == price_all_normal
        assert supply_no == supply_all_normal


# ===========================================================================
# 3. SINGLE MEMBER DECISION — effect per share
# ===========================================================================
#
# Canonical math:
#   supply_delta = (multiplier - 1.0) × member_share × 2.0
#
# With the test world (total mbpd = 0.8+3.5+3.5+10+10+13 = 40.8):
#   Solaria share: 10.0 / 40.8 ≈ 0.2451
#   Sarmatia share: 10.0 / 40.8 ≈ 0.2451
#   Persia share: 3.5 / 40.8 ≈ 0.0858
#   Mirage share: 3.5 / 40.8 ≈ 0.0858
#   Caribe share: 0.8 / 40.8 ≈ 0.0196
#   Columbia share: 13.0 / 40.8 ≈ 0.3186
# ---------------------------------------------------------------------------


class TestSingleMemberDecision:
    def test_solaria_min_drops_supply(self, world):
        """Solaria alone at min: supply_delta = -0.30 × 0.2451 × 2.0 = -0.1471"""
        _, supply_min = _run(world, {"solaria": "min"})
        _, supply_base = _run(world, {})
        delta = supply_min - supply_base
        assert delta == pytest.approx(-0.1471, abs=0.005)

    def test_solaria_max_raises_supply(self, world):
        """Solaria alone at max: supply_delta = +0.30 × 0.2451 × 2.0 = +0.1471"""
        _, supply_max = _run(world, {"solaria": "max"})
        _, supply_base = _run(world, {})
        delta = supply_max - supply_base
        assert delta == pytest.approx(0.1471, abs=0.005)

    def test_caribe_min_is_smallest_effect(self, world):
        """Caribe is the smallest producer → smallest per-decision effect."""
        _, supply_caribe_min = _run(world, {"caribe": "min"})
        _, supply_base = _run(world, {})
        delta = supply_caribe_min - supply_base
        # Caribe share ≈ 0.0196, so delta ≈ -0.30 × 0.0196 × 2 = -0.0118
        assert delta == pytest.approx(-0.0118, abs=0.002)

    def test_sarmatia_and_solaria_equal_shares(self, world):
        """Sarmatia and Solaria both have 10 mbpd → equal supply deltas."""
        _, supply_sarm = _run(world, {"sarmatia": "min"})
        _, supply_sol = _run(world, {"solaria": "min"})
        assert supply_sarm == pytest.approx(supply_sol, abs=1e-6)

    def test_min_raises_price(self, world):
        """All OPEC+ at min → supply drops → price rises."""
        all_members = {"caribe", "mirage", "persia", "sarmatia", "solaria"}
        price_min, _ = _run(world, {m: "min" for m in all_members})
        price_base, _ = _run(world, {})
        assert price_min > price_base

    def test_max_drops_price(self, world):
        """All OPEC+ at max → supply rises → price drops."""
        all_members = {"caribe", "mirage", "persia", "sarmatia", "solaria"}
        price_max, _ = _run(world, {m: "max" for m in all_members})
        price_base, _ = _run(world, {})
        assert price_max < price_base


# ===========================================================================
# 4. 2× CARTEL LEVERAGE — explicit verification
# ===========================================================================


class TestCartelLeverage:
    def test_leverage_doubles_effect(self, world):
        """supply_delta with 2× leverage should be 2× the naive delta.

        Naive: (mult-1) × share         (what you'd get without cartel leverage)
        Engine: (mult-1) × share × 2.0  (what the engine actually does)

        We check by computing the delta and comparing to the naive prediction × 2.
        """
        _, supply_base = _run(world, {})
        _, supply_solaria_min = _run(world, {"solaria": "min"})
        delta = supply_solaria_min - supply_base

        # Solaria share
        total_mbpd = sum(
            c["economic"]["oil_production_mbpd"]
            for c in world.values()
            if c["economic"]["oil_producer"]
        )
        solaria_share = 10.0 / total_mbpd
        naive_delta = (0.70 - 1.0) * solaria_share  # no leverage
        with_leverage = naive_delta * 2.0

        assert delta == pytest.approx(with_leverage, abs=1e-4)


# ===========================================================================
# 5. NON-OPEC PRODUCERS ARE NOT AFFECTED BY OPEC DICT
# ===========================================================================


class TestNonOpecImmune:
    def test_columbia_not_in_opec_dict(self, world):
        """A set_opec decision on Columbia should NOT affect supply — Columbia
        isn't (yet) in opec_production dict, only OPEC+ members are.
        If somehow Columbia ends up in the dict (bug), the engine would apply it.
        This test documents the current intended state: non-members aren't there.
        """
        # Baseline: no decisions
        _, supply_base = _run(world, {})
        # With a hypothetical columbia="min" in the dict, the engine WOULD apply it
        # because the engine doesn't check opec_member — it only checks producer_output.
        # This test documents the implicit contract: the validator + persistence
        # handler MUST ensure only OPEC+ members ever end up in the dict.
        _, supply_with_columbia = _run(world, {"columbia": "min"})
        # If columbia is in producer_output (which it is), the engine applies
        # the delta. This is the known gap documented in CONTRACT_OPEC §6.
        assert supply_with_columbia != supply_base  # delta applied — gap documented

    def test_validator_must_gate_membership(self, world):
        """This test documents the contract: the validator + resolve_round handler
        are responsible for ensuring non-OPEC members never reach this code path.
        The engine does not enforce membership."""
        from engine.services.opec_validator import (
            CANONICAL_OPEC_MEMBERS,
            validate_opec_decision,
        )
        report = validate_opec_decision({
            "action_type": "set_opec",
            "country_code": "columbia",
            "round_num": 1,
            "decision": "change",
            "rationale": "This should never reach the engine because the validator rejects it.",
            "changes": {"production_level": "min"},
        })
        assert not report["valid"]
        assert any("NOT_OPEC_MEMBER" in e for e in report["errors"])
        assert "columbia" not in CANONICAL_OPEC_MEMBERS


# ===========================================================================
# 6. SYMMETRY — equal magnitude in opposite directions
# ===========================================================================


class TestSymmetry:
    def test_min_and_max_are_symmetric_deltas(self, world):
        """'min' (0.70) and 'max' (1.30) are symmetric around 1.0 → equal-magnitude
        opposite-sign supply deltas for the same member."""
        _, supply_base = _run(world, {})
        _, supply_min = _run(world, {"solaria": "min"})
        _, supply_max = _run(world, {"solaria": "max"})
        delta_min = supply_min - supply_base
        delta_max = supply_max - supply_base
        assert delta_min == pytest.approx(-delta_max, abs=1e-6)

    def test_low_and_high_are_symmetric_deltas(self, world):
        """'low' (0.85) and 'high' (1.15) are symmetric around 1.0."""
        _, supply_base = _run(world, {})
        _, supply_low = _run(world, {"solaria": "low"})
        _, supply_high = _run(world, {"solaria": "high"})
        delta_low = supply_low - supply_base
        delta_high = supply_high - supply_base
        assert delta_low == pytest.approx(-delta_high, abs=1e-6)

    def test_low_is_half_of_min(self, world):
        """'low' (0.85) is half the intensity of 'min' (0.70) from normal (1.00)."""
        _, supply_base = _run(world, {})
        _, supply_low = _run(world, {"solaria": "low"})
        _, supply_min = _run(world, {"solaria": "min"})
        delta_low = supply_low - supply_base
        delta_min = supply_min - supply_base
        # low = -0.15 × share × 2, min = -0.30 × share × 2 → ratio is 1/2
        assert delta_low == pytest.approx(delta_min / 2, abs=1e-6)


# ===========================================================================
# 7. COLLECTIVE DECISION — all OPEC+ at max
# ===========================================================================


class TestCollectiveDecision:
    def test_all_opec_at_max_floods_market(self, world):
        """All 5 OPEC+ members at max → significant price drop."""
        opec = {"caribe": "max", "mirage": "max", "persia": "max",
                "sarmatia": "max", "solaria": "max"}
        price_all_max, supply_all_max = _run(world, opec)
        price_base, supply_base = _run(world, {})

        assert price_all_max < price_base
        # Combined supply boost: sum of (0.30 × share × 2) for all 5 members
        # OPEC+ total share = (0.8+3.5+3.5+10+10) / 40.8 ≈ 0.6814
        # Delta = 0.30 × 0.6814 × 2 ≈ 0.4088
        delta = supply_all_max - supply_base
        assert delta == pytest.approx(0.4088, abs=0.01)

    def test_all_opec_at_min_starves_market(self, world):
        """All 5 OPEC+ members at min → significant price rise."""
        opec = {"caribe": "min", "mirage": "min", "persia": "min",
                "sarmatia": "min", "solaria": "min"}
        price_all_min, _ = _run(world, opec)
        price_base, _ = _run(world, {})
        assert price_all_min > price_base
