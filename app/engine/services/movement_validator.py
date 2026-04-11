"""Movement decision validator — CONTRACT_MOVEMENT v1.0.

Pure validator for `move_units` action payloads. Unlike the economic-slice
validators, this one requires context dicts (units, zones, basing_rights)
because movement rules are state-dependent: whether a target hex is legal
depends on who owns it, whether you have basing rights there, whether a
friendly unit is already on it, etc.

See `PHASES/UNMANNED_SPACECRAFT/CONTRACT_MOVEMENT.md` §4 for the authoritative
rules.

Used by:
- AI skill harness (validates LLM-produced move_units JSON before persistence)
- Human UI (future)
- Test fixtures
- resolve_round.py set_movements handler (gates writes to unit_states_per_round)

The validator collects ALL errors (does not stop at first) and returns a single
report. If ANY move in the batch is invalid, the entire batch is rejected
(atomic). Batch-internal state propagation is simulated in order so that
move #1's new position qualifies move #2's "previously occupied" check.
"""

from __future__ import annotations

import copy
from typing import Any

# ---------------------------------------------------------------------------
# SCHEMA CONSTANTS — keep in lock-step with CONTRACT_MOVEMENT v1.0 §2 + §4
# ---------------------------------------------------------------------------

#: Canonical 20-country roster. Used only for country_code validation.
CANONICAL_COUNTRIES: frozenset[str] = frozenset({
    "albion", "bharata", "caribe", "cathay", "choson", "columbia",
    "formosa", "freeland", "gallia", "hanguk", "levantia", "mirage",
    "persia", "phrygia", "ponte", "ruthenia", "sarmatia", "solaria",
    "teutonia", "yamato",
})

#: Unit types that are embarkable (can be loaded onto a friendly naval carrier)
EMBARKABLE_UNIT_TYPES: frozenset[str] = frozenset({"ground", "tactical_air"})

#: Unit types that cannot enter sea hexes under normal movement (land-bound)
LAND_BOUND_UNIT_TYPES: frozenset[str] = frozenset({
    "ground", "air_defense", "strategic_missile",
})

#: Per-carrier embark capacity: 1 ground + 2 tactical_air = 3 total
CARRIER_CAPACITY_GROUND = 1
CARRIER_CAPACITY_AIR = 2

ALLOWED_TOP_FIELDS: frozenset[str] = frozenset({
    "action_type", "country_code", "round_num", "decision", "rationale", "changes",
})

ALLOWED_CHANGE_FIELDS: frozenset[str] = frozenset({"moves"})

ALLOWED_MOVE_FIELDS: frozenset[str] = frozenset({
    "unit_code", "target", "target_global_row", "target_global_col",
})

VALID_TARGET_MODES: frozenset[str] = frozenset({"hex", "reserve"})

RATIONALE_MIN_CHARS = 30


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------


def _is_real_int(value: Any) -> bool:
    """True if value is an int and NOT a bool (bool is a subclass of int)."""
    return isinstance(value, int) and not isinstance(value, bool)


def _carrier_embark_counts(carrier_code: str, units: dict) -> tuple[int, int]:
    """Return (ground_count, air_count) currently embarked on the given carrier."""
    ground = 0
    air = 0
    for u in units.values():
        if u.get("embarked_on") == carrier_code:
            if u.get("unit_type") == "ground":
                ground += 1
            elif u.get("unit_type") == "tactical_air":
                air += 1
    return ground, air


def _hex_has_friendly_carrier_with_capacity(
    country_code: str,
    tgt_row: int,
    tgt_col: int,
    incoming_unit_type: str,
    units: dict,
) -> bool:
    """True if the target hex has a friendly naval carrier that could accept
    the incoming unit without exceeding capacity.

    Used by the validator to decide whether a sea-hex destination for a
    ground/air unit is legal (via auto-embark).
    """
    if incoming_unit_type not in EMBARKABLE_UNIT_TYPES:
        return False
    for u in units.values():
        if (
            u.get("country_code") == country_code
            and u.get("unit_type") == "naval"
            and u.get("status") == "active"
            and u.get("global_row") == tgt_row
            and u.get("global_col") == tgt_col
        ):
            g, a = _carrier_embark_counts(u["unit_code"], units)
            if incoming_unit_type == "ground" and g < CARRIER_CAPACITY_GROUND:
                return True
            if incoming_unit_type == "tactical_air" and a < CARRIER_CAPACITY_AIR:
                return True
    return False


