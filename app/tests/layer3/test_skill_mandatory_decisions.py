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
from engine.services.budget_validator import (
    REQUIRED_PRODUCTION_BRANCHES,
    validate_budget_decision,
)
from engine.services.sanction_validator import validate_sanctions_decision
from engine.services.tariff_validator import validate_tariffs_decision
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
    "You are an AI head of state reviewing your sanctions policy per "
    "CONTRACT_SANCTIONS v1.0. Return ONLY JSON matching the set_sanctions "
    "schema. Rationale >= 30 chars mandatory on both change and no_change. "
    "On no_change: OMIT the changes field entirely. "
    "On change: include changes.sanctions as a flat dict of {target: level} "
    "where level is a signed integer in [-3, +3] (positive = sanctioner, "
    "negative = evasion support, 0 = lift)."
)
SYSTEM_TARIFFS = (
    "You are an AI head of state reviewing your trade and tariff policy "
    "per CONTRACT_TARIFFS v1.0. Return ONLY JSON matching the set_tariffs "
    "schema. Rationale >= 30 chars mandatory on both change and no_change. "
    "On no_change: OMIT the changes field entirely. "
    "On change: include changes.tariffs as a flat dict of {target: level}."
)
SYSTEM_OPEC = (
    "You are an AI head of state reviewing OPEC production posture. "
    "Return ONLY JSON. Every field required. Rationale mandatory on both "
    "change and no_change."
)

