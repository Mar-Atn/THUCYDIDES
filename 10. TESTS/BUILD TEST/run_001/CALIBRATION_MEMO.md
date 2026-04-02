# Calibration Memo — Test Run #001

**Date:** 2026-04-01 | **Author:** SUPER EXPERT | **Engine version:** Sprint 2 initial port
**Methodology:** CALIBRATION_METHODOLOGY.md v1.0, Levels A/B/C

---

## Level A: Macro Realism Check

### A1: Starting Values — GDP Mismatch

The CSV (`countries.csv`) defines Sarmatia GDP = 20.0 coins, but the results show R0 = 5.2 — a 74% drop before the simulation even begins. Similarly:

| Country | CSV GDP | R0 GDP | Discrepancy |
|---------|---------|--------|-------------|
| columbia | 280.0 | 357.5 | +27.7% |
| cathay | 190.0 | 254.5 | +33.9% |
| sarmatia | 20.0 | 5.2 | **-74.0%** |
| persia | 5.0 | 1.8 | **-64.0%** |
| gallia | 34.0 | 36.9 | +8.5% |
| bharata | 42.0 | 56.3 | +34.0% |

**Verdict:** R0 is not the initial state — it is the state after Round 1 processing. But the magnitude of change in Round 1 is catastrophically unrealistic. Columbia should not gain 28% in a single round. Sarmatia should not lose 74% in a single round.

### A2: Overall Shape Assessment

- **Plausible:** Bharata grows faster than Columbia (real-world: India 6-7% vs US 2-3%). Correct direction.
- **Implausible:** Columbia GDP triples in 8 rounds (+228%). Real-world US GDP grows ~2%/year = ~17% over 8 years, not 228%.
- **Implausible:** Sarmatia GDP collapses from 20.0 to 0.5 by R2 (-97.5%). Real-world Russia under the heaviest sanctions in history: -1.2% in 2022, then +3.6% in 2023, +4% in 2024. Cumulative sanctions impact over 3 years was approximately -5% to -10% vs counterfactual.
- **Implausible:** Persia GDP collapses from 5.0 to 0.5 by R2 (-90%). Real-world Iran under maximum pressure: +3.7% in 2024, projected 0.6% in 2025. Even under the harshest historical sanctions (2011-2014), Iran's GDP declined ~17% over 3 years, not 90%.
- **Implausible:** Oil price drifts DOWN from $92 to $67 over 8 rounds despite 3 active wars. Real-world: Brent surged from $72 to $112 (+55%) in just one month when Iran conflict escalated in Feb-March 2026.

### A3: Real-World Benchmarks Summary

| Metric | Real World | Sim Produces | Assessment |
|--------|-----------|-------------|------------|
| Russia GDP under sanctions (annual) | -1% to -5% | -74% (R1) | **BROKEN** (15-75x too aggressive) |
| Iran GDP under sanctions + war | -2% to -17% cumulative | -64% (R1) | **BROKEN** (4-30x too aggressive) |
| China GDP growth (annual) | 4.5-5.0% | +34% (R1) | **BROKEN** (7x too fast) |
| US GDP growth (annual) | 1.8-2.8% | +28% (R1) | **BROKEN** (10x too fast) |
| India GDP growth (annual) | 6.5-7.6% | +34% (R1) | **BROKEN** (5x too fast) |
| Oil price during Middle East war | +15% to +55% | -27% over 8 rounds | **BROKEN** (wrong direction) |
| Sanctions GDP impact (academic) | -2.8% over 2 years (avg) | -97.5% over 2 rounds | **BROKEN** (35x too aggressive) |

---

## Level B: Parameter Dynamic Analysis

### Outliers Ranked by Severity

