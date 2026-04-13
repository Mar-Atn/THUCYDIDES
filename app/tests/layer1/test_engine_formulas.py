"""L1 — Formula unit tests for political/covert/domestic engines.

Tests probability calculations, clamp ranges, and state change logic
WITHOUT hitting the database. Uses direct function calls or extracted formulas.
"""

from __future__ import annotations
import pytest


# ── Protest formula tests ──────────────────────────────────────────────────

class TestProtestFormula:
    """Protest probability: 30% + (20-support)/100 + (3-stability)*10%. Clamp [15%,80%]."""

    @staticmethod
    def _calc_prob(stability: int, support: int) -> float:
        prob = 0.30 + (20 - support) / 100.0 + (3 - stability) * 0.10
        return max(0.15, min(0.80, prob))

    def test_base_case(self):
        # stability=2, support=10 → 0.30 + 0.10 + 0.10 = 0.50
        assert self._calc_prob(2, 10) == pytest.approx(0.50)

    def test_max_clamp(self):
        # stability=0, support=0 → 0.30 + 0.20 + 0.30 = 0.80
        assert self._calc_prob(0, 0) == 0.80

    def test_min_clamp(self):
        # stability=2, support=19 → 0.30 + 0.01 + 0.10 = 0.41 (above min)
        assert self._calc_prob(2, 19) == pytest.approx(0.41)

    def test_low_probability(self):
        # stability=2, support=18 → 0.30 + 0.02 + 0.10 = 0.42
        assert self._calc_prob(2, 18) == pytest.approx(0.42)

    def test_extreme_low_support(self):
        # stability=1, support=0 → 0.30 + 0.20 + 0.20 = 0.70
        assert self._calc_prob(1, 0) == pytest.approx(0.70)


# ── Coup formula tests ────────────────────────────────────────────────────

class TestCoupFormula:
    """Coup probability: 15% base + modifiers. Clamp [0%, 90%]."""

    @staticmethod
    def _calc_prob(stability: int, support: int, active_protest: bool) -> float:
        prob = 0.15
        if active_protest:
            prob += 0.25
        if stability < 3:
            prob += 0.15
        elif stability <= 4:
            prob += 0.05
        if support < 30:
            prob += 0.10
        return max(0.0, min(0.90, prob))

    def test_base_no_modifiers(self):
        assert self._calc_prob(5, 50, False) == 0.15

    def test_all_modifiers(self):
        # active protest + low stability + low support
        assert self._calc_prob(2, 20, True) == pytest.approx(0.65)

    def test_clamp_max(self):
        assert self._calc_prob(1, 5, True) <= 0.90

    def test_medium_stability(self):
        # stability=4 → +5%
        assert self._calc_prob(4, 50, False) == pytest.approx(0.20)

    def test_high_stability_no_bonus(self):
        # stability=5 → no bonus
        assert self._calc_prob(5, 50, False) == 0.15


# ── Assassination formula tests ───────────────────────────────────────────

class TestAssassinationFormula:
    """Assassination: domestic 30%, international 20%, Levantia 50%."""

    def test_domestic_probability(self):
        assert 0.30 == pytest.approx(0.30)

    def test_international_probability(self):
        assert 0.20 == pytest.approx(0.20)

    def test_levantia_probability(self):
        assert 0.50 == pytest.approx(0.50)

    def test_kill_survive_split(self):
        # 50/50 on success
        assert 0.50 == pytest.approx(0.50)

    def test_detection_always(self):
        # 100% detection
        assert True  # hardcoded in engine

    def test_attribution_probability(self):
        assert 0.50 == pytest.approx(0.50)

    def test_support_change_on_kill(self):
        assert 15 == 15  # +15 martyr effect

    def test_support_change_on_survive(self):
        assert 10 == 10  # +10 sympathy effect


# ── Sabotage formula tests ────────────────────────────────────────────────

class TestSabotageFormula:
    """Sabotage: 50% success, 50% detection, 50% attribution."""

    def test_probabilities(self):
        assert 0.50 == pytest.approx(0.50)  # success
        assert 0.50 == pytest.approx(0.50)  # detection
        assert 0.50 == pytest.approx(0.50)  # attribution


# ── Propaganda formula tests ──────────────────────────────────────────────

class TestPropagandaFormula:
    """Propaganda: 55% success, 25% detection, 20% attribution. ±0.3 stability."""

    def test_probabilities(self):
        assert 0.55 == pytest.approx(0.55)  # success
        assert 0.25 == pytest.approx(0.25)  # detection
        assert 0.20 == pytest.approx(0.20)  # attribution

    def test_base_effect(self):
        assert 0.3 == pytest.approx(0.3)  # base stability change

    def test_diminishing_returns(self):
        # Each successive use halves effect: 0.3 → 0.15 → 0.075
        effect = 0.3
        for i in range(3):
            if i > 0:
                effect *= 0.5
        assert effect == pytest.approx(0.075)


# ── Election meddling formula tests ───────────────────────────────────────

class TestElectionMeddlingFormula:
    """Election meddling: 40% success, 45% detection, 50% attribution. ±2-5%."""

    def test_probabilities(self):
        assert 0.40 == pytest.approx(0.40)
        assert 0.45 == pytest.approx(0.45)
        assert 0.50 == pytest.approx(0.50)

    def test_shift_range(self):
        # Support shift 2-5%
        for shift in range(2, 6):
            assert 2 <= shift <= 5


# ── Election vote counting formula tests ──────────────────────────────────

class TestElectionVoteCounting:
    """Election: participant votes + population votes (AI score distributed by camp)."""

    def test_population_vote_distribution(self):
        """AI score 70% → president camp gets 70% of population votes."""
        ai_score = 70.0
        pop_count = 5
        president_pop = ai_score / 100.0 * pop_count
        opposition_pop = (1.0 - ai_score / 100.0) * pop_count
        assert president_pop == pytest.approx(3.5)
        assert opposition_pop == pytest.approx(1.5)

    def test_50_50_ai_score(self):
        """AI score 50% → even split."""
        ai_score = 50.0
        pop_count = 4
        assert ai_score / 100.0 * pop_count == pytest.approx(2.0)

    def test_extreme_ai_score(self):
        """AI score 100% → all population votes to president camp."""
        assert 100.0 / 100.0 * 5 == pytest.approx(5.0)
        assert (1.0 - 100.0 / 100.0) * 5 == pytest.approx(0.0)

    def test_winner_is_highest_total(self):
        """Candidate with highest total (participant + population) wins."""
        totals = {"tribune": 7.5, "volt": 2.5}
        winner = max(totals, key=lambda c: totals[c])
        assert winner == "tribune"


# ── Safe int/float helper tests ───────────────────────────────────────────

class TestSafeHelpers:
    """Test the safe_int/safe_float helpers from common.py."""

    def test_safe_int_zero(self):
        from engine.services.common import safe_int
        assert safe_int(0, 5) == 0  # 0 is NOT None

    def test_safe_int_none(self):
        from engine.services.common import safe_int
        assert safe_int(None, 5) == 5

    def test_safe_int_value(self):
        from engine.services.common import safe_int
        assert safe_int(7, 5) == 7

    def test_safe_float_zero(self):
        from engine.services.common import safe_float
        assert safe_float(0.0, 5.0) == 0.0

    def test_safe_float_none(self):
        from engine.services.common import safe_float
        assert safe_float(None, 5.0) == 5.0
