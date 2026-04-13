# CHECKPOINT: Sanctions Vertical Slice

**Status:** ✅ DONE end-to-end
**Date:** 2026-04-10
**Owner:** Marat + Build Team
**Authoritative contract:** `CONTRACT_SANCTIONS.md` v1.0 (🔒 locked)
**Methodology:** `EVOLVING METHODOLOGY/VERTICAL_SLICE_PATTERN.md` v1.1

This is the durable record of the third completed mandatory-decision vertical slice, and the **first slice that required a real engine rewrite** (vs. budget/tariffs which locked contracts around existing math). The sanctions engine was substantially redesigned with Marat during the slice — simpler, more intuitive, sector-derived per-country ceilings instead of a global constant, signed coverage for evasion support.

---

## 1. Scope

The sanctions slice covers one mandatory end-of-round decision per country:

- **Bilateral sanctions with signed levels** — integer level `∈ [-3, +3]` per target country, set via a sparse `changes.sanctions` dict in a `set_sanctions` (plural) action
- **Positive levels** = active sanctions; **negative levels** = evasion support (buying discounted exports, providing workarounds)
- **Coalition coverage dynamics** — the coalition's total world-GDP share drives effectiveness via a non-linear S-curve with a tipping point at 0.5-0.6
- **Per-country max damage ceiling** from sector mix (tech/services-heavy → ~22% max loss; resource-heavy → ~13% max loss)
- **`no_change`** — a fully legitimate explicit choice

---

## 2. Design decisions locked (per Marat, 2026-04-10)

| # | Gap | Decision | Resolution |
|---|---|---|---|
| **G1** | Floor discrepancy (SEED_D8 said 0.13, CARD_FORMULAS/engine said 0.50) | **Floor = 0.15** canonical — updated in all three locations | Done |
| **G2** | Imposer cost prose in CARD_ACTIONS but no formula | **Dropped for now.** Target-damage-only model. "No negative impact on system actor side." May be added in future calibration pass. | Done |
| **G3** | Temporal adaptation: contradictory specs + dead code + consumer in political.py | **Dropped entirely.** Too complex (countries joining/lifting async), effect marginal. Deleted 4 dead constants, `update_sanctions_rounds()`, `sanctions_rounds` counter, and `political.py`'s `sanctions_rounds > 4 ? 0.70 : 1.0` multiplier. Now stateless recomputation everywhere. | Done |
| **G4** | Anti-sanctions L=−1 in seed data, no mechanism | **Signed coverage.** Levels now `[-3, +3]`. Negative levels contribute negatively to coverage, clamped at 0. Evasion can cancel sanctions but cannot produce a bonus. Cathay → Sarmatia L=−1 row preserved, now canonically valid. | Done |
| **G5** | Sector carve-outs (financial / tech / energy) in seed notes | **No sector logic.** Single integer level. Sectoral nuance captured implicitly via per-country max_damage ceiling. Cleared sectoral text from `sanctions.notes` column (kept column for future use). | Done |
| **G6** | Mirage ±20% routing prose in DET_A1 | **DELETE from DET_A1.** No special role mechanic. Role description narrative-only, no engine effect. | Done |
| **G7** | Missing contract / validator / context / mandatory-decision flow | **Slice work.** Contract + validator + context + persistence + harness + acceptance gate all built. | Done |

## Bonus: formula redesign (agreed during calibration)

Rather than "lock the engine around existing behavior" (the tariff pattern), the sanctions engine was **rewritten** with a simpler, more intuitive model:

**Old formula (removed):**
```
damage = SANCTIONS_MAX_DAMAGE(0.87) × effectiveness × trade_openness × sector_vulnerability
coefficient = max(0.50, 1.0 - damage)
```
Four multiplicative factors, global 0.87 ceiling, hand-wavy sector_vulnerability, redundant trade_openness.

**New formula (canonical v1.0):**
```
max_damage  = tec × 0.25 + svc × 0.25 + ind × 0.125 + res × 0.05    # per-country sector ceiling
coverage    = Σ (actor_gdp_share × level / 3)                         # level ∈ [-3, +3]
coverage    = clamp(coverage, 0, 1)
effectiveness = S_curve(coverage)                                     # new 11-knot steeper curve
damage      = max_damage × effectiveness
coefficient = max(SANCTIONS_FLOOR(0.15), 1.0 - damage)
```