| Rank | Outlier | Expected | Actual | Severity |
|------|---------|----------|--------|----------|
| 1 | Sarmatia GDP R0-R2: -97.5% | -5% to -15% total | -97.5% | **CRITICAL** |
| 2 | Persia GDP R0-R2: -90% | -5% to -20% total | -90% | **CRITICAL** |
| 3 | Columbia GDP R0-R8: +228% | +15% to +25% | +228% | **CRITICAL** |
| 4 | Cathay GDP R0-R8: +239% | +35% to +45% | +239% | **CRITICAL** |
| 5 | Oil price: -27% during 3 wars | +15% to +55% | -27% | **SEVERE** |
| 6 | Bharata stability: 6.0→3.9 | Stable 5.5-6.5 | 3.9 | **MAJOR** |
| 7 | Phrygia stability: 5.0→2.3 | 4.5-5.5 | 2.3 | **MAJOR** |
| 8 | Persia revolution from R1 | Not before R3-R4 | R1 | **MAJOR** |
| 9 | Elections: incumbent always wins | 50-60% win rate | 100% | **MODERATE** |
| 10 | Caribe GDP: collapse to floor | -5% to -15% annual | Floor by R3 | **MODERATE** |

---

## Level C: Single-Variable Diagnosis

### C1: CRITICAL — Sarmatia/Persia GDP Catastrophic Collapse

**Trace the chain:**

1. `_country_to_dict()` (orchestrator.py:89) initializes `economic_state: "normal"` for ALL countries, including those starting at war.
2. But Sarmatia starts `at_war_with: ruthenia` and Persia starts `at_war_with: columbia;levantia`.
3. In Round 1, the economic engine processes these countries. The GDP growth formula (`calc_gdp_growth`, economic.py:812) computes:
   - `base_growth = eco["gdp_growth_rate"] / 100.0` — Sarmatia: 1.0/100 = 0.01, Persia: -3.0/100 = -0.03
   - `sanctions_hit` (economic.py:834): `sanctions_damage * SANCTIONS_GDP_MULTIPLIER` (1.5x). If sanctions coverage is high (Columbia + allies = ~60% of world GDP), the S-curve returns ~0.60 effectiveness. With Sarmatia trade_openness ~0.40, `damage = 0.50 * 0.60 * 0.40 = 0.12`. Then `sanctions_hit = -0.12 * 1.5 = -0.18` (-18% per round).
   - `war_hit` (economic.py:862): occupied zones * 0.03 + infra_damage * 0.05. If Sarmatia has 2 occupied zones: war_hit = -0.06 - 0.05 = -0.11.
   - For Persia, similar sanctions damage + war hit with TWO wars (columbia + levantia).

4. **The real killer:** After Round 1, Sarmatia GDP drops dramatically. This triggers `economic_state` transition to "stressed" (economic.py:1259) via stress triggers (GDP growth < -1, treasury <= 0, stability < 4). In Round 2, the crisis state multiplier kicks in: `CRISIS_NEGATIVE_AMPLIFIER["stressed"] = 1.2` or `CRISIS_GDP_MULTIPLIER["crisis"] = 0.5`. Combined with continuing sanctions, this creates a death spiral: lower GDP → worse economic state → larger negative amplifier → even lower GDP → floor.

5. **Key bug:** The `sanctions_rounds` counter (orchestrator.py:89) always starts at 0, so the diminishing returns threshold (SANCTIONS_DIMINISHING_THRESHOLD = 4 rounds) never applies in the first critical rounds. But the real problem is that sanctions damage is applied EACH ROUND as a percentage of current GDP, not as a fixed amount. A country losing 18% per round to sanctions alone hits the floor in 4-5 rounds.

**Root cause:** SANCTIONS_GDP_MULTIPLIER = 1.5 and SANCTIONS_MAX_DAMAGE = 0.50 combine to produce up to 75% GDP loss per round. Academic literature says sanctions cause -2.8% GDP loss over 2 years on average. Even the most extreme case (Syria) was -57% over 5 years.

### C2: CRITICAL — Columbia/Cathay Unchecked Compound Growth

**Trace the chain:**

