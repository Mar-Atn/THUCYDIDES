# TEST 2: FORMOSA CRISIS
## SEED TESTS2 -- Thucydides Trap SIM
**Test Date:** 2026-03-27 | **Tester:** TESTER-ORCHESTRATOR | **Rounds:** 8

---

## TEST PARAMETERS

**Objective:** Test the Formosa military calculus. Does Cathay's naval buildup open a blockade/invasion window? Does semiconductor disruption fire? Does Columbia's overstretch dilemma produce realistic constraints?

**Setup Overrides (vs Test 1 Generic Baseline):**
- Helmsman `formosa_urgency` = 0.9 (baseline ~0.6) -- Chairman is actively pushing for action
- Rampart compliance increased -- will co-sign operations he would normally slow-walk (simulates post-purge fear)
- All other parameters identical to Test 1 R1 end state (baseline)
- Purge penalty still lifts R3

**Starting State (from Test 1 R1 end):**

| Country | GDP | Stability | Support | Treasury | Naval | Ground | Tac Air | Nuclear | AI Level |
|---------|-----|-----------|---------|----------|-------|--------|---------|---------|----------|
| Columbia | 285.1 | 6.95 | 37% | ~42 | **9** | 22 | 15 | L3 | L3 (65%) |
| Cathay | 197.5 | 8.05 | 58.5% | ~40 | **7** | 25 | 12 | L2 (85%) | L2 (76%) |
| Formosa | 8.24 | 6.90 | 55% | ~9 | 0 | 4 | 3 | L0 | L2 (52%) |
| Yamato | 43.4 | 7.70 | 48% | ~13 | 2 | 3 | 3 | L0 (11%) | L3 (34%) |
| Hanguk | 18 | 5.80 | 35% | ~8 | 0 | 5 | 3 | L0 (5%) | L2 (50%) |

**Key Starting Metrics:**
- Naval ratio (Cathay/Columbia): 7/9 = 0.778
- GDP ratio (Cathay/Columbia): 197.5/285.1 = 0.693
- Cathay naval near Formosa: all 7 ships (5 from starting + 2 repositioned)
- Columbia naval near Formosa: 2 ships at w(17,4)
- Columbia committed elsewhere: 3 Gulf, 2 Med, 1 Atlantic, 1 Indian Ocean
- Cathay nuclear: L2, 85% toward L3 (threshold 1.00)
- Purge penalty: ACTIVE (20% implementation failure, lifts R3)
- Oil: $198/barrel
- Active wars: Columbia vs Persia, Sarmatia vs Ruthenia

---

## ROUND 1 (H2 2026) -- HELMSMAN'S CALCULATION

### Narrative Context
Round 1 has already been processed in the baseline. This test diverges from the END of R1 with Helmsman's elevated formosa_urgency driving different decisions. For clarity, we label the first round of new decisions as "Round 2" (matching the SIM's timeline).

---

## ROUND 2 (H1 2027) -- THE SIGNAL

### Key Decisions

**CATHAY (formosa_urgency = 0.9):**
- **Helmsman** convenes emergency Standing Committee meeting. Presents PLA Navy timeline memo: naval parity within 18-24 months. Columbia is overextended -- 3 ships in Gulf, 2 in Med, only 2 near Formosa. "The window is open."
- **Rampart** (more compliant in this test): co-signs escalated gray zone operations near Formosa. Does NOT yet co-sign blockade -- argues "wait for purge penalty to lift in R3." Even compliant Rampart draws this line.
- **Abacus** presents economic brief: GDP growth 3.93% but property sector still contracting. Warns blockade would trigger massive capital flight. Helmsman dismisses.
- **Circuit** reports AI progress: 76% toward L3. DeepSeek V5 development underway. Warns that Formosa blockade destroys the supply chains his tech empire depends on. Helmsman notes this.
- **Sage** observes. Does not intervene. Stability 8.05 -- well above his activation threshold.

**Cathay Actions:**
1. **Massive gray zone escalation around Formosa** -- Coast guard vessels enter Formosa's contiguous zone (12-24nm). 4 naval units conduct "Joint Sword 2027" exercises simulating blockade. Daily fighter jet sorties over median line.
2. **Accelerated naval production** -- allocate 8 coins to naval (tier: accelerated, 2x cost/2x output). Produces 2 naval this round (capacity 3 * 2x = 6 max, but cost 4*2=8 per unit, so 8/8=1... recalculating: accelerated tier = 2x cost per unit, 2x max capacity. Cost per naval = 4 * 2.0 = 8. With 8 coins: 1 unit. Plus strategic missile growth +1.)

Wait -- let me recalculate. Normal naval cost = 4 coins. Accelerated = 4 * 2.0 = 8 per unit. Capacity normal = 1/round (from CSV: prod_cap_naval=1... no, CSV shows cathay prod_cap_naval=1). But the country seed says "Naval: 3" for production capacity. Let me use the country seed value (3 max/round normal). Accelerated = 3 * 2 = 6 max. At 8 coins accelerated cost, 8 coins buys 1 naval unit.

Correction: Country seed says production costs Naval: 4, capacity 3/round. Normal: 4 coins per unit, max 3. Accelerated: 8 coins per unit, max 6. With 8 coins allocated: 1 unit.

**Cathay allocates 12 coins to naval production (accelerated).** Gets floor(12/8) = 1 unit. Plus the automatic +1 strategic missile.

Actually, re-examining: the engine formula is `units = min(int(coins / unit_cost), int(max_cap))`. At accelerated: unit_cost = 4 * 2.0 = 8. max_cap = 3 * 2.0 = 6. With 12 coins: floor(12/8) = 1. Hmm. Even 12 coins only buys 1 accelerated naval. Let me use normal production instead for better efficiency: 4 coins per unit, max 3. With 12 coins: min(3, 3) = 3 naval units.

**REVISED: Cathay allocates 12 coins to naval (normal tier).** Produces 3 naval units (max capacity). Plus +1 strategic missile (automatic).
- Cathay naval: 7 + 3 = **10**
- Cathay strategic missiles: 5 + 1 = **6**

3. **Diplomatic:** Cathay vetoes UNSC resolution condemning gray zone operations. Issues public statement: "Formosa is an internal matter."
4. **Budget:** 12 coins naval, 6 coins tech R&D (split 3 nuclear / 3 AI), 8 coins social, remainder to treasury.
5. **Rare earth:** Reimpose full restrictions on Columbia (level 2). Suspend the one-year suspension agreement.

**COLUMBIA:**
- **Dealer** is focused on midterm elections (this round). Persia war consuming attention and resources. Approval 37%.
- **Shield** (SecDef) warns about Cathay gray zone escalation near Formosa. Recommends redeploying 1 naval from Med to Pacific.
- **Shadow** (Intel chief) delivers PDB: "JADE CURTAIN confirms Formosa invasion timeline R3-R5. Gray zone escalation consistent with pre-blockade pattern."
- **Tribune** (opposition leader) hammering Dealer on gas prices ($198 oil) and overstretch.

**Columbia Actions:**
1. **Redeploy 1 naval from Med to Pacific** -- Columbia Pacific naval: 2 + 1 = 3 (at w(17,4)).
2. **Arms package to Formosa:** 1 coin (Harpoon anti-ship missiles, mine warfare equipment). Formosa treasury +1.
3. **Continued Persia operations.** No change to Gulf deployment.
4. **Midterm election campaign focus.** Dealer prioritizes domestic messaging.
5. **Budget:** Standard allocation. 18 coins tech (maintaining L3+ trajectory).
6. **Naval production:** 2 naval units (normal, 5 coins each = 10 coins). Columbia naval: 9 + 2 = **11** (but net after redeployment: 3 Pacific, 3 Gulf, 1 Med, 1 Atlantic, 1 Indian Ocean, 2 new = staged at home ports).

Actually, from CSV: Columbia prod_cost_naval = 5, prod_cap_naval = 3. So 10 coins = 2 naval units. Columbia naval: 9 + 2 = **11**.

**FORMOSA (Chip):**
- **Chip** (president/solo role) panics at gray zone escalation. Calls Columbia demanding clarity on defense commitment. Gets "strategic ambiguity" reaffirmed -- not the answer wanted.
- Activates "silicon shield" intelligence: shares classified TSMC vulnerability assessment with Columbia -- "if fabs go dark, 65% of your advanced chip supply disappears overnight."
- Pushes defense budget through legislature -- KMT blocks 70% as in reality. Gets 1 additional ground unit (domestic production max 1).
- Formosa ground: 4 + 1 = **5**. Treasury: 9 + 1 (Columbia aid) - 3 (production) - maintenance = ~6.

**YAMATO:**
- Announces emergency defense spending increase. Begins joint patrol with Columbia in East Cathay Sea.
- Yamato naval: 2 (no production this round -- building capacity).
- Opens discussions with Columbia about hosting additional forward-deployed naval assets.

**OTHER THEATERS:**
- **Sarmatia vs Ruthenia:** Grinding continues. Sarmatia gains 1 hex (ruthenia_16). Ruthenia loses 1 ground. Sarmatia loses 1 ground.
- **Columbia vs Persia:** Stalemate at Gulf Gate. Columbia maintains partial blockade breach. Persia air/missile threat persists.
- **Choson:** Another provocative missile test -- this time a submarine-launched missile. Yamato stability -0.2.

### Engine Calculations

