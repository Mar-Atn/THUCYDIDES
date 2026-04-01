# DET_E3_DEV_PLAN_v1.md
## TTT Development Plan — "Unmanned Spacecraft" Strategy
**Version:** 1.0 | **Date:** 2026-04-01 | **Status:** ACTIVE
**Owner:** LEAD (Build Phase Orchestrator)
**Cross-references:** [Execution Concept Draft](DET_E3_EXECUTION_CONCEPT_DRAFT.md) | [KING AI Analysis](DET_KING_AI_ANALYSIS.md) | [Tech Stack](DET_D1_TECH_STACK.md) | [Round Workflow](DET_ROUND_WORKFLOW.md) | [CLAUDE.md v2](../CLAUDE.md)

---

# 1. THREE-PHASE OVERVIEW

The TTT application is built engine-first. The simulation runs fully autonomous before any human touches an interface. This inverts the typical UI-first approach and is correct because the ENGINE is the product — the interface is a window.

```
PHASE 1: UNMANNED SHIP          (Sprints 1-5, Weeks 1-11)
  Build the autonomous simulation: DB, engines, AI moderator, AI agents, public display.
  AI runs full 8-round SIMs without human intervention.
  Marat observes via Public Display and judges credibility.

PHASE 2: CALIBRATED & VALIDATED  (Weeks 12-15)
  50+ AI test runs. Formula tuning. Starting data calibration.
  The "social modelling lab" becomes operational.
  Parallel: UI component designs finalized on paper for Phase 3.

PHASE 3: MAKE IT HABITABLE       (Weeks 16-22)
  Facilitator Dashboard. Participant Interface. Argus. Voice.
  Human-in-the-loop playtesting. Mixed human + AI sessions.
```

**Why this order:**

| Reason | Detail |
|--------|--------|
| Engine IS the product | UI is a window into the engine. Fix the engine first. |
| AI testing is 100x faster | 50 AI runs = 1 day. 1 human playtest = full day + 40 people. |
| Calibration before interfaces | Saves massive UI rework when formulas change. |
| Marat validates by watching | The Public Display is the observation window — no buttons needed. |
| Risk reduction | Engine problems found in week 2, not month 4. |

---

# 2. PHASE 1: UNMANNED SHIP — FIVE SPRINTS

## Sprint 1: Foundation (Weeks 1-2)

**Goal:** Infrastructure deployed. Data in the database. Real-time proven. Scenario loads from DB.

| Deliverable | Owner | Detail |
|-------------|-------|--------|
| Supabase project deployed | BACKEND | Schema from `DET_B1_DATABASE_SCHEMA.sql` applied. RLS policies on all tables. |
| Seed data loaded | BACKEND | `DET_B3_SEED_DATA.sql` loaded. All 21 countries, 37 roles, zones, deployments, relationships populated. |
| Auth working | BACKEND | Magic link + email/password. JWT custom claims (`sim_id`, `role_id`, `country_id`, `access_level`). |
| Real-time proven | BACKEND | Supabase Realtime channels created (`public`, `country:{id}`, `moderator`). Round-trip latency measured. Reconnection protocol tested. |
| Scenario configurator (basic) | BACKEND | Edge function: load template into scenario, create SIM run. `POST /scenario/create`, `POST /sim-run/create`. |
| Template/Scenario/Run hierarchy | BACKEND | Three-level data separation working in DB (see Section 7). |
| Frontend scaffold | FRONTEND | React/Vite/TypeScript/Tailwind initialized. Supabase client connected. Auth flow working. Route structure (`/public`, `/facilitator`, `/participant`). |
| Layer 1 tests | TESTER | DB schema validation. Auth flow tests. Seed data integrity checks. |

**Demo Point (Marat):** Log into the app. See the database populated with all 21 countries and 37 roles. See a real-time event appear within 1 second of insertion. Create a SIM run from the base template.

---

## Sprint 2: Engines + Visibility (Weeks 3-4)

**Goal:** Python engines running on Railway. Engine reads from and writes to Supabase. Public Display shows world state. First Tier 1 test passes.

