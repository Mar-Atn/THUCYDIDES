# DET_ROUND_WORKFLOW.md
## Complete Facilitator Round-End Workflow
**Version:** 1.0 | **Date:** 2026-03-30 | **Status:** DRAFT
**Owner:** NOVA (Backend) + SIMON (SIM Design)
**Cross-references:** [C3 API Spec](DET_C3_API_SPEC.yaml) | [F5 Engine API](DET_F5_ENGINE_API.md) | [Edge Functions](DET_EDGE_FUNCTIONS.md) | [C1 System Contracts](DET_C1_SYSTEM_CONTRACTS.md)

---

# PURPOSE

This document specifies the complete facilitator workflow from "End Phase A" through "Next Round Begins" as a single end-to-end sequence. This was identified as a gap in DET_VALIDATION_LEVEL3 (Trace 3, Issue T3-3): the full facilitator workflow spans multiple endpoints across C3 and F5 but was not documented as a unified sequence.

---

# COMPLETE ROUND WORKFLOW

## Overview

```
Phase A (Live Play, 60 min)
    |
    v
Step 1: Facilitator clicks "End Phase A"
Step 2: System collects all pending submissions
Step 3: Facilitator reviews submissions summary
Step 4: Facilitator triggers "Process Round"
Step 5: Edge Function assembles data, calls F5 /engine/round/process
Step 6: Engine runs 14-step world model + elections
Step 7: Results returned to Edge Function
Step 8: Expert panel adjustments applied (within engine)
Step 9: Coherence flags raised (within engine)
Step 10: Facilitator reviews results + expert panel + flags
Step 11: Facilitator can override any value
Step 12: Facilitator clicks "Publish"
Step 13: Edge Function calls F5 /engine/round/publish
Step 14: Results written to DB, events logged
Step 15: Real-time broadcast to all channels
Step 16: Participants see new world state
Step 17: Next round begins (Phase A timer starts)
```

---

## Step-by-Step Specification

### Step 1: Facilitator Clicks "End Phase A"

| Property | Value |
|----------|-------|
| **Who** | Facilitator (moderator) |
| **UI** | Facilitator Dashboard > Round Management > "End Phase A" button |
| **C3 Endpoint** | `POST /moderator/round/advance` |
| **Request** | `{ "action": "end_phase_a" }` |
| **What Happens** | Phase changes from `A` to `B`. Timer stops. Late submissions blocked. |
| **Channel** | `sim:{sim_run_id}:phase` -- broadcasts `system.phase_change` event |
| **DB Change** | `sim_runs.current_phase = 'B'` |
| **Can Fail** | Yes -- if phase is not `A`, returns `409 Conflict` |

### Step 2: System Collects All Pending Submissions

| Property | Value |
|----------|-------|
| **Who** | Automatic (triggered by Step 1) |
| **What Happens** | Edge Function queries all submitted actions for the current round |
| **Data Collected** | Per country: budget (from `country_state.budget`), tariffs (from `tariffs`), sanctions (from `sanctions`), OPEC production (from `country_state.opec_production`), Phase A events (from `events` table) |
| **Missing Submissions** | Countries without submitted budgets are flagged. Previous round settings used as default. |
| **Output** | Submissions summary JSON for facilitator review |
| **Can Fail** | No -- missing submissions use defaults |

### Step 3: Facilitator Reviews Submissions Summary

| Property | Value |
|----------|-------|
| **Who** | Facilitator (moderator) |
| **UI** | Facilitator Dashboard shows: countries that submitted budgets, countries with defaults, Phase A combat count, transaction count, covert ops count |
| **C3 Endpoint** | `GET /moderator/state/{round_num}` (includes submission status) |
| **Decision Point** | Facilitator can: (a) proceed to engine processing, (b) extend Phase A to allow late submissions, (c) manually enter missing budgets |
| **Can Fail** | No -- informational step |

### Step 4: Facilitator Triggers "Process Round"

| Property | Value |
|----------|-------|
| **Who** | Facilitator (moderator) |
| **UI** | Facilitator Dashboard > "Process Round" button (enabled only when Phase = B) |
| **C3 Endpoint** | `POST /moderator/engine/trigger` |
| **Request** | `{ "round_num": 3, "auto_publish": false }` |
| **What Happens** | Triggers Step 5 |
| **Can Fail** | Yes -- if round already processed, returns `409 Conflict` |

### Step 5: Edge Function Assembles Data, Calls F5

| Property | Value |
|----------|-------|
| **Who** | Edge Function (`trigger-engine`) |
| **Source Data** | DB: `country_state.budget`, `tariffs`, `sanctions`, `events` (Phase A), `world_state` |
| **Assembly** | Constructs `country_actions` object per country, `event_log` array |
| **F5 Endpoint** | `POST /engine/round/process` |
| **F5 Request** | See F5 Section 2.4 for full schema |
| **Timeout** | Returns `202 Accepted` immediately; engine processes async (up to 5 min) |
| **Can Fail** | Yes -- if engine unreachable, returns `503` to facilitator |

