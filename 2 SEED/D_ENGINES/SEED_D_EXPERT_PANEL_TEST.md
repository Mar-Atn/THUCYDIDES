# SEED D: EXPERT PANEL VALIDATION TEST
## Three-Expert AI Panel vs. 5 Extreme Scenarios
**Date:** 2026-03-28 | **Engine:** world_model_engine.py v3 | **Source:** SEED TESTS3 battery

---

## METHODOLOGY

For each scenario, I extract the **actual Round 4 state** from the test results, then manually trace through every check in `_expert_keynes()`, `_expert_clausewitz()`, and `_expert_machiavelli()` to determine:
1. Which checks fire (with specific trigger values)
2. What adjustments each expert produces
3. How the synthesis (majority rule) resolves agreements/disagreements
4. The net effect on key variables after the panel runs

The expert panel operates on **soft variables only**: `gdp_growth_rate`, `stability`, `political_support`, `momentum`, `inflation`, `military_production_efficiency`, `ai_rd_progress`, `nuclear_rd_progress`. Hard variables (GDP level, treasury, units, tech levels) cannot be directly adjusted, though some legacy checks (market panic, capital flight) do adjust GDP directly.

### Synthesis Rules (from engine lines 2031-2107):
- **Single expert**: applied at 50% weight
- **2+ experts agree on direction**: applied at average magnitude of agreeing experts
- **All disagree on direction**: flagged for moderator, NOT applied

### Bounding: All adjustments capped at +/-30% of current value

---

## SCENARIO 1: GULF GATE R4 — Oil at Peak, OPEC Restricts

### State at R4 (from TEST_3_FULL_RESULTS.md):

| Variable | Columbia | Cathay | Sarmatia | Solaria | Teutonia |
|----------|----------|--------|-----------|---------|----------|
| GDP | 269.2 | 211.8 | 10.2 | 12.5 | ~42 |
| Growth | -3.4% | +1.5% | ~-11% | +4% | ~-1.5% |
| Stability | ~6.2 | 8.0 | ~3.0 | 7.0 | 6.8 |
| Support | ~35% | ~65% | ~50% | ~70% | ~55% |
| Eco State | STRESSED | normal | crisis | normal | normal |
| Momentum | ~-0.5 | +0.3 | -2.5 | +0.3 | -0.3 |
| Oil Price | $184.9 (global) | — | — | — | — |
| Inflation | ~5% | ~1% | ~85% | ~2.5% | ~4% |
| War Tired | 1.6 | 0 | 4.2 | 0 | 0 |

**History (R1-R3):** Gulf Gate blocked since R0. Oil climbed $80 -> $128 -> $147 -> $152. R4 is when OPEC restricts (all "low"), pushing oil to $185. Columbia hit by oil shock + Persia war. Sarmatia declining under sanctions + war but oil revenue cushioning slightly. Solaria booming on oil windfall.

---

### KEYNES Assessment:

**Check: GDP trajectory declining 3+ rounds (growth > -1)?**
- Columbia: GDP declined R1-R3 (280 -> 282.6 -> 278.9 -> 269.2). rounds_declining = 2 (R2-R3). Does NOT fire (needs 3+). NO TRIGGER.
- Sarmatia: GDP declined R1-R3 (16.4 -> 13.5 -> 11.5 -> 10.2). rounds_declining = 3. growth = -11% (not > -1). Does NOT fire (growth already below -1). NO TRIGGER.

**Check: Stability declining 3+ rounds?**
- No country has stability declining for 3 consecutive rounds yet by R4. NO TRIGGER.

**Check 1: GDP growing during crisis/collapse?**
- Sarmatia in crisis with growth -11%. NOT growing. NO TRIGGER.
- No country in crisis with positive growth. NO TRIGGER.

**Check 2: Oil importer growing >2% with oil >$150?**
- Oil = $184.9 (> $150). Cathay growth +1.5% (NOT > 2%). NO TRIGGER.
- Columbia is oil PRODUCER (is_importer = False). NO TRIGGER.
- Teutonia: importer, growth -1.5% (not > 2%). NO TRIGGER.
- Bharata: importer, growth likely ~0-1% (not > 2%). NO TRIGGER.
- **FINDING: At $185 oil, no importer is growing >2%, so this check catches nothing. It has already been priced in by Pass 1.**

**Check 3: Oil producer NOT benefiting (oil >$120, resource_pct >20%, growth <1%)?**
- Sarmatia: oil_producer = True. Oil = $185 > $120. resource_pct = 0.40 (> 0.20). growth = -11% (< 1%). FIRES.
  - boost = min(2.0, 0.40 * 3) = min(2.0, 1.2) = **+1.2 to gdp_growth_rate**
  - Reason: "KEYNES: Sarmatia is a major oil producer (40% resources) with oil at $185 -- should be benefiting."
  - Confidence: medium
- Solaria: oil_producer = True. growth = +4% (NOT < 1%). NO TRIGGER.
- Persia: oil_producer = True. resource_pct = 0.35. growth likely very negative. FIRES.
  - boost = min(2.0, 0.35 * 3) = min(2.0, 1.05) = **+1.05 to gdp_growth_rate**

**Check 4: Inflation spiral (delta >20) without GDP consequence (growth >0)?**
- Sarmatia: inflation delta = 85 - 5 = 80 (> 20). But growth = -11% (NOT > 0). NO TRIGGER.
- No country has both high inflation AND positive growth. NO TRIGGER.

**Check 5: Major trading partner in crisis (weight >10%)?**
- Sarmatia is in crisis. Partners with weight > 0.10: likely Cathay, possibly Teutonia.
  - Cathay: momentum = +0.3 (> -1). FIRES. adjustment: momentum -0.5 for Cathay.
  - Teutonia: if weight > 0.10, FIRES. momentum -0.5 for Teutonia.

**Check 6: Printing money without sufficient inflation?**
- Sarmatia: printed ~8 coins, inf_delta = 80. Is 80 < 8*2=16? No (80 > 16). NO TRIGGER.
- Columbia: minimal printing at this stage. NO TRIGGER.

**Legacy: Market panic on crisis entry?**
- Sarmatia entered crisis in an earlier round, not this round. prev_state = crisis, current = crisis. NO TRIGGER (not a new transition).

**Legacy: Capital flight (stability < 3)?**
- Sarmatia: stability ~3.0. Is stability < 3? Borderline. If exactly 3.0, condition `< 3` = False. NO TRIGGER.
- If stability = 2.9 (plausible): flight = 10.2 * 0.01 (autocracy) = **-0.102 GDP**. FIRES.

**Legacy: Capital outflow (stability < 4)?**
- Sarmatia: stability ~3.0, < 4. And not < 3 (if exactly 3.0). flight = 10.2 * 0.01 = **-0.102 GDP**. FIRES (medium confidence).

**Legacy: Sanctions adaptation (>4 rounds)?**
- Sarmatia: sanctions_rounds by R4 = 4. Needs > 4. NO TRIGGER (exactly 4, not >4).

**Legacy: Tech breakthrough?**
- No country leveled up AI or nuclear this round. NO TRIGGER.

#### KEYNES R4 Adjustments Summary:
| Country | Variable | Amount | Reason |
|---------|----------|--------|--------|
| Sarmatia | gdp_growth_rate | +1.2 | Oil producer should benefit at $185 |
| Persia | gdp_growth_rate | +1.05 | Oil producer should benefit at $185 |
| Cathay | momentum | -0.5 | Sarmatia crisis contagion |
| Teutonia | momentum | -0.5 | Sarmatia crisis contagion (if weight >10%) |
| Sarmatia | gdp | -0.102 | Capital outflows (stability ~3.0) |

---

### CLAUSEWITZ Assessment:

**Check: Military trajectory declining 2+ rounds while at war?**
- Sarmatia: mil_traj data needed. If Sarmatia has been losing units, FIRES. Assuming no explicit losses in Gulf Gate test (that test focuses on oil, not combat): likely NO TRIGGER.
- Columbia: at war (Persia). No unit losses in oil scenario. NO TRIGGER.

