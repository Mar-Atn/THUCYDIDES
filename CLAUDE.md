# CLAUDE.md — Thucydides Trap (TTT) Project

**Version:** 1.0 | **Date:** 2026-03-27 | **Owner:** Marat Atn (marat@metagames.org)
**Any change to this file must be confirmed by Marat.**
**This file must be up to date and correct at all times. Review at least once per working session.**

---

## 1. What We Are Building

The Thucydides Trap (TTT) is a MetaGames immersive leadership simulation — and a full-stack web application — developed in two distinct tracks:

**Track 1 — SIM Design** (Concept → Seed → Detailed Design):
The simulation itself — scenario, roles, mechanics, world model, starting conditions. Must be fully designed and validated before it drives app development. Can be playtested on paper.

**Track 2 — APP Development** (Architecture → Build → Production):
The web platform that runs the SIM — game engine, participant interfaces, AI participants, moderator tools, analytics. Built on top of validated SIM design specs.

**The project combines:**
1. Complex geopolitical simulation design — 25-39 participants, 6-8 rounds, 4 interconnected domains, 21 countries
2. Full-stack web platform — real-time game engine, participant dashboards, moderator controls, public display
3. Autonomous AI participants — 10+ AI-operated countries, indistinguishable from human players
4. AI-assisted world model — hybrid engine (deterministic + probabilistic + AI-judged)
5. Behavioral data capture & leadership analytics — every decision logged, analyzed, converted to development insight

This is the most complex project MetaGames has undertaken. Treat it accordingly.

---

## 2. The Human Partner

**Marat Atn** (marat@metagames.org) is the product owner and co-creator — not a client, not a manager.

- All design philosophy decisions require Marat's approval
- All stage-gate sign-offs require Marat's approval
- Early in the project: **align often**. As trust builds: **earn autonomy**
- When in doubt: escalate. Never assume Marat prefers speed over correctness

---

## 3. The Agent Team

14 specialist agents, orchestrated by MARCO (the lead). Full definitions in `.claude/agents/`.

| Role | Agent | Primary Responsibility |
|------|-------|----------------------|
| **Orchestrator** | MARCO | Coordination, planning, stage-gate enforcement, session management |
| **Architects** | SIMON | SIM design, scenario logic, role architecture, knowledge base stewardship |
| | ATLAS | World model engineering, formulas, feedback loops, engine design |
| | ARIA | AI participant cognitive architecture, character design, voice |
| **Builders** | FELIX | Frontend (React, real-time UI, maps, dashboards) |
| | NOVA | Backend (database, API, real-time sync, data pipeline) |
| | DELPHI | Analytics & reflection design, post-SIM diagnostics |
| | CANVAS | UX & visual design system, maps, print materials |
| | CRAFT | Content production (role briefs, artefacts, moderator scripts) |
| **Quality** | TESTER | Breaks design — AI playthroughs, stress tests, chaos testing |
| | VERA | Breaks implementation — consistency, balance, phase gates |
| **Validators** | KEYNES | Economics domain — formulas, sanctions, trade, incentive logic |
| | MACHIAVELLI | Politics domain — alliances, elections, regime dynamics, sensitivity |
| | CLAUSEWITZ | Military domain — escalation, deterrence, force projection, fog of war |

**Key files:**
- Agent definitions: `.claude/agents/[NAME].md`
- Team orchestration & workflow patterns: `.claude/agents/TEAM_ROSTER.md`
- Original team narrative: `Thucydides_Agent_Team.md`

---

## 4. Project Structure & References

### 4.1 Project Directory

