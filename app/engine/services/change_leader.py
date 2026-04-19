"""Change of Leader — 3-phase leadership change flow.

Implements CONTRACT_CHANGE_LEADER v1.0:
  Phase 1: Initiation (validate preconditions, create vote)
  Phase 2: Removal vote (strict majority of non-HoS citizens)
  Phase 3: Election vote (absolute majority of all citizens)

Source of truth: 3 DETAILED DESIGN/CONTRACTS/CONTRACT_CHANGE_LEADER.md
"""

import logging
import math
from datetime import datetime, timezone, timedelta

from engine.services.supabase import get_client
from engine.services.common import write_event, get_scenario_id
from engine.services.position_helpers import transfer_position, recompute_role_actions

logger = logging.getLogger(__name__)

VOTE_TIMEOUT_MINUTES = 10
DEFAULT_THRESHOLD = 4.0


def initiate_change_leader(
    sim_run_id: str,
    round_num: int,
    role_id: str,
    country_code: str,
) -> dict:
    """Phase 1: Initiate a leadership change.

    Validates preconditions per CONTRACT_CHANGE_LEADER:
    - Country has 3+ active roles
    - Stability ≤ threshold (default 4.0)
    - Initiator is non-HoS citizen of the country
    - No existing active vote this round
    """
    client = get_client()

    # Load country roles
    roles = (
        client.table("roles")
        .select("id, character_name, positions, position_type, is_head_of_state, country_id, status")
        .eq("sim_run_id", sim_run_id)
        .eq("country_id", country_code)
        .eq("status", "active")
        .execute()
    ).data or []

    if len(roles) < 3:
        return {"success": False, "narrative": f"Country {country_code} has only {len(roles)} active roles (need 3+)"}

    def _is_hos(r: dict) -> bool:
        """Check if role is HoS using positions array (primary) or legacy fields (fallback)."""
        positions = r.get("positions") or []
        if positions:
            return "head_of_state" in positions
        # Fallback to legacy fields
        return bool(r.get("is_head_of_state")) or r.get("position_type") == "head_of_state"

    # Find current HoS
    hos = [r for r in roles if _is_hos(r)]
    if not hos:
        return {"success": False, "narrative": f"Country {country_code} has no Head of State"}
    hos_role = hos[0]

    # Check initiator identity
    initiator = [r for r in roles if r["id"] == role_id]
    if not initiator:
        return {"success": False, "narrative": f"Role {role_id} not found in {country_code}"}
    is_voluntary = _is_hos(initiator[0])

    if not is_voluntary:
        # Citizen-initiated: check stability threshold
        country = (
            client.table("countries")
            .select("stability")
            .eq("sim_run_id", sim_run_id)
            .eq("id", country_code)
            .execute()
        ).data
        if not country:
            return {"success": False, "narrative": f"Country {country_code} not found"}

        stability = country[0].get("stability", 10)
        if stability > DEFAULT_THRESHOLD:
            return {"success": False, "narrative": f"Stability {stability:.1f} is above threshold {DEFAULT_THRESHOLD}. Leadership change requires stability ≤ {DEFAULT_THRESHOLD}"}

    # Check no existing active vote this round
    existing = (
        client.table("leadership_votes")
        .select("id")
        .eq("sim_run_id", sim_run_id)
        .eq("country_code", country_code)
        .eq("round_num", round_num)
        .in_("status", ["voting"])
        .execute()
    ).data
    if existing:
        return {"success": False, "narrative": "A leadership change vote is already in progress this round"}

    # HoS voluntary resignation: skip removal vote, go straight to election
    if is_voluntary:
        # Remove HoS position immediately
        old_positions = list(hos_role.get("positions") or [])
        new_positions = [p for p in old_positions if p != "head_of_state"]
        client.table("roles").update({
            "positions": new_positions,
            "is_head_of_state": False,
        }).eq("sim_run_id", sim_run_id).eq("id", hos_role["id"]).execute()

        recompute_role_actions(client, sim_run_id, hos_role["id"])

        hos_name = hos_role["character_name"]
        scenario_id = get_scenario_id(client, sim_run_id)

        write_event(
            client, sim_run_id, scenario_id, round_num,
            country_code, "change_leader_removal",
            f"{hos_name} RESIGNED as Head of State of {country_code}. Election for new leader begins.",
            {"vote_id": None, "resigned": True, "removed": hos_role["id"]},
            phase="A", category="political", role_name=hos_name,
        )

        # Create election phase directly
        total_voters = len(roles)
        election_required = total_voters // 2 + 1
        expires_at = (datetime.now(timezone.utc) + timedelta(minutes=VOTE_TIMEOUT_MINUTES)).isoformat()

        election_vote = client.table("leadership_votes").insert({
            "sim_run_id": sim_run_id,
            "round_num": round_num,
            "country_code": country_code,
            "phase": "election",
            "status": "voting",
            "initiated_by": role_id,
            "target_role": hos_role["id"],
            "votes": {},
            "required_majority": election_required,
            "expires_at": expires_at,
        }).execute()

        election_id = election_vote.data[0]["id"] if election_vote.data else None

        logger.info("HoS %s resigned in %s, election started (vote %s)", hos_role["id"], country_code, election_id)

        return {
            "success": True,
            "narrative": f"{hos_name} resigned. Election for new Head of State open. Need {election_required} votes.",
            "vote_id": election_id,
            "phase": "election",
            "resigned": True,
        }

    # Citizen-initiated: create removal vote
    non_hos = [r for r in roles if not _is_hos(r)]
    required = math.ceil(len(non_hos) / 2) + (0 if len(non_hos) % 2 == 1 else 1)
    # Strict majority: more than half
    # 2 non-HoS → need 2, 3 → need 2, 4 → need 3, 6 → need 4
    required = len(non_hos) // 2 + 1

    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=VOTE_TIMEOUT_MINUTES)).isoformat()

    vote_record = {
        "sim_run_id": sim_run_id,
        "round_num": round_num,
        "country_code": country_code,
        "phase": "removal",
        "status": "voting",
        "initiated_by": role_id,
        "target_role": hos_role["id"],
        "votes": {},
        "required_majority": required,
        "expires_at": expires_at,
    }

    result = client.table("leadership_votes").insert(vote_record).execute()
    vote_id = result.data[0]["id"] if result.data else None

    # Write event
    scenario_id = get_scenario_id(client, sim_run_id)
    initiator_name = initiator[0]["character_name"]
    hos_name = hos_role["character_name"]
    write_event(
        client, sim_run_id, scenario_id, round_num,
        country_code, "change_leader_initiated",
        f"Leadership change initiated by {initiator_name} against {hos_name} in {country_code}. Vote open for {VOTE_TIMEOUT_MINUTES} minutes.",
        {"vote_id": vote_id, "initiator": role_id, "target": hos_role["id"],
         "citizens": [r["id"] for r in roles], "required_majority": required},
        phase="A", category="political", role_name=initiator_name,
    )

    logger.info("Change leader initiated: %s vs %s in %s (vote %s)", role_id, hos_role["id"], country_code, vote_id)

    return {
        "success": True,
        "narrative": f"Leadership change initiated by {initiator_name}. {len(non_hos)} citizens vote on removing {hos_name}. Need {required} YES votes.",
        "vote_id": vote_id,
        "phase": "removal",
        "target": hos_role["id"],
        "voters": [r["id"] for r in non_hos],
        "required_majority": required,
    }