Three-step structure, per-country ceiling from economic structure (no global constant), signed coverage, steeper S-curve with tipping point at 0.5 → 0.6 (+0.20 effectiveness jump).

---

## 3. What changed

### 3.1 Engine (`app/engine/engines/economic.py`)

- **`calc_sanctions_coefficient` rewritten** — new 3-step structure (max_damage × S_curve × coverage), signed levels, no trade_openness, no global MAX_DAMAGE constant
- **`_sanctions_max_damage` new helper** — per-country ceiling from sector mix
- **New constants:** `SANCTIONS_WEIGHT_TEC/SVC/IND/RES` (0.25 / 0.25 / 0.125 / 0.05), `SANCTIONS_FLOOR = 0.15`, new 11-knot `SANCTIONS_S_CURVE`
- **Dead code removed:** `SANCTIONS_MAX_DAMAGE`, `SANCTIONS_ADAPTATION_RATE`, `SANCTIONS_PERMANENT_FRACTION`, `SANCTIONS_DIMINISHING_THRESHOLD`, `SANCTIONS_DIMINISHING_FACTOR`, `update_sanctions_rounds()` function, `sanctions_rounds` counter increment in `process_economy`
- **Related effects untouched:** target revenue cost (`calc_revenue`), oil producer supply effect (`calc_oil_price`) — both remain as calibrated mechanisms

### 3.2 Engine — political layer (`app/engine/engines/political.py`)

- **Removed** the `sanctions_rounds > 4 ? 0.70 : 1.0` stability multiplier (political adaptation) for consistency with the G3 "drop adaptation" decision. Full-strength stability friction now applies whenever `sanctions_level > 0`.
- **`StabilityInput.sanctions_rounds`** field left in place as deprecated default (for backward compat with existing test call sites that still pass it as kwarg).

### 3.3 Engine — code callers cleaned up

All references to the dead columns/counter removed from:
- `engine/engines/round_tick.py` (`_merge_to_engine_dict`)
- `engine/engines/orchestrator.py` (engine dict construction + result persistence)
- `engine/agents/runner.py` (agent runner state init)
- `engine/models/db.py` (Pydantic Country model)

### 3.4 New services

| Service | File | Purpose |
|---|---|---|
| **Validator** | `app/engine/services/sanction_validator.py` | Pure `validate_sanctions_decision(payload) → {valid, errors, warnings, normalized}`. 11 error codes. Signed level range `[-3, +3]`. Collects all errors in one pass. |
| **Context builder** | `app/engine/services/sanction_context.py` | `build_sanction_context(country_code, scenario_code, round_num) → dict`. Read-only. Returns: `economic_state` (incl. `my_max_damage_pct`), `country_roster` (all 20 with current **coalition coverage per target** + per-country max_damage + current GDP loss), `my_sanctions`, `sanctions_on_me`, `decision_rules`, `instruction`. No cognitive blocks — decision-specific only. |

### 3.5 Persistence changes

**Migration:** `sanctions_v1_canonical_schema` (applied 2026-04-10)

- **Added** `country_states_per_round.sanction_decision` JSONB (per-round audit trail, same pattern as `tariff_decision`)
- **Dropped** `countries.sanctions_adaptation_rounds` and `countries.sanctions_recovery_rounds` (dead columns)
- **Cleared** sectoral text from all 36 `sanctions.notes` rows (column kept for future use)
- **Preserved** Cathay → Sarmatia L=−1 row (now canonically valid under signed-coverage model)

**Write path** — `resolve_round.py:set_sanctions` handler:
1. Validate via production `validate_sanctions_decision`
2. On invalid → emit `sanction_rejected` observatory event, skip
3. Always write normalized payload to `country_states_per_round.sanction_decision`
4. On `change` → upsert `sanctions` state table for each `(target, level)` in sparse dict (signed levels stored as-is)
5. On `no_change` → audit only, state table untouched

---

## 4. Test coverage (acceptance evidence)

