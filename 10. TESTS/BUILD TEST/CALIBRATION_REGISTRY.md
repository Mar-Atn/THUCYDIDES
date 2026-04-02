# Calibration Run Registry

| Run | Date | Fixes Applied | Key Result | Score |
|-----|------|--------------|------------|-------|
| #001 | 2026-04-01 | Baseline (first run) | Everything broken. Sarmatia -97%, Columbia +228%, stability collapse | 1/9 |
| #002 | 2026-04-01 | Sanctions ÷10, growth ÷2 (6mo), social key fix, Persia growth 0.5 | Sarmatia still -91% (budget deficit, not sanctions). Oil fixed. | 3/9 |
| #003 | 2026-04-01 | SIPRI-based maintenance recalibration (all 20 countries) | Sarmatia survives (+4%). But universal stability drain persists. | 4/9 |
| #004 | 2026-04-01 | GDP base rate fix (use structural, not result), social model redesign (flat coins) | Stability improved but still drifting. Columbia still +36%. | 5/9 |
| #005 | 2026-04-01 | Persistence bug fix (orchestrator line 194), social = % of revenue, momentum 10% decay | Stability much better. Columbia +35% unchanged (persistence bug was the cause). | 6/9 |
| #006 | 2026-04-01 | GDP-scaled tech/momentum dampener, social ratio units fix | **Stability SOLVED** (19/20). Columbia +24%, Bharata +5% (under). | ~7/9 |
| #007 | 2026-04-01 | Maturity-aware GDP dampener (structural rate / 6.0) | Mature economies better. Emerging still under-growing. | ~7/9 |
| #008 | 2026-04-01 | Shock absorption, tariff cap, structural/cyclical separation | **Stability 19/20. GDP 8/20.** Mature W. Europe correct. Emerging under-grow. | ~7/9 |

## Key Lessons Learned
1. Most problems were DATA, not formulas (maintenance costs, starting GDP ratios)
2. Budget balance is THE key to stable steady state
3. Feedback loops amplify small errors exponentially
4. GDP growth rate feedback loop was the single worst bug (result overwrote base)
5. Social spending units mismatch caused universal stability drain
6. Caps are symptoms of broken fundamentals — fix the model, not the symptoms
7. Emerging economies need different treatment than mature ones (maturity factor)
8. Formula-based GDP/stability is brittle — every fix creates side effects

## Next Step
Approach 1: Supervised parameter-by-parameter review with Marat before further calibration.
