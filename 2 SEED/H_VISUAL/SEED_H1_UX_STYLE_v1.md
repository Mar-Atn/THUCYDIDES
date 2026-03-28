# TTT UX Style Guide — SEED Level
## The Thucydides Trap Simulation | Visual Identity & Design System
**Version:** 1.0 DRAFT | **Date:** 2026-03-28 | **Status:** OPTIONS FOR REVIEW
**Owner:** CANVAS | **Approval:** Marat

---

## 1. Design Philosophy

### The Feeling
**"The Economist meets McKinsey — with just enough game to remind you this isn't real. Yet."**

TTT is a premium intellectual experience for professionals. The visual identity signals: this is serious, smart, complex, and powered by modern technology. It is NOT a video game. It is NOT a military command system. It is a strategic thinking environment where leaders face real dilemmas in a fictional world.

### Core Principles

1. **Intellectual Authority** — Typography-led, not illustration-led. Clean information hierarchy. Like reading a premium strategy publication that happens to be interactive.

2. **Data-Rich Clarity** — High information density (GDP, stability, military, oil, tech) that is never cluttered. Every number has a place. Every chart tells a story. Whitespace is a tool, not waste.

3. **Restrained Drama** — The CONTENT is dramatic (wars, nuclear threats, economic collapse). The DESIGN is calm. Let the scenario create tension. The interface stays composed. No flashy animations, no aggressive colors, no sensationalism.

4. **Fictional Coherence** — Everything reinforces the parallel world. Abstract country emblems (not real flags). Fictional place names on maps. Consistent visual vocabulary that is distinctly TTT — not borrowed from any real government or military.

5. **Cross-Platform Consistency** — The same visual language works on a web dashboard, a printed role brief, a presentation slide, a name badge, and a landing page. Different formats, same identity.

---

## 2. Color System

### Three Options for Review

---

### OPTION A: "Situation Room" (Dark Base)
*Cool, authoritative, high-tech. Like a strategic command center designed by a luxury brand.*

**Base palette:**
| Token | Hex | Usage |
|-------|-----|-------|
| `base-900` | #0F1923 | App background |
| `base-800` | #1B2838 | Card/panel background |
| `base-700` | #243447 | Elevated surfaces |
| `base-600` | #2E4259 | Borders, subtle dividers |
| `text-primary` | #E8ECF1 | Main text |
| `text-secondary` | #8899AA | Secondary text, labels |
| `text-muted` | #5A6B7D | Tertiary, timestamps |

**Accent colors:**
| Token | Hex | Usage |
|-------|-----|-------|
| `action-primary` | #4A8EC2 | Primary buttons, links, active states |
| `action-hover` | #3A7EB2 | Hover state |
| `accent-gold` | #D4A843 | Key metrics, warnings, important highlights |
| `accent-gold-muted` | #B89438 | Secondary gold |
| `success` | #4A8C6A | Positive changes, ceasefire, growth |
| `warning` | #C4873A | Caution, approaching thresholds |
| `danger` | #C25454 | Crisis, collapse, military alerts |
| `info` | #5B8DB8 | Informational, neutral updates |

**When to use:** Web app (primary), test dashboards, facilitator screens, public display. Print materials use the Light variant (Option B inverted).

**Emotional register:** Controlled tension. Calm authority. "We have the information. Now decide."

---

### OPTION B: "Strategic Paper" (Light Base)
*Editorial, clean, The Economist. Like a beautifully designed briefing document that became interactive.*

**Base palette:**
| Token | Hex | Usage |
|-------|-----|-------|
| `base-50` | #F5F6F8 | App background (cool paper) |
| `base-100` | #EBEDF2 | Card backgrounds |
| `base-200` | #D8DCE5 | Borders, dividers |
| `base-300` | #B8BFC9 | Subtle elements |
| `text-primary` | #1A2332 | Main text (near-black, warm) |
| `text-secondary` | #4A5568 | Secondary text |
| `text-muted` | #8494A7 | Tertiary |

**Accent colors:**
| Token | Hex | Usage |
|-------|-----|-------|
| `action-primary` | #1A5276 | Primary buttons, links (deep teal) |
| `action-hover` | #154360 | Hover |
| `accent-gold` | #C4922A | Key metrics, highlights |
| `accent-red` | #B03A3A | Crisis, military, danger |
| `success` | #2E7D4F | Growth, peace, positive |
| `warning` | #B8762E | Approaching thresholds |
| `info` | #2C6FA0 | Informational |

**When to use:** Print materials (primary), presentations, landing page. Web app could use this for a lighter feel.

