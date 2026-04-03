"""NOUS — LLM-powered judgment layer (Pass 2).

NOUS (νοῦς — cosmic mind) reviews deterministic engine outputs and applies
bounded adjustments for realism. Calls LLM with assembled context, parses
structured output, validates bounds, returns JudgmentResult for orchestrator.

Source: SEED_D10_ENGINE_JUDGMENT_v1.md
"""

from __future__ import annotations

import json
import logging
from typing import Any

from engine.context.assembler import ContextAssembler
from engine.judgment.schemas import JudgmentResult, validate_and_clamp

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# SYSTEM PROMPT
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are NOUS — the analytical judgment layer of the Thucydides Trap world model engine.

Your role: Review the deterministic engine outputs (Pass 1) and apply bounded adjustments that formulas cannot capture — crisis declarations, contagion effects, stability/support nudges, market sentiment, and capitulation assessment.

You are NOT a player, advisor, or character. You are the cosmic mind of the simulation — you observe, understand patterns, and ensure the world model produces coherent, realistic outcomes.

RULES:
1. Most countries most rounds need NO adjustment
2. Never double-count Pass 1 (GDP, oil, sanctions coefficient already computed)
3. Respect bounds strictly
4. Arguments: MAX 10 WORDS each. Be telegraphic.
5. No country eliminated before Round 4
6. Sanctions = choke, not spiral
7. Return ONLY valid compact JSON. No markdown. No prose outside JSON.
8. Keep total response under 1500 tokens."""


INSTRUCTION_TEMPLATE = """Review Round {round_num} results. Return ONLY a JSON object.

CRITICAL: Keep arguments SHORT (max 15 words each). Keep reasoning_summary under 30 words. No verbose explanations. Compact JSON only.

Schema:
{{
  "round_num": {round_num},
  "crisis_declarations": [{{"country": "str", "crisis_state": "crisis|normal", "gdp_penalty_pct": -2.0 to 0, "argument": "max 15 words"}}],
  "contagion_effects": [{{"from_country": "str", "to_country": "str", "channel": "str", "gdp_impact_pct": -2.0 to 0, "argument": "max 15 words"}}],
  "stability_adjustments": [{{"country": "str", "delta": -0.5 to 0.5, "argument": "max 15 words"}}],
  "support_adjustments": [{{"country": "str", "delta": -5.0 to 5.0, "argument": "max 15 words"}}],
  "market_index_nudges": [{{"index": "wall_street|europa|dragon", "delta": -10 to 10, "argument": "max 15 words"}}],
  "capitulation_recommendations": [{{"country": "str", "likelihood": "low|medium|high", "argument": "max 15 words"}}],
  "flags": ["short_flag_name"],
  "confidence": 0.0 to 1.0,
  "reasoning_summary": "max 30 words"
}}

