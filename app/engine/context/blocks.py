"""Context block builders — each block is a named function that produces text.

Blocks are registered in BLOCK_REGISTRY. The assembler calls build_block()
which dispatches to the appropriate builder function.

Source: SEED_D9_CONTEXT_ASSEMBLY_v1.md (Section 3: Context Blocks)
"""

from __future__ import annotations

import json
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from engine.context.assembler import ContextAssembler


# ---------------------------------------------------------------------------
# BLOCK REGISTRY
# ---------------------------------------------------------------------------

BLOCK_REGISTRY: dict[str, str] = {
    "sim_rules": "Game rules, mechanics, all parameters",
    "methodology": "Judgment rules, definitions, examples, bounds",
    "world_state": "Current state of all countries (visibility-scoped)",
    "sim_history": "Summarized round-by-round events",
    "round_inputs": "This round's submitted actions/decisions",
    "round_outputs": "Pass 1 formula results",
    "role_context": "Role brief, powers, objectives, personal state",
    "available_actions": "What this role can do this round",
}


def build_block(
    name: str,
    assembler: ContextAssembler,
    *,
    scope: str | None = None,
    **params,
) -> str:
    """Dispatch to the appropriate block builder."""
    builder = _BUILDERS.get(name)
    if builder is None:
        return f"[Block '{name}' not implemented]"
    return builder(assembler, scope=scope, **params)


# ---------------------------------------------------------------------------
# BLOCK BUILDERS
# ---------------------------------------------------------------------------

def _build_sim_rules(ctx: ContextAssembler, **_) -> str:
    """Game rules and mechanics — loaded from sim_config or generated."""
    custom = ctx.get_methodology("sim_rules")
    if custom:
        return f"# SIM Rules\n\n{custom}"

    # Default rules summary
    return """# SIM Rules — Thucydides Trap

## Overview
The Thucydides Trap is a geopolitical simulation with 21 countries, 6-8 rounds, 4 domains (economic, military, political, technology). Each round represents ~6 months.

## Economic
- GDP growth uses immutable base rates (annual, halved for 6-month rounds)
- Sanctions: GDP coefficient model (0.50-1.0), recomputed every round
- Tariffs: prisoner's dilemma model (big economy hits small cheaply)
- Oil price: supply/demand with non-linear amplification (exponent 2.5)
- Budget: social spending as % of GDP, maintenance ×3, deficit 50/50 borrowed/printed
- Inflation: printing ×60, oil ±3pp/$50, tariff level, surplus -1pp/round

## Military
- RISK dice + modifiers for combat resolution
- Blockades: ship or ground can block chokepoints (partial/full)
- Reserve mechanic: off-map, deploy between rounds
- Mobilization: finite, depletable, never recovers

## Political
- Stability (1-9): GDP growth + social spending + war + inflation delta + regime modifiers
- Support (5-85%): GDP + stability + inflation + casualties + war tiredness
- Elections: Columbia R2 midterms, R5 presidential. Ruthenia R3 (or forced).
- Revolution: protests auto-trigger at stability≤2 AND support<20%

## Technology
- AI race: only Columbia + Cathay compete. L4 achievable R7-8.
- Nuclear: Persia at 70% toward L1 (breakout imminent).

## Key Countries
- **Columbia** (US): GDP 280, democracy, at war with Persia, high Formosa dependency
- **Cathay** (China): GDP 190, autocracy, rising power, 4% growth
- **Sarmatia** (Russia): GDP 20, autocracy, at war with Ruthenia, under sanctions
- **Ruthenia** (Ukraine): GDP 2.2, democracy, defending homeland
- **Persia** (Iran): GDP 5, hybrid, nuclear program, controls Gulf Gate
"""


def _build_methodology(ctx: ContextAssembler, **_) -> str:
    """The Book — judgment methodology, definitions, bounds."""
    parts = ["# Judgment Methodology\n"]

    # Load all methodology entries from sim_config
    for key in ("crisis_definition", "contagion_rules", "capitulation_criteria",
                "stability_factors", "support_factors", "market_sentiment",
                "bounds", "anti_patterns", "historical_examples"):
        content = ctx.get_methodology(key)
        if content:
            parts.append(f"## {key.replace('_', ' ').title()}\n{content}\n")

    # If no custom methodology loaded, use defaults
    if len(parts) == 1:
        parts.append(_DEFAULT_METHODOLOGY)

    return "\n".join(parts)


