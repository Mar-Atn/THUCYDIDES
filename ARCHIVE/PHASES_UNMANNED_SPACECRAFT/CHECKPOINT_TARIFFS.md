# CHECKPOINT: Tariff Vertical Slice

**Status:** ✅ DONE end-to-end
**Date:** 2026-04-10
**Owner:** Marat + Build Team
**Authoritative contract:** `CONTRACT_TARIFFS.md` v1.0 (🔒 locked)
**Methodology:** `EVOLVING METHODOLOGY/VERTICAL_SLICE_PATTERN.md` v1.1 (with the new decision-specific-only boundary)

This is the durable record of the second completed mandatory-decision vertical slice. It is also the **first slice shipped under the corrected boundary** — the system supplies decision-specific context only; cognitive blocks belong to the AI Participant Module (future). Tests emulate the cognitive layer with a persona stub in the test harness.

---

## 1. Scope

The tariff slice covers one mandatory end-of-round decision per country:

- **Bilateral tariffs** — integer level `0..3` per target country, set via a sparse `changes.tariffs` dict in a `set_tariffs` (plural) action
- **`no_change`** — a fully legitimate explicit choice (tariffs are a possibility, not an obligation)

The engine math was **NOT changed** — this slice locks a contract around `calc_tariff_coefficient` behavior that already worked. The work is in the layers around the engine: contract, validator, decision-specific context, persistence audit trail, AI skill harness, acceptance gate.

---

## 2. What changed

### 2.1 Design decisions locked (per Marat, 2026-04-10)

| # | Decision | Rationale |
|---|---|---|
| 1 | Action name is `set_tariffs` (plural) | One submission carries the country's full intent. Distinct from legacy singular `set_tariff` which keeps working in parallel during migration. |
| 2 | Sparse `changes.tariffs = {target: level}` | Only name targets you want to change. Untouched targets carry forward via the `tariffs` state table. Matches how policymakers deliberate. |
| 3 | Level 0 means lift (no separate action) | Uniform schema. Level=0 upserts the row with level=0; engine treats as no tariff. |
| 4 | Self-tariff and unknown-target are hard rejections | Validator errors `SELF_TARIFF`, `UNKNOWN_TARGET`. No warnings, no silent drops. |
| 5 | Rationale ≥30 chars required for BOTH change and no_change | Forces explicit reasoning. No silent defaults. |
| 6 | `no_change` must OMIT the `changes` field entirely | Structurally distinct from `change`. `{"decision": "no_change", "changes": {...}}` is `UNEXPECTED_CHANGES`. |
| 7 | Empty `changes.tariffs = {}` on a change is invalid | `EMPTY_CHANGES`. If nothing to change, use `no_change`. |
| 8 | No forecast/dry-run in the context package | Tariff consequences are emergent (retaliation, contagion). Learning by doing or future intelligence skill — not a misleadingly precise one-round dry-run. |
| 9 | Decision-specific context only (no cognitive blocks) | **Boundary rule for all slices going forward.** System serves decision data; AI Participant Module (future) provides cognitive state. Tests use persona stub as fixture only. |
| 10 | Engine math is UNCHANGED | The slice locks a contract around existing `calc_tariff_coefficient` behavior. Constants (TARIFF_K=0.54, TARIFF_IMPOSER_FRACTION=0.5, TARIFF_REVENUE_RATE=0.075, TARIFF_INFLATION_RATE=12.5) pinned as regression guards in L1 tests. Any future change requires an explicit ticket. |

### 2.2 Engine changes

**None.** `calc_tariff_coefficient()` in `app/engine/engines/economic.py` (line 904) is untouched. The L1 regression test `test_tariff_engine.py` locks the constants and canonical examples so any future change breaks loudly.

### 2.3 New services

| Service | File | Purpose |
|---|---|---|
| **Validator** | `app/engine/services/tariff_validator.py` | Pure `validate_tariffs_decision(payload) → {valid, errors, warnings, normalized}`. 11 error codes per CONTRACT §4. Collects ALL errors in one pass. Used by: AI skill harness, `resolve_round` handler, test fixtures, human UI (future). |
| **Context builder** | `app/engine/services/tariff_context.py` | `build_tariff_context(country_code, scenario_code, round_num) → dict`. Read-only, no writes. Returns: `economic_state`, `country_roster` (all 20 countries with trade_rank from `derive_trade_weights`), `my_tariffs`, `tariffs_on_me`, `decision_rules`, `instruction`. **No cognitive blocks** — this is the first slice shipped under the new boundary. |

