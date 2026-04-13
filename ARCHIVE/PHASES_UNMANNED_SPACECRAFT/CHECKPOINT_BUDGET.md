# CHECKPOINT: Budget Vertical Slice

**Status:** ✅ DONE end-to-end
**Date:** 2026-04-10
**Owner:** Marat + Build Team
**Authoritative contract:** `CONTRACT_BUDGET.md` v1.1 (🔒 locked)
**Pattern:** `EVOLVING METHODOLOGY/VERTICAL_SLICE_PATTERN.md` (the 7-step template derived from this slice)

This document is the durable record of the first completed mandatory-decision vertical slice in the Unmanned Spacecraft phase. It captures WHAT changed, WHY, and WHERE to find the code, so future work on sanctions / tariffs / OPEC can reproduce the same shape without reinvention, and so any future reconciliation can rebuild this slice's intent from a single page.

---

## 1. Scope

The budget slice covers one mandatory end-of-round decision per country:

- **Social spending** — continuous slider `social_pct ∈ [0.5, 1.5]` on top of the country's `social_baseline × revenue`
- **Production levels** — discrete integer level `∈ {0, 1, 2, 3}` for each of 5 branches: `ground`, `naval`, `tactical_air`, `strategic_missile`, `air_defense`
- **Research coins** — absolute integer coin allocation for `nuclear` and `ai` R&D

That is the entire decision surface. The engine computes everything else (revenue, maintenance, coin conversion, unit production, R&D progress, stability/support side-effects, deficit cascade, inflation).

---

## 2. What changed

### 2.1 Design decisions locked (per Marat, 2026-04-10)

| # | Decision | Rationale |
|---|---|---|
| 1 | Remove all percentage caps (40% military, 30% R&D) | Caps were invented during implementation, not in SEED_D8. They scale budgets silently and confuse participants. Over-spending now feeds the deficit cascade directly. |
| 2 | Production is level-based (0/1/2/3), not coin-based | Matches how real policymakers think ("build at maximum pace"), not accountants ("12.37 coins"). Level × capacity × branch_unit_cost → coins. |
| 3 | Level 3 is non-linear: 4× cost for 3× output | "Emergency gear" — deliberately worthwhile only in crisis. Models overtime, backup suppliers, defects. |
| 4 | Social spending is continuous (slider, not tier) | Linear formulas on deviation from 1.0: `stability_delta = (social_pct - 1.0) × 4`, `support_delta = (social_pct - 1.0) × 6`. |
| 5 | Research is absolute coins, not levels | R&D is a funding decision ("give the nuclear program X coins"), not a pacing decision. |
| 6 | `strategic_missile` + `air_defense` in schema but capacity 0 for all countries | Forward-compatible. Raising capacities later is a pure data change. |
| 7 | `no_change` must explicitly omit the `changes` field | Strict contract — decisions are explicit choices, null is ambiguous. |
| 8 | Validator returns ALL errors in one pass | Fail-fast validators waste participants' time. One report → fix everything. |
| 9 | Context package includes a dry-run "no-change forecast" | Participants see "what happens if I do nothing" before deciding. Single source of truth (same engine code). |
| 10 | Rationale required for both `change` AND `no_change` (≥30 chars) | Forces explicit reasoning. No silent defaults. |

### 2.2 Engine changes (`app/engine/engines/economic.py`)

- **`calc_budget_execution`** rewritten for v1.1 schema. Returns `(BudgetResult, production_result)`. Cap enforcement removed. Consumes `social_pct`, per-branch `production` dict, and `research` dict directly.
- **`_compute_production_from_levels`** new helper: expands a `{branch: level}` dict into `{branch: {coins, units, level}}` using `PRODUCTION_COST_MULT`, `PRODUCTION_OUTPUT_MULT`, and `BRANCH_UNIT_COST` constants.
- **`calc_military_production`** signature changed: iterates all 5 branches, credits `country.military[branch]` with pre-computed units, handles Cathay strategic-missile auto-growth and naval auto-production.
- **`calc_tech_advancement`** consumes `_research_nuclear_coins` and `_research_ai_coins` stashed on the economic state by `calc_budget_execution` (no `tech_rd` actions dict needed for v1.1 paths).
- **New constants:**
  ```
  PRODUCTION_COST_MULT   = {0: 0.0, 1: 1.0, 2: 2.0, 3: 4.0}
  PRODUCTION_OUTPUT_MULT = {0: 0.0, 1: 1.0, 2: 2.0, 3: 3.0}
  BRANCH_UNIT_COST       = {ground: 3, naval: 6, tactical_air: 5, strategic_missile: 8, air_defense: 4}
  BUDGET_PRODUCTION_BRANCHES = (ground, naval, tactical_air, strategic_missile, air_defense)
  SOCIAL_STABILITY_MULT = 4.0
  SOCIAL_SUPPORT_MULT   = 6.0
  RD_MULTIPLIER         = 0.8
  ```
