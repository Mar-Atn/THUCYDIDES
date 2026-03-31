# TTT UX Style Guide — SEED Level (FROZEN)
## The Thucydides Trap Simulation | Visual Identity & Design System
**Version:** 2.0 | **Date:** 2026-03-29 | **Status:** APPROVED — READY TO FREEZE
**Owner:** CANVAS | **Approval:** Marat

---

## 1. Design Philosophy

**"The Economist meets McKinsey — with just enough game to remind you this isn't real. Yet."**

### Core Principles
1. **Intellectual Authority** — Typography-led. Clean information hierarchy.
2. **Data-Rich Clarity** — High density, never cluttered. Whitespace is a tool.
3. **Restrained Drama** — Content is dramatic. Design is calm.
4. **Fictional Coherence** — Abstract emblems, fictional names, no real-world flags.
5. **Cross-Platform Consistency** — Same language on web, print, slides, badges.

---

## 2. Color System — Dual Theme

### Light Theme: "Strategic Paper" (DEFAULT)
| Token | Hex | Usage |
|-------|-----|-------|
| `base` | #F5F6F8 | Page background |
| `card` | #FFFFFF | Card/panel background |
| `border` | #D8DCE5 | Borders, dividers |
| `text-primary` | #1A2332 | Main text |
| `text-secondary` | #4A5568 | Secondary text |
| `action` | #1A5276 | Primary buttons, links |
| `accent` | #C4922A | Key metrics, highlights |
| `success` | #2E7D4F | Positive changes |
| `warning` | #B8762E | Caution states |
| `danger` | #B03A3A | Crisis, military alerts |

### Dark Theme: "Midnight Intelligence" (SECONDARY)
| Token | Hex | Usage |
|-------|-----|-------|
| `base` | #0D1B2A | Page background |
| `card` | #1B2A3E | Card/panel background |
| `border` | #253D54 | Borders, dividers |
| `text-primary` | #D4DEE8 | Main text |
| `text-secondary` | #7A8FA3 | Secondary text |
| `action` | #5B9BD5 | Primary buttons, links |
| `accent` | #E8B84D | Key metrics, highlights |
| `success` | #5BAD7A | Positive |
| `warning` | #D4A040 | Caution |
| `danger` | #D45B5B | Crisis |

---

## 3. Country Colors — Unified Dual Palette

Each country has THREE color values from the SAME hue family:
- **Map** (muted) — territory fill on hex maps
- **UI** (vivid) — badges, icons, chart lines, unit markers
- **Light** — badge background tint

### Western Treaty Bloc (EU members harmonized in blue-green-teal)
| Country | UI Vivid | Map Muted | Light BG |
|---------|----------|-----------|----------|
| Columbia | #3A6B9F | #9AB5D0 | #E8EFF6 |
| Gallia | #4A6FA0 | #A5B8D4 | #EBF0F6 |
| Teutonia | #3A8A7A | #8AB5AA | #E8F2EF |
| Thule | #3A8A7A | #8AB5AA | #E8F2EF |
| Albion | #4A7A8F | #8AA5B5 | #E8EFF3 |
| Freeland | #5A80A0 | #A0B8C8 | #EBF1F5 |
| Ponte | #6A9A8A | #A5C8B8 | #EBF3EF |
| Levantia | #9A9A40 | #D4D4A5 | #F3F3E8 |
| Yamato | #5A7A9B | #A5B5C8 | #EBF0F5 |

### League Bloc (warm reds, earth tones)
| Country | UI Vivid | Map Muted | Light BG |
|---------|----------|-----------|----------|
| Cathay | #C4A030 | #E8D5A3 | #F8F2E5 |
| Sarmatia | #A06060 | #D4A5A5 | #F5EAEA |
| Persia | #9A7040 | #C8A57A | #F2EBE0 |
| Choson | #5A5A5A | #8A8A8A | #EFEFEF |

### Non-Aligned / Swing
| Country | UI Vivid | Map Muted | Light BG |
|---------|----------|-----------|----------|
| Bharata | #B87850 | #D4B5A5 | #F5EDE5 |
| Formosa | #B89048 | #DCC5A0 | #F5EEE0 |
| Hanguk | #4A8FA8 | #A5C8D4 | #E8F1F5 |
| Phrygia | #8A6A48 | #B5A08A | #F0EBE5 |
| Solaria | #A89030 | #C8B896 | #F3F0E5 |
| Mirage | #A88050 | #D4BFA5 | #F5EEE5 |

### War / Special
| Country | UI Vivid | Map Muted | Light BG |
|---------|----------|-----------|----------|
| Ruthenia | #5A9A5A | #A5C8A5 | #EBF3EB |
| Caribe | #3A7AAA | #8AACCC | #E8F0F6 |

### Contested
| Country | UI Vivid | Map Muted | Light BG |
|---------|----------|-----------|----------|
| Sogdiana | #8A8A60 | #C8C8A5 | #F0F0E8 |
| Horn | #8A7A68 | #B5A896 | #F0ECE8 |

---

## 4. Typography

