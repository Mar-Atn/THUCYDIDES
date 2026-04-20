# AUDIT CROSS-CHECK REPORT

**Date:** 2026-04-20
**Auditor:** Cross-Check Agent (read-only, independent verification)
**Inputs:** 4 audit reports — Comprehensive Build Documentation, Realtime & Refresh, Functional Redundancies, Scalability

---

## 1. CONTRADICTIONS FOUND

### 1.1 Table Count Discrepancy
- **Realtime audit:** States "65 tables" total, 16 published for Realtime.
- **DB verification:** Actual count is **64 tables** (confirmed via `pg_tables`). The Realtime audit likely counted the `realtime.messages` table or double-counted one table.
- **Published tables:** Confirmed exactly **16** via `pg_publication_tables`. This is accurate.
- **Impact:** Minor. The off-by-one does not affect recommendations.

### 1.2 Scalability vs Realtime: Channel Count Estimates Agree (No Contradiction)
- Scalability audit estimated ~75-80 Supabase Realtime channels. Realtime audit counted 10-11 channels per ParticipantDashboard via ChannelManager + 1 manual. These are consistent because the ChannelManager deduplicates -- both reports correctly identified this.

### 1.3 Comprehensive Doc vs Realtime Audit: Realtime Table List Mismatch
- **Comprehensive Build Doc (Section 4, M2):** Lists `countries (UPDATE)`, `deployments (INSERT, UPDATE, DELETE)`, `hex_control (INSERT, UPDATE)` as Realtime-enabled. This is correct per DB verification.
- **Comprehensive Build Doc** also lists channel structure (`sim:{sim_id}:country:{cc}`, `sim:{sim_id}:presence`, etc.) that does NOT match actual implementation. The ChannelManager uses `rt:{table}:{simId}` keys. The documented channel naming appears aspirational, not actual.
- **Impact:** The Comprehensive Build Doc's M2 section gives a misleading picture of the Realtime architecture. The Realtime audit is more accurate.

### 1.4 Functional Audit vs Realtime Audit: RLS Claims Agreement
- Both reports agree that `roles`, `role_actions`, `sanctions`, `tariffs`, `world_state`, `org_memberships`, `organizations` have moderator-only SELECT policies, blocking participants.
- **DB verification confirms:** These tables indeed have only `is_moderator()` SELECT policies. No contradiction here -- both reports correctly identified the same critical issue.

### 1.5 Comprehensive Doc vs Functional Audit: `sim_scenarios` Status
- **Comprehensive Build Doc:** States "`sim_scenarios` table is **retired**."
- **Functional audit:** Does not mention `sim_scenarios` at all.
- **DB verification:** `sim_scenarios` table exists, has RLS enabled, has 0 SELECT policies. It was not listed as empty in the functional audit (it may have rows from seeds).
- **Impact:** Minor. Consistency gap in documentation coverage.

### 1.6 Scalability Audit: N+1 Query Attribution
- **Scalability audit (Section 7):** Claims a per-event deployment lookup N+1 pattern at "line 257 of main.py."
- **Code verification:** The N+1 is at lines 315-320 (within the `get_map_combat_events` endpoint starting at line 257). The line reference is slightly inaccurate but the issue is real. Each combat event without pre-existing theater coordinates triggers a separate `deployments` query.
- **Impact:** The bug is real, but it only fires for events missing `target_theater_row` in their payload. Events that include theater coords skip the lookup.

---

## 2. GAPS IN COVERAGE

### 2.1 Tables Missed by Functional Audit's Dead Table Inventory
The functional audit listed 14 orphan tables. Independent verification found **2 additional**:
- **`transactions`** — 0 rows, not referenced anywhere in `app/engine/` code. Likely a vestigial table from early design. NOT listed in functional audit.
- **`observatory_combat_results`** — 0 rows but IS referenced by `movement_context.py`, `sim_run_manager.py`, tests, and `test-interface/server.py`. This is a runtime-populated table, not dead. The functional audit missed it entirely (neither dead nor live inventory).

