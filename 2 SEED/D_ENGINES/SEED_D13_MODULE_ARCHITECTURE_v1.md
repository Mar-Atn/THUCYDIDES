# SEED D13 — Module Architecture & Dependency Map (v1)

**Status:** SEED reference (snapshot of app/engine/ as of 2026-04-04)
**Owner:** LEAD + BACKEND
**Purpose:** Single source of truth for how TTT modules connect. Any new module or rewiring MUST be reconciled against this doc.

---

## Section 1: Module Structure

Snapshot of `app/engine/` on 2026-04-04:

```
app/engine/
├── main.py                         FastAPI entrypoint
├── requirements.txt
├── CLAUDE.md
│
├── config/
│   └── settings.py                 env vars, LLM keys, model IDs
│
├── models/
│   ├── db.py                       Supabase table schemas / ORM helpers
│   └── api.py                      Pydantic request/response models
│
├── services/
│   ├── llm.py                      provider-agnostic LLM calls (Anthropic, Gemini)
│   └── supabase.py                 Supabase client wrapper
│
├── engines/                        STATELESS formula engines
│   ├── economic.py                 GDP, oil, sanctions, trade, budget
│   ├── military.py                 capability, posture, theater resolution
│   ├── political.py                stability, legitimacy, regime dynamics
│   ├── technology.py               tech tree, R&D, diffusion
│   └── orchestrator.py             chains all four engines per round
│
├── judgment/                       NOUS — qualitative AI judge
│   ├── judge.py                    LLM-backed adjudication & reflection
│   └── schemas.py                  JudgeRequest / JudgeResponse types
│
├── context/                        context window assembly for agents
│   ├── assembler.py                composes blocks → prompt context
│   └── blocks.py                   canonical context blocks (identity, world,
│                                   memory, goals, options)
│
└── agents/                         AI participants (21 country leaders)
    ├── profiles.py                 CSV loading (countries, roles, archetypes)
    ├── memory.py                   per-leader memory (episodic, goals)
    ├── decisions.py                decision-making (mandatory + discretionary)
    ├── conversations.py            bilateral conversation runner
    ├── transactions.py             proposals, evaluation, execution
    ├── leader.py                   Leader class — composes all of the above
    └── runner.py                   RoundRunner — orchestrates full round
```

**Domain tiers** (leaf → root):

```
Tier 0  config/, models/           pure data, no logic
Tier 1  services/                  thin external wrappers
Tier 2  engines/, context/blocks   stateless domain logic
Tier 3  judgment/, context/assembler
Tier 4  agents/ (memory, profiles, decisions, conversations, transactions)
Tier 5  agents/leader.py           composes Tier 4 primitives
Tier 6  agents/runner.py           top-level round orchestration
```

A module may import from its own tier or below. Upward imports are forbidden.

---

## Section 2: Dependency Graph

```
                         ┌──────────────────────┐
                         │  agents/runner.py    │  (Tier 6)
                         └──────────┬───────────┘
                ┌───────────────────┼──────────────────────┐
                ▼                   ▼                      ▼
       ┌────────────────┐  ┌──────────────────┐  ┌──────────────────┐
       │ agents/leader  │  │ engines/         │  │ judgment/judge   │
       │    .py         │  │  orchestrator.py │  │     .py          │
       └───────┬────────┘  └────────┬─────────┘  └─────────┬────────┘
               │                    │                      │
   ┌───────────┼────────────┐       │                      │
   ▼           ▼            ▼       ▼                      ▼
┌────────┐ ┌────────┐ ┌──────────┐  ┌──────────┐    ┌─────────────┐
│memory  │ │profiles│ │decisions │  │economic  │    │ context/    │
│  .py   │ │  .py   │ │  .py     │  │military  │    │ assembler   │
└────────┘ └────┬───┘ ├──────────┤  │political │    └──────┬──────┘
                │     │conversa- │  │technology│           │
                │     │ tions.py │  └──────────┘           ▼
                │     ├──────────┤                    ┌─────────┐
                │     │transac-  │                    │ blocks  │
                │     │ tions.py │                    │   .py   │
                │     └────┬─────┘                    └─────────┘
                │          │
                │          └─────► services/llm.py ◄──── (all agents,
                │                  services/supabase.py   judge use this)
                │                        │
                │                        ▼
                │                  config/settings.py
                ▼
           CSV files
       (countries, roles,
        archetypes)
```

