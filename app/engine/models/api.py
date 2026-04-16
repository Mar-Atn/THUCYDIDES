"""API request/response schemas for FastAPI endpoints."""

from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Standard response envelope
# ---------------------------------------------------------------------------

class APIResponse(BaseModel):
    """Standard API response wrapper."""
    success: bool = True
    data: Any = None
    error: Optional[str] = None
    meta: dict = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

class HealthStatus(BaseModel):
    status: str = "ok"
    db: str = "unknown"
    llm_anthropic: str = "unknown"
    llm_gemini: str = "unknown"
    sim_id: str = ""
    version: str = "0.1.0"


# ---------------------------------------------------------------------------
# LLM test endpoint
# ---------------------------------------------------------------------------

class LLMTestRequest(BaseModel):
    prompt: str = "Say OK"
    provider: Optional[str] = None  # anthropic | gemini | None (auto)
    model: Optional[str] = None  # Override specific model


class LLMTestResponse(BaseModel):
    provider: str
    model: str
    response_text: str
    tokens_in: int = 0
    tokens_out: int = 0


# ---------------------------------------------------------------------------
# SIM state queries
# ---------------------------------------------------------------------------

class SimStateQuery(BaseModel):
    """Query parameters for state endpoints."""
    sim_id: str
    round_num: Optional[int] = None  # None = current round
    country_id: Optional[str] = None  # Filter by country


class CountryListResponse(BaseModel):
    """Response for /api/sim/{id}/countries."""
    sim_id: str
    count: int
    countries: list[dict]


# ---------------------------------------------------------------------------
# Action submission (M4 Sprint 2.1)
# ---------------------------------------------------------------------------

class ActionSubmission(BaseModel):
    """POST /api/sim/{id}/action request body.

    The action_type determines which engine processes it.
    role_id + country_code identify who is acting.
    params holds action-specific data (varies by action_type).
    """
    action_type: str
    role_id: str
    country_code: str
    params: dict = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# SimRun creation (M4 / M9 — data inheritance)
# ---------------------------------------------------------------------------

class RoleCustomization(BaseModel):
    """Per-role customization from the wizard."""
    role_id: str
    active: bool = True
    is_ai_operated: bool = True


class SimRunCreateRequest(BaseModel):
    """POST /api/sim/create request body.

    Creates a new SimRun by copying all template data from the source sim
    and applying wizard customizations.
    """
    name: str
    source_sim_id: str = "00000000-0000-0000-0000-000000000001"
    template_id: str
    schedule: dict = Field(default_factory=dict)
    key_events: list = Field(default_factory=list)
    max_rounds: int = 6
    description: Optional[str] = None
    logo_url: Optional[str] = None
    role_customizations: list[RoleCustomization] = Field(default_factory=list)
