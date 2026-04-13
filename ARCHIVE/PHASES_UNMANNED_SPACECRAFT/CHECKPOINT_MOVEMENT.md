# CHECKPOINT: Movement Vertical Slice (M1)

**Status:** ✅ DONE end-to-end
**Date:** 2026-04-11
**Owner:** Marat + Build Team
**Authoritative contract:** `CONTRACT_MOVEMENT.md` v1.0 (🔒 locked)
**Methodology:** `EVOLVING METHODOLOGY/VERTICAL_SLICE_PATTERN.md` v1.1

This is the durable record of the **first military vertical slice** — unit movement. Same 7-step pattern as the 4 economic slices (Budget / Tariffs / Sanctions / OPEC), but with a net new production engine and a mandatory **full legacy cleanup pass** as part of the close. This is also the first slice that required renaming an unrelated function (`military.resolve_mobilization` → `resolve_martial_law`) to eliminate a naming collision exposed by the cleanup.

---

## 1. Scope

The M1 slice covers **unit movement** — between-round repositioning, deployment from reserve, withdrawal to reserve, and the engine-detected auto-embark / auto-debark flows:

- **Reposition** — active unit → new hex
- **Deploy from reserve** — reserve unit → hex (becomes active)
- **Withdraw to reserve** — active unit → reserve pool (invisible, unavailable next round)
- **Auto-embark** — ground / tactical_air moving onto a hex with a friendly carrier with capacity → auto-loaded
- **Debark + move** — embarked unit's hex order debarks first, then applies the target

**Not in scope** (separate future slices):
- Combat / attack advance (M2 `declare_attack`)
- Martial law conscription pool (handled by the renamed `military.resolve_martial_law`)
- Transit-time delays, supply / fuel, stacking limits — all deferred
- Naval chokepoint-transit blocking — M5 Blockade
- Cognitive blocks (identity / memory / goals / rules) — AI Participant Module v1.0

---

## 2. Design decisions locked (Marat Q1–Q6 pre-slice)

