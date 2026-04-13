# Reconciliation Log — Build Phase Changes for Upward Doc Update

**Purpose:** Track all changes made during BUILD that need to propagate
upward to DET → SEED → CONCEPT when the doc reconciliation sprint runs.
Each entry notes WHAT changed, WHERE in the code it lives, and WHICH
design docs are now out of date.

**When to use this log:** After all action slices + AI Participant Module
are complete, this log drives a single coherent reconciliation pass
across all design documents. Do NOT update DET/SEED/CONCEPT piecemeal.

---

## F1 — Sim Run Foundation (2026-04-11/12)

| Change | Code location | Docs to update |
|---|---|---|
| 12 hot-path tables re-keyed by `sim_run_id` (was `scenario_id`) | All `*_per_round` tables | DET_B1_DATABASE_SCHEMA, DET_F_SCENARIO_CONFIG_SCHEMA |
| `sim_runs` lifecycle fields: description, seed, finalized_at, status enum extended | `sim_runs` table | DET_B1 |
| `sim_run_manager` service: create/seed/finalize/list runs | `engine/services/sim_run_manager.py` | DET_F, SEED_C_MAP_UNITS_MASTER §5 |
| Template / Scenario / Run canonical 3-level model locked | `F1_TAXONOMY.md` | SEED_C §5, CONCEPT (hierarchy diagram) |
| Observatory reads `sim_runs` directly (dropped `test_runs` table) | `test-interface/server.py` | CARD_OBSERVATORY |
| `resolve_round` + all context builders accept `sim_run_id` (dual-input) | All engine entry points | DET_D8, DET_F5 |
| Temporary DB default on `sim_run_id` (to be dropped in F1.1) | Migration | N/A (temporary) |

---

## M1 — Movement (2026-04-11)

| Change | Code location | Docs to update |
|---|---|---|
| `move_units` (plural) replaces `move_unit` everywhere | CONTRACT_MOVEMENT v1.0 | SEED_D8 Part 6B |
| No range limit per CARD_ACTIONS §1.1 (overrides SEED_D8 transit delay) | Validator | SEED_D8 |
| Movement validator: 17 error codes, batch-atomic, state-propagating | `engine/services/movement_validator.py` | DET_D8, DET_C1 |
| Movement engine auto-detects embark/debark | `engine/engines/movement.py` | SEED_D8 |
| `movement_decision` JSONB audit column on `country_states_per_round` | DB migration | DET_B1 |
| `resolve_mobilization` renamed to `resolve_martial_law` | `engine/engines/military.py` | DET_D8 |

---

## M2 — Ground Combat (2026-04-12)

| Change | Code location | Docs to update |
|---|---|---|
| `attack_ground` replaces `declare_attack` as canonical action_type | CONTRACT_GROUND_COMBAT v1.0 | SEED_D8 |
| `CombatResult.attacker_rolls` → list-of-lists (per-exchange, not flat) | `engines/military.py:GroundCombatResult` | DET_D8 |
| `modifier_breakdown` list of `{side, value, reason}` replaces summed bonus | Same | DET_D8 |
| `precomputed_rolls` hook on `resolve_ground_combat()` | Same | NEW — not in any doc |
| `observatory_combat_results.modifier_breakdown JSONB` column added | DB migration | DET_B1 |
| `attack_ground_decision` JSONB audit column | DB migration | DET_B1 |
| `_build_ground_modifiers` returns structured modifier list (not dict) | `resolve_round.py` | DET_D8 |

---

## M3 — Air Strikes (2026-04-12)

| Change | Code location | Docs to update |
|---|---|---|
| `attack_air` canonical action_type | CONTRACT_AIR_STRIKES v1.0 | SEED_D8 |
| Per-shot result list (AirStrikeShot) with individual probabilities | `engines/military.py:AirStrikeResult` | DET_D8 |
| **No air superiority bonus** per CARD_FORMULAS D.2 (removed from engine) | Same | SEED_D8 (was wrongly stated) |
| `observatory_combat_results.attacker_rolls` + `defender_rolls` migrated from `int[]` to `jsonb` | DB migration `m3_combat_rolls_to_jsonb` | DET_B1 |
| `attack_air_decision` JSONB audit column | DB migration | DET_B1 |

---

## M4 — Naval Combat (2026-04-12)

