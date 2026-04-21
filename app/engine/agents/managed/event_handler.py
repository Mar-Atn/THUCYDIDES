"""Phase 3b — Event handler utilities for managed agent sessions.

Provides logging, transcript formatting, and observatory event writing
for the managed agent experiment. Separates I/O concerns from the
session manager's core event loop.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from engine.services.supabase import get_client

logger = logging.getLogger(__name__)


def write_agent_log_event(
    sim_run_id: str,
    country_code: str,
    round_num: int,
    event_type: str,
    title: str,
    description: str,
    metadata: dict | None = None,
) -> None:
    """Write an AI agent log entry to observatory_events.

    These events are visible in the Facilitator Dashboard and via
    the /api/sim/{id}/agent-log endpoint.
    """
    try:
        client = get_client()
        client.table("observatory_events").insert({
            "sim_run_id": sim_run_id,
            "event_type": "ai_agent_log",
            "category": event_type,
            "country_code": country_code,
            "round_num": round_num,
            "summary": f"{title}: {description[:500]}",
            "payload": metadata or {},
            "created_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
    except Exception as e:
        logger.warning("Failed to write agent log event: %s", e)


def log_transcript_to_observatory(
    sim_run_id: str,
    country_code: str,
    round_num: int,
    transcript: list[dict],
) -> None:
    """Write key transcript entries to observatory_events for observation."""
    for entry in transcript:
        etype = entry.get("type", "")

        if etype == "agent_message":
            write_agent_log_event(
                sim_run_id, country_code, round_num,
                event_type="agent_reasoning",
                title=f"AI Agent ({country_code}) reasoning",
                description=entry.get("content", "")[:2000],
            )

        elif etype == "tool_call":
            tool = entry.get("tool", "unknown")
            write_agent_log_event(
                sim_run_id, country_code, round_num,
                event_type="agent_tool_call",
                title=f"AI Agent ({country_code}) called {tool}",
                description=entry.get("result_preview", "")[:2000],
                metadata={"tool": tool, "input": entry.get("input", {})},
            )

        elif etype == "error":
            write_agent_log_event(
                sim_run_id, country_code, round_num,
                event_type="agent_error",
                title=f"AI Agent ({country_code}) error",
                description=entry.get("content", "")[:2000],
            )


def format_transcript_text(transcript: list[dict]) -> str:
    """Format transcript entries as readable text for logging/display."""
    lines: list[str] = []
    for entry in transcript:
        etype = entry.get("type", "")
        if etype == "user_message":
            lines.append(f"\n{'='*60}")
            lines.append(f"USER: {entry['content']}")
            lines.append(f"{'='*60}\n")
        elif etype == "agent_message":
            lines.append(f"AGENT: {entry['content']}")
        elif etype == "agent_thinking":
            lines.append(f"[thinking]: {entry['content'][:200]}...")
        elif etype == "tool_call":
            tool = entry.get("tool", "?")
            inp = json.dumps(entry.get("input", {}), indent=2)[:200]
            lines.append(f"  -> {tool}({inp})")
            preview = entry.get("result_preview", "")[:200]
            if preview:
                lines.append(f"  <- {preview}")
        elif etype == "error":
            lines.append(f"ERROR: {entry['content']}")
    return "\n".join(lines)


def extract_actions_from_transcript(transcript: list[dict]) -> list[dict]:
    """Extract submitted actions from transcript for verification."""
    actions: list[dict] = []
    for entry in transcript:
        if entry.get("type") == "tool_call" and entry.get("tool") in ("submit_action", "commit_action"):
            result_str = entry.get("result_preview", "{}")
            try:
                result = json.loads(result_str)
            except json.JSONDecodeError:
                result = {"raw": result_str}
            actions.append({
                "action_input": entry.get("input", {}),
                "result": result,
                "success": result.get("success", False),
            })
    return actions
