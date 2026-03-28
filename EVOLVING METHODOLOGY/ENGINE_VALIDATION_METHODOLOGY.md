# Engine Validation Methodology
## TTT World Model — Iterative Calibration Process
**Version:** 1.0 | **Date:** 2026-03-28 | **Status:** Validated (8.6/10 credibility)

---

## Summary

A 4-step iterative process for validating and calibrating the world model engine against real-world economic, military, and political dynamics.

**Applied:** March 27-28, 2026. Two iterations. Engine credibility improved from 6.5/10 to 8.6/10.

---

## The Process

### Step 1: Expert Dependency Mapping

**Who:** Domain experts (KEYNES economics, CLAUSEWITZ military, MACHIAVELLI political)
**What:** Define 20-30 key causal dependencies with:
- Causal chain (A → B → C)
- Feedback loop (how C feeds back to A)
- Stabilizing mechanism (what prevents runaway)
- Observable behavior (what the SIM should show)
- Failure mode (what's wrong if the engine fails)

**Output:** `SEED_D_DEPENDENCIES_v[N].md`

### Step 2: Focused Test Scenario Design

**Who:** ATLAS (engine architect) + domain experts
**What:** Create 10 focused scenarios that cover all dependencies. Each scenario has:
- Prescribed round-by-round actions (deterministic inputs)
- Expected outcome corridors (min-max ranges for key variables)
- Pass/fail criteria

**Key principle:** Expected ranges are set by EXPERTS based on real-world analogies, not by looking at what the engine produces. The engine must match reality, not the other way around.

**Output:** `SEED_D_TEST_SCENARIOS_v[N].md`

### Step 3: Run Scenarios + Score Credibility

**Who:** ATLAS runs engine formulas manually against prescribed inputs
**What:** For each scenario, trace through the engine code step by step, record actual values, compare vs expected corridors.

**Scoring:**
- Per-scenario: 1-10 (10 = perfectly realistic, 7+ = credible)
- Per-dependency: 1-10
- Overall: weighted average

**Output:** `SEED_D_TEST_RESULTS_v[N].md`

### Step 4: Fix + Iterate

**Who:** ATLAS fixes code, experts validate fixes
**What:**
- Critical issues (score < 6): fix immediately, re-run affected scenarios
- Calibration issues (score 6-7): fix and re-run
- Minor issues (score 7-8): fix if time allows
- Target: overall 8+/10, no scenario below 7/10

**Continue iterating** until target met. Each iteration produces a new version of test results.

---

## Results Log

| Iteration | Engine Version | Overall Score | Key Fixes |
|-----------|---------------|:------------:|-----------|
| v1 (initial) | v2.0 | **6.5/10** | — (first run, identified 4 critical bugs) |
| v2 (fixes) | v2.1 | **7.9/10** | Gulf Gate double-count, mandatory social spending, chokepoint sync, inflation decay |
| v3 (calibration) | v2.2 | **8.6/10** | Oil inertia, sanctions multiplier, tech boost as growth rate, inflation cap |

---

## When to Apply This Methodology

- After any significant engine redesign
- Before SEED gate review
- After adding new mechanics (new domain, new formula)
- When test results show unexpected behavior
- Periodically (every 2-3 major development cycles) as regression validation

---

## Files Produced

```
D_ENGINES/
├── SEED_D_DEPENDENCIES_v1.md        ← 25 causal dependencies
├── SEED_D_TEST_SCENARIOS_v1.md      ← 10 focused test scenarios
├── SEED_D_TEST_RESULTS_v1.md        ← Iteration 1 results (6.5/10)
├── SEED_D_TEST_RESULTS_v2.md        ← Iteration 2 results (7.9/10)
└── SEED_D_TEST_RESULTS_v3.md        ← Iteration 3 results (8.6/10)
```

---

## Key Lessons Learned

1. **Multiplicative factor models produce unrealistically smooth curves.** Real economies have tipping points. The crisis escalation ladder (NORMAL→STRESSED→CRISIS→COLLAPSE) solved this.

2. **Double-counting is the #1 bug pattern.** Gulf Gate affected GDP through both oil price AND direct blockade fraction. Always check: does this effect have multiple channels?

3. **Inflation must use delta-from-baseline, not absolute.** Countries with structurally high inflation have already "priced it in."

4. **Tech multipliers compound dangerously.** A 15% GDP multiplier applied each round doubles GDP in 5 rounds. Use growth-rate additive bonuses instead.

5. **Oil price needs inertia.** Markets don't jump instantly to equilibrium. 60% movement per round produces realistic trajectories.

6. **Expert-defined corridors prevent fitting to broken formulas.** Always set expected ranges BEFORE looking at engine output.
