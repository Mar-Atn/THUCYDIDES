# TTT Scenario Test Results
**Date:** 2026-04-03 14:01
**Engine:** economic.py + political.py + AI Judgment (Pass 2)
**Data:** countries.csv (D1-D18 calibration applied)
**Scenarios:** 1 × 6 rounds

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
| R4 | $81 | 257 (-6.2%) | 188 (+0.2%) | 20 (+0.3%) | 2 (+1.1%) | 5 (+0.4%) | 45 (-1.8%) | 47 (+1.7%) | 8 (+1.6%) |
| R5 | $50 | 225 (-12.3%) | 185 (-1.6%) | 20 (-0.1%) | 2 (+1.5%) | 5 (+0.3%) | 44 (-2.7%) | 48 (+1.7%) | 9 (+2.2%) |
| R6 | $36 | 194 (-12.7%) | 186 (+0.2%) | 20 (-0.4%) | 2 (+1.7%) | 5 (+0.0%) | 42 (-3.2%) | 48 (+1.2%) | 9 (+2.5%) |

### Stability & Support

| Round | Columb S/Sup | Cathay S/Sup | Sarmat S/Sup | Ruthen S/Sup | Persia S/Sup | Teuton S/Sup |
|-------|----------|----------|----------|----------|----------|----------|
| R0 | 7.0/38% | 8.0/58% | 5.0/55% | 5.0/52% | 4.0/40% | 7.0/45% |
| R1 | 7.0/37% | 8.1/59% | 4.9/54% | 4.8/48% | 4.0/38% | 7.1/45% |
| R2 | 7.0/34% | 8.2/61% | 4.8/53% | 4.7/43% | 3.6/36% | 7.2/44% |
| R3 | 7.0/30% | 8.3/62% | 4.6/51% | 4.5/38% | 3.2/35% | 7.3/44% |
| R4 | 6.5/18% | 8.4/63% | 4.5/50% | 4.3/34% | 2.9/33% | 7.3/40% |
| R5 | 5.8/5% | 8.5/65% | 4.3/49% | 4.1/31% | 2.8/31% | 7.2/35% |
| R6 | 4.7/5% | 8.6/66% | 4.2/47% | 3.9/27% | 2.5/28% | 7.0/30% |

**Market Indexes (R6):** Wall Street=50, Europa=87, Dragon=88

**Coefficients (R6):** Columbia: sanctions=1.000, tariffs=0.959 | Cathay: sanctions=0.979, tariffs=0.952 | Sarmatia: sanctions=0.970, tariffs=1.000 | Persia: sanctions=0.968, tariffs=1.000

### AI Judgment (Pass 2)

**R1:** 0 adjustments (confidence 50%)
  Flags: PARSE_ERROR: judgment response could not be parsed
  _Parse error: Expecting value: line 13 column 38 (char 747)_

**R2:** 6 adjustments (confidence 80%)
  Flags: high_inflation_cluster, war_fatigue_emerging
  _Round 2 shows emerging stress patterns: Caribe entering hyperinflation crisis, war fatigue beginning to affect Columbia and regional allies, while Persia/Phrygia face inflation-driven instability. Most adjustments are modest as Pass 1 formulas capture the primary effects well._
  -   JUDGMENT: caribe → CRISIS (GDP -1.5%): 60% inflation with 502% debt/GDP ratio and declining stability creates economic crisis conditions
  -   JUDGMENT: persia stability 3.9→3.6: War pressure and 50% inflation eroding regime confidence beyond formula capture
  -   JUDGMENT: phrygia stability 5.1→4.9: 45% inflation creating social unrest not fully captured in base calculations
  -   JUDGMENT: columbia support 36%→34%: War fatigue from Persian conflict affecting approval beyond economic factors
  -   JUDGMENT: hanguk support 35%→33%: Regional security concerns from multiple conflicts dampening public confidence
  -   JUDGMENT: dragon index 98→93: Regional instability from multiple conflicts creating investor nervousness in Asian markets