def cast_leader_vote(
    sim_run_id: str,
    vote_id: str,
    role_id: str,
    vote: str,
) -> dict:
    """Cast a vote in an active leadership change.

    For removal phase: vote = "yes" or "no"
    For election phase: vote = candidate role_id
    """
    client = get_client()

    record = (
        client.table("leadership_votes")
        .select("*")
        .eq("id", vote_id)
        .eq("sim_run_id", sim_run_id)
        .execute()
    ).data
    if not record:
        return {"success": False, "narrative": "Vote not found"}
    record = record[0]

    if record["status"] != "voting":
        return {"success": False, "narrative": f"Vote is {record['status']}, not open"}

    # Check expiry
    if record.get("expires_at"):
        expires = datetime.fromisoformat(record["expires_at"].replace("Z", "+00:00"))
        if datetime.now(timezone.utc) > expires:
            return {"success": False, "narrative": "Vote has expired"}

    # Record the vote
    votes = record.get("votes", {})
    votes[role_id] = vote

    client.table("leadership_votes").update({"votes": votes}).eq("id", vote_id).execute()

    return {
        "success": True,
        "narrative": f"Vote recorded: {role_id} → {vote}",
        "votes_cast": len(votes),
    }


def _check_auto_resolve(sim_run_id: str, vote_id: str) -> dict | None:
    """Check if a vote can be auto-resolved (majority already achieved).

    Returns resolution result if auto-resolved, None otherwise.
    """
    client = get_client()
    record = (
        client.table("leadership_votes")
        .select("*")
        .eq("id", vote_id)
        .eq("sim_run_id", sim_run_id)
        .execute()
    ).data
    if not record or record[0]["status"] != "voting":
        return None
    record = record[0]

    votes = record.get("votes", {})
    required = record.get("required_majority", 2)
    phase = record.get("phase", "removal")

    if phase == "removal":
        target_role = record.get("target_role", "")
        yes_count = sum(1 for rid, v in votes.items() if v == "yes" and rid != target_role)
        if yes_count >= required:
            return resolve_leader_vote(sim_run_id, vote_id)
    elif phase == "election":
        tallies: dict[str, int] = {}
        for rid, candidate in votes.items():
            tallies[candidate] = tallies.get(candidate, 0) + 1
        for candidate, count in tallies.items():
            if count >= required:
                return resolve_leader_vote(sim_run_id, vote_id)

    return None


