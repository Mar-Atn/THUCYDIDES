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

*SPEC ready for Marat review.*
