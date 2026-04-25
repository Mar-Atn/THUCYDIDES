"""Agreement Engine — CONTRACT_AGREEMENTS v1.0.

Pure service for written commitments. Actor-agnostic.

Lifecycle:
    propose_agreement(proposal, sim_run_id) → {id, status}
    sign_agreement(agreement_id, country_code, role_id, confirm, comments) → {status}
    get_pending_agreements(country_code, sim_run_id) → list
    get_active_agreements(country_code, sim_run_id) → list

No enforcement — all agreements are just saved.
"""

from __future__ import annotations

from engine.services.common import get_scenario_id, write_event

import logging
from datetime import datetime, timezone

from engine.services.supabase import get_client
from engine.services.agreement_validator import validate_agreement_proposal

logger = logging.getLogger(__name__)


def propose_agreement(
    proposal: dict,
    sim_run_id: str,
    roles: dict[str, dict] | None = None,
) -> dict:
    """Validate and create a PROPOSED agreement.

    Returns ``{agreement_id, status, errors}``.
    """
    client = get_client()

    if roles is None:
        roles = _load_roles(client, sim_run_id)

    report = validate_agreement_proposal(proposal, roles)
    if not report["valid"]:
        return {"agreement_id": None, "status": "rejected", "errors": report["errors"]}

    norm = report["normalized"]
    scenario_id = get_scenario_id(client, sim_run_id)

    # Proposer auto-signs
    signatures = {
        norm["proposer_country_code"]: {
            "confirmed": True,
            "role_id": norm["proposer_role_id"],
            "comments": norm.get("rationale", ""),
            "signed_at": datetime.now(timezone.utc).isoformat(),
        }
    }

    row = {
        "sim_run_id": sim_run_id,
        "scenario_id": scenario_id,
        "round_num": norm["round_num"],
        "agreement_name": norm["agreement_name"],
        "agreement_type": norm["agreement_type"],
        "visibility": norm["visibility"],
        "terms": norm["terms"],
        "signatories": norm["signatories"],
        "proposer_country_code": norm["proposer_country_code"],
        "proposer_role_id": norm["proposer_role_id"],
        "signatures": signatures,
        "status": "proposed",
    }

    res = client.table("agreements").insert(row).execute()
    agreement_id = res.data[0]["id"]

    # Check if only 2 signatories and proposer already signed → need 1 more
    # If proposer is the only signatory needed... (shouldn't happen, min 2)

    write_event(client, sim_run_id, scenario_id, norm["round_num"],
                norm["proposer_country_code"], "agreement_proposed",
                 f"{norm['proposer_country_code']} proposes {norm['agreement_type']}: "
                 f"'{norm['agreement_name']}' with {', '.join(norm['signatories'])}",
                 {"agreement_id": agreement_id, "type": norm["agreement_type"],
                  "visibility": norm["visibility"]})

    logger.info("[agreement] proposed %s: '%s' by %s",
                agreement_id, norm["agreement_name"], norm["proposer_country_code"])

    return {"agreement_id": agreement_id, "status": "proposed", "errors": []}


def sign_agreement(
    agreement_id: str,
    country_code: str,
    role_id: str,
    confirm: bool,
    comments: str = "",
) -> dict:
    """Sign or decline an agreement.

    Returns ``{status, activated?}``.
    """
    client = get_client()

    res = client.table("agreements").select("*").eq("id", agreement_id).limit(1).execute()
    if not res.data:
        return {"status": "error", "errors": ["Agreement not found"]}
    agr = res.data[0]

    if agr["status"] != "proposed":
        return {"status": agr["status"], "errors": ["Agreement not in proposed state"]}

    if country_code not in (agr["signatories"] or []):
        return {"status": "error", "errors": [f"{country_code} is not a signatory"]}

    signatures = agr.get("signatures") or {}
    sim_run_id = agr["sim_run_id"]
    scenario_id = agr.get("scenario_id")

    signatures[country_code] = {
        "confirmed": confirm,
        "role_id": role_id,
        "comments": comments,
        "signed_at": datetime.now(timezone.utc).isoformat(),
    }

    if not confirm:
        client.table("agreements").update({
            "signatures": signatures,
            "status": "declined",
        }).eq("id", agreement_id).execute()

        write_event(client, sim_run_id, scenario_id, agr["round_num"],
                    country_code, "agreement_declined",
                     f"{country_code} declined '{agr['agreement_name']}'",
                     {"agreement_id": agreement_id, "comments": comments})

        return {"status": "declined", "declined_by": country_code}

    # Confirm — check if all signatories have now signed
    client.table("agreements").update({
        "signatures": signatures,
    }).eq("id", agreement_id).execute()

    all_signed = all(
        signatures.get(s, {}).get("confirmed") is True
        for s in (agr["signatories"] or [])
    )

    if all_signed:
        client.table("agreements").update({
            "status": "active",
        }).eq("id", agreement_id).execute()

        # Auto-update bilateral relationships based on agreement type
        _update_relationships_for_agreement(client, sim_run_id, agr["agreement_type"], agr["signatories"] or [])

        write_event(client, sim_run_id, scenario_id, agr["round_num"],
                    agr.get("proposer_country_code", ""), "agreement_activated",
                     f"Agreement ACTIVE: '{agr['agreement_name']}' ({agr['agreement_type']}) — "
                     f"signed by {', '.join(agr['signatories'] or [])}",
                     {"agreement_id": agreement_id, "type": agr["agreement_type"],
                      "visibility": agr["visibility"]})

        logger.info("[agreement] ACTIVATED %s: '%s'", agreement_id, agr["agreement_name"])
        return {"status": "active", "activated": True}

    write_event(client, sim_run_id, scenario_id, agr["round_num"],
                country_code, "agreement_signed",
                 f"{country_code} signed '{agr['agreement_name']}'",
                 {"agreement_id": agreement_id})

    return {"status": "proposed", "signed_by": country_code, "activated": False}


