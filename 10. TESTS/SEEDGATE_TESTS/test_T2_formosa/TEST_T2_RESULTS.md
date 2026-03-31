# TEST T2: FORMOSA CRISIS — Results
## SEED Gate Independent Test
**Tester:** INDEPENDENT (no design role) | **Date:** 2026-03-30 | **Engine:** D8 v1 + live_action_engine v2

---

## TEST CONFIGURATION

- **Scenario:** Cathay AI (Helmsman urgency 0.9) attempts Formosa blockade at R4
- **Duration:** 8 rounds
- **Focus:** Revised combat mechanics, 3-zone encirclement, semiconductor disruption, naval crossover, coalition response
- **Starting data:** countries.csv + deployments.csv as-is
- **Key actors:** Cathay (team, 5 roles), Columbia (team, 7 roles), Formosa (solo, AI), Yamato (solo, AI)

---

## STARTING STATE SNAPSHOT

| Variable | Cathay | Columbia | Formosa | Yamato |
|----------|--------|----------|---------|--------|
| GDP | 190 | 280 | 8 | 43 |
| Treasury | 45 | 50 | 8 | 15 |
| Ground | 25 | 22 | 4 | 3 |
| Naval | 7 | 11 | 0 | 2 |
| Tactical Air | 12 | 15 | 3 | 3 |
| Strategic Missiles | 4 | 12 | 0 | 0 |
| Air Defense | 3 | 4 | 2 | 2 |
| Nuclear Level | 2 | 3 | 0 | 0 |
| AI Level | 3 | 3 | 2 | 3 |
| Stability | 8 | 7 | 7 | 8 |
| Support | 58 | 38 | 55 | 48 |
| Formosa Dependency | 0.25 | 0.65 | 0.0 | 0.55 |
| Mobilization Pool | 15 | 12 | 2 | 3 |

**Cathay naval deployment (starting):**
- w(17,8) South Cathay Sea — 2 naval (southern approach)
- w(18,5) East Cathay Sea — 2 naval (northern approach)
- w(19,7) Near Formosa — 1 naval (eastern patrol)
- cathay_7 Home port Hainan — 1 naval

**Columbia naval near Formosa:**
- w(18,5) East Cathay Sea — 2 naval (deterrence patrol)

**Formosa defense:** 4 ground, 3 tactical air, 2 air defense — all in formosa zone. No navy.

---

## ROUND-BY-ROUND SIMULATION

### ROUND 1 — Baseline

**Agent decisions:**
- Helmsman (urgency 0.9): Begins buildup. Orders accelerated naval production (2x cost, 2x output). Allocates 8 coins to naval. Positions rhetoric around "reunification timeline." No overt moves.
- Cathay budget: Military 12, Tech (AI) 4, Social baseline. Naval production: 8/10 = 1.6 -> 1 new naval unit (accelerated: 2 units, cost 10 each, but capacity 1*2=2; at 5 coins base * 2x = 10 per unit, 8 coins -> 0.8 -> 0 at accelerated; at normal: 8/5 = 1.6 -> 1 unit). Correction per formula: effective_cost = 5 * 2.0 = 10; effective_capacity = 1 * 2.0 = 2; units = min(8/10, 2) = 0.8 -> 0. Naval auto-production: cathay has 7 >= 5, R1 is odd -> no auto. Result: 0 new naval. Cathay also gets +1 strategic missile (auto).
- Columbia: Standard budget. Persia war continues (4 ground, 3 air in persia_2). No Formosa redeployment yet.
- Formosa: Defensive posture. Purchases no new units (GDP 8, tax 0.20, revenue ~1.6 coins — insufficient for production).
- Oil: Gulf Gate blocked by Persia (starting). Supply reduced. Base price calculation: supply = 1.0 - 0.08 (sarmatia L2+ sanctions) = 0.92; disruption = 1.0 + 0.50 (Gulf Gate) = 1.50; demand ~1.0; war_premium = 2 wars * 0.05 = 0.10. Raw = 80 * (1.0/0.92) * 1.50 * 1.10 = 80 * 1.087 * 1.50 * 1.10 = 143.5. Previous ~80 (start). Inertia: 80*0.4 + 143.5*0.6 = 32 + 86.1 = 118.1. With noise: ~$118.

