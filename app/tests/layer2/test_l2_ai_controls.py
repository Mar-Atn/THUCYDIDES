"""Level 2 — AI Controls: freeze/resume/stop-all + AI settings.

Tests the AI agent control infrastructure and global settings.
No LLM calls — uses direct function calls and DB queries.

Run:
    cd /path/to/THUCYDIDES && PYTHONPATH=app .venv/bin/python -m pytest \
        app/tests/layer2/test_l2_ai_controls.py -v -s
"""
import json
import logging
import os
import pytest
from pathlib import Path

logger = logging.getLogger(__name__)

from dotenv import load_dotenv
for _env in [Path(__file__).resolve().parents[3] / ".env",
             Path(__file__).resolve().parents[2] / "engine" / ".env"]:
    if _env.exists():
        load_dotenv(_env)
        break

SIM_RUN_ID = os.environ.get("TEST_SIM_RUN_ID", "c954b9b6-35f0-4973-a08b-f38406c524e7")


@pytest.fixture(scope="module")
def client():
    from engine.services.supabase import get_client
    return get_client()


# ---------------------------------------------------------------------------
# AI Settings (ai_settings table)
# ---------------------------------------------------------------------------

class TestAISettings:
    """Verify ai_settings table and reader functions."""

    def test_read_assertiveness(self):
        from engine.agents.managed.ai_config import get_assertiveness
        val = get_assertiveness()
        assert 1 <= val <= 10
        logger.info("assertiveness = %d", val)

    def test_read_model_decisions(self):
        from engine.agents.managed.ai_config import get_ai_model
        model = get_ai_model("decisions")
        assert model  # non-empty string
        assert "claude" in model.lower() or "gemini" in model.lower()
        logger.info("model_decisions = %s", model)

    def test_read_model_conversations(self):
        from engine.agents.managed.ai_config import get_ai_model
        model = get_ai_model("conversations")
        assert model
        logger.info("model_conversations = %s", model)

    def test_read_model_stateless(self):
        from engine.agents.managed.ai_config import get_ai_model
        model = get_ai_model("stateless")
        assert model
        logger.info("model_stateless = %s", model)

    def test_write_and_read_setting(self, client):
        """Write a value to ai_settings and read it back."""
        from engine.agents.managed.ai_config import get_assertiveness

        # Save original
        original = client.table("ai_settings").select("value") \
            .eq("key", "assertiveness").limit(1).execute()
        original_val = original.data[0]["value"] if original.data else "5"

        # Write new value
        client.table("ai_settings").update({"value": "3"}) \
            .eq("key", "assertiveness").execute()

        # Read it back
        val = get_assertiveness()
        assert val == 3, f"Expected 3, got {val}"

        # Restore original
        client.table("ai_settings").update({"value": original_val}) \
            .eq("key", "assertiveness").execute()
        logger.info("assertiveness write/read roundtrip OK")

    def test_assertiveness_flows_to_system_prompt(self, client):
        """Verify assertiveness value appears in the system prompt."""
        from engine.agents.managed.system_prompt import build_system_prompt

        # Set cooperative
        client.table("ai_settings").update({"value": "2"}) \
            .eq("key", "assertiveness").execute()

        prompt = build_system_prompt("vizier", sim_run_id=SIM_RUN_ID, assertiveness=2)
        assert "cooperation" in prompt.lower() or "cooperative" in prompt.lower(), \
            "Cooperative nudge should be in prompt at assertiveness=2"

        # Set aggressive
        prompt2 = build_system_prompt("vizier", sim_run_id=SIM_RUN_ID, assertiveness=8)
        assert "competitive" in prompt2.lower() or "strength" in prompt2.lower(), \
            "Competitive nudge should be in prompt at assertiveness=8"

        # Restore
        client.table("ai_settings").update({"value": "5"}) \
            .eq("key", "assertiveness").execute()
        logger.info("assertiveness → system prompt flow OK")


# ---------------------------------------------------------------------------
# Freeze / Resume / Stop All
# ---------------------------------------------------------------------------

class TestFreezeResume:
    """Verify freeze/resume/stop-all agent control mechanics."""

    def test_event_queue_clear_on_stop(self, client):
        """Insert test events into queue, then clear them."""
        # Insert some test events
        for i in range(3):
            client.table("agent_event_queue").insert({
                "sim_run_id": SIM_RUN_ID,
                "role_id": "vizier",
                "tier": 3,
                "event_type": "test_event",
                "message": f"Test event {i} for stop-all verification",
                "metadata": {"test": True},
            }).execute()

        # Verify they exist (unprocessed)
        pending = client.table("agent_event_queue") \
            .select("id") \
            .eq("sim_run_id", SIM_RUN_ID) \
            .eq("event_type", "test_event") \
            .is_("processed_at", "null") \
            .execute()
        assert len(pending.data or []) >= 3, "Should have at least 3 pending test events"

        # Clear unprocessed events (same as stop-all does)
        cleared = client.table("agent_event_queue") \
            .delete() \
            .eq("sim_run_id", SIM_RUN_ID) \
            .eq("event_type", "test_event") \
            .is_("processed_at", "null") \
            .execute()
        logger.info("Cleared %d test events", len(cleared.data or []))

        # Verify cleared
        remaining = client.table("agent_event_queue") \
            .select("id") \
            .eq("sim_run_id", SIM_RUN_ID) \
            .eq("event_type", "test_event") \
            .is_("processed_at", "null") \
            .execute()
        assert len(remaining.data or []) == 0, "All test events should be cleared"

    def test_agent_states_exist(self):
        """Verify agent state constants are defined."""
        from engine.agents.managed.event_dispatcher import IDLE, ACTING, IN_MEETING, FROZEN
        assert IDLE == "IDLE"
        assert FROZEN == "FROZEN"
        assert ACTING == "ACTING"
        assert IN_MEETING == "IN_MEETING"

    def test_session_manager_freeze_resume(self):
        """Verify freeze/resume methods exist on SessionManager."""
        from engine.agents.managed.session_manager import ManagedSessionManager
        mgr = ManagedSessionManager.__new__(ManagedSessionManager)
        assert hasattr(mgr, "freeze_session")
        assert hasattr(mgr, "resume_session")
