"""Sim Run Manager — lifecycle service for sim_runs.

A SIM-RUN is one playthrough of a SCENARIO. Every per-round snapshot row
(``country_states_per_round``, ``unit_states_per_round``, ``agent_decisions``,
etc.) is keyed by ``sim_run_id`` so runs are isolated. Runs can coexist for
the same scenario: tests, comparison runs, calibration sweeps.

This module is the single entry point for creating, seeding, finalizing,
and listing runs. Engine code, test fixtures, and the Observatory all go
through these functions — no direct writes to ``sim_runs``.

Lifecycle:

    create_run(scenario, name) -> sim_run_id
        |
        v  status='setup'
    seed_round_zero(run_id) -> copies template R0 snapshot into the new run
        |
        v
    (engine executes rounds — resolve_round writes *_per_round rows)
        |
        v
    finalize_run(run_id, status='completed' | 'visible_for_review' | 'archived')
        |
        v
    list_runs() / get_run() for Observatory + tests
"""

from __future__ import annotations

import logging
from typing import Optional

from engine.services.supabase import get_client

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_VALID_STATUSES = {
    "setup",
    "active",
    "paused",
    "completed",
    "aborted",
    "archived",
    "visible_for_review",
}


def _resolve_scenario_id(client, scenario_code: str) -> str:
    """Look up a scenario's uuid by its human-readable code."""
    res = (
        client.table("sim_scenarios")
        .select("id")
        .eq("code", scenario_code)
        .limit(1)
        .execute()
    )
    if not res.data:
        raise ValueError(f"Scenario '{scenario_code}' not found")
    return res.data[0]["id"]


def _is_uuid(s: str) -> bool:
    return isinstance(s, str) and len(s) == 36 and s.count("-") == 4


def resolve_sim_run_id(run_or_scenario: str) -> str:
    """Normalize any accepted lookup key to an actual sim_run_id uuid.

    Accepts either:
      - an existing ``sim_run_id`` uuid (returned unchanged), or
      - a ``scenario_code`` like ``'start_one'`` (resolved to the legacy
        archived run for that scenario — the F1 migration placed every
        pre-F1 per-round row under this run).

    Raises ValueError if neither resolves.
    """
    client = get_client()
    # 1. Direct uuid lookup
    if _is_uuid(run_or_scenario):
        res = (
            client.table("sim_runs")
            .select("id")
            .eq("id", run_or_scenario)
            .limit(1)
            .execute()
        )
        if res.data:
            return run_or_scenario
    # 2. Scenario code → legacy archived run
    try:
        scenario_id = _resolve_scenario_id(client, run_or_scenario)
    except ValueError:
        raise ValueError(
            f"'{run_or_scenario}' is neither a known sim_run_id nor a scenario code"
        )
    legacy = _legacy_run_id_for_scenario(client, scenario_id)
    if legacy is None:
        raise ValueError(
            f"No archived (legacy) run found for scenario '{run_or_scenario}'. "
            f"Create and finalize a run with status='archived' first, or pass "
            f"an explicit sim_run_id."
        )
    return legacy


def get_scenario_id_for_run(sim_run_id: str) -> str:
    """Return the scenario_id that a sim_run belongs to. Cached in-process."""
    return get_run(sim_run_id)["scenario_id"]


def _legacy_run_id_for_scenario(client, scenario_id: str) -> Optional[str]:
    """Return the archived 'legacy' run that holds the scenario's template R0.

    After the F1 migration, every historical per-round row for a scenario
    lives under the single archived run created by ``sim_run_foundation_v1``.
    That run is the authoritative source for R0 template snapshots until we
    introduce explicit scenario template_run_id pointers.
    """
    res = (
        client.table("sim_runs")
        .select("id,created_at")
        .eq("scenario_id", scenario_id)
        .eq("status", "archived")
        .order("created_at", desc=False)
        .limit(1)
        .execute()
    )
    return res.data[0]["id"] if res.data else None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def create_run(
    scenario_code: str,
    name: str,
    description: Optional[str] = None,
    seed: Optional[int] = None,
    max_rounds: int = 8,
) -> str:
    """Create a new sim_run bound to a scenario. Returns the new run's uuid.

    The run starts in status ``setup``. Caller should invoke
    ``seed_round_zero(run_id)`` to copy template state before running any
    rounds, then ``finalize_run`` when done.
    """
    client = get_client()
    scenario_id = _resolve_scenario_id(client, scenario_code)
    payload = {
        "name": name,
        "description": description,
        "scenario_id": scenario_id,
        "status": "setup",
        "seed": seed,
        "max_rounds": max_rounds,
        "current_round": 0,
        "current_phase": "pre",
        "run_config": {},
    }
    res = client.table("sim_runs").insert(payload).execute()
    if not res.data:
        raise RuntimeError(f"Failed to create sim_run for scenario '{scenario_code}'")
    run_id = res.data[0]["id"]
    logger.info("Created sim_run %s for scenario %s (%s)", run_id, scenario_code, name)
    return run_id


