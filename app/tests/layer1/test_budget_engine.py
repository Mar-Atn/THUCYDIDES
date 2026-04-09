"""Layer 1 tests — budget execution engine per CONTRACT_BUDGET v1.1.

Verifies that the economic engine consumes the new budget schema correctly:

    budget = {
        "social_pct":  float 0.5-1.5,
        "production":  {ground, naval, tactical_air, strategic_missile, air_defense},
        "research":    {nuclear_coins, ai_coins},
    }

Reference: PHASES/UNMANNED_SPACECRAFT/CONTRACT_BUDGET.md §§2, 6, 8.

Run:
    cd app && PYTHONPATH=. python3 -m pytest tests/layer1/test_budget_engine.py -v
"""

from __future__ import annotations

import pytest

from engine.engines.economic import (
    BRANCH_UNIT_COST,
    BUDGET_PRODUCTION_BRANCHES,
    PRODUCTION_COST_MULT,
    PRODUCTION_OUTPUT_MULT,
    RD_MULTIPLIER,
    SOCIAL_STABILITY_MULT,
    SOCIAL_SUPPORT_MULT,
    _compute_production_from_levels,
    calc_budget_execution,
    calc_military_production,
    calc_tech_advancement,
)


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------


def _country(
    *,
    gdp: float = 280.0,
    treasury: float = 200.0,
    social_baseline: float = 0.25,
    production_capacity: dict | None = None,
    units: dict | None = None,
) -> dict:
    """Minimal country dict covering everything calc_budget_execution touches."""
    cap = {
        "ground": 4,
        "naval": 2,
        "tactical_air": 3,
        "strategic_missile": 0,
        "air_defense": 0,
    }
    if production_capacity is not None:
        cap.update(production_capacity)

    mil = {
        "ground": 0,
        "naval": 0,
        "tactical_air": 0,
        "strategic_missile": 0,
        "air_defense": 0,
        "maintenance_cost_per_unit": 0.0,   # silence maintenance so we can check coin flows
        "production_capacity": cap,
        "production_costs": {
            "ground": 3,
            "naval": 6,
            "tactical_air": 5,
            "strategic_missile": 8,
            "air_defense": 4,
        },
    }
    if units:
        mil.update(units)

    eco = {
        "gdp": gdp,
        "treasury": treasury,
        "inflation": 3.0,
        "starting_inflation": 3.0,
        "debt_burden": 0.0,
        "social_spending_baseline": social_baseline,
    }
    tech = {
        "nuclear_level": 0,
        "nuclear_rd_progress": 0.0,
        "ai_level": 0,
        "ai_rd_progress": 0.0,
    }
    return {"economic": eco, "military": mil, "technology": tech}


def _budget(
    social_pct: float = 1.0,
    production: dict | None = None,
    nuclear_coins: int = 0,
    ai_coins: int = 0,
) -> dict:
    prod = {
        "ground": 0,
        "naval": 0,
        "tactical_air": 0,
        "strategic_missile": 0,
        "air_defense": 0,
    }
    if production:
        prod.update(production)
    return {
        "social_pct": social_pct,
        "production": prod,
        "research": {"nuclear_coins": nuclear_coins, "ai_coins": ai_coins},
    }


# ===========================================================================
# 1. PRODUCTION LEVEL EXPANSION (via _compute_production_from_levels)
# ===========================================================================


