"""
TTT SEED — World Model Engine
===============================
Between-round batch processing. THREE-PASS architecture:
  Pass 1: Deterministic formulas calculate direct effects
  Pass 2: AI contextual adjustment (bounded +/-30%)
  Pass 3: Coherence check + narrative generation (no number changes)

Uses ALL formulas from concept test engine, IMPROVED:
- Stability: positive inertia, war-gated, autocracy resilience (v2)
- Oil: responsive to crises, producers benefit (Gulf Gate blockade = +60%)
- GDP: multiplicative, bilateral trade weighted
- Elections: Columbia midterms R2, Ruthenia wartime R3-4, Columbia presidential R5

Author: ATLAS (World Model Engineer)
Version: 2.0 (SEED)
"""

import copy
import random
import math
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


class WorldModelEngine:
    """Three-pass world model engine for batch processing between rounds."""

    def __init__(self, world_state: WorldState):
        self.ws = world_state
        self.trade_weights = derive_trade_weights(self.ws.countries)
        self._log: List[str] = []

    def process_round(self, world_state: WorldState,
                      all_actions: dict, round_num: int) -> Tuple[dict, str, List[str]]:
        """Three-pass processing per round.

        Returns (results_dict, narrative_string, flags_list).
        """
        self.ws = world_state
        self.ws.round_num = round_num
        self.trade_weights = derive_trade_weights(self.ws.countries)
        self._log = []
        self._log.append(f"=== ROUND {round_num} WORLD MODEL PROCESSING ===")

        # PASS 1: Deterministic
        self._log.append("--- PASS 1: DETERMINISTIC ---")
        det_results = self.deterministic_pass(all_actions, round_num)

        # PASS 2: AI Contextual Adjustment (bounded +/-30%)
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

    # ===================================================================
    # PASS 1: DETERMINISTIC
    # ===================================================================

    def deterministic_pass(self, actions: dict, round_num: int) -> dict:
        """Pure formula calculations. Mutates world state."""
        results: dict = {
            "gdp": {}, "sanctions": {}, "tariffs": {},
            "stability": {}, "support": {}, "oil_price": 0.0,
            "revenue": {}, "budget": {}, "military_production": {},
            "tech": {}, "inflation": {}, "debt": {},
            "combat_secondary": [], "financial_crisis": {},
            "elections": {},
        }

        # Step 0: Apply submitted settings
        self._apply_tariff_changes(actions.get("tariff_changes", {}))
        self._apply_sanction_changes(actions.get("sanction_changes", {}))
        self._apply_opec_changes(actions.get("opec_production", {}))
        self._apply_rare_earth_changes(actions.get("rare_earth_restrictions", {}))
        self._apply_blockade_changes(actions.get("blockade_changes", {}))

        # Step 1: Oil price
        results["oil_price"] = self._calc_oil_price()
        self.ws.oil_price = results["oil_price"]
        self.ws.oil_price_index = results["oil_price"] / 80.0 * 100.0

        # Steps 2-5: Per-country calculations
        events_by_country = self._collate_events(actions, results)

        for cid in list(self.ws.countries.keys()):
            c = self.ws.countries[cid]

            # Step 2: Economic state update
            sanc_damage, sanc_costs = self._calc_sanctions_impact(cid)
            results["sanctions"][cid] = {"damage": sanc_damage, "costs": sanc_costs}

            tariff_info = self._calc_tariff_impact(cid)
            results["tariffs"][cid] = tariff_info

            money_printed = actions.get("budgets", {}).get(cid, {}).get("money_printed", 0)
            new_inflation = self._calc_inflation(cid, money_printed)
            results["inflation"][cid] = new_inflation
            c["economic"]["inflation"] = new_inflation

            gdp_result = self._calc_gdp_growth(cid, sanc_damage, tariff_info)
            results["gdp"][cid] = gdp_result
            c["economic"]["gdp"] = gdp_result["new_gdp"]
            c["economic"]["gdp_growth_rate"] = gdp_result["growth_pct"]

            deficit = actions.get("budgets", {}).get(cid, {}).get("deficit", 0)
            new_debt = self._calc_debt_service(cid, max(deficit, 0))
            results["debt"][cid] = new_debt
            c["economic"]["debt_burden"] = new_debt

            # Step 3: Political state update
            ev = events_by_country.get(cid, {})
            new_stab = self._calc_stability(cid, ev)
            results["stability"][cid] = new_stab
            c["political"]["stability"] = new_stab

            new_sup = self._calc_political_support(cid, ev, round_num)
            results["support"][cid] = new_sup
            c["political"]["political_support"] = new_sup

            # Update war tiredness
            self._update_war_tiredness(cid)

            # Update threshold flags
            self._update_threshold_flags(cid)

            # Step 4: Revenue & budget execution
            rev = self._calc_revenue(cid)
            results["revenue"][cid] = rev

            budget = actions.get("budgets", {}).get(cid, {})
            bud_result = self._calc_budget_execution(cid, budget, rev)
            results["budget"][cid] = bud_result

            # Military production
            mil_alloc = budget.get("military", {})
            prod_result = self._calc_military_production(cid, mil_alloc)
            results["military_production"][cid] = prod_result

            # Mobilization
            mob = actions.get("mobilizations", {}).get(cid, None)
            if mob:
                self._apply_mobilization(cid, mob)

            # Step 5: Technology advancement
            rd = actions.get("tech_rd", {}).get(cid, {"nuclear": 0, "ai": 0})
            tech_result = self._calc_tech_advancement(cid, rd)
            results["tech"][cid] = tech_result

            # Financial crisis check
            crisis = self._check_financial_crisis(cid)
            results["financial_crisis"][cid] = crisis

        # Elections
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
    # ECONOMIC FORMULAS
    # ===================================================================

    def _calc_gdp_growth(self, country_id: str, sanctions_damage: float,
                         tariff_info: dict) -> dict:
        """Multiplicative factor model for GDP growth."""
        c = self.ws.countries[country_id]
        eco = c["economic"]
        old_gdp = eco["gdp"]
        base_growth = eco["gdp_growth_rate"] / 100.0

        # Tariff factor
        net_tariff_cost = tariff_info.get("net_gdp_cost", 0)
        tariff_factor = max(0.5, 1.0 - (net_tariff_cost / max(old_gdp, 0.01)))

        # Sanctions factor
        sanctions_factor = max(0.5, 1.0 - sanctions_damage)

        # War factor
        war_zones = self._count_war_zones(country_id)
        infra_damage = self._get_infra_damage(country_id)
        war_factor = max(0.5, 1.0 - (war_zones * 0.02) - (infra_damage * 0.05))

        # Tech factor
        ai_level = c["technology"]["ai_level"]
        tech_factor = 1.0 + AI_LEVEL_TECH_FACTOR.get(ai_level, 0)

        # Inflation factor
        inflation = eco["inflation"]
        inflation_factor = max(0.5, 1.0 - (inflation / 100.0 * 0.015))

        # Blockade factor
        blockade_frac = self._get_blockade_fraction(country_id)
        blockade_factor = max(0.5, 1.0 - blockade_frac * 0.4)

        # Semiconductor disruption factor (FIX 2)
        semiconductor_factor = self._calc_semiconductor_disruption(country_id)

        # Combined multiplicative growth
        combined = (tariff_factor * sanctions_factor * war_factor
                    * tech_factor * inflation_factor * blockade_factor
                    * semiconductor_factor)
        effective_growth = base_growth * combined
        new_gdp = old_gdp * (1.0 + effective_growth)
        new_gdp = max(new_gdp, 0.01)

        growth_pct = effective_growth * 100.0

        self._log.append(
            f"  GDP {country_id}: {old_gdp:.2f}->{new_gdp:.2f} "
            f"(growth {growth_pct:+.2f}%, t={tariff_factor:.3f} "
            f"s={sanctions_factor:.3f} w={war_factor:.3f} "
            f"tech={tech_factor:.3f} i={inflation_factor:.3f} "
            f"b={blockade_factor:.3f} semi={semiconductor_factor:.3f})"
        )

        return {
            "old_gdp": old_gdp, "new_gdp": round(new_gdp, 2),
            "growth_pct": round(growth_pct, 2), "base_growth": round(base_growth * 100, 2),
            "tariff_factor": tariff_factor, "sanctions_factor": sanctions_factor,
            "war_factor": war_factor, "tech_factor": tech_factor,
            "inflation_factor": inflation_factor, "blockade_factor": blockade_factor,
            "semiconductor_factor": semiconductor_factor,
        }

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

    def _calc_oil_price(self) -> float:
        """Oil price: responsive to crises, blockades, wars, sanctions.

        V4 changes:
        - Gulf Gate blockade = +80% (was +60%)
        - Formosa Strait blockade = +15%
        - War premium: +10% per major war (capped 30%)
        - Sanctions on oil producers reduce supply
        - Speculative spike from crisis count
        - Oil producer revenue update
        - Target: peacetime $75-85, Gulf Gate blocked $140-180, crisis $180-250
        """
        base_price = 80.0

        # OPEC decisions
        supply_factor = 1.0
        for member, decision in self.ws.opec_production.items():
            if decision == "low":
                supply_factor -= 0.06  # was 0.05
            elif decision == "high":
                supply_factor += 0.06

        # CHOKEPOINT DISRUPTIONS -- much stronger impact
        disruption = 1.0

        # Gulf Gate blockade -- MASSIVE impact (20% of world oil transits)
        gulf_gate_blocked = self._is_chokepoint_blocked('gulf_gate')
        # Also check legacy chokepoint_status for hormuz / gulf_gate_ground
        for cp_name in ('hormuz', 'gulf_gate_ground'):
            if self.ws.chokepoint_status.get(cp_name) == 'blocked':
                gulf_gate_blocked = True
        if gulf_gate_blocked:
            disruption += 0.80  # was 0.60 -- 80% price spike

        # Formosa Strait blockade -- moderate (trade disruption, not oil directly)
        formosa_blocked = self._is_chokepoint_blocked('formosa_strait')
        if self.ws.chokepoint_status.get('taiwan_strait') == 'blocked':
            formosa_blocked = True
        if formosa_blocked:
            disruption += 0.15

        # Other chokepoints (suez, malacca, etc.)
        for cp_name, status in self.ws.chokepoint_status.items():
            if status != "blocked":
                continue
            if cp_name in ("hormuz", "gulf_gate_ground", "taiwan_strait"):
                continue  # already handled above
            if cp_name == "suez":
                disruption += 0.15
            elif cp_name == "malacca":
                disruption += 0.20
            else:
                disruption += 0.05

        # WAR PREMIUM -- any major war adds uncertainty premium
        war_premium = 0.0
        major_war_countries = {'columbia', 'cathay', 'persia', 'solaria', 'sarmatia'}
        for war in self.ws.wars:
            participants = [war.get('attacker', ''), war.get('defender', '')]
            if any(p in major_war_countries for p in participants):
                war_premium += 0.10  # 10% per major war
        war_premium = min(war_premium, 0.30)  # cap at 30%

        # SANCTIONS on oil producers -- reduce supply
        sanctions_supply_hit = 0.0
        for producer in ['sarmatia', 'persia']:
            sanctions_level = self._get_sanctions_on(producer)
            if sanctions_level >= 2:
                sanctions_supply_hit += 0.08  # each heavily sanctioned producer = 8% supply reduction

        # DEMAND from global GDP growth
        n_countries = len(self.ws.countries)
        gdp_growth_avg = 0.0
        if n_countries > 0:
            gdp_growth_avg = sum(
                c["economic"].get("gdp_growth_rate", 0)
                for c in self.ws.countries.values()
            ) / n_countries
        demand_factor = 1.0 + (gdp_growth_avg - 2.0) * 0.05  # demand elasticity

        # SPECULATIVE SPIKE -- markets overreact to crises
        crisis_count = len(self.ws.wars) + (1 if gulf_gate_blocked else 0) + (1 if formosa_blocked else 0)
        speculation = 1.0 + crisis_count * 0.05  # 5% per active crisis

        final_supply = max(0.5, supply_factor - sanctions_supply_hit)
        price = base_price * (demand_factor / final_supply) * disruption * (1 + war_premium) * speculation

        # Oil producer revenue update
        for cid, country in self.ws.countries.items():
            if country["economic"].get("oil_producer"):
                resource_pct = country["economic"]["sectors"].get("resources", 0) / 100.0
                oil_revenue = price * resource_pct * country["economic"]["gdp"] * 0.01
                oil_revenue = max(oil_revenue, 0.0)
                country["economic"]["oil_revenue"] = round(oil_revenue, 2)

        price = round(max(30.0, min(250.0, price)), 1)  # floor $30, ceiling $250

        self._log.append(
            f"  Oil price: ${price:.1f} (supply={final_supply:.2f} "
            f"demand={demand_factor:.3f} disruption={disruption:.2f} "
            f"war_premium={war_premium:.2f} speculation={speculation:.2f} "
            f"sanctions_supply_hit={sanctions_supply_hit:.2f})"
        )
        return price

    def _calc_inflation(self, country_id: str, money_printed: float) -> float:
        """Inflation with 15% natural decay, 60x money-printing multiplier."""
        c = self.ws.countries[country_id]
        prev = c["economic"]["inflation"]
        gdp = c["economic"]["gdp"]

        new_infl = prev * 0.85
        if gdp > 0 and money_printed > 0:
            new_infl += (money_printed / gdp) * 60.0
        new_infl = clamp(new_infl, 0.0, 500.0)

        excess = max(0, new_infl - 5)
        erosion = excess * 0.03 * gdp
        c["economic"]["inflation_revenue_erosion"] = round(erosion, 2)

        return round(new_infl, 2)

    def _calc_debt_service(self, country_id: str, deficit: float) -> float:
        c = self.ws.countries[country_id]
        old_debt = c["economic"]["debt_burden"]
        new_debt = old_debt
        if deficit > 0:
            new_debt = old_debt + deficit * 0.12
        return round(max(new_debt, 0.0), 2)

    def _calc_revenue(self, country_id: str) -> float:
        """Revenue = GDP * tax_rate + oil_revenue - sanctions - inflation_erosion - war_damage - debt."""
        c = self.ws.countries[country_id]
        eco = c["economic"]
        gdp = eco["gdp"]
        tax_rate = eco["tax_rate"]

        base_rev = gdp * tax_rate

        oil_rev = 0.0
        if eco.get("oil_producer"):
            oil_share = eco["sectors"].get("resources", 0) / 100.0
            oil_rev = gdp * oil_share * (self.ws.oil_price / 80.0 - 1.0) * 0.3
            oil_rev = max(oil_rev, 0.0)

        sanc_cost = 0.0
        sanctions = self.ws.bilateral.get("sanctions", {})
        for sanctioner, targets in sanctions.items():
            level = targets.get(country_id, 0)
            if level > 0:
                bw = self.trade_weights.get(sanctioner, {}).get(country_id, 0)
                sanc_cost += level * bw * 0.015 * gdp

        infl_erosion = eco.get("inflation_revenue_erosion",
                               (eco["inflation"] / 100.0) * 0.03 * gdp)
        war_damage = self._get_infra_damage(country_id) * 0.02 * gdp
        debt = eco["debt_burden"]

        revenue = base_rev + oil_rev - sanc_cost - infl_erosion - war_damage - debt
        revenue = max(revenue, 0.0)

        self._log.append(f"  Revenue {country_id}: {revenue:.2f}")
        return round(revenue, 2)

    # ===================================================================
    # POLITICAL FORMULAS
    # ===================================================================

    def _calc_stability(self, country_id: str, events: dict) -> float:
        """V4 stability: refined friction model with wartime resilience.

        Key changes from v3:
        - War friction reduced: defenders -0.10 (was -0.25), attackers -0.08 (was -0.15)
        - Wartime democratic resilience: democracies under invasion get +0.15/round
        - Society adaptation: war 3+ rounds halves war tiredness growth
        - Social spending 1.5x effectiveness during war
        - War tiredness accumulation slowed (0.2 defender, 0.15 attacker)
        - Target: Ruthenia declines ~4->2.5-3.0 over 8 rounds, not to 1.0
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

        # Positive inertia -- weaker, only at high stability
        if 7 <= old_stab < 9:
            delta += 0.05

        # GDP growth -- much weaker positive effect
        gdp_growth = eco.get("gdp_growth_rate", 0)
        if gdp_growth > 2:
            delta += min((gdp_growth - 2) * 0.08, 0.15)
        elif gdp_growth < -2:
            delta += gdp_growth * 0.3  # negative growth hurts more

        # Social spending -- below baseline is costly
        # During war, social spending is 1.5x more effective (wartime programs matter more)
        social_ratio = events.get("social_spending_ratio", 0.20)
        baseline = eco.get("social_spending_baseline", 0.30)
        social_effectiveness = 1.5 if at_war else 1.0
        if social_ratio >= baseline:
            delta += 0.05 * social_effectiveness  # meeting baseline: slight positive, amplified in war
        elif social_ratio >= baseline - 0.05:
            delta -= 0.05  # minor shortfall -- small penalty
        else:
            shortfall = baseline - social_ratio
            delta -= shortfall * 3  # meaningful penalty for serious underspending

        # WAR FRICTION: depends on how directly involved (REDUCED from v3)
        is_frontline = False
        is_primary = False
        if at_war:
            # Check if primary belligerent (attacker/defender) or allied
            is_primary = any(
                w.get("attacker") == country_id or w.get("defender") == country_id
                for w in self.ws.wars
            )
            # Check if frontline (territory being fought over) vs distant power projection
            is_frontline = any(
                w.get("defender") == country_id for w in self.ws.wars
            )
            if is_frontline:
                delta -= 0.10  # defender: was -0.25, now -0.10
            elif is_primary:
                delta -= 0.08  # attacker: was -0.15, now -0.08
            else:
                delta -= 0.05  # allied/supporting role: lighter cost
            casualties = events.get("casualties", 0)
            delta -= casualties * 0.2
            territory_lost = events.get("territory_lost", 0)
            delta -= territory_lost * 0.4
            territory_gained = events.get("territory_gained", 0)
            delta += territory_gained * 0.15
            war_tiredness = pol.get("war_tiredness", 0)
            delta -= min(war_tiredness * 0.04, 0.4)  # capped contribution

            # WARTIME DEMOCRATIC RESILIENCE: democracies under existential threat
            # get sustained +0.15 per round ("rally around the flag" ongoing effect)
            if is_frontline and regime in ("democracy", "hybrid"):
                delta += 0.15  # sustained democratic resilience under invasion

        # SANCTIONS FRICTION: -0.1 * level per round for targets
        if sanctions_level > 0:
            delta -= 0.1 * sanctions_level
        if under_heavy_sanctions:
            sanc_hit = events.get("sanctions_pain", 0)
            gdp = eco["gdp"]
            if gdp > 0:
                sanc_hit = sanc_hit / gdp
            delta -= abs(sanc_hit) * 0.8

        # INFLATION FRICTION: above 3% costs stability
        inflation = eco.get("inflation", 0)
        if inflation > 3:
            delta -= (inflation - 3) * 0.05
        if inflation > 20:
            delta -= (inflation - 20) * 0.03  # additional penalty for hyperinflation

        # Mobilization
        mob_level = events.get("mobilization_level", 0)
        if mob_level > 0:
            delta -= mob_level * 0.2

        # Propaganda
        prop_boost = events.get("propaganda_boost", 0)
        delta += prop_boost

        # Peaceful non-sanctioned countries: slightly less volatile (but not 0.25x)
        if not at_war and not under_heavy_sanctions:
            if delta < 0:
                delta *= 0.5  # was 0.25, now 0.5 -- still dampened but real

        # Autocracy resilience
        if regime == "autocracy":
            if delta < 0:
                delta *= 0.75

        # HARD CAP at 9.0
        new_stab = clamp(old_stab + delta, 1.0, 9.0)
        self._log.append(
            f"  Stability {country_id}: {old_stab:.1f}->{new_stab:.1f} (d={delta:+.2f})")
        return round(new_stab, 2)

    def _calc_political_support(self, country_id: str, events: dict,
                                 round_num: int) -> float:
        """Democracy vs autocracy support calculation.

        V3 changes:
        - Mean-reversion toward 50% at rate 0.05 * (support - 50) per round
        - Hard cap at 85% (not 100%)
        - Reduced positive deltas from GDP/stability
        - War casualties have stronger effect
        """
        c = self.ws.countries[country_id]
        pol = c["political"]
        eco = c["economic"]
        regime = pol.get("regime_type", c.get("regime_type", "democracy"))
        old_sup = pol["political_support"]
        delta = 0.0

        stability = pol["stability"]
        gdp_growth = eco["gdp_growth_rate"]
        casualties = events.get("casualties", 0)

        if regime in ("democracy", "hybrid"):
            delta += (gdp_growth - 2.0) * 0.8  # reduced from 1.5
            delta -= casualties * 3.0  # increased from 2.0
            delta += (stability - 6.0) * 0.5  # reduced and centered higher

            # Election proximity effect
            if country_id == "columbia":
                if round_num == 1:
                    delta -= 1.0  # midterms approaching
                elif round_num == 4:
                    delta -= 2.0  # presidential approaching
            elif country_id == "ruthenia":
                if round_num in (2, 3):
                    delta -= 1.5  # election pressure

            # War tiredness damages support in democracies
            war_tiredness = pol.get("war_tiredness", 0)
            if war_tiredness > 2:
                delta -= (war_tiredness - 2) * 1.0
        else:
            delta += (stability - 6.0) * 0.8  # reduced from 1.5
            weakness = events.get("perceived_weakness", 0)
            delta -= weakness * 5.0
            repression = events.get("repression_effect", 0)
            delta += repression
            nationalist = events.get("nationalist_rally", 0)
            delta += nationalist

        # STRONG mean-reversion toward 50%
        delta -= (old_sup - 50.0) * 0.05

        # Hard cap at 85%
        new_sup = clamp(old_sup + delta, 5.0, 85.0)
        self._log.append(
            f"  Support {country_id}: {old_sup:.1f}->{new_sup:.1f} (d={delta:+.2f})")
        return round(new_sup, 2)

    # ===================================================================
    # MILITARY & TECH FORMULAS
    # ===================================================================

    def _calc_budget_execution(self, country_id: str, budget: dict,
                               revenue: float) -> dict:
        c = self.ws.countries[country_id]
        mil = c["military"]
        eco = c["economic"]

        maint_rate = mil.get("maintenance_cost_per_unit", 0.3)
        total_units = sum(mil.get(ut, 0) for ut in UNIT_TYPES)
        maintenance = total_units * maint_rate
        mandatory = maintenance + eco["debt_burden"]

        discretionary = max(revenue - mandatory, 0.0)

        social = min(budget.get("social_spending", discretionary * 0.3), discretionary)
        mil_budget = min(budget.get("military_total", discretionary * 0.3),
                         discretionary - social)
        tech_budget = min(budget.get("tech_total", discretionary * 0.1),
                          discretionary - social - mil_budget)
        reserves_add = max(discretionary - social - mil_budget - tech_budget, 0)

        eco["treasury"] += reserves_add
        surplus_deficit = revenue - mandatory - social - mil_budget - tech_budget
        if surplus_deficit < 0:
            eco["treasury"] += surplus_deficit
            if eco["treasury"] < 0:
                eco["treasury"] = 0
                self._log.append(f"  CRISIS: {country_id} reserves exhausted!")

        return {
            "revenue": revenue, "mandatory": mandatory, "maintenance": maintenance,
            "discretionary": discretionary, "social_spending": social,
            "military_budget": mil_budget, "tech_budget": tech_budget,
            "reserves_added": reserves_add, "surplus_deficit": surplus_deficit,
            "new_treasury": eco["treasury"],
        }

    def _calc_military_production(self, country_id: str,
                                   military_alloc: dict) -> dict:
        """Produce units. Tiers: normal(1x/1x), accelerated(2x/2x), maximum(4x/3x)."""
        c = self.ws.countries[country_id]
        mil = c["military"]
        cap = mil.get("production_capacity", {})
        costs = mil.get("production_costs", {})
        produced = {}

        for utype in ["ground", "naval", "tactical_air"]:
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

        # Cathay strategic missile growth
        if country_id == "cathay" and mil.get("strategic_missile_growth", 0) > 0:
            mil["strategic_missiles"] = mil.get("strategic_missiles", 0) + 1
            produced["strategic_missiles"] = 1
            self._log.append("  Cathay strategic missile: +1")

        self._log.append(f"  Production {country_id}: {produced}")
        return produced

    def _calc_tech_advancement(self, country_id: str, rd_investment: dict) -> dict:
        c = self.ws.countries[country_id]
        tech = c["technology"]
        gdp = c["economic"]["gdp"]
        result = {"nuclear_levelup": False, "ai_levelup": False}

        # Rare earth impact on R&D (FIX 3)
        rare_earth_factor = self._calc_rare_earth_impact(country_id)

        # Nuclear R&D
        nuc_invest = rd_investment.get("nuclear", 0)
        if nuc_invest > 0 and gdp > 0:
            nuc_progress = (nuc_invest / max(gdp, 0.01)) * 0.5 * rare_earth_factor
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
            ai_progress = (ai_invest / max(gdp, 0.01)) * 0.5 * rare_earth_factor
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
    # ELECTIONS
    # ===================================================================

    def _process_election(self, country_id: str, election_type: str,
                          votes: dict, round_num: int) -> dict:
        """Process scheduled elections.

        Columbia midterms R2: team votes + AI popular vote (50/50)
        Ruthenia wartime R3-4: AI judges on gameplay outcomes
        Columbia presidential R5: nominations R4, speeches, votes + AI (50/50)
        """
        c = self.ws.countries[country_id]
        eco = c["economic"]
        pol = c["political"]

        gdp_growth = eco["gdp_growth_rate"]
        stability = pol["stability"]

        # AI incumbent score
        econ_perf = gdp_growth * 10.0
        stab_factor = (stability - 5) * 5.0
        war_penalty = 0.0
        for war in self.ws.wars:
            if (war.get("attacker") == country_id or
                    war.get("defender") == country_id or
                    country_id in war.get("allies", {}).get("attacker", []) or
                    country_id in war.get("allies", {}).get("defender", [])):
                war_penalty -= 5.0

        ai_score = clamp(50.0 + econ_perf + stab_factor + war_penalty, 0.0, 100.0)

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
        }

        # Columbia midterms: affects parliament seats
        if election_type == "columbia_midterms":
            if not incumbent_wins:
                # Opposition wins Seat 5, parliament flips 3-2 opposition
                result["parliament_change"] = "opposition_majority"
                result["note"] = ("Midterms: Opposition wins. Parliament now 3-2 "
                                  "opposition (Tribune + Challenger + NPC Seat 5).")
            else:
                result["parliament_change"] = "status_quo"
                result["note"] = "Midterms: President's camp retains majority."

        # Ruthenia wartime election
        elif election_type in ("ruthenia_wartime", "ruthenia_wartime_runoff"):
            war_tiredness = pol.get("war_tiredness", 0)
            # Adjust AI score for war-specific factors
            territory_factor = 0
            for w in self.ws.wars:
                if w.get("defender") == "ruthenia":
                    territory_factor -= len(w.get("occupied_zones", [])) * 3
            ai_score_adjusted = clamp(
                ai_score + territory_factor - war_tiredness * 2, 0, 100)
            final_incumbent = 0.5 * ai_score_adjusted + 0.5 * player_incumbent_pct
            incumbent_wins = final_incumbent >= 50.0
            result["ai_score"] = round(ai_score_adjusted, 2)
            result["final_incumbent_pct"] = round(final_incumbent, 2)
            result["incumbent_wins"] = incumbent_wins
            if not incumbent_wins:
                result["note"] = "Ruthenia election: Beacon loses. Bulwark becomes president."
            else:
                result["note"] = "Ruthenia election: Beacon survives."

        # Columbia presidential
        elif election_type == "columbia_presidential":
            result["note"] = ("Presidential election. " +
                              ("Incumbent camp wins." if incumbent_wins
                               else "Opposition wins. New president."))

        self._log.append(
            f"  Election {country_id} ({election_type}): "
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
    # PASS 2: AI CONTEXTUAL ADJUSTMENT (bounded +/-30%)
    # ===================================================================

    def ai_adjustment_pass(self, det_results: dict,
                           actions: dict, round_num: int) -> dict:
        """Heuristic adjustments simulating expert panel. All bounded +/-30%."""
        adjustments: dict = {}

        for cid, c in self.ws.countries.items():
            adj_list = []
            eco = c["economic"]
            pol = c["political"]
            gdp = eco["gdp"]

            # Major war loss: GDP confidence shock
            for combat in det_results.get("combat_secondary", []):
                if combat.get("defender") == cid and combat.get("defender_remaining", 1) == 0:
                    pct = random.uniform(0.05, 0.15)
                    hit = min(gdp * pct, gdp * 0.30)
                    eco["gdp"] = max(eco["gdp"] - hit, 0.01)
                    adj_list.append({
                        "type": "war_loss_confidence_shock",
                        "gdp_adjustment": -hit,
                        "justification": f"Market confidence collapses after defeat in {combat.get('zone', '?')}."
                    })

            # Sanctions coalition expansion
            regime = pol.get("regime_type", c.get("regime_type", "democracy"))
            sanc_data = det_results.get("sanctions", {}).get(cid, {})
            adapted = regime == "autocracy" and pol.get("war_tiredness", 0) > 2
            if sanc_data.get("damage", 0) > 0.10:
                pct = 0.02 if adapted else 0.05
                hit = min(gdp * pct, gdp * 0.30)
                eco["gdp"] = max(eco["gdp"] - hit, 0.01)
                adj_list.append({
                    "type": "sanctions_market_panic",
                    "gdp_adjustment": -hit,
                    "justification": "Broad sanctions trigger market panic."
                                     + (" (adapted)" if adapted else "")
                })

            # Tech breakthrough optimism
            tech_res = det_results.get("tech", {}).get(cid, {})
            if tech_res.get("ai_levelup") or tech_res.get("nuclear_levelup"):
                boost = min(gdp * 0.05, gdp * 0.30)
                eco["gdp"] += boost
                adj_list.append({
                    "type": "tech_breakthrough_optimism",
                    "gdp_adjustment": boost,
                    "justification": "Tech breakthrough sparks investor confidence."
                })

            # Rally-around-flag (diminishing)
            at_war = self.ws.get_country_at_war(cid)
            if at_war:
                war_duration = 0
                for w in self.ws.wars:
                    if w.get("attacker") == cid or w.get("defender") == cid:
                        start = w.get("start_round", 0)
                        war_duration = round_num - start if start >= 0 else round_num + abs(start)
                rally = max(10.0 - war_duration * 3.0, 0.0)
                if rally > 0:
                    bounded = min(rally, pol["political_support"] * 0.30)
                    pol["political_support"] = clamp(
                        pol["political_support"] + bounded, 0, 100)
                    adj_list.append({
                        "type": "rally_around_flag",
                        "support_adjustment": bounded,
                        "justification": f"Rally effect in year {war_duration}, diminishing."
                    })

            # War fatigue acceleration (long wars)
            if at_war:
                for w in self.ws.wars:
                    if w.get("attacker") == cid or w.get("defender") == cid:
                        start = w.get("start_round", 0)
                        dur = round_num - start if start >= 0 else round_num + abs(start)
                        if dur > 6:
                            wt = pol.get("war_tiredness", 0)
                            extra = min(wt * 0.03, 0.5)
                            pol["war_tiredness"] = wt + extra
                            adj_list.append({
                                "type": "war_fatigue_acceleration",
                                "fatigue_increase": extra,
                                "justification": f"Prolonged war ({dur} rounds) accelerates fatigue."
                            })

            # Capital flight if stability < 4
            if pol["stability"] < 4:
                flight_pct = 0.01 if regime == "autocracy" else 0.03
                flight = min(gdp * flight_pct, gdp * 0.30)
                eco["gdp"] = max(eco["gdp"] - flight, 0.01)
                adj_list.append({
                    "type": "capital_flight",
                    "gdp_adjustment": -flight,
                    "justification": "Low stability triggers capital exodus."
                                     + (" (controls)" if regime == "autocracy" else "")
                })

            if adj_list:
                adjustments[cid] = adj_list

        return adjustments

    # ===================================================================
    # PASS 3: COHERENCE CHECK + NARRATIVE
    # ===================================================================

    def coherence_pass(self, round_num: int) -> Tuple[List[str], str]:
        """Review world state. Flag contradictions. Generate narrative. No number changes."""
        flags: List[str] = []

        for cid, c in self.ws.countries.items():
            eco = c["economic"]
            pol = c["political"]
            mil = c["military"]

            if eco["gdp"] < 0:
                flags.append(f"IMPOSSIBLE: {cid} GDP negative ({eco['gdp']})")

            stab = pol["stability"]
            sup = pol["political_support"]
            if stab <= 2 and sup > 70:
                flags.append(f"SUSPICIOUS: {cid} stability={stab} but support={sup}")
            if stab >= 8 and sup < 20:
                flags.append(f"UNUSUAL: {cid} stability={stab} but support={sup}")

            at_war = self.ws.get_country_at_war(cid)
            total_mil = sum(mil.get(ut, 0) for ut in ["ground", "naval", "tactical_air"])
            if at_war and total_mil == 0:
                flags.append(f"CRITICAL: {cid} at war with 0 combat units")

            if self.ws.nuclear_used_this_sim and stab > 6:
                flags.append(f"CHECK: Nuclear used but {cid} stability={stab}")

        narrative = self._generate_narrative(round_num)
        return flags, narrative

    def _generate_narrative(self, round_num: int) -> str:
        lines = [f"ROUND {round_num} WORLD BRIEFING", "=" * 40]

        total_gdp = sum(c["economic"]["gdp"] for c in self.ws.countries.values())
        lines.append(f"\nGlobal GDP: {total_gdp:.1f} coins. Oil: ${self.ws.oil_price:.0f}/bbl.")

        if self.ws.wars:
            lines.append("\nACTIVE CONFLICTS:")
            for w in self.ws.wars:
                lines.append(f"  {w['attacker']} vs {w['defender']} ({w.get('theater', '?')})")

        sorted_c = sorted(self.ws.countries.items(),
                          key=lambda x: x[1]["economic"]["gdp"], reverse=True)
        lines.append("\nTOP ECONOMIES:")
        for cid, c in sorted_c[:5]:
            lines.append(
                f"  {c.get('sim_name', cid)}: GDP {c['economic']['gdp']:.1f}, "
                f"growth {c['economic']['gdp_growth_rate']:+.1f}%, "
                f"stab {c['political']['stability']:.0f}/10")

        lines.append("\nKEY INDICATORS:")
        for cid, c in self.ws.countries.items():
            stab = c["political"]["stability"]
            if stab <= 4:
                lines.append(f"  WARNING: {c.get('sim_name', cid)} stability {stab}/10")
            if c["economic"]["inflation"] > 20:
                lines.append(
                    f"  WARNING: {c.get('sim_name', cid)} inflation {c['economic']['inflation']:.0f}%")

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
    # INTERNAL HELPERS
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
        """Apply rare earth restriction actions. Cathay can restrict exports to target countries.

        Format: {"target_country_id": level} where level is 0-3.
        Level 0 = lift restrictions, 1-3 = mild to severe.
        Cost to Cathay: loses trade revenue proportional to restriction level.
        """
        if not changes:
            return
        for target, level in changes.items():
            level = int(clamp(level, 0, 3))
            if level == 0:
                self.ws.rare_earth_restrictions.pop(target, None)
                self._log.append(f"  Rare earth: restrictions on {target} LIFTED")
            else:
                self.ws.rare_earth_restrictions[target] = level
                # Cost to Cathay: lose some trade revenue (rare earths are exports)
                cathay = self.ws.countries.get('cathay')
                if cathay:
                    trade_loss = level * 0.3  # coins per level per target
                    cathay['economic']['treasury'] = max(
                        cathay['economic']['treasury'] - trade_loss, 0)
                self._log.append(
                    f"  Rare earth: Cathay restricts {target} at level {level} "
                    f"(trade cost: {level * 0.3:.1f} coins)")

    def _apply_blockade_changes(self, changes: dict) -> None:
        """Apply blockade declarations or removals.

        Format: {"chokepoint_key": {"blocker": country_id}} to add,
                {"chokepoint_key": None} to remove.
        Also handles formosa_blockade flag.
        """
        if not changes:
            return
        for chokepoint, data in changes.items():
            if data is None:
                self.ws.active_blockades.pop(chokepoint, None)
                if chokepoint == 'formosa_strait':
                    self.ws.formosa_blockade = False
                self._log.append(f"  Blockade: {chokepoint} LIFTED")
            else:
                self.ws.active_blockades[chokepoint] = data
                if chokepoint == 'formosa_strait':
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
        c["political"]["war_tiredness"] = c["political"].get("war_tiredness", 0) + stab_cost * 0.5
        self._log.append(f"  Mobilization {country_id} ({level}): +{mobilized}G, stab-{stab_cost}")

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

    def _sanctions_level(self, country_id: str) -> int:
        sanctions = self.ws.bilateral.get("sanctions", {})
        max_level = 0
        for sanctioner, targets in sanctions.items():
            level = targets.get(country_id, 0)
            if level > max_level:
                max_level = level
        return max_level

    def _is_chokepoint_blocked(self, chokepoint_key: str) -> bool:
        """Check if a chokepoint is actively blocked via active_blockades."""
        blockades = getattr(self.ws, 'active_blockades', {})
        return chokepoint_key in blockades

    def _get_sanctions_on(self, target_country: str) -> int:
        """Get the maximum sanctions level imposed on a country (from bilateral data)."""
        sanctions = self.ws.bilateral.get("sanctions", {})
        max_level = 0
        for sanctioner, targets in sanctions.items():
            level = targets.get(target_country, 0)
            if level > max_level:
                max_level = level
        return max_level

    def _calc_semiconductor_disruption(self, country_id: str) -> float:
        """If Formosa is blockaded, invaded, or at war, dependent countries lose GDP.

        Uses formosa_dependency from countries.csv (0-1 scale).
        Returns multiplicative factor for GDP growth (1.0 = no impact, 0.5 = floor).
        """
        dep = self.ws.countries[country_id]['economic'].get('formosa_dependency', 0)
        if dep <= 0:
            return 1.0  # no dependency, no impact

        # Check if Formosa is disrupted
        formosa_disrupted = False
        disruption_severity = 0.0

        # Check if Formosa is at war
        for war in self.ws.wars:
            if 'formosa' in [war.get('attacker'), war.get('defender')]:
                formosa_disrupted = True
                disruption_severity = 0.8  # severe -- active combat on semiconductor island

        # Check if Formosa is blockaded (naval blockade flag or active_blockades)
        formosa_blockade = getattr(self.ws, 'formosa_blockade', False)
        if not formosa_blockade:
            # Also check active_blockades for formosa_strait
            formosa_blockade = self._is_chokepoint_blocked('formosa_strait')
        if not formosa_blockade:
            # Also check chokepoint_status for taiwan_strait
            formosa_blockade = self.ws.chokepoint_status.get('taiwan_strait') == 'blocked'

        if formosa_blockade and not formosa_disrupted:
            formosa_disrupted = True
            disruption_severity = 0.5  # moderate -- blockade disrupts shipping but fabs still operate

        if not formosa_disrupted:
            return 1.0

        # GDP impact: country loses (dependency * severity) of its tech sector GDP
        # E.g., Columbia with 65% dependency and 80% severity loses 52% of tech sector output
        tech_sector_pct = self.ws.countries[country_id]['economic']['sectors'].get('technology', 0) / 100.0
        gdp_loss_fraction = dep * disruption_severity * tech_sector_pct

        return max(0.5, 1.0 - gdp_loss_fraction)  # floor at 50% -- total collapse prevented

    def _calc_rare_earth_impact(self, country_id: str) -> float:
        """If Cathay has declared rare earth restrictions, affected countries' R&D slows.

        Returns multiplicative factor for R&D progress (1.0 = no impact, 0.4 = floor).
        """
        restrictions = getattr(self.ws, 'rare_earth_restrictions', {})
        if country_id in restrictions:
            restriction_level = restrictions[country_id]  # 0-3 scale
            # Each level reduces R&D progress by 15%
            rd_penalty = 1.0 - (restriction_level * 0.15)
            return max(0.4, rd_penalty)  # floor at 40% -- can't completely block R&D
        return 1.0  # no restrictions

    def _update_war_tiredness(self, country_id: str) -> None:
        """War tiredness: defenders +0.2/round, attackers +0.15/round.
        Society adaptation: after 3+ rounds at war, growth rate halves.
        """
        c = self.ws.countries[country_id]
        pol = c["political"]
        at_war = self.ws.get_country_at_war(country_id)
        current_wt = pol.get("war_tiredness", 0)
        if at_war:
            # Determine role: defender accumulates faster than attacker
            is_defender = any(
                w.get("defender") == country_id for w in self.ws.wars
            )
            is_attacker = any(
                w.get("attacker") == country_id for w in self.ws.wars
            )
            if is_defender:
                base_increase = 0.20  # was 0.4
            elif is_attacker:
                base_increase = 0.15
            else:
                base_increase = 0.10  # allied/supporting role

            # Society adaptation: after 3+ rounds at war, tiredness growth halves
            war_duration = 0
            for w in self.ws.wars:
                if w.get("attacker") == country_id or w.get("defender") == country_id:
                    start = w.get("start_round", 0)
                    dur = self.ws.round_num - start if start >= 0 else self.ws.round_num + abs(start)
                    war_duration = max(war_duration, dur)
            if war_duration >= 3:
                base_increase *= 0.5  # society adapts to wartime

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

    def _check_financial_crisis(self, country_id: str) -> dict:
        c = self.ws.countries[country_id]
        eco = c["economic"]
        pol = c["political"]
        gdp_growth = eco["gdp_growth_rate"]
        stability = pol["stability"]
        inflation = eco["inflation"]

        market_index = clamp(
            50.0 + gdp_growth * 5.0 + (stability - 5) * 5.0 - inflation * 0.5,
            0.0, 100.0)

        crisis = False
        capital_flight = 0.0
        if market_index < 30.0:
            crisis = True
            severity = (30.0 - market_index) / 30.0
            capital_flight = severity * 0.10 * eco["gdp"]
            eco["gdp"] = max(eco["gdp"] - capital_flight, 0.01)
            eco["treasury"] = max(eco["treasury"] - capital_flight * 0.5, 0)

        return {
            "market_index": round(market_index, 2),
            "crisis": crisis,
            "capital_flight": round(capital_flight, 2),
        }

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

            # From combat events in the events_log
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

            # Sanctions pain
            sanc = results.get("sanctions", {}).get(cid, {})
            ev["sanctions_pain"] = sanc.get("damage", 0) * c["economic"]["gdp"]

            # Mobilization
            mob = actions.get("mobilizations", {}).get(cid, None)
            if mob:
                ev["mobilization_level"] = {"partial": 1, "general": 2, "total": 3}.get(mob, 0)

            # Budget social spending -- check both key names
            budget = actions.get("budgets", {}).get(cid, {})
            if "social_spending_ratio" in budget:
                ev["social_spending_ratio"] = budget["social_spending_ratio"]
            elif "social_pct" in budget:
                ev["social_spending_ratio"] = budget["social_pct"]
            else:
                # No budget submitted: use a DEFAULT that is BELOW baseline
                # This forces stability pressure when agents don't allocate
                ev["social_spending_ratio"] = max(
                    c["economic"]["social_spending_baseline"] - 0.10, 0.10)

            # Propaganda
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