**Explicit edges** (verified in code on 2026-04-04):

- `agents/leader.py` → `memory.py`, `profiles.py`, `decisions.py`, `conversations.py`, `transactions.py`, `services/llm.py`, `context/assembler.py`
- `agents/runner.py` → `leader.py`, `engines/orchestrator.py`, `judgment/judge.py`, `context/assembler.py`, `models/db.py`
- `agents/decisions.py` → `context/assembler.py`, `services/llm.py`, `memory.py`
- `agents/conversations.py` → `services/llm.py`, `context/assembler.py`, `memory.py`
- `agents/transactions.py` → `services/llm.py`, `memory.py`
- `agents/profiles.py` → (CSV files only, no Python deps)
- `agents/memory.py` → (stdlib only)
- `judgment/judge.py` → `judgment/schemas.py`, `context/assembler.py`, `services/llm.py`
- `context/assembler.py` → `context/blocks.py`
- `engines/orchestrator.py` → `economic.py`, `political.py`, `military.py`, `technology.py`
- `engines/*.py` → (stdlib + numpy only; stateless functions)
- `services/llm.py` → `config/settings.py`, anthropic SDK, google-genai SDK
- `services/supabase.py` → `config/settings.py`, supabase-py
- `main.py` → `models/api.py`, `agents/runner.py`, `services/supabase.py`

---

## Section 3: Data Flow (One Round)

```
 STEP                        MODULE                    OUTPUT
 ────────────────────────────────────────────────────────────────────────
 1. Load countries.csv    →  profiles.py            →  countries dict (21)
 2. Load roles + archetypes profiles.py             →  role registry
 3. Initialize 21 leaders →  leader.py              →  Leader[] in memory
      - load role                                       (identity,
      - generate identity                                goals,
      - build initial goals                              memory shell)
 4. runner.start_round(N) →  runner.py              →  round_state
 5. For each leader:         runner.py
      5a. Assemble context →  context/assembler.py  →  context_str
      5b. Decide action    →  decisions.py + LLM    →  Action list
      5c. Submit           →  runner.py queue
 6. Match conversations   →  runner.py              →  pair list
 7. Run each conversation →  conversations.py + LLM →  dialog turns
 8. Propose transactions  →  transactions.py + LLM  →  TX proposals
 9. Evaluate TXs          →  transactions.py + LLM  →  accept / reject
 10. Execute accepted TXs →  transactions.py        →  state deltas
 11. Collect mandatory    →  decisions.py           →  budget, oil, etc.
     inputs (per domain)
 12. Engine Pass 1        →  engines/orchestrator   →  quantitative
     (economic → political    → economic.py             state changes
      → military → tech)       → political.py
                               → military.py
                               → technology.py
 13. Engine Pass 2        →  judgment/judge.py+LLM →  qualitative
     (NOUS reflection)                                   verdicts, narrative
 14. Write reflections    →  memory.py              →  per-leader memory
 15. Build RoundReport    →  runner.py              →  RoundReport JSON
 16. (optional) Persist   →  models/db.py           →  Supabase rows
                             + services/supabase.py
```

---

## Section 4: Communication Protocols Between Modules

