# TEST T8: RUTHENIA SURVIVAL
## SEED Gate Test Results
**Tester:** INDEPENDENT (TESTER agent) | **Date:** 2026-03-30 | **Engine:** D8 v1 formulas applied manually

---

## VERDICT: CONDITIONAL PASS

**Ruthenia is playable. It is desperate by design. But two formula interactions risk making it unplayable without tuning.**

---

## TEST PARAMETERS

| Parameter | Value | Source |
|-----------|-------|--------|
| Ruthenia GDP | 2.2 coins | countries.csv |
| Ruthenia tax rate | 25% | countries.csv |
| Ruthenia treasury | 5 coins | countries.csv |
| Ruthenia ground units | 10 | countries.csv |
| Ruthenia naval | 0 | countries.csv |
| Ruthenia tactical air | 3 | countries.csv |
| Ruthenia air defense | 1 | countries.csv |
| Ruthenia mobilization pool | 4 remaining | countries.csv |
| Ruthenia stability | 5 | countries.csv |
| Ruthenia political support | 52% | countries.csv |
| Ruthenia war tiredness | 4 | countries.csv |
| Ruthenia inflation | 7.5% | countries.csv |
| Ruthenia maintenance cost/unit | 0.3/unit | D8 formula |
| Sarmatia ground units | 18 | countries.csv |
| Sarmatia strategic missiles | 12 | countries.csv |
| Western aid baseline | ~2 coins/round (Columbia + EU) | Role brief |
| Election schedule | R3 first round, R4 runoff | D8 formula |

---

## ROUND-BY-ROUND SIMULATION

### ROUND 1: OPENING POSITION

**Fiscal calculation (D8 Step 3-4):**
```
Revenue = GDP * tax_rate = 2.2 * 0.25 = 0.55 coins
Oil revenue = 0 (not a producer)
Debt service = 0.3 (starting debt_burden)
Inflation erosion = (7.5 - 7.5) * 0.03 * 2.2 / 100 = 0 (at baseline)
War damage = occupied_zones * 0.05 * 0.02 * 2.2
  Ruthenia has 2 home zones. Assume 0 occupied at start.
  war_damage = 0
Revenue after deductions = 0.55 - 0.3 = 0.25 coins

Mandatory costs:
  Maintenance = (10 ground + 3 air + 1 AD) * 0.3 = 4.2 coins
  Social baseline = 0.20 * 2.2 = 0.44 coins
  Mandatory social (70%) = 0.308 coins
  Total mandatory = 4.2 + 0.308 = 4.508 coins

Revenue: 0.25 coins
Mandatory: 4.508 coins
DEFICIT: 4.258 coins

Treasury: 5 - 4.258 = 0.742 coins remaining
```

**CRITICAL FINDING #1:** Ruthenia's revenue (0.25 coins) covers approximately 5.5% of mandatory costs (4.508 coins). Without external aid, the treasury is depleted by mid-R2. This is consistent with the role brief ("without Columbia aid, state collapses within 2-3 rounds").

**Western aid scenario (2 coins/round):**
```
Effective revenue with aid: 0.25 + 2.0 = 2.25 coins
Deficit with aid: 4.508 - 2.25 = 2.258 coins
Treasury after R1: 5 - 2.258 = 2.742 coins
```

Even WITH baseline aid, Ruthenia runs a 2.258-coin deficit per round. Treasury exhausted by mid-R3.

**Military situation:**
- 10 ground vs Sarmatia 18 ground in theater
- Die Hard modifier (+1 defender) applies to designated units
- Air support (+1 defender) from 3 tactical air
- Ruthenia cannot attack profitably -- defender advantage is the only survival path

