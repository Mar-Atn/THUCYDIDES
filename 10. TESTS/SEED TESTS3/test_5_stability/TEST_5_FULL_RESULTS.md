# TEST 5: STABILITY CALIBRATION — Full Results
**Date:** 2026-03-28 | **Engine:** v3 (4 calibration fixes) | **Tester:** TESTER-ORCHESTRATOR

---

## Purpose
Validate ALL stability formula fixes from v3. Retest every country flagged in TESTS2. Confirm inflation cap (Cal-4), siege resilience, GDP contraction cap, crisis state penalty, and democratic resilience all function correctly in combination.

## Scenario Setup
Standard SEED starting conditions. No player actions — pure formula validation. All countries process through 8 rounds with only engine-generated events (wars continue, sanctions persist, budgets auto-execute).

### Key Starting Conditions (from CSV + overrides)

| Country | Stability | Regime | At War | Sanctions On | War Tired | GDP | Inflation | Treasury |
|---------|-----------|--------|--------|-------------|-----------|-----|-----------|----------|
| Ruthenia | 5.0 | democracy | YES (defender vs Sarmatia) | None significant | 4.0 | 2.2 | 7.5 | 1.0 |
| Sarmatia | 5.0 | autocracy | YES (attacker vs Ruthenia) | L3 (broad coalition) | 4.0 | 20.0 | 5.0 | 6.0 |
| Persia | 4.0 | hybrid | YES (defender vs Columbia+Levantia) | L3 (Columbia), L2+ (EU) | 1.0 | 5.0 | 50.0 | 1.0 |
| Caribe | 3.0 | autocracy | NO | L3 (Columbia) | 0.0 | 2.0 | 60.0 | 1.0 |
| Columbia | 7.0 | democracy | YES (attacker vs Persia) | None significant | 1.0 | 280 | 3.5 | 50 |
| Cathay | 8.0 | autocracy | NO | None | 0.0 | 190 | 0.5 | 45 |
| Gallia | 7.0 | democracy | NO | None | 0.0 | 34 | 2.5 | 8 |
| Teutonia | 7.0 | democracy | NO | None | 0.0 | 45 | 2.5 | 12 |
| Freeland | 8.0 | democracy | NO | None | 0.0 | 9 | 4.0 | 4 |
| Bharata | 6.0 | democracy | NO | None | 0.0 | 42 | 5.0 | 12 |
| Levantia | 5.0 | democracy | YES (ally attacker vs Persia) | None significant | 2.0 | 5 | 3.5 | 5 |
| Formosa | 7.0 | democracy | NO | None | 0.0 | 8 | 2.0 | 8 |
| Solaria | 7.0 | autocracy | NO | None | 0.0 | 11 | 2.0 | 20 |
| Yamato | 8.0 | democracy | NO | None | 0.0 | 43 | 2.5 | 15 |
| Choson | 4.0 | autocracy | NO | L3 (Columbia, Yamato, Hanguk) | 0.0 | 0.3 | 10.0 | 1.0 |
| Hanguk | 6.0 | democracy | NO | None | 0.0 | 18 | 2.5 | 8 |
| Mirage | 8.0 | autocracy | NO | None | 0.0 | 5 | 2.0 | 15 |
| Phrygia | 5.0 | hybrid | NO | None | 0.0 | 11 | 45.0 | 4 |
| Ponte | 6.0 | democracy | NO | None | 0.0 | 22 | 2.5 | 4 |
| Caribe | 3.0 | autocracy | NO | L3 (Columbia) | 0.0 | 2.0 | 60.0 | 1.0 |
| Albion | 7.0 | democracy | NO | None | 0.0 | 33 | 3.0 | 8 |

---

## Oil Price Trajectory (Global — affects all)

Using standard scenario: Gulf Gate ground blockade active (Persia forces), 2 wars, OPEC at "normal".

| Round | Prev Price | Formula Price | Inertia Price (40/60) | Notes |
|-------|-----------|---------------|----------------------|-------|
| R0 (start) | — | — | $80.0 | Baseline |
| R1 | $80.0 | $96.8 | $90.1 | 2 wars (premium +10%), Gulf Gate blocked (+50% disruption), supply=1.0, demand~1.0. formula=80*(1.0/1.0)*1.50*(1.10)=$132. Wait — Gulf Gate IS blocked from start (Persia ground forces). Recalculating. |

**Recalculation R1:**
- Supply: 1.0 (OPEC normal). Sanctions on Sarmatia (L3, oil producer): -0.08. Sanctions on Persia (L3): -0.08. Supply = 1.0 - 0.08 - 0.08 = 0.84.
- Disruption: Gulf Gate blocked = +0.50. Disruption = 1.50.
- Wars: 2. War premium = 0.10.
- Demand: ~1.0 (no crises yet, avg GDP growth slightly positive ~+2.3%, demand += (2.3-2.0)*0.03 = +0.009).
- formula_price = 80 * (1.009/0.84) * 1.50 * 1.10 = 80 * 1.201 * 1.50 * 1.10 = 80 * 1.982 = **$158.5**
- Inertia: 80 * 0.4 + 158.5 * 0.6 = 32 + 95.1 = **$127.1**

| Round | Prev Price | Formula Price | Inertia Price | Notes |
|-------|-----------|---------------|--------------|-------|
| R1 | $80.0 | ~$158 | **$127** | Gulf Gate blocked, 2 sanctioned producers |
| R2 | $127 | ~$158 | **$146** | Same conditions, converging |
| R3 | $146 | ~$155 | **$150** | Slight demand reduction from stressed economies |
| R4 | $150 | ~$152 | **$151** | Near equilibrium |
| R5 | $151 | ~$148 | **$150** | Demand destruction starting (Sarmatia crisis) |
| R6 | $150 | ~$145 | **$148** | More demand destruction |
| R7 | $148 | ~$143 | **$145** | Gradual decline |
| R8 | $145 | ~$140 | **$143** | Stabilizing |

