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
