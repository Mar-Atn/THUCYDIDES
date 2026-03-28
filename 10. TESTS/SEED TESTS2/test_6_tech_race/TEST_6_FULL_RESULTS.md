# TEST 6: RARE EARTH + TECH RACE — Full 8-Round Results

**Test ID:** 6 | **Theme:** Technology Competition
**Date:** 2026-03-27
**Tester:** TESTER-ORCHESTRATOR

---

## SCENARIO SETUP

**Premise:** Cathay activates rare earth restrictions on Columbia at Level 3 (maximum) from R1. Columbia pushes maximum tech investment toward AI L4. Both superpowers prioritize technology. Does the tech race produce interesting dynamics?

**Setup Override:**
- Cathay rare earth restriction on Columbia = Level 3 (from R1)
- Columbia: maximum AI tech investment each round
- Cathay: maximum AI + nuclear tech investment each round
- No Formosa blockade unless Cathay initiates (tested as scenario branch in R5)
- Background wars (Nordostan-Heartland, Columbia-Persia) continue at low intensity
- Other countries invest at normal rates

**Key Formula (from `world_model_engine.py` line 749-788):**
```
R&D progress per round = (investment / GDP) * 0.5 * rare_earth_factor
```
- Rare earth factor (Level 3): 1.0 - (3 * 0.15) = 0.55 (floor 0.40, so 0.55 applies)
- AI thresholds: L0->L1 at 0.20, L1->L2 at 0.40, L2->L3 at 0.60, L3->L4 at 1.00
- Nuclear thresholds: L0->L1 at 0.60, L1->L2 at 0.80, L2->L3 at 1.00
- AI tech GDP factor: L2=+5%, L3=+15%, L4=+30%
- AI combat bonus: L3=+1, L4=+2

---

## STARTING STATE (R0)

| Country | GDP | Treasury | AI Level | AI Progress | AI Threshold | Nuclear Level | Nuc Progress | Nuc Threshold | formosa_dep | RE Restriction |
|---------|-----|----------|----------|-------------|-------------|---------------|-------------|--------------|-------------|----------------|
| Columbia | 280.0 | 50 | L3 | 0.60 | 1.00 | L3 | complete | -- | 0.65 | **L3 (x0.55)** |
| Cathay | 190.0 | 45 | L2 | 0.70 | 0.60 | L2 | 0.80 | 1.00 | 0.25 | none |
| Yamato | 43.0 | 15 | L3 | 0.30 | 1.00 | L0 | 0.10 | 0.60 | 0.55 | none |
| Hanguk | 18.0 | 8 | L2 | 0.50 | 0.60 | L0 | 0.05 | 0.60 | 0.40 | none |
| Formosa | 8.0 | 8 | L2 | 0.50 | 0.60 | L0 | 0.00 | 0.60 | 0.00 | none |
| Bharata | 42.0 | 12 | L2 | 0.45 | 0.60 | L1 | 0.40 | 0.80 | 0.35 | none |
| Albion | 33.0 | 8 | L2 | 0.40 | 0.60 | L2 | 0.70 | 1.00 | 0.40 | none |
| Gallia | 34.0 | 8 | L2 | 0.30 | 0.60 | L2 | 0.80 | 1.00 | 0.35 | none |
| Teutonia | 45.0 | 12 | L2 | 0.20 | 0.60 | L0 | 0.00 | 0.60 | 0.45 | none |

---

## TECH INVESTMENT ASSUMPTIONS

**Budget model:** Revenue = GDP * tax_rate. After mandatory costs (maintenance + debt), discretionary is split. Countries prioritizing tech allocate heavily; others allocate moderate amounts.

| Country | Tech Priority | AI Investment (coins/round) | Nuclear Investment | Notes |
|---------|--------------|---------------------------|-------------------|-------|
| Columbia | **MAXIMUM** | ~18 coins/round | 0 (already L3) | Pushing hard for AI L4. Sacrifices some military spending. |
| Cathay | **HIGH** | ~10 coins/round | ~6 coins/round | Dual track: AI L3 + Nuclear L3. Can afford both. |
| Yamato | MODERATE | ~4 coins/round | 0 | AI L4 pursuit, cautious spending |
| Hanguk | MODERATE | ~3 coins/round | 0 | AI L3 pursuit |
| Formosa | LOW | ~1 coin/round | 0 | Too small, focused on defense |
| Bharata | MODERATE | ~3 coins/round | ~2 coins/round | Dual track |
| Albion | LOW | ~2 coins/round | ~1 coin/round | Moderate |
| Gallia | LOW | ~2 coins/round | ~1 coin/round | Moderate |
| Teutonia | LOW | ~2 coins/round | 0 | Focus on industrial base |

---

## ROUND-BY-ROUND RESULTS

### ROUND 1

**Actions:**
- Cathay activates rare earth restrictions on Columbia at Level 3
- Columbia allocates 18 coins to AI R&D (maximum push)
- Cathay allocates 10 coins AI + 6 coins nuclear R&D
- Background: Nordostan-Heartland war continues, Columbia-Persia conflict at low intensity