**Check 1: At war with war_tiredness >3 but stability >6?**
- Sarmatia: war_tired = 4.2, stability = 3.0. Stability NOT > 6. NO TRIGGER.
- Columbia: war_tired = 1.6, NOT > 3. NO TRIGGER.

**Check 2: Columbia overstretch (3+ theaters)?**
- Columbia in Gulf Gate scenario: Persia theater only (1 theater). NO TRIGGER.

**Check 3: Country in crisis producing military?**
- Sarmatia: in crisis. FIRES.
  - adjustment: military_production_efficiency = **-0.3** (crisis penalty)
  - Confidence: high

**Check 4: Prolonged blockade (3+ rounds)?**
- Gulf Gate is a GROUND blockade by Persia, not a naval blockade by a player. The active_blockades check looks for controller == cid. Persia controls Gulf Gate. If Persia has stability > 4 (it does not -- Persia ~2.0-3.0), NO TRIGGER. Likely NO TRIGGER.

**Legacy: War loss confidence shock?**
- No combat results in this round showing total defeat. NO TRIGGER.

**Legacy: Ceasefire rally?**
- No ceasefire this round. NO TRIGGER.

**Legacy: Brain drain (democracy in crisis)?**
- Sarmatia: autocracy, not democracy. NO TRIGGER.
- No democracy is in crisis. NO TRIGGER.

#### CLAUSEWITZ R4 Adjustments Summary:
| Country | Variable | Amount | Reason |
|---------|----------|--------|--------|
| Sarmatia | military_production_efficiency | -0.3 | In crisis, production degraded |

---

### MACHIAVELLI Assessment:

**Check 1: Election approaching?**
- Columbia: round_num = 4. Code checks `round_num in (1, 4)`. R4 = YES (before R5 presidential). elections_soon = True.
- Support trajectory: if declining trend, amplified anxiety fires.
  - Columbia support declining from ~38 -> ~35 over 3 rounds. trend = 'falling'. avg_change ~ -1.0.
  - FIRES: political_support adjustment = -1.0 * 0.5 = **-0.5**
  - Reason: "MACHIAVELLI: columbia support trending down (-1.0/round) into election -- panic among allies."
- GDP growth < 0 and elections_soon: Columbia growth = -3.4%. FIRES.
  - adjustment: political_support **-3.0**
  - Reason: "MACHIAVELLI: columbia has elections approaching with negative GDP growth -- voter anger amplified."
- Oil > $150 and not oil_producer and elections_soon: Columbia IS oil_producer. NO TRIGGER.

**Check 2: Ceasefire achieved?**
- No ceasefire. NO TRIGGER.

**Check 3: Autocracy under pressure (stability <3, support >50)?**
- Sarmatia: stability ~3.0, support ~50%. If stability = 2.9 and support = 51: FIRES.
  - adjustment: political_support **-5.0**
  - Borderline -- depends on exact values.

**Check 4: Democracy in crisis with support >45?**
- No democracy is in crisis at R4. NO TRIGGER.

**Check 5: War for 4+ rounds with no progress (war_tiredness >3, support >40)?**
- Sarmatia: war_tired = 4.2 (> 3), support ~50 (> 40). FIRES.
  - adjustment: political_support **-2.0**
  - Reason: "MACHIAVELLI: sarmatia war fatigue at 4.2 -- when does this end?"

**Legacy: Rally around the flag?**
- Columbia at war with Persia. war_duration = R4 - R0 = 4. rally = max(10 - 4*3, 0) = max(-2, 0) = 0. NO RALLY.
- Sarmatia at war. war_duration = R4 + 4 (pre-sim) = 8. rally = max(10 - 8*3, 0) = 0. NO RALLY.

#### MACHIAVELLI R4 Adjustments Summary:
| Country | Variable | Amount | Reason |
|---------|----------|--------|--------|
| Columbia | political_support | -0.5 | Support declining into election |
| Columbia | political_support | -3.0 | Negative GDP + elections |
| Sarmatia | political_support | -5.0 | Autocracy cracking (borderline) |
| Sarmatia | political_support | -2.0 | War fatigue at 4.2 |

---

### SYNTHESIS:

**Columbia political_support:** Only MACHIAVELLI adjusts (-0.5 and -3.0). Single expert -> applied at 50%.
- Combined Machiavelli opinion on columbia.political_support: two entries from same expert, grouped as one variable target. Total opinions = 2, both from MACHIAVELLI (counted as one expert). Since only one expert touches this variable: **single expert rule, x0.5**.
- Net: (-3.5) * 0.5 = **-1.75 to political_support**

**Sarmatia gdp_growth_rate:** Only KEYNES adjusts (+1.2). Single expert -> applied at 50%.
- Net: +1.2 * 0.5 = **+0.6 to gdp_growth_rate**

**Sarmatia political_support:** Only MACHIAVELLI adjusts (-5.0, -2.0). Single expert -> x0.5.
- Net: (-7.0) * 0.5 = **-3.5 to political_support** (bounded at 30% of current ~50 = max -15, so -3.5 is within bounds)

**Sarmatia military_production_efficiency:** Only CLAUSEWITZ adjusts (-0.3). Single expert -> x0.5.
- Net: -0.3 * 0.5 = **-0.15**

**Cathay momentum:** Only KEYNES adjusts (-0.5). Single expert -> x0.5.
- Net: -0.5 * 0.5 = **-0.25**

**No 2+ expert agreements.** All adjustments are single-expert, applied at half weight.

### Net Effect on Key Variables:

| Variable | Before Panel | After Panel | Change | Expert(s) |
|----------|-------------|-------------|--------|-----------|
| Columbia support | 35.0% | 33.25% | -1.75 | MACHIAVELLI (solo x0.5) |
| Sarmatia growth | -11.0% | -10.4% | +0.6 | KEYNES (solo x0.5) |
| Sarmatia support | 50% | 46.5% | -3.5 | MACHIAVELLI (solo x0.5) |
| Sarmatia mil_prod_eff | 1.0 | 0.85 | -0.15 | CLAUSEWITZ (solo x0.5) |
| Cathay momentum | +0.30 | +0.05 | -0.25 | KEYNES (solo x0.5) |

### VERDICT: Moderate Value

- **Pass 1 would have been somewhat unrealistic** for Sarmatia: an oil producer at $185 oil shrinking at -11% without any GDP offset is harsh. The +0.6% Keynes boost is justified but modest.
- **Panel correctly identifies** Columbia pre-election vulnerability (Machiavelli) and Sarmatia military production degradation (Clausewitz).
- **Gap identified:** No expert catches the Sarmatia Enrichment Paradox directly. Keynes gives a generic oil-producer boost, but does not reason about the specific paradox that Sarmatia's own war is driving the oil price that benefits it.
- **No overcorrection.** All adjustments are sensible and small (thanks to single-expert 0.5x rule).
- **Missing:** No expert adjusts Solaria (booming on oil windfall) or flags the oil-dependent economy asymmetry.

---

## SCENARIO 2: FORMOSA R4 — Semiconductor Disruption Active, Crisis Cascade

### State at R4 (from TEST_2_FULL_RESULTS.md):

| Variable | Columbia | Cathay | Formosa | Yamato | Hanguk |
|----------|----------|--------|---------|--------|--------|
| GDP | 229.5 (post-panic) | 216.7 | 7.80 | 37.9 | 15.8 |
| Growth | -9.12% | +1.97% | -3.7% | -6.76% | -7.1% |
| Stability | 5.20 | 8.0 | 5.90 | 7.10 | 4.90 |
| Support | ~30% | ~65% | ~45% | ~55% | ~40% |
| Eco State | **CRISIS** | normal | stressed | **STRESSED** | **STRESSED** |
| Momentum | -1.85 | +0.30 | -1.35 | -1.35 | -1.50 |
| Oil Price | $138.9 (global) | — | — | — | — |
| Semi Severity | 0.7 | 0.7 | n/a (producer) | 0.7 | 0.7 |
| War Tired | ~1.6 | 0 | 0 | 0 | 0 |

