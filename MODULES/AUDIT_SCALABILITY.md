# AUDIT: Scalability Analysis — 30+ Humans + 10-20 AI Agents

**Date:** 2026-04-20
**Auditor:** LEAD
**Scope:** Every system boundary from browser to database, at production load
**Target:** 30-39 human participants + 1 moderator + 1 public screen + 10-20 AI agents

---

## 1. Executive Summary — Top 5 Scaling Risks

| # | Risk | Severity | Current State | Impact |
|---|------|----------|---------------|--------|
| 1 | **ParticipantDashboard fires 11+ REST queries on load** | CRITICAL | 30 users load simultaneously = 330+ REST calls in <2s | Supabase rate limiting, slow page loads, potential 429s |
| 2 | **Supabase Realtime channel explosion** | HIGH | ParticipantDashboard uses 11 realtime hooks per tab; ChannelManager deduplicates per table+simId but each hook on different tables creates a separate channel | 30 participants x ~11 distinct table subscriptions = ~330 logical channels; PublicScreen adds 3 more; Facilitator adds 8 more |
| 3 | **LLM calls are synchronous (blocking)** | HIGH | `_call_anthropic()` and `_call_gemini()` are sync functions called from async `call_llm()` without `await asyncio.to_thread()` | Blocks the FastAPI event loop; 20 AI agents running = 20 threads via `asyncio.to_thread` in full_round_runner, but moderator/human LLM calls block the main loop |
| 4 | **Single FastAPI process, no workers configured** | HIGH | No uvicorn worker count specified; no gunicorn; single process | One blocked request stalls all others; no horizontal scaling |
| 5 | **Supabase client is sync (not thread-safe singleton)** | MEDIUM | Global `_client` used by all async handlers and all agent threads concurrently | Potential connection pool exhaustion under concurrent load |

---

## 2. Connection Budget Calculation

### Supabase Pro Plan Limits (eu-west-2)

| Resource | Pro Plan Limit | Notes |
|----------|---------------|-------|
| Database connections (direct) | 60 (can be raised) | Shared across engine + frontend + edge functions |
| Realtime concurrent connections | 500 | Per project; each browser tab = 1 WebSocket |
| REST API (PostgREST) | ~1000 req/s | Shared across all clients |
| Realtime messages | 10M/month included | Events broadcast to subscribers |
| Database size | 8 GB | Sufficient for SIM data |

### Frontend WebSocket Budget

| Client | Tabs | Channels per tab | Total channels |
|--------|------|-----------------|----------------|
| ParticipantDashboard | 30 | 11 (via useRealtimeTable/Row hooks on distinct tables) | 330 |
| FacilitatorDashboard | 1 | 8 (useRealtimeRow x1 + useRealtimeTable x7) | 8 |
| PublicScreen | 1 | 3 (manual channels: sim_runs, observatory_events, nuclear_actions) | 3 |
| **Total logical channels** | 32 | — | **341** |

**Important nuance:** The ChannelManager deduplicates channels by `table:simId` key. If all 30 ParticipantDashboards subscribe to the same table+simId, they share ONE Supabase channel and the ChannelManager fans out events client-side. This is excellent design.

However, `useRealtimeRow` (used for sim_runs) creates its OWN channel (`rt:sim_runs:row:{id}`) bypassing the ChannelManager. Each of 30 participants creates a separate `supabase.channel()` for role-status watching too (line 290 of ParticipantDashboard.tsx).

**Revised WebSocket count:**
- Shared channels via ChannelManager: ~11 distinct table subscriptions (shared) = 11 Supabase channels
- Per-participant `useRealtimeRow` for sim_runs: 30 (each creates own channel name `rt:sim_runs:row:{simId}` -- BUT simId is the same, so Supabase may multiplex)
- Per-participant role-status channel: 30 (each unique: `role-status:{roleId}`)
- Facilitator useRealtimeRow: 1
- PublicScreen manual channels: 3

**Estimated total Supabase Realtime channels: ~75-80** (well within the 500 limit)

### REST API Budget (Simultaneous Page Load)

| Page | REST calls on mount | x Tabs | Total |
|------|-------------------|--------|-------|
| ParticipantDashboard | 1 (role query) + 10 (Promise.all batch) + ~11 (useRealtimeTable initial fetches) = **22** | 30 | **660** |
| FacilitatorDashboard | ~9 (useRealtimeTable/Row initial fetches) + 1 (getSimRunRoles) = **10** | 1 | 10 |
| PublicScreen | 2 (getSimRun + events query) | 1 | 2 |
| Map iframe (per tab) | 4 (global + 2 theaters + countries) + 3 (units + hex_control + combat-events) = **7** | 32 | **224** |
| **TOTAL** | | | **~896** |

