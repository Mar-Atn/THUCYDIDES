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
| 0.3 | **Carry-forward: Relationship Matrix** | `SEED_B3_RELATIONSHIPS_v1.md` | ○ |
| 0.4 | **Carry-forward: Public Speaking & Press** | `SEED_C5_PUBLIC_SPEAKING_v1.md` | ○ |

---

## A — SCENARIO FOUNDATION

| # | Item | Deliverable | Status |
|---|------|------------|:------:|
| A1 | **Phenomenon reference** — carries forward from Concept | `CON_A1_THUCYDIDES_TRAP_v2.frozen.md` | ● 🔒 |
| A2 | **Core tensions** — carries forward from Concept | `CON_A2_CORE_TENSIONS_v2.frozen.md` | ● 🔒 |
| A3 | **World Context Narrative** — opening briefing, ~2000 words | `SEED_A3_WORLD_CONTEXT_v1.md` | ○ |

---

## B — ACTORS & STRUCTURE

| # | Item | Deliverable | Status |
|---|------|------------|:------:|
| B1 | **Country Seeds (16)** — full template per country | `SEED_COUNTRIES/SEED_B1_COUNTRY_[name]_v1.md` (16 files) | ● |
| B2 | **Role Seeds (37)** — all team + solo roles, 9 sections each | `role_briefs/SEED_B2_ROLES_[team]_v1.md` (7 files) | ● |
| B3 | **Relationship Matrix** — bilateral relationships, all country pairs | `SEED_B3_RELATIONSHIPS_v1.md` | ○ |
| B4 | **AI Country Profiles** — 4-block cognitive initialization for AI countries | `SEED_B4_AI_PROFILES_v1.md` | ○ |

---

## C — GAME MECHANICS & MAP

| # | Item | Deliverable | Status |
|---|------|------------|:------:|
| C1 | **Global Hex Map** — 22 countries, 3 chokepoints, hex tessellation | `SEED_C1_MAP_GLOBAL_v1.svg` | ● |
| C2 | **Zone Structure** — hex registry, adjacency, theater appendix | `SEED_C2_MAP_ZONES_v3.md` | ● |
| C3 | **Theater Maps (3)** — Eastern Ereb, Formosa, Mashriq | `SEED_C3_THEATER_[name]_v1.svg` (3 files) | ● |
| C4 | **Starting Data** — all numerical values in CSV format | `data/` folder (9 CSVs) | ● |
| C5 | **Public Speaking & Press** — speech protocol, Veritas mechanic | `SEED_C5_PUBLIC_SPEAKING_v1.md` | ○ |
| C6 | **Contracts & Collective Decisions** — treaty format, org decisions | `SEED_C6_CONTRACTS_DECISIONS_v1.md` | ○ |
| C7 | **Time Structure** — finalize as 8 rounds | Confirmed in engine; formal doc pending | ◐ |

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
| D8 | **Engine Formula Docs** — formal specification of all formulas | `SEED_D8_ENGINE_FORMULAS_v1.md` | ○ |

---

## E — AI SYSTEMS

| # | Item | Deliverable | Status |
|---|------|------------|:------:|
| E1 | **AI Participant Architecture** — carries from Concept | `CON_F1_AI_PARTICIPANT_MODULE_v2.frozen.md` | ● 🔒 |
| E2 | **AI Conversation & Negotiation** — how AI agents negotiate | `ENGINE/llm_agent_runner.py` (implemented in test); formal spec pending | ◐ |
| E3 | **AI Navigator Architecture** — carries from Concept | `CON_F2_AI_ASSISTANT_MODULE_v2.frozen.md` | ● 🔒 |
| E4 | **AI Navigator Prompt Specs** — per-phase templates | `SEED_E4_NAVIGATOR_PROMPTS_v1.md` | ○ |

---

## F — DATA ARCHITECTURE

| # | Item | Deliverable | Status |
|---|------|------------|:------:|
| F1 | **Data Schema** — CSV schemas, column definitions, validation rules | `SEED_F1_DATA_SCHEMA_v1.md` | ● |
| F2 | **Event Log Schema** — action logging for analytics | `SEED_F2_EVENT_LOG_v1.md` | ○ |
| F3 | **Real-Time Data Flows** — engine↔participant↔facilitator | `SEED_F3_DATA_FLOWS_v1.md` | ○ |
| F4 | **API Contracts** — interface definitions | `SEED_F4_API_CONTRACTS_v1.md` | ○ |