VALID_OPEC_LEVELS = {"min", "low", "normal", "high", "max"}
VALID_DECISION_VALUES = {"change", "no_change"}
MIN_RATIONALE_LEN = 30  # CONTRACT_BUDGET v1.1 §4: rationale >= 30 chars

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

    # Current economic settings — CONTRACT_BUDGET v1.1
    social_pct: float = 1.0
    # Current per-branch production levels (0..3). All 5 branches always present.
    current_production: dict = field(
        default_factory=lambda: {
            "ground": 1,
            "naval": 1,
            "tactical_air": 1,
            "strategic_missile": 0,
            "air_defense": 0,
        }
    )
    # Standard production capacity — Template data (units/round at level 1).
    # strategic_missile + air_defense are 0 for all countries in v1.1.
    production_capacity: dict = field(
        default_factory=lambda: {
            "ground": 4,
            "naval": 2,
            "tactical_air": 3,
            "strategic_missile": 0,
            "air_defense": 0,
        }
    )
    current_research: dict = field(
        default_factory=lambda: {"nuclear_coins": 0, "ai_coins": 0}
    )

    sanctions_imposed: list[dict] = field(default_factory=list)
    sanctions_against: list[dict] = field(default_factory=list)
    tariffs_imposed: list[dict] = field(default_factory=list)
    tariffs_against: list[dict] = field(default_factory=list)

    # Trade partners (for tariff call)
    major_trade_partners: list[dict] = field(default_factory=list)

    # Country roster summary (for tariff call — top trade partners + all 20)
    country_roster: list[dict] = field(default_factory=list)

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

    cap = s.production_capacity
    lvl = s.current_production
    cap_lines = "\n".join(
        f"  - {b}: cap {cap.get(b, 0)}/round (current level {lvl.get(b, 0)})"
        for b in ("ground", "naval", "tactical_air", "strategic_missile", "air_defense")
    )
    nuc = s.current_research.get("nuclear_coins", 0)
    ai = s.current_research.get("ai_coins", 0)

    return f"""You are {s.character_name}, {s.title} of {s.country_name}.

## D1 — BUDGET REVIEW (Round {ROUND_NUM})

This is the BUDGET meeting per CONTRACT_BUDGET v1.1. Focus only on fiscal
allocation. Do NOT address sanctions, tariffs, or OPEC in this call.

## Economic state
- GDP: {s.gdp:.0f} ({gdp_sign}{s.gdp_change_pct:.1f}% vs last round)
- Treasury: {s.treasury:.0f} coins
- Inflation: {s.inflation:.1f}%
- Stability: {s.stability:.1f}/10
- Political support: {s.political_support:.0f}%
- War tiredness: {s.war_tiredness:.1f}
- {war_line}

## Current budget (last round)
- Social spending slider: {s.social_pct:.2f} x baseline
- Production levels (by branch):
{cap_lines}
- Research allocation: nuclear={nuc} coins, ai={ai} coins

## Production level scale (all 5 branches, 0-3)
- 0 = none (no spending, no units)
- 1 = normal (1x cost, 1x output per capacity)
- 2 = accelerated (2x cost, 2x output — rushed)
- 3 = maximum (4x cost, 3x output — emergency gear, inefficient)

Branch unit costs at level 1: ground 3, naval 6, tac_air 5, strat_missile 8,
air_defense 4 (coins per unit). Strategic missile and air defense currently
have capacity 0 for all countries — setting levels is accepted but produces 0
units until capacity is raised.

## Social slider
Continuous range [0.5, 1.5]. Effects linear on deviation from 1.0:
- stability delta = (social_pct - 1.0) × 4
- political support delta = (social_pct - 1.0) × 6

## Research
Direct coin allocation. Progress = (coins/GDP) × 0.8 per round. Over-spending
feeds the deficit cascade (treasury → money printing → inflation).

## Your relevant objectives
{_objectives_block(s.objectives)}

## INSTRUCTIONS
Decide whether to CHANGE the budget or keep it NO_CHANGE. Either way you MUST
provide a rationale of at least 30 characters explaining WHY.

Respond with JSON ONLY, matching this EXACT schema (CONTRACT_BUDGET v1.1 §2):

{{
  "action_type": "set_budget",
  "country_code": "{s.country_code}",
  "round_num": {ROUND_NUM},
  "decision": "change",
  "rationale": "string, >= 30 characters",
  "changes": {{
    "social_pct": 1.0,
    "production": {{
      "ground": 1,
      "naval": 1,
      "tactical_air": 1,
      "strategic_missile": 0,
      "air_defense": 0
    }},
    "research": {{
      "nuclear_coins": 0,
      "ai_coins": 0
    }}
  }}
}}

Rules:
- social_pct: float in [0.5, 1.5]
- production: ALL 5 branches required, each integer in [0, 3]
- research: both nuclear_coins and ai_coins required, integers >= 0
- On decision="no_change", OMIT the "changes" field entirely (do not send
  null, do not send an empty object)
- On decision="change", include the full "changes" object with all fields
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

    # All 20 countries roster — synthetic coalition_coverage hint derived
    # from the scenario's known sanctions_imposed/sanctions_against entries.
    # Real system uses sanction_context.build_sanction_context; this harness
    # emulates the persona layer with hand-crafted data only.
    roster_lines = []
    if s.country_roster:
        for r in s.country_roster:
            coverage_hint = r.get("coalition_coverage", "n/a")
            roster_lines.append(
                f"  {r.get('code', '?'):<12s} GDP {r.get('gdp', '?'):>7} "
                f"  {r.get('sector_profile', 'mixed'):<22s}  "
                f"{r.get('relationship', 'neutral'):<16s}  "
                f"coverage={coverage_hint}"
            )
    roster_block = (
        "\n".join(roster_lines)
        if roster_lines
        else "  (roster data unavailable — use allies/threats lists)"
    )

    # Current sanctions imposed BY me (both signs)
    my_sanc_lines = []
    for entry in s.sanctions_imposed:
        target = entry.get("target", "?")
        level = entry.get("level", "?")
        note = entry.get("note", "")
        suffix = f' — "{note}"' if note else ""
        my_sanc_lines.append(f"  {target}   L{level}{suffix}")
    my_sanc_block = (
        "\n".join(my_sanc_lines)
        if my_sanc_lines
        else "  (none — you currently sanction no one)"
    )

    # Sanctions imposed ON me
    on_me_lines = []
    for entry in s.sanctions_against:
        imposer = entry.get("imposer", "?")
        level = entry.get("level", "?")
        note = entry.get("note", "")
        suffix = f' — "{note}"' if note else ""
        on_me_lines.append(f"  {imposer}   L{level}{suffix}")
    on_me_block = (
        "\n".join(on_me_lines)
        if on_me_lines
        else "  (none — no country currently sanctions you)"
    )

    return f"""You are {s.character_name}, {s.title} of {s.country_name}.

## D2 — SANCTIONS REVIEW (Round {ROUND_NUM})

This is the SANCTIONS committee per CONTRACT_SANCTIONS v1.0. Focus only on
coercive economic measures (and evasion support) against hostile or
strategically relevant countries. Do NOT address budget, tariffs, or OPEC
in this call.

## Economic state
- GDP: {s.gdp:.0f}
- Treasury: {s.treasury:.0f} coins
- Inflation: {s.inflation:.1f}%
- Stability: {s.stability:.1f}/10
- Political support: {s.political_support:.0f}%

