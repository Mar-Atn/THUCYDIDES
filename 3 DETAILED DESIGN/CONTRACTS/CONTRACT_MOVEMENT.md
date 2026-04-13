# CONTRACT: Unit Movement Decision

**Status:** 🔒 **LOCKED** (2026-04-11) — canonical reference, frozen for the Unmanned Spacecraft phase. Any change requires Marat's explicit approval + version bump + same-commit reconciliation of all listed consumers.

**Version:** 1.0 (2026-04-11)
**Owner:** Marat
**Authoritative source:** `PHASES/UNMANNED_SPACECRAFT/CARD_ACTIONS.md` §1.1 (where it conflicts with SEED_D8, CARD wins).
**Will be used by:**
- Engine: `app/engine/engines/movement.py` (**NEW** — replaces deprecated `round_engine/movement.py`)
- Validator: `app/engine/services/movement_validator.py` (NEW)
- Context builder: `app/engine/services/movement_context.py` (NEW — read-only, decision-specific, data only)
- Persistence: `app/engine/round_engine/resolve_round.py` (set_movements handler — full rewrite) + existing `unit_states_per_round` table (outcomes) + `country_states_per_round.movement_decision` JSONB column (NEW — per-round decision audit)
- Tests: `app/tests/layer1/test_movement_validator.py`, `app/tests/layer1/test_movement_engine.py`, `app/tests/layer2/test_movement_persistence.py`, `app/tests/layer2/test_movement_context.py`, `app/tests/layer3/test_movement_full_chain_ai.py`

---

## 1. PURPOSE

Each round, between Phase A (active round) and Phase A of the next round, every country decides how to reposition its military forces. Movement includes **three use cases**:

1. **Reposition** — active unit moves from its current hex to a new hex
2. **Deploy from reserve** — reserve unit activates and takes a position on the map
3. **Withdraw to reserve** — active unit returns to the reserve pool (invisible, unavailable next round)

Plus two **auto-detected flows** (no separate target type needed — engine infers from state):

4. **Embark** — a ground or tactical air unit moving onto a hex where the country has a friendly naval carrier with spare capacity is auto-embarked onto that carrier
5. **Debark + move** — an embarked unit's move order automatically restores its own position (starting from the carrier's current location) before applying the target

**Key design principles:**

1. **One batch per country per round.** All move orders are submitted in a single `move_units` action containing a list of individual moves. Atomic validation — if any move in the batch is invalid, the entire batch is rejected with all errors reported.
2. **No range limit.** Per CARD_ACTIONS §1.1, "All units can be relocated globally to any suitable hex." Spatial constraints are type-based and territory-based, NOT distance-based. The old hex-distance code (`MOVE_RANGE = {ground: 1, naval: 2, ...}`) is abandoned.
3. **Instant between-round deployment.** Moves submitted in round N take effect at the start of round N+1. No transit delay. The move order written to `agent_decisions` in round N is processed by `resolve_round(N)` at round-end and written to `unit_states_per_round` for round N (the "end of round N" snapshot), which is then read as the "start of round N+1" state.
4. **Last-submission-wins.** If a country (human!) submits `move_units` twice in the same round, the second submission replaces the first via upsert on `(scenario, country, round, action_type)`. This supports human correction workflows; AI agents submit once and the mechanism is transparent to them.
5. **Engine owns embark/debark detection.** The participant just says "move unit X to hex Y". If the hex has a friendly carrier with capacity, the engine embarks. If the unit is already embarked, the engine debarks first. The schema doesn't expose embark as a distinct concept.
6. **Decision-specific context, data only.** The context builder serves: own units (active/reserve/embarked), zone ownership map, basing rights, recent combat events. No commentary, no strategic hints, no cognitive layer. Standard VERTICAL_SLICE_PATTERN boundary.
7. **CARD_ACTIONS §1.1 is canonical.** Where SEED_D8 Part 6B conflicts with CARD (strategic missile mobility, transit delay, "leave ≥1 unit" constraint), CARD wins. SEED_D8 will be updated in the closing doc reconciliation step.

---

## 2. DECISION SCHEMA

### 2.1 The decision object

