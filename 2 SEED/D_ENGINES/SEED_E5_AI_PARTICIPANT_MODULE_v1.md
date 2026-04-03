# AI Participant Module — SEED Specification
## Thucydides Trap SIM
**Version:** 2.0 | **Date:** 2026-04-04 | **Status:** Active
**Concept reference:** CON_C1 F1 (AI Participant Module), SEED_E2 (AI Conversations)
**Architecture reference:** KING SIM (`/KING/app/src/services/ai/`)
**Dependencies:** Context Assembly Service (D9), NOUS (D10), Engine (D8)

---

## 1. Overview

The AI Participant Module operates **all non-human roles** in the simulation. In full product mode, this means up to 40 roles across 21 countries — heads of state, military chiefs, intelligence directors, diplomats, opposition leaders. In unmanned mode, all 40 roles are AI-operated.

**Each AI participant is an autonomous agent** that:
- Receives information through its visibility scope
- Reasons about strategy using LLM calls
- Proactively initiates actions during the round (conversations, attacks, deals)
- Reacts to incoming events (proposals, combat alerts, news)
- Submits mandatory decisions at round deadlines
- Updates its memory after significant events
- Adapts its strategy based on outcomes

**Architecture:** KING-proven 4-block cognitive model with event-driven active loop, priority-based memory updates, and context caching (~85% cost reduction).

---

## 2. Cognitive Model (4 Blocks)

### Block 1: RULES (immutable per SIM)
Game mechanics, available actions for this role, combat odds, production costs, economic formulas summary, map structure, authorization rules. Customized per role type (HoS sees budget rules; military chief sees combat rules). **Cached for entire SIM.**

### Block 2: IDENTITY (generated once, rarely updated)
Character personality, values, speaking style, negotiation approach, risk orientation, faction loyalty. Generated from role brief via LLM call at T=0.85 for personality diversity. Updated only on major identity events (regime change, traumatic defeat, ideological shift). **Cached, refreshed on identity events only.**

### Block 3: MEMORY (updated continuously)
Three tiers of memory, managed by freshness and relevance:

| Tier | Content | Update trigger | Retention |
|------|---------|---------------|-----------|
| **Immediate** | Last conversation summary, last action outcome, last proposal received | After each event | Until replaced by next |
| **Round** | All conversations this round, all decisions, all outcomes, relationship changes | Accumulated during round | Full detail current round, summarized for past rounds |
| **Strategic** | Key commitments, betrayals, alliances, failed negotiations, intelligence gathered | Promoted from Round tier | Persistent, compressed over time |

### Block 4: GOALS & STRATEGY (updated per round + after major events)
Current priorities ranked by urgency, action plans, contingencies. Derived from role objectives + current situation. Revised:
- At round start (new world state)
- After major events (war outcome, election result, treaty signed)
- After conversations that change strategic picture

### Context Caching Strategy
```
Block 1 (Rules):    Cached entire SIM              ~3K tokens
Block 2 (Identity): Cached, rare refresh           ~500 tokens
Block 3 (Memory):   Refreshed continuously          ~2-4K tokens (grows, compressed)
Block 4 (Goals):    Refreshed per round + events    ~500-800 tokens

Per-call fresh: world_state + instruction           ~3-4K tokens
Per-call cached: Blocks 1+2                         ~3.5K tokens
Savings: ~40% per call (Anthropic prompt caching)
```

---

## 3. Role Types & Capabilities

### 3.1 Heads of State (21 roles — one per country)
**The strategic decision-maker.** Controls all country-level actions.

Powers: budget, tariffs, sanctions, treaties, OPEC, fire team members, authorize attacks (co-sign with mil chief), nuclear authorization (3-way), public statements, propaganda, repression.

### 3.2 Military Chiefs (5 roles — major countries only)
**Combat commander.** Controls military operations.

Powers: ground attack (needs HoS co-sign), naval combat, bombardment, air strike, blockade, deploy forces, mobilize, reserve management. Cannot set budget or diplomacy.

### 3.3 Intelligence Directors (3-5 roles)
**Covert operations.** Controls intelligence pool.

