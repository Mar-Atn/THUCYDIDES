# TTT Map + Units — Changes Log

**Purpose:** Running record of all modifications made during the map harness build and unit disposition work (2026-04-04 onwards). For documentation once this exercise concludes.

---

## 🏗 REUNIFICATION SPRINT — Phase 2 Agent Migration (2026-04-06)

**Scope:** Replace the parallel test-harness agent (`stage5_test.run_stage5_test`) with the designed `LeaderAgent` + cognitive blocks, via the dual-provider `llm_tools` wrapper.

### New canonical module

**`app/engine/agents/leader_round.py`** (~260 lines) — single-agent-round flow that:
- Initializes a `LeaderAgent` via `initialize_sync()` (no extra LLM calls)
- Builds system prompt from the **4 cognitive blocks** (Rules / Identity / Goals / Memory)
- Runs the tool-use loop via `llm_tools.call_tool_llm` (Gemini or Anthropic)
- Reuses the existing domain tools (`get_my_identity`, `get_my_forces`, etc.) and memory tools (`list_my_memories`, `read_memory`, `write_memory`)
- Persists commits + memory via `agents/tools.py` → `agent_decisions` / `agent_memories` tables

### Block 1 context jump

| Before (stage5_test) | After (leader_round) |
|---|---|
| ~500 chars system prompt | **~10K chars** Block 1 from `agents/world_context.build_rich_block1()` |
| Just `character_name + title` | Full SIM world context: roster, structure, geography, situation |

Richer identity, goals, and SIM-world awareness — foundation for the vision's "autonomous AI participants".

### Wiring

- **`full_round_runner._run_leader_sync`** replaces `_run_stage5_sync` — thin thread bridge
- Resolves `country_code → role_id` via `profiles.load_heads_of_state()` CSV lookup
- No changes to the parallel semaphore or observability event emission

### End-to-end smoke test (Beacon / Ruthenia, round 99)
- Gemini Flash, 11 tool calls, 1 read + 3 memory writes
- Committed `diplomatic_move` (public statement) — validation passed
- 25s total duration
- Cognitive blocks snapshot: block1_rules 10K chars, block2_identity 148, block4_goals 375

### Known minor issues (non-blocker)
- `get_relationships` tool throws `'str' object has no attribute 'get'` on certain war-state shapes — agent continues, deferred fix

### Files

| File | Change |
|---|---|
| `app/engine/agents/leader_round.py` | NEW — canonical single-agent round runner |
| `app/engine/agents/full_round_runner.py` | swapped `run_stage5_test` → `run_leader_round` |
| `app/engine/agents/stage5_test.py` | kept for now (delete in Phase 4) |

### Next (Phase 3)
- Merge decision-processing into `engines/orchestrator.run_round()`
- Wire new unit-level combat functions (`resolve_ground_attack_units` etc.) into the orchestrator
- Add economic + political tick per round (currently static)
- Phase 4: delete `round_engine/`, `stage*_test.py`

---

## 🎯 NUCLEAR MODEL — UNIFIED (2026-04-06)

Final simplified nuclear mechanics after Marat clarified confusion between warhead types and country capability tiers.

### Clean terminology

| Concept | Type | Values |
|---|---|---|
| **Warhead** (per missile) | `WarheadType` enum | `conventional`, `nuclear` |
| **Country nuclear capability** | `countries.nuclear_level` int | 0 – 4 |
| **Attack type** (per launch) | `StrategicAttackTier` enum | `t1_midrange`, `t2_strategic_single`, `t3_strategic_salvo` |

### Capability tiers unlock attack types

| Tier | Can launch | Range | Missiles per strike | Interception |
|---|---|---|---|---|
| T0 | — | — | — | — |
| **T1** | midrange | ≤3 hex | 1 | Standard AD-halving (30% if AD present, else 80%) |
| **T2** | strategic single | global | 1 | T3+ nations only (see below) |
| **T3** | strategic salvo | global | **3+** (up to all available) | T3+ nations only |
| T4 | reserved / max | | | |

### Nuclear damage (per hit — uniform, warhead-only distinction)

