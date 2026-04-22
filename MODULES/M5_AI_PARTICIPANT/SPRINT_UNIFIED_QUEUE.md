# M5 Sprint: Unified Event Queue — Single AI Agent End-to-End

**Version:** 1.0
**Date:** 2026-04-22
**Status:** ACTIVE SPRINT
**Goal:** One AI agent that reliably receives ALL game events and responds correctly at every stage of the simulation lifecycle.
**Test Subject:** Any single AI agent in Test33 sim_run (Marat selects)

---

## 1. What This Sprint Delivers

A unified event queue that replaces both the orchestrator pulse system AND the auto-pulse service with ONE central mechanism. After this sprint:

- AI agent receives every event that affects it (chat, meetings, transactions, attacks, nuclear, round updates)
- Events are prioritized (critical vs routine)
- No race conditions, no lost events, no stuck sessions
- Events survive backend restart (DB-persisted queue)
- Observable from the dashboard (queue depth per agent)
- Works for Human↔AI interaction in real-time
- Works for AI autonomous play during rounds
- SIM restart properly cleans up all AI state

---

## 2. Architecture: Unified Event Queue

### The Contract (what AI agent knows)

```
"You receive updates through a single channel. Some arrive immediately
(chat messages, attacks), others are batched periodically (news,
economic changes). You don't need to know the delivery mechanism.
When you receive an update, assess and act."
```

### The Queue

```
agent_event_queue (DB table)
├── id: UUID
├── sim_run_id: UUID
├── role_id: TEXT          ← WHO receives this event
├── tier: INTEGER          ← 1=critical, 2=urgent, 3=routine
├── event_type: TEXT       ← chat_message, meeting_invitation, attack, etc.
├── message: TEXT          ← formatted message for the agent
├── metadata: JSONB        ← structured data (meeting_id, action details, etc.)
├── created_at: TIMESTAMPTZ
├── processed_at: TIMESTAMPTZ  ← NULL until delivered
└── processing_error: TEXT      ← error message if delivery failed
```

### The Dispatcher (single loop)

```python
class EventDispatcher:
    """Single loop that delivers queued events to AI agents.

    Runs continuously. Checks queue every N seconds.
    ONE send_event per agent at a time. Never concurrent.
    """

    async def run(self):
        """Main loop — runs during active simulation."""
        while self.running:
            for agent in self.agents:
                if agent.state == IDLE:
                    events = dequeue(agent.role_id)
                    if events:
                        message = format_events(events)
                        await send_event(agent, message)
                        mark_processed(events)
            await asyncio.sleep(CHECK_INTERVAL)

    def enqueue(self, role_id, tier, event_type, message, metadata=None):
        """Write event to queue. Called from anywhere."""
        # Insert into agent_event_queue table
```

### Writers (anything can enqueue)

| Source | Events | Tier |
|--------|--------|------|
| Chat endpoint | Human message in meeting | 2 (urgent) |
| Action dispatcher | Meeting invitation, transaction, agreement | 2 (urgent) |
| Action dispatcher | Attack, war declaration | 1 (critical) |
| Action dispatcher | Nuclear events | 1 (critical) |
| Round transition | Round results, economic changes | 3 (routine) |
| Orchestrator schedule | Periodic "check your situation" | 3 (routine) |
| Moderator | Manual alerts, broadcasts | 2 (urgent) |

### Tier Behavior

| Tier | Check Interval | Max Latency | Batching |
|------|----------------|-------------|----------|
| 1 (Critical) | 3 seconds | 5 seconds | Never batched — deliver immediately |
| 2 (Urgent) | 5 seconds | 10 seconds | Batch if multiple arrive within interval |
| 3 (Routine) | Pulse interval (configurable) | 30-60 seconds | Always batched with other Tier 3 |

### Tool Calls (SEPARATE path — NOT queued)

Tool calls happen INSIDE the SSE stream during send_event(). NOT through the queue:

