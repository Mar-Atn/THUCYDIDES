"""L3-lite: AI response quality for mandatory economic decisions.

Real LLM calls (~$0.001 each on Gemini Flash). Tests that the AI module
understands the mandatory decision context and responds with valid structure.

Run:
    cd app && PYTHONPATH=. python3 -m pytest tests/layer3/test_mandatory_ai.py -v

Skip LLM tests:
    cd app && PYTHONPATH=. python3 -m pytest tests/layer3/test_mandatory_ai.py -v -m "not llm"
"""

import asyncio
import json
import logging

import pytest

from engine.agents.full_round_runner import _build_mandatory_prompt, OPEC_MEMBERS
from engine.agents.decisions import _parse_json
from engine.services.llm import call_llm
from engine.config.settings import LLMUseCase

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SYSTEM_MSG = (
    "You are an AI leader in a geopolitical simulation. "
    "Respond concisely with JSON or 'no_changes'."
)

VALID_OPEC_LEVELS = {"min", "low", "normal", "high", "max"}
VALID_MANDATORY_KEYS = {"budget", "sanctions", "tariffs", "opec"}


def _make_agent(
    country_code: str,
    character_name: str,
    title: str,
    country_name: str,
    objectives: list[str],
) -> dict:
    """Build a minimal agent dict matching full_round_runner expectations."""
    return {
        "country_code": country_code,
        "character_name": character_name,
        "title": title,
        "country_name": country_name,
        "objectives": objectives,
    }


async def _call_mandatory(prompt: str) -> str:
    """Send a mandatory prompt to the LLM and return raw text."""
    response = await call_llm(
        use_case=LLMUseCase.AGENT_DECISION,
        messages=[{"role": "user", "content": prompt}],
        system=SYSTEM_MSG,
        max_tokens=512,
        temperature=0.4,
    )
    return response.text.strip()


def _is_no_changes(text: str) -> bool:
    """Check if the response signals no changes."""
    low = text.lower()
    return "no_change" in low or low in ("no_changes", "no changes", "none")


# ---------------------------------------------------------------------------
# Test 1: Columbia budget response
# ---------------------------------------------------------------------------

@pytest.mark.llm
def test_columbia_budget_response():
    """Columbia (Dealer, President) should return valid budget JSON or no_changes."""
    agent = _make_agent(
        country_code="columbia",
        character_name="Dealer",
        title="President",
        country_name="Columbia",
        objectives=["maintain global hegemony", "contain Cathay"],
    )
    eco_state = {}  # defaults: social_pct=1.0, military=0, tech=0
    prompt = _build_mandatory_prompt(agent, "columbia", round_num=2, eco_state=eco_state)

    text = asyncio.run(_call_mandatory(prompt))
    logger.info("Columbia response: %s", text[:300])

    if _is_no_changes(text):
        return  # valid

    parsed = _parse_json(text)
    assert parsed is not None, f"Response was neither no_changes nor valid JSON: {text[:200]}"
    assert isinstance(parsed, dict), f"Expected dict, got {type(parsed)}"

    # If budget present, check ranges
    if "budget" in parsed:
        b = parsed["budget"]
        assert isinstance(b, dict), "budget must be a dict"
        if "social_pct" in b:
            assert 0.5 <= float(b["social_pct"]) <= 1.5, f"social_pct out of range: {b['social_pct']}"
        if "military_coins" in b:
            assert float(b["military_coins"]) >= 0, "military_coins must be >= 0"
        if "tech_coins" in b:
            assert float(b["tech_coins"]) >= 0, "tech_coins must be >= 0"


# ---------------------------------------------------------------------------
# Test 2: Sarmatia sanctions response
# ---------------------------------------------------------------------------

@pytest.mark.llm
def test_sarmatia_sanctions_response():
    """Sarmatia at war with Ruthenia — likely to impose sanctions. Validate structure."""
    agent = _make_agent(
        country_code="sarmatia",
        character_name="Pathfinder",
        title="President",
        country_name="Sarmatia",
        objectives=["win war against Ruthenia", "maintain stability"],
    )
    eco_state = {}
    prompt = _build_mandatory_prompt(agent, "sarmatia", round_num=3, eco_state=eco_state)

    text = asyncio.run(_call_mandatory(prompt))
    logger.info("Sarmatia response: %s", text[:300])

    if _is_no_changes(text):
        return  # acceptable — agent may choose status quo

    parsed = _parse_json(text)
    assert parsed is not None, f"Unparseable response: {text[:200]}"
    assert isinstance(parsed, dict)

    # Soft check: if sanctions present, targets should be strings
    if "sanctions" in parsed:
        s = parsed["sanctions"]
        assert isinstance(s, list), "sanctions must be a list"
        for entry in s:
            assert isinstance(entry, dict), f"sanction entry must be dict: {entry}"
            if "target" in entry:
                assert isinstance(entry["target"], str), f"target must be string: {entry['target']}"