**History (R1-R3):** Cathay blockaded Formosa at R2. Semiconductor disruption ramped 0.3 -> 0.5 -> 0.7. Columbia GDP crashed 280 -> 288 -> 282 -> 266 -> 242 (then panic to 229.5). Columbia entered CRISIS this round. Midterm election lost at R2. Cathay growing steadily despite self-imposed blockade.

---

### KEYNES Assessment:

**Trajectory: GDP declining 3+ rounds?**
- Columbia: GDP declining R2 -> R3 -> R4 (288 -> 282 -> 266 -> 242). rounds_declining = 3. growth = -9.12% (not > -1). Does NOT fire (already below -1 threshold). NO TRIGGER.
- Yamato: declining 3 rounds (43.4 -> 42.5 -> 40.6 -> 37.9). rounds_declining = 3. growth = -6.76% (not > -1). NO TRIGGER.
- Hanguk: declining 3 rounds. growth = -7.1% (not > -1). NO TRIGGER.

**Trajectory: Stability declining 3+ rounds?**
- Columbia: stability ~7.0 -> 6.95 -> 6.68 -> 6.15 -> 5.20. rounds_declining = 4, trend = falling. FIRES.
  - momentum adjustment: **-0.5**
  - Reason: "KEYNES: columbia stability declining 4 rounds -- investor confidence eroding."

**Check 1: GDP growing during crisis?**
- Columbia: in CRISIS, growth = -9.12%. NOT growing. NO TRIGGER.

**Check 2: Oil importer growing >2% with oil >$150?**
- Oil = $138.9. NOT > $150. NO TRIGGER for any country.

**Check 3: Oil producer NOT benefiting?**
- Oil = $138.9 > $120. Sarmatia: resource_pct = 0.40 (>0.20), growth likely negative (<1%). FIRES: +1.2.
- Columbia: IS oil_producer with resource_pct = 0.08. resource_pct NOT > 0.20. NO TRIGGER.

**Check 4: Inflation spiral without GDP consequence?**
- No country has both inflation delta > 20 AND positive growth. NO TRIGGER.

**Check 5: Major trading partner in crisis?**
- Columbia (GDP 229.5 > 30) is in CRISIS. Partners with weight > 0.10:
  - Cathay: weight likely ~12-15%. momentum = +0.30 (> -1). FIRES: **momentum -0.5 for Cathay**.
  - Yamato: weight likely ~8-10%. Borderline. If > 10%: FIRES.
  - Teutonia: weight likely > 10%. FIRES: momentum -0.5.

**Check 6: Printing money without inflation?**
- Columbia: printed ~13 coins (market panic), inf_delta small. If printed > 0 and inf_delta < printed*2: need to check. Columbia inf_delta = ~2-3, printed ~1 (pre-panic). Borderline.

**Legacy: Market panic on crisis entry?**
- Columbia entered crisis THIS round (prev_state = normal/stressed, current = crisis). FIRES.
  - gdp adjustment: -229.5 * 0.05 = **-11.475 GDP** (but wait -- this was already applied in the test results showing 241.6 -> 229.5. So it already fired. The test results INCLUDE Pass 2.)
  - Since the test already accounts for this, it is NOT double-counted here.

**Legacy: Capital flight (stability <3 or <4)?**
- Columbia stability = 5.20. NOT < 4. NO TRIGGER.
- Hanguk stability = 4.90. NOT < 4. NO TRIGGER.

**Legacy: Sanctions adaptation?**
- Sarmatia: sanctions_rounds ~4. NOT > 4. NO TRIGGER.

#### KEYNES R4 Adjustments Summary:
| Country | Variable | Amount | Reason |
|---------|----------|--------|--------|
| Columbia | momentum | -0.5 | Stability declining 4 rounds |
| Cathay | momentum | -0.5 | Columbia crisis contagion |
| Teutonia | momentum | -0.5 | Columbia crisis contagion |
| Sarmatia | gdp_growth_rate | +1.2 | Oil producer benefit at $139 |

---

### CLAUSEWITZ Assessment:

**Military trajectory declining 2+ rounds?**
- No country losing units in this scenario. NO TRIGGER.

**Check 1: War tiredness >3, stability >6?**
- Columbia: war_tired = 1.6, NOT > 3. NO TRIGGER.
- Sarmatia: war_tired = 4.2+, stability ~3.0, NOT > 6. NO TRIGGER.

**Check 2: Columbia overstretch (3+ theaters)?**
- Columbia in Persia + Pacific (Formosa response). 2 theaters. NOT >= 3. NO TRIGGER.
- BUT if Columbia also has forces near Ruthenia (aid/staging), could be 3. Borderline.

**Check 3: Crisis military production?**
- Columbia in CRISIS. FIRES: **military_production_efficiency -0.3** (high confidence).
- Yamato in STRESSED (not crisis). NO TRIGGER.

**Check 4: Prolonged blockade?**
- Cathay blocking Formosa: duration = 3 rounds (R2-R4). duration >= 3 AND stability > 4: Cathay stability = 8.0 > 4. FIRES.
  - stability adjustment for Cathay: **-0.2**
  - Reason: "CLAUSEWITZ: cathay maintaining blockade at taiwan_strait for 3 rounds -- military fatigue."
  - Confidence: low

**Legacy: Brain drain (democracy in crisis)?**
- Columbia: democracy + crisis. FIRES.
  - ai_rd_progress: **-0.02**
  - Reason: "CLAUSEWITZ: Brain drain from Columbia as skilled workers emigrate."
  - Confidence: medium

#### CLAUSEWITZ R4 Adjustments Summary:
| Country | Variable | Amount | Reason |
|---------|----------|--------|--------|
| Columbia | mil_prod_eff | -0.3 | In crisis, production degraded |
| Columbia | ai_rd_progress | -0.02 | Brain drain (democracy in crisis) |
| Cathay | stability | -0.2 | Prolonged blockade fatigue (3 rounds) |

---

### MACHIAVELLI Assessment:

**Check 1: Election approaching?**
- Columbia: round_num = 4. Code checks `round_num in (1, 4)`. YES. elections_soon = True.
- Support trajectory: Columbia support declining ~38 -> ~30 over 4 rounds. trend = 'falling'.
  - FIRES: **political_support -1.5** (avg_change ~-3.0 * 0.5, bounded)
- GDP growth < 0 and elections_soon: Columbia growth -9.12%. FIRES: **political_support -3.0**
- Oil > $150 and elections_soon: Oil = $138.9, NOT > $150. NO TRIGGER.

**Check 3: Autocracy under pressure?**
- No autocracy with stability < 3 AND support > 50 at this point. NO TRIGGER.

**Check 4: Democracy in crisis with support >45?**
- Columbia: democracy + CRISIS + support ~30%. NOT > 45. NO TRIGGER.
- (If support were above 45 somehow, this would fire strongly.)

**Check 5: War fatigue (war_tired >3, support >40)?**
- Sarmatia: war_tired > 3, support ~50 (> 40). FIRES: **political_support -2.0** for Sarmatia.
- Columbia: war_tired = 1.6, NOT > 3. NO TRIGGER.

**Legacy: Rally?**
- Columbia war duration = 4. rally = max(10-12, 0) = 0. NO RALLY.

#### MACHIAVELLI R4 Adjustments Summary:
| Country | Variable | Amount | Reason |
|---------|----------|--------|--------|
| Columbia | political_support | -1.5 | Support declining into election |
| Columbia | political_support | -3.0 | Negative GDP + elections |
| Sarmatia | political_support | -2.0 | War fatigue at 4.2 |

---

### SYNTHESIS:

**Columbia momentum:** KEYNES (-0.5) solo. -> **-0.25** applied.

**Columbia political_support:** MACHIAVELLI (-1.5, -3.0) solo. -> **-2.25** applied ((-4.5) * 0.5).

**Columbia mil_prod_eff:** CLAUSEWITZ (-0.3) solo. -> **-0.15** applied.

**Columbia ai_rd_progress:** CLAUSEWITZ (-0.02) solo. -> **-0.01** applied.

**Cathay momentum:** KEYNES (-0.5) solo. -> **-0.25** applied.

**Cathay stability:** CLAUSEWITZ (-0.2) solo. -> **-0.10** applied.

