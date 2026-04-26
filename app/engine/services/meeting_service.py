"""Meeting service — CRUD operations for bilateral meetings and messages.

Handles meeting lifecycle: creation (on invitation accept), messaging,
turn enforcement, and meeting completion.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from engine.services.supabase import get_client

logger = logging.getLogger(__name__)


def create_meeting(
    sim_run_id: str,
    invitation_id: str,
    participant_a_role_id: str,
    participant_a_country: str,
    participant_b_role_id: str,
    participant_b_country: str,
    agenda: Optional[str] = None,
    round_num: Optional[int] = None,
) -> dict:
    """Create a meeting record when an invitation is accepted.

    Returns the created meeting row dict, or raises on failure.
    """
    client = get_client()
    row = {
        "sim_run_id": sim_run_id,
        "invitation_id": invitation_id,
        "round_num": round_num,
        "participant_a_role_id": participant_a_role_id,
        "participant_a_country": participant_a_country,
        "participant_b_role_id": participant_b_role_id,
        "participant_b_country": participant_b_country,
        "agenda": agenda,
        "status": "active",
        "turn_count": 0,
        "max_turns": 16,
        "modality": "text",
        "metadata": {},
    }
    result = client.table("meetings").insert(row).execute()
    if not result.data:
        logger.error("[meeting] Failed to insert meeting for invitation %s", invitation_id)
        return {"success": False, "error": "Failed to create meeting record"}
    meeting = result.data[0]
    logger.info(
        "[meeting] Created meeting %s for invitation %s (%s vs %s)",
        meeting["id"], invitation_id, participant_a_role_id, participant_b_role_id,
    )
    return meeting


def send_message(
    meeting_id: str,
    role_id: str,
    country_code: str,
    content: str,
) -> dict:
    """Send a message in a meeting.

    Validates the meeting is active and turn_count < max_turns.
    Inserts the message row and increments turn_count on the meeting.
    Returns {"success": True/False, "message": ..., "narrative": ...}.
    """
    client = get_client()

    # Fetch meeting
    meeting_rows = client.table("meetings").select("*") \
        .eq("id", meeting_id).limit(1).execute().data
    if not meeting_rows:
        return {"success": False, "narrative": "Meeting not found"}
    meeting = meeting_rows[0]

    # Validate meeting is active
    if meeting["status"] != "active":
        return {"success": False, "narrative": "Meeting is no longer active"}

    # Validate sender is a participant
    if role_id not in (meeting["participant_a_role_id"], meeting["participant_b_role_id"]):
        return {"success": False, "narrative": "You are not a participant in this meeting"}

    # Enforce max turns
    if meeting["turn_count"] >= meeting["max_turns"]:
        return {"success": False, "narrative": "Maximum number of turns reached. End the meeting."}

    new_turn = meeting["turn_count"] + 1

    # Insert message
    msg_row = {
        "meeting_id": meeting_id,
        "role_id": role_id,
        "country_code": country_code,
        "content": content[:2000],  # Cap message length
        "channel": "text",
        "turn_number": new_turn,
    }
    msg_result = client.table("meeting_messages").insert(msg_row).execute()
    if not msg_result.data:
        return {"success": False, "narrative": "Failed to save message"}

    # Increment turn count
    turn_result = client.table("meetings").update({"turn_count": new_turn}) \
        .eq("id", meeting_id).execute()
    if not turn_result.data:
        logger.warning("[meeting] Failed to update turn_count for meeting %s", meeting_id)

    logger.info("[meeting] Message in %s by %s (turn %d/%d)",
                meeting_id, role_id, new_turn, meeting["max_turns"])

    return {
        "success": True,
        "message": msg_result.data[0],
        "narrative": f"Message sent (turn {new_turn}/{meeting['max_turns']})",
    }


def end_meeting(meeting_id: str, role_id: str) -> dict:
    """End a meeting. Either participant can end it.

    Sets status='completed' and ended_at, inserts a system message.
    Returns {"success": True/False, "narrative": ...}.
    """
    client = get_client()

    meeting_rows = client.table("meetings").select("*") \
        .eq("id", meeting_id).limit(1).execute().data
    if not meeting_rows:
        return {"success": False, "narrative": "Meeting not found"}
    meeting = meeting_rows[0]

    if meeting["status"] != "active":
        return {"success": False, "narrative": "Meeting is already ended"}

    if role_id not in (meeting["participant_a_role_id"], meeting["participant_b_role_id"]):
        return {"success": False, "narrative": "You are not a participant in this meeting"}

    now = datetime.now(timezone.utc).isoformat()
    upd_result = client.table("meetings").update({
        "status": "completed",
        "ended_at": now,
    }).eq("id", meeting_id).execute()
    if not upd_result.data:
        return {"success": False, "narrative": "Failed to update meeting status"}

    # Insert system message noting who ended the meeting
    sys_result = client.table("meeting_messages").insert({
        "meeting_id": meeting_id,
        "role_id": role_id,
        "country_code": meeting.get("participant_a_country") if role_id == meeting["participant_a_role_id"] else meeting.get("participant_b_country"),
        "content": f"Meeting ended by {role_id}",
        "channel": "system",
        "turn_number": meeting["turn_count"] + 1,
    }).execute()
    if not sys_result.data:
        logger.warning("[meeting] Failed to insert system message for meeting %s end", meeting_id)

    logger.info("[meeting] Meeting %s ended by %s after %d turns",
                meeting_id, role_id, meeting["turn_count"])

    return {"success": True, "narrative": "Meeting ended."}


def get_meeting(meeting_id: str) -> Optional[dict]:
    """Get a meeting with all its messages.

    Returns {meeting: {...}, messages: [...]} or None if not found.
    """
    client = get_client()

    meeting_rows = client.table("meetings").select("*") \
        .eq("id", meeting_id).limit(1).execute().data
    if not meeting_rows:
        return None

    messages = client.table("meeting_messages").select("*") \
        .eq("meeting_id", meeting_id) \
        .order("created_at") \
        .execute().data or []

    return {
        "meeting": meeting_rows[0],
        "messages": messages,
    }


def save_transcript(meeting_id: str, transcript: str) -> dict:
    """Save formatted transcript to meeting record.

    Called after avatar conversation completes.
    """
    client = get_client()
    try:
        result = client.table("meetings").update({
            "transcript": transcript,
        }).eq("id", meeting_id).execute()
        if result.data:
            logger.info("[meeting] Transcript saved for meeting %s (%d chars)",
                       meeting_id, len(transcript))
            return {"success": True}
        return {"success": False, "narrative": "Meeting not found"}
    except Exception as e:
        logger.error("[meeting] Failed to save transcript for %s: %s", meeting_id, e)
        return {"success": False, "narrative": str(e)}


def update_meeting_metadata(meeting_id: str, metadata_update: dict) -> dict:
    """Merge new keys into meeting metadata JSONB.

    Used for storing intent_note, avatar_context, voice_conversation_id.
    Reads existing metadata, merges, writes back.
    """
    client = get_client()
    try:
        # Read current metadata
        meeting_rows = client.table("meetings").select("metadata") \
            .eq("id", meeting_id).limit(1).execute().data
        if not meeting_rows:
            return {"success": False, "narrative": "Meeting not found"}

        current = meeting_rows[0].get("metadata") or {}
        current.update(metadata_update)

        result = client.table("meetings").update({
            "metadata": current,
        }).eq("id", meeting_id).execute()
        if result.data:
            return {"success": True}
        return {"success": False, "narrative": "Update failed"}
    except Exception as e:
        logger.error("[meeting] Failed to update metadata for %s: %s", meeting_id, e)
        return {"success": False, "narrative": str(e)}


def get_meeting_messages(meeting_id: str) -> list[dict]:
    """Get all messages for a meeting, ordered chronologically.

    Simple helper used by avatar_service to build conversation history.
    """
    client = get_client()
    try:
        result = client.table("meeting_messages").select("*") \
            .eq("meeting_id", meeting_id) \
            .order("created_at") \
            .execute()
        return result.data or []
    except Exception as e:
        logger.warning("[meeting] Failed to get messages for %s: %s", meeting_id, e)
        return []


def get_active_meetings(sim_run_id: str, role_id: str) -> list[dict]:
    """Get all active meetings for a role in a SIM run.

    Checks both participant_a and participant_b columns.
    Returns list of meeting dicts.
    """
    client = get_client()

    # Supabase doesn't support OR across columns in a single query easily,
    # so we run two queries and deduplicate.
    as_a = client.table("meetings").select("*") \
        .eq("sim_run_id", sim_run_id) \
        .eq("participant_a_role_id", role_id) \
        .eq("status", "active") \
        .execute().data or []

    as_b = client.table("meetings").select("*") \
        .eq("sim_run_id", sim_run_id) \
        .eq("participant_b_role_id", role_id) \
        .eq("status", "active") \
        .execute().data or []

    # Deduplicate by meeting id
    seen = set()
    result = []
    for m in as_a + as_b:
        if m["id"] not in seen:
            seen.add(m["id"])
            result.append(m)

    return result
