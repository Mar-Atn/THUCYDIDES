# TEST 3: GULF GATE ECONOMICS — Full Results
## SEED TESTS3 | Engine v3 (4 Calibration Fixes)
**Date:** 2026-03-28 | **Tester:** TESTER-ORCHESTRATOR (Independent Instance)

---

## SCENARIO SETUP

**Focus:** Oil price with Cal-1 inertia model (40% sticky / 60% equilibrium).
**Key question:** Does Cal-1 produce the gradual climb (R1 ~$137, converging to ~$175 by R3-4) that the calibration doc predicts? Does demand destruction work? How does the soft cap above $200 behave?

**Starting conditions:**
- Oil price: $80 (baseline)
- Gulf Gate: BLOCKED (Persia ground forces on cp_gulf_gate)
- OPEC production: all "normal" (Nordostan, Persia, Solaria, Mirage)
- Active wars: 2 (Nordostan-Heartland, Columbia-Persia)
- No Formosa blockade (isolated Gulf Gate scenario)

**Scenario phases:**
- R1-R3: Gulf Gate blocked, OPEC normal. Test gradual climb.
- R4: OPEC restricts (all "low"). Test combined shock.
- R5: Demand destruction visible? One OPEC defects to "high."
- R6: Full OPEC defection to "high." Gulf Gate still blocked.
- R7: Gulf Gate opens (military resolution). Test gradual decline.
- R8: Full normalization. Test convergence.

---

## OIL PRICE FORMULA TRACE

### Reference Formula
```
supply = 1.0 + sum(OPEC adjustments) - sanctions_on_producers
disruption = 1.0 + gulf_gate(0.50) + formosa(0.10) + other_chokepoints
demand = 1.0 + GDP_elasticity - crisis_demand_reduction
war_premium = min(n_wars * 0.05, 0.15)
raw_price = 80 * (demand/supply) * disruption * (1 + war_premium)
formula_price = soft_cap(raw_price) if raw_price > 200
price = previous * 0.40 + formula_price * 0.60  [Cal-1 inertia]
```

---

## ROUND-BY-ROUND SIMULATION

### ROUND 1: Gulf Gate Shock — Inertia Dampens

**Conditions:**
- Gulf Gate: BLOCKED. disruption = 1.0 + 0.50 = 1.50.
- OPEC: all "normal." supply = 1.0.
- Sanctions on Nordostan L2+: supply -= 0.08. Sanctions on Persia L2+: supply -= 0.08. Total supply = 1.0 - 0.16 = **0.84**.
- Wars: 2. war_premium = 0.10.
- Demand: ~1.0 (no crisis economies yet, slight GDP elasticity).
  - Average GDP growth across 21 countries: ~2.5%. demand += (2.5 - 2.0) * 0.03 = +0.015.
  - demand = **1.015**.

**Calculation:**
- raw_price = 80 * (1.015 / 0.84) * 1.50 * (1 + 0.10)
- raw_price = 80 * 1.2083 * 1.50 * 1.10
- raw_price = 80 * 1.994 = **$159.5**

- **Inertia (Cal-1):** previous = $80 (R0 baseline).
- price = 80 * 0.40 + 159.5 * 0.60 = 32.0 + 95.7 = **$127.7**

**Calibration doc predicted:** ~$137 (with supply = 1.0, no sanctions reduction). The difference is that I'm including sanctions supply reduction (-0.16), which was not explicitly in the calibration trace. Without sanctions: supply = 1.0, raw_price = 80 * 1.015 * 1.50 * 1.10 = $133.98, inertia price = 80*0.4 + 134*0.6 = **$112.4**.

CLARIFICATION: The v3 calibration doc (Scenario 1) used supply = 0.76 (4 OPEC at "low"), which is a different scenario. For THIS test (OPEC normal, Gulf Gate blocked, sanctions on producers), supply = 0.84 is correct.

**Revised R1 price: $127.7** with sanctions supply reduction included.

**Key country GDP impacts at $128 oil:**

