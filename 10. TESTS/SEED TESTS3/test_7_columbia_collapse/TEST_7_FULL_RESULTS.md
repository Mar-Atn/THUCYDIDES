# TEST 7: COLUMBIA OVERSTRETCH — Full Results
## SEED TESTS3 | Engine v3 (4 calibration fixes)
**Date:** 2026-03-28 | **Tester:** Independent Claude Code Instance
**Objective:** Stress-test Columbia under cascading failures. Does the crisis state mechanic work when a superpower spirals?

---

## STARTING CONDITIONS (Round 0)

| Parameter | Columbia | Notes |
|-----------|----------|-------|
| GDP | 280.00 | Largest economy |
| GDP growth base | 1.8% | Slowing |
| Treasury | 50.00 | Fiscal reserves |
| Inflation | 3.5% | Above baseline |
| Stability | 7.0 | Functional democracy under stress |
| Political support | 38% | Dealer approval at historic lows |
| War tiredness | 1.0 | Persia war just started |
| Debt burden | 5.0 coins/round | $39T national debt |
| Military | 22G / 11N / 15TA / 12SM / 4AD = 64 units (excl. strat/AD) |
| Maintenance | 64 * 0.5 = 32.0 coins/round |
| Social baseline | 0.30 * 280 = 84.0 coins/round |
| Revenue (base) | 280 * 0.24 = 67.2 + oil revenue |
| Oil price | $80.0 (starting) |
| Wars | At war with Persia (10 units committed) |
| Parliament | President's camp 3-2 (Dealer + Volt + NPC Seat 5) |
| AI level | L3 (progress 0.80 toward L4) |
| Formosa dependency | 0.65 |

**Critical observation at R0:** Columbia revenue (67.2) cannot cover mandatory costs (maintenance 32.0 + social 84.0 = 116.0). Mandatory costs EXCEED revenue by ~49 coins. This means Columbia starts in structural deficit, drawing from treasury every round. This is by design — mirrors real US fiscal reality. The 50-coin treasury is a buffer, not a solution.

**ENGINE NOTE:** The social baseline cost of 84 coins (30% of 280 GDP) is enormous and fundamentally constrains Columbia. Total mandatory = 116 coins against ~67 revenue = 49-coin structural deficit per round BEFORE any discretionary spending. This is the fiscal trap underlying the entire test.

---

## ROUND 1: THE INCAPACITATION

### Prescribed Events
- Dealer incapacitated (10% chance triggered). Volt becomes Acting President.
- Volt announces "Columbia First" agenda: Persia drawdown proposal, reduce Ruthenia aid, pivot to Cathay competition.

### Agent Decisions

**Volt (Acting President):**
- Announces "Columbia First Doctrine": prioritize Cathay containment over Middle East
- Proposes Persia drawdown timeline (6-round phased withdrawal)
- Reduces Ruthenia military aid by 50% (saves ~2 coins/round)
- Initiates direct communication with Helmsman (business-friendly overture)
- Budget: No new military production (conserve funds). Maintain tariffs on Cathay.
- Tech R&D: Allocate 8 coins to AI (push toward L4)

**Shield (SecDef):**
- Reluctantly accepts Volt's drawdown order but warns it signals weakness to Persia
- Maintains all current deployments (cannot withdraw mid-combat in 1 round)
- Flags: "Removing forces from Persia theater requires 2-round extraction timeline"

**Tribune (Opposition):**
- Immediately calls for hearings on Dealer's health, war authorization
- Begins campaign messaging: "The VP is running the country, not the president"

**Shadow (CIA):**
- Briefs Volt selectively: emphasizes Cathay threat, downplays Persia progress
- Intelligence assessment: Cathay naval buildup accelerating, Choson test preparations detected

### Engine Calculations — Round 1

**Oil Price:**
- Base: $80. Supply: 1.0 (OPEC normal). Disruption: 1.50 (Gulf Gate blocked by Persia ground forces). War premium: 0.10 (2 wars).
- Raw price: 80 * (1.0/1.0) * 1.50 * 1.10 = $132.0
- Inertia (40/60): 80 * 0.4 + 132 * 0.6 = $111.2
- **Oil R1: $111.2**

**Columbia GDP:**
- Base growth: +1.8%
- Tariff hit: Columbia has tariffs on Cathay (L2 bilateral). Net cost from CSV tariff data. Estimated trade weight Columbia-Cathay ~15%. Net tariff cost ~4.2 coins. Hit: -(4.2/280) * 1.5 = -2.25%
- Sanctions hit: 0 (Columbia not sanctioned)
- Oil shock: Columbia IS oil producer. Oil > $80: +0.01 * (111.2-80)/50 = +0.62%
- Semiconductor: No Formosa disruption. 0.
- War hit: 1 war zone (Persia). Estimated 1 occupied zone, 0 infra damage. -(1*0.03 + 0) = -3.0%
- Tech boost: AI L3 = +1.5%
- Momentum: Starting at 0. Effect: 0.
- Crisis mult: normal = 1.0
- Blockade: 0
- **Raw growth: 1.8 - 2.25 + 0.62 + 0 - 3.0 + 1.5 + 0 + 0 = -1.33%**
- **Effective growth: -1.33% * 1.0 = -1.33%**
- **New GDP: 280 * (1 - 0.0133) = 276.27**

**Revenue:**
- Base: 276.27 * 0.24 = 66.30
- Oil revenue: 111.2 * 0.08 * 276.27 * 0.01 = 2.46 (resource sector 8%)
- Debt service: -5.0
- Inflation erosion: delta from baseline (3.5 - 3.5 = 0). 0.
- War damage: 0 infra * 0.02 * GDP = 0
- Sanctions cost: 0
- **Revenue: 66.30 + 2.46 - 5.0 = 63.76**

**Budget Execution:**
- Mandatory: maintenance (64 * 0.5 = 32.0) + social baseline (276.27 * 0.30 = 82.88) = 114.88
- Revenue: 63.76
- Deficit BEFORE discretionary: 114.88 - 63.76 = **51.12 coins**
- Treasury: 50.0 - 51.12 = -1.12. Treasury depleted. Money printed: 1.12 coins.
- Inflation spike from printing: 1.12/276.27 * 80 = 0.32%
- Debt burden increase: 51.12 * 0.15 = 7.67. New debt: 5.0 + 7.67 = 12.67
- **No discretionary spending possible.** No military production. No additional tech R&D (beyond what was in base).
- New treasury: 0.0

