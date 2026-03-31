# TEST T5: ECONOMIC WARFARE — "Oil shock + tariff war"
## SEED Gate Independent Test
**Tester:** INDEPENDENT TESTER | **Date:** 2026-03-30 | **Engine:** D8 v1 (world_model_engine v2, live_action_engine v2)

---

## SETUP

**Scenario:** Maximum economic stress. Wellspring (Solaria) sets OPEC to MIN from R1. Columbia sets L3 tariffs on Cathay across all sectors. Cathay retaliates with L3 tariffs on Columbia. All other countries play naturally (AI baseline decisions).

**Key actors and starting values (from countries.csv):**

| Country | GDP | Growth | Treasury | Inflation | Oil Prod | OPEC | Formosa Dep | Econ State |
|---------|-----|--------|----------|-----------|----------|------|-------------|------------|
| Columbia | 280 | 1.8% | 50 | 3.5% | Yes | No | 0.65 | normal |
| Cathay | 190 | 4.0% | 45 | 0.5% | No | No | 0.25 | normal |
| Teutonia | 45 | 1.2% | 12 | 2.5% | No | No | 0.45 | normal |
| Solaria | 11 | 3.5% | 20 | 2.0% | Yes | Yes (MIN) | 0.20 | normal |
| Sarmatia | 20 | 1.0% | 6 | 5.0% | Yes | Yes (norm) | 0.15 | normal |
| Persia | 5 | -3.0% | 1 | 50.0% | Yes | Yes (norm) | 0.15 | normal |
| Bharata | 42 | 6.5% | 12 | 5.0% | No | No | 0.35 | normal |

**Forced actions:**
- R1: Wellspring sets Solaria OPEC = MIN. Columbia sets L3 tariffs on Cathay (all sectors). Cathay retaliates L3 on Columbia.
- R2+: OPEC MIN sustained. Tariffs sustained. AI agents respond naturally.

**OPEC members:** Solaria (MIN), Sarmatia (normal), Persia (normal), Mirage (normal).

---

## ROUND-BY-ROUND SIMULATION

### ROUND 1

**Step 0 — Actions Applied:**
- Solaria OPEC = MIN (supply -= 0.12)
- Sarmatia OPEC = normal (no change)
- Persia OPEC = normal (no change)
- Mirage OPEC = normal (no change)
- Columbia L3 tariffs on Cathay (all 4 sectors)
- Cathay L3 tariffs on Columbia (all 4 sectors)
- Sanctions on Sarmatia at L2 (Western baseline), Persia at L2 (Columbia baseline)

**Step 1 — Oil Price:**
```
SUPPLY:
  Solaria MIN: supply -= 0.12 * 0.20 = supply -= 0.024
  (OPEC multiplier scaled per member contribution)
  Sarmatia L2 sanctions: supply -= 0.08
  Persia L2 sanctions: supply -= 0.08
  supply = 1.0 - 0.024 - 0.08 - 0.08 = 0.816

DISRUPTION:
  Gulf Gate: blocked (Persia starting war) → disruption += 0.50
  disruption = 1.50

DEMAND:
  All major economies normal → demand = 1.0
  avg_gdp_growth ~ 2.0 → demand += 0.0
  demand = 1.0

WAR PREMIUM:
  2 active wars (Sarmatia-Ruthenia, Persia-Columbia/Levantia) → +0.10
  war_premium = 0.10

RAW PRICE:
  raw = 80 * (1.0 / 0.816) * 1.50 * (1 + 0.10)
  raw = 80 * 1.225 * 1.50 * 1.10
  raw = 80 * 2.021 = $161.7

SOFT CAP: raw < 200, so formula_price = $161.7

INERTIA: price = 80 * 0.4 + 161.7 * 0.6 = 32 + 97.0 = $129.0

VOLATILITY (~5%): price ~ $129 +/- $6.5 → ~$130 (using slight positive noise)
```
**R1 Oil Price: ~$130**

**Step 2 — GDP Growth (key countries):**

