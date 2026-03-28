"""
TTT SEED — Shared World State Model
====================================
Complete world state shared between all three engines and the orchestrator.
Loads from CSV data files, serializes to JSON for persistence.

Author: ATLAS (World Model Engineer)
Version: 2.0 (SEED)
"""

import csv
import copy
import json
import os
from typing import Dict, List, Optional, Any


# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

CHOKEPOINTS = {
    "hormuz": {"zone": "cp_gulf_gate", "oil_impact": 0.35, "trade_impact": 0.10},
    "malacca": {"zone": "w(15,9)", "trade_impact": 0.30, "oil_impact": 0.05},
    "taiwan_strait": {"zone": "w(17,4)", "tech_impact": 0.50, "trade_impact": 0.15},
    "suez": {"zone": "w(10,7)", "trade_impact": 0.15, "oil_impact": 0.05},
    "bosphorus": {"zone": "w(10,3)", "trade_impact": 0.08, "oil_impact": 0.0},
    "giuk": {"zone": "w(6,1)", "detection": True, "trade_impact": 0.02},
    "caribbean": {"zone": "w(4,8)", "trade_impact": 0.05, "oil_impact": 0.02},
    "south_china_sea": {"zone": "w(16,7)", "trade_impact": 0.20, "oil_impact": 0.03},
    "gulf_gate_ground": {"zone": "cp_gulf_gate", "oil_impact": 0.60, "ground_blockade": True},
}

UNIT_TYPES = ["ground", "naval", "tactical_air", "strategic_missiles", "air_defense"]

# Cal-3 v3: Tech boost applied to GROWTH RATE, not GDP multiplier.
# L3 adds +1.5 percentage points to growth rate (not x1.15 to GDP).
# L4 adds +3.0pp. This prevents unrealistic GDP doubling over 8 rounds.
AI_LEVEL_TECH_FACTOR = {0: 0.0, 1: 0.0, 2: 0.005, 3: 0.015, 4: 0.030}
AI_LEVEL_COMBAT_BONUS = {0: 0, 1: 0, 2: 0, 3: 1, 4: 2}

NUCLEAR_RD_THRESHOLDS = {0: 0.60, 1: 0.80, 2: 1.00}
AI_RD_THRESHOLDS = {0: 0.20, 1: 0.40, 2: 0.60, 3: 1.00}

OPEC_PRODUCTION_MULTIPLIER = {"low": 0.80, "normal": 1.00, "high": 1.20}
PRODUCTION_TIER_COST = {"normal": 1.0, "accelerated": 2.0, "maximum": 4.0}
PRODUCTION_TIER_OUTPUT = {"normal": 1.0, "accelerated": 2.0, "maximum": 3.0}

STABILITY_THRESHOLDS = {
    "unstable": 6,
    "protest_probable": 5,
    "protest_automatic": 3,
    "regime_collapse_risk": 2,
    "failed_state": 1,
}

# Scheduled events
SCHEDULED_EVENTS = {
    2: [{"type": "election", "subtype": "columbia_midterms", "country": "columbia"}],
    3: [{"type": "election", "subtype": "heartland_wartime", "country": "heartland"}],
    4: [{"type": "election", "subtype": "heartland_wartime_runoff", "country": "heartland"}],
    5: [{"type": "election", "subtype": "columbia_presidential", "country": "columbia"}],
}


# ---------------------------------------------------------------------------
# WORLD STATE
# ---------------------------------------------------------------------------

