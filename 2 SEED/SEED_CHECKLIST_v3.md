# SEED Stage Checklist
## Thucydides Trap SIM — Complete Product Specification
**Version:** 3.0 | **Date:** 2026-03-27 | **Status:** IN PROGRESS

---

### What SEED Produces
The **complete product specification** — SIM scenario + world model engines + AI systems + data architecture + web app specs + visual design + testing infrastructure. Detailed enough to generate all downstream deliverables.

### Gate Criteria
Zero inconsistencies across all seed files. Every name, number, relationship, formula, and data field must match. Marat signs off. VERA certifies consistency.

### File Naming Convention
`SEED_[CODE]_[TOPIC]_v[N].[status].ext` — Section code maps to checklist item. `.frozen` = locked.

---

## 0 — PREREQUISITES

| # | Item | Deliverable | Status |
|---|------|------------|:------:|
| 0.1 | **Retrospective** — concept test lessons | Memory + analysis reports | ● |
| 0.2 | **Templates** — role & country seed standard formats | `SEED_TEMPLATE_ROLE_v1.md` + `SEED_TEMPLATE_COUNTRY_v1.md` | ● |
| 0.3 | **Carry-forward: Relationship Matrix** | `SEED_B3_RELATIONSHIPS_v1.md` | ● |
| 0.4 | **Carry-forward: Public Speaking & Press** | `SEED_C5_PUBLIC_SPEAKING_v1.md` | ● |

---

## A — SCENARIO FOUNDATION

| # | Item | Deliverable | Status |
|---|------|------------|:------:|
| A1 | **Phenomenon reference** — carries forward from Concept | `CON_A1_THUCYDIDES_TRAP_v2.frozen.md` | ● 🔒 |
| A2 | **Core tensions** — carries forward from Concept | `CON_A2_CORE_TENSIONS_v2.frozen.md` | ● 🔒 |
| A3 | **World Context Narrative** — opening briefing, ~1200 words, all participants receive | `SEED_A3_WORLD_CONTEXT_v1.md` | ● |

---

## B — ACTORS & STRUCTURE

| # | Item | Deliverable | Status |
|---|------|------------|:------:|
| B1 | **Country Seeds (16)** — full template per country | `SEED_COUNTRIES/SEED_B1_COUNTRY_[name]_v1.md` (16 files) | ● |
| B2 | **Role Seeds (37)** — all team + solo roles, 9 sections each | `role_briefs/SEED_B2_ROLES_[team]_v1.md` (7 files) | ● |
| B3 | **Relationship Matrix** — 87 key relationships across 37 roles, role-centric, sliceable into briefs | `SEED_B3_RELATIONSHIPS_v1.md` + `SEED_B3_RELATIONSHIPS_v1.html` (interactive graph) | ● |
| B4 | **AI Country Profiles** — NOT NEEDED: AI countries use same role seeds (B2) + country seeds (B1); initialization handled by E2 pipeline | N/A | ● |

---

## C — GAME MECHANICS & MAP

| # | Item | Deliverable | Status |
|---|------|------------|:------:|
| C1 | **Global Hex Map** — 22 countries, 3 chokepoints, hex tessellation | `SEED_C1_MAP_GLOBAL_v1.svg` | ● |
| C2 | **Zone Structure** — hex registry, adjacency, theater appendix | `SEED_C2_MAP_ZONES_v3.md` | ● |
| C3 | **Theater Map (1)** — Eastern Ereb only. Formosa/Mashriq archived (resolved at global hex level per 2026-03-27 decision) | `SEED_C3_THEATER_EASTERN_EREB_v1.svg` | ● |
| C4 | **Starting Data** — all numerical values in CSV format | `data/` folder (9 CSVs) | ● |
| C5 | **Public Speaking & Press** — speech protocol, capture, public commitments | `SEED_C5_PUBLIC_SPEAKING_v1.md` | ● |
| C6 | **Contracts & Collective Decisions** — treaty format, org decisions | `SEED_C6_CONTRACTS_DECISIONS_v1.md` | ● |
| C7 | **Time Structure** — 6-8 rounds, dramatic arc, two-day/single-day formats | `SEED_C7_TIME_STRUCTURE_v1.md` | ● |

---

## D — WORLD MODEL ENGINES

