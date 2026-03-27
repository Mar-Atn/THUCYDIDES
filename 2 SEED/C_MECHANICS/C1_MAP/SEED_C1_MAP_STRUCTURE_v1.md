# TTT Map System Structure v1

> Canonical reference for all map mechanics. SVGs visualize this document; this document governs.

---

## Section 1: Global Map — Hex Registry

**Grid**: 23 columns x 15 rows, pointy-top hexagons, side length s=35
**Canvas**: 1700 x 950 px
**Total hexes**: 308 (54 land, 3 chokepoint, 251 ocean)

> Grid coordinates displayed on map: column (horizontal) first, row (vertical) second. Format: (col, row).

### Hex Math (Pointy-Top, Odd-Row Offset)

```
Side length:        s = 35
Hex width:          w = sqrt(3) * s = 60.6218
Hex height:         h = 2 * s = 70
Row spacing (vert): dy = 1.5 * s = 52.5
Col spacing (horiz): dx = sqrt(3) * s = 60.6218
Odd-row offset:     dx/2 = 30.3109

Center formula:
  cx = 55 + col * 60.6218 + (row % 2) * 30.3109
  cy = 30 + row * 52.5

Grid origin: Row 1, Column 1 (shifted +1 from zero-based indexing).
The first row and column of hexes on the map are water hexes
added for framing. All land hexes start at row 2+ and column 1+.
```

### Adjacency Rules

For even rows (r % 2 == 0), neighbors at:
```
(r-1, c-1)  (r-1, c)
(r,   c-1)  (r,   c+1)
(r+1, c-1)  (r+1, c)
```

For odd rows (r % 2 == 1), neighbors at:
```
(r-1, c)    (r-1, c+1)
(r,   c-1)  (r,   c+1)
(r+1, c)    (r+1, c+1)
```

### Complete Land Hex Registry

| hex_id | display_name | owner | row | col |
|--------|-------------|-------|-----|-----|
| col_nw | Columbia NW | columbia | 5 | 2 |
| col_w | Columbia W | columbia | 6 | 1 |
| col_main_1 | Columbia | columbia | 6 | 2 |
| col_main_2 | Columbia E | columbia | 6 | 3 |
| col_main_3 | Columbia SW | columbia | 7 | 2 |
| col_main_4 | Columbia SE | columbia | 7 | 3 |
| col_south | Columbia S | columbia | 8 | 2 |
| caribe | Caribe | caribe | 10 | 3 |
| thule | Thule | teutonia | 3 | 5 |
| teutonia_1 | Teutonia N | teutonia | 4 | 8 |
| teutonia_2 | Teutonia S | teutonia | 5 | 8 |
| freeland | Freeland | freeland | 5 | 9 |
| albion | Albion | albion | 5 | 6 |
| gallia_1 | Gallia W | gallia | 6 | 7 |
| gallia_2 | Gallia E | gallia | 6 | 8 |
| ponte | Ponte | ponte | 7 | 7 |
| heartland_1 | Heartland N | heartland | 4 | 9 |
| heartland_2 | Heartland S | heartland | 5 | 10 |
| nord_n1 | Nordostan N | nordostan | 2 | 11 |
| nord_w1 | Nordostan W1 | nordostan | 3 | 10 |
| nord_c1 | Nordostan C1 | nordostan | 3 | 11 |
| nord_e1 | Nordostan E1 | nordostan | 3 | 12 |
| nord_e2 | Nordostan E2 | nordostan | 3 | 13 |
| nord_e3 | Nordostan E3 | nordostan | 3 | 14 |
| nord_w2 | Nordostan W2 | nordostan | 4 | 10 |
| nord_c2 | Nordostan C2 | nordostan | 4 | 11 |
| phrygia_1 | Phrygia N | phrygia | 6 | 10 |
| phrygia_2 | Phrygia S | phrygia | 7 | 10 |
| persia_1 | Persia N | persia | 6 | 12 |
| persia_2 | Persia W | persia | 7 | 11 |
| persia_3 | Persia E | persia | 7 | 12 |
| levantia | Levantia | levantia | 7 | 9 |
| solaria_1 | Solaria W | solaria | 8 | 9 |
| solaria_2 | Solaria E | solaria | 8 | 10 |
| horn | Horn | horn | 9 | 9 |
| mirage | Mirage | mirage | 9 | 11 |
| sogdiana_1 | Sogdiana N | sogdiana | 4 | 12 |
| sogdiana_2 | Sogdiana S | sogdiana | 5 | 13 |
| sogdiana_3 | Sogdiana E | sogdiana | 4 | 13 |
| bharata_1 | Bharata S | bharata | 7 | 14 |
| bharata_2 | Bharata N | bharata | 6 | 13 |
| bharata_3 | Bharata E | bharata | 6 | 14 |
| cathay_1 | Cathay NW | cathay | 4 | 14 |
| cathay_2 | Cathay W | cathay | 5 | 15 |
| cathay_3 | Cathay C | cathay | 5 | 16 |
| cathay_4 | Cathay NE | cathay | 5 | 17 |
| cathay_5 | Cathay SW | cathay | 6 | 15 |
| cathay_6 | Cathay SE | cathay | 6 | 16 |
| cathay_7 | Cathay S | cathay | 7 | 16 |
| choson | Choson | choson | 3 | 16 |
| hanguk | Hanguk | hanguk | 4 | 16 |
| formosa | Formosa | formosa | 8 | 17 |
| yamato_1 | Yamato N | yamato | 4 | 19 |
| yamato_2 | Yamato S | yamato | 5 | 19 |