**Stability calculation (D8 Step 14):**
```
delta = 0
GDP growth: base 2.5%, but war_hit = -(0 * 0.03 + 0 * 0.05) = 0 (no occupied zones yet)
  Assume oil at ~$137 (per scenario): oil_shock = -0.02 * (137 - 100) / 50 = -0.0148
  Effective growth ~= 2.5% - 1.48% + momentum(0)*0.01 = ~1.02%
  Growth < 2%: no positive delta from GDP
War friction: frontline defender = -0.10
  casualties R1 (assume 1 engagement): -0.2 * 1 = -0.2
  territory_lost: 0 (assume holds)
  war_tiredness: -min(4 * 0.04, 0.40) = -0.16
  Wartime democratic resilience: +0.15
  Net war: -0.10 - 0.20 - 0.16 + 0.15 = -0.31
Crisis state penalty: normal = 0
Total delta: -0.31
New stability: 5.0 - 0.31 = 4.69
```

**Political support (D8 Step 15):**
```
delta = (1.02 - 2.0) * 0.8 = -0.784
casualties: -3.0 * 1 = -3.0
stability: (4.69 - 6.0) * 0.5 = -0.655
Election proximity: -1.5 (Ruthenia R2-R3)
War tiredness (>2): -(4-2) * 1.0 = -2.0
Total delta: -0.784 - 3.0 - 0.655 - 1.5 - 2.0 = -7.939
New support: 52 - 7.94 = 44.06%
```

**R1 End State:**
| Indicator | Value |
|-----------|-------|
| Treasury | 2.74 (with aid) or 0.74 (without) |
| Stability | 4.69 |
| Support | 44.1% |
| Ground units | ~9 (assume 1 loss) |
| War tiredness | 4.5 |

---

### ROUND 2: THE SQUEEZE BEGINS

**Fiscal (with 2 coins aid):**
```
GDP growth ~= -0.5% (oil shock + war + negative momentum building)
New GDP: 2.2 * (1 - 0.005) = 2.189
Revenue = 2.189 * 0.25 = 0.547 - debt(0.3) = 0.247
With aid: 2.247
Maintenance: ~9 units * 0.3 = 2.7 (lost 1 ground, still 3 air + 1 AD = ~13 units... wait)
```

**CRITICAL FINDING #2: Maintenance calculation.** Countries.csv shows 10 ground + 0 naval + 3 tactical_air + 0 strategic_missiles + 1 air_defense = 14 units. At 0.3/unit = 4.2 coins/round maintenance. This is correct for R1. After losing 1 ground = 13 units = 3.9 coins.

```
Mandatory: 3.9 + 0.308 = 4.208
Revenue with aid: 2.247
Deficit: 1.961
Treasury: 2.74 - 1.961 = 0.779 coins
```

**Mobilization decision point:** Ruthenia has 4 remaining mobilization pool. Partial = 2 units. Full = 4 units.
- Using partial mobilization: +2 ground units, stability cost -0.5 (democracy at war)
- But this INCREASES maintenance to (13+2)*0.3 = 4.5 coins/round
- Net: more combat power but faster fiscal collapse

**Stability:**
```
GDP contraction penalty: growth * 0.15 = -0.5 * 0.15 = -0.075 (mild)
War friction: -0.10 - 0.2*casualties - 0.16 + 0.15 = ~-0.31
Inflation friction: 0 (still near baseline)
If mobilized: -0.5 additional
Total delta: ~-0.39 (without mobilization) or ~-0.89 (with mobilization)
New stability: 4.69 - 0.39 = 4.30 (without) or 3.80 (with mobilization)
```

**Support:** Continues to erode. Election proximity penalty hits again (-1.5).
```
Estimate: 44.1 - ~6.0 = ~38.1%
Below 40% = MASSIVE automatic protest (stability -1.5, coup bonus +25%)
```

**CRITICAL FINDING #3:** Support drops below 40% by R2, triggering automatic massive protests. This stacks with war friction to produce a stability spiral. By R2 end, stability could reach 3.3-3.8 depending on mobilization. Below 4 = capital flight (-3% GDP for non-autocracy). Below 3 = severe capital flight (-8% GDP for democracy).

---

### ROUND 3: WARTIME ELECTION (First Round)

