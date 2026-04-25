"""AI configuration reader — loads settings from ai_settings table.

Settings are managed via AI Settings page (global, across all sim runs).
Stored in ai_settings table (key → value).

Two categories of AI model usage:
  1. Managed Agent sessions (M5): model_decisions, model_conversations, assertiveness
     → Locked at initialization. Changing requires Shutdown → Re-initialize.
  2. Stateless API calls: model_stateless
     → Intelligence, chat, Navigator. Changes take effect immediately.

Settings:
  - model_decisions: Claude model for AI participant strategic decisions
  - model_conversations: Claude model for bilateral meetings
  - model_stateless: Claude model for stateless API calls (intelligence, chat, etc.)
  - assertiveness: Global assertiveness dial (1-10, default 5)

Falls back to defaults if not configured.
"""
from __future__ import annotations

import logging

from engine.services.supabase import get_client

logger = logging.getLogger(__name__)

# Defaults — used when ai_settings has no entry
DEFAULT_MODEL_DECISIONS = "claude-sonnet-4-6"
DEFAULT_MODEL_CONVERSATIONS = "claude-sonnet-4-6"
DEFAULT_MODEL_STATELESS = "claude-sonnet-4-6"
DEFAULT_ASSERTIVENESS = 5


def _read_setting(key: str, default: str = "") -> str:
    """Read a single value from ai_settings table."""
    try:
        db = get_client()
        result = (
            db.table("ai_settings")
            .select("value")
            .eq("key", key)
            .limit(1)
            .execute()
        )
        if result.data and result.data[0].get("value"):
            return result.data[0]["value"].strip()
    except Exception as e:
        logger.warning("[ai_config] Failed to read %s: %s", key, e)
    return default


def get_ai_model(use_case: str = "decisions") -> str:
    """Get the configured AI model for a use case.

    Args:
        use_case: "decisions", "conversations", or "stateless"

    Returns:
        Model ID string (e.g., "claude-sonnet-4-6")

    Note:
        - "decisions" and "conversations" are locked at agent initialization.
        - "stateless" changes take effect immediately on next API call.
    """
    key = f"model_{use_case}"
    defaults = {
        "decisions": DEFAULT_MODEL_DECISIONS,
        "conversations": DEFAULT_MODEL_CONVERSATIONS,
        "stateless": DEFAULT_MODEL_STATELESS,
    }
    default = defaults.get(use_case, DEFAULT_MODEL_DECISIONS)

    model = _read_setting(key, default)
    if model != default:
        logger.info("[ai_config] Using model %s=%s", use_case, model)
    return model


def get_assertiveness() -> int:
    """Get the global assertiveness dial (1-10).

    1 = very cooperative/accommodating
    5 = balanced (default)
    10 = very assertive/competitive

    Applied at agent session initialization — baked into the immutable
    system prompt. Changing requires reinitializing agents.
    """
    val_str = _read_setting("assertiveness", str(DEFAULT_ASSERTIVENESS))
    try:
        return max(1, min(10, int(val_str)))
    except (ValueError, TypeError):
        return DEFAULT_ASSERTIVENESS
