"""
TTT Simulation Engine -- Thucydides Trap Test
==============================================
Three-pass world model engine for processing simulation rounds.

Pass 1: Deterministic formulas calculate direct effects.
Pass 2: AI contextual adjustment (heuristic rules for test; upgradeable to LLM).
Pass 3: Coherence check -- flags contradictions, generates narrative, does NOT change numbers.

Author: ATLAS (World Model Engineer)
Version: 1.0
"""

import json
import copy
import random
import math
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any


# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

AI_LEVEL_TECH_FACTOR = {0: 0.0, 1: 0.0, 2: 0.05, 3: 0.15, 4: 0.30}
AI_LEVEL_COMBAT_BONUS = {0: 0, 1: 0, 2: 0, 3: 1, 4: 2}

NUCLEAR_RD_THRESHOLDS = {0: 0.60, 1: 0.80, 2: 1.00}
AI_RD_THRESHOLDS = {0: 0.20, 1: 0.40, 2: 0.60, 3: 1.00}

OPEC_PRODUCTION_MULTIPLIER = {"low": 0.80, "normal": 1.00, "high": 1.20}

PRODUCTION_TIER_COST = {"normal": 1.0, "accelerated": 2.0, "maximum": 4.0}
PRODUCTION_TIER_OUTPUT = {"normal": 1.0, "accelerated": 2.0, "maximum": 3.0}

UNIT_TYPES = ["ground", "naval", "tactical_air", "strategic_missiles", "air_defense"]

STABILITY_THRESHOLDS = {
    "unstable": 6,
    "protest_probable": 5,
    "protest_automatic": 3,
    "regime_collapse_risk": 2,
    "failed_state": 1,
}

CHOKEPOINTS = {
    "hormuz": {"zone": "me_gulf_hormuz", "oil_impact": 0.35},
    "malacca": {"zone": "g_sea_southeast_asia", "trade_impact": 0.30},
    "taiwan_strait": {"zone": "ts_strait", "tech_impact": 0.50},
    "suez": {"zone": "g_sea_med_east", "trade_impact": 0.15},
    "bosphorus": {"zone": "g_sea_black", "trade_impact": 0.08},
    "giuk": {"zone": "g_sea_giuk", "detection": True},
    "caribbean": {"zone": "g_sea_gulf_caribbean", "trade_impact": 0.05},
    "south_china_sea": {"zone": "g_sea_south_china", "trade_impact": 0.20},
}


# ---------------------------------------------------------------------------
# WORLD STATE
# ---------------------------------------------------------------------------

class WorldState:
    """Holds the complete world state: all countries, zones, global indicators.
    Serializable to/from JSON for persistence between rounds."""

    def __init__(self):
        self.round_num: int = 0
        self.countries: Dict[str, dict] = {}
        self.zones: Dict[str, dict] = {}
        self.deployments: List[dict] = []
        self.bilateral: dict = {}
        self.organizations: List[dict] = []
        self.wars: List[dict] = []
        self.active_theaters: List[str] = []
        self.oil_price: float = 80.0
        self.oil_price_index: float = 100.0
        self.opec_production: Dict[str, str] = {}
        self.global_trade_volume_index: float = 100.0
        self.chokepoint_status: Dict[str, str] = {}
        self.round_log: List[str] = []
        self.nuclear_used_this_sim: bool = False

    # --- Serialization ---

    def to_dict(self) -> dict:
        """Serialize entire world state to a plain dictionary."""
        return {
            "round_num": self.round_num,
            "countries": copy.deepcopy(self.countries),
            "zones": copy.deepcopy(self.zones),
            "deployments": copy.deepcopy(self.deployments),
            "bilateral": copy.deepcopy(self.bilateral),
            "organizations": copy.deepcopy(self.organizations),
            "wars": copy.deepcopy(self.wars),
            "active_theaters": list(self.active_theaters),
            "oil_price": self.oil_price,
            "oil_price_index": self.oil_price_index,
            "opec_production": dict(self.opec_production),
            "global_trade_volume_index": self.global_trade_volume_index,
            "chokepoint_status": dict(self.chokepoint_status),
            "round_log": list(self.round_log),
            "nuclear_used_this_sim": self.nuclear_used_this_sim,
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, d: dict) -> "WorldState":
        """Reconstruct WorldState from a dictionary."""
        ws = cls()
        ws.round_num = d.get("round_num", 0)
        ws.countries = d.get("countries", {})
        ws.zones = d.get("zones", {})
        ws.deployments = d.get("deployments", [])
        ws.bilateral = d.get("bilateral", {})
        ws.organizations = d.get("organizations", [])
        ws.wars = d.get("wars", [])
        ws.active_theaters = d.get("active_theaters", [])
        ws.oil_price = d.get("oil_price", 80.0)
        ws.oil_price_index = d.get("oil_price_index", 100.0)
        ws.opec_production = d.get("opec_production", {})
        ws.global_trade_volume_index = d.get("global_trade_volume_index", 100.0)
        ws.chokepoint_status = d.get("chokepoint_status", {})
        ws.round_log = d.get("round_log", [])
        ws.nuclear_used_this_sim = d.get("nuclear_used_this_sim", False)
        return ws


# ---------------------------------------------------------------------------
# HELPER: derive bilateral trade weight matrix
# ---------------------------------------------------------------------------

def _derive_trade_weights(countries: Dict[str, dict]) -> Dict[str, Dict[str, float]]:
    """Derive approximate bilateral trade weights from GDP and sector profiles.

    Since bilateral.json provides tariff/sanction levels but not explicit trade
    volumes, we approximate: trade between A and B is proportional to the product
    of their GDPs, weighted by sector complementarity (industry exports matched
    to services/tech imports and vice-versa).  The result is normalized so each
    country's outgoing trade weights sum to 1.0.
    """
    ids = list(countries.keys())
    raw: Dict[str, Dict[str, float]] = {c: {} for c in ids}
    for a in ids:
        ca = countries[a]
        gdp_a = ca["economic"]["gdp"]
        sec_a = ca["economic"]["sectors"]
        for b in ids:
            if a == b:
                continue
            cb = countries[b]
            gdp_b = cb["economic"]["gdp"]
            sec_b = cb["economic"]["sectors"]
            # Complementarity: industry↔resources, services↔tech
            comp = (sec_a.get("industry", 0) * sec_b.get("resources", 0)
                    + sec_a.get("resources", 0) * sec_b.get("industry", 0)
                    + sec_a.get("technology", 0) * sec_b.get("services", 0)
                    + sec_a.get("services", 0) * sec_b.get("technology", 0))
            comp = max(comp, 1.0)
            raw[a][b] = gdp_a * gdp_b * comp
    # Normalize per country
    weights: Dict[str, Dict[str, float]] = {}
    for a in ids:
        total = sum(raw[a].values())
        if total == 0:
            weights[a] = {b: 0.0 for b in ids if b != a}
        else:
            weights[a] = {b: raw[a][b] / total for b in ids if b != a}
    return weights


# ---------------------------------------------------------------------------
# LOADER
# ---------------------------------------------------------------------------

def load_starting_state(data_dir: Optional[str] = None) -> WorldState:
    """Load the initial world state from the three starting-data JSON files.

    Parameters
    ----------
    data_dir : str, optional
        Path to the STARTING_DATA directory.  If *None* the function looks
        relative to *this* file at ``../STARTING_DATA/``.
    """
    if data_dir is None:
        data_dir = os.path.join(os.path.dirname(__file__), "..", "STARTING_DATA")

    with open(os.path.join(data_dir, "countries.json"), "r") as f:
        countries_data = json.load(f)
    with open(os.path.join(data_dir, "bilateral.json"), "r") as f:
        bilateral_data = json.load(f)
    with open(os.path.join(data_dir, "deployments.json"), "r") as f:
        deployments_data = json.load(f)

    ws = WorldState()
    ws.round_num = 0

    # --- Countries ---
    country_list = countries_data.get("countries", [])
    for c in country_list:
        cid = c["id"]
        ws.countries[cid] = c

    # --- Bilateral ---
    ws.bilateral = bilateral_data

    # --- Deployments ---
    ws.deployments = deployments_data.get("deployments", [])

    # Build zone occupation map from deployments
    zone_map: Dict[str, dict] = {}
    for dep in ws.deployments:
        zid = dep["zone"]
        if zid not in zone_map:
            zone_map[zid] = {"forces": {}}
        country = dep["country"]
        utype = dep["unit_type"]
        count = dep["count"]
        if country not in zone_map[zid]["forces"]:
            zone_map[zid]["forces"][country] = {}
        zone_map[zid]["forces"][country][utype] = (
            zone_map[zid]["forces"][country].get(utype, 0) + count
        )
    ws.zones = zone_map

    # --- Organizations ---
    ws.organizations = countries_data.get("organizations", [])

    # --- Starting conditions ---
    sc = countries_data.get("starting_conditions", {})
    ws.wars = sc.get("wars", [])
    ws.active_theaters = sc.get("active_theaters", [])
    ws.opec_production = sc.get("opec_production", {})
    ws.oil_price_index = sc.get("oil_price_index", 100.0)
    ws.oil_price = 80.0 * (ws.oil_price_index / 100.0)

    # Initialize chokepoint statuses as open
    for cp in CHOKEPOINTS:
        ws.chokepoint_status[cp] = "open"

    return ws


# ---------------------------------------------------------------------------
# QUERY HELPERS  (for test runner convenience)
# ---------------------------------------------------------------------------

def get_country_gdp(ws: WorldState, country_id: str) -> float:
    """Return the GDP of *country_id*."""
    return ws.countries[country_id]["economic"]["gdp"]


def get_country_stability(ws: WorldState, country_id: str) -> float:
    return ws.countries[country_id]["political"]["stability"]