**Verdict:** ~900 REST calls within a 2-3 second window on simultaneous load. Supabase Pro can handle ~1000 req/s, so this is at the edge. A staggered login (realistic) makes this fine. A hard refresh by all participants simultaneously would spike.

### Database Connection Budget

| Consumer | Connections |
|----------|------------|
| PostgREST (serves REST API) | ~20 (connection pool) |
| Realtime server | ~10 |
| FastAPI engine (service_role client) | 1 (sync singleton, but threads may open more) |
| AI agent threads (10-20 concurrent) | Each calls `get_client()` returning the same singleton | 1 (shared) |
| Edge Functions | ~5 |
| **Total estimated** | **~37** |

**Verdict:** Within Pro plan's 60 connection limit. Safe margin exists.

---

## 3. Per-Page Load Analysis

### ParticipantDashboard (`/play/:simId`)

**On mount (loadData):**
1. `roles` query (1 REST call)
2. Then `Promise.all` with 10 parallel queries:
   - countries, artefacts, role_actions, relationships, org_memberships, role_relationships (x2 directions), sanctions, tariffs, countries (full)
3. 11 `useRealtimeTable` hooks (meeting_invitations, pending_txns, proposed_agreements, leadership_votes, election_nominations, election_votes, election_results, outgoing_txns, nuclear_actions, sim_runs row, plus role-status channel)

**On round change:** loadData re-fires all 11 queries.

**Data volume per load:** ~50-200 rows total across all queries. Small payload (~10-50 KB).

**Concern:** The 77 `supabase.from()` calls throughout the file (many triggered by user interactions like opening action panels) mean active gameplay generates continuous REST traffic. With 30 users actively submitting actions, expect 5-10 REST calls per action submission.

### FacilitatorDashboard (`/sim/:id/live`)

**On mount:**
- 1 `useRealtimeRow` (sim_runs)
- 7 `useRealtimeTable` hooks (pending_actions, observatory_events, nuclear_actions, leadership_votes, election_nominations, election_votes, election_results)
- 1 `getSimRunRoles()` call
- 1 `getAllUsers()` call (for role assignment UI)

**Concern:** The `observatory_events` subscription with `limit: 100` means the initial fetch loads 100 rows. With 20 AI agents each emitting 3-5 events per round, this table grows fast. No pagination on the events feed.

### PublicScreen (`/screen/:id`)

**On mount:**
- 1 `getSimRun()` + 1 events query
- 3 manual Supabase channels (sim_runs, observatory_events, nuclear_actions)
- 1 map iframe (7 REST calls to FastAPI)
- 30-second fallback polling interval

**Concern:** Map iframe reloads on every phase/round change (`setMapKey(k + 1)` forces iframe re-render). Each reload = 7 REST calls. With 8 rounds x 3 phases = 24 reloads per SIM = 168 additional REST calls.

---

## 4. Backend Bottleneck Analysis

### FastAPI Architecture

**Current state:**
- Single process, no worker configuration found
- No `uvicorn --workers` flag in any startup script
- No gunicorn wrapper
- Async handlers (`async def`) but sync Supabase client underneath

**Critical issue — Sync-over-async pattern:**
The `supabase.py` service module declares functions as `async def` but uses the synchronous `supabase-py` client:
```python
async def get_countries(sim_id: str) -> list[Country]:
    client = get_client()  # sync singleton
    result = client.table("countries").select("*").eq(...).execute()  # SYNC HTTP call
```
These are **fake async** functions. They block the event loop during every DB call. Under load, a single slow DB query blocks ALL concurrent request handling.

**Impact with 30 concurrent users:**
- If 10 users submit actions simultaneously, each action triggers 2-5 DB queries
- Each DB query blocks the event loop for ~5-20ms
- Total blocking time: 100-1000ms where NO other requests are processed
- Users experience intermittent timeouts/slowness

### Action Submission Path

When a participant submits an action:
1. REST call to FastAPI `/api/sim/{id}/action`
2. Auth validation (1 DB query)
3. Action validation (2-5 DB queries depending on action type)
4. Insert into `pending_actions` table (1 DB write)
5. If auto-approve: execute action immediately (3-10 DB queries + writes)

**For attack actions (worst case):** `get_valid_attack_targets` makes 3-5 DB queries including a full deployment scan. If 5 players attack simultaneously, that is 15-25 blocking DB calls in sequence on a single event loop.