**R3:** 6 adjustments (confidence 80%)
  Flags: caribe_economic_collapse, inflation_pressure_persia_phrygia
  _Focused on hyperinflation impacts in Caribe/Persia/Phrygia and war fatigue effects. Caribe crisis formalized due to sustained collapse indicators. Most countries stable, minimal intervention needed._
  -   JUDGMENT: caribe → CRISIS (GDP -1.5%): 60% inflation, 503% debt/GDP, treasury near depletion - sustained economic collapse
  -   JUDGMENT: persia stability 3.5→3.2: 50% inflation eroding public confidence beyond formula capture, war stress compounding
  -   JUDGMENT: phrygia stability 5.0→4.8: 45% inflation creating social unrest, economic hardship beyond base calculations
  -   JUDGMENT: columbia support 33%→30%: War fatigue from prolonged Persia conflict, economic headwinds affecting public mood
  -   JUDGMENT: hanguk support 33%→31%: Economic stagnation and regional tensions creating political dissatisfaction
  -   JUDGMENT: wall_street index 92→89: Ongoing war costs and inflation concerns weighing on investor sentiment

**R4:** 7 adjustments (confidence 80%)
  Flags: columbia_crisis_watch, formosa_contagion_risk
  _Columbia showing clear crisis indicators with sustained GDP decline and critical support levels. Contagion effects limited to closest trade partners. Other stressed economies not yet at crisis threshold but warrant monitoring._
  -   JUDGMENT: columbia → CRISIS (GDP -1.5%): Three rounds of GDP decline (-6.2% this round), support at critical 21%, war costs mounting, approaching crisis threshold
  -   JUDGMENT: contagion columbia→formosa (supply_chain_dependency): GDP -0.8%
  -   JUDGMENT: contagion columbia→freeland (trade_integration): GDP -0.5%
  -   JUDGMENT: persia stability 3.2→2.9: War with Columbia and Levantia creating additional domestic pressure beyond formula capture, 50% inflation compounding stress
  -   JUDGMENT: columbia support 21%→18%: War fatigue from Persia conflict, economic decline narrative creating additional support erosion beyond formula
  -   JUDGMENT: caribe support 37%→35%: 60% inflation creating severe public hardship, low stability amplifying dissatisfaction beyond economic formula
  -   JUDGMENT: wall_street index 80→75: Columbia crisis fears creating broader market sentiment deterioration beyond fundamentals

**R5:** 0 adjustments (confidence 50%)
  Flags: PARSE_ERROR: judgment response could not be parsed
  _Parse error: Expecting value: line 13 column 36 (char 1093)_

**R6:** 9 adjustments (confidence 80%)
  Flags: columbia_crisis_deepening, yamato_debt_spiral, regional_contagion_asia
  _Round 6 shows crisis deepening in Columbia and Yamato with contagion spreading to regional partners. Oil price decline to $35.5 provides some relief but insufficient to offset structural problems. Columbia's 5% support with -12.7% GDP decline represents potential system failure. Regional contagion particularly affecting Asia-Pacific economies through trade and financial linkages._
  -   JUDGMENT: columbia → CRISIS (GDP -1.5%): GDP declined 12.7% this round, support at catastrophic 5%, war costs mounting - deep crisis confirmed
  -   JUDGMENT: yamato → CRISIS (GDP -1.2%): GDP declined 4.6% this round following previous declines, 250% debt/GDP ratio unsustainable, crisis deepening
  -   JUDGMENT: contagion columbia→hanguk (trade_dependency): GDP -0.8%
  -   JUDGMENT: contagion yamato→hanguk (regional_financial): GDP -0.5%
  -   JUDGMENT: columbia stability 5.0→4.7: War fatigue beyond formula capture as casualties mount and economic crisis deepens public resolve
  -   JUDGMENT: persia stability 2.7→2.5: War pressure and 50% inflation creating social unrest beyond economic formula capture
  -   JUDGMENT: columbia support 5%→5%: Economic collapse narrative dominating media, war costs visible to public, support eroding faster than formula captures
  -   JUDGMENT: hanguk support 19%→17%: Economic contagion from major partners creating public anxiety about government competence
  -   JUDGMENT: wall_street index 55→50: Columbian crisis deepening, contagion fears to regional partners creating additional market pessimism


---
## Cross-Scenario Analysis

### Final GDP Comparison (R6)

| Country | S4 |
|---------|------|
| Columbia | 194 |
| Cathay | 186 |
| Sarmatia | 20 |
| Ruthenia | 2 |
| Persia | 5 |

### Convergence Criteria

| Criterion | Target | S4 |
|-----------|--------|------|
| No country GDP < 50% of start by R4 |  | PASS |
| Columbia GDP > 200 at R6 |  | FAIL |
| Cathay GDP > 150 at R6 |  | PASS |
| No stability < 2.0 (baseline) |  | PASS |
| Oil $30-$200 range |  | PASS |
| Sarmatia GDP declining under sanctions |  | FAIL |