# Detailed Design Checklist
## Thucydides Trap SIM — Stage 3
**Version:** 1.0 | **Date:** 2026-03-30 | **Status:** PLANNING
**Prerequisite:** SEED gate passed (pending test results)

---

## What Detailed Design Produces

The bridge from "what to build" (SEED) to "how to build" (code). Every deliverable here is DIRECTLY implementable — a developer reads it and writes code without asking questions.

---

## D1 — DATABASE SCHEMA

| # | Item | Deliverable | Source |
|---|------|------------|--------|
| D1.1 | **Complete PostgreSQL schema** — every table, column, type, constraint, index | `DET_D1_DATABASE_SCHEMA.sql` | Derived from F1 (data schema) + F2 (architecture) |
| D1.2 | **RLS policies** — row-level security for every table, enforcing information asymmetry | Within schema file | Derived from F3 (data flows) visibility matrix |
| D1.3 | **Seed data migration** — SQL to load all CSV starting data into the database | `DET_D1_SEED_DATA.sql` | Generated from C4 CSVs |
| D1.4 | **Database functions** — stored procedures for atomic operations (e.g., transaction execution, AI context versioning) | Within schema file | Derived from engine interfaces |

## D2 — SYSTEM CONTRACTS (the shared language)

| # | Item | Deliverable | Source |
|---|------|------------|--------|
| D2.1 | **Event schema** — every event type, exact JSON payload structure | `DET_D2_SYSTEM_CONTRACTS.md` | Derived from G spec (every action → event) |
| D2.2 | **Real-time channel map** — channel names, subscribers, message formats | Within contracts | Derived from G spec + F3 data flows |
| D2.3 | **API endpoint specifications** — OpenAPI/Swagger format, request/response schemas | `DET_D2_API_SPEC.yaml` | Derived from F4 (API contracts) + G spec |
| D2.4 | **Module interface contracts** — exact input/output per engine, per AI module | Within contracts | Derived from D engine interface + E2/E4 |

## D3 — TECHNOLOGY STACK & ARCHITECTURE

| # | Item | Deliverable | Source |
|---|------|------------|--------|
| D3.1 | **Tech stack decision** — final choices for all layers | `DET_D3_TECH_STACK.md` | React/Supabase/Python/Claude/ElevenLabs |
| D3.2 | **Deployment architecture** — how services connect in production | Within tech stack | Vercel + Supabase Cloud + Python service host |
| D3.3 | **Development environment setup** — how to get the project running locally | `DET_D3_DEV_SETUP.md` | |
| D3.4 | **CI/CD pipeline** — automated testing and deployment | Within dev setup | |

## D4 — ENGINE PRODUCTION CODE

| # | Item | Deliverable | Source |
|---|------|------------|--------|
| D4.1 | **World Model Engine** — production Python, API wrapper, input validation | Port from SEED engine code | D8 formulas + existing Python |
| D4.2 | **Live Action Engine** — production Python, real-time API | Port from SEED engine code | D8 formulas + existing Python |
| D4.3 | **Transaction Engine** — production Python or Edge Function | Port from SEED engine code | C6 + existing Python |
| D4.4 | **Engine test suite** — automated formula tests (Layer 1) | `tests/engine/` | Auto-generated from D8 expected values |

## D5 — FRONTEND COMPONENTS

| # | Item | Deliverable | Source |
|---|------|------------|--------|
| D5.1 | **Component architecture** — React component tree per interface | `DET_D5_COMPONENTS.md` | G spec info blocks → components |
| D5.2 | **Participant Interface** — all screens, data binding, actions | React code | G spec G2 |
| D5.3 | **Facilitator Dashboard** — god-view, controls, monitors | React code | G spec G3 |
| D5.4 | **Public Display** — large-screen optimized | React code | G spec G4 |
| D5.5 | **Hex map renderer** — interactive map component | React component | C1 map structure + H1 style |

## D6 — AI INTEGRATION

| # | Item | Deliverable | Source |
|---|------|------------|--------|
| D6.1 | **AI Participant Module** — production implementation of cognitive core + SIM adapter | Code | E2 + CON_F1 + KING reference |
| D6.2 | **Argus Module** — production implementation of 7-block prompt assembly + voice | Code | E4 + CON_F2 + KING reference |
| D6.3 | **LLM provider abstraction** — switchable between Claude/Gemini at runtime | Code | E2 architecture |
| D6.4 | **Voice integration** — ElevenLabs Conversational AI for Argus + AI participants | Code | E4 + CON_F1 |

## D7 — COMMUNICATION SYSTEM

| # | Item | Deliverable | Source |
|---|------|------------|--------|
| D7.1 | **AI meeting system** — request/accept/voice/transcript | Code | G spec G5 |
| D7.2 | **Team channels** — country group chat | Code | G spec G5 |
| D7.3 | **Public broadcast** — moderator announcements | Code | G spec G5 |

## D8 — TESTING INFRASTRUCTURE

| # | Item | Deliverable | Source |
|---|------|------------|--------|
| D8.1 | **Layer 1 test suite** — automated formula tests | `tests/` | D8 formulas → test cases |
| D8.2 | **Layer 2 test suite** — module integration tests | `tests/` | G spec actions → test scenarios |
| D8.3 | **Layer 3 test framework** — AI simulation test runner (production version of current Battery approach) | `tests/simulation/` | TESTER_CONCEPT.md + Battery 4 |
| D8.4 | **Continuous testing pipeline** — tests run on every code change | CI/CD config | |

## D9 — SCENARIO CONFIGURATOR

| # | Item | Deliverable | Source |
|---|------|------------|--------|
| D9.1 | **Template management** — CRUD for scenario templates | Code | G spec G1 (Scenario Configurator) |
| D9.2 | **AI-assisted context refresh** — update scenario to current events | Code | CON_G1 Section 12 |
| D9.3 | **Role assignment UI** — drag-and-drop participant → role mapping | Code | CON_G1 Section 12 |
| D9.4 | **Brief generation** — auto-generate role briefs from template | Code | H3 artefact templates |

---

## Build Sequence

```
PHASE 1 — Foundation (D1, D2, D3)          ← 1-2 weeks
  Database schema, system contracts, tech stack, dev environment

PHASE 2 — Engines (D4)                      ← 1-2 weeks
  Port Python engines to production, API wrappers, formula test suite

PHASE 3 — Facilitator First (D5.3, D7.3)   ← 2-3 weeks
  Facilitator dashboard + broadcast. Need this to test everything else.

PHASE 4 — Participant Core (D5.2, D5.5)    ← 3-4 weeks
  Participant interface + hex map. The main product.

PHASE 5 — AI Integration (D6, D7.1)        ← 2-3 weeks
  AI participants + Argus + AI meeting system

PHASE 6 — Polish & Launch (D5.4, D8, D9)   ← 2-3 weeks
  Public display, full test suite, scenario configurator
```

**Total estimated: 12-18 weeks from Detailed Design start to playable prototype.**

---

## Gate Criteria

- All module integration tests pass (Layer 2)
- AI simulation test produces credible 6-round game (Layer 3)
- Facilitator can run a complete session from dashboard
- 5 human participants + 10 AI participants play simultaneously without errors
- Marat plays one full test session and approves
