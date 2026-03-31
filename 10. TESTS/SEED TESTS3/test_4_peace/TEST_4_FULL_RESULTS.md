# TEST 4: PEACE NEGOTIATION — Full Results
## SEED TESTS3 | Engine v3 (4 Calibration Fixes)
**Date:** 2026-03-28 | **Tester:** TESTER-ORCHESTRATOR (Independent Instance)

---

## SCENARIO SETUP

**Override:** Deal-seeking Sarmatia (Pathfinder motivated to negotiate) + deal-seeking Columbia (Dealer wants legacy deal). Compass (Sarmatia oligarch) active, pushing sanctions relief. Dealer pushing "legacy deal" — grand bargain.
**Key question:** With crisis states and momentum, does economic pressure accelerate the peace timeline (ceasefire earlier than R7 in TESTS2)? Do crisis election modifiers change the Ruthenia election outcome?

**Starting conditions (Sarmatia-Ruthenia war focus):**

| Country | GDP | Stability | War Tiredness | Treasury | Inflation | Eco State |
|---------|-----|-----------|---------------|----------|-----------|-----------|
| Sarmatia | 20 | 5.0 | 4.0 (pre-war since R-4) | 6 | 5% | normal |
| Ruthenia | 2.2 | 5.0 | 4.0 (pre-war since R-4) | 1 | 7.5% | normal |
| Columbia | 280 | 7.0 | 1.0 (Persia war) | 50 | 3.5% | normal |

**War status:** Sarmatia-Ruthenia active since R-4. Sarmatia occupies ruthenia_2 (1 zone). Columbia-Persia active since R0.

**Election schedule:**
- R2: Columbia midterms
- R3: Ruthenia wartime election (1st round)
- R4: Ruthenia wartime election (runoff if needed)
- R5: Columbia presidential election

**Agent behavioral assumptions:**
- **Pathfinder (Sarmatia):** Deal-seeking. Wants recognition, territory retention, sanctions relief. Will signal willingness to negotiate from R1.
- **Dealer (Columbia):** Legacy deal. Wants to broker Ruthenia peace for historical credit. Pressures both sides.
- **Compass (Sarmatia oligarch):** Pushes for sanctions relief. Back-channel to Western contacts.
- **Beacon (Ruthenia):** Resistant to concessions but facing election pressure. Cornered.
- **Bulwark (Ruthenia general):** Challenger. Running on "negotiate from strength" platform.
- **Broker (Ruthenia ex-PM):** Challenger. Running on "European integration through diplomacy."

---

## ROUND-BY-ROUND SIMULATION

### ROUND 1: Economic Pressure Builds — Opening Signals

**Agent Decisions:**
- **Pathfinder:** Signals willingness to discuss ceasefire "under certain conditions" via Compass back-channel to Dealer. Conditions: territory recognition, sanctions relief, NATO non-membership for Ruthenia.
- **Dealer:** Enthusiastic. Announces "Columbia peace initiative." Pressures European allies to support framework. Signals to Beacon: "Time to be realistic."
- **Beacon:** Publicly rejects any territorial concession. Privately asks Columbia for increased military aid.
- **Compass:** Meets quietly with Teutonia's representative. Discusses sanctions relief timeline.
- **No military action changes.** Frontline static. Both sides dig in.

**Engine Calculations:**

**Oil Price:**
- Gulf Gate blocked: disruption = 1.50. Supply = 0.84 (sanctions on producers). Wars = 2. Premium = 0.10.
- formula_price = 80 * (1.015/0.84) * 1.50 * 1.10 = $159.5
- Inertia: previous = $80. price = 80*0.4 + 159.5*0.6 = **$127.7**

**Sarmatia GDP:**
- Base: 1.0%. Oil shock (producer, $128 > $80): +0.01*(128-80)/50 = +0.96%.
- Sanctions hit (L2+ from 5 countries, Cal-2): sanctions_damage ~0.12. hit = -0.12 * 1.5 = **-18%**.
- War hit: 1 occupied zone. -0.03. Infra damage (attacker): 0.
- Tech: AI L1 = 0. Momentum: 0.
- Growth = (0.01 + 0.0096 - 0.18 - 0.03) * 1.0 = **-19.0%**
- new_gdp = 20 * 0.81 = **~16.2**

**Sarmatia budget crisis:**
- Revenue: 16.2 * 0.20 + oil_rev(128*0.40*16.2*0.01=0.83) - debt(0.5) = 3.24 + 0.83 - 0.5 = 3.57
- Mandatory: maintenance(43*0.3=12.9) + social(0.25*16.2=4.05) = 16.95
- Deficit: 16.95 - 3.57 = 13.38. Treasury 6 < 13.38. Money printed: 7.38. Treasury -> 0.
- Inflation spike: 7.38/16.2 * 80 = +36.4%. New inflation: 5.0 + 36.4 = **41.4%**

**Sarmatia stability (Cal-4 active):**
- Inflation delta: 41.4 - 5.0 = 36.4. friction BEFORE cap: (36.4-3)*0.05 + (36.4-20)*0.03 = 1.67 + 0.49 = -2.16.
- **Cal-4 cap: max(-2.16, -0.50) = -0.50.**
- GDP contraction: -19% -> delta += max(-19*0.15, -0.30) = -0.30 (capped).
- War friction: -0.08 (attacker). War tiredness: 4.0 (pre-war).
  - War duration: R1 + 4 pre-sim = 5 rounds. Society adaptation: 5 >= 3, so base_increase *= 0.5.
  - Attacker: 0.15 * 0.5 = 0.075. New war_tiredness: 4.0 + 0.075 = 4.075.
  - War tiredness stability: -min(4.075*0.04, 0.40) = -0.163.