---

## G — WEB APP SPECIFICATION

| # | Item | Deliverable | Status |
|---|------|------------|:------:|
| G1 | **App Architecture** — carries from Concept | `CON_G1_WEB_APP_ARCHITECTURE_v2.frozen.md` | ● 🔒 |
| G2 | **Participant Interface Spec** | `SEED_G2_APP_PARTICIPANT_v1.md` | ○ |
| G3 | **Facilitator Dashboard Spec** | `SEED_G3_APP_FACILITATOR_v1.md` | ○ |
| G4 | **Public Display Spec** | `SEED_G4_APP_PUBLIC_DISPLAY_v1.md` | ○ |
| G5 | **Communication System Spec** | `SEED_G5_APP_COMMUNICATIONS_v1.md` | ○ |

---

## H — VISUAL DESIGN & MAP

| # | Item | Deliverable | Status |
|---|------|------------|:------:|
| H1 | **UX Style Guide** — colors, typography, emotional register | `SEED_H1_UX_STYLE_v1.md` | ○ |
| H2 | **Map Visual Upgrade** — hex maps polished to final quality | SVG files (upgrade from current) | ◐ |
| H3 | **Artefact Templates** — role briefs, action cards, intel reports | Templates (HTML/CSS) | ○ |
| H4 | **Presentation & Print Templates** — intro/debrief decks, badges | Templates | ○ |

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
| 0 Prerequisites | 4 | 2 | 0 | 2 | 0 |
| A Scenario | 3 | 2 | 0 | 1 | 2 |
| B Actors | 4 | 2 | 0 | 2 | 0 |
| C Mechanics & Map | 7 | 4 | 1 | 2 | 0 |
| D Engines | 9 | 7 | 1 | 1 | 0 |
| E AI Systems | 4 | 1 | 1 | 1 | 2 |
| F Data Architecture | 4 | 1 | 0 | 3 | 0 |
| G Web App | 5 | 0 | 0 | 4 | 1 |
| H Visual Design | 4 | 0 | 1 | 3 | 0 |
| I Testing | 5 | 4 | 1 | 0 | 0 |
| J Delivery | 1 | 0 | 0 | 0 | 1 |
| **TOTAL** | **50** | **23** | **5** | **19** | **6** |

**Progress: 23/50 done (46%), 5 in progress, 19 not started, 6 frozen from Concept**

---

## What's Done (23 items):
- All 16 country seeds, all 37 role seeds
- Global hex map + 3 theater maps + zone structure
- All 9 CSV data files (starting data)
- 7 of 8 engine models implemented (code)
- Data schema
- Test harness + negotiation emulation + 9 test runs
- Templates, retrospective

## What's In Progress (5 items):
- Engine narrative generation (basic, needs upgrade)
- AI conversation specs (implemented in code, needs formal doc)
- Time structure formalization
- Map visual polish
- Calibration iteration (ongoing)

## What Remains (19 items):
- B3 Relationship matrix, B4 AI profiles
- A3 World context narrative
- C5 Public speaking, C6 Contracts
- D8 Engine formula documentation
- E4 Navigator prompts
- F2-F4 Event log, data flows, API contracts
- G2-G5 Web app screen specs
- H1 UX style guide, H3-H4 Templates

## Recommended Next Priorities:
1. **B3** — Relationship matrix (informs everything bilateral)
2. **A3** — World context narrative (the opening briefing)
3. **H1** — UX style guide (informs all visual work)
4. **D8** — Engine formula docs (formalize what's in code)
5. **C5** — Public speaking & press (carry-forward, small)

---

## Changelog
- **v3.0 (2026-03-27):** Complete status update. Section codes added to all deliverables. File references updated to match renamed files. Added engine items D8 (formula docs). Status summary table. 23/50 complete.
- **v2.0 (2026-03-26):** Restructure as integrated product spec. 51 items.
- **v1.0 (2026-03-26):** Initial draft. 28 items.