### Chokepoint Hexes

| hex_id | display_name | row | col |
|--------|-------------|-----|-----|
| cp_formosa_strait | Formosa Strait | 7 | 17 |
| cp_gulf_gate | Gulf Gate | 8 | 11 |
| cp_caribe_passage | Caribe Passage | 9 | 3 |

### Complete Land-to-Land Adjacency List

```
col_nw:         col_w, col_main_1
col_w:          col_nw, col_main_1, col_main_3
col_main_1:     col_nw, col_w, col_main_2, col_main_3, col_main_4
col_main_2:     col_main_1, col_main_4
col_main_3:     col_w, col_main_1, col_main_4, col_south
col_main_4:     col_main_1, col_main_2, col_main_3, col_south
col_south:      col_main_3, col_main_4
caribe:         (island, no land adjacency — connected via cp_caribe_passage water)

thule:          (island, no land adjacency)
teutonia_1:     heartland_1, teutonia_2, freeland
teutonia_2:     teutonia_1, freeland, gallia_1, gallia_2
freeland:       teutonia_1, heartland_1, teutonia_2, heartland_2, gallia_2
albion:         (island, no land adjacency)
gallia_1:       teutonia_2, gallia_2, ponte
gallia_2:       teutonia_2, freeland, gallia_1, levantia
ponte:          gallia_1

heartland_1:    teutonia_1, freeland, heartland_2, nord_w1, nord_w2
heartland_2:    heartland_1, freeland, phrygia_1, nord_w2

nord_n1:        nord_c1, nord_e1
nord_w1:        heartland_1, nord_c1, nord_w2
nord_c1:        nord_n1, nord_w1, nord_e1, nord_w2, nord_c2
nord_e1:        nord_n1, nord_c1, nord_e2, nord_c2, sogdiana_1
nord_e2:        nord_e1, nord_e3, sogdiana_1, sogdiana_3
nord_e3:        nord_e2, sogdiana_3, cathay_1
nord_w2:        nord_w1, nord_c1, heartland_1, nord_c2, heartland_2
nord_c2:        nord_c1, nord_e1, nord_w2, sogdiana_1

phrygia_1:      heartland_2, phrygia_2, persia_2
phrygia_2:      phrygia_1, levantia, persia_2, solaria_1, solaria_2
persia_1:       sogdiana_2, bharata_2, persia_3
persia_2:       phrygia_1, phrygia_2, persia_3, solaria_2
persia_3:       persia_1, persia_2
levantia:       gallia_2, phrygia_2, solaria_1
solaria_1:      levantia, phrygia_2, solaria_2, horn
solaria_2:      phrygia_2, persia_2, solaria_1, mirage
horn:           solaria_1
mirage:         solaria_2

sogdiana_1:     nord_e1, nord_e2, nord_c2, sogdiana_3, sogdiana_2
sogdiana_2:     sogdiana_1, sogdiana_3, persia_1, bharata_2
sogdiana_3:     nord_e2, nord_e3, sogdiana_1, cathay_1, sogdiana_2

bharata_1:      bharata_2, bharata_3
bharata_2:      sogdiana_2, persia_1, bharata_3, bharata_1
bharata_3:      bharata_2, cathay_2, cathay_5, bharata_1

cathay_1:       nord_e3, sogdiana_3, cathay_2
cathay_2:       cathay_1, cathay_3, bharata_3, cathay_5
cathay_3:       hanguk, cathay_2, cathay_4, cathay_5, cathay_6
cathay_4:       hanguk, cathay_3, cathay_6
cathay_5:       cathay_2, cathay_3, bharata_3, cathay_6, cathay_7
cathay_6:       cathay_3, cathay_4, cathay_5, cathay_7
cathay_7:       cathay_5, cathay_6

choson:         hanguk
hanguk:         choson, cathay_3, cathay_4

formosa:        (island, no land adjacency — adjacent to cp_formosa_strait water)
yamato_1:       yamato_2
yamato_2:       yamato_1
```

