"""AI Participant Decision Module — LLM-powered decision making for all action types.

Implements the Three-Layer Context Model (SEED E5 Section 2.5):
- Layer 1 (permanent): identity + goals + memory — from LeaderAgent.cognitive
- Layer 2 (task-specific): assembled here per decision type
- Layer 3 (instruction): concise prompt for what decision is being asked

KEY PRINCIPLE: We don't prescribe decisions. We provide identity + goals + memory +
relevant data + action space. The AI reasons autonomously.

Source: SEED_E5_AI_PARTICIPANT_MODULE_v1.md, DET_C1 C6
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# JSON PARSING UTILITY
# ---------------------------------------------------------------------------

def _parse_json(text: str) -> dict | list | None:
    """Parse JSON from LLM output, handling markdown fences and preamble."""
    text = text.strip()

    # Strip markdown code fences
    if "```" in text:
        # Find JSON block between fences
        parts = text.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part and (part.startswith("{") or part.startswith("[")):
                text = part
                break

    # Try to find JSON in the text
    for start_char, end_char in [("{", "}"), ("[", "]")]:
        start = text.find(start_char)
        if start >= 0:
            # Find matching end
            depth = 0
            for i in range(start, len(text)):
                if text[i] == start_char:
                    depth += 1
                elif text[i] == end_char:
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(text[start:i + 1])
                        except json.JSONDecodeError:
                            break

    # Last resort: try the whole text
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logger.warning("Failed to parse JSON from LLM output: %s", text[:200])
        return None


# ---------------------------------------------------------------------------
# LAYER 2: TASK-SPECIFIC CONTEXT BUILDERS
# ---------------------------------------------------------------------------

def build_budget_context(country: dict, round_context: dict) -> str:
    """Build Layer 2 context for budget decisions.

    Args:
        country: Country data dict (from profiles or world state).
        round_context: Current round context with economic data.
    """
    eco = round_context.get("economic", {})
    gdp = eco.get("gdp", country.get("gdp", 0))
    treasury = eco.get("treasury", country.get("treasury", 0))
    inflation = eco.get("inflation", country.get("inflation", 0))
    debt_burden = eco.get("debt_burden", country.get("debt_burden", 0))
    tax_rate = eco.get("tax_rate", country.get("tax_rate", 0.24))
    social_baseline = eco.get("social_baseline", country.get("social_baseline", 0.30))
    stability = round_context.get("political", {}).get("stability", country.get("stability", 5))
    support = round_context.get("political", {}).get("political_support", country.get("political_support", 50))
    maintenance = eco.get("maintenance_cost", country.get("maintenance_per_unit", 0.05))

    # Estimate revenue and maintenance costs
    revenue_est = gdp * tax_rate
    mil_units = (
        country.get("mil_ground", 0) +
        country.get("mil_naval", 0) +
        country.get("mil_tactical_air", 0)
    )
    maintenance_cost = mil_units * maintenance
    social_cost_baseline = gdp * social_baseline

    budget = round_context.get("current_budget", {})
    current_social = budget.get("social_pct", 1.0)
    current_military = budget.get("military_coins", 0)
    current_tech = budget.get("tech_coins", 0)

    return f"""# Economic Situation — Budget Decision

## Country Economics
- GDP: {gdp:.1f} (revenue estimate: {revenue_est:.1f} from {tax_rate:.0%} tax)
- Treasury: {treasury:.1f}
- Inflation: {inflation:.1f}%
- Debt/GDP: {debt_burden:.0%}
- Stability: {stability:.1f}, Support: {support:.0f}%

## Budget Components
- Social spending baseline: {social_cost_baseline:.1f} ({social_baseline:.0%} of GDP)
  Current social multiplier: {current_social:.2f}x (range: 0.50x to 1.50x)
  Cutting below 1.0x reduces stability. Above 1.0x improves it.
- Military maintenance: {maintenance_cost:.1f} (for {mil_units} units)
- Current military allocation: {current_military:.1f}
- Current tech allocation: {current_tech:.1f}

