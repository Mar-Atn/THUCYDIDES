# CLAUDE.md — Engine Rules

**Scope:** All code under `/app/engine/`. Subordinate to `/app/CLAUDE.md` and root CLAUDE.md.

---

## Source of Truth

**World Model + Contracts** govern what actions exist, what fields they take, and how they route.
Before writing ANY engine code:
1. Read `MODULES/MODULE_REGISTRY.md` — canonical 33 action types (ACTION_NAMING section)
2. Read relevant contract in `MODULES/CONTRACTS/`
3. IMPORT canonical names — never hardcode action type strings
4. If a name or field is unclear → look it up, don't guess

**Design heritage** (`2 SEED/D_ENGINES/`, `3 DETAILED DESIGN/DET_D8`) — useful for understanding formula intent. Not the current specification.

---

## Language & Framework

- Python 3.11+, FastAPI with async handlers
- Pydantic v2 for all data models
- async where possible — especially DB operations, LLM calls

## Architecture Rules

- **No direct engine-to-engine calls.** Orchestrator mediates all inter-engine communication.
- **Engines are stateless.** Receive game state as input, return updated state. No engine holds state between calls.
- **All engine functions are PURE** (no DB calls). DB access lives in orchestrator/services only.
- **Action names:** Use ONLY the canonical names from MODULE_REGISTRY. Never invent, alias, or abbreviate.

## Map + Units

- **`app/engine/config/map_config.py`** — THE source for map grids, theater linkage, hex topology.
- JS counterpart: `app/test-interface/static/map_config.js`. Keep in lock-step.
- Coord convention: `(row, col)`, row first, 1-indexed. Global: [1..10]x[1..20]. Theater: [1..10]x[1..10].
- Unit model: individual rows (1 unit per row) in `deployments` table. Positioned by hex coordinates.

## File Structure

```
engine/
├── CLAUDE.md              ← THIS FILE
├── main.py                ← FastAPI app, route registration, all API endpoints
├── config/
│   ├── settings.py        ← Environment + LLM model config
│   └── map_config.py      ← Map grids, theater linkage, hex topology
├── engines/               ← PURE engine functions (no DB calls)
│   ├── economic.py        ← GDP, trade, sanctions, tariffs
│   ├── military.py        ← Combat resolution (unit-level)
│   ├── political.py       ← Stability, elections, alliances
│   ├── technology.py      ← R&D, tech transfer
│   ├── orchestrator.py    ← Round resolution orchestrator
│   └── round_tick.py      ← Per-round engine tick bridge
├── agents/                ← AI participant code
│   ├── managed/           ← Managed Agents (Claude SDK) — M5
│   │   ├── session_manager.py   ← Agent session lifecycle (async)
│   │   ├── event_dispatcher.py  ← Unified event queue + dispatch loop
│   │   ├── tool_executor.py     ← Game tool execution
│   │   ├── tool_definitions.py  ← Tool schemas for managed agents
│   │   ├── system_prompt.py     ← Layer 1 identity builder
│   │   ├── game_rules_context.py ← Game rules for AI context
│   │   ├── db_context.py        ← World context from DB
│   │   └── conversations.py     ← Bilateral meeting router
│   ├── tools.py           ← Domain query tools (shared)
│   ├── profiles.py        ← Role + country data loaders
│   └── action_schemas.py  ← Pydantic action validation models
├── services/
│   ├── action_dispatcher.py  ← Routes all 33 action types to engines
│   ├── supabase.py        ← Sync Supabase client
│   ├── async_db.py        ← Async Supabase client (for dispatch loop)
│   ├── meeting_service.py ← Meeting lifecycle
│   ├── transaction_engine.py ← Exchange transactions
│   ├── agreement_engine.py   ← Formal agreements
│   └── [other engines]    ← Per-domain service modules
└── models/
    └── db.py              ← Pydantic models for DB tables
```

## Event Dispatcher & AI Agents (M5)

The AI participant system uses a **single-process architecture** (workers=1) with three background async loops:

1. **Dispatch loop** — checks `agent_event_queue` table, delivers events to idle agents in parallel (`asyncio.gather`)
2. **Auto-pulse loop** — sends periodic `round_pulse` events during Phase A (configurable 0-10 per round)
3. **Meeting monitor** — detects active meetings, drives AI-AI conversations via ConversationRouter, prompts AI in AI-Human meetings

**Critical rules:**
- **Single worker ONLY** — multi-worker breaks in-memory dispatcher state. Set in `main.py`.
- **No CSV files** — Railway has no `2 SEED/` directory. ALL data from Supabase DB. System prompt, zone data, role data — all DB.
- **Event tiers:** Tier 1 (critical, 3s) = attacks, nuclear, batch solicitation. Tier 2 (urgent, 5s) = meetings, transactions. Tier 3 (routine, 30s) = round pulses.
- **Per-pulse context:** Each pulse includes recent events, pending proposals, country snapshot. Agents told to use tools for full details.
- **Phase restrictions:** Phase A = all actions except batch. Phase B = only batch + move_units. Enforced in `tool_executor._submit_action()`.

## Deprecation Rules

- **NEVER add new logic to `round_engine/`** — all combat/movement in `engines/military.py`
- **NEVER hardcode action type strings** — import from canonical source
- **NEVER bypass `services/action_dispatcher.py`** — all actions route through it
- **`agents/leader.py`, `leader_round.py`** — old agent system, superseded by `agents/managed/`

## Testing

Every formula must have a Layer 1 test before merge. No exceptions.
- Location: `/app/tests/layer1/`
- pytest with parametrized test cases
- Happy path + edge cases + boundary values

## KING Reference

`/Users/marat/CODING/KING/app/` — evaluate critically for reusable patterns (queue system, atomic updates, reflection service). Not mandatory.
