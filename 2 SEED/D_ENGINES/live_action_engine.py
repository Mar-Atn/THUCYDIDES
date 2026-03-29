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
INTELLIGENCE_POWERS = {"columbia", "cathay", "levantia", "albion", "nordostan"}

# Max covert ops per round
MAX_COVERT_OPS_PER_ROUND = {
    "default": 2,
    "intelligence_power": 3,
}

# Amphibious assault ratios
AMPHIBIOUS_RATIO_DEFAULT = 3  # 3:1 needed
AMPHIBIOUS_RATIO_FORMOSA = 3  # 3:1 for Formosa (reduced from 4:1 — still very hard)

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
        """RISK combat with simplified integer modifiers (ACTION REVIEW 2026-03-30).

        Rules:
        - Each unit pair rolls 1d6 + modifiers
        - Attacker needs >= defender + 1 to win (ties = defender holds)
        - Simplified modifiers: AI L4 (+1 random), low morale (-1),
          die hard (+1 def), amphibious (-1 att), air support (+1 def binary)
        - REMOVED: naval support, militia modifier, home territory, capital,
          scaled air/morale, 3:1 amphibious ratio
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

        # Check for amphibious assault (simplified: -1 modifier replaces ratio requirement)
        is_amphibious = self._is_amphibious_attack(origin_zone, zone)

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
            if a_roll >= d_roll + 1:  # attacker needs >= defender + 1
                d_losses += 1
            else:
                a_losses += 1  # defender wins ties and +0 draws

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

    def resolve_blockade(self, country: str, zone: str,
                         level: str = "full") -> dict:
        """Ground-force blockade at chokepoints (ACTION REVIEW 2026-03-30).

        Key changes:
        - Blockade requires GROUND FORCES at chokepoint (not naval superiority)
        - level: "full" or "partial"
        - Formosa special: full requires naval in 3+ surrounding sea zones.
          1 friendly ship at any adjacent zone = automatic downgrade to partial.

        Breaking a blockade: destroy ALL military units at chokepoint,
        or blocker lifts voluntarily.
        """
        result = {
            "type": "blockade",
            "country": country,
            "zone": zone,
            "level": level,
            "success": False,
        }

        if level not in ("full", "partial"):
            result["error"] = f"Invalid blockade level: {level}. Must be 'full' or 'partial'."
            self._log_action(result)
            return result

        # --- FORMOSA SPECIAL BLOCKADE ---
        if zone in ("formosa", "g_formosa"):
            return self._resolve_formosa_blockade(country, zone, level, result)

        # --- STANDARD CHOKEPOINT BLOCKADE (ground forces required) ---
        zone_forces = self.ws.get_zone_forces(zone)
        country_forces = zone_forces.get(country, {})
        ground = country_forces.get("ground", 0)

        if ground < 1:
            result["error"] = (
                f"{country} has no ground forces at {zone}. "
                "Ground forces required for blockade."
            )
            self._log_action(result)
            return result

        # Ground blockade established
        self.ws.ground_blockades[zone] = {
            "controller": country,
            "ground_units": ground,
            "level": level,
            "breakable_by_air": False,
            "requires_ground_invasion": True,
        }

        # Apply to chokepoint status
        for cp_name, cp_data in CHOKEPOINTS.items():
            if cp_data["zone"] == zone:
                self.ws.chokepoint_status[cp_name] = "blocked"
                result["chokepoint"] = cp_name
                break

        self.ws.active_blockades[zone] = {
            "controller": country,
            "level": level,
            "type": "ground",
        }

        result["success"] = True
        result["blockade_type"] = "ground"
        result["blockade_level"] = level
        result["note"] = (
            f"Ground blockade at {zone} ({level}). "
            "Air strikes cannot break — requires ground invasion or voluntary lift."
        )
        self._log_action(result)
        return result

    def _resolve_formosa_blockade(self, country: str, zone: str,
                                   level: str, result: dict) -> dict:
        """Formosa special blockade rules.

        Full blockade: requires naval units in 3+ surrounding sea zones.
        Any 1 friendly (to Formosa) ship at any adjacent zone = automatic
        downgrade to partial. Partial = strait only.
        """
        # Get adjacent sea zones around Formosa
        adjacent = self.ws.get_adjacent_zones(zone)
        sea_zones = [a["zone"] for a in adjacent
                     if self.ws.zones.get(a["zone"], {}).get("type", "").startswith("sea")]

        # Count how many sea zones the blocker has naval presence in
        zones_with_naval = 0
        for sz in sea_zones:
            blocker_naval = self.ws.get_naval_in_zone(sz, country)
            if blocker_naval > 0:
                zones_with_naval += 1

        if level == "full":
            if zones_with_naval < 3:
                result["error"] = (
                    f"Formosa full blockade requires naval in 3+ surrounding zones. "
                    f"{country} has naval in {zones_with_naval} zones."
                )
                self._log_action(result)
                return result

            # Check for any friendly (to Formosa) ship in adjacent zones
            # that would auto-downgrade to partial
            formosa_owner = self.ws.zones.get(zone, {}).get("owner", "formosa")
            friendly_ship_present = False
            for sz in sea_zones:
                sz_forces = self.ws.get_zone_forces(sz)
                for cid, forces in sz_forces.items():
                    if cid == country:
                        continue  # skip the blocker
                    naval = forces.get("naval", 0)
                    if naval > 0 and cid != country:
                        # Any non-blocker ship = friendly to Formosa for this purpose
                        friendly_ship_present = True
                        break
                if friendly_ship_present:
                    break

            if friendly_ship_present:
                level = "partial"
                result["auto_downgraded"] = True
                result["downgrade_reason"] = (
                    "Friendly ship detected at adjacent zone — "
                    "full blockade automatically downgraded to partial"
                )

        # Establish blockade
        self.ws.active_blockades["formosa"] = {
            "controller": country,
            "level": level,
            "type": "naval",
        }
        self.ws.formosa_blockade = True
        self.ws.chokepoint_status["taiwan_strait"] = "blocked"

        result["success"] = True
        result["blockade_type"] = "naval"
        result["blockade_level"] = level
        result["level"] = level  # update in case downgraded
        result["chokepoint"] = "taiwan_strait"
        result["note"] = (
            f"Formosa blockade ({level}). "
            + ("Strait only — partial." if level == "partial"
               else "Full naval encirclement.")
        )
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
        if mil.get("strategic_missile", 0) <= 0:
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
        mil["strategic_missile"] -= 1

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
                          target: str, role_id: str = None,
                          details: Optional[dict] = None) -> dict:
        """Intelligence, sabotage, cyber, disinformation, election meddling.

        Rules (updated 2026-03-30 per action review):
        - Per-INDIVIDUAL card pools (from roles.csv: intelligence_pool, sabotage_cards, etc.)
        - Each card consumed permanently — never recovers
        - Intelligence requests ALWAYS return an answer (accuracy varies)
        - Failed ops return low-accuracy info (not nothing)
        - Detection and attribution are SEPARATE events
        """
        result = {
            "type": "covert_op",
            "op_type": op_type,
            "country": country,
            "target": target,
            "role_id": role_id,
            "success": False,
            "detected": False,
            "attributed": False,
        }

        # Check per-individual card pool
        card_field_map = {
            "espionage": "intelligence_pool",
            "intelligence": "intelligence_pool",
            "sabotage": "sabotage_cards",
            "cyber": "cyber_cards",
            "disinformation": "disinfo_cards",
            "election_meddling": "election_meddling_cards",
        }
        card_field = card_field_map.get(op_type, "intelligence_pool")

        if role_id:
            role = self.ws.get_role(role_id)
            if role:
                remaining = role.get(card_field, 0)
                if remaining <= 0:
                    result["error"] = f"{role_id} has no {op_type} cards remaining"
                    self._log_action(result)
                    return result
                # Consume the card
                role[card_field] = remaining - 1
        else:
            # Fallback: country-level limit (legacy compatibility)
            max_ops = 3
            current_ops = self.covert_ops_this_round.get(country, 0)
            if current_ops >= max_ops:
                result["error"] = f"{country} has reached covert op limit this round"
                self._log_action(result)
                return result
            self.covert_ops_this_round[country] = current_ops + 1

        # Calculate success probability
        base_prob = COVERT_BASE_PROBABILITY.get(op_type, 0.50)
        ai_level = self.ws.countries.get(country, {}).get("technology", {}).get("ai_level", 0)
        prob = base_prob + ai_level * 0.05

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

        # Roll for detection (target learns SOMETHING happened)
        detect_base = COVERT_DETECTION_BASE.get(op_type, 0.40)
        detect_prob = detect_base + prev_ops_against_target * 0.10
        detect_prob = clamp(detect_prob, 0.10, 0.90)
        detected = random.random() < detect_prob
        result["detected"] = detected

        # Roll for attribution SEPARATELY (target learns WHO did it)
        # Attribution only possible if detected first
        attributed = False
        if detected:
            attribution_prob = {
                "espionage": 0.30, "intelligence": 0.30,
                "sabotage": 0.50, "cyber": 0.40,
                "disinformation": 0.20, "election_meddling": 0.50,
            }.get(op_type, 0.30)
            attributed = random.random() < attribution_prob
        result["attributed"] = attributed
        result["detection_probability"] = round(detect_prob, 3)

        # Apply effects
        if target in self.ws.countries:
            tc = self.ws.countries[target]

            if op_type in ("espionage", "intelligence"):
                # ALWAYS returns an answer — accuracy varies by success
                # Success: high accuracy (85-90%). Failure: low accuracy (40-60%).
                accuracy = 0.85 if success else 0.45
                result["intelligence"] = self._gather_intelligence(target, details, accuracy)
                result["accuracy"] = accuracy
                # Intelligence ALWAYS has a result — never returns nothing

            elif op_type == "sabotage" and success:
                damage = tc["economic"]["gdp"] * 0.02
                tc["economic"]["gdp"] = max(tc["economic"]["gdp"] - damage, 0.01)
                result["damage"] = round(damage, 2)
            elif op_type == "cyber" and success:
                damage = tc["economic"]["gdp"] * 0.01
                tc["economic"]["gdp"] = max(tc["economic"]["gdp"] - damage, 0.01)
                result["damage"] = round(damage, 2)
            elif op_type == "disinformation" and success:
                tc["political"]["stability"] = max(tc["political"]["stability"] - 0.3, 1)
                tc["political"]["political_support"] = max(
                    tc["political"]["political_support"] - 3, 0)
                result["stability_impact"] = -0.3
                result["support_impact"] = -3
            elif op_type == "election_meddling" and success:
                shift = random.uniform(2, 5)  # 2-5% shift
                tc["political"]["political_support"] = max(
                    tc["political"]["political_support"] - shift, 0)
                result["support_impact"] = round(-shift, 1)

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

    def _gather_intelligence(self, target: str, details: Optional[dict] = None,
                              accuracy: float = 0.85) -> dict:
        """Generate intelligence report — ALWAYS returns data, accuracy varies.

        High accuracy (0.85-0.90): success — data is ±5% of real values
        Low accuracy (0.40-0.60): failure — data is ±30% of real values, may be wrong
        The recipient does NOT know the accuracy level — report looks the same.
        """
        tc = self.ws.countries.get(target, {})

        # Noise based on accuracy: high accuracy = ±5%, low = ±30%
        if accuracy >= 0.75:
            noise_range = 0.05  # ±5%
        elif accuracy >= 0.50:
            noise_range = 0.15  # ±15%
        else:
            noise_range = 0.30  # ±30% — seriously unreliable

        def noisy(value, is_int=False):
            noise = random.uniform(1.0 - noise_range, 1.0 + noise_range)
            result = value * noise
            return int(round(result)) if is_int else round(result, 1)

        intel = {
            "gdp_estimate": noisy(tc.get("economic", {}).get("gdp", 0)),
            "treasury_estimate": noisy(tc.get("economic", {}).get("treasury", 0)),
            "stability_estimate": noisy(tc.get("political", {}).get("stability", 5)),
            "support_estimate": noisy(tc.get("political", {}).get("political_support", 50)),
            "military_ground_estimate": noisy(tc.get("military", {}).get("ground", 0), True),
            "military_naval_estimate": noisy(tc.get("military", {}).get("naval", 0), True),
            "military_air_estimate": noisy(tc.get("military", {}).get("tactical_air", 0), True),
            "nuclear_level": tc.get("technology", {}).get("nuclear_level", 0),
            "nuclear_progress_estimate": noisy(
                tc.get("technology", {}).get("nuclear_rd_progress", 0)),
            "ai_level": tc.get("technology", {}).get("ai_level", 0),
            "mobilization_pool_estimate": noisy(
                tc.get("military", {}).get("mobilization_pool", 0), True),
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

        # Execute arrest — pure player removal, NO stability or support cost
        # (per action review 2026-03-30: arrest is a standalone action, no mechanical linkages)
        role["status"] = "arrested"
        result["success"] = True
        result["note"] = f"{role['character_name']} arrested by {country}"

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

    # Country-specific assassination bonuses (international)
    _ASSASSINATION_COUNTRY_BONUS = {
        "levantia": 0.30,   # total 50% (20% + 30%)
        "nordostan": 0.10,  # total 30% (20% + 10%)
    }

    def resolve_assassination(self, country: str, target_role: str,
                              domestic: bool = False) -> dict:
        """Assassination (ACTION REVIEW 2026-03-30).

        1 card per game per eligible role.
        Domestic: 60% base hit.
        International: 20% base + country-specific bonuses.
        No AI tech or intel chief modifiers. Raw probability.
        Hit = 50% kill, 50% survive (injured + martyr effect).
        International: higher chance of being revealed if failed.
        """
        result = {
            "type": "assassination",
            "country": country,
            "target_role": target_role,
            "domestic": domestic,
            "success": False,
            "detected": False,
        }

        role = self.ws.roles.get(target_role)
        if not role:
            result["error"] = f"Role {target_role} not found"
            self._log_action(result)
            return result

        # Base probability — domestic vs international
        if domestic:
            prob = 0.60
        else:
            prob = 0.20
            # Country-specific bonuses (international only)
            prob += self._ASSASSINATION_COUNTRY_BONUS.get(country, 0.0)

        hit = random.random() < prob

        # Detection: international failures have higher reveal chance
        if domestic:
            detected = random.random() < 0.50
        else:
            detected = random.random() < (0.70 if not hit else 0.40)

        result["hit"] = hit
        result["detected"] = detected
        result["probability"] = round(prob, 3)

        if hit:
            # 50/50 kill or survive
            if random.random() < 0.50:
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
            else:
                result["target_survived"] = True
                result["note"] = (
                    f"{role['character_name']} survived — injured. "
                    "Martyr effect boosts support."
                )
                # Survived assassination still triggers martyr sympathy
                target_country = role["country_id"]
                if target_country in self.ws.countries:
                    tc = self.ws.countries[target_country]
                    tc["political"]["political_support"] = clamp(
                        tc["political"]["political_support"] + 10, 0, 100)
                    result["martyr_effect"] = 10

            result["success"] = True
        else:
            result["success"] = False
            result["note"] = "Assassination attempt failed"

        self.ws.log_event({
            "type": "assassination",
            "country": country,
            "target_role": target_role,
            "domestic": domestic,
            "hit": hit,
            "detected": detected,
        })
        self._log_action(result)
        return result

    # -----------------------------------------------------------------------
    # COUP ATTEMPT
    # -----------------------------------------------------------------------

    def resolve_coup(self, country: str, plotters: List[str]) -> dict:
        """Coup attempt (ACTION REVIEW 2026-03-30).

        Two conspirators required: initiator + co-conspirator.
        Any two roles within the same country can attempt.
        Base 15%
        + active_protest: +25%
        + stability < 3: +15%
        + stability 3-4: +5%
        + support < 30%: +10%
        Success: initiator becomes HoS, old HoS arrested.
        Failure: both exposed (arrested, world learns).
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

        # Require exactly 2 conspirators
        if len(plotters) < 2:
            result["error"] = "Coup requires two conspirators (initiator + co-conspirator)"
            self._log_action(result)
            return result

        # Verify both plotters are roles in the same country
        for p in plotters[:2]:
            role = self.ws.roles.get(p)
            if not role:
                result["error"] = f"Role {p} not found"
                self._log_action(result)
                return result
            if role["country_id"] != country:
                result["error"] = f"Role {p} is not in {country}"
                self._log_action(result)
                return result

        pol = c["political"]
        stability = pol["stability"]
        support = pol["political_support"]

        # Base probability
        prob = 0.15

        # Active protest bonus
        if pol.get("protest_risk", False) or pol.get("protest_active", False):
            prob += 0.25

        # Stability bonuses
        if stability < 3:
            prob += 0.15
        elif stability <= 4:
            prob += 0.05

        # Low support bonus
        if support < 30:
            prob += 0.10

        prob = clamp(prob, 0.0, 0.90)

        success = random.random() < prob
        result["success"] = success
        result["probability"] = round(prob, 3)

        initiator_id = plotters[0]
        co_conspirator_id = plotters[1]

        if success:
            # Initiator becomes HoS, old HoS arrested
            old_hos = self.ws.get_head_of_state(country)
            if old_hos:
                old_hos["status"] = "arrested"
                old_hos["is_head_of_state"] = False

            initiator_role = self.ws.roles.get(initiator_id)
            if initiator_role:
                initiator_role["is_head_of_state"] = True
                result["new_leader"] = initiator_id

            pol["stability"] = max(stability - 2, 1)
            result["note"] = (
                f"Coup successful. {initiator_id} takes power. "
                f"Former leader arrested."
            )
        else:
            # Failed: both conspirators exposed
            for p in plotters[:2]:
                role = self.ws.roles.get(p)
                if role:
                    role["status"] = "exposed"
            pol["stability"] = max(stability - 1, 1)
            result["note"] = (
                f"Coup failed. {initiator_id} and {co_conspirator_id} exposed. "
                "Ruler and world learn of the attempt."
            )

        self.ws.log_event({
            "type": "coup",
            "country": country,
            "plotters": plotters[:2],
            "success": success,
        })
        self._log_action(result)
        return result

    # -----------------------------------------------------------------------
    # NAVAL COMBAT (ship vs ship)
    # -----------------------------------------------------------------------

    def resolve_naval_combat(self, attacker: str, defender: str,
                             sea_zone: str) -> dict:
        """Ship vs ship combat in a sea zone.

        Same RISK dice as ground: 1d6 per pair, attacker needs >= defender + 1.
        No terrain modifiers (open sea). Carrier air support applies (+1).
        Sunk ship = all embarked units (ground + air) also lost.
        Moderator must be present.
        """
        result = {
            "type": "naval_combat",
            "attacker": attacker,
            "defender": defender,
            "sea_zone": sea_zone,
            "attacker_ships_committed": 0,
            "attacker_losses": 0,
            "defender_losses": 0,
            "embarked_units_lost": {"attacker": {}, "defender": {}},
            "success": False,
        }

        # Get naval forces in the zone
        att_naval = self.ws.get_naval_in_zone(sea_zone, attacker)
        def_naval = self.ws.get_naval_in_zone(sea_zone, defender)

        if att_naval <= 0:
            result["error"] = f"{attacker} has no ships in {sea_zone}"
            self._log_action(result)
            return result
        if def_naval <= 0:
            result["error"] = f"{defender} has no ships in {sea_zone}"
            self._log_action(result)
            return result

        result["attacker_ships_committed"] = att_naval

        # Modifiers (simplified — open sea, no terrain)
        att_c = self.ws.countries.get(attacker, {})
        def_c = self.ws.countries.get(defender, {})

        # AI L4 bonus
        att_mod = 1 if att_c.get("technology", {}).get("ai_l4_bonus", False) else 0
        def_mod = 1 if def_c.get("technology", {}).get("ai_l4_bonus", False) else 0

        # Low morale
        if att_c.get("political", {}).get("stability", 5) <= 3:
            att_mod -= 1
        if def_c.get("political", {}).get("stability", 5) <= 3:
            def_mod -= 1

        # Carrier air support: +1 if any tactical_air embarked on ships in this zone
        # (check country military for embarked air)
        att_air = att_c.get("military", {}).get("tactical_air", 0)
        def_air = def_c.get("military", {}).get("tactical_air", 0)
        if att_air > 0:
            att_mod += 1
        if def_air > 0:
            def_mod += 1

        # RISK dice combat — same as ground
        a_losses = 0
        d_losses = 0
        pairs = min(att_naval, def_naval)

        for _ in range(pairs):
            a_roll = random.randint(1, 6) + att_mod
            d_roll = random.randint(1, 6) + def_mod
            if a_roll >= d_roll + 1:
                d_losses += 1
            else:
                a_losses += 1

        # Apply losses
        att_embarked_lost = {"ground": 0, "tactical_air": 0}
        def_embarked_lost = {"ground": 0, "tactical_air": 0}

        # Attacker ship losses — each sunk ship loses embarked units
        if a_losses > 0:
            att_c["military"]["naval"] = max(0, att_c["military"]["naval"] - a_losses)
            # Embarked units lost: 1 ground + up to 5 air per sunk ship
            ground_per_ship = min(1, att_c["military"].get("ground", 0) // max(att_naval, 1))
            air_per_ship = min(5, att_c["military"].get("tactical_air", 0) // max(att_naval, 1))
            att_ground_lost = min(a_losses * ground_per_ship, att_c["military"].get("ground", 0))
            att_air_lost = min(a_losses * air_per_ship, att_c["military"].get("tactical_air", 0))
            att_c["military"]["ground"] = max(0, att_c["military"].get("ground", 0) - att_ground_lost)
            att_c["military"]["tactical_air"] = max(0, att_c["military"].get("tactical_air", 0) - att_air_lost)
            att_embarked_lost = {"ground": att_ground_lost, "tactical_air": att_air_lost}

        # Defender ship losses
        if d_losses > 0:
            def_c["military"]["naval"] = max(0, def_c["military"]["naval"] - d_losses)
            ground_per_ship = min(1, def_c["military"].get("ground", 0) // max(def_naval, 1))
            air_per_ship = min(5, def_c["military"].get("tactical_air", 0) // max(def_naval, 1))
            def_ground_lost = min(d_losses * ground_per_ship, def_c["military"].get("ground", 0))
            def_air_lost = min(d_losses * air_per_ship, def_c["military"].get("tactical_air", 0))
            def_c["military"]["ground"] = max(0, def_c["military"].get("ground", 0) - def_ground_lost)
            def_c["military"]["tactical_air"] = max(0, def_c["military"].get("tactical_air", 0) - def_air_lost)
            def_embarked_lost = {"ground": def_ground_lost, "tactical_air": def_air_lost}

        result["attacker_losses"] = a_losses
        result["defender_losses"] = d_losses
        result["embarked_units_lost"]["attacker"] = att_embarked_lost
        result["embarked_units_lost"]["defender"] = def_embarked_lost
        result["success"] = d_losses > a_losses  # attacker "wins" if they sank more

        self._log_action(result)
        self.ws.log_event({
            "type": "naval_combat",
            "attacker": attacker,
            "defender": defender,
            "sea_zone": sea_zone,
            "attacker_ships_lost": a_losses,
            "defender_ships_lost": d_losses,
            "embarked_lost": {
                "attacker": att_embarked_lost,
                "defender": def_embarked_lost,
            },
        })

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
    # AIR/DRONE STRIKE — Tactical air units strike ground targets
    # -----------------------------------------------------------------------

    def resolve_air_strike(self, country: str, target_zone: str,
                           air_units_sent: Optional[int] = None) -> dict:
        """Full tactical air combat system.

        Air units strike a target zone. Defender's air defense intercepts with
        degrading probability per AD unit. Intercepted air units are DESTROYED.
        Surviving air units strike at 15% hit rate per unit.

        Range: Global map = adjacent hexes. Theater map = 2 hexes.
        """
        result = {
            "type": "air_strike",
            "country": country,
            "target_zone": target_zone,
            "air_sent": 0,
            "intercepted_destroyed": 0,
            "strikes_landed": 0,
            "ground_units_destroyed": 0,
            "air_returned": 0,
        }

        c = self.ws.countries.get(country)
        if not c:
            result["error"] = f"Country {country} not found"
            self._log_action(result)
            return result

        available_air = c["military"].get("tactical_air", 0)
        if available_air <= 0:
            result["error"] = f"{country} has no tactical air units"
            self._log_action(result)
            return result

        # Determine how many air units to send (default: all available)
        air_sent = min(air_units_sent or available_air, available_air)
        result["air_sent"] = air_sent

        # --- STEP 1: Air Defense Interception ---
        # Collect AD units in target zone's coverage area
        # (coverage = target zone + adjacent zones)
        defender_ad = 0
        zone_forces = self.ws.get_zone_forces(target_zone)
        for cid, forces in zone_forces.items():
            if cid != country:
                defender_ad += forces.get("air_defense", 0)
        # Also check adjacent zones for AD coverage
        adjacent = self.ws.get_adjacent_zones(target_zone) if hasattr(self.ws, 'get_adjacent_zones') else []
        for adj_zone in adjacent:
            adj_forces = self.ws.get_zone_forces(adj_zone) if adj_zone else {}
            for cid, forces in adj_forces.items():
                if cid != country:
                    defender_ad += forces.get("air_defense", 0)

        # Each AD unit runs its own interception sequence
        intercepted = 0
        incoming_remaining = air_sent

        for ad_unit in range(defender_ad):
            if incoming_remaining <= 0:
                break
            attempt = 0
            while incoming_remaining > 0:
                attempt += 1
                # Degrading interception: 95%, 80%, 75%, 70%, 65%, 60% floor
                if attempt == 1:
                    rate = 0.95
                elif attempt == 2:
                    rate = 0.80
                else:
                    rate = max(0.60, 0.75 - (attempt - 3) * 0.05)

                if random.random() < rate:
                    intercepted += 1
                    incoming_remaining -= 1
                else:
                    incoming_remaining -= 1  # missed — this air unit gets through
                    break  # AD unit moves to next incoming (but sequence continues)
                # Actually: each AD processes ALL incoming sequentially
                # Re-thinking: each incoming air unit faces ONE intercept attempt
                # from the AD pool. Let me simplify.
                break  # One attempt per incoming per AD unit

        # Simpler model: each incoming air unit faces one intercept attempt.
        # AD units are distributed across incoming. Each AD unit handles
        # ceil(air_sent / defender_ad) attempts with degrading rate.
        intercepted = 0
        surviving = []
        if defender_ad > 0:
            for i in range(air_sent):
                # Which AD unit handles this? Round-robin.
                ad_idx = i % defender_ad
                attempt_num = (i // defender_ad) + 1
                # Degrading rate per attempt number for this AD unit
                if attempt_num == 1:
                    rate = 0.95
                elif attempt_num == 2:
                    rate = 0.80
                else:
                    rate = max(0.60, 0.75 - (attempt_num - 3) * 0.05)

                if random.random() < rate:
                    intercepted += 1
                else:
                    surviving.append(i)
        else:
            surviving = list(range(air_sent))

        survivors = air_sent - intercepted
        result["intercepted_destroyed"] = intercepted

        # Destroy intercepted air units from attacker's military
        c["military"]["tactical_air"] = max(0, available_air - intercepted)

        # --- STEP 2: Surviving air units strike ---
        ground_destroyed = 0
        for _ in range(survivors):
            if random.random() < 0.15:
                ground_destroyed += 1

        result["strikes_landed"] = survivors

        # Apply ground damage
        if ground_destroyed > 0:
            remaining_to_destroy = ground_destroyed
            for cid, forces in zone_forces.items():
                if cid == country or remaining_to_destroy <= 0:
                    continue
                ground = forces.get("ground", 0)
                actual_loss = min(remaining_to_destroy, ground)
                forces["ground"] = max(ground - actual_loss, 0)
                if cid in self.ws.countries:
                    self.ws.countries[cid]["military"]["ground"] = max(
                        self.ws.countries[cid]["military"]["ground"] - actual_loss, 0)
                remaining_to_destroy -= actual_loss

        result["ground_units_destroyed"] = ground_destroyed
        result["air_returned"] = survivors

        self._log_action(result)
        self.ws.log_event({
            "type": "air_strike",
            "attacker": country,
            "target_zone": target_zone,
            "air_sent": air_sent,
            "intercepted": intercepted,
            "ground_destroyed": ground_destroyed,
            "air_lost": intercepted,
        })

        return result

    def resolve_airfield_vulnerability(self, target_zone: str,
                                        attacking_country: str) -> dict:
        """When a zone is attacked (ground or air), stationed air units risk destruction.

        20% chance per air unit of being destroyed 'on the ground' (parked aircraft,
        airfield damage, carrier strikes on ports).
        Called BEFORE ground combat or air defense in the target zone.
        """
        result = {"type": "airfield_vulnerability", "zone": target_zone, "destroyed": 0}

        zone_forces = self.ws.get_zone_forces(target_zone)
        for cid, forces in zone_forces.items():
            if cid == attacking_country:
                continue
            air_in_zone = forces.get("tactical_air", 0)
            destroyed = 0
            for _ in range(air_in_zone):
                if random.random() < 0.20:
                    destroyed += 1
            if destroyed > 0:
                forces["tactical_air"] = max(0, air_in_zone - destroyed)
                if cid in self.ws.countries:
                    self.ws.countries[cid]["military"]["tactical_air"] = max(
                        0, self.ws.countries[cid]["military"]["tactical_air"] - destroyed)
                result["destroyed"] += destroyed

        if result["destroyed"] > 0:
            self.ws.log_event({
                "type": "airfield_attack",
                "zone": target_zone,
                "air_destroyed_on_ground": result["destroyed"],
            })

        self._log_action(result)
        return result

    # -----------------------------------------------------------------------
    # G1: NUCLEAR TEST — Signal Action + Tech Path
    # -----------------------------------------------------------------------

    def resolve_nuclear_test(self, country_id: str, test_type: str = "underground") -> dict:
        """Nuclear test — a SIGNAL to the world + tech development milestone.

        - underground: less provocative, smaller diplomatic cost
        - overground: maximum signal, major diplomatic event, global stability shock

        NOT required to advance nuclear tech — R&D investment is the path.
        But test CONFIRMS capability (makes deterrent credible).
        A strike on nuclear sites can push R&D progress BACK.
        Countries can also BUY L1 tech from others via tech_transfer transaction
        and deploy it next turn.
        """
        c = self.ws.countries[country_id]
        nuc_level = c['technology']['nuclear_level']

        if nuc_level < 1:
            return {"success": False, "reason": "Must have at least L1 nuclear to test"}

        result = {
            "action": "nuclear_test",
            "country": country_id,
            "test_type": test_type,
            "success": True,
        }

        # Diplomatic consequences
        if test_type == "overground":
            # Global stability shock
            for cid, country in self.ws.countries.items():
                country['political']['stability'] = max(1.0, country['political']['stability'] - 0.3)
            result["global_event"] = f"{country_id} conducts overground nuclear test — global shock"
            result["stability_cost_to_tester"] = -0.5  # self-cost too
            c['political']['stability'] = max(1.0, c['political']['stability'] - 0.5)
        else:
            # Underground — less dramatic
            result["global_event"] = f"{country_id} conducts underground nuclear test — detected by intelligence"
            result["stability_cost_to_tester"] = -0.2
            c['political']['stability'] = max(1.0, c['political']['stability'] - 0.2)

        # Confirms capability — makes deterrent credible
        c['technology']['nuclear_tested'] = True

        # Political support boost domestically (nationalist rally)
        c['political']['political_support'] = min(100, c['political']['political_support'] + 5)

        self.ws.log_event({
            "type": "nuclear_test",
            "country": country_id,
            "test_type": test_type,
            "global_event": result.get("global_event", ""),
        })
        self._log_action(result)
        return result

    # -----------------------------------------------------------------------
    # G2: FIRE / REASSIGN ACTION
    # -----------------------------------------------------------------------

    def resolve_fire(self, country_id: str, target_role_id: str, replacement_role_id: str = None) -> dict:
        """Head of state fires/reassigns a subordinate.

        - Instant power removal
        - Columbia: Parliament must confirm replacement (Acting if not confirmed)
        - Other countries: instant
        - Fired role loses ALL powers, stays in game as opposition/disgraced
        - Political cost: -3 support, -0.3 stability (institutional disruption)
        """
        c = self.ws.countries[country_id]

        # Verify initiator is HoS
        # (authorization check handled by orchestrator)

        result = {
            "action": "fire",
            "country": country_id,
            "target_role": target_role_id,
            "success": True,
        }

        # Remove target's powers
        target_role = self.ws.get_role(target_role_id)
        if target_role:
            target_role['status'] = 'fired'
            target_role['powers'] = []  # all powers removed
            result["fired_role"] = target_role_id
        else:
            result["success"] = False
            result["error"] = f"Role {target_role_id} not found"
            self._log_action(result)
            return result

        # Political cost
        c['political']['political_support'] = max(0, c['political']['political_support'] - 3)
        c['political']['stability'] = max(1.0, c['political']['stability'] - 0.3)

        # Columbia special: Parliament confirmation
        if country_id == 'columbia' and replacement_role_id:
            # Check if parliament majority supports (3 of 5 seats)
            parliament_approves = True  # simplified — orchestrator handles vote
            if not parliament_approves:
                result["acting"] = True
                result["note"] = "Parliament did not confirm. Replacement serves as Acting official."

        self.ws.log_event({
            "type": "fire",
            "country": country_id,
            "target_role": target_role_id,
            "replacement": replacement_role_id,
        })
        self._log_action(result)
        return result

    # -----------------------------------------------------------------------
    # G3: PROTEST ACTION (elite leads mass protest)
    # -----------------------------------------------------------------------

    def resolve_protest_action(self, country_id: str, leader_role_id: str) -> dict:
        """Elite participant leads the mass protest. Dice roll determines outcome."""
        c = self.ws.countries[country_id]
        stab = c['political']['stability']
        support = c['political']['political_support']

        base_prob = 0.30 + (20 - support) / 100 + max(0, (3 - stab)) * 0.10
        prob = min(0.80, max(0.15, base_prob))  # floor 15%, cap 80%

        roll = random.random()
        success = roll < prob

        if success:
            # Regime change — protest leader takes power
            # Remove old HoS
            old_hos = self.ws.get_head_of_state(country_id)
            if old_hos:
                old_hos["status"] = "deposed"
                old_hos["is_head_of_state"] = False

            # Install protest leader
            new_leader = self.ws.get_role(leader_role_id)
            if new_leader:
                new_leader["is_head_of_state"] = True

            c['political']['stability'] = min(10.0, stab + 1.0)  # new hope
            c['political']['political_support'] = min(100, support + 20)  # fresh mandate

            result = {
                "action": "protest_action",
                "success": True,
                "outcome": "regime_change",
                "new_leader": leader_role_id,
                "probability": round(prob, 3),
                "note": f"Mass protests succeed. {leader_role_id} takes power. Previous HoS removed.",
                "stability_change": +1.0,
                "support_change": +20,
            }
        else:
            # Protest crushed — leader imprisoned
            leader_role = self.ws.get_role(leader_role_id)
            if leader_role:
                leader_role["status"] = "imprisoned"

            c['political']['stability'] = max(1.0, stab - 0.5)  # more repression
            c['political']['political_support'] = max(0, support - 5)  # fear, not loyalty

            result = {
                "action": "protest_action",
                "success": False,
                "outcome": "protest_crushed",
                "imprisoned": leader_role_id,
                "probability": round(prob, 3),
                "note": f"Protest crushed. {leader_role_id} imprisoned. Regime consolidates.",
                "stability_change": -0.5,
                "support_change": -5,
            }

        self.ws.log_event({
            "type": "protest_action",
            "country": country_id,
            "leader": leader_role_id,
            "success": success,
            "probability": round(prob, 3),
        })
        self._log_action(result)
        return result

    # -----------------------------------------------------------------------
    # HELPERS
    # -----------------------------------------------------------------------

    def _build_combat_modifiers(self, attacker: str, defender: str,
                                 zone: str, is_amphibious: bool) -> dict:
        """Simplified integer-only modifiers (ACTION REVIEW 2026-03-30).

        Modifiers kept:
        - AI L4: +1 if country has ai_level==4 AND random flag was set when L4 reached
        - Low morale: -1 if stability <= 3
        - Die Hard: +1 defender if zone has die_hard flag
        - Amphibious: -1 attacker
        - Air support: +1 defender if ANY tactical_air > 0 in zone (binary)

        REMOVED: naval support, militia modifier, home territory, capital,
                 scaled air support, proportional morale.
        """
        att_c = self.ws.countries.get(attacker, {})
        def_c = self.ws.countries.get(defender, {})

        # --- AI L4 bonus: +1 if ai_level == 4 and random flag set ---
        att_ai_bonus = 0
        if att_c.get("technology", {}).get("ai_level", 0) == 4:
            if att_c.get("technology", {}).get("ai_l4_bonus", False):
                att_ai_bonus = 1

        def_ai_bonus = 0
        if def_c.get("technology", {}).get("ai_level", 0) == 4:
            if def_c.get("technology", {}).get("ai_l4_bonus", False):
                def_ai_bonus = 1

        # --- Low morale: -1 if stability <= 3 ---
        att_morale = -1 if att_c.get("political", {}).get("stability", 5) <= 3 else 0
        def_morale = -1 if def_c.get("political", {}).get("stability", 5) <= 3 else 0

        # --- Die Hard: +1 defender if zone has die_hard flag ---
        zone_data = self.ws.zones.get(zone, {})
        die_hard = 1 if zone_data.get("die_hard", False) else 0

        # --- Amphibious: -1 attacker ---
        amphibious_penalty = -1 if is_amphibious else 0

        # --- Air support: +1 defender if any tactical_air > 0 (binary yes/no) ---
        zone_forces = self.ws.get_zone_forces(zone) if hasattr(self.ws, 'get_zone_forces') else {}
        def_air_in_zone = zone_forces.get(defender, {}).get("tactical_air", 0)
        air_support = 1 if def_air_in_zone > 0 else 0

        att_total = att_ai_bonus + att_morale + amphibious_penalty
        def_total = def_ai_bonus + def_morale + die_hard + air_support

        return {
            "attacker_ai_l4": att_ai_bonus,
            "attacker_morale": att_morale,
            "amphibious_penalty": amphibious_penalty,
            "defender_ai_l4": def_ai_bonus,
            "defender_morale": def_morale,
            "die_hard": die_hard,
            "defender_air_support": air_support,
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
                # If attacker is on a water hex attacking a land zone
                if origin_data.get("type", "").startswith("sea"):
                    return True
        return False

    def _get_intervening_sea_zones(self, origin: Optional[str],
                                    target: str) -> List[str]:
        """Get water hexes between origin and target for amphibious checks."""
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
