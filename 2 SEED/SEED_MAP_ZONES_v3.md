# TTT Hex Map Zone Structure v3

## Overview

- **Total hexes on grid**: 308
- **Land hexes**: 54
- **Ocean hexes**: 251
- **Chokepoint hexes**: 3
- **Grid**: 22 columns x 14 rows, pointy-top hexagons, side length 35px
- **Canvas**: 1600 x 900 px

## Hex Math

- Side length: s = 35
- Hex width: sqrt(3) * s = 60.6218
- Hex height: 2 * s = 70
- Row spacing (vertical): 1.5 * s = 52.5
- Column spacing (horizontal): sqrt(3) * s = 60.6218
- Odd-row horizontal offset: width/2 = 30.3109
- Center formula: cx = 55 + c * 60.6218 + (r % 2) * 30.3109
- Center formula: cy = 30 + r * 52.5

## Country Hex Counts

- **NORDOSTAN**: 8 hexes
- **COLUMBIA**: 7 hexes
- **CATHAY**: 7 hexes
- **TEUTONIA**: 3 hexes
- **SOGDIANA**: 3 hexes
- **PERSIA**: 3 hexes
- **BHARATA**: 3 hexes
- **HEARTLAND**: 2 hexes
- **GALLIA**: 2 hexes
- **PHRYGIA**: 2 hexes
- **SOLARIA**: 2 hexes
- **YAMATO**: 2 hexes
- **CARIBE**: 1 hex
- **ALBION**: 1 hex
- **FREELAND**: 1 hex
- **PONTE**: 1 hex
- **LEVANTIA**: 1 hex
- **HORN**: 1 hex
- **MIRAGE**: 1 hex
- **CHOSON**: 1 hex
- **HANGUK**: 1 hex
- **FORMOSA**: 1 hex

## Chokepoints

- **Formosa Strait** (`cp_formosa_strait`): grid (6,16), adjacent land: cathay, cathay, formosa
- **Gulf Gate** (`cp_gulf_gate`): grid (7,10), adjacent land: persia, persia, solaria, mirage
- **Caribe Passage** (`cp_caribe_passage`): grid (8,2), adjacent land: columbia, caribe

## Adjacency Rules

Two hexes are adjacent if they share an edge in the pointy-top offset hex grid (odd-r offset).
Each hex has up to 6 neighbors. For even rows, neighbors are:
  (r-1,c-1), (r-1,c), (r,c-1), (r,c+1), (r+1,c-1), (r+1,c)
For odd rows:
  (r-1,c), (r-1,c+1), (r,c-1), (r,c+1), (r+1,c), (r+1,c+1)

## Country Border Summary

Countries that share at least one land border edge:

- BHARATA -- CATHAY
- BHARATA -- PERSIA
- BHARATA -- SOGDIANA
- CATHAY -- HANGUK
- CATHAY -- NORDOSTAN
- CATHAY -- SOGDIANA
- CHOSON -- HANGUK
- FREELAND -- GALLIA
- FREELAND -- HEARTLAND
- FREELAND -- TEUTONIA
- GALLIA -- LEVANTIA
- GALLIA -- PONTE
- GALLIA -- TEUTONIA
- HEARTLAND -- NORDOSTAN
- HEARTLAND -- PHRYGIA
- HEARTLAND -- TEUTONIA
- HORN -- SOLARIA
- LEVANTIA -- PHRYGIA
- LEVANTIA -- SOLARIA
- MIRAGE -- SOLARIA
- NORDOSTAN -- SOGDIANA
- PERSIA -- PHRYGIA
- PERSIA -- SOGDIANA
- PERSIA -- SOLARIA
- PHRYGIA -- SOLARIA

## Islands (separated from mainland by water)

- **Albion** (albion): grid (4,5)
- **Caribe** (caribe): grid (9,2)
- **Yamato** (yamato_1): grid (3,18) and (4,18)
- **Formosa** (formosa): grid (7,16)
- **Thule** (thule): grid (2,4) -- same color as Teutonia, separated by water

## Hex Registry

### Americas

