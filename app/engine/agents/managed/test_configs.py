"""Test configurations for M5 AI Participant testing.

Defines role sets for different test scenarios. Used by test scripts
and the orchestrator to select which agents to initialize.

These don't require new sim_runs — they work with any existing sim_run
by selecting a subset of roles to activate as AI participants.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TestConfig:
    """A test scenario configuration."""
    name: str
    description: str
    role_ids: list[str]
    pulses_per_round: int = 3
    assertiveness: int = 5
    rounds: int = 1
    max_meetings_per_round: int = 5


# ---------------------------------------------------------------------------
# Test scenarios
# ---------------------------------------------------------------------------

# Minimal: 2 agents, test basic interaction
DUO_TEST = TestConfig(
    name="Duo: Columbia vs Cathay",
    description="2 HoS — Dealer and Helmsman. Strategic rivals. Tests bilateral dynamics.",
    role_ids=["dealer", "helmsman"],
    pulses_per_round=3,
    assertiveness=6,
)

# Core conflict: 5 agents, two active wars
FIVE_AGENT_TEST = TestConfig(
    name="Five: Core Conflicts",
    description="5 HoS — Columbia, Cathay, Sarmatia, Ruthenia, Persia. Two active wars, max tension.",
    role_ids=["dealer", "helmsman", "pathfinder", "beacon", "furnace"],
    pulses_per_round=3,
    assertiveness=6,
)

# 10-country world: major players only
TEN_COUNTRY_TEST = TestConfig(
    name="Ten: Major Powers",
    description=(
        "10 HoS — the 10 most strategically important countries. "
        "Two wars (Columbia-Persia, Sarmatia-Ruthenia), Cathay-Formosa tension, "
        "Korean standoff, European alliance dynamics."
    ),
    role_ids=[
        "dealer",       # Columbia (superpower, war with Persia)
        "helmsman",     # Cathay (rising power, Formosa threat)
        "pathfinder",   # Sarmatia (autocrat, war with Ruthenia)
        "beacon",       # Ruthenia (under attack, needs Western support)
        "furnace",      # Persia (at war with Columbia, nuclear race)
        "forge",        # Teutonia (European anchor, sanctions enforcer)
        "sakura",       # Yamato (Pacific power, remilitarizing)
        "chip",         # Formosa (semiconductor flashpoint)
        "wellspring",   # Solaria (OPEC power, oil leverage)
        "mariner",      # Albion (naval power, Western Treaty)
    ],
    pulses_per_round=4,
    assertiveness=5,
)

# Columbia team: internal dynamics with international context
COLUMBIA_TEAM_TEST = TestConfig(
    name="Columbia Team + Neighbors",
    description=(
        "Columbia's full team (HoS + secondary roles) plus key international "
        "HoS. Tests internal team coordination and multi-role dynamics."
    ),
    role_ids=[
        # Columbia team (all roles for this country)
        "dealer",       # HoS
        # Add Columbia secondary roles here when we know their IDs
        # International context
        "helmsman",     # Cathay HoS (strategic rival)
        "pathfinder",   # Sarmatia HoS (adversary)
        "furnace",      # Persia HoS (at war)
        "beacon",       # Ruthenia HoS (ally)
        "forge",        # Teutonia HoS (ally)
    ],
    pulses_per_round=4,
    assertiveness=6,
    rounds=2,  # 2 rounds to test memory persistence
)

# 2-round test: tests memory across rounds
TWO_ROUND_TEST = TestConfig(
    name="Two Rounds: Memory Test",
    description=(
        "3 agents play 2 rounds. Tests: do agents remember Round 1? "
        "Do they build on prior decisions? Do conversations emerge in Round 2?"
    ),
    role_ids=["dealer", "helmsman", "pathfinder"],
    pulses_per_round=3,
    assertiveness=6,
    rounds=2,
)

# Conversation-focused: 3 agents with high meeting encouragement
CONVERSATION_TEST = TestConfig(
    name="Conversation Focus",
    description=(
        "3 agents, 2 pulses, assertiveness=4 (cooperative). "
        "Designed to encourage bilateral meetings."
    ),
    role_ids=["dealer", "helmsman", "beacon"],
    pulses_per_round=2,
    assertiveness=4,  # More cooperative = more likely to seek meetings
    max_meetings_per_round=5,
)

# Full 20 HoS (expensive! ~$4-5 per round)
FULL_WORLD_TEST = TestConfig(
    name="Full World: 20 HoS",
    description="All 20 heads of state. Full geopolitical simulation. ~$4-5 per round.",
    role_ids=[
        "dealer", "helmsman", "pathfinder", "beacon", "furnace",
        "forge", "sakura", "chip", "wellspring", "mariner",
        "lumiere", "sentinel", "scales", "havana", "pyro",
        "vanguard", "citadel", "spire", "vizier", "ponte_role",
    ],
    pulses_per_round=5,
    assertiveness=5,
    rounds=1,
)


# Registry of all configs
ALL_CONFIGS: dict[str, TestConfig] = {
    "duo": DUO_TEST,
    "five": FIVE_AGENT_TEST,
    "ten": TEN_COUNTRY_TEST,
    "columbia_team": COLUMBIA_TEAM_TEST,
    "two_rounds": TWO_ROUND_TEST,
    "conversation": CONVERSATION_TEST,
    "full_world": FULL_WORLD_TEST,
}
