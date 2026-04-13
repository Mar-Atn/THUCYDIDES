"""Election Engine — nominations, voting, and resolution.

Three actions:
1. submit_nomination() — self-nominate for an upcoming election (round before)
2. cast_vote() — vote for a nominated candidate (election round, secret ballot)
3. resolve_election() — count votes, apply AI score, determine winner, update seat

Camp assignment: each Columbia role belongs to 'president_camp' or 'opposition'.
AI score ("other people vote") distributes population votes by camp:
  - president_camp candidates share ai_score% of population votes
  - opposition candidates share (100-ai_score)% of population votes
  - within each camp, population votes split evenly among candidates
Total population votes = number of participant votes (50/50 balance).
"""

from __future__ import annotations

import logging
import math

from engine.services.run_roles import get_run_role
from engine.services.supabase import get_client

logger = logging.getLogger(__name__)

# Camp assignment for Columbia roles (Template v1.0)
COLUMBIA_CAMPS: dict[str, str] = {
    # President's camp
    "dealer": "president_camp",
    "volt": "president_camp",
    "anchor": "president_camp",
    "shadow": "president_camp",
    "shield": "president_camp",
    # Opposition
    "tribune": "opposition",
    "challenger": "opposition",
}

# Columbia roles eligible to vote in elections
COLUMBIA_VOTER_ROLES = list(COLUMBIA_CAMPS.keys())


# ── 1. Nomination ─────────────────────────────────────────────────────────

def submit_nomination(
    sim_run_id: str,
    round_num: int,
    role_id: str,
    election_type: str,
    election_round: int,
) -> dict:
    """Self-nominate for an upcoming election.

    Must be called the round before the election (round_num == election_round - 1).
    """
    client = get_client()

    # Validate timing
    if round_num != election_round - 1:
        return {"success": False, "narrative": (
            f"Nominations for {election_type} (round {election_round}) "
            f"must be submitted in round {election_round - 1}, not round {round_num}"
        )}

    # Validate role
    role = get_run_role(sim_run_id, role_id)
    if not role or role["status"] != "active":
        return {"success": False, "narrative": f"Role {role_id} not active"}

    country = role.get("country_code", "")
    if country != "columbia":
        return {"success": False, "narrative": f"{role_id} is not a Columbia role — only Columbia participants can nominate"}

    # Determine camp
    camp = COLUMBIA_CAMPS.get(role_id, "unknown")

    # Check for duplicate nomination
    existing = client.table("election_nominations").select("id") \
        .eq("sim_run_id", sim_run_id).eq("election_type", election_type) \
        .eq("role_id", role_id).execute().data
    if existing:
        return {"success": False, "narrative": f"{role_id} already nominated for {election_type}"}

    # Insert nomination
    client.table("election_nominations").insert({
        "sim_run_id": sim_run_id,
        "election_type": election_type,
        "election_round": election_round,
        "role_id": role_id,
        "country_code": "columbia",
        "camp": camp,
    }).execute()

    # Observatory event
    scenario_id = _get_scenario_id(client, sim_run_id)
    narrative = (f"NOMINATION: {role_id} ({camp}) nominates for {election_type} "
                 f"(election round {election_round}).")
    _write_event(client, sim_run_id, scenario_id, round_num, "columbia",
                 "election_nomination", narrative,
                 {"role_id": role_id, "election_type": election_type,
                  "election_round": election_round, "camp": camp})

    logger.info("[election] %s nominates for %s (round %d)", role_id, election_type, election_round)

    return {
        "success": True,
        "camp": camp,
        "election_type": election_type,
        "election_round": election_round,
        "narrative": narrative,
    }


# ── 2. Voting ──────────────────────────────────────────────────────────────

