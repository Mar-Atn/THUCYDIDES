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

```
┌──────────────────────────────────────────────────────────┐
│  Round 3 · Phase A · 42:17 remaining     [Extend] [End] │
│  ═══════════════════════════════▓▓▓░░░░░░░  (65%)       │
│  [Manual ○ / Automatic ●]   [Pause] [Next] [End Sim]    │
└──────────────────────────────────────────────────────────┘

┌─────────────┬──────────────────────────┬────────────────┐
│ LEFT PANEL  │  CENTER                  │ RIGHT PANEL    │
│             │  Map (god view, all      │                │
│ Participants│  units visible)          │ Country Status │
│  7 human    │                          │  (stability,   │
│  33 AI      │                          │   key metrics) │
│  [Assign]   │                          │                │
│             │                          │ Alerts         │
│ AI Status   │                          │  ⚠ warnings    │
│  33/33 idle │                          │  ☢ nuclear     │
│  [Details]  │                          │  🗳 votes      │
│             ├──────────────────────────┤                │
│ Confirmation│  Action Feed             │ Key Events     │
│  Queue (2)  │  (live stream)           │  this round    │
│  [Review]   │                          │                │
│             │  [Test Action Panel]     │                │
│ Public Scr  │  (act as any role)       │                │
│  [Controls] │                          │                │
│             │                          │                │
│ [Broadcast] │                          │                │
└─────────────┴──────────────────────────┴────────────────┘
```

### Pre-Start view
Same layout but center shows participant assignment interface instead of map.

### Phase B view
Center shows engine processing progress (step 1/11... 2/11... done). Results summary appears when complete. Moderator can review and adjust before publishing.

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

## 13. Open Questions for Marat

**Q1: Number of AI triggers per Phase A.** You said 2-3 times. Suggest: (1) at Phase A start, (2) at midpoint, (3) 5 minutes before end for regular decisions. Does this feel right, or should it be configurable?

**Q2: What does "moderator reviews Phase B results before publishing" mean in practice?** Does the moderator see a summary screen with all changes and can adjust individual values before they become visible to participants? Or is it more of a quick sanity check?

**Q3: Participant lobby/waiting room.** After assignment in Phase 0, do participants see a "waiting for simulation to start" screen? Or do they immediately get their role brief?

**Q4: Multiple facilitators.** Can two moderators share the dashboard simultaneously, or is it single-moderator only?

---

*This SPEC will be updated based on Marat's review. Once approved, Phase 1 implementation begins.*
