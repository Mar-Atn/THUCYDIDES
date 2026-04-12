# PLAN M2 — Ground Combat Vertical Slice

**Status:** DRAFT for review | **Owner:** Marat + Build Team | **Drafted:** 2026-04-12
**Predecessor:** F1 Sim Run Foundation ✅, M1 Movement ✅
**Successor:** M3 Air Strikes (after this)
**Methodology:** Same 7-step vertical slice pattern as Budget / Tariffs / Sanctions / OPEC / Movement

---

## Why M2 next

Per Marat's strategic directive (2026-04-10):
> tariffs → sanctions → oil → **military actions (standard / blockade / nuclear) → military movements** → nuclear decisions → transactions → agreements → other actions

We've shipped 4 economic mandatory decisions + movement (military prereq).
**Ground combat is the first true offensive military action**, and it
unlocks the rest of the military slice chain. It's also the most
mechanically rich (RISK iterative dice + chain mechanic + modifiers +
trophies + occupation), so getting the contract right here pays dividends
for M3-M6.

---

## What already exists vs what needs work

### Already in code (LIVE per CARD_ACTIONS 1.3)

- `engine/round_engine/combat.py:resolve_ground_combat()` (398 lines) — pure RISK iterative dice with modifiers (die_hard, air_support, amphibious, AI L4, low morale)
- `engine/round_engine/resolve_round.py:_process_attack()` — entry point invoked from `resolve_round` for `declare_attack` decisions
- `engine/round_engine/resolve_round.py:_resolve_ground_chain()` — chain mechanic (recursive attack to adjacent hexes after a win)
- `engine/round_engine/resolve_round.py:_build_ground_modifiers()` — terrain / morale / AI level checks
- `_combat_row()` writer that persists to `observatory_combat_results` (already keyed by `sim_run_id` after F1 rewire)
- `engine/engines/military.py:resolve_ground_combat_units()` — unit-level v2 implementation (pydantic-typed, 2688 line file)

### What's missing (M2 work)

1. **No CONTRACT** — there's no `CONTRACT_GROUND_COMBAT.md` locking the action schema, normalized payload, error codes, validator preview semantics
2. **No standalone validator** — combat eligibility checks live inside `_process_attack` and are scattered (range, friendly fire, source hex, etc.). Should be a pure `validate_ground_attack()` function like the 5 prior slices have
3. **Action_type collision** — code uses `declare_attack`, CARD_ACTIONS spec says `attack_ground`. One must rename to match
4. **No L1 unit tests for validator** — the engine has L1 dice tests but the *eligibility* logic isn't covered
5. **No L2 persistence test** — there's no `test_ground_combat_persistence.py` exercising the full DB chain
6. **No L3 AI full-chain test** — no test_ground_combat_full_chain_ai.py
7. **No combat-specific decision context builder** — `engine/services/combat_context.py` doesn't exist; AI gets nothing tailored
8. **`engine/round_engine/combat.py` is marked DEPRECATED** but still in active use. Either fully port to `engines/military.py` v2 or un-deprecate. Pick one and document.

---

## Marat — open contract questions to lock before execution

### Q1 — Trigger & action_type
**Question:** Is ground combat triggered by a SUBMITTED `attack_ground` decision only, or also by automatic adjacency detection?
**Recommendation:** Submitted-only (matches `declare_attack` semantics today, matches all other actions in the system, gives the AI agency).
**Also:** Rename `declare_attack` → `attack_ground` to match CARD_ACTIONS spec, OR update CARD_ACTIONS to say `declare_attack`. Pick one.

### Q2 — Per-round limit
**Question:** How many ground attacks per country per round?
**Options:** (a) 1 attack action per country, (b) N independent attacks, (c) unlimited
**Recommendation:** **No fixed limit but each `attack_ground` decision = ONE source hex → ONE target hex**. A country wanting to attack 3 hexes submits 3 decisions. Last-submission-wins doesn't apply (each is independent because source hex differs). Matches CARD_ACTIONS §1.3 step 1: "from ONE source hex".