**Tech Investment Calculations:**

**Columbia AI R&D:**
```
investment = 18 coins
GDP = 280
base_progress = (18 / 280) * 0.5 = 0.0321
rare_earth_factor = 0.55 (Level 3 restriction)
actual_progress = 0.0321 * 0.55 = 0.0177
new_progress = 0.60 + 0.0177 = 0.6177
threshold for L4 = 1.00
remaining = 1.00 - 0.6177 = 0.3823
```
Columbia AI: L3, 61.8% toward L4 (+1.8%)

**Cathay AI R&D:**
```
investment = 10 coins
GDP = 190
base_progress = (10 / 190) * 0.5 = 0.0263
rare_earth_factor = 1.0 (no restriction)
actual_progress = 0.0263
new_progress = 0.70 + 0.0263 = 0.7263
threshold for L3 = 0.60
```
**BREAKTHROUGH: Cathay AI -> L3!** (Progress was 0.70, threshold was 0.60 -- already past threshold!)

Wait -- Cathay's starting progress is 0.70 and the L2->L3 threshold is 0.60. **Cathay already exceeded the threshold at game start.** This means Cathay should advance to AI L3 immediately upon the first engine tick.

*DESIGN NOTE: This is a critical finding. Cathay starts at 0.70 progress with a 0.60 threshold. The engine would promote them to L3 on the first processing pass, resetting progress to 0.0. This means Cathay enters R1 effectively at AI L3 with 0.0 progress toward L4.*

**Corrected Cathay AI R&D (post-levelup):**
```
After levelup: AI L3, progress reset to 0.0
R1 investment adds: 0.0263
new_progress = 0.0 + 0.0263 = 0.0263
threshold for L4 = 1.00
```
Cathay AI: L3, 2.6% toward L4

**Cathay Nuclear R&D:**
```
investment = 6 coins
GDP = 190
progress = (6 / 190) * 0.5 = 0.0158
new_progress = 0.80 + 0.0158 = 0.8158
threshold for L3 = 1.00
remaining = 0.1842
```
Cathay Nuclear: L2, 81.6% toward L3

**Other Countries:**
| Country | AI Investment | Progress Calc | New AI Progress | AI Level | Notes |
|---------|-------------|---------------|-----------------|----------|-------|
| Yamato | 4 | (4/43)*0.5=0.0465 | 0.30+0.047=0.347 | L3, 34.7% | Steady |
| Hanguk | 3 | (3/18)*0.5=0.0833 | 0.50+0.083=0.583 | L2, 58.3% | Near L3 |
| Formosa | 1 | (1/8)*0.5=0.0625 | 0.50+0.063=0.563 | L2, 56.3% | Near L3 |
| Bharata | 3 AI, 2 nuc | AI:(3/42)*0.5=0.036, Nuc:(2/42)*0.5=0.024 | AI:0.486, Nuc:0.424 | AI L2, 48.6%; Nuc L1, 42.4% | Dual |

**GDP Impact from Tech Multipliers R1:**
| Country | AI Level | Tech Factor | GDP Effect |
|---------|----------|-------------|------------|
| Columbia | L3 | 1.15 (+15%) | GDP growth boosted significantly |
| Cathay | L3 (just achieved) | 1.15 (+15%) | **Parity with Columbia on tech GDP** |
| Yamato | L3 | 1.15 (+15%) | Same tier as superpowers |
| Hanguk | L2 | 1.05 (+5%) | Modest boost |
| Formosa | L2 | 1.05 (+5%) | Modest boost |

**GDP Calculations (simplified, key countries):**
```
Columbia: 280 * (1 + 1.8% * 1.15 * other_factors) = 280 * 1.0189 = ~285.3
  (tech_factor=1.15, war_factor~0.98, tariff~0.97, semi=1.0)
Cathay: 190 * (1 + 4.0% * 1.15 * other_factors) = 190 * 1.0434 = ~198.2
  (tech_factor=1.15 NOW, tariff~0.96, semi=0.975)
```

**R1 State Table:**

| Country | GDP | AI Lvl | AI Prog | Nuc Lvl | Nuc Prog | Tech Factor | Treasury |
|---------|-----|--------|---------|---------|----------|-------------|----------|
| Columbia | 285.3 | L3 | 0.618 | L3 | done | 1.15 | ~44 |
| Cathay | 198.2 | **L3** | 0.026 | L2 | 0.816 | **1.15** | ~39 |
| Yamato | 43.4 | L3 | 0.347 | L0 | 0.10 | 1.15 | ~13 |
| Hanguk | 18.4 | L2 | 0.583 | L0 | 0.05 | 1.05 | ~7 |
| Formosa | 8.2 | L2 | 0.563 | L0 | 0.00 | 1.05 | ~7 |
| Bharata | 44.7 | L2 | 0.486 | L1 | 0.424 | 1.05 | ~10 |

**Key Event:** Cathay reaches AI L3 immediately (was already past threshold). Now has same +15% GDP tech factor as Columbia. The tech gap *closes* rather than opens.

---

