"""Pydantic models mirroring Supabase DB tables.

Source of truth: DET_B1_DATABASE_SCHEMA.sql
These models are used for typed query results and API responses.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Core tables
# ---------------------------------------------------------------------------

class SimRun(BaseModel):
    """sim_runs table."""
    id: str
    name: str
    status: str  # setup | active | paused | completed | aborted
    current_round: int = 0
    current_phase: str = "pre"  # pre | A | B | C | post
    config: dict = Field(default_factory=dict)
    max_rounds: int = 8
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class Country(BaseModel):
    """countries table — full country state."""
    id: str
    sim_run_id: str
    sim_name: str
    parallel: str = ""
    regime_type: str  # democracy | autocracy | hybrid
    team_type: str  # team | solo | europe
    team_size_min: int = 1
    team_size_max: int = 1
    ai_default: bool = True

    # Economic
    gdp: float = 0
    gdp_growth_base: float = 0
    sector_resources: int = 0
    sector_industry: int = 0
    sector_services: int = 0
    sector_technology: int = 0
    tax_rate: float = 0
    treasury: float = 0
    inflation: float = 0
    trade_balance: float = 0
    oil_producer: bool = False
    opec_member: bool = False
    opec_production: str = "na"
    formosa_dependency: float = 0
    debt_burden: float = 0
    social_baseline: float = 0.20
    oil_production_mbpd: float = 0.0  # D5: million barrels per day

    # Calibration baselines (persisted for delta-only calculations)
    # (sanctions_recovery_rounds + sanctions_adaptation_rounds DROPPED 2026-04-10
    #  per CONTRACT_SANCTIONS v1.0 — temporal adaptation removed entirely)
    sanctions_coefficient: float = 1.0
    tariff_coefficient: float = 1.0

    # Military
    mil_ground: int = 0
    mil_naval: int = 0
    mil_tactical_air: int = 0
    mil_strategic_missiles: int = 0
    mil_air_defense: int = 0
    prod_cost_ground: float = 3
    prod_cost_naval: float = 5
    prod_cost_tactical: float = 4
    prod_cap_ground: int = 2
    prod_cap_naval: int = 1
    prod_cap_tactical: int = 1
    maintenance_per_unit: float = 0.3
    strategic_missile_growth: int = 0
    mobilization_pool: int = 0

    # Political
    stability: float = 5
    political_support: float = 50  # DEPRECATED 2026-04-15: use stability only
    dem_rep_split_dem: int = 0  # DEPRECATED 2026-04-15: parliament simplified to 3 seats
    dem_rep_split_rep: int = 0  # DEPRECATED 2026-04-15: parliament simplified to 3 seats
    war_tiredness: float = 0

    # Technology
    nuclear_level: int = 0
    nuclear_rd_progress: float = 0
    ai_level: int = 0
    ai_rd_progress: float = 0

    # Zones
    home_zones: str = ""


class Role(BaseModel):
    """roles table."""
    id: str
    sim_run_id: str
    user_id: Optional[str] = None
    character_name: str
    parallel: str = ""
    country_id: str
    team: str = ""
    faction: str = ""
    title: str = ""
    age: int = 50
    gender: str = "M"
    is_head_of_state: bool = False
    is_military_chief: bool = False
    parliament_seat: int = 0
    personal_coins: float = 0  # DEPRECATED 2026-04-15: no personal transactions
    personal_coins_notes: str = ""  # DEPRECATED 2026-04-15
    expansion_role: bool = False
    ai_candidate: bool = False
    is_ai_operated: bool = False
    brief_file: str = ""
    intelligence_pool: int = 0
    powers: list[str] = Field(default_factory=list)
    objectives: list[str] = Field(default_factory=list)
    ticking_clock: str = ""
    status: str = "active"
    # Covert ops cards
    sabotage_cards: int = 0
    cyber_cards: int = 0
    disinfo_cards: int = 0
    election_meddling_cards: int = 0
    assassination_cards: int = 0
    protest_stim_cards: int = 0
    fatherland_appeal: int = 0
    is_diplomat: bool = False


class Zone(BaseModel):
    """zones table."""
    id: str
    sim_run_id: str
    display_name: str
    type: str  # land_home | land_contested | sea | chokepoint | chokepoint_sea
    owner: str = "none"
    controlled_by: Optional[str] = None
    theater: str = "global"
    is_chokepoint: bool = False
    die_hard: bool = False


class ZoneAdjacency(BaseModel):
    """zone_adjacency table."""
    id: str
    sim_run_id: str
    zone_a: str
    zone_b: str
    connection_type: str = "land_land"


class Deployment(BaseModel):
    """deployments table."""
    id: str
    sim_run_id: str
    country_id: str
    unit_type: str  # ground | naval | tactical_air | strategic_missile | air_defense
    count: int = 0
    zone_id: str
    notes: str = ""


class Organization(BaseModel):
    """organizations table."""
    id: str
    sim_run_id: str
    sim_name: str
    parallel: str = ""
    decision_rule: str = "consensus"
    chair_role_id: str = ""
    voting_threshold: str = "unanimous"
    meeting_frequency: str = ""
    can_be_created: bool = False
    description: str = ""


class OrgMembership(BaseModel):
    """org_memberships table."""
    sim_run_id: str
    country_id: str
    org_id: str
    role_in_org: str = "member"
    has_veto: bool = False


class Relationship(BaseModel):
    """relationships table.

    Dual-column semantics (2026-04-08):
      relationship = STARTING/REFERENCE value (frozen per template, legacy labels)
      status       = LIVE engine state (canonical 8-state model, updated during play)
    Engine reads `status` for all war/peace checks.
    """
    sim_run_id: str
    from_country_id: str
    to_country_id: str
    relationship: str  # close_ally | alliance | friendly | neutral | tense | hostile | at_war | strategic_rival
    status: str = "neutral"  # allied | friendly | neutral | tense | hostile | military_conflict | armistice | peace
    basing_rights_a_to_b: bool = False
    basing_rights_b_to_a: bool = False
    dynamic: str = ""


class Sanction(BaseModel):
    """sanctions table."""
    sim_run_id: str
    imposer_country_id: str
    target_country_id: str
    level: int = 0  # -1 to 3 (-1 = evasion support)
    notes: str = ""


class Tariff(BaseModel):
    """tariffs table."""
    sim_run_id: str
    imposer_country_id: str
    target_country_id: str
    level: int = 0  # 0-3
    notes: str = ""


class WorldState(BaseModel):
    """world_state table — global state snapshot per round."""
    sim_run_id: str
    round_num: int = 0
    oil_price: float = 80.0
    oil_price_index: float = 100.0
    global_trade_volume_index: float = 100.0
    dollar_credibility: float = 100.0
    nuclear_used_this_sim: bool = False
    formosa_blockade: bool = False
    opec_production: dict = Field(default_factory=dict)
    chokepoint_status: dict = Field(default_factory=dict)
    wars: list[dict] = Field(default_factory=list)
    active_blockades: dict = Field(default_factory=dict)
    market_indexes: dict = Field(default_factory=dict)  # {wall_street, europa, dragon} floats
    is_frozen: bool = False
    schema_version: str = "1.0"