def get_pending_agreements(country_code: str, sim_run_id: str) -> list[dict]:
    """Return proposed agreements awaiting this country's signature."""
    client = get_client()
    res = client.table("agreements").select("*") \
        .eq("sim_run_id", sim_run_id) \
        .eq("status", "proposed") \
        .contains("signatories", [country_code]) \
        .order("created_at", desc=True) \
        .execute()
    # Filter to those where this country hasn't signed yet
    out = []
    for a in (res.data or []):
        sigs = a.get("signatures") or {}
        if country_code not in sigs:
            out.append(a)
    return out


def get_active_agreements(country_code: str, sim_run_id: str) -> list[dict]:
    """Return all active agreements involving this country."""
    client = get_client()
    res = client.table("agreements").select("*") \
        .eq("sim_run_id", sim_run_id) \
        .eq("status", "active") \
        .contains("signatories", [country_code]) \
        .order("created_at", desc=True) \
        .execute()
    return res.data or []


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_roles(client, sim_run_id: str | None = None):
    try:
        q = client.table("roles").select("*")
        if sim_run_id:
            q = q.eq("sim_run_id", sim_run_id)
        res = q.execute()
        return {r.get("id") or r.get("role_id", ""): r for r in (res.data or [])}
    except Exception:
        return {}




# Agreement type → relationship status mapping (SIMPLIFICATION_CHANGE_PLAN §C)
AGREEMENT_TO_RELATION: dict[str, str] = {
    "military_alliance": "alliance",
    "trade_agreement": "economic_partnership",
    "peace_treaty": "neutral",
    "ceasefire": "hostile",
}

# Relationship priority (higher = stronger, dominates lower)
RELATION_PRIORITY: dict[str, int] = {
    "alliance": 5,
    "economic_partnership": 4,
    "neutral": 3,
    "hostile": 2,
    "at_war": 1,
}


def _update_relationships_for_agreement(client, sim_run_id: str, agreement_type: str, signatories: list[str]):
    """Auto-update bilateral relationships when agreement is activated.

    Rules (SIMPLIFICATION_CHANGE_PLAN §C):
    - Military Alliance → alliance (highest priority)
    - Trade Agreement → economic_partnership (unless alliance exists)
    - Peace Treaty → neutral (from war/hostile)
    - Ceasefire → hostile (from war)
    - Higher priority agreement dominates
    """
    new_relation = AGREEMENT_TO_RELATION.get(agreement_type)
    if not new_relation:
        return

    new_priority = RELATION_PRIORITY.get(new_relation, 0)

    # Update all bilateral pairs among signatories
    for i, a in enumerate(signatories):
        for b in signatories[i+1:]:
            try:
                # Check current relationship
                rel = client.table("relationships").select("relationship") \
                    .eq("sim_run_id", sim_run_id) \
                    .eq("from_country_code", a).eq("to_country_code", b).execute()

                current = rel.data[0]["relationship"] if rel.data else "neutral"
                current_priority = RELATION_PRIORITY.get(current, 0)

                # Only upgrade (higher priority agreement dominates)
                if new_priority >= current_priority:
                    client.table("relationships").update({"relationship": new_relation}) \
                        .eq("sim_run_id", sim_run_id) \
                        .eq("from_country_code", a).eq("to_country_code", b).execute()
                    # Also update reverse direction
                    client.table("relationships").update({"relationship": new_relation}) \
                        .eq("sim_run_id", sim_run_id) \
                        .eq("from_country_code", b).eq("to_country_code", a).execute()

                    logger.info("[agreement] Relationship %s↔%s → %s (was %s)", a, b, new_relation, current)
            except Exception as e:
                logger.warning("Failed to update relationship %s↔%s: %s", a, b, e)