- **`BudgetResult`** dataclass extended with `military_spending`, `research_spending`, `coins_by_branch`, `stability_delta`, `political_support_delta`.

### 2.3 New services

| Service | File | Purpose |
|---|---|---|
| **Validator** | `app/engine/services/budget_validator.py` | Pure function `validate_budget_decision(payload) → {valid, errors, warnings, normalized}`. 10 error codes per CONTRACT §4. Accumulates ALL errors in one pass. Used by: AI skill harness, human UI (future), test fixtures. |
| **Context builder + dry-run** | `app/engine/services/budget_context.py` | `build_budget_context(country_code, scenario_code, round_num) → dict` (pure, read-only). `dry_run_budget(..., budget_override=None) → dict` (deep-copies engine dict, runs full chain, captures deltas, discards). The "what happens if you don't change anything" forecast comes from the same code that runs the real engine — single source of truth. |

### 2.4 Persistence changes

- **`resolve_round.py`**: `set_budget` handler runs the validator and writes `budget_social_pct`, `budget_production` (JSONB), `budget_research` (JSONB) columns on `country_states_per_round`. Invalid decisions emit `budget_rejected` observatory events. `no_change` falls through to the previous round's values via `_load_country_state`.
- **`round_tick.py`**: loads the three budget columns into the v1.1 dict shape before calling `process_economy`. Write-back payload extended to include all persistable engine outputs (see §2.5).

### 2.5 Database migration — closing two known gaps

**Migration:** `add_mil_columns_country_states_per_round` (applied 2026-04-10 to Supabase project `lukcymegoldprbovglmn`)

Added five integer columns to `country_states_per_round`:

```
mil_ground             integer
mil_naval              integer
mil_tactical_air       integer
mil_strategic_missiles integer   -- plural, matches countries table convention
mil_air_defense        integer
```

R0 snapshots backfilled from the structural `countries` table.

**What this fixed:**

- **Gap A (units not persisted).** Before: `round_tick` credited `country.military[branch]` in memory but never wrote it back; units evaporated every round, and `_merge_to_engine_dict` re-loaded structural defaults, silently wiping any buildup or combat losses. After: units are loaded from the snapshot first (falling back to structural only when NULL), and written back at the end of every tick.
- **Gap B (R&D progress truncated).** Before: `nuclear_rd_progress` and `ai_rd_progress` were `numeric` in the DB but loaded via `int(...)` in `_merge_to_engine_dict`, and never written back anyway. After: loaded as float, written back with 6-decimal precision. Multi-round R&D progress now accumulates correctly.

Both gaps now have hard DB-backed assertions in `test_budget_e2e.py`.

---

## 3. Test coverage (acceptance evidence)

| Layer | File | Count | Purpose |
|---|---|---|---|
| **L1** | `tests/layer1/test_budget_engine.py` | 16 | Pure formula tests — level expansion, social slider, research progress, deficit cascade, 5-branch iteration, contract §8 example replication |
| **L1** | `tests/layer1/test_budget_validator.py` | 36 | Every validation rule in CONTRACT §4 — all 10 error codes, boundary values, payload shape variants |
| **L2** | `tests/layer2/test_budget_persistence.py` | 3 | Decision → DB round-trip, `no_change` carry-forward, invalid rejection |
| **L2** | `tests/layer2/test_budget_context.py` | 8 | Context builder read path, revenue forecast, mandatory costs, dry-run with and without override, deficit warning |
| **L2** | `tests/layer2/test_budget_e2e.py` | 10 | Full chain: scripted decision → resolve → engine → snapshot. Includes the acceptance gate `test_full_chain_values_match` that asserts every persisted value against a hand-computed expected |
| **L3** | `tests/layer3/test_skill_mandatory_decisions.py` (D1 budget) | 10 (+ 6 offline) | Real LLM decisions for 10 leaders run through the production validator — proves the AI can produce valid v1.1 payloads |
| **L3** | `tests/layer3/test_budget_full_chain_ai.py` | 1 | **THE acceptance gate** — AI decision → validator → DB → engine → snapshot, no human fixup. If this passes, the slice holds. |