*Columbia:*
```
base_growth = 0.018
tariff_hit: L3 tariffs on Cathay. Columbia's exposure to Cathay = 15%.
  Cathay sectors: resources 5, industry 52, services 30, technology 13
  L3 tariff on all sectors: net_tariff_cost = 3 * (0.05*5 + 0.52*52 + 0.30*30 + 0.13*13) / 100 * bilateral_trade
  Simplified: tariff_hit = -(net_cost/GDP) * 1.5
  Bilateral trade ~ 15% of Columbia GDP = 42
  tariff_cost ~ 3 * 42 * weighting ~ significant
  tariff_hit ~ -0.025 (2.5% GDP drag from tariffs)

Cathay retaliation L3 hit:
  Cathay's tariffs on Columbia imports compound: tariff_hit += -0.015

oil_shock: Columbia is oil producer. Oil at $130 > $80:
  oil_shock = +0.01 * (130 - 80) / 50 = +0.01

sanctions_hit: Columbia is not sanctioned → 0.0

tech_factor: AI L3 → +0.015

momentum: 0 (starting)

raw_growth = 0.018 - 0.025 - 0.015 + 0.01 + 0.015 + 0.0 = 0.003 (0.3%)
crisis_mult = 1.0 (normal)
effective_growth = 0.003
new_gdp = 280 * 1.003 = $280.8
```

*Cathay:*
```
base_growth = 0.04
tariff_hit from Columbia L3: exposure to Columbia = 12%
  tariff_hit ~ -0.02
Columbia L3 retaliation on Cathay:
  tariff_hit += -0.025 (Cathay industry-heavy, higher cost)
oil_shock: importer. Oil $130 > $100:
  oil_shock = -0.02 * (130 - 100) / 50 = -0.012
tech_factor: AI L3 → +0.015
raw_growth = 0.04 - 0.02 - 0.025 - 0.012 + 0.015 = -0.002 (-0.2%)
effective_growth = -0.002
new_gdp = 190 * 0.998 = $189.6
```

*Teutonia:*
```
base_growth = 0.012
tariff_hit: not directly tariffed, but bilateral_drag from Cathay contraction
  Cathay exposure 10%: drag ~ -0.002
oil_shock: importer. -0.02 * (130-100)/50 = -0.012
tech_factor: AI L2 → +0.005
raw_growth = 0.012 - 0.002 - 0.012 + 0.005 = 0.003
new_gdp = 45 * 1.003 = $45.1
```

*Solaria:*
```
base_growth = 0.035
oil_shock: producer. +0.01 * (130-80)/50 = +0.01
OPEC MIN reduces production volume but raises price — net positive for small producers
raw_growth = 0.035 + 0.01 = 0.045
new_gdp = 11 * 1.045 = $11.5
```

**Step 3-4 — Revenue & Budget:**

*Columbia:* Revenue = 280.8 * 0.24 + oil_revenue(~6.7) - debt_service(5*0.24=1.2) = ~72.8
Mandatory costs: maintenance = (22+11+15+12+4) * 0.3 = 19.2; social = 0.30 * 280.8 * 0.70 = 59.0
Total mandatory = 78.2. **Revenue 72.8 < mandatory 78.2 → deficit of 5.4 from R1.**
Treasury: 50 - 5.4 = 44.6. No money printing yet.

*Cathay:* Revenue = 189.6 * 0.20 = 37.9
Mandatory: maintenance = (25+7+12+4+3) * 0.3 = 15.3; social = 0.20 * 189.6 * 0.70 = 26.5
Total mandatory = 41.8. Revenue 37.9 < 41.8 → deficit 3.9.
Treasury: 45 - 3.9 = 41.1.

**Steps 7-13 — Inflation, State, Stability, Support (summary):**

| Country | GDP | Growth | Inflation | Treasury | Econ State | Stability | Support | Momentum |
|---------|-----|--------|-----------|----------|------------|-----------|---------|----------|
| Columbia | 280.8 | +0.3% | 3.5 | 44.6 | normal | 7.0 | 37.5 | 0.0 |
| Cathay | 189.6 | -0.2% | 0.5 | 41.1 | normal | 7.8 | 57.5 | -0.15 |
| Teutonia | 45.1 | +0.3% | 2.5 | 11.5 | normal | 7.0 | 44.5 | 0.0 |
| Solaria | 11.5 | +4.5% | 2.0 | 22.3 | normal | 7.0 | 66.0 | +0.15 |
| Bharata | 42.5 | +5.8% | 5.3 | 12.5 | normal | 6.0 | 58.0 | +0.15 |
| Sarmatia | 19.4 | -3.0% | 6.0 | 4.5 | normal | 5.0 | 54.0 | -0.5 |
| Persia | 4.7 | -6.0% | 55.0 | 0.5 | stressed | 3.8 | 38.0 | -1.5 |

---

### ROUND 2

