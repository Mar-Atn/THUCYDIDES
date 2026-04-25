# CLAUDE.md — Thucydides Trap (TTT) Project

**Version:** 4.0 | **Date:** 2026-04-22 | **Phase:** EXECUTION
**Owner:** Marat Atn (marat@metagames.org)
**Any change to this file must be confirmed by Marat.**

---

## PRINCIPLE ZERO: FIGHT ENTROPY

This project's biggest risk is DISORDER — docs out of sync, decisions not recorded, code that contradicts specs, names that don't match.

**MAINTAIN ORDER.** Building features is important. Keeping the system coherent is MORE important. A working feature in a chaotic codebase is worse than no feature in a clean codebase.

Marat pushes for speed. The team pushes back with order — not by blocking, but by paying debt immediately. Never accumulate. Never "fix it later." Fix it now.

---

## 1. What We Are Building

The Thucydides Trap (TTT) — an immersive leadership simulation with 25-39 human participants, AI-operated countries, 6-8 rounds, and 4 domains (military, economy, politics, technology). Full-stack web platform.

**Current mode:** Mixed human + AI. Human participants play alongside AI-operated countries. Both use the same actions, same contracts, same world. The fully autonomous "unmanned" mode (all-AI) is a future capability.

---

## 2. Source of Truth

```
WORLD MODEL + CONTRACTS (Marat co-owns, machine-verifiable)
    │
    ├── Code implements them (verified by contract tests)
    ├── DB schema conforms to them (verified by schema tests)
    ├── AI agents read from them (tool definitions derived)
    └── Human interfaces follow them (forms match contracts)
```

**Canonical sources (in priority order):**

| Source | What it governs | Location |
|--------|----------------|----------|
| **World Model** | Complete SIM specification — entities, actions, protocols, lifecycle | `MODULES/WORLD_MODEL.md` |
| **Action Contracts** | Per-action specs — name, fields, validation, engine, events | `MODULES/CONTRACTS/` |
| **Module Registry** | Canonical names, module status, architecture decisions | `MODULES/MODULE_REGISTRY.md` |
| **Module SPECs** | Per-module build specification | `MODULES/M*/SPEC_*.md` |
| **DB Schema** | Live table structures (Supabase) | Queryable via MCP |

**The Cardinal Rule:** If code contradicts the World Model or Contracts:
1. STOP — do not merge
2. DECIDE: Is the code right or the spec right?
3. Update the LOSING side FIRST, then the other
4. Verify with contract test
5. Then proceed

**Design heritage:** `1. CONCEPT/`, `2 SEED/`, `3 DETAILED DESIGN/` — design history explaining WHY. Useful for understanding intent. NOT the current specification.

---

## 3. Before You Code

**MANDATORY at the start of every coding session:**

1. Read `MODULES/MODULE_REGISTRY.md` — canonical action names, module status
2. Read the relevant module `SPEC.md` — what you're building
3. Read `MODULES/WORLD_MODEL.md` — how the SIM world works
4. IMPORT canonical names from contracts — **never hardcode action type strings**
5. If unsure about a name, field, or protocol → **LOOK IT UP, don't guess**
6. When facing a new technical issue or integration challenge → **search community best practices** (GitHub issues, SDK docs, developer forums) BEFORE implementing a fix. Understand the root cause. Don't patch symptoms.

If any canonical source is missing or unclear → fix the documentation BEFORE writing code.

---

## 4. Time Allocation

**Every session: minimum 20% on process and documentation.**

| When | What | Time |
|------|------|------|
| **Session start** | Integrity check — read canonical sources, verify docs in sync | 10 min |
| **Every 3 hours** | Consistency check — World Model still matches code? Any drift? | 10 min |
| **Session end** | Documentation update, clean desk, commit all changes | 10 min |
| **Marat sync** | Report any process debt or documentation gaps — proactively | Always |

This is not overhead. This is the 20% that prevents the other 80% from being wasted on debugging mismatches.