**Emotional register:** Thoughtful authority. "This is important reading. Pay attention."

---

### OPTION C: "Hybrid" (Dark App + Light Print)
*Best of both: dark web interface for immersion during gameplay, light templates for everything printed or projected.*

- **Web app, facilitator, public display:** Use Option A palette (dark)
- **Role briefs, presentations, badges, landing page:** Use Option B palette (light)
- **Shared elements:** Country colors, typography, emblems, spacing are identical across both modes
- **Map:** Dark background on screen, light background in print

**This is the recommended approach.** Most SIM apps use dark interfaces (immersion, readability in dim venues) while print materials must be light (ink economy, readability, professional appearance).

---

### Country Colors (21 Countries)

Organized by geopolitical alignment for intuitive grouping:

**Western Treaty Bloc (Blues/Teals):**
| Country | Hex | Light BG | Emblem |
|---------|-----|----------|--------|
| Columbia | #4A90D9 | #E8F1FA | ☆ Star (5-point) |
| Gallia | #2E86AB | #E6F1F5 | ⬡ Hexagonal tower |
| Teutonia | #5B7FA6 | #EBF0F5 | ◆ Anvil |
| Albion | #3B6E8F | #E8EEF3 | △ Crown point |
| Freeland | #4AA0A0 | #E8F3F3 | ▢ Shield |
| Ponte | #7B9CB8 | #EEF2F6 | ○ Column |

**League Bloc (Reds/Ambers):**
| Country | Hex | Light BG | Emblem |
|---------|-----|----------|--------|
| Cathay | #D94A4A | #FAE8E8 | ⬡ Layered hexagon |
| Nordostan | #808080 | #F0F0F0 | ◇ Diamond |
| Persia | #4AD97A | #E8FAF0 | ☽ Crescent |
| Choson | #8B4513 | #F3EBE5 | ✶ Burst |
| Caribe | #CC7722 | #F7EEE3 | ◎ Sun circle |

**Non-Aligned / Swing States:**
| Country | Hex | Light BG | Emblem |
|---------|-----|----------|--------|
| Bharata | #E67E22 | #F9F0E5 | ◉ Wheel |
| Formosa | #3498DB | #E7F1F9 | ▽ Chip (semiconductor) |
| Yamato | #1ABC9C | #E4F6F1 | ⊞ Rising grid |
| Hanguk | #2ECC71 | #E6F8ED | ⊕ Circuit |
| Phrygia | #9B59B6 | #F2EAF6 | ☾ Bridge (Bosphorus) |

**At War / Under Pressure:**
| Country | Hex | Light BG | Emblem |
|---------|-----|----------|--------|
| Heartland | #D4A843 | #F8F2E5 | ⛨ Shield (defensive) |
| Levantia | #5DADE2 | #EAF4F9 | ✡ Star of points |
| Solaria | #F1C40F | #FBF5E0 | ☀ Sun |
| Mirage | #A569BD | #F0E8F4 | ◈ Faceted gem |

**Organizations:**
| Org | Hex | Emblem |
|-----|-----|--------|
| Western Treaty (NATO) | #3A6FA0 | Compass rose |
| The League (BRICS+) | #C0392B | Interlocked circles |
| The Cartel (OPEC+) | #F39C12 | Oil drop |
| The Union (EU) | #2E4057 | Ring of dots |
| The Council (UNSC) | #1A5276 | Globe outline |

**Note:** Emblems will be designed as simple SVG icons — geometric, abstract, approximately 24×24px at minimum size. Style: single-weight line art or filled geometric shapes. NOT pictographic, NOT realistic. Think: what a stamp seal would look like if designed by Dieter Rams.

---

## 3. Typography

### Font Selection (Confirm with MetaGames site font)

**Option A — Editorial Authority:**
- Headings: **Playfair Display** (high-contrast serif, Economist/FT feel)
- Body: **Inter** (clean sans-serif, same as KING — MetaGames consistency)
- Data: **JetBrains Mono** (monospace for numbers, engine output)

**Option B — Corporate Strategy:**
- Headings: **Source Serif 4** (neutral professional serif, McKinsey/BCG feel)
- Body: **Inter**
- Data: **IBM Plex Mono**

**Option C — Modern Authority (if MetaGames site uses a sans-serif):**
- Headings: **Inter 700** (bold weight of body font — ultra-clean, no serif)
- Body: **Inter 400**
- Data: **Inter Mono** or **JetBrains Mono**
- Accent text (country names on maps): **Cinzel** (classical serif — subtle nod to ancient origins of Thucydides)

### Type Scale

