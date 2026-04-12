"""Naval bombardment validator — CONTRACT M5 Part A."""

from __future__ import annotations
from typing import Any

CANONICAL_COUNTRIES: frozenset[str] = frozenset({
    "albion", "bharata", "caribe", "cathay", "choson", "columbia",
    "formosa", "freeland", "gallia", "hanguk", "levantia", "mirage",
    "persia", "phrygia", "ponte", "ruthenia", "sarmatia", "solaria",
    "teutonia", "yamato",
})

ALLOWED_TOP = frozenset({"action_type", "country_code", "round_num", "decision", "rationale", "changes"})
ALLOWED_CHANGE = frozenset({"naval_unit_codes", "target_global_row", "target_global_col"})
RATIONALE_MIN = 30


def _is_int(v: Any) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def _hex_distance(r1, c1, r2, c2):
    return abs(r1 - r2) + abs(c1 - c2)


def validate_bombardment(
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

    if payload.get("action_type") != "attack_bombardment":
        errors.append(f"INVALID_ACTION_TYPE: expected 'attack_bombardment'")

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
            "action_type": "attack_bombardment", "country_code": cc,
            "round_num": payload.get("round_num"), "decision": "no_change",
            "rationale": rationale.strip(),
        }}

    if not changes or not isinstance(changes, dict):
        errors.append("MISSING_CHANGES")
        return {"valid": False, "errors": errors, "warnings": warnings, "normalized": None}

    extra_ch = set(changes.keys()) - ALLOWED_CHANGE
    if extra_ch:
        errors.append(f"UNKNOWN_FIELD: change keys {sorted(extra_ch)}")

    codes = changes.get("naval_unit_codes")
    if not isinstance(codes, list) or not codes:
        errors.append("EMPTY_NAVAL_LIST")
        codes = []

    tgt_r = changes.get("target_global_row")
    tgt_c = changes.get("target_global_col")
    if tgt_r is None or tgt_c is None:
        errors.append("MISSING_COORDS")
    elif not _is_int(tgt_r) or not _is_int(tgt_c) or not (1 <= tgt_r <= 10) or not (1 <= tgt_c <= 20):
        errors.append(f"BAD_COORDS: ({tgt_r},{tgt_c})")

    # Target must be land
    if tgt_r is not None and tgt_c is not None:
        z = zones.get((tgt_r, tgt_c)) or {}
        if (z.get("type") or "").lower() == "sea":
            errors.append(f"TARGET_NOT_LAND: ({tgt_r},{tgt_c}) is sea")

    # Check each naval unit
    for code in codes:
        if not isinstance(code, str):
            continue
        u = units.get(code)
        if not u:
            errors.append(f"UNKNOWN_UNIT: {code!r}")
            continue
        if u.get("country_code") != cc:
            errors.append(f"NOT_OWN_UNIT: {code!r}")
            continue
        if (u.get("unit_type") or "").lower() != "naval":
            errors.append(f"WRONG_UNIT_TYPE: {code!r} is {u.get('unit_type')!r}")
            continue
        if (u.get("status") or "").lower() != "active":
            errors.append(f"UNIT_NOT_ACTIVE: {code!r}")
            continue
        # Must be on adjacent sea hex
        ur, uc = u.get("global_row"), u.get("global_col")
        if ur is not None and tgt_r is not None:
            if _hex_distance(ur, uc, tgt_r, tgt_c) > 1:
                errors.append(f"NOT_ADJACENT: {code!r} at ({ur},{uc}) not adjacent to ({tgt_r},{tgt_c})")

    # Must have enemy ground on target
    if tgt_r is not None and tgt_c is not None and not errors:
        enemy_ground = any(
            u.get("global_row") == tgt_r and u.get("global_col") == tgt_c
            and u.get("country_code") not in (None, cc)
            and (u.get("status") or "").lower() == "active"
            and (u.get("unit_type") or "").lower() in ("ground", "armor")
            for u in units.values()
        )
        if not enemy_ground:
            errors.append(f"NO_GROUND_TARGETS: no enemy ground at ({tgt_r},{tgt_c})")

    if errors:
        return {"valid": False, "errors": errors, "warnings": warnings, "normalized": None}

    return {"valid": True, "errors": [], "warnings": warnings, "normalized": {
        "action_type": "attack_bombardment", "country_code": cc,
        "round_num": payload.get("round_num"), "decision": "change",
        "rationale": rationale.strip(),
        "changes": {
            "naval_unit_codes": sorted(set(codes)),
            "target_global_row": int(tgt_r),
            "target_global_col": int(tgt_c),
        },
    }}
