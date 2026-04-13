"""L2 — Election engine: nominations, voting, resolution."""

from __future__ import annotations
import pytest
from engine.services.election_engine import (
    submit_nomination, cast_vote, resolve_election,
    get_nominations, get_vote_count,
)
from engine.services.run_roles import seed_run_roles
from engine.services.supabase import get_client
from tests._sim_run_helper import create_isolated_run

SCENARIO = "start_one"


@pytest.fixture
def client():
    return get_client()


@pytest.fixture
def isolated_run(client):
    sim_run_id, cleanup = create_isolated_run(scenario_code=SCENARIO, test_name="election")
    seed_run_roles(sim_run_id)
    # Copy R0 to R1 and R2
    cs = client.table("country_states_per_round").select("*") \
        .eq("sim_run_id", sim_run_id).eq("round_num", 0).execute()
    if cs.data:
        for target_round in [1, 2]:
            rows = [{k: v for k, v in r.items() if k != "id"} for r in cs.data]
            for r in rows:
                r["round_num"] = target_round
            client.table("country_states_per_round").upsert(
                rows, on_conflict="sim_run_id,round_num,country_code"
            ).execute()
    yield sim_run_id
    cleanup()


# ── Nomination tests ──────────────────────────────────────────────────────

def test_nomination_success(client, isolated_run):
    """Columbia role nominates for midterms."""
    sim_run_id = isolated_run

    result = submit_nomination(sim_run_id, 1, "tribune", "columbia_midterms", 2)
    assert result["success"]
    assert result["camp"] == "opposition"
    print(f"\n  [nominated] {result['narrative']}")

    noms = get_nominations(sim_run_id, "columbia_midterms", 2)
    assert len(noms) == 1
    assert noms[0]["role_id"] == "tribune"


def test_nomination_wrong_round(client, isolated_run):
    """Must nominate exactly 1 round before election."""
    sim_run_id = isolated_run

    result = submit_nomination(sim_run_id, 2, "tribune", "columbia_midterms", 2)
    assert not result["success"]
    assert "round 1" in result["narrative"]
    print(f"\n  [blocked] {result['narrative']}")


def test_nomination_duplicate(client, isolated_run):
    """Cannot nominate twice for same election."""
    sim_run_id = isolated_run

    submit_nomination(sim_run_id, 1, "tribune", "columbia_midterms", 2)
    result = submit_nomination(sim_run_id, 1, "tribune", "columbia_midterms", 2)
    assert not result["success"]
    assert "already nominated" in result["narrative"]
    print(f"\n  [blocked] {result['narrative']}")


def test_nomination_non_columbia_blocked(client, isolated_run):
    """Non-Columbia roles cannot nominate."""
    sim_run_id = isolated_run

    result = submit_nomination(sim_run_id, 1, "ironhand", "columbia_midterms", 2)
    assert not result["success"]
    assert "not a Columbia role" in result["narrative"]
    print(f"\n  [blocked] {result['narrative']}")


def test_multiple_nominations(client, isolated_run):
    """Multiple candidates can nominate for same election."""
    sim_run_id = isolated_run

    r1 = submit_nomination(sim_run_id, 1, "tribune", "columbia_midterms", 2)
    r2 = submit_nomination(sim_run_id, 1, "volt", "columbia_midterms", 2)
    r3 = submit_nomination(sim_run_id, 1, "challenger", "columbia_midterms", 2)
    assert r1["success"] and r2["success"] and r3["success"]

    noms = get_nominations(sim_run_id, "columbia_midterms", 2)
    assert len(noms) == 3
    print(f"\n  [3 nominees] {[n['role_id'] for n in noms]}")


# ── Voting tests ──────────────────────────────────────────────────────────

def test_vote_success(client, isolated_run):
    """Columbia participant votes for a nominated candidate."""
    sim_run_id = isolated_run

    submit_nomination(sim_run_id, 1, "tribune", "columbia_midterms", 2)
    submit_nomination(sim_run_id, 1, "volt", "columbia_midterms", 2)

    result = cast_vote(sim_run_id, 2, "dealer", "tribune", "columbia_midterms")
    assert result["success"]
    print(f"\n  [voted] {result['narrative']}")

    assert get_vote_count(sim_run_id, "columbia_midterms") == 1


def test_vote_for_unnominated_blocked(client, isolated_run):
    """Cannot vote for someone who didn't nominate."""
    sim_run_id = isolated_run

    submit_nomination(sim_run_id, 1, "tribune", "columbia_midterms", 2)

    result = cast_vote(sim_run_id, 2, "dealer", "volt", "columbia_midterms")
    assert not result["success"]
    assert "not nominated" in result["narrative"]
    print(f"\n  [blocked] {result['narrative']}")


def test_vote_duplicate_blocked(client, isolated_run):
    """Cannot vote twice in same election."""
    sim_run_id = isolated_run

    submit_nomination(sim_run_id, 1, "tribune", "columbia_midterms", 2)

    cast_vote(sim_run_id, 2, "dealer", "tribune", "columbia_midterms")
    result = cast_vote(sim_run_id, 2, "dealer", "tribune", "columbia_midterms")
    assert not result["success"]
    assert "already voted" in result["narrative"]
    print(f"\n  [blocked] {result['narrative']}")


