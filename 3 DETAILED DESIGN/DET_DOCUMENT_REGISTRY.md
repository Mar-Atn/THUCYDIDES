# DET_DOCUMENT_REGISTRY.md
## Canonical Design Documentation Map
**Version:** 1.0 | **Date:** 2026-04-13 | **Status:** ACTIVE
**Purpose:** Single reference for the complete documentation structure across all design tiers.
**Maintained by:** Any agent updating design documents must update this registry.

---

## How to Use This Registry

- **Starting a new session?** Read this file first to understand where everything lives.
- **Looking for a specific topic?** Use the topic index (Section 5).
- **Creating a new document?** Add it to the appropriate section below and update the topic index.
- **Updating an existing document?** Bump its version in this registry.

---

## 1. CONCEPT — What & Why (~8,500 lines)

*Gate passed 2026-03-25. Frozen with BUILD reconciliation notes (2026-04-13).*
*Location:* `1. CONCEPT/CONCEPT V 2.0/`

| Code | File | Purpose | Updated |
|------|------|---------|---------|
| TOP | `CON_TOP_TTT_CONCEPT_v1.frozen.md` | Top-level premise, three-layer trap | — |
| CHK | `CON_CHECKLIST_v3.frozen.md` | Gate checklist (14/21 items, gate passed) | — |
| **A — PHENOMENON** | | | |
| A1 | `CON_A1_THUCYDIDES_TRAP_v2.frozen.md` | Historical phenomenon (12/16 cases led to war) | — |
| A2 | `CON_A2_CORE_TENSIONS_v2.frozen.md` | US-China power transition statement | — |
| **B — ACTORS** | | | |
| B1 | `CON_B1_COUNTRY_STRUCTURE_v2.frozen.md` | 14 countries, teams, strategic roles | — |
| B2 | `CON_B2_ROLES_ARCHITECTURE_v2.frozen.md` | 7-9 roles per team, human vs AI design | — |
| **C — MECHANICS** | | | |
| C1 | `CON_C1_DOMAINS_ARCHITECTURE_v2.frozen.md` | 4 domains (military, economy, politics, tech) | ★ BUILD |
| C2 | `CON_C2_ACTION_SYSTEM_v2.frozen.md` | Action catalog (25 implemented with contracts) | ★ BUILD |
| C3 | `CON_C3_TIME_STRUCTURE_v2.frozen.md` | Round flow (Phase A / Phase B / Inter-Round) | ★ BUILD |
| C4 | `CON_C4_MAP_CONCEPT_v2.frozen.md` | Two-layer map (global 10×20 + theater 10×10) | — |
| **D — PARAMETERS** | | | |
| D0 | `CON_D0_PARAMETER_STRUCTURE_v2.frozen.md` | Block A/B/C → Template / Scenario / Run | ★ BUILD |
| **E — ENGINES** | | | |
| E1 | `CON_E1_ENGINE_ARCHITECTURE_v2.frozen.md` | 3 processing systems + action dispatcher | ★ BUILD |
| **F — AI** | | | |
| F1 | `CON_F1_AI_PARTICIPANT_MODULE_v2.frozen.md` | 4-block cognitive model, 10 context blocks | ★ BUILD |
| F2 | `CON_F2_AI_ASSISTANT_MODULE_v2.frozen.md` | Navigator — personal AI mentor for participants | — |
| **G — WEB APP** | | | |
| G1 | `CON_G1_WEB_APP_ARCHITECTURE_v2.frozen.md` | 3-layer platform (participant/facilitator/public) | — |
| **I — DELIVERY** | | | |
| I1 | `CON_I1_DELIVERY_OPERATIONS_v2.frozen.md` | Facilitator model, logistics, debrief | — |

*Also: `prep/` subdirectory contains 8 historical drafts (v1.0-v1.1). Not maintained.*

---

## 2. SEED — How (Specification Level) (~27,000 lines)

*Gate passed 2026-03-28. 88% complete (44/50 items). BUILD reconciliation 2026-04-13.*
*Location:* `2 SEED/`

### A — Scenario Foundation

| File | Purpose | Updated |
|------|---------|---------|
| `SEED_A3_WORLD_CONTEXT_v1.md` | Opening narrative — the world in July 2026 | — |
| `SEED_CHECKLIST_v3.md` | Master checklist (44/50 done) | — |
| `SEED_COMPLETION_REVIEW.md` | Coverage matrix across all domains | — |
| `STATUS.md` | Progress dashboard | — |

### B — Actors & Structure