### ROUND 2

**Columbia AI R&D:**
```
investment = 18 coins, GDP = 285.3
progress = (18/285.3) * 0.5 * 0.55 = 0.0174
new = 0.618 + 0.0174 = 0.635
remaining to L4: 0.365
```
Columbia AI: L3, 63.5% toward L4

**Cathay AI R&D:**
```
investment = 10 coins, GDP = 198.2
progress = (10/198.2) * 0.5 = 0.0252
new = 0.026 + 0.0252 = 0.051
remaining to L4: 0.949
```
Cathay AI: L3, 5.1% toward L4

**Cathay Nuclear R&D:**
```
investment = 6 coins, GDP = 198.2
progress = (6/198.2) * 0.5 = 0.0151
new = 0.816 + 0.0151 = 0.831
remaining to L3: 0.169
```
Cathay Nuclear: L2, 83.1% toward L3

**Other Countries:**
| Country | New AI Progress | New Nuc Progress | Level Changes |
|---------|-----------------|------------------|---------------|
| Yamato | 0.347+0.046=0.393 | 0.10 | -- |
| Hanguk | 0.583+0.082=0.665 | 0.05 | **AI -> L3!** (0.665 > 0.60) reset to 0.065 |
| Formosa | 0.563+0.061=0.624 | 0.00 | **AI -> L3!** (0.624 > 0.60) reset to 0.024 |
| Bharata | 0.486+0.034=0.520 | 0.424+0.024=0.448 | -- |

**BREAKTHROUGHS R2:**
- **Hanguk AI -> L3** (tech factor now 1.15, combat bonus +1)
- **Formosa AI -> L3** (tech factor now 1.15, combat bonus +1 -- significant for defense!)

**GDP Calculations R2:**
```
Columbia: 285.3 * 1.0187 = ~290.6 (tech=1.15, war costs down slightly)
Cathay: 198.2 * 1.0430 = ~206.7 (tech=1.15, strong base growth)
Yamato: 43.4 * 1.0112 = ~43.9
Hanguk: 18.4 * 1.0231 = ~18.8 (tech boost kicks in next round)
Formosa: 8.2 * 1.0315 = ~8.5 (tech boost kicks in next round)
```

**Columbia Midterms (SCHEDULED EVENT R2):**
Election occurs. Columbia is spending heavily on tech at the expense of social/military. Possible political cost.

**R2 State Table:**

| Country | GDP | AI Lvl | AI Prog | Nuc Lvl | Nuc Prog | Tech Factor | Gap Ratio |
|---------|-----|--------|---------|---------|----------|-------------|-----------|
| Columbia | 290.6 | L3 | 0.635 | L3 | done | 1.15 | -- |
| Cathay | 206.7 | L3 | 0.051 | L2 | 0.831 | 1.15 | 0.711 |
| Yamato | 43.9 | L3 | 0.393 | L0 | 0.10 | 1.15 | -- |
| Hanguk | 18.8 | **L3** | 0.065 | L0 | 0.05 | **1.15** | -- |
| Formosa | 8.5 | **L3** | 0.024 | L0 | 0.00 | **1.15** | -- |
| Bharata | 47.6 | L2 | 0.520 | L1 | 0.448 | 1.05 | -- |

---

### ROUND 3

**Columbia AI R&D:**
```
investment = 18, GDP = 290.6
progress = (18/290.6) * 0.5 * 0.55 = 0.0170
new = 0.635 + 0.0170 = 0.652
remaining to L4: 0.348
```

**Cathay AI R&D:**
```
investment = 10, GDP = 206.7
progress = (10/206.7) * 0.5 = 0.0242
new = 0.051 + 0.0242 = 0.075
```

**Cathay Nuclear R&D:**
```
investment = 6, GDP = 206.7
progress = (6/206.7) * 0.5 = 0.0145
new = 0.831 + 0.0145 = 0.846
remaining to L3: 0.154
```

**Other Countries:**
| Country | New AI Progress | Level Changes |
|---------|-----------------|---------------|
| Yamato | 0.393+0.045=0.438 | -- |
| Hanguk | 0.065+0.079=0.144 | -- |
| Formosa | 0.024+0.059=0.083 | -- |
| Bharata | 0.520+0.032=0.552 | -- (close to L3) |

**R3 State Table:**

| Country | GDP | AI Lvl | AI Prog | Nuc Lvl | Nuc Prog | Tech Factor |
|---------|-----|--------|---------|---------|----------|-------------|
| Columbia | 296.1 | L3 | 0.652 | L3 | done | 1.15 |
| Cathay | 215.6 | L3 | 0.075 | L2 | 0.846 | 1.15 |
| Yamato | 44.4 | L3 | 0.438 | L0 | 0.10 | 1.15 |
| Hanguk | 19.4 | L3 | 0.144 | L0 | 0.05 | 1.15 |
| Formosa | 8.7 | L3 | 0.083 | L0 | 0.00 | 1.15 |
| Bharata | 50.7 | L2 | 0.552 | L1 | 0.472 | 1.05 |

---

### ROUND 4

