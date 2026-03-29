# AI Conversation & Negotiation
## Thucydides Trap SIM — SEED Specification
**Version:** 1.0 | **Date:** 2026-03-28

---

## Principle

AI participants negotiate, communicate, and build relationships the same way human participants do — through conversation. The conversation system reproduces the KING SIM's proven architecture, extended for TTT's richer action space and continuous round activity.

**Core design insight from KING (March 2026):** Trust the AI's natural reasoning. Remove behavioral constraints ("MUST be aggressive") — they produce rigid, repetitive characters. Instead, give the AI a rich identity, clear interests, and accurate situational awareness, then let it reason naturally about what to do.

---

## Architecture Overview

```
┌────────────────────────────────────────────────────────────┐
│              AI CONVERSATION SYSTEM                         │
│                                                             │
│  ┌──────────────────┐    ┌──────────────────┐              │
│  │  4-BLOCK          │    │  CONVERSATION     │              │
│  │  COGNITIVE MODEL  │───▶│  ENGINE           │              │
│  │                   │    │                   │              │
│  │  Block 1: Rules   │    │  Intent notes     │              │
│  │  Block 2: Identity│    │  Turn management  │              │
│  │  Block 3: Memory  │    │  Transcript       │              │
│  │  Block 4: Goals   │    │  Post-reflection  │              │
│  └──────────────────┘    └──────────────────┘              │
│           ↕                        ↕                        │
│  ┌──────────────────┐    ┌──────────────────┐              │
│  │  REFLECTION       │    │  VOICE ENGINE     │              │
│  │  SERVICE          │    │  (optional)       │              │
│  │                   │    │                   │              │
│  │  Block updates    │    │  Speech synthesis  │              │
│  │  after events     │    │  Speech-to-text   │              │
│  │  Priority queue   │    │  Real-time dialog  │              │
│  └──────────────────┘    └──────────────────┘              │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

---

## The 4-Block Cognitive Model

Inherited from KING, proven in production. Each AI participant maintains persistent cognitive state:

### Block 1 — Fixed Context (never changes after initialization)

The rules of the game and how the AI should think:
- Metacognitive framework (how to perceive, reason, decide)
- Available actions and their mechanics (what this role CAN do)
- SIM rules relevant to this role (budget, combat, trade, organization membership)
- Behavioral guidelines ("speak naturally, reason from interests")

**TTT-specific:** Block 1 for an AI Wellspring (Saudi Arabia) includes OPEC+ production mechanics, oil pricing, sanctions/tariff system, bilateral transaction rules, and this role's specific powers.

### Block 2 — Identity (updates rarely)

Who the AI IS. Personality, values, speaking style, factional alignment. Generated from the role seed during initialization.

**TTT-specific:** Wellspring is "pragmatic, patient, leverage-obsessed" — hedging between Columbia and Cathay, using oil as leverage, pursuing BRICS+ diversification while maintaining the Columbia security umbrella.

**Key KING lesson:** Block 2 (not Block 1) is the primary context used during conversations. Block 1 was found to drown personality in rules when included in conversation prompts.

### Block 3 — Memory (updates frequently)

What the AI remembers. Relationships, promises, deals, betrayals, intelligence, meeting outcomes:

*"Helmsman offered a 5-year oil purchase guarantee in exchange for BRICS+ currency commitment. Dealer threatened secondary sanctions if we join BRICS+ currency. Forge privately indicated Teutonia would not enforce sanctions on oil."*

### Block 4 — Goals & Strategy (updates each round + after major events)

What the AI wants and how it plans to get it:

*"Priority 1: Keep oil price above 80 by coordinating OPEC+ restraint. Priority 2: Delay BRICS+ currency commitment until R4 — maintain leverage. Priority 3: Acquire air defense from Columbia. Contingency: If Gulf Gate blockaded, pivot to maximum production."*

### Block Updates

- **Atomic versioning** — all versions preserved, rollback supported
- **Priority 1 (immediate):** Direct proposals, combat alerts, coup attempts, phase changes
- **Priority 2 (batched):** World updates, others' public actions, economic changes — combined into single reflection call

---

## Conversation Types

### 1. Bilateral Negotiation (AI ↔ Human or AI ↔ AI)

The most common interaction. Proposing deals, building trust, making threats, hammering out terms.

**Flow:**
1. AI generates **intent notes** from current cognitive state (what it wants, what it'll offer, red lines, tone)
2. Conversation proceeds turn-by-turn
3. AI adapts position based on what counterpart says
4. After conversation ends, **transcript triggers reflection** (Block 3 + 4 update)

**AI capabilities in negotiation:**
- **Propose** — initiate a deal, suggest terms
- **Counter** — reject and propose alternatives
- **Bluff** — misrepresent intentions, exaggerate capabilities (emerges naturally from reasoning about interests — not from explicit instructions)
- **Commit** — make promises, accept terms (recorded in Block 3)
- **Stall** — delay decisions, change subject when strategically appropriate
- **Walk away** — end unproductive conversations

### 2. Multi-Party Meetings (Organization sessions, alliance caucuses)

NATO sessions, BRICS+ summits, OPEC+ meetings, peace conferences.

**KING-proven approach:** The AI uses the standard conversation interface with behavioral framing: "YOU ARE A DIPLOMAT IN A MULTILATERAL SETTING." The AI listens more than it speaks, restrains itself from interjecting unless directly addressed or when it has something genuinely important to contribute, and tracks other speakers' positions.

This is simpler than building dedicated multi-party orchestration and mirrors how real diplomats behave — mostly listening, choosing moments carefully.

### 3. Public Speeches & Statements

AI participants can make public speeches (per C5 protocol). These are generated through the conversation engine with the context that the statement is PUBLIC and will be heard by all participants.

AI public statements are **automatically transcribed** and become public commitments (per C5).

### 4. AI-to-AI Conversations

When both parties are AI-operated. These run as automated turn-based exchanges:

| Parameter | Value |
|-----------|-------|
| **Max turns per participant** | 8–12 (configurable) |
| **Max total messages** | 16–24 |
| **Delay between messages** | 2–2.5 seconds (natural pacing) |
| **Early stop** | AI can decide conversation is complete |
| **Context caching** | Enabled — reduces API costs ~85% for multi-turn exchanges |

**AI-to-AI pacing question:** Should these run in fast mode (more turns, shorter messages) or at realistic pace? Current design: fast mode for efficiency, with transcript available for human review.

### 5. Receiving Messages (Asynchronous)

AI processes incoming messages in context of sender's identity and current situation. May respond immediately, with deliberate delay, or not at all — based on strategic reasoning.

---

## Intent Notes

Before entering any conversation, the AI generates intent notes from its current cognitive state:

```
INTENT NOTE — Bilateral with Helmsman (Cathay)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WHAT I WANT:
- 5-year oil purchase guarantee at $90/barrel floor
- Cathay's support for OPEC+ production restraint