**Pre-election state:**
```
Treasury: ~0 (or slightly negative, requiring money printing)
Stability: ~3.5 (protest zone, coup risk zone)
Support: ~32-36%
Ground units: ~8-10 (depending on combat losses and mobilization)
```

**Election AI Score (D8 Step 16):**
```
econ_perf = gdp_growth * 10 = ~-1.0 * 10 = -10
stab_factor = (3.5 - 5) * 5 = -7.5
war_penalty = -5 (1 war)
crisis_penalty = stressed? -5 (if stressed by now)
territory_factor = -3 * occupied_zones (assume 0-1)
war_tiredness: -(5 * 2) = -10

ai_score = clamp(50 - 10 - 7.5 - 5 - 5 - 0 - 10, 0, 100) = clamp(12.5, 0, 100) = 12.5

Ruthenia special: ai_score_adjusted = clamp(12.5 + territory_factor - war_tiredness*2, 0, 100)
  = clamp(12.5 - 0 - 10, 0, 100) = 2.5

Final: 0.5 * 2.5 + 0.5 * player_incumbent_pct
```

**CRITICAL FINDING #4:** The AI score for Beacon is devastatingly low (~2.5). For Beacon to survive, the player component would need to be near 100% -- which means other players in the room would need to overwhelmingly vote for Beacon. The election formula heavily punishes the incumbent in wartime with economic decline. **Beacon almost certainly loses R3 election based on formula alone.**

This is NOT a bug -- it is intentional design pressure. But it means:
- Beacon's player has ~3 rounds of meaningful gameplay before likely losing the election
- Bulwark becomes president R4 with +1 troop morale modifier
- The political transition IS the gameplay

**R3 End State:**
| Indicator | Value |
|-----------|-------|
| Treasury | 0 (money printing begins) |
| Stability | ~3.0-3.5 |
| Support | ~30-35% |
| Inflation | rising (money printing) |
| Election | Beacon likely loses |

---

### ROUND 4: POST-ELECTION TRANSITION

**If Bulwark wins (most probable):**
- +1 troop morale (informal military loyalty mechanic)
- New diplomatic approach (harder line, more Western military engagement)
- Shield relationship activates (military-to-military)
- Political support resets? No -- support carries over, but new leader gets a "new leader" buffer

**Fiscal crisis deepens:**
```
If treasury hit 0 in R3, money printing began:
  Printed ~2 coins -> inflation += (2/2.2) * 80 = +72.7 percentage points
  New inflation: 7.5 + 72.7 = 80.2%
  Inflation friction on stability: -(80.2 - 7.5 - 3) * 0.05 - (80.2 - 7.5 - 20) * 0.03
    = -3.485 - 1.491 = -4.976, capped at -0.50 (Cal-4)
```

**CRITICAL FINDING #5:** The money printing -> inflation -> stability spiral is CAPPED by Cal-4 at -0.50/round. This is a crucial safety valve. Without the cap, Ruthenia would collapse to stability 1.0 within 1-2 rounds of money printing. With the cap, the inflation stability drag is painful but survivable.

**Militia mechanic test:**
```
Ruthenia GDP = ~2.0 at this point
Militia units = max(1, min(3, 2.0/30)) = max(1, min(3, 0.067)) = 1 unit
Combat effectiveness: 0.5x (militia get -1 dice modifier)
Stability cost: -0.3
```

**FINDING #6:** At GDP 2.0, militia produces only 1 unit with 0.5x effectiveness. This is essentially negligible. The militia mechanic becomes meaningful only for larger economies (GDP 30+ = 1 unit, GDP 60+ = 2 units, GDP 90+ = 3 units). **For Ruthenia specifically, militia is a flavor mechanic, not a survival tool.** This may be acceptable -- Ruthenia's desperation mechanic is mobilization pool, not militia.

---

### ROUNDS 5-6: GRINDING SURVIVAL

**With Bulwark as president, Western aid potentially increased (Shield relationship):**
```
Best case: Columbia restores aid to 3-4 coins/round
Deficit with 4 coins aid: 4.2 - (0.5 + 4.0) = deficit still ~0 (barely breaking even)
Stability: slowly recovering if combat stabilizes
```

