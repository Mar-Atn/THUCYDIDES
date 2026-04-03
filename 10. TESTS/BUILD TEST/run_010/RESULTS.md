# TTT Scenario Test Results
**Date:** 2026-04-03 14:34
**Engine:** economic.py + political.py + AI Judgment (Pass 2)
**Data:** countries.csv (D1-D18 calibration applied)
**Scenarios:** 5 × 6 rounds

---
## S1: Baseline (no intervention)

_All countries on autopilot. Tests natural economic trajectories, budget balance, and stability._

### GDP Trajectories

| Round | Oil$ | Columb | Cathay | Sarmat | Ruthen | Persia | Teuton | Bharat | Formos |
|-------|------|------|------|------|------|------|------|------|------|
| R0 | $80 | 280 (+1.8%) | 190 (+4.0%) | 20 (+1.0%) | 2 (+2.5%) | 5 (+0.5%) | 45 (+1.2%) | 42 (+6.5%) | 8 (+3.0%) |
| R1 | $86 | 283 (+1.1%) | 194 (+2.1%) | 20 (+0.6%) | 2 (+1.1%) | 5 (+0.3%) | 45 (+0.6%) | 43 (+3.4%) | 8 (+1.5%) |
| R2 | $98 | 286 (+1.1%) | 197 (+1.6%) | 20 (+0.8%) | 2 (+1.1%) | 5 (+0.5%) | 45 (+0.3%) | 45 (+3.1%) | 8 (+1.3%) |
| R3 | $86 | 289 (+1.1%) | 201 (+2.1%) | 20 (+0.6%) | 2 (+1.3%) | 5 (+0.3%) | 46 (+0.6%) | 46 (+3.4%) | 8 (+1.5%) |
| R4 | $83 | 292 (+1.0%) | 206 (+2.2%) | 21 (+0.6%) | 2 (+1.3%) | 5 (+0.3%) | 46 (+0.6%) | 48 (+3.4%) | 8 (+1.6%) |
| R5 | $82 | 295 (+1.0%) | 211 (+2.3%) | 21 (+0.6%) | 2 (+1.3%) | 5 (+0.3%) | 46 (+0.6%) | 50 (+3.5%) | 9 (+1.6%) |
| R6 | $82 | 298 (+1.0%) | 215 (+2.3%) | 21 (+0.6%) | 2 (+1.3%) | 5 (+0.3%) | 46 (+0.6%) | 51 (+3.5%) | 9 (+1.6%) |

### Stability & Support

| Round | Columb S/Sup | Cathay S/Sup | Sarmat S/Sup | Ruthen S/Sup | Persia S/Sup | Teuton S/Sup |
|-------|----------|----------|----------|----------|----------|----------|
| R0 | 7.0/38% | 8.0/58% | 5.0/55% | 5.0/52% | 4.0/40% | 7.0/45% |
| R1 | 7.0/35% | 8.1/59% | 4.9/54% | 4.8/48% | 3.6/38% | 7.1/45% |
| R2 | 7.0/34% | 8.2/61% | 4.8/53% | 4.7/43% | 3.3/36% | 7.2/44% |
| R3 | 7.0/32% | 8.3/62% | 4.6/51% | 4.5/38% | 2.9/31% | 7.3/44% |
| R4 | 6.9/29% | 8.4/63% | 4.5/50% | 4.3/34% | 2.6/26% | 7.4/44% |
| R5 | 6.9/28% | 8.6/65% | 4.3/49% | 4.1/31% | 2.3/24% | 7.5/44% |
| R6 | 6.6/28% | 8.7/66% | 4.2/47% | 3.9/27% | 1.6/14% | 7.6/44% |

**Market Indexes (R6):** Wall Street=91, Europa=98, Dragon=98

**Coefficients (R6):** Sarmatia: sanctions=0.964, tariffs=1.000 | Persia: sanctions=0.950, tariffs=1.000

**Revolutions:** persia: major

### AI Judgment (Pass 2)

**R1:** 6 adjustments (confidence 80%)
  Flags: caribe_hyperinflation
  _caribe crisis from hyperinflation, war states showing stress, regional tensions emerging_
  -   JUDGMENT: caribe → CRISIS (GDP -1.5%): hyperinflation 60%, massive debt 501%, economic collapse
  -   JUDGMENT: persia stability 4.0→3.7: war stress, sanctions bite, inflation 50%
  -   JUDGMENT: phrygia stability 5.0→4.8: inflation 45% eroding public confidence
  -   JUDGMENT: columbia support 37%→35%: war costs rising, inflation up
  -   JUDGMENT: hanguk support 35%→32%: economic stagnation, regional tensions
  -   JUDGMENT: dragon index 99→96: formosa tension fears, supply chain anxiety

**R2:** 6 adjustments (confidence 80%)
  Flags: caribe_hyperinflation
  _Crisis limited to Caribe. War fatigue emerging. Inflation pressures building._
  -   JUDGMENT: caribe → CRISIS (GDP -1.5%): hyperinflation 60%, low stability, debt spiral
  -   JUDGMENT: persia stability 3.6→3.3: war stress, sanctions bite, inflation surge
  -   JUDGMENT: phrygia stability 4.9→4.7: high inflation eroding public confidence
  -   JUDGMENT: columbia support 36%→34%: war costs rising, inflation up
  -   JUDGMENT: hanguk support 32%→29%: economic concerns, regional tensions
  -   JUDGMENT: europa index 100→96: energy concerns, sanctions impact

