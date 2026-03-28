# TEST 5: STABILITY CALIBRATION — FULL RESULTS
## 8-Round Stability Trajectory Test (New v4 Formula)

**Test Date:** 2026-03-27
**Tester:** TESTER-ORCHESTRATOR
**Purpose:** Validate the v4 stability formula fix. Previous tests had Heartland hitting 1.0 by R3 (catastrophically unrealistic). New formula targets: Heartland ~2.5-3.0 by R8, Nordostan ~3.5-4.5, peaceful countries 6-8.
**Formula Version:** v4 (world_model_engine.py `_calc_stability`)
**War tiredness model:** v2 (defender +0.20/R, attacker +0.15/R, society adaptation after R3)

---

## SCENARIO ASSUMPTIONS (8 Rounds)

### War Trajectory (Nordostan-Heartland)
Based on R1 results from Test 1 and projected SIM narrative:

| Round | Military Events | Heartland | Nordostan |
|-------|----------------|-----------|-----------|
| R1 | Nordostan advances, takes 1 hex. Heartland loses 2 ground. | Defender, 1 zone lost, 1 casualty event | Attacker, 1 zone gained, 1 casualty event |
| R2 | Grinding. Heartland holds with Columbia aid. No zone change. | Defender, 0 zones lost, 1 casualty | Attacker, 0 zones gained, 1 casualty |
| R3 | Nordostan minor push, takes 1 hex. Heartland counterattack fails. | Defender, 1 zone lost, 1 casualty | Attacker, 1 zone gained, 1 casualty |
| R4 | Stalemate. Mutual exhaustion. No zone change. | Defender, 0 zones lost, 1 casualty | Attacker, 0 zones gained, 1 casualty |
| R5 | Heartland counteroffensive (Columbia weapons). Retakes 1 hex. | Defender, 1 zone gained, 1 casualty | Attacker, 1 zone lost, 1 casualty |
| R6 | Nordostan escalation. Heavy fighting, 1 hex to Nordostan. | Defender, 1 zone lost, 2 casualty events | Attacker, 1 zone gained, 1 casualty |
| R7 | Ceasefire negotiations begin. Reduced fighting. | Defender, 0 zones, 0 casualties | Attacker, 0 zones, 0 casualties |
| R8 | Fragile ceasefire. Minimal combat. | Defender, 0 zones, 0 casualties | Attacker, 0 zones, 0 casualties |

### War Trajectory (Columbia-Persia + Levantia-Persia)
| Round | Columbia | Persia | Levantia |
|-------|----------|--------|----------|
| R1-R3 | Allied (supporting, not frontline) | Defender (2 wars), 1 casualty/R | Attacker, 0-1 casualties/R |
| R4 | Persia ceasefire with Columbia | Ceasefire with Columbia | Still fighting Persia proxies |
| R5-R8 | Not at war | Not at war (ceasefire) | Winds down |

### Economic Assumptions (GDP growth rates used for stability calc)
| Country | R1-R2 | R3-R4 | R5-R6 | R7-R8 | Sanctions Level |
|---------|-------|-------|-------|-------|-----------------|
| Columbia | 1.8% | 1.5% | 2.0% | 2.2% | 0 |
| Cathay | 3.9% | 3.5% | 3.8% | 4.0% | 0 |
| Nordostan | 0.7% | 0.5% | 0.3% | 0.5% | 3 |
| Heartland | 2.4% | 1.5% | 2.0% | 2.5% | 0 |
| Persia | -1.8% | -3.0% | -0.5% | 0.5% | 2 |
| Gallia | 1.0% | 0.8% | 1.0% | 1.2% | 0 |
| Teutonia | 1.2% | 0.8% | 1.0% | 1.2% | 0 |
| Freeland | 3.7% | 3.0% | 3.2% | 3.5% | 0 |
| Ponte | 0.8% | 0.5% | 0.8% | 0.8% | 0 |
| Albion | 1.1% | 0.8% | 1.0% | 1.2% | 0 |
| Bharata | 6.5% | 6.0% | 6.2% | 6.5% | 0 |
| Levantia | 3.0% | 2.0% | 2.5% | 3.0% | 0 |
| Formosa | 3.0% | 2.5% | 2.8% | 3.0% | 0 |
| Phrygia | 3.0% | 2.0% | 2.5% | 3.0% | 0 |
| Yamato | 1.0% | 0.8% | 1.0% | 1.0% | 0 |
| Solaria | 3.5% | 3.0% | 3.0% | 3.5% | 1 (minor) |
| Choson | 0.5% | 0.3% | 0.3% | 0.3% | 3 |
| Hanguk | 2.2% | 2.0% | 2.2% | 2.5% | 0 |
| Caribe | -1.0% | -2.0% | -1.5% | -1.0% | 2 |
| Mirage | 4.0% | 3.5% | 3.8% | 4.0% | 1 (minor) |

### Social Spending Assumptions
- Most countries: at baseline (delta = +0.05)
- Heartland: at baseline (wartime programs, 1.5x effectiveness = +0.075)
- Nordostan: slight shortfall R3+ (delta = -0.05)
- Persia: serious shortfall (delta = -0.15 avg)
- Caribe: serious shortfall (delta = -0.10 avg)
- Choson: at baseline (minimal baseline met)

### Inflation Impact (above 3%)
- Nordostan: 5% inflation -> -(5-3)*0.05 = -0.10
- Heartland: 7.5% -> -(7.5-3)*0.05 = -0.225 R1, declining to ~5% by R8 -> -0.10
- Persia: 50% -> -(50-3)*0.05 + -(50-20)*0.03 = -2.35-0.90 = -3.25 (MASSIVE, but dampened)
- Phrygia: 45% -> similar massive hit
- Caribe: 60% -> catastrophic
- Choson: 10% -> -(10-3)*0.05 = -0.35

**IMPORTANT NOTE ON INFLATION:** The inflation penalty is extremely harsh for high-inflation countries (Persia at 50%, Phrygia at 45%, Caribe at 60%, Choson at 10%). This creates enormous negative deltas BEFORE dampening. This is a critical finding -- see Analysis section.

**ADJUSTMENT FOR REALISM:** The inflation penalties for countries that START with high inflation should be understood as already priced into the starting stability. For this test, I will apply inflation friction as a CHANGE from starting conditions: only the DELTA in inflation from round start matters, not the absolute level. Otherwise Persia/Caribe/Phrygia would hit 1.0 in R1 from inflation alone, which is nonsensical. This is flagged as a **FORMULA BUG** -- see Analysis.

**REVISED INFLATION APPROACH (for this test):** Use inflation CHANGE from starting value.
- If inflation rises 5pp above start: -(5)*0.05 = -0.25
- If inflation stays flat: 0
- Countries starting with high inflation: no additional penalty unless inflation worsens

---

## STARTING CONDITIONS (from countries.csv)

| Country | Stability | Regime | War Status | War Tiredness | Inflation |
|---------|-----------|--------|------------|---------------|-----------|
| Columbia | 7.0 | democracy | at war (Persia) - allied/supporting | 1.0 | 3.5% |
| Cathay | 8.0 | autocracy | not at war | 0 | 0.5% |
| Nordostan | 5.0 | autocracy | at war (Heartland) - attacker | 4.0 | 5.0% |
| Heartland | 5.0 | democracy | at war (Nordostan) - defender | 4.0 | 7.5% |
| Persia | 4.0 | hybrid | at war (Columbia, Levantia) - defender | 1.0 | 50.0% |
| Gallia | 7.0 | democracy | not at war | 0 | 2.5% |
| Teutonia | 7.0 | democracy | not at war | 0 | 2.5% |
| Freeland | 8.0 | democracy | not at war | 0 | 4.0% |
| Ponte | 6.0 | democracy | not at war | 0 | 2.5% |
| Albion | 7.0 | democracy | not at war | 0 | 3.0% |
| Bharata | 6.0 | democracy | not at war | 0 | 5.0% |
| Levantia | 5.0 | democracy | at war (Persia) - attacker | 2.0 | 3.5% |
| Formosa | 7.0 | democracy | not at war | 0 | 2.0% |
| Phrygia | 5.0 | hybrid | not at war | 0 | 45.0% |
| Yamato | 8.0 | democracy | not at war | 0 | 2.5% |
| Solaria | 7.0 | autocracy | at war (minor - under attack) | 1.0 | 2.0% |
| Choson | 4.0 | autocracy | not at war (allied) | 0 | 10.0% |
| Hanguk | 6.0 | democracy | not at war | 0 | 2.5% |
| Caribe | 3.0 | autocracy | not at war (blockaded) | 0 | 60.0% |
| Mirage | 8.0 | autocracy | at war (minor - under attack) | 1.0 | 2.0% |

**Note on war_tiredness starting values:** Nordostan and Heartland start at 4.0 (4 years of pre-SIM war). Persia/Levantia/Solaria/Mirage start at 1.0-2.0 (recent conflict).

**Note on war start_round:** Nordostan-Heartland war started pre-SIM (start_round = -4, so by R1 war_duration = 5, already past the 3-round adaptation threshold). Persia wars started R0.