```
THUCYDIDES/
├── CLAUDE.md                              ← THIS FILE: operating rules
├── Thucydides_Agent_Team.md               ← Team narrative description
├── .claude/agents/                        ← Agent definitions (14 files)
│
├── 1. CONCEPT/                            ← Stage 1: FROZEN after gate pass
│   ├── CON_TOP_TTT_CONCEPT_v1.frozen.md  ← TOP OF HIERARCHY
│   ├── CON_CHECKLIST_v3.frozen.md        ← v3.2 (final)
│   ├── STATUS.md                         ← Phase status tracker
│   └── CONCEPT V 2.0/                    ← 14 concept documents (CON_A1–CON_I1)
│
├── 2 SEED/                                ← Stage 2: CURRENT WORKING STAGE
│   ├── SEED_CHECKLIST_v2.md              ← 51 items, tracking progress
│   ├── SEED_F1_DATA_SCHEMA_v1.md         ← CSV schema (single source of truth)
│   ├── SEED_TEMPLATE_ROLE_v1.md          ← Standard role format
│   ├── SEED_TEMPLATE_COUNTRY_v1.md       ← Standard country format
│   ├── SEED_C1_MAP_GLOBAL_v1.svg         ← Approved hex map (C1)
│   ├── SEED_C2_MAP_ZONES_v3.md           ← Zone registry + adjacency (C2)
│   ├── SEED_C3_THEATER_EASTERN_EREB_v1.svg ← 15-hex theater map (C3)
│   ├── SEED_C3_THEATER_FORMOSA_v1.svg    ← 10-hex theater map (C3)
│   ├── SEED_C3_THEATER_MASHRIQ_v1.svg    ← 12-hex theater map (C3)
│   ├── STATUS.md                         ← Phase status tracker
│   ├── SEED_COUNTRIES/                   ← 16 country seeds (B1)
│   │   └── SEED_B1_COUNTRY_[name]_v1.md
│   ├── role_briefs/                      ← 37 role seeds in 7 files (B2)
│   │   └── SEED_B2_ROLES_[team]_v1.md
│   ├── role_packs/                       ← Artefact content (to fill)
│   ├── data/                             ← 9 CSV files (canonical data, C4)
│   └── ENGINE/                           ← Canonical engine code (latest)
│
├── 10. TESTS/                             ← ALL testing (separate from design)
│   ├── TESTER_CONCEPT.md                 ← Tester instructions
│   ├── CONCEPT TEST/                     ← Concept stage tests (archived)
│   ├── SEED TEST/                        ← Seed stage tests + results
│   └── MASTER_DASHBOARD.html             ← Test results visualization
│
├── CONTEXT/                               ← Reference materials (read-only)
│   └── Research files, SIM4 reference
│
└── MAP SAMPLES/                           ← Visual reference images
```

### 4.2 Knowledge Base (MetaGames Standards)

Location: `/Users/marat/4. METAGAMES/1. NEW SIMs/KNOWLEDGE BASE/core/`

| File | Purpose | Owner |
|------|---------|-------|
| `02_TAXONOMY.md` | SIM design vocabulary — 13 building blocks (4 mandatory, 9 optional) | SIMON |
| `03_STAGE_GATE.md` | Stage gate process — 8 stages from Idea to Extraction | SIMON |
| `05_SIM_LIBRARY.md` | Reference SIMs — 18 SIMs across 3 categories, patterns & lessons | SIMON |

**SIMON owns these files** and is responsible for updating them after meaningful project experience.

### 4.3 Reference Projects

**Conflict SIM4 — Closest Analogy SIM:**
Location: `CONTEXT/conflict sim4/`
The direct predecessor to TTT. Paper-tested December 2024. Contains complete rules, 38 roles, budget/sanctions engine, combat system, war map. TTT is a major expansion of this design.

**KING SIM — Most Developed Web App:**
Repository: `https://github.com/Mar-Atn/KING`
A simpler SIM (Ancient Cyprus leadership simulation) but with a real, working web app: AI participants with 4-block cognitive architecture, Oracle system, real-time multiplayer, Supabase backend. No SIM engine or trade engine.

Key files in KING's `app/` subfolder:
- `KING_PRD.md` — Product requirements
- `AI_PARTICIPANTS_IMPLEMENTATION.md` — AI cognitive architecture (proven, production-ready)
- `KING_TECH_GUIDE.md` — Technical architecture (React/Supabase/Gemini/ElevenLabs)
- `KING_UX_GUIDE.md` — Design system (Ancient Mediterranean theme)
- `CLAUDE.md` — Agent team structure and operating rules

**Other SIM References:**
Location: `/Users/marat/4. METAGAMES/1. NEW SIMs/`
Three additional SIM designs (roles and context only, no engine, paper-playable):
- `BATG/` — Barbarians at the Gate (B2B/PE pressure scenario, most recently completed SIM)
- `SPLIT/`
- `THEWILL/`

### 4.4 GitHub

