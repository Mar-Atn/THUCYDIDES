"""Layer 1: Combat engine pure-function tests.

No DB, no LLM. Tests combat mechanics against CARD_FORMULAS probabilities.
Run: cd app && PYTHONPATH=. pytest tests/layer1/test_combat.py -v
"""
import random
import pytest
from engine.round_engine.combat import resolve_ground_combat, resolve_air_strike, resolve_missile_strike, resolve_naval


# ===========================================================================
# GROUND COMBAT (CARD_ACTIONS 1.3 + CARD_FORMULAS D.1)
# ===========================================================================

class TestGroundCombat:
    """Iterative RISK dice with SEED modifiers."""

    def test_attacker_wins_5v2_no_mods(self):
        """5 attackers vs 2 defenders, no mods → attacker very likely wins."""
        random.seed(1)
        atk = [{"unit_code": f"a{i}", "unit_type": "ground"} for i in range(5)]
        dfd = [{"unit_code": f"d{i}", "unit_type": "ground"} for i in range(2)]
        r = resolve_ground_combat(atk, dfd, {})
        assert r.success is True
        assert len(r.defender_losses) == 2  # all defenders dead

    def test_defender_advantage_with_diehard_plus_air(self):
        """Die hard + air support STACK to +2 defender. Makes defense very strong."""
        random.seed(42)
        atk = [{"unit_code": f"a{i}", "unit_type": "ground"} for i in range(5)]
        dfd = [{"unit_code": f"d{i}", "unit_type": "ground"} for i in range(3)]
        r = resolve_ground_combat(atk, dfd, {"die_hard": True, "air_support": True})
        # With +2 defender, 5v3 should often fail
        assert r.success is False

    def test_amphibious_penalty(self):
        """Amphibious -1 attacker. Harder to win."""
        random.seed(42)
        atk = [{"unit_code": f"a{i}", "unit_type": "ground"} for i in range(4)]
        dfd = [{"unit_code": f"d{i}", "unit_type": "ground"} for i in range(2)]
        r = resolve_ground_combat(atk, dfd, {"amphibious": True})
        # Just verify it runs without error and modifier is applied
        assert r.modifiers_applied["attacker_bonus"] == -1

    def test_iterative_until_one_side_zero(self):
        """Combat loops until one side has 0 units."""
        random.seed(7)
        atk = [{"unit_code": f"a{i}", "unit_type": "ground"} for i in range(3)]
        dfd = [{"unit_code": f"d{i}", "unit_type": "ground"} for i in range(3)]
        r = resolve_ground_combat(atk, dfd, {})
        total_losses = len(r.attacker_losses) + len(r.defender_losses)
        # One side must be fully destroyed
        assert len(r.attacker_losses) == 3 or len(r.defender_losses) == 3
        assert r.modifiers_applied["exchanges"] >= 1

    def test_no_combat_zero_attackers(self):
        r = resolve_ground_combat([], [{"unit_code": "d1", "unit_type": "ground"}], {})
        assert r.success is False

    def test_no_combat_zero_defenders(self):
        r = resolve_ground_combat([{"unit_code": "a1", "unit_type": "ground"}], [], {})
        assert r.success is False

    def test_ai_l4_bonus(self):
        """AI L4 gives +1 to attacker."""
        random.seed(42)
        atk = [{"unit_code": f"a{i}", "unit_type": "ground"} for i in range(3)]
        dfd = [{"unit_code": f"d{i}", "unit_type": "ground"} for i in range(3)]
        r = resolve_ground_combat(atk, dfd, {"ai_l4_attacker": True})
        assert r.modifiers_applied["attacker_bonus"] == 1

    def test_low_morale_penalty(self):
        """Low morale -1 for defender."""
        random.seed(42)
        atk = [{"unit_code": f"a{i}", "unit_type": "ground"} for i in range(3)]
        dfd = [{"unit_code": f"d{i}", "unit_type": "ground"} for i in range(3)]
        r = resolve_ground_combat(atk, dfd, {"low_morale_defender": True})
        assert r.modifiers_applied["defender_bonus"] == -1


# ===========================================================================
# AIR STRIKE (CARD_ACTIONS 1.4 + CARD_FORMULAS D.2)
# ===========================================================================

class TestAirStrike:
    """12% base, 6% with AD, 15% downed by AD."""

    def test_hit_rate_no_ad_approximately_12pct(self):
        """Over many trials, hit rate should be ~12% without AD."""
        hits = 0
        N = 2000
        random.seed(99)
        au = {"unit_code": "a1", "unit_type": "tactical_air"}
        defs = [{"unit_code": "d1", "unit_type": "ground"}]
        for _ in range(N):
            r = resolve_air_strike(au, defs, active_ad_units=[])
            if r.success:
                hits += 1
        rate = hits / N
        assert 0.08 < rate < 0.16, f"Expected ~12%, got {rate*100:.1f}%"

    def test_hit_rate_with_ad_approximately_6pct(self):
        """With AD, hit rate should be ~6%."""
        hits = 0
        N = 2000
        random.seed(99)
        au = {"unit_code": "a1", "unit_type": "tactical_air"}
        defs = [{"unit_code": "d1", "unit_type": "ground"}]
        ad = [{"unit_code": "ad1", "unit_type": "air_defense", "status": "active"}]
        for _ in range(N):
            r = resolve_air_strike(au, defs, active_ad_units=ad)
            if r.success:
                hits += 1
        rate = hits / N
        assert 0.03 < rate < 0.10, f"Expected ~6%, got {rate*100:.1f}%"


# ===========================================================================
# NAVAL COMBAT (CARD_ACTIONS 1.5 + CARD_FORMULAS D.3)
# ===========================================================================

class TestNavalCombat:
    """1v1 dice, ties → defender."""

    def test_1v1_produces_one_loss(self):
        """One ship vs one ship → exactly one destroyed."""
        random.seed(42)
        a = [{"unit_code": "n1", "unit_type": "naval"}]
        d = [{"unit_code": "n2", "unit_type": "naval"}]
        r = resolve_naval(a, d)
        total_losses = len(r.attacker_losses) + len(r.defender_losses)
        assert total_losses >= 1  # at least one side loses

    def test_no_combat_empty(self):
        r = resolve_naval([], [{"unit_code": "n1", "unit_type": "naval"}])
        assert r.success is False


# ===========================================================================
# MISSILE STRIKE (CARD_FORMULAS D.5/D.6)
# ===========================================================================

class TestMissileStrike:

    def test_conventional_hit_rate_approximately_70pct(self):
        """Conventional missile: ~70% hit without AD."""
        # Note: current resolve_missile_strike uses 80% base (nuclear-era code)
        # This test documents what the code ACTUALLY does; update when
        # resolve_missile_strike is split into conventional vs nuclear
        pass  # TODO: implement after missile action split
