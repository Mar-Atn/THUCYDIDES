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
MAP_CONFIG_VERSION = "1.0"  # Template v1.0 — 2026-04-05

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


__all__ = [
    "MAP_CONFIG_VERSION",
    "GLOBAL_ROWS",
    "GLOBAL_COLS",
    "THEATERS",
    "THEATER_NAMES",
    "COUNTRY_CODES",
    "UNIT_TYPES",
    "UNIT_STATUSES",
    "NUCLEAR_SITES",
    "global_hex_for_theater_cell",
    "theater_link_hexes",
    "is_theater_link_hex",
    "theater_for_global_hex",
    "in_global_bounds",
    "in_theater_bounds",
]