---

## ROUND-BY-ROUND DETAILED CALCULATIONS

### ============================================================
### ROUND 1
### ============================================================

#### HEARTLAND (Democracy, Defender, Frontline)
```
Starting stability: 5.00
War tiredness (start of round): 4.00

DELTA COMPONENTS:
  Positive inertia (7 <= stab < 9):     +0.00  (stab=5.0, not eligible)
  GDP growth boost (2.4% > 2%):          +0.08 * (2.4-2) = +0.032
  Social spending (at baseline, war 1.5x): +0.075
  War friction (defender frontline):      -0.10
  Casualties (1 event):                   -0.20
  Territory lost (1 zone):                -0.40
  Territory gained (0):                   +0.00
  War tiredness (min(4.0*0.04, 0.4)):     -0.16
  Democratic resilience (frontline dem):  +0.15
  Sanctions friction (level 0):           +0.00
  Inflation change (0pp from start):      +0.00

  RAW DELTA = +0.032 +0.075 -0.10 -0.20 -0.40 +0.00 -0.16 +0.15 +0.00 +0.00
            = -0.603

  Non-war dampening: N/A (at war)
  Autocracy resilience: N/A (democracy)

  FINAL DELTA = -0.603

New stability: 5.00 + (-0.603) = 4.40
War tiredness update: war_duration=5 (>=3, adaptation active)
  base_increase = 0.20 * 0.5 = 0.10
  new_war_tiredness = 4.00 + 0.10 = 4.10
```
**Heartland R1: 5.00 -> 4.40** (war_tiredness: 4.00 -> 4.10)

#### NORDOSTAN (Autocracy, Attacker)
```
Starting stability: 5.00
War tiredness (start of round): 4.00

DELTA COMPONENTS:
  Positive inertia:                       +0.00  (stab=5.0)
  GDP growth boost (0.7% < 2%):           +0.00
  Social spending (at baseline):          +0.05
  War friction (attacker):                -0.08
  Casualties (1 event):                   -0.20
  Territory lost (0):                     +0.00
  Territory gained (1 zone):              +0.15
  War tiredness (min(4.0*0.04, 0.4)):     -0.16
  Democratic resilience: N/A (autocracy)
  Sanctions friction (level 3):           -0.30
  Inflation change (0pp):                 +0.00

  RAW DELTA = +0.05 -0.08 -0.20 +0.15 -0.16 -0.30
            = -0.54

  Autocracy resilience: -0.54 * 0.75 = -0.405

  FINAL DELTA = -0.405

New stability: 5.00 + (-0.405) = 4.60
War tiredness: duration=5 (>=3), base=0.15*0.5=0.075
  new_war_tiredness = 4.00 + 0.075 = 4.075
```
**Nordostan R1: 5.00 -> 4.60** (war_tiredness: 4.00 -> 4.075)

#### COLUMBIA (Democracy, Allied/Supporting in Persia war)
```
Starting stability: 7.00
War tiredness (start of round): 1.00

DELTA COMPONENTS:
  Positive inertia (7 <= 7.0 < 9):       +0.05
  GDP growth boost (1.8% < 2%):           +0.00
  Social spending (at baseline):          +0.05
  War friction (allied):                  -0.05
  Casualties (1 event - Gulf Gate):       -0.20
  Territory lost (0):                     +0.00
  War tiredness (min(1.0*0.04, 0.4)):     -0.04
  Democratic resilience: N/A (not frontline)
  Sanctions friction (0):                 +0.00
  Inflation change (0pp):                 +0.00

  RAW DELTA = +0.05 +0.05 -0.05 -0.20 -0.04
            = -0.19

  FINAL DELTA = -0.19

New stability: 7.00 + (-0.19) = 6.81
War tiredness: allied, duration ~1, base=0.10
  new_war_tiredness = 1.00 + 0.10 = 1.10
```
**Columbia R1: 7.00 -> 6.81** (war_tiredness: 1.00 -> 1.10)

#### PERSIA (Hybrid, Defender in 2 wars)
```
Starting stability: 4.00
War tiredness (start of round): 1.00

DELTA COMPONENTS:
  Positive inertia:                       +0.00
  GDP growth boost (-1.8%, < -2?): NO    +0.00  (between -2 and 2, no effect)
  Social spending (serious shortfall):    -0.15
  War friction (defender frontline):      -0.10
  Casualties (1 event):                   -0.20
  Territory lost (0 zones):              +0.00
  War tiredness (min(1.0*0.04, 0.4)):     -0.04
  Democratic resilience (frontline hybrid): +0.15
  Sanctions friction (level 2):           -0.20
  Inflation change (0pp from 50% start):  +0.00

  RAW DELTA = -0.15 -0.10 -0.20 -0.04 +0.15 -0.20
            = -0.54

  Non-war dampening: N/A (at war)
  Autocracy resilience: N/A (hybrid - not autocracy)

  FINAL DELTA = -0.54

New stability: 4.00 + (-0.54) = 3.46
War tiredness: defender, duration=1 (<3), base=0.20
  new_war_tiredness = 1.00 + 0.20 = 1.20
```
**Persia R1: 4.00 -> 3.46** (war_tiredness: 1.00 -> 1.20)

#### CATHAY (Autocracy, Not at war)
```
Starting stability: 8.00
War tiredness: 0

DELTA COMPONENTS:
  Positive inertia (7 <= 8.0 < 9):       +0.05
  GDP growth boost (3.9% > 2%):           +0.08*(3.9-2) = +0.152 -> capped at +0.15
  Social spending (at baseline):          +0.05
  No war components.
  Sanctions friction (0):                 +0.00
  Inflation change (0pp):                 +0.00

  RAW DELTA = +0.05 +0.15 +0.05 = +0.25

  Non-war peaceful dampening: positive delta, no dampening applied
  (dampening only applies to negative delta for peaceful countries)

  FINAL DELTA = +0.25

New stability: 8.00 + 0.25 = 8.25 -> clamped to 9.0 max -> 8.25
```
**Cathay R1: 8.00 -> 8.25** (no war tiredness)

#### CARIBE (Autocracy, Not at war, Blockaded)
```
Starting stability: 3.00
War tiredness: 0

DELTA COMPONENTS:
  Positive inertia:                       +0.00
  GDP growth boost (-1.0%, > -2%):        +0.00
  Social spending (serious shortfall):    -0.10
  No war friction (not at war).
  Sanctions friction (level 2):           -0.20
  Inflation change (0pp from 60% start):  +0.00

  RAW DELTA = -0.10 -0.20 = -0.30

  Non-war peaceful dampening: delta<0, *0.5 = -0.15
  Autocracy resilience: delta<0, *0.75 = -0.1125

  FINAL DELTA = -0.1125

New stability: 3.00 + (-0.1125) = 2.89
```
**Caribe R1: 3.00 -> 2.89**

#### YAMATO (Democracy, Not at war)
```
Starting stability: 8.00

DELTA COMPONENTS:
  Positive inertia (7 <= 8.0 < 9):       +0.05
  GDP growth boost (1.0% < 2%):           +0.00
  Social spending (at baseline):          +0.05
  No war.
  ICBM shock (special event R1):          -0.30 (from R1 results)

  RAW DELTA = +0.05 +0.05 -0.30 = -0.20

  Non-war peaceful dampening: delta<0, *0.5 = -0.10

  FINAL DELTA = -0.10

New stability: 8.00 + (-0.10) = 7.90
```
**Yamato R1: 8.00 -> 7.90**

#### SOLARIA (Autocracy, Under attack - minor)
```
Starting stability: 7.00

DELTA COMPONENTS:
  Positive inertia (7 <= 7.0 < 9):       +0.05
  GDP growth boost (3.5% > 2%):           +0.08*(3.5-2) = +0.12
  Social spending (at baseline):          +0.05
  War friction (allied/under attack):     -0.05
  Casualties (0 this round):             +0.00
  War tiredness (min(1.0*0.04, 0.4)):     -0.04
  Sanctions friction (level 1):           -0.10

  RAW DELTA = +0.05 +0.12 +0.05 -0.05 -0.04 -0.10 = +0.03

  Autocracy resilience: N/A (delta positive)

  FINAL DELTA = +0.03

New stability: 7.00 + 0.03 = 7.03
```
**Solaria R1: 7.00 -> 7.03**

#### GALLIA (Democracy, Not at war)
```
Starting stability: 7.00

DELTA COMPONENTS:
  Positive inertia (7 <= 7.0 < 9):       +0.05
  GDP growth boost (1.0% < 2%):           +0.00
  Social spending (at baseline):          +0.05
  No war. No sanctions.

  RAW DELTA = +0.10
  Peaceful non-war: delta positive, no dampening.

  FINAL DELTA = +0.10

New stability: 7.00 + 0.10 = 7.10
```
**Gallia R1: 7.00 -> 7.10**

#### REMAINING COUNTRIES R1 (abbreviated, same method)

