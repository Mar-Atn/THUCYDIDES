# Time Structure
## Thucydides Trap SIM — SEED Specification
**Version:** 1.1 | **Date:** 2026-04-13 | **Updated:** BUILD reconciliation
**Canonical round flow:** `PHASES/UNMANNED_SPACECRAFT/CONTRACT_ROUND_FLOW.md`
**Detailed spec:** `3 DETAILED DESIGN/DET_ROUND_WORKFLOW.md` v2.0

---

## Core Parameters

| Parameter | Value |
|-----------|-------|
| **Rounds** | 6 to 8 (moderator decides; minimum 6, extend if dynamics warrant) |
| **Time per round** | 6 months of scenario time |
| **Scenario span** | H2 2026 → H1 2029 (6 rounds) or H2 2029 (8 rounds) |
| **Delivery format** | Two-day (recommended) or single-day (compressed) |

---

## Round Structure

Every round has **three phases:**

### Phase A — Free Actions + Regular Decisions (45–80 min manned, ~2-5 min unmanned)

The heart of the SIM. This is where 80% of the learning happens.

**A.1 Free Actions** (concurrent, real-time):

All actions route through the **Action Dispatcher** (`action_dispatcher.py`) for
immediate resolution. 25 action types across 6 categories:

- **Military:** ground/air/naval/bombardment attacks, missile launch, blockade, basing rights
- **Covert:** intelligence, sabotage, propaganda, election meddling (card-based)
- **Domestic:** arrest, martial law (one-off), reassign powers, lead protest, coup attempt, assassination
- **Political:** submit nomination, cast vote, call early elections, public statement
- **Transactions:** propose exchange, propose agreement (counterpart responds asynchronously)

Human participants act freely throughout the round. AI participants are asked **2 times
per round**, max **5 free actions total** per participant.

**A.2 Regular Decisions** (mandatory, per-country):

Budget allocations, tariff levels, sanctions positions, OPEC production. Submitted via
web app. If not submitted, previous round's settings continue.

### Phase B — Batch Processing (30 sec unmanned, 5-20 min manned with review)

No participant input during Phase B. The orchestrator runs 19 steps:

```
Step 0:    Apply regular decisions (tariff/sanction/OPEC changes)
Steps 1-11: Economic engine (oil → GDP → revenue → budget → production →
            tech → inflation → debt → crisis → momentum → contagion)
Step 12:   Stability per country
Step 13:   Political support per country
Step 14:   War tiredness
Step 15:   Revolution checks
Step 16:   Health events
Step 17:   Elections (scheduled + early_election_called flag)
Step 18:   Capitulation check
Step 19:   Persist all state to DB
```

In manned mode, a facilitator reviews results and may override before publishing.

### Inter-Round — Unit Movement Window (5-10 min)

**This is the ONLY time unit movement is submitted.** Both human and AI participants
reposition their forces on the map while Phase B results are processed/published.

AI participants are asked once for movement orders during this window.

---

## Dramatic Arc

### Act 1 — Setup (Rounds 1–2)

Establish the world. Form alliances. Set initial policies. First consequences visible.

| Round | Scenario Time | Phase A Length | Key Events |
|:-----:|:------------:|:-------------:|------------|
| **R1** | H2 2026 | 75–80 min | Opening org meetings (NATO, BRICS+). Opening statements (voluntary). Gulf Gate blockade active from start. |
| **R2** | H1 2027 | 70–75 min | **Columbia mid-term elections** (political checkpoint). OPEC+ meeting. G7 coordination. First sanctions/tariff consequences visible. |

**Pacing:** Longer rounds. Participants are learning the system and each other.

### Act 2 — Escalation (Rounds 3–4)

Consequences accumulate. Crises emerge. The Trap begins to close.

| Round | Scenario Time | Phase A Length | Key Events |
|:-----:|:------------:|:-------------:|------------|
| **R3** | H2 2027 | 60–65 min | **UNGA vote** — every country declares position publicly. BRICS+ summit (currency union?). First tech breakthroughs possible. Ruthenia wartime election. |
| **R4** | H1 2028 | 55–60 min | NATO crisis session (if theater activated). EU emergency coordination. Pre-election maneuvering in Columbia. **Halfway point — extended world update.** |

**Pacing:** Moderate rounds. Participants know the system. Conversations more focused.

### Act 3 — Climax & Resolution (Rounds 5–6, optionally 7–8)

Maximum pressure. The Trap springs — or extraordinary leadership averts it.

| Round | Scenario Time | Phase A Length | Key Events |
|:-----:|:------------:|:-------------:|------------|
| **R5** | H2 2028 | 50–55 min | **Columbia presidential election** — THE climactic event. Candidates: Volt (current), Anchor, Challenger. All participants watch speeches. |
| **R6** | H1 2029 | 45–50 min | New/re-elected president's first moves. Final state of alliances, wars, economies. **Moderator decides: end here or continue?** |
| **R7** | H2 2029 | 45 min | (If played) Extended consequences. Does the new order hold? |
| **R8** | H1 2030 | 40 min | (If played) Final round. Long-term trajectories established. |

**Pacing:** Compressed rounds. Less time to think. More pressure to act. The compression itself is a teaching tool — participants experience how crises accelerate beyond leaders' ability to deliberate.

---

## Two-Day Format (Recommended)

### Day 1

