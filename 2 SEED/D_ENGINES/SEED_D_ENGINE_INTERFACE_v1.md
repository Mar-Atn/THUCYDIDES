# TTT Engine Interface Contract
## Stable Interface — Evolving Implementation

### Purpose
The engine is a black box with stable interfaces. The internals (formulas,
expert panel, calibration) can evolve without affecting external consumers
(Tester, web app, AI agents, moderator).

### STABLE (do not change without versioning):

#### Input: Actions per Round
JSON format:
```json
{
  "round_num": 4,
  "country_actions": {
    "columbia": {
      "budget": {},
      "tariffs": {},
      "sanctions": {},
      "military": {},
      "diplomatic": []
    }
  }
}
```

#### Input: World State
Loaded from CSVs (data/) or JSON snapshot.
Schema defined in SEED_F1_DATA_SCHEMA_v1.md.

#### Output: Round Results
JSON format:
```json
{
  "round_num": 4,
  "world_state": {},
  "combat_results": [],
  "transactions_executed": [],
  "elections": {},
  "narrative": "...",
  "expert_panel": {
    "keynes": [],
    "clausewitz": [],
    "machiavelli": [],
    "applied": [],
    "flags": []
  },
  "coherence_flags": []
}
```

#### Processing Timing
Target: < 5 minutes per round.
Heuristic version: < 1 second.
LLM version: < 30 seconds (3 parallel API calls).

#### Three-Pass Architecture
1. **Deterministic** — formulas + feedback loops
2. **Expert Panel** — 3 independent evaluations + majority-rule synthesis
3. **Coherence Check** — plausibility scoring

### EVOLVING (can change freely):
- Formula coefficients and thresholds
- Expert panel check logic
- Crisis ladder transition rules
- Calibration parameters (80+ tunable values)
- Pass 2 implementation (heuristic vs LLM)
- Pass 3 implementation (rules vs LLM-as-judge)

### Three Engines
1. **World Model Engine** — between-round batch processing
2. **Live Action Engine** — real-time combat/events during rounds
3. **Transaction Engine** — real-time bilateral transfers

Each engine has the same contract pattern:
stable input format, stable output format, evolving internals.
