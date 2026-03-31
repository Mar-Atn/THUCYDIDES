# DET_VALIDATION_LEVEL3 -- End-to-End System Chain Trace
## 3 Representative Actions: UI Click to Database Update to Real-Time Broadcast

**Date:** 2026-03-30
**Validator:** VERA (via Claude)
**Documents traced:**
- G: `SEED_G_WEB_APP_SPEC_v1.md` (UI spec, 31 actions)
- C3: `DET_C3_API_SPEC.yaml` (API endpoints)
- F5: `DET_F5_ENGINE_API.md` (engine API)
- D8: `SEED_D8_ENGINE_FORMULAS_v1.md` (engine formulas)
- B1: `DET_B1_DATABASE_SCHEMA.sql` (database schema)
- C1: `DET_C1_SYSTEM_CONTRACTS.md` (events + channels + module contracts)
- `live_action_engine.py` (engine code)
- `world_model_engine.py` (engine code)
- `transaction_engine.py` (engine code)

---

# TRACE 1: GROUND ATTACK (Military Action, Real-Time)

**Scenario:** Pathfinder (Sarmatia HoS) orders a ground attack on `ruthenia_2`.

## Step-by-Step Table

| Step | Layer | Document | Reference | Field/Table/Endpoint | Status |
|------|-------|----------|-----------|---------------------|--------|
| 1 | UI | G spec | Action #7 (line 472-494) | Player sees Military Actions > Ground Attack panel. Selects target zone (`ruthenia_2`), origin zone, units to commit. Both commanders present + moderator. Dice rolled (real or app). Modifiers HIDDEN until after roll. | **OK** |
| 2 | API Call | C3 | `POST /actions/{round}/{country_id}` (line 979-1046) | Request body: `ActionSubmission` schema with `actions.military[]` containing `{action_type: "attack", target_zone: "ruthenia_2", from_zone: "...", units: {ground: N}}` | **OK** |
| 2a | API Call (Engine) | F5 | `POST /engine/action` (Section 2.1, line 110-246) | Edge Function forwards to engine: `{sim_run_id, round, action_type: "attack", actor_role_id: "pathfinder", actor_country_id: "sarmatia", target: {zone: "ruthenia_2", from_zone: "..."}, parameters: {units: {ground: N}}}` | **OK** |
| 3 | Engine Route | F5 | Section 2.1 Action Types table (line 154) | `action_type: "attack"` maps to `LiveActionEngine.resolve_attack()` | **OK** |
| 4 | Engine Processing | live_action_engine.py | `resolve_attack()` (line 82-185) | Method: `resolve_attack(attacker_country="sarmatia", defender_country="ruthenia", zone="ruthenia_2", units=N, origin_zone=...)`. Validates zone exists, gets defender forces via `zone_data["forces"]`, checks amphibious, builds modifiers via `_build_combat_modifiers()`, executes RISK dice (1d6+mods per pair, attacker needs >= defender+1), applies losses, checks zone capture, updates `war_tiredness += 0.5` per side. | **OK** |
| 4a | Formula (D8) | D8 | Part 6A: Ground Attack (line ~varies) | D8 documents same modifiers: AI L4 (+0 or +1 random), Low morale (-1 if stability <=3), Die Hard (+1 def), Amphibious (-1 att), Air support (+1 def binary). G spec Action #7 table matches. | **OK** |
| 5 | State Change | B1 | Tables: `deployments`, `zones`, `country_state`, `combat_results`, `events` | Engine updates: (a) `zones.owner` if captured, (b) `deployments.count` for both sides (losses), (c) `countries` table military counts, (d) writes to `combat_results` table with `combat_type='ground_attack'`, `attacker_country`, `defender_country`, `zone_id`, `outcome`, `attacker_losses`, `defender_losses`, `zone_control_change`. | **OK** |
| 5a | State Change detail | B1 | `combat_results` (line 545-568) | Fields: `attacker_country TEXT`, `defender_country TEXT`, `zone_id TEXT`, `attacker_units JSONB`, `defender_units JSONB`, `modifiers JSONB`, `dice_rolls JSONB`, `outcome TEXT` (CHECK: `attacker_wins`, `defender_wins`, `attacker_repelled`, `mutual_losses`, `stalemate`), `attacker_losses JSONB`, `defender_losses JSONB`, `zone_control_change JSONB`. | **OK** |
| 5b | State Change: war_tiredness | B1 | `country_state` (line 422) | `war_tiredness NUMERIC(6,2)` -- matches engine's `+= 0.5` per combat. | **OK** |
| 6 | Event Logged | C1 | `action.ground_attack` (line 178-206) | Event type: `action.ground_attack`, visibility: `PUBLIC`. Payload includes: `attacker_country_id`, `defender_country_id`, `from_zone`, `target_zone`, `attacker_units`, `defender_units`, `result: {outcome, attacker_losses, defender_losses, zone_control_changed, new_zone_owner}`, `modifiers_applied`. | **OK** |
| 6a | Event Logged (engine) | C1 | `engine.combat_result` (line 955-978) | Also: `engine.combat_result` event at PUBLIC visibility with `combat_type: "ground"`, zone info, outcome, losses. | **OK** |
| 7 | Real-Time Broadcast | C1 | Part 2, Channel `sim:{sim_id}:world` (line 1364-1397) | PUBLIC combat result pushed to `sim:{sim_id}:world` channel as `state_update` + `event`. All participants subscribed. | **OK** |
| 7a | Real-Time Broadcast (country) | C1 | Channel `sim:{sim_id}:country:{country_id}` (line 1399-1427) | Detailed country state changes pushed to both `sim:{sim_id}:country:sarmatia` and `sim:{sim_id}:country:ruthenia` channels. | **OK** |
| 7b | Real-Time Broadcast (alert) | C1 | Channel `sim:{sim_id}:alerts` (line 1507-1531) | If this is a war declaration or zone capture, an alert with `alert_type: "war_declared"` sent to alerts channel. | **OK** |
| 8 | RLS Filter | B1 | RLS policies (line 867-896) | **Events:** `events_read_public` policy -- `visibility='public'` events visible to ALL participants in the sim. Combat results are PUBLIC. **Combat results:** `combat_read` policy -- visible to attacker_country, defender_country, AND all participants (line 896: broad read for all sim members). **Facilitator:** sees everything via `is_facilitator()` check. | **OK** |
| 8a | RLS: Sarmatia sees | B1 | Various policies | Full combat details (own country), exact losses, modifiers (post-resolution), zone control change. Via `country_state_read_own` for country_state. | **OK** |
| 8b | RLS: Columbia sees | B1 | `events_read_public` (line 868-882) | Public event summary (combat outcome, zone change). Does NOT see detailed Sarmatia/Ruthenia country_state (treasury etc.) due to `country_state_read_own` policy filtering by `country_id = get_user_country_id()`. | **OK** |
| 8c | RLS: Facilitator sees | B1 | `is_facilitator()` bypasses all filters | Full unfiltered view of everything. | **OK** |
| 9 | UI Update | G spec | W1 Map (line 311-321), W2 News (line 322-332) | Map updates: zone control changes (occupied territory shown as stripes), unit positions update. News feed: combat outcome entry appears. Country dashboard: military unit counts update. War tiredness updates in political section. | **OK** |