def _is_sea_hex(tgt_row: int, tgt_col: int, zones: dict) -> bool:
    """True if the target hex is a sea hex.

    Sea identification: any zone whose id/name/type contains sea markers, OR
    any zone whose owner/controlled_by is 'sea'. The simplest canonical
    signal is `zones[zone_id].get('owner') == 'sea'` which matches the
    template seed data.

    The caller passes a `zones` dict keyed by `(global_row, global_col)` →
    zone record, OR by zone_id. This helper looks up via coords if the dict
    supports it.
    """
    key = (tgt_row, tgt_col)
    zone = zones.get(key) if isinstance(key, tuple) else None
    if zone is None:
        # Fall back: scan zones for one matching the coords (if zones dict
        # has a 'global_row'/'global_col' field per record)
        for z in zones.values():
            if z.get("global_row") == tgt_row and z.get("global_col") == tgt_col:
                zone = z
                break
    if zone is None:
        return False
    if zone.get("owner") == "sea":
        return True
    if zone.get("type") in ("sea", "ocean", "water"):
        return True
    return False


def _zone_at(tgt_row: int, tgt_col: int, zones: dict) -> dict | None:
    """Return the zone record at the given coords, or None."""
    key = (tgt_row, tgt_col)
    zone = zones.get(key) if isinstance(key, tuple) else None
    if zone is not None:
        return zone
    for z in zones.values():
        if z.get("global_row") == tgt_row and z.get("global_col") == tgt_col:
            return z
    return None


def _is_own_territory(country_code: str, tgt_row: int, tgt_col: int, zones: dict) -> bool:
    """True if the target hex is in a zone owned or controlled by the country."""
    zone = _zone_at(tgt_row, tgt_col, zones)
    if zone is None:
        return False
    return (
        zone.get("owner") == country_code
        or zone.get("controlled_by") == country_code
    )


def _has_basing_rights_at(
    country_code: str, tgt_row: int, tgt_col: int,
    zones: dict, basing_rights: dict,
) -> bool:
    """True if the country has basing rights in the zone at the target hex.

    `basing_rights` is a dict `country_code → set[host_country_code]` — if
    I have basing rights from country X, any zone owned by X is legal.
    """
    zone = _zone_at(tgt_row, tgt_col, zones)
    if zone is None:
        return False
    host = zone.get("owner") or zone.get("controlled_by")
    if not host:
        return False
    grantors = basing_rights.get(country_code, set())
    return host in grantors


def _previously_occupied_by(
    country_code: str, tgt_row: int, tgt_col: int, units: dict,
) -> bool:
    """True if the country has ≥1 active unit at the target hex."""
    for u in units.values():
        if (
            u.get("country_code") == country_code
            and u.get("status") == "active"
            and u.get("global_row") == tgt_row
            and u.get("global_col") == tgt_col
        ):
            return True
    return False


# ---------------------------------------------------------------------------
# MAIN VALIDATOR
# ---------------------------------------------------------------------------


