"""Transaction Engine — CONTRACT_TRANSACTIONS v1.0.

Pure service for exchange transactions. Actor-agnostic: same API for
human, AI, and moderator. No LLM calls. No agent logic.

Lifecycle:
    propose_exchange(proposal, sim_run_id) → {id, status, errors}
    respond_to_exchange(txn_id, response, ...) → {status}
    get_pending_proposals(country_or_role, sim_run_id) → list

Execution happens atomically inside ``respond_to_exchange`` when the
response is "accept" and both sides' assets validate.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from engine.services.supabase import get_client
from engine.services.transaction_validator import validate_proposal, validate_execution

logger = logging.getLogger(__name__)

# Tech transfer boosts (CARD_FORMULAS C.4)
NUCLEAR_TECH_BOOST = 0.20
AI_TECH_BOOST = 0.15


def propose_exchange(
    proposal: dict,
    sim_run_id: str,
    units: dict[str, dict] | None = None,
    country_state: dict[str, dict] | None = None,
    roles: dict[str, dict] | None = None,
) -> dict:
    """Validate and create a PENDING exchange transaction.

    If ``units`` / ``country_state`` / ``roles`` are not provided, they
    are loaded from the DB (convenience for callers that don't pre-load).

    Returns ``{transaction_id, status, errors}``.
    """
    client = get_client()
    round_num = proposal.get("round_num", 0)

    # Load context if not provided
    if units is None or country_state is None:
        units, country_state = _load_world_state(client, sim_run_id, round_num)
    if roles is None:
        roles = _load_roles(client)

    # Validate proposer side
    report = validate_proposal(proposal, units, country_state, roles)
    if not report["valid"]:
        return {"transaction_id": None, "status": "rejected", "errors": report["errors"]}

    normalized = report["normalized"]

    # Look up scenario_id for denorm
    scenario_id = _get_scenario_id(client, sim_run_id)

    # Create PENDING record
    row = {
        "sim_run_id": sim_run_id,
        "scenario_id": scenario_id,
        "round_num": round_num,
        "proposer": normalized["proposer_country_code"],
        "counterpart": normalized["counterpart_country_code"],
        "offer": normalized["offer"],
        "request": normalized["request"],
        "terms": normalized.get("rationale", ""),
        "status": "pending",
    }
    res = client.table("exchange_transactions").insert(row).execute()
    txn_id = res.data[0]["id"]

    # Write event
    _write_event(client, sim_run_id, scenario_id, round_num,
                 "transaction_proposed", normalized["proposer_country_code"],
                 f"{normalized['proposer_country_code']} proposes exchange to "
                 f"{normalized['counterpart_country_code']}: "
                 f"offer={_summarize_assets(normalized['offer'])}, "
                 f"request={_summarize_assets(normalized['request'])}",
                 {"transaction_id": txn_id, "offer": normalized["offer"],
                  "request": normalized["request"]})

    logger.info("[txn] proposed %s: %s → %s", txn_id,
                normalized["proposer_country_code"], normalized["counterpart_country_code"])

    return {"transaction_id": txn_id, "status": "pending", "errors": []}


def respond_to_exchange(
    transaction_id: str,
    response: str,
    sim_run_id: str,
    rationale: str = "",
    counter_offer: dict | None = None,
    counter_request: dict | None = None,
) -> dict:
    """Respond to a pending transaction: accept, decline, or counter.

    On accept: validates both sides → executes atomically.
    On counter: updates the transaction with counter terms.
    On decline: closes the transaction.

    Returns ``{status, changes?, errors?}``.
    """
    client = get_client()

    # Load the transaction
    res = client.table("exchange_transactions").select("*") \
        .eq("id", transaction_id).limit(1).execute()
    if not res.data:
        return {"status": "error", "errors": ["Transaction not found"]}
    txn = res.data[0]

    if txn["status"] not in ("pending", "countered"):
        return {"status": txn["status"], "errors": ["Transaction not in respondable state"]}

    round_num = txn["round_num"]
    scenario_id = txn.get("scenario_id")

    if response == "decline":
        client.table("exchange_transactions").update({
            "status": "declined",
        }).eq("id", transaction_id).execute()

        _write_event(client, sim_run_id, scenario_id, round_num,
                     "transaction_declined", txn["counterpart"],
                     f"{txn['counterpart']} declined exchange from {txn['proposer']}",
                     {"transaction_id": transaction_id})

        return {"status": "declined"}

    if response == "counter":
        if not counter_offer and not counter_request:
            return {"status": "error", "errors": ["Counter requires counter_offer or counter_request"]}

        client.table("exchange_transactions").update({
            "status": "countered",
            "offer": counter_offer or txn["offer"],
            "request": counter_request or txn["request"],
            "terms": txn.get("terms", "") + f"\n[COUNTER] {rationale}",
        }).eq("id", transaction_id).execute()

        _write_event(client, sim_run_id, scenario_id, round_num,
                     "transaction_countered", txn["counterpart"],
                     f"{txn['counterpart']} counter-offered to {txn['proposer']}",
                     {"transaction_id": transaction_id,
                      "counter_offer": counter_offer, "counter_request": counter_request})

        return {"status": "countered"}

    if response == "accept":
        # Load current world state for execution validation
        units, country_state = _load_world_state(client, sim_run_id, round_num)

        # Build the effective deal (may be counter terms)
        effective_offer = txn["offer"]
        effective_request = txn["request"]

        # Validate BOTH sides at execution time
        deal = {
            "proposer_country_code": txn["proposer"],
            "counterpart_country_code": txn["counterpart"],
            "scope": "country",  # TODO: store scope on txn row
            "offer": effective_offer,
            "request": effective_request,
        }
        exec_report = validate_execution(deal, units, country_state)
        if not exec_report["valid"]:
            client.table("exchange_transactions").update({
                "status": "failed_validation",
            }).eq("id", transaction_id).execute()

            _write_event(client, sim_run_id, scenario_id, round_num,
                         "transaction_failed", txn["proposer"],
                         f"Exchange {txn['proposer']}↔{txn['counterpart']} failed validation: "
                         f"{exec_report['errors'][:2]}",
                         {"transaction_id": transaction_id, "errors": exec_report["errors"]})

            return {"status": "failed_validation", "errors": exec_report["errors"]}

        # EXECUTE atomically
        changes = _execute_transfers(
            client, sim_run_id, round_num,
            txn["proposer"], txn["counterpart"],
            effective_offer, effective_request,
            units, country_state,
        )

        client.table("exchange_transactions").update({
            "status": "executed",
            "executed_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", transaction_id).execute()

        _write_event(client, sim_run_id, scenario_id, round_num,
                     "transaction_executed", txn["proposer"],
                     f"Exchange executed: {txn['proposer']}↔{txn['counterpart']} — {', '.join(changes[:3])}",
                     {"transaction_id": transaction_id, "changes": changes})

        logger.info("[txn] EXECUTED %s: %s ↔ %s — %d changes",
                    transaction_id, txn["proposer"], txn["counterpart"], len(changes))

        return {"status": "executed", "changes": changes}

    return {"status": "error", "errors": [f"Invalid response: {response!r}"]}


def get_pending_proposals(
    country_code: str,
    sim_run_id: str,
) -> list[dict]:
    """Return pending proposals where this country is the counterpart."""
    client = get_client()
    res = client.table("exchange_transactions").select("*") \
        .eq("sim_run_id", sim_run_id) \
        .eq("counterpart", country_code) \
        .eq("status", "pending") \
        .order("created_at", desc=True) \
        .execute()
    return res.data or []


# ---------------------------------------------------------------------------
# Internal: atomic execution
# ---------------------------------------------------------------------------


def _execute_transfers(
    client, sim_run_id: str, round_num: int,
    proposer_cc: str, counterpart_cc: str,
    offer: dict, request: dict,
    units: dict, country_state: dict,
) -> list[str]:
    """Execute all asset transfers atomically. Returns list of change descriptions."""
    changes: list[str] = []

    # --- COINS (proposer offers to counterpart) ---
    offer_coins = int(offer.get("coins") or 0)
    if offer_coins > 0:
        _transfer_coins(client, sim_run_id, round_num, proposer_cc, counterpart_cc, offer_coins, changes)

    # --- COINS (counterpart gives to proposer via request) ---
    request_coins = int(request.get("coins") or 0)
    if request_coins > 0:
        _transfer_coins(client, sim_run_id, round_num, counterpart_cc, proposer_cc, request_coins, changes)

    # --- UNITS (proposer gives) ---
    for code in (offer.get("units") or []):
        _transfer_unit(client, sim_run_id, round_num, code, proposer_cc, counterpart_cc, changes)

    # --- UNITS (counterpart gives via request) ---
    for code in (request.get("units") or []):
        _transfer_unit(client, sim_run_id, round_num, code, counterpart_cc, proposer_cc, changes)

    # --- TECHNOLOGY (proposer shares) ---
    tech = offer.get("technology") or {}
    if tech.get("nuclear"):
        _transfer_tech(client, sim_run_id, round_num, counterpart_cc, "nuclear_rd_progress", NUCLEAR_TECH_BOOST, changes, f"{proposer_cc}→{counterpart_cc}")
    if tech.get("ai"):
        _transfer_tech(client, sim_run_id, round_num, counterpart_cc, "ai_rd_progress", AI_TECH_BOOST, changes, f"{proposer_cc}→{counterpart_cc}")

    # --- TECHNOLOGY (counterpart shares via request) ---
    req_tech = request.get("technology") or {}
    if req_tech.get("nuclear"):
        _transfer_tech(client, sim_run_id, round_num, proposer_cc, "nuclear_rd_progress", NUCLEAR_TECH_BOOST, changes, f"{counterpart_cc}→{proposer_cc}")
    if req_tech.get("ai"):
        _transfer_tech(client, sim_run_id, round_num, proposer_cc, "ai_rd_progress", AI_TECH_BOOST, changes, f"{counterpart_cc}→{proposer_cc}")

    # --- BASING RIGHTS (proposer grants) ---
    if offer.get("basing_rights"):
        _grant_basing(client, sim_run_id, proposer_cc, counterpart_cc, changes)

    # --- BASING RIGHTS (counterpart grants via request) ---
    if request.get("basing_rights"):
        _grant_basing(client, sim_run_id, counterpart_cc, proposer_cc, changes)

    return changes


def _transfer_coins(client, sim_run_id, round_num, from_cc, to_cc, amount, changes):
    """Move coins between country treasuries."""
    try:
        # Deduct from sender
        row = client.table("country_states_per_round").select("treasury") \
            .eq("sim_run_id", sim_run_id).eq("round_num", round_num) \
            .eq("country_code", from_cc).limit(1).execute().data
        if row:
            new_val = max(0, float(row[0]["treasury"] or 0) - amount)
            client.table("country_states_per_round").update({"treasury": round(new_val, 2)}) \
                .eq("sim_run_id", sim_run_id).eq("round_num", round_num) \
                .eq("country_code", from_cc).execute()

        # Add to receiver
        row = client.table("country_states_per_round").select("treasury") \
            .eq("sim_run_id", sim_run_id).eq("round_num", round_num) \
            .eq("country_code", to_cc).limit(1).execute().data
        if row:
            new_val = float(row[0]["treasury"] or 0) + amount
            client.table("country_states_per_round").update({"treasury": round(new_val, 2)}) \
                .eq("sim_run_id", sim_run_id).eq("round_num", round_num) \
                .eq("country_code", to_cc).execute()

        changes.append(f"{from_cc} → {to_cc}: {amount} coins")
    except Exception as e:
        logger.warning("coin transfer failed %s→%s: %s", from_cc, to_cc, e)


def _transfer_unit(client, sim_run_id, round_num, unit_code, from_cc, to_cc, changes):
    """Transfer a specific unit to new owner's reserve."""
    try:
        client.table("unit_states_per_round").update({
            "country_code": to_cc,
            "status": "reserve",
            "global_row": None,
            "global_col": None,
            "theater": None,
            "theater_row": None,
            "theater_col": None,
            "embarked_on": None,
        }).eq("sim_run_id", sim_run_id).eq("round_num", round_num) \
          .eq("unit_code", unit_code).execute()
        changes.append(f"{from_cc} → {to_cc}: unit {unit_code}")
    except Exception as e:
        logger.warning("unit transfer failed %s: %s", unit_code, e)


def _transfer_tech(client, sim_run_id, round_num, receiver_cc, field, boost, changes, label):
    """Boost receiver's R&D progress."""
    try:
        row = client.table("country_states_per_round").select(field) \
            .eq("sim_run_id", sim_run_id).eq("round_num", round_num) \
            .eq("country_code", receiver_cc).limit(1).execute().data
        if row:
            old = float(row[0].get(field) or 0)
            client.table("country_states_per_round").update({
                field: round(old + boost, 4),
            }).eq("sim_run_id", sim_run_id).eq("round_num", round_num) \
              .eq("country_code", receiver_cc).execute()
        changes.append(f"{label}: {field} +{boost}")
    except Exception as e:
        logger.warning("tech transfer failed %s: %s", receiver_cc, e)


def _grant_basing(client, sim_run_id, host_cc, guest_cc, changes):
    """Grant basing rights via the canonical basing_rights_engine."""
    from engine.services.basing_rights_engine import grant_basing_rights
    result = grant_basing_rights(
        sim_run_id=sim_run_id,
        host_country=host_cc,
        guest_country=guest_cc,
        round_num=0,  # round_num not tracked per transaction — use 0
        source="transaction",
    )
    if result.get("success"):
        changes.append(f"{host_cc} grants basing rights to {guest_cc}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_world_state(client, sim_run_id, round_num):
    """Load units + country_state for validation."""
    us = client.table("unit_states_per_round").select("*") \
        .eq("sim_run_id", sim_run_id).lte("round_num", round_num) \
        .order("round_num", desc=True).execute().data or []
    units = {}
    for r in us:
        c = r.get("unit_code")
        if c and c not in units:
            units[c] = r

    cs = client.table("country_states_per_round").select("*") \
        .eq("sim_run_id", sim_run_id).lte("round_num", round_num) \
        .order("round_num", desc=True).execute().data or []
    country_state = {}
    for r in cs:
        cc = r.get("country_code")
        if cc and cc not in country_state:
            country_state[cc] = r

    return units, country_state


def _load_roles(client):
    """Load role data for authorization checks."""
    try:
        res = client.table("roles").select("*").execute()
        return {r.get("id") or r.get("role_id", ""): r for r in (res.data or [])}
    except Exception:
        return {}


def _get_scenario_id(client, sim_run_id):
    try:
        r = client.table("sim_runs").select("scenario_id").eq("id", sim_run_id).limit(1).execute()
        return r.data[0]["scenario_id"] if r.data else None
    except Exception:
        return None


def _write_event(client, sim_run_id, scenario_id, round_num, event_type, country_code, summary, payload):
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


def _summarize_assets(assets: dict) -> str:
    parts = []
    if assets.get("coins"):
        parts.append(f"{assets['coins']} coins")
    if assets.get("units"):
        parts.append(f"{len(assets['units'])} units")
    if assets.get("technology"):
        techs = [k for k, v in assets["technology"].items() if v]
        if techs:
            parts.append(f"tech({','.join(techs)})")
    if assets.get("basing_rights"):
        parts.append("basing_rights")
    return " + ".join(parts) if parts else "(nothing)"