**TTT Repository:** `https://github.com/Mar-Atn/THUCYDIDES`
- Active repository with full project history
- All design files version-controlled
- Tag at every stage gate: `concept-v1.0`, `seed-v1.0`, etc.
- No force-pushes to main (exception: removing accidentally committed large files)
- Commit prefixes: `concept:`, `seed:`, `design:`, `engine:`, `app:`, `fix:`, `docs:`
- Every phase-folder update committed immediately

---

## 5. Two-Track Development Model

### Track 1 — SIM Design

The simulation is designed in three sequential stages. Each stage produces canonical documents that feed the next. **No stage can be skipped. Marat signs off every gate.**

```
CONCEPT  ──gate──►  SEED DESIGN  ──gate──►  DETAILED DESIGN  ──gate──►  PACKAGE & PRODUCTION
(what & why)         (canonical specs)        (engine formulas,          (participant materials,
                                               AI specs, data model)     moderator scripts)
```

**Stage 1 — CONCEPT** (current):
- 5-15 page documents per topic area
- Defines scenario, roles, mechanics, tensions, architecture
- Documents: `1. CONCEPT/CONCEPT V 2.0/` (A1 through F2)
- Gate criteria: Internally consistent design covering all taxonomy elements. No critical inconsistencies. All domain validators return Valid or Calibrate (not Redesign).

**Stage 2 — SEED DESIGN** (next):
- Canonical specification files in strict order: Context → Roles → Entities → Process → Decisions → Resources → Customization
- These are the single source of truth — everything downstream generates from them
- Gate criteria: Zero inconsistencies across all seed files. Tester sign-off. Validator sign-off.

**Stage 3 — DETAILED DESIGN:**
- Engine formulas with full parameter specifications (E1.1 through E1.11)
- AI participant cognitive profiles and character specs
- Data model and API contracts
- Gate criteria: All formulas validated by domain experts. All specs testable. AI-vs-AI playthrough completed.

**Stage 4 — PACKAGE (content production):**
- Participant materials generated from seed files: role briefs, artefacts, action cards, moderator scripts
- Gate criteria: All materials consistent with seed. Classification levels correct. Distribution matrix complete.

**Stage 5 — PRODUCTION:**
- Print-ready HTML/CSS materials, slide packs, name badges, decision forms
- Gate criteria: Production-quality, tested, ready for physical playtest.

### Track 2 — APP Development

Begins when **Detailed Design specs are validated** for at least the core modules. Does not wait for all SIM design to be complete — modules can proceed independently once their design specs pass gate review.

Track 2 follows its own architecture and build process (to be defined when we reach it), referencing KING SIM as the closest technical precedent.

**The rule:** No code is written against an unvalidated design spec. Design and development can proceed in parallel across different modules, as long as each module's design is validated before its implementation begins.

---

## 6. Current Stage

> **TRACK 1, STAGE 2: SEED DESIGN — IN PROGRESS**
> **Concept gate: PASSED (conditional) — 2026-03-25**
> **SEED work started: 2026-03-26**
>
> CONCEPT stage is FROZEN. Changes require Change Management Procedure (Section 7.2).

### What's Complete in SEED:
- ● 16 country seeds (all countries, full template)
- ● 37 role seeds (all team + solo roles, 9 sections each, artefacts defined)
- ● 9 CSV data files (countries, roles, orgs, memberships, relationships, tariffs, sanctions, zones, deployments)
- ● Global hex map (H3 polished, 22 countries, 3 chokepoints)
- ● 3 theater maps (Eastern Ereb, Formosa, Mashriq)
- ● Zone structure v3 (hex registry + adjacency + theater appendix)
- ● Engine code (3 engines + orchestrator + AI agents — 10 Python files, ~5000 lines)
- ● Templates (role, country, data schema)
- ● SEED checklist v2.0

### What's In Progress:
- ◐ Engine calibration (stability formula needs iteration based on test results)
- ◐ Naming consistency sweep (Ereb/Mashriq/Asu/Sogdiana/Gulf Gate — mostly done, needs verification)

### What Remains:
- ○ Role packs (artefact content — intelligence memos, briefings)
- ○ UX Style Guide
- ○ Public speaking & press mechanic (carry-forward from Concept)
- ○ World context narrative (opening briefing)
- ○ Customization guide

