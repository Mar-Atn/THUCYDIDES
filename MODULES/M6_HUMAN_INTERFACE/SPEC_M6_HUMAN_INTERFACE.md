# M6 — Human Participant Interface SPEC

**Version:** 1.2 | **Date:** 2026-04-18
**Status:** DRAFT — Marat review before coding. **Sprint 6.7 (military map UX + territory/capture) substantially complete.**
**Dependencies:** M4 (sim runner), M3 (data), M10.1 (auth), M8 (map embed)

---

## 1. What This Module Does

M6 is what 25-30 human participants see and interact with during the simulation. It is:
- Their window into the world
- Their tool for submitting actions
- Their source of asymmetric information (artefacts)
- Their connection to the Navigator AI assistant

**M6 is also the full action pipeline integration.** Every one of the 32 action types gets properly wired to contract spec, with validators, submission UI, and outcome display. When M6 is done, every action works correctly — not just routed, but validated and resolved per CONTRACT.

---

## 2. Lifecycle Phases

### Pre-SIM (before roles distributed)
- **World tab:** Public information about the SIM world (countries, map, organizations)
- **Navigator:** Accessible — understand rules, familiarize with the world, set personal development targets
- Other tabs visible but empty/greyed

### Pre-SIM (after roles distributed)
- **Full Information Pack** unlocked for assigned role
- **Artefacts** delivered — classified reports, cables, telegrams
- **Navigator:** Understand your role, set targets, plan initial strategy

### During SIM (rounds)
- **Actions tab** (primary) — submit actions, respond to incoming requests
- **Country tab** — own country's full state (economic, military, political)
- **World tab** — all countries' public data, map, relationships
- **Strictly Confidential tab** — artefacts, intelligence, private instructions
- **Navigator** — always available for questions

### Between Rounds (inter-round)
- Military/HoS: Move units on map
- Others: Review results, plan next round

### Post-SIM
- **Navigator:** Reflection conversation, debrief

---

## 3. Information Architecture

