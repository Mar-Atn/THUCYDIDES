# Foundation: Communication & Standards Layer (M2)

## Action Dispatcher
**File:** `app/engine/services/action_dispatcher.py`
**Spec:** `3 DETAILED DESIGN/DET_ACTION_DISPATCHER.md`

Routes all 25 action types to their engines. Three dispatch categories:
- **IMMEDIATE** (Phase A): combat, covert ops, domestic, political, transactions
- **BATCH** (Phase B): budget, sanctions, tariffs, OPEC
- **MOVEMENT** (Inter-Round): unit repositioning

## Validators (14 files)
All under `app/engine/services/*_validator.py`:

| Validator | Actions | Error Codes |
|---|---|---|
| movement_validator | move_units | 17 |
| budget_validator | set_budget | 36 |
| tariff_validator | set_tariff | 11 |
| sanction_validator | set_sanction | 44 |
| opec_validator | set_opec | 39 |
| ground_combat_validator | attack_ground | 33 |
| air_strike_validator | attack_air | 23 |
| naval_combat_validator | attack_naval | 14 |
| bombardment_validator | bombardment | — |
| blockade_validator | blockade | — |
| missile_validator | launch_missile | — |
| nuclear_validator | nuclear_test/launch | 17 |
| domestic_validator | arrest, martial_law | 11 |
| covert_ops_validator | intelligence, sabotage, propaganda, election_meddling | 13 |
| political_validator | assassination, coup, mass_protest, early_elections | 9 |

## Action Schemas
**File:** `app/engine/agents/action_schemas.py`
25 Pydantic v2 models. `ACTION_TYPE_TO_MODEL` dict maps action_type → model class.

## Shared Helpers
**File:** `app/engine/services/common.py`
- `safe_int(val, default)` — treats only None as missing (not 0)
- `safe_float(val, default)` — same for floats
- `get_scenario_id(client, sim_run_id)` — look up scenario for a run
- `write_event(...)` — write to observatory_events table

## Real-Time Channels (designed, not yet implemented)
Per SEED_F3 + DET_C1:
- `sim:{sim_run_id}:world` — public world state updates
- `sim:{sim_run_id}:country:{code}` — per-country private updates
- `sim:{sim_run_id}:role:{id}` — per-role private updates
- `sim:{sim_run_id}:facilitator` — moderator channel

## Event Logging
All actions log to `observatory_events` table with: sim_run_id, scenario_id, round_num, event_type, country_code, summary, payload (JSONB).

## Contracts
28 locked CONTRACT documents in `3 DETAILED DESIGN/CONTRACTS/`
5 reference CARD documents in `3 DETAILED DESIGN/CARDS/`
