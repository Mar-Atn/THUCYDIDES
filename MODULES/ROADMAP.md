# TTT EXECUTION ROADMAP
**Version:** 1.0 | **Date:** 2026-04-13 | **Timeline:** 6 weeks
**Target:** Working SIM for 25-30 human participants + 0-7 AI participants

---

## Module Sequence

```
Week 1-2:  M10.1 (Auth) + M9 (Sim Setup) + M4 (Sim Runner MVP)
Week 2-3:  M8 (Public Screen) + M4 (Facilitator controls)
Week 3-5:  M6 (Human Participant Interface)
Week 5-6:  M5 (AI Participant — basic) + M7 (Navigator MVP) + M10 (Assembly)
```

---

## Modules

| # | Module | Purpose | KING Reuse? | Status |
|---|---|---|---|---|
| **M1** | World Model Engines | Economic/political/military/technology formulas. NOUS judgment (Pass 2) = sub-module. | — | ✅ DONE |
| **M2** | Communication & Standards | Contracts, dispatcher, validators, real-time channels, event schemas. | — | ✅ DONE |
| **M3** | Data Foundation | Template/Scenario/Run, DB schema, seed data, state snapshots. | — | ✅ DONE |
| **M10.1** | Auth | Login for humans + moderator. JWT, roles, session. | YES — heavy | ❌ Week 1 |
| **M9** | Sim Setup & Configuration | Template editing, scenario config, role assignment, user mgmt. Pre-sim. | YES — heavy | ❌ Week 1-2 |
| **M4** | Sim Runner & Facilitator | Round orchestration, Phase A/B/Inter-Round, facilitator controls. | YES — moderate | ⚠️ Week 1-3 |
| **M8** | Public Screen | Room display: maps, dashboards, activity, narrative. | Moderate | ⚠️ Week 2-3 |
| **M6** | Human Participant Interface | Role dashboards, action submission, world view, map interaction. | YES — moderate | ❌ Week 3-5 |
| **M5** | AI Participant | Autonomous agents (basic: mandatory decisions + simple actions). | Moderate | ⚠️ Week 5-6 |
| **M7** | Navigator | Personal AI assistant for human participants. MVP: rules + strategy. | Low (new concept) | ❌ Week 5-6 |
| **M10** | Final Assembly | Integration testing, reliability, production deployment. | — | ❌ Week 6 |

---

## Foundation (already built — reference in MODULES/FOUNDATION/)

- **25 action engines** with locked contracts and validators
- **Action dispatcher** routing all types to engines
- **DB schema** (55+ tables, Template/Scenario/Run hierarchy)
- **Phase A/B/Inter-Round** round flow defined
- **10 context blocks** for AI agents
- **Dual LLM provider** (Gemini + Claude)
- **976 tests** across L1/L2/L3
- **125 design documents** reconciled (CONCEPT → SEED → DET)

---

## Per-Module Protocol

Before starting ANY module:

1. **KING analysis** — read KING's equivalent, note patterns to reuse/adapt
2. **Write SPEC.md** — detailed spec derived from design docs + KING + Marat input
3. **Marat validation** — review and approve spec before coding
4. **Build to spec** — no placeholders, no "fix later"
5. **Matrix check** — verify M1/M2/M3 still valid after delivery
6. **Documentation update** — zero debt

---

## Matrix Check (after each module delivery)

- [ ] M1 (Engines): still function correctly?
- [ ] M2 (Communication): contracts valid? New endpoints documented?
- [ ] M3 (Data): seed data correct? Schema changes documented?
- [ ] Visual style: follows SEED_H1 UX guide?
- [ ] Tests: L1 pass? L2 pass? Module acceptance gate?
- [ ] Documentation: updated, no debt?

---

## Milestones

| Milestone | When | What it proves |
|---|---|---|
| **Auth + Setup + Runner MVP** | End of week 2 | Can create a sim and start a round |
| **Public Screen live** | End of week 3 | Can watch the sim in a room |
| **Human can play** | End of week 5 | A human participant can log in, see their role, submit actions, see results |
| **Mixed mode works** | End of week 6 | 25 humans + 5 AI countries play 2+ rounds |

---

## Postponed (revisit after main delivery)

- Court/tribunal mechanics (ICJ, international judicial actions)
- Full 40-role AI expansion with bilateral conversations
- Information scoping / fog of war
- AI event reactions (mid-round responses)
- Voice integration (ElevenLabs)
- 50+ calibration runs
- Multi-session support
