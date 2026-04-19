"""Domestic action validators — fire/reassign, arrest, martial law.

Group B actions from CARD_ACTIONS §6 + §1.2. All are immediate-effect
actions that modify role state or unit counts.
"""

from __future__ import annotations

from engine.config.position_actions import has_position

CANONICAL_COUNTRIES: frozenset[str] = frozenset({
    "albion", "bharata", "caribe", "cathay", "choson", "columbia",
    "formosa", "freeland", "gallia", "hanguk", "levantia", "mirage",
    "persia", "phrygia", "ponte", "ruthenia", "sarmatia", "solaria",
    "teutonia", "yamato",
})

RATIONALE_MIN = 30


# ---------------------------------------------------------------------------
# 6.3 Fire / Reassign
# ---------------------------------------------------------------------------

def validate_fire_role(
    payload: dict,
    roles: dict[str, dict],
) -> dict:
    """Validate a fire_role action. HoS fires a direct report."""
    errors: list[str] = []

    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["INVALID_PAYLOAD"], "warnings": [], "normalized": None}

    if payload.get("action_type") != "fire_role":
        errors.append("INVALID_ACTION_TYPE: expected 'fire_role'")

    rationale = payload.get("rationale")
    if not isinstance(rationale, str) or len(rationale.strip()) < RATIONALE_MIN:
        errors.append("RATIONALE_TOO_SHORT")

    firer_role = payload.get("role_id")
    target_role = (payload.get("changes") or {}).get("target_role")

    if not firer_role:
        errors.append("MISSING_ROLE: role_id required")
    if not target_role:
        errors.append("MISSING_TARGET: changes.target_role required")

    # Firer must have authority over target (simplified: must be HoS)
    firer_info = roles.get(firer_role) or {}
    if not has_position(firer_info, "head_of_state"):
        errors.append(f"UNAUTHORIZED: {firer_role!r} is not HoS — cannot fire roles")

    # Target must exist and be same country
    target_info = roles.get(target_role) or {}
    if not target_info:
        errors.append(f"UNKNOWN_TARGET: {target_role!r} not found")
    elif firer_info.get("country_id") != target_info.get("country_id"):
        errors.append(f"WRONG_COUNTRY: {target_role!r} belongs to {target_info.get('country_id')!r}")

    # Cannot fire yourself
    if firer_role == target_role:
        errors.append("SELF_FIRE: cannot fire yourself")

    if errors:
        return {"valid": False, "errors": errors, "warnings": [], "normalized": None}

    return {"valid": True, "errors": [], "warnings": [], "normalized": {
        "action_type": "fire_role",
        "role_id": firer_role,
        "country_code": firer_info.get("country_id"),
        "round_num": payload.get("round_num"),
        "rationale": rationale.strip(),
        "changes": {"target_role": target_role},
    }}


# ---------------------------------------------------------------------------
# 6.1 Arrest
# ---------------------------------------------------------------------------

def validate_arrest(
    payload: dict,
    roles: dict[str, dict],
) -> dict:
    """Validate an arrest action. HoS arrests a role (removes from play)."""
    errors: list[str] = []

    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["INVALID_PAYLOAD"], "warnings": [], "normalized": None}

    if payload.get("action_type") != "arrest":
        errors.append("INVALID_ACTION_TYPE: expected 'arrest'")

    rationale = payload.get("rationale")
    if not isinstance(rationale, str) or len(rationale.strip()) < RATIONALE_MIN:
        errors.append("RATIONALE_TOO_SHORT")

    arrester_role = payload.get("role_id")
    target_role = (payload.get("changes") or {}).get("target_role")

    if not arrester_role:
        errors.append("MISSING_ROLE")
    if not target_role:
        errors.append("MISSING_TARGET")

    arrester_info = roles.get(arrester_role) or {}
    if not has_position(arrester_info, "head_of_state"):
        errors.append(f"UNAUTHORIZED: {arrester_role!r} not HoS")

    target_info = roles.get(target_role) or {}
    if not target_info:
        errors.append(f"UNKNOWN_TARGET: {target_role!r}")
    elif arrester_info.get("country_id") != target_info.get("country_id"):
        errors.append(f"WRONG_COUNTRY: {target_role!r}")

    if arrester_role == target_role:
        errors.append("SELF_ARREST: cannot arrest yourself")

    if errors:
        return {"valid": False, "errors": errors, "warnings": [], "normalized": None}

    return {"valid": True, "errors": [], "warnings": [], "normalized": {
        "action_type": "arrest",
        "role_id": arrester_role,
        "country_code": arrester_info.get("country_id"),
        "round_num": payload.get("round_num"),
        "rationale": rationale.strip(),
        "changes": {"target_role": target_role},
    }}


# ---------------------------------------------------------------------------
# 1.2 Martial Law (Conscription)
# ---------------------------------------------------------------------------

MARTIAL_LAW_POOLS: dict[str, int] = {
    "sarmatia": 10, "ruthenia": 6, "persia": 8, "cathay": 10,
}


def validate_martial_law(
    payload: dict,
    country_state: dict[str, dict],
) -> dict:
    """Validate a martial_law declaration. Spawns reserve units from population."""
    errors: list[str] = []

    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["INVALID_PAYLOAD"], "warnings": [], "normalized": None}

    if payload.get("action_type") != "martial_law":
        errors.append("INVALID_ACTION_TYPE: expected 'martial_law'")

    decision = payload.get("decision")
    if decision not in ("change", "no_change"):
        errors.append(f"INVALID_DECISION: {decision!r}")

    rationale = payload.get("rationale")
    if not isinstance(rationale, str) or len(rationale.strip()) < RATIONALE_MIN:
        errors.append("RATIONALE_TOO_SHORT")

    cc = payload.get("country_code")
    if not cc or cc not in CANONICAL_COUNTRIES:
        errors.append(f"INVALID_COUNTRY: {cc!r}")

    if decision == "no_change":
        if errors:
            return {"valid": False, "errors": errors, "warnings": [], "normalized": None}
        return {"valid": True, "errors": [], "warnings": [], "normalized": {
            "action_type": "martial_law", "country_code": cc,
            "round_num": payload.get("round_num"), "decision": "no_change",
            "rationale": rationale.strip(),
        }}

    # Check country is eligible for martial law
    if cc and cc not in MARTIAL_LAW_POOLS:
        errors.append(f"NOT_ELIGIBLE: {cc!r} has no martial law conscription pool")

    # Check not already declared this run (one-time per country per SIM)
    cs = country_state.get(cc) or {}
    if cs.get("martial_law_declared"):
        errors.append(f"ALREADY_DECLARED: {cc} has already declared martial law this SIM")

    if errors:
        return {"valid": False, "errors": errors, "warnings": [], "normalized": None}

    return {"valid": True, "errors": [], "warnings": [], "normalized": {
        "action_type": "martial_law", "country_code": cc,
        "round_num": payload.get("round_num"), "decision": "change",
        "rationale": rationale.strip(),
        "changes": {"conscription_pool": MARTIAL_LAW_POOLS.get(cc, 0)},
    }}
