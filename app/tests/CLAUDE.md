# CLAUDE.md — Testing Protocol

**Scope:** All test code under `/app/tests/`. Subordinate to `/app/CLAUDE.md` and root CLAUDE.md.

---

## TESTER Independence Rule

TESTER writes and runs tests. TESTER NEVER modifies source code, engine logic, design documents, or production configuration. Test results and recommendations are reported to LEAD. BACKEND/AGENT/FRONTEND make the fixes. This separation is non-negotiable.

---

## Three-Layer Testing

### Layer 1 — Formula Unit Tests
- **Framework:** pytest (Python)
- **Source of truth:** DET_D8 (all formulas specification)
- **Auto-generation:** For each formula in D8, generate parametrized test cases covering:
  - Happy path (typical inputs, expected outputs)
  - Edge cases (zero values, maximum values, single-country scenarios)
  - Boundary values (thresholds where behavior changes)
  - Negative/invalid inputs (graceful failure, not crashes)
- **Location:** `/app/tests/layer1/` (mirrors engine module structure)
- **Speed:** Total suite must run in <30 seconds
- **When:** Every commit. Layer 1 must pass before merge. No exceptions.

### Layer 2 — Module Integration Tests
- **Framework:** pytest + httpx (for FastAPI testing)
- **What's tested:**
  - Engine + DB: correct read/write of game state
  - Engine + API: endpoints return correct results for known inputs
  - API + Realtime: state changes trigger subscription events
  - Orchestrator + Engines: round resolution produces consistent multi-domain output
- **Location:** `/app/tests/layer2/`
- **Speed:** Total suite must run in <5 minutes
- **When:** Every deployment or significant integration change

### Layer 3 — AI Simulation Tests
- **Framework:** Custom test harness (Python)
- **8-scenario battery** (from SEED test architecture):
  - Baseline stability (no shocks, does system stay coherent?)
  - Economic crisis cascade
  - Military escalation spiral
  - Alliance formation and breakdown
  - Sanctions effectiveness
  - Technology race dynamics
  - Regime change propagation
  - Full chaos (multiple simultaneous shocks)
- **Tiers:**
  - Tier 1: No conversations — pure formula + AI decisions (~2 min/run)
  - Tier 2: Modelled conversations — structured negotiation outcomes (~5 min/run)
  - Tier 3: Full text — complete LLM dialogue (~20 min/run)
  - Tier 4: Voice — future phase
- **Location:** `/app/tests/layer3/`
- **When:** Sprint milestones, after significant engine or AI changes

## Speed Dial Configuration

`test_mode` config controls test execution speed:
- `fast` — Layer 1 only, no LLM calls, mock external services
- `standard` — Layer 1 + Layer 2, real DB, mock LLM
- `full` — All layers, real services, real LLM calls
- `simulation` — Layer 3 only, specific scenario selection

## Results & Reports

- **HTML dashboard:** Visual results with trend lines, pass/fail rates, historical comparison
- **MD reports:** Detailed findings per test run, with failure analysis
- **Location:** `10. TESTS/BUILD TEST/` (results), `10. TESTS/MASTER_DASHBOARD.html` (dashboard)
- Dashboard updated after every Layer 2+ test run

## Calibration Workflow

After Layer 3 runs:
1. **Run** — Execute scenario battery, capture all outputs
2. **Review** — Analyze game outcomes: plausible? balanced? interesting?
3. **Recommend** — Write calibration memo: which parameters to adjust, by how much, with rationale
4. **Adjust** — BACKEND implements parameter changes (TESTER does NOT)
5. **Re-run** — Execute same scenarios with new parameters
6. **Compare** — Side-by-side before/after analysis, document improvement

## File Structure

```
tests/
├── CLAUDE.md            ← THIS FILE
├── conftest.py          ← Shared fixtures, test DB setup
├── test_config.py       ← Speed dial settings
├── layer1/
│   ├── test_economic.py
│   ├── test_military.py
│   ├── test_political.py
│   └── test_technology.py
├── layer2/
│   ├── test_engine_db.py
│   ├── test_engine_api.py
│   └── test_api_realtime.py
└── layer3/
    ├── scenarios/       ← 8 scenario definitions
    ├── harness.py       ← Simulation test runner
    └── analysis.py      ← Results comparison and reporting
```