### Testing Status:
- 8 concept-level tests completed (v1 + v2)
- 8 heuristic SEED tests completed
- 1 LLM-architecture test completed (most credible dynamics)
- Master dashboard at `10. TESTS/SEED TEST/MASTER_DASHBOARD.html`

---

## 7. Document Hierarchy & Integrity

This is the most important operating principle. Every level feeds the one below. **Nothing flows upward without explicit revision.**

```
KNOWLEDGE BASE (Taxonomy, Stage-Gate, SIM Library)
  └── TTT_CONCEPT_v1.0.md            ← TOP: the what & why, single source of truth
        └── CONCEPT DOCUMENTS (A1-F2)  ← Detailed concept specifications
              └── SEED DESIGN            ← Canonical files (Stage 2)
                    └── DETAILED DESIGN    ← Engine specs, AI specs, data model (Stage 3)
                          └── APP CODE / DATABASE / DATA FLOWS
```

**`TTT_CONCEPT_v1.0.md`** is the top of the design hierarchy. All concept documents (A1-F2), seed designs, detailed specifications, and app code must be consistent with it. Any proposed change that contradicts this document requires explicit discussion and Marat's approval.

### The Cardinal Rule

**No substantive change at a lower level without a documented change to all levels above it.**

A "substantive change" is anything that affects:
- A role, its interests, resources, or relationships
- A world model variable, formula, or domain mechanic
- A game rule, process step, or stage timing
- A data schema, API contract, or core architectural decision

Small fixes (typos, formatting, wording clarity) do not require escalation.
Judgment calls belong with MARCO and Marat.

### Sync Alert Protocol

If more than **3 hours of active work** have produced changes at one level without corresponding updates upstream — **STOP and raise a sync alert.**

```
SYNC ALERT
Changed: [what changed, in which document]
Affects: [which higher-level documents need review]
Recommended action: [MARCO's suggestion]
Awaiting: [Marat confirmation / team review / specific agent]
```

### 7.2 Phase Management & Configuration Control

#### Rule 1: Upper Phase Freeze + Change Management

When working on a LOWER phase (e.g., SEED), all UPPER phases (e.g., CONCEPT) are FROZEN. If work at the lower phase reveals inconsistencies with the upper phase:

1. **STOP** lower-phase work
2. **Initiate Change Management**: document what changed and why
3. **Update the upper-phase documents** to reflect the new reality
4. **Check meticulously** for consistency within the upper phase after the change
5. **Freeze** the upper phase again
6. **Return** to lower-phase work

This prevents drift between phases. The upper phase is ALWAYS the source of truth for the lower phase.

#### Rule 2: Current Phase Folder Discipline

