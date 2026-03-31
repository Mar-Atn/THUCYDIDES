# SEED GATE TEST PLAN
## Independent Tester Assessment — Pre-Gate Validation
**Date:** 2026-03-30 | **Tester:** Independent Claude Code Instance
**SEED Status:** 44/50 (88%) | 3 in progress | 7 frozen
**Verdict:** CONDITIONAL GO — 6 issues found, 1 blocker

---

## TESTER ASSESSMENT: STATE OF SEED

The SEED phase is **substantially complete**. Since my last test round (TESTS3, March 28), the team delivered:
- Complete action review (31 actions, one-by-one with Marat) — CM-002
- Web app spec G2-G5 (50K integrated spec)
- Engine formula docs D8 (102K audit reference)
- Data architecture F2-F4 (data model, flows, API contracts)
- AI assistant "Argus" prompts (E4)
- World context narrative (A3)
- Relationship matrix (B3, 87 relationships + interactive graph)
- Artefact + print templates (H3, H4)
- 12 engine fixes + 4 calibration patches
- 5 change management entries (properly documented)
- UX Style Guide frozen (H1)

**The engine has been revised significantly since TESTS3.** The action review changed combat modifiers, blockade logic, nuclear system (5-tier), intelligence pools, sanctions S-curve, OPEC 5-level, and added militia/volunteer, court, impeachment, protest mechanics. **These changes have NOT been tested by independent AI agents yet.**

---

## 6 ISSUES FOUND IN AUDIT

| # | Issue | Severity | Description |
|---|-------|----------|-------------|
| 1 | **Formosa amphibious discrepancy** | BLOCKER | D8 says 3:1 ratio, ACTION_REVIEW says "no assault viable, blockade only", code unclear. Must resolve before gate. |
| 2 | **Expansion role completeness** | MEDIUM | 4 expansion roles in CSV but relationship matrix may be incomplete for them. |
| 3 | **Semiconductor ramp location** | MEDIUM | D8 documents formosa_disruption_rounds counter but code location unclear after engine rewrite. |
| 4 | **Columbia oil revenue cap** | LOW | FIX-11 mentioned in test results but not in main D8 formula spec. |
| 5 | **Theater activation mechanism** | MEDIUM | C7 references "if theater active" but no documented trigger mechanism. |
| 6 | **31 new/revised actions untested** | HIGH | Complete action review changed the engine significantly. No AI agent tests run since. |

---

## GATE TEST BATTERY — 10 Tests

### Test Approach
- **Real AI agents** (Claude instances) playing all 37 roles independently
- **v4 engine** with all 12 fixes + 4 calibration patches + action review changes
- **Focus:** Validate the REVISED mechanics, not repeat baseline dynamics
- **Cold and objective** — expose holes, not smooth them

### Tests

| # | Name | Rounds | Focus | What Changed Since TESTS3 |
|---|------|:------:|-------|--------------------------|
| G1 | **ACTION VALIDATION: Combat** | 4 | Test revised ground attack (simplified modifiers, dice-based), amphibious (-1 modifier), naval bombardment | New combat system from CM-002 |
| G2 | **ACTION VALIDATION: Blockade & Oil** | 4 | Test ground-only blockade, partial/full Formosa blockade, 5-level OPEC | Blockade rewrite + OPEC 5-level |
| G3 | **ACTION VALIDATION: Nuclear** | 4 | Test 5-tier nuclear system, 10-min authorization clock, 10-min flight time, interception | Complete nuclear rewrite |
| G4 | **ACTION VALIDATION: Intelligence & Covert** | 4 | Test per-individual intelligence pools, always-returns-answer, accuracy variation, sabotage, cyber, disinformation | Intelligence rewrite |
| G5 | **ACTION VALIDATION: Political** | 6 | Test court (AI judge for democracies), impeachment (Columbia/Ruthenia), protest (auto + stimulated), coup (betrayal mechanic) | New political mechanics |
| G6 | **FULL INTEGRATION: Generic Baseline** | 8 | Full 37-agent run with ALL revised mechanics. Validate the complete system works together. | Everything changed — this is the comprehensive test |
| G7 | **SANCTIONS S-CURVE** | 6 | Test new sanctions model (S-curve coalition effectiveness). Does 60% coverage threshold still work? Does adaptation after 4 rounds function? | Sanctions formula revised |
| G8 | **MILITIA & MOBILIZATION** | 6 | Test new militia/volunteer call mechanic + finite depletable mobilization pool. Ruthenia scenario: can militia defend when regular forces depleted? | New mechanic (CM-001) |
| G9 | **ROLE ENGAGEMENT** | 8 | Focus on non-HoS roles: Tribune (impeachment power), Challenger (campaign), Dawn (reform), Sage (party meeting), Broker (back-channel). Do they have meaningful mechanical impact now? | Action review gave non-HoS roles new tools |
| G10 | **TIMING & FEASIBILITY** | 4 | Run 4 rounds with realistic timing. How long does Phase A actually take with 37 agents making 31 action types? Is the 45-80 min window feasible? | Phase B/C merge (CM-003), new action volume |