## Relationships and threats
- {war_line}
- {allies_line}
- {threats_line}

## ALL 20 COUNTRIES (the full roster — anyone is a possible target)

  code          GDP    sector profile          relationship       coverage-hint
  ----         ----    ------------------      ------------       -------------
{roster_block}

## CURRENT SANCTIONS — IMPOSED BY ME (you can change these)
{my_sanc_block}

## CURRENT SANCTIONS — IMPOSED ON ME (informational only — you cannot change these)
{on_me_block}

## HOW SANCTIONS WORK (mechanically)
- Levels are signed integers in [-3, +3]. Positive = active sanctioner.
  Negative = evasion support (buying discounted exports, workarounds).
- Coverage = sum over all actors of (actor_gdp_share x level/3), clamped [0,1].
  Evasion can cancel a coalition but cannot produce a GDP bonus.
- Effectiveness = S-curve(coverage). Flat below 0.4, steep tipping point at
  0.5 - 0.6, saturates near 1.0. SOLO ACTION IS NOISE; COALITIONS MATTER.
- Per-target damage ceiling derived from sector mix:
    max_damage = tec x 0.25 + svc x 0.25 + ind x 0.125 + res x 0.05
  (tech/services economies up to ~22%; resource economies ~13%)
- Setting a target to 0 LIFTS any existing sanction (or evasion support).
- Untouched targets keep their previous level (carry-forward).
- No imposer cost, no evasion benefit — you do not pay a mechanical fee.

## DECISION RULES
- decision="change"    -> must include changes.sanctions with >=1 (target, level) entry
- decision="no_change" -> must OMIT the changes field entirely
- rationale >=30 chars REQUIRED in both cases
- self-sanction and unknown-target are validation errors
- levels must be integers in the signed range [-3, +3]

REMINDER — no_change is a legitimate choice. Sanctions are a possibility,
not an obligation. If your current posture still serves your goals,
no_change is the right answer with a clear rationale. Do not churn sanctions
for the sake of action.

## Your relevant objectives
{_objectives_block(s.objectives)}

## INSTRUCTIONS
Decide whether to CHANGE your sanctions posture or keep it NO_CHANGE.
Either way you MUST provide a rationale of at least 30 characters explaining WHY.

Respond with JSON ONLY, matching this EXACT schema (CONTRACT_SANCTIONS v1.0 §2):

{{
  "action_type": "set_sanctions",
  "country_code": "{s.country_code}",
  "round_num": {ROUND_NUM},
  "decision": "change",
  "rationale": "string, >= 30 characters",
  "changes": {{
    "sanctions": {{
      "target_country": 3
    }}
  }}
}}

Rules:
- changes.sanctions is a flat dict mapping target country code to signed int [-3, +3]
- It is SPARSE — only include targets you want to CHANGE this round
- On decision="no_change", OMIT the "changes" field entirely (do not send null)
- On decision="change", include "changes" with a "sanctions" dict with at least 1 entry
"""


# ---------------------------------------------------------------------------
# D3: Tariffs prompt — trade partners focus
# ---------------------------------------------------------------------------

def _build_tariffs_prompt(s: LeaderScenario) -> str:
    # Country roster — all 19 other countries
    roster_lines = []
    if s.country_roster:
        for r in s.country_roster:
            roster_lines.append(
                f"  {r.get('code', '?'):<12s} GDP {r.get('gdp', '?'):>7} "
                f"  {r.get('sector_profile', 'mixed'):<22s}  "
                f"{r.get('relationship', 'neutral'):<16s}  #{r.get('trade_rank', '?')}"
            )
    if not roster_lines:
        # Fallback — build minimal roster from major_trade_partners
        for p in s.major_trade_partners:
            roster_lines.append(
                f"  {p.get('country', '?'):<12s}  {p.get('type', 'trade'):<16s} "
                f"(volume {p.get('volume', '?')})"
            )
    roster_block = "\n".join(roster_lines) if roster_lines else "  (roster data unavailable)"

    # Tariffs I impose
    my_tariffs_lines = []
    for t in s.tariffs_imposed:
        tgt = t.get("target", "?")
        lvl = t.get("level", "?")
        note = t.get("note", "")
        suffix = f' — "{note}"' if note else ""
        my_tariffs_lines.append(f"  {tgt}   L{lvl}{suffix}")
    my_tariffs_block = "\n".join(my_tariffs_lines) if my_tariffs_lines else "  (none — you currently impose no tariffs)"

    # Tariffs on me
    on_me_lines = []
    for t in s.tariffs_against:
        imp = t.get("imposer", "?")
        lvl = t.get("level", "?")
        note = t.get("note", "")
        suffix = f' — "{note}"' if note else ""
        on_me_lines.append(f"  {imp}   L{lvl}{suffix}")
    on_me_block = "\n".join(on_me_lines) if on_me_lines else "  (none — no country currently tariffs you)"

    return f"""You are {s.character_name}, {s.title} of {s.country_name}.