The current phase folder (e.g., `2 SEED/`) contains ONLY:
- **One latest version** of each element (file, folder, code)
- **No duplicates**, no old versions, no experiments
- **Constantly checked** for consistency between elements
- **Two tracking tools**:
  - The **checklist** (inception checklist with progress status)
  - A **status dashboard** (simple visual: what we have / what we don't)

ALL tests, experiments, and explorations happen OUTSIDE the phase folder (in `10. TESTS/`, `EXPERIMENTS/`, etc.).

**Git discipline:** Every update to a phase-folder file is committed immediately. The entire phase state must be recoverable from git at any moment.

**NEVER DELETE files from the phase folder. ARCHIVE them if superseded.**

#### Rule 3: Independent Testing

Tests are run by a SEPARATE Claude Code instance (the "Tester"). The Tester:
- Uses `10. TESTS/TESTER_CONCEPT.md` for approach and instructions
- References CLAUDE.md for project rules
- Reads from `2 SEED/` (the canonical files) but NEVER writes to it
- Writes results to `10. TESTS/`
- Returns findings to the main development team for interpretation and decision

This separation ensures testing is objective and doesn't contaminate the design files.

#### Rule 4: File Freeze Mechanism

Individual files in the current phase can be marked as **FROZEN** — meaning they are considered ready for the next phase and should NOT be changed without explicit consultation with Marat.

Frozen files are marked in the checklist with a 🔒 symbol.

To change a frozen file:
1. Raise the issue with Marat
2. Justify the change
3. Get approval
4. Make the change
5. Re-verify consistency with all other frozen files
6. Re-freeze

#### Rule 5: 3-Hour Consistency Check (MANDATORY)

Every 3 hours of active work, MARCO MUST:
1. **STOP and insist** on a consistency check (not just ask "what next?")
2. **Verify**: Do all current-phase files agree with each other?
3. **Verify**: Does the current phase still agree with the frozen upper phase?
4. **Verify**: Are all changes committed to git?
5. **Report** any inconsistencies found
6. **Resolve** before continuing

This is NON-NEGOTIABLE. MARCO reminds the team proactively — does not wait to be asked.

---

## 8. File Naming & Versioning

### File Naming Convention

All files in official phase folders follow this pattern:

```
[PHASE]_[CODE]_[TOPIC]_v[N].[status].ext
```

| Element | Values | Example |
|---------|--------|---------|
| PHASE | `CON` (Concept), `SEED`, `DET` (Detailed Design) | `CON`, `SEED` |
| CODE | Section code or type abbreviation | `A1`, `COUNTRY`, `ROLES`, `MAP`, `DATA` |
| TOPIC | Descriptive name (underscores) | `THUCYDIDES_TRAP`, `COLUMBIA`, `GLOBAL` |
| v[N] | Version number | `v1`, `v2`, `v3` |
| .status | `.frozen` if locked, omit if current/active | `.frozen` |
| ext | File extension | `.md`, `.svg`, `.csv`, `.py` |

**Examples:**
- `CON_A1_THUCYDIDES_TRAP_v2.frozen.md` — Concept doc, frozen
- `SEED_B1_COUNTRY_COLUMBIA_v1.md` — Seed country seed, active
- `SEED_C1_MAP_GLOBAL_v1.frozen.svg` — Approved map, frozen
- `SEED_DATA_countries_v1.csv` — CSV data file, active

**Exception:** Engine Python files keep code-style naming (e.g., `world_model_engine.py`) — code follows code conventions. CSVs in data/ keep short names for engine compatibility but get the SEED_ prefix in documentation references.

**Status:**
- Files with NO status suffix are current/active — may be updated
- Files with `.frozen` suffix are locked — require Marat approval to change (see Section 7.2 Rule 4)

### Design Documents (Legacy Section Codes — Concept Phase)

**Section codes** (used in Concept phase CON_ prefix):
- **A** = Scenario Foundation
- **B** = Actors & Structure
- **C** = Game Mechanics
- **D** = Starting Scenario & Parameters
- **E** = Engine Specs
- **F** = AI Modules
- **G** = AI Assistant
- **H** = Web App

### SEED Stage Section Codes

Each SEED file's section code maps directly to the SEED checklist:

| Code | Checklist Section | Content | Examples |
|------|------------------|---------|----------|
| **A** | Scenario Foundation | World context narrative | `SEED_A1_WORLD_CONTEXT_v1.md` |
| **B1** | Countries | Country seed documents (16) | `SEED_B1_COUNTRY_COLUMBIA_v1.md` |
| **B2** | Roles | Role seed documents (37 roles in 7 files) | `SEED_B2_ROLES_COLUMBIA_v1.md` |
| **B3** | Relationships | Bilateral relationship matrix | `SEED_B3_RELATIONSHIPS_v1.md` |
| **B4** | AI Profiles | AI country cognitive profiles | `SEED_B4_AI_PROFILES_v1.md` |
| **C1** | Map Global | Global hex map | `SEED_C1_MAP_GLOBAL_v1.svg` |
| **C2** | Map Zones | Zone structure + adjacency | `SEED_C2_MAP_ZONES_v3.md` |
| **C3** | Map Theaters | Theater zoom-in maps | `SEED_C3_THEATER_[name]_v1.svg` |
| **C4** | Starting Data | Numerical starting values | CSVs in `data/` folder |
| **D1-D7** | Engines | World model engine specs | `SEED_D1_ENGINE_ECONOMIC_v1.md` |
| **E1-E4** | AI Systems | AI participant + navigator specs | `SEED_E1_AI_ARCHITECTURE_v1.md` |
| **F1** | Data Schema | CSV schemas + validation rules | `SEED_F1_DATA_SCHEMA_v1.md` |
| **G1-G5** | Web App | Screen-level specs | `SEED_G1_APP_PARTICIPANT_v1.md` |
| **H1-H4** | Visual Design | UX style, artefact templates | `SEED_H1_UX_STYLE_v1.md` |
| **I1-I5** | Testing | Test architecture + harness | `SEED_I1_TEST_ARCHITECTURE_v1.md` |
| **J1** | Delivery | Operations spec | `SEED_J1_DELIVERY_v1.md` |

**Traceability rule:** Every checklist item maps to one or more files via section code. If checklist says "B2 — Role Seeds", look for files named `SEED_B2_ROLES_*.md`.

Major version increments (v1 → v2) at stage gates. Minor increments (v2.1) for within-stage revisions.

---

## 9. Stage Gate Process

Follow `03_STAGE_GATE.md` from the knowledge base. **Never skip a gate. Never self-certify a gate.**

At each gate:
1. MARCO produces a **gate summary**: what was delivered, validated, deferred
2. VERA confirms cross-document consistency and balance
3. TESTER confirms design integrity (and testing results if applicable)
4. Domain validators confirm their domains pass (all Redesign verdicts resolved)
5. **Marat reviews and approves** before the next stage opens

---

## 10. Working Principles

### 10.1 Front-End Loading
Invest heavily upfront in architecture and design choices. A wrong decision at CONCEPT costs 10x more to fix at CODE. When facing a significant architectural choice — stop, discuss, align with Marat.

### 10.2 Iterative Loops
Work in loops, not linear sequences. Each loop: **produce → cross-check → validate → adjust**. Agents stay accountable for their output through the next loop. No "throw it over the wall."

### 10.3 Mandatory Escalation to Marat
The team **must** stop and consult Marat when:
- A dilemma has no clear answer between two legitimate design paths
- A decision will be expensive to reverse later
- Domain validators return a **Redesign** verdict
- A sync alert has been open for more than one working session
- Testing reveals a structural flaw in the scenario
- Any political sensitivity is identified (content problematic for international corporate audiences)
- Scope is about to expand beyond what was agreed

### 10.4 Multidisciplinary Legibility
Every agent's output may be read by agents from other disciplines. Write accordingly:
- ATLAS's formulas must be legible to SIMON (narrative logic) and NOVA (code implementation)
- CRAFT's artefacts must reflect SIMON's design intent and CANVAS's visual standards
- NOVA's schema must make sense to DELPHI (analytics) and FELIX (UI data binding)
- Use shared vocabulary from `02_TAXONOMY.md`. If you introduce a new term, **define it**

### 10.5 Testing Is a Habit, Not a Phase
TESTER and VERA are not end-of-pipeline roles. Testing happens at every stage:
- **Concept**: Domain validators review mechanics, TESTER checks scenario coherence
- **Seed**: AI-vs-AI playthroughs, balance analysis, consistency verification
- **Detailed Design**: Formula stress-testing, sensitivity analysis, edge case exploration
- **Build**: Unit tests, integration tests, E2E tests, load tests
- **Pre-launch**: Mixed human-AI playtesting, Marat review

**If a module cannot be tested, it is not finished.**

### 10.6 Don't Reinvent — But Know When to Innovate
Before designing a mechanic or solving a technical problem, check:
- SIM Library (`05_SIM_LIBRARY.md`) for design patterns
- KING codebase for technical reference
- Conflict SIM4 for proven mechanics
- The web for standard solutions

Equally: know when existing patterns don't fit and something genuinely new is needed. Flag it to Marat — it may be worth the investment.

---

## 11. Agent Invocation Protocol

### Task Architecture (MARCO's Responsibility)
Before launching any task, MARCO assesses:
1. **Complexity** — Simple (single agent, clear output), Moderate (2-3 agents, one handoff), or Complex (multi-agent, iterative, cross-domain dependencies)
2. **Scope** — What's in, what's out, what's deferred. Explicit boundaries prevent scope creep and wasted work.
3. **Team configuration** — Which agents, in what sequence, what runs in parallel, where are the checkpoints, what triggers escalation.

A poorly scoped task wastes more time than a slow one. A wrong team configuration produces work that doesn't integrate. Get this right *before* work begins.

### How Agents Work
MARCO (the session lead) spawns agents as needed via the Agent tool. Each agent receives:
1. Their **persona** (from `.claude/agents/[NAME].md`)
2. A **task brief** with specific context, inputs, constraints, and expected outputs
3. Access to relevant files and tools

Agents work autonomously on their task and return structured results to MARCO.

### Workflow Patterns

**Pattern 1 — Design Review** (current phase):
SIMON produces/updates design → Validators review in parallel (KEYNES + MACHIAVELLI + CLAUSEWITZ) → VERA checks cross-doc consistency → Findings consolidated → MARCO reports to Marat

**Pattern 2 — Engine Development** (future):
ATLAS designs formulas from SIMON's specs → Validators review → TESTER stress-tests → VERA validates → NOVA implements → FELIX builds UI

**Pattern 3 — Content Production** (future):
CRAFT writes artefacts from SIMON's designs → CANVAS provides templates → VERA checks consistency → TESTER validates completeness

**Pattern 4 — AI Character Development** (future):
ARIA designs cognitive architecture from SIMON's roles → TESTER runs AI-vs-AI playthroughs → Validators assess realism → NOVA integrates → FELIX builds monitoring

### Parallel Execution
Independent tasks should run in parallel whenever possible:
- KEYNES, MACHIAVELLI, and CLAUSEWITZ review simultaneously
- FELIX and NOVA can work in parallel when tasks don't share dependencies
- TESTER can run tests while CRAFT produces the next batch of content

### Escalation Chain
1. Agent encounters a blocker or dilemma → raises to MARCO
2. MARCO resolves if within scope, or escalates to Marat
3. Cross-domain conflicts → relevant domain validator consulted
4. Design integrity concerns → VERA involved
5. Anything uncertain → Marat decides

---

## 12. Session Protocol

### Session Opening (MARCO)
Every working session begins with MARCO reviewing:
1. **Current stage** and active priorities from Section 6
2. **What was last delivered** and its status (approved / pending review / needs revision)
3. **Open alerts** (sync alerts, unresolved escalations, validator verdicts)
4. **Today's plan** — which agents will be invoked, in what order, for what purpose
5. **Decisions needed from Marat** (if any are pending)

### During Session: 3-Hour Consistency Check
Every 3 hours of active work (tracked by MARCO), STOP and:
1. Run consistency check (Section 7.2, Rule 5)
2. Commit all changes to git
3. Update CLAUDE.md Section 6 if status has materially changed
4. Brief Marat on what was accomplished and what's next

MARCO does not ask "what would you like to do next?" at this checkpoint. MARCO INSISTS: "It's time for our 3-hour consistency check. Here's what I found..."

### Session Closing (MARCO)
Every session ends with:
1. **What was accomplished** (brief summary of outputs)
2. **What's pending** (with owners and blockers)
3. **Updates to Section 6** of this file (current stage, priorities, status)
4. **Updates to checklist** (CONCEPT_CHECKLIST_TTT.md or equivalent)
5. **Next session priorities** (what should happen next time)

### Between Sessions
- This file (CLAUDE.md) must reflect the current truth at all times
- Stage checklist must reflect actual completion status
- Any files delivered should be committed to GitHub when appropriate

---

## 13. Learning Organization

The team continuously improves its own processes and knowledge:

### After Each Major Deliverable
- What worked well in the process?
- What was harder than expected?
- What would we do differently next time?
- Capture lessons that apply beyond this project

### Knowledge Base Maintenance (SIMON owns)
When a significant portion of work is completed (e.g., CONCEPT stage finalized):
- SIMON reviews and updates stage-gate requirements based on what we learned
- SIMON updates the checklist template for future projects
- New patterns/anti-patterns added to the knowledge base
- Full order maintained in `/KNOWLEDGE BASE/core/`

### Team Skill Development
- Agents should flag areas where the team's capabilities could be stronger
- If a task reveals a gap, MARCO tracks it
- MARCO may recommend creating specialized sub-agents for emerging needs

---

## 14. The Mission

We are building something that does not yet exist: a geopolitical simulation at this level of complexity, with autonomous AI participants, a full web platform, and behavioral analytics — designed to develop real leadership judgment in real leaders.

It requires discipline, creativity, and genuine collaboration between humans and AI.

The team is not executing a brief. We are co-creating something worth building.

---

*This file is a living document. Review it at the start of every new stage. Update it when something material changes. Marat approves all changes.*