class TestProductionLevels:
    def test_level_0_produces_nothing(self):
        c = _country()
        result = _compute_production_from_levels(c, {"ground": 0})
        print(f"Level 0 ground: {result['ground']}")
        assert result["ground"]["coins"] == 0
        assert result["ground"]["units"] == 0

    def test_level_1_normal_production(self):
        """ground level 1, cap 4 → 12 coins (3 × 4 × 1), 4 units (4 × 1)."""
        c = _country(production_capacity={"ground": 4})
        result = _compute_production_from_levels(c, {"ground": 1})
        print(f"Level 1 ground cap=4: {result['ground']}")
        assert result["ground"]["coins"] == 12
        assert result["ground"]["units"] == 4

    def test_level_2_accelerated(self):
        """naval level 2, cap 2 → 24 coins (6 × 2 × 2), 4 units (2 × 2)."""
        c = _country(production_capacity={"naval": 2})
        result = _compute_production_from_levels(c, {"naval": 2})
        print(f"Level 2 naval cap=2: {result['naval']}")
        assert result["naval"]["coins"] == 24
        assert result["naval"]["units"] == 4

    def test_level_3_maximum_inefficient(self):
        """tactical_air level 3, cap 3 → 60 coins (5 × 3 × 4), 9 units (3 × 3)."""
        c = _country(production_capacity={"tactical_air": 3})
        result = _compute_production_from_levels(c, {"tactical_air": 3})
        print(f"Level 3 tac_air cap=3: {result['tactical_air']}")
        assert result["tactical_air"]["coins"] == 60
        assert result["tactical_air"]["units"] == 9

    def test_strategic_missile_zero_capacity(self):
        c = _country(production_capacity={"strategic_missile": 0})
        result = _compute_production_from_levels(c, {"strategic_missile": 2})
        print(f"Strat missile cap=0 lvl=2: {result['strategic_missile']}")
        assert result["strategic_missile"]["coins"] == 0
        assert result["strategic_missile"]["units"] == 0

    def test_air_defense_zero_capacity(self):
        c = _country(production_capacity={"air_defense": 0})
        result = _compute_production_from_levels(c, {"air_defense": 3})
        print(f"Air defense cap=0 lvl=3: {result['air_defense']}")
        assert result["air_defense"]["coins"] == 0
        assert result["air_defense"]["units"] == 0

    def test_all_five_branches_iterated(self):
        """All 5 branches at level 1 → all 5 present in result."""
        c = _country(
            production_capacity={
                "ground": 4, "naval": 2, "tactical_air": 3,
                "strategic_missile": 1, "air_defense": 1,
            }
        )
        result = _compute_production_from_levels(
            c,
            {b: 1 for b in BUDGET_PRODUCTION_BRANCHES},
        )
        print(f"All branches level 1: {result}")
        for branch in BUDGET_PRODUCTION_BRANCHES:
            assert branch in result
            assert "coins" in result[branch]
            assert "units" in result[branch]
        assert result["ground"]["units"] == 4
        assert result["naval"]["units"] == 2
        assert result["tactical_air"]["units"] == 3
        assert result["strategic_missile"]["units"] == 1
        assert result["air_defense"]["units"] == 1


# ===========================================================================
# 2. SOCIAL PCT → STABILITY / SUPPORT DELTAS
# ===========================================================================


class TestSocialSideEffects:
    def test_social_pct_05_stability_minus_2(self):
        countries = {"alpha": _country(gdp=280, treasury=500)}
        budget = _budget(social_pct=0.5)
        result, _ = calc_budget_execution("alpha", countries, budget, revenue=100.0, log=[])
        print(f"social 0.5 → stab Δ={result.stability_delta}, supp Δ={result.political_support_delta}")
        assert result.stability_delta == pytest.approx(-2.0)
        assert result.political_support_delta == pytest.approx(-3.0)
        assert countries["alpha"]["economic"]["_social_pct"] == 0.5

    def test_social_pct_15_stability_plus_2(self):
        countries = {"alpha": _country(gdp=280, treasury=500)}
        budget = _budget(social_pct=1.5)
        result, _ = calc_budget_execution("alpha", countries, budget, revenue=100.0, log=[])
        print(f"social 1.5 → stab Δ={result.stability_delta}, supp Δ={result.political_support_delta}")
        assert result.stability_delta == pytest.approx(2.0)
        assert result.political_support_delta == pytest.approx(3.0)

    def test_social_pct_10_no_change(self):
        countries = {"alpha": _country(gdp=280, treasury=500)}
        budget = _budget(social_pct=1.0)
        result, _ = calc_budget_execution("alpha", countries, budget, revenue=100.0, log=[])
        print(f"social 1.0 → stab Δ={result.stability_delta}, supp Δ={result.political_support_delta}")
        assert result.stability_delta == pytest.approx(0.0)
        assert result.political_support_delta == pytest.approx(0.0)


# ===========================================================================
# 3. RESEARCH COINS → PROGRESS
# ===========================================================================


class TestResearchProgress:
    def test_research_coins_to_progress(self):
        """ai_coins=5, gdp=280 → progress = (5/280) × 0.8 ≈ 0.01429."""
        countries = {"alpha": _country(gdp=280, treasury=500)}
        budget = _budget(ai_coins=5)
        bud, _ = calc_budget_execution("alpha", countries, budget, revenue=100.0, log=[])
        print(f"research_spending={bud.research_spending}")
        assert bud.research_spending == pytest.approx(5.0)

        # Now run tech advancement using the rd dict the engine builds
        eco = countries["alpha"]["economic"]
        rd = {
            "nuclear": eco["_research_nuclear_coins"],
            "ai": eco["_research_ai_coins"],
        }
        calc_tech_advancement("alpha", countries, rd, {}, [])
        ai_progress = countries["alpha"]["technology"]["ai_rd_progress"]
        expected = (5 / 280) * RD_MULTIPLIER
        print(f"ai progress={ai_progress}, expected={expected}")
        assert ai_progress == pytest.approx(expected, rel=1e-4)


# ===========================================================================
# 4. CAP ENFORCEMENT
# ===========================================================================