| # | Question | Decision |
|---|---|---|
| **Q1** | Singular vs plural action name | **`move_units` (PLURAL)**. Full replacement for legacy singular `move_unit`. No backward compatibility. Clean audit per Marat's directive. |
| **Q2** | Range constraint | **UNLIMITED.** No hex-distance limit. Per CARD_ACTIONS §1.1 "all units can be relocated globally to any suitable hex". Spatial legality is type-based + territory-based. The old `MOVE_RANGE = {ground: 1, naval: 2, ...}` table is abandoned. |
| **Q3** | Transit delay | **Zero.** Moves submitted in round N take effect at the start of round N+1. No transit-time mechanic. |
| **Q4** | Batch semantics | **One `move_units` action per country per round**, atomic validation. Any invalid move rejects the entire batch with all errors reported. Batch-internal state propagation (move #1's new position qualifies move #2's "previously occupied" check). |
| **Q5** | Multiple submissions | **Last-submission-wins.** Second submission replaces first via document-order collection in resolve_round. Supports human correction workflows. |
| **Q6** | Embark/debark representation | **Engine-detected, not schema-exposed.** Participant says "move unit X to hex Y"; if hex Y has a friendly carrier with capacity → auto-embark; if X is currently embarked → auto-debark first. Carrier capacity: 1 ground + 2 tactical_air per naval. |

---

## 3. What changed

### 3.1 Engine

**NEW:** `app/engine/engines/movement.py` — the canonical production engine, replacing the deprecated `round_engine/movement.py` (deleted).

```python
def process_movements(
    moves: list[dict],
    country_code: str,
    units: dict[str, dict],   # MUTATED in place
    zones: dict,
) -> list[dict]:              # list of per-move result dicts
    ...
```

Per-move apply logic (per CONTRACT §6.2):
- `target == "reserve"` → withdraw (clear coords + embarked_on, status=reserve)
- `target == "hex"` →
  1. If status=embarked, clear embarked_on first (debark).
  2. Check if the target hex has a friendly carrier with capacity for this unit type. If yes → auto-embark (pick carrier with most remaining capacity).
  3. Otherwise → normal hex move / deploy. Set coords, auto-derive theater from the canonical theater-link table in `engine/config/map_config.py`.

Carrier capacity:

```python
def _carrier_capacity_remaining(carrier: dict, all_units: dict) -> int:
    g, a = _carrier_embark_counts(carrier["unit_code"], all_units)
    return max(0, 1 - g) + max(0, 2 - a)   # 1 ground + 2 tactical_air
```

### 3.2 Services

| Service | File | Purpose |
|---|---|---|
| **Validator** | `engine/services/movement_validator.py` | `validate_movement_decision(payload, units, zones, basing_rights) → {valid, errors, warnings, normalized}`. **17 error codes**. Pure, context-dependent, batch-atomic, state-propagating. Already shipped in Step 2 (pre-close). |
| **Data loaders** | `engine/services/movement_data.py` | `load_global_grid_zones()` (cached — synthesizes per-hex zones dict from `2 SEED/C_MECHANICS/C1_MAP/SEED_C1_MAP_GLOBAL_STATE_v4.json`), `load_basing_rights(client)`, `build_units_dict_from_rows(rows)`. |
| **Context builder** | `engine/services/movement_context.py` | `build_movement_context(country_code, scenario_code, round_num) → dict`. Returns 10 data blocks per CONTRACT §3: economic_state, my_units, own_territory, basing_rights_i_have, previously_occupied_hexes, recent_combat_events, world_zone_map (57 zones), zone_adjacency, decision_rules, instruction. **Data only — no cognitive layer.** |

### 3.3 Persistence

**Migration:** `movement_v1_canonical_schema` (applied 2026-04-11)

```sql
ALTER TABLE country_states_per_round
  ADD COLUMN IF NOT EXISTS movement_decision jsonb;

COMMENT ON COLUMN country_states_per_round.movement_decision IS
  'Per-round record of the move_units decision (CONTRACT_MOVEMENT v1.0).';

DELETE FROM agent_decisions WHERE action_type IN ('move_unit', 'mobilize_reserve');
-- (7 stale rows deleted)
```

**Resolve handler:** `engine/round_engine/resolve_round.py` movement block fully rewritten.
- `MOVEMENT_ACTIONS = {"move_units"}` (plural)
- `MOBILIZATION_ACTIONS` constant deleted entirely
- `from engine.round_engine import movement as movement_mod` removed
- New handler collects all `move_units` decisions per country (last-in-document-order wins), builds units + zones + basing context dicts, calls the validator, emits `movement_rejected` events on invalid, writes `movement_decision` JSONB on valid (both change and no_change paths), calls `process_movements` on change, emits `movement_applied` / `movement_no_change` events

### 3.4 Legacy cleanup (exhaustive)

| File | Action |
|---|---|
| `engine/round_engine/movement.py` | **DELETED** (whole file — deprecated Phase-1 MVP) |
| `engine/round_engine/test_resolve.py` | **DELETED** (old test scaffold) |
| `engine/round_engine/resolve_round.py` | Movement block rewritten, legacy import + constant removed |
| `engine/round_engine/spec_compliance.md` | Movement row updated to point at new engine + CONTRACT |
| `engine/engines/military.py` | Renamed `resolve_mobilization` → `resolve_martial_law`, `MobilizationInput` → `MartialLawInput`, `MobilizationResult` → `MartialLawResult` (eliminates naming collision) |
| `engine/agents/action_schemas.py` | Replaced `MoveOrder` + `MobilizeOrder` Pydantic models with a single `MoveUnitsOrder` envelope shim |
| `engine/agents/tools.py` | `commit_action` dispatch rewritten — legacy pair removed, `move_units` added |
| `engine/agents/stage4_test.py` | Action-list text updated |
| `tests/layer2/test_battery.py` | Migrated Columbia reserve deploy to `move_units` v1.0 schema |
| `tests/layer2/test_battery_military.py` | Same — migrated to `move_units` |
| `tests/layer3/test_skill_action_selection.py` | Removed `move_unit` + `mobilize_reserve` from action list; replaced with `move_units` |
| DB `agent_decisions` | 7 stale rows with legacy action_types deleted |

---

## 4. Test coverage (acceptance evidence)

| Layer | File | Count | Purpose |
|---|---|---|---|
| **L1** | `tests/layer1/test_movement_validator.py` | **42** | All 17 error codes + batch-internal state propagation (previously-occupied chaining, embark capacity across batch) |
| **L1** | `tests/layer1/test_movement_engine.py` | **10** | Reposition, deploy-from-reserve, withdraw, auto-embark, debark+move, atomic batch, theater auto-derivation |
| **L2** | `tests/layer2/test_movement_persistence.py` | **4** | Change decision persisted; no_change audit + unit preservation; invalid rejected event; last-submission-wins |
| **L2** | `tests/layer2/test_movement_context.py` | **10** | 10 context blocks present; 57-zone world map; zone adjacency; decision rules with no_change reminder |
| **L3** | `tests/layer3/test_skill_movement.py` | **4 offline + 1 LLM** | D5 prompt v1.0 markers; reference change + no_change payloads validated by production validator; min rationale constant |
| **L3** | `tests/layer3/test_movement_full_chain_ai.py` | **1** | **THE acceptance gate** — real LLM → validator → DB → engine → snapshot. Visual demo rounds 200-201 **LEFT IN DB**. |

**Totals:** 71 new/migrated tests green. Full L1 suite: 458 passing.

---

## 5. Concrete demo (2026-04-11 acceptance gate run)

Columbia R200 → R201, real LLM decision:

```json
{
  "action_type": "move_units",
  "country_code": "columbia",
  "round_num": 201,
  "decision": "change",
  "rationale": "Deploying ground forces to secure both territories and establish defensive positions across our controlled hexes for better territorial control.",
  "changes": {
    "moves": [
      {"unit_code": "col_g_04", "target": "hex",
       "target_global_row": 3, "target_global_col": 3},
      {"unit_code": "col_g_05", "target": "hex",
       "target_global_row": 4, "target_global_col": 3}
    ]
  }
}
```

**Persistence + engine result:**
- `movement_decision` JSONB byte-for-byte matches normalized AI output ✅
- `col_g_04`: R200 reserve/(None,None) → R201 active/(3,3) ✅
- `col_g_05`: R200 reserve/(None,None) → R201 active/(4,3) ✅
- `movement_applied` observatory event emitted ✅

**Visual demo rounds 200-201 LEFT IN DB for Marat's Observatory review.** They can be scrubbed via the existing round selector in the Observatory and will show Columbia's new deployments on the global map.

---

## 6. What this slice proves

1. **The 7-step pattern generalizes beyond economic decisions.** All 4 economic slices (Budget / Tariffs / Sanctions / OPEC) used the same pattern. M1 is the first military slice and re-uses the pattern without modification — contract → validator → engine → persistence → context → harness → acceptance gate → closing.
2. **Aggressive legacy cleanup is non-negotiable** in the close step. Naming collisions (`resolve_mobilization` vs `resolve_mobilization`), orphan Pydantic models, stale DB rows, legacy prompt text — all removed in the same commit as the slice is shipped. Principle Zero (fight entropy) in action.
3. **Context-dependent validators work.** Movement legality is state-dependent (own territory, basing rights, previously occupied hex, friendly carrier capacity), so the validator needs context dicts that the caller pre-builds. The signature `validate_movement_decision(payload, units, zones, basing_rights)` keeps the validator pure while letting the caller source context from anywhere (DB for production, fixtures for tests).
4. **Batch-internal state propagation** is a real requirement. Move #1 putting a unit on hex (3, 3) must make (3, 3) a "previously occupied" hex for move #2 in the same batch. The validator simulates the batch in order on a deep-copy of `units` to support this cleanly.

---

## 7. Pointers (copy-pasteable)

```
# Contract
PHASES/UNMANNED_SPACECRAFT/CONTRACT_MOVEMENT.md           🔒 v1.0

# Engine (NEW — replaces deprecated round_engine/movement.py which is DELETED)
app/engine/engines/movement.py                            process_movements + helpers
app/engine/engines/military.py                            resolve_martial_law (renamed from resolve_mobilization)

# Persistence handler
app/engine/round_engine/resolve_round.py                  movement block (v1.0 rewrite)

# Services
app/engine/services/movement_validator.py                 17 error codes, batch-atomic
app/engine/services/movement_data.py                      zones + basing_rights loaders
app/engine/services/movement_context.py                   build_movement_context (decision-specific, data only)

# Tests
app/tests/layer1/test_movement_validator.py               42 tests (shipped in Step 2)
app/tests/layer1/test_movement_engine.py                  10 tests (NEW)
app/tests/layer2/test_movement_persistence.py             4 tests (NEW)
app/tests/layer2/test_movement_context.py                 10 tests (NEW)
app/tests/layer3/test_skill_movement.py                   4 offline + 1 LLM (NEW)
app/tests/layer3/test_movement_full_chain_ai.py           acceptance gate (NEW, visual demo rounds persist)

# Docs reconciled
PHASES/UNMANNED_SPACECRAFT/CARD_ACTIONS.md                §1.1 rewritten with v1.0 schema
PHASES/UNMANNED_SPACECRAFT/PHASE.md                       M1 DONE status block added
2 SEED/D_ENGINES/SEED_D8_ENGINE_FORMULAS_v1.md            Part 6B reconciliation note (CARD wins)
CONCEPT TEST/CHANGES_LOG.md                               MOVEMENT VERTICAL SLICE — DONE entry

# DB migration
movement_v1_canonical_schema                              Applied 2026-04-11 to Supabase project lukcymegoldprbovglmn
```

---

## 8. Next — M2 Ground Combat

```
✅ Budget       DONE  2026-04-10
✅ Tariffs      DONE  2026-04-10
✅ Sanctions    DONE  2026-04-10
✅ OPEC         DONE  2026-04-11
✅ Movement M1  DONE  2026-04-11  ← FIRST MILITARY SLICE
---
   M2: Ground Combat (declare_attack)  ← NEXT
   M3: Air / Missile Strikes
   M4: Naval Combat
   M5: Blockades
   Nuclear Decisions
   Transactions + Agreements
   Other Actions (fire/reassign / assassination / arrest / propaganda / sabotage / private investments)
```

**Milestone:** with M1 movement shipped, the military decision layer has its first slice complete. The 7-step pattern now has a proven military exemplar. All 4 economic + 1 military mandatory decisions in the sim now have canonical contracts, validators, engines, decision-specific context builders, persistence handlers, AI skill harnesses, and full-chain acceptance gates.
