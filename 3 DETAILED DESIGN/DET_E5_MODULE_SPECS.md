# DET E5 — Module Specifications
## Per-Module Specs: Bridge from DET to BUILD
**Version:** 1.0 | **Date:** 2026-04-01 | **Status:** ACTIVE
**Owner:** LEAD
**Cross-references:** [Dev Plan](DET_E3_DEV_PLAN_v1.md) | [Engine API](DET_F5_ENGINE_API.md) | [System Contracts](DET_C1_SYSTEM_CONTRACTS.md) | [App CLAUDE.md](../app/CLAUDE.md)

---

## Sprint 1 — Foundation

### 1. `engine/config/`
**Purpose:** Centralized settings, environment loading, and LLM model configuration.
**Inputs:** `.env` file, `LLM_MODELS.md` definitions.
**Outputs:** `Settings` singleton consumed by all modules via dependency injection.
**Dependencies:** None (leaf module — everything else depends on this).
**Design decisions:** Use `pydantic-settings` for env parsing with validation. Single `Settings` class, not scattered `os.getenv()`. LLM config defines provider/model/fallback per use-case (moderator, agent, news). Dual-provider setup (Anthropic primary, Gemini fallback) configured here.

### 2. `engine/models/`
**Purpose:** All Pydantic models — DB row schemas, API request/response schemas, internal engine types.
**Inputs:** DB schema (`DET_B1_DATABASE_SCHEMA.sql`), event envelope (`DET_C1`), API contracts (`DET_F5`).
**Outputs:** Typed models imported by every other module.
**Dependencies:** None (leaf module).
**Design decisions:** Three submodules: `db.py` (mirrors DB tables), `api.py` (request/response envelopes), `engine.py` (internal calculation types). All models frozen where possible (`model_config = {"frozen": True}`). Event envelope from C1 is a base class. Country/zone/world state models must support snapshot versioning.

### 3. `engine/services/supabase.py`
**Purpose:** Supabase client wrapper — CRUD operations, real-time channel management, auth validation.
**Inputs:** Supabase URL + service role key from config. SQL queries per operation.
**Outputs:** Typed query results (using models from `engine/models/`). Real-time broadcast calls.
**Dependencies:** `config/`, `models/`.
**Design decisions:** Use `supabase-py` async client. Wrap all DB calls in typed methods (no raw queries outside this file). Real-time publish via Supabase Realtime channels (`public`, `country:{id}`, `moderator`). All writes include `snapshot_version` for optimistic concurrency. RLS is enforced at DB level; this service uses service role key (bypasses RLS) since engine is trusted.

### 4. `engine/services/llm.py`
**Purpose:** Dual-provider LLM service — Anthropic Claude + Google Gemini with automatic failover.
**Inputs:** Prompt + model selector from config. Structured output schemas when needed.
**Outputs:** LLM response (text or structured). Token usage metrics. Provider health status.
**Dependencies:** `config/`.
**Design decisions:** Port KING's model health monitoring pattern — track latency/errors per provider, auto-switch on failure. Support context caching for Anthropic (essential for agent conversations — 85% cost reduction). Expose `call_llm(use_case, messages, schema?)` — use_case maps to model via config. All calls async. Log token usage per call for cost tracking.

### 5. `engine/main.py`
**Purpose:** FastAPI application entry point — CORS, health check, router mounting, middleware.
**Inputs:** Config settings. Route definitions from engines and services.
**Outputs:** Running HTTP server on Railway.
**Dependencies:** `config/`, all routers.
**Design decisions:** HMAC auth middleware validates `X-Engine-Auth` header on all routes except `/health`. CORS allows Supabase Edge Function origins only. Request ID middleware (`X-Request-Id`) for tracing. Standard response envelope: `{"success": bool, "data": ..., "error": ...}`. Uvicorn with 2 workers (Railway single-container).

---

## Sprint 2 — Engines

