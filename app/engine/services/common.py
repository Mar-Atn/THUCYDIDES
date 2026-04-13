"""Shared helpers for engine services.

Eliminates duplication of _get_scenario_id, _write_event, and safe
type-conversion helpers across all engine modules.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


# ── Safe type conversions (avoids 0-is-falsy bug) ─────────────────────────

def safe_int(val, default: int = 0) -> int:
    """Convert to int, treating only None as missing (not 0)."""
    return int(val) if val is not None else default


def safe_float(val, default: float = 0.0) -> float:
    """Convert to float, treating only None as missing (not 0.0)."""
    return float(val) if val is not None else default


# ── Observatory helpers ────────────────────────────────────────────────────

def get_scenario_id(client, sim_run_id: str) -> str | None:
    """Look up scenario_id for a sim_run."""
    try:
        r = client.table("sim_runs").select("scenario_id").eq("id", sim_run_id).limit(1).execute()
        return r.data[0]["scenario_id"] if r.data else None
    except Exception:
        return None


def write_event(
    client,
    sim_run_id: str,
    scenario_id: str | None,
    round_num: int,
    country_code: str,
    event_type: str,
    summary: str,
    payload: dict,
) -> None:
    """Write an observatory event. Silently skips if no scenario_id."""
    if not scenario_id:
        return
    try:
        client.table("observatory_events").insert({
            "sim_run_id": sim_run_id,
            "scenario_id": scenario_id,
            "round_num": round_num,
            "event_type": event_type,
            "country_code": country_code,
            "summary": summary,
            "payload": payload,
        }).execute()
    except Exception as e:
        logger.debug("event write failed: %s", e)