**R3:** 5 adjustments (confidence 80%)
  Flags: caribe_crisis
  _Caribe hyperinflation crisis, war fatigue hitting Columbia/Persia_
  -   JUDGMENT: caribe → CRISIS (GDP -1.5%): hyperinflation 60%, low stability, debt spiral
  -   JUDGMENT: persia stability 3.2→2.9: war stress, sanctions bite, inflation surge
  -   JUDGMENT: caribe stability 2.9→2.7: economic collapse accelerating
  -   JUDGMENT: columbia support 34%→32%: war costs rising, inflation up
  -   JUDGMENT: persia support 34%→31%: hyperinflation crushing living standards

**R4:** 6 adjustments (confidence 80%)
  Flags: caribe_collapse_risk
  _Crisis deepening in Caribe, war fatigue emerging, hyperinflation biting_
  -   JUDGMENT: caribe → CRISIS (GDP -1.5%): hyperinflation 60%, low stability, debt spiral
  -   JUDGMENT: persia stability 2.9→2.6: war pressure, sanctions bite, inflation surge
  -   JUDGMENT: caribe stability 2.6→2.4: economic collapse accelerating social unrest
  -   JUDGMENT: columbia support 31%→29%: war costs rising, inflation up
  -   JUDGMENT: persia support 29%→26%: hyperinflation crushing living standards
  -   JUDGMENT: wall_street index 93→90: war uncertainty, inflation concerns

**R5:** 6 adjustments (confidence 80%)
  Flags: caribe_collapse_risk, persia_regime_pressure
  _Crisis states emerging hyperinflation war fatigue mounting pressure_
  -   JUDGMENT: caribe → CRISIS (GDP -1.5%): hyperinflation 60%, low stability, debt spiral
  -   JUDGMENT: persia → CRISIS (GDP -1.0%): war sanctions inflation 50% low support
  -   JUDGMENT: caribe stability 2.4→2.1: hyperinflation social unrest accelerating
  -   JUDGMENT: persia stability 2.5→2.3: war fatigue sanctions bite deeper
  -   JUDGMENT: columbia support 30%→28%: war costs mounting midterm pressure
  -   JUDGMENT: hanguk support 30%→28%: economic stagnation public dissatisfaction

**R6:** 6 adjustments (confidence 85%)
  Flags: persia_collapse_risk, caribe_hyperinflation
  _Crisis states deepening for Persia and Caribe. War fatigue emerging._
  -   JUDGMENT: persia → CRISIS (GDP -1.5%): War, sanctions, hyperinflation, regime collapse imminent
  -   JUDGMENT: caribe → CRISIS (GDP -1.0%): Hyperinflation, treasury depletion, stability critical
  -   JUDGMENT: persia stability 1.9→1.6: War losses accelerating regime breakdown
  -   JUDGMENT: columbia stability 6.8→6.6: War costs mounting, support eroding
  -   JUDGMENT: persia support 17%→14%: Economic collapse fueling protests
  -   JUDGMENT: caribe support 32%→28%: Hyperinflation destroying living standards


---
## S2: Economic Pressure

_Columbia escalates sanctions on Sarmatia to L3, full coalition. Gulf Gate blockade R3._

### GDP Trajectories

| Round | Oil$ | Columb | Cathay | Sarmat | Ruthen | Persia | Teuton | Bharat | Formos |
|-------|------|------|------|------|------|------|------|------|------|
| R0 | $80 | 280 (+1.8%) | 190 (+4.0%) | 20 (+1.0%) | 2 (+2.5%) | 5 (+0.5%) | 45 (+1.2%) | 42 (+6.5%) | 8 (+3.0%) |
| R1 | $86 | 283 (+1.1%) | 194 (+2.1%) | 20 (+0.6%) | 2 (+1.1%) | 5 (+0.3%) | 45 (+0.6%) | 43 (+3.4%) | 8 (+1.5%) |
| R2 | $98 | 286 (+1.1%) | 197 (+1.6%) | 20 (-2.7%) | 2 (+1.1%) | 5 (+0.5%) | 45 (+0.3%) | 45 (+3.1%) | 8 (+1.3%) |
| R3 | $118 | 290 (+1.2%) | 199 (+0.9%) | 20 (+0.3%) | 2 (+0.7%) | 5 (+0.6%) | 45 (-0.2%) | 46 (+2.7%) | 8 (+0.9%) |
| R4 | $124 | 293 (+1.2%) | 200 (+0.7%) | 20 (+1.0%) | 2 (+0.6%) | 5 (+0.7%) | 45 (-0.3%) | 47 (+2.6%) | 8 (+0.8%) |
| R5 | $125 | 297 (+1.2%) | 201 (+0.6%) | 20 (+1.0%) | 2 (+0.6%) | 5 (+0.7%) | 45 (-0.3%) | 48 (+2.5%) | 8 (+0.8%) |
| R6 | $115 | 300 (+1.2%) | 203 (+1.0%) | 21 (+4.5%) | 2 (+0.8%) | 5 (+0.4%) | 45 (-0.1%) | 50 (+2.7%) | 8 (+1.0%) |

### Stability & Support

