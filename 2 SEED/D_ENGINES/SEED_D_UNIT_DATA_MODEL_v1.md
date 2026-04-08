# SEED D — Unit Data Model

**Version:** 1.0 | **Date:** 2026-04-05 | **Status:** Template v1.0 candidate
**Canonical source:** `2 SEED/C_MECHANICS/SEED_C_MAP_UNITS_MASTER_v1.md`

---

## Purpose

Formal engineering-level specification of the unit record: its schema, invariants, state transitions, validation rules, and `unit_id` convention. This is the contract implemented by `app/engine/agents/map_context.py::load_units()`, the `/api/map/units` endpoints, and the `units.csv` data file.

---

## 1. Schema

| # | Field | Type | Required | Allowed values | Notes |
|:--:|---|---|:--:|---|---|
| 1 | `unit_id` | string | yes | unique, matches `^[a-z]{3}_[gamdn]_(r)?[0-9]+$` | See §5 for convention. |
| 2 | `country_id` | string | yes | must exist in `countries.csv` | Owner. |
| 3 | `unit_type` | enum | yes | `ground` \| `tactical_air` \| `strategic_missile` \| `air_defense` \| `naval` | |
| 4 | `global_row` | int | conditional | 1..10 | Required iff `status=active`. |
| 5 | `global_col` | int | conditional | 1..20 | Required iff `status=active`. |
| 6 | `theater` | enum | conditional | `''` \| `eastern_ereb` \| `mashriq` | See invariant I-6. |
| 7 | `theater_row` | int | conditional | 1..10 | Required iff `theater` set. |
| 8 | `theater_col` | int | conditional | 1..10 | Required iff `theater` set. |
| 9 | `embarked_on` | string | conditional | another row's `unit_id` | Required iff `status=embarked`. |
| 10 | `status` | enum | yes | `active` \| `reserve` \| `embarked` \| `destroyed` | |
| 11 | `notes` | string | no | free text | Human description. |

**Storage format:** CSV with header row. Empty string encodes "null" for conditional fields.

---

## 2. Invariants (MUST hold for every row)

- **I-1 Unique id.** `unit_id` is unique across the table.
- **I-2 Active placement.** `status=active` ⇒ `global_row` AND `global_col` set and in-bounds.
- **I-3 Reserve cleared.** `status=reserve` ⇒ `global_row`, `global_col`, `theater`, `theater_row`, `theater_col`, `embarked_on` ALL empty.
- **I-4 Embarked cleared + linked.** `status=embarked` ⇒ coord fields empty AND `embarked_on` references a row whose `unit_type=naval` AND that carrier has matching `country_id`.
- **I-5 Destroyed terminal.** `status=destroyed` ⇒ terminal state, kept only for audit. Coord fields MAY be empty or frozen at the final position; runtime queries ignore destroyed units.
- **I-6 Theater consistency.** If `theater` is non-empty, then `theater_row` AND `theater_col` set AND the unit's `(global_row, global_col)` must equal the canonical mapping of its theater cell (per `SEED_C_MAP_UNITS_MASTER_v1.md` §1.5). Conversely, a non-naval active unit whose `(global_row, global_col)` is a theater-link hex MUST carry a theater cell.
- **I-7 Naval on water.** `unit_type=naval` AND `status=active` ⇒ `(global_row, global_col)` is a water hex. Naval units never carry theater coords.
- **I-8 Land-type on land or ship.** `unit_type ∈ {ground, tactical_air, strategic_missile, air_defense}` ⇒ either on a land hex, or `status=embarked`.
- **I-9 Bounded coords.** global_row ∈ [1,10], global_col ∈ [1,20], theater_row ∈ [1,10], theater_col ∈ [1,10] whenever set.
- **I-10 No self-embark.** `embarked_on ≠ unit_id`.

---

## 3. State Transitions

```
                 ┌───────────┐
    place ───►   │   active  │   ◄─── disembark
   ┌─────────    └─┬───┬─────┘
   │               │   │
┌──┴──────┐   pick-up   board-ship
│ reserve │   (back)      │
└──▲──────┘       │       ▼
   │              │   ┌──────────┐
   └──────────────┤   │ embarked │
                  │   └────┬─────┘
                  │        │
                  ▼        ▼
              ┌─────────────────┐
              │    destroyed    │   (terminal, audit only)
              └─────────────────┘
```

| From | To | Trigger | Field updates |
|---|---|---|---|
| reserve | active | place on hex | set global_row/col (+theater if applicable) |
| active | reserve | pick up | clear global_row/col, theater, theater_row/col |
| active | embarked | board own-country ship | clear coord fields, set `embarked_on` |
| embarked | active | disembark to adjacent hex | clear `embarked_on`, set global_row/col (+theater) |
| active | destroyed | combat loss | set `status=destroyed`; position may be frozen for audit |
| reserve | destroyed | decommission | set `status=destroyed` |
| embarked | destroyed | carrier sunk with embarked units | set `status=destroyed` on embarked units |

