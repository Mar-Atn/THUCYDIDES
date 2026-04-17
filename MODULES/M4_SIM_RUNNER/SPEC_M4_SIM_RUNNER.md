# M4 — Sim Runner & Facilitator Controls SPEC

**Version:** 1.0 | **Date:** 2026-04-16
**Status:** DRAFT — awaiting Marat review
**Dependencies:** M1 (engines), M2 (contracts/dispatcher), M3 (data), M9 (template/SimRun), M10.1 (auth)

---

## 1. What This Module Does

M4 is the runtime engine that makes the simulation move. It manages the lifecycle of a live simulation — from pre-start through rounds to post-sim — and provides the moderator with real-time control and visibility.

Two inseparable components:
- **Sim Runner** (backend service): state machine, action pipeline, engine triggers, AI coordination
- **Facilitator Dashboard** (frontend): the moderator's cockpit during a live simulation

---

## 2. Full SIM-Run Flow

### Phase 0: Pre-Start
- Moderator opens the SimRun from dashboard
- **Participant assignment:** dedicated screen showing registered users on one side, roles on the other. Moderator assigns users to human roles (drag-and-drop or dropdown). Random assignment option available. Solo countries default to AI.
- **Oracle intro check:** track which human participants have spoken to the AI assistant (count: N of M talked). Expandable to see details. (Oracle/Navigator built in M7 — M4 just tracks the flag.)
- **Status:** all roles assigned → moderator can press "Start Simulation"

### Phase A: Active Round (timed, e.g. 60-80 minutes)
Free gameplay. Discussions, meetings, actions submitted.

**What participants do:**
- Submit any action available to their role (validated against role_actions)
- All actions except unit movement and regular decisions are processed immediately
- Regular decisions (budget, tariffs, sanctions, OPEC) can be submitted anytime — reminder sent X minutes before end of round to relevant participants
- AI participants are triggered multiple times during Phase A to consider and submit actions
- AI participants explicitly asked to submit regular decisions a few minutes before round end

**What the moderator does:**
- Monitors action feed in real-time
- Approves/rejects actions requiring confirmation (assassination, arrest, change_leader)
- Can pause/extend timer
- Can override any decision
- Can broadcast announcements

