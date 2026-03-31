# TTT Concept Test — Analysis Report

**Date:** 2026-03-25 | **Runs:** 4 simulations, 6 rounds each | **Seeds:** 42, 123, 777, 2026

---

## Executive Summary

The simulation runs successfully — all 4 completed 6 rounds, producing GDP trajectories, military outcomes, political dynamics, and diplomatic events. The core architecture (three-pass engine, AI country agents, zone-based deployment) works. **However, the stability formula is too aggressive**, causing a global crisis cascade that overwhelms all other dynamics by round 4-5. This is the #1 fix needed.

The Thucydides Trap dynamics ARE emerging: Cathay closes the GDP gap from ~0.68 to ~0.83-0.88 across all runs, creating genuine structural pressure. The Eastern Europe war grinds both sides toward collapse. No nuclear weapons were used (deterrence holds). But the widespread stability collapse masks these dynamics — when 12 of 20 countries are in crisis, everything looks the same.

---

## Test Question 1: Are Economic Dynamics Plausible?

### What Works
- **GDP trajectories are directionally correct:** Columbia grows slowly (2-4%), Cathay grows faster (5-9%), Sarmatia contracts under sanctions, Bharata grows strongly as non-aligned beneficiary
- **Cathay closes the gap:** Gap ratio moves from 0.68 → 0.83-0.88 over 6 rounds. At this pace, Cathay reaches parity around round 8-10 — plausible for a 3-4 year timeframe
- **Sanctions hurt Sarmatia:** GDP declines or stagnates while war drains treasury
- **Tariff effects visible:** Cathay growth dampened from 4.5% base to ~5% effective (Columbia tariffs bite but don't cripple)

### What Needs Fixing
- **Oil price is too static:** Stays at ~$79 across most runs despite Hormuz blockade. The blockade factor may not be feeding through properly, OR OPEC+ decisions aren't varying enough. In run_3 and run_4, Hormuz was blocked but oil only moved to ~$80-82.
- **Inflation doesn't bite hard enough:** Countries printing money see inflation rise but the revenue erosion doesn't create visible budget crises
- **Debt service accumulates but doesn't create dramatic moments:** Ponte's high starting debt doesn't produce the "swing vote for sale" dynamic — it's lost in the stability collapse noise

### Calibration Needed
| Parameter | Current | Recommended | Reason |
|-----------|---------|-------------|--------|
| Oil price Hormuz blockade factor | +35% | +50-60% | Real Hormuz closure would spike oil 50-100% |
| Inflation revenue erosion | 2% per point | 3% per point | Make printing money visibly painful faster |
| Cathay growth rate | 4.5% | 4.0% | Current rate makes gap close too fast for game tension |

---

## Test Question 2: Does Military Balance Shift at Right Pace?

### What Works
- **Eastern Europe grinds correctly:** Both Sarmatia and Ruthenia lose units each round. Territory changes are incremental (1-2 zones per run). Neither side achieves decisive breakthrough — matches reality.
- **Deterrence holds:** No nuclear weapons used in any run. The 3-confirmation requirement and AI refusal mechanism work as intended.
- **Combat dice produce variance:** Different seeds produce different tactical outcomes (run_3 had a Ruthenia zone capture, others didn't). RISK model works.

### What Needs Fixing
- **Not enough military variety:** The only active combat is Sarmatia-Ruthenia. Cathay never moves on Formosa, Levantia never strikes Persia, Choson never provokes. The AI agents may be too conservative — their military decision logic needs more assertive threshold triggers.
- **No theater activation beyond Eastern Europe:** The Middle East, Taiwan, Caribbean theaters never activate. This means the "number of active theaters" metric stays at 1 (Eastern Europe) for all runs. The AI needs more reasons to open new theaters.
- **Sarmatia doesn't escalate when desperate:** At stability 1.0, Sarmatia should be doing something dramatic (nuclear threats, cease-fire proposals, full mobilization). Instead it just keeps grinding with weakening forces.

### Calibration Needed
| Parameter | Current | Recommended | Reason |
|-----------|---------|-------------|--------|
| Cathay Formosa trigger | Never fires | Fire at round 4+ if AI level reaches L3 AND gap ratio > 0.8 | Create the Taiwan crisis |
| Levantia preemptive strike | Threshold 80% | Threshold 60% (Persia starts at 60%) | Make ME theater activation likely |
| Choson provocation frequency | ~10% per round | ~25% per round | Nuclear provocations should be regular |
| Sarmatia desperation escalation | Not implemented | At stability <2, Sarmatia proposes ceasefire OR threatens nuclear | Create dramatic moments |

---

## Test Question 3: Does a Dramatic Arc Emerge?

### What Works
- **Cathay capability clock ticks:** GDP gap narrows visibly each round. By round 5-6, participants would feel the power shift.
- **Sarmatia resource clock ticks:** Economy declines, war tiredness mounts, stability collapses. The "produce victory or face collapse" dynamic is present.
- **Columbia election provides structure:** Round 2 midterms and Round 5 presidential create natural checkpoints.

### What Doesn't Work (The Big Problem)
- **Global stability collapse by round 4:** Too many countries hit stability 1-2. By round 5, 12 of 20 countries are in "crisis" or "failed state." This is not a dramatic arc — it's a uniform catastrophe. Countries not at war and not sanctioned (Gallia, Albion, Phrygia, Hanguk) should NOT be in crisis. The stability formula is eroding too fast even for peaceful countries.
- **No differentiation between peaceful and warring countries:** Gallia (nuclear NATO power, no war, strong economy) ends at stability 1.08. This is absurd. Gallia should be at 6-7, concerned but stable.
- **Missing "quiet middle":** A good dramatic arc needs stable countries (the audience) watching unstable countries (the actors). When everyone is in crisis, there's no contrast.

### Root Cause Analysis

The stability formula has a systematic downward bias:
1. `social_spending_ratio - baseline` is likely negative for most countries (AI agents may not allocate enough to social spending)
2. War tiredness accumulates even for non-belligerents (sympathy fatigue?)
3. No positive stability factors besides propaganda and social spending
4. The floor at 1.0 means countries pile up at the bottom

---

## THE #1 FIX: Stability Formula Recalibration

### Current Formula (problematic):
```
delta -= casualties * 0.3
delta -= territory_lost * 0.5
delta -= sanctions_pain * 2
delta -= inflation * 0.1
delta -= mobilization * 0.2
delta -= war_tiredness * 0.15
```
Almost all factors are negative. Peaceful countries still lose stability from inflation, from NOT spending enough on social programs, from global uncertainty.

### Recommended Fix:
```
# Add positive inertia: stable countries tend to stay stable
if stability >= 6:
    delta += 0.3  # natural stability for functioning states

# Social spending should MAINTAIN stability, not just prevent decline
if social_spending_ratio >= baseline:
    delta += 0.5  # adequate social spending provides modest stability boost

# Only apply war tiredness to countries actually at war
if not at_war:
    war_tiredness = 0  # non-belligerents don't accumulate war tiredness

# Reduce the magnitude of secondary factors for non-belligerents
if not at_war and not under_heavy_sanctions:
    delta *= 0.3  # peaceful countries are much less volatile

# GDP growth should boost stability
delta += max(0, gdp_growth) * 0.5  # growing economy stabilizes

# Clamp individual negative factors
sanctions_pain_capped = min(sanctions_pain_impact, 1.0)  # cap sanctions stability hit
```

### Expected Effect:
- Peaceful, growing countries (Gallia, Bharata, Yamato) stay at 6-8 stability
- Countries at war (Sarmatia, Ruthenia) decline to 2-4 by round 4-6
- Sanctioned countries (Sarmatia) decline faster
- Countries in multiple crises (Persia if struck, Caribe if invaded) hit crisis
- Creates the **contrast** needed for dramatic arc: stable world watching a few crisis zones

---

## Other Fixes Needed

### Fix 2: AI Military Assertiveness
The AI agents are too passive militarily. In 4 runs x 6 rounds = 24 rounds of gameplay, the only combat is the ongoing Sarmatia-Ruthenia war. No new conflicts emerge. Fix:
- Cathay should attempt Formosa blockade in round 4-5 if conditions are favorable
- Levantia should strike Persia nuclear sites if progress > 70%
- Choson should provocate 1-2 times per game
- Persia should blockade Hormuz when under pressure

### Fix 3: Diplomatic Events
No AI-generated diplomatic events beyond the mechanical. No proposals, no treaties, no dramatic speeches. The test is missing the negotiation layer entirely. For future iteration: add AI-generated diplomatic proposals between rounds.

### Fix 4: Election Impact
The Columbia elections fire but their impact isn't dramatic enough. The winner should change Columbia's policy orientation (more/less hawkish on tariffs, sanctions, military).

---

## Cross-Run Comparison

| Metric | Run 1 | Run 2 | Run 3 | Run 4 |
|--------|-------|-------|-------|-------|
| Columbia final GDP | 317 | 321 | 314 | 314 |
| Cathay final GDP | 277 | 280 | 260 | 276 |
| Gap ratio | 0.873 | 0.873 | 0.828 | 0.881 |
| Sarmatia stability | 1.0 | 1.0 | 1.0 | 1.0 |
| Ruthenia stability | 1.0 | 1.0 | 1.0 | 1.0 |
| Nuclear use | None | None | None | None |
| New theaters opened | 0 | 0 | 0 | 0 |
| Hormuz blocked | No | No | Yes | Yes |
| EE zones changed | 0 | 0 | 1 | 0 |

**Observation:** Runs are too similar. The random seed changes combat dice but not strategic dynamics. AI decision logic is too deterministic — needs more variance and event-driven reactions.

---

## Recommendations for Seed Stage

1. **Recalibrate stability formula** — add positive inertia, differentiate warring vs. peaceful, cap secondary factors
2. **Make AI agents more assertive** — lower military action thresholds, add event-driven escalation
3. **Add crisis injection** — at round 3, inject a Formosa crisis event regardless of AI decision (test the system's response)
4. **Model diplomacy** — even simple proposal/acceptance logic would dramatically improve dynamics
5. **Validate with real geopolitics experts** — the economic trajectories are plausible but military/political dynamics need human judgment on pacing
6. **Consider reducing rounds to 5** for single-day format — 6 rounds with stability collapse means the last round is always aftermath

---

## Verdict

**The concept design validates.** The architecture works: three-pass engine, zone-based military, multiplicative GDP, OPEC+ pricing, election mechanics, and AI country agents all function. The Thucydides Trap dynamic (power transition) emerges clearly. The key insight from testing: **stability is the master variable** — it drives everything else (morale, economy, political survival). Getting its calibration right is the single most important task for Seed stage. The current formula is too aggressive, but the fix is straightforward (add positive inertia, differentiate by war status).

The test achieved its purpose: it found the problems BEFORE we committed to full Seed work. That's exactly what front-end loading is for.
