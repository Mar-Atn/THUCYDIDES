"""Movement engine — CONTRACT_MOVEMENT v1.0.

Pure state-mutation engine. The validator (`engine/services/movement_validator.py`)
has already proven the batch is legal; this module simply applies each move
in order to a unit-state dict.

See `PHASES/UNMANNED_SPACECRAFT/CONTRACT_MOVEMENT.md` §6 for the contract.

Per-move outcomes:
- ``target == "reserve"`` → withdraw to reserve pool (clear coords + embarked_on)
- ``target == "hex"`` →
    1. If unit is currently embarked, clear ``embarked_on`` first (debark).
    2. If the target hex has a friendly active naval unit with spare capacity
       AND the moving unit is ground / tactical_air → auto-embark.
    3. Otherwise, set coords + auto-derive theater fields and mark active.

Theater auto-derivation uses the canonical theater-link table from
``engine.config.map_config``: a global hex either IS a theater anchor (in which
case the unit is on the global side, theater coords are cleared) OR it isn't,
which is the same outcome — global coords are authoritative, theater coords
only matter for theater-grid display and are cleared on global moves.

Replaces deprecated ``engine/round_engine/movement.py`` (deleted in the M1
slice closing step).
"""

from __future__ import annotations

from typing import Optional

from engine.config.map_config import theater_for_global_hex

# ---------------------------------------------------------------------------
# Constants — keep in lock-step with movement_validator.py + CONTRACT §6.4
# ---------------------------------------------------------------------------

#: Unit types that can be auto-embarked onto a friendly carrier
EMBARKABLE_UNIT_TYPES: frozenset[str] = frozenset({"ground", "tactical_air"})

#: Per-carrier embark capacity: 1 ground + 2 tactical_air = 3 total embarked
CARRIER_CAPACITY_GROUND = 1
CARRIER_CAPACITY_AIR = 2


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _carrier_embark_counts(carrier_code: str, units: dict) -> tuple[int, int]:
    """Return (ground_count, tactical_air_count) embarked on this carrier."""
    g, a = 0, 0
    for u in units.values():
        if u.get("embarked_on") != carrier_code:
            continue
        ut = u.get("unit_type")
        if ut == "ground":
            g += 1
        elif ut == "tactical_air":
            a += 1
    return g, a


def _carrier_capacity_remaining(carrier: dict, all_units: dict) -> int:
    """Total remaining capacity on a carrier (ground + tactical_air slots)."""
    code = carrier["unit_code"]
    g, a = _carrier_embark_counts(code, all_units)
    return max(0, CARRIER_CAPACITY_GROUND - g) + max(0, CARRIER_CAPACITY_AIR - a)


def _friendly_carriers_at(
    country_code: str,
    tgt_row: int,
    tgt_col: int,
    incoming_unit_type: str,
    units: dict,
) -> list[dict]:
    """Friendly active naval units at the target hex with capacity for the
    incoming unit type."""
    if incoming_unit_type not in EMBARKABLE_UNIT_TYPES:
        return []
    out: list[dict] = []
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
                out.append(u)
            elif incoming_unit_type == "tactical_air" and a < CARRIER_CAPACITY_AIR:
                out.append(u)
    return out


def _hex_to_theater(
    global_row: int, global_col: int, zones: dict,
) -> tuple[Optional[str], Optional[int], Optional[int]]:
    """Return (theater, theater_row, theater_col) for a global hex.

    Authoritative source is ``engine.config.map_config.theater_for_global_hex``
    (the canonical theater-link table). Theater row/col are NOT computed —
    units operating on the global grid carry their theater coords as None.
    A future enhancement could derive theater coords from a per-zone lookup.
    """
    theater = theater_for_global_hex(global_row, global_col)
    return theater, None, None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def process_movements(
    moves: list[dict],
    country_code: str,
    units: dict[str, dict],
    zones: dict,
) -> list[dict]:
    """Apply a validated batch of moves atomically to ``units`` (mutated in place).

    Args:
        moves: list of normalized move dicts from
               ``validate_movement_decision``. Each move has:
                 - unit_code (str)
                 - target ("hex" or "reserve")
                 - target_global_row + target_global_col (only for "hex")
        country_code: actor (used for embark friendliness check)
        units: dict[unit_code → unit-state-dict], MUTATED in place
        zones: dict of zone records (passed through to ``_hex_to_theater``)

    Returns:
        list of per-move result dicts describing what actually happened —
        useful for the audit/Observatory event payload.
    """
    results: list[dict] = []

    for move in moves:
        unit_code = move["unit_code"]
        unit = units.get(unit_code)
        if unit is None:
            # Should never happen — validator already checked, but defensive.
            results.append({
                "unit_code": unit_code,
                "action": "skip",
                "reason": "unit not found",
            })
            continue

        target = move["target"]

        if target == "reserve":
            prev = {
                "global_row": unit.get("global_row"),
                "global_col": unit.get("global_col"),
                "theater": unit.get("theater"),
                "status": unit.get("status"),
                "embarked_on": unit.get("embarked_on"),
            }
            unit["status"] = "reserve"
            unit["global_row"] = None
            unit["global_col"] = None
            unit["theater"] = None
            unit["theater_row"] = None
            unit["theater_col"] = None
            unit["embarked_on"] = None
            results.append({
                "unit_code": unit_code,
                "action": "withdraw",
                "from": prev,
            })
            continue

        # target == "hex"
        tgt_row = move["target_global_row"]
        tgt_col = move["target_global_col"]

        prev = {
            "global_row": unit.get("global_row"),
            "global_col": unit.get("global_col"),
            "status": unit.get("status"),
            "embarked_on": unit.get("embarked_on"),
        }

        # Debark first: if currently embarked, clear embarked_on so the
        # carrier capacity calc that follows sees this slot as freed.
        if unit.get("status") == "embarked":
            unit["embarked_on"] = None

        unit_type = unit.get("unit_type", "")
        carriers = _friendly_carriers_at(
            country_code, tgt_row, tgt_col, unit_type, units,
        )

        if carriers:
            # Auto-embark — pick the carrier with most remaining capacity.
            carrier = max(
                carriers,
                key=lambda c: _carrier_capacity_remaining(c, units),
            )
            unit["status"] = "embarked"
            unit["embarked_on"] = carrier["unit_code"]
            unit["global_row"] = None
            unit["global_col"] = None
            unit["theater"] = None
            unit["theater_row"] = None
            unit["theater_col"] = None
            results.append({
                "unit_code": unit_code,
                "action": "embark",
                "carrier": carrier["unit_code"],
                "hex": [tgt_row, tgt_col],
                "from": prev,
            })
            continue

        # Normal hex move (or deploy from reserve, or debark + reposition)
        unit["status"] = "active"
        unit["embarked_on"] = None
        unit["global_row"] = tgt_row
        unit["global_col"] = tgt_col
        theater, t_row, t_col = _hex_to_theater(tgt_row, tgt_col, zones)
        unit["theater"] = theater
        unit["theater_row"] = t_row
        unit["theater_col"] = t_col

        if prev["status"] == "reserve":
            action = "deploy"
        elif prev["status"] == "embarked":
            action = "debark"
        else:
            action = "reposition"

        results.append({
            "unit_code": unit_code,
            "action": action,
            "to": [tgt_row, tgt_col],
            "theater": theater,
            "from": prev,
        })

    return results


__all__ = [
    "EMBARKABLE_UNIT_TYPES",
    "CARRIER_CAPACITY_GROUND",
    "CARRIER_CAPACITY_AIR",
    "process_movements",
]