### 2.4 Persistence changes

**Migration:** `add_tariff_decision_country_states_per_round` (applied 2026-04-10)

Added one JSONB column to `country_states_per_round`:

```sql
tariff_decision jsonb
```

This is the **per-round audit record** of the decision submitted (including `no_change` with rationale). The **canonical world state** lives in the existing `tariffs` state table and is unchanged.

**Write path** — `resolve_round.py` `set_tariffs` handler:
1. Run `validate_tariffs_decision(payload)`
2. On invalid → emit `tariff_rejected` observatory event, skip
3. Always write the normalized payload to `country_states_per_round.tariff_decision`
4. On `change` → upsert `tariffs` state table for each `(target, level)` in the sparse dict. Untouched targets carry forward by inaction.
5. On `no_change` → audit only, state table untouched

**Read path** — unchanged. The engine reads `tariffs` state table via the existing `_load_state_from_tables` in `round_tick.py`. **No round_tick changes in this slice.**

---

## 3. Test coverage (acceptance evidence)

| Layer | File | Count | Purpose |
|---|---|---|---|
| **L1** | `tests/layer1/test_tariff_validator.py` | 41 | All 11 error codes + boundary values + accumulation (multi-error in one pass) + normalized output integrity |
| **L1** | `tests/layer1/test_tariff_engine.py` | 22 | Engine regression lock — constants pinned, canonical examples (Columbia→Cathay L3), level scaling monotonicity, asymmetry (imposer vs target), floor at 0.80, additive multi-target |
| **L2** | `tests/layer2/test_tariff_persistence.py` | 4 | Change → state table + audit; no_change → audit only, state untouched; level=0 lifts; invalid → `tariff_rejected` event, no leak into state |
| **L2** | `tests/layer2/test_tariff_context.py` | 6 | Economic state present; all 20 countries in roster; my_tariffs + tariffs_on_me from both directions; decision_rules with no_change reminder; trade_rank 1..19 ordering |
| **L3** | `tests/layer3/test_skill_mandatory_decisions.py` (D3 portion) | 10 | Real LLM decisions from 10 leaders, all validated by production `validate_tariffs_decision()` |
| **L3** | `tests/layer3/test_tariffs_full_chain_ai.py` | 1 | **THE acceptance gate** — real AI decision → validator → DB → resolve_round → run_engine_tick → snapshot, no fixup |

**Totals:** 84 tests green (63 L1+L2 + 11 L3). Engine math unchanged. All persisted under the new boundary.

---

## 4. Concrete demo (2026-04-10 acceptance gate run)

**Columbia, R85→R86, real LLM decision:**

```json
{
  "action_type": "set_tariffs",
  "country_code": "columbia",
  "round_num": 86,
  "decision": "change",
  "rationale": "Escalating pressure on Persia during active war.",
  "changes": {
    "tariffs": { "persia": 2 }
  }
}
```

**Persistence result:**
- `country_states_per_round.tariff_decision` JSONB byte-for-byte matches normalized AI output
- `tariffs` state table: `(columbia, persia).level` upserted to `2`
- `country_states_per_round.tariff_coefficient` (columbia R86): 1.0 → 0.997538 (direction matches — small additional self-damage from the new L2 tariff)
- Engine tick completed `success: true`

---

## 5. The boundary in practice (first slice under the new rule)

This slice is the first concrete demonstration of the "decision-specific only" boundary from VERTICAL_SLICE_PATTERN.md v1.1. Specifics:

### What `tariff_context.py` provides

- `economic_state` — Columbia's own GDP/treasury/inflation/sectors/trade_balance/oil/stability
- `country_roster` — all 20 countries (code, GDP, sector profile, relationship status, trade rank 1..19)
- `my_tariffs` — Columbia's outgoing bilateral tariffs from the `tariffs` state table
- `tariffs_on_me` — incoming bilateral tariffs from the `tariffs` state table
- `decision_rules` — text describing levels, sparse semantics, no_change reminder
- `instruction` — what to decide + schema pointer

