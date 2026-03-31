# SEED TESTS3 — MASTER ANALYSIS REPORT
## 8 Tests × 8 Rounds | 64 Rounds Simulated | Engine v3 (4 calibration fixes)
**Date:** 2026-03-28 | **Tester:** Independent Claude Code Instance
**Previous:** SEED TESTS2 (2026-03-27) — 14 issues found. Team applied 4 calibration fixes + data corrections overnight.

---

## EXECUTIVE SUMMARY

Engine v3 is a significant improvement over v2. **All 4 calibration fixes validated working.** Oil inertia eliminates price spikes. Additive tech factor eliminates GDP doubling. Inflation cap prevents instant collapse. Sanctions adaptation is more realistic.

**However, 12 new design issues discovered** — including 2 critical engine bugs and a structural economic problem that undermines the stability system. The new crash-test scenarios (Tests 7-8) proved their value by exposing bugs invisible to baseline tests.

**Overall engine credibility: 7.5/10** (up from ~6.5 in TESTS2 v2, but new bugs found).

**GAME-BREAKING FINDING (Test 8):** Patience is the dominant strategy for Cathay. The non-military path produces GDP parity + naval superiority by R8 without risk. This dissolves the Thucydides Trap — if the rising power can just wait and win, there is no trap. The Helmsman's legacy clock must have mechanical consequences (not just narrative pressure), and economic convergence must plateau before full parity.

---

## TEST RESULTS AT A GLANCE

| Test | Score | Verdict | Key Finding |
|------|-------|---------|-------------|
| 1. Generic Baseline | 8.0/10 | **PASS** | All 4 Cal fixes validated. Columbia oil windfall bug distorts GDP dynamics. |
| 2. Formosa Crisis | 8.0/10 | **PASS** | Semiconductor ramp works (0.3→1.0). Formosa export collapse not modeled. |
| 3. Gulf Gate Economics | 8.5/10 | **PASS** | Oil inertia perfect ($80→$128→$147→$152). No swing >$47. |
| 4. Peace Negotiation | 7.5/10 | **PASS (gaps)** | Crisis accelerates ceasefire R7→R5. But post-ceasefire mechanically punishing. |
| 5. Stability Calibration | 6.5/10 | **CONDITIONAL** | Formula caps work, but economic death spiral overwhelms stability buffers. |
| 6. Tech Race | 8.5/10 | **PASS** | Columbia reaches L4 in R4 unrestricted, R8 with rare earth L3. Fix works. |
| 7. Columbia Overstretch | 7.0/10 | **PASS (bugs)** | **CRITICAL: Crisis GDP multiplier is BACKWARDS** — dampens instead of amplifies contraction. |
| 8. Cathay Patience | 7.0/10 | **PASS (design issue)** | **Patience is DOMINANT strategy.** Cathay reaches GDP parity + naval superiority by R8 without military action. Dissolves the Trap's core tension. |

---

## CRITICAL BUGS (Must Fix)

### BUG 1: Crisis GDP Multiplier Direction (Test 7) — CRITICAL
**Problem:** `CRISIS_GDP_MULTIPLIER = {crisis: 0.50, collapse: 0.20}` applied as `effective_growth = raw_growth × crisis_mult`. When raw growth is NEGATIVE, this REDUCES contraction. A country in COLLAPSE with -5% raw growth gets -1% effective — BETTER than normal.
**Impact:** Crisis states protect countries instead of punishing them. The entire crisis escalation ladder is inverted for contracting economies.
**Fix:**
```python
if raw_growth < 0:
    effective_growth = raw_growth * (2.0 - crisis_mult)  # Amplify contraction
else:
    effective_growth = raw_growth * crisis_mult  # Dampen growth
```

### BUG 2: Columbia Oil Revenue Formula (Test 1) — HIGH
**Problem:** Oil revenue = `price × resource_pct × GDP × 0.01`. Columbia (GDP 280, resources 8%) gets 29.9 coins/round at $133 oil — larger than Sarmatia's windfall despite not being a comparable oil exporter. This makes Columbia immune to oil shocks.
**Fix:** Oil revenue should use a fixed production capacity, not GDP-scaled. Or cap oil revenue as percentage of GDP (e.g., max 5% of GDP for non-OPEC producers).

### BUG 3: Formosa Export Collapse Not Modeled (Test 2) — HIGH
**Problem:** Engine models IMPORT dependency (countries lose GDP from chip shortage) but not EXPORT dependency (Formosa's economy should crash when it can't export semiconductors). Formosa's GDP barely drops when blockaded despite being the world's semiconductor producer.
**Fix:** Add `export_dependency` field. When blockaded, Formosa loses GDP proportional to tech_sector exports.

---

## CALIBRATION FIXES VALIDATED (All Working)