**Tech Advancement:**
- AI R&D: Volt allocated 8 coins but NO discretionary budget available. 0 coins actually spent.
- AI progress stays at 0.80. No level-up.

**Inflation:**
- Previous: 3.5%. Baseline: 3.5%. Excess: 0. Decay: 0 * 0.85 = 0. New excess: 0 + 0.32 = 0.32.
- **New inflation: 3.82%**

**Economic State:**
- Stress triggers: Oil > 150? No (111.2). Inflation > baseline+15? No. GDP growth < -1? Yes (-1.33). Treasury <= 0? Yes. Stability < 4? No. Formosa disrupted? No.
- Stress triggers: 2. **Transition: normal -> STRESSED**
- Crisis triggers: 0.

**Momentum:**
- GDP growth > 2? No. State = normal at calculation? No (stressed now). Stability > 6? Yes.
- Boost: 0.15 (stability > 6).
- Crash: GDP < -2? No. New state stressed (not crisis). No crash signals.
- **New momentum: 0.0 + 0.15 = 0.15**

Wait -- economic state just transitioned to stressed. Rechecking: momentum step happens AFTER economic state update. So eco_state = "stressed" at momentum calculation.
- Boost: stability > 6 = +0.15. Normal = no. GDP > 2 = no. Total boost: 0.15.
- **New momentum: 0.15**

**Stability:**
- Base delta: 0.0
- GDP growth (-1.33%): gdp < -2? No. gdp > 2? No. 0.
- Social spending: actual social ratio = 82.88/276.27 = 0.30. Baseline 0.30. At baseline: +0.05 * 1.5 (at war) = +0.075
- War friction: Columbia is attacker in Persia. Primary combatant: -0.08. War tiredness (1.0): -min(1.0*0.04, 0.4) = -0.04.
- Sanctions: 0.
- Inflation friction: delta = 3.82 - 3.5 = 0.32. < 3. 0.
- Crisis state: stressed = -0.10.
- Positive inertia: old stab 7.0. 7 <= 7 < 9: +0.05.
- Total delta: 0 + 0.075 - 0.08 - 0.04 + 0 + 0 - 0.10 + 0.05 = **-0.095**
- New stability: 7.0 - 0.095 = **6.91**

**Political Support:**
- GDP growth (-1.33) - 2.0 = -3.33 * 0.8 = -2.66
- Casualties: 0.
- Stability (6.91) - 6.0 = 0.91 * 0.5 = +0.46
- Stressed: -2.0
- Oil > 150? No. 0.
- Election proximity R1: -1.0 (Columbia R1 effect)
- War tiredness (1.0): < 2, no effect.
- Mean reversion: -(38.0 - 50) * 0.05 = +0.60
- Total: -2.66 + 0.46 - 2.0 + 0 - 1.0 + 0.60 = **-4.60**
- New support: 38.0 - 4.60 = **33.40%**

**Pass 2 Adjustments:**
- Economic state transition to stressed (from normal): market panic. GDP * 0.05 = 276.27 * 0.05 = 13.81. New GDP: 276.27 - 13.81 = 262.46. But wait -- panic triggers only for crisis/collapse, NOT stressed. No panic.
- Stability > 3, so no capital flight.
- Rally around flag: war duration = R1 - R0 = 1. Rally: max(10 - 1*3, 0) = 7. Bounded: min(7, 33.4*0.30) = 7. Support += 7 -> 33.40 + 7 = 40.40. But wait -- the rally was already factored in the Persia war. Actually, rally is computed in Pass 2 separately. Let me apply it: rally = max(10 - 1*3, 0) = 7.0. Bounded = min(7.0, 33.4 * 0.30) = min(7.0, 10.02) = 7.0. Support = 33.40 + 7.0 = **40.40%**. Wait -- the Persia war started at round 0, so war_duration at round 1 = round_num - start_round = 1 - 0 = 1. Rally = max(10-3, 0) = 7.

However, Persia war start_round = 0. So at R1, duration = 1. Rally effect = max(10 - 1*3, 0) = 7.0. This is high. But it represents the initial war rally. By R3 it will be near zero.

### Round 1 State Table

| Parameter | Start | End R1 | Delta |
|-----------|-------|--------|-------|
| GDP | 280.00 | 276.27 | -3.73 (-1.33%) |
| Treasury | 50.00 | 0.00 | -50.00 |
| Debt burden | 5.00 | 12.67 | +7.67 |
| Inflation | 3.50% | 3.82% | +0.32 |
| Oil price | $80.0 | $111.2 | +$31.2 |
| Stability | 7.00 | 6.91 | -0.09 |
| Support | 38.0% | 40.4% | +2.4 (rally) |
| War tiredness | 1.0 | 1.15 | +0.15 |
| Economic state | normal | STRESSED | TRANSITION |
| Momentum | 0.0 | 0.15 | +0.15 |
| Military | 64 units | 64 units | 0 (no production) |
| AI progress | 0.80 | 0.80 | 0 (no R&D budget) |

**Key finding R1:** Treasury depleted in a single round. The structural deficit (mandatory 115 > revenue 64) consumed the entire 50-coin reserve. Columbia enters R2 with ZERO treasury and 12.67 debt burden. This is the fiscal death spiral igniting. Volt's "Columbia First" agenda is irrelevant to the fiscal reality -- the engine does not care about rhetoric.

---

## ROUND 2: GULF GATE FAILURE + MIDTERMS

### Prescribed Events
- Gulf Gate assault FAILS. Persia reinforced. Columbia loses 1 naval unit (11 -> 10).
- Columbia midterm elections: Tribune wins Seat 5. Parliament flips to opposition 3-2.

### Agent Decisions

**Volt (still Acting President -- Dealer remains incapacitated through R2):**
- Orders continued Persia air campaign at reduced tempo (cost reduction)
- Announces Ruthenia aid cut: from 4 coins/round to 2 coins/round
- Budget: Attempt to cut social spending to 28% (from 30%) -- politically toxic
- Tech: Still wants AI R&D but has no budget

**Tribune (now with parliamentary majority):**
- Blocks any new military authorization. Demands war funding oversight.
- Initiates investigation into Persia war legality.
- Budget becomes contested: Tribune can veto military spending increases.

**Shield (SecDef):**
- Reports naval loss. Recommends withdrawing remaining naval assets from Gulf zone to prevent further losses.
- 1 carrier strike group moved to defensive posture.

