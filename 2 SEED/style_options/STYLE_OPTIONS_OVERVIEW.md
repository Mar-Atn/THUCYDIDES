# Thucydides Trap SIM — Visual Style Options
**Date:** 2026-03-26 | **Author:** CANVAS (UX & Visual Design) | **Status:** 4 Options for Review

---

## How to Compare

All four SVG samples show the **same geographic region** — the Middle East theater and its surroundings (Persia, Levantia, Solaria, Mirage, Bharata, Horn of Africa, Phrygia, with Arabian Sea, Persian Gulf, Red Sea, and chokepoints at Hormuz and Bab el-Mandeb). Each includes identical unit deployments and a blockaded Hormuz. Open them side-by-side in a browser for direct comparison.

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

## Files

| File | Description |
|------|-------------|
| `OPTION_A_POLITICAL_ATLAS.svg` | 800x500 SVG sample — pale pastel atlas style |
| `OPTION_B_STRATEGIC_BOARD.svg` | 800x500 SVG sample — dark navy board game style |
| `OPTION_C_INTELLIGENCE_MAP.svg` | 800x500 SVG sample — parchment military intelligence style |
| `OPTION_D_TERRAIN_ATLAS.svg` | 800x500 SVG sample — terrain-rich atlas with pennant units |
| `STYLE_OPTIONS_OVERVIEW.md` | This document |
