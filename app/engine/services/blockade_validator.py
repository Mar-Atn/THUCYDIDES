"""Blockade decision validator — CONTRACT M5 Part B."""

from __future__ import annotations

CANONICAL_COUNTRIES: frozenset[str] = frozenset({
    "albion", "bharata", "caribe", "cathay", "choson", "columbia",
    "formosa", "freeland", "gallia", "hanguk", "levantia", "mirage",
    "persia", "phrygia", "ponte", "ruthenia", "sarmatia", "solaria",
    "teutonia", "yamato",
})

CANONICAL_CHOKEPOINTS = frozenset({"cp_caribe", "cp_gulf_gate", "cp_formosa"})
VALID_ACTIONS = frozenset({"establish", "lift", "partial_lift"})
VALID_LEVELS = frozenset({"partial", "full"})

ALLOWED_TOP = frozenset({"action_type", "country_code", "round_num", "decision", "rationale", "changes"})
ALLOWED_CHANGE = frozenset({"zone_id", "action", "level"})
RATIONALE_MIN = 30


def validate_blockade(
    payload: dict,
    units: dict[str, dict],
    zones: dict[tuple[int, int], dict],
) -> dict:
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["INVALID_PAYLOAD"], "warnings": [], "normalized": None}

    extra = set(payload.keys()) - ALLOWED_TOP
    if extra:
        errors.append(f"UNKNOWN_FIELD: {sorted(extra)}")

    if payload.get("action_type") != "blockade":
        errors.append(f"INVALID_ACTION_TYPE: expected 'blockade'")

    decision = payload.get("decision")
    if decision not in ("change", "no_change"):
        errors.append(f"INVALID_DECISION: {decision!r}")

    rationale = payload.get("rationale")
    if not isinstance(rationale, str) or len(rationale.strip()) < RATIONALE_MIN:
        errors.append("RATIONALE_TOO_SHORT")

    cc = payload.get("country_code")
    if not isinstance(cc, str) or cc not in CANONICAL_COUNTRIES:
        errors.append(f"UNKNOWN_FIELD: country_code {cc!r}")

    changes = payload.get("changes")

    if decision == "no_change":
        if changes is not None:
            errors.append("UNEXPECTED_CHANGES")
        if errors:
            return {"valid": False, "errors": errors, "warnings": warnings, "normalized": None}
        return {"valid": True, "errors": [], "warnings": warnings, "normalized": {
            "action_type": "blockade", "country_code": cc,
            "round_num": payload.get("round_num"), "decision": "no_change",
            "rationale": rationale.strip(),
        }}

    if not changes or not isinstance(changes, dict):
        errors.append("MISSING_CHANGES")
        return {"valid": False, "errors": errors, "warnings": warnings, "normalized": None}

    extra_ch = set(changes.keys()) - ALLOWED_CHANGE
    if extra_ch:
        errors.append(f"UNKNOWN_FIELD: change keys {sorted(extra_ch)}")

    zone_id = changes.get("zone_id")
    if zone_id not in CANONICAL_CHOKEPOINTS:
        errors.append(f"INVALID_ZONE: {zone_id!r} not in {sorted(CANONICAL_CHOKEPOINTS)}")

    action = changes.get("action")
    if action not in VALID_ACTIONS:
        errors.append(f"INVALID_ACTION: {action!r} not in {sorted(VALID_ACTIONS)}")

    level = changes.get("level")
    if action == "establish" and level not in VALID_LEVELS:
        errors.append(f"INVALID_LEVEL: {level!r} not in {sorted(VALID_LEVELS)}")

    # For establish: require own naval or ground at/near the chokepoint
    # (simplified — full hex-level check deferred to engine)
    if action == "establish" and not errors:
        has_unit_near = any(
            u.get("country_code") == cc
            and (u.get("status") or "").lower() == "active"
            and (u.get("unit_type") or "").lower() in ("naval", "ground")
            for u in units.values()
        )
        if not has_unit_near:
            errors.append("NO_UNIT_AT_CHOKEPOINT: no active military unit to enforce blockade")

    if errors:
        return {"valid": False, "errors": errors, "warnings": warnings, "normalized": None}

    norm_changes: dict = {"zone_id": zone_id, "action": action}
    if action == "establish":
        norm_changes["level"] = level

    return {"valid": True, "errors": [], "warnings": warnings, "normalized": {
        "action_type": "blockade", "country_code": cc,
        "round_num": payload.get("round_num"), "decision": "change",
        "rationale": rationale.strip(),
        "changes": norm_changes,
    }}
