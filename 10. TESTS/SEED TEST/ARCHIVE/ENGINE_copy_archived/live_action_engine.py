"""
TTT SEED — Live Action Engine
===============================
Real-time unilateral actions requiring calculation.
One party decides, engine resolves with dice/probability.

Handles: attacks, blockades, missile strikes, arrests,
         covert ops, propaganda, assassinations, coups.

Includes: Gulf Gate ground-based blockade mechanic.
          Air cannot break ground blockade — requires ground invasion.

Author: ATLAS (World Model Engineer)
Version: 2.0 (SEED)
"""

import random
import math
from typing import Dict, List, Optional, Tuple, Any

from world_state import (
    WorldState, UNIT_TYPES, CHOKEPOINTS,
    AI_LEVEL_COMBAT_BONUS, clamp,
)


# ---------------------------------------------------------------------------
# COVERT OPS PROBABILITY TABLES
# ---------------------------------------------------------------------------

COVERT_BASE_PROBABILITY = {
    "espionage": 0.60,
    "sabotage": 0.45,
    "cyber": 0.50,
    "disinformation": 0.55,
    "election_meddling": 0.40,
}

COVERT_DETECTION_BASE = {
    "espionage": 0.30,
    "sabotage": 0.40,
    "cyber": 0.35,
    "disinformation": 0.25,
    "election_meddling": 0.45,
}

# Countries with enhanced covert capabilities
INTELLIGENCE_POWERS = {"columbia", "cathay", "levantia", "albion", "sarmatia"}

# Max covert ops per round
MAX_COVERT_OPS_PER_ROUND = {
    "default": 2,
    "intelligence_power": 3,
}

# Amphibious assault ratios
AMPHIBIOUS_RATIO_DEFAULT = 3  # 3:1 needed
AMPHIBIOUS_RATIO_FORMOSA = 4  # 4:1 for Formosa

# Naval bombardment hit probability per unit
NAVAL_BOMBARDMENT_HIT_PROB = 0.10


