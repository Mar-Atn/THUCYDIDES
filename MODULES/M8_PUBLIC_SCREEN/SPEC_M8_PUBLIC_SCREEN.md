# M8 — Public Screen SPEC

**Version:** 1.0 | **Date:** 2026-04-16
**Status:** DRAFT
**Dependencies:** M4 (sim runner), M3 (data), M1 (engines)

---

## 1. What This Is

The Public Screen is the focal point of the simulation room — projected on a large screen/TV visible to all participants. It is NOT an information tool (participants have their own interfaces). It is a **visual heartbeat of the Trap** — showing the competitive dynamic, rising tensions, and consequences of collective decisions.

Think: **war room situation display** meets **stock exchange ticker** meets **doomsday clock**.

---

## 2. Layout

Full screen, dark background (`#0A0E1A`), high contrast. No scrolling — everything visible at once.

```
┌──────────────────────────────────────────────────────────────────┐
│  ROUND 3 · Phase A · 42:17                    H1 2028           │ ← Header
├────────────────────────────────────┬─────────────────────────────┤
│                                    │  GEOPOLITICAL TENSION  7/10 │
│                                    │  ████████░░  ↑ from 5       │
│          GLOBAL MAP                │                             │
│      (with attacks + units)        │  ECONOMIC HEALTH       4/10 │
│                                    │  ████░░░░░░  ↓ from 6       │
│      auto-rotates to theater       │                             │
│      maps when attacks occurred    │  NUCLEAR DANGER        3/10 │
│                                    │  ███░░░░░░░  ↑ from 1       │
│                                    │                             │
│                                    │  AI RACE               6/10 │
│                                    │  ██████░░░░  ↑ from 4       │
├────────────────────────────────────┤                             │
│  COLUMBIA vs CATHAY                │                             │
│  ███████████░░░░░░░░░              │                             │
│  Power balance trend (20yr)        │                             │
├────────────────────────────────────┴─────────────────────────────┤
│  ► Cathay deploys 3 naval units to Taiwan Strait · Albion signs │ ← News ticker
│    defense pact with Formosa · Columbia imposes L3 sanctions ... │
└──────────────────────────────────────────────────────────────────┘
```

---

## 3. Elements

### 3.1 Header
- Round number + Phase + Timer countdown
- Real-world time mapping: "H1 2028" (each round = 6 months from H2 2026)
- Sim name

### 3.2 Global Map (60-70% of screen)
- Full hex map with unit deployments and country colors
- Attack markers for current round (flashing/highlighted)
- Auto-rotation: Global (30s) → Theater with attacks (15s each) → back to Global
- Theaters only shown when combat events occurred in that theater during the round
- Minimal legend — map should be self-explanatory with country colors
- Same renderer as facilitator map, but display-optimized (larger hexes, no inspector)

### 3.3 Doomsday Indices (right panel, 4 gauges)
Each gauge: 1-10 scale, bar visualization, trend arrow (↑/↓/→), previous value.

| Index | What it captures | Feel |
|---|---|---|
| **Geopolitical Tension** | Wars, attacks, military deployments, alliance fractures | "How close to WW3" |
| **Economic Health** | GDP growth, sanctions burden, trade volume, cooperation | "Global prosperity direction" |
| **Nuclear Danger** | Nuclear levels, tests, proximity to launch | "Minutes to midnight" |
| **AI Race** | Highest AI level, progress toward L4 breakthrough | "How close to singularity" |

**Calculation:** LLM-judged after each Phase B. One API call with all world state data → returns 4 scores (1-10) with one-line rationale each. Abstract, not scientific — like the real Doomsday Clock. **Dynamic is key** — showing how each index changed from previous round.

### 3.4 Columbia vs Cathay Power Balance
- Horizontal bar: Columbia on left, Cathay on right, meeting point shows relative power
- Composite score: weighted GDP + military strength + tech level + alliance count
- **Historical perspective:** graph showing the last "10 years" (fictional pre-sim data) + sim rounds
- Shows the trajectory: Cathay catching up, crossing point approaching
- This is the visual embodiment of the Thucydides Trap

### 3.5 News Ticker (bottom strip)
- Horizontal scrolling strip, TV news style
- Pulls from `observatory_events` — filtered to significant types:
  - Combat events, sanctions/tariffs, public statements, elections, nuclear, agreements
- Shows character name + action + target: "Shield (Columbia) declares ground attack on zone 4,11"
- Cycles last ~20 significant events
- New events prepend with brief highlight animation

---

## 4. Data Sources (all exist in DB)