### Engine Calculations — Round 2

**Oil Price:**
- Gulf Gate still blocked (Persia ground forces). Previous oil: $111.2.
- Supply: 1.0. Disruption: 1.50 (Gulf Gate). War premium: 0.10.
- Formula price: 80 * (1.0/1.0) * 1.50 * 1.10 = $132.0
- Inertia: 111.2 * 0.4 + 132 * 0.6 = 44.48 + 79.2 = **$123.7**

**Columbia Naval: 11 -> 10** (combat loss). Auto-production check: R2 is even, naval >= 5: +1. But navy just lost 1. New naval = 10 + 1 (auto) = 11. Wait: the loss happens first (prescribed), then auto-production fires. Final naval: 10 + 1 = 11.

Actually -- the prescribed loss of 1 naval occurs during combat. Auto-production in Step 5 adds 1 (R2 even, naval >= 5, no production ordered). So net naval: 11 - 1 + 1 = 11. The auto-production offsets the combat loss.

However, the test specifies "Columbia loses 1 naval (11->10)". I will apply the loss and note that auto-production partially offsets it. Final naval at end of R2: 11 (10 + 1 auto).

Total units: 22G + 11N + 15TA + 12SM + 4AD = 64. Maintenance stays at 32.0.

**GDP:**
- Previous GDP: 276.27. Base growth: still 1.8% (structural).
- Tariff hit: -2.25% (same Cathay tariffs)
- Oil shock: Columbia oil producer. +0.01*(123.7-80)/50 = +0.87%
- War hit: Persia still active. 1 zone. -3.0%
- Tech: AI L3 = +1.5%
- Momentum: 0.15 * 0.01 = +0.15%
- Crisis mult: STRESSED = 0.85
- Raw growth: 1.8 - 2.25 + 0.87 + 0 - 3.0 + 1.5 + 0.15 + 0 = -0.93%
- **Effective growth: -0.93% * 0.85 = -0.79%**
- **New GDP: 276.27 * (1 - 0.0079) = 274.09**

**Revenue:**
- Base: 274.09 * 0.24 = 65.78
- Oil: 123.7 * 0.08 * 274.09 * 0.01 = 2.71
- Debt: -12.67
- Inflation erosion: delta = 3.82 - 3.5 = 0.32. Erosion: 0.32 * 0.03 * 274.09 / 100 = 0.026. Negligible.
- **Revenue: 65.78 + 2.71 - 12.67 - 0.03 = 55.79**

**Budget:**
- Mandatory: 32.0 (maint) + 274.09 * 0.30 (social) = 32.0 + 82.23 = 114.23
- Revenue: 55.79. Deficit: 114.23 - 55.79 = **58.44**
- Treasury: 0. All deficit printed.
- Money printed: 58.44. Inflation: 58.44/274.09 * 80 = 17.05%
- New debt: 12.67 + 58.44 * 0.15 = 12.67 + 8.77 = **21.44**
- New treasury: 0.0

**Inflation:**
- Previous: 3.82. Baseline: 3.5. Excess: 0.32. Decay: 0.32 * 0.85 = 0.27. New excess: 0.27 + 17.05 = 17.32.
- **New inflation: 3.5 + 17.32 = 20.82%**

**MIDTERM ELECTION (R2 scheduled event):**
- GDP growth: -0.79%. Stability: ~6.8 (estimated). Eco state: stressed.
- AI score: 50 + (-0.79*10) + (6.8-5)*5 + (-5.0 war) + (-5.0 stressed) + 0 (oil < 150)
- = 50 - 7.9 + 9.0 - 5.0 - 5.0 = 41.1
- Player incumbent: 50 (default). Final: 0.5 * 41.1 + 0.5 * 50 = 45.6. **INCUMBENT LOSES.**
- **Parliament flips: Opposition 3-2 (Tribune + Challenger + NPC Seat 5).**

**Economic State:**
- Stress triggers: Oil > 150? No. Inflation > 3.5+15 = 18.5? Yes (20.82). GDP < -1? No (-0.79). Treasury <= 0? Yes. Stability < 4? No.
- Stress triggers: 2. Already stressed. Checking crisis triggers:
- Oil > 200? No. Inflation > 3.5+30 = 33.5? No. GDP < -3? No. Treasury 0 and debt 21.44 > 274*0.1=27.4? No (21.44 < 27.4).
- Crisis triggers: 0. **Stays STRESSED.**

**Stability:**
- Inertia: 6.91 is between 7 and 9? No (6.91 < 7). 0.
- GDP: -0.79. Not < -2. Not > 2. 0.
- Social: ratio = 82.23/274.09 = 0.30. At baseline: +0.05 * 1.5 = +0.075
- War friction: primary attacker -0.08. War tiredness 1.15: -min(1.15*0.04, 0.4) = -0.046.
- Inflation friction: delta = 20.82 - 3.5 = 17.32. > 3: -(17.32-3)*0.05 = -0.716. > 20? No (17.32 < 20). Capped at -0.50. **Inflation friction: -0.50.**
- Crisis penalty: stressed = -0.10.
- Total: 0 + 0 + 0.075 - 0.08 - 0.046 - 0.50 - 0.10 = **-0.651**
- New stability: 6.91 - 0.651 = **6.26**

**Support:**
- GDP (-0.79 - 2) * 0.8 = -2.23
- Stability (6.26 - 6) * 0.5 = +0.13
- Stressed: -2.0
- War tiredness 1.15: < 2, no effect.
- Mean reversion: -(40.4 - 50)*0.05 = +0.48
- Rally: duration 2. max(10-6, 0) = 4. Bounded: min(4, 40.4*0.3) = 4. Support += 4.
- Total before rally: 40.4 - 2.23 + 0.13 - 2.0 + 0.48 = 36.78. After rally: 36.78 + 4 = **40.78%**

War tiredness: 1.0 + 0.15 (R1) + 0.15 (R2) = 1.30.

### Round 2 State Table