| Round | Columb S/Sup | Cathay S/Sup | Sarmat S/Sup | Ruthen S/Sup | Persia S/Sup | Teuton S/Sup |
|-------|----------|----------|----------|----------|----------|----------|
| R0 | 7.0/38% | 8.0/58% | 5.0/55% | 5.0/52% | 4.0/40% | 7.0/45% |
| R1 | 7.0/35% | 8.1/59% | 4.9/54% | 5.0/48% | 3.6/38% | 7.1/45% |
| R2 | 7.0/34% | 8.2/61% | 4.3/52% | 4.8/43% | 3.3/36% | 7.2/44% |
| R3 | 7.0/34% | 8.3/62% | 4.2/51% | 4.7/38% | 2.9/30% | 7.3/43% |
| R4 | 6.9/30% | 8.4/63% | 4.1/49% | 4.5/34% | 2.6/29% | 7.4/42% |
| R5 | 6.9/29% | 8.5/65% | 3.9/48% | 4.3/30% | 2.3/27% | 7.5/42% |
| R6 | 6.8/28% | 8.6/66% | 3.9/46% | 4.1/26% | 1.6/20% | 7.6/41% |

**Market Indexes (R6):** Wall Street=80, Europa=97, Dragon=97

**Coefficients (R6):** Sarmatia: sanctions=0.956, tariffs=1.000 | Persia: sanctions=0.948, tariffs=1.000

**Revolutions:** persia: major

### AI Judgment (Pass 2)

**R1:** 6 adjustments (confidence 80%)
  Flags: caribe_hyperinflation
  _caribe crisis clear, war stress emerging, markets nervous about asia tensions_
  -   JUDGMENT: caribe → CRISIS (GDP -1.5%): hyperinflation 60%, massive debt 501%, economic collapse
  -   JUDGMENT: persia stability 4.0→3.7: war stress, sanctions bite, inflation surge
  -   JUDGMENT: ruthenia stability 4.8→5.0: rally effect defending homeland
  -   JUDGMENT: columbia support 37%→35%: war costs rising, inflation tick up
  -   JUDGMENT: hanguk support 35%→32%: economic stagnation, regional tensions
  -   JUDGMENT: dragon index 99→96: formosa tensions, cathay growth concerns

**R2:** 6 adjustments (confidence 80%)
  Flags: caribe_hyperinflation
  _Crisis limited to Caribe hyperinflation. War stress affecting belligerents. Market caution._
  -   JUDGMENT: caribe → CRISIS (GDP -1.5%): hyperinflation 60%, low stability, debt spiral
  -   JUDGMENT: persia stability 3.6→3.3: war stress, sanctions bite, inflation surge
  -   JUDGMENT: sarmatia stability 4.5→4.3: GDP decline, war costs mounting
  -   JUDGMENT: columbia support 36%→34%: war fatigue, inflation rising
  -   JUDGMENT: hanguk support 32%→29%: economic stagnation, low confidence
  -   JUDGMENT: europa index 100→94: energy concerns, sanctions uncertainty

**R3:** 6 adjustments (confidence 80%)
  Flags: oil_spike, inflation_pressure
  _Oil spike creating inflation pressure. Caribe entering crisis. War fatigue building._
  -   JUDGMENT: caribe → CRISIS (GDP -1.5%): hyperinflation 60%, low stability, debt spiral
  -   JUDGMENT: persia stability 3.2→2.9: war pressure, sanctions bite, inflation surge
  -   JUDGMENT: caribe stability 2.9→2.5: hyperinflation destroying social fabric
  -   JUDGMENT: hanguk support 29%→26%: economic stagnation, regional tensions
  -   JUDGMENT: persia support 34%→30%: war costs, inflation pain
  -   JUDGMENT: wall_street index 94→89: oil spike concerns, war escalation

**R4:** 6 adjustments (confidence 80%)
  Flags: caribe_hyperinflation, persia_instability
  _caribe hyperinflation crisis, persia war stress, columbia midterm pressure_
  -   JUDGMENT: caribe → CRISIS (GDP -1.5%): hyperinflation 60%, debt 504%, stability 2.5
  -   JUDGMENT: persia stability 2.9→2.6: war pressure, sanctions, 50% inflation stress
  -   JUDGMENT: caribe stability 2.5→2.2: hyperinflation social unrest deepening
  -   JUDGMENT: columbia support 33%→30%: war costs, inflation, midterm election pressure
  -   JUDGMENT: hanguk support 26%→24%: economic stagnation, low support trend
  -   JUDGMENT: wall_street index 89→84: war uncertainty, oil price concerns

**R5:** 7 adjustments (confidence 85%)
  Flags: hyperinflation_caribe, war_fatigue
  _Crisis states for hyperinflation economies, war fatigue effects, market sentiment decline_
  -   JUDGMENT: caribe → CRISIS (GDP -1.5%): 60% inflation, debt 505%, stability 2.2
  -   JUDGMENT: persia → CRISIS (GDP -1.0%): 50% inflation, war stress, stability 2.5
  -   JUDGMENT: caribe stability 2.2→1.9: hyperinflation destroying social fabric
  -   JUDGMENT: persia stability 2.5→2.3: war fatigue compounding economic stress
  -   JUDGMENT: columbia support 31%→29%: war costs rising, midterm election pressure
  -   JUDGMENT: hanguk support 24%→22%: economic stagnation, regional tensions
  -   JUDGMENT: wall_street index 86→83: oil price concerns, war escalation fears

**R6:** 7 adjustments (confidence 80%)
  Flags: crisis_deepening
  _crisis states deepening caribe persia war fatigue emerging columbia hanguk_
  -   JUDGMENT: caribe → CRISIS (GDP -1.5%): hyperinflation collapse, stability critical
  -   JUDGMENT: persia → CRISIS (GDP -1.0%): war sanctions inflation triple shock
  -   JUDGMENT: persia stability 1.9→1.6: regime legitimacy eroding under war pressure
  -   JUDGMENT: caribe stability 1.8→1.6: economic collapse accelerating social unrest
  -   JUDGMENT: hanguk support 22%→19%: economic stagnation eroding government approval
  -   JUDGMENT: columbia support 30%→28%: war costs mounting without clear victory
  -   JUDGMENT: wall_street index 86→80: persian war uncertainty weighing on sentiment


