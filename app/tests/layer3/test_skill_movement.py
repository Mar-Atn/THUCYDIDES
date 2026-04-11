"""L3 skill harness for the move_units mandatory decision (CONTRACT_MOVEMENT v1.0).

D5 in the mandatory-decision sequence (after D1 budget, D2 sanctions,
D3 tariffs, D4 OPEC). This file is intentionally separate from
``test_skill_mandatory_decisions.py`` to keep movement isolated — the
movement decision context is structurally larger and the prompt is more
complex.

Offline tests verify the prompt has the v1.0 schema markers and the
real production validator (``validate_movement_decision``) accepts a
hand-crafted reference payload. The full LLM acceptance gate lives in
``test_movement_full_chain_ai.py``.

Run::

    cd app && PYTHONPATH=. python3 -m pytest tests/layer3/test_skill_movement.py -v
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field

import pytest

from engine.agents.decisions import _parse_json
from engine.config.settings import LLMUseCase
from engine.services.llm import call_llm
from engine.services.movement_validator import (
    RATIONALE_MIN_CHARS,
    validate_movement_decision,
)

logger = logging.getLogger(__name__)

SYSTEM_MOVEMENT = (
    "You are an AI head of state reviewing your military deployment per "
    "CONTRACT_MOVEMENT v1.0. Return ONLY JSON matching the move_units "
    "schema. Rationale >= 30 chars mandatory on both change and no_change. "
    "On no_change: OMIT the changes field entirely. "
    "On change: include changes.moves as a list of move objects."
)

MOVEMENT_ROUND_NUM = 200


# ---------------------------------------------------------------------------
# Minimal scenario for the movement skill harness
# ---------------------------------------------------------------------------

@dataclass
class MovementScenario:
    """A self-contained snapshot of a leader's military situation."""

    country_code: str
    country_name: str
    character_name: str
    title: str

    gdp: float
    treasury: float
    stability: float
    at_war: bool
    war_with: list[str] = field(default_factory=list)

    # Own units (validator-shape)
    units: dict = field(default_factory=dict)
    # Per-hex zone shape: (row,col) -> {owner, type}
    zones: dict = field(default_factory=dict)
    # {country_code -> set[host_country_code]}
    basing_rights: dict = field(default_factory=dict)

    # Hexes I currently occupy (for the prompt's PREVIOUSLY OCCUPIED block)
    occupied_hexes: list[tuple[int, int]] = field(default_factory=list)
    # Hexes I own (for OWN TERRITORY)
    owned_hexes: list[tuple[int, int]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------


def _format_units_block(units: dict) -> str:
    if not units:
        return "  (no units)"
    lines = []
    for code, u in sorted(units.items()):
        pos = (
            f"({u['global_row']}, {u['global_col']})"
            if u.get("global_row") is not None
            else "-"
        )
        emb = u.get("embarked_on") or "-"
        lines.append(
            f"  {code:<14} {u.get('unit_type','?'):<18} "
            f"{u.get('status','?'):<10} {pos:<10} embarked={emb}"
        )
    return "\n".join(lines)


def _build_movement_prompt(s: MovementScenario) -> str:
    """Compose a CONTRACT_MOVEMENT v1.0 prompt for one leader."""
    war_line = (
        f"At war with: {', '.join(s.war_with)}" if s.war_with else "Not at war."
    )

    units_block = _format_units_block(s.units)

    own_block = (
        "\n".join(f"  ({r}, {c})" for (r, c) in s.owned_hexes)
        if s.owned_hexes
        else "  (none)"
    )

    poh_block = (
        "  " + ", ".join(f"({r}, {c})" for (r, c) in s.occupied_hexes)
        if s.occupied_hexes
        else "  (none)"
    )

    grantors = sorted(s.basing_rights.get(s.country_code, set()))
    basing_block = (
        "\n".join(f"  - {g}" for g in grantors) if grantors else "  (none)"
    )

    return f"""You are {s.character_name}, {s.title} of {s.country_name}.

## D5 — MOVEMENT REVIEW (Round {MOVEMENT_ROUND_NUM}) — CONTRACT_MOVEMENT v1.0

This is the MILITARY DEPLOYMENT meeting. Decide how to position your forces
this round. Do NOT address budget, sanctions, tariffs, or OPEC here.

[ECONOMIC STATE]
  GDP:                {s.gdp:.0f}
  Treasury:           {s.treasury:.0f}
  Stability:          {s.stability:.0f}/10
  {war_line}

[MY UNITS]
  unit_code      type               status     position   embarked_on
{units_block}

[OWN TERRITORY] — global hexes I own
{own_block}

[PREVIOUSLY OCCUPIED HEXES] — hexes I have >=1 active unit on (qualify for deploy)
{poh_block}

[BASING RIGHTS I HAVE] — countries that grant me deploy rights
{basing_block}

[DECISION RULES]
HOW MOVEMENT WORKS
- Three use cases per unit: reposition / deploy from reserve / withdraw to reserve
- Two auto-detected flows: embark (onto own naval with capacity) / debark (implicit)
- Range is unlimited; territory rules gate legality
- Moves take effect at the start of the next round

CONSTRAINTS by unit type
- Ground / AD / Strategic Missile: target hex NOT sea; must be own territory,
  basing-rights zone, OR previously occupied hex (>=1 own unit there)
- Tactical Air: same as ground, PLUS can auto-embark on own naval
- Naval: sea hexes ONLY (cannot touch land)
- Carrier capacity: 1 ground + 2 tactical_air per friendly naval

DECISION RULES
- decision="change"    -> MUST include changes.moves with >=1 valid move
- decision="no_change" -> MUST OMIT the changes field entirely
- rationale >=30 chars REQUIRED in both cases

REMINDER -- no_change is a legitimate choice
Movement has real costs: units in transit are committed, withdrawing to
reserve loses a round of availability. If your current deployment serves
your goals, no_change with a clear rationale is the correct answer.

[INSTRUCTION]
Decide whether to CHANGE or NO_CHANGE. Rationale >=30 chars required.
Respond with JSON ONLY, matching CONTRACT_MOVEMENT §2:

{{
  "action_type": "move_units",
  "country_code": "{s.country_code}",
  "round_num": {MOVEMENT_ROUND_NUM},
  "decision": "change" | "no_change",
  "rationale": "string, >= 30 characters",
  "changes": {{
    "moves": [
      {{
        "unit_code": "<one of MY UNITS>",
        "target": "hex",
        "target_global_row": 3,
        "target_global_col": 3
      }}
    ]
  }}
}}

Rules:
- On "change": include "changes" with "moves" list (>=1 entry).
- Each move: unit_code (string), target ("hex" or "reserve"). For "hex"
  targets, include target_global_row + target_global_col integers.
- On "no_change": OMIT the "changes" field entirely (do not send null).
"""


# ---------------------------------------------------------------------------
# Assertion helper
# ---------------------------------------------------------------------------


def _assert_movement_payload(
    parsed: dict,
    cc: str,
    units: dict,
    zones: dict,
    basing_rights: dict,
) -> None:
    """Run the production validator against an LLM/test parsed payload."""
    payload = dict(parsed)
    payload.setdefault("action_type", "move_units")
    payload.setdefault("country_code", cc)
    payload.setdefault("round_num", MOVEMENT_ROUND_NUM)

    report = validate_movement_decision(payload, units, zones, basing_rights)
    assert report["valid"], (
        f"{cc} movement: validator rejected decision: {report['errors']}\n"
        f"payload: {payload}"
    )


# ---------------------------------------------------------------------------
# Reference fixture
# ---------------------------------------------------------------------------


def _columbia_reference() -> MovementScenario:
    """Hard-coded snapshot of Columbia's situation matching seed_data."""
    units = {
        "col_g_04": {
            "unit_code": "col_g_04", "country_code": "columbia",
            "unit_type": "ground", "status": "reserve",
            "global_row": None, "global_col": None,
            "theater": None, "embarked_on": None,
        },
        "col_g_05": {
            "unit_code": "col_g_05", "country_code": "columbia",
            "unit_type": "ground", "status": "reserve",
            "global_row": None, "global_col": None,
            "theater": None, "embarked_on": None,
        },
        "col_m_01": {
            "unit_code": "col_m_01", "country_code": "columbia",
            "unit_type": "strategic_missile", "status": "active",
            "global_row": 3, "global_col": 3,
            "theater": None, "embarked_on": None,
        },
    }
    zones = {
        (3, 3): {
            "id": "columbia_3_3", "global_row": 3, "global_col": 3,
            "owner": "columbia", "controlled_by": "columbia", "type": "land",
        },
        (4, 3): {
            "id": "columbia_4_3", "global_row": 4, "global_col": 3,
            "owner": "columbia", "controlled_by": "columbia", "type": "land",
        },
    }
    return MovementScenario(
        country_code="columbia",
        country_name="Columbia",
        character_name="Dealer",
        title="President",
        gdp=28000.0,
        treasury=320.0,
        stability=7.0,
        at_war=False,
        war_with=[],
        units=units,
        zones=zones,
        basing_rights={},
        occupied_hexes=[(3, 3)],
        owned_hexes=[(3, 3), (4, 3)],
    )


# ---------------------------------------------------------------------------
# Offline structural tests (no LLM)
# ---------------------------------------------------------------------------


def test_movement_prompt_has_v1_schema_markers():
    """D5 prompt: CONTRACT_MOVEMENT v1.0 schema markers are present."""
    s = _columbia_reference()
    p = _build_movement_prompt(s)

    assert "MOVEMENT REVIEW" in p
    assert "CONTRACT_MOVEMENT v1.0" in p
    assert '"action_type": "move_units"' in p
    assert '"target"' in p
    assert "target_global_row" in p
    assert "target_global_col" in p
    # no_change reminder
    assert "no_change" in p
    assert "legitimate" in p.lower()
    # rationale length requirement
    assert ">=30" in p or "30 char" in p.lower()
    # legacy schema must NOT leak
    assert '"move_unit"' not in p
    assert "mobilize_reserve" not in p


def test_validator_accepts_reference_change():
    """Hand-crafted change payload validates against the production validator."""
    s = _columbia_reference()
    payload = {
        "action_type": "move_units",
        "country_code": "columbia",
        "round_num": MOVEMENT_ROUND_NUM,
        "decision": "change",
        "rationale": (
            "L3 reference: deploy reserve ground unit col_g_04 to home "
            "territory hex (3, 3) — exercises validator + harness."
        ),
        "changes": {
            "moves": [
                {"unit_code": "col_g_04", "target": "hex",
                 "target_global_row": 3, "target_global_col": 3},
            ],
        },
    }
    _assert_movement_payload(
        payload, "columbia", s.units, s.zones, s.basing_rights,
    )


def test_validator_accepts_reference_no_change():
    s = _columbia_reference()
    payload = {
        "action_type": "move_units",
        "country_code": "columbia",
        "round_num": MOVEMENT_ROUND_NUM,
        "decision": "no_change",
        "rationale": (
            "L3 reference: current deployment serves Columbia's strategic "
            "objectives — no movement needed this round."
        ),
    }
    _assert_movement_payload(
        payload, "columbia", s.units, s.zones, s.basing_rights,
    )


def test_validator_min_rationale_constant():
    """Sanity check the validator's min-rationale constant matches the contract."""
    assert RATIONALE_MIN_CHARS == 30


# ---------------------------------------------------------------------------
# Optional LLM call (gated by -m llm)
# ---------------------------------------------------------------------------


async def _call_llm(prompt: str, system: str, max_tokens: int = 600) -> str:
    response = await call_llm(
        use_case=LLMUseCase.AGENT_DECISION,
        messages=[{"role": "user", "content": prompt}],
        system=system,
        max_tokens=max_tokens,
        temperature=0.4,
    )
    return response.text.strip()


@pytest.mark.llm
def test_columbia_movement_llm() -> None:
    """One-shot smoke LLM call against Columbia's movement skill."""
    s = _columbia_reference()
    prompt = _build_movement_prompt(s)
    text = asyncio.run(_call_llm(prompt, SYSTEM_MOVEMENT))
    parsed = _parse_json(text)
    assert parsed is not None, f"unparseable LLM JSON: {text!r}"
    _assert_movement_payload(
        parsed, "columbia", s.units, s.zones, s.basing_rights,
    )