- **50% of all military units** on target hex destroyed (including launcher's own if present)
- **30% × (1 / target_country_hex_count)** of target country's GDP destroyed
- Single hex only — no neighbour effect

### T3 salvo aggregate (applied once per salvo, if ≥1 nuclear hit lands)
- Global stability **-1.5**
- Target country stability **-2.5**
- **1/6 leader death roll** (target nation only)

### T3+ interception (for T2 + T3 strategic attacks only)

1. Launcher fires (authorization chain enforced at decision layer, not combat engine)
2. Global alert: all see "launch detected"; **only T3+ nations see launcher + target**
3. **Auto-fire interception** by every T3+ nation except launcher
4. Each T3+ nation rolls **1 d(25%) per active AD unit** they own
5. Each success destroys one missile from the salvo
6. **Opaque** — launcher does not learn who intercepted
7. **AD-in-target-zone does NOT halve nuclear missile hit probability** (T3 mechanic replaces it for strategic attacks)
8. **T1 midrange keeps standard AD halving** (T3 mechanic doesn't apply to short-range)

### Files

| File | Change |
|---|---|
| `app/engine/engines/military.py` | `WarheadType` simplified to binary. New `StrategicAttackTier` enum. New `UnitMissileStrikeInput.attack_tier`. New `resolve_nuclear_salvo_interception()` + `InterceptorReport`. New `resolve_nuclear_salvo_aggregate()`. Old L1/L2 damage code replaced by uniform nuclear damage. Old `resolve_nuclear_interception` single-nation stub removed. |

### Documentation propagation

- [ ] CON_C2 §1.4 — update warhead definition (binary) + tier attack types
- [ ] Remove any L1/L2 warhead prose; replace with "nuclear" binary
- [ ] Document capability tiers (T0-T4) clearly in SEED_C
- [ ] Clarify that AD serves DUAL purpose: (a) halving conv/T1 strikes at target zone, (b) interception rolls for T2/T3 strategic strikes when owner has T3+ capability

---

## 🎯 BALLISTIC MISSILE v2 + BLOCKADE DISPLAY-ON-DECLARED (2026-04-06)

### Ballistic missile strike — final calibration

| scenario | old (v1) | new (v2) |
|---|---|---|
| Unprotected | 20% | **80%** |
| AD covering zone | 10% | **30%** |

Rationale (Marat): missiles are very accurate; AD helps significantly but doesn't halve them. Air-strike halving rule doesn't apply.

**Disposable:** ballistic missiles are CONSUMED on firing. The missile unit itself is marked `destroyed` immediately after firing (before or after hit, regardless). This is enforced in `_resolve_attack` via a second `_apply_losses` call after each missile strike.

**File:** `app/engine/round_engine/combat.py` `resolve_missile_strike`; `app/engine/round_engine/resolve_round.py` `_resolve_attack` (strategic_missile branch).

### Air attack unit types — confirmation (no change)

Only two unit types can conduct air/ranged attacks against ground targets:
- `tactical_air` (recoverable, 12% / 6% probabilities, range ≤ 2 hexes)
- `strategic_missile` (disposable, 80% / 30% probabilities, global range)

No other types launch ranged strikes. Confirmed 2026-04-06.

### Blockade visualization — only from DECLARED actions

Previous (2026-04-05): derived from naval positions → false positives on half the map.
Now (2026-04-06): observatory reads committed `declare_blockade` actions from `agent_decisions` via new `GET /api/observatory/blockades` endpoint. Each action carries `payload.target_hexes` + `payload.level` (partial|full).

**Until `declare_blockade` is wired into the agent action catalog, the endpoint returns empty → no blockade contours drawn.** This eliminates the false positives while keeping the infrastructure ready.

**Files:**
- `app/test-interface/server.py` — new `_observatory_blockades()` method + `/api/observatory/blockades` route
- `app/test-interface/static/observatory.js` — `renderBlockadeZones()` now reads `state.blockades` populated by `applyBlockades()` from the new endpoint; derivation code removed

### Documentation propagation

- [ ] CON_C2 §1.4 Strategic missile — update **80% unprotected / 30% w/AD, DISPOSABLE**
- [ ] DET_COMBAT_MECHANICS.md — ballistic missile scarcity rules
- [ ] Action catalog — formally add `declare_blockade` action with payload schema `{target_hexes: [[r,c]], level: "partial"|"full"}`

---

## 🎯 STRIKE CALIBRATION v2 + AIR RANGE + SEA-HEX GUARD (2026-04-06)

Four changes this session, all from Marat's calibration feedback.

### 1. Air strike probability — reset to low, simple halving rule

Replaces the earlier absorption-counter model. Simpler and lower base.

| scenario | old (2026-04-05 v1) | new (2026-04-06 v2) |
|---|---|---|
| Unprotected (no AD) | 40% | **12%** |
| AD covering zone | 0% if capacity, else 40% | **6%** (halved) |
| +1 air-superiority unit | +10% | +2% |
| +2 air-superiority units (cap) | +20% | +4% |
| Clamp | [10%, 80%] | **[3%, 20%]** |

**Rule:** AD is now a simple coverage flag, not an absorbing buffer. `ad_strikes_absorbed` counter removed from the air-strike path.

### 2. Missile strike probability — same halving model

| scenario | new |
|---|---|
| Unprotected | **20%** (missiles scarce + more destructive) |
| AD covering zone | **10%** (halved) |

### 3. Air strike range — adjacent + 1 hex beyond

**New rule:** tactical_air can strike hexes within **hex distance ≤ 2** of the launching unit (covers ~19 hexes including center). Works on both global and theater coordinates. Out-of-range strikes emit `attack_out_of_range` event.

Implementation: `_hex_distance()` helper added using cube-coord conversion on odd-r offset grid. Range check enforced in `_resolve_attack()` before calling `resolve_air_strike`.

### 4. Sea-hex placement guard — non-naval units forbidden on sea

**Rule:** non-naval non-embarked units cannot be placed on sea hexes. Enforced in `movement.resolve_movement()`.

**Data fix:** 5 ground units were found on sea hexes in `unit_states_per_round`:
- `yam_g_01`, `yam_g_02` at (5,18) — sea
- `yam_g_03` at (6,18) — sea
- `fre_g_04`, `fre_g_r1` at (3,9) — sea

All were `reserve` in the canonical `layout_units` (coords NULL) but wrongly deployed to sea in rounds 1–6 by an earlier seeding bug. **Fixed in DB:** reset to `reserve` with NULL coords across all rounds.

### Files

| File | Change |
|---|---|
| `app/engine/round_engine/combat.py` | `resolve_air_strike` — new 12%/6% halving model. `resolve_missile_strike` — new 20%/10% halving model. |
| `app/engine/round_engine/resolve_round.py` | Added `_hex_distance()` + AIR_STRIKE_MAX_RANGE=2 enforcement. |
| `app/engine/round_engine/movement.py` | Added `is_sea_hex()` + `_load_sea_hexes()` helpers; `resolve_movement` rejects non-naval placement on sea. |

### Documentation propagation

- [ ] CON_C2 §1.3 Tactical air strike — update p=12% base, 6% w/AD, range=2
- [ ] CON_C2 §1.4 Strategic missile — update p=20% base, 10% w/AD
- [ ] CON_C2 §3 Units — add explicit "non-naval never on sea" rule
- [ ] DET_COMBAT_MECHANICS.md — full probability tables + range tables

---

## 🎨 OBSERVATORY VISUAL — Blockade zones constrained (2026-04-06 refinement)

Blockade visualization restricted to: **chokepoints + sea hexes adjacent to island nations** (today: Formosa only). Earlier derivation marked any sea hex with enemy naval adjacent to any foreign coast → too many false positives. File: `observatory.js` `renderBlockadeZones` now filters through a `blockadeable` set.

---

## 🎨 OBSERVATORY VISUAL — Blockade zones on map (2026-04-05)

**Rule (Marat):** When naval blockade is in effect, mark sea hexes with orange contour.
- Partial blockade → orange, thicker boundary
- Full blockade → more intense orange, bolder boundary + glow

**Derivation (since `declare_blockade` action isn't yet wired):** computed client-side from current naval positions:
- Sea hex S is "blockading country X" if S is adjacent to any X-owned land hex AND S contains at least one non-X active naval unit.
- Country X is "fully blockaded" if ALL its coastal sea hexes are blockading hexes; otherwise partial.
- A blockading sea hex gets the max intensity across all countries it blocks.

**Files:** `app/test-interface/static/observatory.js` (new `renderBlockadeZones`), `app/test-interface/static/observatory.css` (`.hex.blockade-partial`, `.hex.blockade-full`).

**Applies:** global view only (theater-view ownership mapping is simplified).

---

## 🎯 COMBAT CALIBRATION — Ground Combat & Occupation (2026-04-05)

**Rules locked in by Marat** (2026-04-05 after Q&A):

### Attack mechanics (RISK-style with TTT modifications)

| Rule | Decision |
|---|---|
| **Source hex** | Attacker selects ANY number of own ground units from one source hex |
| **Source = own territory** | No minimum — can empty the source hex |
| **Source = foreign hex already captured this round** | Must leave ≥1 ground unit behind |
| **Target** | Adjacent hex (6-neighbour pointy-top odd-r offset) |
| **Defenders in combat** | Ground units ON target hex + **naval units on any adjacent sea hex** |
| **Naval defensive strength** | Equal to ground (1 die per unit, same dice cap) |
| **Dice** | Attacker min(3, N), defender min(2, N). Ties → defender |
| **Combat resolution** | **Iterative** — exchanges continue until one side has 0 units |
| **Non-ground non-naval on target hex** | `tactical_air`, `air_defense`, `strategic_missile` → **captured as trophies** if attacker wins |
| **Trophy handling** | Flip ownership to attacker, status=`reserve`, coords cleared, type preserved. Re-deployable next round as standard reserves. |
| **Unopposed occupation** | If target has no ground and no adjacent-naval defenders → occupy + capture trophies, no dice rolled |
| **Post-victory movement** | All surviving attackers move onto captured hex (Phase 1 — simplified) |
| **Naval on adjacent sea that defended** | If naval survives combat → remains on its sea hex, unchanged |
| **Naval on adjacent sea CANNOT be captured** (it's on sea, not on land hex) |
| **Chaining (multi-hex conquest in one round)** | **NOT a schema feature** — each attack = separate `declare_attack` decision |
| **Intra-round movement** | **NONE** — only attack-moves. Other repositioning happens between rounds |

### Files changed

| File | Change |
|---|---|
| `app/engine/round_engine/combat.py` | `resolve_ground_combat()` rewritten as **iterative** loop (was one-shot). Returns total losses + `.success` flag. |
| `app/engine/round_engine/resolve_round.py` | New ground-combat path: separates true ground defenders from naval-adjacent + trophies. Unopposed-occupation branch. Post-victory `_move_attackers_forward` + `_capture_trophies`. |
| `app/engine/round_engine/resolve_round.py` | New helpers: `_hex_neighbors()` (1-indexed odd-r offset, matches frontend `map.js`), `_adjacent_naval_defenders()`, `_capture_trophies()`, `_move_attackers_forward()`. |

### Defunct assumptions removed

- Previous `_resolve_attack` treated `air_defense + strategic_missile` as "ground defenders that fight back" — wrong. Those are now trophies (if no ground there) or simply don't participate in ground melee.
- Previous one-shot dice roll replaced with iterative exchanges.

### Documentation propagation required

- [ ] `CON_C2_ACTION_SYSTEM_v2.frozen.md` §1.1 Ground attack — add iterative-dice rule + naval-adjacent-defends-land rule + trophy-capture rule
- [ ] `SEED_C_MAP_UNITS_MASTER_v1.md` — add attack/occupation mechanics section
- [ ] `DET_COMBAT_MECHANICS.md` (to be created) — full probability tables for ground + strikes + naval
- [ ] Update action-catalog docs so `declare_attack` is documented as one-target-per-decision

---

## 🎯 COMBAT CALIBRATION — Air Strikes + AD Zone of Coverage (2026-04-05)

**Flagged by Marat during Observatory testing:** "air strikes seem extremely effective — they are meant to be much less effective, especially if the area is protected by air defense. AND — air defence placed on a global map area protects the entire global map area (which means it protects all the local map connected areas)."

### Change 1 — Air strike base effectiveness reduced

| | Before | After |
|---|---|---|
| Base hit probability | 0.60 | **0.40** |
| AD modifier | −0.15 per AD, clamped 5–95% | **AD absorbs first (canonical), then roll** |
| Air-superiority bonus | +0.10 per unit (uncapped) | +0.10 per unit, **cap +0.20** |
| Clamp | [0.05, 0.95] | [0.10, 0.80] |

**File:** `app/engine/round_engine/combat.py` — `resolve_air_strike()`

### Change 2 — AD absorption model now matches CON_C2 canonical rule

Canonical rule (CON_C2_ACTION_SYSTEM_v2.frozen.md §1.4):
> "Air defense in target zone absorbs up to 3 (configurable) incoming strikes per air defense unit before remaining strikes resolve."

**Before:** AD was a probability-reducer (−15% per AD, max impact ~45% absolute). A 4-AD defence still allowed 5% strike probability.
**After:** AD *absorbs* strikes one-for-one until depleted (3 per AD unit). Only after ALL AD in zone is depleted do any remaining strikes roll against base probability.

Applied symmetrically to `resolve_missile_strike()`:
- Before: 0.50 base, −0.20 if any AD present.
- After: AD absorbs first, then 0.55 base post-depletion.

### Change 3 — AD coverage is ZONE-WIDE (not hex-local)

**Before (bug):** `defender_ad = [u for u in defender_units if u.get("unit_type") == "air_defense"]` — AD only counted if stationed ON THE EXACT TARGET HEX.

**After:** AD coverage zone = the global hex PLUS every theater hex linked to it. An AD unit covers the zone if it is:
- On the zone's global hex, OR
- On any theater hex that maps back to the zone's global hex via the canonical theater↔global linkage table, OR
- On a theater hex in the same linked theater (safety-net fallback for edge cases).

**File:** `app/engine/round_engine/resolve_round.py` — new `_ad_units_in_zone()` helper; `_resolve_attack()` now calls it instead of inline filter.

### Impact on existing unit placements

Template v1.0 has AD units placed at global hexes that are also theater-link hexes (e.g. Sarmatia AD at (3,12), (4,12); Ruthenia AD at (4,11); Persia/Mirage/Solaria AD on Mashriq-link hexes). Under the new zone rule these AD units now protect:
- Their own global hex, AND
- The full theater area they link to (all Eastern Ereb hexes for Sarmatia/Ruthenia AD; all Mashriq hexes for Persia AD; etc.)

No unit moves required — only the coverage logic changed.

### Observatory UI — battle-marker animation fix

Two bugs fixed simultaneously (flagged by Marat same session):
- **Blast pulse appeared to move across map** — caused by `transform: scale()` without `transform-origin`; SVG text scaled from origin (0,0). Fixed by adding `transform-box: fill-box; transform-origin: center;` to `.battle-marker`.
- **Animation too aggressive** — pulse was 1.0→1.25 over 1.4s. Reduced to **1.0→1.12 over 1.8s** ("small expansion" per Marat).
- **Blast marker now renders in theater view too** (previously global-only) — locates blast at any affected unit whose `theater` matches the active theater view.

**Files:** `app/test-interface/static/observatory.css`, `app/test-interface/static/observatory.js`

### Documentation propagation required (to be done before concluding this exercise)

- [ ] `CON_C2_ACTION_SYSTEM_v2.frozen.md` §1.4 — clarify "zone" explicitly means global hex + linked theater
- [ ] `SEED_C_MAP_UNITS_MASTER_v1.md` — add AD coverage-zone rule to combat section
- [ ] New DET doc or addendum: `DET_COMBAT_MECHANICS.md` with canonical probability tables

---

## 🚩 MANDATORY CLEANUP — Unit Notes Field (flagged 2026-04-05)

**Issue:** `layout_units.notes` (and source `units.csv` notes column) contains real-world names that MUST NOT leak into the fictional SIM world:
- "Russian artillery", "US Marines", "Kremlin garrison", etc. — real-world country names forbidden per SIM naming discipline
- Unit sub-type names like "artillery", "armored brigade", "Patriot battery" — create imaginary mechanics that don't exist in the 5-unit-type model (ground/tactical_air/strategic_missile/air_defense/naval). Participants will ask "how does artillery differ from infantry" — pointless cognitive load.

**Mandatory fix:** ONE OF:
- **Option A (clean):** DELETE the notes column entirely. Every unit is just its `unit_code` + type + status. No prose hints.
- **Option B (simplified):** REPLACE all notes with simple locational labels only, using SIM names: "Nord-W border forward", "Central reserve", "Mashriq front" — no equipment, no real-world names, no unit-subtype language.

**Marat recommends Option A-or-B — decision pending.**

**Scope of fix:**
- `units.csv` source file
- `layout_units` DB rows for all layouts (template_v1_0_default, start_one)
- Future commits via `commit_action` should NOT auto-inject unit subtypes into notes
- Any AI agent tool descriptions that reference unit sub-types should be audited

**Priority:** BEFORE any human-participant play. Agents don't care, humans will.

---

## 🏛️ SCENARIO TAXONOMY LOCKED — 2026-04-05

**Approved by Marat via 12 locked decisions in planning session. Closes Critical Gap 1 from inventory.**

### The 12 Decisions

| # | Question | Decision |
|---|---|---|
| Q1 | Per-country starting stats | Free override; default to template |
| Q2 | Relationship matrix | Free override; default to template |
| Q3 | Formula coefficients | **TEMPLATE-LOCKED** (preserves calibration) |
| Q4 | Starting military deployments | Free override; default to template placement |
| Q5 | Role briefings | Free override; default to template |
| Q6 | Oil price starting value | Scenario sets within template range |
| Q7 | Pre-scripted events | YES — election dates, SIM starting date, mandatory events all scenario-configurable |
| Q8 | Multiple templates in DB | Multiple coexist |
| Q9 | Max rounds | Template allows range, scenario picks |
| Q10 | Role personality variation | Free override; default to template |
| Q-A | Hard-coding policy | Agreed — actions, event types, engines, cognitive arch, round phases are code |
| Q-B | Template versioning | Semver + names |

### Core Principle

**A SCENARIO is a "modified copy of TEMPLATE" with sparse overrides.**

Every scenario field defaults to its template value. Scenario stores only modifications. Falls back to template at runtime.

### Artifacts produced this session

- NEW: `3 DETAILED DESIGN/DET_F_SCENARIO_CONFIG_SCHEMA.md` — canonical spec (closes Critical Gap 1)
- NEW: `3 DETAILED DESIGN/DET_B1a_TEMPLATE_TAXONOMY.sql` — DB schema additions
- NEW: `CONCEPT TEST/template_v1_0_seed.sql` — Template v1.0 seed
- NEW: `CONCEPT TEST/scenario_start_one_seed.sql` — first scenario seed
- UPDATED: `SEED_C_MAP_UNITS_MASTER_v1.md` §5 — expanded canonical 3-level model
- UPDATED: `CHANGES_LOG.md` — this section

### Unblocks

- AI participant testing harness (can now query Template v1.0 from DB)
- Future scenarios (facilitators have formal customization contract)
- DB migration to Supabase (schema is now specified)

---

## 🔒 TEMPLATE v1.0 FORCE STRUCTURE LOCKED — 2026-04-05

**Approved by Marat 2026-04-05. `start_one.csv` is the canonical Template v1.0 default unit placement AND force structure.**

### Authority chain

```
start_one.csv (moderator hand-reviewed) = CANONICAL
        ↓ (snapshot at lock-time)
units.csv (engine default, identical content)
        ↓ (aggregated totals)
countries.csv mil_* columns (derived summary)
```

Any divergence between these three must be resolved in favor of `start_one.csv`. `countries.csv` mil_* totals are a *derived cache* of the canonical force pool, not an independent truth.

### Force-structure adjustments applied 2026-04-05 (14 changes)

Hand-reviewed by Marat via the placement editor, representing doctrinal reality:

| Country | Type | Before | After | Design rationale |
|---|---|---|---|---|
| ruthenia | ground | 10 | 11 | +1 reflects actual frontline strength |
| persia | strategic_missile | 1 | 0 | Persia lacks true strategic doctrine |
| teutonia | strategic_missile | 1 | 0 | Germany has no strategic missile force |
| albion | air_defense | 1 | 2 | +1 for homeland BMD coverage |
| bharata | strategic_missile | 2 | 0 | Separates Indian tactical from strategic |
| levantia | strategic_missile | 2 | 3 | +1 reflects Israeli doctrine reality |
| yamato | strategic_missile | 2 | 0 | Japan is non-nuclear, no strategic force |
| solaria | air_defense | 2 | 1 | Consolidated coverage |
| choson | tactical_air | 2 | 1 | Shift toward strategic capability |
| choson | strategic_missile | 1 | 2 | North Korean doctrine priority |
| hanguk | naval | 2 | 1 | Trimmed to reflect ROK deployable fleet |
| hanguk | strategic_missile | 1 | 0 | South Korea relies on US umbrella |
| caribe | tactical_air | 1 | 0 | Post-collapse reality (Maduro captured) |
| mirage | air_defense | 2 | 1 | Consolidated UAE BMD coverage |

**Net effect:** 353 → 345 units total (−8). Force pool now matches moderator-reviewed canonical placement.

### Files synced

- `units.csv`: replaced with `start_one.csv` snapshot (345 rows)
- `countries.csv`: 14 `mil_*` cells updated to match aggregated start_one totals
- Backups: `units.csv.bak_pre_template_v1`, `countries.csv.bak_pre_template_v1`

### Reconciliation verified

Post-sync validator output: **345/345 pass, 0 hard errors, 0 warnings, 0 count mismatches, 0 self-occupation.**

---

## 🏛️ CANONICAL ARCHITECTURE — MAP + UNITS (must be reflected in SEED)

**Approved by Marat 2026-04-05. This is the main logic of the ultimate system.**

### Hierarchy

```
SIM TEMPLATE (master)
  ├── MAP SYSTEM — canonical global map + theater maps + linkage rules
  │     (global ↔ theater connectedness is PART OF the template)
  └── DEFAULT UNIT PLACEMENT — canonical starting positions on the map
        (also PART OF the template, represents "default scenario")

SIM SCENARIO (derived from a TEMPLATE)
  └── Moderator adjustments to DEFAULT unit placement
        (theater positions, reserves, force structure)
        (scenario CANNOT modify the MAP — map changes require a NEW TEMPLATE)

SIM RUN (instance of a SCENARIO)
  └── Immutable once started
```

### Implications

1. **MAP system is template-level.** Changing the global map, theater maps, or the theater↔global linkage requires creating a new SIM TEMPLATE (not just a new scenario).
2. **Default unit placement is template-level.** Every template carries ONE default starting layout.
3. **Scenario-level unit placement** is moderator-adjustable, stored as a delta or full layout on top of template default.
4. **A saved layout file** (like `start_one.csv`) represents a candidate **default template unit placement** OR a **scenario variant**.
5. **When loading a saved layout, its stored coordinates must be respected** — they were derived from the map state at the time of saving. If the map/linkage changes later, that constitutes a template change, and layouts from old templates stay pinned to their original coords.
6. **`units.csv` (the default)** represents the canonical Template v1.0 default placement.
7. **`units_layouts/*.csv`** represents candidate template defaults or scenario variants.

### Source of truth for each field

| Field | Source of truth |
|---|---|
| Theater cell coords (`theater`, `theater_row`, `theater_col`) | Authoritative position for theater-placed units |
| Global coords (`global_row`, `global_col`) | For theater units: derived from theater cell via template's canonical mapping |
| For global-only units (no theater) | Authoritative global position |

### Migration rule

When the canonical theater→global mapping changes:
- The template is considered to have moved to a new version
- Old layouts loaded under the new version should be **explicitly re-saved** by the moderator if they want the new mapping applied
- Otherwise loaded layouts render with their saved coords

---

## 🚩 PENDING SEED UPDATES (must apply before finalizing scenario)

These are corrections identified during the map harness work. They must be propagated into the canonical SEED files before the scenario is locked.

**✅ RESOLVED 2026-04-05 — Critical Gap 1: Scenario configuration data model.** Closed by the SCENARIO TAXONOMY LOCKED session (12 decisions) and the new `DET_F_SCENARIO_CONFIG_SCHEMA.md` + `DET_B1a_TEMPLATE_TAXONOMY.sql` artifacts. See top of this log.

### 1. CANONICAL theater → global linkage mapping (Marat-approved 2026-04-05)

This is the authoritative mapping. Any SEED documentation (structure docs, theater JSONs with `global_link` fields, aggregation code) must conform to this table.

**Eastern Ereb theater → global hex (FINAL v2 2026-04-05):**

| Theater cell condition | Global hex |
|---|---|
| Rows 1-4, owner=sarmatia | (3,12) |
| Rows 5+, owner=sarmatia | (4,12) |
| owner=ruthenia (any row, free or occupied) | (4,11) |
| Any sea cells | (5,12) |

**Mashriq theater → global hex:**

| Theater cell condition | Global hex |
|---|---|
| owner=phrygia | (6,11) |
| owner=solaria | (7,11) |
| owner=mirage | (8,11) |
| owner=persia, rows 1-3 | (6,12) |
| owner=persia, rows 4-6 | (7,13) |
| owner=persia, rows 7-10 | (8,13) |
| owner=sea, rows 3-6 | (7,12) |
| owner=sea, rows 7-10 | (8,12) |

**SEED files affected:**
- `SEED_C1_MAP_STRUCTURE_v4.md` — theater→global linkage table must match above
- `SEED_C3_THEATER_EASTERN_EREB_STATE_v3.json` — `global_link` fields per hex must match
- `SEED_C3_THEATER_MASHRIQ_STATE_v1.json` — add missing `global_link` fields per hex matching table
- `SEED_C3_THEATER_EASTERN_EREB_STRUCTURE_v3.md` — linkage doc
- `SEED_C3_THEATER_MASHRIQ_STRUCTURE_v1.md` — linkage doc

**Editor status:** `map.js::globalHexForTheaterCell()` now implements this canonical mapping. `units.csv` global_row/global_col re-synced to match (22 units updated).

### 2. BUG: Self-occupation in Eastern Ereb theater JSON — FIXED 2026-04-05

**File:** `SEED_C3_THEATER_EASTERN_EREB_STATE_v3.json`
**Bug:** Cell at theater (row=5, col=8) had `owner=sarmatia, occupied_by=sarmatia` — a country cannot occupy its own territory.
**Applied fix:** Set `occupied_by=None` at (5,8). Full scan confirmed this was the only self-occupation cell. Backup saved at `SEED_C3_THEATER_EASTERN_EREB_STATE_v3.json.bak_pre_fix`.
**Remaining:** Scan Mashriq JSON for same pattern when it's next reviewed.

### 2b. start_one.csv global coord re-sync — APPLIED 2026-04-05

**File:** `2 SEED/C_MECHANICS/C4_DATA/units_layouts/start_one.csv`
**Action:** Re-derived `global_row`/`global_col` for 28 theater-placed units to match the canonical Marat-approved mapping. Theater coordinates (`theater`, `theater_row`, `theater_col`) and all other fields were NOT modified. 50 units were already correct. 268 non-theater units untouched.
**Backup:** `start_one.csv.bak_pre_remap`
**Status:** start_one.csv is now near-canonical for Template v1.0 default unit placement, pending any further moderator adjustments.

### 3. Sarmatian ground units currently sitting on sea cells

**File:** `units.csv` post-migration
**Issue:** `sar_g_05`, `sar_g_06`, `sar_d_02`, `sar_m_10` are at theater cells with `owner=sea` (rows 8 cols 6,7). Sarmatian GROUND units on sea hexes is invalid.

**Fix required:** Re-place these units on valid Sarmatian land theater cells. Can be done via the editor interactively.

---

## 2026-04-04 — Map Viewer Harness

### Created
- `app/test-interface/templates/map.html` — full-page SVG hex map viewer
- `app/test-interface/static/map.js` — vanilla JS renderer, click handlers, theater drill-down
- `app/test-interface/static/map.css` — dark theme styles per UX style guide

### Modified
- `app/test-interface/server.py` — added `/map` route and 5 data endpoints (`/api/map/global`, `/api/map/theater/{eastern_ereb,mashriq}`, `/api/map/deployments`, `/api/map/countries`)
- `app/test-interface/templates/index.html` — added "🗺 Open Map Viewer" button

### Design decisions
- SVG (not Canvas) for native click handlers and scalability
- Vanilla JS (no framework) to match existing test-interface style
- Pointy-top hexes with odd-row offset
- Country colors from `SEED_H1_UX_STYLE_v2.md` Map Muted palette
- Unit icons inlined from `UNIT_ICONS_CONFIRMED.svg`

---

## 2026-04-04 — Coordinate Convention Locked

### Canonical convention
**`(row, col)` — row first, col second. Both 1-indexed.**
- Row = vertical position from top (1 = top row, 10 = bottom row)
- Col = horizontal position from left (1 = leftmost, 20 = rightmost global)

### Issues fixed in `map.js`
1. Chokepoint rendering: removed incorrect `-1` offset (JSON stores 0-indexed, code double-decremented)
2. Chokepoint inspector lookup: fixed coord comparison to match array index
3. Mashriq theater linkage keys: flipped from legacy `(col,row)` to canonical `(row,col)`
4. Eastern Ereb `global_link` strings: flipped from `(col,row)` to `(row,col)` on read
5. `w(col,row)` naval coord parser: flipped output to canonical `(row,col)`
6. `MASHRIQ_ZONE_LINKS` values: all flipped to canonical
7. `persiaZoneToGlobal()` return values: flipped to canonical
8. `ruthenia` fallback: `11,4` → `4,11` canonical

### Noted in code
Theater JSON `global_link` fields still store legacy `(col,row)` format — viewer flips on read. Data files unchanged (frozen SEED).

---

## 2026-04-04 — Map Visual Refinements

- Chokepoints (Formosa Strait, Gulf Gate, Caribe Passage) — positions fixed via coord convention fix
- Die Hard marker (Eastern Ereb): position shifted +1 row, +1 col from JSON value to match actual theater layout
- Added global hex `(8,12)` "Gulf Gate" as Mashriq theater-link (clicking opens Mashriq)
- Country name labels added at geometric centroid of each country's territory
- Country labels styled classic cartographic: italic, light weight, wide letter-spacing, muted fill
- Unit icon dispersion: reduced overlap (40%→55%), added deterministic x/y jitter per icon for natural spread

---

## 2026-04-04 — Units Data Migration

### Schema change
Migrated from aggregate `deployments.csv` (count-per-zone) to individual `units.csv` (one row per unit).

### New file
- `2 SEED/C_MECHANICS/C4_DATA/units.csv` — 342 individual unit rows

### Schema
| Column | Purpose |
|---|---|
| `unit_id` | Unique label (e.g. `col_g_01`, `per_d_01`, `sar_g_r1`) |
| `country_id` | Owner |
| `unit_type` | ground / tactical_air / strategic_missile / air_defense / naval |
| `zone_id` | Current hex location (empty if reserve/embarked) |
| `embarked_on` | Carrier/ship unit_id if embarked (empty otherwise) |
| `status` | active / reserve / embarked / damaged |
| `notes` | Human-readable description |

### Code updates
- `app/engine/agents/map_context.py`: added `load_units()`, `units_by_zone()`, `units_by_country()` functions; marked `load_deployments()` deprecated
- `app/test-interface/server.py`: `/api/map/deployments` now reads units.csv, returns same shape for backward compat; new `/api/map/units` endpoint for individual unit queries

### Q1 2026 Real-world research basis
Deployment positions informed by Q1 2026 open-source intelligence:
- Russia-Ukraine war: Pokrovsk fall (late Jan), Fortress Belt offensive (Mar 21)
- US-Iran war (Op Epic Fury, Feb 28): 3 CSGs in CENTCOM
- Israel multi-front ops (Lebanon 3 divisions, Gaza, Syria buffer)
- US Caribbean residual (post-Maduro capture Jan 3)
- Germany 45th Brigade operational in Lithuania (Feb)
- THAAD/Patriot layered across Gulf states

### Embarked units (6 total)
- 4 air: on US carrier, Chinese carrier, Charles de Gaulle, HMS Prince of Wales
- 2 ground: US Marines on ARG (Red Sea), Turkish naval infantry on TCG Anadolu

### Reserves (21 total)
Peace countries hold strategic reserves; at-war countries fully committed.

### Principle: universal coordinate system
Each unit has ONE coordinate: its `zone_id`. The zone_id namespace is universal — names like `col_main_1` (global hex), `ruthenia_2` (Eastern Ereb theater hex), `persia_17` (Mashriq theater hex), `w(13,9)` (water) all resolve unambiguously. Viewer aggregates theater units to their parent global hex for global-view display.

---

## Pending / To Do

- Re-disperse ground units realistically across home territories (currently too concentrated)
- Apply frontline principle: along active war zones, most hexes should carry ground+air presence
- Die Hard zone: concentrate strong ground+air protection
- Air defense strategic placement (AD covers full global hex where placed)
- Columbia AD: increase from 4→6 (allows 1-2 overseas bases at mainland cost)
- Peace countries: increase reserves share
- Enforce: NO Sarmatian troops on non-occupied Ruthenian territory
- Enforce: NO Columbia troops on Persian soil (ships + allied bases only)
- Strategic missiles: place centrally in owner's territory
- Occupied territory: visual distinction (color change) when captured
- Embarked units: visual indicator on map for ground/air units on ships

---

## 2026-04-05 — units.csv Tactical Redispersion

Full rewrite of `2 SEED/C_MECHANICS/C4_DATA/units.csv` enforcing strict placement rules and tactical dispersion.

### What changed vs previous units.csv

1. **Columbia ground redistributed out of Persia.** Previously 2 ground units (`col_g_14`, `col_g_15`) were sitting on `persia_2` ("Op Epic Fury" theater). Both removed from Persian soil. Columbia ground now spans 8 CONUS hexes (col_nw, col_w, col_main_1×2, col_main_2, col_main_3, col_main_4, col_south) + Poland (freeland ×3) + Germany (teutonia_1 ×2) + Israel (levantia ×1, coordination element) + Korea (hanguk ×2) + Okinawa (yamato_2 ×1) + Formosa (×1) + Caribbean (caribe ×1) + Saudi (solaria_1 ×1) + UAE (mirage ×1) + Red Sea ARG (embarked ×1) = 22. **Zero Columbia units inside persia_*/t_persia_* zones.**
2. **Columbia air redistributed.** `col_a_08`, `col_a_09` previously on `persia_2` removed. New air footprint: 4 CONUS, 2 Europe (freeland, teutonia_1), 3 Middle East (solaria_1, mirage, levantia), 3 Indo-Pacific (yamato_2, hanguk, formosa), 1 embarked CVW, 2 ANG/AFRC reserves = 15.
3. **Columbia strategic missile.** `col_m_12` previously on `persia_2` removed; reallocated to solaria_1. ICBM silos now dispersed across col_main_1 (×2), col_main_2, col_main_3, col_main_4, col_nw, col_w, col_south (8 CONUS), plus forward deterrents in freeland, yamato_2 ×2, solaria_1 = 12.
4. **Columbia AD expanded 4→6** per countries.csv update: 3 CONUS (col_main_1, col_main_3, col_nw — GBI Ft Greely represents homeland BMD), 1 Freeland (Patriot Poland), 1 yamato_2 (PAC-3/THAAD Pacific), 1 solaria_1 (Patriot Gulf).
5. **Sarmatia ground strictly confined to Sarmatian home hexes + `ruthenia_2` (contested/occupied).** Previously `sar_g_14` (Kherson) was on `ruthenia_1` — that violated the rule and was corrected to `ruthenia_2`. All 10 Sarmatian frontline ground units now sit inside `ruthenia_2` (Pokrovsk/Donetsk, Luhansk/Lyman, Bakhmut, Zaporizhzhia east/west, Kherson lower-Dnipro, Crimea). Kursk/Belgorod/Voronezh (3) on nord_w1, Kaliningrad on nord_w2, Moscow garrison on nord_c1, Arctic on nord_n1, Far East on nord_e2, 1 VDV reserve = 18.
6. **Sarmatia AD `sar_d_02`** moved from `ruthenia_1` to `ruthenia_2` (Crimea/occupied zone, valid).
7. **Sarmatia air moved OFF Ruthenian soil entirely** — all 4 front-area strike aviation now on nord_w1 (Russia-side airbases as specified). 2 home defense nord_c1, 1 Kaliningrad nord_w2, 1 strategic aviation reserve = 8.
8. **Sarmatia missiles:** 6 strategic in Sarmatian interior (4× nord_c1 Moscow VO, 1× nord_c2, 1× nord_e2), 1 SSBN nord_n1, 3 Iskander forward in `ruthenia_2` (occupied zone — valid), 1 Kaliningrad, 1 reserve = 12.
9. **Die Hard hex hardened.** Ruthenia positions 3 ground units as Die Hard core (Fortress Belt Kramatorsk/Sloviansk/Kostiantynivka) + 3 fortress wing (Pokrovsk, Lyman, Chasiv Yar) + Kharkiv axis + Zaporizhzhia counter-offensive, all on `ruthenia_2`. Plus 1 Sumy border + 1 Dnipro strategic reserve on `ruthenia_1` = 10G. Air includes 1 CAS unit on ruthenia_2 (Die Hard close air support), 2 dispersal on ruthenia_1. AD on ruthenia_2 = Die Hard Patriot/NASAMS coverage.
10. **Persia dispersed across 7 theater hexes.** Previously stacked 2 on persia_1, 2 on persia_2, etc. Now 1 unit each on t_persia_4, 10, 17, 25, 30, 42, 50 + 1 reserve. Air dispersed across t_persia_8, 22, 28, 35, 45 + reserve. AD on t_persia_25 (nuclear sites central).
11. **Bharata reserves increased to 2** (12G includes 10 active + 2 strategic reserves, 20% reserve share per peace posture). Cathay reserves increased to 4G (strategic buffer at-peace posture).
12. **Naval repositioning.** Columbia naval spread across 7 water zones instead of 4: w(13,9) Gulf ×3, w(12,8) Red Sea ×2, w(18,5) WestPac ×2, w(4,2) Caribbean, w(6,1) Atlantic Norfolk, w(10,7) Med, 1 reserve = 11.
13. **Dispersion principle** applied to all home-zone countries: ground units spread across multiple home hexes rather than stacked (e.g. Cathay ETC split between cathay_6 ×4 and cathay_7 ×2; Bharata northern 4+1 internal; Freeland eastern 3 + central 1).

### Strict rule enforcement (verified by grep)

- `grep ",columbia,.*,(persia_1|persia_2|persia_3|t_persia_|cp_gulf_gate)"` → **0 matches**. Columbia has zero presence on Persian soil. Its near-Persia reach comes only through water zones (w(13,9) Arabian Sea/Gulf, w(12,8) Red Sea) and allied basing (solaria_1, mirage, levantia, yamato_2, hanguk, formosa, teutonia_1, freeland, albion).
- `grep ",sarmatia,.*,ruthenia_1,"` → **0 matches**. Sarmatia places troops only on Sarmatian home hexes (nord_* and sarmatia_*) and on `ruthenia_2` (the contested/occupied zone per Eastern Ereb theater JSON, where all `occupied_by: sarmatia` hexes global_link to "12,4" = ruthenia_2). No Sarmatian footprint on free Ruthenia.

### Occupied-by-Sarmatia hexes (Eastern Ereb theater)

The Eastern Ereb theater JSON (`SEED_C3_THEATER_EASTERN_EREB_STATE_v3.json`) marks ~10 tactical hexes with `owner: ruthenia, occupied_by: sarmatia`, all `global_link: "12,4"` which corresponds to the `ruthenia_2` global zone (East/contested). The free-Ruthenia tactical hexes (owner=ruthenia, no occupied_by field) all global_link to "11,4" which maps to `ruthenia_1` (West/home). Thus at the global-zone level: `ruthenia_2` is the only valid Ruthenian zone for Sarmatian placement. `ruthenia_1` is strictly free Ruthenia and off-limits to Sarmatian forces.

### Columbia AD 4→6 effect

The 2 additional AD units extend CONUS homeland coverage (previously 0 AD at home — all 4 were forward) and add strategic forward-area BMD. Result: 3 homeland + 3 forward (Europe/Pacific/Gulf). This balances deterrence presence abroad with basic interior missile defense, removing the previous gap where CONUS had no dedicated AD units at all.

### Total unit counts (validated)

columbia 22/15/12/6/11 | cathay 25/12/4/3/7 | sarmatia 18/8/12/3/2 | ruthenia 10/3/0/1/0 | persia 8/6/0/1/0 | gallia 6/4/2/1/1 | teutonia 6/3/0/1/0 | freeland 5/2/0/1/0 | ponte 4/2/0/0/0 | albion 4/3/2/1/2 | bharata 12/4/0/2/2 | levantia 6/4/0/3/0 | formosa 4/3/0/2/0 | phrygia 6/3/0/1/1 | yamato 3/3/0/2/2 | solaria 3/3/0/2/0 | choson 8/2/1/1/0 | hanguk 5/3/0/2/2 | caribe 3/1/0/0/0 | mirage 2/2/0/2/0.

All 20 countries × 5 unit types match specified table exactly. No discrepancies.

---

## 2026-04-05 — units.csv Migrated to Coordinate Schema (zone_id RETIRED)

### Schema change

**Before** (legacy zone_id):
```
unit_id, country_id, unit_type, zone_id, embarked_on, status, notes
```
Units were located via `zone_id` strings (`col_main_1`, `ruthenia_2`, `t_persia_17`, `w(13,9)`, …) that required multiple per-view lookup tables and per-country distribution rules to render on the global/theater hex grids.

**After** (pure coordinates):
```
unit_id, country_id, unit_type, global_row, global_col, theater, theater_row, theater_col, embarked_on, status, notes
```
Each active unit carries its own `(global_row, global_col)` on the global map, and — when sitting on a theater-link hex — also carries `theater` ∈ {eastern_ereb, mashriq} plus `(theater_row, theater_col)` on that theater's local grid. Reserves / embarked units have all coord fields empty.

### Why

- **Clean separation of concerns.** Units know where they are; the map renderer just reads coords.
- **Adjacency becomes trivial.** Neighbor-hex queries are pure hex-grid math — no zone_adjacency.csv lookup needed to place/move units.
- **No more zone-to-coord translation tables** in map.js (ZONE_TO_HEX, MASHRIQ_ZONE_LINKS, persiaZoneToGlobal, mashriqZoneToCell, easternErebZoneCells/…). All deleted.
- **Unambiguous placement.** Ten `ruthenia_2` units now each have an explicit theater cell instead of being round-robin-distributed at render time.

### Validation results

- 344 rows read / 344 rows written.
- Per-country-per-type totals preserved exactly (before == after).
- Status breakdown: 314 active, 24 reserve, 6 embarked.
- All reserve units: all coord fields empty + embarked_on empty ✓
- All embarked units: embarked_on points to a naval unit_id + coord fields empty ✓
- All active units: global_row AND global_col set, in-bounds ([1,10]×[1,20]) ✓
- When unit sits on a theater-link hex → theater + theater_row + theater_col all set (naval units exempted; sea-link hexes have no theater-grid cell) ✓
- When theater set → global coords match one of that theater's link hexes ✓
- Theater cells ∈ [1,10]×[1,10] ✓

### Files changed

- `2 SEED/C_MECHANICS/C4_DATA/units.csv` — rewritten with new schema.
- `2 SEED/C_MECHANICS/C4_DATA/units_legacy_zone_id.csv` — preserved backup of pre-migration CSV.
- `app/engine/agents/map_context.py` — `load_units()` reads new columns (ints); `units_by_zone()` removed; new `units_by_global_hex()` and `units_by_theater_cell(theater)` aggregators.
- `app/test-interface/server.py` — `/api/map/units` returns new schema; `/api/map/deployments` deprecated compat shim now returns `{rows, by_hex}` keyed by `"row,col"`; `/api/map/units/save` accepts new schema columns.
- `app/test-interface/static/map.js` — all zone lookup tables and helper functions deleted; `aggregateGlobalUnits()` and `aggregateTheaterUnits()` now read coords directly; edit mode rewritten to set/clear coord fields on pick-up, place, embark, and reset. Theater drill-down still uses `MASHRIQ_LINKS` badge list (retained for "theater-link" hex styling).

---

## 📋 TEMPLATE v1.0 RECONCILIATION CHECKLIST — 2026-04-05

Version tag for everything delivered this session: **Template v1.0 candidate**

### COMPLETED (applied to SEED/code/data)
- [x] Canonical TEMPLATE / SCENARIO / RUN architecture defined and approved (Marat 2026-04-05)
- [x] Canonical theater↔global linkage **v2** locked and documented (FINAL v2 table)
- [x] `map.js::globalHexForTheaterCell()` implements canonical mapping
- [x] `units.csv` global_row/global_col re-synced to canonical mapping (22 units updated)
- [x] `start_one.csv` global coord re-sync applied (28 units re-derived, 50 already correct, 268 non-theater untouched; backup `.bak_pre_remap`)
- [x] Coordinate convention locked: **(row, col)**, row first, 1-indexed
- [x] map.js coord-convention bugs fixed (8 distinct fixes: chokepoints, mashriq links, global_link strings, naval parser, persiaZoneToGlobal, ruthenia fallback, etc.)
- [x] Self-occupation bug fixed in Eastern Ereb JSON (cell 5,8 sarmatia/sarmatia → occupied_by=None); backup saved
- [x] Units schema migrated from `zone_id` → pure coordinates (`global_row/col` + optional `theater/theater_row/theater_col`)
- [x] `units_legacy_zone_id.csv` preserved as pre-migration backup
- [x] units.csv tactical redispersion complete (342 rows); strict placement rules enforced and grep-verified
- [x] Zero Columbia units on Persian soil verified
- [x] Zero Sarmatian units on free Ruthenia (ruthenia_1) verified
- [x] `map_context.py` updated: `load_units()` reads new schema; new aggregators `units_by_global_hex()`, `units_by_theater_cell()`; `units_by_zone()` removed
- [x] server.py endpoints migrated: `/api/map/units` (new schema), `/api/map/deployments` compat shim, `/api/map/units/save`
- [x] map.js zone lookup tables deleted (ZONE_TO_HEX, MASHRIQ_ZONE_LINKS, persiaZoneToGlobal, mashriqZoneToCell, easternErebZoneCells)
- [x] Validation results: 314 active / 24 reserve / 6 embarked; all invariants hold
- [x] Columbia AD expanded 4→6 per countries.csv update
- [x] Chokepoints (Formosa Strait, Gulf Gate, Caribe Passage) coord-fixed
- [x] Die Hard marker position fixed in Eastern Ereb
- [x] Gulf Gate (8,12) added as Mashriq theater-link
- [x] Country name labels added at geometric centroids on global map
- [x] Map viewer harness built: map.html, map.js, map.css; /map route and 5 data endpoints
- [x] Unit icon dispersion tuned (55% overlap, deterministic jitter)
- [x] DET unit model promoted (`DET_UNIT_MODEL_v1.md`) — this session
- [x] DB schema draft created (`CONCEPT TEST/db_schema_v1.sql`) — this session
- [x] Root CLAUDE.md updated with map+units canonical pointer — this session
- [x] engine/CLAUDE.md updated with map_config source-of-truth note — this session
- [x] **SCENARIO TAXONOMY locked (12 Marat-approved decisions 2026-04-05) — closes Critical Gap 1**
- [x] **DET_F_SCENARIO_CONFIG_SCHEMA.md created** (`3 DETAILED DESIGN/DET_F_SCENARIO_CONFIG_SCHEMA.md`) — canonical spec
- [x] **DET_B1a_TEMPLATE_TAXONOMY.sql created** (`3 DETAILED DESIGN/DET_B1a_TEMPLATE_TAXONOMY.sql`) — DB schema additions
- [x] **Template v1.0 seed SQL created** (`CONCEPT TEST/template_v1_0_seed.sql`)
- [x] **scenario_start_one seed SQL created** (`CONCEPT TEST/scenario_start_one_seed.sql`)
- [x] **SEED_C_MAP_UNITS_MASTER_v1.md §5 expanded** to full canonical 3-level model (Template/Scenario/Run with sparse-override principle)

### PENDING (to apply in next sync)
- [ ] Fix 4 Sarmatian ground units currently on sea cells (`sar_g_05`, `sar_g_06`, `sar_d_02`, `sar_m_10`) — re-place on valid Sarmatian land hexes
- [ ] Scan Mashriq JSON (`SEED_C3_THEATER_MASHRIQ_STATE_v1.json`) for self-occupation bugs (same pattern fixed in Eastern Ereb)
- [ ] Add missing `global_link` fields per-hex to `SEED_C3_THEATER_MASHRIQ_STATE_v1.json` matching canonical v2 table
- [ ] Re-sync `SEED_C3_THEATER_EASTERN_EREB_STATE_v3.json` `global_link` fields per-hex to canonical v2 table
- [ ] Update `SEED_C1_MAP_STRUCTURE_v4.md` theater→global linkage table to match v2
- [ ] Update `SEED_C3_THEATER_EASTERN_EREB_STRUCTURE_v3.md` linkage doc
- [ ] Update `SEED_C3_THEATER_MASHRIQ_STRUCTURE_v1.md` linkage doc
- [ ] Re-disperse ground units realistically across home territories (currently too concentrated in spots)
- [ ] Apply frontline principle: along active war zones, most hexes should carry ground+air presence
- [ ] Die Hard zone: verify strong ground+air protection concentration
- [ ] Peace countries: increase reserves share
- [ ] Strategic missiles: verify central placement in owner's territory
- [ ] Occupied territory: visual distinction (color change) when captured
- [ ] Embarked units: visual indicator on map for ground/air units on ships
- [ ] Generate full `theater_global_links` seed rows from theater JSONs (currently sketch-only in db_schema_v1.sql)
- [ ] Generate full `global_hexes` seed rows from `SEED_C1_MAP_GLOBAL_STATE_v4.json`
- [ ] Create Pydantic Unit model (`app/engine/models/unit.py`) per DET_UNIT_MODEL_v1
- [ ] Create TS Unit type (`app/frontend/src/types/unit.ts`) per DET_UNIT_MODEL_v1
- [ ] Create unit_validator service (`app/engine/services/unit_validator.py`) per DET_UNIT_MODEL_v1 §10
- [ ] Theater JSONs `global_link` format: either migrate data files from legacy `(col,row)` to canonical `(row,col)`, OR formalise the map.js flip-on-read (currently an untracked inconsistency)
- [ ] Promote `SEED_D_UNIT_DATA_MODEL_v1.md` companion SEED doc (referenced by DET, currently being authored by another agent)
- [ ] Promote `SEED_C_MAP_UNITS_MASTER_v1.md` master SEED doc (referenced by CLAUDE.md pointer, currently being authored by another agent)

### CROSS-REFERENCES

| Artifact | Location | Status |
|---|---|---|
| Master SEED doc | `2 SEED/C_MECHANICS/SEED_C_MAP_UNITS_MASTER_v1.md` | new (in progress — other agent) |
| Unit data model (SEED) | `2 SEED/D_ENGINES/SEED_D_UNIT_DATA_MODEL_v1.md` | new (in progress — other agent) |
| DET unit model | `3 DETAILED DESIGN/DET_UNIT_MODEL_v1.md` | **new (this session)** |
| DB schema draft | `CONCEPT TEST/db_schema_v1.sql` | **new (this session)** |
| Config module (py) | `app/engine/config/map_config.py` | new (other agent) |
| Config module (js) | `app/test-interface/static/map_config.js` | new (other agent) |
| Canonical units | `2 SEED/C_MECHANICS/C4_DATA/units.csv` | v1.0 |
| Candidate scenario | `2 SEED/C_MECHANICS/C4_DATA/units_layouts/start_one.csv` | v1.0 |
| Units legacy backup | `2 SEED/C_MECHANICS/C4_DATA/units_legacy_zone_id.csv` | archived |
| Global map state | `2 SEED/C_MECHANICS/C1_MAP/SEED_C1_MAP_GLOBAL_STATE_v4.json` | v4 |
| Eastern Ereb state | `2 SEED/C_MECHANICS/C1_MAP/SEED_C3_THEATER_EASTERN_EREB_STATE_v3.json` | v3 (pending global_link resync) |
| Mashriq state | `2 SEED/C_MECHANICS/C1_MAP/SEED_C3_THEATER_MASHRIQ_STATE_v1.json` | v1 (pending global_link adds + self-occ scan) |
| Map viewer harness | `app/test-interface/templates/map.html` + `static/map.{js,css}` | operational |
| Map context (engine) | `app/engine/agents/map_context.py` | migrated to coord schema |

**Completion tally:** 32 completed / 24 pending ≈ **57% reconciliation complete**.

---

## ✅ Unit notes cleanup — COMPLETED 2026-04-05

**Problem:** `layout_units.notes` (and source `units.csv`) contained real-world names ("Pentagon", "Kremlin", "Kursk", "Okinawa"), equipment names ("F-35", "Iskander", "Patriot", "S-400", "Minuteman III", "Tomahawk"), unit sub-types ("artillery", "marines", "ICBM", "brigade", "corps", "squadron"), and operational tags ("Operation Rising Lion"). These leaked real-world identity into fiction and implied imaginary mechanics beyond the 5-type model.

**Fix:** Replaced every `notes` value with a SIM-native label `"{Country} {posture}"` where posture ∈ {home garrison, forward deployment, theater deployment, fleet, reserve, embarked, destroyed}. Posture derived from `status` + unit coordinates versus owner grid in `SEED_C1_MAP_GLOBAL_STATE_v4.json` (home garrison when hex owner == country_id, forward deployment otherwise; naval on `sea` hex → fleet).

**Rows updated:**
- `units.csv`: 345 rows (backup: `units.csv.bak_pre_notes_cleanup`)
- Supabase `layout_units` (template_v1_0_default): 345 rows
- Supabase `layout_units` (start_one): 345 rows

**Unique values after cleanup:** 55 (down from 289)

**Sample before/after:**
| unit_id | before | after |
|---|---|---|
| col_g_01 | CONUS central - Ft Campbell/Pentagon | Columbia embarked |
| col_g_09 | Poland V Corps HQ forward | Columbia reserve |
| sar_g_15 | Bakhmut/Chasiv Yar | Sarmatia home garrison |
| col_n_06 | 7th Fleet WestPac CSG | Columbia fleet |
| alb_n_02 | Atlantic SSBN patrol | Albion fleet |

**Top posture distribution:**
- Columbia reserve: 32
- Cathay reserve: 32
- Sarmatia forward deployment: 26
- Ruthenia forward deployment: 15
- Columbia forward deployment: 12

**Verification:** Regex scan of DB for real-world/equipment/sub-type terms (F-35, Iskander, Patriot, Russian, Ukrainian, Kursk, Okinawa, Pentagon, Kremlin, CONUS, brigade, corps, artillery, ICBM, squadron, Operation, Bakhmut, Tehran, Minuteman, Tomahawk, S-400, marines) → **0 matches**. No real-world names, equipment, or sub-type language remains.

---

## DATA ENRICHMENT — Nuclear Sites + Public Bios (2026-04-08)

### Nuclear site hex coordinates — canonical storage confirmed

Verified that `sim_templates.map_config.nuclear_sites` already contains correct values:
- Persia: `{global_row: 7, global_col: 13}` (Mashriq theater-link hex)
- Choson: `{global_row: 3, global_col: 18}` (global map, no theater)

Added `NUCLEAR_SITES` constant to `app/engine/config/map_config.py` for code-level access. Documented in SEED_C_MAP_UNITS_MASTER_v1.md section 1.3a. Updated CARD_FORMULAS.md and CARD_TEMPLATE.md with canonical references.

### `public_bio` column added to roles table

**Migration:** `ALTER TABLE roles ADD COLUMN IF NOT EXISTS public_bio text NOT NULL DEFAULT '';`

**40 bios written** — 2-3 sentences each, public-facing only:
- Who the person is, their title, age
- Known policy positions and public reputation
- NO secret objectives, NO ticking clocks, NO hidden agendas

These bios serve as the "world knowledge" that all participants and AI agents can reference about each character. Updated DET_B1_DATABASE_SCHEMA.sql, CARD_TEMPLATE.md, and STARTING_DATA_AUDIT.md (M4 + M5 marked FIXED).

---

## DATA FIX — Relationship Status Column + Basing Rights (2026-04-08)

### C1 FIXED: `status` column corrected from all-"peace" to proper 8-state values

All 380 rows in `relationships` had `status = 'peace'` regardless of actual relationship. Updated via mapping from `relationship` column:

| relationship value | status value |
|---|---|
| close_ally, alliance | allied |
| friendly | friendly |
| neutral | neutral |
| tense | tense |
| hostile, strategic_rival | hostile |
| at_war | military_conflict |

**Result:** neutral 128, friendly 126, hostile 43, allied 42, tense 35, military_conflict 6.

Engine code reading `status = 'military_conflict'` now correctly identifies 6 at-war pairs (Sarmatia-Ruthenia, Persia-Columbia, Persia-Levantia).

### C2 FIXED: Starting basing rights seeded (12 records)

Set `basing_rights_a_to_b = true` for 12 host-guest pairs reflecting real-world military base parallels:

**Columbia bases abroad (9 hosts):**
- Yamato (Okinawa), Hanguk (Camp Humphreys), Teutonia (Ramstein), Albion (RAF bases), Phrygia (Incirlik), Formosa (informal), Mirage (Al Dhafra), Ponte (Aviano/Sigonella), Freeland (Redzikowo)

**Sarmatia-Choson mutual (2 records):**
- Choson hosts Sarmatia, Sarmatia hosts Choson

**Gallia abroad (1 host):**
- Mirage hosts Gallia (Djibouti parallel)

Column semantics: `basing_rights_a_to_b = true` means `from_country_id` (a) is the HOST granting basing to `to_country_id` (b).

### Schema documentation updated
- DET_B1_DATABASE_SCHEMA.sql: added `status` and `basing_rights_*` columns with CHECK constraints and comments
- CARD_ARCHITECTURE.md: relationships table description updated
- CARD_TEMPLATE.md: starting relationships and basing rights documented
- SEED_C_MAP_UNITS_MASTER_v1.md: basing rights section added
- STARTING_DATA_AUDIT.md: C1 and C2 marked FIXED

---

## 8-STATE BILATERAL RELATIONSHIP MODEL — Cross-Document Embedding (2026-04-08)

**Scope:** Canonical 8-state bilateral relationship model embedded across all SEED, DET, PHASE, and code documents.

**Dual-column semantics established:**
- `relationship` column = STARTING/REFERENCE value (frozen per template, legacy CSV labels)
- `status` column = LIVE engine state (8-state model: allied, friendly, neutral, tense, hostile, military_conflict, armistice, peace)
- Engine reads `status` for all war/peace checks

**Key rule:** `military_conflict` is STICKY — only transitions via signed armistice or peace treaty. Armistice breach → auto-return to `military_conflict` + global notification.

### Documents updated:
| Document | Change |
|---|---|
| `2 SEED/C_MECHANICS/SEED_C_MAP_UNITS_MASTER_v1.md` | Added section 5a with full 8-state table, transition rules, dual-column semantics, relationship→status mapping |
| `2 SEED/D_ENGINES/SEED_D8_ENGINE_FORMULAS_v1.md` | Added section 5a (after agreement spec) with 8-state enum and key rules |
| `3 DETAILED DESIGN/DET_B1_DATABASE_SCHEMA.sql` | Enhanced comment block on relationships table with full 8-state documentation |
| `3 DETAILED DESIGN/DET_C1_SYSTEM_CONTRACTS.md` | Added typed enum `RelationshipStatus`, updated agent context shape from 6 to 8 states |
| `PHASES/UNMANNED_SPACECRAFT/INFORMATION_SCOPING.md` | Added dual-column note to existing 8-state section |
| `PHASES/UNMANNED_SPACECRAFT/CARD_ARCHITECTURE.md` | Added dual-column semantics + 8-state summary to relationships table |
| `PHASES/UNMANNED_SPACECRAFT/CARD_FORMULAS.md` | Replaced simplified AT WAR/PEACE diagram with full 8-state table + transition diagram |
| `app/engine/models/db.py` | Added `status`, `basing_rights_a_to_b`, `basing_rights_b_to_a` fields to Relationship Pydantic model |
| `app/engine/agents/leader.py` | Extended `_initial_relationships()` rel_map with all 8 canonical states + legacy labels |

### Code alignment check:
- `at_war` usage in engine code (`engines/economic.py`, `engines/political.py`, `engines/round_tick.py`) refers to a boolean `_at_war` flag derived from combat/relationship status — NOT the `status` column value. This is consistent with the model (the engine detects war state from events, which drives the `status` column update).
- Legacy `at_war` string values in CSV data files and template JSONB (`at_war_with` field) are starting data that maps to `military_conflict` in the `status` column.
- `stage*_results/` JSON files contain `at_war` boolean fields — these are test fixtures, not production data. No change needed.

---

## BUDGET VERTICAL SLICE — DONE end-to-end (2026-04-10)

**Scope:** First of the four mandatory end-of-round decisions shipped as a fully polished vertical slice. CONTRACT_BUDGET v1.1 is now 🔒 LOCKED. The 7-step methodology used to ship this is documented as the template for sanctions/tariffs/OPEC.

### Design decisions locked

| # | Decision | Why |
|---|---|---|
| 1 | Removed all percentage caps (40% military, 30% R&D) | Caps were invented during implementation, not in SEED_D8. Over-spending now feeds the deficit cascade directly. |
| 2 | Production is level-based (0/1/2/3), not coin-based | Matches policymaker thinking, not accountant typing. Level × capacity × branch_unit_cost → coins. |
| 3 | Level 3 is non-linear: 4× cost for 3× output | "Emergency gear" — deliberately worthwhile only in crisis. |
| 4 | Social spending is continuous (slider, not tier) | Linear formulas: stability_delta = (social_pct−1.0)×4, support_delta = ×6. |
| 5 | Research is absolute coins, not levels | R&D is a funding decision, not a pacing decision. |
| 6 | strategic_missile + air_defense in schema, capacity 0 for all countries | Forward-compatible. Raising capacity is a pure data change. |
| 7 | `no_change` must explicitly omit the `changes` field; rationale required for both branches (≥30 chars) | Explicit choice, not silent default. |
| 8 | Validator returns ALL errors in one pass | Fail-fast wastes participant time. |
| 9 | Context package includes a dry-run "no-change forecast" using the real engine on a deep copy | Single source of truth — preview = real round. |

### Two known gaps closed

- **Gap A (units not persisted):** added 5 mil_* integer columns to `country_states_per_round` (`mil_ground`, `mil_naval`, `mil_tactical_air`, `mil_strategic_missiles`, `mil_air_defense`). Backfilled R0 from `countries`. Migration: `add_mil_columns_country_states_per_round`. Fixed `_merge_to_engine_dict` to load from snapshot first; extended write-back payload to persist credited units.
- **Gap B (R&D progress truncated):** `nuclear_rd_progress` and `ai_rd_progress` already existed as numeric columns but were loaded via `int()` and never written back. Fixed both halves; multi-round R&D progress now accumulates correctly with 6-decimal precision.

### Documents updated

| Document | Change |
|---|---|
| `PHASES/UNMANNED_SPACECRAFT/CONTRACT_BUDGET.md` | 🔒 LOCKED status header, version 1.1, list of consumers |
| `PHASES/UNMANNED_SPACECRAFT/CHECKPOINT_BUDGET.md` | NEW — durable record of the slice (decisions, code, tests, demo numbers, gaps closed, pointers) |
| `PHASES/UNMANNED_SPACECRAFT/PHASE.md` | Marked Sprint B6 budget portion DONE, added 2026-04-10 status block |
| `PHASES/UNMANNED_SPACECRAFT/CARD_FORMULAS.md` | A.6 + A.7 rewritten to match v1.1 (caps removed, level scale, social slider formula, branch unit costs) |
| `PHASES/UNMANNED_SPACECRAFT/CARD_ACTIONS.md` | 2.1 set_budget rewritten with v1.1 schema, removed cap language, added validator + context refs |
| `EVOLVING METHODOLOGY/VERTICAL_SLICE_PATTERN.md` | NEW — the 7-step methodology template for sanctions/tariffs/OPEC |

### Code changed

- `app/engine/engines/economic.py` — `calc_budget_execution`, `calc_military_production`, `calc_tech_advancement` rewritten for v1.1; added `_compute_production_from_levels` helper, `PRODUCTION_COST_MULT`, `PRODUCTION_OUTPUT_MULT`, `BRANCH_UNIT_COST`, `BUDGET_PRODUCTION_BRANCHES`, `SOCIAL_STABILITY_MULT`, `SOCIAL_SUPPORT_MULT` constants; removed all percentage caps; extended `BudgetResult` dataclass.
- `app/engine/engines/round_tick.py` — `_merge_to_engine_dict` loads units from snapshot first (fall back to base), R&D progress as float (was truncating int), added strategic_missile + air_defense to production_capacity. Write-back payload extended with 5 mil_* counts + 2 R&D progress floats + 2 tech levels.
- `app/engine/round_engine/resolve_round.py` — `set_budget` handler runs the validator, writes JSONB columns, emits `budget_rejected` events on invalid input.
- `app/engine/services/budget_validator.py` — NEW pure validator with 10 error codes per CONTRACT §4.
- `app/engine/services/budget_context.py` — NEW context builder + dry-run service.

### Tests

- L1: 16 in `test_budget_engine.py`, 36 in `test_budget_validator.py`
- L2: 3 in `test_budget_persistence.py`, 8 in `test_budget_context.py`, 10 in `test_budget_e2e.py`
- L3: 10 LLM decisions in `test_skill_mandatory_decisions.py` (D1 budget portion ported to v1.1) + 1 acceptance gate in `test_budget_full_chain_ai.py`
- All passing as of 2026-04-10. Both gaps verified by hard DB-backed assertions in `test_budget_e2e.py`.

### Out of scope (deferred to post-phase architectural re-synthesis)

- Full SEED_D8 rewrite — needs sanctions/tariffs/OPEC to be at the same level first
- Unified mandatory-decision base contract — same reason
- CONCEPT/SEED frozen documents — no changes during mid-phase work
- Schema cleanup of stale `budget_military_coins` / `budget_tech_coins` columns — separate ticket

---

## TARIFFS VERTICAL SLICE — DONE end-to-end (2026-04-10)

**Scope:** Second of the mandatory end-of-round decisions shipped as a fully polished vertical slice. CONTRACT_TARIFFS v1.0 is now 🔒 LOCKED. **First slice shipped under the corrected "decision-specific context only" boundary** — cognitive blocks (identity/memory/goals/world rules) are provided by the AI Participant Module (future work), not by decision context builders.

### Strategy directive (Marat 2026-04-10)

Complete engines + contracts + DB + decision-specific context for ALL SIM activities, one slice at a time, with full focus. Order: budget ✅ → tariffs ✅ → sanctions → oil (OPEC) → military actions (standard/blockade/nuclear) → military movements → nuclear decisions → transactions → agreements → other actions. Then reconcile up to CONCEPT and SEED in a single coherent pass. Then build the AI Participant Module v1.0 on a known-good substrate. Do not patch the AI module inside decision slices. Tests emulate the cognitive layer with a persona stub in the harness only.

### Design decisions locked

| # | Decision | Why |
|---|---|---|
| 1 | Action is `set_tariffs` (plural) | One submission carries country's full intent for the round |
| 2 | `changes.tariffs` is sparse dict `{target: level}` | Name only changed targets; untouched carry forward via state table |
| 3 | Level 0 means lift (no separate action) | Uniform schema |
| 4 | Self-tariff and unknown-target are hard rejections | `SELF_TARIFF` / `UNKNOWN_TARGET` validator errors |
| 5 | Rationale ≥30 chars required for both change and no_change | Forces explicit reasoning |
| 6 | `no_change` must OMIT `changes` field entirely | Structurally distinct |
| 7 | Empty `changes.tariffs = {}` on a change is invalid | Use `no_change` instead |
| 8 | No forecast/dry-run in context | Tariff consequences are emergent |
| 9 | **Decision-specific context only, NO cognitive blocks** | Boundary rule for all slices going forward |
| 10 | Engine math UNCHANGED | Slice locks contract around existing `calc_tariff_coefficient`; constants pinned in L1 regression tests |

### Documents updated

| Document | Change |
|---|---|
| `PHASES/UNMANNED_SPACECRAFT/CONTRACT_TARIFFS.md` | NEW — 🔒 LOCKED v1.0 (with v1.0-rev2 boundary correction) |
| `PHASES/UNMANNED_SPACECRAFT/CHECKPOINT_TARIFFS.md` | NEW — durable record of the slice |
| `PHASES/UNMANNED_SPACECRAFT/PHASE.md` | Added tariffs DONE status + strategic directive block |
| `PHASES/UNMANNED_SPACECRAFT/CARD_FORMULAS.md` | A.3 rewritten with locked constants, contract pointer, regression test reference |
| `PHASES/UNMANNED_SPACECRAFT/CARD_ACTIONS.md` | 2.2 rewritten with v1.0 schema, sparse changes semantics, validator ref, context ref |
| `EVOLVING METHODOLOGY/VERTICAL_SLICE_PATTERN.md` | v1.1 — added "⚠️ Boundary statement — READ FIRST" section + Step 5 rewrite (decision-specific only, no cognitive assembly) |

### Code changed

- `app/engine/services/tariff_validator.py` — NEW pure validator, 11 error codes, `CANONICAL_COUNTRIES` frozenset (20 countries)
- `app/engine/services/tariff_context.py` — NEW decision-specific context builder (economic state, full 20-country roster with trade rank, bilateral tariffs both directions, decision rules with no_change reminder). NO cognitive blocks.
- `app/engine/round_engine/resolve_round.py` — added `set_tariffs` (plural) handler: validate, write audit JSONB, upsert state table for each sparse entry
- `app/engine/engines/economic.py` — UNCHANGED (engine math is the contract)

### DB migration

- `add_tariff_decision_country_states_per_round` — added `tariff_decision` JSONB column to `country_states_per_round` for the per-round decision audit record. Canonical world state remains in the `tariffs` state table (unchanged).

### Tests

- L1: 41 in `test_tariff_validator.py`, 22 in `test_tariff_engine.py` (regression lock)
- L2: 4 in `test_tariff_persistence.py`, 6 in `test_tariff_context.py`
- L3: 10 LLM decisions in `test_skill_mandatory_decisions.py` D3 portion + 1 acceptance gate in `test_tariffs_full_chain_ai.py`
- **Total: 84 tests green**

### Concrete demo (2026-04-10 acceptance gate)

Columbia R85→R86, real LLM decision:
```json
{
  "decision": "change",
  "rationale": "Escalating pressure on Persia during active war.",
  "changes": { "tariffs": { "persia": 2 } }
}
```
Result: `tariff_decision` JSONB matches, `(columbia, persia).level` upserted to 2, `tariff_coefficient` moved 1.0 → 0.997538 (matches contract's small self-damage at L2).

### Out of scope (deferred)

- Any change to `calc_tariff_coefficient` or its constants (locked by regression tests)
- Trade agreement actions (separate slice)
- Multilateral coalition logic (emergent from individual decisions)
- Legacy singular `set_tariff` / `lift_tariff` removal (kept in parallel for migration)
- Forecast/dry-run preview (deferred — learning by doing or future intelligence skill)
- Backport of 4-block cognitive context to budget — **superseded by the new boundary**; no backport needed
- Cognitive persistence (cognitive_states table, self-curated memory, goal evolution) — AI Participant Module v1.0, separate phase block
- CONCEPT/SEED reconciliation — waits until ALL decision slices ship

---

## SANCTIONS VERTICAL SLICE — DONE end-to-end (2026-04-10)

**Scope:** Third of the mandatory end-of-round decisions shipped as a fully polished vertical slice. CONTRACT_SANCTIONS v1.0 is now 🔒 LOCKED. **First slice with a real engine rewrite** — the sanctions math was redesigned with Marat during calibration (vs. budget/tariffs which locked contracts around existing behavior).

### Key difference from budget/tariffs slices

Budget and tariffs both used the "lock the engine around existing math" pattern. Sanctions required a real rewrite because the existing engine had:
- Global `SANCTIONS_MAX_DAMAGE = 0.87` constant (inverted semantics — meant "floor 0.13")
- Redundant `trade_openness` factor
- Hand-wavy `sector_vulnerability` multiplier
- Contradictory floor values (SEED_D8 said 0.13, CARD_FORMULAS/engine said 0.50)
- Dead adaptation code (4 constants + `update_sanctions_rounds()` counter not read by anyone)
- Documented-but-unimplemented imposer cost
- L=−1 evasion rows in seed data that the engine silently ignored

Rather than lock the broken math, we rewrote it into a cleaner 3-step formula with Marat's new design.

### Design decisions locked

| # | Gap | Decision |
|---|---|---|
| G1 | Floor discrepancy (SEED 0.13 vs engine 0.50) | **Floor = 0.15** canonical everywhere |
| G2 | Imposer cost prose without formula | **Dropped** — target-damage-only model for now |
| G3 | Temporal adaptation: dead code + contradictory specs | **Dropped entirely.** Stateless recomputation. Also removed political.py's `sanctions_rounds > 4 ? 0.70 : 1.0` multiplier. |
| G4 | L=−1 anti-sanctions in seed data, no mechanism | **Signed coverage** `[-3, +3]`. Negative contributes negatively, clamped at 0 |
| G5 | Sector carve-outs (financial / tech / energy) | **Dropped.** Single integer level only. Sectoral nuance implicit via per-country max_damage ceiling |
| G6 | Mirage ±20% routing prose in DET_A1 | **Deleted** from DET_A1. No special role mechanic |
| G7 | Missing contract / validator / context / mandatory-decision flow | **Slice work** — all built |

### Canonical new formula (v1.0)

```
max_damage  = tec × 0.25 + svc × 0.25 + ind × 0.125 + res × 0.05    # per-country sector ceiling
coverage    = Σ (actor_gdp_share × level / 3)                         # level ∈ [-3, +3]
coverage    = clamp(coverage, 0, 1)
effectiveness = S_curve(coverage)                                     # new 11-knot steeper curve
damage      = max_damage × effectiveness
coefficient = max(0.15, 1.0 - damage)
```

Per-country sector-derived ceilings: Levantia 22.5% (services+tech), Columbia 21.9%, Cathay 17.5% (industrial), Sarmatia 13.9% (resources), Caribe 12.5% (pure resource).

New steeper S-curve with tipping point at coverage 0.5 → 0.6 (+0.20 effectiveness jump).

### Canonical calibration anchors (Sarmatia, locked in L1 tests)

| Scenario | GDP loss |
|---|---|
| Clean world | 0.00% |
| Teutonia alone L3 | 0.40% |
| Columbia alone L3 | 2.86% |
| **Real DB starting (12 actors incl. Cathay L−1 evasion)** | **5.10%** |
| Starting + Cathay flips L−1 → L+2 | 9.72% |

### Documents updated

| Document | Change |
|---|---|
| `PHASES/UNMANNED_SPACECRAFT/CONTRACT_SANCTIONS.md` | NEW — 🔒 LOCKED v1.0 |
| `PHASES/UNMANNED_SPACECRAFT/CHECKPOINT_SANCTIONS.md` | NEW — durable record of the slice |
| `PHASES/UNMANNED_SPACECRAFT/PHASE.md` | Added sanctions DONE status block |
| `PHASES/UNMANNED_SPACECRAFT/CARD_FORMULAS.md` | A.2 rewritten with new 3-step formula + constants + canonical anchors |
| `PHASES/UNMANNED_SPACECRAFT/CARD_ACTIONS.md` | 2.3 rewritten with set_sanctions (plural) + signed level range + removed false "imposer cost" and "adaptation" claims |
| `2 SEED/D_ENGINES/SEED_D8_ENGINE_FORMULAS_v1.md` | §Sanctions Hit rewritten to match new canonical formula; Pass 2 adaptation line struck |
| `3 DETAILED DESIGN/DET_C1_SYSTEM_CONTRACTS.md` | §MandatoryInputs sanctions schema updated to reference CONTRACT_SANCTIONS v1.0 |

### Code changed

- `app/engine/engines/economic.py` — `calc_sanctions_coefficient` rewritten, `_sanctions_max_damage` helper added, new constants, dead constants removed, `update_sanctions_rounds()` deleted
- `app/engine/engines/political.py` — removed `sanctions_rounds > 4 ? 0.70 : 1.0` adaptation multiplier; `StabilityInput.sanctions_rounds` field left deprecated for backward compat
- `app/engine/engines/round_tick.py` — cleaned `_merge_to_engine_dict` (dead column refs removed)
- `app/engine/engines/orchestrator.py` — cleaned engine dict construction + result persistence
- `app/engine/agents/runner.py` — cleaned agent runner state init
- `app/engine/models/db.py` — removed dropped fields from Country Pydantic model
- `app/engine/round_engine/resolve_round.py` — added `set_sanctions` (plural) handler
- `app/engine/services/sanction_validator.py` — NEW pure validator (11 error codes, signed `[-3, +3]` level range)
- `app/engine/services/sanction_context.py` — NEW decision-specific context builder (economic state + all 20 countries with coalition coverage per target + my_sanctions + sanctions_on_me + decision rules). No cognitive blocks.

### DB migration

- `sanctions_v1_canonical_schema` — added `sanction_decision` JSONB column to `country_states_per_round`; dropped `sanctions_adaptation_rounds` and `sanctions_recovery_rounds` from `countries`; cleared sectoral text from all 36 `sanctions.notes` rows (column kept); Cathay → Sarmatia L=−1 row preserved (now canonically valid under signed-coverage model).

### Tests

- L1: 27 in `test_sanctions_engine.py` (regression lock + calibration anchors + signed coverage), 44 in `test_sanction_validator.py` (11 error codes + signed level range), S-curve tests in `test_engines.py` updated for new 11-knot curve
- L2: 4 in `test_sanction_persistence.py` (change, no_change, **negative level evasion persists**, invalid rejected), 7 in `test_sanction_context.py` (economic state + all 20 countries + **coalition coverage per target** + my_sanctions + sanctions_on_me + decision rules + **negative level display**)
- L3: 10 LLM D2 decisions via updated `test_skill_mandatory_decisions.py` (sanctions prompt rewritten to v1.0 schema with signed levels + persona stub) + 1 full-chain acceptance gate in `test_sanctions_full_chain_ai.py`
- **Total: 83 sanctions-specific tests green.** Full L1 suite: 295 green.

### Concrete demo (2026-04-10 acceptance gate run)

Columbia R75→R76, real LLM decision: `set_sanctions change {cathay: 3}` with rationale "Adding maximum sanctions against Cathay to contain strategic rival". Chain: validator ✓ → agent_decisions ✓ → resolve_round (audit JSONB + state table upsert) ✓ → run_engine_tick (coefficient recomputed) ✓. Result: Cathay's `sanctions_coefficient` moved 1.0 → 0.9639 (−3.61% one-time GDP shock). Matches hand-calculated prediction.

### Out of scope (deferred)

- Imposer cost / evasion benefit formulas — dropped per G2 "no negative impact for now"
- Full Pass 2 / NOUS architectural layer — separate phase block
- Cognitive persistence (cognitive_states table) — AI Participant Module v1.0
- CONCEPT/SEED architectural re-synthesis — waits until all decision slices ship
- Cleanup of `StabilityInput.sanctions_rounds` deprecated field — future cleanup pass
- OPEC slice — next in the sequence per Marat's strategy directive

---

## OPEC VERTICAL SLICE — DONE end-to-end (2026-04-11)

**Scope:** Fourth and final mandatory-decision vertical slice. **All 4 mandatory decisions now shipped.** CONTRACT_OPEC v1.0 🔒 LOCKED. Engine math UNCHANGED — contract-around-existing-behavior pattern (tariff template, not a sanctions-style rewrite). The existing `calc_oil_price` OPEC section at lines 650-659 already matched SEED_D8 + CARD_FORMULAS A.1; we locked it with regression tests and built the validator + context + persistence around it.

### Design decisions locked

| # | Gap | Decision |
|---|---|---|
| G1 | Field name chaos (`production` vs `production_level` vs `new_level`) | **Canonical: `production_level`** — nested inside `changes.production_level` |
| G2 | No validator | **NEW** `opec_validator.py` with 9 error codes + CANONICAL_OPEC_MEMBERS frozenset |
| G3 | OPEC+ roster mismatch between DB and code | **5 canonical members** per Marat 2026-04-11: `{caribe, mirage, persia, sarmatia, solaria}`. Fixed DB (Caribe `opec_member=true`), fixed code constant, contract locks it. |
| G4 | R0 snapshot pollution (all 20 had `opec_production="normal"`) | Migration cleans non-OPEC rows to `"na"` — 15 cleaned, 5 OPEC+ members stay at `"normal"` |
| G5 | Engine doesn't check OPEC membership | Not an engine problem — enforced at validator + handler layer. Documented as implicit contract in regression tests. |
| G6 | No per-round decision audit | **NEW** `country_states_per_round.opec_decision` JSONB column (matches tariff_decision/sanction_decision pattern) |
| G7 | No mandatory-decision flow | Slice work — contract/validator/context/persistence/harness/gate all built |
| G8 | D4 skill harness had wrong roster + wrong field + old 20-char rationale | Rewritten to v1.0 schema with 5-member roster, `production_level`, 30-char rationale |

### Key design principle (inherited from prior slices)

- **Decision-specific context is data-only per Marat's 2026-04-10 directive.** No commentary, no warnings, no "consider X" hints. The context delivers raw facts; interpretation is the participant's job. Only the no_change reminder remains (approved separately by Marat).

### Canonical new facts

- **OPEC+ roster: 5 members**: Caribe (0.8 mbpd), Mirage (3.5), Persia (3.5), Sarmatia (10), Solaria (10). Caribe = Venezuela-equivalent, Sarmatia = Russia-equivalent OPEC+. Total OPEC+ share ~68% of world oil supply.
- **Columbia** (13 mbpd, 31.7% world supply) is the biggest producer in the world but NOT OPEC+. Free agent.
- **Engine unchanged** — `calc_oil_price` OPEC section already correct. Constants locked: `OPEC_PRODUCTION_MULTIPLIER = {min:0.70, low:0.85, normal:1.00, high:1.15, max:1.30}` + 2× cartel leverage.

### Calibration anchors (Solaria, locked in L1)

| Scenario | Supply delta | Notes |
|---|---|---|
| Solaria alone at `min` | −0.147 supply (−15%) | 24.5% share × 30% cut × 2× leverage |
| Solaria alone at `max` | +0.147 supply | Symmetric |
| All 5 OPEC+ at `max` | +0.409 supply | Full market flood |
| Caribe alone at `min` | −0.012 supply (−1.2%) | Smallest member, marginal effect |

### Documents updated

| Document | Change |
|---|---|
| `PHASES/UNMANNED_SPACECRAFT/CONTRACT_OPEC.md` | NEW — 🔒 LOCKED v1.0 |
| `PHASES/UNMANNED_SPACECRAFT/CHECKPOINT_OPEC.md` | NEW — durable record |
| `PHASES/UNMANNED_SPACECRAFT/CARD_ACTIONS.md` | 2.4 rewritten with v1.0 schema, 5-member roster, level table, data-only context reference |
| `PHASES/UNMANNED_SPACECRAFT/PHASE.md` | Added OPEC DONE status block; Sprint B6 now **ALL 4 DONE** |

### Code changed

- `app/engine/agents/full_round_runner.py` — `OPEC_MEMBERS` updated to 5-member canonical set
- `app/engine/round_engine/resolve_round.py` — `set_opec` handler rewritten: validates, writes `opec_decision` JSONB audit + `opec_production` live value, emits `opec_rejected` events, handles backward-compat for top-level `production_level` field
- `app/engine/services/opec_validator.py` — NEW pure validator
- `app/engine/services/opec_context.py` — NEW decision-specific context builder (9 blocks, data-only)
- `app/tests/layer3/test_skill_mandatory_decisions.py` — D4 OPEC prompt rewritten, scenarios updated with OPEC fields for Sarmatia/Solaria/Caribe/Persia, real validator assertion

### DB migration

`opec_v1_canonical_schema`:
- Added `country_states_per_round.opec_decision` JSONB column
- Fixed `countries.opec_member = true` for Caribe
- Cleaned R0 snapshot: non-OPEC countries → `opec_production = 'na'`

### Tests

- L1: 47 in `test_opec_validator.py`, 20 in `test_opec_engine.py` (regression lock)
- L2: 4 in `test_opec_persistence.py`, 10 in `test_opec_context.py`
- L3: D4 OPEC portion updated + 1 acceptance gate in `test_opec_full_chain_ai.py`
- **Total: 82 OPEC-specific tests green.** Full L1 suite continues green.

### Concrete demo (2026-04-11 acceptance gate run)

Solaria R40→R41, real LLM decision: `set_opec no_change` with rationale "Current oil price at $78/bbl provides solid revenue while maintaining market stability. No immediate need to adjust production given stable economic conditions and absence of external pressures."

Chain: validator ✓ → agent_decisions ✓ → resolve_round (audit JSONB written, live value unchanged per no_change) ✓ → run_engine_tick (oil price recomputed) ✓. Result: oil_price $85 → $87.20, Solaria `opec_production = "normal"` (unchanged). Audit JSONB matches AI output byte-for-byte.

### All 4 mandatory decisions — milestone

With OPEC locked, all 4 mandatory decision slices are complete:

| Decision | Status | Commit |
|---|---|---|
| Budget | 🔒 DONE 2026-04-10 | `776aaaf` |
| Tariffs | 🔒 DONE 2026-04-10 | `8a4c9d1` |
| Sanctions | 🔒 DONE 2026-04-10 | `175fbe3` |
| OPEC | 🔒 DONE 2026-04-11 | this commit |

**Milestone:** the economic decision layer is complete. Every economic lever in the sim is now fully specified, tested, and canonical. Next per strategy directive: Military Actions slices.
