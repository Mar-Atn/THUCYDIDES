# Calibration Memo — Run #004

**Analyst:** SUPER EXPERT (Cycle 4)
**Date:** 2026-04-01

---

## Executive Summary

Two bugs found. One is the ROOT CAUSE of Columbia's +36% growth. The other is a strong contributor to universal stability drift.

| Issue | Root cause | Location | Severity |
|-------|-----------|----------|----------|
| Columbia GDP +36% | Persistence layer overwrites `gdp_growth_base` with actual growth result every round | `orchestrator.py` line 194 | CRITICAL — nullifies the line 828 fix entirely |
| Universal stability drift | Debt burden grows every round via budget deficits, eating into revenue, creating larger deficits, printing money, raising inflation — a slow doom loop | `economic.py` lines 948, 1036, 1034 | HIGH — structural deficit for most countries |

---

## Issue 1: Columbia GDP +36% — The Persistence Bug

### The intended fix (line 828) is correct but NULLIFIED

`economic.py` line 828 correctly reads the structural base rate:
```python
base_growth = eco.get("gdp_growth_base", eco["gdp_growth_rate"]) / 100.0 / 2.0
```

But `orchestrator.py` line 194 writes BACK to the database:
```python
"gdp_growth_base": round(eco.get("gdp_growth_rate", 0), 4),
```

This saves the ACTUAL growth result (e.g., +4.5%) into the `gdp_growth_base` column. Next round, when the orchestrator loads from DB (line 75-76), both `gdp_growth_rate` and `gdp_growth_base` are set to last round's actual result. The "immutable structural rate" is being mutated every round.

### Tracing Columbia's math (round by round)

**Starting values:** GDP=280, gdp_growth_base=1.8, ai_level=3, oil_producer=true, stability=7

**Round 1:**
- base_growth = 1.8 / 100 / 2 = 0.009 (0.9% per half-year)
- tech_boost (ai_level=3) = 0.015 (from AI_LEVEL_TECH_FACTOR)
- momentum = 0.0 * 0.01 = 0.0 (starts at zero)
- oil_shock: oil_producer=true, oil_price=80 → 0.0 (price at baseline)
- No tariffs, sanctions, war, blockade, semi disruption
- raw_growth = 0.009 + 0.015 = 0.024 (2.4%)
- crisis_mult = 1.0 (normal state, positive growth)
- effective_growth = 0.024 → GDP = 280 * 1.024 = 286.72
- growth_pct = 2.4%

After R1: `gdp_growth_rate` = 2.4. Line 194 saves `gdp_growth_base` = 2.4 to DB.

**Momentum after R1:**
- gdp_growth=2.4 > 2 → boost += 0.15
- eco_state=normal → boost += 0.15
- stability=7 > 6 → boost += 0.15
- boost = 0.45, capped at MOMENTUM_BOOST_CAP = 0.3
- new_momentum = 0.0 + 0.3 = 0.3

**Round 2:**
- base_growth = 2.4 / 100 / 2 = 0.012 (was 0.009 — already inflated!)
- tech_boost = 0.015
- momentum_effect = 0.3 * 0.01 = 0.003
- oil: price ~96, oil_producer=true, price > 80 → oil_shock = 0.01 * (96-80)/50 = 0.0032
- raw_growth = 0.012 + 0.015 + 0.003 + 0.0032 = 0.0332 (3.32%)
- GDP = 286.72 * 1.0332 = 296.24
- Saves `gdp_growth_base` = 3.32 to DB.

**Momentum after R2:** gdp_growth=3.32>2, state=normal, stab>6 → boost=0.3
- new_momentum = 0.3 + 0.3 = 0.6

**Round 3:**
- base_growth = 3.32 / 100 / 2 = 0.0166
- tech_boost = 0.015
- momentum = 0.6 * 0.01 = 0.006
- oil: price ~107, producer, (107-80)/50*0.01 = 0.0054
- raw_growth = 0.0166 + 0.015 + 0.006 + 0.0054 = 0.043 (4.3%)
- GDP = 296.24 * 1.043 = 308.98
- Saves `gdp_growth_base` = 4.3 to DB.

**This pattern continues exponentially.** By round 8:
- base_growth itself is ~3% per half-year (was 0.9%)
- momentum reaches 1.5-2.0 (contributing +1.5-2.0% per round)
- tech boost is constant +1.5%
- oil revenue bonus adds ~0.5%

Total growth per round reaches ~5-6%, giving 280 → 381 over 8 rounds. **The feedback loop through the persistence layer is the primary cause.**

### The fix

**One-line fix in `orchestrator.py` line 194:**

