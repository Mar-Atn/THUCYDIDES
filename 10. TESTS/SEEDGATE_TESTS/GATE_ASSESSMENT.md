# SEED GATE ASSESSMENT — Independent Tester Verdict
**Date:** 2026-03-30 | **Tester:** Independent Claude Code Instance
**Tests Run:** 11 (T1-T9, T11-T12) | ~80 rounds simulated | v4 engine

---

## VERDICT: CONDITIONAL PASS

**The SEED design is architecturally sound, narratively rich, and mechanically functional. It produces credible geopolitical dynamics across all tested scenarios. However, 21 issues were found — 4 blockers, 10 high priority, 7 medium/low — that must be addressed before the gate can be fully passed.**

**Engine Credibility: 6.9/10** (average across all tests)

---

## SCOREBOARD

| Test | Focus | Score | Verdict |
|------|-------|:-----:|---------|
| T1 | Baseline (full integration) | 7.0 | CONDITIONAL |
| T2 | Formosa Crisis | 7.2 | CONDITIONAL |
| T3 | Sanctions Stress | 6.8 | CONDITIONAL |
| T4 | Nuclear Escalation | 7.5 | CONDITIONAL |
| T5 | Economic Warfare | 7.0 | CONDITIONAL |
| T6 | Political Crisis | 6.0 | CONDITIONAL |
| T7 | Covert Operations | 6.0 | CONDITIONAL |
| T8 | Ruthenia Survival | — | CONDITIONAL |
| T9 | Role Engagement | — | CONDITIONAL |
| T11 | Consistency Check | 12/16 | PROCEED |
| T12 | Full Stress | — | CONDITIONAL |

---

## BLOCKERS (4) — Must fix before gate PASS

| # | Issue | Source | Description |
|---|-------|--------|-------------|
| **B1** | No naval combat mechanic | T2 | Ships are invulnerable. Cannot contest blockades with force. The Formosa scenario requires ship-vs-ship resolution. |
| **B2** | Persia nuclear auto-breakout | T4 | countries.csv has nuclear_rd_progress=0.60 which equals the L0→L1 threshold. Persia achieves L1 at R1 with zero investment. Must reduce to ~0.30. |
| **B3** | Court AI formula undefined | T6 | Democracy's key check on executive power has no formula. Impeachment, contested arrests, contested elections — all route through Court but Court has no decision logic. |
| **B4** | Per-individual intelligence pools not implemented | T7 | D8 spec and G spec describe per-individual pools (Shadow: 8 intel, 3 sabotage, 3 cyber). Engine code uses country-level limits only. 3 related issues: accuracy tiers missing, failed espionage returns nothing (should return low-accuracy), detection=attribution (should be separate). |

---

## HIGH PRIORITY (10) — Should fix before gate PASS

| # | Issue | Source | Description |
|---|-------|--------|-------------|
| H1 | Combat modifier stacking | T1 | Die Hard (+1) + air support (+1) = defenders win 83%. Amphibious at Formosa ~8% success. Too heavy. |
| H2 | Columbia structural deficit | T1 | Mandatory costs (91.6) exceed revenue (67) from R1. Columbia can't cover expenses. |
| H3 | Sanctions formula ambiguity | T1, T3 | 1.5× multiplier unclear — applied once or twice? Potentially 50%+ GDP hits. |
| H4 | Imposer cost negligible | T3 | Teutonia loses 0.02 coins from L3 sanctions on Sarmatia. Should be 0.1-0.5 (10-50× higher). |
| H5 | Election formula missing crisis modifiers | T6 | Arresting opposition, impeachment, political crisis have no direct election effect. |
| H6 | Arrest cost spec vs code mismatch | T6 | Spec says 0 cost, code applies -1 stability / -3 support. Reconcile. |
| H7 | Semiconductor GDP cap needed | T12 | -29% single-round GDP crash at severity 0.9. Cap at ~10%/round. |
| H8 | Persia has 0 strategic missiles | T12 | Cannot deliver nuclear weapons despite having capability. Needs at least 1 missile. |
| H9 | Ruthenia aid dependency razor-thin | T8 | Single-round aid delay = fiscal death. Add automatic baseline EU aid or facilitator guidance. |
| H10 | Sage/Dawn activation thresholds too high | T9 | Both roles idle for multiple rounds. Lower thresholds so players have mechanical actions from R1. |

---

## MEDIUM / LOW (7) — Fix or document before gate

| # | Issue | Source | Priority |
|---|-------|--------|----------|
| M1 | Dollar/BRICS+ currency no pathway | T5 | MEDIUM — only via Columbia money printing, no structural mechanism |
| M2 | OPEC per-member impact too small | T5 | MEDIUM — MIN nearly irrelevant vs chokepoint disruption |
| M3 | No post-impeachment state change formula | T6 | MEDIUM |
| M4 | Propaganda diminishing returns code vs spec | T6 | MEDIUM |
| M5 | Detection/attribution not separated in code | T7 | MEDIUM |
| M6 | Columbia starts at 38% support (below 40% protest threshold) | T6 | LOW — may be intentional design |
| M7 | 80× money printing multiplier may be too aggressive | T5 | LOW/CALIBRATE |