Powers: espionage, sabotage (3 targets), cyber attack, disinformation, election meddling, assassination. Limited pool per round (2-3 ops).

### 3.4 Diplomats (3-5 roles)
**Negotiation specialists.** Can conduct parallel diplomacy.

Powers: negotiate treaties, represent abroad, diplomatic channels, public statements. Cannot commit country (needs HoS approval for binding agreements).

### 3.5 Opposition Leaders (2-3 roles — democracies)
**Political challengers.** Pursue alternative agenda.

Powers: block budget (if majority), launch investigation, campaign, public statements, foreign meetings. Can undermine incumbent, run for office.

### 3.6 Solo Country Leaders (14 roles)
**Combined HoS + mil chief.** Small countries with one AI role.

Powers: all HoS powers + military command. Simplified decision-making (no internal team dynamics).

### Authorization Matrix

| Action | HoS | Mil Chief | Intel | Diplomat | Opposition |
|--------|:---:|:---------:|:-----:|:--------:|:----------:|
| Budget submission | ✓ | | | | Block (if majority) |
| Tariffs/Sanctions | ✓ | | | | |
| OPEC production | ✓ | | | | |
| Ground attack | Co-sign | Co-sign | | | |
| Naval/Air/Blockade | | ✓ | | | |
| Strategic missile | ✓ + mil | | | | |
| Nuclear auth | ✓ + mil + 1 | Co-sign | | | |
| Covert ops | | | ✓ | | |
| Treaty signing | ✓ | | | Negotiate (not sign) | |
| Propaganda | ✓ | | | | |
| Public statement | ✓ | | | ✓ | ✓ |
| Fire role | ✓ | | | | |
| Arrest | ✓ | | | | |
| Investigation | | | | | ✓ |
| Election campaign | | | | | ✓ |
| Conversation | ✓ | ✓ | ✓ | ✓ | ✓ |
| Transaction | ✓ | | | Propose (HoS confirms) | |

---

## 4. Active Round Loop

**This is the core innovation from KING.** During each round, AI participants don't just submit one batch of decisions. They operate in a continuous active loop, proactively pursuing goals and reacting to events.

### 4.1 Loop Architecture (from KING AIDecisionLoopService)

```
ROUND STARTS
    │
    ▼
INITIAL DELIBERATION
    │ "What are my priorities this round?"
    │ Sets Block 4 goals, identifies conversation targets, plans actions
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│              ACTIVE LOOP (repeats every N seconds)       │
│                                                         │
│  1. CHECK STATUS                                        │
│     Am I idle? (not in conversation, not waiting)       │
│     Is there time remaining in the round?               │
│                                                         │
│  2. CHECK INCOMING                                      │
│     Any new events since last check?                    │
│     - Conversation request received?                    │
│     - Proposal to evaluate?                             │
│     - Combat result arrived?                            │
│     - News/announcement?                                │
│     → If yes: REACT (handle event, update memory)       │
│                                                         │
│  3. PROACTIVE DECISION (LLM call)                       │
│     Given current situation, what should I do now?      │
│     Options:                                            │
│     - Initiate conversation with another leader         │
│     - Execute a military action                         │
│     - Propose a transaction/deal                        │
│     - Issue a public statement                          │
│     - Launch covert operation                           │
│     - Wait (nothing urgent)                             │
│     → Execute chosen action                             │
│                                                         │
│  4. COOLDOWN                                            │
│     Wait N seconds before next loop iteration           │
│     (configurable: 30s unmanned, 5min real-time)        │
│                                                         │
└─────────────────────────────────────────────────────────┘
    │
    ▼ (round timer expires)
MANDATORY SUBMISSION
    │ Budget, tariffs, sanctions, OPEC, deployment
    │ Submitted from current Block 4 strategy
    │
    ▼
ENGINE PROCESSES (Pass 1 → NOUS Pass 2 → results)
    │
    ▼
ROUND REFLECTION
    │ Receive results, update Blocks 3+4
    │ Prepare for next round
```

### 4.2 Decision Cycle Parameters

