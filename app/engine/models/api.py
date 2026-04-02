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
