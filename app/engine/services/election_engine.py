"""Election Engine — Columbia elections (nominations, voting, resolution).

Contract: CONTRACT_COLUMBIA_ELECTIONS.md v2.0

Three actions:
1. submit_nomination() — self-nominate for an upcoming election (round before)
2. cast_vote() — vote for a nominated candidate (election round, secret ballot)
3. resolve_election() — count weighted votes, apply economy bonus, determine winner

Voting mechanics (CONTRACT v2.0):
  - 5 non-opposition roles: 1 vote each = 5
  - 2 opposition roles: 2 votes each = 4
  - Base total: 9 votes
  - If economy_score < 0.5: each opposition role gets +1 bonus vote (3 each = 6)
  - With bonus total: 11 votes
  - Simple majority wins (5/9 or 6/11). Ties = no winner.

Economy score formula (tuned 2026-04-19):
  economy_score = max(0, (stability-2)/10) * 0.45 + max(0, 1 - inflation/12) * 0.55
  Starting ~0.615 (stab=7, infl=3.5%). Threshold: < 0.5 triggers bonus.
"""

from __future__ import annotations

import logging

from engine.services.supabase import get_client as _get_sb_client

def _get_role(sim_run_id: str, role_id: str) -> dict | None:
    """Get role from roles table (not run_roles which may be empty)."""
    client = _get_sb_client()
    rows = client.table("roles").select("id, character_name, status, country_id, positions") \
        .eq("sim_run_id", sim_run_id).eq("id", role_id).limit(1).execute().data
    return rows[0] if rows else None
from engine.services.supabase import get_client

logger = logging.getLogger(__name__)

# Opposition roles get 2 base votes (3 with economy bonus); all others get 1
OPPOSITION_ROLES = {"tribune", "challenger"}

# All Columbia voter roles
COLUMBIA_VOTER_ROLES = ["dealer", "volt", "anchor", "shadow", "shield", "tribune", "challenger"]


# ── Economy Score ────────────────────────────────────────────────────────

def compute_economy_score(stability: float, inflation: float) -> float:
    """Compute economy score for Columbia elections.

    Tuned formula (approved 2026-04-19):
    - Stability floor at 2 (below = zero contribution)
    - Inflation ceiling at 12% (above = zero contribution)
    - Inflation weighted slightly more (55% vs 45%)
    - Starting score ~0.615 (stab=7, infl=3.5%)
    - Bonus triggers at: stab=7/infl=12+, stab=6/infl=6, stab=4/infl=4

    Returns a value [0, 1]. If < 0.5, opposition gets bonus votes.
    """
    stability_component = max(0.0, (stability - 2.0) / 10.0) * 0.45
    inflation_component = max(0.0, 1.0 - inflation / 12.0) * 0.55
    return stability_component + inflation_component