| Time | Duration | Activity |
|------|----------|----------|
| 9:00–9:45 | 45 min | Check-in. World briefing, rules, role distribution |
| 9:45–10:15 | 30 min | Read briefs, set personal goals |
| 10:15–11:45 | 90 min | **Round 1** (80 min action + 10 min submit) |
| 11:45–12:00 | 15 min | World update R1 |
| 12:00–13:25 | 85 min | **Round 2** (75 min action + 10 min submit) |
| 13:25–13:40 | 15 min | World update R2 (includes mid-term results) |
| 13:40–14:30 | 50 min | Lunch (stay in role — the lunch table is a negotiation venue) |
| 14:30–15:50 | 80 min | **Round 3** (65 min action + UNGA vote) |
| 15:50–16:05 | 15 min | World update R3 |
| 16:05–16:20 | 15 min | Break |
| 16:20–17:35 | 75 min | **Round 4** (60 min action) |
| 17:35–17:50 | 15 min | Extended world update R4 — "state of the world at the halfway point" |
| 17:50–18:00 | 10 min | Press conference / recap / set up overnight dynamics |
| 18:00 | | **SIM PAUSES — stay in role until tomorrow** |

**Day 1: Rounds 1–4 completed. ~8.5 hours.**

### Overnight

The SIM does NOT stop. Participants remain in role:
- Secret communications via any channel (messages, notes, in person)
- Coup/conspiracy coordination
- Back-channel peace negotiations
- Press publishes evening/morning edition
- Moderator may introduce overnight events ("happened overnight")
- Exhausted leaders make promises they might regret in the morning

### Day 2

| Time | Duration | Activity |
|------|----------|----------|
| 9:00–9:15 | 15 min | Check-in. Overnight events announced. |
| 9:15–10:25 | 70 min | **Round 5** (55 min action + presidential election) |
| 10:25–10:40 | 15 min | Extended world update R5 (election results — seismic moment) |
| 10:40–11:35 | 55 min | **Round 6** (45 min action) |
| 11:35–11:50 | 15 min | World update R6 |
| 11:50–12:00 | 10 min | Moderator decision: continue to R7–8, or end? |

**If ending at R6:** Final state announced → decompress → 60 min debrief → end ~14:15.

**If continuing to R7–8:** Lunch → R7 (45 min) → R8 (40 min) → final state → decompress → debrief → end ~16:00.

**Total two-day program: ~14–16 hours active SIM + overnight immersion.**

---

## Single-Day Format (Compressed)

6 rounds in ~11.5 hours. Loses overnight scheming, processing time, and R7–8 possibility.

| Time | Duration | Activity |
|------|----------|----------|
| 8:30–9:00 | 30 min | Check-in |
| 9:00–9:45 | 45 min | Briefing, rules, role distribution, Q&A |
| 9:45–10:05 | 20 min | Read briefs |
| 10:05–11:30 | 85 min | **Round 1** |
| 11:30–11:40 | 10 min | World update R1 |
| 11:40–12:55 | 75 min | **Round 2** |
| 12:55–13:05 | 10 min | World update R2 |
| 13:05–13:50 | 45 min | Lunch (in role) |
| 13:50–15:00 | 70 min | **Round 3** |
| 15:00–15:10 | 10 min | World update R3 |
| 15:10–16:15 | 65 min | **Round 4** |
| 16:15–16:30 | 15 min | Extended world update R4 + break |
| 16:30–17:30 | 60 min | **Round 5** (+ election) |
| 17:30–17:45 | 15 min | World update R5 |
| 17:45–18:35 | 50 min | **Round 6 — FINAL** |
| 18:35–18:50 | 15 min | Final state. SIM ENDS. |
| 18:50–19:50 | 60 min | Decompress + debrief |

---

## Scheduled Events by Scenario Time

Events are anchored to scenario time, not round number.

| Scenario Time | Round | Event | Type |
|:-------------:|:-----:|-------|------|
| H2 2026 | R1 | NATO summit, BRICS+ opening, org meetings | Scheduled |
| H1 2027 | R2 | **Columbia mid-term elections** | Political clock |
| H2 2027 | R3 | **UNGA vote** — all countries declare positions | Forcing function |
| H2 2027 | R3 | **Ruthenia wartime election** (Beacon/Bulwark/Broker) | Political clock |
| H1 2028 | R4 | NATO crisis session (if theater active). Pre-election maneuvering. | Conditional |
| H2 2028 | R5 | **Columbia presidential election** (Volt/Anchor/Challenger) | THE climax |
| H1 2029 | R6 | New president's first moves. Resolution or continuation. | Denouement |

---

## Moderator Flexibility

| The moderator CAN... | But should NOT... |
|----------------------|-------------------|
| Extend a round by 10–15 min for breakthrough negotiations | Add extra rounds beyond 8 |
| Call submissions early if a round feels exhausted | Cut a round short during active crisis |
| Introduce overnight events (Day 2 format) | Script outcomes or override participant decisions |
| Decide to end at R6 or continue to R7–8 | End before R5 (must reach presidential election) |
| Adjust round length based on energy | Make all rounds the same length |

---

## Connection to Engines

| Engine | When it runs | Duration |
|--------|:----------:|:--------:|
| **Action Dispatcher** | Phase A — routes all 25 action types to engines | Real-time |
| **Combat Engines** | Phase A — ground/air/naval/bombardment/missile/nuclear | Immediate per action |
| **Covert Ops Engines** | Phase A — intelligence/sabotage/propaganda/election meddling | Immediate per action |
| **Transaction Engine** | Phase A — propose/respond/execute | Immediate per action |
| **Batch Orchestrator** | Phase B — Steps 0-19 (economic → political → elections) | 30 sec - 5 min |
| **Movement Engine** | Inter-Round — unit repositioning | Immediate per batch |

---

*The time structure creates a dramatic arc through compression: early rounds give time to think, late rounds force action under pressure. The presidential election at R5 is the structural climax by design — everything builds toward it.*
