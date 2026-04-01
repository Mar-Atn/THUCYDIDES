# DET_E4 -- Testing Architecture v1

**Version:** 1.0 | **Date:** 2026-04-01 | **Status:** Active
**Owner:** TESTER | **Reviewers:** MARCO, ATLAS, NOVA
**Depends on:** DET_E3 (Execution Concept), SEED_D8 (Engine Formulas)

---

## 1. Three Testing Layers

All testing operates on the principle that the ENGINE is the product. Tests are organized in three layers of increasing scope, cost, and fidelity.

### Layer 1: Formula Tests

**Scope:** Every deterministic formula in D8, tested in isolation.
**Count:** 200-300 auto-generated tests.
**Runtime:** <30 seconds total.
**Trigger:** Every commit (pre-commit hook or CI).

Tests are derived directly from SEED_D8_ENGINE_FORMULAS_v1.md. Each formula step (0-13 plus post-steps) generates 10-25 test cases covering: baseline, boundary conditions, edge cases, and calibration-specific values.

#### 10 Specific Test Cases

| # | Formula Step | Test Name | Input | Expected Output |
|---|-------------|-----------|-------|-----------------|
| 1 | Oil Price (Step 1) | Baseline -- no disruptions | All OPEC normal, no sanctions, no blockades, no wars, prev_price=$80 | Price $76-$84 (base $80 +/- 5% volatility) |
| 2 | Oil Price (Step 1) | Gulf Gate blockade | Gulf Gate blocked, all else baseline | Raw price $120 (disruption 1.5x), after inertia ~$104 |
| 3 | Oil Price (Step 1) | Soft cap engagement | Raw price $300 (extreme scenario) | Formula price $200 + 50*(1-e^(-1)) = ~$231.6, never exceeds $250 |
| 4 | GDP Growth (Step 2) | Sanctions S-curve -- low coverage | Coverage 0.3 (West alone) | Effectiveness 10%, sanctions_hit = -0.10 * 1.5 = -0.15 * base_mult |
| 5 | GDP Growth (Step 2) | Sanctions adaptation | Coverage 0.7, sanctions_rounds=5 | Effectiveness 60% * 0.60 adaptation = 36% effective |
| 6 | GDP Growth (Step 2) | Semiconductor disruption -- Round 3 | Formosa disrupted, round 3, dep=0.8, tech_sector=40% | severity=0.7, semi_hit = -0.8 * 0.7 * 0.4 = -0.224 |
| 7 | Revenue (Step 3) | Oil producer windfall | Oil price $150, oil_resource_pct=0.6, GDP=500 | oil_revenue = 150 * 0.6 * 500 * 0.01 = $450 |
| 8 | Stability (Step 12) | War casualty stability drain | 500 casualties, social_spending=low, GDP_growth=-3% | Stability drops by war_drag + economic_drag, net negative |
| 9 | Political Support (Step 13) | Rally-around-flag diminishing | War round 1 vs war round 4 | Round 1: +5pp support; Round 4: +1pp (diminishing) |
| 10 | Economic State (Step 9) | Crisis escalation threshold | GDP growth -4% for 2 consecutive rounds, stressed state | Transition: stressed -> crisis (threshold met) |

#### Auto-Generation Rule

For each formula in D8:
- Parse inputs, formula, and stated output ranges
- Generate: 1 baseline case, 2 boundary cases (min/max input), 2 edge cases (zero, overflow, negative), 1 calibration regression case
- Store tests as JSON fixtures in `tests/layer1/fixtures/`
- Test runner: pytest with <30s budget enforced via timeout

---

### Layer 2: Module Integration Tests

**Scope:** Multi-step formula chains, cross-engine interactions, round sequencing.
**Count:** 50-80 tests.
**Runtime:** <5 minutes total.
**Trigger:** Every deployment to staging.

These tests verify that the 14-step processing chain produces coherent end-to-end results, and that the three engines (World Model, Live Action, Transaction) interact correctly.