### Step 6: Engine Runs 14-Step World Model

| Property | Value |
|----------|-------|
| **Who** | Python Engine Server (WorldModelEngine) |
| **Processing** | Three-pass architecture: |
| | **Pass 1 (Deterministic, <1s):** 14 chained steps -- oil price, GDP, revenue, budget execution, military production, tech advancement, inflation, debt, economic state, momentum, contagion, stability, political support |
| | **Pass 2 (Expert Panel, <30s):** Three AI experts (KEYNES, CLAUSEWITZ, MACHIAVELLI) make heuristic adjustments. GDP adjustment capped at 30% per country. |
| | **Pass 3 (Coherence, <60s):** Auto-fixes HIGH severity contradictions. Generates round narrative (200-400 words). |
| **Elections** | If scheduled for this round (per C7 Time Structure), separate `POST /engine/election` call processes election results |
| **Output** | New world state, combat results, elections, narrative, expert panel, coherence flags |
| **Can Fail** | Yes -- `ENGINE_PROCESSING_FAILED` (500) or `ENGINE_TIMEOUT` (504) |

### Step 7: Results Returned to Edge Function

| Property | Value |
|----------|-------|
| **Who** | Engine Server -> Edge Function |
| **Response** | F5 Section 2.4 response schema: `new_world_state`, `combat_results`, `elections`, `narrative`, `expert_panel`, `coherence_flags`, `processing_metadata` |
| **Edge Function Action** | Stores results in temporary state (DB or in-memory) for facilitator review. Does NOT publish to participants yet. |
| **Channel** | `sim:{sim_run_id}:facilitator` -- sends `engine_status: processing_complete` |

### Step 8: Expert Panel Adjustments (Within Engine)

| Property | Value |
|----------|-------|
| **Who** | Engine (Pass 2) |
| **What** | Three AI domain experts review Pass 1 output and propose adjustments |
| **Constraints** | GDP adjustment capped at +/-30% per country. Each adjustment requires 2/3 expert votes. |
| **Output** | `expert_panel` object in response: per-expert assessments, synthesis of applied/rejected adjustments |
| **Facilitator Action** | Review in Step 10 |

### Step 9: Coherence Flags (Within Engine)

| Property | Value |
|----------|-------|
| **Who** | Engine (Pass 3) |
| **What** | Checks for logical contradictions (e.g., GDP growth during economic collapse) |
| **Severity Levels** | HIGH (auto-fixed if `auto_fix_coherence: true`), MEDIUM (flagged for review), LOW (informational) |
| **Output** | `coherence_flags` array in response |
| **Facilitator Action** | Review in Step 10 |

### Step 10: Facilitator Reviews Results

| Property | Value |
|----------|-------|
| **Who** | Facilitator (moderator) |
| **UI** | Facilitator Dashboard > Engine Results panel showing: |
| | - Per-country economic changes (GDP, treasury, inflation, debt) |
| | - Per-country military changes (production, losses) |
| | - Per-country political changes (stability, support) |
| | - Expert panel assessments (expandable per expert) |
| | - Coherence flags (highlighted by severity) |
| | - Round narrative preview |
| | - Election results (if any) |
| **C3 Endpoint** | `GET /moderator/expert-panel/{round_num}` (for detailed panel data) |
| **Decision Point** | Facilitator can: (a) approve and publish as-is, (b) apply overrides (Step 11), (c) re-run engine with different options |
| **Can Fail** | No -- review step |

### Step 11: Facilitator Overrides (Optional)

| Property | Value |
|----------|-------|
| **Who** | Facilitator (moderator) |
| **UI** | Click any value in results panel > Override dialog > Enter new value + reason |
| **C3 Endpoint** | `POST /moderator/override` |
| **Request** | `{ "idempotency_key": "...", "overrides": [{ "path": "countries.persia.economic.gdp_growth_rate", "new_value": -0.02, "reason": "..." }] }` |
| **What Happens** | Override applied to staged results. Logged as `system.moderator_override` event (MODERATOR visibility). |
| **Can Fail** | Yes -- if path invalid, returns `422` |

### Step 12: Facilitator Clicks "Publish"

| Property | Value |
|----------|-------|
| **Who** | Facilitator (moderator) |
| **UI** | Facilitator Dashboard > "Publish Results" button |
| **C3 Endpoint** | `POST /moderator/engine/publish` |
| **Request** | `{ "round_num": 3, "adjustments": [...], "idempotency_key": "publish_round3_v1" }` |
| **What Happens** | Triggers Steps 13-16 |
| **Can Fail** | Yes -- if already published, returns `409 Conflict` |

### Step 13: Edge Function Calls F5 /engine/round/publish

| Property | Value |
|----------|-------|
| **Who** | Edge Function (`publish-results`) |
| **F5 Endpoint** | `POST /engine/round/publish` |
| **Request** | `{ "sim_run_id": "...", "round_num": 3, "approved_state": "full" or "with_overrides", "overrides": [...] }` |
| **What Happens** | Engine finalizes state, applies any remaining overrides |
| **Can Fail** | Yes -- engine error |