**Columbia AI R&D:**
```
investment = 18, GDP = 296.1
progress = (18/296.1) * 0.5 * 0.55 = 0.0167
new = 0.652 + 0.0167 = 0.669
remaining to L4: 0.331
```

**Cathay AI R&D:**
```
investment = 10, GDP = 215.6
progress = (10/215.6) * 0.5 = 0.0232
new = 0.075 + 0.0232 = 0.098
```

**Cathay Nuclear R&D:**
```
investment = 6, GDP = 215.6
progress = (6/215.6) * 0.5 = 0.0139
new = 0.846 + 0.0139 = 0.860
remaining to L3: 0.140
```

**Other Countries:**
| Country | New AI Progress | Level Changes |
|---------|-----------------|---------------|
| Yamato | 0.438+0.044=0.482 | -- |
| Hanguk | 0.144+0.076=0.220 | -- |
| Bharata | 0.552+0.030=0.582 | -- (very close to L3) |

**R4 State Table:**

| Country | GDP | AI Lvl | AI Prog | Nuc Lvl | Nuc Prog | Tech Factor |
|---------|-----|--------|---------|---------|----------|-------------|
| Columbia | 301.7 | L3 | 0.669 | L3 | done | 1.15 |
| Cathay | 224.9 | L3 | 0.098 | L2 | 0.860 | 1.15 |
| Yamato | 44.9 | L3 | 0.482 | L0 | 0.10 | 1.15 |
| Hanguk | 19.8 | L3 | 0.220 | L0 | 0.05 | 1.15 |
| Bharata | 54.0 | L2 | 0.582 | L1 | 0.496 | 1.05 |

**Gap Ratio: 224.9/301.7 = 0.745** (was 0.679 at start -- closing steadily)

---

### ROUND 5

**Columbia AI R&D:**
```
investment = 18, GDP = 301.7
progress = (18/301.7) * 0.5 * 0.55 = 0.0164
new = 0.669 + 0.0164 = 0.685
remaining to L4: 0.315
```

**Cathay AI R&D:**
```
investment = 10, GDP = 224.9
progress = (10/224.9) * 0.5 = 0.0222
new = 0.098 + 0.0222 = 0.120
```

**Cathay Nuclear R&D:**
```
investment = 6, GDP = 224.9
progress = (6/224.9) * 0.5 = 0.0133
new = 0.860 + 0.0133 = 0.873
remaining to L3: 0.127
```

**Other Countries:**
| Country | New AI Progress | Level Changes |
|---------|-----------------|---------------|
| Yamato | 0.482+0.043=0.525 | -- |
| Hanguk | 0.220+0.075=0.295 | -- |
| Bharata | 0.582+0.029=0.611 | **AI -> L3!** (0.611 > 0.60) reset to 0.011 |

**BREAKTHROUGH R5:**
- **Bharata AI -> L3** (tech factor now 1.15, combat bonus +1)

**Columbia Presidential Election (SCHEDULED EVENT R5):**
Columbia has been spending max on tech for 5 rounds. GDP is growing well (+15% tech factor) but military readiness may be questioned. The tech race becomes a campaign issue.

**SCENARIO BRANCH -- Formosa Strait Crisis:**
If Cathay blockades Formosa Strait in R5, semiconductor disruption hits:
```
Columbia: formosa_dep=0.65, severity=0.5 (blockade), tech_pct=0.22
  semiconductor_factor = 1.0 - (0.65 * 0.5 * 0.22) = 1.0 - 0.072 = 0.928
  GDP growth penalty: ~7.2% reduction in growth rate
Cathay: formosa_dep=0.25, severity=0.5
  semiconductor_factor = 1.0 - (0.25 * 0.5 * 0.13) = 1.0 - 0.016 = 0.984 (minimal self-harm)
Yamato: formosa_dep=0.55, severity=0.5
  semiconductor_factor = 1.0 - (0.55 * 0.5 * 0.20) = 1.0 - 0.055 = 0.945
```
**Formosa blockade hurts Columbia 4.5x more than Cathay.** This is a powerful secondary tech weapon.

*For this test: NO Formosa blockade (baseline). Branch noted for analysis.*

**R5 State Table:**

| Country | GDP | AI Lvl | AI Prog | Nuc Lvl | Nuc Prog | Tech Factor |
|---------|-----|--------|---------|---------|----------|-------------|
| Columbia | 307.4 | L3 | 0.685 | L3 | done | 1.15 |
| Cathay | 234.6 | L3 | 0.120 | L2 | 0.873 | 1.15 |
| Yamato | 45.4 | L3 | 0.525 | L0 | 0.10 | 1.15 |
| Hanguk | 20.3 | L3 | 0.295 | L0 | 0.05 | 1.15 |
| Bharata | 57.5 | **L3** | 0.011 | L1 | 0.520 | **1.15** |

**Gap Ratio: 234.6/307.4 = 0.763**

---

### ROUND 6

**Columbia AI R&D:**
```
investment = 18, GDP = 307.4
progress = (18/307.4) * 0.5 * 0.55 = 0.0161
new = 0.685 + 0.0161 = 0.701
remaining to L4: 0.299
```