### Request Queuing

No explicit request queuing exists. FastAPI handles requests via the asyncio event loop, but since DB calls are sync, effective concurrency = 1.

---

## 5. LLM Scaling Constraints

### Current LLM Architecture

| Component | Sync/Async | Provider |
|-----------|-----------|----------|
| `call_llm()` | Declared `async`, but `_call_anthropic` / `_call_gemini` are **sync** | Anthropic + Gemini |
| `call_tool_llm()` | Fully **sync** | Anthropic + Gemini |
| `call_llm_sync()` | Explicitly sync with ThreadPoolExecutor | Wrapper for sync contexts |

**Critical issue:** `_call_anthropic()` (line 198) and `_call_gemini()` (line 227) are plain synchronous functions called from `async _call_provider()`. The `await` keyword on line 122 (`return await _call_provider(...)`) actually calls a non-async function — this blocks the event loop for the full LLM roundtrip (1-10 seconds per call).

### Rate Limits

| Provider | Model | RPM | TPM |
|----------|-------|-----|-----|
| Anthropic Claude Sonnet 4 | Agent decisions | ~4000 RPM (Tier 2) | ~400K TPM |
| Gemini 2.5 Flash | Quick scans, narrative | ~1500 RPM | ~1M TPM |
| Gemini 2.5 Pro | Moderator fallback | ~360 RPM | ~2M TPM |

### Concurrent LLM Scenarios

**Scenario A: 5 intelligence reports requested simultaneously**
- 5 x `call_llm()` = 5 sync HTTP calls
- Since they block the event loop, they run SEQUENTIALLY
- Latency: 5 x 2-5s = 10-25 seconds for the last user
- Fix required: wrap in `asyncio.to_thread()`

**Scenario B: AI agent round (20 agents)**
- The full_round_runner correctly uses `asyncio.to_thread()` and a semaphore (MAX_CONCURRENCY=10)
- 20 agents x 3-8 LLM calls each = 60-160 LLM calls per round
- With semaphore of 10: ~6-16 sequential batches
- At ~3s per LLM call: 18-48 seconds per round (acceptable)
- Rate limit risk: 160 calls / 48s = ~200 RPM (within Anthropic limits)

**Scenario C: AI agents + human LLM requests concurrent**
- AI agents run in threads (correctly isolated from event loop)
- Human LLM requests block the main event loop
- During an AI round, human LLM requests queue behind sync DB calls
- Degraded UX for humans during AI processing

---

## 6. AI Agent Load Projection

### Per-Agent Resource Consumption

| Resource | Per agent per round | Notes |
|----------|-------------------|-------|
| LLM calls | 3-8 (investigate + commit + reflect) | Via `call_tool_llm` (sync, threaded) |
| DB reads | 5-15 (tools: get_my_forces, get_economy, etc.) | Via sync supabase client |
| DB writes | 2-5 (commit_action, write_memory, events) | Via sync supabase client |
| Context size | ~20-30 KB system prompt | 4-block cognitive model |
| Token consumption | ~3K in + ~1K out per call | ~4K tokens per LLM call |
| Wall time | 30-90 seconds | With retries up to 90s timeout |

### Full Round with 20 AI Agents

| Resource | 20 agents x 1 round | Calculation |
|----------|---------------------|-------------|
| LLM calls | 60-160 | 20 x 3-8 |
| DB reads | 100-300 | 20 x 5-15 |
| DB writes | 40-100 | 20 x 2-5 |
| Observatory events | 40-60 | 20 x 2-3 (started, committed/failed) |
| Token consumption | ~240K-640K input, ~80K-160K output | Per round |
| Wall time | 30-90 seconds | With semaphore=10, 2 batches |

### Cost per Round (LLM only)

| Provider | Input tokens | Output tokens | Cost |
|----------|-------------|--------------|------|
| Claude Sonnet 4 | ~400K | ~120K | ~$1.56 input + $0.60 output = **~$2.16** |
| Gemini 2.5 Flash | ~400K | ~120K | ~$0.03 input + $0.04 output = **~$0.07** |

**Per full SIM (8 rounds):** ~$17 (Claude) or ~$0.56 (Gemini).

### Concurrent Load: AI Agents + Human Players

During a human phase (Phase A), if AI agents are also deliberating:
- AI agents consume 10 concurrent DB connections via threads
- Human REST requests compete for the single event loop
- Database sees 10 agent threads + 30 human REST calls within the same window

