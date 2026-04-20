# AUDIT: Realtime & Refresh Issues

**Date:** 2026-04-20
**Scope:** All frontend pages, Supabase Realtime configuration, RLS policies
**Status:** Read-only analysis — no code changes

---

## 1. Executive Summary — Top 5 Issues

| # | Issue | Severity | Impact |
|---|-------|----------|--------|
| **1** | **49 tables NOT published for Realtime** — only 16 of 65 tables are in the `supabase_realtime` publication. Key tables used by frontend (`roles`, `countries`, `world_state`, `sanctions`, `tariffs`, `role_actions`, `artefacts`, `org_memberships`, etc.) lack realtime, forcing one-time fetches that go stale. | CRITICAL | All pages show stale data for unpublished tables until manual refresh or round change. |
| **2** | **RLS blocks participants from 10+ tables** — `roles`, `role_actions`, `org_memberships`, `organizations`, `sanctions`, `tariffs`, `world_state`, `country_state` all have `SELECT` restricted to `is_moderator()`. Participants using the anon key get **empty results**. The ParticipantDashboard's `loadData()` silently fails for these tables. | CRITICAL | Participant dashboard is non-functional or shows incomplete data for non-moderator users. |
| **3** | **JSONB `schedule` field updates don't trigger Realtime** — election state (`nominations_open`, `nominations_closed`, `election_open`, `election_stopped`) is stored as JSONB sub-keys on `sim_runs.schedule`. Supabase Realtime fires on row-level changes but JSONB diff detection is unreliable. Four `*Local` state variables are used as workarounds. | HIGH | Election UI (both Facilitator and Participant) can show stale state; moderator actions may not propagate to participants. |
| **4** | **PublicScreen has no auth but needs authenticated RLS** — route `/screen/:id` requires no login, but `sim_runs`, `observatory_events`, and `nuclear_actions` all have RLS policies restricted to `{authenticated}` role only. An unauthenticated user sees nothing. | HIGH | Public Screen is broken for truly unauthenticated viewers. Only works if user happens to have a session cookie. |
| **5** | **76 REST calls in ParticipantDashboard** — many scattered ad-hoc fetches throughout action forms, each triggered by UI interactions. No caching, no deduplication. Several tables (`countries`, `roles`) are fetched 10+ times in different components. | MEDIUM | Slow page transitions, unnecessary DB load, data inconsistency between components reading the same table at different times. |

---

## 2. Table-by-Table Realtime Status

### 2a. Tables Published for Realtime (16 of 65)

| Table | RLS Enabled | SELECT Policy | Participant Access |
|-------|------------|---------------|-------------------|
| `sim_runs` | Yes | `is_moderator()` only | NO — broken for participants |
| `countries` | Yes | `true` (authenticated) | YES |
| `deployments` | Yes | `true` (authenticated) | YES |
| `relationships` | Yes | `true` (authenticated) | YES |
| `artefacts` | Yes | own role OR moderator | YES (own only) |
| `observatory_events` | Yes | `true` (authenticated) | YES |
| `agreements` | Yes | `true` (authenticated) | YES |
| `exchange_transactions` | Yes | `true` (authenticated) | YES |
| `nuclear_actions` | Yes | `true` (authenticated) | YES |
| `election_nominations` | Yes | `true` (public) | YES |
| `election_votes` | Yes | `true` (public) | YES |
| `election_results` | Yes | `true` (public) | YES |
| `pending_actions` | Yes | `true` (authenticated) | YES |
| `leadership_votes` | Yes | `true` (authenticated) | YES |
| `hex_control` | Yes | `true` (authenticated) | YES |
| `meeting_invitations` | Yes | `true` (public) | YES |

**NOTE:** `sim_runs` is published for Realtime but its SELECT policy is `is_moderator()` only. This means participants subscribed via `useRealtimeRow('sim_runs', simId)` will receive NO updates — Supabase filters out rows the user cannot SELECT.

