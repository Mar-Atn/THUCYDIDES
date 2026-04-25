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

from engine.services.common import get_scenario_id, write_event

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
        roles = _load_roles(client, sim_run_id)

    # Validate proposer side
    report = validate_proposal(proposal, units, country_state, roles)
    if not report["valid"]:
        return {"transaction_id": None, "status": "rejected", "errors": report["errors"]}

    normalized = report["normalized"]

    # Look up scenario_id for denorm
    scenario_id = get_scenario_id(client, sim_run_id)

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
    write_event(client, sim_run_id, scenario_id, round_num,
                normalized["proposer_country_code"], "transaction_proposed",
                 f"{normalized['proposer_country_code']} proposes exchange to "
                 f"{normalized['counterpart_country_code']}: "
                 f"offer={_summarize_assets(normalized['offer'])}, "
                 f"request={_summarize_assets(normalized['request'])}",
                 {"transaction_id": txn_id, "offer": normalized["offer"],
                  "request": normalized["request"]},
                 category="diplomatic")

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
        return {"status": txn["status"], "errors": [f"Transaction is {txn['status']}, not respondable"]}

    round_num = txn["round_num"]
    scenario_id = txn.get("scenario_id")

    if response == "decline":
        client.table("exchange_transactions").update({
            "status": "declined",
        }).eq("id", transaction_id).execute()

        write_event(client, sim_run_id, scenario_id, round_num,
                    txn["counterpart"], "transaction_declined",
                     f"{txn['counterpart']} declined exchange from {txn['proposer']}",
                     {"transaction_id": transaction_id},
                     category="diplomatic")

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

        write_event(client, sim_run_id, scenario_id, round_num,
                    txn["counterpart"], "transaction_countered",
                     f"{txn['counterpart']} counter-offered to {txn['proposer']}",
                     {"transaction_id": transaction_id,
                      "counter_offer": counter_offer, "counter_request": counter_request},
                     category="diplomatic")

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

            write_event(client, sim_run_id, scenario_id, round_num,
                        txn["proposer"], "transaction_failed",
                         f"Exchange {txn['proposer']}↔{txn['counterpart']} failed validation: "
                         f"{exec_report['errors'][:2]}",
                         {"transaction_id": transaction_id, "errors": exec_report["errors"]},
                         category="diplomatic")

            return {"status": "failed_validation", "errors": exec_report["errors"]}

        # Lock: set status to 'executing' to prevent double-accept
        client.table("exchange_transactions").update({
            "status": "executing",
        }).eq("id", transaction_id).in_("status", ["pending", "countered"]).execute()

        # Re-verify we got the lock
        recheck = client.table("exchange_transactions").select("status").eq("id", transaction_id).execute()
        if recheck.data and recheck.data[0]["status"] != "executing":
            return {"status": recheck.data[0]["status"], "errors": ["Transaction already processed"]}

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

        write_event(client, sim_run_id, scenario_id, round_num,
                    txn["proposer"], "transaction_executed",
                     f"Exchange executed: {txn['proposer']}↔{txn['counterpart']} — {', '.join(changes[:3])}",
                     {"transaction_id": transaction_id, "changes": changes},
                     category="diplomatic")

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

    # --- UNITS (counterpart gives via request — type+count, system picks) ---
    req_units = request.get("units") or []
    for item in req_units:
        if isinstance(item, str):
            # Specific unit_id (legacy format)
            _transfer_unit(client, sim_run_id, round_num, item, counterpart_cc, proposer_cc, changes)
        elif isinstance(item, dict) and item.get("type") and item.get("count"):
            # Type + count — system auto-picks from reserve
            _transfer_unit_by_type(client, sim_run_id, round_num, item["type"], int(item["count"]), counterpart_cc, proposer_cc, changes)

    # --- TECHNOLOGY (proposer shares — sets recipient level) ---
    tech = offer.get("technology") or {}
    if tech.get("type") and tech.get("level"):
        _transfer_tech(client, sim_run_id, round_num, counterpart_cc, tech["type"], int(tech["level"]), changes, f"{proposer_cc}→{counterpart_cc}")

    # --- TECHNOLOGY (counterpart shares via request) ---
    req_tech = request.get("technology") or {}
    if req_tech.get("type") and req_tech.get("level"):
        _transfer_tech(client, sim_run_id, round_num, proposer_cc, req_tech["type"], int(req_tech["level"]), changes, f"{counterpart_cc}→{proposer_cc}")

    # --- BASING RIGHTS (proposer grants) ---
    if offer.get("basing_rights"):
        _grant_basing(client, sim_run_id, proposer_cc, counterpart_cc, changes)

    # --- BASING RIGHTS (counterpart grants via request) ---
    if request.get("basing_rights"):
        _grant_basing(client, sim_run_id, counterpart_cc, proposer_cc, changes)

    return changes


def _transfer_coins(client, sim_run_id, round_num, from_cc, to_cc, amount, changes):
    """Move coins between country treasuries (live countries table)."""
    try:
        # Deduct from sender
        row = client.table("countries").select("treasury") \
            .eq("sim_run_id", sim_run_id).eq("id", from_cc).execute().data
        if row:
            new_val = max(0, float(row[0]["treasury"] or 0) - amount)
            client.table("countries").update({"treasury": round(new_val, 2)}) \
                .eq("sim_run_id", sim_run_id).eq("id", from_cc).execute()

        # Add to receiver
        row = client.table("countries").select("treasury") \
            .eq("sim_run_id", sim_run_id).eq("id", to_cc).execute().data
        if row:
            new_val = float(row[0]["treasury"] or 0) + amount
            client.table("countries").update({"treasury": round(new_val, 2)}) \
                .eq("sim_run_id", sim_run_id).eq("id", to_cc).execute()

        changes.append(f"{from_cc} → {to_cc}: {amount} coins")
    except Exception as e:
        logger.warning("coin transfer failed %s→%s: %s", from_cc, to_cc, e)


