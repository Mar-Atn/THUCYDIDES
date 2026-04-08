"""Dual-provider LLM tool-use adapter.

Provides a single ``call_tool_llm()`` that speaks the Anthropic tool-use
protocol shape but routes calls to Anthropic or Gemini under the hood.

Why: stage5_test / full_round_runner build multi-turn tool-use
conversations (agent investigates via tools, then commits an action,
then writes memory). We need to swap providers without rewriting every
call site.

Contract:
  * Input messages use the **Anthropic** shape:
      [
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": [ContentBlock, ...]},
        {"role": "user", "content": [{"type":"tool_result","tool_use_id":..,"content":..}]},
        ...
      ]
    where a content block is either a string or a list of dicts with
    ``type`` ∈ {"text","tool_use","tool_result"}.

  * Tools use the **Anthropic** schema shape:
      {"name": "...", "description": "...", "input_schema": {...json-schema...}}

  * Output: ``ToolLLMResponse`` with ``content`` (list of ContentBlock),
    ``stop_reason`` ∈ {"end_turn","tool_use","max_tokens","error"},
    provider, model, usage.

The Gemini adapter translates both ways.
"""
from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from engine.config.settings import LLMProvider, LLMUseCase, LLMModelConfig, settings
from engine.services.llm import _get_anthropic, _get_gemini, _health

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Unified response shape
# ---------------------------------------------------------------------------

@dataclass
class ContentBlock:
    """A single content block inside an assistant message."""
    type: str                        # "text" | "tool_use"
    text: Optional[str] = None
    # tool_use fields
    id: Optional[str] = None         # tool_use_id, required if type=="tool_use"
    name: Optional[str] = None
    input: Optional[dict] = None


@dataclass
class ToolLLMResponse:
    content: list[ContentBlock]
    stop_reason: str                 # "end_turn" | "tool_use" | "max_tokens" | "error"
    provider: str
    model: str
    tokens_in: int = 0
    tokens_out: int = 0
    latency_ms: int = 0
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def call_tool_llm(
    system: str,
    messages: list[dict],
    tools: list[dict],
    max_tokens: int = 4000,
    use_case: LLMUseCase = LLMUseCase.AGENT_DECISION,
    provider_override: Optional[LLMProvider] = None,
    model_override: Optional[str] = None,
    allow_fallback: bool = True,
) -> ToolLLMResponse:
    """Route a tool-use call to Anthropic or Gemini.

    By default uses the provider configured for ``use_case``. If
    ``provider_override`` is set, it pins that provider. On a 4xx/5xx
    failure the opposite provider is tried (if healthy + allow_fallback).
    """
    if provider_override is not None:
        provider = provider_override
        model = model_override or _default_model_for(provider, use_case)
    else:
        config = settings.get_llm_config(use_case)
        provider = LLMProvider(config["provider"])
        model = model_override or config["model"]
        # Prefer healthy provider
        if not _health[provider].is_healthy and allow_fallback:
            alt = _other_provider(provider)
            if _health[alt].is_healthy and _provider_configured(alt):
                logger.info("provider %s unhealthy, pre-routing to %s", provider.value, alt.value)
                provider = alt
                model = _default_model_for(alt, use_case)

    return _call_with_fallback(
        provider, model, system, messages, tools, max_tokens, use_case, allow_fallback,
    )


def _call_with_fallback(
    provider: LLMProvider,
    model: str,
    system: str,
    messages: list[dict],
    tools: list[dict],
    max_tokens: int,
    use_case: LLMUseCase,
    allow_fallback: bool,
) -> ToolLLMResponse:
    start = time.time()
    try:
        if provider == LLMProvider.ANTHROPIC:
            r = _call_anthropic_tools(model, system, messages, tools, max_tokens)
        elif provider == LLMProvider.GEMINI:
            r = _call_gemini_tools(model, system, messages, tools, max_tokens)
        else:
            raise ValueError(f"Unknown provider: {provider}")
        r.latency_ms = int((time.time() - start) * 1000)
        _health[provider].record_success(r.tokens_in, r.tokens_out)
        return r
    except Exception as e:
        _health[provider].record_error()
        logger.warning("tool-use call failed provider=%s model=%s err=%s", provider.value, model, e)
        if not allow_fallback:
            raise
        alt = _other_provider(provider)
        if not _provider_configured(alt):
            raise
        alt_model = _default_model_for(alt, use_case)
        logger.info("falling back to %s/%s", alt.value, alt_model)
        start2 = time.time()
        if alt == LLMProvider.ANTHROPIC:
            r = _call_anthropic_tools(alt_model, system, messages, tools, max_tokens)
        else:
            r = _call_gemini_tools(alt_model, system, messages, tools, max_tokens)
        r.latency_ms = int((time.time() - start2) * 1000)
        _health[alt].record_success(r.tokens_in, r.tokens_out)
        return r