**Sarmatia gdp_growth_rate:** KEYNES (+1.2) solo. -> **+0.6** applied.

**Sarmatia political_support:** MACHIAVELLI (-2.0) solo. -> **-1.0** applied.

**No 2+ expert agreements on any variable.** All single-expert adjustments at 0.5x.

### Net Effect:

| Variable | Before Panel | After Panel | Change | Expert(s) |
|----------|-------------|-------------|--------|-----------|
| Columbia momentum | -1.85 | -2.10 | -0.25 | KEYNES solo |
| Columbia support | 30% | 27.75% | -2.25 | MACHIAVELLI solo |
| Columbia mil_prod_eff | 1.0 | 0.85 | -0.15 | CLAUSEWITZ solo |
| Columbia ai_rd_progress | 0.80 | 0.79 | -0.01 | CLAUSEWITZ solo |
| Cathay momentum | +0.30 | +0.05 | -0.25 | KEYNES solo |
| Cathay stability | 8.0 | 7.90 | -0.10 | CLAUSEWITZ solo |
| Sarmatia growth | ~-11% | ~-10.4% | +0.6 | KEYNES solo |
| Sarmatia support | ~50% | ~49% | -1.0 | MACHIAVELLI solo |

### VERDICT: Good Value — Panel Catches What Formulas Miss

- **Brain drain (Clausewitz)** is a genuine insight. Columbia in economic crisis with AI L3 at 0.80 progress should be losing talent. The -0.01 ai_rd_progress adjustment is small but meaningful over multiple rounds.
- **Cathay blockade fatigue (Clausewitz)** is a real-world concern. Maintaining a naval blockade for 3+ rounds should stress Cathay's military posture. But at -0.10 stability (from 8.0 to 7.9) after 0.5x, the effect is negligible.
- **Columbia pre-election panic (Machiavelli)** is well-calibrated. The -2.25 support penalty amplifies what the formula already captures.
- **GAP: No expert reasons about the semiconductor asymmetry.** Cathay is growing while Columbia collapses -- this strategic insight (blockade is asymmetric warfare) is not captured. Keynes only checks standard oil/inflation/GDP patterns.
- **GAP: Formosa itself gets zero attention** despite being the blockaded country. No expert adjusts Formosa's variables.

---

## SCENARIO 3: STABILITY R4 — War Countries Declining, Sarmatia vs Ruthenia Asymmetry

### State at R4 (from TEST_5_FULL_RESULTS.md):

| Variable | Ruthenia | Sarmatia | Persia | Columbia | Cathay |
|----------|-----------|-----------|--------|----------|--------|
| GDP | ~1.6 | ~9.5 | ~2.5 | ~278 | ~210 |
| Growth | ~-8% | ~-15% | ~-12% | ~+1.5% | ~+3.5% |
| Stability | 2.39 | 2.11 | 1.00 | 6.9 | 8.0 |
| Support | ~35% | ~40% | ~20% | ~38% | ~65% |
| Eco State | crisis | crisis | collapse | normal | normal |
| Momentum | -2.0 | -3.0 | -3.0 | +0.15 | +0.30 |
| Oil Price | $151 (global) | — | — | — | — |
| War Tired | 4.4 (Ruthenia) | 4.2 | 1.4 | 1.6 | 0 |

**History (R1-R3):** Pure formula validation. Ruthenia collapse driven by military costs 8x revenue. Sarmatia collapse driven by sanctions + deficit. Persia collapsed by R3 (defender under L3 sanctions). Both Ruthenia and Sarmatia at stability floor approaching. Cal-4 cap holds but cannot prevent structural death spiral.

---

### KEYNES Assessment:

**Trajectory: GDP declining 3+ rounds?**
- Ruthenia: GDP declining every round (2.2 -> 2.16 -> 2.12 -> 2.0 -> 1.6). rounds_declining = 4. growth = -8% (not > -1). NO TRIGGER (already severely negative).
- Sarmatia: Same pattern, growth -15%. NO TRIGGER.
- Persia: Same. NO TRIGGER.

**Trajectory: Stability declining 3+ rounds?**
- Ruthenia: stab 5.0 -> 4.47 -> 3.53 -> 2.39. rounds_declining = 3, trend = 'falling'. FIRES.
  - momentum: **-0.5** for Ruthenia.
- Sarmatia: stab 5.0 -> 4.14 -> 3.20 -> 2.11. rounds_declining = 3, trend = 'falling'. FIRES.
  - momentum: **-0.5** for Sarmatia.

**Check 1: GDP growing during crisis/collapse?**
- No crisis/collapse country has positive growth. NO TRIGGER.

**Check 2: Oil importer growing >2% with oil >$150?**
- Oil = $151 (> $150). Cathay: importer, growth +3.5% (> 2%). FIRES.
  - penalty = min(3.5 - 0.5, 3.0) = min(3.0, 3.0) = **-3.0 to gdp_growth_rate**
  - Reason: "KEYNES: cathay growing 3.5% with oil at $151 -- oil shock drag."
  - This is the FIRST time this check fires across all scenarios. Significant.

**Check 3: Oil producer NOT benefiting?**
- Sarmatia: producer, resource_pct = 0.40, growth = -15% (<1%). FIRES: +1.2.
- Persia: producer, resource_pct = 0.35, growth = -12% (<1%). FIRES: +1.05.
- Solaria: growth likely positive. NO TRIGGER.

**Check 4: Inflation spiral without growth?**
- Ruthenia: inflation delta very high (>>20), growth -8% (not > 0). NO TRIGGER.
- Sarmatia: same pattern. NO TRIGGER.

**Check 5: Major partner in crisis?**
- Sarmatia is in crisis. Cathay trade weight > 10%? Probably yes. FIRES: momentum -0.5 for Cathay.
- Ruthenia is in crisis (GDP ~1.6, NOT > 30, so NOT a major economy). NO contagion trigger (below MAJOR_ECONOMY_THRESHOLD of 30).

**Legacy: Capital flight (stability <3)?**
- Ruthenia: stability 2.39 < 3, democracy, eco_state = crisis (not collapse). FIRES.
  - flight = 1.6 * 0.08 = **-0.128 GDP** (democracy rate)
- Sarmatia: stability 2.11 < 3, autocracy. FIRES.
  - flight = 9.5 * 0.03 = **-0.285 GDP** (autocracy rate)
- Persia: stability 1.0, collapse (eco_state = collapse). Condition: `stability < 3 AND state != 'collapse'`. state IS collapse. NO TRIGGER.

**Legacy: Sanctions adaptation >4 rounds?**
- Sarmatia: sanctions_rounds = 4 (not > 4). NO TRIGGER.

#### KEYNES R4 Adjustments Summary:
| Country | Variable | Amount | Reason |
|---------|----------|--------|--------|
| Ruthenia | momentum | -0.5 | Stability declining 3 rounds |
| Sarmatia | momentum | -0.5 | Stability declining 3 rounds |
| Cathay | gdp_growth_rate | -3.0 | Growing 3.5% at $151 oil (importer) |
| Cathay | momentum | -0.5 | Sarmatia crisis contagion |
| Sarmatia | gdp_growth_rate | +1.2 | Oil producer should benefit |
| Persia | gdp_growth_rate | +1.05 | Oil producer should benefit |
| Ruthenia | gdp | -0.128 | Capital flight (democracy, stab 2.39) |
| Sarmatia | gdp | -0.285 | Capital flight (autocracy, stab 2.11) |

---

### CLAUSEWITZ Assessment:

**Military declining 2+ rounds while at war?**
- If either Ruthenia or Sarmatia lost units: likely NO explicit losses in stability test (pure formula run, no combat). NO TRIGGER.

**Check 1: War tired >3, stability >6?**
- Ruthenia: war_tired = 4.4 (> 3), stability = 2.39, NOT > 6. NO TRIGGER.
- Sarmatia: war_tired = 4.2 (> 3), stability = 2.11, NOT > 6. NO TRIGGER.
- **FINDING: This check is useless for countries deep in crisis.** By the time war tiredness is high enough, stability has already crashed below 6. The check only catches countries that are "strangely stable despite long wars" -- a narrow and unlikely scenario.

