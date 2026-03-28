"""
TTT SEED -- World Model Engine v2
====================================
Between-round batch processing. THREE-PASS architecture with FEEDBACK LOOPS.

Pass 1: Deterministic formulas with CHAINED dependencies (each step feeds the next)
Pass 2: AI contextual adjustment (aggressive heuristics, AI-ready architecture)
Pass 3: Coherence check + narrative generation (auto-fixes implausible states)

v2 CHANGES from v1:
- Feedback loops: GDP -> Revenue -> Budget -> Debt/Inflation -> Stability -> Capital Flight -> GDP
- Crisis escalation ladder: NORMAL -> STRESSED -> CRISIS -> COLLAPSE
- Economic momentum: confidence variable that accelerates growth or decline
- Tipping points: oil > $150/$200, chip supply cut, sanctions fatigue
- Contagion: major economy crisis spreads to trade partners
- Asymmetry: breaking is fast, fixing is slow (3-4 round recovery)
- Soft oil cap (asymptotic above $200)
- Semiconductor disruption scales with duration
- Sanctions diminishing returns after 4 rounds

Processing sequence (CHAINED, not parallel):
1. Oil price (global)
2. GDP growth per country
3. Revenue per country (from GDP)
4. Budget execution (mandatory costs, deficit handling, money printing)
5. Military production and maintenance
6. Tech advancement
7. Inflation update
8. Debt service update
9. Update economic state (crisis ladder)
10. Update momentum (confidence)
11. Apply contagion
12. Stability update
13. Political support update
14. Narrative generation

Author: ATLAS (World Model Engineer)
Version: 2.0 (SEED) -- Feedback Loop Architecture
"""

import copy
import math
import random
from typing import Dict, List, Optional, Tuple, Any

from world_state import (
    WorldState, CHOKEPOINTS, UNIT_TYPES,
    AI_LEVEL_TECH_FACTOR, AI_LEVEL_COMBAT_BONUS,
    NUCLEAR_RD_THRESHOLDS, AI_RD_THRESHOLDS,
    OPEC_PRODUCTION_MULTIPLIER,
    PRODUCTION_TIER_COST, PRODUCTION_TIER_OUTPUT,
    STABILITY_THRESHOLDS, SCHEDULED_EVENTS,
    derive_trade_weights, clamp,
)


# ---------------------------------------------------------------------------
# CRISIS STATE CONSTANTS
# ---------------------------------------------------------------------------

CRISIS_STATES = ("normal", "stressed", "crisis", "collapse")

CRISIS_GDP_MULTIPLIER = {
    "normal": 1.0,
    "stressed": 0.85,
    "crisis": 0.5,
    "collapse": 0.2,
}

CRISIS_STABILITY_PENALTY = {
    "normal": 0.0,
    "stressed": -0.10,
    "crisis": -0.30,
    "collapse": -0.50,
}

# Major economies for contagion (GDP > 30 coins at game start)
MAJOR_ECONOMY_THRESHOLD = 30.0

# Oil importers: countries that are NOT oil producers
# Oil producers are flagged in country data

# R&D multiplier fix: 0.5 -> 0.8
RD_MULTIPLIER = 0.8