**Totals:** 37 tests green at L1+L2, 1 at L3, 16 LLM decisions producing valid budgets on Gemini Flash.

---

## 4. Concrete demo numbers (2026-04-10)

Captured live from the system during `/tmp/budget_demo.py`.

### Columbia — wartime push against Persia

**AI decision:** `social_pct=0.8`, `ground=3, naval=1, tac_air=3`, `ai_coins=4`. Rationale: "War with Persia requires increased military production."

| Metric | Before | After | Δ |
|---|---|---|---|
| Treasury | 30 | 0 | −30 |
| Stability | 7 | 6 | −1 (contract: social_pct=0.8 → Δ=−0.8) |
| Inflation | 3.5% | 25.74% | +22.2 (deficit cascade active) |
| Ground units | 22 | 34 | +12 (requested +15 at L3) |
| Naval units | 11 | 13 | +2 (L1, cap 4) |
| Tac air units | 15 | 24 | +9 (requested +15 at L3) |
| `ai_rd_progress` | 0.000000 | 0.011914 | +0.011914 (contract: +0.01143) |

Columbia over-ordered → deficit cascade drained treasury, printed money (+22 inflation), affordability scaled L3 production down from the full contract calculation. All expected behavior.

### Bharata — peaceful modernization

**AI decision:** `social_pct=1.0`, `ground=2, naval=1, tac_air=2`, `nuclear_coins=3, ai_coins=3`.

| Metric | Before | After | Δ |
|---|---|---|---|
| Treasury | 0 | 0 | 0 |
| Stability | 6 | 6 | 0 (neutral) |
| Ground units | 12 | 18 | +6 |
| Tac air units | 4 | 6 | +2 |
| `nuclear_rd_progress` | 0 | 0.055672 | +0.055672 |
| `ai_rd_progress` | 0 | 0.055672 | +0.055672 |

---

## 5. Known non-gap observations

- **Affordability-proportional production scaling.** When a country's requested military spending exceeds what the deficit cascade can fund, the engine scales branch production proportionally. This is correct behavior but **participants will almost always over-order** unless shown the dry-run forecast from `build_budget_context`. This is the motivation behind Step 5 of the vertical slice.
- **`mil_strategic_missiles`** (plural) in DB vs `strategic_missile` (singular) in engine dict. The `countries` table uses plural and we matched that convention for the snapshot columns. The mapping is handled in `_merge_to_engine_dict` and the write-back payload.
- **Stale columns on `country_states_per_round`.** `budget_military_coins` and `budget_tech_coins` are pre-v1.1 artifacts that are no longer read or written. Dropping them is a separate schema cleanup ticket, not a budget slice concern.

---

## 6. Pointers (copy-pasteable)

```
# Contract
PHASES/UNMANNED_SPACECRAFT/CONTRACT_BUDGET.md          🔒 v1.1

# Engine
app/engine/engines/economic.py                        calc_budget_execution, calc_military_production, calc_tech_advancement
app/engine/engines/round_tick.py                      _merge_to_engine_dict, run_engine_tick write-back
app/engine/round_engine/resolve_round.py              set_budget handler

# Services
app/engine/services/budget_validator.py
app/engine/services/budget_context.py                 build_budget_context, dry_run_budget

# Tests
app/tests/layer1/test_budget_engine.py
app/tests/layer1/test_budget_validator.py
app/tests/layer2/test_budget_persistence.py
app/tests/layer2/test_budget_context.py
app/tests/layer2/test_budget_e2e.py
app/tests/layer3/test_skill_mandatory_decisions.py    D1 budget section (v1.1 prompt + validator)
app/tests/layer3/test_budget_full_chain_ai.py         acceptance gate

# Methodology
EVOLVING METHODOLOGY/VERTICAL_SLICE_PATTERN.md        7-step template
```

---

## 7. Next

This slice is the template for the other three mandatory decisions. Do them in this order, following the same 7 steps:

1. **Sanctions** — bilateral, state-table-backed (`sanctions` table)
2. **Tariffs** — bilateral, state-table-backed (`tariffs` table)
3. **OPEC production** — 4 members, discrete levels (min/low/normal/high/max)

After all four are at the same level of polish, do the cross-domain architectural re-synthesis (unified mandatory-decision base contract, shared validator patterns, cross-cutting SEED_D8 update).
