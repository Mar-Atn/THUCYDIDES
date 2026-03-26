# TTT Hex Map Zone Structure v2

## Overview

- **Total hexes on grid**: 400
- **Land hexes**: 50
- **Ocean hexes**: 347
- **Chokepoint hexes**: 3
- **Grid**: 25 columns x 16 rows, pointy-top hexagons, side length 35px
- **Canvas**: 1600 x 900 px

## Hex Math

- Side length: s = 35
- Hex width: sqrt(3) * s = 60.6218
- Hex height: 2 * s = 70
- Row spacing (vertical): 1.5 * s = 52.5
- Column spacing (horizontal): sqrt(3) * s = 60.6218
- Odd-row horizontal offset: width/2 = 30.3109
- Center formula: cx = 50 + c * 60.6218 + (r % 2) * 30.3109
- Center formula: cy = 50 + r * 52.5

## Country Hex Counts

- **NORDOSTAN**: 8 hexes
- **CATHAY**: 5 hexes
- **COLUMBIA**: 5 hexes
- **TEUTONIA**: 3 hexes
- **SOGDIANA**: 3 hexes
- **PERSIA**: 3 hexes
- **BHARATA**: 3 hexes
- **YAMATO**: 2 hexes
- **GALLIA**: 2 hexes
- **HEARTLAND**: 2 hexes
- **PHRYGIA**: 2 hexes
- **SOLARIA**: 2 hexes
- **ALBION**: 1 hex
- **CHOSON**: 1 hex
- **FREELAND**: 1 hex
- **HANGUK**: 1 hex
- **PONTE**: 1 hex
- **LEVANTIA**: 1 hex
- **FORMOSA**: 1 hex
- **CARIBE**: 1 hex
- **HORN**: 1 hex
- **MIRAGE**: 1 hex

## Chokepoints

- **Formosa Strait** (`cp_formosa_strait`): grid (6,17), adjacent land: cathay, formosa
- **Gulf Gate** (`cp_gulf_gate`): grid (8,13), adjacent land: persia, solaria, mirage, bharata
- **Caribe Passage** (`cp_caribe_passage`): grid (9,2), adjacent land: caribe, columbia

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
- FREELAND -- HEARTLAND
- FREELAND -- NORDOSTAN
- FREELAND -- TEUTONIA
- GALLIA -- PONTE
- GALLIA -- TEUTONIA
- HEARTLAND -- NORDOSTAN
- HEARTLAND -- PHRYGIA
- HEARTLAND -- TEUTONIA
- HORN -- SOLARIA
- LEVANTIA -- PERSIA
- LEVANTIA -- PHRYGIA
- LEVANTIA -- SOLARIA
- MIRAGE -- SOLARIA
- NORDOSTAN -- SOGDIANA
- PERSIA -- SOGDIANA
- PERSIA -- SOLARIA
- PHRYGIA -- SOLARIA

## Islands (separated from mainland by water)

- **Albion** (3,6)
- **Caribe** (9,3)
- **Yamato** (4,19) and (5,19)
- **Formosa** (7,17)
- **Thule** (2,8) -- same color as Teutonia, separated by water

## Hex Registry

### Americas

| hex_id | display_name | type | owner | grid_row | grid_col | adjacent_hexes |
|--------|-------------|------|-------|----------|----------|---------------|
| col_nw | Columbia | land | columbia | 5 | 1 | sea_4_1, sea_4_2, sea_5_0, sea_5_2, col_main_1, col_main_3 |
| col_main_1 | Columbia | land | columbia | 6 | 1 | sea_5_0, col_nw, sea_6_0, col_main_3, sea_7_0, col_main_2 |
| col_main_3 | Columbia | land | columbia | 6 | 2 | col_nw, sea_5_2, col_main_1, sea_6_3, col_main_2, sea_7_2 |
| col_main_2 | Columbia | land | columbia | 7 | 1 | col_main_1, col_main_3, sea_7_0, sea_7_2, sea_8_1, col_south |
| col_south | Columbia | land | columbia | 8 | 2 | col_main_2, sea_7_2, sea_8_1, sea_8_3, sea_9_1, cp_caribe_passage |
| caribe | Caribe | land | caribe | 9 | 3 | sea_8_3, sea_8_4, cp_caribe_passage, sea_9_4, sea_10_3, sea_10_4 |

### Ereb (Europe)

