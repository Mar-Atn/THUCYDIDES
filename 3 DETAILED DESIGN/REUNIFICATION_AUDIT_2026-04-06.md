# Architectural Reunification Audit
**Date:** 2026-04-06
**Author:** Claude (in collaboration with Marat)
**Purpose:** Identify architectural drift between the designed modules (SEED/DET) and the parallel test-harness code built during calibration. Decide what to keep, port, and delete.

---

## Context

During calibration testing (2026-04-04 → 2026-04-06) a parallel code path was built in `app/engine/round_engine/` + `app/engine/agents/stage*_test.py` to iterate the Observatory UI quickly. Meanwhile the DESIGNED modules in `app/engine/engines/`, `app/engine/agents/leader.py`, and `app/engine/context/` (built in the DET phase) were left unused. This audit catalogs the drift and proposes a reunification plan.

**Marat's direction (2026-04-06):** "I want us to work with modules, and document them properly. Test work should mostly prevail over initial design when specific elements were agreed. Keep the vision, keep the architectural solution."

---

## Module inventory

| Module | Built | Used by | LOC | Status |
|---|---|---|---|---|
| **DESIGNED (canonical)** | | | | |
| `engine/context/assembler.py` | yes | nothing | 184 | Orphaned |
| `engine/context/blocks.py` | yes | nothing | 429 | Orphaned |
| `engine/agents/leader.py` | yes | nothing | 693 | Orphaned |
| `engine/engines/military.py` | yes | nothing | 1,840 | Orphaned |
| `engine/engines/economic.py` | yes | orchestrator only | 2,011 | Orphaned (no live call) |
| `engine/engines/political.py` | yes | orchestrator only | 836 | Orphaned |
| `engine/engines/technology.py` | yes | nothing | 357 | Orphaned |
| `engine/engines/orchestrator.py` | yes | not wired to test runner | 543 | Orphaned |
| **PARALLEL (test harness)** | | | | |
| `engine/round_engine/combat.py` | yes | `full_round_runner` | ~320 | **Has calibration** |
| `engine/round_engine/resolve_round.py` | yes | `full_round_runner` | ~550 | **Has calibration** |
| `engine/round_engine/movement.py` | yes | `resolve_round` | ~180 | **Has calibration** |
| `engine/round_engine/rd.py` | yes | `resolve_round` | ~40 | Simple stub |
| `engine/agents/stage5_test.py` | yes | `full_round_runner` | ~460 | Live |
| `engine/agents/full_round_runner.py` | yes | observatory server | ~400 | Live |
| **LEGITIMATE NEW** | | | | |
| `engine/services/llm_tools.py` | yes | stage5 + future leader | ~320 | **Keep — belongs in designed architecture** |

**Summary:** ~7,000 lines of designed but unused code + ~2,300 lines of parallel calibrated code. ~9.3K lines that must be unified into one stack.

---

## Conflict map (calibrated rules vs designed rules)

### C1. Combat data model — **STRUCTURAL CONFLICT**

| Aspect | Designed (`engines/military.py`) | Calibrated (`round_engine/combat.py`) |
|---|---|---|
| **State unit** | `ZoneInfo` with `forces: dict[country, dict[type, count]]` | per-unit dict with `unit_code`, `global_row/col`, `theater*`, `status` |
| **Combat pairing** | unit COUNTS (e.g. 3 attackers vs 2 defenders) | unit INSTANCES (specific unit_codes tracked) |
| **Loss tracking** | `attacker_losses: int` | `attacker_losses: list[unit_code]` |
| **Source spec** | DET_B1 `ZoneInfo`, SEED world_state.py | CON_C2_v2 + Marat calibration 2026-04-05 |

**Conflict resolution (per Marat "test prevails"):** unit-level model wins. Requires military.py to be restructured from zone+count → unit-level. Substantial refactor (~800 lines affected).

**Cost:** high. **Benefit:** matches DB schema (`unit_states_per_round` is already unit-level), enables trophies, theater visualization, unit-specific mechanics.

---

### C2. Air strike mechanics — **NUMBERS CONFLICT**

| Aspect | Designed | Calibrated (2026-04-06) |
|---|---|---|
| Base hit prob | 15% per surviving aircraft | **12%** |
| AD effect | **INTERCEPTS** incoming aircraft (destroys them); rate degrades 95→80→60% per attempt | **Coverage flag halves hit prob** (12% → 6%) |
| Aircraft losses | yes (interception) | no (no attacker losses from AD) |
| Air superiority | n/a | +2% per unit, cap +4% |
| Range | n/a (zone-adjacent only?) | **≤2 hexes** from launching unit |