**Cathay AI R&D:**
```
investment = 10, GDP = 234.6
progress = (10/234.6) * 0.5 = 0.0213
new = 0.120 + 0.0213 = 0.141
```

**Cathay Nuclear R&D:**
```
investment = 6, GDP = 234.6
progress = (6/234.6) * 0.5 = 0.0128
new = 0.873 + 0.0128 = 0.886
remaining to L3: 0.114
```

**Other Countries:**
| Country | New AI Progress | Level Changes |
|---------|-----------------|---------------|
| Yamato | 0.525+0.043=0.568 | -- |
| Hanguk | 0.295+0.073=0.368 | -- |

**R6 State Table:**

| Country | GDP | AI Lvl | AI Prog | Nuc Lvl | Nuc Prog | Tech Factor |
|---------|-----|--------|---------|---------|----------|-------------|
| Columbia | 313.2 | L3 | 0.701 | L3 | done | 1.15 |
| Cathay | 244.7 | L3 | 0.141 | L2 | 0.886 | 1.15 |
| Yamato | 45.9 | L3 | 0.568 | L0 | 0.10 | 1.15 |
| Hanguk | 20.8 | L3 | 0.368 | L0 | 0.05 | 1.15 |

**Gap Ratio: 244.7/313.2 = 0.781**

---

### ROUND 7

**Columbia AI R&D:**
```
investment = 18, GDP = 313.2
progress = (18/313.2) * 0.5 * 0.55 = 0.0158
new = 0.701 + 0.0158 = 0.717
remaining to L4: 0.283
```

**Cathay AI R&D:**
```
investment = 10, GDP = 244.7
progress = (10/244.7) * 0.5 = 0.0204
new = 0.141 + 0.0204 = 0.162
```

**Cathay Nuclear R&D:**
```
investment = 6, GDP = 244.7
progress = (6/244.7) * 0.5 = 0.0123
new = 0.886 + 0.0123 = 0.898
remaining to L3: 0.102
```

**Other Countries:**
| Country | New AI Progress | Level Changes |
|---------|-----------------|---------------|
| Yamato | 0.568+0.042=0.610 | -- |
| Hanguk | 0.368+0.072=0.440 | -- |

**R7 State Table:**

| Country | GDP | AI Lvl | AI Prog | Nuc Lvl | Nuc Prog | Tech Factor |
|---------|-----|--------|---------|---------|----------|-------------|
| Columbia | 319.1 | L3 | 0.717 | L3 | done | 1.15 |
| Cathay | 255.2 | L3 | 0.162 | L2 | 0.898 | 1.15 |
| Yamato | 46.4 | L3 | 0.610 | L0 | 0.10 | 1.15 |
| Hanguk | 21.3 | L3 | 0.440 | L0 | 0.05 | 1.15 |

**Gap Ratio: 255.2/319.1 = 0.800** (was 0.679 at start)

---

### ROUND 8

**Columbia AI R&D:**
```
investment = 18, GDP = 319.1
progress = (18/319.1) * 0.5 * 0.55 = 0.0155
new = 0.717 + 0.0155 = 0.733
remaining to L4: 0.267
```

**Cathay AI R&D:**
```
investment = 10, GDP = 255.2
progress = (10/255.2) * 0.5 = 0.0196
new = 0.162 + 0.0196 = 0.181
```

**Cathay Nuclear R&D:**
```
investment = 6, GDP = 255.2
progress = (6/255.2) * 0.5 = 0.0118
new = 0.898 + 0.0118 = 0.910
remaining to L3: 0.090
```

**Other Countries:**
| Country | New AI Progress | Level Changes |
|---------|-----------------|---------------|
| Yamato | 0.610+0.042=0.652 | -- |
| Hanguk | 0.440+0.070=0.510 | -- |

**R8 FINAL State Table:**

| Country | GDP | AI Lvl | AI Prog | Nuc Lvl | Nuc Prog | Tech Factor | Combat Bonus |
|---------|-----|--------|---------|---------|----------|-------------|-------------|
| Columbia | 325.1 | L3 | **0.733** | L3 | done | 1.15 | +1 |
| Cathay | 266.2 | L3 | 0.181 | L2 | **0.910** | 1.15 | +1 |
| Yamato | 46.9 | L3 | 0.652 | L0 | 0.10 | 1.15 | +1 |
| Hanguk | 21.8 | L3 | 0.510 | L0 | 0.05 | 1.15 | +1 |
| Formosa | 9.8 | L3 | 0.220 | L0 | 0.00 | 1.15 | +1 |
| Bharata | 68.5 | L3 | 0.090 | L1 | 0.590 | 1.15 | +1 |

---

## SUMMARY TABLE: TECH PROGRESSION OVER 8 ROUNDS

### Columbia AI (L3 -> L4 attempt, restricted)