---
## S3: Tariff Wars (Prisoner's Dilemma)

_Columbia imposes L2 tariffs on Cathay R1. Cathay retaliates L2 R2. Full escalation L3 R3. Tests asymmetric impact._

### GDP Trajectories

| Round | Oil$ | Columb | Cathay | Sarmat | Ruthen | Persia | Teuton | Bharat | Formos |
|-------|------|------|------|------|------|------|------|------|------|
| R0 | $80 | 280 (+1.8%) | 190 (+4.0%) | 20 (+1.0%) | 2 (+2.5%) | 5 (+0.5%) | 45 (+1.2%) | 42 (+6.5%) | 8 (+3.0%) |
| R1 | $86 | 279 (-0.2%) | 186 (-2.0%) | 20 (+0.5%) | 2 (+1.1%) | 5 (+0.3%) | 45 (+0.4%) | 43 (+3.4%) | 8 (+1.5%) |
| R2 | $97 | 275 (-1.7%) | 185 (-0.6%) | 20 (+0.8%) | 2 (+1.1%) | 5 (+0.6%) | 45 (+0.3%) | 45 (+3.2%) | 8 (+1.3%) |
| R3 | $84 | 272 (-1.0%) | 183 (-1.1%) | 20 (+0.6%) | 2 (+1.3%) | 5 (+0.4%) | 46 (+0.5%) | 46 (+3.4%) | 8 (+1.6%) |
| R4 | $81 | 274 (+0.9%) | 186 (+1.7%) | 20 (+0.6%) | 2 (+1.4%) | 5 (+0.3%) | 45 (-1.4%) | 48 (+3.5%) | 8 (+1.6%) |
| R5 | $81 | 277 (+1.0%) | 190 (+2.3%) | 21 (+0.6%) | 2 (+1.4%) | 5 (+0.3%) | 45 (+0.6%) | 50 (+3.5%) | 9 (+1.6%) |
| R6 | $81 | 291 (+5.0%) | 207 (+8.9%) | 21 (+0.6%) | 2 (+1.4%) | 5 (+0.2%) | 45 (+0.6%) | 51 (+3.5%) | 9 (+1.6%) |

### Stability & Support

| Round | Columb S/Sup | Cathay S/Sup | Sarmat S/Sup | Ruthen S/Sup | Persia S/Sup | Teuton S/Sup |
|-------|----------|----------|----------|----------|----------|----------|
| R0 | 7.0/38% | 8.0/58% | 5.0/55% | 5.0/52% | 4.0/40% | 7.0/45% |
| R1 | 7.0/34% | 8.1/59% | 4.9/54% | 5.0/48% | 3.6/38% | 7.1/44% |
| R2 | 7.2/33% | 8.2/61% | 4.8/53% | 4.8/43% | 3.3/34% | 7.2/44% |
| R3 | 7.2/29% | 8.3/62% | 4.6/51% | 4.7/38% | 2.9/28% | 7.3/44% |
| R4 | 6.9/27% | 8.4/63% | 4.5/50% | 4.5/35% | 2.9/27% | 7.4/40% |
| R5 | 6.6/28% | 8.5/64% | 4.3/49% | 4.3/31% | 2.2/17% | 7.5/40% |
| R6 | 6.7/30% | 8.8/66% | 4.2/47% | 4.1/28% | 1.7/10% | 7.6/40% |

**Market Indexes (R6):** Wall Street=90, Europa=99, Dragon=100

**Coefficients (R6):** Columbia: sanctions=1.000, tariffs=0.981 | Cathay: sanctions=1.000, tariffs=0.965 | Sarmatia: sanctions=0.964, tariffs=1.000 | Persia: sanctions=0.950, tariffs=1.000 | Teutonia: sanctions=1.000, tariffs=0.979

**Revolutions:** persia: major

### AI Judgment (Pass 2)

**R1:** 6 adjustments (confidence 80%)
  Flags: caribe_hyperinflation
  _caribe crisis clear, war stress adjustments, market anxiety_
  -   JUDGMENT: caribe → CRISIS (GDP -1.5%): hyperinflation 60%, massive debt 501%, economic collapse
  -   JUDGMENT: persia stability 4.0→3.7: war stress, sanctions bite, inflation 50%
  -   JUDGMENT: ruthenia stability 4.8→5.0: rally around flag defending homeland
  -   JUDGMENT: columbia support 36%→34%: war fatigue, inflation concerns
  -   JUDGMENT: hanguk support 35%→32%: economic anxiety, regional tensions
  -   JUDGMENT: dragon index 97→92: cathay tariff concerns, regional instability

**R2:** 6 adjustments (confidence 80%)
  Flags: caribe_hyperinflation
  _caribe crisis deepens, war effects emerging, regional anxiety_
  -   JUDGMENT: caribe → CRISIS (GDP -1.5%): hyperinflation 60%, low stability, debt spiral
  -   JUDGMENT: persia stability 3.6→3.3: war pressure, sanctions bite, inflation surge
  -   JUDGMENT: columbia stability 7.0→7.2: rally effect from war mobilization
  -   JUDGMENT: hanguk support 32%→29%: economic anxiety, regional tensions
  -   JUDGMENT: persia support 36%→34%: war costs, inflation pain
  -   JUDGMENT: dragon index 93→88: formosa tension, cathay slowdown fears

