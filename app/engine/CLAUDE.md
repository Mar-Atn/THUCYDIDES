# CLAUDE.md — Engine Rules

**Scope:** All code under `/app/engine/`. Subordinate to `/app/CLAUDE.md` and root CLAUDE.md.

---

## Language & Framework

- Python 3.11+
- FastAPI with async handlers
- Pydantic v2 for all data models
- async where possible — especially DB operations, LLM calls, inter-engine orchestration

## Source of Truth: SEED Engine Code

Port from `2 SEED/D_ENGINES/*.py`. These files contain the validated engine logic:
- Economic engine (GDP, trade, sanctions, tariffs)
- Military engine (force projection, combat resolution, deterrence)
- Political engine (stability, elections, regime dynamics, alliances)
- Technology engine (R&D, tech transfer, dual-use)
- World model orchestrator (round resolution, domain integration)

**Porting rules:**
- Preserve every formula EXACTLY as specified in DET_D8
- Do not optimize formulas for performance until correctness is proven (Layer 1 tests pass)
- If a formula seems wrong, do NOT fix it silently — raise to LEAD
- Add type hints and Pydantic models around the ported logic

## Testing Requirement

**Every formula must have a Layer 1 test before merge.** No exceptions.
- Test file lives in `/app/tests/layer1/` (mirroring engine module structure)
- pytest with parametrized test cases
- Generated from DET_D8 formula specifications
- Happy path + edge cases + boundary values + zero/negative inputs

## Key Specifications

| Spec | What It Contains |
|------|-----------------|
| DET_D8 | All formulas — the mathematical source of truth |
| DET_F5 | Engine API — how the orchestrator calls engines |
| DET_C1 | System contracts — inter-module communication |
| DET_B1 | Database schema — what gets persisted |
| SEED engine code | Reference implementation to port from |

## Map + Units: Source of Truth

- **`app/engine/config/map_config.py` is THE source** for global/theater grid dimensions and the canonical theater↔global linkage table. Any new engine code touching map grids, theater linkage, or coord conversions MUST import from this module — never hardcode dimensions, link mappings, or coord tables elsewhere.
- JS counterpart: `app/test-interface/static/map_config.js`. Keep the two in lock-step.
- Unit entity contract: see `3 DETAILED DESIGN/DET_UNIT_MODEL_v1.md`. Pydantic model lives in `app/engine/models/unit.py` (to be created). Validation library: `app/engine/services/unit_validator.py` (to be created).
- Coord convention: `(row, col)`, row first, 1-indexed. Global: [1..10]×[1..20]. Theater: [1..10]×[1..10]. Never deviate.

## Architecture Rules

- **No direct engine-to-engine calls.** The orchestrator mediates all inter-engine communication. Economic engine does not import military engine.
- **Engines are stateless.** They receive game state as input, return updated state as output. No engine holds state between calls.
- **Orchestrator controls round flow.** It calls engines in the correct order, passes outputs as inputs, handles conflicts.
- **Dual LLM provider.** Gemini + Claude, centrally configurable via `/app/engine/config/`. Engine code calls a provider-agnostic interface, never a specific LLM SDK directly.

## Check KING For

- **Reflection service:** How KING processes AI reasoning chains
- **Queue system:** How KING handles async task execution
- **Atomic updates:** How KING ensures DB consistency during multi-step operations
- Location: `/Users/marat/CODING/KING/app/`

## File Structure (updated 2026-04-06 — post-reunification)

```
engine/
├── CLAUDE.md              ← THIS FILE
├── main.py                ← FastAPI app, route registration
├── config/
│   ├── settings.py        ← Environment + LLM model config (dual-provider)
│   └── map_config.py      ← Map grids, theater linkage, hex topology
├── engines/               ← CANONICAL — all engine work goes here
│   ├── economic.py        ← GDP, trade, sanctions, tariffs (2K lines, pure)
│   ├── military.py        ← Combat (unit-level v2 + zone-deprecated v1) (2.5K lines)
│   ├── political.py       ← Stability, elections, alliances (836 lines, pure)
│   ├── technology.py      ← R&D, tech transfer (357 lines, pure)
│   ├── orchestrator.py    ← Designed orchestrator (sim_runs-based, 543 lines)
│   └── round_tick.py      ← NEW: per-round engine tick bridge (scenario-based)
├── agents/                ← AI participant code
│   ├── leader.py          ← CANONICAL LeaderAgent (4-block cognitive model)
│   ├── leader_round.py    ← CANONICAL single-agent round runner (tool-use)
│   ├── full_round_runner.py ← 20-agent parallel runner (Observatory)
│   ├── profiles.py        ← Role + country data loaders
│   ├── memory.py          ← CognitiveState persistent memory
│   ├── decisions.py       ← Per-category decision functions (budget, tariff, etc.)
│   ├── tools.py           ← Domain tools (get_my_forces, commit_action, etc.)
│   ├── stage*_test.py     ← DEPRECATED — replaced by leader_round.py
│   └── runner.py          ← DESIGNED full-sim runner (in-memory, for later)
├── context/               ← Context Assembly Service (SEED D9)
│   ├── assembler.py       ← Block-based context builder
│   └── blocks.py          ← Block registry + builders
├── round_engine/          ← DEPRECATED — being replaced by engines/*
│   ├── resolve_round.py   ← Decision processor (still used for combat/movement)
│   ├── combat.py          ← DEPRECATED — use engines/military.py v2
│   └── movement.py        ← DEPRECATED — will merge into engines/
├── services/
│   ├── llm.py             ← Dual-provider plain-text LLM calls
│   ├── llm_tools.py       ← Dual-provider tool-use adapter (Anthropic ↔ Gemini)
│   └── supabase.py        ← Supabase client operations
└── models/
    └── db.py              ← Pydantic models for DB tables
```

## Deprecation rules (2026-04-06)

- **NEVER add new logic to `round_engine/`** — all combat/movement work goes in `engines/military.py` (unit-level v2 section)
- **NEVER add new agent test stages** — use `agents/leader_round.py` for tool-use agent loops
- **NEVER bypass `services/llm_tools.py`** for tool-use calls — it handles dual-provider routing
- **All engine functions are PURE** (no DB calls). DB access lives in orchestrator/round_tick/services only.
