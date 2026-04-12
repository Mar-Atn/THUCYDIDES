# CONTRACT: Air Strike Decision

**Status:** 🔒 **LOCKED** (2026-04-12) — canonical reference, frozen for the Unmanned Spacecraft phase. Any change requires Marat's explicit approval + version bump + same-commit reconciliation of all listed consumers.

**Version:** 1.0 (2026-04-12)
**Owner:** Marat
**Authoritative source:** `PHASES/UNMANNED_SPACECRAFT/CARD_ACTIONS.md` §1.4 (where it conflicts with SEED_D8, CARD wins).
**Will be used by:**
- Engine: `app/engine/engines/military.py:resolve_air_strike()` (M3 canonical, NEW)
- Validator: `app/engine/services/air_strike_validator.py` (NEW)
- Context builder: `app/engine/services/combat_context.py:build_air_strike_context()` (extends M2 file)
- Persistence: `app/engine/round_engine/resolve_round.py:_resolve_ranged_strikes` (rewired) + existing `observatory_combat_results` (outcomes) + `country_states_per_round.attack_air_decision` JSONB (NEW)
- Tests: `app/tests/layer1/test_air_strike_validator.py`, `app/tests/layer2/test_air_strike_persistence.py`, `app/tests/layer3/test_air_strike_full_chain_ai.py`

---

## 1. PURPOSE

Air strikes are the second offensive military action shipped under contract. Tactical air units fly from a source hex to a target hex (≤2 hexes away), each one rolling independently for hit + AD interception. Unlike ground combat, air strikes are **probability-based, not iterative dice**.

**Per CARD_ACTIONS §1.4:**
- 12% base hit probability (no AD covering target)
- 6% if AD covers target (halved)
- 15% chance attacker is downed if AD present (independent of hit roll)
- No air superiority bonus (per CARD_FORMULAS D.2)
- All probabilities Template-customizable

**Key design principles:**

1. **One source hex → one target hex per decision.** A country wanting air strikes from multiple sources submits multiple decisions. Mirrors M2 ground combat.

2. **Each attacker rolls independently.** A batch of N tactical_air units in one decision produces N independent rolls. Per-shot results are stored individually for visualization.

3. **Range = 2 cardinal hexes max.** Chebyshev distance ≤ 2 means the target hex must be within 2 steps cardinally from the source hex. Source hex itself is invalid (use ground combat for adjacent attacks). Diagonal distances count as the sum of row and col deltas.

4. **AD coverage is hex-level.** A target hex is "AD-covered" if ANY enemy AD unit is on the same hex OR on an adjacent hex (same definition as the existing `_ad_units_in_zone` helper).

5. **Probability roll, not dice.** Result = `random.random() < threshold`. The `precomputed_rolls` hook accepts pre-rolled floats from a moderator (or test).

6. **Validator does legality only, not probability.** Modifier preview is computed at the validator/context level for AI use; the engine recomputes them when applying.

---

## 2. DECISION SCHEMA

### 2.1 The decision object (change)

```json
{
  "action_type": "attack_air",
  "country_code": "cathay",
  "round_num": 3,
  "decision": "change",
  "rationale": "string >= 30 chars",
  "changes": {
    "source_global_row": 6,
    "source_global_col": 15,
    "target_global_row": 7,
    "target_global_col": 14,
    "attacker_unit_codes": ["cat_a_05", "cat_a_06"]
  }
}
```

### 2.2 Field specifications

| Field | Type | Required | Semantics |
|---|---|---|---|
| `action_type` | string | yes | Must be `"attack_air"` |
| `country_code` | string | yes | Attacking country |
| `round_num` | int | yes | Round number |
| `decision` | string | yes | `"change"` or `"no_change"` |
| `rationale` | string | yes | ≥ 30 chars |
| `changes.source_global_row` | int 1..10 | yes (change) | Source hex row |
| `changes.source_global_col` | int 1..20 | yes (change) | Source hex col |
| `changes.target_global_row` | int 1..10 | yes (change) | Target hex row |
| `changes.target_global_col` | int 1..20 | yes (change) | Target hex col |
| `changes.attacker_unit_codes` | list[str] | yes (change) | tactical_air codes from source hex |

### 2.3 The `no_change` form

```json
{
  "action_type": "attack_air",
  "country_code": "cathay",
  "round_num": 3,
  "decision": "no_change",
  "rationale": "Holding air assets in reserve for next round - no priority targets visible"
}
```

---

## 3. VALIDATION RULES

`validate_air_strike(payload, units, country_state, zones) → {valid, errors, warnings, normalized}`.

### 3.1 Error codes

| Code | Rule |
|---|---|
| `INVALID_PAYLOAD` | top-level dict |
| `INVALID_ACTION_TYPE` | `attack_air` |
| `INVALID_DECISION` | `change` / `no_change` |
| `RATIONALE_TOO_SHORT` | ≥ 30 chars |
| `MISSING_CHANGES` | change requires changes block |
| `UNEXPECTED_CHANGES` | no_change must omit changes |
| `UNKNOWN_FIELD` | extra keys |
| `MISSING_COORDS` | required coords missing |
| `BAD_COORDS` | row 1..10, col 1..20 |
| `SAME_HEX` | source == target |
| `OUT_OF_RANGE` | abs(dr)+abs(dc) > 2 |
| `EMPTY_ATTACKER_LIST` | attacker_unit_codes non-empty |
| `UNKNOWN_UNIT` | each code must exist |
| `NOT_OWN_UNIT` | each unit must belong to country_code |
| `WRONG_UNIT_TYPE` | each must be tactical_air |
| `UNIT_NOT_ON_SOURCE` | each unit at source hex with status=active |
| `UNIT_NOT_ACTIVE` | status must be active (not embarked/reserve/destroyed) |
| `TARGET_FRIENDLY` | target hex must contain at least one ENEMY active unit |
| `DUPLICATE_ATTACKER` | unit_code listed twice |