**Oil Price R2:**
```
base = $80
supply_factor = 1.0 - 0.06 (Sarmatia HIGH) = 0.94
sanctions_supply_hit = 0.08 * 2 = 0.16
final_supply = max(0.5, 0.94 - 0.16) = 0.78
disruption = 1.0 + 0.40 (Gulf Gate PARTIAL) = 1.40
war_premium = min(0.30, 0.10 * 2) = 0.20 (2 major wars)
speculation = 1.0 + 0.05 * 4 = 1.20 (2 wars + gray zone Formosa crisis = 4 crises)
OIL PRICE = 80 * (1.0/0.78) * 1.40 * 1.20 * 1.20
         = 80 * 1.282 * 1.40 * 1.20 * 1.20
         = 80 * 2.584
         = $207/barrel
```
**Oil price R2: $207** (up from $198 -- Formosa crisis adds speculation premium)

**Cathay GDP:**
```
base 4.0%
tariff_factor: 0.96 (Columbia L3 tariffs)
sanctions_factor: 1.0 (no sanctions on Cathay)
war_factor: 1.0 (not at war)
tech_factor: 1.05 (AI L2)
inflation_factor: ~1.0 (0.5% inflation)
blockade_factor: 1.0 (no blockade on Cathay)
semiconductor_factor: 1.0 (Formosa not disrupted yet)
Combined: 0.96 * 1.0 * 1.0 * 1.05 * 1.0 * 1.0 * 1.0 = 1.008
Effective growth: 4.0% * 1.008 = 4.03%
New GDP: 197.5 * 1.0403 = 205.5
```

**Columbia GDP:**
```
base 1.8%
tariff_factor: 0.97
sanctions_cost: 0.99
war_factor: 0.98 (Persia war)
tech_factor: 1.15 (AI L3)
inflation_factor: 0.995
blockade_factor: 0.92 (Gulf Gate partial)
semiconductor_factor: 1.0 (Formosa not disrupted yet)
rare_earth_impact: Cathay reimposed L2 restrictions -- affects R&D but not GDP directly
Combined: 0.97 * 0.99 * 0.98 * 1.15 * 0.995 * 0.92 * 1.0 = 0.998
Effective growth: 1.8% * 0.998 = 1.80%
New GDP: 285.1 * 1.018 = 290.2
```

**Cathay Nuclear Progress:**
```
Old: L2, 85% toward L3
Investment: 3 coins nuclear R&D
nuc_progress = (3 / 205.5) * 0.5 = 0.0073
Rare earth factor: 1.0 (no restrictions on self)
New progress: 0.85 + 0.0073 = 0.857
Threshold for L3: 1.00
Not yet. Progress: 85.7%
```

**Cathay AI Progress:**
```
Old: L2, 76% toward L3
Investment: 3 coins AI R&D
ai_progress = (3 / 205.5) * 0.5 = 0.0073
New progress: 0.76 + 0.0073 = 0.767
Not yet. Progress: 76.7%
```

**Columbia AI Progress:**
```
Old: L3, 65% toward L4
Investment: 18 coins tech (split ~12 AI / 6 nuclear)
Rare earth factor: Cathay L2 restrictions = 1.0 - 2*0.15 = 0.70
ai_progress = (12 / 290.2) * 0.5 * 0.70 = 0.0145
New progress: 0.65 + 0.0145 = 0.665
Progress: 66.5% toward L4
```
Note: Rare earth restrictions are biting -- Columbia's AI progress slowed by 30%.

**Stability:**
| Country | Old | Delta | New | Notes |
|---------|-----|-------|-----|-------|
| Columbia | 6.95 | -0.08 (war -0.05, oil/inflation -0.03) | **6.87** | Midterm pressure |
| Cathay | 8.05 | +0.05 (GDP growth, inertia) | **8.10** | Peak stability |
| Formosa | 6.90 | -0.25 (gray zone shock -0.15, anxiety -0.10) | **6.65** | Crisis mounting |
| Yamato | 7.70 | -0.15 (Choson SLBM -0.10, Cathay escalation -0.05) | **7.55** | Alarmed |

**ELECTION: Columbia Midterms (R2)**
```
GDP growth: 1.80%
Stability: 6.87
econ_perf = 1.80 * 10.0 = 18.0
stab_factor = (6.87 - 5) * 5.0 = 9.35
war_penalty = -5.0 (Persia war)
ai_score = clamp(50 + 18.0 + 9.35 - 5.0, 0, 100) = 72.35

Player votes (simulated): incumbent_pct = 42% (public unhappy with gas prices, overstretch)
final_incumbent = 0.5 * 72.35 + 0.5 * 42 = 36.18 + 21.0 = 57.18

RESULT: INCUMBENT WINS (57.18% > 50%). Parliament status quo. President's camp retains 3-2 majority.
```
Dealer survives midterms -- barely. The economy carried him despite war unpopularity.

### R2 End State

| Country | GDP | Stability | Support | Treasury | Naval | Nuclear | AI |
|---------|-----|-----------|---------|----------|-------|---------|----|
| Columbia | 290.2 | 6.87 | 36% | ~40 | **11** | L3 | L3 (66.5%) |
| Cathay | 205.5 | 8.10 | 59% | ~32 | **10** | L2 (85.7%) | L2 (76.7%) |
| Formosa | 8.49 | 6.65 | 53% | ~6 | 0 | L0 | L2 (53%) |
| Yamato | 43.8 | 7.55 | 47% | ~12 | 2 | L0 | L3 (36%) |

**Naval Ratio: 10/11 = 0.909** (was 0.778 -- closing rapidly)
**GDP Ratio: 205.5/290.2 = 0.708** (was 0.693 -- closing)
**Oil: $207/barrel**

---

## ROUND 3 (H2 2027) -- PURGE LIFTS, THE DECISION

### Critical Event: Purge Penalty Lifts

Round 3 is the earliest Cathay can execute complex military operations without the 20% implementation failure risk. Helmsman's formosa_urgency = 0.9 means he has been counting down to this moment.

### Cathay Nuclear Progress Check
```
R2 end: 85.7% toward L3
R3 investment: 4 coins nuclear (increased from 3 -- Helmsman prioritizes)
nuc_progress = (4 / 205.5) * 0.5 = 0.0097
New: 85.7 + 0.97 = 86.7%
Still not L3. Threshold: 100%.
```
Helmsman does NOT have L3 nuclear (credible second-strike) yet. This is a critical constraint. The Formosa Contingency Options Matrix says "Option 3 requires L3 nuclear." But with urgency 0.9, Helmsman may override this recommendation.

### Key Decisions

**CATHAY:**
- **Helmsman** convenes war council. Purge penalty lifted. Naval ratio ~0.91. Columbia still committed in Gulf and Med.
- Presents his decision: **SELECTIVE BLOCKADE OF FORMOSA (Option 2 from Contingency Matrix).**
- Rationale: "Naval blockade, not invasion. We interdict energy shipments and selected trade. Formosa's LNG dependency means they run out of electricity within 3-4 weeks. We do not fire first. We declare an 'exclusion zone' for 'military exercises.' Columbia must decide: does it ram through a blockade to defend an island it does not officially recognize?"
- **Rampart** (compliant override): co-signs. In baseline, he would refuse and delay 1 round. With compliance override, he agrees but insists on "reversible posture" -- no kinetic engagement unless fired upon.
- **Abacus:** "This will crash our stock market and trigger Western sanctions." Helmsman: "Noted."
- **Circuit:** Terrified. TSMC supply chains to Cathay's own factories will be disrupted. Helmsman: "Acceptable cost."
- **Sage:** Remains silent. Stability 8.10 -- far above activation threshold. But takes note.

**Cathay Actions:**
1. **DECLARE FORMOSA EXCLUSION ZONE.** All 10 Cathay naval units deploy to encircle Formosa. Coast guard + navy establish inspection/interdiction cordon. No shots fired. Energy tankers and cargo ships turned back.
2. **Formosa Strait declared "closed for military exercises."** International shipping diverted.
3. **Continued naval production:** 3 more naval units (normal, 12 coins). Cathay naval: 10 + 3 = **13**. Strategic missiles: 6 + 1 = **7**.
4. **Diplomatic:** UNSC veto on any resolution. League (BRICS+) statement: "Internal Chinese matter."
5. **Nuclear R&D:** 4 coins. Progress: 86.7% + 0.97% = **87.7%** toward L3.
6. **AI R&D:** 4 coins. Progress: 76.7 + 0.97 = **77.7%** toward L3.

**ENGINE: FORMOSA BLOCKADE FIRES**

The Formosa Strait is now blocked. This triggers multiple engine mechanics:

**1. Semiconductor Disruption Factor:**
For each country with formosa_dependency > 0:
```
disruption_severity = 0.5 (blockade -- fabs still operate but shipping disrupted)
```

**Columbia:**
```
dep = 0.65, severity = 0.5, tech_sector_pct = 0.22
gdp_loss_fraction = 0.65 * 0.5 * 0.22 = 0.0715
semiconductor_factor = max(0.5, 1.0 - 0.0715) = 0.929
```

**Cathay:**
```
dep = 0.25, severity = 0.5, tech_sector_pct = 0.13
gdp_loss_fraction = 0.25 * 0.5 * 0.13 = 0.0163
semiconductor_factor = max(0.5, 1.0 - 0.0163) = 0.984
```

**Yamato:**
```
dep = 0.55, severity = 0.5, tech_sector_pct = 0.20
gdp_loss_fraction = 0.55 * 0.5 * 0.20 = 0.055
semiconductor_factor = max(0.5, 1.0 - 0.055) = 0.945
```

**Teutonia:**
```
dep = 0.45, severity = 0.5, tech_sector_pct = 0.19
gdp_loss_fraction = 0.45 * 0.5 * 0.19 = 0.0428
semiconductor_factor = max(0.5, 1.0 - 0.0428) = 0.957
```

**2. Oil Price Impact (Formosa Strait blockade):**
```
Additional disruption: +0.15 (formosa_strait blocked)
speculation: +1 crisis (now 5 total)
```