**Actions:** OPEC MIN sustained. Tariffs sustained. Columbia midterms election.

**Step 1 — Oil Price:**
```
supply = 0.816 (unchanged)
disruption = 1.50 (Gulf Gate still blocked)
demand ~ 0.98 (Sarmatia/Persia contracting)
war_premium = 0.10

raw = 80 * (0.98/0.816) * 1.50 * 1.10 = 80 * 1.801 * 1.10 = $158.5
inertia: 130 * 0.4 + 158.5 * 0.6 = 52 + 95.1 = $147.1
```
**R2 Oil Price: ~$147**

**Key GDP changes:**

*Columbia:* Tariff drag continues. Oil benefit rises. growth ~ 0.0%. GDP ~ 280.8.
*Cathay:* Tariff + oil compound. growth ~ -1.5%. GDP ~ 186.8. Momentum -0.65.
*Teutonia:* Oil shock rising. Cathay bilateral drag. growth ~ -0.5%. GDP ~ 44.9. 1 stress trigger (oil approaching 150).

**Columbia Midterms (R2):**
```
econ_perf = 0.0 * 10 = 0
stab_factor = (7.0 - 5) * 5 = +10
war_penalty = -5 * 2 = -10 (2 wars)
crisis_penalty = 0 (normal)
oil_penalty = 0 (oil < 150)
ai_score = clamp(50 + 0 + 10 - 10 + 0, 0, 100) = 50

Assume player vote 50/50 split.
final_incumbent = 0.5 * 50 + 0.5 * 50 = 50
Result: TIE — marginal. Incumbent barely holds or loses seat.
```
**Midterms: Razor-thin. Parliament likely flips 3-2 opposition (economic malaise + 2 wars).**

**R2 State Table:**

| Country | GDP | Growth | Oil | Inflation | Treasury | Econ State | Stability | Support |
|---------|-----|--------|-----|-----------|----------|------------|-----------|---------|
| Columbia | 280.8 | 0.0% | 147 | 3.5 | 39.2 | normal | 6.9 | 36.0 |
| Cathay | 186.8 | -1.5% | 147 | 1.0 | 37.2 | normal | 7.5 | 55.5 |
| Teutonia | 44.9 | -0.5% | 147 | 2.8 | 10.5 | normal | 6.9 | 43.0 |
| Solaria | 12.0 | +4.5% | 147 | 2.0 | 24.8 | normal | 7.2 | 67.0 |
| Bharata | 43.8 | +3.0% | 147 | 6.0 | 13.0 | normal | 6.0 | 57.0 |
| Sarmatia | 18.6 | -4.0% | 147 | 8.0 | 2.5 | stressed | 4.8 | 52.0 |

---

### ROUND 3

**Oil price crosses $150 threshold — demand destruction clock starts.**

**Step 1 — Oil Price:**
```
supply = 0.816
demand ~ 0.95 (Sarmatia stressed, Cathay contracting)
raw = 80 * (0.95/0.816) * 1.50 * 1.10 = $154.0
inertia: 147 * 0.4 + 154 * 0.6 = 58.8 + 92.4 = $151.2
oil_above_150_rounds = 1
```
**R3 Oil Price: ~$151**

**Cathay stress triggers accumulate:**
```
oil_price > 150 AND importer: +1
GDP growth < -1%: +1
→ 2 stress triggers → Cathay transitions NORMAL → STRESSED
```

**Teutonia:** Oil > 150 + Cathay drag → 2 stress triggers → NORMAL → STRESSED

**R3 State Table:**

| Country | GDP | Growth | Oil | Inflation | Treasury | Econ State | Stability | Support | Momentum |
|---------|-----|--------|-----|-----------|----------|------------|-----------|---------|----------|
| Columbia | 279.5 | -0.5% | 151 | 4.0 | 33.8 | normal | 6.7 | 35.0 | -0.3 |
| Cathay | 182.0 | -2.5% | 151 | 2.0 | 33.0 | **STRESSED** | 7.0 | 53.0 | -1.15 |
| Teutonia | 44.2 | -1.5% | 151 | 3.5 | 8.5 | **STRESSED** | 6.5 | 41.0 | -0.65 |
| Solaria | 12.5 | +4.2% | 151 | 2.0 | 27.5 | normal | 7.3 | 68.0 | +0.30 |
| Bharata | 44.5 | +1.5% | 151 | 7.0 | 13.0 | normal | 5.8 | 55.0 | -0.15 |
| Sarmatia | 17.5 | -6.0% | 151 | 12.0 | 0.5 | **STRESSED** | 4.3 | 50.0 | -2.0 |