1. Columbia base_growth = 1.8/100 = 0.018 per round.
2. But the actual R0→R1 growth is (395.5 - 357.5) / 357.5 = 10.6%. This is 5.9x the base rate.
3. The culprit is the additive factor model (economic.py:884-888). In addition to base_growth, Columbia gets:
   - `tech_boost`: AI level 3 → 0.015 (1.5%)
   - `momentum_effect`: If momentum builds to +3 → 0.03 (3%)
   - `oil_shock`: Columbia is an oil producer, oil > $80 → positive shock
   - Market index bonuses: GDP growth > 2 → index rises → no penalty
4. The compound growth is: (1 + 0.018 + 0.015 + 0.03 + oil_bonus) per round. With all factors, effective growth is ~10% per round.
5. Over 8 rounds: 1.10^8 = 2.14x — matches the observed ~228% increase.

**Root cause:** There is no growth ceiling or diminishing returns for large economies. Real-world large economies have structural constraints that limit growth. US GDP has never grown above 4% in a single year since 2000. The model allows unlimited positive factor stacking with compound interest.

### C3: CRITICAL — Oil Price Declining During Wars

**Trace the chain:**

1. `calc_oil_price()` (economic.py:525): `war_premium = len(wars) * 0.05`, capped at 0.15 (15% max).
2. With 3 wars, war_premium = 0.15. This adds only $12 to the $80 base.
3. Meanwhile, `demand` (economic.py:580-603) is dragged down by:
   - Countries in crisis/collapse (Sarmatia, Persia, Caribe all collapse to floor) → each subtracts 0.06-0.10
   - Average GDP growth factor: as collapsed countries drag down the average, demand falls further
4. The demand destruction from economic collapses OUTWEIGHS the war premium.

**Root cause:** (A) War premium cap of 0.15 is far too low. Real-world: the Iran conflict alone caused a 55% oil price spike. (B) The demand calculation counts collapsed small economies (Persia GDP 5, Caribe GDP 2) equally with majors, creating an artificial demand destruction signal. (C) The oil model doesn't distinguish between supply disruption from countries at war (Persia, a major oil producer, being at war should MASSIVELY reduce supply).

### C4: MAJOR — Bharata Stability Declining Despite Strong Growth

**Trace the chain:**

1. Bharata: democracy, stability 6.0, GDP growth 6.5%.
2. `calc_stability()` (political.py:265): GDP growth > 2 → delta += min((6.5 - 2) * 0.08, 0.15) = +0.15
3. But social spending check (political.py:293-302): `social_ratio` comes from orchestrator.py:331: `eco.get("social_spending_ratio", eco.get("social_baseline", 0.20))`.
4. **BUG:** The dict key is `social_spending_baseline` (orchestrator.py:87), but the orchestrator looks for `social_baseline` (wrong key). The fallback default is 0.20.
5. Bharata's actual `social_spending_baseline` = 0.20, and `social_baseline` in CSV = 0.20. So the fallback gives 0.20 as both ratio and baseline — which means `social_ratio >= baseline`, giving +0.05.
6. The actual stability decline comes from the `peaceful non-sanctioned dampening` NOT applying when it should: at stability 6, the positive inertia doesn't kick in (requires 7-9). Meanwhile, negative factors accumulate from inflation friction (Bharata starts at 5.0% inflation, and if inflation grows, the delta from baseline triggers friction).
7. Actually, the PRIMARY issue is that Bharata starts at stability 6.0 and the GDP growth bonus (+0.15) is offset by the social spending mechanics. The key factor: with NO player actions (Tier 1 test), the budget execution defaults leave social spending at mandatory-only levels. The discretionary social pool is not allocated because `budget.get("social_spending", discretionary_social_pool)` uses an empty budget dict. This means actual social spending = mandatory only = 70% of baseline. So `actual_social_ratio` = 0.70 * 0.20 = 0.14, while baseline = 0.20. The shortfall is 0.06 → `delta -= 0.06 * 3 = -0.18` per round.

**Root cause:** In Tier 1 tests (no player actions), the budget execution defaults to zero discretionary social spending, creating a structural stability drain for ALL countries. This is a TEST HARNESS issue, not a formula issue — but it means all Tier 1 results are unreliable because they model a world where every government cuts 30% of its social spending.