def _build_world_state(ctx: ContextAssembler, *, scope: str | None = None, **_) -> str:
    """Current world state — full or visibility-scoped."""
    countries = ctx.countries
    ws = ctx.world_state
    if not countries:
        return "[No world state available]"

    lines = ["# World State\n"]

    # Global
    oil = ws.get("oil_price", 80)
    mkt = ws.get("market_indexes", {})
    lines.append(f"**Oil price:** ${oil:.0f}")
    if mkt:
        lines.append(f"**Market indexes:** Wall Street={mkt.get('wall_street', 100):.0f}, "
                      f"Europa={mkt.get('europa', 100):.0f}, Dragon={mkt.get('dragon', 100):.0f}")

    # Wars
    wars = ws.get("wars", [])
    if wars:
        war_strs = []
        for w in wars:
            a = ", ".join(w.get("belligerents_a", []))
            b = ", ".join(w.get("belligerents_b", []))
            war_strs.append(f"{a} vs {b}")
        lines.append(f"**Active wars:** {'; '.join(war_strs)}")

    # Blockades
    blockades = ws.get("active_blockades", {})
    if blockades:
        lines.append(f"**Active blockades:** {', '.join(blockades.keys())}")

    lines.append("")

    # Countries
    if scope:
        # Scoped: show one country in detail
        country_ids = [scope]
    else:
        # Full: show all countries
        country_ids = sorted(countries.keys())

    for cid in country_ids:
        c = countries.get(cid)
        if not c:
            continue
        eco = c.get("economic", {})
        pol = c.get("political", {})
        tech = c.get("technology", {})

        lines.append(f"## {c.get('sim_name', cid)} ({c.get('regime_type', '?')})")
        lines.append(f"- GDP: {eco.get('gdp', 0):.1f} (growth: {eco.get('gdp_growth_rate', 0):+.1f}%)")
        lines.append(f"- Treasury: {eco.get('treasury', 0):.1f}, Inflation: {eco.get('inflation', 0):.1f}%")
        lines.append(f"- Debt/GDP: {eco.get('debt_burden', 0):.0%}")
        lines.append(f"- Sanctions coeff: {eco.get('sanctions_coefficient', 1.0):.3f}, "
                      f"Tariff coeff: {eco.get('tariff_coefficient', 1.0):.3f}")
        lines.append(f"- Stability: {pol.get('stability', 5):.1f}, Support: {pol.get('political_support', 50):.0f}%")
        lines.append(f"- Economic state: {eco.get('economic_state', 'normal')}")
        if eco.get("oil_producer"):
            lines.append(f"- Oil producer: {eco.get('oil_production_mbpd', 0)} mbpd")
        if tech.get("nuclear_rd_progress", 0) > 0:
            lines.append(f"- Nuclear: L{tech.get('nuclear_level', 0)} ({tech.get('nuclear_rd_progress', 0):.0%} to next)")
        if tech.get("ai_rd_progress", 0) > 0:
            lines.append(f"- AI: L{tech.get('ai_level', 0)} ({tech.get('ai_rd_progress', 0):.0%} to next)")
        lines.append("")

    return "\n".join(lines)


def _build_sim_history(ctx: ContextAssembler, **_) -> str:
    """Summarized round-by-round events."""
    events = ctx.event_log
    if not events:
        return "# SIM History\n\nNo events recorded yet."

    lines = ["# SIM History\n"]
    # Group by round
    by_round: dict[int, list] = {}
    for e in events:
        rnd = e.get("round_num", 0)
        by_round.setdefault(rnd, []).append(e)

    for rnd in sorted(by_round.keys()):
        lines.append(f"## Round {rnd}")
        for e in by_round[rnd][:10]:  # limit per round to control token count
            lines.append(f"- {e.get('summary', json.dumps(e, default=str)[:200])}")
        if len(by_round[rnd]) > 10:
            lines.append(f"  ... and {len(by_round[rnd]) - 10} more events")
        lines.append("")

    return "\n".join(lines)


