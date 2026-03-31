# TTT Delivery Plan — Road to May 26
**Version:** 1.0 | **Date:** 2026-03-29 | **Owner:** Marat
**Target:** First live SIM with real participants — May 26, 2026

---

## Timeline Overview

```
MAR 29 ──── APR 3/5 ──── APR 18-19 ──── MAY 2-3 ──── MAY 20 ──── MAY 26
  │            │              │              │            │           │
  NOW    DESIGN REVIEW   WEB APP TEST   FULL SIM TEST  FREEZE    LIVE SIM
         (Marat+Timur     (5-7 testers)  (12-15 people) (prod     (25-30
          +Dima, 1hr)     core mechanics  near-full day  ready)   participants)
```

---

## Milestone 1: DESIGN REVIEW
**Date:** April 1 (Tuesday) or April 3 (Thursday) — confirm Monday
**Format:** Zoom/mixed, 1 hour total (20 min presentation + 40 min discussion)
**Participants:** Marat, Timur, Dima

### What We Present (20 min)
1. **Concept overview** (3 min) — the Thucydides Trap, 21 countries, 37 roles, why it matters
2. **SEED architecture** (5 min) — map, starting positions, two active wars, Gulf Gate blockade, 8-round structure
3. **AI test results** (5 min) — 3 test iterations (TESTS1-3), key dynamics that emerged, what the engine produces (oil price, stability, elections, ceasefires)
4. **UX/Style choices** (4 min) — Strategic Paper + Midnight Intelligence themes, country colors, emblems, unit icons, dashboard/map mockups
5. **Web app plan** (3 min) — tech stack, timeline, what's built vs what remains

### Questions for Timur & Dima (prepared, structured)

**SIM Design (Timur focus):**
1. **Complexity calibration:** We have 37 roles, 4 domains, 30+ action types. For a first run with 25-30 participants (mix of experienced and new) — is this the right level, or should we simplify for v1? What would you cut?
2. **Dilemma quality:** The core tension is Thucydides Trap (rising vs ruling power). In our tests, Cathay's patience was dominant (no need to fight). We added a Helmsman legacy clock. Is that enough pressure, or do we need structural forcing functions?
3. **Character credibility:** Our 37 roles have fictional names and detailed backstories. Do the role briefs feel like real people with real dilemmas, or do they read like game characters? (Share 2-3 sample briefs for review.)
4. **Timing realism:** 8 rounds × 6 months = 4 years of scenario time. Each round 45-80 min real time. Full day ~11.5 hours. Is this the right compression? Too fast? Too slow?

**Business & Participant Experience (Dima focus):**
5. **Participant profile:** CEOs, founders, senior executives, academia — mostly European. What's the right pitch? "Leadership development" or "strategic thinking exercise" or "geopolitical simulation"? What language resonates with this audience?
6. **Assessment/takeaway:** After the SIM, participants should receive a personal leadership report. What metrics/observations would be most valuable to a C-level participant? What would make them recommend this to peers?

**Both:**
7. **Starting positions & balance:** We'll show the opening state (oil at $137, two wars, Cathay naval buildup). Does the scenario feel credible as a near-future extrapolation? Any immediate "that would never happen" reactions?

### Deliverables to Prepare by Monday
- [ ] 15-slide deck (Concept → SEED → Tests → UX → Plan)
- [ ] 2-3 printed role briefs (Dealer, Helmsman, Beacon) for review
- [ ] Map printout with starting positions
- [ ] UX style demo open in browser
- [ ] This plan document shared with Timur & Dima

---

## Milestone 2: WEB APP TEST
**Date:** Saturday April 18 or 19
**Duration:** 4-5 hours (setup + 3-4 rounds + debrief)
**Participants:** 5-7 testers (core team + 2-3 invited friends)
**Location:** Remote (Zoom + web app) or at a convenient location

### Objectives
1. **App functionality** — Does the web app work? Login, dashboard, map, budget submission, military actions, communication, transactions — all core flows.
2. **Real-time sync** — When one player acts, do others see it? Latency, race conditions, data integrity.
3. **Engine integration** — Do budgets process? Do attacks resolve? Does the world model update correctly between rounds?
4. **UX clarity** — Can a new user understand their dashboard within 5 minutes? Is the map readable? Are actions intuitive?
5. **Audio/recording** — First test of the recording/transcription pipeline (see Dependencies).

### Test Configuration
- **Rounds:** 3-4 (enough to hit midterm election at R2)
- **Human roles:** 5-7 players, each running 1-2 positions. Suggested: Dealer, Helmsman, Pathfinder, Beacon, Scales + 1-2 solos
- **AI roles:** All remaining countries run by AI participants
- **Facilitator:** Marat (using facilitator dashboard)