```python
# BEFORE (bug):
"gdp_growth_base": round(eco.get("gdp_growth_rate", 0), 4),

# AFTER (fix):
"gdp_growth_base": round(eco.get("gdp_growth_base", eco.get("gdp_growth_rate", 0)), 4),
```

This preserves the original structural base rate through the persistence cycle. The value loaded at line 76 (`gdp_growth_base`) flows through unchanged, rather than being overwritten by the actual growth result.

**Expected impact:** Columbia's per-round growth drops from ~5-6% to ~2.4% (base 0.9% + tech 1.5% + momentum effect). Over 8 rounds: 280 * 1.024^8 = 339 (+21%). Still high due to momentum stacking (see Issue 1b below).

---

## Issue 1b: Momentum Stacking (secondary growth amplifier)

Even after the persistence fix, momentum accumulates +0.3/round indefinitely for any country that:
- Has GDP growth > 2% (boost +0.15)
- Is in normal economic state (boost +0.15)
- Has stability > 6 (boost +0.15)

All three are trivially true for Columbia. After 8 rounds: momentum = 0.3 * 8 = 2.4, capped at MOMENTUM_CEILING=5.0. Momentum effect = 2.4 * 0.01 = 0.024 = +2.4% per round.

**The problem:** Momentum has no natural DECAY. It only goes down on crashes. A peacetime superpower accumulates +0.3/round every round. By round 8, momentum alone contributes more growth than the structural base rate.

### Proposed systemic fix: Add momentum decay

```python
# In update_momentum(), after boost/crash calculation:
# Natural decay: momentum regresses toward zero by 10% per round
decay = -old_m * 0.10
new_m = clamp(old_m + boost + crash + decay, MOMENTUM_FLOOR, MOMENTUM_CEILING)
```

This creates a natural equilibrium: at steady state, +0.3 boost = 0.10 * m → m_eq = 3.0 (contributing +3% growth). But it takes ~15 rounds to approach that, vs. the current 10 rounds to hit 3.0. More importantly, a country that loses one positive signal (e.g., stability drops below 6) sees momentum start decaying.

