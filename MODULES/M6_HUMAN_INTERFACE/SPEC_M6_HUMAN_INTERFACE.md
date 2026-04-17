# M6 — Human Participant Interface SPEC

**Version:** 1.0 | **Date:** 2026-04-17
**Status:** DRAFT — Marat review before coding
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
│  · Ground Attack (i)  · Air Strike (i)  · Naval Combat (i)  │
│  · Naval Bombardment (i)  · Missile Launch (i)               │
│  · Naval Blockade (i)  · Move Units (inter-round)            │
│  · Martial Law (i)  · Nuclear Test (i)                       │
├──────────────────────────────────────────────────────────────┤
│ ECONOMIC                                                      │
│  · Set Budget (i)  · Set Tariffs (i)  · Set Sanctions (i)   │
│  · Set OPEC Production (i)                                    │
├──────────────────────────────────────────────────────────────┤
│ INTERNATIONAL AFFAIRS                                         │
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

### Type B: Map-based (ground attack, air strike, naval combat, move units)
- Full-screen map embed
- Click source hex (your units) → click target hex (adjacent enemy)
- Unit selection panel (which units to send)
- Adjacency validation (highlighted valid targets)
- Submit button overlaid on map
- Per CONTRACT_GROUND_COMBAT: source → target, unit selection, chain option

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

## 8. Responsive Design

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
| **6.7** | Military actions: ground_attack (full contract), air_strike, naval_combat — MAP INTERFACE |
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