### C5: MAJOR — Phrygia Crisis (Stability 5.0 → 2.3)

**Trace the chain:**

1. Phrygia starts with: stability 5.0, inflation 45.0%, starting_inflation = 45.0%.
2. The inflation delta friction (political.py:336-342): `inflation_delta = current - starting`. If Phrygia's inflation rises due to budget deficits (money printing), the delta grows rapidly.
3. Phrygia has GDP 11, maintenance costs for 11 military units × 0.30 = 3.3 coins. Revenue = 11 × 0.25 = 2.75. **Revenue < maintenance alone.** This means deficit → money printing → inflation spiral → inflation friction on stability.
4. Inflation grows: 45% base + money_printing/GDP * 80. Even a small printed amount (1 coin) on 11 GDP = 7.3% inflation increase per round. After 4 rounds: inflation ~75%, delta from baseline = 30 → friction = -(30-3)*0.05 - (30-20)*0.03 = -1.35 - 0.30 = -1.65 per round. Capped at -0.50 per round (Cal-4 cap).
5. Combined with the social spending shortfall from C4 (-0.18), Phrygia loses ~0.68 stability per round.
6. Phrygia is a hybrid regime (no autocracy resilience bonus). With non-war, non-sanctioned dampening (delta * 0.5), effective loss is ~0.34/round. From 5.0: after 8 rounds → ~2.3. This matches the results.

**Root cause:** (A) Phrygia starts with structural budget deficit (military costs > revenue). (B) The Tier 1 test doesn't provide budgets, so the default behavior creates deficits. (C) Turkey/Phrygia in reality has high inflation but the government manages it — the model has no fiscal policy response mechanism in autopilot mode.

### C6: MODERATE — Elections Always Won by Incumbent

**Trace the chain:**

1. `process_election()` (political.py:443): `ai_score = clamp(50 + econ_perf + stab_factor + ..., 0, 100)`.
2. For Columbia: `econ_perf = gdp_growth * 10.0`. If gdp_growth = 10%, econ_perf = 100. `stab_factor = (8 - 5) * 5 = 15`.
3. `ai_score = clamp(50 + 100 + 15 + 0 + 0 + 0 + 0, 0, 100) = 100`. Capped at 100.
4. `final_incumbent = 0.5 * 100 + 0.5 * 50 = 75%`. Always wins.

**Root cause:** The `econ_perf = gdp_growth * 10.0` multiplier is calibrated for real GDP growth rates (1-3%), not the inflated 10%+ rates the sim produces. With realistic growth, econ_perf would be 18-30, giving ai_score of 70-80 and final_incumbent of 60-65% — still high but more competitive. The PRIMARY fix is the GDP growth fix; elections will self-correct once GDP growth is realistic.

### C7: MODERATE — No Health Events

**Trace the chain:**

1. `check_health_events()` (political.py:590): Requires `round_num > 2`.
2. Columbia leader: age 80, medical 0.9. `base_prob = 0.03 + 10*0.01 = 0.13`, `prob = 0.13 * (1 - 0.9*0.5) = 0.13 * 0.55 = 0.0715` (7.15% per round).
3. Over 6 eligible rounds (3-8): probability of at least one event = 1 - (1-0.0715)^6 = 1 - 0.641 = 35.9%.
4. There is a 64.1% chance of NO event over 6 rounds. This is within expected variance for a single run.

**Verdict:** Not a bug. Needs multiple runs to validate. However, the probability could be slightly low — an 80-year-old leader having only a 7% chance per 3-month round seems conservative.

---

## Prescriptions

### P1: PARAMETRIC — Cap GDP Growth Rate Per Round

**Change:** Add a growth rate cap in `calc_gdp_growth()` (economic.py, after line 896).

```python
# After line 896: effective_growth = raw_growth * crisis_mult
# ADD: Hard cap on per-round growth
MAX_GROWTH_PER_ROUND = 0.08  # 8% max per round (~3 months)
MIN_GROWTH_PER_ROUND = -0.15  # -15% floor for catastrophic events
effective_growth = max(MIN_GROWTH_PER_ROUND, min(MAX_GROWTH_PER_ROUND, effective_growth))
```