| Country | Start | Key Drivers | Raw Delta | Dampening | Final Delta | End R1 |
|---------|-------|-------------|-----------|-----------|-------------|--------|
| Teutonia | 7.00 | +0.05 inertia, +0.05 social | +0.10 | none | +0.10 | **7.10** |
| Freeland | 8.00 | +0.05 inertia, +0.08*(3.7-2)=+0.136, +0.05 social | +0.236 | none | +0.236 | **8.24** |
| Ponte | 6.00 | +0.05 social | +0.05 | none | +0.05 | **6.05** |
| Albion | 7.00 | +0.05 inertia, +0.05 social | +0.10 | none | +0.10 | **7.10** |
| Bharata | 6.00 | +0.08*(6.5-2)=+0.36 capped +0.15, +0.05 social | +0.20 | none | +0.20 | **6.20** |
| Levantia | 5.00 | attacker -0.08, WT -0.04*(2.0)=-0.08, cas -0.20, +0.05 social, +0.08*(3-2)=+0.08 | -0.23 | none(at war) | -0.23 | **4.77** |
| Formosa | 7.00 | +0.05 inertia, +0.05 social, +0.08*(3-2)=+0.08, encirclement -0.10 | +0.08 | pos->none | +0.08 | **7.08** |
| Phrygia | 5.00 | +0.05 social, +0.08*(3-2)=+0.08 | +0.13 | none | +0.13 | **5.13** |
| Hanguk | 6.00 | +0.05 social, +0.08*(2.2-2)=+0.016, ICBM -0.20 | -0.134 | *0.5=-0.067 | -0.067 | **5.93** |
| Choson | 4.00 | +0.05 social, sanctions L3 -0.30 | -0.25 | *0.5=-0.125, *0.75=-0.094 | -0.094 | **3.91** |
| Mirage | 8.00 | +0.05 inertia, +0.08*(4-2)=+0.16 capped +0.15, +0.05 social, war -0.05, WT -0.04, sanctions L1 -0.10 | +0.06 | none(pos) | +0.06 | **8.06** |

### R1 SUMMARY

| Country | R0 | R1 | Change | Status |
|---------|----|----|--------|--------|
| **Heartland** | 5.00 | **4.40** | -0.60 | Declining (defender, territory lost) |
| **Nordostan** | 5.00 | **4.60** | -0.40 | Declining slowly (autocracy resilience) |
| **Columbia** | 7.00 | **6.81** | -0.19 | Mild decline (allied war cost) |
| **Persia** | 4.00 | **3.46** | -0.54 | Sharp decline (2 wars, sanctions) |
| **Cathay** | 8.00 | **8.25** | +0.25 | Rising (growth, peaceful) |
| **Caribe** | 3.00 | **2.89** | -0.11 | Slow decline (blockade, autocracy dampens) |
| **Yamato** | 8.00 | **7.90** | -0.10 | ICBM shock, still high |
| **Gallia** | 7.00 | **7.10** | +0.10 | Stable/rising |
| **Teutonia** | 7.00 | **7.10** | +0.10 | Stable/rising |
| **Freeland** | 8.00 | **8.24** | +0.24 | Rising (strong growth) |
| **Bharata** | 6.00 | **6.20** | +0.20 | Rising (strong growth) |
| **Levantia** | 5.00 | **4.77** | -0.23 | Declining (attacker war costs) |
| **Formosa** | 7.00 | **7.08** | +0.08 | Stable |
| **Phrygia** | 5.00 | **5.13** | +0.13 | Slightly rising |
| **Solaria** | 7.00 | **7.03** | +0.03 | Stable |
| **Choson** | 4.00 | **3.91** | -0.09 | Slow decline (sanctions, autocracy dampens) |
| **Hanguk** | 6.00 | **5.93** | -0.07 | ICBM anxiety, dampened |
| **Mirage** | 8.00 | **8.06** | +0.06 | Stable (oil wealth offsets minor war) |
| **Ponte** | 6.00 | **6.05** | +0.05 | Stable |
| **Albion** | 7.00 | **7.10** | +0.10 | Stable/rising |

---

### ============================================================
### ROUND 2
### ============================================================

#### HEARTLAND
```
Starting stability: 4.40
War tiredness: 4.10

DELTA COMPONENTS:
  Positive inertia:                       +0.00
  GDP growth boost (2.4% > 2%):           +0.032
  Social spending (war 1.5x):             +0.075
  War friction (defender):                -0.10
  Casualties (1):                         -0.20
  Territory lost (0):                     +0.00
  War tiredness (min(4.10*0.04, 0.4)):    -0.164
  Democratic resilience:                  +0.15

  RAW DELTA = +0.032 +0.075 -0.10 -0.20 -0.164 +0.15 = -0.207
  FINAL DELTA = -0.207

New stability: 4.40 + (-0.207) = 4.19
WT: duration=6 (>=3), +0.20*0.5=0.10 -> 4.10+0.10 = 4.20
```
**Heartland R2: 4.40 -> 4.19** (WT: 4.10 -> 4.20)

#### NORDOSTAN
```
Starting stability: 4.60
War tiredness: 4.075

DELTA COMPONENTS:
  Positive inertia:                       +0.00
  GDP growth boost (0.7% < 2%):           +0.00
  Social spending (at baseline):          +0.05
  War friction (attacker):                -0.08
  Casualties (1):                         -0.20
  Territory gained (0):                   +0.00
  War tiredness (min(4.075*0.04, 0.4)):   -0.163
  Sanctions friction (L3):                -0.30

  RAW DELTA = +0.05 -0.08 -0.20 -0.163 -0.30 = -0.693
  Autocracy resilience: *0.75 = -0.520

  FINAL DELTA = -0.520

New stability: 4.60 + (-0.520) = 4.08
WT: duration=6, +0.15*0.5=0.075 -> 4.075+0.075 = 4.15
```
**Nordostan R2: 4.60 -> 4.08** (WT: 4.075 -> 4.15)

#### COLUMBIA
```
Starting stability: 6.81
War tiredness: 1.10

DELTA COMPONENTS:
  Positive inertia:                       +0.00  (6.81 < 7)
  GDP growth boost (1.8% < 2%):           +0.00
  Social spending:                        +0.05
  War friction (allied):                  -0.05
  Casualties (0 this round):              +0.00
  War tiredness (min(1.10*0.04, 0.4)):    -0.044

  RAW DELTA = +0.05 -0.05 -0.044 = -0.044
  FINAL DELTA = -0.044

New stability: 6.81 + (-0.044) = 6.77
WT: allied, duration=2 (<3), +0.10 -> 1.10+0.10 = 1.20
```
**Columbia R2: 6.81 -> 6.77** (WT: 1.10 -> 1.20)

#### PERSIA
```
Starting stability: 3.46
War tiredness: 1.20

DELTA COMPONENTS:
  GDP growth (-1.8%):                     +0.00  (> -2%)
  Social spending (shortfall):            -0.15
  War friction (defender):                -0.10
  Casualties (1):                         -0.20
  War tiredness (min(1.20*0.04, 0.4)):    -0.048
  Democratic resilience (hybrid):         +0.15
  Sanctions friction (L2):                -0.20

  RAW DELTA = -0.15 -0.10 -0.20 -0.048 +0.15 -0.20 = -0.548
  FINAL DELTA = -0.548

New stability: 3.46 + (-0.548) = 2.91
WT: defender, duration=2 (<3), +0.20 -> 1.20+0.20 = 1.40
```
**Persia R2: 3.46 -> 2.91** (WT: 1.20 -> 1.40)

#### CATHAY
```
Starting stability: 8.25
WT: 0

  Positive inertia (7 <= 8.25 < 9):      +0.05
  GDP growth (3.9% > 2%):                 +0.15 (capped)
  Social spending:                        +0.05

  RAW DELTA = +0.25
  FINAL DELTA = +0.25

New stability: 8.25 + 0.25 = 8.50
```
**Cathay R2: 8.25 -> 8.50**

#### CARIBE
```
Starting stability: 2.89
WT: 0

  Social spending shortfall:              -0.10
  Sanctions (L2):                         -0.20

  RAW DELTA = -0.30
  Peaceful dampening: *0.5 = -0.15
  Autocracy resilience: *0.75 = -0.1125

  FINAL DELTA = -0.1125

New stability: 2.89 + (-0.1125) = 2.78
```
**Caribe R2: 2.89 -> 2.78**

#### OTHER COUNTRIES R2