```json
{
  "action_type": "move_units",
  "country_code": "columbia",
  "round_num": 3,
  "decision": "change" | "no_change",
  "rationale": "string, >= 30 chars, required in both cases",
  "changes": {
    "moves": [
      {
        "unit_code": "col_g_012",
        "target": "hex",
        "target_global_row": 5,
        "target_global_col": 12
      },
      {
        "unit_code": "col_ta_004",
        "target": "hex",
        "target_global_row": 5,
        "target_global_col": 12
      },
      {
        "unit_code": "col_g_008",
        "target": "reserve"
      }
    ]
  }
}
```

### 2.2 Field specifications

| Field | Type | Values | Required | Semantics |
|---|---|---|---|---|
| `action_type` | string | `"move_units"` (PLURAL) | yes | Full replacement for legacy singular `move_unit`. No backward-compat. |
| `country_code` | string | canonical country code | yes | Decision owner. Must own every unit in the moves list. |
| `round_num` | int | ≥ 0 | yes | Round in which the decision is submitted |
| `decision` | string | `"change"` or `"no_change"` | yes | Explicit choice. `no_change` is legitimate (no units moved). |
| `rationale` | string | ≥ 30 chars | yes | Required in both branches |
| `changes` | object | see §2.3 | only if `decision=="change"` | Must be absent when `no_change` |

### 2.3 The `changes.moves` list

A non-empty list of move objects. Each move has this shape:

| Field | Type | Values | Required | Semantics |
|---|---|---|---|---|
| `unit_code` | string | canonical unit identifier | yes | Must exist in `unit_states_per_round`, belong to `country_code`, and not be destroyed |
| `target` | string | `"hex"` or `"reserve"` | yes | Two target modes: a map hex, or withdrawal to the reserve pool |
| `target_global_row` | int | 1..N (global grid rows) | only when `target=="hex"` | Row in the global hex grid |
| `target_global_col` | int | 1..N (global grid cols) | only when `target=="hex"` | Column in the global hex grid |

### 2.4 No_change example

```json
{
  "action_type": "move_units",
  "country_code": "solaria",
  "round_num": 3,
  "decision": "no_change",
  "rationale": "Current defensive posture across Gulf zones is optimal. No reinforcement or redeployment needed this round."
}
```

Note: NO `changes` field. Just the envelope.

### 2.5 Duplicate unit in batch

A unit cannot appear twice in the `moves` list. The validator rejects such batches with `DUPLICATE_UNIT_IN_BATCH`. If a participant wants to move a unit through intermediate hexes in a single round, it's still represented as **one** move to the final position — movement is abstract (instant deployment), not step-by-step pathing.

---

## 3. CONTEXT PROVIDED TO DECISION-MAKER (decision-specific only)

The system supplies decision-specific context. **Cognitive context (identity, memory, goals, world rules) is OUT OF SCOPE** per the VERTICAL_SLICE_PATTERN boundary — it's the AI Participant Module's responsibility.

### 3.1 What the system provides

```
[ECONOMIC STATE]           ← own country snapshot (GDP, treasury, stability, war status)
[MY UNITS]                 ← full list of own units with status, position, type
[OWN TERRITORY]            ← list of zones owned/controlled by me
[BASING RIGHTS I HAVE]     ← zones in other countries where I can legally deploy
[PREVIOUSLY OCCUPIED HEXES] ← hexes I already have ≥1 unit on (qualifies for deploy target)
[RECENT COMBAT EVENTS]     ← last 3 rounds' combat outcomes involving my units (for context)
[WORLD ZONE MAP]           ← all 57 zones with theater, owner, controlled_by, is_chokepoint, die_hard
[ZONE ADJACENCY]           ← adjacency graph (for player intuition — not a range constraint)
[DECISION RULES]           ← schema summary + constraints + no_change reminder
[INSTRUCTION]
```

### 3.2 [ECONOMIC STATE]

```
GDP:                {gdp}
Treasury:           {treasury}
Stability:          {stability}/10
War status:         at war with {N countries}: {list} / at peace
Relationships:      {summary of allies, tensions}
```

### 3.3 [MY UNITS] — full inventory