**R3:** 6 adjustments (confidence 80%)
  Flags: caribe_crisis, war_fatigue
  _Crisis emerging in Caribe. War fatigue building in Columbia/Persia._
  -   JUDGMENT: caribe → CRISIS (GDP -1.5%): hyperinflation 60%, low stability, debt spiral
  -   JUDGMENT: persia stability 3.2→2.9: war stress, sanctions bite, inflation 50%
  -   JUDGMENT: caribe stability 2.9→2.5: hyperinflation social unrest, economic collapse
  -   JUDGMENT: columbia support 32%→29%: war costs rising, inflation up
  -   JUDGMENT: persia support 32%→28%: war casualties, economic hardship mounting
  -   JUDGMENT: wall_street index 90→85: war uncertainty, inflation concerns

**R4:** 6 adjustments (confidence 80%)
  Flags: caribe_collapse_watch
  _Crisis deepening in weak economies, war fatigue emerging in democracies_
  -   JUDGMENT: caribe → CRISIS (GDP -1.5%): hyperinflation collapse, low stability, massive debt
  -   JUDGMENT: persia → CRISIS (GDP -1.0%): war economy strain, sanctions bite, high inflation
  -   JUDGMENT: columbia stability 7.2→6.9: war fatigue, low support eroding confidence
  -   JUDGMENT: phrygia stability 5.2→5.0: inflation pressure building social tension
  -   JUDGMENT: hanguk support 30%→27%: economic stagnation, regional war anxiety
  -   JUDGMENT: teutonia support 42%→40%: negative growth hurting incumbent approval

**R5:** 7 adjustments (confidence 85%)
  Flags: persia_crisis, caribe_collapse
  _Two clear crises: Persia war-driven, Caribe hyperinflation. Limited contagion due to isolation._
  -   JUDGMENT: persia → CRISIS (GDP -1.5%): War, sanctions, 50% inflation, stability 2.5, support 20%
  -   JUDGMENT: caribe → CRISIS (GDP -1.0%): 60% inflation, 505% debt, stability 2.4, economic collapse
  -   JUDGMENT: persia stability 2.5→2.2: War fatigue, economic crisis deepening, regime stress
  -   JUDGMENT: columbia stability 6.8→6.6: War costs mounting, low support, midterm pressure
  -   JUDGMENT: persia support 20%→17%: Crisis worsening, war casualties, inflation crushing population
  -   JUDGMENT: caribe support 34%→30%: Hyperinflation destroying livelihoods, economic system failing
  -   JUDGMENT: wall_street index 88→85: War uncertainty, oil volatility concerns

**R6:** 6 adjustments (confidence 85%)
  Flags: persia_regime_stress, caribe_collapse
  _Crisis states emerging, war fatigue building, hyperinflation accelerating collapses_
  -   JUDGMENT: caribe → CRISIS (GDP -1.5%): hyperinflation collapse, stability critical
  -   JUDGMENT: persia → CRISIS (GDP -1.0%): war sanctions hyperinflation triple shock
  -   JUDGMENT: persia stability 2.0→1.7: war exhaustion mounting pressure
  -   JUDGMENT: caribe stability 2.3→2.1: economic collapse accelerating
  -   JUDGMENT: columbia support 32%→30%: war costs rising midterm fatigue
  -   JUDGMENT: persia support 13%→10%: hyperinflation war desperation


---
## S4: Thucydides Trap (Rising Power vs Incumbent)

_Cathay builds naval, Columbia responds with tariffs + tech race. Formosa crisis R4. Tests power transition dynamics._

### GDP Trajectories

| Round | Oil$ | Columb | Cathay | Sarmat | Ruthen | Persia | Teuton | Bharat | Formos |
|-------|------|------|------|------|------|------|------|------|------|
| R0 | $80 | 280 (+1.8%) | 190 (+4.0%) | 20 (+1.0%) | 2 (+2.5%) | 5 (+0.5%) | 45 (+1.2%) | 42 (+6.5%) | 8 (+3.0%) |
| R1 | $86 | 281 (+0.4%) | 190 (+0.1%) | 20 (+0.6%) | 2 (+1.1%) | 5 (+0.3%) | 45 (+0.6%) | 43 (+3.4%) | 8 (+1.5%) |
| R2 | $98 | 281 (-0.2%) | 190 (-0.1%) | 20 (+0.7%) | 2 (+1.1%) | 5 (+0.5%) | 45 (+0.3%) | 45 (+3.1%) | 8 (+1.3%) |
| R3 | $85 | 278 (-0.9%) | 188 (-1.1%) | 20 (+0.6%) | 2 (+1.3%) | 5 (+0.4%) | 46 (+0.5%) | 46 (+3.4%) | 8 (+1.6%) |
| R4 | $81 | 258 (-6.2%) | 188 (+0.2%) | 20 (+0.3%) | 2 (+1.1%) | 5 (+0.4%) | 45 (-1.8%) | 47 (+1.7%) | 8 (+1.6%) |
| R5 | $50 | 223 (-12.3%) | 185 (-1.7%) | 20 (-0.1%) | 2 (+1.5%) | 5 (+0.3%) | 44 (-2.7%) | 48 (+1.7%) | 9 (+2.2%) |
| R6 | $36 | 192 (-12.8%) | 186 (+0.3%) | 20 (-0.4%) | 2 (+1.7%) | 5 (+0.1%) | 42 (-3.2%) | 48 (+1.2%) | 9 (+2.5%) |

### Stability & Support

