# SEED Stage Checklist
## Thucydides Trap SIM — Complete Product Specification
**Version:** 2.0 | **Date:** 2026-03-26 | **Status:** DRAFT — awaiting Marat approval

---

### What SEED produces

SEED is the **complete product specification** — detailed enough to generate all downstream deliverables (detailed design, web app code, participant materials, production assets). It covers the integrated product: SIM scenario + world model engines + web app architecture + AI systems + data architecture + visual design + testing infrastructure.

Each concept-stage document (A1-I1) either carries forward intact or is deepened to SEED level. New elements are added where the product requires them.

### Gate criteria

Zero inconsistencies across all seed files. Every name, number, relationship, formula, data field, and API contract must match across documents. Marat signs off. Domain validators confirm. VERA certifies consistency.

---

## 0 — PREREQUISITES

| # | Item | Deliverable | Status |
|---|------|------------|:------:|
| 0.1 | **Retrospective** — concept test lessons captured | Learnings in memory + `TTT_TEST_ANALYSIS_V2.md` | ● |
| 0.2 | **Role & Country Seed Templates** — standard structure agreed before writing any briefs | `SEED_ROLE_TEMPLATE.md` + `SEED_COUNTRY_TEMPLATE.md` | ○ |
| 0.3 | **Concept carry-forward: B4 Relationship Matrix** — research real protagonists online, map bilateral tensions/alignments | `B4_TTT_RELATIONSHIP_MATRIX.md` | ○ |
| 0.4 | **Concept carry-forward: C5 Public Speaking & Press** | `C5_TTT_PUBLIC_SPEAKING_PRESS.md` | ○ |

---

## A — SCENARIO FOUNDATION

Concept status: **strong** (A1 phenomenon reference, A2 core tensions — both complete). SEED deepens with canonical world narrative.

| # | Item | Concept | SEED adds | Deliverable |
|---|------|---------|-----------|-------------|
| A1 | **Phenomenon reference** | ● Complete (3-layer model, flashpoints, clocks) | No change — carries forward | A1 v2 (intact) |
| A2 | **Core tensions** | ● Complete (5 attractors, resolution conditions) | No change — carries forward | A2 v2 (intact) |
| A3 | **World Context Narrative** | — (new) | Canonical state of the world at H2 2026. Public facts all participants receive. ~2000 words. The "opening briefing." | `SEED_WORLD_CONTEXT.md` |

---

## B — ACTORS & STRUCTURE

Concept status: **strong** (countries and roles architected). SEED is the **biggest work area** — deepening every country and every role to character-level detail.

| # | Item | Concept | SEED adds | Deliverable |
|---|------|---------|-----------|-------------|
| B1 | **Country roster & organizations** | ● Complete (21 countries, 8 orgs) | Minor refinements from concept test | B1 v3 (updated) |
| B2 | **Roles architecture** | ● Complete (6 teams, 40+ roles) | Structural refinements from concept test | B2 v3 (updated) |
| B3 | **Country Seeds (21)** | ◐ Skeleton only | Full seed per country in standard template: geography, regime, economy, military, alliances, internal dynamics, key challenges, relationship to the Trap. Research real-world data and protagonists. | `SEED_COUNTRIES/SEED_B1_COUNTRY_[name]_v1.md` (16 files) |
| B4 | **Role Seeds (40+)** | — (new at this depth) | Full seed per role: bio/character, position/resources/powers, interests/objectives/needs, views/beliefs/values, key relationships, ticking clock, core dilemma. Research real protagonists. **Work role-by-role with Marat.** | `role_briefs/SEED_B2_ROLES_[team]_v1.md` (7 files) |
| B5 | **Relationship Matrix** | ○ Not started | Bilateral relationships for all country pairs. Based on protagonist research. Tensions AND alignments mapped for SIM playability. | `SEED_RELATIONSHIP_MATRIX.md` |
| B6 | **AI Country Profiles** | ◐ Concept test profiles | Full 4-block cognitive initialization for all AI-operated countries. Identity, personality, memory, goals/strategy. | `SEED_AI_COUNTRY_PROFILES.md` |

---

## C — GAME MECHANICS