| Fix | TESTS2 Problem | TESTS3 Result | Status |
|-----|----------------|---------------|--------|
| Cal-1: Oil inertia | $198 instant spike | $133 R1, gradual climb to $152 | **VALIDATED** |
| Cal-2: Sanctions | Over-aggressive GDP damage | Adaptation kicks in R5, damage slows 40% | **VALIDATED** |
| Cal-3: Tech factor | +15% multiplicative GDP doubling | +1.5pp additive, no doubling | **VALIDATED** |
| Cal-4: Inflation cap | -3.25 instant collapse for Persia | -0.50 max per round | **VALIDATED** |

---

## STRUCTURAL ISSUE: Economic Death Spiral vs Stability

**Found in:** Tests 5, 7
**Problem:** The stability formula is now well-calibrated, but the economic model underneath creates fiscal death spirals that overwhelm ALL stability buffers:
- Ruthenia: maintenance 4.2 coins vs revenue 0.55 → 8x deficit
- Sarmatia: maintenance 12.9 vs revenue 3.3 → 4x deficit
- Columbia (Test 7): debt burden consumes 67% of revenue by R4

The chain: deficit → money printing → inflation spike → revenue erosion → larger deficit → more printing → crisis state → stability collapse. This happens faster than any stability mechanic can offset.

**Not a stability formula bug** — it's an economic model structural issue. The missing pieces:
1. **External aid mechanic** — Ruthenia receives 3 coins from Columbia, but maintenance still vastly exceeds total income
2. **Wartime economy modifier** — defense-driven deficits should have lower inflation multiplier than peacetime deficits
3. **Siege resilience needs amplification** — +0.10 offsets only ~10% of the negative delta for sanctioned autocracies. Need +0.30-0.50.
4. **Debt forgiveness / restructuring** — no mechanism for countries to reduce accumulated debt burden

---

## NEW DESIGN ISSUES (Tests 2-4, 7)

| # | Issue | Test | Severity | Fix |
|---|-------|------|----------|-----|
| 1 | Crisis GDP multiplier backwards | 7 | CRITICAL | Amplify negative growth, dampen positive |
| 2 | Columbia oil windfall too large | 1 | HIGH | Cap or use fixed production, not GDP-scaled |
| 3 | Formosa export collapse missing | 2 | HIGH | Add export_dependency field |
| 4 | Ceasefire removes siege resilience, gives no peace dividend | 4 | HIGH | Add +0.20 stability bonus on ceasefire signing |
| 5 | Collapse recovery impossible in 8 rounds | 4 | HIGH | Add recovery mechanic or allow faster debt restructuring |
| 6 | Demand destruction not GDP-weighted | 3 | HIGH | Weight by GDP share, not equal average |
| 7 | No diplomatic achievement election bonus | 4 | MEDIUM | Add ceasefire/treaty bonus to election AI score |
| 8 | Cathay semiconductor self-damage too low | 2 | CALIBRATE | formosa_dependency 0.25 → 0.35-0.40 |
| 9 | Naval parity has no blockade consequence | 2 | DESIGN | Force ratio should affect blockade effectiveness |
| 10 | Columbia prod_cap_naval = 0 in CSV | 1 | DATA | Fix CSV — Columbia should be able to build ships |
| 11 | Cathay can't reach L4 in 8 rounds | 6 | DESIGN | Start at 0.50 progress if two-way race intended |
| 12 | R&D penalizes fast-growing economies | 6 | DESIGN | investment/GDP shrinks as GDP grows |

---

## KEY METRICS (TESTS3 vs TESTS2)

### Oil Price R1
| Test Batch | Value | Notes |
|------------|-------|-------|
| TESTS2 | $198 | Instant spike, no inertia |
| **TESTS3** | **$133** | Inertia dampened. Gradual climb. **Fixed.** |

### Ruthenia Stability R8
| Test Batch | Test 5 Value | Notes |
|------------|-------------|-------|
| Old formula | 1.0 by R3 | Catastrophic |
| TESTS2 | 2.31 | Improved but slightly low |
| **TESTS3** | **1.0 by R5** | Formula caps work but economic spiral overwhelms |

### Sarmatia Stability R8
| Test Batch | Test 5 Value | Notes |
|------------|-------------|-------|
| TESTS2 | 1.0 by R8 | Too fast |
| **TESTS3** | **1.0 by R4** | Siege resilience +0.10 insufficient. Economic spiral dominates. |

### Tech Race
| Test Batch | Columbia L4 | Notes |
|------------|------------|-------|
| TESTS2 | Unreachable (13+ rounds) | R&D formula broken |
| **TESTS3** | **R4 unrestricted, R8 with rare earth L3** | **Fixed.** Rare earth now strategic. |

---

## WHAT WORKED BRILLIANTLY

1. **Oil inertia (Cal-1)** — Perfect. $80→$128→$147→$152 over 3 rounds. No single swing >$47. The 40/60 blend is exactly right.

2. **Semiconductor severity ramp** — 0.3→0.5→0.7→0.9→1.0 models stockpile depletion realistically. R1 impact is mild (stockpiles), R3+ is severe.

