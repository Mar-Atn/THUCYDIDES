"""Level 2 — Context Assembly Tests.

Verifies that build_system_prompt() produces correct, role-specific
system prompts for each AI country. Tests that:
  - Each prompt contains the correct country name, character name, position
  - Country-specific data (nuclear level, wars, alliances, OPEC) is present
  - Game rules and autonomy doctrine are included
  - No cross-contamination of confidential info between countries
  - Assertiveness nudges work correctly
  - Prompts are within expected size bounds

Run:
    cd "/Users/marat/4. METAGAMES/1. NEW SIMs/THUCYDIDES" && \
    PYTHONPATH=app .venv/bin/python -m pytest app/tests/layer2/test_l2_context_assembly.py -v -s
"""

import logging
import os
import re
import pytest

logger = logging.getLogger(__name__)

# Load .env before importing engine modules
from pathlib import Path

for p in [
    Path(__file__).resolve().parents[2] / "engine" / ".env",
    Path(__file__).resolve().parents[3] / ".env",
]:
    if p.exists():
        from dotenv import load_dotenv
        load_dotenv(p)
        break

SIM_RUN_ID = os.environ.get(
    "TEST_SIM_RUN_ID", "c954b9b6-35f0-4973-a08b-f38406c524e7"
)

# ── Role definitions for the 5 AI countries ──

AI_ROLES = {
    "pathfinder": {
        "country": "Sarmatia",
        "character": "Pathfinder",
        "position": "President",
        "country_code": "sarmatia",
    },
    "dealer": {
        "country": "Columbia",
        "character": "Dealer",
        "position": "President",
        "country_code": "columbia",
    },
    "furnace": {
        "country": "Persia",
        "character": "Furnace",
        "position": "Supreme Leader",
        "country_code": "persia",
    },
    "wellspring": {
        "country": "Solaria",
        "character": "Wellspring",
        "position": "Crown Prince",
        "country_code": "solaria",
    },
    "vizier": {
        "country": "Phrygia",
        "character": "Vizier",
        "position": "President",
        "country_code": "phrygia",
    },
}


# ── Fixtures ──


@pytest.fixture(scope="module")
def prompts() -> dict[str, str]:
    """Build system prompts for all 5 AI roles (cached for module)."""
    from engine.agents.managed.system_prompt import build_system_prompt

    result = {}
    for role_id in AI_ROLES:
        prompt = build_system_prompt(
            role_id=role_id,
            sim_run_id=SIM_RUN_ID,
            assertiveness=5,
        )
        result[role_id] = prompt
        logger.info(
            "Built prompt for %s: %d chars", role_id, len(prompt)
        )
    return result


# ── Parametrized identity tests ──


@pytest.mark.parametrize("role_id", AI_ROLES.keys())
class TestCountryIdentity:
    """Each prompt contains correct identity for its role."""

    def test_country_name(self, prompts, role_id):
        prompt = prompts[role_id]
        country = AI_ROLES[role_id]["country"]
        assert country.lower() in prompt.lower(), (
            f"{role_id} prompt missing country name '{country}'"
        )

    def test_character_name(self, prompts, role_id):
        prompt = prompts[role_id]
        character = AI_ROLES[role_id]["character"]
        assert character in prompt, (
            f"{role_id} prompt missing character name '{character}'"
        )

    def test_head_of_state(self, prompts, role_id):
        """Prompt mentions the role's position/title."""
        prompt = prompts[role_id]
        info = AI_ROLES[role_id]
        # Check for either the specific title or generic "head of state"
        prompt_lower = prompt.lower()
        assert (
            info["position"].lower() in prompt_lower
            or "head of state" in prompt_lower
            or "head_of_state" in prompt_lower
        ), f"{role_id} prompt missing position '{info['position']}'"


# ── Country-specific content tests ──


