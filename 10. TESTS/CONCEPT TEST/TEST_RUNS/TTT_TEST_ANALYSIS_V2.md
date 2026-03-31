# TTT Concept Test Analysis: V1 vs V2

**Date:** 2026-03-25
**V1 Runs:** 1-4 (6 rounds, seeds 42/123/77/256)
**V2 Runs:** 5-8 (8 rounds, seeds 100/200/300/400)

---

## Executive Summary

V2 engine fixes resolve the most critical V1 flaw: **unrealistic universal stability collapse**. In V1, peaceful countries like Columbia (stability 3.1), Cathay (3.3), and Bharata (3.1) all collapsed toward crisis levels despite no wars or domestic crises -- a formula artifact, not emergent behavior. V2 introduces institutional inertia, autocracy resilience, and peaceful-country dampening. The result: stable countries stay stable, war-fighting countries decline gradually (not catastrophically), and the Thucydides Trap dynamic emerges more naturally.

---

## Key Findings: V1 vs V2 Comparison

### 1. Stability Realism

| Country | V1 Final Stability (6 rounds) | V2 Final Stability (8 rounds) | Assessment |
|---------|------|------|------------|
| Columbia | 3.1 (avg) | 9.0 (avg) | V2 correct: peaceful superpower should not collapse |
| Cathay | 3.3 (avg) | 8.8 (avg) | V2 correct: growing economy with no war should be stable |
| Sarmatia | 1.0 (all runs) | 1.9 (avg) | Both stressed, but V2 shows resilience before decline |
| Ruthenia | 1.0 (all runs) | 1.0 (all runs) | Consistent: warzone with tiny GDP collapses regardless |
| Persia | 1.0 (all runs) | 3.5 (avg) | V2 better: Iran is strained but functional |
| Bharata | 3.1 (avg) | 8.7 (avg) | V2 correct: fastest-growing democracy should not crash |
| Gallia | ~3 (fracturing) | ~7 (holding) | V2 correct: France is stable despite geopolitical stress |

**Key V2 improvement:** Peaceful, non-sanctioned countries now resist destabilization (delta * 0.25 for negative changes). Autocracies get additional 30% resilience to stability drops. Positive institutional inertia for stable states (+0.15 for stability >= 7).

### 2. Alliance Cohesion

| Metric | V1 | V2 |
|--------|-----|-----|
| NATO status | FRACTURING (all 4 runs) | HOLDING (all 4 runs) |
| Weakest link | Gallia (all runs) | Phrygia (all runs) |
| Columbia stability | 3.1 | 8.8-9.1 |

V1 showed NATO fracturing because the stability formula dragged all members into crisis. V2 correctly shows NATO holding together with Phrygia (Turkey) as the weakest link -- consistent with real-world alliance dynamics where Turkey's hybrid regime and economic crisis make it the most likely defector.

### 3. Thucydides Trap Dynamic

| Metric | V1 (avg) | V2 (avg) |
|--------|----------|----------|
| GDP gap ratio | 0.864 | 0.925 |
| Columbia GDP | 316.5 | 366.2 |
| Cathay GDP | 273.4 | 338.9 |
| Direct conflict | None | None |
| Assessment | ELEVATED | ELEVATED |

V2 shows a **more dangerous** Thucydides Trap trajectory:
- Cathay closes the gap faster (0.925 vs 0.864 ratio) due to higher growth compounding over 8 rounds
- Run 8 (seed 400) reaches 0.999 -- virtual parity
- Despite parity, no direct conflict emerges -- consistent with nuclear deterrence theory
- The Formosa window calculation shows Cathay accumulating capability without acting (window score not yet exceeding threshold)

**Critical finding:** The trap is economic/technological, not military. Both sides avoid direct confrontation while competing intensely in GDP, AI technology, and alliance building.

### 4. Eastern Europe War

| Metric | V1 | V2 |
|--------|-----|-----|
| Status | COLLAPSE_IMMINENT | COLLAPSE_IMMINENT |
| Sarmatia stability | 1.0 (all) | 1.7-2.2 |
| Sarmatia war tiredness | ~10+ | 8.4 |
| Ruthenia stability | 1.0 (all) | 1.0 (all) |
| Sarmatia GDP | 17.5 (avg) | 20.0 (avg) |

V2 improvements for Sarmatia:
- Autocracy resilience bonus prevents immediate collapse
- War tiredness decay (5%/round adaptation) prevents runaway fatigue
- Sanctions-adapted economy (reduced market panic for long-sanctioned autocracies)
- Capital controls limit capital flight vs democracies

Sarmatia declines from stability 5 to ~2 over 8 rounds (4 years of additional war). This is plausible: severe strain but not collapse. GDP holds around 20 (vs starting 22), showing the sanctions-resistant economy described in the design doc.

Ruthenia remains at 1.0 -- with GDP of only 2, high war tiredness (starting at 5), and active combat, the small economy cannot sustain prolonged war. This represents Ukraine's dependence on Western aid for survival.

### 5. Nuclear Proliferation

| Country | V1 Nuclear Level | V2 Nuclear Level |
|---------|-----------------|-----------------|
| Persia | L1 (all runs) | L1 (all runs) |
| Cathay | L2 (all runs) | L2 (all runs) |
| Choson | L1 (all runs) | L1 (all runs) |

Persia reaches L1 (nuclear threshold) in all runs. In V2, Levantia's graduated response (intensified covert ops at 60-70%, strike probability at 70-80%) means the Levantia-Persia dynamic is more tense. Persia ends at stability 3.3-3.7 in V2 (vs 1.0 in V1), showing a strained but functional regime navigating between nuclear ambition and strike risk.