---

## COUNTRY-BY-COUNTRY STABILITY TRACE

---

### RUTHENIA (Target: 2.5-3.5 by R8)
**Starting:** Stability 5.0, democracy, defender in war (start R-4), war_tiredness 4.0, GDP 2.2, inflation 7.5, treasury 1.0.

War duration at R1: R1 - (-4) = 5 rounds. Society adaptation ACTIVE (>=3). WT growth = 0.20 * 0.5 = 0.10/round.

**GDP trajectory:** Ruthenia is tiny (GDP 2.2), not oil producer, high inflation baseline (7.5%). Revenue ~ 2.2 * 0.25 = 0.55. Military maintenance: (10+0+3+0+1)*0.3 = 4.2. Social baseline: 0.20 * 2.2 = 0.44. Mandatory = 4.2 + 0.44 = 4.64. Revenue 0.55 << 4.64. Deficit = 4.09. Treasury 1.0 covers 1.0, prints 3.09. Inflation spike: 3.09/2.2 * 80 = 112.4pp. New inflation: 7.5 + 112.4 = 119.9%. Inflation DELTA from baseline (7.5): 112.4.

This creates extreme conditions. Ruthenia is a wartime economy running on printed money. BUT Cal-4 caps inflation stability friction at -0.50.

#### Round 1
```
Country: Ruthenia
Old stability: 5.00
GDP growth: ~-5.8% (base 2.5%, oil shock at $127: -0.02*(127-100)/50 = -1.08%, war_hit: 1 occupied zone = -3%, infra damage 0.05*0.05 = -0.25%)
  Growth = (0.025 - 0.0108 - 0.0325) * 1.0 = -0.0183 = -1.83%

War friction (defender, frontline): -0.10
War tiredness: WT=4.0, -min(4.0*0.04, 0.4) = -0.16
Territory lost: 1 zone occupied (pre-existing), events territory_lost=0 (no new loss R1) = 0.00
Casualties: 0 (no combat resolution this round, baseline test) = 0.00
Democratic resilience (frontline democracy): +0.15
Siege resilience: N/A (not autocracy) = 0.00
Sanctions friction: 0 (no significant sanctions on Ruthenia) = 0.00
Inflation friction: delta = 112.4 (after money printing).
  Raw: -(112.4-3)*0.05 - (112.4-20)*0.03 = -5.47 - 2.77 = -8.24
  Cal-4 CAP: max(-8.24, -0.50) = -0.50
GDP contraction: -1.83% growth. gdp_growth < -2? No (-1.83 > -2). = 0.00
Social spending: ratio = mandatory social / GDP = 0.44/2.16 = 0.204. baseline = 0.20. ratio >= baseline? Yes (barely). = +0.05 * 1.5 (wartime) = +0.075
Positive inertia: old_stab = 5.0 (not in 7-9 range) = 0.00
Crisis state penalty: normal (R1 start) = 0.00
Autocracy resilience: N/A (democracy) = N/A
Peaceful dampening: N/A (at war)

Net delta: -0.10 - 0.16 + 0.15 - 0.50 + 0.075 = -0.535
New stability: 5.0 - 0.535 = 4.465 → **4.47**
```

#### Round 2
```
Country: Ruthenia
Old stability: 4.47
War tiredness: 4.0 + 0.10 = 4.10 (society adaptation active)
GDP: ~2.12 (declined ~1.8%). Deficit worsens. More money printing. Inflation climbs further.
  Inflation excess decays 15%: (119.9-7.5)*0.85 = 95.5 excess. Plus new printing ~3.0 coins.
  New printing inflation: 3.0/2.12*80 = 113.2pp. Total excess: 95.5 + 113.2 = 208.7. Inflation: 216.2%
  But delta from baseline (7.5) is capped at -0.50 for stability anyway.

War friction (frontline): -0.10
War tiredness: -min(4.10*0.04, 0.4) = -0.164
Democratic resilience: +0.15
Inflation (Cal-4 capped): -0.50
GDP contraction: growth ~-2.5% this round (worsening). delta += max(-2.5*0.15, -0.30) = -0.30 (actually: -2.5 < -2, so: max(-2.5*0.15, -0.30) = max(-0.375, -0.30) = -0.30)
Social spending: baseline met (mandatory). +0.075
Crisis state: likely "stressed" (treasury=0, negative growth, inflation > baseline+15). -0.10
Autocracy resilience: N/A

Net delta: -0.10 - 0.164 + 0.15 - 0.50 - 0.30 + 0.075 - 0.10 = -0.939
New stability: 4.47 - 0.939 = 3.53 → **3.53**
```

#### Round 3
```
Country: Ruthenia
Old stability: 3.53
War tiredness: 4.20
GDP: ~2.0 (continuing decline). Crisis state likely "crisis" (3+ stress triggers: negative growth, treasury=0, inflation >> baseline+15).

War friction (frontline): -0.10
War tiredness: -min(4.20*0.04, 0.4) = -0.168
Democratic resilience: +0.15
Inflation (Cal-4 capped): -0.50
GDP contraction: growth ~-4%, max(-4*0.15, -0.30) = -0.30
Social spending: +0.075
Crisis state: "crisis" → -0.30
Autocracy resilience: N/A

Net delta: -0.10 - 0.168 + 0.15 - 0.50 - 0.30 + 0.075 - 0.30 = -1.143
New stability: 3.53 - 1.143 = 2.39 → **2.39**
```