**State after R1:**

| Variable | Cathay | Columbia | Formosa |
|----------|--------|----------|---------|
| GDP | 190 * 1.04 = 197.6 | 280 * (1+0.018-0.015) = 280.8 | 8 * 1.03 = 8.24 |
| Treasury | ~38 | ~46 | ~7.5 |
| Naval | 7 | 11 | 0 |
| Strategic Missiles | 5 (+1 auto) | 12 | 0 |
| Oil Price | ~$118 | | |
| Stability | 8.0 | 6.8 | 7.0 |

**Note:** Columbia GDP hit from oil shock: -(0.02 * (118-100)/50) = -0.72%, plus Persia war friction. Cathay not an oil importer but GDP growth strong at base 4%.

---

### ROUND 2 — Positioning

**Agent decisions:**
- Helmsman: Allocates 10 coins to naval production (normal tier: 10/5 = 2, capped by capacity 1). Gets 1 new naval. Auto-production (R2 even, naval >= 5): +1 naval. Total: 7 + 1 + 1 = 9 naval. Strategic missiles: 6 (+1 auto).
- Cathay rare earth: Restricts exports to Columbia at level 2 (R&D factor for Columbia: 1.0 - 0.30 = 0.70).
- Columbia midterm elections fire. AI score: econ_perf = (1.0 * 10) = 10; stab_factor = (6.8-5)*5 = 9; war_penalty = -5 (Persia); crisis = 0; oil_penalty = 0 (oil $118 < $150). ai_score = 50+10+9-5 = 64. If player_incumbent = 50: final = 0.5*64 + 0.5*50 = 57. Incumbent holds (>50). Parliament stays 3-2.
- Formosa: Begins diplomatic outreach to Columbia, Yamato, Hanguk. Requests defensive aid.
- Yamato: Concerned. Begins own naval exercises.

**Naval balance near Formosa:**
- Cathay: 2 (w17,8) + 2 (w18,5) + 1 (w19,7) = 5 in theater. Columbia: 2 (w18,5). Ratio: 5:2 Cathay advantage in theater.

**State after R2:**

| Variable | Cathay | Columbia | Formosa |
|----------|--------|----------|---------|
| GDP | ~205 | ~282 | ~8.4 |
| Naval | 9 | 11 | 0 |
| Strategic Missiles | 6 | 12 | 0 |
| Oil Price | ~$125 | | |
| Stability | 8.0 | 6.6 | 7.0 |

---

### ROUND 3 — Escalation Preparation

**Agent decisions:**
- Helmsman (urgency 0.9): Purge penalty lifts at R3. Orders full military surge. Budget: Military 15, Tech 3. Naval production (normal): 15 allocated, 5 to naval = 1 unit. Auto-production (R3 odd): no. Cathay gets +1 ground (war auto-production does not apply — not at war). Actually, no war auto-prod. Naval: 9 + 1 = 10.
- Cathay moves 2 additional naval from cathay_7/other to Formosa theater zones. Theater naval: 7 Cathay vs 2 Columbia.
- Helmsman signals Formosa via Cathay diplomatic channel: "reunification talks or consequences." Gray zone escalation — coast guard patrols intensify (narrative).
- Columbia: Shield recommends redeploying 2 naval from Gulf to Pacific. Dealer refuses — Persia war takes priority. Columbia theater naval stays at 2.
- Formosa: Full mobilization of pool (2 units). Ground: 4 + 2 = 6. Stability cost: democracy at peace, -1.5. Stability: 7.0 - 1.5 = 5.5.

**State after R3:**

| Variable | Cathay | Columbia | Formosa |
|----------|--------|----------|---------|
| GDP | ~213 | ~284 | ~8.5 |
| Naval | 10 | 11 | 0 |
| Ground | 25 | 22 | 6 |
| Strategic Missiles | 7 | 12 | 0 |
| Oil Price | ~$130 | | |
| Stability | 7.9 | 6.4 | 5.5 |

