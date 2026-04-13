# DET — Map System (Engineering Spec)

**Version:** 1.0 | **Status:** Active | **Date:** 2026-04-13
**Bridges:** SEED_C_MAP_UNITS_MASTER_v1.md (design) -> code implementation
**Sufficient to:** build a map editor or alternative renderer from scratch

---

## 1. PURPOSE

This document captures the complete engineering specification of the TTT map system as implemented in code. It extracts every formula, constant, data schema, and algorithm from the actual codebase so that a developer can build a map editor, alternative renderer, or migration tool purely from this document plus the SEED references it cites.

**Canonical code files:**
- Python constants: `app/engine/config/map_config.py`
- JS constants: `app/test-interface/static/map_config.js`
- Renderer + editor: `app/test-interface/static/map.js`
- API server: `app/test-interface/server.py`

---

## 2. HEX GEOMETRY SPECIFICATION

### 2.1 Orientation

**Pointy-top hexagons** with **odd-row offset** (odd rows shift right by half a hex width).

### 2.2 Core Constants

| Constant | Value | Usage |
|---|---|---|
| `HEX_R_GLOBAL` | 34 px | Circumradius for global map hexes |
| `HEX_R_THEATER` | 40 px | Circumradius for theater map hexes |
| `PAD` | 60 px | Padding around the hex grid on all sides |

### 2.3 Hex Center Calculation: `hexCenter(row, col, r)`

Given a 0-indexed grid position `(row, col)` and circumradius `r`, the pixel center of the hex is:

```
w = sqrt(3) * r          // horizontal distance between hex centers
h = 1.5 * r              // vertical distance between hex centers
xOffset = w / 2   if row is odd (row % 2 == 1)
         0        if row is even

cx = PAD + col * w + xOffset + w / 2
cy = PAD + row * h + r
```

**Language-agnostic pseudocode:**

```pseudocode
function hexCenter(row, col, r):
    w = sqrt(3) * r
    h = 1.5 * r
    xOffset = (row % 2 == 1) ? w / 2 : 0
    return {
        x: PAD + col * w + xOffset + w / 2,
        y: PAD + row * h + r
    }
```

**Important:** `row` and `col` in this function are **0-indexed** (array indices). The display convention is 1-indexed. When rendering hex (display_row, display_col), call `hexCenter(display_row - 1, display_col - 1, r)`.

### 2.4 Hex Vertices: `hexPoints(cx, cy, r)`

Six vertices of a pointy-top hex centered at `(cx, cy)` with circumradius `r`:

```pseudocode
function hexPoints(cx, cy, r):
    points = []
    for i in 0..5:
        angle_deg = 60 * i - 30
        angle_rad = PI / 180 * angle_deg
        points.append(cx + r * cos(angle_rad), cy + r * sin(angle_rad))
    return points
```

The `-30` offset makes vertex 0 point upper-right (pointy-top orientation). The six vertices are at angles -30, 30, 90, 150, 210, 270 degrees from the positive x-axis.

### 2.5 Canvas/SVG Sizing

For a grid of `rows` x `cols` hexes:

```
canvas_width  = PAD * 2 + cols * w + w / 2
canvas_height = PAD * 2 + rows * h + r * 0.5
```

Where `w = sqrt(3) * r` and `h = 1.5 * r`.

The SVG `viewBox` is set to `0 0 canvas_width canvas_height`. Coordinate origin is top-left.

### 2.6 Pixel to Hex (inverse)

Not explicitly implemented in the current renderer (click detection uses SVG `data-row`/`data-col` attributes on polygon elements). For a standalone implementation:

```pseudocode
function pixelToHex(px, py, r):
    w = sqrt(3) * r
    h = 1.5 * r
    // Approximate row from y
    row_approx = (py - PAD - r) / h
    row = round(row_approx)
    // Adjust x for offset
    xOffset = (row % 2 == 1) ? w / 2 : 0
    col_approx = (px - PAD - xOffset - w / 2) / w
    col = round(col_approx)
    return (row, col)  // 0-indexed
```

This is an approximation. For precise hit-testing, compute the distance from the click point to each candidate hex center and select the nearest.

### 2.7 Adjacency (Odd-Row Offset, Pointy-Top)

For a hex at 0-indexed `(row, col)`:

```pseudocode
if row is odd:
    neighbors = [(-1, 0), (-1, +1), (0, -1), (0, +1), (+1, 0), (+1, +1)]
if row is even:
    neighbors = [(-1, -1), (-1, 0), (0, -1), (0, +1), (+1, -1), (+1, 0)]
```

Each tuple is `(delta_row, delta_col)`. Neighbor = `(row + dr, col + dc)`. Filter out-of-bounds results.

---

## 3. COORDINATE SYSTEM

### 3.1 Canonical Convention (LOCKED)

**`(row, col)` -- row first, col second. Both 1-indexed.**

- `row` = vertical position from top (1 = top row)
- `col` = horizontal position from left (1 = leftmost)

This applies everywhere: CSV columns, API payloads, prompt contexts, renderer helpers, SEED tables.

### 3.2 Bounds

| Map | Row range | Col range |
|---|---|---|
| Global | [1, 10] | [1, 20] |
| Eastern Ereb (theater) | [1, 10] | [1, 10] |
| Mashriq (theater) | [1, 10] | [1, 10] |