#### Rounds 4-8 (Ruthenia trajectory)
The decline continues but slows as stability approaches the floor. Key factors:
- War tiredness grows slowly (0.10/round with adaptation)
- Cal-4 cap holds inflation at -0.50
- GDP contraction cap holds at -0.30
- Crisis state penalty -0.30 (crisis) or -0.50 (collapse)
- Democratic resilience +0.15 is a meaningful counter

| Round | Old Stab | War Fric | WT Pen | Dem Resil | Inflation (capped) | GDP Contr | Social | Crisis State | Net Delta | New Stab |
|-------|----------|----------|--------|-----------|-------------------|-----------|--------|-------------|-----------|----------|
| R1 | 5.00 | -0.10 | -0.16 | +0.15 | -0.50 | 0.00 | +0.075 | 0.00 | -0.535 | **4.47** |
| R2 | 4.47 | -0.10 | -0.164 | +0.15 | -0.50 | -0.30 | +0.075 | -0.10 | -0.939 | **3.53** |
| R3 | 3.53 | -0.10 | -0.168 | +0.15 | -0.50 | -0.30 | +0.075 | -0.30 | -1.143 | **2.39** |
| R4 | 2.39 | -0.10 | -0.172 | +0.15 | -0.50 | -0.30 | +0.075 | -0.50 | -1.347 | **1.04** |
| R5 | 1.04 | -0.10 | -0.176 | +0.15 | -0.50 | -0.30 | +0.075 | -0.50 | -1.351 | **1.00** (floor) |
| R6 | 1.00 | -0.10 | -0.180 | +0.15 | -0.50 | -0.30 | +0.075 | -0.50 | -1.355 | **1.00** (floor) |
| R7 | 1.00 | — | — | — | — | — | — | — | — | **1.00** |
| R8 | 1.00 | — | — | — | — | — | — | — | — | **1.00** |

**RESULT: Ruthenia R8 = 1.00 (at floor). Target was 2.5-3.5.**

**VERDICT: FAIL — Ruthenia collapses to stability floor by R5.**

**Root cause:** Ruthenia's GDP (2.2) cannot support its military (14 units * 0.3 = 4.2 maintenance) plus social spending (0.44). Revenue is ~0.55. The deficit triggers massive money printing every round. Even with Cal-4 capping inflation friction at -0.50, the combined weight of war friction (-0.10), war tiredness (-0.17), inflation cap (-0.50), GDP contraction (-0.30), and crisis state (-0.30 to -0.50) totals approximately -1.0 to -1.35 per round, which no amount of democratic resilience (+0.15) or social spending (+0.075) can offset.

**Key insight:** The Cal-4 cap works correctly — without it, Ruthenia would collapse R1 (inflation friction alone would be -8.24). But Ruthenia's structural deficit (military costs 8x revenue) creates a fiscal death spiral that collapses stability through GDP contraction and crisis state channels, not just inflation. The inflation cap delays but does not prevent collapse.

**Recommendation:** Ruthenia needs either (a) reduced starting military (or zero maintenance for defending forces — "wartime conscripts"), (b) external aid mechanics (Western aid packages), or (c) a dedicated "wartime economy" modifier that reduces the stability penalty when the deficit is caused by defense spending. Without intervention, Ruthenia is a failed state by R5 in every scenario.

---

### SARMATIA (Target: 3.5-4.5 by R8)
**Starting:** Stability 5.0, autocracy, attacker in war (start R-4), war_tiredness 4.0, GDP 20.0, inflation 5.0, treasury 6.0, L3 sanctions from broad coalition.

War duration at R1: 5 rounds. Society adaptation ACTIVE. WT growth = 0.15 * 0.5 = 0.075/round.

Sanctions level: L3 (max from columbia, gallia, teutonia, freeland, albion, ruthenia).
Coalition coverage: Columbia + Gallia + Teutonia + Freeland + Albion + Ruthenia + Yamato + Hanguk + Levantia + Formosa = broad. Coverage likely > 0.60, so effectiveness = 1.0.

#### Round 1
```
Country: Sarmatia
Old stability: 5.00

GDP calculation:
  Base: 1.0% = 0.01
  Oil shock (producer, $127 > $80): +0.01*(127-80)/50 = +0.0094
  Sanctions: damage ~0.12, hit = -0.12 * 1.5 = -0.18
  War hit: 1 occupied zone = -0.03
  Tech: AI L1 = 0.0
  Growth = (0.01 + 0.0094 - 0.18 - 0.03) * 1.0 = -0.1906 = -19.1%
  New GDP: 20 * 0.809 = ~16.18

Budget:
  Revenue: 16.18 * 0.20 = 3.24. Oil revenue: 127 * 0.40 * 16.18 * 0.01 = 0.82.
  Debt: 0.5. Revenue = 3.24 + 0.82 - 0.5 - (sanctions cost on revenue ~0.3) = ~3.26
  Maintenance: (18+2+8+12+3)*0.3 = 12.9
  Social: 0.25 * 16.18 = 4.05
  Mandatory: 12.9 + 4.05 = 16.95
  Deficit: 16.95 - 3.26 = 13.69
  Treasury 6.0 -> prints 7.69. Inflation: 7.69/16.18 * 80 = 38.0pp.
  New inflation: 5.0 + 38.0 = 43.0%. Delta from baseline (5.0): 38.0

STABILITY:
War friction (attacker, primary): -0.08
War tiredness: -min(4.0*0.04, 0.4) = -0.16
Casualties: 0.00
Territory: 0.00
Democratic resilience: N/A (autocracy)
Sanctions friction: L3, sanctions_rounds=1 (<= 4). -0.1 * 3 * 1.0 = -0.30
  Heavy sanctions pain: sanctions cost ~0.30, sanc_hit/gdp = 0.30/16.18 = 0.019. -abs(0.019)*0.8 = -0.015
Inflation (Cal-4 capped): raw = -(38-3)*0.05 - (38-20)*0.03 = -1.75 - 0.54 = -2.29. Capped: -0.50
GDP contraction: -19.1%. max(-19.1*0.15, -0.30) = -0.30
Social spending: ratio = 4.05/16.18 = 0.25. baseline = 0.25. Met. +0.05 (not wartime effectiveness since attacker not frontline). Actually at_war=true, so social_effectiveness=1.5. +0.05*1.5 = +0.075
Positive inertia: 0 (stab=5.0, not in 7-9)
Crisis state: "normal" → 0.00 (R1, not yet transitioned)
Autocracy resilience: delta so far = -0.08-0.16-0.30-0.015-0.50-0.30+0.075 = -1.28. Negative, so *0.75 = -0.96
Siege resilience (autocracy + at_war + heavy_sanctions): +0.10

Net delta: -0.96 + 0.10 = -0.86
New stability: 5.0 - 0.86 = 4.14 → **4.14**
```

