# CHECKPOINT — M2 Ground Combat Vertical Slice

**Date:** 2026-04-12 | **Status:** ✅ DONE | **Owner:** Marat + Build Team

> First true offensive military action shipped under contract. RISK
> iterative dice + chain mechanic + 5 modifiers + trophies + occupation
> + per-exchange dice + modifier breakdown for visualization +
> moderator-dice override hook. Live AI plays through it.

---

## What M2 delivered

### 1. Contract — `CONTRACT_GROUND_COMBAT.md` v1.0 LOCKED
9 sections, 21 error codes, locked invariants (action_type, RISK mechanic,
modifier list, chain max, dice list-of-lists shape, modifier_breakdown
shape, precomputed_rolls hook).

### 2. Validator — `engine/services/ground_combat_validator.py`
Pure function `validate_ground_attack(payload, units, country_state, zones)`.
21 error codes. Atomic batch validation. No DB access.

### 3. L1 tests — `tests/layer1/test_ground_combat_validator.py`
**33 / 33 ✅** in 0.15s. Covers every error code, happy path, normalized
output shape, multi-error collection.

### 4. Engine canonical — `engines/military.py:resolve_ground_combat()`
New M2 canonical pure dice function with:
- **`precomputed_rolls`** parameter (default `None` = random; pass dice
  to support moderator input or deterministic tests)
- **`modifiers: list[dict]`** instead of summed bonus dict — full
  `{side, value, reason}` breakdown echoed in result
- **Per-exchange dice as list-of-lists** (one inner list per exchange,
  not flattened) for the visualization
- **`GroundCombatResult`** Pydantic model with `rolls_source`, `summed_*_bonus`,
  `exchanges`, full `modifier_breakdown`

### 5. Engine wiring — `engine/round_engine/resolve_round.py`
- `ATTACK_ACTIONS = {"declare_attack", "attack_ground"}` (legacy + M2)
- `_process_attack()` recognizes both shapes, extracts from `changes`
  envelope when M2, persists `attack_ground_decision` JSONB audit
- `_resolve_ground_chain()` accepts `country_state` + `allow_chain`,
  passes through to canonical dice fn
- `_build_ground_modifiers()` rewritten to return the 5-modifier list
  with reasons (not the old `{defender_bonus: 2}` summed dict)
- Chain mechanic preserved as-is; only the dice call is rewired
- Combat row write enriched with `modifier_breakdown` JSONB

### 6. DB migration — `m2_ground_combat_audit_columns`
- `country_states_per_round.attack_ground_decision JSONB` (audit)
- `observatory_combat_results.modifier_breakdown JSONB` (visualization)

### 7. Decision context — `engine/services/combat_context.py`
`build_ground_combat_context(country_code, scenario_code, round_num, sim_run_id?)`.

Returns the M2 decision-specific context dict with:
- `economic_state` (gdp, treasury, stability, war_tiredness, at_war_with)
- `my_ground_forces_by_hex` (groupings of own active grounds by source hex)
- **`adjacent_enemy_hexes`** — pre-computed list of (source, target,
  enemy_country, defenders_composition, modifier_preview) for every
  legal attack the AI could declare
- `recent_combat_events` (last 3 rounds)
- `decision_rules` text + `instruction`

### 8. L2 persistence test — `tests/layer2/test_ground_combat_persistence.py`
**4 / 4 ✅**. Covers:
- Full DB chain: validator → resolve_round → combat row + audit + losses
- `no_change` writes zero combat rows
- `precomputed_rolls` engine smoke test
- Modifier breakdown passed through end-to-end

Uses `create_isolated_run` for true per-test isolation.

### 9. L3 acceptance gate — `tests/layer3/test_ground_combat_full_chain_ai.py`
**1 / 1 ✅** in 20s. Live Gemini Flash AI:
- Receives the build_ground_combat_context output
- Decides `change` or `no_change`
- Production validator gates the response
- `resolve_round` applies the canonical pure dice
- Combat row + audit + losses verified
- Run finalized as `visible_for_review` for Observatory inspection

**First AI ground combat decision:** Cathay attacks Bharata at (7,15)
from (7,16) with cat_g_02. Rationale: *"Attacking Bharata at (7,15) with
favorable odds - no defensive modifiers and only 2 defenders vs our
ground unit. Low risk expansion opportunity."* Combat resolves: Cathay
ATK 3 vs Bharata DEF 2 → ATTACKER WINS, 1 defender lost.

