"""Air strike decision validator — CONTRACT_AIR_STRIKES v1.0.

Pure validator for `attack_air` action payloads. State-dependent: needs
unit positions to verify the attacker units exist on the source hex,
the target hex contains enemy units, and range ≤ 2 cardinal hexes.

Used by:
- AI skill harness (M3 L3 tests)
- Test fixtures
- resolve_round.py _resolve_ranged_strikes (gates writes)
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
    "source_global_row", "source_global_col",
    "target_global_row", "target_global_col",
    "attacker_unit_codes",
})

RATIONALE_MIN_CHARS = 30
GLOBAL_ROW_MIN, GLOBAL_ROW_MAX = 1, 10
GLOBAL_COL_MIN, GLOBAL_COL_MAX = 1, 20

#: Range = 2 cardinal hexes (Manhattan distance)
MAX_RANGE = 2


def _is_real_int(v: Any) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def _hex_distance(r1: int, c1: int, r2: int, c2: int) -> int:
    return abs(r1 - r2) + abs(c1 - c2)


def validate_air_strike(
    payload: dict,
    units: dict[str, dict],
    country_state: dict[str, dict],
    zones: dict[tuple[int, int], dict],
) -> dict:
    """Validate an attack_air decision per CONTRACT_AIR_STRIKES v1.0."""
    errors: list[str] = []
    warnings: list[str] = []

    # 1. Top-level structural
    if not isinstance(payload, dict):
        return {
            "valid": False,
            "errors": ["INVALID_PAYLOAD: top-level must be a dict"],
            "warnings": [],
            "normalized": None,
        }

    extra_top = set(payload.keys()) - ALLOWED_TOP_FIELDS
    if extra_top:
        errors.append(f"UNKNOWN_FIELD: unexpected top-level keys {sorted(extra_top)}")

    if payload.get("action_type") != "attack_air":
        errors.append(
            f"INVALID_ACTION_TYPE: expected 'attack_air', got {payload.get('action_type')!r}"
        )

    decision = payload.get("decision")
    if decision not in ("change", "no_change"):
        errors.append(f"INVALID_DECISION: expected 'change' or 'no_change', got {decision!r}")

    rationale = payload.get("rationale")
    if not isinstance(rationale, str) or len(rationale.strip()) < RATIONALE_MIN_CHARS:
        errors.append(
            f"RATIONALE_TOO_SHORT: rationale must be a string ≥{RATIONALE_MIN_CHARS} chars"
        )

    country_code = payload.get("country_code")
    if not isinstance(country_code, str) or country_code not in CANONICAL_COUNTRIES:
        errors.append(
            f"UNKNOWN_FIELD: country_code {country_code!r} not in canonical roster"
        )

    # 2. Decision branch
    changes = payload.get("changes")

    if decision == "no_change":
        if changes is not None:
            errors.append(
                "UNEXPECTED_CHANGES: decision='no_change' must omit the 'changes' field"
            )
        if errors:
            return {"valid": False, "errors": errors, "warnings": warnings, "normalized": None}
        return {
            "valid": True,
            "errors": [],
            "warnings": warnings,
            "normalized": {
                "action_type": "attack_air",
                "country_code": country_code,
                "round_num": payload.get("round_num"),
                "decision": "no_change",
                "rationale": rationale.strip(),
            },
        }

    # change branch
    if changes is None:
        errors.append("MISSING_CHANGES: decision='change' requires a 'changes' block")
        return {"valid": False, "errors": errors, "warnings": warnings, "normalized": None}

    if not isinstance(changes, dict):
        errors.append("MISSING_CHANGES: 'changes' must be a dict")
        return {"valid": False, "errors": errors, "warnings": warnings, "normalized": None}

    extra_changes = set(changes.keys()) - ALLOWED_CHANGE_FIELDS
    if extra_changes:
        errors.append(f"UNKNOWN_FIELD: unexpected change keys {sorted(extra_changes)}")

    # 3. Coordinate checks
    src_r = changes.get("source_global_row")
    src_c = changes.get("source_global_col")
    tgt_r = changes.get("target_global_row")
    tgt_c = changes.get("target_global_col")

    coord_missing = [n for n, v in (
        ("source_global_row", src_r), ("source_global_col", src_c),
        ("target_global_row", tgt_r), ("target_global_col", tgt_c),
    ) if v is None]
    if coord_missing:
        errors.append(f"MISSING_COORDS: {sorted(coord_missing)}")

    coords_valid = True
    for name, v, lo, hi in (
        ("source_global_row", src_r, GLOBAL_ROW_MIN, GLOBAL_ROW_MAX),
        ("source_global_col", src_c, GLOBAL_COL_MIN, GLOBAL_COL_MAX),
        ("target_global_row", tgt_r, GLOBAL_ROW_MIN, GLOBAL_ROW_MAX),
        ("target_global_col", tgt_c, GLOBAL_COL_MIN, GLOBAL_COL_MAX),
    ):
        if v is None:
            continue
        if not _is_real_int(v) or v < lo or v > hi:
            errors.append(f"BAD_COORDS: {name}={v!r} (must be int in [{lo},{hi}])")
            coords_valid = False

    if coords_valid and not coord_missing:
        if (src_r, src_c) == (tgt_r, tgt_c):
            errors.append(f"SAME_HEX: source ({src_r},{src_c}) cannot equal target")
        else:
            dist = _hex_distance(src_r, src_c, tgt_r, tgt_c)
            if dist > MAX_RANGE:
                errors.append(
                    f"OUT_OF_RANGE: distance {dist} > {MAX_RANGE} hexes from "
                    f"({src_r},{src_c}) to ({tgt_r},{tgt_c})"
                )

    # 4. attacker_unit_codes checks
    attacker_codes = changes.get("attacker_unit_codes")
    if not isinstance(attacker_codes, list) or not attacker_codes:
        errors.append("EMPTY_ATTACKER_LIST: attacker_unit_codes must be a non-empty list")
        attacker_codes = []

    seen_codes: set[str] = set()
    duplicates: list[str] = []
    for c in attacker_codes:
        if not isinstance(c, str):
            errors.append(f"UNKNOWN_FIELD: attacker_unit_codes entry must be str, got {c!r}")
            continue
        if c in seen_codes:
            duplicates.append(c)
        seen_codes.add(c)
    if duplicates:
        errors.append(f"DUPLICATE_ATTACKER: {sorted(set(duplicates))}")

    if coords_valid and not coord_missing:
        for code in seen_codes:
            unit = units.get(code)
            if unit is None:
                errors.append(f"UNKNOWN_UNIT: attacker {code!r} not found")
                continue
            if unit.get("country_code") != country_code:
                errors.append(
                    f"NOT_OWN_UNIT: {code!r} belongs to {unit.get('country_code')!r}"
                )
                continue
            utype = (unit.get("unit_type") or "").lower()
            if utype != "tactical_air":
                errors.append(
                    f"WRONG_UNIT_TYPE: {code!r} is {utype!r}, must be tactical_air"
                )
                continue
            status = (unit.get("status") or "").lower()
            if status != "active":
                errors.append(
                    f"UNIT_NOT_ACTIVE: {code!r} status={status!r} (must be 'active')"
                )
                continue
            ur = unit.get("global_row")
            uc = unit.get("global_col")
            if (ur, uc) != (src_r, src_c):
                errors.append(
                    f"UNIT_NOT_ON_SOURCE: {code!r} at ({ur},{uc}), expected source ({src_r},{src_c})"
                )

    # 5. Target hex must contain enemies
    if coords_valid and not coord_missing and not errors:
        enemy_present = any(
            u.get("global_row") == tgt_r
            and u.get("global_col") == tgt_c
            and u.get("country_code") not in (None, country_code)
            and (u.get("status") or "").lower() == "active"
            for u in units.values()
        )
        if not enemy_present:
            errors.append(
                f"TARGET_FRIENDLY: target ({tgt_r},{tgt_c}) has no enemy active units"
            )

    if errors:
        return {"valid": False, "errors": errors, "warnings": warnings, "normalized": None}

    normalized = {
        "action_type": "attack_air",
        "country_code": country_code,
        "round_num": payload.get("round_num"),
        "decision": "change",
        "rationale": rationale.strip(),
        "changes": {
            "source_global_row": int(src_r),
            "source_global_col": int(src_c),
            "target_global_row": int(tgt_r),
            "target_global_col": int(tgt_c),
            "attacker_unit_codes": sorted(seen_codes),
        },
    }
    return {"valid": True, "errors": [], "warnings": warnings, "normalized": normalized}