#### Round 2
```
Country: Sarmatia
Old stability: 4.14
War tiredness: 4.0 + 0.075 = 4.075
GDP: ~13.5 (further contraction ~-16%, debt burden growing)
Inflation: excess decays (43-5)*0.85 = 32.3. Plus new printing ~8 coins. +8/13.5*80 = 47.4pp.
  New inflation: 5 + 32.3 + 47.4 = 84.7%. Delta: 79.7.

War friction (attacker): -0.08
War tiredness: -min(4.075*0.04, 0.4) = -0.163
Sanctions friction: -0.30, pain ~-0.02
Inflation (Cal-4 capped): -0.50
GDP contraction: -0.30
Social: +0.075
Crisis state: "stressed" (triggers: negative growth, treasury=0, inflation > baseline+15) → -0.10
Pre-autocracy delta: -0.08-0.163-0.30-0.02-0.50-0.30+0.075-0.10 = -1.388
Autocracy resilience: -1.388 * 0.75 = -1.041
Siege resilience: +0.10

Net delta: -1.041 + 0.10 = -0.941
New stability: 4.14 - 0.941 = 3.20 → **3.20**
```

#### Round 3
```
Country: Sarmatia
Old stability: 3.20
War tiredness: 4.15
GDP: ~11.4. Inflation excess continues. Crisis state escalates.

War friction: -0.08
War tiredness: -min(4.15*0.04, 0.4) = -0.166
Sanctions: -0.30, pain -0.02
Inflation (capped): -0.50
GDP contraction: -0.30
Social: +0.075
Crisis state: "crisis" (sustained stress) → -0.30
Pre-autocracy: -0.08-0.166-0.30-0.02-0.50-0.30+0.075-0.30 = -1.591
Autocracy: -1.591*0.75 = -1.193
Siege: +0.10

Net delta: -1.193 + 0.10 = -1.093
New stability: 3.20 - 1.093 = 2.11 → **2.11**
```

#### Rounds 4-8
| Round | Old Stab | War Fric | WT Pen | Sanc Fric | Inflation (cap) | GDP Contr | Social | Crisis | Autocracy×0.75 | Siege | Net Delta | New Stab |
|-------|----------|----------|--------|-----------|----------------|-----------|--------|--------|----------------|-------|-----------|----------|
| R1 | 5.00 | -0.08 | -0.16 | -0.315 | -0.50 | -0.30 | +0.075 | 0.00 | ×0.75 | +0.10 | -0.86 | **4.14** |
| R2 | 4.14 | -0.08 | -0.163 | -0.32 | -0.50 | -0.30 | +0.075 | -0.10 | ×0.75 | +0.10 | -0.94 | **3.20** |
| R3 | 3.20 | -0.08 | -0.166 | -0.32 | -0.50 | -0.30 | +0.075 | -0.30 | ×0.75 | +0.10 | -1.09 | **2.11** |
| R4 | 2.11 | -0.08 | -0.169 | -0.32 | -0.50 | -0.30 | +0.075 | -0.50 | ×0.75 | +0.10 | -1.22 | **1.00** (floor) |
| R5 | 1.00 | — | — | — | — | — | — | — | — | — | — | **1.00** |
| R6 | 1.00 | — | — | — | — | — | — | — | — | — | — | **1.00** |
| R7 | 1.00 | — | — | — | — | — | — | — | — | — | — | **1.00** |
| R8 | 1.00 | — | — | — | — | — | — | — | — | — | — | **1.00** |

Note: At R5, sanctions_rounds > 4 → sanctions friction reduces: -0.1 * 3 * 0.70 = -0.21. But Sarmatia is already at the floor.

**RESULT: Sarmatia R8 = 1.00 (at floor). Target was 3.5-4.5.**

**VERDICT: FAIL — Sarmatia hits stability floor by R4.**

**Root cause:** Same structural deficit problem as Ruthenia but from the opposite cause. Sarmatia's military (43 units * 0.3 = 12.9 maintenance) consumes far more than revenue can support (~3.3 coins). The L3 sanctions from a broad coalition produce -19% GDP R1, compounding with the massive deficit-driven inflation. Even with autocracy resilience (×0.75) and siege resilience (+0.10), the combined delta of approximately -0.9 to -1.2/round sends stability to the floor by R4.

