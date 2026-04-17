# MODULE REGISTRY — Live Status
**Last updated:** 2026-04-16

| Module | Status | SPEC | Progress |
|---|---|---|---|
| M1 World Model Engines | ⚠️ MOSTLY ALIGNED | N/A | 720 L1 tests passing. `SCHEDULED_EVENTS` deprecated → orchestrator reads `sim_runs.key_events`. Ground + air combat wired to DB (coordinate-based). Naval combat partially wired. **Legacy Input models in military.py still use zone_id** — refactor when bombardment/blockade/missile are fully wired. |
| M2 Communication & Standards | ✅ ALIGNED | N/A | **32 canonical action types** reconciled across DB, dispatcher, category map. 3 active contracts + 3 archived. Action dispatcher routes all 32 types. Visibility model: public/secret on agreements + transactions. |
| M3 Data Foundation | ✅ ALIGNED | N/A | **Individual unit model**: 345 units (1 row per unit) with hex coordinates from canonical `units.csv`. SimRun creation copies 11 tables. `deployments` table has `global_row/col`, `theater/row/col`, `unit_id`, `unit_status`. `zone_id` deprecated for positioning. |
| M10.1 Auth | ✅ DONE | ✅ | Email/password + Google OAuth, RLS, GDPR consent. All FK constraints CASCADE on sim_run delete. |
| M9 Sim Setup | ✅ v2 DONE | ✅ | 10-tab Template Editor, SimRun wizard (server-side data inheritance, 11 tables), User Mgmt, AI Setup. 40 roles (5 position types), 32 action types, country/role briefs. |
| M4 Sim Runner | ✅ DONE | ✅ | All 5 phases. 43+ API endpoints, Supabase Realtime, confirmation queue, change_leader voting, nuclear chain, physical dice, AI stub, participant assignment, restart/rollback, two-column dashboard. |
| M8 Public Screen | ⚠️ ~90% | ✅ | Global map (sim-run-aware, blast markers 💥, clean embed mode), theater rotation on combat, 4 doomsday gauges (placeholder — LLM calculation TODO at Phase B), Columbia-Cathay power trend, 2-line news ticker (public events only, sorted by significance). **Remaining: LLM indices (wired at Phase B engine review).** |
| M6 Human Interface | ❌ NOT STARTED | — | Clean map embed ready (`?display=clean&sim_run_id=`). |
| M5 AI Participant | ⚠️ STUB | — | AI stub submits default decisions (budget, public_statement, OPEC). Agent tool names need reconciliation. Full LLM agent wiring pending. |
| M7 Navigator | ❌ NOT STARTED | — | |
| M10 Final Assembly | ❌ NOT STARTED | — | |

---

## ARCHITECTURE DECISIONS (2026-04-16)

### Individual Unit Model
- **Decision:** Each deployment row = 1 unit (was: aggregate counts per zone)
- **Source of truth:** `2 SEED/C_MECHANICS/C4_DATA/units.csv` (345 units, manually curated positions)
- **DB columns:** `unit_id, global_row, global_col, theater, theater_row, theater_col, embarked_on, unit_status`
- **Impact:** All deployment queries, map renderer, combat dispatcher, sim_create.py, template editor
- **Status:** Fully implemented across all layers

### Coordinate-Based Positioning
- **Decision:** Units positioned by hex coordinates `(global_row, global_col)`, not zone_id
- **zone_id:** Deprecated for deployment positioning. Preserved ONLY for named game entities (chokepoints, blockade targets)
- **Combat:** Dispatcher targets by `(target_row, target_col)`. Loads units from DB at that hex.
- **Map:** Reads coordinates directly from `/api/sim/{id}/map/units` — zero translation
- **Status:** Fully implemented. 181 active units on 68 distinct hex positions.

### Information Visibility
- **Decision:** Public screen only shows public events. Covert ops, secret agreements, intelligence — hidden.
- **DB:** `agreements.visibility`, `exchange_transactions.visibility` (public|secret)
- **Observatory events:** `payload.visibility` checked for agreements on public screen
- **Covert ops:** Never on public screen. Future: `covert_op_revealed` event type when engine detects exposure.

---

## ACTION_NAMING — Canonical 32 Action Types (2026-04-16)

Source of truth: `role_actions.action_id` in DB (M9).
Dispatcher: `engine/services/action_dispatcher.py` — fully aligned.
Category map: `engine/main.py:ACTION_CATEGORIES` — fully aligned.