| hex_id | display_name | type | owner | grid_row | grid_col | adjacent_hexes |
|--------|-------------|------|-------|----------|----------|---------------|
| col_nw | Columbia | land | columbia | 4 | 1 | sea_3_0, sea_3_1, sea_4_0, sea_4_2, col_w, col_main_1 |
| col_w | Columbia | land | columbia | 5 | 0 | sea_4_0, col_nw, col_main_1, sea_6_0, col_main_3 |
| col_main_1 | Columbia | land | columbia | 5 | 1 | col_nw, sea_4_2, col_w, col_main_2, col_main_3, col_main_4 |
| col_main_2 | Columbia | land | columbia | 5 | 2 | sea_4_2, sea_4_3, col_main_1, sea_5_3, col_main_4, sea_6_3 |
| col_main_3 | Columbia | land | columbia | 6 | 1 | col_w, col_main_1, sea_6_0, col_main_4, sea_7_0, col_south |
| col_main_4 | Columbia | land | columbia | 6 | 2 | col_main_1, col_main_2, col_main_3, sea_6_3, col_south, sea_7_2 |
| col_south | Columbia | land | columbia | 7 | 1 | col_main_3, col_main_4, sea_7_0, sea_7_2, sea_8_1, cp_caribe_passage |
| caribe | Caribe | land | caribe | 9 | 2 | cp_caribe_passage, sea_8_3, sea_9_1, sea_9_3, sea_10_2, sea_10_3 |

### Ereb (Europe)

| hex_id | display_name | type | owner | grid_row | grid_col | adjacent_hexes |
|--------|-------------|------|-------|----------|----------|---------------|
| thule | Thule | land | teutonia | 2 | 4 | sea_1_3, sea_1_4, sea_2_3, sea_2_5, sea_3_3, sea_3_4 |
| teutonia_1 | Teutonia | land | teutonia | 3 | 7 | sea_2_7, sea_2_8, sea_3_6, heartland_1, teutonia_2, freeland |
| freeland | Freeland | land | freeland | 4 | 8 | teutonia_1, heartland_1, teutonia_2, heartland_2, gallia_2, sea_5_8 |
| albion | Albion | land | albion | 4 | 5 | sea_3_4, sea_3_5, sea_4_4, sea_4_6, sea_5_4, sea_5_5 |
| teutonia_2 | Teutonia | land | teutonia | 4 | 7 | sea_3_6, teutonia_1, sea_4_6, freeland, gallia_1, gallia_2 |
| gallia_1 | Gallia | land | gallia | 5 | 6 | sea_4_6, teutonia_2, sea_5_5, gallia_2, ponte, sea_6_7 |
| gallia_2 | Gallia | land | gallia | 5 | 7 | teutonia_2, freeland, gallia_1, sea_5_8, sea_6_7, levantia |
| ponte | Ponte | land | ponte | 6 | 6 | sea_5_5, gallia_1, sea_6_5, sea_6_7, sea_7_5, sea_7_6 |

### Heartland

| hex_id | display_name | type | owner | grid_row | grid_col | adjacent_hexes |
|--------|-------------|------|-------|----------|----------|---------------|
| heartland_1 | Heartland | land | heartland | 3 | 8 | sea_2_8, nord_w1, teutonia_1, nord_w2, freeland, heartland_2 |
| heartland_2 | Heartland | land | heartland | 4 | 9 | heartland_1, nord_w2, freeland, sea_4_10, sea_5_8, phrygia_1 |

### Nordostan

