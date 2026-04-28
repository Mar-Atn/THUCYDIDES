# M4 — Sim Runner & Facilitator Controls SPEC

**Version:** 2.2 | **Date:** 2026-04-24
**Status:** STAGE GATE PASSED — aligned with World Model v3.0
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
- All actions except unit movement and batch decisions are processed immediately
- Human participants can submit batch decisions (budget, tariffs, sanctions, OPEC) anytime during Phase A — reminder sent X minutes before end of round to relevant participants
- AI participants can perform all immediate actions (combat, covert, diplomatic, political, communication) but NOT batch decisions (set_budget, set_tariffs, set_sanctions, set_opec) or move_units — these are solicited at Phase B
- AI participants are triggered multiple times during Phase A to consider and submit immediate actions

**What the moderator does:**
- Monitors action feed in real-time
- Approves/rejects actions requiring confirmation (assassination, arrest, change_leader)
- Can pause/extend timer
- Can override any decision
- Can broadcast announcements

**What the system does:**
- Validates and dispatches each action
- Processes immediate actions (combat, covert ops, intelligence, transactions, agreements)
- Queues batch decisions for Phase B
- Tracks submission status (who has/hasn't submitted budget)
- Triggers AI agents 2-3 times during phase for immediate actions
- AI batch decisions are NOT solicited during Phase A — they are solicited at Phase B

### Phase B: Processing + Solicitation + Movement (~10 minutes)
A 4-step sequential flow. Human batch decisions submitted during Phase A are already queued.

**Step 1: AI Batch Decision Solicitation**
- System asks each AI agent ONCE to submit batch decisions (budget, tariffs, sanctions, OPEC)
- Wait for all responses or 2-minute timeout
- Human decisions submitted during Phase A are already queued

**Step 2: Engine Processing**
- Economic engine runs (oil → GDP → revenue → budget → production → tech → inflation → debt → crisis → momentum)
- Political engine runs (stability, elections if scheduled, health events)
- Results written to `country_states_per_round` and `global_state_per_round`
- Observatory events generated (narrative, summaries)

**Step 3: AI Troop Movement Solicitation**
- System asks each AI agent ONCE to submit move_units
- Wait for responses or 2-minute timeout
- Human participants can also submit movements during Phase B

**Step 4: Results Published, Phase B Complete**

**Completion:** Phase B auto-completes after Step 4. Results are published automatically. Future enhancement: moderator review gate + AI-powered results commentary.

### Round End → Next Round
- Phase B closes
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

**auto_approve:** skips pending_actions confirmation queue. All actions that would normally require moderator approval execute immediately. For testing and AI-only runs.

**auto_attack:** combat executes immediately. When OFF (default), combat goes to the pending queue regardless of dice_mode. When ON, combat actions execute without moderator approval. DB column: `sim_runs.auto_attack` (BOOLEAN DEFAULT FALSE). Toggled via `POST /api/sim/{id}/mode` with `auto_attack: true/false`.

**dice_mode:** physical dice vs computed. Only affects `ground_attack` and `naval_combat` when `auto_attack` is OFF. DB column: `sim_runs.dice_mode` (BOOLEAN). Toggled via `POST /api/sim/{id}/mode` with `dice_mode: true/false`.

**change_leader:** goes through its own voting flow, NOT the pending_actions queue. Participants vote, votes are tallied. Future: add final moderator confirmation after voting completes.

**Timeout:** if moderator doesn't respond within 5 minutes, system can auto-approve (configurable).

---

## 4. Combat Dice

**Dice Mode Toggle** (Facilitator Dashboard, Pending Actions area): button next to auto-attack toggle.

Two modes:
- **Automatic** (default, label "Dice: Auto"): engine rolls probabilistic dice internally
- **Physical dice** (label "Dice: REAL", red pulsing): moderator enables this globally. Only applies to `ground_attack` and `naval_combat` when `auto_attack` is OFF. When combat is submitted:
  1. System calculates how many dice each side rolls (based on units + modifiers)
  2. Moderator sees: "Attacker rolls 3 dice, Defender rolls 2 dice"
  3. Participants physically roll at the table
  4. Moderator inputs each die value (1-6)
  5. Engine applies results using the input values instead of random generation
  6. All combat modifiers (AI level, terrain, morale) still apply

---

## 5. State Machine, Timer & Round Control

### State Machine
All valid sim states: `setup` → `pre_start` → `active` → `processing` → `paused` → `completed` | `aborted`

| State | Description |
|---|---|
| **setup** | SimRun created, not yet configured |
| **pre_start** | Participant assignment, Oracle intro check |
| **active** | Phase A — free gameplay, actions submitted |
| **processing** | Phase B — engines running, unit movement window |
| **paused** | Simulation paused. Allows `nuclear_authorize` and `nuclear_intercept` actions only. |
| **completed** | Simulation ended normally |
| **aborted** | Simulation terminated early |

Transitions: `setup` → `pre_start` → `active` ⇄ `processing` (cycles per round). From `active` or `processing`: can transition to `paused`, `completed`, or `aborted`. From `paused`: can resume to `active`.

### Manual mode (default)
- Moderator clicks to start each phase
- Timer counts down but does NOT auto-advance
- Shows OVERTIME in red if timer expires — moderator decides when to move on
- Moderator clicks "End Phase A" / "End Phase B" / "Next Round"

### Automatic mode
- Moderator enables at sim start or per-round
- Timer auto-advances phases when it expires
- Phase B triggers automatically after Phase A ends
- Next round starts automatically after Phase B completes
- Moderator can still pause, extend, or intervene at any point

### Timer mechanics (from KING pattern)
- Calculated client-side from DB: `phase_started_at + duration_seconds`
- Recalculated every second
- If facilitator refreshes, timer recalculates correctly (no drift)
- Not persisted to DB as a ticking value — only start time + duration stored

### Restart & Recovery — Three Operations

The system has three distinct lifecycle operations. They have **different goals** and must **never interfere with each other**. The fundamental invariant: after any of these operations, the three layers (Anthropic sessions, DB records, in-memory dispatcher) are in a consistent state.

#### 5.1 Restart Simulation (`POST /api/sim/{id}/restart`)

**Goal:** Return the simulation to its initial state. As if it was just created. Clean slate.

**What the moderator expects:** "I pressed restart. Everything from the previous run is gone. I see a fresh sim with 'Initialize AI Agents' button."

**The sequence (all steps mandatory, in order):**

1. **Stop the dispatcher.** Cancel all background loops (dispatch, auto-pulse, meeting monitor). No more event delivery.
2. **Terminate all AI sessions on Anthropic.** Archive every session and agent via the Anthropic API. Best-effort — if Anthropic is unreachable, proceed anyway (sessions expire on their own).
3. **Archive all session records in DB.** Set `ai_agent_sessions.status = 'archived'` for this sim. This is the critical step �� it tells the system "no active AI agents."
4. **Delete the event queue.** All events (processed and unprocessed) for this sim. Clean slate.
5. **Delete agent memories.** Avatar identities, strategic notes, everything the agents wrote. They start fresh on next init.
6. **Delete agent decisions.** Action history from the agents.
7. **Delete observatory AI logs.** Agent activity feed.
8. **Delete meetings, messages, invitations.** All conversation history.
9. **Remove the dispatcher from memory.** `_dispatchers.pop(sim_id)`. No in-memory references survive.
10. **Reset all game state tables.** Re-copy from template (countries, deployments, relationships, etc.).
11. **Reset sim_runs row.** Status → pre_start, round → 0, phase → pre.

**Preserves:** User-to-role assignments, AI/human flags, role definitions.

**Post-condition:** DB has zero active AI sessions for this sim. No dispatcher in memory. No events in queue. Moderator sees "Initialize AI Agents" button. Clicking it creates fresh Anthropic sessions from scratch.

#### 5.2 Restart Current Round (`POST /api/sim/{id}/restart-round`)

**Goal:** Redo the current round from Phase A. Prior rounds untouched. AI sessions stay alive.

**What the moderator expects:** "Round went badly. I want to replay it from the start."

**The sequence:**
1. Delete this round's runtime data (events, combat, meetings, decisions, snapshots).
2. Clear unprocessed events from the agent queue (agents get a fresh start to the round).
3. AI sessions remain active — agents continue with their existing memories and identity.
4. Reset phase to A, restart timer.

**Does NOT touch:** Prior rounds, AI sessions, agent memories, avatar identities.

#### 5.3 Server Recovery (automatic on startup)

**Goal:** Resume a running simulation after server restart (deploy, crash, reboot). The moderator did NOT ask to reset anything. The simulation is still "in progress."

**What the moderator expects:** "I didn't do anything. The server restarted on its own. My agents should come back."

**The sequence:**
1. **Find active sims only.** Query `sim_runs` for status `active` or `pre_start`. Ignore completed, aborted, setup sims.
2. **For each active sim:** find `ai_agent_sessions` with status `active` or `ready`. If none → skip (moderator hasn't initialized agents yet).
3. **For each session:** Check if the Anthropic session is still alive (health-check). If alive → reconnect (instant). If dead → recreate (same prompt, same tools, ~10s).
4. **Set all recovered agents to IDLE.** The old in-memory state (ACTING, IN_MEETING) is meaningless after restart — the session is fresh, nothing is in progress.
5. **Start the dispatch loop.** Deliver any pending events from the queue.
6. **Send recovery pulse** (if session was recreated): "Your session was recovered. Read your notes to restore context."

**Critical rules:**
- Recovery ONLY processes sims with `sim_runs.status IN ('active', 'pre_start')`.
- Recovery ONLY processes sessions with `ai_agent_sessions.status IN ('active', 'ready')`.
- If restart has archived the sessions (step 3 of 5.1), recovery skips them entirely. **This is how restart and recovery avoid conflicting.**
- Recovered agents always start as IDLE — never inherit stale ACTING/IN_MEETING state from DB.

#### 5.4 The Non-Interference Rule

These three operations can never run simultaneously for the same sim. But they interact through shared DB state. The single rule that prevents conflict:

> **The `ai_agent_sessions.status` column is the handshake.**
> - `active`/`ready` = "this session should be running" → recovery will pick it up
> - `archived` = "this session is dead" → recovery ignores it
>
> Restart sets all sessions to `archived` BEFORE deleting any data.
> Recovery only touches `active`/`ready` sessions.
> Therefore: if restart ran first, recovery has nothing to recover.

#### 5.5 Initialize AI Agents (`POST /api/sim/{id}/ai/initialize`)

**Goal:** Create fresh AI agent sessions from scratch. Only works when no agents are currently running.

**Pre-condition:** No active dispatcher for this sim, OR dispatcher has zero agents.

**The sequence:**
1. If a dispatcher exists with agents → refuse ("already initialized").
2. Archive any leftover sessions in DB (safety cleanup).
3. Archive those sessions on Anthropic (best-effort).
4. Load AI-operated roles from DB (`is_ai_operated = true`, `status = 'active'`).
5. Create Anthropic sessions (agent + environment + session) for each role.
6. Register each with the dispatcher. State = IDLE.
7. Enqueue initialization event + avatar identity request for each.
8. Start the dispatch loop.

**Post-condition:** All AI agents are IDLE with pending initialization events. Dispatch loop delivers them within seconds.

#### 5.6 Maintenance Rule

When a new table is added that stores runtime data, update `restart_simulation()` in `sim_run_manager.py` to include it. When a new per-round table is added, update both `restart_simulation()` and `restart_current_round()`. When a new AI-related table is added, update `cleanup_sim_ai_state()` in `event_dispatcher.py`.

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
Phase control bar with full functionality: go back one phase, restart round, restart sim, pause, resume, advance, extend, end. Plus LLM/AI model health indicator.

### Main Area (scrollable, sections below)

```
┌──────────────────────────────────────────────────────────────┐
│  ⚠ PENDING ACTIONS (2)        [Auto ○] [Attack ○] [Dice ○] │
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
- Phase A start: first trigger (AI assesses situation, may initiate immediate actions)
- Phase A mid-point: second trigger (AI reacts to what's happened so far)
- Phase B Step 1: `batch_decision_request` — solicits batch decisions (budget, tariffs, sanctions, OPEC). One chance, 2-minute timeout.
- Phase B Step 3: `movement_request` — solicits troop movements (move_units). One chance, 2-minute timeout.

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

## 12. API Endpoints

### Sim Lifecycle
| Endpoint | Method | What |
|---|---|---|
| `POST /api/sim/{id}/start` | POST | Transition setup → active, start Phase A of R1 |
| `POST /api/sim/{id}/pre-start` | POST | Transition to pre_start state |
| `POST /api/sim/{id}/pause` | POST | Pause simulation |
| `POST /api/sim/{id}/resume` | POST | Resume simulation |
| `POST /api/sim/{id}/end` | POST | End simulation (→ completed) |
| `POST /api/sim/{id}/abort` | POST | Abort simulation (→ aborted) |
| `POST /api/sim/{id}/restart` | POST | Restart simulation with full cleanup (26+ tables, back to pre_start) |
| `POST /api/sim/{id}/restart-round` | POST | Restart current round only (clean Phase A, keep prior rounds) |
| `POST /api/sim/{id}/rollback` | POST | Rollback to a specific round |

### Round Control
| Endpoint | Method | What |
|---|---|---|
| `POST /api/sim/{id}/phase/end` | POST | End current phase, trigger next |
| `POST /api/sim/{id}/phase/extend` | POST | Add minutes to current phase |
| `POST /api/sim/{id}/phase/back` | POST | Go back one phase |
| `POST /api/sim/{id}/mode` | POST | Toggle modes: `auto_approve`, `auto_attack`, `dice_mode` (bool fields in body) |

### Actions
| Endpoint | Method | What |
|---|---|---|
| `POST /api/sim/{id}/action` | POST | Submit an action (validated against role_actions) |
| `GET /api/sim/{id}/pending` | GET | List pending actions awaiting confirmation |
| `POST /api/sim/{id}/pending/{action_id}/confirm` | POST | Approve queued action |
| `POST /api/sim/{id}/pending/{action_id}/reject` | POST | Reject queued action |
| `GET /api/sim/{id}/pending/{action_id}/status` | GET | Check status of a pending action |

### Combat
| Endpoint | Method | What |
|---|---|---|
| `GET /api/sim/{id}/attack/valid-targets` | GET | Returns valid target hexes (`?unit_id=X`). Uses `hex_range()` BFS + `ATTACK_RANGE` per unit type. |
| `GET /api/sim/{id}/attack/preview` | GET | Preview attack outcome before committing |

### Nuclear Chain
| Endpoint | Method | What |
|---|---|---|
| `GET /api/sim/{id}/nuclear` | GET | Get nuclear status for all countries |
| `GET /api/sim/{id}/nuclear/active` | GET | Get active nuclear launches |
| `POST /api/sim/{id}/nuclear/{id}/resolve` | POST | Resolve a nuclear launch |

### Leadership
| Endpoint | Method | What |
|---|---|---|
| `GET /api/sim/{id}/leadership-votes` | GET | List leadership vote sessions |
| `POST /api/sim/{id}/leadership-votes/{id}/cast` | POST | Cast a leadership vote |
| `POST /api/sim/{id}/leadership-votes/{id}/resolve` | POST | Resolve a leadership vote |

### Data (read-only)
| Endpoint | Method | What |
|---|---|---|
| `GET /api/sim/{id}/state` | GET | Current simulation state |
| `GET /api/sim/{id}/countries` | GET | All countries in sim |
| `GET /api/sim/{id}/country/{id}` | GET | Single country detail |
| `GET /api/sim/{id}/roles` | GET | All roles in sim |
| `GET /api/sim/{id}/world` | GET | World/global state |
| `GET /api/sim/{id}/relationships` | GET | Country relationships |
| `GET /api/sim/{id}/sanctions` | GET | Active sanctions |
| `GET /api/sim/{id}/organizations` | GET | International organizations |
| `GET /api/sim/{id}/deployments` | GET | Military deployments |
| `GET /api/sim/{id}/blockades` | GET | Active blockades |
| `GET /api/sim/{id}/zones` | GET | Geographic zones |
| `GET /api/sim/{id}/map/hex-control` | GET | Occupied hexes for territory overlay |

### Moderator Tools
| Endpoint | Method | What |
|---|---|---|
| `POST /api/sim/{id}/recompute-actions` | POST | Recompute available actions for all roles |

### Planned / DEFER
| Endpoint | Method | What |
|---|---|---|
| `PUT /api/sim/{id}/override/state` | PUT | Moderator state override (not yet built) |
| `POST /api/sim/{id}/broadcast` | POST | Moderator announcement (not yet built) |

> **Note:** Meeting endpoints, AI endpoints, map renderer endpoints, and auth endpoints belong to M5/M6/M8/M10.1 SPECs respectively.

### Attack Infrastructure (engine)
- **`hex_range(row, col, distance)`** in `engine/map_config.py` — BFS range calculator returning all hexes within `distance` steps
- **`ATTACK_RANGE`** dict in `engine/map_config.py` — canonical attack range per unit type (e.g., infantry: 1, artillery: 2, fighter: 3, etc.)
- Valid targets computed server-side: units within range that belong to a different country

---

## 13. Resolved Questions (Marat, 2026-04-16)

| # | Question | Decision |
|---|----------|----------|
| Q1 | AI triggers per Phase A | **3 triggers:** (1) Phase A start, (2) midpoint, (3) near-end for regular decisions. Configurable later. |
| Q2 | Phase B review | **Auto-completes.** Results published automatically. Future enhancement: moderator review gate + AI-powered results commentary. |
| Q3 | Participant lobby | **Role brief immediately** after assignment, then "Waiting for simulation to start" screen until moderator presses Start. |
| Q4 | Multiple facilitators | **Single moderator** for now. Read-only observer mode for second facilitator can be added later. |
| Q5 | Dashboard layout | **Events-first, not map-first.** Map accessible via link, not embedded. Priority: pending actions → event feed → AI status → participants. |
| Q6 | Auto-approve mode | **Available for testing.** Toggle in Pending Actions section. Bypasses confirmation queue for all action types. |

---

*SPEC v2.2 — stage gate passed (2026-04-24). Aligned with World Model v3.0. Phase B AI solicitation design added.*

---

## 14. Build Progress (Live)

### Phase 1: Foundation — DONE (2026-04-16)
- State machine (`sim_run_manager.py`): setup → pre_start → active → processing → paused → completed → aborted
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

### Post-Phase Additions (2026-04-17)
- **Auto-Attack toggle:** `sim_runs.auto_attack` (BOOLEAN DEFAULT FALSE). When ON, combat bypasses confirmation queue. Red pulsing danger style.
- **Dice Mode toggle:** `sim_runs.dice_mode` toggle in Pending Actions area. "Dice: Auto" (OFF) vs "Dice: REAL" (ON, red pulsing). Ground + naval combat pause for physical dice input when ON.
- **Attack targeting API:** `GET /api/sim/{id}/attack/valid-targets?unit_id=X` returns valid hexes
- **`hex_range()` BFS:** range calculator in `map_config.py` + `ATTACK_RANGE` dict per unit type
- **Map attack mode:** `?mode=attack&country=X` with postMessage protocol (hex-click, highlight-hexes, clear-highlights, navigate-theater, refresh-units)
- All three toggles (auto-approve, auto-attack, dice mode) share red danger styling (`animate-pulse`, red glow shadow) via `POST /api/sim/{id}/mode`

### Post-Phase Additions (2026-04-18)
- **`hex_control` table:** persistent territory occupation — schema: `sim_run_id, global_row, global_col, theater_row, theater_col, theater, owner, controlled_by, captured_round, captured_by_action`. Upserted on ground_attack victory and ground_move advance.
- **API:** `GET /api/sim/{id}/map/hex-control` returns occupied hexes for map overlay
- **Unit capture mechanics:** ground advance into undefended hex or combat victory captures non-ground enemies as trophies (country_id changed to attacker, status=reserve, position cleared; naval excluded; type preserved)
- **Ground movement:** `ground_move` action — advance to adjacent LAND hex, sea filtered via `GLOBAL_SEA_HEXES` + `THEATER_SEA_HEXES` frozensets + `is_sea_hex()`, must leave 1 unit behind (max = min(3, count-1)), authorized by `ground_attack` permission, 100% probability, embarked units can land
- **Map config:** `GLOBAL_HEX_OWNERS` (64 land hexes) + `hex_owner()` helper for canonical territory ownership
- **Basing rights:** foreign units with basing agreement NOT treated as occupiers
- **Map display:** occupied hexes shown with diagonal stripes (owner color + occupier color)

### Architecture Fixes (2026-04-16)
- **Individual unit model:** deployments 1 row = 1 unit, from canonical `units.csv` (345 units)
- **Coordinate-based positioning:** `(global_row, global_col)` replaces zone_id for deployment positioning
- **Combat wired to DB:** ground + air attacks load units by hex coordinates, apply losses (delete rows)
- **Blast markers:** map shows 💥 at combat hexes with pulsing glow
- **Information visibility:** public screen filters out covert ops and secret agreements
- **FK cascade:** all sim_run FK constraints now CASCADE on delete