```
Queue → send_event(agent, message)
           │
           ▼
    Agent thinks... calls get_my_country
           │ tool_executor runs (sync, fast)
           │ result returned in SAME stream
           ▼
    Agent calls submit_action
           │ tool_executor runs (writes to DB)
           │ result returned in SAME stream
           ▼
    Agent goes idle → send_event returns
```

---

## 3. Lifecycle Stages (what happens when)

### Stage 1: Initialization

```
Moderator clicks "Initialize AI" (or API call)
  → Create managed agent session on Anthropic
  → Persist to ai_agent_sessions table
  → Enqueue Tier 2: "The simulation has begun. You are X. Assess your situation."
  → Dispatcher picks up → send_event → agent explores → tools fire → agent writes notes
  → Agent goes IDLE. Ready for play.
```

### Stage 2: Active Play (Phase A)

```
Dispatcher loop runs continuously:
  Every 3s: check for Tier 1 events → deliver immediately to IDLE agents
  Every 5s: check for Tier 2 events → deliver to IDLE agents
  Every Ns: check for Tier 3 events → batch and deliver to IDLE agents

Human actions trigger enqueue:
  Chat message → enqueue(vizier, tier=2, "Pathfinder says: ...")
  Transaction → enqueue(vizier, tier=2, "Transaction proposed: ...")
  Attack → enqueue(vizier, tier=1, "ATTACK on your territory!")
  Meeting invite → enqueue(vizier, tier=2, "Meeting invitation from ...")
```

### Stage 3: Meetings

```
Meeting starts:
  → Both agents set to IN_MEETING
  → ConversationRouter relays turns (direct send_event, NOT queued)
  → Events arriving during meeting → enqueue as normal
  → Dispatcher sees agent IN_MEETING → skips (events accumulate)

Meeting ends:
  → Both agents set to IDLE
  → Next dispatcher check: delivers all accumulated events
```

### Stage 4: Between Rounds (Phase B)

```
Round ends:
  → Engine processes (GDP, combat, elections, etc.)
  → Enqueue Tier 3: "Round N complete. Results: [summary]" for each agent
  → Dispatcher delivers → agents reflect, update memory

Round starts:
  → Enqueue Tier 3: "Round N+1 started. [situation update]" for each agent
```

### Stage 5: SIM Restart / Shutdown

```
Moderator restarts SIM:
  → Archive all agent sessions on Anthropic
  → Set ai_agent_sessions status='archived'
  → Delete unprocessed events from agent_event_queue
  → Clear agent_memories for this sim_run (optional — configurable)
  → Clear agent_decisions for this sim_run (optional — configurable)
  → SIM ready for fresh start with new AI initialization
```

---

## 4. Implementation Plan (Iterations)

### Iteration 1: Queue Foundation (~2 hours)

**Build:**
- Create `agent_event_queue` DB table (migration)
- Create `EventDispatcher` class with `enqueue()`, `dequeue()`, `format_events()`, `mark_processed()`
- Create dispatcher loop (`run()`) with tier-based intervals
- Wire into FastAPI startup (background task)

**Test:**
- Enqueue 3 events for Vizier (Tier 1, 2, 3)
- Verify dispatcher delivers them in priority order
- Verify events marked as processed in DB

### Iteration 2: Wire All Event Sources (~2 hours)

**Build:**
- Replace all `auto_pulse.*` calls in action_dispatcher.py with `enqueue()`
- Replace chat auto-pulse in main.py with `enqueue()`
- Add scheduled pulse enqueue (periodic Tier 3 "situation update")
- Add round transition enqueue

**Test:**
- Human sends chat → agent responds via queue (verify <10s latency)
- Human proposes transaction → agent receives and responds
- Human invites to meeting → agent accepts/declines
- Human declares attack → agent receives critical alert

### Iteration 3: Meeting Integration (~1 hour)

**Build:**
- ConversationRouter uses direct send_event (unchanged)
- Events during IN_MEETING accumulate in queue
- Events delivered when meeting ends