| Deliverable | Owner | Detail |
|-------------|-------|--------|
| Engine server deployed | BACKEND | FastAPI on Railway. Health check endpoint. Supabase REST client configured. |
| World Model Engine ported | BACKEND | `world_model_engine.py` wrapped in FastAPI. `POST /engine/round/process` reads world state from DB, runs 14-step pipeline, writes results back. |
| Live Action Engine ported | BACKEND | `live_action_engine.py` wrapped. `POST /engine/action` for combat, covert ops, political actions. |
| Transaction Engine ported | BACKEND | `transaction_engine.py` wrapped. `POST /engine/transaction` for bilateral transfers. |
| Engine-to-DB pipeline | BACKEND | Full round cycle: read state from Supabase → process → write new `world_state_snapshot` + `country_states` + `zone_states` + events → Realtime broadcasts updates. |
| Edge function proxies | BACKEND | Edge functions proxy frontend calls to Railway engine server. Auth validation on every call. |
| Public Display Light | FRONTEND | Single-page view: world state summary table (GDP, stability, oil price per country), round number, phase indicator. Auto-updates via Realtime subscription. No map yet. |
| Tier 1 test (first) | TESTER | Scripted 1-round processing: submit pre-defined budgets for all 21 countries → trigger round → verify all formulas produce expected outputs. No AI, no conversations. |
| Calibration begins | TESTER | First formula output review. Flag any values that look implausible. Log calibration notes. |

**Demo Point (Marat):** Watch the Public Display. Trigger a round manually. See GDP, stability, and oil price update in real time. Review the Tier 1 test results — are the numbers credible?

---

## Sprint 3: Orchestration (Weeks 5-6)

**Goal:** AI Super-Moderator runs rounds automatically. Full 8-round SIM completes without human intervention. Results exportable.

| Deliverable | Owner | Detail |
|-------------|-------|--------|
| AI Super-Moderator | BACKEND | Autonomous orchestrator: advances phases, collects submissions, triggers engine, publishes results, starts next round. Configurable timing (instant for testing, realistic for observation). |
| Round workflow automated | BACKEND | Full 17-step round workflow (per `DET_ROUND_WORKFLOW.md`) runs end-to-end without facilitator clicks. |
| Default budget submissions | BACKEND | When no AI agents exist yet: auto-generate budget allocations using simple heuristic rules (proportional to previous round, slight random variation). |
| Results export | BACKEND | `GET /sim-run/{id}/export` — JSON dump of full SIM state per round. CSV export of key indicators (GDP, stability, military strength, oil price) across all 8 rounds. |
| Tier 1 full 8-round test | TESTER | Complete 8-round SIM with heuristic budgets. Verify: no crashes, all formulas chain correctly across rounds, state accumulates properly, edge cases (war, sanctions, elections) trigger correctly. |
| Event log viewer | FRONTEND | Public Display addition: scrolling event log showing what happened each round (public-tier events only). |
| Calibration iteration | TESTER | Review 8-round output trajectories. GDP growth rates, stability drift, oil price oscillation — do they produce a credible 8-round arc? Flag formula parameters that need tuning. |

**Demo Point (Marat):** Press "Start SIM." Walk away for 2 minutes. Come back to a completed 8-round simulation. Review the Public Display — does the world tell a credible story? Download the CSV export. Review the numbers.

---

## Sprint 4: AI Agents (Weeks 7-9)

**Goal:** 10+ AI country agents making strategic decisions. Conversations between agents. Claude SDK prototype tested alongside 4-block model. Three testing tiers operational.