### 3.3 Representations by Language

**Python (map_config.py):** Tuples `(row, col)` -- e.g., `(3, 12)`. Dict keys: `(int, int)`.

**JavaScript (map_config.js):** Arrays `[row, col]` -- e.g., `[3, 12]`. String keys in lookup dicts: `"3,12"`.

**API (JSON):** Objects `{"row": 3, "col": 12}` or flat fields `{"global_row": 3, "global_col": 12}`.

**CSV:** Separate columns `global_row`, `global_col`, `theater_row`, `theater_col`.

### 3.4 Bounds Validation

```python
# Python
def in_global_bounds(row: int, col: int) -> bool:
    return 1 <= row <= 10 and 1 <= col <= 20

def in_theater_bounds(theater: str, row: int, col: int) -> bool:
    t = THEATERS.get(theater)
    if not t: return False
    return 1 <= row <= t["rows"] and 1 <= col <= t["cols"]
```

```javascript
// JavaScript
inGlobalBounds: function(row, col) {
    return row >= 1 && row <= 10 && col >= 1 && col <= 20;
},
inTheaterBounds: function(theater, row, col) {
    var t = this.THEATERS[theater];
    if (!t) return false;
    return row >= 1 && row <= t.rows && col >= 1 && col <= t.cols;
}
```

### 3.5 JSON 0-Indexed Arrays vs 1-Indexed Display

The SEED JSON files (`SEED_C1_MAP_GLOBAL_STATE_v4.json`, theater JSONs) store grids as nested arrays (0-indexed). The embedded `_coordinate_convention` field documents this:

> Grid arrays are 0-indexed. Display coordinates are 1-indexed. `display_row = array_row + 1`, `display_col = array_col + 1`.

Chokepoint and die-hard coordinates within the JSON are also 0-indexed. When displaying or using them in the 1-indexed coordinate system, add 1 to both row and col.

---

## 4. THEATER-GLOBAL LINKAGE

### 4.1 Concept

Every theater cell aggregates up to exactly one global hex. The mapping is determined by the **theater name**, the **cell owner**, and sometimes the **theater row**. This mapping is part of the Template and is immutable per template version.

### 4.2 Complete Linkage Table

#### Eastern Ereb -> Global

| Theater cell condition | Global hex (row, col) |
|---|:---:|
| `owner = sarmatia`, theater row 1-4 | (3, 12) |
| `owner = sarmatia`, theater row 5+ | (4, 12) |
| `owner = ruthenia` (any row) | (4, 11) |
| `owner = sea` (any) | (5, 12) |

#### Mashriq -> Global

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

### 4.3 `globalHexForTheaterCell()` Algorithm

**Python canonical implementation** (`map_config.py`):

```python
def global_hex_for_theater_cell(
    theater: str,
    theater_row: int,
    theater_col: int,
    cell_owner: Optional[str],
) -> Optional[tuple[int, int]]:
    if cell_owner is None:
        return None
    if theater == "eastern_ereb":
        if cell_owner == "sea":       return (5, 12)
        if cell_owner == "sarmatia":  return (3, 12) if theater_row <= 4 else (4, 12)
        if cell_owner == "ruthenia":  return (4, 11)
        return None
    if theater == "mashriq":
        if cell_owner == "phrygia":   return (6, 11)
        if cell_owner == "solaria":   return (7, 11)
        if cell_owner == "mirage":    return (8, 11)
        if cell_owner == "persia":
            if theater_row <= 3:      return (6, 12)
            if theater_row <= 6:      return (7, 13)
            return (8, 13)
        if cell_owner == "sea":
            if 3 <= theater_row <= 6: return (7, 12)
            if 7 <= theater_row <= 10: return (8, 12)
            return None
        return None
    return None
```

**JS mirror** (`map_config.js`): Identical logic, returns `[row, col]` array or `null`.

**JS renderer wrapper** (`map.js`): The renderer resolves `cell_owner` automatically from the theater grid state before calling `MAP_CONFIG.globalHexForTheaterCell()`:

```javascript
function globalHexForTheaterCell(theater, trow, tcol) {
    var tData = state.theaters[theater];
    var owner = null;
    if (tData && tData.grid && tData.grid[trow - 1] && tData.grid[trow - 1][tcol - 1]) {
        owner = tData.grid[trow - 1][tcol - 1].owner;
    }
    return window.MAP_CONFIG.globalHexForTheaterCell(theater, trow, tcol, owner);
}
```

### 4.4 Static Theater-Link Hex Registry

All global hexes that carry a theater link (pre-computed, manually enumerated):

```python
_THEATER_LINK_HEXES = {
    # Eastern Ereb
    (3, 12): "eastern_ereb",
    (4, 12): "eastern_ereb",
    (4, 11): "eastern_ereb",
    (5, 12): "eastern_ereb",
    # Mashriq
    (6, 11): "mashriq",
    (7, 11): "mashriq",
    (8, 11): "mashriq",
    (6, 12): "mashriq",
    (7, 13): "mashriq",
    (8, 13): "mashriq",
    (7, 12): "mashriq",
    (8, 12): "mashriq",
}
```