class TestNoCaps:
    """No percentage caps per SEED_D8 and CONTRACT_BUDGET v1.1 (2026-04-10).

    Participants can allocate up to full discretionary budget. Over-spending
    triggers the deficit cascade (treasury → money printing → inflation).
    """

    def test_no_military_cap(self):
        """Full level-3 military allocation spent in full, no scaling."""
        # cap=20 for ground → level 3 = 3×20×4 = 240 coins requested.
        # Treasury high enough (500) to cover via deficit cascade.
        countries = {"alpha": _country(
            gdp=280, treasury=500, production_capacity={"ground": 20},
        )}
        budget = _budget(production={"ground": 3})
        result, prod = calc_budget_execution("alpha", countries, budget, revenue=100.0, log=[])
        print(f"military_spending={result.military_spending} (no cap, full spend)")
        # Full level 3: 20 cap × 3 cost × 4 mult = 240 coins, 60 units
        assert result.military_spending == pytest.approx(240.0, rel=1e-3)
        assert prod["ground"]["units"] == 60

    def test_no_research_cap(self):
        """Large R&D allocation spent in full, no scaling."""
        countries = {"alpha": _country(gdp=280, treasury=500)}
        budget = _budget(ai_coins=50)
        result, _ = calc_budget_execution("alpha", countries, budget, revenue=100.0, log=[])
        print(f"research_spending={result.research_spending} (no cap, full 50)")
        # Full 50 coins spent on AI research
        assert result.research_spending == pytest.approx(50.0, rel=1e-3)


# ===========================================================================
# 5. DEFICIT CASCADE
# ===========================================================================


class TestDeficitCascade:
    def test_deficit_cascade(self):
        """spending > revenue → treasury drawn → printed → inflation up."""
        # Maintenance + social forced high enough to overrun revenue.
        # Give country 100 units with maintenance 0.3 each × 3 multiplier = 90.
        # Revenue = 50, baseline 25% = 12.5 social. Total mandatory = 102.5.
        # Deficit = 52.5. Treasury = 20 → drawn 20 → printed 32.5.
        countries = {"alpha": _country(
            gdp=280, treasury=20.0,
            units={
                "ground": 100,
                "maintenance_cost_per_unit": 0.3,
            },
        )}
        budget = _budget(social_pct=1.0)
        start_inflation = countries["alpha"]["economic"]["inflation"]
        result, _ = calc_budget_execution("alpha", countries, budget, revenue=50.0, log=[])
        print(
            f"revenue=50 maint={result.maintenance} social={result.social_spending} "
            f"total={result.total_spending} deficit={result.deficit} "
            f"treasury_drawn={result.treasury_drawn} printed={result.money_printed}"
        )
        assert result.deficit > 0
        assert result.treasury_drawn == pytest.approx(20.0, rel=1e-3)
        assert result.money_printed > 0
        assert countries["alpha"]["economic"]["treasury"] == 0
        assert countries["alpha"]["economic"]["inflation"] > start_inflation


# ===========================================================================
# 6. END-TO-END: calc_military_production wires through to units
# ===========================================================================


class TestMilitaryProductionIntegration:
    def test_budget_execution_then_production_adds_units(self):
        countries = {"alpha": _country(
            gdp=280, treasury=500,
            production_capacity={"ground": 4, "naval": 2, "tactical_air": 3,
                                 "strategic_missile": 0, "air_defense": 0},
        )}
        budget = _budget(production={"ground": 1, "tactical_air": 2})
        bud, prod = calc_budget_execution("alpha", countries, budget, revenue=500.0, log=[])
        print(f"coins_by_branch={bud.coins_by_branch}")
        print(f"production_result={prod}")
        mp = calc_military_production("alpha", countries, prod, round_num=1, log=[])
        print(f"produced={mp.produced}")
        assert mp.produced["ground"] == 4
        assert mp.produced["tactical_air"] == 6  # cap 3 × level 2 output mult 2
        assert mp.produced["naval"] == 0
        assert mp.produced["strategic_missile"] == 0
        assert mp.produced["air_defense"] == 0
        # All 5 branches present
        for branch in BUDGET_PRODUCTION_BRANCHES:
            assert branch in mp.produced
        # Country military state updated
        assert countries["alpha"]["military"]["ground"] == 4
        assert countries["alpha"]["military"]["tactical_air"] == 6

    def test_coins_by_branch_matches_contract_example(self):
        """CONTRACT_BUDGET §8 example: ground=4 at lvl1 → 12 coins, tac_air=3 lvl2 → 30."""
        countries = {"alpha": _country(
            gdp=280, treasury=500,
            production_capacity={"ground": 4, "naval": 2, "tactical_air": 3,
                                 "strategic_missile": 0, "air_defense": 0},
        )}
        budget = _budget(production={"ground": 1, "tactical_air": 2})
        bud, _ = calc_budget_execution("alpha", countries, budget, revenue=500.0, log=[])
        print(f"coins_by_branch={bud.coins_by_branch}")
        assert bud.coins_by_branch["ground"] == 12
        assert bud.coins_by_branch["tactical_air"] == 30
        assert bud.coins_by_branch["naval"] == 0
        assert bud.coins_by_branch["strategic_missile"] == 0
        assert bud.coins_by_branch["air_defense"] == 0
