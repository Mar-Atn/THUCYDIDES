"""Political action validators — assassination, coup, mass protest, elections.

Group C/D from CARD_ACTIONS §6.2, §6.4, §6.5, §6.6, §6.7.
"""

from __future__ import annotations

CANONICAL_COUNTRIES: frozenset[str] = frozenset({
    "albion", "bharata", "caribe", "cathay", "choson", "columbia",
    "formosa", "freeland", "gallia", "hanguk", "levantia", "mirage",
    "persia", "phrygia", "ponte", "ruthenia", "sarmatia", "solaria",
    "teutonia", "yamato",
})

RATIONALE_MIN = 30


# ---------------------------------------------------------------------------
# 6.2 Assassination
# ---------------------------------------------------------------------------

def validate_assassination(
    payload: dict,
    roles: dict[str, dict] | None = None,
) -> dict:
    """Validate assassination action. Card-based (consumable)."""
    errors: list[str] = []

    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["INVALID_PAYLOAD"], "warnings": [], "normalized": None}

    if payload.get("action_type") != "assassination":
        errors.append("INVALID_ACTION_TYPE")

    rationale = payload.get("rationale")
    if not isinstance(rationale, str) or len(rationale.strip()) < RATIONALE_MIN:
        errors.append("RATIONALE_TOO_SHORT")

    role_id = payload.get("role_id")
    target_role = payload.get("target_role")
    domestic = payload.get("domestic", False)

    if not target_role:
        errors.append("MISSING_TARGET: target_role required")

    # Card check
    if roles and role_id:
        role_info = roles.get(role_id) or {}
        cards = int(role_info.get("assassination_cards", 0) or 0)
        if cards <= 0:
            errors.append(f"NO_CARDS: {role_id!r} has 0 assassination cards")

    if role_id == target_role:
        errors.append("SELF_ASSASSINATION: cannot target yourself")

    if errors:
        return {"valid": False, "errors": errors, "warnings": [], "normalized": None}

    return {"valid": True, "errors": [], "warnings": [], "normalized": {
        "action_type": "assassination",
        "role_id": role_id,
        "country_code": payload.get("country_code"),
        "round_num": payload.get("round_num"),
        "rationale": rationale.strip(),
        "target_role": target_role,
        "domestic": bool(domestic),
    }}


# ---------------------------------------------------------------------------
# 6.4 Coup Attempt
# ---------------------------------------------------------------------------

def validate_coup(
    payload: dict,
    roles: dict[str, dict] | None = None,
    country_state: dict[str, dict] | None = None,
) -> dict:
    """Validate a coup attempt. Military chief or opposition with conditions."""
    errors: list[str] = []

    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["INVALID_PAYLOAD"], "warnings": [], "normalized": None}

    if payload.get("action_type") != "coup_attempt":
        errors.append("INVALID_ACTION_TYPE")

    rationale = payload.get("rationale")
    if not isinstance(rationale, str) or len(rationale.strip()) < RATIONALE_MIN:
        errors.append("RATIONALE_TOO_SHORT")

    role_id = payload.get("role_id")
    cc = payload.get("country_code")

    # Role check: must be military chief or opposition with coup_potential
    if roles and role_id:
        role_info = roles.get(role_id) or {}
        is_mil = role_info.get("is_military_chief")
        powers = str(role_info.get("powers") or "")
        if not is_mil and "coup" not in powers.lower():
            errors.append(f"UNAUTHORIZED: {role_id!r} lacks coup capability")

    if errors:
        return {"valid": False, "errors": errors, "warnings": [], "normalized": None}

    return {"valid": True, "errors": [], "warnings": [], "normalized": {
        "action_type": "coup_attempt",
        "role_id": role_id,
        "country_code": cc,
        "round_num": payload.get("round_num"),
        "rationale": rationale.strip(),
    }}


# ---------------------------------------------------------------------------
# 6.5 Mass Protest
# ---------------------------------------------------------------------------

def validate_mass_protest(
    payload: dict,
    roles: dict[str, dict] | None = None,
) -> dict:
    """Validate a mass protest action. Opposition/tycoon triggers."""
    errors: list[str] = []

    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["INVALID_PAYLOAD"], "warnings": [], "normalized": None}

    if payload.get("action_type") != "mass_protest":
        errors.append("INVALID_ACTION_TYPE")

    rationale = payload.get("rationale")
    if not isinstance(rationale, str) or len(rationale.strip()) < RATIONALE_MIN:
        errors.append("RATIONALE_TOO_SHORT")

    role_id = payload.get("role_id")

    # Card check: protest_stim_cards
    if roles and role_id:
        role_info = roles.get(role_id) or {}
        cards = int(role_info.get("protest_stim_cards", 0) or 0)
        if cards <= 0:
            errors.append(f"NO_CARDS: {role_id!r} has 0 protest_stim_cards")

    if errors:
        return {"valid": False, "errors": errors, "warnings": [], "normalized": None}

    return {"valid": True, "errors": [], "warnings": [], "normalized": {
        "action_type": "mass_protest",
        "role_id": role_id,
        "country_code": payload.get("country_code"),
        "round_num": payload.get("round_num"),
        "rationale": rationale.strip(),
    }}


# ---------------------------------------------------------------------------
# 6.7 Call Early Elections
# ---------------------------------------------------------------------------

def validate_early_elections(
    payload: dict,
    roles: dict[str, dict] | None = None,
) -> dict:
    """Validate early elections call. HoS only."""
    errors: list[str] = []

    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["INVALID_PAYLOAD"], "warnings": [], "normalized": None}

    if payload.get("action_type") != "call_early_elections":
        errors.append("INVALID_ACTION_TYPE")

    rationale = payload.get("rationale")
    if not isinstance(rationale, str) or len(rationale.strip()) < RATIONALE_MIN:
        errors.append("RATIONALE_TOO_SHORT")

    role_id = payload.get("role_id")
    if roles and role_id:
        role_info = roles.get(role_id) or {}
        if not role_info.get("is_head_of_state"):
            errors.append(f"UNAUTHORIZED: {role_id!r} is not HoS — only HoS can call elections")

    if errors:
        return {"valid": False, "errors": errors, "warnings": [], "normalized": None}

    return {"valid": True, "errors": [], "warnings": [], "normalized": {
        "action_type": "call_early_elections",
        "role_id": role_id,
        "country_code": payload.get("country_code"),
        "round_num": payload.get("round_num"),
        "rationale": rationale.strip(),
    }}