### 10. Visualization — Observatory rewire
`observatory.js` `renderCombatTicker()` rewritten for M2 ground combat:
- Modifiers section with side-coded `{value, reason}` list
- Per-exchange dice table (Exchange # | Attacker | Defender)
- Result line with ATK losses / DEF losses / winner badge
- Losses detail
- Narrative line
- "moderator-input dice" tag when `rolls_source == "moderator"`

CSS in `observatory.css` for `.obs-combat-mods`, `.obs-combat-dice`,
`.obs-combat-result`, `.obs-combat-mod-tag`.

Battle markers on the map (already existed in `renderBattleMarkers`)
pick up the new combat rows automatically since they're tied to
`state.combats`.

---

## Test coverage at M2 close

| Layer | Suite | Result |
|---|---|---|
| L1 | `test_ground_combat_validator.py` | **33 / 33 ✅** (0.15s) |
| L1 | All other validators (regression check) | **491 / 491 ✅** (1.05s, +33 from M2 = was 458) |
| L2 | `test_ground_combat_persistence.py` | **4 / 4 ✅** (22s) |
| L2 | All slice persistence + sim_run_manager (regression) | **32 / 32 ✅** (6m) — full sweep green |
| L3 | `test_ground_combat_full_chain_ai.py` | **1 / 1 ✅** (20s) |

**Net: zero regressions on the 5 prior slices** (budget / tariff /
sanction / opec / movement). M2 added 38 tests (33 L1 + 4 L2 + 1 L3).

---

## Visualization data shape (live)

Current M2 acceptance gate combat row in `observatory_combat_results`:

```json
{
  "round_num": 1,
  "combat_type": "ground",
  "attacker_country": "cathay",
  "defender_country": "bharata",
  "location_global_row": 7,
  "location_global_col": 15,
  "attacker_rolls": [[3]],
  "defender_rolls": [[2]],
  "attacker_losses": [],
  "defender_losses": ["bha_g_04"],
  "modifier_breakdown": [],
  "narrative": "Ground combat (1 exchanges, atk_bonus=+0, def_bonus=+0): attackers -0, defenders -1. ATTACKER WINS"
}
```

Note: `attacker_rolls` and `defender_rolls` are list-of-lists (one inner
list per exchange) — exactly the shape the visualization needs. The
flat-list legacy shape is gone.

---

## Bugs caught and fixed during M2

| # | Bug | Cause | Fix |
|---|---|---|---|
| 1 | L2 sweep had transient failure on ground_combat persistence test | Test interaction with other persistence tests sharing the legacy run + scenario_id queries | Re-ran clean — passed 32/32. Real fix is migrating other slice tests to `create_isolated_run` (deferred to F1.1) |
| 2 | Visible runs (`status=visible_for_review`) pollute `_seed_round_from_r0` queries in pre-F1 fixture-style tests | Same root cause as during F1: query by `scenario_id` returns rows from multiple sim_run_ids | Documented as F1.1 cleanup. M2 acceptance gate uses `create_isolated_run` so its OWN test is immune. Other tests need migration. |

---

## Files inventory

### New
| Path | Purpose |
|---|---|
| `PHASES/UNMANNED_SPACECRAFT/CONTRACT_GROUND_COMBAT.md` | v1.0 LOCKED contract |
| `PHASES/UNMANNED_SPACECRAFT/PLAN_M2_GROUND_COMBAT.md` | Execution plan |
| `PHASES/UNMANNED_SPACECRAFT/CHECKPOINT_M2_GROUND_COMBAT.md` | This document |
| `app/engine/services/ground_combat_validator.py` | Pure validator (350 lines) |
| `app/engine/services/combat_context.py` | Context builder (280 lines) |
| `app/tests/layer1/test_ground_combat_validator.py` | 33 tests |
| `app/tests/layer2/test_ground_combat_persistence.py` | 4 tests |
| `app/tests/layer3/test_ground_combat_full_chain_ai.py` | Acceptance gate |

### Modified
| Path | Reason |
|---|---|
| `app/engine/engines/military.py` | Added `GroundCombatResult` + `resolve_ground_combat()` canonical pure dice |
| `app/engine/round_engine/resolve_round.py` | `_process_attack` + `_resolve_ground_chain` + `_build_ground_modifiers` rewired to call new canonical fn, audit JSONB write, allow_chain support |
| `app/test-interface/static/observatory.js` | `renderCombatTicker()` rewritten for M2 ground combat shape |
| `app/test-interface/static/observatory.css` | Combat panel styling (modifiers, dice table, result, mod tag) |
| `PHASES/UNMANNED_SPACECRAFT/CARD_ACTIONS.md` | §1.3 status flipped to LIVE — slice locked v1.0 |

### NOT touched (kept as-is per the M2 plan)
- `app/engine/round_engine/combat.py` — `resolve_air_strike`, `resolve_missile_strike`, `resolve_naval`, naval bombardment all stay here. The OLD `resolve_ground_combat` in this file is now unused and superseded by the canonical M2 version in `engines/military.py`. M3 / M4 / M5 will migrate the remaining functions over the same way.

---

## Open items deferred to F1.1 / future slices

1. **Drop the unused `resolve_ground_combat` from `round_engine/combat.py`** — superseded by `engines/military.resolve_ground_combat`. Keep the rest of `combat.py` until M3 ports the air dice function.
2. **Migrate L2 slice persistence tests to `create_isolated_run`** — eliminates the pollution-by-scenario_id problem entirely.
3. **Hex-level land/sea zones table** — the validator currently infers hex type from unit positions; a proper hex-level zones table would let the validator catch attempted ground deploys to sea hexes the engine doesn't know about yet.
4. **Modifier reasons for `die_hard` terrain** — hex flag wiring is TODO. Currently always `false` because no template hex flag table exists.
5. **Ground combat decisions in `full_round_runner.py`** — not yet exposed to the orchestrator's mandatory decisions phase. M2 only exposes it at the AI skill level.

---

## What this unlocks

1. **M3 Air Strikes** can follow the same 7-step pattern with the slice already proven
2. **The visualization data shape is locked** — M3/M4/M5 just have to populate `attacker_rolls` / `defender_rolls` / `modifier_breakdown` in the same shape
3. **Moderator dice input** is one tiny UI plug away — the engine accepts pre-rolled dice today
4. **AI Participant Module v1.0** has another action shape to consume; the F1_CONTEXT_GAPS recommendations apply identically

---

## Next on the plate

Per the strategic directive, the order is:

```
M2 Ground Combat ✅
   ↓
M3 Air Strikes      ← NEXT
   ↓
M4 Naval combat
   ↓
M5 Naval bombardment + blockades
   ↓
M6 Nuclear (launch_missile + interception)
   ↓
F1.1 polish
   ↓
Transactions + Agreements + Covert ops + Domestic actions
   ↓
CONCEPT/SEED reconciliation pass
   ↓
AI Participant Module v1.0
```
