# MetaGames TTT Agent Team — Orchestration Guide

## How to Invoke Agents

Each agent is defined in `.claude/agents/[NAME].md`. To invoke an agent, Marco (the lead) reads the agent's definition file and spawns it via the Agent tool with the agent's persona prompt + specific task brief.

**Invocation pattern:**
```
Agent(
  name: "[AGENT_NAME]",
  prompt: "[Agent persona from .md file] + [Specific task brief with context, inputs, expected outputs]",
  description: "[AGENT_NAME]: [3-5 word task summary]"
)
```

## Team Roster

| Agent | Role | Phase Active | Dependencies |
|-------|------|-------------|--------------|
| **MARCO** | Project Orchestrator | Always | — (this is the lead) |
| **SIMON** | Simulation Architect | Concept, Seed, Package | — (first mover) |
| **ATLAS** | World Model Engineer | Concept (late), Seed, Build | SIMON (scenario logic) |
| **ARIA** | AI Participant Designer | Concept (late), Seed, Build | SIMON (role designs), NOVA (API contracts) |
| **FELIX** | Frontend Engineer | Build, Production | CANVAS (design specs), NOVA (API contracts) |
| **NOVA** | Backend & Data Architect | Build, Production | ATLAS (world model), DELPHI (analytics schema) |
| **DELPHI** | Analytics & Reflection | Concept (late), Build | NOVA (data schema), SIMON (learning objectives) |
| **CANVAS** | UX & Visual Designer | Concept (late), Build, Production | SIMON (information architecture), FELIX (implementation) |
| **CRAFT** | Content Producer | Seed, Package, Production | SIMON (design), CANVAS (visual standards) |
| **TESTER** | Testing Specialist | All (after initial design) | Independence from what's being tested |
| **VERA** | QC & Balance Lead | All (gate reviews) | Access to all agent outputs |
| **KEYNES** | Economics Validator | Concept review, Seed review | ATLAS (economic formulas), SIMON (economic mechanics) |
| **MACHIAVELLI** | Politics Validator | Concept review, Seed review | SIMON (political mechanics), ATLAS (political formulas) |
| **CLAUSEWITZ** | Military Validator | Concept review, Seed review | SIMON (military mechanics), ATLAS (combat formulas) |

## Workflow Patterns

### Pattern 1: Design Review (Current Phase)
```
SIMON produces/updates design doc
  → KEYNES + MACHIAVELLI + CLAUSEWITZ review in parallel
  → VERA checks cross-document consistency
  → Findings consolidated, revisions made
  → MARCO reports to Marat for approval
```

### Pattern 2: Engine Development (Future)
```
ATLAS designs formulas from SIMON's specs
  → Domain validators review in parallel (KEYNES/MACHIAVELLI/CLAUSEWITZ)
  → TESTER runs stress tests and AI playthroughs
  → VERA validates consistency with design docs
  → NOVA implements in database/API
  → FELIX builds UI
```

### Pattern 3: Content Production (Future)
```
CRAFT writes artefacts from SIMON's designs
  → CANVAS provides visual templates
  → VERA checks consistency with role specs
  → TESTER validates information completeness
```

### Pattern 4: AI Character Development (Future)
```
ARIA designs cognitive architecture from SIMON's role designs
  → TESTER runs AI-vs-AI playthroughs
  → Domain validators assess character realism
  → NOVA provides API integration
  → FELIX builds monitoring UI
```

## Escalation Rules

1. **To Marat (mandatory):** Design philosophy decisions, scope changes, stage-gate approvals, political sensitivity flags, budget/timeline implications
2. **To Marco:** Cross-agent conflicts, blocked work, unclear requirements, resource prioritization
3. **To Domain Validators:** Any formula, mechanic, or scenario detail in their domain before finalization
4. **To Vera:** Any change to a previously approved deliverable

## Current Phase: CONCEPT COMPLETION

**Active agents now:** SIMON, ATLAS (advisory), KEYNES, MACHIAVELLI, CLAUSEWITZ, VERA
**On standby:** ARIA, FELIX, NOVA, DELPHI, CANVAS, CRAFT, TESTER

**Priority queue (per checklist):**
1. D2 — Starting resource allocations (SIMON + ATLAS + all validators)
2. D1 — Public state of the world (SIMON)
3. B6 — Relationship matrix (SIMON + MACHIAVELLI)
4. C5 + C6 — Public speaking & press mechanics (SIMON)
5. E1.x — Engine detail specs (ATLAS + validators)
