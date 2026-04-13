# CONTRACT: Ground Combat Decision

**Status:** 🔒 **LOCKED** (2026-04-12) — canonical reference, frozen for the Unmanned Spacecraft phase. Any change requires Marat's explicit approval + version bump + same-commit reconciliation of all listed consumers.

**Version:** 1.0 (2026-04-12)
**Owner:** Marat
**Authoritative source:** `PHASES/UNMANNED_SPACECRAFT/CARD_ACTIONS.md` §1.3 (where it conflicts with SEED_D8, CARD wins).
**Will be used by:**
- Engine: `app/engine/engines/military.py` (canonical — `round_engine/combat.py` to be DELETED)
- Validator: `app/engine/services/ground_combat_validator.py` (NEW)
- Context builder: `app/engine/services/combat_context.py` (NEW — read-only, decision-specific, data only)
- Persistence: `app/engine/round_engine/resolve_round.py:_process_attack` (rewired) + existing `observatory_combat_results` (outcomes) + `country_states_per_round.attack_ground_decision` JSONB column (NEW — per-round decision audit)
- Tests: `app/tests/layer1/test_ground_combat_validator.py`, `app/tests/layer2/test_ground_combat_persistence.py`, `app/tests/layer3/test_ground_combat_full_chain_ai.py`, `app/tests/layer3/test_combat_visible_demo.py`

---

## 1. PURPOSE

Each round, after Phase A movement resolution, a country may attack an adjacent enemy hex. Ground combat is the **first true offensive military action** in the simulation and the model for M3 Air, M4 Naval, and the other military slices.

**The combat is RISK-style iterative dice** (CARD §1.3 step 2-5): attacker rolls min(3, attacking_units) dice, defender rolls min(2, defending_units) dice, compare highest-vs-highest with ties to defender, losing pair removes one unit on the losing side, repeat until one side has zero units.

**Three optional flows beyond the basic engagement:**

1. **Unattended hex** — target hex has no enemy ground; attacker walks in, takes the hex, captures any non-ground enemy units there as "trophies"
2. **Trophy capture** — non-ground units on a captured hex (tactical_air, air_defense, strategic_missile) become attacker reserve units, original type preserved
3. **Chain attack** — after winning a hex, if the attacker has ≥2 units survived AND there's another adjacent enemy hex AND `chain_step < max_chain`, the attack auto-continues (leaving ≥1 behind on the captured hex)

**Key design principles:**

1. **One source hex → one target hex per decision.** A country wanting to attack 3 different hexes submits 3 separate `attack_ground` decisions in the same round. Each decision is independent — last-submission-wins does NOT apply because the source hex differs. This is different from `move_units` (one batch per country) because attack semantics require explicit (source, target) pairing.

2. **Adjacency required.** Source hex and target hex must be cardinally adjacent on the global hex grid. No "leapfrog" attacks. Adjacency is computed by the validator using standard hex-grid neighbor math.

3. **Attacker selects which units.** The decision specifies `attacker_unit_codes` — a subset of own ground/armor units currently on the source hex. Units not listed stay on the source hex. The attacker must leave **≥1 unit on every occupied foreign hex** (own territory may be emptied).

4. **Modifiers applied at dice time, not at engine entry.** The validator does NOT compute or apply modifiers — that's the engine's job. The validator only checks legality (correct unit types, valid hexes, adjacency, ownership).

5. **Pure dice function with optional precomputed_rolls.** The pure RISK dice function `resolve_ground_combat()` accepts an optional `precomputed_rolls` parameter. When `None` (unmanned default), it generates random dice. When provided as `{"attacker": [[5,3,2], [6,4]], "defender": [[6,2], [4,1]]}` (one inner list per exchange), it consumes them in order. This unlocks deterministic tests + future moderator dice input.

6. **Chain mechanic owned by `_resolve_ground_chain` in resolve_round.** The pure dice function handles ONE engagement. The chain logic (next adjacent hex, leave-1-behind, max_chain bound) is wrapper code that calls the pure function repeatedly.

7. **CARD_ACTIONS §1.3 is canonical.** Where SEED_D8 conflicts (modifier list, win rates, chain mechanic semantics), CARD wins.

