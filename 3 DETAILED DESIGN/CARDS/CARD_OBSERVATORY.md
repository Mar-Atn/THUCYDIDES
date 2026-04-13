# CARD: OBSERVATORY — The Interface

**The Observatory is the ONLY user interface for the Unmanned Spacecraft phase.** Everything we build must be visible here. If it's not in the Observatory, it doesn't exist for the observer.

**Existing spec:** `CONCEPT TEST/OBSERVATORY_SPEC_v0_1.md` (v0.1, 2026-04-05)
**UX guide:** `2 SEED/H_UX/SEED_H1_UX_STYLE_v2.md` (Midnight Intelligence)

---

## Purpose

Let the facilitator/observer watch 20-40 AI roles play the Thucydides Trap autonomously across 6-8 rounds. Pause, resume, stop, rewind. Inspect any element. See consequences cascade in real time.

---

## Three Screens

### 1. MAPS (primary view — ~70% of use)

**What it shows:**
- Global hex map (10×20) with country territory colors
- Local theater maps (Eastern Ereb, Mashriq) via drill-down on linked hexes
- All military units positioned on hexes (5 types, country-colored, clustered if crowded)
- Battle markers (💥) on hexes where combat occurred this round 
- Blockade indicators on chokepoints (orange contour: partial, intense orange: full)
- Occupied territory overlay (diagonal stripes: owner color + occupier color)
- Country name labels (italic, centered on territory)
- Chokepoint labels (dashed border, uppercase name)
- Die-hard zone markers (red dashed circle, theater view)
- Embarked unit indicators (mini icons on ships)

**Interactions:**
- Click hex → inspector panel (coordinates, owner, units list, chokepoint info)
- Click theater-link hex twice → drill into local map
- "← Back to Global" button returns to global view

