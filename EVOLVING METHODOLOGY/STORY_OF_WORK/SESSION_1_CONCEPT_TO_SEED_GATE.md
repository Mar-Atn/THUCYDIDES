# Story of Work — Session 1: Concept to SEED Gate
## Thucydides Trap SIM | March 25-30, 2026
**Authors:** Marat Atn + MARCO (Claude Opus 4.6) + 14-agent AI team
**Purpose:** Knowledge preservation — how we built what we built

---

## Executive Summary

In 5 working days (March 25-30, 2026), one human product owner and a team of AI agents took a geopolitical simulation from approved Concept to a near-complete SEED design — 44 of 50 deliverables, 17,000+ lines of design documents, executable engine code validated through 4 test batteries (~80 simulated rounds), and a comprehensive web app specification.

The project: **The Thucydides Trap (TTT)** — an immersive leadership simulation modeling US-China power transition with 25-39 human participants, 10 AI-operated countries, 6-8 rounds, and 4 interconnected domains (military, economy, politics, technology).

---

## Timeline

### Day 1 (March 25): Foundation
- **Started with:** Concept gate just passed (14 concept documents, frozen)
- **Created:** CLAUDE.md v1 (operating rules), 14 agent definitions, project structure
- **Key decisions:** Stage-gate process, file naming convention, folder discipline rules
- **Delivered:** Agent team framework, knowledge base integration

### Day 2 (March 26): Country Seeds + Role Seeds
- **Created:** 16 country seed documents (every country in the SIM), 37 role seeds across 7 files
- **Process:** Marat provided detailed character sketches for key roles. AI agents fleshed out all 37 roles to a standard 9-section template.
- **Key decisions:** Role naming (Dealer, Helmsman, Pathfinder, Beacon, Furnace...), team structures, power distributions
- **Also:** SEED checklist v1, CSV data files (countries, roles, deployments, zones, relationships, sanctions, tariffs, organizations, memberships)

### Day 3 (March 27): Maps + Engine v1-v2
- **Created:** Global hex map (10×20 grid, 22 territories), Eastern Ereb theater map, interactive map editor (HTML)
- **Engine work:** World model engine v1 → v2 (three-pass architecture: deterministic → AI expert panel → coherence check)
- **Key crisis:** GDP formula produced unrealistically smooth curves. Redesigned with crisis escalation ladder (NORMAL→STRESSED→CRISIS→COLLAPSE) and momentum variable.
- **First test battery:** 8 concept-level tests revealed 4 critical engine bugs (Gulf Gate double-counting, inflation on absolute value, tech boost compounding, crisis multiplier dampening)
- **All bugs fixed same day.** Engine credibility: 6.5 → 7.9/10 in one iteration.

### Day 4 (March 28): Engine Calibration + Data Architecture
- **Engine v2.5-v2.8:** Oil price inertia, sanctions multiplier, expert panel (3 AI experts: KEYNES/CLAUSEWITZ/MACHIAVELLI), soft-variable constraint, trajectory awareness
- **Engine credibility reached 8.6/10** after 3 calibration iterations
- **Data architecture completed:** F2 (store facts, derive assessments), F3 (data flows), F4 (API contracts — 15 endpoints)
- **Methodology documented:** Engine Validation Methodology (4-step iterative process) added to EVOLVING METHODOLOGY

### Day 5 (March 29): Relationship Map + AI Specs + Templates
- **Morning:** Discovered checklist was undercounting — actual progress 62%, not 46%
- **Created:** C6 (Contracts), C7 (Time Structure), E2 (AI Conversations — based on KING SIM)
- **B3 Relationship Matrix:** Interactive HTML graph (37 roles, ~80 edges). Validated by MACHIAVELLI (political accuracy) and SIMON (playability). Research-grounded personal dynamics between leaders.
- **Named the AI assistant: ARGUS** (the hundred-eyed giant, replacing working name "Navigator")
- **E4 Argus Prompts:** 7-block prompt assembly, 3 phases, voice-first
- **A3 World Context:** ~1200-word opening briefing for participants
- **H3 + H4:** Artefact templates (5 types) and print templates (5 types)
- **Major naming audit:** Found role name mismatches between working names and canonical seeds. Established B2 role seeds as single source of truth. Fixed all files.
- **Consistency review:** VERA found 18 issues (1 critical, 6 high). All fixed same day.
- **End of day:** 38/50 (76%)