| Country | Type | Oil Shock | Oil Revenue | GDP Impact |
|---------|------|-----------|-------------|------------|
| Columbia | Importer, producer | -0.02*(128-100)/50 = -1.12% | 128*0.08*288*0.01 = $2.95 | Mild net: oil revenue offsets shock |
| Cathay | Importer | -1.12% | 0 | Moderate negative |
| Nordostan | Producer | +0.01*(128-80)/50 = +0.96% | 128*0.40*20*0.01 = $1.02 | Strong positive — oil windfall |
| Persia | Producer (under siege) | +0.96% | 128*0.35*4.5*0.01 = $0.20 | Minor (GDP so low) |
| Solaria | Producer | +0.96% | 128*0.45*11*0.01 = $0.63 | Strong positive |
| Teutonia | Importer | -1.12% | 0 | Moderate negative |
| Bharata | Importer | -1.12% | 0 | Significant (large economy) |

**Nordostan Enrichment Paradox check:**
- Nordostan oil revenue at $128: ~$1.02 coins.
- Nordostan under L2+ sanctions. sanctions_hit: ~-18% GDP (from Cal-2).
- GDP: 20 * 0.82 = ~16.4. Tax revenue: 16.4 * 0.20 = 3.28. Plus oil rev 1.02 = **4.30 total revenue**.
- Military maintenance: (18+2+8+12+3)*0.3 = 12.9. Social: 0.25*16.4 = 4.1. Mandatory = 17.0.
- Deficit: 17.0 - 4.30 = **12.7**. Still deep deficit despite oil windfall.
- Without oil revenue: deficit would be 17.0 - 3.28 = 13.72. Oil saves ~1 coin.

The paradox is visible but not overwhelming: oil revenue cushions but does not offset sanctions. At $128, the paradox is moderate. At higher prices, it becomes more significant.

**R1 State:**

| Variable | Value | Cal Doc Prediction | Verdict |
|----------|-------|--------------------|---------|
| Oil price | $127.7 | ~$137 (different scenario) | PASS — correct formula with sanctions |
| Nordostan oil_rev | $1.02 | 0.8-1.4 corridor | PASS |
| Columbia GDP impact | -1.12% oil + $2.95 rev | mild net | PASS |

---

### ROUND 2: Inertia Convergence

**Conditions unchanged:** Gulf Gate blocked, OPEC normal, sanctions on producers.

**Calculation:**
- Same formula_price: $159.5 (conditions unchanged).
- previous = $127.7.
- price = 127.7 * 0.40 + 159.5 * 0.60 = 51.08 + 95.70 = **$146.8**

Oil climbs from $127.7 to $146.8 — a $19.1 increase. The inertia model produces a gradual staircase, not a spike.

**Key GDP impacts at $147:**

Columbia oil shock: -0.02 * (147-100)/50 = -1.88%. More significant now.
Nordostan oil revenue: 147 * 0.40 * ~16 * 0.01 = **$0.94** (GDP declining from sanctions).
Cathay oil shock: -1.88%. Starting to bite.

**Demand elasticity update:**
- Average GDP growth declining (sanctions + oil hitting growth rates). avg ~1.8%.
- demand += (1.8 - 2.0) * 0.03 = -0.006. demand = 0.994.
- This slightly reduces formula_price for R3. Feedback loop engaging.

**R2 State:**

| Variable | Value | Change from R1 |
|----------|-------|----------------|
| Oil price | $146.8 | +$19.1 |
| Columbia GDP | ~282.6 | -0.8% (oil + war) |
| Cathay GDP | ~202.8 | +1.6% (base growth offsets oil) |
| Nordostan GDP | ~13.5 | -17% (sanctions compounding) |

---

### ROUND 3: Approaching Equilibrium

**Conditions unchanged.**

**Calculation:**
- Demand adjusting: avg growth ~1.5%. demand = 1.0 + (1.5-2.0)*0.03 = 0.985.
- raw_price = 80 * (0.985/0.84) * 1.50 * 1.10 = 80 * 1.7589 * 1.10 = 80 * 1.758 * 1.10 = **$154.7**
- previous = $146.8.
- price = 146.8 * 0.40 + 154.7 * 0.60 = 58.72 + 92.82 = **$151.5**