| # | Item | Deliverable | Status |
|---|------|------------|:------:|
| D0 | **Engine Architecture** — three-pass (det→AI→coherence) | Carries from Concept + implemented in code | ● |
| D1 | **Economic Model** — GDP, sanctions, tariffs, oil, inflation, debt | `ENGINE/world_model_engine.py` (implemented) | ● |
| D2 | **Political Model** — stability, support, propaganda, elections, coups | `ENGINE/world_model_engine.py` (implemented) | ● |
| D3 | **Military Model** — RISK combat, amphibious, blockade, production | `ENGINE/live_action_engine.py` (implemented) | ● |
| D4 | **Technology Model** — nuclear, AI tracks, R&D, breakthroughs | `ENGINE/world_model_engine.py` (implemented) | ● |
| D5 | **Narrative Engine** — AI prompts for briefings | `ENGINE/world_model_engine.py` (basic); needs upgrade | ◐ |
| D6 | **Transaction Engine** — bilateral transfers, validation | `ENGINE/transaction_engine.py` (implemented) | ● |
| D7 | **Live Action Engine** — combat, arrests, covert ops | `ENGINE/live_action_engine.py` (implemented) | ● |
| D8 | **Engine Formula Docs** — formal specification of all formulas | `SEED_D8_ENGINE_FORMULAS_v1.md` | ● |

---

## E — AI SYSTEMS

| # | Item | Deliverable | Status |
|---|------|------------|:------:|
| E1 | **AI Participant Architecture** — carries from Concept | `CON_F1_AI_PARTICIPANT_MODULE_v2.frozen.md` | ● 🔒 |
| E2 | **AI Conversation & Negotiation** — how AI agents negotiate | `SEED_E2_AI_CONVERSATIONS_v1.md` + `ENGINE/llm_agent_runner.py` | ● |
| E3 | **AI Navigator Architecture** — carries from Concept | `CON_F2_AI_ASSISTANT_MODULE_v2.frozen.md` | ● 🔒 |
| E4 | **Argus (AI Assistant) Prompt Specs** — 7-block assembly, 3 phases, voice-first | `SEED_E4_ARGUS_PROMPTS_v1.md` | ● |

---

## F — DATA ARCHITECTURE

| # | Item | Deliverable | Status |
|---|------|------------|:------:|
| F1 | **Data Schema** — CSV schemas, column definitions, validation rules | `SEED_F1_DATA_SCHEMA_v1.md` | ● |
| F2 | **Data Architecture** — core data model, store facts/derive assessments | `SEED_F2_DATA_ARCHITECTURE_v1.md` | ● |
| F3 | **Real-Time Data Flows** — engine↔participant↔facilitator | `SEED_F3_DATA_FLOWS_v1.md` | ● |
| F4 | **API Contracts** — interface definitions (15 endpoints) | `SEED_F4_API_CONTRACTS_v1.md` | ● |

---

## G — WEB APP SPECIFICATION

| # | Item | Deliverable | Status |
|---|------|------------|:------:|
| G1 | **App Architecture** — carries from Concept | `CON_G1_WEB_APP_ARCHITECTURE_v2.frozen.md` | ● 🔒 |
| G2 | **Participant Interface** — fixed ref, personal/country/world info, actions, transactions, deployment | `SEED_G_WEB_APP_SPEC_v1.md` (integrated) | ● |
| G3 | **Facilitator Dashboard** — god-view, engine controls, AI manager, overrides | `SEED_G_WEB_APP_SPEC_v1.md` (integrated) | ● |
| G4 | **Public Display** — map, indicators, news ticker, round clock | `SEED_G_WEB_APP_SPEC_v1.md` (integrated) | ● |
| G5 | **Communication System** — AI meetings, team channel, broadcasts (humans talk face to face) | `SEED_G_WEB_APP_SPEC_v1.md` (integrated) | ● |

---

## H — VISUAL DESIGN & MAP

| # | Item | Deliverable | Status |
|---|------|------------|:------:|
| H1 | **UX Style Guide** — dual theme, country colors, typography, emblems, unit icons, Tailwind config | `SEED_H1_UX_STYLE_v2.md` + `SEED_H1_UX_STYLE_DEMO_FINAL.html` | ● 🔒 |
| H2 | **Map Visual Upgrade** — hex maps polished to final quality | SVG files (upgrade from current) | ◐ |
| H3 | **Artefact Templates** — 5 types: intel report, diplomatic cable, personal letter, press bulletin, country briefing | `SEED_H3_ARTEFACT_TEMPLATES_v1.html` | ● |
| H4 | **Print & Event Templates** — name badge, table sign, schedule board, role brief cover, decision form | `SEED_H4_PRINT_TEMPLATES_v1.html` | ● |

---

## I — TESTING ARCHITECTURE