WHAT I CAN OFFER:
- Priority supply allocation to Cathay
- BRICS+ currency commitment (my biggest card — use carefully)
- Support for Cathay's UNSC position

RED LINES:
- Will NOT commit to exclusive Cathay alignment
- Will NOT accept price below $80
- Will NOT break Columbia basing agreement (yet)

WHAT I COULD TRADE TO GET WHAT I WANT:
- Partial BRICS+ commitment (trade settlement only, not reserves)
- Support on Formosa issue in UNGA (verbal, not binding)

TONE:
- Warm but non-committal. Let them make the bigger offers first.
```

Intent notes are **not shown to other participants** — they are internal planning documents that guide the AI's conversation without being rigidly prescriptive.

---

## Conversation Engine Implementation

### Conversation Lifecycle

```
1. INITIALIZATION
   ├─ Create conversation record
   ├─ Load participants (roles + cognitive blocks)
   └─ Generate intent notes for AI participants

2. CONTEXT ASSEMBLY
   ├─ Block 2 (identity) as primary personality context
   ├─ Block 3 (memory of this counterpart specifically)
   ├─ Block 4 (current goals relevant to this interaction)
   ├─ Intent notes
   └─ Conversation history so far

3. CONVERSATION LOOP (turn-by-turn)
   ├─ Determine current speaker
   ├─ Build prompt with conversation context
   ├─ Generate message via LLM
   ├─ Validate (length, coherence)
   ├─ Store message
   ├─ Check end conditions
   └─ Next speaker