| hex_id | display_name | type | owner | grid_row | grid_col | adjacent_hexes |
|--------|-------------|------|-------|----------|----------|---------------|
| nord_n1 | Nordostan | land | nordostan | 1 | 10 | sea_0_10, sea_0_11, sea_1_9, sea_1_11, nord_c1, nord_e1 |
| nord_w1 | Nordostan | land | nordostan | 2 | 9 | sea_1_8, sea_1_9, sea_2_8, nord_c1, heartland_1, nord_w2 |
| nord_c1 | Nordostan | land | nordostan | 2 | 10 | sea_1_9, nord_n1, nord_w1, nord_e1, nord_w2, nord_c2 |
| nord_e1 | Nordostan | land | nordostan | 2 | 11 | nord_n1, sea_1_11, nord_c1, nord_e2, nord_c2, sogdiana_1 |
| nord_e2 | Nordostan | land | nordostan | 2 | 12 | sea_1_11, sea_1_12, nord_e1, nord_e3, sogdiana_1, sogdiana_3 |
| nord_e3 | Nordostan | land | nordostan | 2 | 13 | sea_1_12, sea_1_13, nord_e2, sea_2_14, sogdiana_3, cathay_1 |
| nord_w2 | Nordostan | land | nordostan | 3 | 9 | nord_w1, nord_c1, heartland_1, nord_c2, heartland_2, sea_4_10 |
| nord_c2 | Nordostan | land | nordostan | 3 | 10 | nord_c1, nord_e1, nord_w2, sogdiana_1, sea_4_10, sea_4_11 |

### Mashriq (Middle East / Africa)

| hex_id | display_name | type | owner | grid_row | grid_col | adjacent_hexes |
|--------|-------------|------|-------|----------|----------|---------------|
| phrygia_1 | Phrygia | land | phrygia | 5 | 9 | heartland_2, sea_4_10, sea_5_8, sea_5_10, phrygia_2, persia_2 |
| persia_1 | Persia | land | persia | 5 | 11 | sea_4_11, sogdiana_2, sea_5_10, bharata_2, persia_3, sea_6_12 |
| levantia | Levantia | land | levantia | 6 | 8 | gallia_2, sea_5_8, sea_6_7, phrygia_2, sea_7_7, solaria_1 |
| phrygia_2 | Phrygia | land | phrygia | 6 | 9 | sea_5_8, phrygia_1, levantia, persia_2, solaria_1, solaria_2 |
| persia_2 | Persia | land | persia | 6 | 10 | phrygia_1, sea_5_10, phrygia_2, persia_3, solaria_2, cp_gulf_gate |
| persia_3 | Persia | land | persia | 6 | 11 | sea_5_10, persia_1, persia_2, sea_6_12, cp_gulf_gate, sea_7_11 |
| solaria_1 | Solaria | land | solaria | 7 | 8 | levantia, phrygia_2, sea_7_7, solaria_2, horn, sea_8_9 |
| solaria_2 | Solaria | land | solaria | 7 | 9 | phrygia_2, persia_2, solaria_1, cp_gulf_gate, sea_8_9, mirage |
| horn | Horn | land | horn | 8 | 8 | sea_7_7, solaria_1, sea_8_7, sea_8_9, sea_9_7, sea_9_8 |
| mirage | Mirage | land | mirage | 8 | 10 | solaria_2, cp_gulf_gate, sea_8_9, sea_8_11, sea_9_9, sea_9_10 |

### Sogdiana (Central Asia)

| hex_id | display_name | type | owner | grid_row | grid_col | adjacent_hexes |
|--------|-------------|------|-------|----------|----------|---------------|
| sogdiana_1 | Sogdiana | land | sogdiana | 3 | 11 | nord_e1, nord_e2, nord_c2, sogdiana_3, sea_4_11, sogdiana_2 |
| sogdiana_3 | Sogdiana | land | sogdiana | 3 | 12 | nord_e2, nord_e3, sogdiana_1, cathay_1, sogdiana_2, sea_4_13 |
| sogdiana_2 | Sogdiana | land | sogdiana | 4 | 12 | sogdiana_1, sogdiana_3, sea_4_11, sea_4_13, persia_1, bharata_2 |

### Bharata (South Asia)

| hex_id | display_name | type | owner | grid_row | grid_col | adjacent_hexes |
|--------|-------------|------|-------|----------|----------|---------------|
| bharata_1 | Bharata | land | bharata | 6 | 13 | bharata_2, bharata_3, sea_6_12, sea_6_14, sea_7_12, sea_7_13 |
| bharata_2 | Bharata | land | bharata | 5 | 12 | sogdiana_2, sea_4_13, persia_1, bharata_3, sea_6_12, bharata_1 |
| bharata_3 | Bharata | land | bharata | 5 | 13 | sea_4_13, cathay_2, bharata_2, cathay_5, bharata_1, sea_6_14 |

