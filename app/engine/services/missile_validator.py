"""Conventional missile launch validator — CONTRACT M5 / CARD_ACTIONS §1.8a.

Validates `launch_missile` with `warhead: "conventional"`. Nuclear warheads
are M6 scope — this validator rejects `warhead: "nuclear"`.

Missile consumed on launch regardless of outcome. Range depends on the
country's nuclear tech level (T1: ≤2, T2: ≤4, T3: global) BUT since
conventional missiles don't require nuclear program, they use a fixed
range of ≤4 hexes (Template-customizable).
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
ALLOWED_CHANGE = frozenset({
    "missile_unit_code", "warhead", "target_global_row", "target_global_col", "target_choice",
})
VALID_TARGET_CHOICES = frozenset({"military", "infrastructure", "nuclear_site", "ad"})
RATIONALE_MIN = 30
CONVENTIONAL_MAX_RANGE = 4  # Template-customizable default


def _is_int(v: Any) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def validate_missile_launch(
    payload: dict,
    units: dict[str, dict],
    country_state: dict[str, dict],
    zones: dict[tuple[int, int], dict],
) -> dict:
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

    extra_ch = set(changes.keys()) - ALLOWED_CHANGE
    if extra_ch:
        errors.append(f"UNKNOWN_FIELD: change keys {sorted(extra_ch)}")

    # Warhead must be conventional (nuclear is M6)
    warhead = changes.get("warhead")
    if warhead != "conventional":
        errors.append(f"INVALID_WARHEAD: expected 'conventional', got {warhead!r} (nuclear is M6)")

    # Missile unit
    missile_code = changes.get("missile_unit_code")
    if not missile_code or not isinstance(missile_code, str):
        errors.append("MISSING_UNIT_CODE: missile_unit_code required")
    else:
        u = units.get(missile_code)
        if not u:
            errors.append(f"UNKNOWN_UNIT: {missile_code!r}")
        else:
            if u.get("country_code") != cc:
                errors.append(f"NOT_OWN_UNIT: {missile_code!r}")
            if (u.get("unit_type") or "").lower() != "strategic_missile":
                errors.append(f"WRONG_UNIT_TYPE: {missile_code!r} is {u.get('unit_type')!r}, must be strategic_missile")
            if (u.get("status") or "").lower() != "active":
                errors.append(f"UNIT_NOT_ACTIVE: {missile_code!r} must be active (deployed on map)")

    # Target coords
    tgt_r = changes.get("target_global_row")
    tgt_c = changes.get("target_global_col")
    if tgt_r is None or tgt_c is None:
        errors.append("MISSING_COORDS")
    elif not _is_int(tgt_r) or not _is_int(tgt_c) or not (1 <= tgt_r <= 10) or not (1 <= tgt_c <= 20):
        errors.append(f"BAD_COORDS: ({tgt_r},{tgt_c})")

    # Range check (from missile's current position)
    if missile_code and tgt_r is not None and units.get(missile_code):
        mu = units[missile_code]
        mr, mc = mu.get("global_row"), mu.get("global_col")
        if mr is not None and mc is not None:
            dist = abs(mr - tgt_r) + abs(mc - tgt_c)
            if dist > CONVENTIONAL_MAX_RANGE:
                errors.append(f"OUT_OF_RANGE: distance {dist} > {CONVENTIONAL_MAX_RANGE}")

    # Target choice
    target_choice = changes.get("target_choice")
    if target_choice not in VALID_TARGET_CHOICES:
        errors.append(f"INVALID_TARGET_CHOICE: {target_choice!r} not in {sorted(VALID_TARGET_CHOICES)}")

    if errors:
        return {"valid": False, "errors": errors, "warnings": warnings, "normalized": None}

    return {"valid": True, "errors": [], "warnings": warnings, "normalized": {
        "action_type": "launch_missile", "country_code": cc,
        "round_num": payload.get("round_num"), "decision": "change",
        "rationale": rationale.strip(),
        "changes": {
            "missile_unit_code": missile_code,
            "warhead": "conventional",
            "target_global_row": int(tgt_r),
            "target_global_col": int(tgt_c),
            "target_choice": target_choice,
        },
    }}