| Change | Code location | Docs to update |
|---|---|---|
| `attack_naval` canonical action_type (1v1 ship dice) | CONTRACT_NAVAL_COMBAT v1.0 | SEED_D8 |
| `NavalCombatResultM4` with `{roll, modified}` per side | `engines/military.py` | DET_D8 |
| Legacy `resolve_naval_combat` → `resolve_naval_combat_legacy_v1` | Same | N/A (internal) |
| `attack_naval_decision` JSONB audit column | DB migration | DET_B1 |

---

## M5 — Bombardment + Blockade + Conventional Missile (2026-04-12)

| Change | Code location | Docs to update |
|---|---|---|
| `attack_bombardment` canonical action_type (10% per naval) | CONTRACT M5 Part A | SEED_D8 |
| `blockade` canonical action_type (3 chokepoints) | CONTRACT M5 Part B | SEED_D8 |
| `launch_missile` (conventional, warhead="conventional") | CONTRACT M5 Part C | SEED_D8 |
| 3 new JSONB audit columns: bombardment, blockade, missile | DB migration | DET_B1 |
| 3 new validators: bombardment, blockade, missile | `engine/services/` | DET_D8 |

---

## M6 — Nuclear Chain (2026-04-13)

| Change | Code location | Docs to update |
|---|---|---|
| **First multi-step chained decision** (4-phase state machine) | `engine/orchestrators/nuclear_chain.py` | NEW — not in any doc. Needs new DET section. |
| `nuclear_actions` DB table (state machine tracker) | DB migration | DET_B1 (new table) |
| `nuclear_test` + `launch_missile` (warhead="nuclear") validators | `engine/services/nuclear_validator.py` | DET_D8 |
| 3-way authorization chain: HoS + 2 authorizers (or AI Officers) | Orchestrator | SEED_E5 (agent model), DET_C1 (contracts) |
| Authorization role mapping per country (5 multi-role, rest AI Officer) | `AUTHORIZATION_ROLES` constant | Template data / CARD_TEMPLATE |
| AI Officer one-off LLM calls for authorization + interception | Orchestrator | NEW — needs DET section |
| T3+ voluntary interception decision flow | Orchestrator | SEED_D8, DET_D8 |
| Nuclear test success probability: 70% (below T2) / 95% (T2+) | Engine | CARD_FORMULAS D.7 (already correct) |
| Nuclear launch: 80% hit, 50% military destroy, GDP%, salvo aggregate | Engine | CARD_FORMULAS D.6 (already correct) |
| `nuclear_confirmed` field usage: R&D complete → unconfirmed → test → confirmed | Engine + validator | DET_B1 (field exists, semantics need doc) |
| `nuclear_test_decision` + `nuclear_launch_decision` JSONB audit columns | DB migration | DET_B1 |
| Nuclear site hexes: Persia (7,13), Choson (3,18) hardcoded in config | `NUCLEAR_SITE_HEXES` constant | Template data, map_config |

---

## Observatory Enhancements (2026-04-11/12)

| Change | Code location | Docs to update |
|---|---|---|
| Test Run selector reads `sim_runs` (not `test_runs`) | `observatory.js` + `server.py` | CARD_OBSERVATORY |
| Map-tab round scrubber (`/api/observatory/available-rounds`) | Both | CARD_OBSERVATORY |
| "Movements This Round" panel below map | `observatory.js` | CARD_OBSERVATORY |
| AI movement context viewer (`/api/observatory/movement-context`) | Both | CARD_OBSERVATORY |
| "Combats This Round" panel: M2 ground (per-exchange dice + modifiers), M3 air (per-shot sorties), M4 naval (1v1 dice) | `observatory.js` + `observatory.css` | CARD_OBSERVATORY |
| Combat hex markers on map (existing, auto-picks new combat types) | Already existed | N/A |

---

## AI Context Gaps (documented for future AI Module)

See `F1_CONTEXT_GAPS.md` — captures everything the current decision-specific
context builders DON'T provide that the AI Participant Module v1.0 will need
(map semantics, enemy positions, unit descriptions, doctrine, memory, goals,
lookup tools).

---

## Summary counts

| Category | Items |
|---|---|
| New contracts | 8 (`CONTRACT_MOVEMENT`, `_BUDGET`, `_TARIFFS`, `_SANCTIONS`, `_OPEC`, `_GROUND_COMBAT`, `_AIR_STRIKES`, `_NAVAL_COMBAT`, `_NAVAL_BOMBARDMENT_BLOCKADE`, `_NUCLEAR_CHAIN`) |
| New DB tables | 1 (`nuclear_actions`) |
| New DB columns | 12 JSONB audit columns on `country_states_per_round` |
| DB column type changes | 2 (`attacker_rolls`/`defender_rolls` int[] → jsonb) |
| New validators | 9 files in `engine/services/` |
| New engine functions | 4 (ground combat, air strike, naval combat, nuclear chain orchestrator) |
| L1 tests added | 108 (458 → 566) |
| L2 tests added | ~25 |
| L3 tests added | ~8 |
| Design docs to update | DET_B1, DET_D8, DET_C1, DET_F, SEED_D8, SEED_C §5, SEED_E5, CARD_OBSERVATORY, CONCEPT (hierarchy) |