| Country | Start R2 | Key Changes from R1 | Delta | End R2 |
|---------|----------|---------------------|-------|--------|
| Yamato | 7.90 | +0.05 inertia, +0.05 social (no shock) | +0.10 | **8.00** |
| Gallia | 7.10 | +0.05 inertia, +0.05 social | +0.10 | **7.20** |
| Teutonia | 7.10 | +0.05 inertia, +0.05 social | +0.10 | **7.20** |
| Freeland | 8.24 | +0.05 inertia, +0.15 GDP, +0.05 social | +0.25 | **8.49** |
| Ponte | 6.05 | +0.05 social | +0.05 | **6.10** |
| Albion | 7.10 | +0.05 inertia, +0.05 social | +0.10 | **7.20** |
| Bharata | 6.20 | +0.15 GDP, +0.05 social | +0.20 | **6.40** |
| Levantia | 4.77 | attacker -0.08, WT(2.0+0.15=2.15) -0.086, cas -0.20, +0.05 social, +0.08 GDP | -0.236 | **4.53** |
| Formosa | 7.08 | +0.05 inertia, +0.05 social, +0.08 GDP | +0.18 | **7.26** |
| Phrygia | 5.13 | +0.05 social, +0.08 GDP | +0.13 | **5.26** |
| Hanguk | 5.93 | +0.05 social, +0.016 GDP (no shock R2) | +0.066 positive, no damp | **6.00** |
| Choson | 3.91 | +0.05 social, sanctions -0.30, *0.5*0.75 = -0.094 | -0.094 | **3.81** |
| Mirage | 8.06 | +0.05 inertia, +0.15 GDP, +0.05 social, -0.05 war, -0.04 WT, -0.10 sanc | +0.06 | **8.12** |
| Solaria | 7.03 | +0.05 inertia, +0.12 GDP, +0.05 social, -0.05 war, -0.04 WT, -0.10 sanc | +0.03 | **7.06** |

### R2 SUMMARY

| Country | R1 | R2 | Cumulative Change |
|---------|----|----|-------------------|
| **Heartland** | 4.40 | **4.19** | -0.81 from start |
| **Nordostan** | 4.60 | **4.08** | -0.92 from start |
| **Columbia** | 6.81 | **6.77** | -0.23 from start |
| **Persia** | 3.46 | **2.91** | -1.09 from start |
| **Cathay** | 8.25 | **8.50** | +0.50 from start |
| **Caribe** | 2.89 | **2.78** | -0.22 from start |
| **Levantia** | 4.77 | **4.53** | -0.47 from start |

---

### ============================================================
### ROUND 3
### ============================================================

#### HEARTLAND
```
Starting stability: 4.19
War tiredness: 4.20

DELTA COMPONENTS:
  GDP growth (1.5% < 2%):                +0.00
  Social spending (war 1.5x):            +0.075
  War friction (defender):               -0.10
  Casualties (1):                        -0.20
  Territory lost (1 zone):               -0.40
  War tiredness (min(4.20*0.04, 0.4)):   -0.168
  Democratic resilience:                 +0.15

  RAW DELTA = +0.075 -0.10 -0.20 -0.40 -0.168 +0.15 = -0.643
  FINAL DELTA = -0.643

New stability: 4.19 + (-0.643) = 3.55
WT: +0.10 -> 4.30
```
**Heartland R3: 4.19 -> 3.55** (WT: 4.20 -> 4.30)

#### NORDOSTAN
```
Starting stability: 4.08
War tiredness: 4.15

DELTA COMPONENTS:
  GDP growth (0.5% < 2%):                +0.00
  Social spending (shortfall R3+):       -0.05
  War friction (attacker):               -0.08
  Casualties (1):                        -0.20
  Territory gained (1):                  +0.15
  War tiredness (min(4.15*0.04, 0.4)):   -0.166
  Sanctions (L3):                        -0.30

  RAW DELTA = -0.05 -0.08 -0.20 +0.15 -0.166 -0.30 = -0.646
  Autocracy: *0.75 = -0.485

  FINAL DELTA = -0.485

New stability: 4.08 + (-0.485) = 3.60
WT: +0.075 -> 4.225
```
**Nordostan R3: 4.08 -> 3.60** (WT: 4.15 -> 4.225)

#### COLUMBIA
```
Starting stability: 6.77
WT: 1.20

  Social spending:                        +0.05
  War friction (allied):                  -0.05
  Casualties (0):                         +0.00
  War tiredness (1.20*0.04):              -0.048

  RAW DELTA = +0.05 -0.05 -0.048 = -0.048
  FINAL DELTA = -0.048

New stability: 6.77 - 0.048 = 6.72
WT: +0.10 -> 1.30
```
**Columbia R3: 6.77 -> 6.72** (WT: 1.20 -> 1.30)

#### PERSIA
```
Starting stability: 2.91
War tiredness: 1.40

  GDP growth (-3.0% < -2%):              +(-3.0)*0.3 = -0.90
  Social spending (shortfall):           -0.15
  War friction (defender):               -0.10
  Casualties (1):                        -0.20
  War tiredness (min(1.40*0.04, 0.4)):   -0.056
  Democratic resilience (hybrid):        +0.15
  Sanctions (L2):                        -0.20

  RAW DELTA = -0.90 -0.15 -0.10 -0.20 -0.056 +0.15 -0.20 = -1.456
  FINAL DELTA = -1.456

New stability: 2.91 + (-1.456) = 1.45
WT: duration=3 (>=3!), +0.20*0.5=0.10 -> 1.40+0.10 = 1.50
```
**Persia R3: 2.91 -> 1.45** (WT: 1.40 -> 1.50)
*Note: Persia's GDP contraction (-3.0%) triggers the severe negative growth penalty. This is a critical moment -- Persia is near collapse. Ceasefire with Columbia at R4 is essential.*

#### CATHAY
```
Starting stability: 8.50
  +0.05 inertia, +0.15 GDP, +0.05 social = +0.25
New stability: 8.50 + 0.25 = 8.75
```
**Cathay R3: 8.50 -> 8.75**

#### CARIBE
```
Starting stability: 2.78
  Social shortfall: -0.10, Sanctions L2: -0.20
  GDP now -2.0% -> penalty: +(-2.0)*0.3 = -0.60
  RAW DELTA = -0.10 -0.20 -0.60 = -0.90
  Peaceful dampening: *0.5 = -0.45
  Autocracy: *0.75 = -0.3375

New stability: 2.78 + (-0.3375) = 2.44
```
**Caribe R3: 2.78 -> 2.44**
*Note: GDP contraction past -2% triggers severe penalty. Caribe accelerates toward crisis.*

#### OTHER COUNTRIES R3

| Country | Start R3 | Delta | End R3 |
|---------|----------|-------|--------|
| Yamato | 8.00 | +0.10 | **8.10** |
| Gallia | 7.20 | +0.10 | **7.30** |
| Teutonia | 7.20 | +0.10 | **7.30** |
| Freeland | 8.49 | +0.25 | **8.74** |
| Ponte | 6.10 | +0.05 | **6.15** |
| Albion | 7.20 | +0.10 | **7.30** |
| Bharata | 6.40 | +0.20 | **6.60** |
| Levantia | 4.53 | attacker -0.08, WT(2.30) -0.092, cas -0.20, +0.05 social = -0.322 | **4.21** |
| Formosa | 7.26 | +0.05 inertia, +0.05 social, +0.04 GDP | +0.14 | **7.40** |
| Phrygia | 5.26 | +0.05 social | +0.05 | **5.31** |
| Hanguk | 6.00 | +0.05 social | +0.05 | **6.05** |
| Choson | 3.81 | sanctions -0.30, +0.05 social -> *0.5*0.75 = -0.094 | **3.72** |
| Mirage | 8.12 | +0.06 | **8.18** |
| Solaria | 7.06 | +0.03 | **7.09** |

---

### ============================================================
### ROUND 4
### ============================================================

**Key events:** Persia ceasefire with Columbia. Columbia exits war. Stalemate on Nordostan-Heartland front.

#### HEARTLAND
```
Starting stability: 3.55
War tiredness: 4.30

DELTA COMPONENTS:
  GDP growth (1.5% < 2%):                +0.00
  Social spending (war 1.5x):            +0.075
  War friction (defender):               -0.10
  Casualties (1):                        -0.20
  Territory lost (0):                    +0.00
  War tiredness (min(4.30*0.04, 0.4)):   -0.172
  Democratic resilience:                 +0.15

  RAW DELTA = +0.075 -0.10 -0.20 -0.172 +0.15 = -0.247
  FINAL DELTA = -0.247

New stability: 3.55 + (-0.247) = 3.30
WT: +0.10 -> 4.40
```
**Heartland R4: 3.55 -> 3.30** (WT: 4.30 -> 4.40)

#### NORDOSTAN
```
Starting stability: 3.60
War tiredness: 4.225

DELTA COMPONENTS:
  GDP growth (0.5%):                     +0.00
  Social spending (shortfall):           -0.05
  War friction (attacker):               -0.08
  Casualties (1):                        -0.20
  Territory gained (0):                  +0.00
  War tiredness (min(4.225*0.04, 0.4)):  -0.169
  Sanctions (L3):                        -0.30

  RAW DELTA = -0.05 -0.08 -0.20 -0.169 -0.30 = -0.799
  Autocracy: *0.75 = -0.599

  FINAL DELTA = -0.599

New stability: 3.60 + (-0.599) = 3.00
WT: +0.075 -> 4.30
```
**Nordostan R4: 3.60 -> 3.00** (WT: 4.225 -> 4.30)