def validate_movement_decision(
    payload: dict,
    units: dict[str, dict],
    zones: dict,
    basing_rights: dict[str, set],
) -> dict:
    """Validate a movement decision against CONTRACT_MOVEMENT v1.0.

    Args:
        payload: the decision dict submitted by participant (AI or human)
        units: dict keyed by unit_code → unit state (country_code, unit_type,
               global_row, global_col, theater, status, embarked_on)
        zones: dict of zone records. May be keyed by zone_id OR by
               (global_row, global_col) tuple — helpers try both.
        basing_rights: dict country_code → set[host_country_code]

    Returns:
        {
            "valid":      bool,
            "errors":     list[str],
            "warnings":   list[str],
            "normalized": dict | None,
        }
    """
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(payload, dict):
        return {
            "valid": False,
            "errors": [f"INVALID_PAYLOAD: expected dict, got {type(payload).__name__}"],
            "warnings": [],
            "normalized": None,
        }

    # -----------------------------------------------------------------------
    # STRUCTURAL VALIDATION (§4)
    # -----------------------------------------------------------------------

    action_type = payload.get("action_type")
    if action_type != "move_units":
        errors.append(
            f"INVALID_ACTION_TYPE: got {action_type!r}, must be 'move_units'"
        )

    actor_raw = payload.get("country_code")
    actor: str | None = None
    if isinstance(actor_raw, str) and actor_raw.strip():
        actor = actor_raw.strip().lower()

    decision = payload.get("decision")
    if decision not in ("change", "no_change"):
        errors.append(
            f"INVALID_DECISION: got {decision!r}, must be 'change' or 'no_change'"
        )

    rationale = payload.get("rationale")
    rationale_trimmed = ""
    if not isinstance(rationale, str):
        errors.append(
            f"RATIONALE_TOO_SHORT: got {type(rationale).__name__}, "
            f"must be str >= {RATIONALE_MIN_CHARS} chars"
        )
    else:
        rationale_trimmed = rationale.strip()
        if len(rationale_trimmed) < RATIONALE_MIN_CHARS:
            errors.append(
                f"RATIONALE_TOO_SHORT: {len(rationale_trimmed)} chars, "
                f"must be >= {RATIONALE_MIN_CHARS}"
            )

    changes = payload.get("changes")
    changes_present = "changes" in payload and changes is not None

    if decision == "change" and not changes_present:
        errors.append("MISSING_CHANGES: decision='change' requires 'changes' object")
    if decision == "no_change" and changes_present:
        errors.append(
            "UNEXPECTED_CHANGES: decision='no_change' must not include 'changes'"
        )

    for field_name in payload.keys():
        if field_name not in ALLOWED_TOP_FIELDS:
            errors.append(f"UNKNOWN_FIELD: top-level field {field_name!r} not allowed")

    # -----------------------------------------------------------------------
    # MOVES BATCH VALIDATION (if present)
    # -----------------------------------------------------------------------

    normalized_moves: list[dict] | None = None

    if changes_present:
        if not isinstance(changes, dict):
            errors.append(
                f"MISSING_CHANGES: 'changes' must be dict, got {type(changes).__name__}"
            )
        else:
            for key in changes.keys():
                if key not in ALLOWED_CHANGE_FIELDS:
                    errors.append(
                        f"UNKNOWN_FIELD: changes.{key!r} not allowed "
                        f"(expected {sorted(ALLOWED_CHANGE_FIELDS)})"
                    )

            moves = changes.get("moves")
            if not isinstance(moves, list):
                errors.append(
                    f"MISSING_CHANGES: 'changes.moves' must be list, "
                    f"got {type(moves).__name__}"
                )
            elif len(moves) == 0:
                errors.append(
                    "EMPTY_CHANGES: decision='change' with empty moves list — "
                    "use decision='no_change' instead"
                )
            else:
                # Deep copy units state for batch-internal simulation.
                # Move #1 may change state that move #2 depends on.
                sim_units = copy.deepcopy(units)
                normalized_moves = []
                seen_unit_codes: set[str] = set()

                for move_idx, move in enumerate(moves):
                    move_errors = _validate_single_move(
                        move, move_idx, actor, sim_units, zones, basing_rights,
                        seen_unit_codes,
                    )
                    errors.extend(move_errors)

                    if not move_errors:
                        # Add to normalized list AND simulate in sim_units
                        norm_move = _normalize_move(move)
                        normalized_moves.append(norm_move)
                        _apply_move_to_sim(norm_move, actor, sim_units, zones)
                        seen_unit_codes.add(norm_move["unit_code"])

    # -----------------------------------------------------------------------
    # BUILD NORMALIZED OUTPUT
    # -----------------------------------------------------------------------

    if errors:
        return {
            "valid": False,
            "errors": errors,
            "warnings": warnings,
            "normalized": None,
        }

    normalized: dict = {
        "action_type": "move_units",
        "country_code": actor,
        "round_num": payload.get("round_num"),
        "decision": decision,
        "rationale": rationale_trimmed,
    }
    if decision == "change":
        normalized["changes"] = {"moves": normalized_moves or []}

    return {
        "valid": True,
        "errors": [],
        "warnings": warnings,
        "normalized": normalized,
    }