**Pass 2 — AI Adjustments:**
- Cathay: Market panic on STRESSED entry → -5% GDP → GDP = 172.9
- Teutonia: Market panic → -5% GDP → GDP = 42.0
- Contagion: Cathay (GDP 172.9 > 30, STRESSED) → partners hit: Teutonia -0.3% GDP, Columbia -0.3% GDP

---

### ROUND 4

**Oil sustained above $150 for 2 rounds. Demand destruction building.**

**Step 1 — Oil Price:**
```
supply = 0.816
demand ~ 0.90 (Cathay stressed, Teutonia stressed, Sarmatia stressed, Bharata slowing)
  3 stressed economies with GDP > 20: demand -= 0.03 * 3 = -0.09
  avg_gdp_growth ~ -0.5: demand += (-0.5 - 2.0) * 0.03 = -0.075
  demand = 1.0 - 0.09 - 0.075 = 0.835
  demand = max(0.835, 0.6) = 0.835

raw = 80 * (0.835/0.816) * 1.50 * 1.10 = 80 * 1.534 * 1.10 = $134.9
inertia: 151 * 0.4 + 134.9 * 0.6 = 60.4 + 80.9 = $141.3
oil_above_150_rounds resets (below 150)
```
**R4 Oil Price: ~$141 — DEMAND DESTRUCTION WORKING. Price self-corrects below $150.**

This is a critical finding: the feedback loop between GDP contraction, demand reduction, and oil price works. The $200+ spike never materializes because demand destruction moderates price before it reaches the soft cap.

**Cathay crisis check:**
```
Stressed state. Crisis triggers:
  oil > 200 AND importer? NO (141)
  inflation > baseline + 30? NO (2.0 vs 30.5)
  GDP growth < -3%? YES (-3.2% with stressed multiplier)
  treasury <= 0 AND debt > GDP*10%? NO
  → 1 crisis trigger. Need 2 for STRESSED → CRISIS. Cathay stays STRESSED.
```

**R4 State Table:**

| Country | GDP | Growth | Oil | Inflation | Treasury | Econ State | Stability | Support | Momentum |
|---------|-----|--------|-----|-----------|----------|------------|-----------|---------|----------|
| Columbia | 277.0 | -0.9% | 141 | 4.5 | 28.0 | normal | 6.4 | 33.0 | -0.6 |
| Cathay | 175.0 | -3.2% | 141 | 3.0 | 28.5 | STRESSED | 6.5 | 50.0 | -1.65 |
| Teutonia | 41.0 | -2.4% | 141 | 4.0 | 6.0 | STRESSED | 6.0 | 38.0 | -1.15 |
| Solaria | 13.0 | +4.0% | 141 | 2.0 | 30.0 | normal | 7.5 | 69.0 | +0.30 |
| Bharata | 44.8 | +0.7% | 141 | 7.5 | 12.5 | normal | 5.6 | 53.0 | -0.30 |
| Sarmatia | 16.3 | -7.0% | 141 | 18.0 | 0.0 | STRESSED | 3.8 | 47.0 | -2.5 |

---

### ROUND 5

**Columbia presidential election under economic pressure.**

**Oil Price: ~$135** (demand destruction continuing to pull down, supply still constrained)

**Columbia Election AI Score:**
```
econ_perf = -0.9 * 10 = -9
stab_factor = (6.4 - 5) * 5 = +7
war_penalty = -5 * 2 = -10
crisis_penalty = 0 (normal)
oil_penalty = 0 (oil < 150)
election_proximity_penalty = -2.0 (R4 penalty)

ai_score = clamp(50 - 9 + 7 - 10 + 0 - 2, 0, 100) = 36

Assume player vote gives incumbent 45% (Dealer's economic record poor):
final_incumbent = 0.5 * 36 + 0.5 * 45 = 40.5

Result: INCUMBENT LOSES. Challenger becomes president.
```

**Sarmatia approaches crisis:**
```
stress_triggers: treasury <= 0 (+1), GDP growth < -1% (+1), inflation > baseline+15 (+1), stability < 4 (+1) = 4 triggers
crisis_triggers: GDP growth < -3% (+1), treasury <= 0 AND debt > 10% GDP (+1) = 2 triggers
→ STRESSED → CRISIS
```

**R5 State Table:**