```
unit_code           type              status     position (global)   theater     embarked_on
-------             ----              -------    -----------------   -------     -----------
col_g_001           ground            active     (6, 4)              americas    -
col_g_012           ground            active     (3, 12)             asu         -
col_g_099           ground            reserve    -                   -           -
col_n_003           naval             active     (8, 15)             asu         -
col_ta_007          tactical_air      embarked   -                   -           col_n_003
col_ad_002          air_defense       active     (6, 5)              americas    -
col_sm_011          strategic_missile active     (6, 5)              americas    -
...
```

All own units (~15-35 per country) listed. Status ∈ {active, reserve, embarked, destroyed}.

### 3.4 [OWN TERRITORY] — zones I own or control

```
americas_1    (owned)      theater: americas
americas_2    (owned)      theater: americas
asu_3         (controlled) theater: asu
...
```

Sourced from `zones.owner == my_country` OR `zones.controlled_by == my_country`.

### 3.5 [BASING RIGHTS I HAVE] — foreign zones I can legally deploy to

```
I have basing rights from (granted by → zones):
  - albion: all owned zones
  - teutonia: all owned zones
  - yamato: all owned zones
```

Sourced from `relationships.basing_rights_*_to_*` booleans. Expanded to zone list.

### 3.6 [PREVIOUSLY OCCUPIED HEXES]

```
Hexes where I have ≥1 unit currently placed:
  (6, 4)  (6, 5)  (3, 12)  (8, 15)  ...
```

Sourced from `unit_states_per_round` — distinct `(global_row, global_col)` for units with status=active and country_code=mine. **These hexes qualify as "previously occupied" and are valid deploy targets for my ground/AD/missile units per CARD §1.1.**

### 3.7 [RECENT COMBAT EVENTS] — last 3 rounds

```
R{N-2}: col_g_055 destroyed at (4, 7) in ground combat vs persia
R{N-1}: col_ta_012 destroyed at (3, 8) in air interception (ruthenia AD)
R{N}:   (none)
```

Sourced from `observatory_combat_results` (last 3 rounds, involving my units). Data only, no narrative.

### 3.8 [WORLD ZONE MAP]

Compact representation of the 57 zones:

```
zone_id       theater    owner       controlled_by  chokepoint  die_hard
---------     -------    -----       -------------  ----------  --------
americas_1    americas   columbia    columbia       false       false
cp_gulf_gate  mashriq    persia      persia         true        false
asu_7         asu        cathay      cathay         false       true
...
```

All 57 zones. Participant uses this to figure out which hexes correspond to which zones, which zones are owned by whom, and which are chokepoints/die-hard.

### 3.9 [ZONE ADJACENCY]

```
americas_1: [americas_2, americas_5]
americas_2: [americas_1, americas_3, cp_atlantic]
...
```

The adjacency graph. **Not a range constraint** (range is unlimited per the card), but provides spatial intuition for the participant.

### 3.10 [DECISION RULES]

```
HOW MOVEMENT WORKS (mechanically)
- Three use cases per unit: reposition / deploy from reserve / withdraw to reserve
- Two auto-detected flows: embark (onto own naval with capacity) / debark (implicit)
- Range: unlimited during deployment phase
- Timing: moves take effect at the start of the next round
- One `move_units` submission per country per round (batch all moves together)
- Last submission in a round wins (supports human correction)

CONSTRAINTS by unit type
- Ground / AD / Strategic Missile: target hex NOT sea; must be own territory, basing rights zone, OR previously occupied hex (≥1 own unit there)
- Tactical Air: same as ground, PLUS can auto-embark on own naval (max 2 air per ship)
- Naval: sea hexes ONLY (cannot touch land)
- Embark auto-detection: ground can auto-embark on own naval (max 1 ground + 2 air per ship)

DECISION RULES
- decision="change"    → must include changes.moves with ≥1 valid move
- decision="no_change" → must OMIT the changes field entirely
- rationale ≥30 chars REQUIRED in both cases
- duplicate unit_code in the same batch is invalid

REMINDER — no_change is a legitimate choice
Movement has real costs: units in transit are committed, withdrawing to reserve
loses a round of availability. If your current deployment serves your goals,
no_change with a clear rationale is the correct answer.
```

### 3.11 [INSTRUCTION]

```
Decide whether to CHANGE your unit dispositions or keep them NO_CHANGE.
Either way you MUST provide a rationale of at least 30 characters.

Respond with JSON ONLY, matching the schema in CONTRACT_MOVEMENT §2.
```

