"""L3 Skill E1: Unit Deployment Test.

Tests the inter-round RELOCATION skill per AI_CONCEPT.md Section 8.
Between rounds, the orchestrator prompts military chiefs + HoS to
deploy/redeploy troops. This harness checks whether the AI can make
STRATEGIC unit positioning decisions given current positions, round
results, strategic threats, and objectives.

Architecture: domain-specific LLM call with focused context — same
pattern as mandatory decisions v2 and action selection skill tests.

Real LLM calls (~$0.001 each). 6 leader scenarios. Unit state is
SIMULATED in-test (no DB) to keep the harness isolated.

Run:
    cd app && PYTHONPATH=. python3 -m pytest tests/layer3/test_skill_deployment.py -v -s

Skip LLM tests:
    cd app && PYTHONPATH=. python3 -m pytest tests/layer3/test_skill_deployment.py -v -m "not llm"
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

import pytest

from engine.agents.decisions import _parse_json
from engine.services.llm import call_llm
from engine.config.settings import LLMUseCase

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Schema constants
# ---------------------------------------------------------------------------

VALID_DECISIONS = {"deploy", "reposition", "withdraw", "no_change"}
VALID_ORDER_ACTIONS = {
    "deploy_from_reserve",
    "move_active",
    "withdraw_to_reserve",
    "embark",
}
VALID_UNIT_TYPES = {"ground", "naval", "air", "missile", "ad"}


# ---------------------------------------------------------------------------
# Scenario dataclass
# ---------------------------------------------------------------------------

@dataclass
class DeploymentScenario:
    """A test scenario for the E1 unit deployment skill."""
    name: str
    country: str
    leader: str
    role: str  # "HoS" or "military_chief"
    title: str
    # Simulated military state
    active_units: list[dict[str, Any]]        # [{type, count, hex: [r,c], theater}]
    reserve_units: dict[str, int]             # {type: count}
    production_capacity: str                  # narrative
    # Theater summary
    own_territories: list[str]                # hex labels / province names
    allied_neighbors: list[str]
    hostile_neighbors: list[str]
    recent_combat: str                        # narrative of last round's combat
    strategic_objectives: list[str]
    # Expectations (for assertion + printout)
    expected_decisions: set[str]              # acceptable decision values
    rationale_must_mention: list[str] = field(default_factory=list)
    notes: str = ""


# ---------------------------------------------------------------------------
# Six focused scenarios
# ---------------------------------------------------------------------------

SCENARIOS: list[DeploymentScenario] = [
    # 1. Sarmatia — pressing advantage
    DeploymentScenario(
        name="sarmatia_pressing_advantage",
        country="Sarmatia",
        leader="Pathfinder",
        role="HoS",
        title="President",
        active_units=[
            {"type": "ground", "count": 4, "hex": [12, 18], "theater": "Ereb East"},
            {"type": "ground", "count": 3, "hex": [12, 19], "theater": "Ereb East"},
            {"type": "ground", "count": 3, "hex": [13, 18], "theater": "Ereb East"},
            {"type": "air",    "count": 2, "hex": [11, 17], "theater": "Ereb East"},
            {"type": "ad",     "count": 1, "hex": [12, 17], "theater": "Ereb East"},
        ],
        reserve_units={"ground": 5, "air": 1, "missile": 2},
        production_capacity="Moderate — 2 ground + 1 air per round",
        own_territories=["hex (12,17)", "hex (12,18)", "hex (13,18)", "hex (11,17)"],
        allied_neighbors=["Anatolia (non-belligerent)"],
        hostile_neighbors=["Ruthenia (at war, losing ground)"],
        recent_combat=(
            "Advanced into Ruthenian territory, captured 2 hexes. "
            "Lost ~1 ground unit's worth of strength across 3 frontline units. "
            "Ruthenian line is cracking on the southern flank."
        ),
        strategic_objectives=[
            "territorial_control of disputed eastern provinces",
            "win war before international intervention",
            "exploit the southern breakthrough",
        ],
        expected_decisions={"deploy", "reposition"},
        rationale_must_mention=["offens", "advance", "exploit", "breakthrough", "frontline", "press"],
        notes="Should commit reserves or push active units forward.",
    ),
    # 2. Ruthenia — desperate defense
    DeploymentScenario(
        name="ruthenia_desperate_defense",
        country="Ruthenia",
        leader="Guardian",
        role="HoS",
        title="President",
        active_units=[
            {"type": "ground", "count": 2, "hex": [13, 20], "theater": "Ereb East"},
            {"type": "ground", "count": 2, "hex": [14, 20], "theater": "Ereb East"},
            {"type": "ground", "count": 1, "hex": [13, 21], "theater": "Ereb East"},
            {"type": "ad",     "count": 1, "hex": [14, 21], "theater": "Ereb East"},
        ],
        reserve_units={"ground": 2, "missile": 1},
        production_capacity="Low — treasury depleted, 1 ground per round max",
        own_territories=["hex (13,20)", "hex (14,20)", "hex (13,21)", "hex (14,21)", "capital (15,21)"],
        allied_neighbors=["Columbia (arms shipment inbound)", "Teutonia (political support only)"],
        hostile_neighbors=["Sarmatia (at war, advancing)"],
        recent_combat=(
            "Lost 2 hexes last round. Two frontline units destroyed. "
            "Sarmatian breakthrough on southern flank threatens supply lines. "
            "Columbia arms shipment arrives in reserves NEXT round."
        ),
        strategic_objectives=[
            "hold the capital and remaining territory",
            "buy time for Columbia arms to arrive",
            "prevent southern envelopment",
        ],
        expected_decisions={"deploy", "reposition"},
        rationale_must_mention=["defen", "hold", "line", "capital", "flank", "protect"],
        notes="Should commit last reserves; no_change would be negligent.",
    ),
    # 3. Columbia — global power projection, no active homeland combat
    DeploymentScenario(
        name="columbia_global_posture",
        country="Columbia",
        leader="Dealer",
        role="HoS",
        title="President",
        active_units=[
            {"type": "ground", "count": 4, "hex": [20, 10], "theater": "Columbia homeland"},
            {"type": "naval",  "count": 3, "hex": [18, 25], "theater": "Pacific"},
            {"type": "naval",  "count": 2, "hex": [10, 18], "theater": "Ereb West"},
            {"type": "air",    "count": 2, "hex": [11, 19], "theater": "Ereb West"},
            {"type": "ground", "count": 2, "hex": [15, 30], "theater": "Mashriq"},
            {"type": "air",    "count": 1, "hex": [15, 30], "theater": "Mashriq"},
            {"type": "missile", "count": 2, "hex": [20, 10], "theater": "Columbia homeland"},
        ],
        reserve_units={"ground": 6, "naval": 2, "air": 3, "missile": 4},
        production_capacity="High — 3 ground + 2 air + 1 naval per round",
        own_territories=["Columbia homeland (multiple hexes)"],
        allied_neighbors=["Teutonia", "Formosa", "Solaria (friendly)"],
        hostile_neighbors=["Persia (at war, distant)"],
        recent_combat=(
            "Mashriq: Persia strike forces engaged, moderate losses on Columbian air wing. "
            "Pacific/Ereb theaters quiet. Homeland stable."
        ),
        strategic_objectives=[
            "project power globally without overextension",
            "reinforce Mashriq for Persia war",
            "maintain deterrence across Pacific and Ereb",
        ],
        expected_decisions={"deploy", "reposition", "no_change"},
        rationale_must_mention=["theater", "Mashriq", "Persia", "Pacific", "Ereb", "project", "reinforce", "global"],
        notes="Any decision is acceptable; rationale must reflect theater logic.",
    ),
    # 4. Formosa — pure defense, Cathay pressure
    DeploymentScenario(
        name="formosa_pure_defense",
        country="Formosa",
        leader="Islander",
        role="HoS",
        title="President",
        active_units=[
            {"type": "ground", "count": 2, "hex": [22, 28], "theater": "Pacific"},
            {"type": "naval",  "count": 1, "hex": [22, 29], "theater": "Pacific"},
            {"type": "air",    "count": 1, "hex": [22, 28], "theater": "Pacific"},
            {"type": "ad",     "count": 2, "hex": [22, 28], "theater": "Pacific"},
        ],
        reserve_units={"ground": 1, "missile": 1},
        production_capacity="Low — small industrial base, 1 unit per round",
        own_territories=["Formosa main island (22,28)", "outlying island (22,29)"],
        allied_neighbors=["Columbia (naval task force nearby, offering embark slots)"],
        hostile_neighbors=["Cathay (hostile, naval exercises intensifying)"],
        recent_combat=(
            "No active combat. Cathay naval drills within 2 hexes. "
            "Columbia Pacific fleet has offered to host Formosan marines for joint posture."
        ),
        strategic_objectives=[
            "deter Cathay invasion",
            "coordinate defense with Columbia ally",
            "preserve strategic depth on main island",
        ],
        expected_decisions={"deploy", "reposition", "no_change"},
        rationale_must_mention=["defen", "Columbia", "coordin", "ally", "Cathay", "deter", "hold"],
        notes="Embark on Columbia naval is a valid reading; consolidation also fine.",
    ),
    # 5. Cathay — not at war but preparing
    DeploymentScenario(
        name="cathay_preparing",
        country="Cathay",
        leader="Helmsman",
        role="HoS",
        title="President",
        active_units=[
            {"type": "ground", "count": 6, "hex": [21, 26], "theater": "Cathay homeland"},
            {"type": "naval",  "count": 4, "hex": [22, 27], "theater": "Pacific"},
            {"type": "air",    "count": 3, "hex": [21, 27], "theater": "Pacific"},
            {"type": "missile", "count": 3, "hex": [21, 26], "theater": "Cathay homeland"},
            {"type": "ad",     "count": 2, "hex": [21, 26], "theater": "Cathay homeland"},
        ],
        reserve_units={"ground": 4, "naval": 2, "air": 2, "missile": 2},
        production_capacity="High — 2 ground + 2 naval + 1 air per round",
        own_territories=["Cathay homeland (multiple hexes)"],
        allied_neighbors=["Persia (friendly)"],
        hostile_neighbors=["Formosa (tension, no war)"],
        recent_combat=(
            "No combat. Conducted naval exercises near Formosa — no contact. "
            "Fleet readiness improved; ground forces conducted amphibious training."
        ),
        strategic_objectives=[
            "maintain readiness for Formosa contingency",
            "avoid provoking Columbia intervention",
            "consolidate Pacific naval dominance",
        ],
        expected_decisions={"reposition", "no_change", "deploy"},
        rationale_must_mention=["Formosa", "Pacific", "ready", "posture", "train", "consolid", "naval"],
        notes="Reposition toward Formosa staging or training consolidation both acceptable.",
    ),
    # 6. Teutonia — stable peace, rearmament
    DeploymentScenario(
        name="teutonia_stable_peace",
        country="Teutonia",
        leader="Chancellor",
        role="HoS",
        title="Chancellor",
        active_units=[
            {"type": "ground", "count": 3, "hex": [10, 14], "theater": "Ereb West"},
            {"type": "ground", "count": 2, "hex": [11, 15], "theater": "Ereb West"},
            {"type": "air",    "count": 2, "hex": [10, 14], "theater": "Ereb West"},
            {"type": "ad",     "count": 2, "hex": [10, 14], "theater": "Ereb West"},
        ],
        reserve_units={"ground": 3, "air": 1},
        production_capacity="Moderate — recent budget increase, 2 ground + 1 air per round",
        own_territories=["Teutonia homeland (10,14)", "(11,15)", "(10,15)"],
        allied_neighbors=["Columbia", "Eastern Ereb allies (multiple)"],
        hostile_neighbors=["Sarmatia (at war with Ruthenia nearby, not with Teutonia)"],
        recent_combat="No combat. Regional war ongoing but Teutonia not belligerent.",
        strategic_objectives=[
            "maintain European stability",
            "modest reinforcement of eastern flank as deterrent",
            "avoid provoking Sarmatia",
        ],
        expected_decisions={"no_change", "reposition", "deploy"},
        rationale_must_mention=["defen", "eastern", "deter", "stab", "posture", "flank", "adequate", "no change"],
        notes="no_change acceptable if rationale explains adequate posture.",
    ),
]


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

def _format_active_units(units: list[dict[str, Any]]) -> str:
    if not units:
        return "  (none)"
    lines = []
    for u in units:
        hex_label = f"[{u['hex'][0]},{u['hex'][1]}]"
        lines.append(
            f"  - {u['count']}x {u['type']} at {hex_label} ({u['theater']})"
        )
    return "\n".join(lines)


def _format_reserves(reserves: dict[str, int]) -> str:
    if not reserves:
        return "  (none)"
    return "\n".join(f"  - {count}x {utype}" for utype, count in reserves.items())


def _build_deployment_prompt(scenario: DeploymentScenario) -> str:
    """Build a focused E1 unit-deployment prompt for the scenario."""
    active_txt = _format_active_units(scenario.active_units)
    reserves_txt = _format_reserves(scenario.reserve_units)
    own_txt = "\n".join(f"  - {t}" for t in scenario.own_territories)
    allies_txt = "\n".join(f"  - {a}" for a in scenario.allied_neighbors) or "  (none)"
    hostiles_txt = "\n".join(f"  - {h}" for h in scenario.hostile_neighbors) or "  (none)"
    objectives_txt = "\n".join(f"  - {o}" for o in scenario.strategic_objectives)

    return (
        f"You are {scenario.leader}, {scenario.title} of {scenario.country} "
        f"(role: {scenario.role}).\n\n"
        f"INTER-ROUND DEPLOYMENT PHASE. You must decide how to position your "
        f"forces before the next round begins.\n\n"
        f"ACTIVE UNITS (already on map):\n{active_txt}\n\n"
        f"RESERVE UNITS (can be deployed from reserve pool):\n{reserves_txt}\n\n"
        f"PRODUCTION CAPACITY: {scenario.production_capacity}\n\n"
        f"OWN TERRITORIES:\n{own_txt}\n\n"
        f"ALLIED / FRIENDLY NEIGHBORS:\n{allies_txt}\n\n"
        f"HOSTILE / WAR NEIGHBORS:\n{hostiles_txt}\n\n"
        f"LAST ROUND COMBAT RESULTS:\n  {scenario.recent_combat}\n\n"
        f"STRATEGIC OBJECTIVES:\n{objectives_txt}\n\n"
        f"DECIDE: deploy (commit reserves), reposition (move active units), "
        f"withdraw (pull back to reserve), or no_change (posture already optimal).\n\n"
        f"Output STRICT JSON only (no markdown, no preamble):\n"
        f'{{\n'
        f'  "decision": "deploy" | "reposition" | "withdraw" | "no_change",\n'
        f'  "rationale": "string, at least 30 characters explaining strategic reasoning",\n'
        f'  "orders": [\n'
        f'    {{\n'
        f'      "action": "deploy_from_reserve" | "move_active" | "withdraw_to_reserve" | "embark",\n'
        f'      "unit_type": "ground" | "naval" | "air" | "missile" | "ad",\n'
        f'      "count": 1-5,\n'
        f'      "from_hex": [row, col] or "reserve",\n'
        f'      "to_hex": [row, col] or "reserve",\n'
        f'      "strategic_purpose": "brief reason"\n'
        f'    }}\n'
        f'  ]\n'
        f'}}\n'
        f"If decision is no_change, orders may be an empty list."
    )


SYSTEM_MSG = (
    "You are a military commander in the Thucydides Trap geopolitical "
    "simulation. You decide unit deployments between rounds. You must "
    "respond with strict JSON only: a single object with keys 'decision', "
    "'rationale', and 'orders'. No markdown fences, no preamble, no "
    "trailing text."
)


# ---------------------------------------------------------------------------
# LLM caller
# ---------------------------------------------------------------------------

async def _call_deployment_skill(prompt: str) -> str:
    """Send a deployment prompt to the LLM and return raw text."""
    response = await call_llm(
        use_case=LLMUseCase.AGENT_DECISION,
        messages=[{"role": "user", "content": prompt}],
        system=SYSTEM_MSG,
        max_tokens=900,
        temperature=0.4,
    )
    return response.text.strip()


# ---------------------------------------------------------------------------
# Response validator
# ---------------------------------------------------------------------------

def _validate_order(order: Any) -> list[str]:
    """Return list of validation errors for a single order. Empty = valid."""
    errors: list[str] = []
    if not isinstance(order, dict):
        return ["order is not a dict"]

    action = order.get("action")
    if action not in VALID_ORDER_ACTIONS:
        errors.append(f"invalid action '{action}'")

    utype = order.get("unit_type")
    if utype not in VALID_UNIT_TYPES:
        errors.append(f"invalid unit_type '{utype}'")

    count = order.get("count")
    if not isinstance(count, int) or count < 1 or count > 5:
        errors.append(f"invalid count '{count}' (must be int 1-5)")

    # from_hex and to_hex may be "reserve" or [row, col]
    for field_name in ("from_hex", "to_hex"):
        val = order.get(field_name)
        if val == "reserve":
            continue
        if isinstance(val, list) and len(val) == 2 and all(isinstance(x, int) for x in val):
            continue
        errors.append(f"invalid {field_name} '{val}' (must be 'reserve' or [row,col])")

    purpose = order.get("strategic_purpose", "")
    if not isinstance(purpose, str) or len(purpose) < 3:
        errors.append("strategic_purpose missing or too short")

    return errors


def _parse_deployment(text: str) -> dict[str, Any] | None:
    """Parse and return the deployment decision dict, or None on failure."""
    parsed = _parse_json(text)
    if not isinstance(parsed, dict):
        return None
    return parsed


# ---------------------------------------------------------------------------
# Scenario runner
# ---------------------------------------------------------------------------

def _run_scenario(scenario: DeploymentScenario) -> None:
    """Execute a single deployment scenario: build prompt, call LLM, validate."""
    prompt = _build_deployment_prompt(scenario)
    text = asyncio.run(_call_deployment_skill(prompt))

    parsed = _parse_deployment(text)
    assert parsed is not None, (
        f"[{scenario.name}] Failed to parse JSON from LLM response:\n{text[:500]}"
    )

    decision = parsed.get("decision", "")
    rationale = parsed.get("rationale", "")
    orders = parsed.get("orders", [])

    # ---- Schema validation ----
    assert decision in VALID_DECISIONS, (
        f"[{scenario.name}] Invalid decision '{decision}'. "
        f"Valid: {sorted(VALID_DECISIONS)}"
    )

    assert isinstance(rationale, str) and len(rationale) >= 30, (
        f"[{scenario.name}] Rationale missing or too short "
        f"(need >= 30 chars, got {len(rationale) if isinstance(rationale, str) else 'non-string'}): "
        f"{rationale!r}"
    )

    assert isinstance(orders, list), (
        f"[{scenario.name}] 'orders' must be a list, got {type(orders).__name__}"
    )

    # If decision is not no_change, orders should typically be non-empty
    if decision != "no_change" and len(orders) == 0:
        logger.warning(
            "[%s] decision=%s but orders list is empty — suspicious",
            scenario.name, decision,
        )

    # Validate each order
    for idx, order in enumerate(orders):
        order_errors = _validate_order(order)
        assert not order_errors, (
            f"[{scenario.name}] order[{idx}] invalid: {order_errors}\n"
            f"order={order}"
        )

    # ---- Scenario-specific expectations ----
    in_expected = decision in scenario.expected_decisions
    rationale_lc = rationale.lower()
    mention_hit = any(kw.lower() in rationale_lc for kw in scenario.rationale_must_mention) \
        if scenario.rationale_must_mention else True

    # ---- Print consolidated output for human review ----
    print(f"\n  [{scenario.name}] ({scenario.country} — {scenario.role})")
    print(f"    Decision: {decision}  ({'EXPECTED' if in_expected else 'UNEXPECTED'})")
    print(f"    Expected set: {sorted(scenario.expected_decisions)}")
    print(f"    Rationale: {rationale[:250]}")
    print(f"    Keyword mention: {'YES' if mention_hit else 'NO'} "
          f"(wanted one of {scenario.rationale_must_mention})")
    print(f"    Orders ({len(orders)}):")
    for order in orders[:8]:
        print(
            f"      - {order.get('action')} {order.get('count')}x "
            f"{order.get('unit_type')} "
            f"{order.get('from_hex')} -> {order.get('to_hex')}: "
            f"{str(order.get('strategic_purpose', ''))[:80]}"
        )
    if scenario.notes:
        print(f"    Notes: {scenario.notes}")

    # ---- Per-scenario assertions ----
    if scenario.name == "sarmatia_pressing_advantage":
        # Pressing advantage: must not be no_change or withdraw
        assert decision in {"deploy", "reposition"}, (
            f"[{scenario.name}] Winning force should deploy/reposition, not '{decision}'"
        )
        assert len(orders) >= 1, (
            f"[{scenario.name}] Must issue at least one order to exploit breakthrough"
        )

    elif scenario.name == "ruthenia_desperate_defense":
        # Desperate defense: must act, rationale must be defense-oriented
        assert decision in {"deploy", "reposition"}, (
            f"[{scenario.name}] Desperate defender must deploy or reposition, not '{decision}'"
        )
        assert mention_hit, (
            f"[{scenario.name}] Rationale must reference defense/hold/line/capital. "
            f"Got: {rationale[:200]}"
        )

    elif scenario.name == "columbia_global_posture":
        # Any decision OK, but if not no_change the rationale should cite theater logic
        assert decision in scenario.expected_decisions, (
            f"[{scenario.name}] Unexpected decision '{decision}'"
        )
        if decision != "no_change":
            assert mention_hit, (
                f"[{scenario.name}] Change rationale must cite theater logic. "
                f"Got: {rationale[:200]}"
            )

    elif scenario.name == "formosa_pure_defense":
        assert mention_hit, (
            f"[{scenario.name}] Rationale must mention defense or allied coordination. "
            f"Got: {rationale[:200]}"
        )

    elif scenario.name == "cathay_preparing":
        assert mention_hit, (
            f"[{scenario.name}] Rationale must reference Formosa or Pacific posture. "
            f"Got: {rationale[:200]}"
        )

    elif scenario.name == "teutonia_stable_peace":
        # no_change is fine but must be justified
        if decision == "no_change":
            assert len(rationale) >= 40, (
                f"[{scenario.name}] no_change requires substantive justification "
                f"(>=40 chars). Got: {rationale!r}"
            )

    # Soft: decision in expected set (warn-only if not already hard-asserted)
    if not in_expected:
        logger.warning(
            "[%s] decision '%s' not in expected set %s",
            scenario.name, decision, sorted(scenario.expected_decisions),
        )


# ---------------------------------------------------------------------------
# Tests — one per scenario
# ---------------------------------------------------------------------------

@pytest.mark.llm
def test_e1_sarmatia_pressing_advantage():
    """Sarmatia winning war — should press advantage via deploy/reposition."""
    _run_scenario(SCENARIOS[0])


@pytest.mark.llm
def test_e1_ruthenia_desperate_defense():
    """Ruthenia losing war — must commit reserves to defense."""
    _run_scenario(SCENARIOS[1])


@pytest.mark.llm
def test_e1_columbia_global_posture():
    """Columbia global power — theater-aware repositioning or maintain."""
    _run_scenario(SCENARIOS[2])


@pytest.mark.llm
def test_e1_formosa_pure_defense():
    """Formosa under Cathay pressure — defensive consolidation / allied coordination."""
    _run_scenario(SCENARIOS[3])


@pytest.mark.llm
def test_e1_cathay_preparing():
    """Cathay not at war but preparing — Formosa-oriented posture."""
    _run_scenario(SCENARIOS[4])


@pytest.mark.llm
def test_e1_teutonia_stable_peace():
    """Teutonia at peace — likely no_change or modest eastern reinforcement."""
    _run_scenario(SCENARIOS[5])