| Layer | File | Count | Purpose |
|---|---|---|---|
| **L1** | `tests/layer1/test_sanctions_engine.py` | **27** | Engine regression lock: 6 constants, 5 max_damage-by-sector cases, 3 trivial cases, **4 canonical Sarmatia calibration anchors** (clean 1.0, Teutonia alone 0.9960, Columbia alone 0.9714, real DB 0.9490, Cathay flip 0.9028), signed coverage (evasion cancel/no-bonus), level ladder monotonicity, imposer asymmetry, max-possible-damage ceiling, S-curve shape |
| **L1** | `tests/layer1/test_sanction_validator.py` | **44** | All 11 error codes + boundary values + accumulation + normalized output integrity + **signed level support** (all values from −3 to +3 accepted) + negative level evasion test + self-sanction with both signs |
| **L1** | `tests/layer1/test_engines.py` (S-curve subset) | **9** | New 11-knot S-curve exact values + monotonicity + tipping-point jump verification |
| **L2** | `tests/layer2/test_sanction_persistence.py` | **4** | change → state + audit; no_change → audit only; **level=−2 evasion support persists**; invalid → `sanction_rejected` event, no leak |
| **L2** | `tests/layer2/test_sanction_context.py` | **7** | Economic state present; all 20 countries listed; **coalition coverage computed per target**; my_sanctions (positive + negative); sanctions_on_me; decision rules with no_change reminder; **negative level display** |
| **L3** | `tests/layer3/test_skill_mandatory_decisions.py` (D2 portion) | **(updated)** | D2 sanctions prompt rewritten to v1.0 schema with signed levels; persona stub pattern; validates via real production validator |
| **L3** | `tests/layer3/test_sanctions_full_chain_ai.py` | **1** | **THE acceptance gate** — real LLM → validator → DB → resolve_round → run_engine_tick → snapshot, no fixup |

**Totals:** 83 sanctions-specific tests passing. Full L1 suite 295 passing.

---

## 5. Concrete demo (2026-04-10 acceptance gate run)

Columbia R75→R76, real LLM decision:

```json
{
  "action_type": "set_sanctions",
  "country_code": "columbia",
  "round_num": 76,
  "decision": "change",
  "rationale": "Adding maximum sanctions against Cathay to contain strategic rival while maintaining wartime sanctions on Persia. Coalition building essential for effectiveness.",
  "changes": { "sanctions": { "cathay": 3 } }
}
```

**Persistence:**
- `sanction_decision` JSONB byte-for-byte matches normalized AI output ✅
- `sanctions` state table: `(columbia → cathay)` upserted to level 3 ✅

**Engine tick result:**
- Cathay's `sanctions_coefficient` moved from 1.0 → **0.9639** (one-time GDP shock of **−3.61%**)
- Engine computed per-country max_damage for Cathay (tec13 + svc30 + ind52 + res5 → 0.175 ceiling)
- Coverage contribution from Columbia at L3: `0.356 × 1.0 = 0.356`
- S-curve(0.356) ≈ 0.206 effectiveness
- damage = 0.175 × 0.206 = 0.0361 (matches the 3.61% observed)

The canonical formula working in production. The strategic dynamic (L3 on a big target from a big sanctioner hurts ~3-4%) is legibly present.

---

## 6. Canonical calibration anchors (Sarmatia, locked in L1 tests)

| Scenario | Coverage | S-curve effectiveness | Coefficient | GDP loss |
|---|---|---|---|---|
| Clean world | 0.000 | 0.000 | 1.0000 | 0.00% |
| Teutonia alone L3 | 0.057 | 0.029 | 0.9960 | 0.40% |
| Columbia alone L3 | 0.357 | 0.206 | 0.9714 | 2.86% |
| **Real DB starting** (12 actors incl. Cathay L−1 evasion) | 0.509 | 0.367 | **0.9490** | **5.10%** |
| Starting + Cathay flips L−1 → L+2 | 0.751 | 0.701 | 0.9028 | 9.72% |

**The pivotal observation:** Cathay alone can move Sarmatia's GDP loss from **5.10% → 9.72%** by switching from evasion support to sanctioning — nearly doubling the damage. This captures the "will China join?" dynamic as the single most strategically pivotal decision in the sim.

---

## 7. Known non-gap observations

