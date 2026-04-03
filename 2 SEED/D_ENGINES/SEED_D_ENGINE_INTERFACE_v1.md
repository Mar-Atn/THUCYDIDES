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
  "judgment": {
    "mode": "automatic",
    "crisis_declarations": [],
    "contagion_effects": [],
    "stability_adjustments": [],
    "support_adjustments": [],
    "market_index_nudges": [],
    "capitulation_recommendations": [],
    "flags": [],
    "confidence": 0.82,
    "reasoning_summary": "..."
  },
  "coherence_flags": []
}
```

#### Processing Timing
Target: < 5 minutes per round.
Pass 1 (deterministic): < 1 second.
Pass 2 (NOUS): < 30 seconds.
Pass 3 (coherence + narrative): < 60 seconds.

#### Three-Pass Architecture
1. **Deterministic (Pass 1)** — 14 chained formula steps (see SEED_D8)
2. **NOUS (Pass 2)** — LLM reviews outputs, applies bounded adjustments (see SEED_D10)
3. **Coherence + Narrative (Pass 3)** — plausibility check + round summary

#### Context Assembly
All LLM consumers (judgment, leader agents, Argus, narrative) use the shared
Context Assembly Service (see SEED_D9). Context is assembled from run-level
data with visibility filtering. Methodology is DB-stored and moderator-editable.

#### Judgment Modes
- **Automatic**: adjustments applied and logged (unmanned runs)
- **Manual**: adjustments presented to moderator for approve/modify/reject (live SIM)

### EVOLVING (can change freely):
- Formula coefficients and thresholds
- Judgment methodology ("The Book" in sim_config table)
- Calibration parameters (100+ tunable values)
- Pass 2 prompt templates and bounds
- Pass 3 implementation (rules vs LLM-as-judge)
- Context block definitions and token budgets

### Three Engines
1. **World Model Engine** — between-round batch processing
2. **Live Action Engine** — real-time combat/events during rounds
3. **Transaction Engine** — real-time bilateral transfers

Each engine has the same contract pattern:
stable input format, stable output format, evolving internals.
