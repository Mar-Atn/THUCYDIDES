# Foundation: Communication & Standards Layer (M2)

**Last verified:** 2026-04-23 | **Source of truth:** `MODULE_REGISTRY.md` ACTION_NAMING section

---

## Action Dispatcher

**File:** `app/engine/services/action_dispatcher.py`
**Entry point:** `dispatch_action()` — single routing function for all 33 canonical action types.

Three dispatch modes:
- **IMMEDIATE** (Phase A): combat, covert, diplomacy, political, transactions
- **BATCH** (Phase B): budget, sanctions, tariffs, OPEC — queued in Phase A, processed by economic engine
- **MOVEMENT** (Phase A + inter-round): unit repositioning

---

## Canonical Action Types (33)

### Military — Combat (6)
| Action | Engine |
|--------|--------|
| `ground_attack` | `engines/military.resolve_ground_combat` |
| `ground_move` | `action_dispatcher._ground_advance` |
| `air_strike` | `engines/military.resolve_air_strike` |
| `naval_combat` | `engines/military.resolve_naval_combat` |
| `naval_bombardment` | `engines/military.resolve_naval_bombardment` |
| `launch_missile_conventional` | `engines/military.resolve_missile_strike` |

### Military — Non-Combat (7)
| Action | Engine |
|--------|--------|
| `move_units` | `engines/movement.process_movements` |
| `naval_blockade` | `services/blockade_engine` |
| `basing_rights` | `services/basing_rights_engine` |
| `martial_law` | `services/martial_law_engine` |
| `nuclear_test` | `engines/military.resolve_nuclear_test` |
| `nuclear_launch_initiate` | `orchestrators/nuclear_chain` |
| `nuclear_authorize` / `nuclear_intercept` | `orchestrators/nuclear_chain` |

### Economic (6)
| Action | Engine |
|--------|--------|
| `set_budget` | Batch -> Phase B |
| `set_tariffs` | Batch -> Phase B |
| `set_sanctions` | Batch -> Phase B |
| `set_opec` | Batch -> Phase B |
| `propose_transaction` | `services/transaction_engine` |
| `accept_transaction` | `services/transaction_engine` |

### Diplomatic (5)
| Action | Engine |
|--------|--------|
| `public_statement` | Observatory log only |
| `declare_war` | `action_dispatcher._declare_war()` |
| `propose_agreement` | `services/agreement_engine` |
| `sign_agreement` | `services/agreement_engine` |
| `call_org_meeting` | `action_dispatcher._create_meeting_invitation` |

### Covert (2)
| Action | Engine |
|--------|--------|
| `covert_operation` | `engines/military` (subtypes: sabotage, propaganda) |
| `intelligence` | AI-generated analytical report |

### Political (6)
| Action | Engine |
|--------|--------|
| `arrest` | `services/arrest_engine` (moderator confirmation) |
| `assassination` | `engines/political.resolve_assassination` (moderator confirmation) |
| `change_leader` | `services/change_leader` (3-phase voting) |
| `reassign_types` | `services/power_assignments` |
| `self_nominate` | `services/election_engine` |
| `cast_vote` | `services/election_engine` |

### Reactive / System (8, not player-initiated)
`release_arrest`, `respond_meeting`, `invite_to_meet`, `set_meetings`, `meet_freely`, `withdraw_nomination`, `cast_election_vote`, `resolve_election`

---

## Validation Layer

**Schemas:** `app/engine/agents/action_schemas.py` — Pydantic v2 models, one per action type. `ACTION_TYPE_TO_MODEL` dict maps canonical name to model class.
**Contract tests:** `app/tests/test_action_contracts.py` — verifies dispatcher routes all action types.
**Category map:** `app/engine/main.py:ACTION_CATEGORIES` — aligned with this document.

---

## Event System

**Observatory events:** `observatory_events` table. All actions log: sim_run_id, round_num, event_type, country_code, summary, payload (JSONB). Public screen reads only events with public visibility.

**Agent event queue:** AI participants receive events through `agent_event_queue` — filtered by country and visibility. Drives AI situational awareness each cognitive cycle.

---

## Real-Time Channels

**Implementation:** Supabase Realtime (WebSocket push). See `MODULES/M2_REALTIME/SPEC_M2_REALTIME.md`.

- 5 DB tables in realtime publication with RLS policies
- Frontend hooks: `useRealtimeTable`, `useRealtimeRow` (zero polling)
- Auth token caching (5-min TTL) to avoid `getSession()` blocking
- `PendingResultPoller` endpoint for reliable result delivery