## Budget Rules
- social_pct: multiplier on social baseline (0.5 = harsh cuts, 1.5 = generous)
- military_coins: additional coins for arms purchases, beyond maintenance
- tech_coins: investment in technology R&D
- Total spending = (social_pct × baseline) + maintenance + military + tech
- Deficit = spending - revenue → 50% borrowed (debt), 50% printed (inflation)
- Surplus reduces debt and inflation over time
"""


def build_tariff_context(country: dict, round_context: dict) -> str:
    """Build Layer 2 context for tariff decisions."""
    bilateral = round_context.get("bilateral", {})
    current_tariffs = bilateral.get("tariffs", {}).get(country.get("id", ""), {})
    trade_data = bilateral.get("trade", {}).get(country.get("id", ""), {})
    relationships = round_context.get("relationships", {}).get(country.get("id", ""), {})

    lines = ["# Trade & Tariff Situation\n"]
    lines.append("## Current Tariffs (you impose on others)")
    if current_tariffs:
        for target, level in sorted(current_tariffs.items()):
            trade_vol = trade_data.get(target, {}).get("volume", "?")
            rel = relationships.get(target, "neutral")
            lines.append(f"- {target}: L{level} (trade: {trade_vol}, relationship: {rel})")
    else:
        lines.append("- No tariffs currently imposed")

    # Show tariffs imposed ON this country
    tariffs_on_me = {}
    all_tariffs = bilateral.get("tariffs", {})
    my_id = country.get("id", "")
    for imposer, targets in all_tariffs.items():
        if my_id in targets:
            tariffs_on_me[imposer] = targets[my_id]
    if tariffs_on_me:
        lines.append("\n## Tariffs ON You (imposed by others)")
        for imposer, level in sorted(tariffs_on_me.items()):
            lines.append(f"- {imposer}: L{level}")

    lines.append("""
## Tariff Levels
- L0: Free trade (no penalty)
- L1: Light tariffs (small GDP drag on both sides, you bear ~30% of cost)
- L2: Moderate tariffs (significant drag, especially on smaller economy)
- L3: Heavy tariffs (near-embargo, massive mutual damage, smaller economy hurt more)

## Key Trade Relationships""")

    if trade_data:
        for partner, data in sorted(trade_data.items(), key=lambda x: -float(x[1].get("exposure", 0)) if isinstance(x[1], dict) else 0):
            if isinstance(data, dict):
                exposure = data.get("exposure", 0)
                lines.append(f"- {partner}: exposure {exposure:.1%}")
    else:
        lines.append("- Trade data not available for this round")

    return "\n".join(lines)


def build_sanction_context(country: dict, round_context: dict) -> str:
    """Build Layer 2 context for sanction decisions."""
    bilateral = round_context.get("bilateral", {})
    my_id = country.get("id", "")
    current_sanctions = bilateral.get("sanctions", {}).get(my_id, {})
    all_sanctions = bilateral.get("sanctions", {})

    lines = ["# Sanctions Situation\n"]
    lines.append("## Sanctions You Impose")
    if current_sanctions:
        for target, level in sorted(current_sanctions.items()):
            lines.append(f"- {target}: L{level}")
    else:
        lines.append("- No sanctions currently imposed")

    # Sanctions on us
    sanctions_on_me = {}
    for imposer, targets in all_sanctions.items():
        if my_id in targets:
            sanctions_on_me[imposer] = targets[my_id]
    if sanctions_on_me:
        lines.append("\n## Sanctions ON You")
        for imposer, level in sorted(sanctions_on_me.items()):
            lines.append(f"- {imposer}: L{level}")

    # Coalition info
    coalitions = round_context.get("sanction_coalitions", {})
    if coalitions:
        lines.append("\n## Active Coalitions")
        for target, members in coalitions.items():
            lines.append(f"- Against {target}: {', '.join(members)}")

    lines.append("""
## Sanction Mechanics
- L0: No sanctions
- L1: Targeted sanctions (asset freezes, travel bans — minimal GDP impact)
- L2: Broad sanctions (sector bans — significant impact, needs 2+ countries)
- L3: Maximum sanctions (near-total isolation — devastating, needs coalition)
- Sanctions coefficient: reduces target's GDP growth (0.50 at L3 full coalition)
- Cost to imposer: 30-50% of damage you inflict (trade disruption, lost markets)
- Each additional coalition member increases effectiveness ~15-20%
""")

    return "\n".join(lines)