#### 5 Specific Integration Scenarios

| # | Scenario | Steps Covered | What It Verifies |
|---|----------|--------------|-----------------|
| 1 | **Sanctions cascade** -- West imposes L3 sanctions on Sarmatia | Steps 0,1,2,3,4,9,10,11 | Sanctions reduce GDP -> lower revenue -> budget squeeze -> economic state transition -> contagion to trade partners. Imposer cost applied to sanctioning countries. |
| 2 | **Formosa blockade spiral** -- Cathay blockades Formosa Strait | Steps 0,1,2,6,9,12,13 | Oil price spike (disruption +0.10) + semiconductor hit (duration-scaling over 3 rounds) + tech slowdown + stability drain + political support shift. Verify semiconductor severity ramps 0.3/0.5/0.7 across rounds. |
| 3 | **Budget-military feedback** -- Country at war with shrinking GDP | Steps 2,3,4,5,8 | GDP contracts -> revenue falls -> budget can't cover military spending -> debt accumulates -> inflation rises -> further GDP drag next round. Verify the doom loop converges (doesn't produce infinite contraction). |
| 4 | **OPEC coordination** -- Three OPEC members cut to "min" | Steps 0,1,2,3,13 | Supply drops 0.36 -> oil price spikes -> importers GDP hit -> producers gain oil revenue -> political support shifts (importers angry, producers pleased). Verify oil floor/cap respected. |
| 5 | **Contagion chain** -- Cathay enters crisis, propagation test | Steps 2,9,10,11 | Cathay crisis -> bilateral drag on trade partners -> momentum shift -> contagion check on dependent economies (Columbia 15% exposure, Hanseatic 12%). Verify contagion doesn't chain-react into global collapse within 1 round. |

#### Integration Test Architecture

- Each scenario loads a known starting state (snapshot from seed data)
- Executes 1-3 complete engine rounds
- Asserts on: final values, intermediate state transitions, cross-engine consistency
- Tests run against the actual engine code (not mocks)
- Stored in `tests/layer2/scenarios/`

---

### Layer 3: AI Simulation Battery

**Scope:** Full 8-round simulations with 21 AI-operated countries.
**Count:** 8 canonical scenarios.
**Runtime:** Tier-dependent (2 min to 80 min per scenario).
**Trigger:** Manual, or by LEAD after sprint milestones.

#### The 8 Scenarios

| # | Name | Setup Modification | What It Tests |
|---|------|--------------------|--------------|
| 1 | **Baseline** | No modifications -- seed data as-is | Does the simulation produce a credible 8-round arc? No crashes, no runaway values, plausible narrative. The control run. |
| 2 | **Formosa Crisis** | Cathay blockades Formosa at Round 2 | Semiconductor cascade, global supply chain disruption, alliance response, escalation/de-escalation dynamics. Peak stress on tech and trade formulas. |
| 3 | **Sanctions Pressure** | West imposes maximum sanctions on Sarmatia at Round 1 | Sanctions S-curve effectiveness, adaptation over time, coalition building (do swing states join?), imposer costs, energy market disruption. |
| 4 | **Nuclear Brinkmanship** | Sarmatia-Ruthenia war escalates, nuclear threat at Round 3 | Escalation ladder, deterrence mechanics, political support under existential threat, alliance commitments, crisis de-escalation pathways. |
| 5 | **Economic Decoupling** | Columbia and Cathay impose maximum mutual tariffs at Round 1 | Bilateral trade collapse, supply chain reorientation, impact on smaller economies, inflation dynamics, tech race without trade. |
| 6 | **Political Upheaval** | Three countries trigger elections/regime change simultaneously | Domestic political mechanics under stress, policy continuity disruption, alliance reliability, AI decision-making under regime transition. |
| 7 | **Covert Operations** | Multiple intelligence operations launched Round 1-3 | Covert action mechanics, discovery probability, diplomatic fallout, trust erosion, escalation from covert to overt conflict. |
| 8 | **Ruthenia Survival** | Ruthenia starts with 20% lower GDP and stability | Asymmetric pressure on a key actor, Western aid dynamics, war sustainability, capitulation thresholds, negotiation under duress. |

