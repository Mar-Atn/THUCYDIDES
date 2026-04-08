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

ROUND DEADLINE → Submit mandatory inputs (budget, tariffs, sanctions, OPEC)
  → If not submitted: previous round's settings carry forward

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
