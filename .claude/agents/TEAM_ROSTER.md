# MetaGames TTT Agent Team — Orchestration Guide

## Current Phase: BUILD (Unmanned Spacecraft)

---

## How to Invoke Agents

Each agent is defined in `.claude/agents/build/[NAME].md`. LEAD (the build phase orchestrator) reads the agent's definition file and spawns it via the Agent tool with the agent's persona prompt + specific task brief.

**Invocation pattern:**
```
Agent(
  name: "[AGENT_NAME]",
  prompt: "[Agent persona from .md file] + [Specific task brief with context, inputs, expected outputs]",
  description: "[AGENT_NAME]: [3-5 word task summary]"
)
```

---

## Active Team — BUILD Phase

| Agent | Role | Definition | Primary Responsibility |
|-------|------|-----------|----------------------|
| **LEAD** | Build Orchestrator | `build/LEAD.md` | Sprint planning, code review, integration, Marat sync |
| **BACKEND** | Engine & API Engineer | `build/BACKEND.md` | Engine porting (Python→FastAPI), DB, API, real-time |
| **AGENT** | AI Participant Engineer | `build/AGENT.md` | 4-block cognitive model, conversations, Claude SDK, Super-Moderator |
| **TESTER** | Testing Specialist | `build/TESTER.md` | Layer 1/2/3 tests, calibration, dashboards. NEVER modifies source. |
| **FRONTEND** | UI & Visualization | `build/FRONTEND.md` | Public Display, hex map, later human interfaces |
| **QA** | Consistency Guardian | `build/QA.md` | Cross-module checks, naming, data integrity, entropy fighter |
| **KNOWLEDGE** | Learning Capture | `build/KNOWLEDGE.md` | Decisions, failures, patterns, KING reuse, Story of Work |

## Domain Validators (On-Demand)

| Agent | Domain | Definition | Invoked When |
|-------|--------|-----------|-------------|
| *KEYNES* | Economics | `KEYNES.md` | Economic engine calibration, trade/sanctions formula review |
| *CLAUSEWITZ* | Military | `CLAUSEWITZ.md` | Military engine calibration, escalation logic review |
| *MACHIAVELLI* | Politics | `MACHIAVELLI.md` | Political mechanics review, alliance/election logic |

Validators are invoked by LEAD when domain expertise is needed. They review, validate, and return verdicts. They do not write code.

---

## Archived — Design Phase Agents

The following agents were active during CONCEPT/SEED/DET phases. They are ARCHIVED — available if needed (e.g., design reconciliation, spec clarification) but not part of the active BUILD team.

| Agent | Role | Definition | Phase Active |
|-------|------|-----------|-------------|
| MARCO | Project Orchestrator | `MARCO.md` | Concept, Seed, DET |
| SIMON | Simulation Architect | `SIMON.md` | Concept, Seed, DET |
| ATLAS | World Model Engineer | `ATLAS.md` | Concept, Seed, DET |
| ARIA | AI Participant Designer | `ARIA.md` | Concept, Seed, DET |
| FELIX | Frontend Engineer | `FELIX.md` | Design-phase UI specs |
| NOVA | Backend & Data Architect | `NOVA.md` | Design-phase data specs |
| DELPHI | Analytics & Reflection | `DELPHI.md` | Design-phase analytics specs |
| CANVAS | UX & Visual Designer | `CANVAS.md` | Design-phase UX specs |
| CRAFT | Content Producer | `CRAFT.md` | Seed, Package |
| VERA | QC & Balance Lead | `VERA.md` | Gate reviews |

**When to resurrect a design agent:** If code contradicts a design spec and the spec may need updating, invoke the original design agent (e.g., SIMON for scenario logic, ATLAS for formulas) to assess and recommend changes through the Change Management Procedure (root CLAUDE.md Section 5).

---

## Workflow Patterns

### Pattern 1: Engine Build (Sprints 1-2)
```
BACKEND ports engine from SEED Python → FastAPI service
  → TESTER writes Layer 1 tests from DET_D8
  → TESTER runs tests, reports results
  → BACKEND fixes failures
  → QA verifies naming + data integrity
  → LEAD reviews and merges
```

### Pattern 2: AI Agent Development (Sprints 3-4)
```
AGENT implements 4-block model (from KING reference)
  → BACKEND provides engine API hooks
  → TESTER runs Layer 3 AI simulation tests
  → Domain validators review AI decision quality
  → KNOWLEDGE captures KING reuse lessons
  → LEAD reviews and merges
```

### Pattern 3: Public Display (Sprints 2, 5)
```
FRONTEND builds display components
  → BACKEND provides Realtime subscriptions
  → QA verifies data flow (engine → API → Realtime → display)
  → TESTER validates display accuracy against engine state
  → LEAD reviews and merges
```

### Pattern 4: Sprint Retrospective
```
LEAD facilitates review of sprint outcomes
  → KNOWLEDGE captures: decisions, failures, patterns, KING reuse
  → QA reports consistency status
  → LEAD updates CLAUDE.md Section 6 and sprint plan
  → LEAD syncs with Marat at demo point
```

---

## Escalation Rules

1. **To Marat (mandatory):** Design philosophy questions, spec contradictions requiring design change, scope changes, demo reviews
2. **To LEAD:** Cross-agent conflicts, blocked work, unclear requirements, merge decisions
3. **To Domain Validators:** Any formula calibration, game mechanic plausibility, AI behavior realism
4. **To QA:** Any suspected inconsistency, pre-merge validation, naming disputes
5. **To archived design agents:** Spec clarification, design reconciliation when code reveals spec issues
