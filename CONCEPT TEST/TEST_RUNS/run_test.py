#!/usr/bin/env python3
"""
TTT Concept Test Runner -- Runs AI-driven simulation for 6-8 rounds.
=====================================================================
Each of 20 countries is controlled by a CountryAI agent that makes strategic
decisions based on its profile, the current world state, and memory of past
rounds.  The engine processes all actions simultaneously each round.

Usage:
    python3 run_test.py [run_name] [seed] [num_rounds]
    python3 run_test.py run_1 42 6

Author: ARIA (AI Participant Designer) + ATLAS (Engine Integration)
"""

import sys
import os
import json
import random
import copy
import math
from typing import Dict, List, Optional, Any, Tuple

# ---------------------------------------------------------------------------
# Engine import
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ENGINE'))
from engine import TTTEngine, WorldState, load_starting_state

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

WESTERN_ALLIANCE = {"columbia", "albion", "teutonia", "gallia", "freeland", "ponte", "phrygia"}
WESTERN_PARTNERS = {"yamato", "hanguk"}
COLUMBIA_BLOC = WESTERN_ALLIANCE | WESTERN_PARTNERS | {"levantia", "formosa"}
CATHAY_BLOC = {"cathay", "nordostan", "persia", "caribe", "choson"}
OPEC_MEMBERS = {"solaria", "nordostan", "persia", "mirage"}
LEAGUE_MEMBERS = {"cathay", "nordostan", "bharata", "solaria", "persia", "mirage"}

# Eastern Europe theater front-line zones and who occupies them at start
EE_FRONT_ZONES = [
    "ee_east_front_north", "ee_east_front_central",
    "ee_east_front_south", "ee_occupied_south", "ee_crimea_naval"
]
EE_HEARTLAND_ZONES = [
    "ee_capital", "ee_central_ukr", "ee_south_ukr",
    "ee_dnipro_line", "ee_kherson", "ee_west_ukr", "ee_southwest", "ee_west_border"
]
EE_NORDOSTAN_ZONES = ["ee_belarus", "ee_nord_border"]

ROUND_DATES = {
    0: "Q1 2026 (Baseline)",
    1: "H2 2026",
    2: "H1 2027",
    3: "H2 2027",
    4: "H1 2028",
    5: "H2 2028",
    6: "H1 2029",
    7: "H2 2029",
    8: "H1 2030",
}


# ---------------------------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------------------------

def get_round_date(round_num: int) -> str:
    return ROUND_DATES.get(round_num, f"Round {round_num}")


def load_country_profiles() -> Dict[str, dict]:
    """Load AI decision profiles from country_profiles.json."""
    profile_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "country_profiles.json")
    with open(profile_path, "r") as f:
        data = json.load(f)
    profiles = {}
    for p in data.get("profiles", []):
        profiles[p["country_id"]] = p
    return profiles


def get_country_summary(ws: WorldState, country_id: str) -> dict:
    """Return a brief status snapshot for a country."""
    c = ws.countries.get(country_id, {})
    eco = c.get("economic", {})
    pol = c.get("political", {})
    mil = c.get("military", {})
    tech = c.get("technology", {})
    total_mil = sum(mil.get(ut, 0) for ut in ["ground", "naval", "tactical_air"])
    return {
        "gdp": eco.get("gdp", 0),
        "growth": eco.get("gdp_growth_rate", 0),
        "treasury": eco.get("treasury", 0),
        "inflation": eco.get("inflation", 0),
        "debt": eco.get("debt_burden", 0),
        "stability": pol.get("stability", 5),
        "support": pol.get("political_support", 50),
        "war_tiredness": pol.get("war_tiredness", 0),
        "total_military": total_mil,
        "ground": mil.get("ground", 0),
        "naval": mil.get("naval", 0),
        "air": mil.get("tactical_air", 0),
        "nukes": mil.get("strategic_missiles", 0),
        "nuclear_level": tech.get("nuclear_level", 0),
        "ai_level": tech.get("ai_level", 0),
    }


def save_round(run_dir: str, round_num: int, world_state: WorldState,
               actions: dict, report: dict) -> None:
    """Save round data as JSON files."""
    round_dir = os.path.join(run_dir, f"round_{round_num}")
    os.makedirs(round_dir, exist_ok=True)

    with open(os.path.join(round_dir, "world_state.json"), "w") as f:
        json.dump(world_state.to_dict(), f, indent=2, default=str)

    if actions:
        with open(os.path.join(round_dir, "actions.json"), "w") as f:
            json.dump(actions, f, indent=2, default=str)

    if report:
        with open(os.path.join(round_dir, "report.json"), "w") as f:
            json.dump(report, f, indent=2, default=str)


def print_round_summary(ws: WorldState, report: dict, round_num: int) -> None:
    """Print key metrics for the round."""
    print(f"\n--- Round {round_num} Summary ({get_round_date(round_num)}) ---")
    print(f"Oil price: ${ws.oil_price:.0f}/barrel")

    # Top 5 economies
    sorted_c = sorted(ws.countries.items(),
                      key=lambda x: x[1]["economic"]["gdp"], reverse=True)
    print("\nTop economies:")
    for cid, c in sorted_c[:5]:
        eco = c["economic"]
        pol = c["political"]
        print(f"  {c.get('sim_name', cid):12s}: GDP {eco['gdp']:6.1f}  "
              f"growth {eco['gdp_growth_rate']:+5.1f}%  "
              f"stab {pol['stability']:.0f}/10  "
              f"support {pol['political_support']:.0f}%")

    # Wars
    if ws.wars:
        print("\nActive wars:")
        for w in ws.wars:
            print(f"  {w['attacker']} vs {w['defender']} "
                  f"(theater: {w.get('theater', '?')}, "
                  f"occupied: {len(w.get('occupied_zones', []))} zones)")

    # Crisis alerts
    for cid, c in ws.countries.items():
        stab = c["political"]["stability"]
        if stab <= 3:
            print(f"  CRISIS: {c.get('sim_name', cid)} stability at {stab}/10!")

    # Chokepoints
    blocked = [cp for cp, s in ws.chokepoint_status.items() if s == "blocked"]
    if blocked:
        print(f"\nBlocked chokepoints: {', '.join(blocked)}")

    # Combat results
    combat_results = report.get("deterministic_results", {}).get("combat", [])
    if combat_results:
        print("\nCombat results:")
        for cr in combat_results:
            captured = " [CAPTURED]" if cr.get("zone_captured") else ""
            print(f"  {cr['attacker']} vs {cr['defender']} at {cr['zone']}: "
                  f"losses {cr['attacker_losses']}/{cr['defender_losses']}{captured}")

    # Narrative excerpt
    narrative = report.get("narrative", "")
    if narrative:
        lines = narrative.split("\n")
        for line in lines[:3]:
            if line.strip():
                print(f"  {line.strip()}")