Bounds: stability ±0.5, support ±5, crisis GDP -2 to -1%, contagion -2 to 0%, market ±10. Max 5 crisis, 5 contagion.
Return ONLY valid JSON. No markdown wrapping."""


class WorldJudge:
    """Calls LLM to review round results and produce bounded adjustments."""

    def __init__(self, assembler: ContextAssembler, intensity: int = 3):
        self.assembler = assembler
        self.intensity = intensity

    async def judge_round(self, round_num: int) -> tuple[JudgmentResult, list[str]]:
        """Run Pass 2 judgment on the current round.

        Returns:
            (JudgmentResult, warnings) — result with validated bounds + any warnings.
        """
        from engine.judgment.schemas import INTENSITY_LEVELS, DEFAULT_INTENSITY
        level_info = INTENSITY_LEVELS.get(self.intensity, INTENSITY_LEVELS[DEFAULT_INTENSITY])

        # Build context
        context = self.assembler.build([
            "sim_rules",
            "methodology",
            "sim_history",
            "world_state",
            "round_inputs",
            "round_outputs",
        ])

        intensity_instruction = (
            f"\n\nINTERVENTION INTENSITY: {self.intensity}/5 ({level_info['name']}). "
            f"Max {level_info['max_adjustments']} adjustments this round. "
            f"{level_info['description']}."
        )
        if self.intensity == 0:
            intensity_instruction += " Return empty adjustment arrays — analysis and flags only."

        instruction = INSTRUCTION_TEMPLATE.format(round_num=round_num) + intensity_instruction

        # Call LLM (lazy import to avoid dependency chain at module level)
        from engine.services.llm import call_llm
        from engine.config.settings import LLMUseCase
        response = await call_llm(
            use_case=LLMUseCase.MODERATOR,
            messages=[{"role": "user", "content": f"{context}\n\n---\n\n{instruction}"}],
            system=SYSTEM_PROMPT,
            max_tokens=4000,
            temperature=0.3,  # low temperature for consistent, analytical output
        )

        # Parse JSON response
        result = _parse_judgment(response.text, round_num)

        # Validate bounds + enforce intensity limits
        result, warnings = validate_and_clamp(result, intensity=self.intensity)

        if warnings:
            for w in warnings:
                logger.warning("Judgment bound violation: %s", w)

        return result, warnings

    def judge_round_sync(self, round_num: int) -> tuple[JudgmentResult, list[str]]:
        """Synchronous version for testing (no LLM call — returns empty result)."""
        logger.info("Sync judgment for round %d (intensity=%d) — no LLM", round_num, self.intensity)
        return JudgmentResult(round_num=round_num), []


def _parse_judgment(text: str, round_num: int) -> JudgmentResult:
    """Parse LLM response text into JudgmentResult."""
    # Strip markdown code fences if present
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    if text.startswith("json"):
        text = text[4:].strip()

    try:
        data = json.loads(text)
        data["round_num"] = round_num  # enforce correct round
        return JudgmentResult(**data)
    except json.JSONDecodeError as e:
        # Attempt repair: fix common LLM JSON glitches
        repaired = _repair_json(text)
        if repaired:
            try:
                data = json.loads(repaired)
                data["round_num"] = round_num
                logger.info("Judgment JSON repaired successfully")
                return JudgmentResult(**data)
            except Exception:
                pass
        logger.error("Failed to parse judgment response: %s\nText: %s", e, text[:500])
        return JudgmentResult(
            round_num=round_num,
            flags=["PARSE_ERROR: judgment response could not be parsed"],
            reasoning_summary=f"Parse error: {e}",
        )
    except Exception as e:
        logger.error("Failed to build JudgmentResult: %s", e)
        return JudgmentResult(
            round_num=round_num,
            flags=[f"BUILD_ERROR: {e}"],
            reasoning_summary=f"Build error: {e}",
        )


def _repair_json(text: str) -> str | None:
    """Attempt to fix common LLM JSON output glitches."""
    import re
    repaired = text

    # Fix missing opening quotes before key names: , europa" → , "europa"
    repaired = re.sub(r',\s*([a-z_]+)"', r', "\1"', repaired)
    # Fix missing opening quotes at start of value: : europa" → : "europa"
    repaired = re.sub(r':\s*([a-z_]+)"', r': "\1"', repaired)

    # If response was truncated mid-JSON, try to close it
    if repaired.count('{') > repaired.count('}'):
        # Find the last complete entry and close the JSON
        # Strategy: truncate to last complete ], then close remaining braces
        last_bracket = repaired.rfind(']')
        if last_bracket > 0:
            # Count what needs closing after the last complete array
            snippet = repaired[:last_bracket + 1]
            # Add missing closing elements
            open_braces = snippet.count('{') - snippet.count('}')
            open_brackets = snippet.count('[') - snippet.count(']')
            repaired = snippet + ']' * open_brackets + '}' * open_braces
        else:
            return None

    if repaired == text:
        return None  # no changes made
    return repaired


def apply_judgment(
    countries: dict[str, dict],
    world_state: dict,
    result: JudgmentResult,
    log: list[str],
) -> None:
    """Apply validated judgment adjustments to country/world state dicts.

    Mutates countries and world_state in place.
    """
    # Crisis declarations
    for decl in result.crisis_declarations:
        cid = decl.country
        if cid in countries:
            eco = countries[cid]["economic"]
            eco["economic_state"] = decl.crisis_state
            if decl.crisis_state == "crisis" and decl.gdp_penalty_pct < 0:
                penalty = eco["gdp"] * abs(decl.gdp_penalty_pct) / 100.0
                eco["gdp"] = max(0.5, eco["gdp"] - penalty)
                log.append(f"  JUDGMENT: {cid} → CRISIS (GDP {decl.gdp_penalty_pct}%): {decl.argument}")
            elif decl.crisis_state == "normal":
                log.append(f"  JUDGMENT: {cid} exits crisis: {decl.argument}")

    # Contagion effects
    for eff in result.contagion_effects:
        cid = eff.to_country
        if cid in countries:
            eco = countries[cid]["economic"]
            penalty = eco["gdp"] * abs(eff.gdp_impact_pct) / 100.0
            eco["gdp"] = max(0.5, eco["gdp"] - penalty)
            log.append(f"  JUDGMENT: contagion {eff.from_country}→{cid} ({eff.channel}): "
                       f"GDP {eff.gdp_impact_pct}%")

    # Stability adjustments
    for adj in result.stability_adjustments:
        cid = adj.country
        if cid in countries:
            pol = countries[cid]["political"]
            old = pol["stability"]
            pol["stability"] = max(1.0, min(9.0, old + adj.delta))
            log.append(f"  JUDGMENT: {cid} stability {old:.1f}→{pol['stability']:.1f}: {adj.argument}")

    # Support adjustments
    for adj in result.support_adjustments:
        cid = adj.country
        if cid in countries:
            pol = countries[cid]["political"]
            old = pol["political_support"]
            pol["political_support"] = max(5.0, min(85.0, old + adj.delta))
            log.append(f"  JUDGMENT: {cid} support {old:.0f}%→{pol['political_support']:.0f}%: {adj.argument}")

    # Market index nudges
    mkt = world_state.get("market_indexes")
    if mkt:
        for nudge in result.market_index_nudges:
            idx_name = nudge.index
            if idx_name in mkt:
                old = mkt[idx_name]
                mkt[idx_name] = max(0, min(200, old + nudge.delta))
                log.append(f"  JUDGMENT: {idx_name} index {old:.0f}→{mkt[idx_name]:.0f}: {nudge.argument}")