### 2b. Tables NOT Published but Accessed by Frontend

These tables are fetched via `supabase.from().select()` one-time calls. Changes are NEVER pushed to the client.

| Table | Frontend Usage | RLS SELECT Policy | Participant Access | Staleness Risk |
|-------|---------------|-------------------|-------------------|---------------|
| `roles` | 12+ fetches across ParticipantDashboard | `is_moderator()` | **NO** | HIGH — role status, arrests, power changes invisible |
| `role_actions` | 5+ fetches (uses_remaining) | `is_moderator()` | **NO** | HIGH — action availability stale |
| `org_memberships` | 3+ fetches | `is_moderator()` | **NO** | MEDIUM |
| `organizations` | 2 fetches | `is_moderator()` | **NO** | LOW |
| `sanctions` | 2 fetches | `is_moderator()` | **NO** | HIGH — sanction changes invisible |
| `tariffs` | 2 fetches | `is_moderator()` | **NO** | HIGH — tariff changes invisible |
| `world_state` | 2 fetches (oil_price, etc.) | `is_moderator()` | **NO** | MEDIUM — global economic data stale |
| `country_state` | moderator_all only | `is_moderator()` | **NO** | LOW (not used by participant) |
| `role_relationships` | 2 fetches | none for SELECT | **NO POLICY** | RLS enabled but no SELECT policy = blocked |
| `blockades` | not directly fetched | no SELECT policy | N/A | N/A |
| `basing_rights` | not directly fetched | no SELECT policy | N/A | N/A |
| `combat_results` | not directly fetched by participants | `is_moderator()` | N/A | N/A |
| `round_reports` | not directly fetched | no SELECT policy | N/A | N/A |
| `events` | not directly fetched | `is_moderator()` | N/A | N/A |

### 2c. Tables with RLS Enabled but NO SELECT Policy at All

These tables have RLS enabled (`rowsecurity = true`) but no SELECT policy exists, meaning no one (except service role) can read them:

- `agent_actions`, `agent_conversations`, `agent_decisions`, `agent_memories`, `agent_reflections`, `agent_transactions`
- `ai_context`
- `basing_rights`, `blockades`
- `covert_ops_log`
- `global_state_per_round`
- `judgment_log`
- `layout_units`
- `power_assignments`
- `pre_seeded_meetings`
- `round_reports`, `round_states`
- `run_roles`
- `sim_scenarios`
- `unit_layouts`, `unit_states_per_round`
- `zone_adjacency`, `zones`

Most of these are backend-only tables, so this is likely intentional. However, `run_roles` is used by `getSimRunRoles()` in FacilitatorDashboard.

---

## 3. Page-by-Page Subscription Audit

### 3a. ParticipantDashboard (`/play/:simId`)

**Realtime subscriptions (LIVE):**
| Hook | Table | What | Works for Participant? |
|------|-------|------|----------------------|
| `useRealtimeRow` | `sim_runs` | Sim status, round, phase | **NO** — RLS blocks non-moderators |
| `useRealtimeTable` | `nuclear_actions` | Global nuclear flight banner | YES |
| `useRealtimeTable` | `meeting_invitations` | Incoming meeting invitations | YES |
| `useRealtimeTable` | `pending_actions` (filtered) | Own pending action status | YES |
| `useRealtimeTable` | `agreements` | Proposed agreements | YES |
| `useRealtimeTable` | `leadership_votes` | Active leadership votes | YES |
| `useRealtimeTable` | `election_nominations` | Election nominations | YES |
| `useRealtimeTable` | `election_votes` | Election votes | YES |
| `useRealtimeTable` | `election_results` | Election results | YES |
| `useRealtimeTable` | `exchange_transactions` (outgoing) | Own outgoing transactions | YES |
| Manual channel | `roles` (single row) | Role status changes (arrest) | **NO** — not published + RLS blocks |