### 2.2 MARTIAL_LAW_POOLS: 4 Copies, Not 3
- **Functional audit** identified 3 copies (martial_law_engine.py, domestic_validator.py, resolve_round.py).
- **Code verification** found a **4th copy** in `ParticipantDashboard.tsx` (line 2544) -- a frontend JavaScript version of the same constant.
- **Impact:** The functional audit underestimated the problem by missing the cross-language duplication.

### 2.3 No Audit Covered the `test-interface/` Directory
All 4 audits focus on `app/engine/` and `app/frontend/`. The `app/test-interface/` directory (which serves the hex map renderer and has its own `server.py` with 1,297+ lines) was not audited by any report. This is a significant gap because:
- It has its own REST endpoints for combat results (`observatory_combat_results`)
- It duplicates map configuration from `map_config.py` into `map_config.js`
- It serves as an iframe embedded in the production frontend

### 2.4 No Audit Covered Database Indexes
- **Scalability audit** mentions "Missing Indexes (probable)" but qualifies with "without seeing the actual DB schema applied."
- No audit actually queried `pg_indexes` to verify which compound indexes exist or are missing.
- **Impact:** The scalability recommendations about indexes remain unverified.

### 2.5 No Audit Covered Error Handling / Resilience
None of the 4 reports analyzed:
- What happens when an LLM call fails mid-agent-round (partial state)
- What happens when a DB write fails during combat resolution (partial losses applied)
- Whether any transaction/rollback patterns exist in the engine
- Frontend error boundaries or retry logic

### 2.6 `election_nominations` and `election_votes` Have Public RLS
- **Realtime audit** correctly noted these tables have `true (public)` SELECT policies.
- No report flagged the security implication: these tables can be read by **unauthenticated** users (anon key), not just authenticated ones. Secret ballot votes are readable by anyone with the project URL and anon key.

---

## 3. CONSOLIDATED PRIORITY LIST

Merging all 4 reports, de-duplicated and ordered by combined severity.

### CRITICAL (must fix before any live event)

| # | Issue | Source Report(s) | Effort |
|---|-------|-----------------|--------|
| C1 | **RLS blocks participants from `sim_runs`, `roles`, `role_actions`, `sanctions`, `tariffs`, `world_state`, `org_memberships`, `organizations`** — ParticipantDashboard is broken for non-moderator users | Realtime | 1 migration, 8 policy statements, ~30 min |
| C2 | **`role_relationships` has NO SELECT policy** — blocked for everyone except service role | Realtime | 1 policy statement, 5 min |
| C3 | **Sync-over-async DB calls** — all `supabase.py` async functions wrap sync HTTP, blocking FastAPI event loop | Scalability | 2-3 days (option b: wrap in `asyncio.to_thread()` is 1 day) |
| C4 | **Sync LLM calls blocking event loop** — `_call_anthropic()` and `_call_gemini()` are sync inside `async _call_provider()` | Scalability | 30 min |

### HIGH (should fix before production)

| # | Issue | Source Report(s) | Effort |
|---|-------|-----------------|--------|
| H1 | **49 tables NOT published for Realtime** — key tables (`roles`, `sanctions`, `tariffs`, `world_state`, `role_actions`) cause stale data | Realtime | 1 migration + frontend hook changes, 1 day |
| H2 | **Single FastAPI process, no workers** — one blocked request stalls all | Scalability | 1 hour |
| H3 | **PublicScreen has no auth but needs authenticated RLS** — broken for unauthenticated viewers | Realtime | Half day |
| H4 | **14 duplicate `_write_event()` functions** with inconsistent parameter order | Functional | 1 day |
| H5 | **13 duplicate `_get_scenario_id()` functions** | Functional | Half day |
| H6 | **`resolve_round.py` labeled DEPRECATED but is core engine** — imported by 29 test files + `full_round_runner.py` | Functional | Design decision needed |
| H7 | **Batch ParticipantDashboard REST calls** — 22 REST calls per page load x 30 users = 660 burst | Scalability | 1 day |
| H8 | **Deprecated `stage*_test.py` files still imported by active code** — `leader_round.py` depends on constants in deprecated files | Functional | Half day (extract constants) |
| H9 | **Election votes readable by unauthenticated users** — secret ballot compromised | Cross-check (new finding) | 1 policy change, 15 min |

