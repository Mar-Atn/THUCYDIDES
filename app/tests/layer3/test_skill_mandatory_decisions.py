"""L3 Skill: Mandatory End-of-Round Economic Decisions (RIGOROUS, 4-call architecture).

This harness verifies MEANINGFUL DECISIONS on all 4 mandatory decision types
(budget, sanctions, tariffs, OPEC) using the CORRECT architecture: FOUR
separate, domain-focused LLM calls per agent — not one combined call.

Each decision has its own focused prompt with only the context relevant to
that domain (D1 budget = economic state; D2 sanctions = relationships/wars;
D3 tariffs = trade partners; D4 OPEC = oil + geopolitics). This matches
real-world leadership: a budget meeting is not a sanctions committee.

Benefits of the split architecture:
1. Reduced cognitive load per call (focused context, focused decision)
2. Specialized context per domain
3. Parallelizable via asyncio.gather
4. Each skill (D1/D2/D3/D4) independently testable
5. Matches the 34-skill catalog in AI_CONCEPT.md

The four prompt builder functions are defined INSIDE this test file. They are
intentionally not imported from production source — the goal is to prove the
new approach here before deciding whether to port it to
``engine/agents/full_round_runner.py``.

Run:
    cd app && PYTHONPATH=. python3 -m pytest tests/layer3/test_skill_mandatory_decisions.py -v -s

Skip LLM tests:
    cd app && PYTHONPATH=. python3 -m pytest tests/layer3/test_skill_mandatory_decisions.py -v -m "not llm"

Cost: 10 leaders x ~3.4 calls each = ~34 LLM calls on Gemini Flash ~ $0.04.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field

import pytest

from engine.agents.decisions import _parse_json
from engine.agents.full_round_runner import OPEC_MEMBERS
from engine.config.settings import LLMUseCase
from engine.services.llm import call_llm

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SYSTEM_BUDGET = (
    "You are an AI head of state reviewing the national budget. "
    "Return ONLY JSON. Every field required. Rationale mandatory on both "
    "change and no_change."
)
SYSTEM_SANCTIONS = (
    "You are an AI head of state reviewing your sanctions policy. "
    "Return ONLY JSON. Every field required. Rationale mandatory on both "
    "change and no_change."
)
SYSTEM_TARIFFS = (
    "You are an AI head of state reviewing your trade and tariff policy. "
    "Return ONLY JSON. Every field required. Rationale mandatory on both "
    "change and no_change."
)
SYSTEM_OPEC = (
    "You are an AI head of state reviewing OPEC production posture. "
    "Return ONLY JSON. Every field required. Rationale mandatory on both "
    "change and no_change."
)

VALID_OPEC_LEVELS = {"min", "low", "normal", "high", "max"}
VALID_DECISION_VALUES = {"change", "no_change"}
MIN_RATIONALE_LEN = 20

ROUND_NUM = 2


# ---------------------------------------------------------------------------
# Scenario dataclass — self-contained snapshot of a leader's situation
# ---------------------------------------------------------------------------

@dataclass
class LeaderScenario:
    """A self-contained snapshot of a leader's situation at round-end.

    Values approximate round-2 state in ``start_one``. Hard-coded snapshots
    keep tests deterministic and independent of DB drift.
    """

    country_code: str
    country_name: str
    character_name: str
    title: str

    # Economic state
    gdp: float
    gdp_change_pct: float
    treasury: float
    inflation: float
    stability: float
    political_support: float
    war_tiredness: float

    # Situation narrative
    wars: list[str] = field(default_factory=list)
    allies: list[str] = field(default_factory=list)
    threats: list[str] = field(default_factory=list)
    recent_events: list[str] = field(default_factory=list)

    # Current economic settings
    social_pct: float = 1.0
    military_coins: int = 0
    tech_coins: int = 0

    sanctions_imposed: list[dict] = field(default_factory=list)
    sanctions_against: list[dict] = field(default_factory=list)
    tariffs_imposed: list[dict] = field(default_factory=list)

    # Trade partners (for tariff call)
    major_trade_partners: list[dict] = field(default_factory=list)

    # OPEC-specific
    opec_level: str | None = None
    oil_price: float = 75.0
    oil_revenue_potential: float = 0.0

    objectives: list[str] = field(default_factory=list)
    expected_direction: str = ""

    @property
    def is_opec(self) -> bool:
        return self.country_code in OPEC_MEMBERS


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _bullets(items: list[str], empty: str = "  (none)") -> str:
    if not items:
        return empty
    return "\n".join(f"  - {i}" for i in items)


def _fmt_entries(items: list[dict], empty: str) -> str:
    if not items:
        return empty
    lines = []
    for s in items:
        target = s.get("target", "?")
        level = s.get("level", "?")
        note = s.get("note", "")
        suffix = f" — {note}" if note else ""
        lines.append(f"  - {target}: level {level}{suffix}")
    return "\n".join(lines)


def _objectives_block(objs: list[str]) -> str:
    return _bullets(objs, "  (no objectives specified)")


# ---------------------------------------------------------------------------
# D1: Budget prompt — economic state only, focused on allocation
# ---------------------------------------------------------------------------

def _build_budget_prompt(s: LeaderScenario) -> str:
    gdp_sign = "+" if s.gdp_change_pct >= 0 else ""
    war_line = f"At war with: {', '.join(s.wars)}" if s.wars else "Not at war."

    return f"""You are {s.character_name}, {s.title} of {s.country_name}.

