"""Nuclear decision validators — CONTRACT_NUCLEAR_CHAIN v1.0.

Two validators:
  - ``validate_nuclear_test()`` — underground/surface test
  - ``validate_nuclear_launch()`` — nuclear missile launch (warhead="nuclear")

Both are Phase 1 (initiation) validators. The 3-way authorization chain
and interception decisions are handled by the NuclearChainOrchestrator,
not by these validators.
"""

from __future__ import annotations
from typing import Any

CANONICAL_COUNTRIES: frozenset[str] = frozenset({
    "albion", "bharata", "caribe", "cathay", "choson", "columbia",
    "formosa", "freeland", "gallia", "hanguk", "levantia", "mirage",
    "persia", "phrygia", "ponte", "ruthenia", "sarmatia", "solaria",
    "teutonia", "yamato",
})

ALLOWED_TOP = frozenset({"action_type", "country_code", "round_num", "decision", "rationale", "changes"})
RATIONALE_MIN = 30

# Range per tier (Manhattan distance)
TIER_RANGE = {1: 2, 2: 4, 3: 999}  # T3 = global


def _is_int(v: Any) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


# ---------------------------------------------------------------------------
# Nuclear Test validator
# ---------------------------------------------------------------------------

ALLOWED_TEST_CHANGES = frozenset({"test_type", "target_global_row", "target_global_col"})
VALID_TEST_TYPES = frozenset({"underground", "surface"})


def validate_nuclear_test(
    payload: dict,
    units: dict[str, dict],
    country_state: dict[str, dict],
    zones: dict[tuple[int, int], dict],
) -> dict:
    """Validate a nuclear_test decision per CONTRACT_NUCLEAR_CHAIN v1.0 §2.1."""
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["INVALID_PAYLOAD"], "warnings": [], "normalized": None}

    extra = set(payload.keys()) - ALLOWED_TOP
    if extra:
        errors.append(f"UNKNOWN_FIELD: {sorted(extra)}")

    if payload.get("action_type") != "nuclear_test":
        errors.append(f"INVALID_ACTION_TYPE: expected 'nuclear_test'")

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
            "action_type": "nuclear_test", "country_code": cc,
            "round_num": payload.get("round_num"), "decision": "no_change",
            "rationale": rationale.strip(),
        }}

    if not changes or not isinstance(changes, dict):
        errors.append("MISSING_CHANGES")
        return {"valid": False, "errors": errors, "warnings": warnings, "normalized": None}

    extra_ch = set(changes.keys()) - ALLOWED_TEST_CHANGES
    if extra_ch:
        errors.append(f"UNKNOWN_FIELD: change keys {sorted(extra_ch)}")

    test_type = changes.get("test_type")
    if test_type not in VALID_TEST_TYPES:
        errors.append(f"INVALID_TEST_TYPE: {test_type!r} not in {sorted(VALID_TEST_TYPES)}")

    tgt_r = changes.get("target_global_row")
    tgt_c = changes.get("target_global_col")
    if tgt_r is None or tgt_c is None:
        errors.append("MISSING_COORDS")
    elif not _is_int(tgt_r) or not _is_int(tgt_c) or not (1 <= tgt_r <= 10) or not (1 <= tgt_c <= 20):
        errors.append(f"BAD_COORDS: ({tgt_r},{tgt_c})")

    # Nuclear level check
    cs = country_state.get(cc) or {} if cc else {}
    nuc_level = int(cs.get("nuclear_level", 0) or 0)
    if nuc_level < 1:
        errors.append(f"NO_NUCLEAR_CAPABILITY: {cc} nuclear_level={nuc_level} (need ≥1)")

    # Target must be own territory
    if tgt_r is not None and tgt_c is not None:
        z = zones.get((tgt_r, tgt_c)) or {}
        if z.get("owner") != cc:
            errors.append(f"NOT_OWN_TERRITORY: target ({tgt_r},{tgt_c}) owned by {z.get('owner')!r}, not {cc!r}")

    if errors:
        return {"valid": False, "errors": errors, "warnings": warnings, "normalized": None}

    return {"valid": True, "errors": [], "warnings": warnings, "normalized": {
        "action_type": "nuclear_test", "country_code": cc,
        "round_num": payload.get("round_num"), "decision": "change",
        "rationale": rationale.strip(),
        "changes": {
            "test_type": test_type,
            "target_global_row": int(tgt_r),
            "target_global_col": int(tgt_c),
        },
    }}


# ---------------------------------------------------------------------------
# Nuclear Launch validator
# ---------------------------------------------------------------------------

ALLOWED_LAUNCH_CHANGES = frozenset({"warhead", "missiles"})


