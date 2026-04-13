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

## Updated summary counts (post T1+T2)

| Category | Items |
|---|---|
| New contracts | 10 (added: `CONTRACT_TRANSACTIONS`, `CONTRACT_AGREEMENTS`) |
| New DB tables | 1 (`nuclear_actions`) |
| New DB columns | 12 JSONB audit columns + 3 agreement enhancement columns |
| DB column type changes | 2 (`attacker_rolls`/`defender_rolls` int[] → jsonb) |
| New validators | 11 files in `engine/services/` (added: transaction, agreement) |
| New engine functions | 6 (added: transaction_engine, agreement_engine) |
| L1 tests added | 134 (458 → 592) |
| L2 tests added | ~33 |
| L3 tests added | ~8 |
| Design docs to update | DET_B1, DET_D8, DET_C1, DET_F, SEED_D8, SEED_C §5, SEED_E5 §7, CARD_OBSERVATORY, CONCEPT (hierarchy), TRANSACTION_LOGIC.md (minor updates) |
