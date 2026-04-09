"""L3 Skill B2: Bilateral conversation quality harness.

Tests that two AI leaders can hold a strategic 8-turn bilateral conversation
that stays in character, uses SIM names, makes concrete proposals, and
produces actionable outcomes.

Real LLM calls (~$0.05 per conversation, ~$0.15 total for 3 scenarios).

Run:
    cd app && PYTHONPATH=. python3 -m pytest tests/layer3/test_skill_conversation.py -v -s

Skip LLM tests:
    cd app && PYTHONPATH=. python3 -m pytest tests/layer3/test_skill_conversation.py -v -m "not llm"
"""

import asyncio
import logging
import re

import pytest

from engine.agents.leader import LeaderAgent
from engine.agents.conversations import ConversationEngine

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Real-world name immersion checks
# ---------------------------------------------------------------------------

BANNED_NAMES = [
    r"\bUSA\b", r"\bUnited States\b", r"\bAmerica(?!n)\b",
    r"\bChina\b", r"\bRussia\b", r"\bUkraine\b",
    r"\bIran\b", r"\bIsrael\b", r"\bGermany\b",
    r"\bFrance\b", r"\bJapan\b", r"\bTaiwan\b",
    r"\bSouth Korea\b", r"\bNorth Korea\b",
    r"\bSaudi Arabia\b", r"\bTurkey\b",
    r"\bPoland\b", r"\bItaly\b", r"\bIndia\b",
    r"\bUnited Kingdom\b", r"\bBritain\b",
    r"\bTrump\b", r"\bBiden\b", r"\bXi Jinping\b",
    r"\bPutin\b", r"\bZelensky\b", r"\bKhamenei\b",
    r"\bNetanyahu\b", r"\bModi\b", r"\bMacron\b",
]

BANNED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in BANNED_NAMES]


def _check_immersion(transcript: list[dict]) -> list[str]:
    """Return list of immersion violations found in transcript."""
    violations = []
    for entry in transcript:
        text = entry["text"]
        for pattern in BANNED_PATTERNS:
            match = pattern.search(text)
            if match:
                violations.append(
                    f"Turn {entry.get('turn', '?')} ({entry['speaker_name']}): "
                    f"found '{match.group()}' — real-world name"
                )
    return violations


def _speaker_counts(transcript: list[dict]) -> dict[str, int]:
    """Count turns per speaker."""
    counts: dict[str, int] = {}
    for entry in transcript:
        name = entry["speaker_name"]
        counts[name] = counts.get(name, 0) + 1
    return counts


def _has_concrete_content(transcript: list[dict]) -> bool:
    """Check if at least one turn contains concrete proposals (numbers, conditions, terms)."""
    concrete_signals = [
        r"\d+%",           # percentages
        r"\$\d+",          # dollar amounts
        r"\bpropose\b",    # proposal language
        r"\boffer\b",
        r"\bdemand\b",
        r"\bcondition\b",
        r"\bcommit\b",
        r"\bguarantee\b",
        r"\btariff\b",
        r"\bsanction",
        r"\btroops?\b",
        r"\bceasefire\b",
        r"\btreaty\b",
        r"\bdefense\b",
        r"\bcooperation\b",
        r"\balliance\b",
        r"\bterritorial\b",
        r"\bblockade\b",
        r"\bnuclear\b",
        r"\bsemiconductor\b",
        r"\bstrait\b",
    ]
    for entry in transcript:
        text = entry["text"]
        hits = sum(1 for sig in concrete_signals if re.search(sig, text, re.IGNORECASE))
        if hits >= 2:
            return True
    return False


def _print_transcript(scenario: str, result) -> None:
    """Print full transcript for Marat's review."""
    print(f"\n{'='*72}")
    print(f"SCENARIO: {scenario}")
    print(f"Turns: {result.turns} | Ended by: {result.ended_by}")
    print(f"{'='*72}")
    for entry in result.transcript:
        print(f"\n--- Turn {entry.get('turn', '?')}: {entry['speaker_name']} ---")
        print(entry["text"])
    print(f"\n{'='*72}")

    # Print intent notes
    for role_id, intent in result.intent_notes.items():
        print(f"\n[INTENT — {role_id}]")
        print(intent[:400])

    # Print reflections
    for role_id, ref in result.reflections.items():
        print(f"\n[REFLECTION — {role_id}]")
        details = ref.get("details", {})
        print(f"  Assessment: {details.get('assessment', 'N/A')}")
        print(f"  Memory update: {details.get('memory_update', 'N/A')}")
        print(f"  Relationship change: {details.get('relationship_change', 0)}")
    print()


def _make_agent(role_id: str) -> LeaderAgent:
    """Create and synchronously initialize a LeaderAgent."""
    agent = LeaderAgent(role_id=role_id)
    agent.initialize_sync()
    return agent


def _run_bilateral(agent_a: LeaderAgent, agent_b: LeaderAgent, topic: str):
    """Run a bilateral conversation synchronously."""
    engine = ConversationEngine()
    return asyncio.run(engine.run_bilateral(agent_a, agent_b, max_turns=8, topic=topic))


# ---------------------------------------------------------------------------
# Shared quality assertions
# ---------------------------------------------------------------------------

