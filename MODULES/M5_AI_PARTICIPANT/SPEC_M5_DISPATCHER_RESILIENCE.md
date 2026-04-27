# SPEC: M5.8 — Dispatcher Resilience & Auto-Recovery

**Version:** 1.0
**Date:** 2026-04-27
**Status:** DONE — Phase A+B implemented, auto-recovery verified (10 agents across 3 sims)
**Depends on:** M5 (Managed Agents core)
**Owner:** Team

---

## 1. Problem

The EventDispatcher holds all AI agent state in memory. When the server restarts (code deploy, crash, Railway infrastructure), this state is lost:

- Agent registrations (`dispatcher.agents`)
- Agent states (`IDLE`, `ACTING`, `IN_MEETING`)
- Anthropic session references (`SessionContext`)
- Background loops (dispatch, auto-pulse, meeting monitor)

**Current recovery:** Moderator must manually click "Initialize AI Agents" — creates fresh Anthropic sessions (~10-15s per agent), losing the previous session's conversation history and context window.

**Impact:**
- **Production:** A 10-30 hour SIM cannot tolerate manual recovery. Any server restart during play disrupts all AI participants.
- **Development:** Every code change → restart → manual re-init → 30-60s wait. Unacceptable test cycle speed.

---

## 2. Solution: DB-Backed Dispatcher with Auto-Recovery

### Principle

The DB is the source of truth for all dispatcher state. In-memory state is a **cache** — fast to read, but always reconstructable from DB.

```
SERVER START
  │
  ├── Query ai_agent_sessions (status='active')
  │     └── Found active sessions? ──YES──► RECOVER
  │                                           │
  │                                           ├── Rebuild agents dict from DB
  │                                           ├── Rebuild agent_states from DB
  │                                           ├── Health-check each Anthropic session
  │                                           │     ├── Alive → reconnect (instant)
  │                                           │     └── Dead → recreate (~10-15s)
  │                                           ├── Start background loops
  │                                           └── Resume event delivery
  │
  └── No active sessions ──► WAIT for moderator to initialize
```

### What changes

| Component | Before | After |
|-----------|--------|-------|
| `agent_states` | In-memory dict only | Write-through to `ai_agent_sessions.agent_state` column |
| Server startup | "AI agents require manual initialization" | Auto-recover from DB if active sessions exist |
| Session health | No check | Verify Anthropic session alive before delivery |
| Session recreation | Manual only | Automatic on dead session detection |
| Dedup sets | In-memory Python sets | DB-derived (check meeting status/messages) |

### What stays the same

- Dispatcher loop architecture (dispatch, auto-pulse, meeting monitor)
- Event queue in DB (`agent_event_queue`)
- Tool definitions, system prompt, avatar service
- All existing APIs
- Moderator "Initialize AI Agents" button (used once at SIM start)

---

## 3. Database Changes

### 3.1 ai_agent_sessions — Add `agent_state` Column

```sql
ALTER TABLE ai_agent_sessions ADD COLUMN IF NOT EXISTS agent_state TEXT DEFAULT 'IDLE';
```

Values: `IDLE`, `ACTING`, `IN_MEETING`, `FROZEN`

Updated by `EventDispatcher.set_agent_state()` on every state transition.

### 3.2 ai_agent_sessions — Existing Columns (already stored)

| Column | Purpose | Status |
|--------|---------|--------|
| `session_id` | Anthropic managed agent session ID | Already stored |
| `agent_id` | Anthropic agent resource ID | Already stored |
| `environment_id` | Anthropic environment resource ID | Already stored |
| `role_id` | Game role (e.g., "vizier") | Already stored |
| `country_code` | Country (e.g., "phrygia") | Already stored |
| `sim_run_id` | Which SIM run | Already stored |
| `status` | Session status (active/terminated/archived) | Already stored |
| `model` | Claude model ID | Already stored |
| `agent_state` | Dispatcher state (IDLE/ACTING/IN_MEETING) | **NEW** |

---

## 4. EventDispatcher Changes

### 4.1 `set_agent_state()` — Write-Through to DB

