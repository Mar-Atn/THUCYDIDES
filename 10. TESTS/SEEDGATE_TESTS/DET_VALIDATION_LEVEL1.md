# DET_VALIDATION_LEVEL1.md
## Detailed Design Cross-Reference Integrity Check
**Date:** 2026-03-30 | **Validator:** VERA (automated) | **Status:** COMPLETE

**Documents Validated:**
- B1: `DET_B1_DATABASE_SCHEMA.sql` (25 tables + RLS + functions)
- B3: `DET_B3_SEED_DATA.sql` (seed INSERT statements)
- C1: `DET_C1_SYSTEM_CONTRACTS.md` (event schemas + channels + module contracts)
- C3: `DET_C3_API_SPEC.yaml` (OpenAPI spec, 17+ endpoints)
- D1: `DET_D1_TECH_STACK.md` (technology stack)
- F5: `DET_F5_ENGINE_API.md` (engine API wrapper, 10 endpoints)
- G:  `SEED_G_WEB_APP_SPEC_v1.md` (31 action types)

---

## CHECK 1: Schema <> API Coverage
### Status: PASS
### Details:
Every C3 API endpoint reads from or writes to tables that exist in B1.

**Endpoint-to-table mapping verified:**

| C3 Endpoint | B1 Tables Used | Match |
|---|---|---|
| `GET /state/{round}/{country_id}` | `country_state` | OK |
| `GET /map/{round}` | `zones`, `deployments`, `world_state`, `combat_results` | OK |
| `GET /events/{round}` | `events` | OK |
| `GET /briefing/{round}` | `world_state` (narrative field) | OK |
| `GET /role/{role_id}` | `roles`, `role_state`, `artefacts` | OK |
| `POST /actions/{round}/{country_id}` | `events`, `country_state`, `sanctions`, `tariffs`, `deployments` | OK |
| `POST /deploy/{round}/{country_id}` | `deployments`, `events` | OK |
| `POST /transactions` | `transactions`, `events` | OK |
| `POST /transactions/{id}/confirm` | `transactions`, `events`, `country_state` | OK |
| `GET /moderator/state/{round}` | `world_state`, `country_state`, all tables | OK |
| `POST /moderator/override` | `world_state`, `country_state`, `events` | OK |
| `GET /moderator/expert-panel/{round}` | `world_state` (expert_panel JSONB) | OK |
| `POST /moderator/round/advance` | `sim_runs`, `events` | OK |
| `POST /moderator/engine/trigger` | Proxies to F5 engine | OK |
| `POST /moderator/engine/publish` | `world_state`, `country_state`, `events` | OK |
| `GET /ai/context/{role_id}` | `roles`, `role_state`, `country_state`, `ai_contexts` | OK |
| `POST /ai/decision/{role_id}` | `ai_decisions`, `events` | OK |
| `POST /ai/argus` | `events` (ai.argus_conversation) | OK |
| `GET /messages/{channel_id}` | `messages` | OK |

**Field-level spot checks:**
- C3 `CountryState` schema fields (`gdp`, `treasury`, `inflation`, `debt_burden`, `economic_state`, `momentum`, `market_index`, `revenue_last_round`) all map to columns in `country_state` table. OK.
- C3 `MilitaryState` fields (`ground`, `naval`, `tactical_air`, `strategic_missiles`, `air_defense`) map to `mil_ground`, `mil_naval`, `mil_tactical_air`, `mil_strategic_missiles`, `mil_air_defense`. **Minor naming difference noted** (see CHECK 10).
- C3 `PoliticalState` fields map correctly to `country_state` columns. OK.
- C3 `TechnologyState` fields match exactly. OK.

### Issues Found:
- **[LOW]** C3 field `revenue_last_round` maps to `revenue` in `country_state`. Name is close but not identical; the API adds `_last_round` suffix for clarity. Acceptable as an API presentation concern, not a schema mismatch.
- **[LOW]** C3 `MilitaryState` uses `strategic_missiles` (plural) while B1 uses `mil_strategic_missiles` (prefixed). Consistent within their respective contexts but requires mapping layer.

---

## CHECK 2: Schema <> Events Coverage
### Status: PASS
### Details:
All event types defined in C1 Section 1.7 have storage in the `events` table (B1 Section 3.1). The `events` table uses a generic schema with `action_type` (TEXT), `details` (JSONB), and `result` (JSONB) columns, which can store any event payload.

**Storage targets per event category:**