| Parameter | Real-time SIM | Unmanned SIM |
|-----------|:------------:|:------------:|
| Loop interval | 5 minutes | 10-30 seconds |
| Stagger between agents | 3 seconds | 1 second |
| Max conversations per leader per round | 3 | 3 |
| Conversation turns | 8 per side | 8 per side |
| Cooldown after conversation | 2 minutes | 5 seconds |
| Round duration | 60-120 minutes | 60-180 seconds |
| Min time remaining to start action | 3 minutes | 10 seconds |

### 4.3 Decision Prompt (proactive loop)

```
You are {character_name}, {title} of {country}.
It is Round {N}, {time_remaining} remaining in this round.

Since your last check:
{new_events_summary}

Your current priorities (Block 4):
{goals_summary}

Your pending conversations: {pending_list}
Your available actions: {available_actions}

What do you want to do RIGHT NOW? Choose one:
0 = Wait (nothing urgent, check again later)
1 = Initiate 1:1 conversation with [target_name] about [topic]
2 = Execute military action: [specify]
3 = Propose transaction to [target]: [terms]
4 = Launch covert operation: [specify]
5 = Issue public statement: [content]
6 = Other action: [specify]

Respond with JSON: {"action": 0-6, "details": {...}, "reasoning": "brief"}
```

### 4.4 Status Lifecycle

```
IDLE ──→ DECIDING (LLM call for proactive decision)
  │         │
  │         ▼
  │      ACTING (executing action — e.g., starting conversation)
  │         │
  │         ▼
  │      BUSY (in conversation, waiting for response)
  │         │
  │         ▼
  │      REFLECTING (post-action memory update)
  │         │
  └─────────┘ (back to IDLE)
```

Only IDLE agents are polled in the active loop. BUSY agents (in conversation) are skipped until conversation completes.

---

## 5. Cognitive Update System

### 5.1 Update Triggers & Priority

| Trigger | Priority | Memory update | Strategy update | When |
|---------|:--------:|:------------:|:---------------:|------|
| Conversation completed | **1 (immediate)** | ✓ Summary + relationship | ✓ If strategic picture changed | Before next action |
| Proposal received | **1** | ✓ Record proposal | ✓ Evaluate urgency | Before response deadline |
| Combat result | **1** | ✓ Record outcome | ✓ If territory/forces changed | Immediately |
| Own action outcome | **1** | ✓ Record result | Only if unexpected | After action resolves |
| Round results (engine) | **1** | ✓ Full round record | ✓ Full reassessment | After Pass 2 |
| Other country's public action | **2 (batched)** | ✓ Note event | Only if affects plans | Batched (5 items or 30s) |
| Market/economic change | **2** | ✓ Note change | Only if significant | Batched |
| News/announcement | **2** | ✓ Note | Rarely | Batched |

### 5.2 Immediate Updates (Priority 1)

After a conversation completes:
```
1. Summarize conversation (LLM call, ~200 tokens out)
   "Spoke with Helmsman about Formosa. He deflected on naval buildup.
    Offered trade deal but didn't commit on timeline. Trust: slightly down."

2. Update Block 3 MEMORY
   - Add conversation summary
   - Update relationship score for counterpart
   - Record any proposals made/received

3. Update Block 4 GOALS (if needed)
   - "Helmsman is evasive → increase Formosa deterrence priority"
   - Only if conversation revealed something strategy-changing

4. Agent returns to IDLE status
   → Available for next loop iteration
   → CRITICAL: next conversation/action uses updated memory
```

### 5.3 Batched Updates (Priority 2)

Non-critical events accumulate:
```
Batch triggers when: 5 items accumulated OR 30 seconds passed (unmanned) / 5 minutes (real-time)

Process as single LLM reflection call:
  "Here are 5 things that happened since your last update:
   1. Oil price rose to $125
   2. Teutonia imposed L1 tariffs on Cathay
   3. Ruthenia lost zone ruthenia_2
   4. Caribe declared in crisis
   5. Solaria cut OPEC production

   Update your situational awareness. Any changes to priorities?"

Output: Updated Block 3 notes + optional Block 4 priority revision
```

### 5.4 Memory Compression (Late Rounds)