## D1 — BUDGET REVIEW (Round {ROUND_NUM})

This is the BUDGET meeting. Focus only on fiscal allocation. Do NOT address
sanctions, tariffs, or OPEC in this call.

## Economic state
- GDP: {s.gdp:.0f} ({gdp_sign}{s.gdp_change_pct:.1f}% vs last round)
- Treasury: {s.treasury:.0f} coins
- Inflation: {s.inflation:.1f}%
- Stability: {s.stability:.1f}/10
- Political support: {s.political_support:.0f}%
- War tiredness: {s.war_tiredness:.1f}
- {war_line}

## Current budget
- Social spending: {s.social_pct:.2f} x baseline
- Military allocation: {s.military_coins} coins
- Tech R&D allocation: {s.tech_coins} coins

## Your relevant objectives
{_objectives_block(s.objectives)}

## INSTRUCTIONS
Decide whether to CHANGE the budget or keep it NO_CHANGE. Either way you MUST
provide a rationale of at least one sentence (>20 chars) explaining WHY.

Consider:
- If at war or treasury healthy → military or tech may rise
- If inflation high → social spending may need to be cut
- If treasury critical → austerity; minimal new allocations
- If stable and rich → tech or diversification

Respond with JSON ONLY, matching this EXACT schema:

{{
  "decision": "change" | "no_change",
  "rationale": "string, >= 20 characters, explains the why",
  "changes": {{
    "social_pct": 1.0,
    "military_coins": 2,
    "tech_coins": 1
  }}
}}

Rules:
- social_pct range 0.5 to 1.5
- military_coins / tech_coins: 0 to 10 each
- Include "changes" ONLY when decision == "change"
"""


# ---------------------------------------------------------------------------
# D2: Sanctions prompt — relationships and wars focus
# ---------------------------------------------------------------------------

def _build_sanctions_prompt(s: LeaderScenario) -> str:
    war_line = f"At war with: {', '.join(s.wars)}" if s.wars else "Not at war."
    allies_line = f"Allies/friendly: {', '.join(s.allies)}" if s.allies else "No formal allies."
    threats_line = (
        f"Key threats: {', '.join(s.threats)}" if s.threats else "No acute external threats."
    )

    imposed_block = _fmt_entries(
        s.sanctions_imposed,
        "  (none) — you currently sanction no one.",
    )
    against_block = _fmt_entries(
        s.sanctions_against,
        "  (none) — no country currently sanctions you.",
    )

    return f"""You are {s.character_name}, {s.title} of {s.country_name}.

## D2 — SANCTIONS REVIEW (Round {ROUND_NUM})

This is the SANCTIONS committee. Focus only on coercive economic measures
against hostile countries. Do NOT address budget, tariffs, or OPEC here.

## Relationships and threats
- {war_line}
- {allies_line}
- {threats_line}

## Sanctions you currently impose
{imposed_block}

## Sanctions currently imposed against you
{against_block}
Note: You cannot change these (they are imposed by others).

## Your relevant objectives
{_objectives_block(s.objectives)}

## INSTRUCTIONS
Decide whether to CHANGE your sanctions policy or keep it NO_CHANGE. Either
way you MUST provide a rationale of at least one sentence (>20 chars)
explaining WHY.

