"""Basing Rights Engine — single source of truth for grant/revoke.

Called by:
- Standalone basing_rights action (unilateral grant/revoke)
- Transaction engine (basing rights as part of a deal)
- Template seed (initial alliance basing from scenario data)

All paths write to the `basing_rights` table. This is the ONLY place
basing rights state is managed.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from engine.services.supabase import get_client

logger = logging.getLogger(__name__)


def grant_basing_rights(
    sim_run_id: str,
    host_country: str,
    guest_country: str,
    round_num: int,
    granted_by_role: str = "",
    source: str = "direct",
) -> dict:
    """Grant basing rights: guest can deploy on host territory.

    Upserts into basing_rights table. If a revoked row exists, reactivates it.
    Writes an observatory event notifying both countries.

    Returns ``{success, status, message}``.
    """
    client = get_client()

    try:
        client.table("basing_rights").upsert({
            "sim_run_id": sim_run_id,
            "host_country": host_country,
            "guest_country": guest_country,
            "granted_by_role": granted_by_role,
            "granted_round": round_num,
            "status": "active",
            "revoked_round": None,
            "source": source,
        }, on_conflict="sim_run_id,host_country,guest_country").execute()
    except Exception as e:
        logger.warning("basing_rights grant failed: %s", e)
        return {"success": False, "status": "error", "message": str(e)}

    # Notify both countries
    _write_event(client, sim_run_id, round_num, host_country,
                 "basing_rights_granted",
                 f"{host_country} grants basing rights to {guest_country}",
                 {"host": host_country, "guest": guest_country, "source": source})
    _write_event(client, sim_run_id, round_num, guest_country,
                 "basing_rights_received",
                 f"{guest_country} receives basing rights from {host_country}",
                 {"host": host_country, "guest": guest_country, "source": source})

    logger.info("[basing] GRANTED: %s → %s (source=%s)", host_country, guest_country, source)
    return {"success": True, "status": "active", "message": f"{host_country} grants basing to {guest_country}"}


def revoke_basing_rights(
    sim_run_id: str,
    host_country: str,
    guest_country: str,
    round_num: int,
) -> dict:
    """Revoke basing rights. Guest can no longer deploy on host territory.

    Caller MUST have already validated that guest has no troops on host soil
    (via basing_rights_validator). This function does NOT re-check.

    Returns ``{success, status, message}``.
    """
    client = get_client()

    try:
        client.table("basing_rights").update({
            "status": "revoked",
            "revoked_round": round_num,
        }).eq("sim_run_id", sim_run_id) \
          .eq("host_country", host_country) \
          .eq("guest_country", guest_country).execute()
    except Exception as e:
        logger.warning("basing_rights revoke failed: %s", e)
        return {"success": False, "status": "error", "message": str(e)}

    # Notify both countries
    _write_event(client, sim_run_id, round_num, host_country,
                 "basing_rights_revoked",
                 f"{host_country} revokes basing rights from {guest_country}",
                 {"host": host_country, "guest": guest_country})
    _write_event(client, sim_run_id, round_num, guest_country,
                 "basing_rights_lost",
                 f"{guest_country} loses basing rights from {host_country} — must withdraw forces",
                 {"host": host_country, "guest": guest_country})

    logger.info("[basing] REVOKED: %s → %s", host_country, guest_country)
    return {"success": True, "status": "revoked", "message": f"{host_country} revokes basing from {guest_country}"}


def get_active_basing_rights(
    sim_run_id: str,
    country_code: str | None = None,
) -> list[dict]:
    """Return all active basing rights. Optionally filter by host or guest."""
    client = get_client()
    q = client.table("basing_rights").select("*") \
        .eq("sim_run_id", sim_run_id) \
        .eq("status", "active")
    if country_code:
        q = q.or_(f"host_country.eq.{country_code},guest_country.eq.{country_code}")
    res = q.execute()
    return res.data or []


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_event(client, sim_run_id, round_num, country_code, event_type, summary, payload):
    scenario_id = None
    try:
        r = client.table("sim_runs").select("scenario_id").eq("id", sim_run_id).limit(1).execute()
        if r.data:
            scenario_id = r.data[0].get("scenario_id")
    except Exception:
        pass
    if not scenario_id:
        return
    try:
        client.table("observatory_events").insert({
            "sim_run_id": sim_run_id,
            "scenario_id": scenario_id,
            "round_num": round_num,
            "event_type": event_type,
            "country_code": country_code,
            "summary": summary,
            "payload": payload,
        }).execute()
    except Exception as e:
        logger.debug("event write failed: %s", e)
