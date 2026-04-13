"""Basing rights action validator — unilateral grant/revoke.

Separate from the transaction flow (where basing can be part of a deal).
This is a standalone HoS action: "I allow/disallow country X on my soil."

Grant: immediate, no confirmation from guest needed.
Revoke: immediate, BUT guest must have NO active units on host territory.
"""

from __future__ import annotations

CANONICAL_COUNTRIES: frozenset[str] = frozenset({
    "albion", "bharata", "caribe", "cathay", "choson", "columbia",
    "formosa", "freeland", "gallia", "hanguk", "levantia", "mirage",
    "persia", "phrygia", "ponte", "ruthenia", "sarmatia", "solaria",
    "teutonia", "yamato",
})

VALID_ACTIONS = frozenset({"grant", "revoke"})
RATIONALE_MIN = 30


def validate_basing_rights(
    payload: dict,
    units: dict[str, dict],
    zones: dict[tuple[int, int], dict],
) -> dict:
    """Validate a basing_rights grant/revoke action."""
    errors: list[str] = []

    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["INVALID_PAYLOAD"], "warnings": [], "normalized": None}

    if payload.get("action_type") != "basing_rights":
        errors.append("INVALID_ACTION_TYPE: expected 'basing_rights'")

    decision = payload.get("decision")
    if decision not in ("change", "no_change"):
        errors.append(f"INVALID_DECISION: {decision!r}")

    rationale = payload.get("rationale")
    if not isinstance(rationale, str) or len(rationale.strip()) < RATIONALE_MIN:
        errors.append("RATIONALE_TOO_SHORT")

    host_cc = payload.get("country_code")
    if not host_cc or host_cc not in CANONICAL_COUNTRIES:
        errors.append(f"INVALID_HOST: {host_cc!r}")

    changes = payload.get("changes")

    if decision == "no_change":
        if changes is not None:
            errors.append("UNEXPECTED_CHANGES")
        if errors:
            return {"valid": False, "errors": errors, "warnings": [], "normalized": None}
        return {"valid": True, "errors": [], "warnings": [], "normalized": {
            "action_type": "basing_rights", "country_code": host_cc,
            "round_num": payload.get("round_num"), "decision": "no_change",
            "rationale": rationale.strip(),
        }}

    if not changes or not isinstance(changes, dict):
        errors.append("MISSING_CHANGES")
        return {"valid": False, "errors": errors, "warnings": [], "normalized": None}

    guest_cc = changes.get("counterpart_country")
    action = changes.get("action")

    if not guest_cc or guest_cc not in CANONICAL_COUNTRIES:
        errors.append(f"INVALID_GUEST: {guest_cc!r}")
    if guest_cc == host_cc:
        errors.append("SELF_BASING: cannot grant/revoke basing rights to yourself")
    if action not in VALID_ACTIONS:
        errors.append(f"INVALID_ACTION: {action!r} not in {sorted(VALID_ACTIONS)}")

    # On REVOKE: check guest has NO active units on host territory
    if action == "revoke" and host_cc and guest_cc and not errors:
        # Find host-owned hexes
        host_hexes = {(r, c) for (r, c), z in zones.items() if z.get("owner") == host_cc}
        # Check if guest has any active units on those hexes
        guest_on_host = [
            u["unit_code"] for u in units.values()
            if u.get("country_code") == guest_cc
            and (u.get("status") or "").lower() == "active"
            and u.get("global_row") is not None
            and (u["global_row"], u.get("global_col")) in host_hexes
        ]
        if guest_on_host:
            errors.append(
                f"GUEST_FORCES_PRESENT: cannot revoke — {guest_cc} has "
                f"{len(guest_on_host)} active units on your territory "
                f"(e.g. {guest_on_host[:3]}). They must withdraw first."
            )

    if errors:
        return {"valid": False, "errors": errors, "warnings": [], "normalized": None}

    return {"valid": True, "errors": [], "warnings": [], "normalized": {
        "action_type": "basing_rights", "country_code": host_cc,
        "round_num": payload.get("round_num"), "decision": "change",
        "rationale": rationale.strip(),
        "changes": {
            "counterpart_country": guest_cc,
            "action": action,
        },
    }}