def get_vote_weight(role_id: str, economy_score: float) -> int:
    """Return vote weight for a role given the current economy score."""
    if role_id in OPPOSITION_ROLES:
        return 3 if economy_score < 0.5 else 2
    return 1


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
    role = _get_role(sim_run_id, role_id)
    if not role or role["status"] != "active":
        return {"success": False, "narrative": f"Role {role_id} not active"}

    country = role.get("country_code", "") or role.get("country_id", "")
    if country != "columbia":
        return {"success": False, "narrative": f"{role_id} is not a Columbia role — only Columbia citizens can nominate"}

    # Eligibility checks per contract
    if election_type == "presidential" and _is_head_of_state(role):
        return {"success": False, "narrative": f"{role_id} is the current Head of State — cannot run for re-election"}

    if election_type == "parliamentary_midterm":
        # Current parliament members whose seats are NOT up for re-election cannot run
        parliament_membership = _get_parliament_membership(client, sim_run_id, role_id)
        if parliament_membership and parliament_membership.get("role_in_org") == "member":
            return {"success": False, "narrative": (
                f"{role_id} holds a parliament seat not up for re-election — cannot nominate"
            )}

    # Check for duplicate nomination
    existing = client.table("election_nominations").select("id") \
        .eq("sim_run_id", sim_run_id).eq("election_type", election_type) \
        .eq("role_id", role_id).execute().data
    if existing:
        return {"success": False, "narrative": f"{role_id} already nominated for {election_type}"}

    camp = "opposition" if role_id in OPPOSITION_ROLES else "president_camp"

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
    narrative = (f"NOMINATION: {role_id} nominates for {election_type} "
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


def withdraw_nomination(
    sim_run_id: str,
    role_id: str,
    election_type: str,
) -> dict:
    """Withdraw a nomination."""
    client = get_client()

    result = client.table("election_nominations").delete() \
        .eq("sim_run_id", sim_run_id).eq("election_type", election_type) \
        .eq("role_id", role_id).execute()

    if not result.data:
        return {"success": False, "narrative": f"{role_id} has no nomination to withdraw for {election_type}"}

    logger.info("[election] %s withdraws nomination for %s", role_id, election_type)
    return {
        "success": True,
        "narrative": f"{role_id} withdrew nomination for {election_type}.",
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
    voter = _get_role(sim_run_id, voter_role_id)
    if not voter or voter["status"] != "active":
        return {"success": False, "narrative": f"Voter {voter_role_id} not active"}

    voter_country = voter.get("country_code", "") or voter.get("country_id", "")
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
    contested_seat_role: str | None = None,
) -> dict:
    """Resolve an election using weighted votes per CONTRACT v2.0.

    No ai_score parameter — economy score is computed from Columbia's
    current stability and inflation.
    """
    client = get_client()

    # Load Columbia's economy data for economy score
    country_row = client.table("countries").select("stability,inflation") \
        .eq("sim_run_id", sim_run_id).eq("id", "columbia").limit(1).execute().data
    if not country_row:
        return {"success": False, "narrative": "Columbia country data not found"}

    stability = float(country_row[0].get("stability", 5.0))
    inflation = float(country_row[0].get("inflation", 3.0))
    economy_score = compute_economy_score(stability, inflation)
    has_bonus = economy_score < 0.5

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

    # Count weighted votes per candidate
    weighted_votes: dict[str, int] = {c: 0 for c in candidates}
    voter_weights: dict[str, int] = {}

    for v in votes:
        voter_id = v["voter_role_id"]
        cid = v["candidate_role_id"]
        weight = get_vote_weight(voter_id, economy_score)
        voter_weights[voter_id] = weight
        if cid in weighted_votes:
            weighted_votes[cid] += weight

    # Determine total possible votes and majority threshold
    total_possible = sum(get_vote_weight(r, economy_score) for r in COLUMBIA_VOTER_ROLES)
    majority_threshold = total_possible // 2 + 1  # strict majority

    # Find winner — must exceed majority threshold; ties = no winner
    sorted_candidates = sorted(weighted_votes.items(), key=lambda x: x[1], reverse=True)
    winner = None
    if sorted_candidates:
        top_votes = sorted_candidates[0][1]
        if top_votes >= majority_threshold:
            # Check for tie at the top
            tied = [c for c, v in sorted_candidates if v == top_votes]
            if len(tied) == 1:
                winner = tied[0]
            # else: tie — no winner

    # Apply post-election effects
    seat_changed = None
    if winner:
        if election_type == "parliamentary_midterm":
            seat_changed = _apply_midterm_result(client, sim_run_id, round_num, winner, contested_seat_role)
        elif election_type == "presidential":
            _apply_presidential_result(client, sim_run_id, round_num, winner)

    # Store result
    result_row = {
        "sim_run_id": sim_run_id,
        "election_type": election_type,
        "election_round": round_num,
        "country_code": "columbia",
        "winner_role_id": winner,
        "ai_score": round(economy_score, 4),  # stored as economy_score in ai_score column
        "participant_votes": weighted_votes,
        "population_votes": {"economy_score": round(economy_score, 4),
                             "has_bonus": has_bonus,
                             "stability": stability,
                             "inflation": inflation},
        "total_votes": weighted_votes,
        "seat_changed": seat_changed,
    }
    client.table("election_results").insert(result_row).execute()

    # Build narrative
    bonus_note = " (opposition bonus active)" if has_bonus else ""
    votes_summary = ", ".join(
        f"{c}: {weighted_votes[c]}" for c, _ in sorted_candidates
    )

    if winner is None:
        narrative = (f"ELECTION RESULT ({election_type}): No winner — tied or no majority.{bonus_note} "
                     f"Economy score: {economy_score:.2f}. Votes: {votes_summary}. "
                     f"Majority needed: {majority_threshold}/{total_possible}.")
    elif election_type == "presidential":
        narrative = (f"ELECTION RESULT ({election_type}): {winner} elected President of Columbia!{bonus_note} "
                     f"Economy score: {economy_score:.2f}. Votes: {votes_summary}.")
    elif seat_changed:
        narrative = (f"ELECTION RESULT ({election_type}): {winner} elected to Columbia Parliament!{bonus_note} "
                     f"Takes seat from {contested_seat_role}. "
                     f"Economy score: {economy_score:.2f}. Votes: {votes_summary}.")
    else:
        narrative = (f"ELECTION RESULT ({election_type}): {winner} wins!{bonus_note} "
                     f"Economy score: {economy_score:.2f}. Votes: {votes_summary}.")

    # Observatory event
    scenario_id = _get_scenario_id(client, sim_run_id)
    _write_event(client, sim_run_id, scenario_id, round_num, "columbia",
                 "election_result", narrative,
                 {"winner": winner, "economy_score": round(economy_score, 4),
                  "has_bonus": has_bonus,
                  "weighted_votes": weighted_votes,
                  "total_possible": total_possible,
                  "majority_threshold": majority_threshold,
                  "seat_changed": seat_changed})

    logger.info("[election] %s resolved: winner=%s economy=%.2f bonus=%s",
                election_type, winner, economy_score, has_bonus)

    return {
        "success": True,
        "winner": winner,
        "economy_score": round(economy_score, 4),
        "has_bonus": has_bonus,
        "weighted_votes": weighted_votes,
        "total_possible": total_possible,
        "majority_threshold": majority_threshold,
        "seat_changed": seat_changed,
        "narrative": narrative,
    }


# ── Post-Election Effects ─────────────────────────────────────────────────

def _apply_midterm_result(
    client, sim_run_id: str, round_num: int,
    winner: str, contested_seat_role: str | None,
) -> str | None:
    """Apply mid-term parliament seat change."""
    if not contested_seat_role or winner == contested_seat_role:
        return None

    # Remove old holder's membership (member_reelection)
    client.table("org_memberships").delete() \
        .eq("sim_run_id", sim_run_id) \
        .eq("org_id", "columbia_parliament") \
        .eq("role_id", contested_seat_role).execute()

    # Add winner to parliament
    client.table("org_memberships").insert({
        "sim_run_id": sim_run_id,
        "country_id": "columbia",
        "org_id": "columbia_parliament",
        "role_id": winner,
        "role_in_org": "member",
        "has_veto": False,
        "seat_type": "individual_seat",
    }).execute()

    logger.info("[election] Parliament seat: %s → %s", contested_seat_role, winner)
    return contested_seat_role


def _apply_presidential_result(
    client, sim_run_id: str, round_num: int, winner: str,
) -> None:
    """Apply presidential election: transfer head_of_state position."""
    # Find current HoS (Dealer)
    hos_roles = client.table("roles").select("id,positions") \
        .eq("sim_run_id", sim_run_id).eq("country_id", "columbia").execute().data or []

    old_hos_id = None
    for r in hos_roles:
        positions = r.get("positions") or []
        if "head_of_state" in positions:
            old_hos_id = r["id"]
            # Remove head_of_state from old HoS
            new_positions = [p for p in positions if p != "head_of_state"]
            client.table("roles").update({"positions": new_positions}) \
                .eq("sim_run_id", sim_run_id).eq("id", old_hos_id).execute()
            break

    # Add head_of_state to winner
    winner_role = client.table("roles").select("positions") \
        .eq("sim_run_id", sim_run_id).eq("id", winner).limit(1).execute().data
    if winner_role:
        winner_positions = winner_role[0].get("positions") or []
        if "head_of_state" not in winner_positions:
            winner_positions = ["head_of_state"] + winner_positions
            client.table("roles").update({"positions": winner_positions}) \
                .eq("sim_run_id", sim_run_id).eq("id", winner).execute()

    # Recompute role actions for both affected roles
    try:
        from engine.services.position_helpers import recompute_role_actions
        if old_hos_id:
            recompute_role_actions(client, sim_run_id, old_hos_id)
        recompute_role_actions(client, sim_run_id, winner)
    except Exception as e:
        logger.warning("[election] Failed to recompute role actions: %s", e)

    logger.info("[election] Presidency transfer: %s → %s", old_hos_id, winner)


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


def get_active_election(sim_run_id: str, round_num: int) -> dict | None:
    """Check if there is an active election in this round (from key_events)."""
    client = get_client()
    sim = client.table("sim_runs").select("key_events") \
        .eq("id", sim_run_id).limit(1).execute().data
    if not sim:
        return None

    key_events = sim[0].get("key_events") or []
    for ev in key_events:
        if ev.get("type") != "election":
            continue
        if ev.get("round") == round_num:
            return {
                "election_type": ev.get("subtype", ""),
                "election_round": round_num,
                "nominations_round": ev.get("nominations_round", round_num - 1),
                "country_code": ev.get("country_code", "columbia"),
                "name": ev.get("name", ""),
            }
        if ev.get("nominations_round") == round_num:
            return {
                "election_type": ev.get("subtype", ""),
                "election_round": ev.get("round"),
                "nominations_round": round_num,
                "country_code": ev.get("country_code", "columbia"),
                "name": ev.get("name", ""),
                "is_nominations_phase": True,
            }
    return None


def _is_head_of_state(role: dict) -> bool:
    """Check if a role currently holds head_of_state position."""
    positions = role.get("positions") or []
    if "head_of_state" in positions:
        return True
    return role.get("position_type", "") == "head_of_state"


def _get_parliament_membership(client, sim_run_id: str, role_id: str) -> dict | None:
    """Get a role's parliament membership if any."""
    result = client.table("org_memberships").select("role_in_org") \
        .eq("sim_run_id", sim_run_id).eq("org_id", "columbia_parliament") \
        .eq("role_id", role_id).limit(1).execute().data
    return result[0] if result else None


def _get_scenario_id(client, sim_run_id):
    """Get scenario_id for a sim run (used for observatory events)."""
    try:
        r = client.table("sim_runs").select("scenario_id").eq("id", sim_run_id).limit(1).execute()
        return r.data[0]["scenario_id"] if r.data else None
    except Exception:
        return None


def _write_event(client, sim_run_id, scenario_id, round_num, country_code, event_type, summary, payload):
    """Write an observatory event."""
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