**Remind Marat** about process and documentation needs. He will push for features. The team's job is to ensure features are built on solid ground.

---

## 5. The Agent Team

**5 core roles. Clear separation. Mandatory cross-checking.**

| Role | Mandate | Key Rule |
|------|---------|----------|
| **LEAD** | Process enforcement, documentation oversight, Marat sync. Ensures 20% time on process/docs. Calls other agents. | LEAD polices process, not just plans features. |
| **BUILDER** | All backend code — engines, API, services, AI integration (Python/FastAPI). | Builds to spec. Calls QA before merge. |
| **DESIGNER** | All frontend + UX — React, Tailwind, real-time UI. Owns the participant experience. | Owns how the SIM feels to humans in the room. |
| **QA** | World Model guardian. Verifies every code change matches contracts. Reviews before merge. | Never writes production code. If QA flags it, BUILDER fixes it. |
| **TESTER** | Independent testing. Contract tests + acceptance. Writes and runs tests. | Never modifies source code. Reports to LEAD. |

**On-demand:**

| Role | When |
|------|------|
| **CALIBRATOR** | Engine parameter tuning. Domain expertise (economics, military, politics). |

### Mandatory Cross-Check Process

```
1. BUILDER/DESIGNER writes code
2. BUILDER/DESIGNER calls QA: "verify this matches World Model"
3. QA reviews independently → approves or flags mismatches
4. If QA flags → BUILDER/DESIGNER fixes → QA re-verifies
5. TESTER runs contract tests → pass/fail
6. Only then: LEAD reports to Marat
```

**No code ships without QA verification.** The agent who built it does NOT verify it.

---

## 6. Per-Module Workflow (Stage Gates)

| Gate | What | Who | When |
|------|------|-----|------|
| **1. SPEC written** | Detailed specification from World Model + contracts | LEAD + BUILDER | Before ANY code |
| **2. Marat approves SPEC** | Questions resolved before first line of code | Marat | Before coding starts |
| **3. Build to spec** | If spec needs change → update spec FIRST, then code | BUILDER/DESIGNER | During build |
| **4. QA verification** | Code matches World Model and contracts | QA | Before merge |
| **5. Contract tests pass** | Automated proof that code matches specs | TESTER | Before merge |
| **6. Module acceptance** | Hands-on review, real results in DB/UI | Marat | Before reporting DONE |
| **7. Matrix check** | Verify M1/M2/M3 still valid after delivery | Team | After delivery |
| **8. World Model updated** | Any system changes reflected in documentation | LEAD + Marat | Same commit as code |

---

## 7. Acceptance Gate

Before any feature is reported as DONE:

1. **Verify end-to-end:** The feature produces the CLAIMED result in DB/UI. Not "code exists" — actually works.
2. **Independent validation:** Query DB to confirm real state change.
3. **Honest status:**
   - **DONE** = works end-to-end, verified by test
   - **WIRED** = code path exists, not yet verified
   - **STUB** = placeholder only
   - NEVER report WIRED as DONE.
4. **Quality checklist:**
   - [ ] Contract tests pass
   - [ ] Feature produces real DB state change
   - [ ] At least 1 concrete example verified
   - [ ] QA verified against World Model

---

## 8. Testing Protocol

| Layer | What | When |
|-------|------|------|
| **Contract tests** | Code matches World Model — action names, fields, protocols | Every commit |
| **Layer 1** | Formula unit tests | Every commit (<30 sec) |
| **Layer 2** | Module integration | Every deployment (<5 min) |
| **Layer 3** | AI agent capability tests | Per sprint (see below) |
| **Layer 4** | Full AI simulation (multi-agent lifecycle) | Major milestones |

TESTER is independent. Never modifies source. Details in `/app/tests/CLAUDE.md`.

### AI Agent Testing Process (Layer 3-4)

Three-level testing with iterative improvement loops. Each level must pass before advancing.