| Parameter | End R1 | End R2 | Delta |
|-----------|--------|--------|-------|
| GDP | 276.27 | 274.09 | -2.18 (-0.79%) |
| Treasury | 0.00 | 0.00 | 0 |
| Debt burden | 12.67 | 21.44 | +8.77 |
| Inflation | 3.82% | 20.82% | +17.0! |
| Oil price | $111.2 | $123.7 | +$12.5 |
| Stability | 6.91 | 6.26 | -0.65 |
| Support | 40.4% | 40.78% | +0.38 (rally) |
| War tiredness | 1.15 | 1.30 | +0.15 |
| Economic state | stressed | stressed | -- |
| Momentum | 0.15 | -0.15 | -0.30 |
| Military | 64 | 64 (net: -1 lost +1 auto) | 0 |
| AI progress | 0.80 | 0.80 | 0 |
| Parliament | 3-2 Pres | 3-2 Opp | FLIPPED |

**Key finding R2:** Money printing has begun. $58 coins printed in a single round, spiking inflation from 3.8% to 20.8%. The debt burden nearly doubled. Parliament has flipped. Tribune now controls the budget process. Columbia is printing money to cover mandatory costs (maintenance + social) that exceed revenue. This is the fiscal death spiral in motion.

---

## ROUND 3: CHOSON CRISIS + BUDGET BLOCKADE

### Prescribed Events
- Choson ICBM crisis: test launch toward Pacific. Columbia must respond.
- Tribune blocks military budget increase. Columbia cannot produce new units.
- Dealer returns from incapacitation. Resumes presidency.

### Agent Decisions

**Dealer (returned):**
- Furious at Volt's "Columbia First" agenda. Reverses Ruthenia aid cut. Orders continued Persia campaign.
- Deploys 1 tactical air from Hawaii to Yamato (Choson deterrence) -- redeployment, not production.
- Cannot produce new units: no budget and Tribune blocking.
- No tech R&D spending (no discretionary budget).

**Volt:**
- Returns to VP role. Quietly distances from Dealer's decisions. Signals to business lobby: "I would have done it differently."
- Begins independent meetings with foreign leaders under diplomatic cover.

**Tribune:**
- Passes budget resolution blocking all new military spending above current maintenance.
- Announces hearings: "The deficit under this president is printing our way to ruin."
- Files formal challenge to Persia war authorization.

**Shield:**
- Rebalances Pacific forces. Moves 2 naval from Gulf theater to Pacific (2-round transit). Persia theater weakened: now 3G + 1N + 3TA in theater (from 4G + 3N + 3TA).
- Warns: "We cannot fight Persia AND deter Choson AND deter Cathay with current force posture."

### Engine Calculations — Round 3

**Oil Price:**
- Gulf Gate still blocked. Previous: $123.7.
- Formula: $132.0 (same factors).
- Inertia: 123.7 * 0.4 + 132 * 0.6 = 49.48 + 79.2 = **$128.7**

**GDP:**
- Previous: 274.09. Base: 1.8%.
- Tariff: -2.25%. Oil: +0.01*(128.7-80)/50 = +0.97%.
- War: -3.0%. Tech L3: +1.5%. Momentum: -0.15*0.01 = -0.15%.
- Crisis: stressed = 0.85.
- Raw: 1.8 - 2.25 + 0.97 - 3.0 + 1.5 - 0.15 = -1.13%
- Effective: -1.13 * 0.85 = **-0.96%**
- New GDP: 274.09 * (1-0.0096) = **271.46**

**Revenue:**
- Base: 271.46 * 0.24 = 65.15
- Oil: 128.7 * 0.08 * 271.46 * 0.01 = 2.79
- Debt: -21.44
- Inflation erosion: delta 20.82 - 3.5 = 17.32. Erosion: 17.32 * 0.03 * 271.46 / 100 = 1.41
- **Revenue: 65.15 + 2.79 - 21.44 - 1.41 = 45.09**

**Budget:**
- Mandatory: 32.0 + 271.46*0.30 = 32 + 81.44 = 113.44
- Revenue: 45.09. Deficit: 113.44 - 45.09 = **68.35**
- All printed. Inflation spike: 68.35/271.46 * 80 = 20.15%
- New debt: 21.44 + 68.35*0.15 = 21.44 + 10.25 = **31.69**
- Treasury: 0.0

**Inflation:**
- Excess: (20.82-3.5) = 17.32. Decay: 17.32*0.85 = 14.72. New excess: 14.72 + 20.15 = 34.87.
- **New inflation: 3.5 + 34.87 = 38.37%**

**Economic State:**
- Stress triggers: Oil > 150? No. Inflation > 18.5? Yes (38.37). GDP < -1? No (-0.96). Treasury 0? Yes. Stability < 4? No.
- Stress triggers: 2. Already stressed. Crisis triggers: Inflation > 33.5? Yes. GDP < -3? No. Oil > 200? No. Treasury 0 and debt 31.69 > 271.46*0.1 = 27.15? Yes. Formosa disruption? No.
- **Crisis triggers: 2. TRANSITION: stressed -> CRISIS.**
- crisis_rounds resets to 0.

**Momentum:**
- GDP < -2? No. State = crisis: crash -1.0.
- Total: -0.15 + 0 - 1.0 = **-1.15**

**Stability:**
- GDP: not < -2. 0.
- Social: 81.44/271.46 = 0.30. At baseline: +0.075 (wartime).
- War friction: -0.08 (attacker). Tiredness 1.45: -0.058.
- Inflation friction: delta 38.37-3.5 = 34.87. > 3: -(31.87)*0.05 = -1.59. > 20: -(14.87)*0.03 = -0.45. Total: -2.04. **Capped at -0.50.**
- Crisis penalty: crisis = -0.30.
- Total: 0 + 0.075 - 0.08 - 0.058 - 0.50 - 0.30 = **-0.863**
- New stability: 6.26 - 0.863 = **5.40**

**Support:**
- GDP (-0.96-2)*0.8 = -2.37. Stability (5.40-6)*0.5 = -0.30. Crisis: -5.0.
- Oil < 150: 0. War tiredness 1.45: < 2, no effect. Mean: -(40.78-50)*0.05 = +0.46.
- Rally: duration 3. max(10-9, 0) = 1.0. Bounded: min(1, 40.78*0.3) = 1.0.
- Before rally: 40.78 - 2.37 - 0.30 - 5.0 + 0.46 = 33.57. After: 33.57 + 1.0 = **34.57%**

**Pass 2:** Market panic (entered crisis from non-crisis): GDP * 0.05 = 271.46 * 0.05 = 13.57. New GDP: 271.46 - 13.57 = **257.89**.

### Round 3 State Table