| Round | Columb S/Sup | Cathay S/Sup | Sarmat S/Sup | Ruthen S/Sup | Persia S/Sup | Teuton S/Sup |
|-------|----------|----------|----------|----------|----------|----------|
| R0 | 7.0/38% | 8.0/58% | 5.0/55% | 5.0/52% | 4.0/40% | 7.0/45% |
| R1 | 7.0/35% | 8.1/59% | 4.9/54% | 5.0/48% | 3.6/38% | 7.1/45% |
| R2 | 7.0/32% | 8.2/61% | 4.8/53% | 4.8/43% | 3.3/36% | 7.2/44% |
| R3 | 7.2/31% | 8.3/62% | 4.6/51% | 4.7/38% | 2.9/32% | 7.3/44% |
| R4 | 6.8/19% | 8.4/63% | 4.5/50% | 4.5/35% | 2.6/30% | 7.3/40% |
| R5 | 5.7/5% | 8.5/65% | 4.3/49% | 4.3/31% | 2.3/28% | 7.2/35% |
| R6 | 4.6/5% | 8.6/66% | 4.2/47% | 4.1/28% | 2.0/26% | 7.0/30% |

**Market Indexes (R6):** Wall Street=41, Europa=87, Dragon=87

**Coefficients (R6):** Columbia: sanctions=1.000, tariffs=0.958 | Cathay: sanctions=0.980, tariffs=0.953 | Sarmatia: sanctions=0.970, tariffs=1.000 | Persia: sanctions=0.969, tariffs=1.000

### AI Judgment (Pass 2)

**R1:** 6 adjustments (confidence 80%)
  Flags: caribe_hyperinflation
  _caribe crisis clear, war stress adjustments, regional anxiety_
  -   JUDGMENT: caribe → CRISIS (GDP -1.5%): hyperinflation 60%, massive debt, economic collapse
  -   JUDGMENT: persia stability 4.0→3.7: war stress, sanctions bite, inflation surge
  -   JUDGMENT: ruthenia stability 4.8→5.0: rally around flag defending homeland
  -   JUDGMENT: columbia support 37%→35%: war fatigue, inflation concerns
  -   JUDGMENT: hanguk support 35%→32%: economic anxiety, regional tensions
  -   JUDGMENT: dragon index 99→94: formosa tensions, cathay trade concerns

**R2:** 6 adjustments (confidence 80%)
  Flags: caribe_hyperinflation, persia_stress
  _caribe crisis deepens, war fatigue emerging, regional anxiety_
  -   JUDGMENT: caribe → CRISIS (GDP -1.5%): hyperinflation 60%, low stability, debt spiral
  -   JUDGMENT: persia stability 3.6→3.3: war stress, sanctions bite, inflation 50%
  -   JUDGMENT: phrygia stability 5.1→4.9: inflation 45% eroding public confidence
  -   JUDGMENT: columbia support 34%→32%: war costs rising, inflation concerns
  -   JUDGMENT: hanguk support 32%→29%: economic anxiety, regional tensions
  -   JUDGMENT: dragon index 95→90: formosa tensions, cathay trade war

**R3:** 6 adjustments (confidence 80%)
  Flags: caribe_hyperinflation, persia_pressure
  _Caribe entering crisis from hyperinflation. War states showing strain. Markets cautious._
  -   JUDGMENT: caribe → CRISIS (GDP -1.5%): hyperinflation 60%, low stability, debt spiral
  -   JUDGMENT: persia stability 3.2→2.9: war pressure, sanctions bite, inflation surge
  -   JUDGMENT: columbia stability 7.0→7.2: rally effect from active war leadership
  -   JUDGMENT: caribe support 39%→36%: hyperinflation destroying living standards
  -   JUDGMENT: persia support 34%→32%: war costs plus economic pain
  -   JUDGMENT: wall_street index 92→87: war uncertainty dampening sentiment

**R4:** 7 adjustments (confidence 85%)
  Flags: columbia_crisis, caribe_collapse
  _Crisis deepening in Columbia/Caribe, contagion limited, war fatigue mounting_
  -   JUDGMENT: caribe → CRISIS (GDP -1.5%): 60% inflation, 504% debt, stability 2.9
  -   JUDGMENT: columbia → CRISIS (GDP -1.0%): 6.2% GDP decline, war costs, support 22%
  -   JUDGMENT: contagion columbia→freeland (trade): GDP -0.5%
  -   JUDGMENT: persia stability 2.9→2.6: War pressure, sanctions, 50% inflation stress
  -   JUDGMENT: columbia support 22%→19%: War fatigue, economic decline accelerating
  -   JUDGMENT: caribe support 34%→30%: Hyperinflation destroying living standards
  -   JUDGMENT: wall_street index 78→73: Columbia crisis contagion fears

**R5:** 9 adjustments (confidence 85%)
  Flags: columbia_political_crisis, contagion_active
  _Major power crisis creating regional contagion effects_
  -   JUDGMENT: columbia → CRISIS (GDP -1.5%): Sustained GDP decline, political collapse imminent
  -   JUDGMENT: yamato → CRISIS (GDP -1.0%): Debt spiral accelerating with GDP contraction
  -   JUDGMENT: contagion columbia→freeland (trade): GDP -0.8%
  -   JUDGMENT: contagion yamato→hanguk (supply_chain): GDP -0.5%
  -   JUDGMENT: columbia stability 6.0→5.7: Political system stress from economic catastrophe
  -   JUDGMENT: persia stability 2.5→2.3: War pressure plus hyperinflation eroding regime
  -   JUDGMENT: columbia support 5%→5%: Economic disaster blamed on leadership
  -   JUDGMENT: caribe support 28%→26%: Hyperinflation destroying living standards
  -   JUDGMENT: wall_street index 62→54: Columbia crisis panic spreading to markets