### 6. `engine/engines/economic.py`
**Purpose:** GDP growth, taxation, sanctions, tariffs, oil price, inflation, debt — all economic formulas.
**Inputs:** `CountryState` (previous round), budget allocations, active sanctions/tariffs, global oil price.
**Outputs:** Updated economic fields on `CountryState`, economic events.
**Dependencies:** `models/`, `services/supabase.py`.
**Design decisions:** Pure functions: `process_economy(state, actions) -> EconomicResult`. No DB calls inside — engine caller handles IO. Formulas from `SEED_D8_ENGINE_FORMULAS_v1.md`. Oil price is global (calculated once, applied to all). Sanctions reduce GDP by target-specific percentages. All parameters are configurable constants (for calibration tuning).

### 7. `engine/engines/military.py`
**Purpose:** Combat resolution (ground/naval/air), deployments, mobilization, unit production.
**Inputs:** `ZoneState` for contested zones, military orders, force compositions.
**Outputs:** Combat results, zone ownership changes, casualty reports, deployment confirmations.
**Dependencies:** `models/`.
**Design decisions:** Pure functions. Combat uses force-ratio model with terrain/technology modifiers. Three theaters resolved independently. Nuclear use triggers special escalation path (separate from conventional). Unit production takes 1 round (ordered in Phase A, available Phase B next round).

### 8. `engine/engines/political.py`
**Purpose:** Stability calculation, domestic support, elections, coups, alliance effects.
**Inputs:** `CountryState`, social spending, war casualties, economic performance, events.
**Outputs:** Updated stability/support scores, triggered political events (election, coup).
**Dependencies:** `models/`.
**Design decisions:** Pure functions. Stability is composite (economic performance + social spending + war fatigue + event shocks). Elections trigger at configured rounds. Coup threshold: stability < 20 AND military spending > social spending. Alliance membership modifies stability via security bonus.

### 9. `engine/engines/technology.py`
**Purpose:** Nuclear program progression, AI/cyber capability advancement.
**Inputs:** `CountryState`, technology budget allocation, espionage events.
**Outputs:** Updated tech levels, breakthrough events, proliferation alerts.
**Dependencies:** `models/`.
**Design decisions:** Pure functions. Nuclear progression is a multi-round track (research -> development -> testing -> deployment). Each stage requires sustained investment. AI/cyber is a parallel track affecting military effectiveness multipliers. Espionage can accelerate or sabotage progression.

### 10. `engine/engines/world_model.py`
**Purpose:** Round orchestrator — calls all four engines in correct sequence, produces world state snapshot.
**Inputs:** Current `WorldStateSnapshot`, all submitted actions for the round.
**Outputs:** New `WorldStateSnapshot` + all generated events.
**Dependencies:** `economic.py`, `military.py`, `political.py`, `technology.py`, `models/`, `services/supabase.py`.
**Design decisions:** 14-step pipeline per `DET_ROUND_WORKFLOW.md`. Execution order matters: economic first (funds available), then military (spend funds), then political (consequences), then technology (long-term). Pass 1 (formulas) -> Pass 2 (coherence check via LLM) -> Pass 3 (narrative generation). Atomic write: entire round result committed in single transaction.

---

## Sprint 3 — Orchestration

### 11. `engine/services/moderator.py`
**Purpose:** AI Super-Moderator (Argus) — autonomous round flow, event injection, narrative generation.
**Inputs:** Current SIM state, round workflow definition, scenario configuration.
**Outputs:** Phase transitions, round triggers, injected events, narrative summaries.
**Dependencies:** `services/llm.py`, `services/supabase.py`, `engines/world_model.py`, `models/`.
**Design decisions:** State machine: `WAITING_SUBMISSIONS -> PROCESSING -> PUBLISHING -> NEXT_ROUND`. Configurable timing (instant for Tier 1 testing, realistic delays for observation). Default budget heuristic for Sprint 3 (before AI agents exist): proportional to previous round with small random variation. Argus uses Claude Sonnet for narrative; Haiku for routine decisions.