### Country Colors (Canonical)

| Country | Fill | Stroke |
|---------|------|--------|
| Columbia | #D4B896 | #666 |
| Cathay | #E8D5A3 | #666 |
| Nordostan | #D4A5A5 | #666 |
| Heartland | #A5C8A5 | #666 |
| Teutonia | #8FB59A | #666 |
| Freeland | #A5C8D4 | #666 |
| Persia | #C8A57A | #666 |
| Bharata | #D4B5A5 | #666 |
| Yamato | #A5B5C8 | #666 |
| Phrygia | #B5A5C8 | #666 |
| Solaria | #C8B896 | #666 |
| Levantia | #D4A5B5 | #666 |
| Formosa | #8AC8B5 | #666 |
| Gallia | #8FB59A | #666 |
| Ponte | #8AA5B5 | #666 |
| Albion | #D4B58A | #666 |
| Sogdiana | #C8C8A5 | #666 |
| Caribe | #A5C8A0 | #666 |
| Horn | #B5A896 | #666 |
| Mirage | #D4BFA5 | #666 |
| Choson | #8A8A8A | #666 |
| Hanguk | #A5C8D4 | #666 |
| Water | #B5CCE0 | #99AABB |
| Chokepoint border | — | #D4880F (3px) |

---

## Section 2: Sea & Naval Rules

### Addressing

Every hex on the global grid has an address `(row, col)`. Water hexes are addressed solely by grid coordinate — there are NO named sea zones.

Examples:
- `(1,1)` = top-left ocean hex
- `(6,9)` = water hex between Freeland and Levantia
- `(8,12)` = water hex east of Gulf Gate

### Naval Placement

- Naval units can be placed on **any water hex** on the global map.
- Multiple countries' fleets can coexist in the same water hex — no automatic conflict. Combat occurs only when an attack is ordered.
- Naval units project power: they can support adjacent land hexes in combat and interdict sea movement through occupied water hexes.

### Chokepoints (3 Total)

These are the ONLY water hexes with special mechanics:

| Chokepoint | Grid | Mechanic |
|-----------|------|----------|
| Gulf Gate | (8,11) | Blocked while Persia holds ground units on adjacent coast. See Section 5. |
| Formosa Strait | (7,17) | Blockade requires occupying ALL water hexes adjacent to Formosa. See Section 6. |
| Caribe Passage | (9,3) | Controls Atlantic-Pacific transit for Columbia's southern approaches. |

### Formosa Blockade Rule

To blockade Formosa, a fleet must occupy **ALL** water hexes adjacent to the Formosa hex `(8,17)`. The adjacent water hexes are:

```
cp_formosa_strait  (7,17)
sea_7_18           (7,18)
sea_8_16           (8,16)
sea_8_18           (8,18)
sea_9_17           (9,17)
sea_9_18           (9,18)
```

If **even one** adjacent water hex is unoccupied or occupied by a friendly/neutral navy, the blockade is incomplete. An incomplete blockade allows partial supply and reinforcement (50% capacity).

---

## Section 3: Global-to-Theater Conversion

### Expansion Ratio

Each global hex "expands into" approximately 7-8 theater hexes (standard ratio). When a theater activates, units positioned on the corresponding global hex must be placed onto specific theater hexes according to the conversion table below.

### Theater Hex Geometry

Theater maps use the **same hex geometry** as the global map (pointy-top, regular hexagons) but at smaller scale:
- Theater hex side length: s = 25
- Theater hex width: sqrt(3) * 25 = 43.30
- Theater hex height: 2 * 25 = 50
- Row spacing: 1.5 * 25 = 37.5
- Col spacing: sqrt(3) * 25 = 43.30

