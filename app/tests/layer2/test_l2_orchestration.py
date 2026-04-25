"""Level 2 — Orchestration Correctness Tests.

Verifies that the RIGHT actions/permissions apply at each sim stage:
  - pre_start: actions blocked, observation tools work
  - Phase A: immediate actions allowed, batch actions blocked
  - Phase B (processing): batch actions allowed
  - inter_round: actions allowed (no phase restriction)
  - Event enqueue verification: meeting invitations, etc.

Uses ToolExecutor directly against the live DB ($0 cost, no LLM).
Requires: .env loaded, sim_run exists.

Run:
    cd "/Users/marat/4. METAGAMES/1. NEW SIMs/THUCYDIDES" && \
    PYTHONPATH=app .venv/bin/python -m pytest app/tests/layer2/test_l2_orchestration.py -v -s
"""
import json
import logging
import os
import pytest

logger = logging.getLogger(__name__)

# Load .env before importing engine modules
from pathlib import Path
_env_path = Path(__file__).resolve().parents[2] / "engine" / ".env"
if _env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(_env_path)

SIM_RUN_ID = os.environ.get("TEST_SIM_RUN_ID", "c954b9b6-35f0-4973-a08b-f38406c524e7")
COUNTRY_CODE = "phrygia"
ROLE_ID = "phrygia_vizier"
SCENARIO_CODE = "ttt_v1"


def _parse(executor, tool_name: str, tool_input: dict) -> dict:
    """Execute a tool and parse the JSON result."""
    return json.loads(executor.execute(tool_name, tool_input))


@pytest.fixture(scope="module")
def executor():
    """Create a ToolExecutor for Vizier/Phrygia."""
    from engine.agents.managed.tool_executor import ToolExecutor
    return ToolExecutor(
        country_code=COUNTRY_CODE,
        scenario_code=SCENARIO_CODE,
        sim_run_id=SIM_RUN_ID,
        round_num=1,
        role_id=ROLE_ID,
    )


@pytest.fixture(scope="module")
def client():
    """Get Supabase client."""
    from engine.services.supabase import get_client
    return get_client()


# ===========================================================================
# Ordered test class — walks through sim stages sequentially
# ===========================================================================

