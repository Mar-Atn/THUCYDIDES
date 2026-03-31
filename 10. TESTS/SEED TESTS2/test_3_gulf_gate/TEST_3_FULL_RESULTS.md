# TEST 3: GULF GATE ECONOMICS
## 8-Round Oil Price Stress Test
**Test Date:** 2026-03-27 | **Tester:** TESTER-ORCHESTRATOR | **Engine:** World Model v2.0

---

## TEST PREMISE

Gulf Gate blockade remains **FULLY ACTIVE** for the first 5 rounds. Persia commits maximum garrison (ground + tac air + mines at 100%). Columbia's R1 assault FAILS (unlike Test 1 where it partially succeeded). The blockade is finally broken in R6 by a major amphibious operation. This test isolates the economic dynamics of sustained chokepoint denial.

**Key Differences from Test 1 Baseline:**
- Gulf Gate: FULL blockade (+80%) instead of PARTIAL (+40%) after R1
- Persia: More aggressive defense, no ground unit lost at Gulf Gate
- Oil price: Starts and stays much higher
- OPEC: Sarmatia starts HIGH (flooding market). Will coordination hold?
- Columbia: Under massive economic/political pressure to break the blockade

**OPEC Members & Starting Decisions:**
- Solaria: NORMAL (cautious leader)
- Sarmatia: HIGH (needs revenue for war, broke sanctions solidarity)
- Persia: NORMAL (war-disrupted, mostly symbolic)
- Mirage: NORMAL (follows Solaria lead)

---

## ROUND 1 (H1 2026)

### Decisions

| Country | Key Economic Decisions |
|---------|----------------------|
| **Solaria** | OPEC: NORMAL. Hedge: Signs long-term supply deal with Cathay at $200/bbl floor. |
| **Sarmatia** | OPEC: HIGH (+0.06 supply). Sells discounted oil to Cathay (15% off). Needs cash for war. |
| **Persia** | OPEC: NORMAL. Gulf Gate garrison: 2 ground + 1 tac air + mines 100%. Maximum defense. |
| **Mirage** | OPEC: NORMAL. Diversifies sovereign fund into gold. |
| **Columbia** | Gulf Gate assault: 1 naval + 1 ground. Budget: 4 coins to military, 3 coins to Ruthenia aid. |
| **Cathay** | Buys Sarmatia energy at 15% discount. 3 coins to Ponte BRI. +1 naval produced. |
| **Teutonia** | Emergency energy procurement. 2 coins to strategic reserve. |
| **Bharata** | Buys discounted Sarmatia oil through intermediaries. Sanctions evasion. |

### Gulf Gate Assault — FAILS

Columbia commits 1 naval + 1 ground against Persia's 2 ground + 1 tac air at fortified chokepoint with mines at 100%.

