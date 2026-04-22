# M5: Async Supabase Client Migration Plan

**Date:** 2026-04-22
**Status:** PLANNING → EXECUTION
**Problem:** Sync Supabase client blocks the async event loop, causing [Errno 35] on macOS and will bottleneck at scale (20-40 agents)

---

## 1. The Problem

The EventDispatcher runs an async loop (`while self._running`) that polls the
`agent_event_queue` table every 5-10 seconds. Each poll calls the sync Supabase
client (`get_client()`) which blocks the event loop thread. When other async tasks
(action endpoints, Anthropic API calls) need the event loop simultaneously, macOS
runs out of connections → [Errno 35] Resource temporarily unavailable.

**This affects:**
- Dispatcher queue polling (dequeue, get_queue_depth)
- Dispatcher enqueue (write to queue)
- Dispatcher mark_processed (update queue)
- Dispatcher cleanup (delete from queue, archive sessions)
- get_status() (read from ai_agent_sessions)

**This does NOT affect:**
- Tool executor (runs inside Anthropic SSE stream — sync is fine, fast <100ms)
- Action dispatcher (runs in asyncio.to_thread from endpoints — has its own thread)
- Session manager (uses AsyncAnthropic — already async)

## 2. The Fix

Create an **async Supabase client** for the EventDispatcher. All queue operations
become `await`-based. The dispatch loop never blocks.

```python
from supabase import create_async_client

class EventDispatcher:
    def __init__(self, sim_run_id: str):
        self._async_db = None  # Lazy init

    async def _get_async_db(self):
        if not self._async_db:
            self._async_db = await create_async_client(url, key)
        return self._async_db

    async def enqueue(self, ...):
        db = await self._get_async_db()
        await db.table("agent_event_queue").insert({...}).execute()

    async def dequeue(self, role_id, max_tier):
        db = await self._get_async_db()
        result = await db.table("agent_event_queue").select("*")...execute()
        return result.data
```

## 3. What Changes

| Component | Current | After | Impact |
|-----------|---------|-------|--------|
| `EventDispatcher.enqueue()` | sync (get_client) | async (create_async_client) | No blocking in dispatch loop |
| `EventDispatcher.dequeue()` | sync | async | No blocking |
| `EventDispatcher.mark_processed()` | sync | async | No blocking |
| `EventDispatcher.get_queue_depth()` | sync | async | No blocking |
| `EventDispatcher.clear_queue()` | sync | async | No blocking |
| `EventDispatcher.get_status()` | sync DB reads | async | No blocking |
| `EventDispatcher.initialize_all_agents()` | sync DB reads | async | No blocking |
| `EventDispatcher.reconnect_from_db()` | sync DB reads | async | No blocking |
| `cleanup_sim_ai_state()` | sync DB operations | async | No blocking |
| `_find_hos_for_country()` | sync | stays sync (called from sync action_dispatcher) | Keep separate sync version |

**What stays sync:**
- `tool_executor.py` — runs inside SSE stream, sync is correct
- `action_dispatcher.py` — runs in thread, sync is correct
- `supabase.py get_client()` — shared by ALL sync code, don't change

## 4. New File: `async_db.py`

Create a shared async Supabase client module:

```
app/engine/services/async_db.py

"""Async Supabase client for non-blocking DB operations.

Used by EventDispatcher and other async-native code.
The sync get_client() in supabase.py is preserved for sync code
(tool_executor, action_dispatcher, engines).
"""

_async_client = None

async def get_async_client():
    global _async_client
    if _async_client is None:
        from supabase import create_async_client
        _async_client = await create_async_client(url, key)
    return _async_client
```

## 5. Testing Plan

| Test | What | Expected |
|------|------|----------|
| 1 | Async client connects | Can read/write to any table |
| 2 | Enqueue + dequeue async | Events flow through queue |
| 3 | Dispatcher loop runs without blocking | No [Errno 35] |
| 4 | Human action + dispatcher simultaneous | Both succeed |
| 5 | 5 agents parallel init + polling | No resource exhaustion |
| 6 | Full lifecycle: init → interact → cleanup | All clean |

## 6. Execution Steps

1. Create `async_db.py` with async client
2. Migrate EventDispatcher queue methods to async client
3. Migrate EventDispatcher DB reads (get_status, init, reconnect) to async
4. Migrate cleanup_sim_ai_state to async client
5. Keep sync `_find_hos_for_country()` for action_dispatcher compatibility
6. Test all 6 scenarios
7. Verify on macOS with simultaneous operations

## 7. Risk Assessment

| Risk | Mitigation |
|------|------------|
| Async client API differs from sync | Check supabase-py docs, both use PostgREST |
| Connection pooling | AsyncClient uses httpx.AsyncClient — shared pool |
| Lazy init race condition | Use asyncio.Lock for client creation |
| Sync callers (action_dispatcher) need enqueue | Keep a sync wrapper or use fire-and-forget |

---

*This is a foundation fix. Once done, the system scales to 40+ agents without
thread/connection issues on any platform.*