**Check 3: Crisis military production?**
- Ruthenia: in crisis. FIRES: **mil_prod_eff -0.3** (high confidence).
- Sarmatia: in crisis. FIRES: **mil_prod_eff -0.3** (high confidence).
- Persia: in collapse. FIRES: **mil_prod_eff -0.5** (high confidence).

**Legacy: Brain drain?**
- Ruthenia: democracy + crisis. FIRES: **ai_rd_progress -0.02**.

#### CLAUSEWITZ R4 Adjustments Summary:
| Country | Variable | Amount | Reason |
|---------|----------|--------|--------|
| Ruthenia | mil_prod_eff | -0.3 | In crisis |
| Sarmatia | mil_prod_eff | -0.3 | In crisis |
| Persia | mil_prod_eff | -0.5 | In collapse |
| Ruthenia | ai_rd_progress | -0.02 | Brain drain |

---

### MACHIAVELLI Assessment:

**Check 1: Election approaching?**
- Columbia: round_num = 4, yes (before R5 presidential). elections_soon = True.
  - GDP growth +1.5% (> 0). GDP < 0 condition: NO. NO voter anger trigger.
  - Oil $151 > $150, but Columbia IS oil_producer. NO TRIGGER for oil election pressure.
  - Support trajectory: if stable/rising, no panic trigger.

**Check 3: Autocracy under pressure (stability <3, support >50)?**
- Sarmatia: stability 2.11 < 3, support ~40%. NOT > 50. NO TRIGGER.

**Check 4: Democracy in crisis with support >45?**
- Ruthenia: democracy + crisis + support ~35%. NOT > 45. NO TRIGGER.

**Check 5: War fatigue (war_tired >3, support >40)?**
- Ruthenia: war_tired 4.4 > 3, support ~35%. NOT > 40. NO TRIGGER.
- Sarmatia: war_tired 4.2 > 3, support ~40%. BORDERLINE. If exactly 40: `> 40` = False. NO TRIGGER.
- **FINDING: By the time countries are deeply in crisis, their support has already dropped below 40, making this check irrelevant. War fatigue check only fires for countries not yet deeply damaged.**

**Legacy: Rally?**
- War durations too long for any rally effect. NO TRIGGER.

#### MACHIAVELLI R4 Adjustments Summary:
| Country | Variable | Amount | Reason |
|---------|----------|--------|--------|
| (none) | — | — | All checks fail for crisis countries |

---

### SYNTHESIS:

**Cathay gdp_growth_rate:** KEYNES (-3.0) solo. -> **-1.5** applied (bounded: 30% of 3.5 = 1.05, so actually capped at -1.05).
Actually: bounded at 30% of current value. Current growth_rate = 3.5%. max_delta = 3.5 * 0.30 = 1.05. bounded_amount = max(-1.05, min(1.05, -1.5)) = -1.05. Applied: **-1.05**.

**Cathay momentum:** KEYNES (-0.5) solo. -> **-0.25** applied.

**Ruthenia momentum:** KEYNES (-0.5) solo. -> **-0.25** applied.

**Sarmatia momentum:** KEYNES (-0.5) solo. -> **-0.25** applied.

**Sarmatia gdp_growth_rate:** KEYNES (+1.2) solo. -> **+0.6** applied. But bounded: 30% of |-15%| = 4.5. +0.6 within bounds. OK.

**Ruthenia mil_prod_eff:** CLAUSEWITZ (-0.3) solo. -> **-0.15** applied.

**Sarmatia mil_prod_eff:** CLAUSEWITZ (-0.3) solo. -> **-0.15** applied.

**Persia mil_prod_eff:** CLAUSEWITZ (-0.5) solo. -> **-0.25** applied.

**Ruthenia ai_rd_progress:** CLAUSEWITZ (-0.02) solo. -> **-0.01** applied.

**Ruthenia gdp:** KEYNES (-0.128) solo -> **-0.064** applied. BUT: GDP is a HARD VARIABLE. The apply_bounded_adjustment function checks `if variable in self.HARD_VARIABLES` and rejects it. **REJECTED.**

**Sarmatia gdp:** Same -- HARD VARIABLE. **REJECTED.**

Note: The capital flight adjustments targeting 'gdp' directly will be REJECTED by the engine because GDP is a hard variable. This is a **design inconsistency**: the legacy capital flight code generates adjustments targeting 'gdp', but the soft/hard variable filter blocks them. The capital flight effect is therefore **non-functional** in the current code.

### Net Effect:

| Variable | Before Panel | After Panel | Change | Expert(s) |
|----------|-------------|-------------|--------|-----------|
| Cathay growth_rate | +3.5% | +2.45% | -1.05 | KEYNES solo (bounded) |
| Cathay momentum | +0.30 | +0.05 | -0.25 | KEYNES solo |
| Ruthenia momentum | -2.0 | -2.25 | -0.25 | KEYNES solo |
| Sarmatia momentum | -3.0 | -3.25 | -0.25 | KEYNES solo |
| Sarmatia growth | -15% | -14.4% | +0.6 | KEYNES solo |
| Ruthenia mil_prod_eff | 1.0 | 0.85 | -0.15 | CLAUSEWITZ solo |
| Sarmatia mil_prod_eff | 1.0 | 0.85 | -0.15 | CLAUSEWITZ solo |
| Persia mil_prod_eff | 1.0 | 0.75 | -0.25 | CLAUSEWITZ solo |
| Ruthenia gdp | 1.6 | 1.6 | 0 | REJECTED (hard var) |
| Sarmatia gdp | 9.5 | 9.5 | 0 | REJECTED (hard var) |

### VERDICT: Mixed Value — Key Bug Found

- **Cathay oil shock drag (-1.05% growth)** is the panel's best contribution. At $151 oil, Cathay growing 3.5% is implausible for a major oil importer. This is a genuine catch.
- **Military production degradation** for crisis countries is logical and well-calibrated.
- **CRITICAL BUG: Capital flight adjustments target 'gdp' (hard variable) and are silently rejected.** The legacy capital flight logic produces adjustments that the soft/hard filter blocks. This means capital flight NEVER actually applies in the current code. This is a significant gap.
- **Machiavelli produces ZERO adjustments** when countries are deeply in crisis. All thresholds (support >45 for democracy crisis, support >40 for war fatigue) are already blown past. The expert is blind to countries in extremis.
- **Overcorrection concern:** Reducing Ruthenia momentum from -2.0 to -2.25 when the country is already at stability 2.39 is piling on. The formula is already producing collapse; the panel accelerates it slightly without adding insight.

---

## SCENARIO 4: COLUMBIA OVERSTRETCH R4 — Persia + Choson + Election

### State at R4 (from TEST_7_FULL_RESULTS.md):

| Variable | Columbia |
|----------|----------|
| GDP | 255.13 |
| Growth | -1.07% (crisis multiplier dampened from -2.13% raw) |
| Stability | 4.53 |
| Support | 25.14% |
| Eco State | **CRISIS** (crisis_rounds = 1) |
| Momentum | -1.65 |
| Oil Price | $126.7 |
| Inflation | 57.95% |
| War Tired | 1.60 |
| Treasury | 0 |
| Debt Burden | 43.55 |
| Military | 64 units (no production possible) |

**History (R1-R3):** Dealer incapacitated R1. Treasury depleted R1 (structural deficit). Money printing started R2. Midterms lost R2. Entered CRISIS R3 (market panic hit -5% GDP). Inflation spiraling (3.5% -> 3.82% -> 20.82% -> 38.37% -> 57.95%). Debt burden ballooning (5 -> 12.67 -> 21.44 -> 31.69 -> 43.55). Choson crisis R3 forced military rebalancing.

---

### KEYNES Assessment:

**Trajectory: GDP declining 3+ rounds?**
- Columbia: 280 -> 276.3 -> 274.1 -> 257.9 -> 255.1. rounds_declining = 4. growth = -1.07% (not > -1). Borderline. -1.07 < -1, so condition `growth > -1` = False. NO TRIGGER.

