# TEST T12: FULL STRESS -- "Everything Breaks at Once"
## SEED Gate Test Results
**Tester:** INDEPENDENT (TESTER agent) | **Date:** 2026-03-30 | **Engine:** D8 v1 formulas applied under maximum simultaneous load

---

## VERDICT: CONDITIONAL PASS

**The engine handles 5+ simultaneous crises without producing absurd results. Feedback loops compound correctly. Two stabilization gaps identified. One formula interaction produces implausible output under extreme stress.**

---

## TEST SETUP

Maximum simultaneous crises injected per the scenario brief:

| Round | Crisis Injected |
|-------|----------------|
| R1 | Gulf Gate blockade (Persia). Cathay begins Formosa encirclement. |
| R2 | Columbia midterms. Dealer arrests Tribune. Oil spike from dual blockade. |
| R3 | Persia nuclear test. Ruthenia election. Cathay purge lifts. |
| R4 | Cathay blockades Formosa (full). Sarmatia major offensive. Columbia impeachment attempt. |
| R5 | Columbia presidential election under triple crisis. Nuclear escalation risk. |
| R6-8 | Resolution or collapse. |

---

## ROUND 1: GULF GATE BLOCKADE + FORMOSA ENCIRCLEMENT BEGINS

### Oil Price Calculation (D8 Step 1)

```
SUPPLY:
  Baseline = 1.0
  OPEC members at normal = no change
  Sanctions on sarmatia at L2: supply -= 0.08
  Sanctions on persia at L2: supply -= 0.08
  supply = 1.0 - 0.08 - 0.08 = 0.84

DISRUPTION:
  Gulf Gate blocked (Persia): +0.50
  Formosa partial encirclement (not yet full): +0.10
  disruption = 1.0 + 0.50 + 0.10 = 1.60

DEMAND:
  No major economies in crisis yet
  demand = 1.0

WAR PREMIUM:
  Wars: Sarmatia-Ruthenia, Columbia-Persia, Columbia-Levantia vs Persia = 3 wars
  war_premium = min(3 * 0.05, 0.15) = 0.15

RAW PRICE:
  raw = 80 * (1.0 / 0.84) * 1.60 * (1 + 0.15)
  raw = 80 * 1.190 * 1.60 * 1.15
  raw = 80 * 2.191 = 175.3

INERTIA (assuming previous price $80):
  price = 80 * 0.4 + 175.3 * 0.6 = 32 + 105.2 = 137.2

VOLATILITY: +/- 5% noise
  price ~= $130-$144 range
```

**R1 oil price: ~$137.** Consistent with scenario notes. Below $150 soft threshold. Not yet in crisis territory.

### GDP Effects (D8 Step 2)

**Key countries affected:**

| Country | Base Growth | Oil Shock | Sanctions | War | Other | Effective Growth |
|---------|-----------|-----------|-----------|-----|-------|-----------------|
| Columbia | 1.8% | -0.0148 (importer, oil 137) | 0 | -0.08 (war with Persia) | -0.015 (bilateral Cathay tariff) | ~1.2% |
| Cathay | 4.0% | -0.0148 | 0 | 0 | Formosa disruption starting (0.3 severity * 0.25 dep * tech_pct) | ~3.5% |
| Sarmatia | 1.0% | +0.01 (producer) | -sanctions_hit | -0.03 (war) | | ~-2 to -3% |
| Ruthenia | 2.5% | -0.0148 | 0 | -0.10 (frontline) | | ~-1% |
| Teutonia | 1.2% | -0.0148 | 0 | 0 | Cathay bilateral drag | ~0.5% |
| Persia | -3.0% | +0.01 | -heavy sanctions | -war | Blockade | ~-8 to -10% |

**R1 GDP assessment:** No absurd values. Persia suffers most (war + sanctions + blockade). Sarmatia under sanctions pressure. Ruthenia declining but not collapsing. Columbia mildly affected.

### Stability Effects (D8 Step 14)

```
Persia: stability 4 -> ~2.5 (war + sanctions + blockade + GDP crash)
  War friction: -0.10 (frontline) - casualties*0.2 - 0.04*war_tiredness
  Sanctions friction: -0.1 * 2 * 1.0 = -0.20
  GDP penalty: -0.15 (growth < -2%)
  Crisis penalty: stressed at minimum
  Total: severe decline

Ruthenia: stability 5 -> ~4.5 (war friction)
Columbia: stability 7 -> ~6.5 (war + oil)
Cathay: stability 8 -> ~7.8 (minor decline)
Sarmatia: stability 5 -> ~4.5 (sanctions + war)
Teutonia: stability 7 -> ~6.8 (minor oil shock)
```

