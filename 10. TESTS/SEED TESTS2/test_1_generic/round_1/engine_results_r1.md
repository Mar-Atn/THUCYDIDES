# ROUND 1 — ENGINE PROCESSING RESULTS
## Test 1: Generic Baseline

---

## LIVE ACTION RESOLUTION (Phase A)

### 1. Gulf Gate Assault (Columbia vs Persia)
**Columbia commits:** 1 naval + 1 ground from ME theater
**Persia defends:** 1 ground + 1 tac air at cp_gulf_gate + mines at 75%

**Resolution (RISK dice + modifiers):**
- Columbia: 2 units attacking. Attacker dice: 1d6 per unit pair.
- Persia: 2 units defending (1 ground + 1 tac air). Defender wins ties.
- Modifiers: Columbia tech bonus +1 (AI L3). Persia terrain defense +0.5 (fortified chokepoint). Mine hazard: -0.5 to naval attacker.
- Columbia effective: 2 units, modifier net +0.0 (tech +1, mines -0.5, no terrain)
- Persia effective: 2 units, modifier +0.5 (terrain)

**Dice rolls (simulated, seed 100):**
- Pair 1 (Columbia ground vs Persia ground): Columbia 4+0.0=4.0 vs Persia 3+0.5=3.5 → Columbia wins. Persia loses 1 ground.
- Pair 2 (Columbia naval vs Persia tac air): Columbia 2+0.0=2.0 vs Persia 5+0.5=5.5 → Persia wins. Columbia loses 1 naval.

**Result: PARTIAL SUCCESS.** Columbia destroys Persia's ground unit at Gulf Gate but loses 1 naval unit. Persia still has 1 tac air (anti-ship missiles) at the chokepoint. **Blockade PARTIALLY BROKEN** — ground component eliminated but air/missile threat remains. Oil disruption reduced from +80% to +40% (missiles still threaten shipping but ground batteries gone).

**Casualties:** Columbia -1 naval (total: 9). Persia -1 ground at Gulf Gate (total ground: 7).
**War tiredness:** Columbia +0.15, Persia +0.20 (defender).

### 2. Donetsk Concentration Offensive (Nordostan)
**Nordostan:** 12 ground + 4 tac air concentrated on Donetsk axis
**Heartland defense:** 7 ground + 2 tac air on front line

**Resolution:**
- Nordostan attacks with local superiority (~1.7:1 ratio)
- Modifiers: Nordostan tech +0 (AI L1). Heartland terrain +0.5 (defending home). Choson support +0.5 (2 units rear security enabling concentration).
- Heartland drone logistics strikes: -0.3 modifier to Nordostan supply lines

**Dice rolls (simulated):**
- 5 unit-pair engagements on Donetsk axis
- Nordostan wins 3, Heartland wins 2 (concentration advantage partially offset by defense)
- Nordostan loses 1 ground. Heartland loses 2 ground.

**Result: NORDOSTAN ADVANCES.** Gains 1 additional theater hex (heartland_15 occupied). Heartland front line pushed back slightly. No strategic breakthrough — grinding advance as designed.

**Casualties:** Nordostan -1 ground (12→11 on front). Heartland -2 ground (7→5 on front, 3 reserve).
**War tiredness:** Both +0.15/0.20.

### 3. Choson ICBM Launch Over Yamato
**Resolution:** Hwasong-type ICBM launched, overflies Yamato, splashes in Pacific.
- **Global alert triggered.** All countries notified.
- **No interception attempted** (not a strike, just a test/provocation).
- **Yamato:** Stability -0.3 (security shock). Political support shift (rally effect short-term but anxiety long-term).
- **Hanguk:** Stability -0.2 (DMZ anxiety).
- **Columbia:** Forced to acknowledge Pacific theater while managing Gulf Gate + Persia.
- **Cathay:** No comment publicly. Privately signals Choson restraint.

### 4. Persia Missile Strikes on Solaria/Mirage
**Resolution:** Continued ballistic missile + drone barrages.
- Solaria: 2 AD units intercept ~70% of incoming. Infrastructure damage: -0.3 coins equivalent. Stability -0.2.
- Mirage: 2 AD units intercept ~75%. Financial district near-miss. Stability -0.3. Capital flight trigger check: stability still 7.7 → no capital flight.

### 5. Levantia Operations Against Hezbollah
**Resolution:** 2 ground units in Lebanon theater continue degradation.
- Hezbollah degraded by ~20% this round. No Persia resupply possible (corridor collapsed).
- Levantia: war tiredness +0.10.

