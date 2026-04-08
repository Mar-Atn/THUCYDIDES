# DET — Unit Data Model (Engineering Spec)

**Version:** 1.0 | **Status:** Draft | **Date:** 2026-04-05
**Promoted from:** `SEED_D_UNIT_DATA_MODEL_v1.md` (companion SEED doc)
**Related:** `CONCEPT TEST/db_schema_v1.sql`, `2 SEED/C_MECHANICS/C4_DATA/units.csv`

---

## 1. Purpose

Engineering contract for the **unit** entity across the four representations it lives in:

1. **CSV** — `2 SEED/C_MECHANICS/C4_DATA/units.csv` (authoring + version control)
2. **Python (Pydantic)** — engines, orchestrator, map_context
3. **JS/TypeScript** — test-interface editor, frontend renderers
4. **SQL** — `CONCEPT TEST/db_schema_v1.sql` (persistence)

Any change to the unit schema must be applied in **all four** representations in the same commit, or the system is out of integrity (Principle Zero).

---

## 2. Schema authority

The authoritative column list, types, and invariants are defined in this document.

| Representation | Location | Role |
|---|---|---|
| CSV header | `units.csv` row 1 | Canonical field order |
| Pydantic model | `app/engine/models/unit.py` (to be created) | Python type + validators |
| TS type | `app/frontend/src/types/unit.ts` (to be created) | JS type |
| SQL DDL | `CONCEPT TEST/db_schema_v1.sql` table `units` | DB persistence |

---

## 3. Pydantic model (Python)

```python
from typing import Literal, Optional
from pydantic import BaseModel, Field, model_validator

UnitType = Literal["ground", "tactical_air", "strategic_missile", "air_defense", "naval"]
UnitStatus = Literal["active", "reserve", "embarked", "destroyed"]
TheaterCode = Literal["", "eastern_ereb", "mashriq"]  # "" = no theater


class Unit(BaseModel):
    unit_id: str                                # natural key, e.g. 'col_g_01'
    country_id: str                             # country code, e.g. 'columbia'
    unit_type: UnitType
    global_row: Optional[int] = Field(None, ge=1, le=10)
    global_col: Optional[int] = Field(None, ge=1, le=20)
    theater: TheaterCode = ""
    theater_row: Optional[int] = Field(None, ge=1, le=10)
    theater_col: Optional[int] = Field(None, ge=1, le=10)
    embarked_on: str = ""                       # unit_id of carrier or ""
    status: UnitStatus
    notes: str = ""

    @model_validator(mode="after")
    def _check_invariants(self) -> "Unit":
        # I1: active ⇒ global coords set
        if self.status == "active":
            if self.global_row is None or self.global_col is None:
                raise ValueError(f"{self.unit_id}: active unit needs global coords")
        # I2: reserve ⇒ no coords, no carrier
        if self.status == "reserve":
            if any([self.global_row, self.global_col, self.theater_row,
                    self.theater_col, self.embarked_on, self.theater]):
                raise ValueError(f"{self.unit_id}: reserve unit must have no coords/carrier")
        # I3: embarked ⇒ has carrier, no coords
        if self.status == "embarked":
            if not self.embarked_on:
                raise ValueError(f"{self.unit_id}: embarked unit needs embarked_on")
        # I4: theater all-or-nothing
        theater_set = bool(self.theater)
        cell_set = self.theater_row is not None and self.theater_col is not None
        if theater_set != cell_set:
            raise ValueError(f"{self.unit_id}: theater fields must be all-or-nothing")
        return self
```

---

## 4. TypeScript type

```typescript
export type UnitType =
  | "ground" | "tactical_air" | "strategic_missile"
  | "air_defense" | "naval";

export type UnitStatus = "active" | "reserve" | "embarked" | "destroyed";
export type TheaterCode = "" | "eastern_ereb" | "mashriq";

export interface Unit {
  unit_id: string;
  country_id: string;
  unit_type: UnitType;
  global_row: number | null;    // 1..10
  global_col: number | null;    // 1..20
  theater: TheaterCode;
  theater_row: number | null;   // 1..10
  theater_col: number | null;   // 1..10
  embarked_on: string;          // "" or carrier unit_id
  status: UnitStatus;
  notes: string;
}
```

---

## 5. SQL column mapping

| CSV / Pydantic / TS | SQL column (`units` table) | Notes |
|---|---|---|
| `unit_id` | `unit_code TEXT` | Natural key |
| `country_id` | `country_code TEXT` (FK countries.code) | |
| `unit_type` | `unit_type TEXT` | CHECK enum |
| `global_row` | `global_row INT` | 1..10 |
| `global_col` | `global_col INT` | 1..20 |
| `theater` | `theater_code TEXT` (FK theaters.code, nullable) | "" ⇔ NULL |
| `theater_row` | `theater_row INT` | 1..10 |
| `theater_col` | `theater_col INT` | 1..10 |
| `embarked_on` | `embarked_on_unit_id UUID` | "" ⇔ NULL (resolved via lookup on unit_code) |
| `status` | `status TEXT` | CHECK enum |
| `notes` | `notes TEXT` | |

