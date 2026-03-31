"""
TTT SEED — AI Agent System
============================
Each role in the simulation is represented by an AI agent.
Team countries have multiple agents that coordinate internally.
Solo countries have one agent per country.

Decision logic references DETAILED role seeds:
- Helmsman calculates Formosa window from naval ratio + age
- Pathfinder weighs war continuation vs. deal opportunity
- Dealer pursues heritage targets (Caribe, Persia, Ruthenia deal)
- Beacon fights to hold the line while support erodes
- Anvil manages Gulf Gate blockade as leverage

Author: ATLAS (World Model Engineer)
Version: 2.0 (SEED)
"""

import random
import math
import copy
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

from world_state import WorldState, clamp, UNIT_TYPES


# ---------------------------------------------------------------------------
# ROLE PROFILES — embedded from role seeds
# ---------------------------------------------------------------------------

ROLE_PROFILES = {
    # COLUMBIA
    "dealer": {
        "country": "columbia", "head_of_state": True,
        "aggression": 0.6, "risk_tolerance": 0.5, "deal_seeking": 0.9,
        "objectives": ["secure_legacy", "win_persia_war", "resolve_caribe",
                        "ruthenia_deal", "contain_cathay", "acquire_thule"],
        "acceptance_threshold": 0.4, "rejection_threshold": 0.2,
        "incapacitation_risk": 0.10,
        "heritage_targets": ["caribe", "persia"],
        "negotiation_priority": ["sarmatia", "cathay", "ruthenia"],
    },
    "volt": {
        "country": "columbia", "head_of_state": False,
        "aggression": 0.3, "risk_tolerance": 0.4, "deal_seeking": 0.6,
        "objectives": ["win_nomination", "build_base", "prove_loyalty"],
        "acceptance_threshold": 0.5, "rejection_threshold": 0.3,
        "faction": "presidents_camp",
        "isolationist_tendency": 0.7,
    },
    "anchor": {
        "country": "columbia", "head_of_state": False,
        "aggression": 0.5, "risk_tolerance": 0.5, "deal_seeking": 0.7,
        "objectives": ["win_nomination", "cuba_legacy", "alliance_management"],
        "acceptance_threshold": 0.5, "rejection_threshold": 0.3,
        "faction": "presidents_camp",
        "hawk_level": 0.7,
    },
    "shield": {
        "country": "columbia", "head_of_state": False, "military_chief": True,
        "aggression": 0.3, "risk_tolerance": 0.3, "deal_seeking": 0.4,
        "objectives": ["military_readiness", "manage_overstretch", "warrior_ethos"],
        "acceptance_threshold": 0.6, "rejection_threshold": 0.4,
        "overstretch_concern": 0.8,
    },
    "shadow": {
        "country": "columbia", "head_of_state": False,
        "aggression": 0.4, "risk_tolerance": 0.5, "deal_seeking": 0.5,
        "objectives": ["intelligence_accuracy", "covert_influence", "protect_sources"],
        "acceptance_threshold": 0.5, "rejection_threshold": 0.3,
        "information_power": 0.9,
    },
    "tribune": {
        "country": "columbia", "head_of_state": False,
        "aggression": 0.6, "risk_tolerance": 0.4, "deal_seeking": 0.3,
        "objectives": ["flip_parliament", "constrain_president", "opposition_agenda"],
        "acceptance_threshold": 0.3, "rejection_threshold": 0.1,
        "faction": "opposition",
    },
    "challenger": {
        "country": "columbia", "head_of_state": False,
        "aggression": 0.4, "risk_tolerance": 0.4, "deal_seeking": 0.5,
        "objectives": ["win_presidency", "build_coalition", "alternative_future"],
        "acceptance_threshold": 0.4, "rejection_threshold": 0.2,
        "faction": "opposition",
    },

    # CATHAY
    "helmsman": {
        "country": "cathay", "head_of_state": True,
        "aggression": 0.5, "risk_tolerance": 0.4, "deal_seeking": 0.3,
        "objectives": ["formosa_resolution", "military_parity", "keep_sarmatia",
                        "prevent_columbia_ai4", "internal_control", "growth_above_3"],
        "acceptance_threshold": 0.6, "rejection_threshold": 0.4,
        "formosa_urgency": 0.6, "purge_tendency": 0.5,
        "age": 73, "legacy_pressure": 0.8,
    },
    "rampart": {
        "country": "cathay", "head_of_state": False, "military_chief": True,
        "aggression": 0.3, "risk_tolerance": 0.2, "deal_seeking": 0.3,
        "objectives": ["survive_purges", "military_readiness", "professional_standards"],
        "acceptance_threshold": 0.5, "rejection_threshold": 0.3,
        "caution_level": 0.8, "slow_walk_probability": 0.3,
    },
    "abacus": {
        "country": "cathay", "head_of_state": False,
        "aggression": 0.1, "risk_tolerance": 0.2, "deal_seeking": 0.5,
        "objectives": ["economic_stability", "reform", "prevent_catastrophe"],
        "acceptance_threshold": 0.5, "rejection_threshold": 0.3,
        "economic_caution": 0.9,
    },
    "circuit": {
        "country": "cathay", "head_of_state": False,
        "aggression": 0.2, "risk_tolerance": 0.3, "deal_seeking": 0.6,
        "objectives": ["tech_self_sufficiency", "protect_assets", "global_integration"],
        "acceptance_threshold": 0.5, "rejection_threshold": 0.3,
        "defection_risk": 0.15,
    },
    "sage": {
        "country": "cathay", "head_of_state": False,
        "aggression": 0.1, "risk_tolerance": 0.1, "deal_seeking": 0.4,
        "objectives": ["party_survival", "collective_leadership", "prevent_catastrophe"],
        "acceptance_threshold": 0.3, "rejection_threshold": 0.1,
        "activation_threshold_stability": 5, "activation_threshold_support": 40,
    },

    # SARMATIA
    "pathfinder": {
        "country": "sarmatia", "head_of_state": True,
        "aggression": 0.6, "risk_tolerance": 0.5, "deal_seeking": 0.7,
        "objectives": ["control_territories", "great_power_recognition",
                        "survive_in_power", "exploit_dealer_window", "cathay_partnership"],
        "acceptance_threshold": 0.5, "rejection_threshold": 0.3,
        "territorial_minimum": 0.65,  # won't accept less than 65% of claimed
        "deal_window_urgency": 0.7,
    },
    "ironhand": {
        "country": "sarmatia", "head_of_state": False, "military_chief": True,
        "aggression": 0.4, "risk_tolerance": 0.3, "deal_seeking": 0.4,
        "objectives": ["military_result", "professional_honor", "survive"],
        "acceptance_threshold": 0.5, "rejection_threshold": 0.3,
        "resentment": 0.6, "coup_calculation": 0.2,
    },
    "compass": {
        "country": "sarmatia", "head_of_state": False,
        "aggression": 0.2, "risk_tolerance": 0.5, "deal_seeking": 0.9,
        "objectives": ["economic_survival", "back_channel_deals", "sanctions_relief"],
        "acceptance_threshold": 0.4, "rejection_threshold": 0.2,
        "western_asset_value": 0.8,
    },

    # RUTHENIA
    "beacon": {
        "country": "ruthenia", "head_of_state": True,
        "aggression": 0.4, "risk_tolerance": 0.4, "deal_seeking": 0.5,
        "objectives": ["survive_politically", "no_territorial_concessions",
                        "eu_membership", "maintain_western_aid", "prevent_rivals"],
        "acceptance_threshold": 0.6, "rejection_threshold": 0.4,
        "territorial_red_line": True,
    },
    "bulwark": {
        "country": "ruthenia", "head_of_state": False, "military_chief": True,
        "aggression": 0.5, "risk_tolerance": 0.4, "deal_seeking": 0.3,
        "objectives": ["military_victory", "popular_mandate", "better_leadership"],
        "acceptance_threshold": 0.4, "rejection_threshold": 0.2,
        "election_ambition": 0.8,
    },
    "broker": {
        "country": "ruthenia", "head_of_state": False,
        "aggression": 0.2, "risk_tolerance": 0.6, "deal_seeking": 0.9,
        "objectives": ["negotiated_peace", "political_survival", "pragmatic_deal"],
        "acceptance_threshold": 0.3, "rejection_threshold": 0.1,
        "back_channel_active": True,
    },

    # PERSIA
    "furnace": {
        "country": "persia", "head_of_state": True,
        "aggression": 0.6, "risk_tolerance": 0.5, "deal_seeking": 0.2,
        "objectives": ["survive_physically", "consolidate_power",
                        "maintain_republic", "nuclear_threshold", "resist_west"],
        "acceptance_threshold": 0.7, "rejection_threshold": 0.5,
        "independence_from_anvil": 0.7,
    },
    "anvil": {
        "country": "persia", "head_of_state": False, "military_chief": True,
        "aggression": 0.5, "risk_tolerance": 0.5, "deal_seeking": 0.6,
        "objectives": ["military_leverage", "business_protection", "power_broker"],
        "acceptance_threshold": 0.4, "rejection_threshold": 0.2,
        "gulf_gate_leverage": 0.9,
        "nuclear_as_bargaining_chip": True,
    },
    "dawn": {
        "country": "persia", "head_of_state": False,
        "aggression": 0.1, "risk_tolerance": 0.6, "deal_seeking": 0.9,
        "objectives": ["engagement", "economic_opening", "represent_youth"],
        "acceptance_threshold": 0.3, "rejection_threshold": 0.1,
        "reform_urgency": 0.8,
    },
}