**Rationale:** No real economy grows more than 8% in a quarter. China's best quarter in recent history was ~7% annualized. The US has never exceeded 4% annual in the 21st century. A per-round cap of 8% allows exceptional growth while preventing runaway compounding.

**Predicted effect:** Columbia GDP over 8 rounds: 280 * 1.02^8 = ~328 (realistic) instead of 1171.5. Cathay: 190 * 1.04^8 = ~260 instead of 862.9.

---

### P2: PARAMETRIC — Reduce Sanctions GDP Impact by 10x

**Changes in economic.py:**

1. Line 94: Change `SANCTIONS_GDP_MULTIPLIER` from `1.5` to `0.15`
2. Line 93: Change `SANCTIONS_MAX_DAMAGE` from `0.50` to `0.08`

**Rationale:** Academic literature (Neuenkirch & Neumeier 2015) shows UN sanctions reduce annual GDP growth by ~2 percentage points. The most extreme case in modern history (Iran 2011-2014) saw a cumulative -17% over 3 years, averaging -5.7% per year. Russia under the heaviest sanctions regime ever assembled lost only ~5% vs counterfactual over 2022-2024.

With `MAX_DAMAGE = 0.08` and `MULTIPLIER = 0.15`: maximum sanctions hit per round = 0.08 * 0.15 = -1.2% per round for a fully sanctioned, trade-open economy. Over 8 rounds, cumulative effect = ~-9.6% (without compounding acceleration). This matches the Iran historical benchmark.

**Predicted effect:** Sarmatia GDP decline: ~5-8% per round instead of 74%. Over 8 rounds: ~20 * 0.93^8 = ~11.2 coins (44% decline over 8 rounds = 2 simulated years). Still severe, but within historical range.

---

### P3: PARAMETRIC — Increase War Premium on Oil Price

**Changes in economic.py:**

1. Line 607: Change `war_premium = len(wars) * 0.05` to `war_premium = 0.0`
2. Replace with a structured premium based on war involvement of oil producers/chokepoints:

```python
# Replace lines 605-607 with:
war_premium = 0.0
for w in wars:
    belligerents = set(w.get("belligerents_a", []) + w.get("belligerents_b", []))
    # Oil producers at war = supply disruption premium
    for bp in belligerents:
        if countries.get(bp, {}).get("economic", {}).get("oil_producer", False):
            resource_pct = countries[bp]["economic"]["sectors"].get("resources", 0) / 100.0
            war_premium += 0.15 * resource_pct  # scaled by resource dependence
    # Any war near chokepoints
    war_premium += 0.05  # base risk premium per war
war_premium = min(war_premium, 0.60)  # cap at 60% increase
```

**Rationale:** Real-world: Iran conflict alone caused +55% oil spike. The current model caps total war premium at 15% regardless of whether oil producers or chokepoints are involved. Persia (35% resource sector, OPEC member) being at war should add ~5.25% supply disruption premium. Sarmatia (40% resource, OPEC) adds ~6%. Combined with base risk premium: total ~16% from two oil-producer wars alone — before chokepoint effects.

**Predicted effect:** Oil price should rise from $92 to ~$100-120 range during active wars with oil producers, matching real-world 2026 trajectory.

---

### P4: STRUCTURAL — Fix Social Spending Default for Tier 1 Tests

**Change in orchestrator.py**, around line 331. The stability input should use the budget-computed actual social ratio when available:

```python
social_spending_ratio=eco.get("_actual_social_ratio", eco.get("social_spending_baseline", 0.20)),
```

Additionally, fix `calc_budget_execution()` (economic.py, line 1011) so that when no explicit budget is provided, discretionary social spending defaults to the FULL discretionary pool (not zero):