| Deliverable | Owner | Detail |
|-------------|-------|--------|
| 4-block cognitive model | AGENT | Ported from KING: Block 1 (rules — init + reflection only), Block 2 (identity/persona), Block 3 (memory/events), Block 4 (goals/strategy). Atomic versioning via PostgreSQL function. |
| Decision engine | AGENT | AI agents produce structured budget allocations, military orders, trade proposals, political actions. Output validated against game rules before submission. |
| Conversation engine (Tier 2) | AGENT | Modelled conversations: agents declare intent, system summarizes negotiation outcome without full dialogue. Fast (< 5 sec per conversation). |
| Conversation engine (Tier 3) | AGENT | Full text conversations: turn-by-turn dialogue between AI agents. Context caching (85% cost reduction, per KING analysis). End conditions: max turns, agent decides to end, all pass. |
| Intent notes | AGENT | 6-field strategic memo before conversations (ported from KING). Replaces Block 1 in conversation context to avoid rules drowning personality. |
| Reflection service | AGENT | Event-triggered updates to cognitive blocks. Priority queue (immediate: war declared on you. Batched: minor trade changes). |
| Claude SDK prototype | AGENT | Test Claude's native agent SDK for AI participants. Compare output quality, cost, and latency against the 4-block model. Document findings for Marat decision. |
| 10 solo AI agents running | AGENT | All 10 AI-operated countries (per SEED) producing autonomous decisions. Each agent has a distinct character, strategy profile, and voice. |
| Auto-triggers | BACKEND | Fire-and-forget async triggers on phase transitions (ported from KING). Agents reflect and plan between rounds without explicit invocation. |
| Tier 1/2/3 speed dial | TESTER | Three testing modes operational. Tier 1: ~2 min/SIM (no conversations). Tier 2: ~5 min/SIM (modelled conversations). Tier 3: ~30-40 min/SIM (full dialogue). |
| Calibration: AI behavior | TESTER | Do AI agents make plausible decisions? Do conversations produce realistic outcomes? Flag agents that exploit game mechanics or act out of character. |

**Demo Point (Marat):** Watch a Tier 3 simulation. Read the AI conversations. Are they in character? Do they negotiate realistically? Does the Cathay agent act like Cathay? Review the Claude SDK prototype results — is it worth switching from the 4-block model?

**Cost estimate:** ~$5-9 per full Tier 3 simulation run (10 AI agents, 8 rounds). Context caching essential.

---

## Sprint 5: Full Unmanned Ship (Weeks 10-11)

**Goal:** Public Display complete with hex map, theater views, and unit positions. Real-time push working at full fidelity. Full integration test passes. Speed dial verified across all tiers.

| Deliverable | Owner | Detail |
|-------------|-------|--------|
| Hex map renderer | FRONTEND | Custom SVG hex grid (10x20 global). Country colors at 55% opacity. Chokepoint markers. Zone tooltips (name, owner, visible forces). Pan/zoom via viewBox. |
| Theater map views | FRONTEND | Eastern Ereb theater (10x10 detail). Toggle between global and theater. Unit icons (tank, warship, drone, radar, missile) from `UNIT_ICONS_CONFIRMED.svg`. |
| Public Display full | FRONTEND | Complete observation screen: hex map + indicator dashboard (GDP comparison, oil price trend, stability) + event log + round/phase clock. Auto-updates via Realtime. Dark theme (Midnight Intelligence). |
| Real-time push verified | BACKEND | All 5 Realtime channels working under load. 21 concurrent AI agent updates pushing to clients. Latency < 2 seconds for state changes. Reconnection tested. |
| AI news ticker | AGENT | AI-generated news headlines summarizing each round's events. Displayed on Public Display. Generated by Claude Haiku (cheap, fast). |
| Full integration test | TESTER | Complete 8-round SIM: AI Super-Moderator + 10 AI agents + full conversation + engine + DB + Realtime + Public Display. End-to-end, nothing manual. |
| Speed dial verification | TESTER | All four tiers timed and documented. Tier 1: < 3 min. Tier 2: < 8 min. Tier 3: < 45 min. Tier 4 (voice): deferred to Phase 3. |
| Load test | TESTER | k6 script: 40 concurrent WebSocket connections + 21 AI agent API calls per round. Verify no dropped connections, no data races, no timeouts. |
| Phase 1 gate report | LEAD | Formal gate assessment: engine credibility, AI agent quality, infrastructure stability, known issues, calibration status. |

**Demo Point (Marat):** The full show. Start a Tier 3 SIM. Watch the Public Display as it runs — hex map updates with unit movements, GDP bars shift, events scroll, news headlines appear. This is the "unmanned spacecraft flying." Judge: Is this credible? Would you watch this for 4 hours?