def test_non_columbia_cannot_vote(client, isolated_run):
    """Non-Columbia roles cannot vote."""
    sim_run_id = isolated_run

    submit_nomination(sim_run_id, 1, "tribune", "columbia_midterms", 2)

    result = cast_vote(sim_run_id, 2, "ironhand", "tribune", "columbia_midterms")
    assert not result["success"]
    assert "not a Columbia role" in result["narrative"]
    print(f"\n  [blocked] {result['narrative']}")


# ── Resolution tests ──────────────────────────────────────────────────────

def test_resolve_opposition_wins_midterms(client, isolated_run):
    """Opposition candidate wins midterms with low AI score + participant votes."""
    sim_run_id = isolated_run

    # Nominations (R1)
    submit_nomination(sim_run_id, 1, "tribune", "columbia_midterms", 2)
    submit_nomination(sim_run_id, 1, "volt", "columbia_midterms", 2)

    # Votes (R2): 4 vote tribune, 1 votes volt
    cast_vote(sim_run_id, 2, "dealer", "tribune", "columbia_midterms")
    cast_vote(sim_run_id, 2, "anchor", "tribune", "columbia_midterms")
    cast_vote(sim_run_id, 2, "challenger", "tribune", "columbia_midterms")
    cast_vote(sim_run_id, 2, "shadow", "tribune", "columbia_midterms")
    cast_vote(sim_run_id, 2, "shield", "volt", "columbia_midterms")

    # Resolve with low AI score (bad economy = opposition advantage)
    result = resolve_election(
        sim_run_id, 2, "columbia_midterms",
        ai_score=30.0,
        contested_seat_role="volt",  # volt's seat is contested
    )
    assert result["success"]
    assert result["winner"] == "tribune"
    assert result["seat_changed"] == "volt"
    print(f"\n  [resolved] {result['narrative']}")
    print(f"  total_votes: {result['total_votes']}")


def test_resolve_incumbent_wins_with_high_ai_score(client, isolated_run):
    """Incumbent camp candidate wins when AI score is high despite fewer participant votes."""
    sim_run_id = isolated_run

    submit_nomination(sim_run_id, 1, "tribune", "columbia_midterms", 2)
    submit_nomination(sim_run_id, 1, "volt", "columbia_midterms", 2)

    # 3 vote tribune (opposition), 2 vote volt (president camp)
    cast_vote(sim_run_id, 2, "challenger", "tribune", "columbia_midterms")
    cast_vote(sim_run_id, 2, "tribune", "tribune", "columbia_midterms")
    cast_vote(sim_run_id, 2, "anchor", "tribune", "columbia_midterms")
    cast_vote(sim_run_id, 2, "dealer", "volt", "columbia_midterms")
    cast_vote(sim_run_id, 2, "shadow", "volt", "columbia_midterms")

    # Very high AI score (90%) — strong economy boosts incumbent camp
    result = resolve_election(
        sim_run_id, 2, "columbia_midterms",
        ai_score=90.0,
        contested_seat_role="volt",
    )
    assert result["success"]
    # volt gets 2 participant + 90% of 5 population = 2 + 4.5 = 6.5
    # tribune gets 3 participant + 10% of 5 population / 1 = 3 + 0.5 = 3.5
    assert result["winner"] == "volt"
    assert result["seat_changed"] is None  # volt keeps own seat
    print(f"\n  [resolved] {result['narrative']}")
    print(f"  total_votes: {result['total_votes']}")


def test_resolve_presidential(client, isolated_run):
    """Presidential election — simple plurality with AI score."""
    sim_run_id = isolated_run

    # Use R4 nominations for R5 presidential
    submit_nomination(sim_run_id, 4, "volt", "columbia_presidential", 5)
    submit_nomination(sim_run_id, 4, "challenger", "columbia_presidential", 5)

    # Copy country state to R5
    cs = client.table("country_states_per_round").select("*") \
        .eq("sim_run_id", sim_run_id).eq("round_num", 1).eq("country_code", "columbia") \
        .execute()
    if cs.data:
        row = {k: v for k, v in cs.data[0].items() if k != "id"}
        row["round_num"] = 5
        client.table("country_states_per_round").upsert(
            [row], on_conflict="sim_run_id,round_num,country_code"
        ).execute()

    # Votes (R5)
    cast_vote(sim_run_id, 5, "dealer", "volt", "columbia_presidential")
    cast_vote(sim_run_id, 5, "anchor", "volt", "columbia_presidential")
    cast_vote(sim_run_id, 5, "tribune", "challenger", "columbia_presidential")
    cast_vote(sim_run_id, 5, "shadow", "challenger", "columbia_presidential")

    result = resolve_election(sim_run_id, 5, "columbia_presidential", ai_score=55.0)
    assert result["success"]
    print(f"\n  [presidential] winner={result['winner']}")
    print(f"  {result['narrative']}")


def test_resolve_no_candidates_blocked(client, isolated_run):
    """Cannot resolve election with no candidates."""
    sim_run_id = isolated_run

    result = resolve_election(sim_run_id, 2, "columbia_midterms", ai_score=50.0)
    assert not result["success"]
    assert "No candidates" in result["narrative"]
    print(f"\n  [blocked] {result['narrative']}")