## D3 — TRADE AND TARIFF REVIEW (Round {ROUND_NUM})

This is the TRADE POLICY review per CONTRACT_TARIFFS v1.0. Focus only on
tariffs and trade posture. Do NOT address budget, sanctions, or OPEC here.

## Economic state
- GDP: {s.gdp:.0f}
- Treasury: {s.treasury:.0f} coins
- Inflation: {s.inflation:.1f}%
- Stability: {s.stability:.1f}/10
- Political support: {s.political_support:.0f}%

## ALL 20 COUNTRIES (the full roster — anyone is a possible target)

  code          GDP    sector profile          relationship        trade-rank
  ----         ----    ------------------      ------------        ----------
{roster_block}

## CURRENT TARIFFS — IMPOSED BY ME (you can change these)
{my_tariffs_block}

## CURRENT TARIFFS — IMPOSED ON ME (informational only — you cannot change these)
{on_me_block}

## HOW TARIFFS WORK (mechanically)
- Bilateral. Set a level (0-3) for any subset of the other 19 countries.
- Levels: 0 = none / lift, 1 = light, 2 = moderate, 3 = heavy / near-embargo.
- As imposer you get: customs revenue + small self-damage + inflation pressure.
- As target you get: GDP hit proportional to imposer's market share.
- Setting a target to 0 LIFTS the tariff. No separate "lift" action.
- Untouched targets keep their previous level (carry-forward).

## DECISION RULES
- decision="change"    -> must include changes.tariffs with >=1 (target, level) entry
- decision="no_change" -> must OMIT the changes field entirely
- rationale >=30 chars REQUIRED in both cases
- self-tariff and unknown-target are validation errors

REMINDER — no_change is a legitimate choice. If your current posture still
serves your goals, no_change is the right answer with a clear rationale.
Do not invent changes for the sake of action.

## Your relevant objectives
{_objectives_block(s.objectives)}

## INSTRUCTIONS
Decide whether to CHANGE your tariff posture or keep it NO_CHANGE.
Either way you MUST provide a rationale of at least 30 characters explaining WHY.

Respond with JSON ONLY, matching this EXACT schema (CONTRACT_TARIFFS v1.0 §2):

{{
  "action_type": "set_tariffs",
  "country_code": "{s.country_code}",
  "round_num": {ROUND_NUM},
  "decision": "change",
  "rationale": "string, >= 30 characters",
  "changes": {{
    "tariffs": {{
      "target_country": 2
    }}
  }}
}}