| Category | Event Types | Storage Table | Additional Table |
|---|---|---|---|
| Action: Regular | 6 types | `events` | `sanctions`, `tariffs` (for state changes) |
| Action: Military | 7 types | `events` | `combat_results` (for combat detail), `deployments` |
| Action: Covert | 4 types | `events` | None (JSONB details sufficient) |
| Action: Political | 7 types | `events` | `role_state` (for status changes) |
| Action: Transaction | 4 types | `events` | `transactions` (linked via `event_id` FK) |
| Action: Communication | 3 types | `events` | `messages`, `meetings` |
| Engine | 9 types | `events` | `world_state`, `country_state`, `combat_results` |
| System | 6 types | `events` | None (metadata only) |
| Comms | 3 types | `events` | `messages`, `meetings` |
| AI | 3 types | `events` | `ai_decisions`, `ai_contexts` |

**All 52 event types from C1 Section 1.7 can be stored.** The generic `events` table with JSONB `details` and `result` columns accommodates all payloads.

### Issues Found:
- **[MEDIUM]** C1 event envelope uses `event_id` (string, ULID format like `evt_<ulid>`), but B1 `events` table uses `id` (UUID). These are different ID formats. The C1 spec says ULID for time-sortability, but the schema generates UUID v4. **This is a functional mismatch** -- ULIDs are time-sortable, UUIDs are not. The `timestamp` column + index provides time ordering, but cursor-based pagination expects ULID-style IDs per C1 Section 1.1.
- **[LOW]** C1 event envelope field `actor_role_id` maps to B1 column `actor` (TEXT). Name difference, but semantically identical.
- **[LOW]** C1 event envelope field `actor_country_id` maps to B1 column `country_context` (TEXT). Name difference.
- **[LOW]** C1 uses uppercase visibility (`"PUBLIC"`, `"COUNTRY"`, `"ROLE"`, `"MODERATOR"`) while B1 uses lowercase (`'public'`, `'country'`, `'role'`, `'moderator'`). Must normalize at API layer.

---

## CHECK 3: API <> Engine API Coverage
### Status: PARTIAL
### Details:
C3 endpoints that trigger engine processing and their F5 counterparts:

| C3 Endpoint | Triggers Engine? | F5 Route | Match |
|---|---|---|---|
| `POST /actions/{round}/{country_id}` (military actions) | Yes | `POST /engine/action` | PARTIAL |
| `POST /transactions` | Yes | `POST /engine/transaction` | PARTIAL |
| `POST /transactions/{id}/confirm` | Yes | `POST /engine/transaction/{id}/confirm` | OK |
| `POST /moderator/engine/trigger` | Yes | `POST /engine/round/process` | OK |
| `POST /moderator/engine/publish` | Yes | `POST /engine/round/publish` | OK |
| `GET /ai/context/{role_id}` | Indirectly | `GET /engine/state/{sim_run_id}` | OK (state fetch) |
| `POST /ai/decision/{role_id}` | Yes | `POST /engine/ai/deliberate` | PARTIAL |
| `POST /ai/argus` | Yes | `POST /engine/ai/argus` | OK |

**Mismatches:**

1. **C3 `POST /actions` vs F5 `POST /engine/action`**: C3 uses `ActionSubmission` schema with nested `actions` object containing `budget`, `tariffs`, `sanctions`, `military[]`, `diplomatic[]`. F5 expects flat `action_type`, `actor_role_id`, `target`, `parameters`. The C3 submission is a batch of multiple action types; F5 processes one action at a time. **The Edge Function must decompose** the C3 batch into individual F5 calls. This is an architectural pattern, not a bug, but it is not explicitly documented.

2. **C3 `TransactionProposal` vs F5 transaction request**: C3 uses `proposer` (role_id string), `counterparty` (role_id string), `details` object. F5 uses `proposer_role_id`, `proposer_country_id`, `receiver_role_id`, `receiver_country_id`, `terms` object. Field naming differs (`details` vs `terms`, `counterparty` vs `receiver_role_id`). Edge Function must map.

3. **C3 transaction types**: C3 defines `[transfer_coins, trade_deal, basing_rights, aid_package, personal_invest, bribe]`. F5 defines `[coin_transfer, arms_transfer, tech_transfer, basing_rights, treaty, agreement, organization_create, personal_investment, bribe]`. **Vocabulary mismatch**: `transfer_coins` vs `coin_transfer`, `trade_deal` vs `arms_transfer`/`tech_transfer` (C3 collapses these), `personal_invest` vs `personal_investment`.

### Issues Found:
- **[HIGH]** Transaction type vocabulary mismatch between C3 and F5. C3 has 6 types, F5 has 9 types. `arms_transfer`, `tech_transfer`, `treaty`, `agreement`, `organization_create` are in F5 but not in C3's `TransactionProposal.transaction_type` enum. Either C3 must expand its enum or F5 must accept the C3 vocabulary with decomposition logic.
- **[MEDIUM]** Field naming differences between C3 and F5 for transactions (`details` vs `terms`, `counterparty` vs `receiver_role_id`). Not blocking but needs a documented mapping.
- **[MEDIUM]** C3 batch action submission vs F5 single-action processing pattern is not documented as a design decision. The Edge Function decomposition logic must be specified.