# Solo country profiles (simplified)
SOLO_PROFILES = {
    "lumiere": {"country": "gallia", "aggression": 0.4, "deal_seeking": 0.6,
                "objectives": ["european_autonomy", "nuclear_credibility"]},
    "forge": {"country": "teutonia", "aggression": 0.2, "deal_seeking": 0.7,
              "objectives": ["economic_prosperity", "cathay_trade", "reluctant_rearmament"]},
    "sentinel": {"country": "freeland", "aggression": 0.5, "deal_seeking": 0.4,
                 "objectives": ["maximum_security", "sarmatia_containment"]},
    "ponte_role": {"country": "ponte", "aggression": 0.2, "deal_seeking": 0.8,
                   "objectives": ["debt_survival", "eu_influence", "hedge_all_sides"]},
    "mariner": {"country": "albion", "aggression": 0.4, "deal_seeking": 0.5,
                "objectives": ["special_relationship", "post_brexit_relevance"]},
    "pillar": {"country": "gallia", "aggression": 0.1, "deal_seeking": 0.5,
               "objectives": ["eu_unity", "institutional_relevance"]},
    "scales": {"country": "bharata", "aggression": 0.3, "deal_seeking": 0.7,
               "objectives": ["strategic_autonomy", "economic_growth", "third_pole"]},
    "citadel": {"country": "levantia", "aggression": 0.7, "deal_seeking": 0.4,
                "objectives": ["regional_dominance", "persia_threat", "columbia_alliance"]},
    "chip": {"country": "formosa", "aggression": 0.1, "deal_seeking": 0.6,
             "objectives": ["survival", "semiconductor_leverage", "columbia_protection"]},
    "vizier": {"country": "phrygia", "aggression": 0.4, "deal_seeking": 0.8,
               "objectives": ["maximum_leverage", "straits_control", "hedge_everyone"]},
    "sakura": {"country": "yamato", "aggression": 0.3, "deal_seeking": 0.5,
               "objectives": ["pacific_security", "remilitarization", "columbia_alliance"]},
    "wellspring": {"country": "solaria", "aggression": 0.3, "deal_seeking": 0.8,
                   "objectives": ["oil_pricing_power", "vision_2030", "hedge_us_china"]},
    "pyro": {"country": "choson", "aggression": 0.7, "deal_seeking": 0.3,
             "objectives": ["regime_survival", "nuclear_leverage", "extract_concessions"]},
    "vanguard": {"country": "hanguk", "aggression": 0.3, "deal_seeking": 0.5,
                 "objectives": ["national_security", "economic_stability"]},
    "havana": {"country": "caribe", "aggression": 0.3, "deal_seeking": 0.7,
               "objectives": ["regime_survival", "resist_columbia", "find_patrons"]},
    "spire": {"country": "mirage", "aggression": 0.2, "deal_seeking": 0.9,
              "objectives": ["financial_power", "connect_everyone", "pragmatic_hedging"]},
}


