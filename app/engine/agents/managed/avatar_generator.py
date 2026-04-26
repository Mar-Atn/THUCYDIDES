"""Avatar Identity + Intent Note prompt generators.

These prompts instruct the Managed Agent to create context documents
for its conversation avatar. Pure functions — no DB calls.

Architecture: SPEC_M5_AVATAR_CONVERSATIONS.md
"""
from __future__ import annotations


def build_avatar_identity_prompt() -> str:
    """Return the prompt telling a Managed Agent to generate its Avatar Identity.

    The Avatar Identity is a compact (~500 word) document that the
    conversation avatar uses to represent the agent in ALL meetings.
    It covers who the agent is, their country, objectives, and
    knowledge of the SIM world.

    Returns:
        Prompt string for the Managed Agent.
    """
    return (
        'Generate your AVATAR IDENTITY — a compact document (~500 words) that your '
        'conversation avatar will use to represent you in ALL meetings.\n'
        '\n'
        'Your avatar is a lightweight agent that handles dialogue. It has NO access '
        'to your tools, memory, or strategic context — only this identity document '
        'and a per-meeting Intent Note.\n'
        '\n'
        'RECOMMENDED STRUCTURE (modify as you see fit — the goal is effective representation):\n'
        '\n'
        'WHO I AM:\n'
        '  [Your name, title, country, personality, communication style]\n'
        '\n'
        'MY COUNTRY:\n'
        '  [GDP, stability, military strength, nuclear/AI levels — headline numbers]\n'
        '  [Key strengths and vulnerabilities]\n'
        '\n'
        'MY OBJECTIVES:\n'
        '  [Top 3 strategic goals, current priorities]\n'
        '\n'
        'THE SIM WORLD (essential for natural conversation):\n'
        '  COUNTRIES: [All countries with sim_names you know about]\n'
        '  ORGANIZATIONS: [Key organizations with members]\n'
        '  KEY GEOGRAPHY: [Theaters, chokepoints, contested areas]\n'
        '  CURRENT CONFLICTS: [Who is at war, major tensions, recent events]\n'
        '  MY ALLIANCES: [Who you\'re allied with, who you trust, who you don\'t]\n'
        '\n'
        'The SIM WORLD section is critical — when a counterpart mentions '
        '"the Formosa situation" or "Western Treaty obligations", your avatar '
        'must know what they\'re talking about.\n'
        '\n'
        'Write this now using write_notes with key="avatar_identity".'
    )


def build_intent_note_prompt(
    counterpart_name: str,
    counterpart_country: str,
    counterpart_title: str,
    meeting_agenda: str,
) -> str:
    """Return the prompt for generating an Intent Note before a specific meeting.

    The Intent Note is a tactical briefing that the conversation avatar
    uses alongside the Avatar Identity for one specific meeting.

    Args:
        counterpart_name: Name of the person being met.
        counterpart_country: Country of the counterpart.
        counterpart_title: Title/role of the counterpart.
        meeting_agenda: Agenda or topic for the meeting.

    Returns:
        Prompt string for the Managed Agent.
    """
    return (
        'Generate an INTENT NOTE for your upcoming meeting.\n'
        '\n'
        f'MEETING WITH: {counterpart_name}, {counterpart_title} of {counterpart_country}\n'
        f'AGENDA: {meeting_agenda}\n'
        '\n'
        'Your conversation avatar will use ONLY this Intent Note (plus your Avatar '
        'Identity) to represent you. Write it carefully.\n'
        '\n'
        'RECOMMENDED STRUCTURE (adapt as you see fit — you own this):\n'
        '\n'
        'MY OBJECTIVE: [What you want to achieve — 1-2 sentences]\n'
        '\n'
        'APPROACH:\n'
        '- [Key tactics, arguments, proposals to bring up]\n'
        '- [What to probe / ask about]\n'
        '- [Concessions you\'re willing to make, if any]\n'
        '\n'
        'BOUNDARIES:\n'
        '- [What NOT to reveal]\n'
        '- [What NOT to agree to without further consultation]\n'
        '- [When to gracefully end the meeting]\n'
        '\n'
        'TONE: [How to sound — warm/cold, cautious/bold, formal/casual]\n'
        '\n'
        'KEY CONTEXT:\n'
        '- [Recent events relevant to this counterpart]\n'
        '- [Your shared history, past agreements, unresolved issues]\n'
        '- [Intelligence about their current position/needs]\n'
        '\n'
        'Write this now using write_notes with key="intent_note_[meeting_id]".'
    )