def build_opec_context(country: dict, round_context: dict) -> str:
    """Build Layer 2 context for OPEC production decisions."""
    eco = round_context.get("economic", {})
    oil_price = round_context.get("oil_price", 80)
    oil_production = eco.get("oil_production_mbpd", country.get("oil_production_mbpd", 0))
    treasury = eco.get("treasury", country.get("treasury", 0))
    gdp = eco.get("gdp", country.get("gdp", 0))

    # Oil revenue estimate
    oil_revenue = oil_production * oil_price * 0.365  # rough annual factor scaled

    return f"""# OPEC Production Decision

## Oil Market
- Current oil price: ${oil_price:.0f}/barrel
- Your production: {oil_production} mbpd
- Estimated oil revenue: {oil_revenue:.1f} (at current price)
- Treasury: {treasury:.1f}
- GDP: {gdp:.1f}

## Production Levels & Effects
- "min": Cut production heavily. Pushes price UP significantly. Revenue may increase if price rises enough.
- "low": Moderate cuts. Pushes price UP modestly.
- "normal": Maintain quota. Neutral effect on price.
- "high": Modest increase. Pushes price DOWN modestly. More volume, lower price.
- "max": Pump at capacity. Pushes price DOWN significantly. Volume play — hurts other producers.

## Strategic Considerations
- Higher oil price benefits oil exporters but hurts importers (may strain alliances)
- Lower oil price hurts rivals who depend on oil revenue (e.g., economic warfare)
- OPEC coordination: if others cut and you don't, you gain market share at their expense
- Oil price affects global inflation and stability
"""


def build_military_context(country: dict, round_context: dict) -> str:
    """Build Layer 2 context for military decisions."""
    military = round_context.get("military", {})
    units = military.get("units", {})
    zones = military.get("zones", {})
    wars = round_context.get("wars", [])
    at_war = country.get("at_war_with", "")

    lines = ["# Military Situation\n"]

    # Current forces
    lines.append("## Your Forces")
    ground = units.get("ground", country.get("mil_ground", 0))
    naval = units.get("naval", country.get("mil_naval", 0))
    air = units.get("tactical_air", country.get("mil_tactical_air", 0))
    missiles = units.get("strategic_missiles", country.get("mil_strategic_missiles", 0))
    air_def = units.get("air_defense", country.get("mil_air_defense", 0))
    mob_pool = military.get("mobilization_pool", country.get("mobilization_pool", 0))
    reserves = military.get("reserves", {})

    lines.append(f"- Ground: {ground} (reserve: {reserves.get('ground', 0)})")
    lines.append(f"- Naval: {naval} (reserve: {reserves.get('naval', 0)})")
    lines.append(f"- Tactical Air: {air} (reserve: {reserves.get('air', 0)})")
    lines.append(f"- Strategic Missiles: {missiles}")
    lines.append(f"- Air Defense: {air_def}")
    lines.append(f"- Mobilization Pool: {mob_pool}")

    # War status
    if at_war:
        lines.append(f"\n## WAR STATUS: At war with {at_war}")
    if wars:
        lines.append("\n## Active Wars")
        for w in wars:
            a = ", ".join(w.get("belligerents_a", []))
            b = ", ".join(w.get("belligerents_b", []))
            lines.append(f"- {a} vs {b}")

    # Zone control
    if zones:
        lines.append("\n## Zone Control")
        for zone_id, info in sorted(zones.items()):
            controller = info.get("controller", "?")
            forces = info.get("forces", {})
            force_str = ", ".join(f"{k}:{v}" for k, v in forces.items() if v > 0)
            lines.append(f"- {zone_id}: {controller} ({force_str})" if force_str else f"- {zone_id}: {controller}")

    # Enemy forces (visible)
    enemy_forces = military.get("enemy_visible", {})
    if enemy_forces:
        lines.append("\n## Visible Enemy Forces")
        for zone, forces in enemy_forces.items():
            force_str = ", ".join(f"{k}:{v}" for k, v in forces.items() if v > 0)
            lines.append(f"- {zone}: {force_str}")

    lines.append("""
## Military Actions Available
- **attack**: Order ground/naval/air attack on enemy zone. Requires sufficient forces.
- **blockade**: Naval blockade of chokepoint (requires naval units in range).
- **mobilize**: Call up units from mobilization pool (finite, depletable, never recovers).
- **deploy**: Move units from reserve to a zone.
- **move**: Reposition units between your/allied zones.
- **missile_strike**: Launch strategic missile at target.
- **fortify**: Dig in — bonus when defending.

## Combat Rules (simplified)
- RISK-style dice + modifiers. Attacker needs local superiority for good odds.
- Air superiority grants +1 to ground combat.
- Naval blockades cut off supply and trade through chokepoints.
- Mobilization is permanent — once spent, never comes back.
""")

    return "\n".join(lines)


