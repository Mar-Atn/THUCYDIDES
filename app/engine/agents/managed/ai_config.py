"""AI configuration reader — loads settings from sim_config table.

Settings are managed via M9 AI System Setup screen (global, across all sim runs).
Stored in sim_config table with category='ai'.

Settings:
  - ai/model_decisions: Claude model for AI participant decisions
  - ai/model_conversations: Claude model for AI conversations (future: faster model)
  - ai/assertiveness: Global assertiveness dial (1-10, default 5)

Falls back to defaults if not configured.
"""
from __future__ import annotations

import logging
from functools import lru_cache

from engine.services.supabase import get_client

logger = logging.getLogger(__name__)

# Defaults — used when sim_config has no entry
DEFAULT_MODEL_DECISIONS = "claude-sonnet-4-6"
DEFAULT_MODEL_CONVERSATIONS = "claude-sonnet-4-6"
DEFAULT_ASSERTIVENESS = 5


def get_ai_model(use_case: str = "decisions") -> str:
    """Get the configured AI model for a use case.

    Args:
        use_case: "decisions" or "conversations"

    Returns:
        Model ID string (e.g., "claude-sonnet-4-6")
    """
    key = f"model_{use_case}"
    default = DEFAULT_MODEL_DECISIONS if use_case == "decisions" else DEFAULT_MODEL_CONVERSATIONS

    try:
        db = get_client()
        result = (
            db.table("sim_config")
            .select("content")
            .eq("category", "ai")
            .eq("key", key)
            .eq("is_active", True)
            .limit(1)
            .execute()
        )
        if result.data and result.data[0].get("content"):
            model = result.data[0]["content"].strip()
            logger.info("[ai_config] Using model %s=%s", use_case, model)
            return model
    except Exception as e:
        logger.warning("[ai_config] Failed to read model config: %s", e)

    return default


def get_assertiveness() -> int:
    """Get the global assertiveness dial (1-10).

    1 = very cooperative/accommodating
    5 = balanced (default)
    10 = very assertive/competitive

    Affects AI agent system prompts — shifts decision-making tendency.
    """
    try:
        db = get_client()
        result = (
            db.table("sim_config")
            .select("content")
            .eq("category", "ai")
            .eq("key", "assertiveness")
            .eq("is_active", True)
            .limit(1)
            .execute()
        )
        if result.data and result.data[0].get("content"):
            val = int(result.data[0]["content"])
            return max(1, min(10, val))
    except Exception as e:
        logger.warning("[ai_config] Failed to read assertiveness: %s", e)

    return DEFAULT_ASSERTIVENESS