### Asu (East Asia)

| hex_id | display_name | type | owner | grid_row | grid_col | adjacent_hexes |
|--------|-------------|------|-------|----------|----------|---------------|
| choson | Choson | land | choson | 2 | 15 | sea_1_14, sea_1_15, sea_2_14, sea_2_16, sea_3_14, hanguk |
| cathay_1 | Cathay | land | cathay | 3 | 13 | nord_e3, sea_2_14, sogdiana_3, sea_3_14, sea_4_13, cathay_2 |
| hanguk | Hanguk | land | hanguk | 3 | 15 | choson, sea_2_16, sea_3_14, sea_3_16, cathay_3, cathay_4 |
| yamato_1 | Yamato | land | yamato | 3 | 18 | sea_2_18, sea_2_19, sea_3_17, sea_3_19, yamato_2, sea_4_19 |
| cathay_2 | Cathay | land | cathay | 4 | 14 | cathay_1, sea_3_14, sea_4_13, cathay_3, bharata_3, cathay_5 |
| cathay_3 | Cathay | land | cathay | 4 | 15 | sea_3_14, hanguk, cathay_2, cathay_4, cathay_5, cathay_6 |
| cathay_4 | Cathay | land | cathay | 4 | 16 | hanguk, sea_3_16, cathay_3, sea_4_17, cathay_6, sea_5_16 |
| yamato_2 | Yamato | land | yamato | 4 | 18 | sea_3_17, yamato_1, sea_4_17, sea_4_19, sea_5_17, sea_5_18 |
| cathay_5 | Cathay | land | cathay | 5 | 14 | cathay_2, cathay_3, bharata_3, cathay_6, sea_6_14, cathay_7 |
| cathay_6 | Cathay | land | cathay | 5 | 15 | cathay_3, cathay_4, cathay_5, sea_5_16, cathay_7, cp_formosa_strait |
| cathay_7 | Cathay | land | cathay | 6 | 15 | cathay_5, cathay_6, sea_6_14, cp_formosa_strait, sea_7_14, sea_7_15 |
| formosa | Formosa | land | formosa | 7 | 16 | cp_formosa_strait, sea_6_17, sea_7_15, sea_7_17, sea_8_16, sea_8_17 |

### Chokepoints

| hex_id | display_name | type | grid_row | grid_col | adjacent_hexes |
|--------|-------------|------|----------|----------|---------------|
| cp_formosa_strait | Formosa Strait | chokepoint | 6 | 16 | cathay_6, sea_5_16, cathay_7, sea_6_17, sea_7_15, formosa |
| cp_gulf_gate | Gulf Gate | chokepoint | 7 | 10 | persia_2, persia_3, solaria_2, sea_7_11, mirage, sea_8_11 |
| cp_caribe_passage | Caribe Passage | chokepoint | 8 | 2 | col_south, sea_7_2, sea_8_1, sea_8_3, sea_9_1, caribe |

---

## Theater Zoom-In Maps

Theater maps expand global hex zones into higher-granularity tactical hexes. Pointy-top hexagons, side length s = 30. These activate when military escalation demands tactical resolution.

---

### Theater 1: Eastern Ereb (Heartland-Nordostan Conflict)

**File:** `THEATER_EASTERN_EREB.svg`
**Expands:** Global hexes `heartland_1`, `heartland_2`, `nord_w1`, `nord_w2`
**Hex count:** 15 | **Canvas:** 900 x 700 | **Status:** Active at game start

#### Hex Registry