Oil is converging. The gap between current price and equilibrium narrows each round:
- R1: $80 -> $127.7 (gap = 31.8 to equilibrium ~$160)
- R2: $127.7 -> $146.8 (gap = 13.2)
- R3: $146.8 -> $151.5 (gap = 3.2)

The exponential convergence of the 40/60 blend is clear: each round closes ~60% of the remaining gap.

**Stress trigger check (oil > $150 for importers):**
- Columbia: oil > $150 = YES. This is the first stress trigger from oil.
- Combined with any other trigger (GDP contraction, etc.) = stressed state possible.

**R3 State:**

| Variable | Value | Change from R2 |
|----------|-------|----------------|
| Oil price | $151.5 | +$4.7 |
| Columbia GDP | ~278.9 | -1.3% |
| Cathay GDP | ~208.7 | +2.9% |
| Nordostan GDP | ~11.5 | Declining slower (approaching adaptation) |
| Nordostan oil_rev | ~$0.66 | Declining with GDP |

---

### ROUND 4: OPEC Restricts — Combined Shock

**OPEC decision: ALL members set "low" production.**
- Nordostan: low. Persia: low. Solaria: low. Mirage: low.
- supply -= 4 * 0.06 = -0.24. supply = 1.0 - 0.24 - 0.16 (sanctions) = **0.60**.

**Calculation:**
- demand ~0.98 (growth slowing globally).
- raw_price = 80 * (0.98/0.60) * 1.50 * 1.10 = 80 * 1.633 * 1.50 * 1.10 = 80 * 2.695 = **$215.6**
- Soft cap: raw > $200. formula_price = 200 + 50 * (1 - exp(-(215.6-200)/100)) = 200 + 50 * (1 - exp(-0.156)) = 200 + 50 * 0.1443 = **$207.2**
- previous = $151.5.
- price = 151.5 * 0.40 + 207.2 * 0.60 = 60.6 + 124.3 = **$184.9**

OPEC restriction causes a sharp jump — from $151.5 to $184.9 (+$33.4). Even with inertia, the combined effect of Gulf Gate blockade + OPEC restriction + sanctions supply reduction pushes through strongly.

**Without inertia (binary):** Price would jump to $207.2 — a $55.7 single-round swing. Inertia dampens this by 40%, producing a more realistic $33.4 swing.

**Soft cap test:** The raw price of $215.6 triggers the asymptotic cap, compressing it to $207.2 — a $8.4 compression. The cap is working but the price is not yet high enough to show dramatic compression (that happens above $250 raw).

**Key impacts at $185:**

Columbia oil shock: -0.02 * (185-100)/50 = **-3.4%**. Severe.
Columbia stress triggers: oil > $150 (yes), GDP < -1 (yes). **2 triggers = STRESSED.**

Nordostan oil revenue surges: 185 * 0.40 * ~11 * 0.01 = **$0.81**. Still modest because GDP has been eroded by sanctions. But the revenue/GDP ratio is improving.

**Nordostan Enrichment Paradox amplified:**
At $185 oil, Nordostan's oil sector (40% of GDP) generates significant revenue relative to its shrinking economy. Tax + oil revenue: ~2.2 + 0.81 = ~3.0. Still far short of mandatory costs (~10), but the oil cushion is now ~27% of total revenue. If sanctions were lifted, Nordostan's oil revenue would explode.

**R4 State:**

| Variable | Value | Change from R3 |
|----------|-------|----------------|
| Oil price | $184.9 | +$33.4 |
| Columbia GDP | ~269.2 | -3.4% |
| Columbia eco_state | STRESSED | NEW |
| Cathay GDP | ~211.8 | +1.5% |
| Nordostan GDP | ~10.2 | Declining slower |
| Solaria GDP | ~12.5 | GROWING (oil windfall) |

---

### ROUND 5: Demand Destruction Engages — OPEC Defection

