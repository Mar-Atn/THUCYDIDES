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


def hex_distance(r1: int, c1: int, r2: int, c2: int) -> int:
    """Hex distance on pointy-top odd-r offset grid (1-indexed).

    Converts to cube coordinates then uses standard hex distance formula.
    """
    def _to_cube(row: int, col: int) -> tuple[int, int, int]:
        is_odd_row_0idx = ((row - 1) % 2) == 1
        x = (col - 1) - ((row - 1) - (1 if is_odd_row_0idx else 0)) // 2
        z = row - 1
        y = -x - z
        return (x, y, z)
    a = _to_cube(r1, c1)
    b = _to_cube(r2, c2)
    return (abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])) // 2


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
# SEA HEXES — 1-indexed coordinates of water hexes (ground cannot enter)
# ---------------------------------------------------------------------------
GLOBAL_SEA_HEXES: frozenset[tuple[int, int]] = frozenset([
    (1,1),(1,2),(1,3),(1,4),(1,5),(1,6),(1,7),(1,8),(1,9),(1,10),(1,11),(1,12),(1,13),(1,14),(1,15),(1,16),(1,17),(1,18),(1,19),(1,20),
    (2,1),(2,2),(2,3),(2,4),(2,5),(2,6),(2,7),(2,8),(2,9),(2,13),(2,14),(2,15),(2,17),(2,18),(2,19),(2,20),
    (3,1),(3,2),(3,4),(3,5),(3,7),(3,9),(3,17),(3,19),(3,20),
    (4,1),(4,4),(4,5),(4,6),(4,8),(4,15),(4,18),(4,20),
    (5,1),(5,2),(5,6),(5,7),(5,8),(5,12),(5,13),(5,18),(5,20),
    (6,1),(6,2),(6,5),(6,6),(6,7),(6,9),(6,17),(6,18),(6,19),(6,20),
    (7,1),(7,2),(7,3),(7,5),(7,6),(7,7),(7,8),(7,10),(7,12),(7,17),(7,19),(7,20),
    (8,1),(8,2),(8,3),(8,4),(8,5),(8,6),(8,7),(8,8),(8,9),(8,12),(8,16),(8,17),(8,18),(8,19),(8,20),
    (9,1),(9,2),(9,3),(9,4),(9,6),(9,7),(9,8),(9,9),(9,11),(9,12),(9,13),(9,14),(9,16),(9,17),(9,18),(9,19),(9,20),
    (10,1),(10,2),(10,3),(10,4),(10,5),(10,6),(10,7),(10,8),(10,9),(10,10),(10,11),(10,12),(10,13),(10,14),(10,15),(10,16),(10,17),(10,18),(10,19),(10,20),
])

THEATER_SEA_HEXES: dict[str, frozenset[tuple[int, int]]] = {
    "eastern_ereb": frozenset([
        (8,4),(8,6),(8,7),(8,8),(9,4),(9,7),(9,8),(9,9),(9,10),
        (10,3),(10,4),(10,5),(10,6),(10,7),(10,8),(10,9),(10,10),
    ]),
    "mashriq": frozenset([
        (3,2),(3,3),(4,2),(4,3),(5,2),(5,3),(5,4),(5,5),(6,2),(6,3),(6,4),(6,5),
        (7,2),(7,3),(7,4),(7,5),(7,6),(8,2),(8,3),(8,4),(8,5),(8,7),
        (9,4),(9,5),(9,6),(9,7),(9,8),(10,6),(10,7),(10,8),
    ]),
}


def is_sea_hex(row: int, col: int, theater: Optional[str] = None) -> bool:
    """True if the hex is a sea hex (ground cannot enter)."""
    if theater:
        return (row, col) in THEATER_SEA_HEXES.get(theater, frozenset())
    return (row, col) in GLOBAL_SEA_HEXES


