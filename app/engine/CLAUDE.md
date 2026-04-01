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

## File Structure

```
engine/
├── CLAUDE.md           ← THIS FILE
├── main.py             ← FastAPI app, route registration
├── config/
│   ├── settings.py     ← Environment-based configuration
│   └── llm_config.py   ← LLM provider configuration
├── engines/
│   ├── economic.py     ← GDP, trade, sanctions, tariffs
│   ├── military.py     ← Combat, deterrence, force projection
│   ├── political.py    ← Stability, elections, alliances
│   ├── technology.py   ← R&D, tech transfer
│   └── orchestrator.py ← Round resolution, domain integration
├── models/
│   ├── game_state.py   ← Core game state model
│   ├── actions.py      ← Player/AI action schemas
│   └── results.py      ← Engine output models
└── services/
    ├── ai_service.py   ← Provider-agnostic LLM interface
    └── db_service.py   ← Supabase client operations
```