**Columbia now STRESSED.** Cathay approaching stress (growth slowing). Multiple smaller economies feeling oil pain.

**OPEC defection:** Solaria defects to "high" (prisoner's dilemma — wants market share).
- supply: Nordostan low (-0.06), Persia low (-0.06), Solaria HIGH (+0.06), Mirage low (-0.06).
- Net: -0.12. supply = 1.0 - 0.12 - 0.16 (sanctions) = **0.72**.

**Demand destruction:**
- Columbia STRESSED but not yet CRISIS (GDP > 30, but not in crisis state yet). No demand reduction from crisis states.
- BUT average GDP growth has fallen to ~0.5%. demand = 1.0 + (0.5 - 2.0)*0.03 = **0.955**.

**Calculation:**
- raw_price = 80 * (0.955/0.72) * 1.50 * 1.10 = 80 * 1.326 * 1.50 * 1.10 = 80 * 2.189 = **$175.1**
- formula_price = $175.1 (< $200, no soft cap).
- previous = $184.9.
- price = 184.9 * 0.40 + 175.1 * 0.60 = 73.96 + 105.06 = **$179.0**

Oil DECLINES from $184.9 to $179.0 (-$5.9). Solaria's defection to "high" reduces the supply squeeze, and demand destruction from slowing global growth pulls the equilibrium price below the current price. The inertia model produces a gradual decline rather than a sharp drop.

**Demand destruction analysis:**
The demand-side feedback is working but WEAK. The formula uses average GDP growth across ALL 21 countries, so a few stressed economies are diluted by many still-growing small economies. The crisis-specific demand reduction (-0.05 per crisis major economy) would be more impactful but requires a country to formally enter crisis state.

DESIGN OBSERVATION: Demand destruction through GDP growth elasticity is too slow. Consider: (a) weighting demand by GDP (large economy contraction should matter more than small economy growth), or (b) adding oil-specific demand destruction (countries explicitly reduce consumption when oil > $150 for 2+ rounds).

**R5 State:**

| Variable | Value | Change from R4 |
|----------|-------|----------------|
| Oil price | $179.0 | -$5.9 |
| Columbia GDP | ~263.0 | -2.3% |
| Columbia eco_state | STRESSED | Holding |
| Cathay GDP | ~214.0 | +1.0% (slowing) |

---

### ROUND 6: Full OPEC Defection

**All OPEC members defect to "high":**
- supply: +4 * 0.06 = +0.24. supply = 1.0 + 0.24 - 0.16 (sanctions) = **1.08**.

**Demand:** avg growth ~0.3%. demand = 1.0 + (0.3-2.0)*0.03 = 0.949.

**Calculation:**
- raw_price = 80 * (0.949/1.08) * 1.50 * 1.10 = 80 * 0.879 * 1.50 * 1.10 = 80 * 1.450 = **$116.0**
- previous = $179.0.
- price = 179.0 * 0.40 + 116.0 * 0.60 = 71.6 + 69.6 = **$141.2**

Dramatic decline: $179 -> $141 (-$37.8). OPEC defection floods the market. But inertia prevents the crash from being instant — without inertia, price would drop to $116 (a $63 swing). Inertia dampens to $37.8.

**Gulf Gate still blocked:** The $141 price is STILL elevated above the ~$95-100 that would prevail with Gulf Gate open + OPEC high. The blockade maintains a $40-50 price floor even with OPEC flooding.

**Nordostan oil revenue at $141:**
- 141 * 0.40 * ~9.5 * 0.01 = ~$0.54. Revenue declining with both GDP and price.
- Nordostan sanctions adaptation kicks in (R5+): sanctions_hit * 0.60.

**R6 State:**

| Variable | Value | Change from R5 |
|----------|-------|----------------|
| Oil price | $141.2 | -$37.8 |
| Columbia GDP | ~261.0 | -0.8% (oil relief helps) |
| Cathay GDP | ~216.5 | +1.2% (recovering) |
| Nordostan GDP | ~9.3 | Adaptation slowing decline |

---

### ROUND 7: Gulf Gate Opens — Military Resolution

**Gulf Gate opens:** Columbia-coalition ground forces clear Persia from Gulf Gate zone. `chokepoint gulf_gate_ground = open`. `ground_blockades gulf_gate` removed.

- disruption: 1.50 -> 1.00 (Gulf Gate component removed).
- OPEC still at "high." supply = 1.08.
- Sanctions on producers still active: supply adjustment already counted.

**Calculation:**
- raw_price = 80 * (0.95/1.08) * 1.00 * 1.10 = 80 * 0.880 * 1.00 * 1.10 = 80 * 0.968 = **$77.4**
- Wait — one war resolved (Columbia-Persia ceasefire after Gulf Gate clearance). Wars: 1 (Nordostan-Heartland). war_premium = 1 * 0.05 = 0.05.
- raw_price = 80 * (0.95/1.08) * 1.00 * 1.05 = 80 * 0.880 * 1.05 = **$73.9**
- previous = $141.2.
- price = 141.2 * 0.40 + 73.9 * 0.60 = 56.48 + 44.34 = **$100.8**

Gulf Gate opening produces a dramatic formula price drop to $74, but inertia dampens the actual price to $100.8. Without inertia, price would crash from $141 to $74 in a single round — a $67 cliff. With inertia, it drops $40.4. Still large, but gradual.

**Oil producer impact:**
Nordostan: oil revenue plummets. 101 * 0.40 * ~9.0 * 0.01 = **$0.36**. At this price, oil revenue barely matters.
Solaria: 101 * 0.45 * 12.5 * 0.01 = $0.57. Down from $0.80+ at peak.

**Columbia ceasefire rally:** Momentum +1.5 (Pass 2 ceasefire rally). GDP boost from peace dividend.
Columbia eco_state: recovery begins. stress_triggers declining.

**R7 State:**

| Variable | Value | Change from R6 |
|----------|-------|----------------|
| Oil price | $100.8 | -$40.4 |
| Columbia GDP | ~265.0 | +1.5% (recovery) |
| Columbia eco_state | STRESSED (recovering) | Improving |
| Nordostan GDP | ~8.8 | Decline continuing but slower |

---

### ROUND 8: Normalization

**Conditions:** Gulf Gate open. OPEC "high." 1 war (Nordostan-Heartland). Sanctions on Nordostan.

**Calculation:**
- supply = 1.0 + 0.24 - 0.08 (Nordostan only, Persia ceasefire) = **1.16**.
- demand recovering: avg growth ~1.5%. demand = 0.985.
- disruption = 1.0. war_premium = 0.05.
- raw_price = 80 * (0.985/1.16) * 1.0 * 1.05 = 80 * 0.849 * 1.05 = **$71.3**
- previous = $100.8.
- price = 100.8 * 0.40 + 71.3 * 0.60 = 40.32 + 42.78 = **$83.1**

Oil approaching baseline. The full cycle: $80 -> $128 -> $147 -> $152 -> $185 -> $179 -> $141 -> $101 -> $83. Convergence toward the new equilibrium (~$71 with OPEC high and one war) continues.

**R8 State:**

| Variable | Value | Change from R7 |
|----------|-------|----------------|
| Oil price | $83.1 | -$17.7 |
| Columbia GDP | ~269.5 | +1.7% (recovering) |
| Cathay GDP | ~222.0 | +2.5% |
| Nordostan GDP | ~8.5 | Stabilizing at low level |

---

## OIL PRICE TRAJECTORY — COMPLETE

| Round | Formula Price | Inertia Price | Delta from Previous | Conditions Change |
|-------|-------------|---------------|--------------------|--------------------|
| R0 | — | $80.0 | — | Baseline |
| R1 | $159.5 | **$127.7** | +$47.7 | Gulf Gate blocked, sanctions |
| R2 | $159.5 | **$146.8** | +$19.1 | Same conditions |
| R3 | $154.7 | **$151.5** | +$4.7 | Demand elasticity slight reduction |
| R4 | $207.2* | **$184.9** | +$33.4 | OPEC all "low" — combined shock |
| R5 | $175.1 | **$179.0** | -$5.9 | Solaria defects to "high" |
| R6 | $116.0 | **$141.2** | -$37.8 | All OPEC "high" |
| R7 | $73.9 | **$100.8** | -$40.4 | Gulf Gate opens, ceasefire |
| R8 | $71.3 | **$83.1** | -$17.7 | Normalization continuing |

*Soft-capped from $215.6 raw.

### Inertia Behavior Analysis

**Upward convergence (R1-R3):**
- Gap closure rate: ~60% per round (exactly as designed).
- R1: 80 -> 127.7 (closes 60% of 79.5 gap = 47.7). Correct.
- R2: 127.7 -> 146.8 (closes 60% of 31.8 gap = 19.1). Correct.
- R3: 146.8 -> 151.5 (closes 60% of 7.9 gap = 4.7). Correct.
- Full convergence in 3-4 rounds. The gradual climb avoids the $80-to-$160 spike that TESTS2 produced.

**Shock response (R4 OPEC restriction):**
- Formula jumps from $155 to $207 (new equilibrium). Price jumps from $152 to $185.
- Gap closure: 60% of $55 gap = $33. Correct.
- The inertia model handles NEW shocks well — it still transmits 60% of the shock immediately while smoothing the rest.

**Downward convergence (R5-R8):**
- R5: formula drops, inertia dampens decline. Price falls $5.9.
- R6: OPEC floods, formula crashes. Price drops $37.8 (inertia prevents $63 crash).
- R7: Gulf Gate opens, formula at $74. Price drops $40.4 (inertia prevents $67 crash).
- R8: Continuing convergence. Price approaches new equilibrium.

**Key finding:** Downward inertia is equally important. Without it, OPEC defection + Gulf Gate opening in R6-R7 would crash oil from $179 to $74 in 2 rounds — a $105 collapse. With inertia, the decline is $179 -> $141 -> $101 -> $83 over 3 rounds. This is far more realistic (physical oil stocks take time to clear, contracts are forward-priced, refinery margins adjust slowly).

---

## SOFT CAP BEHAVIOR

The soft cap formula: `200 + 50 * (1 - exp(-(raw - 200) / 100))`

| Raw Price | Soft-Capped Price | Compression |
|-----------|-------------------|-------------|
| $200 | $200.0 | 0% |
| $215 | $207.0 | -$8.0 |
| $230 | $213.5 | -$16.5 |
| $250 | $219.4 | -$30.6 |
| $300 | $231.6 | -$68.4 |
| $400 | $243.2 | -$156.8 |
| $500+ | ~$249.0 | Asymptotic to $250 |

**Assessment:** The theoretical maximum is ~$250 (200 + 50). The cap engages gently at $200 and becomes aggressive above $250 raw. In this test, the cap fired only once (R4 at $215.6 raw -> $207.2 capped), compressing by $8.4. More extreme scenarios (multiple chokepoints blocked + OPEC restriction + war premium max) could push raw price to $300+, where the cap would compress to ~$232.

**Design observation:** The $250 ceiling may be too low. Historical oil spikes have reached $147 (2008) in real terms, and a simultaneous Gulf Gate + Formosa disruption with OPEC restriction could plausibly push prices to $250-300. Consider raising the asymptote: `200 + 80 * (1 - exp(-(raw-200)/150))` would give a ceiling of ~$280 while maintaining the compression curve shape.

---

## DEMAND DESTRUCTION ANALYSIS

**Mechanism 1: GDP growth elasticity**
- demand += (avg_growth - 2.0) * 0.03
- At R5 (avg_growth ~0.5%): demand = 1.0 + (0.5-2.0)*0.03 = 0.955. Only -4.5% demand reduction.
- This is weak. A 5pp drop in average global growth produces only 4.5% demand reduction, which translates to ~$7-8 lower price. Against a Gulf Gate disruption of +50%, this is negligible.

**Mechanism 2: Crisis state demand reduction**
- demand -= 0.05 per major economy in crisis, -0.10 per collapse.
- In this test, no major economy entered crisis (Columbia stayed at STRESSED). So this mechanism never fired.
- If Columbia had entered crisis (R6+), demand -= 0.05 would reduce price by ~$8-10.

**Assessment: Demand destruction is too weak.** Two issues:

1. **GDP elasticity is averaged across ALL countries.** A GDP-weighted average would be more responsive — Columbia contracting 3% matters more than Caribe contracting 3%. Currently both equally dilute the average.

2. **Crisis threshold is too high.** Countries must formally enter "crisis" economic state for the stronger demand reduction to fire. A country can be in severe recession (-5% GDP) but still in "stressed" state, producing no demand destruction.

**Recommendation:** Replace simple average with GDP-weighted growth average: `demand += (gdp_weighted_avg_growth - 2.0) * 0.05` (larger coefficient). Add intermediate demand response: STRESSED major economy reduces demand by -0.02 (in addition to crisis -0.05 and collapse -0.10).

---

## NORDOSTAN ENRICHMENT PARADOX — DEEP ANALYSIS

**Oil revenue trajectory:**

| Round | Oil Price | Nord GDP | Oil Rev | Tax Rev | Total Rev | Mandatory | Deficit | Money Printed |
|-------|-----------|----------|---------|---------|-----------|-----------|---------|---------------|
| R1 | $128 | 16.4 | 1.02 | 3.28 | 4.30 | 17.0 | 12.7 | 6.7 |
| R2 | $147 | 13.5 | 0.79 | 2.70 | 3.49 | 14.6 | 11.1 | 11.1 |
| R3 | $152 | 11.5 | 0.70 | 2.30 | 3.00 | 12.5 | 9.5 | 9.5 |
| R4 | $185 | 10.2 | 0.76 | 2.04 | 2.80 | 11.2 | 8.4 | 8.4 |
| R5 | $179 | 9.3 | 0.67 | 1.86 | 2.53 | 10.4 | 7.9 | 7.9 |
| R6 | $141 | 9.0 | 0.51 | 1.80 | 2.31 | 10.1 | 7.8 | 7.8 |
| R7 | $101 | 8.8 | 0.36 | 1.76 | 2.12 | 9.8 | 7.7 | 7.7 |
| R8 | $83 | 8.5 | 0.27 | 1.70 | 1.97 | 9.5 | 7.5 | 7.5 |

**Key finding:** Oil revenue is meaningful but NOT sufficient to change Nordostan's trajectory. Even at peak oil ($185, R4), oil revenue of $0.76 is only 27% of total revenue. The structural deficit is driven by military maintenance costs (12.9 coins at start) vastly exceeding revenue capacity. Oil revenue cannot close this gap.

**Paradox verdict:** The Nordostan Enrichment Paradox exists but is not as dramatic as the Dependencies document suggests. Nordostan benefits from high oil prices, and high oil prices are partially caused by the war Nordostan wages (via Gulf Gate disruption and war premium). But the benefit is marginal (~$0.3-0.5 additional revenue per round at peak) compared to the costs of war and sanctions. The paradox is more ironic than game-breaking.

**DESIGN OBSERVATION:** The oil revenue formula `price * resource_pct * GDP * 0.01` means oil revenue SHRINKS as GDP shrinks. This creates a second paradox: sanctions reduce GDP, which reduces the base for oil revenue, which reduces the benefit of high oil prices. Nordostan's oil revenue would be $2.24 at $185 with starting GDP of 20, but only $0.76 with actual R4 GDP of 10.2. Sanctions reduce oil revenue by 66%.

---

## COMPARISON TO TESTS2

| Metric | TESTS2 (binary pricing) | TESTS3 (inertia model) | Assessment |
|--------|------------------------|------------------------|------------|
| R1 oil price | $175 (instant spike) | $127.7 (inertia dampened) | MAJOR IMPROVEMENT — realistic |
| R1 -> R2 oil | $175 -> $175 (flat) | $127.7 -> $146.8 (climbing) | Gradual convergence realistic |
| Peak oil | $198 (R1) | $184.9 (R4, with OPEC restriction) | Peak delayed and requires additional shock |
| OPEC defection effect | -$90 instant crash | -$37.8 (inertia dampened) | No more cliff edges |
| Gulf Gate opening | -$110 instant crash | -$40.4 (inertia dampened) | Gradual decline realistic |
| Full normalization | 1 round | 3-4 rounds | Matches physical oil market behavior |
| Demand destruction | Not visible | Weak but present | Improved but needs calibration |
| Nordostan enrichment | Dramatic (high peak price) | Moderate (lower peak, GDP decay) | More realistic — paradox exists but manageable |

---

## DESIGN HOLES IDENTIFIED

### HOLE 1: Demand Destruction Too Weak (CALIBRATE — HIGH PRIORITY)
**Issue:** GDP growth elasticity averages across all 21 countries equally. A $280B economy contracting has the same demand impact as a $0.3B economy contracting. Crisis state demand reduction requires formal crisis entry, which can take 3-4 rounds.
**Recommendation:** GDP-weighted demand elasticity. Add intermediate STRESSED demand reduction of -0.02 per major economy. Target behavior: sustained oil > $150 for 3+ rounds should produce visible demand reduction of 8-12%, not 4-5%.

### HOLE 2: Soft Cap Ceiling May Be Too Low (CALIBRATE)
**Issue:** Asymptotic maximum of ~$250 may not be sufficient for simultaneous Gulf Gate + Formosa + OPEC restriction scenario. Historical precedent (1979 oil crisis) suggests prices can double the pre-crisis level when multiple supply disruptions coincide.
**Recommendation:** Raise asymptote to ~$280 (`200 + 80 * (1 - exp(-(raw-200)/150))`).

### HOLE 3: Oil Revenue Decay with GDP Creates Double Punishment (DESIGN)
**Issue:** Oil revenue formula `price * resource_pct * GDP * 0.01` means sanctioned producers see oil revenue decline even when prices rise, because sanctions erode the GDP base. This may over-penalize oil-dependent sanctioned states.
**Recommendation:** Consider using STARTING GDP (or a floor of 80% of starting GDP) as the revenue base, reflecting that oil extraction infrastructure does not degrade as fast as the broader economy.

### HOLE 4: No Forward Contract / Hedging Mechanic (DESIGN)
**Issue:** Oil importers are fully exposed to spot price each round. In reality, major importers hedge 6-12 months forward, dampening the impact of price spikes. This makes the oil shock on GDP too responsive.
**Recommendation:** Not needed for SIM simplicity. The inertia model already partially captures this effect (price moves gradually, GDP impact follows price). No action needed.

### HOLE 5: OPEC Prisoner's Dilemma Has No Memory (DESIGN)
**Issue:** OPEC members defect/cooperate freely each round with no consequence. In reality, OPEC agreements create reputational costs for defection.
**Recommendation:** Track OPEC cooperation history. After 2+ rounds of cooperation, defection costs -0.5 stability (relationship damage with other OPEC members). After 2+ rounds of defection, return to cooperation provides +0.3 stability bonus. This creates the iterated game dynamic.

---

## VERDICT

**Overall Score: 8.5/10**

Cal-1 oil inertia model is validated. It produces:
1. Gradual price convergence (~3 rounds to reach equilibrium from any shock)
2. No single-round swings exceeding ~$47 (vs $100+ in TESTS2)
3. Symmetric dampening on both upward and downward movements
4. Proper interaction with OPEC decisions, chokepoint status, and sanctions

The 40/60 blend ratio feels correct — 60% toward equilibrium gives meaningful price movement each round while preventing whiplash. The soft cap functions but is unlikely to be tested hard in standard scenarios.

Demand destruction remains the weakest link. Oil-weighted GDP elasticity and intermediate stress demand reduction would complete the feedback loop and make sustained high oil prices self-correcting on a realistic timeline.