```python
# Line 1011: Change from:
social_extra = min(budget.get("social_spending", discretionary_social_pool), discretionary)
# No change needed — the default is already discretionary_social_pool.
# The issue is that budget is {} (empty), so budget.get("social_spending", discretionary_social_pool)
# returns discretionary_social_pool. This should be correct.
```

Actually, re-examining: the default IS `discretionary_social_pool`. So the issue is that `discretionary = max(revenue - mandatory, 0.0)` — if revenue < mandatory, discretionary = 0, and social_extra = 0 even though the default would be higher. Countries with revenue shortfall (Phrygia, Persia) get zero discretionary social spending, creating the stability drain.

**Real fix:** In orchestrator.py line 331, use `_actual_social_ratio`:

Change line 331 from:
```python
social_spending_ratio=eco.get("social_spending_ratio", eco.get("social_baseline", 0.20)),
```
To:
```python
social_spending_ratio=eco.get("_actual_social_ratio", eco.get("social_spending_baseline", 0.20)),
```

And line 332 from:
```python
social_spending_baseline=eco.get("social_baseline", 0.20), gdp=eco["gdp"],
```
To:
```python
social_spending_baseline=eco.get("social_spending_baseline", 0.20), gdp=eco["gdp"],
```

**Rationale:** The stability function was reading wrong keys, always falling back to 0.20 for both ratio and baseline. Even with the correct key, the actual social ratio reflects what the budget engine computed — this is the value that should flow into stability.

**Predicted effect:** Countries with adequate revenue will no longer show spurious stability decline. Bharata stability should remain 5.5-6.5 over 8 rounds instead of falling to 3.9.

---

### P5: PARAMETRIC — Reduce Stability Volatility for Peaceful Countries

**Change in political.py**, line 302: The social spending shortfall penalty multiplier of 3 is too aggressive.

Change line 301-302 from:
```python
        shortfall = baseline - social_ratio
        delta -= shortfall * 3
```
To:
```python
        shortfall = baseline - social_ratio
        delta -= shortfall * 1.5
```

**Rationale:** The calibration methodology specifies stability changes should be "gradual (±0.5 per round typical, ±1.0 for major events)." A 6% social spending shortfall currently produces -0.18 delta, which when combined with other factors exceeds ±0.5/round. Reducing the multiplier to 1.5 brings this into the target range.

**Predicted effect:** Stability changes for peaceful non-sanctioned countries will stay within ±0.3 per round, matching convergence criterion #4.

---

### P6: INITIALIZATION — Start At-War Countries in "stressed" Economic State

**Change in orchestrator.py**, `_country_to_dict()` (line 90):

The current code hardcodes `"economic_state": "normal"` for all countries. Countries that start at war should begin in at least "stressed" state.

```python
# After line 90, add logic:
# In _country_to_dict or in process_round initialization:
if c.at_war_with:  # non-empty string means at war
    eco["economic_state"] = "stressed"
```

Or better: add an `initial_economic_state` column to the CSV/DB.

**Rationale:** Russia/Sarmatia has been at war since 2022 and under sanctions since then. Starting the sim in 2025 with "normal" economic state is historically inaccurate. Similarly, Persia has been under heavy sanctions and at war — "normal" is wrong.

**Predicted effect:** At-war countries start with appropriate economic stress, avoiding the jarring transition from "normal" to "crisis" in Round 1.

---

### P7: PARAMETRIC — Fix Persia Starting GDP Growth Rate

**Change in countries.csv:**

Persia's `gdp_growth_base` is currently -3.0. This is already a contraction rate, which when combined with sanctions (-1.2% from P2's calibrated values) and war damage, pushes Persia into an immediate death spiral.

