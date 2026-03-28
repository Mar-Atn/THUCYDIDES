# SEED TESTS2 — MASTER ANALYSIS REPORT
## 6 Tests × 8 Rounds | 48 Rounds Simulated | 37 Independent Roles
**Date:** 2026-03-27 | **Tester:** Independent Claude Code Instance
**Method:** Real Claude agents playing each role independently, engine formulas applied manually

---

## EXECUTIVE SUMMARY

Six focused tests were run against the updated SEED engine (v4 stability, v2 oil formula, ceasefire mechanic, semiconductor disruption, rare earth restrictions). **The core simulation architecture works.** The Thucydides Trap dynamics emerge naturally. Wars can start, escalate, and — with the new mechanic — end. The oil economy creates genuine strategic pressure. Elections fire and produce regime changes.

**However, 14 design issues were identified, including 3 critical bugs and 5 calibration fixes needed before the SEED gate.**

---

## TEST RESULTS AT A GLANCE

| Test | Verdict | Key Finding |
|------|---------|-------------|
| **1. Generic Baseline** | **PASS** | Full 8-round arc. Cathay blockades Formosa R4 (after purge lifts + L3 nuclear). Persia ceasefire R4. Heartland ceasefire R7. Columbia election R5 (Anchor wins). Formosa resolved R7 via TSMC JV framework. Oil $237→$82. |
| **2. Formosa Crisis** | **PASS** | Cathay blockades R3 (purge lifts). NEVER invades (4:1 ratio impossible). Semiconductor disruption fires. Blockade self-limiting (Cathay treasury depletes in 5 rounds). |
| **3. Gulf Gate Economics** | **PASS** | Oil formula well-calibrated. $221→$250(cap)→$117 trajectory. OPEC prisoner's dilemma works. Blockade enriches Nordostan (emergent). |
| **4. Peace Negotiation** | **PASS (with gaps)** | Ceasefire achieved R7. Transaction engine works. 9 design holes found, 3 Priority 1 (breach, territory freeze, ally coverage). |
| **5. Stability Calibration** | **CONDITIONAL PASS** | Heartland 5.0→2.31 (vs old 1.0 by R3). But Nordostan collapses faster than Heartland — wrong. 3 formula fixes needed. |
| **6. Tech Race** | **FAIL — CRITICAL BUG** | Columbia CANNOT reach AI L4 in 8 rounds. R&D formula too slow. Cathay AI data bugged (auto-promotes R1). Rare earth restrictions have no strategic impact. |

---

## CRITICAL ISSUES (Must Fix Before SEED Gate)

### BUG 1: Tech R&D Formula Too Slow (Test 6)
**Severity:** CRITICAL
**Problem:** The R&D formula `(investment/GDP) × 0.5` produces ~3.2% progress per round for Columbia. The 40-point gap from L3 (60%) to L4 (100%) requires ~13 rounds unrestricted — far beyond the 8-round game. Rare earth restrictions (which slow this to ~1.7%/round) are meaningless because the goal is already unreachable.
**Impact:** The entire tech race mechanic is non-functional. The +30% GDP at L4 and +2 combat bonus are phantom rewards no one can reach. Rare earth restrictions are "flavor, not strategy."
**Fix:** Start Columbia AI at 0.80 progress (not 0.60) AND increase R&D multiplier from 0.5 to 0.8. This makes L4 reachable in ~4 rounds unrestricted, ~8 rounds with L3 rare earth restriction. The restriction becomes the strategic fulcrum.

### BUG 2: Cathay AI Starting Data Inconsistency (Test 6)
**Severity:** CRITICAL
**Problem:** Cathay starts at AI L2 with 0.70 ai_rd_progress. But the L2→L3 threshold is 0.60. Cathay should auto-promote to L3 on the first engine tick (or start at L3 with 0.10 progress toward L4).
**Fix:** Either set Cathay ai_rd_progress to 0.10 (already L3) or set threshold L2→L3 higher.

### BUG 3: Inflation Stability Penalty Applied to Absolute Level (Test 5)
**Severity:** HIGH
**Problem:** The stability formula applies inflation friction to absolute inflation, not change from start. Countries starting with high inflation (Persia 50%, Caribe 60%, Phrygia 45%) would collapse in R1 from inflation penalties alone before any war or sanctions effects.
**Fix:** Apply inflation stability friction to *change from starting inflation*, not absolute level. Countries adapted to their baseline inflation.

---

## CALIBRATION FIXES NEEDED