def cast_vote(
    sim_run_id: str,
    round_num: int,
    voter_role_id: str,
    candidate_role_id: str,
    election_type: str,
) -> dict:
    """Cast a secret vote for a nominated candidate.

    Must be called during the election round.
    """
    client = get_client()

    # Validate voter
    voter = get_run_role(sim_run_id, voter_role_id)
    if not voter or voter["status"] != "active":
        return {"success": False, "narrative": f"Voter {voter_role_id} not active"}

    voter_country = voter.get("country_code", "")
    if voter_country != "columbia":
        return {"success": False, "narrative": f"{voter_role_id} is not a Columbia role — cannot vote"}

    # Validate candidate is nominated
    nominations = client.table("election_nominations").select("role_id") \
        .eq("sim_run_id", sim_run_id).eq("election_type", election_type) \
        .eq("election_round", round_num).execute().data
    nominated_ids = {n["role_id"] for n in (nominations or [])}

    if not nominated_ids:
        return {"success": False, "narrative": f"No candidates nominated for {election_type} round {round_num}"}
    if candidate_role_id not in nominated_ids:
        return {"success": False, "narrative": (
            f"{candidate_role_id} is not nominated for {election_type}. "
            f"Candidates: {', '.join(sorted(nominated_ids))}"
        )}

    # Check for duplicate vote
    existing = client.table("election_votes").select("id") \
        .eq("sim_run_id", sim_run_id).eq("election_type", election_type) \
        .eq("voter_role_id", voter_role_id).execute().data
    if existing:
        return {"success": False, "narrative": f"{voter_role_id} already voted in {election_type}"}

    # Insert vote (secret — only moderator sees)
    client.table("election_votes").insert({
        "sim_run_id": sim_run_id,
        "election_type": election_type,
        "election_round": round_num,
        "voter_role_id": voter_role_id,
        "candidate_role_id": candidate_role_id,
        "country_code": "columbia",
    }).execute()

    # Observatory event (logged but candidate NOT revealed — secret ballot)
    scenario_id = _get_scenario_id(client, sim_run_id)
    narrative = f"VOTE CAST: {voter_role_id} voted in {election_type} (secret ballot)."
    _write_event(client, sim_run_id, scenario_id, round_num, "columbia",
                 "election_vote_cast", narrative,
                 {"voter": voter_role_id, "election_type": election_type})

    logger.info("[election] %s voted in %s", voter_role_id, election_type)

    return {
        "success": True,
        "narrative": narrative,
    }


# ── 3. Resolution ─────────────────────────────────────────────────────────