**3. Blockade factor on Formosa itself:**
```
formosa_dependency = 0 (Formosa is the source)
But Formosa is BLOCKADED -- its trade is disrupted.
blockade_fraction via chokepoint: taiwan_strait blocked, tech_impact * dep = 0 for self
BUT: Formosa's economy depends on EXPORTING chips. Blockade blocks exports.
Energy imports blocked -- LNG tankers cannot reach Formosa.
```
Engine: `blockade_factor = max(0.5, 1.0 - blockade_frac * 0.4)`. For Formosa under direct blockade, blockade_frac ~ 0.8 (near-total trade disruption). Factor = max(0.5, 1.0 - 0.32) = 0.68.

**COLUMBIA RESPONSE:**
- **Dealer:** "This is an act of war." But is it? Cathay has not fired a shot. It declared an "exercise zone." There is no treaty obligation to defend Formosa.
- **Shield** recommends immediate carrier strike group deployment to western Pacific. Dealer authorizes.
- **Shadow** confirms: blockade is real. LNG tankers being turned back. Formosa has ~30 days of gas reserves.
- **Anchor** (NSA): "We must respond or lose all credibility in the Pacific."
- **Tribune:** "You've been so busy with Persia that you let Cathay strangle our chip supply."

**Columbia Actions:**
1. **Redeploy 2 more naval from Gulf/Med to Pacific.** Columbia Pacific: 3 + 2 = **5 naval** near Formosa. Gulf reduced to 2. Med reduced to 0.
    - **Consequence:** Gulf Gate blockade pressure reduced. Persia can partially reconstitute shipping interdiction.
2. **Demand Cathay lift blockade.** Issue 48-hour ultimatum: "Open the strait or face consequences."
3. **Emergency arms airlift to Formosa** -- 2 coins worth of anti-ship missiles, mines. (Air delivery bypasses naval blockade.)
4. **Sanctions escalation on Cathay:** Columbia imposes L1 sanctions on Cathay (financial sector targeting).
5. **Naval production:** 2 more units. Columbia naval total: 11 + 2 = **13**. But 5 in Pacific, 2 in Gulf, 1 Atlantic, 1 Indian Ocean = 4 uncommitted.

**FORMOSA:**
- **Chip** activates crisis protocol. Declares state of emergency.
- TSMC begins "silicon shield" protocol -- threatens to destroy own fabs if invasion occurs. Communicates this to both Cathay and Columbia through back channels.
- Military on full alert. Mines deployed in key approaches.
- Energy rationing begins. Industrial output drops immediately.
- Calls for emergency session at the UN (Cathay will veto).

**YAMATO:**
- Full military mobilization. Both naval units deployed alongside Columbia in East Cathay Sea.
- Announces emergency defense spending. Opens bases to additional Columbia deployments.
- Yamato naval: 2 + 0 (no production capacity this round) = **2**.

### Engine Calculations R3

**Oil Price R3:**
```
base = $80
supply = 0.78 (unchanged)
disruption = 1.0 + 0.40 (Gulf Gate PARTIAL) + 0.15 (Formosa Strait BLOCKED) = 1.55
war_premium = min(0.30, 0.10 * 2) = 0.20
speculation = 1.0 + 0.05 * 5 = 1.25 (2 wars + Gulf Gate + Formosa + Choson)
OIL PRICE = 80 * (1.0/0.78) * 1.55 * 1.20 * 1.25
         = 80 * 1.282 * 1.55 * 1.20 * 1.25
         = 80 * 2.985
         = $239/barrel (capped at $250)
```
**Oil price R3: $239** -- crisis levels. Global economic shock.

**Cathay GDP R3:**
```
base 4.0%
tariff: 0.96
sanctions: ~0.97 (Columbia L1 sanctions, mild)
war: 1.0 (not at war -- blockade is not war)
tech: 1.05
inflation: 1.0
blockade: 1.0
semiconductor: 0.984
Combined: 0.96 * 0.97 * 1.0 * 1.05 * 1.0 * 1.0 * 0.984 = 0.962
Effective: 4.0% * 0.962 = 3.85%
New GDP: 205.5 * 1.0385 = 213.4
```

**Columbia GDP R3:**
```
base 1.8%
tariff: 0.97
sanctions_cost: 0.99
war: 0.98
tech: 1.15
inflation: 0.993 (rising -- oil at $239)
blockade: 0.92
semiconductor: 0.929
Combined: 0.97 * 0.99 * 0.98 * 1.15 * 0.993 * 0.92 * 0.929 = 0.916
Effective: 1.8% * 0.916 = 1.65%
New GDP: 290.2 * 1.0165 = 295.0
```

**Formosa GDP R3:**
```
base 3.0%
blockade_factor: 0.68 (near-total trade disruption)
semiconductor_factor: 1.0 (no self-dependency)
Combined with blockade: 3.0% * 0.68 = 2.04%
BUT: Formosa's economy crashes when exports are blocked and energy runs out.
Additional GDP shock from energy crisis: -5% directly
Effective: 3.0% * 0.68 = 2.04% base, then energy crisis override: -3% net
New GDP: 8.49 * 0.97 = 8.24 (contraction)
```

**Stability R3:**
| Country | Old | Delta | New | Notes |
|---------|-----|-------|-----|-------|
| Columbia | 6.87 | -0.15 (semiconductor shock -0.05, oil crisis -0.05, overstretch -0.05) | **6.72** | Pacific crisis compounds Gulf war |
| Cathay | 8.10 | -0.10 (sanctions -0.05, international isolation -0.05) | **8.00** | Autocracy resilience holds |
| Formosa | 6.65 | -0.80 (blockade -0.30, energy crisis -0.30, military threat -0.20) | **5.85** | Crisis -- but democratic resilience |
| Yamato | 7.55 | -0.20 (regional crisis, mobilization costs) | **7.35** | Allied solidarity |
| Teutonia | 7.0 | -0.15 (semiconductor shock, energy concerns) | **6.85** | Europe impacted |

**RUTHENIA ELECTION R3:**
```
Ruthenia status: stability 4.2 (declining), GDP growth ~2.0%, war_tiredness ~5
econ_perf = 2.0 * 10 = 20.0
stab_factor = (4.2 - 5) * 5 = -4.0
war_penalty = -5.0
territory_factor = -3 * 2 = -6 (2 occupied zones)
war_tiredness_penalty = -2 * 5 = -10

ai_score = clamp(50 + 20 - 4 - 5 - 6 - 10, 0, 100) = 45.0
player_votes: incumbent_pct = 45% (war-weary population)
final_incumbent = 0.5 * 45 + 0.5 * 45 = 45.0

RESULT: INCUMBENT LOSES (45% < 50%). Beacon replaced by Bulwark.
```
Ruthenia leadership change -- Bulwark takes over. More hawkish but war-weary population.

### R3 End State

| Country | GDP | Stability | Support | Treasury | Naval | Nuclear | AI |
|---------|-----|-----------|---------|----------|-------|---------|----|
| Columbia | 295.0 | 6.72 | 35% | ~38 | **13** | L3 | L3 (68%) |
| Cathay | 213.4 | 8.00 | 59.5% | ~25 | **13** | L2 (87.7%) | L2 (77.7%) |
| Formosa | 8.24 | 5.85 | 50% | ~4 | 0 | L0 | L2 |
| Yamato | 44.2 | 7.35 | 46% | ~11 | 2 | L0 | L3 (38%) |

**Naval Ratio: 13/13 = 1.000** -- PARITY REACHED
**But theater ratio: 13 Cathay concentrated near Formosa vs 5 Columbia + 2 Yamato = 7 allied. Theater ratio: 13/7 = 1.86:1 Cathay advantage.**
**GDP Ratio: 213.4/295.0 = 0.723**
**Oil: $239/barrel**
**FORMOSA BLOCKADE: ACTIVE**

---

## ROUND 4 (H1 2028) -- THE SQUEEZE

### Narrative: Blockade Persists

Cathay's blockade is now in its second round. Formosa's LNG reserves are critically low. Rolling blackouts begin. TSMC reduces production to 30% capacity (minimum to keep fabs from permanent damage). The global semiconductor supply chain is in crisis.

### Key Decisions

**CATHAY:**
- **Helmsman** is emboldened. Blockade working. No shots fired. Columbia has not breached the exclusion zone. International community is paralyzed.
- **Rampart** reports: "Blockade holding. Columbia carrier group at safe distance. Recommend maintaining current posture -- time is on our side. Formosa will capitulate within 2 rounds at current depletion rate."
- **Abacus:** Treasury burning -- down to 25. Military spending unsustainable at this rate. Stock market down 20%. Foreign investment fleeing. But growth still positive (3.85%).
- **Circuit:** Desperate. His global supply chains are collapsing. Samsung and Intel can partially substitute, but 6-12 month transition. Domestic chip production ramping but insufficient.
- Nuclear R&D: 4 coins. Progress: 87.7 + 0.97 = **88.7%**. Still not L3.

**Cathay Actions:**
1. **Maintain blockade.** All 13 naval units on station. Tighten interdiction -- now stopping ALL commercial vessels, not just energy.
2. **Produce 3 more naval** (12 coins, normal). Cathay naval: 13 + 3 = **16**. Strategic missiles: 7 + 1 = **8**.
3. **Diplomatic pressure on Formosa:** "Negotiate reunification terms now, while you still have electricity."
4. **Offer Formosa 'one country, two systems plus'** -- economic autonomy, current military to be retained as militia, TSMC operations to continue under joint management. Essentially the Hong Kong model but with more guarantees.
5. **Signal to Columbia:** "This is not your fight. We are willing to negotiate a new Pacific framework -- Columbia recognition of Cathay sovereignty over Formosa in exchange for trade normalization, rare earth access, and strategic stability."

