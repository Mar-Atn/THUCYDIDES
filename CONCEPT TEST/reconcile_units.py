#!/usr/bin/env python3
"""Units.csv reconciliation pass.

Validates `2 SEED/C_MECHANICS/C4_DATA/units.csv` against:
- the canonical schema (valid fields, valid types/statuses)
- the canonical theater <-> global mapping (map_config)
- the global map JSON (sea hex check)
- the theater map JSONs (self-occupation check)
- countries.csv mil_* expected counts

Run:
    cd app && PYTHONPATH=. python3 ../CONCEPT\\ TEST/reconcile_units.py

Writes a report to stdout. Non-zero exit if any HARD failure.
"""
from __future__ import annotations

import csv
import json
import os
import sys
from collections import defaultdict
from typing import Any, Optional

# --- Path to engine config ----------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, ".."))
_APP_DIR = os.path.join(_REPO_ROOT, "app")
if _APP_DIR not in sys.path:
    sys.path.insert(0, _APP_DIR)

from engine.config.map_config import (  # noqa: E402
    GLOBAL_ROWS,
    GLOBAL_COLS,
    THEATERS,
    COUNTRY_CODES,
    UNIT_TYPES,
    UNIT_STATUSES,
    global_hex_for_theater_cell,
    is_theater_link_hex,
    theater_for_global_hex,
    in_global_bounds,
    in_theater_bounds,
)

# --- Paths --------------------------------------------------------------------
_DATA_DIR = os.path.join(_REPO_ROOT, "2 SEED", "C_MECHANICS", "C4_DATA")
_MAP_DIR = os.path.join(_REPO_ROOT, "2 SEED", "C_MECHANICS", "C1_MAP")
UNITS_CSV = os.path.join(_DATA_DIR, "units.csv")
COUNTRIES_CSV = os.path.join(_DATA_DIR, "countries.csv")
GLOBAL_MAP_JSON = os.path.join(_MAP_DIR, "SEED_C1_MAP_GLOBAL_STATE_v4.json")
EE_MAP_JSON = os.path.join(_MAP_DIR, "SEED_C3_THEATER_EASTERN_EREB_STATE_v3.json")
MQ_MAP_JSON = os.path.join(_MAP_DIR, "SEED_C3_THEATER_MASHRIQ_STATE_v1.json")


# --- Helpers ------------------------------------------------------------------
def _to_int(s: Any) -> Optional[int]:
    try:
        v = str(s).strip()
        if not v:
            return None
        return int(v)
    except (ValueError, TypeError):
        return None


