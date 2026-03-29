# Development Approach
## TTT — How We Build, Test, and Learn
**Version:** 1.0 | **Date:** 2026-03-30 | **Status:** Draft for Marat review

---

## 1. Philosophy

**Build the product AND the machine for building products.**

TTT is not a disposable app. It's a professional-grade platform for immersive leadership simulations. The development approach must produce both:
1. A working, production-quality TTT web platform
2. A reusable development process and infrastructure for future MetaGames SIMs

Every decision below serves both goals.

---

## 2. Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Frontend** | React (Next.js) + Zustand + Tailwind | KING-proven. Real-time state management. H1 Tailwind config ready. |
| **Backend** | Supabase (PostgreSQL + Auth + Realtime + Edge Functions + Storage) | KING-proven. RLS enforces information asymmetry at database level. Real-time subscriptions for live updates. |
| **Engines** | Python (FastAPI) — containerized service | Already written and validated (8.75/10). Complex math stays in Python. Called via API by the frontend/Edge Functions. |
| **AI/LLM** | Provider-agnostic: Anthropic Claude (primary reasoning) + Google Gemini (conversations, context caching) | Best-in-class reasoning for geopolitical decisions. Switchable at runtime per task type. |
| **Voice** | ElevenLabs Conversational AI | KING-proven. Per-character voice profiles. Low-latency turn-taking. |
| **Deployment** | Vercel (frontend) + Supabase Cloud (backend) + Railway or Fly.io (Python engine service) | Managed services. Zero infrastructure maintenance. Auto-scaling. |
| **Testing** | Pytest (engines) + Vitest (frontend) + AI Simulation Framework (Layer 3) | Three-layer testing built into CI/CD. |

---

## 3. Module Architecture

Six build modules, each independently deployable and testable:

```
MODULE 1: PLATFORM
  Database schema + Auth + Real-time layer + File storage
  The foundation everything else depends on.

MODULE 2: ENGINES
  World Model + Live Action + Transaction engines
  Python service with API. Already prototyped.

MODULE 3: FACILITATOR DASHBOARD
  The command center. Build first because you need it to test everything else.
  Round management, engine controls, god-view, AI monitor.

MODULE 4: PARTICIPANT INTERFACE
  The main product. Mobile-first.
  Role dashboards, actions, hex map, event feed.

MODULE 5: AI PARTICIPANTS + ARGUS
  Autonomous AI agents + personal AI assistant.
  Needs Modules 1-4 working first.

MODULE 6: POLISH + LAUNCH
  Public display, scenario configurator, analytics, brief generation.
```

**Dependency chain:** 1 → 2 → 3 → 4 → 5 → 6 (mostly sequential, some parallel possible within phases).

---

## 4. Build Rhythm

### Weekly Cycle

```
Monday:    Plan — what to build this week, what to test
Tue-Thu:   Build — autonomous development, automated tests running
Friday:    Demo + Review — show what was built, test manually, decide next week
```

### Sync Points with Marat

| When | What | Duration | Marat's role |
|------|------|:--------:|-------------|
| **Weekly** | Status sync | 30 min | Review progress, flag concerns, set priorities |
| **At each module demo** | Hands-on review | 60 min | USE the product. Judge by feel, not by specs. |
| **On design questions** | Ad-hoc | 15 min | Only when the team can't resolve internally |
| **At phase gate** | Gate review | 90 min | Full review, approve to proceed |

**Between sync points:** Team works autonomously. Marat is NOT notified unless something breaks or a design question requires his judgment. This is the "earned autonomy" from CLAUDE.md Section 2.

### Module Demo Points

| Module | Demo shows | Marat judges |
|--------|-----------|-------------|
| 1 (Platform) | Login, see your role, data loads | "Does the data look right?" |
| 2 (Engines) | Submit budget, see GDP change | "Do the numbers feel realistic?" |
| 3 (Facilitator) | Run a round, see all countries, trigger world update | "Could I moderate a SIM with this?" |
| 4 (Participant) | Play a full round — see data, take actions, get results | "Would a participant understand this?" |
| 5 (AI) | 10 AI countries play alongside you | "Are they believable?" |
| 6 (Launch) | Full session end-to-end | "Would I sell this to a client?" |

---

## 5. Testing Strategy

### The Three Layers

**Layer 1: Formula Tests (automated, continuous)**

Every engine formula gets automated tests: input → expected output.
- Auto-generated from D8 (formula spec has exact numbers)
- Run on every code change (CI/CD pipeline)
- ~200-300 test cases covering all formulas, edge cases, boundary conditions
- Fast: <30 seconds to run entire suite
- **Purpose:** Catch formula bugs instantly. Regression prevention.

**Layer 2: Module Integration Tests (automated, per module)**