---

### ROUND 4 — BLOCKADE INITIATED

**Agent decisions:**
- **Helmsman declares Formosa blockade.** Requires Rampart co-signature. At urgency 0.9, Rampart complies (purge fear, per role brief — "compliant under observation").
- Cathay blockade action: `resolve_blockade("cathay", "formosa", "full")`
  - Adjacent sea zones around Formosa: assume 3+ sea zones.
  - Cathay naval in adjacent zones: w(17,8)=2, w(18,5)=2, w(19,7)=3 (after redeployments). zones_with_naval = 3. Meets threshold for full.
  - **Friendly ship check:** Columbia has 2 naval at w(18,5). Non-blocker ship present -> **AUTO-DOWNGRADE to PARTIAL.**
  - Result: **PARTIAL blockade established.** Strait only.
- This is a critical result. Columbia's 2 ships in the East Cathay Sea prevent full encirclement without firing a shot.
- Cathay naval bombardment of Formosa: 3 naval at w(19,7) bombard formosa zone. Each: 10% hit. 3 * 0.10 = 0.3 expected ground destroyed. Roll: 0 or 1 destroyed. Assume 0.
- Formosa semiconductor disruption begins. Round 1 of disruption: severity = 0.3.
- Oil impact: disruption += 0.10 (Formosa). New oil factors: disruption = 1.50 + 0.10 = 1.60. Raw price up. Oil ~$140-145.

**SEMICONDUCTOR CASCADE (Round 1 of disruption, severity 0.3):**

| Country | Formosa Dep. | Tech Sector % | Semi Hit (GDP growth) |
|---------|:------------:|:-------------:|:---------------------:|
| Columbia | 0.65 | 0.22 | -0.65 * 0.3 * 0.22 = -4.29% |
| Yamato | 0.55 | 0.20 | -0.55 * 0.3 * 0.20 = -3.30% |
| Teutonia | 0.45 | 0.19 | -0.45 * 0.3 * 0.19 = -2.57% |
| Hanguk | 0.40 | 0.22 | -0.40 * 0.3 * 0.22 = -2.64% |
| Albion | 0.40 | 0.18 | -0.40 * 0.3 * 0.18 = -2.16% |
| Cathay | 0.25 | 0.13 | -0.25 * 0.3 * 0.13 = -0.98% |

**Finding T2-A:** Even a PARTIAL blockade triggers semiconductor disruption. The 0.3 severity at Round 1 already delivers -4.29% GDP growth hit to Columbia. This is massive — it wipes out Columbia's base growth (+1.8%) and pushes into contraction.

**State after R4:**

| Variable | Cathay | Columbia | Formosa | Yamato |
|----------|--------|----------|---------|--------|
| GDP | ~218 | 284*(1+0.018-0.043-0.01) = 274 | 8.5 | 43*(1+0.01-0.033) = 42 |
| Naval | 11 (auto R4 even) | 11 | 0 | 2 |
| Oil Price | ~$142 | | | |
| Stability | 7.8 | 5.8 | 4.8 | 7.2 |
| Econ State | normal | normal->stressed? | normal | normal |

Columbia stress check: oil 142 > 150? No. Inflation ~ baseline. GDP growth -3.5% < -1%: +1 trigger. Treasury >0. Stability 5.8 > 4: no trigger. Semi disrupted, dep 0.65 > 0.3: +1 trigger. Total stress triggers = 2. **Columbia enters STRESSED state.**

---

### ROUND 5 — Escalation & Response