def resolve_election(
    sim_run_id: str,
    round_num: int,
    election_type: str,
    ai_score: float,
    contested_seat_role: str | None = None,
) -> dict:
    """Resolve an election: count participant votes + population votes → winner.

    Args:
        ai_score: AI incumbent score [0-100] from process_election() or precomputed.
        contested_seat_role: For midterms — the role_id whose parliament seat is contested.
            The winner replaces this role in the seat.
    """
    client = get_client()

    # Load nominations
    nominations = client.table("election_nominations").select("role_id,camp") \
        .eq("sim_run_id", sim_run_id).eq("election_type", election_type) \
        .eq("election_round", round_num).execute().data or []

    if not nominations:
        return {"success": False, "narrative": f"No candidates for {election_type} round {round_num}"}

    candidates = {n["role_id"]: n["camp"] for n in nominations}

    # Load votes
    votes = client.table("election_votes").select("voter_role_id,candidate_role_id") \
        .eq("sim_run_id", sim_run_id).eq("election_type", election_type) \
        .eq("election_round", round_num).execute().data or []

    # Count participant votes per candidate
    participant_votes: dict[str, int] = {c: 0 for c in candidates}
    for v in votes:
        cid = v["candidate_role_id"]
        if cid in participant_votes:
            participant_votes[cid] += 1

    total_participant_votes = sum(participant_votes.values())

    # Population votes ("other people") — same count as participant votes for 50/50 balance
    population_vote_count = max(total_participant_votes, 1)

    # Split population votes by camp based on AI score
    president_camp_pop = ai_score / 100.0 * population_vote_count
    opposition_pop = (1.0 - ai_score / 100.0) * population_vote_count

    # Count candidates per camp
    president_candidates = [c for c, camp in candidates.items() if camp == "president_camp"]
    opposition_candidates = [c for c, camp in candidates.items() if camp == "opposition"]
    unknown_candidates = [c for c, camp in candidates.items() if camp not in ("president_camp", "opposition")]

    # Distribute population votes evenly within each camp
    population_votes: dict[str, float] = {}
    if president_candidates:
        per_pres = president_camp_pop / len(president_candidates)
        for c in president_candidates:
            population_votes[c] = per_pres
    if opposition_candidates:
        per_opp = opposition_pop / len(opposition_candidates)
        for c in opposition_candidates:
            population_votes[c] = per_opp
    # Unknown camp candidates get no population votes
    for c in unknown_candidates:
        population_votes[c] = 0.0

    # Total votes = participant + population
    total_votes: dict[str, float] = {}
    for c in candidates:
        total_votes[c] = participant_votes.get(c, 0) + population_votes.get(c, 0.0)

    # Winner = candidate with highest total votes
    winner = max(total_votes, key=lambda c: total_votes[c])

    # Handle seat change for midterms
    seat_changed = None
    if election_type == "columbia_midterms" and contested_seat_role:
        if winner != contested_seat_role:
            seat_changed = contested_seat_role
            # Update parliament membership: winner takes the contested seat
            # (This is tracked via observatory event — no mechanical DB change beyond recording)

    # Store result
    result_row = {
        "sim_run_id": sim_run_id,
        "election_type": election_type,
        "election_round": round_num,
        "country_code": "columbia",
        "winner_role_id": winner,
        "ai_score": round(ai_score, 2),
        "participant_votes": participant_votes,
        "population_votes": {c: round(v, 2) for c, v in population_votes.items()},
        "total_votes": {c: round(v, 2) for c, v in total_votes.items()},
        "seat_changed": seat_changed,
    }
    client.table("election_results").insert(result_row).execute()

    # Build narrative
    votes_summary = ", ".join(
        f"{c}: {participant_votes[c]}+{population_votes.get(c, 0):.1f}={total_votes[c]:.1f}"
        for c in sorted(total_votes, key=lambda x: total_votes[x], reverse=True)
    )

    if seat_changed:
        narrative = (f"ELECTION RESULT ({election_type}): {winner} wins! "
                     f"Takes parliament seat from {contested_seat_role}. "
                     f"AI score: {ai_score:.0f}%. Votes: {votes_summary}")
    else:
        narrative = (f"ELECTION RESULT ({election_type}): {winner} wins! "
                     f"AI score: {ai_score:.0f}%. Votes: {votes_summary}")

    # Observatory event
    scenario_id = _get_scenario_id(client, sim_run_id)
    _write_event(client, sim_run_id, scenario_id, round_num, "columbia",
                 "election_result", narrative,
                 {"winner": winner, "ai_score": round(ai_score, 2),
                  "participant_votes": participant_votes,
                  "total_votes": {c: round(v, 2) for c, v in total_votes.items()},
                  "seat_changed": seat_changed})

    logger.info("[election] %s resolved: winner=%s ai=%.0f%%", election_type, winner, ai_score)

    return {
        "success": True,
        "winner": winner,
        "ai_score": round(ai_score, 2),
        "participant_votes": participant_votes,
        "population_votes": {c: round(v, 2) for c, v in population_votes.items()},
        "total_votes": {c: round(v, 2) for c, v in total_votes.items()},
        "seat_changed": seat_changed,
        "narrative": narrative,
    }


# ── Helpers ────────────────────────────────────────────────────────────────

def get_nominations(sim_run_id: str, election_type: str, election_round: int) -> list[dict]:
    """Get all nominations for a specific election."""
    client = get_client()
    return client.table("election_nominations").select("*") \
        .eq("sim_run_id", sim_run_id).eq("election_type", election_type) \
        .eq("election_round", election_round).execute().data or []


def get_vote_count(sim_run_id: str, election_type: str) -> int:
    """Get number of votes cast (without revealing who voted for whom)."""
    client = get_client()
    votes = client.table("election_votes").select("id") \
        .eq("sim_run_id", sim_run_id).eq("election_type", election_type).execute().data
    return len(votes or [])


def _get_scenario_id(client, sim_run_id):
    try:
        r = client.table("sim_runs").select("scenario_id").eq("id", sim_run_id).limit(1).execute()
        return r.data[0]["scenario_id"] if r.data else None
    except Exception:
        return None


def _write_event(client, sim_run_id, scenario_id, round_num, country_code, event_type, summary, payload):
    if not scenario_id:
        return
    try:
        client.table("observatory_events").insert({
            "sim_run_id": sim_run_id, "scenario_id": scenario_id,
            "round_num": round_num, "event_type": event_type,
            "country_code": country_code, "summary": summary, "payload": payload,
        }).execute()
    except Exception as e:
        logger.debug("event write failed: %s", e)