**JS equivalent** uses string keys: `"3,12": "eastern_ereb"`, etc.

### 4.5 Lookup Functions

| Function | Python | JS | Returns |
|---|---|---|---|
| Is this global hex a theater link? | `is_theater_link_hex(row, col)` | `MAP_CONFIG.isTheaterLinkHex(row, col)` | `bool` |
| Which theater does this global hex belong to? | `theater_for_global_hex(row, col)` | `MAP_CONFIG.theaterForGlobalHex(row, col)` | `str` or `None`/`null` |
| Get all theater-link hexes | `theater_link_hexes()` | `MAP_CONFIG.theaterLinkHexes()` | `dict` (copy) |

### 4.6 Dynamic Theater-Link Discovery

The renderer builds a dynamic theater-link index by iterating all theater cells and calling `globalHexForTheaterCell()` for each. This guarantees that visual badges and drill-down behavior match the canonical mapping:

```javascript
function buildGlobalTheaterLinks() {
    var links = {};
    MAP_CONFIG.THEATER_NAMES.forEach(function(theater) {
        var t = state.theaters[theater];
        if (!t || !t.grid) return;
        for (var ri = 0; ri < t.rows; ri++) {
            for (var ci = 0; ci < t.cols; ci++) {
                var g = globalHexForTheaterCell(theater, ri + 1, ci + 1);
                if (g) links[g[0] + "," + g[1]] = theater;
            }
        }
    });
    return links;
}
```

---

## 5. MAP DATA SCHEMA

### 5.1 Global Map JSON Schema

**Source file:** `2 SEED/C_MECHANICS/C1_MAP/SEED_C1_MAP_GLOBAL_STATE_v4.json`

```json
{
  "version": 2,
  "rows": 10,
  "cols": 20,
  "countries": {
    "<country_code>": {
      "name": "<Display Name>",
      "color": "<#RRGGBB>"
    }
  },
  "grid": [
    // 10 rows, each containing 20 hex objects (0-indexed arrays)
    [
      { "owner": "<country_code or 'sea'>" },
      { "owner": "sea" }
      // ... 20 entries per row
    ]
    // ... 10 rows
  ],
  "chokepoints": {
    "<chokepoint_id>": {
      "row": <int, 0-indexed>,
      "col": <int, 0-indexed>,
      "name": "<Display Name>"
    }
  },
  "dieHards": {},
  "dieHardDefs": [
    { "key": "<die_hard_id>", "name": "<Display Name>" }
  ],
  "_coordinate_convention": "0-indexed arrays. display = array + 1."
}
```

**Chokepoints (Template v1.0):**

| Key | 0-indexed (row, col) | 1-indexed (row, col) | Display Name |
|---|---|---|---|
| `formosa_strait` | (6, 16) | (7, 17) | Formosa Strait |
| `gulf_gate` | (7, 11) | (8, 12) | Gulf Gate |
| `caribe_passage` | (7, 3) | (8, 4) | Caribe Passage |

**Note:** The global JSON `countries` block includes colors, but the renderer uses the palette from the `/api/map/countries` endpoint instead (which provides separate `map`, `ui`, and `light` color tiers).

### 5.2 Theater Map JSON Schema

**Source files:**
- `SEED_C3_THEATER_EASTERN_EREB_STATE_v3.json`
- `SEED_C3_THEATER_MASHRIQ_STATE_v1.json`

```json
{
  "version": 2,
  "rows": 10,
  "cols": 10,
  "countries": {
    "<country_code>": {
      "name": "<Display Name>",
      "color": "<#RRGGBB>"
    }
  },
  "grid": [
    // 10 rows, each containing 10 hex objects
    [
      {
        "owner": "<country_code or 'sea'>",
        "occupied_by": "<country_code or null>",
        "global_link": "<legacy col,row string>"
      }
    ]
  ],
  "chokepoints": {},
  "dieHards": {
    "<die_hard_id>": {
      "row": <int, 0-indexed>,
      "col": <int, 0-indexed>,
      "name": "<Display Name>"
    }
  },
  "dieHardDefs": [
    { "key": "<die_hard_id>", "name": "<Display Name>" }
  ],
  "_coordinate_convention": "0-indexed arrays. display = array + 1."
}
```

**Per-hex fields (theater):**

| Field | Type | Required | Notes |
|---|---|---|---|
| `owner` | string | yes | Country code or `"sea"` |
| `occupied_by` | string/null | no | Another country controlling this cell. Must differ from `owner`. |
| `global_link` | string | no | Legacy `"col,row"` format. Frozen in existing JSONs. New data uses `(row,col)`. |

**Die-Hards (Template v1.0):**

| Theater | Key | 0-indexed (row, col) | 1-indexed (row, col) | Name |
|---|---|---|---|---|
| Eastern Ereb | `die_hard_1` | (5, 5) | (6, 6) | Die Hard |

**Occupied territory:** Eastern Ereb contains multiple cells where `owner=ruthenia` and `occupied_by=sarmatia`. This represents Sarmatia's occupation of Ruthenia's territory. Mashriq has no `occupied_by` fields at Template v1.0.

### 5.3 Unit State Schema

**DB table:** `unit_states_per_round`