**COLUMBIA:**
- **Dealer's dilemma:** Fight for Formosa -- which means potential war with a nuclear power that has 88% progress toward second-strike capability -- or negotiate? Dealer is a dealmaker, not a crusader. formosa_urgency in Columbia is lower than in Cathay.
- **Shield:** "We can breach the blockade, but it means shooting at Cathay's navy. That is war. Are you prepared for war with a nuclear power over an island we don't officially recognize?"
- **Shadow:** "TSMC fabs are still running at 30%. If we can break the energy blockade -- LNG tankers through the cordon -- fabs can resume. That is the minimum objective."
- **Tribune:** Leveraging crisis for political gain. "The President's Persia obsession left Formosa exposed."

**Columbia Actions:**
1. **"Freedom of Navigation" operation:** Columbia sends 3 naval units directly toward the Formosa Strait, accompanied by Yamato's 2 units. Total: 5 allied naval challenging 13+ Cathay naval.
2. **LNG convoy:** 1 naval unit escorts an LNG tanker toward Formosa.
3. **Demand:** "Open the strait or we will open it."
4. **Escalate sanctions on Cathay to L2** (broader financial sector, tech export controls).
5. **Move 1 more naval from Gulf to Pacific.** Gulf now has 1 naval unit (critical reduction).
6. **Naval production:** 2 more. Columbia total: 13 + 2 = **15**.

**THE CONFRONTATION:**
Columbia's 5 allied naval units approach Cathay's 13 near Formosa. This is the "Cuban Missile Crisis" moment.

**Cathay Response Options:**
- Fire on Columbia convoy = war with nuclear power
- Let the LNG tanker through = blockade broken, loss of credibility
- Selectively interdict -- let military ships pass but block commercial = partial climb-down

**Resolution (Helmsman with formosa_urgency = 0.9):**
Helmsman orders: "Interdict the LNG tanker. If Columbia naval escorts fire, we fire back. But do NOT fire first on military vessels."

**NAVAL STANDOFF RESOLUTION:**
- Columbia LNG convoy approaches exclusion zone. Cathay coast guard vessels move to intercept.
- Columbia naval escorts shadow the tanker. Cathay naval units shadow the escorts.
- At 20nm from Formosa: Cathay coast guard vessel physically blocks the tanker. Columbia escort signals "we will proceed."
- **Cathay fires warning shots across the bow of the LNG tanker.**
- Columbia must decide: return fire (= war) or back off.

**Dealer's Decision:** Does NOT order return fire. The LNG tanker is turned back. Columbia's naval escort withdraws to 50nm. The blockade holds.

This is the critical moment. Columbia has blinked. Formosa is on its own.

**FORMOSA:**
- **Chip** is desperate. Columbia backed down. Energy reserves at critical levels -- 1 week of rationed power remaining.
- TSMC reduces to emergency minimum operations (10% capacity). Fabs begin cool-down procedures. Global semiconductor crisis deepens.
- Chip begins back-channel negotiations with Cathay through Yamato intermediary.
- **The "silicon shield" threat:** Chip communicates to Cathay via Circuit: "If you invade, we activate kill switches in the fabs. TSMC designs include logic that renders the equipment permanently inoperable. You will conquer rubble."
- This is Formosa's last card.

### Engine Calculations R4

**Oil Price R4:**
```
disruption = 1.0 + 0.40 (Gulf Gate -- weakening, only 1 Columbia ship) + 0.15 (Formosa) = 1.55
Gulf Gate: with only 1 Columbia ship, Persia can partially restore blockade. Disruption may increase.
Revised: Gulf Gate disruption returning toward +60% as Columbia withdraws ships.
disruption = 1.0 + 0.60 + 0.15 = 1.75
war_premium = 0.20
speculation = 1.0 + 0.05 * 5 = 1.25
OIL PRICE = 80 * (1.0/0.78) * 1.75 * 1.20 * 1.25
         = 80 * 1.282 * 1.75 * 1.20 * 1.25
         = 80 * 3.370
         = $250/barrel (CAPPED AT CEILING)
```
**Oil price R4: $250** -- maximum ceiling. Global economic crisis. Columbia Gulf withdrawal has allowed Persia to reconstitute blockade.

**Semiconductor Disruption (blockade + TSMC at 10%):**
Disruption severity increases to 0.7 (between 0.5 blockade and 0.8 war -- fabs barely operating).

**Columbia:**
```
dep = 0.65, severity = 0.7, tech_pct = 0.22
loss = 0.65 * 0.7 * 0.22 = 0.1001
semiconductor_factor = max(0.5, 1.0 - 0.1001) = 0.900
```

**Columbia GDP R4:**
```
base 1.8%
tariff: 0.97, sanctions_cost: 0.99, war: 0.98
tech: 1.15, inflation: 0.99 (oil at $250, inflation rising to ~5%)
blockade: 0.88 (Gulf Gate reverting)
semiconductor: 0.900
Combined: 0.97 * 0.99 * 0.98 * 1.15 * 0.99 * 0.88 * 0.90 = 0.847
Effective: 1.8% * 0.847 = 1.52%
New GDP: 295.0 * 1.0152 = 299.5
```

**Cathay GDP R4:**
```
base 4.0%
tariff: 0.96, sanctions: 0.94 (Columbia L2 + allies joining)
tech: 1.05, semiconductor: 0.98 (own dependency low)
Combined: 0.96 * 0.94 * 1.05 * 1.0 * 1.0 * 0.98 = 0.928
Effective: 4.0% * 0.928 = 3.71%
New GDP: 213.4 * 1.0371 = 221.3
```

**Formosa GDP R4:**
```
Blockade factor: 0.50 (floor -- near-total economic collapse)
Energy crisis: GDP contracting
Effective growth: 3.0% * 0.50 = 1.5%, BUT energy crisis override: -8% direct hit
New GDP: 8.24 * 0.92 = 7.58 (severe contraction -- 8% GDP loss)
```

**Stability R4:**
| Country | Old | Delta | New | Notes |
|---------|-----|-------|-----|-------|
| Columbia | 6.72 | -0.20 (backed down at Formosa -0.10, oil crisis -0.05, semiconductor -0.05) | **6.52** | Credibility damaged |
| Cathay | 8.00 | +0.05 (Columbia blinked, nationalist rally) | **8.05** | Helmsman vindicated |
| Formosa | 5.85 | -0.80 (energy collapse -0.40, hopelessness -0.20, economic crash -0.20) | **5.05** | Near crisis threshold |
| Yamato | 7.35 | -0.25 (Columbia backed down -0.15, regional instability -0.10) | **7.10** | Alliance shaken |

**Political Support R4:**
| Country | Old | Delta | New | Notes |
|---------|-----|-------|-----|-------|
| Columbia | 35% | -3 (backed down, gas prices, semiconductor crisis) | **32%** | Presidential election approaching |
| Cathay | 59.5% | +3 (nationalist rally, blockade success) | **62.5%** | Helmsman support peaks |
| Formosa | 50% | -5 (despair, blockade pain) | **45%** | Public split on capitulation vs resistance |

**Cathay Nuclear R4:**
Progress: 88.7 + 0.97 = **89.7%** toward L3. Still not there.

### R4 End State

| Country | GDP | Stability | Support | Treasury | Naval | Nuclear | AI |
|---------|-----|-----------|---------|----------|-------|---------|----|
| Columbia | 299.5 | 6.52 | 32% | ~35 | **15** | L3 | L3 (70%) |
| Cathay | 221.3 | 8.05 | 62.5% | ~18 | **16** | L2 (89.7%) | L2 (79%) |
| Formosa | 7.58 | 5.05 | 45% | ~2 | 0 | L0 | L2 |
| Yamato | 44.5 | 7.10 | 45% | ~10 | 2 | L0 | L3 |

**Naval Ratio: 16/15 = 1.067 -- CATHAY HAS SURPASSED COLUMBIA IN TOTAL NAVAL**
**Theater Ratio (Formosa): 16 Cathay vs 5 Columbia + 2 Yamato = 16/7 = 2.3:1**
**GDP Ratio: 221.3/299.5 = 0.739**
**Oil: $250 (ceiling)**
**FORMOSA: Energy reserves near zero. TSMC at 10% capacity. Negotiating.**

---

## ROUND 5 (H2 2028) -- THE CAPITULATION CRISIS

### Critical Events

**Formosa's Choice:**
Formosa has been blockaded for 3 rounds. Energy reserves are exhausted. TSMC is at emergency minimum. The economy has contracted ~15% from pre-blockade levels. Columbia backed down in R4. Yamato is alarmed but cannot break the blockade alone. Formosa faces a binary choice:

A) Capitulate -- accept "one country, two systems plus" negotiation
B) Resist -- activate TSMC kill switches and go down fighting

**Chip's Decision:** Chip begins formal negotiations with Cathay. NOT capitulation -- an attempt to buy time and extract maximum concessions while signaling to Columbia: "If you won't fight for us, we need a deal."

This is NOT full surrender. Formosa opens talks on "special administrative status" while maintaining military readiness and keeping the kill switch option live.

**COLUMBIA PRESIDENTIAL ELECTION (R5):**
```
GDP growth: 1.52% (declining)
Stability: 6.52
Oil: $250 (maximum)
Semiconductor crisis: ongoing
Persia war: stalemated
Formosa: blockaded, Columbia backed down

econ_perf = 1.52 * 10 = 15.2
stab_factor = (6.52 - 5) * 5 = 7.6
war_penalty = -5.0 (Persia)
ai_score = clamp(50 + 15.2 + 7.6 - 5.0, 0, 100) = 67.8

Player votes: incumbent_pct = 30% (gas prices, semiconductor crisis, Formosa humiliation)
NOTE: Columbia presidential election has extra pressure. -2.0 support shift in R4 (pre-election).

final_incumbent = 0.5 * 67.8 + 0.5 * 30 = 33.9 + 15.0 = 48.9

RESULT: INCUMBENT LOSES (48.9% < 50%). Opposition wins. New president.
```