| Element | Table | Fields |
|---|---|---|
| Round/Phase/Timer | sim_runs | current_round, current_phase, phase_started_at, phase_duration_seconds |
| Map + Units | zones, deployments, countries | Full hex grid + unit positions |
| Attack markers | observatory_events | event_type IN (ground_attack, air_strike, naval_combat, ...) |
| Doomsday indices | LLM call using: countries, world_state, sanctions, tariffs, relationships, observatory_events | Composite judgment |
| Columbia vs Cathay | countries (cathay, columbia) | gdp, mil_*, nuclear_level, ai_level + relationships |
| News ticker | observatory_events | Latest 20 significant events |

---

## 5. Technical Approach

- **Route:** `/public-screen/:simId` (separate page, full-screen, no nav)
- **Supabase Realtime:** Subscribe to sim_runs + observatory_events (same as facilitator)
- **Map:** Embed existing map renderer in display-only mode (no click, no inspector)
- **LLM indices:** Called once per Phase B completion, results stored in `world_state` or `sim_config`
- **Auto-refresh:** Realtime push for events, poll for map/indices after phase changes

---

## 6. Build Phases

| Sprint | What |
|---|---|
| 8.1 | Page shell, header, timer, Realtime subscriptions |
| 8.2 | News ticker (bottom strip, cycling events) |
| 8.3 | Map display (global + conditional theater rotation) |
| 8.4 | Doomsday indices (LLM-calculated, 4 gauges with trend) |
| 8.5 | Columbia-Cathay power balance (historical + live trend) |
| 8.6 | Polish: animations, transitions, dark room optimization |

---

## 7. Build Progress

### Delivered (2026-04-16)

| Element | Status | Details |
|---|---|---|
| **Page shell + routing** | ✅ | `/screen/:id` — no auth, full-screen dark layout |
| **Header** | ✅ | Round, phase, timer countdown, sim date (H2 2026...), sim name |
| **Global map** | ✅ | Sim-run-aware via `?sim_run_id=`, clean display mode (no chrome), units from DB with coordinates |
| **Blast markers** | ✅ | 💥 with red glow + pulse animation at combat hexes. Both global and theater views. API: `/api/sim/{id}/map/combat-events` |
| **Theater rotation** | ✅ | Right sidebar rotates (15s) between World Status and active theater maps when combat events exist in that theater |
| **Doomsday gauges** | ✅ (visual) | 4 speedometer gauges with green/yellow/red/deep-red zones, needle, trend arrows. Economic Health has reversed zones (green=high). **Values are placeholder — LLM calculation not wired yet.** |
| **Columbia vs Cathay** | ✅ | Power bar (country colors #3A6B9F/#C4A030) + 20-year historical trend graph with SIM continuation. Pulsing dots at current round. |
| **News ticker** | ✅ | 2-line scrolling, opposite directions, category color dots. Filters to significant events. |
| **Supabase Realtime** | ✅ | sim_runs UPDATE + observatory_events INSERT. 30s fallback poll. |
| **View from facilitator** | ✅ | "View Public Screen" button opens in new tab |

### Remaining (TODO)

| Element | Priority | What's needed |
|---|---|---|
| **Doomsday indices — LLM calculation** | HIGH | After each Phase B, call LLM with world state summary → returns 4 scores (1-10). Store in `world_state` or `sim_config`. Currently placeholder values (5, 6, 4, 4). |
| **News filtering/sorting** | MEDIUM | Filter by category (military/economic/diplomatic/political). Sort by significance. Currently shows all significant events chronologically. |
| **Columbia-Cathay historical accuracy** | LOW | The pre-SIM trend data is estimated. Could be refined with real-world GDP/military data for the 2006-2026 period. |
| **Map auto-refresh after Phase B** | MEDIUM | Map iframe should reload units after world state changes. Currently static until page refresh. |
| **Blast marker cleanup** | LOW | Markers should clear when moving to next round. Currently persist across rounds. |
| **Theater map unit display** | MEDIUM | Theater maps show in sidebar but unit rendering needs verification — theater_row/col coords may need tuning. |
| **Responsive sizing** | LOW | Optimize for different projector resolutions (1080p, 4K, ultrawide). |
| **Sound effects** | FUTURE | Optional: alert sound when combat events or phase transitions occur. |
| **Moderator broadcast overlay** | FUTURE | Moderator sends announcement → appears as overlay on public screen. |

### Architecture Notes

- Map uses `?display=clean&sim_run_id={id}` for embed — reusable by M6 (participant interface)
- Combat events stored with `target_row`/`target_col` in observatory_events payload — no zone_id translation
- Doomsday indices designed for LLM judgment (abstract, not formulaic) — one call per Phase B
- Theater detection reads `payload.theater` from combat events in observatory_events

---

*SPEC approved in principle (2026-04-16). Core layout and mechanics delivered. LLM indices are the main remaining feature.*
