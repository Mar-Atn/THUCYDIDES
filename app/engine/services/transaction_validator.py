"""Transaction proposal validator — CONTRACT_TRANSACTIONS v1.0.

Validates the PROPOSER side of an exchange transaction at proposal time.
Does NOT validate the counterpart's assets (that happens at execution).

Used by:
- transaction_engine.propose_exchange()
- Test fixtures
- Human UI (future)
"""

from __future__ import annotations

from typing import Any

CANONICAL_COUNTRIES: frozenset[str] = frozenset({
    "albion", "bharata", "caribe", "cathay", "choson", "columbia",
    "formosa", "freeland", "gallia", "hanguk", "levantia", "mirage",
    "persia", "phrygia", "ponte", "ruthenia", "sarmatia", "solaria",
    "teutonia", "yamato",
})

VALID_SCOPES = frozenset({"country", "personal"})

ALLOWED_TOP = frozenset({
    "action_type", "proposer_role_id", "proposer_country_code", "scope",
    "counterpart_role_id", "counterpart_country_code", "round_num",
    "offer", "request", "rationale",
})

ALLOWED_ASSET_KEYS = frozenset({"coins", "units", "technology", "basing_rights"})


def validate_proposal(
    payload: dict,
    units: dict[str, dict],
    country_state: dict[str, dict],
    roles: dict[str, dict] | None = None,
) -> dict:
    """Validate a propose_transaction payload.

    Only validates the PROPOSER side:
    - Role authorization for the asset types offered
    - Asset availability (coins, units)
    - Structural correctness

    Returns ``{valid, errors, warnings, normalized}``.
    """
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["INVALID_PAYLOAD"], "warnings": [], "normalized": None}

    # Structural
    scope = payload.get("scope")
    if scope not in VALID_SCOPES:
        errors.append(f"INVALID_SCOPE: {scope!r} not in {sorted(VALID_SCOPES)}")

    proposer_cc = payload.get("proposer_country_code")
    counterpart_cc = payload.get("counterpart_country_code")
    proposer_role = payload.get("proposer_role_id")
    counterpart_role = payload.get("counterpart_role_id")

    if not proposer_cc or proposer_cc not in CANONICAL_COUNTRIES:
        errors.append(f"INVALID_PROPOSER: country {proposer_cc!r}")
    if not counterpart_cc or counterpart_cc not in CANONICAL_COUNTRIES:
        errors.append(f"INVALID_COUNTERPART: country {counterpart_cc!r}")
    if proposer_cc and counterpart_cc and proposer_cc == counterpart_cc and scope == "country":
        # Same country can trade personal coins between individuals
        if proposer_role == counterpart_role:
            errors.append("SELF_TRADE: cannot trade with yourself")

    offer = payload.get("offer") or {}
    request = payload.get("request") or {}

    if not isinstance(offer, dict) or not isinstance(request, dict):
        errors.append("INVALID_OFFER_REQUEST: offer and request must be dicts")
        return {"valid": False, "errors": errors, "warnings": warnings, "normalized": None}

    # Check offer + request have valid keys
    for label, d in (("offer", offer), ("request", request)):
        extra = set(d.keys()) - ALLOWED_ASSET_KEYS
        if extra:
            errors.append(f"UNKNOWN_ASSET_KEY: {label} has {sorted(extra)}")

    # Empty trade check
    offer_has = any(bool(offer.get(k)) for k in ALLOWED_ASSET_KEYS)
    request_has = any(bool(request.get(k)) for k in ALLOWED_ASSET_KEYS)
    if not offer_has and not request_has:
        errors.append("EMPTY_TRADE: both offer and request are empty")

    # Personal scope limits
    if scope == "personal":
        for label, d in (("offer", offer), ("request", request)):
            if d.get("units"):
                errors.append(f"PERSONAL_SCOPE_LIMIT: {label} cannot include units in personal scope")
            if d.get("technology"):
                errors.append(f"PERSONAL_SCOPE_LIMIT: {label} cannot include technology in personal scope")
            if d.get("basing_rights"):
                errors.append(f"PERSONAL_SCOPE_LIMIT: {label} cannot include basing_rights in personal scope")

    # Role authorization (country scope)
    if scope == "country" and proposer_role and not errors:
        from engine.config.position_actions import has_position
        role_info = (roles or {}).get(proposer_role) or {}
        is_hos = has_position(role_info, "head_of_state")
        is_mil = has_position(role_info, "military")
        powers = role_info.get("powers") or ""

        if not is_hos:
            # Non-HoS: check specific permissions
            if offer.get("units") and not is_mil:
                errors.append(f"UNAUTHORIZED_ROLE: {proposer_role!r} cannot trade military units (need HoS or military chief)")
            if offer.get("technology") and not is_hos:
                errors.append(f"UNAUTHORIZED_ROLE: {proposer_role!r} cannot share technology (need HoS)")

    # Validate proposer's offered assets
    if proposer_cc and not errors:
        cs = country_state.get(proposer_cc) or {}

        # Coins
        offered_coins = int(offer.get("coins") or 0)
        if offered_coins > 0:
            if scope == "country":
                available = float(cs.get("treasury") or 0)
                if offered_coins > available:
                    errors.append(f"INSUFFICIENT_COINS: offered {offered_coins}, treasury has {available:.0f}")
            elif scope == "personal":
                # Personal coins checked from role data
                role_info = (roles or {}).get(proposer_role) or {}
                personal = int(role_info.get("personal_coins") or 0)
                if offered_coins > personal:
                    errors.append(f"INSUFFICIENT_COINS: offered {offered_coins}, personal wallet has {personal}")

        # Units
        offered_units = offer.get("units") or []
        if isinstance(offered_units, list):
            for code in offered_units:
                u = units.get(code)
                if not u:
                    errors.append(f"UNKNOWN_UNIT: {code!r}")
                elif u.get("country_code") != proposer_cc:
                    errors.append(f"NOT_OWN_UNIT: {code!r} belongs to {u.get('country_code')!r}")
                elif (u.get("status") or "").lower() == "destroyed":
                    errors.append(f"UNIT_DESTROYED: {code!r}")

    if errors:
        return {"valid": False, "errors": errors, "warnings": warnings, "normalized": None}

    # Normalize
    normalized = {
        "action_type": "propose_transaction",
        "proposer_role_id": proposer_role,
        "proposer_country_code": proposer_cc,
        "scope": scope,
        "counterpart_role_id": counterpart_role,
        "counterpart_country_code": counterpart_cc,
        "round_num": payload.get("round_num"),
        "offer": {
            "coins": int(offer.get("coins") or 0),
            "units": sorted(offer.get("units") or [], key=lambda x: str(x)),
            "technology": offer.get("technology") or {},
            "basing_rights": bool(offer.get("basing_rights")),
        },
        "request": {
            "coins": int(request.get("coins") or 0),
            "units": request.get("units") or [],  # type+count dicts, not unit_ids
            "technology": request.get("technology") or {},
            "basing_rights": bool(request.get("basing_rights")),
        },
        "rationale": (payload.get("rationale") or "").strip(),
    }
    return {"valid": True, "errors": [], "warnings": warnings, "normalized": normalized}