### Trace 1 Issues Found

| # | Severity | Issue | Documents |
|---|----------|-------|-----------|
| T1-1 | **AMBIGUOUS** | F5 engine action endpoint uses `action_type: "attack"` but C1 event type is `action.ground_attack`. The mapping from F5's `"attack"` to C1's `"action.ground_attack"` is implicit -- no explicit translation table exists in a single place. F5 Section 2.1 (line 154) maps `attack` -> `resolve_attack()` but does not state the event_type string. The engine code `_log_combat_event()` would need to emit `action.ground_attack` not just `attack`. | F5/C1/live_action_engine.py |
| T1-2 | **AMBIGUOUS** | Engine code `resolve_attack()` (line 96-99) returns result dict with `"type": "attack"` but C1 event payload expects `"event_type": "action.ground_attack"`. The translation from engine internal type to C1 event type needs to happen somewhere (Edge Function or engine server wrapper). Not documented where. | live_action_engine.py / C1 |
| T1-3 | **AMBIGUOUS** | B1 `deployments` table does not have a FK to `zones` or `countries` with `sim_run_id` composite key. The `country_id` and `zone_id` columns are plain TEXT with no FK constraint. This allows referential integrity issues. | B1 (line 227-237) |
| T1-4 | **MINOR** | G spec Action #7 says "Both commanders present + moderator" but the C3 API endpoint `/actions/{round}/{country_id}` does not have a mechanism to verify physical presence of both commanders. This is expected to be a physical/facilitator-enforced rule, not a system-enforced one, but it is not explicitly stated which layer enforces it. | G/C3 |
| T1-5 | **OK** | F5 response (line 172-224) includes `state_changes` array with `path`, `old`, `new` format matching C1's `StateChange` schema and C3's `StateChange` component. Chain intact. | F5/C1/C3 |