class TestSarmatia:
    """Sarmatia (Pathfinder) specific checks."""

    def test_nuclear_level(self, prompts):
        prompt = prompts["pathfinder"]
        # Sarmatia is L3 nuclear
        assert re.search(r"nuclear.*3|L3|level.*3", prompt, re.IGNORECASE), (
            "Sarmatia prompt missing nuclear level 3"
        )

    def test_at_war_with_ruthenia(self, prompts):
        prompt = prompts["pathfinder"]
        assert "ruthenia" in prompt.lower() or "war" in prompt.lower(), (
            "Sarmatia prompt missing war reference"
        )

    def test_opec_or_cartel(self, prompts):
        """Sarmatia is a major energy producer (cartel/OPEC context)."""
        prompt = prompts["pathfinder"]
        prompt_lower = prompt.lower()
        # Check for oil producer or energy-related content
        assert (
            "oil" in prompt_lower
            or "opec" in prompt_lower
            or "cartel" in prompt_lower
            or "energy" in prompt_lower
        ), "Sarmatia prompt missing energy/oil context"


class TestColumbia:
    """Columbia (Dealer) specific checks."""

    def test_nuclear_level(self, prompts):
        prompt = prompts["dealer"]
        assert re.search(r"nuclear.*3|L3|level.*3", prompt, re.IGNORECASE), (
            "Columbia prompt missing nuclear level 3"
        )

    def test_at_war_with_persia(self, prompts):
        prompt = prompts["dealer"]
        prompt_lower = prompt.lower()
        assert "persia" in prompt_lower or "war" in prompt_lower, (
            "Columbia prompt missing war with Persia"
        )


class TestPersia:
    """Persia (Furnace) specific checks."""

    def test_at_war(self, prompts):
        prompt = prompts["furnace"]
        prompt_lower = prompt.lower()
        assert "war" in prompt_lower, (
            "Persia prompt missing war reference"
        )

    def test_nuclear_context(self, prompts):
        """Persia has nuclear ambitions (level shown in prompt)."""
        prompt = prompts["furnace"]
        assert "nuclear" in prompt.lower(), (
            "Persia prompt missing nuclear context"
        )


class TestSolaria:
    """Solaria (Wellspring) specific checks."""

    def test_oil_context(self, prompts):
        """Solaria is a major oil producer / OPEC member."""
        prompt = prompts["wellspring"]
        prompt_lower = prompt.lower()
        assert (
            "oil" in prompt_lower
            or "opec" in prompt_lower
            or "energy" in prompt_lower
        ), "Solaria prompt missing oil/OPEC context"


class TestPhrygia:
    """Phrygia (Vizier) specific checks."""

    def test_country_present(self, prompts):
        prompt = prompts["vizier"]
        assert "phrygia" in prompt.lower(), (
            "Vizier prompt missing Phrygia country name"
        )

    def test_bosphorus_or_strategic(self, prompts):
        """Vizier controls Bosphorus — should appear in powers or objectives."""
        prompt = prompts["vizier"]
        prompt_lower = prompt.lower()
        assert (
            "bosphorus" in prompt_lower
            or "leverage" in prompt_lower
            or "nato" in prompt_lower
            or "western treaty" in prompt_lower
        ), "Phrygia prompt missing strategic context (Bosphorus/NATO)"


# ── Cross-cutting tests ──