| Interface | Mechanism | Contract |
|---|---|---|
| Engine ↔ Engine | Chained calls in `engines/orchestrator.py` | In-memory dicts (world_state). Each engine is a pure `fn(state) → new_state`. |
| Agents ↔ Engines | `agents/runner.py` calls `engines/orchestrator.run_round(state, inputs)` | `inputs` = dict keyed by country_id. |
| Agents ↔ LLM | `services/llm.py` (provider-agnostic) | `llm.call(model, system, messages) → str/json`. Swaps Anthropic / Gemini by model ID. |
| Agents ↔ Data | `agents/profiles.py` loads CSVs at init | Read-only; returns dicts. |
| Agents ↔ Memory | `agents/memory.py` in-process Python objects | Per-leader instance; no cross-leader access. |
| Context ↔ everything | `context/assembler.py` composes `blocks.py` primitives | `assembler.build(leader, world, round) → str`. |
| Judgment ↔ Agents | `judgment/judge.py` reads world_state + context | Returns `JudgeResponse` (schemas.py) consumed by runner.py. |
| API ↔ Runner | `main.py` FastAPI routes call `runner.py` | HTTP JSON (Pydantic models in `models/api.py`). |
| DB ↔ Engine | `services/supabase.py` via `models/db.py` | Currently only used at round persistence (step 16). |

---

## Section 5: What's NOT Connected (Honest Gaps)

As of 2026-04-04, these edges are **missing** from the code and must not be assumed:

- **Agent state has no DB persistence.** `memory.py` holds everything in-process; a server restart loses all leader state. No `agents → supabase` edge exists.
- **Military decisions have no map/zone integration.** `military.py` operates on aggregate posture numbers, not theaters. Agents cannot target specific zones.
- **No real transaction engine.** `transactions.py` does proposal + LLM evaluation + simplified state-delta execute. No clearing house, no escrow, no rollback.
- **No Live Action Engine.** Combat resolution (from `2 SEED/D_ENGINES/live_action_engine.py` legacy) is NOT wired into the current `engines/` stack.
- **No event log persistence.** The round-level event stream is built in-memory by `runner.py` and dropped after the round ends unless explicitly serialized.
- **No real-time broadcasting.** No WebSocket/SSE layer. Frontend (Public Display) cannot yet subscribe to round events.
- **No frontend wiring.** `app/frontend/` is scaffolded but does not consume `runner.py` output live.
- **NOUS does not feed back into engines.** `judge.py` produces qualitative reflections post-hoc; Pass 2 does not modify Pass 1 numbers.

---

## Section 6: Swappable Components

Modules designed to be replaceable without breaking the system:

| Component | Swap point | Interface contract |
|---|---|---|
| **LLM provider** | `services/llm.py` + `config/settings.py` model ID | `llm.call(...)` signature stable across Anthropic / Gemini / (future OpenAI). |
| **AI module implementation** | `agents/leader.py` | DET_C1 §C6 abstract interface: `decide()`, `converse()`, `reflect()`. KING 4-block and Anthropic-persistent implementations both satisfy it. |
| **NOUS implementation** | `judgment/judge.py` | Must match `schemas.JudgeRequest → JudgeResponse`. Can be rule-based, single-LLM, or panel-of-experts. |
| **Engine formulas** | `engines/economic.py` etc. | Stateless `fn(state, inputs) → new_state`. Replace formulas without touching orchestrator. |
| **Context blocks** | `context/blocks.py` | Each block is `fn(leader, world) → str`. Add/remove blocks via `assembler.py` composition. |
| **Persistence backend** | `services/supabase.py` | Thin wrapper; replaceable with Postgres / SQLite / file store. |

Modules that are **NOT** currently swappable (tightly coupled):

- `agents/runner.py` — orchestration logic is specific to the current round shape.
- `engines/orchestrator.py` — hardcodes the 4-engine chain order.
- `agents/profiles.py` — expects specific CSV column names from SEED seed data.

---

## Change Protocol

Any PR that adds/removes a module, adds a new cross-tier import, or changes an interface listed in §4 MUST:
1. Update this doc in the same PR.
2. Pass Layer 1 tests.
3. Be reviewed by LEAD.

Upward imports (lower tier importing higher) are automatic rejects.