Concept status: **strong** (4 domains, 30 actions, time structure, map). SEED finalizes mechanics and adds starting data.

| # | Item | Concept | SEED adds | Deliverable |
|---|------|---------|-----------|-------------|
| C1 | **Domains architecture** | ● Complete (military, economy, politics, tech) | Incorporate concept test fixes (stability formula, oil price, inflation, cost-to-sanctioner, debt service). Finalize all mechanic details. | C1 v3 (updated) |
| C2 | **Action system** | ● Complete (30 actions, auth chains) | Minor refinements | C2 v4 (updated) |
| C3 | **Time structure** | ● Complete (6-8 rounds, dramatic arc) | Finalize as 8 rounds based on concept test | C3 v2 (updated) |
| C4 | **Map & zones** | ● Concept + concept test (89 zones, adjacency) | Finalize zone structure, refine adjacency from test learnings | `SEED_C2_MAP_ZONES_v3.md` (refined) |
| C5 | **Public speaking & press** | ○ Not started | Speech protocol, Veritas mechanic | `C5_TTT_PUBLIC_SPEAKING_PRESS.md` |
| C6 | **Contracts & collective decisions** | ◐ Distributed | Consolidate into single reference | `C6_TTT_CONTRACTS_DECISIONS.md` |
| C7 | **Starting Data Pack** | — (concept test draft exists) | ALL numerical starting values for 21 countries: GDP, military, tech, stability, sanctions, tariffs, deployments. Refined from concept test. Validated by all domain experts. | `SEED_STARTING_DATA.json` + `.md` |

---

## D — WORLD MODEL ENGINES

Concept status: **architecture complete** (3 engines, 8-step processing). SEED specifies all formulas and processing logic.

| # | Item | Concept | SEED adds | Deliverable |
|---|------|---------|-----------|-------------|
| D0 | **Engine architecture** | ● Complete (three-pass: deterministic → AI ±30% → coherence) | No change — carries forward | E1 v2 (intact) |
| D1 | **Economic model** | — (concept test draft) | All formulas: GDP growth, sanctions, tariffs, oil price, inflation, debt service, financial markets, trade flows, budget cycle | `SEED_ENGINE_ECONOMIC.md` + code |
| D2 | **Political model** | — (concept test draft) | Stability (positive inertia), political support, propaganda, elections, coups | `SEED_ENGINE_POLITICAL.md` + code |
| D3 | **Military model** | — (concept test draft) | Combat (RISK+), amphibious, blockade, production, maintenance, covert ops, deployment | `SEED_ENGINE_MILITARY.md` + code |
| D4 | **Technology model** | — (concept test draft) | Nuclear track, AI track, R&D, breakthroughs, Formosa disruption, transfers | `SEED_ENGINE_TECHNOLOGY.md` + code |
| D5 | **Narrative engine** | — (concept test draft) | AI prompts for world/country briefings, structural clocks, risk flags | `SEED_ENGINE_NARRATIVE.md` + prompts |
| D6 | **Transaction engine** | — (architecture only) | Real-time bilateral transfers: validation, auth chains, irreversibility | `SEED_ENGINE_TRANSACTIONS.md` |
| D7 | **Live Action engine** | — (architecture only) | Real-time combat, arrests, covert ops: dice/probability, global alerts | `SEED_ENGINE_LIVE_ACTION.md` |

---

## E — AI SYSTEMS

Concept status: **architecture complete** (F1 participant module, F2 Navigator). SEED specifies character profiles and conversation/negotiation mechanics.

| # | Item | Concept | SEED adds | Deliverable |
|---|------|---------|-----------|-------------|
| E1 | **AI Participant Architecture** | ● Complete (4-block cognitive, perceive-think-act) | No change — carries forward | F1 v2 (intact) |
| E2 | **AI Conversation & Negotiation** | — (missing from concept test) | How AI participants negotiate: propose, counter, bluff, commit, stall. Prompt architecture for bilateral and multi-party. Essential — 90% of SIM is talking. | `SEED_AI_CONVERSATIONS.md` |
| E3 | **AI Navigator Architecture** | ● Complete (intro/mid/outro, 3 phases) | No change at SEED — carries forward. Detailed prompts in Detailed Design. | F2 v2 (intact) |
| E4 | **AI Navigator Prompt Specs** | — (new) | Per-phase prompt templates, knowledge base structure, reflection protocols, data extraction schemas | `SEED_AI_NAVIGATOR_PROMPTS.md` |