---

## T1 — Exchange Transactions (2026-04-13)

| Change | Code location | Docs to update |
|---|---|---|
| `propose_transaction` + `respond_to_exchange` as canonical API | `engine/services/transaction_engine.py` | SEED_E5 §7 (transaction flow), DET_C1 (contracts) |
| Transaction validator with role authorization (HoS=all, mil=units, FM=coins+basing) | `engine/services/transaction_validator.py` | DET_D8 (action validation) |
| Atomic asset transfers: coins, units (unit_code-level), tech (+0.20 nuclear/+0.15 AI), basing rights | `transaction_engine.py:_execute_transfers` | SEED_E5 §7, CARD_FORMULAS C.4 (tech transfer values) |
| Country scope vs personal scope trading | Validator + engine | SEED_E5 §7.2 (individual transactions) |
| Counter-offer chain: propose → counter → accept/decline (one iteration max) | Engine | TRANSACTION_LOGIC.md (already correct) |
| Execution validation: both sides re-checked at execution time (assets may have changed) | `transaction_validator.py:validate_execution` | NEW — not in any doc |
| Unit transfer = specific unit_codes flipped to receiver's reserve (not count-based) | `_transfer_unit` | SEED_D8 (unit ownership), DET_B1 (unit_states_per_round) |
| `exchange_transactions` table already had `sim_run_id` from F1 | F1 migration | DET_B1 |

---

## T2 — Agreements (2026-04-13)

| Change | Code location | Docs to update |
|---|---|---|
| `propose_agreement` + `sign_agreement` as canonical API | `engine/services/agreement_engine.py` | SEED_E5 §7, DET_C1 |
| Agreement validator: 10 error codes, role auth (HoS/FM/diplomat), signatory checks | `engine/services/agreement_validator.py` | DET_D8 |
| Per-signatory tracking via `signatures JSONB` column on `agreements` table | DB migration `t2_agreements_enhancement` | DET_B1 |
| `proposer_country_code` + `proposer_role_id` columns added to `agreements` | Same migration | DET_B1 |
| Pre-defined agreement types (armistice, peace_treaty, military_alliance, etc.) + custom | Engine | CARD_ACTIONS §5.2 (already correct) |
| Public/secret visibility flag | Engine | CARD_ACTIONS §5.2 (already correct) |
| **NO enforcement** of any agreement type — all trust-based, full sovereignty | Design decision | SEED_E5 (update: remove "engine-enforced ceasefire" language), DET_C1 |
| Proposer auto-signs at proposal time (included in signatures) | Engine | NEW — not in design docs |
| Multilateral support: N signatories, unanimous required for activation | Engine | CARD_ACTIONS §5.2 (already correct) |

---

---

## Power Assignments — Authorization Backbone (2026-04-13)

| Change | Code location | Docs to update |
|---|---|---|
| **NEW `power_assignments` DB table** — tracks who holds military/economic/foreign_affairs authority per country per run | DB migration `power_assignments_table` | DET_B1 (new table) |
| **`power_assignments.py` service** — seed_defaults, check_authorization, reassign_power, get_assignments | `engine/services/power_assignments.py` | DET_C1, SEED_E5 (role authorization model) |
| **Canonical starting table** — 5 multi-role countries × 3 powers = 15 default assignments | `DEFAULT_ASSIGNMENTS` constant | CARD_TEMPLATE (new section: starting power assignments) |
| **Action-to-power mapping** — every action_type mapped to military/economic/foreign_affairs power | `ACTION_TO_POWER` dict | CARD_ACTIONS (add authorization column to action table) |
| **HoS implicit authority** — HoS always authorized for everything, not stored in table | Design decision | SEED_E5, CONCEPT (role model) |
| **Reassign_power action** — HoS can reassign or vacate any power slot mid-game | Engine function | CARD_ACTIONS §6.3 (replaces fire_role concept) |
| **Basing rights table** — separate from relationships, tracks grant/revoke with source | DB migration + `basing_rights_engine.py` | DET_B1 (new table), CARD_ACTIONS §1.11 |
| **Transaction engine routes through basing_rights_engine** — single source of truth | `transaction_engine.py:_grant_basing` updated | DET_C1 |