### Fonts
| Role | Font | Weights | Source |
|------|------|---------|--------|
| Headings | Playfair Display | 600, 700 | Google Fonts |
| Body | DM Sans | 400, 500, 600 | Google Fonts (MetaGames site font) |
| Data/Numbers | JetBrains Mono | 400, 500 | Google Fonts |
| Map labels | Playfair Display | 600, small caps | Google Fonts |

### Type Scale
| Token | Size | Weight | Usage |
|-------|------|--------|-------|
| `display` | 2.5rem (40px) | Bold | Hero titles |
| `h1` | 1.75rem (28px) | Bold | Page titles |
| `h2` | 1.375rem (22px) | Semibold | Section headings |
| `h3` | 1.125rem (18px) | Semibold | Card titles |
| `body` | 1rem (16px) | Regular | Default body |
| `body-sm` | 0.875rem (14px) | Regular | Secondary text |
| `caption` | 0.75rem (12px) | Medium | Labels, timestamps |
| `data` | 1rem (16px) | Mono Medium | Numbers, metrics |
| `data-lg` | 1.5rem (24px) | Mono Bold | Key metric displays |

---

## 5. Country Emblem System

**Style:** Geometric Abstract (Bauhaus/Isotype)
**Format:** SVG, 24×24 viewBox, monochrome using country UI color
**Sizes:** 16px (inline), 24px (badge), 48px (card), 96px (print cover)

All 23 territories + 6 organizations have geometric emblems.
See `SEED_H1_UX_STYLE_DEMO_FINAL.html` Section 3 for full inventory.

---

## 6. Military Unit Icon System

**Style:** Flat filled silhouettes, monochrome, country-colored
**Format:** SVG, 24×24 viewBox
**Canonical paths:** `H_VISUAL/assets/UNIT_ICONS_CONFIRMED.svg`

| Unit Type | Icon | Map Size | Notes |
|-----------|------|----------|-------|
| Naval | Warship side profile | **19px** (20% larger) | Stepped superstructure |
| Ground (→) | Tank V4 sloped front | 16px | Faces right (attacker/default) |
| Ground (←) | Tank V4 mirrored | 16px | Faces left (defender/opposing) |
| Tactical Air | Drone/UAV with sensor dome | 14px | Top-down view |
| Air Defense | Radar dish umbrella | 16px | Arc + mast + base |
| Strategic | ICBM vertical | 16px | Pointed missile with fins |

**Rendering rules:**
- 3 tank fill paths (no stroke) + 1 outer outline path (stroke only) = no internal stripes
- Enemy tanks face each other on theater maps
- Multiple units stack in rows (3 per row, 60% overlap)
- White stroke outline (0.5-0.6px) for visibility when overlapping
- Icons can extend slightly outside hex boundary

---

## 7. Map System

### Global Map
- 10×20 hex grid, 1-indexed (rows 1-10, cols 1-20)
- Country territories in muted (map) colors at 55% opacity
- Water hexes in #D4E4F0 (light) or #1B2A3E (dark)
- Watermark geometric emblems on every land hex (12% opacity)
- Country names at geometric centroid of territory
- Chokepoint names INSIDE hex, subtle dashed border (1.2px, 70% opacity)
- Grid labels on edges (1-indexed)
- Naval units as 19px warship icons, ground as 16px tanks, air as 14px drones

### Theater Map (Eastern Ereb)
- 10×10 hex grid, 1-indexed
- Sarmatia tanks face LEFT, Ruthenia tanks face RIGHT
- Occupied zones: striped pattern (owner color + occupier stripes)
- Die Hard position marked with dashed circle
- 70% max-width container (proportional to global map)

---

## 8. MetaGames Logo Usage

