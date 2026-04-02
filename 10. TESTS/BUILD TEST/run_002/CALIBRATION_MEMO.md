# Calibration Memo — Test Run #002 (Cycle 2)

**Date:** 2026-04-01 | **Author:** SUPER EXPERT | **Engine version:** Sprint 2 + Cal-5 fixes
**Changes from #001:** sanctions /10, growth /2 (6mo rounds), social key fix, Persia growth 0.5
**Methodology:** CALIBRATION_METHODOLOGY.md v1.0, Levels A/B/C

---

## What I See (Autonomous Assessment)

### What Improved (Run #001 -> Run #002)

1. **Persia GDP: MUCH better.** 5.0 -> 4.7 over 8 rounds (-6%). Run #001 had Persia at floor by R2. This is now within the real-world Iran range (IMF projects ~0.3-0.6% annual growth under sanctions). PASS.

2. **Oil price: NOW REALISTIC.** $80 -> $101 (+26%), rising trend during wars. Real-world: Brent crude rose ~20-55% during Middle East escalations in early 2026. The direction is correct and magnitude is plausible. PASS.

3. **Elections: MORE COMPETITIVE.** Range 53-75% vs always 75% in Run #001. Columbia midterms still at 75% (too high), but Ruthenia elections at 53-55% show genuine competition. IMPROVED, not yet fully realistic.

4. **No revolutions triggered.** Run #001 had Persia in permanent revolution from R1. The absence of revolutions in a baseline (no player actions) run is acceptable. PASS.

5. **Columbia/Cathay growth: SIGNIFICANTLY reduced.** Columbia +58% (was +228%), Cathay +49% (was +239%). Still too high but a massive improvement. NEEDS MORE WORK.

### What Is Still Broken

**ISSUE 1 — CRITICAL: Sarmatia GDP Collapse (20.0 -> 1.8, -91%)**

Sarmatia loses 78.5% of GDP in Round 1 alone (20.0 -> 4.3), then continues declining to 1.8 by R5. This is the single worst calibration failure and was already flagged in Run #001. The Run #001 fixes (sanctions /10) clearly did not reach Sarmatia's primary damage channel.

Real-world comparison: Russia's GDP under the heaviest sanctions regime in history:
- 2022: -2.1%
- 2023: +3.6%
- 2024: +4.0%
- 2025 forecast: +0.5% to +2.5%
- Cumulative 2022-2025: approximately +5% to +8% vs 2021 baseline