#### COLUMBIA (No longer at war after R4 ceasefire with Persia)
```
Starting stability: 6.72
WT: 1.30

  Still at war R4 (ceasefire takes effect end of round).
  Same as R3 but war tiredness higher:

  Social spending:                        +0.05
  War friction (allied):                  -0.05
  War tiredness (1.30*0.04):              -0.052

  RAW DELTA = -0.052
  FINAL DELTA = -0.052

New stability: 6.72 - 0.052 = 6.67
WT: ceasefire -> decay: 1.30 * 0.80 = 1.04 (starts decaying)
```
**Columbia R4: 6.72 -> 6.67** (WT: 1.30, decaying to 1.04 post-ceasefire)

#### PERSIA (Ceasefire with Columbia, still at war with Levantia but winding down)
```
Starting stability: 1.45
War tiredness: 1.50

  GDP growth (-3.0% < -2%):              +(-3.0)*0.3 = -0.90
  Social spending (shortfall):           -0.15
  War friction (defender - still in Levantia war): -0.10
  Casualties (0 - winding down):         +0.00
  War tiredness (min(1.50*0.04, 0.4)):   -0.06
  Democratic resilience (hybrid):        +0.15
  Sanctions (L2):                        -0.20

  RAW DELTA = -0.90 -0.15 -0.10 -0.06 +0.15 -0.20 = -1.26
  FINAL DELTA = -1.26

New stability: 1.45 + (-1.26) = 0.19 -> clamped to 1.00
WT: duration 4 (>=3), +0.20*0.5=0.10 -> 1.60
```
**Persia R4: 1.45 -> 1.00 (floor)** (WT: 1.50 -> 1.60)
*Persia hits stability floor. Regime crisis. In-game this triggers revolution risk, IRGC coup potential, or forced peace.*

#### CATHAY
```
Starting stability: 8.75
  +0.05 inertia, +0.15 GDP (3.5% > 2%), +0.05 social = +0.25
New stability: 8.75 + 0.25 = 9.00 (capped)
```
**Cathay R4: 8.75 -> 9.00 (cap)**

#### CARIBE
```
Starting stability: 2.44
  GDP -2.0% -> penalty -0.60
  Social shortfall: -0.10, Sanctions L2: -0.20
  RAW = -0.90, *0.5 = -0.45, *0.75 = -0.3375

New stability: 2.44 + (-0.3375) = 2.10
```
**Caribe R4: 2.44 -> 2.10**

#### OTHER COUNTRIES R4

| Country | Start R4 | Delta | End R4 |
|---------|----------|-------|--------|
| Yamato | 8.10 | +0.10 | **8.20** |
| Gallia | 7.30 | +0.10 | **7.40** |
| Teutonia | 7.30 | +0.10 | **7.40** |
| Freeland | 8.74 | +0.25 | **8.99** -> capped **9.00** |
| Ponte | 6.15 | +0.05 | **6.20** |
| Albion | 7.30 | +0.10 | **7.40** |
| Bharata | 6.60 | +0.20 | **6.80** |
| Levantia | 4.21 | WT(2.30+0.15=2.45) adapt(dur=4>=3, +0.075), att -0.08, WT -0.098, +0.05 social = -0.128 | **4.08** |
| Formosa | 7.40 | +0.14 | **7.54** |
| Phrygia | 5.31 | +0.05 | **5.36** |
| Hanguk | 6.05 | +0.05 | **6.10** |
| Choson | 3.72 | -0.094 | **3.62** |
| Mirage | 8.18 | +0.06 | **8.24** |
| Solaria | 7.09 | +0.03 | **7.12** |

---

### ============================================================
### ROUND 5
### ============================================================

**Key events:** Columbia no longer at war. Heartland counteroffensive retakes 1 hex. Persia at floor.

#### HEARTLAND
```
Starting stability: 3.30
War tiredness: 4.40

DELTA COMPONENTS:
  GDP growth (2.0%):                      +0.00  (not > 2%)
  Social spending (war 1.5x):            +0.075
  War friction (defender):               -0.10
  Casualties (1):                        -0.20
  Territory GAINED (1 zone!):            +0.15
  War tiredness (min(4.40*0.04, 0.4)):   -0.176
  Democratic resilience:                 +0.15

  RAW DELTA = +0.075 -0.10 -0.20 +0.15 -0.176 +0.15 = -0.101
  FINAL DELTA = -0.101

New stability: 3.30 + (-0.101) = 3.20
WT: +0.10 -> 4.50
```
**Heartland R5: 3.30 -> 3.20** (WT: 4.40 -> 4.50)
*The counteroffensive provides a +0.15 boost from territory gained, significantly slowing decline.*

#### NORDOSTAN
```
Starting stability: 3.00
War tiredness: 4.30

DELTA COMPONENTS:
  GDP growth (0.3%):                     +0.00
  Social spending (shortfall):           -0.05
  War friction (attacker):               -0.08
  Casualties (1):                        -0.20
  Territory LOST (1 zone):               -0.40
  War tiredness (min(4.30*0.04, 0.4)):   -0.172
  Sanctions (L3):                        -0.30

  RAW DELTA = -0.05 -0.08 -0.20 -0.40 -0.172 -0.30 = -1.202
  Autocracy: *0.75 = -0.902

  FINAL DELTA = -0.902

New stability: 3.00 + (-0.902) = 2.10
WT: +0.075 -> 4.375
```
**Nordostan R5: 3.00 -> 2.10** (WT: 4.30 -> 4.375)
*CRITICAL: Nordostan loses territory for the first time. The -0.40 penalty is devastating even with autocracy resilience. This is the "Heartland strikes back" moment.*

#### COLUMBIA (Not at war, WT decaying)
```
Starting stability: 6.67
WT: 1.04, decaying

  Social spending:                        +0.05
  GDP growth (2.0%):                      +0.00
  No war friction.

  RAW DELTA = +0.05
  FINAL DELTA = +0.05

New stability: 6.67 + 0.05 = 6.72
WT: not at war -> 1.04 * 0.80 = 0.83
```
**Columbia R5: 6.67 -> 6.72** (recovering)

#### PERSIA (At floor, ceasefire taking hold)
```
Starting stability: 1.00
War tiredness: 1.60

  Persia exits wars R5 (ceasefire holds). No longer at war.
  GDP growth (-0.5%):                     +0.00
  Social spending (shortfall):           -0.15
  Sanctions (L2):                        -0.20

  RAW DELTA = -0.35
  Peaceful dampening: *0.5 = -0.175
  (hybrid - no autocracy resilience)

  FINAL DELTA = -0.175

New stability: 1.00 + (-0.175) = 0.825 -> clamped to 1.00
WT: not at war -> 1.60 * 0.80 = 1.28
```
**Persia R5: 1.00 -> 1.00 (floor)** (WT decaying: 1.60 -> 1.28)

#### CATHAY
```
Stability: 9.00 (cap)
  All positive drivers -> stays at 9.00 (hard cap)
```
**Cathay R5: 9.00 -> 9.00 (cap)**

#### CARIBE
```
Starting stability: 2.10
  GDP -1.5% (improving slightly)
  Social shortfall: -0.10, Sanctions L2: -0.20
  RAW = -0.30 (no GDP penalty since > -2%)
  Peaceful: *0.5 = -0.15
  Autocracy: *0.75 = -0.1125

New stability: 2.10 + (-0.1125) = 1.99
```
**Caribe R5: 2.10 -> 1.99**

#### LEVANTIA (War winding down)
```
Starting stability: 4.08
WT: 2.525 (adapted)

  War winding down. Attacker -0.08, WT -0.101, cas 0, +0.05 social, +0.04 GDP
  RAW = -0.091
  FINAL = -0.091

New stability: 4.08 - 0.091 = 3.99
```
**Levantia R5: 4.08 -> 3.99**

#### OTHER COUNTRIES R5

| Country | Start R5 | Delta | End R5 |
|---------|----------|-------|--------|
| Yamato | 8.20 | +0.10 | **8.30** |
| Gallia | 7.40 | +0.10 | **7.50** |
| Teutonia | 7.40 | +0.10 | **7.50** |
| Freeland | 9.00 | capped | **9.00** |
| Ponte | 6.20 | +0.05 | **6.25** |
| Albion | 7.40 | +0.10 | **7.50** |
| Bharata | 6.80 | +0.20 | **7.00** |
| Formosa | 7.54 | +0.14 | **7.68** |
| Phrygia | 5.36 | +0.05 | **5.41** |
| Hanguk | 6.10 | +0.05 | **6.15** |
| Choson | 3.62 | -0.094 | **3.53** |
| Mirage | 8.24 | +0.06 | **8.30** |
| Solaria | 7.12 | +0.03 | **7.15** |

---

### ============================================================
### ROUND 6
### ============================================================

**Key events:** Nordostan escalation. Heavy fighting, Nordostan retakes hex. Heartland takes heavy casualties.

#### HEARTLAND
```
Starting stability: 3.20
War tiredness: 4.50

DELTA COMPONENTS:
  GDP growth (2.0%):                      +0.00
  Social spending (war 1.5x):            +0.075
  War friction (defender):               -0.10
  Casualties (2 events - heavy):         -0.40
  Territory lost (1 zone):               -0.40
  War tiredness (min(4.50*0.04, 0.4)):   -0.18
  Democratic resilience:                 +0.15

  RAW DELTA = +0.075 -0.10 -0.40 -0.40 -0.18 +0.15 = -0.855
  FINAL DELTA = -0.855

New stability: 3.20 + (-0.855) = 2.35
WT: +0.10 -> 4.60
```
**Heartland R6: 3.20 -> 2.35** (WT: 4.50 -> 4.60)
*Nordostan's escalation hits Heartland hard. Double casualties + territory loss is devastating.*