3. **Tech race with rare earth** — Columbia R4 unrestricted vs R8 restricted is a genuine 4-round strategic delay. The rare earth restriction is now a real weapon.

4. **Crisis states accelerate peace** — Sarmatia entering crisis forced ceasefire from R7 (TESTS2) to R5 (TESTS3). Economic pressure creates diplomatic urgency. Exactly right.

5. **Crash-test scenarios (Tests 7-8)** — Test 7 found the crisis multiplier bug that no baseline test would expose. Proves the value of adversarial testing.

6. **OPEC prisoner's dilemma** — Still works perfectly. Defection, follow-the-leader, and re-coordination all emerge naturally.

---

## PRIORITY ACTION LIST

### Must Fix (Blocks SEED Gate)
1. **Crisis GDP multiplier direction** — amplify negative growth, don't dampen it
2. **Columbia oil revenue cap** — prevent GDP-scaled windfall from making superpower immune to oil shocks
3. **Columbia prod_cap_naval** — fix CSV data so Columbia can build ships
4. **Formosa export dependency** — blockade should crash Formosa's own GDP

### Should Fix (Improves Realism)
5. **Ceasefire peace dividend** — +0.20 stability bonus when ceasefire signed
6. **Siege resilience amplification** — +0.10 → +0.30 for sanctioned autocracies
7. **Wartime economy modifier** — reduce inflation multiplier for defense-driven deficits
8. **External aid mechanic** — formalize how aid offsets maintenance for war-dependent countries
9. **Demand destruction GDP-weighting** — weight by economy size, not equal averaging
10. **Diplomatic achievement election bonus** — ceasefire broker gets support boost

### Must Fix (from Test 8 — Game Balance)
11. **Patience cannot be dominant** — if Cathay can win by waiting, the Trap dissolves. Need: (a) Helmsman legacy clock with mechanical consequence (aging/death/succession crisis if he doesn't act), (b) Columbia recovery possibility (fiscal reform actions that reduce deficit), (c) Economic convergence should plateau, not guarantee parity.
12. **Both superpowers have structural deficits from R1** — Columbia's mandatory costs (116 coins) exceed revenue (67) by 49/round. Cathay's (54) exceed revenue (37) by 17/round. Social spending should be partially discretionary (70/30 split).
13. **No military decommissioning** — countries can't shed maintenance costs by reducing forces. Need: decommission action that destroys units but saves maintenance.

### Consider (Design Decisions)
14. Cathay formosa_dependency: 0.25 → 0.35-0.40
15. Cathay AI starting progress: 0.10 → 0.50 (for two-way race)
16. Naval blockade force-ratio scaling
17. Collapse recovery mechanic
18. R&D efficiency correction for growing economies
19. Alliance erosion mechanic (alliances weaken as balance shifts)
20. Base R&D progress for L3+ countries (private sector innovation)

---

## FILES DELIVERED

```
SEED TESTS3/
├── TEST_PLAN.md
├── MASTER_ANALYSIS.md                           ← THIS FILE
├── DASHBOARD.html                               ← (building)
├── test_1_generic/TEST_1_FULL_RESULTS.md        ← 72KB, 8.0/10
├── test_2_formosa/TEST_2_FULL_RESULTS.md        ← 30KB, 8.0/10
├── test_3_gulf_gate/TEST_3_FULL_RESULTS.md      ← 27KB, 8.5/10
├── test_4_peace/TEST_4_FULL_RESULTS.md          ← 38KB, 7.5/10
├── test_5_stability/TEST_5_FULL_RESULTS.md      ← 34KB, 6.5/10
├── test_6_tech_race/TEST_6_FULL_RESULTS.md      ← 17KB, 8.5/10
├── test_7_columbia_collapse/TEST_7_FULL_RESULTS.md ← 41KB, 7.0/10
└── test_8_cathay_patience/TEST_8_FULL_RESULTS.md ← 41KB, 7.0/10 — PATIENCE DOMINANT
```

**Total test output: ~300KB of detailed analysis across 8 completed tests.**

---

## FINAL SCOREBOARD

| Test | Score | Verdict |
|------|-------|---------|
| 1. Generic Baseline | 8.0/10 | PASS |
| 2. Formosa Crisis | 8.0/10 | PASS |
| 3. Gulf Gate Economics | 8.5/10 | PASS |
| 4. Peace Negotiation | 7.5/10 | PASS (gaps) |
| 5. Stability Calibration | 6.5/10 | CONDITIONAL |
| 6. Tech Race | 8.5/10 | PASS |
| 7. Columbia Overstretch | 7.0/10 | PASS (bugs) |
| 8. Cathay Patience | 7.0/10 | PASS (design issue) |
| **Average** | **7.6/10** | |

**20 total design issues identified: 5 critical/game-breaking, 7 high, 8 medium/design.**

*SEED TESTS3 complete. All 8 tests delivered. Dashboard building.*