Token budget for Block 3 grows each round. Compression strategy:
- **Current round**: Full detail (~800-1200 tokens)
- **Previous round**: Key decisions + outcomes + conversation summaries (~400 tokens)
- **2+ rounds ago**: Compressed to strategic facts only (~150 tokens each)
- **Strategic memory**: Persistent key facts (betrayals, alliances, commitments) (~200 tokens)

Total Block 3 budget: ~3000 tokens at round 6. Well within context limits.

---

## 6. Conversation System

### 6.1 Conversation Types

| Type | Participants | Max turns | Initiation | Product | Unmanned v1 |
|------|-------------|-----------|-----------|---------|:-----------:|
| **Bilateral** | 2 roles | 8 per side (16 total) | Either party | ✓ | ✓ |
| **Multi-party meeting** | 3-8 roles | 4 per participant | HoS or org chair | ✓ | Skip |
| **Public speech** | 1 → all | 1 (monologue) | Any role | ✓ | ✓ |
| **Team council** | 2-9 (same country) | 6 per participant | HoS or any member | ✓ | Skip |

### 6.2 Bilateral Conversation Flow

```
LEADER A decides: "I want to talk to Leader B about Formosa"
    │
    ▼
INTENT NOTES generated (private, not shared):
    A's intent: "Warn about consequences. Probe naval buildup timing.
                 Offer trade deal if he backs down."
    │
    ▼
CHECK: Is Leader B available? (status = IDLE)
    - If yes → start conversation
    - If busy → queue request, notify when available
    │
    ▼
CONVERSATION START
    Both leaders set status = BUSY
    Context per participant:
      - Block 2 (Identity) — speaking style
      - Relationship history with counterpart
      - Intent notes (private)
      - World state (shared, visibility-scoped)
    │
    ▼
TURN-BY-TURN (max 8 turns per side)
    A speaks → LLM generates message (~100-200 tokens)
    B responds → LLM generates message
    A speaks → ...
    │
    Early stop: either participant can end ("I think we've covered
    everything" / "I need to think about your proposal")
    │
    ▼
CONVERSATION END
    Transcript stored
    Each participant: summarize + update memory (Priority 1)
    Both set status = IDLE
    Any proposals made → logged as pending transactions
```

### 6.3 Conversation Context per Turn

```
System: You are {character_name}. {identity_summary from Block 2}

Context:
  You are in a private meeting with {counterpart_name}, {their_title}.
  Your relationship: {history_summary}

  Your private intent (NOT to be stated explicitly):
  {intent_notes}

  World context relevant to this conversation:
  {filtered_world_state}

Conversation so far:
  {transcript}

Generate your next message. Speak in character.
Be strategic — pursue your intent without revealing your full hand.
Keep messages under 150 words.
```

### 6.4 Limits

| Constraint | Value | Rationale |
|-----------|-------|-----------|
| Max conversations per agent per round | 3 | Time budget + decision fatigue |
| Max turns per conversation | 8 per side | Diminishing returns after 8 |
| Message length | 150 words max | Focused, strategic dialogue |
| Cooldown between conversations | 5s (unmanned) / 2min (real-time) | Memory update time |
| Max simultaneous conversations | 1 per agent | Status lifecycle: IDLE→BUSY→IDLE |

---

## 7. Transaction System

### 7.1 Transaction Types

| Transaction | A gives | A receives | Authorization | Confirmation |
|------------|---------|-----------|--------------|-------------|
| **Coin transfer** | Coins | Goodwill / deal term | HoS | Recipient accepts |
| **Arms sale** | Military units | Coins | HoS | Recipient accepts + pays |
| **Arms gift** | Military units | Alliance / deal | HoS | Recipient accepts |
| **Tech sharing** | Tech access | Coins / reciprocal | HoS | Recipient accepts |
| **Basing rights** | Zone access | Coins / security | HoS (both) | Both HoS confirm |
| **Ceasefire** | Stop attacks | Mutual stop | HoS (both) | Both HoS confirm |
| **Peace treaty** | End war | Mutual end | HoS (both) | Both HoS confirm |
| **Alliance** | Mutual defense | Mutual defense | HoS (both) | Both HoS confirm |
| **Trade agreement** | Tariff reduction | Mutual reduction | HoS (both) | Both HoS confirm |
| **Sanctions coordination** | Joint sanctions | Shared burden | HoS (coalition) | All parties confirm |