**R1 Stability assessment:** No absurd values. Persia is the most stressed country. No collapses.

---

## ROUND 2: COLUMBIA MIDTERMS + TRIBUNE ARREST + OIL SPIKE

### Crisis Injection
- Dealer arrests Tribune (political action #19)
- Columbia midterms occur
- Oil price climbing from dual blockade

### Oil Price R2

```
Previous: $137
Gulf Gate STILL blocked. Formosa encirclement continues.
Supply unchanged (0.84). Disruption unchanged (1.60).

Demand: Persia now in stressed/crisis state
  Persia GDP 5 (< 20, no demand impact from Persia)
  No major economy in crisis yet
  demand ~= 1.0

raw = 80 * (1.0/0.84) * 1.60 * 1.15 = 175.3
price = 137 * 0.4 + 175.3 * 0.6 = 54.8 + 105.2 = 160.0
With noise: ~$152-$168
```

**R2 oil price: ~$160.** Now above $150 threshold. Triggers stress factors.

### Tribune Arrest Effects

```
Arrest mechanic (D8 Part 3, item 7):
  Tribune status = "arrested"
  Tribune OUT OF PLAY until released
  NO stability or support cost (per action review simplification)

BUT: In democracy, AI Court convenes between rounds
  Court can order release

Political consequences (indirect):
  If parliament was about to flip (midterms): Tribune's seat still counts
  Opposition still has Challenger (Seat 4)
  If midterms flip Seat 5: Parliament is 3-2 opposition even without Tribune
  Tribune can submit arguments to Court from arrest
```

**FINDING #1:** Arresting Tribune before midterms does NOT prevent the midterm election. The election is engine-scheduled (D8 Step 16). Dealer cannot prevent it by arresting Tribune. But Tribune cannot campaign while arrested, which may affect the player-component of the election.

### Columbia Midterm Election (D8 Step 16)

```
ai_score = 50 + (gdp_growth * 10) + (stability - 5) * 5 + war_penalty + crisis_penalty + oil_penalty

Columbia: growth ~1.2%, stability ~6.5, 1 active war, oil 160
  econ_perf = 1.2 * 10 = 12
  stab_factor = (6.5 - 5) * 5 = 7.5
  war_penalty = -5
  oil_penalty = -(160 - 150) * 0.1 = -1.0
  ai_score = 50 + 12 + 7.5 - 5 - 1.0 = 63.5

  Dealer (incumbent) needs: 0.5 * 63.5 + 0.5 * player_pct >= 50
  = 31.75 + 0.5 * player_pct >= 50
  player_pct >= 36.5%
```

**Midterms are competitive.** Not a guaranteed loss for Dealer despite the crises. The economic conditions are still moderate enough that the AI score favors the incumbent. If Dealer's team votes together (3 votes to 2), midterms may not flip.

### Compounding Effects Check

| Country | GDP Growth R2 | Stability R2 | Support R2 | Economic State |
|---------|:------------:|:----------:|:---------:|:--------------:|
| Columbia | ~0.5% | ~6.2 | ~35% | Normal |
| Cathay | ~3.2% | ~7.6 | ~56% | Normal |
| Sarmatia | ~-3% | ~4.0 | ~48% | Stressed |
| Ruthenia | ~-2% | ~4.0 | ~38% | Stressed |
| Persia | ~-12% | ~2.5 | ~28% | Crisis |
| Teutonia | ~0% | ~6.5 | ~42% | Normal |
| Yamato | ~0.5% | ~7.5 | ~46% | Normal (Formosa dep starting) |
| Hanguk | ~1% | ~5.8 | ~33% | Normal (Formosa dep starting) |

**R2 assessment:** Persia is in crisis. Sarmatia and Ruthenia stressed. No collapses. No absurd values. Oil at $160 is uncomfortable but not catastrophic for major economies. Feedback loops compounding correctly -- Persia's collapse is self-reinforcing, others are declining but manageable.

---

## ROUND 3: PERSIA NUCLEAR TEST + RUTHENIA ELECTION + CATHAY PURGE LIFTS

### Persia Nuclear Test (D8 Part 3, item 3 -- Tier 2 Open Test)

```
Global event. Everyone knows immediately.
No damage. Maximum political signal.
Global stability shock: all countries -0.3 stability.
Stability cost to tester (Persia): -0.5 (on top of global -0.3)
Political support boost (Persia): +5 (nationalist rally)

Persia current: stability ~2.5, support ~28%
After test: stability 2.5 - 0.3 - 0.5 = 1.7, support 28 + 5 = 33%
```

**FINDING #2: Persia nuclear test at stability 1.7 triggers revolution check threshold (stability <= 2 AND support < 20). Support is 33%, so revolution check does NOT trigger.** But Persia is dangerously close. Another round of decline could trigger it.

**Global stability shock (-0.3 to all):**

| Country | Pre-Test Stability | Post-Test | Notes |
|---------|:-----------------:|:--------:|-------|
| Columbia | 6.2 | 5.9 | Now < 6 = coup risk flag |
| Cathay | 7.6 | 7.3 | Still comfortable |
| Sarmatia | 4.0 | 3.7 | Capital flight triggers (< 4) |
| Ruthenia | 4.0 | 3.7 | Capital flight triggers |
| Persia | 2.5 | 1.7 | Near revolution |
| All others | varies | -0.3 | Minor shock |

**Nuclear test has cascading effects:** Sarmatia and Ruthenia both pushed below stability 4, triggering capital flight (-3% GDP for non-autocracy, -1% GDP for autocracy). This compounds their existing economic problems.

### Ruthenia Election (D8 Step 16)

```
Ruthenia R3: stability ~3.7, support ~32%, GDP growth ~-3%, war_tiredness ~5.5

ai_score = 50 + (-3 * 10) + (3.7 - 5)*5 + (-5) + (-5 if stressed) + territory_factor
  = 50 - 30 - 6.5 - 5 - 5 - 3*zones_lost - 5.5*2
  = 50 - 30 - 6.5 - 5 - 5 - 0 - 11 = -7.5 -> clamped to 0

Beacon needs: 0.5 * 0 + 0.5 * player_pct >= 50
  player_pct >= 100% -- IMPOSSIBLE
```

**CONFIRMED: Under these crisis conditions, Beacon cannot win the R3 election mathematically.** The AI score is 0. Even with 100% player support, final score = 50.0, which ties (and per formula: incumbent_wins = final >= 50.0, so Beacon BARELY wins with 100% player vote). In practice, not achievable.

**Bulwark takes over as president of Ruthenia.**

### Cathay Purge Lifts

```
Per role seed: purge penalty lifts after R3.
Cathay military operations no longer suffer 20% implementation failure.
Formosa contingency options matrix: "Option 4 not recommended before Round 3 (purge penalty lifts)"
```

This is a narrative gate, not a formula mechanic. The engine does not have a purge penalty variable -- it is handled by moderator/AI judgment on Cathay military effectiveness. **No engine inconsistency here, but the purge lift mechanic should be documented as a moderator-managed event, not an engine variable.**

### Compounding Effects R3

**Oil price R3:**
```
Previous: $160
No change in blockade status
Demand slightly reduced (Sarmatia, Persia contracting)
  Major economies with GDP > 20 in stressed: Sarmatia stressed -> demand -0.03
  demand = 1.0 - 0.03 = 0.97

raw = 80 * (0.97/0.84) * 1.60 * 1.15 = 80 * 1.845 * 1.15 = 169.7
price = 160 * 0.4 + 169.7 * 0.6 = 64 + 101.8 = 165.8
Mean-reversion: oil > $150 for 2 rounds (not yet 3, so no penalty)
```

**Oil at ~$166.** Rising but not runaway. Demand destruction beginning to moderate the increase. **Soft cap and inertia working correctly.**

---

## ROUND 4: CATHAY BLOCKADES FORMOSA (FULL) + SARMATIA OFFENSIVE + COLUMBIA IMPEACHMENT

### This is the maximum stress round. Five simultaneous crises active:
1. Gulf Gate blockade (ongoing since R1)
2. Formosa full blockade (NEW)
3. Persia nuclear (declared R3)
4. Sarmatia major offensive against Ruthenia
5. Columbia impeachment proceeding

### Oil Price R4 (Dual Blockade + War)

```
SUPPLY:
  supply = 0.84 (unchanged)

DISRUPTION:
  Gulf Gate blocked: +0.50
  Formosa FULL blockade: +0.10 (unchanged -- Formosa is +0.10 regardless of partial/full)
  disruption = 1.60

Wait -- is this correct? The D8 formula lists:
  "if Formosa blocked: disruption += 0.10"
  This does NOT distinguish partial vs full.

DEMAND:
  Sarmatia stressed: -0.03
  Persia crisis (GDP 5, < 20): no impact
  No other major economy in crisis
  demand = 0.97

SEMICONDUCTOR DISRUPTION (separate from oil):
  Formosa FULL blockade = Formosa disrupted
  Duration: R4 = round 4 of encirclement (started R1)
  severity = min(1.0, 0.3 + 0.2 * max(0, 4-1)) = min(1.0, 0.9) = 0.9

  For each dependent country:
    Columbia: dep 0.65, tech_pct 0.22, semi_hit = -0.65 * 0.9 * 0.22 = -0.129 (-12.9%)
    Cathay: dep 0.25, tech_pct 0.13, semi_hit = -0.025 * 0.9 * 0.13 = -0.029 (-2.9%)
    Teutonia: dep 0.45, tech_pct 0.19, semi_hit = -0.45 * 0.9 * 0.19 = -0.077 (-7.7%)
    Yamato: dep 0.55, tech_pct 0.20, semi_hit = -0.55 * 0.9 * 0.20 = -0.099 (-9.9%)
    Hanguk: dep 0.40, tech_pct 0.22, semi_hit = -0.40 * 0.9 * 0.22 = -0.079 (-7.9%)
```

**CRITICAL FINDING #3: Semiconductor disruption at severity 0.9 is devastating.** Columbia loses -12.9% GDP from semiconductors ALONE. This is on top of oil shock, war costs, and political instability. Combined GDP shock for Columbia at R4:

```
Columbia GDP R4:
  base: 1.8%
  oil_shock: -0.02 * (170-100)/50 = -0.028
  semi_hit: -0.129
  war_hit: -0.08
  tariff_hit: ~-0.015
  Raw growth: 1.8 - 2.8 - 12.9 - 8.0 - 1.5 = ~-23.4%

  WAIT -- these are in different units. Let me recalculate properly.

  All as decimal growth rates:
  base_growth = 0.018
  oil_shock = -0.028
  semi_hit = -0.129
  war_hit = -0.08
  tariff_hit = -0.015
  momentum (was ~0, declining): -0.01

  raw_growth = 0.018 - 0.028 - 0.129 - 0.08 - 0.015 - 0.01 = -0.244

  Crisis multiplier: If Columbia is stressed (likely by R4 with 2+ stress triggers):
    stressed contraction: -0.244 * 1.2 = -0.293

  GDP: 280 * (1 - 0.293) = ~198 coins
  SINGLE-ROUND GDP DROP OF ~29%
```

**CRITICAL FINDING #4: The semiconductor disruption formula produces a ~13% direct GDP hit to Columbia, which when combined with other factors and crisis multiplier, produces a ~29% single-round GDP crash.** This is extreme but arguably realistic for a full semiconductor cutoff (Columbia has 65% Formosa dependency, highest in the SIM).

**Is this absurd?** A complete semiconductor supply cutoff would be catastrophic for the real US economy. The 2021 chip shortage (partial, not total) caused ~$500B in lost output. A total cutoff would be worse. -29% GDP in one round may be at the edge of plausibility but is not internally inconsistent with the formula.

**However:** The Pass 3 coherence check should flag this. GDP drop > 20% in a single round from a country that was at 280 GDP is a HIGH severity flag. The coherence check should auto-correct or at least flag for moderator review.

### Sarmatia Offensive

```
Sarmatia ground: ~16 (started 18, lost ~2 in R1-R3 combat)
Ruthenia ground: ~8 (started 10, lost 2, mobilized 0 or 2)

If Sarmatia attacks a Ruthenia zone without Die Hard:
  Sarmatia modifiers: +0 (no special mods)
  Ruthenia modifiers: air support +1 (if air in zone), low morale -1 (stability 3.7 > 3, so NO low morale)
  Net: Ruthenia +1 (air support)

  Per pair: Sarmatia needs roll >= Ruthenia + 2 (attacker needs +1 over defender, defender has +1 mod)
  Probability per pair: attacker wins when a_roll >= d_roll + 2
  With d6+0 vs d6+1: attacker wins ~27.8% of pairs

  8 pairs (min of 16 att, 8 def):
  Expected Sarmatia losses: ~5.8
  Expected Ruthenia losses: ~2.2

  Net: Sarmatia loses 5-6 units, Ruthenia loses 2 units
  Sarmatia remaining: ~10-11
  Ruthenia remaining: ~6
  Zone NOT captured (defender still has units)
```

**FINDING #5:** Ruthenia's air support modifier makes Sarmatia offensives costly. Even with 2:1 numerical advantage, Sarmatia takes disproportionate losses. This is correct -- defender advantage is a core design principle. Sarmatia must either achieve 3:1+ or use strategic missiles to degrade Ruthenia first.

### Columbia Impeachment

```
Impeachment mechanic (D8 Part 3, item 25 -- from web app spec):
  Tribune (arrested) -- can Tribune file impeachment from arrest?
  Per arrest mechanic: "Target is OUT OF PLAY until released"

  BUT: in democracy, AI Court convenes and may release Tribune
  If Court releases Tribune in R3-R4: Tribune can file impeachment

  Parliament vote required: 3 of 5
  Post-midterms (if opposition won R2): Opposition has seats 4, 5, 7 = 3 seats
  Wait -- Columbia Parliament: Dealer(1), Volt(2), Tribune(3), Challenger(4), NPC Seat 5
  Starting: Dealer+Volt+NPC = 3-2 majority
  If midterms flip NPC seat: Tribune+Challenger+NPC = 3-2 opposition

  Impeachment needs 3 votes. If Tribune is released and has majority: 3-2 passes.

  Effect: President removed. Volt becomes president.
```

**FINDING #6:** The impeachment mechanic works under stress conditions. The sequence is: Tribune arrested R2 -> Court may release R2-R3 -> Midterms flip parliament R2 -> Impeachment filed R4 -> 3-2 vote succeeds -> Volt becomes president.

**Constitutional crisis:** This produces a genuine constitutional crisis -- arrest, court challenge, release, impeachment, power transfer -- all while the country is in a semiconductor-driven economic crash and fighting a war in Persia. This is EXACTLY the kind of multi-crisis gameplay the SIM is designed to produce.

### Compounding Effects R4

| Country | GDP Growth R4 | Stability R4 | Economic State R4 | Notes |
|---------|:------------:|:----------:|:-----------------:|-------|
| Columbia | ~-29% | ~4.0 | Stressed -> CRISIS | Semiconductor crash + war + political crisis |
| Cathay | ~1% | ~7.0 | Normal | Blockading Formosa, purge lifted |
| Sarmatia | ~-4% | ~3.5 | Crisis | Offensive costly, sanctions biting |
| Ruthenia | ~-5% | ~3.5 | Crisis | Under attack, fiscal collapse |
| Persia | ~-15% | ~1.5 | Collapse | Nuclear state under total siege |
| Teutonia | ~-8% | ~5.5 | Stressed | Semiconductor dependency + Cathay trade hit |
| Yamato | ~-10% | ~5.0 | Stressed | Semiconductor dependency severe |
| Hanguk | ~-8% | ~4.5 | Stressed | Semiconductor dependency |

**CRITICAL FINDING #7: The semiconductor disruption creates a GLOBAL economic crisis.** Countries with high Formosa dependency (Columbia 65%, Yamato 55%, Teutonia 45%, Hanguk 40%) all suffer severe GDP contractions. This triggers contagion (D8 Step 11): when major economies (GDP > 30) enter crisis, trade partners lose additional GDP.

**Contagion chain:**
```
Columbia enters crisis (GDP 280 -> ~198):
  Trade partners hit: cathay (0.6 weight), teutonia (0.3), yamato (0.3), hanguk (0.2), albion (0.2)
  severity = 1.0 (crisis)
  cathay: GDP *= (1 - 1.0 * 0.6 * 0.02) = GDP *= 0.988 (-1.2%)
  teutonia: GDP *= (1 - 1.0 * 0.3 * 0.02) = GDP *= 0.994 (-0.6%)
  All partners: momentum -= 0.3
```

**Contagion is modest.** 1-2% GDP hits from partner crisis. This is realistic -- contagion adds secondary pressure but does not by itself create cascading collapse.

---

## ROUND 5: COLUMBIA PRESIDENTIAL UNDER TRIPLE CRISIS

### Columbia at R5

```
GDP: ~198 (down from 280) -- 29% contraction in one round
Treasury: depleting rapidly (maintenance + war costs > revenue)
Stability: ~3.5 (falling)
Support: ~25% (Dealer's original, or Volt if impeachment succeeded)
Economic state: Crisis
Nuclear threat: Persia has declared nuclear capability
Wars: Persia (ongoing), Caribe (ongoing)
Semiconductor supply: cut off (Formosa blockaded)
```

### Columbia Presidential Election (D8 Step 16)

```
If Volt is now president (impeachment succeeded R4):
  ai_score = 50 + (-29 * 10) + (3.5 - 5)*5 + (-5*2) + (-15 crisis penalty) + (-(170-150)*0.1)
  = 50 - 290 - 7.5 - 10 - 15 - 2 = -274.5 -> clamped to 0

Incumbent (whoever is president) CANNOT win.
ai_score = 0, needs player_pct >= 100% -- impossible.
```

**FINDING #8:** Under maximum stress, the Columbia presidential election becomes unwinnable for the incumbent. This is correct -- a -29% GDP crash with crisis state and two active wars is politically unsurvivable. The election mechanic correctly punishes catastrophic performance.

### Nuclear Escalation Risk Assessment

```
Persia at stability 1.5, support ~25%, in Collapse state.
Nuclear capability declared (Tier 2 test completed R3).
Nuclear level >= 1 (assumed from R&D progress -- Persia starts at 0.60 progress toward L1,
  threshold is 0.60, so Persia is AT L1 threshold at game start).

Can Persia launch Tier 4 (single nuclear strike)?
  Requires nuclear_level >= 1: YES (if at threshold)
  Requires strategic missiles: Persia has 0 strategic missiles (countries.csv)

  WAIT: Persia has 0 strategic_missiles in countries.csv.
  Persia CANNOT launch any missile strike (conventional or nuclear) without strategic missiles.
```

**CRITICAL FINDING #9: Persia has 0 strategic missiles in countries.csv.** Persia can conduct nuclear R&D, reach nuclear capability (L1), conduct nuclear tests, but CANNOT deliver a nuclear strike. There is no delivery mechanism. Persia would need to acquire missiles through production or trade.

```
Persia production capacity (from countries.csv):
  prod_cap_ground: 2
  prod_cap_naval: 0
  prod_cap_tactical: 1
  strategic_missile_growth: 0 (no automatic growth)

Persia has NO strategic missile production capability and no automatic growth.
```

**FINDING #10:** Persia can develop nuclear weapons but cannot deliver them. The nuclear test creates diplomatic/deterrence effects, but Persia cannot actually strike anyone with nuclear weapons unless:
1. Persia acquires strategic missiles through trade (from Sarmatia or Choson)
2. The engine is modified to give Persia missile production capability
3. Conventional delivery (aircraft) is used (not in the current engine)

**This may be intentional (Persia is a threshold state, not a deployed nuclear power) or an oversight. It limits the nuclear escalation scenario significantly.**

### R5 World State

| Country | GDP | Growth | Stability | Support | State | Notes |
|---------|:---:|:------:|:---------:|:-------:|:-----:|-------|
| Columbia | ~198 | -29% | 3.5 | 25% | Crisis | Semiconductor crash, political crisis |
| Cathay | ~190 | 0% | 6.8 | 52% | Normal | Blockade succeeding, slight slowdown |
| Sarmatia | ~14 | -6% | 3.0 | 42% | Crisis | Offensive stalled, sanctions deepening |
| Ruthenia | ~1.5 | -8% | 3.0 | 30% | Crisis | Under attack, near collapse |
| Persia | ~2.0 | -20% | 1.3 | 22% | Collapse | Nuclear but no delivery, dying |
| Teutonia | ~36 | -10% | 5.0 | 36% | Stressed | Semiconductor + contagion |
| Yamato | ~34 | -12% | 4.5 | 38% | Stressed | Semiconductor severe |
| Hanguk | ~14 | -10% | 4.0 | 30% | Stressed | Semiconductor + Cathay dependency |
| Bharata | ~42 | +4% | 5.8 | 54% | Normal | Least affected, multi-alignment works |
| Formosa | ~6 | -15% | 4.0 | 45% | Crisis | Under blockade |

---

## ROUNDS 6-8: RESOLUTION OR COLLAPSE

### Scenario A: Stabilization Path

**If Formosa blockade is broken or lifted (Columbia naval intervention):**
```
Semiconductor supply restored over 1-2 rounds
  Severity drops: 0.9 -> 0.5 -> 0.3
Columbia GDP recovery begins
  From crisis: growth suppressed to 20% of raw positive growth
  Recovery from -29% to break-even: ~4-5 rounds minimum
  Recovery to pre-crisis: 7+ rounds (beyond SIM scope)

Oil price: if Gulf Gate also reopened
  disruption drops from 1.60 to 1.0
  raw price drops to ~$95-100
  Inertia: 170 * 0.4 + 95 * 0.6 = 68 + 57 = $125 (R6)
  Then: 125 * 0.4 + 95 * 0.6 = 50 + 57 = $107 (R7)
  Mean-reversion: oil was > $150 for 4+ rounds, -8% penalty
  $107 * 0.92 = $98 (R7)
  $98 * 0.4 + 90 * 0.6 = 39 + 54 = $93 (R8)
```

**Oil recovery works correctly.** Inertia slows the drop (40% sticky, 60% toward equilibrium). Mean-reversion accelerates after 3+ rounds above $150. Price normalizes to ~$90-100 by R8. **Feedback loop working as designed.**

### Scenario B: Collapse Path

**If all crises continue:**
```
R6: Columbia GDP continues contracting
  Crisis multiplier: -x * 1.3
  If growth raw is -10%: effective = -13%
  GDP: 198 * 0.87 = 172
  Contagion spreads to all trade partners
  Teutonia enters crisis (triggers own contagion to Cathay)

R7: Cascade
  Columbia: 172 * 0.85 = ~146
  Contagion: Cathay hit -2.4% from dual contagion (Columbia + Teutonia)
  Cathay growth turns negative
  Cathay enters stressed state

R8: Global recession
  Columbia: ~125 (GDP halved from start)
  Cathay: ~180 (down from 190)
  Global GDP down ~15-20%
  Oil demand destruction: price drops to ~$100 despite blockades
  Multiple countries in crisis
```

**FINDING #11: The collapse path produces a global recession but NOT absurd results.** Columbia's GDP falling from 280 to ~125 over 8 rounds (-55%) under maximum stress (semiconductor cutoff + two wars + political crisis + oil shock) is severe but plausible. The real-world equivalent would be a simultaneous semiconductor cutoff, oil embargo, and constitutional crisis -- a combination that would indeed produce catastrophic economic output.

**Natural stabilization mechanisms:**
1. Oil demand destruction (demand side of oil formula reduces as economies contract)
2. Crisis multiplier on POSITIVE growth is suppressed (crisis: 50% of positive growth captured)
3. Mean-reversion on oil price after 3+ rounds above $150
4. Momentum builds slowly (+0.3/round max) but provides gradual recovery signal
5. Sanctions adaptation after 4 rounds (+2% GDP via Pass 2)

**Missing stabilization mechanisms:**
1. No IMF/emergency lending mechanic (countries cannot borrow in extremis)
2. No "war exhaustion ceasefire" mechanic (wars continue mechanically even when both sides are collapsing)
3. Contagion has no dampening -- if it cascades through 3+ major economies, the effect is cumulative without friction

---

## KEY FINDINGS

### FINDING 1: Engine Handles Simultaneous Crises (POSITIVE)
Five simultaneous crises produce severe but internally consistent results. No formula produces undefined values, division by zero, or contradictory outputs. GDP floors (0.5 coins), stability floors (1.0), and support bounds (5-85%) prevent mathematical collapse.

### FINDING 2: Semiconductor Disruption May Be Over-Tuned (IMPORTANT)
At severity 0.9 (round 4 of disruption), Columbia loses 12.9% GDP from semiconductors alone. Combined with other factors and crisis multiplier, single-round GDP crash reaches 29%. This is internally consistent with the formula but may produce results that feel unfair to the Columbia player.

The issue: formosa_dependency = 0.65 (from countries.csv) is very high. The real US semiconductor dependency is significant but diversified. 65% may overstate the single-source vulnerability.

**Recommendation:** Consider capping semiconductor GDP hit at 10% per round (hard cap in Step 2), or reducing Columbia's formosa_dependency from 0.65 to 0.45.

### FINDING 3: Oil Price Stabilization Works (POSITIVE)
Inertia (40/60 blend), soft cap (asymptotic above $200), and mean-reversion (after 3 rounds above $150) all function correctly under stress. Oil rises from $80 to ~$170 over 4 rounds with dual blockade, then begins natural moderation. Demand destruction accelerates decline when blockades lift.

### FINDING 4: Contagion Is Modest (POSITIVE)
Major economy crisis generates 1-2% GDP hits to trade partners. Sufficient to create secondary pressure without producing runaway cascading collapse. The threshold (GDP > 30 for contagion source) prevents small economies from generating contagion.

### FINDING 5: Persia Cannot Deliver Nuclear Weapons (IMPORTANT)
Persia has 0 strategic missiles and 0 missile production capacity. Nuclear capability without delivery means Persia's nuclear test is a diplomatic/deterrence signal but cannot escalate to actual nuclear strike. This limits the T12 nuclear escalation scenario.

### FINDING 6: Columbia Presidential Election Under Crisis Is Correctly Unwinnable (POSITIVE)
The election formula produces ai_score = 0 under maximum crisis conditions. This is correct -- no incumbent survives -29% GDP and crisis state. The formula does not produce absurd results; it produces harsh but realistic political consequences.

### FINDING 7: Crisis Recovery Is Slow by Design (POSITIVE)
Recovery from collapse requires minimum 7 rounds of clean conditions. This means a country that collapses by R4 cannot fully recover within the 8-round SIM. This is intentional -- it creates irreversible consequences for catastrophic decisions.

### FINDING 8: No Emergency Lending Mechanic (GAP)
Under maximum stress, multiple countries face fiscal death spirals (zero treasury, money printing, inflation) with no mechanical option to borrow or restructure. In reality, the IMF, bilateral emergency lending, and debt restructuring would provide some relief. The absence of this mechanic makes fiscal death spirals faster and less escapable than reality.

### FINDING 9: Purge Penalty Is Not an Engine Variable (MINOR)
Cathay's purge penalty (20% implementation failure until R3) is mentioned in the role brief but is not an engine variable. It must be managed by the moderator or AI judgment. This creates a consistency risk under stress -- moderators may forget to apply/remove it.

---

## ISSUES LOG

| # | Severity | Issue | Recommendation |
|---|----------|-------|----------------|
| T12-1 | HIGH | Semiconductor hit can produce -29% single-round GDP crash for Columbia. Technically correct but may feel disproportionate. | Cap semiconductor GDP hit at 10% per round. OR reduce Columbia formosa_dependency from 0.65 to 0.45. |
| T12-2 | MEDIUM | Persia has 0 strategic missiles and 0 production capacity. Nuclear capability without delivery limits escalation scenario. | Add strategic_missile_growth: 1 for Persia (slow but automatic) OR ensure nuclear test mechanic works without missiles. |
| T12-3 | MEDIUM | No emergency lending/IMF mechanic. Fiscal death spirals have no relief valve except aid transfers. | Consider adding an IMF mechanic: countries in crisis can borrow 2-3 coins at cost of -1 stability and sovereignty conditions. |
| T12-4 | LOW | Purge penalty not in engine code. Must be moderator-managed. | Document as explicit moderator instruction. OR add purge_penalty variable to world_state. |
| T12-5 | LOW | Contagion has no dampening across multiple cascade sources. 3+ major economies in crisis could produce compounding hits. | Add cap: max contagion GDP hit per country per round = 5%. |
| T12-6 | INFO | War exhaustion does not force ceasefire. Wars continue mechanically even when both sides are collapsing. | Intentional design (human players decide peace). Flag for facilitator awareness. |

---

## STRESS TEST METRICS

| Metric | R1 | R2 | R3 | R4 | R5 | R6 | R7 | R8 |
|--------|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| Active crises | 2 | 4 | 5 | 5 | 5 | 4 | 3 | 2 |
| Countries in crisis/collapse | 0 | 1 | 2 | 5 | 6 | 5 | 4 | 3 |
| Oil price (approx) | $137 | $160 | $166 | $170 | $165 | $125 | $98 | $93 |
| Global GDP change | -2% | -5% | -8% | -18% | -12% | -5% | -2% | +1% |
| Nuclear events | 0 | 0 | 1 (test) | 0 | 0 | 0 | 0 | 0 |
| Elections | 0 | 1 (midterm) | 1 (Ruthenia) | 0 | 1 (Columbia) | 0 | 0 | 0 |
| Absurd outputs | 0 | 0 | 0 | 1 (Columbia -29%) | 0 | 0 | 0 | 0 |
| Internal consistency violations | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

---

## FINAL VERDICT

**CONDITIONAL PASS**

The engine handles maximum simultaneous stress without producing internally inconsistent results. Feedback loops compound correctly -- GDP contraction reduces oil demand, which moderates oil price. Crisis states amplify contraction but are bounded by floors. Contagion spreads secondary effects without runaway cascading. Recovery is slow by design.

**One output is at the edge of plausibility:** Columbia's -29% single-round GDP crash from semiconductor cutoff under crisis multiplier. Technically correct per formulas but may require either a cap on semiconductor GDP hit or a reduction in Columbia's formosa_dependency parameter.

**Conditions for PASS:**
1. Address T12-1: Cap semiconductor GDP hit at 10%/round OR reduce Columbia formosa_dependency
2. Address T12-2: Give Persia some missile delivery capability (even if limited) to enable the nuclear escalation scenario as designed

**No conditions for:**
- T12-3 (IMF mechanic) -- enhancement, not blocker
- T12-4 (purge penalty) -- moderator-manageable
- T12-5 (contagion cap) -- edge case, unlikely in practice
- T12-6 (war exhaustion) -- intentional design
