"""Agreement proposal validator — CONTRACT_AGREEMENTS v1.0."""

from __future__ import annotations

CANONICAL_COUNTRIES: frozenset[str] = frozenset({
    "albion", "bharata", "caribe", "cathay", "choson", "columbia",
    "formosa", "freeland", "gallia", "hanguk", "levantia", "mirage",
    "persia", "phrygia", "ponte", "ruthenia", "sarmatia", "solaria",
    "teutonia", "yamato",
})

VALID_VISIBILITIES = frozenset({"public", "secret"})

ALLOWED_TOP = frozenset({
    "action_type", "proposer_role_id", "proposer_country_code", "round_num",
    "agreement_name", "agreement_type", "visibility", "terms",
    "signatories", "rationale",
})


def validate_agreement_proposal(
    payload: dict,
    roles: dict[str, dict] | None = None,
) -> dict:
    """Validate a propose_agreement payload."""
    errors: list[str] = []

    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["INVALID_PAYLOAD"], "warnings": [], "normalized": None}

    if payload.get("action_type") != "propose_agreement":
        errors.append("INVALID_ACTION_TYPE: expected 'propose_agreement'")

    name = payload.get("agreement_name")
    if not name or not isinstance(name, str) or not name.strip():
        errors.append("MISSING_NAME: agreement_name required")

    atype = payload.get("agreement_type")
    if not atype or not isinstance(atype, str) or not atype.strip():
        errors.append("INVALID_TYPE: agreement_type required")

    visibility = payload.get("visibility")
    if visibility not in VALID_VISIBILITIES:
        errors.append(f"INVALID_VISIBILITY: {visibility!r} not in {sorted(VALID_VISIBILITIES)}")

    terms = payload.get("terms")
    if not terms or not isinstance(terms, str) or not terms.strip():
        errors.append("MISSING_TERMS: terms required (non-empty)")

    signatories = payload.get("signatories")
    if not isinstance(signatories, list) or len(signatories) < 2:
        errors.append("MISSING_SIGNATORIES: at least 2 country codes required")
        signatories = signatories or []
    else:
        for s in signatories:
            if s not in CANONICAL_COUNTRIES:
                errors.append(f"INVALID_SIGNATORY: {s!r} not a valid country")

    proposer_cc = payload.get("proposer_country_code")
    if proposer_cc and signatories and proposer_cc not in signatories:
        errors.append(f"PROPOSER_NOT_SIGNATORY: {proposer_cc!r} must be in signatories")

    # Role authorization: HoS, FM, or diplomat can sign
    proposer_role = payload.get("proposer_role_id")
    if proposer_role and roles:
        role_info = roles.get(proposer_role) or {}
        is_hos = bool(role_info.get("is_head_of_state"))
        is_diplomat = bool(role_info.get("is_diplomat"))
        powers = str(role_info.get("powers") or "")
        if not is_hos and not is_diplomat and "sign" not in powers.lower() and "agreement" not in powers.lower():
            errors.append(f"UNAUTHORIZED_ROLE: {proposer_role!r} not authorized to sign agreements")

    if errors:
        return {"valid": False, "errors": errors, "warnings": [], "normalized": None}

    return {"valid": True, "errors": [], "warnings": [], "normalized": {
        "action_type": "propose_agreement",
        "proposer_role_id": proposer_role,
        "proposer_country_code": proposer_cc,
        "round_num": payload.get("round_num"),
        "agreement_name": name.strip(),
        "agreement_type": atype.strip().lower(),
        "visibility": visibility,
        "terms": terms.strip(),
        "signatories": sorted(set(signatories)),
        "rationale": (payload.get("rationale") or "").strip(),
    }}