### 6. Oil Price Dynamics

V2 oil prices are more responsive to disruptions:
- Hormuz blockade by Persia in several runs causes 60% price spike (vs 35% in V1)
- Oil-producing countries (Sarmatia, Solaria) benefit explicitly from high prices through the new oil_revenue calculation
- This creates a feedback loop: sanctions on Sarmatia reduce stability -> Sarmatia threatens energy leverage -> oil prices rise -> Sarmatia gets more oil revenue -> partial sanctions offset

### 7. AI Technology Race

Both versions show Columbia and Cathay reaching AI L3, with the AI tech race as a key Thucydides Trap accelerant. V2's enriched profiles explicitly reference this: Cathay's "ticking clock" includes the fear that Columbia reaches L4 first, permanently closing the window.

---

## What V2 Gets Right

1. **Peaceful countries stay stable.** Columbia, Cathay, Bharata, Yamato, and European allies maintain high stability through institutional inertia and economic growth -- matching real-world expectations.

2. **War-fighting countries decline gradually, not catastrophically.** Sarmatia goes from 5.0 to ~2.0 over 8 rounds (4 years), consistent with Russia's real-world trajectory of "strained but functional."

3. **Autocracy resilience is modeled.** Sarmatia and Cathay benefit from regime-type-specific bonuses (capital controls, suppression of instability) at the cost of reduced political responsiveness.

4. **Sanctions are painful but survivable.** The adapted-economy mechanic for long-sanctioned autocracies prevents unrealistic GDP collapse while maintaining steady erosion.

5. **The Thucydides Trap is structural, not accidental.** The GDP gap closes naturally through differential growth rates, not through random shocks.

---

## What Still Needs Work

1. **Political support ceiling.** Bharata hits 100% support in all V2 runs -- the mean-reversion dampening helps but isn't strong enough for high-growth, non-war countries. Need stronger ceiling effects or more domestic friction factors.

2. **Cathay GDP growth too high.** At 8% effective growth in some rounds (compounding), Cathay reaches near-parity too fast. The AI tech bonus (L3 = +15%) on top of 4.5% base growth creates 5.2%+ effective growth that compounds dramatically over 8 rounds.

3. **Formosa crisis never triggers.** Despite enriched window calculations, no run produces a Formosa blockade. The window_score threshold (0.65) may be too high, or Cathay's naval buildup too slow (starting at 8, needing 10+ for the window to open).

4. **Ruthenia has no path to survival.** GDP 2 with negative growth means Ruthenia collapses in every scenario. Need a "Western aid" mechanic that offsets some of the economic decline -- currently arms transfers boost military units but not economic resilience.

5. **Choson provocations too mild.** The attention-seeking logic works but Choson never meaningfully escalates. Need a mechanism for nuclear/ICBM tests that create diplomatic crises forcing Columbia response.

6. **European differentiation weak.** Gallia, Teutonia, Freeland, Ponte, and Albion all end up similarly stable. Their different strategic positions (Gallia's autonomy drive, Teutonia's China-trade dependency, Ponte's debt crisis) should produce more divergent outcomes.

7. **War termination missing.** The Sarmatia-Ruthenia war never ends. Need a ceasefire/settlement mechanic triggered by mutual exhaustion, collapse of one side, or great-power mediation.

---

## Recommendations for V3

1. **Add war termination mechanics** -- ceasefire when both sides below stability 3, or when one side collapses below 1.5.
2. **Add Western economic aid to Ruthenia** -- $5-10B/round equivalent keeping GDP from crashing below 1.5.
3. **Lower Cathay Formosa window threshold** or increase naval production rate to test the Taiwan contingency.
4. **Add domestic friction events** (protests, scandals, economic shocks) to prevent peaceful-country support from plateauing at 100%.
5. **Add Choson nuclear/ICBM test events** that force Security Council responses and create diplomatic mini-crises.
6. **Differentiate European country responses** to Columbia-Cathay competition (Teutonia trade exposure, Ponte debt vulnerability, Gallia independence drive).

---

## Run Summary Table

| Run | Seed | Trap Gap | Columbia GDP | Cathay GDP | Nord Stab | Alliance | Key Event |
|-----|------|----------|-------------|------------|-----------|----------|-----------|
| V1-R1 | 42 | 0.873 | 317.4 | 277.0 | 1.0 | FRACTURING | All countries destabilize |
| V1-R2 | 123 | 0.873 | 320.6 | 279.8 | 1.0 | FRACTURING | Universal collapse |
| V1-R3 | 77 | 0.828 | 314.4 | 260.4 | 1.0 | FRACTURING | Universal collapse |
| V1-R4 | 256 | 0.881 | 313.7 | 276.4 | 1.0 | FRACTURING | Universal collapse |
| **V2-R5** | **100** | **0.943** | **363.6** | **342.8** | **1.9** | **HOLDING** | Hormuz blocked, Persia reaches L1 |
| **V2-R6** | **200** | **0.834** | **358.7** | **299.0** | **2.2** | **HOLDING** | Lower Cathay growth seed |
| **V2-R7** | **300** | **0.924** | **371.0** | **342.8** | **1.7** | **HOLDING** | Sarmatia lowest stability |
| **V2-R8** | **400** | **0.999** | **371.6** | **371.2** | **2.0** | **HOLDING** | Near GDP parity reached |