---

## 2. DECISION SCHEMA

### 2.1 The decision object (change)

```json
{
  "action_type": "attack_ground",
  "country_code": "cathay",
  "round_num": 3,
  "decision": "change",
  "rationale": "string, >= 30 chars, required in both cases",
  "changes": {
    "source_global_row": 6,
    "source_global_col": 15,
    "target_global_row": 6,
    "target_global_col": 14,
    "attacker_unit_codes": ["cat_g_03", "cat_g_04", "cat_g_05"],
    "allow_chain": true
  }
}
```

### 2.2 Field specifications

| Field | Type | Required | Semantics |
|---|---|---|---|
| `action_type` | string | yes | Must be `"attack_ground"` |
| `country_code` | string | yes | The attacking country |
| `round_num` | integer | yes | The round in which the attack is declared |
| `decision` | string | yes | `"change"` (attack) or `"no_change"` (skip) |
| `rationale` | string | yes | ≥ 30 chars after strip, both decision values |
| `changes.source_global_row` | int 1..10 | yes (change) | Row of source hex |
| `changes.source_global_col` | int 1..20 | yes (change) | Col of source hex |
| `changes.target_global_row` | int 1..10 | yes (change) | Row of target hex |
| `changes.target_global_col` | int 1..20 | yes (change) | Col of target hex |
| `changes.attacker_unit_codes` | list[string] | yes (change) | Unit codes from the source hex to commit |
| `changes.allow_chain` | bool | optional, default `true` | Whether to attempt chain after a win |

### 2.3 The `no_change` form

```json
{
  "action_type": "attack_ground",
  "country_code": "albion",
  "round_num": 3,
  "decision": "no_change",
  "rationale": "Not initiating ground combat this round - maintaining defensive posture and observing"
}
```

Note: NO `changes` field. Just the envelope.

### 2.4 Multiple attacks

A country wanting to launch attacks from multiple source hexes submits **one `attack_ground` decision per attack**. Each is independent. There is no batch shape.

---

## 3. CONTEXT PROVIDED TO DECISION-MAKER (decision-specific only)

The system supplies decision-specific context. **Cognitive context (identity, memory, goals, world rules) is OUT OF SCOPE** per the VERTICAL_SLICE_PATTERN boundary — see `F1_CONTEXT_GAPS.md` for what the future AI Participant Module will add.

### 3.1 What the system provides

```
[ECONOMIC STATE]                ← own country snapshot (gdp, treasury, stability, war status)
[MY GROUND FORCES]              ← own ground/armor units, status, position, source hex grouping
[ADJACENT ENEMY HEXES]          ← list of adjacent enemy-occupied hexes I could attack
[ATTACK MODIFIER FLAGS]         ← which modifiers WOULD apply per candidate target (if I attack)
[RECENT COMBAT EVENTS]          ← last 3 rounds of combat involving my units
[DECISION RULES]                ← schema summary + RISK mechanic + chain rules + no_change reminder
[INSTRUCTION]
```

### 3.2 [ECONOMIC STATE]

```
GDP:                280
Treasury:           30
Stability:          7/10
At war with:        persia
War tiredness:      2
```

### 3.3 [MY GROUND FORCES]

```
Source hex (6, 15) — 4 ground units:
  cat_g_03   ground   active
  cat_g_04   ground   active
  cat_g_05   ground   active
  cat_g_15   ground   active

Source hex (5, 16) — 2 ground units:
  cat_g_01   ground   active
  cat_g_02   ground   active
```

Only hexes with ≥1 own ground/armor unit are listed. This makes obvious which hexes are valid attack sources.

### 3.4 [ADJACENT ENEMY HEXES] (the heart of the context)

For each own source hex, the validator pre-computes adjacent hexes that contain enemy units. The AI sees them ranked.

```
Source (6, 15) → adjacent enemy hexes:
  (6, 14)  enemy=persia  defenders={ground×2, air_defense×1}  modifiers={defender +1 air_support}
  (5, 15)  enemy=persia  defenders={ground×3}                 modifiers={none}
  (7, 15)  enemy=sarmatia defenders={ground×1, tactical_air×2} modifiers={defender +2 die_hard+air_support}
```