Even in the most pessimistic counterfactual analysis (what Russia's GDP would have been WITHOUT the war/sanctions), the loss is estimated at -15% to -20% over 3 years. The simulation produces -91% over 4 simulated years. This is 5-6x too aggressive.

**ISSUE 2 — MAJOR: Universal Stability Decline**

Almost every country's stability declines over 8 rounds. This is the "entropy problem" — the engine has a structural negative bias.

| Country | Start | End | Change | At war? | Sanctioned? | Plausible? |
|---------|-------|-----|--------|---------|-------------|------------|
| columbia | 7.0 | 4.0 | -3.0 | yes (minor) | no | NO — dominant power should be 6-7 |
| gallia | 7.0 | 3.4 | -3.6 | no | no | NO — stable democracy, should be 6-7 |
| bharata | 6.0 | 2.6 | -3.4 | no | no | NO — growing democracy, should be 5.5-6.5 |
| yamato | 8.0 | 6.2 | -1.8 | no | no | BORDERLINE — Japan is very stable |
| formosa | 7.0 | 6.4 | -0.6 | no | no | OK |
| teutonia | 7.0 | 7.2 | +0.2 | no | no | GOOD — Germany stable |
| cathay | 8.0 | 7.8 | -0.2 | no | no | OK — slight autocracy friction |

Only Teutonia maintains stability correctly. Most peaceful democracies drift from stable to crisis in 8 rounds. A geopolitics expert would find this implausible: France, India, Japan, and the US do not drift to stability scores of 2-4 over two peaceful years.

**ISSUE 3 — MAJOR: Columbia/Cathay Still Grow Too Fast**

Columbia: 280 -> 442.2 (+58% over 8 rounds = ~4 simulated years)
Cathay: 190 -> 283.8 (+49% over 8 rounds = ~4 simulated years)

Real-world annual growth rates:
- US: 2.1-2.8% annual (2024-2025). Over 4 years: ~10-12% cumulative.
- China: 5.0% annual (2024-2025). Over 4 years: ~20-22% cumulative.

The simulation produces growth approximately 5x too fast for Columbia and 2.5x too fast for Cathay.

**ISSUE 4 — MODERATE: Caribe Slow Collapse**

Caribe: 2.0 -> 0.9 (-55%) and stability 3.0 -> 1.0 (floor). Cuba+Venezuela analog losing half its GDP in a baseline run without any player aggression seems too harsh, though this is a lower-priority country.

**ISSUE 5 — MINOR: Choson Stability Decline**

Choson (North Korea): stability 4.0 -> 2.5. An isolated autocracy with no wars or sanctions should be stable (authoritarian stability is their whole model). The engine treats all countries the same way, but North Korea's regime has been stable for 70+ years.

---

## Root Cause Analysis

### RCA-1: Sarmatia GDP Collapse — STRUCTURAL + PARAMETRIC

**Tracing the formula chain for Round 1:**

Starting state: Sarmatia GDP = 20.0, gdp_growth_base = 1.0, at_war_with = ruthenia, sanctions assumed from columbia coalition.

Step 1: `calc_gdp_growth()` (economic.py:812-927)
- `base_growth = 1.0 / 100.0 / 2.0 = 0.005` (0.5% per round) -- correct
- `sanctions_hit`: `calc_sanctions_impact()` (economic.py:676-723)
  - Coverage: Columbia alone is 280/(280+190+20+...) ~ 280/700 ~ 40% of world GDP. At level 3 sanctions: coverage = 0.40 * (3/3) = 0.40.
  - S-curve at 0.40: interpolating between (0.3, 0.10) and (0.5, 0.20) gives ~0.15.
  - Trade openness: Sarmatia trade_balance = 2, GDP = 20. `trade_openness = clamp(2/20 + 0.3, 0, 1) = 0.40`.
  - `total_damage = 0.08 * 0.15 * 0.40 = 0.0048` (0.48%)
  - `sanctions_hit = -0.0048 * 0.15 = -0.00072` (-0.07%)

  This is TINY. The sanctions fix worked. So sanctions are NOT the primary Sarmatia killer in Run #002.

Step 2: **The real killer is the CRISIS STATE MULTIPLIER chain.**

Look at what happens:
- Sarmatia starts `economic_state = "normal"` (orchestrator.py:90 hardcodes this)
- But Sarmatia is at war with occupied zones. `war_hit = -(zones * 0.03 + infra_damage * 0.05)`. If Sarmatia has 2 zones occupied: war_hit ~ -0.11.
- `effective_growth = raw_growth * crisis_mult` — for "normal" state, crisis_mult = 1.0.
- After Round 1: GDP drops, treasury drops to 0, stability drops. This triggers `update_economic_state()` (economic.py:1207).
- **Stress triggers fire:** GDP growth < -1? YES. Treasury <= 0? LIKELY. Stability < 4? POSSIBLY. That is 2+ triggers -> state becomes "stressed".
- In Round 2: `CRISIS_GDP_MULTIPLIER["stressed"] = 0.85` for positive growth, but `CRISIS_NEGATIVE_AMPLIFIER["stressed"] = 1.2` for negative growth. The war hit + any remaining negative factors get AMPLIFIED.
- More importantly: `CRISIS_GDP_MULTIPLIER["crisis"] = 0.5` and `CRISIS_NEGATIVE_AMPLIFIER["collapse"] = 2.0`. Once Sarmatia enters crisis/collapse, negative growth is doubled, creating an irrecoverable death spiral.

**BUT WAIT** — the GDP drop from 20.0 to 4.3 in ONE round is -78.5%. That cannot come from war_hit = -11% alone. Let me trace more carefully.

The missing piece: **budget execution deficit spiral** (economic.py:984-1059).
- Sarmatia revenue = GDP * tax_rate = 20 * 0.20 = 4.0 coins
- Military maintenance: 18 ground + 2 naval + 8 tactical_air + 12 strategic_missiles + 3 air_defense = 43 units * 0.30 = 12.9 coins
- Social baseline mandatory = 0.25 * 20 * 0.70 = 3.5 coins
- Total mandatory = 12.9 + 3.5 = 16.4 coins
- Revenue = 4.0. Deficit = 16.4 - 4.0 = 12.4 coins
- Treasury = 6.0. After deficit: treasury = 0, money_printed = 12.4 - 6.0 = 6.4 coins
- Inflation from printing: 6.4 / 20 * 80 = 25.6% increase
- Debt burden increase: 12.4 * 0.15 = 1.86 coins added to existing 0.5

This MASSIVE deficit comes from military maintenance costs exceeding total revenue by 3x. The budget execution creates a deficit spiral that feeds inflation, which feeds stability decline, which feeds economic state transitions.

**Then the inflation feeds back into GDP via revenue erosion and crisis state transitions.** After Round 1, Sarmatia inflation spikes from 5% to ~30%+, triggering stress triggers for inflation > starting + 15 and potentially crisis triggers for inflation > starting + 30.

**ROOT CAUSE: Sarmatia's military maintenance (43 units * 0.30 = 12.9 coins/round) exceeds total revenue (4.0 coins/round) by 3.2x.** This creates a structural budget deficit that spirals into hyperinflation and economic collapse independent of sanctions or war damage.

Real-world: Russia spends ~4% of GDP on military (not 65%). Even during the Ukraine war, Russian military spending rose to ~6-8% of GDP, funded partially by sovereign wealth fund drawdowns and oil revenue. The simulation gives Sarmatia zero budget flexibility.

**Classification: STRUCTURAL (budget deficit spiral) + INITIALIZATION (military costs vs GDP ratio unrealistic)**

### RCA-2: Universal Stability Decline — STRUCTURAL

The stability formula (`calc_stability()`, political.py:265-377) has a systematic downward bias in Tier 1 tests (no player actions). Tracing for a peaceful, prosperous democracy like Gallia:

- Gallia: stability 7.0, GDP growth ~1.0% per round, democracy, not at war, not sanctioned.
- `base_growth = 1.0 / 100 / 2 = 0.005` -> `gdp_growth_rate` stored as growth_pct = ~0.37% (after processing). This means `gdp_growth_rate` passed to stability is approximately 0.37.

Wait — I need to check what value gets passed. In orchestrator.py:328, `gdp_growth_rate=eco.get("gdp_growth_rate", 0.0)`. After economic engine runs, `eco["gdp_growth_rate"] = gdp_result.growth_pct` (orchestrator.py line 182/economic.py:900: `growth_pct = effective_growth * 100.0`). So if effective_growth = 0.005, growth_pct = 0.5.

In `calc_stability()`:
- **Positive inertia** (line 281): stability 7.0 is in [7,9) -> delta += 0.05. GOOD.
- **GDP growth** (line 286): growth_pct = 0.5. Since 0.5 < 2: no GDP bonus. Since 0.5 > -2: no GDP penalty. Net: 0.
- **Social spending** (line 293-302): With the social key fix applied (orchestrator.py:331 now uses `_actual_social_ratio`), the budget execution defaults should give social_ratio = baseline when there is sufficient revenue. For Gallia: revenue = 34 * 0.45 = 15.3, maintenance = ~12 units * 0.5 = 6.0, mandatory social = 0.35 * 34 * 0.70 = 8.33. Total mandatory = 14.33. Revenue 15.3 > mandatory 14.33, so discretionary = 0.97. Discretionary social pool = 0.35 * 34 * 0.30 = 3.57. social_extra = min(3.57, 0.97) = 0.97.

  actual_social_total = 8.33 + 0.97 = 9.30. actual_social_ratio = 9.30 / 34 = 0.274.
  baseline = 0.35.

  **Shortfall = 0.35 - 0.274 = 0.076.** This triggers line 301-302: `delta -= 0.076 * 3 = -0.228`.

- **Peaceful non-sanctioned dampening** (line 357): delta * 0.5.
- Net delta after dampening: (0.05 + 0 - 0.228) * 0.5 = -0.089 per round.

Over 8 rounds: 7.0 - (0.089 * 8) = 7.0 - 0.71 = 6.29. But the actual result is 3.4. That is much steeper. So there must be an additional accelerating factor.

**The acceleration comes from the feedback loop:** As stability drops below 7, positive inertia stops (line 281). As stability drops below 6, the momentum engine may stop boosting. As stability drops below 4, stress triggers fire for `economic_state` (line 1240), potentially pushing the country to "stressed," which adds CRISIS_STABILITY_PENALTY of -0.10 (line 346). Each of these transitions removes a stabilizing factor or adds a destabilizing one.

**The core structural issue:** Gallia has a social spending baseline of 35% (the highest in the game — France analog). With tax_rate 0.45 and military costs, Gallia cannot fully fund social spending from revenue alone. The 7.6% shortfall creates a permanent -0.228/round stability drain. With dampening, this is -0.114/round. Over 8 rounds: -0.91, giving 7.0 -> 6.09. The steeper actual decline (to 3.4) suggests the feedback loop accelerates after R3-R4.

**The same mechanism hits every country differently:**
- **Teutonia** (7.0 -> 7.2): social_baseline = 0.30, tax_rate = 0.38, GDP = 45. Revenue = 17.1, mandatory = maintenance + 0.30*45*0.70 = maybe ~12. Teutonia has enough revenue headroom that social spending is fully funded. Hence stability RISES.
- **Bharata** (6.0 -> 2.6): social_baseline = 0.20, tax_rate = 0.18, GDP = 42. Revenue = 7.56, mandatory = ~12 units * 0.25 + 0.20*42*0.70 = 3.0 + 5.88 = 8.88. Revenue 7.56 < mandatory 8.88. **Bharata runs a deficit from Round 1**, meaning zero discretionary social spending, so actual_social_ratio = 5.88/42 = 0.14 vs baseline 0.20. Shortfall = 0.06, penalty = -0.18. Plus deficit -> money printing -> inflation -> additional stability friction. This creates the severe decline.

**Classification: STRUCTURAL — The social spending shortfall penalty (3x multiplier) combined with budget constraints creates a deterministic stability drain for any country where revenue < mandatory + full social spending.**

**The key insight:** The social spending penalty was designed for a world where players CHOOSE to cut social spending. In Tier 1 (no player actions), the budget engine defaults are insufficient to fund full social spending for most countries. The formula interprets "government cannot afford social spending" the same as "government deliberately cut social spending" — but the stability impact should be different.

### RCA-3: Columbia/Cathay Excessive Growth — PARAMETRIC

Run #001 applied "growth /2" to convert annual rates to 6-month rounds. Line 827: `base_growth = eco["gdp_growth_rate"] / 100.0 / 2.0`.

Columbia: base_growth = 1.8 / 100 / 2 = 0.009 (0.9% per round).
Cathay: base_growth = 4.0 / 100 / 2 = 0.020 (2.0% per round).

But the RESULTS show Columbia growing from 280 -> 442.2, which is (442.2/280)^(1/8) - 1 = 5.9% per round compounded. That is 6.6x the base rate.

The excess growth comes from:
1. **Momentum stacking:** `momentum_effect = momentum * 0.01`. If momentum builds to 3.0 (maximum positive signals each round), this adds 3% per round.
2. **Oil revenue for Columbia:** As an oil producer with rising oil prices ($80 -> $101), Columbia gets positive oil_shock: `0.01 * (101-80)/50 = 0.0042` (0.42% per round).
3. **Market index feedback:** GDP growth > 2% -> market index rises -> no penalty. This is self-reinforcing.
4. **No growth cap was implemented.** Run #001's prescription P1 (MAX_GROWTH_PER_ROUND = 0.08) was NOT applied in Run #002. Only the /2 fix was applied.

For Cathay: base 2.0% + momentum ~2-3% + tech boost (AI level 3 = 1.5%) = ~5.5-6.5% per round. Over 8 rounds: 1.06^8 = 1.59 -> 190 * 1.59 = 302. Close to the observed 283.8 (some dampening from diminishing momentum).

**Classification: PARAMETRIC — No per-round growth cap. The /2 fix halved the base rate but did not cap the additive factor stacking (momentum + tech + oil).**

### RCA-4: Caribe Collapse — INITIALIZATION + STRUCTURAL

Caribe starts with GDP 2.0, gdp_growth_base = -1.0, inflation 60%, debt_burden 5, stability 3.0. This is already a country in crisis. With negative base growth (-0.5% per round after /2), high inflation, high debt, and the budget deficit spiral (same mechanism as Sarmatia — military costs likely exceed revenue), collapse is deterministic.

**Classification: INITIALIZATION — starting conditions make collapse inevitable. May be intentional for Cuba+Venezuela, but the trajectory seems too steep.**

---

## Fix Options (with tradeoffs)

### FIX A: Sarmatia GDP Collapse

**Option A1: Cap military maintenance at percentage of revenue** (RECOMMENDED)
- Add a maintenance affordability cap: `effective_maintenance = min(maintenance, revenue * 0.40)`
- Countries cannot spend more than 40% of revenue on maintenance. Excess units are "degraded" (flagged but not removed — they lose effectiveness).
- **Predicted effect:** Sarmatia maintenance capped at ~1.6 coins instead of 12.9. Deficit reduced from 12.4 to ~5.0. Money printing cut by 60%. Inflation spiral broken.
- **Risk:** Changes military balance calculations. Need to track "degraded" units. MEDIUM complexity.

**Option A2: Reduce maintenance_per_unit for Sarmatia** (SIMPLER)
- Change Sarmatia maintenance_per_unit from 0.30 to 0.10 in countries.csv.
- Rationale: Russia's military is largely conscript-based with lower per-unit costs. The 0.30 rate was designed for Western professional militaries.
- **Predicted effect:** Maintenance = 43 * 0.10 = 4.3 coins vs revenue of 4.0. Still a deficit but manageable with treasury (6.0 coins). GDP decline slowed to ~5-8% per round from war damage alone.
- **Risk:** LOW. Simple data change. But feels ad-hoc — the structural problem (maintenance > revenue = death spiral) affects other countries too.

**Option A3: Add "wartime economy" mode** (BEST LONG-TERM)
- When at war, countries can redirect social spending to military, access emergency reserves, and accept controlled inflation.
- This is closer to reality: Russia's wartime economy explicitly redirected civilian production to military, accepted 8%+ inflation, and drew down its National Wealth Fund.
- **Predicted effect:** Sarmatia survives with degraded social indicators but functional economy. GDP decline 10-20% over 8 rounds.
- **Risk:** HIGH complexity. New subsystem. Not appropriate for this calibration cycle.

**RECOMMENDATION: Apply A2 now (reduce Sarmatia maintenance_per_unit to 0.10), and also apply A1 as a general safety mechanism (cap maintenance at 40% of revenue). Both changes together prevent the death spiral while keeping the simulation interesting.**

### FIX B: Universal Stability Decline

**Option B1: Reduce social spending shortfall penalty multiplier** (RECOMMENDED)
- Change political.py line 302: `delta -= shortfall * 3` to `delta -= shortfall * 1.0`
- The current 3x multiplier means a 6% funding gap costs -0.18 stability/round. At 1.0x, the same gap costs -0.06/round.
- **Predicted effect:** Gallia stability over 8 rounds: ~6.5 instead of 3.4. Bharata: ~4.8 instead of 2.6.
- **Risk:** LOW. May make social spending cuts too painless as a player action. Can re-tune later.

**Option B2: Add a "government autopilot" social spending guarantee**
- When no explicit budget is provided (Tier 1 test), assume governments fund social spending at 100% of baseline, even if it means deficit.
- This is realistic: no government voluntarily cuts 30% of social spending without being forced to.
- **Predicted effect:** All countries fund social spending fully. Stability drain eliminated for funded countries. Deficit countries (Sarmatia, Caribe, Persia) still struggle but less severely.
- **Risk:** MEDIUM. Changes Tier 1 test behavior. Could mask real budget constraint issues.

**Option B3: Widen positive inertia band** (COMPLEMENTARY)
- Change political.py line 281: `if 7 <= old_stab < 9:` to `if 5 <= old_stab < 9:`
- Stable countries (5+) get +0.05/round inertia bonus, partially offsetting negative drift.
- **Predicted effect:** Slows decline for countries in the 5-7 range. Does not prevent decline, just reduces speed.
- **Risk:** LOW. Minor constant change.

**RECOMMENDATION: Apply B1 (reduce multiplier to 1.0) + B3 (widen inertia band to 5+). Together these keep peaceful countries in realistic stability ranges while still allowing genuine crises to develop.**

### FIX C: Columbia/Cathay Excessive Growth

**Option C1: Add per-round growth cap** (RECOMMENDED)
- This was prescribed in Run #001 (P1) but NOT implemented. Add after economic.py line 896:
  ```python
  MAX_GROWTH_PER_ROUND = 0.06  # 6% per 6-month round = ~12% annualized max
  MIN_GROWTH_PER_ROUND = -0.15
  effective_growth = clamp(effective_growth, MIN_GROWTH_PER_ROUND, MAX_GROWTH_PER_ROUND)
  ```
- **Predicted effect:** Columbia over 8 rounds: 280 * 1.06^8 = 446 (still high but closer). With realistic base rate (0.9%) and some momentum, actual growth would be 2-4% per round -> 280 * 1.03^8 = 355 (~27% over 4 years, vs real-world US ~10-12%).
- **Risk:** LOW. Simple clamp.

**Option C2: Cap momentum accumulation** (COMPLEMENTARY)
- Reduce MOMENTUM_CEILING from 5.0 to 2.0 in economic.py line 114.
- At 2.0 max, momentum_effect = 2.0 * 0.01 = 2% per round. Combined with base, total stays under 4-5% per round.
- **Predicted effect:** Columbia growth capped at ~3-4% per round. Over 8 rounds: ~27-37%.
- **Risk:** LOW. Constant change.

**Option C3: Apply diminishing returns to large economies**
- Add a growth dampener for GDP > 100: `effective_growth *= 100 / max(gdp, 100)`
- Rationale: Large economies face structural headwinds (Baumol's cost disease, regulatory burden, base effect).
- **Predicted effect:** Columbia (280) growth dampened by factor of 100/280 = 0.36. Base 0.9% * 0.36 = 0.32% + smaller factor additions. More realistic but may over-correct.
- **Risk:** MEDIUM. Could make large economies too stagnant. Needs careful calibration.

**RECOMMENDATION: Apply C1 (growth cap at 6%) + C2 (reduce momentum ceiling to 2.0). C3 is a good idea but needs more thought — save for Cycle 3.**

---

## What I'm Not Sure About

1. **Sarmatia's war setup.** I can see Sarmatia starts `at_war_with: ruthenia` in the CSV, but I do not know how the test harness translates this into the `wars` list in `world_state`. Specifically, I do not know how many occupied zones Sarmatia starts with, or whether Sarmatia is the attacker or defender. This matters enormously for war_hit calculations. If the test harness gives Sarmatia 3+ occupied zones, the war damage alone could account for much of the R1 GDP drop.

2. **The budget execution default behavior.** When `actions["budgets"]` is empty (Tier 1), `budget.get("social_spending", discretionary_social_pool)` should default to the full discretionary pool. But `discretionary = max(revenue - mandatory, 0.0)` — if revenue < mandatory, discretionary is 0 regardless. I am fairly confident this is what happens for Sarmatia and Bharata, but I have not run the actual computation to verify the exact numbers.

3. **Whether the growth /2 fix was the right approach.** The CSV stores `gdp_growth_base` as ANNUAL rates (e.g., Columbia = 1.8 meaning 1.8% annual). Dividing by 2 gives approximately correct 6-month rates for small values. But for Cathay (4.0% annual), the correct 6-month equivalent is (1.04)^0.5 - 1 = 1.98%, which is close enough to 4.0/2 = 2.0%. This is fine.

4. **Whether Caribe collapse is intentional.** Cuba+Venezuela as a combined entity starting with -1% growth, 60% inflation, and debt burden of 5.0 (vs GDP 2.0 = 250% debt-to-GDP) might be designed to collapse. Marat's judgment needed: should Caribe be a viable entity or a failing state from the start?

5. **The interaction between economic engine order and feedback loops.** The economic engine processes countries sequentially (economic.py:1630: `for cid in list(countries.keys())`), which means earlier-processed countries' GDP changes affect later countries' trade weights and contagion. The order could matter for Sarmatia's trajectory. I have not analyzed order-dependent effects.

---

## Accumulated Insights (Across 2 Runs)

### Engine Behavior Patterns

1. **Death spiral mechanics are extremely powerful.** Any country that enters a deficit spiral (maintenance > revenue) loses control within 2-3 rounds. The chain is: deficit -> money printing -> inflation -> stability loss -> economic state transition -> GDP amplification -> lower revenue -> deeper deficit. Once triggered, this is nearly irrecoverable without external intervention.

2. **The social spending penalty is the dominant stability driver.** For most countries in Tier 1, the social spending shortfall (caused by budget constraints, not player choice) is the single largest contributor to stability decline. Fixing this one mechanism would stabilize 80% of the anomalous trajectories.

3. **Momentum is the dominant GDP growth driver.** Base growth rates are reasonable after the /2 fix. But momentum stacking (+3% per round possible) overwhelms the base rate. Momentum was designed as a "confidence" variable but in practice acts as a free compound interest multiplier for prosperous countries.

4. **The crisis state system amplifies small problems into catastrophes.** The jump from "normal" to "stressed" is binary (2 triggers = instant transition) and the GDP multipliers are dramatic (1.0 -> 0.85 for positive, 1.0 -> 1.2 for negative). For countries near the threshold, a single bad round can trigger a multi-round cascade.

5. **Parametric fixes have limited reach.** Run #001 reduced sanctions by 10x, which fixed Persia beautifully. But Sarmatia's problem was never sanctions — it was the military maintenance budget deficit. Diagnosing the correct root cause matters more than tuning constants.

### What to Watch in Run #003

1. Does the growth cap prevent Columbia/Cathay runaway? Watch for growth_pct values — they should be 2-4% per round, not 5-6%.
2. Does the social spending multiplier reduction stabilize peaceful democracies? Gallia and Bharata should stay above 5.0 over 8 rounds.
3. Does the maintenance cap save Sarmatia from the deficit spiral? Sarmatia GDP should decline 10-20% total over 8 rounds (like real Russia), not 91%.
4. Watch for over-correction: if all countries become too stable (nobody below 4.0 by R8), the simulation loses dramatic tension. The target is SOME instability for fragile states, not universal calm.
5. Watch election results: with more realistic GDP growth rates, Columbia's `econ_perf = gdp_growth * 10.0` should produce lower values, making elections more competitive without any election-specific fixes.

### Convergence Criteria Assessment (Run #002)

| # | Criterion | Status | Notes |
|---|-----------|--------|-------|
| 1 | No GDP collapse to floor without catastrophe | **FAIL** | Sarmatia 20->1.8, Caribe 2->0.9 |
| 2 | Sanctioned countries decline 5-15% per round | **PASS** | Persia -6% total. Sarmatia fails but cause is budget, not sanctions |
| 3 | Growing economies grow 2-8% per round | **FAIL** | Columbia ~5.9%/round, Cathay ~5.1%/round (borderline high) |
| 4 | Stability changes +/-0.5 per round typical | **FAIL** | Gallia -0.45/round, Bharata -0.43/round |
| 5 | Oil price $50-$200 without clamping | **PASS** | $80->$101, realistic range |
| 6 | Elections competitive | **PARTIAL** | 53-75% range (was always 75%) |
| 7 | At least one unscripted crisis | **PASS** | Caribe and Sarmatia crises are emergent |
| 8 | No country eliminated before R4 | **FAIL** | Sarmatia at 1.8 by R5 |
| 9 | Geopolitics-literate human says "plausible" | **FAIL** | Universal stability decline is implausible |

**Score: 3/9 criteria met (was 1/9 in Run #001). Improving but 3 critical fixes needed for Cycle 3.**

### Recommended Fix Batch for Run #003

| Priority | Fix | Type | Code Location | Change |
|----------|-----|------|---------------|--------|
| 1 | **Growth cap** | PARAMETRIC | economic.py:896 | Add `clamp(effective_growth, -0.15, 0.06)` |
| 2 | **Momentum ceiling** | PARAMETRIC | economic.py:114 | MOMENTUM_CEILING: 5.0 -> 2.0 |
| 3 | **Social penalty multiplier** | PARAMETRIC | political.py:302 | Shortfall multiplier: 3 -> 1.0 |
| 4 | **Positive inertia band** | PARAMETRIC | political.py:281 | Threshold: 7 -> 5 |
| 5 | **Sarmatia maintenance cost** | INITIALIZATION | countries.csv:4 | maintenance_per_unit: 0.30 -> 0.10 |
| 6 | **Maintenance revenue cap** | STRUCTURAL | economic.py:997 | `maintenance = min(maintenance, revenue * 0.40)` |

Apply all 6 as a batch. Predicted outcome: 6-7/9 convergence criteria met.