### 7.2 Transaction Flow

```
PROPOSE (during conversation or as standalone action)
    │ Proposer creates structured terms
    │ Logged as pending_transaction
    │
    ▼
EVALUATE (counterpart receives proposal)
    │ LLM call with proposal terms + own situation + relationship
    │ Output: accept / reject / counter-propose
    │
    ▼
CONFIRM or COUNTER
    │ If accepted: execute immediately
    │ If counter: proposer evaluates counter (1 iteration max)
    │ If rejected: logged, relationship may adjust
    │
    ▼
EXECUTE
    │ State changes applied (coins moved, units transferred)
    │ Event logged (visibility depends on transaction type)
    │ Both parties' memory updated
```

---

## 8. Complete Action Catalog

### 8.1 Mandatory Inputs (once per round, submitted at round end)

| # | Action | Parameters | Who |
|---|--------|-----------|-----|
| 1 | `budget_submit` | social_pct (0.5-1.5), military_coins, tech_coins | HoS |
| 2 | `tariff_set` | {target: level(0-3)} | HoS |
| 3 | `sanction_set` | {target: level(0-3)} | HoS |
| 4 | `opec_production` | min/low/normal/high/max | HoS (OPEC member) |
| 5 | `deployment` | {unit_type: zone} for new/moved units | HoS |

### 8.2 Military Actions (anytime during round)

| # | Action | Parameters | Authorization | Resolution |
|---|--------|-----------|--------------|-----------|
| 6 | `ground_attack` | from_zone, to_zone, units | HoS + mil chief | RISK dice |
| 7 | `naval_combat` | zone, target | Mil chief | RISK dice (naval) |
| 8 | `naval_bombardment` | target_zone, ships | Mil chief | Random unit |
| 9 | `air_strike` | target_zone, aircraft | Mil chief | Random unit |
| 10 | `blockade_set` | chokepoint, level | Mil chief | Supply reduction |
| 11 | `blockade_remove` | chokepoint | Mil chief | Restore trade |
| 12 | `strategic_missile` | target_zone, quantity | HoS + mil chief | Zone damage |
| 13 | `nuclear_authorize` | target_zone | HoS + mil + 1 | MAD destruction |
| 14 | `mobilize` | units_from_pool | HoS or mil chief | Pool → active |
| 15 | `reserve_move` | units | Mil chief | Active → reserve |

### 8.3 Covert Operations (limited pool)

| # | Action | Target | Success | Detection | Effect |
|---|--------|--------|:-------:|:---------:|--------|
| 16 | `espionage` | Country | 70% | 20% | Reveal hidden data |
| 17 | `sabotage_military` | Country | 50% | 40% | Destroy 1 unit |
| 18 | `sabotage_economic` | Country | 50% | 40% | Destroy coins |
| 19 | `sabotage_infrastructure` | Country | 50% | 40% | GDP damage |
| 20 | `sabotage_nuclear` | Country | 40% | 50% | -15-20% progress |
| 21 | `cyber_attack` | Country | 60% | 30% | System disruption |
| 22 | `disinformation` | Country | 55% | 25% | -stability/-support |
| 23 | `election_meddling` | Country | 40% | 35% | Shift election |
| 24 | `assassination` | Role | 20-60% | varies | Eliminate person |
| 25 | `proxy_attack` | Country | 50% | 30% | Deniable damage |

### 8.4 Political Actions

| # | Action | Parameters | Who | Effect |
|---|--------|-----------|-----|--------|
| 26 | `propaganda` | coins (1-3) | HoS | +stability, +support |
| 27 | `repression` | intensity (1-3) | HoS (autocracy) | +stability, -support |
| 28 | `arrest` | target_role | HoS | Remove from play |
| 29 | `fire` | target_role | HoS | Remove from position |
| 30 | `call_election` | (Ruthenia) | 2 of 3 players | Force election |
| 31 | `impeach` | target_HoS | Opposition (democracy) | Requires votes |
| 32 | `nominate` | candidate_role | Party/faction | Election candidacy |