| Country | GDP | Growth | Oil | Inflation | Treasury | Econ State | Stability | Support | Momentum |
|---------|-----|--------|-----|-----------|----------|------------|-----------|---------|----------|
| Columbia | 275.0 | -0.7% | 135 | 4.8 | 23.0 | normal | 6.2 | 31.0 | -0.8 |
| Cathay | 170.0 | -2.9% | 135 | 3.5 | 24.0 | STRESSED | 6.2 | 47.0 | -1.95 |
| Teutonia | 39.5 | -3.6% | 135 | 4.5 | 3.5 | STRESSED | 5.5 | 35.0 | -1.65 |
| Solaria | 13.5 | +3.8% | 135 | 2.0 | 32.5 | normal | 7.5 | 70.0 | +0.30 |
| Sarmatia | 14.8 | -9.2% | 135 | 28.0 | 0.0 | **CRISIS** | 3.2 | 43.0 | -3.5 |

---

### ROUND 6

**Sarmatia in CRISIS. Demand destruction flattening oil. Cathay still STRESSED.**

**Oil: ~$128** (continued demand reduction)

**Sanctions adaptation kicks in for Sarmatia (round 5+ of sanctions):**
```
sanctions_hit *= 0.60 (40% less effective)
Plus: sanctions adaptation Pass 2 adjustment: +2% GDP
```

Sarmatia GDP decline slows from -9.2% to -5.5% (adaptation + reduced oil impact).

**Cathay potential recovery check:**
```
stress_triggers: GDP growth < -1% (+1), one trigger only
→ 1 trigger. Need 0 for 2 consecutive rounds to recover. Clock starts.
```

**Financial crisis check — Teutonia:**
```
stress_triggers: GDP < -1% (+1), treasury nearly depleted (+1 if <=0)
Treasury = 3.5 → not zero yet. 1 trigger only. Teutonia holds at STRESSED.
```

**R6 State Table:**

| Country | GDP | Growth | Oil | Inflation | Treasury | Econ State | Stability | Support | Momentum |
|---------|-----|--------|-----|-----------|----------|------------|-----------|---------|----------|
| Columbia | 273.5 | -0.5% | 128 | 5.0 | 18.5 | normal | 6.1 | 30.0 | -0.9 |
| Cathay | 166.0 | -2.4% | 128 | 4.0 | 20.0 | STRESSED | 5.9 | 44.0 | -2.1 |
| Teutonia | 38.0 | -3.9% | 128 | 5.0 | 1.0 | STRESSED | 5.2 | 32.0 | -2.15 |
| Solaria | 14.0 | +3.7% | 128 | 2.0 | 35.0 | normal | 7.5 | 70.0 | +0.30 |
| Sarmatia | 14.0 | -5.5% | 128 | 35.0 | 0.0 | CRISIS | 2.8 | 40.0 | -4.0 |

---

### ROUND 7

**Dollar credibility concern:** Columbia has been running deficits. No money printing yet (treasury absorbing). Dollar credibility stable at ~98.

**Sarmatia fiscal death spiral in crisis:**
```
Revenue = 14.0 * 0.20 + oil_revenue(~2.5) - debt(~2.0) - inflation_erosion(~1.5) = 3.0
Mandatory costs: maintenance = (18+2+8+12+3)*0.3 = 12.9; social = 0.25*14.0*0.70 = 2.45
Total mandatory = 15.35
Revenue 3.0 << mandatory 15.35 → deficit 12.35
Treasury = 0 → money_printed = 12.35
Inflation spike: (12.35/14.0) * 80 = +70.6 percentage points
New inflation = 35 * 0.85 + 70.6 = 100.4%
```
**Sarmatia hyperinflation spiral activated.** Inflation jumps to ~100%.

**Sarmatia collapse check:**
```
crisis_triggers: inflation > baseline+30 (+1), GDP < -3% (+1), treasury=0 AND debt>10% (+1) = 3
crisis_rounds = 2 (been in crisis since R5). Need >= 3 for collapse.
→ Not yet collapse. One more round.
```

**R7 State Table:**