**What's needed but not yet built:**
- Movement animations (800ms tween when units relocate between rounds)
- Attack arrows (dashed red line from attacker to target hex)
- Nuclear site markers on Persia/Choson hexes (need to place them - any hex of that countries' - your choice, need to create and save as seed data in map design data)
- Blockade visualization from declared actions (currently disabled — no false positives)
- Theater-view unit rendering (partially working)

### 2. DASHBOARD (country stats + global indicators)

Need a set of comprehansive dashboards for an external observer - that show the (1) Currnet Status and (2) the dynamic of the sim. 

Need a ThukyDIdes Trap visualisation (two countries summary Columbia vs Cathay: military (focus on naval, nuclear), economic tech, geopolitical (alliances/wars?, overall assessemnt))

Specific indicators to be considered and adjusted. We need to represent a holistic picture of the events in the SIM. Visuals and forms - essential (not just technical tables - think of what is telling the story, provides useful information in  auseful form). 

**Top strip — Global indicators:**
- Oil price ($/bbl) with round-over-round delta
- 3 Main Stock indexes
- Round scrubber (clickable buttons R0, R1, R2... — loads that round's data across all views)

**Summary bar:**
- World GDP total, Average stability, Total forces
- Countries at war / at peace / in collapse
- Nuclear-capable countries count

**Country tiles (20 tiles, 4 columns, sortable):**
- Country name + flag color
- GDP + delta, Treasury + delta, Stability (color-coded), Inflation
- Forces (active + reserve), Political support, Nuclear level, AI level
- Last committed action this round (emoji + type)
- Border color: green (peace), red (at war), grey (collapse)

**Sort options:** by country name, GDP, stability, forces, nuclear level

**What's needed but not yet built:**
- Click tile → expanded country detail drawer (full stats, agent reasoning, memory excerpts, relationship map)
- Sparkline charts per country (GDP, stability over all rounds)
- War/alliance relationship lines between tiles

### 3. ACTIVITY (event feed + filters)

**Filter toolbar (sticky top):**
- Category chips: All | 🌍 Round | 🎯 Action | ⚔ Combat | 🤝 Diplomatic | 💭 Memory (with counts)
- Country dropdown (filter by country)
- Round dropdown (filter by round)
- Search box (text search across summaries)

**Feed:**
- Reverse-chronological event list
- Grouped by round (divider headers)
- Each event: timestamp + emoji + country + summary
- Click to expand: full payload JSON detail
- Event types: round_started, agent_started, agent_committed, combat, movement, mobilization, economic_action, blockade, covert_op, public_statement, transaction, agreement, round_completed

**What's needed but not yet built:**
- Conversation transcripts in feed (bilateral meeting summaries)
- Transaction records (exchange details)
- Agreement records (signatories, terms, public/secret indicator)
- Covert op results (success/detection, with redaction for secret ops)
- Nuclear alerts (global broadcast format)
- Ability to sort by actor, by country, by type of cativity (military, economic, political, technology)

---

## Top Bar (persistent across all screens)

```
[🗺 MAPS] [📊 DASHBOARD] [📜 ACTIVITY]    Round [3/6]  [RUNNING]  ⏱ 02:34  ◷ 00:45

[🆕 New Run] [▶ Start] [⏸ Pause] [⏹ Stop] [⏮ Rewind]  Speed: [15s ▼]  📛 Run Name
```

- Screen nav tabs (only active screen visible)
- Round badge + status badge (IDLE / RUNNING / PAUSED / FINISHED / ERROR)
- Two timers: total elapsed (⏱) + current round elapsed (◷)
- Controls: New Run (wipe + restart), Start, Pause (freezes clock), Stop (hard halt), Rewind
- Speed selector (delay between rounds)
- Run name (user-assigned at start)

**Timer behavior:**
- Running: both timers tick
- Paused / Stopped / Finished: both timers freeze (display final values)
- New Run: both reset to 00:00

---

## Data Sources (what feeds each screen)

| Screen element | API endpoint | DB table | Refresh |
|---|---|---|---|
| Map hex grid | `/api/map/global`, `/api/map/theater/*` | `sim_templates.rules` | Once at load |
| Unit positions | `/api/observatory/units?round=N` | `unit_states_per_round` | Per poll (3s) |
| Country colors | `/api/map/countries` | `countries` | Once at load |
| Country stats | `/api/observatory/countries?round=N` | `country_states_per_round` | Per poll |
| Global indicators | `/api/observatory/global-series` | `global_state_per_round` | Per poll |
| Events | `/api/observatory/events?limit=50` | `observatory_events` | Per poll |
| Combats | `/api/observatory/combats?round=N` | `observatory_combat_results` | Per poll |
| Blockades | `/api/observatory/blockades?round=N` | `agent_decisions` (declare_blockade) | Per poll |
| Runtime state | `/api/observatory/state` | In-memory runtime dict | Per poll |

**Round scrubber:** clicking a past round re-fetches units + countries + combats for that specific round. Poll loop respects scrubbed view (doesn't overwrite with current-round data while browsing history).

---

## Visual Standards

Per SEED_H1 "Midnight Intelligence" style:
- Dark background (`#0d1b2a`), muted borders, monospace for data
- Accent blue (`#5b9bd5`), success green, warning amber, danger red
- Font: heading (Inter/system bold), body (Inter/system), mono (JetBrains Mono/system mono)
- Compact information density — maximum data per pixel
- Subtle animations (transitions ≤300ms, no decoration)
- Hover states for interactive elements, click-to-expand for detail

---

## Implementation Status

| Component | Status |
|---|---|
| 3-screen layout + tab navigation | **LIVE** |
| Global map with territory colors | **LIVE** |
| Theater drill-down | **LIVE** |
| Unit icons (5 types, clustered, colored) | **LIVE** |
| Battle markers (💥 pulse) | **LIVE** |
| Country labels (italic centroid) | **LIVE** |
| Chokepoint markers | **LIVE** |
| Die-hard markers (theater view) | **LIVE** |
| Embarked unit mini-icons | **LIVE** |
| Occupied territory stripes | **LIVE** |
| Dashboard: global strip + round scrubber + chart | **LIVE** |
| Dashboard: country tiles (8 metrics + sort) | **LIVE** |
| Dashboard: summary bar | **LIVE** |
| Activity: filter chips + country/round dropdown + search | **LIVE** |
| Activity: round dividers + expandable events | **LIVE** |
| Top bar: controls + timers + run name | **LIVE** |
| Stop button (hard halt) | **LIVE** |
| Movement animations | **PARTIAL** |
| Attack arrows | **PARTIAL** |
| Country detail drawer | **NOT BUILT** |
| Conversation/transaction feed | **NOT BUILT** |
| Nuclear alert broadcast | **NOT BUILT** |
| Blockade visualization | **STUB** (from declared actions only) |