Each module gets 5-10 scenario tests:
- "Submit budget → engine processes → dashboard updates → correct values"
- "Initiate attack → authorization chain → dice resolution → map updates"
- "AI participant deliberates → submits action → engine processes → AI reflects"
- Run on every deployment to staging
- ~50-80 test cases across all modules
- **Purpose:** Catch integration bugs. Verify modules talk to each other correctly.

**Layer 3: AI Simulation Tests (periodic, comprehensive)**

AI agents play the full SIM — the approach proven in SEED testing:
- Run after each major milestone (module completion, integration point)
- 8 scenario battery (baseline + focused tests) — same as Battery 4 approach
- Each run: 6-8 rounds, 21 countries, all mechanics exercised
- Takes ~30-60 minutes per scenario
- Produces structured analysis: economic trajectories, military balance, political events, narrative coherence
- **Purpose:** Answer the REAL question — "does this produce interesting gameplay?"

### Testing Built INTO Development, Not After

```
Developer writes code → Layer 1 runs automatically → catches formula bugs
Module complete → Layer 2 runs → catches integration bugs
Milestone reached → Layer 3 runs → catches design/balance issues
```

No separate "QA phase." Testing is continuous. If a Layer 3 simulation produces nonsensical results, we catch it the week it happens — not 3 months later.

---

## 6. Quality Gates

Each module must pass before the next begins:

| Gate | What passes | Who decides |
|------|-----------|-------------|
| **Module complete** | All Layer 1 + Layer 2 tests pass | Automated (CI/CD) |
| **Integration verified** | Layer 3 simulation runs without crashes | TESTER agent |
| **Demo approved** | Marat uses the product and approves | Marat |
| **Phase gate** | All modules in phase pass + Layer 3 produces credible gameplay | Marat + VERA |

---

## 7. Knowledge Accumulation

### What We Learn

| Source | What it teaches | Where it's stored |
|--------|---------------|-------------------|
| Layer 3 simulation results | Balance issues, formula calibration, narrative quality | `10. TESTS/` + `EVOLVING METHODOLOGY/` |
| Module development experience | What patterns work, what's over-engineered, what's missing | `EVOLVING METHODOLOGY/` |
| Marat's demo feedback | Product judgment — what feels right, what doesn't | Session notes in memory |
| Cross-module integration | Where contracts are ambiguous, where assumptions break | System Contracts (living document) |

### How We Improve

After each phase:
1. **Retrospective:** What worked? What was harder than expected? What would we do differently?
2. **Methodology update:** New patterns added to `EVOLVING METHODOLOGY/`
3. **Agent team update:** Agent definitions refined based on what worked
4. **Template update:** Checklists, test scenarios, review protocols improved

### The Learning Organization Vision

By TTT launch, MetaGames has:
- A validated SIM design methodology (Concept → SEED → Detailed Design → Build)
- A reusable technology platform (React/Supabase/Python/AI)
- A testing framework that uses AI simulation as QA (Battery approach)
- An agent team structure that can be deployed on the next project
- A CLAUDE.md template for human-AI co-creation projects
- Documented lessons in EVOLVING METHODOLOGY that any future team can learn from

---

## 8. Risk Management

| Risk | Mitigation |
|------|-----------|
| Engine port introduces bugs | Layer 1 tests auto-generated from D8. Every formula tested before and after port. |
| Real-time layer unreliable | Use Supabase Realtime (proven in KING) + reconnection sync (learned from KING bugs). |
| AI participants too costly | Context caching (85% cost reduction, proven in KING). Model mixing (cheap model for routine, expensive for critical). |
| Scope creep | SEED is frozen. Only implement what's in the spec. New ideas go to "future" list, not current sprint. |
| Marat becomes bottleneck | Demo-point reviews only. Team works autonomously between demos. Clear escalation criteria. |
| Testing takes too long | Three-layer approach. Layer 1+2 are fast (<5 min). Layer 3 runs in background. No manual QA required. |

---

## 9. Communication Protocol

### Team → Marat

| Channel | When | Content |
|---------|------|---------|
| Weekly sync | Friday | "Here's what we built. Here's the demo. Here's next week." |
| Demo invitation | At module demo point | "Module X is ready for your review. Here's how to access it." |
| Blocker alert | When stuck >4 hours | "We need your decision on X. Options are A or B. Our recommendation is A because..." |
| Status dashboard | Always available | Live dashboard showing: modules status, test results, current sprint |

### Marat → Team

| Channel | When | Content |
|---------|------|---------|
| Demo feedback | After using product | "This feels right" / "This feels wrong because..." |
| Priority adjustment | Weekly sync | "Focus on X next week" / "De-prioritize Y" |
| Design decision | On blocker alert | "Go with A" or "Neither — here's what I want instead" |

### What Marat Does NOT Need to Do

- Read code
- Review pull requests
- Approve individual design decisions within an approved module
- Attend daily standups
- Write test cases
- Debug issues

---

*This document will be embedded into CLAUDE.md once the approach is validated through the first 2-3 modules of development.*