| hex_id | display_name | type | owner | grid_row | grid_col | adjacent_hexes |
|--------|-------------|------|-------|----------|----------|---------------|
| thule | Thule | land | teutonia | 2 | 8 | sea_1_7, sea_1_8, sea_2_7, sea_2_9, sea_3_7, sea_3_8 |
| albion | Albion | land | albion | 3 | 6 | sea_2_6, sea_2_7, sea_3_5, sea_3_7, sea_4_6, sea_4_7 |
| teutonia_1 | Teutonia | land | teutonia | 4 | 8 | sea_3_7, sea_3_8, sea_4_7, freeland, gallia_1, teutonia_2 |
| freeland | Freeland | land | freeland | 4 | 9 | sea_3_8, sea_3_9, teutonia_1, nord_w2, teutonia_2, heartland_1 |
| gallia_1 | Gallia | land | gallia | 5 | 7 | sea_4_7, teutonia_1, sea_5_6, teutonia_2, gallia_2, sea_6_8 |
| teutonia_2 | Teutonia | land | teutonia | 5 | 8 | teutonia_1, freeland, gallia_1, heartland_1, sea_6_8, heartland_2 |
| gallia_2 | Gallia | land | gallia | 6 | 7 | sea_5_6, gallia_1, sea_6_6, sea_6_8, sea_7_6, ponte |
| ponte | Ponte | land | ponte | 7 | 7 | gallia_2, sea_6_8, sea_7_6, sea_7_8, sea_8_7, sea_8_8 |

### Heartland

| hex_id | display_name | type | owner | grid_row | grid_col | adjacent_hexes |
|--------|-------------|------|-------|----------|----------|---------------|
| heartland_1 | Heartland | land | heartland | 5 | 9 | freeland, nord_w2, teutonia_2, sea_5_10, heartland_2, phrygia_1 |
| heartland_2 | Heartland | land | heartland | 6 | 9 | teutonia_2, heartland_1, sea_6_8, phrygia_1, sea_7_8, sea_7_9 |

### Nordostan

| hex_id | display_name | type | owner | grid_row | grid_col | adjacent_hexes |
|--------|-------------|------|-------|----------|----------|---------------|
| nord_n1 | Nordostan | land | nordostan | 2 | 11 | sea_1_10, sea_1_11, sea_2_10, sea_2_12, nord_w1, nord_c1 |
| nord_w1 | Nordostan | land | nordostan | 3 | 10 | sea_2_10, nord_n1, sea_3_9, nord_c1, nord_w2, nord_c2 |
| nord_c1 | Nordostan | land | nordostan | 3 | 11 | nord_n1, sea_2_12, nord_w1, nord_e1, nord_c2, sogdiana_1 |
| nord_e1 | Nordostan | land | nordostan | 3 | 12 | sea_2_12, sea_2_13, nord_c1, nord_e2, sogdiana_1, sogdiana_3 |
| nord_e2 | Nordostan | land | nordostan | 3 | 13 | sea_2_13, sea_2_14, nord_e1, nord_e3, sogdiana_3, cathay_1 |
| nord_e3 | Nordostan | land | nordostan | 3 | 14 | sea_2_14, sea_2_15, nord_e2, sea_3_15, cathay_1, cathay_3 |
| nord_w2 | Nordostan | land | nordostan | 4 | 10 | sea_3_9, nord_w1, freeland, nord_c2, heartland_1, sea_5_10 |
| nord_c2 | Nordostan | land | nordostan | 4 | 11 | nord_w1, nord_c1, nord_w2, sogdiana_1, sea_5_10, sea_5_11 |

### Mashriq (Middle East / Africa)

| hex_id | display_name | type | owner | grid_row | grid_col | adjacent_hexes |
|--------|-------------|------|-------|----------|----------|---------------|
| persia_1 | Persia | land | persia | 5 | 12 | sogdiana_1, sogdiana_3, sea_5_11, sogdiana_2, persia_2, sea_6_13 |
| phrygia_1 | Phrygia | land | phrygia | 6 | 10 | heartland_1, sea_5_10, heartland_2, sea_6_11, sea_7_9, phrygia_2 |
| persia_2 | Persia | land | persia | 6 | 12 | sea_5_11, persia_1, sea_6_11, sea_6_13, levantia, persia_3 |
| phrygia_2 | Phrygia | land | phrygia | 7 | 10 | phrygia_1, sea_6_11, sea_7_9, levantia, sea_8_10, solaria_1 |
| levantia | Levantia | land | levantia | 7 | 11 | sea_6_11, persia_2, phrygia_2, persia_3, solaria_1, solaria_2 |
| persia_3 | Persia | land | persia | 7 | 12 | persia_2, sea_6_13, levantia, bharata_3, solaria_2, cp_gulf_gate |
| solaria_1 | Solaria | land | solaria | 8 | 11 | phrygia_2, levantia, sea_8_10, solaria_2, horn, sea_9_11 |
| solaria_2 | Solaria | land | solaria | 8 | 12 | levantia, persia_3, solaria_1, cp_gulf_gate, sea_9_11, mirage |
| horn | Horn | land | horn | 9 | 10 | sea_8_10, solaria_1, sea_9_9, sea_9_11, sea_10_10, sea_10_11 |
| mirage | Mirage | land | mirage | 9 | 12 | solaria_2, cp_gulf_gate, sea_9_11, sea_9_13, sea_10_12, sea_10_13 |

