# Thucydides Trap SIM — Visual Style Options
**Date:** 2026-03-26 | **Author:** CANVAS (UX & Visual Design) | **Status:** 7 Options for Review

---

## How to Compare

**Options A-D** show the **same regional slice** — the Mashriq theater and its surroundings (Persia, Levantia, Solaria, Mirage, Bharata, Horn of Africa, Phrygia, with Arabian Sea, Persian Gulf, Red Sea, and chokepoints at Gulf Gate and Bab el-Mandeb). Each includes identical unit deployments and a blockaded Gulf Gate.

**Options E-G** show the **full global map** — all 45 zones, 20 countries, 8 chokepoints, and 2 active theaters (Eastern Ereb, Mashriq). These three options explore fundamentally different visual paradigms: hex grid, wargame board, and abstract network graph. They are 1200x700 SVGs with Indian Ocean-centered projection.

---

## Option A: Political Atlas

**Visual register:** The Economist magazine meets a Rand McNally printed atlas — calm authority, editorial elegance.

### Color Palette

| Element | Hex | Description |
|---------|-----|-------------|
| Background | `#F5F5F5` | Very light gray |
| Sea | `#7BA7CC` | Clean medium blue |
| Zone borders | `#333333` | Dark charcoal, 1.5px |
| Text | `#333333` | Dark charcoal |
| Country 1 (Persia) | `#D0B898` | Warm sand |
| Country 2 (Levantia) | `#C8D8C0` | Light sage |
| Country 3 (Solaria) | `#F5E6D0` | Pale cream |
| Country 4 (Phrygia) | `#E8D5E0` | Soft lavender |
| Conflict zones | N/A (same fill, distinguished by labels) | |
| Chokepoints | `#CC3333` | Bold red diamond markers |

### Typography
- **Headings:** Georgia, serif
- **Body/labels:** Georgia, serif (small-caps for land zones, italic for sea zones)
- **Unit labels:** Georgia, serif, 6-9pt

### Unit Representation
Colored circles with count number centered inside. Country-color fill matches the zone owner. Small "GND" / "AIR" / "NAV" type labels adjacent.

### Web App Extension
Dashboard would use the light gray background with serif typography throughout. Data panels in white cards with thin charcoal borders. Charts in the same muted pastel palette. Status indicators in the red/amber/green vocabulary. The map sits in a centered panel with information sidebars.

### Print Suitability (A3)
Excellent. The pale palette and thin lines reproduce cleanly on standard inkjet and laser printers. High contrast between land and sea. Zone labels are legible at A3 scale. The light background saves ink. This is the most print-friendly option.

### Pros
- Immediately legible and professional
- Familiar register for executives used to The Economist, FT, or policy briefings
- Excellent print reproduction
- Low visual fatigue in long sessions
- Accessible (high contrast, clear labels)

### Cons
- May feel too "flat" or static — less sense of being in a game
- Low gamification energy — could read as a report rather than a simulation
- No terrain indication — geography feels abstract

---

## Option B: Strategic Board

**Visual register:** A premium digital board game — modern, polished, slightly dramatic, like a Bloomberg terminal crossed with a luxury Risk edition.

### Color Palette

| Element | Hex | Description |
|---------|-----|-------------|
| Background | `#1A2A3A` | Dark navy |
| Sea | `#4A7FA5` | Deep blue with wave pattern |
| Zone borders | `#A0B0B0` | Light gray/silver, 1px |
| Text | `#D0D8D0` | Soft light gray |
| Country 1 (Persia) | `#6B4B3B` | Dark terracotta |
| Country 2 (Levantia) | `#7B8B6B` | Muted olive |
| Country 3 (Solaria) | `#8B7B5B` | Dusty sand |
| Country 4 (Phrygia) | `#6B7B6B` | Muted sage-gray |
| Conflict zones | N/A | |
| Chokepoints | `#FF6644` | Warm red-orange, anchor icons |

### Typography
- **Headings:** Helvetica, sans-serif, bold, all-caps
- **Body/labels:** Helvetica, sans-serif
- **Sea labels:** Helvetica italic