**Trajectory: Stability declining 3+ rounds?**
- Columbia: 7.0 -> 6.91 -> 6.26 -> 5.40 -> 4.53. rounds_declining = 4, trend = 'falling'. FIRES.
  - momentum: **-0.5**

**Check 1: GDP growing during crisis?**
- Columbia: CRISIS, growth = -1.07%. NOT growing. NO TRIGGER.

**Check 2: Oil importer growing >2% with oil >$150?**
- Oil = $126.7, NOT > $150. NO TRIGGER.

**Check 3: Oil producer NOT benefiting?**
- Oil = $126.7 > $120. Columbia: resource_pct = 0.08, NOT > 0.20. NO TRIGGER.
- Sarmatia/Persia/Solaria: would fire separately but not the focus here.

**Check 4: Inflation spiral without GDP consequence?**
- Columbia: inf_delta = 57.95 - 3.5 = 54.45 (> 20). growth = -1.07% (NOT > 0). NO TRIGGER.
- **FINDING: This check requires BOTH high inflation AND positive growth. Since inflation and GDP contraction are correlated, this check almost never fires. It is poorly designed.**

**Check 5: Major partner in crisis?**
- Columbia itself is in crisis. Its partners check if COLUMBIA is in crisis and apply contagion. The check is FROM partner perspective, not Columbia looking outward.
- Cathay: Columbia in crisis, trade weight > 10%. momentum = +0.30 (> -1). FIRES: momentum -0.5 for Cathay.

**Check 6: Money printing without inflation?**
- Columbia: printed ~79 coins this round. inf_delta = 54.45. Is 54.45 < 79 * 2 = 158? YES. FIRES.
  - inflation adjustment: 79 * 1.5 = **+118.5**
  - But bounded at 30% of current inflation (57.95 * 0.3 = 17.39). So bounded: **+17.39 to inflation**.
  - Confidence: low
  - **This is a MASSIVE false positive.** The check says "printed 79 coins but inflation only +54% -- should be higher." But inflation IS responding -- it went from 38% to 58% this round. The check's threshold (inf_delta < printed * 2) is comparing lifetime delta against single-round printing, which is meaningless. At high printing rates, this always fires.

**Legacy: Market panic?**
- Columbia entered crisis last round (R3), not this round. prev_state = crisis, current = crisis. NO TRIGGER (not a new transition).

**Legacy: Capital flight (stability <4)?**
- Columbia: stability 4.53, NOT < 4. NO TRIGGER.
- Stability 4.53 < 4? No. But < 5? Not checked. Stability at 4.53 is between thresholds.

#### KEYNES R4 Adjustments Summary:
| Country | Variable | Amount | Reason |
|---------|----------|--------|--------|
| Columbia | momentum | -0.5 | Stability declining 4 rounds |
| Columbia | inflation | +118.5 (bounded to +17.39) | Printing vs inflation gap (FALSE POSITIVE) |
| Cathay | momentum | -0.5 | Columbia crisis contagion |

---

### CLAUSEWITZ Assessment:

**Check 2: Columbia overstretch (3+ theaters)?**
- Columbia forces in: Persia/Gulf (mashriq), Pacific staging for Choson (if classified as pacific), plus home. Need to check deployment zones.
- Persia theater: YES (gulf/persia zones). Pacific: if TA deployed to Yamato (Choson deterrence). Home: always.
- If 3 theaters AND stability > 5: stability = 4.53, NOT > 5. Condition is `stability > 5`: NO TRIGGER.
- **FINDING: The overstretch check requires stability > 5, but by the time Columbia is overstretched, stability has already dropped. Same problem as Clausewitz Check 1.**

**Check 3: Crisis military production?**
- Columbia in CRISIS. FIRES: **mil_prod_eff -0.3** (high confidence).

**Legacy: Brain drain (democracy in crisis)?**
- Columbia: democracy + crisis. FIRES: **ai_rd_progress -0.02**.

#### CLAUSEWITZ R4 Adjustments Summary:
| Country | Variable | Amount | Reason |
|---------|----------|--------|--------|
| Columbia | mil_prod_eff | -0.3 | In crisis |
| Columbia | ai_rd_progress | -0.02 | Brain drain |

---

### MACHIAVELLI Assessment:

**Check 1: Election approaching?**
- Columbia: round_num = 4. YES (before R5 presidential). elections_soon = True.
- Support trajectory: Columbia support declining 38 -> 40.4 (rally) -> 40.78 -> 34.57 -> 25.14. Recent trend = falling.
  - If avg_change ~ -5.0 (steep decline): FIRES: **political_support -5.0 * 0.5 = -2.5**
- GDP growth < 0 and elections_soon: growth = -1.07%. FIRES: **political_support -3.0**
- Oil > $150 and elections_soon: $126.7, NOT > $150. NO TRIGGER.

**Check 4: Democracy in crisis with support >45?**
- Columbia: democracy + CRISIS + support = 25.14%. NOT > 45. NO TRIGGER.

**Check 5: War fatigue (war_tired >3, support >40)?**
- Columbia: war_tired = 1.60, NOT > 3. NO TRIGGER.

**Legacy: Rally?**
- war_duration = 4. rally = max(10-12, 0) = 0. NO TRIGGER.

#### MACHIAVELLI R4 Adjustments Summary:
| Country | Variable | Amount | Reason |
|---------|----------|--------|--------|
| Columbia | political_support | -2.5 | Support declining into election |
| Columbia | political_support | -3.0 | Negative GDP + elections |

---

### SYNTHESIS:

**Columbia momentum:** KEYNES (-0.5) solo. -> **-0.25** applied.

**Columbia inflation:** KEYNES (+17.39) solo. -> **+8.70** applied (0.5x). New inflation: 57.95 + 8.70 = **66.65%**.
- **This is a FALSE POSITIVE overcorrection.** Inflation is already spiraling realistically at 58%. Adding 8.7% more is unjustified.

**Columbia political_support:** MACHIAVELLI (-2.5, -3.0) solo. -> **-2.75** applied ((-5.5) * 0.5). Bounded at 30% of 25.14 = 7.54. -2.75 within bounds.

**Columbia mil_prod_eff:** CLAUSEWITZ (-0.3) solo. -> **-0.15** applied.

**Columbia ai_rd_progress:** CLAUSEWITZ (-0.02) solo. -> **-0.01** applied.

**Cathay momentum:** KEYNES (-0.5) solo. -> **-0.25** applied.

### Net Effect:

| Variable | Before Panel | After Panel | Change | Expert(s) |
|----------|-------------|-------------|--------|-----------|
| Columbia momentum | -1.65 | -1.90 | -0.25 | KEYNES solo |
| Columbia inflation | 57.95% | 66.65% | +8.70 | KEYNES solo (FALSE POSITIVE) |
| Columbia support | 25.14% | 22.39% | -2.75 | MACHIAVELLI solo |
| Columbia mil_prod_eff | 1.0 | 0.85 | -0.15 | CLAUSEWITZ solo |
| Columbia ai_rd_progress | 0.80 | 0.79 | -0.01 | CLAUSEWITZ solo |
| Cathay momentum | +0.30 | +0.05 | -0.25 | KEYNES solo |

### VERDICT: Net Negative — False Positive Damages Output

- **The inflation false positive is harmful.** Keynes Check 6 compares lifetime inflation delta against single-round money printing, producing a nonsensical "not enough inflation" signal when inflation is already at 58%. Adding 8.7% more inflation makes Columbia's spiral even worse than the formula produces, which was already unrealistically fast (per the test's own findings).
- **Brain drain and mil_prod_eff** are legitimate additions.
- **Machiavelli's pre-election support hit** (-2.75) is reasonable but perhaps excessive -- Columbia's support at 25% is already catastrophic. Pushing it to 22% does not change any game outcome.
- **Overall: the panel makes Columbia's situation WORSE when the test itself identifies that the formula is ALREADY too punishing** (fiscal death spiral too fast, crisis multiplier bug dampening negative growth). The panel piles on additional penalties without providing any corrective insight.

---