def build_covert_context(country: dict, role: dict, round_context: dict) -> str:
    """Build Layer 2 context for covert operations decisions."""
    intel_pool = role.get("intelligence_pool", 0)
    sabotage = role.get("sabotage_cards", 0)
    cyber = role.get("cyber_cards", 0)
    disinfo = role.get("disinfo_cards", 0)
    election = role.get("election_meddling_cards", 0)
    assassination = role.get("assassination_cards", 0)

    covert_history = round_context.get("covert_history", [])

    lines = [f"""# Covert Operations

## Your Intelligence Resources
- Intelligence Pool: {intel_pool}
- Sabotage Cards: {sabotage}
- Cyber Cards: {cyber}
- Disinformation Cards: {disinfo}
- Election Meddling Cards: {election}
- Assassination Cards: {assassination}

## Covert Op Types
- **espionage**: Gather intelligence on target. Low risk, low cost.
- **sabotage**: Damage infrastructure/military assets. Medium risk, high impact.
- **cyber**: Disrupt technology, communications, finances. Medium risk.
- **disinformation**: Reduce target's stability/support. Low risk, gradual effect.
- **election_meddling**: Influence elections in target country. High risk, high reward.
- **assassination**: Eliminate key figure. Very high risk, dramatic consequences.

## Detection Risk
- Each op has ~20-40% base detection chance depending on type
- Detection causes diplomatic incident, trust damage, possible sanctions
- Repeated ops against same target increase detection risk

## Constraints
- Each card is single-use per game
- Intelligence pool determines how many concurrent ops you can run
"""]

    if covert_history:
        lines.append("## Past Covert Ops (your history)")
        for op in covert_history[-5:]:
            lines.append(f"- {op.get('type', '?')} vs {op.get('target', '?')}: {op.get('result', '?')}")

    return "\n".join(lines)


def build_political_context(country: dict, round_context: dict) -> str:
    """Build Layer 2 context for political action decisions."""
    pol = round_context.get("political", {})
    stability = pol.get("stability", country.get("stability", 5))
    support = pol.get("political_support", country.get("political_support", 50))
    regime = country.get("regime_type", "democracy")
    war_tiredness = pol.get("war_tiredness", country.get("war_tiredness", 0))

    elections = round_context.get("elections", {})
    treasury = round_context.get("economic", {}).get("treasury", country.get("treasury", 0))

    return f"""# Political Situation

## Domestic Status
- Stability: {stability:.1f}/9
- Political Support: {support:.0f}%
- Regime Type: {regime}
- War Tiredness: {war_tiredness}

## Upcoming Events
- Elections: {elections.get('description', 'None scheduled this round')}

## Available Political Actions
- **propaganda**: Spend coins to boost stability (+0.3 to +0.5). Costs 1-3 coins.
  More effective in autocracies. Diminishing returns if used repeatedly.
- **repression**: (Autocracy only) Forcibly suppress opposition. +stability short term,
  -support long term. Risk of backfire if stability already low.
- **public_statement**: Make a statement that signals intent. Costs nothing.
  Can rally support (+1-3% support) or damage rival's legitimacy.

## Warning Thresholds
- Stability <= 2 AND Support < 20%: Revolution risk (protests auto-trigger)
- Stability <= 3: Economic growth penalty
- Support < 25%: Election likely to be lost
- Treasury: {treasury:.1f} (propaganda/repression cost coins)
"""


def build_active_loop_context(country: dict, role: dict, round_context: dict) -> str:
    """Build Layer 2 context for active-loop 'what to do now' decisions."""
    pending = round_context.get("pending_conversations", [])
    available_actions = round_context.get("available_actions", [])
    recent_events = round_context.get("recent_events", [])

    lines = ["# Current Situation Overview\n"]

    if recent_events:
        lines.append("## Recent Events")
        for e in recent_events[-5:]:
            lines.append(f"- {e.get('summary', str(e)[:100])}")
        lines.append("")

    if pending:
        lines.append("## Pending Conversations")
        for p in pending:
            lines.append(f"- {p.get('from', '?')}: {p.get('topic', 'wants to talk')}")
        lines.append("")

    if available_actions:
        lines.append("## Available Actions")
        for a in available_actions:
            lines.append(f"- {a}")
    else:
        lines.append("## Available Actions")
        lines.append("- Request conversation with another leader")
        lines.append("- Take a military action (if at war)")
        lines.append("- Launch covert operation")
        lines.append("- Make a public statement")
        lines.append("- Wait and observe")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# LAYER 3: INSTRUCTION PROMPTS