**Alternative:** Reduce MOMENTUM_BOOST_CAP from 0.3 to 0.15 (simpler, but doesn't solve the "no decay" structural issue).

**Recommended:** Apply BOTH the persistence fix AND momentum decay. They address different problems.

---

## Issue 2: Universal Stability Drift — The Deficit-Inflation Doom Loop

### Tracing Gallia step by step

**Starting values:** GDP=34, stability=7, tax_rate=0.45, inflation=2.5, debt_burden=3, social_baseline=0.35, maintenance_per_unit=0.50, total_military_units=14 (6+1+4+2+1), ai_level=2, democracy, no war, no sanctions.

**Round 1 Budget:**
- Revenue = GDP * tax_rate - debt = 34 * 0.45 - 3 = 15.3 - 3 = 12.3
- Maintenance = 14 units * 0.50 = 7.0
- Social spending = 0.35 * 34 * 1.0 = 11.9 (100% of baseline)
- Mandatory total = 7.0 + 11.9 = 18.9
- **Revenue (12.3) < Mandatory (18.9) → DEFICIT = 6.6**
- Treasury = 8.0, covers 6.6 → treasury drops to 1.4, no money printing yet

**Round 2 Budget:**
- GDP barely grew (maybe 34.3 with persistence bug giving slightly higher base)
- Revenue ~ 34.3 * 0.45 - 3 = 12.44
- Same maintenance = 7.0, social = 12.0
- Mandatory = 19.0, Revenue = 12.44 → DEFICIT = 6.56
- Treasury = 1.4, can cover 1.4 → money_printed = 5.16
- Inflation += 5.16 / 34.3 * 80 = +12.0%!
- debt_burden += 6.56 * 0.15 = +0.98 → debt_burden = 3.98

**Round 3 Budget:**
- Revenue ~ 34.5 * 0.45 - 3.98 = 11.55 (lower! debt grew)
- Maintenance still 7.0, social still ~12.1
- DEFICIT = ~7.55, treasury = 0, money_printed = 7.55
- Inflation += 7.55 / 34.5 * 80 = +17.5%!
- debt_burden += 7.55 * 0.15 = +1.13 → debt_burden = 5.11

### How this drives stability down

After round 3, Gallia's inflation has risen from 2.5 to ~28% (2.5 baseline + accumulated printing). The stability formula at line 340:

```python
inflation_delta = inp.inflation - inp.starting_inflation
```

**BUT** — `starting_inflation` in the orchestrator is set at DB load time (line 84) to the current inflation in the DB. The economic engine then updates inflation during processing. So `starting_inflation` = inflation at round start, and `inp.inflation` = inflation after this round's budget execution.

If money printing adds +15% inflation in one round, then `inflation_delta` = 15.
- (15 - 3) * 0.05 = -0.60
- Capped at -0.50 (line 346)

**Combined with peaceful dampening (line 361):** if delta < 0, delta *= 0.5. So -0.50 becomes -0.25 after dampening.

But stability also gets social bonus +0.05 and inertia +0.05 (while above 7).

Net per round: +0.10 - 0.25 = -0.15/round once the deficit spiral starts.

As debt grows and revenue falls further, the deficit worsens every round, printing MORE money, creating HIGHER inflation, and the stability penalty increases until it hits the -0.50 cap every round. After enough rounds:

Net = +0.05 (social) + 0 (no inertia below 7) - 0.25 (inflation after dampening) = -0.20/round

Over 8 rounds: 7.0 - (varies) = ~4.1. This matches Gallia's observed 7 → 4.1.

### The root cause: STRUCTURAL BUDGET DEFICIT AT START

Gallia starts with:
- Revenue: 34 * 0.45 - 3 = **12.3 coins**
- Mandatory: 14 * 0.50 + 0.35 * 34 = 7.0 + 11.9 = **18.9 coins**
- **Starting deficit: 6.6 coins/round (54% of revenue!)**

This violates Marat's directive: "Budget must be balanced at start: revenue > maintenance + social + some discretionary."

The same problem affects most countries. Here's the starting balance for all:

| Country | Revenue | Maintenance | Social | Mandatory | Balance |
|---------|---------|-------------|--------|-----------|---------|
| Columbia | 280*0.24-5=62.2 | 64*0.17=10.9 | 0.30*280=84 | 94.9 | **-32.7** |
| Cathay | 190*0.20-2=36 | 52*0.30=15.6 | 0.20*190=38 | 53.6 | **-17.6** |
| Gallia | 34*0.45-3=12.3 | 14*0.50=7.0 | 0.35*34=11.9 | 18.9 | **-6.6** |
| Teutonia | 45*0.38-2=15.1 | 11*0.40=4.4 | 0.30*45=13.5 | 17.9 | **-2.8** |
| Yamato | 43*0.28-2=10.0 | 18*0.35=6.3 | 0.25*43=10.75 | 17.05 | **-7.05** |

**EVERY major country starts in structural deficit.** Social baseline percentages are too high relative to tax rates. The model cannot balance.

### Why some countries are stable (Teutonia 7→7.8, Mirage 8→8.8)

Teutonia's deficit is small (-2.8), and treasury=12 covers ~4 rounds before printing starts. By then, GDP growth (especially with the inflated base rate bug) has raised revenue enough to close the gap. Countries with small deficits and large treasuries survive; countries with large deficits and small treasuries collapse.

---

## Proposed Fixes (systemic, not caps)

### Fix 1: Persistence bug (CRITICAL — one-line fix)

**File:** `/app/engine/engines/orchestrator.py` line 194

```python
# Change from:
"gdp_growth_base": round(eco.get("gdp_growth_rate", 0), 4),
# Change to:
"gdp_growth_base": round(eco.get("gdp_growth_base", eco.get("gdp_growth_rate", 0)), 4),
```

**Impact:** Eliminates the growth rate feedback loop. Columbia's base rate stays at 1.8% (= 0.9% per half-year) for the entire simulation.

**Risk:** None. This is a pure bug fix restoring intended behavior.

### Fix 2: Momentum decay (systemic improvement)

**File:** `/app/engine/engines/economic.py` in `update_momentum()` around line 1361

Add natural decay before the clamp:
```python
# Natural regression: 10% decay toward zero per round
decay = -old_m * 0.10
new_m = clamp(old_m + boost + crash + decay, MOMENTUM_FLOOR, MOMENTUM_CEILING)
```

**Impact:** Momentum equilibrium at ~3.0 instead of accumulating to 5.0. Growth for stable superpowers drops from ~6%/round to ~4%/round in late game.

**Risk:** Low. Decay is gentle (10%). Countries in trouble already have crash signals that dominate.

### Fix 3: Balance starting budgets (data fix)

Two options:

**Option A: Reduce social_baseline across all countries**

Current baselines are 20-35% of GDP. Real-world social spending for developed nations is 15-25% of GDP, but that INCLUDES tax revenue recycling. In TTT, tax_rate * GDP = total revenue, and social spending comes OUT of that. So social_baseline should be a fraction of REVENUE, not GDP.

Proposed recalibration: Set `social_baseline` so that mandatory spending (maintenance + social) = 70% of revenue, leaving 30% discretionary.

| Country | Revenue | Target mandatory (70%) | Maintenance | Max social | New baseline |
|---------|---------|----------------------|-------------|------------|-------------|
| Columbia | 62.2 | 43.5 | 10.9 | 32.6 | 32.6/280 = **0.117** |
| Cathay | 36 | 25.2 | 15.6 | 9.6 | 9.6/190 = **0.050** |
| Gallia | 12.3 | 8.6 | 7.0 | 1.6 | 1.6/34 = **0.047** |
| Teutonia | 15.1 | 10.6 | 4.4 | 6.2 | 6.2/45 = **0.138** |

Problem: This makes social spending unrealistically low for some countries. Gallia spending 4.7% of GDP on social = unrealistic for France.

**Option B: Redefine social_baseline as % of revenue (not GDP)**

Change the budget formula so that social_base_coins = social_baseline_pct * REVENUE instead of social_baseline_pct * GDP. This way, social spending automatically scales with what the country can afford.

```python
# economic.py line 1005, change from:
social_base_coins = social_baseline_pct * eco["gdp"]
# to:
social_base_coins = social_baseline_pct * revenue
```

With social_baseline = 0.50 (50% of revenue goes to social), Gallia gets:
- Revenue = 12.3, social = 6.15, maintenance = 7.0
- Mandatory = 13.15, deficit = 0.85 (manageable with treasury)

**This is the recommended approach.** It means "social baseline" = what fraction of the government's income goes to social programs (50-60% is realistic for European welfare states). The political penalty kicks in when a player CUTS below this share.

Set baseline values: democracies 0.50, autocracies 0.35, hybrids 0.40.

**Option C: Raise tax rates to balance budgets**

Rejected — tax rates are already set to match real-world parallels.

### Fix 4 (optional): Debt service deduction should be SEPARATE from revenue

Currently (line 948-964), `debt_burden` is subtracted from revenue as a flat cost. As debt grows, revenue falls, creating larger deficits, creating more debt — a vicious cycle. Consider making debt service proportional: `debt_service = debt_burden * 0.05` (5% interest on accumulated debt) rather than the full debt_burden being deducted every round.

Current code: `revenue = base_rev + oil_rev - debt - ...` where `debt` = full `debt_burden`.
This means ALL accumulated debt is deducted every round. A country that once had a 10-coin deficit now permanently loses 1.5 coins/round from revenue (10 * 0.15 = 1.5 added to debt_burden, which is then subtracted from revenue every round).

**Proposed:** `debt_service = debt_burden * DEBT_INTEREST_RATE` (e.g., 0.05), deducted from revenue instead of the full debt_burden.

---

## Priority and Sequencing

| Priority | Fix | Effort | Impact |
|----------|-----|--------|--------|
| 1 | Persistence bug (line 194) | 1 line | Fixes Columbia +36%, fixes growth feedback for ALL countries |
| 2 | Social baseline as % of revenue | 1 line formula + seed data update | Eliminates structural deficits, fixes stability drift |
| 3 | Momentum decay | 2 lines | Prevents late-game growth explosion |
| 4 | Debt service reform | 3 lines | Stops debt doom loop; optional if Fix 2 works |

**Recommendation:** Apply fixes 1-3 for run #005. Fix 4 is insurance if the deficit spiral persists after Fix 2.

---

## Verification Plan

After applying fixes, run #005 should show:
- Columbia GDP growth: 280 → ~330 (+18%) over 8 rounds — not +36%
- Gallia stability: 7 → 6.5-7.0 (slight drift or stable) — not 4.1
- No country should have >15% inflation by round 8 in a peacetime baseline scenario
- Budget deficit for all countries should be <15% of revenue in round 1

---

## Reference: Exact file locations

| File | Lines | What |
|------|-------|------|
| `app/engine/engines/orchestrator.py` | 194 | **BUG:** gdp_growth_base overwritten with actual growth |
| `app/engine/engines/orchestrator.py` | 75-76 | Loads gdp_growth_base from DB (correct) |
| `app/engine/engines/economic.py` | 828 | Reads gdp_growth_base (correct, but input is wrong) |
| `app/engine/engines/economic.py` | 1005 | Social spending = baseline_pct * GDP (should be * revenue) |
| `app/engine/engines/economic.py` | 948 | Full debt_burden deducted from revenue (too aggressive) |
| `app/engine/engines/economic.py` | 1036 | Deficit adds to debt_burden (compounds with line 948) |
| `app/engine/engines/economic.py` | 1312-1373 | Momentum: no decay, accumulates to ceiling |
| `app/engine/engines/economic.py` | 86 | AI_LEVEL_TECH_FACTOR: level 3 = +1.5%/round |
| `app/engine/engines/political.py` | 265-381 | Stability formula (correct, but receives inflated inputs) |
| `3 DETAILED DESIGN/DET_B3_SEED_DATA.sql` | 58-64 | Starting country parameters |