def get_country_support(ws: WorldState, country_id: str) -> float:
    return ws.countries[country_id]["political"]["political_support"]


def get_country_military(ws: WorldState, country_id: str) -> dict:
    return ws.countries[country_id]["military"]


def get_zone_control(ws: WorldState, zone_id: str) -> Dict[str, dict]:
    """Return {country: {unit_type: count}} for a zone."""
    return ws.zones.get(zone_id, {}).get("forces", {})


def get_oil_price(ws: WorldState) -> float:
    return ws.oil_price


# ---------------------------------------------------------------------------
# MAIN ENGINE
# ---------------------------------------------------------------------------

class TTTEngine:
    """Three-pass world-model engine for the Thucydides Trap simulation.

    Usage::

        ws = load_starting_state()
        engine = TTTEngine(ws)
        new_ws, report = engine.process_round(actions, round_num=1)
    """

    def __init__(self, world_state: WorldState):
        self.ws = copy.deepcopy(world_state)
        self.trade_weights = _derive_trade_weights(self.ws.countries)
        self._log: List[str] = []

    # -----------------------------------------------------------------------
    # TOP-LEVEL ROUND PROCESSOR
    # -----------------------------------------------------------------------

    def process_round(self, actions: dict, round_num: int) -> Tuple[WorldState, dict]:
        """Execute all three passes for one round.

        Parameters
        ----------
        actions : dict
            Round actions submitted by all countries.  Keys may include:

            - ``budgets``: {country_id: budget_dict}
            - ``tariff_changes``: {country_id: {target: new_level}}
            - ``sanction_changes``: {country_id: {target: new_level}}
            - ``opec_production``: {country_id: "low"/"normal"/"high"}
            - ``mobilizations``: {country_id: "partial"/"general"/"total"}
            - ``combat``: [{"attacker": ..., "defender": ..., "zone": ..., "units": N}]
            - ``blockades``: [{"country": ..., "zone": ...}]
            - ``missile_strikes``: [{"country": ..., "target_zone": ..., "warhead": "conventional"/"nuclear"}]
            - ``covert_ops``: [{"country": ..., "type": ..., "target": ...}]
            - ``propaganda``: {country_id: coins_spent}
            - ``tech_rd``: {country_id: {"nuclear": amount, "ai": amount}}
            - ``events``: [{"type": ..., ...}]  (misc events: arrests, coups, elections)

        round_num : int
            Current round number (1-indexed).

        Returns
        -------
        (WorldState, dict)
            The new world state and a report dictionary.
        """
        self.ws.round_num = round_num
        self._log = []
        self._log.append(f"=== ROUND {round_num} PROCESSING BEGINS ===")

        # PASS 1 -- DETERMINISTIC
        self._log.append("--- PASS 1: DETERMINISTIC ---")
        det_results = self._pass1_deterministic(actions, round_num)

        # PASS 2 -- AI CONTEXTUAL ADJUSTMENT
        self._log.append("--- PASS 2: AI CONTEXTUAL ADJUSTMENT ---")
        adj_results = self.ai_contextual_adjustment(det_results, actions, round_num)

        # PASS 3 -- COHERENCE CHECK
        self._log.append("--- PASS 3: COHERENCE CHECK ---")
        flags, narrative = self.coherence_check(round_num)

        self._log.append(f"=== ROUND {round_num} PROCESSING COMPLETE ===")
        self.ws.round_log = list(self._log)

        report = {
            "round": round_num,
            "deterministic_results": det_results,
            "ai_adjustments": adj_results,
            "coherence_flags": flags,
            "narrative": narrative,
            "log": list(self._log),
        }
        return copy.deepcopy(self.ws), report

    # -----------------------------------------------------------------------
    # PASS 1 — DETERMINISTIC
    # -----------------------------------------------------------------------

    def _pass1_deterministic(self, actions: dict, round_num: int) -> dict:
        """Run all deterministic formulas.  Mutates self.ws in place."""
        results: dict = {"gdp": {}, "sanctions": {}, "tariffs": {},
                         "stability": {}, "support": {}, "oil_price": 0.0,
                         "revenue": {}, "budget": {}, "military_production": {},
                         "tech": {}, "inflation": {}, "debt": {},
                         "combat": [], "financial_crisis": {}}

        # --- Apply setting changes ---
        self._apply_tariff_changes(actions.get("tariff_changes", {}))
        self._apply_sanction_changes(actions.get("sanction_changes", {}))
        self._apply_opec_changes(actions.get("opec_production", {}))

        # --- Blockades ---
        blockades = actions.get("blockades", [])
        self._apply_blockades(blockades)

        # --- Combat resolution ---
        combat_list = actions.get("combat", [])
        for battle in combat_list:
            result = self._resolve_combat_action(battle)
            results["combat"].append(result)

        # --- Missile strikes ---
        strikes = actions.get("missile_strikes", [])
        for strike in strikes:
            self._resolve_missile_strike(strike)

        # --- Covert ops ---
        covert = actions.get("covert_ops", [])
        for op in covert:
            self._resolve_covert_op(op)

        # --- Oil price ---
        results["oil_price"] = self.calc_oil_price(
            self.ws.opec_production, self._get_disruptions()
        )
        self.ws.oil_price = results["oil_price"]
        self.ws.oil_price_index = results["oil_price"] / 80.0 * 100.0

        # --- Per-country economic + political ---
        country_ids = list(self.ws.countries.keys())
        events_by_country = self._collate_events(actions, results)

        for cid in country_ids:
            c = self.ws.countries[cid]

            # Sanctions impact on this country
            sanc_damage, sanc_costs = self.calc_sanctions_impact(cid)
            results["sanctions"][cid] = {"damage": sanc_damage, "costs_to_imposers": sanc_costs}

            # Tariff impact
            tariff_info = self.calc_tariff_impact(cid)
            results["tariffs"][cid] = tariff_info

            # Inflation
            money_printed = self._get_money_printed(cid, actions)
            new_inflation = self.calc_inflation(
                cid, money_printed, c["economic"]["inflation"]
            )
            results["inflation"][cid] = new_inflation
            c["economic"]["inflation"] = new_inflation

            # GDP growth
            gdp_result = self.calc_gdp_growth(cid, actions, sanc_damage,
                                               tariff_info, results)
            results["gdp"][cid] = gdp_result
            c["economic"]["gdp"] = gdp_result["new_gdp"]
            c["economic"]["gdp_growth_rate"] = gdp_result["growth_pct"]

            # Debt service
            deficit = self._get_deficit(cid, actions)
            new_debt = self.calc_debt_service(cid, deficit)
            results["debt"][cid] = new_debt
            c["economic"]["debt_burden"] = new_debt

            # Revenue
            rev = self.calc_revenue(cid)
            results["revenue"][cid] = rev

            # Tech advancement
            rd = actions.get("tech_rd", {}).get(cid, {"nuclear": 0, "ai": 0})
            tech_result = self.calc_tech_advancement(cid, rd)
            results["tech"][cid] = tech_result

            # Budget execution
            budget = actions.get("budgets", {}).get(cid, {})
            bud_result = self.calc_budget_execution(cid, budget, rev)
            results["budget"][cid] = bud_result

            # Military production
            mil_alloc = budget.get("military", {})
            prod_result = self.calc_military_production(cid, mil_alloc)
            results["military_production"][cid] = prod_result

            # Stability
            ev = events_by_country.get(cid, {})
            new_stab = self.calc_stability(cid, ev)
            results["stability"][cid] = new_stab
            c["political"]["stability"] = new_stab

            # Political support
            new_sup = self.calc_political_support(cid, ev)
            results["support"][cid] = new_sup
            c["political"]["political_support"] = new_sup

            # Financial crisis check
            crisis = self.check_financial_crisis(cid)
            results["financial_crisis"][cid] = crisis

            # Mobilization
            mob = actions.get("mobilizations", {}).get(cid, None)
            if mob:
                self._apply_mobilization(cid, mob)

            # Propaganda
            prop_coins = actions.get("propaganda", {}).get(cid, 0)
            if prop_coins > 0:
                self._apply_propaganda(cid, prop_coins)

            # War tiredness: +0.3 per round for countries at war (separate from combat)
            # Society adapts: natural decay of 5% per round (adaptation/normalization)
            at_war = any(
                w.get("attacker") == cid or w.get("defender") == cid
                for w in self.ws.wars
            )
            current_wt = c["political"].get("war_tiredness", 0)
            if at_war:
                c["political"]["war_tiredness"] = current_wt * 0.95 + 0.3  # decay + increment
            else:
                # Not at war: war tiredness decays faster
                c["political"]["war_tiredness"] = max(current_wt * 0.85, 0)

        return results

    # -----------------------------------------------------------------------
    # FORMULA 1: GDP GROWTH  (multiplicative factor model)
    # -----------------------------------------------------------------------

    def calc_gdp_growth(self, country_id: str, actions: dict,
                        sanctions_damage: float, tariff_info: dict,
                        round_results: dict) -> dict:
        """Calculate new GDP using multiplicative factor model.

        Formula::

            growth_rate = base_growth
            tariff_factor = 1.0 - net_tariff_gdp_cost / gdp
            sanctions_factor = 1.0 - sanctions_damage
            war_factor = 1.0 - (active_war_zones * 0.02) - (infra_damage * 0.05)
            tech_factor = 1.0 + AI_LEVEL_TECH_FACTOR[ai_level]
            inflation_factor = 1.0 - (inflation_rate * 0.015)
            blockade_factor = 1.0 - (trade_disrupted_fraction * 0.4)
            new_gdp = old_gdp * (1 + growth_rate * product_of_factors)
        """
        c = self.ws.countries[country_id]
        eco = c["economic"]
        old_gdp = eco["gdp"]
        base_growth = eco["gdp_growth_rate"] / 100.0  # stored as percentage

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

        # Combined growth
        combined = (tariff_factor * sanctions_factor * war_factor
                    * tech_factor * inflation_factor * blockade_factor)
        effective_growth = base_growth * combined
        new_gdp = old_gdp * (1.0 + effective_growth)
        new_gdp = max(new_gdp, 0.01)  # Floor: GDP cannot go to zero

        growth_pct = effective_growth * 100.0

        self._log.append(
            f"  GDP {country_id}: {old_gdp:.2f} -> {new_gdp:.2f} "
            f"(growth {growth_pct:+.2f}%, factors: tariff={tariff_factor:.3f} "
            f"sanc={sanctions_factor:.3f} war={war_factor:.3f} "
            f"tech={tech_factor:.3f} infl={inflation_factor:.3f} "
            f"block={blockade_factor:.3f})"
        )

        return {
            "old_gdp": old_gdp,
            "new_gdp": new_gdp,
            "growth_pct": growth_pct,
            "base_growth": base_growth * 100.0,
            "tariff_factor": tariff_factor,
            "sanctions_factor": sanctions_factor,
            "war_factor": war_factor,
            "tech_factor": tech_factor,
            "inflation_factor": inflation_factor,
            "blockade_factor": blockade_factor,
        }

    # -----------------------------------------------------------------------
    # FORMULA 2: SANCTIONS IMPACT
    # -----------------------------------------------------------------------

    def calc_sanctions_impact(self, target_id: str) -> Tuple[float, Dict[str, float]]:
        """Calculate total sanctions damage to *target_id* and cost to each sanctioner.

        Formula::

            for each sanctioner:
                bilateral_weight = trade_weight[sanctioner][target]
                raw_impact = sanctions_level * bilateral_weight * 0.03
            coalition_coverage = sum(sanctioner trade weights)
            effectiveness = 1.0 if coverage >= 0.6 else 0.3
            total_damage = sum(raw_impacts) * effectiveness
            cost_to_sanctioner = sanctions_level * bilateral_weight * 0.012

        Returns (total_damage_fraction, {sanctioner_id: cost_fraction}).
        """
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
        total_damage = min(total_damage, 0.50)  # Cap at 50% GDP damage

        self._log.append(
            f"  Sanctions on {target_id}: damage={total_damage:.4f}, "
            f"coalition_coverage={coalition_coverage:.3f}, "
            f"effectiveness={'full' if effectiveness == 1.0 else 'weak'}"
        )
        return total_damage, costs

    # -----------------------------------------------------------------------
    # FORMULA 3: TARIFF IMPACT
    # -----------------------------------------------------------------------

    def calc_tariff_impact(self, country_id: str) -> dict:
        """Calculate net tariff impact on *country_id* (as imposer AND as target).

        Formula::

            for each tariff pair:
                trade_volume = bilateral_trade_weight * gdp
                tariff_cost_incoming = tariff_level * trade_weight * 0.04 * gdp
                revenue_collected = tariff_cost * 0.7
                net_gdp_cost = tariff_cost * 0.3
                rerouting = tariff_level * 0.15 (reduces impact over time)

        Returns dict with net cost and revenue.
        """
        tariffs = self.ws.bilateral.get("tariffs", {})
        tw = self.trade_weights
        c = self.ws.countries[country_id]
        gdp = c["economic"]["gdp"]

        total_cost_as_imposer = 0.0
        total_revenue_as_imposer = 0.0
        total_cost_as_target = 0.0

        # Cost as imposer: tariffs WE impose on others
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
            total_cost_as_imposer += net_cost
            total_revenue_as_imposer += revenue

        # Cost as target: tariffs OTHERS impose on us
        for imposer_id, targets in tariffs.items():
            if imposer_id == country_id:
                continue
            level = targets.get(country_id, 0)
            if level <= 0:
                continue
            bw = tw.get(imposer_id, {}).get(country_id, 0.0)
            imposer_gdp = self.ws.countries.get(imposer_id, {}).get("economic", {}).get("gdp", 1)
            cost_to_us = level * bw * 0.04 * imposer_gdp * 0.5  # partial pass-through
            rerouting = level * 0.15
            cost_to_us *= max(0.0, 1.0 - rerouting)
            total_cost_as_target += cost_to_us

        net_gdp_cost = total_cost_as_imposer + total_cost_as_target - total_revenue_as_imposer
        net_gdp_cost = max(net_gdp_cost, 0.0)

        self._log.append(
            f"  Tariffs {country_id}: imposer_cost={total_cost_as_imposer:.3f}, "
            f"revenue={total_revenue_as_imposer:.3f}, target_cost={total_cost_as_target:.3f}, "
            f"net_cost={net_gdp_cost:.3f}"
        )
        return {
            "cost_as_imposer": total_cost_as_imposer,
            "revenue_as_imposer": total_revenue_as_imposer,
            "cost_as_target": total_cost_as_target,
            "net_gdp_cost": net_gdp_cost,
        }

    # -----------------------------------------------------------------------
    # FORMULA 4: STABILITY  (1-10 scale)
    # -----------------------------------------------------------------------

    def calc_stability(self, country_id: str, events: dict) -> float:
        """Calculate new stability index.

        V2: Destabilization comes from ACTOR BEHAVIOR, not formula decay.
        Stable states have institutional inertia.  Peaceful non-sanctioned
        countries are much less volatile.  Autocracies suppress instability
        (at political support cost).
        """
        c = self.ws.countries[country_id]
        pol = c["political"]
        eco = c["economic"]
        old_stab = pol["stability"]
        delta = 0.0

        at_war = any(
            w.get("attacker") == country_id or w.get("defender") == country_id
            for w in self.ws.wars
        )
        under_heavy_sanctions = self._sanctions_level(country_id) >= 2

        # POSITIVE INERTIA: Stable states tend to stay stable (but don't grow forever)
        if old_stab >= 7 and old_stab < 9:
            delta += 0.15  # well-functioning states have institutional resilience
        elif old_stab >= 5 and old_stab < 7:
            delta += 0.1  # moderate states have some inertia

        # GDP GROWTH STABILIZES
        gdp_growth = eco.get("gdp_growth_rate", 0)
        # Store last_growth for reference
        eco["last_growth"] = gdp_growth
        if gdp_growth > 0:
            delta += min(gdp_growth * 0.3, 0.5)  # growing economy helps, capped
        elif gdp_growth < -2:
            delta += gdp_growth * 0.2  # recession destabilizes

        # SOCIAL SPENDING (maintains, doesn't just prevent decline)
        social_ratio = events.get("social_spending_ratio", 0.3)
        baseline = eco.get("social_spending_baseline", 0.30)
        if social_ratio >= baseline:
            delta += 0.2  # adequate spending maintains stability
        else:
            delta -= (baseline - social_ratio) * 3  # underspending hurts

        # WAR EFFECTS (only for countries AT WAR)
        if at_war:
            casualties = events.get("casualties", 0)
            delta -= casualties * 0.2  # each unit lost
            territory_lost = events.get("territory_lost", 0)
            delta -= territory_lost * 0.4
            territory_gained = events.get("territory_gained", 0)
            delta += territory_gained * 0.2
            war_tiredness = pol.get("war_tiredness", 0)
            delta -= war_tiredness * 0.05  # cumulative but gradual
            # Note: war tiredness is incremented by combat resolution and mobilization,
            # NOT here -- to avoid double-counting

        # SANCTIONS PAIN (proportional to actual economic damage)
        if under_heavy_sanctions:
            sanctions_gdp_hit = events.get("sanctions_gdp_impact",
                                           events.get("sanctions_pain", 0))
            gdp = eco["gdp"]
            if gdp > 0:
                sanctions_gdp_hit = sanctions_gdp_hit / gdp  # normalise
            delta -= abs(sanctions_gdp_hit) * 0.8  # significant but survivable

        # INFLATION (only severe inflation destabilizes)
        inflation = eco.get("inflation", 0)
        if inflation > 10:
            delta -= (inflation - 10) * 0.05  # only high inflation matters

        # MOBILIZATION
        mobilization = events.get("mobilization_level", 0)
        if mobilization > 0:
            delta -= mobilization * 0.15

        # PROPAGANDA BOOST (diminishing returns)
        propaganda = events.get("propaganda_boost", 0)
        delta += propaganda

        # FOR PEACEFUL, NON-SANCTIONED COUNTRIES: much less volatile
        if not at_war and not under_heavy_sanctions:
            # Only extreme events move stability
            if delta < 0:
                delta *= 0.25  # peaceful countries resist destabilization

        # AUTOCRACY RESILIENCE BONUS
        regime = pol.get("regime_type", c.get("regime_type", "democracy"))
        if regime == "autocracy":
            if delta < 0:
                delta *= 0.7  # autocracies are 30% more resilient to stability drops

        new_stab = _clamp(old_stab + delta, 1.0, 10.0)
        self._log.append(
            f"  Stability {country_id}: {old_stab:.1f} -> {new_stab:.1f} (delta={delta:+.2f})"
        )
        return round(new_stab, 2)

    def _sanctions_level(self, country_id: str) -> int:
        """Return the maximum sanctions level imposed on country_id by any actor."""
        sanctions = self.ws.bilateral.get("sanctions", {})
        max_level = 0
        for sanctioner, targets in sanctions.items():
            if sanctioner.startswith("_"):
                continue
            level = targets.get(country_id, 0)
            if level > max_level:
                max_level = level
        return max_level

    # -----------------------------------------------------------------------
    # FORMULA 5: POLITICAL SUPPORT  (0-100 scale)
    # -----------------------------------------------------------------------

    def calc_political_support(self, country_id: str, events: dict) -> float:
        """Calculate new political support, differentiated by regime type.

        Democracy::

            delta = (gdp_growth - 2.0) * 3
            delta -= casualties * 2
            delta += (stability - 5) * 2
            delta += election_proximity_modifier
            delta += rally_effect

        Autocracy::

            delta = (stability - 5) * 3
            delta -= perceived_weakness * 5
            delta += repression_effect
            delta += nationalist_rally
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
            delta += (gdp_growth - 2.0) * 1.5  # reduced from 3.0
            delta -= casualties * 2.0
            delta += (stability - 5.0) * 1.0  # reduced from 2.0
            election_mod = events.get("election_proximity_modifier", 0)
            delta += election_mod
            rally = events.get("rally_effect", 0)
            delta += rally
        else:  # autocracy, theocracy
            delta += (stability - 5.0) * 1.5  # reduced from 3.0
            weakness = events.get("perceived_weakness", 0)
            delta -= weakness * 5.0
            repression = events.get("repression_effect", 0)
            delta += repression
            nationalist = events.get("nationalist_rally", 0)
            delta += nationalist

        # Mean-reversion: extreme values tend to drift back toward center
        if old_sup > 70:
            delta -= (old_sup - 70) * 0.05  # high support erodes slightly
        elif old_sup < 30:
            delta += (30 - old_sup) * 0.05  # very low support gets slight bounce

        new_sup = _clamp(old_sup + delta, 0.0, 100.0)
        self._log.append(
            f"  Support {country_id} ({regime}): {old_sup:.1f} -> {new_sup:.1f} "
            f"(delta={delta:+.2f})"
        )
        return round(new_sup, 2)

    # -----------------------------------------------------------------------
    # FORMULA 6: OIL PRICE
    # -----------------------------------------------------------------------

    def calc_oil_price(self, opec_decisions: Dict[str, str],
                       disruptions: dict) -> float:
        """Calculate global oil price from OPEC+ production decisions and disruptions.

        V2: MORE responsive to crises.  High prices EXPLICITLY benefit producers.
        """
        base_price = 80.0

        # Supply factor from OPEC+ decisions
        supply_factor = 1.0
        for member, decision in opec_decisions.items():
            if decision == "low":
                supply_factor -= 0.05
            elif decision == "high":
                supply_factor += 0.05
        supply_factor = max(supply_factor, 0.5)

        # Disruption factor -- MUCH more responsive
        disruption = 1.0
        for cp_name, status in self.ws.chokepoint_status.items():
            if status != "blocked":
                continue
            if cp_name == "hormuz":
                disruption += 0.60  # 60% spike
            elif cp_name == "suez":
                disruption += 0.15
            elif cp_name == "malacca":
                disruption += 0.20
            else:
                disruption += 0.05

        # Demand factor from global GDP growth
        total_gdp = sum(c["economic"]["gdp"] for c in self.ws.countries.values())
        avg_growth = 0.0
        if total_gdp > 0:
            avg_growth = sum(
                c["economic"]["gdp"] * c["economic"]["gdp_growth_rate"] / 100.0
                for c in self.ws.countries.values()
            ) / total_gdp
        demand = 1.0 + (avg_growth - 2.0) * 0.1

        price = base_price * (demand / supply_factor) * disruption
        price = _clamp(price, 20.0, 300.0)

        # BENEFIT TO PRODUCERS: oil revenue = price * 15% of GDP base capacity
        for cid, country in self.ws.countries.items():
            if country["economic"].get("oil_producer"):
                oil_revenue = price * 0.15 * country["economic"]["gdp"] / 80.0
                country["economic"]["oil_revenue"] = round(oil_revenue, 2)

        self._log.append(
            f"  Oil price: ${price:.1f} (supply_factor={supply_factor:.2f}, "
            f"demand={demand:.3f}, disruption={disruption:.2f})"
        )
        return round(price, 2)

    # -----------------------------------------------------------------------
    # FORMULA 7: COMBAT RESOLUTION  (RISK dice model)
    # -----------------------------------------------------------------------

    def resolve_combat(self, attacker_id: str, defender_id: str,
                       zone_id: str, attacker_units: int,
                       defender_units: int,
                       modifiers: Optional[dict] = None) -> dict:
        """Resolve combat between two forces using RISK-style dice.

        Each pair rolls 1d6 + modifiers.  Defender wins ties.
        Returns dict with losses for each side.
        """
        if modifiers is None:
            modifiers = {}
        a_tech = modifiers.get("attacker_tech", 0)
        a_morale = modifiers.get("attacker_morale", 0)
        d_tech = modifiers.get("defender_tech", 0)
        d_morale = modifiers.get("defender_morale", 0)
        terrain = modifiers.get("terrain", 0)

        a_losses = 0
        d_losses = 0
        pairs = min(attacker_units, defender_units)

        for _ in range(pairs):
            a_roll = random.randint(1, 6) + a_tech + a_morale
            d_roll = random.randint(1, 6) + d_tech + d_morale + terrain
            if a_roll > d_roll:
                d_losses += 1
            else:
                a_losses += 1

        self._log.append(
            f"  Combat {zone_id}: {attacker_id}({attacker_units}) vs "
            f"{defender_id}({defender_units}) -> "
            f"attacker_losses={a_losses}, defender_losses={d_losses}"
        )
        return {
            "attacker": attacker_id,
            "defender": defender_id,
            "zone": zone_id,
            "attacker_units": attacker_units,
            "defender_units": defender_units,
            "attacker_losses": a_losses,
            "defender_losses": d_losses,
            "attacker_remaining": attacker_units - a_losses,
            "defender_remaining": defender_units - d_losses,
        }

    # -----------------------------------------------------------------------
    # FORMULA 11: TECH ADVANCEMENT
    # -----------------------------------------------------------------------

    def calc_tech_advancement(self, country_id: str,
                              rd_investment: dict) -> dict:
        """Advance R&D progress toward next tech level.

        Formula::

            progress += rd_investment_normalized
            if progress >= threshold[current_level]:
                level += 1
                progress = 0.0

        Investment is normalized: 1 coin of R&D per GDP adds ~0.05 progress.
        """
        c = self.ws.countries[country_id]
        tech = c["technology"]
        gdp = c["economic"]["gdp"]
        result = {"nuclear_levelup": False, "ai_levelup": False}

        # Nuclear R&D
        nuc_invest = rd_investment.get("nuclear", 0)
        if nuc_invest > 0 and gdp > 0:
            progress_add = (nuc_invest / max(gdp, 0.01)) * 0.5
            tech["nuclear_rd_progress"] += progress_add
        nuc_level = tech["nuclear_level"]
        nuc_threshold = NUCLEAR_RD_THRESHOLDS.get(nuc_level, 999.0)
        if tech["nuclear_rd_progress"] >= nuc_threshold and nuc_level < 3:
            tech["nuclear_level"] += 1
            tech["nuclear_rd_progress"] = 0.0
            result["nuclear_levelup"] = True
            self._log.append(f"  TECH BREAKTHROUGH: {country_id} nuclear -> L{tech['nuclear_level']}")

        # AI / Semiconductor R&D
        ai_invest = rd_investment.get("ai", 0)
        if ai_invest > 0 and gdp > 0:
            progress_add = (ai_invest / max(gdp, 0.01)) * 0.5
            tech["ai_rd_progress"] += progress_add
        ai_level = tech["ai_level"]
        ai_threshold = AI_RD_THRESHOLDS.get(ai_level, 999.0)
        if tech["ai_rd_progress"] >= ai_threshold and ai_level < 4:
            tech["ai_level"] += 1
            tech["ai_rd_progress"] = 0.0
            result["ai_levelup"] = True
            self._log.append(f"  TECH BREAKTHROUGH: {country_id} AI -> L{tech['ai_level']}")

        # Cathay strategic missile growth (+1/round if funded)
        mil = c["military"]
        if country_id == "cathay" and mil.get("strategic_missile_growth", 0) > 0:
            budget_data = {}  # simplified: Cathay always gets +1
            mil["strategic_missiles"] = mil.get("strategic_missiles", 0) + 1
            self._log.append(f"  Cathay strategic missile production: +1")

        return result

    # -----------------------------------------------------------------------
    # FORMULA 12: INFLATION
    # -----------------------------------------------------------------------

    def calc_inflation(self, country_id: str, money_printed: float,
                       previous_inflation: float) -> float:
        """Calculate new inflation rate.

        V2: Higher multiplier (60 vs 50), 3% GDP erosion per inflation point above 5%.
        """
        c = self.ws.countries[country_id]
        gdp = c["economic"]["gdp"]

        # Natural decay (15% per round)
        new_inflation = previous_inflation * 0.85
        if gdp > 0 and money_printed > 0:
            new_inflation += (money_printed / gdp) * 60.0  # was 50, now 60

        new_inflation = max(new_inflation, 0.0)
        new_inflation = min(new_inflation, 500.0)  # hard cap

        # Revenue erosion: 3% of GDP per inflation point above 5% (was 2%)
        excess_inflation = max(0, new_inflation - 5)
        revenue_erosion = excess_inflation * 0.03 * gdp
        c["economic"]["inflation_revenue_erosion"] = round(revenue_erosion, 2)

        self._log.append(
            f"  Inflation {country_id}: {previous_inflation:.1f}% -> {new_inflation:.1f}%"
        )
        return round(new_inflation, 2)

    # -----------------------------------------------------------------------
    # FORMULA 13: DEBT SERVICE
    # -----------------------------------------------------------------------

    def calc_debt_service(self, country_id: str, deficit: float) -> float:
        """Calculate new debt burden.

        Formula::

            if deficit > 0:
                new_debt_burden = old_debt_burden + deficit * 0.12
        """
        c = self.ws.countries[country_id]
        old_debt = c["economic"]["debt_burden"]
        new_debt = old_debt
        if deficit > 0:
            new_debt = old_debt + deficit * 0.12

        new_debt = max(new_debt, 0.0)
        self._log.append(
            f"  Debt {country_id}: {old_debt:.2f} -> {new_debt:.2f} (deficit={deficit:.2f})"
        )
        return round(new_debt, 2)

    # -----------------------------------------------------------------------
    # FORMULA: REVENUE
    # -----------------------------------------------------------------------

    def calc_revenue(self, country_id: str) -> float:
        """Calculate revenue available for next round.

        Formula::

            revenue = gdp * tax_rate
                    + oil_revenue (if producer)
                    - sanctions_cost
                    - inflation_erosion
                    - war_damage
                    - debt_burden
        """
        c = self.ws.countries[country_id]
        eco = c["economic"]
        gdp = eco["gdp"]
        tax_rate = eco["tax_rate"]

        base_rev = gdp * tax_rate

        # Oil revenue for producers
        oil_rev = 0.0
        if eco.get("oil_producer", False):
            oil_share = eco["sectors"].get("resources", 0) / 100.0
            oil_rev = gdp * oil_share * (self.ws.oil_price / 80.0 - 1.0) * 0.3
            oil_rev = max(oil_rev, 0.0)

        # Sanctions cost
        sanc_cost = 0.0
        sanctions = self.ws.bilateral.get("sanctions", {})
        for sanctioner, targets in sanctions.items():
            if sanctioner.startswith("_"):
                continue
            level = targets.get(country_id, 0)
            if level > 0:
                bw = self.trade_weights.get(sanctioner, {}).get(country_id, 0)
                sanc_cost += level * bw * 0.015 * gdp

        # Inflation erosion (use V2 inflation_revenue_erosion if available)
        inflation_erosion = eco.get("inflation_revenue_erosion",
                                    (eco["inflation"] / 100.0) * 0.03 * gdp)

        # War damage
        war_damage = self._get_infra_damage(country_id) * 0.02 * gdp

        # Debt burden
        debt = eco["debt_burden"]

        revenue = base_rev + oil_rev - sanc_cost - inflation_erosion - war_damage - debt
        revenue = max(revenue, 0.0)

        self._log.append(
            f"  Revenue {country_id}: {revenue:.2f} "
            f"(base={base_rev:.2f} oil={oil_rev:.2f} sanc_cost={sanc_cost:.2f} "
            f"infl_erosion={inflation_erosion:.2f} war={war_damage:.2f} debt={debt:.2f})"
        )
        return round(revenue, 2)

    # -----------------------------------------------------------------------
    # FORMULA: BUDGET EXECUTION
    # -----------------------------------------------------------------------

    def calc_budget_execution(self, country_id: str, budget: dict,
                              revenue: float) -> dict:
        """Execute the national budget.

        Order: mandatory costs first (maintenance, debt), then discretionary.
        If deficit: options are cut, print money, or draw reserves.
        """
        c = self.ws.countries[country_id]
        mil = c["military"]
        eco = c["economic"]

        # Mandatory: maintenance
        maint_rate = mil.get("maintenance_cost_per_unit", 0.3)
        total_units = sum(mil.get(ut, 0) for ut in
                         ["ground", "naval", "tactical_air", "strategic_missiles", "air_defense"])
        maintenance = total_units * maint_rate
        mandatory = maintenance + eco["debt_burden"]

        discretionary = max(revenue - mandatory, 0.0)

        # Budget allocation
        social = budget.get("social_spending", discretionary * 0.3)
        social = min(social, discretionary)
        military_budget = budget.get("military_total", discretionary * 0.3)
        military_budget = min(military_budget, discretionary - social)
        tech_budget = budget.get("tech_total", discretionary * 0.1)
        tech_budget = min(tech_budget, discretionary - social - military_budget)
        reserves_add = max(discretionary - social - military_budget - tech_budget, 0)

        eco["treasury"] += reserves_add
        surplus_deficit = revenue - mandatory - social - military_budget - tech_budget
        if surplus_deficit < 0:
            eco["treasury"] += surplus_deficit  # draw from reserves
            if eco["treasury"] < 0:
                eco["treasury"] = 0
                self._log.append(f"  CRISIS: {country_id} reserves exhausted!")

        result = {
            "revenue": revenue,
            "mandatory": mandatory,
            "maintenance": maintenance,
            "discretionary": discretionary,
            "social_spending": social,
            "military_budget": military_budget,
            "tech_budget": tech_budget,
            "reserves_added": reserves_add,
            "surplus_deficit": surplus_deficit,
            "new_treasury": eco["treasury"],
        }
        self._log.append(
            f"  Budget {country_id}: rev={revenue:.2f} maint={maintenance:.2f} "
            f"social={social:.2f} mil={military_budget:.2f} tech={tech_budget:.2f} "
            f"treasury={eco['treasury']:.2f}"
        )
        return result

    # -----------------------------------------------------------------------
    # FORMULA: MILITARY PRODUCTION
    # -----------------------------------------------------------------------

    def calc_military_production(self, country_id: str,
                                 military_alloc: dict) -> dict:
        """Produce military units based on budget allocation.

        Production tiers: normal (1x/1x), accelerated (2x cost/2x output),
        maximum (4x cost/3x output).
        """
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

            if unit_cost > 0:
                units = min(int(coins / unit_cost), int(max_cap))
            else:
                units = 0
            units = max(units, 0)

            mil[utype] = mil.get(utype, 0) + units
            produced[utype] = units

        self._log.append(
            f"  Production {country_id}: {produced}"
        )
        return produced

    # -----------------------------------------------------------------------
    # FORMULA 14: FINANCIAL CRISIS CHECK
    # -----------------------------------------------------------------------

    def check_financial_crisis(self, country_id: str) -> dict:
        """Check if a financial crisis is triggered.

        Market index proxy: gdp_growth + stability_contribution - inflation_drag.
        If index drops below crisis threshold, capital flight occurs.
        """
        c = self.ws.countries[country_id]
        eco = c["economic"]
        pol = c["political"]

        gdp_growth = eco["gdp_growth_rate"]
        stability = pol["stability"]
        inflation = eco["inflation"]

        # Synthetic market index (0-100 scale)
        market_index = 50.0 + gdp_growth * 5.0 + (stability - 5) * 5.0 - inflation * 0.5
        market_index = _clamp(market_index, 0.0, 100.0)

        crisis = False
        capital_flight = 0.0
        if market_index < 30.0:
            crisis = True
            severity = (30.0 - market_index) / 30.0  # 0 to 1
            capital_flight = severity * 0.10 * eco["gdp"]  # up to 10% GDP
            eco["gdp"] = max(eco["gdp"] - capital_flight, 0.01)
            eco["treasury"] = max(eco["treasury"] - capital_flight * 0.5, 0)
            self._log.append(
                f"  FINANCIAL CRISIS {country_id}: market_index={market_index:.1f}, "
                f"capital_flight={capital_flight:.2f}"
            )

        return {
            "market_index": round(market_index, 2),
            "crisis": crisis,
            "capital_flight": round(capital_flight, 2),
        }

    # -----------------------------------------------------------------------
    # FORMULA: ELECTION  (Columbia presidential, midterm)
    # -----------------------------------------------------------------------

    def calc_election(self, country_id: str, election_type: str,
                      votes: Optional[dict] = None) -> dict:
        """Calculate election outcome.

        AI vote share = 50% of outcome.
        AI factors: economic performance, stability, war outcomes, scandals.
        """
        c = self.ws.countries[country_id]
        eco = c["economic"]
        pol = c["political"]

        gdp_growth = eco["gdp_growth_rate"]
        stability = pol["stability"]

        # AI incumbent score
        economic_performance = gdp_growth * 10.0
        stability_factor = (stability - 5) * 5.0
        war_outcome = 0.0
        for war in self.ws.wars:
            if war.get("attacker") == country_id or war.get("defender") == country_id:
                war_outcome += -5.0  # being at war generally hurts
        scandal_factor = 0.0  # from covert ops exposure, etc.

        ai_score = 50.0 + economic_performance + stability_factor + war_outcome + scandal_factor
        ai_score = _clamp(ai_score, 0.0, 100.0)

        # Combine with player votes (50/50 split)
        if votes:
            player_incumbent_pct = votes.get("incumbent_pct", 50.0)
        else:
            player_incumbent_pct = 50.0

        final_incumbent = 0.5 * ai_score + 0.5 * player_incumbent_pct
        incumbent_wins = final_incumbent >= 50.0

        result = {
            "election_type": election_type,
            "ai_score": round(ai_score, 2),
            "player_score": player_incumbent_pct,
            "final_incumbent_pct": round(final_incumbent, 2),
            "incumbent_wins": incumbent_wins,
        }
        self._log.append(
            f"  Election {country_id} ({election_type}): incumbent={final_incumbent:.1f}% "
            f"-> {'WINS' if incumbent_wins else 'LOSES'}"
        )
        return result

    # -----------------------------------------------------------------------
    # FORMULA: COUP PROBABILITY
    # -----------------------------------------------------------------------

    def calc_coup_probability(self, country_id: str,
                              military_chief_opposed: bool = False) -> float:
        """Calculate probability of a successful coup.

        Formula::

            base = 0.05
            if stability < 5: base += (5 - stability) * 0.05
            if support < 40: base += (40 - support) / 100 * 0.15
            if military_chief_opposed: base += 0.10
        """
        c = self.ws.countries[country_id]
        pol = c["political"]
        stability = pol["stability"]
        support = pol["political_support"]

        prob = 0.05
        if stability < 5:
            prob += (5 - stability) * 0.05
        if support < 40:
            prob += (40 - support) / 100.0 * 0.15
        if military_chief_opposed:
            prob += 0.10
        prob = _clamp(prob, 0.0, 0.95)

        self._log.append(
            f"  Coup probability {country_id}: {prob:.2%} "
            f"(stab={stability}, sup={support}, chief_opposed={military_chief_opposed})"
        )
        return round(prob, 4)

    # -----------------------------------------------------------------------
    # PASS 2 — AI CONTEXTUAL ADJUSTMENT  (heuristic for test)
    # -----------------------------------------------------------------------

    def ai_contextual_adjustment(self, det_results: dict,
                                 actions: dict, round_num: int) -> dict:
        """Apply bounded heuristic adjustments simulating an expert panel.

        Rules:
        - Major war loss: GDP -5% to -15% (confidence shock)
        - Sanctions coalition expansion: additional -5% to target
        - Tech breakthrough: +5% GDP (market optimism)
        - Rally-around-flag: +10 support first engagement, diminishing
        - War fatigue acceleration: if war > 3 rounds, fatigue +50% faster
        - Capital flight: if stability < 4, additional -3% GDP

        All adjustments bounded at +/-30% of formula result.
        """
        adjustments: dict = {}

        for cid, c in self.ws.countries.items():
            adj_list = []
            eco = c["economic"]
            pol = c["political"]
            gdp = eco["gdp"]

            # --- Major war loss ---
            for combat in det_results.get("combat", []):
                if combat["defender"] == cid and combat["defender_remaining"] == 0:
                    pct = random.uniform(0.05, 0.15)
                    gdp_hit = gdp * pct
                    bounded = min(gdp_hit, gdp * 0.30)
                    eco["gdp"] = max(eco["gdp"] - bounded, 0.01)
                    adj_list.append({
                        "type": "war_loss_confidence_shock",
                        "gdp_adjustment": -bounded,
                        "justification": f"Market confidence collapses after major defeat in {combat['zone']}."
                    })

            # --- Sanctions coalition expansion ---
            # V2: reduced impact for countries that have adapted (autocracies at war for >2 rounds)
            sanc_data = det_results.get("sanctions", {}).get(cid, {})
            regime = pol.get("regime_type", c.get("regime_type", "democracy"))
            sanctions_adapted = regime == "autocracy" and pol.get("war_tiredness", 0) > 2
            if sanc_data.get("damage", 0) > 0.10:
                pct = 0.02 if sanctions_adapted else 0.05  # adapted countries feel less market panic
                additional = gdp * pct
                bounded = min(additional, gdp * 0.30)
                eco["gdp"] = max(eco["gdp"] - bounded, 0.01)
                adj_list.append({
                    "type": "sanctions_market_panic",
                    "gdp_adjustment": -bounded,
                    "justification": "Broad sanctions coalition triggers market panic and currency sell-off."
                                     + (" (adapted economy, reduced impact)" if sanctions_adapted else "")
                })

            # --- Tech breakthrough ---
            tech_res = det_results.get("tech", {}).get(cid, {})
            if tech_res.get("ai_levelup") or tech_res.get("nuclear_levelup"):
                boost = gdp * 0.05
                bounded = min(boost, gdp * 0.30)
                eco["gdp"] += bounded
                adj_list.append({
                    "type": "tech_breakthrough_optimism",
                    "gdp_adjustment": bounded,
                    "justification": "Technology breakthrough sparks investor confidence and market rally."
                })

            # --- Rally-around-flag ---
            at_war = any(
                w.get("attacker") == cid or w.get("defender") == cid
                for w in self.ws.wars
            )
            if at_war:
                war_duration = 0
                for w in self.ws.wars:
                    if w.get("attacker") == cid or w.get("defender") == cid:
                        start = w.get("start_round", 0)
                        if start < 0:
                            war_duration = round_num + abs(start)
                        else:
                            war_duration = max(round_num - start, 0)
                rally_bonus = max(10.0 - war_duration * 3.0, 0.0)
                if rally_bonus > 0:
                    bounded = min(rally_bonus, pol["political_support"] * 0.30)
                    pol["political_support"] = _clamp(
                        pol["political_support"] + bounded, 0, 100
                    )
                    adj_list.append({
                        "type": "rally_around_flag",
                        "support_adjustment": bounded,
                        "justification": f"Rally effect in year {war_duration} of conflict, diminishing."
                    })

            # --- War fatigue acceleration ---
            # V2: reduced acceleration, capped to prevent runaway
            if at_war:
                for w in self.ws.wars:
                    if w.get("attacker") == cid or w.get("defender") == cid:
                        start = w.get("start_round", 0)
                        if start < 0:
                            dur = round_num + abs(start)
                        else:
                            dur = max(round_num - start, 0)
                        if dur > 6:
                            # Only accelerate for very long wars, with diminishing effect
                            current_wt = pol.get("war_tiredness", 0)
                            extra_fatigue = min(current_wt * 0.03, 0.5)  # cap at 0.5
                            pol["war_tiredness"] = current_wt + extra_fatigue
                            adj_list.append({
                                "type": "war_fatigue_acceleration",
                                "fatigue_increase": extra_fatigue,
                                "justification": f"Prolonged war ({dur} rounds) accelerates public fatigue."
                            })

            # --- Capital flight if stability < 4 ---
            # V2: autocracies with capital controls experience less capital flight
            if pol["stability"] < 4:
                regime = pol.get("regime_type", c.get("regime_type", "democracy"))
                flight_pct = 0.01 if regime == "autocracy" else 0.03
                flight = gdp * flight_pct
                bounded = min(flight, gdp * 0.30)
                eco["gdp"] = max(eco["gdp"] - bounded, 0.01)
                adj_list.append({
                    "type": "capital_flight",
                    "gdp_adjustment": -bounded,
                    "justification": "Low stability triggers capital exodus."
                                     + (" (capital controls limit outflow)" if regime == "autocracy" else "")
                })

            if adj_list:
                adjustments[cid] = adj_list
                for adj in adj_list:
                    self._log.append(
                        f"  AI ADJ {cid}: {adj['type']} — {adj['justification']}"
                    )

        return adjustments

    # -----------------------------------------------------------------------
    # PASS 3 — COHERENCE CHECK
    # -----------------------------------------------------------------------

    def coherence_check(self, round_num: int) -> Tuple[List[str], str]:
        """Review world state for contradictions.  Generate narrative summary.
        Does NOT change numbers.

        Checks:
        - GDP < 0 (impossible)
        - Stability/support sharp divergence
        - Country at war with 0 military
        - Nuclear used without global stability shock
        """
        flags: List[str] = []

        for cid, c in self.ws.countries.items():
            eco = c["economic"]
            pol = c["political"]
            mil = c["military"]

            # GDP negativity
            if eco["gdp"] < 0:
                flags.append(f"IMPOSSIBLE: {cid} GDP is negative ({eco['gdp']})")

            # Stability/support divergence
            stab = pol["stability"]
            sup = pol["political_support"]
            if stab <= 2 and sup > 70:
                flags.append(
                    f"SUSPICIOUS: {cid} stability={stab} but support={sup} — "
                    f"check if rally effect is overriding structural crisis"
                )
            if stab >= 8 and sup < 20:
                flags.append(
                    f"UNUSUAL: {cid} stability={stab} but support={sup} — "
                    f"stable society with deeply unpopular leader"
                )

            # At war with zero military
            at_war = any(
                w.get("attacker") == cid or w.get("defender") == cid
                for w in self.ws.wars
            )
            total_mil = sum(mil.get(ut, 0) for ut in
                           ["ground", "naval", "tactical_air"])
            if at_war and total_mil == 0:
                flags.append(
                    f"CRITICAL: {cid} is at war but has 0 combat units — "
                    f"should trigger surrender or regime collapse"
                )

            # Nuclear check
            if self.ws.nuclear_used_this_sim:
                if stab > 6:
                    flags.append(
                        f"CHECK: Nuclear weapons used this sim but {cid} "
                        f"stability={stab} — global shock may be underrepresented"
                    )

        # --- Generate narrative ---
        narrative = self._generate_narrative(round_num)

        for flag in flags:
            self._log.append(f"  FLAG: {flag}")

        return flags, narrative

    # -----------------------------------------------------------------------
    # INTERNAL HELPERS
    # -----------------------------------------------------------------------

    def _apply_tariff_changes(self, changes: dict) -> None:
        """Apply tariff level changes from actions."""
        tariffs = self.ws.bilateral.setdefault("tariffs", {})
        for imposer, targets in changes.items():
            if imposer not in tariffs:
                tariffs[imposer] = {}
            for target, new_level in targets.items():
                tariffs[imposer][target] = _clamp(new_level, 0, 3)
                self._log.append(f"  Tariff: {imposer} -> {target} set to {new_level}")

    def _apply_sanction_changes(self, changes: dict) -> None:
        """Apply sanction level changes from actions."""
        sanctions = self.ws.bilateral.setdefault("sanctions", {})
        for imposer, targets in changes.items():
            if imposer not in sanctions:
                sanctions[imposer] = {}
            for target, new_level in targets.items():
                sanctions[imposer][target] = _clamp(new_level, -3, 3)
                self._log.append(f"  Sanctions: {imposer} -> {target} set to {new_level}")

    def _apply_opec_changes(self, changes: dict) -> None:
        """Apply OPEC production level changes."""
        for member, level in changes.items():
            if level in ("low", "normal", "high"):
                self.ws.opec_production[member] = level
                self._log.append(f"  OPEC: {member} production set to {level}")

    def _apply_blockades(self, blockades: list) -> None:
        """Apply blockade actions to chokepoints."""
        for b in blockades:
            zone = b.get("zone", "")
            country = b.get("country", "")
            for cp_name, cp_data in CHOKEPOINTS.items():
                if cp_data["zone"] == zone:
                    self.ws.chokepoint_status[cp_name] = "blocked"
                    self._log.append(f"  Blockade: {country} blocks {cp_name} ({zone})")

    def _resolve_combat_action(self, battle: dict) -> dict:
        """Resolve a combat action from the actions list."""
        attacker_id = battle.get("attacker", "")
        defender_id = battle.get("defender", "")
        zone_id = battle.get("zone", "")
        att_units = battle.get("units", 1)

        # Determine defender units from zone
        zone_forces = self.ws.zones.get(zone_id, {}).get("forces", {})
        def_forces = zone_forces.get(defender_id, {})
        def_units = def_forces.get("ground", 0)

        if def_units == 0:
            # Uncontested capture
            self._log.append(f"  Combat: {attacker_id} captures undefended {zone_id}")
            self._transfer_zone_control(zone_id, attacker_id, att_units)
            return {
                "attacker": attacker_id, "defender": defender_id,
                "zone": zone_id, "attacker_losses": 0, "defender_losses": 0,
                "attacker_remaining": att_units, "defender_remaining": 0,
                "zone_captured": True,
            }

        # Build modifiers
        modifiers = self._build_combat_modifiers(attacker_id, defender_id, zone_id)

        result = self.resolve_combat(
            attacker_id, defender_id, zone_id,
            att_units, def_units, modifiers
        )

        # Apply losses
        self._apply_combat_losses(attacker_id, defender_id, zone_id, result)

        # Determine zone control
        if result["defender_remaining"] <= 0 and result["attacker_remaining"] > 0:
            self._transfer_zone_control(zone_id, attacker_id, result["attacker_remaining"])
            result["zone_captured"] = True
        else:
            result["zone_captured"] = False

        # Update war tiredness
        att_country = self.ws.countries.get(attacker_id, {})
        def_country = self.ws.countries.get(defender_id, {})
        if att_country:
            att_country.setdefault("political", {})["war_tiredness"] = (
                att_country.get("political", {}).get("war_tiredness", 0) + 0.5
            )
        if def_country:
            def_country.setdefault("political", {})["war_tiredness"] = (
                def_country.get("political", {}).get("war_tiredness", 0) + 0.5
            )

        return result

    def _resolve_missile_strike(self, strike: dict) -> dict:
        """Resolve a strategic missile or tactical air strike."""
        country = strike.get("country", "")
        target_zone = strike.get("target_zone", "")
        warhead = strike.get("warhead", "conventional")
        c = self.ws.countries.get(country, {})
        mil = c.get("military", {})

        # Check if country has missiles
        if mil.get("strategic_missiles", 0) <= 0:
            self._log.append(f"  Strike FAILED: {country} has no strategic missiles")
            return {"success": False, "reason": "no_missiles"}

        # Consume missile
        mil["strategic_missiles"] -= 1

        # Air defense interception
        zone_forces = self.ws.zones.get(target_zone, {}).get("forces", {})
        total_ad = sum(
            f.get("air_defense", 0) for f in zone_forces.values()
            if f != zone_forces.get(country, {})
        )
        intercepted = False
        for _ in range(min(total_ad * 3, 5)):  # each AD unit blocks up to 3
            if random.random() < 0.3:
                intercepted = True
                break

        if intercepted:
            self._log.append(f"  Strike {country}->{target_zone}: INTERCEPTED by air defense")
            return {"success": False, "reason": "intercepted"}

        if warhead == "nuclear":
            self.ws.nuclear_used_this_sim = True
            nuc_level = c.get("technology", {}).get("nuclear_level", 0)
            if nuc_level >= 2:
                # Strategic nuclear
                for def_id, forces in zone_forces.items():
                    if def_id == country:
                        continue
                    for ut in ["ground", "naval", "tactical_air"]:
                        losses = int(forces.get(ut, 0) * 0.50)
                        forces[ut] = max(forces.get(ut, 0) - losses, 0)
                # Global stability shock
                for cid2 in self.ws.countries:
                    self.ws.countries[cid2]["political"]["stability"] = max(
                        self.ws.countries[cid2]["political"]["stability"] - 2, 1
                    )
                self._log.append(f"  NUCLEAR STRIKE (L2) {country}->{target_zone}: Devastating impact")
            else:
                # Tactical nuclear
                for def_id, forces in zone_forces.items():
                    if def_id == country:
                        continue
                    losses = int(forces.get("ground", 0) * 0.50)
                    forces["ground"] = max(forces.get("ground", 0) - losses, 0)
                self._log.append(f"  NUCLEAR STRIKE (L1) {country}->{target_zone}: Tactical impact")
        else:
            # Conventional
            for def_id, forces in zone_forces.items():
                if def_id == country:
                    continue
                losses = max(1, int(forces.get("ground", 0) * 0.1))
                forces["ground"] = max(forces.get("ground", 0) - losses, 0)
            self._log.append(f"  Missile strike (conventional) {country}->{target_zone}")

        return {"success": True, "warhead": warhead, "zone": target_zone}

    def _resolve_covert_op(self, op: dict) -> dict:
        """Resolve a covert operation."""
        op_type = op.get("type", "espionage")
        country = op.get("country", "")
        target = op.get("target", "")

        # Base success probability
        base_prob = {"espionage": 0.60, "sabotage": 0.45, "cyber": 0.50,
                     "disinformation": 0.55, "election_meddling": 0.40}
        prob = base_prob.get(op_type, 0.50)

        # AI level bonus
        ai_level = self.ws.countries.get(country, {}).get("technology", {}).get("ai_level", 0)
        prob += ai_level * 0.05

        success = random.random() < prob
        detected = random.random() < 0.40  # 40% base detection

        result = {"type": op_type, "country": country, "target": target,
                  "success": success, "detected": detected}

        if success and target in self.ws.countries:
            tc = self.ws.countries[target]
            if op_type == "sabotage":
                tc["economic"]["gdp"] = max(tc["economic"]["gdp"] * 0.98, 0.01)
            elif op_type == "cyber":
                tc["economic"]["gdp"] = max(tc["economic"]["gdp"] * 0.99, 0.01)
            elif op_type == "disinformation":
                tc["political"]["stability"] = max(tc["political"]["stability"] - 0.3, 1)
                tc["political"]["political_support"] = max(
                    tc["political"]["political_support"] - 2, 0
                )
            elif op_type == "election_meddling":
                tc["political"]["political_support"] = max(
                    tc["political"]["political_support"] - 3, 0
                )

        self._log.append(
            f"  Covert {op_type} by {country} on {target}: "
            f"{'SUCCESS' if success else 'FAILED'}, "
            f"{'DETECTED' if detected else 'undetected'}"
        )
        return result

    def _build_combat_modifiers(self, attacker_id: str, defender_id: str,
                                 zone_id: str) -> dict:
        """Build combat modifiers from tech, morale, terrain."""
        att_c = self.ws.countries.get(attacker_id, {})
        def_c = self.ws.countries.get(defender_id, {})

        att_ai = att_c.get("technology", {}).get("ai_level", 0)
        def_ai = def_c.get("technology", {}).get("ai_level", 0)

        att_stab = att_c.get("political", {}).get("stability", 5)
        def_stab = def_c.get("political", {}).get("stability", 5)
        att_morale = max((att_stab - 5) * 0.5, -2)
        def_morale = max((def_stab - 5) * 0.5, -2)

        # Terrain: defenders in home territory get bonus
        terrain = 0
        if zone_id.startswith("ee_") or zone_id.startswith("me_"):
            terrain = 1  # general defense bonus in theater zones
        if "capital" in zone_id or "core" in zone_id:
            terrain = 2  # capital/core defense bonus

        return {
            "attacker_tech": AI_LEVEL_COMBAT_BONUS.get(att_ai, 0),
            "attacker_morale": att_morale,
            "defender_tech": AI_LEVEL_COMBAT_BONUS.get(def_ai, 0),
            "defender_morale": def_morale,
            "terrain": terrain,
        }

    def _apply_combat_losses(self, attacker_id: str, defender_id: str,
                              zone_id: str, result: dict) -> None:
        """Apply combat losses to zone forces and country military totals."""
        zone = self.ws.zones.get(zone_id, {"forces": {}})
        forces = zone["forces"]

        # Attacker losses (from origin zone -- simplified: deducted from country total)
        att_mil = self.ws.countries.get(attacker_id, {}).get("military", {})
        att_mil["ground"] = max(att_mil.get("ground", 0) - result["attacker_losses"], 0)

        # Defender losses
        def_forces = forces.get(defender_id, {})
        def_forces["ground"] = max(def_forces.get("ground", 0) - result["defender_losses"], 0)
        def_mil = self.ws.countries.get(defender_id, {}).get("military", {})
        def_mil["ground"] = max(def_mil.get("ground", 0) - result["defender_losses"], 0)

    def _transfer_zone_control(self, zone_id: str, new_owner: str,
                                units: int) -> None:
        """Transfer control of a zone to a new owner."""
        zone = self.ws.zones.setdefault(zone_id, {"forces": {}})
        # Clear old forces
        zone["forces"] = {new_owner: {"ground": units}}
        self._log.append(f"  Zone {zone_id} captured by {new_owner} ({units} units)")

    def _apply_mobilization(self, country_id: str, level: str) -> None:
        """Apply mobilization — produces extra units at stability cost."""
        c = self.ws.countries[country_id]
        mil = c["military"]
        cap = mil.get("production_capacity", {})

        multiplier = {"partial": 0.5, "general": 1.0, "total": 2.0}.get(level, 0)
        stab_cost = {"partial": 0.5, "general": 1.0, "total": 2.0}.get(level, 0)

        mobilized = int(cap.get("ground", 0) * multiplier)
        mil["ground"] = mil.get("ground", 0) + mobilized
        c["political"]["stability"] = max(c["political"]["stability"] - stab_cost, 1)
        c["political"]["war_tiredness"] = c["political"].get("war_tiredness", 0) + stab_cost * 0.5

        self._log.append(
            f"  Mobilization {country_id} ({level}): +{mobilized} ground, "
            f"stability -{stab_cost}"
        )

    def _apply_propaganda(self, country_id: str, coins: float) -> None:
        """Apply propaganda campaign effect with diminishing returns."""
        c = self.ws.countries[country_id]
        pol = c["political"]
        gdp = c["economic"]["gdp"]

        # Diminishing returns: first coin/GDP is most effective
        if gdp > 0:
            intensity = coins / gdp
        else:
            intensity = coins
        boost = math.log1p(intensity * 100) * 3.0  # diminishing via log
        boost = min(boost, 10.0)

        pol["political_support"] = _clamp(pol["political_support"] + boost, 0, 100)
        self._log.append(
            f"  Propaganda {country_id}: spent {coins} coins, support +{boost:.1f}"
        )

    def _count_war_zones(self, country_id: str) -> int:
        """Count how many zones a country is actively fighting in."""
        count = 0
        for w in self.ws.wars:
            if w.get("attacker") == country_id or w.get("defender") == country_id:
                count += len(w.get("occupied_zones", []))
        return count

    def _get_infra_damage(self, country_id: str) -> float:
        """Estimate infrastructure damage from war zones and strikes.
        Returns a 0-1 fraction."""
        damage = 0.0
        for w in self.ws.wars:
            if w.get("defender") == country_id:
                damage += len(w.get("occupied_zones", [])) * 0.05
        return min(damage, 1.0)

    def _get_blockade_fraction(self, country_id: str) -> float:
        """Estimate fraction of trade disrupted by blockades."""
        frac = 0.0
        c = self.ws.countries.get(country_id, {})
        eco = c.get("economic", {})

        for cp_name, status in self.ws.chokepoint_status.items():
            if status != "blocked":
                continue
            impact = CHOKEPOINTS[cp_name].get("trade_impact",
                     CHOKEPOINTS[cp_name].get("oil_impact", 0.1))
            # Hormuz affects oil importers
            if cp_name == "hormuz" and not eco.get("oil_producer", False):
                frac += impact
            # Malacca affects Cathay especially
            elif cp_name == "malacca" and country_id == "cathay":
                frac += impact * 2.0
            # Taiwan strait affects formosa-dependent countries
            elif cp_name == "taiwan_strait":
                dep = eco.get("formosa_dependency", 0)
                frac += impact * dep
            else:
                frac += impact * 0.3  # general trade disruption
        return min(frac, 1.0)

    def _get_disruptions(self) -> dict:
        """Get chokepoint disruption flags for oil price calculation."""
        hormuz = 1 if self.ws.chokepoint_status.get("hormuz") == "blocked" else 0
        other = sum(
            1 for cp, status in self.ws.chokepoint_status.items()
            if status == "blocked" and cp != "hormuz"
        )
        return {"hormuz_blocked": hormuz, "other_disruptions": other}

    def _get_money_printed(self, country_id: str, actions: dict) -> float:
        """Get money printed by a country this round (from budget deficit financing)."""
        budget = actions.get("budgets", {}).get(country_id, {})
        return budget.get("money_printed", 0)

    def _get_deficit(self, country_id: str, actions: dict) -> float:
        """Get budget deficit for a country this round."""
        budget = actions.get("budgets", {}).get(country_id, {})
        return max(budget.get("deficit", 0), 0)

    def _collate_events(self, actions: dict, results: dict) -> Dict[str, dict]:
        """Collate events relevant to each country for stability/support calculations."""
        events: Dict[str, dict] = {}
        for cid in self.ws.countries:
            ev: dict = {
                "casualties": 0,
                "territory_lost": 0,
                "territory_gained": 0,
                "sanctions_pain": 0,
                "mobilization_level": 0,
                "social_spending_ratio": self.ws.countries[cid]["economic"]["social_spending_baseline"],
                "propaganda_boost": 0,
                "rally_effect": 0,
                "perceived_weakness": 0,
                "repression_effect": 0,
                "nationalist_rally": 0,
                "election_proximity_modifier": 0,
            }

            # Casualties from combat
            for combat in results.get("combat", []):
                if combat["attacker"] == cid:
                    ev["casualties"] += combat["attacker_losses"]
                if combat["defender"] == cid:
                    ev["casualties"] += combat["defender_losses"]
                # Territory changes
                if combat.get("zone_captured") and combat["attacker"] == cid:
                    ev["territory_gained"] += 1
                if combat.get("zone_captured") and combat["defender"] == cid:
                    ev["territory_lost"] += 1

            # Sanctions pain
            sanc = results.get("sanctions", {}).get(cid, {})
            ev["sanctions_pain"] = sanc.get("damage", 0) * self.ws.countries[cid]["economic"]["gdp"]

            # Mobilization
            mob = actions.get("mobilizations", {}).get(cid, None)
            if mob:
                ev["mobilization_level"] = {"partial": 1, "general": 2, "total": 3}.get(mob, 0)

            # Budget social spending
            budget = actions.get("budgets", {}).get(cid, {})
            if "social_spending_ratio" in budget:
                ev["social_spending_ratio"] = budget["social_spending_ratio"]

            # Propaganda
            prop_coins = actions.get("propaganda", {}).get(cid, 0)
            if prop_coins > 0:
                gdp = self.ws.countries[cid]["economic"]["gdp"]
                if gdp > 0:
                    ev["propaganda_boost"] = min(math.log1p(prop_coins / gdp * 100) * 0.5, 2.0)

            events[cid] = ev
        return events

    def _generate_narrative(self, round_num: int) -> str:
        """Generate a ~200-word narrative summary of the round."""
        lines = []
        lines.append(f"ROUND {round_num} WORLD BRIEFING")
        lines.append("=" * 40)

        # Global economy
        total_gdp = sum(c["economic"]["gdp"] for c in self.ws.countries.values())
        lines.append(f"\nGlobal GDP: {total_gdp:.1f} coins. Oil price: ${self.ws.oil_price:.0f}/barrel.")

        # Wars
        if self.ws.wars:
            lines.append("\nACTIVE CONFLICTS:")
            for w in self.ws.wars:
                lines.append(f"  {w['attacker']} vs {w['defender']} in {w.get('theater', 'unknown')}")

        # Top economies
        sorted_c = sorted(self.ws.countries.items(),
                          key=lambda x: x[1]["economic"]["gdp"], reverse=True)
        lines.append("\nTOP ECONOMIES:")
        for cid, c in sorted_c[:5]:
            lines.append(
                f"  {c.get('sim_name', cid)}: GDP {c['economic']['gdp']:.1f}, "
                f"growth {c['economic']['gdp_growth_rate']:.1f}%, "
                f"stability {c['political']['stability']:.0f}/10"
            )

        # Crises
        lines.append("\nKEY INDICATORS:")
        for cid, c in self.ws.countries.items():
            stab = c["political"]["stability"]
            if stab <= 4:
                lines.append(f"  WARNING: {c.get('sim_name', cid)} stability critical ({stab}/10)")
            if c["economic"]["inflation"] > 20:
                lines.append(
                    f"  WARNING: {c.get('sim_name', cid)} inflation at {c['economic']['inflation']:.0f}%"
                )

        # Blocked chokepoints
        blocked = [cp for cp, s in self.ws.chokepoint_status.items() if s == "blocked"]
        if blocked:
            lines.append(f"\nBLOCKED CHOKEPOINTS: {', '.join(blocked)}")

        # Tech breakthroughs
        for cid, c in self.ws.countries.items():
            tech = c["technology"]
            if tech["ai_level"] >= 3:
                lines.append(f"  {c.get('sim_name', cid)} maintains AI Level {tech['ai_level']}")

        narrative = "\n".join(lines)
        # Trim to ~200 words
        words = narrative.split()
        if len(words) > 250:
            narrative = " ".join(words[:250]) + "..."
        return narrative


# ---------------------------------------------------------------------------
# UTILITY FUNCTIONS
# ---------------------------------------------------------------------------

def _clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value to [min_val, max_val]."""
    return max(min_val, min(max_val, value))