### Day 6 (March 30): Web App Spec + Action Review + Gate
- **Web App Spec:** Marat redesigned the participant interface structure (fixed reference / personal / country / world / actions / communications). Key insight: human-to-human communication is FACE TO FACE — app only handles AI meetings.
- **ACTION-BY-ACTION REVIEW (the biggest single session):** Marat and MARCO reviewed all 31 SIM actions one by one. Each action explained in plain participant language. Marat confirmed or adjusted. Major revisions:
  - Ground attack: simplified to integer-only dice modifiers
  - Blockade: ground-forces-only (not naval superiority)
  - Nuclear: 5-tier system with 10-minute real-time authorization clock
  - Intelligence: renamed from espionage, per-individual pools, always returns answer
  - Sanctions: S-curve coalition model
  - New mechanics: Court (AI judge), Impeachment, Protest (auto + stimulated)
- **3 parallel agents** updated G spec, D8 formulas, and engine code simultaneously
- **Gate tests:** Independent tester ran 11 tests (~80 rounds). Verdict: CONDITIONAL PASS. 4 blockers + 10 high + 7 medium issues found.
- **All blockers fixed:** Naval combat added, Persia nuclear fixed, Court AI logic defined, intelligence pools implemented
- **All HIGH items fixed:** Combat stacking softened, sanctions imposer cost increased, election crisis modifiers added, semiconductor capped
- **SEED GATE: PASSED**
- **Detailed Design checklist created**, development approach documented

---

## Key Design Decisions (chronological)

| Day | Decision | Why | Impact |
|-----|----------|-----|--------|
| 1 | 14-agent team with MARCO orchestrator | Complex project needs specialist roles | Enabled parallel work streams |
| 2 | Fictional country names (Columbia, Cathay, Sarmatia...) | Corporate audiences, political sensitivity | All documents use SIM names |
| 2 | 37 core + 3 expansion roles | Coverage + scalability | 25-39 participants supported |
| 3 | Hex grid map (not zone-based) | Visual clarity, modular theaters | Global 10×20 + theater 10×10 |
| 3 | Three-pass engine (deterministic → AI → coherence) | Realism + controllability | Expert panel catches qualitative dynamics |
| 3 | Crisis escalation ladder | GDP curves were too smooth | Tipping points create drama |
| 4 | "Store Facts, Derive Assessments" | 18 variables were ad-hoc | Clean data architecture |
| 4 | Soft-variable constraint for AI panel | Experts were adjusting hard variables | Only growth rates, stability, support adjustable |
| 5 | AI assistant named "Argus" | "Navigator" conflicted with role names | Memorable, mythological, fits function |
| 5 | B2 role seeds = single source of truth for names | Names were drifting across documents | One source, all others derive |
| 6 | Humans talk face to face, app only for AI meetings | Immersive SIM = physical interaction | Massively simplified communication system |
| 6 | Blockade = ground forces on shore | Naval superiority alone unrealistic | Gulf Gate requires ground invasion to break |
| 6 | Sanctions S-curve: coalition coverage → effectiveness | Western allies alone = modest, add swing states = devastating | Creates the diplomatic game |
| 6 | Nuclear 10-minute clock | Real-time crisis simulation within the SIM | Most intense gameplay moment |
| 6 | Die Hard + air support don't stack | Formosa needs 15-25% attack success | Max positional bonus = +1 |
| 6 | Mobilization = finite depletable pool | Repeated conscription unrealistic | One-shot strategic reserve |