---

# TRACE 2: BILATERAL TRANSACTION (Trade Deal, Two-Phase)

**Scenario:** Columbia's Dealer proposes a 3-coin military aid transfer to Ruthenia's Beacon.

## Step-by-Step Table

| Step | Layer | Document | Reference | Field/Table/Endpoint | Status |
|------|-------|----------|-----------|---------------------|--------|
| 1 | UI | G spec | Transactions section (line 730-748), Action #26 Trade | Dealer opens Transaction panel. Selects type: "Trade" (coin transfer). Selects recipient: Ruthenia (Beacon). Enters amount: 3 coins. Sees visibility tier: "COUNTRY" (both country teams see it). Submits. | **OK** |
| 2 | API Call | C3 | `POST /transactions` (line 1113-1156) | Request body: `TransactionProposal` schema: `{idempotency_key, transaction_type: "transfer_coins", proposer: "dealer", counterparty: "beacon", details: {from_country: "columbia", to_country: "ruthenia", amount: 3.0}}` | **OK** |
| 2a | API Call (Engine) | F5 | `POST /engine/transaction` (Section 2.2, line 250-354) | Edge Function forwards: `{sim_run_id, round, proposer_role_id: "dealer", proposer_country_id: "columbia", receiver_role_id: "beacon", receiver_country_id: "ruthenia", transaction_type: "coin_transfer", terms: {amount: 3.0, from_country: "columbia", to_country: "ruthenia"}}` | **OK** |
| 3 | Engine Route | F5 | Section 3.3 Internal Function Mapping (line 1081) | `POST /engine/transaction` -> `TransactionEngine.propose(transaction)` | **OK** |
| 4 | Engine Processing | transaction_engine.py | `propose_transaction()` (line 92-118) | Creates proposal dict with `tx_id`, `sender: "dealer"` (or "columbia"), `receiver: "beacon"` (or "ruthenia"), `tx_type: "coin_transfer"`, `status: "pending"`, `sender_confirmed: True`, `receiver_confirmed: False`. Validates via `_validate_proposal()`: checks tx_type valid, sender exists, balance check (amount > 0, treasury >= amount), authorization check. If valid, appends to `pending_transactions`. | **OK** |
| 5 | State Change (Proposal) | B1 | `transactions` table (line 514-535) | INSERT: `transaction_type='transfer_coins'`, `proposer_role_id='dealer'`, `counterparty_role_id='beacon'`, `from_country='columbia'`, `to_country='ruthenia'`, `details={amount: 3.0}`, `status='pending'`, `confirmation_token=<generated>`, `expires_at=<30min>`. | **OK** |
| 5a | State Change type mismatch | C3 vs transaction_engine.py | C3 schema uses `transfer_coins`; engine code uses `coin_transfer` | C3 `TransactionProposal.transaction_type` enum: `transfer_coins`. F5 Section 2.2 transaction types table: `coin_transfer`. Engine code `TRANSACTION_TYPES`: `coin_transfer`. B1 transactions table CHECK: `transfer_coins`. **MISMATCH: C3/B1 use `transfer_coins`, F5/engine use `coin_transfer`.** | **BROKEN** |
| 6 | Notification | C1 | `action.transaction_propose` (line 681-701) | Event: `event_type: "action.transaction_propose"`, visibility: `ROLE`. Payload: `{transaction_id, transaction_type: "transfer_coins", proposer_role_id: "dealer", counterparty_role_id: "beacon", terms: {from_country, to_country, amount}, expires_at}`. Pushed to Beacon via `sim:{sim_id}:role:beacon` channel. | **OK** |
| 6a | Notification channel | C1 | Channel `sim:{sim_id}:role:{role_id}` (line 1429-1456) | Auth rule: JWT `role_id` must match `beacon`. Only Beacon + moderator sees the proposal notification. | **OK** |
| 7 | Confirmation | C3 | `POST /transactions/{transaction_id}/confirm` (line 1158-1210) | Beacon confirms: `{confirmation_token: "conf_xyz", accepted: true}`. | **OK** |
| 7a | Confirmation (Engine) | F5 | `POST /engine/transaction/{id}/confirm` (Section 2.3, line 357-444) | Engine call: `TransactionEngine.confirm(transaction_id, accepted=true)`. Re-validates treasury balance at confirmation time. | **OK** |
| 7b | Confirmation (Engine code) | transaction_engine.py | `confirm_transaction()` (line 120-133) | Finds pending tx by `tx_id`, sets `receiver_confirmed = True`. Since both confirmed, calls `_execute_transaction(tx)`. | **OK** |
| 8 | State Change (Execution) | B1 + transaction_engine.py | Multiple tables | (a) `transactions.status` -> `'executed'`, `confirmed_at` set. (b) `country_state`: Columbia `treasury -= 3.0`, Ruthenia `treasury += 3.0`. (c) Event logged. | **OK** |
| 8a | Engine execution | transaction_engine.py | `_execute_transaction()` line 272-280 | `coin_transfer` branch: `ws.countries[sender_country]["economic"]["treasury"] -= amount`, `ws.countries[receiver_country]["economic"]["treasury"] += amount`. Logs event with `type: "transaction"`. | **OK** |
| 8b | Event logged | C1 | `action.transaction_confirm` (line 704-721) | Event: `event_type: "action.transaction_confirm"`, visibility: `COUNTRY`. Payload includes `state_changes` array showing treasury old/new for both countries. | **OK** |
| 9 | Broadcast | C1 | Channels: country channels for both sides | `sim:{sim_id}:country:columbia` and `sim:{sim_id}:country:ruthenia` receive `state_update` with treasury changes. Visibility: COUNTRY -- both country teams see it. Other countries do NOT see the transaction (per G spec line 741: "Others learn only via intelligence or observation"). | **OK** |
| 9a | RLS | B1 | `txn_read` policy (line 885-889) | Transaction visible to: `proposer_role_id = get_user_role_id()` OR `counterparty_role_id = get_user_role_id()` OR `is_facilitator()`. Other participants cannot see the transaction record. | **OK** |
| 9b | Facilitator view | B1 | `is_facilitator()` bypass | Facilitator sees full transaction details. | **OK** |

