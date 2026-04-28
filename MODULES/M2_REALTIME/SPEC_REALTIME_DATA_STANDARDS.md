# SPEC: Realtime Data Standards

**Version:** 2.0
**Date:** 2026-04-28
**Status:** APPROVED — Phase 1-3 done, Phase 4-5 ready for implementation
**Scope:** All frontend code that displays data from Supabase
**Enforcement:** `app/frontend/CLAUDE.md` references this spec. All PRs checked against it.

---

## 1. The Problem

Users must manually refresh pages to see updated data. Root causes:
1. Too many concurrent queries on page load (20+ REST + 10+ Realtime channels)
2. Browser HTTP/2 stream limit causes request queuing and hangs
3. WebSocket connections drop silently on Safari/mobile

**The core principle:**
> The number of HTTP requests on page load should equal the number of **pages**, not the number of **database tables**.

---

## 2. The Standard

**Every piece of data displayed to the user MUST update automatically.**

No manual refresh. No polling as primary mechanism. No "fetch once on mount." No 20+ independent queries competing for the same connection.

---

## 3. Database Requirements

### 3.1 REPLICA IDENTITY FULL on all tables

Every table in the Realtime publication MUST have REPLICA IDENTITY FULL. Without this, UPDATE events only send the primary key — the frontend can't read new values.

**Status:** DONE (2026-04-28) — all 31 tables set to FULL.

### 3.2 Realtime Publication

Every table the frontend reads MUST be in `supabase_realtime` publication.

**Status:** DONE (2026-04-28) — 31 tables including ai_agent_sessions, users, organizations.

### 3.3 RPC Functions

Each page gets a PostgreSQL function that returns ALL its data in one call. See Section 4.1.

---

## 4. Frontend Data Patterns

### 4.1 Pattern A: RPC Page Loader (PRIMARY — use for all pages)

**One HTTP request per page load.** A PostgreSQL function returns all data the page needs as a JSON object. One DB round-trip, one HTTP request, atomic consistent snapshot.

```sql
-- Example: Participant Dashboard data loader
CREATE OR REPLACE FUNCTION get_participant_data(
  p_sim_id uuid, p_role_id text, p_country text
) RETURNS json AS $$
  SELECT json_build_object(
    'country', (SELECT row_to_json(c) FROM countries c
                WHERE sim_run_id = p_sim_id AND id = p_country),
    'artefacts', (SELECT COALESCE(json_agg(a), '[]') FROM artefacts a
                  WHERE sim_run_id = p_sim_id AND role_id = p_role_id),
    'role_actions', (SELECT COALESCE(json_agg(ra.action_id), '[]') FROM role_actions ra
                     WHERE sim_run_id = p_sim_id AND role_id = p_role_id),
    'relationships', (SELECT COALESCE(json_agg(r), '[]') FROM relationships r
                      WHERE sim_run_id = p_sim_id AND from_country_code = p_country),
    'sanctions', (SELECT COALESCE(json_agg(s), '[]') FROM sanctions s
                  WHERE sim_run_id = p_sim_id
                  AND (target_country_code = p_country OR imposer_country_code = p_country)),
    'tariffs', (SELECT COALESCE(json_agg(t), '[]') FROM tariffs t
                WHERE sim_run_id = p_sim_id
                AND (target_country_code = p_country OR imposer_country_code = p_country)),
    'org_memberships', (SELECT COALESCE(json_agg(om), '[]') FROM org_memberships om
                        WHERE sim_run_id = p_sim_id AND country_code = p_country),
    'meetings', (SELECT COALESCE(json_agg(m), '[]') FROM meetings m
                 WHERE sim_run_id = p_sim_id AND status = 'active'
                 AND (participant_a_role_id = p_role_id OR participant_b_role_id = p_role_id)),
    'invitations', (SELECT COALESCE(json_agg(mi), '[]') FROM meeting_invitations mi
                    WHERE sim_run_id = p_sim_id AND status = 'pending'
                    AND invitee_role_id = p_role_id)
  );
$$ LANGUAGE sql STABLE;
```

Frontend:
```typescript
const { data } = await supabase.rpc('get_participant_data', {
  p_sim_id: simId, p_role_id: roleId, p_country: countryCode
})
// data.country, data.artefacts, data.relationships, etc. — all available
```