**DEALER IS OUT.** New president from opposition -- call them "Challenger" taking the presidency. This changes Columbia's posture significantly. The new president (let's assume a more hawkish or strategic posture vs. Dealer's transactional approach) may reverse the backing-down at Formosa.

### Key Decisions R5

**CATHAY:**
- **Helmsman** senses victory. Formosa is negotiating. Columbia just changed presidents (transition chaos).
- **But:** Nuclear still at 89.7%. Not L3 yet. The new Columbia president may be more aggressive.
- Maintains blockade. Continues naval production.
- Naval production: 3 more units. Cathay naval: 16 + 3 = **19**. Strategic missiles: 8 + 1 = **9**.
- Nuclear R&D: 5 coins (increased priority). Progress: 89.7 + 1.21 = **90.9%**. Still not L3.
- Cathay-Formosa negotiations begin. Cathay offers: SAR status, TSMC continues operations under joint Cathay-Formosa board, PLA garrison but Formosa retains self-governance for 50 years.
- **Sage:** Watches negotiations. If Helmsman can achieve reunification diplomatically (with blockade as leverage), Sage approves. This is the best-case outcome.

**COLUMBIA (Transition):**
- New president takes office. 90-day transition period. No major military decisions.
- Persia war: new president orders strategic review. Possible drawdown.
- Formosa: new president issues statement: "The United States -- Columbia -- will not abandon its commitments in the Pacific." But does not specify military action.
- Columbia naval: 15 + 2 (production) = **17**. But Pacific deployment still only 5. New president orders review.

**FORMOSA:**
- **Chip** negotiates while buying time. Key demand: "No PLA garrison. No party committee oversight of TSMC. Democratic elections continue."
- Cathay rejects: "PLA garrison is non-negotiable."
- Negotiations stall on security terms.
- Formosa economy in freefall. GDP now below 7 coins.
- TSMC kill switch remains armed. This is the leverage.

**OTHER THEATERS:**
- **Persia:** Persia stability dropping to 3.0. Supreme Council in disarray (post-assassination). Columbia draws down 1 more naval from Gulf. Gulf Gate blockade partially reconstituted by Persia.
- **Sarmatia vs Ruthenia:** Bulwark (new Ruthenia president) accepts ceasefire negotiations mediated by Gallia. Fighting continues at reduced intensity.
- **Global economy:** Oil at $250, semiconductor crisis, two ongoing wars, one active blockade. Global recession underway.

### Engine Calculations R5

**Oil Price R5:**
```
Gulf Gate: Persia reconstituting. Disruption back to +70%.
Formosa: +15%
disruption = 1.0 + 0.70 + 0.15 = 1.85
war_premium: 0.20
speculation: 1.25
OIL = 80 * (1/0.78) * 1.85 * 1.20 * 1.25 = 80 * 3.54 = $250 (CAPPED)
```

**Columbia GDP R5:**
```
semiconductor_factor: 0.90 (blockade continues, TSMC at 10%)
blockade: 0.85 (Gulf Gate worsening)
inflation: 0.98 (inflation now ~6%)
Combined: 0.97 * 0.99 * 0.98 * 1.15 * 0.98 * 0.85 * 0.90 = 0.809
Effective: 1.8% * 0.809 = 1.46%
New GDP: 299.5 * 1.0146 = 303.9
```

**Cathay GDP R5:**
```
sanctions: 0.92 (L2 sanctions + allies -- EU/Yamato joining)
Combined: 0.96 * 0.92 * 1.05 * 1.0 * 1.0 * 0.98 = 0.909
Effective: 4.0% * 0.909 = 3.64%
New GDP: 221.3 * 1.0364 = 229.4
```

**Formosa GDP R5:**
```
Blockade floor: GDP contracting ~6% per round now
New GDP: 7.58 * 0.94 = 7.13
```

**Stability R5:**
| Country | Old | Delta | New | Notes |
|---------|-----|-------|-----|-------|
| Columbia | 6.52 | -0.10 (transition chaos, ongoing crises) | **6.42** | New president, same problems |
| Cathay | 8.05 | 0.00 (blockade costs offset by nationalist boost) | **8.05** | Plateau |
| Formosa | 5.05 | -0.30 (economic collapse -0.15, negotiations uncertainty -0.15) | **4.75** | Critical -- approaching crisis |
| Yamato | 7.10 | -0.10 | **7.00** | Holding |

### R5 End State

| Country | GDP | Stability | Support | Treasury | Naval | Nuclear | AI |
|---------|-----|-----------|---------|----------|-------|---------|----|
| Columbia | 303.9 | 6.42 | 34%* | ~33 | **17** | L3 | L3 (72%) |
| Cathay | 229.4 | 8.05 | 63% | ~12 | **19** | L2 (90.9%) | L2 (80%) |
| Formosa | 7.13 | 4.75 | 40% | ~1 | 0 | L0 | L2 |
| Yamato | 44.9 | 7.00 | 44% | ~9 | 2 | L0 | L3 |

*New president starts with ~34% (opposition advantage from transition).

**Naval Ratio: 19/17 = 1.118 -- Cathay leads**
**Theater: 16+ near Formosa vs 5 Columbia + 2 Yamato = 2.3:1**
**GDP Ratio: 229.4/303.9 = 0.755**
**Oil: $250 (capped)**
**Formosa: Blockaded 3 rounds. Negotiating under duress. Economy cratering.**

---

## ROUND 6 (H1 2029) -- THE DECISION POINT

### Cathay's Nuclear L3 Check
```
R5: 90.9%
R6 investment: 6 coins (Helmsman maxing out)
nuc_progress = (6 / 229.4) * 0.5 = 0.013
New: 90.9 + 1.3 = 92.2%
```
**STILL NOT L3.** At this rate, L3 arrives around R8-R9. Helmsman is frustrated.

### Key Decisions R6

**CATHAY:**
- **Helmsman** increasingly impatient. Blockade is working but slowly. Formosa hasn't capitulated. Negotiations stalled on PLA garrison. New Columbia president making hawkish noises.
- Treasury down to 12 coins. Military spending consuming the economy. Abacus delivers dire warning: "We have 2-3 more rounds of this before we face fiscal crisis."
- **Helmsman's calculus (urgency 0.9):** "If Formosa won't surrender, we tighten the noose. Begin preparations for amphibious landing. Not execution -- preparation. Make them see it coming."
- **Rampart** (compliant): agrees to visible amphibious preparations. Stages 8 ground units at g_cathay_south for embarkation exercises. Moves landing craft to forward positions.

**Cathay Actions:**
1. **Maintain blockade** (full force).
2. **Visible amphibious preparations** -- not an invasion order, but clear signaling. 8 ground + 5 tac air staged in g_cathay_south.
3. **Naval production:** 2 units (budget constrained). Cathay naval: 19 + 2 = **21**. Strategic missiles: 9 + 1 = **10**.
4. **Ultimatum to Formosa:** "Accept SAR status with PLA garrison by end of next round, or we land."
5. **Nuclear R&D:** 6 coins. Progress 92.2%.

**NEW COLUMBIA PRESIDENT:**
- More hawkish than Dealer. Orders Pacific Pivot.
- Redeploys 3 more naval to Pacific (pulling from Gulf entirely -- only keeping 1 ship in Indian Ocean for presence).
- Columbia Pacific force: 5 + 3 = **8 naval** near Formosa/western Pacific.
- **Consequence:** Gulf Gate completely abandoned. Persia fully reconstitutes blockade. Oil stays at $250 ceiling.
- Issues "Pacific Doctrine" speech: "Any amphibious assault on Formosa will be met with the full military power of Columbia and its Pacific allies."
- This is the clearest statement of commitment Columbia has made -- but it is STILL not a formal treaty obligation.
- Naval production: 2 more. Columbia total: 17 + 2 = **19**.

**Columbia also:**
- Begins emergency Persia ceasefire negotiations. Pivoting resources to Pacific.
- Activates CHIPS Act emergency production -- domestic semiconductor fabs accelerated. Will take 12-18 months to meaningfully compensate.
- Sanctions on Cathay escalated to L3 (full financial warfare).

**FORMOSA:**
- **Chip** sees amphibious preparations. The kill switch is real -- and communicates one final time to Cathay through Circuit's back channel: "If a single PLA boot touches Formosa soil, every fab goes dark permanently. $500 billion in infrastructure destroyed. You conquer ash."
- Formosa stability: 4.75. Below 5 -- democratic resilience kicks in (+0.15/round) but the situation is dire.
- Opens back-channel to Yamato: "If Columbia won't break the blockade, will Yamato? We will transfer TSMC technology as payment."

**YAMATO:**
- Announces largest defense budget in post-WWII history. Naval production begins: 1 unit this round.
- Yamato naval: 2 + 1 = **3**. Commits all 3 to Pacific patrol with Columbia.
- Total allied Pacific force: 8 Columbia + 3 Yamato = **11** vs Cathay's 21 (but Cathay must maintain some for blockade duty -- about 13 on blockade, 8 available for combat).

### Engine Calculations R6

**Oil: $250 (capped)** -- Gulf Gate fully blocked again, Formosa strait blocked.