| # | Item | Deliverable | Status |
|---|------|------------|:------:|
| I1 | **Test Harness** — full system with actual engine components | `ENGINE/llm_orchestrator.py` + `ENGINE/run_seed_test.py` | ● |
| I2 | **Negotiation Emulation** — AI-to-AI conversation layer | `ENGINE/llm_agent_runner.py` (implemented) | ● |
| I3 | **Generic Test Battery** — 4-8 full runs, 8 rounds | 9 tests completed (8 heuristic + 1 LLM) | ● |
| I4 | **Focused Test Suite** — targeted scenario tests | 8 focused configs defined; results in `10. TESTS/` | ● |
| I5 | **Calibration & Iteration** — run→analyze→adjust→re-run | 2 iterations completed; stability recalibrated | ◐ |

---

## J — DELIVERY & OPERATIONS

| # | Item | Deliverable | Status |
|---|------|------------|:------:|
| J1 | **Delivery Operations** — carries from Concept | `CON_I1_DELIVERY_OPERATIONS_v2.frozen.md` | ● 🔒 |

---

## STATUS SUMMARY

| Section | Total | ● Done | ◐ In Progress | ○ Not Started | 🔒 Frozen |
|---------|:-----:|:------:|:-------------:|:-------------:|:---------:|
| 0 Prerequisites | 4 | 4 | 0 | 0 | 0 |
| A Scenario | 3 | 3 | 0 | 0 | 2 |
| B Actors | 4 | 4 | 0 | 0 | 0 |
| C Mechanics & Map | 7 | 7 | 0 | 0 | 0 |
| D Engines | 9 | 8 | 1 | 0 | 0 |
| E AI Systems | 4 | 3 | 0 | 0 | 2 |
| F Data Architecture | 4 | 4 | 0 | 0 | 0 |
| G Web App | 5 | 4 | 0 | 0 | 1 |
| H Visual Design | 4 | 3 | 1 | 0 | 1 |
| I Testing | 5 | 4 | 1 | 0 | 0 |
| J Delivery | 1 | 0 | 0 | 0 | 1 |
| **TOTAL** | **50** | **44** | **3** | **0** | **7** |

**Progress: 44/50 done (88%), 3 in progress, 0 not started, 7 frozen (6 Concept + 1 H1)**

---

## What's Done (40 items):
- Prerequisites: templates, retrospective, B3 carry-forward, C5 carry-forward
- Scenario: A1+A2 (frozen from Concept), A3 world context narrative
- Actors: B1 (16 country seeds), B2 (37 core + 3 expansion roles), B3 (relationship matrix + interactive graph), B4 (not needed — AI uses same seeds)
- Mechanics: C1-C7 complete (map, zones, theater, data, public speaking, contracts, time structure)
- Engines: D0-D8 complete (architecture + 7 implemented engines + formula docs)
- AI Systems: E1+E3 (frozen from Concept), E2 (AI conversations), E4 (Argus prompts)
- Data Architecture: F1-F4 complete (schema, architecture, data flows, API contracts)
- Visual: H1 (UX style guide, frozen), H3 (artefact templates), H4 (print templates)
- Testing: I1-I4 complete (harness, negotiation, generic battery, focused suite)

## What's In Progress (3 items):
- D5 — Engine narrative generation (basic, needs upgrade)
- H2 — Map visual polish
- I5 — Calibration iteration (ongoing)

## What Remains (0 items):
All deliverables are either complete or in progress. No items are "not started."

## Recommended Next Priorities:
1. **SEED Gate Review** — VERA consistency check, TESTER validation, Marat sign-off
2. **D5** — Upgrade narrative generation engine (in progress)
3. **H2** — Map visual polish (in progress)
4. **I5** — Calibration iteration (in progress — ongoing)

---

## Changelog
- **v3.0 (2026-03-27):** Complete status update. Section codes added to all deliverables. File references updated to match renamed files. Added engine items D8 (formula docs). Status summary table. 23/50 complete.
- **v2.0 (2026-03-26):** Restructure as integrated product spec. 51 items.
- **v3.2 (2026-03-30):** Complete action review with Marat (31 actions, one-by-one). Major revisions: ground attack (dice, simplified modifiers), blockade (ground-only), nuclear (5-tier, 10-min clock), intelligence (renamed, per-individual pools), sanctions (S-curve), tariffs (per-sector), oil (5 levels), mobilization (finite pool). New mechanics: Court, Impeachment, Protest auto/stimulated, Fatherland appeal. All engine code, D8 formulas, G spec, CSV data updated. F1 schema updated. 5 Change Management entries (CM-001 through CM-005). STATUS.md refreshed. Pre-gate consistency review (VERA): 9/10. Test scenarios for Battery 4 prepared (8 scenarios).
- **v3.1 (2026-03-30):** Added militia/volunteer mechanic (new SEED addition from Conflict SIM4 pattern). Mobilization levels detailed. Web App Spec (G2-G5) created. Consistency fixes applied (operation name, unit type naming, CSV/code sync, SCO org).
- **v1.0 (2026-03-26):** Initial draft. 28 items.