### 6. Covert Operations
| Op | Success (dice) | Detection | Effect |
|----|-------|-----------|--------|
| DESERT MIRROR (Columbia→Persia) | 4/6 = SUCCESS | Not detected | Identifies 2 potential defectors in IRGC mid-ranks |
| JADE CURTAIN (Columbia→Cathay) | 3/6 = SUCCESS | Not detected | Updated Formosa invasion timeline: R3-R5 window confirmed |
| TROPIC STORM (Columbia→Caribe) | 2/6 = FAIL | Detected | Caribe security arrests 2 exile network contacts. Columbia embarrassment. |
| CHECKPOINT (Columbia sweep) | 5/6 = SUCCESS | N/A | Identifies 3 sanctions evasion networks through Mirage |
| Cathay cyber recon (→Columbia Pacific) | 4/6 = SUCCESS | Not detected | Maps 2 Columbia submarine patrol routes near Formosa |

---

## TRANSACTIONS PROCESSED

| Transaction | Status | Effect |
|-------------|--------|--------|
| Columbia → Heartland: 3 coins military aid | EXECUTED | Heartland treasury +3 (→4 before maintenance) |
| Columbia → Formosa: 1 coin security package | EXECUTED | Formosa treasury +1 (→9) |
| Cathay → Nordostan: expanded energy at 15% discount | EXECUTED | Nordostan revenue +1.5 coins (energy sales). Cathay costs +2 coins. |
| Cathay → Ponte: 3 coins BRI infrastructure | EXECUTED | Ponte treasury +3 (→7). Cathay treasury -3. |
| IRGC → Persia state: 1.8 coins | INTERNAL | Deficit covered. Anvil's reserves: 5→3.2. |
| Nordostan ↔ Choson: tech for troops | EXECUTED | Choson gains nuclear sub components. Nordostan gains 2 ground units (3rd wave, arrive R2). |

---

## WORLD MODEL ENGINE — BATCH PROCESSING

### Oil Price Calculation
```
base = $80
supply_factor = 1.0 - 0.06 (Nordostan HIGH) = 0.94
sanctions_supply_hit = 0.08 × 2 = 0.16
final_supply = max(0.5, 0.94 - 0.16) = 0.78
disruption = 1.0 + 0.40 (Gulf Gate PARTIAL — reduced from 0.80) = 1.40
war_premium = min(0.30, 0.10 × 2) = 0.20
demand_factor = 1.0 + (2.0 - 2.0) × 0.05 = 1.0
speculation = 1.0 + 0.05 × 3 = 1.15

OIL PRICE = 80 × (1.0/0.78) × 1.40 × 1.20 × 1.15
         = 80 × 1.282 × 1.40 × 1.20 × 1.15
         = 80 × 2.478
         = $198/barrel
```
**Oil price R1: $198** (down from $237 starting due to partial Gulf Gate breach + Nordostan flooding market)

### Oil Revenue to Producers
- Solaria: $198 × oil_share × GDP factor = +2.1 coins revenue boost
- Nordostan: $198 × HIGH production = +1.8 coins (partially offset by discount)
- Mirage: +0.8 coins
- Persia: Minimal (war-disrupted exports, mostly smuggling)

### GDP Growth Calculations (Key Countries)

**Columbia:** base 1.8% × tariff(0.97) × sanctions_cost(0.99) × war(0.98) × tech(1.15) × inflation(0.995) × blockade(0.92) × semiconductor(1.0) = 1.8% × 1.005 = **1.81%**
New GDP: 280 × 1.0181 = **285.1**

**Cathay:** base 4.0% × tariff(0.96) × rare_earth_self(1.0) × tech(1.05) × inflation(1.0) × semiconductor(0.975) = 4.0% × 0.983 = **3.93%**
New GDP: 190 × 1.0393 = **197.5** (+1 naval produced = 7 total)

**Nordostan:** base 1.0% × sanctions(0.85) × war(0.92) × tech(1.0) × inflation(0.96) = 1.0% × 0.745 = **0.75%**
New GDP: 20 × 1.0075 = **20.15** (Treasury: 6 → ~0 after deficit)

**Heartland:** base 2.5% × war(0.90) × sanctions_on_nordostan_benefit(1.0) × aid_boost(1.05) = 2.5% × 0.945 = **2.36%**
New GDP: 2.2 × 1.0236 = **2.25** (Treasury: 1 + 3 aid - maintenance = ~2)

**Persia:** base -3.0% × war(0.85) × sanctions(0.80) × blockade(0.90) = -3.0% × 0.612 = **-1.84%** (contraction slowed by oil revenue at high prices)
New GDP: 5 × 0.9816 = **4.91**

### Stability Updates

```
STABILITY FORMULA: old + delta (war friction + economic + democratic resilience + autocracy resilience)
```