| Round | Progress | Gain | Cumulative Gain | Remaining |
|-------|----------|------|-----------------|-----------|
| R0 | 0.600 | -- | -- | 0.400 |
| R1 | 0.618 | +0.018 | 0.018 | 0.382 |
| R2 | 0.635 | +0.017 | 0.035 | 0.365 |
| R3 | 0.652 | +0.017 | 0.052 | 0.348 |
| R4 | 0.669 | +0.017 | 0.069 | 0.331 |
| R5 | 0.685 | +0.016 | 0.085 | 0.315 |
| R6 | 0.701 | +0.016 | 0.101 | 0.299 |
| R7 | 0.717 | +0.016 | 0.117 | 0.283 |
| R8 | 0.733 | +0.016 | 0.133 | **0.267** |

**Columbia gains ~0.017/round under restriction.** At this rate, Columbia needs ~24 total rounds to reach AI L4 from the 0.60 start. Within 8 rounds, Columbia covers only 33% of the gap (0.133 out of 0.400 needed).

**Without restriction (x1.0 instead of x0.55):** Progress per round would be ~0.032, reaching L4 in ~13 rounds from 0.60 start. Still not within 8 rounds, but nearly twice as fast.

### Cathay AI (L2 -> L3 -> L4 attempt, unrestricted)

| Round | Level | Progress | Gain | Notes |
|-------|-------|----------|------|-------|
| R0 | L2 | 0.700 | -- | Already past L3 threshold (0.60)! |
| R1 | **L3** | 0.026 | -- | Instant levelup + first investment |
| R2 | L3 | 0.051 | +0.025 | |
| R3 | L3 | 0.075 | +0.024 | |
| R4 | L3 | 0.098 | +0.023 | |
| R5 | L3 | 0.120 | +0.022 | |
| R6 | L3 | 0.141 | +0.021 | |
| R7 | L3 | 0.162 | +0.020 | |
| R8 | L3 | 0.181 | +0.020 | |

**Cathay gains ~0.022/round toward L4.** At this rate, Cathay needs ~40+ rounds to reach AI L4. Columbia is ahead on the L4 race despite the restriction because it started at 0.60 progress.

### Cathay Nuclear (L2 -> L3 attempt)

| Round | Progress | Gain | Remaining |
|-------|----------|------|-----------|
| R0 | 0.800 | -- | 0.200 |
| R1 | 0.816 | +0.016 | 0.184 |
| R2 | 0.831 | +0.015 | 0.169 |
| R3 | 0.846 | +0.015 | 0.154 |
| R4 | 0.860 | +0.014 | 0.140 |
| R5 | 0.873 | +0.013 | 0.127 |
| R6 | 0.886 | +0.013 | 0.114 |
| R7 | 0.898 | +0.012 | 0.102 |
| R8 | 0.910 | +0.012 | **0.090** |

**Cathay does NOT reach Nuclear L3 within 8 rounds.** At ~0.014/round, needs ~7 more rounds (R15). This is because nuclear investment of 6 coins against a GDP of 190+ yields tiny progress increments.

### GDP Gap Ratio (Cathay/Columbia)

| Round | Columbia GDP | Cathay GDP | Ratio | Change |
|-------|------------|-----------|-------|--------|
| R0 | 280.0 | 190.0 | 0.679 | -- |
| R1 | 285.3 | 198.2 | 0.695 | +0.016 |
| R2 | 290.6 | 206.7 | 0.711 | +0.016 |
| R3 | 296.1 | 215.6 | 0.728 | +0.017 |
| R4 | 301.7 | 224.9 | 0.745 | +0.017 |
| R5 | 307.4 | 234.6 | 0.763 | +0.018 |
| R6 | 313.2 | 244.7 | 0.781 | +0.018 |
| R7 | 319.1 | 255.2 | 0.800 | +0.019 |
| R8 | 325.1 | 266.2 | **0.819** | +0.019 |

**The GDP gap closes from 0.679 to 0.819 over 8 rounds.** This is driven entirely by Cathay's higher base growth rate (4.0% vs 1.8%), NOT by tech differentiation (both are at L3/+15% for the entire game). The tech race produces no GDP divergence because neither country changes AI level during the 8-round game.

---

## BREAKTHROUGH TIMELINE (ALL COUNTRIES)

| Round | Country | Breakthrough | Effect |
|-------|---------|-------------|--------|
| R1 | Cathay | AI L2 -> L3 | +15% GDP factor, +1 combat bonus. **Instant -- was already past threshold.** |
| R2 | Hanguk | AI L2 -> L3 | +15% GDP factor, +1 combat bonus |
| R2 | Formosa | AI L2 -> L3 | +15% GDP factor, +1 combat bonus (defense boost!) |
| R5 | Bharata | AI L2 -> L3 | +15% GDP factor, +1 combat bonus |

**NO L4 breakthroughs in 8 rounds.** Columbia, the closest, finishes at 73.3% (needs 100%).
**NO Nuclear L3 for Cathay.** Finishes at 91.0% (needs 100%).

---

## ANALYSIS

### Finding 1: COLUMBIA CANNOT REACH AI L4 IN 8 ROUNDS -- EVEN WITHOUT RESTRICTIONS

