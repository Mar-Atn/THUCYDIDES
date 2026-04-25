"""Movement data loaders — CONTRACT_MOVEMENT v1.0 §5.

Helpers that build the context dicts the validator + engine require:

- ``load_global_grid_zones`` — synthesizes a per-hex zones dict from the
  SEED canonical global map JSON. Each global hex becomes a synthetic
  zone-record keyed by ``(global_row, global_col)`` with ``owner``,
  ``controlled_by``, ``type`` ('sea' or 'land'), ``theater``,
  ``is_chokepoint``, and ``die_hard``. The validator already supports
  this shape (see _is_sea_hex / _zone_at).

- ``load_basing_rights`` — reads ``relationships.basing_rights_a_to_b`` /
  ``basing_rights_b_to_a`` for the active sim_run and returns
  ``{country_code: set[host_country_code]}``.

- ``build_units_dict_from_rows`` — converts raw ``unit_states_per_round``
  rows into the dict shape the validator/engine expect.

The global grid is cached at module level (immutable across the run).
"""
from __future__ import annotations

import json
import logging
import os
from typing import Optional

from engine.config.map_config import theater_for_global_hex

logger = logging.getLogger(__name__)

# Cache for the synthesized global-hex zones dict.
_GLOBAL_GRID_ZONES_CACHE: Optional[dict[tuple[int, int], dict]] = None

# Path to SEED canonical map (matches test-interface/server.py)
_REPO_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
_SEED_GLOBAL_MAP = os.path.join(
    _REPO_ROOT, "2 SEED", "C_MECHANICS", "C1_MAP",
    "SEED_C1_MAP_GLOBAL_STATE_v4.json",
)


def _load_seed_global_grid() -> dict:
    """Load and parse the canonical SEED global-map JSON."""
    if not os.path.exists(_SEED_GLOBAL_MAP):
        logger.warning("SEED global map missing: %s", _SEED_GLOBAL_MAP)
        return {}
    with open(_SEED_GLOBAL_MAP) as f:
        return json.load(f)


def load_global_grid_zones() -> dict[tuple[int, int], dict]:
    """Return a per-hex zones dict keyed by ``(row, col)`` (1-indexed).

    Each value has the shape the validator expects:
        {id, global_row, global_col, owner, controlled_by, type,
         theater, is_chokepoint, die_hard}

    PRIMARY SOURCE: GLOBAL_HEX_OWNERS from map_config.py (always available,
    works on Railway where SEED files don't exist).
    OPTIONAL: SEED JSON for chokepoints/die-hards metadata.

    Cached after first call.
    """
    global _GLOBAL_GRID_ZONES_CACHE
    if _GLOBAL_GRID_ZONES_CACHE is not None:
        return _GLOBAL_GRID_ZONES_CACHE

    from engine.config.map_config import GLOBAL_HEX_OWNERS, GLOBAL_ROWS, GLOBAL_COLS

    # Optional: load chokepoints/die-hards from SEED JSON (may not exist on Railway)
    chokepoint_set: set[tuple[int, int]] = set()
    die_hard_set: set[tuple[int, int]] = set()
    if os.path.exists(_SEED_GLOBAL_MAP):
        data = _load_seed_global_grid()
        for cp in (data.get("chokepoints") or {}).values():
            if isinstance(cp, dict) and "row" in cp and "col" in cp:
                chokepoint_set.add((cp["row"], cp["col"]))
        die_hards_raw = data.get("dieHards") or {}
        dh_list = die_hards_raw.values() if isinstance(die_hards_raw, dict) else die_hards_raw if isinstance(die_hards_raw, list) else []
        for dh in dh_list:
            if isinstance(dh, dict) and "row" in dh and "col" in dh:
                die_hard_set.add((dh["row"], dh["col"]))

    # Build zones from GLOBAL_HEX_OWNERS (canonical, always available)
    out: dict[tuple[int, int], dict] = {}
    for r in range(1, GLOBAL_ROWS + 1):
        for c in range(1, GLOBAL_COLS + 1):
            owner = GLOBAL_HEX_OWNERS.get((r, c), "sea")
            ztype = "sea" if owner == "sea" else "land"
            out[(r, c)] = {
                "id": f"{owner}_{r}_{c}",
                "global_row": r,
                "global_col": c,
                "owner": owner,
                "controlled_by": owner,
                "type": ztype,
                "theater": theater_for_global_hex(r, c),
                "is_chokepoint": (r, c) in chokepoint_set,
                "die_hard": (r, c) in die_hard_set,
            }

    _GLOBAL_GRID_ZONES_CACHE = out
    logger.info("Loaded %d global grid zones (from GLOBAL_HEX_OWNERS)", len(out))
    return out


def load_basing_rights(client, sim_run_id: str | None = None) -> dict[str, set[str]]:
    """Build ``{country_code: set[host_country_code]}`` from relationships table.

    A row ``(from=A, to=B, basing_rights_a_to_b=true)`` means A has basing
    rights from B's territory (i.e., A may deploy to B's zones). Likewise
    ``basing_rights_b_to_a`` reverses the direction.
    """
    out: dict[str, set[str]] = {}
    try:
        query = client.table("relationships").select(
            "from_country_code, to_country_code, "
            "basing_rights_a_to_b, basing_rights_b_to_a"
        )
        if sim_run_id:
            query = query.eq("sim_run_id", sim_run_id)
        res = query.execute()
        for row in (res.data or []):
            a = row.get("from_country_code")
            b = row.get("to_country_code")
            if not a or not b:
                continue
            # NOTE: schema reading per existing resolve_round basing_rights
            # handler — basing_rights_a_to_b means A→B grants A access to B's
            # land. We follow that convention here.
            if row.get("basing_rights_a_to_b"):
                out.setdefault(a, set()).add(b)
            if row.get("basing_rights_b_to_a"):
                out.setdefault(b, set()).add(a)
    except Exception as e:
        logger.warning("basing rights load failed: %s", e)
    return out


def build_units_dict_from_rows(rows: list[dict]) -> dict[str, dict]:
    """Convert raw unit_states_per_round rows into the validator dict shape."""
    out: dict[str, dict] = {}
    for row in rows:
        uc = row.get("unit_code")
        if not uc:
            continue
        out[uc] = {
            "unit_code": uc,
            "country_code": row.get("country_code"),
            "unit_type": row.get("unit_type"),
            "status": row.get("status"),
            "global_row": row.get("global_row"),
            "global_col": row.get("global_col"),
            "theater": row.get("theater"),
            "theater_row": row.get("theater_row"),
            "theater_col": row.get("theater_col"),
            "embarked_on": row.get("embarked_on"),
        }
    return out


__all__ = [
    "load_global_grid_zones",
    "load_basing_rights",
    "build_units_dict_from_rows",
]