## SCENARIO 5: PEACE DIVIDEND R5 — Right After Ceasefire

### State at R5 (from TEST_4_FULL_RESULTS.md):

| Variable | Sarmatia | Ruthenia | Columbia |
|----------|-----------|-----------|----------|
| GDP | 8.44 | 2.05 | 295.0 |
| Growth | -8% | ~+0.5% | +1.8% |
| Stability | 1.00 (floor) | 4.50 | 6.65 |
| Support | ~40% | ~45% | ~60.6% (post-election) |
| Eco State | CRISIS (R3) | normal | normal |
| Momentum | -2.00 (after +1.5 ceasefire rally) | +0.65 (after +1.5 ceasefire rally) | +0.30 |
| Oil Price | $149.3 | — | — |
| Inflation | 198% | 10.8% | 3.5% |
| War Tired | 3.41 (decaying from 4.26) | 3.48 (decaying from 4.35) | 1.14 |

**History (R1-R4):** Sarmatia crisis accelerated by sanctions + deficit + war. Stability collapsed to 1.74 by R4 (regime collapse risk active). Ruthenia election R3: Beacon lost, Broker took power. Ceasefire agreed R5 -- Sarmatia retains occupied zone, sanctions review begins. Ceasefire rally: momentum +1.5 for both sides.

The ceasefire was JUST signed. This tests the panel's response to peace.

---

### KEYNES Assessment:

**Trajectory: GDP declining 3+ rounds?**
- Sarmatia: GDP declining all rounds. rounds_declining = 4+. growth = -8% (not > -1). NO TRIGGER.
- Ruthenia: GDP declining R1-R4 but now +0.5%. rounds_declining broken (growth turned positive). NO TRIGGER.

**Trajectory: Stability declining 3+ rounds?**
- Sarmatia: stab declined every round to 1.0. rounds_declining = 4+. trend = 'falling'. FIRES.
  - momentum: **-0.5**
  - **This is a problem:** Sarmatia just signed a ceasefire, received a +1.5 momentum boost, and is at stability floor. Keynes is ADDING -0.5 momentum, partially canceling the ceasefire rally. This is mechanical -- the trajectory check doesn't know about the ceasefire.

**Check 1: GDP growing during crisis?**
- Sarmatia: crisis, growth -8%. NO TRIGGER.

**Check 2: Oil importer growing >2% with oil >$150?**
- Oil = $149.3, NOT > $150. NO TRIGGER.

**Check 3: Oil producer NOT benefiting?**
- Oil = $149.3 > $120. Sarmatia: resource_pct = 0.40, growth = -8% (< 1%). FIRES: +1.2.
- But Sarmatia just signed ceasefire and sanctions are under review. Oil boost makes some sense.

**Check 4: Inflation spiral without growth?**
- Sarmatia: inf_delta = 193 (>> 20), growth = -8% (not > 0). NO TRIGGER.

**Check 5: Major partner in crisis?**
- Sarmatia is in crisis but GDP = 8.44 (< 30, NOT major economy). Does NOT trigger contagion on partners.

**Check 6: Money printing without inflation?**
- Sarmatia: printed ~5 coins, inf_delta = 193. Is 193 < 5*2 = 10? No. NO TRIGGER.

**Legacy: Capital flight (stability <3)?**
- Sarmatia: stability = 1.0 < 3, autocracy, eco_state = crisis (not collapse). FIRES.
  - gdp adjustment: 8.44 * 0.03 = **-0.253 GDP**. But GDP is HARD VARIABLE -> **REJECTED**.

**Legacy: Sanctions adaptation (>4 rounds)?**
- Sarmatia: sanctions_rounds = 4 at R4, now R5. If sanctions_rounds = 5: > 4. FIRES.
  - adaptation: 8.44 * 0.02 = **+0.169 GDP**. But GDP is HARD VARIABLE -> **REJECTED**.

**Legacy: Tech breakthrough?**
- No breakthroughs. NO TRIGGER.

#### KEYNES R5 Adjustments Summary:
| Country | Variable | Amount | Reason |
|---------|----------|--------|--------|
| Sarmatia | momentum | -0.5 | Stability declining 4+ rounds (COUNTERPRODUCTIVE) |
| Sarmatia | gdp_growth_rate | +1.2 | Oil producer benefit |
| Sarmatia | gdp | -0.253 | Capital flight (REJECTED - hard var) |
| Sarmatia | gdp | +0.169 | Sanctions adaptation (REJECTED - hard var) |

---

### CLAUSEWITZ Assessment:

**Legacy: Ceasefire rally (was at war, now not)?**
- Sarmatia: was_at_war = True (R4), at_war_now = False (R5 ceasefire). FIRES.
  - momentum: **+1.5**
  - Reason: "CLAUSEWITZ: Peace dividend -- markets rally on Sarmatia ceasefire."
  - **BUT WAIT: This ceasefire rally was already applied in the test results** (test shows momentum went from -3.50 to -2.00, a +1.5 boost). Is it double-counted?
  - Answer: The test results were traced manually including Pass 2. If this is the mechanism that produced the +1.5, then it is the same adjustment, not double-counted. We are tracing what the panel WOULD produce, which matches.

- Ruthenia: was_at_war = True, at_war_now = False. FIRES.
  - momentum: **+1.5**

**Check 3: Crisis military production?**
- Sarmatia: in crisis. FIRES: **mil_prod_eff -0.3**.

**Legacy: Brain drain?**
- Sarmatia: autocracy, not democracy. NO TRIGGER.
- Ruthenia: democracy, but NOT in crisis (eco_state = normal). NO TRIGGER.

#### CLAUSEWITZ R5 Adjustments Summary:
| Country | Variable | Amount | Reason |
|---------|----------|--------|--------|
| Sarmatia | momentum | +1.5 | Ceasefire peace dividend |
| Ruthenia | momentum | +1.5 | Ceasefire peace dividend |
| Sarmatia | mil_prod_eff | -0.3 | In crisis |

---

### MACHIAVELLI Assessment:

**Check 2: Ceasefire achieved (was_at_war, not now, support <60)?**
- Sarmatia: ceasefire, support ~40% (< 60). FIRES: **political_support +5.0**
- Ruthenia: ceasefire, support ~45% (< 60). FIRES: **political_support +5.0**

**Check 3: Autocracy under pressure (stability <3, support >50)?**
- Sarmatia: stability 1.0 < 3, support ~40%. NOT > 50. NO TRIGGER.

**Check 5: War fatigue (war_tired >3, support >40)?**
- Sarmatia: war_tired = 3.41 > 3, support = 40. `> 40` = False. BORDERLINE NO TRIGGER.
- Ruthenia: war_tired = 3.48 > 3, support = 45 > 40. FIRES: **political_support -2.0**
  - **This fires AFTER ceasefire.** The war is over but war tiredness hasn't fully decayed. The -2.0 partially cancels the +5.0 ceasefire bonus. This is debatable -- war fatigue should start declining after ceasefire, not continue penalizing.

**Legacy: Rally?**
- No longer at war. Rally only fires if at_war_now. NO TRIGGER.

#### MACHIAVELLI R5 Adjustments Summary:
| Country | Variable | Amount | Reason |
|---------|----------|--------|--------|
| Sarmatia | political_support | +5.0 | Ceasefire relief |
| Ruthenia | political_support | +5.0 | Ceasefire relief |
| Ruthenia | political_support | -2.0 | War fatigue at 3.48 (after ceasefire!) |

---

### SYNTHESIS:

**Sarmatia momentum:** KEYNES (-0.5) + CLAUSEWITZ (+1.5). Two experts, DISAGREE on direction. -> **FLAGGED for moderator.**
- This is the correct outcome. Keynes sees declining trajectory; Clausewitz sees ceasefire rally. They genuinely disagree. The moderator must decide.
- If only Clausewitz adjustment were applied: +1.5 (the ceasefire was just signed, this should dominate).
- FLAGGING is the right call.

**Ruthenia momentum:** CLAUSEWITZ (+1.5) solo. -> **+0.75** applied.

**Sarmatia gdp_growth_rate:** KEYNES (+1.2) solo. -> **+0.6** applied.

