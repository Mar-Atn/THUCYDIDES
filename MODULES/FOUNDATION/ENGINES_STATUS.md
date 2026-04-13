# Foundation: Engines Status (M1)
**25 action engines — all implemented with locked contracts**

| # | Action Type | Engine File | Contract | Validator | Tests |
|---|---|---|---|---|---|
| 1 | `move_units` | `engines/movement.py` | CONTRACT_MOVEMENT | movement_validator | L1+L2 |
| 2 | `declare_attack` (ground) | `engines/military.py:resolve_ground_combat` | CONTRACT_GROUND_COMBAT | ground_combat_validator | L1+L2 |
| 3 | `declare_attack` (air) | `engines/military.py:resolve_air_strike` | CONTRACT_AIR_STRIKES | air_strike_validator | L1+L2 |
| 4 | `declare_attack` (naval) | `engines/military.py:resolve_naval_combat` | CONTRACT_NAVAL_COMBAT | naval_combat_validator | L1+L2 |
| 5 | `declare_attack` (bombardment) | `engines/military.py:resolve_naval_bombardment` | CONTRACT_NAVAL_BOMBARDMENT_BLOCKADE | bombardment_validator | L1 |
| 6 | `blockade` | `engines/military.py:resolve_blockade` | CONTRACT_NAVAL_BOMBARDMENT_BLOCKADE | blockade_validator | L1 |
| 7 | `launch_missile` | `engines/military.py:resolve_missile_strike` | CONTRACT_NAVAL_BOMBARDMENT_BLOCKADE | missile_validator | L1 |
| 8 | `nuclear_test` | `engines/military.py:resolve_nuclear_test` | CONTRACT_NUCLEAR_CHAIN | nuclear_validator | L1+L2 |
| 9 | `martial_law` | `services/martial_law_engine.py` | CONTRACT_MARTIAL_LAW | domestic_validator | L2 |
| 10 | `basing_rights` | `services/basing_rights_engine.py` | CONTRACT_BASING_RIGHTS | basing_rights_validator | L1+L2 |
| 11 | `set_budget` | `engines/economic.py:calc_budget_execution` | CONTRACT_BUDGET | budget_validator | L1+L2+L3 |
| 12 | `set_tariff` | `engines/economic.py:calc_tariff_coefficient` | CONTRACT_TARIFFS | tariff_validator | L1+L2+L3 |
| 13 | `set_sanction` | `engines/economic.py:calc_sanctions_coefficient` | CONTRACT_SANCTIONS | sanction_validator | L1+L2+L3 |
| 14 | `set_opec` | `engines/economic.py:calc_oil_price` | CONTRACT_OPEC | opec_validator | L1+L2+L3 |
| 15 | `intelligence` | `services/intelligence_engine.py` | CONTRACT_INTELLIGENCE | covert_ops_validator | L2 |
| 16 | `sabotage` | `services/sabotage_engine.py` | CONTRACT_SABOTAGE | covert_ops_validator | L2 |
| 17 | `propaganda` | `services/propaganda_engine.py` | CONTRACT_PROPAGANDA | covert_ops_validator | L2 |
| 18 | `election_meddling` | `services/election_meddling_engine.py` | CONTRACT_ELECTION_MEDDLING | covert_ops_validator | L2 |
| 19 | `arrest` | `services/arrest_engine.py` | CONTRACT_ARREST | domestic_validator | L2 |
| 20 | `assassination` | `services/assassination_engine.py` | CONTRACT_ASSASSINATION | political_validator | L2 |
| 21 | `coup_attempt` | `services/coup_engine.py` | CONTRACT_COUP | political_validator | L2 |
| 22 | `lead_protest` | `services/protest_engine.py` | CONTRACT_MASS_PROTEST | political_validator | L2 |
| 23 | `submit_nomination` / `cast_vote` | `services/election_engine.py` | CONTRACT_ELECTIONS | political_validator | L2 |
| 24 | `call_early_elections` | `services/early_elections_engine.py` | CONTRACT_EARLY_ELECTIONS | political_validator | L2 |
| 25 | `reassign_powers` | `services/power_assignments.py` | CONTRACT_POWER_ASSIGNMENTS | — | L2 |

**Batch engines (Phase B):**
- `engines/orchestrator.py:process_round()` — 19-step economic→political→elections pipeline
- `engines/political.py:process_election()` — AI score calculation for elections
- `engines/round_tick.py` — per-round engine tick bridge

**All engine files under:** `app/engine/engines/` and `app/engine/services/`
**All contracts under:** `3 DETAILED DESIGN/CONTRACTS/`
**All validators under:** `app/engine/services/*_validator.py`