**Conflict resolution:** Calibrated numbers win (12%/6%). Interception model is arguably more realistic — **Marat decision needed: merge the two (halving + occasional interception) or keep pure halving?** My recommendation: **pure halving for now** (simpler, matches test calibration); optionally add 5% interception chance per AD as secondary loss mechanism later.

---

### C3. Missile strike mechanics — **NUMBERS + MODEL CONFLICT**

| Aspect | Designed | Calibrated (2026-04-06) |
|---|---|---|
| Hit prob (no AD) | implicit — limited by interception | **80%** |
| Hit prob (with AD) | AD makes ≤5 intercept attempts at 30% each | **30%** (halved directly) |
| Disposable | — | **yes, missile unit destroyed on fire** |
| Nuclear warheads | yes (L1, L2 with different damage models) | not modeled |

**Conflict resolution:** Calibrated numbers win for conventional missiles. Nuclear L1/L2 models from designed should be PRESERVED and ported — we'll need them before production.

---

### C4. Ground combat — **ALGORITHM CONFLICT**

| Aspect | Designed | Calibrated |
|---|---|---|
| Dice | 1d6 + modifiers each side, single pass | 3d6 vs 2d6 per exchange, ITERATIVE until one side zero |
| Win rule | attacker ≥ defender + 1 (ties defender) | standard RISK (ties defender) |
| Amphibious | -1 attacker modifier | +1 attacker modifier when 3:1 ratio |
| Naval adjacent defends | no | **yes (Marat 2026-04-06) — equal strength** |
| Trophy capture | no | **yes (Marat 2026-04-06) — non-ground non-naval captured** |
| Source min | not checked | ≥1 on captured hex before chaining |
| Post-victory move-forward | flag only (`zone_captured`) | physical `_move_attackers_forward` |

**Conflict resolution:** Calibrated model wins (iterative dice + naval-adjacent + trophies). Requires rewriting `resolve_attack` in military.py.

---

### C5. AD coverage zone — **SCOPE CONFLICT**

| Aspect | Designed | Calibrated |
|---|---|---|
| AD coverage | target zone only (resolve_air_strike also counts AD in adjacent zones!) | **global hex + ALL linked theater hexes** |

Interesting: designed actually reads adjacent zones' AD too (line 918-921). But the GEOMETRY is different — it's zone-adjacent, not theater-linked. Our calibration uses the canonical theater↔global linkage table.

**Conflict resolution:** Calibrated (theater-link-aware). Preserve the adjacent-zones idea where applicable.

---

### C6. Agent architecture — **COGNITIVE MODEL GAP**

| Aspect | Designed (`leader.py` + `context/*`) | Parallel (`stage5_test.py`) |
|---|---|---|
| Cognitive blocks | 4 blocks explicit: Rules / Identity / Goals / Memory | ad-hoc system prompt (name+title only) |
| Context assembly | via `ContextAssembler` with block registry | inline f-string |
| Role data | full (powers, objectives, ticking_clock, intel_pool) | only character_name, title |
| SIM-name discipline | enforced in RULES_TEMPLATE | absent |
| Memory | `CognitiveState` with typed layers | dict of strings |
| Decision interface | matches DET_C1 PART 5 | custom tool calls |
| Persistence | via `memory.py` | via `tools.write_memory` |

**No conflict — designed is strictly richer.** The parallel stack is a 10% subset.

**Resolution:** Migrate to `leader.py`. Keep the stage5 memory tool mechanics (list/read/write) but feed them from the designed `CognitiveState`. The `llm_tools.py` dual-provider wrapper slots in underneath leader.py.

---

### C7. Round orchestration — **COMPLEMENTARY, NOT CONFLICTING**

| Concern | Designed (`orchestrator.py`) | Parallel (`resolve_round.py`) |
|---|---|---|
| Agent decision processing | NOT handled | **handled** (agent_decisions → combat, movement) |
| Economic tick | called | not called |
| Political tick | called | not called |
| Technology tick | n/a | R&D stub |
| Round snapshots | writes to unit_states_per_round? | writes |

**These are complementary!** The parallel `resolve_round` processes WHAT AGENTS DID. The designed `orchestrator` runs the BETWEEN-ROUNDS world tick. Both need to run — designed orchestrator should call into our decision-processor OR we merge them.