**What the system does:**
- Validates and dispatches each action
- Processes immediate actions (combat, covert ops, intelligence, transactions, agreements)
- Queues regular decisions for Phase B
- Tracks submission status (who has/hasn't submitted budget)
- Triggers AI agents 2-3 times during phase
- Sends explicit "submit your regular decisions now" to AI agents near end of round

### Phase B: Processing (automated, 5-12 minutes)
World model engines process all round data.

**Sequence (from CONTRACT_ROUND_FLOW):**
1. Economic engine (oil → GDP → revenue → budget → production → tech → inflation → debt → crisis → momentum)
2. Political engine (stability, elections if scheduled, health events)
3. Results written to `country_states_per_round` and `global_state_per_round`
4. Observatory events generated (narrative, summaries)
5. Moderator reviews results, can adjust before publishing
6. Results published → all participants see updated world

### Inter-Round: Unit Movement (5-10 minutes)
- Only time unit movement is submitted
- Military commanders and HoS can reposition forces
- Map updates in real-time as units move
- Timer-based, moderator can extend

### Round End → Next Round
- Inter-round closes
- Round counter advances
- Key events for new round triggered (mandatory meetings, election nominations)
- Phase A of next round begins

### Post-Sim
- Moderator clicks "End Simulation"
- Quick AI reflection conversation (each human participant invited to brief chat with Navigator)
- Placeholder for analysis report generation
- Data export available (all events, context, decisions)

---

## 3. Moderator Actions Requiring Confirmation

Some participant actions require moderator approval before execution:

| Action | Why | Flow |
|---|---|---|
| **Assassination** | Sensitive — removes a participant from active play | Submitted → appears in moderator queue → moderator confirms → executed |
| **Arrest** | Temporarily removes a participant's ability to act | Same flow |
| **Change Leader** | Changes team leadership — high-impact, emotional | Same flow |
| **Combat (ground, naval)** | Optional: moderator may input real dice results | If dice mode on: submitted → moderator inputs dice → result calculated |

**Auto-approve mode:** for testing and AI-only runs, moderator can toggle "auto-approve all" which bypasses the confirmation queue.

**Timeout:** if moderator doesn't respond within 5 minutes, system can auto-approve (configurable).

---

## 4. Combat Dice

Two modes:
- **Automatic** (default): engine rolls probabilistic dice internally
- **Physical dice:** moderator enables this per combat. When combat is submitted:
  1. System calculates how many dice each side rolls (based on units + modifiers)
  2. Moderator sees: "Attacker rolls 3 dice, Defender rolls 2 dice"
  3. Participants physically roll at the table
  4. Moderator inputs each die value (1-6)
  5. Engine applies results using the input values instead of random generation
  6. All combat modifiers (AI level, terrain, morale) still apply

---

## 5. Timer & Round Control

### Manual mode (default)
- Moderator clicks to start each phase
- Timer counts down but does NOT auto-advance
- Shows OVERTIME in red if timer expires — moderator decides when to move on
- Moderator clicks "End Phase A" / "End Inter-Round" / "Next Round"

### Automatic mode
- Moderator enables at sim start or per-round
- Timer auto-advances phases when it expires
- Phase B triggers automatically after Phase A ends
- Inter-round window runs automatically
- Next round starts automatically
- Moderator can still pause, extend, or intervene at any point

### Timer mechanics (from KING pattern)
- Calculated client-side from DB: `phase_started_at + duration_seconds`
- Recalculated every second
- If facilitator refreshes, timer recalculates correctly (no drift)
- Not persisted to DB as a ticking value — only start time + duration stored

---

## 6. Facilitator Dashboard Layout

The dashboard prioritizes what the moderator DOES, not what the world looks like. The map is accessible but not the center focus — the moderator's attention goes to events, decisions, and control.

### Top Bar (always visible, fixed)
```
┌──────────────────────────────────────────────────────────────┐
│  R3 · Phase A · 42:17          [◄ Back] [Pause] [▸ Next]    │
│  ════════════════════▓▓▓░░░░░  [Extend +5m] [End Sim]       │
│  Mode: [Manual ○ / Auto ●]    LLM: ✓ ok  Tokens: 82% left  │
└──────────────────────────────────────────────────────────────┘
```
Phase control bar with full functionality: go back one phase, restart sim, pause, resume, advance, extend, end. Plus LLM/AI model health indicator.

### Main Area (scrollable, sections below)

```
┌──────────────────────────────────────────────────────────────┐
│  ⚠ PENDING ACTIONS (2)                              [Auto ○]│
│  ┌────────────────────────────────────────────────────────┐  │
│  │ ☠ Assassination: Shadow → Furnace     [Confirm][Reject]│  │
│  │ 🔄 Change Leader: Ironhand (Sarmatia) [Confirm][Reject]│  │
│  └────────────────────────────────────────────────────────┘  │
├──────────────────────────────────────────────────────────────┤
│  📋 SIM EVENTS (live feed)                    [Filter] [All]│
│  ┌────────────────────────────────────────────────────────┐  │
│  │ 42:15  Shield submitted Ground Attack → (4,11)    MIL  │  │
│  │ 41:50  Helmsman submitted Budget (social 1.2)     ECON │  │
│  │ 41:30  ★ Dawn proposed Agreement to Anchor        DIPL │  │
│  │ 40:55  Shadow submitted Intelligence request      COV  │  │
│  │ 40:12  Compass submitted Set Tariffs on Columbia  ECON │  │
│  │ ...                                                     │  │
│  │ [Test Action: act as any role ▾]                        │  │
│  └────────────────────────────────────────────────────────┘  │
├──────────────────────────────────────────────────────────────┤
│  🤖 AI PARTICIPANTS                                          │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Scales(idle) Chip(busy) Havana(idle) Pyro(busy)        │ │
│  │ Vanguard(idle) Citadel(busy) Spire(idle) Sakura(idle)  │ │
│  │ Vizier(busy) Wellspring(idle)                          │ │
│  │ [Trigger Now] [Pause All] [Details ▸]                  │ │
│  └─────────────────────────────────────────────────────────┘ │
├──────────────────────────────────────────────────────────────┤
│  👥 PARTICIPANTS                    7 human · 33 AI          │
│  [Manage Assignments] [Oracle: 5/7 talked]                   │
├──────────────────────────────────────────────────────────────┤
│  📺 PUBLIC SCREEN          [View ▸] [Customize ▸]           │
│  [📢 Broadcast Message]                                      │
├──────────────────────────────────────────────────────────────┤
│  🗺 MAP                    [Open Map ▸] [Open Deployments ▸] │
├──────────────────────────────────────────────────────────────┤
│  📊 EXPLORE SIM DATA       [Countries ▸] [Relationships ▸]  │
│                             [Sanctions ▸] [All Tables ▸]     │
└──────────────────────────────────────────────────────────────┘
```

### Special Moments Area (context-sensitive, appears when relevant)

This section appears ONLY when the current round/phase triggers special events:

```
┌──────────────────────────────────────────────────────────────┐
│  🔔 THIS ROUND: Columbia Mid-Term Elections                  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ Nominations: 3 received (Shadow, Challenger, Shield)   │  │
│  │ [Start Voting] [Extend Nominations]                    │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

Other special moment variants:
- **Pre-start:** Participant assignment interface, Oracle status
- **Nominations round:** Who has nominated, start/extend
- **Voting round:** Vote progress, trigger counting
- **Nuclear alert:** Authorization chain status, interception window
- **Phase B:** Engine processing progress bar (step 1/11... done), result review

### Linked Pages (open in new tab or modal)
- **Map** → full hex map god-view (from map renderer)
- **Deployments** → unit deployment view
- **Public Screen** → preview of what the room projection shows
- **Public Screen Customize** → control what's displayed
- **Explore SIM Data** → all tables/data browser (countries, roles, relationships, sanctions, tariffs, etc.)
- **AI Agent Details** → expanded view of each AI's status, pending actions, cognitive state

---

## 7. Real-Time Architecture

### Supabase Realtime (persistent data changes)
- Subscribe to `sim_runs` changes (phase transitions, timer updates)
- Subscribe to `observatory_events` (action feed — new actions appear live)
- Subscribe to `country_states_per_round` (world state updates after Phase B)
- Subscribe to `deployments` (unit movement during inter-round)

### Supabase Broadcast (transient signals)
- Moderator announcements → all connected clients
- "Submit your decisions" reminder → relevant participants
- Public screen display commands
- Phase transition alerts

### Pattern
Facilitator dashboard subscribes to both channels on mount. Actions submitted by participants trigger DB writes → Realtime pushes to dashboard. Moderator broadcasts don't write to DB — they're ephemeral signals.

---

## 8. AI Participant Integration

M4 doesn't build the AI agent logic (that's M5). M4 provides:

**Triggering:** Call `full_round_runner.py` (or a subset for solo countries only) at defined moments:
- Phase A start: first trigger (AI assesses situation, may initiate actions)
- Phase A mid-point: second trigger (AI reacts to what's happened so far)
- Phase A near-end: explicit "submit regular decisions" trigger
- Inter-round: AI submits unit movement orders

**Monitoring:** Dashboard shows per-agent status (idle/busy/error), action queue depth, current activity.

**Override:** Moderator can pause any AI agent, view its pending actions, override or cancel before execution.

**Context:** AI agents receive world state via the existing context assembly service (M1). M4 ensures the context is current when agents are triggered.

---

## 9. Action Pipeline

```
Participant submits action
  → API receives (POST /sim/{id}/action)
  → Validate: correct phase? role has this action? game state allows?
  → If requires confirmation: add to moderator queue, wait
  → If auto-approved: dispatch to engine
  → Engine processes → result
  → Write result to DB (observatory_events, state tables)
  → Supabase Realtime pushes update to dashboard
  → Affected participants notified
```

### Regular decisions (budget, tariffs, sanctions, OPEC)
- Submitted during Phase A, queued for Phase B processing
- Not executed immediately — collected and batch-processed
- Submission tracker shows who has/hasn't submitted
- Reminder sent near end of round to roles with missing submissions

### Immediate actions (combat, covert, transactions, etc.)
- Executed immediately when submitted (or when moderator confirms)
- Results visible instantly in action feed

---

## 10. Build Phases

### Phase 1: Foundation (Steps 0-2)
- Move map files to shared location
- Round state machine on sim_runs
- Participant assignment screen
- Facilitator control API endpoints

### Phase 2: MVP (Steps 3-5)
- Facilitator Dashboard layout (KING-inspired)
- Action submission pipeline
- Phase B engine integration
- Test action panel

**MVP milestone:** Moderator can run a 2-round sim with AI agents, see actions in feed, Phase B updates world.

### Phase 3: Real-Time (Steps 6-7)
- Supabase Realtime subscriptions
- AI agent trigger integration
- Live action feed
- Timer synchronization across clients

### Phase 4: Special Mechanics (Step 8)
- Moderator confirmation queue
- Change of Leader voting flow
- Columbia elections flow
- Nuclear chain authorization
- Physical dice input for combat
- Key event triggers (mandatory meetings, nominations)

### Phase 5: Polish (Step 9)
- Action test panel
- Auto/manual mode toggle
- 2-round dry run with full validation
- Post-sim placeholder

---

## 11. What M4 Does NOT Do

| Out of Scope | Module |
|---|---|
| Participant's own dashboard/action UI | M6 |
| AI agent cognitive model, conversations | M5 |
| Navigator/Oracle AI assistant | M7 |
| Public screen projection layout | M8 |
| Post-sim analysis report generation | Future |
| Audio recording/transcription | Future |

---

## 12. API Endpoints (New)

### Round Control
| Endpoint | Method | Who | What |
|---|---|---|---|
| `/api/sim/{id}/start` | POST | Moderator | Transition setup → active, start Phase A of R1 |
| `/api/sim/{id}/phase/end` | POST | Moderator | End current phase, trigger next |
| `/api/sim/{id}/phase/extend` | POST | Moderator | Add minutes to current phase |
| `/api/sim/{id}/phase/pause` | POST | Moderator | Pause timer |
| `/api/sim/{id}/phase/resume` | POST | Moderator | Resume timer |
| `/api/sim/{id}/end` | POST | Moderator | End simulation |
| `/api/sim/{id}/mode` | PUT | Moderator | Toggle manual/automatic |

### Actions
| Endpoint | Method | Who | What |
|---|---|---|---|
| `/api/sim/{id}/action` | POST | Any authenticated | Submit an action (validated against role_actions) |
| `/api/sim/{id}/action/{action_id}/confirm` | POST | Moderator | Approve queued action |
| `/api/sim/{id}/action/{action_id}/reject` | POST | Moderator | Reject queued action |
| `/api/sim/{id}/combat/{id}/dice` | POST | Moderator | Input physical dice results |

### Overrides
| Endpoint | Method | Who | What |
|---|---|---|---|
| `/api/sim/{id}/override/state` | PUT | Moderator | Adjust any country/world state value |
| `/api/sim/{id}/override/action` | POST | Moderator | Submit action as any role |
| `/api/sim/{id}/broadcast` | POST | Moderator | Send announcement to all |

### Participants
| Endpoint | Method | Who | What |
|---|---|---|---|
| `/api/sim/{id}/participants` | GET | Moderator | List all assigned participants |
| `/api/sim/{id}/participants/assign` | POST | Moderator | Assign user to role |
| `/api/sim/{id}/participants/unassign` | POST | Moderator | Remove user from role |

### AI
| Endpoint | Method | Who | What |
|---|---|---|---|
| `/api/sim/{id}/ai/trigger` | POST | Moderator/System | Trigger AI agent round |
| `/api/sim/{id}/ai/status` | GET | Moderator | Get all AI agent statuses |
| `/api/sim/{id}/ai/{role_id}/pause` | POST | Moderator | Pause specific AI agent |

---

## 13. Resolved Questions (Marat, 2026-04-16)

| # | Question | Decision |
|---|----------|----------|
| Q1 | AI triggers per Phase A | **3 triggers:** (1) Phase A start, (2) midpoint, (3) near-end for regular decisions. Configurable later. |
| Q2 | Phase B review | **Quick sanity check.** Moderator sees summary, can adjust values if something looks wrong. Not a full approval gate. |
| Q3 | Participant lobby | **Role brief immediately** after assignment, then "Waiting for simulation to start" screen until moderator presses Start. |
| Q4 | Multiple facilitators | **Single moderator** for now. Read-only observer mode for second facilitator can be added later. |
| Q5 | Dashboard layout | **Events-first, not map-first.** Map accessible via link, not embedded. Priority: pending actions → event feed → AI status → participants. |
| Q6 | Auto-approve mode | **Available for testing.** Toggle in Pending Actions section. Bypasses confirmation queue for all action types. |

---

*SPEC approved in principle (2026-04-16). Phase 1 implementation begins.*

---

## 14. Build Progress (Live)

### Phase 1: Foundation — DONE (2026-04-16)
- State machine (`sim_run_manager.py`): setup → pre_start → active → processing → inter_round → completed
- 12 facilitator control API endpoints in `main.py`
- Facilitator Dashboard shell with timer, phase controls, event feed
- Supabase Python SDK `.update()` chain fix (no `.select().single()`)

### Phase 2: MVP — IN PROGRESS

**Sprint 2.1: Action Endpoint + Event Schema** — DONE (2026-04-16)
- DB migration: `observatory_events` +phase, +category, +role_name, scenario_id nullable
- `write_event()` enriched with new fields
- Frontend `ObservatoryEvent` interface aligned to actual DB columns
- `SimRun` Pydantic model synced (24 fields), `Role` model +position_type
- `POST /api/sim/{id}/action` endpoint: validate → dispatch → write event
- `ACTION_CATEGORIES` map for 32 canonical action types

**Sprint 2.1+: SimRun Data Inheritance** — DONE (2026-04-16)
- `POST /api/sim/create` endpoint: server-side creation with full data copy
- `engine/services/sim_create.py`: copies 11 tables (1,471 rows) from source sim
- Wizard customizations applied: role active/inactive, human/AI flags
- Frontend `createSimRun()` and `duplicateSimRun()` call server API
- M9 SPEC updated with implementation details

**Sprint 2.2: Test Action Panel + Naming Reconciliation** — DONE (2026-04-16)
- Test Action panel on dashboard: select role → loads actual role_actions from DB → submit
- **Action naming reconciliation**: all 32 DB canonical action IDs now match dispatcher
- Stale names removed: `declare_attack`, `blockade`, `covert_op`, `reassign_powers`, etc.
- Full systematic test: 32/32 route correctly (26 routed, 6 stubs for Phase 4)
- MODULE_REGISTRY updated with canonical ACTION_NAMING table
- Known gap: 9 military engine functions have param signature mismatches (v2 refactor)

**Sprint 2.3: Phase B Engine Integration** — DONE (2026-04-16)
**Sprint 2.4: AI Agent Trigger (M5 stub)** — DONE (2026-04-16)
**Sprint 2.5: Full 2-Round Integration Test** — DONE (2026-04-16)

### Phase 3: Real-Time — DONE (2026-04-16)
- Supabase Realtime subscriptions: sim_runs UPDATE + observatory_events INSERT
- Instant push to dashboard (was 5s polling), 30s fallback poll for resilience
- DB: REPLICA IDENTITY FULL on sim_runs and observatory_events

### Phase 4: Special Mechanics — IN PROGRESS

**Sprint 4.1: Confirmation Queue** — DONE (2026-04-16)
- `pending_actions` table with RLS + Realtime
- Actions requiring approval (assassination, arrest, change_leader) queue for moderator
- Confirm/Reject endpoints dispatch or cancel the action
- Auto-approve mode respects `sim_runs.auto_approve` flag
- Dashboard Pending Actions section with realtime updates

**Sprint 4.2: Key Event Triggers** — DONE (2026-04-16)
- Orchestrator reads elections + meetings from `sim_runs.key_events` (JSONB)
- Removed hardcoded `SCHEDULED_EVENTS` from `political.py`
- Elections fire on correct rounds per DB config (Columbia R2, R6)
- Mandatory meetings logged in round processing output
- Source of truth: M9 wizard → sim_runs.key_events

**Sprint 4.3: Change of Leader** — DONE (2026-04-16)
**Sprint 4.4: Physical Dice** — DONE (2026-04-16)
**Sprint 4.5: Nuclear Chain** — DONE (2026-04-16)

### Phase 5: Polish — DONE (2026-04-16)
- Participant assignment (KING pattern, position type badges, confirm dialogs)
- Auto/manual mode toggle (military danger switch style)
- Restart with full cleanup + rollback to round N
- Two-column dashboard layout, 30vh events feed
- Map + Public Screen links

### Architecture Fixes (2026-04-16)
- **Individual unit model:** deployments 1 row = 1 unit, from canonical `units.csv` (345 units)
- **Coordinate-based positioning:** `(global_row, global_col)` replaces zone_id for deployment positioning
- **Combat wired to DB:** ground + air attacks load units by hex coordinates, apply losses (delete rows)
- **Blast markers:** map shows 💥 at combat hexes with pulsing glow
- **Information visibility:** public screen filters out covert ops and secret agreements
- **FK cascade:** all sim_run FK constraints now CASCADE on delete