4. POST-CONVERSATION
   ├─ Format full transcript
   ├─ Trigger reflection for all AI participants
   │   ├─ Block 3 update (new memory of what was discussed)
   │   └─ Block 4 update (strategy adjustment based on new info)
   └─ If deal discussed → may follow up with formal transaction
```

### Context Caching (KING-proven optimization)

For multi-turn conversations, the cognitive blocks and participant info are cached at conversation start. Only the growing message history is sent fresh each turn.

**Cost savings:** Without caching: ~50,000 tokens × 20 turns = 1M input tokens. With caching: 50,000 cached + 20 × 5,000 fresh = 150,000 tokens. **~85% reduction.**

### LLM Configuration

| Parameter | Value |
|-----------|-------|
| **Primary model** | Best available reasoning model (Gemini/Claude) |
| **Reflection model** | Fast model (for high-frequency block updates) |
| **Temperature** | 0.7 (conversations), 0.85 (identity generation for diversity) |
| **Max tokens per message** | 1,000 (conversations), 6,000–8,000 (block generation) |
| **Model mixing** | Supported — stronger model for critical decisions, faster model for routine |

The system is **LLM-agnostic** — provider abstraction allows switching models during the SIM. KING proved this works in production with Gemini; TTT may use Claude for complex geopolitical reasoning.

---

## Autonomous Action Loop

The key extension from KING. During Phase A, AI participants don't just wait — they proactively pursue goals.

```
ROUND STARTS
    │
    ▼
DELIBERATE: "What are my priorities this round?"
    │
    ▼
┌──────────────────────────────────────┐
│         ACTIVE ROUND LOOP            │
│                                      │
│  1. Check incoming events/messages   │
│     → React if needed                │
│                                      │
│  2. Assess current situation         │
│     → Has something changed?         │
│     → Any deadlines approaching?     │
│                                      │
│  3. Evaluate action opportunities    │
│     → Should I contact someone?      │
│     → Should I make a trade?         │
│     → Should I initiate an action?   │
│                                      │
│  4. Execute highest-priority action  │
│                                      │
│  5. Wait (30-90 seconds)             │
│     → Check for new events → loop    │
│                                      │
│  INTERRUPT: Incoming event breaks    │
│  the wait → immediate processing     │
└──────────────────────────────────────┘
    │
    ▼
ROUND DEADLINE → Submit routine settings
    │
    ▼
WORLD UPDATE → Reflect on results
    │
    ▼
