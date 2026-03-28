# TTT World Model -- Test Scenarios for Dependency Validation
## Version 1.0

**Purpose:** 10 focused test scenarios to validate all 25 dependencies defined in `SEED_D_DEPENDENCIES_v1.md`. Each scenario specifies deterministic inputs (no AI decisions), expected outcome corridors, and pass/fail criteria.

**Engine:** `world_model_engine.py` v2 (three-pass architecture)
**Data baseline:** `countries.csv` starting values (with overrides from `world_state.py`)

**Starting values reference (key countries):**

| Country | GDP | Growth | Tax | Treasury | Inflation | Stability | Naval | Ground | Regime | Oil? | Formosa Dep | Debt |
|---------|-----|--------|-----|----------|-----------|-----------|-------|--------|--------|------|-------------|------|
| Columbia | 280 | 1.8% | 0.24 | 50 | 3.5% | 7.0 | 11 | 22 | democracy | yes | 0.65 | 5.0 |
| Cathay | 190 | 4.0% | 0.20 | 45 | 0.5% | 8.0 | 7 | 25 | autocracy | no | 0.25 | 2.0 |
| Nordostan | 20 | 1.0% | 0.20 | 6 | 5.0% | 5.0 | 2 | 18 | autocracy | yes | 0.15 | 0.5 |
| Heartland | 2.2 | 2.5% | 0.25 | 1 | 7.5% | 5.0 | 0 | 10 | democracy | no | 0.10 | 0.3 |
| Persia | 5.0 | -3.0% | 0.18 | 1 | 50.0% | 4.0 | 0 | 8 | hybrid | yes | 0.15 | 0.0 |
| Ponte | 22 | 0.8% | 0.40 | 4 | 2.5% | 6.0 | 0 | 4 | democracy | no | 0.30 | 8.0 |
| Teutonia | 45 | 1.2% | 0.38 | 12 | 2.5% | 7.0 | 0 | 6 | democracy | no | 0.45 | 2.0 |
| Formosa | 8 | 3.0% | 0.20 | 8 | 2.0% | 7.0 | 0 | 4 | democracy | no | 0.00 | 1.0 |
| Yamato | 43 | 1.0% | 0.30 | 15 | 2.5% | 8.0 | 2 | 3 | democracy | no | 0.55 | 6.0 |
| Hanguk | 18 | 2.2% | 0.26 | 8 | 2.5% | 6.0 | 0 | 5 | democracy | no | 0.40 | 2.0 |

**Note on overrides applied by `world_state.py`:**
- Columbia: naval 10->11, resource sector 5->8, AI progress 0.60->0.80
- Cathay: naval 6->7, AI level 2->3, AI progress 0.70->0.10

---

## Scenario 1: OIL SHOCK

