# CHECKPOINT — M3 Air Strikes Vertical Slice

**Date:** 2026-04-12 | **Status:** ✅ DONE | **Owner:** Marat + Build Team

> Second offensive military action shipped under contract. Tactical air
> strikes with probability rolls + AD interception + air superiority
> bonus + per-shot dice list + modifier breakdown for visualization +
> moderator-roll override hook. Live AI plays through it.

---

## What M3 delivered

### 1. Contract — `CONTRACT_AIR_STRIKES.md` v1.0 LOCKED
8 sections, 19 error codes, 9 locked invariants. Cleaner than M2 because
air strikes have no chain mechanic, no trophies, no occupation.

### 2. Validator — `engine/services/air_strike_validator.py`
Pure function `validate_air_strike(payload, units, country_state, zones)`.
19 error codes including range check (≤2 cardinal hexes), wrong unit type
(must be tactical_air), target_friendly (must contain enemies).

### 3. L1 tests — `tests/layer1/test_air_strike_validator.py`
**23 / 23 ✅** in 0.05s.

### 4. Engine canonical — `engines/military.py:resolve_air_strike()`
New M3 canonical pure function with:
- **`precomputed_rolls`** parameter accepting per-shot rolls:
  `{"shots": [{"hit_roll": 0.05, "downed_roll": 0.30}, ...]}`
- **Per-shot result list** with `AirStrikeShot` containing
  `attacker_code`, `hit_probability`, `hit_roll`, `hit`,
  `downed_probability`, `downed_roll`, `downed`, `target_destroyed`
- **`AirStrikeResult`** model with shots list, attacker/defender losses,
  modifier_breakdown (informational, mirrors M2 shape), rolls_source
- Hit prob formula: `clamp([3%, 20%], (12% + 2% × air_sup) × (0.5 if AD else 1))`
- Downed prob: 15% if AD present
- Hit and downed are independent rolls

The legacy country-level `resolve_air_strike(inp: AirStrikeInput)` and
its `AirStrikeResult` Pydantic class were renamed to
`resolve_air_strike_legacy_v1` and `AirStrikeResultLegacyV1` to free up
the canonical names. No callers depended on the legacy versions.

### 5. Engine wiring — `engine/round_engine/resolve_round.py`
New `_process_air_strike()` handler parallel to `_process_attack`:
- Extracts source/target from `changes` envelope
- Loads attacker tactical_air, target hex defenders, AD coverage
- Counts air superiority (other friendly tac_air on source not in attacker_codes)
- Calls `engines.military.resolve_air_strike()`
- Persists ONE combat row with full per-shot list in `attacker_rolls` JSONB
- Applies losses to unit_state
- Writes `attack_air_decision` JSONB audit
- Emits `air_strike` event

`AIR_STRIKE_ACTIONS = {"attack_air"}` constant added. New handler block
in main resolve_round loop (parallel to ground combat block).

### 6. DB migrations
- `m3_air_strike_audit_column`: `country_states_per_round.attack_air_decision JSONB`
- `m3_combat_rolls_to_jsonb`: **converts `observatory_combat_results.attacker_rolls` and `defender_rolls` from `int[]` to `jsonb`**

The second migration is a critical fix that was hiding behind M2: the
`int[]` column was silently flattening M2's per-exchange list-of-lists
into a 1D array. Existing M2 data was corrupted in this way (visible
in DB: 27-die ground combats stored as flat [6,4,2,6,3,5,3,3,2,...]
instead of [[6,4,2],[6,3],[5,3,3,2]]). The JSONB migration preserves
both M2 (per-exchange list-of-lists) and M3 (per-shot dicts) shapes.

### 7. Decision context — `engine/services/combat_context.py:build_air_strike_context()`
Returns:
- `economic_state`
- `my_air_forces_by_hex` (own active tactical_air grouped by source hex)
- **`targetable_enemy_hexes`** — for each source hex, list of enemy hexes within 2 cardinal hexes with: enemy_country, defenders composition, AD coverage flag, **hit_prob_preview**, **downed_prob_preview**
- `recent_combat_events`
- `decision_rules` text + `instruction`

The previews let the AI gauge whether a strike is worth attempting.