DEPLOYMENT → Place new units
```

**Loop frequency** is configurable by the moderator to match game pace. In a quiet round, AI is mostly proactive (initiating). During a crisis, mostly reactive (responding).

---

## Reflection System

After significant events, the AI updates its cognitive blocks:

| Trigger | Blocks Updated | Priority |
|---------|:-------------:|:--------:|
| Meeting/conversation ended | 3, 4 | Immediate |
| Phase/round change | 4 | Immediate |
| Direct proposal received | 3, 4 | Immediate |
| Combat alert / coup attempt | 2, 3, 4 | Immediate |
| World state update | 4 | Batched |
| Others' public actions | 3 | Batched |
| General announcements | 3 | Batched |

**Batched processing:** Priority 2 items accumulate (up to 10 items or 5 minutes), then processed in a single reflection call. Reduces LLM costs while maintaining awareness.

**Atomic save:** All block updates use database transactions to prevent race conditions. Every version preserved for rollback and post-game analysis.

---

## Voice Engine (Optional)

For face-to-face interaction between human and AI participants:

1. Human approaches AI terminal, initiates conversation
2. AI generates intent notes based on cognitive state + who's approaching
3. Voice connection via speech synthesis API (ElevenLabs or equivalent)
4. Real-time spoken conversation — both sides heard live
5. Dual-channel transcript captured (human speech-to-text + AI text)
6. Post-conversation: reflection triggers, commitments tracked

Each AI character gets a **distinct voice profile** — different timbre, accent, speaking pace. Wellspring sounds different from Pyro who sounds different from Citadel.

**Fallback:** Chat-only mode. Same cognitive pipeline, text I/O instead of voice.

---

## KING Inheritance & TTT Extensions

| Component | KING (proven) | TTT (extended) |
|-----------|:------------:|:--------------|
| 4-block cognitive model | ✅ Blocks 1–4, JSONB, atomic versioning | Same. Block 4 extended for multi-round strategic planning |
| Initialization pipeline | ✅ 4-stage sequential | Same. TTT-specific rules and roles |
| Reflection system | ✅ Event-triggered, priority queue | Same. More event types, higher throughput (~5× events/round) |
| Conversation manager | ✅ Round-robin turns, context caching | Extended: more types (bilateral, multilateral, org meetings). Multi-thread management |
| Voice synthesis | ✅ ElevenLabs, intent notes, transcripts | Same approach. Per-character voice profiles |
| Decision services | ✅ Vote, King decisions | Massively expanded: budget, tariffs, sanctions, military, diplomatic, covert |
| **Autonomous action loop** | ❌ Minimal | **NEW:** Continuous proactive loop during rounds |
| **Module interface protocol** | ❌ Tightly coupled | **NEW:** Standardized API for SIM-agnostic reuse |
| **SIM adapter layer** | ❌ Not separated | **NEW:** Translates TTT game state ↔ cognitive core |

### Key KING Lessons Applied

1. **Block 1 out of conversations** — inject rules at initialization, use Block 2 (identity) as primary conversation context
2. **No rigid behavioral constraints** — frame AI as "a political actor," let it choose approach (argue, compromise, concede, bluff)
3. **Higher temperature for diversity** — 0.85 for identity generation produces distinct personalities
4. **Plain speech nudge** — "clarity beats poetry in a political meeting" — reduces metaphor saturation
5. **Intent notes with trade awareness** — include "what I COULD trade to get what I want," not just red lines
6. **Learn from setbacks** — reflection prompts ask AI to adapt tactics, not just track goals

---

## Moderator Controls

The moderator can:
- View any AI participant's cognitive state (all 4 blocks)
- See reasoning behind any AI decision
- Adjust AI activity frequency (loop interval)
- Pause/resume any AI participant
- Override an AI decision before execution
- Inject information via manual reflection trigger
- Switch LLM models at runtime if performance requires

---

## Scaling Considerations

A full TTT session has ~10 AI-operated countries active simultaneously, each running its own cognitive loop.

| Concern | Mitigation |
|---------|-----------|
| API rate limits | Staggered loop intervals (not all 10 deliberate simultaneously) |
| Cost | Context caching (~85% reduction), batched reflections, model mixing (cheap model for routine, strong model for critical) |
| Latency | Graceful degradation — reduce AI activity frequency rather than fail |
| Consistency | All AI decisions logged with reasoning for post-SIM analysis |

---

## What This Specification Does NOT Do

- Does NOT define the World Model Engine (which calculates game physics — that's D1-D7)
- Does NOT define the web app UI (that's G2-G5)
- Does NOT replace human participants — AI operates countries that don't have human teams
- Does NOT give AI participants more information than a human in the same role would have

---

*The conversation system is the AI participant's primary interface with the world. Everything else — decisions, actions, strategy — flows through and is informed by conversation. Reproducing KING's proven architecture and extending it for TTT's richer domain is the path with lowest risk and highest confidence.*