### Conversion Table

#### Theater: Eastern Ereb

| Global Hex | Global Grid | Theater Hexes |
|-----------|-------------|---------------|
| heartland_1 | (4,9) | ee_front_1, ee_front_2, ee_depth_1, ee_depth_2, ee_capital, ee_west_1, ee_west_2 |
| heartland_2 | (4,10) → (5,10) | ee_front_3, ee_front_4, ee_depth_3, ee_south_1, ee_south_2 |
| nord_w1 | (3,10) | ee_staging_1, ee_staging_2, ee_occupied_1, ee_occupied_2, ee_corridor |
| nord_w2 | (4,10) | ee_staging_3, ee_occupied_3, ee_occupied_4, ee_bastion_approach, ee_peninsula |

**Also mapped:** ee_bastion (disputed, between zones), ee_alliance (NATO border), ee_sea_1, ee_sea_2 (adjacent water)

#### Theater: Mashriq

| Global Hex | Global Grid | Theater Hexes |
|-----------|-------------|---------------|
| persia_2 | (7,11) | ma_interior, ma_highlands |
| persia_3 | (7,12) | ma_coast |
| cp_gulf_gate | (8,11) | ma_gulf_gate |
| solaria_2 | (8,10) | ma_solaria |
| mirage | (9,11) | ma_mirage |
| phrygia_2 | (7,10) | ma_corridor, ma_frontier |
| levantia | (7,9) | ma_levantia |

**Also mapped:** ma_gulf (Gulf waters), ma_southern (southern approach), ma_yemen (proxy zone)

#### Theater: Formosa Strait

| Global Hex | Global Grid | Theater Hexes |
|-----------|-------------|---------------|
| cathay_6 | (6,16) | fs_staging_1 |
| cathay_7 | (7,16) | fs_staging_2 |
| cp_formosa_strait | (7,17) | fs_strait_1, fs_strait_2 |
| formosa | (8,17) | fs_formosa_n, fs_formosa_s |

**Also mapped:** fs_east_sea, fs_south_sea, fs_channel (adjacent waters for intervention routes)

### Deployment Rules

When a theater activates:

1. **Owned territory:** Units on a global hex deploy to any theater hex that hex expands into, at the controlling player's choice.
2. **Contested/occupied:** Units on contested or occupied theater hexes stay where they are (already deployed from game start or prior turns).
3. **Reinforcement:** New units entering from the global map must enter at a theater-edge hex adjacent to the global hex they came from.
4. **Supply:** Supply traces from a theater-edge hex back to the global map. If the connecting global hex is cut off, all theater hexes from that global hex are unsupplied.

---

## Section 4: Theater — Eastern Ereb (23 hexes)

**Expands:** heartland_1, heartland_2, nord_w1, nord_w2 (plus border/sea hexes)
**Canvas:** 900 x 600
**Status:** Active at game start

### Hex Grid Layout

Pointy-top hexagons, s=25. Grid uses (row, col) with odd-row right offset.

| hex_id | display_name | type | owner | grid (r,c) |
|--------|-------------|------|-------|------------|
| ee_staging_1 | Staging North | land | nordostan | (1,5) |
| ee_staging_2 | Staging Central | land | nordostan | (2,5) |
| ee_staging_3 | Staging South | land | nordostan | (3,5) |
| ee_occupied_1 | Occupied NW | land_occupied | nordostan | (2,4) |
| ee_occupied_2 | Occupied NE | land_occupied | nordostan | (1,4) |
| ee_occupied_3 | Occupied SW | land_occupied | nordostan | (3,4) |
| ee_occupied_4 | Occupied SE | land_occupied | nordostan | (4,5) |
| ee_bastion_approach | Bastion Approach | land | nordostan | (3,3) |
| ee_bastion | The Bastion | land_fortified | heartland | (4,4) |
| ee_front_1 | Front North | land | heartland | (3,2) |
| ee_front_2 | Front West | land | heartland | (4,3) |
| ee_front_3 | Front South | land | heartland | (5,3) |
| ee_front_4 | Front East | land | heartland | (5,4) |
| ee_depth_1 | River Line North | land | heartland | (4,2) |
| ee_depth_2 | River Line Central | land | heartland | (5,2) |
| ee_depth_3 | River Line South | land | heartland | (6,2) |
| ee_capital | The Capital | land | heartland | (5,1) |
| ee_west_1 | Western Corridor | land | heartland | (4,1) |
| ee_west_2 | Western Supply | land | heartland | (6,1) |
| ee_south_1 | Southern Sector | land | heartland | (7,2) |
| ee_south_2 | Southern Flank | land | heartland | (7,3) |
| ee_corridor | Northern Flank | land | nordostan | (1,3) |
| ee_peninsula | Naval Base | land_occupied | nordostan | (6,5) |
| ee_sea_1 | Southern Sea W | sea | neutral | (7,4) |
| ee_sea_2 | Southern Sea E | sea | neutral | (7,5) |
| ee_alliance | Alliance Border | land | alliance | (4,0) |