---

## Methodology Innovations

### 1. Action-by-Action Review
Instead of reviewing the game design as a document, MARCO explained each of the 31 actions to Marat as if he were a participant. Plain language, worked examples, real numbers. Marat confirmed or adjusted each one. Took ~4 hours but eliminated ambiguity across the entire action system.

**Lesson:** Complex designs become clear when you explain them as user experiences, not as specifications.

### 2. Parallel Agent Validation
MACHIAVELLI (political), CLAUSEWITZ (military), and SIMON (SIM design) reviewed the relationship map simultaneously. Each caught different issues. Combined: a much more thorough review than any one expert could provide.

**Lesson:** Multi-perspective validation is worth the compute cost.

### 3. Three-Layer Testing
- Layer 1: Data traceability (CSV → engine → screen)
- Layer 2: Role walkthroughs (simulate a round for specific roles)
- Layer 3: Assembly readiness (can a developer code from this?)

All three ran in parallel, testing different dimensions of the same design.

**Lesson:** Different test types catch different bugs. Run them all.

### 4. Engine Validation Methodology
Expert dependency mapping → focused test scenarios → run & score → fix & iterate. Brought engine credibility from 6.5/10 to 8.6/10 in 2 iterations.

**Lesson:** Set expected ranges BEFORE looking at engine output. The engine must match reality, not the other way around.

### 5. Consistency-First Development
CLAUDE.md enforces: 3-hour consistency checks, sync alerts when phases drift, cardinal rule (no change at lower level without updating all levels above), file freeze mechanism.

**Lesson:** Consistency enforcement must be MANDATORY and AUTOMATED, not voluntary. Without it, a 50-document design WILL drift.

---

## Statistics

| Metric | Value |
|--------|-------|
| Working days | 5 (March 25-30) |
| SEED deliverables | 44 of 50 (88%) |
| Documents created | ~30 markdown files |
| Engine code | ~5,000 lines Python |
| CSV data | 10 files, ~1,500 data points |
| HTML visualizations | 5 files (map editor, style demo, artefacts, print, relationship graph) |
| Test batteries | 4 (concept tests + 3 SEED batteries) |
| Simulated rounds | ~80 |
| Actions reviewed | 31 (one by one with Marat) |
| Consistency reviews | 3 (VERA automated) |
| Change Management entries | 5 (CM-001 through CM-005) |
| Git commits | ~15 |
| Total lines added | ~20,000+ |
| Agent team | 14 defined, 8 actively used |

---

## What Worked

1. **Stage-gate discipline** — never skipping ahead, always checking consistency
2. **Agent specialization** — ATLAS for engines, VERA for consistency, TESTER for stress-testing
3. **Marat's design instincts** — "humans talk face to face," "keep it simple," "sanctions need coalition"
4. **Iterative calibration** — engine improved from 6.5 to 8.75/10 through systematic testing
5. **CLAUDE.md as living constitution** — everyone knows the rules, rules evolve with the project

## What Was Hard

1. **Name consistency** — role names evolved during conversation and drifted across documents
2. **Checklist accuracy** — manual tracking fell behind; had to re-audit multiple times
3. **Context window management** — conversation compressed multiple times, losing details
4. **Formula complexity** — sanctions, GDP, stability all interact; tuning one affects others
5. **Balancing realism vs. playability** — every mechanic is a trade-off

## What We'd Do Differently

1. **Establish canonical names FIRST** before any document references them
2. **Automate checklist updates** — manual tracking is error-prone
3. **Test earlier** — concept tests were invaluable; should have started engine testing on Day 2
4. **Save context more aggressively** — memory files help but can't replace full conversation context

---

*This document captures the first development session. Future sessions will be documented in the same folder, building a complete development story for the MetaGames knowledge base.*