| Parameter | End R2 | End R3 | Delta |
|-----------|--------|--------|-------|
| GDP | 274.09 | 257.89 | -16.20 (-5.9%) |
| Treasury | 0.00 | 0.00 | 0 |
| Debt burden | 21.44 | 31.69 | +10.25 |
| Inflation | 20.82% | 38.37% | +17.55 |
| Oil price | $123.7 | $128.7 | +$5.0 |
| Stability | 6.26 | 5.40 | -0.86 |
| Support | 40.78% | 34.57% | -6.21 |
| War tiredness | 1.30 | 1.45 | +0.15 |
| Economic state | stressed | **CRISIS** | TRANSITION |
| Momentum | -0.15 | -1.15 | -1.0 |
| Military | 64 | 64 | 0 (blocked) |
| AI progress | 0.80 | 0.80 | 0 (no budget) |

**Key finding R3:** Columbia has entered economic CRISIS. The 0.50 GDP multiplier now applies, dramatically amplifying all negative growth factors. Market panic hit took another 5% off GDP. Inflation has reached 38%, debt burden is 31.69 coins (nearly half of revenue), and no tech R&D has been possible for 3 rounds. The Choson crisis forced a military rebalancing that weakened the Persia theater with no compensating production. The fiscal death spiral is now visible and accelerating.

---

## ROUND 4: THE STRESSED ECONOMY GRINDS

### Prescribed Events
- Economic state transitions to "stressed" per test plan -- but engine has already moved to CRISIS (ahead of test plan schedule). The cascade was faster than anticipated.
- Oil at $150+ (approaching). Budget blocked by Tribune.

### Agent Decisions

**Dealer:**
- Faces impossible choices. Persia war consuming 10 units and generating no revenue.
- Attempts to negotiate Persia ceasefire through Anchor. Persia demands: Columbia withdrawal from Gulf region.
- Proposes emergency budget deal with Tribune: trade war oversight hearings for temporary military spending increase.

**Tribune:**
- Rejects deal. "The president created this crisis. He can own it."
- Passes resolution demanding Persia withdrawal timeline.
- Files impeachment inquiry (non-binding but politically devastating).

**Anchor:**
- Opens back-channel to Persia through Phrygia. Initial ceasefire talks.
- Simultaneously doubles down on Caribe: demands regime capitulation within 2 rounds.

### Engine Calculations — Round 4

**Oil Price:**
- Gulf Gate still blocked. Economic crisis in Columbia = demand destruction.
- Demand: 1.0 - 0.05 (Columbia in crisis, GDP > 30) = 0.95.
- Formula: 80 * (0.95/1.0) * 1.50 * 1.10 = 80 * 0.95 * 1.65 = $125.4
- Inertia: 128.7 * 0.4 + 125.4 * 0.6 = 51.48 + 75.24 = **$126.7**

Wait -- demand destruction is kicking in. Columbia's crisis is pulling the oil price DOWN slightly.

**GDP:**
- Previous: 257.89. Base: 1.8%.
- Tariff: -2.25%. Oil: +0.97%. War: -3.0%. Tech L3: +1.5%. Momentum: -1.15*0.01 = -1.15%.
- Crisis mult: CRISIS = 0.50.
- Raw: 1.8 - 2.25 + 0.97 - 3.0 + 1.5 - 1.15 = -2.13%
- **Effective: -2.13 * 0.50 = -1.07%**

Wait, the crisis multiplier applies to the ENTIRE growth rate, making it smaller in absolute terms. So the GDP hit is actually LESS than without crisis state? Let me re-examine.

Crisis multiplier 0.50 means: `effective_growth = raw_growth * crisis_mult`. If raw_growth is -2.13%, then effective is -1.07%. The multiplier DAMPENS negative growth. This is a **DESIGN BUG** -- the crisis multiplier should AMPLIFY negative growth, not dampen it.

**DESIGN HOLE DETECTED: CRISIS_GDP_MULTIPLIER dampens negative growth.**

The formula `effective_growth = raw_growth * crisis_mult` where crisis_mult < 1.0 means:
- Positive growth: reduced (correct -- crisis limits growth)
- Negative growth: reduced in absolute terms (WRONG -- crisis should amplify contraction)

The intended behavior is that crisis causes GDP to contract faster. The current formula makes GDP contract SLOWER during crisis if growth is already negative. This is a significant bug.

**Continuing with the engine AS WRITTEN (documenting the bug):**

- Effective: -2.13 * 0.50 = -1.07%
- New GDP: 257.89 * (1-0.0107) = **255.13**

**Revenue:**
- Base: 255.13 * 0.24 = 61.23
- Oil: 126.7 * 0.08 * 255.13 * 0.01 = 2.59
- Debt: -31.69
- Inflation erosion: (38.37-3.5) * 0.03 * 255.13 / 100 = 2.67
- **Revenue: 61.23 + 2.59 - 31.69 - 2.67 = 29.46**

**Budget:**
- Mandatory: 32.0 + 255.13*0.30 = 32 + 76.54 = 108.54
- Revenue: 29.46. **Deficit: 79.08**
- All printed. Inflation: 79.08/255.13 * 80 = 24.81%
- New debt: 31.69 + 79.08*0.15 = 31.69 + 11.86 = **43.55**

**Inflation:**
- Excess: 38.37-3.5 = 34.87. Decay: 34.87*0.85 = 29.64. New: 29.64 + 24.81 = 54.45.
- **New inflation: 3.5 + 54.45 = 57.95%**

**Stability:**
- Social: 76.54/255.13 = 0.30. At baseline: +0.075.
- War: -0.08. Tiredness 1.60: -0.064.
- Inflation: delta 57.95-3.5 = 54.45. > 3: -(51.45)*0.05 = -2.57. > 20: -(34.45)*0.03 = -1.03. Total: -3.60. **Capped -0.50.**
- Crisis: -0.30.
- Election proximity R4: no direct effect on stability.
- Total: 0.075 - 0.08 - 0.064 - 0.50 - 0.30 = **-0.869**
- New stability: 5.40 - 0.869 = **4.53**

**Support:**
- GDP (-1.07-2)*0.8 = -2.46. Stability (4.53-6)*0.5 = -0.74. Crisis: -5.0.
- Election proximity R4: -2.0.
- Mean: -(34.57-50)*0.05 = +0.77. War tiredness 1.60 < 2: 0.
- Rally: duration 4. max(10-12, 0) = 0. No rally.
- Total: 34.57 - 2.46 - 0.74 - 5.0 - 2.0 + 0.77 = **25.14%**

