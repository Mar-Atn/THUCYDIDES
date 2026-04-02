# Calibration Memo — Test Run #003 (Cycle 3)

**Date:** 2026-04-01 | **Analyst:** SUPER EXPERT (autonomous)
**Engine version:** economic.py + political.py (post-Cal-5 / Run #002 fixes)

---

## What I See

**Improved from Run #002:**
- Oil price band $92-113 is realistic (PASS)
- Elections competitive, Ruthenia losing (PASS)
- Revolutions appear R6-R8 in weak states (PASS)
- Sarmatia stagnation +4% is credible (PASS per Marat)
- Cathay +23% is plausible for China-scale growth (PASS)

**Still broken:**
1. **Universal stability drain:** 15/20 countries decline. Gallia (France) 7->2.9, Albion (UK) 7->3.1, Bharata (India) 6->3.4, Columbia 7->3.5. Stable democracies should NOT enter crisis in 4 peaceful years.
2. **Columbia GDP +36%:** 280->381. US growing 36% in 4 years is ~2.5x too high. Real US grows ~2% annual = ~8% over 4 years.
3. **Yamato GDP +19%:** 43->51.3. Real Japan grows ~1% annual = ~4% over 4 years.

**Quiet win:** Teutonia (+5%), Solaria (+8%), Mirage (+8%) are reasonable. The model CAN produce realistic output for some countries. The bugs are systematic, not random.

---

## Root Cause Analysis

### ROOT CAUSE 1: Growth Rate Feedback Loop (Columbia +36%, Yamato +19%)

**The critical bug.** The `gdp_growth_rate` field is being overwritten with the ACTUAL growth result, which then becomes the BASE for the next round. This creates exponential compounding.

**The chain:**

1. `economic.py` line 827: `base_growth = eco["gdp_growth_rate"] / 100.0 / 2.0`
2. The growth calculation adds factors and computes `growth_pct = effective_growth * 100.0` (line 900)
3. `economic.py` line 1646: `c["economic"]["gdp_growth_rate"] = gdp_result.growth_pct` -- **result overwrites input**
4. Next round, line 827 reads this RESULT as the new base, not the structural rate

**Traced math for Columbia, Round 1:**
- `gdp_growth_base` = 1.8 (from seed data)
- `base_growth` = 1.8 / 100 / 2 = 0.009 (0.9% per 6-month round)
- Oil producer bonus at $92: +0.01 * (92-80)/50 = +0.0024
- Tech boost (AI L3): +0.015
- Momentum starts at 0: +0.0
- `effective_growth` ~ 0.009 + 0.0024 + 0.015 = ~0.0264
- `growth_pct` = 2.64%
- GDP: 280 * 1.0264 = 287.4

**Round 2 -- the compounding begins:**
- `gdp_growth_rate` is now 2.64 (the RESULT, not 1.8)
- `base_growth` = 2.64 / 100 / 2 = 0.0132 (already 47% higher than intended)
- Meanwhile momentum is building: gdp_growth > 2 (+0.15), state normal (+0.15), stability > 6 (+0.15) = +0.30/round
- By round 3-4, momentum is 0.6-1.2, adding +0.6-1.2% via momentum_effect
- Each round the growth rate compounds because the RESULT feeds back as BASE

**By round 8:**
- base_growth has compounded from 0.9% to potentially 3-4% per round
- momentum has maxed at 5.0, adding +5% per round
- total growth per round is 4-5%, giving 36% cumulative

**Why Yamato at 19%:** Same feedback loop. Yamato starts at gdp_growth_base=1.0, but has AI L3 (+1.5%), high stability (+momentum). The feedback loop accelerates growth from ~0.5%/round to ~2.5%/round.

**Why Teutonia is OK at +5%:** Teutonia has higher social_baseline (0.30) and maintenance burden, which causes minor budget stress, preventing momentum from maxing. The negative stability feedback partially offsets the growth compounding. It's a coincidental balance, not a correct model.

### ROOT CAUSE 2: Structural Budget Deficit -> Social Spending Shortfall (Universal Stability Drain)

**The stability drain is driven by one formula:** `political.py` lines 296-302.

```python
if social_ratio >= baseline:
    delta += 0.05
elif social_ratio >= baseline - 0.05:
    delta -= 0.05
else:
    shortfall = baseline - social_ratio
    delta -= shortfall * 3  # <-- THIS IS THE KILLER
```

Countries can't fully fund social spending because **mandatory costs (maintenance + 70% of social baseline) consume all revenue**, leaving zero discretionary budget for the remaining 30% of social needs.

**Traced math for Gallia (France), every round:**

| Item | Value |
|------|-------|
| GDP | 34 |
| Tax rate | 0.45 |
| Base revenue | 34 * 0.45 = 15.30 |
| Debt cost | -3.00 |
| Net revenue | ~12.30 |
| Military maintenance | 14 units * 0.50/unit = 7.00 |
| Mandatory social (70%) | 0.35 * 34 * 0.70 = 8.33 |
| **Total mandatory** | **15.33** |
| **Revenue - mandatory** | **12.30 - 15.33 = -3.03 (DEFICIT)** |

Gallia is in deficit BEFORE any discretionary spending. The remaining 30% social pool (3.57) is unfunded. Actual social ratio = 8.33/34 = 0.245 vs baseline 0.35.

**Stability penalty per round:**
- shortfall = 0.35 - 0.245 = 0.105
- raw delta from social = -0.105 * 3 = -0.315
- peaceful dampening (x0.5): -0.158 per round
- positive inertia at stab 7: +0.05
- Net: ~-0.108 per round
- Over 8 rounds: -0.86 from social spending alone
- Add minor inflation friction, no GDP growth bonus (growth ~1%): total drain ~-0.5/round
- 7.0 - 4.0 = 3.0 -- matches observed 7->2.9

**Why this hits almost everyone:** The budget formula splits social spending into 70% mandatory + 30% discretionary (lines 1001-1002 of economic.py). The discretionary 30% can only be funded from revenue AFTER mandatory costs. Most countries' revenue barely covers mandatory costs (maintenance + 70% social). So the actual social ratio always falls short of baseline.

**Countries that escape:** Teutonia (high tax rate 0.38, low maintenance 0.4/unit), Solaria (low tax but huge treasury 20 + oil revenue), Mirage (same -- oil wealth covers gaps).

**Affected countries and their budget gaps:**

| Country | Revenue | Mandatory | Gap | Social Shortfall |
|---------|---------|-----------|-----|------------------|
| Gallia | 12.3 | 15.3 | -3.0 | 0.105 |
| Albion | 8.6 | 11.4 | -2.8 | 0.095 |
| Bharata | 4.6 | 6.9 | -2.3 | 0.065 |
| Columbia | 62.2 | 66.5 | -4.3 | 0.085 |
| Ponte | 5.0 | 5.8 | -0.8 | 0.045 |

The pattern: every country with social_baseline > 0.25 AND military maintenance > ~15% of revenue is structurally underwater.

---

## Fix Options

### Issue 1: Growth Rate Feedback Loop

**Option A (RECOMMENDED): Preserve structural base rate separately**

The `gdp_growth_rate` field conflates two things: the country's structural growth potential (which should persist) and the actual growth achieved (which is a result). Fix by keeping `gdp_growth_base` as the immutable structural rate and using it in the growth formula, while storing the actual growth result in a separate field for display and other formulas.

In `economic.py` line 827, change:
```python
# CURRENT (broken):
base_growth = eco["gdp_growth_rate"] / 100.0 / 2.0

# FIX: Always use structural base rate
base_growth = eco.get("gdp_growth_base", eco["gdp_growth_rate"]) / 100.0 / 2.0
```

And preserve `gdp_growth_base` in the country dict (it's already there from the DB model but gets overwritten when `gdp_growth_rate` is used as the base). In `orchestrator.py` line 75, `gdp_growth_rate` is initialized from `gdp_growth_base`. The fix is to keep `gdp_growth_base` as a separate persistent field that never gets overwritten, and always use it in line 827.

**Impact:** Columbia growth drops from ~36% to ~12-14% (still slightly high due to momentum + tech, but in realistic range). Yamato drops from ~19% to ~6-8%.

**Tradeoff:** Momentum and tech still add growth ON TOP of base rate, which is correct -- these represent real economic dynamics (confidence, innovation). But they no longer compound on themselves.

**Option B: Decay the result toward structural rate**

Instead of using the raw result as next round's base, blend it with the structural rate:
```python
base_growth_rate = eco.get("gdp_growth_base", eco["gdp_growth_rate"])
actual_rate = eco["gdp_growth_rate"]
effective_base = base_growth_rate * 0.7 + actual_rate * 0.3
base_growth = effective_base / 100.0 / 2.0
```

**Tradeoff:** More complex, harder to reason about. Some compounding preserved (which may be desirable for economic realism -- countries that grow tend to keep growing). But the 0.7/0.3 split needs calibration.

**Option C: Hard reset each round**

Simply never overwrite `gdp_growth_rate` with the result:
```python
# Remove line 1646: c["economic"]["gdp_growth_rate"] = gdp_result.growth_pct
# Store result in a display-only field instead:
c["economic"]["actual_growth_pct"] = gdp_result.growth_pct
```

**Tradeoff:** Other formulas (stability, political support, elections) use `gdp_growth_rate` and should see the ACTUAL growth, not the base rate. Those formulas need to be updated to read `actual_growth_pct`.

**My recommendation:** Option A is cleanest. Keep structural `gdp_growth_base` for the growth formula. Keep writing `gdp_growth_rate` for other formulas (stability, elections) to read. The two are different things: "how fast SHOULD this economy grow" vs "how fast DID it grow this round."

### Issue 2: Structural Budget Deficit / Social Spending Shortfall

**Option A (RECOMMENDED): Reduce mandatory social fraction from 70% to 50%**

The 70/30 split means countries must pay 70% of their social baseline as non-negotiable mandatory cost, then try to fund the remaining 30% from discretionary. But discretionary is often zero.

Reducing mandatory to 50% means:
- Gallia mandatory social: 0.35 * 34 * 0.50 = 5.95 (was 8.33)
- Total mandatory: 7.0 + 5.95 = 12.95
- Revenue 12.3: gap is only -0.65 (was -3.0)
- With some discretionary allocation, actual social ratio could reach ~0.30
- Shortfall drops to ~0.05, penalty = -0.05 * 3 * 0.5 = -0.075/round (was -0.158)

**Tradeoff:** Makes it easier for ALL countries to fund social spending. Some very poor countries (Caribe, Choson) would still struggle, which is correct. The 50% mandatory floor still ensures a minimum social safety net exists.

**Option B: Scale the shortfall penalty from 3x to 1.5x**

```python
# CURRENT:
delta -= shortfall * 3
# FIX:
delta -= shortfall * 1.5
```

Gallia penalty would drop from -0.315 to -0.158 raw, -0.079 after dampening. Over 8 rounds: -0.63 instead of -1.26.

**Tradeoff:** This is a symptomatic fix (Marat doesn't like caps/patches), but it IS a formula parameter, not a cap. The 3x multiplier was designed for a scenario where countries CHOOSE to underfund social spending. In steady state with no player choices, countries shouldn't be punished for structural budget constraints they didn't choose.

**Option C: Make social baseline scale with fiscal capacity**

Instead of a fixed percentage of GDP, tie social_baseline to what the country can actually afford:
```python
affordable_social = min(social_spending_baseline, revenue * 0.4 / gdp)
```

**Tradeoff:** More realistic (governments adjust social programs to budget reality) but harder to calibrate and may mask real budget crises that SHOULD happen.

**Option D (COMPLEMENTARY): Fix initial budget parameters**

Per Marat's directive: "balancing formulas and initial budget states so a normal country in steady state has sufficient resources for basic maintenance, standard social spending, some technology, some military production."

For each country, verify: `revenue > maintenance + full_social_baseline + minimum_tech + minimum_production`. If not, adjust ONE of:
- Lower `social_baseline` for countries where it's unrealistically high
- Lower `maintenance_per_unit` further
- Raise `tax_rate` to match real-world effective tax rates
- Reduce `debt_burden` starting values

Example for Gallia: social_baseline 0.35 (35% of GDP) is high but realistic for France. The problem is debt_burden=3, which eats ~25% of base revenue. Reducing debt_burden to 1.5 adds 1.5 to revenue, closing half the gap. Combined with Option A or B, this resolves the issue.

**My recommendation:** Option A (50% mandatory) + Option D (audit starting budgets). This is a systemic fix to the model AND the data, not a cap.

### Issue 3: Momentum Needs Dampening (Secondary)

Even after fixing the growth feedback loop (Issue 1), momentum can still add up to +5% per round (momentum * 0.01 at momentum=5.0). Over 8 rounds of uninterrupted prosperity, that's a significant growth boost.

**Fix:** Reduce momentum ceiling from 5.0 to 3.0 and/or reduce the growth coefficient from 0.01 to 0.005. This caps momentum's GDP contribution at +1.5% per round instead of +5%.

---

## What I'm Not Sure About

1. **Is the gdp_growth_rate overwrite intentional?** It could be a SEED design choice to model compound growth. If so, the fix is different -- you'd want to add drag/friction factors that prevent runaway, not eliminate the feedback. But the SEED engine code comment says "base growth rate," implying it should be a fixed structural parameter.

2. **Social spending 70/30 split origin.** Is this from SEED design docs or a BUILD-phase assumption? If it's a tested SEED mechanic, changing it needs design reconciliation per CLAUDE.md Cardinal Rule.

3. **Should momentum affect the growth rate at all?** The current coefficient (0.01 = 1% per momentum point) may be too high even after fixing the feedback loop. Real-world confidence effects on GDP are smaller.

4. **Persia stability 4->1.2 with no war.** Marat flagged this. Persia starts with inflation=50%, which creates inflation_delta = 50 - 50 = 0 (no friction from inflation itself, good). But gdp_growth_base = -3.0 (post-Cal-5 fix changed to +0.5 per accumulated knowledge... need to verify which value is in the actual seed data). If still -3.0, then GDP contracts, triggering stability penalty. The seed data shows -3.0, which may not have been updated.

---

## Accumulated Insights (Across 3 Runs)

| Run | Key Problem | Root Cause | Fix Applied |
|-----|------------|------------|-------------|
| #001 | Everything broken | Sanctions 10-75x too aggressive, growth uncapped | Sanctions /10, growth /2 |
| #002 | Sarmatia collapse, universal stability drain | Maintenance costs 3-531% of GDP | SIPRI-based maintenance recalibration |
| #003 | Universal stability drain persists, Columbia/Yamato overgrowth | **Growth rate feedback loop** + **structural budget deficit** | TBD |

**Pattern recognition across 3 runs:**

1. **The engine is more interconnected than it looks.** Fixing one parameter exposes the next bottleneck. Maintenance fix (Run 2) fixed Sarmatia but revealed social spending as the real stability driver for everyone else. Growth rate fix (this run) will change momentum dynamics downstream.

2. **Two classes of problems:** DATA problems (wrong starting values) vs FORMULA problems (wrong mechanics). Run 1 was data. Run 2 was data. Run 3 is primarily FORMULA (the feedback loop and the 70/30 split).

3. **The "peaceful dampening" (0.5x multiplier on negative delta) is working.** Without it, stability drops would be 2x worse. But it's masking the underlying problem rather than preventing it.

4. **Budget balance is THE key to stable steady state.** If revenue >= mandatory costs with room for discretionary, countries stabilize. If not, everything cascades: deficit -> money printing -> inflation -> stability loss -> crisis -> GDP hit -> less revenue -> deeper deficit.

5. **Priority order for fixes:**
   - FIX 1 (critical): Separate structural base rate from actual growth rate in GDP formula
   - FIX 2 (critical): Reduce mandatory social fraction OR audit starting budgets for fiscal balance
   - FIX 3 (nice-to-have): Reduce momentum ceiling to 3.0
   - FIX 4 (verify): Confirm Persia gdp_growth_base is +0.5 not -3.0 in actual test data

---

*Calibration Memo generated by SUPER EXPERT, Cycle 3. Ready for Marat review.*