Each scenario produces a complete game trace: all 8 rounds, all country decisions, all engine outputs, all state transitions.

---

## 2. Speed Dial (Tier System)

A single configuration parameter controls simulation fidelity across all Layer 3 runs.

```
test_mode = "tier1" | "tier2" | "tier3" | "tier4"
```

| Tier | Name | AI Decisions | Conversations | Voice | Time per SIM | Use Case |
|------|------|-------------|---------------|-------|-------------|----------|
| **Tier 1** | Quick-scan | Rule-based heuristics, no LLM calls | None | No | ~2 min | Formula validation, regression checks, bulk calibration (50+ runs) |
| **Tier 2** | Modelled | LLM-generated decisions with reasoning | Summarized (1-line per exchange) | No | ~5 min | Mechanic validation, AI behavior tuning, scenario exploration |
| **Tier 3** | Full dialogue | LLM-generated with full cognitive 4-block model | Real AI-to-AI text conversations | No | ~30-40 min | Narrative credibility, diplomatic dynamics, pre-playtest validation |
| **Tier 4** | Production | Full cognitive model + voice pipeline | Full text + ElevenLabs audio | Yes | ~60-80 min | Phase 3 only -- human experience testing, voice UX validation |

### Tier Implementation

**Tier 1** replaces AI agent calls with deterministic decision functions: each country follows a fixed behavioral profile (aggressive/defensive/neutral) encoded as rules. No API calls. Runs locally.

**Tier 2** makes one LLM call per country per round. The prompt includes country state, objectives, and available actions. Response is a structured JSON decision. Conversations between countries are summarized as single-line outcomes ("Cathay and Sarmatia discussed energy -- no deal reached").

**Tier 3** runs the full 4-block cognitive architecture (Perception -> Analysis -> Decision -> Communication) per country. Countries hold actual multi-turn text conversations. Each diplomatic meeting is a real dialogue. This is the credibility benchmark.

**Tier 4** adds ElevenLabs TTS to all AI communications. Each country has a distinct voice. Used only in Phase 3 for testing the human participant experience.

### Configuration

```python
# In test runner or environment config
TEST_MODE = os.getenv("TTT_TEST_MODE", "tier1")

# The engine, AI agents, and communication layer all read this single setting
# and adjust their behavior accordingly:
#   tier1 -> skip LLM, use rule-based decisions
#   tier2 -> single LLM call, summarized conversations
#   tier3 -> full cognitive model, real conversations
#   tier4 -> full cognitive model + voice synthesis
```

---

## 3. Results Format

Every test run produces three outputs.

### 3.1 HTML Dashboard

Location: `tests/results/dashboard.html`

A self-contained HTML file (no server required) displaying:
- **Run summary table:** scenario, tier, date, duration, pass/fail, key metrics
- **Trajectory charts:** oil price, GDP by country, stability, political support -- line charts across 8 rounds
- **Heatmap:** country-by-round economic state (normal/stressed/crisis/collapse)
- **Anomaly flags:** values that exceeded expected bounds, highlighted in red
- **Comparison mode:** overlay two runs on the same charts (toggle between Run A / Run B / Both)

Built with Chart.js or similar -- single HTML file with embedded JS/CSS.

### 3.2 MD Detailed Report

Location: `tests/results/run_[N]_[scenario]_[tier]_[date].md`

Per-run markdown file containing:
- Run metadata (scenario, tier, seed data version, engine version, timestamp)
- Round-by-round state dump (all country variables after each round)
- All AI decisions with reasoning (Tier 2+)
- All conversations (Tier 3+)
- Engine processing log (which formulas fired, intermediate values)
- Anomalies and warnings from Pass 3 coherence checks
- Final world state summary