**Total: 26 hexes** (8 Nordostan + 1 Bastion + 12 Heartland + 1 corridor + 1 peninsula + 2 sea + 1 alliance)

### Adjacency List (Theater)

```
ee_corridor:          ee_staging_1, ee_occupied_2, ee_front_1
ee_staging_1:         ee_corridor, ee_occupied_2, ee_staging_2
ee_staging_2:         ee_staging_1, ee_occupied_2, ee_occupied_1, ee_staging_3
ee_staging_3:         ee_staging_2, ee_occupied_1, ee_occupied_3, ee_bastion_approach
ee_occupied_1:        ee_staging_2, ee_staging_3, ee_occupied_2, ee_occupied_3
ee_occupied_2:        ee_corridor, ee_staging_1, ee_staging_2, ee_occupied_1
ee_occupied_3:        ee_staging_3, ee_occupied_1, ee_occupied_4, ee_bastion_approach, ee_bastion
ee_occupied_4:        ee_occupied_3, ee_bastion, ee_front_4, ee_peninsula
ee_bastion_approach:  ee_staging_3, ee_occupied_3, ee_bastion, ee_front_1, ee_front_2
ee_bastion:           ee_bastion_approach, ee_occupied_3, ee_occupied_4, ee_front_2, ee_front_3, ee_front_4
ee_front_1:           ee_corridor, ee_bastion_approach, ee_front_2, ee_depth_1, ee_west_1
ee_front_2:           ee_bastion_approach, ee_bastion, ee_front_1, ee_front_3, ee_depth_1, ee_depth_2
ee_front_3:           ee_bastion, ee_front_2, ee_front_4, ee_depth_2, ee_depth_3
ee_front_4:           ee_bastion, ee_occupied_4, ee_front_3, ee_south_2, ee_peninsula
ee_depth_1:           ee_front_1, ee_front_2, ee_west_1, ee_depth_2, ee_capital
ee_depth_2:           ee_front_2, ee_front_3, ee_depth_1, ee_depth_3, ee_capital
ee_depth_3:           ee_front_3, ee_depth_2, ee_west_2, ee_south_1
ee_capital:           ee_depth_1, ee_depth_2, ee_west_1, ee_west_2
ee_west_1:            ee_front_1, ee_depth_1, ee_capital, ee_alliance
ee_west_2:            ee_capital, ee_depth_3, ee_south_1
ee_south_1:           ee_depth_3, ee_west_2, ee_south_2
ee_south_2:           ee_south_1, ee_front_4, ee_sea_1
ee_alliance:          ee_west_1
ee_peninsula:         ee_occupied_4, ee_front_4, ee_sea_2
ee_sea_1:             ee_south_2, ee_sea_2
ee_sea_2:             ee_sea_1, ee_peninsula
```

### The Front Line

The active front line runs between the Nordostan-controlled hexes (occupied_*, bastion_approach) and the Heartland-controlled hexes (front_*, bastion). Shown as a **red dashed line** on the SVG.

Specifically, the front line edges are between:
- ee_corridor / ee_front_1
- ee_bastion_approach / ee_front_1
- ee_bastion_approach / ee_front_2
- ee_occupied_3 / ee_bastion
- ee_occupied_4 / ee_bastion
- ee_occupied_4 / ee_front_4

### Special Hexes

| Hex | Mechanic |
|-----|----------|
| ee_bastion | **Fortified:** +1 to defender dice. THE strategic prize. Nordostan claims it; Heartland defends it as existential. |
| ee_alliance | **Article 5:** Any attack triggers Alliance collective defense. Untouchable. Functions as supply entry for Western aid to Heartland. |
| ee_corridor | **Northern Flank:** Allows Nordostan to threaten a bypass attack toward the capital. Uncommitted but constant threat. |
| ee_peninsula | **Occupied Naval Base:** Nordostan-controlled. Provides naval projection into theater sea hexes. |
| ee_capital | **Political Center:** Star marker. Loss triggers severe stability penalty for Heartland. |