### Success Criteria
- [ ] All players can log in and see their role dashboard
- [ ] Budget submission → engine processing → results displayed
- [ ] At least 1 military action resolves correctly on the map
- [ ] At least 1 bilateral transaction completes
- [ ] Communication system works (messaging between players)
- [ ] Round transition works (Phase A → B → C)
- [ ] No data loss or corruption across 3 rounds
- [ ] Recording/transcription produces usable output

### What We Learn
- Bug list (priority: critical / high / medium)
- UX friction points (where do players get confused?)
- Engine issues (any unrealistic outputs?)
- Timing calibration (how long does a round actually take with real humans?)

---

## Milestone 3: FULL SIM TEST
**Date:** Saturday May 2 or 3 (or Friday May 1 if Saturday not possible)
**Duration:** Full day (~8-10 hours including setup, breaks, debrief)
**Participants:** 12-15 people (team + friends + 5-8 invited alumni/contacts)
**Location:** Physical venue (see Dependencies)

### Objectives
1. **SIM design validation** — Do the dilemmas work? Do players face real choices? Do alliances form and break? Do wars start and end?
2. **Full round cycle** — 6-8 rounds, full Phase A/B/C, all mechanics active including elections (R2, R3-4, R5).
3. **AI participant quality** — Do AI-operated countries behave credibly? Can human players tell which countries are AI?
4. **Facilitator workflow** — Can the facilitator manage the room, the engine, the AI, and the timeline?
5. **Recording + analysis pipeline** — Full test of audio capture → transcription → analysis → report generation.
6. **Post-SIM report** — Generate a draft leadership report for each participant. Test the analytics/reflection pipeline.
7. **Timing** — How long does a full SIM actually take? Where do we need to compress or expand?

### Test Configuration
- **Rounds:** 6-8 (full arc: setup → escalation → climax → resolution)
- **Human roles:** 12-15 distributed across Columbia (3-4), Cathay (2-3), Europe (2-3), key solos (3-4), possibly Nordostan/Heartland (2)
- **AI roles:** Remaining countries + any unfilled team positions
- **Facilitator team:** Marat (lead) + 1 assistant facilitator + 1 engine operator

### Success Criteria
- [ ] Complete 6+ rounds without critical system failure
- [ ] At least 1 ceasefire or peace negotiation attempted
- [ ] At least 1 election produces visible political consequences
- [ ] Participant engagement sustained through 6+ hours (not losing people)
- [ ] AI countries act credibly (post-test survey: "could you tell which were AI?")
- [ ] Recording pipeline produces full transcript
- [ ] Draft leadership reports generated within 24 hours post-SIM
- [ ] Participant feedback: >70% would recommend to a peer

---

## Dependencies on Operations / Marketing Team

### MUST HAVE by dates:

| What | Owner | Deadline | Notes |
|------|-------|----------|-------|
| **25-30 confirmed participants** | Ops/Marketing | **May 5** | Reliably committed. Not "interested" — confirmed with calendar block. |
| **Participant commitment: full day** | Ops/Marketing | **May 5** | Clear communication: 9am-7pm (or 2-day format if chosen). No "I'll come for the morning." |
| **Venue identified** | Ops/Marketing | **April 20** | Requirements: main hall (30 people + screen), 3-5 meeting rooms, WiFi for 50 devices, power at every table, catering. |
| **Venue confirmed & paid** | Ops/Marketing | **April 25** | Deposit/contract signed. No last-minute changes. |
| **Sound recording solution — DECIDED** | Product + Ops | **April 10** | Must decide: how many mics, what type, where placed, how recorded, how transcribed. Options below. |
| **Sound recording solution — TESTED** | Product + Ops | **April 18** (web app test) | First test of whatever we choose. Must work before May test. |
| **Sound recording — PROCURED & READY** | Ops | **April 28** | All hardware purchased, software configured, tested end-to-end. |
| **Participant pre-registration** | Product + Ops | **May 10** | All participants registered in web app, roles assigned, login credentials sent. |
| **Pre-event materials sent** | Product + Ops | **May 19** | Welcome email, role teaser, world briefing PDF, login credentials. |
| **Physical materials printed** | Product | **May 20** | Role briefs, name badges, schedule cards, table signs. |

### Sound Recording — Decision Needed by April 10

**Option A: Room Microphones (simpler)**
- 5 omnidirectional USB mics placed in main hall + meeting rooms
- Record continuously to laptops/phones
- Post-processing: AI speaker diarization + transcription (e.g., Whisper + pyannote)
- Pros: Simple setup, no per-person hardware
- Cons: Cross-talk in main hall, speaker identification harder, meeting rooms need separate mics