**R6:** 9 adjustments (confidence 85%)
  Flags: columbia_collapse_risk, contagion_active
  _Major power crisis spreading, political systems under extreme stress_
  -   JUDGMENT: columbia → CRISIS (GDP -1.5%): Sustained GDP decline, political collapse, war costs
  -   JUDGMENT: yamato → CRISIS (GDP -1.0%): Fourth consecutive GDP decline, debt spiral
  -   JUDGMENT: contagion columbia→freeland (trade_dependency): GDP -0.8%
  -   JUDGMENT: contagion yamato→hanguk (supply_chain): GDP -0.5%
  -   JUDGMENT: columbia stability 4.9→4.6: Political system breakdown, war fatigue
  -   JUDGMENT: persia stability 2.2→2.0: War pressure, economic strain
  -   JUDGMENT: columbia support 5%→5%: Economic catastrophe, war casualties
  -   JUDGMENT: hanguk support 18%→15%: Economic decline, regional instability
  -   JUDGMENT: wall_street index 49→41: Columbia crisis panic, recession fears


---
## S5: Military Escalation + Nuclear Crisis

_Sarmatia launches offensive R2. Persia approaches nuclear breakout. Cathay naval buildup. Tests escalation spiral._

### GDP Trajectories

| Round | Oil$ | Columb | Cathay | Sarmat | Ruthen | Persia | Teuton | Bharat | Formos |
|-------|------|------|------|------|------|------|------|------|------|
| R0 | $80 | 280 (+1.8%) | 190 (+4.0%) | 20 (+1.0%) | 2 (+2.5%) | 5 (+0.5%) | 45 (+1.2%) | 42 (+6.5%) | 8 (+3.0%) |
| R1 | $86 | 283 (+1.1%) | 194 (+2.1%) | 20 (+0.6%) | 2 (+1.1%) | 5 (+0.3%) | 45 (+0.6%) | 43 (+3.4%) | 8 (+1.5%) |
| R2 | $98 | 286 (+1.1%) | 197 (+1.6%) | 20 (+0.8%) | 2 (+1.1%) | 5 (+0.5%) | 45 (+0.3%) | 45 (+3.1%) | 8 (+1.3%) |
| R3 | $86 | 289 (+1.1%) | 201 (+2.1%) | 20 (-3.7%) | 2 (+1.3%) | 5 (+0.3%) | 46 (+0.6%) | 46 (+3.4%) | 8 (+1.5%) |
| R4 | $82 | 292 (+1.0%) | 206 (+2.3%) | 20 (+0.5%) | 2 (+1.3%) | 5 (+0.3%) | 46 (+0.6%) | 48 (+3.5%) | 8 (+1.6%) |
| R5 | $82 | 295 (+1.0%) | 211 (+2.3%) | 20 (+0.6%) | 2 (+1.4%) | 5 (+0.3%) | 46 (+0.6%) | 50 (+3.5%) | 9 (+1.6%) |
| R6 | $82 | 298 (+1.0%) | 215 (+2.3%) | 20 (+0.6%) | 2 (+1.4%) | 5 (+0.3%) | 46 (+0.6%) | 51 (+3.5%) | 9 (+1.6%) |

### Stability & Support

| Round | Columb S/Sup | Cathay S/Sup | Sarmat S/Sup | Ruthen S/Sup | Persia S/Sup | Teuton S/Sup |
|-------|----------|----------|----------|----------|----------|----------|
| R0 | 7.0/38% | 8.0/58% | 5.0/55% | 5.0/52% | 4.0/40% | 7.0/45% |
| R1 | 7.0/35% | 8.1/59% | 4.9/54% | 4.8/48% | 3.6/38% | 7.1/45% |
| R2 | 7.0/34% | 8.2/61% | 4.8/53% | 4.7/43% | 3.3/36% | 7.2/44% |
| R3 | 7.0/32% | 8.3/62% | 4.2/51% | 4.5/38% | 2.9/31% | 7.3/44% |
| R4 | 6.9/29% | 8.4/63% | 4.0/47% | 4.3/34% | 2.6/29% | 7.4/44% |
| R5 | 6.6/30% | 8.6/65% | 3.7/45% | 4.1/31% | 2.2/19% | 7.5/44% |
| R6 | 6.5/27% | 8.7/66% | 3.6/41% | 4.1/27% | 1.7/15% | 7.6/44% |

**Market Indexes (R6):** Wall Street=85, Europa=98, Dragon=98

**Coefficients (R6):** Sarmatia: sanctions=0.923, tariffs=1.000 | Persia: sanctions=0.950, tariffs=1.000

**Revolutions:** persia: major

### AI Judgment (Pass 2)

**R1:** 6 adjustments (confidence 80%)
  Flags: caribe_hyperinflation
  _caribe crisis from hyperinflation, war states show stress, markets cautious_
  -   JUDGMENT: caribe → CRISIS (GDP -1.5%): hyperinflation 60%, massive debt 501%, economic collapse
  -   JUDGMENT: persia stability 4.0→3.7: war stress, sanctions bite, inflation 50%
  -   JUDGMENT: phrygia stability 5.0→4.8: inflation 45% eroding public confidence
  -   JUDGMENT: columbia support 37%→35%: war costs rising, inflation up
  -   JUDGMENT: hanguk support 35%→33%: economic stagnation, low growth concerns
  -   JUDGMENT: dragon index 99→96: regional tension, formosa dependency fears