```sql
id uuid PK,
scenario_id FK,
sim_run_id FK,
round_num int,
unit_code text,
country_code text,
unit_type text,          -- ground | tactical_air | strategic_missile | air_defense | naval
global_row int,          -- 1..10 (NULL if not on map)
global_col int,          -- 1..20 (NULL if not on map)
map_id text,             -- NULL | 'eastern_ereb' | 'mashriq'
theater_row int,         -- 1..10 (NULL if not on theater)
theater_col int,         -- 1..10 (NULL if not on theater)
embarked_on text,        -- unit_code of carrier ship, or NULL
status text,             -- active | reserve | embarked | destroyed
notes text,
created_at timestamptz,
UNIQUE(scenario_id, round_num, unit_code)
```

**Status values:**

| Status | Meaning | Coord fields | embarked_on |
|---|---|---|---|
| `active` | On the map | global_row/col set; theater fields set if on theater-link hex | empty |
| `reserve` | Off-map pool | all NULL | empty |
| `embarked` | Aboard a naval unit | all NULL (inherits carrier position) | set to carrier unit_code |
| `destroyed` | Permanently eliminated | all NULL | empty |

**CSV column order** (authoring format, same fields):
`unit_id, country_id, unit_type, global_row, global_col, theater, theater_row, theater_col, embarked_on, status, notes`

---

## 6. API ENDPOINTS

All endpoints served by `app/test-interface/server.py`. Base URL: `http://localhost:8000` (default).

### 6.1 Map Data Endpoints

#### `GET /api/map/global`

Returns the raw global map JSON from `SEED_C1_MAP_GLOBAL_STATE_v4.json`.

**Response:** See section 5.1 for schema.

---

#### `GET /api/map/theater/eastern_ereb`

Returns the raw Eastern Ereb theater JSON.

**Response:** See section 5.2 for schema.

---

#### `GET /api/map/theater/mashriq`

Returns the raw Mashriq theater JSON.

**Response:** See section 5.2 for schema.

---

#### `GET /api/map/units`

Returns individual unit entities from `units.csv` (coordinate schema).

**Response:**
```json
{
  "units": [
    {
      "unit_id": "col_g_01",
      "country_id": "columbia",
      "unit_type": "ground",
      "global_row": 5,
      "global_col": 3,
      "theater": "",
      "theater_row": null,
      "theater_col": null,
      "embarked_on": "",
      "status": "active",
      "notes": ""
    }
  ],
  "by_country": {
    "columbia": { "ground": 22, "tactical_air": 15, ... }
  },
  "by_hex_summary": {
    "5,3": { "ground": 3, "tactical_air": 2 }
  },
  "total": 345
}
```

---

#### `GET /api/map/deployments`

**DEPRECATED** compatibility shim. Aggregates unit coords into legacy-shape rows.

**Response:**
```json
{
  "rows": [
    {
      "country_id": "columbia",
      "unit_type": "ground",
      "count": 3,
      "global_row": 5,
      "global_col": 3,
      "notes": ""
    }
  ],
  "by_hex": {
    "5,3": [ ... ]
  }
}
```

---

#### `GET /api/map/countries`

Returns country metadata and the dual color palette (from `countries.csv` + hardcoded UX palette).

**Response:**
```json
{
  "countries": {
    "columbia": {
      "id": "columbia",
      "name": "Columbia",
      "parallel": "United States",
      "regime": "democracy",
      "home_zones": [...],
      "at_war_with": [...],
      "colors": { "ui": "#3A6B9F", "map": "#9AB5D0", "light": "#E8EFF6" }
    }
  },
  "palette": {
    "columbia": { "ui": "#3A6B9F", "map": "#9AB5D0", "light": "#E8EFF6" },
    ...
  }
}
```

---

#### `GET /api/map/layouts`

Lists saved layout files from `units_layouts/` directory.

**Response:**
```json
{
  "layouts": [
    { "name": "start_one", "count": 345, "modified": 1712345678.0 }
  ]
}
```

---

#### `GET /api/map/layouts/load?name=<layout_name>`

Loads a named layout file and returns its unit list.

**Response:**
```json
{
  "success": true,
  "name": "start_one",
  "units": [ ... ],
  "count": 345
}
```

---

#### `POST /api/map/units/save`

Saves an edited unit roster to a named CSV layout file.

**Request body:**
```json
{
  "name": "my_layout",
  "units": [ ... ]
}
```

**Response:**
```json
{
  "success": true,
  "name": "my_layout",
  "path": "/path/to/units_layouts/my_layout.csv",
  "count": 345,
  "timestamp": "2026-04-13T12:00:00"
}
```

**Save format:** CSV with columns `unit_id, country_id, unit_type, global_row, global_col, theater, theater_row, theater_col, embarked_on, status, notes`. Written to `2 SEED/C_MECHANICS/C4_DATA/units_layouts/<name>.csv`. Never modifies `units.csv`.

---

#### `GET /api/config`

Returns central map config (mirrors `map_config.py`).

