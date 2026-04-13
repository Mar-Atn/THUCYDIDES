# CLAUDE.md — Thucydides Trap (TTT) Project

**Version:** 3.0 | **Date:** 2026-04-13 | **Phase:** EXECUTION — Module Build
**Owner:** Marat Atn (marat@metagames.org)
**Any change to this file must be confirmed by Marat.**

---

## CURRENT PHASE: EXECUTION (6-week sprint)

**Start here:** `MODULES/ROADMAP.md` — module sequence, timeline, milestones.
**Build standards:** `MODULES/STANDARDS.md` — per-module protocol, quality gates.
**Status dashboard:** `MODULES/MODULE_REGISTRY.md` — live status of all modules.
**Foundation reference:** `MODULES/FOUNDATION/` — what's already built (engines, communication, data).

**Design heritage (frozen reference):**
- `1. CONCEPT/` — what and why
- `2 SEED/` — how (specification level)
- `3 DETAILED DESIGN/` — how (implementation level), includes CONTRACTS/ and CARDS/
- `3 DETAILED DESIGN/DET_DOCUMENT_REGISTRY.md` — index to all 125+ design documents

**Reference cards:** `3 DETAILED DESIGN/CARDS/` — actions, formulas, architecture, template.
**Locked contracts:** `3 DETAILED DESIGN/CONTRACTS/` — 28 action specifications.

Every session: check ROADMAP.md and current module SPEC.md. Build to spec. Do not invent — look up.

---

## PRINCIPLE ZERO: FIGHT ENTROPY

This project's biggest risk is not bad design or bad code. It is DISORDER — files in wrong places, docs out of sync, decisions made but not recorded, code that contradicts specs.

Every agent, every session, every commit: **MAINTAIN ORDER.** Building features is important. Keeping the system coherent is MORE important. A working feature in a chaotic codebase is worse than no feature in a clean codebase.

Marat is a creative product leader, not a project manager. He will push for speed. The team MUST push back with order — not by blocking, but by logging debt and paying it immediately. Never accumulate. Never "fix it later." Fix it now.

---

## 1. What We Are Building

The Thucydides Trap (TTT) — an immersive leadership simulation with 25-39 human participants, 10+ AI-operated countries, 6-8 rounds, and 4 domains (military, economy, politics, technology). Full-stack web platform with autonomous AI participants.

**Current approach: "Unmanned Spacecraft."** Build a fully autonomous simulation first (AI moderator + AI agents + engine + public display), test with 50+ AI runs, calibrate, THEN add human interfaces. The unmanned mode is a permanent product capability, not scaffolding.

---

## 2. The Human Partner

**Marat Atn** — product owner and co-creator. All design philosophy and stage-gate decisions require Marat's approval. Sync rhythm:
- **Weekly:** 30-min status sync (Friday)
- **Demo points:** Hands-on review at each sprint milestone
- **On-demand:** Only for decisions the team cannot resolve
- **Between syncs:** Team works autonomously

---

## 3. The Agent Team

**7 BUILD roles + 3 domain validators.** See `.claude/agents/` for full definitions.

| Role | Primary Responsibility |
|------|----------------------|
| **LEAD** | Sprint planning, code review, integration, Marat sync |
| **BACKEND** | Engine (Python/FastAPI), DB, API, real-time layer |
| **AGENT** | AI participants (4-block model), conversations, Claude SDK |
| **TESTER** | Layer 1/2/3 tests, calibration, results dashboards. NEVER modifies source code. |
| **FRONTEND** | Public Display, later human interfaces |
| **QA** | Consistency checks, naming enforcement, integrity guardian |
| **KNOWLEDGE** | Learning capture, EVOLVING METHODOLOGY, patterns, Story of Work |
| *KEYNES* | Economics validation (on-demand) |
| *CLAUSEWITZ* | Military validation (on-demand) |
| *MACHIAVELLI* | Political validation (on-demand) |

---

## 4. Project Structure

```
THUCYDIDES/
├── CLAUDE.md                    ← THIS FILE (root constitution)
├── 1. CONCEPT/                  ← FROZEN. Do not modify.
├── 2 SEED/                      ← FROZEN. Do not modify.
├── 3 DETAILED DESIGN/           ← Reference specs for BUILD
├── 10. TESTS/                   ← All test results
├── EVOLVING METHODOLOGY/        ← Knowledge base (KNOWLEDGE agent maintains)
├── CONTEXT/                     ← Reference materials
├── app/                         ← APPLICATION CODE (BUILD phase)
│   ├── CLAUDE.md               ← Build standards
│   ├── engine/                 ← Python engines (FastAPI)
│   │   └── CLAUDE.md          ← Engine-specific rules
│   ├── frontend/               ← React app
│   │   └── CLAUDE.md          ← Frontend-specific rules
│   └── tests/                  ← Test suites
│       └── CLAUDE.md          ← Testing protocol
└── .claude/agents/              ← Agent definitions
```

---

## 5. Design Heritage & Code Hierarchy

