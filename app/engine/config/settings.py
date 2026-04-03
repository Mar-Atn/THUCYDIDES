"""Centralized settings — single source for all environment config."""

from enum import Enum
from pathlib import Path
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class LLMProvider(str, Enum):
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"


class LLMUseCase(str, Enum):
    """Each use case maps to a provider + model via LLM_MODELS config."""
    MODERATOR = "moderator"       # Argus Super-Moderator — needs best reasoning
    AGENT_DECISION = "agent_decision"  # AI country strategic decisions
    AGENT_CONVERSATION = "agent_conversation"  # AI-to-AI dialogue turns
    AGENT_REFLECTION = "agent_reflection"  # Post-round cognitive block updates
    QUICK_SCAN = "quick_scan"     # Tier 1 fast evaluations
    NARRATIVE = "narrative"       # News generation, event descriptions


class LLMModelConfig:
    """Model assignment per use case. Update when models change."""

    # See app/config/LLM_MODELS.md for full reference
    MODELS: dict[LLMUseCase, dict] = {
        LLMUseCase.MODERATOR: {
            "primary": {"provider": LLMProvider.ANTHROPIC, "model": "claude-sonnet-4-20250514"},
            "fallback": {"provider": LLMProvider.GEMINI, "model": "gemini-2.5-pro"},
            "max_tokens": 4096,
        },
        LLMUseCase.AGENT_DECISION: {
            "primary": {"provider": LLMProvider.ANTHROPIC, "model": "claude-sonnet-4-20250514"},
            "fallback": {"provider": LLMProvider.GEMINI, "model": "gemini-2.5-flash"},
            "max_tokens": 2048,
        },
        LLMUseCase.AGENT_CONVERSATION: {
            "primary": {"provider": LLMProvider.ANTHROPIC, "model": "claude-sonnet-4-20250514"},
            "fallback": {"provider": LLMProvider.GEMINI, "model": "gemini-2.5-flash"},
            "max_tokens": 1024,
        },
        LLMUseCase.AGENT_REFLECTION: {
            "primary": {"provider": LLMProvider.ANTHROPIC, "model": "claude-sonnet-4-20250514"},
            "fallback": {"provider": LLMProvider.GEMINI, "model": "gemini-2.5-pro"},
            "max_tokens": 2048,
        },
        LLMUseCase.QUICK_SCAN: {
            "primary": {"provider": LLMProvider.GEMINI, "model": "gemini-2.5-flash-lite"},
            "fallback": {"provider": LLMProvider.ANTHROPIC, "model": "claude-haiku-4-5-20251001"},
            "max_tokens": 512,
        },
        LLMUseCase.NARRATIVE: {
            "primary": {"provider": LLMProvider.GEMINI, "model": "gemini-2.5-flash"},
            "fallback": {"provider": LLMProvider.ANTHROPIC, "model": "claude-haiku-4-5-20251001"},
            "max_tokens": 2048,
        },
    }

    @classmethod
    def get(cls, use_case: LLMUseCase) -> dict:
        return cls.MODELS[use_case]


class Settings(BaseSettings):
    """Environment-based settings with validation."""

    # --- Supabase ---
    supabase_url: str = Field(..., description="Supabase project URL")
    supabase_anon_key: str = Field(..., description="Supabase publishable anon key")
    supabase_service_role_key: str = Field(..., description="Supabase service role key (server-side only)")

    # --- LLM Providers ---
    anthropic_api_key: str = Field(default="", description="Anthropic Claude API key")
    google_ai_api_key: str = Field(default="", description="Google Gemini API key")

    # --- ElevenLabs (Phase 3) ---
    elevenlabs_api_key: str = Field(default="", description="ElevenLabs voice API key")

    # --- App Config ---
    app_env: str = Field(default="development", description="development | staging | production")
    log_level: str = Field(default="INFO", description="Logging level")
    cors_origins: list[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000"],
        description="Allowed CORS origins",
    )

    # --- Engine Config ---
    default_sim_id: str = Field(
        default="00000000-0000-0000-0000-000000000001",
        description="Default SIM run ID for development",
    )
    max_rounds: int = Field(default=8, description="Maximum rounds per SIM")

    model_config = {
        "env_file": str(Path(__file__).resolve().parents[3] / ".env"),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def has_anthropic(self) -> bool:
        return bool(self.anthropic_api_key)

    @property
    def has_gemini(self) -> bool:
        return bool(self.google_ai_api_key)

    def get_llm_config(self, use_case: LLMUseCase) -> dict:
        """Get model config for a use case, respecting available providers."""
        config = LLMModelConfig.get(use_case)
        primary = config["primary"]
        fallback = config["fallback"]

        # Check if primary provider is available
        if primary["provider"] == LLMProvider.ANTHROPIC and not self.has_anthropic:
            return {**fallback, "max_tokens": config["max_tokens"]}
        if primary["provider"] == LLMProvider.GEMINI and not self.has_gemini:
            return {**fallback, "max_tokens": config["max_tokens"]}

        return {**primary, "max_tokens": config["max_tokens"]}


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()


# Module-level convenience
settings = get_settings()