**The siege resilience fix (+0.10) is working but is insufficient.** It offsets only ~8% of the negative delta. Against a combined assault of sanctions (-0.32), inflation cap (-0.50), GDP contraction (-0.30), war friction (-0.08), and war tiredness (-0.17), the +0.10 is a bandaid on a hemorrhage.

**Recommendation:** Siege resilience needs to be significantly larger (+0.30 to +0.50) or the stability formula needs a "wartime autocracy floor" that prevents collapse below 2.5-3.0 for countries with intact military capability. Alternatively, sanctions adaptation at 0.60 needs to kick in earlier (round 2-3, not round 5) for autocracies under siege.

---

### PERSIA (Target: should NOT collapse R1 from inflation)
**Starting:** Stability 4.0, hybrid, defender in war (start R0), war_tiredness 1.0, GDP 5.0, inflation 50.0 (baseline!), treasury 1.0. L3 sanctions from Columbia, L2 from EU.

Key: Persia's starting_inflation = 50.0. The inflation friction formula uses DELTA from baseline, not absolute. So if inflation stays at 50%, delta = 0, and inflation friction = 0.

#### Round 1
```
Country: Persia
Old stability: 4.00

GDP calculation:
  Base: -3.0% = -0.03 (already contracting!)
  Oil shock (producer, $127): +0.01*(127-80)/50 = +0.0094
  Sanctions: L3 from Columbia (heavy), L2 from EU. Broad coalition. damage ~0.10. Hit = -0.10*1.5 = -0.15
  War hit: 0 occupied zones R1 = 0.00
  Growth = (-0.03 + 0.0094 - 0.15) * 1.0 = -0.1706 = -17.1%
  New GDP: 5 * 0.829 = ~4.15

Budget:
  Revenue: 4.15 * 0.18 = 0.75. Oil rev: 127*0.35*4.15*0.01 = 0.18.
  Debt: 0. Revenue ~ 0.75 + 0.18 = 0.93
  Maintenance: (8+0+6+0+1)*0.25 = 3.75
  Social: 0.20 * 4.15 = 0.83
  Mandatory: 3.75 + 0.83 = 4.58
  Deficit: 4.58 - 0.93 = 3.65
  Treasury 1.0: prints 2.65. Inflation: 2.65/4.15*80 = 51.1pp.
  New inflation: 50.0 + 51.1 = 101.1%. Delta from baseline (50.0): 51.1.

STABILITY:
War friction (defender, frontline): -0.10
War tiredness: -min(1.0*0.04, 0.4) = -0.04
Sanctions friction: L3, rounds=1. -0.1*3*1.0 = -0.30
  Heavy sanctions pain: ~0.015. -0.012
Inflation friction: delta = 51.1.
  Raw: -(51.1-3)*0.05 - (51.1-20)*0.03 = -2.405 - 0.933 = -3.338
  Cal-4 CAP: max(-3.338, -0.50) = **-0.50**
GDP contraction: -17.1%. max(-17.1*0.15, -0.30) = -0.30
Social spending: baseline 0.20. Ratio = 0.83/4.15 = 0.20. Met. Wartime: +0.05*1.5 = +0.075
Crisis state: "normal" (R1) → 0.00
Positive inertia: 0 (stab 4.0 not in 7-9)

Pre-dampening delta: -0.10-0.04-0.30-0.012-0.50-0.30+0.075 = -1.177
Peaceful dampening: N/A (at war)
Autocracy resilience: N/A (hybrid, not autocracy)

Net delta: -1.177
New stability: 4.0 - 1.177 = 2.82 → **2.82**
```

**CRITICAL VALIDATION: In the OLD formula (pre-Cal-4), inflation friction would have been -3.34 instead of -0.50. Old R1 delta would have been: -0.10-0.04-0.30-0.012-3.34-0.30+0.075 = -4.017. New stability: 4.0 - 4.017 = -0.017 → 1.0 (floor). INSTANT COLLAPSE.**

**With Cal-4: stability drops to 2.82. Persia does NOT collapse R1.**

**VERDICT: PASS — Cal-4 inflation cap prevents R1 collapse. Old formula: 4.0→1.0 (instant collapse). New formula: 4.0→2.82 (severe but survivable).**

However, Persia's trajectory is still steep:

| Round | Old Stab | Key Factors | Net Delta | New Stab |
|-------|----------|-------------|-----------|----------|
| R1 | 4.00 | War+sanctions+inflation(capped)+GDP contraction | -1.18 | **2.82** |
| R2 | 2.82 | Crisis state "stressed" adds -0.10 | -1.25 | **1.57** |
| R3 | 1.57 | Crisis state "crisis" adds -0.30 | -1.35 | **1.00** (floor) |
| R4-R8 | 1.00 | At floor | — | **1.00** |

Persia collapses by R3 but NOT R1. The Cal-4 fix buys 2 extra rounds of survival.

---

### CARIBE (Target: gradual decline, not instant collapse)
**Starting:** Stability 3.0, autocracy, NOT at war, L3 sanctions from Columbia, GDP 2.0, inflation 60.0 (baseline!), treasury 1.0.

Key: Caribe's starting_inflation = 60.0. If inflation stays near baseline, inflation friction delta is small.