---

## 4. VALIDATION RULES

The validator is a pure function `validate_movement_decision(payload, context) → {valid, errors, warnings, normalized}`. **All errors are collected in a single pass.** Atomic: any single invalid move rejects the entire batch.

The validator needs **context** beyond the payload — it must query current `unit_states_per_round`, `zones`, `relationships`, and country ownership. For pure testability, the validator signature is:

```python
def validate_movement_decision(
    payload: dict,
    units: dict[str, dict],        # unit_code → unit state
    zones: dict[str, dict],        # zone_id → zone record
    basing_rights: dict[str, set], # country_code → set of zone_ids granting basing
) -> dict:
```

The harness and resolve_round both build these dicts from DB queries before calling the validator.

### 4.1 Error codes (17 total)

| Code | Rule | Trigger |
|---|---|---|
| `INVALID_PAYLOAD` | top-level must be a dict | non-dict input |
| `INVALID_ACTION_TYPE` | `action_type == "move_units"` | missing or wrong value |
| `INVALID_DECISION` | `decision in {"change", "no_change"}` | missing or wrong value |
| `RATIONALE_TOO_SHORT` | rationale string ≥ 30 chars after strip | missing, non-string, or too short |
| `MISSING_CHANGES` | `decision=="change"` requires `changes.moves` list | change without changes; non-dict changes; non-list moves |
| `UNEXPECTED_CHANGES` | `decision=="no_change"` must omit `changes` | `no_change` with `changes` present |
| `EMPTY_CHANGES` | `decision=="change"` with empty moves list | zero-length moves list |
| `UNKNOWN_FIELD` | top-level or changes-level keys must be in allowed set | extra fields anywhere |
| `UNKNOWN_UNIT` | each move's unit_code must exist in units | unknown unit |
| `UNIT_NOT_OWNED` | unit_code must belong to country_code | foreign unit |
| `UNIT_DESTROYED` | destroyed units cannot be moved | status=destroyed |
| `INVALID_TARGET` | target must be `"hex"` or `"reserve"`; hex targets require coords | wrong target, missing coords |
| `DUPLICATE_UNIT_IN_BATCH` | same unit_code appears twice in moves list | duplicate |
| `SEA_HEX_FORBIDDEN` | ground/AD/missile/tactical_air targeting a sea hex with no friendly carrier present | land unit to sea hex without embark option |
| `LAND_HEX_FORBIDDEN` | naval targeting a non-sea hex | naval to land hex |
| `NOT_ALLOWED_TERRITORY` | ground/AD/missile hex target not in {own territory, basing rights, previously occupied} | illegal deploy destination |
| `EMBARK_CAPACITY_EXCEEDED` | after applying the batch, a carrier would exceed 1 ground + 2 air | over-embark |

### 4.2 Allowed fields

Top level: `action_type`, `country_code`, `round_num`, `decision`, `rationale`, `changes`.
Inside `changes`: `moves` (only).
Inside each move: `unit_code`, `target`, `target_global_row`, `target_global_col`.

### 4.3 Batch validation semantics

- **Atomic rejection.** If ANY move in the batch is invalid, the entire batch is rejected. The participant gets ALL errors (across all moves) in one report.
- **Batch-internal state propagation.** The validator simulates the batch in order: move #1 is applied to a copy of state, then move #2 is checked against the updated state, etc. This matters for:
  - **Previously-occupied check:** if move #1 deploys a unit to a new hex, move #2 may legally target the same hex as "previously occupied" now.
  - **Embark capacity:** carriers' embarked counts are tracked across the batch.
- **Last-submission-wins.** If a country submits `move_units` twice in a round, the second submission's `agent_decisions` row replaces the first via `upsert` on `(scenario_id, country_code, round_num, action_type)`.

### 4.4 Normalized output (when valid)

```json
{
  "action_type": "move_units",
  "country_code": "columbia",
  "round_num": 3,
  "decision": "change",
  "rationale": "<trimmed string>",
  "changes": {
    "moves": [
      {"unit_code": "col_g_012", "target": "hex", "target_global_row": 5, "target_global_col": 12},
      {"unit_code": "col_g_008", "target": "reserve"}
    ]
  }
}
```

For `no_change`, the `changes` field is omitted. Whitespace stripped. Country codes lowercased.