| Token | Size | Weight | Usage |
|-------|------|--------|-------|
| `display` | 2.5rem (40px) | Bold | Hero titles, landing page headings |
| `h1` | 1.75rem (28px) | Bold | Page titles ("Columbia Dashboard") |
| `h2` | 1.375rem (22px) | Semibold | Section headings ("Economic Status") |
| `h3` | 1.125rem (18px) | Semibold | Card titles ("GDP Trajectory") |
| `body` | 1rem (16px) | Regular | Default body text |
| `body-sm` | 0.875rem (14px) | Regular | Secondary text, table cells |
| `caption` | 0.75rem (12px) | Medium | Labels, timestamps, chart annotations |
| `data` | 1rem (16px) | Mono Medium | Numbers, metrics, engine output |
| `data-lg` | 1.5rem (24px) | Mono Bold | Key metric displays (GDP: 280, Oil: $198) |

### Map Typography
- Country names: Heading font, SMALL CAPS, letter-spacing +0.1em
- Zone labels: Caption size, uppercase
- Chokepoint labels: Caption size, italic, accent color
- Water labels: Caption size, italic, muted color

---

## 4. Spacing & Layout

### Grid System
- **Web app:** 12-column grid, 24px gutters, max-width 1440px
- **Print (A4):** 20mm margins, 2-column layout for role briefs, single column for narratives
- **Presentation (16:9):** Safe area with 48px margins, content in center 80%

### Spacing Scale
| Token | Value | Usage |
|-------|-------|-------|
| `xs` | 4px | Tight: icon-to-text, inline elements |
| `sm` | 8px | Small: between related items |
| `md` | 16px | Standard: between components |
| `lg` | 24px | Large: between sections |
| `xl` | 32px | Extra: between major areas |
| `2xl` | 48px | Hero: page-level separations |

### Card Pattern
The primary container for information groups:
- Padding: `lg` (24px)
- Border-radius: 8px
- Border: 1px `base-600` (dark) or `base-200` (light)
- No drop shadow (flat, editorial)
- Header: `h3` + optional subtitle in `text-secondary`

### Dashboard Layout (Web App)
```
┌─────────────────────────────────────────────────┐
│ TOP BAR: MetaGames logo │ SIM name │ Round │ Timer │ Role  │
├────────┬────────────────────────────────────────┤
│ NAV    │ MAIN CONTENT AREA                      │
│        │                                        │
│ Home   │ ┌──────────┐ ┌──────────┐              │
│ Map    │ │ Card 1   │ │ Card 2   │              │
│ Budget │ │ GDP: 280 │ │ Oil: $198│              │
│ Military│ └──────────┘ └──────────┘              │
│ Diplo  │                                        │
│ Intel  │ ┌─────────────────────────┐            │
│ Comms  │ │ Map / Chart Area        │            │
│        │ │                         │            │
│        │ └─────────────────────────┘            │
├────────┴────────────────────────────────────────┤
│ BOTTOM: Status bar │ Economic state │ Alerts     │
└─────────────────────────────────────────────────┘
```

---

## 5. Country Emblem System

### Design Direction: Abstract Geometric Pictograms

Inspired by ancient seal marks and modern information design. Each country gets one emblem — a simple geometric shape or abstract pictogram that:
- Works at 16px (icon), 32px (badge), 64px (card), 128px+ (print)
- Is recognizable in monochrome (color adds identity, not information)
- Has NO resemblance to real-world flags, coats of arms, or national symbols
- Follows a consistent line weight and geometric vocabulary

### Style Reference
Think: **Egyptian hieroglyphic simplicity** meets **Isotype (Otto Neurath) pictograms** meets **modern app icons.** Abstract, geometric, single-concept-per-mark. All drawn on the same grid (24×24 base), same stroke weight (2px at 24px scale), same corner radius (2px).

### Emblem Assignments (To Be Designed as SVG)

| Country | Concept | Description |
|---------|---------|-------------|
| Columbia | Authority | Five-point star — hegemonic, central |
| Cathay | Structure | Nested hexagon — layered, expansive |
| Nordostan | Hardness | Angular diamond — hard, unyielding |
| Heartland | Defense | Upward shield — protecting, enduring |
| Persia | Arc | Crescent form — historical, curved tension |
| Gallia | Elevation | Vertical tower — proud, independent |
| Teutonia | Industry | Anvil/cog — productive, solid |
| Albion | Reach | Triangle/crown point — maritime, projection |
| Freeland | Stability | Solid square — grounded, determined |
| Ponte | Heritage | Column/arch — ancient, structural |
| Bharata | Balance | Wheel/circle — non-aligned, turning |
| Formosa | Technology | Chip/grid — semiconductor, modern |
| Yamato | Precision | Rising grid — ordered, ascending |
| Hanguk | Innovation | Circuit node — connected, technical |
| Phrygia | Connection | Bridge form — crossroads, linking |
| Solaria | Energy | Sun burst — resource, power |
| Mirage | Facets | Faceted diamond — financial, polished |
| Levantia | Points | Multi-point star — defense in all directions |
| Choson | Threat | Spike/burst — sharp, unpredictable |
| Caribe | Survival | Sun circle — endurance, heat |
| Sogdiana | Contested | Fragmented square — broken, disputed |

