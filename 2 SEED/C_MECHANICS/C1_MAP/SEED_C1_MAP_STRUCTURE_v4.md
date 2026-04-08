# Global Map Structure

> Size: 10 rows × 20 cols

---

## Map Architecture Decision

**Global Map:** 10×20 hex grid, 22 countries, 3 chokepoints (Formosa Strait, Gulf Gate, Caribe Passage)

**Theater Maps:** Two detailed theater maps:
1. **Eastern Ereb** (10×10 hexes) — Sarmatia-Ruthenia front. Active at start.
2. **Mashriq** (10×10 hexes, 70 land hexes) — Persia/Gulf war theater. Active at start. Persia (51 hexes), Mirage (8), Phrygia (6), Solaria (5). Provides tactical depth for Gulf Gate blockade, ground invasion paths, and air campaign.

Other theaters (Formosa, Caribbean, Thule, Korea) resolved at global hex level:
- Formosa blockade: fleet occupies water hexes adjacent to Formosa
- Amphibious assault: modifiers apply at global hex level
- Caribbean/Thule/Korea: political events, 1 hex resolution sufficient

**Global-Theater Link:** Eastern Ereb theater hexes link to global hexes:
- All Ruthenia theater hexes → global (12,5)
- Sarmatia rows 1-3 → global (13,4)
- Sarmatia rows 4+ → global (13,5)

---

## Land Hex Registry

| hex_id | owner | row | col |
|--------|-------|-----|-----|
| freeland_1 | freeland | 2 | 10 |
| sarmatia_1 | sarmatia | 2 | 11 |
| sarmatia_2 | sarmatia | 2 | 12 |
| sarmatia_3 | sarmatia | 2 | 16 |
| columbia_1 | columbia | 3 | 3 |
| thule_1 | thule | 3 | 6 |
| albion_1 | albion | 3 | 8 |
| freeland_2 | freeland | 3 | 10 |
| ruthenia_1 | ruthenia | 3 | 11 |
| sarmatia_4 | sarmatia | 3 | 12 |
| sarmatia_5 | sarmatia | 3 | 13 |
| sarmatia_6 | sarmatia | 3 | 14 |
| sarmatia_7 | sarmatia | 3 | 15 |
| sarmatia_8 | sarmatia | 3 | 16 |
| choson_1 | choson | 3 | 18 |
| columbia_2 | columbia | 4 | 2 |
| columbia_3 | columbia | 4 | 3 |
| albion_2 | albion | 4 | 7 |
| teutonia_2 | teutonia | 4 | 9 |
| teutonia_3 | teutonia | 4 | 10 |
| ruthenia_2 | ruthenia | 4 | 11 |
| sarmatia_9 | sarmatia | 4 | 12 |
| sarmatia_10 | sarmatia | 4 | 13 |
| sarmatia_11 | sarmatia | 4 | 14 |
| sarmatia_12 | sarmatia | 4 | 16 |
| hanguk_1 | hanguk | 4 | 17 |
| yamato_1 | yamato | 4 | 19 |
| columbia_4 | columbia | 5 | 3 |
| columbia_5 | columbia | 5 | 4 |
| columbia_6 | columbia | 5 | 5 |
| gallia_1 | gallia | 5 | 9 |
| gallia_2 | gallia | 5 | 10 |
| phrygia_1 | phrygia | 5 | 11 |
| sogdiana_1 | sogdiana | 5 | 14 |
| cathay_1 | cathay | 5 | 15 |
| cathay_2 | cathay | 5 | 16 |
| cathay_3 | cathay | 5 | 17 |
| yamato_2 | yamato | 5 | 19 |
| columbia_7 | columbia | 6 | 3 |
| columbia_8 | columbia | 6 | 4 |
| ponte_1 | ponte | 6 | 8 |
| levantia_1 | levantia | 6 | 10 |
| phrygia_2 | phrygia | 6 | 11 |
| persia_1 | persia | 6 | 12 |
| sogdiana_2 | sogdiana | 6 | 13 |
| sogdiana_3 | sogdiana | 6 | 14 |
| cathay_4 | cathay | 6 | 15 |
| cathay_5 | cathay | 6 | 16 |
| columbia_9 | columbia | 7 | 4 |
| ponte_2 | ponte | 7 | 9 |
| solaria_1 | solaria | 7 | 11 |
| persia_2 | persia | 7 | 13 |
| bharata_1 | bharata | 7 | 14 |
| bharata_2 | bharata | 7 | 15 |
| cathay_6 | cathay | 7 | 16 |
| formosa_1 | formosa | 7 | 18 |
| solaria_2 | solaria | 8 | 10 |
| mirage_1 | mirage | 8 | 11 |
| persia_3 | persia | 8 | 13 |
| bharata_3 | bharata | 8 | 14 |
| bharata_4 | bharata | 8 | 15 |
| caribe_1 | caribe | 9 | 5 |
| horn_1 | horn | 9 | 10 |
| bharata_5 | bharata | 9 | 15 |

## Chokepoints

| Name | Row | Col |
|------|-----|-----|
| Formosa Strait | 7 | 17 |
| Gulf Gate | 8 | 12 |
| Caribe Passage | 8 | 4 |

---

## Naval Positioning

Naval units are positioned on water hexes using grid coordinates: `w(col,row)`.
No named sea zones exist. Every water hex on the global map is a valid naval position.

**Rules:**
- Naval units can move to ANY water hex between rounds
- Attacks only target adjacent hexes (6 neighbors in hex grid)
- Multiple nations' fleets can coexist on the same water hex
- Chokepoints (Formosa Strait, Gulf Gate, Caribe Passage) are specific water hexes with blockade mechanics
- Blockade: fleet must occupy the chokepoint hex + surrounding water hexes

**Coordinate format:** `w(col,row)` where col and row are visual grid numbers from the global map.
Example: `w(13,9)` = water hex at column 13, row 9 (Gulf waters near Persia coast)

---

## Addendum: Template v1.0 — 2026-04-05

**Canonical source:** `SEED_C_MAP_UNITS_MASTER_v1.md`

### Canonical Global Linkage (replaces the provisional §"Global-Theater Link" above)

All coordinates below are **`(row, col)`, 1-indexed, global grid 10×20**. This supersedes any earlier linkage table in this file.

#### Eastern Ereb theater → global

| Theater cell condition | Global hex (row, col) |
|---|:---:|
| `owner = sarmatia`, theater row 1-4 | (3, 12) |
| `owner = sarmatia`, theater row 5+ | (4, 12) |
| `owner = ruthenia` (any row, free or occupied) | (4, 11) |
| `owner = sea` (any) | (5, 12) |

#### Mashriq theater → global

| Theater cell condition | Global hex (row, col) |
|---|:---:|
| `owner = phrygia` | (6, 11) |
| `owner = solaria` | (7, 11) |
| `owner = mirage` | (8, 11) |
| `owner = persia`, theater row 1-3 | (6, 12) |
| `owner = persia`, theater row 4-6 | (7, 13) |
| `owner = persia`, theater row 7-10 | (8, 13) |
| `owner = sea`, theater row 3-6 | (7, 12) |
| `owner = sea`, theater row 7-10 | (8, 12) |

### Coordinate convention (LOCKED)

`(row, col)`, row first, 1-indexed, row measured from top. Any legacy `(col, row)` references in the older text above are historical; use the canonical source for all new work.

Addendum: Template v1.0 — 2026-04-05