Rules:
- changes.tariffs is a flat dict mapping target country code to integer level (0-3)
- It is SPARSE — only include targets you want to CHANGE this round
- On decision="no_change", OMIT the "changes" field entirely (do not send null)
- On decision="change", include "changes" with a "tariffs" dict with at least 1 entry
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
        social_pct=1.0,
        current_production={"ground": 2, "naval": 1, "tactical_air": 2, "strategic_missile": 0, "air_defense": 0},
        production_capacity={"ground": 5, "naval": 4, "tactical_air": 5, "strategic_missile": 0, "air_defense": 0},
        current_research={"nuclear_coins": 0, "ai_coins": 6},
        sanctions_imposed=[{"target": "persia", "level": 3, "note": "wartime"}],
        tariffs_imposed=[
            {"target": "cathay", "level": 2, "note": "ongoing trade war"},
            {"target": "sarmatia", "level": 2, "note": "sanctions-aligned"},
            {"target": "caribe", "level": 3, "note": "energy blockade"},
        ],
        tariffs_against=[
            {"imposer": "cathay", "level": 2, "note": "retaliatory"},
            {"imposer": "caribe", "level": 1, "note": "counter-sanctions symbolic"},
            {"imposer": "persia", "level": 2, "note": "counter-sanctions"},
        ],
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
        social_pct=0.9,
        current_production={"ground": 1, "naval": 2, "tactical_air": 1, "strategic_missile": 0, "air_defense": 0},
        production_capacity={"ground": 5, "naval": 3, "tactical_air": 4, "strategic_missile": 0, "air_defense": 0},
        current_research={"nuclear_coins": 0, "ai_coins": 10},
        sanctions_imposed=[],
        tariffs_imposed=[{"target": "columbia", "level": 2, "note": "retaliatory"}],
        tariffs_against=[
            {"imposer": "columbia", "level": 2, "note": "ongoing trade war"},
            {"imposer": "bharata", "level": 1, "note": "strategic hedging"},
        ],
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
        social_pct=0.8,
        current_production={"ground": 3, "naval": 1, "tactical_air": 2, "strategic_missile": 0, "air_defense": 0},
        production_capacity={"ground": 4, "naval": 2, "tactical_air": 3, "strategic_missile": 0, "air_defense": 0},
        current_research={"nuclear_coins": 3, "ai_coins": 0},
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
        social_pct=0.7,
        current_production={"ground": 3, "naval": 0, "tactical_air": 2, "strategic_missile": 0, "air_defense": 0},
        production_capacity={"ground": 3, "naval": 1, "tactical_air": 2, "strategic_missile": 0, "air_defense": 0},
        current_research={"nuclear_coins": 0, "ai_coins": 0},
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
        social_pct=1.0,
        current_production={"ground": 1, "naval": 1, "tactical_air": 1, "strategic_missile": 0, "air_defense": 0},
        production_capacity={"ground": 2, "naval": 1, "tactical_air": 2, "strategic_missile": 0, "air_defense": 0},
        current_research={"nuclear_coins": 0, "ai_coins": 8},
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
        social_pct=1.1,
        current_production={"ground": 1, "naval": 1, "tactical_air": 2, "strategic_missile": 0, "air_defense": 0},
        production_capacity={"ground": 3, "naval": 2, "tactical_air": 3, "strategic_missile": 0, "air_defense": 0},
        current_research={"nuclear_coins": 0, "ai_coins": 3},
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
        social_pct=1.3,
        current_production={"ground": 1, "naval": 0, "tactical_air": 0, "strategic_missile": 0, "air_defense": 0},
        production_capacity={"ground": 1, "naval": 0, "tactical_air": 0, "strategic_missile": 0, "air_defense": 0},
        current_research={"nuclear_coins": 0, "ai_coins": 0},
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
        social_pct=0.85,
        current_production={"ground": 2, "naval": 1, "tactical_air": 2, "strategic_missile": 0, "air_defense": 0},
        production_capacity={"ground": 3, "naval": 1, "tactical_air": 2, "strategic_missile": 0, "air_defense": 0},
        current_research={"nuclear_coins": 5, "ai_coins": 0},
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
        social_pct=1.0,
        current_production={"ground": 1, "naval": 1, "tactical_air": 1, "strategic_missile": 0, "air_defense": 0},
        production_capacity={"ground": 4, "naval": 2, "tactical_air": 3, "strategic_missile": 0, "air_defense": 0},
        current_research={"nuclear_coins": 2, "ai_coins": 2},
        sanctions_imposed=[],
        tariffs_imposed=[{"target": "cathay", "level": 1, "note": "strategic hedging"}],
        tariffs_against=[],
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
        social_pct=1.1,
        current_production={"ground": 1, "naval": 1, "tactical_air": 1, "strategic_missile": 0, "air_defense": 0},
        production_capacity={"ground": 3, "naval": 2, "tactical_air": 3, "strategic_missile": 0, "air_defense": 0},
        current_research={"nuclear_coins": 0, "ai_coins": 4},
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
    """Full CONTRACT_BUDGET v1.1 validation via the production validator.

    The harness auto-fills action_type/country_code/round_num if the LLM
    omitted them — these are envelope fields the communication layer would
    normally inject, not decision content.
    """
    payload = dict(parsed)
    payload.setdefault("action_type", "set_budget")
    payload.setdefault("country_code", cc)
    payload.setdefault("round_num", ROUND_NUM)

    report = validate_budget_decision(payload)
    assert report["valid"], (
        f"{cc} budget: validator rejected decision: {report['errors']}\n"
        f"payload: {payload}"
    )