class WorldModelEngine:
    """Three-pass world model engine v2 with feedback loops and crisis states."""

    def __init__(self, world_state: WorldState):
        self.ws = world_state
        self.trade_weights = derive_trade_weights(self.ws.countries)
        self._log: List[str] = []
        self._previous_states: Dict[str, dict] = {}  # snapshot for detecting transitions

    def process_round(self, world_state: WorldState,
                      all_actions: dict, round_num: int) -> Tuple[dict, str, List[str]]:
        """Three-pass processing per round.

        Returns (results_dict, narrative_string, flags_list).
        """
        self.ws = world_state
        self.ws.round_num = round_num
        self.trade_weights = derive_trade_weights(self.ws.countries)
        self._log = []
        self._log.append(f"=== ROUND {round_num} WORLD MODEL ENGINE v2 ===")

        # Snapshot previous states for transition detection
        self._snapshot_previous_states()

        # PASS 1: Deterministic with feedback loops
        self._log.append("--- PASS 1: DETERMINISTIC (CHAINED) ---")
        det_results = self.deterministic_pass(all_actions, round_num)

        # PASS 2: AI Contextual Adjustment (aggressive heuristics)
        self._log.append("--- PASS 2: AI CONTEXTUAL ADJUSTMENT ---")
        adj_results = self.ai_adjustment_pass(det_results, all_actions, round_num)

        # PASS 3: Coherence Check + Narrative
        self._log.append("--- PASS 3: COHERENCE CHECK ---")
        flags, narrative = self.coherence_pass(round_num)

        self._log.append(f"=== ROUND {round_num} PROCESSING COMPLETE ===")

        final_results = {
            "round": round_num,
            "deterministic": det_results,
            "ai_adjustments": adj_results,
            "coherence_flags": flags,
            "narrative": narrative,
            "log": list(self._log),
        }

        return final_results, narrative, flags

    def _snapshot_previous_states(self):
        """Store previous round state for transition detection."""
        self._previous_states = {}
        for cid, c in self.ws.countries.items():
            self._previous_states[cid] = {
                "economic_state": c["economic"].get("economic_state", "normal"),
                "gdp": c["economic"]["gdp"],
                "stability": c["political"]["stability"],
                "at_war": self.ws.get_country_at_war(cid),
            }

    # ===================================================================
    # PASS 1: DETERMINISTIC (CHAINED FEEDBACK LOOPS)
    # ===================================================================

    def deterministic_pass(self, actions: dict, round_num: int) -> dict:
        """Chained formula calculations. Each step uses output of previous steps."""
        results: dict = {
            "oil_price": 0.0, "gdp": {}, "revenue": {}, "budget": {},
            "military_production": {}, "tech": {}, "inflation": {},
            "debt": {}, "economic_state": {}, "momentum": {},
            "contagion": {}, "stability": {}, "support": {},
            "sanctions": {}, "tariffs": {},
            "elections": {}, "combat_secondary": [],
            "financial_crisis": {},
        }

        # Step 0: Apply submitted actions
        self._apply_tariff_changes(actions.get("tariff_changes", {}))
        self._apply_sanction_changes(actions.get("sanction_changes", {}))
        self._apply_opec_changes(actions.get("opec_production", {}))
        self._apply_rare_earth_changes(actions.get("rare_earth_restrictions", {}))
        self._apply_blockade_changes(actions.get("blockade_changes", {}))

        # Update sanctions duration tracking
        self._update_sanctions_rounds()

        # Update Formosa disruption duration tracking
        self._update_formosa_disruption_rounds()

        # --- STEP 1: Oil price (global, everything depends on this) ---
        results["oil_price"] = self._calc_oil_price()
        self.ws.oil_price = results["oil_price"]
        self.ws.oil_price_index = results["oil_price"] / 80.0 * 100.0

        # Collate events for stability/support calculations
        events_by_country = self._collate_events(actions, results)

        # --- PER-COUNTRY CHAINED PROCESSING ---
        for cid in list(self.ws.countries.keys()):
            c = self.ws.countries[cid]

            # Pre-compute sanctions and tariff impacts
            sanc_damage, sanc_costs = self._calc_sanctions_impact(cid)
            results["sanctions"][cid] = {"damage": sanc_damage, "costs": sanc_costs}

            tariff_info = self._calc_tariff_impact(cid)
            results["tariffs"][cid] = tariff_info

            # --- STEP 2: GDP growth (with oil shock, semiconductor, sanctions,
            #              war, momentum, crisis state) ---
            gdp_result = self._calc_gdp_growth(cid, sanc_damage, tariff_info)
            results["gdp"][cid] = gdp_result
            c["economic"]["gdp"] = gdp_result["new_gdp"]
            c["economic"]["gdp_growth_rate"] = gdp_result["growth_pct"]

            # --- STEP 3: Revenue (from GDP, chained) ---
            rev = self._calc_revenue(cid)
            results["revenue"][cid] = rev

            # --- STEP 4: Budget execution (mandatory costs, deficit, money printing) ---
            budget = actions.get("budgets", {}).get(cid, {})
            bud_result = self._calc_budget_execution(cid, budget, rev)
            results["budget"][cid] = bud_result

            # --- STEP 5: Military production and maintenance ---
            mil_alloc = budget.get("military", {})
            prod_result = self._calc_military_production(cid, mil_alloc, round_num)
            results["military_production"][cid] = prod_result

            # Mobilization
            mob = actions.get("mobilizations", {}).get(cid, None)
            if mob:
                self._apply_mobilization(cid, mob)

            # --- STEP 6: Technology advancement ---
            rd = actions.get("tech_rd", {}).get(cid, {"nuclear": 0, "ai": 0})
            tech_result = self._calc_tech_advancement(cid, rd)
            results["tech"][cid] = tech_result

            # --- STEP 7: Inflation update (money printing from budget -> inflation) ---
            money_printed = bud_result.get("money_printed", 0)
            new_inflation = self._calc_inflation(cid, money_printed)
            results["inflation"][cid] = new_inflation
            c["economic"]["inflation"] = new_inflation

            # --- STEP 8: Debt service update ---
            deficit = bud_result.get("deficit", 0)
            new_debt = self._calc_debt_service(cid, max(deficit, 0))
            results["debt"][cid] = new_debt
            c["economic"]["debt_burden"] = new_debt

        # --- STEP 9: Update economic state (crisis ladder) ---
        for cid in self.ws.countries:
            state_result = self._update_economic_state(cid)
            results["economic_state"][cid] = state_result

        # --- STEP 10: Update momentum ---
        for cid in self.ws.countries:
            momentum_result = self._update_momentum(cid, round_num)
            results["momentum"][cid] = momentum_result

        # --- STEP 11: Apply contagion ---
        contagion_result = self._apply_contagion()
        results["contagion"] = contagion_result

        # --- STEP 12: Stability update (v4 formula + crisis state penalty) ---
        for cid in self.ws.countries:
            c = self.ws.countries[cid]
            ev = events_by_country.get(cid, {})
            new_stab = self._calc_stability(cid, ev)
            results["stability"][cid] = new_stab
            c["political"]["stability"] = new_stab

            # Update war tiredness
            self._update_war_tiredness(cid)

            # Update threshold flags
            self._update_threshold_flags(cid)

        # --- STEP 13: Political support update ---
        for cid in self.ws.countries:
            c = self.ws.countries[cid]
            ev = events_by_country.get(cid, {})
            new_sup = self._calc_political_support(cid, ev, round_num)
            results["support"][cid] = new_sup
            c["political"]["political_support"] = new_sup

        # --- Elections ---
        scheduled = SCHEDULED_EVENTS.get(round_num, [])
        for event in scheduled:
            if event["type"] == "election":
                election_result = self._process_election(
                    event["country"], event["subtype"],
                    actions.get("votes", {}).get(event["country"], {}),
                    round_num
                )
                results["elections"][event["country"]] = election_result

        return results

    # ===================================================================
    # STEP 1: OIL PRICE (global, computed first)
    # ===================================================================

    def _calc_oil_price(self) -> float:
        """Oil price with supply/demand/disruption/war factors.

        v2 changes:
        - Demand side linked to economic states (crisis = demand drops)
        - Soft cap above $200 (asymptotic, not hard clamp)
        - Reduced Gulf Gate from +80% to +50% (still massive)
        - Simplified war premium
        """
        base_price = 80.0

        # --- SUPPLY SIDE ---
        supply = 1.0

        # OPEC production decisions
        for member, decision in self.ws.opec_production.items():
            if decision == "low":
                supply -= 0.06
            elif decision == "high":
                supply += 0.06

        # Sanctions on oil producers reduce supply
        for producer in ("nordostan", "persia"):
            sanc_level = self._get_sanctions_on(producer)
            if sanc_level >= 2:
                supply -= 0.08

        supply = max(0.5, supply)

        # --- DISRUPTION (chokepoints) ---
        disruption = 1.0

        gulf_gate_blocked = self._is_gulf_gate_blocked()
        if gulf_gate_blocked:
            disruption += 0.50  # reduced from 0.80 -- still huge

        formosa_blocked = self._is_formosa_blocked()
        if formosa_blocked:
            disruption += 0.10

        # Other chokepoints
        for cp_name, status in self.ws.chokepoint_status.items():
            if status != "blocked":
                continue
            if cp_name in ("hormuz", "gulf_gate_ground", "taiwan_strait"):
                continue  # already handled
            if cp_name == "suez":
                disruption += 0.15
            elif cp_name == "malacca":
                disruption += 0.20
            else:
                disruption += 0.05

        # --- DEMAND SIDE (GDP-linked) ---
        demand = 1.0
        for cid, c in self.ws.countries.items():
            eco_state = c["economic"].get("economic_state", "normal")
            gdp = c["economic"]["gdp"]
            if gdp >= MAJOR_ECONOMY_THRESHOLD:
                if eco_state == "crisis":
                    demand -= 0.05
                elif eco_state == "collapse":
                    demand -= 0.10

        # Global GDP growth demand elasticity
        n_countries = len(self.ws.countries)
        if n_countries > 0:
            gdp_growth_avg = sum(
                c["economic"].get("gdp_growth_rate", 0)
                for c in self.ws.countries.values()
            ) / n_countries
            demand += (gdp_growth_avg - 2.0) * 0.03

        demand = max(0.6, demand)

        # --- WAR PREMIUM (simplified) ---
        war_premium = len(self.ws.wars) * 0.05
        war_premium = min(war_premium, 0.15)

        # --- COMPUTE PRICE ---
        raw_price = base_price * (demand / supply) * disruption * (1 + war_premium)

        # Soft cap: asymptotic above $200
        if raw_price <= 200:
            price = raw_price
        else:
            price = 200 + 50 * (1 - math.exp(-(raw_price - 200) / 100))

        # Floor at $30
        price = max(30.0, price)

        # --- OIL REVENUE TO PRODUCERS ---
        for cid, country in self.ws.countries.items():
            if country["economic"].get("oil_producer"):
                resource_pct = country["economic"]["sectors"].get("resources", 0) / 100.0
                oil_revenue = price * resource_pct * country["economic"]["gdp"] * 0.01
                country["economic"]["oil_revenue"] = round(max(oil_revenue, 0.0), 2)
            else:
                country["economic"]["oil_revenue"] = 0.0

        price = round(price, 1)
        self._log.append(
            f"  Oil: ${price:.1f} (supply={supply:.2f} demand={demand:.2f} "
            f"disruption={disruption:.2f} war={war_premium:.2f} "
            f"gulf_gate={'BLOCKED' if gulf_gate_blocked else 'open'} "
            f"formosa={'BLOCKED' if formosa_blocked else 'open'})"
        )
        return price

    # ===================================================================
    # STEP 2: GDP GROWTH (with feedback loops and crisis states)
    # ===================================================================

    def _calc_gdp_growth(self, country_id: str, sanctions_damage: float,
                         tariff_info: dict) -> dict:
        """Additive factor model with crisis multiplier."""
        c = self.ws.countries[country_id]
        eco = c["economic"]
        old_gdp = eco["gdp"]
        base_growth = eco["gdp_growth_rate"] / 100.0  # as decimal

        # --- TARIFF HIT (stronger: -1.5% GDP per tariff level) ---
        net_tariff_cost = tariff_info.get("net_gdp_cost", 0)
        tariff_hit = -(net_tariff_cost / max(old_gdp, 0.01)) * 1.5

        # --- SANCTIONS HIT (stronger: -2% GDP per sanctions level) ---
        sanctions_hit = -sanctions_damage * 2.0

        # Sanctions diminishing returns after 4 rounds
        sanc_rounds = eco.get("sanctions_rounds", 0)
        if sanc_rounds > 4:
            adaptation = 0.70  # 30% less effective
            sanctions_hit *= adaptation

        # --- OIL SHOCK (non-linear for importers) ---
        oil_price = self.ws.oil_price
        oil_shock = 0.0
        is_oil_importer = not eco.get("oil_producer", False)

        if is_oil_importer:
            if oil_price > 100:
                oil_shock = -0.02 * (oil_price - 100) / 50  # -2% per $50 above $100
        else:
            # Producers benefit, but less
            if oil_price > 80:
                oil_shock = 0.01 * (oil_price - 80) / 50

        # --- SEMICONDUCTOR DISRUPTION (duration-scaling) ---
        semi_hit = 0.0
        dep = eco.get("formosa_dependency", 0)
        formosa_disrupted = self._is_formosa_disrupted()

        if formosa_disrupted and dep > 0:
            rounds_disrupted = eco.get("formosa_disruption_rounds", 0)
            # Severity ramps: 0.3, 0.5, 0.7, 0.9, 1.0
            severity = min(1.0, 0.3 + 0.2 * rounds_disrupted)
            tech_sector_pct = eco["sectors"].get("technology", 0) / 100.0
            semi_hit = -dep * severity * tech_sector_pct

        # --- WAR DAMAGE ---
        war_zones = self._count_war_zones(country_id)
        infra_damage = self._get_infra_damage(country_id)
        war_hit = -(war_zones * 0.03 + infra_damage * 0.05)

        # --- TECH FACTOR ---
        ai_level = c["technology"]["ai_level"]
        tech_boost = AI_LEVEL_TECH_FACTOR.get(ai_level, 0)

        # --- MOMENTUM EFFECT (key non-linearity) ---
        momentum = eco.get("momentum", 0.0)
        momentum_effect = momentum * 0.01  # +/-5% max

        # --- CRISIS STATE MULTIPLIER (dramatic) ---
        eco_state = eco.get("economic_state", "normal")
        crisis_mult = CRISIS_GDP_MULTIPLIER.get(eco_state, 1.0)

        # --- BLOCKADE FACTOR ---
        blockade_frac = self._get_blockade_fraction(country_id)
        blockade_hit = -blockade_frac * 0.4

        # --- COMPUTE GROWTH ---
        raw_growth = (base_growth + tariff_hit + sanctions_hit + oil_shock
                      + semi_hit + war_hit + tech_boost + momentum_effect
                      + blockade_hit)
        effective_growth = raw_growth * crisis_mult

        new_gdp = old_gdp * (1.0 + effective_growth)
        new_gdp = max(0.5, new_gdp)  # floor at 0.5 coins

        growth_pct = effective_growth * 100.0

        self._log.append(
            f"  GDP {country_id}: {old_gdp:.2f}->{new_gdp:.2f} "
            f"(growth {growth_pct:+.2f}% | base={base_growth*100:.1f} "
            f"tariff={tariff_hit*100:+.1f} sanc={sanctions_hit*100:+.1f} "
            f"oil={oil_shock*100:+.1f} semi={semi_hit*100:+.1f} "
            f"war={war_hit*100:+.1f} tech={tech_boost*100:+.1f} "
            f"momentum={momentum_effect*100:+.1f} blockade={blockade_hit*100:+.1f} "
            f"crisis_mult={crisis_mult:.2f} state={eco_state})"
        )

        return {
            "old_gdp": old_gdp, "new_gdp": round(new_gdp, 2),
            "growth_pct": round(growth_pct, 2), "base_growth": round(base_growth * 100, 2),
            "tariff_hit": round(tariff_hit * 100, 2),
            "sanctions_hit": round(sanctions_hit * 100, 2),
            "oil_shock": round(oil_shock * 100, 2),
            "semi_hit": round(semi_hit * 100, 2),
            "war_hit": round(war_hit * 100, 2),
            "tech_boost": round(tech_boost * 100, 2),
            "momentum_effect": round(momentum_effect * 100, 2),
            "blockade_hit": round(blockade_hit * 100, 2),
            "crisis_multiplier": crisis_mult,
            "economic_state": eco_state,
        }

    # ===================================================================
    # STEP 3: REVENUE (chained from GDP)
    # ===================================================================

    def _calc_revenue(self, country_id: str) -> float:
        """Revenue = GDP * tax_rate + oil_revenue - debt_burden - inflation_erosion - war_damage."""
        c = self.ws.countries[country_id]
        eco = c["economic"]
        gdp = eco["gdp"]
        tax_rate = eco["tax_rate"]

        base_rev = gdp * tax_rate
        oil_rev = eco.get("oil_revenue", 0.0)

        # Debt service eats revenue
        debt = eco["debt_burden"]

        # Inflation erosion: based on DELTA from baseline (not absolute)
        starting_infl = eco.get("starting_inflation", 0)
        inflation_delta = max(0, eco["inflation"] - starting_infl)
        inflation_erosion = inflation_delta * 0.03 * gdp / 100.0
        eco["inflation_revenue_erosion"] = round(inflation_erosion, 2)

        # War damage cost
        war_damage = self._get_infra_damage(country_id) * 0.02 * gdp

        # Sanctions cost on revenue
        sanc_cost = 0.0
        sanctions = self.ws.bilateral.get("sanctions", {})
        for sanctioner, targets in sanctions.items():
            level = targets.get(country_id, 0)
            if level > 0:
                bw = self.trade_weights.get(sanctioner, {}).get(country_id, 0)
                sanc_cost += level * bw * 0.015 * gdp

        revenue = base_rev + oil_rev - debt - inflation_erosion - war_damage - sanc_cost
        revenue = max(revenue, 0.0)

        self._log.append(
            f"  Revenue {country_id}: {revenue:.2f} "
            f"(base={base_rev:.2f} oil={oil_rev:.2f} debt=-{debt:.2f} "
            f"infl_erosion=-{inflation_erosion:.2f} war=-{war_damage:.2f} "
            f"sanc=-{sanc_cost:.2f})")
        return round(revenue, 2)

    # ===================================================================
    # STEP 4: BUDGET EXECUTION (deficit handling, money printing)
    # ===================================================================

    def _calc_budget_execution(self, country_id: str, budget: dict,
                               revenue: float) -> dict:
        """Budget execution with deficit -> money printing -> inflation chain."""
        c = self.ws.countries[country_id]
        mil = c["military"]
        eco = c["economic"]

        # Mandatory costs
        maint_rate = mil.get("maintenance_cost_per_unit", 0.3)
        total_units = sum(mil.get(ut, 0) for ut in UNIT_TYPES)
        maintenance = total_units * maint_rate
        social_baseline_cost = eco.get("social_spending_baseline", 0.25) * eco["gdp"]
        mandatory = maintenance + social_baseline_cost

        discretionary = max(revenue - mandatory, 0.0)
        money_printed = 0.0
        deficit = 0.0

        # Allocate from budget (or defaults)
        social = min(budget.get("social_spending", discretionary * 0.3), revenue)
        mil_budget = min(budget.get("military_total", discretionary * 0.3),
                         max(revenue - social, 0))
        tech_budget = min(budget.get("tech_total", discretionary * 0.1),
                          max(revenue - social - mil_budget, 0))

        total_spending = social + mil_budget + tech_budget + maintenance

        if total_spending > revenue:
            deficit = total_spending - revenue

            # Try to draw from reserves
            if eco["treasury"] >= deficit:
                eco["treasury"] -= deficit
            else:
                # Print money for the gap
                money_printed = deficit - eco["treasury"]
                eco["treasury"] = 0

                # Money printing -> AGGRESSIVE inflation
                if eco["gdp"] > 0:
                    eco["inflation"] += money_printed / eco["gdp"] * 80.0

                # Deficit becomes permanent debt
                eco["debt_burden"] += deficit * 0.15

                self._log.append(
                    f"  DEFICIT CRISIS {country_id}: printed {money_printed:.2f} coins, "
                    f"inflation +{money_printed / max(eco['gdp'], 0.01) * 80:.1f}%")
        else:
            surplus = revenue - total_spending
            eco["treasury"] += surplus

        return {
            "revenue": revenue, "mandatory": round(mandatory, 2),
            "maintenance": round(maintenance, 2),
            "discretionary": round(discretionary, 2),
            "social_spending": round(social, 2),
            "military_budget": round(mil_budget, 2),
            "tech_budget": round(tech_budget, 2),
            "deficit": round(deficit, 2),
            "money_printed": round(money_printed, 2),
            "new_treasury": round(eco["treasury"], 2),
        }

    # ===================================================================
    # STEP 5: MILITARY PRODUCTION
    # ===================================================================

    def _calc_military_production(self, country_id: str,
                                   military_alloc: dict,
                                   round_num: int) -> dict:
        """Produce units. Includes Columbia naval auto-production fix."""
        c = self.ws.countries[country_id]
        mil = c["military"]
        cap = mil.get("production_capacity", {})
        costs = mil.get("production_costs", {})
        produced = {}

        for utype in ("ground", "naval", "tactical_air"):
            alloc = military_alloc.get(utype, {})
            coins = alloc.get("coins", 0)
            tier = alloc.get("tier", "normal")
            if coins <= 0:
                produced[utype] = 0
                continue

            unit_cost = costs.get(utype, 3) * PRODUCTION_TIER_COST.get(tier, 1.0)
            max_cap = cap.get(utype, 0) * PRODUCTION_TIER_OUTPUT.get(tier, 1.0)

            units = min(int(coins / unit_cost), int(max_cap)) if unit_cost > 0 else 0
            units = max(units, 0)
            mil[utype] = mil.get(utype, 0) + units
            produced[utype] = units

        # Columbia naval auto-production: 1 per 2 rounds for countries with naval >= 5
        # This prevents unrealistic naval decline
        if mil.get("naval", 0) >= 5 and round_num % 2 == 0:
            if produced.get("naval", 0) == 0:
                mil["naval"] = mil.get("naval", 0) + 1
                produced["naval"] = produced.get("naval", 0) + 1
                self._log.append(
                    f"  Naval auto-production {country_id}: +1 "
                    f"(maintenance replacement, total={mil['naval']})")

        # Cathay strategic missile growth
        if country_id == "cathay" and mil.get("strategic_missile_growth", 0) > 0:
            mil["strategic_missiles"] = mil.get("strategic_missiles", 0) + 1
            produced["strategic_missiles"] = 1
            self._log.append("  Cathay strategic missile: +1")

        if any(v > 0 for v in produced.values()):
            self._log.append(f"  Production {country_id}: {produced}")
        return produced

    # ===================================================================
    # STEP 6: TECHNOLOGY ADVANCEMENT
    # ===================================================================

    def _calc_tech_advancement(self, country_id: str, rd_investment: dict) -> dict:
        """R&D with fixed multiplier 0.8 (was 0.5) and rare earth impact."""
        c = self.ws.countries[country_id]
        tech = c["technology"]
        gdp = c["economic"]["gdp"]
        result = {"nuclear_levelup": False, "ai_levelup": False}

        # Rare earth impact on R&D
        rare_earth_factor = self._calc_rare_earth_impact(country_id)

        # Nuclear R&D
        nuc_invest = rd_investment.get("nuclear", 0)
        if nuc_invest > 0 and gdp > 0:
            nuc_progress = (nuc_invest / max(gdp, 0.01)) * RD_MULTIPLIER * rare_earth_factor
            tech["nuclear_rd_progress"] += nuc_progress
        nuc_threshold = NUCLEAR_RD_THRESHOLDS.get(tech["nuclear_level"], 999.0)
        if tech["nuclear_rd_progress"] >= nuc_threshold and tech["nuclear_level"] < 3:
            tech["nuclear_level"] += 1
            tech["nuclear_rd_progress"] = 0.0
            result["nuclear_levelup"] = True
            self._log.append(
                f"  TECH BREAKTHROUGH: {country_id} nuclear->L{tech['nuclear_level']}")

        # AI R&D
        ai_invest = rd_investment.get("ai", 0)
        if ai_invest > 0 and gdp > 0:
            ai_progress = (ai_invest / max(gdp, 0.01)) * RD_MULTIPLIER * rare_earth_factor
            tech["ai_rd_progress"] += ai_progress
        ai_threshold = AI_RD_THRESHOLDS.get(tech["ai_level"], 999.0)
        if tech["ai_rd_progress"] >= ai_threshold and tech["ai_level"] < 4:
            tech["ai_level"] += 1
            tech["ai_rd_progress"] = 0.0
            result["ai_levelup"] = True
            self._log.append(
                f"  TECH BREAKTHROUGH: {country_id} AI->L{tech['ai_level']}")

        if rare_earth_factor < 1.0:
            self._log.append(
                f"  Rare earth restriction on {country_id}: R&D factor={rare_earth_factor:.2f}")

        return result

    # ===================================================================
    # STEP 7: INFLATION
    # ===================================================================

    def _calc_inflation(self, country_id: str, money_printed: float) -> float:
        """Inflation with 15% natural decay, 80x money-printing multiplier."""
        c = self.ws.countries[country_id]
        prev = c["economic"]["inflation"]
        gdp = c["economic"]["gdp"]

        # Natural decay
        new_infl = prev * 0.85

        # Money printing spike (aggressive: 80x multiplier)
        if gdp > 0 and money_printed > 0:
            new_infl += (money_printed / gdp) * 80.0

        new_infl = clamp(new_infl, 0.0, 500.0)
        return round(new_infl, 2)

    # ===================================================================
    # STEP 8: DEBT SERVICE
    # ===================================================================

    def _calc_debt_service(self, country_id: str, deficit: float) -> float:
        """Deficits become 15% permanent debt burden."""
        c = self.ws.countries[country_id]
        old_debt = c["economic"]["debt_burden"]
        new_debt = old_debt
        if deficit > 0:
            new_debt = old_debt + deficit * 0.15
        return round(max(new_debt, 0.0), 2)

    # ===================================================================
    # STEP 9: ECONOMIC STATE (Crisis Ladder)
    # ===================================================================

    def _update_economic_state(self, country_id: str) -> dict:
        """Transition between NORMAL/STRESSED/CRISIS/COLLAPSE.

        Downward transitions are fast (immediate).
        Upward transitions are slow (2-3 rounds of positive indicators).
        """
        c = self.ws.countries[country_id]
        eco = c["economic"]
        state = eco.get("economic_state", "normal")
        old_state = state

        oil_price = self.ws.oil_price
        is_oil_importer = not eco.get("oil_producer", False)
        starting_infl = eco.get("starting_inflation", 0)
        gdp_growth = eco.get("gdp_growth_rate", 0)
        formosa_disrupted = self._is_formosa_disrupted()
        dep = eco.get("formosa_dependency", 0)
        disruption_rounds = eco.get("formosa_disruption_rounds", 0)

        # --- COUNT STRESS TRIGGERS ---
        stress_triggers = 0
        if oil_price > 150 and is_oil_importer:
            stress_triggers += 1
        if eco["inflation"] > starting_infl + 15:
            stress_triggers += 1
        if gdp_growth < -1:
            stress_triggers += 1
        if eco["treasury"] <= 0:
            stress_triggers += 1
        if c["political"]["stability"] < 4:
            stress_triggers += 1
        if formosa_disrupted and dep > 0.3:
            stress_triggers += 1

        # --- COUNT CRISIS TRIGGERS ---
        crisis_triggers = 0
        if oil_price > 200 and is_oil_importer:
            crisis_triggers += 1
        if eco["inflation"] > starting_infl + 30:
            crisis_triggers += 1
        if gdp_growth < -3:
            crisis_triggers += 1
        if eco["treasury"] <= 0 and eco["debt_burden"] > eco["gdp"] * 0.1:
            crisis_triggers += 1
        if disruption_rounds >= 3 and dep > 0.5:
            crisis_triggers += 1

        # --- DOWNWARD TRANSITIONS (fast) ---
        if state == "normal" and stress_triggers >= 2:
            state = "stressed"
        if state == "stressed" and crisis_triggers >= 2:
            state = "crisis"
            eco["crisis_rounds"] = 0
        if state in ("crisis", "collapse"):
            eco["crisis_rounds"] = eco.get("crisis_rounds", 0) + 1
        if state == "crisis" and eco["crisis_rounds"] >= 3 and crisis_triggers >= 2:
            state = "collapse"

        # --- UPWARD TRANSITIONS (slow: 2-3 rounds of positive indicators) ---
        if state == "collapse" and crisis_triggers == 0:
            eco["recovery_rounds"] = eco.get("recovery_rounds", 0) + 1
            if eco["recovery_rounds"] >= 3:
                state = "crisis"
                eco["recovery_rounds"] = 0
        elif state == "crisis" and stress_triggers <= 1:
            eco["recovery_rounds"] = eco.get("recovery_rounds", 0) + 1
            if eco["recovery_rounds"] >= 2:
                state = "stressed"
                eco["recovery_rounds"] = 0
        elif state == "stressed" and stress_triggers == 0:
            eco["recovery_rounds"] = eco.get("recovery_rounds", 0) + 1
            if eco["recovery_rounds"] >= 2:
                state = "normal"
                eco["recovery_rounds"] = 0
        else:
            eco["recovery_rounds"] = 0  # reset if conditions worsen

        eco["economic_state"] = state

        if state != old_state:
            self._log.append(
                f"  ECONOMIC STATE {country_id}: {old_state} -> {state} "
                f"(stress={stress_triggers} crisis={crisis_triggers})")

        return {
            "old_state": old_state, "new_state": state,
            "stress_triggers": stress_triggers, "crisis_triggers": crisis_triggers,
            "crisis_rounds": eco.get("crisis_rounds", 0),
            "recovery_rounds": eco.get("recovery_rounds", 0),
        }

    # ===================================================================
    # STEP 10: MOMENTUM (Confidence Variable)
    # ===================================================================

    def _update_momentum(self, country_id: str, round_num: int) -> dict:
        """Economic confidence. Builds slowly (+0.3/round max), crashes fast (-2.0/round)."""
        c = self.ws.countries[country_id]
        eco = c["economic"]
        old_m = eco.get("momentum", 0.0)

        gdp_growth = eco.get("gdp_growth_rate", 0)
        eco_state = eco.get("economic_state", "normal")
        oil_price = self.ws.oil_price
        is_oil_importer = not eco.get("oil_producer", False)
        formosa_disrupted = self._is_formosa_disrupted()
        dep = eco.get("formosa_dependency", 0)

        # --- POSITIVE SIGNALS (each +0.15, capped at +0.3/round) ---
        boost = 0.0
        if gdp_growth > 2:
            boost += 0.15
        if eco_state == "normal":
            boost += 0.15
        if c["political"]["stability"] > 6:
            boost += 0.15
        boost = min(0.3, boost)

        # --- NEGATIVE SIGNALS (each -0.5 to -2.0, NO cap -- crashes FAST) ---
        crash = 0.0
        if eco_state == "crisis":
            crash -= 1.0
        if eco_state == "collapse":
            crash -= 2.0
        if gdp_growth < -2:
            crash -= 0.5
        if oil_price > 200 and is_oil_importer:
            crash -= 0.5
        if formosa_disrupted and dep > 0.3:
            crash -= 0.5

        # Just entered war this round
        prev = self._previous_states.get(country_id, {})
        at_war_now = self.ws.get_country_at_war(country_id)
        was_at_war = prev.get("at_war", False)
        if at_war_now and not was_at_war:
            crash -= 1.0

        new_m = clamp(old_m + boost + crash, -5.0, 5.0)
        eco["momentum"] = round(new_m, 2)

        if abs(new_m - old_m) > 0.05:
            self._log.append(
                f"  Momentum {country_id}: {old_m:+.2f} -> {new_m:+.2f} "
                f"(boost={boost:+.2f} crash={crash:+.2f})")

        return {
            "old_momentum": old_m, "new_momentum": round(new_m, 2),
            "boost": round(boost, 2), "crash": round(crash, 2),
        }

    # ===================================================================
    # STEP 11: CONTAGION
    # ===================================================================

    def _apply_contagion(self) -> dict:
        """When major economies enter crisis, trade partners feel it."""
        contagion_hits = {}

        for cid, c in self.ws.countries.items():
            eco_state = c["economic"].get("economic_state", "normal")
            gdp = c["economic"]["gdp"]

            if eco_state in ("crisis", "collapse") and gdp >= MAJOR_ECONOMY_THRESHOLD:
                severity = 1.0 if eco_state == "crisis" else 2.0

                tw = self.trade_weights.get(cid, {})
                for partner_id, trade_weight in tw.items():
                    if trade_weight > 0.10:
                        partner = self.ws.countries.get(partner_id)
                        if not partner:
                            continue
                        hit = severity * trade_weight * 0.02
                        partner["economic"]["gdp"] *= (1 - hit)
                        partner["economic"]["gdp"] = max(0.5, partner["economic"]["gdp"])
                        partner["economic"]["momentum"] = max(
                            -5.0,
                            partner["economic"].get("momentum", 0) - 0.3
                        )

                        if partner_id not in contagion_hits:
                            contagion_hits[partner_id] = []
                        contagion_hits[partner_id].append({
                            "source": cid,
                            "gdp_hit_pct": round(hit * 100, 2),
                            "momentum_hit": -0.3,
                        })
                        self._log.append(
                            f"  CONTAGION: {cid} crisis -> {partner_id} "
                            f"GDP -{hit*100:.1f}%, momentum -0.3")

        return contagion_hits

    # ===================================================================
    # STEP 12: STABILITY (v4 formula + crisis state integration)
    # ===================================================================

    def _calc_stability(self, country_id: str, events: dict) -> float:
        """V4 stability with crisis state penalty and inflation delta fix.

        Keeps: democratic resilience, siege resilience, society adaptation
        Adds: crisis state penalty, inflation delta (not absolute), GDP cap
        Fixes: Nordostan siege resilience for sanctioned autocracies
        """
        c = self.ws.countries[country_id]
        pol = c["political"]
        eco = c["economic"]
        old_stab = pol["stability"]
        delta = 0.0

        at_war = self.ws.get_country_at_war(country_id)
        sanctions_level = self._sanctions_level(country_id)
        under_heavy_sanctions = sanctions_level >= 2
        regime = pol.get("regime_type", c.get("regime_type", "democracy"))
        eco_state = eco.get("economic_state", "normal")

        # --- POSITIVE INERTIA (only at high stability) ---
        if 7 <= old_stab < 9:
            delta += 0.05

        # --- GDP GROWTH (capped contraction penalty at -0.30) ---
        gdp_growth = eco.get("gdp_growth_rate", 0)
        if gdp_growth > 2:
            delta += min((gdp_growth - 2) * 0.08, 0.15)
        elif gdp_growth < -2:
            # Cap GDP contraction stability penalty at -0.30/round
            delta += max(gdp_growth * 0.15, -0.30)

        # --- SOCIAL SPENDING ---
        social_ratio = events.get("social_spending_ratio", 0.20)
        baseline = eco.get("social_spending_baseline", 0.30)
        social_effectiveness = 1.5 if at_war else 1.0
        if social_ratio >= baseline:
            delta += 0.05 * social_effectiveness
        elif social_ratio >= baseline - 0.05:
            delta -= 0.05
        else:
            shortfall = baseline - social_ratio
            delta -= shortfall * 3

        # --- WAR FRICTION (v4: reduced, with democratic resilience) ---
        is_frontline = False
        is_primary = False
        if at_war:
            is_primary = any(
                w.get("attacker") == country_id or w.get("defender") == country_id
                for w in self.ws.wars
            )
            is_frontline = any(
                w.get("defender") == country_id for w in self.ws.wars
            )
            if is_frontline:
                delta -= 0.10
            elif is_primary:
                delta -= 0.08
            else:
                delta -= 0.05

            casualties = events.get("casualties", 0)
            delta -= casualties * 0.2
            territory_lost = events.get("territory_lost", 0)
            delta -= territory_lost * 0.4
            territory_gained = events.get("territory_gained", 0)
            delta += territory_gained * 0.15
            war_tiredness = pol.get("war_tiredness", 0)
            delta -= min(war_tiredness * 0.04, 0.4)

            # Wartime democratic resilience
            if is_frontline and regime in ("democracy", "hybrid"):
                delta += 0.15

        # --- SANCTIONS FRICTION ---
        if sanctions_level > 0:
            # Diminishing returns after 4 rounds
            sanc_rounds = eco.get("sanctions_rounds", 0)
            sanc_multiplier = 0.70 if sanc_rounds > 4 else 1.0
            delta -= 0.1 * sanctions_level * sanc_multiplier

        if under_heavy_sanctions:
            sanc_hit = events.get("sanctions_pain", 0)
            gdp = eco["gdp"]
            if gdp > 0:
                sanc_hit = sanc_hit / gdp
            delta -= abs(sanc_hit) * 0.8

        # --- INFLATION FRICTION (DELTA from baseline, not absolute) ---
        starting_infl = eco.get("starting_inflation", 0)
        inflation_delta = eco.get("inflation", 0) - starting_infl
        if inflation_delta > 3:
            delta -= (inflation_delta - 3) * 0.05
        if inflation_delta > 20:
            delta -= (inflation_delta - 20) * 0.03

        # --- CRISIS STATE PENALTY ---
        delta += CRISIS_STABILITY_PENALTY.get(eco_state, 0.0)

        # --- MOBILIZATION ---
        mob_level = events.get("mobilization_level", 0)
        if mob_level > 0:
            delta -= mob_level * 0.2

        # --- PROPAGANDA ---
        prop_boost = events.get("propaganda_boost", 0)
        delta += prop_boost

        # --- PEACEFUL NON-SANCTIONED DAMPENING ---
        if not at_war and not under_heavy_sanctions:
            if delta < 0:
                delta *= 0.5

        # --- AUTOCRACY RESILIENCE ---
        if regime == "autocracy":
            if delta < 0:
                delta *= 0.75

        # --- SIEGE RESILIENCE: sanctioned autocracies at war ---
        if regime == "autocracy" and at_war and under_heavy_sanctions:
            delta += 0.10  # institutional adaptation to siege conditions

        # HARD CAP at 9.0, FLOOR at 1.0
        new_stab = clamp(old_stab + delta, 1.0, 9.0)
        self._log.append(
            f"  Stability {country_id}: {old_stab:.2f}->{new_stab:.2f} "
            f"(d={delta:+.3f} state={eco_state})")
        return round(new_stab, 2)

    # ===================================================================
    # STEP 13: POLITICAL SUPPORT
    # ===================================================================

    def _calc_political_support(self, country_id: str, events: dict,
                                 round_num: int) -> float:
        """Support calculation with crisis modifiers and oil penalty."""
        c = self.ws.countries[country_id]
        pol = c["political"]
        eco = c["economic"]
        regime = pol.get("regime_type", c.get("regime_type", "democracy"))
        old_sup = pol["political_support"]
        delta = 0.0

        stability = pol["stability"]
        gdp_growth = eco["gdp_growth_rate"]
        casualties = events.get("casualties", 0)
        eco_state = eco.get("economic_state", "normal")

        if regime in ("democracy", "hybrid"):
            delta += (gdp_growth - 2.0) * 0.8
            delta -= casualties * 3.0
            delta += (stability - 6.0) * 0.5

            # Crisis penalty on incumbents
            if eco_state == "crisis":
                delta -= 5.0
            elif eco_state == "collapse":
                delta -= 10.0
            elif eco_state == "stressed":
                delta -= 2.0

            # Oil price shock penalty on incumbents
            oil_price = self.ws.oil_price
            if oil_price > 150 and not eco.get("oil_producer"):
                delta -= (oil_price - 150) * 0.05  # -2.5 at $200

            # Election proximity effect
            if country_id == "columbia":
                if round_num == 1:
                    delta -= 1.0
                elif round_num == 4:
                    delta -= 2.0
            elif country_id == "heartland":
                if round_num in (2, 3):
                    delta -= 1.5

            # War tiredness damages support
            war_tiredness = pol.get("war_tiredness", 0)
            if war_tiredness > 2:
                delta -= (war_tiredness - 2) * 1.0
        else:
            delta += (stability - 6.0) * 0.8
            weakness = events.get("perceived_weakness", 0)
            delta -= weakness * 5.0
            repression = events.get("repression_effect", 0)
            delta += repression
            nationalist = events.get("nationalist_rally", 0)
            delta += nationalist

        # Mean-reversion toward 50%
        delta -= (old_sup - 50.0) * 0.05

        new_sup = clamp(old_sup + delta, 5.0, 85.0)
        self._log.append(
            f"  Support {country_id}: {old_sup:.1f}->{new_sup:.1f} (d={delta:+.2f})")
        return round(new_sup, 2)

    # ===================================================================
    # ELECTIONS
    # ===================================================================

    def _process_election(self, country_id: str, election_type: str,
                          votes: dict, round_num: int) -> dict:
        """Elections with crisis modifiers, oil penalty, endorsement toxicity."""
        c = self.ws.countries[country_id]
        eco = c["economic"]
        pol = c["political"]

        gdp_growth = eco["gdp_growth_rate"]
        stability = pol["stability"]
        eco_state = eco.get("economic_state", "normal")
        oil_price = self.ws.oil_price

        # AI incumbent score (base)
        econ_perf = gdp_growth * 10.0
        stab_factor = (stability - 5) * 5.0

        # War penalty
        war_penalty = 0.0
        for war in self.ws.wars:
            if (war.get("attacker") == country_id or
                    war.get("defender") == country_id or
                    country_id in war.get("allies", {}).get("attacker", []) or
                    country_id in war.get("allies", {}).get("defender", [])):
                war_penalty -= 5.0

        # Crisis penalty (NEW)
        crisis_penalty = 0.0
        if eco_state == "stressed":
            crisis_penalty = -5.0
        elif eco_state == "crisis":
            crisis_penalty = -15.0
        elif eco_state == "collapse":
            crisis_penalty = -25.0

        # Oil penalty for importers (NEW)
        oil_penalty = 0.0
        if oil_price > 150 and not eco.get("oil_producer"):
            oil_penalty = -(oil_price - 150) * 0.1

        ai_score = clamp(
            50.0 + econ_perf + stab_factor + war_penalty + crisis_penalty + oil_penalty,
            0.0, 100.0)

        player_incumbent_pct = votes.get("incumbent_pct", 50.0)
        final_incumbent = 0.5 * ai_score + 0.5 * player_incumbent_pct
        incumbent_wins = final_incumbent >= 50.0

        result = {
            "election_type": election_type,
            "country": country_id,
            "ai_score": round(ai_score, 2),
            "player_score": player_incumbent_pct,
            "final_incumbent_pct": round(final_incumbent, 2),
            "incumbent_wins": incumbent_wins,
            "crisis_penalty": crisis_penalty,
            "oil_penalty": round(oil_penalty, 2),
        }

        # Columbia midterms
        if election_type == "columbia_midterms":
            if not incumbent_wins:
                result["parliament_change"] = "opposition_majority"
                result["note"] = ("Midterms: Opposition wins. Parliament now 3-2 "
                                  "opposition (Tribune + Challenger + NPC Seat 5).")
            else:
                result["parliament_change"] = "status_quo"
                result["note"] = "Midterms: President's camp retains majority."

        # Heartland wartime election
        elif election_type in ("heartland_wartime", "heartland_wartime_runoff"):
            war_tiredness = pol.get("war_tiredness", 0)
            territory_factor = 0
            for w in self.ws.wars:
                if w.get("defender") == "heartland":
                    territory_factor -= len(w.get("occupied_zones", [])) * 3
            ai_score_adjusted = clamp(
                ai_score + territory_factor - war_tiredness * 2, 0, 100)
            final_incumbent = 0.5 * ai_score_adjusted + 0.5 * player_incumbent_pct
            incumbent_wins = final_incumbent >= 50.0
            result["ai_score"] = round(ai_score_adjusted, 2)
            result["final_incumbent_pct"] = round(final_incumbent, 2)
            result["incumbent_wins"] = incumbent_wins
            if not incumbent_wins:
                result["note"] = "Heartland election: Beacon loses. Bulwark becomes president."
            else:
                result["note"] = "Heartland election: Beacon survives."

        # Columbia presidential
        elif election_type == "columbia_presidential":
            result["note"] = ("Presidential election. " +
                              ("Incumbent camp wins." if incumbent_wins
                               else "Opposition wins. New president."))

        self._log.append(
            f"  Election {country_id} ({election_type}): "
            f"AI={ai_score:.1f} (crisis={crisis_penalty:+.0f} oil={oil_penalty:+.1f}) "
            f"incumbent={final_incumbent:.1f}% -> "
            f"{'WINS' if incumbent_wins else 'LOSES'}")

        self.ws.log_event({
            "type": "election",
            "subtype": election_type,
            "country": country_id,
            "incumbent_wins": incumbent_wins,
            "result": result,
        })
        return result

    # ===================================================================
    # PASS 2: AI CONTEXTUAL ADJUSTMENT (aggressive heuristics)
    # ===================================================================

    def ai_adjustment_pass(self, det_results: dict,
                           actions: dict, round_num: int) -> dict:
        """Aggressive AI adjustments producing VISIBLE effects.

        Structured for Pass 2 upgrade to real LLM calls:
        each adjustment has type, variable, magnitude, and reasoning.
        """
        adjustments: dict = {}

        for cid, c in self.ws.countries.items():
            adj_list = []
            eco = c["economic"]
            pol = c["political"]
            gdp = eco["gdp"]
            eco_state = eco.get("economic_state", "normal")
            regime = pol.get("regime_type", c.get("regime_type", "democracy"))

            # --- PANIC: Country just entered CRISIS ---
            prev_state = self._previous_states.get(cid, {}).get("economic_state", "normal")
            if eco_state in ("crisis", "collapse") and prev_state not in ("crisis", "collapse"):
                hit = gdp * 0.05  # additional 5% GDP hit
                eco["gdp"] = max(eco["gdp"] - hit, 0.5)
                adj_list.append({
                    "type": "market_panic",
                    "variable": "gdp",
                    "adjustment": -hit,
                    "reason": f"Market panic as {c.get('sim_name', cid)} enters economic {eco_state}"
                })

            # --- CAPITAL FLIGHT: stability < 3 ---
            if pol["stability"] < 3 and eco_state != "collapse":
                flight_pct = 0.08 if regime == "democracy" else 0.03
                flight = gdp * flight_pct
                eco["gdp"] = max(eco["gdp"] - flight, 0.5)
                adj_list.append({
                    "type": "capital_flight",
                    "variable": "gdp",
                    "adjustment": -flight,
                    "reason": (f"Capital flight as {c.get('sim_name', cid)} stability "
                               f"drops to {pol['stability']:.1f}")
                })
            elif pol["stability"] < 4:
                # Milder flight
                flight_pct = 0.03 if regime != "autocracy" else 0.01
                flight = gdp * flight_pct
                eco["gdp"] = max(eco["gdp"] - flight, 0.5)
                adj_list.append({
                    "type": "capital_flight_mild",
                    "variable": "gdp",
                    "adjustment": -flight,
                    "reason": (f"Capital outflows as {c.get('sim_name', cid)} stability "
                               f"at {pol['stability']:.1f}")
                })

            # --- CEASEFIRE RALLY: peace dividend ---
            # Detect ceasefire by checking if country was at war last round but not now
            was_at_war = self._previous_states.get(cid, {}).get("at_war", False)
            at_war_now = self.ws.get_country_at_war(cid)
            if was_at_war and not at_war_now:
                eco["momentum"] = min(5.0, eco.get("momentum", 0) + 1.5)
                adj_list.append({
                    "type": "ceasefire_rally",
                    "variable": "momentum",
                    "adjustment": 1.5,
                    "reason": f"Peace dividend: markets rally on {c.get('sim_name', cid)} ceasefire"
                })

            # --- SANCTIONS ADAPTATION: After 4+ rounds ---
            sanc_rounds = eco.get("sanctions_rounds", 0)
            if sanc_rounds > 4:
                # Small GDP recovery (adaptation)
                adaptation_boost = gdp * 0.02
                eco["gdp"] += adaptation_boost
                adj_list.append({
                    "type": "sanctions_adaptation",
                    "variable": "gdp",
                    "adjustment": adaptation_boost,
                    "reason": (f"{c.get('sim_name', cid)} adapts to sanctions "
                               f"after {sanc_rounds} rounds")
                })

            # --- BRAIN DRAIN: democracies in crisis lose tech ---
            if eco_state in ("crisis", "collapse") and regime == "democracy":
                tech = c["technology"]
                tech["ai_rd_progress"] = max(0, tech["ai_rd_progress"] - 0.02)
                adj_list.append({
                    "type": "brain_drain",
                    "variable": "ai_rd_progress",
                    "adjustment": -0.02,
                    "reason": (f"Brain drain from {c.get('sim_name', cid)} "
                               f"as skilled workers emigrate")
                })

            # --- WAR LOSS CONFIDENCE SHOCK ---
            for combat in det_results.get("combat_secondary", []):
                if (combat.get("defender") == cid and
                        combat.get("defender_remaining", 1) == 0):
                    pct = random.uniform(0.08, 0.15)
                    hit = min(gdp * pct, gdp * 0.30)
                    eco["gdp"] = max(eco["gdp"] - hit, 0.5)
                    adj_list.append({
                        "type": "war_loss_shock",
                        "variable": "gdp",
                        "adjustment": -hit,
                        "reason": (f"Confidence collapses after defeat "
                                   f"in {combat.get('zone', '?')}")
                    })

            # --- TECH BREAKTHROUGH OPTIMISM ---
            tech_res = det_results.get("tech", {}).get(cid, {})
            if tech_res.get("ai_levelup") or tech_res.get("nuclear_levelup"):
                boost = gdp * 0.05
                eco["gdp"] += boost
                eco["momentum"] = min(5.0, eco.get("momentum", 0) + 0.5)
                adj_list.append({
                    "type": "tech_breakthrough_optimism",
                    "variable": "gdp",
                    "adjustment": boost,
                    "reason": "Tech breakthrough sparks investor confidence."
                })

            # --- RALLY AROUND THE FLAG (diminishing) ---
            if at_war_now:
                war_duration = 0
                for w in self.ws.wars:
                    if w.get("attacker") == cid or w.get("defender") == cid:
                        start = w.get("start_round", 0)
                        war_duration = (round_num - start if start >= 0
                                        else round_num + abs(start))
                rally = max(10.0 - war_duration * 3.0, 0.0)
                if rally > 0:
                    bounded = min(rally, pol["political_support"] * 0.30)
                    pol["political_support"] = clamp(
                        pol["political_support"] + bounded, 0, 100)
                    adj_list.append({
                        "type": "rally_around_flag",
                        "variable": "political_support",
                        "adjustment": bounded,
                        "reason": f"Rally effect in year {war_duration}, diminishing."
                    })

            # Bound all GDP adjustments: total AI adjustment cannot exceed 30% of GDP
            total_gdp_adj = sum(
                a["adjustment"] for a in adj_list if a["variable"] == "gdp"
            )
            prev_gdp = self._previous_states.get(cid, {}).get("gdp", gdp)
            if prev_gdp > 0 and abs(total_gdp_adj) > prev_gdp * 0.30:
                # Scale back proportionally
                scale = (prev_gdp * 0.30) / abs(total_gdp_adj)
                for a in adj_list:
                    if a["variable"] == "gdp":
                        a["adjustment"] *= scale
                # Recompute GDP
                eco["gdp"] = max(0.5, prev_gdp + sum(
                    a["adjustment"] for a in adj_list if a["variable"] == "gdp"
                ))

            if adj_list:
                adjustments[cid] = adj_list

        return adjustments

    # ===================================================================
    # PASS 3: COHERENCE CHECK + NARRATIVE
    # ===================================================================

    def coherence_pass(self, round_num: int) -> Tuple[List[dict], str]:
        """Review world state for implausible combinations. Auto-fix HIGH severity."""
        flags: List[dict] = []

        for cid, c in self.ws.countries.items():
            eco = c["economic"]
            pol = c["political"]
            mil = c["military"]
            eco_state = eco.get("economic_state", "normal")
            gdp_growth = eco.get("gdp_growth_rate", 0)
            stab = pol["stability"]
            is_oil_importer = not eco.get("oil_producer", False)

            # Growing GDP during crisis = implausible
            if eco_state == "crisis" and gdp_growth > 0:
                flags.append({
                    "severity": "HIGH",
                    "country": cid,
                    "issue": (f"{c.get('sim_name', cid)} GDP growing "
                              f"({gdp_growth:+.1f}%) while in economic crisis"),
                    "fix": "Force GDP contraction of at least -1%",
                })
                # Auto-fix: force contraction
                eco["gdp"] *= 0.99
                eco["gdp_growth_rate"] = min(gdp_growth, -1.0)

            if eco_state == "collapse" and gdp_growth > -2:
                flags.append({
                    "severity": "HIGH",
                    "country": cid,
                    "issue": (f"{c.get('sim_name', cid)} in collapse but GDP "
                              f"growth at {gdp_growth:+.1f}%"),
                    "fix": "Force GDP contraction of at least -3%",
                })
                eco["gdp"] *= 0.97
                eco["gdp_growth_rate"] = min(gdp_growth, -3.0)

            # Collapse but high stability = contradictory
            if eco_state == "collapse" and stab > 5:
                flags.append({
                    "severity": "MEDIUM",
                    "country": cid,
                    "issue": (f"{c.get('sim_name', cid)} in economic collapse "
                              f"but stability at {stab:.1f}"),
                    "fix": "Reduce stability to max 4",
                })

            if eco_state == "crisis" and stab > 7:
                flags.append({
                    "severity": "MEDIUM",
                    "country": cid,
                    "issue": (f"{c.get('sim_name', cid)} in economic crisis "
                              f"but stability at {stab:.1f}"),
                    "fix": "Reduce stability to max 6",
                })

            # Oil at $200+ but importers growing normally
            if self.ws.oil_price > 200 and is_oil_importer and gdp_growth > 1.5:
                flags.append({
                    "severity": "HIGH",
                    "country": cid,
                    "issue": (f"{c.get('sim_name', cid)} growing {gdp_growth:+.1f}% "
                              f"with oil at ${self.ws.oil_price:.0f}"),
                    "fix": "Apply oil shock penalty",
                })
                shock = (self.ws.oil_price - 200) / 100 * 0.02
                eco["gdp"] *= (1 - shock)
                eco["gdp_growth_rate"] = min(gdp_growth, 0.5)

            # Negative GDP
            if eco["gdp"] < 0:
                flags.append({
                    "severity": "HIGH",
                    "country": cid,
                    "issue": f"{c.get('sim_name', cid)} GDP negative ({eco['gdp']:.2f})",
                    "fix": "Set GDP to floor 0.5",
                })
                eco["gdp"] = 0.5

            # Stability/support contradictions
            if stab <= 2 and pol["political_support"] > 70:
                flags.append({
                    "severity": "MEDIUM",
                    "country": cid,
                    "issue": (f"{c.get('sim_name', cid)} stability={stab:.1f} "
                              f"but support={pol['political_support']:.0f}"),
                    "fix": None,
                })

            # At war with 0 units
            at_war = self.ws.get_country_at_war(cid)
            total_mil = sum(mil.get(ut, 0) for ut in ("ground", "naval", "tactical_air"))
            if at_war and total_mil == 0:
                flags.append({
                    "severity": "HIGH",
                    "country": cid,
                    "issue": f"{c.get('sim_name', cid)} at war with 0 combat units",
                    "fix": None,
                })

        narrative = self._generate_narrative(round_num)

        # Return only string flags for backward compatibility, plus full dicts
        flag_strings = [f"{f['severity']}: {f['issue']}" for f in flags]
        return flag_strings, narrative

    def _generate_narrative(self, round_num: int) -> str:
        """Generate round briefing with crisis state reporting."""
        lines = [f"ROUND {round_num} WORLD BRIEFING", "=" * 40]

        total_gdp = sum(c["economic"]["gdp"] for c in self.ws.countries.values())
        lines.append(f"\nGlobal GDP: {total_gdp:.1f} coins. Oil: ${self.ws.oil_price:.0f}/bbl.")

        # Crisis states
        crisis_countries = [
            (cid, c) for cid, c in self.ws.countries.items()
            if c["economic"].get("economic_state", "normal") != "normal"
        ]
        if crisis_countries:
            lines.append("\nECONOMIC ALERTS:")
            for cid, c in crisis_countries:
                state = c["economic"]["economic_state"].upper()
                momentum = c["economic"].get("momentum", 0)
                lines.append(
                    f"  {c.get('sim_name', cid)}: {state} "
                    f"(momentum {momentum:+.1f})")

        if self.ws.wars:
            lines.append("\nACTIVE CONFLICTS:")
            for w in self.ws.wars:
                lines.append(
                    f"  {w['attacker']} vs {w['defender']} ({w.get('theater', '?')})")

        sorted_c = sorted(self.ws.countries.items(),
                          key=lambda x: x[1]["economic"]["gdp"], reverse=True)
        lines.append("\nTOP ECONOMIES:")
        for cid, c in sorted_c[:5]:
            eco_state = c["economic"].get("economic_state", "normal")
            state_tag = f" [{eco_state.upper()}]" if eco_state != "normal" else ""
            lines.append(
                f"  {c.get('sim_name', cid)}: GDP {c['economic']['gdp']:.1f}, "
                f"growth {c['economic']['gdp_growth_rate']:+.1f}%, "
                f"stab {c['political']['stability']:.1f}/10"
                f"{state_tag}")

        lines.append("\nKEY INDICATORS:")
        for cid, c in self.ws.countries.items():
            stab = c["political"]["stability"]
            if stab <= 4:
                lines.append(
                    f"  WARNING: {c.get('sim_name', cid)} stability {stab:.1f}/10")
            inflation_delta = (c["economic"]["inflation"]
                               - c["economic"].get("starting_inflation", 0))
            if inflation_delta > 15:
                lines.append(
                    f"  WARNING: {c.get('sim_name', cid)} inflation "
                    f"+{inflation_delta:.0f}% above baseline")

        blocked = [cp for cp, s in self.ws.chokepoint_status.items() if s == "blocked"]
        if blocked:
            lines.append(f"\nBLOCKED CHOKEPOINTS: {', '.join(blocked)}")

        if self.ws.ground_blockades:
            for name, bl in self.ws.ground_blockades.items():
                lines.append(
                    f"  GROUND BLOCKADE: {name} by {bl['controller']} "
                    f"({bl['ground_units']}G + {bl['naval_units']}N) -- AIR CANNOT BREAK")

        return "\n".join(lines)

    # ===================================================================
    # SANCTIONS & TARIFFS IMPACT
    # ===================================================================

    def _calc_sanctions_impact(self, target_id: str) -> Tuple[float, Dict[str, float]]:
        """Total sanctions damage to target + cost to each sanctioner."""
        sanctions = self.ws.bilateral.get("sanctions", {})
        tw = self.trade_weights

        raw_impacts: List[float] = []
        costs: Dict[str, float] = {}
        coalition_coverage = 0.0

        for sanctioner_id, targets in sanctions.items():
            if sanctioner_id.startswith("_"):
                continue
            level = targets.get(target_id, 0)
            if level <= 0:
                continue
            bw = tw.get(sanctioner_id, {}).get(target_id, 0.0)
            raw_impact = level * bw * 0.03
            raw_impacts.append(raw_impact)
            coalition_coverage += bw
            costs[sanctioner_id] = level * bw * 0.012

        effectiveness = 1.0 if coalition_coverage >= 0.6 else 0.3
        total_damage = sum(raw_impacts) * effectiveness
        total_damage = min(total_damage, 0.50)

        return total_damage, costs

    def _calc_tariff_impact(self, country_id: str) -> dict:
        """Net tariff impact on country_id."""
        tariffs = self.ws.bilateral.get("tariffs", {})
        tw = self.trade_weights
        c = self.ws.countries[country_id]
        gdp = c["economic"]["gdp"]

        cost_imposer = 0.0
        revenue_imposer = 0.0
        cost_target = 0.0

        my_tariffs = tariffs.get(country_id, {})
        for target, level in my_tariffs.items():
            if level <= 0:
                continue
            bw = tw.get(country_id, {}).get(target, 0.0)
            tariff_cost = level * bw * 0.04 * gdp
            revenue = tariff_cost * 0.70
            net_cost = tariff_cost * 0.30
            rerouting = level * 0.15
            net_cost *= max(0.0, 1.0 - rerouting)
            cost_imposer += net_cost
            revenue_imposer += revenue

        for imposer_id, targets in tariffs.items():
            if imposer_id == country_id:
                continue
            level = targets.get(country_id, 0)
            if level <= 0:
                continue
            bw = tw.get(imposer_id, {}).get(country_id, 0.0)
            imposer_gdp = self.ws.countries.get(imposer_id, {}).get(
                "economic", {}).get("gdp", 1)
            c2us = level * bw * 0.04 * imposer_gdp * 0.5
            rerouting = level * 0.15
            c2us *= max(0.0, 1.0 - rerouting)
            cost_target += c2us

        net_gdp_cost = max(cost_imposer + cost_target - revenue_imposer, 0.0)
        return {
            "cost_as_imposer": cost_imposer, "revenue_as_imposer": revenue_imposer,
            "cost_as_target": cost_target, "net_gdp_cost": net_gdp_cost,
        }

    # ===================================================================
    # INTERNAL HELPERS
    # ===================================================================

    def _is_gulf_gate_blocked(self) -> bool:
        """Check if Gulf Gate / Hormuz is blocked."""
        if self._is_chokepoint_blocked("gulf_gate"):
            return True
        for cp_name in ("hormuz", "gulf_gate_ground"):
            if self.ws.chokepoint_status.get(cp_name) == "blocked":
                return True
        return False

    def _is_formosa_blocked(self) -> bool:
        """Check if Formosa Strait is blocked."""
        if self._is_chokepoint_blocked("formosa_strait"):
            return True
        if self.ws.chokepoint_status.get("taiwan_strait") == "blocked":
            return True
        if getattr(self.ws, "formosa_blockade", False):
            return True
        return False

    def _is_formosa_disrupted(self) -> bool:
        """Check if Formosa semiconductor production is disrupted."""
        # War on Formosa
        for war in self.ws.wars:
            if "formosa" in (war.get("attacker"), war.get("defender")):
                return True
        # Blockade
        return self._is_formosa_blocked()

    def _is_chokepoint_blocked(self, chokepoint_key: str) -> bool:
        blockades = getattr(self.ws, "active_blockades", {})
        return chokepoint_key in blockades

    def _get_sanctions_on(self, target_country: str) -> int:
        sanctions = self.ws.bilateral.get("sanctions", {})
        max_level = 0
        for sanctioner, targets in sanctions.items():
            level = targets.get(target_country, 0)
            if level > max_level:
                max_level = level
        return max_level

    def _sanctions_level(self, country_id: str) -> int:
        return self._get_sanctions_on(country_id)

    def _count_war_zones(self, country_id: str) -> int:
        count = 0
        for w in self.ws.wars:
            if w.get("attacker") == country_id or w.get("defender") == country_id:
                count += len(w.get("occupied_zones", []))
        return count

    def _get_infra_damage(self, country_id: str) -> float:
        damage = 0.0
        for w in self.ws.wars:
            if w.get("defender") == country_id:
                damage += len(w.get("occupied_zones", [])) * 0.05
        return min(damage, 1.0)

    def _get_blockade_fraction(self, country_id: str) -> float:
        frac = 0.0
        c = self.ws.countries.get(country_id, {})
        eco = c.get("economic", {})
        for cp_name, status in self.ws.chokepoint_status.items():
            if status != "blocked":
                continue
            cp = CHOKEPOINTS.get(cp_name, {})
            impact = cp.get("trade_impact", cp.get("oil_impact", 0.1))
            if cp_name in ("hormuz", "gulf_gate_ground") and not eco.get("oil_producer"):
                frac += impact
            elif cp_name == "malacca" and country_id == "cathay":
                frac += impact * 2.0
            elif cp_name == "taiwan_strait":
                dep = eco.get("formosa_dependency", 0)
                frac += cp.get("tech_impact", 0.5) * dep
            else:
                frac += impact * 0.3
        return min(frac, 1.0)

    def _calc_rare_earth_impact(self, country_id: str) -> float:
        """Rare earth restrictions slow R&D. Each level = -15%, floor 40%."""
        restrictions = getattr(self.ws, "rare_earth_restrictions", {})
        if country_id in restrictions:
            restriction_level = restrictions[country_id]
            rd_penalty = 1.0 - (restriction_level * 0.15)
            return max(0.4, rd_penalty)
        return 1.0

    def _update_sanctions_rounds(self):
        """Track how many consecutive rounds each country is under L2+ sanctions."""
        for cid, c in self.ws.countries.items():
            level = self._sanctions_level(cid)
            if level >= 2:
                c["economic"]["sanctions_rounds"] = (
                    c["economic"].get("sanctions_rounds", 0) + 1)
            else:
                c["economic"]["sanctions_rounds"] = 0

    def _update_formosa_disruption_rounds(self):
        """Track consecutive rounds of Formosa semiconductor disruption."""
        formosa_disrupted = self._is_formosa_disrupted()
        for cid, c in self.ws.countries.items():
            dep = c["economic"].get("formosa_dependency", 0)
            if formosa_disrupted and dep > 0:
                c["economic"]["formosa_disruption_rounds"] = (
                    c["economic"].get("formosa_disruption_rounds", 0) + 1)
            else:
                c["economic"]["formosa_disruption_rounds"] = 0

    def _update_war_tiredness(self, country_id: str) -> None:
        """War tiredness: defenders +0.2/round, attackers +0.15/round.
        Society adaptation: after 3+ rounds at war, growth rate halves.
        """
        c = self.ws.countries[country_id]
        pol = c["political"]
        at_war = self.ws.get_country_at_war(country_id)
        current_wt = pol.get("war_tiredness", 0)
        if at_war:
            is_defender = any(
                w.get("defender") == country_id for w in self.ws.wars)
            is_attacker = any(
                w.get("attacker") == country_id for w in self.ws.wars)
            if is_defender:
                base_increase = 0.20
            elif is_attacker:
                base_increase = 0.15
            else:
                base_increase = 0.10

            # Society adaptation: after 3+ rounds at war, tiredness growth halves
            war_duration = 0
            for w in self.ws.wars:
                if w.get("attacker") == country_id or w.get("defender") == country_id:
                    start = w.get("start_round", 0)
                    dur = (self.ws.round_num - start if start >= 0
                           else self.ws.round_num + abs(start))
                    war_duration = max(war_duration, dur)
            if war_duration >= 3:
                base_increase *= 0.5

            pol["war_tiredness"] = min(current_wt + base_increase, 10.0)
        else:
            pol["war_tiredness"] = max(current_wt * 0.80, 0)

    def _update_threshold_flags(self, country_id: str) -> None:
        c = self.ws.countries[country_id]
        pol = c["political"]
        stab = pol["stability"]
        pol["protest_risk"] = stab < STABILITY_THRESHOLDS["protest_probable"]
        pol["coup_risk"] = stab < STABILITY_THRESHOLDS["unstable"]
        if stab < STABILITY_THRESHOLDS["protest_automatic"]:
            pol["regime_status"] = "crisis"
        elif stab < STABILITY_THRESHOLDS["unstable"]:
            pol["regime_status"] = "unstable"
        else:
            pol["regime_status"] = "stable"

    # ===================================================================
    # ACTION APPLICATION
    # ===================================================================

    def _apply_tariff_changes(self, changes: dict) -> None:
        tariffs = self.ws.bilateral.setdefault("tariffs", {})
        for imposer, targets in changes.items():
            if imposer not in tariffs:
                tariffs[imposer] = {}
            for target, level in targets.items():
                tariffs[imposer][target] = clamp(level, 0, 3)

    def _apply_sanction_changes(self, changes: dict) -> None:
        sanctions = self.ws.bilateral.setdefault("sanctions", {})
        for imposer, targets in changes.items():
            if imposer not in sanctions:
                sanctions[imposer] = {}
            for target, level in targets.items():
                sanctions[imposer][target] = clamp(level, -3, 3)

    def _apply_opec_changes(self, changes: dict) -> None:
        for member, level in changes.items():
            if level in ("low", "normal", "high"):
                self.ws.opec_production[member] = level

    def _apply_rare_earth_changes(self, changes: dict) -> None:
        """Apply rare earth restrictions. Cost to Cathay per level per target."""
        if not changes:
            return
        for target, level in changes.items():
            level = int(clamp(level, 0, 3))
            if level == 0:
                self.ws.rare_earth_restrictions.pop(target, None)
                self._log.append(f"  Rare earth: restrictions on {target} LIFTED")
            else:
                self.ws.rare_earth_restrictions[target] = level
                cathay = self.ws.countries.get("cathay")
                if cathay:
                    trade_loss = level * 0.3
                    cathay["economic"]["treasury"] = max(
                        cathay["economic"]["treasury"] - trade_loss, 0)
                self._log.append(
                    f"  Rare earth: Cathay restricts {target} at level {level} "
                    f"(trade cost: {level * 0.3:.1f} coins)")

    def _apply_blockade_changes(self, changes: dict) -> None:
        """Apply blockade declarations or removals."""
        if not changes:
            return
        for chokepoint, data in changes.items():
            if data is None:
                self.ws.active_blockades.pop(chokepoint, None)
                if chokepoint == "formosa_strait":
                    self.ws.formosa_blockade = False
                self._log.append(f"  Blockade: {chokepoint} LIFTED")
            else:
                self.ws.active_blockades[chokepoint] = data
                if chokepoint == "formosa_strait":
                    self.ws.formosa_blockade = True
                self._log.append(
                    f"  Blockade: {chokepoint} declared by {data.get('blocker', '?')}")

    def _apply_mobilization(self, country_id: str, level: str) -> None:
        c = self.ws.countries[country_id]
        mil = c["military"]
        cap = mil.get("production_capacity", {})
        mult = {"partial": 0.5, "general": 1.0, "total": 2.0}.get(level, 0)
        stab_cost = {"partial": 0.5, "general": 1.0, "total": 2.0}.get(level, 0)
        mobilized = int(cap.get("ground", 0) * mult)
        mil["ground"] = mil.get("ground", 0) + mobilized
        c["political"]["stability"] = max(c["political"]["stability"] - stab_cost, 1)
        c["political"]["war_tiredness"] = (
            c["political"].get("war_tiredness", 0) + stab_cost * 0.5)
        self._log.append(
            f"  Mobilization {country_id} ({level}): +{mobilized}G, stab-{stab_cost}")

    def _collate_events(self, actions: dict, results: dict) -> Dict[str, dict]:
        """Build per-country event dicts for stability/support calculations."""
        events: Dict[str, dict] = {}
        for cid in self.ws.countries:
            c = self.ws.countries[cid]
            ev = {
                "casualties": 0, "territory_lost": 0, "territory_gained": 0,
                "sanctions_pain": 0, "mobilization_level": 0,
                "social_spending_ratio": c["economic"]["social_spending_baseline"],
                "propaganda_boost": 0, "rally_effect": 0,
                "perceived_weakness": 0, "repression_effect": 0,
                "nationalist_rally": 0,
            }

            for e in self.ws.events_log:
                if e.get("round") != self.ws.round_num:
                    continue
                if e.get("type") == "combat":
                    if e.get("attacker") == cid:
                        ev["casualties"] += e.get("attacker_losses", 0)
                    if e.get("defender") == cid:
                        ev["casualties"] += e.get("defender_losses", 0)
                    if e.get("zone_captured") and e.get("attacker") == cid:
                        ev["territory_gained"] += 1
                    if e.get("zone_captured") and e.get("defender") == cid:
                        ev["territory_lost"] += 1

            sanc = results.get("sanctions", {}).get(cid, {})
            ev["sanctions_pain"] = sanc.get("damage", 0) * c["economic"]["gdp"]

            mob = actions.get("mobilizations", {}).get(cid, None)
            if mob:
                ev["mobilization_level"] = {
                    "partial": 1, "general": 2, "total": 3}.get(mob, 0)

            budget = actions.get("budgets", {}).get(cid, {})
            if "social_spending_ratio" in budget:
                ev["social_spending_ratio"] = budget["social_spending_ratio"]
            elif "social_pct" in budget:
                ev["social_spending_ratio"] = budget["social_pct"]
            else:
                ev["social_spending_ratio"] = max(
                    c["economic"]["social_spending_baseline"] - 0.10, 0.10)

            for e in self.ws.events_log:
                if (e.get("round") == self.ws.round_num and
                        e.get("type") == "propaganda" and e.get("country") == cid):
                    boost = e.get("boost", 0)
                    gdp = c["economic"]["gdp"]
                    if gdp > 0:
                        ev["propaganda_boost"] = min(
                            math.log1p(boost / gdp * 100) * 0.5, 2.0)

            events[cid] = ev
        return events