`destroyed` is terminal. No transition out.

---

## 4. Validation Rules

### 4.1 Hard blocks (reject write)

- Any breach of invariants I-1 through I-10.
- `unit_type=naval` attempted placement on a land hex.
- `unit_type ∈ {ground, tactical_air, strategic_missile, air_defense}` attempted placement on a water hex without `status=embarked`.
- `embarked_on` references a non-existent `unit_id` OR a non-naval carrier OR a different-country carrier.
- Theater mismatch: `(global_row, global_col)` does not correspond to the theater specified.
- Coord out-of-bounds.

### 4.2 Soft warnings (allow write, flag for review)

- Non-native placement: unit's `global_row/col` is in a country whose `country_id ≠ unit.country_id` (cross-country basing).
- Unit on an enemy-occupied theater cell without a friendly ground unit co-located.
- Stacking ≥ 6 units of the same country on one global hex (compact-badge rendering kicks in; gameplay-wise may be intentional, e.g. fortress or reserve depot).
- Ground unit on a theater cell with `owner=sea`.

### 4.3 Data integrity checks (per file load)

On loading `units.csv`:
1. Scan for duplicate `unit_id`.
2. Resolve every `embarked_on` reference.
3. Verify every theater-cell coord combination matches the canonical linkage table.
4. Cross-check per-country totals against `countries.csv` (G/A/M/D/N columns).

---

## 5. `unit_id` Convention

Format: `{country3}_{type1}_{seq}`

- **country3** — 3-letter country prefix: `col`, `cat`, `sar`, `rut`, `per`, `gal`, `teu`, `fre`, `pon`, `alb`, `bha`, `lev`, `for`, `phr`, `yam`, `sol`, `cho`, `han`, `car`, `mir`.
- **type1** — single-letter unit type:
  - `g` = ground
  - `a` = tactical_air
  - `m` = strategic_missile
  - `d` = air_defense (D to avoid clash with "a")
  - `n` = naval
- **seq** — zero-padded sequence number, two digits minimum: `01`, `02`, ... `15`.
- **reserve prefix** (optional) — reserves use `r` before the sequence: `sar_g_r1` = Sarmatia ground reserve #1.

Examples: `col_g_01`, `per_d_03`, `sar_m_r1`, `alb_n_02`.

Sequence is per country per type. Deleting a unit does not renumber survivors; new units take the next free sequence.

---

## 6. Examples

### 6.1 Global-only placement (no theater)

```
col_g_01,columbia,ground,4,3,,,,,active,"CONUS central - Ft Campbell"
```

Active ground unit at global (row=4, col=3). No theater cell because (4,3) is not a theater-link hex.

### 6.2 Theater placement

```
sar_g_01,sarmatia,ground,3,12,eastern_ereb,2,5,,active,"Kursk axis"
```

Active ground unit at global (3,12) which is the Eastern Ereb theater-link for Sarmatia rows 1-4. Theater cell (2,5) is owned by Sarmatia, row 2, col 5.

### 6.3 Theater placement on occupied territory

```
sar_g_10,sarmatia,ground,4,11,eastern_ereb,5,6,,active,"Pokrovsk axis — occupied Ruthenia"
```

Sarmatia ground unit at global (4,11) = Ruthenia global hex. Theater cell (5,6) has `owner=ruthenia, occupied_by=sarmatia` in the Eastern Ereb JSON — valid placement.

### 6.4 Reserve

```
sar_g_r1,sarmatia,ground,,,,,,,reserve,"VDV strategic reserve"
```

All coord fields empty. Not on any map.

### 6.5 Embarked

```
col_a_10,columbia,tactical_air,,,,,col_n_01,embarked,"CVW-5 on USS carrier"
```

Embarked on `col_n_01` (a Columbia naval unit). Position inherited from carrier.

### 6.6 Naval on water (sea-link global hex)

```
col_n_03,columbia,naval,7,12,,,,,active,"Gulf CSG — Arabian Sea"
```

Naval unit on global (7,12) — a sea-link hex for Mashriq (sea rows 3-6). No theater coords (naval exempt, I-7).

### 6.7 Destroyed (audit row)

```
per_m_02,persia,strategic_missile,,,,,,,destroyed,"Struck R3 by Op Epic Fury"
```

Terminal. Ignored by runtime queries; kept for audit trail.

---

## 7. References

- `2 SEED/C_MECHANICS/SEED_C_MAP_UNITS_MASTER_v1.md` — canonical map+units master, includes theater linkage table.
- `2 SEED/C_MECHANICS/C4_DATA/units.csv` — live Template v1.0 default placement.
- `app/engine/agents/map_context.py` — reference implementation.