---

## 5. PERSISTENCE

### 5.1 Two storage layers

| Layer | Purpose | Written by |
|---|---|---|
| **`unit_states_per_round`** (existing) | **The OUTCOME** — per-unit position after the move is applied. `(unit_code, round_num)` primary key. Updated every round by the engine's write-back pass, inheriting from round N-1 where unchanged. | engine (`engines/movement.py` via `resolve_round` → `round_tick`) |
| **`country_states_per_round.movement_decision`** (NEW, JSONB, 2026-04-11) | **The INTENT** — per-country-per-round audit record of the submitted decision envelope, including `no_change` decisions with rationale. | `resolve_round` set_movements handler |

These are complementary:
- `unit_states_per_round` answers "where is every unit at round N?"
- `movement_decision` answers "what did Columbia DECIDE to do in round N, and why?"

### 5.2 DB migration

Migration name: `movement_v1_canonical_schema`

Changes:
- **Add** `country_states_per_round.movement_decision jsonb` (NEW audit column)
- **Delete** stale `agent_decisions` rows: `WHERE action_type IN ('move_unit', 'mobilize_reserve')` (7 rows)

### 5.3 Write path (resolve_round set_movements handler)

```
1. Build full envelope from the latest agent_decisions row for this country / round / action=move_units
2. Load context dicts: units, zones, basing_rights
3. Call validate_movement_decision(payload, units, zones, basing_rights)
4. If invalid:
     - Log warning
     - Emit observatory_event(type="movement_rejected", country, payload, errors)
     - DO NOT touch unit_states_per_round or movement_decision column
5. If valid and decision == "no_change":
     - Write {"decision": "no_change", "rationale": "..."} to movement_decision for (country, round)
     - DO NOT touch unit_states_per_round (carry-forward by inaction)
6. If valid and decision == "change":
     - Write normalized envelope to movement_decision column
     - For each move in normalized.changes.moves, apply to unit_state dict:
         * reposition: update global coords + auto-derive theater coords
         * deploy from reserve: set status=active, update coords, auto-derive theater
         * withdraw to reserve: set status=reserve, clear coords, clear embarked_on
         * embark (auto-detected): set status=embarked, set embarked_on=carrier, clear coords
         * debark (auto-detected): restore coords from carrier, set status=active, clear embarked_on
     - Persist the updated unit_state dict back to unit_states_per_round for this round
     - Emit observatory_event(type="movement_applied", country, moves_count, summary)
```

### 5.4 Read path

The `unit_states_per_round` table is read at the start of each round by `round_tick._load_unit_state` (existing). No changes to the load path for this slice. The `movement_decision` column is read only by the context builder (Step 5) and the observatory (for replay).

---

## 6. ENGINE BEHAVIOR

**NEW:** `app/engine/engines/movement.py` — canonical engine module, replacing the deprecated `round_engine/movement.py`.

### 6.1 Core function

```python
def process_movements(
    moves: list[dict],              # normalized moves list from the validator
    country_code: str,              # actor
    units: dict[str, dict],         # unit_code → unit state (MUTATED in place)
    zones: dict[str, dict],         # zone_id → zone record
    zone_adjacency: dict,           # not used for range, only for display context
) -> list[dict]:                    # list of per-move result dicts (for audit + Observatory)
    """Apply a validated batch of moves atomically to the unit state dict.

    The validator has already checked legality. This function performs the
    state mutations and returns a list of result dicts describing what happened.
    """
```

### 6.2 Per-move apply logic

For each move in the batch, in order:

```python
unit = units[move["unit_code"]]

if move["target"] == "reserve":
    # Withdraw
    prev = (unit["global_row"], unit["global_col"], unit["theater"], unit["status"], unit.get("embarked_on"))
    unit["status"] = "reserve"
    unit["global_row"] = None
    unit["global_col"] = None
    unit["theater"] = None
    unit["theater_row"] = None
    unit["theater_col"] = None
    unit["embarked_on"] = None
    result = {"unit_code": ..., "action": "withdraw", "from": prev}

elif move["target"] == "hex":
    tgt_row, tgt_col = move["target_global_row"], move["target_global_col"]

    # Debark handling: if unit is currently embarked, clear embarked_on FIRST
    if unit["status"] == "embarked":
        unit["embarked_on"] = None

    # Embark auto-detection: check if target hex has a friendly carrier with capacity
    friendly_carriers_at_target = [
        u for u in units.values()
        if u["country_code"] == country_code
        and u["unit_type"] == "naval"
        and u["status"] == "active"
        and u.get("global_row") == tgt_row
        and u.get("global_col") == tgt_col
        and _carrier_capacity_remaining(u, units) > 0
        and unit["unit_type"] in ("ground", "tactical_air")
    ]

    if friendly_carriers_at_target:
        # Auto-embark (pick carrier with most capacity)
        carrier = max(friendly_carriers_at_target, key=lambda u: _carrier_capacity_remaining(u, units))
        unit["status"] = "embarked"
        unit["embarked_on"] = carrier["unit_code"]
        unit["global_row"] = None
        unit["global_col"] = None
        unit["theater"] = None
        unit["theater_row"] = None
        unit["theater_col"] = None
        result = {"unit_code": ..., "action": "embark", "carrier": carrier["unit_code"]}
    else:
        # Normal hex move (or deploy from reserve)
        unit["global_row"] = tgt_row
        unit["global_col"] = tgt_col
        (theater, theater_row, theater_col) = _hex_to_theater(tgt_row, tgt_col, zones)
        unit["theater"] = theater
        unit["theater_row"] = theater_row
        unit["theater_col"] = theater_col
        unit["status"] = "active"
        unit["embarked_on"] = None
        result = {"unit_code": ..., "action": "reposition_or_deploy", "to": (tgt_row, tgt_col, theater)}
```

### 6.3 Theater auto-derivation

`_hex_to_theater(global_row, global_col, zones)` looks up which theater contains the global hex. Uses the existing global→theater mapping from `engine/config/map_config.py` (the canonical source per `/app/engine/CLAUDE.md`). Returns `(theater, theater_row, theater_col)`.

### 6.4 Carrier capacity helper

```python
def _carrier_capacity_remaining(carrier: dict, all_units: dict) -> int:
    """A naval carrier has capacity for 1 ground + 2 tactical_air = 3 total embarked units.

    Returns 3 - current_embarked_count (minimum 0).
    """
    carrier_code = carrier["unit_code"]
    embarked = [
        u for u in all_units.values()
        if u.get("embarked_on") == carrier_code
    ]
    ground_embarked = sum(1 for u in embarked if u["unit_type"] == "ground")
    air_embarked = sum(1 for u in embarked if u["unit_type"] == "tactical_air")
    return max(0, (1 - ground_embarked)) + max(0, (2 - air_embarked))
```

The validator uses this same helper to pre-check `EMBARK_CAPACITY_EXCEEDED` during batch simulation.

### 6.5 What the engine does NOT do in this slice

- **No combat.** Moving into enemy territory is REJECTED by the validator (`NOT_ALLOWED_TERRITORY`), not resolved via combat. Combat is M2 (`declare_attack` action).
- **No retreat.** Forced retreats from combat are M2 territory.
- **No transit through contested zones.** Naval units don't check chokepoint blockades in M1 (that interacts with M5 Blockade). For now, moves are accepted as instant teleports to the target hex provided the hex itself is legal.
- **No supply/fuel consumption.** Movement is free.
- **No unit stacking limits.** You can pile 50 ground units in one hex. Stacking limits are a separate calibration if we need them later.

---

## 7. WHAT IS OUT OF SCOPE FOR THIS SLICE

- **Cognitive blocks** (rules/identity/memory/goals) — AI Participant Module (future)
- **AI agent persistence** — AI Participant Module v1.0 (separate phase block)
- **Combat** — M2 slice (`declare_attack`)
- **Martial law / recruitment** — separate future slice. The existing `engines/military.py:resolve_mobilization` function (the pool-depleting one) will be **renamed to `resolve_martial_law`** in the closing step of M1 to eliminate the naming collision with `round_engine/movement.py:resolve_mobilization`.
- **Legacy `move_unit` / `mobilize_reserve` actions** — DELETED. No backward compatibility. All legacy callers in code + tests are migrated to `move_units` or removed.
- **Chokepoint transit for naval** — deferred to M5 Blockade slice
- **Supply / fuel / stacking limits** — not in the design; deferred to any future calibration pass
- **Intra-round movement** — per CARD_ACTIONS, only "attack advance" allows movement during active round, and that's part of M2 combat
- **Transit delay** — zero per CARD_ACTIONS (moves are instant between rounds)
- **Observatory test replay feature** — separate follow-up effort (M1-VIS) after M1 closes. M1 visual review uses fixed round numbers (200-203) and the existing Observatory scrubber.