def resolve_leader_vote(sim_run_id: str, vote_id: str) -> dict:
    """Resolve a leadership change vote (moderator triggers this).

    For removal phase: count YES/NO, apply if majority
    For election phase: count candidate votes, apply if majority
    """
    client = get_client()

    record = (
        client.table("leadership_votes")
        .select("*")
        .eq("id", vote_id)
        .eq("sim_run_id", sim_run_id)
        .execute()
    ).data
    if not record:
        return {"success": False, "narrative": "Vote not found"}
    record = record[0]

    votes = record.get("votes", {})
    required = record.get("required_majority", 2)
    phase = record.get("phase", "removal")
    country_code = record["country_code"]
    round_num = record["round_num"]
    scenario_id = get_scenario_id(client, sim_run_id)

    if phase == "removal":
        return _resolve_removal(client, sim_run_id, scenario_id, record, votes, required, country_code, round_num)
    elif phase == "election":
        return _resolve_election(client, sim_run_id, scenario_id, record, votes, required, country_code, round_num)

    return {"success": False, "narrative": f"Unknown vote phase: {phase}"}


def _resolve_removal(client, sim_run_id, scenario_id, record, votes, required, country_code, round_num):
    """Resolve removal vote: count YES vs NO among non-HoS citizens."""
    vote_id = record["id"]
    target_role = record.get("target_role", "")

    # Count YES votes (excluding HoS vote)
    yes_count = sum(1 for rid, v in votes.items() if v == "yes" and rid != target_role)
    no_count = sum(1 for rid, v in votes.items() if v == "no" and rid != target_role)

    passed = yes_count >= required

    if passed:
        # Remove HoS — remove 'head_of_state' from positions array + sync legacy fields
        target_data_full = client.table("roles").select("character_name, positions").eq("id", target_role).eq("sim_run_id", sim_run_id).execute()
        old_positions = list((target_data_full.data[0].get("positions") or []) if target_data_full.data else [])
        new_positions = [p for p in old_positions if p != "head_of_state"]
        client.table("roles").update({
            "positions": new_positions,
            "is_head_of_state": False,  # legacy sync
        }).eq("sim_run_id", sim_run_id).eq("id", target_role).execute()

        # Recompute actions for the removed HoS
        recompute_role_actions(client, sim_run_id, target_role)

        # Get target name for event
        target_data = target_data_full
        target_name = target_data.data[0]["character_name"] if target_data.data else target_role

        client.table("leadership_votes").update({
            "status": "passed",
            "resolved_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", vote_id).execute()

        write_event(
            client, sim_run_id, scenario_id, round_num,
            country_code, "change_leader_removal",
            f"{target_name} REMOVED as Head of State of {country_code}. Vote: {yes_count} YES, {no_count} NO (needed {required}).",
            {"vote_id": vote_id, "yes": yes_count, "no": no_count, "required": required, "removed": target_role},
            phase="A", category="political",
        )

        # Create election phase vote
        all_roles = (
            client.table("roles")
            .select("id")
            .eq("sim_run_id", sim_run_id)
            .eq("country_id", country_code)
            .eq("status", "active")
            .execute()
        ).data or []
        total_voters = len(all_roles)
        election_required = total_voters // 2 + 1

        expires_at = (datetime.now(timezone.utc) + timedelta(minutes=VOTE_TIMEOUT_MINUTES)).isoformat()

        election_vote = client.table("leadership_votes").insert({
            "sim_run_id": sim_run_id,
            "round_num": round_num,
            "country_code": country_code,
            "phase": "election",
            "status": "voting",
            "initiated_by": record["initiated_by"],
            "target_role": target_role,
            "votes": {},
            "required_majority": election_required,
            "expires_at": expires_at,
        }).execute()

        election_id = election_vote.data[0]["id"] if election_vote.data else None

        return {
            "success": True,
            "narrative": f"{target_name} removed ({yes_count}-{no_count}). Election phase started. Need {election_required} votes for new HoS.",
            "outcome": "removed",
            "election_vote_id": election_id,
        }
    else:
        client.table("leadership_votes").update({
            "status": "failed",
            "resolved_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", vote_id).execute()

        write_event(
            client, sim_run_id, scenario_id, round_num,
            country_code, "change_leader_removal",
            f"Leadership change FAILED in {country_code}. Vote: {yes_count} YES, {no_count} NO (needed {required}).",
            {"vote_id": vote_id, "yes": yes_count, "no": no_count, "required": required},
            phase="A", category="political",
        )

        return {
            "success": True,
            "narrative": f"Removal vote failed ({yes_count}-{no_count}, needed {required}). HoS remains.",
            "outcome": "kept",
        }


def _resolve_election(client, sim_run_id, scenario_id, record, votes, required, country_code, round_num):
    """Resolve election vote: candidate with absolute majority wins."""
    vote_id = record["id"]

    # Count votes per candidate
    tallies: dict[str, int] = {}
    for rid, candidate in votes.items():
        tallies[candidate] = tallies.get(candidate, 0) + 1

    # Find winner (absolute majority)
    winner = None
    winner_votes = 0
    for candidate, count in sorted(tallies.items(), key=lambda x: -x[1]):
        if count >= required:
            winner = candidate
            winner_votes = count
            break

    if winner:
        old_hos = record.get("target_role", "")

        # Add 'head_of_state' to winner's positions array + sync legacy fields
        winner_role = client.table("roles").select("positions").eq("id", winner).eq("sim_run_id", sim_run_id).execute()
        winner_positions = list((winner_role.data[0].get("positions") or []) if winner_role.data else [])
        if "head_of_state" not in winner_positions:
            winner_positions.append("head_of_state")
        client.table("roles").update({
            "positions": winner_positions,
            "is_head_of_state": True,  # legacy sync
        }).eq("sim_run_id", sim_run_id).eq("id", winner).execute()

        # Recompute actions for new HoS (replaces old _migrate_hos_actions)
        recompute_role_actions(client, sim_run_id, winner)

        winner_data = client.table("roles").select("character_name").eq("id", winner).eq("sim_run_id", sim_run_id).execute()
        winner_name = winner_data.data[0]["character_name"] if winner_data.data else winner

        client.table("leadership_votes").update({
            "status": "passed",
            "winner_role": winner,
            "resolved_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", vote_id).execute()

        write_event(
            client, sim_run_id, scenario_id, round_num,
            country_code, "change_leader_elected",
            f"{winner_name} elected Head of State of {country_code} ({winner_votes} votes, needed {required}).",
            {"vote_id": vote_id, "winner": winner, "tallies": tallies, "required": required},
            phase="A", category="political",
        )

        return {
            "success": True,
            "narrative": f"{winner_name} elected as new Head of State ({winner_votes} votes).",
            "outcome": "elected",
            "winner": winner,
        }
    else:
        client.table("leadership_votes").update({
            "status": "failed",
            "resolved_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", vote_id).execute()

        write_event(
            client, sim_run_id, scenario_id, round_num,
            country_code, "change_leader_election_failed",
            f"No candidate achieved majority in {country_code}. Country is leaderless. Tallies: {tallies}",
            {"vote_id": vote_id, "tallies": tallies, "required": required},
            phase="A", category="political",
        )

        return {
            "success": True,
            "narrative": f"No candidate achieved majority (needed {required}). Country is leaderless.",
            "outcome": "leaderless",
            "tallies": tallies,
        }


def _migrate_hos_actions(client, sim_run_id: str, old_hos_id: str, new_hos_id: str) -> None:
    """DEPRECATED: Use recompute_role_actions() from position_helpers instead.

    Kept for backward compatibility — not called by new code paths.
    The positions-based recompute replaces this heuristic migration.
    """
    logger.warning("[change_leader] _migrate_hos_actions called but DEPRECATED — use recompute_role_actions()")
    return