| hex_id | display_name | type | owner | adjacent_hexes | starting_units |
|--------|-------------|------|-------|---------------|----------------|
| ee_corridor | The Corridor | land | nordostan | ee_nord_staging_n, ee_occupied_north, ee_river_line | — |
| ee_nord_staging_n | Northern Staging | land | nordostan | ee_corridor, ee_nord_staging_s, ee_occupied_north, ee_occupied_east | 3 ground |
| ee_nord_staging_s | Southern Staging | land | nordostan | ee_nord_staging_n, ee_occupied_east | 2 ground, 1 missile |
| ee_occupied_north | Occupied North | land_occupied | nordostan | ee_corridor, ee_nord_staging_n, ee_occupied_east, ee_front_north, ee_contested | 2 ground |
| ee_occupied_east | Occupied East | land_occupied | nordostan | ee_nord_staging_n, ee_nord_staging_s, ee_occupied_north, ee_contested, ee_peninsula | 3 ground, 1 air |
| ee_front_north | Northern Front | land | heartland | ee_occupied_north, ee_contested, ee_river_line, ee_capital | 2 ground, 1 air_defense |
| ee_contested | The Contested Ground | land_contested | heartland | ee_occupied_north, ee_occupied_east, ee_front_north, ee_front_south, ee_central | 3 ground, 1 air, 1 air_defense |
| ee_front_south | Southern Front | land | heartland | ee_contested, ee_central, ee_river_line, ee_peninsula | 2 ground |
| ee_river_line | River Line | land | heartland | ee_corridor, ee_front_north, ee_front_south, ee_capital, ee_western | 1 ground |
| ee_capital | The Capital | land | heartland | ee_front_north, ee_river_line, ee_central, ee_western | 1 ground, 1 air_defense |
| ee_central | Central Heartland | land | heartland | ee_contested, ee_front_south, ee_capital | 1 ground |
| ee_western | Western Heartland | land | heartland | ee_river_line, ee_capital, ee_nato_border | — |
| ee_nato_border | Alliance Border | land | nato | ee_western | — |
| ee_peninsula | The Peninsula | land_occupied | nordostan | ee_occupied_east, ee_front_south, ee_sea | 1 ground, 1 naval |
| ee_sea | Southern Waters | sea | neutral | ee_peninsula, ee_front_south | 1 naval (Nordostan) |

#### Starting Force Summary

| Side | Ground | Naval | Air | Air Defense | Missiles | Total |
|------|--------|-------|-----|------------|----------|-------|
| Nordostan | 11 | 2 | 1 | 0 | 1 | 15 |
| Heartland | 10 | 0 | 1 | 3 | 0 | 14 |

#### Special Rules

1. **Occupied Territory:** `ee_occupied_north` and `ee_occupied_east` are former Heartland territory under Nordostan military control. Shown with striped overlay. Heartland may attempt to recapture.
2. **Contested Zone:** `ee_contested` (The Contested Ground) is the critical hex. Heartland holds ~20% of the territory after 4 years of fighting. Nordostan claims it for any settlement. Heartland defends it as existential. Amber highlight. If Nordostan captures it, Heartland stability drops sharply.
3. **The Corridor:** `ee_corridor` allows Nordostan to threaten a northern flank attack toward the capital, bypassing the front line. Historically uncommitted but a constant threat.
4. **The Peninsula:** `ee_peninsula` is Nordostan-occupied with a naval base. Connected to Southern Waters. Provides naval projection into the theater.
5. **Alliance Border:** `ee_nato_border` is protected by Article 5. Any attack on this hex triggers Alliance (NATO) collective defense. Effectively untouchable. No units deployed — serves as supply entry point for Western aid to Heartland.
6. **Front Line:** The active front line runs between rows 2-3 (occupied/contested and Heartland front hexes). Shown as red dashed line.
7. **Supply Corridor:** Western military aid enters through `ee_nato_border` -> `ee_western` -> `ee_capital` -> front lines. Disrupting this corridor (e.g., long-range strikes) degrades Heartland resupply.

---

### Theater 2: Formosa Strait (Cathay-Formosa Conflict)

**File:** `THEATER_FORMOSA.svg`
**Expands:** Global hexes `cathay_6`, `cathay_7`, `cp_formosa_strait`, `formosa`
**Hex count:** 10 | **Canvas:** 800 x 600 | **Status:** Activates on escalation

#### Hex Registry