**Proposed merged sequence per round:**
1. Agents commit actions (already works)
2. **Decision processing** (current `round_engine/resolve_round`) — combat, movement, R&D
3. **World tick** (designed `orchestrator`) — economic/political/technology mutations
4. Snapshot next round state

**No conflict — just wiring.**

---

### C8. Observatory / dashboard — **NOT IN ARCHITECTURE**

The Observatory UI + API endpoints were built from scratch during this sprint. They weren't in the original DET. They're pure additions. **No conflict.** Will remain in `test-interface/`.

---

## Decision matrix

| Conflict | Decision | Cost | Note |
|---|---|---|---|
| C1 Data model | **Unit-level wins** | high (refactor military.py) | DB already unit-level |
| C2 Air strike | **Calibrated wins (12/6)** | medium | preserve interception idea for later |
| C3 Missile | **Calibrated wins (80/30, disposable)** | low | port nuclear models from designed |
| C4 Ground combat | **Calibrated wins (iterative + trophies)** | medium | |
| C5 AD coverage | **Calibrated wins (theater-linked)** | low | |
| C6 Agent architecture | **Designed wins (leader.py)** | medium | stage5_test → deprecated |
| C7 Orchestration | **Merge — complementary** | medium | plug both into sequence |
| C8 Observatory UI | **Keep as-is** | none | not in architecture |

---

## Recommended Reunification Sprint (revised)

### Phase 0 (DONE): this audit

### Phase 1 — Combat port + validation (~4 hours)
1. Rewrite `engines/military.resolve_attack` to unit-level iterative (from `round_engine/combat.resolve_ground_combat`)
2. Update `engines/military.resolve_air_strike` to 12%/6% halving model + range≤2
3. Update `engines/military.resolve_missile_strike` to 80%/30% + disposable
4. Preserve nuclear L1/L2 logic separately
5. Add `_ad_units_in_zone` + trophy capture helpers into military.py
6. Port naval-adjacent-defends-land
7. Unit tests against calibrated expected values

### Phase 2 — Agent migration (~3 hours)
1. Wire `leader.py` to use `llm_tools.call_tool_llm` (provider-agnostic)
2. Wire `context/assembler.py` + `blocks.py` as the system-prompt builder
3. Load role data from DB (already wired via `profiles.py`)
4. Memory tools from stage5 → merge into `memory.CognitiveState`
5. Validate 1 agent end-to-end round on Gemini

### Phase 3 — Orchestrator integration (~3 hours)
1. Add decision-processing step to `engines/orchestrator.run_round()` (port from `round_engine/resolve_round`)
2. Ensure orchestrator calls: decisions → military → economic → political → technology → snapshot
3. Swap `full_round_runner.py` to call `orchestrator.run_round()` instead of `round_engine.resolve_round()`
4. Run 2-round test on Gemini, verify observatory renders correctly

### Phase 4 — Decommission (~1 hour)
1. Delete `engine/round_engine/`
2. Delete `engine/agents/stage1_test.py ... stage5_test.py`, `runner.py`
3. Update `app/engine/CLAUDE.md`: forbid new code in deprecated paths; all engine work goes in `engine/engines/`
4. Update root CLAUDE.md traceability section

### Phase 5 — Traceability matrix (~2 hours)
Create `3 DETAILED DESIGN/TRACEABILITY_MATRIX.md`:
- concept | SEED anchor | DET anchor | code path | test path
- One row per calibration rule + one per architectural piece
- Update `CHANGES_LOG` to cross-reference this matrix going forward

### Phase 6 — Doc propagation (~1 hour)
Update SEED_E5, CON_C2, DET_E5 with the calibration deltas locked in during this sprint. (Previously logged in CHANGES_LOG as TODO.)

**Total estimate: ~14 hours (~2 working days).**

---

## Open questions for Marat

1. **AD interception model** — pure halving (calibrated) OR halving + 5% interception chance per AD? Designed had full interception; calibrated has none.
2. **Nuclear missile strikes (L1/L2)** — preserve designed warhead models now OR defer?
3. **Naval combat** — designed `resolve_naval_combat` uses zone-based; our calibrated doesn't touch it yet. Upgrade to unit-level at same time or defer?
4. **Economic/political tick cadence** — run every round (makes for dynamic state) or let agents drive mutations via actions only?
5. **Sprint timing** — start Phase 1 immediately or sleep on the audit first?

---

## End of audit