# ---------------------------------------------------------------------------

BUDGET_INSTRUCTION = """Decide your budget allocation for this round.

Return a JSON object with EXACTLY these fields:
{
  "social_pct": <float 0.5-1.5>,
  "military_coins": <float >= 0>,
  "tech_coins": <float >= 0>,
  "reasoning": "<1-2 sentences explaining your priorities>"
}

Consider: your objectives, current stability/support, war needs, tech race, fiscal health.
Cutting social spending saves money but hurts stability. Overspending causes inflation.
Return ONLY valid JSON."""

TARIFF_INSTRUCTION = """Decide tariff changes for this round. You may adjust tariffs on any country.

Return a JSON object:
{
  "changes": {
    "<country_id>": <level 0-3>,
    ...
  },
  "reasoning": "<1-2 sentences>"
}

Only include countries where you want to CHANGE the tariff level. Omit countries where you want no change.
If no changes needed, return {"changes": {}, "reasoning": "maintaining current tariffs"}.
Return ONLY valid JSON."""

SANCTION_INSTRUCTION = """Decide sanction changes for this round.

Return a JSON object:
{
  "changes": {
    "<country_id>": <level 0-3>,
    ...
  },
  "reasoning": "<1-2 sentences>"
}

Only include countries where you want to CHANGE the sanction level.
Higher levels need coalition support to be effective.
If no changes needed, return {"changes": {}, "reasoning": "maintaining current sanctions"}.
Return ONLY valid JSON."""

OPEC_INSTRUCTION = """Decide your OPEC production level.

Return a JSON object:
{
  "production": "<one of: min, low, normal, high, max>",
  "reasoning": "<1-2 sentences>"
}

Return ONLY valid JSON."""

MILITARY_INSTRUCTION = """Decide your military actions for this round.

Return a JSON object:
{
  "actions": [
    {"type": "<attack|blockade|mobilize|deploy|move|missile_strike|fortify>",
     "target_zone": "<zone_id>",
     "units": {"ground": 0, "naval": 0, "air": 0},
     "detail": "<brief description>"}
  ],
  "reasoning": "<1-2 sentences on overall military strategy>"
}

If no military actions needed, return {"actions": [], "reasoning": "no military action needed"}.
Be specific about zones and unit counts. Don't commit more units than you have.
Return ONLY valid JSON."""

COVERT_INSTRUCTION = """Decide whether to launch a covert operation this round.

Return a JSON object:
{
  "operation": {
    "type": "<espionage|sabotage|cyber|disinformation|election_meddling|assassination>",
    "target_country": "<country_id>",
    "detail": "<brief description>"
  },
  "reasoning": "<1-2 sentences>"
}

If no covert op needed, return {"operation": null, "reasoning": "no covert action warranted"}.
Return ONLY valid JSON."""

POLITICAL_INSTRUCTION = """Decide whether to take a political action this round.

Return a JSON object:
{
  "action": {
    "type": "<propaganda|repression|public_statement>",
    "detail": "<brief description or statement text>",
    "spend": <coins to spend, 0 for public_statement>
  },
  "reasoning": "<1-2 sentences>"
}

If no political action needed, return {"action": null, "reasoning": "no political action needed"}.
Return ONLY valid JSON."""

ACTIVE_LOOP_INSTRUCTION = """What should you do RIGHT NOW?

Return a JSON object:
{
  "action": "<wait|request_conversation|military_action|covert_op|public_statement|other>",
  "target": "<who/what — e.g., country_id for conversation, zone for military>",
  "detail": "<brief description>",
  "urgency": "<low|medium|high>",
  "reasoning": "<1-2 sentences>"
}

If nothing urgent, return {"action": "wait", "target": null, "detail": "monitoring situation", "urgency": "low", "reasoning": "..."}.
Return ONLY valid JSON."""