**One-time fetches (STALE after load):**
- `roles` (own role) — loaded in `loadData()`, refreshed on round change
- `countries` (own country) — loaded in `loadData()`, refreshed on round change
- `artefacts` — loaded in `loadData()`, refreshed on round change
- `role_actions` — loaded in `loadData()`, refreshed on round change
- `relationships` — loaded in `loadData()`, refreshed on round change
- `org_memberships` — loaded in `loadData()`, refreshed on round change
- `role_relationships` — loaded in `loadData()`, refreshed on round change
- `sanctions`, `tariffs` — loaded in `loadData()`, refreshed on round change
- `sim_runs.schedule` — separate fetches at lines 886 and 930 for election/nomination state, triggered by `dataVersion`
- `countries` — fetched again 10+ times in individual action forms (attack, nuclear, declare_war, etc.)
- `roles` — fetched again 8+ times in action forms (reassign, arrest, change_leader, etc.)
- `world_state` — fetched in World tab
- `organizations` — fetched in meeting setup
- `deployments` — fetched in attack forms and map

**Polling:**
- Nuclear launch status: 2s polling during authorizing/flight phase (line 3054)
- Pending action result: 2s polling while waiting for moderator approval (line 3755)

**Total REST calls on initial page load:** ~12 (1 role query + 10 parallel in `loadData()` + 1 `useRealtimeRow` initial fetch)
**Total REST calls across all interactions:** 76 `supabase.from()` call sites

### 3b. FacilitatorDashboard (`/sim/:id/live`)

**Realtime subscriptions (LIVE):**
| Hook | Table | What |
|------|-------|------|
| `useRealtimeRow` | `sim_runs` | Sim status, round, phase |
| `useRealtimeTable` | `pending_actions` | All pending actions (last 20) |
| `useRealtimeTable` | `observatory_events` | SIM event feed (last 100) |
| `useRealtimeTable` | `nuclear_actions` | Nuclear flight tracking |
| `useRealtimeTable` | `leadership_votes` | Leadership vote tallies |
| `useRealtimeTable` | `election_nominations` | Election nomination tracking |
| `useRealtimeTable` | `election_votes` | Election vote tracking |
| `useRealtimeTable` | `election_results` | Election results |

**One-time fetches (STALE after load):**
- `getSimRunRoles()` — roles list, loaded once
- `countries` (Columbia stability) — single fetch for auto-approve checks (line 1502)
- `getAllUsers()` — loaded when user management panel opened

**Refresh workarounds:**
- Retry loading roles after 3s timeout (auth token may not be ready)
- `refetchElectionVotes()` called with 500ms delay after election stop (line 1272)

**Total REST calls on page load:** ~3 (1 simRun, 1 roles, 8 realtime initial fetches)

### 3c. PublicScreen (`/screen/:id`)

**Realtime subscriptions (LIVE):**
| Channel | Table | What |
|---------|-------|------|
| `pub_sim:{id}` | `sim_runs` | Sim status, round, phase changes |
| `pub_events:{id}` | `observatory_events` | News ticker (INSERT only) |
| `pub_nuclear:{id}` | `nuclear_actions` | Nuclear flight tracking |

**One-time fetches (STALE):**
- `getSimRun()` — initial sim_runs load
- `observatory_events` — initial events load (last 30)

**Never-updated static data:**
- Doomsday Indices — hardcoded defaults (5, 6, 4, 4), never fetched from DB
- Columbia vs Cathay Power — hardcoded (55/45), never updated

**Polling:**
- 30s fallback polling of `loadData()` (line 274)

**Auth issue:** Uses manual `supabase.channel()` directly (not via ChannelManager). These channels require authenticated RLS but the page has no auth.

### 3d. ModeratorDashboard (`/dashboard`)

- One-time fetch of `getSimRuns()` — list of all sim runs
- No realtime subscriptions
- No refresh mechanism — completely stale after load

---

## 4. JSONB Workaround Inventory