This is the most important finding. The R&D formula produces such small increments that the L3->L4 gap (0.40 from 0.60 starting progress to 1.00 threshold) is effectively uncrossable in an 8-round game.

**Without restriction:** ~0.032/round * 8 = 0.256 gained. End at 0.856. Still short.
**With Level 3 restriction:** ~0.017/round * 8 = 0.133 gained. End at 0.733. Far short.

The restriction slows Columbia by ~45%, but the base speed is already too slow to matter within the game timeline. **AI L4 is unreachable.** This means the +30% GDP factor and +2 combat bonus are effectively impossible rewards -- they exist in the design but no country can achieve them.

**Impact on game design:** The L4 tier is a phantom. Players will invest heavily toward something they cannot achieve. This could be intentional (simulating the real-world AI race where "AGI" is always 5 years away) or it could be a calibration problem.

### Finding 2: RARE EARTH RESTRICTIONS PRODUCE MINIMAL STRATEGIC IMPACT

The rare earth restriction (Level 3, x0.55 R&D penalty) sounds dramatic but has negligible game impact because:

1. **L4 is unreachable anyway** -- slowing progress toward an unreachable goal doesn't change outcomes
2. **Columbia already has L3** -- the restriction doesn't downgrade existing tech, only slows new progress
3. **The GDP tech factor stays at 1.15** for both superpowers for the entire game
4. **No combat bonus change** -- both stay at +1

The rare earth mechanic as designed is a **flavor element, not a strategic weapon**. Cathay gains nothing tangible by restricting Columbia's rare earths.

### Finding 3: CATHAY'S AI L3 STARTING STATE IS A DATA BUG

Cathay starts at AI L2 with 0.70 progress, but the L2->L3 threshold is 0.60. **Cathay has already passed the threshold.** The engine would promote Cathay to L3 on the first processing tick, making the "L2" starting state fictional.

**Options:**
- A) **Intentional**: Cathay is "about to break through" -- R1 engine processes the advancement. Dramatic.
- B) **Bug**: Starting progress should be 0.50 (below 0.60 threshold), giving Cathay 1-2 rounds of genuine L2 status.
- C) **Relabel**: Just start Cathay at L3 with 0.10 progress toward L4.

If (B), the test would show Cathay reaching L3 in R2 instead of R1 -- a minor difference.

### Finding 4: THE GDP GAP CLOSES REGARDLESS OF TECH OUTCOMES

Cathay's GDP ratio improves from 0.679 to 0.819 over 8 rounds. This is entirely driven by the base growth rate differential (4.0% vs 1.8%), amplified equally by the same +15% tech factor on both sides. The tech race does not create GDP divergence.

**Thucydides Trap implication:** The "trap" is economic convergence, not tech divergence. The tech race is a costly sideshow that consumes resources without changing the fundamental power dynamic.

### Finding 5: MIDDLE POWERS BENEFIT MOST FROM THE TECH RACE

Hanguk and Formosa reach AI L3 in R2, gaining the +15% GDP factor and +1 combat bonus. Bharata reaches L3 in R5. These are the meaningful level-up events in the game.

The superpower tech race (both stuck at L3, both chasing L4) is a treadmill. The middle powers' L2->L3 transitions are the actual strategic breakthroughs that change the board.

### Finding 6: NUCLEAR ADVANCEMENT IS TOO SLOW

Cathay starts at Nuclear L2 with 0.80 progress toward L3 (threshold 1.00). Despite investing 6 coins/round, progress is ~0.014/round. Cathay needs ~14 more rounds (R15) to reach Nuclear L3. **Nuclear advancement is irrelevant within 8 rounds.**

This means the nuclear deterrence escalation ladder (L3 = full triad) is largely fixed at starting conditions. No country meaningfully changes nuclear status during the game.

### Finding 7: TECH INVESTMENT IS A RESOURCE TRAP

Columbia spends 18 coins/round on AI tech -- a massive allocation from a ~70 coin discretionary budget. Over 8 rounds, that is 144 coins spent on a capability that never materializes (L4 never reached). Those 144 coins could have:
- Produced ~48 ground units (at 3 coins each)
- Funded social spending to maintain stability
- Funded allies (Heartland, Formosa)

The game design creates a genuine dilemma only if the L4 payoff is achievable. Since it is not, the "optimal" strategy is to stop investing in AI tech once L3 is reached and spend elsewhere. This reduces the tech race to a knowledge problem (do players know L4 is unreachable?) rather than a strategic dilemma.

### Finding 8: FORMOSA SEMICONDUCTOR DISRUPTION IS THE REAL TECH WEAPON

The Formosa Strait scenario branch (R5) shows that blockading Formosa hurts Columbia's GDP growth by ~7.2% while barely denting Cathay (-1.6%). This asymmetric impact (formosa_dep: Columbia 0.65 vs Cathay 0.25) makes the semiconductor chokepoint a far more powerful tech weapon than rare earth restrictions.

**Design implication:** The interesting tech mechanic is not R&D progress penalties -- it is semiconductor supply disruption. The game should steer players toward this realization.