def validate_nuclear_launch(
    payload: dict,
    units: dict[str, dict],
    country_state: dict[str, dict],
    zones: dict[tuple[int, int], dict],
) -> dict:
    """Validate a launch_missile (warhead=nuclear) decision per CONTRACT_NUCLEAR_CHAIN v1.0 §2.2."""
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["INVALID_PAYLOAD"], "warnings": [], "normalized": None}

    extra = set(payload.keys()) - ALLOWED_TOP
    if extra:
        errors.append(f"UNKNOWN_FIELD: {sorted(extra)}")

    if payload.get("action_type") != "launch_missile":
        errors.append("INVALID_ACTION_TYPE: expected 'launch_missile'")

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
            "action_type": "launch_missile", "country_code": cc,
            "round_num": payload.get("round_num"), "decision": "no_change",
            "rationale": rationale.strip(),
        }}

    if not changes or not isinstance(changes, dict):
        errors.append("MISSING_CHANGES")
        return {"valid": False, "errors": errors, "warnings": warnings, "normalized": None}

    extra_ch = set(changes.keys()) - ALLOWED_LAUNCH_CHANGES
    if extra_ch:
        errors.append(f"UNKNOWN_FIELD: change keys {sorted(extra_ch)}")

    # Warhead must be nuclear
    if changes.get("warhead") != "nuclear":
        errors.append(f"INVALID_WARHEAD: expected 'nuclear', got {changes.get('warhead')!r}")

    # Country must have CONFIRMED nuclear tier
    cs = country_state.get(cc) or {} if cc else {}
    nuc_level = int(cs.get("nuclear_level", 0) or 0)
    nuc_confirmed = bool(cs.get("nuclear_confirmed", False))

    if nuc_level < 1:
        errors.append(f"NO_NUCLEAR_CAPABILITY: {cc} nuclear_level={nuc_level}")
    elif not nuc_confirmed:
        errors.append(f"NUCLEAR_NOT_CONFIRMED: {cc} has level {nuc_level} but nuclear_confirmed=false (test required)")

    # Missiles list
    missiles = changes.get("missiles")
    if not isinstance(missiles, list) or not missiles:
        errors.append("EMPTY_MISSILE_LIST: missiles must be a non-empty list")
        missiles = []

    # T1/T2 limit: max 1 missile
    if nuc_level <= 2 and len(missiles) > 1:
        errors.append(f"TOO_MANY_MISSILES: T{nuc_level} allows max 1 missile, got {len(missiles)}")

    max_range = TIER_RANGE.get(nuc_level, 2)

    seen_codes: set[str] = set()
    for i, m in enumerate(missiles):
        if not isinstance(m, dict):
            errors.append(f"INVALID_MISSILE_ENTRY: missiles[{i}] must be a dict")
            continue
        code = m.get("missile_unit_code")
        if not code or not isinstance(code, str):
            errors.append(f"MISSING_UNIT_CODE: missiles[{i}]")
            continue
        if code in seen_codes:
            errors.append(f"DUPLICATE_MISSILE: {code!r}")
        seen_codes.add(code)

        u = units.get(code)
        if not u:
            errors.append(f"UNKNOWN_UNIT: {code!r}")
            continue
        if u.get("country_code") != cc:
            errors.append(f"NOT_OWN_UNIT: {code!r}")
        if (u.get("unit_type") or "").lower() != "strategic_missile":
            errors.append(f"WRONG_UNIT_TYPE: {code!r} is {u.get('unit_type')!r}")
        if (u.get("status") or "").lower() != "active":
            errors.append(f"UNIT_NOT_ACTIVE: {code!r} must be deployed (active)")

        # Target coords
        tr = m.get("target_global_row")
        tc = m.get("target_global_col")
        if tr is None or tc is None:
            errors.append(f"MISSING_COORDS: missiles[{i}]")
        elif not _is_int(tr) or not _is_int(tc) or not (1 <= tr <= 10) or not (1 <= tc <= 20):
            errors.append(f"BAD_COORDS: missiles[{i}] ({tr},{tc})")
        elif u.get("global_row") is not None:
            dist = abs(u["global_row"] - tr) + abs(u.get("global_col", 0) - tc)
            if dist > max_range:
                errors.append(f"OUT_OF_RANGE: {code!r} distance {dist} > T{nuc_level} max {max_range}")

    if errors:
        return {"valid": False, "errors": errors, "warnings": warnings, "normalized": None}

    return {"valid": True, "errors": [], "warnings": warnings, "normalized": {
        "action_type": "launch_missile", "country_code": cc,
        "round_num": payload.get("round_num"), "decision": "change",
        "rationale": rationale.strip(),
        "changes": {
            "warhead": "nuclear",
            "missiles": [
                {
                    "missile_unit_code": m["missile_unit_code"],
                    "target_global_row": int(m["target_global_row"]),
                    "target_global_col": int(m["target_global_col"]),
                }
                for m in missiles
            ],
        },
    }}