**Risk:** The sync Supabase singleton client is NOT documented as thread-safe. Multiple threads calling `client.table().execute()` simultaneously could cause connection pool issues or race conditions.

---

## 7. Database Query Hot Spots

### Most Expensive Queries (by frequency x complexity)

| Query | Triggered by | Frequency | Rows scanned | Index needed |
|-------|-------------|-----------|-------------|--------------|
| `deployments` full scan | Map units endpoint, attack targets | Every map load (32 tabs), every attack | ~345 rows | `(sim_run_id, unit_status)` |
| `observatory_events` ordered | FacilitatorDashboard, PublicScreen | Every page load + realtime | Grows unbounded | `(sim_run_id, created_at DESC)` |
| `countries` by sim_run_id | ParticipantDashboard (x2), World tab | 60+ calls on simultaneous load | 21 rows | Already indexed |
| `roles` by sim_run_id | ParticipantDashboard, Facilitator | 30+ calls on load | ~40 rows | Already indexed |
| `combat_events` scan | Map combat markers | Every map reload | Grows with rounds | `(sim_run_id, round_num)` |

### Missing Indexes (probable)

Without seeing the actual DB schema applied, these compound indexes should exist:
- `deployments(sim_run_id, country_id, unit_status)`
- `deployments(sim_run_id, global_row, global_col)`
- `observatory_events(sim_run_id, created_at DESC)`
- `pending_actions(sim_run_id, status)`

### N+1 Query Patterns

The `get_map_combat_events` endpoint (line 257 of main.py) has an N+1 pattern:
```python
for e in evts:
    # ... inner loop per combat event ...
    dep = client.table("deployments").select(...).eq(...).limit(1).execute()
```
Each combat event triggers a separate deployment lookup. With 20 combat events, that is 20 sequential DB queries in a loop.

---

## 8. Architectural Recommendations (Ordered by Priority)

### P0 — Must fix before production

#### 8.1 Fix sync-over-async DB calls
**Problem:** All `supabase.py` functions are `async def` wrapping sync HTTP calls.
**Fix:** Either:
- (a) Use `httpx` async client with `supabase-py` async support, OR
- (b) Wrap every sync call in `asyncio.to_thread()`, OR
- (c) Use Supabase connection pooler (PgBouncer) + `asyncpg` for direct queries

**Effort:** 2-3 days. Option (b) is quickest.

#### 8.2 Fix sync LLM calls blocking event loop
**Problem:** `_call_anthropic()` and `_call_gemini()` are sync inside `async call_llm()`.
**Fix:** Wrap in `asyncio.to_thread()` inside `_call_provider()`:
```python
result = await asyncio.to_thread(_call_anthropic, model, messages, system, max_tokens, temperature)
```
**Effort:** 30 minutes.

#### 8.3 Add uvicorn workers
**Problem:** Single process handles all requests.
**Fix:** Start with `uvicorn engine.main:app --workers 4` or use gunicorn with uvicorn workers.
**Caveat:** The singleton Supabase client and LLM clients would be per-process (fine — each process gets its own). In-memory state (like `_health` tracking) would not be shared across workers.
**Effort:** 1 hour.

### P1 — Should fix before production

#### 8.4 Batch ParticipantDashboard REST calls
**Problem:** 22 REST calls per page load x 30 users = 660 calls in burst.
**Fix:** Create a single FastAPI endpoint `/api/sim/{id}/player-state/{role_id}` that returns all player data in ONE response (country, artefacts, role_actions, relationships, org_memberships, sanctions, tariffs).
**Effort:** 1 day. Reduces 660 calls to 30.

#### 8.5 Make useRealtimeRow use ChannelManager
**Problem:** `useRealtimeRow` creates its own channel bypassing ChannelManager, losing deduplication benefits.
**Fix:** Route through ChannelManager (which already handles table-level subscriptions and fan-out).
**Effort:** 2 hours.

#### 8.6 Fix N+1 in combat events endpoint
**Problem:** Per-event deployment lookup in a loop.
**Fix:** Batch-load all deployments for the sim_run_id once, then look up in a dict.
**Effort:** 30 minutes.

#### 8.7 Add connection pooling configuration
**Problem:** Default Supabase connection pool may be undersized.
**Fix:** Use Supabase connection pooler URL (port 6543) for the engine service_role client. Configure pool size in settings.
**Effort:** 1 hour.

### P2 — Nice to have for production

#### 8.8 Implement server-side event aggregation for PublicScreen
Instead of having the PublicScreen poll/subscribe to raw events and filter client-side, have the engine push pre-filtered "public news" events to a dedicated channel or view.

