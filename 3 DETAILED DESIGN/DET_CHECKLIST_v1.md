# Detailed Design Checklist
## Thucydides Trap SIM — Stage 3
**Version:** 3.0 | **Date:** 2026-04-01 | **Status:** GATE PASSED — DET COMPLETE
**Prerequisite:** SEED gate PASSED

---

## What Detailed Design Produces

Everything needed so that BUILD can start with zero ambiguity. No code is written in this stage — only specifications, schemas, contracts, configurations, and content. The gate question: "Can a developer sit down and start coding without asking questions?"

---

## A — FINAL SIM CALIBRATION

| # | Item | Deliverable |
|---|------|------------|
| A1 | **Role calibration** — verify all 40 roles have balanced starting positions, realistic card pools, correct powers | Updated roles.csv + role seeds |
| A2 | **Data calibration** — final pass on all CSV numbers based on gate test results | Updated countries.csv + all CSVs |
| A3 | **Artefact content** — write actual classified reports, cables, letters for each role pack | Role pack content files (per H3 templates) |
| A4 | **Balance verification** — run calibration battery (focused tests on specific mechanics flagged during gate) | Test results in `10. TESTS/` |

## B — DATABASE & INFRASTRUCTURE DESIGN

| # | Item | Deliverable |
|---|------|------------|
| B1 | **Complete PostgreSQL schema** — every table, column, type, constraint, index, foreign key | `DET_B1_DATABASE_SCHEMA.sql` |
| B2 | **RLS policies** — row-level security for every table, enforcing information asymmetry per F3 visibility matrix | Within schema file |
| B3 | **Seed data migration** — SQL to load all CSV starting data into the database | `DET_B3_SEED_DATA.sql` |
| B4 | **Database functions** — stored procedures for atomic operations (transaction execution, AI context versioning, election processing) | Within schema file |

## C — SYSTEM CONTRACTS (the shared language)

| # | Item | Deliverable |
|---|------|------------|
| C1 | **Event schema** — every event type, exact JSON payload | `DET_C1_SYSTEM_CONTRACTS.md` |
| C2 | **Real-time channel map** — channel names, subscribers, message formats | Within contracts |
| C3 | **API specification** — OpenAPI/Swagger, request/response schemas for all endpoints | `DET_C3_API_SPEC.yaml` |
| C4 | **Module interface contracts** — exact input/output per engine, per AI module | Within contracts |

## D — TECHNOLOGY & ENVIRONMENT SETUP

| # | Item | Deliverable |
|---|------|------------|
| D1 | **Tech stack document** — final confirmed choices for all layers | `DET_D1_TECH_STACK.md` |
| D2 | **Supabase project** — created, configured, schema deployed, seed data loaded | Live Supabase instance |
| D3 | **Vercel project** — created, linked to Git repo, environment variables set | Live Vercel instance |
| D4 | **API keys** — Anthropic (Claude), Google (Gemini), ElevenLabs (voice) — all provisioned and tested | Secure key storage |
| D5 | **Git repository structure** — monorepo or multi-repo, branch strategy, CI/CD pipeline | Configured repo |
| D6 | **Development environment** — local setup guide, tested on clean machine | `DET_D6_DEV_SETUP.md` |
| D7 | **Verify all infrastructure** — can log in, can query database, can call LLM API, can deploy to Vercel, real-time subscriptions work | Verification checklist |

## E — DEVELOPMENT PROCESS SETUP

| # | Item | Deliverable |
|---|------|------------|
| E1 | **CLAUDE.md v2** — updated for BUILD phase: agent team for development, coding standards, testing protocols, commit conventions, review process | Updated CLAUDE.md |
| E2 | **Agent team for BUILD** — which agents do what during development (frontend agent, backend agent, tester, etc.) | Updated `.claude/agents/` |
| E3 | **Development plan** — module build sequence, sprint breakdown, milestones, demo points | `DET_E3_DEV_PLAN.md` |
| E4 | **Testing architecture** — Layer 1/2/3 test infrastructure, CI/CD integration, how to run each layer | `DET_E4_TESTING_ARCH.md` |
| E5 | **Module specifications** — per module: component list, data bindings, state management, real-time subscriptions | `DET_E5_MODULE_SPECS.md` |

## F — COMPONENT DESIGN

| # | Item | Deliverable |
|---|------|------------|
| F1 | **Participant Interface components** — React component tree, data binding per info block, action flow per action type | `DET_F1_PARTICIPANT_COMPONENTS.md` |
| F2 | **Facilitator Dashboard components** — same level of detail | `DET_F2_FACILITATOR_COMPONENTS.md` |
| F3 | **Public Display components** | `DET_F3_PUBLIC_DISPLAY_COMPONENTS.md` |
| F4 | **Hex map renderer specification** — how to render the map, unit placement, zoom, interaction | `DET_F4_MAP_RENDERER.md` |
| F5 | **Engine API wrapper** — how Python engines are called from the web app (FastAPI routes, request/response formats) | `DET_F5_ENGINE_API.md` |

---

## Gate Criteria

Before BUILD starts:

- [x] All CSVs finalized and loaded into Supabase — 2026-04-01, seed data verified (see D7)
- [x] Database schema deployed and verified — 26 tables, 4 migrations, RLS enabled
- [x] All API keys provisioned and tested — Anthropic, Gemini, ElevenLabs (stored), Supabase
- [x] Vercel + Supabase + Git all connected and deployable
- [x] System contracts document complete — C1 (2179 lines), C3 (OpenAPI spec)
- [x] CLAUDE.md v2 approved by Marat — 2026-04-01
- [x] Development plan approved by Marat — E3 v1.0
- [ ] At least 3 role artefact packs complete — DEFERRED to Phase 2 (unmanned spacecraft has no human players)
- [ ] One "hello world" deployment — Sprint 1 task (not DET gate blocker per unmanned strategy)

---

## Overall Product Lifecycle

```
IDEA
  └── CONCEPT (what & why)                          ✅ PASSED
        └── SEED (canonical specs)                   ✅ PASSED
              └── DETAILED DESIGN (how, exactly)     ✅ PASSED 2026-04-01
                    └── [GATE: ready to build?]       ✅ YES
                          └── BUILD (implementation)  ← WE ARE HERE
                                ├── Module 1: Platform
                                ├── Module 2: Engines
                                ├── Module 3: Facilitator
                                ├── Module 4: Participant
                                ├── Module 5: AI Integration
                                └── Module 6: Polish
                                      └── TEST / OPERATE
                                            └── LEARN → improve → next SIM
```

Each stage produces deliverables that feed the next. No stage is skipped. Marat signs off every gate.