### Step 14: Results Written to DB, Events Logged

| Property | Value |
|----------|-------|
| **Who** | Engine Server -> Supabase REST API |
| **DB Changes** | |
| | `world_state` -- INSERT new row for round N+1 with updated global values |
| | `country_state` -- INSERT per country for round N+1 with updated values |
| | `role_state` -- INSERT per role for round N+1 with updated pools/status |
| | `events` -- INSERT: `engine.round_end` (PUBLIC), `engine.world_update` (MODERATOR), `engine.country_update` per country (COUNTRY), `engine.production_complete` per country (COUNTRY), `engine.tech_advance` if any (PUBLIC), `engine.election_result` if any (PUBLIC) |
| | `combat_results` -- INSERT any combat records from this round |
| | `sim_runs.current_round` -- Incremented to N+1 |
| **Snapshot Frozen** | Current round's `world_state`, `country_state`, `role_state` rows set `is_frozen = TRUE` |
| **Can Fail** | Yes -- DB write failure. Engine retries once. On second failure, facilitator alerted. |

### Step 15: Real-Time Broadcast to All Channels

| Property | Value |
|----------|-------|
| **Who** | Edge Function (post-publish) |
| **Channels Broadcast** | |
| | `sim:{sim_run_id}:world` -- oil price change, chokepoint changes, public events, round narrative |
| | `sim:{sim_run_id}:country:{country_id}` (x21) -- per-country economic/military/political/tech updates |
| | `sim:{sim_run_id}:phase` -- `system.phase_change` to next round |
| | `sim:{sim_run_id}:alerts` -- significant events (election result, tech breakthrough, war outcomes) |
| | `sim:{sim_run_id}:facilitator` -- engine status, full diagnostics |
| **Event Types** | `engine.round_end`, `engine.country_update`, `engine.production_complete`, `engine.tech_advance`, `engine.election_result`, `system.phase_change` |

### Step 16: Participants See New World State

| Property | Value |
|----------|-------|
| **Who** | All participants (via React frontend) |
| **UI Updates** | |
| | Country dashboard: new GDP, treasury, inflation, military counts, stability, support |
| | World map: zone ownership changes, new unit positions, chokepoint status |
| | News feed: round narrative, combat outcomes, election results, announcements |
| | Global dashboard: Columbia vs Cathay GDP bars, oil price, naval comparison, active wars, election countdown, nuclear threat level |
| | Public display (room screens): global map, key indicators, news ticker, round clock |
| **Zustand Stores** | `worldStateStore`, `roleStore`, `eventStore`, `timerStore`, `mapStore` all update |

### Step 17: Next Round Begins

| Property | Value |
|----------|-------|
| **Who** | Facilitator triggers |
| **C3 Endpoint** | `POST /moderator/round/advance { "action": "start_phase_a" }` |
| **What Happens** | Phase set to `A`. Timer starts (default 60 minutes). `engine.round_start` event broadcast. |
| **Channel** | `sim:{sim_run_id}:phase` -- `system.phase_change` to new round Phase A |
| **DB Change** | `sim_runs.current_phase = 'A'`. New `world_state` row's `phase_a_start` set. |

---

# TIMING SUMMARY

| Step | Duration | Who Waits |
|------|----------|-----------|
| Steps 1-3 (End Phase A + review) | 2-5 minutes | Participants see "Phase B -- Processing" |
| Steps 4-9 (Engine processing) | 30 seconds - 5 minutes | Facilitator sees progress bar |
| Steps 10-11 (Facilitator review + overrides) | 2-10 minutes | Participants see "Results pending" |
| Steps 12-16 (Publish + broadcast) | 5-15 seconds | Near-instant for participants |
| Step 17 (Start next round) | Immediate | Timer begins |

**Total between-round gap:** 5-20 minutes typical. Facilitator controls the pace.

---

# ERROR RECOVERY

| Failure Point | Recovery |
|---------------|----------|
| Engine unreachable (Step 5) | Retry once. If still down, facilitator sees "Engine unavailable" with option to retry. Participants not affected (still in Phase A hold). |
| Engine processing fails (Step 6) | Facilitator sees error details. Can re-trigger with `auto_fix_coherence: false` to skip Pass 3, or manually adjust and re-trigger. |
| DB write fails (Step 14) | Engine retries once. On second failure, facilitator alerted. State is not published. Can retry publish. |
| Broadcast fails (Step 15) | Participants reconnect and receive full state refresh (via client reconnection protocol, C1 Section 2.4). |
| Facilitator disconnects mid-review | State persists in DB. Any facilitator can resume from where it was left. |

---

*This document specifies the complete round-end workflow. Each step references the specific C3 endpoint, F5 route, DB operation, and Realtime channel involved. For endpoint details, see C3 and F5. For event schemas, see C1.*