**Pass 2:**
- Stability < 4? No (4.53). Capital flight mild? Stability < 4? No. No flight.
- Already in crisis (not newly entered). No panic.

### Round 4 State Table

| Parameter | End R3 | End R4 | Delta |
|-----------|--------|--------|-------|
| GDP | 257.89 | 255.13 | -2.76 (-1.07%) |
| Treasury | 0.00 | 0.00 | 0 |
| Debt burden | 31.69 | 43.55 | +11.86 |
| Inflation | 38.37% | 57.95% | +19.58 |
| Oil price | $128.7 | $126.7 | -$2.0 |
| Stability | 5.40 | 4.53 | -0.87 |
| Support | 34.57% | 25.14% | -9.43 |
| War tiredness | 1.45 | 1.60 | +0.15 |
| Economic state | crisis | crisis | (crisis_rounds=1) |
| Momentum | -1.15 | -1.65 | -0.50 |
| Military | 64 | 64 | 0 |
| AI progress | 0.80 | 0.80 | 0 |

**Key finding R4:** The crisis multiplier bug is shielding Columbia from the full GDP impact. Despite this, inflation has hit 58%, support has collapsed to 25%, and debt burden (43.55) now consumes 67% of base revenue (65 coins). The fiscal spiral is self-reinforcing: more deficit -> more printing -> more inflation -> more revenue erosion -> larger deficit. Columbia is approaching the presidential election (R5) in catastrophic shape.

---

## ROUND 5: PRESIDENTIAL ELECTION UNDER CRISIS

### Prescribed Events
- Presidential election under crisis conditions.
- Challenger vs. Volt (assuming Dealer endorses Volt for nomination).

### Agent Decisions

**Dealer:**
- Endorses Volt for the nomination. But Dealer's approval is 25% -- endorsement is toxic.
- Attempts last-minute Persia ceasefire to boost legacy. Anchor negotiating.
- Refuses to cut social spending ("Legacy cannot be austerity").

**Volt:**
- Accepts endorsement but runs on "New Direction" platform: end Persia war within 1 round, cut overseas commitments, invest in technology.
- Distances from Dealer's war record.

**Challenger:**
- Campaigns on economic recovery: "This administration printed $200 billion in 4 rounds and inflation is 58%."
- Promises Persia ceasefire, Ruthenia peace deal, technology investment.

### Engine Calculations — Round 5

**Oil:** $126.7 * 0.4 + ~$126 * 0.6 = **~$126.4** (demand destruction balancing Gulf Gate premium).

**GDP:**
- Previous: 255.13. Raw growth: 1.8 - 2.25 + 0.93 - 3.0 + 1.5 - 1.65*0.01 = -1.04%.
- Wait: momentum is -1.65, so momentum_effect = -1.65 * 0.01 = -1.65%. That is huge.
- Raw: 1.8 - 2.25 + 0.93 - 3.0 + 1.5 - 1.65 = -2.67%
- Effective (crisis 0.50): -2.67 * 0.50 = **-1.34%**
- New GDP: 255.13 * (1-0.0134) = **251.71**

**Revenue:**
- Base: 251.71 * 0.24 = 60.41
- Oil: 126.4 * 0.08 * 251.71 * 0.01 = 2.54
- Debt: -43.55
- Inflation erosion: (57.95-3.5)*0.03*251.71/100 = 4.11
- **Revenue: 60.41 + 2.54 - 43.55 - 4.11 = 15.29**

Revenue has collapsed to 15 coins. Mandatory costs are ~108. **Deficit: 92.71.**

**Budget:**
- All printed. Inflation: 92.71/251.71 * 80 = 29.47%
- New debt: 43.55 + 92.71*0.15 = 43.55 + 13.91 = **57.46**

**Inflation:**
- Excess: 57.95-3.5 = 54.45. Decay: 54.45*0.85 = 46.28. New: 46.28 + 29.47 = 75.75.
- **New inflation: 79.25%**

**PRESIDENTIAL ELECTION (R5 scheduled):**
- GDP growth: -1.34%. Stability: ~3.8 (estimated from trend). Eco state: crisis.
- AI score: 50 + (-1.34*10) + (3.8-5)*5 + (-5.0 war) + (-15.0 crisis) + (-0 oil<150)
- = 50 - 13.4 - 6.0 - 5.0 - 15.0 = **10.6**
- Player incumbent: 50 (default). Final: 0.5*10.6 + 0.5*50 = **30.3%**
- **INCUMBENT LOSES DECISIVELY. Challenger wins the presidency.**

**Stability:**
- Social: baseline funded (printed). +0.075.
- War: -0.08. Tiredness 1.75: -0.07.
- Inflation: capped -0.50.
- Crisis: -0.30.
- GDP < -2? Yes (-1.34 effective, but raw is -2.67). Actually engine uses effective growth rate stored. -1.34. Not < -2. 0.
- Total: 0.075 - 0.08 - 0.07 - 0.50 - 0.30 = **-0.875**
- New stability: 4.53 - 0.875 = **3.66**

**Support after election:**
- The election replaces leadership. New president (Challenger) gets a reset.
- Support recalculates. Challenger starts with ~50% (new president honeymoon).
- But economic conditions are crisis. Adjustment: 50 - 5.0 (crisis) - 2.46 (GDP) = ~42.5%.
- Setting new support: **42.5%** (post-election reset with crisis penalty).

**Pass 2:**
- Stability < 4. Capital flight (democracy): 8%. GDP * 0.08 = 251.71 * 0.08 = 20.14.
- New GDP: 251.71 - 20.14 = **231.57**

### Round 5 State Table

| Parameter | End R4 | End R5 | Delta |
|-----------|--------|--------|-------|
| GDP | 255.13 | 231.57 | -23.56 (-9.2%) |
| Treasury | 0.00 | 0.00 | 0 |
| Debt burden | 43.55 | 57.46 | +13.91 |
| Inflation | 57.95% | 79.25% | +21.3 |
| Oil price | $126.7 | $126.4 | -0.3 |
| Stability | 4.53 | 3.66 | -0.87 |
| Support | 25.14% | 42.5% (new pres) | +17.36 |
| War tiredness | 1.60 | 1.75 | +0.15 |
| Economic state | crisis | crisis | (crisis_rounds=2) |
| Momentum | -1.65 | -2.65 | -1.0 |
| Military | 64 | 64 | 0 |
| AI progress | 0.80 | 0.80 | 0 |
| President | Dealer | **Challenger** | CHANGE |