### 8.5 Economic Actions

| # | Action | Parameters | Who | Effect |
|---|--------|-----------|-----|--------|
| 33 | `print_money` | (once/round) | HoS | +3% GDP → treasury, +inflation |
| 34 | `tech_investment` | coins, program | HoS | Accelerate AI/nuclear R&D |
| 35 | `private_tech_invest` | personal_coins | Designated roles | Pioneer/Circuit role action |

### 8.6 Transactions (bilateral, 2-phase)

| # | Transaction | Authorization |
|---|------------|--------------|
| 36 | `coin_transfer` | HoS |
| 37 | `arms_sale` | HoS |
| 38 | `arms_gift` | HoS |
| 39 | `tech_transfer` | HoS |
| 40 | `basing_rights` | Both HoS |
| 41 | `ceasefire` | Both HoS |
| 42 | `peace_treaty` | Both HoS |
| 43 | `alliance` | Both HoS |
| 44 | `trade_agreement` | Both HoS |
| 45 | `sanctions_coordination` | Coalition HoS |

### 8.7 Communication

| # | Action | Who | Details |
|---|--------|-----|---------|
| 46 | `request_conversation` | Any role | Bilateral, specify target + intent |
| 47 | `request_meeting` | HoS or chair | Multi-party, specify participants |
| 48 | `public_statement` | Any role | Visible to all |
| 49 | `public_speech` | HoS at events | Formal address |

### 8.8 Election-Related

| # | Action | Who | When |
|---|--------|-----|------|
| 50 | `cast_vote` | Team members | During elections |
| 51 | `campaign_speech` | Candidates | Before election |

---

## 9. Event System

### 9.1 Incoming Event Types

| Event | Priority | Agent reaction |
|-------|:--------:|---------------|
| `conversation_request` | 1 | Accept/decline, prepare intent notes |
| `proposal_received` | 1 | Evaluate, accept/reject/counter |
| `combat_result` | 1 | Update military assessment, may trigger escalation |
| `covert_op_detected` | 1 | Diplomatic response, retaliation? |
| `election_called` | 1 | Campaign strategy, voting plan |
| `leader_incapacitated` | 1 | Succession protocol |
| `round_results` | 1 | Full strategic reassessment |
| `public_statement_by_other` | 2 | Note, maybe respond |
| `market_change` | 2 | Note, adjust if significant |
| `third_party_war_declared` | 2 | Assess implications |
| `treaty_announced` | 2 | Assess impact on own strategy |
| `general_news` | 2 | Background awareness |

### 9.2 Event Dispatch Pattern (from KING)

```
Event arrives
    │
    ▼
EventDispatcher singleton
    │ Routes to registered handlers
    │ Dedup check (prevent double-processing)
    │
    ▼
Priority 1 → Queue for immediate processing
    │ Agent interrupts idle state
    │ Handles event → memory update → resume
    │
Priority 2 → Accumulate in batch
    │ Process when: 5 items OR 30 seconds (unmanned)
    │ Single reflection call covers all batched items
```

---

## 10. Integration with Engine

### 10.1 Round Orchestration

```
┌─ AGENTS PHASE (active loop) ─────────────────────────┐
│                                                       │
│  All 21+ agents run active loops in parallel          │
│  Conversations happen between agents                   │
│  Transactions proposed and resolved                    │
│  Military actions executed (via Live Action Engine)    │
│  Covert operations launched                            │
│                                                       │
│  Duration: 60-180s (unmanned) / 60-120min (real-time) │
└───────────────────────────┬───────────────────────────┘
                            │
                            ▼
┌─ MANDATORY SUBMISSION ────────────────────────────────┐
│  Each HoS submits: budget, tariffs, sanctions, OPEC   │
│  Each mil chief submits: deployment orders             │
│  Derived from current Block 4 strategy                 │
└───────────────────────────┬───────────────────────────┘
                            │
                            ▼
┌─ ENGINE PROCESSING ───────────────────────────────────┐
│  Pass 1: Deterministic formulas (economic, political)  │
│  NOUS Pass 2: AI judgment adjustments                  │
│  Pass 3: Narrative generation                          │
└───────────────────────────┬───────────────────────────┘
                            │
                            ▼
┌─ RESULTS BROADCAST ───────────────────────────────────┐
│  All agents receive results (visibility-scoped)        │
│  Priority 1 reflection: update memory + strategy       │
│  Prepare for next round                                │
└───────────────────────────────────────────────────────┘
```