### 3.3 Comparison Tool

Location: `tests/tools/compare.py`

Command: `python compare.py run_17 run_18`

Output:
- **Side-by-side trajectory table:** each variable, each round, both runs, delta column
- **Decision diff:** where AI countries made different choices, with reasoning
- **Divergence point:** first round where the runs meaningfully diverge (delta > threshold)
- **Parameter diff:** if engine parameters changed between runs, list them
- **Summary verdict:** "Run 18 shows improved stability convergence; sanctions cascade resolved 1 round faster"

Output format: both terminal-printable table and markdown file.

---

## 4. Calibration Workflow

Calibration is the iterative process of adjusting simulation parameters until AI runs produce credible geopolitical dynamics.

### The Loop

```
1. SELECT scenario (from the 8-scenario battery)
2. RUN at Tier 1 (quick-scan) -- 5-10 runs for statistical spread
3. REVIEW dashboard -- identify anomalies, implausible trajectories
4. IDENTIFY root cause -- which formula, parameter, or starting value
5. ADJUST the parameter (in engine config or seed data)
6. RE-RUN the same scenario
7. COMPARE (Run N vs Run N+1) -- verify improvement, check for regressions
8. If credible: PROMOTE to Tier 2/3 for narrative validation
9. If not credible: REPEAT from step 4
```

### What Gets Calibrated

| Category | Examples | Adjusted In |
|----------|----------|-------------|
| **Starting economics** | GDP, growth rates, debt levels, inflation, trade weights | Seed data (DET_B3) |
| **Starting military** | Force levels, deployment positions, production capacity | Seed data (DET_B3) |
| **Starting politics** | Stability, political support, regime type thresholds | Seed data (DET_B3) |
| **Map state** | Zone control, chokepoint status, contested regions | Seed data (DET_B3) |
| **Action parameters** | Tariff levels, sanction levels, OPEC production options | Engine config |
| **Formula parameters** | Multipliers, thresholds, cap values, inertia ratios | Engine code (D8 formulas) |
| **AI behavior** | Aggression profiles, risk tolerance, cooperation thresholds | AI agent config |

### Calibration Log

Every calibration change is logged in `tests/calibration/log.md`:

```
## Cal-N: [Description]
- Date: YYYY-MM-DD
- Scenario: [which scenario revealed the issue]
- Problem: [what was wrong -- e.g., "Sarmatia GDP collapses to zero by Round 4"]
- Root cause: [which formula/parameter]
- Change: [old value -> new value]
- Before: Run [X] -- [summary]
- After: Run [Y] -- [summary]
- Verdict: [Fixed / Improved / Needs more work]
```

This log is the audit trail for every engine tuning decision. It connects directly to the D8 "Calibration notes" sections.

---

## 5. TESTER Independence

The TESTER operates as a completely separate entity from the design and development team.

### Separation Rules

1. **Separate Claude Code instance.** TESTER runs in its own session. Does not share context with the build team's session.
2. **Read-only access to source.** TESTER reads from `2 SEED/`, `3 DETAILED DESIGN/`, and engine code. TESTER **never** modifies these files.
3. **Write-only to test directory.** All TESTER output goes to `10. TESTS/` and `tests/`. No exceptions.
4. **Reports findings, does not fix.** TESTER identifies problems and writes structured findings. The design team (ATLAS, SIMON, NOVA) decides what to change and makes the changes.
5. **No soothing.** TESTER's job is to crash-test the simulation. A test that passes everything is suspicious. The mandate: **"You are here to CRASH TEST, not to soothe."**

### TESTER Outputs

All findings follow this structure:

```
FINDING [ID]: [Title]
Severity: CRITICAL / HIGH / MEDIUM / LOW
Layer: 1 / 2 / 3
Scenario: [which test/scenario]
Observed: [what happened]
Expected: [what should happen]
Root cause (hypothesis): [TESTER's best guess]
Suggested fix: [optional -- TESTER may suggest, team decides]
```