---

## F — DATA ARCHITECTURE

**New at SEED.** The product requires a defined data model that all engines, the web app, AI systems, and analytics read/write.

| # | Item | Concept | SEED adds | Deliverable |
|---|------|---------|-----------|-------------|
| F1 | **World State Schema** | — (implicit in engine) | Canonical data model for the complete world state: per-country state (economic, military, political, tech), bilateral relations, zone control, deployments, war status, chokepoints, org membership. Versioned per round. | `SEED_F1_DATA_SCHEMA_v1.md` |
| F2 | **Event Log Schema** | — (new) | Every SIM action logged: who, what, when, where, authorization, outcome. This is the behavioral data pipeline that feeds post-SIM analytics. The product's long-term value. | `SEED_DATA_EVENT_LOG.md` |
| F3 | **Real-Time Data Flows** | — (new) | How data moves between engines, participants, facilitator, public display. What's pushed vs. pulled. Latency requirements. Information asymmetry enforcement (who sees what). | `SEED_DATA_FLOWS.md` |
| F4 | **API Contracts** | — (new) | Interface definitions between: front-end ↔ back-end, engine ↔ database, AI module ↔ engine, facilitator ↔ system. Typed, versioned. | `SEED_API_CONTRACTS.md` |

---

## G — WEB APP SPECIFICATION

Concept status: **architecture complete** (15 modules, tech stack). SEED adds screen-level specs and data bindings.

| # | Item | Concept | SEED adds | Deliverable |
|---|------|---------|-----------|-------------|
| G1 | **App architecture** | ● Complete (3-layer, 15 modules) | No change — carries forward | G1 v2 (intact) |
| G2 | **Participant Interface Spec** | — (new at this detail) | Screen-by-screen: dashboard layout, action panels (per role type), map view, communication, budget form, deployment interface. Data bindings to F1 world state. | `SEED_APP_PARTICIPANT.md` |
| G3 | **Facilitator Dashboard Spec** | — (new at this detail) | Screen-by-screen: live control panel, AI monitoring, round management, moderator overrides, event injection, narrative review | `SEED_APP_FACILITATOR.md` |
| G4 | **Public Display Spec** | — (new at this detail) | What the room sees: map with live updates, round status, dramatic reveals, key metrics | `SEED_APP_PUBLIC_DISPLAY.md` |
| G5 | **Communication System Spec** | — (new at this detail) | In-app messaging, meeting requests, organization channels, private/public distinction, AI participant communication interface | `SEED_APP_COMMUNICATIONS.md` |

---

## H — VISUAL DESIGN & MAP

**New section at SEED.** Concept had no visual design work. SEED establishes the design language.

| # | Item | Concept | SEED adds | Deliverable |
|---|------|---------|-----------|-------------|
| H1 | **UX Style Guide** | — (new) | Color palette, typography, map aesthetics, component patterns, emotional register. Applies to: web app, presentations, printed materials, artefacts. Initial version — refined in Detailed Design into full standard. | `SEED_UX_STYLE.md` |
| H2 | **Map Visual Upgrade** | Schematic SVGs from concept test | Upgrade to styled cartographic maps. Fantasy cartography, fictional names, alliance colors, unit markers, chokepoint icons | Updated SVG files |
| H3 | **Artefact Templates** | — (new) | Standard formats for: role briefs, action cards, intelligence reports, moderator scripts, decision forms, country briefing sheets. Visual identity consistent with H1. | Templates (HTML/CSS) |
| H4 | **Presentation & Print Templates** | — (new) | Intro briefing deck, debrief deck, printed table materials, name badges. All in the design language. | Templates |

---

## I — TESTING ARCHITECTURE

**New section at SEED.** The reusable testing infrastructure.