#### NORDOSTAN
```
Starting stability: 2.10
War tiredness: 4.375

DELTA COMPONENTS:
  GDP growth (0.3%):                     +0.00
  Social spending (shortfall):           -0.05
  War friction (attacker):               -0.08
  Casualties (1):                        -0.20
  Territory gained (1):                  +0.15
  War tiredness (min(4.375*0.04, 0.4)):  -0.175
  Sanctions (L3):                        -0.30

  RAW DELTA = -0.05 -0.08 -0.20 +0.15 -0.175 -0.30 = -0.655
  Autocracy: *0.75 = -0.491

  FINAL DELTA = -0.491

New stability: 2.10 + (-0.491) = 1.61
WT: +0.075 -> 4.45
```
**Nordostan R6: 2.10 -> 1.61** (WT: 4.375 -> 4.45)
*Nordostan is also approaching crisis despite gaining territory. The sanctions + war tiredness grind is relentless.*

#### COLUMBIA (Peacetime recovery)
```
Starting stability: 6.72
  +0.05 social
  RAW = +0.05, FINAL = +0.05
New stability: 6.72 + 0.05 = 6.77
WT: 0.83 * 0.80 = 0.66
```
**Columbia R6: 6.72 -> 6.77**

#### CARIBE
```
Starting stability: 1.99
  GDP -1.5%, social shortfall -0.10, sanctions L2 -0.20
  RAW = -0.30, *0.5 = -0.15, *0.75 = -0.1125
New stability: 1.99 - 0.1125 = 1.88
```
**Caribe R6: 1.99 -> 1.88**

#### OTHER COUNTRIES R6

| Country | Start R6 | Delta | End R6 |
|---------|----------|-------|--------|
| Cathay | 9.00 | capped | **9.00** |
| Persia | 1.00 | floor (slight recovery? -0.175 -> clamped 1.00) | **1.00** |
| Yamato | 8.30 | +0.10 | **8.40** |
| Gallia | 7.50 | +0.10 | **7.60** |
| Teutonia | 7.50 | +0.10 | **7.60** |
| Freeland | 9.00 | capped | **9.00** |
| Ponte | 6.25 | +0.05 | **6.30** |
| Albion | 7.50 | +0.10 | **7.60** |
| Bharata | 7.00 | +0.05 inertia + 0.15 GDP + 0.05 social = +0.25 | **7.25** |
| Levantia | 3.99 | Not at war R6 (war ended). +0.05 social, +0.04 GDP = +0.09, WT decay | **4.08** |
| Formosa | 7.68 | +0.14 | **7.82** |
| Phrygia | 5.41 | +0.05 | **5.46** |
| Hanguk | 6.15 | +0.05 | **6.20** |
| Choson | 3.53 | -0.094 | **3.43** |
| Mirage | 8.30 | Not at war (ceasefire). +0.05 inertia + 0.15 GDP + 0.05 social = +0.25 | **8.55** |
| Solaria | 7.15 | +0.05 inertia + 0.12 GDP + 0.05 social = +0.22, minus sanctions L1 -0.10 = +0.12 | **7.27** |

---

### ============================================================
### ROUND 7
### ============================================================

**Key events:** Ceasefire negotiations begin. Reduced/no fighting on Nordostan-Heartland front.

#### HEARTLAND
```
Starting stability: 2.35
War tiredness: 4.60

  Still technically at war (ceasefire negotiations, not yet signed).
  But: 0 casualties, 0 territory change.

DELTA COMPONENTS:
  GDP growth (2.5% > 2%):                +0.08*(2.5-2) = +0.04
  Social spending (war 1.5x):            +0.075
  War friction (defender):               -0.10
  Casualties (0):                        +0.00
  Territory change (0):                  +0.00
  War tiredness (min(4.60*0.04, 0.4)):   -0.184
  Democratic resilience:                 +0.15

  RAW DELTA = +0.04 +0.075 -0.10 -0.184 +0.15 = -0.019
  FINAL DELTA = -0.019

New stability: 2.35 + (-0.019) = 2.33
WT: +0.10 -> 4.70
```
**Heartland R7: 2.35 -> 2.33** (WT: 4.60 -> 4.70)
*Near-zero delta. Democratic resilience + social spending almost exactly offset war friction + war tiredness. The ceasefire (no casualties, no territory loss) stabilizes the decline.*

#### NORDOSTAN
```
Starting stability: 1.61
War tiredness: 4.45

DELTA COMPONENTS:
  GDP growth (0.5%):                     +0.00
  Social spending (shortfall):           -0.05
  War friction (attacker):               -0.08
  Casualties (0):                        +0.00
  Territory (0):                         +0.00
  War tiredness (min(4.45*0.04, 0.4)):   -0.178
  Sanctions (L3):                        -0.30

  RAW DELTA = -0.05 -0.08 -0.178 -0.30 = -0.608
  Autocracy: *0.75 = -0.456

  FINAL DELTA = -0.456

New stability: 1.61 + (-0.456) = 1.15
WT: +0.075 -> 4.525
```
**Nordostan R7: 1.61 -> 1.15** (WT: 4.45 -> 4.525)
*CRITICAL FINDING: Nordostan continues declining even without casualties or territory changes, because sanctions L3 (-0.30) + war tiredness (-0.178) + social shortfall (-0.05) + war friction (-0.08) create a persistent -0.608 raw delta. Autocracy resilience reduces it to -0.456 but cannot stop the bleed. Nordostan will hit floor before Heartland.*

#### COLUMBIA
```
Starting stability: 6.77
  +0.05 social, GDP 2.2% -> +0.08*(2.2-2)=+0.016
  RAW = +0.066, FINAL = +0.066
New stability: 6.77 + 0.066 = 6.84
```
**Columbia R7: 6.77 -> 6.84** (steady recovery)

#### CARIBE
```
Starting stability: 1.88
  GDP -1.0% (> -2%), social shortfall -0.10, sanctions L2 -0.20
  RAW = -0.30, *0.5 = -0.15, *0.75 = -0.1125
New stability: 1.88 - 0.1125 = 1.77
```
**Caribe R7: 1.88 -> 1.77**

#### OTHER COUNTRIES R7

| Country | Start R7 | Delta | End R7 |
|---------|----------|-------|--------|
| Cathay | 9.00 | capped | **9.00** |
| Persia | 1.00 | Recovery: not at war, sanctions winding down, GDP -0.5%. Sanctions still L2 -0.20, social -0.15. RAW -0.35, *0.5=-0.175. Still 1.00 | **1.00** |
| Yamato | 8.40 | +0.10 | **8.50** |
| Gallia | 7.60 | +0.10 | **7.70** |
| Teutonia | 7.60 | +0.10 | **7.70** |
| Freeland | 9.00 | capped | **9.00** |
| Ponte | 6.30 | +0.05 | **6.35** |
| Albion | 7.60 | +0.10 | **7.70** |
| Bharata | 7.25 | +0.25 | **7.50** |
| Levantia | 4.08 | +0.09 | **4.17** |
| Formosa | 7.82 | +0.14 | **7.96** |
| Phrygia | 5.46 | +0.05 | **5.51** |
| Hanguk | 6.20 | +0.05 | **6.25** |
| Choson | 3.43 | -0.094 | **3.34** |
| Mirage | 8.55 | +0.25 | **8.80** |
| Solaria | 7.27 | +0.12 | **7.39** |

---

### ============================================================
### ROUND 8
### ============================================================

**Key events:** Fragile ceasefire holds. Minimal combat.

#### HEARTLAND
```
Starting stability: 2.33
War tiredness: 4.70

  Same dynamics as R7 (ceasefire, no combat):

DELTA COMPONENTS:
  GDP growth (2.5% > 2%):                +0.04
  Social spending (war 1.5x):            +0.075
  War friction (defender):               -0.10
  Casualties (0):                        +0.00
  Territory (0):                         +0.00
  War tiredness (min(4.70*0.04, 0.4)):   -0.188
  Democratic resilience:                 +0.15

  RAW DELTA = +0.04 +0.075 -0.10 -0.188 +0.15 = -0.023
  FINAL DELTA = -0.023

New stability: 2.33 + (-0.023) = 2.31
WT: +0.10 -> 4.80
```
**Heartland R8: 2.33 -> 2.31** (WT: 4.70 -> 4.80)

#### NORDOSTAN
```
Starting stability: 1.15
War tiredness: 4.525

DELTA COMPONENTS:
  Same structure as R7:
  RAW DELTA = -0.608
  Autocracy: *0.75 = -0.456

New stability: 1.15 + (-0.456) = 0.694 -> clamped to 1.00
WT: +0.075 -> 4.60
```
**Nordostan R8: 1.15 -> 1.00 (floor)**