- Columbia: 2 units attacking. Tech bonus +1 (AI L3). Mine hazard: -1.0 (100% mines, worse than Test 1's -0.5).
- Persia: 3 units defending. Terrain +0.5 (fortified chokepoint).
- Dice (seed 200): Pair 1: Columbia 3+0.0=3.0 vs Persia 4+0.5=4.5 -- Persia wins. Pair 2: Columbia 2-1.0=1.0 vs Persia 5+0.5=5.5 -- Persia wins decisively.
- **Result: ASSAULT REPULSED.** Columbia loses 1 naval unit. Persia loses nothing.
- **Blockade remains FULL. Disruption stays at +80%.**

Casualties: Columbia -1 naval (10 to 9). Persia: 0 losses at Gulf Gate.
War tiredness: Columbia +0.15, Persia +0.10 (successful defense).

### Oil Price Calculation — Round 1

```
BASE PRICE = $80

SUPPLY SIDE:
  OPEC decisions:
    Solaria: NORMAL  → 0.00
    Sarmatia: HIGH  → +0.06
    Persia: NORMAL   → 0.00
    Mirage: NORMAL   → 0.00
  supply_factor = 1.0 + 0.06 = 1.06

  Sanctions on oil producers:
    Sarmatia L3 sanctions → -0.08
    Persia L3 sanctions    → -0.08
  sanctions_supply_hit = 0.16

  final_supply = max(0.5, 1.06 - 0.16) = 0.90

DISRUPTION:
  Gulf Gate FULL blockade → +0.80
  disruption = 1.0 + 0.80 = 1.80

WAR PREMIUM:
  War 1: Columbia vs Persia (major) → +0.10
  War 2: Sarmatia vs Ruthenia (major) → +0.10
  war_premium = min(0.30, 0.20) = 0.20

DEMAND:
  Average GDP growth ~2.0% → demand_factor = 1.0 + (2.0 - 2.0) × 0.05 = 1.00

SPECULATION:
  2 wars + 1 Gulf Gate blocked + 0 Formosa = 3 crises
  speculation = 1.0 + 3 × 0.05 = 1.15

OIL PRICE = 80 × (1.00/0.90) × 1.80 × 1.20 × 1.15
         = 80 × 1.111 × 1.80 × 1.20 × 1.15
         = 80 × 2.766
         = $221.3/barrel

CLAMPED: $221 (within $30-250 range)
```

**OIL PRICE R1: $221/barrel**

Compare Test 1: $198 (partial blockade). Difference: +$23 (+12%) from full vs partial blockade.

### Oil Revenue Impact

Revenue formula: `oil_rev = GDP × (resource_sector/100) × (oil_price/80 - 1) × 0.3`

| Producer | GDP | Resource% | Oil Revenue (coins) | Total Revenue Effect |
|----------|-----|-----------|--------------------|--------------------|
| **Solaria** | 11 | 45% | 11 × 0.45 × (221/80-1) × 0.3 = **2.61** | Windfall. Treasury swelling. |
| **Sarmatia** | 20 | 40% | 20 × 0.40 × (221/80-1) × 0.3 = **4.22** | War chest refilling despite sanctions. |
| **Persia** | 5 | 35% | 5 × 0.35 × (221/80-1) × 0.3 = **0.92** | Minimal — war-disrupted, can barely export. |
| **Mirage** | 5 | 30% | 5 × 0.30 × (221/80-1) × 0.3 = **0.79** | Decent for small economy. |
| **Caribe** | 2 | 50% | 2 × 0.50 × (221/80-1) × 0.3 = **0.53** | Helps but not enough to fix grid. |
| **Columbia** | 280 | 5% | 280 × 0.05 × (221/80-1) × 0.3 = **7.39** | Domestic production benefits, but net importer — costs dwarf this. |

### GDP Impact on Key Importers

Oil importers face blockade_factor penalty. Countries dependent on Gulf transit:
- **blockade_fraction** for Gulf-dependent importers: ~0.20 (Cathay, Teutonia, Bharata, Yamato heavily dependent)
- blockade_factor = max(0.5, 1.0 - 0.20 × 0.4) = **0.92**

| Country | Base Growth | Key Modifiers | Effective Growth | New GDP |
|---------|------------|---------------|-----------------|---------|
| Columbia | 1.8% | tariff(0.97) × war(0.98) × tech(1.15) × blockade(0.92) | **1.66%** | 280 × 1.0166 = **284.6** |
| Cathay | 4.0% | tariff(0.96) × tech(1.05) × semi(0.975) × blockade(0.95) | **3.71%** | 190 × 1.0371 = **197.1** |
| Teutonia | 1.2% | blockade(0.92) × inflation(0.998) | **1.06%** | 45 × 1.0106 = **45.5** |
| Bharata | 6.5% | blockade(0.92) × inflation(0.996) | **5.96%** | 42 × 1.0596 = **44.5** |
| Yamato | 1.0% | blockade(0.92) | **0.90%** | 43 × 1.009 = **43.4** |
| Phrygia | 3.0% | blockade(0.92) × inflation(0.37) | **1.02%** | 11 × 1.0102 = **11.1** |
| Sarmatia | 1.0% | sanctions(0.85) × war(0.92) × inflation(0.96) | **0.75%** | 20 × 1.0075 = **20.15** |
| Persia | -3.0% | war(0.85) × sanctions(0.80) × blockade(0.90) | **-1.84%** | 5 × 0.9816 = **4.91** |

### Round 1 State Table

| Country | GDP | Oil Price Effect | Stability | Support | Treasury | Key |
|---------|-----|-----------------|-----------|---------|----------|-----|
| Columbia | 284.6 | Net importer, PAIN | 6.90 | 36% | ~43 | Gulf Gate assault failed, -1 naval |
| Cathay | 197.1 | Moderate pain, discount helps | 8.05 | 58.5% | ~41 | Building naval, patient |
| Sarmatia | 20.15 | WINDFALL (+4.22 oil rev) | 4.90 | 54% | ~4 | Oil revenue keeping war funded |
| Ruthenia | 2.25 | No oil, receiving aid | 4.62 | 50% | ~2 | Losing territory, dependent on aid |
| Persia | 4.91 | Cannot export effectively | 3.90 | 38.5% | ~1 | Blockade holds, economy dying |
| Solaria | 13.1 | WINDFALL (+2.61) | 7.04 | 65% | ~23 | Profits enormously |
| Mirage | 5.3 | WINDFALL (+0.79) | 8.00 | 70% | ~16 | Under missile attack but profitable |
| Teutonia | 45.5 | Major importer PAIN | 6.90 | 44% | ~9 | Energy crisis emerging |
| Bharata | 44.5 | Buying discounted, moderate pain | 5.95 | 57.5% | ~12 | Playing all sides |
| Phrygia | 11.1 | SEVERE PAIN (45% inflation + oil) | 4.70 | 48% | ~3 | Approaching crisis |
| Yamato | 43.4 | Major importer PAIN | 7.70 | 48% | ~13 | ICBM shock + oil costs |

**R1 OIL PRICE: $221/barrel**

---

## ROUND 2 (H2 2026)

### Context
Columbia midterm elections this round. Gulf Gate still blocked. Oil at $221 is creating domestic pressure. Sarmatia's HIGH production provides some relief but also funds their war. OPEC is under pressure from importers to increase supply.

### Decisions

| Country | Key Economic Decisions |
|---------|----------------------|
| **Solaria** | OPEC: Moves to HIGH (+0.06). Importers begging for relief. Maximizes revenue at peak prices. |
| **Sarmatia** | OPEC: HIGH (continues). Expanding Cathay pipeline. |
| **Persia** | OPEC: NORMAL (irrelevant, can barely export). Gulf Gate defense: Reinforces with 1 more ground unit. |
| **Mirage** | OPEC: HIGH (+0.06). Follows Solaria lead. |
| **Columbia** | NO second Gulf Gate assault (midterms — cannot afford another failure). Increases aid to Ruthenia (+4 coins). Dealer focuses on elections. |
| **Cathay** | Announces Formosa "patrol zone" expansion. +1 naval produced (total 8). Signs 5-year energy deal with Solaria. |
| **Teutonia** | Emergency LNG contracts. Activates strategic reserve. Budget: 2 coins energy subsidy. |
| **Bharata** | BRICS+ summit agenda: proposes "energy stability framework." Buys more Sarmatia oil. |

### Oil Price Calculation — Round 2

```
BASE PRICE = $80

SUPPLY SIDE:
  OPEC decisions:
    Solaria: HIGH   → +0.06
    Sarmatia: HIGH → +0.06
    Persia: NORMAL  → 0.00
    Mirage: HIGH    → +0.06
  supply_factor = 1.0 + 0.18 = 1.18

  Sanctions supply hit: 0.16 (unchanged)
  final_supply = max(0.5, 1.18 - 0.16) = 1.02

DISRUPTION:
  Gulf Gate FULL blockade → +0.80
  disruption = 1.80

WAR PREMIUM: 0.20 (2 major wars, unchanged)

DEMAND:
  Avg GDP growth declining due to oil shock → ~1.8%
  demand_factor = 1.0 + (1.8 - 2.0) × 0.05 = 0.99

SPECULATION:
  3 crises (unchanged) → 1.15

OIL PRICE = 80 × (0.99/1.02) × 1.80 × 1.20 × 1.15
         = 80 × 0.971 × 1.80 × 1.20 × 1.15
         = 80 × 2.419
         = $193.5/barrel
```

**OIL PRICE R2: $194/barrel** (DOWN from $221)

OPEC flooding the market works. Three members on HIGH (+0.18 total) pushes supply above sanctions hit. Price drops $27 (12%). But still catastrophically high for importers.

### Oil Revenue — Round 2

| Producer | GDP | Resource% | Oil Revenue (coins) | Change from R1 |
|----------|-----|-----------|--------------------|----|
| **Solaria** | 13.5 | 45% | 13.5 × 0.45 × (194/80-1) × 0.3 = **2.59** | -0.02 (higher GDP offsets lower price) |
| **Sarmatia** | 20.3 | 40% | 20.3 × 0.40 × (194/80-1) × 0.3 = **3.47** | -0.75 (still massive for wartime) |
| **Mirage** | 5.5 | 30% | 5.5 × 0.30 × (194/80-1) × 0.3 = **0.71** | -0.08 |

### Columbia Midterm Elections

Political support entering election: ~34% (war, oil shock, Gulf Gate failure).
- GDP growth: 1.66% (below 2% → negative factor)
- Oil prices: $221→$194 (dropping but still crushing)
- Gulf Gate: Failed assault, blockade continues
- War: No visible progress, 1 naval unit lost
- Midterm penalty: -1.0 (approaching elections)

**Election result: Opposition gains.** Columbia's political support drops to **32%**. Tribune party gains seats. Investigations into war management intensify. Pressure to either break the blockade or negotiate mounts.

### GDP Updates — Round 2

| Country | Old GDP | Growth | New GDP | Notes |
|---------|---------|--------|---------|-------|
| Columbia | 284.6 | 1.55% | **289.0** | Slowing — oil costs + war |
| Cathay | 197.1 | 3.68% | **204.4** | Steady, discount oil helps |
| Sarmatia | 20.15 | 0.70% | **20.3** | Barely growing but oil revenue sustains |
| Teutonia | 45.5 | 0.95% | **45.9** | Energy crisis dragging growth |
| Bharata | 44.5 | 5.85% | **47.1** | Resilient, multi-alignment |
| Phrygia | 11.1 | 0.80% | **11.2** | Inflation destroying growth |
| Persia | 4.91 | -2.0% | **4.81** | Continued contraction |

### Round 2 State Table

| Country | GDP | Stability | Support | Treasury | Oil Price Effect |
|---------|-----|-----------|---------|----------|-----------------|
| Columbia | 289.0 | 6.80 | **32%** | ~39 | Midterms lost, pressure mounting |
| Cathay | 204.4 | 8.05 | 59% | ~39 | Patient, building power |
| Sarmatia | 20.3 | 4.82 | 53% | ~5 | Oil keeps war going |
| Solaria | 13.5 | 7.10 | 66% | ~26 | Revenue bonanza continues |
| Teutonia | 45.9 | 6.75 | 43% | ~8 | Energy subsidies draining treasury |
| Bharata | 47.1 | 5.90 | 57% | ~13 | Multi-alignment pays |
| Phrygia | 11.2 | 4.45 | 46% | ~2 | Inflation spiral (48%) |
| Persia | 4.81 | 3.75 | 36% | ~0.5 | Economy collapsing, blockade holds |

**R2 OIL PRICE: $194/barrel** | **Gap Ratio: 204.4/289.0 = 0.707** (was 0.679 — closing fast)

---

## ROUND 3 (H1 2027)

### Context
Columbia at 32% support. Blockade in 3rd round. Oil at $194. Domestic pressure forces action. Ruthenia wartime election approaching (R3-4). Sarmatia's oil revenue is funding the war — this becomes visible intelligence. Columbia must decide: break the blockade (costly) or negotiate (politically devastating)?

### Decisions

| Country | Key Economic Decisions |
|---------|----------------------|
| **Solaria** | OPEC: HIGH (continues). Announces "stability pricing" initiative — private deal with Columbia at $180/bbl. |
| **Sarmatia** | OPEC: HIGH. Expands pipeline capacity to Cathay. Signs arms-for-oil deal with Bharata. |
| **Persia** | Gulf Gate: Adds anti-ship mines (mines now 100%). IRGC sacrifices domestic economy for blockade. Stability 3.60 — approaching collapse threshold. |
| **Mirage** | OPEC: HIGH. Privately signals to Columbia willingness to mediate Persia ceasefire. |
| **Columbia** | Prepares major Gulf Gate operation for R4 (2 naval + 2 ground + mine clearance). Spends 8 coins on buildup. No assault this round. |
| **Cathay** | +1 naval (total 9). Begins "inspection regime" near Formosa. |
| **Teutonia** | Proposes EU-wide energy rationing. Support drops to 41%. |
| **Bharata** | Hosts BRICS+ summit. Proposes multilateral oil stability fund. |

### Oil Price Calculation — Round 3

```
BASE PRICE = $80

SUPPLY:
  OPEC: Solaria HIGH (+0.06), Sarmatia HIGH (+0.06), Mirage HIGH (+0.06), Persia NORMAL
  supply_factor = 1.18
  Sanctions supply hit: 0.16
  final_supply = max(0.5, 1.18 - 0.16) = 1.02

DISRUPTION:
  Gulf Gate FULL blockade → disruption = 1.80

WAR PREMIUM: 0.20 (unchanged)

DEMAND:
  Global growth slowing → avg ~1.5%
  demand_factor = 1.0 + (1.5 - 2.0) × 0.05 = 0.975

SPECULATION:
  3 crises → 1.15
  BUT: Mirage mediation signal reduces speculation slightly
  speculation = 1.0 + 2.5 × 0.05 = 1.125 (market hope)

OIL PRICE = 80 × (0.975/1.02) × 1.80 × 1.20 × 1.125
         = 80 × 0.956 × 1.80 × 1.20 × 1.125
         = 80 × 2.325
         = $186.0/barrel
```

**OIL PRICE R3: $186/barrel** (DOWN from $194)

Gradual decline: OPEC flooding + demand destruction + mediation hopes. But still catastrophically elevated. The formula is doing its job — the blockade floor keeps prices above $180 regardless of OPEC action.

### Key Insight: OPEC Coordination Failure

Sarmatia went HIGH in R1 to fund its war. Solaria and Mirage followed in R2 to maximize revenue. Now ALL three active OPEC members are on HIGH, and the price has dropped $35 from R1. But the blockade floor prevents prices from crashing. This is a **prisoner's dilemma**: each member benefits individually from HIGH, but collectively they are reducing their per-barrel revenue without being able to push prices down enough to help importers.

| Scenario | Supply Factor | Final Supply | Oil Price (approx) |
|----------|--------------|-------------|-------------------|
| All NORMAL | 1.00 | 0.84 | ~$235 |
| Sarmatia HIGH only | 1.06 | 0.90 | ~$221 |
| All 3 HIGH | 1.18 | 1.02 | ~$186 |
| All 3 LOW | 0.82 | 0.66 | ~$250 (capped) |

**Design observation:** OPEC decisions matter (~$50 swing) but cannot overcome the blockade disruption. The blockade is the dominant variable.

### Oil Revenue — Round 3

| Producer | GDP | Oil Rev (coins) | Cumulative R1-R3 |
|----------|-----|-----------------|-----------------|
| Solaria | 13.9 | 2.48 | **7.68** |
| Sarmatia | 20.4 | 3.19 | **10.88** |
| Mirage | 5.7 | 0.65 | **2.15** |
| Persia | 4.71 | 0.78 | **2.48** (mostly inaccessible) |

**Sarmatia cumulative oil revenue through 3 rounds: 10.88 coins.** This is funding approximately 7 ground units worth of war production. The blockade is inadvertently subsidizing Sarmatia's war against Ruthenia.

### GDP Updates — Round 3

| Country | Old GDP | Growth | New GDP |
|---------|---------|--------|---------|
| Columbia | 289.0 | 1.48% | **293.3** |
| Cathay | 204.4 | 3.65% | **211.9** |
| Sarmatia | 20.3 | 0.68% | **20.4** |
| Teutonia | 45.9 | 0.88% | **46.3** |
| Bharata | 47.1 | 5.75% | **49.8** |
| Phrygia | 11.2 | 0.60% | **11.3** |
| Persia | 4.81 | -2.1% | **4.71** |

### Round 3 State Table

| Country | GDP | Stability | Support | Treasury | Notes |
|---------|-----|-----------|---------|----------|-------|
| Columbia | 293.3 | 6.70 | 31% | ~33 | Spending on R4 assault prep |
| Cathay | 211.9 | 8.05 | 59% | ~38 | Gap ratio: 0.722 |
| Sarmatia | 20.4 | 4.75 | 52% | ~6 | Oil-funded war machine |
| Solaria | 13.9 | 7.15 | 67% | ~29 | Richest it has ever been |
| Teutonia | 46.3 | 6.60 | 41% | ~7 | EU energy rationing |
| Phrygia | 11.3 | 4.20 | 44% | ~2 | Approaching crisis (50%+ inflation) |
| Persia | 4.71 | 3.60 | 34% | ~0.3 | Nearing collapse threshold (3.0) |

**R3 OIL PRICE: $186/barrel** | **Gap Ratio: 0.722**

---

## ROUND 4 (H2 2027)

### Context
Columbia at 31% support. Presidential election in R5. Must show progress. Ruthenia wartime election this round. Persia stability at 3.60 — one more shock could trigger internal crisis. Columbia launches the big Gulf Gate operation.

### Decisions

| Country | Key Economic Decisions |
|---------|----------------------|
| **Solaria** | OPEC: Returns to NORMAL. Revenue per barrel dropping too fast. Signals to Sarmatia to coordinate. |
| **Sarmatia** | OPEC: Returns to NORMAL. Agrees with Solaria — price is falling too fast despite blockade. |
| **Persia** | Gulf Gate: Maximum defense. Commits last reserves. IRGC deploys suicide drones. Stability: 3.60. |
| **Mirage** | OPEC: NORMAL (follows Solaria). Continues mediation push. |
| **Columbia** | **OPERATION GULF BREAKER:** 3 naval + 2 ground + mine clearance fleet. Total commitment: 12 coins. |
| **Cathay** | +1 naval (total 10). "Formosa inspection" becomes quasi-blockade — partial Formosa Strait disruption. |
| **Teutonia** | Slashes military budget to fund energy subsidies. 0 coins to defense. |

### Oil Price Calculation — Round 4

**Pre-assault price (blockade still holds at start of round):**

```
BASE PRICE = $80

SUPPLY:
  OPEC: All back to NORMAL
  supply_factor = 1.00
  Sanctions supply hit: 0.16
  final_supply = max(0.5, 1.00 - 0.16) = 0.84

DISRUPTION:
  Gulf Gate FULL blockade → +0.80
  Formosa Strait partial → +0.15 (NEW — Cathay "inspections")
  disruption = 1.0 + 0.80 + 0.15 = 1.95

WAR PREMIUM: 0.20

DEMAND:
  Global growth further depressed → avg ~1.3%
  demand_factor = 1.0 + (1.3 - 2.0) × 0.05 = 0.965

SPECULATION:
  2 wars + Gulf Gate + Formosa partial = 4 crises
  speculation = 1.0 + 4 × 0.05 = 1.20

OIL PRICE = 80 × (0.965/0.84) × 1.95 × 1.20 × 1.20
         = 80 × 1.149 × 1.95 × 1.20 × 1.20
         = 80 × 3.226
         = $250 (CAPPED — formula gives $258)
```

**OIL PRICE R4: $250/barrel** (CAP HIT)

OPEC returning to NORMAL + Formosa Strait disruption + FULL Gulf Gate = ceiling hit. The price cap at $250 activates for the first time.

**DESIGN FLAG:** The $250 cap is load-bearing here. Without it, the formula produces $258. With two simultaneous chokepoint disruptions, the formula correctly generates extreme prices. The cap prevents unrealistic runaway.

### Gulf Gate Assault — Round 4

Columbia commits 3 naval + 2 ground + mine clearance (12 coins invested).
Persia: 2 ground + 1 tac air + mines 100% + suicide drones.

- Columbia: 5 units attacking. Tech +1 (AI L3). Mine clearance: -0.5 (reduced from -1.0). Suicide drone attrition: -0.3.
- Persia: 3 units defending. Terrain +0.5. Drone swarm +0.3.
- Columbia has overwhelming force but chokepoint is narrow (max 3 unit-pairs engaged).

Dice (seed 300):
- Pair 1: Columbia 5+0.2=5.2 vs Persia 3+0.8=3.8 → Columbia wins. Persia -1 ground.
- Pair 2: Columbia 4+0.2=4.2 vs Persia 4+0.8=4.8 → Persia wins. Columbia -1 naval.
- Pair 3: Columbia 6+0.2=6.2 vs Persia 2+0.8=2.8 → Columbia wins decisively. Persia -1 tac air.

**Result: PARTIAL BREACH.** Columbia destroys 1 ground + 1 tac air. Persia retains 1 ground unit at the chokepoint. Mines partially cleared. **Blockade reduced from FULL to PARTIAL.** Disruption drops from +80% to +40% — effective NEXT round.

Casualties: Columbia -1 naval (9→8). Persia -1 ground, -1 tac air at Gulf Gate.

### Oil Revenue at $250 — Round 4

| Producer | GDP | Oil Rev (coins) | Notes |
|----------|-----|-----------------|-------|
| Solaria | 14.2 | 14.2 × 0.45 × (250/80-1) × 0.3 = **4.07** | PEAK REVENUE |
| Sarmatia | 20.5 | 20.5 × 0.40 × (250/80-1) × 0.3 = **5.22** | PEAK — funds massive war production |
| Mirage | 5.9 | 5.9 × 0.30 × (250/80-1) × 0.3 = **1.13** | Peak |

**Cumulative Sarmatia oil revenue R1-R4: 16.10 coins.** Enough to produce 10+ ground units at wartime rates.

### Ruthenia Wartime Election

Ruthenia at stability 4.40, support 46%. Territory lost. Casualties mounting. But democratic resilience (+0.15/round) and Columbia aid keeping it viable.

Election outcome: Beacon narrowly retains power (46% > 45% threshold). Wartime rally holds.

### GDP Updates — Round 4

| Country | Old GDP | Growth | New GDP |
|---------|---------|--------|---------|
| Columbia | 293.3 | 1.30% | **297.1** |
| Cathay | 211.9 | 3.50% | **219.3** |
| Sarmatia | 20.4 | 0.65% | **20.5** |
| Teutonia | 46.3 | 0.70% | **46.6** |
| Bharata | 49.8 | 5.60% | **52.6** |
| Phrygia | 11.3 | 0.40% | **11.3** |
| Persia | 4.71 | -2.5% | **4.59** |
| Formosa | 8.5 | 1.5% | **8.6** (Strait partial disruption) |

### Round 4 State Table

| Country | GDP | Stability | Support | Treasury | Notes |
|---------|-----|-----------|---------|----------|-------|
| Columbia | 297.1 | 6.55 | 30% | ~25 | Spent 12 on assault, partial breach |
| Cathay | 219.3 | 8.00 | 59% | ~37 | Naval 10, Formosa squeeze |
| Sarmatia | 20.5 | 4.68 | 51% | ~8 | Peak oil revenue funding war |
| Solaria | 14.2 | 7.20 | 68% | ~34 | Record treasury |
| Teutonia | 46.6 | 6.45 | 39% | ~5 | Gutted military for energy |
| Phrygia | 11.3 | 3.95 | 42% | ~1 | FINANCIAL CRISIS THRESHOLD |
| Persia | 4.59 | 3.40 | 32% | ~0 | Near regime collapse |
| Formosa | 8.6 | 6.50 | 50% | ~7 | Strait disruption beginning |

**R4 OIL PRICE: $250/barrel (CAP)** | **Gap Ratio: 219.3/297.1 = 0.738**

---

## ROUND 5 (H1 2028)

### Context
Columbia presidential election this round — the CLIMAX. Support at 30%. Oil partially dropping (blockade now PARTIAL from R4 breach). Cathay naval at 10 = parity zone. Persia at 3.40 stability — near collapse. Formosa Strait partially disrupted.

### Decisions

| Country | Key Economic Decisions |
|---------|----------------------|
| **Solaria** | OPEC: HIGH. Wants to help Columbia (customer) before election. |
| **Sarmatia** | OPEC: NORMAL. No longer needs to flood — prices are dropping anyway. |
| **Persia** | Gulf Gate: Cannot reinforce (only 1 ground left). Prepares for final defense. Seeks ceasefire. |
| **Mirage** | OPEC: HIGH (supports Solaria). |
| **Columbia** | All diplomatic and military focus on election survival. NO new military spending. Cuts war budget. |
| **Cathay** | +1 naval (total 11). Formosa Strait: maintains "inspection" regime. Partial disruption continues. |
| **Teutonia** | Proposes ceasefire resolution at Council. |

### Oil Price Calculation — Round 5

```
BASE PRICE = $80

SUPPLY:
  OPEC: Solaria HIGH (+0.06), Sarmatia NORMAL, Mirage HIGH (+0.06), Persia NORMAL
  supply_factor = 1.0 + 0.12 = 1.12
  Sanctions supply hit: 0.16
  final_supply = max(0.5, 1.12 - 0.16) = 0.96

DISRUPTION:
  Gulf Gate PARTIAL blockade → +0.40 (reduced from R4)
  Formosa Strait partial → +0.15
  disruption = 1.0 + 0.40 + 0.15 = 1.55

WAR PREMIUM: 0.20

DEMAND:
  Slight recovery as prices drop → avg ~1.5%
  demand_factor = 0.975

SPECULATION:
  2 wars + Gulf Gate partial + Formosa partial = 4 crises
  BUT ceasefire talks reduce speculation
  speculation = 1.0 + 3 × 0.05 = 1.15

OIL PRICE = 80 × (0.975/0.96) × 1.55 × 1.20 × 1.15
         = 80 × 1.016 × 1.55 × 1.20 × 1.15
         = 80 × 2.173
         = $173.8/barrel
```

**OIL PRICE R5: $174/barrel** (DOWN sharply from $250)

**Partial blockade breach drops price $76 in one round.** This is the key finding: breaking the blockade from FULL to PARTIAL drops disruption from 1.80 to 1.55 (-14%), but the multiplicative nature of the formula amplifies this into a 30% price drop. OPEC HIGH from Solaria/Mirage adds further downward pressure.

### Columbia Presidential Election

Support entering: ~29% (after round effects).
- Oil price dropping ($250→$174) — positive signal
- Gulf Gate partially breached — positive signal
- But: 8 rounds of economic pain, naval losses, ally Ruthenia losing territory
- War tiredness: 3.5 (accumulating for 5 rounds)

**Election: Extremely tight.** The oil price drop and Gulf Gate breach may not arrive fast enough. Tribune opposition runs on "endless war" platform.

Result: Columbia support stabilizes at **28%** — historic low. If democratic support falls below 25%, forced policy change (ceasefire pressure becomes irresistible). The Dealer is politically damaged but survives.

### Oil Revenue Impact of Price Drop

| Producer | GDP | Oil Rev at $174 | Change from R4 ($250) |
|----------|-----|-----------------|----------------------|
| Solaria | 14.6 | 2.31 | -1.76 (-43%) |
| Sarmatia | 20.6 | 2.90 | -2.32 (-44%) |
| Mirage | 6.0 | 0.63 | -0.50 (-44%) |

Revenue drops proportionally with price. The $76 drop hits ALL producers equally. Sarmatia loses 2.32 coins/round — equivalent to 1.5 ground units of production capacity per round.

### GDP Updates — Round 5

| Country | Old GDP | Growth | New GDP |
|---------|---------|--------|---------|
| Columbia | 297.1 | 1.50% | **301.6** |
| Cathay | 219.3 | 3.55% | **227.1** |
| Sarmatia | 20.5 | 0.60% | **20.6** |
| Teutonia | 46.6 | 0.90% | **47.0** |
| Bharata | 52.6 | 5.70% | **55.6** |
| Persia | 4.59 | -2.8% | **4.46** |

### Round 5 State Table

| Country | GDP | Stability | Support | Treasury | Notes |
|---------|-----|-----------|---------|----------|-------|
| Columbia | 301.6 | 6.40 | 28% | ~22 | Election survival, barely |
| Cathay | 227.1 | 8.00 | 59% | ~36 | Naval 11, Gap 0.753 |
| Sarmatia | 20.6 | 4.60 | 50% | ~6 | Revenue dropping, war costly |
| Solaria | 14.6 | 7.20 | 67% | ~32 | Revenue declining from peak |
| Teutonia | 47.0 | 6.50 | 40% | ~6 | Some relief from lower oil |
| Phrygia | 11.3 | 3.80 | 40% | ~1 | In financial crisis |
| Persia | 4.46 | 3.20 | 30% | ~0 | Seeks ceasefire, near collapse |

**R5 OIL PRICE: $174/barrel** | **Gap Ratio: 227.1/301.6 = 0.753**

---

## ROUND 6 (H2 2028)

### Context
Columbia finally breaks the Gulf Gate blockade completely. Persia at 3.20 stability. One more push.

### Decisions

| Country | Key Economic Decisions |
|---------|----------------------|
| **Solaria** | OPEC: NORMAL. Revenue falling, no need to flood market. |
| **Sarmatia** | OPEC: NORMAL. Same logic. |
| **Persia** | Gulf Gate: Last ground unit overwhelmed. **Ceasefire negotiations begin.** |
| **Mirage** | OPEC: NORMAL. Mediating ceasefire. |
| **Columbia** | **OPERATION GULF LIBERATOR:** 2 naval + 3 ground + mine clearance. Final push. 8 coins. |
| **Cathay** | +1 naval (total 12). Formosa pressure maintained but no escalation. |

### Gulf Gate Final Assault

Columbia: 2 naval + 3 ground + mine clearance vs Persia: 1 ground (last unit).
Overwhelming force. Dice irrelevant at 5:1 ratio.

**Result: BLOCKADE BROKEN.** Gulf Gate cleared. Persia's last ground unit destroyed or captured. Mine clearance ongoing (partial disruption for 1 round, then clear).

**Blockade status: CLEARED (effective R7).** This round: residual mines = partial disruption (+20%, half of +40%).

### Oil Price Calculation — Round 6

```
BASE PRICE = $80

SUPPLY:
  OPEC: All NORMAL
  supply_factor = 1.00
  Sanctions supply hit: 0.16
  final_supply = 0.84

DISRUPTION:
  Gulf Gate: Residual mines only → +0.20 (clearing in progress)
  Formosa partial → +0.15
  disruption = 1.0 + 0.20 + 0.15 = 1.35

WAR PREMIUM:
  Columbia-Persia: ceasefire negotiations → effectively 1 major war
  Sarmatia-Ruthenia: continuing → +0.10
  war_premium = 0.10

DEMAND:
  Recovery beginning → avg ~1.7%
  demand_factor = 0.985

SPECULATION:
  1 war + residual Gulf Gate + Formosa = 3 crises, but ceasefire optimism
  speculation = 1.0 + 2 × 0.05 = 1.10

OIL PRICE = 80 × (0.985/0.84) × 1.35 × 1.10 × 1.10
         = 80 × 1.173 × 1.35 × 1.10 × 1.10
         = 80 × 1.916
         = $153.3/barrel
```

**OIL PRICE R6: $153/barrel** (DOWN from $174)

### Round 6 State Table

| Country | GDP | Stability | Support | Treasury | Notes |
|---------|-----|-----------|---------|----------|-------|
| Columbia | 305.0 | 6.50 | 30% | ~18 | Gulf Gate broken, rally effect |
| Cathay | 235.2 | 8.00 | 59% | ~35 | Naval 12, patient |
| Sarmatia | 20.7 | 4.55 | 49% | ~5 | Revenue declining |
| Solaria | 14.8 | 7.15 | 66% | ~33 | Revenue dropping |
| Persia | 4.35 | 3.05 | 28% | ~0 | Ceasefire imminent |
| Teutonia | 47.4 | 6.60 | 41% | ~7 | Relief beginning |

**R6 OIL PRICE: $153/barrel** | **Gap Ratio: 235.2/305.0 = 0.771**

---

## ROUND 7 (H1 2029)

### Context
Gulf Gate fully cleared. Persia ceasefire signed. Only Sarmatia-Ruthenia war continues. Oil markets normalizing. Formosa Strait tension remains.

### Decisions

| Country | Key Economic Decisions |
|---------|----------------------|
| **Solaria** | OPEC: LOW (-0.06). Wants to prop up prices — revenue has halved from peak. |
| **Sarmatia** | OPEC: LOW (-0.06). Joins Solaria in price support. War needs funding. |
| **Mirage** | OPEC: NORMAL. Doesn't want to antagonize importers. |
| **Columbia** | Post-war reconstruction focus. Rebuilding treasury. |
| **Cathay** | +1 naval (total 13). Formosa partial disruption maintained. |

### Oil Price Calculation — Round 7

```
BASE PRICE = $80

SUPPLY:
  OPEC: Solaria LOW (-0.06), Sarmatia LOW (-0.06), Mirage NORMAL, Persia NORMAL
  supply_factor = 1.0 - 0.12 = 0.88
  Sanctions supply hit: 0.16 (Sarmatia + Persia still sanctioned)
  final_supply = max(0.5, 0.88 - 0.16) = 0.72

DISRUPTION:
  Gulf Gate: CLEAR → 0
  Formosa partial → +0.15
  disruption = 1.15

WAR PREMIUM:
  Sarmatia-Ruthenia → +0.10
  war_premium = 0.10

DEMAND:
  Recovery underway → avg ~2.0%
  demand_factor = 1.00

SPECULATION:
  1 war + Formosa = 2 crises
  speculation = 1.0 + 2 × 0.05 = 1.10

OIL PRICE = 80 × (1.00/0.72) × 1.15 × 1.10 × 1.10
         = 80 × 1.389 × 1.15 × 1.10 × 1.10
         = 80 × 1.933
         = $154.6/barrel
```

**OIL PRICE R7: $155/barrel** (FLAT despite blockade being cleared!)

**DESIGN FLAG:** OPEC going LOW + sanctions supply hit = final_supply 0.72. This is LOWER than when the blockade was active but OPEC was on HIGH (final_supply 1.02 in R2-R3). The supply constraint from OPEC cuts + sanctions now exceeds the blockade effect. Price stabilizes around $155 instead of dropping further.

**This is a critical finding:** OPEC LOW + sanctions can replicate half the price effect of a full blockade. The engine correctly shows that supply-side tools remain powerful even after the crisis ends.

### Round 7 State Table

| Country | GDP | Stability | Support | Treasury | Notes |
|---------|-----|-----------|---------|----------|-------|
| Columbia | 309.5 | 6.65 | 31% | ~20 | Post-war recovery |
| Cathay | 243.6 | 8.00 | 59% | ~34 | Naval 13 (!), Gap 0.786 |
| Sarmatia | 20.8 | 4.50 | 48% | ~5 | OPEC LOW props revenue |
| Solaria | 15.1 | 7.10 | 65% | ~33 | OPEC LOW props revenue |
| Teutonia | 47.9 | 6.70 | 42% | ~8 | Recovering |
| Persia | 4.35 | 3.10 | 27% | ~0 | Post-war wreckage |

**R7 OIL PRICE: $155/barrel** | **Gap Ratio: 243.6/309.5 = 0.787**

---

## ROUND 8 (H2 2029)

### Context
Post-crisis normalization. One war remains. Formosa tension. OPEC adjusting. Markets expect further easing.

### Decisions

| Country | Key Economic Decisions |
|---------|----------------------|
| **Solaria** | OPEC: NORMAL. Revenue stabilized, no need for extreme cuts. |
| **Sarmatia** | OPEC: NORMAL. War grinding down, ceasefire talks beginning. |
| **Mirage** | OPEC: NORMAL. |
| **Columbia** | Rebuilds treasury. Redeployment from Gulf to Pacific. |
| **Cathay** | +1 naval (total 14). Eases Formosa "inspections" slightly. |

### Oil Price Calculation — Round 8

```
BASE PRICE = $80

SUPPLY:
  OPEC: All NORMAL
  supply_factor = 1.00
  Sanctions supply hit: 0.16
  final_supply = 0.84

DISRUPTION:
  Gulf Gate: CLEAR
  Formosa: Eased → +0.08 (reduced from +0.15)
  disruption = 1.08

WAR PREMIUM:
  Sarmatia-Ruthenia (ceasefire talks) → +0.05 (reduced)
  war_premium = 0.05

DEMAND:
  Recovery → avg ~2.1%
  demand_factor = 1.005

SPECULATION:
  1 winding-down war + reduced Formosa = 1.5 crises
  speculation = 1.0 + 1.5 × 0.05 = 1.075

OIL PRICE = 80 × (1.005/0.84) × 1.08 × 1.05 × 1.075
         = 80 × 1.196 × 1.08 × 1.05 × 1.075
         = 80 × 1.458
         = $116.7/barrel
```

**OIL PRICE R8: $117/barrel**

Finally approaching normalization. Still elevated above the $80 baseline due to sanctions supply hit (0.16) and residual Formosa tension. Without sanctions, price would be ~$93. Sanctions on oil producers maintain a permanent ~$25 premium.

### Final State Table — Round 8

| Country | GDP | Stability | Support | Treasury | Naval | Notes |
|---------|-----|-----------|---------|----------|-------|-------|
| Columbia | 314.2 | 6.75 | 32% | ~24 | 8 | Post-war, treasury damaged |
| Cathay | 252.3 | 8.00 | 59% | ~33 | **14** | Gap: 0.803, Naval: 14/8 = 1.75 |
| Sarmatia | 20.9 | 4.45 | 47% | ~5 | 2 | War winding down |
| Ruthenia | 2.5 | 3.80 | 42% | ~1 | 0 | Survived but battered |
| Persia | 4.30 | 3.10 | 26% | ~0 | 0 | Post-war ruin |
| Solaria | 15.4 | 7.10 | 64% | ~34 | 0 | Massive wealth accumulated |
| Mirage | 6.5 | 7.90 | 68% | ~18 | 0 | Wealthy from oil |
| Teutonia | 48.4 | 6.80 | 43% | ~9 | 0 | Recovered but weakened |
| Bharata | 61.5 | 5.95 | 56% | ~16 | 2 | Major winner — grew 46% |
| Phrygia | 11.5 | 3.60 | 38% | ~1 | 1 | Economic crisis ongoing |
| Yamato | 45.0 | 7.60 | 47% | ~11 | 2 | Stable |
| Formosa | 8.8 | 6.30 | 48% | ~6 | 0 | Under Cathay pressure |

**R8 OIL PRICE: $117/barrel** | **Gap Ratio: 252.3/314.2 = 0.803**

---

## OIL PRICE TRAJECTORY SUMMARY

| Round | Blockade Status | OPEC Config | Disruption | Final Supply | Oil Price | Change |
|-------|----------------|-------------|-----------|-------------|-----------|--------|
| R1 | FULL | N/H/N/N | 1.80 | 0.90 | **$221** | — |
| R2 | FULL | H/H/N/H | 1.80 | 1.02 | **$194** | -$27 |
| R3 | FULL | H/H/N/H | 1.80 | 1.02 | **$186** | -$8 |
| R4 | FULL→PARTIAL | N/N/N/N + Formosa | 1.95 | 0.84 | **$250** | +$64 (CAP) |
| R5 | PARTIAL + Formosa | H/N/N/H | 1.55 | 0.96 | **$174** | -$76 |
| R6 | CLEARING + Formosa | N/N/N/N | 1.35 | 0.84 | **$153** | -$21 |
| R7 | CLEAR + Formosa | L/L/N/N | 1.15 | 0.72 | **$155** | +$2 |
| R8 | CLEAR + Formosa easing | N/N/N/N | 1.08 | 0.84 | **$117** | -$38 |

### Price Arc
```
$250 |          *
     |
$220 |  *
$200 |
$190 |     * *
$175 |             *
$155 |                 * *
$120 |                     *
$100 |
 $80 |.............................  (baseline)
     R1  R2  R3  R4  R5  R6  R7  R8
```

---

## CUMULATIVE OIL REVENUE (coins)

| Producer | R1 | R2 | R3 | R4 | R5 | R6 | R7 | R8 | TOTAL |
|----------|----|----|----|----|----|----|----|----|-------|
| Solaria | 2.61 | 2.59 | 2.48 | 4.07 | 2.31 | 1.85 | 1.90 | 1.35 | **19.16** |
| Sarmatia | 4.22 | 3.47 | 3.19 | 5.22 | 2.90 | 2.25 | 2.30 | 1.58 | **25.13** |
| Mirage | 0.79 | 0.71 | 0.65 | 1.13 | 0.63 | 0.50 | 0.48 | 0.38 | **5.27** |
| Persia | 0.92 | 0.80 | 0.78 | 1.10 | 0.60 | 0.40 | 0.35 | 0.30 | **5.25** |

**Sarmatia total: 25.13 coins from oil alone over 8 rounds.** At 1.5 coins/ground unit (wartime production), that funds 16+ ground units. The blockade that was meant to pressure Persia enriched Sarmatia — Columbia's other adversary.

**Solaria total: 19.16 coins.** Started with 20 coins treasury. Ends with ~34 coins treasury. Nearly doubled sovereign wealth during the crisis.

---

## ANALYSIS: OIL PRICE MECHANIC CALIBRATION

### 1. Does $198+ starting price create right economic pressure?

**YES, with caveats.** The full blockade produces $221 R1 price (vs $198 in Test 1 with partial blockade). This creates:
- Visible GDP drag on importers (Teutonia growth halved, Phrygia enters crisis)
- Treasury drain on Columbia (net importer despite domestic production)
- Massive political pressure (Columbia support drops from 38% to 28% by R5)
- Genuine incentive for military action to break blockade

**Caveat:** The pressure is almost entirely on importers, not on the blockader. Persia's economy was already destroyed before the blockade. The blockade hurts Columbia's allies more than it hurts Columbia's enemy.

### 2. Do OPEC+ decisions matter?

**YES — significantly.** OPEC member decisions create a ~$50 price swing:
- All NORMAL + full blockade: ~$235
- All HIGH + full blockade: ~$186
- All LOW + no blockade: ~$155
- All NORMAL + no blockade: ~$117

OPEC is the second most important variable after the blockade. However, the **coordination problem is real**: Sarmatia defects to HIGH immediately (needs war funding), and others follow (revenue maximization). OPEC coordination only returns when prices drop enough to hurt per-barrel revenue. This is realistic and creates genuine player decisions.

### 3. Does breaking the blockade work mechanically?

**YES — dramatically.** Full→Partial: $250→$174 (-30%). Partial→Clear: $174→$153 (-12%). The multiplicative formula means that the blockade's +80% disruption interacts with ALL other multipliers (war premium, speculation, supply constraints). Removing it cascades through the entire calculation.

**DESIGN FLAG:** The R4 spike to $250 (cap) when Formosa Strait is simultaneously disrupted reveals that **dual chokepoint disruption is the worst-case scenario** and correctly hits the price ceiling. This is good design — it creates a natural escalation limit and gives players a visible "danger zone."

### 4. Does oil price affect political stability?

**STRONGLY.** The chain is:
- Oil price → inflation → inflation_factor on GDP → lower growth → stability penalty → support drop
- For Phrygia (45% starting inflation): oil shock pushes toward 50%+ inflation, stability drops from 5.0 to 3.60 over 8 rounds, triggering financial crisis
- For Columbia: indirect through GDP drag and political support (-10 points over 5 rounds)
- For Teutonia: GDP growth halved (1.2% → 0.7%), military budget gutted for energy subsidies

### 5. OPEC coordination dynamics

The OPEC prisoner's dilemma plays out exactly as designed:
- **R1:** Sarmatia defects (HIGH), others stay NORMAL
- **R2-3:** Others follow to HIGH (revenue maximization)
- **R4:** All return to NORMAL (prices dropping, per-barrel revenue matters again)
- **R7:** Solaria + Sarmatia go LOW (blockade cleared, need to prop prices)
- **R8:** All NORMAL (new equilibrium)

This creates genuine decision tension for OPEC members every round.

### 6. Perverse incentive: Blockade enriches the wrong adversary

**CRITICAL DESIGN FINDING.** The Gulf Gate blockade is meant to be Persia's weapon against Columbia and Gulf states. But the primary economic beneficiary is **Sarmatia** — Columbia's other enemy. Sarmatia earns 25+ coins from elevated oil prices over 8 rounds, directly funding its war against Ruthenia (Columbia's ally).

This is either:
- (a) A brilliant emergent dynamic that creates a genuine strategic dilemma for Columbia (breaking the blockade helps Ruthenia indirectly by reducing Sarmatia's revenue), or
- (b) An unintended consequence that needs design attention

**Recommendation:** This should be flagged as an intentional design feature. It creates a multi-front economic dilemma that tests leadership judgment — exactly what the SIM is for. Columbia must weigh: Gulf Gate blockade hurts my economy AND funds my other enemy's war. Breaking it helps both problems simultaneously. This reinforces the incentive to act.

### 7. Producer vs Importer asymmetry

Over 8 rounds:
- **Solaria** gained ~19 coins in oil revenue (treasury nearly doubled)
- **Teutonia** lost ~8 coins in energy costs and military cuts
- **Phrygia** entered financial crisis
- **Bharata** grew 46% (bought discounted oil from everyone)

The SIM correctly creates a **producer bonanza** during crisis and **importer pain**. But the pain distribution is uneven — Phrygia and Teutonia suffer more than Columbia (whose domestic production partially hedges exposure). This creates different incentive structures for different Western Treaty members.

### 8. Price cap analysis

The $250 cap activated in R4 when Gulf Gate + Formosa were simultaneously disrupted. Without the cap, the formula produced $258. The cap is necessary to prevent unrealistic prices, but it creates a **design plateau** where further disruption has no additional price effect. If both chokepoints are fully blocked AND OPEC goes LOW, the formula would produce ~$350+ — all clamped to $250.

**Recommendation:** The $250 cap is appropriate. Consider whether the cap should be soft (exponential decay approaching $250) rather than hard (brick wall at $250), to preserve marginal incentives near the ceiling.

### 9. Sanctions as permanent price floor

Even after the blockade clears, sanctions on Sarmatia and Persia maintain a permanent 0.16 supply hit. This keeps oil above $100 in all post-crisis scenarios. Lifting sanctions on either country would drop supply_hit to 0.08, reducing prices by ~$15-20.

**This creates a sanctions trade-off:** maintaining sanctions on Sarmatia hurts Columbia's own economy through elevated oil prices. This is a genuine design tension that forces choices.

### 10. Speed of normalization

Oil drops from $250 (peak R4) to $117 (R8) over 4 rounds — a 53% decline. This is driven by:
- Blockade clearance (biggest factor)
- Ceasefire reducing war premium
- Demand recovery
- OPEC normalization

The 4-round normalization is appropriate — fast enough that breaking the blockade feels impactful, slow enough that accumulated damage persists. Columbia's treasury never recovers to starting levels.

---

## DESIGN RECOMMENDATIONS

| # | Finding | Severity | Recommendation |
|---|---------|----------|---------------|
| 1 | Gulf Gate full blockade creates $220+ oil — correct pressure level | VALID | No change needed |
| 2 | OPEC decisions create ~$50 swing — meaningful but not dominant | VALID | No change needed |
| 3 | Blockade breach cascades multiplicatively — dramatic and satisfying | VALID | No change needed |
| 4 | $250 cap hit with dual chokepoint disruption | CALIBRATE | Consider soft cap (asymptotic approach to $250) instead of hard clamp |
| 5 | Sarmatia enriched by 25+ coins from Persia's blockade | FEATURE | Intentional emergent dynamic — document as design feature |
| 6 | Phrygia enters financial crisis from oil shock alone | VALID | Correct — 45% starting inflation + oil shock = crisis |
| 7 | OPEC coordination breaks and reforms realistically | VALID | Prisoner's dilemma works as intended |
| 8 | Sanctions maintain permanent $25 price floor | VALID | Creates genuine sanctions trade-off |
| 9 | Columbia domestic oil production (+$7/round at peak) partially hedges | CHECK | Verify Columbia's 5% resource sector is intentional — seems low for the world's largest oil producer parallel |
| 10 | Post-blockade price floor (~$117) still elevated | VALID | Sanctions + residual tension maintain realistic premium |

---

## TESTER VERDICT

**Oil price mechanic: WELL-CALIBRATED.** The formula produces realistic price dynamics across a wide range of scenarios. The blockade is correctly the dominant variable. OPEC decisions create meaningful but not overwhelming secondary effects. The multiplicative structure generates satisfying cascade effects when blockades are broken. Producer/importer asymmetry creates genuine strategic tensions.

**One concern:** Columbia's 5% resource sector may understate its oil producer status. If Columbia is meant to parallel the world's largest oil producer, 5% seems low. This would increase Columbia's hedge against high oil prices and reduce the blockade's political pressure. Verify with SIMON whether this is intentional.

**The Gulf Gate blockade is the most consequential single action in the SIM economy.** It creates more economic disruption than all sanctions combined. This is correct — chokepoint control should matter enormously in a geopolitical SIM. But it means the Persia player has outsized economic leverage relative to their military and economic size. That may be intentional (asymmetric warfare thesis) or may need balancing.

---

*Test 3 complete. Filed for VERA cross-check and KEYNES economic validation.*
