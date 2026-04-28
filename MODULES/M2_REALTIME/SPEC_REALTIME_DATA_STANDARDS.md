# SPEC: Realtime Data Standards

**Version:** 1.0
**Date:** 2026-04-28
**Status:** APPROVED — ready for implementation
**Scope:** All frontend code that displays data from Supabase
**Enforcement:** `app/frontend/CLAUDE.md` references this spec. All PRs checked against it.

---

## 1. The Problem

Users must manually refresh pages to see updated data. This happens because:
1. Many tables lack proper Realtime configuration (REPLICA IDENTITY, publication)
2. WebSocket connections drop silently and never recover
3. Most data is fetched once on mount and never refreshed

This is the #1 UX issue. It affects all platforms: Chrome, Safari, mobile, tablet.

---

## 2. The Standard

**Every piece of data displayed to the user MUST update automatically.**

No manual refresh. No polling as primary mechanism. No "fetch once on mount."

---

## 3. Database Requirements

### 3.1 Every table the frontend reads MUST be in the Realtime publication

```sql
ALTER PUBLICATION supabase_realtime ADD TABLE {table_name};
```

When adding a new table that the frontend will query: add it to the publication in the same migration.

### 3.2 Every table that receives UPDATEs MUST have REPLICA IDENTITY FULL

```sql
ALTER TABLE {table_name} REPLICA IDENTITY FULL;
```

Without this, UPDATE events only contain the primary key — the frontend can't read the new values.

**Why:** Supabase Realtime sends change payloads based on replica identity. `DEFAULT` = only PK + changed columns. `FULL` = all columns. The frontend needs all columns to update state without a re-fetch.

### 3.3 Table Registry

Every table used by the frontend must be listed here with its configuration:

| Table | In Publication | Replica Identity | Frontend Reads | Frontend Writes |
|-------|:-:|:-:|:-:|:-:|
| `sim_runs` | YES | FULL | All pages | Moderator |
| `countries` | YES | FULL | Participant, Facilitator | Engine |
| `roles` | YES | MUST BE FULL | Participant, Facilitator | Moderator |
| `meetings` | YES | FULL | Participant, Facilitator | Engine |
| `meeting_messages` | YES | MUST BE FULL | MeetingChat | Participant, Avatar |
| `meeting_invitations` | YES | MUST BE FULL | Participant | Participant, AI |
| `observatory_events` | YES | FULL | Facilitator | Engine |
| `pending_actions` | YES | FULL | Facilitator | Engine |
| `agreements` | YES | MUST BE FULL | Participant | Engine |
| `exchange_transactions` | YES | MUST BE FULL | Participant | Engine |
| `artefacts` | YES | MUST BE FULL | Participant | Engine |
| `deployments` | YES | FULL | Map | Engine |
| `relationships` | YES | FULL | Participant | Engine |
| `sanctions` | YES | MUST BE FULL | Participant | Engine |
| `tariffs` | YES | MUST BE FULL | Participant | Engine |
| `leadership_votes` | YES | FULL | Participant | Engine |
| `nuclear_actions` | YES | FULL | All | Engine |
| `hex_control` | YES | MUST BE FULL | Map | Engine |
| `role_actions` | YES | MUST BE FULL | Participant | Moderator |
| `org_memberships` | YES | MUST BE FULL | Participant | Engine |
| `world_state` | YES | MUST BE FULL | Facilitator | Engine |
| `ai_agent_sessions` | MUST ADD | MUST BE FULL | AI Dashboard | Engine |
| `users` | MUST ADD | MUST BE FULL | User Management | Auth |
| `organizations` | MUST ADD | MUST BE FULL | Participant | Moderator |

`MUST BE FULL` = currently DEFAULT, needs migration.
`MUST ADD` = not yet in publication, needs migration.

---

## 4. Frontend Data Patterns

### 4.1 Pattern A: Realtime Table (primary pattern)

For lists of data scoped to a simrun:

```typescript
const { data, loading } = useRealtimeTable<Type>('table_name', simId, {
  orderBy: 'created_at.desc',
  limit: 100,
  eq: { country_code: myCountryCode }, // optional filter
})
```

**Use for:** observatory_events, meetings, pending_actions, artefacts, agreements, transactions, etc.

**How it works:** Initial fetch + INSERT/UPDATE/DELETE streaming. State always current.

### 4.2 Pattern B: Realtime Row (single record)

For a single record that changes:

```typescript
const { data: simRun } = useRealtimeRow<SimRun>('sim_runs', simId)
```

**Use for:** sim_runs (current state), specific meeting, specific role.

### 4.3 Pattern C: Realtime-triggered refetch (complex queries)

When the query is too complex for Realtime filters (joins, aggregations):

```typescript
const [data, setData] = useState(initialData)

// Initial fetch
useEffect(() => { fetchComplexData().then(setData) }, [simId])

// Realtime trigger: refetch when source table changes
useEffect(() => {
  const ch = supabase.channel('trigger-key')
    .on('postgres_changes', { event: '*', schema: 'public', table: 'source_table',
      filter: `sim_run_id=eq.${simId}` }, () => fetchComplexData().then(setData))
    .subscribe()
  return () => { supabase.removeChannel(ch) }
}, [simId])
```