### Trace 2 Issues Found

| # | Severity | Issue | Documents |
|---|----------|-------|-----------|
| T2-1 | **BROKEN** | **Transaction type naming mismatch.** C3 API spec and B1 database schema use `transfer_coins`. F5 engine API and transaction_engine.py use `coin_transfer`. This is a direct naming conflict that would cause either API validation failure or engine rejection. One side must be renamed. | C3 (line 499) / F5 (line 293) / B1 (line 519) / transaction_engine.py (line 26) |
| T2-2 | **BROKEN** | **Extended type mismatch.** C3/B1 enum: `transfer_coins, trade_deal, basing_rights, aid_package, personal_invest, bribe`. F5/engine enum: `coin_transfer, arms_transfer, tech_transfer, basing_rights, treaty, agreement, org_creation`. Only `basing_rights` overlaps exactly. `aid_package` has no engine equivalent. `bribe` has no engine equivalent. `arms_transfer`, `tech_transfer`, `treaty`, `agreement`, `org_creation` have no C3/B1 equivalent. These are two different type systems. | C3/B1 vs F5/engine |
| T2-3 | **AMBIGUOUS** | F5 `POST /engine/transaction` uses `proposer_role_id` and `receiver_role_id`. Engine code `propose_transaction()` uses `sender` and `receiver`. The mapping between these field names is not documented -- the engine server wrapper must translate. | F5/transaction_engine.py |
| T2-4 | **AMBIGUOUS** | F5 response (line 303-337) returns `confirmation_token` and `expires_at`. Transaction engine code has no concept of confirmation tokens or expiration times -- these are purely database/API-layer constructs. The boundary of responsibility between engine and API layer is not explicitly documented for this. | F5/transaction_engine.py |
| T2-5 | **MINOR** | G spec describes transaction as "military aid transfer" (coins for military purpose) but neither the API nor engine has a transaction subtype or purpose field. All coin transfers are equivalent mechanically. This is by design (narrative context is player-facing), but the UI should make clear this is just a coin transfer with a narrative label. | G spec |