### Supply Corridors

- **Heartland supply:** ee_alliance -> ee_west_1 -> ee_capital -> ee_depth_* -> ee_front_*
- **Nordostan supply:** Off-map (north edge) -> ee_staging_* -> ee_occupied_* -> front

---

## Section 5: Theater — Mashriq (12 hexes)

**Expands:** persia_2, persia_3, cp_gulf_gate, solaria_2, mirage, phrygia_2, levantia
**Canvas:** 700 x 500
**Status:** Active at game start

### Hex Grid Layout

| hex_id | display_name | type | owner | grid (r,c) |
|--------|-------------|------|-------|------------|
| ma_levantia | Levantia | land | levantia | (1,1) |
| ma_corridor | The Corridor | land | neutral | (2,1) |
| ma_frontier | The Frontier | land | neutral | (2,2) |
| ma_interior | The Interior | land | persia | (1,2) |
| ma_highlands | The Highlands | land_mountain | persia | (2,3) |
| ma_coast | The Coast | land | persia | (3,3) |
| ma_gulf_gate | Gulf Gate | sea_chokepoint | neutral | (3,4) |
| ma_gulf | Gulf Waters | sea | neutral | (4,4) |
| ma_solaria | Solaria | land | solaria | (4,3) |
| ma_mirage | Mirage | land | mirage | (4,5) |
| ma_southern | Southern Waters | sea | neutral | (4,2) |
| ma_yemen | Southern Gate | land | persia_proxy | (5,2) |

**Total: 12 hexes**

### Adjacency List

```
ma_levantia:    ma_corridor, ma_interior
ma_corridor:    ma_levantia, ma_frontier
ma_frontier:    ma_corridor, ma_highlands, ma_interior
ma_interior:    ma_levantia, ma_frontier, ma_highlands
ma_highlands:   ma_frontier, ma_interior, ma_coast
ma_coast:       ma_highlands, ma_gulf_gate, ma_gulf, ma_southern
ma_gulf_gate:   ma_coast, ma_gulf, ma_solaria, ma_mirage
ma_gulf:        ma_coast, ma_gulf_gate, ma_solaria, ma_mirage, ma_southern
ma_solaria:     ma_gulf_gate, ma_gulf, ma_mirage
ma_mirage:      ma_gulf_gate, ma_gulf, ma_solaria
ma_southern:    ma_coast, ma_gulf, ma_yemen
ma_yemen:       ma_southern
```

### Gulf Gate Blockade Mechanic

The Gulf Gate (`ma_gulf_gate`) is **blocked as long as Persia has ground units on The Coast (`ma_coast`)**. Ground-based anti-ship missiles and coastal defenses make the chokepoint impervious to naval or air attacks alone.

To reopen the gate:
1. **Ground invasion:** ma_corridor -> ma_frontier -> ma_highlands -> ma_coast
2. **Amphibious assault:** From ma_gulf onto ma_coast (requires 4:1 ratio)
3. **Combined arms:** Simultaneous ground + amphibious relaxes ratio to 2:1

The Highlands (`ma_highlands`) imposes **-1 combat modifier on attackers** (mountain terrain).

### Special Hexes

| Hex | Mechanic |
|-----|----------|
| ma_interior | Nuclear sites. Strikes risk escalation. If Persia achieves breakout, theater dynamics shift. |
| ma_highlands | Mountain terrain: -1 attacker modifier. |
| ma_coast | Anti-ship missile battery. While held by Persia, Gulf Gate is blocked. |
| ma_gulf_gate | Chokepoint. Orange border. Controlled by ma_coast ground presence. |
| ma_levantia | Independent strike capability. Undeclared nuclear arsenal. Separate escalation vector. |
| ma_yemen | Proxy-controlled. Second chokepoint equivalent. Can harass shipping in Southern Waters. |
| ma_solaria / ma_mirage | Oil infrastructure. Combat here risks oil disruption events affecting global economy. |

---

## Section 6: Theater — Formosa Strait (9 hexes)

**Expands:** cathay_6, cathay_7, cp_formosa_strait, formosa
**Canvas:** 700 x 500
**Status:** Activates on escalation

### Hex Grid Layout