def _load_json(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def _global_owner(gmap: dict, row1: int, col1: int) -> Optional[str]:
    if not in_global_bounds(row1, col1):
        return None
    return gmap["grid"][row1 - 1][col1 - 1].get("owner")


def _theater_cell(tmap: dict, row1: int, col1: int) -> Optional[dict]:
    if row1 < 1 or col1 < 1 or row1 > tmap["rows"] or col1 > tmap["cols"]:
        return None
    return tmap["grid"][row1 - 1][col1 - 1]


# --- Checks -------------------------------------------------------------------
def check_self_occupation(name: str, tmap: dict) -> list[str]:
    findings: list[str] = []
    for r in range(tmap["rows"]):
        for c in range(tmap["cols"]):
            cell = tmap["grid"][r][c]
            owner = cell.get("owner")
            occ = cell.get("occupied_by")
            if owner and occ and owner == occ:
                findings.append(
                    f"  {name} theater cell ({r+1},{c+1}): owner=occupied_by={owner}"
                )
    return findings


def load_units() -> list[dict]:
    units: list[dict] = []
    with open(UNITS_CSV) as f:
        for row in csv.DictReader(f):
            unit_id = (row.get("unit_id") or "").strip()
            if not unit_id:
                continue
            units.append({
                "unit_id": unit_id,
                "country_id": (row.get("country_id") or "").strip(),
                "unit_type": (row.get("unit_type") or "").strip(),
                "global_row": _to_int(row.get("global_row")),
                "global_col": _to_int(row.get("global_col")),
                "theater": (row.get("theater") or "").strip() or None,
                "theater_row": _to_int(row.get("theater_row")),
                "theater_col": _to_int(row.get("theater_col")),
                "embarked_on": (row.get("embarked_on") or "").strip() or None,
                "status": (row.get("status") or "active").strip(),
                "notes": (row.get("notes") or "").strip(),
            })
    return units


def load_countries() -> dict[str, dict]:
    out: dict[str, dict] = {}
    with open(COUNTRIES_CSV) as f:
        for row in csv.DictReader(f):
            cid = (row.get("id") or "").strip()
            if cid:
                out[cid] = row
    return out


def main() -> int:
    units = load_units()
    countries = load_countries()
    gmap = _load_json(GLOBAL_MAP_JSON)
    ee = _load_json(EE_MAP_JSON)
    mq = _load_json(MQ_MAP_JSON)
    theater_maps = {"eastern_ereb": ee, "mashriq": mq}

    total = len(units)
    errors: list[str] = []   # hard validation failures
    warnings: list[str] = [] # soft / flagged items
    unit_ids: set[str] = set()
    naval_by_country: dict[str, set[str]] = defaultdict(set)

    # Pre-index naval unit ids per country
    for u in units:
        if u["unit_type"] == "naval":
            naval_by_country[u["country_id"]].add(u["unit_id"])

    for u in units:
        uid = u["unit_id"]
        # 1. basic fields
        if uid in unit_ids:
            errors.append(f"duplicate unit_id: {uid}")
        unit_ids.add(uid)

        if u["country_id"] not in COUNTRY_CODES:
            errors.append(f"{uid}: unknown country_id={u['country_id']!r}")
        if u["unit_type"] not in UNIT_TYPES:
            errors.append(f"{uid}: unknown unit_type={u['unit_type']!r}")
        if u["status"] not in UNIT_STATUSES:
            errors.append(f"{uid}: unknown status={u['status']!r}")

        status = u["status"]
        gr, gc = u["global_row"], u["global_col"]
        th, tr, tc = u["theater"], u["theater_row"], u["theater_col"]

        # 6. reserves must have all coord fields empty
        if status == "reserve":
            if any(v is not None for v in (gr, gc, tr, tc)) or th:
                errors.append(f"{uid}: reserve must have empty coords (got gr={gr},gc={gc},th={th},tr={tr},tc={tc})")
            if u["embarked_on"]:
                errors.append(f"{uid}: reserve cannot be embarked_on={u['embarked_on']}")
            continue

        # embarked units
        if status == "embarked":
            if not u["embarked_on"]:
                errors.append(f"{uid}: embarked but embarked_on is empty")
            else:
                # 5. embarked_on must be valid naval unit of SAME country
                host = u["embarked_on"]
                if host not in naval_by_country.get(u["country_id"], set()):
                    errors.append(
                        f"{uid}: embarked_on={host} is not a valid naval unit of {u['country_id']}"
                    )
            if any(v is not None for v in (gr, gc, tr, tc)) or th:
                warnings.append(f"{uid}: embarked unit has coord fields set (expected empty)")
            continue

        if status == "destroyed":
            # no coord constraints (any)
            continue

        # active units below
        # 2. valid global coords
        if gr is None or gc is None:
            errors.append(f"{uid}: active unit missing global coords")
            continue
        if not in_global_bounds(gr, gc):
            errors.append(f"{uid}: global coords ({gr},{gc}) out of range")
            continue

        # 3. theater link hex -> theater fields required
        link_theater = theater_for_global_hex(gr, gc)
        has_theater_fields = bool(th and tr is not None and tc is not None)

        # 4. if theater is set -> theater coords in range + matches mapping
        if th:
            if th not in THEATERS:
                errors.append(f"{uid}: unknown theater={th!r}")
                continue
            if tr is None or tc is None:
                errors.append(f"{uid}: theater set but theater_row/col empty")
                continue
            if not in_theater_bounds(th, tr, tc):
                errors.append(f"{uid}: theater coords ({tr},{tc}) out of range for {th}")
                continue
            # look up theater cell owner, verify canonical mapping
            tcell = _theater_cell(theater_maps[th], tr, tc)
            if tcell is None:
                errors.append(f"{uid}: theater cell not found {th}/({tr},{tc})")
                continue
            cell_owner = tcell.get("owner")
            expected = global_hex_for_theater_cell(th, tr, tc, cell_owner)
            if expected is None:
                errors.append(
                    f"{uid}: no canonical global mapping for {th}/({tr},{tc}) owner={cell_owner}"
                )
            elif (gr, gc) != expected:
                errors.append(
                    f"{uid}: global ({gr},{gc}) != canonical {expected} "
                    f"for {th}/({tr},{tc}) owner={cell_owner}"
                )
            # 7. ground unit on sea cell (invalid) — flag sarmatia ground on sea
            if u["unit_type"] == "ground" and cell_owner == "sea":
                warnings.append(
                    f"{uid}: GROUND unit on sea cell {th}/({tr},{tc}) (country={u['country_id']})"
                )
        else:
            # no theater fields set
            if link_theater:
                # active unit sits on a theater-link hex but has no theater coords
                warnings.append(
                    f"{uid}: active unit on theater-link hex ({gr},{gc})={link_theater} "
                    f"but no theater fields"
                )

        # 7b. sea-hex check on global (non-theater-placed units only)
        gowner = _global_owner(gmap, gr, gc)
        if gowner == "sea" and u["unit_type"] not in ("naval",) and not th:
            # non-naval unit on a global sea hex with no theater context
            warnings.append(
                f"{uid}: {u['unit_type']} on global sea hex ({gr},{gc}) with no theater"
            )

    # 8. Per-country per-type counts vs countries.csv mil_* columns
    csv_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for u in units:
        # Count active + embarked + reserve; skip destroyed
        if u["status"] == "destroyed":
            continue
        csv_counts[u["country_id"]][u["unit_type"]] += 1

    col_by_type = {
        "ground": "mil_ground",
        "naval": "mil_naval",
        "tactical_air": "mil_tactical_air",
        "strategic_missile": "mil_strategic_missiles",
        "air_defense": "mil_air_defense",
    }
    mismatches: list[str] = []
    for cid in COUNTRY_CODES:
        row = countries.get(cid, {})
        for ut, col in col_by_type.items():
            try:
                expected = int(float(row.get(col, "0") or "0"))
            except (ValueError, TypeError):
                expected = 0
            got = csv_counts.get(cid, {}).get(ut, 0)
            if expected != got:
                mismatches.append(
                    f"  {cid:10s} {ut:20s} expected={expected:3d} units.csv={got:3d} diff={got-expected:+d}"
                )

    # Self-occupation scan (CHANGES_LOG item 2)
    self_occ: list[str] = []
    self_occ.extend(check_self_occupation("eastern_ereb", ee))
    self_occ.extend(check_self_occupation("mashriq", mq))

    # Known flagged Sarmatian ground on sea cells (CHANGES_LOG item 3)
    FLAGGED_SAR_GROUND_SEA = {"sar_g_05", "sar_g_06", "sar_d_02", "sar_m_10"}
    known_seen = {u["unit_id"] for u in units if u["unit_id"] in FLAGGED_SAR_GROUND_SEA}

    # --- Report ---
    print("=" * 70)
    print("UNITS.CSV RECONCILIATION REPORT")
    print(f"  file: {os.path.relpath(UNITS_CSV, _REPO_ROOT)}")
    print(f"  map_config version: 1.0")
    print("=" * 70)
    print(f"Total units rows:       {total}")
    print(f"Hard errors:            {len(errors)}")
    print(f"Warnings / soft flags:  {len(warnings)}")
    print(f"Count mismatches:       {len(mismatches)}")
    print(f"Self-occupation cells:  {len(self_occ)}")
    print()

    if errors:
        print("## HARD ERRORS")
        for e in errors[:200]:
            print(f"  {e}")
        if len(errors) > 200:
            print(f"  ... and {len(errors)-200} more")
        print()

    if warnings:
        print("## WARNINGS / SOFT FLAGS")
        for w in warnings[:200]:
            print(f"  {w}")
        if len(warnings) > 200:
            print(f"  ... and {len(warnings)-200} more")
        print()

    if mismatches:
        print("## COUNT MISMATCHES (countries.csv mil_* vs units.csv)")
        for m in mismatches:
            print(m)
        print()

    if self_occ:
        print("## SELF-OCCUPATION IN THEATER JSONS (per CHANGES_LOG item 2)")
        for s in self_occ:
            print(s)
        print()
    else:
        print("## SELF-OCCUPATION: none detected (clean)")
        print()

    print("## KNOWN FLAGGED UNITS (CHANGES_LOG item 3 — Sarmatian ground on sea)")
    print(f"  Expected: {sorted(FLAGGED_SAR_GROUND_SEA)}")
    print(f"  Found in units.csv: {sorted(known_seen)}")
    print()

    pass_count = total - sum(
        1 for u in units if any(u["unit_id"] in e for e in errors)
    )
    print(f"PASS (no hard error): {pass_count}/{total}")
    print("=" * 70)

    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