### 3.2 Normalized output

On valid: same shape as input with deduped + sorted attacker_unit_codes.

---

## 4. ENGINE BEHAVIOR

`engines/military.py:resolve_air_strike(...)`:

```python
def resolve_air_strike(
    attackers: list[dict],          # tactical_air units
    defenders: list[dict],          # all units on target hex (any type)
    ad_units: list[dict],           # AD units that cover the target hex
    air_superiority_count: int = 0, # extra friendly tac_air on source hex
    precomputed_rolls: dict | None = None,
) -> AirStrikeResult:
```

`AirStrikeResult` shape:

```python
class AirStrikeShot(BaseModel):
    attacker_code: str
    hit_probability: float
    hit_roll: float
    hit: bool
    downed_probability: float       # 0.15 if AD present, 0 otherwise
    downed_roll: float
    downed: bool
    target_destroyed: str | None    # unit_code if hit, else None

class AirStrikeResult(BaseModel):
    combat_type: str = "air_strike"
    shots: list[AirStrikeShot]
    attacker_losses: list[str]      # downed attackers
    defender_losses: list[str]      # destroyed defenders
    modifier_breakdown: list[GroundCombatModifier]  # reuse M2 type for visualization
    rolls_source: str               # "random" | "moderator"
    narrative: str
    success: bool                   # True iff at least one hit
```

### 4.1 Modifier breakdown

The engine builds this list at entry (for the visualization to mirror M2):

```python
[
  {"side": "defender", "value": -50, "reason": "AD coverage halves hit probability"},  # -50% relative
  {"side": "attacker", "value": +2,  "reason": "air superiority: 1 extra friendly tac_air on source"},
]
```

For air strikes, modifiers are *informational* (reasons for the probabilities) — they don't add/subtract dice.

### 4.2 precomputed_rolls

```python
precomputed_rolls = {
  "shots": [
    {"hit_roll": 0.05, "downed_roll": 0.30},   # for attacker[0]
    {"hit_roll": 0.18, "downed_roll": 0.05},   # for attacker[1]
  ]
}
```

When set, the engine consumes per-shot rolls in order. When None, uses `random.random()`.

### 4.3 Resolution order per attacker

1. Compute `hit_prob` (12% base, halved to 6% if AD covers — no air superiority bonus per CARD)
2. Roll `hit_roll = random.random()` (or precomputed)
3. `hit = hit_roll < hit_prob`
4. If hit: pick a target (prefer non-AD enemy unit), record `target_destroyed`
5. If AD present: roll `downed_roll`, `downed = downed_roll < 0.15`
6. If downed: add attacker_code to attacker_losses

---

## 5. PERSISTENCE

- `country_states_per_round.attack_air_decision JSONB` (audit, NEW column)
- `observatory_combat_results` row written per attack:
  - `combat_type='air_strike'`
  - `attacker_country`, `defender_country`
  - `location_global_row/col` = target hex
  - `attacker_units` = list of attacker codes
  - `defender_units` = list of defender codes on target hex
  - `attacker_rolls` = JSONB list-of-shots: `[{hit_prob, hit_roll, hit, downed_prob, downed_roll, downed}, ...]`
  - `defender_rolls` = `[]` (defenders don't roll)
  - `attacker_losses`, `defender_losses` (lists of unit_codes)
  - `modifier_breakdown` = informational modifier list
  - `narrative`
- `observatory_events` row: `event_type='air_strike'`

---

## 6. CONTEXT (decision-specific)

`build_air_strike_context(country_code, scenario_code, round_num, sim_run_id?)` returns:

- `economic_state` (gdp, treasury, stability, war_tiredness, at_war_with)
- `my_air_forces_by_hex` — own active tactical_air grouped by source hex
- `targetable_enemy_hexes` — for each source hex, list of enemy hexes within 2 cardinal hexes, with: enemy_country, defenders composition, AD coverage flag, hit_prob_preview, downed_prob_preview
- `recent_combat_events`
- `decision_rules` text + `instruction`

---

## 7. NON-GOALS (out of scope for v1.0)

- Bombing infrastructure (covered by missile strikes)
- Suppression of enemy AD (SEAD)
- Multi-target single mission
- Return-to-base mechanics (air units don't run out of fuel mid-round)
- Pilot loss tracking separate from airframe destruction

---

## 8. LOCKED INVARIANTS

1. `action_type = "attack_air"`
2. Range = 2 cardinal hexes (Manhattan distance ≤ 2)
3. Hit probability formula: `12% × (0.5 if AD else 1)` — no air superiority bonus, no clamp (per CARD_FORMULAS D.2)
4. Downed probability = 15% if AD present, 0 otherwise
5. Per-shot result list (one entry per attacker)
6. `precomputed_rolls` hook accepts `{"shots": [{"hit_roll": float, "downed_roll": float}, ...]}`
7. Modifier_breakdown list-of-dicts (mirrors M2 shape for combined visualization)
8. Validator pure, no DB access
9. observatory_combat_results.modifier_breakdown column already exists (added in M2)