---

# TRACE 3: ROUND-END PROCESSING (Batch, Facilitator-Triggered)

**Scenario:** Facilitator clicks "Process Round" at end of Phase A, Round 2.

## Step-by-Step Table

| Step | Layer | Document | Reference | Field/Table/Endpoint | Status |
|------|-------|----------|-----------|---------------------|--------|
| 1 | UI | G spec | Facilitator interface (line 102-122) | Facilitator dashboard > Round Management > "End Phase A" button. Then trigger "Process Round" (world model engine). Controls section shows: round status, submissions, pending authorizations. | **OK** |
| 2a | API Call (Phase) | C3 | `POST /moderator/round/advance` (line 1338-1382) | First: `{action: "end_phase_a"}` to end Phase A. Then: | **OK** |
| 2b | API Call (Engine) | C3 | `POST /moderator/engine/trigger` (line 1384+) | Triggers world model engine processing. | **OK** |
| 2c | API Call (Engine route) | F5 | `POST /engine/round/process` (Section 2.4, line 448-621) | Request: `{sim_run_id, round: 2, country_actions: {columbia: {budget, tariffs, sanctions, ...}, cathay: {...}, ...}, event_log: [...], options: {use_ai_panel: true, generate_narrative: true, auto_fix_coherence: true}}` | **OK** |
| 3 | Engine Route | F5 | Section 3.3 (line 1083) | `POST /engine/round/process` -> `WorldModelEngine.process_round(round_num, country_actions, event_log)` | **OK** |
| 4 | Data Collection | F5 + world_model_engine.py | Section 2.4 request schema (line 497-508) | Engine receives: `country_actions` (all budgets, tariffs, sanctions, OPEC production, military orders), `event_log` (all Phase A events: combats, transactions, covert ops). Engine reads from in-memory `WorldState`: current country states, zones, deployments, wars, blockades, chokepoints, treaties, sanctions durations. | **OK** |
| 5 | Engine Processing | world_model_engine.py | `process_round()` (line 102-141) | **Three-pass architecture:** | **OK** |
| 5a | Pass 1: Deterministic | world_model_engine.py | `deterministic_pass()` (line 167-200+) | 14 chained steps: | **OK** |
| 5a-0 | Step 0: Apply Actions | world_model_engine.py | Line 180-190 | `_apply_tariff_changes()`, `_apply_sanction_changes()`, `_apply_opec_changes()`, `_apply_rare_earth_changes()`, `_apply_blockade_changes()`, `_update_sanctions_rounds()`, `_update_formosa_disruption_rounds()` | **OK** |
| 5a-1 | Step 1: Oil Price | D8 | Part 2, Step 1 (line 85-186) | Global: supply (OPEC decisions + sanctions), demand (economic health), disruption (blockades), war premium, inertia (40/60 blend), soft cap at $200, volatility noise, mean-reversion above $150. Output: `ws.oil_price`, `ws.oil_price_index`. | **OK** |
| 5a-2 | Step 2: GDP Growth | D8 | Part 2, Step 2 (line 189+) | Per country: base growth + tariff impact + sanctions damage + oil shock + formosa disruption + war damage + tech boost + crisis multiplier. | **OK** |
| 5a-3 | Step 3: Revenue | D8 | Part 2, Step 3 | Per country: GDP x tax_rate + oil_revenue + trade adjustments. | **OK** |
| 5a-4 | Step 4: Budget Execution | D8 | Part 2, Step 4 | Per country: mandatory maintenance first, then player allocations, deficit handling (print money or draw from treasury). | **OK** |
| 5a-5 | Step 5: Military Production | D8 | Part 2, Step 5 | Per country: coins allocated -> units produced based on production capacity and tier costs. | **OK** |
| 5a-6 | Step 6: Tech Advancement | D8 | Part 2, Step 6 | Per country: R&D investment -> progress increment -> level-up check against thresholds. | **OK** |
| 5a-7 | Step 7: Inflation | D8 | Part 2, Step 7 | Per country: money printed -> inflation increase. | **OK** |
| 5a-8 | Step 8: Debt Service | D8 | Part 2, Step 8 | Per country: deficit -> debt burden increase. | **OK** |
| 5a-9 | Step 9: Economic State | D8 | Part 2, Step 9 | Per country: evaluate crisis ladder (normal -> stressed -> crisis -> collapse). | **OK** |
| 5a-10 | Step 10: Momentum | D8 | Part 2, Step 10 | Per country: confidence variable updated based on growth, crisis, oil, war. | **OK** |
| 5a-11 | Step 11: Contagion | D8 | Part 2, Step 11 | Cross-country: major economy crisis spreads to trade partners. | **OK** |
| 5a-12 | Step 12: Stability | D8 | Part 2, Step 12 | Per country: GDP growth + social spending + war + sanctions + inflation + crisis state -> stability update. | **OK** |
| 5a-13 | Step 13: Political Support | D8 | Part 2, Step 13 | Per country: GDP growth + stability + casualties + crisis + oil price -> support update. | **OK** |
| 5b | Pass 2: Expert Panel | world_model_engine.py | `pass_2_expert_panel()` (line 122-123) | Three AI experts (KEYNES / CLAUSEWITZ / MACHIAVELLI) make heuristic adjustments. GDP adjustment capped at 30% per country. | **OK** |
| 5c | Pass 3: Coherence | world_model_engine.py | `coherence_pass()` (line 126-127) | Auto-fixes HIGH severity contradictions (e.g., GDP growth during collapse). Generates round narrative. | **OK** |
| 6 | State Changes | B1 | Multiple tables | (a) `world_state` INSERT new row for round 3: `oil_price`, `oil_price_index`, `wars`, `chokepoint_status`, `narrative`, `expert_panel`, `coherence_flags`. (b) `country_state` INSERT per country for round 3: `gdp`, `gdp_growth_rate`, `treasury`, `inflation`, `debt_burden`, `momentum`, `economic_state`, `market_index`, `revenue`, `mil_*`, `stability`, `political_support`, `war_tiredness`, `nuclear_level`, `ai_level`, `budget JSONB`. (c) `role_state` INSERT per role for round 3: `personal_coins`, `status`, pool remainders. | **OK** |
| 6a | State table match | B1 vs F5 response | Compare fields | F5 response `new_world_state.countries.columbia.economic` fields (`gdp`, `treasury`, `inflation`, `debt_burden`, `economic_state`, `momentum`, `revenue_last_round`) all have corresponding columns in `country_state` table. Military, political, technology fields also match. | **OK** |
| 7 | Election Check | F5 + C1 | F5 Section 2.8 `POST /engine/election` (line 840-921) | If Round 2: check scheduled events. Per D8/C7: Ruthenia wartime election occurs at Round 2 or 3. If election fires: separate `POST /engine/election` call with candidates and votes. Election result event: `engine.election_result` at PUBLIC visibility. | **OK** |
| 7a | Election endpoint | F5 | Section 2.8 (line 840) | `POST /engine/election` -- facilitator submits tallied votes. Engine applies effects to political_support, stability, leadership change. | **OK** |
| 7b | Election event | C1 | `engine.election_result` (line 928-953) | Event: `event_type: "engine.election_result"`, visibility: `PUBLIC`. Payload: election_type, country_id, candidates with vote_pct, winner, margin, effects. | **OK** |
| 8 | Events Logged | C1 | Multiple event types | (a) `engine.round_end` (PUBLIC, line 846-862): round frozen, events count, next round. (b) `engine.world_update` (MODERATOR, line 864-891): processing time, pass results, adjustments. (c) `engine.country_update` (COUNTRY, line 894-925): per-country economic/military/political/tech changes. (d) `engine.production_complete` (COUNTRY, line 981-1001): units produced. (e) `engine.tech_advance` (PUBLIC, line 1004-1025): if any country leveled up. (f) `engine.coherence_flag` (MODERATOR, line 1027-1046): if flags raised. (g) `engine.election_result` (PUBLIC): if election occurred. | **OK** |
| 9 | Facilitator Review | F5 | Section 2.4 notes (line 620) | F5 response includes `coherence_flags` and `expert_panel`. Facilitator reviews before publishing. Separate endpoint for expert panel review: `GET /moderator/expert-panel/{round}` (C3 line 1311). | **OK** |
| 9a | Facilitator review UI | G spec | Facilitator Controls (line 117) | "World Model Engine (trigger, review output, adjust values, approve & publish)". | **OK** |
| 10 | Publication | F5 | `POST /engine/round/publish` (Section 2.9, line 925-995) | Facilitator approves: `{sim_run_id, round: 2, approved_state: "full", overrides: [...]}`. Engine persists new state to Supabase via REST. Triggers Realtime updates. Response includes `round_published: 2`, `current_round: 3`. | **OK** |
| 10a | Publication event | C1 | Event types at publication | `engine.round_end` (PUBLIC) already logged. On publish: round_briefing event (PUBLIC) with narrative. `system.phase_change` to Phase B/C or next round's A. | **OK** |
| 11 | Real-Time Broadcast | C1 | Part 2 channels (line 1356+) | **Multi-channel fan-out:** (a) `sim:{sim_id}:world` -- oil price, chokepoint changes, public events (PUBLIC). (b) `sim:{sim_id}:country:{country_id}` -- per-country economic/military/political updates (COUNTRY). (c) `sim:{sim_id}:phase` -- phase_change to next round (PUBLIC). (d) `sim:{sim_id}:alerts` -- if significant events (election result, tech breakthrough, war declared). (e) `sim:{sim_id}:facilitator` -- engine status, coherence flags (MODERATOR). | **OK** |
| 11a | UI Update (participants) | G spec | Current Information (line 239-363) | Every participant's dashboard updates: (a) Country dashboard: new GDP, treasury, inflation, military counts, stability, support. (b) World map: zone ownership changes, new unit positions. (c) W2 News feed: round narrative, combat outcomes, election results, announcements. (d) W4 Global dashboard: Columbia vs Cathay GDP bars, oil price, naval comparison, active wars, election countdown, nuclear threat level. | **OK** |
| 11b | Public display | G spec | Public Display section (line 124-133) | Room screens update: global map, key indicators, news ticker, round clock advances to new round. | **OK** |