---

# 3. CALIBRATION: CONTINUOUS FROM SPRINT 2

Calibration is not a phase — it is a continuous activity that runs alongside every sprint from Sprint 2 onward.

| Sprint | Calibration Focus | Method |
|--------|------------------|--------|
| Sprint 2 | Formula outputs | Tier 1: Are GDP, stability, military values in plausible ranges after 1 round? |
| Sprint 3 | Multi-round trajectories | Tier 1: Do 8-round arcs tell credible stories? Does Columbia's GDP grow? Does instability cascade? |
| Sprint 4 | AI decision quality | Tier 2/3: Do AI agents make decisions that produce interesting dynamics? Do wars break out? Do alliances form? |
| Sprint 5 | Full system integration | Tier 3: Does the complete system produce credible, varied outcomes across multiple runs? |
| Phase 2 | Statistical calibration | 50+ runs: parameter tuning based on aggregate outcomes. Distribution analysis. Outlier identification. |

**Calibration feedback loop:**
```
Run SIM → Observe results → Identify implausible outcomes →
  → Trace to formula parameter OR AI behavior OR starting data →
    → Adjust → Re-run → Verify improvement → Log change
```

**All calibration changes are logged** in a calibration journal with: what changed, why, before/after values, which test run triggered it.

---

# 4. PHASE 2: CALIBRATED & VALIDATED (Weeks 12-15)

**Entry gate:** Phase 1 complete. Unmanned ship flies reliably. Marat has watched at least 3 full Tier 3 runs.

| Deliverable | Owner | Detail |
|-------------|-------|--------|
| 50+ AI test runs | TESTER | Mix of Tier 1 (volume — 30+ runs for statistical analysis) and Tier 3 (depth — 20+ runs for narrative quality). |
| Formula parameter tuning | BACKEND + TESTER | Systematic adjustment of engine parameters based on aggregate outcomes. Target: every country has a viable path, no single dominant strategy, wars are costly but sometimes rational. |
| Starting data calibration | BACKEND + TESTER | GDP values, military deployments, stability scores, relationship scores — all tuned for interesting opening dynamics. |
| AI character tuning | AGENT + TESTER | Each AI country's persona refined: Cathay should be strategically patient, Ruritania should be opportunistic, etc. Character consistency across 50 runs verified. |
| Domain validator review | KEYNES, CLAUSEWITZ, MACHIAVELLI | Economic model credible? Military escalation ladder realistic? Political dynamics plausible? Formal sign-off from each. |
| Social modelling lab | TESTER | Scenario variant testing: "What if Cathay blockades at R2?" "What if sanctions are 2x stronger?" "What if oil starts at $120?" Document findings. |
| UI component designs (paper) | FRONTEND + LEAD | Screen-level wireframes for Facilitator Dashboard and Participant Interface. Finalized and approved before Phase 3 coding begins. |
| Phase 2 gate report | LEAD | Calibration complete. Credibility score from Marat. Domain validator sign-offs. Known limitations documented. |

**Gate criteria:**
- 50+ successful AI runs with no crashes
- Marat rates overall credibility >= 8/10
- All three domain validators sign off (Valid or Calibrate, no Redesign)
- No single dominant strategy identified across 50 runs
- Starting data stable (no changes needed for 10+ consecutive runs)
- UI wireframes approved for Phase 3

---

# 5. PHASE 3: MAKE IT HABITABLE (Weeks 16-22)

**Entry gate:** Phase 2 complete. Calibration signed off. UI wireframes approved.

| Deliverable | Owner | Weeks |
|-------------|-------|-------|
| Facilitator Dashboard | FRONTEND + BACKEND | 16-18 |
| Participant Interface | FRONTEND + BACKEND | 18-20 |
| Argus Integration | AGENT + FRONTEND | 20-21 |
| Voice Integration | AGENT + FRONTEND | 21-22 |
| Human-in-the-loop testing | TESTER + ALL | 20-22 (overlapping) |

### Facilitator Dashboard (Weeks 16-18)

The moderator's god-view and control surface.