**R2:** 6 adjustments (confidence 80%)
  Flags: caribe_hyperinflation
  _Crisis limited to Caribe hyperinflation. War fatigue emerging in Columbia. Modest adjustments._
  -   JUDGMENT: caribe → CRISIS (GDP -1.5%): hyperinflation 60%, low stability, debt spiral
  -   JUDGMENT: persia stability 3.6→3.3: war stress, sanctions bite, inflation surge
  -   JUDGMENT: phrygia stability 4.9→4.7: high inflation eroding public confidence
  -   JUDGMENT: columbia support 36%→34%: war costs rising, inflation up
  -   JUDGMENT: hanguk support 33%→31%: economic stagnation, low confidence
  -   JUDGMENT: wall_street index 95→92: war uncertainty, oil price pressure

**R3:** 6 adjustments (confidence 80%)
  Flags: caribe_hyperinflation
  _Crisis emerging in Caribe. War fatigue building in Columbia/Persia._
  -   JUDGMENT: caribe → CRISIS (GDP -1.5%): hyperinflation 60%, low stability, debt spiral
  -   JUDGMENT: persia stability 3.2→2.9: war stress, sanctions bite, inflation 50%
  -   JUDGMENT: sarmatia stability 4.4→4.2: GDP decline -3.7%, sanctions pressure mounting
  -   JUDGMENT: columbia support 34%→32%: war costs rising, inflation up
  -   JUDGMENT: persia support 34%→31%: economic hardship from war, sanctions
  -   JUDGMENT: europa index 99→96: energy concerns, sanctions uncertainty

**R4:** 7 adjustments (confidence 85%)
  Flags: war_fatigue, hyperinflation_crisis
  _Crisis states emerging, war fatigue building, hyperinflation destabilizing Caribe_
  -   JUDGMENT: caribe → CRISIS (GDP -1.5%): hyperinflation 60%, low stability, debt spiral
  -   JUDGMENT: persia → CRISIS (GDP -1.0%): war economy, 50% inflation, sanctions bite
  -   JUDGMENT: persia stability 2.9→2.6: war fatigue, economic pressure mounting
  -   JUDGMENT: caribe stability 2.9→2.6: hyperinflation eroding regime legitimacy
  -   JUDGMENT: columbia support 31%→29%: war costs rising, midterm election pressure
  -   JUDGMENT: sarmatia support 50%→47%: sanctions impact, war stalemate fatigue
  -   JUDGMENT: wall_street index 92→87: war uncertainty, oil volatility concerns

**R5:** 8 adjustments (confidence 85%)
  Flags: crisis_deepening, war_fatigue
  _Crisis states emerging, war fatigue building, contagion limited_
  -   JUDGMENT: caribe → CRISIS (GDP -1.5%): hyperinflation, low stability, debt spiral
  -   JUDGMENT: persia → CRISIS (GDP -1.0%): war sanctions inflation triple hit
  -   JUDGMENT: contagion persia→phrygia (regional_instability): GDP -0.5%
  -   JUDGMENT: columbia stability 6.9→6.6: war fatigue mounting low support
  -   JUDGMENT: sarmatia stability 3.9→3.7: sanctions bite war costs
  -   JUDGMENT: persia support 22%→19%: war losses economic collapse
  -   JUDGMENT: caribe support 35%→31%: hyperinflation destroying living standards
  -   JUDGMENT: wall_street index 88→83: war uncertainty oil volatility

**R6:** 6 adjustments (confidence 85%)
  Flags: persia_instability, caribe_collapse
  _Crisis states emerging, war fatigue setting in, no major contagion yet_
  -   JUDGMENT: caribe → CRISIS (GDP -1.5%): hyperinflation 60%, stability 2.5, treasury depleted
  -   JUDGMENT: persia → CRISIS (GDP -1.0%): war stress, 50% inflation, stability 2.0
  -   JUDGMENT: persia stability 2.0→1.7: war fatigue, economic collapse accelerating
  -   JUDGMENT: ruthenia stability 3.9→4.1: defensive war rally effect
  -   JUDGMENT: columbia support 30%→27%: war costs rising, midterm election pressure
  -   JUDGMENT: sarmatia support 43%→41%: sanctions bite, war stalemate


---
## Cross-Scenario Analysis

### Final GDP Comparison (R6)

| Country | S1 | S2 | S3 | S4 | S5 |
|---------|------|------|------|------|------|
| Columbia | 298 | 300 | 291 | 192 | 298 |
| Cathay | 215 | 203 | 207 | 186 | 215 |
| Sarmatia | 21 | 21 | 21 | 20 | 20 |
| Ruthenia | 2 | 2 | 2 | 2 | 2 |
| Persia | 5 | 5 | 5 | 5 | 5 |

### Convergence Criteria

| Criterion | Target | S1 | S2 | S3 | S4 | S5 |
|-----------|--------|------|------|------|------|------|
| No country GDP < 50% of start by R4 |  | PASS | PASS | PASS | PASS | PASS |
| Columbia GDP > 200 at R6 |  | PASS | PASS | PASS | FAIL | PASS |
| Cathay GDP > 150 at R6 |  | PASS | PASS | PASS | PASS | PASS |
| No stability < 2.0 (baseline) |  | FAIL | FAIL | FAIL | FAIL | FAIL |
| Oil $30-$200 range |  | PASS | PASS | PASS | PASS | PASS |
| Sarmatia GDP declining under sanctions |  | FAIL | FAIL | FAIL | FAIL | PASS |