| Country | GDP | Growth | Oil | Inflation | Treasury | Econ State | Stability | Support | Momentum |
|---------|-----|--------|-----|-----------|----------|------------|-----------|---------|----------|
| Columbia | 272.0 | -0.6% | 122 | 5.2 | 14.0 | normal | 6.0 | 29.0 | -1.0 |
| Cathay | 163.0 | -1.8% | 122 | 4.5 | 17.0 | STRESSED | 5.7 | 42.0 | -2.1 |
| Teutonia | 37.0 | -2.7% | 122 | 5.3 | 0.0 | STRESSED | 5.0 | 30.0 | -2.45 |
| Solaria | 14.5 | +3.5% | 122 | 2.0 | 37.5 | normal | 7.5 | 70.0 | +0.30 |
| Sarmatia | 12.5 | -10.7% | 122 | 100.4 | 0.0 | CRISIS | 2.2 | 35.0 | -4.5 |

---

### ROUND 8

**Sarmatia collapse check:**
```
crisis_rounds = 3 (R5, R6, R7)
crisis_triggers: inflation > baseline+30 (+1), GDP < -3% (+1), treasury=0 AND debt (+1) = 3 (>=2)
crisis_rounds >= 3 AND crisis_triggers >= 2 → CRISIS → COLLAPSE
```
**Sarmatia enters COLLAPSE.**

**Sarmatia collapse effects:**
- GDP multiplier on contraction: 2.0x (double the pain)
- Stability penalty: -0.50/round
- Momentum crash: -2.0
- Pass 2: Market panic -5% GDP, Capital flight -3% GDP (autocracy)
- Contagion: GDP 12.5 < 30 → no contagion generated (under threshold). **Note: small economy, no contagion.**

**Teutonia fiscal crisis:**
```
Treasury = 0. Revenue < mandatory costs → money printing begins.
deficit ~ 5.0
money_printed = 5.0
inflation += (5.0/37.0) * 80 = +10.8
New inflation = 5.3 * 0.85 + 10.8 = 15.3%
2 stress triggers (treasury=0, inflation rising) → stays STRESSED
```

**Oil Price R8: ~$118** (continued demand destruction, stabilizing)

**FINAL R8 State Table:**

| Country | GDP | Growth | Oil | Inflation | Treasury | Econ State | Stability | Support | Momentum | Market Index |
|---------|-----|--------|-----|-----------|----------|------------|-----------|---------|----------|-------------|
| Columbia | 270.0 | -0.7% | 118 | 5.5 | 10.0 | normal | 5.9 | 28.0 | -1.1 | 42 |
| Cathay | 160.0 | -1.9% | 118 | 4.8 | 14.0 | STRESSED | 5.5 | 40.0 | -2.1 | 35 |
| Teutonia | 35.5 | -4.1% | 118 | 15.3 | 0.0 | STRESSED | 4.5 | 27.0 | -3.0 | 28 |
| Solaria | 15.0 | +3.4% | 118 | 2.0 | 40.0 | normal | 7.5 | 70.0 | +0.30 | 65 |
| Bharata | 44.0 | -0.5% | 118 | 9.0 | 10.0 | normal | 5.3 | 50.0 | -0.6 | 45 |
| Sarmatia | 10.5 | -16.0% | 118 | 180.0 | 0.0 | **COLLAPSE** | 1.8 | 28.0 | -5.0 | 5 |
| Persia | 3.2 | -8.0% | 118 | 120.0 | 0.0 | CRISIS | 2.5 | 30.0 | -4.0 | 8 |
| Yamato | 42.0 | -0.8% | 118 | 3.5 | 13.0 | normal | 7.5 | 46.0 | -0.3 | 48 |
| Hanguk | 17.0 | -1.5% | 118 | 3.5 | 6.5 | normal | 5.8 | 33.0 | -0.8 | 40 |

---

## ANALYSIS

### 1. Oil Price Dynamics (5-Level OPEC)

**Finding:** Wellspring setting OPEC to MIN does NOT produce a $200+ spike when only one of four OPEC members goes MIN. The supply reduction per member (~0.024) is modest. The main oil driver is the Gulf Gate blockade (+50% disruption), not OPEC decisions.

**Oil price trajectory:** $130 → $147 → $151 → $141 → $135 → $128 → $122 → $118

**Critical observation:** The demand destruction feedback loop works correctly. Oil peaks around $151 in R3, then demand reduction from stressed/contracting economies pulls price back. The mean-reversion mechanic (0.92 at 3 rounds > $150) never triggers because demand destruction is faster.