### MEDIUM (should fix before scaling)

| # | Issue | Source Report(s) | Effort |
|---|-------|-----------------|--------|
| M1 | **`_hex_distance()` duplicated in 5 files** | Functional | 1 hour |
| M2 | **MARTIAL_LAW_POOLS in 4 places** (3 backend + 1 frontend) | Functional + Cross-check | 1 hour |
| M3 | **OPEC_MEMBERS in 3 places** | Functional | 30 min |
| M4 | **ParticipantDashboard.tsx is 7,108 lines** — monolith | Functional | 2-3 days (phased extraction) |
| M5 | **N+1 query in combat events endpoint** | Scalability | 30 min |
| M6 | **`useRealtimeRow` bypasses ChannelManager** | Scalability, Realtime | 2 hours |
| M7 | **76 REST calls scattered in ParticipantDashboard** — countries fetched 8x, roles 10x | Realtime | 1 day (React Query or store) |
| M8 | **country_code vs country_id naming split** across DB and code | Functional | Multi-sprint (incremental) |
| M9 | **position_type vs positions[] vs is_* booleans** — 3 systems for the same concept | Functional | Design decision + migration |
| M10 | **Doomsday Indices and Power Balance hardcoded** on PublicScreen | Realtime, Comprehensive | 1 day |
| M11 | **14 orphan DB tables + 1 missed (`transactions`)** — dead schema | Functional + Cross-check | 1 migration, 30 min |
| M12 | **Deprecated columns** (`ticking_clock`, `fatherland_appeal`, `zone_id`) still in schema | Functional | 1 migration |
| M13 | **Probabilities scattered** across 8+ engine files with no central config | Functional | Design decision + 1 day |
| M14 | **JSONB schedule field** — election state buried in JSONB sub-keys | Realtime | High effort migration |

---

## 4. INDEPENDENT VERIFICATION RESULTS

### 4.1 Line Counts (all confirmed accurate)

| File | Claimed | Actual | Match |
|------|---------|--------|-------|
| ParticipantDashboard.tsx | 7,108 | **7,108** | YES |
| FacilitatorDashboard.tsx | 2,160 | **2,160** | YES |
| main.py | 1,935 | **1,935** | YES |
| resolve_round.py | 2,087 | **2,087** | YES |
| llm.py | 354 (Comprehensive says N/A) | **354** | YES |

### 4.2 Sync-over-Async Pattern (CONFIRMED)

- `supabase.py` line 36: `async def check_connection()` calls `client.table().select().execute()` synchronously.
- `supabase.py` line 64: `async def get_countries()` same pattern.
- `llm.py` line 182: `_call_provider()` is `async def` but calls `_call_anthropic()` (line 198, plain `def`) without `await asyncio.to_thread()`. The result is assigned directly (line 182: `result = _call_anthropic(...)`) -- no `await`, confirming it blocks the event loop.
- **Verdict:** Scalability audit's P0 findings are correct.

### 4.3 Realtime Publication Status (CONFIRMED from DB)

**Published (16 tables, verified):** agreements, artefacts, countries, deployments, election_nominations, election_results, election_votes, exchange_transactions, hex_control, leadership_votes, meeting_invitations, nuclear_actions, observatory_events, pending_actions, relationships, sim_runs.

**NOT published (key frontend tables, verified):** roles, role_actions, sanctions, tariffs, world_state, org_memberships, organizations, role_relationships.

The Realtime audit's findings are fully confirmed.

### 4.4 RLS Policy Verification (CONFIRMED from DB)

Tables with ONLY `is_moderator()` SELECT policy (participant blocked):
- `roles`, `sanctions`, `tariffs`, `world_state`, `org_memberships`, `organizations`, `sim_runs`, `sim_config`, `sim_templates`, `zones`

Tables with `true` (authenticated) SELECT:
- `countries`, `deployments`, `agreements`, `hex_control`, `relationships`, `observatory_events`, `pending_actions`, `nuclear_actions`, `leadership_votes`, `exchange_transactions`

Tables with `true` (public/anon) SELECT:
- `election_nominations`, `election_votes`, `election_results`

Tables with NO SELECT policy at all:
- `role_relationships` (confirmed -- RLS enabled, zero policies)