def _build_round_inputs(ctx: ContextAssembler, **_) -> str:
    """This round's submitted actions."""
    ws = ctx.world_state
    lines = ["# Round Inputs\n"]

    sanctions = ws.get("bilateral", {}).get("sanctions", {})
    tariffs = ws.get("bilateral", {}).get("tariffs", {})

    if sanctions:
        lines.append("## Active Sanctions")
        for imposer, targets in sorted(sanctions.items()):
            for target, level in sorted(targets.items()):
                lines.append(f"- {imposer} → {target}: L{level}")
        lines.append("")

    if tariffs:
        lines.append("## Active Tariffs")
        for imposer, targets in sorted(tariffs.items()):
            for target, level in sorted(targets.items()):
                lines.append(f"- {imposer} → {target}: L{level}")
        lines.append("")

    blockades = ws.get("active_blockades", {})
    if blockades:
        lines.append("## Active Blockades")
        for cp, info in blockades.items():
            controller = info.get("controller", "unknown") if isinstance(info, dict) else "unknown"
            status = info.get("status", "blocked") if isinstance(info, dict) else "blocked"
            lines.append(f"- {cp}: {status} (controller: {controller})")
        lines.append("")

    return "\n".join(lines)


def _build_round_outputs(ctx: ContextAssembler, **_) -> str:
    """Pass 1 formula results."""
    results = ctx.round_results
    if not results:
        return "# Round Outputs\n\n[No results available — Pass 1 not yet run]"

    lines = ["# Round Outputs (Pass 1 — Deterministic)\n"]

    # Oil
    oil = results.get("oil_price")
    if oil:
        lines.append(f"**Oil price:** ${oil:.1f}")

    # Market indexes
    mkt = results.get("market_indexes")
    if mkt:
        lines.append(f"**Market indexes:** Wall Street={mkt.get('wall_street', 100):.0f}, "
                      f"Europa={mkt.get('europa', 100):.0f}, Dragon={mkt.get('dragon', 100):.0f}")

    # Per-country results
    countries = ctx.countries
    lines.append("\n## Per-Country Results\n")

    for cid in sorted(countries.keys()):
        c = countries[cid]
        eco = c.get("economic", {})
        pol = c.get("political", {})
        name = c.get("sim_name", cid)

        gdp = eco.get("gdp", 0)
        growth = eco.get("gdp_growth_rate", 0)
        stab = pol.get("stability", 5)
        sup = pol.get("political_support", 50)
        infl = eco.get("inflation", 0)
        treas = eco.get("treasury", 0)
        state = eco.get("economic_state", "normal")

        flag = ""
        if stab < 3:
            flag = " ⚠️ LOW STABILITY"
        elif state != "normal":
            flag = f" ⚠️ {state.upper()}"

        lines.append(f"- **{name}**: GDP {gdp:.0f} ({growth:+.1f}%), stab {stab:.1f}, "
                      f"sup {sup:.0f}%, infl {infl:.0f}%, treas {treas:.0f}{flag}")

    return "\n".join(lines)


def _build_role_context(ctx: ContextAssembler, *, scope: str | None = None, **_) -> str:
    """Role brief, powers, objectives for a specific role."""
    if not scope:
        return "[role_context requires scope — e.g., role_context:anchor]"

    role = ctx.roles.get(scope, {})
    if not role:
        return f"[Role '{scope}' not found]"

    lines = [f"# Role: {role.get('character_name', scope)}"]
    lines.append(f"**Country:** {role.get('country_id', '?')}")
    lines.append(f"**Title:** {role.get('title', '?')}")
    if role.get("is_head_of_state"):
        lines.append("**Head of State** — has broadest decision powers")

    powers = role.get("powers", [])
    if powers:
        lines.append(f"\n**Powers:** {', '.join(powers)}")

    objectives = role.get("objectives", [])
    if objectives:
        lines.append(f"\n**Objectives:**")
        for obj in objectives:
            lines.append(f"- {obj}")

    clock = role.get("ticking_clock", "")
    if clock:
        lines.append(f"\n**Ticking Clock:** {clock}")

    return "\n".join(lines)


