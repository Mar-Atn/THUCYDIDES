"""Covert ops validator — CARD_ACTIONS §4.1-4.4.

Unified validator for 2 covert op types:
  - sabotage: 50% success, card-based (consumable)
  - propaganda: 55% success, card-based

Note: intelligence is a SEPARATE standalone action, not a covert op subtype.
"""

from __future__ import annotations

CANONICAL_COUNTRIES: frozenset[str] = frozenset({
    "albion", "bharata", "caribe", "cathay", "choson", "columbia",
    "formosa", "freeland", "gallia", "hanguk", "levantia", "mirage",
    "persia", "phrygia", "ponte", "ruthenia", "sarmatia", "solaria",
    "teutonia", "yamato",
})

VALID_OP_TYPES = frozenset({"sabotage", "propaganda"})
VALID_SABOTAGE_TARGETS = frozenset({"infrastructure", "nuclear_tech", "military"})
VALID_PROPAGANDA_INTENTS = frozenset({"boost", "destabilize"})
RATIONALE_MIN = 30

# Card pool field names (from roles.csv)
CARD_POOL_FIELDS = {
    "sabotage": "sabotage_cards",
    "propaganda": "disinfo_cards",
}


def validate_covert_op(
    payload: dict,
    roles: dict[str, dict] | None = None,
) -> dict:
    """Validate a covert_op action."""
    errors: list[str] = []

    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["INVALID_PAYLOAD"], "warnings": [], "normalized": None}

    if payload.get("action_type") != "covert_op":
        errors.append("INVALID_ACTION_TYPE: expected 'covert_op'")

    rationale = payload.get("rationale")
    if not isinstance(rationale, str) or len(rationale.strip()) < RATIONALE_MIN:
        errors.append("RATIONALE_TOO_SHORT")

    cc = payload.get("country_code")
    role_id = payload.get("role_id")

    op_type = payload.get("op_type")
    if op_type not in VALID_OP_TYPES:
        errors.append(f"INVALID_OP_TYPE: {op_type!r} not in {sorted(VALID_OP_TYPES)}")
        return {"valid": False, "errors": errors, "warnings": [], "normalized": None}

    # Card availability check
    if roles and role_id:
        role_info = roles.get(role_id) or {}
        pool_field = CARD_POOL_FIELDS.get(op_type, "")
        cards_available = int(role_info.get(pool_field, 0) or 0)
        if cards_available <= 0:
            errors.append(f"NO_CARDS: {role_id!r} has 0 {pool_field} cards")

    # Type-specific validation
    if op_type == "sabotage":
        target_country = payload.get("target_country")
        target_type = payload.get("target_type")
        if not target_country or target_country not in CANONICAL_COUNTRIES:
            errors.append(f"INVALID_TARGET_COUNTRY: {target_country!r}")
        if target_type not in VALID_SABOTAGE_TARGETS:
            errors.append(f"INVALID_TARGET_TYPE: {target_type!r} not in {sorted(VALID_SABOTAGE_TARGETS)}")
        if target_country == cc:
            errors.append("SELF_SABOTAGE: cannot sabotage own country")

    elif op_type == "propaganda":
        target = payload.get("target")
        intent = payload.get("intent")
        if not target or target not in CANONICAL_COUNTRIES:
            errors.append(f"INVALID_TARGET: {target!r}")
        if intent not in VALID_PROPAGANDA_INTENTS:
            errors.append(f"INVALID_INTENT: {intent!r} not in {sorted(VALID_PROPAGANDA_INTENTS)}")

    if errors:
        return {"valid": False, "errors": errors, "warnings": [], "normalized": None}

    normalized: dict = {
        "action_type": "covert_op",
        "op_type": op_type,
        "country_code": cc,
        "role_id": role_id,
        "round_num": payload.get("round_num"),
        "rationale": rationale.strip(),
    }

    # Copy type-specific fields
    if op_type == "sabotage":
        normalized["target_country"] = payload["target_country"]
        normalized["target_type"] = payload["target_type"]
    elif op_type == "propaganda":
        normalized["target"] = payload["target"]
        normalized["intent"] = payload["intent"]
        normalized["content"] = (payload.get("content") or "").strip()
    return {"valid": True, "errors": [], "warnings": [], "normalized": normalized}
