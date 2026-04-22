"""Meta-awareness context for Layer 1 system prompt (~1,000-1,500 tokens).

Tells the agent HOW the simulation interface works: pulse system,
available tools, busy state, resource limits, time awareness,
memory discipline, and information scoping.
"""
from __future__ import annotations


def build_meta_context(
    round_num: int,
    total_rounds: int,
    pulse_num: int,
    total_pulses: int,
    meetings_remaining: int,
    intel_cards_remaining: int,
    mandatory_submitted: dict,  # {budget: bool, tariffs: bool, ...}
    tools_summary: list[str],   # tool names with descriptions
) -> str:
    """Build the meta-awareness section for per-pulse injection.

    This is NOT part of the immutable Layer 1 system prompt. It is sent
    per-pulse by the orchestrator so the agent has current resource state.

    Args:
        round_num: Current round (1-indexed).
        total_rounds: Total rounds in the simulation.
        pulse_num: Current pulse within this round (1-indexed).
        total_pulses: Total pulses per round.
        meetings_remaining: Meeting slots left this round.
        intel_cards_remaining: Intelligence cards left (lifetime).
        mandatory_submitted: Which mandatory inputs are done.
        tools_summary: List of "tool_name — description" strings.

    Returns:
        Formatted meta-awareness text (~1,000-1,500 tokens).
    """
    # ── Pulse & Time ──────────────────────────────────────────────
    pulse_section = (
        f"## SITUATION AWARENESS\n\n"
        f"**Round {round_num} of {total_rounds}** | "
        f"Each round ≈ 6 months of scenario time.\n"
        f"**This is update {pulse_num} of {total_pulses}.** "
    )
    if pulse_num <= 2:
        pulse_section += "Early in the round — time to gather information and plan."
    elif pulse_num >= total_pulses - 1:
        pulse_section += "Late in the round — submit remaining actions and mandatory inputs NOW."
    else:
        pulse_section += "Mid-round — balance information gathering with decisive action."

    # ── Resource Dashboard ────────────────────────────────────────
    mandatory_lines = []
    for key, done in mandatory_submitted.items():
        status = "SUBMITTED" if done else "PENDING"
        mandatory_lines.append(f"  - {key}: {status}")
    mandatory_block = "\n".join(mandatory_lines) if mandatory_lines else "  - (none this pulse)"

    resource_section = (
        f"\n\n### Your Resources This Round\n\n"
        f"- **Meetings remaining:** {meetings_remaining}\n"
        f"- **Intelligence cards remaining:** {intel_cards_remaining} (lifetime — never recover)\n"
        f"- **Mandatory inputs:**\n{mandatory_block}\n\n"
        f"Unsubmitted mandatory inputs at round end → parliament imposes defaults "
        f"(budget cuts, no tariff changes). Act before the last pulse."
    )

    # ── Tools ─────────────────────────────────────────────────────
    tool_lines = "\n".join(f"- `{t}`" for t in tools_summary)
    tools_section = (
        f"\n\n### Your Tools\n\n"
        f"{tool_lines}\n\n"
        f"Use situation tools BEFORE acting. One well-informed action beats three blind ones."
    )

    # ── Diplomatic Consideration ─────────────────────────────────
    if pulse_num <= 2 and meetings_remaining > 0:
        diplomacy_nudge = (
            "\n\n### Diplomatic Opportunities\n\n"
            f"You have **{meetings_remaining} meeting slots** remaining this round. "
            "Consider: is there a leader you should talk to? Meetings are how deals "
            "get made — alliances formed, ceasefires negotiated, sanctions coordinated. "
            "Use `request_meeting(target_country, agenda)` to invite someone."
        )
    elif pulse_num > 2 and meetings_remaining > 0:
        diplomacy_nudge = (
            "\n\n### Diplomatic Window Closing\n\n"
            f"You have **{meetings_remaining} meeting slots** left. "
            "If you need to talk to someone this round, do it now."
        )
    else:
        diplomacy_nudge = ""

    # ── Busy State & Scheduling ───────────────────────────────────
    busy_section = (
        "\n\n### Busy State\n\n"
        "When you are in a meeting, you are BUSY — incoming events queue until "
        "the meeting ends. You miss updates while talking. Budget your meeting "
        "time carefully. Declining a meeting is a valid strategic choice."
    )

    # ── Memory ────────────────────────────────────────────────────
    memory_section = (
        "\n\n### Memory Discipline\n\n"
        "You have NO memory between pulses except what you explicitly save "
        "with `write_notes`. At the start of each pulse, read your notes. "
        "At the end, update them. What you don't write down, you FORGET.\n\n"
        "Recommended keys: strategic_plan, observations, relationships, "
        "open_threads, character_traits."
    )

    # ── Information Scoping ───────────────────────────────────────
    scoping_section = (
        "\n\n### Information Scoping\n\n"
        "You see ONLY what a real player in your position would see:\n"
        "- Public events (observatory feed)\n"
        "- Your own country data (full detail)\n"
        "- Other countries (public data only — use intelligence for secrets)\n"
        "- Your private intel reports and artefacts\n"
        "- Meeting conversations you participated in\n\n"
        "You do NOT have access to other leaders' private notes, "
        "internal deliberations, or undisclosed covert operations."
    )

    return (
        pulse_section
        + resource_section
        + diplomacy_nudge
        + tools_section
        + busy_section
        + memory_section
        + scoping_section
    )


# ── Static Layer 1 meta section (for immutable system prompt) ─────────

META_AWARENESS_STATIC = """## HOW YOU INTERACT WITH THE SIMULATION

### Pulse System

You do NOT act continuously. You receive a fixed number of updates ("pulses") per round.
Each pulse brings: new events, pending proposals, resource status, and a prompt to act.
Between pulses, you do not exist. Budget your actions across pulses — don't front-load.

### Busy State

When in a meeting, you are BUSY. Incoming events queue until the meeting ends.
You miss updates while talking. This is the same time-pressure tradeoff humans face.
Declining a meeting is a valid strategic choice. Don't accept every invitation.

### Memory

You have NO memory between sessions except what you save with `write_notes`.
Start every pulse by reading your notes. End every pulse by updating them.
What you don't write down, you WILL forget. Be specific and concrete.

### Information Scoping

You see ONLY what a real player in your position would see:
- Public events, your own country (full detail), other countries (public only)
- Your private intel reports, artefacts, and meeting transcripts
- You do NOT see other leaders' notes, hidden ops, or private data

Intelligence tools let you probe deeper — but results may be inaccurate.
Trust but verify. Cross-reference multiple sources."""


def build_meta_awareness_static() -> str:
    """Return the static meta-awareness section for Layer 1 system prompt.

    This covers the structural rules (pulse system, busy state, memory,
    information scoping) that don't change per pulse.

    Returns:
        Formatted text (~500-700 tokens).
    """
    return META_AWARENESS_STATIC.strip()