### Sogdiana (Central Asia)

| hex_id | display_name | type | owner | grid_row | grid_col | adjacent_hexes |
|--------|-------------|------|-------|----------|----------|---------------|
| sogdiana_1 | Sogdiana | land | sogdiana | 4 | 12 | nord_c1, nord_e1, nord_c2, sogdiana_3, sea_5_11, persia_1 |
| sogdiana_3 | Sogdiana | land | sogdiana | 4 | 13 | nord_e1, nord_e2, sogdiana_1, cathay_1, persia_1, sogdiana_2 |
| sogdiana_2 | Sogdiana | land | sogdiana | 5 | 13 | sogdiana_3, cathay_1, persia_1, cathay_2, sea_6_13, bharata_1 |

### Bharata (South Asia)

| hex_id | display_name | type | owner | grid_row | grid_col | adjacent_hexes |
|--------|-------------|------|-------|----------|----------|---------------|
| bharata_1 | Bharata | land | bharata | 6 | 14 | sogdiana_2, cathay_2, sea_6_13, sea_6_15, bharata_3, bharata_2 |
| bharata_3 | Bharata | land | bharata | 7 | 13 | sea_6_13, bharata_1, persia_3, bharata_2, cp_gulf_gate, sea_8_14 |
| bharata_2 | Bharata | land | bharata | 7 | 14 | bharata_1, sea_6_15, bharata_3, sea_7_15, sea_8_14, sea_8_15 |

### Asu (East Asia)

| hex_id | display_name | type | owner | grid_row | grid_col | adjacent_hexes |
|--------|-------------|------|-------|----------|----------|---------------|
| choson | Choson | land | choson | 3 | 16 | sea_2_16, sea_2_17, sea_3_15, sea_3_17, sea_4_16, hanguk |
| cathay_1 | Cathay | land | cathay | 4 | 14 | nord_e2, nord_e3, sogdiana_3, cathay_3, sogdiana_2, cathay_2 |
| cathay_3 | Cathay | land | cathay | 4 | 15 | nord_e3, sea_3_15, cathay_1, sea_4_16, cathay_2, cathay_4 |
| hanguk | Hanguk | land | hanguk | 4 | 17 | choson, sea_3_17, sea_4_16, sea_4_18, cathay_5, sea_5_17 |
| yamato_1 | Yamato | land | yamato | 4 | 19 | sea_3_18, sea_3_19, sea_4_18, sea_4_20, sea_5_18, yamato_2 |
| cathay_2 | Cathay | land | cathay | 5 | 14 | cathay_1, cathay_3, sogdiana_2, cathay_4, bharata_1, sea_6_15 |
| cathay_4 | Cathay | land | cathay | 5 | 15 | cathay_3, sea_4_16, cathay_2, cathay_5, sea_6_15, sea_6_16 |
| cathay_5 | Cathay | land | cathay | 5 | 16 | sea_4_16, hanguk, cathay_4, sea_5_17, sea_6_16, cp_formosa_strait |
| yamato_2 | Yamato | land | yamato | 5 | 19 | yamato_1, sea_4_20, sea_5_18, sea_5_20, sea_6_19, sea_6_20 |
| formosa | Formosa | land | formosa | 7 | 17 | cp_formosa_strait, sea_6_18, sea_7_16, sea_7_18, sea_8_17, sea_8_18 |

### Chokepoints

| hex_id | display_name | type | grid_row | grid_col | adjacent_hexes |
|--------|-------------|------|----------|----------|---------------|
| cp_formosa_strait | Formosa Strait | chokepoint | 6 | 17 | cathay_5, sea_5_17, sea_6_16, sea_6_18, sea_7_16, formosa |
| cp_gulf_gate | Gulf Gate | chokepoint | 8 | 13 | persia_3, bharata_3, solaria_2, sea_8_14, mirage, sea_9_13 |
| cp_caribe_passage | Caribe Passage | chokepoint | 9 | 2 | col_south, sea_8_3, sea_9_1, caribe, sea_10_2, sea_10_3 |
