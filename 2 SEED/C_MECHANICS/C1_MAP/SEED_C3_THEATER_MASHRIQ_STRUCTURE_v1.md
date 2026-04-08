# Mashriq Theater Map — Structure
## Thucydides Trap SIM — SEED Specification
**Version:** 1.0 | **Date:** 2026-03-31 | **Status:** Active

---

## Overview

The Mashriq (Middle East/Persian Gulf) theater map provides tactical depth for the Persia war — the longest-running active conflict in the SIM. Active by default at game start (Gulf Gate blockade, Columbia-Levantia strikes ongoing).

**Grid:** 10 columns × 10 rows pointy-top hexagons
**Countries:** Persia (51 hexes), Mirage (8), Phrygia (6), Solaria (5) = **70 land hexes**
**Water hexes:** Gulf waters between coastal areas (for naval positioning and Gulf Gate blockade)

---

## Global-to-Local Mapping

Each global hex maps to specific local theater hexes:

| Global Hex | Global ID | Local Theater Hexes | Notes |
|-----------|-----------|-------------------|-------|
| Solaria (11,7) | solaria_1/solaria_2 | solaria_1 through solaria_5 (all Solaria on local map) | Western coast, oil infrastructure |
| Mirage (11,8) | mirage | mirage_1 through mirage_8 (all Mirage on local map) | Southern Gulf coast, financial hub |
| Persia (13,7) | persia_1 | persia_1 through persia_22 (rows 0,1,2 of local map) | Northern Persia — inland, mountainous |
| Persia (13,8) | persia_2 | persia_23 through persia_39 (rows 3,4,5 of local map) | Central Persia — nuclear sites, industrial |
| Persia (12,7) | persia_3 | persia_40 through persia_51 (rows 6,7,8,9 of local map) | Southern Persia — Gulf coast, blockade zone |
| Phrygia (11,6) | phrygia_1/phrygia_2 | phrygia_1 through phrygia_6 (all Phrygia on local map) | Northern border, NATO territory |

**Aggregation rule:** When displaying on the global map, all military units on local theater hexes that map to a given global hex are consolidated and shown as a single aggregate count on that global hex.

---

## Strategic Geography

**The Gulf Gate blockade zone:** Southern Persia coast (persia_40 through persia_51) faces the Gulf waters. Persia's coastal missile batteries and ground forces here control the Gulf Gate. Breaking the blockade requires:
1. Naval bombardment from Gulf waters (10% per ship per round — slow)
2. Air strikes on coastal positions (subject to AD interception)
3. Ground invasion through either:
   - Phrygia border (north — long march through all of Persia)
   - Amphibious assault from Gulf (south — requires naval superiority + 3:1 ratio)
   - Mirage border (south — if Mirage allows basing rights)

**Persia's depth:** 51 hexes. An invading force from the south must cross ~5-6 rows of Persia territory to reach the northern industrial/nuclear zones. Each row is a defensive line. This is why ground invasion of Persia is extremely difficult — the country has strategic depth.

**Nuclear sites:** Located in central Persia (rows 3-5, approximately persia_23 through persia_39). Reachable by strategic missiles (global range) or air strikes (from adjacent theater hexes) but defended by terrain depth.

**Phrygia's position:** Northern border. NATO territory. If Phrygia allows basing rights, it provides the closest staging area for a ground invasion. But Phrygia (Vizier) plays all sides — basing rights for Columbia would end Phrygia's neutrality.

**Solaria's vulnerability:** Western coast, 5 hexes. Oil infrastructure. Under missile attack from Persia. Defended but exposed — the economic target.

**Mirage's position:** Southern Gulf coast, 8 hexes. Financial hub. Under drone/missile attack. Closest non-hostile territory to Persia's Gulf coast — potential staging area for amphibious operations.

---

## Theater Activation

**Active by default at game start.** The Persia war (Operation Epic Fury + Operation Rising Lion) is ongoing from R1. Gulf Gate blockade is active. Columbia air strikes are in progress. Units should be deployed on this theater map from the start.