def _assert_sanctions_payload(parsed: dict, cc: str) -> None:
    """D2 sanctions: full CONTRACT_SANCTIONS v1.0 validation via production validator.

    The harness auto-fills action_type/country_code/round_num if the LLM
    omitted them — these are envelope fields the communication layer would
    normally inject, not decision content.
    """
    payload = dict(parsed)
    payload.setdefault("action_type", "set_sanctions")
    payload.setdefault("country_code", cc)
    payload.setdefault("round_num", ROUND_NUM)

    report = validate_sanctions_decision(payload)
    assert report["valid"], (
        f"{cc} sanctions: validator rejected decision: {report['errors']}\n"
        f"payload: {payload}"
    )


def _assert_tariff_payload(parsed: dict, cc: str) -> None:
    """D3 tariffs: full CONTRACT_TARIFFS v1.0 validation via production validator.

    The harness auto-fills action_type/country_code/round_num if the LLM
    omitted them — these are envelope fields the communication layer would
    normally inject, not decision content.
    """
    payload = dict(parsed)
    payload.setdefault("action_type", "set_tariffs")
    payload.setdefault("country_code", cc)
    payload.setdefault("round_num", ROUND_NUM)

    report = validate_tariffs_decision(payload)
    assert report["valid"], (
        f"{cc} tariffs: validator rejected decision: {report['errors']}\n"
        f"payload: {payload}"
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
    _assert_sanctions_payload(parsed, scenario.country_code)


@pytest.mark.llm
@pytest.mark.parametrize("scenario", SCENARIOS, ids=[s.country_code for s in SCENARIOS])
def test_d3_tariffs(scenario: LeaderScenario, decision_cache) -> None:
    """D3 — Tariffs decision: explicit, rationaled, valid targets."""
    decisions = _get_leader_decisions(decision_cache, scenario)
    parsed = decisions.get("tariffs")
    _assert_base_shape("tariffs", parsed, scenario.country_code)
    _assert_tariff_payload(parsed, scenario.country_code)


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
    # CONTRACT_BUDGET v1.1 schema markers — prompt must teach the new shape
    assert "CONTRACT_BUDGET v1.1" in p
    for branch in REQUIRED_PRODUCTION_BRANCHES:
        assert branch in p, f"budget prompt missing branch {branch}"
    assert "nuclear_coins" in p
    assert "ai_coins" in p
    assert '"action_type": "set_budget"' in p
    # Old schema must not leak
    assert "military_coins" not in p
    assert "tech_coins" not in p
    # Budget prompt should not include other domain section headers
    assert "SANCTIONS committee" not in p
    assert "TRADE AND TARIFF REVIEW" not in p
    assert "OPEC PRODUCTION REVIEW" not in p


def test_sanctions_prompt_has_relationships_focus():
    """D2 prompt: CONTRACT_SANCTIONS v1.0 schema — roster, both directions, signed levels."""
    s = next(x for x in SCENARIOS if x.sanctions_imposed)
    p = _build_sanctions_prompt(s)
    assert "SANCTIONS REVIEW" in p
    assert "CONTRACT_SANCTIONS v1.0" in p
    assert "Relationships and threats" in p
    assert "IMPOSED BY ME" in p
    assert "IMPOSED ON ME" in p
    assert '"action_type": "set_sanctions"' in p
    # Signed level range + evasion support
    assert "-3" in p and "+3" in p
    assert "evasion" in p.lower()
    # no_change reminder
    assert "no_change" in p
    assert "legitimate" in p.lower()
    # Coverage and tipping point
    assert "coverage" in p.lower() or "Coverage" in p
    # Schema teaches sparse dict, not legacy list-of-dicts
    assert '"sanctions"' in p
    assert "impose|lift|adjust" not in p  # legacy format must not leak
    assert "BUDGET REVIEW" not in p
    assert "TRADE AND TARIFF REVIEW" not in p


def test_tariffs_prompt_has_trade_focus():
    """D3 prompt: CONTRACT_TARIFFS v1.0 schema — roster, both tariff directions, decision rules."""
    s = next(x for x in SCENARIOS if x.tariffs_imposed)
    p = _build_tariffs_prompt(s)
    assert "TRADE AND TARIFF REVIEW" in p
    assert "CONTRACT_TARIFFS v1.0" in p
    assert "IMPOSED BY ME" in p
    assert "IMPOSED ON ME" in p
    assert "no_change" in p
    assert '"action_type": "set_tariffs"' in p
    assert "changes" in p
    assert "tariffs" in p
    # Schema teaches sparse dict, not list of entries
    assert "target_country" in p
    # Decision rules present
    assert "carry-forward" in p
    assert "legitimate" in p.lower()


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