---

## DESIGN RECOMMENDATIONS

### CRITICAL: Recalibrate R&D Progress Formula

The current formula `(investment / GDP) * 0.5` produces ~0.03/round for a superpower investing heavily. The L3->L4 gap is 0.40 (from 0.60 to 1.00). This means ~13 rounds unrestricted, ~24 rounds restricted. Neither is achievable in 8 rounds.

**Option A -- Increase the multiplier:** Change 0.5 to 1.5 or 2.0. This triples/quadruples progress, making L4 achievable in 4-6 rounds (unrestricted) or 7-11 rounds (restricted). The rare earth penalty becomes meaningful because it is the difference between "barely possible" and "impossible."

**Option B -- Lower L4 threshold:** Change L3->L4 from 1.00 to 0.80 or even 0.70. This reduces the gap from 0.40 to 0.20 or 0.10, making L4 reachable in 6-7 rounds (unrestricted) or barely unreachable (restricted). Creates genuine tension.

**Option C -- Increase starting progress:** Start Columbia AI at 0.80 instead of 0.60. Gap to L4 = 0.20. Reachable in ~7 rounds unrestricted, ~12 rounds restricted. Rare earth restriction becomes the difference between "achievable in game" and "not achievable." BEST OPTION for creating meaningful rare earth dilemma.

**Option D -- Investment-based progress (not GDP-scaled):** Use `investment * 0.01` instead of `(investment/GDP)*0.5`. This means 18 coins = 0.18 progress/round. Columbia reaches L4 in ~2 rounds unrestricted, ~4 rounds restricted. Too fast, but shows the scaling issue.

**Recommended: Option C (start at 0.80) combined with modest multiplier increase (0.5 -> 0.8).** This produces:
- Columbia unrestricted: ~0.051/round, L4 in ~4 rounds from 0.80 = achievable R4
- Columbia restricted (x0.55): ~0.028/round, L4 in ~7 rounds from 0.80 = achievable R7-R8 (barely, creating tension)
- Cathay unrestricted: ~0.040/round, L4 from 0.0 in ~25 rounds = not achievable (correct -- Cathay is behind)

This makes rare earth restriction the difference between "easy L4" and "barely possible L4" -- a genuine strategic weapon.

### IMPORTANT: Recalibrate Nuclear R&D Similarly

Nuclear advancement is also too slow. Cathay needs ~14 rounds to go from L2 to L3 with 6 coins/round investment. Either increase the multiplier or lower thresholds. Nuclear L3 (full triad) should be achievable within 8 rounds for a country that dedicates serious resources to it.

### MODERATE: Fix Cathay Starting AI Progress

Cathay's AI progress (0.70) exceeds the L2->L3 threshold (0.60). Either:
- Start Cathay at L3 with 0.10 progress (transparent)
- Lower starting progress to 0.50 (gives Cathay a 1-2 round L2 window where Columbia's L3 advantage matters)

Recommend the latter (0.50 start) -- it creates 1-2 rounds of genuine tech asymmetry early in the game.

### MODERATE: Make Rare Earth Restrictions Affect Existing Tech (Not Just R&D)

Currently, rare earth restrictions only slow *future* R&D. They do not degrade existing capabilities. Consider adding:
- **Maintenance penalty:** Existing AI systems degrade without rare earth supply. AI tech factor reduced by (restriction_level * 0.03) per round while restricted. At Level 3, Columbia's L3 tech factor drops from 1.15 to 1.15 - 0.09 = 1.06 per round of sustained restriction. This creates urgency to resolve the restriction.
- **Stockpile mechanic:** Countries have 2-3 rounds of rare earth reserves. Restriction has no effect for 2 rounds, then bites hard. Creates a window for diplomacy.

### LOW: Consider Tech Espionage

The test reveals that both superpowers grind toward L4 in parallel. A tech espionage mechanic (steal progress, copy breakthroughs, sabotage rival R&D) would add player agency to a currently formulaic process.

---

## VERDICT

**Tech race as designed: NEEDS RECALIBRATION.**

The core issue is that R&D progress is too slow relative to game length. No country changes AI level during the superpower race (both stay L3). The rare earth restriction is strategically meaningless because it slows progress toward an unreachable goal. The interesting tech dynamics are:
1. Middle powers reaching L3 (Hanguk, Formosa, Bharata) -- these are the real breakthroughs
2. Semiconductor supply disruption via Formosa -- far more impactful than rare earth R&D penalties
3. Investment opportunity cost -- 144 coins spent on unreachable tech vs military/social spending

**With recalibration (Option C + multiplier increase), the tech race becomes genuinely compelling:** Columbia can reach L4 in ~4 rounds unrestricted but ~8 rounds restricted. The rare earth restriction becomes the strategic fulcrum -- Cathay can delay Columbia's breakthrough by 4 rounds, during which the GDP gap closes. This is the Thucydides Trap tech race we want.

---

*Test completed by TESTER-ORCHESTRATOR. Results written for ATLAS (recalibration), SIMON (design implications), and VERA (consistency check).*