| hex_id | display_name | type | owner | adjacent_hexes | starting_units |
|--------|-------------|------|-------|---------------|----------------|
| fs_staging_north | Northern Staging | land | cathay | fs_staging_center, fs_strait_north | 2 air, 1 missile |
| fs_staging_center | Central Staging | land | cathay | fs_staging_north, fs_staging_south, fs_strait_north, fs_strait_south | 4 ground, 2 naval |
| fs_staging_south | Southern Staging | land | cathay | fs_staging_center, fs_strait_south, fs_scs_approach | 2 naval, 1 ground |
| fs_strait_north | Northern Passage | sea | neutral | fs_staging_north, fs_staging_center, fs_formosa_north | — |
| fs_strait_south | Southern Passage | sea_chokepoint | neutral | fs_staging_center, fs_staging_south, fs_formosa_south, fs_scs_approach, fs_channel | — |
| fs_formosa_north | Northern Shore | land | formosa | fs_strait_north, fs_formosa_south, fs_eastern_sea | 2 ground, 1 air_defense, 1 air |
| fs_formosa_south | Southern Shore | land | formosa | fs_strait_south, fs_formosa_north, fs_channel, fs_eastern_sea | 1 ground, 1 naval |
| fs_eastern_sea | Eastern Waters | sea | neutral | fs_formosa_north, fs_formosa_south, fs_channel | 2 naval (Columbia), 1 air (Columbia) |
| fs_scs_approach | Southern Sea | sea | neutral | fs_staging_south, fs_strait_south, fs_channel | — |
| fs_channel | The Channel | sea | neutral | fs_strait_south, fs_formosa_south, fs_eastern_sea, fs_scs_approach | — |

#### Starting Force Summary

| Side | Ground | Naval | Air | Air Defense | Missiles | Total |
|------|--------|-------|-----|------------|----------|-------|
| Cathay | 5 | 4 | 2 | 0 | 1 | 12 |
| Formosa | 3 | 1 | 1 | 1 | 0 | 6 |
| Columbia (pre-positioned) | 0 | 2 | 1 | 0 | 0 | 3 |

#### Special Rules

1. **Amphibious Assault (4:1):** Crossing the strait from any Cathay staging hex to any Formosa hex requires 4:1 force ratio (attacker:defender in the target hex). Naval superiority in the strait hex is a prerequisite — Cathay must control at least one strait hex before landing.
2. **Strait Chokepoint:** `fs_strait_south` (Southern Passage) is the Formosa Strait chokepoint from the global map. Controlling it allows blockade of Formosa's southern maritime access.
3. **Columbia/Yamato Intervention:** Columbia and Yamato forces enter via `fs_eastern_sea`. If Columbia declares intervention, additional naval and air units deploy here. Yamato may independently reinforce.
4. **Semiconductor Fabs:** `fs_formosa_north` contains the world's critical semiconductor fabrication facilities. Combat in this hex risks destroying them (roll for collateral damage each combat round). Destruction triggers global economic shock (-2 to all nations' economic stability).
5. **Pre-positioned Forces:** Columbia has 2 naval + 1 air pre-positioned in Eastern Waters (routine Pacific deployment). These can intervene immediately if Columbia declares support, without needing to deploy from the global map.
6. **Southern Approach:** `fs_scs_approach` connects to the South China Sea on the global map. Cathay can reinforce through here, but it is also vulnerable to interdiction from The Channel.

---

### Theater 3: Mashriq / Persian Gulf

**File:** `THEATER_MASHRIQ.svg`
**Expands:** Global hexes `persia_2`, `persia_3`, `cp_gulf_gate`, `solaria_2`, `phrygia_2`, `levantia`
**Hex count:** 12 | **Canvas:** 800 x 600 | **Status:** Active at game start

#### Hex Registry

