# CONTRACT: Map Rendering

**Version:** 1.0 | **Date:** 2026-04-15 | **Status:** LOCKED

---

## 1. Overview

This contract defines how any TTT client (template editor, moderator view, participant view, public screen) renders the hex map. All implementations MUST follow these rules to ensure visual consistency across contexts.

## 2. Hex Geometry

| Property | Value |
|---|---|
| **Hex type** | Pointy-top (vertex at top) |
| **Offset convention** | Odd-r (0-indexed odd rows shifted right by half hex width) |
| **Coordinates** | `(row, col)`, 1-indexed in all human-facing contexts |
| **Array indexing** | 0-indexed in JSON/code, +1 for display |

### Hex center calculation (pointy-top, odd-r offset)
```
w = sqrt(3) × radius
h = 1.5 × radius
xOffset = (row_0indexed % 2 === 1) ? w/2 : 0
center_x = PADDING + col_0indexed × w + xOffset + w/2
center_y = PADDING + row_0indexed × h + radius
```

### Hex vertices (pointy-top, 6 points)
```
for i in 0..5:
  angle = PI/180 × (60 × i - 30)
  vertex_x = center_x + radius × cos(angle)
  vertex_y = center_y + radius × sin(angle)
```

### Adjacency (6 neighbors per hex)
```
0-indexed odd rows (1,3,5,7,9):   deltas = [(-1,0), (-1,+1), (0,-1), (0,+1), (+1,0), (+1,+1)]
0-indexed even rows (0,2,4,6,8):  deltas = [(-1,-1), (-1,0), (0,-1), (0,+1), (+1,-1), (+1,0)]
```

## 3. Map Grids

| Grid | Rows | Cols | Radius |
|---|---|---|---|
| **Global** | 10 | 20 | 34 (default) |
| **Eastern Ereb** | 10 | 10 | 34-40 |
| **Mashriq** | 10 | 10 | 34-40 |

### Data source
- Template: `sim_templates.map_config` JSONB
- Structure: `map_config.global.grid[row][col] = { owner: string }`
- Theaters: `map_config.theaters.eastern_ereb.grid`, `map_config.theaters.mashriq.grid`
- Fallback: JSON files in `2 SEED/C_MECHANICS/C1_MAP/`

## 4. Visual Rules

### Country colors
- Stored on `countries` table: `color_ui` (vivid), `color_map` (muted), `color_light` (background)
- Map hexes use `color_map` (muted variant)
- UI elements (badges, charts) use `color_ui` (vivid variant)
- Sea hexes: CSS variable `--sea` (default `#2a4a6a`)

### Grid edge labels
- Column numbers: top edge, aligned with even-row hex centers
- Row numbers: left edge, centered vertically with hex row
- Font: monospace, small (9-10px)

### Hex labels
- Land hexes show `row,col` (1-indexed) inside the hex
- Font: monospace, very small (7-8px), subdued color

### Country name labels
- Rendered at the centroid of each country's hex cluster
- Font: heading font, small caps

## 5. Map Features (rendered as overlays)

### Chokepoints
- Source: `map_config.global.chokepoints`
- Visual: dashed gold border on hex + name label
- Color: `#E8B84D`

### Die-Hard Zones
- Source: `map_config.theaters.{name}.dieHards`
- Visual: dashed gold circle overlay + name label centered on hex
- Color: `#C4922A`, dashed stroke

### Nuclear Sites
- Source: `map_config.global.nuclear_sites` (country → [row, col] 1-indexed)
- Visual: ☢ radiation trefoil symbol centered on hex
- Color: `#B03A3A`

### Theater Link Hexes
- Global hexes that link to theater submaps
- Visual: highlighted border (per existing CSS `.theater-link`)
- Click behavior: drill down to theater view

## 6. Unit Rendering (deployment mode only)

### Unit types and icons
| Type | Icon | Map size |
|---|---|---|
| Naval | Warship silhouette | 19px |
| Ground | Tank silhouette | 16px |
| Tactical Air | Drone/UAV | 14px |
| Air Defense | Radar dish | 16px |
| Strategic Missile | ICBM vertical | 16px |

### Unit stacking
- Multiple units on same hex: stack in rows (3 per row, 60% overlap)
- White stroke outline (0.5-0.6px) for visibility
- Icons colored by country (`color_ui`)

### Unit data source
- CSV: `units.csv` or saved layouts in `units_layouts/`
- Each unit: `unit_id, country_id, unit_type, global_row, global_col, theater, theater_row, theater_col, embarked_on, status`
- Coordinates: 1-indexed display format
- Theater units project to global hex via `global_hex_for_theater_cell()`

## 7. Rendering Modes

| Mode | Shows | Editable | Used by |
|---|---|---|---|
| **Geography** | Countries, chokepoints, die-hards, nuclear | Hex ownership, features, colors | M9 Template Editor (Map tab) |
| **Deployment** | Geography + military units | Unit placement | M9 Template Editor (Deployments tab) |
| **Moderator** | Geography + all units (god view) | Round controls, overrides | M4 Sim Runner |
| **Participant** | Geography + own forces (fog of war) | Action submission | M6 Human Interface |
| **Public** | Geography + key indicators | None (read-only) | M8 Public Screen |

## 8. Layout Rules

### Combined view (geography mode default)
- Global map at top, full available width
- Two theater maps below, side by side
- Theaters start collapsed (title only), expand on click
- Scroll vertically to see theaters when expanded

### Drill-down view
- Click theater-link hex on global → full theater map replaces view
- Back button returns to combined view

## 9. Implementation Notes

### Current canonical implementation
- `app/test-interface/static/map.js` — SVG renderer (vanilla JS)
- `app/test-interface/static/map_config.js` — config mirror
- `app/test-interface/static/geo_edit.js` — geography editing
- `app/test-interface/static/map.css` — styling

### Integration pattern
- Embedded via iframe in React template editor
- Served from test-interface HTTP server (port 8888)
- Future: extract to shared `map-core.js` module

### Save pipeline
- Geography changes → POST `/api/map/save_geography` → local JSON + Supabase template
- Unit changes → POST `/api/map/units/save` → layout CSV files
- Color changes → included in geography save → `countries.color_map` in DB