**Response:**
```json
{
  "version": "1.0",
  "global_rows": 10,
  "global_cols": 20,
  "theaters": {
    "eastern_ereb": { "rows": 10, "cols": 10, "display_name": "Eastern Ereb" },
    "mashriq": { "rows": 10, "cols": 10, "display_name": "Mashriq" }
  },
  "theater_names": ["eastern_ereb", "mashriq"],
  "countries": ["albion", "bharata", ...],
  "unit_types": ["ground", "tactical_air", "strategic_missile", "air_defense", "naval"],
  "unit_statuses": ["active", "reserve", "embarked", "destroyed"],
  "theater_link_hexes": {
    "3,12": "eastern_ereb",
    "4,12": "eastern_ereb",
    ...
  }
}
```

### 6.2 Observatory Endpoints

#### `GET /api/observatory/units?round=N&scenario=<code>&sim_run_id=<uuid>`

Returns unit states at a given round from `unit_states_per_round` DB table. Falls back to `units.csv` at round 0 or when DB is unavailable.

**Response:**
```json
{
  "round": 1,
  "scenario": "start_one",
  "sim_run_id": "uuid-here",
  "units": [ ... ],
  "source": "db"          // or "seed_csv"
}
```

---

#### `GET /api/observatory/countries?round=N&scenario=<code>&sim_run_id=<uuid>`

Returns country states at a given round from `country_states_per_round`. Falls back to `countries.csv`.

**Response:**
```json
{
  "round": 1,
  "scenario": "start_one",
  "sim_run_id": "uuid-here",
  "countries": [
    {
      "country_code": "columbia",
      "gdp": 285.0,
      "treasury": 50.0,
      "inflation": 3.2,
      "stability": 7,
      "political_support": 55,
      "war_tiredness": 0,
      "nuclear_level": 5,
      "ai_level": 5
    }
  ],
  "source": "db"
}
```

---

#### `GET /api/observatory/available-rounds?scenario=<code>&sim_run_id=<uuid>`

Returns sorted list of round numbers that have data.

**Response:**
```json
{
  "rounds": [0, 1, 2, 3],
  "source": "db",
  "sim_run_id": "uuid-here"
}
```

---

#### `GET /api/observatory/combats?round=N&scenario=<code>&sim_run_id=<uuid>`

Returns combat log from `observatory_combat_results`.

**Response:**
```json
{
  "round": 1,
  "scenario": "start_one",
  "sim_run_id": "uuid-here",
  "combats": [ ... ],
  "source": "db"
}
```

---

#### `GET /api/observatory/events?limit=50&scenario=<code>&sim_run_id=<uuid>`

Returns observatory events (activity feed).

---

#### `GET /api/observatory/blockades?round=N&scenario=<code>&sim_run_id=<uuid>`

Returns blockade state for a round.

---

#### `GET /api/observatory/global-series?scenario=<code>&sim_run_id=<uuid>`

Returns `global_state_per_round` for all rounds (oil_price, stock_index time series).

---

#### `GET /api/observatory/sim_runs`

Returns list of visible sim runs for the Observatory selector.

**Response:**
```json
{
  "runs": [
    {
      "id": "uuid",
      "name": "full_sim",
      "status": "visible_for_review",
      "current_round": 6,
      "max_rounds": 6,
      "scenario_code": "start_one",
      "created_at": "2026-04-10T...",
      ...
    }
  ],
  "source": "db"
}
```

---

#### `GET /api/observatory/movement-context?country=<code>&round=N&scenario=<code>&sim_run_id=<uuid>`

Returns the AI movement context dict for a country at a given round.

---

#### `GET /api/observatory/state`

Returns current Observatory runtime state (status, current_round, speed, etc.).

---

## 7. RENDERING SPECIFICATION

### 7.1 Canvas Setup

The renderer uses inline SVG (`<svg id="mapSvg">`). The `viewBox` and `width`/`height` are computed dynamically from grid dimensions and hex radius (see section 2.5). The SVG content is cleared and rebuilt on each view change.

### 7.2 Hex Fill Colors

**Color resolution order:**
1. Look up `state.countries.palette[owner_id].map` for the country's map color
2. If owner is `"sea"`: fallback `#2a4a6a`
3. Default fallback: `#556677`

**Occupied territory:** Theater hexes with `occupied_by` set use a diagonal stripe SVG pattern. The pattern combines the owner's color as background with the occupier's UI color at 65% opacity in 45-degree rotated stripes (8x8 px pattern).

### 7.3 Unit Rendering

**Icon types** (SVG `<use>` references to symbol defs):

| unit_type | Icon ID |
|---|---|
| `ground` | `unit-ground-right` (or `unit-ground-left` for Sarmatia on theater views) |
| `naval` | `unit-naval` |
| `tactical_air` | `unit-tactical-air` |
| `air_defense` | `unit-air-defense` |
| `strategic_missile` | `unit-strategic-missile` |

**Icon sizing:**

| unit_type | Size (global) | Size (theater) |
|---|---|---|
| `naval` | 21 px | 23 px |
| `ground` | 14 px | 16 px |
| `tactical_air` | 12 px | 14 px |
| `air_defense` | 14 px | 16 px |
| `strategic_missile` | 14 px | 16 px |

Base size: 14 px (global), 16 px (theater). Naval gets +7.