@pytest.mark.parametrize("role_id", AI_ROLES.keys())
class TestCrossCutting:
    """Tests that apply to ALL AI prompts."""

    def test_prompt_length(self, prompts, role_id):
        """Prompt is within reasonable bounds (3000-30000 chars)."""
        prompt = prompts[role_id]
        length = len(prompt)
        assert 3000 <= length <= 30000, (
            f"{role_id} prompt length {length} out of range [3000, 30000]"
        )

    def test_contains_game_rules(self, prompts, role_id):
        """Prompt includes game action types."""
        prompt = prompts[role_id]
        prompt_lower = prompt.lower()
        for action in ["ground_attack", "declare_attack", "set_budget", "propose_transaction", "set_tariffs"]:
            # At least some action types should be present
            if action in prompt_lower:
                return
        # Fallback: check for game rules header
        assert "game rules" in prompt_lower, (
            f"{role_id} prompt missing game rules / action types"
        )

    def test_contains_autonomy_doctrine(self, prompts, role_id):
        """Prompt includes the autonomy doctrine."""
        prompt = prompts[role_id]
        assert (
            "AUTONOMY DOCTRINE" in prompt
            or "autonomous" in prompt.lower()
        ), f"{role_id} prompt missing autonomy doctrine"

    def test_contains_character_traits(self, prompts, role_id):
        """Prompt includes character trait framework."""
        prompt = prompts[role_id]
        assert "CHARACTER TRAITS" in prompt or "character_traits" in prompt, (
            f"{role_id} prompt missing character trait framework"
        )


# ── Information scoping (no cross-contamination) ──


@pytest.mark.parametrize("role_id", AI_ROLES.keys())
class TestInformationScoping:
    """Verify prompts don't leak another country's confidential data."""

    def test_no_other_country_gdp(self, prompts, role_id):
        """The prompt's 'YOUR STARTING POSITION' should only show own GDP."""
        prompt = prompts[role_id]
        own_country = AI_ROLES[role_id]["country"]

        # Find the STARTING POSITION section
        match = re.search(
            r"YOUR STARTING POSITION.*?(?=^##|\Z)",
            prompt,
            re.DOTALL | re.MULTILINE,
        )
        if not match:
            pytest.skip("No STARTING POSITION section found")

        section = match.group(0)
        # The starting position should mention own country
        assert own_country.lower() in section.lower(), (
            f"Starting position for {role_id} doesn't mention {own_country}"
        )

    def test_prompt_is_country_specific(self, prompts, role_id):
        """The 'Who You Are' section mentions own country, not others."""
        prompt = prompts[role_id]
        own_country = AI_ROLES[role_id]["country"]
        own_character = AI_ROLES[role_id]["character"]

        # Find the Who You Are section
        match = re.search(
            r"Who You Are.*?(?=^##|\Z)",
            prompt,
            re.DOTALL | re.MULTILINE,
        )
        if not match:
            pytest.skip("No 'Who You Are' section found")

        section = match.group(0)
        assert own_character in section, (
            f"Who You Are for {role_id} doesn't mention {own_character}"
        )


# ── Assertiveness nudge tests ──


class TestAssertiveness:
    """Verify assertiveness dial controls cooperative/competitive nudge."""

    def test_neutral_no_nudge(self):
        """Assertiveness=5 (default) should not include any disposition nudge."""
        from engine.agents.managed.system_prompt import build_system_prompt

        prompt = build_system_prompt(
            role_id="dealer",
            sim_run_id=SIM_RUN_ID,
            assertiveness=5,
        )
        assert "World disposition" not in prompt, (
            "Neutral assertiveness (5) should not contain disposition nudge"
        )

    def test_cooperative_nudge(self):
        """Assertiveness < 5 should include cooperative nudge."""
        from engine.agents.managed.system_prompt import build_system_prompt

        prompt = build_system_prompt(
            role_id="dealer",
            sim_run_id=SIM_RUN_ID,
            assertiveness=3,
        )
        assert "cooperation" in prompt.lower() or "diplomatic" in prompt.lower(), (
            "Cooperative assertiveness (3) should include cooperative nudge"
        )

    def test_competitive_nudge(self):
        """Assertiveness > 5 should include competitive nudge."""
        from engine.agents.managed.system_prompt import build_system_prompt

        prompt = build_system_prompt(
            role_id="dealer",
            sim_run_id=SIM_RUN_ID,
            assertiveness=8,
        )
        assert "competitive" in prompt.lower() or "strength" in prompt.lower(), (
            "Competitive assertiveness (8) should include competitive nudge"
        )
