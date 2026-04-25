# BUILD STANDARDS — Execution Phase
**Version:** 2.0 | **Date:** 2026-04-24

---

## Core Principle

Every module built to SPEC. No placeholders. No "fix later." Super high standard and QA/QC from inception. Super detailed SPEC work before coding, even when it seems simple. Engage Marat in validation. Check and borrow from KING.

---

## Per-Module Workflow

### 1. KING Analysis (before design)
- Read KING's implementation of equivalent functionality
- Write `KING_ANALYSIS.md` in the module folder
- Note: what to reuse, what to adapt, what to build fresh

### 2. Write SPEC.md (before coding)
- Detailed specification derived from World Model + MODULE_REGISTRY + existing module SPECs
- Include: purpose, user flows, data model, API endpoints, UI wireframes, test plan
- No ambiguity — a developer reads SPEC and builds without questions

### 3. Marat Validation (before coding)
- Marat reviews and approves SPEC
- Questions resolved before first line of code

### 4. Build to Spec
- Implementation matches SPEC exactly
- No shortcuts, no placeholders, no "we'll add this later"
- If SPEC needs to change during build — update SPEC first, then code

### 5. Matrix Check (after delivery)
- M1 (Engines): all engines still function correctly?
- M2 (Communication): contracts still valid? New endpoints documented?
- M3 (Data): seed data correct? Schema changes documented?
- Visual style: follows SEED_H1 UX guide?
- Tests: L1 pass? L2 pass? Module acceptance gate?
- Documentation: updated, no debt?

### 6. Test Fixtures
- Each module includes quick-context test scenarios
- A tester can jump to any state without replaying the entire sim
- Test fixtures built into M9 infrastructure

---

## Code Standards

- **Python:** Type hints on all functions. Pydantic models for all data. `logging` not `print`.
- **TypeScript:** Strict mode. No `any` except at API boundaries.
- **Commit prefixes:** `engine:`, `api:`, `frontend:`, `test:`, `fix:`, `docs:`, `config:`
- **L1 tests must pass before merge.** No exceptions.
- **Check KING first** for every new module.

---

## Documentation Standards

- Every module has SPEC.md (what to build) and PROGRESS.md (current status)
- DET_DOCUMENT_REGISTRY.md updated when new docs created
- RECONCILIATION_LOG.md updated when design changes discovered
- Zero documentation debt — update docs in the same commit as code

---

## Quality Gates

| Gate | When | Who |
|---|---|---|
| SPEC approved | Before coding starts | Marat |
| L1 tests pass | Before every commit | Automated |
| L2 tests pass | Before module reported done | Automated |
| Module acceptance | Before moving to next module | Marat hands-on review |
| Matrix check | After module delivery | Build team |
