"""Persistence layer for SIM run results.

Saves RoundReport data to Supabase. All functions are best-effort:
DB errors are logged but never raised — a round must complete even if
persistence fails.

Tables written:
    - sim_runs           (created via create_test_sim_run)
    - round_reports      (one row per round)
    - agent_actions      (one row per action)
    - agent_conversations (one row per bilateral)
    - agent_transactions (one row per deal)
    - agent_reflections  (one row per role per round)

Test runs are prefixed with "test_" in the name and carry a
{"test_run": true} flag in sim_runs.config.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, TYPE_CHECKING

from engine.services.supabase import get_client

if TYPE_CHECKING:
    from engine.agents.runner import RoundReport

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# SIM RUN
# ---------------------------------------------------------------------------

def create_test_sim_run(name: str = "unmanned_test", max_rounds: int = 6) -> Optional[str]:
    """Create a new sim_runs row for a test run and return its ID.

    Prefixes name with "test_" and timestamp so it is identifiable. Marks
    config with {"test_run": true}. Returns None if DB unavailable.
    """
    try:
        client = get_client()
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        full_name = f"test_{name}_{ts}"
        row = {
            "name": full_name,
            "status": "running",
            "current_round": 0,
            "current_phase": "active",
            "config": {"test_run": True, "source": "unmanned_runner"},
            "max_rounds": max_rounds,
            "started_at": datetime.now(timezone.utc).isoformat(),
        }
        result = client.table("sim_runs").insert(row).execute()
        if result.data:
            sim_run_id = result.data[0]["id"]
            logger.info("Created test sim_run: %s (id=%s)", full_name, sim_run_id)
            return sim_run_id
    except Exception as e:
        logger.error("Failed to create test sim_run: %s", e)
    return None


def mark_sim_run_complete(sim_run_id: str, current_round: int) -> None:
    """Mark sim_run as completed."""
    try:
        client = get_client()
        client.table("sim_runs").update({
            "status": "completed",
            "current_round": current_round,
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", sim_run_id).execute()
    except Exception as e:
        logger.warning("Failed to mark sim_run %s complete: %s", sim_run_id, e)


# ---------------------------------------------------------------------------
# ROUND REPORT
# ---------------------------------------------------------------------------

def save_round_report(sim_run_id: str, report: "RoundReport") -> None:
    """Persist a RoundReport to round_reports table (and its children)."""
    try:
        client = get_client()
        n_actions = sum(len(v) for v in report.actions_taken.values())
        row = {
            "sim_run_id": sim_run_id,
            "round_num": report.round_num,
            "duration_seconds": report.duration_seconds,
            "actions_count": n_actions,
            "conversations_count": len(report.conversations),
            "transactions_count": len(report.transactions),
            "mandatory_count": len(report.mandatory_inputs),
            "summary": report.summary(),
            "log": report.log,
            "engine_results": _safe_jsonable(report.engine_results),
            "nous_adjustments": _safe_jsonable(report.nous_adjustments),
        }
        client.table("round_reports").insert(row).execute()
        logger.info("Persisted round_report for round %d (sim_run=%s)", report.round_num, sim_run_id)

        # Update sim_run current_round
        try:
            client.table("sim_runs").update({
                "current_round": report.round_num,
            }).eq("id", sim_run_id).execute()
        except Exception as e:
            logger.debug("Failed to bump current_round: %s", e)

        # Persist children
        save_actions(sim_run_id, report.round_num, report.actions_taken)
        save_conversations(sim_run_id, report.round_num, report.conversations)
        save_transactions(sim_run_id, report.round_num, report.transactions)
        save_reflections(sim_run_id, report.round_num, report.agent_reflections)
        save_mandatory(sim_run_id, report.round_num, report.mandatory_inputs)
    except Exception as e:
        logger.error("save_round_report failed (sim_run=%s, round=%d): %s",
                     sim_run_id, report.round_num, e)


def save_actions(
    sim_run_id: str,
    round_num: int,
    actions_taken: dict[str, list[dict]],
) -> None:
    """Persist per-agent actions as individual rows in agent_actions."""
    if not actions_taken:
        return
    try:
        client = get_client()
        rows: list[dict] = []
        for role_id, actions in actions_taken.items():
            for action in actions:
                rows.append({
                    "sim_run_id": sim_run_id,
                    "round_num": round_num,
                    "role_id": role_id,
                    "action_type": str(action.get("action_type") or action.get("type") or "unknown"),
                    "action_data": _safe_jsonable(action),
                    "reasoning": action.get("reasoning") or action.get("rationale"),
                })
        if rows:
            client.table("agent_actions").insert(rows).execute()
            logger.info("Persisted %d agent_actions (round=%d)", len(rows), round_num)
    except Exception as e:
        logger.error("save_actions failed: %s", e)


def save_conversations(
    sim_run_id: str,
    round_num: int,
    conversations: list[dict],
) -> None:
    """Persist bilateral conversations."""
    if not conversations:
        return
    try:
        client = get_client()
        rows: list[dict] = []
        for conv in conversations:
            rows.append({
                "sim_run_id": sim_run_id,
                "round_num": round_num,
                "role_a": str(conv.get("role_a") or conv.get("initiator") or "unknown"),
                "role_b": str(conv.get("role_b") or conv.get("counterpart") or "unknown"),
                "transcript": _safe_jsonable(conv.get("transcript") or []),
                "intent_notes": _safe_jsonable(conv.get("intent_notes")),
                "reflections": _safe_jsonable(conv.get("reflections")),
                "turns": conv.get("turns"),
                "ended_by": conv.get("ended_by"),
            })
        if rows:
            client.table("agent_conversations").insert(rows).execute()
            logger.info("Persisted %d conversations (round=%d)", len(rows), round_num)
    except Exception as e:
        logger.error("save_conversations failed: %s", e)


def save_transactions(
    sim_run_id: str,
    round_num: int,
    transactions: list[dict],
) -> None:
    """Persist transaction proposals / outcomes."""
    if not transactions:
        return
    try:
        client = get_client()
        rows: list[dict] = []
        for txn in transactions:
            rows.append({
                "sim_run_id": sim_run_id,
                "round_num": round_num,
                "transaction_type": str(txn.get("transaction_type") or txn.get("type") or "unknown"),
                "proposer_role_id": str(txn.get("proposer_role_id") or txn.get("from") or "unknown"),
                "counterpart_role_id": str(txn.get("counterpart_role_id") or txn.get("to") or "unknown"),
                "actor_scope": str(txn.get("actor_scope") or "country"),
                "terms": _safe_jsonable(txn.get("terms") or txn),
                "status": txn.get("status"),
                "decision": txn.get("decision"),
                "reasoning": txn.get("reasoning"),
            })
        if rows:
            client.table("agent_transactions").insert(rows).execute()
            logger.info("Persisted %d transactions (round=%d)", len(rows), round_num)
    except Exception as e:
        logger.error("save_transactions failed: %s", e)


def save_reflections(
    sim_run_id: str,
    round_num: int,
    reflections: dict[str, dict],
) -> None:
    """Persist per-agent post-round reflections."""
    if not reflections:
        return
    try:
        client = get_client()
        rows: list[dict] = []
        for role_id, refl in reflections.items():
            rows.append({
                "sim_run_id": sim_run_id,
                "round_num": round_num,
                "role_id": role_id,
                "reflection_data": _safe_jsonable(refl),
            })
        if rows:
            client.table("agent_reflections").insert(rows).execute()
            logger.info("Persisted %d reflections (round=%d)", len(rows), round_num)
    except Exception as e:
        logger.error("save_reflections failed: %s", e)


def save_mandatory(
    sim_run_id: str,
    round_num: int,
    mandatory_inputs: dict[str, dict],
) -> None:
    """Persist mandatory submissions (budget, tariffs, sanctions, OPEC) as agent_actions.

    Flattens each submission into one action row per role per decision type.
    """
    if not mandatory_inputs:
        return
    try:
        client = get_client()
        rows: list[dict] = []
        for role_id, inputs in mandatory_inputs.items():
            if not isinstance(inputs, dict):
                continue
            for decision_type, data in inputs.items():
                rows.append({
                    "sim_run_id": sim_run_id,
                    "round_num": round_num,
                    "role_id": role_id,
                    "action_type": f"mandatory_{decision_type}",
                    "action_data": _safe_jsonable(data),
                    "reasoning": None,
                })
        if rows:
            client.table("agent_actions").insert(rows).execute()
            logger.info("Persisted %d mandatory submissions (round=%d)", len(rows), round_num)
    except Exception as e:
        logger.error("save_mandatory failed: %s", e)


# ---------------------------------------------------------------------------
# CLEANUP
# ---------------------------------------------------------------------------

def delete_test_runs(older_than_hours: int = 24) -> int:
    """Delete test sim_runs older than N hours. Cascade-deletes children.

    Returns number of sim_runs deleted.
    """
    try:
        client = get_client()
        cutoff = datetime.now(timezone.utc) - timedelta(hours=older_than_hours)
        cutoff_iso = cutoff.isoformat()

        # Find matching test sim_runs
        result = (
            client.table("sim_runs")
            .select("id,name")
            .like("name", "test_%")
            .lt("created_at", cutoff_iso)
            .execute()
        )
        rows = result.data or []
        if not rows:
            logger.info("No test sim_runs older than %dh to delete", older_than_hours)
            return 0

        ids = [r["id"] for r in rows]
        client.table("sim_runs").delete().in_("id", ids).execute()
        logger.info("Deleted %d test sim_runs older than %dh", len(ids), older_than_hours)
        return len(ids)
    except Exception as e:
        logger.error("delete_test_runs failed: %s", e)
        return 0


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def _safe_jsonable(obj: Any) -> Any:
    """Convert to JSON-serialisable form. Dataclasses → dict, tuples → list."""
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {str(k): _safe_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_safe_jsonable(v) for v in obj]
    # dataclass / pydantic / generic object
    if hasattr(obj, "__dict__"):
        try:
            return {k: _safe_jsonable(v) for k, v in vars(obj).items()}
        except Exception:
            pass
    return str(obj)
