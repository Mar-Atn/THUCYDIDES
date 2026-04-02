# Calibration Methodology — TTT Engine
**Version:** 1.0 | **Date:** 2026-04-01 | **Owner:** LEAD + SUPER EXPERT
**Status:** ACTIVE — First cycle in progress

---

## Purpose

Transform engine formulas from "mathematically correct" to "produces credible world dynamics." The goal is not perfection — it is a **viable model** that produces plausible trajectories recognizable to someone who follows geopolitics.

---

## The Calibration Cycle

```
RUN → ANALYZE → DIAGNOSE → PRESCRIBE → IMPLEMENT → RE-RUN → COMPARE
```

### Step 1: RUN
- Execute 8-round Tier 1 simulation (no AI agents, no player actions)
- Record full trajectories: GDP, stability, treasury, oil price per country per round
- Record all events (elections, revolutions, health, capitulation)
- Save as numbered test run (Test Run #N)

### Step 2: ANALYZE (SUPER EXPERT agent)
Three-level analysis, each level narrows focus:

**Level A — Macro Realism Check:**
- Are the STARTING values correct? (GDP ratios, inflation levels, military balance)
- Does the overall shape make sense? (Who grows, who declines, what collapses)
- Compare to real-world: "If these were real countries under these conditions, would this trajectory be plausible over ~2 years?"
- Web research: check actual Q1 2026 data for reference points

**Level B — Parameter Dynamic Analysis:**
- For each parameter (GDP, stability, inflation, oil price): is the RATE of change realistic?
- Real-world benchmarks: Russia GDP under sanctions (-2% to -5% annual, not -46%). Iran GDP under sanctions + war (-10% to -20% worst case). China growth (4-5% realistic, not 10%).
- Identify OUTLIERS: which countries/parameters deviate most from plausible trajectories?
- Rank by severity (most broken → least broken)

**Level C — Single-Variable Control Analysis (Scientific Method):**
- For the top 3-5 outliers: isolate the formula responsible
- Trace the chain: which input → which formula → which output → which downstream effect?
- Identify the specific constant, multiplier, or threshold that's wrong
- Compare the formula's behavior to economic/political science literature

### Step 3: DIAGNOSE
- Root cause for each outlier (bug vs. calibration vs. missing mechanic)
- Classify: STRUCTURAL (formula is wrong) vs. PARAMETRIC (formula is right, constants are wrong) vs. INITIALIZATION (starting data is wrong)

### Step 4: PRESCRIBE
- For each diagnosis: specific change with rationale
- Format: "Change X from Y to Z because [real-world evidence / theory]"
- Predict expected effect: "This should make Sarmatia GDP decline ~5-10% per round instead of ~50%"

### Step 5: IMPLEMENT
- Apply changes to engine code (BACKEND, not EXPERT)
- Layer 1 tests must still pass after changes

### Step 6: RE-RUN
- Same 8-round Tier 1 run
- Save as Test Run #(N+1)

### Step 7: COMPARE
- Side-by-side trajectory comparison: Run N vs Run N+1
- Did the prescribed changes produce the predicted effects?
- Are there new issues introduced?
- If satisfactory → cycle complete. If not → repeat from Step 2.

---

## Convergence Criteria

The model is "viable" when:
1. No country GDP collapses to floor (0.5) without a genuine catastrophe (nuclear strike, full invasion)
2. Sanctioned countries decline 5-15% per round, not 50%+
3. Growing economies grow 2-8% per round, not 10%+
4. Stability changes are gradual (±0.5 per round typical, ±1.0 for major events)
5. Oil price stays in $50-$200 range without artificial clamping
6. Elections are competitive (not 75-25 every time)
7. At least one crisis escalates WITHOUT being scripted
8. No country eliminated before Round 4
9. A geopolitics-literate human reads the 8-round summary and says "this is plausible"

---

## SUPER EXPERT Agent Role

A specialized agent with:
- **Domain knowledge:** International relations, macroeconomics, military studies, political science
- **Web access:** Can research real-world data, historical precedents, academic literature
- **Engine access:** Can read all formula code, constants, and test results
- **Output:** Structured calibration memos (diagnosis + prescription + predicted effect)
- **Independence:** Does NOT modify code. Recommends changes. BACKEND implements.

---

## Test Run Registry

| Run# | Date | Changes from previous | Key finding |
|------|------|----------------------|-------------|
| 1 | 2026-04-01 | Baseline (first run) | Sanctions too aggressive, growth uncapped, stability too volatile |
| 2 | — | — | — |