- Round management: advance phases, trigger engine, publish results, override values
- AI agent manager: monitor agent status, pause/resume agents, view agent reasoning logs
- World state overview: all countries visible, all variables exposed
- Event log with full visibility (all tiers: public + country + role + moderator)
- Engine diagnostics: coherence flags, expert panel adjustments, formula traces
- Scenario controls: adjust parameters mid-SIM if needed

### Participant Interface (Weeks 18-20)

The player experience — mobile-first, role-specific.

- Role-specific dashboard: only information your role can see (RLS-enforced)
- Budget submission form: allocate coins across categories
- Action submission: military orders, trade proposals, political actions
- Communication: message other participants (human or AI)
- World view: filtered world state, hex map (own forces + public knowledge only)
- Event log: personal + country + public events

### Argus Integration (Weeks 20-21)

AI advisory assistant for human participants.

- Text chat with Claude (Sonnet): "What are my options?" "What happens if I sanction Cathay?"
- Context-aware: knows the participant's role, country, current world state, recent events
- Does NOT reveal hidden information — respects the same visibility rules as the participant
- Voice mode (ElevenLabs): speak to Argus, hear responses in character voice

### Voice Integration (Weeks 21-22)

- ElevenLabs TTS for Argus responses
- Browser Speech API for voice input
- AI participant voice in meetings (Tier 4 mode)
- Meeting recording and transcription (Deepgram)

### Human-in-the-Loop Testing (Weeks 20-22)

| Test | Participants | Goal |
|------|-------------|------|
| Small group | Marat + 3-5 testers | UX feedback, flow validation, pain point identification |
| Mixed session | 5 humans + 10 AI | Verify humans and AI agents coexist seamlessly. Test information asymmetry. |
| Full dress rehearsal | 10+ humans + AI | Closest to production. Verify timing, cognitive load, facilitator workflow. |

**Phase 3 Gate Criteria:**
- Full session playable with 5+ humans and 10+ AI participants
- Facilitator can run entire SIM from dashboard without backend intervention
- Argus provides useful advisory (Marat rates >= 7/10)
- No critical UX blockers identified in human testing
- Marat approves for external playtest

---

# 6. TECHNOLOGY STACK SUMMARY

Full details in `DET_D1_TECH_STACK.md`. Summary for planning reference:

| Layer | Technology | Hosting |
|-------|-----------|---------|
| **Frontend** | React 18 + TypeScript + Vite + Tailwind + Zustand | Vercel |
| **Database** | PostgreSQL + RLS + Realtime | Supabase Cloud |
| **Auth** | Magic link + JWT custom claims | Supabase Auth |
| **Edge Functions** | Deno/TypeScript (proxies, auth hooks, light logic) | Supabase Edge |
| **Engine Server** | Python 3.11 + FastAPI + Uvicorn | Railway |
| **Primary AI** | Anthropic Claude Sonnet (participants, Argus, Pass 2/3) | Anthropic API |
| **Secondary AI** | Google Gemini 2.5 Flash (fallback, image gen) | Google API |
| **Voice Output** | ElevenLabs TTS + Conversational AI | ElevenLabs API |
| **Voice Input** | Browser Web Speech API | Client-side |
| **Transcription** | Deepgram (real-time) / Whisper (batch) | Deepgram API |
| **Error Tracking** | Sentry | Sentry Cloud |
| **CI/CD** | GitHub Actions + Vercel auto-deploy + Railway auto-deploy | GitHub |

---

# 7. TEMPLATE / SCENARIO / RUN ARCHITECTURE

Three-level hierarchy that separates design from configuration from execution.

```
TEMPLATE (master SIM design — evolves over months)
  └── SCENARIO (configured for a specific event — limited customization)
        └── SIM-RUN (one execution — immutable once started)
```