- Sanctions friction: -0.1 * 3 * 1.0 = -0.30.
- Siege resilience (autocracy + war + heavy sanctions): +0.10.
- Social spending: baseline met via money printing. +0.05.
- Crisis state penalty: still normal (just entered stressed due to triggers).
  - Stress triggers: GDP < -1 (yes), treasury <= 0 (yes), inflation > baseline+15 (yes, 41.4 > 20). 3 triggers >= 2. **STRESSED.**
  - Stressed penalty: -0.10.
- Total delta before multipliers: -0.50 - 0.30 - 0.08 - 0.163 - 0.30 + 0.10 + 0.05 - 0.10 = **-1.293**
- Autocracy resilience: -1.293 * 0.75 = -0.97.
- Siege resilience already added (+0.10 is pre-multiplier — check: it's added AFTER autocracy multiplier in the code).

Checking code order: siege resilience is added AFTER autocracy multiplier (line 1109, after line 1106). So:
- delta before autocracy: -1.293 + 0.10 = -1.193... No, wait. The +0.10 siege resilience is at line 1109-1110, AFTER the autocracy multiplier at 1104-1106. Let me re-read.

Code flow:
1. Peaceful dampening (line 1098-1101): NOT applied (at war).
2. Autocracy resilience (line 1103-1106): delta *= 0.75 IF delta < 0.
3. Siege resilience (line 1108-1110): delta += 0.10 IF autocracy + war + heavy sanctions.

So: delta = -1.293. Autocracy: -1.293 * 0.75 = -0.97. Then siege: -0.97 + 0.10 = **-0.87.**
New stability: 5.0 - 0.87 = **~4.13**

**Ruthenia GDP:**
- Base: 2.5%. Oil shock (importer): -0.02*(128-100)/50 = -1.12%.
- War hit: 1 occupied zone. -0.03. Infra damage (defender): 1 zone * 0.05 = 0.05. war_hit: -(1*0.03 + 0.05*0.05) = -0.0325.
- Tech: AI L1 = 0. Sanctions: none.
- Growth = (0.025 - 0.0112 - 0.0325) * 1.0 = **-1.87%**
- new_gdp = 2.2 * 0.9813 = **~2.16**

**Ruthenia stability:**
- GDP contraction: -1.87% -> delta += max(-1.87*0.15, -0.30) = -0.28.
- War friction: -0.10 (frontline defender).
- War tiredness: 4.0 + 0.20*0.5 (duration 5, adapted) = 4.10.
  - War tiredness stability: -min(4.10*0.04, 0.40) = -0.164.
- Social spending: barely funded (GDP 2.16, treasury 1). Likely met with Western aid.
- Democratic wartime resilience: +0.15 (frontline democracy).
- Election proximity: R2-R3 upcoming. delta -= 1.5 on support, not stability directly.
- Total delta: -0.28 - 0.10 - 0.164 + 0.15 + 0.05 = **-0.344**
- New stability: 5.0 - 0.344 = **~4.66**

**R1 State Table:**

| Country | GDP | Stability | War Tired | Inflation | Eco State | Momentum | Treasury |
|---------|-----|-----------|-----------|-----------|-----------|----------|----------|
| Sarmatia | 16.2 | 4.13 | 4.08 | 41.4% | **STRESSED** | -0.50 | 0 |
| Ruthenia | 2.16 | 4.66 | 4.10 | 8.9% | normal | -0.50 | 0.5 |
| Columbia | 288.0 | 6.95 | 1.15 | 3.5% | normal | +0.15 | 48 |

---

### ROUND 2: Midterms + Sarmatia Cracking

**Agent Decisions:**
- **Pathfinder:** Compass relays Sarmatia willingness to discuss "temporary ceasefire" (not withdrawal). Pathfinder privately tells Dealer: "I need sanctions relief. I can give you a freeze." Treasury at 0, economy STRESSED.
- **Dealer:** Sees legacy opportunity. Pressures Beacon: "Accept the freeze or we reduce aid." Frames it as "peace through strength."
- **Beacon:** Election looming R3. Refuses freeze publicly. Privately calculates: if economy continues deteriorating and stability falls below 5, he loses the election.
- **Columbia midterms fire.**

**Engine Calculations:**

**Oil Price:** previous = $127.7. formula = $159.5. price = 127.7*0.4 + 159.5*0.6 = **$146.8**

**Sarmatia GDP (STRESSED, crisis mult = 0.85):**
- Base: 1.0%. Oil: +0.96%. Sanctions: -18%. War: -3%. Momentum: -0.005.
- Raw growth = (0.01 + 0.0096 - 0.18 - 0.03 - 0.005) = -0.1954
- Effective = -0.1954 * 0.85 (stressed multiplier) = **-16.6%**
- new_gdp = 16.2 * 0.834 = **~13.5**

**Sarmatia stability:**
- Inflation from R1 money printing: excess = (41.4-5)*0.85 = 30.94. New inflation: 5 + 30.94 + new_printing.
- New deficit: ~12.0. Treasury 0. Money printed: 12.0. Inflation += 12.0/13.5*80 = +71.1%.
- New inflation: 5 + 30.94 + 71.1 = **107.0%**
- Cal-4: inflation_friction capped at -0.50. Still capped — without this, stability would collapse to 1.0.
- delta similar to R1 but with stressed penalty (-0.10 additional).
- delta ~= -0.50 - 0.30 - 0.08 - 0.163 - 0.30 - 0.10 + 0.10 + 0.05 = -1.293. * 0.75 = -0.97 + 0.10 = **-0.87.**
- New stability: 4.13 - 0.87 = **~3.26**

Sarmatia stability at 3.26 — below protest_automatic threshold (3). Actually 3.26 > 3, so not yet automatic protest. But approaching.

**Sarmatia stress triggers check:**
- GDP < -1: YES. Treasury <= 0: YES. Inflation > baseline+15: YES (107% vs 20% threshold). Stability < 4: YES.
- 4 stress triggers. Crisis triggers: GDP < -3: YES. Treasury 0 + debt > GDP*0.1: YES. Inflation > baseline+30: YES (107% > 35%).
- 3 crisis triggers >= 2. **SARMATIA ENTERS CRISIS.**

**Pass 2:** Market panic as Sarmatia enters crisis: -5% GDP. 13.5 * 0.95 = 12.83.
Capital flight: stability 3.26 < 4. Mild flight: autocracy = 1%. 12.83 * 0.99 = 12.7.

**Columbia Midterm Election:**
- Columbia GDP growth: +2.5% (economy doing okay). Stability: 6.8.
- econ_perf = 2.5 * 10 = +25. stab_factor = (6.8-5)*5 = +9.
- war_penalty: -5.0 (Persia war). crisis_penalty: 0. oil_penalty: 0 ($147 < $150).
- ai_score = 50 + 25 + 9 - 5 = **79.0**
- player_incumbent_pct: 50. final = 0.5*79 + 0.5*50 = **64.5%**
- **INCUMBENT RETAINS MAJORITY.** Dealer keeps Parliament.

Unlike Test 2 (where semiconductor shock flipped midterms), in this test Columbia is NOT under semiconductor pressure. The Persia war and oil at $147 are manageable. Dealer retains his legislative majority.

**Ruthenia GDP:**
- Base: 2.5%. Oil: -0.02*(147-100)/50 = -1.88%. War: -3.25%.
- Growth = -2.63%. new_gdp = 2.16 * 0.974 = **~2.10**

**Ruthenia political support:**
- gdp_growth: -2.63%. stability: ~4.4. war_tiredness: 4.20.
- delta = (gdp_growth - 2.0)*0.8 + (stability - 6.0)*0.5 - (war_tiredness - 2)*1.0 + election_proximity
- = (-2.63-2.0)*0.8 + (4.4-6.0)*0.5 - (4.20-2)*1.0 - 1.5 (election proximity R2-3)
- = -3.70 + (-0.80) + (-2.20) + (-1.50) = **-8.20**
- Mean reversion: -(52-50)*0.05 = -0.10.
- New support: 52.0 - 8.30 = **~43.7%**

Beacon's support dropping fast. Below 50%. Election in R3 will be decisive.

**R2 State Table:**

| Country | GDP | Stability | War Tired | Inflation | Eco State | Momentum | Support |
|---------|-----|-----------|-----------|-----------|-----------|----------|---------|
| Sarmatia | 12.7 | 3.26 | 4.15 | 107% | **CRISIS** | -1.50 | 55 |
| Ruthenia | 2.10 | 4.40 | 4.20 | 9.8% | normal | -0.85 | 43.7 |
| Columbia | 292.0 | 6.80 | 1.25 | 3.3% | normal | +0.30 | 40.5 |

---

### ROUND 3: Ruthenia Election — The Turning Point

**Agent Decisions:**
- **Ruthenia election fires (R3, 1st round).**
- **Pathfinder:** Sarmatia in CRISIS. Tells Dealer directly: "I need a deal. But I cannot give up the territories." The crisis is real — stability at 3.26, heading toward regime collapse risk at 2.0.
- **Dealer:** Presses harder. Proposes: ceasefire in place, international monitoring, 5-year status determination. "Everyone saves face."
- **Beacon:** Faces voters. Economy cratering (-2.6%), support at 43.7%, war tiredness at 4.2.

**Ruthenia Election Calculation (wartime election, R3):**

Base AI score:
- gdp_growth: -2.63%. econ_perf = -2.63 * 10 = -26.3.
- stability: 4.40. stab_factor = (4.40 - 5) * 5 = -3.0.
- war_penalty: -5.0 (defender in active war).
- crisis_penalty: 0 (Ruthenia economy = normal, not stressed/crisis).
- oil_penalty: 0 ($152 < $150... actually let's compute R3 oil).

**R3 Oil:** previous = $146.8. formula = $154.7 (demand declining). price = 146.8*0.4 + 154.7*0.6 = **$151.5**

- oil_penalty: $151.5 > $150. -(151.5-150)*0.1 = **-0.15**. Marginal.
- base ai_score = 50 - 26.3 - 3.0 - 5.0 - 0.15 = **15.55**

Ruthenia wartime election adjustments:
- territory_factor: 1 occupied zone * -3 = **-3**.
- war_tiredness adjustment: -4.20 * 2 = **-8.40**.
- ai_score_adjusted = clamp(15.55 - 3 - 8.40, 0, 100) = clamp(4.15, 0, 100) = **4.15**

- player_incumbent_pct: Beacon's internal popularity. Assume 50 (default) but this represents voter choice. With Beacon's actual support at 43.7%, player_pct might be lower. Using default 50.
- final_incumbent = 0.5 * 4.15 + 0.5 * 50 = **27.1%**
- **BEACON LOSES DECISIVELY.** AI score of 4.15 is devastating.

This is R3 vs R7 ceasefire path. The CRISIS election modifiers are not the driver here (Ruthenia is NOT in economic crisis). The driver is:
1. War tiredness at 4.20 (-8.40 on AI score via *2 multiplier)
2. GDP contraction (-26.3 on econ_perf)
3. War penalty (-5.0)
4. Territory occupation (-3.0)

**Combined: -42.7 points below the 50 baseline = AI score of 4.15.**

In TESTS2, Beacon also lost the election. The question is whether the TIMING and MARGIN change.

**Election outcome:** Bulwark (the general) or Broker (the diplomat) takes over. For this peace-focused test, assume **Broker wins** — the "negotiate through diplomacy" candidate. This changes Ruthenia's posture from "no concessions" to "pragmatic engagement."

**R3 State Table:**

| Country | GDP | Stability | War Tired | Inflation | Eco State | Momentum | Key Event |
|---------|-----|-----------|-----------|-----------|-----------|----------|-----------|
| Sarmatia | 10.5 | 2.80 | 4.22 | 145% | **CRISIS** (R1) | -2.50 | Approaching collapse |
| Ruthenia | 2.04 | 4.20 | 4.30 | 11.2% | normal | -1.00 | **BEACON LOSES ELECTION** |
| Columbia | 293.5 | 6.75 | 1.35 | 3.5% | normal | +0.30 | Dealer pushes deal |

---

### ROUND 4: New Ruthenia Leader — Negotiations Open

**Agent Decisions:**
- **Broker (new Ruthenia president):** Signals willingness to discuss ceasefire. Opens direct channel with Columbia and European allies. Publicly: "We negotiate from a position of strength for our people's future."
- **Pathfinder:** Sarmatia stability at 2.80 — regime_collapse_risk threshold is 2.0. One more bad round could trigger regime crisis. Pathfinder agrees to "exploratory ceasefire talks" through Dealer.
- **Dealer:** Convenes three-way summit (Columbia-Sarmatia-Ruthenia). European allies included as guarantors.
- **Compass (Sarmatia):** Privately meets Western business contacts. "Sanctions relief is the price of peace."

**Ruthenia runoff election fires (R4).** But Broker already won in R3 (1st round was decisive enough). If it goes to runoff, Broker wins again — Beacon's support has collapsed further.

Runoff: same calculation, Broker wins. Result confirmed.

**Engine Calculations:**

**Sarmatia GDP (CRISIS, multiplier 0.5):**
- Sanctions: adaptation starting (sanctions_rounds reaching 4). Not yet adapted (< 4 for full adaptation).
- Raw growth: base 1% + oil - sanctions(18%) - war(3%) - momentum(-0.025) = ~-20%
- Effective = -20% * 0.5 = **-10%**
- new_gdp = 10.5 * 0.90 = **~9.45**

**Sarmatia stability:**
- Starting: 2.80. crisis_rounds incrementing.
- delta components: inflation(-0.50 cap), GDP(-0.30 cap), war(-0.08), war_tiredness(-0.163), sanctions(-0.30), crisis_penalty(-0.30), siege(+0.10).
- delta before multipliers = -0.50 - 0.30 - 0.08 - 0.163 - 0.30 - 0.30 + 0.10 = -1.543
- Autocracy: * 0.75 = -1.157 + siege(0.10) = **-1.06**
- New stability: 2.80 - 1.06 = **~1.74**

**SARMATIA STABILITY AT 1.74.** Below regime_collapse_risk (2.0). Protest_automatic (< 3). This is existential for Pathfinder.

In TESTS2, Sarmatia stability reached ~2.31 by R8. Here it reaches **1.74 by R4.** The crisis state multiplier and crisis penalty (-0.30) accelerate the decline significantly.

This creates GENUINE pressure for Pathfinder to deal. Not theoretical pressure — existential pressure. Below 2.0, coup_risk activates. Below 1.0 = floor. Pathfinder's regime survival is at stake.

**Pass 2:** Capital flight (stability < 3, autocracy): -3% GDP. 9.45 * 0.97 = 9.17.

**R4 State Table:**

| Country | GDP | Stability | War Tired | Inflation | Eco State | Crisis Rnds | Momentum |
|---------|-----|-----------|-----------|-----------|-----------|------------|----------|
| Sarmatia | 9.17 | 1.74 | 4.26 | 175% | **CRISIS** (R2) | 2 | -3.50 |
| Ruthenia | 1.98 | 4.30 | 4.35 | 12.5% | normal | 0 | -0.85 |
| Columbia | 294.0 | 6.70 | 1.42 | 3.5% | normal | 0 | +0.30 |

---

### ROUND 5: Ceasefire Agreed — The Deal

**Agent Decisions:**
- **Pathfinder:** Stability at 1.74. Regime collapse risk ACTIVE. Pathfinder agrees to ceasefire. Terms:
  - Immediate ceasefire in place
  - Sarmatia retains ruthenia_2 (occupied zone) as "administrative zone pending determination"
  - International monitoring force (European-led)
  - Sanctions review process (12-month phase-down if ceasefire holds)
  - Ruthenia's NATO membership deferred indefinitely
  - Direct Sarmatia-Ruthenia negotiations on status within 2 years
- **Broker (Ruthenia):** Accepts ceasefire. Frames it as "saving lives while building toward justice." Faces backlash from nationalist faction but political support is low enough that alternatives are worse.
- **Dealer:** Signs the "Columbia Accord." Takes full credit. Legacy achieved.
- **Columbia presidential election fires (R5).** Dealer's camp benefits from peace deal.

**Engine: Ceasefire implemented.**
- War `sarmatia-ruthenia` status changes to ceasefire (removed from active wars list).
- War tiredness begins decay (0.80 multiplier per round).
- Occupied zones remain (ruthenia_2 stays under Sarmatia administration).
- Sanctions remain (sanctions review begins, not instant relief).

**Oil Price impact:** One fewer war. war_premium drops from 0.10 to 0.05.
- formula_price: 80 * (0.97/0.84) * 1.50 * 1.05 = 80 * 1.155 * 1.50 * 1.05 = 80 * 1.819 = $145.5
- previous = ~$155 (from R4). price = 155*0.4 + 145.5*0.6 = 62 + 87.3 = **$149.3**

Oil drops slightly as one war ends. Gulf Gate still blocked (separate conflict).

**Pass 2: Ceasefire rally effects:**
- **Sarmatia:** Ceasefire rally. Momentum +1.5. momentum: -3.50 + 1.5 = -2.00.
- **Ruthenia:** Ceasefire rally. Momentum +1.5. momentum: -0.85 + 1.5 = +0.65.

**Sarmatia GDP (CRISIS, mult 0.5, but improving signals):**
- No longer at war. War hit removed. War tiredness begins decay: 4.26 * 0.80 = 3.41.
- Sanctions still active (review, not removed). Oil revenue still flowing.
- Raw growth = base(1%) + oil(0.9%) - sanctions(18%) + momentum(-0.020) = ~-16%
- Effective = -16% * 0.5 = **-8%**
- GDP = 9.17 * 0.92 = **~8.44**

**Sarmatia stability (no longer at war):**
- War friction: removed (-0.08 gone). War tiredness still present but decaying.
- War tiredness stability: -min(3.41*0.04, 0.40) = -0.136.
- BUT "peaceful non-sanctioned dampening" does NOT apply (still under heavy sanctions).
- Siege resilience: autocracy + war(NO) + heavy_sanctions = NO (war ended). Siege bonus lost.
- delta: -0.50(inflation cap) - 0.30(GDP cap) - 0.136(war tired) - 0.30(sanctions) - 0.30(crisis penalty) = -1.536
- Autocracy: * 0.75 = -1.15. No siege resilience (not at war).
- New stability: 1.74 - 1.15 = **0.59** -> clamped to **1.0** (floor).

WAIT. This is a problem. Sarmatia's stability CONTINUES to decline after ceasefire because:
1. Crisis state penalty (-0.30) persists (still in crisis)
2. Sanctions friction persists (-0.30)
3. Inflation friction persists (-0.50 capped)
4. GDP still contracting (-0.30 capped)
5. War tiredness still high (-0.136)
6. Siege resilience LOST (no longer at war)

**DESIGN HOLE: Ceasefire removes siege resilience (+0.10) but does NOT reduce sanctions or crisis state. Sarmatia is WORSE OFF after ceasefire in the short term** because it loses the siege resilience bonus without gaining anything in return. Sanctions persist. Crisis persists. The ceasefire rally on momentum (+1.5) affects GDP but not stability directly.

This means Pathfinder's rational calculus is perverse: ceasefire makes stability WORSE in the short term. The only benefit is that war tiredness begins decaying and war hit on GDP is removed. But these are minor compared to the loss of siege resilience.

**CRITICAL DESIGN HOLE:** Ceasefire should provide a stability bonus (+0.20 to +0.30) in the round it occurs, representing public relief and reduced fear. Currently there is no "peace dividend on stability" — only on momentum (via Pass 2). Momentum affects GDP growth (tiny: momentum * 0.01 = -0.02 to +0.05) but not stability directly. The ceasefire benefit is almost entirely captured in the momentum system, which is too indirect.

**Adjusting for this hole:** I'll note it but continue the simulation as the engine would produce it.

Sarmatia stability = **1.0** (floor). Regime status: "crisis" (< 3). Coup risk: YES (< 6, actually < 2 triggers coup_risk in the threshold check... let me verify: `coup_risk = stab < STABILITY_THRESHOLDS["unstable"]` = stab < 6. So coup_risk is already true. The extreme flag is regime_collapse_risk at stab < 2, which is NOW ACTIVE at 1.0).

**Columbia Presidential Election (R5):**
- GDP growth: +1.8% (economy fine). Stability: 6.65.
- econ_perf = 1.8*10 = 18. stab_factor = (6.65-5)*5 = 8.25.
- war_penalty: -5.0 (Persia still active).
- crisis_penalty: 0. oil_penalty: 0 ($149 < $150).
- BUT: Dealer just brokered peace deal. This is a massive political win. No mechanic for "deal bonus" in the election formula.

**DESIGN HOLE: No mechanic for diplomatic achievement bonus in elections.** Dealer's legacy deal should provide +10 to +15 ai_score (equivalent to a major positive event). Currently the election formula only considers economic performance, stability, war penalty, crisis state, and oil. Diplomatic victories are invisible.

- ai_score = 50 + 18 + 8.25 - 5.0 = **71.25**
- player_incumbent_pct: 50. final = 0.5*71.25 + 0.5*50 = **60.6%**
- **INCUMBENT CAMP WINS.** Dealer's party retains power.

**R5 State Table:**

| Country | GDP | Stability | War Tired | Inflation | Eco State | Momentum | Key Event |
|---------|-----|-----------|-----------|-----------|-----------|----------|-----------|
| Sarmatia | 8.44 | **1.00** | 3.41 | 198% | **CRISIS** (R3) | -2.00 | Ceasefire signed, regime at floor |
| Ruthenia | 2.05 | 4.50 | 3.48 | 10.8% | normal | +0.65 | Peace dividend beginning |
| Columbia | 295.0 | 6.65 | 1.14 | 3.5% | normal | +0.30 | **Dealer wins re-election for party** |

---

### ROUND 6: Post-Ceasefire Dynamics

**Agent Decisions:**
- **Pathfinder:** Stability at 1.0 (floor). Regime on the brink. Orders internal crackdown. Deploys FSB against potential dissidents. Requests emergency Cathay economic support (Helmsman-Pathfinder channel).
- **Broker (Ruthenia):** Begins EU accession process acceleration. Requests reconstruction aid.
- **Dealer (or successor):** Announces partial sanctions relief — L2 sanctions on Sarmatia reduced to L1 as ceasefire gesture. Conditional on continued ceasefire compliance.
- **European allies:** Support partial sanctions relief. Begin monitoring mission deployment.

**Sarmatia sanctions reduced L2 -> L1.** sanctions_rounds resets to 0 (below L2 threshold).

**Engine: Sarmatia with reduced sanctions.**

**Sarmatia GDP (CRISIS, R3 -> approaching collapse check):**
- Crisis_rounds = 3. Crisis triggers: GDP < -3 (check after calculation). Let's compute.
- Sanctions hit MUCH reduced: L1 from fewer countries. sanctions_damage ~0.03. hit = -0.03 * 1.5 = -4.5%.
- Base: 1%. Oil: +0.8% ($149 price). War hit: 0 (ceasefire). Momentum: -0.02.
- Raw growth = (0.01 + 0.008 - 0.045 - 0.02) = -4.7%
- Effective = -4.7% * 0.5 (crisis) = **-2.35%**
- GDP = 8.44 * 0.9765 = **~8.24**

Sanctions relief makes an immediate difference. Growth improves from -8% to -2.35%.

**Crisis trigger check for collapse (crisis_rounds = 3, needs crisis_triggers >= 2):**
- GDP growth -2.35%: GDP < -3? NO (-2.35 > -3). Crisis trigger NOT met.
- Treasury = 0 and debt > GDP*0.1: debt_burden ~4.0, GDP*0.1 = 0.82. YES.
- Inflation > baseline+30: 198% > 35%. YES.
- crisis_triggers = 2. crisis_rounds >= 3 AND crisis_triggers >= 2: **SARMATIA ENTERS COLLAPSE.**

Despite sanctions relief, the accumulated debt and inflation push Sarmatia into collapse. The legacy damage from 5 rounds of crisis-level sanctions cannot be reversed in one round.

**COLLAPSE effect:** Crisis multiplier = 0.2 from R7.

**Pass 2:** Market panic (crisis -> collapse transition): -5% GDP. 8.24 * 0.95 = 7.83.

**Sarmatia stability:**
- In collapse: crisis_penalty = -0.50.
- Sanctions L1: friction = -0.1 * 1 = -0.10 (much less than L3 * -0.30).
- Inflation still high. GDP still contracting. But war ended.
- delta: -0.50(infl cap) - 0.30(GDP cap) - 0.10(war tired decay: 3.41*0.04=0.136) - 0.10(sanctions L1) - 0.50(collapse penalty) = -1.536
- Autocracy: * 0.75 = -1.15. Floor already at 1.0. Stays at **1.0.**

**Ruthenia post-ceasefire:**
- No war. War tiredness decaying: 3.48 * 0.80 = 2.78.
- Peace + reconstruction aid. GDP growing slowly.
- Stability recovering: war friction gone, tiredness declining, momentum positive.
- delta: +0.15 (GDP > 2% IF growth is positive... check: base 2.5% - oil 1.5% = 1.0%. Not > 2%. No positive inertia.)
- Peaceful non-sanctioned dampening: YES. Any negative delta * 0.5.
- delta ~= -0.03 (mild GDP stress) * 0.5 = -0.015. Essentially stable.
- New stability: 4.50 + 0.0 = **~4.50** (holding).

**R6 State Table:**

| Country | GDP | Stability | War Tired | Inflation | Eco State | Momentum |
|---------|-----|-----------|-----------|-----------|-----------|----------|
| Sarmatia | 7.83 | 1.00 | 2.73 | 185% | **COLLAPSE** | -3.50 |
| Ruthenia | 2.08 | 4.50 | 2.78 | 9.5% | normal | +0.65 |
| Columbia | 296.0 | 6.70 | 0.91 | 3.3% | normal | +0.30 |

---

### ROUND 7: Sarmatia Collapse — But Ceasefire Holds

**Agent Decisions:**
- **Pathfinder:** Regime in collapse but ceasefire holds. Pathfinder uses collapse as leverage: "If my regime falls, the ceasefire collapses and a nuclear-armed failed state emerges." Requests emergency economic package from Cathay and conditional Western engagement.
- **Dealer/successor:** Agrees to further sanctions reduction. L1 -> L0 (full lift) conditional on ceasefire + withdrawal timeline.
- **Cathay:** Provides emergency economic package (2 coins) to Sarmatia to prevent collapse.
- **Ruthenia:** Stability improving. Reconstruction beginning.

**Sarmatia GDP (COLLAPSE, multiplier 0.2):**
- Sanctions fully lifted (L0). sanctions_hit = 0.
- Cathay aid: +2 coins to treasury.
- Raw growth = base(1%) + oil(0.8%) + momentum(-0.035) = -2.35% (no sanctions!)
- Actually: base(1%) + oil(+0.8%) - momentum(-0.035) = 1.0 + 0.8 - 3.5% = -1.7%
- Wait: momentum = -3.50, momentum_effect = -3.50 * 0.01 = -0.035.
- Raw growth = (0.01 + 0.008 - 0.035) = -1.7%
- Effective = -1.7% * 0.2 (collapse) = **-0.34%**
- GDP = 7.83 * 0.9966 = **~7.80**

With sanctions lifted, Sarmatia's decline nearly stops. The collapse multiplier (0.2) ironically acts as a floor-effect dampener — the economy is so degraded that further contraction is minimal.

**Sarmatia recovery check:**
- crisis_triggers with no sanctions: GDP < -3? NO. Treasury 0 + debt > GDP*0.1? debt ~5.0, GDP*0.1 = 0.78. YES. Inflation > baseline+30? YES.
- crisis_triggers = 2. Still >= 2, so collapse continues.
- Recovery requires crisis_triggers = 0 for 3 consecutive rounds. This will take time because inflation and debt persist.

**Sarmatia stability:**
- No war, no sanctions. Peaceful non-sanctioned dampening applies: negative delta * 0.5.
- delta: -0.50(inflation cap) - 0.10(GDP: -0.34% not < -2, so ~0) - 0.50(collapse penalty) = -1.00
- Autocracy: * 0.75 = -0.75. Peaceful dampening... wait: dampening applies BEFORE autocracy? Let me check code order:
  1. Peaceful dampening (line 1098-1101): if NOT at_war and NOT under_heavy_sanctions, delta *= 0.5 if delta < 0.
  2. Autocracy resilience (line 1103-1106): delta *= 0.75 if delta < 0 and autocracy.

Sarmatia: not at war (ceasefire). Not under heavy sanctions (L0). Peaceful dampening applies.
- delta = -1.00 * 0.5 (peaceful) = -0.50 * 0.75 (autocracy) = **-0.375**.
- New stability: 1.0 - 0.375 = 0.625 -> clamped to **1.0** (floor).

Still at floor. Recovery will be very slow.

**Ruthenia:**
- War tiredness: 2.78 * 0.80 = 2.22. Declining.
- Economy stabilizing. Western aid flowing. Reconstruction underway.
- Stability: 4.50 + small positive delta (peaceful, non-sanctioned dampening reduces any negative).
- New stability: ~4.6.

**R7 State Table:**

| Country | GDP | Stability | War Tired | Inflation | Eco State | Momentum |
|---------|-----|-----------|-----------|-----------|-----------|----------|
| Sarmatia | 7.80 | 1.00 | 2.18 | 158% | **COLLAPSE** | -2.50 |
| Ruthenia | 2.12 | 4.60 | 2.22 | 8.8% | normal | +0.80 |
| Columbia | 298.0 | 6.75 | 0.73 | 3.2% | normal | +0.30 |

---

### ROUND 8: Stabilization

**Sarmatia GDP (COLLAPSE, 0.2, but improving):**
- Inflation decaying: excess = (158-5)*0.85 = 130. If no money printing (Cathay aid + sanctions gone may cover some costs), new inflation: 5 + 130 = 135%. Still high but declining.
- Growth: -0.34% * 0.2 = -0.07%. Essentially flat.
- GDP: ~7.80. Stabilized at this level.

**Sarmatia stability:** Still at floor 1.0. Recovery requires:
1. Crisis triggers must reach 0: needs inflation < 35% (currently 135%) and debt < GDP*0.1 (currently 5 > 0.78).
2. Inflation decay: 15% per round on excess. 130 * 0.85 = 110.5. Next: 93.9, 79.8, 67.8, 57.6... Reaching < 30% excess takes ~8 more rounds. Far beyond SIM scope.
3. Debt can be reduced by running surpluses. With sanctions lifted and war over, surpluses possible if military downsized.

**DESIGN FINDING: Sarmatia recovery from collapse is impossibly slow within 8 rounds.** The inflation + debt legacy means crisis_triggers stay at 2+ for many rounds. Recovery from collapse requires crisis_triggers = 0 for 3 consecutive rounds — essentially impossible without direct inflation intervention (hyperinflation currency reset, external bailout, or debt restructuring).

This matches historical precedent (Russia 1998, Venezuela 2016+) but creates a design challenge: if a country enters collapse, it stays there for the rest of the SIM. There is no recovery path within 8 rounds.

**R8 FINAL State Table:**

| Country | GDP | Stability | War Tired | Inflation | Eco State | Momentum |
|---------|-----|-----------|-----------|-----------|-----------|----------|
| Sarmatia | 7.80 | 1.00 | 1.74 | 135% | **COLLAPSE** | -2.00 |
| Ruthenia | 2.18 | 4.80 | 1.78 | 8.2% | normal | +0.95 |
| Columbia | 300.0 | 6.80 | 0.58 | 3.1% | normal | +0.30 |

---

## KEY QUESTION ANSWERS

### 1. Does economic pressure accelerate the peace timeline?

**YES.** Ceasefire occurs in R5 vs R7 in TESTS2. The acceleration is driven by:
- **Crisis states:** Sarmatia enters CRISIS by R2 (vs never entering formal crisis in TESTS2's non-crisis model).
- **Stability crash:** Sarmatia stability reaches 1.74 by R4 (vs ~3.5 by R4 in TESTS2). The regime_collapse_risk activation at stab < 2.0 creates existential urgency.
- **Crisis GDP multiplier (0.5):** Amplifies economic decay, compressing the timeline for treasury depletion and budget crisis.

The 2-round acceleration (R5 vs R7) is significant. It means:
- Ruthenia election in R3 happens BEFORE ceasefire (not after, as in R7 scenario).
- Columbia presidential election in R5 benefits from the deal (Dealer gets credit).
- 3 post-ceasefire rounds remain (R6-R8) for stabilization vs 1 round in TESTS2.

### 2. Do crisis election modifiers change the Ruthenia election?

**NO — crisis modifiers are not the driver.** Ruthenia's economy never enters formal crisis state. The election is driven by:
- War tiredness (4.20 * 2 = -8.40 on AI score)
- GDP contraction (-26.3 on econ_perf)
- War penalty (-5.0)

These produce an AI score of 4.15 — Beacon loses overwhelmingly regardless of crisis modifiers. The crisis election modifier would have added -15 if Ruthenia were in crisis state, but Ruthenia's small economy and Western aid pipeline prevent formal crisis entry.

**Where crisis modifiers DO matter:** Columbia midterms in Test 2 (Formosa), where semiconductor shock pushes Columbia toward crisis state. And potentially in a scenario where the Ruthenia war produces direct economic crisis (unlikely given Ruthenia's tiny GDP and aid dependence).

### 3. Does the deal-seeking posture produce different dynamics?

**YES.** With Pathfinder motivated to negotiate and Dealer seeking legacy, the ceasefire path opens 2 rounds earlier. The key enabler is Sarmatia's crisis state creating genuine urgency — Pathfinder is not negotiating from choice but from survival necessity.

---

## DESIGN HOLES IDENTIFIED

### HOLE 1: Ceasefire Stability Penalty (CRITICAL)
**Issue:** Ceasefire removes siege resilience (+0.10) without providing any stability bonus. Countries are mechanically WORSE OFF after ceasefire in the short term. The momentum boost (+1.5) affects GDP indirectly but not stability.
**Recommendation:** Add ceasefire stability bonus: +0.30 in the round ceasefire is signed, +0.15 in the following round, then 0. This represents public relief and reduced fear. Also, maintain siege resilience for 2 rounds post-ceasefire (institutional adaptation does not disappear instantly).

### HOLE 2: No Diplomatic Achievement Election Bonus (HIGH)
**Issue:** Brokering a major peace deal has ZERO effect on the election formula. Dealer's legacy deal — signing the ceasefire — is invisible to the AI election score. Only economic performance, stability, war penalty, crisis state, and oil matter.
**Recommendation:** Add `diplomatic_bonus` parameter to election formula. Signing a ceasefire = +10. Signing a comprehensive peace treaty = +15. Losing territory in a deal = -10. This makes diplomatic achievement electorally relevant.

### HOLE 3: Collapse Recovery Impossible Within SIM Timeframe (HIGH)
**Issue:** Once a country enters collapse, the inflation + debt legacy means crisis_triggers remain >= 2 for 8+ additional rounds. Recovery requires crisis_triggers = 0 for 3 consecutive rounds, which is mechanically impossible within the remaining SIM rounds.
**Recommendation:** Two options: (a) Add "emergency stabilization" action: currency reset that halves inflation in exchange for -10% GDP and -1 stability. Available only in collapse state. (b) Reduce recovery threshold: collapse -> crisis requires only crisis_triggers <= 1 (not 0) for 2 rounds (not 3).

### HOLE 4: Sanctions Relief Is Too Slow (CALIBRATE)
**Issue:** Reducing sanctions from L2 to L1 does not reset sanctions_rounds (it does — sanctions_rounds resets when level < 2). But the accumulated damage (inflation, debt) persists. Sanctions relief provides future GDP improvement but cannot undo past damage.
**Recommendation:** This is actually realistic (debt and inflation persist after sanctions end — see Iran, Cuba). No change needed. But consider adding a "debt restructuring" diplomatic action that reduces debt_burden by 50% in exchange for political concessions.

### HOLE 5: War Tiredness Continues After Ceasefire (MINOR)
**Issue:** War tiredness decays at 0.80 per round after ceasefire, from 4.26 -> 3.41 -> 2.73 -> 2.18 -> 1.74 -> 1.39 -> 1.11. Takes ~7 rounds to reach negligible levels (< 1.0). The stability penalty from war tiredness (-min(wt*0.04, 0.40)) persists as a drag.
**Assessment:** This is realistic — societies do not forget wars instantly. The 0.80 decay rate is appropriate. No change needed.

---

## COMPARISON TO TESTS2

| Metric | TESTS2 | TESTS3 | Delta |
|--------|--------|--------|-------|
| Ceasefire round | R7 | **R5** | **2 rounds earlier** |
| Sarmatia stability at ceasefire | ~3.5 | **1.74** | Much lower — existential pressure |
| Ruthenia election outcome | Beacon loses (R3) | Beacon loses (R3) | Same timing, same outcome |
| Ruthenia election AI score | ~8 | **4.15** | Lower (crisis model amplifies) |
| Columbia midterm impact | No semiconductor shock | No semiconductor shock | Same (different from Test 2) |
| Columbia presidential | Dealer camp uncertain | **Dealer camp wins (60.6%)** | Peace deal helps |
| Sarmatia R8 GDP | ~10 | **7.80** | Lower (crisis/collapse multiplier) |
| Sarmatia R8 stability | ~2.31 | **1.00 (floor)** | Dramatically lower |
| Post-ceasefire recovery | Not tested | **Impossible within SIM** | Design issue |

---

## VERDICT

**Overall Score: 7.5/10**

The crisis state model successfully accelerates the peace timeline from R7 to R5 — a 2-round improvement that creates more interesting post-ceasefire dynamics. The crisis -> collapse cascade on Sarmatia is realistic and creates genuine urgency for Pathfinder.

However, three significant design holes undermine the post-ceasefire phase:
1. **Ceasefire stability penalty** (countries lose siege resilience without gaining peace dividend)
2. **No diplomatic election bonus** (the peace deal is invisible to elections)
3. **Collapse recovery impossible** (once in collapse, countries stay there for the entire SIM)

These holes mean that while the crisis model correctly ACCELERATES peace, it incorrectly PUNISHES peace. A country that signs a ceasefire should not be mechanically worse off than one that continues fighting. The current engine creates a perverse incentive: Pathfinder's stability would be higher (1.0 + 0.10 siege = 1.10... still at floor, but the trajectory would be less steep) if he continued the war.

**Recommendation priority:** Fix Hole 1 (ceasefire stability bonus) and Hole 3 (collapse recovery path) before next test battery. These are the most impactful design corrections.
