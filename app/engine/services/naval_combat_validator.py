"""Naval combat decision validator — CONTRACT_NAVAL_COMBAT v1.0.

Pure validator for `attack_naval` 1v1 ship-vs-ship actions.
"""

from __future__ import annotations

from typing import Any

CANONICAL_COUNTRIES: frozenset[str] = frozenset({
    "albion", "bharata", "caribe", "cathay", "choson", "columbia",
    "formosa", "freeland", "gallia", "hanguk", "levantia", "mirage",
    "persia", "phrygia", "ponte", "ruthenia", "sarmatia", "solaria",
    "teutonia", "yamato",
})

ALLOWED_TOP_FIELDS: frozenset[str] = frozenset({
    "action_type", "country_code", "round_num", "decision", "rationale", "changes",
})

ALLOWED_CHANGE_FIELDS: frozenset[str] = frozenset({
    "attacker_unit_code", "target_unit_code",
})

RATIONALE_MIN_CHARS = 30


def _hex_distance(r1: int, c1: int, r2: int, c2: int) -> int:
    return abs(r1 - r2) + abs(c1 - c2)


def validate_naval_attack(
    payload: dict,
    units: dict[str, dict],
    country_state: dict[str, dict],
) -> dict:
    """Validate an attack_naval decision per CONTRACT_NAVAL_COMBAT v1.0."""
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["INVALID_PAYLOAD: must be dict"],
                "warnings": [], "normalized": None}

    extra = set(payload.keys()) - ALLOWED_TOP_FIELDS
    if extra:
        errors.append(f"UNKNOWN_FIELD: unexpected top-level keys {sorted(extra)}")

    if payload.get("action_type") != "attack_naval":
        errors.append(f"INVALID_ACTION_TYPE: expected 'attack_naval', got {payload.get('action_type')!r}")

    decision = payload.get("decision")
    if decision not in ("change", "no_change"):
        errors.append(f"INVALID_DECISION: expected 'change' or 'no_change', got {decision!r}")

    rationale = payload.get("rationale")
    if not isinstance(rationale, str) or len(rationale.strip()) < RATIONALE_MIN_CHARS:
        errors.append(f"RATIONALE_TOO_SHORT: ≥{RATIONALE_MIN_CHARS} chars required")

    country_code = payload.get("country_code")
    if not isinstance(country_code, str) or country_code not in CANONICAL_COUNTRIES:
        errors.append(f"UNKNOWN_FIELD: country_code {country_code!r} not in roster")

    changes = payload.get("changes")

    if decision == "no_change":
        if changes is not None:
            errors.append("UNEXPECTED_CHANGES: no_change must omit changes")
        if errors:
            return {"valid": False, "errors": errors, "warnings": warnings, "normalized": None}
        return {"valid": True, "errors": [], "warnings": warnings, "normalized": {
            "action_type": "attack_naval", "country_code": country_code,
            "round_num": payload.get("round_num"), "decision": "no_change",
            "rationale": rationale.strip(),
        }}

    if changes is None or not isinstance(changes, dict):
        errors.append("MISSING_CHANGES: change requires a changes dict")
        return {"valid": False, "errors": errors, "warnings": warnings, "normalized": None}

    extra_ch = set(changes.keys()) - ALLOWED_CHANGE_FIELDS
    if extra_ch:
        errors.append(f"UNKNOWN_FIELD: unexpected change keys {sorted(extra_ch)}")

    atk_code = changes.get("attacker_unit_code")
    tgt_code = changes.get("target_unit_code")

    if not atk_code or not isinstance(atk_code, str):
        errors.append("MISSING_UNIT_CODE: attacker_unit_code required")
    if not tgt_code or not isinstance(tgt_code, str):
        errors.append("MISSING_UNIT_CODE: target_unit_code required")

    if atk_code and tgt_code and atk_code == tgt_code:
        errors.append("SAME_UNIT: cannot attack yourself")

    atk_unit = units.get(atk_code) if atk_code else None
    tgt_unit = units.get(tgt_code) if tgt_code else None

    if atk_code and atk_unit is None:
        errors.append(f"UNKNOWN_UNIT: attacker {atk_code!r} not found")
    if tgt_code and tgt_unit is None:
        errors.append(f"UNKNOWN_UNIT: target {tgt_code!r} not found")

    if atk_unit:
        if atk_unit.get("country_code") != country_code:
            errors.append(f"NOT_OWN_UNIT: {atk_code!r} belongs to {atk_unit.get('country_code')!r}")
        if (atk_unit.get("unit_type") or "").lower() != "naval":
            errors.append(f"WRONG_UNIT_TYPE: {atk_code!r} is {atk_unit.get('unit_type')!r}, must be naval")
        if (atk_unit.get("status") or "").lower() != "active":
            errors.append(f"UNIT_NOT_ACTIVE: {atk_code!r} status={atk_unit.get('status')!r}")

    if tgt_unit:
        if tgt_unit.get("country_code") == country_code:
            errors.append(f"TARGET_FRIENDLY: {tgt_code!r} is own unit")
        if (tgt_unit.get("unit_type") or "").lower() != "naval":
            errors.append(f"WRONG_UNIT_TYPE: {tgt_code!r} is {tgt_unit.get('unit_type')!r}, must be naval")
        if (tgt_unit.get("status") or "").lower() != "active":
            errors.append(f"UNIT_NOT_ACTIVE: {tgt_code!r} status={tgt_unit.get('status')!r}")

    # Adjacency check (same or adjacent sea hex)
    if atk_unit and tgt_unit and not errors:
        ar, ac = atk_unit.get("global_row"), atk_unit.get("global_col")
        tr, tc = tgt_unit.get("global_row"), tgt_unit.get("global_col")
        if ar is not None and tr is not None:
            dist = _hex_distance(ar, ac, tr, tc)
            if dist > 1:
                errors.append(
                    f"NOT_ADJACENT_OR_SAME: attacker at ({ar},{ac}), target at ({tr},{tc}), distance {dist} > 1"
                )

    if errors:
        return {"valid": False, "errors": errors, "warnings": warnings, "normalized": None}

    return {"valid": True, "errors": [], "warnings": warnings, "normalized": {
        "action_type": "attack_naval", "country_code": country_code,
        "round_num": payload.get("round_num"), "decision": "change",
        "rationale": rationale.strip(),
        "changes": {
            "attacker_unit_code": atk_code,
            "target_unit_code": tgt_code,
        },
    }}