---

## Run Roles — Per-Run Role State (2026-04-13)

| Change | Code location | Docs to update |
|---|---|---|
| **NEW `run_roles` DB table** — per-run clone of template roles, mutable (status, coins) | DB migration `run_roles_table` | DET_B1 (new table), SEED_E5 (role lifecycle model) |
| **`run_roles.py` service** — seed_run_roles, get/update status, personal coins | `engine/services/run_roles.py` | DET_C1 (role state contracts) |
| **Architectural principle: template roles are FROZEN per run** — all mutations go to run_roles | Design decision (matches KING pattern) | CONCEPT (data model), SEED_C §5 (Template/Scenario/Run), DET_B1 |
| **Status lifecycle: active→arrested→released, active→killed, active→deposed** | run_roles.status column | SEED_E5 (role lifecycle), DET_D8 |
| **Personal coins tracked per run** (not template-level) | run_roles.personal_coins | SEED_E5, CARD_TEMPLATE |
| **40 roles seeded per run** from Template v1.0 | seed_run_roles() | CARD_TEMPLATE |
| **Template `roles` table stays frozen** — read-only during sim runs | Architecture constraint | CONCEPT, SEED_C, DET_B1 |

---

## Domestic + Covert + Political Actions (2026-04-13)

| Change | Code location | Docs to update |
|---|---|---|
| **Arrest engine** — request_arrest + release_arrested_roles | `engine/services/arrest_engine.py` | SEED_D8 (political), DET_D8 |
| **Martial law engine** — conscript units + stability/WT costs | `engine/services/martial_law_engine.py` | SEED_D8, DET_D8 |
| **`martial_law_declared` boolean** on country_states_per_round | DB migration | DET_B1 |
| **Intelligence engine** — 9-domain world context + LLM oracle | `engine/services/intelligence_engine.py` | SEED_D8, DET_C1 |
| **Sabotage engine** — 3 damage types + detection/attribution | `engine/services/sabotage_engine.py` | SEED_D8, DET_D8 |
| **Propaganda engine** — boost/destabilize + diminishing returns | `engine/services/propaganda_engine.py` | SEED_D8, DET_D8 |
| **Election meddling engine** — support shift ±2-5% | `engine/services/election_meddling_engine.py` | SEED_D8, DET_D8 |
| **Assassination engine** — kill/survive 50/50 + martyr/sympathy | `engine/services/assassination_engine.py` | SEED_D8, DET_D8 |
| **Coup engine** — AI co-conspirator LLM call + HoS swap | `engine/services/coup_engine.py` | SEED_D8, DET_D8, DET_C1 |
| **Mass protest engine** — revolution attempt + prerequisites | `engine/services/protest_engine.py` | SEED_D8, DET_D8 |
| **Early elections engine** — HoS calls election for next round | `engine/services/early_elections_engine.py` | SEED_D8, DET_D8 |
| **`early_election_called` boolean** on country_states_per_round | DB migration | DET_B1 |
| **Protest engine bug fix** — `0 or 5` falsy guard on stability/support | `protest_engine.py:42-43` | — |
| **Domestic validator** — arrest, martial_law, fire_role | `engine/services/domestic_validator.py` | DET_C1 |
| **Covert ops validator** — intelligence, sabotage, propaganda, election_meddling | `engine/services/covert_ops_validator.py` | DET_C1 |
| **Political validator** — assassination, coup, mass_protest, early_elections | `engine/services/political_validator.py` | DET_C1 |
| **11 new CONTRACT docs** — arrest through early_elections | `PHASES/UNMANNED_SPACECRAFT/CONTRACT_*.md` | — |

---

## Elections — Nominations, Voting, Resolution (2026-04-13)