# ---------------------------------------------------------------------------
# HEX OWNERS — canonical territory ownership (from map grid data)
# ---------------------------------------------------------------------------
GLOBAL_HEX_OWNERS: dict[tuple[int, int], str] = {
    (2,10):"freeland",(2,11):"sarmatia",(2,12):"sarmatia",(2,16):"sarmatia",
    (3,3):"columbia",(3,6):"thule",(3,8):"albion",(3,10):"freeland",
    (3,11):"ruthenia",(3,12):"sarmatia",(3,13):"sarmatia",(3,14):"sarmatia",
    (3,15):"sarmatia",(3,16):"sarmatia",(3,18):"choson",
    (4,2):"columbia",(4,3):"columbia",(4,7):"albion",(4,9):"teutonia",
    (4,10):"teutonia",(4,11):"ruthenia",(4,12):"sarmatia",(4,13):"sarmatia",
    (4,14):"sarmatia",(4,16):"sarmatia",(4,17):"hanguk",(4,19):"yamato",
    (5,3):"columbia",(5,4):"columbia",(5,5):"columbia",(5,9):"gallia",
    (5,10):"gallia",(5,11):"phrygia",(5,14):"sogdiana",(5,15):"cathay",
    (5,16):"cathay",(5,17):"cathay",(5,19):"yamato",
    (6,3):"columbia",(6,4):"columbia",(6,8):"ponte",(6,10):"levantia",
    (6,11):"phrygia",(6,12):"persia",(6,13):"sogdiana",(6,14):"sogdiana",
    (6,15):"cathay",(6,16):"cathay",
    (7,4):"columbia",(7,9):"ponte",(7,11):"solaria",(7,13):"persia",
    (7,14):"bharata",(7,15):"bharata",(7,16):"cathay",(7,18):"formosa",
    (8,10):"solaria",(8,11):"mirage",(8,13):"persia",(8,14):"bharata",
    (8,15):"bharata",
    (9,5):"caribe",(9,10):"horn",(9,15):"bharata",
}


def hex_owner(row: int, col: int) -> str:
    """Return the canonical territory owner for a global hex, or 'sea'."""
    return GLOBAL_HEX_OWNERS.get((row, col), "sea")

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
# CHOKEPOINTS — naval blockade locations on global map
# ---------------------------------------------------------------------------
CHOKEPOINTS: dict[str, dict] = {
    "cp_caribe": {"hex": (8, 4), "name": "Caribe Passage", "ground_ok": False},
    "cp_gulf_gate": {"hex": (8, 12), "name": "Gulf Gate", "ground_ok": True},
    "cp_formosa": {"hex": (7, 17), "name": "Formosa Strait", "ground_ok": False},
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
    "strategic_missile": 2,   # default T1 — use missile_range() for tier-aware range
}

# Missile range per tier (derived from country nuclear_level)
MISSILE_RANGE_BY_TIER: dict[str, int] = {
    "T1": 2,     # nuclear_level 0-1
    "T2": 4,     # nuclear_level 2-3
    "T3": 99,    # nuclear_level 4+ (global)
}


def missile_range(nuclear_level: int) -> int:
    """Return missile range based on country's nuclear technology level.

    T1 (level 0-1): ≤2 hexes
    T2 (level 2):   ≤4 hexes
    T3 (level 3+):  global
    """
    if nuclear_level >= 3:
        return MISSILE_RANGE_BY_TIER["T3"]
    if nuclear_level >= 2:
        return MISSILE_RANGE_BY_TIER["T2"]
    return MISSILE_RANGE_BY_TIER["T1"]


__all__ = [
    "MAP_CONFIG_VERSION",
    "HEX_TYPE",
    "HEX_OFFSET",
    "hex_distance",
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
    "CHOKEPOINTS",
    "ATTACK_RANGE",
    "global_hex_for_theater_cell",
    "theater_link_hexes",
    "is_theater_link_hex",
    "theater_for_global_hex",
    "in_global_bounds",
    "in_theater_bounds",
    "GLOBAL_SEA_HEXES",
    "THEATER_SEA_HEXES",
    "is_sea_hex",
]