# ---------------------------------------------------------------------------
# DECISION FUNCTIONS — each builds full prompt and calls LLM
# ---------------------------------------------------------------------------

async def decide_budget(
    cognitive_blocks: dict,
    country: dict,
    round_context: dict,
) -> dict:
    """Make budget decision using LLM.

    Args:
        cognitive_blocks: {block1_rules, block2_identity, memory_text, goals_text}
        country: Country data dict.
        round_context: Current round context.

    Returns:
        {social_pct: float, military_coins: float, tech_coins: float, reasoning: str}
    """
    from engine.services.llm import call_llm
    from engine.config.settings import LLMUseCase

    layer2 = build_budget_context(country, round_context)
    system = _build_system_prompt(cognitive_blocks, layer2)

    response = await call_llm(
        use_case=LLMUseCase.AGENT_DECISION,
        messages=[{"role": "user", "content": BUDGET_INSTRUCTION}],
        system=system,
        max_tokens=400,
        temperature=0.5,
    )

    result = _parse_json(response.text)
    if result is None:
        logger.warning("Budget decision parse failed, using defaults")
        return {"social_pct": 1.0, "military_coins": 0, "tech_coins": 0, "reasoning": "parse_error"}

    # Clamp values
    result["social_pct"] = max(0.5, min(1.5, float(result.get("social_pct", 1.0))))
    result["military_coins"] = max(0, float(result.get("military_coins", 0)))
    result["tech_coins"] = max(0, float(result.get("tech_coins", 0)))
    return result


async def decide_tariffs(
    cognitive_blocks: dict,
    country: dict,
    round_context: dict,
) -> dict:
    """Make tariff decision using LLM.

    Returns:
        {changes: {country_id: level}, reasoning: str}
    """
    from engine.services.llm import call_llm
    from engine.config.settings import LLMUseCase

    layer2 = build_tariff_context(country, round_context)
    system = _build_system_prompt(cognitive_blocks, layer2)

    response = await call_llm(
        use_case=LLMUseCase.AGENT_DECISION,
        messages=[{"role": "user", "content": TARIFF_INSTRUCTION}],
        system=system,
        max_tokens=400,
        temperature=0.5,
    )

    result = _parse_json(response.text)
    if result is None:
        return {"changes": {}, "reasoning": "parse_error"}

    # Validate levels
    changes = {}
    for cid, level in result.get("changes", {}).items():
        changes[cid] = max(0, min(3, int(level)))
    result["changes"] = changes
    return result


async def decide_sanctions(
    cognitive_blocks: dict,
    country: dict,
    round_context: dict,
) -> dict:
    """Make sanction decision using LLM.

    Returns:
        {changes: {country_id: level}, reasoning: str}
    """
    from engine.services.llm import call_llm
    from engine.config.settings import LLMUseCase

    layer2 = build_sanction_context(country, round_context)
    system = _build_system_prompt(cognitive_blocks, layer2)

    response = await call_llm(
        use_case=LLMUseCase.AGENT_DECISION,
        messages=[{"role": "user", "content": SANCTION_INSTRUCTION}],
        system=system,
        max_tokens=400,
        temperature=0.5,
    )

    result = _parse_json(response.text)
    if result is None:
        return {"changes": {}, "reasoning": "parse_error"}

    changes = {}
    for cid, level in result.get("changes", {}).items():
        changes[cid] = max(0, min(3, int(level)))
    result["changes"] = changes
    return result


async def decide_opec(
    cognitive_blocks: dict,
    country: dict,
    round_context: dict,
) -> dict:
    """Make OPEC production decision using LLM.

    Returns:
        {production: str, reasoning: str}
    """
    from engine.services.llm import call_llm
    from engine.config.settings import LLMUseCase

    layer2 = build_opec_context(country, round_context)
    system = _build_system_prompt(cognitive_blocks, layer2)

    response = await call_llm(
        use_case=LLMUseCase.AGENT_DECISION,
        messages=[{"role": "user", "content": OPEC_INSTRUCTION}],
        system=system,
        max_tokens=300,
        temperature=0.5,
    )

    result = _parse_json(response.text)
    if result is None:
        return {"production": "normal", "reasoning": "parse_error"}

    valid = {"min", "low", "normal", "high", "max"}
    prod = result.get("production", "normal").lower().strip()
    if prod not in valid:
        prod = "normal"
    result["production"] = prod
    return result