**Use for:** Country aggregates, role+country joins, complex dashboard stats.

### 4.4 Pattern D: Fallback poll (resilience only)

As a SUPPLEMENT to Realtime (not replacement). Catches any events the WebSocket missed:

```typescript
// ONLY as backup, with 15-30s minimum interval
const interval = setInterval(() => refetch(), 15000)
```

**Use for:** Critical displays (PublicScreen gauges, facilitator round timer).

### 4.5 FORBIDDEN Pattern: One-time fetch

```typescript
// WRONG — stale on mount:
useEffect(() => { fetchData().then(setData) }, [])

// WRONG — stale after initial load:
useEffect(() => { fetchData().then(setData) }, [simId])
```

**This pattern MUST NOT be used** for any data that can change during the session. If you see this in code, fix it.

---

## 5. Connection Resilience

### 5.1 ChannelManager Must Handle Disconnections

When a channel receives `CHANNEL_ERROR` or `TIMED_OUT`:
1. Log the error
2. Wait 2s (exponential backoff on retry)
3. Remove the dead channel
4. Re-subscribe with fresh channel
5. Trigger a full refetch for all listeners on that channel

### 5.2 Visibility Change Handler

When the browser tab becomes visible again (`document.visibilitychange`):
1. Check all active channels for health
2. Force refetch on all active `useRealtimeTable` instances
3. This handles Safari/iOS aggressive WebSocket cleanup

### 5.3 Heartbeat Monitor

Every 30s, verify the Supabase Realtime connection is alive:
- If `supabase.realtime.isConnected()` returns false: force reconnect
- After reconnect: refetch all active subscriptions

### 5.4 Cross-Browser Requirements

| Platform | Requirement |
|----------|-------------|
| Chrome desktop | Realtime works, visibility refetch handles tab switches |
| Safari desktop | Visibility refetch critical (kills WebSocket after ~30s background) |
| Safari iOS | Visibility refetch + heartbeat (OS kills WebSocket on lock) |
| Chrome Android | Same as iOS Safari |
| Tablets | Same as their OS browser |

**Testing:** Every Realtime feature must be tested on Safari (desktop + iOS) in addition to Chrome.

---

## 6. Component Responsibilities

### ParticipantDashboard

| Data | Current Pattern | Required Pattern |
|------|----------------|-----------------|
| Country stats | One-time fetch in loadData | Pattern C: refetch on `countries` change |
| Artefacts | One-time fetch in loadData | Pattern A: useRealtimeTable |
| Role actions | One-time fetch in loadData | Pattern A: useRealtimeTable |
| Relationships | One-time fetch in loadData | Pattern C: refetch on `relationships` change |
| Sanctions/Tariffs | One-time fetch in loadData | Pattern C: refetch on table change |
| Active meetings | Fetch on dataVersion | Pattern A: useRealtimeTable('meetings') |
| Meeting invitations | useRealtimeTable | CORRECT (keep) |
| Transactions/Agreements | useRealtimeTable | CORRECT (keep) |
| Votes/Elections | useRealtimeTable | CORRECT (keep) |
| roleInfo cache | One-time fetch | Pattern C: refetch on `roles` change |

### FacilitatorDashboard

| Data | Current Pattern | Required Pattern |
|------|----------------|-----------------|
| Sim state | useRealtimeRow | CORRECT (keep) |
| Events | useRealtimeTable | CORRECT (keep) |
| Pending actions | useRealtimeTable | CORRECT (keep) |
| AI agent status | Poll + Realtime | CORRECT (keep) |

### Dashboard (landing page)

| Data | Current Pattern | Required Pattern |
|------|----------------|-----------------|
| Sim availability | One-time fetch | Pattern C: refetch on `sim_runs` change |
| Role assignment | One-time fetch | Pattern C: refetch on `roles` change |

---

## 7. Implementation Phases

### Phase 1: Database Foundation (30 min)
- Set REPLICA IDENTITY FULL on all tables in registry
- Add missing tables to publication
- Zero code changes, immediate improvement

### Phase 2: Connection Resilience (1-2 hours)
- ChannelManager: reconnect on error/timeout
- Visibility change handler: refetch on tab focus
- Heartbeat monitor: periodic connection check

### Phase 3: Component Migration (3-4 hours)
- Replace one-time fetches in ParticipantDashboard
- Add Realtime to Dashboard landing page
- Fix stale closures and remove dataVersion pattern
- Create useSimData() shared hook if beneficial

### Phase 4: Testing (1-2 hours)
- Test on Chrome desktop
- Test on Safari desktop (tab switch test)
- Test on iOS Safari (lock screen test)
- Test on Android Chrome
- Test network drop recovery (DevTools throttle)

---

## 8. Verification Checklist

Before any feature is marked DONE:

- [ ] All queried tables have REPLICA IDENTITY FULL
- [ ] All queried tables are in supabase_realtime publication
- [ ] No one-time fetches for changeable data
- [ ] Tested: data updates without page refresh
- [ ] Tested: tab switch + return shows current data (Safari)
- [ ] Tested: network drop + recovery shows current data

---

*This spec is referenced by `app/frontend/CLAUDE.md` and enforced on all frontend code.*