def check_scheduled_events(round_num: int, ws: WorldState) -> List[dict]:
    """Return scheduled events for this round."""
    events = []
    if round_num == 2:
        events.append({
            "type": "election",
            "country": "columbia",
            "election_type": "midterm",
            "description": "Columbia midterm elections"
        })
    if round_num == 3:
        events.append({
            "type": "unga_vote",
            "description": "UN General Assembly vote on Heartland ceasefire resolution"
        })
    if round_num in (3, 4):
        # Heartland wartime election if stability > 3
        hl = ws.countries.get("heartland", {})
        if hl.get("political", {}).get("stability", 0) > 3:
            events.append({
                "type": "election",
                "country": "heartland",
                "election_type": "wartime_presidential",
                "description": "Heartland wartime presidential election"
            })
    if round_num == 5:
        events.append({
            "type": "election",
            "country": "columbia",
            "election_type": "presidential",
            "description": "Columbia presidential election"
        })
    return events


def process_events(events: List[dict], ws: WorldState, engine: TTTEngine,
                   round_num: int) -> None:
    """Process scheduled events and modify world state."""
    for ev in events:
        if ev["type"] == "election":
            cid = ev["country"]
            result = engine.calc_election(cid, ev["election_type"])
            print(f"\n  ELECTION: {ev['description']}")
            print(f"    Incumbent score: {result['final_incumbent_pct']:.1f}%")
            print(f"    Result: {'INCUMBENT WINS' if result['incumbent_wins'] else 'INCUMBENT LOSES'}")

            if not result["incumbent_wins"]:
                # Policy shift on leadership change
                c = ws.countries[cid]
                if cid == "columbia":
                    # New administration may shift priorities
                    c["political"]["political_support"] = 52.0
                elif cid == "heartland":
                    c["political"]["political_support"] = 50.0

        elif ev["type"] == "unga_vote":
            print(f"\n  UNGA VOTE: {ev['description']}")
            # Count votes based on alignment
            yes_votes = 0
            no_votes = 0
            abstain = 0
            for cid in ws.countries:
                if cid in CATHAY_BLOC:
                    no_votes += 1
                elif cid in COLUMBIA_BLOC:
                    yes_votes += 1
                elif cid == "bharata":
                    abstain += 1
                else:
                    # Small states follow economic interests
                    if random.random() < 0.6:
                        yes_votes += 1
                    else:
                        abstain += 1
            print(f"    Yes: {yes_votes}, No: {no_votes}, Abstain: {abstain}")
            print(f"    Result: {'PASSES' if yes_votes > no_votes else 'FAILS'} "
                  f"(non-binding, vetoed in Security Council by Cathay/Nordostan)")


def generate_analysis(run_dir: str, final_state: WorldState,
                      num_rounds: int) -> dict:
    """Generate final analysis answering the three core test questions."""
    analysis = {
        "run_dir": run_dir,
        "total_rounds": num_rounds,
        "test_questions": {},
        "final_state_summary": {},
    }

    # Question 1: Does the Thucydides Trap dynamic emerge?
    columbia = final_state.countries["columbia"]
    cathay = final_state.countries["cathay"]
    col_gdp = columbia["economic"]["gdp"]
    cat_gdp = cathay["economic"]["gdp"]
    gap_ratio = cat_gdp / max(col_gdp, 0.01)

    formosa_crisis = any(
        final_state.chokepoint_status.get("taiwan_strait") == "blocked"
        for _ in [1]
    )
    new_wars = [w for w in final_state.wars
                if w.get("attacker") in ("columbia", "cathay")
                or w.get("defender") in ("columbia", "cathay")]

    analysis["test_questions"]["thucydides_trap"] = {
        "gdp_gap_ratio": round(gap_ratio, 3),
        "columbia_gdp": round(col_gdp, 1),
        "cathay_gdp": round(cat_gdp, 1),
        "direct_conflict": len(new_wars) > 0,
        "formosa_crisis": formosa_crisis,
        "assessment": (
            "HIGH RISK" if len(new_wars) > 0 or formosa_crisis
            else "ELEVATED" if gap_ratio > 0.8
            else "MODERATE" if gap_ratio > 0.6
            else "LOW"
        ),
    }

    # Question 2: Do alliance systems hold or fracture?
    nato_members_stable = all(
        final_state.countries[cid]["political"]["stability"] >= 5
        for cid in ["columbia", "albion", "teutonia", "gallia", "freeland", "ponte"]
        if cid in final_state.countries
    )
    analysis["test_questions"]["alliance_cohesion"] = {
        "nato_stable": nato_members_stable,
        "weakest_link": min(
            ["columbia", "albion", "teutonia", "gallia", "freeland", "ponte", "phrygia"],
            key=lambda c: final_state.countries[c]["political"]["stability"]
        ),
        "assessment": "HOLDING" if nato_members_stable else "FRACTURING",
    }

    # Question 3: Does the Nordostan-Heartland war resolve?
    ee_war = None
    for w in final_state.wars:
        if w.get("attacker") == "nordostan" and w.get("defender") == "heartland":
            ee_war = w
    nor = final_state.countries["nordostan"]
    hl = final_state.countries["heartland"]

    if ee_war is None:
        war_status = "RESOLVED"
    elif nor["political"]["stability"] <= 2 or hl["political"]["stability"] <= 2:
        war_status = "COLLAPSE_IMMINENT"
    elif nor["political"]["war_tiredness"] > 8 and hl["political"]["war_tiredness"] > 8:
        war_status = "MUTUAL_EXHAUSTION"
    else:
        war_status = "ONGOING"

    analysis["test_questions"]["eastern_europe_war"] = {
        "status": war_status,
        "nordostan_stability": nor["political"]["stability"],
        "heartland_stability": hl["political"]["stability"],
        "nordostan_war_tiredness": nor["political"]["war_tiredness"],
        "heartland_war_tiredness": hl["political"]["war_tiredness"],
        "occupied_zones": ee_war.get("occupied_zones", []) if ee_war else [],
    }

    # Final state summary for all countries
    for cid, c in final_state.countries.items():
        analysis["final_state_summary"][cid] = get_country_summary(final_state, cid)

    return analysis