class WorldState:
    """Complete world state -- shared between all engines."""

    def __init__(self):
        self.round_num: int = 0
        self.countries: Dict[str, dict] = {}
        self.zones: Dict[str, dict] = {}
        self.zone_adjacency: Dict[str, List[dict]] = {}
        self.deployments: List[dict] = []
        self.bilateral: dict = {"tariffs": {}, "sanctions": {}}
        self.organizations: List[dict] = []
        self.org_memberships: Dict[str, List[str]] = {}
        self.wars: List[dict] = []
        self.active_theaters: List[str] = []
        self.oil_price: float = 80.0
        self.oil_price_index: float = 100.0
        self.opec_production: Dict[str, str] = {}
        self.global_trade_volume_index: float = 100.0
        self.chokepoint_status: Dict[str, str] = {}
        self.treaties: List[dict] = []
        self.basing_rights: List[dict] = []
        self.roles: Dict[str, dict] = {}
        self.relationships: Dict[str, Dict[str, dict]] = {}
        self.events_log: List[dict] = []
        self.round_logs: Dict[int, List[dict]] = {}
        self.nuclear_used_this_sim: bool = False
        self.ground_blockades: Dict[str, dict] = {}  # Gulf Gate ground blockade
        self.active_blockades: Dict[str, dict] = {}  # Chokepoint blockades (keyed by chokepoint name)
        self.rare_earth_restrictions: Dict[str, int] = {}  # country_id -> restriction level (1-3)
        self.formosa_blockade: bool = False  # Whether Formosa is under naval blockade

    # --- CSV Loading ---

    def load_from_csvs(self, data_dir: str) -> None:
        """Load world state from CSV data files in data_dir."""
        self._load_countries(os.path.join(data_dir, "countries.csv"))
        self._load_zones(os.path.join(data_dir, "zones.csv"))
        self._load_zone_adjacency(os.path.join(data_dir, "zone_adjacency.csv"))
        self._load_deployments(os.path.join(data_dir, "deployments.csv"))
        self._load_sanctions(os.path.join(data_dir, "sanctions.csv"))
        self._load_tariffs(os.path.join(data_dir, "tariffs.csv"))
        self._load_organizations(os.path.join(data_dir, "organizations.csv"))
        self._load_roles(os.path.join(data_dir, "roles.csv"))
        self._load_relationships(os.path.join(data_dir, "relationships.csv"))
        self._load_org_memberships(os.path.join(data_dir, "org_memberships.csv"))

        # Initialize chokepoints as open
        for cp_name in CHOKEPOINTS:
            self.chokepoint_status[cp_name] = "open"

        # Initialize OPEC production
        for cid, c in self.countries.items():
            if c["economic"].get("opec_member"):
                self.opec_production[cid] = c["economic"].get("opec_production", "normal")

        # Initialize wars from relationships
        self._init_wars_from_relationships()

        # Build zone forces map from deployments
        self._build_zone_forces()

        # Initialize Gulf Gate ground blockade (Persia starts with ground
        # forces on the Gulf Gate zone)
        self._check_ground_blockades()

    def _load_countries(self, path: str) -> None:
        with open(path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cid = row["id"]
                home_zones = [z.strip() for z in row.get("home_zones", "").strip('"').split(",") if z.strip()]
                self.countries[cid] = {
                    "id": cid,
                    "sim_name": row["sim_name"],
                    "parallel": row["parallel"],
                    "regime_type": row["regime_type"],
                    "team_type": row["team_type"],
                    "team_size_min": int(row.get("team_size_min", 1)),
                    "team_size_max": int(row.get("team_size_max", 1)),
                    "ai_default": row.get("ai_default", "true").lower() == "true",
                    "home_zones": home_zones,
                    "economic": {
                        "gdp": float(row["gdp"]),
                        "gdp_growth_rate": float(row["gdp_growth_base"]),
                        "sectors": {
                            "resources": self._override_sector(cid, "resources", float(row["sector_resources"])),
                            "industry": float(row["sector_industry"]),
                            "services": float(row["sector_services"]),
                            "technology": float(row["sector_technology"]),
                        },
                        "tax_rate": float(row["tax_rate"]),
                        "treasury": float(row["treasury"]),
                        "inflation": float(row["inflation"]),
                        "trade_balance": float(row["trade_balance"]),
                        "oil_producer": row.get("oil_producer", "false").lower() == "true",
                        "opec_member": row.get("opec_member", "false").lower() == "true",
                        "opec_production": row.get("opec_production", "na"),
                        "formosa_dependency": float(row.get("formosa_dependency", 0)),
                        "debt_burden": float(row.get("debt_burden", 0)),
                        "social_spending_baseline": float(row.get("social_baseline", 0.25)),
                        "oil_revenue": 0.0,
                        "inflation_revenue_erosion": 0.0,
                        # --- v2 new state variables ---
                        "economic_state": "normal",       # normal/stressed/crisis/collapse
                        "momentum": 0.0,                  # -5.0 to +5.0 confidence
                        "crisis_rounds": 0,               # rounds in crisis/collapse
                        "recovery_rounds": 0,             # rounds recovering
                        "starting_inflation": float(row["inflation"]),  # baseline for delta
                        "sanctions_rounds": 0,            # consecutive rounds under L2+ sanctions
                        "formosa_disruption_rounds": 0,   # consecutive rounds of semiconductor disruption
                    },
                    "military": {
                        "ground": int(row.get("mil_ground", 0)),
                        "naval": self._override_naval(cid, int(row.get("mil_naval", 0))),
                        "tactical_air": int(row.get("mil_tactical_air", 0)),
                        "strategic_missiles": int(row.get("mil_strategic_missiles", 0)),
                        "air_defense": int(row.get("mil_air_defense", 0)),
                        "production_costs": {
                            "ground": float(row.get("prod_cost_ground", 3)),
                            "naval": float(row.get("prod_cost_naval", 5)),
                            "tactical_air": float(row.get("prod_cost_tactical", 4)),
                        },
                        "production_capacity": {
                            "ground": int(float(row.get("prod_cap_ground", 2))),
                            "naval": int(float(row.get("prod_cap_naval", 1))),
                            "tactical_air": int(float(row.get("prod_cap_tactical", 1))),
                        },
                        "maintenance_cost_per_unit": float(row.get("maintenance_per_unit", 0.3)),
                        "strategic_missile_growth": int(float(row.get("strategic_missile_growth", 0))),
                        "mobilization_pool": 0,
                    },
                    "political": {
                        "stability": float(row.get("stability", 5)),
                        "political_support": float(row.get("political_support", 50)),
                        "dem_rep_split": {
                            "dem": float(row.get("dem_rep_split_dem", 0)),
                            "rep": float(row.get("dem_rep_split_rep", 0)),
                        },
                        "war_tiredness": float(row.get("war_tiredness", 0)),
                        "regime_type": row["regime_type"],
                        "regime_status": "stable",
                        "protest_risk": False,
                        "coup_risk": False,
                    },
                    "technology": {
                        "nuclear_level": int(row.get("nuclear_level", 0)),
                        "nuclear_rd_progress": float(row.get("nuclear_rd_progress", 0)),
                        "ai_level": self._override_ai_level(cid, int(row.get("ai_level", 0))),
                        "ai_rd_progress": self._override_ai_progress(cid, float(row.get("ai_rd_progress", 0))),
                    },
                    "diplomatic": {
                        "wars": [],
                        "peace_treaties": [],
                        "organization_memberships": [],
                        "active_treaties": [],
                    },
                }

    # --- v2 Data Overrides (fixes from SEED TESTS2) ---

    @staticmethod
    def _override_naval(cid: str, csv_val: int) -> int:
        """Columbia naval 10->11, Cathay naval 6->7."""
        overrides = {"columbia": 11, "cathay": 7}
        return overrides.get(cid, csv_val)

    @staticmethod
    def _override_sector(cid: str, sector: str, csv_val: float) -> float:
        """Columbia resource sector 5->8."""
        if cid == "columbia" and sector == "resources":
            return 8.0
        return csv_val

    @staticmethod
    def _override_ai_level(cid: str, csv_val: int) -> int:
        """Cathay AI: fix to L3 (was L2 with 0.70 progress past 0.60 threshold)."""
        if cid == "cathay":
            return 3
        return csv_val

    @staticmethod
    def _override_ai_progress(cid: str, csv_val: float) -> float:
        """Columbia AI progress 0.60->0.80. Cathay AI progress 0.70->0.10 (now L3)."""
        overrides = {"columbia": 0.80, "cathay": 0.10}
        return overrides.get(cid, csv_val)

    def _load_zones(self, path: str) -> None:
        with open(path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                zid = row["id"]
                self.zones[zid] = {
                    "id": zid,
                    "display_name": row.get("display_name", zid),
                    "type": row.get("type", "land_home"),
                    "owner": row.get("owner", "none"),
                    "theater": row.get("theater", "global"),
                    "is_chokepoint": row.get("is_chokepoint", "false").lower() == "true",
                    "forces": {},
                }

    def _load_zone_adjacency(self, path: str) -> None:
        with open(path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                za = row["zone_a"]
                zb = row["zone_b"]
                conn = row.get("connection_type", "land_land")
                if za not in self.zone_adjacency:
                    self.zone_adjacency[za] = []
                if zb not in self.zone_adjacency:
                    self.zone_adjacency[zb] = []
                self.zone_adjacency[za].append({"zone": zb, "type": conn})
                self.zone_adjacency[zb].append({"zone": za, "type": conn})

    def _load_deployments(self, path: str) -> None:
        with open(path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.deployments.append({
                    "country": row["country_id"],
                    "unit_type": row["unit_type"],
                    "count": int(row["count"]),
                    "zone": row["zone_id"],
                })

    def _load_sanctions(self, path: str) -> None:
        with open(path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                imposer = row["country"]
                target = row["target"]
                level = int(row["level"])
                if imposer not in self.bilateral["sanctions"]:
                    self.bilateral["sanctions"][imposer] = {}
                self.bilateral["sanctions"][imposer][target] = level

    def _load_tariffs(self, path: str) -> None:
        with open(path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                imposer = row["imposer"]
                target = row["target"]
                level = int(row["level"])
                if imposer not in self.bilateral["tariffs"]:
                    self.bilateral["tariffs"][imposer] = {}
                self.bilateral["tariffs"][imposer][target] = level

    def _load_organizations(self, path: str) -> None:
        with open(path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.organizations.append({
                    "id": row["id"],
                    "sim_name": row["sim_name"],
                    "parallel": row.get("parallel", ""),
                    "decision_rule": row.get("decision_rule", "consensus"),
                    "chair_role_id": row.get("chair_role_id", ""),
                    "voting_threshold": row.get("voting_threshold", "unanimous"),
                    "meeting_frequency": row.get("meeting_frequency", ""),
                    "description": row.get("description", ""),
                })

    def _load_org_memberships(self, path: str) -> None:
        filepath = path
        if not os.path.exists(filepath):
            return
        with open(filepath, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                org_id = row.get("org_id", "")
                country_id = row.get("country_id", "")
                if org_id not in self.org_memberships:
                    self.org_memberships[org_id] = []
                self.org_memberships[org_id].append(country_id)

    def _load_roles(self, path: str) -> None:
        with open(path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rid = row["id"]
                self.roles[rid] = {
                    "id": rid,
                    "character_name": row.get("character_name", rid),
                    "parallel": row.get("parallel", ""),
                    "country_id": row.get("country_id", ""),
                    "team": row.get("team", ""),
                    "faction": row.get("faction", ""),
                    "title": row.get("title", ""),
                    "age": int(row.get("age", 50)),
                    "gender": row.get("gender", "M"),
                    "is_head_of_state": row.get("is_head_of_state", "false").lower() == "true",
                    "is_military_chief": row.get("is_military_chief", "false").lower() == "true",
                    "parliament_seat": int(row.get("parliament_seat", 0)),
                    "personal_coins": float(row.get("personal_coins", 0)),
                    "expansion_role": row.get("expansion_role", "false").lower() == "true",
                    "ai_candidate": row.get("ai_candidate", "false").lower() == "true",
                    "powers": row.get("powers", "").split(";") if row.get("powers") else [],
                    "objectives": row.get("objectives", "").split(";") if row.get("objectives") else [],
                    "ticking_clock": row.get("ticking_clock", ""),
                    "status": "active",
                }

    def _load_relationships(self, path: str) -> None:
        with open(path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                fc = row["from_country"]
                tc = row["to_country"]
                if fc not in self.relationships:
                    self.relationships[fc] = {}
                self.relationships[fc][tc] = {
                    "relationship": row.get("relationship", "neutral"),
                    "dynamic": row.get("dynamic", ""),
                }

    def _init_wars_from_relationships(self) -> None:
        """Initialize active wars from at_war relationships."""
        war_pairs_seen = set()
        for fc, targets in self.relationships.items():
            for tc, data in targets.items():
                if data["relationship"] == "at_war":
                    pair = tuple(sorted([fc, tc]))
                    if pair not in war_pairs_seen:
                        war_pairs_seen.add(pair)
                        # Determine attacker/defender from context
                        if pair == ("heartland", "nordostan"):
                            self.wars.append({
                                "attacker": "nordostan",
                                "defender": "heartland",
                                "theater": "eastern_ereb",
                                "start_round": -4,  # pre-sim war
                                "occupied_zones": [
                                    "heartland_2",
                                ],
                            })
                        elif pair == ("columbia", "persia") or pair == ("levantia", "persia"):
                            # Check if already added
                            already = any(
                                w["attacker"] in ("columbia", "levantia") and w["defender"] == "persia"
                                for w in self.wars
                            )
                            if not already:
                                self.wars.append({
                                    "attacker": "columbia",
                                    "defender": "persia",
                                    "theater": "mashriq",
                                    "start_round": 0,  # starts with sim
                                    "allies": {"attacker": ["levantia"], "defender": []},
                                    "occupied_zones": [],
                                })
                        else:
                            self.wars.append({
                                "attacker": fc,
                                "defender": tc,
                                "theater": "global",
                                "start_round": 0,
                                "occupied_zones": [],
                            })

    def _build_zone_forces(self) -> None:
        """Build zone force maps from deployment records."""
        for dep in self.deployments:
            zid = dep["zone"]
            country = dep["country"]
            utype = dep["unit_type"]
            count = dep["count"]
            if zid in self.zones:
                forces = self.zones[zid]["forces"]
                if country not in forces:
                    forces[country] = {}
                forces[country][utype] = forces[country].get(utype, 0) + count

    def _check_ground_blockades(self) -> None:
        """Check for ground-based blockades (Gulf Gate mechanic)."""
        gulf_gate = self.zones.get("cp_gulf_gate", {})
        forces = gulf_gate.get("forces", {})
        for country, units in forces.items():
            ground = units.get("ground", 0)
            naval = units.get("naval", 0)
            if ground >= 1 or naval >= 1:
                self.ground_blockades["gulf_gate"] = {
                    "controller": country,
                    "ground_units": ground,
                    "naval_units": naval,
                    "breakable_by_air": False,  # ground blockade cannot be broken by air
                    "requires_ground_invasion": True,
                }
                if ground >= 1:
                    self.chokepoint_status["gulf_gate_ground"] = "blocked"

    # --- Accessors ---

    def get_country(self, country_id: str) -> Optional[dict]:
        return self.countries.get(country_id)

    def get_zone(self, zone_id: str) -> Optional[dict]:
        return self.zones.get(zone_id)

    def get_zone_forces(self, zone_id: str) -> Dict[str, dict]:
        zone = self.zones.get(zone_id, {})
        return zone.get("forces", {})

    def get_adjacent_zones(self, zone_id: str) -> List[dict]:
        return self.zone_adjacency.get(zone_id, [])

    def is_adjacent(self, zone_a: str, zone_b: str) -> bool:
        adj = self.zone_adjacency.get(zone_a, [])
        return any(a["zone"] == zone_b for a in adj)

    def get_country_at_war(self, country_id: str) -> bool:
        return any(
            w.get("attacker") == country_id or w.get("defender") == country_id
            or country_id in w.get("allies", {}).get("attacker", [])
            or country_id in w.get("allies", {}).get("defender", [])
            for w in self.wars
        )

    def get_roles_for_country(self, country_id: str) -> List[dict]:
        return [r for r in self.roles.values() if r["country_id"] == country_id]

    def get_head_of_state(self, country_id: str) -> Optional[dict]:
        for r in self.roles.values():
            if r["country_id"] == country_id and r["is_head_of_state"]:
                return r
        return None

    def get_military_chief(self, country_id: str) -> Optional[dict]:
        for r in self.roles.values():
            if r["country_id"] == country_id and r["is_military_chief"]:
                return r
        return None

    def get_total_military(self, country_id: str) -> int:
        c = self.countries.get(country_id, {})
        mil = c.get("military", {})
        return sum(mil.get(ut, 0) for ut in ["ground", "naval", "tactical_air"])

    def get_naval_in_zone(self, zone_id: str, country_id: str) -> int:
        forces = self.get_zone_forces(zone_id)
        return forces.get(country_id, {}).get("naval", 0)

    def log_event(self, event: dict) -> None:
        event["round"] = self.round_num
        self.events_log.append(event)

    # --- Serialization ---

    def to_dict(self) -> dict:
        return {
            "round_num": self.round_num,
            "countries": copy.deepcopy(self.countries),
            "zones": copy.deepcopy(self.zones),
            "zone_adjacency": {k: list(v) for k, v in self.zone_adjacency.items()},
            "bilateral": copy.deepcopy(self.bilateral),
            "organizations": copy.deepcopy(self.organizations),
            "org_memberships": copy.deepcopy(self.org_memberships),
            "wars": copy.deepcopy(self.wars),
            "oil_price": self.oil_price,
            "oil_price_index": self.oil_price_index,
            "opec_production": dict(self.opec_production),
            "global_trade_volume_index": self.global_trade_volume_index,
            "chokepoint_status": dict(self.chokepoint_status),
            "treaties": copy.deepcopy(self.treaties),
            "basing_rights": copy.deepcopy(self.basing_rights),
            "roles": copy.deepcopy(self.roles),
            "events_log": copy.deepcopy(self.events_log),
            "nuclear_used_this_sim": self.nuclear_used_this_sim,
            "ground_blockades": copy.deepcopy(self.ground_blockades),
            "active_blockades": copy.deepcopy(self.active_blockades),
            "rare_earth_restrictions": dict(self.rare_earth_restrictions),
            "formosa_blockade": self.formosa_blockade,
        }

    def save_to_json(self, path: str) -> None:
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def from_dict(cls, d: dict) -> "WorldState":
        ws = cls()
        ws.round_num = d.get("round_num", 0)
        ws.countries = d.get("countries", {})
        ws.zones = d.get("zones", {})
        ws.zone_adjacency = d.get("zone_adjacency", {})
        ws.bilateral = d.get("bilateral", {"tariffs": {}, "sanctions": {}})
        ws.organizations = d.get("organizations", [])
        ws.org_memberships = d.get("org_memberships", {})
        ws.wars = d.get("wars", [])
        ws.oil_price = d.get("oil_price", 80.0)
        ws.oil_price_index = d.get("oil_price_index", 100.0)
        ws.opec_production = d.get("opec_production", {})
        ws.global_trade_volume_index = d.get("global_trade_volume_index", 100.0)
        ws.chokepoint_status = d.get("chokepoint_status", {})
        ws.treaties = d.get("treaties", [])
        ws.basing_rights = d.get("basing_rights", [])
        ws.roles = d.get("roles", {})
        ws.events_log = d.get("events_log", [])
        ws.nuclear_used_this_sim = d.get("nuclear_used_this_sim", False)
        ws.ground_blockades = d.get("ground_blockades", {})
        ws.active_blockades = d.get("active_blockades", {})
        ws.rare_earth_restrictions = d.get("rare_earth_restrictions", {})
        ws.formosa_blockade = d.get("formosa_blockade", False)
        return ws

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


# ---------------------------------------------------------------------------
# TRADE WEIGHT MATRIX (derived from GDP + sector complementarity)
# ---------------------------------------------------------------------------

def derive_trade_weights(countries: Dict[str, dict]) -> Dict[str, Dict[str, float]]:
    """Derive approximate bilateral trade weights from GDP and sector profiles."""
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
            comp = (sec_a.get("industry", 0) * sec_b.get("resources", 0)
                    + sec_a.get("resources", 0) * sec_b.get("industry", 0)
                    + sec_a.get("technology", 0) * sec_b.get("services", 0)
                    + sec_a.get("services", 0) * sec_b.get("technology", 0))
            comp = max(comp, 1.0)
            raw[a][b] = gdp_a * gdp_b * comp
    weights: Dict[str, Dict[str, float]] = {}
    for a in ids:
        total = sum(raw[a].values())
        if total == 0:
            weights[a] = {b: 0.0 for b in ids if b != a}
        else:
            weights[a] = {b: raw[a][b] / total for b in ids if b != a}
    return weights


# ---------------------------------------------------------------------------
# UTILITY
# ---------------------------------------------------------------------------

def clamp(value: float, min_val: float, max_val: float) -> float:
    return max(min_val, min(max_val, value))