| File | Purpose | Count |
|------|---------|-------|
| `B_ACTORS/B1_COUNTRIES/SEED_B1_COUNTRY_*_v1.md` | Full country profiles | 16 countries |
| `B_ACTORS/B2_ROLES/SEED_B2_ROLES_*_v1.md` | Role briefs with objectives, powers, ticking clocks | 40 roles across 8 files |
| `B_ACTORS/SEED_B3_RELATIONSHIPS_v1.md` | 87 key relationships (asymmetric, role-centric) | 1 file |
| `B_ACTORS/B*/SEED_TEMPLATE_*_v1.md` | Templates for country/role briefs | 2 templates |

### C — Mechanics & Data

| File | Purpose | Updated |
|------|---------|---------|
| **Map System** (`C1_MAP/`) | | |
| `SEED_C1_MAP_STRUCTURE_v4.md` | Global 10×20 hex grid architecture | — |
| `SEED_C1_MAP_GLOBAL_STATE_v4.json` | Hex ownership (JSON, authoritative) | — |
| `SEED_C3_THEATER_EASTERN_EREB_*.md/json` | Theater 1: Sarmatia-Ruthenia front (10×10) | — |
| `SEED_C3_THEATER_MASHRIQ_*.md/json` | Theater 2: Gulf war (10×10) | — |
| **Seed Data** (`C4_DATA/`) | | |
| `countries.csv` (21), `roles.csv` (41), `organizations.csv` (10) | Master entity tables | — |
| `relationships.csv` (381), `units.csv` (346), `zones.csv` (183) | Relationship & geography data | — |
| `zone_adjacency.csv` (247), `tariffs.csv` (30), `sanctions.csv` (37) | Bilateral & topology data | — |
| `org_memberships.csv` (61), `deployments.csv` (147) | Membership & starting positions | — |
| `units_layouts/` (start_one.csv, Test1.csv) | Alternate unit starting layouts | — |
| **Mechanics Docs** | | |
| `SEED_C_MAP_UNITS_MASTER_v1.md` | Master integration: map + units + Template/Scenario/Run | ★ v1.1 |
| `SEED_C5_PUBLIC_SPEAKING_v1.md` | Communication protocol (speeches, press, meetings) | — |
| `SEED_C6_CONTRACTS_DECISIONS_v1.md` | Agreements, organizations, typed contract layer | ★ v1.1 |
| `SEED_C7_TIME_STRUCTURE_v1.md` | Round flow: Phase A / Phase B / Inter-Round | ★ v1.1 |

### D — Engines

| File | Purpose | Updated |
|------|---------|---------|
| `SEED_D8_ENGINE_FORMULAS_v1.md` | All formulas: 14-step 3-pass world model (~2,400 lines) | — |
| `SEED_D9_CONTEXT_ASSEMBLY_v1.md` | Context blocks for LLM agents | — |
| `SEED_D10_ENGINE_JUDGMENT_v1.md` | NOUS judgment layer (Pass 2) | — |
| `SEED_D11_JUDGMENT_METHODOLOGY_v1.md` | What TTT models, designed asymmetries | — |
| `SEED_D12_PROMPTS_CATALOG_v1.md` | Unified sim_config prompt templates | — |
| `SEED_D13_MODULE_ARCHITECTURE_v1.md` | Module structure snapshot | — |
| `SEED_D_ENGINE_INTERFACE_v1.md` | Engine input/output API contracts | — |
| `SEED_D_DEPENDENCIES_v1.md` | Calculation order & data dependencies | — |
| `SEED_D_UNIT_DATA_MODEL_v1.md` | 11-column unit entity schema | — |
| `SEED_D_TEST_SCENARIOS_v1.md` | Test battery (8 scenarios) | — |
| `SEED_D_TEST_RESULTS_v[1-4].md` | Calibration progression (4 versions) | — |

### E — AI Participant & Conversations

| File | Purpose | Updated |
|------|---------|---------|
| `SEED_E2_AI_CONVERSATIONS_v1.md` | 4-block cognitive model, conversation engine | — |
| `SEED_E4_ARGUS_PROMPTS_v1.md` | AI assistant (Argus/Navigator) prompt specs | — |
| `SEED_E5_AI_PARTICIPANT_MODULE_v1.md` | Autonomous agent spec (v2.0, ~800 lines) | — |
| `SEED_E6_AI_TEST_INTERFACE_v1.md` | Testing harness for AI participants | — |

### F — Data Architecture

| File | Purpose | Updated |
|------|---------|---------|
| `SEED_F1_DATA_SCHEMA_v1.md` | Per-column CSV schema documentation | — |
| `SEED_F2_DATA_ARCHITECTURE_v1.md` | Design principles + Template/Scenario/Run model | ★ v1.1 |
| `SEED_F3_DATA_FLOWS_v1.md` | Round lifecycle data flows | — |
| `SEED_F4_API_CONTRACTS_v1.md` | API conventions (JSON, errors, pagination) | — |