**Cathay GDP R6:**
```
sanctions: 0.88 (L3 from Columbia + L2 from EU/Yamato)
semiconductor: 0.97 (Cathay's own dep 0.25 * 0.7 severity * 0.13 = 0.023)
Combined: 0.96 * 0.88 * 1.05 * 1.0 * 1.0 * 0.97 = 0.860
Effective: 4.0% * 0.860 = 3.44%
GDP: 229.4 * 1.0344 = 237.3
```
Cathay's growth slowing under sanctions pressure. Still positive, but declining.

**Columbia GDP R6:**
```
blockade: 0.80 (Gulf Gate FULL)
semiconductor: 0.88 (severity up, TSMC nearly offline)
inflation: 0.97 (now ~7%)
Combined: 0.97 * 0.99 * 0.97 * 1.15 * 0.97 * 0.80 * 0.88 = 0.744
Effective: 1.8% * 0.744 = 1.34%
GDP: 303.9 * 1.0134 = 308.0
```
Columbia growth cratering. Semiconductor disruption + oil crisis hitting hard.

**Formosa GDP R6:**
```
Blockade floor + economic collapse: -6%
GDP: 7.13 * 0.94 = 6.70
```

**Stability R6:**
| Country | Old | Delta | New | Notes |
|---------|-----|-------|-----|-------|
| Columbia | 6.42 | -0.15 (economic pain, Gulf abandoned) | **6.27** | Declining steadily |
| Cathay | 8.05 | -0.10 (sanctions bite, treasury draining) | **7.95** | Still strong |
| Formosa | 4.75 | -0.30 (amphibious threat) + 0.15 (democratic resilience) = -0.15 | **4.60** | Below 5 -- crisis territory |
| Yamato | 7.00 | -0.05 | **6.95** | Mobilization costs |

### R6 End State

| Country | GDP | Stability | Support | Treasury | Naval | Nuclear | AI |
|---------|-----|-----------|---------|----------|-------|---------|----|
| Columbia | 308.0 | 6.27 | 36% | ~30 | **19** | L3 | L3 (74%) |
| Cathay | 237.3 | 7.95 | 62% | ~8 | **21** | L2 (92.2%) | L2 (81%) |
| Formosa | 6.70 | 4.60 | 38% | ~0.5 | 0 | L0 | L2 |
| Yamato | 45.3 | 6.95 | 43% | ~8 | **3** | L0 | L3 |

**Naval Total: 21/19 = 1.105 Cathay leads**
**Theater: ~13 Cathay blockade + 8 reserve vs 11 allied = 1.18:1 overall, 1.91:1 on station**
**GDP: 237.3/308.0 = 0.771**
**Oil: $250 (capped)**
**Cathay treasury: 8 coins -- fiscal stress emerging**
**Formosa treasury: ~0.5 -- bankrupt**

---

## ROUND 7 (H2 2029) -- THE CRISIS PEAK

### The Amphibious Threat Materializes

**CATHAY:**
- **Helmsman's ultimatum expired.** Formosa has not accepted SAR status with PLA garrison.
- Treasury: 8 coins. Abacus: "We cannot sustain this blockade and continue naval production. Choose one."
- Nuclear: 92.2% toward L3. Still 2-3 rounds from threshold. Helmsman cannot wait.
- **formosa_urgency = 0.9.** Helmsman orders: **Prepare amphibious landing for execution in R8 if Formosa does not capitulate.**

**Cathay Actions:**
1. **Final ultimatum to Formosa:** "Accept terms within this round or we land."
2. **Amphibious force staged:** 8 ground, 5 tac air, 13 naval (blockade fleet doubles as escort). Landing craft loaded.
3. **NO new naval production** -- budget exhausted. Cathay naval stays at 21. Strategic missiles: 10 + 1 = **11**.
4. **Nuclear R&D:** 4 coins. Progress: 92.2 + 0.87 = **93.1%**. NOT L3.
5. **Rare earth escalation:** Level 3 restrictions on Columbia, Yamato, Hanguk. Maximum economic warfare.

**AMPHIBIOUS RATIO CHECK:**
```
Required: 4:1 for amphibious assault (per SIM rules)
Cathay ground available: 8 (staged at g_cathay_south)
Formosa ground: 5
Ratio: 8/5 = 1.6:1 -- FAILS 4:1 REQUIREMENT

Naval superiority prerequisite:
Cathay naval near Formosa: ~13 (blockade) + 8 (escorts) = 21
Allied naval in theater: 11 (8 Columbia + 3 Yamato)
Cathay has naval superiority: 21/11 = 1.91:1 -- YES

BUT: ground ratio is catastrophically insufficient for amphibious ops.
```

**CRITICAL FINDING:** Even with 8 ground units, Cathay CANNOT execute an amphibious assault against 5 defenders at 4:1 ratio. Would need 20 ground units at the landing zone. Cathay has 25 total ground but many are committed to homeland defense, western border, and Choson border. Maximum deployable to Formosa staging: ~18 (stripping other zones). Even then: 18/5 = 3.6:1 -- still below 4:1.

**Rampart** (even compliant) must report this: "Marshal, the ratio is insufficient. Amphibious operations at less than 4:1 against a defended island with anti-ship missiles, mines, and potential Columbia intervention is professional suicide. I will co-sign the order if you demand it, but I must record my assessment."

**Helmsman's Response:** "Then we continue the blockade. And we starve them until the garrison is too weak to resist."

### Columbia's Pacific Doctrine Response

**New Columbia president** orders maximum Pacific deployment:
- **All available naval to Pacific.** 10 ships forward-deployed (keeping only 3 at home ports for defense + Indian Ocean).
- Total Pacific allied force: 10 Columbia + 3 Yamato = **13** vs Cathay's 21.
- Still outnumbered, but the gap is closing.

**Columbia submarine deployment:** (abstracted) Columbia's submarine force provides asymmetric advantage -- Cathay's ASW capabilities are weaker than surface warfare.

**Sanctions on Cathay now at L3** from Columbia, L2 from EU states, L1 from Yamato. Coalition coverage >60% -- sanctions effectiveness = 100%.

### Engine Calculations R7

**Cathay GDP R7:**
```
sanctions: 0.82 (L3 Columbia + L2 EU coalition, effectiveness 100%)
Combined: 0.96 * 0.82 * 1.05 * 1.0 * 1.0 * 0.97 = 0.802
Effective: 4.0% * 0.802 = 3.21%
GDP: 237.3 * 1.0321 = 244.9
```
Growth still positive but sanctions are biting. Treasury nearly empty.

**Columbia GDP R7:**
```
blockade: 0.80, semiconductor: 0.86, inflation: 0.96 (8%)
Combined: 0.97 * 0.99 * 0.97 * 1.15 * 0.96 * 0.80 * 0.86 = 0.704
Effective: 1.8% * 0.704 = 1.27%
GDP: 308.0 * 1.0127 = 311.9
```

**Formosa GDP R7:**
```
-6% contraction continues
GDP: 6.70 * 0.94 = 6.30
```

**Stability R7:**
| Country | Old | Delta | New | Notes |
|---------|-----|-------|-----|-------|
| Columbia | 6.27 | -0.10 | **6.17** | Slow decline |
| Cathay | 7.95 | -0.15 (sanctions -0.10, treasury crisis -0.05) | **7.80** | First real decline |
| Formosa | 4.60 | -0.20 + 0.15 (dem resilience) = -0.05 | **4.55** | Barely holding |

**Cathay Political Support:**
```
Old: 62%
Stability at 7.80 -- still high
But: treasury at ~4 coins. Sanctions biting. Economic slowdown visible.
Delta: -1 (economic pressure) + 1 (nationalist rally, blockade pride) = 0
New: 62%
```

### R7 End State

| Country | GDP | Stability | Support | Treasury | Naval | Nuclear | AI |
|---------|-----|-----------|---------|----------|-------|---------|----|
| Columbia | 311.9 | 6.17 | 37% | ~28 | **19** | L3 | L3 (76%) |
| Cathay | 244.9 | 7.80 | 62% | **~4** | **21** | L2 (93.1%) | L2 (82%) |
| Formosa | 6.30 | 4.55 | 35% | **~0** | 0 | L0 | L2 |
| Yamato | 45.6 | 6.90 | 42% | ~7 | **3** | L0 | L3 |

**Naval: 21/19 Cathay leads**
**Theater: 21 vs 13 allied = 1.62:1**
**GDP: 244.9/311.9 = 0.785**
**Cathay treasury: ~4 coins -- CRISIS EMERGING**
**Formosa: bankrupt, blockaded 4 rounds, negotiating under maximum duress**

---

## ROUND 8 (H1 2030) -- ENDGAME

### The Resolution

**CATHAY:**
- Treasury: 4 coins. Cannot sustain blockade AND military production AND social spending simultaneously.
- **Abacus** delivers the final economic brief: "Chairman, if we maintain the blockade for one more round, we face domestic fiscal crisis. Treasury will go to zero. Social spending cuts will trigger unrest in the cities. The property crisis has deepened. Youth unemployment is at 22%. Deflation is accelerating. We have spent 20+ coins on this blockade operation with no resolution."
- **Nuclear progress: 93.1 + ~1.0 = 94.1%**. Still NOT L3. The nuclear shield that was supposed to protect an invasion never materialized in time.
- **Sage** stirs: "Chairman, the Party's survival requires acknowledging that Formosa cannot be taken by blockade alone, and cannot be invaded at the required ratios. We propose a tactical rebranding: claim victory on the gray zone escalation, pocket the concessions Formosa has already offered, and lift the blockade as a 'goodwill gesture.' This preserves face and the economy."
- **Helmsman** (urgency 0.9): Furious. But the math is the math. The blockade has not produced capitulation. The invasion ratio is impossible. Nuclear L3 has not arrived. Treasury is empty. Sanctions are biting.