**Stacking algorithm:**
- Units are grouped by `(country_id, unit_type)` and aggregated with a count
- If total units on hex <= 5: show individual icons (one per unit)
- If total units on hex >= 6: compact batch (one icon per country+type group)
- Count badge appears only when a group has 3+ units
- Icons arranged 3 per row, with deterministic jitter for natural spread
- Icons sorted: same-country units grouped together, then by type

**Deterministic jitter formula:**
```javascript
function jitter(idx, amt) {
    var s = Math.sin(idx * 12.9898 + idx * 78.233) * 43758.5453;
    return ((s - Math.floor(s)) - 0.5) * 2 * amt;
}
```

**Icon color:** `uiColorFor(country_id)` -- uses the `ui` palette color for the unit's country.

### 7.4 Global Map Specific Rendering

- **Grid edge labels:** Column numbers (1-20) on top, row numbers (1-10) on left
- **Hex coordinate labels:** `"row,col"` (1-indexed) on land hexes only, positioned above center
- **Theater-link hexes:** CSS class `theater-link` added to polygon (styled with dashed border or highlight)
- **Chokepoint hexes:** CSS class `chokepoint` added; label text in uppercase above hex
- **Country name labels:** Rendered at the geometric centroid of each country's hex group, uppercase, using `uiColorFor()` color
- **Units:** Rendered at each hex center, offset +6 px downward

### 7.5 Theater Map Specific Rendering

- Same grid edge labels and hex labels as global
- **Occupied territory:** Striped pattern fill (see section 7.2)
- **Die-Hard markers:** Circle outline at `r * 0.85` radius, CSS class `die-hard-marker`, with label text below
- **Country name labels:** Same centroid algorithm as global
- **Embark badges:** In edit mode, mini unit icons (26% of hex radius) rendered near ship positions showing embarked units

### 7.6 Battle Markers

**Status:** Not yet implemented in the renderer. Combat results are available via `/api/observatory/combats` but no visual markers are rendered on the map.

### 7.7 Blockade Indicators

**Status:** Stub. Blockade data is available via `/api/observatory/blockades` but no visual treatment exists on the map.

### 7.8 Movement Animation

**Status:** Not implemented. Unit positions update between rounds without animation.

---

## 8. EDIT MODE SPECIFICATION

### 8.1 Toggle Mechanism

Edit mode is toggled via the "Edit Layout" button (`#editBtn`). When activated:
- Inspector panel hides; edit panel shows
- A mutable deep copy of the unit list is created (`state.editableUnits`)
- All rendering switches to read from `editableUnits` instead of `state.units`
- When deactivated: prompts to save if dirty, then reverts to view mode

### 8.2 Edit Panel Structure

The edit panel contains:
1. **Country grid** -- buttons for each country showing placed/total counts
2. **Ledger** -- per-unit-type summary (placed/reserve/total) for selected country
3. **Unit list** -- individual units of the selected type, each showing status and position
4. **"+ Add unit"** button to create new units in reserve
5. **Reserves overview** -- floating panel on the map showing reserve counts

### 8.3 Unit Selection and Placement

**Arm a unit:** Click a reserve unit in the list. It becomes "armed" (selected for placement). The cursor changes and status line shows the armed unit.

**Pick up a placed unit:** Click a placed/embarked unit. It returns to reserve (coords cleared) and becomes armed for re-placement.

**Place on hex:** Click any hex while armed.
- **Global view, non-theater-link hex:** Sets `global_row`, `global_col`. No theater fields.
- **Global view, theater-link hex:** Auto-drills into the theater view. User then clicks a theater cell.
- **Theater view:** Sets `theater`, `theater_row`, `theater_col`. Derives `global_row`/`global_col` via `globalHexForTheaterCell()`.

**Disarm:** Press Escape or click the armed unit again.

### 8.4 Hex Snapping

No sub-hex positioning. Units snap to hex centers. The hex under the cursor is determined by SVG element hit testing (`data-row`/`data-col` attributes on polygons).

### 8.5 Placement Validation

**Hard blocks (prevent placement):**
- Naval unit on land hex: blocked
- Land unit (ground/air/missile/AD) on sea hex without own-country ship: blocked

**Embarkation prompt:**
- Land unit placed on hex with own-country ship: prompt to embark
- Land unit placed on hex with foreign ship on sea: prompt with warning

**Soft warnings (placement proceeds):**
- Unit on foreign-country territory: "basing rights?" warning
- Unit on enemy territory: "ENEMY territory" warning
- Unit on territory occupied by its own country: no warning (legitimate)

### 8.6 Embark/Debark

**Embark:** When placing a land unit on a hex with an own-country ship, user is prompted. If confirmed:
- Unit coords cleared
- `embarked_on` set to ship's `unit_id`
- `status` set to `"embarked"`

**Debark (pick up):** Click an embarked unit in the unit list. It returns to reserve and can be placed anywhere.

### 8.7 Save Layout

Two save modes:
- **Save** (overwrites current layout name): `POST /api/map/units/save` with `{name, units}`
- **Save As** (prompts for new name): Same endpoint, new name

Format: CSV written to `2 SEED/C_MECHANICS/C4_DATA/units_layouts/<name>.csv`. Column order: `unit_id, country_id, unit_type, global_row, global_col, theater, theater_row, theater_col, embarked_on, status, notes`. NULL values written as empty strings.