| hex_id | display_name | type | owner | grid (r,c) |
|--------|-------------|------|-------|------------|
| fs_staging_1 | Northern Staging | land | cathay | (1,1) |
| fs_staging_2 | Southern Staging | land | cathay | (2,1) |
| fs_strait_1 | Northern Strait | sea | neutral | (1,2) |
| fs_strait_2 | Southern Strait | sea_chokepoint | neutral | (2,2) |
| fs_formosa_n | Formosa North | land | formosa | (1,3) |
| fs_formosa_s | Formosa South | land | formosa | (2,3) |
| fs_east_sea | Eastern Waters | sea | neutral | (1,4) |
| fs_south_sea | Southern Sea | sea | neutral | (3,2) |
| fs_channel | The Channel | sea | neutral | (3,3) |

**Total: 9 hexes**

### Adjacency List

```
fs_staging_1:   fs_staging_2, fs_strait_1, fs_strait_2
fs_staging_2:   fs_staging_1, fs_strait_2, fs_south_sea
fs_strait_1:    fs_staging_1, fs_strait_2, fs_formosa_n
fs_strait_2:    fs_staging_1, fs_staging_2, fs_strait_1, fs_formosa_s, fs_south_sea, fs_channel
fs_formosa_n:   fs_strait_1, fs_formosa_s, fs_east_sea
fs_formosa_s:   fs_strait_2, fs_formosa_n, fs_east_sea, fs_channel
fs_east_sea:    fs_formosa_n, fs_formosa_s, fs_channel
fs_south_sea:   fs_staging_2, fs_strait_2, fs_channel
fs_channel:     fs_strait_2, fs_formosa_s, fs_east_sea, fs_south_sea
```

### Formosa Blockade Mechanic

To declare a **complete blockade** of Formosa, Cathay must occupy **all 4 water hexes** adjacent to Formosa:

```
fs_strait_1    (Northern Strait)
fs_strait_2    (Southern Strait — chokepoint)
fs_east_sea    (Eastern Waters)
fs_south_sea   (Southern Sea) — adjacent via fs_channel
```

Actually, blockade requires occupation of the water hexes **directly adjacent to Formosa hexes**:
- Adjacent to fs_formosa_n: fs_strait_1, fs_east_sea
- Adjacent to fs_formosa_s: fs_strait_2, fs_east_sea, fs_channel

So complete blockade requires: **fs_strait_1 + fs_strait_2 + fs_east_sea + fs_channel** (all 4 water hexes touching Formosa). Missing even one = blockade is leaky (50% supply gets through).

### Amphibious Assault

Crossing the strait from any Cathay staging hex to any Formosa hex requires **4:1 force ratio**. Naval superiority in at least one strait hex is a prerequisite — Cathay must control fs_strait_1 or fs_strait_2 before landing.

### Special Hexes

| Hex | Mechanic |
|-----|----------|
| fs_formosa_n | Semiconductor fabs. Combat here risks destruction (roll each combat round). Destruction = -2 global economic stability for ALL nations. |
| fs_strait_2 | Chokepoint. Orange border. Controls southern maritime access. |
| fs_east_sea | Columbia/Yamato intervention entry point. Pre-positioned forces (2 naval, 1 air Columbia). |
| fs_channel | Southern passage connecting strait to eastern sea. Key interdiction point. |

### Intervention Rules

- **Columbia:** 2 naval + 1 air pre-positioned in fs_east_sea (routine Pacific deployment). Can intervene immediately on declaration. Additional forces enter via fs_east_sea from global map.
- **Yamato:** Forces enter via fs_east_sea. Independent reinforcement decision.
- **Cathay reinforcement:** Can reinforce through fs_south_sea from global map's South China Sea region.

---

## Appendix: Cross-Reference

### Which global hexes feed each theater?

| Theater | Global Hexes | Activation |
|---------|-------------|------------|
| Eastern Ereb | heartland_1, heartland_2, nord_w1, nord_w2 | Game start |
| Mashriq | persia_2, persia_3, cp_gulf_gate, solaria_2, mirage, phrygia_2, levantia | Game start |
| Formosa Strait | cathay_6, cathay_7, cp_formosa_strait, formosa | On escalation |

### Non-theater global hexes

All other global hexes remain at global resolution. Units on these hexes interact via the global adjacency list. If a new theater is needed (e.g., Korean Peninsula, Caribe), the same expansion ratio (~7-8 theater hexes per global hex) applies.