---

## CHECK 4: Engine API <> Module Contracts
### Status: PARTIAL
### Details:
C1 Part 3 defines module interface contracts. Comparing with F5 routes:

| F5 Route | C1 Module Contract | I/O Match |
|---|---|---|
| `POST /engine/round/process` | C1 Section 3.1 World Model Engine `process_round(input) -> output` | OK -- input/output schemas align closely |
| `POST /engine/action` | C1 Section 3.2 (implied by Live Action Engine) | PARTIAL |
| `POST /engine/transaction` | C1 Section 3.3 (implied by Transaction Engine) | PARTIAL |
| `POST /engine/ai/deliberate` | C1 Section 3.4 (implied by AI Agent contract) | OK |
| `POST /engine/ai/argus` | No explicit module contract in C1 | MISSING |

**World Model Engine (process_round):**
- C1 Section 3.1 input schema includes `round_num`, `world_state`, `country_actions`, `event_log`. F5 Section 2.4 request includes `sim_run_id`, `round`, `country_actions`, `event_log`, `options`. Match is good.
- C1 output includes new world state with `countries`, `zones`, `bilateral`, `wars`, `oil_price`, etc. F5 response includes `new_world_state` with the same structure. OK.

**Live Action Engine:**
- C1 does not provide a separate formal module contract for the Live Action Engine (it's embedded in the event type definitions). F5 provides full route specification. The action types in F5 (`attack`, `blockade`, `naval_combat`, etc.) map to C1 event types (`action.ground_attack`, `action.blockade`, `action.naval_combat`), but naming differs (`attack` in F5 vs `ground_attack` in C1).

### Issues Found:
- **[MEDIUM]** F5 action type `attack` does not match C1 event type `action.ground_attack`. F5 uses short names (`attack`, `air_strike`); C1 uses full names (`action.ground_attack`, `action.air_strike`). Mapping required.
- **[LOW]** C1 does not include a formal module contract for Argus. F5 defines the Argus route fully, but the contract is only implied by C1's event type `ai.argus_conversation`.
- **[LOW]** C1 does not include a formal module contract for the Live Action Engine or Transaction Engine as separate sections -- they are implied by the event type definitions. F5 fills this gap.

---

## CHECK 5: RLS <> Channels Alignment
### Status: PASS
### Details:
Comparing C1 Part 2 channel subscriber rules with B1 Section 7 RLS policies:

| Channel | Subscriber Rule (C1) | RLS Policy (B1) | Aligned? |
|---|---|---|---|
| `sim:{id}:world` | All authenticated users | `world_state_read`: participants in sim + facilitator | YES |
| `sim:{id}:country:{country_id}` | Team members of country + moderator | `country_state_read_own`: facilitator OR country_id matches | YES |
| `sim:{id}:role:{role_id}` | Assigned user + moderator | `role_state_read_own`: facilitator OR role_id matches | YES |
| `sim:{id}:facilitator` | moderator/admin only | `ai_ctx_read`, `ai_dec_read`: facilitator only | YES |
| `sim:{id}:phase` | All authenticated | No specific RLS (broadcast) | OK (no DB table) |
| `sim:{id}:alerts` | All authenticated | No specific RLS (broadcast) | OK (no DB table) |
| `sim:{id}:chat:{channel_id}` | Channel members | `messages_read`: from/to role match, team channel match, public | YES |

**Events table RLS** (the critical one):
- B1 `events_read_public` policy: facilitator sees all; `public` visibility -> any participant; `country` visibility -> country match; `role` visibility -> actor match.
- C1 visibility rules: `PUBLIC` -> all, `COUNTRY` -> actor_country_id members + moderator, `ROLE` -> actor_role_id + moderator, `MODERATOR` -> moderator only.
- B1 events RLS for `role` visibility checks `events.actor = get_user_role_id()`. This means only the **actor** of a role-visibility event sees it, not any **target**. For intelligence results where the requester is the actor, this works. For transactions where the counterparty should also see it, the visibility is set to `country` anyway. **Alignment is correct.**

### Issues Found:
- **[LOW]** C1 channel `sim:{id}:phase` and `sim:{id}:alerts` are Supabase Broadcast channels (ephemeral, no DB storage). They have no corresponding RLS since they don't read from tables. This is correct by design.
- **[LOW]** Deployments RLS (`deployments_read`) allows all participants in the sim to read all deployments. This is broader than C1's map channel which filters by visibility/adjacency. The design note in B1 line 815 explains: "Fine-grained visibility enforced at API layer." Acceptable.

---

## CHECK 6: Actions Coverage (G spec -> full chain)
### Status: FAIL
### Details:
Tracing each of the 31 action types from G spec through the full chain:

| # | Action (G spec) | C1 Event Type | C3 API Endpoint | F5 Engine Route | B1 Storage | Chain Status |
|---|---|---|---|---|---|---|
| 1 | Budget allocation | `action.budget_submit` | `POST /actions/{round}/{country_id}` | `POST /engine/round/process` (batch) | `events`, `country_state` | OK |
| 2 | Oil production | `action.opec_production_set` | `POST /actions/{round}/{country_id}` | `POST /engine/round/process` (batch) | `events`, `world_state` | OK |
| 3 | Tariff settings | `action.tariff_set` | `POST /actions/{round}/{country_id}` | `POST /engine/round/process` (batch) | `events`, `tariffs` | OK |
| 4 | Sanctions | `action.sanction_set` | `POST /actions/{round}/{country_id}` | `POST /engine/round/process` (batch) | `events`, `sanctions` | OK |
| 5 | Mobilization | `action.mobilization_order` | `POST /actions/{round}/{country_id}` | `POST /engine/action` | `events`, `country_state` | OK |
| 6 | Militia call | `action.militia_call` | `POST /actions/{round}/{country_id}` | `POST /engine/action` | `events`, `deployments` | OK |
| 7 | Ground attack | `action.ground_attack` | `POST /actions/{round}/{country_id}` | `POST /engine/action` (type: `attack`) | `events`, `combat_results`, `deployments` | OK |
| 8 | Blockade | `action.blockade` | `POST /actions/{round}/{country_id}` | `POST /engine/action` (type: `blockade`) | `events`, `world_state` | OK |
| 9 | Naval combat | `action.naval_combat` | `POST /actions/{round}/{country_id}` | `POST /engine/action` (type: `naval_combat`) | `events`, `combat_results` | OK |
| 10 | Naval bombardment | `action.naval_bombardment` | `POST /actions/{round}/{country_id}` | `POST /engine/action` (type: `naval_bombardment`) | `events`, `combat_results` | OK |
| 11 | Air strike | `action.air_strike` | `POST /actions/{round}/{country_id}` | `POST /engine/action` (type: `air_strike`) | `events`, `combat_results` | OK |
| 12 | Strategic missile | `action.strategic_missile` | `POST /actions/{round}/{country_id}` | `POST /engine/action` (type: `strategic_missile`) | `events`, `combat_results` | OK |
| 13 | Troop deployment | `action.troop_deployment` | `POST /deploy/{round}/{country_id}` | Not in F5 | `events`, `deployments` | **BROKEN** |
| 14 | Intelligence | `action.intelligence_request` | `POST /actions/{round}/{country_id}` | `POST /engine/action` (type: `espionage`) | `events` | OK* |
| 15 | Sabotage | `action.sabotage` | `POST /actions/{round}/{country_id}` | `POST /engine/action` (type: `sabotage`) | `events` | OK |
| 16 | Cyber attack | `action.cyber_attack` | `POST /actions/{round}/{country_id}` | `POST /engine/action` (type: `cyber`) | `events` | OK |
| 17 | Disinformation | `action.disinformation` | `POST /actions/{round}/{country_id}` | `POST /engine/action` (type: `disinformation`) | `events` | OK |
| 18 | Election meddling | `action.election_meddling` | `POST /actions/{round}/{country_id}` | `POST /engine/action` (type: `election_meddling`) | `events` | OK |
| 19 | Arrest | `action.arrest` | `POST /actions/{round}/{country_id}` | `POST /engine/action` (type: `arrest`) | `events`, `role_state` | OK |
| 20 | Fire/reassign | `action.fire_role` | `POST /actions/{round}/{country_id}` | `POST /engine/action` (type: `fire_role`) | `events`, `role_state` | OK |
| 21 | Propaganda | `action.propaganda` | `POST /actions/{round}/{country_id}` | `POST /engine/action` (type: `propaganda`) | `events`, `country_state` | OK |
| 22 | Assassination | `action.assassination` | `POST /actions/{round}/{country_id}` | `POST /engine/action` (type: `assassination`) | `events`, `role_state` | OK |
| 23 | Coup attempt | `action.coup_attempt` | `POST /actions/{round}/{country_id}` | `POST /engine/action` (type: `coup_attempt`) | `events`, `role_state`, `country_state` | OK |
| 24 | Protest | `action.protest` | Engine-generated (automatic) | Engine internal | `events`, `country_state` | OK (not player-initiated) |
| 25 | Impeachment | `action.impeachment` | `POST /actions/{round}/{country_id}` | Not in F5 | `events`, `role_state` | **BROKEN** |
| 26 | Trade/transfer | `action.transaction_propose` + `action.transaction_confirm` | `POST /transactions` + `POST /transactions/{id}/confirm` | `POST /engine/transaction` + `POST /engine/transaction/{id}/confirm` | `events`, `transactions` | OK |
| 27 | Agreement | `action.agreement_sign` | `POST /transactions` (type: agreement) | `POST /engine/transaction` (type: `agreement`) | `events`, `transactions` | PARTIAL* |
| 28 | New organization | `action.organization_create` | `POST /transactions` (type: organization_create) | `POST /engine/transaction` (type: `organization_create`) | `events`, `organizations`, `org_memberships` | PARTIAL* |
| 29 | Public statement | `action.public_statement` | `POST /actions/{round}/{country_id}` (diplomatic) | Not engine-processed | `events` | OK (no engine needed) |
| 30 | Call meeting | `action.meeting_call` | `POST /actions/{round}/{country_id}` (diplomatic) | Not engine-processed | `events`, `meetings` | OK (no engine needed) |
| 31 | Election nominate | `action.election_nominate` | `POST /actions/{round}/{country_id}` (diplomatic) | Not engine-processed | `events` | OK (no engine needed) |

### Issues Found:
- **[HIGH]** Action #13 (Troop deployment): C3 has a dedicated `POST /deploy/{round}/{country_id}` endpoint, but F5 has **no corresponding engine route**. Deployment is handled directly by the Edge Function writing to the `deployments` table -- but this is not documented in F5 and the deployment validation logic (adjacency checks, transit time calculations) is not specified in any engine route. Either F5 needs a deployment validation route, or C3/C1 must document that deployment bypasses the engine.
- **[HIGH]** Action #25 (Impeachment): C1 defines `action.impeachment` event type. C3's `ActionSubmission` schema includes `diplomatic` actions but impeachment is not in the enum. F5 has no `impeachment` action type. **Full chain gap.**
- **[MEDIUM]** Action #14 (Intelligence): C1 event type is `action.intelligence_request` but F5 action type is `espionage`. Naming mismatch.
- **[MEDIUM]** Actions #27-28 (Agreement, Organization): These are in F5's transaction types but NOT in C3's `TransactionProposal.transaction_type` enum (which only lists `transfer_coins, trade_deal, basing_rights, aid_package, personal_invest, bribe`). Missing `treaty`, `agreement`, `organization_create` from C3 enum.
- **[LOW]** Action #24 (Protest): Engine-generated, not player-initiated. The `action.protest` event has a `stimulated_by_role_id` field allowing card-triggered protests, but there is no submit mechanism in C3. This may be intentional (moderator/engine handles it).

---

## CHECK 7: Seed Data <> Schema
### Status: PASS
### Details:
Verified all INSERT statements in B3 against B1 table definitions:

| B3 Section | Target Table | Table Exists? | Column Match | FK Valid? |
|---|---|---|---|---|
| 1. sim_runs | `sim_runs` | YES | YES (5 cols) | N/A |
| 2. countries (21 rows) | `countries` | YES | YES (all cols) | FK to sim_runs OK |
| 3. roles (37 rows) | `roles` | YES | YES (all cols) | FK to countries (composite) OK |
| 4. zones + adjacency | `zones`, `zone_adjacency` | YES | YES | FK to sim_runs OK |
| 5. organizations (9 rows) | `organizations` | YES | YES | FK to sim_runs OK |
| 6. org_memberships (61 rows) | `org_memberships` | YES | YES | FK to sim_runs OK |
| 7. relationships (100+ rows) | `relationships` | YES | YES | FK to sim_runs OK |
| 8. sanctions (37 rows) | `sanctions` | YES | YES | FK to sim_runs OK |
| 9. tariffs (30 rows) | `tariffs` | YES | YES | FK to sim_runs OK |
| 10. deployments (147 rows) | `deployments` | YES | YES | FK to sim_runs OK |
| 11. world_state (round 0) | `world_state` | YES | YES | FK to sim_runs OK |
| 12. country_state (round 0) | `country_state` | YES | YES (SELECT FROM countries) | FK to countries OK |
| 13. role_state (round 0) | `role_state` | YES | YES (SELECT FROM roles) | FK to roles OK |

**FK Reference validation (spot checks):**
- Every `country_id` in roles INSERT (`columbia`, `cathay`, `sarmatia`, etc.) exists in countries INSERT. OK.
- Every `country_id` in org_memberships exists in countries INSERT. OK.
- Every `org_id` in org_memberships (`western_treaty`, `the_union`, etc.) exists in organizations INSERT. OK.
- Zone IDs referenced in deployments (`col_main_1`, `cathay_3`, `ruthenia_2`, etc.) exist in zones INSERT. OK.
- Zone IDs in zone_adjacency all exist in zones INSERT. OK.
- All use consistent `sim_run_id = '00000000-0000-0000-0000-000000000001'`. OK.

### Issues Found:
- **[LOW]** B3 Section 7 (relationships) is truncated with a comment: "Remaining 281 relationships omitted for file size." The file contains ~100 relationships out of the expected 381 (21 countries x ~20 relationships each minus self). Not blocking for schema validation but **the production seed is incomplete**.
- **[LOW]** B3 Section 10 (deployments): Phrygia has two duplicate rows for `phrygia_2` with 1 ground unit each (lines 702-703, different notes). This may cause a unique constraint issue if a `(sim_run_id, country_id, unit_type, zone_id)` unique constraint were added, but the current schema uses UUID PK without such a constraint. The data is valid as-is but semantically may be an error (should likely be a single row with count=2).

---

## CHECK 8: Tech Stack <> Implementation Alignment
### Status: PASS
### Details:

| D1 Choice | Other Doc Alignment | Status |
|---|---|---|
| **Supabase (PostgreSQL)** | B1 uses PostgreSQL syntax, `uuid-ossp` extension, `auth.users` reference, RLS policies -- all Supabase-native | OK |
| **FastAPI (Python)** | F5 defines FastAPI routes with Pydantic models, async endpoints, OpenAPI auto-docs | OK |
| **Zustand (state mgmt)** | D1 Section 1.4 lists 6 stores (`worldStateStore`, `roleStore`, `eventStore`, `timerStore`, `uiStore`, `mapStore`). G spec references state updates conceptually. No contradiction. | OK |
| **Tailwind CSS** | D1 Section 1.3 defines full Tailwind config with TTT theme. References `SEED_H1_UX_STYLE_v2.md` Section 10. | OK |
| **React 18+ with TypeScript** | G spec describes component hierarchy (participant, facilitator, public, AI interfaces). No framework contradiction. | OK |
| **Supabase Realtime** | C1 Part 2 defines 8 channel types using Supabase Realtime patterns. D1 Section 1.5 matches. | OK |
| **Railway for engine** | F5 specifies `https://ttt-engine.railway.app/api/v1` as production base URL. D1 Section 3.3 specifies Railway. | OK |
| **Claude (primary LLM)** | F5 Sections 2.6-2.7 reference Claude API calls. D1 Section 4.1 specifies Claude Sonnet. | OK |
| **Recharts** | D1 lists chart types. G spec references dashboards. No contradiction. | OK |
| **Vercel** | D1 Section 1.9 specifies Vercel. No contradictions elsewhere. | OK |

### Issues Found:
- **[LOW]** D1 specifies `@supabase/supabase-js ^2.76+` but does not mention the Supabase service role key usage for server-side operations (Edge Functions writing to DB). F5 uses `httpx` for Supabase REST API from Python. These are compatible but the auth flow from engine server to Supabase is under-documented.

---

## CHECK 9: FK Integrity in Schema
### Status: PASS
### Details:
Every REFERENCES clause in B1 verified:

| Table | Foreign Key | References | Target Exists? | Target is PK/UNIQUE? |
|---|---|---|---|---|
| `users.id` | `auth.users(id)` | External Supabase table | YES (Supabase built-in) | YES (PK) |
| `facilitators.sim_run_id` | `sim_runs(id)` | `sim_runs.id` | YES | YES (PK) |
| `facilitators.user_id` | `users(id)` | `users.id` | YES | YES (PK) |
| `countries(sim_run_id)` | `sim_runs(id)` | `sim_runs.id` | YES | YES (PK) |
| `roles(user_id)` | `users(id)` | `users.id` | YES | YES (PK) |
| `roles(country_id, sim_run_id)` | `countries(id, sim_run_id)` | Composite PK | YES | YES (PK) |
| `zones(sim_run_id)` | `sim_runs(id)` | `sim_runs.id` | YES | YES (PK) |
| `zone_adjacency(sim_run_id)` | `sim_runs(id)` | `sim_runs.id` | YES | YES (PK) |
| `deployments(sim_run_id)` | `sim_runs(id)` | `sim_runs.id` | YES | YES (PK) |
| `organizations(sim_run_id)` | `sim_runs(id)` | `sim_runs.id` | YES | YES (PK) |
| `org_memberships(sim_run_id)` | `sim_runs(id)` | `sim_runs.id` | YES | YES (PK) |
| `relationships(sim_run_id)` | `sim_runs(id)` | `sim_runs.id` | YES | YES (PK) |
| `sanctions(sim_run_id)` | `sim_runs(id)` | `sim_runs.id` | YES | YES (PK) |
| `tariffs(sim_run_id)` | `sim_runs(id)` | `sim_runs.id` | YES | YES (PK) |
| `world_state(sim_run_id)` | `sim_runs(id)` | `sim_runs.id` | YES | YES (PK) |
| `country_state(sim_run_id)` | `sim_runs(id)` | `sim_runs.id` | YES | YES (PK) |
| `country_state(country_id, sim_run_id)` | `countries(id, sim_run_id)` | Composite PK | YES | YES (PK) |
| `role_state(sim_run_id)` | `sim_runs(id)` | `sim_runs.id` | YES | YES (PK) |
| `role_state(role_id, sim_run_id)` | `roles(id, sim_run_id)` | Composite PK | YES | YES (PK) |
| `events(sim_run_id)` | `sim_runs(id)` | `sim_runs.id` | YES | YES (PK) |
| `transactions(sim_run_id)` | `sim_runs(id)` | `sim_runs.id` | YES | YES (PK) |
| `transactions(event_id)` | `events(id)` | `events.id` | YES | YES (PK) |
| `combat_results(sim_run_id)` | `sim_runs(id)` | `sim_runs.id` | YES | YES (PK) |
| `combat_results(event_id)` | `events(id)` | `events.id` | YES | YES (PK) |
| `messages(sim_run_id)` | `sim_runs(id)` | `sim_runs.id` | YES | YES (PK) |
| `meetings(sim_run_id)` | `sim_runs(id)` | `sim_runs.id` | YES | YES (PK) |
| `ai_contexts(sim_run_id)` | `sim_runs(id)` | `sim_runs.id` | YES | YES (PK) |
| `ai_decisions(sim_run_id)` | `sim_runs(id)` | `sim_runs.id` | YES | YES (PK) |
| `artefacts(sim_run_id)` | `sim_runs(id)` | `sim_runs.id` | YES | YES (PK) |
| `artefacts(role_id, sim_run_id)` | `roles(id, sim_run_id)` | Composite PK | YES | YES (PK) |

**Circular dependencies check:**
- No circular FK dependencies. The dependency chain is: `auth.users` -> `users` -> `roles` -> `country_state`/`role_state`. `sim_runs` is the root for all game data tables.
- INSERT order: `sim_runs` -> `users` -> `facilitators` + `countries` -> `roles` -> `zones` -> everything else. No blocking cycles.

**Missing FKs (by design):**
- `deployments.country_id` has no FK to `countries` (uses TEXT, not composite FK). Documented design choice for flexibility.
- `relationships.from_country` / `to_country` have no FK. Same pattern.
- `sanctions.country` / `target` have no FK. Same pattern.
- `events.actor`, `events.target`, `events.country_context` have no FK. By design -- these are flexible TEXT fields that can reference roles, countries, or system actors.

### Issues Found:
- **[LOW]** Several tables use TEXT columns for country_id references without formal FK constraints (`deployments.country_id`, `relationships.from_country`/`to_country`, `sanctions.country`/`target`, `tariffs.imposer`/`target`). This is a deliberate trade-off for insert performance and flexibility, but means referential integrity for these columns depends on application logic.

---

## CHECK 10: Naming Consistency
### Status: FAIL
### Details:

### `sim_run_id` vs `sim_id`
| Document | Term Used | Consistent? |
|---|---|---|
| B1 (schema) | `sim_run_id` (UUID FK to sim_runs) | Baseline |
| B3 (seed data) | `sim_run_id` | OK |
| C1 (events) | `sim_run_id` | OK |
| C3 (API) | `sim_id` (in JWT claims: `sim_id`) | **MISMATCH** |
| F5 (engine) | `sim_run_id` | OK |
| D1 (tech stack) | `sim_id` (in JWT claims) | **MISMATCH** |

**Verdict:** B1, B3, C1, F5 consistently use `sim_run_id`. C3 and D1 JWT claims use `sim_id`. The JWT claim name does not need to match the column name, but it creates mapping complexity and potential bugs.

### `role_id` vs `actor_role_id`
| Document | Term Used | Context |
|---|---|---|
| B1 | `roles.id`, `role_state.role_id`, `events.actor` | Column names |
| C1 | `actor_role_id` (event envelope), `role_id` (in payloads) | Both used |
| C3 | `role_id` (path param, JWT claim) | Consistent |
| F5 | `actor_role_id` (request field), `role_id` (AI endpoints) | Both used |

**Verdict:** `actor_role_id` is used in C1/F5 for the event actor context. `role_id` is used for general role references. B1 uses `actor` (TEXT) in the events table -- shorter name. This is intentional (event actor vs role identity) but `actor` vs `actor_role_id` is a naming gap.

### `country_id` vs `country`
| Document | Term Used | Context |
|---|---|---|
| B1 | `country_id` (most tables), but `country` + `target` (sanctions table), `imposer` + `target` (tariffs), `from_country` + `to_country` (relationships, transactions) | **Inconsistent within schema** |
| C1 | `country_id`, `actor_country_id`, `target_country_id` | Qualified names |
| C3 | `country_id` (path params, schemas) | Consistent |
| F5 | `actor_country_id`, `country_id` | Qualified |

**Verdict:** B1 schema is internally inconsistent: `sanctions` uses `country`/`target`, `tariffs` uses `imposer`/`target`, `relationships` uses `from_country`/`to_country`, while most other tables use `country_id`. This is semantically motivated (imposer vs target) but breaks naming convention.

### `round` vs `round_num` vs `round_number`
| Document | Term Used | Context |
|---|---|---|
| B1 | `round_num` (world_state, country_state, role_state, events, etc.) | Consistent within schema |
| C1 | `round` (event envelope, payloads) | Different from B1 |
| C3 | `round` (path parameter, schema fields) | Different from B1 |
| F5 | `round` (request fields), `round_num` (response `new_world_state`) | **Both used** |

**Verdict:** B1 consistently uses `round_num`. C1 and C3 consistently use `round`. F5 uses both. This is the most significant naming inconsistency -- it spans multiple documents and will cause mapping bugs.

### `event_id` format
| Document | Term Used | Format |
|---|---|---|
| B1 | `events.id` | UUID (v4) |
| C1 | `event_id` | ULID string (`evt_<ulid>`) |
| C3 | `Event.id` | string |
| F5 | `events[].id` | string (`evt_auto_001` in examples) |

**Verdict:** B1 generates UUID v4 for event IDs. C1 specifies ULID format. These are different. ULIDs are time-sortable (needed for cursor pagination); UUID v4 is not.

### Issues Found:
- **[HIGH]** `round` vs `round_num` inconsistency: B1 uses `round_num`, C1/C3 use `round`, F5 uses both. Must standardize or document the mapping.
- **[HIGH]** Event ID format mismatch: B1 uses UUID v4, C1 specifies ULID. Must decide and align.
- **[MEDIUM]** `sim_run_id` vs `sim_id` in JWT claims (C3/D1) vs database column name (B1). Needs explicit mapping documentation.
- **[MEDIUM]** B1 internal inconsistency in country reference columns: `country_id` vs `country` vs `imposer` vs `from_country`.
- **[LOW]** C1 `actor_role_id` vs B1 `actor` column in events table.
- **[LOW]** Visibility case mismatch: C1 uses uppercase (`PUBLIC`), B1 uses lowercase (`public`).

---

## SUMMARY

| Metric | Value |
|---|---|
| **Total checks** | 10 |
| **Passed** | 5 (Checks 1, 2, 5, 7, 9) |
| **Partial** | 3 (Checks 3, 4, 8) |
| **Failed** | 2 (Checks 6, 10) |

### Issues by Severity

| Severity | Count | Key Issues |
|---|---|---|
| **HIGH** | 5 | Transaction type enum mismatch C3<>F5; Troop deployment missing from F5; Impeachment missing from full chain; `round` vs `round_num` naming; Event ID UUID vs ULID |
| **MEDIUM** | 7 | C3<>F5 field naming for transactions; Batch vs single action undocumented; F5 action type naming vs C1; `sim_run_id` vs `sim_id` JWT; B1 country column inconsistency; C1 event ID format vs B1; Edge Function decomposition undocumented |
| **LOW** | 11 | Various minor naming differences, missing formal contracts, truncated seed data, case mismatches |

### Total issues: 23 (5 HIGH, 7 MEDIUM, 11 LOW)

---

## Verdict: **BLOCKED -- RESOLVE HIGH ISSUES BEFORE LEVEL 2**

### Required fixes before proceeding:

1. **[HIGH] Align transaction type vocabulary** between C3 (`TransactionProposal.transaction_type` enum) and F5 (supported transaction types). C3 must add `arms_transfer`, `tech_transfer`, `treaty`, `agreement`, `organization_create` -- or document the mapping layer.

2. **[HIGH] Add deployment validation route to F5** or document that troop deployment bypasses the Python engine and is handled entirely by Edge Functions/database.

3. **[HIGH] Add impeachment to the action chain**: either add to F5 engine action types, or document that impeachment is a facilitator-mediated political action that does not require engine processing (similar to public_statement).

4. **[HIGH] Standardize `round` vs `round_num`**: pick one name and use it consistently across B1, C1, C3, and F5. Recommendation: use `round` everywhere (shorter, used in 3 of 4 docs) and rename the B1 columns.

5. **[HIGH] Resolve event ID format**: decide between UUID v4 (B1 current) and ULID (C1 specified). If cursor-based pagination requires time-sortability, switch B1 to ULID generation or add a sequence/timestamp-based cursor column.

### Recommended but not blocking:

6. **[MEDIUM] Document the Edge Function decomposition pattern** for C3 batch submissions -> F5 individual action calls.
7. **[MEDIUM] Align field naming** between C3 and F5 for transactions (`details` vs `terms`, `counterparty` vs `receiver_role_id`).
8. **[MEDIUM] Document JWT claim to column name mapping** (`sim_id` claim -> `sim_run_id` column).

---

*Validation performed by automated cross-reference analysis. Manual review recommended for all HIGH issues.*
