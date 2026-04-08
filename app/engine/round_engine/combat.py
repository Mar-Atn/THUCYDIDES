# DEPRECATED (2026-04-06) — being replaced by engines/military.py (unit-level v2) + engines/round_tick.py
# See 3 DETAILED DESIGN/REUNIFICATION_AUDIT_2026-04-06.md. Do not add new logic here.
"""Combat resolution — RISK-style ground + air strikes + missiles + naval.

All dice rolls use ``random.randint(1, 6)`` and are returned in the result
for audit. No DB side effects: callers persist results.

Rules sourced from CON_C2_ACTION_SYSTEM_v2.frozen.md.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Result models
# ---------------------------------------------------------------------------


@dataclass
class CombatResult:
    """Outcome of a single combat engagement."""

    combat_type: str
    attacker_rolls: list[int] = field(default_factory=list)
    defender_rolls: list[int] = field(default_factory=list)
    attacker_losses: list[str] = field(default_factory=list)  # destroyed unit_codes
    defender_losses: list[str] = field(default_factory=list)
    modifiers_applied: dict = field(default_factory=dict)
    narrative: str = ""
    success: bool = True


@dataclass
class StrikeResult:
    """Outcome of a ranged strike (air, missile)."""

    combat_type: str
    success: bool
    probability: float
    roll: float
    absorbed_by_ad: Optional[str] = None  # unit_code of AD that absorbed
    attacker_losses: list[str] = field(default_factory=list)
    defender_losses: list[str] = field(default_factory=list)
    narrative: str = ""


# ---------------------------------------------------------------------------
# Dice helpers
# ---------------------------------------------------------------------------


def _roll(n: int) -> list[int]:
    """Roll ``n`` six-sided dice, return sorted descending."""
    rolls = [random.randint(1, 6) for _ in range(n)]
    rolls.sort(reverse=True)
    return rolls


# ---------------------------------------------------------------------------
# Ground combat (RISK-style)
# ---------------------------------------------------------------------------


def resolve_ground_combat(
    attacker_units: list[dict],
    defender_units: list[dict],
    hex_context: Optional[dict] = None,
) -> CombatResult:
    """Resolve a ground engagement — iterative RISK-style (CARD_ACTIONS 1.3).

    Rules (Marat 2026-04-07, aligned with SEED ACTION REVIEW 2026-03-30):
      * Attacker rolls min(3, attackers_alive) dice each exchange.
      * Defender rolls min(2, defenders_alive) dice each exchange.
      * Compare highest-vs-highest, second-vs-second. Ties go to defender.
      * Each losing pair removes one unit from that side.
      * Loop until either side has 0 units.

    ``hex_context`` modifiers (applied to highest die per side per exchange):
      * die_hard: defender +1 (hex has die_hard flag)
      * air_support: defender +1 (defender has tactical_air on hex)
      * die_hard + air_support STACK (max positional +2)
      * amphibious: attacker -1 (attack crosses sea→land)
      * ai_l4_attacker: attacker +1 (AI L4 with 50% flag)
      * ai_l4_defender: defender +1 (AI L4 with 50% flag)
      * low_morale_attacker: attacker -1 (stability ≤ 3)
      * low_morale_defender: defender -1 (stability ≤ 3)
    """
    hex_context = hex_context or {}

    # Defender modifiers (die hard + air support STACK per CARD_ACTIONS)
    defender_bonus = 0
    if hex_context.get("die_hard"):
        defender_bonus += 1
    if hex_context.get("air_support"):
        defender_bonus += 1
    if hex_context.get("ai_l4_defender"):
        defender_bonus += 1
    if hex_context.get("low_morale_defender"):
        defender_bonus -= 1

    # Attacker modifiers
    attacker_bonus = 0
    if hex_context.get("amphibious"):
        attacker_bonus -= 1
    if hex_context.get("ai_l4_attacker"):
        attacker_bonus += 1
    if hex_context.get("low_morale_attacker"):
        attacker_bonus -= 1

    if not attacker_units or not defender_units:
        return CombatResult(
            combat_type="ground",
            narrative="No combat: one side has zero units.",
            success=False,
        )

    # Work on copies so caller state isn't mutated until we return.
    attackers = list(attacker_units)
    defenders = list(defender_units)
    attacker_losses: list[str] = []
    defender_losses: list[str] = []
    all_a_rolls: list[int] = []
    all_d_rolls: list[int] = []
    exchanges = 0

    while attackers and defenders:
        exchanges += 1
        a_n = min(len(attackers), 3)
        d_n = min(len(defenders), 2)
        a_rolls = _roll(a_n)
        d_rolls = _roll(d_n)
        a_mod = a_rolls.copy()
        d_mod = d_rolls.copy()
        if a_mod and attacker_bonus:
            a_mod[0] = min(6, a_mod[0] + attacker_bonus); a_mod.sort(reverse=True)
        if d_mod and defender_bonus:
            d_mod[0] = min(6, d_mod[0] + defender_bonus); d_mod.sort(reverse=True)
        pairs = min(len(a_mod), len(d_mod))
        for i in range(pairs):
            if a_mod[i] > d_mod[i]:
                # defender loses one unit (remove the last defender)
                lost = defenders.pop()
                defender_losses.append(lost["unit_code"])
            else:
                # attacker loses (defender wins ties)
                lost = attackers.pop()
                attacker_losses.append(lost["unit_code"])
        all_a_rolls.append(a_rolls)
        all_d_rolls.append(d_rolls)
        # safety bound
        if exchanges >= 50:
            break

    narrative = (
        f"Ground combat ({exchanges} exchanges): "
        f"attackers -{len(attacker_losses)}, defenders -{len(defender_losses)}. "
        f"{'Attacker wins.' if defenders == [] else 'Defender holds.'}"
    )
    return CombatResult(
        combat_type="ground",
        attacker_rolls=[d for exch in all_a_rolls for d in exch],
        defender_rolls=[d for exch in all_d_rolls for d in exch],
        attacker_losses=attacker_losses,
        defender_losses=defender_losses,
        modifiers_applied={
            "defender_bonus": defender_bonus,
            "attacker_bonus": attacker_bonus,
            "exchanges": exchanges,
        },
        narrative=narrative,
        success=(defenders == []),
    )


# ---------------------------------------------------------------------------
# Air strike
# ---------------------------------------------------------------------------


def resolve_air_strike(
    attacker_unit: dict,
    defender_units: list[dict],
    active_ad_units: Optional[list[dict]] = None,
    air_superiority_count: int = 0,
) -> StrikeResult:
    """Resolve a tactical_air strike vs a target hex.

    Canonical rule (CON_C2_v2): "Air defense in target zone absorbs up to
    3 (configurable) incoming strikes per air defense unit before
    remaining strikes resolve."

    Model:
      1. Each AD unit can absorb up to ``AD_ABSORB_CAPACITY`` strikes
         (tracked on the unit via ``ad_strikes_absorbed``).
      2. While any AD in the zone has capacity, the incoming strike is
         ABSORBED — no damage to defender, no roll.
      3. After all AD capacity is exhausted, the strike rolls against
         base hit probability.

    Probability model (Marat 2026-04-05 final calibration):
      * **12% base** if no AD covers the target zone
      * **6%** if AD covers (halved) — AD "protects" but doesn't absorb 1:1
      * +2% per air-superiority unit (cap +4%) — modest bonus
      * clamped to [3%, 20%]

    The simpler halving rule replaces the earlier 3-strike absorption
    model. AD no longer accumulates "strikes absorbed" — it's just a
    coverage flag.

    On success: one defender unit is destroyed (prefer non-AD target).

    Attacker downed (Marat 2026-04-09 — CARD prevails):
      If AD covers the target zone, 15% chance the attacking air unit is
      DOWNED (destroyed). This is rolled independently of the strike
      success/failure — the attacker can hit AND be downed.
    """
    active_ad_units = active_ad_units or []
    ad_present = any(ad.get("status") != "destroyed" for ad in active_ad_units)

    base = 0.12
    air_sup_bonus = min(0.04, 0.02 * air_superiority_count)
    p = base + air_sup_bonus
    if ad_present:
        p = p * 0.5
    p = max(0.03, min(0.20, p))

    roll = random.random()
    success = roll < p

    defender_losses: list[str] = []
    if success and defender_units:
        target = next(
            (u for u in defender_units if u.get("unit_type") != "air_defense"),
            defender_units[0],
        )
        defender_losses.append(target["unit_code"])

    # DISC-2: 15% chance attacker is downed by AD (CARD_FORMULAS D.2)
    attacker_losses: list[str] = []
    attacker_downed = False
    if ad_present and random.random() < 0.15:
        attacker_downed = True
        attacker_losses.append(attacker_unit["unit_code"])

    narrative = (
        f"Air strike by {attacker_unit['unit_code']}: "
        f"AD={'yes' if ad_present else 'no'}, p={p:.2f}, roll={roll:.2f} -> "
        f"{'HIT' if success else 'MISS'}"
        f"{' | ATTACKER DOWNED by AD' if attacker_downed else ''}"
    )

    return StrikeResult(
        combat_type="air_strike",
        success=success,
        probability=p,
        roll=roll,
        absorbed_by_ad=None,
        attacker_losses=attacker_losses,
        defender_losses=defender_losses,
        narrative=narrative,
    )


# ---------------------------------------------------------------------------
# Missile strike
# ---------------------------------------------------------------------------


def resolve_missile_strike(
    missile_unit: dict,
    target: dict,
    active_ad_units: Optional[list[dict]] = None,
) -> StrikeResult:
    """Resolve a strategic_missile strike (conventional warhead).

    Probability model (Marat 2026-04-09 — CARD prevails):
      * **70% base** if no AD covers the target zone (ballistic missiles
        are very accurate, few defenses stop them outright)
      * AD intercepts via per-unit 50% roll: ``intercept_prob = 1 - (0.5 ^ num_ad_units)``
        1 AD = 50%, 2 AD = 75%, 3 AD = 87.5%
      * If intercepted, strike fails.
      * Ballistic missiles are CONSUMED on firing (disposable). The
        caller is responsible for marking the missile unit destroyed.
    """
    active_ad_units = active_ad_units or []
    live_ad = [ad for ad in active_ad_units if ad.get("status") != "destroyed"]
    num_ad = len(live_ad)

    # Per-unit 50% interception (CARD_FORMULAS D.5)
    intercepted = False
    intercepting_ad: Optional[str] = None
    if num_ad > 0:
        for ad in live_ad:
            if random.random() < 0.50:
                intercepted = True
                intercepting_ad = ad.get("unit_code")
                break

    if intercepted:
        return StrikeResult(
            combat_type="missile_strike",
            success=False,
            probability=0.70,
            roll=0.0,
            absorbed_by_ad=intercepting_ad,
            defender_losses=[],
            narrative=(
                f"Missile strike by {missile_unit['unit_code']} -> {target['unit_code']}: "
                f"INTERCEPTED by AD {intercepting_ad} ({num_ad} AD units, "
                f"intercept_prob={1 - 0.5 ** num_ad:.2f})"
            ),
        )

    p = 0.70

    roll = random.random()
    success = roll < p
    defender_losses: list[str] = []
    if success:
        defender_losses.append(target["unit_code"])

    narrative = (
        f"Missile strike by {missile_unit['unit_code']} -> {target['unit_code']}: "
        f"AD={num_ad} units, p={p:.2f}, roll={roll:.2f} -> "
        f"{'HIT' if success else 'MISS'}"
    )

    return StrikeResult(
        combat_type="missile_strike",
        success=success,
        probability=p,
        roll=roll,
        absorbed_by_ad=None,
        defender_losses=defender_losses,
        narrative=narrative,
    )


# ---------------------------------------------------------------------------
# Naval engagement
# ---------------------------------------------------------------------------


def resolve_naval(
    attacker_fleet: list[dict],
    defender_fleet: list[dict],
) -> CombatResult:
    """Resolve ship-vs-ship naval combat — pure 1v1 dice (CARD prevails 2026-04-09).

    Rules (CARD_ACTIONS 1.5 + CARD_FORMULAS D.3):
      * One ship vs one ship. Each rolls 1d6.
      * Higher roll wins. Ties go to defender.
      * No fleet size modifier — pure 1v1.
      * If multiple ships on each side, pair them off sequentially.
        Unpaired ships survive unscathed.
    """
    if not attacker_fleet or not defender_fleet:
        return CombatResult(
            combat_type="naval",
            narrative="No naval combat: one side has zero ships.",
            success=False,
        )

    pairs = min(len(attacker_fleet), len(defender_fleet))
    attacker_losses: list[str] = []
    defender_losses: list[str] = []
    a_rolls: list[int] = []
    d_rolls: list[int] = []

    for i in range(pairs):
        a_roll = random.randint(1, 6)
        d_roll = random.randint(1, 6)
        a_rolls.append(a_roll)
        d_rolls.append(d_roll)
        if a_roll > d_roll:
            defender_losses.append(defender_fleet[i]["unit_code"])
        else:
            # Ties go to defender — attacker loses
            attacker_losses.append(attacker_fleet[i]["unit_code"])

    narrative = (
        f"Naval combat ({pairs} duels): attacker {a_rolls}, defender {d_rolls}. "
        f"Attacker loses {len(attacker_losses)}, defender loses {len(defender_losses)}."
    )

    return CombatResult(
        combat_type="naval",
        attacker_rolls=a_rolls,
        defender_rolls=d_rolls,
        attacker_losses=attacker_losses,
        defender_losses=defender_losses,
        modifiers_applied={},
        narrative=narrative,
    )
