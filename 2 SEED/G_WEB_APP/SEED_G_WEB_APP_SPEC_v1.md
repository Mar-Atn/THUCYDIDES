# Web App Specification
## Thucydides Trap SIM — SEED Specification
**Version:** 2.0 | **Date:** 2026-03-30 | **Status:** DRAFT
**Architecture:** `CON_G1_WEB_APP_ARCHITECTURE_v2.frozen.md`
**Visual design:** `SEED_H1_UX_STYLE_v2.md`
**Data architecture:** `SEED_F3_DATA_FLOWS_v1.md` + `SEED_F4_API_CONTRACTS_v1.md`

---

# PART 1 — CONCEPTUAL VIEW (one page)

## What the app does

Four interfaces, one database, real-time sync.

```
PARTICIPANTS (25-39 humans)     →  See their situation, take actions, talk to AI
FACILITATOR (1-2 moderators)    →  See everything, control the game, override if needed
PUBLIC DISPLAY (room screens)   →  Show the world to everyone — the "CNN broadcast"
AI PARTICIPANTS (10 agents)     →  Same rights as humans, different interface (API)
ARGUS (AI assistant)            →  Personal mentor for each human participant
```

**Human-to-human communication happens FACE TO FACE in the room.** The app handles only: AI participant meetings, Argus conversations, team channels, and public broadcasts. Everything else is physical — that's the point of an immersive SIM.

## Participant's interface — conceptual

```
FIXED REFERENCE (always accessible)
├── Role brief (bio, connections, interests, artefacts)
├── Country brief (with artefacts — e.g. Western Treaty Article 5)
├── World context (short)
├── Schedule (with events marked: "UNGA R3 — you are a member")
└── Main rules

ARGUS (always accessible)
└── Voice/text AI assistant — rules, strategy, reflection

CURRENT INFORMATION (updated each round + real-time for actions)
├── Personal
│   ├── Assets (coins, technologies, units under your authority)
│   ├── Positions & memberships (can change — fired, elected, arrested)
│   ├── Intelligence log (received reports, if any)
│   └── Action/transaction history (your past moves)
├── Country (dashboard filtered by your access rights)
│   ├── Economic indicators (full for PM/leader, summary for others)
│   ├── Military status (full for military chief, summary for others)
│   ├── Political status (stability, support, elections)
│   ├── Assets (treasury, units, tech levels)
│   └── Signed agreements (past + new)
└── World (public — same for everyone)
    ├── Map with military units (and history)
    ├── News/Events log + announcements
    ├── Upcoming events ("UNSC at 10:20 — you are a member")
    └── Global dashboard (GDPs, oil price, markets — focused on the Trap)

ACTIONS (what you CAN do — filtered by role powers + current state)
├── Regular inputs (once per round, deadline)
│   ├── #1 Budget allocation (maintenance shown first, then discretionary split)
│   ├── #2 Oil production level (5 levels: Min/Low/Normal/High/Max — OPEC+ only)
│   ├── #3 Tariff settings (default = all sectors, expandable to per-sector)
│   ├── #4 Sanctions settings (per target country, S-curve effectiveness)
│   ├── #5 Mobilization (finite depletable pool — never recovers)
│   └── #6 Militia call (homeland under attack only — 1-3 units, 0.5× combat)
├── Military actions (anytime Phase A — moderator present for combat)
│   ├── #7 Ground attack (dice-based, both commanders present, modifiers hidden)
│   ├── #8 Blockade (ground forces on shore, Full/Partial levels)
│   ├── #9 Naval combat (ship vs ship — RISK dice at sea, sunk = embarked units lost)
│   ├── #10 Naval bombardment (10% per ship, safe, slow)
│   ├── #11 Air strike (AD interception, 15% hit per survivor)
│   ├── #12 Strategic missile / nuclear (5-tier, 10-min authorization clock)
│   └── #13 Troop deployment (Phase B)
├── Intelligence / covert (anytime Phase A — limited pools)
│   ├── #14 Intelligence request (per-individual pool, always returns answer)
│   ├── #15 Sabotage (2-3 cards per game, 40% base success)
│   ├── #16 Cyber attack (2-3 cards, 50% base, low impact)
│   ├── #17 Disinformation (2-3 cards, 55% base, hardest to trace)
│   └── #18 Election meddling (1 card per game, 2-5% impact)
├── Political actions (anytime Phase A)
│   ├── #19 Arrest (moderator present, target out of play until released)
│   ├── #20 Fire / reassign (moderator present, immediate power loss)
│   ├── #21 Propaganda (coins for support boost, diminishing returns)
│   ├── #22 Assassination (1 card per game, probability-based)
│   ├── #23 Coup attempt (2 roles conspire, betrayal possible)
│   ├── #24 Protest (automatic + stimulated card option)
│   └── #25 Impeachment (Columbia/Heartland only, parliament votes)
├── Transactions (anytime, bilateral, irreversible)
│   ├── #26 Trade (coins, units, tech, basing rights — country or personal)
│   ├── #27 Agreement (armistice, peace, alliance, custom — free text)
│   └── #28 New organization (2+ countries, public event)
└── Communication
    ├── #29 Public statement (via moderator, physical speech)
    ├── #30 Call organization meeting (physical meeting, app notifies)
    └── #31 Nominate for election (10 min before election)

COMMUNICATION (minimal — humans talk face to face)
├── Request/accept meeting with AI participant (voice or text)
├── Country team channel (digital, for coordination)
└── Receive public broadcasts (moderator announcements)
```

## Facilitator's interface — conceptual

```
INFORMATION (everything, unfiltered)
├── God-view map (all forces, all territory — no information asymmetry)
├── All-countries dashboard (every indicator for every country)
├── Round & phase status (timer, submissions, pending authorizations)
├── Engine status (processing, results, coherence flags, expert panel)
├── AI participant status (per agent: activity, queue, cognitive state)
├── Argus status (per participant: intro complete? active session? outro done?)
├── Alert feed (crisis imminent, nuclear launch, missing submissions, AI errors)
└── Communication monitor (can read any channel, join any meeting)

CONTROLS
├── Round management (start, extend, end, deploy window, next round)
├── World Model Engine (trigger, review output, adjust values, approve & publish)
├── Overrides (adjust any state, cancel action, override dice, inject event, broadcast)
├── AI management (pause/resume, view cognitive state, override action, switch model)
├── Live Action support (dice input, authorization clock, combat resolution, court verdicts)
└── Participant management (assign roles, view any screen)
```

