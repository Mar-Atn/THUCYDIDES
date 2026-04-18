# MODULE REGISTRY — Live Status
**Last updated:** 2026-04-18

| Module | Status | SPEC | Progress |
|---|---|---|---|
| M1 World Model Engines | ⚠️ MOSTLY ALIGNED | N/A | 720 L1 tests passing. `SCHEDULED_EVENTS` deprecated → orchestrator reads `sim_runs.key_events`. **All 5 combat types fully wired to DB (2026-04-17):** ground (RISK dice), air strike (12%/6% hit), naval (1v1 dice), naval bombardment (10%/unit), missile launch (two-phase: 50% AD intercept then 75% hit, 4 target types, range by nuc tier). `hex_range()` BFS + `ATTACK_RANGE` per unit type. Theater-level adjacency. **Territory & capture (2026-04-18):** `hex_control` table for persistent occupation, unit capture mechanics (non-ground trophies), ground movement (land-only adjacency, leave-1-behind), `GLOBAL_SEA_HEXES`/`THEATER_SEA_HEXES` + `is_sea_hex()`, `GLOBAL_HEX_OWNERS` + `hex_owner()`. Basing rights respected (not treated as occupation). **Naval blockade (2026-04-18):** `blockade_engine.py` (establish/lift/reduce/integrity check), 3 chokepoints, auto-integrity check after all combat, restart cleans blockades. **Conventional missile (2026-04-18):** two-phase model (AD interception 50% per AD unit BEFORE hit roll 75% flat), 4 target choices (military/infrastructure/nuclear_site/AD), range per nuc tier (T1≤2, T2≤4, T3 global), constants `MISSILE_HIT_PROB=0.75`, `MISSILE_AD_INTERCEPT_PROB=0.50`. **Martial law (2026-04-18):** rewired to deployments+countries tables, 4 eligible countries, one-time enforcement. **Theater-aware combat (2026-04-18):** all combat types send theater info from theater map, dispatcher loads defenders by theater coords, blast markers include theater coords. **Combat modifiers fix (2026-04-18):** modifiers now applied (were display-only). **Pydantic model_dump() (2026-04-18):** all combat results. Standardized `attacker_unit_codes` across all types. Auto-attack ON skips dice queue. Naval/air once-per-round enforcement. Result labels per attack type (Victory/Defeat, Target Hit/Missed, etc.). |
| M2 Communication & Standards | ✅ ALIGNED | N/A | **33 canonical action types** reconciled across DB, dispatcher, category map (+`declare_war` added 2026-04-17). 3 active contracts + 3 archived. Action dispatcher routes all 33 types. Visibility model: public/secret on agreements + transactions. |
| M2 Realtime | ✅ DONE | ✅ | **SPEC_M2_REALTIME.md created (2026-04-18).** Full WebSocket push architecture. DB: 5 tables added to realtime publication, RLS policies, REPLICA IDENTITY FULL. Hook library: `useRealtimeTable`, `useRealtimeRow` (zero polling). FacilitatorDashboard refactored: 3 manual channels + 2 polls → 3 hooks (-237 lines). ParticipantDashboard refactored: 1 channel + 2 polls → hooks + round-based refresh. Auth token caching: `getSession()` was blocking during realtime traffic, now cached 5min. **PendingResultPoller (2026-04-18):** FastAPI endpoint for reliable result delivery. |
| M3 Data Foundation | ✅ ALIGNED | N/A | **Individual unit model**: 345 units (1 row per unit) with hex coordinates from canonical `units.csv`. SimRun creation copies 11 tables. `deployments` table has `global_row/col`, `theater/row/col`, `unit_id`, `unit_status`. `zone_id` deprecated for positioning. |
| M10.1 Auth | ✅ DONE | ✅ | Email/password + Google OAuth, RLS, GDPR consent. All FK constraints CASCADE on sim_run delete. |
| M9 Sim Setup | ✅ v2 DONE | ✅ | 10-tab Template Editor, SimRun wizard (server-side data inheritance, 11 tables), User Mgmt, AI Setup. 40 roles (5 position types), 32 action types, country/role briefs. |
| M4 Sim Runner | ✅ DONE | ✅ | All 5 phases. 43+ API endpoints, Supabase Realtime, confirmation queue, change_leader voting, nuclear chain, physical dice, AI stub, participant assignment, restart/rollback, two-column dashboard. **Post-phase (2026-04-17):** auto-attack toggle, dice mode toggle (red pulsing), `auto_attack` column on `sim_runs`, attack targeting APIs (`valid-targets` BFS, `preview` with modifiers/probability), map attack mode (postMessage protocol), combat pending cards with dice input, `/api/sim/{id}/state` public endpoint. `SimRun` type updated with `auto_approve`, `auto_attack`, `dice_mode`. **Post-phase (2026-04-18):** `hex_control` table + `GET /api/sim/{id}/map/hex-control` API. Ground movement (`ground_move` action, 100% probability, land-only adjacency). Unit capture on advance/victory. Basing rights vs occupation distinction. **Combat modifier fix (2026-04-18):** modifiers (AI L4, low morale, air support) now computed before pending/immediate branch and stored in engine format — were displayed but NOT passed to engine. **Restart simulation (2026-04-18):** full reset re-copies 11 tables (countries, deployments, relationships, sanctions, tariffs, zones, organizations, org_memberships, artefacts) + deletes agreements, exchange_transactions, hex_control, observatory_events, pending_actions; page reload clears frontend. **Pending action race condition (2026-04-18):** resolved actions kept visible 30s, result stored on pending_action row for reliable delivery. **FastAPI body parsing fix (2026-04-18):** `body: dict = {}` was never parsed as JSON; all endpoints now use `Request.json()`. |
| M8 Public Screen | ⚠️ ~90% | ✅ | Global map (sim-run-aware, blast markers, clean embed mode), theater rotation on combat, 4 doomsday gauges (placeholder — LLM calculation TODO at Phase B), Columbia-Cathay power trend, 2-line news ticker (public events only, sorted by significance). **Blast markers (2026-04-18):** `loadCombatEvents()` loads action+result payload paths, current round only, refreshes on unit changes, all map instances, theater-aware coords. **Blockade map visual (2026-04-18):** red border (dashed partial, solid full). **Remaining: LLM indices (wired at Phase B engine review).** |
| M6 Human Interface | ⚠️ IN PROGRESS | ✅ | **Sprint 6.7 DONE (2026-04-18).** Unified Attack system: single "Attack" button → map-based UX (click hex → select units → targets → preview → confirm). 5 combat types fully wired (ground/air/naval/bombardment/missile). Theater-level adjacency (10x10). postMessage protocol. Moderator auto-attack + dice mode toggles. Combat preview. Declare War action. **Territory occupation (2026-04-18):** `hex_control` table, diagonal stripe overlay on map, `GET /api/sim/{id}/map/hex-control`. **Unit capture:** non-ground enemies captured as trophies on advance/victory, shown as icons + "-> reserve". **Ground movement:** land-only adjacency (`GLOBAL_SEA_HEXES`), leave-1-behind rule, embarked units can land. **Attack UX:** side-by-side layout (25% sidebar / 75% map), SVG unit icons, 5 navy-blue assessment squares, Victory/Defeat labels, theater switcher in header. **Conventional missile (2026-04-18):** target choice radio buttons (military/infrastructure/nuclear_site/AD), nuclear_site conditional on target having R&D, range display by nuc tier. **Naval blockade (2026-04-18):** BlockadeForm with 3 chokepoint cards, establish/lift actions. **Martial law (2026-04-18):** MartialLawForm with eligibility check (4 countries). **Blast markers (2026-04-18):** combat events on all map instances, current round only. **Blockade renamed (2026-04-18):** "Naval Blockade" → "Blockade" in UI. **Result labels (2026-04-18):** per attack type (Victory/Defeat, Target Hit/Missed, Blockade Established, etc.). |
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