**Option B: Per-Table Microphones**
- 1 mic per country table (6-8 mics) + 1 per meeting room (3-5 mics)
- Better isolation, clearer speaker identification
- Could use conference speakerphone devices (e.g., Jabra Speak) which have built-in recording
- Pros: Better audio quality, easier speaker attribution
- Cons: More hardware, more setup

**Option C: In-App Recording**
- All communication happens through the web app (text + voice)
- Voice calls recorded server-side
- Automatic transcription + speaker ID (built into the platform)
- Pros: Perfect attribution, automatic, no hardware beyond laptops
- Cons: Requires voice feature built into app (significant dev), may feel unnatural for face-to-face interactions

**Recommendation:** Option B for physical interactions + Option C for digital communications. The web app captures all text messages and transactions automatically. Physical meetings use table mics. This gives us both channels.

### Reports Generation Pipeline

| Component | What | Status | Deadline |
|-----------|------|--------|----------|
| **Data capture** | All actions, transactions, budgets, military orders logged by engine | Built (engine event log) | Ready |
| **Audio transcription** | Meeting recordings → text | Needs solution (see above) | April 18 test |
| **Speaker attribution** | Who said what | Needs solution | April 18 test |
| **Behavioral analysis** | Decision patterns, negotiation style, leadership indicators | Needs design (DELPHI agent scope) | May 1 |
| **Report template** | Personal leadership report format | Needs design | April 25 |
| **Report generation** | AI-assisted analysis → per-participant report | Needs build | May 1 |
| **Report delivery** | PDF/web, sent within 48 hours post-SIM | Needs process | May 1 |

**Critical path:** The report is the PRODUCT. The SIM is the experience; the report is the takeaway. If we can't generate credible reports within 48 hours, the product isn't ready. This pipeline must be tested at the May 2-3 test.

---

## What Product Team Delivers (and when)

| Deliverable | Deadline | Status |
|-------------|----------|--------|
| SEED design complete (all checklist items) | **April 5** | ~80% done |
| Web app core (login, dashboard, map, budget, actions) | **April 15** | Not started |
| AI participants integrated | **April 15** | Architecture ready, integration needed |
| Facilitator dashboard | **April 15** | Not started |
| Communication system (in-app messaging) | **April 15** | Not started |
| Engine integration (web app ↔ Python engine) | **April 15** | Engine ready, API needed |
| Web app test | **April 18-19** | — |
| Bug fixes from web app test | **April 21-25** | — |
| Report template + generation pipeline | **April 25** | Not started |
| Recording/transcription integration | **April 25** | Needs solution decision |
| Full SIM test | **May 2-3** | — |
| Bug fixes + polish from full test | **May 5-15** | — |
| Production freeze | **May 20** | — |
| Pre-event materials (briefs, badges, etc.) | **May 20** | Templates ready, content needs generation |
| **LIVE SIM** | **May 26** | — |

---

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Web app not ready by April 18 | MEDIUM | HIGH | Can do April 18 test with simplified app (core flows only, skip polish). Worst case: paper playtest with engine running server-side. |
| Not enough participants by May 5 | MEDIUM | HIGH | Start recruitment NOW. Need 30 invitations for 25 confirmations. Personal outreach, not mass email. |
| Venue not available | LOW | HIGH | Book early. Have backup venue identified. |
| Sound recording doesn't work | MEDIUM | MEDIUM | Test at April 18. Have backup plan (smartphone recordings as fallback). |
| Reports can't be generated in 48h | HIGH | HIGH | Build a simple v1 report (data summary + key decisions) even if full AI analysis isn't ready. Something is better than nothing. |
| SIM too complex for first run | MEDIUM | MEDIUM | Prepare a "simplified mode" config: fewer rounds (6 not 8), fewer active mechanics, pre-built AI responses for edge cases. |
| AI participants behave unrealistically | MEDIUM | MEDIUM | Have facilitator override capability. Can manually intervene if AI does something bizarre. |

---

## Decision Log

| # | Decision | Options | Decided | Date |
|---|----------|---------|---------|------|
| 1 | Design review date | Tue Apr 1 / Thu Apr 3 | TBD (confirm Mon) | |
| 2 | Sound recording approach | A (room mics) / B (table mics) / C (in-app) | TBD | By Apr 10 |
| 3 | SIM format | Full day / 2-day | TBD | By Apr 15 |
| 4 | Web app test date | Sat Apr 18 / Sat Apr 19 | TBD | By Apr 7 |
| 5 | Full SIM test date | Sat May 2 / Sat May 3 / Fri May 1 | TBD | By Apr 15 |
| 6 | Venue | TBD | TBD | By Apr 20 |

---

*This plan is a living document until May 20 production freeze. Updated after each milestone.*