### 10.2 Action Validation

Every action goes through validation before execution:
1. **Authorization**: Does this role have the power? (authorization matrix)
2. **Resources**: Can they afford it? (treasury, unit availability, intel pool)
3. **Timing**: Is it the right phase? (military actions during Phase A only)
4. **Rules**: Is it legal? (can't attack allies, can't exceed production capacity)
5. **Co-signature**: Does it need co-sign? (attacks need HoS + mil chief)

Invalid actions: logged, agent notified, no execution.

---

## 11. Testing Interface

### 11.1 Chat with Any Agent

```
> /talk dealer round:3

DEALER (Columbia President): [context loaded, round 3]

You: Why did you escalate tariffs on Cathay?

DEALER: Cathay is approaching AI L3. Tariffs slow their growth and
signal resolve. The cost to us is manageable at L2. If Helmsman
retaliates, I rally Western Treaty allies for L3.

You: What if he blockades Formosa?

DEALER: That's my nightmare scenario. Our GDP takes a 6% hit from
semiconductor disruption. I've positioned Shield to reinforce the
Pacific fleet, but honestly — if he commits fully, we can't stop
the blockade without risking escalation to strategic weapons.

> /inspect memory
[Block 3: 1,850 tokens — 3 rounds of history]
  R1: Set L1 tariffs on Cathay, spoke with Pathfinder about sanctions
  R2: Cathay retaliated L1, escalated to L2. Sabotage on Persia nuclear failed.
  R3: Spoke with Helmsman (evasive on Formosa), arms sale to Ruthenia.

> /inspect goals
[Block 4: 620 tokens — 6 objectives]
  1. Formosa deterrence [URGENT — Cathay naval buildup accelerating]
  2. Persia nuclear prevention [CRITICAL — breakout imminent]
  3. Sarmatia sanctions [MAINTAINING — coalition holding]
  4. Election prep [R5 approaching — support at 34%]
  5. AI L4 race [ON TRACK — 60% progress]
  6. Caribe resolution [LOW PRIORITY]
```

### 11.2 Observation Mode

Watch agents think and act in real-time:
```
> /observe round:3

[R3 Active Loop — Tick 1]
  DEALER (idle): Deliberating... → wants to talk to HELMSMAN about Formosa
  HELMSMAN (idle): Deliberating... → wants to talk to PATHFINDER about alliance
  PATHFINDER (idle): Deliberating... → wants to attack ruthenia_2

[R3 Active Loop — Tick 2]
  DEALER ↔ HELMSMAN: conversation started (8 turns)
  PATHFINDER → ATTACK ruthenia_2 (ground, 5 units)
  BEACON (idle): Deliberating... → wait (nothing urgent)

[R3 Active Loop — Tick 3]
  DEALER ↔ HELMSMAN: conversation ended (6 turns, early stop)
    DEALER memory: "Helmsman evasive. Increasing Formosa priority."
    HELMSMAN memory: "Dealer clearly concerned about Formosa. Good."
  PATHFINDER attack resolved: ruthenia_2 captured (3 units lost)
  BEACON: reacting to territory loss → reassessing defense strategy
```

---

## 12. Unmanned Spacecraft Simplifications