### Public Set (visible to ALL participants)
- Global map with all deployed units and combat markers
- Theater maps (Eastern Ereb, Mashriq) when active
- Country public data: GDP/growth, inflation, stability, market indexes
- Military: unit counts visible on map (what you can see = what's deployed)
- Tariffs, sanctions, relationship status, org memberships
- Public agreements (not secret ones)
- All public news/events (from public screen ticker)
- Election results, leadership changes

### Confidential Set (visible to own country's team only)
- Own country's full economic details (treasury, debt, production, budget)
- Own military: production capacity, costs, reserve units, embarkation
- Own artefacts and intelligence reports
- Secret agreements own country is party to
- Covert operation results (own country's ops)
- Confidential role briefs and instructions

### Implementation
- **Frontend logic (Approach B):** All data loaded, UI filters by country_id match
- Country-check: `role.country_id === targetCountry.id` → show confidential, else show public
- HoS sees full scope of own country
- All roles within same country see same confidential data
- No role-based scoping within a country (simplification per Marat decision)

---

## 4. Screen Layout

### Header (always visible)
```
[Character Name] [Title] [Country flag/color]     R3 · Phase A · 42:17
```

### Tab Navigation
```
[Actions]   [Strictly Confidential]   [Country]   [World]   [Global Map]
```
Right side (persistent):
```
[Navigator]   [Rules]
```

### Pre-roles state
- Only World and Global Map tabs active
- Others visible but greyed/empty
- Navigator and Rules accessible

### Tab: Actions (PRIMARY during SIM play)

```
┌──────────────────────────────────────────────────────────────┐
│ ⚠ ACTIONS EXPECTED NOW                                       │
│  · Submit Budget (deadline: 12 min)                          │
│  · You're being attacked at (4,11)! — respond               │
│  · Vote on leadership change in Sarmatia                     │
├──────────────────────────────────────────────────────────────┤
│ GENERAL                                                       │
│  · Public Statement (i)   · Meet Anyone (i)                  │
│  · Call Organization Meeting (i)                              │
├──────────────────────────────────────────────────────────────┤
│ MILITARY                                                      │
│  · ★ ATTACK (i) — unified map-based combat                  │
│  · Naval Blockade (i)  · Move Units (inter-round)            │
│  · Martial Law (i)  · Nuclear Test (i)                       │
├──────────────────────────────────────────────────────────────┤
│ ECONOMIC                                                      │
│  · Set Budget (i)  · Set Tariffs (i)  · Set Sanctions (i)   │
│  · Set OPEC Production (i)                                    │
├──────────────────────────────────────────────────────────────┤
│ INTERNATIONAL AFFAIRS                                         │
│  · Declare War (i)                                            │
│  · Propose Transaction (i)  · Propose Agreement (i)          │
├──────────────────────────────────────────────────────────────┤
│ SECRET OPS                                                    │
│  · Intelligence (i)  · Covert Operation (i)                  │
│  · Assassination Attempt (i)                                  │
├──────────────────────────────────────────────────────────────┤
│ POLITICAL                                                     │
│  · Reassign Powers (i)  · Arrest (i)                         │
│  · Self-Nominate (i)  · Cast Vote (i)                        │
└──────────────────────────────────────────────────────────────┘
```

- **(i)** = info icon → brief description popup + "Ask Navigator" link
- Each action shows only if role has it in `role_actions`
- Click action → **full-screen action interface** replaces the list
- Action interfaces: map for attacks, form for budget, text for statements

### Tab: Strictly Confidential
- Artefacts (classified reports, cables, telegrams) rendered with H3 templates
- Private role brief (confidential_brief from roles table)
- Intelligence reports (received during SIM from covert ops)
- New/unread badge indicator

### Tab: Country
- Own country full state: GDP, growth, inflation, treasury, debt, stability
- Military: all units by type, production capacity, costs
- Budget allocation
- Active sanctions/tariffs imposed and received
- Relationships with all countries
- Organization memberships

### Tab: World
- All countries public data in table/card format
- Sortable by GDP, stability, military strength
- Relationship matrix (color-coded)
- Active wars, blockades
- Market indexes (wall street, europa, dragon)
- Oil price trend

### Tab: Global Map
- Clean map embed (`?display=clean&sim_run_id=`)
- Blast markers for current round combat
- Click hex → unit info (own units detailed, enemy units counts only)

### Moderator Broadcast Strip
- Persistent strip (below header or above footer) — shows latest moderator message
- Appears when broadcast received, stays visible until next broadcast or dismissed
- Distinct styling — stands out from game data (e.g., amber background)

### Navigator (UI placeholder — logic in M7)
- Floating button (bottom-right) → opens chat panel overlay
- M6 delivers: the UI shell (input field, message display, open/close)
- M7 delivers: the LLM intelligence behind it (rules, role context, strategy advice)
- Architecture: Navigator reads same structured data as participant interface

---

## 5. Action Interfaces — TWO TYPES

### Type A: Form-based (budget, tariffs, sanctions, statements, agreements)
- Full-screen form replacing the action list
- Input fields, dropdowns, text areas
- Validation feedback inline
- Submit button + cancel (back to list)
- Confirmation dialog for irreversible actions

### Type B: Map-based — Unified Attack System (BUILT 2026-04-17, extended 2026-04-18)

**Single "Attack" button** replaces 5 individual military action buttons (ground_attack, air_strike, naval_combat, naval_bombardment, launch_missile_conventional). Combat type is determined automatically from the unit types involved.

**Flow:**
1. Click "Attack" → map enters attack mode
2. Click source hex (your units) → unit selection panel appears
3. Select unit(s) — including embarked units (air from carrier = air strike, ground from carrier = landing)
4. Valid target hexes highlighted (red glow) based on `ATTACK_RANGE` per unit type + `hex_range()` BFS adjacency
5. Click target hex → combat preview: modifiers + win probability shown
6. Confirm → action submitted → pending moderator approval (or auto-resolved if auto-attack enabled)
7. "ATTACK SUBMITTED — awaiting moderator approval" state shown

**Map integration:**
- Works on global map AND theater maps (Eastern Ereb, Mashriq)
- Theater switcher buttons: Global Map / Eastern Ereb / Mashriq
- Theater-level adjacency computed in theater coordinates (10x10), not global
- `postMessage` protocol between React app and map iframe:
  - `hex-click` — hex selected by user
  - `highlight-hexes` — show valid targets (red glow) or source (blue glow)
  - `clear-highlights` — reset map highlights
  - `navigate-theater` — switch theater view
  - `refresh-units` — reload unit positions after combat

**Combat types (all wired engine → dispatcher → DB losses):**
- Ground Attack: RISK dice, 1-3 units (max = min(3, count-1) — must leave 1 behind), iterative exchanges
- Air Strike: 12%/6% hit probability, 15% downed by AD
- Naval Combat: 1v1 dice, ties → defender wins
- Naval Bombardment: 10% per naval unit
- Missile Launch: 80% accuracy, AD halving, missile consumed

**Territory & Capture (2026-04-18):**
- **hex_control table:** persistent territory occupation (sim_run_id, global_row/col, theater coords, owner, controlled_by, captured_round, captured_by_action). Upserted on ground_attack victory and ground_move advance.
- **Unit capture:** ground advance into undefended hex captures non-ground enemies as trophies (country_id changed to attacker, status=reserve, position cleared). Naval units excluded from capture. Type preserved (captured AD stays AD).
- **Basing rights:** foreign units with basing agreement are NOT treated as occupiers.
- **Occupation display:** map shows diagonal stripes (owner color + occupier color) for occupied hexes.
- **API:** `GET /api/sim/{id}/map/hex-control` returns occupied hexes.

**Ground movement rules (2026-04-18):**
- Can advance to any adjacent LAND hex (sea hexes filtered via `GLOBAL_SEA_HEXES` + `THEATER_SEA_HEXES` frozensets + `is_sea_hex()` helper)
- Must leave 1 unit behind when attacking/moving (max = min(3, count-1))
- `ground_move` authorized by `ground_attack` permission
- Embarked units can land (disembark from carrier)
- `GLOBAL_HEX_OWNERS`: canonical territory ownership (64 land hexes) + `hex_owner()` helper

**Moderator controls for combat:**
- Auto-Attack toggle (red pulsing when active) — combat skips moderator confirmation
- Dice Mode toggle (red pulsing when active) — ground/naval pause for physical dice entry
- Combat pending cards with expandable dice input (ground: 3 atk + 2 def dice, naval: 1+1 dice)
- Only ground_attack and naval_combat use dice; air/bombardment/missile are probability-based

**Attack UX improvements (2026-04-18):**
- Side-by-side layout: 25% sidebar, 75% map (stable)
- Unit icons (SVG pictograms) replace text IDs everywhere
- Combat assessment: 5 navy-blue squares, no percentages
- Victory/Defeat labels based on `attacker_won` (not engine success)
- Pending shows "ATTACK SUBMITTED"
- Tab clicks reset to initial page
- Click own hex at any step to re-select
- Theater switcher compact in header
- Captured trophies shown as icons + "-> reserve"

**APIs:**
- `GET /api/sim/{id}/attack/valid-targets?hex_row=&hex_col=&theater=` — BFS adjacency targets
- `GET /api/sim/{id}/attack/preview` — modifiers + win probability before confirming
- `GET /api/sim/{id}/state` — public (no auth), used by map iframe
- `GET /api/sim/{id}/map/hex-control` — occupied hexes for territory overlay

---

## 6. Incoming Action Requests

System-generated notifications that appear in "Actions Expected Now":

| Trigger | Message | Action |
|---|---|---|
| Budget deadline | "Submit budget (X min remaining)" | Opens budget form |
| Under attack | "Your forces at (R,C) are under attack!" | Shows combat result |
| Nuclear authorization | "NUCLEAR LAUNCH requires your authorization!" | Confirm/reject |
| Missile intercept | "Incoming strategic missiles — intercept?" | Confirm |
| Transaction proposal | "Proposal from [Country]: [summary]" | Accept/reject/counter |
| Agreement proposal | "Agreement proposed: [title]" | Review/sign |
| Meeting invitation | "Meeting: [title] called by [role]" | Accept |
| Election nomination | "Nominations open for [election]" | Self-nominate |
| Vote required | "Cast your vote: [election/leadership]" | Vote |
| Moderator broadcast | "[Message from moderator]" | Read |

---

## 7. Artefacts System

### Types (from SEED_H3)
1. **Classified Intelligence Report** — dark header, classification badge, structured sections
2. **Diplomatic Cable / Telegram** — urgent styling, flash priority markers
3. **Personal Email** — informal, from a specific sender
4. (Future: Press Report — public, newspaper style)

### Delivery
- **v1:** Pre-loaded artefacts only (Round 0, from template)
- **Future:** Intelligence operation results delivered as new artefacts (same DB table, same Confidential tab). LLM-generated artefacts from world state changes.
- Architecture: `artefacts` table supports `round_delivered` — new artefacts can appear mid-SIM

### Current Content (3 in template)
1. **Helmsman (Cathay):** Formosa blockade/invasion readiness — blockade feasible now, invasion needs years
2. **Dealer (Columbia):** NIE on Cathay intentions — blockade in 2-4 rounds, personal clock warning
3. **Sabre (Levantia):** FLASH on Persia nuclear — 2 rounds to capability, strike now or lose window

---

## 8. Historical Data & Round Navigation

Participants must be able to access data from ANY completed round — not just the current one.

### Pattern
- **Default view:** Always shows CURRENT round data
- **Round selector:** Small dropdown or stepper in the data area: `◄ R1  R2  [R3] ►`
- **When viewing past round:** Data area shows that round's snapshot. Clear visual indicator "Viewing Round 2" so participant doesn't confuse with current state.
- **What has history:** Country economic data, stability, military counts, world state (oil price, indexes), relationships, combat results, observatory events
- **What doesn't:** Actions tab (always current), Artefacts (cumulative, not per-round)

### Data Sources
- `country_states_per_round` — economic/political snapshots per round
- `world_state` — oil price, indexes per round
- `observatory_events` — filterable by round_num
- `deployments` — current only (no per-round snapshots yet; future: `unit_states_per_round`)

### Trend Indicators
Where numeric data is shown, include micro-trends:
- GDP: `173.5 ↑ (+2.3%)` with green/red arrow
- Stability: `6.2 ↓ (-0.8)`
- Oil price: `$125 ↑`
- Small sparkline charts where space allows (last 3-4 rounds)

---

## 9. UX Principles

**Every screen must be:**
- **Readable at a glance** — most important info largest, hierarchy clear
- **Actionable in 1-2 taps** — no buried menus, no hunting for buttons
- **Informative without overwhelming** — show what matters, hide details behind (i) icons
- **Consistent** — same patterns across all tabs, all action forms, all data displays

**Specific rules:**
- Maximum 2 clicks to submit any action (open form → submit)
- Maximum 1 click to see any country's public data
- No horizontal scrolling on desktop
- Numbers: always with context (GDP: 173.5B, not just 173.5)
- Colors: country colors consistent everywhere (map, tables, charts)
- Loading states: skeleton screens, never blank white pages
- Errors: inline, specific, with suggested fix ("No units at this hex — select a hex where you have forces")

---

## 10. Responsive Design

### Desktop (primary)
- Full layout: tabs + content area + Navigator sidebar
- Map interactions with click precision
- Multi-column data tables

### Mobile (secondary, functional)
- Single column layout
- Tabs as horizontal scroll strip
- Navigator as floating button → full-screen overlay
- Map: view-only with pinch/zoom, actions via simplified dropdowns (not map clicks)
- Action forms: full-width, large touch targets

---

## 9. Action Pipeline Integration (the real work of M6)

Every action wired to contract spec. See `MODULES/ACTION_CONTRACT_AUDIT.md` for gap analysis.

### Sprint Plan

| Sprint | What |
|---|---|
| **6.1** | Participant routing, role dashboard shell, tab navigation, header |
| **6.2** | Artefacts: rendering with H3 templates, "Strictly Confidential" tab |
| **6.3** | World view: public country data, relationships, map embed |
| **6.4** | Country view: own country confidential data |
| **6.5** | Actions catalog: all available actions listed with (i) descriptions |
| **6.6** | Simple actions: public_statement, set_budget, set_tariffs, set_sanctions, set_opec |
| **6.7** | ~~Military actions~~ **DONE 2026-04-18**: Unified Attack system (map UX, 5 combat types, theater adjacency, postMessage protocol, moderator auto-attack/dice mode, combat preview). Declare War action. Territory occupation (`hex_control` table, diagonal stripes on map). Unit capture mechanics (non-ground trophies on advance/victory). Ground movement (land-only adjacency, leave-1-behind). SVG unit icons, combat assessment squares, attack UX polish. |
| **6.8** | Diplomatic + Economic: agreements lifecycle, transactions lifecycle |
| **6.9** | Political + Covert: arrest, assassination, change_leader, covert_ops, elections |
| **6.10** | Incoming requests: "Actions Expected Now" system, notifications |
| **6.11** | Navigator UI shell (chat panel, floating button) — M7 fills the logic |
| **6.12** | Systematic testing: ALL 32 actions validated against contracts |
| **6.13** | Polish: mobile layout, loading states, error handling |

---

## 10. KING Patterns to Reuse

| Pattern | KING Source | TTT Adaptation |
|---|---|---|
| Tab navigation | ParticipantDashboard.tsx | Same pattern, different tabs |
| Card-based sections | White cards with colored borders | Adapt to TTT dark theme |
| Role header with color | Clan color border | Country color border |
| Sticky sidebar (Navigator) | Oracle card + objectives | Navigator chat + role info |
| Decision forms | KingDecisionForm.tsx | Adapt for 32 action types |
| Voting modal | Ballot.tsx + VotingControls | Reuse for elections + leadership votes |
| Real-time updates | Supabase subscriptions | Same pattern |
| Status badges | Complete/In Progress/Not Started | Reuse |

---

## 11. What M6 Does NOT Do

| Out of Scope | Module |
|---|---|
| AI agent decisions | M5 |
| Navigator AI logic (LLM calls) | M7 |
| Public screen | M8 |
| Moderator controls | M4 |
| Template editing | M9 |

---

*SPEC ready for Marat review. The sprint plan is aggressive but systematic — each sprint builds on the previous and adds tested functionality.*