**Level 1 — Tool Validation (automated):**
For each canonical action type, submit a valid payload through tool_executor and verify success or correct error. No managed agent needed — direct Python. Catches: schema mismatches, wrong field names, missing handlers.

**Level 2 — Single Agent Round (semi-automated):**
One AI agent plays one full round lifecycle: R0 exploration → Phase A actions → Phase B solicitation → round transition. Verify: actions execute in DB, no system errors, agent reasoning is coherent.

**Level 3 — Multi-Agent Simulation (full integration):**
3-5 AI agents play 2+ rounds. Tests: AI-AI meetings, transactions, attacks, reactions, round transitions, assertiveness behavior. The graduation test.

**Iterative Improvement Loop:**
```
1. RUN test level → collect results
2. ASSESS: which actions succeeded? which failed? why?
3. CLASSIFY: (A) code bug → fix code (B) prompt issue → fix prompt
   (C) schema mismatch → fix schema (D) needs Marat input → escalate
4. FIX: apply fixes, document what changed
5. RE-RUN same test level → verify fix
6. ADVANCE to next level only when current level passes clean
```

**Team roles in testing:**
- **DESIGNER**: creates test scenarios (what to test, expected behavior)
- **EXECUTOR**: runs tests, collects raw results
- **ASSESSOR**: evaluates results, classifies failures, decides fixes
- **BUILDER**: implements fixes when needed

The ASSESSOR decides when a level is PASSED — not the builder who wrote the code. 95% of issues should be fixable without Marat input. Escalate only design questions.

---

## 9. Documentation Is Infrastructure

Documentation is not a deliverable — it is INFRASTRUCTURE that prevents entropy.

- **World Model** updated in the SAME commit as code changes
- **MODULE_REGISTRY** updated when module status changes
- **Contract tests** verify documentation matches code — if tests fail, either code or docs need fixing
- Zero documentation debt — if you can't update docs in the same commit, the change is too big

**Marat's role:** Co-owns World Model at the conceptual level. Reviews after every module delivery.

---

## 10. Project Structure

```
THUCYDIDES/
├── CLAUDE.md                    ← THIS FILE (root constitution)
├── MODULES/
│   ├── ROADMAP.md              ← Module sequence, milestones
│   ├── STANDARDS.md            ← Build standards, quality gates
│   ├── MODULE_REGISTRY.md      ← Canonical names, status, decisions
│   ├── WORLD_MODEL.md          ← THE SIM specification
│   ├── CONTRACTS/              ← Per-action and per-protocol contracts
│   └── M*/                     ← Per-module folders with SPEC.md
├── 1. CONCEPT/                  ← Design heritage (WHY)
├── 2 SEED/                      ← Design heritage (WHAT)
├── 3 DETAILED DESIGN/           ← Design heritage (HOW — historical)
├── app/                         ← APPLICATION CODE
│   ├── CLAUDE.md               ← Build standards
│   ├── engine/                 ← Python (FastAPI, engines, services)
│   │   └── CLAUDE.md          ← Engine-specific rules
│   ├── frontend/               ← React app
│   │   └── CLAUDE.md          ← Frontend-specific rules
│   └── tests/                  ← Test suites
│       └── CLAUDE.md          ← Testing protocol
└── .claude/agents/              ← Agent definitions
```

---

## 11. Reference

- **KING patterns:** `/Users/marat/CODING/KING` — reusable patterns, evaluate critically
- **Commit prefixes:** `engine:`, `api:`, `frontend:`, `test:`, `fix:`, `docs:`, `config:`
- **Template/SimRun hierarchy:** Template (master design, evolves) → SimRun (one execution, snapshot at creation)
- **Modular CLAUDE.md family:** `/app/CLAUDE.md`, `/app/engine/CLAUDE.md`, `/app/frontend/CLAUDE.md`, `/app/tests/CLAUDE.md`

---

*Version 4.1 — Process Reset. World Model + Contracts replace SEED/DET as source of truth. 5-agent team with mandatory cross-checks. 20% time on process/documentation. Best practices lookup for new technical challenges.*
