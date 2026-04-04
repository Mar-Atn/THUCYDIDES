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

## 2.5 Context Architecture & Autonomy Model

### The Core Principle

An AI participant is a **powerful autonomous intellect** placed inside a geopolitical simulation. Given the right information and genuine freedom, it will reason strategically, pursue goals, build alliances, take risks, and adapt — like a real leader.

We do NOT prescribe behavior. We do NOT script reactions. We provide:
1. A rich identity (who the AI IS)
2. Self-authored goals (what the AI WANTS)
3. Self-curated memory (what the AI CHOSE to remember)
4. The relevant situation data (what's HAPPENING)
5. The action space (what the AI CAN DO)

And then: *"Given all this — what do you do?"*

### The CLAUDE.md Analogy

The architecture mirrors how Claude Code works with a large codebase:

| Claude Code | AI Participant |
|---|---|
| CLAUDE.md — always loaded, defines identity and rules | Block 2 (Identity) + Block 4 (Goals) — always loaded |
| Memory files — own notes, updated by choice | Block 3 (Memory) — self-curated, updated after conversations |
| Codebase files — available, opened on demand | Country data, rules, other countries' info — assembled per task |
| Autonomy — decides what to read, what to do | Autonomy — decides what to prioritize, who to talk to, what actions to take |

The AI participant doesn't carry the entire simulation in its head. It carries its **identity, plans, and key memories** permanently — and receives **task-relevant data** when making specific decisions.

### Three-Layer Context Model

```
┌─────────────────────────────────────────────────────────────┐
│ LAYER 1: PERMANENT CONTEXT (every call, ~4-5K tokens)       │
│                                                             │
│ Block 2: IDENTITY                                           │
│   Who I am, how I think, my personality, my values          │
│   Self-authored at initialization. Rarely changes.          │
│                                                             │
│ Block 4: GOALS & STRATEGY                                   │
│   What I'm trying to achieve. My plans. My priorities.      │
│   Self-authored. Updated by ME after significant events.    │
│   This is MY autonomous strategic thinking — not prescribed.│
│                                                             │
│ Block 3: MEMORY (highlights)                                │
│   What I chose to remember. Key relationships. Commitments. │
│   Lessons learned. Critical facts.                          │
│   Self-curated — I decide what matters.                     │
│   NOT a transcript. NOT all available data.                  │
│   My SUBJECTIVE strategic memory.                           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ LAYER 2: TASK CONTEXT (assembled per decision, ~3-6K)       │
│                                                             │
│ Selected by Context Assembly Service based on what the AI   │
│ is being asked to do RIGHT NOW:                             │
│                                                             │
│ Budget decision   → my economic state, revenue, costs,      │
│                     budget rules, social spending baseline   │
│                                                             │
│ Military decision → unit positions, combat rules, enemy     │
│                     forces, zone control, AD coverage        │
│                                                             │
│ Conversation      → counterpart profile, relationship       │
│                     history, my intent notes                 │
│                                                             │
│ Tariff/sanctions  → trade data, bilateral relations,        │
│                     coalition status, tariff mechanics        │
│                                                             │
│ Covert ops        → intel pool, target vulnerability,       │
│                     detection risk, past ops results         │
│                                                             │
│ Strategic review  → broad world state, all major countries,  │
│                     market indexes, war status, oil price    │
│                                                             │
│ This is OBJECTIVE DATA — not filtered by AI's preferences.  │
│ The AI sees the real numbers and real situation.             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ LAYER 3: INSTRUCTION (specific to the moment, ~200-500)     │
│                                                             │
│ What is being asked right now:                              │
│ - "What actions do you take this round?"                    │
│ - "You're in a conversation with Helmsman. Your turn."      │
│ - "Evaluate this arms sale proposal from Ruthenia."         │
│ - "The round just ended. Here are results. Reflect."        │
│                                                             │
│ The instruction never tells the AI WHAT to decide.          │
│ Only what TYPE of decision is needed.                       │
└─────────────────────────────────────────────────────────────┘
```

### Autonomy Principles

**1. Goals are self-authored.**
The AI receives its role objectives from the brief, but it translates them into its OWN strategic plan in Block 4. It prioritizes, sequences, develops contingencies. After each significant event, it revises its plan — not because we tell it to, but because the plan is ITS OWN.

**2. Memory is self-curated.**
After each conversation or event, the AI decides: *"What from this is worth remembering?"* It might remember a betrayal but forget a pleasantry. It might note an economic trend but ignore a diplomatic nicety. This selectivity IS the AI's intelligence — a leader who remembers everything has no priorities.

**3. Decisions are never prescribed.**
We never say "you should attack" or "you should negotiate." The AI reasons from its identity + goals + memory + situation data and decides. If it decides to do nothing, that's valid. If it decides to betray an ally, that's valid too — if it serves the character's goals.

**4. The AI can surprise us.**
A well-initialized AI participant with rich identity, clear goals, and accurate situation data will sometimes make decisions that surprise the designers. This is a FEATURE. The Thucydides Trap emerges from the interaction of rational actors with different goals — if we script the AI, we kill the emergence.

**5. Information, not prescription.**
Layer 2 provides data, not advice. "Your GDP is declining at -3% and your treasury is near zero" — not "you should cut military spending." The AI draws its own conclusions.

### What Block 3 (Memory) IS and ISN'T

**IS:**
- The AI's own strategic notes
- Relationship assessments ("Helmsman is evasive, probably building toward Formosa action")
- Commitments made ("I promised Pathfinder continued sanctions")
- Lessons learned ("Trade war with Cathay hurt us more than expected")
- Key facts the AI deems important

**ISN'T:**
- A database of all available information (that's Layer 2)
- A transcript of all conversations (too expensive, unnecessary)
- A mirror of the world state (that's always provided fresh in Layer 2)
- Prescribed content (we never tell the AI what to remember)

### What Block 4 (Goals) IS and ISN'T

**IS:**
- The AI's own strategic brief (self-authored, 400-600 words)
- Ranked objectives with urgency assessment
- Concrete plans: who to talk to, what leverage to use, what sequence
- Contingency thinking: what if X fails?
- Timeline awareness: what must happen by when?

**ISN'T:**
- A task list we assign
- A fixed script of behavior
- Reactions to events (those happen in the moment)
- Static (it evolves as the AI learns and adapts)

### Token Budget Per Call Type

| Call type | Layer 1 | Layer 2 | Layer 3 | Total |
|-----------|:-------:|:-------:|:-------:|:-----:|
| Strategic reasoning (start of round) | 4K | 6K (broad world state) | 300 | ~10K |
| Budget decision | 4K | 3K (economic data + rules) | 300 | ~7K |
| Military decision | 4K | 4K (positions + combat rules) | 300 | ~8K |
| Conversation turn | 4K | 2K (counterpart + relationship) | 200 + history | ~8K |
| Transaction evaluation | 4K | 2K (own state + proposal terms) | 300 | ~6K |
| Post-conversation reflection | 4K | 1K (transcript summary) | 300 | ~5K |
| Active loop ("what to do now?") | 4K | 2K (situation summary) | 200 | ~6K |

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

## 14a. Implementation Files (Current State, 2026-04-04)

The module lives at `app/engine/agents/`. This section documents what exists in code
right now (as opposed to the design vision in sections 1–14). Line counts are approximate.

### `leader.py` (~690 lines) — `LeaderAgent` class

The main class implementing the DET_C1 C6 abstract interface for heads of state.

**Constructor:** `__init__(role_id: str)` — creates an empty agent with a `CognitiveState`,
status `"uninitialized"`, and empty conversation history. No LLM calls here.

**`initialize(sim_config, world_state)` (async):**
1. Loads role from `roles.csv` and country from `countries.csv` via `profiles.load_role()` / `load_country_context()`.
2. Populates Block 1 (rules) by formatting the `RULES_TEMPLATE` constant with the role's powers, objectives, intelligence pool, and ticking clock. The template enforces the **SIM-names-only** rule (Columbia, Cathay, Sarmatia, etc.) directly in the prompt.
3. Generates Block 2 (identity) via `_generate_identity()` — a T=0.85 LLM call using the identity-generation prompt from `profiles.build_identity_prompt()`.
4. Sets Block 3 relationships from `world_state["relationships"]` mapped to numeric trust scores (allied=0.8, hostile=-0.6, at_war=-1.0, etc.).
5. Generates Block 4 (goals & strategy) via `_generate_goals()` — a T=0.7 LLM call producing a ~400–600-word strategic brief (ranked objectives, strategy, relationships, risks, timeline).

**`initialize_sync(identity_text, world_state)`:** Synchronous variant — no LLM calls, identity either passed in or filled with a stub. Used by tests.

**4-block cognitive model integration:** All four blocks live in `self.cognitive: CognitiveState`. `_get_cognitive_blocks()` bundles them as a dict for the `decisions` and `transactions` modules.

**DET_C1 C6 abstract interface — 10 methods implemented:**

| Method | Implementation |
|---|---|
| `initialize()` | Above — async, with LLM |
| `get_cognitive_state()` | Delegates to `self.cognitive.snapshot()` |
| `get_state_history()` | Delegates to `self.cognitive.get_history()` |
| `chat(message)` | One message within a live conversation; appends to `_conversation_history`; calls LLM with system = identity + memory + goals |
| `start_conversation(counterpart)` / `end_conversation()` | Open/close the conversation; `end_conversation()` runs a single reflection LLM call (T=0.3) that returns JSON with `memory_update`, `relationship_change`, `goals_update`, `identity_update`; the agent self-curates what to remember |
| `submit_mandatory_inputs(round_context)` | Calls `decisions.submit_all_mandatory()` to produce budget / tariffs / sanctions / OPEC / deployment; records each in memory |
| `decide_action(time_remaining, new_events, round_context)` | Proactive active-loop dispatch to `decisions.decide_action_dispatch()`; returns an action dict or `None` (wait) |
| `react_to_event(event)` | **STUB** — returns `None`; flagged as TODO Phase 3B |
| `generate_conversation_message(conversation_context)` | Produces next bilateral turn; uses `conversations.CONVERSATION_SYSTEM_TEMPLATE` + `_transcript_to_messages`; T=0.8, 300 tokens; detects `[END CONVERSATION]` marker |
| `evaluate_proposal(proposal, counterpart_context)` | Delegates to `transactions.evaluate_transaction()`; accepts dict or `TransactionProposal`; records accept/reject/counter in memory |
| `propose_transaction(counterpart, transaction_type, world_state)` | Delegates to `transactions.propose_transaction()`; records in memory |
| `start_round(round_num, world_state_visible, events_since_last)` | Updates immediate memory with oil price and war count, ingests events |
| `reflect_on_round(round_results)` | LLM reflection (T=0.5) on GDP/inflation/stability/support/oil; appends to Block 4 goals |

**Module dependencies:**
- `profiles.py` — `load_role()`, `load_country_context()`, `build_identity_prompt()`
- `memory.py` — `CognitiveState` (4 blocks + versioning)
- `decisions.py` — `submit_all_mandatory()`, `decide_action_dispatch()`
- `conversations.py` — `CONVERSATION_SYSTEM_TEMPLATE`, `_transcript_to_messages`, `END_MARKER`
- `transactions.py` — `propose_transaction()`, `evaluate_transaction()`, `TransactionProposal`

### `profiles.py` (~150 lines) — Role data loading + identity prompt

Pure CSV loader, no LLM or DB. Points at `2 SEED/C_MECHANICS/C4_DATA/roles.csv` and `countries.csv`.

- `load_role(role_id) -> dict` — single role lookup; raises `ValueError` if missing.
- `load_all_roles() -> dict[str, dict]` — all 40+ roles.
- `load_heads_of_state() -> dict[str, dict]` — filter to `is_head_of_state=true` (21 leaders).
- `load_country_context(country_id) -> dict` — full country starting data (GDP, treasury, stability, oil producer flags, military units, nuclear/AI level, at_war_with, etc.).
- `_parse_role(row)` — parses semicolon-separated `powers`, `objectives`, plus cards (sabotage, cyber, disinfo, election_meddling, assassination).
- `IDENTITY_GENERATION_PROMPT` constant — 4-element template (personality traits, communication style, emotional drivers, strategic tendency) generating 3–4 sentence second-person identity.
- `build_identity_prompt(role, country) -> str` — fills the template.

### `memory.py` (~230 lines) — `CognitiveState` (4 blocks + versioning)

Pure in-memory cognitive state; no DB writes. Version history kept in `_history: list[dict]`.

- `__init__(role_id)` — initializes all 4 blocks empty, `version=0`.
- `snapshot() -> dict` — returns a deep-copied view of current state with timestamp.
- `save_version(reason)` — appends snapshot to `_history`, increments `version`.
- `get_history() -> list[dict]` / `get_version(version) -> dict | None` — historical inspection.

**Block 1 (Rules):** `set_rules(text)` — called once at init.

**Block 2 (Identity):** `set_identity(text)` — called once, saves version tagged `"identity_generated"`.

**Block 3 (Memory):** structured dict with keys `immediate`, `round_history`, `strategic`, `relationships`, `conversations_this_round`, `decisions_this_round`.
- `update_immediate(text)` — overwrites "just now" slot.
- `add_conversation(counterpart, summary, trust_change)` — appends to this-round list, clamps relationship trust to [-1,1], saves version.
- `add_decision(action_type, summary)` — appends to this-round decisions.
- `end_round(round_num, round_summary)` — archives conversations + decisions into `round_history`, resets round accumulators, saves version.
- `set_relationships(dict)` — initial seed from world_state.

**Block 4 (Goals):** plain-text-first design (LLM-generated strategic brief).
- `set_goals_text(text)` / `update_goals_text(text, reason)` — overwrites Block 4 as `{"_text": text}`.

**Context builders for LLM:**
- `get_memory_text()` — formats Block 3 as markdown: "Just now", "This round conversations", "My decisions this round", last 3 rounds in detail + older rounds compressed, relationships with ally/friendly/neutral/tense/hostile labels, strategic facts.
- `get_goals_text()` — returns Block 4 as `"## Goals & Strategy\n\n{text}"` (or legacy structured fallback).

### `decisions.py` (~1013 lines) — 8 decision types

Implements the Three-Layer Context Model: Layer 1 = cognitive blocks (identity + memory + goals), Layer 2 = task-specific context built here, Layer 3 = concise decision instruction.

**Utility:** `_parse_json(text)` — robust JSON extractor from LLM output (strips markdown fences, finds matching braces/brackets, recovers from malformed output).

**Layer 2 context builders** (one per decision type):
- `build_budget_context(country, round_context)` — GDP, revenue estimate, treasury, inflation, debt, stability, maintenance cost, current budget allocation.
- `build_tariff_context(country, round_context)` — current tariff levels to all partners, trade volumes, economic impact guidance.
- `build_sanction_context(country, round_context)` — coalition dynamics, current sanctions matrix, cost-to-imposer (30–50%).
- `build_opec_context(country, round_context)` — oil price, production quotas, OPEC cohesion (members only).
- `build_military_context(country, round_context)` — ground/naval/air inventory, mobilization pool, ongoing wars, blockades, combat odds.
- `build_covert_context(country, role, round_context)` — intelligence pool remaining, cards available (sabotage/cyber/disinfo/election/assassination), target candidates.
- `build_political_context(country, round_context)` — stability/support trends, regime type actions (propaganda/repression/arrests), election calendar.
- `build_active_loop_context(country, role, round_context)` — time remaining, new events, open proposals, relationship snapshots (for the proactive decide_action loop).

**8 decision functions** (all async; each calls the matching context builder, composes system prompt via `_build_system_prompt(cognitive_blocks, layer2_context)`, calls LLM with JSON-structured output, and parses via `_parse_json`):

| # | Function | Output schema |
|---|---|---|
| 1 | `decide_budget` | `{social_pct: 0.5-1.5, military_coins: float, tech_coins: float, reasoning: str}` |
| 2 | `decide_tariffs` | `{changes: {country_id: level_0_to_3}, reasoning: str}` |
| 3 | `decide_sanctions` | `{changes: {country_id: level_0_to_3}, reasoning: str}` |
| 4 | `decide_opec` | `{production: "min"\|"low"\|"normal"\|"high"\|"max", reasoning: str}` |
| 5 | `decide_military` | `{actions: [{type, from_zone, to_zone, units, ...}], reasoning: str}` |
| 6 | `decide_covert` | `{ops: [{type, target, cards_used}], reasoning: str}` |
| 7 | `decide_political` | `{actions: [propaganda\|repression\|arrest\|public_statement], reasoning: str}` |
| 8 | `decide_active_loop` | `{action_type, target, content, reasoning}` — for the proactive in-round loop |

**Entry points used by `LeaderAgent`:**
- `submit_all_mandatory(cognitive_blocks, country, role, round_context)` — runs decisions 1–4 (and 5 in stub form) in sequence.
- `decide_action_dispatch(cognitive_blocks, country, role, round_context, time_remaining, new_events)` — uses `decide_active_loop`, then may fan out to `decide_military`, `decide_covert`, conversation-request dispatch, etc.

**System prompt composer:** `_build_system_prompt(cognitive_blocks, layer2_context)` stacks `block1_rules` → `block2_identity` → memory text → goals text → layer2_context → "Return JSON only."

### `conversations.py` (~500 lines) — Bilateral conversation engine

**`ConversationResult` dataclass** — `transcript: list[{speaker_role_id, text}]`, `turns`, `ended_by`, `intent_notes: {role_a, role_b}` (moderator-only), `reflections: {role_a, role_b}`.

**`ConversationEngine` class:**

- `generate_intent_note(agent, counterpart) -> str` — one LLM call using `INTENT_NOTE_PROMPT` (5-point private plan: objectives / what to share vs. withhold / approach / red lines / what to learn). Private to the agent, never revealed in dialogue. Uses the agent's Block 2 identity + memory + goals + current relationship score.

- `run_bilateral(agent_a, agent_b, max_turns=8, on_turn=None, extra_context=None) -> ConversationResult`:
  1. Generate intent notes for both agents (parallel).
  2. Loop up to `max_turns`, alternating speakers. Each turn calls `_generate_turn(...)`.
  3. Each produced turn is appended to the transcript; if an `on_turn` callback is provided (sync or async), it is invoked with the turn data for **live streaming** (Public Display integration).
  4. If an agent emits `[END CONVERSATION]` (or `[END]`), the loop stops and `ended_by` is set to that role_id; otherwise `ended_by = "max_turns"`.
  5. Finally calls `_reflect_both(...)` to update each agent's blocks.

- `_generate_turn(agent, counterpart, transcript, intent_notes, extra_context)` — builds system prompt from `CONVERSATION_SYSTEM_TEMPLATE` (identity + counterpart identification + 4-turn budget + speaking rules + intent notes + memory + goals). Enforces "Use ONLY SIM names" and "Don't use assistant language". Temperature 0.8, max 300 tokens, <100 words per turn.

- `_reflect_both(agent_a, agent_b, transcript)` — parallel reflection calls. Each agent independently decides what to remember (memory update, trust change, goals update, identity update) via `agent.cognitive.add_conversation(...)` and goal-text append.

**Helpers:**
- `_transcript_to_messages(transcript, speaker_role_id)` — converts shared transcript into `[{role: "user"|"assistant", content}]` from the perspective of the current speaker.
- `_format_transcript`, `_trust_label`.

### `transactions.py` (~585 lines) — Transaction system

**`TransactionProposal` dataclass** — `id` (auto `txn_<uuid8>`), `type`, `proposer_role_id`, `proposer_country_id`, `counterpart_role_id`, `counterpart_country_id`, `terms: dict`, `status: "proposed"|"accepted"|"rejected"|"countered"|"executed"`, `reasoning`, `counter_terms`, `evaluation_reasoning`. `to_dict()` serializes to DET_C1 event schema.

**10 transaction types** (`TRANSACTION_TYPES` set): `coin_transfer`, `arms_sale`, `arms_gift`, `tech_transfer`, `basing_rights`, `ceasefire`, `peace_treaty`, `alliance`, `trade_agreement`, `sanctions_coordination`. Flags: `REQUIRES_WAR = {ceasefire, peace_treaty}`, `RESOURCE_TRANSACTIONS = {coin_transfer, arms_sale, arms_gift, tech_transfer}`.

**Core flow:**

- `propose_transaction(cognitive_blocks, agent_country, agent_role, counterpart_country, counterpart_role, world_state, transaction_type=None) -> TransactionProposal` — async LLM call. Uses `_build_propose_context()` to describe the relationship, what both sides have, and what's plausible. Agent picks type (or uses hint) and terms. Returns a `TransactionProposal` with `status="proposed"`.

- `evaluate_transaction(cognitive_blocks, agent_country, agent_role, proposal) -> dict` — async. Uses `_build_evaluate_context(proposal)` to explain the offer from the counterpart's POV. LLM returns `{decision: "accept"|"reject"|"counter", counter_terms: dict|None, reasoning: str}`. Sets `proposal.status` accordingly.

- `execute_transaction(proposal, countries_state, wars) -> dict` — **synchronous, simplified state mutation**. Handles:
  - `coin_transfer` — moves treasury from proposer to counterpart.
  - `arms_sale` / `arms_gift` — adjusts military unit counts via `_transfer_units()`, and treasury for sales.
  - `tech_transfer` — nuclear/AI level deltas.
  - `ceasefire` / `peace_treaty` — checked against `_are_at_war(country_a, country_b, wars)` and removes from `wars` list.
  - `basing_rights`, `alliance`, `trade_agreement`, `sanctions_coordination` — recorded as agreements (no deep state mutation yet).
  Returns `{executed: bool, changes: list[str], error: str|None}` and sets `proposal.status="executed"`.

- `run_transaction_flow(proposer_agent, counterpart_agent, world_state, transaction_type=None) -> TransactionProposal` — convenience: propose → evaluate → (if accepted) execute, returning the final proposal object.

**CURRENT LIMITATION:** `execute_transaction()` performs **simplified in-memory state mutations only**. It does not model downstream effects (trade flow changes from `trade_agreement`, stability impact of `alliance`, basing-rights influence on force projection, etc.). A future **Transaction Engine** (separate module) will replace this with proper effect propagation through the economic/military/political engines.

### `runner.py` (~1084 lines) — Round runner + Full SIM

The unmanned-mode orchestrator. **No database**; everything is in-memory, mirroring `tests/layer3/run_scenarios.py`.

**Data models:**
- `RoundReport` — `round_num`, `actions_taken: {role_id: [actions]}`, `conversations`, `transactions`, `mandatory_inputs`, `engine_results`, `nous_adjustments`, `agent_reflections`, `log`, `duration_seconds`. Has `summary()` text.
- `SimReport` — `rounds: [RoundReport]`, `num_rounds`, `agents: {role_id: final_info}`, `total_duration_seconds`.

**Data loading:** `load_countries_from_csv()` reads `2 SEED/C_MECHANICS/C4_DATA/countries.csv` and returns the same flat-dict format as `profiles.load_country_context()` but for all 21 countries at once. `_build_engine_countries(flat)` reshapes into the structured form the economic/political engines expect. `_build_default_world_state(round_num)` seeds oil price, wars, relationships, and round metadata.

**`run_round(round_num, agents, countries_flat, wars, round_state, nous) -> RoundReport` (6 phases):**
1. **Start round** (`_start_round`) — builds per-round context via `_build_round_context`, calls `agent.start_round()` on every agent (parallel).
2. **Active loop** (`_active_loop`) — time-boxed proactive phase. Agents call `decide_action()`; actions include conversation requests (dispatched to `conversations.ConversationEngine.run_bilateral`), transaction proposals (dispatched to `transactions.run_transaction_flow`), military/covert/political actions.
3. **Mandatory submission** (`_mandatory_submission`) — every HoS submits budget/tariffs/sanctions/OPEC via `agent.submit_mandatory_inputs()`. `_default_mandatory()` provides a safe fallback if an agent fails.
4. **Engine processing** (`_run_engines`) — calls the **economic engine** and **political engine** with the assembled state, receives GDP/inflation/stability/support updates, reshapes outputs for agent consumption. Applies sanctions, tariffs, OPEC production, budget effects.
5. **NOUS judgment** (`_run_nous`) — passes round_state + engine output to the **NOUS** meta-judge for adjustments (narrative coherence, cascade effects, random events).
6. **Reflection** (`_reflect`) — all agents call `reflect_on_round()` in parallel; each updates its own Block 4. `_sync_to_flat_countries()` writes engine deltas back to the flat country dict for next round.

**`run_full_sim(num_rounds=6, tier=1, use_real_llm=True) -> SimReport`:**
- Loads `countries.csv`, calls `load_heads_of_state()` for all 21 HoS roles.
- Instantiates 21 `LeaderAgent`s and runs `initialize()` for each (parallel).
- Builds initial `wars`, `round_state`, NOUS instance.
- Loops `run_round` for `num_rounds` rounds.
- Returns `SimReport` with cumulative stats.

**Integration with engines and NOUS:**
- Imports are **lazy** (inside `_run_engines`, `_run_nous`) to avoid module-load-time dependencies.
- Economic engine: `engine.engines.economic` via dict-based API (state-in → state-out).
- Political engine: `engine.engines.political` — stability/support/election dynamics.
- NOUS: `engine.services.nous` — narrative judge layer.

### Module-wide implementation notes

- **All LLM imports are lazy** (inside functions): `from engine.services.llm import call_llm` and `from engine.config.settings import LLMUseCase` are not imported at module top, to avoid pulling `pydantic_settings` (and its env-validation chain) at module load time. Tests and CSV-only paths can import `leader.py` / `runner.py` without a live environment.
- **SIM names only** — the RULES_TEMPLATE and CONVERSATION_SYSTEM_TEMPLATE both explicitly list the 20 country SIM names (Columbia not USA, Cathay not China, etc.) and character-name references, enforced in prompts at every LLM call.
- **No direct DB dependency** anywhere in `app/engine/agents/`. Profile data comes from CSVs. Cognitive state lives in memory. This matches the Layer 3 test runner architecture and enables fast unmanned runs without Supabase.

---

## 14b. Prompts in `sim_config` (Database-Seeded)

Seven prompt templates are seeded into the `sim_config` table (per-SIM configurable, overridable per run). These live in the database so SIM designers can tune them without code changes. The agent module currently references them indirectly via the prompts embedded in code; full DB-driven loading is a Sprint 3 task.

| Key | Purpose | When Used | Temp | Max Tokens |
|---|---|---|:---:|:---:|
| `metacognitive_architecture` | Component of Block 1 (Rules). Describes the 4-block cognitive model to the agent so it can reason about its own memory and goal updates (metacognition). | Loaded into Block 1 at `initialize()`. | n/a | n/a |
| `identity_generation` | Template for generating Block 2 (Identity) from role brief — 4 elements: personality, communication style, emotional drivers, strategic tendency. | Once, at `initialize()` → `_generate_identity()`. | 0.85 | 300 |
| `conversation_behavior` | Speaking rules for bilateral turns: 4-message budget, direct style, no assistant language, concrete proposals, SIM names only. | Every conversation turn, as system prompt. | 0.8 | 300 |
| `intent_note_generation` | 5-point private plan before a meeting (objectives, share/withhold, approach, red lines, what to learn). | Once per agent at the start of each bilateral conversation. | 0.7 | 400 |
| `reflection_block_3` | Post-conversation reflection: what to remember in memory, trust delta with counterpart. | After each conversation ends. | 0.3 | 500 |
| `reflection_block_4` | Per-round goal revision: ranked objectives, strategy adjustment, timeline pressure. | After each round's engine results arrive (`reflect_on_round`). | 0.5 | 300 |
| `meeting_decision` | Active-loop decision: should the agent request a conversation now, with whom, with what intent? | During `decide_active_loop`, multiple times per round. | 0.7 | 500 |

**Note:** These templates are currently mirrored in Python constants (`RULES_TEMPLATE`, `IDENTITY_GENERATION_PROMPT`, `CONVERSATION_SYSTEM_TEMPLATE`, `INTENT_NOTE_PROMPT`, reflection prompts in `leader.py`, goal prompt in `_generate_goals()`). A Sprint 3 refactor will load them from `sim_config` at runtime to enable per-SIM tuning without redeploys.

---

## 14c. Current Limitations

The module is functional end-to-end for unmanned runs but has known gaps:

- **Block 1 (Rules) is minimal.** It currently contains the role's own powers, objectives, and a paragraph of mechanics. It **lacks**: the full participant roster (who else is in the SIM, their countries and titles), the map (zones, chokepoints, borders), the SIM structure (round flow, phase ordering, event timeline), and the metacognitive awareness prompt (how to reason about its own 4 blocks). This is a **critical gap** — agents currently reason in a partial vacuum about the broader simulation.
- **Military decisions lack map integration.** `decide_military` produces action intents (attack, blockade, air strike) but has no zones, no unit deployment graph, no supply-line model. The military engine is not yet wired to a map module.
- **Covert operations produce no real outcomes.** `decide_covert` selects ops and consumes cards, but there is no Live Action Engine to resolve success/detection/effect. Sabotage, espionage, cyber, and disinformation are currently intent-only.
- **Transactions execute simplified state changes.** `execute_transaction()` mutates treasury and unit counts directly; it does not propagate effects through the economic/political engines (e.g., a `trade_agreement` doesn't actually change trade flows; an `alliance` doesn't change force-projection calculations). A dedicated **Transaction Engine** is needed.
- **Nothing persists to DB during runs.** Cognitive state, conversation transcripts, transactions, and round reports all live in memory only. Crash = loss. DB writes are a Sprint 3/4 task (tables already exist per DET_B1).
- **Not yet tested at scale.** The target is 21 agents × 6 rounds × full active loop. Current validation is on small subsets (2-3 agents, 1-2 rounds). Expected duration at full scale: ~20–40 min per run, ~$5–8 per run — see Section 15 cost estimate, but not yet empirically confirmed.

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