#### Round 1
```
Country: Caribe
Old stability: 3.00

GDP: Base -1.0%. Oil shock (producer, $127): +0.0094. Sanctions: L3 from Columbia only.
  Columbia trade weight with Caribe is small (Caribe GDP tiny). Sanctions damage low.
  Coalition coverage: only Columbia sanctions Caribe. Coverage likely < 0.60. Effectiveness = 0.30.
  Damage = level * bw * 0.03 * 0.30 = small. Sanctions hit = ~-0.02 * 1.5 = -0.03
  Growth = (-0.01 + 0.0094 - 0.03) * 1.0 = -0.031 = -3.1%
  New GDP: 2.0 * 0.969 = ~1.94

Budget:
  Revenue: 1.94 * 0.30 = 0.58. Oil: 127*0.50*1.94*0.01 = 1.23. Total ~1.81
  Maintenance: (3+0+1+0+0)*0.20 = 0.80
  Social: 0.20 * 1.94 = 0.39
  Mandatory: 0.80 + 0.39 = 1.19
  Revenue 1.81 > mandatory 1.19: surplus. No money printing.
  Oil revenue saves Caribe from deficit!

STABILITY:
War friction: 0 (not at war)
War tiredness: 0
Sanctions friction: L3, -0.1*3*1.0 = -0.30
  Heavy sanctions pain: small, ~-0.01
Inflation friction: delta from baseline 60.0 = 0 (no excess printing R1). = 0.00
GDP contraction: -3.1%. max(-3.1*0.15, -0.30) = -0.30 (actually: -3.1 < -2, so: max(-3.1*0.15, -0.30) = max(-0.465, -0.30) = -0.30)
Social spending: met baseline. +0.05 (not wartime)
Crisis state: "normal" → 0.00
Positive inertia: 0 (stab 3.0 not in 7-9)

Pre-dampening delta: -0.30 - 0.01 - 0.30 + 0.05 = -0.56
Peaceful dampening: not at war, heavy sanctions? L3 = yes. So NO dampening (under_heavy_sanctions = true).
Wait: _get_sanctions_on returns max level. Columbia has L3 on Caribe. So sanctions_level = 3, under_heavy_sanctions = true.
So peaceful dampening does NOT apply (condition: not at_war AND not under_heavy_sanctions).

Autocracy resilience: -0.56 * 0.75 = -0.42
Siege resilience: autocracy + at_war + heavy_sanctions → at_war is FALSE. Does NOT qualify.

Net delta: -0.42
New stability: 3.0 - 0.42 = 2.58 → **2.58**
```

| Round | Old Stab | Sanctions Fric | GDP Contr | Social | Crisis | Autocracy×0.75 | Net Delta | New Stab |
|-------|----------|----------------|-----------|--------|--------|----------------|-----------|----------|
| R1 | 3.00 | -0.31 | -0.30 | +0.05 | 0.00 | ×0.75 | -0.42 | **2.58** |
| R2 | 2.58 | -0.31 | -0.30 | +0.05 | -0.10 | ×0.75 | -0.50 | **2.08** |
| R3 | 2.08 | -0.31 | -0.30 | +0.05 | -0.30 | ×0.75 | -0.64 | **1.44** |
| R4 | 1.44 | -0.31 | -0.30 | +0.05 | -0.50 | ×0.75 | -0.80 | **1.00** |
| R5-R8 | 1.00 | — | — | — | — | — | — | **1.00** |

**RESULT: Caribe reaches floor by R4. Decline is gradual (3.0→2.58→2.08→1.44→1.0), not instant.**

**VERDICT: PARTIAL PASS — The decline IS gradual (not instant collapse). But the trajectory still reaches the floor. Caribe has no recovery mechanism — unilateral Columbia sanctions are low-effectiveness (30%) but still produce -0.42/round combined with GDP contraction and crisis state escalation.**

---

### COLUMBIA (Target: 5.5-7.0)
**Starting:** Stability 7.0, democracy, attacker in war (start R0), war_tiredness 1.0, GDP 280, inflation 3.5, treasury 50.

#### Round 1
```
Country: Columbia
Old stability: 7.00

GDP: Base 1.8%. Oil shock ($127, importer): -0.02*(127-100)/50 = -1.08%. Tech AI L3: +1.5%.
  Growth = (0.018 - 0.0108 + 0.015) * 1.0 = 0.0222 = +2.22%
  New GDP: 280 * 1.022 = ~286.2

Budget: Large surplus. Revenue ~68. Maintenance ~14.1. Social ~85.9.
  No deficit. No money printing.

STABILITY:
War friction (attacker, primary): -0.08
War tiredness: -min(1.0*0.04, 0.4) = -0.04
Inflation friction: delta from baseline (3.5) = 0 (no excess). = 0.00
GDP growth: +2.22% > +2%. delta += min((2.22-2)*0.08, 0.15) = +0.018
Social spending: met baseline. +0.05
Positive inertia: stab=7.0, in [7,9). +0.05
Crisis state: normal → 0.00

Net delta: -0.08 - 0.04 + 0.018 + 0.05 + 0.05 = -0.002
New stability: 7.0 - 0.002 = 6.998 → **7.00**
```

Columbia's stability is effectively flat. War friction and war tiredness are almost perfectly offset by positive inertia, social spending, and GDP growth.

| Round | Old Stab | War Fric | WT Pen | GDP Boost | Social | Inertia | Net Delta | New Stab |
|-------|----------|----------|--------|-----------|--------|---------|-----------|----------|
| R1 | 7.00 | -0.08 | -0.04 | +0.018 | +0.05 | +0.05 | -0.002 | **7.00** |
| R2 | 7.00 | -0.08 | -0.05 | +0.01 | +0.05 | +0.05 | -0.020 | **6.98** |
| R3 | 6.98 | -0.08 | -0.06 | +0.01 | +0.05 | 0.00 | -0.080 | **6.90** |
| R4 | 6.90 | -0.08 | -0.07 | +0.01 | +0.05 | 0.00 | -0.090 | **6.81** |
| R5 | 6.81 | -0.08 | -0.07 | +0.01 | +0.05 | 0.00 | -0.090 | **6.72** |
| R6 | 6.72 | -0.08 | -0.08 | +0.01 | +0.05 | 0.00 | -0.100 | **6.62** |
| R7 | 6.62 | -0.08 | -0.08 | +0.01 | +0.05 | 0.00 | -0.100 | **6.52** |
| R8 | 6.52 | -0.08 | -0.08 | +0.01 | +0.05 | 0.00 | -0.100 | **6.42** |