# ---------------------------------------------------------------------------
# PER-MOVE VALIDATION
# ---------------------------------------------------------------------------


def _validate_single_move(
    move: Any,
    move_idx: int,
    actor: str | None,
    sim_units: dict,
    zones: dict,
    basing_rights: dict,
    seen_unit_codes: set[str],
) -> list[str]:
    """Validate one move in the batch. Returns list of error strings (empty = OK)."""
    errors: list[str] = []
    prefix = f"move[{move_idx}]"

    if not isinstance(move, dict):
        return [f"INVALID_TARGET: {prefix} must be a dict, got {type(move).__name__}"]

    # Unknown fields
    for key in move.keys():
        if key not in ALLOWED_MOVE_FIELDS:
            errors.append(
                f"UNKNOWN_FIELD: {prefix}.{key!r} not allowed "
                f"(expected {sorted(ALLOWED_MOVE_FIELDS)})"
            )

    unit_code = move.get("unit_code")
    if not isinstance(unit_code, str) or not unit_code.strip():
        errors.append(f"UNKNOWN_UNIT: {prefix}.unit_code must be non-empty string")
        return errors
    unit_code = unit_code.strip()

    if unit_code in seen_unit_codes:
        errors.append(
            f"DUPLICATE_UNIT_IN_BATCH: {prefix} unit {unit_code!r} already moved "
            f"earlier in this batch"
        )

    unit = sim_units.get(unit_code)
    if unit is None:
        errors.append(f"UNKNOWN_UNIT: {prefix} unit {unit_code!r} not found")
        return errors

    if unit.get("country_code") != actor:
        errors.append(
            f"UNIT_NOT_OWNED: {prefix} unit {unit_code!r} belongs to "
            f"{unit.get('country_code')!r}, not {actor!r}"
        )
        return errors

    if unit.get("status") == "destroyed":
        errors.append(f"UNIT_DESTROYED: {prefix} unit {unit_code!r} is destroyed")
        return errors

    # Target validation
    target = move.get("target")
    if target not in VALID_TARGET_MODES:
        errors.append(
            f"INVALID_TARGET: {prefix}.target must be in "
            f"{sorted(VALID_TARGET_MODES)}, got {target!r}"
        )
        return errors

    if target == "reserve":
        # Withdraw to reserve — always legal, no coords needed
        return errors

    # target == "hex" — coords required
    tgt_row = move.get("target_global_row")
    tgt_col = move.get("target_global_col")
    if not _is_real_int(tgt_row) or not _is_real_int(tgt_col):
        errors.append(
            f"INVALID_TARGET: {prefix} target='hex' requires integer "
            f"target_global_row and target_global_col, "
            f"got row={tgt_row!r} col={tgt_col!r}"
        )
        return errors

    unit_type = unit.get("unit_type", "")
    is_sea = _is_sea_hex(tgt_row, tgt_col, zones)

    # Naval: sea hexes only
    if unit_type == "naval":
        if not is_sea:
            errors.append(
                f"LAND_HEX_FORBIDDEN: {prefix} naval unit {unit_code!r} "
                f"cannot move to land hex ({tgt_row}, {tgt_col})"
            )
        return errors

    # Land-bound / air: if sea hex, must have auto-embark opportunity
    if is_sea:
        if unit_type in EMBARKABLE_UNIT_TYPES and _hex_has_friendly_carrier_with_capacity(
            actor, tgt_row, tgt_col, unit_type, sim_units,
        ):
            # Auto-embark is possible — legal
            return errors
        errors.append(
            f"SEA_HEX_FORBIDDEN: {prefix} {unit_type} unit {unit_code!r} "
            f"cannot move to sea hex ({tgt_row}, {tgt_col}) "
            f"(no friendly carrier with capacity)"
        )
        return errors

    # Land hex: check allowed_territory for land-bound units
    # (ground, AD, strategic_missile, AND tactical_air — per CARD §1.1 air
    # has same land constraints as ground plus the embark option)
    if unit_type in LAND_BOUND_UNIT_TYPES or unit_type == "tactical_air":
        own = _is_own_territory(actor, tgt_row, tgt_col, zones)
        basing = _has_basing_rights_at(actor, tgt_row, tgt_col, zones, basing_rights)
        prev_occ = _previously_occupied_by(actor, tgt_row, tgt_col, sim_units)
        if not (own or basing or prev_occ):
            zone = _zone_at(tgt_row, tgt_col, zones)
            zone_info = f"zone={zone.get('id') if zone else '?'} owner={zone.get('owner') if zone else '?'}"
            errors.append(
                f"NOT_ALLOWED_TERRITORY: {prefix} {unit_type} unit {unit_code!r} "
                f"cannot move to hex ({tgt_row}, {tgt_col}) "
                f"({zone_info}) — not own territory, no basing rights, "
                f"and no previously-occupied hex"
            )

    return errors