**Asset:** `assets/logo-metagames.png` — Stylized "M" mark in navy (#1A2A44)
**Format:** PNG with transparent background. Navy mark on white/light, or at reduced opacity on dark.

### Placement Rules
| Context | Size | Position | Treatment |
|---------|------|----------|-----------|
| Web app nav bar | 20-24px height | Top-left, with "MetaGames" text | Full color + text |
| Presentation slide footer | 16px height | Bottom-left | Reduced opacity (60%) + text |
| Print materials footer | 12-14px height | Bottom-right | Grayscale or low opacity + text |
| Name badge | 12px height | Bottom area | Small, with "MetaGames" text |
| Landing page | 28-32px height | Top-left nav | Full color + text |
| Public display | 20px height | Bottom-right corner | Subtle, low opacity |

### Rules
- Always pair the mark with "MetaGames" text (DM Sans 600) at small sizes
- Mark can stand alone at 32px+ where brand is already established
- On dark backgrounds: use at 50-60% opacity or in white/light treatment
- Never stretch, rotate, or recolor the mark
- Minimum clear space: 50% of mark height on all sides

---

## 9. Platform Applications

### Web App
- Default: Light theme. Dark available via toggle.
- MetaGames logo: top-left nav bar, 28px height
- Responsive: desktop-first, tablet breakpoint

### Print Materials
- Always light theme
- MetaGames logo: bottom-right, small, grayscale
- Country emblem large on covers, small in headers
- A4, 20mm margins

### Presentations
- Dark theme for projection (Midnight Intelligence)
- 16:9, MetaGames logo bottom-left, TTT bottom-right
- Playfair Display titles, DM Sans content, JetBrains Mono data

### Event Materials
- Name badges: country color band top, emblem + character name + title
- Table signs: country emblem + name
- Schedule board: round timeline with accent gold highlight

---

## 9. Assets & Files

| Asset | Location | Status |
|-------|----------|--------|
| Unit icon SVGs | `H_VISUAL/assets/UNIT_ICONS_CONFIRMED.svg` | FROZEN |
| MetaGames logo | `H_VISUAL/assets/logo-metagames.png` | FROZEN |
| Style demo HTML | `H_VISUAL/SEED_H1_UX_STYLE_DEMO_FINAL.html` | FROZEN |
| Country colors (v2 draft) | `H_VISUAL/SEED_H1_COUNTRY_COLORS_v2.html` | Reference |
| Emblem exploration | `H_VISUAL/SEED_H1_EMBLEM_OPTIONS_v1.html` | Reference |
| Map JSON (with colors) | `C_MECHANICS/C1_MAP/SEED_C1_MAP_GLOBAL_STATE_v4.json` | Updated |
| This document | `H_VISUAL/SEED_H1_UX_STYLE_v2.md` | FROZEN |

---

## 10. Tailwind Configuration

```javascript
// tailwind.config.js — TTT theme
module.exports = {
  theme: {
    extend: {
      colors: {
        base: { DEFAULT: '#F5F6F8', dark: '#0D1B2A' },
        card: { DEFAULT: '#FFFFFF', dark: '#1B2A3E' },
        border: { DEFAULT: '#D8DCE5', dark: '#253D54' },
        text: { primary: '#1A2332', secondary: '#4A5568', muted: '#8494A7' },
        action: { DEFAULT: '#1A5276', dark: '#5B9BD5' },
        accent: { DEFAULT: '#C4922A', dark: '#E8B84D' },
        success: { DEFAULT: '#2E7D4F', dark: '#5BAD7A' },
        warning: { DEFAULT: '#B8762E', dark: '#D4A040' },
        danger: { DEFAULT: '#B03A3A', dark: '#D45B5B' },
        country: {
          columbia: { DEFAULT: '#3A6B9F', map: '#9AB5D0', light: '#E8EFF6' },
          cathay: { DEFAULT: '#C4A030', map: '#E8D5A3', light: '#F8F2E5' },
          sarmatia: { DEFAULT: '#A06060', map: '#D4A5A5', light: '#F5EAEA' },
          ruthenia: { DEFAULT: '#5A9A5A', map: '#A5C8A5', light: '#EBF3EB' },
          persia: { DEFAULT: '#9A7040', map: '#C8A57A', light: '#F2EBE0' },
          gallia: { DEFAULT: '#4A6FA0', map: '#A5B8D4', light: '#EBF0F6' },
          teutonia: { DEFAULT: '#3A8A7A', map: '#8AB5AA', light: '#E8F2EF' },
          albion: { DEFAULT: '#4A7A8F', map: '#8AA5B5', light: '#E8EFF3' },
          freeland: { DEFAULT: '#5A80A0', map: '#A0B8C8', light: '#EBF1F5' },
          ponte: { DEFAULT: '#6A9A8A', map: '#A5C8B8', light: '#EBF3EF' },
          bharata: { DEFAULT: '#B87850', map: '#D4B5A5', light: '#F5EDE5' },
          formosa: { DEFAULT: '#B89048', map: '#DCC5A0', light: '#F5EEE0' },
          yamato: { DEFAULT: '#5A7A9B', map: '#A5B5C8', light: '#EBF0F5' },
          hanguk: { DEFAULT: '#4A8FA8', map: '#A5C8D4', light: '#E8F1F5' },
          phrygia: { DEFAULT: '#8A6A48', map: '#B5A08A', light: '#F0EBE5' },
          solaria: { DEFAULT: '#A89030', map: '#C8B896', light: '#F3F0E5' },
          mirage: { DEFAULT: '#A88050', map: '#D4BFA5', light: '#F5EEE5' },
          levantia: { DEFAULT: '#9A9A40', map: '#D4D4A5', light: '#F3F3E8' },
          choson: { DEFAULT: '#5A5A5A', map: '#8A8A8A', light: '#EFEFEF' },
          caribe: { DEFAULT: '#3A7AAA', map: '#8AACCC', light: '#E8F0F6' },
          sogdiana: { DEFAULT: '#8A8A60', map: '#C8C8A5', light: '#F0F0E8' },
          horn: { DEFAULT: '#8A7A68', map: '#B5A896', light: '#F0ECE8' },
        }
      },
      fontFamily: {
        heading: ['Playfair Display', 'Georgia', 'serif'],
        body: ['DM Sans', 'system-ui', 'sans-serif'],
        data: ['JetBrains Mono', 'monospace'],
      },
    }
  }
}
```

---

*This document is FROZEN at SEED level. Changes require Marat's approval per CLAUDE.md Section 7.2 Rule 4.*
