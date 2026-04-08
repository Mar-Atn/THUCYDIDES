# Calibration Register — Known Issues & Tuning Items

**Created:** 2026-04-08 | **Updated:** 2026-04-08
**Purpose:** Track calibration findings from engine testing. Items here are NOT bugs — the engine works correctly. These are parameter tuning questions.

---

## ACTIVE ITEMS

### CAL-1: R0→R1 GDP drop for Columbia (-4%)
**Finding:** Columbia GDP drops 280→268.7 (-4%) in first round with no new actions.
**Cause:** Starting sanctions (36 records) and tariffs (29 records) now correctly flow through the engine for the first time. The R0 GDP is the "template ideal" without sanctions/tariffs applied. R1 is "reality with starting conditions."
**Decision needed:** Accept R0→R1 as "settling-in round" (recommended), or pre-adjust R0 GDP for starting conditions?
**Recommendation:** Accept. Compare R1→R2+ for real gameplay deltas.

### CAL-2: Budget social spending has no visible stability effect in 1 round
**Finding:** Columbia stability stays at 7 whether social_pct is 0.5, 1.0, or 1.5.
**Cause:** Stability formula coefficient for social spending (+0.05 per 15% above baseline, -0.15 per 15% below) produces sub-integer changes that get rounded. Needs multiple rounds or larger coefficients.
**Treasury effect works correctly:** Austerity saves 4.3 coins, generous costs 4.3 coins.
**Tuning:** Consider increasing social spending stability coefficient from ±0.05/0.15 to ±0.3/0.5, or accumulate fractional stability changes.

### CAL-3: Cathay GDP drops 8.15% in tariff war (vs Columbia 4%)
**Finding:** Asymmetric tariff impact — Cathay hit harder than Columbia.
**Cause:** Columbia→Cathay tariffs are L3 (47.5%), Cathay→Columbia are L2 (30%). Plus Cathay is more trade-dependent.
**Status:** Likely correct per design (asymmetric tariff war). Monitor over multiple rounds.

### CAL-4: Caribe hyperinflation (0→61% in 1 round)
**Finding:** Caribe inflation jumps from 0% to 61.3% in one round.
**Cause:** L3 sanctions + full energy blockade on a tiny economy (GDP=2.0). All supply channels cut.
**Status:** Dramatic but arguably plausible for a fully blockaded economy. Monitor — if it hits 500% cap too fast, dampen the curve.

### CAL-5: Oil revenue is part of total treasury gain (NOT a bug)
**Finding:** Initially appeared that oil revenue was 2-3x expected. Actually, the test was comparing total treasury delta (GDP tax + oil + other) against oil formula alone.
**Cause:** Solaria oil revenue = $85 × 10mbpd × 0.009 = 7.65 coins (correct). Total treasury gain = 22.44 (includes GDP-based tax revenue).
**Status:** RESOLVED — not an issue.

### CAL-6: Budget columns were missing from DB (FIXED)
**Finding:** budget_social_pct, budget_military_coins, budget_tech_coins columns didn't exist in country_states_per_round.
**Cause:** Never created. resolve_round had no code to write budget decisions to state tables.
**Fix applied:** Columns added, resolve_round injects budget into country_state dict before snapshot write.
**Status:** FIXED 2026-04-08.

---

## MONITORING (not yet issues, watch over multiple rounds)

- War economy: Sarmatia/Ruthenia GDP should decline over 3-4 rounds of war
- Nuclear test stability impact: global -0.2 per test — should accumulate
- Formosa semiconductor cascade: not yet tested (needs blockade scenario)
- OPEC production decisions: columns added, not yet tested with real OPEC members
- Debt burden accumulation: countries in deficit should see growing debt ratio

---

## RESOLVED

- CAL-5: Oil revenue (not a bug — test error)
- CAL-6: Budget columns missing (fixed)