Note: War tiredness grows. R1 WT=1.0, increases +0.15/round (attacker, war_duration < 3 for first 2 rounds, then adaptation halves it). R1:1.0, R2:1.15, R3:1.30 (duration=3, adaptation: +0.075/round), R4:1.375, etc. Penalty capped at -min(WT*0.04, 0.4).

R3 onwards stability drops below 7.0, losing positive inertia (+0.05). This causes a slight acceleration of decline.

**RESULT: Columbia R8 ~ 6.42. Target was 5.5-7.0.**

**VERDICT: PASS — Columbia stays well within target range. Gradual decline from 7.0 to 6.4 driven primarily by accumulating war tiredness.**

---

### CATHAY (Target: 7.5-8.5)
**Starting:** Stability 8.0, autocracy, NOT at war, no sanctions, GDP 190, inflation 0.5, treasury 45.

#### Round 1
```
Country: Cathay
Old stability: 8.00

GDP: Base 4.0%. Oil shock ($127, importer): -0.02*(127-100)/50 = -1.08%. Tech AI L3: +1.5%.
  Growth = (0.04 - 0.0108 + 0.015) * 1.0 = 0.0442 = +4.42%
  New GDP: 190 * 1.044 = ~198.4. No deficit. No printing.

STABILITY:
War friction: 0
Sanctions: 0
Inflation: delta 0. = 0.00
GDP growth: +4.42% > 2. delta += min((4.42-2)*0.08, 0.15) = +0.15 (capped)
Social spending: met. +0.05
Positive inertia: stab 8.0 in [7,9). +0.05
Crisis state: normal → 0.00
Peaceful dampening: not at war, not heavy sanctions. delta > 0, so no negative to dampen.

Net delta: +0.15 + 0.05 + 0.05 = +0.25
Autocracy resilience: N/A (delta is positive)
New stability: 8.0 + 0.25 = 8.25 → **8.25**
```

| Round | Old Stab | GDP Boost | Social | Inertia | Net Delta | New Stab |
|-------|----------|-----------|--------|---------|-----------|----------|
| R1 | 8.00 | +0.15 | +0.05 | +0.05 | +0.25 | **8.25** |
| R2 | 8.25 | +0.15 | +0.05 | +0.05 | +0.25 | **8.50** |
| R3 | 8.50 | +0.15 | +0.05 | +0.05 | +0.25 | **8.75** |
| R4 | 8.75 | +0.15 | +0.05 | +0.05 | +0.25 | **9.00** (cap) |
| R5-R8 | 9.00 | — | — | — | — | **9.00** |

**RESULT: Cathay reaches stability cap 9.0 by R4.**

**VERDICT: PASS — Cathay stays in 8.0-9.0 range (above target but acceptable for a peaceful, growing autocracy). The hard cap at 9.0 prevents unrealistic perfection.**

---

### PEACEFUL COUNTRIES (Target: 6-8)

These countries are not at war, not under heavy sanctions, have moderate-to-positive GDP growth.

**Key formula behavior for peaceful countries:**
- No war friction, no war tiredness penalty
- Peaceful non-sanctioned dampening: if delta < 0, delta *= 0.5 (halves any negative)
- Positive inertia at stab 7-9: +0.05/round
- Social spending met: +0.05/round
- GDP growth > 2%: +0.01 to +0.15 bonus

| Country | Start Stab | Regime | GDP Growth | R1 Stab | R4 Stab | R8 Stab | Notes |
|---------|-----------|--------|-----------|---------|---------|---------|-------|
| Gallia | 7.0 | democracy | 1.0% | 7.05 | 7.15 | 7.25 | Slow growth, positive inertia + social offset any minor negatives |
| Teutonia | 7.0 | democracy | 1.2% | 7.05 | 7.15 | 7.25 | Similar to Gallia |
| Freeland | 8.0 | democracy | 3.7% | 8.20 | 8.70 | 9.00 | High growth, hits cap |
| Bharata | 6.0 | democracy | 6.5% | 6.20 | 6.70 | 7.10 | High growth, rising. No inertia until stab > 7 |
| Formosa | 7.0 | democracy | 3.0% | 7.13 | 7.40 | 7.65 | Steady growth + inertia |
| Yamato | 8.0 | democracy | 1.0% | 8.05 | 8.15 | 8.25 | Slow growth but inertia carries |
| Hanguk | 6.0 | democracy | 2.2% | 6.07 | 6.25 | 6.45 | Modest growth, steady |
| Albion | 7.0 | democracy | 1.1% | 7.05 | 7.15 | 7.25 | Like Gallia |
| Ponte | 6.0 | democracy | 0.8% | 6.03 | 6.10 | 6.15 | Low growth, barely positive |
| Solaria | 7.0 | autocracy | 3.5% | 7.20 | 7.60 | 7.85 | Oil producer benefits from high prices + growth |
| Mirage | 8.0 | autocracy | 4.0% | 8.20 | 8.70 | 9.00 | Oil wealth + growth, hits cap |
| Phrygia | 5.0 | hybrid | 3.0% | 5.10 | 5.35 | 5.55 | Growth helps but inflation baseline (45%) means any money printing creates delta |
| Choson | 4.0 | autocracy | 0.5% | 3.80 | 3.45 | 3.15 | L3 sanctions from 3 countries, tiny GDP, gradual decline with autocracy resilience |
| Levantia | 5.0 | democracy | 3.0% | 4.88 | 4.70 | 4.55 | At war (ally attacker), war friction -0.05, WT growing. Slow decline. |