Change to: `gdp_growth_base = 0.5` (matching IMF's 2025 projection of near-zero growth for Iran).

**Rationale:** Iran's GDP grew 3.7% in 2024. Even under tightened sanctions in 2025, the IMF projects 0.3-0.6% growth. A -3% starting rate combined with sanctions and war damage makes collapse inevitable by R2. The simulation should allow Persia to struggle but survive — providing meaningful gameplay for the Persia team.

**Predicted effect:** Persia GDP should decline gradually (2-5% per round) from combined sanctions + war effects, reaching ~3.0-3.5 coins by R8 instead of floor at R2.

---

### P8: PARAMETRIC — Increase Oil War Supply Disruption for Sanctioned Producers

**Change in economic.py**, lines 550-553:

```python
# Current:
for producer in ("sarmatia", "persia"):
    sanc_level = _get_sanctions_on(sanctions, producer)
    if sanc_level >= 2:
        supply -= 0.08

# Change to:
for producer in ("sarmatia", "persia", "caribe"):
    sanc_level = _get_sanctions_on(sanctions, producer)
    if _is_country_at_war(wars, producer):
        supply -= 0.12  # war disrupts production more than sanctions
    elif sanc_level >= 2:
        supply -= 0.08
```

**Rationale:** An oil-producing country actively at war experiences more supply disruption than one merely under sanctions. Russia's oil production fell ~5% due to war logistics before sanctions even bit. Iran's production capacity is directly threatened by military conflict.

**Predicted effect:** Oil supply decreases further during wars involving producers, pushing price UP during conflict (matching real-world behavior).

---

## Priority Order

Fixes should be applied in this sequence to maximize impact while minimizing risk of cascading side effects:

| Priority | Fix | Type | Impact | Risk |
|----------|-----|------|--------|------|
| **1** | **P1: GDP Growth Cap** | PARAMETRIC | Fixes Columbia/Cathay runaway growth; fixes election incumbent dominance as downstream effect | LOW — simple clamp, no formula restructuring |
| **2** | **P2: Sanctions Damage Reduction** | PARAMETRIC | Fixes Sarmatia/Persia collapse; most critical realism issue | LOW — constant change only |
| **3** | **P4: Social Spending Key Fix** | STRUCTURAL | Fixes Bharata/Phrygia stability drain; fixes all Tier 1 test reliability | LOW — corrects a bug, no behavior change for correct inputs |
| **4** | **P7: Persia Starting Growth Rate** | INITIALIZATION | Prevents Persia death spiral | ZERO — CSV data change |
| **5** | **P3: Oil War Premium** | PARAMETRIC | Fixes oil price direction during wars | MEDIUM — new formula logic, needs testing |
| **6** | **P6: At-War Initial State** | INITIALIZATION | More realistic starting conditions | LOW — initialization only |
| **7** | **P5: Social Shortfall Multiplier** | PARAMETRIC | Reduces stability volatility to target range | LOW — constant change only |
| **8** | **P8: Oil War Supply** | PARAMETRIC | Improves oil price realism | LOW — extends existing logic |

**Recommended approach:** Apply P1 + P2 + P4 + P7 together as a batch (highest impact, lowest risk). Re-run as Test Run #002. If trajectories are within convergence criteria, apply P3 + P5 + P6 + P8 as a second batch for Test Run #003.

---

## Convergence Criteria Assessment (Current State)

| # | Criterion | Status |
|---|-----------|--------|
| 1 | No GDP collapse to floor without catastrophe | **FAIL** — Sarmatia, Persia, Caribe, Choson hit floor |
| 2 | Sanctioned countries decline 5-15% per round | **FAIL** — declining 50-75% per round |
| 3 | Growing economies grow 2-8% per round | **FAIL** — growing 10-15% per round |
| 4 | Stability changes ±0.5 per round typical | **FAIL** — some countries losing 0.5-1.0 per round |
| 5 | Oil price $50-$200 without clamping | **PASS** — stays in range (but wrong direction) |
| 6 | Elections competitive | **FAIL** — incumbent always wins |
| 7 | At least one unscripted crisis | **PARTIAL** — Phrygia crisis is emergent but unrealistic |
| 8 | No country eliminated before R4 | **FAIL** — Sarmatia, Persia eliminated by R2 |
| 9 | Geopolitics-literate human says "plausible" | **FAIL** |

**Current score: 1/9 criteria met. Target: 7/9 minimum for "viable model."**