---

## WHAT WORKS BRILLIANTLY

1. **Authorization chain asymmetry** (T4) — Autocracy sole authority vs democracy 3-person chains. Creates first-strike instability, command pressure, moral dilemmas. The strongest design element.

2. **Narrative emergence** (T1) — 8 rounds produce a credible geopolitical arc: wars, ceasefires, elections, regime changes, economic crises — all from independent agent decisions, not scripted.

3. **Nuclear deterrence** (T4) — Air defense interception (83% with 3 AD units) makes single-missile strikes unreliable. Shifts deterrence from guaranteed destruction to probabilistic risk. Brilliant.

4. **Intelligence pool depletion** (T7) — Per-individual card design (when implemented) creates genuine scarcity. Sarmatia goes operationally dark by R7 while Columbia retains 50%. Excellent asymmetry.

5. **Impeachment-to-succession cascade** (T6) — Three presidents in 5 rounds. Mechanically clean, narratively dramatic.

6. **Sanctions adaptation** (T3) — S-curve with adaptation after 4 rounds produces realistic "sanctions fatigue." Countries adapt. Effectiveness declines.

7. **Ceasefire mechanics** (T1) — Agent-driven negotiations produce ceasefires without forcing functions. Peace is possible but difficult. Exactly right.

8. **Economic feedback loops** (T5) — Oil → GDP → demand destruction → price correction. The system self-corrects. Realistic.

---

## COMPARISON TO PREVIOUS TEST ROUNDS

| Metric | TESTS2 (Mar 27) | TESTS3 (Mar 28) | GATE (Mar 30) | Trend |
|--------|:---------------:|:---------------:|:-------------:|:-----:|
| Engine credibility | ~6.5 | 7.6 | 6.9 | ↕ (new mechanics added, new issues found) |
| Oil price dynamic | Static 68-72 | Responsive $82-250 | Responsive $118-198 | ✓ Fixed |
| Stability calibration | Ruthenia 1.0 R3 | Ruthenia 2.31 R8 | Ruthenia ~2.5 R6 | ✓ Improved |
| Tech race | L4 unreachable | L4 at R4-R8 | L4 still slow | → Same issue |
| Ceasefires | Not possible | R5-R7 | R6 | ✓ Working |
| Elections | Firing | Firing with crisis mods | Firing, missing crisis mods | ↓ Regression |
| Action coverage | 18/30 | 20/30 | 20/31 | → Similar |
| New mechanics | — | — | Militia, Court, Impeachment, Protest | + Added |
| Naval combat | Not tested | Not tested | **MISSING** | ! New blocker |

**The engine improved on oil, stability, and ceasefires. But the action review introduced new mechanics (court, intelligence pools, militia) that are specified but not fully implemented in code. This is the primary gap.**

---

## RECOMMENDATION

### For SEED Gate: CONDITIONAL PASS

**Pass conditions (must fix before declaring SEED complete):**

**Tier 1 — Fix immediately (4 blockers):**
1. Add naval combat resolution (even simplified: dice + modifiers like ground combat)
2. Fix Persia nuclear_rd_progress to 0.30 in countries.csv
3. Define Court AI decision formula (even simple: probability based on legality + stability + support)
4. Implement per-individual intelligence pools in engine (or document as Detailed Design deliverable)

**Tier 2 — Fix this week (top 5 high-priority):**
5. Reduce combat modifier stacking (cap total modifier at ±2)
6. Fix Columbia structural deficit (reduce mandatory social or increase tax rate)
7. Clarify sanctions 1.5× formula in D8 with worked example
8. Increase imposer cost multiplier 10×
9. Add election crisis modifiers (arrest → -5 incumbent, impeachment → -10)

**Tier 3 — Fix before first live SIM (remaining):**
10-21. All remaining high/medium items

### For proceeding to WEB APP DEVELOPMENT: GO

The SEED design is complete enough to begin web app implementation. The issues found are **calibration and implementation gaps**, not architectural problems. The data model, API contracts, action system, and UI specs are solid. Development can proceed while the engine team fixes the issues above.

---

## FILES DELIVERED

```
SEEDGATE_TESTS/
├── GATE_TEST_PLAN.md
├── SCENARIOS.md
├── GATE_ASSESSMENT.md               ← THIS FILE
├── T11_CONSISTENCY_CHECK.md
├── test_T1_baseline/TEST_T1_RESULTS.md
├── test_T2_formosa/TEST_T2_RESULTS.md
├── test_T3_sanctions/TEST_T3_RESULTS.md
├── test_T4_nuclear/TEST_T4_RESULTS.md
├── test_T5_economic/TEST_T5_RESULTS.md
├── test_T6_political/TEST_T6_RESULTS.md
├── test_T7_covert/TEST_T7_RESULTS.md
├── test_T8_ruthenia/TEST_T8_RESULTS.md
├── test_T9_roles/TEST_T9_RESULTS.md
└── test_T12_stress/TEST_T12_RESULTS.md
```

---

*SEED Gate Assessment complete. 11 tests, ~80 rounds, 21 issues found (4 blockers, 10 high, 7 medium/low). Conditional pass. Web app development can proceed. Engine fixes required in parallel.*
