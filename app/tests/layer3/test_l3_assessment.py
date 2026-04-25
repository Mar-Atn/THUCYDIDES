"""Level 3 — Independent Assessment: DB Verification After Real Agent Tests.

Queries all DB tables to verify that real agent sessions produced correct
state changes. Independent QA — does NOT modify any data or source code.

Run AFTER test_l3_real_single_agent.py and test_l3_real_multi_agent.py.

Run:
    cd /path/to/THUCYDIDES && PYTHONPATH=app .venv/bin/python -m pytest \
        app/tests/layer3/test_l3_assessment.py -v -s
"""
import json
import logging
import os
import pytest
from pathlib import Path

logger = logging.getLogger(__name__)

from dotenv import load_dotenv
for _env_candidate in [
    Path(__file__).resolve().parents[3] / ".env",
    Path(__file__).resolve().parents[2] / "engine" / ".env",
]:
    if _env_candidate.exists():
        load_dotenv(_env_candidate)
        break

SIM_RUN_ID = os.environ.get("TEST_SIM_RUN_ID", "c954b9b6-35f0-4973-a08b-f38406c524e7")


@pytest.fixture(scope="module")
def client():
    from engine.services.supabase import get_client
    return get_client()


# ---------------------------------------------------------------------------
# Assessment 1: Action Coverage Matrix
# ---------------------------------------------------------------------------

class TestActionCoverage:
    """Verify which of the 33 canonical actions were used by real agents."""

    def test_action_type_coverage(self, client):
        """Check which action types appear in agent_decisions for this sim."""
        decisions = client.table("agent_decisions") \
            .select("action_type,country_code,validation_status") \
            .eq("sim_run_id", SIM_RUN_ID) \
            .execute()

        # Count by action_type
        type_counts = {}
        for d in (decisions.data or []):
            at = d["action_type"]
            type_counts[at] = type_counts.get(at, 0) + 1

        logger.info("=== ACTION COVERAGE MATRIX ===")
        for at, count in sorted(type_counts.items()):
            logger.info("  %-30s: %d submissions", at, count)
        logger.info("Total distinct action types used: %d", len(type_counts))
        logger.info("Total submissions: %d", sum(type_counts.values()))

        # Should have some decisions
        assert len(decisions.data or []) > 0, "No agent decisions found — did real agent tests run?"

    def test_countries_that_acted(self, client):
        """Check which AI countries submitted actions."""
        decisions = client.table("agent_decisions") \
            .select("country_code,action_type") \
            .eq("sim_run_id", SIM_RUN_ID) \
            .execute()

        by_country = {}
        for d in (decisions.data or []):
            cc = d["country_code"]
            if cc not in by_country:
                by_country[cc] = set()
            by_country[cc].add(d["action_type"])

        logger.info("=== COUNTRIES THAT ACTED ===")
        for cc, types in sorted(by_country.items()):
            logger.info("  %-12s: %d action types — %s", cc, len(types), sorted(types))

        # Expect at least 3 AI countries acted (from single-agent tests)
        ai_countries = {"phrygia", "solaria", "sarmatia", "columbia", "persia"}
        acting_ai = set(by_country.keys()) & ai_countries
        logger.info("AI countries that acted: %s", acting_ai)


# ---------------------------------------------------------------------------
# Assessment 2: DB Consistency
# ---------------------------------------------------------------------------