### FIX 1: Nordostan Stability Decays Too Fast (Test 5)
**Problem:** Nordostan hits 1.0 (floor) by R8 — faster than Heartland (2.31). Historically implausible: autocracies are MORE resilient to war stress, not less.
**Root cause:** L3 sanctions create -0.30/round persistent drain with no autocratic equivalent to democratic resilience (+0.15).
**Fix:** Add "siege resilience" mechanic: heavily sanctioned autocracies gain +0.10/round stability bonus (institutional adaptation to sanctions regime). Alternative: reduce sanctions stability impact for autocracies.

### FIX 2: Persia GDP Contraction Penalty Too Harsh (Test 5)
**Problem:** Growth rate of -3.0% produces -0.90 stability penalty per round (growth × 0.3 when < -2%). Persia hits floor by R4.
**Fix:** Cap GDP contraction stability penalty at -0.30/round.

### FIX 3: Oil Price Formula Starting Level (Test 1, 3)
**Problem:** Design team expected ~$140+ at R1. Formula produces $198-237 depending on Gulf Gate status. The multiplicative stacking of 5 factors compounds faster than expected.
**Status:** Tests show the range is actually realistic for a major chokepoint blockade + 2 wars + sanctions. Recommend accepting $198 as correct and adjusting expectations, OR reducing one of the multipliers slightly (e.g., speculation from +5%/crisis to +3%/crisis).

### FIX 4: Columbia Resource Sector (Test 3)
**Problem:** Columbia's 5% resource sector may understate its oil producer parallel. This affects how much Columbia benefits from high oil prices (producer hedge).
**Action:** Verify with SIMON whether 5% is intentional. If Columbia parallels the world's largest oil producer, 10-15% might be more appropriate.

### FIX 5: $250 Oil Cap Hard vs Soft (Test 3)
**Problem:** Hard cap at $250 creates a plateau where further disruption has no additional effect. Dual chokepoint disruption (Gulf Gate + Formosa) produces formula values of $258+ — all clamped to $250.
**Fix:** Consider soft cap (asymptotic approach to $250) to preserve marginal incentives: `price = 250 × (1 - e^(-raw_price/250))`.

---

## DESIGN GAPS IDENTIFIED

### GAP 1: Ceasefire Breach Mechanic Missing (Test 4 — Priority 1)
The ceasefire transaction ends wars, but there's no code to detect violations, freeze territory, or enforce automatic re-declaration if terms are breached.

### GAP 2: Territory Freeze Not Stored (Test 4 — Priority 1)
When a ceasefire is signed, the current front line should be stored as `ceasefire_line` in the agreement data structure. Currently not tracked.

### GAP 3: Ally Coverage in Ceasefire Undefined (Test 4 — Priority 1)
Choson has 2 ground units fighting alongside Nordostan. A Nordostan-Heartland ceasefire does not automatically cover Choson. Must either require all-party signature or add `covers_allies` flag.

### GAP 4: TSMC Kill Switch Not Mechanized (Test 2)
Circuit's intelligence about TSMC's destruction protocol is narrative-only. Should be a mechanic: if Formosa is invaded (not blockaded), semiconductor production is destroyed with X% probability, reducing global tech supply permanently.

### GAP 5: Overstretch Index Not Formalized (Test 1, 2)
Shield's assessment ("67 units, 17 zones, zero reserve") is role-play, not engine. Consider a formal overstretch index that triggers mechanical penalties when force-to-commitment ratio drops below threshold.

### GAP 6: Non-HoS Role Mechanical Impact Still Limited (Test 1)
Tribune, Challenger, Broker, Dawn, Sage — all produced rich role-play but zero mechanical country-level outcomes. The design intent is there but engine support is missing. Tribune should be able to block budgets, Challenger should create foreign policy commitments, etc.

---

## WHAT WORKED WELL

### 1. Thucydides Trap Dynamics Emerge Naturally
Cathay's window calculation (R3-R5 optimal, constrained by purge penalty + nuclear L3) ran independently in every test. The gap ratio closed from 0.679 toward 0.82-0.85 over 8 rounds. The structural tension between Cathay's rising power and Columbia's overstretch IS the game.

### 2. Oil Economy Creates Genuine Strategic Pressure
The Gulf Gate blockade is the most consequential single action in the SIM economy. It drives oil to $200+, funds Nordostan's war, crushes importers, motivates Columbia to assault the chokepoint, and creates OPEC prisoner's dilemmas. Exactly right for a geopolitical SIM.

### 3. Elections as Forcing Functions
Columbia midterms (R2), Heartland wartime election (R3-4), and Columbia presidential (R5) all created genuine decision pressure. In Test 4, the Heartland election was the turning point — Bulwark replacing Beacon enabled the ceasefire. Elections work.

### 4. Independent Agent Behavior
37 roles across 7 agent groups produced genuinely independent decisions. Internal team tensions (Dealer vs Shield, Helmsman vs Sage, Beacon vs Bulwark vs Broker, Furnace vs Anvil vs Dawn) created realistic faction dynamics without orchestrator intervention. No agent "helped" their country succeed.