**Stage-gate process:** IDEA → CONCEPT ✅ → SEED ✅ → DETAILED DESIGN ✅ (2026-04-01) → BUILD ← here

**BUILD combines:** iterative loops + waterfall discipline + mandatory documentation sync.

```
CONCEPT (frozen) → WHAT and WHY
  └── SEED (frozen) → Canonical specs
        └── DET (reference) → HOW exactly
              └── CODE (active) → Implements DET specs
```

**The Cardinal Rule:** If code contradicts any design document:
1. STOP — do not merge
2. DECIDE: Is the code right or the design right?
3. If code is right → unfreeze doc → update → integrity check → re-freeze → then merge
4. If design is right → fix code
5. Documentation-Implementation Reconciliation is MANDATORY. Code and docs must NEVER diverge.

---

## 6. Current Stage

> **BUILD Phase 1: Unmanned Spacecraft**
> Design gates: CONCEPT ✅ | SEED ✅ | DET in progress
> BUILD Sprint: 1 of 5

Five sprints (~11 weeks):
1. Foundation (DB, auth, real-time, scenario configurator)
2. Engines + Public Display Light
3. Orchestration (AI Super-Moderator, results export)
4. AI Agents (4-block model, Tier 1-3, Claude SDK prototype)
5. Full Unmanned Ship (full display, integration test)

---

## 7. Build Standards

- **Check KING first:** Before building anything, review `/Users/marat/CODING/KING` for reusable patterns. Strong recommendation — always critically evaluate, not mandatory to implement.
- **Commit prefixes:** `engine:`, `api:`, `frontend:`, `test:`, `fix:`, `docs:`, `config:`
- **Layer 1 tests must pass before merge.** No exceptions.
- Detailed coding standards in `/app/CLAUDE.md`

---

## 8. Testing Protocol

| Layer | What | When | Time |
|-------|------|------|------|
| **Layer 1** | Formula tests | Every commit | <30 sec |
| **Layer 2** | Module integration | Every deployment | <5 min |
| **Layer 3** | AI simulation (full SIM) | Per sprint milestone | 2-40 min |

**Speed dial:** Tier 1 (no conversations) → Tier 2 (modelled) → Tier 3 (full text) → Tier 4 (+ voice)

TESTER is independent. Never modifies source. Detailed protocol in `/app/tests/CLAUDE.md`

### Acceptance Gate (mandatory before reporting DONE)

Before any feature is reported as DONE or COMPLETE to Marat:

1. **Verify end-to-end:** The feature must produce the CLAIMED result in the DB/UI. Not "code exists" — actually works.
2. **Independent validation:** Run an L2 integration test OR query the DB to confirm the feature's output is real. If the feature claims "29 transactions executed" — verify at least 1 transaction actually changed asset ownership in the DB.
3. **Honest status reporting:**
   - **DONE** = feature works end-to-end, verified by test
   - **WIRED** = code path exists, events logged, but outcome not yet verified or incomplete
   - **STUB** = placeholder, logged only, no real processing
   - NEVER report WIRED as DONE. NEVER report counts of logged-but-unprocessed events as if they were successful outcomes.
4. **Quality checklist before DONE claim:**
   - [ ] L1 tests pass
   - [ ] Feature produces real DB state change (not just event log)
   - [ ] At least 1 concrete example verified in DB
   - [ ] Edge cases considered (what if counterpart doesn't respond? what if asset insufficient?)

Violation of this protocol erodes trust and creates false progress signals.

---

## 9. Integrity Protocol

| When | What |
|------|------|
| **Every session start** | Integrity check — docs in sync? stale references? |
| **Every merge** | Layer 1 pass? Design reconciliation needed? |
| **Every session end** | CLAUDE.md current? Checklist updated? All committed? Clean desk. |
| **Every 3 hours** | Mandatory consistency check. Non-negotiable. |
| **Weekly Friday** | Full cross-document review. |

**Clean Desk Rule:** At session end, a NEW Claude instance could start with zero prior context.

---

## 10. Template / Scenario / Run

```
TEMPLATE (master SIM design — evolves over months)
  └── SCENARIO (configured for event — limited customization)
        └── SIM-RUN (one execution — immutable once started)
```

**Template v1.0 milestone reached 2026-04-05.** Canonical map + units spec: `2 SEED/C_MECHANICS/SEED_C_MAP_UNITS_MASTER_v1.md`. DB schema draft: `CONCEPT TEST/db_schema_v1.sql`. Unit engineering contract: `3 DETAILED DESIGN/DET_UNIT_MODEL_v1.md`. Reconciliation status: `CONCEPT TEST/CHANGES_LOG.md`.

---

## 11. Learning Organization

KNOWLEDGE agent maintains `EVOLVING METHODOLOGY/`. After each sprint: retrospective → promote best practices to CLAUDE.md. See agent definition for details.

---

*Modular CLAUDE.md family. Subfolder files: `/app/CLAUDE.md`, `/app/engine/CLAUDE.md`, `/app/frontend/CLAUDE.md`, `/app/tests/CLAUDE.md`. Each <100 lines. This root file: ~100 lines.*
