# SEED TESTS3 — Test Plan
**Date:** 2026-03-28 | **Engine Version:** v3 (4 calibration fixes applied)
**Tester:** Independent Claude Code Instance
**Previous:** SEED TESTS2 (2026-03-27) — 14 design issues found, fixes applied overnight

---

## What Changed Since SEED TESTS2

| Fix | From | To | Issue Addressed |
|-----|------|----|-----------------|
| Cal-1: Oil inertia | Instant price jumps | 40% sticky + 60% equilibrium | $100 single-round swings |
| Cal-2: Sanctions | 2.0× multiplier, 0.70 adaptation | 1.5× multiplier, 0.60 adaptation | Over-aggressive sanctions damage |
| Cal-3: Tech factor | Multiplicative (+15%/+30% GDP) | Additive (+1.5pp/+3.0pp growth) | GDP doubling bug |
| Cal-4: Inflation cap | Unbounded | -0.50/round max | Persia/Caribe instant collapse |
| Data: Cathay AI | L2 with 0.70 progress (bugged) | L3 with 0.10 progress | Auto-promotion bug |
| Data: Columbia AI | 0.60 progress | 0.80 progress | L4 unreachable |
| Data: Columbia naval | 10 | 11 | Baseline fix |
| Data: Columbia resources | 5% | 8% | Oil producer hedge |
| New: Crisis states | None | normal/stressed/crisis/collapse | Economic escalation ladder |
| New: Momentum | None | -5 to +5 confidence | Growth acceleration/deceleration |
| New: Semiconductor ramp | Binary | 0.3→0.5→0.7→0.9→1.0/round | Stockpile depletion |
| New: Siege resilience | None | +0.10 for sanctioned autocracies | Nordostan collapsing too fast |
| New: Contagion | None | Major economy crisis → trade partners | Systemic risk |
| New: R&D multiplier | 0.5 | 0.8 | Tech race too slow |
| New: Election crisis mods | None | Stressed -5, Crisis -15, Collapse -25 | Election realism |

---

## Test Battery (8 tests — original 6 + 2 new scenarios)

| # | Name | Objective | What Changed Since TESTS2 |
|---|------|-----------|--------------------------|
| 1 | **GENERIC BASELINE** | Full system integration with v3 engine | Oil inertia, tech fix, crisis states |
| 2 | **FORMOSA CRISIS** | Cathay blockade calculus with ramping semiconductor | Semiconductor severity ramps, Cathay at L3 |
| 3 | **GULF GATE ECONOMICS** | Oil price with inertia model | Cal-1 oil inertia, Cal-2 sanctions adaptation |
| 4 | **PEACE NEGOTIATION** | Ceasefire with momentum and crisis states | Economic crisis → deal pressure |
| 5 | **STABILITY CALIBRATION** | All formula fixes validation | Cal-4 caps, siege resilience, crisis states |
| 6 | **RARE EARTH + TECH RACE** | R&D with 0.8 multiplier, Columbia 0.80 start | Cal-3 additive tech, RD_MULTIPLIER 0.8 |
| 7 | **COLUMBIA OVERSTRETCH** (NEW) | What if Columbia loses a carrier? Dealer incapacitated? | Test resilience under cascade stress |
| 8 | **CATHAY PATIENCE** (NEW) | What if Cathay does NOT blockade? Pure economic competition. | Test whether non-military path is viable |

---

## Validation Targets (vs TESTS2 findings)

| Metric | TESTS2 Result | Target for TESTS3 | Pass Criteria |
|--------|---------------|-------------------|---------------|
| Oil R1 | $198 (too high, instant) | $130-150 (with inertia) | Gradual climb, not spike |
| Oil R8 | $82-250 (varies) | $80-160 (varies) | Responsive but dampened |
| Heartland stability R8 | 2.31 (slightly low) | 2.5-3.5 | Within target band |
| Nordostan stability R8 | 1.0 (too low) | 3.0-4.5 | Siege resilience working |
| Columbia AI L4 | Unreachable | Reachable R5-R7 unrestricted | R&D multiplier fix validated |
| Cathay AI | Auto-promoted R1 (bugged) | Starts at L3 correctly | Data fix validated |
| Tech factor on GDP | +15% multiplicative (doubling) | +1.5pp additive | No GDP runaway |
| Persia stability R1 | -3.25 (instant collapse from inflation) | -0.50 max (capped) | Cal-4 working |

---

## New Scenarios

### Test 7: COLUMBIA OVERSTRETCH
**Objective:** Stress-test Columbia under cascading failures.
**Setup:**
- R1: Dealer 10% incapacitation → triggers (Volt becomes Acting President)
- R2: Columbia loses 1 naval unit in Gulf Gate assault (same as TESTS2)
- R3: Choson ICBM crisis forces Pacific redeployment
- R4: Midterms flip (Tribune wins Seat 5, budget blocked)
**Watch:** Does the crisis state cascade work? Does Columbia's GDP enter "stressed"? Does Volt's isolationist agenda change military posture? Can Columbia recover or does it spiral?

### Test 8: CATHAY PATIENCE
**Objective:** What happens if Cathay plays the long game — no blockade, no military action, pure economic/tech competition?
**Setup:** Helmsman's formosa_urgency = 0.3 (low). Sage's influence elevated. Abacus drives economic reform. Circuit focuses on tech self-sufficiency.
**Watch:** Does the gap close faster through growth than through conflict? Does Columbia's overstretch create opportunities Cathay can exploit without firing a shot? Is the non-military path viable or does the design force escalation?
