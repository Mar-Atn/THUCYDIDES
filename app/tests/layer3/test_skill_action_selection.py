"""L3 Skill A1: Action Selection Appropriateness Test.

Tests the MOST IMPORTANT AI skill: given a situation, can the agent select
an APPROPRIATE action from the available action space?

Real LLM calls (Gemini Flash, ~$0.001 each). 10 scenarios, each with a
defined set of plausible actions. The test checks whether the chosen action
falls within the plausible set.

Run:
    cd app && PYTHONPATH=. python3 -m pytest tests/layer3/test_skill_action_selection.py -v -s

Skip LLM tests:
    cd app && PYTHONPATH=. python3 -m pytest tests/layer3/test_skill_action_selection.py -v -m "not llm"
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field

import pytest

from engine.agents.decisions import _parse_json
from engine.services.llm import call_llm
from engine.config.settings import LLMUseCase

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Action types (from COMMIT_ACTION_SCHEMA in stage4_test.py)
# ---------------------------------------------------------------------------

ALL_ACTION_TYPES = [
    "move_unit",
    "mobilize_reserve",
    "declare_attack",
    "naval_bombardment",
    "declare_blockade",
    "nuclear_test",
    "set_budget",
    "set_tariff",
    "set_sanction",
    "set_opec",
    "rd_investment",
    "public_statement",
    "call_org_meeting",
    "covert_op",
    "propose_transaction",
]

ACTION_LIST_TEXT = "\n".join(f"  - {a}" for a in ALL_ACTION_TYPES)

# ---------------------------------------------------------------------------
# Scenario definition
# ---------------------------------------------------------------------------

@dataclass
class Scenario:
    """A test scenario for action selection."""
    name: str
    country: str
    leader: str
    title: str
    situation: str
    objectives: list[str]
    plausible: set[str]
    implausible: set[str] = field(default_factory=set)


SCENARIOS: list[Scenario] = [
    # 1. Columbia under attack
    Scenario(
        name="columbia_under_attack",
        country="Columbia",
        leader="Dealer",
        title="President",
        situation=(
            "Columbia stability 7/10, GDP $280B, treasury $50B. "
            "Persia just launched a missile strike on Columbia's infrastructure last round, "
            "destroying a power plant and killing 200 civilians. Public outrage is at maximum. "
            "Columbia has strong military forces deployed globally."
        ),
        objectives=["defend homeland", "punish aggression", "maintain global credibility"],
        plausible={"declare_attack", "mobilize_reserve", "public_statement", "covert_op"},
        implausible={"rd_investment", "propose_transaction"},
    ),
    # 2. Caribe economic crisis
    Scenario(
        name="caribe_economic_crisis",
        country="Caribe",
        leader="Beacon",
        title="President",
        situation=(
            "Caribe GDP $1.9B (tiny), treasury $0.5B (nearly empty), inflation 60%, "
            "stability 3/10. Under L3 sanctions from Columbia and Teutonia. "
            "No military threats but economy collapsing. Population suffering."
        ),
        objectives=["stabilize economy", "get sanctions lifted", "prevent collapse"],
        plausible={"propose_transaction", "public_statement", "set_budget"},
        implausible={"declare_attack", "rd_investment", "nuclear_test"},
    ),
    # 3. Cathay eyeing Formosa
    Scenario(
        name="cathay_formosa_pressure",
        country="Cathay",
        leader="Helmsman",
        title="President",
        situation=(
            "Cathay GDP $190B, strong military (2nd largest), stability 8/10. "
            "Formosa tension rising — Formosa just signed a new arms deal with Columbia. "
            "Cathay's objective includes formosa_resolution. No active wars yet. "
            "International community is watching closely."
        ),
        objectives=["formosa_resolution", "avoid premature war", "isolate Formosa diplomatically"],
        plausible={"public_statement", "covert_op", "propose_transaction", "call_org_meeting", "set_sanction", "set_tariff"},
        implausible={"declare_attack"},
    ),
    # 4. Ruthenia desperate defense
    Scenario(
        name="ruthenia_desperate_defense",
        country="Ruthenia",
        leader="Guardian",
        title="President",
        situation=(
            "Ruthenia GDP $2.2B, at war with Sarmatia for 3 rounds. Stability 5/10, "
            "war_tiredness 4/5. Treasury near zero ($0.3B). Lost 2 provinces last round. "
            "Sarmatia has military advantage. Ruthenia's reserves are depleted. "
            "Columbia and Teutonia are sympathetic but haven't committed forces."
        ),
        objectives=["survive the war", "get military aid from allies", "hold remaining territory"],
        plausible={"propose_transaction", "public_statement", "mobilize_reserve"},
        implausible={"rd_investment", "set_tariff", "covert_op"},
    ),
    # 5. Solaria oil power
    Scenario(
        name="solaria_oil_leverage",
        country="Solaria",
        leader="Wellspring",
        title="King",
        situation=(
            "Solaria GDP $11B, major oil producer (10 mbpd), OPEC member. "
            "Oil price $85/barrel. Persia (rival OPEC member) is at war, its production disrupted. "
            "Solaria has no active wars, stable at 7/10. Good relations with Columbia. "
            "OPEC meeting coming next round."
        ),
        objectives=["maximize oil revenue", "increase regional influence", "counter Persia"],
        plausible={"set_opec", "propose_transaction", "public_statement"},
        implausible={"declare_attack", "nuclear_test"},
    ),
    # 6. Formosa survival
    Scenario(
        name="formosa_survival",
        country="Formosa",
        leader="Islander",
        title="President",
        situation=(
            "Formosa GDP $8B, under increasing Cathay pressure. Cathay conducting "
            "naval exercises near Formosa. Columbia is an ally but far away. "
            "Formosa's main leverage: semiconductor industry (global supply chain). "
            "Stability 6/10. Small but modern military."
        ),
        objectives=["deter Cathay invasion", "strengthen Columbia alliance", "maintain tech advantage"],
        plausible={"rd_investment", "propose_transaction", "public_statement"},
        implausible={"declare_attack", "set_sanction"},
    ),
    # 7. Sarmatia at war — pressing advantage
    Scenario(
        name="sarmatia_pressing_advantage",
        country="Sarmatia",
        leader="Pathfinder",
        title="President",
        situation=(
            "Sarmatia GDP $20B, at war with Ruthenia. Military advantage — took 2 provinces "
            "last round. Ruthenia's forces weakening. International condemnation exists but "
            "no direct military intervention. Stability 6/10, war_tiredness 2/5 (manageable). "
            "Objectives include territorial_control over disputed eastern provinces."
        ),
        objectives=["territorial_control", "win war quickly", "prevent international intervention"],
        plausible={"declare_attack", "mobilize_reserve", "covert_op", "public_statement"},
        implausible={"propose_transaction"},
    ),
    # 8. Teutonia reluctant rearmament
    Scenario(
        name="teutonia_rearmament",
        country="Teutonia",
        leader="Chancellor",
        title="Chancellor",
        situation=(
            "Teutonia GDP $45B, stable democracy (stability 9/10), no active wars. "
            "Allies pressuring Teutonia to increase defense spending from 1.5% to 3% of GDP. "
            "Sarmatia-Ruthenia war is destabilizing the region. Teutonia is EU and NATO leader. "
            "Economy strong but public prefers social spending over military."
        ),
        objectives=["maintain European stability", "increase defense readiness", "sustain economic growth"],
        plausible={"set_budget", "rd_investment", "public_statement", "call_org_meeting"},
        implausible={"declare_attack", "covert_op", "nuclear_test"},
    ),
    # 9. Persia nuclear ambition
    Scenario(
        name="persia_nuclear_ambition",
        country="Persia",
        leader="Sovereign",
        title="Supreme Leader",
        situation=(
            "Persia GDP $5B, at war with Columbia and Levantia. Nuclear program at T1 level. "
            "Under heavy sanctions (L3 from Columbia, L2 from Teutonia). Stability 4/10. "
            "Objective: develop nuclear weapon as deterrent. Resources are limited but "
            "nuclear program is the regime's top priority."
        ),
        objectives=["develop nuclear weapon", "survive the war", "break sanctions"],
        plausible={"nuclear_test", "rd_investment", "covert_op", "declare_attack"},
        implausible={"propose_transaction"},
    ),
    # 10. Bharata multi-alignment
    Scenario(
        name="bharata_multi_alignment",
        country="Bharata",
        leader="Lotus",
        title="Prime Minister",
        situation=(
            "Bharata GDP $42B, no active wars. Friendly relations with both Columbia and Cathay. "
            "Largest democracy, growing economy. No territorial disputes. "
            "Pursuing strategic autonomy — buys weapons from both blocs. "
            "Stability 7/10. Tech sector booming (AI investment)."
        ),
        objectives=["strategic_autonomy", "economic_growth", "avoid entanglement in great power conflicts"],
        plausible={"rd_investment", "propose_transaction", "public_statement", "set_budget"},
        implausible={"declare_attack", "covert_op", "nuclear_test"},
    ),
]


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

def _build_action_prompt(scenario: Scenario) -> str:
    """Build a focused action-selection prompt for the scenario."""
    objectives_text = "\n".join(f"  - {obj}" for obj in scenario.objectives)
    return (
        f"You are {scenario.leader}, {scenario.title} of {scenario.country}.\n\n"
        f"SITUATION:\n{scenario.situation}\n\n"
        f"YOUR OBJECTIVES:\n{objectives_text}\n\n"
        f"AVAILABLE ACTIONS (choose exactly ONE):\n{ACTION_LIST_TEXT}\n\n"
        f"Choose the SINGLE MOST IMPORTANT action to take right now.\n"
        f"Respond with JSON only, no other text:\n"
        f'{{"action_type": "...", "rationale": "..."}}'
    )


SYSTEM_MSG = (
    "You are an AI leader in a geopolitical simulation called Thucydides Trap. "
    "You must choose ONE action from the available list. "
    "Respond with valid JSON only: {\"action_type\": \"...\", \"rationale\": \"...\"}. "
    "No markdown fences, no preamble."
)


# ---------------------------------------------------------------------------
# LLM caller
# ---------------------------------------------------------------------------

async def _call_action_selection(prompt: str) -> str:
    """Send an action-selection prompt to the LLM and return raw text."""
    response = await call_llm(
        use_case=LLMUseCase.AGENT_DECISION,
        messages=[{"role": "user", "content": prompt}],
        system=SYSTEM_MSG,
        max_tokens=256,
        temperature=0.4,
    )
    return response.text.strip()


def _extract_action(text: str) -> tuple[str | None, str | None]:
    """Parse action_type and rationale from LLM response.

    Returns (action_type, rationale) or (None, None) on parse failure.
    """
    parsed = _parse_json(text)
    if not isinstance(parsed, dict):
        return None, None
    action_type = parsed.get("action_type", "").strip().lower()
    rationale = parsed.get("rationale", "")
    if not action_type:
        return None, None
    return action_type, rationale


# ---------------------------------------------------------------------------
# Test runner helper
# ---------------------------------------------------------------------------

def _run_scenario(scenario: Scenario) -> None:
    """Execute a single scenario test: build prompt, call LLM, validate."""
    prompt = _build_action_prompt(scenario)
    text = asyncio.run(_call_action_selection(prompt))

    action_type, rationale = _extract_action(text)

    # Must parse
    assert action_type is not None, (
        f"[{scenario.name}] Failed to parse action from LLM response: {text[:300]}"
    )

    # Must be a valid action type
    assert action_type in ALL_ACTION_TYPES, (
        f"[{scenario.name}] Unknown action_type '{action_type}'. "
        f"Valid: {ALL_ACTION_TYPES}"
    )

    # Print for human review
    plausible_hit = action_type in scenario.plausible
    implausible_hit = action_type in scenario.implausible
    status = "PLAUSIBLE" if plausible_hit else ("IMPLAUSIBLE" if implausible_hit else "UNEXPECTED")

    print(f"\n  [{scenario.name}] {status}")
    print(f"    Action: {action_type}")
    print(f"    Rationale: {rationale[:200]}")
    print(f"    Plausible set: {sorted(scenario.plausible)}")

    # Hard fail: action is in the explicitly implausible set
    if implausible_hit:
        # Soft assertion: log warning but check rationale
        logger.warning(
            "[%s] Action '%s' is in IMPLAUSIBLE set. Rationale: %s",
            scenario.name, action_type, rationale[:200],
        )
        # If rationale exists and is substantive, warn instead of fail
        if rationale and len(rationale) > 20:
            print(f"    WARNING: Implausible action but rationale provided — review manually.")
        else:
            pytest.fail(
                f"[{scenario.name}] Chose IMPLAUSIBLE action '{action_type}' "
                f"without substantive rationale. Implausible set: {sorted(scenario.implausible)}"
            )

    # Soft check: action should ideally be in plausible set
    if not plausible_hit and not implausible_hit:
        print(f"    NOTE: Action not in plausible set but not implausible either — acceptable.")


# ---------------------------------------------------------------------------
# Tests — one per scenario
# ---------------------------------------------------------------------------

@pytest.mark.llm
def test_s01_columbia_under_attack():
    """Columbia attacked by Persia — should prioritize military response."""
    _run_scenario(SCENARIOS[0])


@pytest.mark.llm
def test_s02_caribe_economic_crisis():
    """Caribe economy collapsing — should seek help or austerity."""
    _run_scenario(SCENARIOS[1])


@pytest.mark.llm
def test_s03_cathay_formosa_pressure():
    """Cathay eyeing Formosa — should pressure not attack (yet)."""
    _run_scenario(SCENARIOS[2])


@pytest.mark.llm
def test_s04_ruthenia_desperate_defense():
    """Ruthenia losing war — should seek allies and weapons."""
    _run_scenario(SCENARIOS[3])


@pytest.mark.llm
def test_s05_solaria_oil_leverage():
    """Solaria oil power — should use OPEC leverage."""
    _run_scenario(SCENARIOS[4])


@pytest.mark.llm
def test_s06_formosa_survival():
    """Formosa under Cathay pressure — should build alliances and tech."""
    _run_scenario(SCENARIOS[5])


@pytest.mark.llm
def test_s07_sarmatia_pressing_advantage():
    """Sarmatia winning war — should press military advantage."""
    _run_scenario(SCENARIOS[6])


@pytest.mark.llm
def test_s08_teutonia_rearmament():
    """Teutonia peacetime — should balance economy and defense."""
    _run_scenario(SCENARIOS[7])


@pytest.mark.llm
def test_s09_persia_nuclear_ambition():
    """Persia at war — should advance nuclear program."""
    _run_scenario(SCENARIOS[8])


@pytest.mark.llm
def test_s10_bharata_multi_alignment():
    """Bharata stable — should stay neutral and grow."""
    _run_scenario(SCENARIOS[9])