class TestOrchestrationStages:
    """Tests MUST run in order: pre_start → Phase A → Phase B → inter_round → restore."""

    # -----------------------------------------------------------------------
    # Stage 1: pre_start (R0) — actions blocked, observation tools work
    # -----------------------------------------------------------------------

    def test_01_restart_to_pre_start(self, executor, client):
        """Restart sim to pre_start state and clean up stale meeting invitations."""
        from engine.services.sim_run_manager import restart_simulation
        state = restart_simulation(SIM_RUN_ID)
        assert state["status"] == "pre_start"
        assert state["current_phase"] == "pre"

        # Clean stale meeting invitations from prior runs (restart_simulation doesn't clear them)
        try:
            client.table("meeting_invitations").delete().eq("sim_run_id", SIM_RUN_ID).execute()
        except Exception:
            pass
        logger.info("Stage 1: sim restarted to pre_start")

    def test_02_pre_start_action_blocked(self, executor):
        """submit_action(public_statement) should be REJECTED during pre_start."""
        result = _parse(executor, "submit_action", {
            "action": {
                "action_type": "public_statement",
                "content": "Test statement during pre_start",
                "rationale": "orchestration test",
            }
        })
        assert result.get("success") is not True, f"Action should be blocked in pre_start: {result}"
        assert result.get("validation_status") == "rejected"
        notes = result.get("validation_notes", "")
        assert "pre_start" in notes.lower() or "setup" in notes.lower(), f"Rejection should mention pre_start: {notes}"
        logger.info("Stage 1: public_statement correctly rejected in pre_start")

    def test_03_pre_start_get_my_country_works(self, executor):
        """get_my_country should WORK during pre_start."""
        result = _parse(executor, "get_my_country", {})
        assert "error" not in result, f"get_my_country should work in pre_start: {result}"
        assert "country" in result
        logger.info("Stage 1: get_my_country works in pre_start")

    def test_04_pre_start_write_notes_works(self, executor):
        """write_notes should WORK during pre_start."""
        result = _parse(executor, "write_notes", {
            "key": "orch_test_pre_start",
            "content": "Note written during pre_start — orchestration test",
        })
        assert result.get("success") is True, f"write_notes should work in pre_start: {result}"
        logger.info("Stage 1: write_notes works in pre_start")

    def test_05_pre_start_meeting_blocked(self, executor, client):
        """request_meeting should be blocked during pre_start."""
        # Verify sim is actually in pre_start before testing
        run = client.table("sim_runs").select("status,current_phase").eq("id", SIM_RUN_ID).limit(1).execute()
        assert run.data and run.data[0]["status"] == "pre_start", \
            f"Sim should be in pre_start, got: {run.data[0] if run.data else 'no data'}"

        result = _parse(executor, "request_meeting", {
            "target_country": "levantia",
            "agenda": "Test meeting during pre_start",
        })
        assert result.get("success") is not True, \
            f"BUG: request_meeting should be blocked in pre_start but succeeded: {result}"
        logger.info("Stage 1: request_meeting correctly blocked in pre_start")

    # -----------------------------------------------------------------------
    # Stage 2: Phase A (active, R1) — immediate actions allowed, batch blocked
    # -----------------------------------------------------------------------

    def test_10_start_simulation(self, executor, client):
        """Start simulation → active Phase A.

        If sim is already active (e.g. from a previous test run that didn't
        clean up), restart first then start.
        """
        from engine.services.sim_run_manager import start_simulation, restart_simulation
        run = client.table("sim_runs").select("status").eq("id", SIM_RUN_ID).limit(1).execute()
        if run.data and run.data[0]["status"] != "pre_start":
            restart_simulation(SIM_RUN_ID)
            # Clean stale meeting invitations
            try:
                client.table("meeting_invitations").delete().eq("sim_run_id", SIM_RUN_ID).execute()
            except Exception:
                pass
        state = start_simulation(SIM_RUN_ID)
        assert state["status"] == "active"
        assert state["current_phase"] == "A"
        assert state["current_round"] == 1
        logger.info("Stage 2: sim started — active Phase A, round 1")

    def test_11_phase_a_public_statement_allowed(self, executor):
        """submit_action(public_statement) should SUCCEED in Phase A."""
        result = _parse(executor, "submit_action", {
            "action": {
                "action_type": "public_statement",
                "content": "Phrygia declares commitment to peace — orchestration test.",
                "rationale": "Phase A orchestration test",
            }
        })
        assert result.get("success") is True, f"public_statement should succeed in Phase A: {result}"
        logger.info("Stage 2: public_statement succeeds in Phase A")

    def test_12_phase_a_ground_attack_not_phase_restricted(self, executor):
        """ground_attack should NOT be rejected for phase reasons in Phase A.

        It may fail on game logic (no valid target, etc.) but should NOT say
        'Phase B solicitation window'.
        """
        result = _parse(executor, "submit_action", {
            "action": {
                "action_type": "ground_attack",
                "target_country_code": "levantia",
                "target_global_row": 5,
                "target_global_col": 10,
                "attacker_unit_codes": ["phy_g_01"],
                "rationale": "Phase A orchestration test — may fail on game logic",
            }
        })
        notes = result.get("validation_notes", "") + result.get("result", "")
        assert "Phase B" not in notes, f"ground_attack should not be phase-restricted: {notes}"
        logger.info("Stage 2: ground_attack not phase-restricted (success=%s)", result.get("success"))

    def test_13_phase_a_set_budget_blocked(self, executor):
        """set_budget should be REJECTED in Phase A (Phase B only)."""
        result = _parse(executor, "submit_action", {
            "action": {
                "action_type": "set_budget",
                "military_pct": 20,
                "social_pct": 30,
                "infrastructure_pct": 25,
                "technology_pct": 25,
                "rationale": "orchestration test",
            }
        })
        assert result.get("success") is not True, f"set_budget should be blocked in Phase A: {result}"
        assert result.get("validation_status") == "rejected"
        notes = result.get("validation_notes", "")
        assert "Phase B" in notes, f"Rejection should mention Phase B: {notes}"
        logger.info("Stage 2: set_budget correctly rejected in Phase A")

    def test_14_phase_a_move_units_blocked(self, executor):
        """move_units should be REJECTED in Phase A (Phase B only)."""
        result = _parse(executor, "submit_action", {
            "action": {
                "action_type": "move_units",
                "decision": "no_change",
                "rationale": "orchestration test",
            }
        })
        assert result.get("success") is not True, f"move_units should be blocked in Phase A: {result}"
        assert result.get("validation_status") == "rejected"
        notes = result.get("validation_notes", "")
        assert "Phase B" in notes, f"Rejection should mention Phase B: {notes}"
        logger.info("Stage 2: move_units correctly rejected in Phase A")

    def test_15_phase_a_set_tariffs_blocked(self, executor):
        """set_tariffs should be REJECTED in Phase A (Phase B only)."""
        result = _parse(executor, "submit_action", {
            "action": {
                "action_type": "set_tariffs",
                "tariff_rates": {},
                "rationale": "orchestration test",
            }
        })
        assert result.get("success") is not True, f"set_tariffs should be blocked in Phase A: {result}"
        assert result.get("validation_status") == "rejected"
        logger.info("Stage 2: set_tariffs correctly rejected in Phase A")

    def test_16_phase_a_request_meeting_allowed(self, executor):
        """request_meeting should WORK in Phase A."""
        result = _parse(executor, "request_meeting", {
            "target_country": "levantia",
            "agenda": "Bilateral discussion — orchestration test",
        })
        assert result.get("success") is True, f"request_meeting should work in Phase A: {result}"
        # Save invitation_id for event check
        self.__class__._meeting_invitation_id = result.get("invitation_id")
        logger.info("Stage 2: request_meeting works in Phase A (inv_id=%s)", result.get("invitation_id"))

    # -----------------------------------------------------------------------
    # Stage 3: Phase B (processing) — batch actions allowed
    # -----------------------------------------------------------------------

    def test_20_end_phase_a(self, executor, client):
        """End Phase A → processing/Phase B."""
        from engine.services.sim_run_manager import end_phase_a
        state = end_phase_a(SIM_RUN_ID)
        assert state["status"] == "processing"
        assert state["current_phase"] == "B"
        logger.info("Stage 3: transitioned to Phase B (processing)")

    def test_21_phase_b_set_budget_allowed(self, executor):
        """set_budget should be ALLOWED in Phase B."""
        result = _parse(executor, "submit_action", {
            "action": {
                "action_type": "set_budget",
                "military_pct": 20,
                "social_pct": 30,
                "infrastructure_pct": 25,
                "technology_pct": 25,
                "rationale": "Phase B orchestration test",
            }
        })
        # Should not be rejected for phase reasons
        notes = result.get("validation_notes", "")
        assert "Phase B solicitation" not in notes, f"set_budget should not be phase-rejected in Phase B: {notes}"
        assert result.get("validation_status") != "rejected" or "Phase" not in notes
        logger.info("Stage 3: set_budget allowed in Phase B (success=%s)", result.get("success"))

    def test_22_phase_b_set_tariffs_allowed(self, executor):
        """set_tariffs should be ALLOWED in Phase B."""
        result = _parse(executor, "submit_action", {
            "action": {
                "action_type": "set_tariffs",
                "tariff_rates": {},
                "rationale": "Phase B orchestration test",
            }
        })
        notes = result.get("validation_notes", "")
        assert "Phase B solicitation" not in notes, f"set_tariffs should not be phase-rejected in Phase B: {notes}"
        logger.info("Stage 3: set_tariffs allowed in Phase B (success=%s)", result.get("success"))

    def test_23_phase_b_public_statement_check(self, executor):
        """Check if public_statement works or is blocked in Phase B.

        This is a discovery test — documents the actual behavior.
        The tool_executor does NOT block non-batch actions in Phase B,
        so this should succeed (status is 'processing', not blocked).
        """
        result = _parse(executor, "submit_action", {
            "action": {
                "action_type": "public_statement",
                "content": "Phrygia statement during Phase B — orchestration test.",
                "rationale": "Phase B discovery test",
            }
        })
        # Document behavior — not a hard pass/fail
        logger.info(
            "Stage 3: public_statement in Phase B — success=%s, status=%s, notes=%s",
            result.get("success"), result.get("validation_status"),
            result.get("validation_notes", "")[:100],
        )

    # -----------------------------------------------------------------------
    # Stage 4: inter_round — movement allowed
    # -----------------------------------------------------------------------

    def test_30_end_phase_b(self, executor, client):
        """End Phase B → inter_round."""
        from engine.services.sim_run_manager import end_phase_b
        state = end_phase_b(SIM_RUN_ID)
        assert state["status"] == "inter_round"
        assert state["current_phase"] == "inter_round"
        logger.info("Stage 4: transitioned to inter_round")

    def test_31_inter_round_move_units_allowed(self, executor):
        """move_units should be ALLOWED in inter_round (not Phase A, so no block)."""
        result = _parse(executor, "submit_action", {
            "action": {
                "action_type": "move_units",
                "decision": "no_change",
                "rationale": "inter_round orchestration test",
            }
        })
        notes = result.get("validation_notes", "")
        assert "Phase B solicitation" not in notes, f"move_units should not be phase-rejected in inter_round: {notes}"
        logger.info("Stage 4: move_units allowed in inter_round (success=%s)", result.get("success"))

    def test_32_inter_round_set_budget_allowed(self, executor):
        """set_budget in inter_round — should not be phase-rejected (only blocked in Phase A)."""
        result = _parse(executor, "submit_action", {
            "action": {
                "action_type": "set_budget",
                "military_pct": 20,
                "social_pct": 30,
                "infrastructure_pct": 25,
                "technology_pct": 25,
                "rationale": "inter_round orchestration test",
            }
        })
        notes = result.get("validation_notes", "")
        assert "Phase B solicitation" not in notes, f"set_budget should not be phase-rejected in inter_round: {notes}"
        logger.info("Stage 4: set_budget in inter_round (success=%s)", result.get("success"))

    # -----------------------------------------------------------------------
    # Stage 5: Event enqueue verification
    # -----------------------------------------------------------------------

    def test_40_meeting_invitation_event_enqueued(self, client):
        """After request_meeting in Phase A, check agent_event_queue for meeting_invitation_received."""
        events = (
            client.table("agent_event_queue")
            .select("id,event_type,role_id,tier,message,metadata")
            .eq("sim_run_id", SIM_RUN_ID)
            .eq("event_type", "meeting_invitation_received")
            .order("created_at", desc=True)
            .limit(5)
            .execute()
            .data or []
        )
        assert len(events) > 0, "Expected meeting_invitation_received event in agent_event_queue"
        latest = events[0]
        assert latest["event_type"] == "meeting_invitation_received"
        assert latest["tier"] == 2
        # The invitee should be a levantia role (we invited levantia)
        # Role IDs use character names (e.g. "citadel"), not country codes,
        # so just verify the event exists with correct type and tier.
        assert latest.get("role_id"), f"Event should have a role_id, got: {latest}"
        logger.info(
            "Stage 5: meeting_invitation_received event found (role=%s, tier=%s)",
            latest.get("role_id"), latest.get("tier"),
        )

    # -----------------------------------------------------------------------
    # Cleanup: restore to Phase A for other tests
    # -----------------------------------------------------------------------

    def test_99_restore_to_phase_a(self, executor, client):
        """Advance round to restore sim to active Phase A."""
        from engine.services.sim_run_manager import advance_round
        state = advance_round(SIM_RUN_ID)
        assert state["status"] == "active"
        assert state["current_phase"] == "A"
        assert state["current_round"] == 2
        logger.info("Cleanup: sim restored to active Phase A, round %s", state["current_round"])