| Feature | Full product | Unmanned v1 | Rationale |
|---------|-------------|-------------|-----------|
| Roles | 40 (multi-role teams) | **21 (leaders only)** | Leaders make all decisions |
| Team dynamics | Internal team negotiation | **Skip** | No internal politics |
| Conversations | Bilateral + multi-party + team | **Bilateral only** | Core mechanic |
| Conversation turns | 8 per side | **8 per side** | Same |
| Max conversations/round | 3 per agent | **3 per agent** | Same |
| Active loop interval | 5 minutes | **15-30 seconds** | Compressed time |
| Round duration | 60-120 minutes | **60-180 seconds** | Fast iteration |
| Voice | Text + speech synthesis | **Text only** | No humans listening |
| Argus | Full mentoring system | **Skip** | No humans to mentor |
| Moderator controls | Manual review + override | **Automatic only** | No moderator |
| Transaction types | All 10 | **All 10** | Full economic gameplay |
| Military actions | All 10 | **All 10** | Full military gameplay |
| Covert ops | All 10 | **All 10** | Full intel gameplay |
| Political actions | All 7 | **All 7** | Full political gameplay |
| Memory compression | Aggressive (long games) | **Light** | Only 6 rounds |
| Event batching | 5 items or 5 min | **5 items or 30 sec** | Fast iteration |
| Testing interface | Full web chat | **CLI /talk** | Developer tool |

---

## 13. Implementation Stages

### Stage 1: Core Agent + Strategic Reasoning
- LeaderAgent class with 4-block context
- Single LLM call per round → structured action JSON (all 51 actions)
- Action validation framework
- Full round loop: 21 agents → engine → NOUS → results
- Memory update at round end
- **Test:** 1 full SIM (6 rounds), all 21 leaders produce valid actions

### Stage 2: Active Loop + Conversations
- Active loop with configurable interval
- 8-turn bilateral conversations
- Intent notes before conversation
- Memory update after conversation (Priority 1 — before next action)
- **Test:** Verify agents initiate conversations, deals emerge from dialogue

### Stage 3: Transactions + Reactions
- Full transaction flow (propose → evaluate → execute)
- Event system (incoming events trigger reactions)
- Priority-based update batching
- **Test:** Arms sales, treaties, alliances form organically

### Stage 4: Memory + Strategy Evolution
- Full memory system (immediate/round/strategic tiers)
- Memory compression for late rounds
- Strategy revision after major events
- **Test:** Agent behavior evolves across rounds, not repetitive

### Stage 5: Testing Interface
- `/talk` CLI chat with any agent
- `/observe` real-time agent activity
- `/inspect` block contents
- Decision replay and analysis

### Stage 6: Option B (Anthropic Persistent Agent)
- Alternative architecture using persistent conversation
- Compare: reasoning quality, cost, reliability, memory coherence
- Decision: adopt, hybrid, or stay with Option A

---

## 14. Module Structure

```
app/engine/agents/
├── __init__.py
├── leader.py            ← LeaderAgent class (4-block, active loop)
├── profiles.py          ← Role data loading, identity generation
├── decisions.py         ← Action schemas, structured output, validation
├── conversations.py     ← Bilateral conversation engine (8-turn)
├── transactions.py      ← Propose → evaluate → execute flow
├── memory.py            ← Block 3/4 management, compression, reflection
├── events.py            ← Event dispatcher, handlers, priority queue
├── runner.py            ← Round orchestrator (all agents + engine + NOUS)
└── chat.py              ← Debug interface (/talk, /observe, /inspect)
```

---

## 15. Cost Estimate (per full unmanned SIM)

| Activity | Calls | Tokens/call | Total tokens | Model |
|----------|:-----:|:-----------:|:------------|:-----:|
| Identity generation (21 agents) | 21 | ~1K | ~21K | Sonnet |
| Initial deliberation (21 × 6 rounds) | 126 | ~10K in, ~2K out | ~1.5M | Sonnet |
| Active loop decisions (~3/agent/round) | ~378 | ~4K in, ~500 out | ~1.7M | Flash |
| Conversations (~30/round × 6) | ~1,440 turns | ~2K in, ~200 out | ~3.2M | Flash |
| Conversation summaries (~180) | 180 | ~1K in, ~200 out | ~216K | Flash |
| Transaction evaluations (~120) | 120 | ~2K in, ~500 out | ~300K | Flash |
| Batched reflections (~126) | 126 | ~3K in, ~500 out | ~440K | Flash |
| NOUS judgment (6 rounds) | 6 | ~8K in, ~1K out | ~54K | Sonnet |
| **Total** | **~2,400** | | **~7.4M tokens** | |

**Estimated cost:** ~$5-8 per full SIM run
**Estimated time:** ~20-40 minutes (with parallelization)