### Unit Representation
Rectangular token/chip with rounded corners. Left side shows unit type letter (G/A/N), right side shows count. Token fill matches country color with lighter stroke for contrast against dark background. Tokens are compact and stackable.

### Web App Extension
Dark-mode dashboard with navy background. Cards with subtle borders in silver/gray. Data visualizations use the muted warm/cool palette on dark canvas. Navigation in a top bar or sidebar with the same navy. Real-time data panels with subtle glow effects. The map dominates the center. This style naturally supports a "situation room" feel.

### Print Suitability (A3)
Moderate. The dark background consumes significant ink/toner and may not reproduce well on standard printers. Best suited to screen display or high-quality glossy printing. For print, a "light mode" variant would be needed (inverting the palette).

### Pros
- Most visually striking and "game-like" — engages competitive instincts
- Dark background makes the map zone colors pop
- Token system is intuitive and compact
- Natural fit for digital/screen-first delivery
- Creates a "war room" atmosphere that appeals to competitive founders

### Cons
- Expensive to print (dark background)
- Harder to annotate by hand (dark surface)
- May feel too "gamey" for some conservative audiences
- Slightly lower legibility in well-lit projection environments (dark-on-dark)

---

## Option C: Intelligence Map

**Visual register:** A classified military briefing document — restrained, precise, authoritative, like something from a general's desk or an intelligence agency analyst's workstation.

### Color Palette

| Element | Hex | Description |
|---------|-----|-------------|
| Background | `#F5F0E8` | Warm cream/parchment |
| Sea | `#9AB5C7` | Muted blue-gray |
| Zone borders | `#8B7355` | Warm brown, 1px |
| Text | `#5B4B35` | Dark brown |
| Country 1 (Persia) | `#D0C0B0` / stroke `#5B3B25` | Very subtle overlay, distinguished by unit symbols |
| Country 2 (Levantia) | `#D8E0D0` / stroke `#3B5B3B` | |
| Country 3 (Solaria) | `#EAE0D0` / stroke `#5B4B25` | |
| Country 4 (Columbia) | N/A fill / stroke `#1A3A5A` | Units only (no territory here) |
| Conflict zones | Same muted fills | |
| Chokepoints | `#8B2222` | Dark red, military star markers |