### What `tariff_context.py` does NOT provide

- **No `block1_rules`** — the AI Participant Module will supply world-mechanics rules when it's built
- **No `block2_identity`** — character, personality, authority constraints
- **No `block3_memory`** — self-curated round history, relationship deltas, promises
- **No `block4_goals`** — strategic objectives, round intentions, coalition obligations

### How tests emulate the cognitive layer

The D3 skill harness in `test_skill_mandatory_decisions.py` uses `LeaderScenario` dataclasses with personality / objectives fields stapled to the LLM system prompt. These are **test fixtures**, not contract artifacts. When the AI Participant Module v1.0 lands, the test stub is replaced by `agent.get_cognitive_state()` and `tariff_context.py` is unchanged.

The acceptance gate in `test_tariffs_full_chain_ai.py` follows the same pattern — the Columbia scenario stub provides enough cognitive context to make the LLM produce a sensible decision, and the assertion target is the **DB state after the chain runs**, not the LLM's reasoning quality.

---

## 6. Known non-gap observations

- **Small coefficient deltas on low-level tariffs.** A single L2 tariff from Columbia onto Persia moved Columbia's coefficient by only ~0.0025. That's correct behavior — imposer self-damage at L2 on a modest target is ≈ 0.12 × 0.43 × 0.67 × 0.54 × 0.5 ≈ 0.009, further reduced by the starting GDP normalization. Tests use relative assertions, not absolute thresholds, so this is fine.
- **The legacy singular `set_tariff` and `lift_tariff` actions still work.** Intentional. Migration-friendly. New code should use `set_tariffs` (plural).
- **The notes field on the `tariffs` table is text-free, written by `resolve_round`** ("set_tariffs by X in round Y"). Not structured, but sufficient for the context builder's "imposed since R{n}" display.

---

## 7. Pointers (copy-pasteable)

```
# Contract
PHASES/UNMANNED_SPACECRAFT/CONTRACT_TARIFFS.md          🔒 v1.0

# Engine (UNCHANGED — regression-locked by L1 tests)
app/engine/engines/economic.py                         calc_tariff_coefficient, _trade_exposure,
                                                       TARIFF_K, TARIFF_IMPOSER_FRACTION,
                                                       TARIFF_REVENUE_RATE, TARIFF_INFLATION_RATE

# Persistence handler
app/engine/round_engine/resolve_round.py               set_tariffs handler (v1.0 block)

# Services
app/engine/services/tariff_validator.py                validate_tariffs_decision + CANONICAL_COUNTRIES
app/engine/services/tariff_context.py                  build_tariff_context (decision-specific only)

# Tests
app/tests/layer1/test_tariff_validator.py              41 tests
app/tests/layer1/test_tariff_engine.py                 22 tests (regression lock)
app/tests/layer2/test_tariff_persistence.py            4 tests
app/tests/layer2/test_tariff_context.py                6 tests
app/tests/layer3/test_skill_mandatory_decisions.py     D3 portion, 10 LLM decisions
app/tests/layer3/test_tariffs_full_chain_ai.py         acceptance gate

# Methodology
EVOLVING METHODOLOGY/VERTICAL_SLICE_PATTERN.md         v1.1 — decision-specific-only boundary
```

---

## 8. Next

Per Marat's 2026-04-10 strategy directive, the slice order from here:

```
✅ Budget        DONE (2026-04-10)
✅ Tariffs       DONE (2026-04-10)  ← this slice
   Sanctions     NEXT
   Oil (OPEC)
   Military Actions (standard / blockade / nuclear)
   Military Movements
   Nuclear Decisions
   Transactions
   Agreements
   Other Actions (fire/reassign / assassination / arrest / propaganda / sabotage / private investments)
```

After all slices ship → reconcile up to CONCEPT and SEED in a single coherent pass. Then → AI Participant Module v1.0 on top of the complete substrate.

The sanctions slice will follow the **exact same pattern** as tariffs (bilateral state-table-backed, sparse changes, level scale, no forecast, decision-specific context only, persona stub for tests). Most of the tariff code is directly reusable as a scaffold.