class LiveActionEngine:
    """Processes real-time unilateral actions during rounds."""

    def __init__(self, world_state: WorldState):
        self.ws = world_state
        self.action_log: List[dict] = []
        self.covert_ops_this_round: Dict[str, int] = {}
        self.combat_results: List[dict] = []

    def new_round(self) -> None:
        """Reset per-round counters."""
        self.covert_ops_this_round = {}
        self.combat_results = []

    # -----------------------------------------------------------------------
    # COMBAT: ATTACK (RISK-style dice)
    # -----------------------------------------------------------------------

    def resolve_attack(self, attacker_country: str, defender_country: str,
                       zone: str, units: int,
                       origin_zone: Optional[str] = None) -> dict:
        """RISK combat with all modifiers.

        Rules:
        - Each unit pair rolls 1d6 + modifiers
        - Defender wins ties (defender advantage)
        - Morale modifier from stability
        - Tech modifier from AI level
        - Terrain modifier for defenders in home/capital zones
        - Amphibious: requires 3:1 (4:1 for Formosa), naval prerequisite
        - Must leave at least 1 unit in origin zone
        """
        result = {
            "type": "attack",
            "attacker": attacker_country,
            "defender": defender_country,
            "zone": zone,
            "origin_zone": origin_zone,
            "attacker_units_committed": units,
            "success": False,
        }

        # Validate
        zone_data = self.ws.zones.get(zone)
        if not zone_data:
            result["error"] = f"Zone {zone} does not exist"
            self.action_log.append(result)
            return result

        # Get defender forces in zone
        zone_forces = zone_data.get("forces", {})
        def_forces = zone_forces.get(defender_country, {})
        def_ground = def_forces.get("ground", 0)

        # Check for amphibious assault
        is_amphibious = self._is_amphibious_attack(origin_zone, zone)
        if is_amphibious:
            # Check naval prerequisite
            sea_zones = self._get_intervening_sea_zones(origin_zone, zone)
            for sz in sea_zones:
                att_naval = self.ws.get_naval_in_zone(sz, attacker_country)
                def_naval = sum(
                    f.get("naval", 0) for cid, f in self.ws.get_zone_forces(sz).items()
                    if cid != attacker_country
                )
                if att_naval <= def_naval:
                    result["error"] = f"Naval superiority required in {sz} for amphibious assault"
                    self.action_log.append(result)
                    return result

            # Check force ratio
            required_ratio = AMPHIBIOUS_RATIO_FORMOSA if zone == "g_formosa" else AMPHIBIOUS_RATIO_DEFAULT
            if def_ground > 0 and units < def_ground * required_ratio:
                result["error"] = (
                    f"Amphibious assault requires {required_ratio}:1 ratio. "
                    f"Need {def_ground * required_ratio} units, have {units}"
                )
                self.action_log.append(result)
                return result

        # Uncontested capture
        if def_ground == 0:
            self._transfer_zone_control(zone, attacker_country, units)
            result["success"] = True
            result["zone_captured"] = True
            result["attacker_losses"] = 0
            result["defender_losses"] = 0
            result["attacker_remaining"] = units
            result["defender_remaining"] = 0
            self._log_combat_event(result)
            return result

        # Build modifiers
        modifiers = self._build_combat_modifiers(
            attacker_country, defender_country, zone, is_amphibious
        )

        # Execute RISK dice combat
        a_losses = 0
        d_losses = 0
        pairs = min(units, def_ground)

        for _ in range(pairs):
            a_roll = random.randint(1, 6) + modifiers["attacker_total"]
            d_roll = random.randint(1, 6) + modifiers["defender_total"]
            if a_roll > d_roll:
                d_losses += 1
            else:
                a_losses += 1  # defender wins ties

        # Apply losses
        att_remaining = units - a_losses
        def_remaining = def_ground - d_losses

        # Update zone forces
        if defender_country in zone_forces:
            zone_forces[defender_country]["ground"] = max(def_remaining, 0)
        # Update country military totals
        att_mil = self.ws.countries[attacker_country]["military"]
        att_mil["ground"] = max(att_mil.get("ground", 0) - a_losses, 0)
        def_mil = self.ws.countries[defender_country]["military"]
        def_mil["ground"] = max(def_mil.get("ground", 0) - d_losses, 0)

        # Zone capture check
        zone_captured = def_remaining <= 0 and att_remaining > 0
        if zone_captured:
            self._transfer_zone_control(zone, attacker_country, att_remaining)

        # Update war tiredness
        self.ws.countries[attacker_country]["political"]["war_tiredness"] += 0.5
        self.ws.countries[defender_country]["political"]["war_tiredness"] += 0.5

        result.update({
            "success": True,
            "zone_captured": zone_captured,
            "attacker_losses": a_losses,
            "defender_losses": d_losses,
            "attacker_remaining": att_remaining,
            "defender_remaining": def_remaining,
            "modifiers": modifiers,
            "is_amphibious": is_amphibious,
        })

        self._log_combat_event(result)
        self.combat_results.append(result)
        return result

    # -----------------------------------------------------------------------
    # BLOCKADE
    # -----------------------------------------------------------------------

    def resolve_blockade(self, country: str, zone: str) -> dict:
        """Naval blockade -- check minimum force requirements.

        Gulf Gate special mechanic:
        - Ground-based blockade: if a country holds ground units on me_gulf_gate,
          air strikes CANNOT break the blockade. Only ground invasion can.
        - Naval blockade: requires at least 1 naval unit in the sea zone.
        """
        result = {
            "type": "blockade",
            "country": country,
            "zone": zone,
            "success": False,
        }

        # Check for ground blockade (Gulf Gate)
        if zone == "cp_gulf_gate":
            zone_forces = self.ws.get_zone_forces(zone)
            country_forces = zone_forces.get(country, {})
            ground = country_forces.get("ground", 0)
            naval = country_forces.get("naval", 0)

            if ground >= 1:
                # Ground-based blockade -- air can't break it
                self.ws.ground_blockades["gulf_gate"] = {
                    "controller": country,
                    "ground_units": ground,
                    "naval_units": naval,
                    "breakable_by_air": False,
                    "requires_ground_invasion": True,
                }
                self.ws.chokepoint_status["gulf_gate_ground"] = "blocked"
                result["success"] = True
                result["blockade_type"] = "ground"
                result["note"] = (
                    "Ground-based Gulf Gate blockade. Air strikes cannot break this. "
                    "Requires ground invasion of me_gulf_gate zone."
                )
                self._log_action(result)
                return result

        # Standard naval blockade
        zone_forces = self.ws.get_zone_forces(zone)
        country_naval = zone_forces.get(country, {}).get("naval", 0)

        if country_naval < 1:
            result["error"] = f"{country} has no naval units in {zone}"
            self._log_action(result)
            return result

        # Apply blockade to relevant chokepoint
        for cp_name, cp_data in CHOKEPOINTS.items():
            if cp_data["zone"] == zone:
                self.ws.chokepoint_status[cp_name] = "blocked"
                result["success"] = True
                result["blockade_type"] = "naval"
                result["chokepoint"] = cp_name
                break
        else:
            # Not a chokepoint, but zone is blocked
            result["success"] = True
            result["blockade_type"] = "zone_control"

        self._log_action(result)
        return result

    # -----------------------------------------------------------------------
    # MISSILE STRIKE
    # -----------------------------------------------------------------------

    def resolve_missile_strike(self, launcher: str, target_zone: str,
                               warhead_type: str = "conventional") -> dict:
        """Strategic missile -- global alert, 3 confirmations for nuclear.

        Warhead types:
        - conventional: 10% of ground units destroyed
        - nuclear_l1: 50% troops destroyed, economy -2 coins
        - nuclear_l2: 30% economic capacity destroyed, 50% military,
                      leader survival 1/6, global stability shock
        """
        result = {
            "type": "missile_strike",
            "launcher": launcher,
            "target_zone": target_zone,
            "warhead_type": warhead_type,
            "success": False,
        }

        c = self.ws.countries.get(launcher)
        if not c:
            result["error"] = f"Country {launcher} not found"
            self._log_action(result)
            return result

        mil = c["military"]
        if mil.get("strategic_missiles", 0) <= 0:
            result["error"] = f"{launcher} has no strategic missiles"
            self._log_action(result)
            return result

        # Nuclear warhead checks
        is_nuclear = warhead_type.startswith("nuclear")
        if is_nuclear:
            nuc_level = c["technology"]["nuclear_level"]
            if nuc_level < 1:
                result["error"] = f"{launcher} lacks nuclear capability (L{nuc_level})"
                self._log_action(result)
                return result

        # Consume missile
        mil["strategic_missiles"] -= 1

        # Air defense interception
        zone_forces = self.ws.get_zone_forces(target_zone)
        total_ad = sum(
            f.get("air_defense", 0)
            for cid, f in zone_forces.items()
            if cid != launcher
        )
        intercepted = False
        # Each AD unit can intercept up to 3 incoming missiles
        intercept_attempts = min(total_ad * 3, 5)
        for _ in range(intercept_attempts):
            if random.random() < 0.30:
                intercepted = True
                break

        if intercepted:
            result["intercepted"] = True
            result["success"] = False
            result["note"] = "Missile intercepted by air defense"
            self._log_action(result)
            # Global alert still fires
            self.ws.log_event({
                "type": "global_alert",
                "subtype": "strategic_missile_launch",
                "launcher": launcher,
                "target_zone": target_zone,
                "outcome": "intercepted",
            })
            return result

        result["success"] = True
        result["intercepted"] = False

        # Apply damage
        if warhead_type == "nuclear_l2" or (is_nuclear and c["technology"]["nuclear_level"] >= 2):
            self._apply_nuclear_l2(launcher, target_zone, result)
        elif warhead_type == "nuclear_l1" or is_nuclear:
            self._apply_nuclear_l1(launcher, target_zone, result)
        else:
            self._apply_conventional_strike(launcher, target_zone, result)

        # Global alert
        self.ws.log_event({
            "type": "global_alert",
            "subtype": "strategic_missile_launch",
            "launcher": launcher,
            "target_zone": target_zone,
            "warhead": warhead_type,
            "outcome": "hit",
        })

        self._log_action(result)
        return result

    def _apply_conventional_strike(self, launcher: str, zone: str, result: dict) -> None:
        zone_forces = self.ws.get_zone_forces(zone)
        total_destroyed = 0
        for cid, forces in zone_forces.items():
            if cid == launcher:
                continue
            ground = forces.get("ground", 0)
            losses = max(1, int(ground * 0.10))
            forces["ground"] = max(ground - losses, 0)
            if cid in self.ws.countries:
                self.ws.countries[cid]["military"]["ground"] = max(
                    self.ws.countries[cid]["military"]["ground"] - losses, 0)
            total_destroyed += losses
        result["ground_destroyed"] = total_destroyed

    def _apply_nuclear_l1(self, launcher: str, zone: str, result: dict) -> None:
        """Tactical nuclear: 50% troops destroyed, economy -2 coins."""
        self.ws.nuclear_used_this_sim = True
        zone_forces = self.ws.get_zone_forces(zone)
        total_destroyed = 0
        affected_countries = []

        for cid, forces in zone_forces.items():
            if cid == launcher:
                continue
            ground = forces.get("ground", 0)
            losses = int(ground * 0.50)
            forces["ground"] = max(ground - losses, 0)
            if cid in self.ws.countries:
                self.ws.countries[cid]["military"]["ground"] = max(
                    self.ws.countries[cid]["military"]["ground"] - losses, 0)
                self.ws.countries[cid]["economic"]["treasury"] = max(
                    self.ws.countries[cid]["economic"]["treasury"] - 2, 0)
            total_destroyed += losses
            affected_countries.append(cid)

        result["ground_destroyed"] = total_destroyed
        result["affected_countries"] = affected_countries
        result["nuclear_level"] = 1

    def _apply_nuclear_l2(self, launcher: str, zone: str, result: dict) -> None:
        """Strategic nuclear: 30% economic capacity, 50% military, leader survival 1/6."""
        self.ws.nuclear_used_this_sim = True
        zone_forces = self.ws.get_zone_forces(zone)
        affected_countries = []

        for cid, forces in zone_forces.items():
            if cid == launcher:
                continue
            # 50% military destroyed
            for ut in ["ground", "naval", "tactical_air"]:
                current = forces.get(ut, 0)
                losses = int(current * 0.50)
                forces[ut] = max(current - losses, 0)
                if cid in self.ws.countries:
                    self.ws.countries[cid]["military"][ut] = max(
                        self.ws.countries[cid]["military"].get(ut, 0) - losses, 0)

            # 30% economic capacity destroyed
            if cid in self.ws.countries:
                self.ws.countries[cid]["economic"]["gdp"] *= 0.70
                # Leader survival: 1/6
                leader_survives = random.randint(1, 6) >= 2  # survives on 2-6
                if not leader_survives:
                    result[f"leader_killed_{cid}"] = True
                    hos = self.ws.get_head_of_state(cid)
                    if hos:
                        hos["status"] = "dead"
            affected_countries.append(cid)

        # Global stability shock: every country loses 2 stability
        for cid2, c2 in self.ws.countries.items():
            c2["political"]["stability"] = max(c2["political"]["stability"] - 2, 1)

        result["affected_countries"] = affected_countries
        result["nuclear_level"] = 2
        result["global_stability_shock"] = True

    # -----------------------------------------------------------------------
    # COVERT OPERATIONS
    # -----------------------------------------------------------------------

    def resolve_covert_op(self, country: str, op_type: str,
                          target: str, details: Optional[dict] = None) -> dict:
        """Espionage, sabotage, cyber, disinformation -- probability tables.

        Rules:
        - Limited per round per country (2 default, 3 for intelligence powers)
        - Detection probability escalates with repeated ops against same target
        - AI level improves success probability
        """
        result = {
            "type": "covert_op",
            "op_type": op_type,
            "country": country,
            "target": target,
            "success": False,
            "detected": False,
        }

        # Check op limit
        max_ops = MAX_COVERT_OPS_PER_ROUND.get(
            "intelligence_power" if country in INTELLIGENCE_POWERS else "default",
            2
        )
        current_ops = self.covert_ops_this_round.get(country, 0)
        if current_ops >= max_ops:
            result["error"] = f"{country} has reached covert op limit ({max_ops}) this round"
            self._log_action(result)
            return result

        self.covert_ops_this_round[country] = current_ops + 1

        # Calculate success probability
        base_prob = COVERT_BASE_PROBABILITY.get(op_type, 0.50)
        ai_level = self.ws.countries.get(country, {}).get("technology", {}).get("ai_level", 0)
        prob = base_prob + ai_level * 0.05

        # Intelligence power bonus
        if country in INTELLIGENCE_POWERS:
            prob += 0.05

        # Repeated ops penalty
        prev_ops_against_target = sum(
            1 for e in self.ws.events_log
            if e.get("type") == "covert_op"
            and e.get("country") == country
            and e.get("target") == target
        )
        prob -= prev_ops_against_target * 0.05
        prob = clamp(prob, 0.05, 0.95)

        # Roll for success
        success = random.random() < prob
        result["success"] = success
        result["success_probability"] = round(prob, 3)

        # Roll for detection
        detect_base = COVERT_DETECTION_BASE.get(op_type, 0.40)
        detect_prob = detect_base + prev_ops_against_target * 0.10
        detect_prob = clamp(detect_prob, 0.10, 0.90)
        detected = random.random() < detect_prob
        result["detected"] = detected
        result["detection_probability"] = round(detect_prob, 3)

        # Apply effects if successful
        if success and target in self.ws.countries:
            tc = self.ws.countries[target]
            if op_type == "sabotage":
                damage = tc["economic"]["gdp"] * 0.02
                tc["economic"]["gdp"] = max(tc["economic"]["gdp"] - damage, 0.01)
                result["damage"] = round(damage, 2)
            elif op_type == "cyber":
                damage = tc["economic"]["gdp"] * 0.01
                tc["economic"]["gdp"] = max(tc["economic"]["gdp"] - damage, 0.01)
                result["damage"] = round(damage, 2)
            elif op_type == "disinformation":
                tc["political"]["stability"] = max(tc["political"]["stability"] - 0.3, 1)
                tc["political"]["political_support"] = max(
                    tc["political"]["political_support"] - 2, 0)
                result["stability_impact"] = -0.3
                result["support_impact"] = -2
            elif op_type == "election_meddling":
                tc["political"]["political_support"] = max(
                    tc["political"]["political_support"] - 3, 0)
                result["support_impact"] = -3
            elif op_type == "espionage":
                # Gather intelligence - return partial world state info
                result["intelligence"] = self._gather_intelligence(target, details)

        self.ws.log_event({
            "type": "covert_op",
            "op_type": op_type,
            "country": country,
            "target": target,
            "success": success,
            "detected": detected,
        })
        self._log_action(result)
        return result

    def _gather_intelligence(self, target: str, details: Optional[dict] = None) -> dict:
        """Generate intelligence report for espionage operation."""
        tc = self.ws.countries.get(target, {})
        # Partial and possibly inaccurate information
        noise = random.uniform(0.85, 1.15)
        intel = {
            "gdp_estimate": round(tc.get("economic", {}).get("gdp", 0) * noise, 1),
            "stability_estimate": round(
                tc.get("political", {}).get("stability", 5) * noise, 1),
            "military_ground_estimate": int(
                tc.get("military", {}).get("ground", 0) * noise),
            "military_naval_estimate": int(
                tc.get("military", {}).get("naval", 0) * noise),
            "nuclear_level": tc.get("technology", {}).get("nuclear_level", 0),
        }
        return intel

    # -----------------------------------------------------------------------
    # ARREST
    # -----------------------------------------------------------------------

    def resolve_arrest(self, country: str, target_role: str) -> dict:
        """Instant arrest, own soil only."""
        result = {
            "type": "arrest",
            "country": country,
            "target_role": target_role,
            "success": False,
        }

        role = self.ws.roles.get(target_role)
        if not role:
            result["error"] = f"Role {target_role} not found"
            self._log_action(result)
            return result

        # Own soil only
        if role["country_id"] != country:
            result["error"] = f"Cannot arrest {target_role}: not on {country} soil"
            self._log_action(result)
            return result

        # Execute arrest
        role["status"] = "arrested"
        result["success"] = True
        result["note"] = f"{role['character_name']} arrested by {country}"

        # Political support cost
        c = self.ws.countries.get(country, {})
        regime = c.get("political", {}).get("regime_type", "democracy")
        support_cost = 3 if regime == "democracy" else 5
        c["political"]["political_support"] = max(
            c["political"]["political_support"] - support_cost, 0)
        c["political"]["stability"] = max(
            c["political"]["stability"] - 1, 1)

        result["support_cost"] = support_cost

        self.ws.log_event({
            "type": "arrest",
            "country": country,
            "target_role": target_role,
            "character_name": role["character_name"],
        })
        self._log_action(result)
        return result

    # -----------------------------------------------------------------------
    # PROPAGANDA
    # -----------------------------------------------------------------------

    def resolve_propaganda(self, country: str, coins_spent: float) -> dict:
        """Propaganda campaign with diminishing returns."""
        result = {
            "type": "propaganda",
            "country": country,
            "coins_spent": coins_spent,
        }

        c = self.ws.countries.get(country)
        if not c:
            result["error"] = f"Country {country} not found"
            self._log_action(result)
            return result

        # Deduct coins
        treasury = c["economic"]["treasury"]
        actual_spent = min(coins_spent, treasury)
        c["economic"]["treasury"] -= actual_spent

        # Diminishing returns via logarithm
        gdp = c["economic"]["gdp"]
        if gdp > 0:
            intensity = actual_spent / gdp
        else:
            intensity = actual_spent

        boost = math.log1p(intensity * 100) * 3.0
        boost = min(boost, 10.0)

        # AI tech L3+ auto-boosts propaganda
        ai_level = c["technology"]["ai_level"]
        if ai_level >= 3:
            boost *= 1.5

        # Negative returns if overused (more than 3% of GDP)
        if gdp > 0 and actual_spent / gdp > 0.03:
            boost *= 0.5  # halved effectiveness when oversaturated

        c["political"]["political_support"] = clamp(
            c["political"]["political_support"] + boost, 0, 100)

        result["actual_spent"] = actual_spent
        result["support_boost"] = round(boost, 2)
        result["new_support"] = round(c["political"]["political_support"], 2)

        self.ws.log_event({
            "type": "propaganda",
            "country": country,
            "coins_spent": actual_spent,
            "boost": round(boost, 2),
        })
        self._log_action(result)
        return result

    # -----------------------------------------------------------------------
    # ASSASSINATION
    # -----------------------------------------------------------------------

    def resolve_assassination(self, country: str, target_role: str) -> dict:
        """50% base +/- modifiers. Detection 60-80%."""
        result = {
            "type": "assassination",
            "country": country,
            "target_role": target_role,
            "success": False,
            "detected": False,
        }

        role = self.ws.roles.get(target_role)
        if not role:
            result["error"] = f"Role {target_role} not found"
            self._log_action(result)
            return result

        # Base probability
        prob = 0.50
        # Intelligence power bonus
        if country in INTELLIGENCE_POWERS:
            prob += 0.10
        # AI level bonus
        ai_level = self.ws.countries.get(country, {}).get(
            "technology", {}).get("ai_level", 0)
        prob += ai_level * 0.03

        success = random.random() < prob
        detected = random.random() < random.uniform(0.60, 0.80)

        result["success"] = success
        result["detected"] = detected
        result["probability"] = round(prob, 3)

        if success:
            # Target killed unless survival dice saves them
            survival = random.randint(1, 6)
            if survival >= 4:  # survive on 4-6
                result["target_survived"] = True
                result["note"] = f"{role['character_name']} survived assassination attempt"
            else:
                role["status"] = "dead"
                result["target_survived"] = False
                result["note"] = f"{role['character_name']} killed"

                # Martyr effect: boost political support of target's country
                target_country = role["country_id"]
                if target_country in self.ws.countries:
                    tc = self.ws.countries[target_country]
                    tc["political"]["political_support"] = clamp(
                        tc["political"]["political_support"] + 15, 0, 100)
                    result["martyr_effect"] = 15

        self.ws.log_event({
            "type": "assassination",
            "country": country,
            "target_role": target_role,
            "success": success,
            "detected": detected,
        })
        self._log_action(result)
        return result

    # -----------------------------------------------------------------------
    # COUP ATTEMPT
    # -----------------------------------------------------------------------

    def resolve_coup(self, country: str, plotters: List[str]) -> dict:
        """Coup attempt probability based on stability, support, conspirators.

        Requires: at least one plotter with military/security access.
        Success probability = f(stability, support, co-conspirators, military units).
        """
        result = {
            "type": "coup",
            "country": country,
            "plotters": plotters,
            "success": False,
        }

        c = self.ws.countries.get(country)
        if not c:
            result["error"] = f"Country {country} not found"
            self._log_action(result)
            return result

        # Check for military plotter
        has_military = any(
            self.ws.roles.get(p, {}).get("is_military_chief", False)
            for p in plotters
        )
        if not has_military:
            result["error"] = "Coup requires at least one plotter with military access"
            self._log_action(result)
            return result

        pol = c["political"]
        stability = pol["stability"]
        support = pol["political_support"]

        # Base probability
        prob = 0.05
        if stability < 5:
            prob += (5 - stability) * 0.05
        if support < 40:
            prob += (40 - support) / 100.0 * 0.15
        prob += len(plotters) * 0.05
        if has_military:
            prob += 0.10

        prob = clamp(prob, 0.0, 0.85)

        success = random.random() < prob
        result["success"] = success
        result["probability"] = round(prob, 3)

        if success:
            # New leader: first military plotter
            new_leader_id = None
            for p in plotters:
                role = self.ws.roles.get(p)
                if role and role["is_military_chief"]:
                    new_leader_id = p
                    break
            if not new_leader_id:
                new_leader_id = plotters[0]

            # Remove old head of state
            old_hos = self.ws.get_head_of_state(country)
            if old_hos:
                old_hos["status"] = "arrested"
                old_hos["is_head_of_state"] = False

            # Install new leader
            new_role = self.ws.roles.get(new_leader_id)
            if new_role:
                new_role["is_head_of_state"] = True
                result["new_leader"] = new_leader_id

            pol["stability"] = max(stability - 2, 1)
            pol["political_support"] = max(support - 15, 0)
            result["note"] = f"Coup successful. {new_leader_id} takes power."
        else:
            # Failed coup: plotters arrested
            for p in plotters:
                role = self.ws.roles.get(p)
                if role:
                    role["status"] = "arrested"
            pol["stability"] = max(stability - 1, 1)
            result["note"] = "Coup failed. Plotters arrested."

        self.ws.log_event({
            "type": "coup",
            "country": country,
            "plotters": plotters,
            "success": success,
        })
        self._log_action(result)
        return result

    # -----------------------------------------------------------------------
    # NAVAL BOMBARDMENT
    # -----------------------------------------------------------------------

    def resolve_naval_bombardment(self, country: str, sea_zone: str,
                                  target_land_zone: str) -> dict:
        """Each naval unit adjacent to land can bombard once per round.
        10% chance per unit of destroying one random ground unit."""
        result = {
            "type": "naval_bombardment",
            "country": country,
            "sea_zone": sea_zone,
            "target_zone": target_land_zone,
            "units_destroyed": 0,
        }

        # Check adjacency
        if not self.ws.is_adjacent(sea_zone, target_land_zone):
            result["error"] = f"{sea_zone} not adjacent to {target_land_zone}"
            self._log_action(result)
            return result

        naval_units = self.ws.get_naval_in_zone(sea_zone, country)
        if naval_units <= 0:
            result["error"] = f"{country} has no naval units in {sea_zone}"
            self._log_action(result)
            return result

        destroyed = 0
        for _ in range(naval_units):
            if random.random() < NAVAL_BOMBARDMENT_HIT_PROB:
                destroyed += 1

        # Apply damage
        if destroyed > 0:
            zone_forces = self.ws.get_zone_forces(target_land_zone)
            for cid, forces in zone_forces.items():
                if cid == country:
                    continue
                ground = forces.get("ground", 0)
                actual_loss = min(destroyed, ground)
                forces["ground"] = max(ground - actual_loss, 0)
                if cid in self.ws.countries:
                    self.ws.countries[cid]["military"]["ground"] = max(
                        self.ws.countries[cid]["military"]["ground"] - actual_loss, 0)
                destroyed -= actual_loss
                if destroyed <= 0:
                    break

        result["units_destroyed"] = destroyed
        self._log_action(result)
        return result

    # -----------------------------------------------------------------------
    # HELPERS
    # -----------------------------------------------------------------------

    def _build_combat_modifiers(self, attacker: str, defender: str,
                                 zone: str, is_amphibious: bool) -> dict:
        att_c = self.ws.countries.get(attacker, {})
        def_c = self.ws.countries.get(defender, {})

        att_ai = att_c.get("technology", {}).get("ai_level", 0)
        def_ai = def_c.get("technology", {}).get("ai_level", 0)

        att_stab = att_c.get("political", {}).get("stability", 5)
        def_stab = def_c.get("political", {}).get("stability", 5)
        att_morale = max((att_stab - 5) * 0.5, -2)
        def_morale = max((def_stab - 5) * 0.5, -2)

        # Terrain bonus for defender
        terrain = 0
        zone_data = self.ws.zones.get(zone, {})
        if zone_data.get("type") in ("land_home",):
            terrain = 1
        if "capital" in zone or "core" in zone:
            terrain = 2

        # Amphibious penalty
        amphibious_penalty = -1 if is_amphibious else 0

        att_total = (AI_LEVEL_COMBAT_BONUS.get(att_ai, 0) +
                     att_morale + amphibious_penalty)
        def_total = (AI_LEVEL_COMBAT_BONUS.get(def_ai, 0) +
                     def_morale + terrain)

        return {
            "attacker_tech": AI_LEVEL_COMBAT_BONUS.get(att_ai, 0),
            "attacker_morale": att_morale,
            "amphibious_penalty": amphibious_penalty,
            "defender_tech": AI_LEVEL_COMBAT_BONUS.get(def_ai, 0),
            "defender_morale": def_morale,
            "terrain": terrain,
            "attacker_total": att_total,
            "defender_total": def_total,
        }

    def _is_amphibious_attack(self, origin_zone: Optional[str],
                               target_zone: str) -> bool:
        """Determine if an attack is amphibious (sea-to-land)."""
        if not origin_zone:
            return False
        origin_data = self.ws.zones.get(origin_zone, {})
        target_data = self.ws.zones.get(target_zone, {})
        if origin_data.get("type", "").startswith("sea") and not target_data.get("type", "").startswith("sea"):
            return True
        # Check if connection type is land_sea
        adj = self.ws.zone_adjacency.get(origin_zone, [])
        for a in adj:
            if a["zone"] == target_zone and a["type"] == "land_sea":
                # If attacker is in a sea zone attacking a land zone
                if origin_data.get("type", "").startswith("sea"):
                    return True
        return False

    def _get_intervening_sea_zones(self, origin: Optional[str],
                                    target: str) -> List[str]:
        """Get sea zones between origin and target for amphibious checks."""
        if not origin:
            return []
        sea_zones = []
        origin_adj = self.ws.zone_adjacency.get(origin, [])
        for a in origin_adj:
            if self.ws.zones.get(a["zone"], {}).get("type", "").startswith("sea"):
                target_adj = self.ws.zone_adjacency.get(a["zone"], [])
                if any(ta["zone"] == target for ta in target_adj):
                    sea_zones.append(a["zone"])
        if not sea_zones and origin:
            # Direct sea-to-land
            origin_data = self.ws.zones.get(origin, {})
            if origin_data.get("type", "").startswith("sea"):
                sea_zones.append(origin)
        return sea_zones

    def _transfer_zone_control(self, zone_id: str, new_owner: str,
                                units: int) -> None:
        zone = self.ws.zones.get(zone_id, {})
        zone["forces"] = {new_owner: {"ground": units}}
        zone["owner"] = new_owner

    def _log_combat_event(self, result: dict) -> None:
        self.action_log.append(result)
        self.ws.log_event({
            "type": "combat",
            "attacker": result.get("attacker"),
            "defender": result.get("defender"),
            "zone": result.get("zone"),
            "zone_captured": result.get("zone_captured", False),
            "attacker_losses": result.get("attacker_losses", 0),
            "defender_losses": result.get("defender_losses", 0),
        })

    def _log_action(self, result: dict) -> None:
        self.action_log.append(result)
