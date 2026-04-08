# DEPRECATED (2026-04-06) — being replaced by engines/military.py (unit-level v2) + engines/round_tick.py
# See 3 DETAILED DESIGN/REUNIFICATION_AUDIT_2026-04-06.md. Do not add new logic here.
"""Movement & mobilization resolvers — Phase 1 MVP.

State here is represented as a mutable dict keyed by ``unit_code``. Each
resolver returns the updated state. No DB side effects.
"""

from __future__ import annotations

from typing import Optional


# Max hex-hops per turn by unit_type. Ground/armor = 1 (adjacent only),
# naval = 2, air = 3, missile = long-range (handled at strike time).
MOVE_RANGE: dict[str, int] = {
    "ground": 1,
    "armor": 1,
    "tactical_air": 3,
    "strategic_missile": 1,
    "naval": 2,
    "air_defense": 1,
}


def _chebyshev(a: tuple[int, int], b: tuple[int, int]) -> int:
    """Chebyshev hex distance on offset grid (8-neighbour)."""
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def _is_land_type(unit_type: str) -> bool:
    return unit_type in ("ground", "armor", "air_defense", "strategic_missile")


def _is_air_type(unit_type: str) -> bool:
    return unit_type in ("tactical_air",)


def _is_naval_type(unit_type: str) -> bool:
    return unit_type in ("naval",)


# Sea-hex lookup, seeded lazily from the Supabase-loaded global map.
_SEA_HEXES: set[tuple[int, int]] | None = None


def is_sea_hex(row: int, col: int) -> bool:
    """True if global hex (row, col) is a sea hex. Caches on first call."""
    global _SEA_HEXES
    if _SEA_HEXES is None:
        _SEA_HEXES = _load_sea_hexes()
    return (row, col) in _SEA_HEXES


def _load_sea_hexes() -> set[tuple[int, int]]:
    """Load sea-hex set from the canonical global map via Supabase.

    Falls back to an empty set if the data can't be loaded (guard is
    then effectively disabled — callers should not crash).
    """
    try:
        from engine.services.supabase import get_client
        client = get_client()
        # Template v1.0 carries the map rules
        res = client.table("sim_templates").select("rules").eq("code", "ttt_v1_0").limit(1).execute()
        if not res.data:
            return set()
        rules = res.data[0].get("rules") or {}
        grid = rules.get("map_global", {}).get("grid") or []
        out: set[tuple[int, int]] = set()
        for r, row in enumerate(grid):
            for c, hx in enumerate(row):
                if (hx or {}).get("owner") == "sea":
                    out.add((r + 1, c + 1))
        return out
    except Exception:
        return set()


def resolve_movement(
    action_payload: dict,
    current_state: dict[str, dict],
) -> tuple[dict[str, dict], str]:
    """Apply a ``move_unit`` action to state.

    Returns ``(new_state, narrative)``. On invalid move, returns the
    state unchanged with an explanatory narrative.
    """
    unit_code = action_payload.get("unit_code")
    tgt_row = action_payload.get("target_global_row")
    tgt_col = action_payload.get("target_global_col")

    if not unit_code or tgt_row is None or tgt_col is None:
        return current_state, f"Invalid move payload: missing fields ({unit_code})"

    if unit_code not in current_state:
        return current_state, f"Unknown unit {unit_code}"

    unit = current_state[unit_code]
    if unit.get("status") == "destroyed":
        return current_state, f"{unit_code} is destroyed, cannot move"

    src_row = unit.get("global_row")
    src_col = unit.get("global_col")
    unit_type = unit.get("unit_type", "ground")
    max_range = MOVE_RANGE.get(unit_type, 1)

    # Guard: if unit has no current coords (reserve or embarked), treat as deployment — no range check
    if src_row is None or src_col is None:
        pass  # reserves/embarked deploying: allow
    else:
        dist = _chebyshev((src_row, src_col), (tgt_row, tgt_col))
        if dist > max_range:
            return (
                current_state,
                f"{unit_code} ({unit_type}) cannot move {dist} hexes (max {max_range})",
            )

    src = (src_row, src_col)
    dst = (tgt_row, tgt_col)

    # Terrain guard (Marat 2026-04-05): non-naval non-embarked units
    # MUST NOT be placed on sea hexes.
    if _is_naval_type(unit_type):
        # Naval can go anywhere sea-linked; caller is trusted for sea-only check
        pass
    else:
        if is_sea_hex(tgt_row, tgt_col):
            return (
                current_state,
                f"{unit_code} ({unit_type}) cannot move to sea hex "
                f"({tgt_row},{tgt_col}) — only naval or embarked units allowed on sea",
            )

    unit["global_row"] = tgt_row
    unit["global_col"] = tgt_col
    unit["status"] = "active"
    return current_state, f"{unit_code} moved from {src} to {dst}"


def resolve_mobilization(
    action_payload: dict,
    current_state: dict[str, dict],
) -> tuple[dict[str, dict], str]:
    """Apply a ``mobilize_reserve`` action.

    Flips a reserve unit to active status, optionally moving to a
    target hex (1-hex range).
    """
    unit_code = action_payload.get("unit_code")
    if not unit_code or unit_code not in current_state:
        return current_state, f"Unknown reserve unit {unit_code}"

    unit = current_state[unit_code]
    if unit.get("status") == "destroyed":
        return current_state, f"{unit_code} is destroyed, cannot mobilize"

    unit["status"] = "active"

    tgt_row = action_payload.get("target_global_row")
    tgt_col = action_payload.get("target_global_col")
    if tgt_row is not None and tgt_col is not None:
        src_row = unit.get("global_row")
        src_col = unit.get("global_col")
        # Reserves typically have NULL coords — deployment from reserve is always allowed
        if src_row is None or src_col is None:
            unit["global_row"] = tgt_row
            unit["global_col"] = tgt_col
            return current_state, f"{unit_code} mobilized from reserve to ({tgt_row},{tgt_col})"
        if _chebyshev((src_row, src_col), (tgt_row, tgt_col)) <= 1:
            unit["global_row"] = tgt_row
            unit["global_col"] = tgt_col
            return current_state, f"{unit_code} mobilized and moved to ({tgt_row},{tgt_col})"
        return current_state, f"{unit_code} mobilized in place (target ({tgt_row},{tgt_col}) too far)"

    return current_state, f"{unit_code} mobilized in place"