#### 8.9 Add request rate limiting on FastAPI
Prevent any single client from flooding the API. Use `slowapi` or custom middleware.

#### 8.10 Map data caching
Static map geometry (global grid, theater grids, countries) rarely changes during a SIM. Cache in FastAPI memory or serve from CDN. Would eliminate ~128 REST calls (4 per tab x 32 tabs) on simultaneous load.

#### 8.11 Supabase client thread safety
Validate that the `supabase-py` sync client is safe for concurrent use from multiple `asyncio.to_thread()` calls. If not, use a client pool or per-thread clients.

#### 8.12 Observatory events pagination
Add server-side pagination or cursor-based loading to the FacilitatorDashboard events feed. Currently loads 100 rows with no cap on the client-side array growth.

---

## 9. Production Deployment Checklist

### Infrastructure

- [ ] Upgrade uvicorn to multi-worker (4 workers minimum)
- [ ] Configure Supabase connection pooler (PgBouncer, port 6543)
- [ ] Set up reverse proxy (nginx/Caddy) for static assets + WebSocket upgrade
- [ ] Move Vite dev server to production build (`vite build` + static serving)
- [ ] Configure CORS for production domain (currently `*`)
- [ ] Set up SSL/TLS termination

### Code Changes

- [ ] Fix sync-over-async in `supabase.py` (P0 — 8.1)
- [ ] Fix sync LLM calls (P0 — 8.2)
- [ ] Create batched player-state endpoint (P1 — 8.4)
- [ ] Fix useRealtimeRow deduplication (P1 — 8.5)
- [ ] Fix N+1 combat events query (P1 — 8.6)
- [ ] Add compound DB indexes (P1 — 8.7)
- [ ] Cache static map data (P2 — 8.10)

### Monitoring

- [ ] Add request latency logging to FastAPI middleware
- [ ] Monitor Supabase Realtime connection count
- [ ] Monitor DB connection pool utilization
- [ ] Set up LLM token usage tracking (already partially done via `_health`)
- [ ] Alert on Supabase REST 429 responses

### Load Testing

- [ ] Simulate 30 concurrent ParticipantDashboard loads
- [ ] Simulate 20 AI agents + 10 human action submissions
- [ ] Measure end-to-end latency under load for action submission
- [ ] Test WebSocket reconnection under network instability
- [ ] Test map iframe reload storm (all 32 tabs reloading simultaneously)

### Security (pre-production)

- [ ] RLS policies implemented on all game tables (currently only `users` table has RLS)
- [ ] Validate service_role key is never exposed to frontend
- [ ] Rate limit action submissions per role per round
- [ ] Validate CORS origins for production

---

## Appendix A: Supabase Project Details

- **Project:** THUCYDIDES (`lukcymegoldprbovglmn`)
- **Plan:** Pro
- **Region:** eu-west-2
- **Database:** PostgreSQL 17.6
- **Organization:** MetaGames Lab (Pro plan)
- **Status:** ACTIVE_HEALTHY

## Appendix B: ChannelManager Effectiveness

The ChannelManager (at `app/frontend/src/lib/channelManager.ts`) is well-designed for scale:
- Singleton persisted across HMR
- Deduplicates by `rt:{table}:{simId}` key
- Reference-counted cleanup
- Fan-out to multiple listeners from a single channel

This means 30 ParticipantDashboards subscribing to `useRealtimeTable('nuclear_actions', simId)` create only ONE Supabase channel, not 30. The ChannelManager is the primary reason WebSocket scaling is manageable.

**Gap:** `useRealtimeRow` and manual `supabase.channel()` calls (role-status, PublicScreen channels) bypass this deduplication. These should be migrated to ChannelManager in P1.

## Appendix C: Data Flow Summary

```
Browser Tab (x32)
  ├── REST calls → Supabase PostgREST → PostgreSQL (via connection pool)
  ├── REST calls → FastAPI → sync supabase-py → PostgreSQL (via single client)
  ├── WebSocket  → Supabase Realtime → PostgreSQL WAL listener
  └── Map iframe → FastAPI /api/map/* and /api/sim/* endpoints

FastAPI Process (x1)
  ├── Handles human REST requests (sync-blocked event loop)
  ├── AI agent threads (asyncio.to_thread, semaphore=10)
  │   ├── LLM calls (sync HTTP to Anthropic/Gemini)
  │   └── DB calls (sync supabase-py singleton)
  └── Round orchestrator (sync DB reads → pure engine functions → sync DB writes)
```