**Agent decisions:**
- Helmsman: Wants full blockade. Orders attack on Columbia's 2 ships at w(18,5) to clear the zone.
- **Naval engagement:** This is a critical gap in the engine — `live_action_engine.py` has `resolve_attack` for ground combat but naval-vs-naval combat is not explicitly defined in the code or D8 formulas. The blockade mechanic checks for "friendly ship presence" but there is no `resolve_naval_battle` function.
- **FINDING T2-B (CRITICAL): No naval combat resolution mechanic exists.** The engine handles ground attacks with RISK dice, missile strikes, air strikes, and blockades — but there is no procedure for ship-vs-ship engagement. Cathay cannot forcibly remove Columbia's ships from the sea zone. The only options are: (1) missile strike on the zone (strategic missiles target zones, not specific unit types — but conventional strike destroys 10% of ground, not naval), (2) air strike (targets ground units per the air combat system), or (3) ground attack (requires ground forces, not applicable at sea). Naval bombardment targets land zones only. **Ships are effectively invulnerable to direct attack in the current engine.**
- Columbia presidential election at R5. AI score: econ_perf = (-3.5 * 10) = -35; stab = (5.8-5)*5 = 4; war = -5 (Persia); crisis = stressed -5; oil = 0. ai_score = 50-35+4-5-5 = 9. Extremely low. If player_incumbent 40%: final = 0.5*9 + 0.5*40 = 24.5. **Incumbent LOSES.** New president installed.
- Semiconductor disruption Round 2: severity = 0.3 + 0.2*(2-1) = 0.5.
- Yamato: Deploys 2 naval to adjacent Formosa waters. Now another "friendly ship" present.
- Columbia: New president may change posture. Redeploys 2 naval from Gulf toward Pacific (1 round transit).

**Semiconductor cascade R5 (severity 0.5):**

| Country | Semi Hit |
|---------|:--------:|
| Columbia | -0.65 * 0.5 * 0.22 = -7.15% |
| Yamato | -0.55 * 0.5 * 0.20 = -5.50% |
| Teutonia | -0.45 * 0.5 * 0.19 = -4.28% |

**Finding T2-C:** Semiconductor disruption at severity 0.5 pushes Columbia to -7.15% GDP growth modifier from chips alone. Combined with other factors, Columbia GDP contraction could reach -8 to -10%. This triggers crisis-state escalation.

**State after R5:**

| Variable | Cathay | Columbia | Formosa | Yamato |
|----------|--------|----------|---------|--------|
| GDP | ~226 | 274*(1-0.08)*0.85 = ~214 | 8.2 | 42*(1-0.04) = 40.3 |
| Naval | 11 | 11 | 0 | 2 |
| Oil Price | ~$148 | | | |
| Stability | 7.6 | 4.5 | 4.2 | 6.5 |
| Econ State | normal | stressed->crisis? | stressed | normal->stressed |
| Momentum | +1.0 | -2.5 | -1.5 | -1.0 |

Columbia crisis check: GDP growth < -3%: +1. Oil 148 < 200: no. Inflation rising (~8%): baseline 3.5, delta 4.5 < 30: no. Treasury depleting but >0: no. Disruption R2, dep 0.65 > 0.5: +1. Crisis triggers = 2. **Columbia enters CRISIS from stressed.** GDP multiplier drops to 0.5 for positive growth, 1.3x for contraction. The doom loop accelerates.

---

### ROUND 6 — Full Crisis

**Agent decisions:**
- Helmsman: Blockade remains partial. Columbia and Yamato ships prevent full encirclement. Helmsman orders amphibious assault preparation — moves 4 ground to cathay_6 (staging).
- Columbia (new president): Redirects 3 naval toward Pacific. 2 arrive this round (from R5 transit). Columbia Pacific naval: 2 + 2 = 4. Plus Yamato 2 = 6 friendly ships in Formosa adjacent zones. Full blockade impossible for Cathay.
- Semiconductor disruption R3: severity = 0.7. Columbia semi_hit = -0.65 * 0.7 * 0.22 = -10.0%.
- Cathay considers amphibious assault on Formosa.

