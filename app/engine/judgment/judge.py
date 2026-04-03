"""World Judge — LLM-powered judgment layer (Pass 2).

Calls the LLM with assembled context, parses structured output, validates
bounds, and returns a JudgmentResult ready for the orchestrator to apply.

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

SYSTEM_PROMPT = """You are the World Model Judgment Layer for the Thucydides Trap geopolitical simulation.

Your role: Review the deterministic engine outputs (Pass 1) and apply bounded adjustments that formulas cannot capture — crisis declarations, contagion effects, stability/support nudges, market sentiment, and capitulation assessment.

You are NOT a player, advisor, or character. You are an analytical engine component that ensures the world model produces realistic, balanced outcomes.

CRITICAL RULES:
1. Most countries most rounds need NO adjustment — only intervene when formulas clearly miss something
2. Never double-count what Pass 1 already handles (GDP growth, oil price, sanctions coefficient are already computed)
3. Your adjustments are BOUNDED — respect the limits strictly
4. Every adjustment needs a compact argument — no vague reasoning
5. No country should be eliminated before Round 4
6. Sanctions are a choke, not a spiral — don't amplify what's already captured
7. Return VALID JSON matching the schema exactly"""


INSTRUCTION_TEMPLATE = """Review Round {round_num} results and return your judgment as JSON.

Respond with ONLY a JSON object matching this schema:
{{
  "round_num": {round_num},
  "crisis_declarations": [
    {{"country": "string", "crisis_state": "crisis|normal", "gdp_penalty_pct": -1.0 to -2.0, "argument": "string"}}
  ],
  "contagion_effects": [
    {{"from_country": "string", "to_country": "string", "channel": "string", "gdp_impact_pct": -2.0 to 0.0, "argument": "string"}}
  ],
  "stability_adjustments": [
    {{"country": "string", "delta": -0.5 to 0.5, "argument": "string"}}
  ],
  "support_adjustments": [
    {{"country": "string", "delta": -5.0 to 5.0, "argument": "string"}}
  ],
  "market_index_nudges": [
    {{"index": "wall_street|europa|dragon", "delta": -10 to 10, "argument": "string"}}
  ],
  "capitulation_recommendations": [
    {{"country": "string", "likelihood": "low|medium|high", "argument": "string"}}
  ],
  "flags": ["string"],
  "confidence": 0.0 to 1.0,
  "reasoning_summary": "string"
}}

Bounds:
- stability delta: [-0.5, +0.5]
- support delta: [-5, +5]
- GDP crisis penalty: [-2%, -1%]
- contagion GDP impact: [-2%, 0%]
- market index nudge: [-10, +10]
- Max 5 contagion effects, max 5 crisis declarations

Return ONLY valid JSON. No markdown, no explanation outside the JSON."""


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
            max_tokens=2000,
            temperature=0.3,  # low temperature for consistent, analytical output
        )

        # Parse JSON response
        result = _parse_judgment(response.content, round_num)

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
    except (json.JSONDecodeError, Exception) as e:
        logger.error("Failed to parse judgment response: %s\nText: %s", e, text[:500])
        return JudgmentResult(
            round_num=round_num,
            flags=["PARSE_ERROR: judgment response could not be parsed"],
            reasoning_summary=f"Parse error: {e}",
        )


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