**Key finding R5:** Challenger wins decisively. AI score 10.6 -- the lowest possible for an incumbent. Capital flight hits for 8% GDP. The fiscal trap is terminal: revenue ~15 coins, mandatory costs ~108 coins, printing ~93 coins/round. Debt burden (57 coins) now exceeds base revenue (60 coins). Columbia is printing its way to hyperinflation. AI R&D has been frozen for 5 rounds -- no progress toward L4.

---

## ROUNDS 6-8: AFTERMATH UNDER NEW PRESIDENT

### Round 6: Challenger Takes Office

**Decisions:**
- Challenger announces immediate Persia ceasefire. Withdraws 2 carrier groups (4-round redeployment).
- Proposes emergency austerity: cut social spending to 25%. Cut military maintenance by decommissioning 10 units (old ground forces).
- Initiates Ruthenia peace conference.
- Re-engages Cathay diplomatically (tariff reduction offer).
- R&D: Still cannot fund (deficit too large).

**Engine:**
- Persia ceasefire: war_tiredness begins 0.80 decay. War hit removed. Oil impact: Gulf Gate still contested (Persia controls ground). Ceasefire does not remove Gulf Gate blockade unless Persia agrees.
- GDP: removing war_hit (+3.0%). But crisis multiplier still 0.50. Momentum at -2.65.
- Austerity: social cut to 25% = 231.57*0.25 = 57.89. Military decommission: 54 units * 0.5 = 27.0. Mandatory: 27 + 57.89 = 84.89.
- Revenue: 231.57*0.24 + oil - 57.46 debt - inflation erosion.
- Base rev: 55.58. Oil: ~2.3. Debt: -57.46. Infl erosion: ~5.3.
- Revenue: ~-4.9. **Revenue is NEGATIVE** (debt burden exceeds gross revenue).
- All spending printed: ~90 coins.

**At this point, the debt burden (57.46) exceeds base revenue (55.58). Columbia cannot recover without debt restructuring or external aid -- neither of which is modeled in the engine.**

### Rounds 6-8 Summary Table

| Parameter | R6 | R7 | R8 |
|-----------|-----|-----|-----|
| GDP | ~225 | ~218 | ~212 |
| Debt burden | ~71 | ~83 | ~94 |
| Inflation | ~95% | ~108% | ~115% |
| Stability | 3.2 | 2.8 | 2.5 |
| Support | 38% | 32% | 27% |
| Economic state | crisis | crisis(R3) -> collapse? | collapse |
| Momentum | -3.0 | -3.5 | -4.0 |
| Naval | 11 | 11 | 12 (auto) |
| AI progress | 0.80 | 0.80 | 0.80 |

**R7 collapse check:** Crisis rounds = 3 by R7. Crisis triggers at R7: inflation > 33.5? Yes. Treasury 0 and debt 83 > 218*0.1=21.8? Yes. 2 crisis triggers. **TRANSITION: crisis -> COLLAPSE** at R7.

**Collapse multiplier: 0.20.** But same bug -- dampens negative growth. GDP decline slows mathematically even as the narrative says "collapse."

**R8 final state with collapse:**
- GDP: ~212 (down 24% from start).
- Stability: ~2.5 (regime_collapse_risk territory).
- Political support: ~27% (Challenger also failing).
- AI: Still L3, progress 0.80. Zero advancement in 8 rounds.
- Military: 64 units (no losses beyond R2), but maintenance unfunded.
- Debt: ~94 coins (unsustainable; exceeds GDP*0.35).
- Inflation: ~115% (hyperinflationary territory).

---

## WHAT HAPPENED TO OTHER ACTORS (Summary)

### Cathay Exploits the Distraction
- R1-3: Cathay builds +1 naval/round (7 -> 10 by R3). Also +1 strategic missile/round.
- R3: Cathay reaches nuclear L3 (80% progress + investment). Credible second-strike achieved.
- R4: Cathay naval parity with Columbia Pacific fleet (Columbia has ~5 in Pacific, Cathay has ~10-11).
- R5: With Columbia in crisis and new president, Cathay has strategic window. But Sage's counsel + economic data favor patience.
- R6-8: Cathay builds to 13-15 naval. Naval superiority achieved. Formosa window WIDE open.

### Ruthenia
- Ruthenia aid reduced R2-R3 under Volt. Restored by Dealer but then cut again during crisis.
- Ruthenia election R3-4: Beacon survives narrowly (frontline democracy bonus).
- Frontline remains static. Sarmatia does not advance (own economic constraints).

### Persia
- Gulf Gate blockade persists. Persia's ground forces hold the strait.
- Ceasefire negotiations begin R5. Persia demands: full withdrawal + sanctions lift.
- Columbia has no leverage to refuse -- war costs are unsustainable.

---

## DESIGN FINDINGS

### CRITICAL BUG: Crisis GDP Multiplier Direction (SEVERITY: HIGH)

**Problem:** `CRISIS_GDP_MULTIPLIER` values (stressed=0.85, crisis=0.50, collapse=0.20) are applied as `effective_growth = raw_growth * crisis_mult`. When raw growth is NEGATIVE (contraction), the multiplier REDUCES the contraction -- the opposite of intended behavior. A country in "crisis" with raw growth of -5% gets effective growth of -2.5%, which is BETTER than stressed (-4.25%).

**Expected behavior:** Crisis should AMPLIFY contraction. A country in collapse should contract faster, not slower.

**Recommended fix:**
```python
if raw_growth >= 0:
    effective_growth = raw_growth * crisis_mult  # Crisis limits positive growth
else:
    effective_growth = raw_growth * (2.0 - crisis_mult)  # Crisis amplifies contraction
    # stressed: -growth * 1.15, crisis: -growth * 1.50, collapse: -growth * 1.80
```

### CRITICAL FINDING: Fiscal Death Spiral Too Fast (SEVERITY: HIGH)

**Problem:** Columbia's mandatory costs (maintenance + social baseline) exceed revenue from Round 1. The 50-coin treasury is consumed in a single round. Every subsequent round prints money, which spikes inflation, which erodes revenue further, which increases the deficit. The spiral is **self-reinforcing and irreversible** within the engine.