def validate_execution(
    proposal: dict,
    units: dict[str, dict],
    country_state: dict[str, dict],
) -> dict:
    """Validate BOTH sides' assets at execution time.

    Called only after both parties confirmed. Checks that:
    - Proposer STILL has offered assets (may have changed since proposal)
    - Counterpart HAS the requested assets

    Returns ``{valid, errors}``.
    """
    errors: list[str] = []
    offer = proposal.get("offer") or {}
    request = proposal.get("request") or {}
    proposer_cc = proposal.get("proposer_country_code")
    counterpart_cc = proposal.get("counterpart_country_code")
    scope = proposal.get("scope", "country")

    # Check proposer still has offer
    _check_assets(proposer_cc, offer, units, country_state, scope, "proposer", errors)

    # Check counterpart has request
    _check_assets(counterpart_cc, request, units, country_state, scope, "counterpart", errors)

    return {"valid": len(errors) == 0, "errors": errors}


def _check_assets(
    cc: str, assets: dict, units: dict, cs: dict, scope: str, side: str,
    errors: list[str],
) -> None:
    """Check that a country has the specified assets."""
    state = cs.get(cc) or {}
    coins = int(assets.get("coins") or 0)
    if coins > 0 and scope == "country":
        treasury = float(state.get("treasury") or 0)
        if coins > treasury:
            errors.append(f"{side.upper()}_INSUFFICIENT_COINS: needs {coins}, has {treasury:.0f}")

    for item in (assets.get("units") or []):
        if isinstance(item, str):
            # Specific unit_id
            u = units.get(item)
            if not u:
                errors.append(f"{side.upper()}_UNKNOWN_UNIT: {item!r}")
            elif u.get("country_code") != cc:
                errors.append(f"{side.upper()}_NOT_OWN_UNIT: {item!r}")
            elif (u.get("status") or "").lower() in ("destroyed", "active"):
                if (u.get("status") or "").lower() != "reserve":
                    errors.append(f"{side.upper()}_UNIT_NOT_RESERVE: {item!r} is {u.get('status')}")
        elif isinstance(item, dict) and item.get("type") and item.get("count"):
            # Type + count request — check sufficient reserves
            utype = item["type"]
            needed = int(item["count"])
            available = sum(1 for u in units.values()
                          if u.get("country_code") == cc
                          and u.get("unit_type") == utype
                          and u.get("status") == "reserve")
            if available < needed:
                errors.append(f"{side.upper()}_INSUFFICIENT_UNITS: needs {needed} {utype} reserve, has {available}")