## Public display — conceptual

```
READ-ONLY (public data only, readable from 5 meters)
├── Global map (territories, theaters, chokepoints, public forces)
├── Key indicators (oil price, active wars, election countdown, nuclear threat level)
├── News ticker (treaties, speeches, combat, elections, announcements)
├── Round clock (round number, scenario date, phase, countdown timer)
└── Display modes (standard, map focus, event focus — facilitator controls)
```

## AI participant interface — conceptual

```
NOT A SCREEN — an API (Module Interface Protocol)

RECEIVES (from SIM)          SENDS (to SIM)
├── World state update       ├── Action submissions (same as human actions)
├── Event notifications      ├── Messages / meeting requests
├── Action menu              └── Status updates
└── Incoming messages

Same rights, same constraints as human in the same role.
Defined in: CON_F1 + E2 + F4
```

---

# PART 2 — DETAILED SPECIFICATION

---

# G2: PARTICIPANT INTERFACE

## Who uses it

25-39 human participants, each assigned one role. Primary device: mobile phone (participants walk around the room for face-to-face meetings). Secondary: tablet or desktop.

---

## FIXED REFERENCE

Available from check-in through debrief. The participant's reference shelf — always one tap away.

### REF-1. Role Brief

| Content | Source |
|---------|--------|
| Character name, title, age | B2 role seed |
| Country and team composition | B1 country seed + role assignments |
| Personality and factional alignment | B2 Section 2 |
| Objectives and ticking clocks | B2 Section 3 |
| Powers and action rights | B2 Section 4 |
| Key relationships (from B3 — this role's slice) | B3 relationship matrix |
| Role-specific artefacts | Role pack (intel reports, cables, letters — per H3 templates) |

**Classification:** ROLE — eyes only. Each participant sees only their own brief.

### REF-2. Country Brief

| Content | Source |
|---------|--------|
| Country overview (2-3 paragraphs) | B1 country seed |
| Starting situation (economic, military, political) | B1 + C4 data |
| Key bilateral relationships | B1 Section 4 |
| Team roster (character names + titles — not who's playing them) | Role assignments |
| Country-level artefacts (e.g., Western Treaty text, OPEC+ charter) | Role pack |

**Classification:** COUNTRY — shared within the team.

### REF-3. World Context

| Content | Source |
|---------|--------|
| The opening briefing (~1200 words) | A3 World Context Narrative |

**Classification:** PUBLIC — all participants receive the same text.

### REF-4. Schedule

| Content | Source |
|---------|--------|
| Day schedule with round times | C7 Time Structure |
| Scheduled events with round anchors | C7 scheduled events table |
| **"You are invited" indicators** | Cross-referenced with role's org memberships |

Example: "R3 — UNGA Vote (you are a member)" or "R5 — Columbia Presidential Election (you are a candidate)"

### REF-5. Main Rules

| Content | Source |
|---------|--------|
| Quick-reference rules card | Derived from C5, C6, C7, engine docs |
| How to submit budget | Action guide |
| How transactions work | C6 + transaction engine |
| How combat works (high level) | Live action engine summary |
| Authorization chain for this role | B2 Section 4 powers |

---

## ARGUS (AI Assistant)

Persistent button on the interface. Available during check-in, Phase A, and debrief.

| Property | Value |
|----------|-------|
| Access | "Talk to Argus" button, always visible |
| Mode | Voice (primary), text (fallback) |
| Phases | INTRO (goal-setting), MID (advisory), OUTRO (reflection) |
| Memory | Remembers ALL previous conversations with this participant |
| Boundary | Cannot send messages to other participants. Cannot reveal classified data. |
| Spec | `SEED_E4_ARGUS_PROMPTS_v1.md` |

---

## CURRENT INFORMATION

### PERSONAL

#### P1. Personal Assets

| Field | Source | Update |
|-------|--------|--------|
| Personal coins | Role state | Real-time (transactions) |
| Technologies under personal authority (if any) | Role state | Per round |
| Units under personal command (if military chief) | Deployments filtered by role | Real-time |

#### P2. Personal Position & Memberships

| Field | Source | Update |
|-------|--------|--------|
| Current title/position | Role state | Real-time (can change: fired, elected, arrested, killed) |
| Organization memberships | Org membership table | Real-time (can join/leave) |
| Alive / arrested / in office status | Role state | Real-time |

#### P3. Intelligence Log

| Field | Source | Update |
|-------|--------|--------|
| Received intelligence reports | Covert op results (where this role is recipient) | Real-time |
| Classified briefings received | Facilitator-injected intelligence | Real-time |

Only visible to roles with intelligence access. Most participants see nothing here.

#### P4. Action & Transaction History

| Field | Source | Update |
|-------|--------|--------|
| Log of all actions this participant initiated or participated in | Events log (filtered by role) | Real-time |
| Log of all transactions (proposed, confirmed, rejected) | Transaction log (filtered) | Real-time |

### COUNTRY (role-filtered dashboard)

One master dashboard exists per country. Each team member sees the sections relevant to their access rights.

#### FULL COUNTRY DASHBOARD (assembled, then filtered)

| Section | Fields | Full access | Summary access |
|---------|--------|:-----------:|:--------------:|
| **Economic** | GDP, growth rate, treasury, revenue projection, inflation, debt, trade balance, market index, crisis state | PM, Head of State | All team |
| **Military** | Unit counts (5 types), deployments on map, production queue, basing rights hosted/received | Military Chief, Head of State | All team (counts only) |
| **Political** | Stability, support, war tiredness, election status, dem/rep split (Columbia), approval rating | Head of State, all team | All team |
| **Technology** | Nuclear level + progress, AI level + progress, R&D investment | Head of State, Tech chief | All team (levels only) |
| **Treasury detail** | Revenue breakdown, spending breakdown, debt service, budget execution | PM, Head of State | Summary to all |

**Key principle:** The dashboard is ONE thing. Access rights FILTER it. A military chief sees full military + summary economic. A PM sees full economic + summary military. Head of state sees everything.

#### C1. Country Assets

| Field | Source | Update |
|-------|--------|--------|
| Treasury (coins) | World state | Real-time (transactions change it) |
| Military units (by type, by zone) | World state + deployments | Real-time |
| Technology levels | World state | Per round |
| Nuclear status | World state | Per round |

#### C2. Signed Agreements

| Field | Source | Update |
|-------|--------|--------|
| Active treaties and agreements (with full text) | Treaties table | Real-time |
| Active basing rights (given and received) | Basing rights table | Real-time |
| Organization memberships | Org membership table | Real-time |

### WORLD (public — same for everyone)

#### W1. World Map

Interactive hex map showing:
- Country territories (muted colors)
- Own unit positions (exact)
- Adjacent zone forces (visible — approximate)
- Distant forces (hidden unless intelligence)
- Active theaters (highlighted)
- Chokepoints (status markers: open / contested / blocked)
- Occupied territory (stripes)
- History mode: toggle to see previous rounds' positions

#### W2. News / Events / Announcements

Chronological feed of public events:
- Combat outcomes (publicly visible)
- Treaty signings and announcements
- Election results
- Organization meeting outcomes
- Moderator announcements
- Facilitator-injected events

Each entry: round + timestamp + attribution + one-line summary.

#### W3. Upcoming Events

| Field | Source |
|-------|--------|
| Scheduled events for current and next round | C7 scheduled events |
| **"You are invited / you are a member"** indicator | Role's org memberships |
| Event time (if scheduled) | Facilitator schedule |

Example display:
```
R3 — UNGA Vote .............. YOU ARE A MEMBER
R3 — Heartland Election ..... Observer
R5 — Columbia Presidential ... YOU ARE A CANDIDATE
```

#### W4. Global Dashboard

Key world indicators — focused on the Trap dynamics:

| Indicator | Format |
|-----------|--------|
| Columbia GDP vs Cathay GDP (bar comparison) | Two bars, relative scale |
| Global oil price | Number + trend |
| Columbia naval vs Cathay naval | Number vs number + trend arrows |
| Active wars (count + list) | Compact list |
| Columbia election countdown | "X rounds" |
| Nuclear threat level | None / Elevated / Active |
| BRICS+ currency status | Not adopted / Under discussion / Active *(tracked via Special Action: BRICS+ currency support declarations from member states)* |
| Chokepoint status (3) | Icons: open / blocked |

---

## ACTIONS

### What appears here

A dynamic list of AVAILABLE actions for this specific role, given the current game state. Actions that this role cannot perform do not appear. Actions that require co-authorization show the authorization chain status.

**31 total actions** organized in 6 categories: Regular Inputs (6), Military (7), Intelligence/Covert (5), Political (7), Transactions (3), Communication (3).

---

### REGULAR INPUTS (once per round — deadline: end of Phase A)

Submitted via forms. If not submitted by deadline, previous round's settings continue.

#### #1. Budget Allocation

**Authorization:** PM or Head of State

**Budget screen layout:**
```
REVENUE THIS ROUND:            67.0 coins  (GDP × tax rate)
MAINTENANCE (fixed, mandatory): -11.2 coins  (all units × maintenance cost)
───────────────────────────────
DISCRETIONARY BUDGET:           55.8 coins  ← split this across buckets
```

| Bucket | Input | Notes |
|--------|-------|-------|
| Social spending % | Slider or number | Below baseline (30%) = stability risk |
| Ground production % | Slider or number | Cost per unit + capacity shown |
| Naval production % | Slider or number | Cost per unit + capacity shown |
| Tactical air production % | Slider or number | Cost per unit + capacity shown |
| Tech R&D % | Slider or number + track selector + speed | See detail below |
| Reserves % | Slider or number | Added to treasury |
| **Total** | Auto-calculated | **Must = 100%** |

**Tech R&D detail:**
- Choose track: Nuclear OR AI (one per round)
- Choose speed: Normal (1x cost), Accelerated (2x cost, 2x progress), Maximum (3x cost, 3x progress)
- Breakthrough threshold is HIDDEN — participants see progress % but don't know the exact level-up point
- **AI private investment (hidden mechanic):** For AI track only, private sector automatically matches government investment 1:1 — effectively doubling progress speed. NOT displayed to the investing country. Others can discover via intelligence.

#### #2. Oil Production (OPEC+ members only)

| Field | Input |
|-------|-------|
| Production level | Min / Low / Normal / High / Max (5 levels) |
| **Authorization** | Head of State |

Prisoner's dilemma: restriction can backfire if others produce more. Demand destruction at high prices limits restriction efficiency.

#### #3. Tariff Settings

| Field | Input |
|-------|-------|
| Default mode | One tariff level for all 4 sectors per target country: 0 (free) / 1 / 2 / 3 |
| Expanded mode (optional) | Per-sector: Resources / Industry / Services / Technology — each 0-3 |
| **Authorization** | Head of State |

Engine accepts per-sector input with sector weights.

#### #4. Sanctions Settings

| Field | Input |
|-------|-------|
| Per target country | Level 0 (none) / 1 / 2 / 3 |
| **Authorization** | Head of State |

**Effectiveness:** S-curve — coverage 0.3=10%, 0.5=20%, 0.7=60%, 0.9=90%. Coverage = weighted by GDP share x sanctions level / 3. Imposer pays cost based on bilateral trade weight. Coalition matters: West alone = modest; add swing states = serious; Cathay joins = devastating.

#### #5. Mobilization

| Field | Input |
|-------|-------|
| Level | None / Partial / Full |
| **Authorization** | Head of State |

**Finite depletable pool.** Each country has a fixed mobilization pool that NEVER recovers. Partial = half remaining pool. Full = all remaining pool. Heartland and Nordostan start partially mobilized.

**Stability cost varies by context:**

| Situation | Cost |
|-----------|------|
| Democracy at peace | -1.5 |
| Democracy at war | -0.5 |
| Autocracy | -0.3 |
| Under invasion | -0.2 |

Columbia mobilization: parliament approval stated (no mechanic — just narrative).

#### #6. Militia / Volunteer Call (homeland under attack only)

| Field | Input |
|-------|-------|
| Activate | Yes / No |
| **Eligibility** | Countries whose home territory is under attack or invasion |
| **Effect** | 1-3 militia units, 0.5x combat effectiveness |
| **Cost** | Minor stability cost |
| **Authorization** | Head of State |

---

### MILITARY ACTIONS (anytime during Phase A)

All combat actions require moderator present. Both commanders available real-time for combat resolution.

#### #7. Ground Attack — LIVE ACTION

**Authorization:** Head of State + Military Chief (both sides present + moderator)

| Element | Detail |
|---------|--------|
| Visibility | NO fog of war — all units visible. Modifiers HIDDEN until after roll. |
| Dice | Real dice or app dice. Both sides roll. Moderator inputs results. |
| Win condition | Attacker needs >= defender roll + 1 to win. Ties = defender holds. |

**Modifiers (integers only):**

| Modifier | Value | Condition |
|----------|-------|-----------|
| AI L4 technology | +0 or +1 | Random, determined once when L4 reached |
| Low morale | -1 | Stability <= 3 |
| Die Hard | +1 defender | Always applies to defender |
| Amphibious | -1 attacker | Attacking from ship to land |
| Air support | +1 defender | Binary yes/no (defender has air in zone) |
| Fatherland appeal | +1 one-time | 60% success, delayed risk 2 rounds later |

**Ships:** Carry 1 ground unit + up to 5 air units. Transport between rounds. Can attack adjacent land from ship (amphibious -1 applies).

#### #8. Blockade

**Authorization:** Head of State + Military Chief

| Element | Detail |
|---------|--------|
| Mechanism | GROUND FORCES on the shore blockade a chokepoint (not naval superiority) |
| Levels | Full or Partial |
| Formosa special | Partial = Strait only. Full = 3+ sea zones around island. |

**Breaking a blockade:**
- Destroy ALL military units at chokepoint, OR blocker lifts voluntarily
- Formosa partial deblocking: 1 friendly ship arriving at any adjacent zone = instant downgrade to partial (ship presence only, no combat)

#### #9. Naval Bombardment

**Authorization:** Head of State + Military Chief

| Element | Detail |
|---------|--------|
| Effect | 10% attrition per ship per round |
| Risk | Safe (no return fire) |
| Use | Slow preparation tool — softens before ground assault |

#### #10. Air Strike

**Authorization:** Head of State + Military Chief

| Element | Detail |
|---------|--------|
| AD interception | Degrading probability per interceptor. Air units destroyed if intercepted. |
| Hit rate | 15% per surviving aircraft |
| Airfield vulnerability | Can target airfields to destroy grounded aircraft |
| Carrier ops | Air can operate from carriers (ships) |

Full system per D8 Part 6C.

#### #11. Strategic Missile / Nuclear — SPECIAL MODE

**5-tier escalation system:**

| Tier | Action | Detection |
|------|--------|-----------|
| 1 | Subsurface nuclear test | AI L3+ countries detect |
| 2 | Open nuclear test | Everyone detects |
| 3 | Conventional missile strike | AI L2+ countries detect launch |
| 4 | Single nuclear strike | AI L2+ countries detect launch |
| 5 | Massive nuclear strike | AI L2+ countries detect launch |

**Authorization (country-specific):**

| Country | Required authorization |
|---------|-----------------------|
| Columbia | Dealer + Shield + Anchor (3-person) |
| Cathay | Helmsman + Rampart + Sage (3-person) |
| Europe | HoS + AI gate |
| Nordostan | Pathfinder + Ironhand (2-person) |
| Choson / Persia / Levantia | HoS alone |

**Procedure:**
1. Authorization submitted → 10-minute authorization clock starts (SIM enters special mode)
2. Launch → 10-minute flight time
3. Nuclear vs. conventional unknown until impact — nobody knows during flight
4. Response options during flight: intercept (coalition AD), counter-launch, massive counter-attack, do nothing

#### #12. Nuclear Test

Covered by #11 (tiers 1-2). Separate submission, same authorization chain.

#### #13. Troop Deployment (Phase B)

Available during Phase B. Production runs FIRST (instant), so new units are immediately available. Deployment window stays open while World Model Engine processes in parallel.

| Field | Input |
|-------|-------|
| Unit to move | Select from available units (produced, mobilized, arrived) |
| Destination | Select zone on map |
| **Rules** | Ships: any unblocked sea zone globally. Ground: own territory or allied territory (military alliance = default permission; otherwise basing rights needed). Transit to foreign theater = 1 round delay. |
| **Authorization** | Military Chief or Head of State |

No combat during deployment. Movements finalize when the window closes.

---

### INTELLIGENCE / COVERT ACTIONS (anytime during Phase A — limited pools)

Each covert action type draws from a SEPARATE limited pool. Pool sizes vary by role.

#### #14. Intelligence Request

| Element | Detail |
|---------|--------|
| Pool | Per INDIVIDUAL (not per country). Intel chief: 6-8, HoS: 3-4, military: 2-3, others with access: 1-2 |
| Who can use | ANY role with intelligence access (not just HoS/intel chief) |
| Input | Question (free text) + target |
| Result | Always returns an answer (never "failed, no info"). Arrives in 5-10 min as styled classified artefact. |
| **Authorization** | Self (any role with intelligence pool) |

**Accuracy varies by question type:**

| Question type | Accuracy |
|---------------|----------|
| Hard facts (unit counts, GDP) | 85-90% |
| Diplomatic secrets (agreements, deals) | 70% |
| Intentions (what will they do next) | 50-60% |
| Aggressive / impractical questions | 40% |

Wrong answers look identical to right ones. Cross-checking same question from different services recommended. Intelligence can be traded as a service (pay someone to use their requests).

#### #15. Sabotage

| Element | Detail |
|---------|--------|
| Pool | 2-3 cards per game per eligible role (separate from intelligence) |
| Target type | Military / Economic / Technology |
| Resolution | Success/failure only — 40% base + AI tech bonus + intel chief bonus |
| Reveal | Results appear publicly at Phase B world update (no attribution) |
| **Authorization** | Intel Chief or Head of State |

Attribution hidden unless discovered through intelligence or leak.

#### #16. Cyber Attack

| Element | Detail |
|---------|--------|
| Pool | 2-3 cards per game (separate pool) |
| Effects | Steal coins / reduce military production / undermine GDP (-1%) |
| Resolution | 50% base success. AI tech level critical. |
| Impact | Low — scarce cards, modest effects |
| **Authorization** | Intel Chief or Head of State |

#### #17. Disinformation

| Element | Detail |
|---------|--------|
| Pool | 2-3 cards per game (separate pool) |
| Target | Political support -3%, stability -0.3 |
| Resolution | 55% base success (easiest covert op) |
| Attribution | Very hard to trace (~60% accuracy even with investigation) |
| **Authorization** | Intel Chief or Head of State |

#### #18. Election Meddling

| Element | Detail |
|---------|--------|
| Pool | 1 card per game |
| Input | Target country + who to support/work against |
| Effect | 2-5% impact on support/attitude. Works with or without active election. |
| Risk | Exposure damages the candidate you tried to help |
| **Authorization** | Intel Chief or Head of State |

---

### POLITICAL ACTIONS (anytime during Phase A)

#### #19. Arrest

**Authorization:** Head of State. **Moderator must be present.**

| Element | Detail |
|---------|--------|
| Procedure | Order in app, moderator executes physically |
| Effect | Target immediately out of play until released |
| Cost | None (no stability or support cost) |
| Democracy | AI Court reviews between rounds (see Court mechanic below) |
| Autocracy | Indefinite, no court review |

#### #20. Fire / Reassign

**Authorization:** Head of State. **Moderator must be present.**

| Element | Detail |
|---------|--------|
| Effect | Immediate loss of role powers. Person stays in play. |
| Columbia | Parliament must confirm. Can block. "Acting" status if blocked. |
| Cost | None (no stability or support cost) |

#### #21. Propaganda Campaign

**Authorization:** Head of State

| Element | Detail |
|---------|--------|
| Input | Spend coins |
| Effect | 1 coin = +2-3% support, up to +10% cap. Diminishing returns with repeated use (oversaturation). |
| AI bonus | AI L3+ gets 50% more effectiveness |

#### #22. Assassination Attempt

**Authorization:** Head of State or Intel Chief. **1 card per game per eligible role.**

| Target | Hit probability |
|--------|----------------|
| Domestic | 60% |
| International (default) | 20% |
| International (Levantia) | 50% |
| International (Nordostan) | 30% |

Hit = 50/50 kill or survive (injured + martyr effect). No AI or intel modifiers — raw probability. International: higher chance of being revealed if failed.

#### #23. Coup Attempt

**Authorization:** Any two roles within same country.

| Step | Detail |
|------|--------|
| 1. Initiate | Initiator names co-conspirator in app |
| 2. Window | Co-conspirator has 5 minutes to respond |
| 3. Response | Accept / Reject silently / BETRAY (initiator arrested immediately) |
| 4. If both accept | Probability check: base 15% + active protest +25% + low stability bonus + low support bonus |
| 5. Failed | Both exposed. Ruler and world learn. |

Trust mechanic IS the game.

#### #24. Protest

| Element | Detail |
|---------|--------|
| Trigger | Automatic (engine checks conditions each round) OR stimulated (1-time card: +20% probability next round) |
| Effect by support level | >60%: fizzle. 40-60%: modest (-0.5 stability). <40%: massive (-1.5 stability, +25% coup bonus) |
| Visibility | Public event |

#### #25. Impeachment

**Available to:** Columbia and Heartland only.

| Country | Procedure |
|---------|-----------|
| Columbia | Any parliament member initiates → parliament votes (real participants) |
| Heartland | Any team member initiates → 2 real votes needed + AI emulates remaining (loyal to president by default) |

Both sides submit positions. Takes 1 round. Removed leader stays in play, loses executive powers.

---

### TRANSACTIONS (anytime — bilateral, irreversible)

Both sides create and confirm. Super simple template.

**Transaction visibility tiers:**

| Type | Visibility | Who sees it |
|------|:----------:|-------------|
| Treaty / Agreement (public) | PUBLIC | All participants + news feed + public display |
| Organization creation | PUBLIC | All participants + news feed |
| Arms transfer | COUNTRY | Both country teams. Others learn only via intelligence or observation. |
| Coin transfer | COUNTRY | Both country teams. |
| Tech transfer | COUNTRY | Both country teams. |
| Basing rights | COUNTRY | Both country teams. Becomes PUBLIC when units are deployed (visible on map). |
| Personal transfer (coins between individuals) | ROLE | Only the two roles involved. |

#### #26. Trade

| Field | Input |
|-------|-------|
| Mode | Country transaction OR personal (individual) transaction |
| What you give | Coins / military units / technology / basing rights |
| What you receive | Coins / military units / technology / basing rights |
| Counterparty | Select role/country |
| Basing rights | Yes/no for entire country (not per zone) |
| **Confirmation** | Both parties confirm → instant execution |
| **Authorization** | HoS OR PM OR Secretary of State/Foreign Affairs |
| **Visibility** | Country mode: COUNTRY visibility. Personal mode: ROLE-ONLY visibility. |

Can be unilateral (send money, donate units) — just leave "receive" empty.

#### #27. Agreement

| Field | Input |
|-------|-------|
| Type | Armistice / Peace / Alliance / Trade Preference / Custom |
| Parties | Two or more countries |
| Text | Free text — whatever the parties agree to |
| Public/Private | Parties choose visibility |
| **Mechanical effect** | Armistice/Peace: ends active war. All others: stored, socially enforced. |
| **Authorization** | Head of State (all parties) |

#### #28. New Organization

| Field | Input |
|-------|-------|
| Name | Free text |
| Founding members | Two or more countries |
| Decision rule | Consensus / Majority / Custom |
| Purpose | Free text |
| **Public event** | Announced to all. Join/leave/expel mechanics available after founding. |
| **Authorization** | Head of State (all founders) |

Org = communication channel + meeting structure, not independent power.

---

### COMMUNICATION (3 actions)

#### #29. Public Statement

| Element | Detail |
|---------|--------|
| Delivery | Via moderator ONLY. Physical speech in the room. |
| Recording | Transcribed and recorded by app |
| **Authorization** | Any role |

#### #30. Call Organization Meeting

| Element | Detail |
|---------|--------|
| Meeting | Physical meeting in the room |
| App role | Handles invitation/notification only |
| **Authorization** | Any org member |

#### #31. Nominate for Election

| Element | Detail |
|---------|--------|
| Timing | 10 minutes before election. Triggered by moderator. |
| Focus | Columbia presidential, some Heartland elections |
| **Authorization** | Eligible role per election rules |

---

### COURT MECHANIC (standard functionality for democracies)

The Court is an AI-adjudicated legal process available to all democratic countries. It is NOT an action — it is a response mechanism triggered by contested political actions.

**Use cases:** Arrest challenges, firing challenges, constitutional disputes, contract disputes, impeachment proceedings.

**Procedure:**

| Step | Detail |
|------|--------|
| 1. Complaint | Affected party submits complaint with arguments |
| 2. Response window | 10 minutes for the other side to respond |
| 3. Clarification | AI Court may ask clarifying questions |
| 4. Verdict | AI renders verdict based on constitutional framework |
| 5. Enforcement | Moderator enforces the verdict |

---

### CONTESTED AUTHORIZATION (Persia exception)

The Persia team has a unique authorization model reflecting the real power structure:

**Two independent military authorities:**
- **Furnace** (Supreme Leader) — constitutional commander-in-chief
- **Anvil** (IRGC Commander) — de facto operational commander, controls IRGC forces + Basij militia
- **Dawn** (President) — NO military authority

**How it works:**
- Both Furnace AND Anvil can independently authorize military actions for Persia
- Anvil can independently maintain/adjust the Gulf Gate blockade, call militia, and direct IRGC forces
- Furnace can independently order regular military actions and override Anvil's orders
- **If they give CONFLICTING orders** in the same round:
  - Both orders flagged as **CONTESTED** in the facilitator dashboard
  - Neither executes until resolved
  - Stability penalty (-0.5) for the visible internal split
  - Facilitator notified (alert)
  - Resolution: face-to-face negotiation between players, or facilitator mediation
- **Existing operations continue** unless someone orders them stopped (blockade persists by default)

This mechanic is UNIQUE to Persia. All other countries use standard co-authorization (Head of State + Military Chief must agree).

---

### SPECIAL ACTIONS (role-specific — appear only for eligible roles)

Actions that don't fit the generic templates above. These are the powers that define each role's unique gameplay identity. They appear in the Actions panel ONLY for the role that has them.

#### Political / Leadership Specials

| Action | Available to | Input | Effect |
|--------|-------------|-------|--------|
| **Endorse successor** | Head of State (Columbia Dealer) | Select candidate (Volt or Anchor) | Public endorsement. Affects R5 election AI scoring. Reversible (can switch endorsement). |
| **Call or delay elections** | Head of State (Heartland Beacon) | Call now / Delay 1 round | Triggers or postpones wartime election. Delay costs stability (-0.5) and support (-3%). Maximum 1 delay. |
| **Declare emergency / martial law** | Head of State (any) | Activate | Suspends parliament (where applicable). Enables total mobilization. Massive stability cost. Facilitator notified. |
| **Set military posture** | Head of State or Military Chief | Defensive / Balanced / Offensive | Affects AI expert panel assessment of military trajectory. Signals intent to allies and adversaries. |
| **Nominate candidate** | Eligible roles per election rules | Select candidate role | Registers for upcoming election (Columbia presidential, Heartland wartime). |

#### Strategic / Economic Specials

| Action | Available to | Input | Effect |
|--------|-------------|-------|--------|
| **BRICS+ currency support** | BRICS+ member Head of State | Support / Oppose / Abstain | Per-round declaration. Contributes to BRICS+ currency adoption vote at R3. Tracked as world state variable. |
| **Nuclear program initiation** | Head of State (non-nuclear countries) | Declare intent | One-time. Starts nuclear R&D at L0 with 0.0 progress. Creates public event. Diplomatic consequences. |
| **Vision 2030 investment** | Wellspring (Solaria) | % of budget | Diverts budget to diversification. Tracked as separate progress variable. Long-term GDP benefit. |
| **Rare earth restrictions** | Cathay Head of State (Helmsman) | Target country / level (0-3) | Restricts rare earth exports. Affects target's tech R&D progress. Already in engine. |
| **War posture escalation** | Head of State (non-belligerent) | Enter war on a side | One-time declaration. Creates war entry event. Commits country to a conflict. |

#### Persia-Specific Specials (see Contested Authorization above)

| Action | Available to | Input | Effect |
|--------|-------------|-------|--------|
| **Kingmaking** | Anvil (IRGC) | Support Furnace / Support Dawn / Neutral | Shifts internal power balance. Affects coup probability, succession, and external negotiation credibility. |
| **IRGC economic intervention** | Anvil | Direct IRGC funds to: military / sanctions evasion / regime stability | Allocates Anvil's personal coins (IRGC reserves) to specific purposes. Separate from state budget. |
| **Veto implementation** | Anvil | Block specific agreement/treaty | Anvil can block execution of agreements Furnace/Dawn signed. Creates political event (stability cost to both sides). |
| **Suppress / permit dissent** | Anvil | Suppress / Permit / Ignore | Affects Dawn's political support, street protest probability, and stability. |
| **Partial blockade adjustment** | Anvil | Full (100%) / Partial (50%) / Open (0%) | Adjusts Gulf Gate blockade intensity. Partial allows some traffic (reduces oil impact but maintains leverage). |

---

## COMMUNICATION

The app handles ONLY structured communication. Humans talk face to face.

| Channel | Purpose | How |
|---------|---------|-----|
| **AI meeting** | Request or accept a meeting with an AI participant. **AI can also initiate:** AI pushes meeting request notification to you — accept or decline. | Button: "Request meeting with [AI role]" or accept incoming AI request |
| **Team channel** | Country team coordination (digital backup to face-to-face) | Group chat, persistent, team members only |
| **Public broadcasts** | Receive moderator announcements | Read-only feed |
| **Argus** | Personal AI assistant | Separate from game comms (see above) |

**Everything else is physical.** Walk up to someone. Negotiate. Shake hands. Pass a note. That's the game.

---

# G3: FACILITATOR DASHBOARD

## Who uses it

1-2 moderators. Desktop with large screen. Command center for the entire SIM.

---

## INFORMATION (everything, unfiltered)

### F1. God-View Map
Full hex map with ALL deployments, ALL forces, ALL territory control. No information asymmetry. The facilitator sees the TRUE state of the world.

### F2. All-Countries Dashboard
Every country, every indicator. Sortable, filterable. Color-coded by crisis state (Normal / Stressed / Crisis / Collapse). Shows: GDP, treasury, stability, support, military summary, war status, AI/human indicator, budget submitted (yes/no).

### F3. Round & Phase Control Panel

| Field | Detail |
|-------|--------|
| Current round + phase | With phase timer (facilitator controls) |
| Submission tracker | Who submitted budget/tariffs/sanctions, who hasn't |
| Pending authorizations | Co-sign requests waiting (e.g., Shield hasn't approved attack) |
| **Contested orders (Persia)** | Conflicting military orders from Furnace vs. Anvil. Requires facilitator mediation. |
| **Nuclear authorization clock** | 10-minute countdown when strategic missile/nuclear action initiated |
| Action queue | Recent and pending actions from Live Action Engine |
| Transaction queue | Recent and pending transactions |
| **Court proceedings** | Active court cases, pending verdicts, enforcement required |

### F4. Engine Monitor

| Field | Detail |
|-------|--------|
| World Model Engine | Status: idle / processing / awaiting approval |
| Expert Panel results | Keynes, Clausewitz, Machiavelli assessments + synthesis |
| Coherence flags | Warnings, anomalies, out-of-range values |
| Processing log | Step-by-step engine output |

### F5. AI Participant Monitor

| Per AI agent | Detail |
|-------------|--------|
| Status | idle / busy / updating / error |
| Current activity | "Negotiating with Wellspring" / "Deliberating budget" |
| Queue depth | Pending perception updates |
| Recent actions | Last 5 actions taken with reasoning summary |
| Cognitive state | Block 4 (goals/strategy) — collapsible view |

### F6. Argus Monitor

| Per participant | Detail |
|----------------|--------|
| Intro | Goals covered Y/N, Rules Y/N, Strategy Y/N |
| Mid | Session count, currently active? |
| Outro | Complete Y/N, duration |

### F7. Alert Feed

Automatic flags:
- Stability < 4 (crisis imminent)
- Nuclear launch initiated (+ authorization clock countdown)
- Strategic missile in flight (+ flight time countdown)
- New theater activating
- Budget not submitted (5 min warning)
- AI participant error
- Participant hasn't completed Argus intro
- Coherence flag from engine
- War started or ended
- Court verdict pending enforcement
- Contested Persia orders awaiting mediation

### F8. Communication Monitor
Can read any team channel, any AI meeting transcript. Can join any AI meeting (listen-only). Full event log access.

---

## CONTROLS

### C1. Round Management

| Action | Effect |
|--------|--------|
| Start round | Opens Phase A, starts timer |
| Extend round (+N min) | Adds negotiation time |
| End round | Closes submissions, locks routine inputs. Auto-triggers production + opens deployment window. |
| Trigger World Model Engine | Starts world model processing (runs parallel to deployment) |
| Close Phase B / next round | Closes deployment window, advances to next round |

### C2. Engine Controls

| Action | Effect |
|--------|--------|
| Review engine output | See all calculated values before publication |
| Adjust any value | Override GDP, stability, oil price, etc. (logged) |
| Edit narrative | Modify AI-generated round briefing |
| Approve & publish | Commits new world state, pushes to all clients |

### C3. Override Controls

| Action | Effect |
|--------|--------|
| Adjust any country's state | Direct edit (logged with reason) |
| Cancel pending action | Block before resolution |
| Override dice result | Change combat/covert outcome before publication |
| Inject event | Create narrative event ("Breaking: earthquake in...") |
| Send broadcast | Public announcement to all participants + display |

### C4. AI Controls

| Action | Effect |
|--------|--------|
| Pause / resume any AI | Stop/start action loop |
| Adjust loop frequency | Slower/faster AI activity |
| View full cognitive state | All 4 blocks, any AI |
| View decision reasoning | Why AI made a specific choice |
| Override AI action | Block before execution |
| Inject information | Force AI to perceive something |
| Switch LLM model | Runtime model change |

### C5. Live Action Support

| Action | Effect |
|--------|--------|
| Input dice results | Enter both sides' dice rolls for ground combat |
| Start/stop authorization clock | 10-minute nuclear authorization timer |
| Court verdict input | Review and publish AI court verdicts |
| Mediate contested orders | Resolve Persia conflicting authorization |
| Execute arrest/fire | Physical enforcement of political actions |

### C6. Participant Management

| Action | Effect |
|--------|--------|
| Assign role | Link participant to character |
| Reassign role | Move participant |
| View participant's screen | See exactly what they see (support mode) |
| Generate printable materials | Role briefs, badges, signs |

---

# G4: PUBLIC DISPLAY

## What it is

Large screen(s) in the room. Read-only. Public data only. Readable from 5+ meters. The "CNN broadcast" of the simulation.

## Elements

### P1. Global Map
Country territories, active theaters, chokepoints (open/blocked), publicly visible military forces (aggregate, not exact), occupied territory.

### P2. Key Indicators

| Indicator | Format |
|-----------|--------|
| Oil price | Large number + trend arrow |
| Active wars | Count + list |
| Columbia election countdown | "X rounds" |
| Chokepoint status (3) | Open / Blocked icons |
| BRICS+ currency | Status label |
| Nuclear threat level | Icon: green / yellow / red |

### P3. News Ticker
Scrolling public events: treaties, speeches, combat, elections, announcements.

### P4. Round Clock
Round number ("ROUND 3"), scenario date ("H2 2027"), phase ("NEGOTIATION"), countdown timer (green → yellow → red).

### P5. Display Modes (facilitator-controlled)
Standard (all elements) / Map focus / Event focus (election results, war outcomes) / Indicators focus / Split screen.

---

# G5: COMMUNICATION SYSTEM

## Design principle

**The SIM is a physical, immersive event.** Humans negotiate face to face. The app provides communication infrastructure ONLY where physical interaction is impossible:

| Need | Solution |
|------|----------|
| Talk to an AI participant | **In-app meeting** (voice or text) |
| Team coordination during movement | **Team channel** (group chat) |
| Moderator announcements | **Public broadcast** (push notification) |
| Personal AI mentor | **Argus** (separate from game comms) |
| Negotiate with another human | **Walk up to them.** |
| Hold an alliance meeting | **Find a room. Sit down. Talk.** |
| Make a public speech | **Stand up. Speak. Secretary transcribes.** |

### AI Meeting Protocol

| Step | Detail |
|------|--------|
| 1. Request | Participant taps "Meet [AI role name]" |
| 2. AI prepares | Intent notes generated from cognitive state |
| 3. Session starts | Voice (primary) or text (fallback) |
| 4. Conversation | Natural turn-taking, AI adapts from its Block 2 personality |
| 5. Transcript | Automatically captured |
| 6. Post-meeting | AI reflects (Block 3/4 update), may follow up with transaction |

### Team Channel

| Property | Detail |
|----------|--------|
| Access | Country team members only |
| Format | Simple group chat (text) |
| Purpose | Coordination when team is physically separated |
| Opacity | Facilitator can see; other countries cannot |

### Public Broadcast

| Property | Detail |
|----------|--------|
| Sender | Facilitator only (or participant via public statement mechanic) |
| Audience | All participants + public display |
| Format | Text announcement, push notification, displayed prominently |

---

# AI PARTICIPANT INTERFACE

Not a screen — an API. Fully defined in existing documents:
- `CON_F1_AI_PARTICIPANT_MODULE_v2.frozen.md` — Module Interface Protocol (7 message types)
- `SEED_E2_AI_CONVERSATIONS_v1.md` — conversation engine, cognitive model
- `SEED_F4_API_CONTRACTS_v1.md` — API endpoints

**Same rights, same constraints as a human in the same role.** The SIM doesn't distinguish human from AI in any game mechanic.

---

# CROSS-CUTTING CONCERNS

## Phase Behavior

| Phase | Participant sees | Participant can do |
|-------|-----------------|-------------------|
| **Check-in** | Fixed reference + Argus | Read brief, talk to Argus, set goals |
| **Phase A** | All current info (real-time) | All actions (#1-#31) + transactions + communications |
| **Deadline** | Timer turns red | Must submit routine inputs (#1-#6) NOW |
| **Phase B** | New units available + "World update processing" | Deploy units (#13). Read-only for everything else. |
| **Results** | Updated dashboards + new briefing | Read results, plan next round |
| **Special: Nuclear** | Authorization clock + flight timer | Response actions only (intercept, counter-launch, do nothing) |

## Information Asymmetry

Enforced at three levels (from G1):
1. **Database (RLS)** — queries return only authorized rows
2. **API (Edge Functions)** — responses filtered by role
3. **Client** — renders only received data

The same country dashboard shows DIFFERENT data to different team members based on their role's access rights.

## Succession Chains

If a Head of State is killed or incapacitated (health event, assassination, arrest):

| Country | Successor | Notes |
|---------|-----------|-------|
| Columbia | **Volt** (VP) | Constitutional succession. Same participant, expanded powers. |
| Cathay | **Sage** (Party Elder) | Acting Chairman. Collective leadership asserts. |
| Nordostan | **Ironhand** (General) | Military succession. Acting President. |
| Heartland | **Bulwark** (if active) or **Broker** | Next most senior active leader. |
| Persia | **Anvil selects** | Kingmaker mechanic — Anvil chooses new Supreme Leader (could be Dawn or an NPC). Creates political event. |
| Solo countries | Facilitator decision | Country goes to AI control, or facilitator assigns new human. |

The successor inherits Head of State powers. The original participant keeps their role (now reduced) or is removed from play (if dead). Arrested roles can be released (via negotiation or coup).

## Mid-Term & Election Reference

Election procedures are fully specified in `SEED_D_ELECTION_PROCEDURE.md`. Key points for the web app:
- **R2 Columbia mid-terms:** 50/50 AI score + player vote. If incumbent loses, Parliament flips to 3-2 opposition. Dealer loses budget/treaty ratification control.
- **R3-4 Heartland wartime election:** If Beacon loses, Bulwark becomes president. Same participant, new powers.
- **R5 Columbia presidential:** Full leadership transition if opposition wins.

The app must: display election status, collect player votes (where applicable), show results with narrative.

## Mobile Requirements

- Primary device is a phone (participants walk the room)
- Touch targets >= 44px
- One-handed action submission
- Pinch-zoomable map
- Push notifications for critical alerts
- Swipeable tabs between Personal / Country / World views

---

# NEXT STEPS

1. **Review this spec** — are the info blocks and actions complete and correct?
2. **System Contracts** — derive from this spec: event schemas, table contracts, channel definitions
3. **Wireframes** (Detailed Design stage) — screen layouts based on these blocks
4. **Implementation** — build against the contracts

---

*The web app serves the simulation, not the other way around. Keep it simple, keep it connected to the SIM design, keep humans talking to humans.*
