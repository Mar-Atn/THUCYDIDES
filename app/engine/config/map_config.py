"""Central map configuration — single source of truth for map dimensions,
theater definitions, and the canonical theater <-> global linkage.

Any code that touches map grid dimensions, theater definitions, or the
theater<->global linkage MUST import from here. Do NOT hardcode these
values elsewhere.

Canonical mapping approved by Marat 2026-04-05 (Template v1.0).
Mirrored in `app/test-interface/static/map_config.js` for browser code.
"""
from __future__ import annotations

from typing import Optional

# ---------------------------------------------------------------------------
# VERSION
# ---------------------------------------------------------------------------
MAP_CONFIG_VERSION = "1.1"  # v1.1 2026-04-15 — hex convention formalized

# ---------------------------------------------------------------------------
# HEX CONVENTION (canonical — all rendering and engine code must follow)
# ---------------------------------------------------------------------------
# Type:       Pointy-top hexagons
# Offset:     Odd-r (odd rows shifted right by half hex)
# Coordinates: (row, col), 1-indexed, row first
# Row 1 at top of map
#
# Visual layout:
#   Row 1:  [1,1] [1,2] [1,3] ...
#   Row 2:    [2,1] [2,2] [2,3] ...    (shifted right)
#   Row 3:  [3,1] [3,2] [3,3] ...
#
# Adjacency (6 neighbors per hex):
#   Odd rows  (1,3,5,7,9):  (-1,0) (-1,+1) (0,-1) (0,+1) (+1,0) (+1,+1)
#   Even rows (2,4,6,8,10): (-1,-1) (-1,0) (0,-1) (0,+1) (+1,-1) (+1,0)

HEX_TYPE = "pointy_top"
HEX_OFFSET = "odd_r"


def hex_neighbors(row: int, col: int) -> list[tuple[int, int]]:
    """Return the 6 adjacent hex coordinates for a given (row, col).

    Uses odd-r offset convention (pointy-top). Coordinates are 1-indexed.
    In 1-indexed coords, EVEN rows are visually shifted right (they map to
    0-indexed odd rows in the renderer which applies the half-hex offset).
    Does NOT check bounds — caller must filter.
    """
    if row % 2 == 0:  # even row (1-indexed) = shifted right in renderer
        deltas = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, 0), (1, 1)]
    else:  # odd row (1-indexed) = NOT shifted
        deltas = [(-1, -1), (-1, 0), (0, -1), (0, 1), (1, -1), (1, 0)]
    return [(row + dr, col + dc) for dr, dc in deltas]


def hex_neighbors_bounded(row: int, col: int, max_rows: int = 10, max_cols: int = 20) -> list[tuple[int, int]]:
    """Return adjacent hex coordinates, filtered to grid bounds (1-indexed)."""
    return [
        (r, c) for r, c in hex_neighbors(row, col)
        if 1 <= r <= max_rows and 1 <= c <= max_cols
    ]


# ---------------------------------------------------------------------------
# GLOBAL MAP DIMENSIONS
# ---------------------------------------------------------------------------
GLOBAL_ROWS: int = 10
GLOBAL_COLS: int = 20

# ---------------------------------------------------------------------------
# THEATERS
# ---------------------------------------------------------------------------
THEATERS: dict[str, dict] = {
    "eastern_ereb": {"rows": 10, "cols": 10, "display_name": "Eastern Ereb"},
    "mashriq":      {"rows": 10, "cols": 10, "display_name": "Mashriq"},
}
THEATER_NAMES: list[str] = sorted(THEATERS.keys())

# ---------------------------------------------------------------------------
# COUNTRY CODES (20 countries, alphabetical)
# ---------------------------------------------------------------------------
COUNTRY_CODES: list[str] = [
    "albion",
    "bharata",
    "caribe",
    "cathay",
    "choson",
    "columbia",
    "formosa",
    "freeland",
    "gallia",
    "hanguk",
    "levantia",
    "mirage",
    "persia",
    "phrygia",
    "ponte",
    "ruthenia",
    "sarmatia",
    "solaria",
    "teutonia",
    "yamato",
]

# ---------------------------------------------------------------------------
# UNIT TYPES & STATUSES
# ---------------------------------------------------------------------------
UNIT_TYPES: list[str] = [
    "ground",
    "tactical_air",
    "strategic_missile",
    "air_defense",
    "naval",
]
UNIT_STATUSES: list[str] = ["active", "reserve", "embarked", "destroyed"]

# ---------------------------------------------------------------------------
# NUCLEAR SITES — physical hex locations on global map
# Only countries with map-located nuclear programs. Others are abstract.
# Canonical source: sim_templates.map_config.nuclear_sites (DB)
# ---------------------------------------------------------------------------
NUCLEAR_SITES: dict[str, tuple[int, int]] = {
    "persia": (7, 13),
    "choson": (3, 18),
}