| Change | Code location | Docs to update |
|---|---|---|
| **3 new DB tables**: `election_nominations`, `election_votes`, `election_results` | DB migration `create_election_nominations_and_votes` | DET_B1 (3 new tables) |
| **Election engine** — submit_nomination(), cast_vote(), resolve_election() | `engine/services/election_engine.py` | SEED_D8 (election mechanics), DET_D8, DET_C1 |
| **Camp system** — Columbia roles tagged president_camp / opposition | `election_engine.py:COLUMBIA_CAMPS` | SEED_B1_COUNTRY_COLUMBIA (political camps) |
| **Population vote mechanic** — AI score distributed by camp, 50/50 with participant votes | `election_engine.resolve_election()` | SEED_D8, CARD_FORMULAS B.3 |
| **Secret ballot** — individual votes not revealed in observatory events | Design decision | DET_C1 (event visibility rules) |
| **`early_election_called` boolean** on country_states_per_round | DB migration | DET_B1 |
| **Early elections engine** — HoS calls election for next round | `engine/services/early_elections_engine.py` | SEED_D8, DET_D8 |
| **CONTRACT_ELECTIONS.md** — nominations, voting, resolution contract | `PHASES/UNMANNED_SPACECRAFT/CONTRACT_ELECTIONS.md` | — |
| **CONTRACT_EARLY_ELECTIONS.md** — call early elections contract | `PHASES/UNMANNED_SPACECRAFT/CONTRACT_EARLY_ELECTIONS.md` | — |

---

## Quality Audit + Integration Glue (2026-04-13)

| Change | Code location | Docs to update |
|---|---|---|
| **Falsy-value bug fix** — `int(x or 5)` treats 0 as 5. Fixed in 8 engine files | coup, assassination, election_meddling, propaganda, protest, martial_law engines | — |
| **Shared helpers module** — `safe_int()`, `safe_float()`, `get_scenario_id()`, `write_event()` | `engine/services/common.py` | DET_C1 (shared services) |
| **Action Dispatcher** — central routing of all 25+ action types to engines | `engine/services/action_dispatcher.py` | DET_F (orchestration), DET_C1 |
| **Round Flow Contract** — Phase A / Phase B / Inter-Round architecture | `CONTRACT_ROUND_FLOW.md` | DET_F, SEED_D9, CONCEPT |
| **AI participant cadence** — 2 asks per round, max 5 actions, mandatory decisions separate | `CONTRACT_ROUND_FLOW.md` | DET_F, SEED_E5 |
| **Agent schemas expanded** — 9 → 25 action types (added 16 domestic/political/military schemas) | `engine/agents/action_schemas.py` | DET_C1 (agent API) |
| **Election state context block** — schedule, nominations, voting status for AI agents | `engine/context/blocks.py` | SEED_D9, DET_C1 |
| **Political risks context block** — revolution probability, coup risk per country | `engine/context/blocks.py` | SEED_D9, DET_C1 |
| **Orchestrator Phase A wiring** — `_dispatch_phase_a_actions()` processes free actions from agent_decisions | `engine/engines/orchestrator.py` | DET_F |
| **`processed_at` column** on agent_decisions — tracks which actions have been dispatched | DB migration | DET_B1 |
| **`nuclear_test` + `propose_transaction` routes** in dispatcher | `engine/services/action_dispatcher.py` | — |
| **L1 tests for dispatcher + schemas + formulas** — 59 new tests (routing, validation, probability formulas, safe helpers) | `tests/layer1/test_action_*.py`, `test_engine_formulas.py` | — |
| **DET_B1 schema addendum** — 26 missing tables documented with full column specs | `3 DETAILED DESIGN/DET_B1_SCHEMA_ADDENDUM_BUILD.sql` | DET_B1 (merge into v1.3) |
| **Probability calibration PASS** — all covert/political engine probabilities match contracts | Audit finding | — |
| **Nuclear intercept clarification** — `MISSILE_INTERCEPT_PROB=0.30` is legacy conventional only; nuclear chain uses correct 50%/25% | `engine/engines/military.py:134` comment, `engine/orchestrators/nuclear_chain.py:61-62` | — |

---

## Updated summary counts (post all work)

| Category | Items |
|---|---|
| New contracts | 24 (added: round_flow, elections, early_elections, mass_protest + prior 20) |
| New DB tables | 4 (`nuclear_actions`, `election_nominations`, `election_votes`, `election_results`) |
| New DB columns | 12 JSONB audit + 3 agreement + `martial_law_declared` bool + `early_election_called` bool |
| DB column type changes | 2 (`attacker_rolls`/`defender_rolls` int[] → jsonb) |
| New validators | 14 files (added: domestic, covert_ops, political) |
| New engine files | 21 (added: action_dispatcher, common, election_engine, early_elections_engine, protest_engine + prior 16) |
| Bug fixes | 8 falsy-value bugs across 6 engine files |
| L2 tests added | ~58 |
| Design docs to update | DET_B1, DET_D8, DET_C1, DET_F, SEED_D8, SEED_D9, SEED_B1_COLUMBIA, SEED_C §5, SEED_E5 §7, CARD_OBSERVATORY, CONCEPT (hierarchy, round flow) |
