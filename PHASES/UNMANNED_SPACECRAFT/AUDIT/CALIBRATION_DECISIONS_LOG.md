# Calibration Decisions Log

**Purpose:** Track all calibration fixes and formula decisions made during Phase 1 testing. Apply to SEED/DET docs in a single reconciliation pass after all tests complete.

---

## CD-1: Sanctions/Tariffs — Choke Model (2026-04-09)

**Design intent (SEED):** Sanctions and tariffs act as a CHOKE — one-time GDP level adjustment when imposed, stable when unchanged, recovery when lifted.

**Implementation:** `GDP_new = GDP_after_growth × (new_coeff / old_coeff)`
- When imposed: old=1.0, new=0.95 → ratio=0.95 → one-time -5% shock
- Unchanged next round: old=0.95, new=0.95 → ratio=1.0 → no further drag
- When lifted: old=0.95, new=1.0 → ratio=1.05 → recovery bounce

**Bugs fixed:**
1. Coefficients not in `_COUNTRY_COLS` → dropped from snapshot → recomputed from scratch each round → repeated full shock
2. `resolve_round._load_country_state` loaded current round (empty) instead of falling back to previous → coefficients lost
3. Market share calculation used current GDP (drifting) → fixed to use `_starting_gdp` (R0, stable)

**Verified result (Columbia, L3 tariff war with Cathay):**
- R1: -4.08% (shock), R2: +1.21% (stable), R3: +1.04%, R4: +5.69% (lifted), R5: +1.06% (normal)

**Docs to update:** SEED_D8 §sanctions, CARD_FORMULAS §A.2/A.3, CARD_ARCHITECTURE §engine contracts

---

## CD-2: Social Spending → Stability — Linear Model (2026-04-09)

**Old formula:** Stepped (+0.05 full funding, -0.15 moderate cut, -0.30 severe austerity). Too small for integer stability — always rounded to 0 effect.

**New formula:** Linear: `delta = (social_pct - 1.0) × 100 / 25`
- 50% cut (social_pct=0.5): stability -2.0 per round
- Normal (1.0): 0
- 50% increase (1.5): stability +2.0 per round

**Bug fixed:** `round_tick` passed `social_spending_baseline` for BOTH ratio and baseline to `calc_stability`, so the formula always saw social_pct=1.0 regardless of budget decision.

**Verified result (Teutonia, 2 rounds):**
- Austerity 50%: stability 7→6→5, support 45→43→41
- Normal: stability 7→7→7
- Generous 150%: stability 7→9→9, support preserved

**Docs to update:** CARD_FORMULAS §B.1 (social spending), SEED_D8 stability formula

---

## CD-3: Budget Columns Added to DB (2026-04-08)

**Added:** `budget_social_pct`, `budget_military_coins`, `budget_tech_coins`, `opec_production` to `country_states_per_round`

**Wired:** resolve_round injects budget into country_state dict before snapshot write. Engine tick reads from these columns.

**Verified:** Austerity saves ~4.3 coins/round, generous costs ~4.3 coins.

**Docs to update:** DET_B1 schema, CARD_ARCHITECTURE DB section

---

## CD-4: Coefficient Columns Added to DB (2026-04-09)

**Added:** `sanctions_coefficient`, `tariff_coefficient` to `country_states_per_round`

**Purpose:** Persist computed GDP modifiers between rounds so the choke model works (ratio=1.0 when unchanged).

**Docs to update:** DET_B1 schema, CARD_ARCHITECTURE DB section

---

## CD-5: Starting GDP for Coefficient Stability (2026-04-09)

**Change:** `calc_sanctions_coefficient` and `calc_tariff_coefficient` now use `_starting_gdp` (R0 value from countries table) instead of current GDP for market share calculations.

**Why:** Current GDP changes each round → market shares drift → coefficient changes → ratio ≠ 1.0 → persistent drag even when sanctions/tariffs unchanged. Using starting GDP makes the coefficient deterministic.

**Docs to update:** CARD_FORMULAS §A.2/A.3 (note: starting GDP used for coefficient stability)

---

## PENDING (not yet tested/decided)

- Combat damage → GDP impact calibration
- Nuclear test → global stability impact magnitude
- Formosa semiconductor cascade magnitude
- OPEC production → oil price sensitivity
- Election trigger thresholds
- Debt accumulation under deficit spending

---

## COMBAT DISCREPANCIES (found 2026-04-09, from test_calibration_combat.py)

### DISC-1: Missile base hit rate — CARD says 70%, code uses 80%
**CARD_FORMULAS D.5:** "conventional missile: 70% hit"
**Code (combat.py):** uses 80% probability
**Decision needed:** Align to 70% (CARD) or keep 80% (code)?

### DISC-2: Air attacker downed by AD — CARD says 15%, code doesn't implement
**CARD_FORMULAS D.2:** "15% downed by AD per strike"
**Code:** No attacker-downed mechanic in resolve_air_strike
**Decision needed:** Implement 15% downed, or defer?

### DISC-3: Naval fleet model — CARD says 1v1, code supports fleet batching
**CARD_ACTIONS 1.5:** "1v1 only, no fleet advantage"
**Code:** Has fleet advantage bonus logic
**Decision needed:** Remove fleet bonus (match CARD) or keep?

### DISC-4: Missile AD interception — CARD says 50% per AD unit, code uses flat 30%
**CARD_FORMULAS D.5:** "AD intercepts missiles at 50% per unit"
**Code:** Uses flat 30% interception rate regardless of AD count
**Decision needed:** Implement per-unit 50% roll, or keep simplified?

---

## POLITICAL CALIBRATION (verified 2026-04-09, 38 tests pass)

- Stability: peaceful democracy holds, war causes -0.08/round, austerity -2/round, generous +2/round ✓
- GDP crash: stability drops (capped -0.30 per round) ✓
- High inflation: stability penalty (capped -0.50 per round) ✓
- Support: war erodes, high stability helps, low stability hurts ✓
- War tiredness: +0.20 defender, +0.15 attacker, +0.10 ally, halved after 3+ rounds, 20% peace decay ✓
- Thresholds: stable/unstable/protest/crisis zones correctly triggered ✓
- Revolution: triggers at stability ≤ 2 AND support < 20% ✓
- Coup: base 15%, modifiers for protest/stability/support, needs 2 plotters ✓