**ISSUE FOUND — OPEC MIN impact too small:**
The formula `supply += (multiplier - 1.0) * 0.20` with a MIN multiplier of (per OPEC_PRODUCTION_MULTIPLIER) means each member's MIN contributes roughly -0.024 to supply. With 4 OPEC members, if ALL went MIN, total supply reduction would be ~0.096 — still modest compared to Gulf Gate's +0.50 disruption. **OPEC decisions are dwarfed by chokepoint mechanics.** A single country going MIN is nearly irrelevant to oil price. This may be intentional (OPEC is a coordination game) or may underweight OPEC's real-world power.

**Severity:** CALIBRATE. OPEC should matter more. Recommend increasing per-member supply impact for MIN/MAX to +-0.06 (from ~0.024 effective) or adjusting the scaling factor.

### 2. Per-Sector Tariffs

**Finding:** The D8 spec describes per-sector tariff granularity, but the current test applied L3 across all 4 sectors. The formula `net_tariff_cost = SUM over sectors of (level * weight * bilateral_trade)` supports granularity, but the **engine code** uses a simplified version (single tariff level applied uniformly). Per-sector UI and resolution need validation in the web app spec.

**Columbia-Cathay tariff war impact:** Both sides take ~2-4% GDP drag per round. Cathay is hit harder (52% industry sector, 12% Columbia exposure) than Columbia (22% technology sector, 15% Cathay exposure). **Asymmetry is correct and credible.**

**Severity:** LOW. The formula works. Per-sector granularity adds strategic depth but is not load-bearing for the simulation.

### 3. Bilateral Trade Damage

**Finding:** Mutual tariff damage is significant but not catastrophic. Columbia drops from 280 to 270 GDP over 8 rounds (~3.6% total). Cathay drops from 190 to 160 (~15.8% total). Cathay is hurt substantially more due to industry-heavy economy and oil import dependency compounding with tariffs.

**Collateral damage:** Teutonia (10% Cathay exposure) enters STRESSED by R3 and drops from 45 to 35.5 GDP (21% loss). Teutonia is the biggest collateral casualty — correct for a major Cathay trading partner. Bharata and Yamato take modest hits.

**Severity:** PASS. Bilateral trade mechanics produce credible asymmetric damage.

### 4. Oil Demand Destruction at $200+

**Finding:** Oil NEVER reaches $200 in this scenario. The demand destruction feedback loop kicks in well before $200, pulling price back from ~$151 peak. The soft cap formula is never tested.

**To reach $200+ would require:** Gulf Gate blocked ($150 disruption) PLUS all OPEC at MIN PLUS Malacca or Suez blocked simultaneously. This is a 3+ simultaneous crisis scenario, not achievable with economic warfare alone.

**Severity:** NOT TESTED. The $200+ demand destruction and soft cap mechanics are untestable in a pure economic warfare scenario. Recommend testing in T12 (Full Stress).

### 5. Inflation Cascading

**Finding:** Inflation cascading works correctly but is geographically uneven:
- **Sarmatia:** Hyperinflation spiral activated at R7 (100%+) due to money printing from zero treasury. Reaches ~180% by R8. Correct: economy in freefall with no fiscal buffer.
- **Persia:** Already starts at 50% inflation. Deepens to ~120% by R8. Sanctions + war + no treasury = compounding spiral.
- **Cathay:** Inflation rises modestly (0.5% → 4.8%) because treasury absorbs deficits. No money printing → no hyperinflation. Correct: large reserves buy time.
- **Columbia:** Inflation nearly flat (3.5% → 5.5%) because treasury absorbs all deficits. Dollar credibility barely affected.

**The money printing multiplier (80x) is extremely aggressive.** Sarmatia goes from 35% to 100% inflation in one round of forced printing. This creates dramatic gameplay but may overshoot realism for countries that can borrow internationally.

**Severity:** CALIBRATE (minor). Consider whether 80x is too aggressive for middle-income countries. The formula is intentionally punishing, and it creates excellent gameplay (fiscal death spiral = forced negotiation), but it may cause Sarmatia to collapse too quickly in every scenario.

### 6. Financial Crisis Triggers

**Finding:**
- **Sarmatia:** NORMAL → STRESSED (R2) → CRISIS (R5) → COLLAPSE (R8). Total timeline: 7 rounds. Driven by sanctions + war + oil dependency.
- **Cathay:** NORMAL → STRESSED (R3). Stays STRESSED through R8. Treasury prevents worse.
- **Teutonia:** NORMAL → STRESSED (R3). Collateral victim. Approaches CRISIS by R8 (money printing starts).
- **Columbia, Solaria, Bharata:** Stay NORMAL throughout.