### Military (13)
| DB action_id | Category | Engine | Status |
|---|---|---|---|
| `ground_attack` | military | `engines/military.resolve_ground_combat` | **Working** — DB units, losses applied |
| `air_strike` | military | `engines/military.resolve_air_strike` | **Working** — DB units, losses applied |
| `naval_combat` | military | `engines/military.resolve_naval_combat` | Routed (unit_code format issue) |
| `naval_bombardment` | military | `engines/military.resolve_naval_bombardment` | Acknowledged (Input object needed) |
| `naval_blockade` | military | `engines/military.resolve_blockade` | Acknowledged (Input object needed) |
| `launch_missile_conventional` | military | `engines/military.resolve_missile_strike` | Acknowledged (Input object needed) |
| `basing_rights` | military | `services/basing_rights_engine` | Routed |
| `martial_law` | military | `services/martial_law_engine` | Routed |
| `nuclear_test` | military | `engines/military.resolve_nuclear_test` | Routed (Input object needed) |
| `move_units` | military | — | Stub (inter-round only) |
| `nuclear_authorize` | military | `orchestrators/nuclear_chain` | Wired |
| `nuclear_intercept` | military | `orchestrators/nuclear_chain` | Wired |
| `nuclear_launch_initiate` | military | `orchestrators/nuclear_chain` | Wired |

### Economic (6)
| DB action_id | Category | Engine | Status |
|---|---|---|---|
| `set_budget` | economic | Batch → Phase B | Queued to `agent_decisions` |
| `set_tariffs` | economic | Batch → Phase B | Queued to `agent_decisions` |
| `set_sanctions` | economic | Batch → Phase B | Queued to `agent_decisions` |
| `set_opec` | economic | Batch → Phase B | Queued to `agent_decisions` |
| `propose_transaction` | economic | `services/transaction_engine` | Routed |
| `accept_transaction` | economic | `services/transaction_engine` | Routed |

### Diplomatic (5)
| DB action_id | Category | Engine | Status |
|---|---|---|---|
| `public_statement` | diplomatic | Observatory log only | **Working** |
| `propose_agreement` | diplomatic | `services/agreement_engine` | Routed |
| `sign_agreement` | diplomatic | `services/agreement_engine` | Routed |
| `call_org_meeting` | diplomatic | — | Stub |
| `meet_freely` | diplomatic | — | Stub |

### Covert (2)
| DB action_id | Category | Engine | Status |
|---|---|---|---|
| `covert_operation` | covert | `services/*_engine` (by op_type) | Routed |
| `intelligence` | covert | `services/intelligence_engine` | Routed |

### Political (6)
| DB action_id | Category | Engine | Status |
|---|---|---|---|
| `arrest` | political | `services/arrest_engine` | Routed (requires confirmation) |
| `assassination` | political | `services/assassination_engine` | Routed (requires confirmation) |
| `change_leader` | political | `services/change_leader` | **Working** (3-phase voting) |
| `reassign_types` | political | `services/power_assignments` | Routed |
| `self_nominate` | political | `services/election_engine` | Routed |
| `cast_vote` | political | `services/election_engine` | Routed |

### Stale Names REMOVED (2026-04-16)
`declare_attack`, `launch_missile`, `blockade`, `covert_op`, `reassign_powers`, `submit_nomination`, `call_early_elections`, `propose_exchange`, `respond_exchange`, `set_tariff`, `set_sanction`, `set_opec_production`

---

## Active Contracts
| Contract | Version | Status |
|---|---|---|
| CONTRACT_CHANGE_LEADER | 1.0 | LOCKED 2026-04-15. Implemented in M4 (3-phase voting). |
| CONTRACT_COLUMBIA_ELECTIONS | 2.0 | LOCKED 2026-04-15 |
| CONTRACT_MAP_RENDERING | 1.0 | LOCKED 2026-04-15. **Updated: clean display mode, sim_run_id param, blast markers.** |
| CONTRACT_POWER_ASSIGNMENTS | 1.0 | LOCKED 2026-04-13 |
| CONTRACT_RUN_ROLES | 1.0 | Updated 2026-04-15 (personal_coins deprecated) |
| CONTRACT_BUDGET | 1.1 | LOCKED 2026-04-10 |
| CONTRACT_SANCTIONS | 1.0 | LOCKED |
| CONTRACT_NUCLEAR_CHAIN | 1.0 | LOCKED 2026-04-13. Wired to dispatcher + API in M4. |

## Archived Contracts (in DEPRECATED/)
- CONTRACT_COUP.md
- CONTRACT_MASS_PROTEST.md
- CONTRACT_ELECTIONS.md (v1, old camp system)