```python
def set_agent_state(self, role_id: str, state: str) -> None:
    """Update agent state in memory AND DB."""
    old = self.agent_states.get(role_id)
    self.agent_states[role_id] = state
    self._state_since[role_id] = asyncio.get_event_loop().time()
    if old != state:
        logger.info("[dispatcher] Agent %s: %s -> %s", role_id, old, state)
        # Write-through to DB (fire-and-forget, non-blocking)
        try:
            db = get_client()
            db.table("ai_agent_sessions") \
                .update({"agent_state": state}) \
                .eq("sim_run_id", self.sim_run_id) \
                .eq("role_id", role_id) \
                .eq("status", "active") \
                .execute()
        except Exception as e:
            logger.warning("[dispatcher] Failed to persist state for %s: %s", role_id, e)
```

### 4.2 `recover_from_db()` — Auto-Recovery on Startup

```python
async def recover_from_db(self) -> int:
    """Recover dispatcher state from DB after server restart.

    Reads ai_agent_sessions for active sessions, rebuilds agents dict,
    health-checks Anthropic sessions, recreates dead ones.

    Returns number of agents recovered.
    """
    db = get_client()
    sessions = db.table("ai_agent_sessions") \
        .select("*") \
        .eq("sim_run_id", self.sim_run_id) \
        .eq("status", "active") \
        .execute().data or []

    if not sessions:
        return 0

    recovered = 0
    for row in sessions:
        role_id = row["role_id"]

        # Rebuild SessionContext from DB row
        ctx = SessionContext(
            agent_id=row["agent_id"],
            agent_version=row.get("agent_version", 1),
            environment_id=row["environment_id"],
            session_id=row["session_id"],
            role_id=role_id,
            country_code=row["country_code"],
            sim_run_id=self.sim_run_id,
            scenario_code=self.sim_run_id,
            model=row.get("model", "claude-sonnet-4-6"),
            round_num=row.get("round_num", 1),
        )

        # Health-check Anthropic session
        health = await self.session_manager.health_check(ctx)
        if health == "terminated":
            # Session dead on Anthropic side — recreate
            logger.info("[recovery] Session for %s is dead, recreating...", role_id)
            try:
                new_ctx = await self.session_manager.create_session(
                    role_id=role_id,
                    country_code=row["country_code"],
                    sim_run_id=self.sim_run_id,
                    scenario_code=self.sim_run_id,
                    round_num=row.get("round_num", 1),
                )
                ctx = new_ctx
            except Exception as e:
                logger.error("[recovery] Failed to recreate session for %s: %s", role_id, e)
                continue

        # Register recovered agent
        self.agents[role_id] = ctx
        self.agent_states[role_id] = row.get("agent_state", "IDLE")
        recovered += 1
        logger.info("[recovery] Recovered agent %s (state=%s)", role_id, self.agent_states[role_id])

    return recovered
```

### 4.3 Dedup Without In-Memory Sets

Replace `_opening_sent` and `_avatar_responding` with DB-derived checks:

**Opening message dedup:** Instead of a set, check `meeting_messages` count > 0 (already done, but the set was added because the async write hadn't completed yet). Fix: after sending opening message, immediately update `meetings.turn_count` to 1 so the next monitor check sees it.

**Avatar response dedup:** Instead of a set, check if the last message in the meeting is from the AI role. If yes, don't respond again.

---

## 5. Server Startup Changes (main.py lifespan)

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("TTT Engine starting")

    # Auto-recover dispatchers from DB
    from engine.agents.managed.event_dispatcher import _dispatchers, create_dispatcher

    # Find sim_runs with active AI sessions
    db = get_client()
    active_sims = db.rpc("get_sims_with_active_agents").execute()
    # OR: query ai_agent_sessions for distinct sim_run_ids where status='active'
    active_sim_ids = db.table("ai_agent_sessions") \
        .select("sim_run_id") \
        .eq("status", "active") \
        .execute()
    unique_sims = set(row["sim_run_id"] for row in active_sim_ids.data or [])

    for sim_id in unique_sims:
        dispatcher = create_dispatcher(sim_id)
        count = await dispatcher.recover_from_db()
        if count > 0:
            await dispatcher.start()
            logger.info("Auto-recovered %d agents for sim %s", count, sim_id[:8])

    yield

    # Shutdown
    for d in list(_dispatchers.values()):
        await d.stop()
```

---

## 6. Session Health-Check & Recreation

### 6.1 Health-Check Protocol

The `session_manager.health_check(ctx)` method already exists. It sends a no-op to the Anthropic session and checks the response:
- `"ok"` — session alive, reconnect
- `"terminated"` — session dead, needs recreation

### 6.2 Recreation

When recreating a dead session:
1. Create new Anthropic agent + environment + session (same system prompt, same tools)
2. The agent's memories (avatar_identity, strategic_plan, etc.) are in DB — they survive
3. Update `ai_agent_sessions` row with new session_id
4. Send a "recovery pulse" event: "Your session was recovered. Read your notes to restore context."

### 6.3 What's Lost on Recreation

- Anthropic's internal conversation history for the managed session
- Agent's "working memory" within the session (not saved between events anyway)
- **NOT lost:** agent_memories (DB), avatar_identity (DB), pending events (DB)

The agent is told to `read_notes` at every pulse start — so after recreation, it reads its own memories and continues. The experience is: agent "wakes up" with slight amnesia about the last few seconds, but all strategic context intact.

---

## 7. Development Velocity

### 7.1 Code Changes That DON'T Require Session Recreation

| Change Type | Impact | Recovery |
|-------------|--------|----------|
| Avatar service logic | None — stateless API calls | Server restart, auto-recover |
| Meeting monitor logic | None — reads from DB | Server restart, auto-recover |
| API endpoint logic | None — stateless handlers | Server restart, auto-recover |
| Event handler logic | None — processes from queue | Server restart, auto-recover |

### 7.2 Code Changes That DO Require Session Recreation

| Change Type | Impact | Recovery |
|-------------|--------|----------|
| Tool schemas (new fields, new tools) | Anthropic session has old schemas | Auto-recreate sessions |
| System prompt changes | Session has old prompt | Auto-recreate sessions |

### 7.3 Smart Recreation

On startup recovery, compare current tool schemas + system prompt hash with what's stored in `ai_agent_sessions`. If different → recreate. If same → reconnect.

```python
# In recover_from_db():
current_prompt_hash = hash(build_system_prompt(role_id, sim_run_id))
stored_prompt_hash = row.get("prompt_hash")

if current_prompt_hash != stored_prompt_hash:
    # Schema or prompt changed — must recreate
    ctx = await self.session_manager.create_session(...)
else:
    # Same code — try to reconnect existing session
    health = await self.session_manager.health_check(ctx)
    ...
```

Store `prompt_hash` in `ai_agent_sessions` at creation time.

---

## 8. Verification Criteria

- [ ] Server restart during active SIM → agents auto-recover in <30s
- [ ] No manual "Initialize AI Agents" needed after restart
- [ ] Code change to avatar_service.py → restart → agents continue without recreation
- [ ] Code change to tool_definitions.py → restart → agents auto-recreate with new tools
- [ ] Agent state (IN_MEETING) survives restart — meeting continues
- [ ] 30-hour SIM with 2+ server restarts → zero data loss, zero manual intervention
- [ ] Event queue processes normally after recovery
- [ ] Active meetings resume after recovery

---

## 9. Implementation Phases

### Phase A: DB Write-Through (minimal, immediate value)
1. Add `agent_state` column to `ai_agent_sessions`
2. `set_agent_state()` writes to DB
3. Dedup sets replaced with DB checks

### Phase B: Auto-Recovery (core value)
4. `recover_from_db()` method on EventDispatcher
5. `lifespan()` calls recovery on startup
6. Health-check + reconnect/recreate logic
7. Store `prompt_hash` for smart recreation

### Phase C: Hardening
8. Recovery pulse event ("You were recovered, read your notes")
9. Monitoring: log recovery events to observatory
10. Test: kill server mid-SIM, verify auto-recovery

---

*This SPEC makes the dispatcher crash-proof by treating DB as the source of truth for all agent state. In-memory state becomes a performance cache, not a reliability dependency.*