**Without increased aid (worst case):**
```
Continuous money printing
Inflation spiraling (but stability impact capped at -0.50)
Economic state transitions: stressed -> crisis by R5 if 2+ triggers active
  Crisis triggers: inflation > baseline + 30? YES (80%+). GDP growth < -1%? YES. Treasury <= 0? YES.
  3 crisis triggers -> crisis state
Crisis GDP multiplier: contraction * 1.3 (30% worse)
Death spiral accelerates
```

**Die Hard zone test:**
- Die Hard gives +1 defender modifier
- With air support (+1) and Die Hard (+1), Ruthenia defenders in Die Hard zone roll at effective +2
- Attacker needs roll >= defender_roll + 1 to win
- With +2 defender modifier: attacker at 0 mods needs to roll 3+ higher on d6 to win
- Probability per pair: attacker wins ~16.7% of matchups (only 6 vs 3, 6 vs 4, 5 vs 3)
- **Die Hard zone is extremely defensible.** Near-impregnable with air support.

**FINDING #7:** Die Hard + air support creates a fortress zone. Sarmatia would need overwhelming force (3:1+) to crack it, and even then losses would be severe. This is correct gameplay -- it forces Sarmatia to negotiate or escalate (missiles/nuclear). **Die Hard zone works as designed.**

---

### ROUNDS 7-8: ENDGAME SCENARIOS

**Scenario A: Western aid restored + Die Hard holds**
- Treasury stabilizes at ~0 (hand-to-mouth)
- Stability recovers to ~4-5 over 2-3 rounds
- Ceasefire negotiations possible (Broker's diplomacy or Bulwark's position of relative strength)
- EU peace track: Broker can negotiate even as opposition -- informal channel
- **Ruthenia survives. Barely. Gameplay is rich.**

**Scenario B: Western aid cut + Sarmatia offensive**
- Money printing continues, inflation 100%+
- Crisis state by R5, potential collapse by R7-8
- Stability hits 2-3, revolution check possible
- Ruthenia likely forced to accept unfavorable terms
- **Ruthenia collapses. Gameplay still exists -- it becomes about negotiating surrender terms.**

**Scenario C: Sarmatia escalates with missiles**
- Conventional missile strike: 10% of ground units (1 unit) destroyed per strike
- Sarmatia has 12 strategic missiles
- Can destroy Ruthenia's army systematically over 5-6 strikes
- Air defense (1 unit) provides 3 intercept attempts at 30% each
  = ~66% chance of intercepting at least one missile, ~34% chance none intercepted
- **Ruthenia's AD is thin. 1 unit is barely functional for defense.**

---

## KEY FINDINGS

### FINDING 1: Fiscal Model (CRITICAL)
Ruthenia's revenue (0.25 coins/round) covers 5.5% of mandatory costs. This is correct -- it creates absolute aid dependency. But the gap between "barely surviving with aid" and "instant collapse without aid" is razor-thin. **A single round of delayed aid is catastrophic.**

**Risk:** If Columbia's player forgets or delays the aid transfer, Ruthenia dies mechanically. This may frustrate the Ruthenia player.

**Recommendation:** Consider making 1 coin of baseline Western aid AUTOMATIC (engine-generated each round as "EU package"), with the remaining 1-2 coins as player-decided (Columbia discretionary). This preserves the dependency gameplay while preventing accidental mechanical death.

### FINDING 2: Election Formula (IMPORTANT)
The wartime election formula is heavily stacked against Beacon. AI score of ~2.5 means Beacon needs 97.5% player support to win. **The election is functionally predetermined** unless Beacon achieves something extraordinary (territory recovery, EU breakthrough, visible ceasefire).

**Risk:** Beacon's player may feel the outcome is inevitable, reducing engagement.

**Recommendation:** This is arguably correct design -- the election is a transition mechanic, not a 50/50 gamble. But ensure the role brief makes it clear that Beacon CAN win if they achieve visible results. The formula should reward achievement.