| Country | Old | War Friction | Economic | Dem. Resilience | Autocracy | Other | New | Change |
|---------|-----|-------------|----------|-----------------|-----------|-------|-----|--------|
| Columbia | 7.0 | -0.05 (allied) | +0.0 | — | — | — | **6.95** | -0.05 |
| Cathay | 8.0 | 0 | +0.05 | — | — | — | **8.05** | +0.05 |
| Nordostan | 5.0 | -0.08 (attacker) | -0.05 | — | ×0.75 = -0.10 | — | **4.90** | -0.10 |
| Heartland | 5.0 | -0.10 (defender) | -0.03 | +0.15 | — | territory -0.4 | **4.62** | -0.38 |
| Persia | 4.0 | -0.10 (defender) | -0.10 | — | — | fatwa rally +0.1 | **3.90** | -0.10 |
| Yamato | 8.0 | 0 | +0.0 | — | — | ICBM shock -0.3 | **7.70** | -0.30 |
| Solaria | 7.0 | -0.05 (under attack) | +0.10 (oil revenue) | — | ×0.75 | — | **7.04** | +0.04 |
| Mirage | 8.0 | -0.05 (under attack) | +0.05 | — | ×0.75 | — | **8.00** | 0.00 |
| Hanguk | 6.0 | 0 | +0.0 | — | — | ICBM anxiety -0.2 | **5.80** | -0.20 |
| Caribe | 3.0 | 0 | -0.20 (blockade) | — | ×0.75 | — | **2.85** | -0.15 |
| Formosa | 7.0 | 0 | +0.0 | — | — | naval encirclement -0.1 | **6.90** | -0.10 |
| Phrygia | 5.0 | 0 | -0.10 (inflation) | — | — | — | **4.90** | -0.10 |

### Political Support Updates
| Country | Old | Change | New | Notes |
|---------|-----|--------|-----|-------|
| Columbia | 38% | -1.0 (war, oil prices, overstretch) | **37%** | Tribune investigation gaining traction |
| Cathay | 58% | +0.5 (stability, growth) | **58.5%** | Steady |
| Nordostan | 55% | -1.0 (war tiredness) | **54%** | Pathfinder's narrative holds |
| Heartland | 52% | -2.0 (territory lost, casualties) | **50%** | Beacon vulnerable |
| Persia | 40% | -1.5 (war damage, economy) | **38.5%** | Dawn's support rising |

### Technology Advancement
| Country | Nuclear | AI | Progress |
|---------|---------|-----|---------|
| Columbia | L3 (complete) | L3, 60%→65% toward L4 | +5% (18 coins tech budget) |
| Cathay | L2, 80%→85% toward L3 | L2, 70%→76% toward L3 | +5/6% (12 coins tech) |
| Persia | L0, 60% (NO advancement — 0 investment) | L0 | Stalled |
| Formosa | L0 | L2, 50%→52% | Slow |
| Yamato | L0, 10%→11% | L3, 30%→34% | Moderate |

### Cathay Naval Production
- +1 naval unit produced (strategic_missile_growth = 1 for naval equivalent)
- Cathay naval: 6 → **7**

---

## ROUND 1 FINAL STATE

| Country | GDP | Stability | Support | Treasury | Naval | Key Event |
|---------|-----|-----------|---------|----------|-------|-----------|
| Columbia | 285.1 | 6.95 | 37% | ~42 | **9** (-1 Gulf Gate) | Gulf Gate partial breach |
| Cathay | 197.5 | 8.05 | 58.5% | ~40 | **7** (+1 produced) | All 7 ships near Formosa |
| Nordostan | 20.15 | 4.90 | 54% | **~0** | 2 | Donetsk advance, treasury empty |
| Heartland | 2.25 | 4.62 | 50% | ~2 | 0 | Lost 2 ground + 1 hex |
| Persia | 4.91 | 3.90 | 38.5% | ~0 | 0 | Gulf Gate ground unit lost, fatwa issued |
| Gallia | 34.3 | 7.0 | 40% | ~7 | 1 | Mediation initiative launched |
| Teutonia | 45.5 | 7.0 | 45% | ~10 | 0 | Energy crisis management |
| Yamato | 43.4 | 7.70 | 48% | ~13 | 2 | ICBM shock, remilitarization |
| Solaria | 13.1 | 7.04 | 65% | ~22 | 0 | Oil revenue bonanza |
| Choson | 0.3 | 3.9 | 70% | ~1 | 0 | ICBM launched, 3rd wave deployed |
| Caribe | 1.98 | 2.85 | 44% | ~0.5 | 0 | Grid collapse continuing |
| Formosa | 8.24 | 6.90 | 55% | ~9 | 0 | Encirclement deepening |

**Oil Price End R1: $198/barrel**
**Gap Ratio (Cathay/Columbia GDP): 197.5/285.1 = 0.693** (was 0.679 — closing)
**Naval Ratio: 7/9 = 0.778** (was 0.60 — closing fast due to Columbia loss + Cathay production)