---

## CHANGE MANAGEMENT LOG

### CM-003: Phase B/C Merge (2026-03-30)
**Change:** Concept defined 3 phases per round (A: negotiation, B: world update, C: deployment). SEED merges B+C into single Phase B: production/deployment runs FIRST (instant), then world model processes in parallel. Deployment window open while engine calculates.
**Rationale:** No units lost during world model processing, so deployment and calculation can run concurrently. Saves ~5 min per round.
**Affects Concept:** CON_C3 (Time Structure) — 3 phases → 2 phases.
**Approved by:** Marat (2026-03-30)

### CM-004: AI Assistant renamed "Navigator" → "Argus" (2026-03-29)
**Change:** Working name "Navigator" changed to "Argus" (the hundred-eyed giant).
**Rationale:** "Navigator" conflicted with the role-name space. Argus is memorable and fits the all-seeing-advisor function.
**Affects Concept:** CON_F2 (AI Assistant Module) — name only, architecture unchanged.
**Approved by:** Marat (2026-03-29)

### CM-005: OPEC+ Production 3-level → 5-level (2026-03-30)
**Change:** Oil production choices expanded from Low/Normal/High to Min/Low/Normal/High/Max for more granular gameplay.
**Affects Concept:** CON_C2 (Action System) — oil production input options.
**Approved by:** Marat (2026-03-30, during action review)

### CM-002: Complete Action Review (2026-03-30)
**Change:** All 31 SIM actions reviewed one-by-one with Marat and revised. Major changes to: ground attack (simplified modifiers, dice-based), blockade (ground-forces-only), nuclear system (5-tier with 10-min clock), intelligence (renamed, per-individual pools, always-returns-answer), sanctions (S-curve coalition model), tariffs (per-sector option), oil (5 levels), mobilization (finite depletable pool), assassination (per-country probability), coup (trust mechanic), plus new mechanics: Court (AI judge for democracies), Impeachment (Columbia/Ruthenia), Protest (auto + stimulated).
**Affects Concept:** CON_E1 (Engine Architecture), CON_C2 (Action System), CON_G1 (Web App Architecture). Multiple mechanics revised from concept-level specifications.
**Files updated:** SEED_G_WEB_APP_SPEC_v1.md (full rewrite of actions), SEED_D8_ENGINE_FORMULAS_v1.md (v1.1, 20+ sections updated), world_model_engine.py (sanctions S-curve, oil 5-level, mobilization pool), live_action_engine.py (combat modifiers, blockade, assassination, coup), world_state.py (new constants, mobilization_pool loading), countries.csv (mobilization_pool column), roles.csv (intelligence_pool column).
**Approved by:** Marat (2026-03-30, action-by-action review)

### CM-001: Militia / Volunteer Call (2026-03-30)
**Change:** New mechanic added at SEED level — not in frozen Concept.
**Origin:** Conflict SIM4 pattern (martial law levels) + Marat's direction for invaded/bombed country defense.
**Affects Concept:** CON_E1 (Engine Architecture) — mobilization section should note militia sub-mechanic. CON_C2 (Action System) — militia call as a new action type.
**Decision:** Proceed at SEED level. Concept docs to be updated at next Concept review sweep (minor addition, consistent with existing mobilization framework).
**Approved by:** Marat (2026-03-30, verbal)

### CM-006: Deployment Rules Clarification (2026-03-30)
**Change:** (1) Transit delay removed — deployment is instant, combat delay inherent in round structure. (2) Ship capacity formalized: 1 ground + 2 air units per ship, own country only. (3) Strategic missiles cannot embark. (4) Naval cannot deploy into active blockade. (5) Air per ship corrected from 5 (G spec error) to 2 (D8 correct).
**Rationale:** Simplifies deployment (no tracking of in-transit units). Overstretch mechanic preserved through force positioning choices, not transit timers. Ship capacity needed for amphibious assault mechanics.
**Affects Concept:** CON_C1 (Domains), CON_C2 (Actions), CON_C3 (Time Structure), CON_E1 (Engine). Transit delay language updated. Ship capacity added.
**Affects SEED:** G spec (ship capacity 5→2, transit delay removed), D8 (ground embarkation + blockade restriction added).
**Affects DET:** Naming conventions Section 0, database deployment_validation function.
**Approved by:** Marat (2026-03-30, verbal during deployment rules discussion)
