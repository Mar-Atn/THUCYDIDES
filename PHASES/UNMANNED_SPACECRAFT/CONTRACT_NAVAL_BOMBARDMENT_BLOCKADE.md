# CONTRACT: Naval Bombardment + Blockade

**Status:** 🔒 **LOCKED** (2026-04-12) | **Version:** 1.0 | **Owner:** Marat
**Source:** `CARD_ACTIONS.md` §1.7 (bombardment) + §1.10 (blockade) + `CARD_FORMULAS.md` D.4 + D.8

---

## PART A — Naval Bombardment (`attack_bombardment`)

### A.1 Purpose

Naval units on a sea hex fire at an adjacent land hex. Each naval unit has a **10% chance** to destroy one random ground unit on the target hex. No AD interaction. No dice — probability roll per unit.

### A.2 Decision Schema

```json
{
  "action_type": "attack_bombardment",
  "country_code": "columbia",
  "round_num": 3,
  "decision": "change",
  "rationale": "string >= 30 chars",
  "changes": {
    "naval_unit_codes": ["col_n_01", "col_n_02"],
    "target_global_row": 3,
    "target_global_col": 3
  }
}
```

### A.3 Validation — `validate_bombardment(payload, units, zones)`

| Code | Rule |
|---|---|
| `INVALID_PAYLOAD` / `INVALID_ACTION_TYPE` / `INVALID_DECISION` | Structural |
| `RATIONALE_TOO_SHORT` | ≥ 30 chars |
| `MISSING_CHANGES` / `UNEXPECTED_CHANGES` | change/no_change envelope |
| `EMPTY_NAVAL_LIST` | naval_unit_codes non-empty |
| `UNKNOWN_UNIT` / `NOT_OWN_UNIT` / `WRONG_UNIT_TYPE` | Each must be own naval |
| `UNIT_NOT_ACTIVE` | status=active |
| `MISSING_COORDS` / `BAD_COORDS` | target row/col |
| `TARGET_NOT_LAND` | target hex must be land |
| `NOT_ADJACENT` | each naval must be on a sea hex adjacent to target |
| `NO_GROUND_TARGETS` | target hex must have enemy ground units |

### A.4 Engine — `resolve_bombardment()`

```python
def resolve_bombardment(
    naval_units: list[dict],
    ground_targets: list[dict],
    precomputed_rolls: dict | None = None,  # {"rolls": [0.05, 0.88, ...]}
) -> BombardmentResult
```

Per naval unit: `random.random() < 0.10` → hit → one random ground unit destroyed.
`precomputed_rolls["rolls"][i]` supplies the float for naval_unit[i].

Result: `shots: list[{naval_code, roll, hit, target_destroyed}]`, `defender_losses`, `narrative`.

### A.5 Persistence

- `country_states_per_round.attack_bombardment_decision JSONB`
- `observatory_combat_results` row: `combat_type='bombardment'`
- Event: `event_type='bombardment'`

---

## PART B — Naval Blockade (`blockade`)

### B.1 Purpose

Declare, lift, or partially lift a blockade at one of 3 chokepoints: **Caribe Passage**, **Gulf Gate**, **Formosa Strait**. Blockades affect oil supply + GDP via the economic engine cascade.

### B.2 Decision Schema

```json
{
  "action_type": "blockade",
  "country_code": "persia",
  "round_num": 3,
  "decision": "change",
  "rationale": "string >= 30 chars",
  "changes": {
    "zone_id": "cp_gulf_gate",
    "action": "establish",
    "level": "full"
  }
}
```

| Field | Values |
|---|---|
| `changes.zone_id` | `"cp_caribe"`, `"cp_gulf_gate"`, `"cp_formosa"` |
| `changes.action` | `"establish"`, `"lift"`, `"partial_lift"` |
| `changes.level` | `"partial"`, `"full"` (only for establish) |

### B.3 Validation — `validate_blockade(payload, units, zones)`

| Code | Rule |
|---|---|
| Structural codes | Same as other validators |
| `INVALID_ZONE` | zone_id must be one of the 3 canonical chokepoints |
| `INVALID_ACTION` | action must be establish/lift/partial_lift |
| `INVALID_LEVEL` | level must be partial/full (on establish) |
| `NO_UNIT_AT_CHOKEPOINT` | establish requires own naval (or ground for Gulf Gate) at/adjacent to the chokepoint hex |

### B.4 Engine

Blockade state is written to the `blockades` state table (already exists, already keyed by `sim_run_id`). The economic engine reads blockade state via `round_tick.py:_detect_formosa_blockade()` and the oil price formula.

**No pure dice function needed** — blockade is a state transition (establish/lift), not a combat resolution. The "engine" is just a write to the `blockades` table + event log.

Economic cascade (already implemented in `engines/economic.py:calc_oil_price()`):
- Partial: -25% oil production for affected producers
- Full: -50%
- Formosa: GDP hit + AI R&D freeze (already in `round_tick.py`)

### B.5 Persistence

- `country_states_per_round.blockade_decision JSONB`
- `blockades` table row: `{sim_run_id, zone_id, imposer_country_id, level, status, established_round}`
- Event: `event_type='blockade_declared'` / `'blockade_lifted'`

---

## LOCKED INVARIANTS

1. `attack_bombardment`: 10% hit per naval unit, no AD, no modifiers
2. `blockade`: 3 canonical chokepoints only
3. Both accept `precomputed_rolls` where applicable
4. Validators pure, no DB access
5. `blockades` table is the canonical state source (economic engine reads from it)
6. Economic cascade is NOT re-implemented in M5 — already live in `calc_oil_price()` + `round_tick`