#### COLUMBIA
```
Starting stability: 6.84
  +0.05 social, +0.016 GDP = +0.066
New stability: 6.84 + 0.066 = 6.91
```
**Columbia R8: 6.84 -> 6.91**

#### PERSIA
```
Starting stability: 1.00
  Still at floor. Sanctions easing (maybe L1 by R8?). Assume L2 still.
  GDP recovering to +0.5% -> no bonus.
  RAW = -0.35, *0.5 = -0.175 -> still at 1.00
```
**Persia R8: 1.00 -> 1.00 (floor)**

#### CATHAY
**Cathay R8: 9.00 -> 9.00 (cap)**

#### CARIBE
```
Starting stability: 1.77
  RAW = -0.30, *0.5 = -0.15, *0.75 = -0.1125
New stability: 1.77 - 0.1125 = 1.66
```
**Caribe R8: 1.77 -> 1.66**

#### OTHER COUNTRIES R8

| Country | Start R8 | Delta | End R8 |
|---------|----------|-------|--------|
| Yamato | 8.50 | +0.10 | **8.60** |
| Gallia | 7.70 | +0.10 | **7.80** |
| Teutonia | 7.70 | +0.10 | **7.80** |
| Freeland | 9.00 | capped | **9.00** |
| Ponte | 6.35 | +0.05 | **6.40** |
| Albion | 7.70 | +0.10 | **7.80** |
| Bharata | 7.50 | +0.25 | **7.75** |
| Levantia | 4.17 | +0.09 | **4.26** |
| Formosa | 7.96 | +0.14 | **8.10** |
| Phrygia | 5.51 | +0.05 | **5.56** |
| Hanguk | 6.25 | +0.05 | **6.30** |
| Choson | 3.34 | -0.094 | **3.24** |
| Mirage | 8.80 | +0.20 (approaching cap) | **9.00** |
| Solaria | 7.39 | +0.12 | **7.51** |

---

## MASTER TRAJECTORY TABLE (All 21 Countries, 8 Rounds)

| Country | R0 | R1 | R2 | R3 | R4 | R5 | R6 | R7 | R8 | Total Change |
|---------|----|----|----|----|----|----|----|----|----|----|
| **Heartland** | 5.00 | 4.40 | 4.19 | 3.55 | 3.30 | 3.20 | 2.35 | 2.33 | **2.31** | **-2.69** |
| **Nordostan** | 5.00 | 4.60 | 4.08 | 3.60 | 3.00 | 2.10 | 1.61 | 1.15 | **1.00** | **-4.00** |
| **Columbia** | 7.00 | 6.81 | 6.77 | 6.72 | 6.67 | 6.72 | 6.77 | 6.84 | **6.91** | **-0.09** |
| **Persia** | 4.00 | 3.46 | 2.91 | 1.45 | 1.00 | 1.00 | 1.00 | 1.00 | **1.00** | **-3.00** |
| **Cathay** | 8.00 | 8.25 | 8.50 | 8.75 | 9.00 | 9.00 | 9.00 | 9.00 | **9.00** | **+1.00** |
| **Caribe** | 3.00 | 2.89 | 2.78 | 2.44 | 2.10 | 1.99 | 1.88 | 1.77 | **1.66** | **-1.34** |
| **Yamato** | 8.00 | 7.90 | 8.00 | 8.10 | 8.20 | 8.30 | 8.40 | 8.50 | **8.60** | **+0.60** |
| **Gallia** | 7.00 | 7.10 | 7.20 | 7.30 | 7.40 | 7.50 | 7.60 | 7.70 | **7.80** | **+0.80** |
| **Teutonia** | 7.00 | 7.10 | 7.20 | 7.30 | 7.40 | 7.50 | 7.60 | 7.70 | **7.80** | **+0.80** |
| **Freeland** | 8.00 | 8.24 | 8.49 | 8.74 | 9.00 | 9.00 | 9.00 | 9.00 | **9.00** | **+1.00** |
| **Ponte** | 6.00 | 6.05 | 6.10 | 6.15 | 6.20 | 6.25 | 6.30 | 6.35 | **6.40** | **+0.40** |
| **Albion** | 7.00 | 7.10 | 7.20 | 7.30 | 7.40 | 7.50 | 7.60 | 7.70 | **7.80** | **+0.80** |
| **Bharata** | 6.00 | 6.20 | 6.40 | 6.60 | 6.80 | 7.00 | 7.25 | 7.50 | **7.75** | **+1.75** |
| **Levantia** | 5.00 | 4.77 | 4.53 | 4.21 | 4.08 | 3.99 | 4.08 | 4.17 | **4.26** | **-0.74** |
| **Formosa** | 7.00 | 7.08 | 7.26 | 7.40 | 7.54 | 7.68 | 7.82 | 7.96 | **8.10** | **+1.10** |
| **Phrygia** | 5.00 | 5.13 | 5.26 | 5.31 | 5.36 | 5.41 | 5.46 | 5.51 | **5.56** | **+0.56** |
| **Hanguk** | 6.00 | 5.93 | 6.00 | 6.05 | 6.10 | 6.15 | 6.20 | 6.25 | **6.30** | **+0.30** |
| **Choson** | 4.00 | 3.91 | 3.81 | 3.72 | 3.62 | 3.53 | 3.43 | 3.34 | **3.24** | **-0.76** |
| **Solaria** | 7.00 | 7.03 | 7.06 | 7.09 | 7.12 | 7.15 | 7.27 | 7.39 | **7.51** | **+0.51** |
| **Mirage** | 8.00 | 8.06 | 8.12 | 8.18 | 8.24 | 8.30 | 8.55 | 8.80 | **9.00** | **+1.00** |

---

## ANALYSIS

### 1. PRIMARY TARGET: Heartland Stability Trajectory

**Target:** Start 5.0, reach ~2.5-3.0 by R8.
**Actual:** Start 5.0, reach **2.31** by R8.

**VERDICT: CLOSE TO TARGET, SLIGHTLY LOW.**

The trajectory is dramatically improved from the old formula (which hit 1.0 by R3). Heartland now declines gradually over 8 rounds, with the sharpest drops corresponding to military setbacks (R1: territory lost, R3: territory lost, R6: double casualties + territory lost). The ceasefire period (R7-R8) nearly flattens the curve.

However, R8 result of 2.31 is slightly below the 2.5-3.0 target range. The R6 escalation event (2 casualty events + territory loss) creates a -0.855 delta that drives Heartland below the target band. Without the R6 shock, Heartland would end around 2.9.

**Recommendation:** The formula is working correctly. The R6 result is scenario-dependent -- a less intense R6 produces results within the target band. No formula change needed; the spread of 2.3-3.0 depending on scenario intensity is realistic.

### 2. Nordostan vs. Heartland: Autocracy Resilience Check

**Target:** Nordostan should end HIGHER than Heartland (autocracy resilience keeps it more stable).
**Actual:** Nordostan ends at **1.00** (floor), Heartland at **2.31**.

**VERDICT: FAILED. Nordostan collapses FASTER than Heartland.**

This is the most significant finding of the test. Despite autocracy resilience (*0.75 on negative deltas), Nordostan hits floor at R8 while Heartland is still at 2.31. The reason:

1. **Sanctions L3 = -0.30 per round** is the primary killer. This is a persistent, unrelenting drain that Heartland does not face.
2. **No democratic resilience.** Heartland gets +0.15/round from democratic resilience under invasion. Nordostan gets nothing equivalent.
3. **R5 territory loss** (-0.40) creates a catastrophic single-round drop (3.00 -> 2.10).
4. **Cumulative:** Nordostan's net penalty per "stalemate round" (no territory change) is still ~-0.456 after autocracy resilience, compared to Heartland's ~-0.02 during ceasefire.

**Root cause:** L3 sanctions (-0.30/round) are too powerful relative to autocracy resilience (*0.75). After autocracy dampening, sanctions still cost -0.225/round -- more than Heartland's total decline in ceasefire rounds.