def _build_available_actions(ctx: ContextAssembler, *, scope: str | None = None, **_) -> str:
    """What actions this role can take this round."""
    # For now, return the standard action categories
    # TODO: filter by role powers and current state
    return """# Available Actions

## Economic
- Set budget allocation (social spending %, military %, tech %)
- Impose/change tariffs (L0-L3) on any country
- Impose/change sanctions (L0-L3) on any country (requires coalition for L2+)
- Print money (once/round, 3% GDP → treasury + inflation)
- OPEC production decision (if OPEC member): min/low/normal/high/max

## Military
- Deploy units from reserve to territory
- Move units between own/allied zones
- Order attack (ground, naval, air strike)
- Mobilize from pool (if available)
- Sell/transfer arms to other countries

## Diplomatic
- Propose ceasefire, peace treaty, alliance
- Trade bilateral agreements
- Make public statement

## Covert (if intelligence pool > 0)
- Espionage, sabotage, cyber attack, disinformation, election interference
"""


# ---------------------------------------------------------------------------
# BUILDER DISPATCH
# ---------------------------------------------------------------------------

_BUILDERS: dict[str, Any] = {
    "sim_rules": _build_sim_rules,
    "methodology": _build_methodology,
    "world_state": _build_world_state,
    "sim_history": _build_sim_history,
    "round_inputs": _build_round_inputs,
    "round_outputs": _build_round_outputs,
    "role_context": _build_role_context,
    "available_actions": _build_available_actions,
}


# ---------------------------------------------------------------------------
# DEFAULT METHODOLOGY (used when sim_config has no entries)
# ---------------------------------------------------------------------------

_DEFAULT_METHODOLOGY = """
## Crisis Definition
A country is in CRISIS when compounding negative indicators are present:
- GDP declined 3+ consecutive rounds AND/OR
- Inflation exceeds baseline by 20+ percentage points AND/OR
- Stability below 4 AND declining AND/OR
- Treasury depleted with ongoing deficit

Crisis is NOT triggered by a single bad round. It requires sustained deterioration.
GDP penalty when in crisis: -1% to -2% per round (judgment call based on severity).

## Contagion Rules
Economic crisis spreads through trade links when:
- A major economy (GDP > 30) enters crisis
- Trade partner has exposure > 10% (via tariff/sanctions coefficients or bilateral trade)
- Channel: energy dependency, supply chain, financial markets, confidence

Contagion GDP impact: 0% to -2% per affected country per round.

## Stability Adjustment Factors (beyond Pass 1 formulas)
- Leadership quality / scandal effects
- Rally-around-flag during external threat
- War fatigue beyond formula capture
- Market panic cascading to public confidence
- Election uncertainty premium

Bounds: ±0.5 stability per round.

## Support Adjustment Factors (beyond Pass 1 formulas)
- Narrative events (scandals, heroic acts, diplomatic wins/losses)
- Propaganda effectiveness
- Opposition mobilization
- Media coverage of economic conditions

Bounds: ±5pp support per round.

## Market Index Nudge
Formula computes base indexes. AI can nudge ±10 points for:
- Sentiment beyond economic fundamentals
- Panic / irrational exuberance
- Contagion fears
- Tech disruption anxiety (e.g., Formosa crisis → Dragon index)

## Anti-Patterns (DO NOT)
- Don't double-count what Pass 1 already handles (GDP growth, oil price, sanctions coefficient)
- Don't create death spirals — if a country is declining, the adjustment should reflect reality, not accelerate collapse
- Don't eliminate any country before Round 4
- Don't override Pass 1 GDP calculations directly — use crisis penalty or contagion
- Don't apply maximum adjustments to every country every round — most rounds, most countries need no adjustment

## Historical Reference Points
- **2008 Financial Crisis**: contagion through financial system, not trade. GDP impact -2% to -8% over 2 years.
- **1973 Oil Embargo**: supply shock, 4× price spike, stagflation. GDP impact -3% to -5%.
- **1997 Asian Financial Crisis**: contagion via capital flight, currency collapse. Spread from Thailand to Korea, Indonesia.
- **2022 Russia Sanctions**: ~10% GDP hit year 1, adaptation and rerouting by year 2. Oil revenue partially maintained.
"""