### G — Web App

| File | Purpose |
|------|---------|
| `SEED_G_WEB_APP_SPEC_v1.md` | 4 interfaces (participant, facilitator, public, AI) |
| `ACTION_REVIEW_CHANGELOG.md` | Action design changes during SEED phase |

### H — Visual Design

| File | Purpose |
|------|---------|
| `SEED_H1_UX_STYLE_v2.md` | UX style guide (frozen) — colors, typography, components |

---

## 3. DETAILED DESIGN — How (Implementation Level) (~16,000 lines)

*Gate passed 2026-04-01. BUILD reconciliation 2026-04-13.*
*Location:* `3 DETAILED DESIGN/`

### A — Calibration

| File | Purpose | Version |
|------|---------|---------|
| `A1_ROLE_REVIEW_CHANGES.md` | 40-role walkthrough with Marat | — |
| `DET_A1_ROLE_CALIBRATION_v1.md` | Role calibration table (objectives, cognitive load) | 1.0 |
| `DET_A2_DATA_CALIBRATION.md` | GDP/military scaling methodology | 1.0 |
| `DET_A3_ARTEFACT_INVENTORY_v1.md` | Role pack contents (intel reports, cables, letters) | 1.0 |

### B — Database

| File | Purpose | Version |
|------|---------|---------|
| `DET_B1_DATABASE_SCHEMA.sql` | PostgreSQL schema for Supabase | ★ 1.3 |
| `DET_B1_SCHEMA_ADDENDUM_BUILD.sql` | 26 new tables from BUILD (pending merge into B1 v1.4) | 1.0 |
| `DET_B1a_TEMPLATE_TAXONOMY.sql` | Template/Scenario/Run SQL definitions | 1.0 |
| `DET_B3_SEED_DATA.sql` | Seed data migration (countries, roles, zones, etc.) | 1.0 |

### C — System Contracts & Communication

| File | Purpose | Version |
|------|---------|---------|
| `DET_C1_SYSTEM_CONTRACTS.md` | Event schemas, real-time channels, module interfaces | 1.3 |
| `DET_CONTRACTS_COMMUNICATION.md` | **★ NEW** Typed contract layer, transactions, agreements | 1.0 |

### D — Infrastructure

| File | Purpose | Version |
|------|---------|---------|
| `DET_D1_TECH_STACK.md` | React/FastAPI/Supabase/Gemini+Claude | 1.0 |
| `DET_D6_DEV_SETUP.md` | Development environment setup | 1.0 |
| `DET_D7_VERIFICATION.md` | Infrastructure verification results | 1.0 |

### E — Execution & Testing

| File | Purpose | Version |
|------|---------|---------|
| `DET_E3_DEV_PLAN_v1.md` | 3-phase unmanned spacecraft strategy | 1.0 |
| `DET_E3_EXECUTION_CONCEPT_DRAFT.md` | Early execution sketch | 0.1 |
| `DET_E4_TESTING_ARCH_v1.md` | 3-layer test architecture (L1/L2/L3) | 1.0 |
| `DET_E5_MODULE_SPECS.md` | Per-module bridge specifications | 1.0 |

### F — Engine, API & Action Specs

| File | Purpose | Version |
|------|---------|---------|
| `DET_F5_ENGINE_API.md` | REST API specification (FastAPI endpoints) | 1.2 |
| `DET_F_SCENARIO_CONFIG_SCHEMA.md` | Scenario sparse override specification | 1.0 |
| `DET_NAMING_CONVENTIONS.md` | Canonical naming dictionary (snake_case, enums, IDs) | 1.0 |
| `DET_UNIT_MODEL_v1.md` | Unit entity engineering spec (CSV→Pydantic→SQL→TS) | 1.0 |
| `DET_ACTION_DISPATCHER.md` | **★ NEW** Central routing for 25 action types | 1.0 |
| `DET_ELECTIONS.md` | **★ NEW** Full election mechanics (nominations, voting, resolution) | 1.0 |
| `DET_MAP_SYSTEM.md` | **★ NEW** Map engineering spec (hex geometry, APIs, rendering, edit mode) | 1.0 |

### Workflow & Orchestration

| File | Purpose | Version |
|------|---------|---------|
| `DET_ROUND_WORKFLOW.md` | **★ REWRITTEN** Phase A / Phase B / Inter-Round canonical flow | 2.0 |
| `DET_EDGE_FUNCTIONS.md` | Supabase Edge Function specifications | 1.0 |

### Reference & Audits