### Typography
- **Headings:** Consolas/Courier New, monospaced, bold, spaced caps
- **Body/labels:** Consolas/Courier New, monospaced, ALL CAPS with letter-spacing
- **Classification header:** Consolas, red, spaced caps (TOP SECRET // NOFORN // THUCYDIDES)

### Unit Representation
NATO-standard military symbology: rectangles with X for ground forces, inverted-V (chevron) for tactical air, rectangle with ellipse for naval. Count shown as "x3" adjacent. Faction distinguished by stroke color (brown for Persia, dark blue for Columbia, dark green for Levantia, olive-brown for Solaria). No fill — outlines only.

### Web App Extension
Parchment-toned dashboard with monospaced typography. Data presented in tabular format with brown rules. Status updates in military dispatch format (timestamps, zone codes, terse language). The map feels like a real-time intelligence feed. Sidebar panels with classified-document styling (borders, headers, section numbering). Very austere, very serious.

### Print Suitability (A3)
Excellent. Light parchment background prints beautifully. Thin brown lines are crisp. The monospaced typography reads cleanly at any scale. NATO symbols are resolution-independent. This prints nearly as well as it displays on screen. The "classification header" adds gravitas in print.

### Pros
- Maximum authority and seriousness — no ambiguity about the stakes
- NATO symbols are universal in defense/strategy contexts
- Monospaced type creates a distinctive "signal intelligence" atmosphere
- Excellent for print and projection
- The classification header is a subtle but powerful framing device
- Appeals to founders who self-identify as strategic thinkers

### Cons
- Least "fun" — could feel oppressively serious for a simulation game
- NATO symbols require brief explanation for non-military audiences
- Country zones are very subtly differentiated — may need color to be stronger in production
- Monospaced type is less elegant than serif or sans-serif for long text
- Could feel like an affectation ("playing soldier") if overdone

---

## Option D: Terrain Atlas

**Visual register:** A beautiful, crafted reference atlas with a game overlay — the most immersive and visually rich option, like a National Geographic map with strategic annotations.

### Color Palette

| Element | Hex | Description |
|---------|-----|-------------|
| Background | `#FAFAF5` | Off-white |
| Sea (deep) | `#4A7A98` | Dark blue (depth) |
| Sea (shallow/coastal) | `#9AC0D8` | Light blue |
| Zone borders | `#8B7355` | Brown, 1px, with drop shadow |
| Text | `#4A3A28` | Warm dark brown |
| Country 1 (Persia) | `#C8B898` | Warm sand with desert stipple |
| Country 2 (Levantia) | `#D0D8C0` | Light green |
| Country 3 (Solaria) | `#EAD8B8` | Sandy desert with heavy stipple |
| Country 4 (Bharata) | `#D0C8D8` | Soft lavender with mountain/forest detail |
| Conflict zones | Brown hatching over zone color | |
| Chokepoints | `#BB3333` | Dashed red passage markers |

### Typography
- **Headings:** Georgia, serif, italic
- **Land labels:** Georgia, serif, italic
- **Sea labels:** Georgia, serif, italic (slightly larger)
- **Unit text:** Georgia, serif, bold

### Unit Representation
Flag pennant markers: a vertical pole with a triangular pennant in the faction's color, with unit type and count text above. Persia = sand pennant, Columbia = blue pennant, Levantia = green pennant, Solaria = desert pennant. Compact but decorative.

### Terrain Indicators
- **Mountains:** Small triangle clusters (Zagros in Persia, Western Ghats in Bharata, Yemen highlands)
- **Deserts:** Dot stippling pattern overlay (Solaria, Persia South)
- **Forests:** Small circle clusters (Bharata interior)
- **Rivers:** Thin blue lines (Tigris-Euphrates suggestion in Mesopotamia)
- **Ocean depth:** Graduated blue (darker = deeper)

### Web App Extension
Light, warm-toned dashboard with the off-white background. Map as the hero element with terrain detail visible. Information panels styled as atlas marginalia — elegant boxed notes with serif type. Charts use the earthy warm palette. The overall feel is closer to a high-end educational/reference product than a military tool. Navigation could include a small "atlas index" sidebar.

### Print Suitability (A3)
Good to excellent. The terrain detail adds visual richness at A3 scale. The drop shadows on zone borders give a subtle dimensionality. Light background is print-friendly. However, some fine terrain details (stippling, small tree clusters) may not reproduce well on lower-resolution printers. Best on high-quality inkjet or offset printing.

### Pros
- Most visually beautiful and immersive
- Terrain detail gives geographic context that aids strategic understanding
- Flag pennants are intuitive and attractive
- Ocean depth graduation is informative (shallow vs. deep water matters strategically)
- The "atlas" feel signals quality craftsmanship — appeals to CEOs who appreciate design
- Most "shareable" — looks impressive in screenshots, presentations

### Cons
- Most complex to produce and maintain
- Fine terrain detail may be lost on projection (5m viewing distance)
- Terrain patterns could compete with unit visibility in dense deployment areas
- Pennant flags may get crowded with many units in small zones
- Higher production cost (more design time per zone)

---

## Comparison Matrix

| Criterion | A: Political Atlas | B: Strategic Board | C: Intelligence Map | D: Terrain Atlas |
|-----------|:-:|:-:|:-:|:-:|
| **Legibility (screen)** | 5 | 4 | 4 | 4 |
| **Legibility (projection)** | 5 | 3 | 5 | 3 |
| **Legibility (print A3)** | 5 | 2 | 5 | 4 |
| **Gamification feel** | 2 | 5 | 2 | 4 |
| **Authority/seriousness** | 4 | 3 | 5 | 4 |
| **Visual beauty** | 3 | 4 | 3 | 5 |
| **Unit visibility** | 4 | 5 | 4 | 3 |
| **Production simplicity** | 5 | 4 | 4 | 2 |
| **CEO/founder appeal** | 4 | 4 | 4 | 5 |
| **Uniqueness/memorability** | 2 | 4 | 5 | 5 |

*Scale: 1 (lowest) to 5 (highest)*

---

## Recommendation

For a CEO/founder audience running a strategic simulation:

- **If screen-first (web app):** Option B (Strategic Board) or Option D (Terrain Atlas)
- **If print/projection priority:** Option A (Political Atlas) or Option C (Intelligence Map)
- **If maximum authority:** Option C (Intelligence Map)
- **If maximum engagement:** Option D (Terrain Atlas)
- **Hybrid approach:** Start with Option A as the base system (simplest, most versatile), then layer in terrain elements from D for the final product. The core zone shapes and color logic of A translate to any of the other styles.

A strong path forward: **Option A as foundation, with selective elements from C** (NATO unit symbols, classification header framing, monospaced zone codes) **and D** (ocean depth gradient, subtle terrain hints in key zones). This gives you authority + beauty + legibility across all media.

---

## Option E: Hex World

**Visual register:** konkr.io meets a simplified political atlas — the world as a clean hex tessellation, every zone a single large hexagon, no empty space. A modern, abstract board game that feels both strategic and approachable.

### Color Palette

| Element | Hex | Description |
|---------|-----|-------------|
| Background | `#E8E4DE` | Warm light gray |
| Sea (coastal) | `#7BA7CC` | Medium blue |
| Sea (deep) | `#4A77A0` | Dark blue |
| Sea (mid) | `#6A97BC` | Blue-gray |
| Hex borders | `#666666` | Medium gray, 1px |
| Columbia | `#B8C4A8` | Pale sage |
| Cathay | `#D8C0A8` | Warm sand |
| Nordostan | `#C0B0A0` | Dusty taupe |
| Gallia | `#D0C0C8` | Dusty rose |
| Teutonia | `#C8D0C0` | Light sage |
| Freeland | `#C8C0D0` | Lavender |
| Persia | `#D0B898` | Warm sand |
| Bharata | `#C8B8D0` | Soft lavender |
| Contested | `#D0D0D0` | Light gray, dashed border |
| Chokepoints | N/A (red ring) | `#8B2222` red circle on sea hexes |

### Typography
- **Zone labels:** Segoe UI / Helvetica Neue, sans-serif, 7px, centered in hex
- **Country names:** Same family, 11px, bold, spans multi-hex areas
- **Sea labels:** Italic, slightly smaller (6.5px)

### Unit Representation
Small rectangular counters inside hexes. Color-coded: green (`#5A8A5A`) for ground with "GND x#", blue (`#4A7FA5`) for naval, gray (`#888`) for air, red (`#CC4444`) for missiles. Count number inside the counter. Compact, readable, stackable.

### Pros
- Instantly readable — each hex = one decision space
- The hex tessellation gives a satisfying board-game tangibility
- Muted political-atlas palette avoids "gamey" saturation while still being pleasant
- Easy to update (add/remove hexes, recolor)
- Hexagonal adjacency is unambiguous — neighbors are visually obvious
- Good for digital interaction (click a hex, get info)

### Cons
- Geographic distortion is significant — countries lose their shape entirely
- Some zones (vast like Nordostan Central, tiny like Formosa) get the same hex size
- Less immersive than terrain-based maps — no sense of landscape
- Hex grid can feel "flat" without terrain variation
- Multi-hex countries need additional visual grouping to read as one entity

---

## Option F: Wargame Board

**Visual register:** CosimAmphibious / professional hex wargame — smaller hexes creating a dense operational grid, terrain indicated through hex color, country borders as thick colored overlays, NATO-standard military symbology for unit counters. A defense analyst's working map.

### Color Palette

| Element | Hex | Description |
|---------|-----|-------------|
| Background | `#D8D0C0` | Warm tan (paper) |
| Hex grid | `#C0C0B8` | Faint gray overlay pattern |
| Sea zones | `#6A92B5` | Medium blue (semi-transparent) |
| Temperate land | `#A0B890` | Light green |
| Desert land | `#D8C898` | Tan/sand |
| Arctic land | `#E0DDD5` | Off-white |
| Mountain land | `#C8B080` | Light brown |
| Contested zones | Terrain color | Dashed border `#999` |
| Columbia border | `#3A6A3A` | Dark green, 2.5px |
| Cathay border | `#8A6A2A` | Dark gold, 2.5px |
| Nordostan border | `#6A5A3A` | Dark brown, 2.5px |
| Persia border | `#7A4A2A` | Dark terracotta, 2.5px |
| Chokepoints | `#CC2222` | Anchor symbol (&#x2693;) |
| Title bar | `#3A3A30` | Dark olive-charcoal |

### Typography
- **All text:** Consolas / Courier New, monospaced — military dispatch feel
- **Zone labels:** 6.5px, bold, ALL CAPS
- **Country names:** 10px, bold, letter-spacing 2px
- **Grid coordinates:** 5px, faint gray (A1, B1, etc. along edges)
- **Title:** 14px, light gray on dark bar, spaced caps

### Unit Representation
NATO-standard military symbology in colored rectangular counters:
- **Ground:** Rectangle with X (infantry/division crosshatch), country color fill
- **Naval:** Rounded rectangle (elliptical ends), country color fill
- **Air:** Rectangle with inverted V/triangle inside
- **Air Defense:** Rectangle with arc symbol
- **Missiles:** Rectangle with vertical arrow, red fill (`#AA3333`)
- Count shown as "x#" text adjacent to counter

### Pros
- Maximum professional credibility — looks like a real defense planning tool
- Terrain indication through hex color gives geographic context without complexity
- NATO symbols are universal in strategy/defense audiences
- Dense hex grid supports precise positioning and movement planning
- Monospaced typography reinforces the operational/intelligence aesthetic
- Grid coordinates enable verbal communication ("Move to E3")
- Dark title bar creates strong visual framing

### Cons
- Most "hardcore" aesthetic — may intimidate non-military audiences
- Small hexes (40px) make labels harder to read at a distance
- NATO symbols require a learning curve for civilian players
- Dense grid can feel overwhelming on first viewing
- Country borders overlaid on hex grid can create visual clutter
- Print at A3 may lose fine detail (small hex labels, grid coords)

---

## Option G: Strategic Network

**Visual register:** Risk-meets-metro-map — a pure adjacency graph where zones are colored circles and connections are lines. Maximum strategic clarity, minimum geographic immersion. Like a power grid schematic of global geopolitics.

### Color Palette

| Element | Hex | Description |
|---------|-----|-------------|
| Background | `#F8F8F5` | Near-white warm |
| Land nodes | Country-specific | Saturated muted tones (darker than hex fills) |
| Columbia | `#5A7A4A` to `#6A8A5A` | Forest green family |
| Cathay | `#8A6A2A` | Dark gold |
| Nordostan | `#7A6A4A` | Dark taupe |
| Europe | `#5A6A7A` / `#7A5A7A` / etc. | Each country distinct |
| Sea nodes | `#4A7FA5` to `#3A6F95` | Blue family, smaller |
| Contested nodes | `#B0B0B0` | Gray, dashed border |
| Chokepoints | N/A (red ring) | `#AA2222` bold ring around sea node |
| Land links | `#888888` | Solid gray, 1.2px |
| Sea links | `#7AA5CC` | Dashed blue, 1px |
| Mixed links | `#8A9AAA` | Dotted gray-blue, 1px |
| Cluster bg | Country-tinted | Very light ellipse behind country group |
| Active theater | `#CC2222` | Dashed red ring around node |

### Typography
- **Node labels:** Inter / Helvetica Neue, sans-serif, 6.5px, white on dark nodes
- **Country labels:** 12px, bold, letter-spacing 1.5px, positioned above clusters
- **Unit badges:** 5px, white on small colored circle attached to node
- **Continent labels:** 15px, ultra-light weight, very faint behind clusters

### Unit Representation
Small colored circles ("badges") attached to the edge of zone nodes. Each badge contains a letter + number: G4 = Ground x4, N2 = Naval x2, M2 = Missile x2. Badge color matches the owning country. Extremely compact — one badge per unit type per zone.

### Pros
- **Maximum strategic clarity** — adjacency relationships are immediately visible
- Easiest to produce, modify, and maintain (SVG circles and lines)
- No geographic distortion debates — it's an explicit abstraction
- Ideal for digital interaction (nodes are natural click targets)
- Unit badges are minimal and unambiguous
- The graph layout reveals strategic structure that geography obscures (e.g., how many hops from Columbia to Cathay)
- Scales well — adding a new zone is adding one circle and some lines
- Cleanest for projector/screen viewing at any distance
- Natural format for algorithmic analysis (pathfinding, connectivity)

### Cons
- **Least immersive** — no sense of "being in the world"
- Players lose geographic intuition (where IS the Malacca Strait relative to India?)
- May feel too abstract for a simulation that's meant to feel consequential
- Cluster layout requires careful design to maintain geographic "feel"
- Long-distance links (e.g., N.Pacific spanning the full width) can create visual clutter
- Not visually impressive in screenshots or presentations — looks like a diagram
- Some founders may perceive it as "not finished" or "too schematic"

---

## Extended Comparison Matrix

| Criterion | A: Political Atlas | B: Strategic Board | C: Intelligence Map | D: Terrain Atlas | E: Hex World | F: Wargame Board | G: Strategic Network |
|-----------|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| **Legibility (screen)** | 5 | 4 | 4 | 4 | 5 | 4 | 5 |
| **Legibility (projection)** | 5 | 3 | 5 | 3 | 4 | 3 | 5 |
| **Legibility (print A3)** | 5 | 2 | 5 | 4 | 4 | 3 | 5 |
| **Gamification feel** | 2 | 5 | 2 | 4 | 4 | 5 | 3 |
| **Authority/seriousness** | 4 | 3 | 5 | 4 | 3 | 5 | 3 |
| **Visual beauty** | 3 | 4 | 3 | 5 | 3 | 4 | 2 |
| **Unit visibility** | 4 | 5 | 4 | 3 | 4 | 5 | 5 |
| **Production simplicity** | 5 | 4 | 4 | 2 | 4 | 3 | 5 |
| **CEO/founder appeal** | 4 | 4 | 4 | 5 | 4 | 4 | 3 |
| **Uniqueness/memorability** | 2 | 4 | 5 | 5 | 4 | 4 | 4 |
| **Global map suitability** | 4 | 4 | 4 | 3 | 5 | 5 | 5 |
| **Adjacency clarity** | 3 | 3 | 3 | 3 | 4 | 4 | 5 |
| **Scalability (add zones)** | 3 | 3 | 3 | 2 | 4 | 3 | 5 |

*Scale: 1 (lowest) to 5 (highest)*

---

## Updated Recommendation

For global map display (all 45 zones), the three new options each serve a distinct purpose:

- **If you want a digital board game feel:** Option E (Hex World) — approachable, clear, tactile
- **If you want maximum defense credibility:** Option F (Wargame Board) — professional, dense, authoritative
- **If you want maximum strategic clarity:** Option G (Strategic Network) — abstract, functional, analytically pure

**Recommended hybrid path:** Use **Option F (Wargame Board) as the primary game map** for its terrain context and NATO symbology, with **Option G (Strategic Network) as a secondary "adjacency view"** that players can toggle to when analyzing movement paths and strategic connectivity. This gives both immersion and analytical clarity. For print/briefing materials, **Option A or E** remains the cleanest choice.

---

## Files

| File | Description |
|------|-------------|
| `OPTION_A_POLITICAL_ATLAS.svg` | 800x500 SVG sample — pale pastel atlas style (ME region) |
| `OPTION_B_STRATEGIC_BOARD.svg` | 800x500 SVG sample — dark navy board game style (ME region) |
| `OPTION_C_INTELLIGENCE_MAP.svg` | 800x500 SVG sample — parchment military intelligence style (ME region) |
| `OPTION_D_TERRAIN_ATLAS.svg` | 800x500 SVG sample — terrain-rich atlas with pennant units (ME region) |
| `OPTION_E_HEX_WORLD.svg` | 1200x700 SVG — hex tessellation global map, konkr.io inspired |
| `OPTION_F_WARGAME_BOARD.svg` | 1200x700 SVG — dense hex wargame global map, NATO symbology |
| `OPTION_G_STRATEGIC_NETWORK.svg` | 1200x700 SVG — abstract graph/network global map |
| `STYLE_OPTIONS_OVERVIEW.md` | This document |