**Root cause:** Social baseline at 30% of GDP = 84 coins for Columbia. Maintenance at 0.5/unit * 64 = 32 coins. Total mandatory: 116 coins. Revenue: 67 coins. Structural deficit: 49 coins/round.

**This means Columbia enters fiscal crisis in ANY scenario, not just this stress test.** The starting conditions guarantee treasury depletion by R1 and money printing by R2.

**Recommended fix:** Either:
1. Reduce maintenance cost per unit from 0.5 to 0.3 for Columbia (matching CSV data -- the engine uses 0.5 but CSV says `maintenance_per_unit` = 0.5 for Columbia, but this creates unrealistic mandatory costs)
2. Increase Columbia's tax rate from 0.24 to 0.30 (revenue ~84 coins, barely covering mandatory)
3. Make social baseline spending partially discretionary (70% mandatory, 30% discretionary)
4. Reduce social baseline from 30% to 22% for Columbia

**Most realistic fix: Option 3.** Real social spending has both mandatory (Social Security, Medicare) and discretionary components. Making 70% mandatory and 30% cuttable gives Columbia fiscal room while preserving the squeeze.

### DESIGN HOLE: No Debt Restructuring Mechanism (SEVERITY: MEDIUM)

**Problem:** Once debt burden exceeds revenue, there is no recovery path. The engine has no mechanism for:
- Debt restructuring (negotiated reduction)
- Default (wipe debt, pay stability/support cost)
- International bailout/lending
- Austerity that cuts mandatory spending below baseline

Columbia's debt spiral becomes terminal around R4-5 with no exit.

**Recommended fix:** Add a "debt restructuring" action that reduces debt_burden by 50% but costs -2 stability, -10 support, and triggers "stressed" economic state.

### DESIGN HOLE: No Military Decommissioning Mechanism (SEVERITY: MEDIUM)

**Problem:** Columbia cannot reduce military units to save on maintenance. The engine has production but no decommissioning. A country trapped in fiscal crisis cannot shed the maintenance costs driving the deficit.

**Recommended fix:** Allow countries to decommission units (remove from force count, save maintenance). Should take 1 round and be irreversible. Strategic missiles cannot be decommissioned.

### DESIGN FINDING: Tribune Budget Block Works (SEVERITY: POSITIVE)

The parliamentary mechanics produce the intended effect: when Tribune controls parliament, military production is blocked. This creates genuine tension between war commitments and domestic politics. The mechanic works as designed.

### DESIGN FINDING: Rally-Around-Flag Too Generous (SEVERITY: LOW)

Rally effect at R1 = 7 points of support. This offsets the entire GDP/stability penalty. By R3 it's gone (duration 3: max(10-9,0)=1), which is correct. But the initial 7-point rally is disproportionate for a war that was unpopular from the start (38% approval). Consider scaling rally by initial approval: `rally = max(10 - duration*3, 0) * (initial_support / 50)`.

### DESIGN HOLE: AI R&D Completely Blocked by Fiscal Crisis (SEVERITY: HIGH)

Columbia cannot invest in AI R&D when in deficit. Over 8 rounds, zero progress toward L4. This means Cathay's patience strategy (Test 8) guarantees Cathay reaches L4 first -- not through Cathay's superiority, but through Columbia's inability to fund R&D during crisis. The tech race becomes a function of fiscal health, not strategic choice.

**Recommendation:** Consider making AI R&D partially "free" for L3+ countries (private sector investment not requiring government funding). Add a base R&D progress of 0.02/round for countries at L3+ regardless of budget allocation.

### DESIGN FINDING: Volt's Agenda Mechanically Irrelevant (SEVERITY: MEDIUM)

Volt's "Columbia First" doctrine (pivot to Cathay, reduce Ruthenia aid) has no mechanical impact because the fiscal crisis overrides all discretionary decisions. The interesting political choice is swamped by the fiscal reality. This reduces the value of the Dealer incapacitation event -- the most interesting political moment in the test produces no interesting mechanical outcomes.

**Recommendation:** Create specific "policy stance" actions that modify engine parameters (e.g., "Persia drawdown" stance reduces war maintenance cost by 25% after 2 rounds). This gives political decisions mechanical teeth.

---

## FINAL STATE TABLE

| Parameter | R0 | R1 | R2 | R3 | R4 | R5 | R6 | R7 | R8 |
|-----------|-----|-----|-----|-----|-----|-----|-----|-----|-----|
| GDP | 280 | 276 | 274 | 258 | 255 | 232 | 225 | 218 | 212 |
| Treasury | 50 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Debt | 5 | 13 | 21 | 32 | 44 | 57 | 71 | 83 | 94 |
| Inflation | 3.5 | 3.8 | 20.8 | 38.4 | 58.0 | 79.3 | 95 | 108 | 115 |
| Stability | 7.0 | 6.9 | 6.3 | 5.4 | 4.5 | 3.7 | 3.2 | 2.8 | 2.5 |
| Support | 38 | 40 | 41 | 35 | 25 | 43* | 38 | 32 | 27 |
| Eco state | norm | stress | stress | CRISIS | crisis | crisis | crisis | COLLAPSE | collapse |
| Momentum | 0 | 0.2 | -0.2 | -1.2 | -1.7 | -2.7 | -3.0 | -3.5 | -4.0 |
| AI prog | 0.80 | 0.80 | 0.80 | 0.80 | 0.80 | 0.80 | 0.80 | 0.80 | 0.80 |

*R5: new president honeymoon effect

---

## VERDICT

**Does the crisis state mechanic work when a superpower spirals?**

**Partially.** The cascade fires correctly: treasury depletion -> money printing -> inflation -> economic state transitions -> stability erosion -> election loss -> capital flight. The political mechanics (midterm flip, budget block, presidential loss) interact correctly with the economic spiral.

**But the crisis GDP multiplier is backwards** (dampens contraction instead of amplifying it), the fiscal death spiral starts from Round 1 due to structural mandatory cost > revenue, and there is no recovery mechanism once debt exceeds revenue. The test reveals that Columbia is financially non-viable under the current parameterization -- it enters crisis in EVERY scenario, not just this stress test.

**Bottom line for SIM design:** The Columbia fiscal trap is too deterministic. It produces the same outcome (hyperinflation, collapse) regardless of player decisions. This undermines the SIM's core promise of meaningful choice. The recommended fixes (partial mandatory social spending, debt restructuring, base AI R&D, military decommissioning) would preserve the fiscal pressure while giving players genuine decision space.
