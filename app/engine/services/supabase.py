"""Supabase client wrapper — typed CRUD operations.

All DB access goes through this module. No raw queries elsewhere.
Uses service_role key (bypasses RLS) since engine is trusted server-side code.
"""

import logging
from typing import Optional

from supabase import create_client, Client

from engine.config import settings
from engine.models.db import (
    SimRun, Country, Role, Zone, ZoneAdjacency,
    Deployment, Organization, OrgMembership,
    Relationship, Sanction, Tariff, WorldState,
)

logger = logging.getLogger(__name__)

_client: Optional[Client] = None


def get_client() -> Client:
    """Get or create the Supabase client singleton."""
    global _client
    if _client is None:
        _client = create_client(
            settings.supabase_url,
            settings.supabase_service_role_key,
        )
        logger.info("Supabase client initialized")
    return _client


async def check_connection() -> bool:
    """Verify DB connection by querying sim_runs count."""
    try:
        client = get_client()
        result = client.table("sim_runs").select("id", count="exact").execute()
        return result.count is not None
    except Exception as e:
        logger.error("Supabase connection check failed: %s", e)
        return False


# ---------------------------------------------------------------------------
# SIM Run
# ---------------------------------------------------------------------------

async def get_sim_run(sim_id: str) -> Optional[SimRun]:
    """Fetch a SIM run by ID."""
    client = get_client()
    result = client.table("sim_runs").select("*").eq("id", sim_id).execute()
    if result.data:
        return SimRun(**result.data[0])
    return None


# ---------------------------------------------------------------------------
# Countries
# ---------------------------------------------------------------------------

async def get_countries(sim_id: str) -> list[Country]:
    """Fetch all countries for a SIM run."""
    client = get_client()
    result = (
        client.table("countries")
        .select("*")
        .eq("sim_run_id", sim_id)
        .order("id")
        .execute()
    )
    return [Country(**row) for row in result.data]


async def get_country(sim_id: str, country_id: str) -> Optional[Country]:
    """Fetch a single country."""
    client = get_client()
    result = (
        client.table("countries")
        .select("*")
        .eq("sim_run_id", sim_id)
        .eq("id", country_id)
        .execute()
    )
    if result.data:
        return Country(**result.data[0])
    return None


# ---------------------------------------------------------------------------
# Roles
# ---------------------------------------------------------------------------

async def get_roles(sim_id: str, country_id: Optional[str] = None) -> list[Role]:
    """Fetch roles, optionally filtered by country."""
    client = get_client()
    query = client.table("roles").select("*").eq("sim_run_id", sim_id)
    if country_id:
        query = query.eq("country_id", country_id)
    result = query.order("id").execute()
    return [Role(**row) for row in result.data]


# ---------------------------------------------------------------------------
# Zones & Map
# ---------------------------------------------------------------------------

async def get_zones(sim_id: str, theater: Optional[str] = None) -> list[Zone]:
    """Fetch zones, optionally filtered by theater."""
    client = get_client()
    query = client.table("zones").select("*").eq("sim_run_id", sim_id)
    if theater:
        query = query.eq("theater", theater)
    result = query.order("id").execute()
    return [Zone(**row) for row in result.data]


async def get_zone_adjacency(sim_id: str) -> list[ZoneAdjacency]:
    """Fetch all zone adjacency records."""
    client = get_client()
    result = (
        client.table("zone_adjacency")
        .select("*")
        .eq("sim_run_id", sim_id)
        .execute()
    )
    return [ZoneAdjacency(**row) for row in result.data]


# ---------------------------------------------------------------------------
# Military
# ---------------------------------------------------------------------------

async def get_deployments(
    sim_id: str,
    country_id: Optional[str] = None,
    zone_id: Optional[str] = None,
) -> list[Deployment]:
    """Fetch deployments with optional filters."""
    client = get_client()
    query = client.table("deployments").select("*").eq("sim_run_id", sim_id)
    if country_id:
        query = query.eq("country_id", country_id)
    if zone_id:
        query = query.eq("zone_id", zone_id)
    result = query.execute()
    return [Deployment(**row) for row in result.data]


# ---------------------------------------------------------------------------
# Diplomacy
# ---------------------------------------------------------------------------

async def get_relationships(sim_id: str, country_id: Optional[str] = None) -> list[Relationship]:
    """Fetch bilateral relationships."""
    client = get_client()
    query = client.table("relationships").select("*").eq("sim_run_id", sim_id)
    if country_id:
        query = query.eq("from_country_id", country_id)
    result = query.execute()
    return [Relationship(**row) for row in result.data]


async def get_sanctions(sim_id: str) -> list[Sanction]:
    """Fetch all active sanctions."""
    client = get_client()
    result = client.table("sanctions").select("*").eq("sim_run_id", sim_id).execute()
    return [Sanction(**row) for row in result.data]


async def get_tariffs(sim_id: str) -> list[Tariff]:
    """Fetch all active tariffs."""
    client = get_client()
    result = client.table("tariffs").select("*").eq("sim_run_id", sim_id).execute()
    return [Tariff(**row) for row in result.data]


# ---------------------------------------------------------------------------
# Organizations
# ---------------------------------------------------------------------------

async def get_organizations(sim_id: str) -> list[Organization]:
    """Fetch all organizations."""
    client = get_client()
    result = client.table("organizations").select("*").eq("sim_run_id", sim_id).execute()
    return [Organization(**row) for row in result.data]


async def get_org_memberships(sim_id: str) -> list[OrgMembership]:
    """Fetch all org memberships."""
    client = get_client()
    result = client.table("org_memberships").select("*").eq("sim_run_id", sim_id).execute()
    return [OrgMembership(**row) for row in result.data]


# ---------------------------------------------------------------------------
# World State
# ---------------------------------------------------------------------------

async def get_world_state(sim_id: str, round_num: Optional[int] = None) -> Optional[WorldState]:
    """Fetch world state. If round_num is None, get the latest."""
    client = get_client()
    query = client.table("world_state").select("*").eq("sim_run_id", sim_id)
    if round_num is not None:
        query = query.eq("round_num", round_num)
    else:
        query = query.order("round_num", desc=True).limit(1)
    result = query.execute()
    if result.data:
        return WorldState(**result.data[0])
    return None