**Test:**
- Start meeting → send events during meeting → verify delivered after meeting ends

### Iteration 4: SIM Lifecycle (~1 hour)

**Build:**
- SIM restart: clean up AI state (sessions, queue, optionally memories/decisions)
- Add "Restart AI" button to dashboard
- Round transition: enqueue round results for all AI agents

**Test:**
- Initialize agent → play → restart SIM → verify clean state → re-initialize

### Iteration 5: Dashboard Integration (~1 hour)

**Build:**
- Show queue depth per agent in AI Participants dashboard
- Show "last event delivered" timestamp
- Agent detail page: show queue status

**Test:**
- Verify dashboard shows real-time queue depth
- Verify events appear in agent detail page activity log

### Iteration 6: Full End-to-End Test (~1 hour)

**Scenario:**
1. Initialize 1 AI agent (Vizier/Phrygia) in Test33
2. As Pathfinder: send meeting invitation → verify AI accepts
3. Chat with AI → verify responses in real-time
4. Propose transaction → verify AI evaluates
5. Declare attack → verify AI receives critical alert
6. Verify all activity visible in agent detail page
7. Restart SIM → verify clean state
8. Re-initialize → verify agent works again

**Success criteria:**
- All 7 interactions work
- No stuck sessions
- No lost events
- Latency: chat <10s, critical <5s
- Dashboard shows all activity
- SIM restart is clean

---

## 5. What Gets Removed

| Current Component | Action |
|-------------------|--------|
| `auto_pulse.py` (532 lines) | REPLACED by EventDispatcher.enqueue() |
| `orchestrator.send_pulse()` | REPLACED by dispatcher loop |
| `orchestrator.run_round()` | SIMPLIFIED — just enqueue round events |
| Inline chat auto-pulse in main.py | REPLACED by enqueue() |
| `_auto_pulse_for_action()` in action_dispatcher | REPLACED by enqueue() |

The EventDispatcher becomes the SINGLE point of delivery. Everything else just enqueues.

---

## 6. What Stays Unchanged

| Component | Why |
|-----------|-----|
| `session_manager.py` | Core send_event works. Dispatcher calls it. |
| `tool_executor.py` | Tools fire inside send_event stream. Not queued. |
| `tool_definitions.py` | Agent's 16 tools unchanged. |
| `system_prompt.py` | Layer 1 prompt unchanged. |
| `db_context.py` | World context from DB unchanged. |
| `conversations.py` | Meeting relay uses direct send_event (correct). |
| `meta_context.py` | Pulse context formatting unchanged. |
| Agent detail page | Reads from same DB tables. |
| AI dashboard | Reads from same DB tables + adds queue depth. |

---

## 7. Files to Create/Modify

| File | Action | Lines est. |
|------|--------|-----------|
| `engine/agents/managed/event_dispatcher.py` | **CREATE** — central queue + dispatch loop | ~300 |
| `engine/agents/managed/auto_pulse.py` | **DELETE** — replaced by dispatcher | -532 |
| `engine/services/action_dispatcher.py` | **MODIFY** — replace auto_pulse calls with enqueue | ~20 changed |
| `engine/main.py` | **MODIFY** — replace chat auto-pulse with enqueue, start dispatcher on startup | ~30 changed |
| `engine/agents/managed/orchestrator.py` | **SIMPLIFY** — init only, no pulse scheduling | ~200 removed |
| `supabase/migrations/00004_agent_event_queue.sql` | **CREATE** — queue table | ~20 |
| `frontend/.../AIParticipantDashboard.tsx` | **MODIFY** — add queue depth | ~10 |
| `engine/agents/managed/test_event_dispatcher.py` | **CREATE** — integration tests | ~200 |

**Net change:** ~550 new lines, ~750 removed lines. Simpler system.

---

*Sprint goal: ONE AI agent, ALL stages, ALL actions, fully tested, fully observable. Then scale to 20.*