def save_analysis(run_dir: str, analysis: dict) -> None:
    """Save the final analysis to disk."""
    path = os.path.join(run_dir, "analysis.json")
    with open(path, "w") as f:
        json.dump(analysis, f, indent=2, default=str)
    print(f"\nAnalysis saved to {path}")


# ---------------------------------------------------------------------------
# COUNTRY AI
# ---------------------------------------------------------------------------

class CountryAI:
    """AI decision-maker for a single country."""

    def __init__(self, country_id: str, profile: dict, world_state: WorldState):
        self.country_id = country_id
        self.profile = profile
        self.memory: List[dict] = []
        self.risk_tolerance = profile.get("risk_tolerance", 0.5)
        self.aggression = profile.get("aggression", 0.3)
        self.cooperation_bias = profile.get("cooperation_bias", 0.5)

    # -------------------------------------------------------------------
    # MAIN DELIBERATION
    # -------------------------------------------------------------------

    def deliberate(self, world_state: WorldState, round_num: int) -> dict:
        """Analyze situation and produce all actions for this round."""
        country = world_state.countries[self.country_id]
        eco = country["economic"]
        pol = country["political"]
        mil = country["military"]
        tech = country["technology"]

        # Compute situational awareness
        at_war = self._is_at_war(world_state)
        revenue = self._estimate_revenue(country)
        total_units = sum(mil.get(ut, 0) for ut in
                         ["ground", "naval", "tactical_air", "strategic_missiles", "air_defense"])
        maintenance = total_units * mil.get("maintenance_cost_per_unit", 0.3)
        discretionary = max(revenue - maintenance - eco.get("debt_burden", 0), 0)

        # Collect all actions
        actions = {}
        actions["budget"] = self.decide_budget(country, world_state, round_num,
                                                discretionary, at_war)
        actions["tariffs"] = self.decide_tariffs(country, world_state, round_num)
        actions["sanctions"] = self.decide_sanctions(country, world_state, round_num)
        actions["military"] = self.decide_military(country, world_state, round_num)
        if self.country_id in OPEC_MEMBERS:
            actions["opec_production"] = self.decide_opec(country, world_state)
        actions["diplomatic"] = self.decide_diplomatic(country, world_state, round_num)
        actions["tech"] = self.decide_tech(country, world_state, discretionary)

        return actions

    # -------------------------------------------------------------------
    # BUDGET DECISIONS
    # -------------------------------------------------------------------

    def decide_budget(self, country: dict, ws: WorldState, round_num: int,
                      discretionary: float, at_war: bool) -> dict:
        """Allocate budget across social, military, tech, and reserves."""
        eco = country["economic"]
        pol = country["political"]
        weights = self.profile.get("decision_weights", {})

        # Base allocation ratios
        social_ratio = 0.30
        military_ratio = 0.30
        tech_ratio = 0.15
        reserve_ratio = 0.25

        # War adjustment: countries at war prioritize military
        if at_war:
            military_ratio += 0.20
            social_ratio -= 0.05
            reserve_ratio -= 0.10
            tech_ratio -= 0.05

        # Low stability: increase social spending
        if pol["stability"] <= 5:
            social_ratio += 0.10
            military_ratio -= 0.05
            reserve_ratio -= 0.05

        # Rich countries invest more in tech
        if eco["gdp"] > 30 and not at_war:
            tech_ratio += 0.10
            military_ratio -= 0.05
            reserve_ratio -= 0.05

        # Election proximity: boost social spending for democracies
        regime = pol.get("regime_type", country.get("regime_type", "democracy"))
        if regime == "democracy" and round_num in (2, 5):
            social_ratio += 0.10
            reserve_ratio -= 0.10

        # Economic crisis: cut everything, save reserves
        if eco["inflation"] > 20 or eco["debt_burden"] > 6:
            reserve_ratio += 0.15
            military_ratio -= 0.10
            tech_ratio -= 0.05

        # Profile-driven adjustments
        mil_weight = weights.get("military_security", weights.get("military_buildup",
                                  weights.get("military_defense", 0.2)))
        econ_weight = weights.get("economic_growth", weights.get("economic_stability", 0.2))
        military_ratio += (mil_weight - 0.2) * 0.5
        social_ratio += (econ_weight - 0.2) * 0.3

        # Normalize
        total = social_ratio + military_ratio + tech_ratio + reserve_ratio
        if total > 0:
            social_ratio /= total
            military_ratio /= total
            tech_ratio /= total
            reserve_ratio /= total

        social = discretionary * social_ratio
        military_total = discretionary * military_ratio
        tech_total = discretionary * tech_ratio

        # Social spending ratio for stability calc
        baseline = eco.get("social_spending_baseline", 0.25)
        gdp = max(eco["gdp"], 0.01)
        social_spending_ratio = baseline + (social / gdp - baseline) * 0.5

        return {
            "social_spending": round(social, 2),
            "military_total": round(military_total, 2),
            "tech_total": round(tech_total, 2),
            "social_spending_ratio": round(social_spending_ratio, 3),
            "money_printed": round(max(-discretionary * 0.1, 0), 2) if discretionary < 1 else 0,
            "deficit": round(max(-discretionary, 0), 2),
            "military": self._allocate_military_production(country, military_total),
        }

    def _allocate_military_production(self, country: dict, budget: float) -> dict:
        """Distribute military budget across unit types."""
        mil = country["military"]
        cap = mil.get("production_capacity", {})
        costs = mil.get("production_costs", {})
        at_war = self._is_at_war_country(country)

        alloc = {}
        if budget <= 0:
            for ut in ["ground", "naval", "tactical_air"]:
                alloc[ut] = {"coins": 0, "tier": "normal"}
            return alloc

        # War: focus on ground
        if at_war:
            ground_share = 0.60
            naval_share = 0.10
            air_share = 0.30
        elif self.country_id in ("columbia", "cathay", "yamato", "albion"):
            # Naval powers
            ground_share = 0.25
            naval_share = 0.40
            air_share = 0.35
        else:
            ground_share = 0.40
            naval_share = 0.20
            air_share = 0.40

        for ut, share in [("ground", ground_share), ("naval", naval_share),
                          ("tactical_air", air_share)]:
            coins = budget * share
            tier = "normal"
            if at_war and ut == "ground" and self.aggression > 0.5:
                tier = "accelerated"
            alloc[ut] = {"coins": round(coins, 2), "tier": tier}

        return alloc

    # -------------------------------------------------------------------
    # TARIFF DECISIONS
    # -------------------------------------------------------------------

    def decide_tariffs(self, country: dict, ws: WorldState, round_num: int) -> dict:
        """Decide tariff adjustments based on strategic relationships."""
        tariff_changes = {}
        current_tariffs = ws.bilateral.get("tariffs", {}).get(self.country_id, {})
        rels = self.profile.get("key_relationships", {})

        for target_id in ws.countries:
            if target_id == self.country_id:
                continue

            current = current_tariffs.get(target_id, 0)
            rel_desc = rels.get(target_id, "")

            # Tit-for-tat: if they raised tariffs on us, consider raising ours
            their_tariffs = ws.bilateral.get("tariffs", {}).get(target_id, {})
            they_tariff_us = their_tariffs.get(self.country_id, 0)

            new_level = current

            # Adversary descriptors trigger higher tariffs
            if any(word in rel_desc.lower() for word in
                   ["adversary", "enemy", "rival", "threat", "competitor"]):
                if current < 2:
                    new_level = min(current + 1, 3)
                # Retaliatory escalation
                if they_tariff_us > current:
                    new_level = min(they_tariff_us, 3)

            # Ally descriptors trigger lower tariffs
            elif any(word in rel_desc.lower() for word in
                     ["ally", "partner", "friend", "protector"]):
                if current > 0:
                    new_level = max(current - 1, 0)

            # Economic pressure: reduce tariffs if GDP is shrinking
            if country["economic"]["gdp_growth_rate"] < 0 and current > 1:
                new_level = max(new_level - 1, 0)

            # Columbia bloc: coordinate tariffs on Cathay
            if (self.country_id in COLUMBIA_BLOC and target_id == "cathay"
                    and round_num >= 2):
                col_tariff = ws.bilateral.get("tariffs", {}).get("columbia", {}).get("cathay", 0)
                if col_tariff >= 2 and current < 1:
                    new_level = 1  # Alliance pressure

            if new_level != current:
                tariff_changes[target_id] = new_level

        return tariff_changes

    # -------------------------------------------------------------------
    # SANCTIONS DECISIONS
    # -------------------------------------------------------------------

    def decide_sanctions(self, country: dict, ws: WorldState, round_num: int) -> dict:
        """Decide sanctions adjustments."""
        sanction_changes = {}
        current_sanctions = ws.bilateral.get("sanctions", {}).get(self.country_id, {})
        rels = self.profile.get("key_relationships", {})

        for target_id in ws.countries:
            if target_id == self.country_id:
                continue

            current = current_sanctions.get(target_id, 0)
            rel_desc = rels.get(target_id, "")

            new_level = current

            # Follow Columbia sanctions lead for western allies
            if self.country_id in WESTERN_ALLIANCE and self.country_id != "columbia":
                col_sanctions = ws.bilateral.get("sanctions", {}).get("columbia", {})
                for target, col_level in col_sanctions.items():
                    if target == target_id and col_level > 0:
                        # Willing to follow but may lag
                        willingness = self.cooperation_bias
                        # Teutonia resists China sanctions due to trade exposure
                        if self.country_id == "teutonia" and target_id == "cathay":
                            willingness *= 0.3
                        if self.country_id == "ponte" and target_id in CATHAY_BLOC:
                            willingness *= 0.5
                        if random.random() < willingness:
                            if current < col_level:
                                new_level = min(current + 1, col_level)

            # Countries sanction invaders
            if target_id == "nordostan":
                for war in ws.wars:
                    if war.get("attacker") == "nordostan":
                        if self.country_id in WESTERN_ALLIANCE and current < 2:
                            new_level = min(current + 1, 3)

            # Sanction nuclear proliferators
            target_c = ws.countries.get(target_id, {})
            target_nuc = target_c.get("technology", {}).get("nuclear_level", 0)
            target_nuc_prog = target_c.get("technology", {}).get("nuclear_rd_progress", 0)
            if (target_id in ("persia", "choson") and target_nuc_prog > 0.7
                    and self.country_id in COLUMBIA_BLOC):
                if current < 2:
                    new_level = min(current + 1, 3)

            # Sanctions evasion: Cathay helps Nordostan
            if (self.country_id == "cathay" and target_id == "nordostan"
                    and current >= 0):
                new_level = min(current, -1)  # Active evasion

            # Nordostan sanctions Heartland
            if self.country_id == "nordostan" and target_id == "heartland":
                new_level = 3

            if new_level != current:
                sanction_changes[target_id] = new_level

        return sanction_changes

    # -------------------------------------------------------------------
    # MILITARY DECISIONS
    # -------------------------------------------------------------------

    def decide_military(self, country: dict, ws: WorldState, round_num: int) -> dict:
        """Decide military actions: attacks, deployments, blockades, missiles."""
        mil = country["military"]
        military_actions = {
            "combat": [],
            "blockades": [],
            "missile_strikes": [],
            "covert_ops": [],
            "mobilizations": None,
        }

        # --- Nordostan: Eastern Europe offensive ---
        if self.country_id == "nordostan":
            military_actions = self._nordostan_military(country, ws, round_num,
                                                        military_actions)

        # --- Heartland: defense and counteroffensive ---
        elif self.country_id == "heartland":
            military_actions = self._heartland_military(country, ws, round_num,
                                                         military_actions)

        # --- Cathay: Taiwan Strait buildup ---
        elif self.country_id == "cathay":
            military_actions = self._cathay_military(country, ws, round_num,
                                                      military_actions)

        # --- Levantia: potential Persia strike ---
        elif self.country_id == "levantia":
            military_actions = self._levantia_military(country, ws, round_num,
                                                        military_actions)

        # --- Choson: provocations ---
        elif self.country_id == "choson":
            military_actions = self._choson_military(country, ws, round_num,
                                                      military_actions)

        # --- Columbia: naval deployments ---
        elif self.country_id == "columbia":
            military_actions = self._columbia_military(country, ws, round_num,
                                                        military_actions)

        # --- Persia: Hormuz leverage ---
        elif self.country_id == "persia":
            military_actions = self._persia_military(country, ws, round_num,
                                                      military_actions)

        # --- Default: intelligence and cyber for capable powers ---
        if self.country_id in ("albion", "columbia", "cathay", "levantia"):
            military_actions = self._add_covert_ops(country, ws, round_num,
                                                     military_actions)

        return military_actions

    def _nordostan_military(self, country: dict, ws: WorldState, round_num: int,
                            actions: dict) -> dict:
        """Nordostan: push in Eastern Europe but conserve if losing."""
        mil = country["military"]
        pol = country["political"]
        ground = mil.get("ground", 0)
        tiredness = pol.get("war_tiredness", 0)

        # Count forces on the front
        front_forces = 0
        for zone_id in EE_FRONT_ZONES:
            zone = ws.zones.get(zone_id, {}).get("forces", {})
            nord_in_zone = zone.get("nordostan", {})
            front_forces += nord_in_zone.get("ground", 0)

        # Heartland forces on adjacent zones
        heartland_front = 0
        for zone_id in EE_HEARTLAND_ZONES[:4]:  # capital, central, south, dnipro
            zone = ws.zones.get(zone_id, {}).get("forces", {})
            hl_in_zone = zone.get("heartland", {})
            heartland_front += hl_in_zone.get("ground", 0)

        # Attack if we have favorable ratio (2:1 or better) and not exhausted
        if front_forces >= heartland_front * 2 and tiredness < 6:
            # Pick a target zone to attack
            targets = ["ee_east_front_north", "ee_dnipro_line", "ee_south_ukr"]
            for target in targets:
                zone_forces = ws.zones.get(target, {}).get("forces", {})
                defenders = zone_forces.get("heartland", {}).get("ground", 0)
                if defenders > 0 and front_forces >= defenders * 2:
                    attack_units = min(front_forces, defenders * 3)
                    actions["combat"].append({
                        "attacker": "nordostan",
                        "defender": "heartland",
                        "zone": target,
                        "units": attack_units,
                    })
                    break  # One attack per round

        # Mobilize if losing ground and desperate
        if tiredness > 4 and ground < 12:
            actions["mobilizations"] = "partial"
        elif tiredness > 6 and ground < 8:
            actions["mobilizations"] = "general"

        # Occasional missile strikes on Heartland infrastructure
        if mil.get("strategic_missiles", 0) > 8 and random.random() < 0.4:
            actions["missile_strikes"].append({
                "country": "nordostan",
                "target_zone": random.choice(["ee_capital", "ee_central_ukr", "ee_south_ukr"]),
                "warhead": "conventional",
            })

        return actions

    def _heartland_military(self, country: dict, ws: WorldState, round_num: int,
                            actions: dict) -> dict:
        """Heartland: defend and counterattack when possible."""
        mil = country["military"]
        ground = mil.get("ground", 0)

        # Count our forces vs Nordostan on contested zones
        our_forces = 0
        for zone_id in EE_HEARTLAND_ZONES:
            zone = ws.zones.get(zone_id, {}).get("forces", {})
            our_forces += zone.get("heartland", {}).get("ground", 0)

        enemy_forces = 0
        for zone_id in EE_FRONT_ZONES:
            zone = ws.zones.get(zone_id, {}).get("forces", {})
            enemy_forces += zone.get("nordostan", {}).get("ground", 0)

        # Counterattack if we have favorable ratio on a specific zone
        if our_forces > 8:
            counter_targets = ["ee_east_front_central", "ee_east_front_south",
                               "ee_occupied_south"]
            for target in counter_targets:
                zone_forces = ws.zones.get(target, {}).get("forces", {})
                defenders = zone_forces.get("nordostan", {}).get("ground", 0)
                if defenders > 0 and our_forces >= defenders * 3:
                    attack_units = min(our_forces // 2, defenders * 3)
                    actions["combat"].append({
                        "attacker": "heartland",
                        "defender": "nordostan",
                        "zone": target,
                        "units": attack_units,
                    })
                    break

        # Mobilize if desperate
        if ground < 8:
            actions["mobilizations"] = "partial"
        if ground < 5:
            actions["mobilizations"] = "general"

        return actions

    def _cathay_military(self, country: dict, ws: WorldState, round_num: int,
                         actions: dict) -> dict:
        """Cathay: gradual buildup near Formosa, act if window opens."""
        mil = country["military"]
        pol = country["political"]
        tech = country["technology"]

        # Check Columbia naval presence in East China Sea
        ecs_forces = ws.zones.get("g_sea_east_china", {}).get("forces", {})
        columbia_naval = ecs_forces.get("columbia", {}).get("naval", 0)
        cathay_naval = ecs_forces.get("cathay", {}).get("naval", 0)
        yamato_naval = ecs_forces.get("yamato", {}).get("naval", 0)

        # Build up naval presence gradually
        # (production handles this, but we can signal intent)

        # If Columbia is distracted (low support or multiple crises)
        col_data = ws.countries.get("columbia", {})
        col_support = col_data.get("political", {}).get("political_support", 50)
        col_stability = col_data.get("political", {}).get("stability", 7)

        formosa_window = (
            col_support < 40
            and columbia_naval <= 2
            and mil.get("naval", 0) >= 10
            and round_num >= 4
        )

        if formosa_window and random.random() < self.aggression:
            # Blockade Formosa
            actions["blockades"].append({
                "country": "cathay",
                "zone": "g_sea_east_china",
            })
        elif round_num >= 3 and cathay_naval < columbia_naval + yamato_naval:
            # Covert cyber against Formosa
            actions["covert_ops"].append({
                "country": "cathay",
                "type": "cyber",
                "target": "formosa",
            })

        # Occasional cyber against Columbia
        if tech.get("ai_level", 0) >= 2 and random.random() < 0.3:
            actions["covert_ops"].append({
                "country": "cathay",
                "type": "cyber",
                "target": "columbia",
            })

        return actions

    def _levantia_military(self, country: dict, ws: WorldState, round_num: int,
                           actions: dict) -> dict:
        """Levantia: strike Persia nuclear sites if threshold crossed."""
        persia = ws.countries.get("persia", {})
        persia_nuc_prog = persia.get("technology", {}).get("nuclear_rd_progress", 0)
        persia_nuc_level = persia.get("technology", {}).get("nuclear_level", 0)

        # Strike if Persia approaching nuclear weapon
        if persia_nuc_prog >= 0.80 and persia_nuc_level == 0:
            # High probability of preemptive strike
            if random.random() < 0.7:
                actions["combat"].append({
                    "attacker": "levantia",
                    "defender": "persia",
                    "zone": "me_persia_nuclear",
                    "units": 4,  # air strike package
                })
                actions["missile_strikes"].append({
                    "country": "levantia",
                    "target_zone": "me_persia_nuclear",
                    "warhead": "conventional",
                })
        elif persia_nuc_level >= 1:
            # Already has nukes -- too late for conventional strike, go covert
            actions["covert_ops"].append({
                "country": "levantia",
                "type": "sabotage",
                "target": "persia",
            })

        # Ongoing proxy management
        if random.random() < 0.4:
            actions["covert_ops"].append({
                "country": "levantia",
                "type": "cyber",
                "target": "persia",
            })

        return actions

    def _choson_military(self, country: dict, ws: WorldState, round_num: int,
                         actions: dict) -> dict:
        """Choson: unpredictable provocations."""
        mil = country["military"]

        # Random provocations based on aggression and need for attention
        provocation_chance = 0.3 + (0.2 if round_num % 2 == 0 else 0)

        if random.random() < provocation_chance:
            provocation_type = random.choice(["missile_test", "border_incident", "cyber"])
            if provocation_type == "missile_test" and mil.get("strategic_missiles", 0) > 0:
                # Don't actually fire at anyone -- just demonstrate
                # Represented as a missile strike on own zone (test)
                pass  # Engine doesn't model tests, just demonstrate intent
            elif provocation_type == "cyber":
                target = random.choice(["hanguk", "yamato", "columbia"])
                actions["covert_ops"].append({
                    "country": "choson",
                    "type": "cyber",
                    "target": target,
                })
            elif provocation_type == "border_incident":
                # Slight naval provocation
                pass

        return actions

    def _columbia_military(self, country: dict, ws: WorldState, round_num: int,
                           actions: dict) -> dict:
        """Columbia: maintain naval presence, support allies, respond to crises."""
        mil = country["military"]

        # Arms transfers to Heartland (represented as increasing Heartland's
        # ground units -- engine handles production, we just signal budget intent)
        # Covert ops against adversaries
        if mil.get("strategic_missiles", 0) > 10:
            # Not using nukes -- but maintain deterrent posture
            pass

        # Intelligence operations
        if random.random() < 0.5:
            target = random.choice(["nordostan", "cathay", "persia"])
            actions["covert_ops"].append({
                "country": "columbia",
                "type": "espionage",
                "target": target,
            })

        # Cyber operations against adversaries
        if random.random() < 0.3:
            actions["covert_ops"].append({
                "country": "columbia",
                "type": "cyber",
                "target": random.choice(["nordostan", "cathay", "choson"]),
            })

        return actions

    def _persia_military(self, country: dict, ws: WorldState, round_num: int,
                         actions: dict) -> dict:
        """Persia: Hormuz leverage, proxy warfare, nuclear ambiguity."""
        eco = country["economic"]
        pol = country["political"]
        mil = country["military"]

        # Hormuz threat if under heavy sanctions or military pressure
        sanctions_on_us = ws.bilateral.get("sanctions", {})
        total_sanctions = sum(
            max(targets.get("persia", 0), 0)
            for imposer, targets in sanctions_on_us.items()
            if not imposer.startswith("_")
        )

        # Threaten Hormuz if sanctions are severe
        if total_sanctions > 10 and pol["stability"] < 5:
            if random.random() < 0.3 * self.aggression:
                actions["blockades"].append({
                    "country": "persia",
                    "zone": "me_gulf_hormuz",
                })

        # Proxy operations
        if random.random() < 0.4:
            actions["covert_ops"].append({
                "country": "persia",
                "type": "sabotage",
                "target": random.choice(["levantia", "solaria"]),
            })

        return actions

    def _add_covert_ops(self, country: dict, ws: WorldState, round_num: int,
                        actions: dict) -> dict:
        """Add intelligence and cyber operations for capable powers."""
        tech = country["technology"]
        ai_level = tech.get("ai_level", 0)

        if ai_level >= 2 and random.random() < 0.3:
            rels = self.profile.get("key_relationships", {})
            adversaries = [
                k for k, v in rels.items()
                if any(w in v.lower() for w in ["adversary", "enemy", "rival", "threat"])
            ]
            if adversaries:
                target = random.choice(adversaries)
                op_type = random.choice(["espionage", "cyber", "disinformation"])
                # Avoid duplicates
                existing_targets = [
                    op["target"] for op in actions.get("covert_ops", [])
                    if op.get("country") == self.country_id
                ]
                if target not in existing_targets:
                    actions.setdefault("covert_ops", []).append({
                        "country": self.country_id,
                        "type": op_type,
                        "target": target,
                    })
        return actions

    # -------------------------------------------------------------------
    # OPEC DECISIONS
    # -------------------------------------------------------------------

    def decide_opec(self, country: dict, ws: WorldState) -> str:
        """Decide OPEC+ production level: low, normal, high."""
        eco = country["economic"]
        oil_price = ws.oil_price

        if self.country_id == "solaria":
            # Solaria: cooperate to maintain price
            if oil_price < 60:
                return "low"  # Cut production to raise price
            elif oil_price > 120:
                return "high"  # Increase production to cool price and gain share
            else:
                return "normal"

        elif self.country_id == "nordostan":
            # Nordostan: needs revenue desperately
            if eco.get("treasury", 0) < 5 or eco.get("gdp_growth_rate", 0) < 0:
                return "high"  # Overproduce for revenue
            else:
                return "normal"

        elif self.country_id == "persia":
            # Persia: produce whatever they can given sanctions
            if eco.get("treasury", 0) < 3:
                return "high"
            return "normal"

        elif self.country_id == "mirage":
            # Mirage: follow Solaria's lead usually
            if oil_price < 70:
                return "low"
            return "normal"

        return "normal"

    # -------------------------------------------------------------------
    # DIPLOMATIC DECISIONS
    # -------------------------------------------------------------------

    def decide_diplomatic(self, country: dict, ws: WorldState,
                          round_num: int) -> dict:
        """Decide diplomatic actions: treaties, proposals, arms transfers."""
        diplomatic = {
            "arms_transfers": [],
            "proposals": [],
        }

        rels = self.profile.get("key_relationships", {})

        # Arms transfers to allies at war
        if self.country_id == "columbia":
            # Arms to Heartland
            hl = ws.countries.get("heartland", {})
            if any(w.get("defender") == "heartland" for w in ws.wars):
                transfer_amount = min(country["economic"]["treasury"] * 0.1, 3)
                if transfer_amount > 0.5:
                    diplomatic["arms_transfers"].append({
                        "from": "columbia",
                        "to": "heartland",
                        "amount": round(transfer_amount, 1),
                        "type": "military_aid",
                    })

        elif self.country_id in ("gallia", "albion", "teutonia", "freeland"):
            # European allies also send aid to Heartland
            if any(w.get("defender") == "heartland" for w in ws.wars):
                transfer = min(country["economic"]["treasury"] * 0.05, 1.5)
                if transfer > 0.3:
                    diplomatic["arms_transfers"].append({
                        "from": self.country_id,
                        "to": "heartland",
                        "amount": round(transfer, 1),
                        "type": "military_aid",
                    })

        # Bharata: play both sides
        if self.country_id == "bharata":
            if round_num % 2 == 1:
                diplomatic["proposals"].append({
                    "type": "trade_deal",
                    "with": "columbia",
                    "description": "Tech transfer agreement in exchange for defense cooperation",
                })
            else:
                diplomatic["proposals"].append({
                    "type": "trade_deal",
                    "with": "cathay",
                    "description": "Infrastructure investment deal via BRICS+ framework",
                })

        # Formosa: international advocacy
        if self.country_id == "formosa" and round_num >= 2:
            diplomatic["proposals"].append({
                "type": "diplomatic_campaign",
                "description": "International semiconductor cooperation agreement to build support",
            })

        return diplomatic

    # -------------------------------------------------------------------
    # TECH DECISIONS
    # -------------------------------------------------------------------

    def decide_tech(self, country: dict, ws: WorldState,
                    discretionary: float) -> dict:
        """Decide R&D investment allocation between nuclear and AI."""
        tech = country["technology"]
        weights = self.profile.get("decision_weights", {})
        tech_budget = discretionary * 0.15  # Base tech allocation

        nuclear_rd = 0
        ai_rd = 0

        # Countries pursuing nuclear weapons
        if self.country_id == "persia":
            # Heavy nuclear investment
            nuclear_rd = tech_budget * 0.70
            ai_rd = tech_budget * 0.30
        elif self.country_id == "choson":
            nuclear_rd = tech_budget * 0.80
            ai_rd = tech_budget * 0.20
        elif tech.get("nuclear_level", 0) >= 2:
            # Already nuclear -- maintain and focus on AI
            nuclear_rd = tech_budget * 0.10
            ai_rd = tech_budget * 0.90
        elif self.country_id in ("columbia", "cathay", "yamato", "hanguk", "bharata",
                                  "albion", "levantia", "formosa"):
            # Tech race countries prioritize AI
            nuclear_rd = tech_budget * 0.05
            ai_rd = tech_budget * 0.95
        else:
            # Default split
            nuclear_rd = tech_budget * 0.20
            ai_rd = tech_budget * 0.80

        return {
            "nuclear": round(max(nuclear_rd, 0), 2),
            "ai": round(max(ai_rd, 0), 2),
        }

    # -------------------------------------------------------------------
    # UTILITY METHODS
    # -------------------------------------------------------------------

    def _is_at_war(self, ws: WorldState) -> bool:
        return any(
            w.get("attacker") == self.country_id or w.get("defender") == self.country_id
            for w in ws.wars
        )

    def _is_at_war_country(self, country: dict) -> bool:
        return country.get("political", {}).get("war_tiredness", 0) > 0

    def _estimate_revenue(self, country: dict) -> float:
        eco = country["economic"]
        gdp = eco.get("gdp", 0)
        tax = eco.get("tax_rate", 0.2)
        return gdp * tax


# ---------------------------------------------------------------------------
# ACTION TRANSLATOR
# ---------------------------------------------------------------------------

def translate_actions(all_agent_actions: dict, ws: WorldState) -> dict:
    """Translate per-country agent actions into engine action format.

    The engine expects a single dict with keys like 'budgets', 'tariff_changes',
    etc. containing all countries' actions. Agents produce per-country dicts.
    """
    engine_actions = {
        "budgets": {},
        "tariff_changes": {},
        "sanction_changes": {},
        "opec_production": {},
        "mobilizations": {},
        "combat": [],
        "blockades": [],
        "missile_strikes": [],
        "covert_ops": [],
        "propaganda": {},
        "tech_rd": {},
        "events": [],
    }

    for country_id, agent_actions in all_agent_actions.items():
        # Budget
        budget = agent_actions.get("budget", {})
        engine_actions["budgets"][country_id] = budget

        # Tariffs
        tariff_changes = agent_actions.get("tariffs", {})
        if tariff_changes:
            engine_actions["tariff_changes"][country_id] = tariff_changes

        # Sanctions
        sanction_changes = agent_actions.get("sanctions", {})
        if sanction_changes:
            engine_actions["sanction_changes"][country_id] = sanction_changes

        # OPEC
        opec = agent_actions.get("opec_production")
        if opec:
            engine_actions["opec_production"][country_id] = opec

        # Military
        military = agent_actions.get("military", {})
        for combat in military.get("combat", []):
            engine_actions["combat"].append(combat)
        for blockade in military.get("blockades", []):
            engine_actions["blockades"].append(blockade)
        for strike in military.get("missile_strikes", []):
            engine_actions["missile_strikes"].append(strike)
        for op in military.get("covert_ops", []):
            engine_actions["covert_ops"].append(op)
        mob = military.get("mobilizations")
        if mob:
            engine_actions["mobilizations"][country_id] = mob

        # Tech
        tech = agent_actions.get("tech", {})
        if tech:
            engine_actions["tech_rd"][country_id] = tech

        # Diplomatic (arms transfers get processed as treasury adjustments)
        diplomatic = agent_actions.get("diplomatic", {})
        for transfer in diplomatic.get("arms_transfers", []):
            sender = transfer.get("from", country_id)
            receiver = transfer.get("to", "")
            amount = transfer.get("amount", 0)
            if (sender in ws.countries and receiver in ws.countries
                    and amount > 0):
                # Deduct from sender treasury, add to receiver
                ws.countries[sender]["economic"]["treasury"] = max(
                    ws.countries[sender]["economic"]["treasury"] - amount, 0
                )
                # Boost receiver military capacity (simplified: add ground units)
                recv_mil = ws.countries[receiver]["military"]
                units_added = max(1, int(amount / recv_mil.get("production_costs", {}).get("ground", 2)))
                recv_mil["ground"] = recv_mil.get("ground", 0) + units_added

    return engine_actions


# ---------------------------------------------------------------------------
# MAIN SIMULATION
# ---------------------------------------------------------------------------

def run_simulation(num_rounds: int = 6, seed: Optional[int] = None,
                   run_name: str = "run_1") -> Tuple[WorldState, dict]:
    """Run a complete simulation."""
    if seed is not None:
        random.seed(seed)

    print(f"\n{'#'*60}")
    print(f"# TTT CONCEPT TEST: {run_name}")
    print(f"# Seed: {seed}, Rounds: {num_rounds}")
    print(f"{'#'*60}")

    # Setup
    world_state = load_starting_state()
    profiles = load_country_profiles()
    engine = TTTEngine(world_state)

    # Initialize AI agents
    agents = {}
    for country_id in world_state.countries:
        agents[country_id] = CountryAI(country_id, profiles.get(country_id, {}),
                                        world_state)

    # Create output directory
    run_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), run_name)
    os.makedirs(run_dir, exist_ok=True)

    # Save initial state
    save_round(run_dir, 0, world_state, {}, {})

    # Run rounds
    for round_num in range(1, num_rounds + 1):
        print(f"\n{'='*60}")
        print(f"ROUND {round_num} -- {get_round_date(round_num)}")
        print(f"{'='*60}")

        # Phase A: AI countries deliberate and submit actions
        all_actions = {}
        for country_id, agent in agents.items():
            actions = agent.deliberate(engine.ws, round_num)
            all_actions[country_id] = actions

        # Translate agent actions to engine format
        engine_actions = translate_actions(all_actions, engine.ws)

        # Check for scheduled events
        events = check_scheduled_events(round_num, engine.ws)

        # Phase B: Engine processes all actions (three-pass)
        new_ws, round_report = engine.process_round(engine_actions, round_num)

        # Phase C: Process scheduled events (elections, etc.)
        if events:
            process_events(events, new_ws, engine, round_num)

        # Rebuild engine with new state for next round
        engine = TTTEngine(new_ws)

        # Update agent memory
        for agent in agents.values():
            agent.memory.append({
                "round": round_num,
                "key_events": round_report.get("narrative", ""),
                "own_state": get_country_summary(new_ws, agent.country_id),
            })

        # Save round data
        save_round(run_dir, round_num, new_ws, all_actions, round_report)

        # Print summary
        print_round_summary(new_ws, round_report, round_num)

    # Final analysis
    final_ws = engine.ws
    analysis = generate_analysis(run_dir, final_ws, num_rounds)
    save_analysis(run_dir, analysis)

    # Print final assessment
    print(f"\n{'='*60}")
    print("FINAL ASSESSMENT")
    print(f"{'='*60}")
    tq = analysis["test_questions"]
    trap = tq["thucydides_trap"]
    print(f"\n1. Thucydides Trap: {trap['assessment']}")
    print(f"   Columbia GDP: {trap['columbia_gdp']}, Cathay GDP: {trap['cathay_gdp']}")
    print(f"   Gap ratio: {trap['gdp_gap_ratio']:.3f}")
    print(f"   Direct conflict: {trap['direct_conflict']}")

    alliance = tq["alliance_cohesion"]
    print(f"\n2. Alliance Cohesion: {alliance['assessment']}")
    print(f"   Weakest NATO link: {alliance['weakest_link']}")

    ee = tq["eastern_europe_war"]
    print(f"\n3. Eastern Europe War: {ee['status']}")
    print(f"   Nordostan stability: {ee['nordostan_stability']}, "
          f"tiredness: {ee['nordostan_war_tiredness']:.1f}")
    print(f"   Heartland stability: {ee['heartland_stability']}, "
          f"tiredness: {ee['heartland_war_tiredness']:.1f}")

    return final_ws, analysis


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    run_name = sys.argv[1] if len(sys.argv) > 1 else "run_1"
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else None
    num_rounds = int(sys.argv[3]) if len(sys.argv) > 3 else 6
    run_simulation(num_rounds=num_rounds, seed=seed, run_name=run_name)