# ---------------------------------------------------------------------------
# Anthropic adapter (pass-through — already native shape)
# ---------------------------------------------------------------------------

def _call_anthropic_tools(
    model: str, system: str, messages: list[dict], tools: list[dict], max_tokens: int,
) -> ToolLLMResponse:
    client = _get_anthropic()
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        tools=tools,
        messages=messages,
    )
    blocks: list[ContentBlock] = []
    for b in response.content:
        if b.type == "text":
            blocks.append(ContentBlock(type="text", text=b.text))
        elif b.type == "tool_use":
            blocks.append(ContentBlock(type="tool_use", id=b.id, name=b.name, input=dict(b.input or {})))
    usage_in = getattr(response.usage, "input_tokens", 0) if response.usage else 0
    usage_out = getattr(response.usage, "output_tokens", 0) if response.usage else 0
    return ToolLLMResponse(
        content=blocks, stop_reason=response.stop_reason or "end_turn",
        provider="anthropic", model=model,
        tokens_in=usage_in, tokens_out=usage_out,
    )


# ---------------------------------------------------------------------------
# Gemini adapter — translate both ways
# ---------------------------------------------------------------------------

def _call_gemini_tools(
    model: str, system: str, messages: list[dict], tools: list[dict], max_tokens: int,
) -> ToolLLMResponse:
    from google.genai import types

    client = _get_gemini()

    # 1) Translate tool schemas. Gemini accepts JSON-schema-like parameters.
    gem_function_decls = []
    for t in tools:
        gem_function_decls.append(types.FunctionDeclaration(
            name=t["name"],
            description=t.get("description", ""),
            parameters=_anthropic_schema_to_gemini(t.get("input_schema", {"type": "object", "properties": {}})),
        ))
    gem_tools = [types.Tool(function_declarations=gem_function_decls)]

    # 2) Translate messages. Also build tool_use_id -> function_name map for later.
    id_to_name: dict[str, str] = {}
    for m in messages:
        if m["role"] != "assistant":
            continue
        if isinstance(m["content"], list):
            for b in m["content"]:
                t = _block_type(b)
                if t == "tool_use":
                    id_to_name[_block_id(b)] = _block_name(b)

    contents: list = []
    for m in messages:
        role = "user" if m["role"] == "user" else "model"
        c = m["content"]
        parts: list = []
        if isinstance(c, str):
            parts.append(types.Part(text=c))
        else:
            for b in c:
                bt = _block_type(b)
                if bt == "text":
                    parts.append(types.Part(text=_block_text(b)))
                elif bt == "tool_use":
                    parts.append(types.Part(function_call=types.FunctionCall(
                        name=_block_name(b), args=_block_input(b),
                    )))
                elif bt == "tool_result":
                    name = id_to_name.get(_block_tool_use_id(b), "unknown_tool")
                    # content can be a JSON string — wrap into a dict for Gemini
                    raw = _block_content_value(b)
                    response_obj: dict
                    if isinstance(raw, dict):
                        response_obj = raw
                    elif isinstance(raw, str):
                        try:
                            import json as _json
                            parsed = _json.loads(raw)
                            response_obj = parsed if isinstance(parsed, dict) else {"result": parsed}
                        except Exception:
                            response_obj = {"result": raw}
                    else:
                        response_obj = {"result": raw}
                    parts.append(types.Part(function_response=types.FunctionResponse(
                        name=name, response=response_obj,
                    )))
        if parts:
            contents.append(types.Content(role=role, parts=parts))

    cfg = types.GenerateContentConfig(
        max_output_tokens=max_tokens,
        temperature=0.7,
        system_instruction=system,
        tools=gem_tools,
    )

    response = client.models.generate_content(model=model, contents=contents, config=cfg)

    # 3) Translate response
    blocks: list[ContentBlock] = []
    has_tool_use = False
    if response.candidates:
        cand = response.candidates[0]
        if cand.content and cand.content.parts:
            for p in cand.content.parts:
                if getattr(p, "text", None):
                    blocks.append(ContentBlock(type="text", text=p.text))
                elif getattr(p, "function_call", None):
                    has_tool_use = True
                    fc = p.function_call
                    args = dict(fc.args) if fc.args else {}
                    # Synthesize a tool_use_id that stage5_test expects
                    tuid = "toolu_" + uuid.uuid4().hex[:22]
                    blocks.append(ContentBlock(type="tool_use", id=tuid, name=fc.name, input=args))
        fr = cand.finish_reason
        if has_tool_use:
            stop = "tool_use"
        elif fr and str(fr).upper().endswith("MAX_TOKENS"):
            stop = "max_tokens"
        else:
            stop = "end_turn"
    else:
        stop = "error"

    um = response.usage_metadata
    tokens_in = getattr(um, "prompt_token_count", 0) if um else 0
    tokens_out = getattr(um, "candidates_token_count", 0) if um else 0

    return ToolLLMResponse(
        content=blocks, stop_reason=stop,
        provider="gemini", model=model,
        tokens_in=tokens_in, tokens_out=tokens_out,
    )