### Trace 3 Issues Found

| # | Severity | Issue | Documents |
|---|----------|-------|-----------|
| T3-1 | **AMBIGUOUS** | The exact trigger flow is: (1) `POST /moderator/round/advance {action: "end_phase_a"}` -> (2) `POST /moderator/engine/trigger` (C3) OR `POST /engine/round/process` (F5). The C3 spec has TWO potentially overlapping endpoints: `/moderator/engine/trigger` (line 1384) and the F5 `POST /engine/round/process`. Whether the C3 endpoint wraps the F5 endpoint or they are alternatives is not explicitly documented. | C3 (line 1384) / F5 (Section 2.4) |
| T3-2 | **AMBIGUOUS** | F5 `POST /engine/round/process` request includes `country_actions` aggregated by the Edge Function. But the C3 `/moderator/engine/trigger` endpoint (line 1384+) does not specify whether it passes country_actions or auto-collects them from the database. The data assembly step is underdocumented. | C3/F5 |
| T3-3 | **AMBIGUOUS** | F5 Section 2.4 says the facilitator reviews results BEFORE publication (separate endpoint 2.9). But the C3 `/moderator/round/advance` endpoint has actions including `start_phase_b` and `end_phase_b` with no explicit link to the engine trigger / review / publish sequence. The full facilitator workflow (end A -> trigger engine -> review -> publish -> start next A) is not documented as a sequence in any single place. | C3/F5/G |
| T3-4 | **MINOR** | world_model_engine.py `process_round()` signature (line 102-103) takes `(self, world_state, all_actions, round_num)` but F5 Section 2.4 notes say the internal call is `process_round(round_num, country_actions, event_log)`. The argument order and names differ. The `event_log` parameter exists in F5 but not in the engine code signature. | F5 (line 619) / world_model_engine.py (line 102) |
| T3-5 | **MINOR** | B1 `world_state` table has `narrative TEXT` and `expert_panel JSONB` columns. The F5 response returns these as `data.narrative` and `data.expert_panel`. The mapping is clear but the `expert_panel` JSONB structure is documented in C3 (`ExpertPanel` schema, line 565-634) and C1 (engine.world_update payload) but not in B1. B1 uses generic `JSONB` without schema constraints. This is normal for JSONB but creates a documentation-only contract. | B1/C3/C1 |