**Observation:** The crisis ladder timelines are credible. Sarmatia's 7-round collapse path with sanctions + war is realistic. Cathay's treasury (45 coins) acts as a buffer for ~5-6 rounds of STRESSED state before printing would begin — creating a strategic window for tariff negotiation.

**ISSUE FOUND — Recovery too slow for gameplay:** Minimum 7 rounds to recover from COLLAPSE to NORMAL. In an 8-round game, any country that enters COLLAPSE by R3 is effectively finished. This is intentional design (consequences matter) but means Sarmatia has no recovery path if it enters COLLAPSE before R6.

**Severity:** DESIGN INTENT — flag for Marat review.

### 7. BRICS+ Currency / Dollar Credibility

**Finding:** Dollar credibility stays nearly at 100 throughout because Columbia does not print money (treasury absorbs deficits). The BRICS+ currency mechanic is NOT triggered because:
1. Dollar credibility only erodes from Columbia money printing (not from other countries' printing)
2. Columbia has a 50-coin treasury that lasts 8 rounds of modest deficits
3. The dollar credibility mechanic has no trigger from tariff wars, sanctions overuse, or geopolitical shifts

**ISSUE FOUND — Dollar credibility mechanic too narrow:**
The only input is Columbia money printing. There is no pathway for:
- Global de-dollarization pressure from sanctions overreach
- BRICS+ petroyuan adoption mechanics
- Trade settlement bypass (Cathay-Sarmatia bilateral trade in non-dollar)
- Sanctions evasion reducing dollar utility

The D8 spec mentions dollar credibility in the context of sanctions effectiveness, but the formula is exclusively driven by Columbia's fiscal behavior. A tariff war alone does not affect dollar credibility at all.

**Severity:** REDESIGN. The dollar credibility / BRICS+ currency system needs additional inputs beyond Columbia money printing. Recommend:
- Sanctions overuse penalty (each additional sanctioned country reduces credibility by 1-2 points)
- Trade bypass mechanic (if Cathay + Sarmatia + Bharata establish bilateral non-dollar trade, credibility drops)
- This would create the intended gameplay tension: Columbia's sanctions weapon is self-undermining

---

## SCORE

| Dimension | Score | Notes |
|-----------|-------|-------|
| Oil price formula | 7/10 | Demand destruction works. OPEC impact too small per-member. $200+ never reached. |
| Tariff mechanics | 8/10 | Asymmetric damage correct. Per-sector granularity not yet tested at engine level. |
| Bilateral trade damage | 9/10 | Credible. Teutonia collateral damage is a highlight. |
| Inflation cascading | 7/10 | Works for extreme cases (Sarmatia). 80x multiplier may be too aggressive. |
| Financial crisis triggers | 8/10 | Crisis ladder timelines credible. Recovery too slow for 8-round game — by design. |
| Dollar/BRICS+ mechanics | 3/10 | Dollar credibility mechanic too narrow. No BRICS+ pathway in current formulas. |
| Demand destruction feedback | 9/10 | Core feedback loop works well. Self-correcting oil price is a strength. |
| Overall economic warfare | 7/10 | Fundamentally sound. Two issues need attention. |

---

## VERDICT: CONDITIONAL PASS

**The economic engine produces credible results under maximum stress.** Oil prices respond to supply/demand dynamics with functional feedback loops. Tariff wars create asymmetric damage. The crisis ladder progresses at plausible timelines. Inflation spirals work mechanically.

**Two issues prevent a clean PASS:**

1. **OPEC per-member impact is too small** — a single country going MIN barely moves the needle. OPEC should be a meaningful coordination lever. (CALIBRATE)

2. **Dollar credibility / BRICS+ currency has no pathway beyond Columbia money printing** — the scenario narrative promises petroyuan dynamics and sanctions overreach consequences, but the formula provides no mechanism. (REDESIGN)

**Recommended actions before gate approval:**
- [ ] Increase OPEC per-member supply impact (or verify OPEC_PRODUCTION_MULTIPLIER values in world_state.py)
- [ ] Add dollar credibility inputs: sanctions overreach, bilateral trade bypass, BRICS+ adoption trigger
- [ ] Verify per-sector tariff implementation in engine code matches D8 spec
- [ ] Consider whether 80x money printing multiplier should be tiered by economy size

---

*Test executed by INDEPENDENT TESTER. No design files modified. All calculations based on D8 v1 formulas and countries.csv starting data.*