TESTER consolidates findings into `10. TESTS/SEED TEST/` (current phase) or `10. TESTS/DET TEST/` (detailed design phase) with a summary dashboard.

---

## 6. CI/CD Integration

### Pipeline Stages

```
Developer commits code
        |
        v
[Pre-commit hook] ── Layer 1: Formula Tests (200-300 tests, <30s)
        |                  FAIL → commit blocked, fix required
        |                  PASS ↓
        v
[Push to branch] ── CI pipeline validates (lint + Layer 1 re-run)
        |
        v
[Deploy to staging] ── Layer 2: Integration Tests (50-80 tests, <5min)
        |                  FAIL → deployment blocked, PR flagged
        |                  PASS ↓
        v
[Staging ready]
        |
        v
[Manual trigger by LEAD] ── Layer 3: AI Simulation Battery
                                 Run selected scenarios at chosen Tier
                                 Results posted to dashboard
                                 Team reviews before production merge
```

### Layer 1 -- Pre-Commit

- Runs via `pytest tests/layer1/ --timeout=30`
- Installed as a git pre-commit hook (`pre-commit` framework or bare shell hook)
- Also runs in CI on every push as a safety net
- Zero tolerance: any formula test failure blocks the commit

### Layer 2 -- Staging Deployment

- Triggered automatically when staging environment updates
- Runs via `pytest tests/layer2/ --timeout=300`
- Results posted to the test dashboard
- Failures block promotion to production but do not block further staging deploys (allows iteration)

### Layer 3 -- Manual / Milestone

- Triggered by LEAD (MARCO) after sprint milestones or significant engine changes
- Command: `python tests/layer3/run_battery.py --scenarios=all --tier=tier1`
- Or selective: `python tests/layer3/run_battery.py --scenarios=baseline,formosa --tier=tier3`
- Results written to `tests/results/` and summarized in the HTML dashboard
- No automated pass/fail gate -- human judgment required (credibility is subjective)
- TESTER reviews results independently and files findings

### Environment Variables

```
TTT_TEST_MODE=tier1|tier2|tier3|tier4    # Speed dial
TTT_TEST_SCENARIOS=all|baseline|formosa  # Scenario selection (Layer 3)
TTT_ENGINE_VERSION=latest|v2.5           # Pin engine version for regression
TTT_SEED_DATA=default|custom_path        # Override seed data for experiments
```

---

## Appendix: File Layout

```
tests/
├── layer1/
│   ├── fixtures/          # JSON test fixtures (auto-generated from D8)
│   ├── test_oil_price.py
│   ├── test_gdp_growth.py
│   ├── test_revenue.py
│   ├── test_budget.py
│   ├── test_military.py
│   ├── test_technology.py
│   ├── test_inflation.py
│   ├── test_debt.py
│   ├── test_economic_state.py
│   ├── test_momentum.py
│   ├── test_contagion.py
│   ├── test_stability.py
│   ├── test_political_support.py
│   └── test_post_steps.py
├── layer2/
│   ├── scenarios/         # Integration scenario definitions (JSON)
│   └── test_integration.py
├── layer3/
│   ├── scenarios/         # AI simulation scenario configs (JSON)
│   ├── run_battery.py     # Main runner
│   └── tier_config.py     # Tier 1-4 behavior switching
├── tools/
│   └── compare.py         # Run comparison tool
├── results/
│   ├── dashboard.html     # Visual dashboard (auto-updated)
│   └── run_*.md           # Per-run detailed reports
├── calibration/
│   └── log.md             # Calibration change log
└── conftest.py            # Shared fixtures, engine initialization
```

---

*This document defines the testing architecture for the TTT simulation engine. It will be refined as the engine codebase matures. TESTER owns execution; ATLAS and NOVA own the test infrastructure code.*