DB also carries `id UUID`, `scenario_id`, `template_id`, `created_at` which are not present in the CSV schema — they are scope/identity columns set at import time.

---

## 6. Invariants (must hold across all representations)

| # | Invariant |
|---|---|
| I1 | `status == "active"` ⇒ `global_row` and `global_col` both set |
| I2 | `status == "reserve"` ⇒ no coord fields set, `embarked_on == ""`, `theater == ""` |
| I3 | `status == "embarked"` ⇒ `embarked_on` non-empty and references an existing naval unit_id, no coord fields set |
| I4 | Theater fields are all-or-nothing: `theater`, `theater_row`, `theater_col` set together or not at all |
| I5 | If `theater` is set, `(global_row, global_col)` must match one of that theater's link hexes per `theater_global_links` |
| I6 | Theater cells ∈ [1,10] × [1,10]; global cells ∈ [1,10] × [1,20] |
| I7 | `unit_id` unique within the containing scope (template default OR scenario) |
| I8 | `country_id` references a row in countries.csv / `countries` table |
| I9 | `unit_type` ∈ {ground, tactical_air, strategic_missile, air_defense, naval} |
| I10 | A unit cannot be embarked on itself |

---

## 7. Status state machine

```
  reserve ──activate──► active ──embark──► embarked
     ▲                    │                  │
     │                    │                  │
     └────demobilize──────┤                  │
                          │                  │
                          ▼                  │
                       destroyed ◄──sunk─────┘
```

Allowed transitions:
- `reserve → active` (deploy)
- `active → reserve` (demobilize; clears coords)
- `active → embarked` (board a naval carrier; clears coords, sets embarked_on)
- `embarked → active` (debark; restores coords from carrier's current position)
- `active → destroyed` (combat loss)
- `embarked → destroyed` (carrier sunk; cascade rule TBD)

Forbidden: `destroyed → *`, `reserve → embarked` (must activate first).

---

## 8. Movement / placement contracts

### 8.1 From the editor (test-interface map.js)
- Pick up: coord fields set to null, status may become `reserve` or stay `active` depending on target.
- Place on global hex: set `global_row`, `global_col`; if hex is a theater-link, set theater + theater cell.
- Place on theater cell: set `theater`, `theater_row`, `theater_col`, derive `global_row`/`global_col` via `theater_global_links` lookup.
- Embark: set `status='embarked'`, `embarked_on=<naval unit_id>`, clear all coord fields.

### 8.2 From AI agents (engine)
- Agents must call a validation library function before committing a movement order.
- Movement orders reference source and target as either (global_row, global_col) OR (theater_code, theater_row, theater_col). The engine resolves both and enforces invariant I5.

---

## 9. Aggregation functions

Required public functions (Python: `app/engine/agents/map_context.py`):

| Function | Signature | Purpose |
|---|---|---|
| `load_units` | `(path) -> list[Unit]` | Parse units.csv into Pydantic models |
| `units_by_global_hex` | `(units) -> dict[(row,col), list[Unit]]` | For global map renderer |
| `units_by_theater_cell` | `(units, theater) -> dict[(row,col), list[Unit]]` | For theater drill-down |
| `units_by_country` | `(units) -> dict[country_code, list[Unit]]` | For country summaries |
| `units_on_carrier` | `(units, carrier_id) -> list[Unit]` | Embarked-on-this-ship list |

JS equivalents live in `app/test-interface/static/map.js` (or the future frontend unit service) and must return identically shaped data.

---

## 10. Validation library

Required public functions (Python: `app/engine/services/unit_validator.py` — to be created):

```python
def validate_unit(u: Unit) -> list[str]: ...
    # Returns list of violated invariant IDs, empty list if valid.

def validate_unit_set(units: list[Unit],
                      template: SimTemplate) -> list[ValidationError]: ...
    # Cross-unit checks:
    #   - unit_id uniqueness
    #   - embarked_on resolves to an existing naval unit in the same set
    #   - theater cell matches one of template's theater_global_links
    #   - country_id exists in template's countries

def validate_placement(u: Unit,
                       target_hex: tuple[int,int],
                       world_state: WorldState) -> list[str]: ...
    # Rules derived from CHANGES_LOG (Pending/To Do):
    #   - no Sarmatian troops on free Ruthenia (ruthenia_1)
    #   - no Columbia troops on Persian soil (persia_*/t_persia_*)
    #   - ground units cannot be placed on sea cells
    #   - naval units can only be placed on sea cells
```

---

## 11. Open issues / TBD

- Cascade rule when a naval carrier is destroyed: embarked units → destroyed, or → reserve?
- `damaged` status was present in early docs but dropped from the enum; confirm never re-introduce without a schema bump.
- `notes` field: cap length? currently unbounded TEXT.
- Scenario-level delta representation (full snapshot vs delta on top of template default) — decide before sprint 3.