### Organization Emblems
| Org | Concept | Description |
|-----|---------|-------------|
| Western Treaty | Navigation | Compass rose — direction, alliance |
| The League | Unity | Interlocked circles — partnership, alternative |
| The Cartel | Resource | Drop — oil, energy control |
| The Union | Integration | Ring of dots — member states, consensus |
| The Council | Authority | Globe outline — world governance |
| The Seven | Coordination | Seven-point form — elite economic club |

---

## 6. Component Patterns

### Data Display Cards
```
┌──────────────────────────┐
│ h3: GDP                  │ ← heading font, semibold
│ caption: Coins (billions)│ ← caption, text-secondary
│                          │
│ data-lg: 280.4          │ ← mono font, large, text-primary
│ ▲ +1.8%                 │ ← success color, small
│                          │
│ ───── sparkline ─────    │ ← thin line chart, last 8 rounds
└──────────────────────────┘
```

### Status Indicators
- **Normal:** `text-secondary`, no highlight
- **Stressed:** `warning` color, subtle left border
- **Crisis:** `danger` color, stronger left border
- **Collapse:** `danger` background tint, pulsing (subtle)

### Country Badge (in lists, tables, chat)
```
[◇ Nordostan]  ← emblem + name, country color background tint
```

### Alert Types
| Type | Color | Icon | Usage |
|------|-------|------|-------|
| Military alert | `danger` | ⚔ | Attack, missile launch, blockade |
| Diplomatic | `action-primary` | ✉ | Treaty, meeting request, proposal |
| Economic | `accent-gold` | ◆ | Oil price change, sanctions, OPEC |
| Election | `info` | ☐ | Scheduled election, results |
| Covert | `text-muted` | ◌ | Detected operation, intelligence |

---

## 7. Platform-Specific Applications

### 7.1 Web App (React / Tailwind)
- **Theme:** Dark base (Option A) as default
- **MetaGames logo:** Top-left corner of nav bar, compact (28px height)
- **Responsive:** Desktop-first (most participants use laptops/tablets), mobile breakpoint for facilitator on-the-go
- **Charts:** Chart.js or Recharts, using country color palette
- **Maps:** SVG hex maps, country colors for territories, dark ocean, muted grid lines

### 7.2 Printed Role Briefs (HTML/CSS → PDF)
- **Theme:** Light base (Option B)
- **Layout:** A4, 2-column for body, full-width for headers and maps
- **MetaGames logo:** Bottom-right corner, small, grayscale
- **Country emblem:** Large (64px) on cover page, small (24px) in headers
- **Classification marking:** "CLASSIFIED — [Country Name] Eyes Only" in `danger` color at top
- **Paper stock:** Recommend 120gsm uncoated for tactile quality

### 7.3 Presentations (PPT / Google Slides)
- **Theme:** Dark base for intro/outro, light base for content slides
- **Layout:** 16:9, MetaGames logo bottom-left, TTT title bottom-right
- **Title slide:** Large country emblem, country name in heading font, subtitle in body font
- **Data slides:** Chart left, key findings right. Max 3 data points per slide.
- **Transition slides (between rounds):** Full-bleed dark background, round number centered, dramatic pause

### 7.4 Event Materials
- **Name badges:** Country color band at top, character name in heading font (large), country name + emblem below, participant real name in body font (small). Lanyard color matches country.
- **Table signs:** Country name + emblem, colored triangle tent cards.
- **Room signage:** "Meeting Room — [Name]" in heading font, directional arrows in body font.
- **Schedule board:** Round timeline, current round highlighted in `accent-gold`.

### 7.5 Landing/Registration Page
- **Theme:** Light base (Option B), generous whitespace
- **Hero section:** TTT title in display size, one-line tagline, dramatic background image (abstract, not photographic — could be stylized hex grid or map fragment)
- **MetaGames logo:** Top nav bar, standard size
- **CTA:** "Register" button in `action-primary`
- **Content sections:** What is TTT, who is it for, what participants say, logistics
- **Tone:** Professional, intellectual curiosity — "Are you ready to lead when the world is watching?"

