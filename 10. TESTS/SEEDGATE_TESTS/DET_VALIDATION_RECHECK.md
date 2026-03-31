# DET_VALIDATION_RECHECK.md
## Re-Validation of Detailed Design Documents (Post-Fix)
**Date:** 2026-03-30 | **Validator:** VERA (via Claude Opus 4.6)
**Scope:** All 9 DET documents (including 3 NEW: NAMING_CONVENTIONS, EDGE_FUNCTIONS, ROUND_WORKFLOW)
**Previous validation:** DET_VALIDATION_LEVEL1.md, DET_VALIDATION_LEVEL3.md (23 issues, 5 HIGH)

---

## PREVIOUSLY FAILED -- RECHECK

### PF1: Transaction Type Enum (was HIGH)
**Verdict: FIXED**

C3 `TransactionProposal.transaction_type` enum (line 533) now lists all 9 canonical types:
`coin_transfer, arms_transfer, tech_transfer, basing_rights, treaty, agreement, org_creation, personal_investment, bribe`

This matches F5 Section 2.2 supported types and B1 `transactions.transaction_type` CHECK constraint (line 521-522). NAMING_CONVENTIONS Section 1.2 lists the same 9 types with deprecated name mapping.

No remaining discrepancy.

---

### PF2: Troop Deployment Validation Endpoint (was HIGH)
**Verdict: FIXED (with NEW ISSUES -- see below)**

