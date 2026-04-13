"""L2 — Intelligence engine: context builder + LLM report generation."""

from __future__ import annotations
import pytest

from engine.services.intelligence_engine import (
    generate_intelligence_report,
    _build_full_world_context,
)
from engine.services.supabase import get_client
from tests._sim_run_helper import create_isolated_run

SCENARIO = "start_one"


@pytest.fixture
def client():
    return get_client()


@pytest.fixture
def isolated_run(client):
    sim_run_id, cleanup = create_isolated_run(scenario_code=SCENARIO, test_name="intelligence")
    yield sim_run_id
    cleanup()


def test_context_builder_loads_all_domains(client, isolated_run):
    """Verify the context builder produces comprehensive output covering all domains."""
    sim_run_id = isolated_run
    context = _build_full_world_context(client, sim_run_id, round_num=0)

    print(f"\n  [context] {len(context)} chars, {context.count(chr(10))} lines")

    # Must contain country data
    assert "[ALL COUNTRIES" in context
    assert "columbia" in context
    assert "sarmatia" in context

    # Must contain military
    assert "[MILITARY FORCES]" in context
    assert "ground" in context

    # Must contain other domains
    assert "[RELATIONSHIPS]" in context
    assert "[AGREEMENTS" in context
    assert "[RECENT EVENTS" in context
    assert "[NUCLEAR STATUS]" in context
    assert "[ACTIVE BLOCKADES]" in context
    assert "[ACTIVE BASING RIGHTS]" in context

    # Print first 2000 chars for inspection
    print(f"\n  --- CONTEXT PREVIEW (first 2000 chars) ---")
    print(context[:2000])
    print(f"  --- END PREVIEW ---")


def test_intelligence_report_generation(client, isolated_run):
    """Full chain: question → context → LLM → report + event."""
    sim_run_id = isolated_run

    result = generate_intelligence_report(
        sim_run_id=sim_run_id,
        round_num=0,
        question="What is the current military balance between Columbia and Sarmatia? Who has more ground forces and where are they deployed?",
        requester_country="columbia",
        requester_role="shadow",
    )

    assert result["success"]
    assert len(result["report"]) > 50  # non-trivial report
    print(f"\n  [report] {len(result['report'])} chars")
    print(f"\n  --- INTELLIGENCE REPORT ---")
    print(result["report"])
    print(f"  --- END REPORT ---")

    # Verify event written
    events = client.table("observatory_events").select("event_type") \
        .eq("sim_run_id", sim_run_id) \
        .eq("event_type", "intelligence_report_received").execute().data or []
    assert events


def test_broad_strategic_question(client, isolated_run):
    """Test a broad strategic question requiring cross-domain analysis."""
    sim_run_id = isolated_run

    result = generate_intelligence_report(
        sim_run_id=sim_run_id,
        round_num=0,
        question="Give me a comprehensive threat assessment: which countries pose the greatest threat to Columbia's interests and why?",
        requester_country="columbia",
        requester_role="shadow",
    )

    assert result["success"]
    assert len(result["report"]) > 100
    print(f"\n  [broad report] {len(result['report'])} chars")
    print(result["report"][:500])