### Dependencies Tested
D1 (Oil Price Shock -> GDP Contraction), D6 (Oil Producer Windfall), D8 (OPEC Prisoner's Dilemma)

### Setup (Prescribed Actions)

**Active wars:** Nordostan-Heartland (pre-existing), Columbia-Persia (starting R0).
**Gulf Gate:** Blocked from R1 onward (Persia ground blockade, already initialized from deployments).
**OPEC:** All members (Nordostan, Persia, Solaria, Mirage) set to "low" production R1-R4. Solaria defects to "high" R5. All "high" R6-R8.
**No other actions.** No sanctions, no tariffs, no tech investment, no military production orders.

**Round-by-round actions:**
- R1: `blockade_changes: {gulf_gate_ground: {controller: persia}}` (confirm active), `opec_production: {nordostan: low, persia: low, solaria: low, mirage: low}`
- R2: Same OPEC as R1. No changes.
- R3: Same OPEC as R1. No changes.
- R4: Same OPEC as R1. No changes.
- R5: `opec_production: {nordostan: low, persia: low, solaria: high, mirage: low}`
- R6: `opec_production: {nordostan: high, persia: high, solaria: high, mirage: high}`
- R7: Same as R6.
- R8: Same as R6.

### Expected Outcome Ranges (the corridor)

**Oil price formula inputs R1:** base=80, supply=1.0-4*0.06=0.76, disruption=1.0+0.50(gulf_gate)=1.50, war_premium=2*0.05=0.10. Raw = 80*(1.0/0.76)*1.50*1.10 = 80*1.316*1.50*1.10 = ~174. Demand adjustments may shift +/-5%.

| Variable | R1 | R2 | R3 | R4 | R5 | R6 | R7 | R8 |
|----------|----|----|----|----|----|----|----|----|
| Oil price ($) | 160-185 | 155-190 | 150-195 | 145-200 | 140-175 | 95-125 | 85-115 | 80-110 |
| Columbia GDP | 272-278 | 266-276 | 260-274 | 254-272 | 250-270 | 252-272 | 254-274 | 256-276 |
| Cathay GDP | 190-198 | 190-198 | 188-198 | 186-198 | 186-198 | 190-200 | 194-206 | 198-210 |
| Nordostan GDP | 20-22 | 20-23 | 20-24 | 20-25 | 20-24 | 19-22 | 18-21 | 18-21 |
| Nordostan oil_revenue | 0.8-1.4 | 0.8-1.5 | 0.8-1.5 | 0.8-1.5 | 0.7-1.3 | 0.4-0.8 | 0.3-0.7 | 0.3-0.7 |
| Teutonia GDP | 43-45 | 42-45 | 41-45 | 40-44 | 40-44 | 41-45 | 42-46 | 43-47 |
| Columbia economic_state | NORMAL | NORMAL | NORMAL-STRESSED | NORMAL-STRESSED | NORMAL-STRESSED | NORMAL-STRESSED | NORMAL | NORMAL |
| Solaria GDP (oil prod) | 11-12 | 11-13 | 11-14 | 11-14 | 11-13 | 10.5-12 | 10.5-12 | 10.5-12 |

### Pass/Fail Criteria
- **PASS** if:
  - Oil spikes above $140 in R1 with Gulf Gate blocked + OPEC restriction
  - Oil drops by $30+ between R5 and R7 after OPEC defection to "high"
  - Oil importers (Columbia, Cathay, Teutonia) show negative oil_shock contribution to GDP
  - Oil producers (Nordostan, Solaria) show positive oil_revenue in R1-R4
  - Nordostan GDP does NOT decline despite being at war (oil windfall offsets -- D6 paradox)
  - All variables within corridor
- **CALIBRATE** if 1-2 variables out of range by <20%
- **FAIL** if:
  - Oil stays below $120 with Gulf Gate blocked (disruption not applied)
  - Oil producers show zero oil_revenue (revenue formula broken)
  - Importers show GDP growth during oil shock (oil_shock term missing)
  - OPEC production changes have zero effect on price (supply variable not connected)

---

## Scenario 2: SANCTIONS SPIRAL

### Dependencies Tested
D2 (Sanctions -> GDP Erosion), D3 (Money Printing -> Inflation), D4 (Debt Accumulation), D18 (Autocratic Resilience)

### Setup (Prescribed Actions)

**Active wars:** Nordostan-Heartland (pre-existing).
**Gulf Gate:** Open (Persia ceasefire assumed, or not relevant -- disable gulf_gate blockade).
**Sanctions:** Columbia, Gallia, Teutonia, Albion, Freeland all impose L3 sanctions on Nordostan starting R1. Maintained R1-R8.
**No other actions.** OPEC normal. No tariffs. No military production.

**Round-by-round actions:**
- R1: `sanction_changes: {columbia: {nordostan: 3}, gallia: {nordostan: 3}, teutonia: {nordostan: 3}, albion: {nordostan: 3}, freeland: {nordostan: 3}}`
- R2-R8: No changes (sanctions persist).

### Expected Outcome Ranges (the corridor)

**Coalition coverage calculation:** Trade weights of columbia+gallia+teutonia+albion+freeland with nordostan need to exceed 0.60 for full effectiveness. Given the GDP sizes and sector complementarity, this coalition should comfortably exceed 60%.

**Nordostan revenue baseline:** GDP 20 * tax 0.20 = 4.0. Oil revenue adds ~0.5-1.0 at base oil price. Mandatory costs: ~18 ground * 0.3 + 8 air * 0.3 + 2 naval * 0.3 + 12 missiles * 0.3 + 3 AD * 0.3 = ~12.9 maintenance + 0.25 * 20 = 5.0 social = ~17.9. Revenue of ~5.0 vs mandatory of ~17.9 = immediate deficit of ~12.9. Treasury of 6 depletes in R1.

| Variable | R1 | R2 | R3 | R4 | R5 | R6 | R7 | R8 |
|----------|----|----|----|----|----|----|----|----|
| Nordostan GDP | 17-20 | 14-19 | 12-18 | 11-17 | 10-16 | 10-16 | 10-16 | 10-16 |
| Nordostan inflation | 10-30 | 20-50 | 30-70 | 35-80 | 30-70 | 25-65 | 22-60 | 20-55 |
| Nordostan treasury | 0-2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Nordostan debt_burden | 1.5-4.0 | 3.0-7.0 | 4.5-10 | 6.0-13 | 7.0-14 | 8.0-15 | 8.5-16 | 9.0-17 |
| Nordostan stability | 4.5-5.0 | 4.0-4.8 | 3.5-4.6 | 3.2-4.4 | 3.0-4.2 | 2.8-4.2 | 2.7-4.2 | 2.5-4.2 |
| Nordostan economic_state | NORMAL-STRESSED | STRESSED | STRESSED-CRISIS | STRESSED-CRISIS | CRISIS | CRISIS | CRISIS | CRISIS |
| Sanctions_hit (R1 vs R5) | 3-8% | 3-8% | 3-8% | 3-8% | 2-6% | 2-6% | 2-6% | 2-6% |

### Pass/Fail Criteria
- **PASS** if:
  - Nordostan GDP declines 15-45% over 8 rounds (sanctions + deficit + inflation compound)
  - Treasury depletes by R1-R2 (tiny treasury vs. huge mandatory costs)
  - Inflation rises above baseline by 15%+ within 3 rounds (money printing chain)
  - Debt burden accumulates each round (deficit * 0.15 persistent)
  - Sanctions damage is LESS in R5-R8 than R1-R4 (adaptation factor 0.70 after 4 rounds)
  - Stability stays ABOVE 2.0 through R8 (autocratic resilience D18: delta * 0.75 + siege bonus +0.10)
  - Stability declines more slowly than a democracy would (compare regime_type in formula)
- **CALIBRATE** if debt grows but inflation does not spike (may need money_printing check)
- **FAIL** if:
  - Sanctions produce zero GDP impact (sanctions_damage not calculated)
  - Inflation unchanged after treasury depletion (money printing -> inflation chain broken)
  - Nordostan stability drops below 2.0 by R4 (autocratic resilience not applied)
  - Sanctions damage identical R1 and R8 (no adaptation/diminishing returns)
  - Debt_burden resets between rounds

---

## Scenario 3: SEMICONDUCTOR CRISIS

### Dependencies Tested
D5 (Semiconductor Disruption -> GDP Crash), D7 (Economic Crisis Contagion), D13 (Amphibious Impossibility -> Blockade-Only), D23 (Formosa Blockade = Multi-Domain Crisis)

### Setup (Prescribed Actions)

**Active wars:** Nordostan-Heartland (pre-existing). Columbia-Persia (starting).
**Formosa blockade:** Cathay declares naval blockade of Formosa Strait starting R1. No ground invasion (Formosa has 4 ground; Cathay cannot achieve 4:1 ratio across strait). Blockade maintained R1-R8.
**No other actions.** OPEC normal. No sanctions beyond existing. No tech investment.

**Round-by-round actions:**
- R1: `blockade_changes: {formosa_strait: {controller: cathay, naval_units: 3}}`. Set `formosa_blockade: true`, `chokepoint_status.taiwan_strait: blocked`.
- R2-R8: No changes (blockade persists).

**Semiconductor severity ramp:** R1=0.3, R2=0.5, R3=0.7, R4=0.9, R5+=1.0

### Expected Outcome Ranges (the corridor)

**Semi_hit calculation for Columbia R1:** dep=0.65, severity=0.3, tech_pct=22/100=0.22. Hit = -0.65*0.3*0.22 = -0.043 = -4.3%. At R3: -0.65*0.7*0.22 = -10.0%.
**Semi_hit for Cathay R1:** dep=0.25, severity=0.3, tech_pct=13/100=0.13. Hit = -0.25*0.3*0.13 = -0.98% (much lower self-damage).
**Semi_hit for Yamato R1:** dep=0.55, severity=0.3, tech_pct=20/100=0.20. Hit = -0.55*0.3*0.20 = -3.3%.
**Semi_hit for Teutonia R1:** dep=0.45, severity=0.3, tech_pct=19/100=0.19. Hit = -0.45*0.3*0.19 = -2.6%.

| Variable | R1 | R2 | R3 | R4 | R5 | R6 | R7 | R8 |
|----------|----|----|----|----|----|----|----|----|
| Oil price ($) | 88-100 | 88-100 | 86-100 | 85-100 | 84-100 | 82-98 | 80-96 | 78-95 |
| Columbia GDP | 265-278 | 250-272 | 235-265 | 222-258 | 212-252 | 205-248 | 200-245 | 196-242 |
| Cathay GDP | 188-198 | 187-198 | 186-198 | 185-198 | 184-198 | 183-198 | 182-198 | 181-198 |
| Yamato GDP | 40-43 | 38-43 | 35-42 | 33-41 | 31-40 | 30-40 | 29-40 | 28-40 |
| Hanguk GDP | 17-18 | 16-18 | 15-18 | 14-17 | 13-17 | 13-17 | 12-17 | 12-17 |
| Teutonia GDP | 43-45 | 41-45 | 39-44 | 37-44 | 36-43 | 35-43 | 34-43 | 34-43 |
| Formosa GDP | 5-8 | 3-7 | 2-6 | 1-5 | 0.5-4 | 0.5-4 | 0.5-4 | 0.5-4 |
| Columbia economic_state | NORMAL | NORMAL-STRESSED | STRESSED | STRESSED-CRISIS | CRISIS | CRISIS | CRISIS | CRISIS |
| Cathay economic_state | NORMAL | NORMAL | NORMAL | NORMAL | NORMAL | NORMAL | NORMAL-STRESSED | NORMAL-STRESSED |
| Cathay treasury | 42-45 | 39-44 | 36-43 | 33-42 | 30-41 | 27-40 | 24-39 | 21-38 |

### Pass/Fail Criteria
- **PASS** if:
  - Columbia GDP drops 5-15% by R4 (high formosa_dependency 0.65, high tech sector 22%)
  - Cathay GDP drops < 3% by R4 (low dependency 0.25, low tech sector 13%) -- self-damage is real but limited
  - Yamato and Hanguk visibly damaged (dependency 0.55 and 0.40)
  - Persia and Solaria unaffected by semiconductor (dependency 0 or near-zero)
  - Severity ramps: R1 damage < R3 damage < R5 damage
  - Formosa economy devastated (blockade_fraction applies massive trade impact)
  - Contagion fires if/when a major economy (Columbia GDP >30) enters crisis (D7)
  - Cathay treasury visibly depleting (blockade naval maintenance costs)
- **CALIBRATE** if contagion does not fire because no major economy reaches crisis state
- **FAIL** if:
  - All countries equally affected regardless of formosa_dependency
  - Full severity from R1 (no stockpile buffer / severity ramp)
  - Cathay experiences zero economic self-damage
  - Formosa blockade does not trigger semiconductor disruption check
  - Oil price unaffected (formosa blockade adds +10% disruption)

---

## Scenario 4: MILITARY ATTRITION

### Dependencies Tested
D9 (Naval Buildup -> Parity Crossing), D10 (Overstretch -> Forced Redeployment), D11 (Blockade -> Economic Attrition), D12 (War Attrition -> Ceasefire Pressure)

### Setup (Prescribed Actions)

**Active wars:** Nordostan-Heartland (pre-existing, start_round=-4). Columbia-Persia (starting R0).
**Cathay naval buildup:** Cathay invests 5 coins/round in naval production at normal tier (cost 4/unit, cap 1/round) R1-R8.
**Columbia:** No additional naval investment (relies on auto-production every 2 rounds).
**No sanctions, no blockades, OPEC normal.** Focus is purely on military mechanics.

**Round-by-round actions:**
- R1-R8: `budgets: {cathay: {military: {naval: {coins: 5, tier: normal}}}}`
- All other countries: no military production orders.

### Expected Outcome Ranges (the corridor)

**Naval production math:**
- Cathay: starts 7. +1/round from production. Auto-production also fires every even round if naval >= 5 and no production that round -- but Cathay IS producing, so auto only fires if produced = 0. Since Cathay produces 1/round, auto does not fire. So: R1=8, R2=9, R3=10, R4=11, R5=12, R6=13, R7=14, R8=15.
- Columbia: starts 11. Auto-production +1 every even round (R2, R4, R6, R8) when no manual production. So: R1=11, R2=12, R3=12, R4=13, R5=13, R6=14, R7=14, R8=15.
- Parity crossing: Cathay catches Columbia around R4-R5.

**War tiredness math:**
- Heartland (defender, war started R-4): duration by R1 = 5 rounds. Since >3, society adaptation: base 0.20 * 0.5 = 0.10/round. Starting tiredness 4.0. R1: 4.10, R2: 4.20, R3: 4.30...
- Nordostan (attacker, war started R-4): base 0.15 * 0.5 = 0.075/round. Starting tiredness 4.0. R1: 4.075...
- Columbia (attacker in Persia war, started R0): base 0.15/round R1-R3 (duration <3), then 0.075 R4+. Starting tiredness 1.0. R1: 1.15, R2: 1.30, R3: 1.45, R4: 1.525...

| Variable | R1 | R2 | R3 | R4 | R5 | R6 | R7 | R8 |
|----------|----|----|----|----|----|----|----|----|
| Cathay naval | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
| Columbia naval | 11 | 12 | 12 | 13 | 13 | 14 | 14 | 15 |
| Naval ratio (Cathay/Col) | 0.73 | 0.75 | 0.83 | 0.85 | 0.92 | 0.93 | 1.00 | 1.00 |
| Heartland war_tiredness | 4.0-4.2 | 4.1-4.3 | 4.2-4.5 | 4.3-4.6 | 4.4-4.7 | 4.5-4.8 | 4.6-4.9 | 4.7-5.0 |
| Columbia war_tiredness | 1.1-1.2 | 1.2-1.4 | 1.4-1.6 | 1.5-1.7 | 1.5-1.8 | 1.6-1.9 | 1.6-2.0 | 1.7-2.1 |
| Nordostan war_tiredness | 4.0-4.2 | 4.1-4.3 | 4.1-4.4 | 4.2-4.5 | 4.3-4.5 | 4.3-4.6 | 4.4-4.6 | 4.4-4.7 |
| Heartland stability | 4.7-5.0 | 4.4-4.9 | 4.2-4.8 | 4.0-4.6 | 3.8-4.5 | 3.6-4.4 | 3.4-4.3 | 3.2-4.2 |
| Columbia political_support | 35-40 | 33-39 | 31-38 | 30-37 | 29-36 | 28-36 | 27-35 | 26-35 |

### Pass/Fail Criteria
- **PASS** if:
  - Cathay naval reaches 10+ by R3, achieving near-parity with Columbia Pacific fleet
  - Columbia auto-production fires on even rounds (11->12 on R2, 12->13 on R4, etc.)
  - War tiredness grows for all belligerents each round
  - Society adaptation halves tiredness growth after 3 rounds of war duration
  - Heartland stability erodes visibly (war friction + tiredness penalty)
  - Columbia political support erodes (war tiredness > 2 triggers -(wt-2)*1.0 for democracies)
  - War_hit produces GDP penalty proportional to occupied zones
- **CALIBRATE** if naval numbers are off by 1 unit (production capacity edge case)
- **FAIL** if:
  - Cathay naval does not increase despite production investment
  - Columbia auto-production fires every round instead of every 2
  - War tiredness does not increase for belligerents
  - War tiredness growth does not slow after 3 rounds (adaptation missing)
  - Heartland stability completely stable despite active war

---

## Scenario 5: CEASEFIRE CASCADE

### Dependencies Tested
D17 (Ceasefire -> Stability Recovery -> Momentum Boost), D24 (Peace Deal = Positive Cascade)

### Setup (Prescribed Actions)

**Active wars:** Nordostan-Heartland (pre-existing), Columbia-Persia (starting R0).
**Gulf Gate:** Blocked R1-R3 (Persia ground blockade).
**Actions:**
- R1-R2: Wars active, Gulf Gate blocked. No other actions.
- R3: Columbia-Persia ceasefire. Gulf Gate blockade lifted. `blockade_changes: {gulf_gate_ground: null}`. Remove Persia from wars list.
- R4-R5: Peace in Mashriq. Nordostan-Heartland continues.
- R6: Nordostan-Heartland ceasefire. Remove from wars list.
- R7-R8: Full peace.

**Round-by-round actions:**
- R1: No changes. Wars run. Gulf Gate blocked. OPEC normal.
- R2: No changes.
- R3: Ceasefire Columbia-Persia. Lift Gulf Gate blockade. `sanction_changes: {}` (existing sanctions persist but no new).
- R4: No changes. (Post-Mashriq ceasefire.)
- R5: No changes.
- R6: Ceasefire Nordostan-Heartland. Remove war.
- R7: No changes.
- R8: No changes.

### Expected Outcome Ranges (the corridor)

**Oil price:** With Gulf Gate blocked R1-R2, oil ~$140-180. After lift R3, oil should drop $30-60 within 2 rounds. By R5, oil should be $85-115. By R8, oil should approach baseline $75-95.

**Ceasefire rally:** Momentum boost of +1.5 in first peace round (Pass 2 ceasefire_rally). War tiredness begins decaying (0.80 multiplier per round).

| Variable | R1 | R2 | R3 | R4 | R5 | R6 | R7 | R8 |
|----------|----|----|----|----|----|----|----|----|
| Oil price ($) | 130-175 | 130-175 | 95-140 | 85-120 | 80-110 | 75-100 | 72-95 | 70-92 |
| Columbia momentum | -0.5-0.3 | -1.0-0.3 | 0.5-2.0 | 0.5-2.3 | 0.5-2.5 | 0.5-2.5 | 0.5-2.8 | 0.5-3.0 |
| Columbia war_tiredness | 1.1-1.3 | 1.2-1.5 | 1.0-1.2 | 0.8-1.0 | 0.6-0.8 | 0.5-0.7 | 0.4-0.6 | 0.3-0.5 |
| Heartland war_tiredness | 4.1-4.3 | 4.2-4.5 | 4.3-4.6 | 4.4-4.7 | 4.5-4.8 | 3.6-3.9 | 2.9-3.2 | 2.3-2.6 |
| Heartland momentum | -1.0-0.0 | -1.5-0.0 | -1.5-0.0 | -1.5-0.0 | -1.5-0.0 | 0.0-2.0 | 0.0-2.3 | 0.0-2.5 |
| Columbia GDP | 272-280 | 268-280 | 270-282 | 272-285 | 274-288 | 276-290 | 278-292 | 280-294 |
| Heartland stability | 4.7-5.0 | 4.5-4.9 | 4.3-4.8 | 4.2-4.8 | 4.1-4.7 | 4.2-5.0 | 4.4-5.2 | 4.6-5.4 |
| Heartland economic_state | NORMAL-STRESSED | NORMAL-STRESSED | NORMAL-STRESSED | NORMAL-STRESSED | NORMAL-STRESSED | STRESSED-NORMAL | STRESSED-NORMAL | NORMAL |

### Pass/Fail Criteria
- **PASS** if:
  - Oil drops $30+ within 2 rounds of Gulf Gate reopening (supply normalization)
  - Columbia momentum jumps +1.0 or more in R3 (ceasefire rally in Pass 2)
  - Heartland momentum jumps +1.0 or more in R6 (ceasefire rally)
  - War tiredness decays at ~0.80 multiplier per round after ceasefire (Columbia R3+, Heartland R6+)
  - War tiredness decay is visible: Columbia R4 tiredness < Columbia R2 tiredness
  - Heartland stability improves after R6 ceasefire (war friction stops, tiredness decays)
  - Recovery is SLOWER than decline: momentum builds at +0.3/round max (not instant +5.0)
  - Economic state recovery takes 2+ rounds per level (stressed->normal needs 2 rounds of positive indicators)
- **CALIBRATE** if momentum boost is present but smaller than expected (1.0 instead of 1.5)
- **FAIL** if:
  - No momentum boost upon ceasefire (Pass 2 ceasefire_rally broken)
  - War tiredness does not decay after ceasefire (0.80 multiplier not applied when not at war)
  - Oil price unchanged after Gulf Gate reopening (disruption factor not updating)
  - Instant recovery: economic_state jumps from STRESSED to NORMAL in one round
  - Debt burden disappears upon ceasefire (it should persist)

---

## Scenario 6: DEBT DEATH SPIRAL

### Dependencies Tested
D3 (Money Printing -> Inflation), D4 (Debt Accumulation -> Fiscal Death Spiral), D16 (Economic Crisis -> Stability Crisis -> Regime Vulnerability)

### Setup (Prescribed Actions)

**Focus country:** Ponte (Italy parallel). GDP 22, tax 0.40, treasury 4, inflation 2.5%, stability 6.0, debt_burden 8.0, democracy.
**Active wars:** Nordostan-Heartland only (Ponte not involved).
**Actions:** Ponte receives no aid, no trade benefits. Social spending maintained at baseline (0.30 * GDP). No military production.
**Key mechanic:** Ponte's high debt_burden (8.0) vs revenue (GDP 22 * 0.40 = 8.8 base). Starting debt nearly equals revenue.

**Round-by-round actions:**
- R1-R8: No actions involving Ponte. Let the engine process Ponte's economy naturally.
- Assume no sanctions on Ponte, no tariffs. Gulf Gate blocked (oil price elevated, hurting Ponte as importer).
- R1: `blockade_changes: {gulf_gate_ground: {controller: persia}}` (activate gulf gate blockade for oil pressure)
- OPEC: all normal.

### Expected Outcome Ranges (the corridor)

**Revenue calc R1:** base = 22 * 0.40 = 8.8. Oil revenue = 0. Debt service = 8.0. Net revenue ~0.8.
**Mandatory costs:** maintenance (4 ground + 2 air) * 0.4 = 2.4 + social (0.30*22) = 6.6. Total mandatory = 9.0.
**Deficit R1:** ~9.0 - 0.8 = 8.2. Treasury 4 covers partial. Money printed = 8.2 - 4 = 4.2.
**Inflation spike R1:** 4.2/22 * 80 = ~15.3%. New inflation = 2.5*0.85 + 15.3 = ~17.4%.
**Debt R2:** 8.0 + 8.2*0.15 = 9.23. Revenue shrinks further due to inflation erosion.

| Variable | R1 | R2 | R3 | R4 | R5 | R6 | R7 | R8 |
|----------|----|----|----|----|----|----|----|----|
| Ponte GDP | 20-22 | 18-21 | 16-20 | 14-19 | 12-18 | 11-17 | 10-16 | 9-15 |
| Ponte treasury | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Ponte inflation | 12-22 | 18-35 | 22-45 | 25-55 | 25-55 | 22-50 | 20-45 | 18-40 |
| Ponte debt_burden | 9-10 | 10-12 | 11-14 | 12-16 | 13-17 | 14-18 | 14-19 | 15-20 |
| Ponte stability | 5.5-6.0 | 4.8-5.8 | 4.0-5.5 | 3.5-5.0 | 3.0-4.8 | 2.5-4.5 | 2.2-4.3 | 2.0-4.2 |
| Ponte economic_state | NORMAL-STRESSED | STRESSED | STRESSED-CRISIS | CRISIS | CRISIS | CRISIS | CRISIS | CRISIS-COLLAPSE |
| Ponte regime_status | stable | stable | stable-unstable | unstable | unstable-crisis | crisis | crisis | crisis |
| Capital flight (Pass 2) | none | none | none-mild | mild-severe | severe | severe | severe | severe |

### Pass/Fail Criteria
- **PASS** if:
  - Ponte treasury depletes in R1 (4 coins vs ~8+ deficit -- insufficient)
  - Money printing commences R1 (treasury cannot cover deficit)
  - Inflation spikes by 10%+ above baseline within 2 rounds
  - Debt_burden grows every round (deficit * 0.15 accumulates permanently)
  - By R4-R5, debt_burden exceeds revenue -- fiscal trap is inescapable
  - Stability erodes via inflation friction (`(inflation_delta - 3) * 0.05`) + crisis penalty
  - Capital flight fires in Pass 2 when stability < 3-4 (democracy: 3-8% GDP hit)
  - Feedback loop visible: deficit -> debt -> less revenue -> bigger deficit -> more printing -> more inflation -> less revenue
- **CALIBRATE** if inflation rises but stability does not erode (may need inflation friction calibration)
- **FAIL** if:
  - Ponte runs perpetual deficits with no inflation consequence
  - Debt_burden resets or does not accumulate
  - Treasury goes negative instead of triggering money printing
  - Stability unaffected despite inflation delta > 20% (inflation friction disconnected)
  - No capital flight despite stability < 3 in a democracy

---

## Scenario 7: INFLATION RUNAWAY

### Dependencies Tested
D3 (Money Printing -> Inflation -> Stability Erosion), D16 (Economic Crisis -> Stability)

### Setup (Prescribed Actions)

**Focus country:** Persia. GDP 5, tax 0.18, treasury 1, inflation 50.0% (starting_inflation 50.0), stability 4.0, hybrid regime.
**Active wars:** Columbia-Persia (starting R0). Persia is defender.
**Key mechanic:** Persia at war, negative base growth (-3.0%), high starting inflation. War costs + negative growth = forced money printing. Each round of printing adds to inflation DELTA above 50% baseline.

**Round-by-round actions:**
- R1-R8: No budget changes for Persia. Let engine auto-allocate.
- Gulf Gate: blocked (Persia controls). Oil price elevated.
- OPEC: Persia set to "low" production.

**Persia revenue R1:** GDP 5 * 0.18 = 0.90. Oil revenue at elevated prices (~0.35*5*oil_price*0.01). Debt 0.
**Mandatory:** 8 ground * 0.25 + 6 air * 0.25 + 1 AD * 0.25 = 3.75 maintenance + 0.20*5 = 1.0 social = 4.75.
**Deficit:** ~4.75 - (0.90 + oil_rev) = significant gap. Treasury 1 depletes quickly.

| Variable | R1 | R2 | R3 | R4 | R5 | R6 | R7 | R8 |
|----------|----|----|----|----|----|----|----|----|
| Persia GDP | 4.2-5.0 | 3.5-4.8 | 3.0-4.5 | 2.5-4.2 | 2.0-4.0 | 1.5-3.8 | 1.0-3.5 | 0.5-3.2 |
| Persia inflation | 50-65 | 52-80 | 55-100 | 55-120 | 55-130 | 50-120 | 48-110 | 45-100 |
| Persia inflation_delta | 0-15 | 2-30 | 5-50 | 5-70 | 5-80 | 0-70 | 0-60 | 0-50 |
| Persia stability | 3.5-4.0 | 3.0-3.8 | 2.5-3.6 | 2.2-3.4 | 2.0-3.2 | 1.8-3.2 | 1.5-3.2 | 1.2-3.2 |
| Persia treasury | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Persia economic_state | STRESSED | STRESSED-CRISIS | CRISIS | CRISIS | CRISIS | CRISIS | CRISIS-COLLAPSE | COLLAPSE |

### Pass/Fail Criteria
- **PASS** if:
  - Each round of money printing adds approximately `(money_printed / gdp) * 80` to inflation
  - Inflation DELTA from baseline (50%) drives stability erosion, NOT absolute inflation
  - Stability penalty from inflation: `(inflation_delta - 3) * 0.05` visible
  - Severe inflation penalty fires when delta > 20: `(inflation_delta - 20) * 0.03` additional
  - Natural inflation decay of 15% per round is visible (prev * 0.85)
  - GDP floor at 0.5 coins prevents total annihilation
  - Inflation hard cap at 500% prevents infinite spiral
  - Combined crisis state penalty + inflation friction drives stability toward 2.0 or below
- **CALIBRATE** if inflation rises but baseline delta calculation uses absolute instead of delta
- **FAIL** if:
  - Money printing produces zero inflation change (80x multiplier missing)
  - Inflation delta confusion: stability eroded by absolute 50% instead of delta from baseline
  - No inflation decay (0.85 multiplier missing -- inflation only goes up, never down)
  - GDP goes to zero (floor at 0.5 not applied)

---

## Scenario 8: CONTAGION EVENT

### Dependencies Tested
D7 (Economic Crisis Contagion), D21 (Military Overstretch + Economic Crisis = Strategic Retreat)

### Setup (Prescribed Actions)

**Setup:** Force Columbia into crisis by R3 through simultaneous shocks. Then observe contagion to trade partners.

**Actions:**
- R1: Gulf Gate blocked. Formosa blockaded. Columbia under L2 tariffs from Cathay. Columbia at war with Persia. OPEC all "low".
- R2: Add L2 sanctions from Cathay on Columbia.
- R3-R8: Maintain all pressures.

This combines oil shock + semiconductor disruption + tariffs + war costs to force Columbia into crisis state.

**Round-by-round actions:**
- R1: `blockade_changes: {gulf_gate_ground: {controller: persia}, formosa_strait: {controller: cathay}}`, `opec_production: {nordostan: low, persia: low, solaria: low, mirage: low}`, `tariff_changes: {cathay: {columbia: 2}}`
- R2: `sanction_changes: {cathay: {columbia: 2}}`
- R3-R8: No new changes. Pressures persist.

### Expected Outcome Ranges (the corridor)

**Columbia stress triggers R1:** Oil >150 (yes, Gulf Gate + OPEC low), formosa disrupted + dep>0.3 (yes), GDP growth < -1 (likely). Multiple stress triggers -> STRESSED.
**By R3:** GDP growth likely < -3, inflation possibly elevated, treasury declining. Multiple crisis triggers possible.

| Variable | R1 | R2 | R3 | R4 | R5 | R6 | R7 | R8 |
|----------|----|----|----|----|----|----|----|----|
| Columbia GDP | 255-275 | 235-265 | 215-255 | 200-245 | 190-240 | 185-238 | 180-236 | 178-234 |
| Columbia economic_state | STRESSED | STRESSED-CRISIS | CRISIS | CRISIS | CRISIS | CRISIS | CRISIS | CRISIS |
| Ponte GDP (contagion target) | 21-22 | 20-22 | 19-22 | 18-21 | 17-21 | 17-21 | 16-21 | 16-20 |
| Cathay GDP | 185-198 | 182-196 | 178-194 | 175-194 | 173-194 | 171-194 | 170-194 | 169-194 |
| Teutonia GDP | 42-45 | 40-44 | 38-44 | 36-43 | 35-43 | 34-43 | 34-43 | 33-43 |
| Yamato GDP | 39-43 | 37-42 | 34-41 | 32-40 | 30-39 | 29-39 | 28-39 | 28-39 |
| Contagion fired | no | no | maybe | likely | yes | yes | yes | yes |
| Columbia maintenance cost | 14-16 | 14-16 | 14-16 | 14-16 | 14-16 | 14-16 | 14-16 | 14-16 |

### Pass/Fail Criteria
- **PASS** if:
  - Columbia enters STRESSED by R1-R2 from combined shocks
  - Columbia enters CRISIS by R3-R4
  - When Columbia is in CRISIS with GDP > 30, contagion fires to trade partners with weight > 10%
  - Contagion hit on partners: `severity * trade_weight * 0.02` -- measurable but not catastrophic (0.2-2% GDP)
  - Partners experience momentum drop of -0.3 from contagion
  - Contagion does NOT fire from small economies entering crisis (GDP < 30 threshold)
  - Military maintenance of ~15 coins/round for Columbia creates fiscal pressure (D21 overstretch)
  - Columbia deficit forces money printing, accelerating the crisis spiral
- **CALIBRATE** if contagion magnitudes are present but outside specified ranges
- **FAIL** if:
  - No contagion despite Columbia in crisis with GDP > 30 (Step 11 skipped)
  - Contagion applied to ALL countries regardless of trade weight threshold (>10%)
  - Columbia somehow avoids crisis despite simultaneous oil shock + semiconductor + tariffs + war
  - Small economy crisis generates contagion wave (MAJOR_ECONOMY_THRESHOLD not checked)

---

## Scenario 9: TECH RACE DYNAMICS

### Dependencies Tested
D22 (Tech Race + Rare Earth Restrictions), D5 (Semiconductor Disruption -- tech sector interaction)

### Setup (Prescribed Actions)

**Starting tech levels (with overrides):**
- Columbia: AI L3 (progress 0.80 -- override), threshold for L3 was 0.60 so already past it. Wait -- override sets progress to 0.80, and AI level stays at 3 per CSV. Threshold for L3->L4 is 1.00. So Columbia needs 0.20 more progress.
- Cathay: AI L3 (override from L2), progress 0.10 (override). Threshold for L3->L4 is 1.00. Cathay needs 0.90 more progress.

**Actions:**
- R1-R8: Columbia invests 10 coins/round in AI R&D. Cathay invests 10 coins/round in AI R&D.
- R2: Cathay imposes rare earth restrictions on Columbia at level 2.
- No wars involving Cathay. Existing wars continue.

**Round-by-round actions:**
- R1: `tech_rd: {columbia: {ai: 10}, cathay: {ai: 10}}`
- R2: Same tech_rd. `rare_earth_restrictions: {columbia: 2}`
- R3-R8: Same tech_rd. Rare earth restrictions persist.

### Expected Outcome Ranges (the corridor)

**R&D progress per round (Columbia, no restriction):**
`(10/280) * 0.8 * 1.0 = 0.0286/round`. Progress: 0.80 + 0.029 = 0.829 R1.

**R&D progress per round (Columbia, with L2 restriction R2+):**
Rare earth factor = 1.0 - 2*0.15 = 0.70.
`(10/280) * 0.8 * 0.70 = 0.020/round`. Progress R2: 0.829 + 0.020 = 0.849.

**Rounds to L4 for Columbia (from R2 with restriction):** Need 1.00 - 0.829 = 0.171 more. At 0.020/round: ~8.5 rounds. So Columbia reaches L4 around R10 -- NOT within 8 rounds.

**R&D progress per round (Cathay, no restriction):**
`(10/190) * 0.8 * 1.0 = 0.042/round`. Progress: 0.10 + 0.042 = 0.142 R1.

**Rounds to L4 for Cathay:** Need 1.00 - 0.10 = 0.90 more. At 0.042/round: ~21 rounds. Also not within 8 rounds, but Cathay makes more progress per round than restricted Columbia.

| Variable | R1 | R2 | R3 | R4 | R5 | R6 | R7 | R8 |
|----------|----|----|----|----|----|----|----|----|
| Columbia AI progress | 0.82-0.84 | 0.84-0.86 | 0.86-0.88 | 0.88-0.90 | 0.90-0.92 | 0.92-0.94 | 0.93-0.96 | 0.95-0.98 |
| Cathay AI progress | 0.13-0.16 | 0.17-0.21 | 0.21-0.26 | 0.25-0.30 | 0.29-0.35 | 0.33-0.40 | 0.37-0.44 | 0.41-0.49 |
| Columbia AI level | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 |
| Cathay AI level | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 |
| Rare earth factor (Col) | 1.0 | 0.70 | 0.70 | 0.70 | 0.70 | 0.70 | 0.70 | 0.70 |
| Columbia GDP (AI L3 boost) | 280-285 | 280-285 | 280-285 | 280-285 | 280-285 | 280-285 | 280-285 | 280-285 |
| Cathay GDP (AI L3 boost) | 190-200 | 190-200 | 194-204 | 198-208 | 202-212 | 206-216 | 210-220 | 214-224 |
| Cathay treasury (RE cost) | 45 | 44.4 | 43.8 | 43.2 | 42.6 | 42.0 | 41.4 | 40.8 |

### Pass/Fail Criteria
- **PASS** if:
  - Columbia R&D progress slows visibly after R2 rare earth restrictions (factor drops to 0.70)
  - Cathay R&D progress faster than restricted Columbia per round (despite lower GDP making per-coin progress higher)
  - Rare earth restriction costs Cathay treasury (level * 0.3 = 0.6 coins/round)
  - AI L3 tech_boost of +15% applied to GDP formula for both countries
  - Neither reaches L4 within 8 rounds at these investment levels (threshold 1.00 is high)
  - R&D progress persists between rounds (not reset)
  - Rare earth floor at 40% prevents complete R&D blockade (even at L3 restriction: 1.0 - 0.45 = 0.55, still > 0.40)
- **CALIBRATE** if progress rates are within 20% of calculated but not exact (rounding, GDP changes)
- **FAIL** if:
  - Rare earth restrictions have zero effect on Columbia R&D (factor always 1.0)
  - AI level tech boost not applied to GDP (AI_LEVEL_TECH_FACTOR missing from growth formula)
  - R&D progress resets each round (not persisted in technology state)
  - Both countries reach L4 at same time despite different investment efficiency

---

## Scenario 10: THE FULL TRAP

### Dependencies Tested
D25 (The Thucydides Trap), D9, D14, D15, D19, D20 (cross-cutting)

### Setup (Prescribed Actions)

**All starting conditions active.** Wars: Nordostan-Heartland, Columbia-Persia. Gulf Gate blocked. Existing sanctions.
**This scenario uses FIXED scripted actions to simulate reasonable strategic behavior without AI:**

**Round-by-round actions:**
- R1: Cathay builds naval (+5 coins). Columbia invests in AI R&D (5 coins). OPEC normal. Columbia invests 3 coins in naval.
  - `budgets: {cathay: {military: {naval: {coins: 5, tier: normal}}}, columbia: {military: {naval: {coins: 3, tier: normal}}}}`
  - `tech_rd: {columbia: {ai: 5}}`
- R2 (Columbia midterms): Same Cathay naval build. Columbia election fires. Oil price pressure on voters.
  - `budgets: {cathay: {military: {naval: {coins: 5, tier: normal}}}}`
  - `votes: {columbia: {incumbent_pct: 48}}` (slight opposition advantage)
- R3: Cathay continues naval build. Heartland election fires.
  - `budgets: {cathay: {military: {naval: {coins: 5, tier: normal}}}}`
  - `votes: {heartland: {incumbent_pct: 45}}`
- R4: Cathay at near-parity. Cathay imposes rare earth restrictions L1 on Columbia.
  - `budgets: {cathay: {military: {naval: {coins: 5, tier: normal}}}}`
  - `rare_earth_restrictions: {columbia: 1}`
- R5 (Columbia presidential): Naval parity crossed or near. Columbia presidential election fires.
  - `votes: {columbia: {incumbent_pct: 45}}`
- R6: Post-election. Nordostan-Heartland ceasefire.
- R7: Stabilization round.
- R8: Final assessment.

### Expected Outcome Ranges (the corridor)

| Variable | R1 | R2 | R3 | R4 | R5 | R6 | R7 | R8 |
|----------|----|----|----|----|----|----|----|----|
| Cathay naval | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
| Columbia naval | 11-12 | 12-13 | 12-13 | 13-14 | 13-14 | 14-15 | 14-15 | 15-16 |
| Naval ratio (C/US) | 0.67-0.73 | 0.69-0.75 | 0.77-0.83 | 0.79-0.85 | 0.86-0.92 | 0.87-0.93 | 0.93-1.00 | 0.94-1.00 |
| Oil price ($) | 115-160 | 115-160 | 110-155 | 110-155 | 105-150 | 95-130 | 85-115 | 80-110 |
| Columbia GDP | 268-280 | 260-278 | 255-276 | 250-274 | 248-272 | 250-275 | 252-278 | 254-280 |
| Cathay GDP | 192-200 | 196-208 | 200-216 | 204-222 | 208-228 | 212-234 | 216-240 | 220-246 |
| GDP ratio (Cathay/Col) | 0.69-0.74 | 0.71-0.78 | 0.73-0.82 | 0.75-0.86 | 0.77-0.90 | 0.78-0.92 | 0.79-0.93 | 0.80-0.95 |
| Columbia stability | 6.5-7.0 | 6.2-6.9 | 6.0-6.8 | 5.8-6.7 | 5.6-6.6 | 5.5-6.6 | 5.5-6.7 | 5.5-6.8 |
| Cathay stability | 7.5-8.0 | 7.5-8.0 | 7.5-8.0 | 7.5-8.0 | 7.5-8.0 | 7.5-8.0 | 7.5-8.0 | 7.5-8.0 |
| Columbia midterm (R2) | -- | lose (AI 30-45) | -- | -- | -- | -- | -- | -- |
| Columbia presidential (R5) | -- | -- | -- | -- | toss-up (AI 35-50) | -- | -- | -- |
| Heartland election (R3) | -- | -- | lose (AI 25-40) | -- | -- | -- | -- | -- |

### Pass/Fail Criteria
- **PASS** if:
  - Cathay closes GDP ratio from ~0.68 toward 0.80-0.95 by R8 (structural growth differential)
  - Naval parity approaches or crosses by R5-R7 (Cathay active build vs Columbia auto-production)
  - Columbia midterms (R2) show war penalty + oil penalty making incumbent score < 50
  - Heartland election (R3) shows war tiredness strongly penalizing incumbent
  - Autocratic resilience visible: Cathay stability flat while Columbia/Heartland erode
  - Nuclear deterrence implicit: no direct Cathay-Columbia war despite tension
  - At least 2 of the 5 elections produce incumbent loss
  - Economic interdependence visible: Cathay growth affected by trade disruption if tensions escalate
  - The TRAP is visible: Cathay rising on all metrics while Columbia faces overstretch + democratic constraints
- **CALIBRATE** if parity trend is visible but exact round differs by 1-2
- **FAIL** if:
  - No visible parity trend (Cathay stays permanently behind on all metrics)
  - Columbia cruises through with no pressure (elections easy wins, stability high)
  - Cathay stability collapses despite being at peace (autocracy baseline positive inertia not working)
  - Elections produce no consequence (no leader change, no policy shift)
  - Nuclear countries directly invade each other's homeland
  - Dependencies operate in isolation (oil shock does not affect elections, war does not affect economy)

---

# DEPENDENCY COVERAGE MATRIX

| Dependency | S1 | S2 | S3 | S4 | S5 | S6 | S7 | S8 | S9 | S10 | Coverage |
|------------|----|----|----|----|----|----|----|----|----|----|---------|
| D1: Oil Shock -> GDP | **X** | | | | X | X | | | | X | 4 |
| D2: Sanctions -> GDP Erosion | | **X** | | | | | | | | | 1 |
| D3: Money Printing -> Inflation | | **X** | | | | **X** | **X** | | | | 3 |
| D4: Debt Accumulation | | **X** | | | | **X** | | | | | 2 |
| D5: Semiconductor Disruption | | | **X** | | | | | | X | | 2 |
| D6: Oil Producer Windfall | **X** | | | | | | X | | | | 2 |
| D7: Economic Crisis Contagion | | | **X** | | | | | **X** | | | 2 |
| D8: OPEC Prisoner's Dilemma | **X** | | | | | | | | | | 1 |
| D9: Naval Buildup -> Parity | | | | **X** | | | | | | X | 2 |
| D10: Overstretch -> Redeployment | | | | **X** | | | | | | | 1 |
| D11: Blockade -> Econ Attrition | | | X | **X** | | | | | | | 2 |
| D12: War Attrition -> Ceasefire | | | | **X** | | | | | | | 1 |
| D13: Amphibious Impossibility | | | **X** | | | | | | | | 1 |
| D14: Nuclear Deterrence | | | | | | | | | | **X** | 1 |
| D15: War Tiredness -> Elections | | | | X | | | | | | **X** | 2 |
| D16: Econ Crisis -> Stability | | | | | | **X** | **X** | X | | | 3 |
| D17: Ceasefire -> Recovery | | | | | **X** | | | | | | 1 |
| D18: Autocratic Resilience | | **X** | | | | | | | | X | 2 |
| D19: Democratic Elections | | | | | | | | | | **X** | 1 |
| D20: Alliance Fracture | | | | | | | | | | **X** | 1 |
| D21: Overstretch + Crisis | | | | | | | | **X** | | | 1 |
| D22: Tech Race + Rare Earth | | | | | | | | | **X** | X | 2 |
| D23: Formosa Blockade Multi-Crisis | | | **X** | | | | | | | | 1 |
| D24: Peace Deal Cascade | | | | | **X** | | | | | | 1 |
| D25: Thucydides Trap | | | | | | | | | | **X** | 1 |

**Legend:** **X** = primary test target. X = secondary/supporting test. All 25 dependencies covered at least once. Bold indicates the scenario where that dependency is the PRIMARY validation target.

**Coverage summary:** Every dependency is tested as a primary target in at least one scenario. Dependencies D1, D3, D16 have the highest coverage (3-4 scenarios) because they are the most interconnected. Dependencies D2, D8, D10, D12, D13, D14, D17, D19, D20, D21, D23, D24, D25 each have exactly 1 primary scenario -- these are the highest-risk areas where a single test must be sufficient.

---

# EXECUTION PROTOCOL

1. **Isolation:** Each scenario should be run independently from a fresh state loaded from CSVs (plus overrides).
2. **Determinism:** Random seed should be fixed for reproducibility. Set `random.seed(42)` before each run.
3. **Logging:** Capture full engine log (`self._log`) for each round to trace formula execution.
4. **Comparison:** After each round, compare actual values against the corridor table. Flag any out-of-range values.
5. **Verdict:** Apply pass/fail criteria after R8. Aggregate across scenarios.

**Target:** 8/10 scenarios PASS on first run = engine is well-calibrated. 2/10 CALIBRATE is acceptable. Any FAIL requires investigation and fix before deployment.

---

*Document version: 1.0*
*Engine version: world_model_engine.py v2 (SEED)*
*Dependencies reference: SEED_D_DEPENDENCIES_v1.md*
*Generated: 2026-03-28*