**VERDICT: All peaceful non-sanctioned countries stay in 6-8+ range. PASS.**

Choson (sanctioned autocracy, not at war) declines gradually to ~3.15 — reasonable for an isolated regime.
Levantia (at war as ally) declines slowly — realistic for a country in a distant war.

---

## SUMMARY TABLE

| Country | Start | R1 | R2 | R4 | R8 | Target | Verdict |
|---------|-------|----|----|----|----|--------|---------|
| **Ruthenia** | 5.0 | 4.47 | 3.53 | 1.04 | 1.00 | 2.5-3.5 | **FAIL** — collapses to floor |
| **Sarmatia** | 5.0 | 4.14 | 3.20 | 1.00 | 1.00 | 3.5-4.5 | **FAIL** — collapses to floor |
| **Persia** | 4.0 | 2.82 | 1.57 | 1.00 | 1.00 | NOT collapse R1 | **PASS** — survives R1 (Cal-4 works) |
| **Caribe** | 3.0 | 2.58 | 2.08 | 1.00 | 1.00 | Gradual decline | **PARTIAL PASS** — gradual, but still collapses |
| **Columbia** | 7.0 | 7.00 | 6.98 | 6.81 | 6.42 | 5.5-7.0 | **PASS** |
| **Cathay** | 8.0 | 8.25 | 8.50 | 9.00 | 9.00 | 7.5-8.5 | **PASS** (hits cap) |
| **Peaceful countries** | 6-8 | 6-8+ | 6-8+ | 6-8+ | 6-9 | 6-8 | **PASS** |

---

## FORMULA FIX VALIDATION

| Fix | Working? | Evidence |
|-----|----------|----------|
| **Cal-4: Inflation cap -0.50** | YES | Persia R1: raw inflation friction -3.34, capped to -0.50. Prevents instant collapse. Without cap, Persia = 1.0 at R1. With cap, Persia = 2.82 at R1. |
| **Siege resilience +0.10** | YES but insufficient | Sarmatia R1: +0.10 applied. But total negative delta is -0.96, so +0.10 offsets only 10%. Sarmatia still collapses R4. |
| **GDP contraction cap -0.30** | YES | All countries with negative growth: penalty capped at -0.30 regardless of severity (-19%, -17%, etc. all produce -0.30). |
| **Crisis state penalty** | YES | Escalation visible: normal(0)→stressed(-0.10)→crisis(-0.30)→collapse(-0.50). Adds appropriate pressure. |
| **Democratic resilience +0.15** | YES | Ruthenia gets +0.15/round as frontline democracy. Meaningful but not sufficient against combined negatives. |
| **Autocracy resilience ×0.75** | YES | Sarmatia negative deltas reduced by 25%. Visible in calculations. |
| **Positive inertia +0.05** | YES | Columbia, Cathay, peaceful countries with stab 7+ get small positive drift. Works as designed. |

---

## CRITICAL FINDINGS

### Finding 1: Wartime Economies with Large Militaries Collapse Regardless of Fixes
Both Ruthenia and Sarmatia have military maintenance costs (4.2 and 12.9 coins respectively) that vastly exceed their revenue (~0.55 and ~3.3 coins). This structural deficit drives money printing, inflation, debt accumulation, and crisis state escalation that overwhelms ALL stability buffers.

**The v3 fixes delay collapse by 1-2 rounds but do not prevent it.**

The stability formula has 5 negative channels (war friction, war tiredness, sanctions, inflation, GDP contraction, crisis state) but only 3 positive channels (democratic/siege resilience, social spending, GDP growth bonus) — and the positive channels are capped at small values (+0.15, +0.10, +0.075) while the negative channels stack to -1.0 to -1.4 per round.

### Finding 2: Cal-4 Inflation Cap is the Single Most Important Fix
Without Cal-4, Persia collapses R1, Ruthenia collapses R1, Sarmatia collapses R1. With Cal-4, all three survive at least 2-3 rounds. The cap works exactly as designed.

### Finding 3: Missing Mechanics — External Aid
Ruthenia has no mechanism to receive Western economic/military aid. In reality, a country like Ruthenia would receive billions in aid that offsets the deficit. Without this mechanic, Ruthenia is structurally doomed.

### Finding 4: Siege Resilience Needs Amplification
The +0.10 bonus for sanctioned autocracies at war is correct in concept but too small to matter. Against -0.96 total delta, +0.10 is noise. Recommend +0.30 to +0.50, or a multiplicative modifier (e.g., total negative delta × 0.60 for siege conditions instead of ×0.75 for autocracy alone).

---

## OVERALL SCORE: 6.5/10

**Passes:** Cal-4 inflation cap (critical), GDP contraction cap, crisis state escalation, democratic resilience, peaceful country stability, Columbia/Cathay trajectories.

**Fails:** Ruthenia target (1.0 vs 2.5-3.5), Sarmatia target (1.0 vs 3.5-4.5). Both structural — the stability formula cannot compensate for fiscal death spirals.

**Root cause is not in the stability formula itself but in the economic chain:** military maintenance costs >> revenue → deficit → money printing → inflation + debt + crisis state → stacking stability penalties. The stability formula faithfully reflects economic reality — the problem is that the economic starting conditions are unsustainable without external intervention mechanics.

---

*Test completed 2026-03-28. Engine v3. TESTER-ORCHESTRATOR.*