### 8.8 Load Layout

Select from dropdown populated by `GET /api/map/layouts`. Loads via `GET /api/map/layouts/load?name=<name>`. Replaces `editableUnits`. Re-derives missing global coords from theater coords via linkage.

### 8.9 Undo/Redo

Implemented with a snapshot stack (max 100 entries).

- **Snapshot:** Before any mutation, the entire `editableUnits` array is deep-cloned and pushed to the undo stack. Redo stack is cleared.
- **Undo** (Ctrl+Z / Cmd+Z): Pop from undo stack, push current state to redo stack, restore.
- **Redo** (Ctrl+Shift+Z / Cmd+Shift+Z): Pop from redo stack, push current to undo, restore.

### 8.10 Clear All Deployments

Resets ALL units (all 20 countries) to reserve status. All coord and embark fields cleared. Requires confirmation.

### 8.11 Reset Country

Resets all units of the currently selected country to reserve. Requires confirmation.

### 8.12 Add / Delete Units

- **Add:** Creates a new unit in reserve with auto-generated `unit_id` following convention `{country3}_{type1}_{seq}` (e.g., `col_g_23`).
- **Delete:** Permanently removes unit after confirmation. Un-embarks any units embarked on a deleted naval unit.

### 8.13 Unit ID Generation

```
Country abbreviations:
  columbia=col, cathay=cat, sarmatia=sar, ruthenia=rut, persia=per,
  gallia=gal, teutonia=teu, freeland=fre, ponte=pon, albion=alb,
  bharata=bha, levantia=lev, formosa=for, phrygia=phr, yamato=yam,
  solaria=sol, choson=cho, hanguk=han, caribe=car, mirage=mir

Type abbreviations:
  ground=g, tactical_air=a, strategic_missile=m, air_defense=d, naval=n

ID format: {country3}_{type1}_{seq:02d}
Example: col_g_01, per_d_03, sar_g_r1
```

Sequence number is max existing + 1 for the `{country3}_{type1}_` prefix.

---

## 9. UNIT PLACEMENT RULES

### 9.1 Terrain Constraints

| Unit type | Allowed hexes | Notes |
|---|---|---|
| `ground` | Land hexes only (or embarked on naval) | Cannot be on sea hex unless embarked |
| `tactical_air` | Land hexes only (or embarked on naval) | Same restriction as ground |
| `strategic_missile` | Land hexes only | Global range for strikes, but physically on land |
| `air_defense` | Land hexes only | Same restriction as ground |
| `naval` | Water/sea hexes only | Never carries theater coords |

### 9.2 Theater-Link Constraint

If a non-naval unit's `(global_row, global_col)` matches a theater-link hex (per section 4.4), the unit MUST carry `theater`, `theater_row`, `theater_col` fields. This prevents "ghost" units visible on global but absent from theater view.

Conversely: a unit may only carry theater coords if its global coords resolve to a theater-link hex for that theater.

### 9.3 Embarkation Rules

- Only land/air units may embark on naval units
- Embarked units must belong to the same country as the carrier (Template v1.0)
- Embarked units have ALL coord fields NULL; they inherit the carrier's position for display
- `embarked_on` field references the carrier's `unit_id`

Template v1.0 starting state: 6 embarked units (4 tactical_air, 2 ground).

### 9.4 Reserve Units

- Status `"reserve"`: all coord fields NULL, `embarked_on` empty
- Not rendered on the map
- Can be deployed (placed) to become `"active"`

### 9.5 Naval on Theater-Link Sea Hexes

Sea-link theater cells (Eastern Ereb sea -> global (5,12); Mashriq sea rows 3-6 -> (7,12); Mashriq sea rows 7-10 -> (8,12)) accept naval placement only. Naval units on these hexes do NOT carry theater cell coords -- they sit on the global hex only.

---

## 10. COUNTRY COLOR PALETTE

### 10.1 Dual Palette System

Each country has three color tiers, sourced from `SEED_H1_UX_STYLE_v2.md` and hardcoded in `server.py`:

| Tier | CSS variable style | Usage |
|---|---|---|
| `map` | Muted/pastel | Hex fill on the map |
| `ui` | Saturated/dark | Unit icons, text, badges |
| `light` | Very light | Background highlights in UI panels |

### 10.2 Complete Palette

