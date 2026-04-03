# TTT Scenario Test Results
**Date:** 2026-04-03 13:56
**Engine:** economic.py + political.py (deterministic only)
**Data:** countries.csv (D1-D18 calibration applied)
**Scenarios:** 1 × 6 rounds

---
## S1: Baseline (no intervention)

_All countries on autopilot. Tests natural economic trajectories, budget balance, and stability._

### GDP Trajectories

| Round | Oil$ | Columb | Cathay | Sarmat | Ruthen | Persia | Teuton | Bharat | Formos |
|-------|------|------|------|------|------|------|------|------|------|
| R0 | $80 | 280 (+1.8%) | 190 (+4.0%) | 20 (+1.0%) | 2 (+2.5%) | 5 (+0.5%) | 45 (+1.2%) | 42 (+6.5%) | 8 (+3.0%) |
| R1 | $86 | 283 (+1.1%) | 194 (+2.1%) | 20 (+0.6%) | 2 (+1.1%) | 5 (+0.3%) | 45 (+0.6%) | 43 (+3.4%) | 8 (+1.5%) |
| R2 | $98 | 286 (+1.1%) | 197 (+1.6%) | 20 (+0.8%) | 2 (+1.1%) | 5 (+0.5%) | 45 (+0.3%) | 45 (+3.1%) | 8 (+1.3%) |
| R3 | $86 | 289 (+1.1%) | 201 (+2.1%) | 20 (+0.6%) | 2 (+1.3%) | 5 (+0.3%) | 46 (+0.6%) | 46 (+3.4%) | 8 (+1.5%) |
| R4 | $83 | 292 (+1.0%) | 206 (+2.2%) | 21 (+0.6%) | 2 (+1.3%) | 5 (+0.3%) | 46 (+0.6%) | 48 (+3.4%) | 8 (+1.6%) |
| R5 | $82 | 295 (+1.0%) | 211 (+2.3%) | 21 (+0.6%) | 2 (+1.3%) | 5 (+0.3%) | 46 (+0.6%) | 50 (+3.5%) | 9 (+1.6%) |
| R6 | $82 | 298 (+1.0%) | 215 (+2.3%) | 21 (+0.6%) | 2 (+1.3%) | 5 (+0.3%) | 46 (+0.6%) | 51 (+3.5%) | 9 (+1.6%) |

### Stability & Support

| Round | Columb S/Sup | Cathay S/Sup | Sarmat S/Sup | Ruthen S/Sup | Persia S/Sup | Teuton S/Sup |
|-------|----------|----------|----------|----------|----------|----------|
| R0 | 7.0/38% | 8.0/58% | 5.0/55% | 5.0/52% | 4.0/40% | 7.0/45% |
| R1 | 7.0/37% | 8.1/59% | 4.9/54% | 4.8/48% | 4.0/38% | 7.1/45% |
| R2 | 7.0/38% | 8.2/61% | 4.8/53% | 4.7/43% | 3.9/36% | 7.2/44% |
| R3 | 7.0/38% | 8.3/62% | 4.6/51% | 4.5/38% | 3.8/35% | 7.3/44% |
| R4 | 6.9/36% | 8.4/63% | 4.5/50% | 4.3/34% | 3.8/33% | 7.4/44% |
| R5 | 6.9/37% | 8.6/65% | 4.3/49% | 4.1/31% | 3.7/31% | 7.5/44% |
| R6 | 6.8/37% | 8.7/66% | 4.2/47% | 3.9/27% | 3.6/30% | 7.6/44% |

**Market Indexes (R6):** Wall Street=92, Europa=99, Dragon=98

**Coefficients (R6):** Sarmatia: sanctions=0.964, tariffs=1.000 | Persia: sanctions=0.950, tariffs=1.000

---
## Cross-Scenario Analysis

### Final GDP Comparison (R6)

| Country | S1 |
|---------|------|
| Columbia | 298 |
| Cathay | 215 |
| Sarmatia | 21 |
| Ruthenia | 2 |
| Persia | 5 |

### Convergence Criteria

| Criterion | Target | S1 |
|-----------|--------|------|
| No country GDP < 50% of start by R4 |  | PASS |
| Columbia GDP > 200 at R6 |  | PASS |
| Cathay GDP > 150 at R6 |  | PASS |
| No stability < 2.0 (baseline) |  | PASS |
| Oil $30-$200 range |  | PASS |
| Sarmatia GDP declining under sanctions |  | FAIL |