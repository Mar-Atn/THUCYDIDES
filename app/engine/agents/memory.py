"""Cognitive block management — create, read, update, version history.

Implements Block 3 (Memory) and Block 4 (Goals) management with
versioning and inspection support.

Source: SEED_E5 Section 2, DET_C1 C6 (CognitiveState)
"""

from __future__ import annotations

import copy
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class CognitiveState:
    """Full cognitive state of an AI participant (4 blocks + version history)."""

    def __init__(self, role_id: str):
        self.role_id = role_id
        self.version = 0
        self._history: list[dict] = []

        # Block 1: Rules (immutable per SIM)
        self.block1_rules: str = ""

        # Block 2: Identity (generated once, rarely updated)
        self.block2_identity: str = ""

        # Block 3: Memory (updated continuously)
        self.block3_memory: dict = {
            "immediate": "",
            "round_history": [],
            "strategic": "",
            "relationships": {},
            "conversations_this_round": [],
            "decisions_this_round": [],
        }

        # Block 4: Goals & Strategy (updated per round + events)
        self.block4_goals: dict = {
            "objectives": [],
            "current_strategy": "",
            "contingencies": "",
            "priority_assessment": {},
        }

    def snapshot(self) -> dict:
        """Return current state as a dict (for inspection)."""
        return {
            "version": self.version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "role_id": self.role_id,
            "block1_rules": self.block1_rules,
            "block2_identity": self.block2_identity,
            "block3_memory": copy.deepcopy(self.block3_memory),
            "block4_goals": copy.deepcopy(self.block4_goals),
        }

    def save_version(self, reason: str = ""):
        """Save current state to history and increment version."""
        snap = self.snapshot()
        snap["reason"] = reason
        self._history.append(snap)
        self.version += 1
        logger.debug("Cognitive state v%d saved for %s: %s", self.version, self.role_id, reason)

    def get_history(self) -> list[dict]:
        """Return all saved versions."""
        return list(self._history)

    def get_version(self, version: int) -> dict | None:
        """Return a specific version."""
        for snap in self._history:
            if snap["version"] == version:
                return snap
        return None

    # ------------------------------------------------------------------
    # Block 1: Rules
    # ------------------------------------------------------------------

    def set_rules(self, rules_text: str):
        """Set Block 1 (rules). Called once at initialization."""
        self.block1_rules = rules_text

    # ------------------------------------------------------------------
    # Block 2: Identity
    # ------------------------------------------------------------------

    def set_identity(self, identity_text: str):
        """Set Block 2 (identity). Called once at initialization."""
        self.block2_identity = identity_text
        self.save_version("identity_generated")

    # ------------------------------------------------------------------
    # Block 3: Memory
    # ------------------------------------------------------------------

    def update_immediate(self, text: str):
        """Update immediate memory (last event/conversation)."""
        self.block3_memory["immediate"] = text

    def add_conversation(self, counterpart: str, summary: str, trust_change: float = 0.0):
        """Record a conversation in memory."""
        self.block3_memory["conversations_this_round"].append({
            "with": counterpart,
            "summary": summary,
            "trust_change": trust_change,
        })
        # Update relationship
        old = self.block3_memory["relationships"].get(counterpart, 0.0)
        self.block3_memory["relationships"][counterpart] = max(-1.0, min(1.0, old + trust_change))
        self.update_immediate(f"Spoke with {counterpart}: {summary}")
        self.save_version(f"conversation_with_{counterpart}")

    def add_decision(self, action_type: str, summary: str):
        """Record a decision in memory."""
        self.block3_memory["decisions_this_round"].append({
            "action": action_type,
            "summary": summary,
        })

    def end_round(self, round_num: int, round_summary: str):
        """End-of-round memory management. Compress and archive."""
        # Archive this round
        self.block3_memory["round_history"].append({
            "round": round_num,
            "summary": round_summary,
            "conversations": list(self.block3_memory["conversations_this_round"]),
            "decisions": list(self.block3_memory["decisions_this_round"]),
        })
        # Reset round-level accumulators
        self.block3_memory["conversations_this_round"] = []
        self.block3_memory["decisions_this_round"] = []
        self.block3_memory["immediate"] = ""
        self.save_version(f"round_{round_num}_end")

    def set_relationships(self, relationships: dict[str, float]):
        """Set initial relationships."""
        self.block3_memory["relationships"] = dict(relationships)

    def get_memory_text(self) -> str:
        """Build Block 3 as text for LLM context."""
        lines = ["## Memory\n"]

        # Immediate
        if self.block3_memory["immediate"]:
            lines.append(f"**Just now:** {self.block3_memory['immediate']}\n")

        # This round conversations
        convos = self.block3_memory["conversations_this_round"]
        if convos:
            lines.append("**This round conversations:**")
            for c in convos:
                lines.append(f"- With {c['with']}: {c['summary']}")
            lines.append("")

        # This round decisions
        decisions = self.block3_memory["decisions_this_round"]
        if decisions:
            lines.append("**My decisions this round:**")
            for d in decisions:
                lines.append(f"- {d['action']}: {d['summary']}")
            lines.append("")

        # Past rounds (most recent first, compressed for older)
        history = self.block3_memory["round_history"]
        for entry in reversed(history[-3:]):  # last 3 rounds in detail
            lines.append(f"**Round {entry['round']}:** {entry['summary']}")
        for entry in reversed(history[:-3]):  # older rounds compressed
            lines.append(f"R{entry['round']}: {entry.get('summary', '')[:100]}")

        # Key relationships
        rels = self.block3_memory["relationships"]
        if rels:
            lines.append("\n**Relationships:**")
            for role, score in sorted(rels.items(), key=lambda x: -abs(x[1])):
                if abs(score) > 0.1:
                    label = "ally" if score > 0.5 else "friendly" if score > 0.2 else "neutral" if abs(score) <= 0.2 else "tense" if score > -0.5 else "hostile"
                    lines.append(f"- {role}: {label} ({score:+.1f})")

        # Strategic memory
        if self.block3_memory["strategic"]:
            lines.append(f"\n**Key strategic facts:** {self.block3_memory['strategic']}")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Block 4: Goals
    # ------------------------------------------------------------------

    def set_goals(self, objectives: list[dict], strategy: str = "", contingencies: str = ""):
        """Set Block 4 goals."""
        self.block4_goals["objectives"] = objectives
        self.block4_goals["current_strategy"] = strategy
        self.block4_goals["contingencies"] = contingencies
        self.save_version("goals_set")

    def update_strategy(self, new_strategy: str, priority_assessment: dict = None):
        """Update strategic priorities."""
        self.block4_goals["current_strategy"] = new_strategy
        if priority_assessment:
            self.block4_goals["priority_assessment"] = priority_assessment
        self.save_version("strategy_updated")

    def get_goals_text(self) -> str:
        """Build Block 4 as text for LLM context."""
        lines = ["## Goals & Strategy\n"]

        for obj in self.block4_goals["objectives"]:
            urgency = obj.get("urgency", "normal")
            status = obj.get("status", "")
            lines.append(f"- **{obj['name']}** [{urgency}] {status}")

        if self.block4_goals["current_strategy"]:
            lines.append(f"\n**Current strategy:** {self.block4_goals['current_strategy']}")

        if self.block4_goals["priority_assessment"]:
            lines.append("\n**Priority assessment:**")
            for k, v in self.block4_goals["priority_assessment"].items():
                lines.append(f"- {k}: {v}")

        if self.block4_goals["contingencies"]:
            lines.append(f"\n**Contingencies:** {self.block4_goals['contingencies']}")

        return "\n".join(lines)