| # | Item | Concept | SEED adds | Deliverable |
|---|------|---------|-----------|-------------|
| I1 | **Test Harness Design** | Concept test runner (basic) | Full test system using ACTUAL engine components, map, roles, starting data. Supports: generic runs, focused scenarios, mechanic stress tests, balance tests, regression. | `SEED_TEST_ARCHITECTURE.md` + `test_harness.py` |
| I2 | **Negotiation Emulation** | — (missing from concept test) | AI-to-AI conversation layer. Countries propose, counter, agree/reject. Captures the negotiation dynamics that are 90% of real SIM activity. | Integrated in test harness |
| I3 | **Generic Test Battery** | 8 runs from concept test | Fresh battery with refined components. 4-8 runs, 8 rounds each. | Test outputs + analysis |
| I4 | **Focused Test Suite** | — (new) | Targeted tests: aggressive actors, oil cartel balance, US internal tensions, Formosa crisis, Sarmatia endgame, economic model stress | Test configs + results |
| I5 | **Calibration & Iteration** | 2 iterations in concept test | Systematic: run → analyze → adjust → re-run. Until dynamics are credible across all focused scenarios. | Updated engine + data + reports |

---

## J — DELIVERY & OPERATIONS

Concept status: **complete** (I1 delivery ops, 15 sections). SEED refines with specific operational details.

| # | Item | Concept | SEED adds | Deliverable |
|---|------|---------|-----------|-------------|
| J1 | **Delivery operations** | ● Complete | Minor refinements based on design evolution. Carries forward. | I1 v2 (updated if needed) |

---

## Summary

| Section | Items | New at SEED | Carried from concept | Biggest effort |
|---------|:-----:|:-----------:|:-------------------:|---------------|
| 0 — Prerequisites | 4 | 2 | 2 carry-forward | Templates + relationship matrix |
| A — Scenario Foundation | 3 | 1 | 2 intact | World context narrative |
| B — Actors & Structure | 6 | 2 | 4 deepened | **Role seeds (40+) — with Marat** |
| C — Game Mechanics | 7 | 1 | 6 (some deepened) | Starting data pack |
| D — World Model Engines | 8 | 7 | 1 intact | **All engine formulas** |
| E — AI Systems | 4 | 2 | 2 intact | AI conversations/negotiation |
| F — Data Architecture | 4 | 4 | — | **World state schema, event log, API** |
| G — Web App Specification | 5 | 4 | 1 intact | Screen-level specs |
| H — Visual Design & Map | 4 | 4 | — | UX style guide |
| I — Testing Architecture | 5 | 4 | 1 evolved | **Test harness + focused tests** |
| J — Delivery & Operations | 1 | 0 | 1 intact | — |
| **TOTAL** | **51** | **31** | **20** | |

---

## Execution Approach

Three parallel tracks, iterative development within each, integration points between:

```
TRACK A — SIM Design (SIMON, CRAFT, Marat):
  0.2 Templates → B3 Countries → B4 Roles (role-by-role) → B5 Relationships
  → A3 World Context → C5 Press → C6 Contracts → C7 Starting Data

TRACK B — Engineering (ATLAS, NOVA, ARIA):
  D1-D7 Engine models → F1-F4 Data architecture → E2 AI Conversations
  → G2-G5 App specs → D6-D7 Transaction/Live Action engines

TRACK C — Visual & Testing (CANVAS, TESTER):
  H1 UX Style → H2 Map upgrade → H3-H4 Templates
  → I1 Test harness → I2 Negotiation → I3-I5 Testing

                    ↓ INTEGRATION ↓
              Wire all components together
                    ↓ TESTING ↓
              Generic → Focused → Calibrate
                    ↓ GATE ↓
              Marat + validators + VERA
```

**Marat hands-on:** B4 (every role), B3 (country review), C7 (starting data review), I4-I5 (test results)

---

## Changelog
- **v2.0 (2026-03-26):** Complete restructure. SEED = integrated product specification, not just "written play." Mirrors concept checklist structure (A-H) plus new sections: F (Data Architecture), H (Visual Design), I (Testing). 51 items total (31 new, 20 carried from concept). Incorporates Marat feedback on product scope.
- **v1.0 (2026-03-26):** Initial draft. 28 items, focused on SIM scenario seed files.