### 5. Ceasefire Mechanic Functions
The core transaction works — wars end, combat stops, stability begins recovering. The 7-round negotiation arc in Test 4 mirrors real peace processes with back-channels, elections, creative formulas, and institutional workarounds.

### 6. 4:1 Amphibious Ratio as Hard Constraint
Cathay NEVER invaded Formosa in Test 2 because the 4:1 ratio is mathematically impossible with available forces. This forces Cathay into blockade (which triggers semiconductor disruption but doesn't capture the island). The constraint creates the strategic dilemma the design intended.

### 7. Blockade Self-Limiting
Cathay's Formosa blockade depleted its treasury from 40 to 2 coins in 5 rounds. Blockade is economically unsustainable long-term. This creates a natural time pressure on both sides — Cathay must achieve objectives before running out of money, Formosa must survive until Cathay withdraws. Emergent and excellent.

---

## KEY METRICS ACROSS TESTS

### Oil Price Trajectory
| Round | Test 1 | Test 2 | Test 3 | Test 4 | Test 5 | Test 6 |
|-------|--------|--------|--------|--------|--------|--------|
| R1 | $198 | $198 | $221 | $198 | $198 | $198 |
| R4 | $180 | $250 | $250 | ~$180 | ~$175 | ~$185 |
| R8 | **$82** | $250 | $117 | ~$120 | ~$130 | ~$160 |
| Arc | Blockade→ceasefire→normal | Blockade+Formosa→sustained | Full blockade cycle | Peace dividend | Slow normalization | Tech focus, less oil drama |

**Verdict: Oil is NOT static.** Range across tests: $82-$250. Formula responds to blockades, ceasefires, OPEC, and sanctions. The old 68-72 static bug is definitively fixed.

### Heartland Stability
| Round | Test 1 | Test 4 | Test 5 | OLD Formula |
|-------|--------|--------|--------|-------------|
| R1 | 4.62 | 4.62 | 4.62 | ~4.0 |
| R3 | ~4.0 | 4.20 | 3.97 | **1.0** |
| R8 | ~4.0 | 5.55 (ceasefire R7) | 2.31 | 1.0 |

**Verdict: Heartland does NOT hit 1.0 by R3.** The stability fix works. Democratic resilience + society adaptation produce realistic gradual decline. Ceasefire enables recovery (Test 4: 4.20→5.55).

### Gap Ratio (Cathay/Columbia GDP)
| Round | Test 1 | Test 2 | Test 6 |
|-------|--------|--------|--------|
| Start | 0.679 | 0.679 | 0.679 |
| R1 | 0.693 | 0.693 | 0.693 |
| R8 | ~0.85 | ~0.82 | 0.819 |

**Verdict: Gap closes consistently across all tests.** Cathay approaches but does not overtake Columbia in 8 rounds. The power transition is visible and varied.

### Naval Ratio (Cathay/Columbia)
| Round | Test 1 | Test 2 |
|-------|--------|--------|
| Start | 0.60 | 0.60 |
| R1 | 0.778 | 0.778 |
| R3 | **1.00** | **1.00** (parity) |
| R8 | **1.56** (14/9) | ~1.44 |

**Verdict: Cathay achieves naval superiority by R3-R4 in every test.** Columbia's flat 10 (no production) vs Cathay's +1/round creates inevitable crossover. **Design concern: Columbia produced ZERO new naval units in Test 1's 8 rounds — unrealistic for the world's largest navy. Need minimum production floor.**

### Events Fired
| Event | T1 | T2 | T3 | T4 | T5 | T6 |
|-------|----|----|----|----|----|----|
| R2 Midterms | Yes (incumbent barely survives 52.6%) | Yes | Yes | Yes | Yes | Yes |
| R3 Heartland Election | Yes (Beacon survives 54.6%) | Yes | Yes | Yes (Bulwark wins) | Yes | Yes |
| R5 Presidential | Yes (**Anchor wins** 52.0%) | Yes (opposition wins) | Yes | Yes | Yes | Yes |
| Ceasefire (any) | **R4 Persia + R7 Heartland** | No | R5 Persia | R7 Heartland + R5 Persia | No | No |
| Formosa Blockade | **R4** | **R3** | R4 (brief) | No | No | No |
| Nuclear Use | 0 | 0 | 0 | 0 | 0 | 0 |
| Semiconductor Disruption | **R4-R7** | **R3-R8** | R4 (brief) | No | No | No |

**Verdict: Elections fire in ALL tests. Nuclear deterrence holds (0 use across 48 rounds). Ceasefires emerge in tests with favorable conditions. Formosa blockade occurs when Cathay is aggressive enough.**

---

## PRIORITY ACTION LIST FOR DESIGN TEAM

### Must Fix (Blocks SEED Gate)
1. **Tech R&D formula recalibration** — Columbia AI 0.80 start + multiplier 0.5→0.8
2. **Cathay AI starting data** — fix 0.70 progress vs 0.60 threshold inconsistency
3. **Inflation stability penalty** — apply to change from baseline, not absolute level
4. **Ceasefire breach mechanic** — add `check_agreement_compliance()` to transaction engine
5. **Ceasefire territory freeze** — store `ceasefire_line` in agreement data

### Should Fix (Improves Realism)
6. **Nordostan siege resilience** — add +0.10/round for sanctioned autocracies
7. **Persia GDP contraction cap** — limit stability penalty to -0.30/round
8. **Soft oil cap** — asymptotic approach to $250 instead of hard clamp
9. **Ally coverage in ceasefire** — `covers_allies` flag or require all-party signature
10. **TSMC kill switch mechanization** — probability-based fab destruction on invasion

### Should Fix (from Test 1)
11. **Columbia naval production floor** — Columbia built ZERO naval units in 8 rounds (budget went to Persia war + tech). Need minimum production or maintenance-includes-replacement mechanic. A navy that shrinks from 10 to 9 and never recovers is unrealistic.
12. **Election AI score needs crisis modifiers** — Oil price shocks and active wars should penalize incumbents more explicitly. Current formula produces close results (52-55%) regardless of conditions.
13. **Semiconductor disruption should scale with duration** — Currently binary (disrupted/not). Should model stockpile depletion: R1 of blockade = mild impact, R3+ = severe as chip inventories empty.
14. **Ceasefire needs automatic stability/tiredness effects** — Currently the engine stops combat but doesn't give a "peace dividend" bonus to stability or reduce war tiredness faster.

### Consider (Design Decisions)
15. Columbia resource sector: 5% → 10%?
16. Overstretch index formalization
17. Non-HoS role mechanical impact (Tribune budget block, etc.)
18. Cathay nuclear start: 80% → 90% (makes L3 achievable by R4)

---

## TESTER VERDICT

**The simulation works.** The 10 engine changes (naval rebalance, water hexes, Gulf Gate active, stability fix, semiconductor disruption, rare earth, oil formula, ceasefire, theater deployments, Cathay naval positioning) collectively produce a dramatically more credible simulation than the previous test battery.

**The Thucydides Trap is real in this SIM.** The gap closes. The window opens and narrows. Both sides face genuine dilemmas. Neither can predict the other's timing. Miscalculation is possible. This IS the design intent, and it works.

**3 critical bugs must be fixed** (tech R&D, Cathay AI data, inflation formula). **5 calibration adjustments** would improve realism. **6 design gaps** need attention before Detailed Design.

**Recommended next step:** Fix the 3 critical bugs, re-run Tests 5 and 6 to validate. Then proceed to SEED gate review with VERA cross-checking all 50 checklist items.

---

## FILES DELIVERED

```
SEED TESTS2/
├── TEST_PLAN.md                           ← Test battery plan
├── MASTER_ANALYSIS.md                     ← THIS FILE
├── DASHBOARD_TEMPLATE.md                  ← Comparison template
├── test_1_generic/
│   └── round_1/
│       ├── world_state_r1.md              ← Starting state
│       ├── team_columbia_r1.md            ← 7-role deliberation
│       ├── team_cathay_r1.md              ← 5-role deliberation
│       ├── team_nordostan_r1.md           ← 3-role deliberation
│       ├── team_heartland_r1.md           ← 3-role deliberation
│       ├── team_persia_r1.md              ← 3-role deliberation
│       ├── team_europe_r1.md              ← 6-role deliberation
│       ├── solo_countries_r1.md           ← 10-role deliberation
│       ├── round_1_phase_a_summary.md     ← Decision collision map
│       └── engine_results_r1.md           ← Engine processing
│   └── TEST_1_FULL_RESULTS.md             ← R2-R8 complete (1,908 lines)
├── test_2_formosa/TEST_2_FULL_RESULTS.md  ← 8 rounds, Formosa blockade R3
├── test_3_gulf_gate/TEST_3_FULL_RESULTS.md ← 8 rounds, oil economics
├── test_4_peace/TEST_4_FULL_RESULTS.md    ← 8 rounds, ceasefire R7
├── test_5_stability/TEST_5_FULL_RESULTS.md ← 8 rounds, formula validation
└── test_6_tech_race/TEST_6_FULL_RESULTS.md ← 8 rounds, R&D dynamics
```

---

*SEED TESTS2 complete. 48 rounds simulated. 14 design issues identified. 3 critical, 5 calibration, 6 gaps. Filed for design team review.*
