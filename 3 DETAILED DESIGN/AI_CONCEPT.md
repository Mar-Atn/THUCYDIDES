# AI Participant Module — Concept

**Status:** Draft for Marat alignment
**Sources:** SEED_E5, SEED_D9, CON_F1, SEED_D13
**Principle:** The AI Participant module is a **standalone, independent module** that communicates with the SIM system via standard real-time connections and typed contracts. It can be developed, tested, and updated independently.

---

## 1. VISION

An AI participant is a **player, not a calculator.** It sits in the same seat a human would sit in. It sees what that human would see — no more, no less. It reasons about strategy, talks to other leaders, makes deals, and surprises the designers.

We do NOT prescribe behavior. We do NOT script reactions. We provide:
1. **A rich identity** (who the AI IS — personality, values, faction, style)
2. **Self-authored goals** (what the AI WANTS — objectives translated into its own strategic plan)
3. **Self-curated memory** (what the AI CHOSE to remember — not everything, just what it deems important)
4. **Relevant situation data** (what's HAPPENING — scoped to what this role can see)
5. **The action space** (what the AI CAN DO — authorized actions for this role)

And then: *"Given all this — what do you do?"*

---

## 2. MODULE BOUNDARY

The AI Participant module is a **black box** from the system's perspective:

```
┌─────────────────────────────────────────────┐
│              SIM SYSTEM                       │
│  (Engines, DB, Observatory, Realtime)         │
│                                               │
│  Provides: context, events, proposals         │
│  Receives: decisions, messages, memory        │
└───────────┬───────────────┬───────────────────┘
            │ STANDARD API  │
            │ (contracts)   │
            ▼               ▼
┌─────────────────────────────────────────────┐
│          AI PARTICIPANT MODULE                │
│                                               │
│  Could be: LLM-based agent (current)          │
│  Could be: rule-based bot (testing)           │
│  Could be: human via UI (future)              │
│  Could be: hybrid (human + AI copilot)        │
│                                               │
│  The system doesn't know or care.             │
└─────────────────────────────────────────────┘
```

**The API contract is the same regardless of who sits in the seat.** The system sends context and events. It receives decisions and messages. Whether a human typed them or an LLM generated them is invisible.

---

## 3. INPUTS — What the module receives

### 3.1 Context (assembled per decision, scoped to this role)

| Layer | Content | When refreshed |
|---|---|---|
| **Identity** | Character name, title, personality, values, faction, speaking style. Generated once at SIM start. | Rarely (regime change, trauma) |
| **Goals** | Self-authored strategic plan: priorities, contingencies, timeline. | Per round + after major events |
| **Memory** | Self-curated notes: relationships, commitments, lessons, observations. | After each conversation and decision |
| **Rules (Block 1)** | Game mechanics, available actions for this role, combat odds, production costs, economic formulas summary, map structure, authorization rules. Customized per role type. | Cached per SIM |
| **Situation data** | Scoped to this role's visibility: own country stats, public world state, targeted data per decision type | Per decision |
| **Instruction** | What type of decision is needed right now | Per LLM call |

### 3.2 Information scoping (critical — enforced at source)

**Each role sees ONLY what it should see:**

| Visibility | Who sees it | Examples |
|---|---|---|
| **PUBLIC** | Everyone | Oil price, public statements, declared wars, map, organizational meetings |
| **COUNTRY** | All roles in that country | Own GDP, treasury, stability, military positions, budget |
| **ROLE** | Only this specific role | Personal coins, intel reports received, covert op results, secret agreements they signed |
| **MODERATOR** | Facilitator only | All internal states, all agents' memory, judgment parameters |

**AI agents MUST NOT see:**
- Other countries' internal stats (unless publicly announced or learned via intelligence)
- Other agents' memory or goals
- Secret agreements they didn't sign
- Covert operations not targeted at or by them
- Moderator-level data

The Context Assembly Service enforces this. Every piece of data passes through visibility filtering BEFORE reaching the agent.

### 3.3 Events (pushed in real-time)

The module receives notifications of events relevant to this role:
- Attacked (combat affecting my country)
- Proposal received (transaction or agreement)
- Public statement mentioning my country
- Covert op detected (if detection succeeded)
- Round lifecycle (start, end, deadline approaching)
- Conversation request from another agent

---

## 4. OUTPUTS — What the module produces

### 4.1 Decisions (structured JSON)

Any action from CARD_ACTIONS that this role is authorized to take:
- Military: attack, move, blockade, missile launch, martial law
- Economic: budget, tariffs, sanctions, OPEC
- Covert: intelligence, sabotage, propaganda, election meddling
- Transactions: propose exchange, accept/decline/counter, propose agreement, sign agreement
- Communication: public statement, call org meeting, request conversation
- Domestic: arrest, fire, propaganda, coup (if conditions met)

Each decision: `{action_type, parameters, rationale}`

### 4.2 Messages (text)

- Conversation turns (bilateral, 8-turn max)
- Public statements (broadcast to all)
- Private messages (to specific role — future)

### 4.3 Memory updates (self-curated)

After significant events, the module produces memory updates:
- Conversation summaries ("Discussed arms deal with Dealer — he's open but wants tech in return")
- Relationship assessments ("Trust with Pathfinder: -0.2 after detected covert op")
- Strategic plan revisions ("Pivot: Formosa situation more urgent than Persia front")
- Observations ("Oil price spiking — Solaria must be cutting production")

These are the module's OWN notes for its future self. Not transcripts — strategic abstractions.

---

## 5. COMMUNICATION PROTOCOL

### 5.1 Standard contracts (Pydantic models + DB tables)

| Direction | Message type | Schema |
|---|---|---|
| System → Module | Context delivery | Assembled text blocks, scoped by visibility |
| System → Module | Event notification | `{event_type, country_code, summary, payload}` |
| System → Module | Proposal received | `{proposer, terms, offer, request, expires_at}` |
| System → Module | Conversation request | `{requester, topic}` |
| Module → System | Decision submitted | `{action_type, action_payload, rationale}` |
| Module → System | Conversation turn | `{text, end_conversation}` |
| Module → System | Memory update | `{memory_key, content, round_num}` |

*Per CON_F1 Module Interface Protocol + SEED_E5 §10.*

### 5.2 Independence

The module NEVER:
- Reads another agent's memories or decisions directly
- Accesses engine internals or formula parameters
- Bypasses visibility scoping
- Modifies world state directly (all changes go through engine processing)

The module CAN:
- Read its own prior memory
- Query visible world state via domain tools
- Submit any authorized action
- Initiate conversations with any other participant

---

## 6. ACTIVE LOOP (how the module operates during a round)

```
ROUND STARTS → Context delivered → Module begins

LOOP (repeats, ~10-30s intervals in unmanned mode):
  │
  ├─ CHECK: any incoming events/proposals/conversation requests?
  │   → If yes: REACT (evaluate proposal, respond to event, join conversation)
  │
  ├─ DECIDE: Given my goals + situation, what should I do NOW?
  │   → Options: wait, attack, propose deal, make statement, covert op, request meeting
  │   → Submit decision if action chosen
  │
  ├─ UPDATE: Did something significant happen?
  │   → If yes: update memory (Block 3), revise goals if needed (Block 4)
  │
  └─ COOLDOWN: wait before next iteration

MANDATORY DECISION CHECK (added 2026-04-08):
  → ~2 min before round deadline, system prompts agent
  → Agent MUST submit: budget, sanctions, tariffs, OPEC (if OPEC member)
  → Decision cycle prioritizes these if not yet submitted and round is near closing
  → If still not submitted by deadline: previous round's settings carry forward
  → In unmanned mode: agent is explicitly prompted before committing other actions

ROUND ENDS → Final reflection: update memory + goals for next round
```

**Decision cycle parameters** (per SEED_E5 §4.2):

| Parameter | Human play | Unmanned mode |
|---|---|---|
| Loop interval | 15-30 seconds | 10-30 seconds |
| Stagger between agents | — | 1-3 seconds (load distribution) |
| Max conversations per agent per round | 3 | 3 |
| Turns per conversation | 8 per side | 8 per side |
| Round duration | 45-80 minutes | 60-180 seconds |
| Mandatory deadline | End of Phase A | End of agent loop |

**Status lifecycle** (per SEED_E5 §4.4):
```
IDLE → DECIDING → ACTING → BUSY (in conversation) → REFLECTING → IDLE
```

**The module is PROACTIVE, not reactive.** It doesn't wait to be asked. It continuously evaluates the situation and acts when strategically valuable.

*Per SEED_E5 §4 + CON_F1 §Autonomous Action Loop.*

---

## 7. CURRENT IMPLEMENTATION vs VISION

| Aspect | Vision | Current | Gap |
|---|---|---|---|
| Cognitive model (4 blocks) | Full | Block 1+2 loaded, Block 3+4 basic | Memory tiers, goal evolution |
| Information scoping | Role-based visibility | Agents see most data | **Critical gap — need filtering** |
| Active loop | Continuous 10-30s polling | Up to 3 actions per round (batch) | Need real polling loop |
| Conversations | Initiated by agent proactively | Triggered by orchestrator after actions | Agent should REQUEST conversations |
| Transactions | Agent proposes + counterpart evaluates | Proposals logged but not executed | Wire `transactions.py` |
| Memory persistence | All blocks persisted to DB | Conversation memories persisted | Goal updates need persistence |
| Event reactions | Real-time push → agent responds | Prior-round events in prompt | Need intra-round reactions |
| Module independence | Standalone, API-only | Tightly coupled to round runner | Need clean API boundary |

### Priority for Unmanned Spacecraft phase:
1. **Information scoping** — agents must NOT see everything (critical for game integrity)
2. **Transaction execution** — via designed `transactions.py` module
3. **Agent-initiated conversations** — agent decides who to talk to, not orchestrator
4. **Goal evolution** — Block 4 updates after significant events, persisted
5. **Clean API boundary** — decouple from round_runner internals

---

## 8. ROUND LIFECYCLE & SKILL CATALOG (added 2026-04-08)

**Design principle:** We design for HUMANS AND AI with identical capabilities. The AI participant has maximum autonomy — same freedom a human participant would have. The delivery mechanism differs (orchestrator prompts vs real-time UI), but the decision space and timing are the same.

### 8.1 Round Lifecycle — From the Participant's Perspective

```
┌─────────────────────────────────────────────────────────────────┐
│  ROUND N: FREE PHASE (~80% of round time)                       │
│                                                                  │
│  Participant has FULL AUTONOMY. Can do anything at any time:     │
│                                                                  │
│  COMMUNICATE:                                                    │
│    • Request bilateral meeting (1-on-1, 8 turns)                │
│    • Attend organization meeting (Western Treaty, OPEC, etc.)   │
│    • Issue public statement                                      │
│    • (Future: multilateral meetings, voice)                      │
│                                                                  │
│  ACT (any authorized action from CARD_ACTIONS):                  │
│    • Military: attack, blockade, missile launch, nuclear         │
│    • Covert: intelligence, sabotage, propaganda, meddling        │
│    • Domestic: arrest, fire, coup, protest, propaganda           │
│    • Technology: private AI investment                            │
│    • Basing rights: grant or revoke                              │
│                                                                  │
│  TRADE:                                                          │
│    • Propose exchange (coins, units, tech, basing)               │
│    • Accept / decline / counter received proposals               │
│    • Draft agreement (ceasefire, alliance, trade deal)           │
│    • Sign / decline agreements                                   │
│                                                                  │
│  CONTEXT UPDATES (pushed by system):                             │
│    • "You were attacked" → can react immediately                 │
│    • "Deal proposed to you" → accept/reject/counter              │
│    • "Public statement by X" → adjust plans if needed            │
│    • "Covert op detected against you" → respond                  │
│    • Updated world state every ~5 minutes                        │
│                                                                  │
│  For AI: orchestrator visits every ~5 min with updates,          │
│  asks "what do you want to do?" Up to 3 actions per visit.       │
│  Reactive events (attacks, proposals) delivered immediately.     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  END OF ROUND: MANDATORY DECISIONS (~last 5 min)                │
│                                                                  │
│  System prompts: "Round ending. Review your economic settings."  │
│                                                                  │
│  MUST DECIDE (or keep status quo):                               │
│    • Budget: social spending (0.5-1.5× baseline),               │
│      ground/naval/air/missile/AD production levels,              │
│      tech investment (nuclear + AI coins)                        │
│    • Tariffs: per-country levels (L0-L3)                        │
│    • Sanctions: per-country levels (L0-L3)                      │
│    • OPEC production (if member): min/low/normal/high/max       │
│                                                                  │
│  Context provided: current settings, economic state,             │
│  relationships, objectives. Agent can explore rules/details.     │
│                                                                  │
│  Default: previous round's settings carry forward.               │
│  Human: reminded 5 min before deadline, manages own time.        │
│  AI: explicitly prompted with full context.                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  BATCH PROCESSING (system, no participant involvement)           │
│                                                                  │
│  • Combat resolution (RISK iterative + air + naval + missiles)  │
│  • Covert op outcomes (success/fail/detected/attributed)        │
│  • Transaction execution (validate + transfer assets)            │
│  • Agreement activation (ceasefire enforcement)                  │
│  • Economic engine (GDP, treasury, inflation, sanctions impact) │
│  • Political engine (stability, support, war tiredness)         │
│  • Technology engine (R&D advancement)                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  INTER-ROUND: RELOCATION PHASE                                   │
│                                                                  │
│  System prompts Military Chiefs + HoS:                           │
│  "Round results are being processed. Deploy/move your forces."  │
│                                                                  │
│  AVAILABLE ACTIONS:                                              │
│    • Deploy from reserve → map hex                               │
│    • Reposition active units → different hex                     │
│    • Withdraw units → reserve                                    │
│    • Embark/disembark ground units on naval                     │
│                                                                  │
│  No combat during this phase. Strategic repositioning only.      │
│  Processed before next round's engine tick.                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  ROUND N+1 START                                                 │
│                                                                  │
│  ALL participants receive:                                       │
│    • Round results summary (what happened, who was affected)    │
│    • Updated world state (new GDP, stability, unit positions)   │
│    • Personal updates (intel reports, covert op results,        │
│      conversation summaries, deal outcomes)                      │
│                                                                  │
│  AI agents: reflect, update memory, revise goals if needed.     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 8.2 Skill Catalog — Complete Set

Every discrete capability the AI participant must have. Each skill is independently testable.

#### A. FREE-PHASE SKILLS (during round, autonomous)

| # | Skill | Trigger | Input | Output | Actions covered |
|---|---|---|---|---|---|
| **A1** | **Action selection** | Orchestrator visits (~5 min) | Situation + goals + memory + available actions | 0-3 chosen actions with rationale | ALL from CARD_ACTIONS |
| **A2** | **Military attack** | Agent decides to attack | Unit positions + enemy positions + strategic goals | Attack order (units, target hex) | 1.3 Ground, 1.4 Air, 1.5 Naval, 1.7 Bombardment |
| **A3** | **Strategic missile/nuclear** | Agent decides escalation | Nuclear capability + targets + consequences | Launch order (warhead type, target) | 1.8 Missile, 1.9 Nuclear |
| **A4** | **Blockade decision** | Agent decides economic warfare | Naval positions + chokepoints + trade routes | Blockade order (zone, level) | 1.10 Blockade |
| **A5** | **Covert operation** | Agent decides to spy/sabotage | Intel pool + cards available + targets | Op order (type, target, question) | 4.1-4.4 Intelligence, Sabotage, Propaganda, Meddling |
| **A6** | **Domestic political action** | Agent decides internal move | Stability + support + faction balance | Action order (arrest, fire, coup, protest) | 6.1-6.7 Arrest, Assassination, Fire, Coup, Protest, Elections |
| **A7** | **Public statement** | Agent wants to signal/pressure | Current events + objectives + audience | Statement text + visibility | 7.3 Public Statement |
| **A8** | **Private tech investment** | Tycoon/business role | Personal coins + tech landscape | Investment amount + domain | 3.1 Private AI Investment |
| **A9** | **Basing rights** | Agent offers/revokes access | Alliances + military needs | Grant/revoke order | 1.11 Basing Rights |
| **A10** | **Martial law** | Crisis situation | Stability + reserve pool + political cost | Declare order | 1.2 Martial Law |

#### B. COMMUNICATION SKILLS

| # | Skill | Trigger | Input | Output |
|---|---|---|---|---|
| **B1** | **Request meeting** | Agent wants to talk to someone | Goals + relationship + topics | Meeting request (who, topic) |
| **B2** | **Bilateral conversation** | Meeting paired | Counterpart identity + topic + history | 8 turns of coherent, strategic dialogue |
| **B3** | **Organization meeting** | Scheduled or called | Org members + agenda + own goals | Meeting contribution (proposals, votes, statements) |
| **B4** | **Public diplomacy** | Agent wants to shape narrative | Current events + audience + goals | Public statement calibrated to audience |

#### C. TRADE/DEAL SKILLS

| # | Skill | Trigger | Input | Output |
|---|---|---|---|---|
| **C1** | **Propose exchange** | Agent wants to trade | Own assets + counterpart + strategic value | Structured offer (gives/receives) |
| **C2** | **Evaluate proposal** | Proposal received | Incoming offer + own situation + goals | Accept / decline / counter with reasoning |
| **C3** | **Draft agreement** | Agent wants formal commitment | Terms + signatories + type | Agreement draft (ceasefire, alliance, trade deal) |
| **C4** | **Evaluate agreement** | Agreement received for signature | Terms + implications + trust level | Sign / decline with comments |

#### D. MANDATORY DECISION SKILLS (end of round)

| # | Skill | Input | Output |
|---|---|---|---|
| **D1** | **Budget allocation** | Current GDP, treasury, military needs, social pressure, tech priorities | social_pct (0.5-1.5), ground_production, naval_production, air_production, missile_production, ad_production, tech_coins |
| **D2** | **Tariff setting** | Trade relationships, economic pressure, retaliation risk | Per-country tariff levels (L0-L3) |
| **D3** | **Sanctions decision** | Wars, alliances, economic warfare goals | Per-country sanction levels (L0-L3) |
| **D4** | **OPEC production** | Oil price, revenue needs, geopolitical leverage | Production level (min/low/normal/high/max) |

#### E. INTER-ROUND SKILLS (relocation phase)

| # | Skill | Input | Output |
|---|---|---|---|
| **E1** | **Unit deployment** | Current positions + threats + objectives + round results | Deploy/reposition/withdraw orders |
| **E2** | **Embarkation** | Naval positions + ground units + planned operations | Embark/disembark orders |

#### F. META SKILLS (cross-cutting, always active)

| # | Skill | Trigger | Input | Output |
|---|---|---|---|---|
| **F1** | **Context absorption** | System pushes update | New events, world state changes, personal notifications | Understanding of what changed and why it matters |
| **F2** | **Reactive decision** | Attacked / proposal received / crisis | Urgent event + current state | Immediate response (counterattack, accept deal, emergency statement) |
| **F3** | **Reflection** | After conversation / major event / round end | Events + conversations + outcomes | Memory updates (Block 3) + goal revisions (Block 4) |
| **F4** | **Memory management** | After any significant event | Raw events + existing memory | Curated notes: what to remember, what to forget, what to update |
| **F5** | **Goal revision** | Dramatic world change (war starts, ally betrays, crisis) | Original goals + new reality | Revised strategic priorities + contingencies |
| **F6** | **Identity adaptation** | Extreme circumstances (regime change, personal crisis) | Original identity + transformative event | Adjusted persona (rare — only under extreme pressure) |
| **F7** | **Information seeking** | Need specific data for decision | Question + available tools | Query results (unit positions, economic data, relationship status) |
| **F8** | **Strategic reasoning** | Before any major decision | Full context + goals + constraints | Reasoned analysis of options, risks, and trade-offs |

### 8.3 Skill → Phase Mapping

| Phase | Skills active | Orchestrator role |
|---|---|---|
| **Free phase** | A1-A10, B1-B4, C1-C4, F1-F8 | Visits every ~5 min with updates, asks "what do you want to do?" |
| **Reactive** | F1, F2, C2, C4 | Delivers urgent events immediately (attack, proposal) |
| **Mandatory** | D1-D4, F7, F8 | Structured prompt: "here are your settings, adjust?" |
| **Relocation** | E1-E2, F7, F8 | Structured prompt: "deploy/move your forces" |
| **Reflection** | F3-F6 | After conversations, after round results delivered |

### 8.4 Testing Approach

Each skill tested independently through a focused harness:

**Level 1: Format** — does the output parse correctly? Valid JSON, correct fields, values in range.

**Level 2: Appropriateness** — given this specific context, is this a reasonable decision? Would a human plausibly do this?

**Level 3: Consistency** — same context 10 times → decisions consistent in direction. Varied contexts → behavior adapts. Adversarial contexts → avoids obvious traps.

**Cycle:** L1 → L2 → L3, iterating through hundreds of fast tests per skill before moving to the next skill. Full system integration (L4) only after all skills pass individually.

### 8.5 Unmanned Mode Specifics

In unmanned mode (all AI, no humans), the orchestrator manages timing:

| Human equivalent | AI implementation |
|---|---|
| Participant acts freely for 45-80 min | Agent gets 3-5 "visits" per round, up to 3 actions each |
| Sees events in real-time | Context updates delivered at each visit |
| Responds to proposals when convenient | Reactive events queued, delivered at next visit (or immediately for urgent) |
| Reminded 5 min before deadline | Mandatory decisions phase explicitly triggered |
| Moves units between rounds | Relocation phase explicitly triggered |
| Reflects naturally | Explicit reflection call after conversations + round end |

### 8.6 Heritage Reconciliation

Verified against heritage documents 2026-04-08:

- **SEED_E5 (AI Participant Module v2.0):** Section 8 round lifecycle aligns with SEED_E5 active loop (§4.1 — check status, check incoming, proactive decision, cooldown), conversation model (§6.2 — bilateral 8-turn, intent notes, reflection after), and decision cycle parameters (§4.2 — loop intervals, max conversations, round durations). The mandatory decisions phase maps to SEED_E5 §4.1 "MANDATORY SUBMISSION" step. Status lifecycle (§4.4: IDLE → DECIDING → ACTING → BUSY → REFLECTING → IDLE) is preserved. No contradictions.

- **SEED_C7 (Time Structure v1.0):** Our four-phase structure (free → mandatory → batch → relocation) maps cleanly to SEED_C7's Phase A (free action + negotiation + routine submissions at end) and Phase B (production + deployment + world model). SEED_C7 specifies "routine submissions deadline: end of Phase A" which matches our mandatory decisions phase. SEED_C7's Phase B combines production, deployment, and world model in parallel — our "batch processing" + "relocation" is a finer decomposition of the same concept but does not contradict. SEED_C7's deployment window (Phase B Step 1) maps to our relocation phase. No contradictions.

- **CON_C2 (Action System v2.0 frozen):** CON_C2 defines ~30 actions across 6 categories. CARD_ACTIONS.md (the current canonical reference, per CON_C2 reconciliation note) specifies 32 actions. Our skill catalog covers all 32 actions: military (A2-A4, A9-A10 → 1.1-1.11), economic (D1-D4 → 2.1-2.4), technology (A8 → 3.1), covert (A5 → 4.1-4.4), transactions (C1-C4 → 5.1-5.2), domestic (A6 → 6.1-6.7), communications (B1-B4 → 7.1-7.3). Action selection skill A1 is the meta-skill that dispatches to all others. No actions missing from skill catalog.

**Conclusion:** No contradictions found between Section 8 and heritage documents SEED_E5, SEED_C7, or CON_C2.