The deployment path now exists end-to-end:
- C3: `POST /deploy/{round}/{country_id}` (line 1087)
- Edge Function: `submit-deployment` (#2 in inventory, line 44)
- B1: `deployment_validation()` function (line 1529, 120 lines of PL/pgSQL)
- NAMING_CONVENTIONS Section 0: Canonical deployment rules

The `deployment_validation()` function correctly implements:
- Ship capacity: 1 ground + 2 air (lines 1592-1598) -- MATCHES NAMING_CONVENTIONS
- Strategic missiles cannot embark (line 1576) -- MATCHES
- Naval cannot deploy into blockaded area (lines 1611-1619) -- MATCHES
- No adjacency check for deployment (comment line 1527) -- MATCHES

**However, 3 NEW ISSUES found:**

**N-PF2a (MEDIUM):** `deployment_validation()` references `ws.blockaded_zones` (line 1614) but `world_state` table has column `active_blockades`, not `blockaded_zones`. The function will fail at runtime.

**N-PF2b (MEDIUM):** `deployment_validation()` references `v_to_zone_rec.controlled_by` (line 1643) but `zones` table has no `controlled_by` column. Only `owner` exists. The function will fail for occupied territory checks.

**N-PF2c (MEDIUM):** Edge Function `submit-deployment` spec (EDGE_FUNCTIONS line 224) says "Zone adjacency check (via `zone_adjacency` table)" and "Transit time calculation (domestic = 0, cross-theater = 1 round)" -- but NAMING_CONVENTIONS Section 0 explicitly says "No transit delay" and "No adjacency requirement" for deployment. The Edge Function description contradicts the canonical rules AND the B1 function (which has no adjacency check). C3 deployment description (line 1094) also says "Long-distance redeployment to foreign theater takes 1 round transit" which contradicts NAMING_CONVENTIONS.

---

### PF3: Impeachment Path (was HIGH)
**Verdict: FIXED**

Complete end-to-end path now exists:
- NAMING_CONVENTIONS 1.3: action #25, `impeachment` -> `action.impeachment` -> `POST /actions/{round_num}/{country_id}` -> `POST /engine/action` -> `LiveActionEngine.resolve_impeachment()`
- C3: Listed in political action enum (line 474): `[impeachment, propaganda, arrest, fire_role, coup_attempt, assassination]`
- F5: Listed in supported action types table (line 172): `impeachment | {target_role_id} | {parliament_votes: {for: int, against: int}} | LiveActionEngine.resolve_impeachment() | action.impeachment`
- C1: Full event schema at line 654 with parliament_votes structure, result with succession logic
- B1: `check_authorization` updated to include impeachment (per changelog line 1691)

No remaining discrepancy.

---

### PF4: `round` vs `round_num` Standardization (was HIGH)
**Verdict: STILL BROKEN -- 4 remaining inconsistencies**

NAMING_CONVENTIONS Section 1.1 declares `round_num` as canonical. B1 uses `round_num` consistently in all column names. C1 event envelope uses `round_num` (line 41). NAMING_CONVENTIONS 1.8 says path parameter should be `round_num`.

**Remaining violations:**

**PF4a (HIGH): C3 path parameter is `round`, not `round_num`.** The `roundParam` component (line 752) declares `name: round`. All C3 paths use `{round}`:
- `/state/{round}/{country_id}` (line 852)
- `/map/{round}` (line 882)
- `/events/{round}` (line 907)
- `/actions/{round}/{country_id}` (line 1014)
- `/deploy/{round}/{country_id}` (line 1087)
- `/moderator/state/{round}` (line 1251)
- `/moderator/expert-panel/{round}` (line 1346)

NAMING_CONVENTIONS 1.8 explicitly says "Round number | `round_num` | integer (0-8) | `/actions/3/columbia`" -- implying the parameter should be `round_num` in paths. C3 uses `round`. Edge Function doc references `{round_num}` in the endpoint column (line 43: `POST /actions/{round_num}/{country_id}`). This is a direct contradiction.

**PF4b (HIGH): F5 request bodies use `round`, not `round_num`.** All F5 request examples use `"round": 3`:
- POST /engine/action (line 119)
- POST /engine/transaction (line 266)
- POST /engine/round/process (line 468)
- POST /engine/election (line 860)
- POST /engine/round/publish (line 945)
- POST /engine/ai/deliberate (line 706)
- GET /engine/state query param (line 649)

The F5 response for round/process correctly uses `"round_num": 3` (line 527), creating an inconsistency between request and response within the same endpoint.

**PF4c (MEDIUM): C3 response bodies use `round`, not `round_num`.** Several response schemas include `round: integer`:
- CountryState requires `round` (line 196-198)
- Action submission response has `round` (line 1047)
- Events response has `round` (line 947)
- MapState requires `round` (line 239)

**PF4d (MEDIUM): C1 event payload examples use `round` in some places.** Several C1 examples use `"round": 3` inside payloads (lines 814, 833, 857, 875, etc.) while the envelope correctly uses `round_num`.

**Summary:** The canonical name `round_num` is defined and used in B1 database columns, C1 event envelope, and NAMING_CONVENTIONS. But C3 paths, C3 response bodies, F5 request bodies, and C1 payload examples still use `round`. This is the single most pervasive remaining issue.

---

### PF5: Event ID Format (was HIGH)
**Verdict: FIXED**

All three documents agree:
- NAMING_CONVENTIONS 1.5: ULID with `evt_` prefix, `events.id TEXT PRIMARY KEY`
- B1: `events.id TEXT PRIMARY KEY` (line 488), comment confirms ULID format (line 488)
- C1: Event envelope uses `"event_id": "evt_<ulid>"` (line 18, field table line 38)

No remaining discrepancy on the specification. F5 response examples still use short IDs like `"evt_auto_001"` (line 196) which are not valid ULIDs, but these are clearly illustrative placeholders.

---

## NEW DOCUMENT CHECKS

### N1: NAMING_CONVENTIONS Completeness
**Verdict: FAIL -- 6 orphan fields**

Fields used in documents but NOT defined in NAMING_CONVENTIONS:

| Orphan Field | Found In | Issue |
|-------------|----------|-------|
| `actor` | F5 response events (lines 200, 213, etc.) | Should be `actor_role_id` per 1.1. F5 response examples use `"actor"` throughout. |
| `action_type` (in events) | F5 response events, C3 Event schema (line 285) | C1 event envelope uses `event_type` (dot-separated). F5/C3 events use `action_type`. These are NOT the same field but the naming dictionary does not clarify the distinction. |
| `controlled_by` | B1 deployment_validation (line 1643) | Column does not exist in zones table. Not in naming dictionary. |
| `blockaded_zones` | B1 deployment_validation (line 1614) | Column does not exist in world_state table. Not in naming dictionary. |
| `confirmation_token` | B1 transactions table, F5 response | Present in schema but not in naming dictionary. |
| `snapshot_version` | C1 event envelope (line 48) | Mentioned in C1 but not defined in naming dictionary with generation rules. |

---

### N2: EDGE_FUNCTIONS Coverage
**Verdict: PASS (with 1 minor gap)**

Every C3 API endpoint has a corresponding edge function:

| C3 Endpoint | Edge Function | Status |
|-------------|--------------|--------|
| `GET /state/{round}/{country_id}` | `read-state` (#11) | Covered |
| `GET /map/{round}` | `read-map` (#12) | Covered |
| `GET /events/{round}` | `read-events` (#13) | Covered |
| `GET /briefing/{round}` | -- | **MINOR GAP: No explicit edge function for briefing. Likely served by `read-state` or direct DB query, but not specified.** |
| `GET /role/{role_id}` | -- | **MINOR GAP: No explicit edge function. Likely direct DB query via Supabase client.** |
| `POST /actions/{round}/{country_id}` | `submit-actions` (#1) | Covered |
| `POST /deploy/{round}/{country_id}` | `submit-deployment` (#2) | Covered |
| `POST /transactions` | `propose-transaction` (#3) | Covered |
| `POST /transactions/{id}/confirm` | `confirm-transaction` (#4) | Covered |
| `POST /moderator/state/{round}` | `read-state` (#11, moderator mode) | Covered |
| `POST /moderator/override` | `moderator-override` (#8) | Covered |
| `GET /moderator/expert-panel/{round}` | -- | **MINOR GAP: No explicit edge function. Likely direct DB query.** |
| `POST /moderator/round/advance` | `advance-round` (#7) | Covered |
| `POST /moderator/engine/trigger` | `trigger-engine` (#5) | Covered |
| `POST /moderator/engine/publish` | `publish-results` (#6) | Covered |
| `POST /ai/decision/{role_id}` | `ai-deliberate` (#9) | Covered |
| `POST /ai/argus` | `ai-argus` (#10) | Covered |
| `GET /ai/context/{role_id}` | -- | **MINOR GAP: No explicit edge function.** |
| `GET /messages/{channel_id}` | -- | **MINOR GAP: Likely direct Supabase query.** |

The minor gaps are read-only endpoints that can use direct Supabase client SDK queries (no engine routing needed). Not a blocking issue, but should be documented as intentionally excluded.

---

### N3: ROUND_WORKFLOW Completeness
**Verdict: PASS**

All 17 steps reference correct endpoints:

| Step | Endpoint Referenced | Exists in C3/F5 | Status |
|------|-------------------|-----------------|--------|
| 1 | `POST /moderator/round/advance` | C3 line 1373 | OK |
| 3 | `GET /moderator/state/{round_num}` | C3 line 1251 | OK |
| 4 | `POST /moderator/engine/trigger` | C3 line 1419 | OK |
| 5 | F5 `POST /engine/round/process` | F5 Section 2.4 | OK |
| 10 | `GET /moderator/expert-panel/{round_num}` | C3 line 1346 | OK |
| 11 | `POST /moderator/override` | C3 line 1304 | OK |
| 12 | `POST /moderator/engine/publish` | C3 line 1471 | OK |
| 13 | F5 `POST /engine/round/publish` | F5 Section 2.9 | OK |
| 17 | `POST /moderator/round/advance` | C3 line 1373 | OK |

Steps 2, 6-9, 14-16 are internal processing steps (DB operations, engine internals, Realtime broadcasts). All reference correct DB tables and channel naming patterns consistent with C1 Part 2.

The workflow document is well-structured and correctly maps to the endpoints.

---

### N4: Deployment Rules Consistency
**Verdict: FAIL -- 3 contradictions (see PF2 NEW ISSUES)**

| Rule | NAMING_CONVENTIONS Section 0 | B1 deployment_validation() | Edge Function spec | C3 description |
|------|------------------------------|---------------------------|-------------------|----------------|
| Ship capacity: 1 ground + 2 air | Yes | Yes (lines 1592-1598) | Not specified | Not specified |
| No transit delay | Yes ("No transit delay") | Yes (no transit logic) | **NO: says "Transit time calculation (domestic = 0, cross-theater = 1 round)"** | **NO: says "Long-distance redeployment to foreign theater takes 1 round transit"** |
| Blockade restriction for naval | Yes | Yes (lines 1611-1619) but references wrong column `blockaded_zones` | Not specified | Not specified |
| Strategic missiles cannot embark | Yes | Yes (line 1576) | Not specified | Not specified |
| No adjacency requirement | Yes ("No adjacency requirement") | Yes (no adjacency check) | **NO: says "Zone adjacency check (via zone_adjacency table)"** | Not specified |

The B1 function itself is correct (no adjacency, no transit), but the Edge Function description and C3 description contradict the canonical rules. Also, B1 references two nonexistent columns.

---

### N5: Cross-Document Action Coverage Matrix (31 Actions)
**Verdict: FAIL -- 8 gaps**

| # | Action Type | NAMING_CONV 1.3 | C1 Event | C3 API | F5 Engine | B1 Storage | Status |
|---|------------|:---:|:---:|:---:|:---:|:---:|--------|
| 1 | `budget_submit` | Y | Y | Y (batch) | Y (batch) | Y (country_state.budget) | OK |
| 2 | `opec_production_set` | Y | Y | Y (batch) | Y (batch) | Y (country_state) | OK |
| 3 | `tariff_set` | Y | Y | Y (batch) | Y (batch) | Y (tariffs table) | OK |
| 4 | `sanction_set` | Y | Y | Y (batch) | Y (batch) | Y (sanctions table) | OK |
| 5 | `mobilization_order` | Y | Y | Y (batch) | Y | Y (events) | OK |
| 6 | `militia_call` | Y | Y | Y (batch) | Y | Y (events) | OK |
| 7 | `ground_attack` | Y | Y | Y | Y | Y (combat_results) | OK |
| 8 | `blockade` | Y | Y | Y | Y | Y (combat_results) | OK |
| 9 | `naval_combat` | Y | Y | Y | Y | Y (combat_results) | OK |
| 10 | `naval_bombardment` | Y | Y | Y | Y | Y (combat_results) | OK |
| 11 | `air_strike` | Y | Y | Y | Y | Y (combat_results) | OK |
| 12 | `strategic_missile` | Y | Y | Y | Y | Y (combat_results) | OK |
| 13 | `troop_deployment` | Y | Y | Y (separate endpoint) | Y (DB function) | Y (deployments table) | OK |
| 14 | `intelligence_request` | Y | Y | Y | Y | Y (events) | OK |
| 15 | `sabotage` | Y | Y | Y | Y | Y (events) | OK |
| 16 | `cyber_attack` | Y | Y | Y | Y | Y (events) | OK |
| 17 | `disinformation` | Y | Y | Y | Y | Y (events) | OK |
| 18 | `election_meddling` | Y | Y | Y | Y | Y (events) | OK |
| 19 | `arrest` | Y | Y | Y | Y | Y (events) | OK |
| 20 | `fire_role` | Y | Y | Y | Y | Y (events) | OK |
| 21 | `propaganda` | Y | Y | Y | Y | Y (events) | OK |
| 22 | `assassination` | Y | Y | Y | Y | Y (events) | OK |
| 23 | `coup_attempt` | Y | Y | Y | Y | Y (events) | OK |
| 24 | `protest` | Y | Y | **GAP: not in C3** | Y (engine-internal) | Y (events) | **Note: engine-generated, no API needed. Acceptable.** |
| 25 | `impeachment` | Y | Y | Y | Y | Y (events) | OK |
| 26 | `transaction_propose` | Y | Y | Y | Y | Y (transactions table) | OK |
| 26b | `transaction_confirm` | Y | Y | Y | Y | Y (transactions table) | OK |
| 27 | `agreement_sign` | Y | Y | Y (via transactions) | Y (via transactions) | Y (transactions table) | OK |
| 28 | `org_creation` | Y | Y | Y (via transactions) | Y (via transactions) | Y (transactions + organizations) | OK |
| 29 | `public_statement` | Y | Y | Y | **GAP: no engine route** | Y (events) | **Note: NAMING_CONV says "No engine processing / Direct event write". Acceptable.** |
| 30 | `meeting_call` | Y | Y | Y | **GAP: no engine route** | Y (events) | **Note: "No engine processing / Direct event write". Acceptable.** |
| 31 | `election_nominate` | Y | Y | Y | **GAP: no engine route** | Y (events) | **Note: "No engine processing / Direct event write". Acceptable.** |

**Gaps that ARE issues:**

| # | Issue | Severity |
|---|-------|----------|
| G1 | `nuclear_strike` appears in C1 event index (line 1310) and C3 military enum (line 456) but is NOT in the NAMING_CONVENTIONS 1.3 table as a separate action (only `strategic_missile` with `nuclear: bool`). C1 has a full `action.nuclear_strike` event schema. NAMING_CONVENTIONS, F5, and C1 disagree on whether nuclear is a separate action type. | **MEDIUM** |
| G2 | F5 response events use non-canonical field names: `actor` (should be `actor_role_id`), `action_type` (F5 uses engine-internal names like `attack`, `combat_losses`, `transaction_proposed` which differ from C1 canonical `event_type` names). | **HIGH** |
| G3 | F5 response events include types not in C1 vocabulary: `combat_losses`, `transaction_proposed`, `transaction_executed`, `transaction_rejected`, `gdp_update`, `round_narrative`, `round_published`. These are F5-internal event names that do not appear in C1 Section 1.7 event index. | **HIGH** |
| G4 | C3 military action enum uses `attack` (line 456) while canonical is `ground_attack`. Edge Function translation table (EDGE_FUNCTIONS line 209) maps `"attack"` -> `"ground_attack"`, but this means C3 intentionally uses a non-canonical name. | **LOW** |

---

## END-TO-END RE-TRACES

### Trace 1: Ground Attack
**Verdict: MOSTLY INTACT -- 2 issues in F5 response format**

| Step | Component | Status | Detail |
|------|-----------|--------|--------|
| UI submits | Frontend | OK | ActionSubmission with military[].action_type = "attack" |
| API receives | C3 `POST /actions/{round}/{country_id}` | OK | Endpoint exists (line 1014) |
| Edge Function | `submit-actions` | OK | Translates "attack" -> "ground_attack" (EDGE_FUNCTIONS line 209) |
| Permission check | Edge Function + DB `check_authorization` | OK | Checks role powers |
| Forward to engine | F5 `POST /engine/action` | OK | With `action_type: "ground_attack"` |
| Engine resolves | `LiveActionEngine.resolve_attack()` | OK | Listed in F5 Section 2.1 table |
| State change | F5 response `state_changes[]` | OK | Zone ownership, unit counts, war_tiredness |
| Event created | F5 response `events[]` | **ISSUE:** Uses `"actor": "dealer"`, `"action_type": "attack"` instead of `"actor_role_id": "dealer"`, `"event_type": "action.ground_attack"` | Non-canonical field names in F5 response events |
| DB write | B1 `events` table | OK | Columns are `actor_role_id`, `action_type` (stores canonical name) |
| Realtime | C1 channels per visibility | OK | PUBLIC -> `sim:{id}:world` channel |
| RLS | B1 RLS policies | OK | Visibility-based filtering |
| UI update | Frontend via Realtime subscription | OK | worldStateStore + mapStore + eventStore |

**Issues:** F5 response event format does not match C1 envelope. The Edge Function must translate F5 event objects to C1 format before writing to DB and broadcasting. This translation is implied but not explicitly specified in EDGE_FUNCTIONS.

---

### Trace 2: Bilateral Transaction
**Verdict: INTACT**

| Step | Component | Status | Detail |
|------|-----------|--------|--------|
| Propose | C3 `POST /transactions` | OK | TransactionProposal with canonical types |
| Edge Function | `propose-transaction` | OK | Field translation C3 -> F5 specified (EDGE_FUNCTIONS 4.3) |
| Engine validates | F5 `POST /engine/transaction` | OK | Treasury check, proposal created |
| Pending state | B1 `transactions` table | OK | status = 'pending' |
| Notify counterparty | Edge Function publishes to role channel | OK | `sim:{id}:role:{receiver_role_id}` |
| Confirm | C3 `POST /transactions/{id}/confirm` | OK | TransactionConfirmation schema |
| Edge Function | `confirm-transaction` | OK | Forwards to F5 |
| Engine executes | F5 `POST /engine/transaction/{id}/confirm` | OK | Re-validates, executes |
| State change | Treasury/units modified | OK | state_changes[] in response |
| DB write | B1 `transactions` table + `events` table | OK | status = 'executed', event logged |
| Broadcast | Per visibility rules | OK | country channel for executed transfers |

The two-phase transaction flow is complete and well-specified.

---

### Trace 3: Round-End Processing (17-Step Workflow)
**Verdict: INTACT (aligns with ROUND_WORKFLOW)**

| Step | ROUND_WORKFLOW | C3/F5 Endpoint | Status |
|------|---------------|----------------|--------|
| 1: End Phase A | Step 1 | `POST /moderator/round/advance` (C3 line 1373) | OK |
| 2: Collect submissions | Step 2 | Automatic (DB queries in `trigger-engine`) | OK |
| 3: Review | Step 3 | `GET /moderator/state/{round}` (C3 line 1251) | OK |
| 4: Trigger engine | Step 4 | `POST /moderator/engine/trigger` (C3 line 1419) | OK |
| 5: Assemble + call F5 | Step 5 | F5 `POST /engine/round/process` (F5 Section 2.4) | OK |
| 6: Engine processes | Step 6 | WorldModelEngine.process_round() | OK |
| 7: Results return | Step 7 | F5 response schema | OK |
| 8: Expert panel | Step 8 | Within engine (Pass 2) | OK |
| 9: Coherence | Step 9 | Within engine (Pass 3) | OK |
| 10: Facilitator review | Step 10 | `GET /moderator/expert-panel/{round}` (C3 line 1346) | OK |
| 11: Overrides | Step 11 | `POST /moderator/override` (C3 line 1304) | OK |
| 12: Publish trigger | Step 12 | `POST /moderator/engine/publish` (C3 line 1471) | OK |
| 13: F5 finalize | Step 13 | F5 `POST /engine/round/publish` (F5 Section 2.9) | OK |
| 14: DB writes | Step 14 | world_state, country_state, role_state, events INSERTs | OK |
| 15: Broadcast | Step 15 | Per C1 Part 2 channel architecture | OK |
| 16: UI update | Step 16 | Zustand stores (per D1 Section 1.4) | OK |
| 17: Next round | Step 17 | `POST /moderator/round/advance` (C3 line 1373) | OK |

The ROUND_WORKFLOW document successfully bridges the gap that was identified in the previous validation. All 17 steps map to real endpoints.

---

## SUMMARY

### Previously Failed: 3/5 Fixed, 2/5 Still Broken

| Check | Previous Severity | Status | Remaining Issue |
|-------|:-:|--------|----------------|
| PF1: Transaction types | HIGH | **FIXED** | -- |
| PF2: Deployment validation | HIGH | **FIXED** (but 3 new medium issues) | B1 function references 2 nonexistent columns; Edge Function + C3 descriptions contradict canonical rules |
| PF3: Impeachment path | HIGH | **FIXED** | -- |
| PF4: `round` vs `round_num` | HIGH | **STILL BROKEN** | C3 paths, F5 requests, C3 responses, C1 examples all still use `round` |
| PF5: Event ID format | HIGH | **FIXED** | -- |

### New Document Checks: 2/5 Passed, 3/5 Failed

| Check | Status | Key Finding |
|-------|--------|-------------|
| N1: NAMING_CONVENTIONS completeness | **FAIL** | 6 orphan fields (actor, controlled_by, blockaded_zones, etc.) |
| N2: EDGE_FUNCTIONS coverage | **PASS** | All write endpoints covered; read-only gaps are acceptable |
| N3: ROUND_WORKFLOW completeness | **PASS** | All 17 steps map to correct endpoints |
| N4: Deployment rules consistency | **FAIL** | Edge Function + C3 descriptions contradict NAMING_CONVENTIONS (transit delay, adjacency) |
| N5: Action coverage matrix | **FAIL** | F5 response events use non-canonical names; nuclear_strike ambiguity; 7 F5-only event types not in C1 vocabulary |

### Traces: 2/3 Fully Intact, 1/3 Mostly Intact

| Trace | Status | Issue |
|-------|--------|-------|
| Trace 1: Ground Attack | **MOSTLY INTACT** | F5 response event format differs from C1 envelope (field names, event type naming) |
| Trace 2: Bilateral Transaction | **INTACT** | -- |
| Trace 3: Round-End Processing | **INTACT** | Aligns with new ROUND_WORKFLOW doc |

---

## ALL REMAINING ISSUES (Ranked by Severity)

| # | Severity | Issue | Documents Affected | Fix Required |
|---|:--------:|-------|-------------------|-------------|
| R1 | **HIGH** | `round` vs `round_num`: C3 paths use `{round}`, F5 requests use `"round"`, while canonical is `round_num` | C3, F5, C1 examples | Rename C3 `roundParam` to `round_num`. Update all F5 request schemas. Update C3 response schemas. Update C1 examples. |
| R2 | **HIGH** | F5 response event objects use non-canonical fields: `actor` (should be `actor_role_id`), `action_type` with engine-internal names (e.g., `attack`, `combat_losses`, `transaction_proposed`) that differ from C1 `event_type` vocabulary | F5 | Standardize F5 response events to match C1 envelope format, OR explicitly specify the Edge Function translation layer that converts F5 events to C1 format |
| R3 | **HIGH** | 7 event types appear in F5 responses but not in C1 Section 1.7 vocabulary: `combat_losses`, `transaction_proposed`, `transaction_executed`, `transaction_rejected`, `gdp_update`, `round_narrative`, `round_published` | F5, C1 | Add to C1 vocabulary OR replace with existing canonical names |
| R4 | **MEDIUM** | B1 `deployment_validation()` references nonexistent column `ws.blockaded_zones` -- should be `ws.active_blockades` | B1 | Fix column reference |
| R5 | **MEDIUM** | B1 `deployment_validation()` references nonexistent column `v_to_zone_rec.controlled_by` -- zones table only has `owner` | B1 | Add `controlled_by` column to zones table OR rewrite check to use deployments-based control logic |
| R6 | **MEDIUM** | Edge Function `submit-deployment` description says "Zone adjacency check" and "Transit time calculation (cross-theater = 1 round)" -- contradicts NAMING_CONVENTIONS Section 0 which says "No transit delay" and "No adjacency requirement" | EDGE_FUNCTIONS, C3, NAMING_CONVENTIONS | Align Edge Function description and C3 description with NAMING_CONVENTIONS canonical rules |
| R7 | **MEDIUM** | `nuclear_strike` appears as separate event type in C1 (line 1310, full payload at line 320) and C3 military enum (line 456) but is NOT in NAMING_CONVENTIONS 1.3 action list (only `strategic_missile` with `nuclear: bool` parameter) | NAMING_CONVENTIONS, C1, C3 | Decide: is nuclear_strike a separate action_type or a parameter of strategic_missile? Add to NAMING_CONVENTIONS if separate. |
| R8 | **LOW** | C3 military action enum uses `attack` instead of canonical `ground_attack` (Edge Function handles translation, but C3 deviates from canonical naming) | C3 | Consider using canonical name `ground_attack` in C3 enum for consistency, or document the C3-specific alias in NAMING_CONVENTIONS |
| R9 | **LOW** | 4 C3 read endpoints (briefing, role, expert-panel, ai/context) have no explicit Edge Function specification -- assumed to use direct Supabase client queries | EDGE_FUNCTIONS | Add a note to EDGE_FUNCTIONS explaining which C3 endpoints are served directly by Supabase client SDK |

**Total: 3 HIGH, 4 MEDIUM, 2 LOW**

---

## VERDICT: NEEDS FIXES

The three new documents (NAMING_CONVENTIONS, EDGE_FUNCTIONS, ROUND_WORKFLOW) significantly improve the design. The ROUND_WORKFLOW closes the major gap from the previous trace. NAMING_CONVENTIONS provides the authoritative reference that was missing. EDGE_FUNCTIONS bridges the C3-to-F5 gap.

However, the documents have not yet been fully harmonized with each other. The `round`/`round_num` inconsistency (R1) is the most pervasive and should be fixed first -- it touches nearly every endpoint. The F5 response event format (R2, R3) creates ambiguity in the event pipeline that will cause implementation confusion. The deployment function column references (R4, R5) will cause runtime failures.

**Recommended fix priority:**
1. R1 -- Standardize `round_num` across C3 paths, F5 requests, C3 responses
2. R4 + R5 -- Fix B1 deployment_validation() column references
3. R6 -- Align deployment descriptions (remove transit/adjacency from Edge Function and C3)
4. R2 + R3 -- Standardize F5 response event format to match C1 envelope
5. R7 -- Decide nuclear_strike action type status

After these fixes, the design should be ready for build.