| File | Purpose | Version |
|------|---------|---------|
| `DET_KING_AI_ANALYSIS.md` | KING SIM AI architecture port analysis | — |
| `DET_CHECKLIST_v1.md` | Gate checklist (passed 2026-04-01) | 3.0 |
| `REUNIFICATION_AUDIT_2026-04-06.md` | Design vs implementation drift analysis | — |
| `STRICT_AUDIT_2026-04-06.md` | Completeness assessment | — |

---

## 4. BUILD PHASE — Source of Truth (contracts, cards, checkpoints)

*Location:* `PHASES/UNMANNED_SPACECRAFT/`
*These documents are NOT part of the CONCEPT/SEED/DET hierarchy. They are the BUILD
source of truth that drives reconciliation upward.*

| Type | Count | Purpose |
|------|-------|---------|
| **Locked Contracts** (`CONTRACT_*.md`) | 28 | Input/output specs for every action |
| **Reference Cards** (`CARD_*.md`) | 5 | Architecture, actions, formulas, template, observatory |
| **Checkpoints** (`CHECKPOINT_*.md`) | 11 | Completion records for vertical slices |
| **Plans** (`PLAN_*.md`) | 2 | Forward-looking sprint plans |
| **Audits** (`AUDIT/`) | 7 | Quality checks and calibration logs |
| **Core** (PHASE.md, REFERENCES.md, etc.) | 9 | Phase scope, taxonomy, concepts, reconciliation log |

---

## 5. TOPIC INDEX — Where to Find What

| Topic | CONCEPT | SEED | DET | PHASE |
|-------|---------|------|-----|-------|
| **Action catalog (25 types)** | C2 | C7 | DET_ACTION_DISPATCHER | CARD_ACTIONS |
| **Round flow (Phase A/B/Inter-Round)** | C3, E1 | C7 | DET_ROUND_WORKFLOW v2.0 | CONTRACT_ROUND_FLOW |
| **Template/Scenario/Run** | D0 | F2, C_MAP_UNITS §5 | DET_F_SCENARIO_CONFIG, B1a | F1_TAXONOMY |
| **Database schema** | — | F1 | DET_B1 + Addendum | — |
| **Elections** | C1 | D8 (formulas) | DET_ELECTIONS | CONTRACT_ELECTIONS |
| **Contracts/communication** | E1 | C6 | DET_CONTRACTS_COMMUNICATION | CONTRACT_TRANSACTIONS, _AGREEMENTS |
| **AI participant** | F1 | E5, E2 | — | AI_CONCEPT |
| **Military combat** | C2 | D8 (formulas) | — | CONTRACT_GROUND/AIR/NAVAL/NUCLEAR |
| **Covert operations** | C2 | D8 (formulas) | — | CONTRACT_SABOTAGE/PROPAGANDA/etc. |
| **Power assignments** | C1 | — | DET_CONTRACTS_COMMUNICATION §D | CONTRACT_POWER_ASSIGNMENTS |
| **Run roles** | C1 | — | DET_CONTRACTS_COMMUNICATION §D | CONTRACT_RUN_ROLES |
| **Map & units** | C4 | C1_MAP, C_MAP_UNITS | DET_MAP_SYSTEM, DET_UNIT_MODEL | CARD_TEMPLATE |
| **Country data (21)** | B1 | B1_COUNTRIES (16 files) | DET_A2 (calibration) | — |
| **Role data (40)** | B2 | B2_ROLES (8 files) | DET_A1 (calibration) | — |
| **Formulas (all engines)** | — | D8 | — | CARD_FORMULAS |
| **Context assembly** | F1 | D9 | — | — |
| **NOUS / judgment** | — | D10, D11 | — | — |
| **Web app** | G1 | G_WEB_APP | DET_D1 (tech stack) | CARD_OBSERVATORY |
| **UX / visual** | — | H1 | — | — |
| **Testing** | — | D_TEST_SCENARIOS | DET_E4 | CHECKPOINT_* |
| **API contracts** | — | F4 | DET_F5, DET_EDGE_FUNCTIONS | — |
| **Naming conventions** | — | — | DET_NAMING_CONVENTIONS | CARD_ARCHITECTURE |

---

## 6. TOTALS

| Tier | Files | Approximate Lines |
|------|-------|-------------------|
| CONCEPT | 15 frozen + 8 prep = 23 | ~8,500 |
| SEED | 73 (16 countries + 8 roles + 12 CSVs + 37 docs) | ~27,000 |
| DET | 29 | ~16,000 |
| PHASE (BUILD) | 62 (28 contracts + 5 cards + 11 checkpoints + 18 other) | ~12,000 |
| **Total** | **187** | **~63,500** |

---

*This registry is the single source of truth for the documentation structure. When in
doubt about where a topic is documented, start here.*
