"""SimRunManager — state machine for live simulation runs.

Controls the lifecycle: setup → pre_start → active (Phase A) → processing (Phase B)
→ inter_round → active (next round) → ... → completed.

All state transitions validated. Each method updates the DB and returns the new state.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from engine.config.settings import settings

logger = logging.getLogger(__name__)


# Valid state transitions
VALID_TRANSITIONS = {
    "setup": ["pre_start", "aborted"],
    "pre_start": ["active", "aborted"],
    "active": ["processing", "paused", "aborted"],
    "processing": ["inter_round", "active", "aborted"],  # inter_round or skip to next Phase A
    "inter_round": ["active", "aborted"],  # next round's Phase A
    "paused": ["active", "aborted"],
    "completed": [],
    "aborted": [],
}

# Phase sequence within a round
PHASE_SEQUENCE = ["A", "B", "inter_round"]


def _get_client():
    """Get Supabase service-role client."""
    from supabase import create_client
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def _get_run(client, sim_id: str) -> dict:
    """Fetch sim_run or raise."""
    result = client.table("sim_runs").select("*").eq("id", sim_id).single().execute()
    if not result.data:
        raise ValueError(f"SimRun {sim_id} not found")
    return result.data


def _update_run(client, sim_id: str, updates: dict) -> dict:
    """Update sim_run and return new state."""
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = client.table("sim_runs").update(updates).eq("id", sim_id).execute()
    return result.data[0] if result.data else {}


def _validate_transition(current_status: str, new_status: str):
    """Validate state transition is allowed."""
    allowed = VALID_TRANSITIONS.get(current_status, [])
    if new_status not in allowed:
        raise ValueError(f"Cannot transition from '{current_status}' to '{new_status}'. Allowed: {allowed}")


# ---------------------------------------------------------------------------
# Lifecycle Methods
# ---------------------------------------------------------------------------

def start_pre_start(sim_id: str) -> dict:
    """Move from setup → pre_start. Moderator prepares participant assignments."""
    client = _get_client()
    run = _get_run(client, sim_id)
    _validate_transition(run["status"], "pre_start")

    return _update_run(client, sim_id, {
        "status": "pre_start",
        "current_round": 0,
        "current_phase": "pre",
    })


def start_simulation(sim_id: str, phase_duration_seconds: int = 4800) -> dict:
    """Move from pre_start → active. Start Round 1 Phase A.

    Args:
        sim_id: SimRun ID
        phase_duration_seconds: Phase A duration (default 80 minutes = 4800s)
    """
    client = _get_client()
    run = _get_run(client, sim_id)
    _validate_transition(run["status"], "active")

    now = datetime.now(timezone.utc).isoformat()
    return _update_run(client, sim_id, {
        "status": "active",
        "current_round": 1,
        "current_phase": "A",
        "phase_started_at": now,
        "phase_duration_seconds": phase_duration_seconds,
        "started_at": now,
    })


def end_phase_a(sim_id: str) -> dict:
    """End Phase A → start Phase B (processing).

    Triggers: engine batch processing (caller must invoke engines separately).
    """
    client = _get_client()
    run = _get_run(client, sim_id)

    if run["current_phase"] != "A":
        raise ValueError(f"Cannot end Phase A — current phase is '{run['current_phase']}'")
    _validate_transition(run["status"], "processing")

    return _update_run(client, sim_id, {
        "status": "processing",
        "current_phase": "B",
        "phase_started_at": datetime.now(timezone.utc).isoformat(),
        "phase_duration_seconds": None,  # Phase B is not timed — runs until engines finish
    })


def end_phase_b(sim_id: str, inter_round_seconds: int = 600) -> dict:
    """End Phase B → start Inter-Round (unit movement window).

    Args:
        inter_round_seconds: Inter-round duration (default 10 minutes)
    """
    client = _get_client()
    run = _get_run(client, sim_id)

    if run["current_phase"] != "B":
        raise ValueError(f"Cannot end Phase B — current phase is '{run['current_phase']}'")
    _validate_transition(run["status"], "inter_round")

    return _update_run(client, sim_id, {
        "status": "inter_round",
        "current_phase": "inter_round",
        "phase_started_at": datetime.now(timezone.utc).isoformat(),
        "phase_duration_seconds": inter_round_seconds,
    })


def advance_round(sim_id: str, phase_duration_seconds: int = 3600) -> dict:
    """End Inter-Round → start next round Phase A.

    Args:
        phase_duration_seconds: Next Phase A duration (default 60 min for subsequent rounds)
    """
    client = _get_client()
    run = _get_run(client, sim_id)

    if run["current_phase"] != "inter_round":
        raise ValueError(f"Cannot advance round — current phase is '{run['current_phase']}'")

    new_round = run["current_round"] + 1
    if new_round > run.get("max_rounds", 8):
        # Simulation complete
        return _update_run(client, sim_id, {
            "status": "completed",
            "current_phase": "post",
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "phase_started_at": None,
            "phase_duration_seconds": None,
        })

    _validate_transition(run["status"], "active")

    return _update_run(client, sim_id, {
        "status": "active",
        "current_round": new_round,
        "current_phase": "A",
        "phase_started_at": datetime.now(timezone.utc).isoformat(),
        "phase_duration_seconds": phase_duration_seconds,
    })


def pause_simulation(sim_id: str) -> dict:
    """Pause the simulation. Timer stops."""
    client = _get_client()
    run = _get_run(client, sim_id)
    _validate_transition(run["status"], "paused")

    return _update_run(client, sim_id, {
        "status": "paused",
    })


def resume_simulation(sim_id: str) -> dict:
    """Resume a paused simulation. Timer restarts with remaining time."""
    client = _get_client()
    run = _get_run(client, sim_id)
    _validate_transition(run["status"], "active")

    return _update_run(client, sim_id, {
        "status": "active",
        "phase_started_at": datetime.now(timezone.utc).isoformat(),
    })


def extend_phase(sim_id: str, additional_seconds: int = 300) -> dict:
    """Add time to the current phase.

    Args:
        additional_seconds: Seconds to add (default 5 minutes)
    """
    client = _get_client()
    run = _get_run(client, sim_id)

    current_duration = run.get("phase_duration_seconds") or 0
    return _update_run(client, sim_id, {
        "phase_duration_seconds": current_duration + additional_seconds,
    })


def end_simulation(sim_id: str) -> dict:
    """End the simulation gracefully."""
    client = _get_client()
    return _update_run(client, sim_id, {
        "status": "completed",
        "current_phase": "post",
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "phase_started_at": None,
        "phase_duration_seconds": None,
    })


def abort_simulation(sim_id: str) -> dict:
    """Abort the simulation (emergency stop)."""
    client = _get_client()
    return _update_run(client, sim_id, {
        "status": "aborted",
        "current_phase": "post",
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "phase_started_at": None,
        "phase_duration_seconds": None,
    })


def set_mode(sim_id: str, auto_advance: bool = False, auto_approve: bool = False) -> dict:
    """Set automatic/manual mode flags."""
    client = _get_client()
    return _update_run(client, sim_id, {
        "auto_advance": auto_advance,
        "auto_approve": auto_approve,
    })


# ---------------------------------------------------------------------------
# Go-back Methods (moderator corrections)
# ---------------------------------------------------------------------------

def go_back_to_phase_a(sim_id: str, phase_duration_seconds: int = 3600) -> dict:
    """Go back to Phase A of the current round (e.g., from Phase B or inter-round)."""
    client = _get_client()
    run = _get_run(client, sim_id)

    if run["current_phase"] == "A":
        raise ValueError("Already in Phase A")

    return _update_run(client, sim_id, {
        "status": "active",
        "current_phase": "A",
        "phase_started_at": datetime.now(timezone.utc).isoformat(),
        "phase_duration_seconds": phase_duration_seconds,
    })


def restart_simulation(sim_id: str) -> dict:
    """Restart from Round 1 Phase A. Preserves template data, resets runtime state."""
    client = _get_client()

    return _update_run(client, sim_id, {
        "status": "pre_start",
        "current_round": 0,
        "current_phase": "pre",
        "phase_started_at": None,
        "phase_duration_seconds": None,
        "started_at": None,
        "completed_at": None,
    })


# ---------------------------------------------------------------------------
# Query Methods
# ---------------------------------------------------------------------------

def get_state(sim_id: str) -> dict:
    """Get current simulation state."""
    client = _get_client()
    return _get_run(client, sim_id)


def get_timer_info(sim_id: str) -> dict:
    """Get timer information for client-side countdown."""
    run = get_state(sim_id)
    return {
        "status": run["status"],
        "current_round": run["current_round"],
        "current_phase": run["current_phase"],
        "phase_started_at": run.get("phase_started_at"),
        "phase_duration_seconds": run.get("phase_duration_seconds"),
        "auto_advance": run.get("auto_advance", False),
        "auto_approve": run.get("auto_approve", False),
        "max_rounds": run.get("max_rounds", 8),
    }