### The Problem

`sim_runs.schedule` is a JSONB column storing election control state:
- `nominations_open` (boolean)
- `nominations_closed` (boolean)
- `election_open` (boolean)
- `election_started_at` (timestamp string)
- `election_stopped` (boolean)
- `election_duration_minutes` (number)
- `phase_a_minutes` (number)

When the moderator updates these sub-keys via `supabase.from('sim_runs').update({ schedule: newSched })`, the entire JSONB blob is replaced. Supabase Realtime DOES fire for this (it's a row-level UPDATE), but there are timing and reliability issues.

### Where schedule JSONB is UPDATED (FacilitatorDashboard)

| Line | Field Updated | Context |
|------|--------------|---------|
| 964 | `nominations_open: true` | Moderator opens nominations |
| 1053 | `nominations_closed: true` | Moderator closes nominations |
| 1127 | `election_open: true, election_started_at` | Moderator starts election |
| 1161 | `election_stopped: true` | Moderator stops election |
| 1252 | `election_stopped: true` | Manual stop button |
| 1270 | reset all election flags | Re-open nominations |

### Where schedule JSONB is READ

| Page | Line | What's read |
|------|------|-------------|
| FacilitatorDashboard | 403-404 | `phase_a_minutes` for timer |
| FacilitatorDashboard | 942 | `nominations_open` |
| FacilitatorDashboard | 977 | `nominations_closed` |
| FacilitatorDashboard | 1070 | `election_open`, `election_started_at`, `election_stopped`, `election_duration_minutes` |
| ParticipantDashboard | 199-200 | `phase_a_minutes` for timer |
| ParticipantDashboard | 886-893 | `nominations_open`, `nominations_closed` (separate REST fetch!) |
| ParticipantDashboard | 930-935 | `election_open` (separate REST fetch!) |
| PublicScreen | 167 | `phase_a_minutes` for timer |

### Local State Workarounds in FacilitatorDashboard

| Variable | Line | Purpose |
|----------|------|---------|
| `electionStartedLocal` | 337 | Optimistic UI for "election started" before Realtime confirms |
| `electionStartedAtLocal` | 338 | Optimistic timestamp |
| `electionStoppedLocal` | 339 | Optimistic UI for "election stopped" |
| `nominationsClosedLocal` | 340 | Optimistic UI for "nominations closed" |
| `localVoteOverrides` | 341 | Optimistic vote display |

These are reset when the moderator re-opens nominations (line 965-969).

### Root Cause

The actual root cause is NOT that JSONB updates don't fire Realtime — they do, since it's a row UPDATE. The real issues are:
1. **ParticipantDashboard reads schedule via SEPARATE REST calls** (lines 886, 930) instead of using the already-subscribed `simRun` object. These are triggered by `dataVersion` (which only updates on `loadData()` completion).
2. **`sim_runs` RLS blocks participants** from receiving Realtime updates, so even the `useRealtimeRow` subscription is broken for them.
3. The FacilitatorDashboard correctly reads schedule from the realtime `simRun` object but uses local state as optimistic UI, which is reasonable.

---

## 5. Performance Analysis

### 5a. Channel Count per Page

| Page | Realtime Channels | Method |
|------|-------------------|--------|
| ParticipantDashboard | 10-11 via ChannelManager + 1 manual | Mixed: useRealtimeTable (deduplicated) + manual channel for role status |
| FacilitatorDashboard | 8 via ChannelManager | All via useRealtimeTable/useRealtimeRow |
| PublicScreen | 3 manual channels | Direct supabase.channel() — NOT using ChannelManager |

The ChannelManager properly deduplicates channels per table+simId and ref-counts them. This is well-architected. However, PublicScreen bypasses it.

### 5b. REST Request Analysis

**ParticipantDashboard initial load sequence:**
1. `useRealtimeRow('sim_runs')` — 1 fetch
2. `useRealtimeTable` x 9 hooks — 9 fetches (parallel, via ChannelManager)
3. `loadData()` — 1 roles query + 10 parallel queries = 11 fetches
4. Election state checks — 2 fetches (schedule for nominations + election)
5. **Total initial: ~23 REST requests**

**ParticipantDashboard per-action overhead:**
- Opening Attack form: 3-5 fetches (countries, deployments, roles)
- Opening Nuclear form: 2 fetches (countries, deployments)
- Opening Transaction form: 4 fetches (countries, roles, orgs, role_actions)
- These are NOT cached — re-fetched every time the form opens

**Redundant fetches (same data, multiple components):**
- `countries` list (`id, sim_name, color_ui`): fetched at lines 2384, 3552, 4467, 4792, 4982, 5953, 6125, 6559 — **8 times**
- `roles` list: fetched at lines 717, 755, 1747, 4461, 4980, 5123, 5298, 5328, 5458, 6928 — **10 times**
- `role_actions.uses_remaining`: fetched at lines 4686, 4793, 4984, 5125 — **4 times**

### 5c. ChannelManager Analysis

The ChannelManager is well-designed:
- Singleton persisted across HMR via `window.__ttt_channel_manager__`
- Deduplicates by `rt:{table}:{simId}` key
- Reference counting for cleanup
- Fan-out to multiple listeners
- Error isolation between listeners

**Potential issue:** The ChannelManager always uses `filter: sim_run_id=eq.${simId}` for all tables. But `useRealtimeRow` for `sim_runs` uses a different channel directly (`rt:{table}:row:{id}`), so there's no conflict. However, the manual channel in ParticipantDashboard for role status (`role-status:{roleId}`) is outside the ChannelManager — it won't be deduplicated if the component re-mounts.

---

## 6. Recommended Fixes (Ranked)

### Tier 1: Critical / Low Risk

#### Fix 1.1: Add participant SELECT policies to essential tables
**Tables:** `roles`, `role_actions`, `org_memberships`, `organizations`, `sanctions`, `tariffs`, `world_state`
**Action:** Add RLS policies like `CREATE POLICY "authenticated_read_<table>" ON <table> FOR SELECT TO authenticated USING (true);`
**Impact:** Fixes the fundamental broken state of the ParticipantDashboard for non-moderator users.
**Risk:** Low — these are read policies; game data is not secret between participants in this simulation.
**Effort:** 1 migration file, 7 policy statements.

#### Fix 1.2: Add `sim_runs` SELECT policy for participants
**Action:** Add `CREATE POLICY "sim_runs_select_participant" ON sim_runs FOR SELECT TO authenticated USING (true);`
**Impact:** Fixes realtime `sim_runs` updates for participants. Currently the most critical subscription (`useRealtimeRow('sim_runs')`) is silently broken.
**Risk:** Low.
**Effort:** 1 policy statement.

#### Fix 1.3: Add `role_relationships` SELECT policy
**Action:** Currently has NO SELECT policy at all (only moderator_all and service). Add one for authenticated users.
**Impact:** Fixes personal relationships display in ParticipantDashboard.
**Risk:** Low.

### Tier 2: High Impact / Medium Risk

#### Fix 2.1: Publish key tables to Supabase Realtime
**Tables to add to publication:**
- `roles` — role status changes (arrest, release, death) need to propagate live
- `countries` — already published but confirm; GDP/stability changes after round processing
- `sanctions` — sanction changes mid-round
- `tariffs` — tariff changes mid-round
- `world_state` — oil price, global metrics
- `artefacts` — new artefacts delivered mid-round
- `role_actions` — uses_remaining updates after action submission

**Action:** `ALTER PUBLICATION supabase_realtime ADD TABLE roles, sanctions, tariffs, world_state, artefacts, role_actions;`
**Impact:** Enables live updates for data that currently goes stale.
**Risk:** Medium — need to verify RLS policies are correct first (Tier 1 fixes).
**Effort:** 1 migration + add `useRealtimeTable` hooks in ParticipantDashboard.

#### Fix 2.2: Replace ParticipantDashboard schedule REST fetches with realtime data
**Lines:** 886 and 930
**Current:** Separate `supabase.from('sim_runs').select('schedule')` calls triggered by `dataVersion`
**Fix:** Read from the already-subscribed `simRun` object: `simRun?.schedule?.nominations_open`
**Impact:** Eliminates 2 stale REST calls; election state updates immediately via Realtime.
**Prerequisite:** Fix 1.2 (participant must be able to receive sim_runs Realtime events).
**Effort:** ~10 lines changed.

#### Fix 2.3: Add PublicScreen auth or public RLS policies
**Options:**
1. Auto-login with a "public viewer" anonymous Supabase session on PublicScreen mount
2. Add `{public}` (anon) SELECT policies to `sim_runs`, `observatory_events`, `nuclear_actions`

**Impact:** Fixes PublicScreen for truly unauthenticated viewers.
**Risk:** Option 2 exposes data to anonymous users — may need row-level filtering.
**Effort:** Medium.

### Tier 3: Medium Impact / Higher Effort

#### Fix 3.1: Cache and share country/role lookups across action forms
**Current:** `countries(id, sim_name, color_ui)` and `roles(id, character_name)` are fetched 8-10 times each by different components.
**Fix:** Lift these to ParticipantDashboard parent state or a Zustand store, pass down as props/context. Or use a React Query-style cache.
**Impact:** Eliminates 15-20 redundant REST calls per page session.
**Effort:** Medium refactor.

#### Fix 3.2: Migrate PublicScreen to ChannelManager + useRealtimeTable
**Current:** PublicScreen uses 3 manual `supabase.channel()` subscriptions.
**Fix:** Switch to `useRealtimeTable` / `useRealtimeRow` hooks.
**Impact:** Consistency, deduplication, proper cleanup.
**Effort:** Low-medium refactor.

#### Fix 3.3: Implement Doomsday Indices and Power Balance
**Current:** Hardcoded at `{5, 6, 4, 4}` and `55/45`.
**Fix:** Calculate from DB data (country GDP, military, nuclear status, relationships) or subscribe to a dedicated `world_state` or `global_state_per_round` table.
**Impact:** PublicScreen displays meaningful data instead of static numbers.
**Effort:** Medium — requires defining the calculation formulas.

#### Fix 3.4: Replace nuclear launch polling with Realtime
**Current:** 2s polling via `fetch('/api/sim/${simId}/nuclear/active')` during launch phase.
**Fix:** `nuclear_actions` is already published for Realtime and the ParticipantDashboard already subscribes to it via `useRealtimeTable`. Use that data instead of polling.
**Impact:** Eliminates polling, reduces server load, faster updates.
**Effort:** Low.

### Tier 4: Architectural / Long-term

#### Fix 4.1: Extract election state from schedule JSONB into dedicated columns or table
**Current:** Election state scattered across `sim_runs.schedule` JSONB sub-keys.
**Fix:** Add columns like `nominations_open`, `election_open`, `election_stopped` directly on `sim_runs`, or create an `election_state` table.
**Impact:** Clean data model, no JSONB parsing in frontend, proper Realtime granularity.
**Effort:** High — migration + update all read/write sites.

#### Fix 4.2: Introduce React Query or SWR for data fetching
**Impact:** Automatic caching, deduplication, stale-while-revalidate, background refetch.
**Effort:** High — wrap all `supabase.from()` calls.

---

## Appendix: Tables Summary

**Total tables:** 65
**Published for Realtime:** 16 (24.6%)
**Accessed by frontend:** ~25
**With participant-accessible SELECT policy:** ~16
**Frontend tables with broken RLS for participants:** ~8
**Tables with RLS enabled but zero SELECT policy:** ~20 (mostly backend-only, acceptable)