| Level | Contains | Mutability | Example |
|-------|----------|-----------|---------|
| **Template** | All game rules, formulas, role definitions, country data, map structure, AI profiles, card pools. The complete SIM design. | Evolves across sprints. Updated by design team. | "Thucydides Trap v1.0" |
| **Scenario** | Copied from template + facilitator customizations: which countries are AI-operated, starting round, modified parameters, selected event triggers, time limits. | Set before SIM starts. Can be tweaked between creation and launch. | "TTT Corporate Workshop — April 2026" |
| **SIM-Run** | One execution of a scenario. All state changes logged immutably. Round-by-round snapshots. | Append-only once started. Never modified retroactively. | "Run #47 — 2026-04-15 14:00" |

**Implementation:**
- Template data lives in `templates` table + related `template_*` tables
- `POST /scenario/create` copies template data into `scenarios` table + related tables, applying customizations
- `POST /sim-run/create` creates a new run from a scenario, initializing `world_state_snapshots[round=0]`
- This allows: running the same scenario multiple times (for testing), comparing runs, and rolling back to template defaults

---

# 8. RISK REGISTER

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|-----------|--------|------------|
| R1 | **AI conversation speed vs. depth** — Tier 3 runs too slow for rapid iteration | Medium | Medium | Speed dial: use Tier 1/2 for formula validation, Tier 3 only for narrative quality checks. Parallelize agent calls where possible. |
| R2 | **AI optimal strategies** — Agents find exploits humans would not | High | Medium | Feature for testing: document exploits, distinguish from legitimate strategy, patch game rules if exploit is degenerate. Validator review of exploits. |
| R3 | **Late UX discovery** — Human interface problems surface only in Phase 3 | Medium | High | Parallel UI design work during Phase 1-2. Paper wireframes reviewed by Marat before coding. Small-group human testing starts early in Phase 3. |
| R4 | **AI agent character drift** — Agents lose persona consistency over 8 rounds | Medium | High | Block 1 for init + reflection only (KING lesson). Intent notes replace Block 1 in conversations. Reflection service maintains character across rounds. Character consistency scored in Tier 3 tests. |
| R5 | **Engine formula instability** — Cascading errors across 14-step pipeline | Low | Critical | Layer 1 tests on every commit. Tier 1 full-SIM tests from Sprint 2. Known stable baseline (8.75/10 from SEED validation). Coherence checks in Pass 3. |
| R6 | **Real-time performance under load** — 40 WebSocket connections + frequent updates | Medium | High | Load test with k6 in Sprint 5. Supabase Realtime proven in KING for smaller scale. Fallback: batch updates instead of real-time for non-critical channels. |
| R7 | **Claude API rate limits during live SIM** — 10 agents + Argus + Pass 2/3 hitting limits | Medium | High | Dual provider (Claude + Gemini fallback). Model health monitoring with automatic fallback (ported from KING). Context caching reduces token volume. Stagger agent calls. |
| R8 | **Scope creep in Phase 1** — Temptation to add participant UI before unmanned ship is proven | High | Medium | Phase 1 has no participant interface. LEAD enforces boundary. Only Public Display + facilitator trigger. Human UI is Phase 3 only. |
| R9 | **Cost escalation from AI API calls** — 50+ Tier 3 runs at $5-9 each | Low | Low | ~$250-450 for full calibration phase. Context caching keeps per-run cost manageable. Tier 1/2 for most iteration. Budget monitoring per sprint. |
| R10 | **Single point of failure — Railway engine server** — Server down during live SIM | Low | Critical | Railway provides 99.9% uptime on Pro plan. Engine is stateless per request (reads from DB, writes to DB). If Railway goes down, can redeploy to Render within minutes. Engine code is containerized. |

---

# 9. GATE CRITERIA

### Phase 1 Gate: "The Unmanned Ship Flies"

| Criterion | Measured By |
|-----------|------------|
| Engine processes 8 rounds without errors | Tier 1 automated test (TESTER) |
| AI agents produce structured, valid decisions | Tier 2/3 test output review (AGENT + TESTER) |
| AI conversations are in-character and strategic | Marat reads 5+ conversations, rates >= 7/10 |
| Real-time updates reach Public Display < 2 sec | Load test measurement (TESTER) |
| Public Display shows credible world state | Marat watches full Tier 3 run, rates >= 7/10 |
| No data integrity issues across 8 rounds | DB consistency checks pass (TESTER) |
| All Tier 1 tests pass on every commit | CI/CD pipeline green (automated) |
| Claude SDK vs. 4-block comparison documented | Analysis document reviewed by Marat (AGENT) |

