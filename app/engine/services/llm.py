"""Dual-provider LLM service — Anthropic Claude + Google Gemini.

Provides a single call_llm() interface. Provider selection, failover,
and model health monitoring are handled internally.
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Optional

from engine.config.settings import LLMProvider, LLMUseCase, settings

logger = logging.getLogger(__name__)

# Lazy imports — only load SDKs when first needed
_anthropic_client = None
_gemini_client = None


def _get_anthropic():
    global _anthropic_client
    if _anthropic_client is None:
        from anthropic import Anthropic
        _anthropic_client = Anthropic(api_key=settings.anthropic_api_key)
        logger.info("Anthropic client initialized")
    return _anthropic_client


def _get_gemini():
    global _gemini_client
    if _gemini_client is None:
        from google import genai
        _gemini_client = genai.Client(api_key=settings.google_ai_api_key)
        logger.info("Gemini client initialized")
    return _gemini_client


# ---------------------------------------------------------------------------
# Provider health tracking (ported from KING pattern)
# ---------------------------------------------------------------------------

@dataclass
class ProviderHealth:
    """Track provider reliability for automatic failover."""
    errors: int = 0
    last_error_time: float = 0
    consecutive_errors: int = 0
    total_calls: int = 0
    total_tokens_in: int = 0
    total_tokens_out: int = 0

    @property
    def is_healthy(self) -> bool:
        """Provider is healthy if <3 consecutive errors or last error >60s ago."""
        if self.consecutive_errors < 3:
            return True
        return (time.time() - self.last_error_time) > 60

    def record_success(self, tokens_in: int = 0, tokens_out: int = 0) -> None:
        self.consecutive_errors = 0
        self.total_calls += 1
        self.total_tokens_in += tokens_in
        self.total_tokens_out += tokens_out

    def record_error(self) -> None:
        self.errors += 1
        self.consecutive_errors += 1
        self.last_error_time = time.time()
        self.total_calls += 1


_health: dict[LLMProvider, ProviderHealth] = {
    LLMProvider.ANTHROPIC: ProviderHealth(),
    LLMProvider.GEMINI: ProviderHealth(),
}


# ---------------------------------------------------------------------------
# Core LLM call
# ---------------------------------------------------------------------------

@dataclass
class LLMResponse:
    """Standardized response from any LLM provider."""
    text: str
    provider: str
    model: str
    tokens_in: int = 0
    tokens_out: int = 0
    latency_ms: int = 0


async def call_llm(
    use_case: LLMUseCase,
    messages: list[dict],
    system: Optional[str] = None,
    max_tokens: Optional[int] = None,
    temperature: float = 0.7,
) -> LLMResponse:
    """Call an LLM with automatic provider selection and failover.

    Args:
        use_case: Determines which model to use (see LLMModelConfig).
        messages: List of {"role": "user"|"assistant", "content": "..."}.
        system: System prompt (optional).
        max_tokens: Override default max tokens for this use case.
        temperature: Sampling temperature.

    Returns:
        LLMResponse with text, provider info, and token usage.
    """
    config = settings.get_llm_config(use_case)
    model_config = LLMModelConfig_get_with_fallback(config, use_case)

    provider = LLMProvider(model_config["provider"])
    model = model_config["model"]
    tok_limit = max_tokens or model_config.get("max_tokens", 1024)

    # Try primary, fallback on error
    try:
        return await _call_provider(provider, model, messages, system, tok_limit, temperature)
    except Exception as e:
        logger.warning("LLM call failed (provider=%s, model=%s): %s", provider, model, e)
        _health[provider].record_error()

        # Try fallback
        fallback_config = _get_fallback(use_case, provider)
        if fallback_config:
            fb_provider = LLMProvider(fallback_config["provider"])
            fb_model = fallback_config["model"]
            logger.info("Falling back to %s/%s", fb_provider, fb_model)
            try:
                return await _call_provider(fb_provider, fb_model, messages, system, tok_limit, temperature)
            except Exception as e2:
                logger.error("Fallback also failed: %s", e2)
                _health[fb_provider].record_error()
                raise

        raise


def LLMModelConfig_get_with_fallback(config: dict, use_case: LLMUseCase) -> dict:
    """Select provider based on health status."""
    from engine.config.settings import LLMModelConfig
    full_config = LLMModelConfig.get(use_case)
    primary = full_config["primary"]
    fallback = full_config["fallback"]

    primary_provider = LLMProvider(primary["provider"])
    if _health[primary_provider].is_healthy:
        return {**primary, "max_tokens": full_config["max_tokens"]}
    else:
        logger.warning("Primary provider %s unhealthy, using fallback", primary_provider)
        return {**fallback, "max_tokens": full_config["max_tokens"]}


def _get_fallback(use_case: LLMUseCase, failed_provider: LLMProvider) -> Optional[dict]:
    """Get fallback config for a use case after primary fails."""
    from engine.config.settings import LLMModelConfig
    full_config = LLMModelConfig.get(use_case)
    primary = full_config["primary"]
    fallback = full_config["fallback"]

    if LLMProvider(primary["provider"]) == failed_provider:
        return fallback
    return primary


async def _call_provider(
    provider: LLMProvider,
    model: str,
    messages: list[dict],
    system: Optional[str],
    max_tokens: int,
    temperature: float,
) -> LLMResponse:
    """Dispatch to the correct provider SDK."""
    start = time.time()

    if provider == LLMProvider.ANTHROPIC:
        result = _call_anthropic(model, messages, system, max_tokens, temperature)
    elif provider == LLMProvider.GEMINI:
        result = _call_gemini(model, messages, system, max_tokens, temperature)
    else:
        raise ValueError(f"Unknown provider: {provider}")

    result.latency_ms = int((time.time() - start) * 1000)
    _health[provider].record_success(result.tokens_in, result.tokens_out)

    logger.debug(
        "LLM call: provider=%s model=%s tokens=%d/%d latency=%dms",
        provider, model, result.tokens_in, result.tokens_out, result.latency_ms,
    )
    return result


def _call_anthropic(
    model: str,
    messages: list[dict],
    system: Optional[str],
    max_tokens: int,
    temperature: float,
) -> LLMResponse:
    """Call Anthropic Claude API."""
    client = _get_anthropic()
    kwargs = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": messages,
        "temperature": temperature,
    }
    if system:
        kwargs["system"] = system

    response = client.messages.create(**kwargs)

    return LLMResponse(
        text=response.content[0].text,
        provider="anthropic",
        model=model,
        tokens_in=response.usage.input_tokens,
        tokens_out=response.usage.output_tokens,
    )


def _call_gemini(
    model: str,
    messages: list[dict],
    system: Optional[str],
    max_tokens: int,
    temperature: float,
) -> LLMResponse:
    """Call Google Gemini API."""
    from google.genai import types

    client = _get_gemini()

    # Convert messages to Gemini format
    contents = []
    for msg in messages:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part(text=msg["content"])]))

    config = types.GenerateContentConfig(
        max_output_tokens=max_tokens,
        temperature=temperature,
    )
    if system:
        config.system_instruction = system

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=config,
    )

    tokens_in = response.usage_metadata.prompt_token_count if response.usage_metadata else 0
    tokens_out = response.usage_metadata.candidates_token_count if response.usage_metadata else 0

    return LLMResponse(
        text=response.text,
        provider="gemini",
        model=model,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
    )


# ---------------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------------

async def check_anthropic() -> bool:
    """Quick health check for Anthropic."""
    if not settings.has_anthropic:
        return False
    try:
        result = _call_anthropic(
            "claude-haiku-4-5-20251001", [{"role": "user", "content": "OK"}],
            None, 5, 0,
        )
        return bool(result.text)
    except Exception:
        return False


async def check_gemini() -> bool:
    """Quick health check for Gemini."""
    if not settings.has_gemini:
        return False
    try:
        result = _call_gemini(
            "gemini-2.5-flash-lite", [{"role": "user", "content": "OK"}],
            None, 5, 0,
        )
        return bool(result.text)
    except Exception:
        return False


def get_health_stats() -> dict:
    """Return provider health statistics for monitoring."""
    return {
        provider.value: {
            "healthy": health.is_healthy,
            "total_calls": health.total_calls,
            "errors": health.errors,
            "consecutive_errors": health.consecutive_errors,
            "total_tokens_in": health.total_tokens_in,
            "total_tokens_out": health.total_tokens_out,
        }
        for provider, health in _health.items()
    }


def call_llm_sync(
    use_case: "LLMUseCase",
    messages: list[dict],
    system: Optional[str] = None,
    max_tokens: Optional[int] = None,
    temperature: float = 0.7,
) -> "LLMResponse":
    """Synchronous wrapper for call_llm.

    Handles the async-from-sync problem: when called from sync code inside
    an already-running event loop (e.g., FastAPI sync endpoint → dispatcher),
    runs the async call in a separate thread.

    Use this instead of asyncio.run(call_llm(...)) which fails when an
    event loop is already running.
    """
    import asyncio
    import concurrent.futures

    coro = call_llm(
        use_case=use_case,
        messages=messages,
        system=system,
        max_tokens=max_tokens,
        temperature=temperature,
    )

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # Already in async context — run in a thread
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, coro).result(timeout=60)
    else:
        return asyncio.run(coro)