# ---------------------------------------------------------------------------
# Test 3: Solaria OPEC response
# ---------------------------------------------------------------------------

@pytest.mark.llm
def test_solaria_opec_response():
    """Solaria (Wellspring, OPEC member) — should include valid OPEC decision."""
    assert "solaria" in OPEC_MEMBERS, "Solaria must be an OPEC member"

    agent = _make_agent(
        country_code="solaria",
        character_name="Wellspring",
        title="King",
        country_name="Solaria",
        objectives=["maximize oil revenue", "counter Persia"],
    )
    eco_state = {"set_opec": {"production_level": "normal"}}
    prompt = _build_mandatory_prompt(agent, "solaria", round_num=2, eco_state=eco_state)

    # Verify OPEC section IS present in the prompt
    assert "OPEC" in prompt, "OPEC section must appear in prompt for OPEC members"

    text = asyncio.run(_call_mandatory(prompt))
    logger.info("Solaria response: %s", text[:300])

    if _is_no_changes(text):
        return  # acceptable

    parsed = _parse_json(text)
    assert parsed is not None, f"Unparseable response: {text[:200]}"
    assert isinstance(parsed, dict)

    # If OPEC decision present, validate production_level
    if "opec" in parsed:
        opec = parsed["opec"]
        assert isinstance(opec, dict), "opec must be a dict"
        if "production_level" in opec:
            level = opec["production_level"].lower().strip()
            assert level in VALID_OPEC_LEVELS, f"Invalid OPEC level: {level}"


# ---------------------------------------------------------------------------
# Test 4: Teutonia — no OPEC in prompt (no LLM call needed)
# ---------------------------------------------------------------------------

def test_teutonia_no_opec_in_prompt():
    """Teutonia (non-OPEC) — the prompt must NOT contain OPEC section."""
    assert "teutonia" not in OPEC_MEMBERS, "Teutonia must NOT be an OPEC member"

    agent = _make_agent(
        country_code="teutonia",
        character_name="Chancellor",
        title="Chancellor",
        country_name="Teutonia",
        objectives=["lead European integration", "maintain economic growth"],
    )
    eco_state = {}
    prompt = _build_mandatory_prompt(agent, "teutonia", round_num=1, eco_state=eco_state)

    assert "OPEC" not in prompt, (
        f"OPEC section must NOT appear for non-OPEC member Teutonia. "
        f"Prompt excerpt: ...{prompt[-200:]}"
    )


# ---------------------------------------------------------------------------
# Test 5: Bharata — no_changes or valid JSON
# ---------------------------------------------------------------------------

@pytest.mark.llm
def test_bharata_no_changes_valid_response():
    """Bharata (stable, defaults) — response must be parseable."""
    agent = _make_agent(
        country_code="bharata",
        character_name="Lotus",
        title="Prime Minister",
        country_name="Bharata",
        objectives=["sustain economic growth", "maintain regional stability"],
    )
    eco_state = {}
    prompt = _build_mandatory_prompt(agent, "bharata", round_num=1, eco_state=eco_state)

    text = asyncio.run(_call_mandatory(prompt))
    logger.info("Bharata response: %s", text[:300])

    # Must be parseable: either no_changes or valid JSON
    if _is_no_changes(text):
        return  # valid

    parsed = _parse_json(text)
    assert parsed is not None, f"Response is neither no_changes nor valid JSON: {text[:200]}"
    assert isinstance(parsed, dict), f"Expected dict, got {type(parsed)}"


# ---------------------------------------------------------------------------
# Test 6: Cathay — JSON structure validation
# ---------------------------------------------------------------------------

@pytest.mark.llm
def test_response_json_structure():
    """Cathay with non-default settings — JSON response keys must be valid."""
    agent = _make_agent(
        country_code="cathay",
        character_name="Dragon",
        title="President",
        country_name="Cathay",
        objectives=["overtake Columbia economically", "reunify Formosa"],
    )
    eco_state = {
        "set_budget": {"social_pct": 0.8, "military_coins": 3, "tech_coins": 2},
        "set_sanction": {"sanctions": [{"target": "formosa", "level": 2}]},
        "set_tariff": {"tariffs": [{"target": "columbia", "level": 1}]},
    }
    prompt = _build_mandatory_prompt(agent, "cathay", round_num=4, eco_state=eco_state)

    text = asyncio.run(_call_mandatory(prompt))
    logger.info("Cathay response: %s", text[:300])

    if _is_no_changes(text):
        return  # valid

    parsed = _parse_json(text)
    assert parsed is not None, f"Unparseable response: {text[:200]}"
    assert isinstance(parsed, dict)

    # Only allowed top-level keys
    unexpected = set(parsed.keys()) - VALID_MANDATORY_KEYS
    assert not unexpected, f"Unexpected keys in response: {unexpected}"