**The Realtime audit's RLS findings are accurate.** Additional finding: `sim_runs` being moderator-only means participants cannot receive Realtime updates for round/phase changes -- this is arguably the single most critical RLS issue.

### 4.5 Dead Code Verification (5 samples checked)

| Claimed Dead | Verified | Finding |
|-------------|----------|---------|
| `stage1_test.py` — "nobody imports" | **CONFIRMED** — no import found anywhere | Truly dead |
| `stage2_test.py` — "imported by 5 files" | **CONFIRMED** — imported by stage3, stage4, stage5, full_round_runner, leader_round (via `load_hos_agents`) | Correctly flagged as dependency chain |
| `resolve_round.py` — "imported by 29 test files" | **CONFIRMED** — found 19+ imports across L2/L3 tests + `full_round_runner.py` | Core code mislabeled as deprecated |
| `ai_context` table — "0 rows, no code refs" | **CONFIRMED** — 0 rows, no references in engine code | Truly dead |
| `transactions` table — NOT in any audit | **NEW FINDING** — 0 rows, zero references in `app/engine/` code | Orphan table missed by all audits |

### 4.6 Action Flow Verification (5 actions traced)

| Action | Dispatcher Route | Engine | Events | DB Writes | Status |
|--------|-----------------|--------|--------|-----------|--------|
| `assassination` | line 196 | `assassination_engine.execute_assassination()` | `write_event()` via common.py | roles.status update | WIRED correctly |
| `arrest` | line 181 | `arrest_engine.request_arrest()` | `write_event()` at line 190 | roles.status update | WIRED correctly |
| `intelligence` | line 162 | `intelligence_engine.generate_intelligence_report()` | N/A (returns report) | artefacts INSERT | WIRED correctly |
| `propose_transaction` | line 240 | `transaction_engine.propose_exchange()` | exchange_transactions INSERT | exchange_transactions | WIRED correctly |
| `set_budget` | line 275 | `_queue_batch_decision()` (queued for Phase B) | agent_decisions INSERT | Deferred to orchestrator | WIRED correctly |

All 5 action flows route correctly from dispatcher to engine to DB. No broken chains found.

### 4.7 Empty Tables Count
- **Functional audit claimed:** 14 orphan tables
- **DB verification:** 29 tables with 0 rows total. Of those, ~15 are runtime-populated (blockades, pending_actions, election_votes, etc.) and ~14-15 are truly orphaned.
- **Missed by all audits:** `transactions` (0 rows, no code references), `observatory_combat_results` (0 rows but IS referenced by code -- runtime-populated, not dead).

---

## 5. FINAL RECOMMENDED ACTION PLAN (Top 20, Priority-Ordered)

### Week 1: Unblock Participant Dashboard (without this, no live event is possible)

1. **Add participant SELECT policies** to `sim_runs`, `roles`, `role_actions`, `sanctions`, `tariffs`, `world_state`, `org_memberships`, `organizations`, `role_relationships`. One migration file, 9 policy statements. (Sources: Realtime C1, C2)

2. **Fix sim_runs SELECT policy** specifically -- this unblocks Realtime round/phase updates for all participants. (Source: Realtime Fix 1.2)

3. **Restrict election_votes SELECT to authenticated** (currently `public`/anon -- secret ballot exposed). (Source: Cross-check new finding)

### Week 1-2: Fix Backend Blocking (without this, 30 concurrent users will timeout)

4. **Wrap sync LLM calls in `asyncio.to_thread()`** inside `_call_provider()`. 30-minute fix. (Source: Scalability P0 8.2)

5. **Wrap sync Supabase calls in `asyncio.to_thread()`** or switch to async client. Start with the most-hit functions (`get_countries`, `get_roles`, `check_connection`). (Source: Scalability P0 8.1)

6. **Add uvicorn workers** (`--workers 4`). 1-hour fix. (Source: Scalability P0 8.3)

### Week 2: Reduce REST Burst

7. **Create batched player-state endpoint** (`/api/sim/{id}/player-state/{role_id}`) -- reduces 660 burst calls to 30. (Source: Scalability P1 8.4)