### 12. `engine/services/results.py`
**Purpose:** Results export — HTML dashboards, Markdown summaries, CSV indicator tables.
**Inputs:** Complete SIM run data (all rounds, all country states, all events).
**Outputs:** JSON dump, CSV (key indicators across rounds), Markdown narrative summary.
**Dependencies:** `services/supabase.py`, `models/`.
**Design decisions:** `GET /sim-run/{id}/export` returns JSON. `GET /sim-run/{id}/export/csv` returns CSV with columns: round, country, GDP, stability, military_strength, oil_price. Markdown summary generated by LLM (optional, Haiku). Results are read-only views — never modify SIM data.

---

## Sprint 4 — AI Agents

### 13. `engine/services/agent.py`
**Purpose:** AI country agent — 4-block cognitive model, reflection, intent notes, decision generation.
**Inputs:** Agent profile (persona, goals), current world state, event history, conversation outcomes.
**Outputs:** Structured decisions (budget, military orders, trade proposals, political actions).
**Dependencies:** `services/llm.py`, `services/supabase.py`, `models/`.
**Design decisions:** Port KING's 4-block model: Block 1 (rules — init + reflection only, never in conversation context), Block 2 (identity/persona), Block 3 (memory/events), Block 4 (goals/strategy). Intent notes (6-field memo) replace Block 1 in conversation context to prevent rules drowning personality. Reflection triggers: immediate (war declared) vs. batched (minor changes). Atomic block versioning via PostgreSQL. 10 AI agents with distinct character profiles.

### 14. `engine/services/conversation.py`
**Purpose:** Turn-by-turn conversation manager between AI agents, with context caching.
**Inputs:** Two agent profiles, conversation topic/agenda, intent notes from both sides.
**Outputs:** Conversation transcript, negotiation outcome, agreed actions.
**Dependencies:** `services/llm.py`, `services/agent.py`, `models/`.
**Design decisions:** Tier 2 (modelled): agents declare intent, system summarizes outcome (< 5 sec). Tier 3 (full text): turn-by-turn dialogue with end conditions (max turns, agent decides to end, mutual pass). Context caching via Anthropic API (reuse system prompt + Block 2/3 across turns — 85% cost reduction). Fire-and-forget async triggers on phase transitions (ported from KING). Conversation visibility: participants see outcomes, moderator sees full transcript.

---

## Sprint 5 — Integration

### 15. `frontend/`
**Purpose:** Public Display — real-time observation screen for the unmanned spacecraft.
**Inputs:** Supabase Realtime subscriptions (world state, events, round status).
**Outputs:** Rendered UI: hex map, indicator dashboard, event log, news ticker, round clock.
**Dependencies:** Supabase client SDK, Zustand stores, backend Realtime channels.
**Design decisions:** React 18 + TypeScript + Vite + Tailwind. Zustand for state (no Redux). Custom SVG hex grid (10x20 global, 10x10 theater detail) with pan/zoom via viewBox. Country colors at 55% opacity. Dark theme (Midnight Intelligence palette). Unit icons from `UNIT_ICONS_CONFIRMED.svg`. Auto-reconnect on WebSocket drop. No participant UI in Phase 1 — display only. News ticker generated by Haiku via `engine/services/agent.py`.

---

## Cross-Cutting Concerns

| Concern | Approach |
|---------|----------|
| **Error handling** | All engine functions return `Result[T, Error]` pattern. No bare exceptions. Sentry for tracking. |
| **Logging** | Python `logging` module. Structured JSON logs. Request ID in every log line. |
| **Testing** | Layer 1 tests per engine (pure function -> expected output). Layer 2 tests per service (mocked DB). |
| **Idempotency** | All write endpoints accept `idempotency_key`. Deduplication at Supabase level. |
| **Concurrency** | `snapshot_version` on all state writes. Optimistic locking. Retry on conflict. |

---

*This document is a BUILD roadmap — not a full design. Each module's implementation will be validated against DET specs during code review. Updated at sprint boundaries.*