### Phase 2 Gate: "Calibration Complete"

| Criterion | Measured By |
|-----------|------------|
| 50+ successful AI runs (no crashes) | Test log (TESTER) |
| Marat overall credibility rating >= 8/10 | Marat observation of 3+ Tier 3 runs |
| No single dominant strategy across 50 runs | Strategy diversity analysis (TESTER) |
| Domain validators sign off (no Redesign verdicts) | KEYNES, CLAUSEWITZ, MACHIAVELLI formal review |
| Starting data stable for 10+ consecutive runs | Calibration journal (TESTER) |
| UI wireframes approved for Phase 3 | Marat sign-off on wireframes |

### Phase 3 Gate: "Ready for External Playtest"

| Criterion | Measured By |
|-----------|------------|
| Full session: 5+ humans + 10+ AI, no critical failures | Dress rehearsal test (ALL) |
| Facilitator runs SIM from dashboard, no backend intervention | Facilitator workflow test (TESTER) |
| Argus provides useful advisory | Marat rates >= 7/10 |
| No critical UX blockers from human testing | Human tester feedback consolidated (FRONTEND) |
| Information asymmetry verified (no data leaks via UI or API) | Security review (QA + TESTER) |
| Marat approves for external playtest | Final sign-off |

---

# 10. SPRINT CALENDAR

| Sprint | Weeks | Dates (indicative) | Key Milestone |
|--------|-------|-------------------|---------------|
| Sprint 1 | 1-2 | Apr 1 - Apr 14 | DB deployed, auth working, real-time proven |
| Sprint 2 | 3-4 | Apr 15 - Apr 28 | Engines on Railway, first Tier 1 test passes |
| Sprint 3 | 5-6 | Apr 29 - May 12 | AI Super-Moderator runs full 8-round SIM autonomously |
| Sprint 4 | 7-9 | May 13 - Jun 2 | 10 AI agents making decisions, Tier 3 operational |
| Sprint 5 | 10-11 | Jun 3 - Jun 16 | Full unmanned ship: hex map, real-time, integration test |
| **Phase 1 Gate** | | Jun 16 | Marat reviews. Go/no-go for Phase 2. |
| Phase 2 | 12-15 | Jun 17 - Jul 14 | 50+ runs, calibration, domain validation |
| **Phase 2 Gate** | | Jul 14 | Calibration signed off. UI wireframes approved. |
| Phase 3 | 16-22 | Jul 15 - Aug 25 | Human interfaces, Argus, voice, playtesting |
| **Phase 3 Gate** | | Aug 25 | Ready for external playtest. |

---

# 11. DEMO POINTS SUMMARY

Every sprint ends with a tangible demo for Marat. These are not status updates — they are hands-on moments where Marat sees the system and makes judgment calls.

| Sprint | Marat Sees | Marat Judges |
|--------|-----------|-------------|
| **1** | Database populated. Real-time event appears < 1 sec. SIM run created from template. | Is the data architecture right? Does the Template/Scenario/Run model make sense? |
| **2** | Public Display updates after round processing. Tier 1 test results. | Are the formula outputs credible? Do the numbers make sense for Round 1? |
| **3** | Full 8-round SIM runs autonomously. CSV export of results. | Does the 8-round arc tell a credible story? Is the world interesting after 8 rounds? |
| **4** | AI agent conversations. Tier 3 full SIM. Claude SDK comparison. | Are the AI characters believable? Is the conversation quality sufficient? 4-block or Claude SDK? |
| **5** | Full Public Display with hex map, theaters, units, charts, news ticker. Complete autonomous SIM. | Would you watch this for 4 hours? Is this credible enough to build human interfaces on top of? |

---

*This plan implements the "Unmanned Spacecraft" strategy agreed on 2026-03-31. All sprint deliverables trace back to DET specs. All gate criteria require Marat sign-off. The plan will be updated at each sprint boundary based on what we learn.*