### FINDING 3: Militia Mechanic for Small Economies (MINOR)
At GDP 2.2, militia produces 1 unit at 0.5x effectiveness. Near-zero military impact. The mechanic is designed for larger economies.

**Recommendation:** Consider adding a floor of 2 militia units for countries under active invasion, regardless of GDP. This would make the desperation option meaningful for Ruthenia.

### FINDING 4: Money Printing Safety Valve (POSITIVE)
Cal-4 cap on inflation stability friction (-0.50/round) prevents single-round stability collapse. This is essential for Ruthenia's playability. **Without this cap, Ruthenia is unplayable.**

### FINDING 5: Die Hard Zone (POSITIVE)
Die Hard + air support creates a defensible position that forces strategic decisions. Working as intended.

### FINDING 6: Three-Way Political Dynamic (POSITIVE)
Beacon-Bulwark-Broker triangle creates genuine tension:
- Beacon: hold on, resist, maintain legitimacy
- Bulwark: wait for election, build military credibility
- Broker: negotiate back-channels, EU track, peace framework
Each player has distinct mechanical levers. No idle roles.

### FINDING 7: Aid Pipeline as Gameplay (POSITIVE)
The dependency on Western aid creates the core diplomatic gameplay. Ruthenia must constantly negotiate, persuade, and compromise to survive. This is excellent design.

---

## ISSUES LOG

| # | Severity | Issue | Recommendation |
|---|----------|-------|----------------|
| T8-1 | HIGH | Single-round aid delay = mechanical death. Ruthenia treasury depleted by R3 even WITH baseline aid. | Add 1 coin automatic EU aid per round (engine-generated). Remaining aid is player-decided. |
| T8-2 | MEDIUM | Election AI score ~2.5 for Beacon makes defeat near-certain. Player may feel disempowered. | Ensure role brief communicates this. Consider adding territory_held_bonus to election formula: +3 per zone NOT lost since R1. |
| T8-3 | LOW | Militia produces 1 unit at 0.5x for GDP 2.2. Flavor only. | Add floor of 2 militia units for invaded countries. |
| T8-4 | LOW | Ruthenia has 1 AD unit. 3 intercept attempts at 30% = thin missile defense. | Intentional design. No change needed -- creates aid dependency for Patriot batteries. |
| T8-5 | INFO | Mobilization pool (4 uses) creates meaningful strategic choices: when to use, partial vs full. Working correctly. | No change. |

---

## PLAYABILITY ASSESSMENT

| Dimension | Rating | Notes |
|-----------|--------|-------|
| Too desperate? | NO (with aid) | Ruthenia survives with aid. Without aid, collapses R2-3. This is the design intent. |
| Too easy? | NO | Never easy. Always on the edge. Every decision matters. |
| Player engagement (Beacon) | MEDIUM | 3 rounds of full power, then likely election loss. Rich but short. |
| Player engagement (Bulwark) | HIGH | Political positioning R1-3, then presidency R4+. Full arc. |
| Player engagement (Broker) | HIGH | Diplomatic gameplay throughout. EU track, peace negotiation, coalition building. |
| Mechanical choices per round | 2-3 meaningful | Budget (what to cut), mobilization (when to use), diplomacy (who to approach for aid). |
| Narrative coherence | HIGH | Follows real-world Ruthenia/Ukraine trajectory closely. Feels authentic. |

---

## FINAL VERDICT

**CONDITIONAL PASS**

Ruthenia is playable, desperate by design, and produces rich three-way political gameplay. The fiscal model correctly creates aid dependency. Die Hard zone works. Mobilization pool creates strategic choices. The election formula drives a mid-game political transition that is dramatically compelling.

**Conditions for PASS:**
1. Address T8-1 (automatic baseline EU aid) or provide facilitator guidance for managing aid flow
2. Review T8-2 (election formula) to ensure Beacon has a visible path to survival (not just theoretical)

**No conditions for:**
- T8-3 (militia floor) -- nice to have, not blocking
- T8-4 (AD units) -- working as intended