# ---------------------------------------------------------------------------
# CONVENIENCE: Run a quick sanity test if executed directly
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Loading starting state...")
    ws = load_starting_state()
    print(f"Loaded {len(ws.countries)} countries, {len(ws.zones)} zones, "
          f"{len(ws.deployments)} deployments")

    engine = TTTEngine(ws)

    # Minimal action set: just process with defaults
    actions = {
        "budgets": {},
        "tariff_changes": {},
        "sanction_changes": {},
        "opec_production": {"solaria": "normal", "nordostan": "normal",
                            "persia": "normal", "mirage": "normal"},
        "combat": [
            {"attacker": "nordostan", "defender": "heartland",
             "zone": "ee_east_front_north", "units": 3}
        ],
        "blockades": [],
        "missile_strikes": [],
        "covert_ops": [],
        "propaganda": {},
        "tech_rd": {},
        "mobilizations": {},
    }

    print("\nProcessing Round 1...")
    new_ws, report = engine.process_round(actions, round_num=1)

    print(f"\n--- ROUND REPORT ---")
    print(f"Oil price: ${new_ws.oil_price:.0f}")
    print(f"Coherence flags: {len(report['coherence_flags'])}")
    for flag in report["coherence_flags"]:
        print(f"  ! {flag}")

    print(f"\nCountry summaries:")
    for cid in ["columbia", "cathay", "nordostan", "heartland", "persia"]:
        c = new_ws.countries[cid]
        print(f"  {c['sim_name']:12s}: GDP={c['economic']['gdp']:7.1f}  "
              f"Growth={c['economic']['gdp_growth_rate']:+5.1f}%  "
              f"Stab={c['political']['stability']:.1f}  "
              f"Sup={c['political']['political_support']:.0f}%  "
              f"Infl={c['economic']['inflation']:.1f}%")

    print(f"\n--- NARRATIVE ---")
    print(report["narrative"])
    print("\nEngine test complete.")