**This is the only place the AI gets to see enemy unit positions.** It's tightly scoped to the legality + decision-relevant subset (only ENEMY hexes ADJACENT to MY source hexes). Per `INFORMATION_SCOPING.md`, this represents tactical intelligence the country's military has by virtue of forces being in contact.

### 3.5 [ATTACK MODIFIER FLAGS]

For each candidate (source, target) pair, the validator pre-computes which modifiers WOULD apply if the attack happens. The numbers are not random — they're derived from current state (stability, ai_level, hex flags, defender unit composition).

```
Source (6, 15) → Target (6, 14):
  Attacker (cathay): no modifiers
  Defender (persia): die_hard=false, air_support=true (per_a_05 on hex), final +1
  Net: defender +1
  Approximate attacker win rate: 28%
```

The AI uses this to gauge whether an attack is worth attempting. The win-rate table from CARD §1.3 is built into the prompt for reference.

### 3.6 [RECENT COMBAT EVENTS]

Same as movement context — last 3 rounds of `observatory_combat_results` involving my country, condensed.

### 3.7 [DECISION RULES]

```
HOW GROUND COMBAT WORKS (RISK iterative dice)
- Attacker selects units from ONE source hex, attacks ONE adjacent enemy hex
- Must leave ≥1 ground unit on every occupied FOREIGN hex (own territory may be emptied)
- Each exchange: attacker rolls min(3, attackers_alive) dice, defender rolls min(2, defenders_alive) dice
- Compare highest-vs-highest then second-vs-second; ties go to defender; losing pair removes one unit
- Loop until one side has zero units (or max 50 exchanges as safety)
- Modifiers apply to highest die per side per exchange (max bonus = +2)
- Approximate win rates: no mods 42%, def +1 28%, def +2 17%, atk -1 vs def +2 8%

ON ATTACKER VICTORY
- All surviving attackers move ONTO captured hex
- Non-ground enemy units on hex become CAPTURED → attacker's reserve, original type preserved
- Hex becomes occupied_by=attacker (owner stays original)
- IF ≥2 surviving attackers AND adjacent enemy hex AND allow_chain=true: chain attack auto-fires (leaves ≥1 unit behind on the just-captured hex)
- Chain max bound: 10 hops

ON ATTACKER DEFEAT
- Attacker forces destroyed
- Defender holds the hex
- Hex remains owned/controlled by defender
- War tiredness +1 for both sides

DECISION RULES
- decision="change"    → MUST include all 5 changes fields (source/target row+col + attacker_unit_codes)
- decision="no_change" → MUST OMIT the changes field entirely
- rationale ≥ 30 chars REQUIRED in both cases
- One attack per decision; submit multiple decisions for multiple attacks

REMINDER — no_change is a legitimate choice
Combat has real costs: unit losses, war tiredness, stability hits, GDP damage from
infrastructure destruction. If your current position serves your goals, no_change
with a clear rationale is the correct answer.
```

### 3.8 [INSTRUCTION]

```
Decide whether to LAUNCH a ground attack this round (change) or HOLD (no_change).
Either way you MUST provide a rationale of at least 30 characters.

Respond with JSON ONLY, matching the schema in CONTRACT_GROUND_COMBAT §2.
```

---

## 4. VALIDATION RULES

The validator is a pure function `validate_ground_attack(payload, units, country_state, zones) → {valid, errors, warnings, normalized}`.

### 4.1 Signature

```python
def validate_ground_attack(
    payload: dict,
    units: dict[str, dict],          # unit_code → unit state
    country_state: dict[str, dict],  # country_code → country snapshot
    zones: dict[tuple[int, int], dict],  # (row, col) → zone record (sea/land/owner)
) -> dict:
```

### 4.2 Error codes