### Test Priorities
1. **G6 (Full Integration)** — most important, tests everything together
2. **G1-G4 (Action Validation)** — validate the revised mechanics individually
3. **G5 (Political)** — new mechanics need validation
4. **G8 (Militia)** — new mechanic, untested
5. **G9 (Role Engagement)** — addresses the biggest design concern from TESTS2/3
6. **G7, G10** — calibration and feasibility

---

## CONSISTENCY CHECKS (automated, before running tests)

### CSV Cross-Validation
- [ ] Every country_id in roles.csv exists in countries.csv
- [ ] Every country_id in deployments.csv exists in countries.csv
- [ ] Every zone_id in deployments.csv exists in zones.csv
- [ ] Every zone in zone_adjacency.csv exists in zones.csv
- [ ] Every org_id in org_memberships.csv exists in organizations.csv
- [ ] Sum of military units in deployments.csv matches countries.csv totals per country
- [ ] All 37 playable roles have entries in relationships.csv
- [ ] No orphan records in any CSV

### Formula vs Code Spot-Checks
- [ ] Oil price formula (D8 Step 1 vs world_model_engine.py)
- [ ] GDP growth formula (D8 Step 2 vs code)
- [ ] Sanctions S-curve (D8 Step 3 vs code)
- [ ] Stability formula (D8 Step 6 vs code)
- [ ] Ground attack resolution (D8 Combat vs live_action_engine.py)
- [ ] Blockade resolution (D8 vs code)
- [ ] Nuclear 5-tier (D8 vs code)
- [ ] Election formula (D8 vs code)
- [ ] All 12 FIX values match between D8 and code

### Authority Chain Verification
- [ ] Every action in G spec has an authorization rule
- [ ] Every role's powers in B2 map to actions in G spec
- [ ] Nuclear authorization requires 3 roles (HoS + military chief + 1)
- [ ] Intelligence pools assigned to correct roles in roles.csv

---

## SUCCESS CRITERIA

### For SEED Gate PASS:
1. **G6 (Full Integration)** produces 8 rounds of credible dynamics — no engine crashes, no absurd outcomes
2. **All 31 action types** fire correctly when triggered by AI agents
3. **No cross-file inconsistencies** found in CSV validation
4. **Formula spot-checks** show <5% deviation between D8 spec and code output
5. **Oil price, stability, GDP** trajectories are within expected corridors (from dependency scenarios)
6. **Elections fire** at scheduled rounds with correct formula
7. **Ceasefire/peace** mechanic works end-to-end
8. **New mechanics** (militia, court, impeachment, protest, betrayal) resolve without errors
9. **Non-HoS roles** produce at least 1 meaningful mechanical action per test

### For SEED Gate CONDITIONAL PASS:
- 1-2 mechanics fail but are isolated and fixable
- Core dynamics (oil, GDP, stability, military) work correctly
- Issue list documented with severity ratings

### For SEED Gate FAIL:
- Engine produces absurd results (GDP doubling, instant collapse, static oil)
- Multiple actions don't resolve
- Cross-file inconsistencies affect gameplay
- Formula spec and code fundamentally disagree

---

## OUTPUT STRUCTURE

```
SEEDGATE_TESTS/
├── GATE_TEST_PLAN.md                    ← THIS FILE
├── CONSISTENCY_CHECK.md                 ← CSV + formula validation results
├── test_G1_combat/
│   └── TEST_G1_RESULTS.md
├── test_G2_blockade/
│   └── TEST_G2_RESULTS.md
├── ... (G3-G10)
├── GATE_ASSESSMENT.md                   ← Final tester verdict
└── DASHBOARD.html                       ← Visual comparison of all 10 tests
```

---

## EXECUTION PLAN

**Phase 1: Consistency checks** (automated, ~30 min)
Run CSV cross-validation + formula spot-checks. Document in CONSISTENCY_CHECK.md.

**Phase 2: Action validation tests G1-G5** (parallel, focused scenarios)
Each tests specific revised mechanics with targeted scenarios.

**Phase 3: Full integration test G6** (sequential, 8 rounds, all 37 agents)
The comprehensive test. Most important.

**Phase 4: Specialized tests G7-G10** (parallel, targeted)
Sanctions, militia, role engagement, timing.

**Phase 5: Assessment** (synthesis)
Compile all results into GATE_ASSESSMENT.md with PASS/CONDITIONAL/FAIL verdict.

---

*Ready to execute on your command, Marat. Shall I start with Phase 1 (consistency checks) and then launch all tests?*