**Benefits:**
- 1 HTTP request instead of 9-20
- 1 DB connection instead of 9-20
- Atomic snapshot (all data from same point in time)
- No request queue contention
- Popup buttons never hang (Supabase client isn't overwhelmed)

### 4.2 Pattern B: Consolidated Realtime Channel (for live updates)

**One channel per page** with multiple table listeners. Realtime events trigger a re-call of the RPC function (Pattern A), not individual state patches.

```typescript
// ONE channel, multiple table listeners
const channel = supabase.channel(`participant-${roleId}`)
  .on('postgres_changes', { event: '*', schema: 'public', table: 'countries',
    filter: `sim_run_id=eq.${simId}` }, refetch)
  .on('postgres_changes', { event: '*', schema: 'public', table: 'artefacts',
    filter: `sim_run_id=eq.${simId}` }, refetch)
  .on('postgres_changes', { event: '*', schema: 'public', table: 'meetings',
    filter: `sim_run_id=eq.${simId}` }, refetch)
  // ... all tables that affect this page
  .subscribe()

// refetch = debounced call to the RPC function
function refetch() {
  supabase.rpc('get_participant_data', { ... }).then(setPageData)
}
```

**Benefits:**
- 1-2 channels instead of 10+
- Fewer WebSocket subscriptions = fewer disconnection issues
- Consistent data on every update (full snapshot, not partial patch)

### 4.3 Pattern C: useRealtimeTable (for standalone lists)

Still valid for simple cases where a component needs ONE table with Realtime:

```typescript
const { data, loading } = useRealtimeTable<Type>('table_name', simId, options)
```

**Use sparingly** — only when a component is independent (e.g., FacilitatorDashboard events feed, MeetingChat messages). Do NOT use 7+ of these on the same page.

### 4.4 Pattern D: useRealtimeRow (single record)

For watching a single record:

```typescript
const { data: simRun } = useRealtimeRow<SimRun>('sim_runs', simId)
```

**Use for:** sim_runs state (round, phase, status). One per page maximum.

### 4.5 Pattern E: Fallback poll (resilience only)

As SUPPLEMENT (not replacement). 15-30s minimum interval.

### 4.6 FORBIDDEN Patterns

```typescript
// WRONG — 20 independent fetches competing for connection:
useEffect(() => { fetchCountry() }, [])
useEffect(() => { fetchArtefacts() }, [])
useEffect(() => { fetchRelationships() }, [])
// ... 17 more

// WRONG — one-time fetch, never refreshed:
useEffect(() => { fetchData().then(setData) }, [])

// WRONG — 10 separate Realtime channels:
useRealtimeTable('countries', simId)
useRealtimeTable('artefacts', simId)
useRealtimeTable('meetings', simId)
// ... 7 more
```

---

## 5. Connection Resilience

### 5.1 ChannelManager Reconnect

**Status:** DONE (2026-04-28)
- Exponential backoff on CHANNEL_ERROR/TIMED_OUT (2s base, max 10s, 5 retries)
- Dead channels removed and recreated
- All hooks notified to refetch on reconnect

### 5.2 Visibility Change Handler

**Status:** DONE (2026-04-28)
- Tab becomes visible → force refetch all active data
- Handles Safari/iOS aggressive WebSocket cleanup

### 5.3 Heartbeat Monitor

**Status:** DONE (2026-04-28)
- 30s periodic check, triggers refetch when tab is visible

### 5.4 Cross-Browser Requirements

| Platform | Requirement |
|----------|-------------|
| Chrome desktop | Realtime works, visibility refetch handles tab switches |
| Safari desktop | Visibility refetch critical |
| Safari iOS | Visibility refetch + heartbeat |
| Chrome Android | Same as iOS Safari |

---

## 6. Page Data Architecture

### ParticipantDashboard

| Current (v1) | Target (v2) |
|---|---|
| `loadData()` with 9 parallel queries | `supabase.rpc('get_participant_data')` — 1 query |
| 7 `useRealtimeTable` hooks (7 channels) | 1 consolidated channel triggering RPC refetch |
| roleInfo one-time fetch | Included in RPC result |
| activeMeetings separate fetch | Included in RPC result |
| **Total: ~20 requests + 10 channels** | **Total: 1 request + 1-2 channels** |

### FacilitatorDashboard

| Current | Target |
|---|---|
| useRealtimeTable for events, pending_actions | Keep as-is (only 3-4 hooks, manageable) |
| AI status poll + Realtime | Keep as-is |
| Consider `get_facilitator_data()` RPC if needed | Future |

### Dashboard (landing page)

| Current | Target |
|---|---|
| One-time fetch + Realtime subscription | Keep as-is (already fixed, simple) |

---

## 7. Implementation Phases

### Phase 1: Database Foundation — DONE
- REPLICA IDENTITY FULL on all 31 tables
- 3 tables added to publication

### Phase 2: Connection Resilience — DONE
- ChannelManager reconnect with backoff
- Visibility change handler + heartbeat
- Hook refetch callback integration

### Phase 3: Realtime-triggered Refetch — DONE
- ParticipantDashboard: 6 tables trigger loadData()
- Dashboard: Realtime subscription for sim/role changes
- Debug log cleanup

### Phase 4: RPC Page Loaders — READY TO BUILD
- Create `get_participant_data()` PostgreSQL function
- Refactor ParticipantDashboard to use single RPC call
- Replace 9 parallel queries + 7 useRealtimeTable hooks
- 1 consolidated Realtime channel for invalidation

### Phase 5: Channel Consolidation — READY TO BUILD
- Merge per-table channels into 1-2 per page
- Realtime events trigger RPC refetch (not individual state patches)
- Remove unused useRealtimeTable instances

---

## 8. Verification Checklist

Before any feature is marked DONE:

- [ ] Page loads with 1-3 HTTP requests maximum (RPC functions)
- [ ] Page has 1-2 Realtime channels maximum
- [ ] All queried tables have REPLICA IDENTITY FULL
- [ ] No one-time fetches for changeable data
- [ ] Tested: data updates without page refresh
- [ ] Tested: tab switch + return shows current data (Safari)
- [ ] Tested: popup/modal interactions don't hang

---

*This spec is referenced by `app/frontend/CLAUDE.md` and enforced on all frontend code.*
*Community best practices: Supabase GitHub Discussions #900, #884, #3646, #7193.*