| Code | Rule |
|---|---|
| `INVALID_PAYLOAD` | top-level must be a dict |
| `INVALID_ACTION_TYPE` | `action_type == "attack_ground"` |
| `INVALID_DECISION` | `decision in {"change","no_change"}` |
| `RATIONALE_TOO_SHORT` | rationale ≥ 30 chars after strip |
| `MISSING_CHANGES` | `decision=="change"` requires `changes` block |
| `UNEXPECTED_CHANGES` | `decision=="no_change"` must omit `changes` |
| `UNKNOWN_FIELD` | extra keys in payload or changes |
| `MISSING_COORDS` | source/target row+col required when change |
| `BAD_COORDS` | row 1..10, col 1..20 |
| `SAME_HEX` | source == target |
| `NOT_ADJACENT` | target hex must be cardinally adjacent to source on the hex grid |
| `EMPTY_ATTACKER_LIST` | attacker_unit_codes must be non-empty |
| `UNKNOWN_UNIT` | each attacker unit_code must exist |
| `NOT_OWN_UNIT` | each attacker unit must belong to country_code |
| `WRONG_UNIT_TYPE` | attackers must be ground or armor (no air, naval, missile, AD) |
| `UNIT_NOT_ON_SOURCE` | each attacker unit must be at the source hex with status=active |
| `UNIT_NOT_ACTIVE` | each attacker unit must be status=active (not embarked/reserve/destroyed) |
| `MIN_LEAVE_BEHIND` | foreign source hex must keep ≥1 ground unit (own territory exempt) |
| `TARGET_HEX_SEA` | target hex must NOT be a sea hex |
| `TARGET_FRIENDLY` | target hex must contain at least one ENEMY unit (cannot attack own territory or empty hex via attack_ground) |
| `DUPLICATE_ATTACKER` | the same unit_code appears twice in attacker_unit_codes |

### 4.3 Normalized output

On `valid: true`, the validator returns a `normalized` dict mirroring the input but with:
- All coordinates as integers
- `attacker_unit_codes` deduplicated and sorted
- `allow_chain` defaulted to `true` if missing
- `rationale` stripped

On `valid: false`, `normalized` is `None` and `errors` is a non-empty list.

---

## 5. ENGINE BEHAVIOR

The engine entry point in `engines/military.py`:

```python
def resolve_ground_combat(
    attackers: list[dict],
    defenders: list[dict],
    modifiers: list[dict],          # [{"side": "attacker"|"defender", "value": int, "reason": str}]
    precomputed_rolls: dict | None = None,  # {"attacker": [[5,3,2], ...], "defender": [[6,2], ...]}
) -> CombatResult:
```

`CombatResult` shape:

```python
@dataclass
class CombatResult:
    combat_type: str                       # "ground"
    attacker_rolls: list[list[int]]        # one inner list per exchange
    defender_rolls: list[list[int]]
    attacker_losses: list[str]             # destroyed unit_codes
    defender_losses: list[str]
    modifier_breakdown: list[dict]         # echoed from input for the visualization
    summed_attacker_bonus: int             # for at-a-glance display
    summed_defender_bonus: int
    exchanges: int
    rolls_source: str                      # "random" or "moderator"
    narrative: str
    success: bool                          # attacker won
```

### 5.1 Modifier list — built upstream by `_build_ground_modifiers`

```python
[
  {"side": "defender", "value": 1, "reason": "die_hard terrain"},
  {"side": "defender", "value": 1, "reason": "air_support: per_a_05 on hex"},
  {"side": "attacker", "value": -1, "reason": "amphibious assault from sea source"},
  {"side": "attacker", "value": 1, "reason": "ai_l4 doctrine bonus"},
]
```

The pure dice function sums these into `summed_attacker_bonus` and `summed_defender_bonus`, applies them to the highest die per side per exchange (capped at die value 6, integer math).

### 5.2 Dice ordering

Per exchange:
1. Roll `min(3, len(attackers_alive))` dice for attacker
2. Roll `min(2, len(defenders_alive))` dice for defender
3. Sort each list descending
4. Apply modifier to the highest die of each side (cap at 6)
5. Re-sort
6. Compare pairs (highest vs highest, second vs second)
7. For each losing pair, remove one unit from the losing side
8. Loop until either side has zero units

When `precomputed_rolls` is provided:
- Use the dice from `precomputed_rolls["attacker"][i]` for the i-th exchange instead of rolling
- Same for defender
- If the precomputed list runs out before combat ends → fall back to random for remaining exchanges
- The CombatResult.rolls_source is `"moderator"` if precomputed_rolls was non-empty, `"random"` otherwise