def seed_round_zero(sim_run_id: str, source_run_id: Optional[str] = None) -> dict:
    """Copy template R0 snapshot into the new run.

    Copies country_states, unit_states, and global_state rows at ``round_num=0``
    from ``source_run_id`` (or, if omitted, the archived legacy run for the
    same scenario) into ``sim_run_id``. Every copied row is re-keyed:
    ``sim_run_id`` replaced, ``id`` dropped (new uuid assigned).

    Returns a dict of copy counts for logging.
    """
    client = get_client()
    run = get_run(sim_run_id)
    scenario_id = run["scenario_id"]

    if source_run_id is None:
        source_run_id = _legacy_run_id_for_scenario(client, scenario_id)
        if source_run_id is None:
            raise RuntimeError(
                f"No legacy archived run found for scenario {scenario_id}. "
                f"Seed the template first or pass source_run_id explicitly."
            )
    if source_run_id == sim_run_id:
        raise ValueError("source_run_id must differ from sim_run_id")

    counts = {"country_states": 0, "unit_states": 0, "global_state": 0}

    # Country states
    cs = (
        client.table("country_states_per_round")
        .select("*")
        .eq("sim_run_id", source_run_id)
        .eq("round_num", 0)
        .execute()
    )
    if cs.data:
        rows = [_rekey_row(r, sim_run_id) for r in cs.data]
        for batch in _batched(rows, 50):
            client.table("country_states_per_round").upsert(
                batch, on_conflict="sim_run_id,round_num,country_code"
            ).execute()
        counts["country_states"] = len(rows)

    # Unit states
    us = (
        client.table("unit_states_per_round")
        .select("*")
        .eq("sim_run_id", source_run_id)
        .eq("round_num", 0)
        .execute()
    )
    if us.data:
        rows = [_rekey_row(r, sim_run_id) for r in us.data]
        for batch in _batched(rows, 200):
            client.table("unit_states_per_round").upsert(
                batch, on_conflict="sim_run_id,round_num,unit_code"
            ).execute()
        counts["unit_states"] = len(rows)

    # Global state (singleton per round)
    gs = (
        client.table("global_state_per_round")
        .select("*")
        .eq("sim_run_id", source_run_id)
        .eq("round_num", 0)
        .execute()
    )
    if gs.data:
        rows = [_rekey_row(r, sim_run_id) for r in gs.data]
        client.table("global_state_per_round").upsert(
            rows, on_conflict="sim_run_id,round_num"
        ).execute()
        counts["global_state"] = len(rows)

    logger.info(
        "Seeded R0 into run %s from source %s: %s", sim_run_id, source_run_id, counts
    )
    return counts


def finalize_run(
    sim_run_id: str,
    status: str = "completed",
    notes: Optional[str] = None,
) -> None:
    """Mark a run as finished. Status must be one of the terminal lifecycle values.

    Common terminal statuses:
        - ``completed``: run finished normally, keep for records
        - ``visible_for_review``: keep AND expose in the Observatory selector
        - ``archived``: keep but hide from default Observatory lists
        - ``aborted``: run was interrupted / failed
    """
    if status not in _VALID_STATUSES:
        raise ValueError(f"Invalid status '{status}'. Must be one of {_VALID_STATUSES}")
    client = get_client()
    payload: dict = {"status": status, "finalized_at": "now()"}
    if notes:
        # notes are appended to description so we don't clobber existing text
        run = get_run(sim_run_id)
        existing = run.get("description") or ""
        payload["description"] = f"{existing}\n[final] {notes}" if existing else f"[final] {notes}"
    # Supabase Python client doesn't expand 'now()' — use explicit timestamp
    from datetime import datetime, timezone
    payload["finalized_at"] = datetime.now(timezone.utc).isoformat()
    client.table("sim_runs").update(payload).eq("id", sim_run_id).execute()
    logger.info("Finalized sim_run %s -> %s", sim_run_id, status)


def get_run(sim_run_id: str) -> dict:
    """Return a single sim_run row by id. Raises if not found."""
    client = get_client()
    res = (
        client.table("sim_runs")
        .select("*")
        .eq("id", sim_run_id)
        .limit(1)
        .execute()
    )
    if not res.data:
        raise ValueError(f"sim_run '{sim_run_id}' not found")
    return res.data[0]


def list_runs(
    scenario_code: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
) -> list[dict]:
    """List sim_runs, optionally filtered by scenario + status.

    Used by the Observatory selector and by tests. Newest first.
    """
    client = get_client()
    q = client.table("sim_runs").select(
        "id,name,description,scenario_id,status,current_round,max_rounds,"
        "seed,created_at,started_at,completed_at,finalized_at"
    )
    if scenario_code is not None:
        scenario_id = _resolve_scenario_id(client, scenario_code)
        q = q.eq("scenario_id", scenario_id)
    if status is not None:
        q = q.eq("status", status)
    res = q.order("created_at", desc=True).limit(limit).execute()
    return res.data or []


# ---------------------------------------------------------------------------
# Internal plumbing
# ---------------------------------------------------------------------------


def _rekey_row(row: dict, new_sim_run_id: str) -> dict:
    """Strip the original PK and replace sim_run_id for insertion into a new run."""
    out = {k: v for k, v in row.items() if k != "id"}
    out["sim_run_id"] = new_sim_run_id
    return out


def _batched(items, size):
    for i in range(0, len(items), size):
        yield items[i : i + size]