def _normalize_move(move: dict) -> dict:
    """Produce a canonical normalized move dict (trimmed types)."""
    norm: dict = {
        "unit_code": move["unit_code"].strip(),
        "target": move["target"],
    }
    if move["target"] == "hex":
        norm["target_global_row"] = int(move["target_global_row"])
        norm["target_global_col"] = int(move["target_global_col"])
    return norm


def _apply_move_to_sim(
    move: dict, actor: str, sim_units: dict, zones: dict,
) -> None:
    """Apply a normalized move to the simulated units dict (for batch validation)."""
    unit = sim_units[move["unit_code"]]

    if move["target"] == "reserve":
        unit["status"] = "reserve"
        unit["global_row"] = None
        unit["global_col"] = None
        unit["theater"] = None
        unit["theater_row"] = None
        unit["theater_col"] = None
        unit["embarked_on"] = None
        return

    # target == "hex"
    tgt_row = move["target_global_row"]
    tgt_col = move["target_global_col"]

    # Clear embarked_on first (handles debark case)
    unit["embarked_on"] = None

    # Check for auto-embark
    unit_type = unit.get("unit_type", "")
    if unit_type in EMBARKABLE_UNIT_TYPES and _hex_has_friendly_carrier_with_capacity(
        actor, tgt_row, tgt_col, unit_type, sim_units,
    ):
        # Find the carrier with most capacity at this hex
        carriers = [
            u for u in sim_units.values()
            if (u.get("country_code") == actor
                and u.get("unit_type") == "naval"
                and u.get("status") == "active"
                and u.get("global_row") == tgt_row
                and u.get("global_col") == tgt_col)
        ]
        if carriers:
            # Pick any valid carrier (first one) — the engine does the same
            carrier = carriers[0]
            unit["status"] = "embarked"
            unit["embarked_on"] = carrier["unit_code"]
            unit["global_row"] = None
            unit["global_col"] = None
            unit["theater"] = None
            unit["theater_row"] = None
            unit["theater_col"] = None
            return

    # Normal hex move
    unit["status"] = "active"
    unit["global_row"] = tgt_row
    unit["global_col"] = tgt_col
    # Theater auto-derivation is the engine's job; validator doesn't need to
    # track theater coords in the sim.