Unlike the Eastern Ereb theater (which shows the Sarmatia-Ruthenia front), the Mashriq theater shows a DIFFERENT kind of war: not a grinding front line, but a blockade + air campaign + potential ground invasion scenario.

---

## Hex Registry

### Persia (51 hexes)

| hex_id | row | col | Strategic notes |
|--------|:---:|:---:|----------------|
| persia_1 to persia_7 | 0 | 3-9 | Northern border — mountainous, defensible |
| persia_8 to persia_15 | 1 | 2-9 | Northern interior |
| persia_16 to persia_22 | 2 | 3-9 | Northern approaches |
| persia_23 to persia_29 | 3 | 3-9 | Central — nuclear sites, industrial |
| persia_30 to persia_34 | 4 | 5-9 | Central-south — strategic depth |
| persia_35 to persia_39 | 5 | 5-9 | South-central |
| persia_40 to persia_43 | 6 | 6-9 | Gulf approaches |
| persia_44 to persia_47 | 7 | 5,7-9 | Coastal — Gulf Gate blockade zone |
| persia_48 to persia_51 | 8-9 | 8-9 | Southern tip — Hormuz area |

### Solaria (5 hexes)

| hex_id | row | col | Notes |
|--------|:---:|:---:|-------|
| solaria_1 | 3 | 0 | Northern Solaria |
| solaria_2 | 4 | 0 | Oil infrastructure zone |
| solaria_3 | 5 | 0 | Central |
| solaria_4 | 6 | 0 | Southern |
| solaria_5 | 7 | 0 | Gulf coast — adjacent to Mirage |

### Mirage (8 hexes)

| hex_id | row | col | Notes |
|--------|:---:|:---:|-------|
| mirage_1 to mirage_3 | 8 | 0-2 | Northern Mirage |
| mirage_4 to mirage_8 | 9 | 0-4 | Southern Mirage — financial hub, ports |

### Phrygia (6 hexes)

| hex_id | row | col | Notes |
|--------|:---:|:---:|-------|
| phrygia_1 to phrygia_3 | 0 | 0-2 | Northern Phrygia — NATO territory |
| phrygia_4 to phrygia_5 | 1 | 0-1 | Central |
| phrygia_6 | 2 | 0 | Southern — border with Solaria |

---

## Files

| File | Content |
|------|---------|
| `SEED_C3_THEATER_MASHRIQ_STATE_v1.json` | Hex map state (from map editor) |
| `SEED_C3_THEATER_MASHRIQ_v1.svg` | Visual map export |
| `SEED_C3_THEATER_MASHRIQ_STRUCTURE_v1.md` | This document |

---

## Addendum: Template v1.0 — 2026-04-05

**Canonical source:** `SEED_C_MAP_UNITS_MASTER_v1.md`

### Canonical Global Linkage (replaces the provisional §"Global-to-Local Mapping" above)

All coordinates below are **`(row, col)`, 1-indexed, global grid 10×20**. Theater rows below are also 1-indexed (previous text used 0-indexed row 0..9; canonical is 1..10).

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

### Persia row split rationale

Persia has 10 rows of depth on this theater. Splitting by row bands gives three distinct global hexes for invading-force progress tracking:
- **rows 1-3 → (6,12):** Northern Persia (mountainous, defensible — approaches from Phrygia).
- **rows 4-6 → (7,13):** Central Persia (nuclear sites, industrial — the prize).
- **rows 7-10 → (8,13):** Southern Persia (Gulf coast, blockade zone, Hormuz).

### Sea split rationale

Mashriq sea cells represent Gulf waters. Northern half (rows 3-6) aggregates to (7,12) = the "mid-Gulf" global hex. Southern half (rows 7-10) aggregates to (8,12) = the Gulf Gate chokepoint hex.

### JSON state file update

The companion `SEED_C3_THEATER_MASHRIQ_STATE_v1.json` has been updated to carry a `global_link: "row,col"` field on every cell per the table above (backup preserved as `.bak_pre_global_link`).

Addendum: Template v1.0 — 2026-04-05