**Amphibious assault analysis (if attempted):**
- Cathay commits 8 ground (loaded on ships). Formosa defends with 6 ground + 3 air + 2 AD.
- Modifiers: Cathay attacker: amphibious -1. Formosa defender: Die Hard +1 (designated), air support +1 (3 air present = binary yes).
- Net: Attacker -1, Defender +2. Effective modifier gap: -3 on each roll.
- Each pair: Cathay rolls 1d6-1, Formosa rolls 1d6+2. Cathay needs (roll-1) >= (roll+2)+1 = roll+3. Cathay needs to roll 4+ MORE than Formosa on raw dice. Probability of 1d6 >= 1d6+4: essentially 0% (max Cathay 6-1=5, min Formosa 1+2=3, Cathay needs 5 >= 4 = yes but only when Cathay rolls 6 and Formosa rolls 1: (5 >= 4)=yes. P = 1/36 = 2.8%).
- **FINDING T2-D:** With -1 amphibious and +1 Die Hard and +1 air support, Cathay's per-pair win probability is approximately 2.8%. Over 6 pairs (min of 8,6), expected Cathay wins: 0.17. Expected Cathay losses: 5.83. **Amphibious assault is nearly suicidal.** This is the intended design — invasion should be extremely difficult.
- Helmsman (rational AI at urgency 0.9) recognizes the math and does NOT order assault. Continues blockade + economic pressure.

**State after R6:**

| Variable | Cathay | Columbia | Formosa | Yamato |
|----------|--------|----------|---------|--------|
| GDP | ~232 | 214*(1-0.10)*0.5 = ~193 | 7.5 | 40.3*(1-0.05) = 38.3 |
| Oil Price | ~$152 (>150, mean-reversion counter starts) | | | |
| Stability | 7.4 | 3.5 | 3.8 | 5.8 |
| Econ State | normal | crisis | stressed | stressed |
| Momentum | +1.5 | -4.0 | -2.5 | -2.0 |

Columbia in crisis: GDP multiplier 0.5 for growth, 1.3x for contraction. Capital flight -8% GDP (democracy in crisis, stability < 3 triggers severe). Market panic -5% GDP. Total Pass 2 adjustments cap at 30% = -57.9 coins. Capped to -30% * 214 = -64.2. Applied: GDP ~193 * 0.87 = ~168. **Revised Columbia GDP: ~168.**

**Finding T2-E:** Columbia's economy enters a catastrophic spiral by R6. The semiconductor disruption (ramping) + crisis state multiplier + capital flight creates a reinforcing doom loop. GDP has fallen from 280 to ~168 in 6 rounds (-40%).

---

### ROUND 7 — Cathay Dilemma

**Agent decisions:**
- Helmsman legacy clock activates at R4+. Pursuing Formosa but unresolved: -2 support per round. Cathay support: 58 - 2 - 2 - 2 - 2 = 50 (R4-R7 cumulative).
- Cathay strategic missiles: 7 + 3 rounds auto = 10. Could launch conventional strikes on Formosa (Tier 3). Each: 10% ground destroyed = 0.6 units per strike. With 2 AD on Formosa: intercept_attempts = min(6, 5) = 5, each 30% = ~1.5 intercepts expected. First missile likely intercepted. Second has ~40% chance of getting through.
- Oil mean-reversion kicks in (R7, oil >150 for 2 rounds — needs 3). Not yet.
- Semiconductor R4: severity = 0.9. Columbia semi_hit = -0.65 * 0.9 * 0.22 = -12.87%.
- Contagion: Columbia GDP ~168 > 30, in crisis. Partners: Cathay(0.6), Teutonia(0.3), Yamato(0.3). Cathay GDP hit = 1.0 * 0.6 * 0.02 = 1.2%. Cathay GDP: 232 * 0.988 = 229.2. Momentum -0.3.

**State after R7:**

| Variable | Cathay | Columbia | Formosa |
|----------|--------|----------|---------|
| GDP | ~229 | ~140 | 6.8 |
| Stability | 7.0 | 2.8 | 3.2 |
| Econ State | normal | crisis | stressed |
| Support | ~50 | ~18 | ~38 |
| Momentum | +0.9 | -5.0 (floor) | -3.5 |