def _transfer_unit(client, sim_run_id, round_num, unit_code, from_cc, to_cc, changes):
    """Transfer a specific unit to new owner's reserve (live deployments table)."""
    try:
        client.table("deployments").update({
            "country_code": to_cc,
            "unit_status": "reserve",
            "global_row": None,
            "global_col": None,
            "theater": None,
            "theater_row": None,
            "theater_col": None,
            "embarked_on": None,
        }).eq("sim_run_id", sim_run_id).eq("unit_id", unit_code).execute()
        changes.append(f"{from_cc} → {to_cc}: unit {unit_code}")
    except Exception as e:
        logger.warning("unit transfer failed %s: %s", unit_code, e)


def _transfer_unit_by_type(client, sim_run_id, round_num, unit_type, count, from_cc, to_cc, changes):
    """Transfer N reserve units of a type from one country to another."""
    try:
        # Find reserve units of the requested type
        available = client.table("deployments").select("id, unit_id") \
            .eq("sim_run_id", sim_run_id).eq("country_code", from_cc) \
            .eq("unit_type", unit_type).eq("unit_status", "reserve") \
            .limit(count).execute().data or []

        transferred = 0
        for u in available[:count]:
            client.table("deployments").update({
                "country_code": to_cc,
                "unit_status": "reserve",
            }).eq("id", u["id"]).execute()
            transferred += 1

        if transferred > 0:
            changes.append(f"{from_cc} → {to_cc}: {transferred} {unit_type} units")
    except Exception as e:
        logger.warning("unit type transfer failed %s %s: %s", unit_type, from_cc, e)


def _transfer_tech(client, sim_run_id, round_num, receiver_cc, tech_type, level, changes, label):
    """Set receiver's technology to specified level (live countries table).

    Per CONTRACT_TRANSACTION v2: tech transfer SETS the level.
    Nuclear: sets nuclear_level but nuclear_confirmed = false (needs test).
    AI: sets ai_level directly.
    """
    try:
        if tech_type == "nuclear":
            client.table("countries").update({
                "nuclear_level": level,
                "nuclear_rd_progress": 0.0,  # Reset — new level, research starts fresh
                "nuclear_confirmed": False,  # Recipient must test to confirm
            }).eq("sim_run_id", sim_run_id).eq("id", receiver_cc).execute()
            changes.append(f"{label}: nuclear → L{level} (unconfirmed, R&D reset)")
        elif tech_type == "ai":
            client.table("countries").update({
                "ai_level": level,
                "ai_rd_progress": 0.0,  # Reset — new level, research starts fresh
            }).eq("sim_run_id", sim_run_id).eq("id", receiver_cc).execute()
            changes.append(f"{label}: AI → L{level} (R&D reset)")
    except Exception as e:
        logger.warning("tech transfer failed %s: %s", receiver_cc, e)


def _grant_basing(client, sim_run_id, host_cc, guest_cc, changes):
    """Grant basing rights by updating relationships table directly."""
    try:
        # Update relationship: host grants basing to guest
        client.table("relationships").update({
            "basing_rights_a_to_b": True,
        }).eq("sim_run_id", sim_run_id) \
          .eq("from_country_code", host_cc).eq("to_country_code", guest_cc).execute()
        changes.append(f"{host_cc} grants basing rights to {guest_cc}")
    except Exception as e:
        logger.warning("basing rights grant failed %s→%s: %s", host_cc, guest_cc, e)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_world_state(client, sim_run_id, round_num):
    """Load units + country_state for validation.

    Uses live `countries` table (not per-round snapshots) to get current
    treasury, tech levels, etc. Uses `deployments` for unit data.
    """
    # Units from deployments (individual unit model)
    deps = client.table("deployments").select("unit_id, country_code, unit_type, unit_status") \
        .eq("sim_run_id", sim_run_id).execute().data or []
    units = {}
    for d in deps:
        uid = d.get("unit_id") or d.get("id")
        if uid:
            units[uid] = {
                "unit_code": uid,
                "country_code": d["country_code"],
                "unit_type": d["unit_type"],
                "status": d.get("unit_status", "active"),
            }

    # Country state from live countries table
    cs_rows = client.table("countries").select("id, treasury, nuclear_level, nuclear_confirmed, ai_level") \
        .eq("sim_run_id", sim_run_id).execute().data or []
    country_state = {}
    for r in cs_rows:
        country_state[r["id"]] = {
            "country_code": r["id"],
            "treasury": r.get("treasury", 0),
            "nuclear_level": r.get("nuclear_level", 0),
            "nuclear_confirmed": r.get("nuclear_confirmed", False),
            "ai_level": r.get("ai_level", 0),
        }

    return units, country_state


def _load_roles(client, sim_run_id: str | None = None):
    """Load role data for authorization checks."""
    try:
        q = client.table("roles").select("*")
        if sim_run_id:
            q = q.eq("sim_run_id", sim_run_id)
        res = q.execute()
        return {r.get("id") or r.get("role_id", ""): r for r in (res.data or [])}
    except Exception:
        return {}




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