### 8. L2 persistence test — `tests/layer2/test_air_strike_persistence.py`
**3 / 3 ✅** in 22s. Covers:
- Full DB chain: validator → resolve_round → combat row + audit + losses
- `no_change` writes zero air_strike rows
- `precomputed_rolls` engine smoke test (deterministic moderator dice)

Uses `create_isolated_run` for true per-test isolation.

### 9. L3 acceptance gate — `tests/layer3/test_air_strike_full_chain_ai.py`
**1 / 1 ✅** in 17s. Live Gemini Flash:
- Receives `build_air_strike_context()` output
- Decides change or no_change
- Production validator gates response
- `resolve_round` resolves through canonical M3 engine
- Combat row + audit + losses verified
- Run finalized as `visible_for_review`

**First AI air strike decision:** Cathay strikes Sarmatia at (4,16) from
(6,16) with cat_a_06. Rationale: *"Strike Sarmatia at (4,16) with 12%
hit probability and no AD risk to test combat effectiveness."* AI cited
the hit_prob preview from the context AND the AD-absence preview.

1 sortie → 1 hit → 1 defender destroyed. Combat row has full per-shot
dict in attacker_rolls JSONB.

### 10. Visualization — `observatory.js renderCombatTicker()`
M3 air strike branch added (parallel to M2 ground combat branch):
- **Modifiers section** — informational `{side, value, reason}` list
  with side color coding (atk/def)
- **Sorties table** — one row per attacker showing attacker_code,
  hit_probability, hit_roll, hit ✓/✗, downed_probability, downed_roll,
  downed 💀/—
- **Result line** — ATK losses / DEF losses / TARGETS HIT or NO HITS badge
- **Losses detail** — destroyed unit codes
- **Narrative**
- **moderator-roll tag** when `rolls_source === "moderator"`

Combat hex markers on the map (existing) pick up the new air_strike
combats automatically since they're tied to `state.combats`.

---

## Test coverage at M3 close

| Layer | Suite | Result |
|---|---|---|
| L1 | `test_air_strike_validator.py` | **23 / 23 ✅** (0.05s) |
| L1 | All L1 (regression) | **514 / 514 ✅** (1.00s, was 491 = +23 from M3) |
| L2 | `test_air_strike_persistence.py` | **3 / 3 ✅** (22s) |
| L2 | M2 + M3 combined sweep | **7 / 7 ✅** (42s) |
| L3 | `test_air_strike_full_chain_ai.py` | **1 / 1 ✅** (17s) |

**Net: zero regressions on prior slices**. M3 added 27 tests (23 L1 + 3 L2 + 1 L3).

---

## Bugs caught and fixed during M3

| # | Bug | Cause | Fix |
|---|---|---|---|
| 1 | `AirStrikeResult` and `resolve_air_strike` already existed in `engines/military.py` (legacy country-level) | Pre-M3 code had duplicate class/function names that would shadow my new M3 versions | Renamed legacy to `AirStrikeResultLegacyV1` + `resolve_air_strike_legacy_v1`. No callers, harmless. |
| 2 | `observatory_combat_results.attacker_rolls` was `int[]` not JSONB | Pre-M2 schema. M2's per-exchange `[[5,3,2]]` shape was being flattened to `[5,3,2]` silently. M3's per-shot dicts couldn't fit at all. | Migration `m3_combat_rolls_to_jsonb` converts both columns to jsonb via `to_jsonb()`. M2 visualization will now show the correct per-exchange shape going forward (existing rows are still flattened and would need a one-time re-resolve to fix). |

---

## Visualization data shape (live)

M3 air strike combat row from the acceptance gate:

```json
{
  "round_num": 1,
  "combat_type": "air_strike",
  "attacker_country": "cathay",
  "defender_country": "sarmatia",
  "location_global_row": 4,
  "location_global_col": 16,
  "attacker_units": ["cat_a_06"],
  "defender_units": ["sar_g_..."],
  "attacker_rolls": [
    {
      "attacker_code": "cat_a_06",
      "hit_probability": 0.12,
      "hit_roll": 0.0834,
      "hit": true,
      "downed_probability": 0.0,
      "downed_roll": 1.0,
      "downed": false,
      "target_destroyed": "sar_g_..."
    }
  ],
  "defender_rolls": [],
  "attacker_losses": [],
  "defender_losses": ["sar_g_..."],
  "modifier_breakdown": [],
  "narrative": "Air strike: 1 sorties, 1 hits, 0 attacker losses to AD (no AD, hit_prob=0.12)"
}
```