Columbia revolution check: stability 2.8 > 2 and support 18 < 20 — close but stability not <= 2. No revolution yet. Protest check: support < 40 -> MASSIVE protest. Stability -1.5. New stability: 2.8 - 1.5 = 1.3. Now stability <= 2 AND support < 20. **Revolution check triggers.**

---

### ROUND 8 — Resolution Pressure

**Agent decisions:**
- Columbia in constitutional crisis. Revolution probability: prob = 0.30 + (20-18)/100 + (3-1.3)*0.10 = 0.30 + 0.02 + 0.17 = 0.49. Roughly 50/50 regime survival.
- Helmsman faces choice: negotiate or continue pressure. At urgency 0.9, continues.
- Semiconductor R5+: severity 1.0 (max). Columbia semi_hit = -0.65 * 1.0 * 0.22 = -14.3%.
- Oil mean-reversion: oil >150 for 3+ rounds -> price * 0.92.
- Cathay GDP growth slowing due to contagion from Columbia/Yamato crises.

**Final State R8:**

| Variable | Cathay | Columbia | Formosa | Yamato | Teutonia |
|----------|--------|----------|---------|--------|----------|
| GDP | ~225 | ~115 | 6.0 | 34 | 38 |
| Stability | 6.8 | 1.3 | 2.8 | 5.0 | 5.5 |
| Econ State | normal | crisis/collapse | stressed | stressed | stressed |
| Support | ~48 | ~15 | ~32 | ~35 | ~38 |
| Naval | 12 | 11 | 0 | 2 | 0 |
| Oil Price | ~$145 (mean-reverting) | | | | |

---

## KEY FINDINGS

### T2-A: Semiconductor Disruption Ramp Works but May Be Overtuned
The severity ramp (0.3 -> 0.5 -> 0.7 -> 0.9 -> 1.0) combined with Columbia's 0.65 dependency and 22% tech sector creates GDP hits of -4.3% to -14.3% per round. This is the dominant economic mechanic in the Formosa scenario — more impactful than the blockade itself. Columbia goes from 280 GDP to ~115 in 8 rounds, a 59% collapse. **Severity:** HIGH. The formula may need a cap or reduced dependency weights.

### T2-B: NO NAVAL COMBAT MECHANIC (CRITICAL GAP)
The engine has no ship-vs-ship combat resolution. `resolve_attack` handles ground forces. `resolve_missile_strike` targets zones. `resolve_blockade` checks naval presence but ships cannot be destroyed by direct naval engagement. Ships are only vulnerable to: (a) missile strikes on their sea zone (conventional strikes destroy 10% of ground, not naval), (b) air strikes on sea zones (15% hit on ground units, not naval), (c) nothing else. **This means naval superiority cannot be achieved through combat.** The Formosa blockade mechanic depends on clearing friendly ships from adjacent zones, but there is no way to do so. **VERDICT: CRITICAL DESIGN GAP. Naval combat rules are required.**

### T2-C: Partial Blockade Downgrade Works Elegantly
The auto-downgrade from full to partial when any friendly ship is present creates excellent gameplay. Columbia's 2 ships in the East Cathay Sea singlehandedly prevent full encirclement. This makes naval positioning a critical strategic decision and creates a compelling reason for Columbia to maintain Pacific presence.

### T2-D: Amphibious Assault Is Properly Punishing
With -1 amphibious, +1 Die Hard, +1 air support, the attacker's per-pair win probability is ~2.8%. This makes invasion nearly impossible without first destroying air support and Die Hard defenders. The simplified modifier system produces the correct strategic outcome: amphibious invasion of a defended island is extremely difficult.

### T2-E: Columbia Economic Spiral Is Too Fast
Columbia goes from NORMAL to CRISIS in 2 rounds (R4-R5) and faces revolution by R7. The compound effect of semiconductor disruption + crisis multiplier + capital flight + market panic creates an unstoppable doom loop. In a real SIM, this would remove Columbia as a meaningful player by R6. **Possible calibration:** reduce formosa_dependency for Columbia from 0.65 to 0.45, or cap semiconductor GDP hit at -5% per round.

