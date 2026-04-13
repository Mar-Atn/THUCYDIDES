# Execution Concept — Early Sketch
## "The Unmanned Spacecraft" Development Strategy
**Version:** Draft 0.1 | **Date:** 2026-03-31 | **Status:** Concept — for discussion and refinement

---

## Core Idea

Build the simulation as a fully autonomous system first ("unmanned spacecraft"), test it extensively with AI agents, then add human interfaces ("make it habitable"). This inverts the typical UI-first approach and is correct for TTT because the ENGINE is the product, not the interface.

---

## Three-Phase Build

### Phase 1: The Unmanned Ship

**Build:**
- Database + schema + seed data (SQL already exists)
- Engine service (port Python to FastAPI — code exists, validated to 8.75/10)
- Real-time layer (Supabase Realtime subscriptions)
- Communication layer and protocols (AI-to-AI messaging)
- Base template scenario + scenario configurator (load/modify scenarios)
- AI Super-Moderator (runs rounds automatically — advances phases, triggers engine, publishes results)
- AI Country Agents (all 21 countries autonomous — cognitive 4-block model)
- Public Display (the observation window — map, indicators, news, clock)
- Persia theater map (new — ground invasion terrain for the long war)

**Test:**
- AI runs full 8-round simulations autonomously
- Two testing modes:
  - **Quick-scan:** Fast agent decisions for formula/mechanic validation (~5 min per full SIM)
  - **Deep-play:** Deliberate agent reasoning for narrative/strategy validation (~30 min per full SIM)
- Marat watches public screen — judges credibility by observation
- 50+ test runs for calibration

**Iterate:**
- Fix formulas, calibrate starting data, adjust AI behavior
- All changes in the DB/engine — no UI rework needed
- Each iteration: change → test → observe → adjust

**Gate:** "The unmanned ship flies reliably." Engine credible. Data stable. Real-time layer proven. AI agents produce interesting gameplay.

### Phase 2: Calibrated & Validated

**Outcome of Phase 1 testing:**
- Scenarios refined through extensive AI testing
- Engine proven reliable under load
- Data architecture proven in production database
- Real-time layer proven with 21 concurrent AI agents
- Starting positions, card pools, formula parameters all calibrated
- The "mini social modelling lab" is operational

**Parallel workstream:** While Phase 1 tests, UI component designs (F1-F4) are finalized on paper — ready to build when Phase 3 starts.

**Gate:** Calibration complete. Design team confident in the mechanics. Ready for human habitation.

### Phase 3: Make It Habitable

**Build:**
- Facilitator Dashboard (moderator controls — god-view, engine controls, AI manager)
- Participant Interface (player experience — mobile-first, role-specific dashboards)
- Argus Integration (AI assistant for human participants — voice + text)
- Voice Integration (ElevenLabs for Argus + AI participant meetings)

**Test:**
- First human-in-the-loop playtest (small group — Marat + 3-5 testers)
- UX refinement based on real human feedback
- Mixed human + AI playtests (some humans, rest AI)

**Gate:** Full session playable. 5+ humans + 10 AI participants. Marat approves.

---

## Why This Order

1. **The engine IS the product.** UI is a window. Fix the engine first.
2. **AI testing is 100× faster** than human playtesting. 50 AI runs = 1 day. 1 human playtest = full day + 40 people.
3. **Calibration before interfaces** saves massive UI rework.
4. **Marat validates by watching** the public screen — not clicking buttons.
5. **Risk reduction:** Engine problems found in week 2, not month 4.

## Risks

1. **AI conversation speed vs. depth:** Quick-scan may miss strategic depth issues. Deep-play is slow. Need both modes.
2. **AI "optimal strategies":** Agents may find exploits humans wouldn't. Feature for testing, but must distinguish exploits from legitimate strategy.
3. **Late UX discovery:** Human interface problems won't surface until Phase 3. Mitigated by parallel UI design work during Phase 1-2.
4. **AI agent architecture quality:** If AI agents make unrealistic decisions, test results are misleading. Need credible cognitive model (the 4-block system from KING is proven).

## The Bonus: Mini Social Modelling Lab

If the unmanned system works well, it becomes more than a SIM tester — it's a platform for:
- Testing geopolitical scenarios ("what if Cathay blockades Formosa at R2?")
- Policy intervention testing ("what if sanctions are 2× stronger?")
- Leadership dynamic analysis ("which leadership style produces best outcomes?")
- Scenario design validation (test new SIM scenarios before human playtesting)

This is potentially a separate MetaGames product.

---

## Tomorrow's Priorities

1. **D2-D7:** Infrastructure setup (Supabase, Vercel, API keys, Git, dev environment)
2. **E1-E3:** CLAUDE.md v2 + agent team for BUILD + development plan (incorporating this execution concept)
3. **E4:** Testing architecture (two-mode AI testing framework)
4. **Persia theater map:** Create Mashriq theater map for ground war depth
5. **Finalize this document** into the formal development plan

---

*This is an early sketch from the Marat-MARCO strategy discussion (2026-03-31). To be refined into the formal DET_E3_DEV_PLAN when we finalize the Detailed Design phase.*