- **Political engine adaptation also removed.** The `sanctions_rounds > 4 ? 0.70 : 1.0` multiplier in `political.py` (a separate diminishing-returns mechanism for political stability friction) was dropped for consistency with G3. Full-strength stability friction now applies whenever sanctions are active.
- **`StabilityInput.sanctions_rounds` field left as deprecated default.** Removed from engine logic but kept as a dataclass field with default 0 so existing test call sites don't break. Can be cleaned up in a future pass.
- **Per-target revenue cost + oil producer supply effect unchanged.** These are separate, already-calibrated mechanisms that remain. They stack with the GDP coefficient hit.
- **No imposer cost, no evasion benefit.** Per Marat's 2026-04-10 directive. Target-damage-only model. May be revisited in future calibration.
- **`sanctions.notes` column preserved** (cleared but kept) for future use — possibly for structured sector carve-outs or diplomatic narrative metadata.

---

## 8. Pointers (copy-pasteable)

```
# Contract
PHASES/UNMANNED_SPACECRAFT/CONTRACT_SANCTIONS.md        🔒 v1.0

# Engine
app/engine/engines/economic.py                         calc_sanctions_coefficient,
                                                       _sanctions_max_damage,
                                                       SANCTIONS_WEIGHT_*, SANCTIONS_FLOOR,
                                                       SANCTIONS_S_CURVE
app/engine/engines/political.py                        sanctions friction (adaptation removed)
app/engine/engines/round_tick.py                       _merge_to_engine_dict (cleaned)
app/engine/engines/orchestrator.py                     engine dict (cleaned)
app/engine/agents/runner.py                            agent runner state (cleaned)
app/engine/models/db.py                                Country Pydantic model (cleaned)

# Persistence handler
app/engine/round_engine/resolve_round.py               set_sanctions handler (v1.0 block)

# Services
app/engine/services/sanction_validator.py              validate_sanctions_decision + CANONICAL_COUNTRIES
app/engine/services/sanction_context.py                build_sanction_context

# Tests
app/tests/layer1/test_sanctions_engine.py              27 tests (regression lock + calibration anchors)
app/tests/layer1/test_sanction_validator.py            44 tests (validator)
app/tests/layer1/test_engines.py                       S-curve tests (updated for new 11-knot curve)
app/tests/layer2/test_sanction_persistence.py          4 tests
app/tests/layer2/test_sanction_context.py              7 tests
app/tests/layer3/test_skill_mandatory_decisions.py     D2 sanctions portion (updated to v1.0 schema)
app/tests/layer3/test_sanctions_full_chain_ai.py       acceptance gate (1 test)

# Docs reconciled
2 SEED/D_ENGINES/SEED_D8_ENGINE_FORMULAS_v1.md         §Sanctions Hit rewritten, Pass 2 line struck
3 DETAILED DESIGN/DET_C1_SYSTEM_CONTRACTS.md           §MandatoryInputs sanctions schema updated
PHASES/UNMANNED_SPACECRAFT/CARD_FORMULAS.md            A.2 rewritten with new formula + constants
PHASES/UNMANNED_SPACECRAFT/CARD_ACTIONS.md             2.3 rewritten with set_sanctions + signed levels

# DB migration
sanctions_v1_canonical_schema                          Applied 2026-04-10 to Supabase project lukcymegoldprbovglmn
```

---

## 9. Next

Per Marat's 2026-04-10 strategy directive, the slice order from here:

```
✅ Budget       DONE 2026-04-10
✅ Tariffs      DONE 2026-04-10
✅ Sanctions    DONE 2026-04-10  ← this slice
   Oil (OPEC)   NEXT
   Military Actions (standard / blockade / nuclear)
   Military Movements
   Nuclear Decisions
   Transactions
   Agreements
   Other Actions (fire/reassign / assassination / arrest / propaganda / sabotage / private investments)
```

After all slices ship → reconcile up to CONCEPT and SEED in a single coherent pass. Then → AI Participant Module v1.0 on top of the complete substrate.

The **OPEC slice** is the likely simplest remaining mandatory decision — it's a single-value choice per OPEC member (min/low/normal/high/max), no bilateral matrix, no signed levels. Should be the smallest slice of the four mandatory decisions.