---

## 8. MetaGames Brand Integration

### Logo Usage
- **Web app nav bar:** Compact horizontal lockup (logomark + "MetaGames"), 28px height, `text-secondary` color
- **Print materials footer:** Grayscale logomark only, 16px height, bottom-right
- **Presentations:** Full color horizontal lockup, bottom-left of every slide, 24px height
- **Landing page:** Full color horizontal lockup, top-left nav, standard size
- **Public display:** Full color, bottom-right corner, 32px height

### Co-Branding (with client organizations)
- Client logo: top-right of landing page and registration
- MetaGames logo: top-left
- Role briefs and in-app: MetaGames only (the experience is MetaGames-delivered)

---

## 9. Visual Mock-Up Specifications (To Be Produced)

The following mock-ups should be created to validate the style guide before implementation:

### Mock-Up Set A: Web App
1. **Participant dashboard** — Columbia's Dealer view, showing GDP card, map preview, message list, round timer
2. **Map screen** — Global hex map with all 21 countries colored, chokepoints marked, unit indicators
3. **Facilitator dashboard** — God-view with all countries' key metrics in a grid

### Mock-Up Set B: Print
4. **Role brief cover page** — "DEALER — President of Columbia" with emblem, classification marking, country color
5. **Role brief interior page** — 2-column layout with character bio, objectives table, ticking clock section
6. **Intelligence report** — Classified document style, country emblem watermark

### Mock-Up Set C: Presentation
7. **Title slide** — "The Thucydides Trap" with TTT visual identity
8. **World briefing slide** — Key metrics in cards, minimap, round indicator
9. **Debrief slide** — Learning outcomes, behavioral insights format

### Mock-Up Set D: Event
10. **Name badge** — Front: character name, country, emblem. Back: schedule, WiFi, emergency.
11. **Landing page** — Hero + 3 content sections + registration CTA

---

## 10. Implementation Notes

### Tailwind Config Structure (following KING pattern)
```javascript
// tailwind.config.js — TTT theme
module.exports = {
  theme: {
    extend: {
      colors: {
        base: { 900: '#0F1923', 800: '#1B2838', 700: '#243447', 600: '#2E4259' },
        text: { primary: '#E8ECF1', secondary: '#8899AA', muted: '#5A6B7D' },
        action: { primary: '#4A8EC2', hover: '#3A7EB2' },
        accent: { gold: '#D4A843', 'gold-muted': '#B89438' },
        success: { DEFAULT: '#4A8C6A' },
        warning: { DEFAULT: '#C4873A' },
        danger: { DEFAULT: '#C25454' },
        // Country colors...
        country: {
          columbia: { DEFAULT: '#4A90D9', light: '#E8F1FA' },
          cathay: { DEFAULT: '#D94A4A', light: '#FAE8E8' },
          // ... all 21
        }
      },
      fontFamily: {
        heading: ['Playfair Display', 'Georgia', 'serif'],  // Option A
        // heading: ['Source Serif 4', 'Georgia', 'serif'],  // Option B
        body: ['Inter', 'system-ui', 'sans-serif'],
        data: ['JetBrains Mono', 'monospace'],
        map: ['Cinzel', 'serif'],  // Country names on maps
      },
      fontSize: { /* as defined in Type Scale */ },
      spacing: { /* as defined in Spacing Scale */ },
    }
  }
}
```

### Design Token Export
All colors, fonts, and spacing should be exported as:
- CSS custom properties (for web)
- Tailwind config (for React implementation)
- Figma variables (for design team, if applicable)
- SCSS variables (for print CSS)

---

## Decisions Needed from Marat

| # | Decision | Options | Impact |
|---|----------|---------|--------|
| 1 | **Color theme** | A (Dark), B (Light), C (Hybrid — recommended) | Everything |
| 2 | **Heading font** | Playfair Display (editorial), Source Serif 4 (corporate), Inter Bold (modern) | Personality |
| 3 | **MetaGames site font** | Need to confirm — affects body font choice | Consistency |
| 4 | **Emblem style** | Geometric abstract (proposed), or different pictographic style? | Country identity |
| 5 | **Mock-ups priority** | Which 3-4 of the 11 mock-ups to produce first? | Next sprint |

---

*This document is a SEED-level specification. It will be refined during Detailed Design when actual React components are built. The goal at SEED is to establish the visual language firmly enough that all downstream work (app, print, presentations, events) can be produced consistently without re-inventing the style each time.*