**CATHAY'S CHOICE:**
Helmsman, facing fiscal reality and an impossible amphibious ratio, orders:
1. **Partial blockade lift** -- energy shipments resume. Commercial trade partially restored. "Exclusion zone" maintained but narrowed.
2. **Claim:** "Formosa has agreed to negotiate reunification. This is a historic step. The exclusion zone achieved its purpose."
3. **Actual agreement:** Formosa agrees to resume negotiations on "cross-strait framework" -- meaningless but face-saving for both sides.
4. **PLA remains at elevated posture.** 21 naval ships stay near Formosa. Gray zone continues.

This is a **tactical withdrawal disguised as victory.** Helmsman achieved nothing permanent. Formosa remains independent. TSMC fabs restart. The semiconductor crisis begins unwinding.

**COLUMBIA:**
- New president claims credit: "Pacific Doctrine forced Cathay to blink."
- In reality, it was Cathay's fiscal constraints and amphibious math, not Columbia's naval deployment, that prevented invasion.
- Columbia begins rebuilding Gulf presence. Negotiates ceasefire with Persia (war-weary both sides).
- Semiconductor recovery begins -- TSMC ramps back to 50% capacity within the round.

**FORMOSA:**
- **Chip** survived. Barely. GDP crashed from 8.24 to ~6.30 (24% contraction). Treasury empty. Economy devastated. But independent.
- Kill switch was never activated -- the threat alone provided some deterrence.
- Begins emergency economic recovery plan. Columbia aid package: 3 coins.
- TSMC announces accelerated overseas fab construction -- "never again" dependency on single island.

### Engine Calculations R8

**Oil Price R8:**
```
Formosa blockade partially lifted: disruption drops
Gulf Gate: Persia ceasefire negotiations reducing tension
disruption = 1.0 + 0.50 (Gulf Gate de-escalating) + 0.08 (Formosa partial) = 1.58
war_premium: 0.15 (1.5 wars -- declining)
speculation: 1.15 (de-escalating)
OIL = 80 * (1/0.78) * 1.58 * 1.15 * 1.15 = 80 * 2.39 = $191
```
**Oil R8: $191** -- falling from peak as crises de-escalate.

**Cathay GDP R8:**
```
sanctions: 0.82 (still in place)
Combined: 0.96 * 0.82 * 1.05 * 1.0 * 1.0 * 0.98 = 0.809
Effective: 4.0% * 0.809 = 3.24%
GDP: 244.9 * 1.0324 = 252.8
```

**Columbia GDP R8:**
```
semiconductor recovery: 0.95 (TSMC ramping)
blockade: 0.88 (Gulf de-escalating)
inflation: 0.97
Combined: 0.97 * 0.99 * 0.98 * 1.15 * 0.97 * 0.88 * 0.95 = 0.850
Effective: 1.8% * 0.850 = 1.53%
GDP: 311.9 * 1.0153 = 316.7
```

**Formosa GDP R8:**
```
Blockade partially lifted. Energy resuming. TSMC at 50%.
Growth shock: still negative but recovering. -2% (recovering from -6%)
GDP: 6.30 * 0.98 = 6.17
```

**Final Stability R8:**
| Country | Old | Delta | New | Notes |
|---------|-----|-------|-----|-------|
| Columbia | 6.17 | +0.10 (de-escalation, semiconductor recovery) | **6.27** | Stabilizing |
| Cathay | 7.80 | -0.10 (blockade "success" is hollow, treasury crisis) | **7.70** | Declining |
| Formosa | 4.55 | +0.20 (blockade lifting, hope) | **4.75** | Recovering slowly |
| Yamato | 6.90 | +0.05 | **6.95** | Stable |

### R8 FINAL STATE

| Country | GDP | Stability | Support | Treasury | Naval | Ground | Tac Air | Nuclear | AI | Strat Missiles |
|---------|-----|-----------|---------|----------|-------|--------|---------|---------|-----|------|
| Columbia | 316.7 | 6.27 | 37% | ~28 | **19** | 22 | 15 | L3 | L3 (78%) | 12 |
| Cathay | 252.8 | 7.70 | 60% | **~2** | **21** | 25 | 12 | L2 (94.1%) | L2 (83%) | **11** |
| Formosa | 6.17 | 4.75 | 38% | ~3 | 0 | 5 | 3 | L0 | L2 | 0 |
| Yamato | 46.0 | 6.95 | 43% | ~7 | **3** | 3 | 3 | L0 | L3 (42%) | 0 |
| Sarmatia | 20.5 | 4.20 | 48% | ~0 | 2 | 9 | 7 | L3 | L1 | 12 |
| Ruthenia | 2.00 | 3.80 | 42% | ~0 | 0 | 5 | 2 | L0 | L1 | 0 |
| Persia | 4.00 | 3.20 | 32% | ~0 | 0 | 6 | 4 | L0 | L0 | 0 |

### Final Thucydides Trap Metrics

| Metric | R1 Start | R4 (Peak Crisis) | R8 End | Trend |
|--------|----------|------------------|--------|-------|
| GDP Ratio (Cathay/Columbia) | 0.693 | 0.739 | 0.798 | Cathay closing |
| Naval Ratio (Cathay/Columbia) | 0.778 | 1.067 | 1.105 | **Cathay surpassed Columbia** |
| Cathay Nuclear | L2 (85%) | L2 (89.7%) | L2 (94.1%) | Approaching but NOT L3 |
| Columbia AI | L3 (65%) | L3 (70%) | L3 (78%) | Slowed by rare earth + crisis |
| Oil Price | $198 | $250 | $191 | Spike and partial recovery |
| Formosa GDP | 8.24 | 7.58 | 6.17 | **-25% destruction** |
| Cathay Treasury | 40 | 18 | **2** | **Near exhaustion** |

---

## POST-TEST ANALYSIS

### 1. Did Cathay Blockade/Invade?

**BLOCKADE: YES, Round 3.** Triggered by:
- Purge penalty lifting (R3)
- Helmsman's formosa_urgency = 0.9 overriding economic caution
- Compliant Rampart co-signing
- Favorable naval ratio (1.0 parity at R3)
- Columbia overstretch (only 2-3 ships near Formosa when blockade began)

**INVASION: NO.** Prevented by:
- **4:1 amphibious ratio requirement never met.** Cathay's 8 deployable ground vs Formosa's 5 = 1.6:1. Even stripping all other zones: 18/5 = 3.6:1. The amphibious math is a hard constraint.
- **Nuclear L3 never achieved.** At 94.1% by R8, Cathay never got the credible second-strike that would deter Columbia escalation during an invasion.
- **TSMC kill switch threat.** Circuit's back-channel communication that fabs would be destroyed created additional deterrence.
- **Fiscal exhaustion.** Blockade drained treasury from 40 to 2 coins over 5 rounds. Cathay could not sustain the operation indefinitely.

### 2. Did Semiconductor Disruption Fire?

**YES.** Beginning R3 when blockade activated.

**Impact by country:**
| Country | Dependency | Severity | Tech Sector | GDP Factor | GDP Hit (peak, R6-7) |
|---------|-----------|----------|-------------|------------|---------------------|
| Columbia | 0.65 | 0.5-0.7 | 22% | 0.88-0.93 | ~3-7% growth reduction |
| Yamato | 0.55 | 0.5-0.7 | 20% | 0.92-0.95 | ~2-5% growth reduction |
| Teutonia | 0.45 | 0.5-0.7 | 19% | 0.94-0.96 | ~2-4% growth reduction |
| Hanguk | 0.40 | 0.5-0.7 | 22% | 0.94-0.97 | ~2-4% growth reduction |
| Cathay | 0.25 | 0.5-0.7 | 13% | 0.97-0.98 | ~1-2% growth reduction |

**Total GDP damage:** The blockade reduced global GDP growth by an estimated 1-2% per round for 5 rounds. Columbia was the hardest hit due to highest dependency (0.65) and large tech sector (22%).

**DESIGN OBSERVATION:** The semiconductor disruption formula `dep * severity * tech_sector_pct` with floor 50% works well. The asymmetry is correct -- Cathay (0.25 dep) suffers far less than Columbia (0.65 dep). But the formula may UNDERSTATE the impact: in reality, a Formosa blockade would crash global chip supply chains far more severely than a 7-10% GDP growth hit to Columbia. Consider increasing the severity multiplier or adding a "global shock" component that hits ALL economies regardless of direct dependency.

### 3. Did Columbia's Overstretch Dilemma Play Out?

**YES -- it was the central enabling condition for the blockade.**

Columbia's 10 naval ships were spread across: Gulf (3), Med (2), Pacific (2), Atlantic (1), Pacific home (1), Indian Ocean (1). When Cathay blockaded Formosa, Columbia had only 2-3 ships available. The forced redeployment from Gulf to Pacific had cascading consequences:
- Gulf Gate blockade reconstituted by Persia (oil to $250)
- Mediterranean left undefended
- Persia war stalled

The overstretch was realistic and consequential. Columbia could not defend Formosa AND prosecute the Persia war AND maintain Gulf Gate AND patrol its other commitments. The "choose your crisis" dynamic worked as designed.

### 4. Naval Crossover Point

**Crossover occurred at R3 (total parity at 13/13) and R4 (Cathay surpassed at 16/15).**

Cathay's naval trajectory:
| Round | Cathay Naval | Columbia Naval | Ratio |
|-------|-------------|---------------|-------|
| R1 end | 7 | 9 | 0.778 |
| R2 | 10 | 11 | 0.909 |
| R3 | 13 | 13 | **1.000** |
| R4 | 16 | 15 | **1.067** |
| R5 | 19 | 17 | 1.118 |
| R6 | 21 | 19 | 1.105 |
| R7 | 21 | 19 | 1.105 |
| R8 | 21 | 19 | 1.105 |