async def decide_military(
    cognitive_blocks: dict,
    country: dict,
    round_context: dict,
) -> dict:
    """Make military decision using LLM.

    Returns:
        {actions: list[dict], reasoning: str}
    """
    from engine.services.llm import call_llm
    from engine.config.settings import LLMUseCase

    layer2 = build_military_context(country, round_context)
    system = _build_system_prompt(cognitive_blocks, layer2)

    response = await call_llm(
        use_case=LLMUseCase.AGENT_DECISION,
        messages=[{"role": "user", "content": MILITARY_INSTRUCTION}],
        system=system,
        max_tokens=600,
        temperature=0.5,
    )

    result = _parse_json(response.text)
    if result is None:
        return {"actions": [], "reasoning": "parse_error"}

    # Validate action types
    valid_types = {"attack", "blockade", "mobilize", "deploy", "move", "missile_strike", "fortify"}
    actions = []
    for a in result.get("actions", []):
        if isinstance(a, dict) and a.get("type") in valid_types:
            actions.append(a)
    result["actions"] = actions
    return result


async def decide_covert(
    cognitive_blocks: dict,
    country: dict,
    role: dict,
    round_context: dict,
) -> dict:
    """Make covert operations decision using LLM.

    Returns:
        {operation: dict|None, reasoning: str}
    """
    from engine.services.llm import call_llm
    from engine.config.settings import LLMUseCase

    layer2 = build_covert_context(country, role, round_context)
    system = _build_system_prompt(cognitive_blocks, layer2)

    response = await call_llm(
        use_case=LLMUseCase.AGENT_DECISION,
        messages=[{"role": "user", "content": COVERT_INSTRUCTION}],
        system=system,
        max_tokens=400,
        temperature=0.7,
    )

    result = _parse_json(response.text)
    if result is None:
        return {"operation": None, "reasoning": "parse_error"}

    # Validate op type
    if result.get("operation"):
        valid_ops = {"espionage", "sabotage", "cyber", "disinformation",
                     "election_meddling", "assassination"}
        op = result["operation"]
        if isinstance(op, dict) and op.get("type") not in valid_ops:
            result["operation"] = None
    return result


async def decide_political(
    cognitive_blocks: dict,
    country: dict,
    round_context: dict,
) -> dict:
    """Make political action decision using LLM.

    Returns:
        {action: dict|None, reasoning: str}
    """
    from engine.services.llm import call_llm
    from engine.config.settings import LLMUseCase

    layer2 = build_political_context(country, round_context)
    system = _build_system_prompt(cognitive_blocks, layer2)

    response = await call_llm(
        use_case=LLMUseCase.AGENT_DECISION,
        messages=[{"role": "user", "content": POLITICAL_INSTRUCTION}],
        system=system,
        max_tokens=400,
        temperature=0.7,
    )

    result = _parse_json(response.text)
    if result is None:
        return {"action": None, "reasoning": "parse_error"}

    if result.get("action"):
        valid = {"propaganda", "repression", "public_statement"}
        action = result["action"]
        if isinstance(action, dict) and action.get("type") not in valid:
            result["action"] = None
    return result


async def decide_active_loop(
    cognitive_blocks: dict,
    country: dict,
    role: dict,
    round_context: dict,
) -> dict:
    """Active loop decision: what to do right now?

    Returns:
        {action: str, target: str|None, detail: str, urgency: str, reasoning: str}
    """
    from engine.services.llm import call_llm
    from engine.config.settings import LLMUseCase

    layer2 = build_active_loop_context(country, role, round_context)
    system = _build_system_prompt(cognitive_blocks, layer2)

    response = await call_llm(
        use_case=LLMUseCase.AGENT_DECISION,
        messages=[{"role": "user", "content": ACTIVE_LOOP_INSTRUCTION}],
        system=system,
        max_tokens=400,
        temperature=0.7,
    )

    result = _parse_json(response.text)
    if result is None:
        return {"action": "wait", "target": None, "detail": "parse_error",
                "urgency": "low", "reasoning": "parse_error"}
    return result


# ---------------------------------------------------------------------------
# SYSTEM PROMPT BUILDER
# ---------------------------------------------------------------------------

