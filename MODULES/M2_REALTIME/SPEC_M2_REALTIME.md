# M2 — Realtime Communication Layer

**Version:** 1.0 | **Date:** 2026-04-18 | **Status:** CRITICAL REFACTOR
**Owner:** LEAD + FRONTEND

---

## Problem Statement

The application uses HTTP polling (2-30 second intervals) through FastAPI for all state updates. Each poll triggers sequential Supabase REST queries (~300ms each). With 30+ concurrent clients (participants, moderator, map iframes), the FastAPI server becomes saturated (8-20 second response times). Users must manually refresh to see updates.

**This is an architectural problem, not a bug.** Polling through FastAPI cannot scale to production load (25-39 human participants + 10+ AI agents + public screens + moderator).

---

## Architecture: Before and After

### Before (Polling)
```
React → setInterval 2-30s → FastAPI GET → Supabase REST (300ms) → response
Result: 30-60 HTTP requests/second sustained. Server saturated.
```

### After (Realtime)
```
WRITE: React → FastAPI POST → Supabase DB → engine processing → DB write
READ:  Supabase DB change → Supabase Realtime (WebSocket) → React client directly
Result: 0 polling requests. <500ms push latency.
```

**FastAPI = write-only API.** Supabase Realtime = read distribution layer.

---

## Three Realtime Primitives

| Primitive | Use Case | Latency | DB-backed |
|-----------|----------|---------|-----------|
| **Postgres Changes** | Table row changes (INSERT/UPDATE/DELETE). Filtered by RLS. | ~200ms | Yes |
| **Broadcast** | Ephemeral push — map refresh, announcements, timer sync. | ~50ms | No |
| **Presence** | Who's online, active country indicators. | ~100ms | No |

### When to Use Each

- **Postgres Changes:** State that persists — countries, deployments, transactions, events, agreements, hex_control, pending_actions
- **Broadcast:** Notifications that don't need persistence — "map needs refresh", "moderator says X", "phase changed"
- **Presence:** Online status — which participants are connected, which country is active

---

## Tables Requiring Realtime

| Table | Publication | RLS SELECT | Events | Subscribers |
|-------|------------|------------|--------|-------------|
| `sim_runs` | YES | public | UPDATE | All clients |
| `pending_actions` | YES | authenticated | INSERT, UPDATE | Moderator, submitting participant |
| `observatory_events` | YES | authenticated | INSERT | All clients (event feed) |
| `exchange_transactions` | YES | authenticated | INSERT, UPDATE | Proposer + counterpart |
| `countries` | **ADD** | **ADD: authenticated** | UPDATE | Country team, world tab |
| `deployments` | **ADD** | **ADD: authenticated** | INSERT, UPDATE, DELETE | Map views |
| `relationships` | **ADD** | **ADD: authenticated** | UPDATE | Country tab, diplomacy |
| `agreements` | **ADD** | **ADD: authenticated** | INSERT, UPDATE | Signatories |
| `hex_control` | YES | **ADD: authenticated** | INSERT, UPDATE | Map views |
| `artefacts` | **ADD** | **ADD: role-filtered** | INSERT, UPDATE | Role owner only |

---

## Channel Structure

```
sim:{sim_id}:global        — Postgres Changes on sim_runs, observatory_events
sim:{sim_id}:pending       — Postgres Changes on pending_actions (moderator)
sim:{sim_id}:country:{cc}  — Postgres Changes on countries, filtered by id
sim:{sim_id}:diplomacy     — Postgres Changes on exchange_transactions, agreements
sim:{sim_id}:map           — Broadcast: unit positions, territory changes
sim:{sim_id}:presence      — Presence: who's online
```

---

## Hook Library

### `useRealtimeTable<T>(table, simId, options)`
Generic hook: initial fetch + subscribe to changes + merge into local state.

### `useRealtimeRow<T>(table, id, options)`
Single-row variant for sim_runs.

### `useRealtimeBroadcast(channel, onMessage)`
Ephemeral pub/sub for map refresh signals and announcements.

All hooks:
- Use `useRef` for callbacks (no dependency-loop bugs)
- Auto-reconnect on channel error with full re-fetch
- Cleanup subscriptions on unmount

---

## Map Iframe Strategy

Map (`map-core.js`) is vanilla JS in an iframe — cannot use React hooks.

**Solution: PostMessage bridge from parent React component.**

Parent subscribes to `deployments` and `hex_control` via hooks, pushes to iframe:
- `units-updated` → replaces unit data, re-renders
- `hex-control-updated` → replaces occupation data, re-renders

Already have 5+ postMessage types working (`hex-click`, `highlight-hexes`, `clear-highlights`, `navigate-theater`, `refresh-units`). This extends the pattern.

---

## FastAPI Endpoint Changes

| Endpoint | Current | After |
|----------|---------|-------|
| `GET /state` | Polled by map iframe | Cached 5s, initial load only |
| `GET /map/units` | Polled by map iframe | Initial load only, live via postMessage |
| `GET /map/hex-control` | Polled by map iframe | Initial load only, live via postMessage |
| `GET /pending` | Not used | Deprecate |
| All POST endpoints | Write actions | **Unchanged** |

---

## Implementation Phases

### Phase 0: Database Preparation
- Add 5 tables to realtime publication
- Add RLS SELECT policies for authenticated users
- Set REPLICA IDENTITY FULL on key tables

### Phase 1: Hook Library
- Create `useRealtimeTable`, `useRealtimeRow`, `useRealtimeBroadcast`
- Unit tests for merge logic

### Phase 2: FacilitatorDashboard
- Replace 3 manual channels + 2 polls with hooks
- Remove all `setInterval`

### Phase 3: ParticipantDashboard
- Replace `loadData` (10 sequential queries) with targeted hooks
- Remove all `setInterval`
- PendingResultPoller uses direct subscription, not polling

### Phase 4: PublicScreen
- Replace 2 channels + poll with hooks

### Phase 5: Map Bridge
- Parent pushes unit/hex updates via postMessage
- Remove `/api/sim/{id}/state` polling from map-core.js

### Phase 6: Endpoint Audit
- Mark GET endpoints as initial-load-only
- Remove polling-related code from FastAPI

---

## Performance Targets

| Metric | Before | After |
|--------|--------|-------|
| Polling requests/client | 1 every 2-30s | 0 |
| Server load (30 clients) | ~900 req/min | ~0 read req/min |
| Update latency | 2-30 seconds | <500ms |
| Map updates | Manual refresh | Automatic push |

---

## Risks

| Risk | Mitigation |
|------|------------|
| Supabase free tier: 200 concurrent connections | 35 clients × 3-4 channels = well within. Monitor dashboard. |
| RLS policy changes | New policies are PERMISSIVE, additive. Test existing flows. |
| Client offline | Reconnection handler re-fetches full state. |
| map-core.js is vanilla JS | PostMessage bridge (proven pattern, 5+ message types). |

---

*This module is a cross-cutting concern. Implementation touches M4 (Facilitator), M6 (Participant), M8 (Public Screen), and the map renderer.*