---

## Files inventory

### New
| Path | Purpose |
|---|---|
| `PHASES/UNMANNED_SPACECRAFT/CONTRACT_AIR_STRIKES.md` | v1.0 LOCKED contract |
| `PHASES/UNMANNED_SPACECRAFT/CHECKPOINT_M3_AIR_STRIKES.md` | This document |
| `app/engine/services/air_strike_validator.py` | Pure validator (~270 lines) |
| `app/tests/layer1/test_air_strike_validator.py` | 23 tests |
| `app/tests/layer2/test_air_strike_persistence.py` | 3 tests |
| `app/tests/layer3/test_air_strike_full_chain_ai.py` | Acceptance gate |

### Modified
| Path | Reason |
|---|---|
| `app/engine/engines/military.py` | Added M3 `AirStrikeShot` + `AirStrikeResult` + `resolve_air_strike()` canonical. Renamed legacy class + fn to `*LegacyV1`. |
| `app/engine/round_engine/resolve_round.py` | New `_process_air_strike` handler + `AIR_STRIKE_ACTIONS` constant + main loop block |
| `app/engine/services/combat_context.py` | Added `build_air_strike_context()` + `_air_strike_rules_text()` |
| `app/test-interface/static/observatory.js` | M3 air_strike branch in `renderCombatTicker` |
| `PHASES/UNMANNED_SPACECRAFT/CARD_ACTIONS.md` | §1.4 status flipped to LIVE — slice locked v1.0 |

### NOT touched (kept as-is per the M3 plan)
- `app/engine/round_engine/combat.py` — `resolve_air_strike()` legacy still here, called by the OLD `_resolve_ranged_strikes` path (when an `attack_ground` decision contains air units mixed with ground units). M2/M3 split: `attack_ground` may still go through that legacy path; pure `attack_air` decisions go through the new M3 handler. The legacy path will be retired in a future cleanup once nothing references `combat.py` ground combat function (already migrated in M2).

---

## Open items deferred to F1.1 / future slices

1. **Re-resolve M2 ground combat acceptance gate** so its corrupted-flattened rolls get rewritten with proper per-exchange shape. (Or re-run the test, which will overwrite the visible row.)
2. **`combat.py:resolve_air_strike` is now redundant** when called via `attack_air` action — only used by the legacy mixed-attacker `_resolve_ranged_strikes` path.
3. **AD coverage logic** uses the existing `_ad_units_in_zone` helper which checks same-hex AND adjacent-hex. The contract preview only checks same-hex. Slight inconsistency between context preview and engine reality.
4. **Air superiority count** is currently just other friendly tactical_air on the SOURCE hex. The CARD definition is more sophisticated (requires "air superiority unit type") but the simpler interpretation works for now.

---

## What this unlocks

1. **M4 Naval combat** can follow the same pattern: pure dice fn + precomputed_rolls + modifier_breakdown + per-engagement result list
2. **Visualization handles 2 combat shapes now** — adding M4/M5/M6 is just adding new branches to `renderCombatTicker`
3. **JSONB combat rolls column** unlocks any future combat shape without schema changes
4. **The 2 visible runs** (M2 + M3 acceptance gates) sit side-by-side in the Observatory — the user can switch between them and see the same combat panel render two different combat types correctly

---

## Next on the plate

```
M2 Ground Combat ✅
M3 Air Strikes ✅
   ↓
M4 Naval combat (1v1 dice, simpler than ground)    ← NEXT
   ↓
M5 Naval bombardment + Blockades
   ↓
M6 Nuclear (launch_missile + interception)
   ↓
F1.1 polish
   ↓
Transactions + Agreements + Covert + Domestic
   ↓
CONCEPT/SEED reconciliation
   ↓
AI Participant Module v1.0
```