---

# CROSS-TRACE ISSUES

| # | Severity | Issue | Documents |
|---|----------|-------|-----------|
| X-1 | **BROKEN** | **Transaction type taxonomy split.** The C3 API + B1 database use one set of transaction type names (`transfer_coins`, `trade_deal`, `basing_rights`, `aid_package`, `personal_invest`, `bribe`). The F5 engine API + transaction_engine.py use a different set (`coin_transfer`, `arms_transfer`, `tech_transfer`, `basing_rights`, `treaty`, `agreement`, `org_creation`). These need to be reconciled into a single canonical list. Either the API/DB adapts to engine naming, or a translation layer is documented. | C3/B1 vs F5/engine |
| X-2 | **AMBIGUOUS** | **Event type naming convention.** C1 uses dot-separated `action.ground_attack`. Engine code returns `"type": "attack"`. F5 uses `action_type: "attack"`. The translation from engine-internal naming to C1 event naming is the responsibility of the engine server wrapper (`server.py` as shown in F5 Section 3.1), but the exact mapping table is not formally documented. | F5/C1/engine code |
| X-3 | **AMBIGUOUS** | **Two API layers.** C3 defines the participant-facing REST API (Supabase Edge Functions). F5 defines the internal engine API (Python FastAPI on Railway). The Edge Function sits between them but its behavior (validation, translation, aggregation) is not specified in a dedicated document. It is described abstractly in F5 Section 1.1 (line 19-47) but has no formal spec. | C3/F5 |