## ACTION_NAMING — Canonical 33 Action Types (2026-04-17)

Source of truth: `role_actions.action_id` in DB (M9).
Dispatcher: `engine/services/action_dispatcher.py` — fully aligned.
Category map: `engine/main.py:ACTION_CATEGORIES` — fully aligned.

### Military (13)
| DB action_id | Category | Engine | Status |
|---|---|---|---|
| `ground_attack` | military | `engines/military.resolve_ground_combat` | **Working** — DB units, losses applied |
| `air_strike` | military | `engines/military.resolve_air_strike` | **Working** — DB units, losses applied |
| `naval_combat` | military | `engines/military.resolve_naval_combat` | **Working** — 1v1 dice, ties→defender, DB losses |
| `naval_bombardment` | military | `engines/military.resolve_naval_bombardment` | **Working** — 10% per naval unit, DB losses |
| `naval_blockade` | military | `services/blockade_engine` | **Working** — establish/lift/reduce/integrity check, 3 chokepoints, auto-integrity after combat |
| `launch_missile_conventional` | military | `engines/military.resolve_missile_strike` | **Working** — two-phase model: AD interception (50% per AD) then hit roll (75% flat), 4 targets (military/infrastructure/nuclear_site/AD), range by nuc tier (T1≤2, T2≤4, T3 global), missile consumed |
| `basing_rights` | military | `services/basing_rights_engine` | Routed |
| `martial_law` | military | `services/martial_law_engine` | **Working** — 4 eligible countries (Sarmatia 10, Cathay 10, Persia 8, Ruthenia 6), deployments+countries tables, one-time enforcement with martial_law_declared flag |
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

### Diplomatic (6)
| DB action_id | Category | Engine | Status |
|---|---|---|---|
| `public_statement` | diplomatic | Observatory log only | **Working** |
| `declare_war` | diplomatic | `action_dispatcher._declare_war()` | **Working** — sets both directions at_war, observatory event |
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