Consider:
- Hostile/at-war countries without sanctions → consider imposing
- Sanctions on neutrals/allies → consider lifting
- Escalation vs de-escalation trade-offs
- "No change" is valid but must be justified (e.g. "existing L3 on Persia is
  already maximal and serves wartime isolation objective")

Respond with JSON ONLY, matching this EXACT schema:

{{
  "decision": "change" | "no_change",
  "rationale": "string, >= 20 characters",
  "changes": [
    {{ "target": "country_code", "level": 0, "action": "impose|lift|adjust" }}
  ]
}}

Rules:
- level: 0 (none) to 3 (heavy)
- action must be one of: impose, lift, adjust
- Include "changes" ONLY when decision == "change"; it may be empty if the
  decision is no_change
"""


# ---------------------------------------------------------------------------
# D3: Tariffs prompt — trade partners focus
# ---------------------------------------------------------------------------

def _build_tariffs_prompt(s: LeaderScenario) -> str:
    partners_lines = []
    for p in s.major_trade_partners:
        partners_lines.append(
            f"  - {p.get('country', '?')}: {p.get('type', 'trade')} "
            f"(volume {p.get('volume', '?')}, notes: {p.get('note', '')})"
        )
    partners_block = "\n".join(partners_lines) if partners_lines else "  (no detailed partner data)"

    tariffs_block = _fmt_entries(
        s.tariffs_imposed,
        "  (none) — you impose no tariffs today.",
    )

    return f"""You are {s.character_name}, {s.title} of {s.country_name}.

## D3 — TRADE AND TARIFF REVIEW (Round {ROUND_NUM})

This is the TRADE POLICY review. Focus only on tariffs and trade posture. Do
NOT address budget, sanctions, or OPEC in this call.

## Economic context (brief)
- GDP: {s.gdp:.0f}, treasury {s.treasury:.0f}, inflation {s.inflation:.1f}%

## Major trade partners
{partners_block}

## Tariffs you currently impose
{tariffs_block}

## Your relevant objectives
{_objectives_block(s.objectives)}

## INSTRUCTIONS
Decide whether to CHANGE your tariff policy or keep it NO_CHANGE. Either way
you MUST provide a rationale of at least one sentence (>20 chars) explaining
WHY.

Consider:
- Strategic rivals with deep trade exposure → tariffs may coerce or decouple
- Critical import dependencies → raising tariffs hurts you
- Retaliatory pressure from ongoing trade wars
- Restraint is valid if existing tariffs already match strategy

Respond with JSON ONLY, matching this EXACT schema:

{{
  "decision": "change" | "no_change",
  "rationale": "string, >= 20 characters",
  "changes": [
    {{ "target": "country_code", "level": 0, "action": "impose|lift|adjust" }}
  ]
}}

Rules:
- level: 0 (none) to 3 (heavy)
- action must be one of: impose, lift, adjust
- Include "changes" ONLY when decision == "change"
"""


# ---------------------------------------------------------------------------
# D4: OPEC prompt — oil price, revenue, geopolitical leverage
# ---------------------------------------------------------------------------

def _build_opec_prompt(s: LeaderScenario) -> str:
    assert s.is_opec, "D4 OPEC prompt is only valid for OPEC members"
    war_line = f"At war with: {', '.join(s.wars)}" if s.wars else "Not at war."
    threats_line = (
        f"Key threats: {', '.join(s.threats)}" if s.threats else "No acute external threats."
    )

    return f"""You are {s.character_name}, {s.title} of {s.country_name}.

## D4 — OPEC PRODUCTION REVIEW (Round {ROUND_NUM})

This is the OPEC posture review. Focus only on oil production level and its
fiscal/geopolitical consequences. Do NOT address budget, sanctions, or
tariffs in this call.

## Oil and fiscal context
- Current OPEC production level: {s.opec_level or 'normal'}
- Current oil price: ${s.oil_price:.0f}/bbl
- Your oil revenue potential at current level: ~{s.oil_revenue_potential:.0f} coins/round
- Treasury: {s.treasury:.0f} coins
- Inflation: {s.inflation:.1f}%

## Geopolitical context
- {war_line}
- {threats_line}

## Your relevant objectives
{_objectives_block(s.objectives)}

## INSTRUCTIONS
Decide whether to CHANGE the OPEC production level or keep it NO_CHANGE.
Either way you MUST provide a rationale of at least one sentence (>20 chars)
explaining WHY.

Consider:
- Treasury critical → high/max to grab revenue (accepting future price erosion)
- Price leverage vs rivals → coordinated cuts to raise prices
- Long-term market share concerns → avoid excessive cuts
- Restraint is valid if current level already matches strategy

Respond with JSON ONLY, matching this EXACT schema:

{{
  "decision": "change" | "no_change",
  "rationale": "string, >= 20 characters",
  "new_level": "min | low | normal | high | max"
}}

Rules:
- new_level MUST be one of: min, low, normal, high, max
- When decision == "no_change", new_level should equal the current level
"""


# ---------------------------------------------------------------------------
# Test scenarios (10 leaders)
# ---------------------------------------------------------------------------

SCENARIOS: list[LeaderScenario] = [
    LeaderScenario(
        country_code="columbia",
        country_name="Columbia",
        character_name="Dealer",
        title="President",
        gdp=28000, gdp_change_pct=1.8, treasury=320, inflation=3.1,
        stability=7.2, political_support=52, war_tiredness=3.5,
        wars=["persia"],
        allies=["formosa", "teutonia", "albion"],
        threats=["cathay (strategic rival)", "persia (active war)"],
        recent_events=[
            "Authorized naval deployment to the Gulf",
            "Fed raised rates to combat inflation",
        ],
        social_pct=1.0, military_coins=3, tech_coins=2,
        sanctions_imposed=[{"target": "persia", "level": 3, "note": "wartime"}],
        tariffs_imposed=[{"target": "cathay", "level": 2, "note": "ongoing trade war"}],
        major_trade_partners=[
            {"country": "cathay", "type": "rival", "volume": "high", "note": "trade war ongoing"},
            {"country": "teutonia", "type": "ally", "volume": "high", "note": "NATO partner"},
            {"country": "bharata", "type": "friendly", "volume": "medium"},
        ],
        objectives=[
            "Maintain global hegemony",
            "Contain Cathay economically",
            "Win the war against Persia",
        ],
        expected_direction="military allocation stable or up; sanctions on Persia maintained",
    ),
    LeaderScenario(
        country_code="cathay",
        country_name="Cathay",
        character_name="Helmsman",
        title="President",
        gdp=24500, gdp_change_pct=4.2, treasury=510, inflation=2.2,
        stability=8.0, political_support=68, war_tiredness=0.5,
        wars=[],
        allies=["sarmatia"],
        threats=["columbia (strategic rival)", "formosa (reunification target)"],
        recent_events=[
            "Launched BRI-2 infrastructure initiative",
            "Imposed counter-tariffs on Columbian goods",
        ],
        social_pct=0.9, military_coins=3, tech_coins=4,
        sanctions_imposed=[],
        tariffs_imposed=[{"target": "columbia", "level": 2, "note": "retaliatory"}],
        major_trade_partners=[
            {"country": "columbia", "type": "rival", "volume": "high", "note": "trade war"},
            {"country": "bharata", "type": "neutral", "volume": "medium"},
            {"country": "solaria", "type": "supplier", "volume": "high", "note": "oil imports"},
        ],
        objectives=[
            "Overtake Columbia economically by round 6",
            "Reunify Formosa without war",
            "Dominate tech supply chains",
        ],
        expected_direction="tech emphasis; trade diversification",
    ),
    LeaderScenario(
        country_code="sarmatia",
        country_name="Sarmatia",
        character_name="Pathfinder",
        title="President",
        gdp=2200, gdp_change_pct=-2.5, treasury=90, inflation=9.5,
        stability=5.5, political_support=58, war_tiredness=6.2,
        wars=["ruthenia"],
        allies=["cathay"],
        threats=["teutonia", "albion", "columbia (sanctions)"],
        recent_events=[
            "Western sanctions hit oil exports",
            "Mobilized 3rd army group for Ruthenia front",
        ],
        social_pct=0.8, military_coins=5, tech_coins=1,
        sanctions_imposed=[{"target": "ruthenia", "level": 3, "note": "wartime"}],
        sanctions_against=[
            {"target": "sarmatia", "imposer": "columbia", "level": 3},
            {"target": "sarmatia", "imposer": "teutonia", "level": 2},
        ],
        tariffs_imposed=[],
        major_trade_partners=[
            {"country": "cathay", "type": "ally", "volume": "high", "note": "oil/gas sales"},
            {"country": "bharata", "type": "neutral", "volume": "medium"},
        ],
        objectives=[
            "Win war against Ruthenia",
            "Break Western sanctions coalition",
            "Maintain regime stability",
        ],
        expected_direction="military up; already isolated so tariffs unlikely",
    ),
    LeaderScenario(
        country_code="ruthenia",
        country_name="Ruthenia",
        character_name="Beacon",
        title="President",
        gdp=380, gdp_change_pct=-8.2, treasury=12, inflation=14.0,
        stability=4.5, political_support=71, war_tiredness=8.1,
        wars=["sarmatia"],
        allies=["columbia", "teutonia", "albion"],
        threats=["sarmatia (existential)"],
        recent_events=[
            "Lost eastern oblast to Sarmatian advance",
            "IMF emergency loan approved",
        ],
        social_pct=0.7, military_coins=6, tech_coins=0,
        sanctions_imposed=[{"target": "sarmatia", "level": 3, "note": "defensive war"}],
        tariffs_imposed=[],
        major_trade_partners=[
            {"country": "teutonia", "type": "ally", "volume": "high", "note": "aid pipeline"},
            {"country": "columbia", "type": "ally", "volume": "medium", "note": "military support"},
        ],
        objectives=[
            "Survive as a sovereign state",
            "Maintain Western military support",
            "Hold the eastern front",
        ],
        expected_direction="austerity; treasury critical",
    ),
    LeaderScenario(
        country_code="formosa",
        country_name="Formosa",
        character_name="Chip",
        title="President",
        gdp=850, gdp_change_pct=2.9, treasury=140, inflation=1.8,
        stability=7.8, political_support=60, war_tiredness=1.0,
        wars=[],
        allies=["columbia", "yamato"],
        threats=["cathay (existential)"],
        recent_events=[
            "Announced 2nm fab investment",
            "Joint naval drill with Columbia",
        ],
        social_pct=1.0, military_coins=2, tech_coins=4,
        sanctions_imposed=[],
        tariffs_imposed=[],
        major_trade_partners=[
            {"country": "columbia", "type": "ally", "volume": "high", "note": "semiconductors"},
            {"country": "cathay", "type": "existential threat", "volume": "high", "note": "exposure"},
            {"country": "yamato", "type": "ally", "volume": "medium"},
        ],
        objectives=[
            "Maintain semiconductor shield via tech dominance",
            "Strengthen Columbian security guarantee",
            "Avoid provoking Cathay",
        ],
        expected_direction="tech-heavy; avoid aggressive sanctions or tariffs",
    ),
    LeaderScenario(
        country_code="solaria",
        country_name="Solaria",
        character_name="Wellspring",
        title="King",
        gdp=1100, gdp_change_pct=3.4, treasury=680, inflation=2.0,
        stability=7.0, political_support=65, war_tiredness=1.5,
        wars=[],
        allies=["columbia"],
        threats=["persia (regional rival)"],
        recent_events=[
            "Signed defense pact renewal with Columbia",
            "Announced Vision-2040 diversification plan",
        ],
        social_pct=1.1, military_coins=4, tech_coins=2,
        sanctions_imposed=[],
        tariffs_imposed=[],
        major_trade_partners=[
            {"country": "cathay", "type": "customer", "volume": "high", "note": "oil buyer"},
            {"country": "columbia", "type": "ally", "volume": "high", "note": "defense deals"},
        ],
        opec_level="normal",
        oil_price=78.0,
        oil_revenue_potential=120.0,
        objectives=[
            "Maximize long-term oil revenue",
            "Counter Persian influence",
            "Diversify economy away from oil",
        ],
        expected_direction="OPEC decision explicit; tech diversification",
    ),
    LeaderScenario(
        country_code="caribe",
        country_name="Caribe",
        character_name="Havana",
        title="Chairman",
        gdp=95, gdp_change_pct=-12.5, treasury=3, inflation=62.0,
        stability=3.2, political_support=41, war_tiredness=2.0,
        wars=[],
        allies=["sarmatia"],
        threats=["columbia (economic blockade)"],
        recent_events=[
            "Currency collapsed 40%",
            "Food riots in two provinces",
        ],
        social_pct=1.3, military_coins=1, tech_coins=0,
        sanctions_imposed=[],
        sanctions_against=[{"target": "caribe", "imposer": "columbia", "level": 3}],
        tariffs_imposed=[],
        major_trade_partners=[
            {"country": "sarmatia", "type": "ally", "volume": "medium", "note": "oil for food"},
        ],
        opec_level="high",
        oil_price=78.0,
        oil_revenue_potential=35.0,
        objectives=[
            "Prevent regime collapse",
            "Secure emergency food imports",
            "Hold minimum social spending",
        ],
        expected_direction="austerity tension; OPEC likely high to grab revenue",
    ),
    LeaderScenario(
        country_code="persia",
        country_name="Persia",
        character_name="Furnace",
        title="Supreme Leader",
        gdp=620, gdp_change_pct=-4.0, treasury=55, inflation=22.0,
        stability=5.0, political_support=54, war_tiredness=5.8,
        wars=["columbia"],
        allies=["sarmatia", "caribe"],
        threats=["columbia (active war)", "levantia"],
        recent_events=[
            "Centrifuge cascade expanded at Natanz",
            "Gulf naval skirmish with Columbia",
        ],
        social_pct=0.85, military_coins=5, tech_coins=3,
        sanctions_imposed=[{"target": "levantia", "level": 2, "note": "proxy conflict"}],
        sanctions_against=[
            {"target": "persia", "imposer": "columbia", "level": 3},
            {"target": "persia", "imposer": "teutonia", "level": 2},
        ],
        tariffs_imposed=[],
        major_trade_partners=[
            {"country": "cathay", "type": "customer", "volume": "high", "note": "discounted oil"},
            {"country": "bharata", "type": "neutral", "volume": "medium"},
        ],
        opec_level="normal",
        oil_price=78.0,
        oil_revenue_potential=90.0,
        objectives=[
            "Achieve nuclear breakout capability",
            "Survive the war with Columbia",
            "Preserve regime legitimacy",
        ],
        expected_direction="military + tech up; OPEC decision explicit during war",
    ),
    LeaderScenario(
        country_code="bharata",
        country_name="Bharata",
        character_name="Scales",
        title="Prime Minister",
        gdp=3400, gdp_change_pct=5.8, treasury=210, inflation=4.2,
        stability=7.5, political_support=62, war_tiredness=0.8,
        wars=[],
        allies=[],
        threats=["cathay (border tensions)"],
        recent_events=[
            "Made In Bharata manufacturing push announced",
            "Purchased S-500 from Sarmatia",
        ],
        social_pct=1.0, military_coins=3, tech_coins=2,
        sanctions_imposed=[],
        tariffs_imposed=[{"target": "cathay", "level": 1, "note": "strategic hedging"}],
        major_trade_partners=[
            {"country": "columbia", "type": "friendly", "volume": "high"},
            {"country": "cathay", "type": "rival", "volume": "high", "note": "border issue"},
            {"country": "sarmatia", "type": "neutral", "volume": "medium", "note": "defense imports"},
        ],
        objectives=[
            "Sustain 6% growth",
            "Maintain non-aligned status",
            "Match Cathay capability along the border",
        ],
        expected_direction="status-quo friendly; modest tweaks",
    ),
    LeaderScenario(
        country_code="teutonia",
        country_name="Teutonia",
        character_name="Forge",
        title="Chancellor",
        gdp=4800, gdp_change_pct=1.2, treasury=260, inflation=3.8,
        stability=8.2, political_support=55, war_tiredness=2.8,
        wars=[],
        allies=["columbia", "albion", "gallia"],
        threats=["sarmatia"],
        recent_events=[
            "Approved Zeitenwende-2 rearmament package",
            "Shut down last nuclear plant",
        ],
        social_pct=1.1, military_coins=3, tech_coins=2,
        sanctions_imposed=[{"target": "sarmatia", "level": 2, "note": "ally coordination"}],
        tariffs_imposed=[],
        major_trade_partners=[
            {"country": "cathay", "type": "customer", "volume": "high", "note": "auto exports"},
            {"country": "columbia", "type": "ally", "volume": "high"},
            {"country": "gallia", "type": "ally", "volume": "high", "note": "EU single market"},
        ],
        objectives=[
            "Lead European strategic autonomy",
            "Support Ruthenia without direct war",
            "Maintain export-led growth",
        ],
        expected_direction="gradual military rise; social maintained",
    ),
]


# ---------------------------------------------------------------------------
# LLM caller
# ---------------------------------------------------------------------------

async def _call_llm(prompt: str, system: str, max_tokens: int = 512) -> str:
    response = await call_llm(
        use_case=LLMUseCase.AGENT_DECISION,
        messages=[{"role": "user", "content": prompt}],
        system=system,
        max_tokens=max_tokens,
        temperature=0.4,
    )
    return response.text.strip()


# ---------------------------------------------------------------------------
# Per-domain runners (async, parallelizable)
# ---------------------------------------------------------------------------

async def _run_budget(s: LeaderScenario) -> dict | None:
    text = await _call_llm(_build_budget_prompt(s), SYSTEM_BUDGET)
    return _parse_json(text)


async def _run_sanctions(s: LeaderScenario) -> dict | None:
    text = await _call_llm(_build_sanctions_prompt(s), SYSTEM_SANCTIONS)
    return _parse_json(text)


async def _run_tariffs(s: LeaderScenario) -> dict | None:
    text = await _call_llm(_build_tariffs_prompt(s), SYSTEM_TARIFFS)
    return _parse_json(text)


async def _run_opec(s: LeaderScenario) -> dict | None:
    text = await _call_llm(_build_opec_prompt(s), SYSTEM_OPEC)
    return _parse_json(text)


async def _run_all_decisions(s: LeaderScenario) -> dict[str, dict | None]:
    """Run all 4 (or 3 for non-OPEC) domain calls concurrently."""
    coros = {
        "budget": _run_budget(s),
        "sanctions": _run_sanctions(s),
        "tariffs": _run_tariffs(s),
    }
    if s.is_opec:
        coros["opec"] = _run_opec(s)

    keys = list(coros.keys())
    results = await asyncio.gather(*coros.values(), return_exceptions=True)
    out: dict[str, dict | None] = {}
    for k, r in zip(keys, results):
        if isinstance(r, Exception):
            logger.warning("%s %s call raised: %s", s.country_code, k, r)
            out[k] = None
        else:
            out[k] = r
    return out


# ---------------------------------------------------------------------------
# Assertion helpers
# ---------------------------------------------------------------------------

def _assert_base_shape(domain: str, parsed: dict | None, cc: str) -> None:
    assert parsed is not None, f"{cc} {domain}: unparseable / null response"
    assert isinstance(parsed, dict), (
        f"{cc} {domain}: expected dict, got {type(parsed).__name__}"
    )
    dec = parsed.get("decision")
    assert dec in VALID_DECISION_VALUES, (
        f"{cc} {domain}: decision must be change|no_change, got {dec!r}"
    )
    rat = parsed.get("rationale", "")
    assert isinstance(rat, str), f"{cc} {domain}: rationale must be string"
    assert len(rat.strip()) >= MIN_RATIONALE_LEN, (
        f"{cc} {domain}: rationale too short ({len(rat.strip())}<{MIN_RATIONALE_LEN}): {rat!r}"
    )


def _assert_budget_payload(parsed: dict, cc: str) -> None:
    if parsed.get("decision") != "change":
        return
    changes = parsed.get("changes")
    assert isinstance(changes, dict), f"{cc} budget: changes must be dict on change"
    if "social_pct" in changes:
        v = float(changes["social_pct"])
        assert 0.5 <= v <= 1.5, f"{cc} budget: social_pct out of range: {v}"
    for k in ("military_coins", "tech_coins"):
        if k in changes:
            v = float(changes[k])
            assert 0 <= v <= 10, f"{cc} budget: {k} out of range: {v}"


def _assert_sanction_or_tariff_payload(domain: str, parsed: dict, cc: str) -> None:
    if parsed.get("decision") != "change":
        return
    changes = parsed.get("changes")
    assert isinstance(changes, list), f"{cc} {domain}: changes must be list on change"
    for entry in changes:
        assert isinstance(entry, dict), f"{cc} {domain}: entry must be dict: {entry}"
        target = entry.get("target")
        assert isinstance(target, str) and target, (
            f"{cc} {domain}: target must be non-empty string: {entry}"
        )
        if "level" in entry:
            lvl = int(entry["level"])
            assert 0 <= lvl <= 3, f"{cc} {domain}: level out of range: {lvl}"
        if "action" in entry:
            assert entry["action"] in {"impose", "lift", "adjust"}, (
                f"{cc} {domain}: invalid action: {entry['action']}"
            )


def _assert_opec_payload(parsed: dict, cc: str) -> None:
    new_level = (parsed.get("new_level") or "").lower().strip()
    assert new_level in VALID_OPEC_LEVELS, (
        f"{cc} opec: new_level invalid: {parsed.get('new_level')!r}"
    )


# ---------------------------------------------------------------------------
# Pretty printer — consolidated per-leader report
# ---------------------------------------------------------------------------

def _print_leader_report(s: LeaderScenario, decisions: dict[str, dict | None]) -> None:
    banner = "=" * 78
    lines = [
        "",
        banner,
        f"LEADER: {s.character_name} ({s.title}) of {s.country_name} [{s.country_code}]",
        banner,
        f"  GDP {s.gdp:.0f} ({s.gdp_change_pct:+.1f}%), treasury {s.treasury:.0f}, "
        f"inflation {s.inflation:.1f}%, stability {s.stability:.1f}/10",
    ]
    if s.wars:
        lines.append(f"  At war with: {', '.join(s.wars)}")
    if s.expected_direction:
        lines.append(f"  Expected direction: {s.expected_direction}")
    lines.append("")

    for domain in ["budget", "sanctions", "tariffs", "opec"]:
        if domain == "opec" and not s.is_opec:
            continue
        parsed = decisions.get(domain)
        if parsed is None:
            lines.append(f"  [{domain.upper():9s}] PARSE FAIL")
            continue
        dec = parsed.get("decision", "?")
        rat = (parsed.get("rationale") or "")[:180]
        lines.append(f"  [{domain.upper():9s}] {dec.upper():9s}  {rat}")
        if dec == "change":
            if domain == "budget":
                lines.append(f"     changes: {parsed.get('changes')}")
            elif domain in ("sanctions", "tariffs"):
                for entry in parsed.get("changes") or []:
                    lines.append(f"     - {entry}")
            elif domain == "opec":
                lines.append(f"     new_level: {parsed.get('new_level')}")
    lines.append(banner)

    report = "\n".join(lines)
    print(report)
    logger.info(report)


def _print_consolidated_table(rows: list[tuple[LeaderScenario, dict[str, dict | None]]]) -> None:
    """Print a compact one-row-per-leader summary table for quick scanning."""
    lines = [
        "",
        "=" * 100,
        "CONSOLIDATED MANDATORY DECISIONS TABLE",
        "=" * 100,
        f"{'Leader':<14} {'D1 Budget':<14} {'D2 Sanctions':<14} {'D3 Tariffs':<14} {'D4 OPEC':<14}",
        "-" * 100,
    ]
    for s, dec_map in rows:
        cells = []
        for domain in ["budget", "sanctions", "tariffs", "opec"]:
            if domain == "opec" and not s.is_opec:
                cells.append("n/a")
                continue
            parsed = dec_map.get(domain)
            if parsed is None:
                cells.append("FAIL")
            else:
                cells.append(parsed.get("decision", "?"))
        lines.append(
            f"{s.country_code:<14} {cells[0]:<14} {cells[1]:<14} {cells[2]:<14} {cells[3]:<14}"
        )
    lines.append("=" * 100)
    report = "\n".join(lines)
    print(report)
    logger.info(report)


# ---------------------------------------------------------------------------
# Parametrized LLM tests — one per (leader, domain) combination
# ---------------------------------------------------------------------------

# Cache per-leader results across the parametrized test calls for the same
# scenario. The session-scoped fixture runs all 3-4 domain calls once per
# leader and shares the results with each domain-specific test.

@pytest.fixture(scope="session")
def decision_cache() -> dict[str, dict[str, dict | None]]:
    return {}


def _get_leader_decisions(
    cache: dict[str, dict[str, dict | None]], scenario: LeaderScenario
) -> dict[str, dict | None]:
    if scenario.country_code not in cache:
        cache[scenario.country_code] = asyncio.run(_run_all_decisions(scenario))
        _print_leader_report(scenario, cache[scenario.country_code])
    return cache[scenario.country_code]


@pytest.mark.llm
@pytest.mark.parametrize("scenario", SCENARIOS, ids=[s.country_code for s in SCENARIOS])
def test_d1_budget(scenario: LeaderScenario, decision_cache) -> None:
    """D1 — Budget decision: explicit, rationaled, in-range."""
    decisions = _get_leader_decisions(decision_cache, scenario)
    parsed = decisions.get("budget")
    _assert_base_shape("budget", parsed, scenario.country_code)
    _assert_budget_payload(parsed, scenario.country_code)


@pytest.mark.llm
@pytest.mark.parametrize("scenario", SCENARIOS, ids=[s.country_code for s in SCENARIOS])
def test_d2_sanctions(scenario: LeaderScenario, decision_cache) -> None:
    """D2 — Sanctions decision: explicit, rationaled, valid targets."""
    decisions = _get_leader_decisions(decision_cache, scenario)
    parsed = decisions.get("sanctions")
    _assert_base_shape("sanctions", parsed, scenario.country_code)
    _assert_sanction_or_tariff_payload("sanctions", parsed, scenario.country_code)


@pytest.mark.llm
@pytest.mark.parametrize("scenario", SCENARIOS, ids=[s.country_code for s in SCENARIOS])
def test_d3_tariffs(scenario: LeaderScenario, decision_cache) -> None:
    """D3 — Tariffs decision: explicit, rationaled, valid targets."""
    decisions = _get_leader_decisions(decision_cache, scenario)
    parsed = decisions.get("tariffs")
    _assert_base_shape("tariffs", parsed, scenario.country_code)
    _assert_sanction_or_tariff_payload("tariffs", parsed, scenario.country_code)


OPEC_SCENARIOS = [s for s in SCENARIOS if s.is_opec]


@pytest.mark.llm
@pytest.mark.parametrize(
    "scenario", OPEC_SCENARIOS, ids=[s.country_code for s in OPEC_SCENARIOS]
)
def test_d4_opec(scenario: LeaderScenario, decision_cache) -> None:
    """D4 — OPEC decision (members only): explicit, rationaled, valid level."""
    decisions = _get_leader_decisions(decision_cache, scenario)
    parsed = decisions.get("opec")
    _assert_base_shape("opec", parsed, scenario.country_code)
    _assert_opec_payload(parsed, scenario.country_code)


@pytest.mark.llm
def test_consolidated_report(decision_cache) -> None:
    """Emit the consolidated table once all per-leader calls have cached.

    Depends on no specific assertion — just produces the summary artifact for
    Marat's review. Run order is irrelevant because per-leader calls are cached
    lazily on first access.
    """
    rows = []
    for s in SCENARIOS:
        decisions = _get_leader_decisions(decision_cache, s)
        rows.append((s, decisions))
    _print_consolidated_table(rows)


# ---------------------------------------------------------------------------
# Offline structural tests (no LLM) — verify prompt builders
# ---------------------------------------------------------------------------

def test_budget_prompt_has_economic_focus_only():
    """D1 prompt: economic state visible; sanctions/tariffs/OPEC NOT addressed as sections."""
    s = SCENARIOS[0]  # columbia
    p = _build_budget_prompt(s)
    assert "BUDGET REVIEW" in p
    assert "Economic state" in p
    assert "GDP" in p
    assert "social_pct" in p
    # Budget prompt should not include other domain section headers
    assert "SANCTIONS committee" not in p
    assert "TRADE AND TARIFF REVIEW" not in p
    assert "OPEC PRODUCTION REVIEW" not in p


def test_sanctions_prompt_has_relationships_focus():
    """D2 prompt: relationships/wars visible; no budget allocation numbers pushed as primary."""
    s = next(x for x in SCENARIOS if x.sanctions_imposed)
    p = _build_sanctions_prompt(s)
    assert "SANCTIONS REVIEW" in p
    assert "Relationships and threats" in p
    assert "Sanctions you currently impose" in p
    assert "Sanctions currently imposed against you" in p
    assert "BUDGET REVIEW" not in p


def test_tariffs_prompt_has_trade_focus():
    """D3 prompt: trade partners visible."""
    s = next(x for x in SCENARIOS if x.major_trade_partners)
    p = _build_tariffs_prompt(s)
    assert "TRADE AND TARIFF REVIEW" in p
    assert "Major trade partners" in p
    assert "Tariffs you currently impose" in p


def test_opec_prompt_only_for_members():
    """D4 prompt: only valid for OPEC members; raises assertion for others."""
    member = next(x for x in SCENARIOS if x.is_opec)
    non_member = next(x for x in SCENARIOS if not x.is_opec)

    p = _build_opec_prompt(member)
    assert "OPEC PRODUCTION REVIEW" in p
    assert "oil price" in p.lower()

    with pytest.raises(AssertionError):
        _build_opec_prompt(non_member)


def test_all_ten_scenarios_present():
    """Ensure the test roster covers all 10 required leaders."""
    expected = {
        "columbia", "cathay", "sarmatia", "ruthenia", "formosa",
        "solaria", "caribe", "persia", "bharata", "teutonia",
    }
    got = {s.country_code for s in SCENARIOS}
    assert got == expected, f"roster drift: missing={expected - got}, extra={got - expected}"


def test_opec_roster_matches_members():
    """OPEC scenarios must align with OPEC_MEMBERS from production source."""
    scenario_opec = {s.country_code for s in SCENARIOS if s.is_opec}
    # Every OPEC scenario must be an actual OPEC member
    for cc in scenario_opec:
        assert cc in OPEC_MEMBERS, f"{cc} marked is_opec but not in OPEC_MEMBERS"
    # Solaria, Persia, Caribe are explicitly in the test roster as OPEC
    assert {"solaria", "persia", "caribe"}.issubset(scenario_opec)
