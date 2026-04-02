"""FastAPI entry point — TTT Engine API.

Health check, SIM state queries, LLM test endpoint.
"""

import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from engine.config import settings
from engine.models.api import (
    APIResponse, HealthStatus, LLMTestRequest, LLMTestResponse, CountryListResponse,
)
from engine.services import supabase as db
from engine.services import llm
from engine.config.settings import LLMUseCase

logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("TTT Engine starting — env=%s", settings.app_env)
    logger.info("Supabase: %s", settings.supabase_url)
    logger.info("Anthropic: %s", "configured" if settings.has_anthropic else "NOT configured")
    logger.info("Gemini: %s", "configured" if settings.has_gemini else "NOT configured")
    yield
    logger.info("TTT Engine shutting down")


app = FastAPI(
    title="Thucydides Trap Engine",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health", response_model=APIResponse)
async def health():
    """Infrastructure health check."""
    db_ok = await db.check_connection()
    anthropic_ok = await llm.check_anthropic()
    gemini_ok = await llm.check_gemini()

    status = HealthStatus(
        status="ok" if db_ok else "degraded",
        db="connected" if db_ok else "error",
        llm_anthropic="ok" if anthropic_ok else "unavailable",
        llm_gemini="ok" if gemini_ok else "unavailable",
        sim_id=settings.default_sim_id,
        version="0.1.0",
    )
    return APIResponse(success=db_ok, data=status.model_dump())


# ---------------------------------------------------------------------------
# SIM state endpoints
# ---------------------------------------------------------------------------

@app.get("/api/sim/{sim_id}/countries", response_model=APIResponse)
async def get_countries(sim_id: str):
    """Get all countries for a SIM run."""
    countries = await db.get_countries(sim_id)
    if not countries:
        raise HTTPException(status_code=404, detail=f"No countries found for SIM {sim_id}")
    return APIResponse(
        data=CountryListResponse(
            sim_id=sim_id,
            count=len(countries),
            countries=[c.model_dump() for c in countries],
        ).model_dump()
    )


@app.get("/api/sim/{sim_id}/country/{country_id}", response_model=APIResponse)
async def get_country(sim_id: str, country_id: str):
    """Get a single country's full state."""
    country = await db.get_country(sim_id, country_id)
    if not country:
        raise HTTPException(status_code=404, detail=f"Country {country_id} not found")
    return APIResponse(data=country.model_dump())


@app.get("/api/sim/{sim_id}/roles", response_model=APIResponse)
async def get_roles(sim_id: str, country_id: Optional[str] = None):
    """Get roles, optionally filtered by country."""
    roles = await db.get_roles(sim_id, country_id)
    return APIResponse(data=[r.model_dump() for r in roles], meta={"count": len(roles)})


@app.get("/api/sim/{sim_id}/zones", response_model=APIResponse)
async def get_zones(sim_id: str, theater: Optional[str] = None):
    """Get map zones, optionally filtered by theater."""
    zones = await db.get_zones(sim_id, theater)
    return APIResponse(data=[z.model_dump() for z in zones], meta={"count": len(zones)})


@app.get("/api/sim/{sim_id}/deployments", response_model=APIResponse)
async def get_deployments(
    sim_id: str,
    country_id: Optional[str] = None,
    zone_id: Optional[str] = None,
):
    """Get military deployments with optional filters."""
    deployments = await db.get_deployments(sim_id, country_id, zone_id)
    return APIResponse(data=[d.model_dump() for d in deployments], meta={"count": len(deployments)})


@app.get("/api/sim/{sim_id}/world", response_model=APIResponse)
async def get_world_state(sim_id: str, round_num: Optional[int] = None):
    """Get world state snapshot."""
    world = await db.get_world_state(sim_id, round_num)
    if not world:
        raise HTTPException(status_code=404, detail="World state not found")
    return APIResponse(data=world.model_dump())


@app.get("/api/sim/{sim_id}/relationships", response_model=APIResponse)
async def get_relationships(sim_id: str, country_id: Optional[str] = None):
    """Get bilateral relationships."""
    rels = await db.get_relationships(sim_id, country_id)
    return APIResponse(data=[r.model_dump() for r in rels], meta={"count": len(rels)})


@app.get("/api/sim/{sim_id}/sanctions", response_model=APIResponse)
async def get_sanctions(sim_id: str):
    """Get all active sanctions."""
    sanctions = await db.get_sanctions(sim_id)
    return APIResponse(data=[s.model_dump() for s in sanctions], meta={"count": len(sanctions)})


@app.get("/api/sim/{sim_id}/organizations", response_model=APIResponse)
async def get_organizations(sim_id: str):
    """Get all organizations and memberships."""
    orgs = await db.get_organizations(sim_id)
    memberships = await db.get_org_memberships(sim_id)
    return APIResponse(
        data={
            "organizations": [o.model_dump() for o in orgs],
            "memberships": [m.model_dump() for m in memberships],
        },
        meta={"org_count": len(orgs), "membership_count": len(memberships)},
    )


# ---------------------------------------------------------------------------
# LLM test endpoint
# ---------------------------------------------------------------------------

@app.post("/api/test/llm", response_model=APIResponse)
async def test_llm(request: LLMTestRequest):
    """Test LLM connectivity. Sends a prompt and returns the response."""
    try:
        result = await llm.call_llm(
            use_case=LLMUseCase.QUICK_SCAN,
            messages=[{"role": "user", "content": request.prompt}],
        )
        return APIResponse(
            data=LLMTestResponse(
                provider=result.provider,
                model=result.model,
                response_text=result.text,
                tokens_in=result.tokens_in,
                tokens_out=result.tokens_out,
            ).model_dump()
        )
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@app.get("/api/llm/health", response_model=APIResponse)
async def llm_health():
    """Get LLM provider health statistics."""
    return APIResponse(data=llm.get_health_stats())