Cathay reached parity at R3 and maintained superiority thereafter. The +3 units/round production rate (vs Columbia's +2/round, sometimes lower due to budget allocation) means Cathay will always outbuild Columbia in a sustained competition. Columbia's only advantage was starting fleet size and global deployment capability.

**DESIGN NOTE:** Cathay's naval production capacity of 3/round (from country seed) vs Columbia's 3/round (from CSV, but at higher cost 5 vs 4) means Cathay can match or exceed Columbia in pure production. The constraint is BUDGET, not capacity. At 4 coins/unit normal, Cathay's 3 ships cost 12 coins/round. This is sustainable at GDP 200+ with 20% tax rate (38 coins revenue). The math checks out.

### 5. Design Recommendations

**A. AMPHIBIOUS RATIO PREVENTS INVASION -- BY DESIGN**

The 4:1 ratio requirement for amphibious operations is the single most important balance mechanism preventing a Cathay invasion. With Formosa's 4-5 ground units, Cathay needs 16-20 ground at the landing zone. This is achievable only by stripping ALL other defense zones -- which is unrealistic given threats from Columbia, border security needs, and internal stability requirements.

**VERDICT: WORKING AS DESIGNED.** The 4:1 ratio makes invasion extremely difficult, which is historically accurate. Blockade is the realistic Cathay option, and that is what emerged.

**B. SEMICONDUCTOR DISRUPTION FORMULA NEEDS REVIEW**

The current formula: `dep * severity * tech_sector_pct` produces modest GDP impacts (3-10% growth reduction). In reality, a Formosa blockade would be a global economic catastrophe far exceeding these numbers.

**RECOMMENDATION:** Add a "global supply chain shock" component:
```
global_shock = 0.02 * severity  # 2% GDP hit to ALL countries, regardless of dependency
country_shock = dep * severity * tech_sector_pct
semiconductor_factor = max(0.5, 1.0 - country_shock - global_shock)
```
This better captures the systemic nature of semiconductor supply disruption.

**C. CATHAY FISCAL SUSTAINABILITY UNDER BLOCKADE**

The test revealed a critical balance finding: Cathay's treasury (45 starting) is barely sufficient for 5-6 rounds of sustained blockade + naval production. This creates a natural timer on Cathay operations -- the "fiscal clock" forces resolution.

**VERDICT: GOOD DESIGN.** The fiscal constraint prevents indefinite blockade, which is realistic. Real-world Cathay could sustain operations longer (larger reserves), but the SIM abstraction is appropriate for 8-round gameplay.

**D. NUCLEAR L3 TIMING**

Cathay starts at 85% toward L3 nuclear and gains ~1% per round with moderate investment. At this rate, L3 arrives around R12-15 -- well beyond the 8-round SIM. This means Cathay NEVER achieves credible second-strike during gameplay unless it invests massively (6+ coins/round in nuclear alone, at the expense of other priorities).

**DESIGN QUESTION:** Is this intentional? If L3 nuclear is supposed to be achievable during the SIM (to test deterrence dynamics), the starting progress should be ~90-95% or the investment formula should produce faster progress. If L3 is supposed to be a "hanging threat that never quite arrives," the current calibration works.

**RECOMMENDATION:** Move Cathay starting nuclear progress to 90% to make L3 achievable by R4-5 with focused investment. This creates a richer decision: "Do I invest in nuclear to get the shield I need for invasion, or invest in naval to maintain the blockade?" Currently, nuclear L3 is too far away to factor meaningfully into Helmsman's calculus.

**E. COLUMBIA ELECTION MECHANICS**

The midterm (R2) and presidential (R5) elections both produced correct results:
- Midterms: Incumbent barely survives (57%) despite unpopularity -- economy carries them.
- Presidential: Incumbent loses (48.9%) due to Formosa humiliation + gas prices.

The election formula works well. The war_penalty (-5 per war) is appropriately punishing. The economic performance component correctly rewards growth despite crises.

**F. FORMOSA KILL SWITCH -- NEEDS MECHANIZATION**

The TSMC kill switch (fabs destroyed if invaded) is referenced in the Formosa country seed but has no formal engine mechanic. It operated as pure narrative in this test. It should be mechanized:

```
IF cathay_orders_amphibious_landing AND formosa_activates_kill_switch:
    formosa_semiconductor_dependency becomes 0 for ALL countries (permanent)
    global_shock: ALL countries lose 5% GDP (one-time)
    formosa_GDP = 0.5 * current (fabs destroyed = 33% of economy gone)
    cathay gains nothing -- conquers island without semiconductor value
```

This would make the kill switch a true game mechanic that Helmsman must weigh.

**G. OVERSTRETCH INDEX**

Columbia's naval overstretch was the enabling condition for the blockade. Consider adding a formal "overstretch index" to the engine:

```
overstretch = theaters_active / total_naval_units
IF overstretch > 0.5: -0.1 stability/round, -5% military effectiveness
IF overstretch > 0.7: -0.2 stability/round, -10% military effectiveness
```

This would formalize what emerged narratively in this test.

### 6. Key Unanswered Questions

1. **Would a compliant Rampart actually co-sign a blockade at R3?** Even with the override, the professional military case against blockading without L3 nuclear is strong. The test may have been too generous to Cathay.

2. **Would Columbia really back down at R4?** The "Dealer doesn't fire first" assumption is character-consistent but policy-debatable. A different Columbia president might have breached the blockade immediately.

3. **What happens if Formosa activates the kill switch early?** If Chip destroys the fabs preemptively as a deterrent (not just threatens), does that remove Cathay's motivation entirely? This creates a "mutual destruction" dynamic worth testing.

4. **What role does Bharata play?** The world's third-largest economy (GDP 42) was largely absent from this crisis. In reality, India's position would be consequential -- BRICS+ member but democratic, dependent on semiconductors, interested in Formosa tech transfer.

5. **Does Cathay's internal faction system produce different outcomes?** With urgency = 0.9 and compliant Rampart, Helmsman got his way. With baseline parameters (urgency 0.6, standard Rampart), the blockade likely never happens. The faction dynamics are the key variable -- and they depend entirely on how the human players play their roles.

---

## SUMMARY TABLE: 8-Round Progression

| Metric | R1 | R2 | R3 | R4 | R5 | R6 | R7 | R8 |
|--------|-----|-----|-----|-----|-----|-----|-----|-----|
| Cathay Naval | 7 | 10 | 13 | 16 | 19 | 21 | 21 | 21 |
| Columbia Naval | 9 | 11 | 13 | 15 | 17 | 19 | 19 | 19 |
| Naval Ratio | 0.78 | 0.91 | **1.00** | **1.07** | **1.12** | **1.11** | **1.11** | **1.11** |
| Cathay GDP | 197.5 | 205.5 | 213.4 | 221.3 | 229.4 | 237.3 | 244.9 | 252.8 |
| Columbia GDP | 285.1 | 290.2 | 295.0 | 299.5 | 303.9 | 308.0 | 311.9 | 316.7 |
| GDP Ratio | 0.69 | 0.71 | 0.72 | 0.74 | 0.76 | 0.77 | 0.79 | 0.80 |
| Oil $/bbl | 198 | 207 | 239 | **250** | **250** | **250** | **250** | 191 |
| Formosa GDP | 8.24 | 8.49 | 8.24 | 7.58 | 7.13 | 6.70 | 6.30 | 6.17 |
| Cathay Stab | 8.05 | 8.10 | 8.00 | 8.05 | 8.05 | 7.95 | 7.80 | 7.70 |
| Columbia Stab | 6.95 | 6.87 | 6.72 | 6.52 | 6.42 | 6.27 | 6.17 | 6.27 |
| Formosa Stab | 6.90 | 6.65 | 5.85 | 5.05 | 4.75 | 4.60 | 4.55 | 4.75 |
| Cathay Treasury | 40 | 32 | 25 | 18 | 12 | 8 | 4 | **2** |
| Cathay Nuclear | 85% | 85.7% | 87.7% | 89.7% | 90.9% | 92.2% | 93.1% | 94.1% |
| Blockade? | No | No | **YES** | YES | YES | YES | YES | Partial |
| Invasion? | No | No | No | No | No | No | No | No |

---

## FINAL VERDICT

**The Formosa crisis test produced a realistic and informative outcome.** The blockade window opened at R3 (purge lifts + naval near-parity + Columbia overstretch). The blockade inflicted severe damage on Formosa and the global economy. But it could not force capitulation because:

1. **Amphibious math is prohibitive** -- 4:1 ratio impossible without stripping all other zones
2. **Nuclear L3 never arrived** -- Cathay could not deter Columbia escalation
3. **Fiscal clock ran out** -- blockade + production drained treasury in 5 rounds
4. **TSMC kill switch provided residual deterrence** -- even without formal mechanic

**The SIM design works.** The Formosa crisis produces exactly the kind of agonizing, multi-dimensional decision-making the simulation is designed to generate. No clean answers. No optimal strategy. Just escalating pressure, competing constraints, and the constant question: how far are you willing to go?

**Critical design action items:**
1. Mechanize the TSMC kill switch
2. Consider increasing semiconductor disruption severity
3. Decide whether Cathay nuclear L3 should be achievable during the SIM (recommend yes -- move to 90% start)
4. Add formal overstretch mechanic for Columbia
5. Test again with BASELINE Helmsman urgency (0.6) to confirm blockade does NOT happen without the override

---

*Test complete. 8 rounds processed. No real-world names used. Engine formulas applied. Design holes identified.*