---

## 8. STANDARD OUTPUT

Per `move_units` decision submitted, the engine produces:

- **`country_states_per_round.movement_decision`** (JSONB) — the audit envelope (decision, rationale, changes)
- **`unit_states_per_round`** rows (updated in place for round N) — the new position/status of every moved unit, including auto-embarked/debarked ones
- **`observatory_events`**:
  - `movement_applied` events with summary and move count (for successful batches)
  - `movement_rejected` events with error list (for invalid batches)

**Cascading effects** this action writes into state that OTHER engines may read:
- Ground/air/naval combat engines (M2-M4): unit positions at round start determine who's adjacent, who's in range
- Oil supply engine: if a naval unit blocks a chokepoint through simple positioning (M5 territory)
- Political engine: forced retreats affect war tiredness (M2 territory)
- **None in M1 itself.** M1 just moves units around; all downstream engines read the `unit_states_per_round` table normally.

Tests assert against:
- `movement_decision` JSONB on the snapshot — matches submitted decision byte-for-byte
- `unit_states_per_round` — every unit in the moves list has the expected position/status
- `observatory_events` — `movement_applied` or `movement_rejected` as appropriate
- Batch-internal state propagation — reinforcing a hex using a prior move's arrival works

---

## 9. ACCEPTANCE CRITERIA

Before marking the slice DONE:

- [ ] **Step 1 — Contract** — this document, reviewed and locked
- [ ] **Step 2 — Validator (L1)** — `movement_validator.py` with 17 error codes + context-dependent signature; L1 tests covering every error code + batch propagation (previously-occupied chaining, embark capacity across batch)
- [ ] **Step 3 — Engine (L1)** — new `engines/movement.py` with `process_movements` + helpers; L1 tests pinning: reposition, deploy from reserve, withdraw, auto-embark, auto-debark, theater auto-derivation, atomic batch
- [ ] **Step 4 — Persistence (L2)** — migration applied (movement_decision JSONB + legacy row cleanup); set_movements handler rewritten; L2 tests for change / no_change / invalid rejected / last-submission-wins; legacy modules deleted
- [ ] **Step 5 — Decision-specific context (L2)** — `movement_context.py` with economic state + my units + own territory + basing rights + previously-occupied hexes + recent combat + world zone map; L2 tests
- [ ] **Step 6 — AI skill harness (L3)** — new D5 (or separate harness) with movement prompt using v1.0 schema; persona stub; real validator
- [ ] **Step 7 — AI acceptance gate (L3)** — `test_movement_full_chain_ai.py`: real LLM → validator → DB → engine → snapshot, no fixup. Verify movement_decision JSONB matches, unit_states_per_round positions updated correctly.
- [ ] **Closing** —
  - CHECKPOINT_MOVEMENT.md written
  - CARD_ACTIONS §1.1 updated to v1.0 schema (plural `move_units`, schema block, validator reference)
  - SEED_D8 Part 6B reconciled (CARD wins; note the changes)
  - PHASE.md updated
  - CHANGES_LOG milestone entry
  - **Legacy cleanup:** delete `round_engine/movement.py`, delete `round_engine/test_resolve.py`, rename `engines/military.py:resolve_mobilization` → `resolve_martial_law`, migrate or delete legacy references in `engine/agents/action_schemas.py`, `engine/agents/tools.py`, `tests/layer2/test_battery.py`, `tests/layer2/test_battery_military.py`, `tests/layer3/test_skill_action_selection.py`
  - DB cleanup: delete the 7 stale legacy `agent_decisions` rows
  - **Visual demo:** test_movement_visual_demo.py leaves rounds 200-203 in DB for Observatory review
  - Commit

---

## 10. CHANGE LOG

- **v1.0 (2026-04-11)** — Initial draft. Pending Marat's 5-minute review before Step 2.
