"""Layer 2 Calibration Test — Combat Probability Distribution Verification.

Statistical tests that run combat functions many times and verify outcome
distributions match CARD_FORMULAS.md probabilities. Pure function tests
(no DB, no LLM) — "L1 calibration" in spirit, filed under layer2/ because
they verify calibrated behaviour across many trials rather than single
deterministic cases.

Reference:
  CARD_FORMULAS.md  D.1 (Ground), D.2 (Air), D.3 (Naval), D.5 (Missile)
  CARD_ACTIONS.md   1.3-1.5, 1.8

Run::

    cd app && PYTHONPATH=. python3 -m pytest tests/layer2/test_calibration_combat.py -v -s

"""
from __future__ import annotations

import random
from collections import Counter

import pytest

from engine.round_engine.combat import (
    resolve_ground_combat,
    resolve_air_strike,
    resolve_missile_strike,
    resolve_naval,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ground(prefix: str, n: int) -> list[dict]:
    """Create ``n`` ground unit dicts with sequential codes."""
    return [{"unit_code": f"{prefix}{i}", "unit_type": "ground"} for i in range(n)]


def _make_naval(prefix: str, n: int) -> list[dict]:
    return [{"unit_code": f"{prefix}{i}", "unit_type": "naval"} for i in range(n)]


def _make_air(code: str = "air1") -> dict:
    return {"unit_code": code, "unit_type": "tactical_air"}


def _make_ad(code: str = "ad1", status: str = "active") -> list[dict]:
    return [{"unit_code": code, "unit_type": "air_defense", "status": status}]


def _pct(label: str, count: int, total: int) -> str:
    """Format a percentage string for informative output."""
    return f"  {label}: {count}/{total} = {count / total * 100:.1f}%"


# ===========================================================================
# 1. GROUND COMBAT — RISK iterative (CARD_FORMULAS D.1)
# ===========================================================================

class TestGroundCalibration:
    """Statistical tests for ground combat distributions."""

    TRIALS = 100

    def test_5v3_attacker_wins_majority(self):
        """5 attackers vs 3 defenders, no modifiers.

        With 3 dice vs 2 dice and a numbers advantage, attacker should win
        the majority of engagements. CARD_FORMULAS single-comparison attacker
        win rate is 42%, but with 5v3 iterative the overall attacker win rate
        should be substantially higher due to dice advantage.

        Expected: attacker wins 60-80% of trials.
        """
        wins = 0
        total_att_losses = 0
        total_def_losses = 0

        for _ in range(self.TRIALS):
            atk = _make_ground("a", 5)
            dfd = _make_ground("d", 3)
            r = resolve_ground_combat(atk, dfd, {})
            if r.success:
                wins += 1
            total_att_losses += len(r.attacker_losses)
            total_def_losses += len(r.defender_losses)

        win_rate = wins / self.TRIALS
        avg_att_loss = total_att_losses / self.TRIALS
        avg_def_loss = total_def_losses / self.TRIALS

        print(f"\n--- Ground 5v3 no mods ({self.TRIALS} trials) ---")
        print(_pct("Attacker win rate", wins, self.TRIALS))
        print(f"  Avg attacker losses: {avg_att_loss:.2f}")
        print(f"  Avg defender losses: {avg_def_loss:.2f}")

        assert 0.50 <= win_rate <= 0.90, (
            f"Attacker win rate {win_rate:.2%} outside [50%, 90%] for 5v3"
        )
        # Attacker should take SOME losses (not free wins)
        assert avg_att_loss > 0.3, (
            f"Avg attacker losses {avg_att_loss:.2f} too low — combat too easy"
        )
        # Defender should lose more on average (they are outnumbered)
        assert avg_def_loss > avg_att_loss, (
            f"Defender losses ({avg_def_loss:.2f}) should exceed attacker "
            f"losses ({avg_att_loss:.2f}) in 5v3"
        )

    def test_3v3_roughly_balanced(self):
        """3v3 even fight. Neither side should dominate overwhelmingly.

        CARD_FORMULAS says single-comparison attacker wins 42%, defender
        wins 58% (ties go to defender). So defender should have an edge.
        """
        wins = 0
        for _ in range(self.TRIALS):
            r = resolve_ground_combat(_make_ground("a", 3), _make_ground("d", 3), {})
            if r.success:
                wins += 1

        win_rate = wins / self.TRIALS
        print(f"\n--- Ground 3v3 no mods ({self.TRIALS} trials) ---")
        print(_pct("Attacker win rate", wins, self.TRIALS))

        # Defender has slight edge due to ties, but either can win
        assert 0.20 <= win_rate <= 0.65, (
            f"Attacker win rate {win_rate:.2%} outside [20%, 65%] for 3v3"
        )

    # -----------------------------------------------------------------------
    # 2. Die Hard modifier
    # -----------------------------------------------------------------------

    def test_die_hard_helps_defender(self):
        """Die hard (+1 defender) should shift outcomes toward defender.

        Run 3v3 baseline and 3v3 with die_hard, compare.
        """
        baseline_wins = 0
        dh_wins = 0

        for _ in range(self.TRIALS):
            r_base = resolve_ground_combat(
                _make_ground("a", 3), _make_ground("d", 3), {}
            )
            if r_base.success:
                baseline_wins += 1

            r_dh = resolve_ground_combat(
                _make_ground("a", 3), _make_ground("d", 3), {"die_hard": True}
            )
            if r_dh.success:
                dh_wins += 1

        print(f"\n--- Die Hard effect ({self.TRIALS} trials, 3v3) ---")
        print(_pct("Baseline attacker wins", baseline_wins, self.TRIALS))
        print(_pct("Die Hard attacker wins", dh_wins, self.TRIALS))

        # Die hard should reduce attacker win rate
        assert dh_wins <= baseline_wins + 10, (
            f"Die hard should help defender: baseline {baseline_wins}, "
            f"die_hard {dh_wins} (attacker should not win MORE with die_hard)"
        )

    # -----------------------------------------------------------------------
    # 3. Air support stacking
    # -----------------------------------------------------------------------

    def test_air_support_and_stacking(self):
        """Air support (+1 defender) and die_hard + air_support (+2 defender).

        +2 stacked should make defense very strong in 3v3.
        """
        air_wins = 0
        stack_wins = 0

        for _ in range(self.TRIALS):
            r_air = resolve_ground_combat(
                _make_ground("a", 3), _make_ground("d", 3), {"air_support": True}
            )
            if r_air.success:
                air_wins += 1

            r_stack = resolve_ground_combat(
                _make_ground("a", 3), _make_ground("d", 3),
                {"die_hard": True, "air_support": True},
            )
            if r_stack.success:
                stack_wins += 1

        print(f"\n--- Air support stacking ({self.TRIALS} trials, 3v3) ---")
        print(_pct("Air support only — attacker wins", air_wins, self.TRIALS))
        print(_pct("Die Hard + Air (+2) — attacker wins", stack_wins, self.TRIALS))

        # With +2 defender, attacker should win rarely (CARD_FORMULAS: 17% per comparison)
        assert stack_wins < 0.50 * self.TRIALS, (
            f"Stacked +2 defender: attacker wins {stack_wins}/{self.TRIALS} "
            f"— should be well below 50%"
        )
        # Stacking should be stronger than air support alone
        assert stack_wins <= air_wins + 10, (
            f"+2 stack ({stack_wins}) should not exceed air-only ({air_wins}) significantly"
        )

    # -----------------------------------------------------------------------
    # 10. Amphibious penalty
    # -----------------------------------------------------------------------

    def test_amphibious_penalty_reduces_attack(self):
        """Amphibious (-1 attacker) should reduce attacker win rate vs baseline.

        Run 3v3 baseline and 3v3 with amphibious.
        """
        baseline_wins = 0
        amph_wins = 0

        for _ in range(self.TRIALS):
            r_base = resolve_ground_combat(
                _make_ground("a", 3), _make_ground("d", 3), {}
            )
            if r_base.success:
                baseline_wins += 1

            r_amph = resolve_ground_combat(
                _make_ground("a", 3), _make_ground("d", 3), {"amphibious": True}
            )
            if r_amph.success:
                amph_wins += 1

        print(f"\n--- Amphibious penalty ({self.TRIALS} trials, 3v3) ---")
        print(_pct("Baseline attacker wins", baseline_wins, self.TRIALS))
        print(_pct("Amphibious attacker wins", amph_wins, self.TRIALS))

        assert amph_wins <= baseline_wins + 10, (
            f"Amphibious should hurt attacker: baseline {baseline_wins}, "
            f"amphibious {amph_wins}"
        )
        # Verify the modifier is correctly applied
        r = resolve_ground_combat(
            _make_ground("a", 3), _make_ground("d", 3), {"amphibious": True}
        )
        assert r.modifiers_applied["attacker_bonus"] == -1


# ===========================================================================
# 4-6. AIR STRIKE (CARD_FORMULAS D.2)
# ===========================================================================

class TestAirStrikeCalibration:
    """Statistical tests for air strike hit rates.

    CARD_FORMULAS D.2:
      - 12% base hit (no AD)
      - 6% hit (AD present, halved)
      - 15% attacker downed by AD (implemented 2026-04-09, DISC-2 fixed)
    """

    TRIALS = 500

    def test_no_ad_hit_rate_around_12pct(self):
        """Air strike with no AD: expected 12% hit rate.

        CARD_FORMULAS: 12% base. Bounds: [8%, 16%].
        """
        hits = 0
        air = _make_air("a_air1")
        targets = [{"unit_code": "d_ground1", "unit_type": "ground"}]

        for _ in range(self.TRIALS):
            r = resolve_air_strike(air, targets, active_ad_units=[])
            if r.success:
                hits += 1

        rate = hits / self.TRIALS
        print(f"\n--- Air strike NO AD ({self.TRIALS} trials) ---")
        print(_pct("Hit rate", hits, self.TRIALS))
        print(f"  Expected: ~12%  Bounds: [8%, 16%]")

        assert 0.08 <= rate <= 0.16, (
            f"Air strike hit rate {rate:.2%} outside [8%, 16%] (expected ~12%)"
        )

    def test_with_ad_hit_rate_around_6pct(self):
        """Air strike with AD present: expected 6% hit rate (halved).

        CARD_FORMULAS: 6% with AD. Bounds: [3%, 10%].
        """
        hits = 0
        air = _make_air("a_air1")
        targets = [{"unit_code": "d_ground1", "unit_type": "ground"}]
        ad = _make_ad("d_ad1")

        for _ in range(self.TRIALS):
            r = resolve_air_strike(air, targets, active_ad_units=ad)
            if r.success:
                hits += 1

        rate = hits / self.TRIALS
        print(f"\n--- Air strike WITH AD ({self.TRIALS} trials) ---")
        print(_pct("Hit rate", hits, self.TRIALS))
        print(f"  Expected: ~6%  Bounds: [3%, 10%]")

        assert 0.03 <= rate <= 0.10, (
            f"Air strike hit rate with AD {rate:.2%} outside [3%, 10%] (expected ~6%)"
        )

    def test_ad_halves_effectiveness(self):
        """AD should roughly halve the hit rate compared to no-AD."""
        hits_no_ad = 0
        hits_ad = 0
        air = _make_air("a_air1")
        targets = [{"unit_code": "d_ground1", "unit_type": "ground"}]
        ad = _make_ad("d_ad1")

        for _ in range(self.TRIALS):
            r1 = resolve_air_strike(air, targets, active_ad_units=[])
            if r1.success:
                hits_no_ad += 1
            r2 = resolve_air_strike(air, targets, active_ad_units=ad)
            if r2.success:
                hits_ad += 1

        rate_no_ad = hits_no_ad / self.TRIALS
        rate_ad = hits_ad / self.TRIALS
        print(f"\n--- AD halving check ({self.TRIALS} trials) ---")
        print(f"  No AD: {rate_no_ad:.2%}   With AD: {rate_ad:.2%}")
        print(f"  Ratio: {rate_ad / rate_no_ad:.2f}x" if rate_no_ad > 0 else "  No AD hits!")

        # AD should reduce rate — allow generous margin
        assert rate_ad < rate_no_ad, (
            f"AD rate ({rate_ad:.2%}) should be lower than no-AD ({rate_no_ad:.2%})"
        )

    def test_attacker_downed_by_ad_15pct(self):
        """Air unit downed by AD: expected 15%.

        CARD_FORMULAS D.2: "If AD covers target zone -> 15% chance attacker
        is DOWNED (unit destroyed, attack fails)". This mechanic is NOT in
        the current resolve_air_strike — it only models hits on defenders.

        When implemented, check: attacker_losses populated, rate ~15%.
        """
        downed = 0
        air = _make_air("a_air1")
        targets = [{"unit_code": "d_ground1", "unit_type": "ground"}]
        ad = _make_ad("d_ad1")

        for _ in range(self.TRIALS):
            r = resolve_air_strike(air, targets, active_ad_units=ad)
            if r.attacker_losses:
                downed += 1

        rate = downed / self.TRIALS
        print(f"\n--- Attacker downed by AD ({self.TRIALS} trials) ---")
        print(_pct("Downed rate", downed, self.TRIALS))
        print(f"  Expected: ~15%  Bounds: [10%, 20%]")

        assert 0.10 <= rate <= 0.20, (
            f"Downed rate {rate:.2%} outside [10%, 20%] (expected ~15%)"
        )


# ===========================================================================
# 7. NAVAL COMBAT 1v1 (CARD_FORMULAS D.3)
# ===========================================================================

class TestNavalCalibration:
    """Statistical tests for naval 1v1 combat.

    CARD_FORMULAS D.3: "One ship vs one ship. Each rolls 1d6 + modifiers.
    Higher wins. Ties -> defender."

    With 1v1, no modifiers, attacker must roll strictly higher to win.
    P(attacker wins 1d6 vs 1d6, ties to defender) = 15/36 = 41.7%.
    """

    TRIALS = 200

    def test_1v1_roughly_balanced(self):
        """1v1 naval, no modifiers. Each side should win a meaningful share.

        Theoretical: attacker wins 41.7% (15/36). Bounds: [30%, 55%].
        """
        att_wins = 0
        for _ in range(self.TRIALS):
            a = _make_naval("na", 1)
            d = _make_naval("nd", 1)
            r = resolve_naval(a, d)
            # Attacker "wins" if defender lost a ship
            if len(r.defender_losses) > len(r.attacker_losses):
                att_wins += 1

        rate = att_wins / self.TRIALS
        print(f"\n--- Naval 1v1 ({self.TRIALS} trials) ---")
        print(_pct("Attacker wins", att_wins, self.TRIALS))
        print(f"  Theoretical: 41.7%  Bounds: [30%, 55%]")

        assert 0.30 <= rate <= 0.55, (
            f"Naval 1v1 attacker win rate {rate:.2%} outside [30%, 55%]"
        )

    def test_1v1_always_produces_loss(self):
        """Every 1v1 naval engagement should destroy at least one ship."""
        for _ in range(50):
            r = resolve_naval(_make_naval("na", 1), _make_naval("nd", 1))
            total = len(r.attacker_losses) + len(r.defender_losses)
            assert total >= 1, "Naval 1v1 must destroy at least one ship"


# ===========================================================================
# 8. CONVENTIONAL MISSILE (CARD_FORMULAS D.5)
# ===========================================================================

class TestMissileCalibration:
    """Statistical tests for conventional missile strikes.

    CARD_FORMULAS D.5: MISSILE_CONV hit = 70% base.
    AD intercept: per-unit 50% roll (1 AD = 50%, 2 AD = 75%, 3 AD = 87.5%).
    Code aligned to CARD as of 2026-04-09 (DISC-1 + DISC-4 fixed).
    """

    TRIALS = 200

    def test_conventional_no_ad_hit_rate(self):
        """Conventional missile, no AD: 70% base (CARD_FORMULAS D.5).

        Bounds: [60%, 80%] (centered on 70%).
        """
        hits = 0
        missile = {"unit_code": "m1", "unit_type": "strategic_missile"}
        target = {"unit_code": "t1", "unit_type": "ground"}

        for _ in range(self.TRIALS):
            r = resolve_missile_strike(missile, target, active_ad_units=[])
            if r.success:
                hits += 1

        rate = hits / self.TRIALS
        print(f"\n--- Missile conventional NO AD ({self.TRIALS} trials) ---")
        print(_pct("Hit rate", hits, self.TRIALS))
        print(f"  Code base: 70%  Bounds: [60%, 80%]")

        assert 0.60 <= rate <= 0.80, (
            f"Missile hit rate {rate:.2%} outside [60%, 80%] (code base=70%)"
        )

    def test_conventional_with_1ad_hit_rate(self):
        """Conventional missile with 1 AD: per-unit 50% intercept, then 70% hit.

        Expected hit rate: 50% pass intercept * 70% hit = 35%.
        Bounds: [25%, 45%].
        """
        hits = 0
        missile = {"unit_code": "m1", "unit_type": "strategic_missile"}
        target = {"unit_code": "t1", "unit_type": "ground"}
        ad = _make_ad("d_ad1")

        for _ in range(self.TRIALS):
            r = resolve_missile_strike(missile, target, active_ad_units=ad)
            if r.success:
                hits += 1

        rate = hits / self.TRIALS
        print(f"\n--- Missile conventional WITH 1 AD ({self.TRIALS} trials) ---")
        print(_pct("Hit rate", hits, self.TRIALS))
        print(f"  Expected: ~35% (50% pass * 70% hit)  Bounds: [25%, 45%]")

        assert 0.25 <= rate <= 0.45, (
            f"Missile hit rate with 1 AD {rate:.2%} outside [25%, 45%]"
        )

    def test_conventional_with_2ad_hit_rate(self):
        """Conventional missile with 2 AD: intercept_prob = 75%, then 70% hit.

        Expected hit rate: 25% pass intercept * 70% hit = 17.5%.
        Bounds: [10%, 25%].
        """
        hits = 0
        missile = {"unit_code": "m1", "unit_type": "strategic_missile"}
        target = {"unit_code": "t1", "unit_type": "ground"}
        ad = [
            {"unit_code": "d_ad1", "unit_type": "air_defense", "status": "active"},
            {"unit_code": "d_ad2", "unit_type": "air_defense", "status": "active"},
        ]

        for _ in range(self.TRIALS):
            r = resolve_missile_strike(missile, target, active_ad_units=ad)
            if r.success:
                hits += 1

        rate = hits / self.TRIALS
        print(f"\n--- Missile conventional WITH 2 AD ({self.TRIALS} trials) ---")
        print(_pct("Hit rate", hits, self.TRIALS))
        print(f"  Expected: ~17.5% (25% pass * 70% hit)  Bounds: [10%, 25%]")

        assert 0.10 <= rate <= 0.25, (
            f"Missile hit rate with 2 AD {rate:.2%} outside [10%, 25%]"
        )

    def test_ad_reduces_missile_effectiveness(self):
        """AD should substantially reduce missile hit rate.

        With per-unit 50% intercept model, 1 AD should roughly halve.
        """
        hits_no_ad = 0
        hits_ad = 0
        missile = {"unit_code": "m1", "unit_type": "strategic_missile"}
        target = {"unit_code": "t1", "unit_type": "ground"}
        ad = _make_ad("d_ad1")

        for _ in range(self.TRIALS):
            r1 = resolve_missile_strike(missile, target, active_ad_units=[])
            if r1.success:
                hits_no_ad += 1
            r2 = resolve_missile_strike(missile, target, active_ad_units=ad)
            if r2.success:
                hits_ad += 1

        rate_no = hits_no_ad / self.TRIALS
        rate_ad = hits_ad / self.TRIALS
        print(f"\n--- Missile AD reduction ({self.TRIALS} trials) ---")
        print(f"  No AD: {rate_no:.2%}   With 1 AD: {rate_ad:.2%}")

        assert rate_ad < rate_no * 0.70, (
            f"1 AD ({rate_ad:.2%}) should be <70% of no-AD ({rate_no:.2%})"
        )


# ===========================================================================
# 9. GROUND COMBAT CHAIN — advance after win
# ===========================================================================

class TestGroundAdvance:
    """Verify post-combat properties: attacker advances, unit accounting."""

    def test_attacker_advance_after_win(self):
        """After attacker wins, surviving units should be available to occupy.

        5 attackers vs 2 defenders — attacker should win most trials.
        Verify: total_losses == initial_units (all accounted for),
        and attacker has survivors (>= 1 for occupation).
        """
        advance_possible = 0
        TRIALS = 50

        for _ in range(TRIALS):
            atk = _make_ground("a", 5)
            dfd = _make_ground("d", 2)
            r = resolve_ground_combat(atk, dfd, {})

            if r.success:
                surviving_attackers = 5 - len(r.attacker_losses)
                assert surviving_attackers >= 1, (
                    "Attacker won but has 0 survivors — cannot occupy hex"
                )
                advance_possible += 1

            # Unit accounting: all losses must reference valid unit codes
            all_att_codes = {u["unit_code"] for u in atk}
            all_def_codes = {u["unit_code"] for u in dfd}
            for code in r.attacker_losses:
                assert code in all_att_codes, f"Unknown attacker loss: {code}"
            for code in r.defender_losses:
                assert code in all_def_codes, f"Unknown defender loss: {code}"

        print(f"\n--- Advance after win ({TRIALS} trials, 5v2) ---")
        print(f"  Attacker won and can advance: {advance_possible}/{TRIALS}")
        assert advance_possible > 0, "Attacker should win at least once in 50 trials of 5v2"

    def test_one_side_fully_eliminated(self):
        """Combat must always end with one side at zero units."""
        for _ in range(50):
            atk = _make_ground("a", 4)
            dfd = _make_ground("d", 3)
            r = resolve_ground_combat(atk, dfd, {})

            att_remaining = 4 - len(r.attacker_losses)
            def_remaining = 3 - len(r.defender_losses)

            assert att_remaining == 0 or def_remaining == 0, (
                f"Combat ended with att={att_remaining}, def={def_remaining} "
                f"— one side must reach 0"
            )


# ===========================================================================
# DISCREPANCY LOG (all resolved 2026-04-09 — CARD prevails on all 4)
# ===========================================================================
#
# 1. MISSILE BASE HIT RATE: FIXED — code aligned to 70% (was 80%).
# 2. AIR STRIKE ATTACKER DOWNED: FIXED — 15% downed mechanic implemented.
# 3. NAVAL FLEET BONUS: FIXED — fleet advantage removed, pure 1v1 dice.
# 4. MISSILE AD MODEL: FIXED — per-unit 50% intercept rolls (was flat 30%).