def _build_system_prompt(cognitive_blocks: dict, layer2_context: str) -> str:
    """Combine Layer 1 (permanent) + Layer 2 (task-specific) into system prompt.

    Args:
        cognitive_blocks: Dict with block1_rules, block2_identity, memory_text, goals_text.
        layer2_context: Task-specific context string (built by context builders above).

    Returns:
        Full system prompt string.
    """
    parts = []

    # Layer 1: Identity (always first — defines who the agent IS)
    identity = cognitive_blocks.get("block2_identity", "")
    if identity:
        parts.append(f"# Who You Are\n{identity}")

    # Layer 1: Goals & Strategy
    goals = cognitive_blocks.get("goals_text", "")
    if goals:
        parts.append(goals)

    # Layer 1: Memory
    memory = cognitive_blocks.get("memory_text", "")
    if memory:
        parts.append(memory)

    # Layer 2: Task-specific context
    parts.append(layer2_context)

    return "\n\n---\n\n".join(parts)


# ---------------------------------------------------------------------------
# HIGH-LEVEL ORCHESTRATION (called from LeaderAgent)
# ---------------------------------------------------------------------------

async def submit_all_mandatory(
    cognitive_blocks: dict,
    country: dict,
    role: dict,
    round_context: dict,
) -> dict:
    """Produce all mandatory round-end decisions.

    Called by LeaderAgent.submit_mandatory_inputs().

    Returns:
        {budget: {}, tariffs: {}, sanctions: {}, opec_production: str|None, reasoning: {}}
    """
    budget = await decide_budget(cognitive_blocks, country, round_context)
    tariffs = await decide_tariffs(cognitive_blocks, country, round_context)
    sanctions = await decide_sanctions(cognitive_blocks, country, round_context)

    opec_result = None
    if country.get("opec_member", False):
        opec_result = await decide_opec(cognitive_blocks, country, round_context)

    return {
        "budget": {
            "social_pct": budget["social_pct"],
            "military_coins": budget["military_coins"],
            "tech_coins": budget["tech_coins"],
        },
        "tariffs": tariffs.get("changes", {}),
        "sanctions": sanctions.get("changes", {}),
        "opec_production": opec_result["production"] if opec_result else None,
        "reasoning": {
            "budget": budget.get("reasoning", ""),
            "tariffs": tariffs.get("reasoning", ""),
            "sanctions": sanctions.get("reasoning", ""),
            "opec": opec_result.get("reasoning", "") if opec_result else None,
        },
    }


async def decide_action_dispatch(
    cognitive_blocks: dict,
    country: dict,
    role: dict,
    round_context: dict,
    time_remaining: float,
    new_events: list[dict],
) -> dict | None:
    """Proactive decision: what to do RIGHT NOW?

    Called by LeaderAgent.decide_action().
    First decides what to do via active loop, then dispatches to specific
    decision type if needed.

    Returns:
        Action dict or None (wait).
    """
    # Merge new events into round context for the active loop
    ctx = dict(round_context)
    ctx["recent_events"] = new_events
    ctx["time_remaining"] = time_remaining

    loop_result = await decide_active_loop(cognitive_blocks, country, role, ctx)

    action_type = loop_result.get("action", "wait")
    if action_type == "wait":
        return None

    if action_type == "military_action":
        mil = await decide_military(cognitive_blocks, country, ctx)
        if mil.get("actions"):
            return {"type": "military", "actions": mil["actions"], "reasoning": mil.get("reasoning", "")}

    if action_type == "covert_op":
        cov = await decide_covert(cognitive_blocks, country, role, ctx)
        if cov.get("operation"):
            return {"type": "covert", "operation": cov["operation"], "reasoning": cov.get("reasoning", "")}

    if action_type == "request_conversation":
        return {
            "type": "request_conversation",
            "target": loop_result.get("target"),
            "detail": loop_result.get("detail", ""),
            "reasoning": loop_result.get("reasoning", ""),
        }

    if action_type == "public_statement":
        return {
            "type": "public_statement",
            "detail": loop_result.get("detail", ""),
            "reasoning": loop_result.get("reasoning", ""),
        }

    # Generic action passthrough
    return {
        "type": action_type,
        "target": loop_result.get("target"),
        "detail": loop_result.get("detail", ""),
        "reasoning": loop_result.get("reasoning", ""),
    }