---

## 6. PERSISTENCE

### 6.1 `country_states_per_round.attack_ground_decision` JSONB

The full normalized decision payload is stored on the country's snapshot row for the round. Audit only — does not affect engine reads. Mirrors `movement_decision` / `tariff_decision` / `sanction_decision` / `opec_decision` pattern.

### 6.2 `observatory_combat_results` row

Existing table. M2 adds the column `modifier_breakdown JSONB` to it. The full row written per combat:

```
sim_run_id, scenario_id, round_num,
combat_type='ground',
attacker_country, defender_country,
location_global_row, location_global_col,
attacker_units (list[str]), defender_units (list[str]),
attacker_rolls (jsonb list-of-lists), defender_rolls (jsonb list-of-lists),
attacker_losses (list[str]), defender_losses (list[str]),
modifier_breakdown (jsonb list of {side, value, reason}),
narrative
```

### 6.3 `unit_states_per_round` updates

After combat resolves:
- Destroyed units → status='destroyed', position cleared
- Surviving attackers (on win) → moved to target hex
- Captured trophies → status='reserve', country_code reassigned to attacker, original type preserved

### 6.4 `observatory_events` rows

Per combat, one event:

```
event_type='ground_combat'
country_code=attacker
summary='cathay attacks (6,14): WIN' | '... LOSS'
payload={attacker, defender, location, losses_atk, losses_def, modifiers}
```

Plus any chain-step events (one per chain hop).

---

## 7. CHAIN MECHANIC

After a winning combat at hex T, the chain logic in `_resolve_ground_chain`:

1. If `allow_chain == false` → stop
2. If `chain_step >= max_chain (10)` → stop
3. If surviving attackers count < 2 → stop (need 1 to leave behind, 1 to attack with)
4. Find adjacent hexes with enemy units → if none, stop
5. Pick the first such hex (deterministic by row, col order) → call it T'
6. Leave 1 unit behind on T (lowest unit_code wins)
7. Move remaining attackers to attack T'
8. Recurse: validate, resolve combat, etc.
9. Each chain step writes its own `observatory_combat_results` row + event

The chain stops on the first defeat. Trophies captured at intermediate hexes still belong to the attacker.

---

## 8. NON-GOALS (out of scope for v1.0)

- **Auto-attack on adjacency.** Combat is always triggered by an explicit `attack_ground` decision. No reactive combat.
- **Combined arms (ground + air same target).** Air strikes are M3 — separate slice, separate decision, separate combat row.
- **Naval bombardment from a ship to ground.** That's a different action (`attack_bombardment`) — covered in M5.
- **Nuclear strikes.** Different action (`launch_missile` warhead=nuclear) — M7.
- **Combat fog of war / surprise attacks.** Defender always sees the attack coming. Future enhancement.
- **Withdrawal under fire.** A unit committed to combat fights to the end of the engagement. Cannot be recalled mid-combat.
- **Multi-source attacks on the same target.** Each `attack_ground` has ONE source hex. To attack the same target from multiple sources, submit multiple decisions; each resolves independently.

---

## 9. LOCKED INVARIANTS

These cannot change without a contract version bump:

1. `action_type` = `"attack_ground"` (not `declare_attack` — old name is renamed in M2)
2. RISK iterative dice with `min(3,A)` vs `min(2,D)` and ties to defender
3. Modifier list: die_hard, air_support, amphibious, ai_l4, low_morale (5 items, no more)
4. Modifier cap: max +2 to any side (the dice cap at 6 anyway)
5. Chain max: 10 hops
6. Pure dice function accepts optional `precomputed_rolls`
7. `CombatResult.attacker_rolls` is `list[list[int]]` (per-exchange), not flat
8. `CombatResult.modifier_breakdown` is the per-modifier list (not summed)
9. `observatory_combat_results.modifier_breakdown` JSONB column exists
10. Validation is pure: takes context dicts, no DB access
11. The chain mechanic lives in `_resolve_ground_chain` (resolve_round.py), NOT in the pure dice function