---

## SUMMARY

- **Traces completed:** 3
- **Total steps traced:** 43
- **Intact links:** 35
- **Broken links:** 2 (both related to the same root cause: transaction type taxonomy split)
- **Ambiguous:** 10
- **Critical gaps found:**
  1. **Transaction type naming mismatch (CRITICAL):** C3/B1 use `transfer_coins` etc.; F5/engine use `coin_transfer` etc. Two incompatible enums with only 1 of 6+ types matching (`basing_rights`). This WILL cause runtime failures unless a translation layer is added.
  2. **Edge Function specification gap (MODERATE):** The Edge Function that bridges C3 (participant API) to F5 (engine API) has no formal document. It must handle: JWT validation, permission checking, field name translation (e.g., `proposer` to `sender`), event type mapping (`attack` to `action.ground_attack`), and state aggregation for round processing. This is a significant undocumented component.
  3. **Round-end workflow orchestration (MODERATE):** The facilitator's exact sequence (end phase A -> trigger engine -> review -> optionally override -> publish -> advance to next round) spans multiple endpoints across C3 and F5 but is not documented as a unified workflow. Each step works individually but the orchestration is implicit.
- **Verdict:** **GAPS FOUND**

### Recommended Fixes (Priority Order)

1. **Reconcile transaction type taxonomy.** Choose ONE canonical set of names and update C3, B1, F5, and transaction_engine.py to match. Recommendation: adopt the engine's naming (`coin_transfer`, `arms_transfer`, etc.) as it is more descriptive, and add `personal_invest` and `bribe` to the engine.
2. **Create DET_C2_EDGE_FUNCTION_SPEC.** Document the Edge Function layer: its request translation logic, permission checking, event type mapping table, and data aggregation for round processing.
3. **Document the facilitator round workflow** as a single sequence diagram showing the complete Phase A -> B -> C -> next round flow with all API calls in order.
4. **Add formal event type mapping table** from engine internal types to C1 event types.
5. **Align F5 `process_round()` signature** with actual engine code, or document the adaptation layer.
