# MODULE REGISTRY — Live Status
**Last updated:** 2026-04-16

| Module | Status | SPEC | Progress |
|---|---|---|---|
| M1 World Model Engines | ✅ ALIGNED | N/A | 720 L1 tests passing. Deprecated fields marked (political_support, dem_rep_split). Agent prompts use stability only. New actions: change_leader (stub for M4). **Military engine function signatures outdated** — v2 refactor changed params but dispatcher not yet updated (9 combat functions). |
| M2 Communication & Standards | ⚠️ UPDATE NEEDED | N/A | **32 canonical action types** (renamed 2026-04-16, see ACTION_NAMING below). 3 contracts (CHANGE_LEADER, COLUMBIA_ELECTIONS, MAP_RENDERING). 3 archived. Action dispatcher fully reconciled to DB names. |
| M3 Data Foundation | ✅ ALIGNED | N/A | Template/Run hierarchy. **SimRun creation now copies 11 tables server-side** (`POST /api/sim/create`). observatory_events enriched (+phase, +category, +role_name). SimRun Pydantic model synced to DB (24 fields). |
| M10.1 Auth | ✅ DONE | ✅ | Email/password + Google OAuth, RLS, GDPR consent. Custom lock bypass for navigator.locks. |
| M9 Sim Setup | ✅ v2 DONE | ✅ | 10-tab Template Editor, SimRun wizard (now with server-side data inheritance), User Mgmt, AI Setup. 40 roles (5 types), 32 action types in role_actions, country/role briefs, map viewer/editor. |
| M4 Sim Runner | ⚠️ Phase 2 IN PROGRESS | ✅ | Phase 1 done (state machine, 12 control endpoints, dashboard). Sprint 2.1 done (action endpoint, event schema). Sprint 2.2 done (test action panel, naming reconciliation). Sprints 2.3-2.5 queued. |
| M8 Public Screen | ⚠️ ~40% | — | Hex map rendering contract ready (CONTRACT_MAP_RENDERING). |
| M6 Human Interface | ❌ NOT STARTED | — | Map rendering contract ready. |
| M5 AI Participant | ⚠️ PARTIAL | — | Agent prompts updated (stability only, no political_support). **Agent tool names need reconciliation to 32 canonical action IDs.** |
| M7 Navigator | ❌ NOT STARTED | — | |
| M10 Final Assembly | ❌ NOT STARTED | — | |

## ACTION_NAMING — Canonical 32 Action Types (2026-04-16)

Source of truth: `role_actions.action_id` in DB (M9).
Dispatcher: `engine/services/action_dispatcher.py` — fully aligned.
Category map: `engine/main.py:ACTION_CATEGORIES` — fully aligned.

### Military (13)
| DB action_id | Category | Engine | Status |
|---|---|---|---|
| `ground_attack` | military | `engines/military.resolve_ground_combat` | Routed (param mismatch — v2) |
| `air_strike` | military | `engines/military.resolve_air_strike` | Routed (param mismatch — v2) |
| `naval_combat` | military | `engines/military.resolve_naval_combat` | Routed (param mismatch — v2) |
| `naval_bombardment` | military | `engines/military.resolve_naval_bombardment` | Routed (param mismatch — v2) |
| `naval_blockade` | military | `engines/military.resolve_blockade` | Routed (param mismatch — v2) |
| `launch_missile_conventional` | military | `engines/military.resolve_missile_strike` | Routed (param mismatch — v2) |
| `basing_rights` | military | `services/basing_rights_engine` | Routed |
| `martial_law` | military | `services/martial_law_engine` | Routed |
| `nuclear_test` | military | `engines/military.resolve_nuclear_test` | Routed (param mismatch — v2) |
| `move_units` | military | — | Stub (M4 Phase 4: inter-round only) |
| `nuclear_authorize` | military | — | Stub (M4 Phase 4: nuclear chain) |
| `nuclear_intercept` | military | — | Stub (M4 Phase 4: nuclear chain) |
| `nuclear_launch_initiate` | military | — | Stub (M4 Phase 4: nuclear chain) |

### Economic (6)
| DB action_id | Category | Engine | Status |
|---|---|---|---|
| `set_budget` | economic | Batch → Phase B | Queued |
| `set_tariffs` | economic | Batch → Phase B | Queued |
| `set_sanctions` | economic | Batch → Phase B | Queued |
| `set_opec` | economic | Batch → Phase B | Queued |
| `propose_transaction` | economic | `services/transaction_engine` | Routed |
| `accept_transaction` | economic | `services/transaction_engine` | Routed |

### Diplomatic (5)
| DB action_id | Category | Engine | Status |
|---|---|---|---|
| `public_statement` | diplomatic | Observatory log only | Working |
| `propose_agreement` | diplomatic | `services/agreement_engine` | Routed |
| `sign_agreement` | diplomatic | `services/agreement_engine` | Routed |
| `call_org_meeting` | diplomatic | — | Stub (M4 Phase 4) |
| `meet_freely` | diplomatic | — | Stub (M4 Phase 4) |

### Covert (2)
| DB action_id | Category | Engine | Status |
|---|---|---|---|
| `covert_operation` | covert | `services/*_engine` (by op_type) | Routed |
| `intelligence` | covert | `services/intelligence_engine` | Routed |

### Political (6)
| DB action_id | Category | Engine | Status |
|---|---|---|---|
| `arrest` | political | `services/arrest_engine` | Routed |
| `assassination` | political | `services/assassination_engine` | Routed |
| `change_leader` | political | M4 voting (logged only) | Routed |
| `reassign_types` | political | `services/power_assignments` | Routed |
| `self_nominate` | political | `services/election_engine` | Routed |
| `cast_vote` | political | `services/election_engine` | Routed |

### Stale Names REMOVED from Dispatcher (2026-04-16)
`declare_attack`, `launch_missile`, `blockade`, `covert_op`, `reassign_powers`, `submit_nomination`, `call_early_elections`, `propose_exchange`, `respond_exchange`, `set_tariff`, `set_sanction`, `set_opec_production`

## Simplification Sprint (2026-04-15) — ALL COMPLETE + RECONCILED
- A. political_support → stability only ✅ (engine, context, agents updated)
- B. personal_coins deprecated ✅ (contract updated, code marked)
- C. Relations: 5 types, 5 agreement types, auto-transitions ✅
- D. change_leader replaces coup/protest ✅ (contract, schema, dispatcher)
- E. Columbia elections: 9+bonus votes, simple majority ✅
- Cross-module reconciliation: ✅ (720 L1 tests pass)

## Active Contracts
| Contract | Version | Status |
|---|---|---|
| CONTRACT_CHANGE_LEADER | 1.0 | LOCKED 2026-04-15 |
| CONTRACT_COLUMBIA_ELECTIONS | 2.0 | LOCKED 2026-04-15 |
| CONTRACT_MAP_RENDERING | 1.0 | LOCKED 2026-04-15 |
| CONTRACT_POWER_ASSIGNMENTS | 1.0 | LOCKED 2026-04-13 |
| CONTRACT_RUN_ROLES | 1.0 | Updated 2026-04-15 (personal_coins deprecated) |
| CONTRACT_BUDGET | 1.1 | LOCKED 2026-04-10 |
| CONTRACT_SANCTIONS | 1.0 | LOCKED |
| CONTRACT_NUCLEAR_CHAIN | 1.0 | LOCKED 2026-04-13 |

## Archived Contracts (in DEPRECATED/)
- CONTRACT_COUP.md
- CONTRACT_MASS_PROTEST.md
- CONTRACT_ELECTIONS.md (v1, old camp system)