# ---------------------------------------------------------------------------
# RESPONSE / PROPOSAL
# ---------------------------------------------------------------------------

@dataclass
class Proposal:
    """A structured negotiation proposal."""
    proposer: str
    target: str
    proposal_type: str  # "trade_deal", "arms_transfer", "peace", "sanctions_coordination", etc.
    terms: dict
    round_num: int

@dataclass
class Response:
    """Response to a proposal."""
    accepted: bool = False
    rejected: bool = False
    counter: Optional[Any] = None
    reason: str = ""


# ---------------------------------------------------------------------------
# AI AGENT
# ---------------------------------------------------------------------------

class AIAgent:
    """An AI participant -- either a country leader or a specific role."""

    def __init__(self, role_id: str, country_id: str, profile: dict,
                 world_state: WorldState):
        self.role_id = role_id
        self.country_id = country_id
        self.profile = profile
        self.ws = world_state
        self.memory: List[dict] = []
        self.relationships: Dict[str, float] = {}  # role_id -> affinity (-1 to 1)
        self.pending_proposals: List[Proposal] = []
        self.actions_this_round: dict = {}
        self.negotiation_history: List[dict] = []

        # Initialize relationships from world state
        self._init_relationships()

    def _init_relationships(self) -> None:
        """Initialize relationship scores from world state data."""
        country_rels = self.ws.relationships.get(self.country_id, {})
        rel_map = {
            "close_ally": 0.8, "alliance": 0.5, "friendly": 0.3,
            "neutral": 0.0, "tense": -0.3, "hostile": -0.6, "at_war": -1.0,
        }
        for target_country, data in country_rels.items():
            score = rel_map.get(data["relationship"], 0.0)
            # Find head of state for that country
            hos = self.ws.get_head_of_state(target_country)
            if hos:
                self.relationships[hos["id"]] = score

    # ===================================================================
    # MAIN DELIBERATION
    # ===================================================================

    def deliberate(self, world_state: WorldState, round_num: int) -> dict:
        """Decide all actions for this round based on role profile."""
        self.ws = world_state
        c = self.ws.countries.get(self.country_id, {})
        if not c:
            return {}

        actions = {}

        # Only heads of state submit country-level actions
        if self.profile.get("head_of_state", False):
            actions["budget"] = self.decide_budget(c, round_num)
            actions["tariffs"] = self.decide_tariffs(c, round_num)
            actions["sanctions"] = self.decide_sanctions(c, round_num)
            actions["military"] = self.decide_military(c, round_num)
            actions["diplomatic"] = self.decide_diplomatic(c, round_num)
            actions["transactions"] = self.decide_transactions(c, round_num)

            if c["economic"].get("opec_member"):
                actions["opec"] = self.decide_opec(c, round_num)
        else:
            # Non-HoS roles: influence, advise, pursue private objectives
            actions["influence"] = self.decide_influence(c, round_num)
            actions["private"] = self.decide_private_actions(c, round_num)

        self.actions_this_round = actions
        self.memory.append({"round": round_num, "actions": copy.deepcopy(actions)})
        return actions

    # ===================================================================
    # BUDGET DECISION
    # ===================================================================

    def decide_budget(self, c: dict, round_num: int) -> dict:
        eco = c["economic"]
        gdp = eco["gdp"]
        at_war = self.ws.get_country_at_war(self.country_id)
        aggression = self.profile.get("aggression", 0.5)

        # Base allocation ratios
        baseline_social = eco.get("social_spending_baseline", 0.30)
        if at_war:
            social_pct = max(baseline_social - 0.05, 0.15)  # slight cut, not drastic
            military_pct = 0.40 + aggression * 0.15
            tech_pct = 0.10
        else:
            social_pct = max(baseline_social + 0.02, 0.20)  # slightly above baseline
            military_pct = 0.20 + aggression * 0.10
            tech_pct = 0.15

        # Country-specific adjustments
        if self.country_id == "ruthenia":
            # Ruthenia is dependent on aid, minimal discretionary
            social_pct = 0.25
            military_pct = 0.50
            tech_pct = 0.05
        elif self.country_id == "cathay":
            # Helmsman prioritizes military buildup
            military_pct = 0.40 + self.profile.get("formosa_urgency", 0.5) * 0.10
            tech_pct = 0.20
        elif self.country_id == "sarmatia":
            military_pct = 0.50
            tech_pct = 0.05

        reserve_pct = max(1.0 - social_pct - military_pct - tech_pct, 0)

        return {
            "social_spending_ratio": social_pct,
            "military_pct": military_pct,
            "tech_pct": tech_pct,
            "reserve_pct": reserve_pct,
            "money_printed": 0,
            "deficit": 0,
        }

    # ===================================================================
    # TARIFF DECISION
    # ===================================================================

    def decide_tariffs(self, c: dict, round_num: int) -> dict:
        """Decide tariff changes. Aggressive toward rivals, lower for allies."""
        changes = {}
        country_rels = self.ws.relationships.get(self.country_id, {})

        for target, data in country_rels.items():
            rel = data["relationship"]
            if rel in ("hostile", "at_war"):
                # Maintain or increase tariffs on enemies
                current = self.ws.bilateral.get("tariffs", {}).get(
                    self.country_id, {}).get(target, 0)
                if current < 2 and self.profile.get("aggression", 0.5) > 0.4:
                    changes[target] = min(current + 1, 3)
            elif rel == "close_ally" and self.profile.get("deal_seeking", 0.5) > 0.6:
                current = self.ws.bilateral.get("tariffs", {}).get(
                    self.country_id, {}).get(target, 0)
                if current > 0:
                    changes[target] = max(current - 1, 0)

        return changes

    # ===================================================================
    # SANCTIONS DECISION
    # ===================================================================

    def decide_sanctions(self, c: dict, round_num: int) -> dict:
        changes = {}
        country_rels = self.ws.relationships.get(self.country_id, {})

        for target, data in country_rels.items():
            rel = data["relationship"]
            if rel == "at_war":
                current = self.ws.bilateral.get("sanctions", {}).get(
                    self.country_id, {}).get(target, 0)
                if current < 3:
                    changes[target] = min(current + 1, 3)

        return changes

    # ===================================================================
    # MILITARY DECISION
    # ===================================================================

    def decide_military(self, c: dict, round_num: int) -> dict:
        """Military decisions: attacks, mobilization, production allocation.

        Countries at war MUST attack every round if they have units.
        Role-specific logic adjusts posture and targets.
        """
        decisions = {"attacks": [], "mobilization": None, "production": {}}
        mil = c["military"]
        at_war = self.ws.get_country_at_war(self.country_id)
        aggression = self.profile.get("aggression", 0.5)
        risk_tol = self.profile.get("risk_tolerance", 0.5)

        # ROLE-SPECIFIC MILITARY LOGIC

        # HELMSMAN: Formosa window calculation
        if self.role_id == "helmsman":
            cathay_naval = mil.get("naval", 0)
            col_naval = self.ws.countries.get("columbia", {}).get("military", {}).get("naval", 0)
            formosa_def = self.ws.countries.get("formosa", {}).get("military", {}).get("ground", 0)
            naval_ratio = cathay_naval / max(col_naval, 1)
            age_pressure = (self.profile.get("age", 73) - 70) * 0.1

            formosa_urgency = self.profile.get("formosa_urgency", 0.6)
            # Blockade threshold lowered -- urgency drives action
            if formosa_urgency > 0.7 and round_num >= 3:
                decisions["formosa_action"] = "full_blockade"
            elif naval_ratio >= 0.6 and formosa_urgency > 0.4 and round_num >= 2:
                decisions["formosa_action"] = "blockade"

        # PATHFINDER: War continuation -- ALWAYS attacks in war
        elif self.role_id == "pathfinder":
            deal_window = self.profile.get("deal_window_urgency", 0.7)
            territory_held = len([
                z for z in self.ws.wars[0].get("occupied_zones", [])
                if self.ws.zones.get(z, {}).get("owner") == "sarmatia"
            ]) if self.ws.wars else 0

            # Posture: negotiate vs pressure
            if deal_window > 0.8 and round_num >= 4 and aggression < 0.5:
                decisions["war_posture"] = "negotiate_from_strength"
            else:
                decisions["war_posture"] = "continue_pressure"

            # ALWAYS attack if at war -- aggression determines scale
            if at_war and mil.get("ground", 0) > 2:
                attack_units = max(2, int(mil.get("ground", 0) * (0.15 + aggression * 0.20)))
                # Target ruthenia zones where Sarmatia has or can project forces
                target_zones = ["ruthenia_2"]  # main contested zone
                if aggression > 0.6:
                    target_zones.append("ruthenia_1")
                for tz in target_zones:
                    decisions["attacks"].append({
                        "target_country": "ruthenia",
                        "preferred_zone": tz,
                        "units": max(2, attack_units // len(target_zones)),
                    })

        # DEALER: Multiple theaters -- Columbia MUST prosecute Persia war
        elif self.role_id == "dealer":
            if any(w.get("defender") == "persia" for w in self.ws.wars):
                decisions["persia_posture"] = "sustained_pressure"
                # Commit forces to Persia theater
                persia_units = max(2, int(mil.get("ground", 0) * 0.15))
                decisions["attacks"].append({
                    "target_country": "persia",
                    "preferred_zone": "persia_1",
                    "units": persia_units,
                })
                # Air strikes
                if mil.get("tactical_air", 0) > 5:
                    decisions["attacks"].append({
                        "target_country": "persia",
                        "preferred_zone": "persia_2",
                        "units": max(1, mil.get("tactical_air", 0) // 5),
                    })
            # Caribe operation
            heritage = self.profile.get("heritage_targets", [])
            if "caribe" in heritage and mil.get("ground", 0) > 15:
                decisions["caribe_action"] = "maintain_pressure"

        # BEACON/BULWARK: Defensive posture -- counterattack when able
        elif self.role_id in ("beacon", "bulwark"):
            if at_war and mil.get("ground", 0) > 3:
                if aggression > 0.3 or mil.get("ground", 0) > 8:
                    decisions["war_posture"] = "limited_counteroffensive"
                    # Counterattack in ruthenia_2 (main contested zone)
                    counter_units = max(2, int(mil.get("ground", 0) * 0.25))
                    decisions["attacks"].append({
                        "target_country": "sarmatia",
                        "preferred_zone": "ruthenia_2",
                        "units": counter_units,
                    })
                else:
                    decisions["war_posture"] = "defensive_hold"
                    # Defensive skirmishes in ruthenia_1
                    decisions["attacks"].append({
                        "target_country": "sarmatia",
                        "preferred_zone": "ruthenia_1",
                        "units": max(1, mil.get("ground", 0) // 5),
                    })

        # CITADEL (Levantia): Multi-front strikes against Persia
        elif self.role_id == "citadel":
            if at_war and mil.get("ground", 0) > 2:
                strike_units = max(2, int(mil.get("ground", 0) * (0.20 + aggression * 0.15)))
                decisions["attacks"].append({
                    "target_country": "persia",
                    "preferred_zone": "persia_1",
                    "units": strike_units,
                })
                # Missile strikes if available
                if mil.get("tactical_air", 0) > 2:
                    decisions["attacks"].append({
                        "target_country": "persia",
                        "preferred_zone": "persia_3",
                        "units": max(1, mil.get("tactical_air", 0) // 3),
                    })

        # FURNACE (Persia): Defend and retaliate
        elif self.role_id == "furnace":
            if at_war and mil.get("ground", 0) > 2:
                decisions["war_posture"] = "active_defense"
                # Defensive counterstrikes
                if aggression > 0.4:
                    decisions["attacks"].append({
                        "target_country": "levantia",
                        "preferred_zone": "levantia",
                        "units": max(1, mil.get("ground", 0) // 4),
                    })

        # ANVIL: Gulf Gate management + military operations
        elif self.role_id == "anvil":
            gulf_forces = self.ws.get_zone_forces("cp_gulf_gate")
            persia_ground = gulf_forces.get("persia", {}).get("ground", 0)
            if persia_ground >= 1:
                decisions["gulf_gate"] = "maintain_blockade"
                decisions["gulf_gate_leverage"] = self.profile.get("gulf_gate_leverage", 0.9)

        # PYRO (Choson): Provocative actions
        elif self.role_id == "pyro":
            if aggression > 0.5 and round_num >= 2:
                decisions["provocation"] = "missile_test"

        # DEFAULT for other solo countries at war: generate attacks
        elif at_war and mil.get("ground", 0) > 2:
            # Find war enemies and attack them
            for w in self.ws.wars:
                enemy = None
                if w.get("attacker") == self.country_id:
                    enemy = w.get("defender")
                elif w.get("defender") == self.country_id:
                    enemy = w.get("attacker")
                elif self.country_id in w.get("allies", {}).get("attacker", []):
                    enemy = w.get("defender")
                elif self.country_id in w.get("allies", {}).get("defender", []):
                    enemy = w.get("attacker")
                if enemy:
                    enemy_zones = self.ws.countries.get(enemy, {}).get("home_zones", [])
                    if enemy_zones:
                        attack_units = max(1, int(mil.get("ground", 0) * 0.15))
                        decisions["attacks"].append({
                            "target_country": enemy,
                            "preferred_zone": enemy_zones[0],
                            "units": attack_units,
                        })

        # Mobilization decision -- more responsive
        if at_war:
            ground = mil.get("ground", 0)
            if ground < 5:
                decisions["mobilization"] = "general"
            elif ground < 10 and aggression > 0.3:
                decisions["mobilization"] = "partial"
            elif ground < 15 and aggression > 0.6:
                decisions["mobilization"] = "partial"

        # Production allocation -- war countries MUST allocate coins
        budget = self.decide_budget(c, round_num) if not hasattr(self, '_budget_decided') else {}
        eco = c["economic"]
        revenue = eco["gdp"] * eco["tax_rate"]
        if at_war:
            mil_coins = revenue * 0.30  # allocate real coins to production
            ground_coins = mil_coins * 0.6
            naval_coins = mil_coins * 0.2
            air_coins = mil_coins * 0.2
            decisions["production"] = {
                "ground": {"coins": round(ground_coins, 1), "tier": "accelerated"},
                "naval": {"coins": round(naval_coins, 1), "tier": "normal"},
                "tactical_air": {"coins": round(air_coins, 1), "tier": "normal"},
            }
        else:
            mil_coins = revenue * 0.15
            decisions["production"] = {
                "ground": {"coins": round(mil_coins * 0.4, 1), "tier": "normal"},
                "naval": {"coins": round(mil_coins * 0.3, 1), "tier": "normal"},
                "tactical_air": {"coins": round(mil_coins * 0.3, 1), "tier": "normal"},
            }

        return decisions

    # ===================================================================
    # DIPLOMATIC DECISION
    # ===================================================================

    def decide_diplomatic(self, c: dict, round_num: int) -> dict:
        decisions = {"proposals": [], "public_statements": []}
        deal_seeking = self.profile.get("deal_seeking", 0.5)

        # Role-specific diplomacy
        if self.role_id == "dealer":
            if deal_seeking > 0.7:
                decisions["proposals"].append({
                    "target": "pathfinder",
                    "type": "peace_framework",
                    "terms": {"ruthenia_freeze_lines": True, "sanctions_relief_partial": True},
                })
            decisions["proposals"].append({
                "target": "helmsman",
                "type": "trade_negotiation",
                "terms": {"tariff_reduction": True, "formosa_status_quo": True},
            })

        elif self.role_id == "pathfinder":
            if self.profile.get("deal_window_urgency", 0.5) > 0.6:
                decisions["proposals"].append({
                    "target": "dealer",
                    "type": "grand_bargain",
                    "terms": {"territorial_recognition": True, "sanctions_relief": True,
                              "great_power_status": True},
                })

        elif self.role_id == "helmsman":
            # Keep Sarmatia close
            decisions["proposals"].append({
                "target": "pathfinder",
                "type": "partnership_renewal",
                "terms": {"economic_support": True, "diplomatic_cover": True},
            })

        elif self.role_id == "beacon":
            # Seek EU membership, maintain aid
            decisions["proposals"].append({
                "target": "lumiere",
                "type": "eu_accession",
                "terms": {"membership_timeline": True, "security_guarantees": True},
            })
            decisions["proposals"].append({
                "target": "dealer",
                "type": "aid_continuation",
                "terms": {"military_aid": True, "no_territorial_concessions": True},
            })

        elif self.role_id == "anvil":
            # Gulf Gate as leverage
            decisions["proposals"].append({
                "target": "dealer",
                "type": "ceasefire_terms",
                "terms": {"end_epic_fury": True, "sanctions_relief": True,
                          "gulf_gate_reopening": True},
            })

        return decisions

    # ===================================================================
    # TRANSACTION DECISION
    # ===================================================================

    def decide_transactions(self, c: dict, round_num: int) -> List[dict]:
        transactions = []
        country_rels = self.ws.relationships.get(self.country_id, {})

        # Arms transfers to allies at war
        for target, data in country_rels.items():
            if data["relationship"] == "close_ally":
                target_c = self.ws.countries.get(target, {})
                if self.ws.get_country_at_war(target):
                    # Consider small arms transfer
                    available = c["military"].get("ground", 0)
                    if available > 15 and target_c.get("military", {}).get("ground", 0) < 10:
                        transactions.append({
                            "type": "arms_transfer",
                            "receiver": target,
                            "details": {"unit_type": "ground", "count": 2},
                        })

        # Coin transfers for strategic purposes
        if self.role_id == "dealer" and c["economic"]["treasury"] > 20:
            # Fund allies
            for ally in ["ruthenia", "levantia"]:
                if self.ws.get_country_at_war(ally):
                    transactions.append({
                        "type": "coin_transfer",
                        "receiver": ally,
                        "details": {"amount": 2},
                    })

        return transactions

    # ===================================================================
    # OPEC DECISION
    # ===================================================================

    def decide_opec(self, c: dict, round_num: int) -> str:
        """OPEC+ production decision: low/normal/high."""
        if self.country_id == "sarmatia":
            # Sarmatia needs high prices for war revenue
            return "low"
        elif self.country_id == "solaria":
            # Wellspring balances market share vs. price
            oil_price = self.ws.oil_price
            if oil_price < 70:
                return "low"
            elif oil_price > 120:
                return "high"
            return "normal"
        elif self.country_id == "persia":
            # Persia under sanctions, produce whatever can sell
            return "normal"
        return "normal"

    # ===================================================================
    # NON-HOS ROLE ACTIONS
    # ===================================================================

    def decide_influence(self, c: dict, round_num: int) -> dict:
        """Non-head-of-state roles: influence country direction."""
        influence = {"advice": [], "slow_walk": [], "leak": []}

        if self.role_id == "rampart":
            # Military assessment: cautious
            if self.profile.get("caution_level", 0.5) > 0.6:
                influence["advice"].append({
                    "to": "helmsman",
                    "content": "military_not_ready" if round_num < 3 else "cautious_action",
                })
            # Slow-walk probability
            if random.random() < self.profile.get("slow_walk_probability", 0.3):
                influence["slow_walk"].append("delay_aggressive_orders")

        elif self.role_id == "tribune":
            # Opposition: investigate, block
            if round_num >= 1:
                influence["advice"].append({
                    "to": "public",
                    "content": "investigate_persia_war_authorization",
                })

        elif self.role_id == "compass":
            # Back-channel deals
            influence["advice"].append({
                "to": "pathfinder",
                "content": "sanctions_relief_opportunity",
            })

        elif self.role_id == "sage":
            # Activate if thresholds breached
            stab = c["political"]["stability"]
            sup = c["political"]["political_support"]
            if (stab < self.profile.get("activation_threshold_stability", 5) or
                    sup < self.profile.get("activation_threshold_support", 40)):
                influence["advice"].append({
                    "to": "helmsman",
                    "content": "party_conference_warning",
                    "severity": "critical",
                })

        return influence

    def decide_private_actions(self, c: dict, round_num: int) -> dict:
        """Private objectives that may conflict with country interest."""
        private = {"covert": [], "personal_deals": []}

        if self.role_id == "compass":
            # Back-channel to Western contacts
            if self.profile.get("western_asset_value", 0) > 0.5:
                private["personal_deals"].append({
                    "type": "back_channel",
                    "target": "western_contacts",
                    "purpose": "sanctions_relief_personal",
                })

        elif self.role_id == "circuit":
            # Protect foreign assets
            if self.profile.get("defection_risk", 0) > 0.1:
                private["personal_deals"].append({
                    "type": "asset_protection",
                    "target": "foreign_holdings",
                })

        return private

    # ===================================================================
    # NEGOTIATION SYSTEM
    # ===================================================================

    def negotiate(self, other_agent: "AIAgent",
                  world_state: WorldState) -> Optional[dict]:
        """Structured negotiation: propose, counter, accept/reject."""
        self.ws = world_state
        proposal = self.generate_proposal(other_agent)
        if not proposal:
            return None

        response = other_agent.evaluate_proposal(proposal)

        self.negotiation_history.append({
            "round": world_state.round_num,
            "partner": other_agent.role_id,
            "proposal": proposal,
            "response": "accepted" if response.accepted else
                        "counter" if response.counter else "rejected",
        })

        if response.accepted:
            return proposal.terms
        elif response.counter:
            counter_response = self.evaluate_counter(response.counter)
            if counter_response:
                return response.counter.terms
        return None

    def generate_proposal(self, other_agent: "AIAgent") -> Optional[Proposal]:
        """Generate a proposal based on relationship and objectives."""
        rel_score = self.relationships.get(other_agent.role_id, 0.0)
        deal_seeking = self.profile.get("deal_seeking", 0.5)

        # Don't propose to enemies unless deal-seeking
        if rel_score < -0.5 and deal_seeking < 0.5:
            return None

        # Build terms based on mutual interests
        terms = {}
        my_objectives = set(self.profile.get("objectives", []))
        their_country = other_agent.country_id

        # ROLE-SPECIFIC PROPOSALS
        # Columbia offers arms to Ruthenia
        if self.country_id == "columbia" and their_country == "ruthenia":
            terms["military_cooperation"] = True
            terms["arms_transfer"] = True
            terms["intelligence_sharing"] = True

        # Cathay offers sanctions evasion to Sarmatia
        elif self.country_id == "cathay" and their_country == "sarmatia":
            terms["economic_cooperation"] = True
            terms["sanctions_evasion_support"] = True
            terms["diplomatic_cover"] = True

        # Sarmatia seeks Columbia deal
        elif self.country_id == "sarmatia" and their_country == "columbia":
            terms["ceasefire"] = True
            terms["territorial_recognition"] = True
            terms["sanctions_reduction"] = True

        # Bharata plays both sides
        elif self.country_id == "bharata":
            terms["trade_agreement"] = True
            terms["tariff_reduction"] = True
            if their_country in ("columbia", "cathay"):
                terms["economic_cooperation"] = True

        # OPEC coordination
        elif (self.ws.countries.get(self.country_id, {}).get("economic", {}).get("opec_member") and
              self.ws.countries.get(their_country, {}).get("economic", {}).get("opec_member")):
            terms["opec_coordination"] = True
            terms["production_agreement"] = True

        # Persia seeks ceasefire / sanctions relief
        elif self.country_id == "persia" and their_country in ("columbia", "gallia", "teutonia"):
            terms["ceasefire"] = True
            terms["sanctions_reduction"] = True
            terms["gulf_gate_reopening"] = True

        # Generic complementary needs
        else:
            if self.ws.get_country_at_war(self.country_id):
                if rel_score > 0:
                    terms["military_cooperation"] = True
                    terms["intelligence_sharing"] = True
                else:
                    terms["ceasefire"] = True
                    terms["prisoner_exchange"] = True

            if "sanctions_relief" in str(my_objectives) or "economic_survival" in str(my_objectives):
                terms["sanctions_reduction"] = True
                terms["economic_cooperation"] = True

            if "economic_growth" in str(my_objectives) or "trade" in str(my_objectives):
                terms["tariff_reduction"] = True
                terms["trade_agreement"] = True

            # Everyone can propose trade
            if deal_seeking > 0.5 and rel_score > -0.3:
                terms["trade_agreement"] = True

        if not terms:
            return None

        return Proposal(
            proposer=self.role_id,
            target=other_agent.role_id,
            proposal_type="bilateral_deal",
            terms=terms,
            round_num=self.ws.round_num,
        )

    def evaluate_proposal(self, proposal: Proposal) -> Response:
        """Evaluate incoming proposal against interests."""
        score = self.score_proposal(proposal)
        accept_threshold = self.profile.get("acceptance_threshold", 0.5)
        reject_threshold = self.profile.get("rejection_threshold", 0.2)

        if score > accept_threshold:
            return Response(accepted=True, reason="Terms align with interests")
        elif score > reject_threshold:
            # Generate counter-proposal
            counter_terms = copy.deepcopy(proposal.terms)
            # Modify terms in our favor
            if "sanctions_reduction" in counter_terms:
                counter_terms["sanctions_reduction_level"] = 1  # less than full
            if "territorial_recognition" in counter_terms:
                counter_terms["territorial_recognition"] = False  # reject this term
                counter_terms["ceasefire_only"] = True

            counter = Proposal(
                proposer=self.role_id,
                target=proposal.proposer,
                proposal_type="counter_proposal",
                terms=counter_terms,
                round_num=self.ws.round_num,
            )
            return Response(counter=counter, reason="Partial alignment, counter-offering")
        else:
            return Response(rejected=True, reason="Terms conflict with core interests")

    def evaluate_counter(self, counter: Proposal) -> bool:
        """Evaluate a counter-proposal."""
        score = self.score_proposal(counter)
        threshold = self.profile.get("acceptance_threshold", 0.5) * 0.8  # lower bar for counters
        return score > threshold

    def score_proposal(self, proposal: Proposal) -> float:
        """Score a proposal from 0 to 1 based on alignment with objectives."""
        terms = proposal.terms
        my_objectives = self.profile.get("objectives", [])
        score = 0.0
        count = 0

        for key, value in terms.items():
            count += 1
            if key in ("military_cooperation", "intelligence_sharing"):
                if self.ws.get_country_at_war(self.country_id):
                    score += 0.8
                else:
                    score += 0.3
            elif key == "sanctions_reduction":
                if "sanctions_relief" in str(my_objectives) or "economic_survival" in str(my_objectives):
                    score += 0.9
                else:
                    score += 0.2
            elif key == "tariff_reduction":
                score += 0.5
            elif key == "trade_agreement":
                score += 0.4
            elif key == "ceasefire":
                if "survive" in str(my_objectives):
                    score += 0.7
                elif "war_victory" in str(my_objectives):
                    score += 0.2
                else:
                    score += 0.5
            elif key == "territorial_recognition":
                if self.role_id == "beacon":
                    score -= 0.5  # Beacon never accepts territorial concessions
                elif self.role_id == "pathfinder":
                    score += 0.9
                else:
                    score += 0.1
            else:
                score += 0.3

        return (score / max(count, 1))

    def choose_negotiation_target(self, world_state: WorldState) -> Optional[str]:
        """Pick someone to negotiate with this round."""
        deal_seeking = self.profile.get("deal_seeking", 0.5)
        # Higher base chance -- at least 40% even for low deal_seeking
        if random.random() > max(deal_seeking, 0.4):
            return None

        priorities = self.profile.get("negotiation_priority", [])
        if priorities:
            # Rotate through priorities based on round
            round_offset = world_state.round_num % max(len(priorities), 1)
            rotated = priorities[round_offset:] + priorities[:round_offset]
            for target_country in rotated:
                hos = world_state.get_head_of_state(target_country)
                if hos and hos["status"] == "active":
                    return hos["id"]

        # Fall back to any head of state with significant relationship
        sorted_rels = sorted(self.relationships.items(),
                             key=lambda x: abs(x[1]), reverse=True)
        for role_id, score in sorted_rels[:5]:
            role = world_state.roles.get(role_id, {})
            if role.get("status") == "active" and role.get("is_head_of_state"):
                return role_id

        # Last resort: random HoS
        all_hos = [r for r in world_state.roles.values()
                   if r.get("is_head_of_state") and r["status"] == "active"
                   and r["country_id"] != self.country_id]
        if all_hos:
            return random.choice(all_hos)["id"]

        return None


# ---------------------------------------------------------------------------
# AGENT FACTORY
# ---------------------------------------------------------------------------

def load_agents_from_seeds(world_state: WorldState,
                           overrides: Optional[dict] = None) -> Dict[str, AIAgent]:
    """Create all AI agents from role profiles.

    Returns dict of role_id -> AIAgent for all 37+ roles.
    """
    agents = {}
    overrides = overrides or {}

    # Team country roles
    for role_id, profile in ROLE_PROFILES.items():
        merged = copy.deepcopy(profile)
        if role_id in overrides:
            merged.update(overrides[role_id])
        country_id = merged["country"]
        agents[role_id] = AIAgent(role_id, country_id, merged, world_state)

    # Solo country roles
    for role_id, profile in SOLO_PROFILES.items():
        merged = copy.deepcopy(profile)
        merged["head_of_state"] = True  # solo = head of state
        merged.setdefault("acceptance_threshold", 0.5)
        merged.setdefault("rejection_threshold", 0.3)
        merged.setdefault("risk_tolerance", 0.5)
        if role_id in overrides:
            merged.update(overrides[role_id])
        country_id = merged["country"]
        agents[role_id] = AIAgent(role_id, country_id, merged, world_state)

    return agents