# ---------------------------------------------------------------------------
# Block accessors — handle both dict blocks and anthropic SDK objects
# ---------------------------------------------------------------------------

def _block_type(b: Any) -> str:
    return b.get("type") if isinstance(b, dict) else getattr(b, "type", "")

def _block_text(b: Any) -> str:
    return b.get("text", "") if isinstance(b, dict) else getattr(b, "text", "") or ""

def _block_id(b: Any) -> str:
    return b.get("id", "") if isinstance(b, dict) else getattr(b, "id", "") or ""

def _block_name(b: Any) -> str:
    return b.get("name", "") if isinstance(b, dict) else getattr(b, "name", "") or ""

def _block_input(b: Any) -> dict:
    if isinstance(b, dict):
        return dict(b.get("input") or {})
    v = getattr(b, "input", None)
    return dict(v or {})

def _block_tool_use_id(b: Any) -> str:
    return b.get("tool_use_id", "") if isinstance(b, dict) else getattr(b, "tool_use_id", "") or ""

def _block_content_value(b: Any) -> Any:
    if isinstance(b, dict):
        return b.get("content")
    return getattr(b, "content", None)


# ---------------------------------------------------------------------------
# JSON schema -> Gemini Schema translation
# ---------------------------------------------------------------------------

_JSON_TO_GEMINI_TYPE = {
    "object": "OBJECT", "array": "ARRAY",
    "string": "STRING", "integer": "INTEGER",
    "number": "NUMBER", "boolean": "BOOLEAN",
}


def _anthropic_schema_to_gemini(schema: dict) -> Any:
    """Convert a JSON-schema dict (Anthropic-style) into a Gemini Schema."""
    from google.genai import types
    if not isinstance(schema, dict):
        return types.Schema(type="OBJECT", properties={})

    t = schema.get("type", "object").lower()
    gem_type = _JSON_TO_GEMINI_TYPE.get(t, "OBJECT")

    kwargs: dict[str, Any] = {"type": gem_type}
    if "description" in schema:
        kwargs["description"] = schema["description"]
    if "enum" in schema and gem_type == "STRING":
        kwargs["enum"] = [str(v) for v in schema["enum"]]
    if gem_type == "OBJECT":
        props = {}
        for key, val in (schema.get("properties") or {}).items():
            props[key] = _anthropic_schema_to_gemini(val)
        kwargs["properties"] = props
        if schema.get("required"):
            kwargs["required"] = list(schema["required"])
    elif gem_type == "ARRAY":
        items = schema.get("items")
        if isinstance(items, dict):
            kwargs["items"] = _anthropic_schema_to_gemini(items)
    return types.Schema(**kwargs)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _other_provider(p: LLMProvider) -> LLMProvider:
    return LLMProvider.GEMINI if p == LLMProvider.ANTHROPIC else LLMProvider.ANTHROPIC


def _provider_configured(p: LLMProvider) -> bool:
    if p == LLMProvider.ANTHROPIC:
        return settings.has_anthropic
    if p == LLMProvider.GEMINI:
        return settings.has_gemini
    return False


def _default_model_for(provider: LLMProvider, use_case: LLMUseCase) -> str:
    cfg = LLMModelConfig.get(use_case)
    if LLMProvider(cfg["primary"]["provider"]) == provider:
        return cfg["primary"]["model"]
    return cfg["fallback"]["model"]


# ---------------------------------------------------------------------------
# Assistant-content serializer (for appending to messages history)
# ---------------------------------------------------------------------------

def serialize_assistant_content(blocks: list[ContentBlock]) -> list[dict]:
    """Convert a response's content into the dict shape Anthropic expects
    on subsequent ``messages.create`` calls. stage5_test appends this to
    the messages list."""
    out: list[dict] = []
    for b in blocks:
        if b.type == "text":
            out.append({"type": "text", "text": b.text or ""})
        elif b.type == "tool_use":
            out.append({
                "type": "tool_use", "id": b.id, "name": b.name, "input": b.input or {},
            })
    return out