**Sarmatia mil_prod_eff:** CLAUSEWITZ (-0.3) solo. -> **-0.15** applied.

**Sarmatia political_support:** MACHIAVELLI (+5.0) solo. -> **+2.5** applied. Bounded: 30% of 40 = 12. +2.5 within bounds.

**Ruthenia political_support:** MACHIAVELLI (+5.0, -2.0). Same expert, two adjustments. Grouped as one variable target: both from MACHIAVELLI. Single expert with net +3.0. -> **+1.5** applied (x0.5).

### Net Effect:

| Variable | Before Panel | After Panel | Change | Expert(s) |
|----------|-------------|-------------|--------|-----------|
| Sarmatia momentum | -2.00 | -2.00 | 0 (FLAGGED) | KEYNES vs CLAUSEWITZ |
| Ruthenia momentum | +0.65 | +1.40 | +0.75 | CLAUSEWITZ solo |
| Sarmatia growth | -8% | -7.4% | +0.6 | KEYNES solo |
| Sarmatia mil_prod_eff | 1.0 | 0.85 | -0.15 | CLAUSEWITZ solo |
| Sarmatia support | 40% | 42.5% | +2.5 | MACHIAVELLI solo |
| Ruthenia support | 45% | 46.5% | +1.5 | MACHIAVELLI solo |

### VERDICT: Good Value — Ceasefire Mechanics Work

- **Clausewitz ceasefire rally (+1.5 momentum)** is the most valuable adjustment in the peace scenario. This is the primary peace dividend mechanism.
- **Machiavelli ceasefire support boost (+5.0 raw, +2.5 applied)** correctly models public relief.
- **The KEYNES vs CLAUSEWITZ disagreement on Sarmatia momentum is correctly flagged.** This is exactly what the moderator system is for -- the trajectory says "declining" but the event says "ceasefire." A human should resolve this in favor of the ceasefire signal.
- **War fatigue penalty AFTER ceasefire (Machiavelli)** is a design issue. The check fires based on war_tiredness > 3, but war_tiredness takes several rounds to decay. The penalty should be suppressed in the round ceasefire is signed.
- **Capital flight and sanctions adaptation both target GDP (hard variable) and are REJECTED.** Same bug as Scenario 3.

---

## OVERALL ASSESSMENT

### Does the Expert Panel Add Value?

**YES, but unevenly.** The panel adds genuine value in 3 of 5 scenarios and creates problems in 1.

| Scenario | Panel Value | Key Contribution | Key Problem |
|----------|------------|------------------|-------------|
| 1: Gulf Gate | Moderate | Election anxiety, oil producer boost | All adjustments single-expert (weak) |
| 2: Formosa | Good | Brain drain, blockade fatigue, pre-election panic | No semiconductor asymmetry insight |
| 3: Stability | Mixed | Cathay oil shock drag (strong catch) | Capital flight REJECTED (hard var bug); Machiavelli blind to deep-crisis countries |
| 4: Overstretch | **Net Negative** | Brain drain, mil_prod_eff | Inflation false positive (+8.7%) makes things worse |
| 5: Peace | Good | Ceasefire rally, support boost, correct flagging | War fatigue fires post-ceasefire; trajectory check fights ceasefire |

### Gaps in Expert Logic

**GAP 1: Capital Flight is Non-Functional (CRITICAL)**
The legacy capital flight code produces adjustments targeting `gdp` (hard variable). The soft/hard variable filter in `_apply_bounded_adjustment()` silently rejects these. Capital flight NEVER actually applies. This is the panel's most important economic correction mechanism, and it is broken.
- **Fix:** Change capital flight to target `gdp_growth_rate` instead of `gdp`, applying an equivalent percentage penalty.

**GAP 2: Keynes Check 6 (Printing vs Inflation) is a False Positive Generator (HIGH)**
The check compares `inf_delta` (lifetime cumulative) against `printed * 2` (single-round). At high printing rates, the single-round printing always exceeds the ratio threshold, producing nonsensical "inflation too low" adjustments even when inflation is spiraling at 58%+.
- **Fix:** Compare SINGLE-ROUND printing against SINGLE-ROUND inflation change, not cumulative delta. Or disable for countries where inflation > baseline + 30.

**GAP 3: Machiavelli is Blind to Countries in Deep Crisis (MEDIUM)**
All of Machiavelli's checks have thresholds that are already blown past by the time a country is in crisis:
- Democracy crisis check requires support > 45% (but support drops below 45 before crisis)
- War fatigue check requires support > 40% (same problem)
- Autocracy cracking requires support > 50% (same)
The only check that fires reliably is the election proximity check, which only applies to Columbia/Ruthenia at specific rounds.
- **Fix:** Add a "deep crisis political disintegration" check that fires when eco_state = crisis/collapse regardless of support level, applying additional stability and support penalties.

**GAP 4: No Expert Reasons About Strategic Asymmetry (MEDIUM)**
None of the experts can identify situations like: "Cathay's blockade hurts Columbia more than Cathay" or "Sarmatia's war drives oil prices that benefit Sarmatia." These are the most interesting strategic dynamics in the simulation, and the panel misses them entirely.
- **Fix:** Add a strategic analysis check that compares growth rates of adversary pairs and flags asymmetries.

**GAP 5: Trajectory Checks Fight Event-Driven Changes (LOW)**
The trajectory check for stability declining 3+ rounds fires even when a ceasefire was just signed (Scenario 5). The mechanical trend analysis does not account for game-changing events.
- **Fix:** Suppress trajectory-based adjustments in the round a major event occurs (ceasefire, election, regime change).

**GAP 6: Overstretch and War-Stability Checks Have Inverted Thresholds (LOW)**
Clausewitz Check 1 (war_tired > 3 AND stability > 6) and Check 2 (overstretch AND stability > 5) require stability to be HIGH, but by the time war tiredness or overstretch is significant, stability has already dropped. These checks are designed to catch "unrealistically stable" countries, but in practice they almost never fire.
- **Fix:** Remove the stability threshold or invert it (fire when stability is LOW and war tiredness is HIGH, as this is where additional pressure is most needed).

### False Positives

| Check | Scenario | Issue | Severity |
|-------|----------|-------|----------|
| Keynes Check 6 (printing/inflation) | Overstretch | Fires at 58% inflation, adds more | HIGH |
| Keynes trajectory (stability) | Peace | Fights ceasefire momentum boost | MEDIUM |
| Machiavelli war fatigue | Peace | Fires after ceasefire signed | LOW |
| Keynes oil producer boost | All | Gives Sarmatia GDP boost despite sanctions (-18% hit) | LOW (correct in isolation, misleading in context) |

### Summary Statistics Across All 5 Scenarios

- **Total adjustments generated by experts:** ~45
- **Adjustments that survived synthesis:** ~30 (single-expert x0.5 or majority)
- **Adjustments REJECTED (hard variable):** ~6 (all capital flight / sanctions adaptation)
- **Flagged for moderator:** 1 (Sarmatia momentum in peace scenario)
- **Two-expert agreements (majority rule):** 0 across ALL 5 scenarios
- **False positives (harmful adjustments):** 2 (inflation pile-on, trajectory vs ceasefire)

### Critical Finding: Zero Majority Agreements

In all 5 extreme scenarios at R4, **not a single adjustment received 2+ expert agreement.** Every applied adjustment was a single-expert opinion at 0.5x weight. This means:
1. The experts operate in silos -- KEYNES adjusts economic variables, CLAUSEWITZ adjusts military variables, MACHIAVELLI adjusts political variables. They almost never touch the same variable.
2. The majority-rule synthesis mechanism is therefore almost never tested. The "2/3 agree" path is dead code in practice.
3. The 0.5x weight for solo experts means all adjustments are halved, making the panel's total impact quite small (typically 0.1-2.0 on any variable).

**Recommendation:** Either (a) design explicit cross-domain checks where experts overlap (e.g., both KEYNES and MACHIAVELLI adjust `political_support` based on economic conditions), or (b) allow single-expert adjustments at full weight for high-confidence opinions instead of blanket 0.5x.