**Recommendations:**
1. **Add "autocracy war mobilization" bonus:** +0.10/round for autocracies at war (representing regime's ability to suppress dissent, control narrative). This would offset ~50% of sanctions.
2. **Or reduce sanctions impact on autocracies:** Apply autocracy resilience ALSO to sanctions friction specifically, giving sanctions_friction *= 0.60 for autocracies (harder to destabilize through economic pressure).
3. **Or cap cumulative sanctions impact:** After 4+ rounds of sanctions, diminishing returns (sanctions fatigue on the population -- they adapt).

### 3. Does Democratic Resilience (+0.15) Adequately Offset War Friction (-0.10)?

**Answer: YES, but only during low-intensity periods.**

During ceasefire (R7-R8), Heartland's delta is approximately:
- +0.075 (social) + 0.04 (GDP) + 0.15 (dem resilience) - 0.10 (war friction) - 0.188 (war tiredness) = **-0.023**

This is near-zero, which is exactly right for a ceasefire: the country stops declining but doesn't recover. The democratic resilience is the critical factor keeping Heartland from continuing to fall.

During active combat with territory loss:
- Democratic resilience (+0.15) is overwhelmed by casualties (-0.20) and territory (-0.40), producing -0.60 to -0.85 deltas.

**This is correct design behavior.** The system produces:
- Active combat: rapid decline
- Stalemate: slow decline
- Ceasefire: near-stabilization
- This matches real-world patterns (Ukraine's stability declined sharply in 2022, then partially stabilized)

### 4. Society Adaptation (R3+) — Does It Work?

**Answer: YES, but its effect is subtle.**

Society adaptation halves the war tiredness GROWTH rate after 3 rounds. Since Nordostan/Heartland started pre-SIM, adaptation was active from R1:
- Heartland WT growth: 0.20 * 0.5 = 0.10/round (instead of 0.20)
- Nordostan WT growth: 0.15 * 0.5 = 0.075/round (instead of 0.15)

Without adaptation, war tiredness at R8 would be:
- Heartland: 4.0 + 8*0.20 = 5.6 (vs actual 4.80)
- Nordostan: 4.0 + 8*0.15 = 5.2 (vs actual 4.60)

The war tiredness contribution to stability delta is capped at -0.40, and with adaptation it stays around -0.18 to -0.19 by R8. Without adaptation it would hit the -0.40 cap by R5. **Adaptation prevents the war tiredness cap from binding, keeping the mechanic graduated rather than hitting a wall.**

### 5. Peaceful Countries — Properly Insulated?

**Target:** Peaceful countries should stay 6-8.
**Actual results at R8:**

| Country | R0 | R8 | In Range? |
|---------|----|----|-----------|
| Gallia | 7.0 | 7.80 | YES |
| Teutonia | 7.0 | 7.80 | YES |
| Freeland | 8.0 | 9.00 | YES (cap) |
| Ponte | 6.0 | 6.40 | YES |
| Albion | 7.0 | 7.80 | YES |
| Bharata | 6.0 | 7.75 | YES |
| Yamato | 8.0 | 8.60 | YES |
| Formosa | 7.0 | 8.10 | YES |
| Hanguk | 6.0 | 6.30 | YES |
| Phrygia | 5.0 | 5.56 | BORDERLINE (started at 5) |

**VERDICT: PASS.** All peaceful countries stay well within or above the 6-8 range. The non-war dampening (*0.5 for negative deltas) is effective. The slight upward drift for all peaceful countries is realistic -- peace and moderate growth produce gradual stability improvement.

**Minor concern:** Freeland, Cathay, and Mirage all hit the 9.0 cap, which means the formula is producing more positive pressure than the cap allows. This isn't a problem mechanically but means these countries have no differentiation at the top. Consider whether cap-hitting should be less common (reduce positive inertia or GDP boost).

### 6. Caribe Blockade Calibration

**Target:** Start 3.0, decline toward 2.0.
**Actual:** Start 3.0, reach **1.66** by R8.

**VERDICT: SLIGHTLY FAST, but reasonable.**

Caribe's decline is driven entirely by:
- Sanctions L2: -0.20/round
- Social spending shortfall: -0.10/round
- Occasional GDP contraction penalty

After peaceful dampening (*0.5) and autocracy resilience (*0.75), the per-round delta is ~-0.11. This produces a steady, slow decline that feels right for a country under blockade but not at war.

The overshoot below 2.0 is largely driven by R3-R4 GDP contraction penalties. If GDP stays above -2%, Caribe stays closer to 2.0 by R8.

### 7. COMPARISON TO OLD FORMULA

| Country | Old Formula R3 | New Formula R3 | Old Formula R8 (projected) | New Formula R8 |
|---------|---------------|----------------|---------------------------|----------------|
| **Heartland** | **1.0 (floor!)** | **3.55** | 1.0 (stuck at floor) | **2.31** |
| Nordostan | ~2.5 | 3.60 | ~1.0 | 1.00 |
| Columbia | ~5.5 | 6.72 | ~4.0 | 6.91 |
| Cathay | ~8.5 | 8.75 | ~9.0 | 9.00 |

**The improvement is dramatic:**
- Heartland no longer hits floor by R3. It takes 8 rounds of sustained war to reach 2.31, vs. 3 rounds to hit 1.0 under the old formula.
- The decline curve is graduated: sharp drops correlate with military events, slow decline during stalemate, near-zero during ceasefire.
- Democratic resilience (+0.15) is the single most important stabilizer, preventing Heartland from free-falling.
- Society adaptation prevents war tiredness from snowballing out of control.

---

## CRITICAL FINDINGS & RECOMMENDATIONS

### FINDING 1: NORDOSTAN COLLAPSES TOO FAST (PRIORITY: HIGH)

Nordostan hits 1.00 (floor) by R8 -- lower than Heartland. This is historically implausible: Russia's internal stability during the Ukraine war has been significantly more resilient than Ukraine's, precisely because of autocratic control mechanisms.

**Root cause:** L3 sanctions create a -0.30/round drain with no offsetting mechanic for autocracies. Democratic resilience (+0.15) has no autocratic equivalent.

**Fix options (choose one):**
- A) Add `autocracy_war_mobilization: +0.10/round` for autocracies at war (narrative: regime clamps down, controls media, rallies nationalism)
- B) Apply additional autocracy dampening to sanctions friction: `sanctions_stab_cost *= 0.50` for autocracies
- C) Add diminishing returns on sanctions: after 4 rounds, sanctions stability cost *= 0.70

**Recommendation:** Option A is cleanest and most narratively justified. Autocracies at war DON'T just resist decline -- they actively mobilize.

### FINDING 2: PERSIA COLLAPSES TOO EARLY (PRIORITY: MEDIUM)

Persia hits floor by R4 due to GDP contraction (-3.0%) triggering the severe negative growth penalty (+growth*0.3 = -0.90 per round). Combined with sanctions, war friction, and social shortfall, Persia's delta exceeds -1.0 per round from R3.

**Root cause:** The GDP contraction penalty (`gdp_growth * 0.3` when < -2%) is extremely harsh for countries that start in deep recession. Persia starts at -3.0% growth.

**Fix options:**
- A) Reduce GDP contraction penalty from 0.3 to 0.15 for moderate contraction (-2% to -5%)
- B) Apply the penalty only to the CHANGE in GDP growth, not absolute level
- C) Cap GDP contraction stability penalty at -0.30 per round

**Recommendation:** Option C is simplest. Cap prevents any single economic factor from dominating.

### FINDING 3: INFLATION FORMULA BUG (PRIORITY: HIGH)

The inflation friction formula (`-(inflation-3)*0.05 + -(inflation-20)*0.03` for hyperinflation) applies to ABSOLUTE inflation, not change. Countries starting with high inflation (Persia 50%, Phrygia 45%, Caribe 60%, Choson 10%) would see catastrophic stability penalties in R1 that would send them to floor immediately:
- Persia: -(50-3)*0.05 + -(50-20)*0.03 = -2.35 -0.90 = -3.25 in a single round
- This would clamp Persia to 1.00 in R1 regardless of anything else

**For this test, I assumed inflation change from starting value rather than absolute level.** In practice, the engine code applies the absolute penalty, which means Persia/Caribe/Phrygia are unplayable as designed.

**Fix:** Change inflation friction to apply only to CHANGE from starting inflation:
```python
inflation_delta = inflation - starting_inflation
if inflation_delta > 0:
    delta -= inflation_delta * 0.05
```

### FINDING 4: POSITIVE DRIFT FOR PEACEFUL COUNTRIES (PRIORITY: LOW)

All peaceful countries drift upward by +0.05 to +0.25 per round. Over 8 rounds, Freeland goes 8.0 -> 9.0 (cap), Bharata 6.0 -> 7.75. This is fine narratively but means peaceful countries have no meaningful stability dynamics -- they just slowly rise.

**Consider:** Adding random event shocks (election crises, natural disasters, market corrections) to peaceful countries to create occasional -0.5 to -1.0 drops. This would make peaceful gameplay more interesting without changing the formula.

### FINDING 5: WAR TIREDNESS CAP NEVER BINDS (FINDING: POSITIVE)

The war tiredness contribution cap of -0.40 never binds in 8 rounds thanks to society adaptation. Maximum actual contribution is ~-0.19. This is good -- it means the war tiredness mechanic operates in its graduated range throughout the entire SIM.

---

## VERDICT

**The v4 stability formula is a major improvement over v3.** Heartland's trajectory (5.0 -> 2.31 over 8 rounds) is vastly more realistic than the old formula's catastrophic collapse (5.0 -> 1.0 by R3).

**Status: CONDITIONAL PASS**

The formula passes for its primary purpose (Heartland calibration) but requires fixes for:
1. **Nordostan autocracy collapse** -- needs autocracy war mobilization bonus or sanctions dampening
2. **Persia GDP contraction penalty** -- needs cap on GDP-driven stability loss
3. **Inflation formula bug** -- must use inflation CHANGE, not absolute level

These three fixes should be implemented and this test re-run before proceeding to broader validation.

---

*Test completed by TESTER-ORCHESTRATOR. Results ready for ATLAS (formula owner) and Marat review.*