| hex_id | display_name | type | owner | adjacent_hexes | starting_units |
|--------|-------------|------|-------|---------------|----------------|
| ma_levantia | Levantia | land | levantia | ma_corridor, ma_interior | 1 air, 1 missile |
| ma_corridor | The Corridor | land | neutral | ma_levantia, ma_frontier | — |
| ma_frontier | The Frontier | land | neutral | ma_corridor, ma_highlands, ma_interior | — |
| ma_interior | The Interior | land | persia | ma_levantia, ma_frontier, ma_highlands | 1 ground, 1 air_defense, 1 missile |
| ma_highlands | The Highlands | land | persia | ma_frontier, ma_interior, ma_coast | 2 ground |
| ma_coast | The Coast | land | persia | ma_highlands, ma_gulf_gate, ma_gulf_waters, ma_southern_waters | 2 ground, 1 naval, 1 missile |
| ma_gulf_gate | Gulf Gate | sea_chokepoint | neutral | ma_coast, ma_gulf_waters, ma_solaria, ma_mirage | — |
| ma_gulf_waters | Gulf Waters | sea | neutral | ma_coast, ma_gulf_gate, ma_solaria, ma_mirage, ma_southern_waters | 1 naval (Columbia) |
| ma_solaria | Solaria | land | solaria | ma_gulf_gate, ma_gulf_waters, ma_mirage | 1 ground (Columbia), 1 air |
| ma_mirage | Mirage | land | mirage | ma_gulf_gate, ma_gulf_waters, ma_solaria | — |
| ma_southern_waters | Southern Waters | sea | neutral | ma_coast, ma_gulf_waters, ma_yemen | 1 naval (Columbia) |
| ma_yemen | Southern Gate | land | persia_proxy | ma_southern_waters, ma_corridor | — |

#### Starting Force Summary

| Side | Ground | Naval | Air | Air Defense | Missiles | Total |
|------|--------|-------|-----|------------|----------|-------|
| Persia | 5 | 1 | 0 | 1 | 2 | 9 |
| Levantia | 0 | 0 | 1 | 0 | 1 | 2 |
| Columbia (deployed) | 1 | 2 | 0 | 0 | 0 | 3 |
| Gulf States (Solaria) | 0 | 0 | 1 | 0 | 0 | 1 |

#### Special Rules

1. **Gulf Gate Blockade Mechanic:** The Gulf Gate (`ma_gulf_gate`) is blocked AS LONG AS Persia has ground units on The Coast (`ma_coast`). Ground-based anti-ship missiles and coastal defenses make the chokepoint impervious to naval or air attacks alone. To reopen the gate, Columbia must capture The Coast hex — either by amphibious assault from Gulf Waters or by ground invasion through The Frontier -> Highlands -> Coast.
2. **Ground Invasion Route:** The Corridor (`ma_corridor`) -> The Frontier (`ma_frontier`) -> The Highlands -> The Coast. This is the overland path to break the blockade. The Highlands impose a -1 combat modifier on attackers (mountain terrain).
3. **Nuclear Dimension:** The Interior (`ma_interior`) contains Persia's nuclear program facilities. Levantia (`ma_levantia`) has an undeclared nuclear arsenal. Strikes on The Interior's nuclear sites risk escalation. If Persia achieves nuclear breakout (event card or timer), the entire theater dynamic shifts.
4. **Levantia Independent Action:** Levantia strikes Persia targets independently (air and missile strikes on The Interior). Does not coordinate with Columbia. Nuclear-armed — serves as a separate escalation vector.
5. **Proxy Control — Southern Gate:** `ma_yemen` is controlled by a Persia-aligned proxy force. It functions as a second chokepoint (equivalent to Bab el-Mandeb). The proxy can harass shipping in Southern Waters. Disrupting the proxy requires dedicated Columbia naval operations.
6. **Oil Infrastructure:** Combat in Gulf Waters, Gulf Gate, Solaria, or Mirage hexes risks damage to oil infrastructure. Each combat round in these hexes: roll for oil disruption event (affects global oil prices, all nations' economies).
7. **Missile Threat to Gulf States:** Persia missiles in The Coast and The Interior can strike Solaria and Mirage. Gulf states cannot intercept without air defense units deployed. Columbia's air defense from the global map must be physically moved here to protect them.
8. **Amphibious Assault on Coast:** Landing from Gulf Waters onto The Coast follows the standard 4:1 amphibious ratio (same as Formosa Strait). Combined arms with ground advance through Highlands can relax this to 2:1 if attacking from both directions simultaneously.