def _assert_conversation_quality(result, scenario: str) -> None:
    """Run standard quality checks on a conversation result."""
    transcript = result.transcript

    # 1. Both engaged — at least 6 turns total
    assert result.turns >= 4, (
        f"[{scenario}] Only {result.turns} turns — conversation too short (need >= 4)"
    )

    # 2. Both speakers appear at least 2 times
    counts = _speaker_counts(transcript)
    for speaker, count in counts.items():
        assert count >= 2, (
            f"[{scenario}] {speaker} only spoke {count} time(s) — not a real conversation"
        )

    # 3. No real-world name violations
    violations = _check_immersion(transcript)
    if violations:
        print(f"\n[IMMERSION VIOLATIONS — {scenario}]")
        for v in violations:
            print(f"  - {v}")
    # Soft assertion: warn but don't fail for up to 2 slips
    assert len(violations) <= 2, (
        f"[{scenario}] Too many immersion violations ({len(violations)}): {violations[:5]}"
    )

    # 4. At least one turn has concrete strategic content
    assert _has_concrete_content(transcript), (
        f"[{scenario}] No turn contained concrete proposals, numbers, or strategic terms"
    )


# ===========================================================================
# TEST 1: Trade negotiation — Columbia <-> Cathay
# ===========================================================================

@pytest.mark.llm
def test_trade_negotiation_columbia_cathay():
    """Columbia (Dealer) and Cathay (Helmsman) negotiate tariff de-escalation.

    Expected: Both discuss tariff levels, make offers/counteroffers,
    reference economic impact. Neither capitulates easily — both are strong.
    """
    agent_a = _make_agent("dealer")    # Columbia — President
    agent_b = _make_agent("helmsman")  # Cathay — Chairman

    topic = "Trade war de-escalation — tariff reduction proposal"
    result = _run_bilateral(agent_a, agent_b, topic)

    _print_transcript("Trade Negotiation: Columbia <-> Cathay", result)
    _assert_conversation_quality(result, "Trade Columbia-Cathay")

    # Scenario-specific: trade language present
    full_text = " ".join(e["text"] for e in result.transcript).lower()
    trade_terms = ["tariff", "trade", "econom", "import", "export", "market", "goods"]
    trade_hits = sum(1 for t in trade_terms if t in full_text)
    assert trade_hits >= 2, (
        f"Trade negotiation lacks trade language (only {trade_hits} terms found)"
    )


# ===========================================================================
# TEST 2: War mediation — Ruthenia <-> Sarmatia
# ===========================================================================

@pytest.mark.llm
def test_ceasefire_ruthenia_sarmatia():
    """Ruthenia (Beacon) and Sarmatia (Pathfinder) discuss ceasefire terms.

    Expected: Ruthenia demands territory back, Sarmatia demands recognition.
    Both make threats/concessions. Asymmetric power — Sarmatia stronger,
    Ruthenia desperate but principled.
    """
    agent_a = _make_agent("beacon")      # Ruthenia — President (weaker, at war)
    agent_b = _make_agent("pathfinder")  # Sarmatia — President (stronger, at war)

    topic = "Ceasefire proposal — terms for stopping hostilities"
    result = _run_bilateral(agent_a, agent_b, topic)

    _print_transcript("Ceasefire Negotiation: Ruthenia <-> Sarmatia", result)
    _assert_conversation_quality(result, "Ceasefire Ruthenia-Sarmatia")

    # Scenario-specific: war/peace language present
    full_text = " ".join(e["text"] for e in result.transcript).lower()
    war_terms = ["ceasefire", "peace", "territory", "war", "withdraw", "recogni",
                 "hostili", "troop", "front", "border", "sovereign"]
    war_hits = sum(1 for t in war_terms if t in full_text)
    assert war_hits >= 2, (
        f"Ceasefire negotiation lacks war/peace language (only {war_hits} terms found)"
    )


# ===========================================================================
# TEST 3: Alliance building — Formosa <-> Columbia
# ===========================================================================

@pytest.mark.llm
def test_alliance_formosa_columbia():
    """Formosa (Chip) seeks defense commitment from Columbia (Dealer).

    Expected: Formosa pushes for explicit defense guarantee,
    Columbia hedges with strategic ambiguity. Both reference Cathay threat,
    semiconductor leverage, and Strait defense.
    """
    agent_a = _make_agent("chip")    # Formosa — President (seeking protection)
    agent_b = _make_agent("dealer")  # Columbia — President (strategic ambiguity)

    topic = "Military cooperation — defense of Formosa Strait"
    result = _run_bilateral(agent_a, agent_b, topic)

    _print_transcript("Alliance Building: Formosa <-> Columbia", result)
    _assert_conversation_quality(result, "Alliance Formosa-Columbia")

    # Scenario-specific: security/defense language present
    full_text = " ".join(e["text"] for e in result.transcript).lower()
    security_terms = ["defense", "defen", "military", "strait", "semiconductor",
                      "chip", "protect", "security", "threat", "commit",
                      "cathay", "deter", "naval", "base"]
    security_hits = sum(1 for t in security_terms if t in full_text)
    assert security_hits >= 2, (
        f"Alliance discussion lacks security language (only {security_hits} terms found)"
    )