### Q3 — Chain mechanic policy
**Question:** Keep the existing recursive chain implementation as canonical, or rewrite under contract?
**Recommendation:** **KEEP IT** — `_resolve_ground_chain()` is already well-shaped. The M2 slice locks a `chain_step <= max_chain` invariant in the contract and adds tests. Same pattern as Sanctions slice (engine kept, contract locked around it).

### Q4 — Modifier scope
**Question:** Which modifiers are in M2 scope vs deferred?
**Listed in CARD_ACTIONS 1.3:**
- Die Hard terrain (defender +1) — NEEDS template hex flag wiring
- Air support (defender +1) — needs tactical_air detection on target hex
- Amphibious assault (attacker -1) — needs sea-source/land-target detection
- AI L4 bonus (either +1) — needs `ai_level==4 AND ai_l4_random_flag` country state
- Low morale (either -1) — needs `stability <= 3` country state read

**Recommendation:** **All 5 in scope**. They already exist in code, the contract just needs to formalize them and L1 tests need to verify each.

### Q5 — Trophies & occupation tracking
**Question:** Are captured non-ground units (trophies) and hex occupation in M2 scope?
**Recommendation:** **YES** (already in `_resolve_ground_chain`). The contract locks the trophy capture rule (non-ground enemy units on captured hex → attacker's reserve, original type preserved) and the occupation rule (`occupied_by` field).

### Q6 — Validator preview
**Question:** Should the validator support a "dry run" preview (would-this-attack-be-legal-without-committing)?
**Recommendation:** **YES** — same shape as `validate_movement_decision`. Returns `{valid, errors[], normalized}`. AI Participant Module will use this for tool-use.

### Q7 — `engine/round_engine/combat.py` deprecation
**Question:** Port the ground combat function fully into `engines/military.py` v2, or un-deprecate the round_engine module?
**Recommendation:** **Port and delete** as part of M2 closing — same pattern as M1 movement closing where we deleted `round_engine/movement.py`. The pure dice function moves to `engines/military.py:resolve_ground_combat_units()` (already exists, just needs to be the canonical caller from `_process_attack`).

### Q8 — Naming collisions
**Question:** Are there other deprecated combat helpers to clean up?
**To check during execution:** `_apply_losses`, `_capture_trophies`, `_move_attackers_forward`, `_build_ground_modifiers`, `_ad_units_in_zone` — should they live in `engines/military.py` or stay as resolve_round helpers?
**Recommendation:** Keep them in `resolve_round.py` as private helpers since they touch the round's `unit_state` dict (impure). Only the pure RISK dice function migrates.

### Q9 — Moderator dice override (added 2026-04-12 per Marat)
**Question:** Should the pure dice function accept *pre-rolled* dice as an optional input, so a human moderator can input physical dice rolls during a real-table game?
**Recommendation:** **YES.** The engine's `resolve_ground_combat()` signature gains an optional `precomputed_rolls` parameter. When `None` (the unmanned default), the function rolls its own random dice as today. When provided as `{"attacker": [[5,3,2], [6,4,3]], "defender": [[6,2], [4,1]]}` (one inner list per exchange), the function consumes them in order.

This is a tiny change (~10 lines in the dice function) and a HUGE win for future use:
- Unmanned mode: random dice, no change to current behavior
- Test mode: deterministic dice for unit tests (no flaky asserts on random outcomes)
- Moderated table mode: physical dice input by the moderator
- Replay / what-if mode: re-resolve a past combat with different modifiers

The dice + result get stored on `observatory_combat_results.attacker_rolls` / `defender_rolls` regardless of source. The Observatory doesn't care whether the dice came from `random` or a moderator's hand — it just renders them.

The moderator dice input UI is **out of scope** for M2 (belongs to a future facilitator UI phase). M2 just adds the engine API hook so the future UI can plug in cleanly.

---

## Visualization & Moderator Override (added 2026-04-12 per Marat)

### What the user wants to see when scrubbing rounds in the Observatory

1. **Combat hex marker on the map** — when a hex was the location of a combat in the currently-viewed round, display a visible icon (💥 / crossed swords / pulse) on that hex. Markers fade or persist for a round so the user can see "combat happened here last round" while scrubbing forward.

2. **"Combats This Round" panel below the map** — already exists in the Observatory but is empty. M2 ships the renderer that fills it. Each combat row shows:
   - **Header:** attacker country → defender country @ (row, col), combat_type
   - **Modifiers BEFORE the combat** — full breakdown of every modifier that was applied to either side, with reason text:
     ```
     Defender: +1 (die_hard terrain), +1 (air_support: cat_a_05 on hex)
     Attacker: -1 (amphibious assault: source col_n_06 sea hex)
     ```
   - **Dice rolled** — for ground combat, every exchange's dice listed. For ranged, the probability roll:
     ```
     Exchange 1:  ATK [6, 5, 3]  DEF [4, 2]
     Exchange 2:  ATK [6, 5]     DEF [3, 1]
     Exchange 3:  ATK [4]        DEF []
     ```
   - **Final result — two numbers**: attacker losses count, defender losses count, plus winner. The user wanted "two numbers indicating who won the combat."
     ```
     RESULT: ATK losses = 1   DEF losses = 3   →  ATTACKER WINS
     ```
   - **Narrative line** at the bottom

3. **The same panel handles "this round" and "last round" semantics**. When the user clicks round N, the panel shows combats that happened *during* round N. There's no separate "last round" panel — the round scrubber already handles "before vs after" by letting the user click R(N-1) vs R(N).

### Data we already have in `CombatResult`

The existing `CombatResult` dataclass already captures everything the panel needs:

```python
@dataclass
class CombatResult:
    combat_type: str
    attacker_rolls: list[int]      # flat list (will become list[list[int]] for per-exchange display)
    defender_rolls: list[int]
    attacker_losses: list[str]     # destroyed unit_codes
    defender_losses: list[str]
    modifiers_applied: dict        # currently {defender_bonus, attacker_bonus, exchanges}
    narrative: str
    success: bool
```

**Two enrichments are needed for the visualization:**
- `attacker_rolls` / `defender_rolls` should become **list of lists** (one inner list per exchange) instead of flat. The data is already structured this way internally — just stop flattening it at the end of `resolve_ground_combat()`.
- `modifiers_applied` should become a **list of `{side, value, reason}` objects** instead of summed bonuses. Today the dict says `{defender_bonus: 2}`. The renderer needs to know +1 came from die_hard, +1 came from air_support. Build this dict during `_build_ground_modifiers` (already collects the boolean flags) and pass through to the result.

These two changes are part of M2's engine work and unlock the visualization without inventing any new data flow.

### Database storage

`observatory_combat_results` already has columns for `attacker_rolls`, `defender_rolls`, `attacker_losses`, `defender_losses`, `narrative`. M2 adds:
- `modifier_breakdown` JSONB — the per-modifier list described above
- (Optional) `precomputed_rolls_source` text — `"random"` (unmanned) or `"moderator"` (future)

### Moderator dice input — engine hook only (Q9)

`resolve_ground_combat()` gains an optional `precomputed_rolls` parameter. Default `None` = use `random.randint(1,6)` as today. When provided, consume the supplied dice in order. Same applies to `resolve_air_strike()` (probability roll input) and `resolve_missile_strike()`. The future facilitator UI calls the engine with moderator-input dice; the Observatory then renders identical-looking combat rows.

### What the M2-VIS demo run will show

After M2 ships, a `test_combat_visible_demo.py` produces a 2-3 round visible run with:
- Pre-positioned forces in adjacent hexes (Cathay vs Persia near Eastern Eurasia, say)
- Round 1: Cathay declares attack_ground on Persia hex
- The combat resolves with deterministic dice (`precomputed_rolls` for reproducibility)
- Round 2: counter-attack by Persia, with different modifiers
- Round 3: a chain attack demonstrating multi-hex sequence
- Run finalizes as `visible_for_review`

When you pick this run from the Observatory selector and scrub R0 → R1 → R2 → R3, you see:
- **Map:** combat hex markers appearing on the attacked hexes, units actually disappearing where losses occurred
- **Combats This Round panel:** every detail per the spec above
- **Movements This Round panel** (already shipped in M1-VIS): the unit repositions that preceded the attack

---

## Outcome — definition of done

1. `CONTRACT_GROUND_COMBAT.md` written, locked (v1.0)
2. `engine/services/ground_combat_validator.py` — pure function `validate_ground_attack(payload, units, country_state, world_state) -> {valid, errors, warnings, normalized}` with N error codes
3. `engine/round_engine/combat.py` deleted; pure ground dice function lives in `engines/military.py` only (canonical)
4. `engine/round_engine/resolve_round.py:_process_attack` rewired to call the validator first, then the pure dice function from `engines/military.py`
5. `agent_decisions.action_type` = `attack_ground` (rename from `declare_attack`); migration handles legacy data
6. `country_states_per_round.attack_ground_decision` JSONB audit column added (matches budget/tariff/sanction/opec/movement_decision pattern)
7. `engine/services/combat_context.py` — `build_ground_combat_context(country, scenario, round_num, sim_run_id?) -> dict` (validator-grade, no cognitive layer per F1 boundary)
8. **L1 tests** in `tests/layer1/test_ground_combat_validator.py` — every error code, every modifier, edge cases (empty hex, friendly target, bad coords, distance, source != adjacency)
9. **L2 persistence test** in `tests/layer2/test_ground_combat_persistence.py` — scripted decision → resolve_round → snapshot reflects losses + occupation + trophies
10. **L3 AI full-chain test** in `tests/layer3/test_ground_combat_full_chain_ai.py` — AI receives context → produces attack_ground payload → validator accepts → engine resolves → snapshot verified
11. **Acceptance gate** — full chain test green, observatory_combat_results row visible, country snapshot reflects losses
12. **L1+L2+L3 all green** + 100% of existing L1/L2/L3 sweep still green (no regressions)
13. **Visualization (per Q9 + Visualization section above):**
    - `CombatResult.attacker_rolls` / `defender_rolls` → list-of-lists (per exchange)
    - `CombatResult.modifier_breakdown` → list of `{side, value, reason}` objects
    - `observatory_combat_results.modifier_breakdown JSONB` column added
    - `engines/military.resolve_ground_combat_units()` accepts optional `precomputed_rolls` parameter (default None = random)
    - Observatory MAPS tab shows combat hex markers for combats in the currently-viewed round
    - Observatory "Combats This Round" panel populated with: header / modifiers-with-reasons / per-exchange dice / loss totals / winner / narrative
    - `tests/layer3/test_combat_visible_demo.py` produces a 2-3 round visible run demonstrating attack + chain + counter-attack
14. `CHECKPOINT_M2_GROUND_COMBAT.md` written

---

## Step-by-step execution (the same 7-step pattern)

### Step 1 — Lock the contract
- Write `CONTRACT_GROUND_COMBAT.md` v1.0
- Define payload schema (`attack_ground`, `attacker_unit_codes`, `target_global_row`, `target_global_col`, optional `chain_target_hexes`)
- Define error codes (probably ~15-20: NO_SOURCE_UNITS, NOT_OWN_UNITS, BAD_COORDS, NOT_ADJACENT, FRIENDLY_FIRE, BAD_UNIT_TYPE, OUT_OF_MIN_LEAVE_BEHIND, …)
- Define normalized output shape
- Define modifier list + lookup keys
- Define chain mechanic invariants

### Step 2 — Validator
- Pure function in `engine/services/ground_combat_validator.py`
- Takes payload + units dict + country_state dict + world_state dict
- Returns `{valid: bool, errors: list[str], warnings: list[str], normalized: dict | None}`
- Mirror the shape of `movement_validator.validate_movement_decision`
- Includes `_check_adjacency`, `_check_unit_ownership`, `_check_unit_types`, `_check_target`, `_check_min_leave_behind`

### Step 3 — Engine cleanup
- Move pure RISK dice function from `round_engine/combat.py` → `engines/military.py:resolve_ground_combat_units` (already 80% there)
- Update `resolve_round._process_attack` to:
  1. Call `validate_ground_attack` first
  2. On valid: call pure dice function
  3. Apply losses to `unit_state`
  4. Apply trophies + occupation
  5. Persist combat row + audit + events
- Delete `round_engine/combat.py`
- Update all imports: `from engine.round_engine import combat as combat_mod` → `from engine.engines import military`

### Step 4 — DB migration
- Add `country_states_per_round.attack_ground_decision JSONB` column
- (Audit only — actual combat results live in `observatory_combat_results`)

### Step 5 — Decision context builder
- `engine/services/combat_context.py:build_ground_combat_context(country, scenario, round_num, sim_run_id=None)`
- Returns: own_units in source hexes, adjacent enemy hexes, modifier flags, country state (stability, ai_level), recent_combat events, decision_rules text, instruction
- Pure read, no DB writes
- Decision-specific only (NOT cognitive — per F1 boundary)

### Step 6 — AI harness
- New `tests/layer3/test_skill_ground_combat.py` (mirror `test_skill_movement.py`)
- `MovementScenario`-equivalent dataclass for combat: source hex with attackers, target hex with defenders, modifiers
- Prompt builder
- LLM call helper
- Reference Cathay-vs-Persia or Columbia-vs-Sarmatia scenario

### Step 7 — Acceptance gate
- `tests/layer3/test_ground_combat_full_chain_ai.py`
- Creates a fresh sim_run via `create_isolated_run`
- Seeds R0 + sets up a deliberate adjacent enemy hex
- Asks AI to decide an attack
- Validator accepts
- `resolve_round` executes
- Verifies: combat row in `observatory_combat_results`, unit losses in `unit_states_per_round`, occupation marked, audit JSONB populated
- Finalizes the run as `visible_for_review` so it shows up in the Observatory selector for visual review

### Closing — same legacy cleanup discipline as M1
- Delete `engine/round_engine/combat.py`
- Update CARD_ACTIONS.md to mark status `LIVE — slice locked v1.0`
- Update PHASE.md status section
- Write `CHECKPOINT_M2_GROUND_COMBAT.md`
- Run full L1+L2 sweep, confirm zero regressions
- Add a `M2-VIS` visible demo similar to M1-VIS-MEGA: scripted attack scenario, 2-3 rounds, multiple attacks, see the combat play out on the map

---

## Risks

| Risk | Mitigation |
|---|---|
| Modifier wiring requires template hex flags (die_hard) that may not be seeded | Skip die_hard test cases on hexes that lack the flag; add a Fix-data-later TODO. The validator + engine still works, just no defender bonus on those hexes. |
| Action_type rename `declare_attack` → `attack_ground` may break legacy event payloads | Migration: backfill rename in `agent_decisions.action_type` for the legacy archived run. Existing events use the old name in payload field, leave them. |
| Adjacency check needs hex-level neighbor logic, not zone-level | Build a small `_hex_neighbors(row, col)` helper in the validator. Standard hex grid math, ~10 lines. |
| Chain mechanic interaction with trophy capture has edge cases (e.g., attacker chains into a hex with trophies but loses) | L1 unit tests for: chain stops on loss, trophies not captured if attacker dies, max_chain bound (10 from current code). |
| `engines/military.py` v2 is 2688 lines and intimidating to surgically modify | Touch only the ground combat section. Don't refactor the rest. |
| AI may reject the prompt or produce invalid payloads (it's a more complex schema than movement) | The L3 test gets up to 3 retries; if AI consistently fails, capture the prompt and iterate it before claiming the slice done. |

---

## Scope boundaries

**IN scope:**
- `attack_ground` action with full RISK iterative dice + chain mechanic
- All 5 modifiers from CARD_ACTIONS §1.3
- Trophy capture
- Hex occupation tracking
- Validator + L1 unit tests
- Persistence + L2 integration test
- AI full-chain + L3 acceptance gate
- Decision-specific context builder
- Visible demo run

**OUT of scope (next slices):**
- M3 Air strikes (`attack_air`)
- M4 Naval combat (`attack_naval`)
- M5 Naval bombardment (`attack_bombardment`)
- M6 Blockades (`declare_blockade`)
- M7 Nuclear (`launch_missile` warhead=nuclear)
- Ground combat AI participants making STRATEGIC decisions about WHEN to attack — that's the AI Participant Module v1.0 work, not M2. M2 just proves the action *can* be invoked correctly through the AI flow.

---

## Execution sequence (when approved)

1. Lock contract (Step 1)
2. Build validator + L1 tests (Step 2)
3. Cleanup engine, delete deprecated combat.py (Step 3)
4. DB migration (Step 4)
5. Build context service (Step 5)
6. Build AI harness (Step 6)
7. Acceptance gate test (Step 7)
8. Add M2-VIS demo run
9. Closing: CARD_ACTIONS update, PHASE.md update, CHECKPOINT_M2 written
10. Full L1+L2+L3 sweep — must stay green

**Green-light checkpoint after each numbered step.** If a step regresses earlier slice tests, stop and diagnose before proceeding.

---

## Estimated touch list

| File | Action |
|---|---|
| `PHASES/UNMANNED_SPACECRAFT/CONTRACT_GROUND_COMBAT.md` | NEW |
| `app/engine/services/ground_combat_validator.py` | NEW (~400 lines) |
| `app/engine/services/combat_context.py` | NEW (~250 lines) |
| `app/engine/engines/military.py` | EDIT — promote ground dice to canonical |
| `app/engine/round_engine/resolve_round.py` | EDIT `_process_attack` to use validator + canonical dice |
| `app/engine/round_engine/combat.py` | DELETE |
| `app/tests/layer1/test_ground_combat_validator.py` | NEW (~25 tests) |
| `app/tests/layer2/test_ground_combat_persistence.py` | NEW (~7 tests) |
| `app/tests/layer3/test_skill_ground_combat.py` | NEW (mirror of test_skill_movement.py) |
| `app/tests/layer3/test_ground_combat_full_chain_ai.py` | NEW |
| `app/tests/layer3/test_combat_visible_demo.py` | NEW (M2-VIS demo, scripted) |
| `app/test-interface/static/observatory.js` | EDIT — add `renderCombatTicker()` filling the existing panel + combat hex markers on the SVG |
| `app/test-interface/static/observatory.css` | EDIT — combat row styling (mirror movement panel) |
| DB migration `attack_ground_audit_column` | NEW (also adds `modifier_breakdown` to observatory_combat_results) |
| `PHASES/UNMANNED_SPACECRAFT/CARD_ACTIONS.md` | EDIT — flip status to LIVE |
| `PHASES/UNMANNED_SPACECRAFT/PHASE.md` | EDIT — mark M2 done |
| `PHASES/UNMANNED_SPACECRAFT/CHECKPOINT_M2_GROUND_COMBAT.md` | NEW |

Plus any test imports that reference `combat as combat_mod` get rewired.