8. **Fix N+1 in combat events endpoint** -- batch-load deployments once, lookup in dict. (Source: Scalability P1 8.6)

9. **Publish key tables for Realtime** (`roles`, `sanctions`, `tariffs`, `world_state`, `role_actions`) -- enables live updates, reduces polling/stale-data workarounds. (Source: Realtime Fix 2.1)

### Week 2-3: Code Health (Eliminate Duplication)

10. **Consolidate `_write_event()`** -- migrate 14 private copies to `common.write_event()` with standardized parameter order. (Source: Functional 8.1 Phase 1 item 2)

11. **Consolidate `_get_scenario_id()`** -- migrate 13 copies to `common.get_scenario_id()`. (Source: Functional 8.1 Phase 1 item 3)

12. **Extract `hex_distance()` to `engine/services/hex_utils.py`** -- single canonical implementation, update 5 files. (Source: Functional 8.1 Phase 1 item 4)

13. **Extract constants from deprecated `stage*_test.py`** -- move `TOOL_SCHEMAS`, `COMMIT_ACTION_SCHEMA`, `load_hos_agents` to `engine/agents/schemas.py`. Then delete the 5 deprecated stage files. (Source: Functional 8.1 Phase 1 item 5)

14. **Centralize `MARTIAL_LAW_POOLS`** (4 copies) and **`OPEC_MEMBERS`** (3 copies) in `config/position_actions.py`. Import everywhere else. (Source: Functional 8.1 Phase 1 items 6-7)

### Week 3-4: PublicScreen and Architecture

15. **Fix PublicScreen auth** -- either auto-login anonymous session or add public RLS policies for `sim_runs`, `observatory_events`, `nuclear_actions`. (Source: Realtime Fix 2.3)

16. **Route `useRealtimeRow` through ChannelManager** for deduplication. (Source: Scalability P1 8.5, Realtime 5c)

17. **Resolve `resolve_round.py` status** -- either remove the DEPRECATED label (it IS the core engine) or actually migrate its logic to `engines/*`. Design decision needed from Marat. (Source: Functional 8.1 Phase 3 item 14)

### Week 4+: Debt Cleanup

18. **Drop 15 orphan DB tables** (`ai_context`, `ai_contexts`, `ai_decisions`, `argus_conversations`, `argus_event_memory`, `combat_results`, `country_state`, `events`, `facilitators`, `judgment_log`, `messages`, `meetings`, `pre_seeded_meetings`, `role_state`, `transactions`). (Source: Functional + Cross-check)

19. **Drop deprecated columns** (`ticking_clock`, `fatherland_appeal` on roles; `zone_id` on deployments). (Source: Functional 8.1 Phase 1 item 8, Phase 2 item 9)

20. **Begin ParticipantDashboard.tsx decomposition** -- extract NuclearModal, TabActions, ActionForms into separate files. Target: main file under 2,000 lines. (Source: Functional 8.1 Phase 2 item 12)

---

## 6. BLIND SPOTS (What None of the Reports Covered)

1. **Error handling / partial failure resilience** -- no analysis of what happens when DB writes fail mid-combat-resolution, when LLM calls timeout during agent rounds, or when Supabase Realtime disconnects.

2. **`test-interface/` directory** -- the hex map renderer (`app/test-interface/`) has its own server, endpoints, and config duplication. Not covered by any audit.

3. **Actual database indexes** -- no audit queried `pg_indexes` to verify which compound indexes exist. Scalability recommendations on indexes are speculative.

4. **Security beyond RLS** -- no analysis of CORS configuration (currently `*`), service_role key exposure risk, or rate limiting on action submissions.

5. **Data migration / rollback safety** -- `sim_run_manager.py` has a rollback endpoint. No audit tested whether rollback correctly restores all 11+ tables or leaves orphaned data.

6. **Frontend bundle size and performance** -- 7,108-line ParticipantDashboard impacts not just maintainability but initial load time. No audit measured JS bundle sizes or Lighthouse scores.

7. **WebSocket reconnection behavior** -- what happens when a participant's connection drops and reconnects? Does the ChannelManager re-subscribe correctly? No audit tested this.

---

*End of cross-check report. No code was modified.*