| Country | `ui` | `map` | `light` |
|---|---|---|---|
| columbia | #3A6B9F | #9AB5D0 | #E8EFF6 |
| cathay | #C4A030 | #E8D5A3 | #F8F2E5 |
| sarmatia | #A06060 | #D4A5A5 | #F5EAEA |
| ruthenia | #5A9A5A | #A5C8A5 | #EBF3EB |
| persia | #9A7040 | #C8A57A | #F2EBE0 |
| gallia | #4A6FA0 | #A5B8D4 | #EBF0F6 |
| teutonia | #3A8A7A | #8AB5AA | #E8F2EF |
| thule | #3A8A7A | #8AB5AA | #E8F2EF |
| albion | #4A7A8F | #8AA5B5 | #E8EFF3 |
| freeland | #5A80A0 | #A0B8C8 | #EBF1F5 |
| ponte | #6A9A8A | #A5C8B8 | #EBF3EF |
| bharata | #B87850 | #D4B5A5 | #F5EDE5 |
| formosa | #B89048 | #DCC5A0 | #F5EEE0 |
| yamato | #5A7A9B | #A5B5C8 | #EBF0F5 |
| hanguk | #4A8FA8 | #A5C8D4 | #E8F1F5 |
| phrygia | #8A6A48 | #B5A08A | #F0EBE5 |
| solaria | #A89030 | #C8B896 | #F3F0E5 |
| mirage | #A88050 | #D4BFA5 | #F5EEE5 |
| levantia | #9A9A40 | #D4D4A5 | #F3F3E8 |
| choson | #5A5A5A | #8A8A8A | #EFEFEF |
| caribe | #3A7AAA | #8AACCC | #E8F0F6 |
| sogdiana | #8A8A60 | #C8C8A5 | #F0F0E8 |
| horn | #8A7A68 | #B5A896 | #F0ECE8 |
| sea | #2a4a6a | #2a4a6a | #2a4a6a |

### 10.3 Color Resolution in Renderer

```javascript
function colorFor(ownerId) {
    var p = state.countries?.palette?.[ownerId];
    if (p) return p.map;
    if (ownerId === 'sea') return '#2a4a6a';
    return '#556677';
}

function uiColorFor(ownerId) {
    var p = state.countries?.palette?.[ownerId];
    return (p && p.ui) || '#888';
}
```

Colors are loaded at init via `GET /api/map/countries` and stored in `state.countries.palette`. The palette is authoritative (overrides colors in the SEED JSON files).

---

## 11. CROSS-REFERENCES

### Design Documents

| Document | Path | What it contains |
|---|---|---|
| SEED Map + Units Master | `2 SEED/C_MECHANICS/SEED_C_MAP_UNITS_MASTER_v1.md` | Design spec: map system, coordinate convention, linkage, unit model, placement rules, Template/Scenario/Run architecture |
| SEED Global Map Structure | `2 SEED/C_MECHANICS/C1_MAP/SEED_C1_MAP_STRUCTURE_v4.md` | Global hex registry, chokepoints |
| SEED Global Map State | `2 SEED/C_MECHANICS/C1_MAP/SEED_C1_MAP_GLOBAL_STATE_v4.json` | Per-hex ownership data (canonical) |
| SEED Eastern Ereb Structure | `2 SEED/C_MECHANICS/C1_MAP/SEED_C3_THEATER_EASTERN_EREB_STRUCTURE_v3.md` | Eastern Ereb hex registry |
| SEED Eastern Ereb State | `2 SEED/C_MECHANICS/C1_MAP/SEED_C3_THEATER_EASTERN_EREB_STATE_v3.json` | Per-hex ownership + occupation + die-hards |
| SEED Mashriq State | `2 SEED/C_MECHANICS/C1_MAP/SEED_C3_THEATER_MASHRIQ_STATE_v1.json` | Per-hex ownership |
| CARD Architecture | `PHASES/UNMANNED_SPACECRAFT/CARD_ARCHITECTURE.md` | Coordinate contract, adjacency rules, module map |
| DET Unit Model | `3 DETAILED DESIGN/DET_UNIT_MODEL_v1.md` | Unit entity spec (Pydantic, TS, SQL, invariants) |
| UX Style Guide | `2 SEED/H_VISUAL/SEED_H1_UX_STYLE_v2.md` | Map color palette, icon set |

### Code Files

| File | Path | What it contains |
|---|---|---|
| Python map config | `app/engine/config/map_config.py` | Canonical constants, linkage functions, bounds validation |
| JS map config | `app/test-interface/static/map_config.js` | Browser mirror of Python config |
| Map renderer + editor | `app/test-interface/static/map.js` | SVG renderer, hex geometry, edit mode, save/load |
| API server | `app/test-interface/server.py` | All `/api/map/*` and `/api/observatory/*` endpoints |
| Map context (engine) | `app/engine/agents/map_context.py` | `load_units()`, `units_by_global_hex()`, `units_by_theater_cell()` |
| Unit data (CSV) | `2 SEED/C_MECHANICS/C4_DATA/units.csv` | 345 units, engine default layout |
| Canonical layout | `2 SEED/C_MECHANICS/C4_DATA/units_layouts/start_one.csv` | Template v1.0 authoritative placement |

### Constants Quick Reference

| Constant | Value | Source |
|---|---|---|
| `MAP_CONFIG_VERSION` | `"1.0"` | map_config.py |
| `GLOBAL_ROWS` | 10 | map_config.py |
| `GLOBAL_COLS` | 20 | map_config.py |
| Theater grid (both) | 10 x 10 | map_config.py |
| `HEX_R_GLOBAL` | 34 px | map.js |
| `HEX_R_THEATER` | 40 px | map.js |
| `PAD` | 60 px | map.js |
| Total units (Template v1.0) | 345 | units.csv |
| Total countries | 20 | map_config.py |
| Theater count | 2 | map_config.py |
| Theater-link hexes | 12 | map_config.py |
| Chokepoints | 3 | Global JSON |
| Nuclear sites | 2 | map_config.py |

---

*This document is the engineering bridge between SEED design and code. When building a new renderer, editor, or migration tool, start here.*