# ---------------------------------------------------------------------------
# THEATER <-> GLOBAL LINKAGE (canonical mapping, Marat-approved 2026-04-05)
# ---------------------------------------------------------------------------
def global_hex_for_theater_cell(
    theater: str,
    theater_row: int,
    theater_col: int,
    cell_owner: Optional[str],
) -> Optional[tuple[int, int]]:
    """Canonical theater cell -> global hex mapping.

    Returns ``(row, col)`` 1-indexed, or ``None`` if no mapping applies.

    Mapping (Template v1.0):

    Eastern Ereb:
      - owner=sarmatia, rows 1-4   -> (3,12)
      - owner=sarmatia, rows 5+    -> (4,12)
      - owner=ruthenia (any row)   -> (4,11)
      - owner=sea (any)            -> (5,12)

    Mashriq:
      - owner=phrygia              -> (6,11)
      - owner=solaria              -> (7,11)
      - owner=mirage               -> (8,11)
      - owner=persia, rows 1-3     -> (6,12)
      - owner=persia, rows 4-6     -> (7,13)
      - owner=persia, rows 7-10    -> (8,13)
      - owner=sea, rows 3-6        -> (7,12)
      - owner=sea, rows 7-10       -> (8,12)
    """
    if cell_owner is None:
        return None

    if theater == "eastern_ereb":
        if cell_owner == "sea":
            return (5, 12)
        if cell_owner == "sarmatia":
            return (3, 12) if theater_row <= 4 else (4, 12)
        if cell_owner == "ruthenia":
            return (4, 11)
        return None

    if theater == "mashriq":
        if cell_owner == "phrygia":
            return (6, 11)
        if cell_owner == "solaria":
            return (7, 11)
        if cell_owner == "mirage":
            return (8, 11)
        if cell_owner == "persia":
            if theater_row <= 3:
                return (6, 12)
            if theater_row <= 6:
                return (7, 13)
            return (8, 13)
        if cell_owner == "sea":
            if 3 <= theater_row <= 6:
                return (7, 12)
            if 7 <= theater_row <= 10:
                return (8, 12)
            return None
        return None

    return None


# ---------------------------------------------------------------------------
# Static list of global hexes that carry a theater link.
# Derived from the canonical mapping above. Manually enumerated to avoid
# needing theater-grid data at import time.
# ---------------------------------------------------------------------------
_THEATER_LINK_HEXES: dict[tuple[int, int], str] = {
    # Eastern Ereb
    (3, 12): "eastern_ereb",
    (4, 12): "eastern_ereb",
    (4, 11): "eastern_ereb",
    (5, 12): "eastern_ereb",
    # Mashriq
    (6, 11): "mashriq",
    (7, 11): "mashriq",
    (8, 11): "mashriq",
    (6, 12): "mashriq",
    (7, 13): "mashriq",
    (8, 13): "mashriq",
    (7, 12): "mashriq",
    (8, 12): "mashriq",
}


def theater_link_hexes() -> dict[tuple[int, int], str]:
    """Return ``{(row, col): theater_name}`` for all global hexes that link
    to a theater. 1-indexed coordinates. Copy is returned to prevent mutation.
    """
    return dict(_THEATER_LINK_HEXES)


def is_theater_link_hex(row: int, col: int) -> bool:
    """True if this global hex has a theater map attached."""
    return (row, col) in _THEATER_LINK_HEXES


def theater_for_global_hex(row: int, col: int) -> Optional[str]:
    """Return the theater name linked to this global hex, or None."""
    return _THEATER_LINK_HEXES.get((row, col))


# ---------------------------------------------------------------------------
# BOUNDS HELPERS
# ---------------------------------------------------------------------------
def in_global_bounds(row: int, col: int) -> bool:
    """True if (row, col) is within the 1-indexed global map bounds."""
    return 1 <= row <= GLOBAL_ROWS and 1 <= col <= GLOBAL_COLS


def in_theater_bounds(theater: str, row: int, col: int) -> bool:
    """True if (row, col) is within the 1-indexed bounds of ``theater``."""
    t = THEATERS.get(theater)
    if not t:
        return False
    return 1 <= row <= t["rows"] and 1 <= col <= t["cols"]


def hex_range(
    row: int, col: int, distance: int,
    max_rows: int = GLOBAL_ROWS, max_cols: int = GLOBAL_COLS,
) -> list[tuple[int, int]]:
    """Return all hexes within ``distance`` steps of (row, col), excluding origin.

    BFS expansion using hex adjacency.  1-indexed coordinates.
    """
    if distance <= 0:
        return []
    visited: set[tuple[int, int]] = {(row, col)}
    frontier: set[tuple[int, int]] = {(row, col)}
    for _ in range(distance):
        next_ring: set[tuple[int, int]] = set()
        for r, c in frontier:
            for nr, nc in hex_neighbors_bounded(r, c, max_rows, max_cols):
                if (nr, nc) not in visited:
                    next_ring.add((nr, nc))
                    visited.add((nr, nc))
        frontier = next_ring
    visited.discard((row, col))  # exclude origin
    return sorted(visited)


# ---------------------------------------------------------------------------
# COMBAT RANGE RULES (per action contracts)
# ---------------------------------------------------------------------------
ATTACK_RANGE: dict[str, int] = {
    "ground": 1,              # adjacent only
    "tactical_air": 2,        # ≤2 hex Manhattan
    "naval": 1,               # same or adjacent sea hex
    "naval_bombardment": 1,   # adjacent sea→land
    "strategic_missile": 99,  # global (effectively unlimited)
}


__all__ = [
    "MAP_CONFIG_VERSION",
    "HEX_TYPE",
    "HEX_OFFSET",
    "hex_neighbors",
    "hex_neighbors_bounded",
    "hex_range",
    "GLOBAL_ROWS",
    "GLOBAL_COLS",
    "THEATERS",
    "THEATER_NAMES",
    "COUNTRY_CODES",
    "UNIT_TYPES",
    "UNIT_STATUSES",
    "NUCLEAR_SITES",
    "ATTACK_RANGE",
    "global_hex_for_theater_cell",
    "theater_link_hexes",
    "is_theater_link_hex",
    "theater_for_global_hex",
    "in_global_bounds",
    "in_theater_bounds",
]