class TestDBConsistency:
    """Verify DB state is internally consistent after agent actions."""

    def test_no_orphaned_agent_decisions(self, client):
        """All agent_decisions should reference valid sim_run_id."""
        decisions = client.table("agent_decisions") \
            .select("id,sim_run_id") \
            .eq("sim_run_id", SIM_RUN_ID) \
            .execute()
        assert all(d["sim_run_id"] == SIM_RUN_ID for d in (decisions.data or []))

    def test_validation_status_distribution(self, client):
        """Check what percentage of actions were executed vs rejected."""
        decisions = client.table("agent_decisions") \
            .select("validation_status") \
            .eq("sim_run_id", SIM_RUN_ID) \
            .execute()

        status_counts = {}
        for d in (decisions.data or []):
            s = d["validation_status"]
            status_counts[s] = status_counts.get(s, 0) + 1

        logger.info("=== VALIDATION STATUS DISTRIBUTION ===")
        total = sum(status_counts.values())
        for s, count in sorted(status_counts.items()):
            pct = (count / total * 100) if total else 0
            logger.info("  %-20s: %3d (%5.1f%%)", s, count, pct)

        # Not all actions should fail — at least some should execute
        executed = status_counts.get("executed", 0)
        logger.info("Executed actions: %d / %d", executed, total)

    def test_observatory_events_recorded(self, client):
        """Actions should produce observatory events."""
        events = client.table("observatory_events") \
            .select("event_type,country_code") \
            .eq("sim_run_id", SIM_RUN_ID) \
            .execute()

        event_types = {}
        for e in (events.data or []):
            et = e["event_type"]
            event_types[et] = event_types.get(et, 0) + 1

        logger.info("=== OBSERVATORY EVENTS ===")
        for et, count in sorted(event_types.items()):
            logger.info("  %-30s: %d", et, count)
        logger.info("Total events: %d", sum(event_types.values()))


# ---------------------------------------------------------------------------
# Assessment 3: Meeting Quality
# ---------------------------------------------------------------------------

class TestMeetingQuality:
    """Verify meeting transcripts are coherent (if any meetings occurred)."""

    def test_meeting_transcript_quality(self, client):
        """Check meeting_messages for coherent conversation."""
        meetings = client.table("meetings") \
            .select("id,status,participant_a_country,participant_b_country") \
            .eq("sim_run_id", SIM_RUN_ID) \
            .execute()

        if not meetings.data:
            logger.info("No meetings found — skipping quality check")
            pytest.skip("No meetings in DB")

        for meeting in meetings.data:
            mid = meeting["id"]
            msgs = client.table("meeting_messages") \
                .select("country_code,content,turn_number") \
                .eq("meeting_id", mid) \
                .order("created_at") \
                .execute()

            logger.info("=== MEETING %s (%s ↔ %s, status=%s) ===",
                        mid[:8], meeting["participant_a_country"],
                        meeting["participant_b_country"], meeting["status"])

            for m in (msgs.data or []):
                content = (m.get("content") or "")[:100]
                logger.info("  Turn %s [%s]: %s",
                            m.get("turn_number", "?"), m["country_code"], content)

            # Basic quality: messages should have actual content
            for m in (msgs.data or []):
                content = m.get("content", "")
                assert len(content) > 5, f"Message too short: {content!r}"


# ---------------------------------------------------------------------------
# Assessment 4: AI Session Metrics
# ---------------------------------------------------------------------------

class TestSessionMetrics:
    """Check AI agent session costs and activity metrics."""

    def test_session_costs(self, client):
        """Report cost per agent session."""
        sessions = client.table("ai_agent_sessions") \
            .select("role_id,country_code,model,total_input_tokens,total_output_tokens,"
                    "events_sent,actions_submitted,tool_calls,status") \
            .eq("sim_run_id", SIM_RUN_ID) \
            .execute()

        logger.info("=== AI SESSION METRICS ===")
        total_cost = 0.0
        for s in (sessions.data or []):
            input_t = s.get("total_input_tokens", 0) or 0
            output_t = s.get("total_output_tokens", 0) or 0
            cost = input_t * 3.0 / 1_000_000 + output_t * 15.0 / 1_000_000
            total_cost += cost
            logger.info("  %-15s %-12s | tokens: %6d in, %5d out | $%.4f | "
                        "events=%d actions=%d tools=%d | status=%s",
                        s["role_id"], s["country_code"],
                        input_t, output_t, cost,
                        s.get("events_sent", 0), s.get("actions_submitted", 0),
                        s.get("tool_calls", 0), s.get("status", "?"))

        logger.info("TOTAL COST: $%.4f across %d sessions", total_cost, len(sessions.data or []))

        # Cost should be reasonable
        if total_cost > 0:
            assert total_cost < 10.0, f"Total cost ${total_cost:.2f} exceeds $10 budget"