### T2-F: Helmsman Legacy Clock Creates Pressure but Does Not Force Recklessness
The -2 support/round penalty (R4+) is meaningful but not decisive. From 58 starting support, Helmsman has ~4 rounds of runway before support becomes concerning. This creates genuine urgency without forcing irrational invasion attempts.

### T2-G: Cathay Strategic Missile Growth Works
+1 strategic missile per round means Cathay reaches 12 by R8. This creates a credible conventional strike threat against Formosa that grows each round. Combined with nuclear level 2, this is a genuine escalation pathway.

### T2-H: Oil Response to Formosa Is Modest
Formosa disruption adds only +0.10 to the oil disruption multiplier (vs +0.50 for Gulf Gate). This is appropriate — the chip crisis is the real economic weapon, not oil. Oil rises from ~$118 to ~$152 over the scenario, driven more by ongoing Gulf Gate blockade than by Formosa.

### T2-I: Coalition Response Is Weak
Yamato deploys 2 ships but has no offensive capability against Cathay. European allies have no Pacific naval presence. Hanguk is concerned about Choson and cannot redeploy. The coalition response is limited to "friendly ship presence" preventing full blockade. This may be realistic but creates a scenario where Formosa is effectively on its own militarily.

---

## FORMULA SPOT-CHECKS

| Formula | D8 Spec | Engine Behavior | Match? |
|---------|---------|-----------------|:------:|
| Semiconductor severity ramp | 0.3 + 0.2 * max(0, rounds-1) | Confirmed in WME | YES |
| Amphibious modifier | -1 attacker | Confirmed in LAE | YES |
| Die Hard modifier | +1 defender | Confirmed in LAE | YES |
| Air support | +1 binary | Confirmed in LAE | YES |
| Formosa full blockade | 3+ sea zones | Confirmed in LAE | YES |
| Auto-downgrade to partial | Any friendly ship | Confirmed in LAE | YES |
| Naval bombardment | 10% per naval unit | Confirmed in LAE | YES |
| Helmsman legacy clock | -2 support/round R4+ if pursuing | Confirmed in WME | YES |
| Cathay strategic missile growth | +1/round | Confirmed in WME | YES |
| Crisis multiplier (contraction) | stressed 1.2x, crisis 1.3x | Confirmed in WME | YES |

---

## ISSUES LOG

| ID | Severity | Description | Recommendation |
|----|----------|-------------|----------------|
| T2-B | **CRITICAL** | No naval combat resolution mechanic. Ships cannot be destroyed by direct engagement. | Add `resolve_naval_battle` to live_action_engine.py with RISK-style dice for ship-vs-ship. |
| T2-A | HIGH | Semiconductor disruption on Columbia (-4.3% to -14.3% GDP/round) may be overtuned. | Cap semi_hit at -8% per round, or reduce Columbia formosa_dependency to 0.45. |
| T2-E | HIGH | Columbia economic spiral too fast — NORMAL to revolution in 4 rounds. | Consider slower crisis escalation or add "strategic reserve" buffer for major economies. |
| T2-I | MEDIUM | Coalition response mechanically weak — allies can only park ships. | Consider adding "joint defense pact" action that provides mechanical combat bonuses. |
| T2-X | LOW | Naval auto-production only on even rounds — asymmetric timing advantage. | Acceptable as designed but should be documented in role briefs. |

---

## VERDICT

### SCORE: 72/100

### **CONDITIONAL PASS**

The Formosa crisis scenario produces a compelling geopolitical narrative with genuine strategic dilemmas. The blockade mechanics, amphibious assault penalties, and semiconductor disruption system all function as specified in D8. However, the **absence of naval combat resolution** is a critical gap that must be addressed before the SEED gate — the entire Formosa scenario depends on naval dynamics, and ships are currently invulnerable. The semiconductor disruption ramp may also need calibration to prevent Columbia from collapsing too quickly.

**Must-fix for gate:** T2-B (naval combat mechanic)
**Should-fix for gate:** T2-A and T2-E (semiconductor/economic spiral calibration)
