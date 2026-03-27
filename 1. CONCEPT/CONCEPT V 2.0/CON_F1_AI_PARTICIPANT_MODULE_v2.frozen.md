# Thucydides Trap SIM — AI Participant Module
**Code:** F1 | **Version:** 1.1 | **Date:** 2026-03-25 | **Status:** Conceptual architecture

---

## Purpose

This document defines the AI Participant Module — a **standalone, reusable system** that enables AI characters to participate in the SIM alongside human players. An AI participant must be indistinguishable in capability from a human participant: it sets goals, plans, negotiates, makes deals, manages resources, votes, deploys units, initiates actions, and reacts to events in real time.

The module is designed to be **separable from the TTT web app** so it can be reused in future SIMs with different domains, rules, and roles. The connection between the module and any host SIM is through a defined protocol, not through shared code.

---

## Design Principles

**1. A participant, not a calculator.** The AI participant is not the World Model Engine (which calculates economic outcomes, combat results, etc.). It is a player — with incomplete information, personal goals, relationships, and the capacity to be surprised, deceived, or outmaneuvered. It sees what a human in the same role would see, and no more.

**2. Trust the AI's reasoning.** Proven in KING SIM testing (March 2026): explicit behavioral constraints ("MUST be aggressive", "ALWAYS oppose X") produce rigid, repetitive characters. Instead, give the AI a rich identity, clear interests, and accurate situational awareness — then let it reason naturally about what to do. The geopolitical complexity of TTT demands genuine reasoning, not scripted behavior.

**3. Separate module, clear protocol.** The cognitive core (how the AI thinks) is SIM-agnostic. The SIM adapter (what the AI knows and can do in THIS game) is SIM-specific. The boundary between them is a defined interface. This means the cognitive architecture can improve independently of any particular SIM, and a new SIM can plug in by writing an adapter — not by rebuilding the AI system.

**4. Same rights, same constraints.** An AI participant has exactly the same action menu, the same information access, and the same authorization requirements as a human in the same role. If a human Shield needs Dealer's approval to attack, so does an AI Shield. If a human Wellspring can only see its own reserves, so can an AI Wellspring.

**5. Continuous presence during rounds.** Unlike the World Model Engine (which runs between rounds), the AI participant is active throughout Phase A — monitoring the situation, responding to proposals, initiating conversations, making real-time decisions. It operates on the same timeline as human players.

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                    AI PARTICIPANT MODULE                          │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐     │
│  │              COGNITIVE CORE (reusable)                  │     │
│  │                                                        │     │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐            │     │
│  │  │ PERCEIVE │→ │  THINK   │→ │   ACT    │            │     │
│  │  │          │  │          │  │          │            │     │
│  │  │ Process  │  │ Reflect  │  │ Decide   │            │     │
│  │  │ events,  │  │ on new   │  │ what to  │            │     │
│  │  │ filter,  │  │ info,    │  │ do, say, │            │     │
│  │  │ prioritze│  │ update   │  │ submit,  │            │     │
│  │  │          │  │ goals    │  │ propose  │            │     │
│  │  └──────────┘  └──────────┘  └──────────┘            │     │
│  │       ↑                            │                  │     │
│  │       │    ┌──────────────┐        │                  │     │
│  │       └────│   MEMORY     │←───────┘                  │     │
│  │            │              │                           │     │
│  │            │ 4-Block      │                           │     │
│  │            │ Cognitive    │                           │     │
│  │            │ State        │                           │     │
│  │            └──────────────┘                           │     │
│  │                                                        │     │
│  │  ┌──────────────┐  ┌──────────────┐                  │     │
│  │  │ CONVERSATION │  │   VOICE      │                  │     │
│  │  │ ENGINE       │  │   ENGINE     │                  │     │
│  │  │              │  │              │                  │     │
│  │  │ Text chat,   │  │ Speech via   │                  │     │
│  │  │ negotiations,│  │ ElevenLabs,  │                  │     │
│  │  │ meetings     │  │ face-to-face │                  │     │
│  │  └──────────────┘  └──────────────┘                  │     │
│  └────────────────────────────────────────────────────────┘     │
│                          ↕                                       │
│  ┌────────────────────────────────────────────────────────┐     │
│  │              SIM ADAPTER (TTT-specific)                 │     │
│  │                                                        │     │
│  │  Translates between:                                   │     │
│  │  • TTT game state  ←→  Cognitive Core inputs           │     │
│  │  • Core decisions  ←→  TTT action submissions          │     │
│  │  • TTT events      ←→  Core event notifications        │     │
│  └────────────────────────────────────────────────────────┘     │
│                          ↕                                       │
│              MODULE INTERFACE PROTOCOL                            │
│              (standardized API)                                   │
└──────────────────────────────────────────────────────────────────┘
                           ↕
┌──────────────────────────────────────────────────────────────────┐
│                    SIM WEB APP (TTT)                              │
│                                                                  │
│  Transaction Engine · Live Action Engine · World Model Engine    │
│  Database · UI · Communication channels                          │
└──────────────────────────────────────────────────────────────────┘
```

The architecture has three layers:

**Cognitive Core** — reusable across SIMs. Handles perception, reasoning, memory, conversation, and voice. Does not know what "GDP" or "ground units" are — it works with abstract concepts fed through the adapter.

**SIM Adapter** — specific to each SIM. Translates game state into the cognitive core's language and translates the core's decisions back into game actions. For TTT, this means converting military deployment maps, budget forms, tariff matrices, and sanctions tables into digestible briefings for the core, and converting the core's decisions ("increase naval production, set tariffs on Cathay to level 2") into structured submissions the web app accepts.

**Module Interface Protocol** — the standardized API between the module and any host SIM web app. Defines how the SIM sends world state, events, and action menus to the module, and how the module sends decisions and communications back.

---

## The Cognitive Core

### 4-Block Cognitive Model

Proven in KING SIM. Each AI participant maintains a persistent cognitive state across four blocks:

**Block 1 — FIXED CONTEXT (never changes after initialization)**

The rules of the game and how the AI should think. Assembled once at game start from:
- The AI's metacognitive framework (how to perceive, reason, decide)
- Available actions and their mechanics (what this role CAN do)
- SIM rules relevant to this role (budget process, combat mechanics, etc.)
- Behavioral guidelines (speak naturally, reason from interests, don't be artificially rigid)

In TTT, Block 1 for an AI playing Wellspring (Saudi Arabia) would include: OPEC+ production mechanics, oil pricing effects, sanctions/tariff system, bilateral transaction rules, and this role's specific powers (OPEC+ production decisions, coin transactions, organizational memberships).

**Block 2 — IDENTITY (updates rarely — only on major identity shifts)**

Who the AI IS. Personality, values, speaking style, factional alignment. Generated during initialization from the role definition, then updated only if something fundamental changes (e.g., a coup succeeds, a new leader takes over, the character's worldview is shattered by events).

In TTT: Wellspring is "pragmatic, patient, leverage-obsessed" — hedging between Columbia and Cathay, using oil as a weapon, pursuing BRICS+ currency diversification while maintaining the US security umbrella.

**Block 3 — MEMORY (updates frequently — after each significant interaction)**

What the AI remembers. Key relationships and their current state, promises made and received, deals struck, betrayals witnessed, intelligence obtained, meeting outcomes, reputation awareness.

In TTT: "Helmsman offered a 5-year oil purchase guarantee in exchange for BRICS+ currency commitment. Dealer threatened secondary sanctions if we join BRICS+ currency. Forge privately indicated Teutonia would not enforce sanctions on oil. Citadel requested missile defense purchase — considering."

**Block 4 — GOALS & STRATEGY (updates each round and after major events)**

What the AI wants and how it plans to get it. Current objectives, multi-round strategic plans, tactical priorities for this round, contingency plans, resource allocation intentions.

In TTT: "Priority 1: Keep oil price above 80 by coordinating OPEC+ restraint. Priority 2: Delay BRICS+ currency commitment until Round 4 — maintain leverage with both sides. Priority 3: Acquire air defense units from Columbia (2 units, willing to pay up to 15 coins). Contingency: If Gulf Gate is blockaded by Persia, pivot to maximum production to capture market share."

### Block Updates and Versioning

All block updates are atomic (database transaction prevents race conditions). Every version is preserved for rollback and analysis. Updates are triggered by events flowing through the perception system, with priority-based processing:

- **Priority 1 (immediate):** Direct proposals requiring response, combat alerts, coup/assassination targeting this role, round phase changes, vote sessions
- **Priority 2 (batched):** General world updates, other countries' public actions, economic indicator changes, news/narrative updates

Batched updates are combined and processed together (single reflection call), reducing AI API costs while maintaining situational awareness.

### Initialization Pipeline

A 4-stage sequential process creates each AI participant at game start:

1. **Assemble Block 1** from the SIM's rules, this role's action menu, and relevant mechanics
2. **Generate Block 2** (identity) — LLM creates the character's personality, speaking style, and self-concept from the role definition, with awareness of other roles in the same country and key international counterparts
3. **Generate Block 3** (memory) — LLM creates initial relationship map and situational awareness from the starting scenario brief (the same brief a human player would receive)
4. **Generate Block 4** (goals) — LLM creates strategic objectives and initial plans from identity + memory + the starting situation

Each stage feeds its output to the next. The result is a unique, coherent character with consistent personality, accurate situational awareness, and a plausible opening strategy — ready to play Round 1.

---

## Perceive → Think → Act Cycle

The core operates as a continuous loop during active play:

### Perceive

The perception layer receives all incoming events and information, filters them by relevance, and routes them to the appropriate processing path.

**Incoming event types:**
- **World state updates** (between rounds): new economic indicators, military positions, tech levels, political scores — the same "state of the world" briefing human players receive
- **Direct communications** (during rounds): messages from other participants, meeting invitations, proposals, demands, threats
- **Action results** (during rounds): outcomes of this role's actions (trade confirmed, attack result, covert op outcome)
- **Alerts** (during rounds): events requiring attention or response (incoming attack, strategic missile launch, coup attempt in progress, vote session started)
- **Public events** (during rounds): announcements, press reports, organization meeting outcomes, other countries' visible actions (military movements, public speeches, treaty signings)

**Filtering and prioritization:**
Not every event requires a full cognitive cycle. The perception layer categorizes each event:
- **React immediately** — direct threats, time-sensitive proposals, active combat
- **Process soon** — new information that may affect current plans
- **Batch for next reflection** — background context, others' actions that don't directly involve this role

### Think

The thinking layer is where the AI reasons about new information and updates its cognitive state. Two modes:

**Reflection** — updating Blocks 2/3/4 in response to new information. The LLM receives the current cognitive state plus the new information and produces updated block content. This is the same pattern proven in KING: load context → build prompt → call LLM → parse response → atomic save.

**Deliberation** — reasoning about what to do next. Not a block update but a decision process. The LLM receives the full cognitive state (all 4 blocks) plus the current situation (what's happening right now, what decisions are pending, what time pressure exists) and produces a structured action plan.

Deliberation happens:
- At the start of each round (what are my priorities for this round?)
- When a significant event changes the situation (how does this affect my plans?)
- When the AI has been idle for a configurable period during an active round (what should I be doing right now?)
- When prompted by the action loop (should I initiate contact with someone? make a trade? launch an operation?)

### Act

The action layer translates decisions into concrete game actions submitted through the SIM adapter. Action types:

**Routine submissions** (budget, tariffs, sanctions, OPEC+ production, export restrictions, mobilization):
- Prepared during deliberation
- Submitted before the round deadline
- Structured data (numbers, levels, allocations) — not free text

**Real-time transactions** (via Market Engine):
- Propose or accept trades (coins, arms, tech, basing rights, treaties)
- Each requires building a proposal, sending it, and handling the counterparty's response

**Real-time actions** (via Live Action Engine):
- Initiate combat, blockades, strikes, covert ops, arrests, propaganda
- Each requires assessing the situation, deciding to act, and requesting authorization from other roles if required

**Communications:**
- Send messages to other participants
- Accept or decline meeting invitations
- Participate in organization meetings
- Make public speeches or statements

**Deployments** (during Phase C):
- Assign newly available units to zones on the map

---

## Conversation Engine

Handles all text-based communication between the AI participant and other players (human or AI).

### Conversation Types

**1-on-1 bilateral negotiation** — the most common. Proposing deals, discussing terms, building trust, making threats. Must handle multi-turn exchanges where the AI adapts its position based on what the counterpart says.

**Multi-party meetings** — organization sessions (NATO, EU, BRICS+, OPEC+, UNSC), alliance caucuses, peace conferences. For the initial version, multi-party participation uses the standard voice interface with additional behavioral instructions: the AI listens more than it speaks, restrains itself from interjecting unless directly addressed or when it has something genuinely important to contribute, and tracks the positions of other speakers. This is simpler than building a dedicated multi-party orchestration system and mirrors how a real diplomat behaves in a multilateral setting — mostly listening, choosing moments carefully.

**Receiving and responding to messages** — asynchronous chat (Telegram, web app messaging). The AI receives a message, processes it in the context of the sender's identity and the current situation, and responds appropriately — which may include not responding, or responding with deliberate delay.

**AI-to-AI conversations** — when both parties in a negotiation are AI-operated. These run as automated turn-based exchanges with configurable turn limits. Context caching (proven in KING) reduces API costs significantly for multi-turn conversations.

### Conversation Capabilities

The AI must be able to:
- **Propose** — initiate a deal, suggest terms, make an offer
- **Counter** — reject and propose alternatives
- **Bluff** — misrepresent intentions, exaggerate capabilities, threaten actions it may not intend to take (this emerges naturally from the AI reasoning about its interests — not from explicit "bluff instructions")
- **Commit** — make promises, accept terms, and remember commitments (Block 3)
- **Stall** — delay a decision, ask for time, change the subject (when strategically appropriate)
- **Coordinate** — align positions with allies before a multilateral meeting, agree on messaging
- **Walk away** — end a conversation that isn't productive

### Intent Notes

Before entering a conversation, the AI generates intent notes from its current cognitive state: what it wants from this interaction, what it's willing to offer, what its red lines are, what tone to adopt. These guide the conversation without being rigidly prescriptive — the AI can adapt if the conversation takes an unexpected turn.

---

## Voice Engine

Enables spoken conversation between a human player and an AI participant. The human walks up to the AI participant's terminal (a screen/device representing that country) and talks.

### How It Works

1. **Human initiates** — approaches the AI terminal, presses "talk" (or the session starts automatically)
2. **AI prepares** — generates intent notes based on current cognitive state and who's approaching
3. **Voice connection** — established via ElevenLabs Conversational AI (or equivalent voice agent API). The AI's cognitive state and intent notes are loaded as the agent's prompt.
4. **Conversation flows** — human speaks, AI listens, AI responds with synthesized voice. Both sides heard in real time.
5. **Transcript captured** — dual-channel recording (human speech-to-text + AI text). Full transcript stored.
6. **Post-conversation** — transcript triggers reflection (Block 3/4 update). Any commitments made are tracked. If a deal was discussed, the AI may follow up with a formal transaction submission.

### Voice Configuration

Each AI character gets a distinct voice profile (selected during initialization): voice timbre, accent, speaking pace, emotional range. Wellspring sounds different from Pyro who sounds different from Citadel. This makes the AI participants feel like distinct people, not the same AI in different costumes.

### Alternative: Chat-Only Mode

For SIM runs where voice isn't practical (cost, infrastructure, noise), the same interaction happens via text chat. The human types, the AI responds in text. The cognitive pipeline is identical — only the I/O channel changes.

---

## Autonomous Action Loop

This is what makes TTT's AI participant fundamentally different from KING's. During Phase A (the active negotiation phase of each round), the AI doesn't just wait for events — it proactively pursues its goals.

### Loop Structure

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
│     → Are any deadlines approaching? │
│                                      │
│  3. Evaluate action opportunities    │
│     → Should I contact someone?      │
│     → Should I make a trade?         │
│     → Should I initiate an action?   │
│     → Should I attend a meeting?     │
│                                      │
│  4. Execute highest-priority action  │
│     → Send message / make proposal   │
│     → Submit transaction             │
│     → Initiate live action           │
│     → Join meeting                   │
│                                      │
│  5. Wait (configurable interval)     │
│     → Check for new events           │
│     → Loop back to 1                 │
│                                      │
│  INTERRUPT: Incoming event breaks    │
│  the wait cycle → immediate process  │
└──────────────────────────────────────┘
    │
    ▼
ROUND DEADLINE APPROACHING
    │
    ▼
SUBMIT: Routine settings (budget, tariffs, sanctions, etc.)
    │
    ▼
ROUND ENDS → WORLD UPDATE → REFLECT ON RESULTS
    │
    ▼
DEPLOYMENT WINDOW: Deploy units
    │
    ▼
NEXT ROUND STARTS
```

### Loop Timing

The loop interval is configurable (e.g., every 30–90 seconds the AI "looks around"). This prevents the AI from overwhelming the system with constant activity while ensuring it doesn't miss time-sensitive opportunities. The moderator can adjust AI activity frequency to match the pace of the game.

### Strategic vs. Reactive

The AI balances two modes:
- **Proactive** — pursuing its own agenda (initiating negotiations, proposing deals, building coalitions)
- **Reactive** — responding to what's happening (answering messages, responding to attacks, adjusting to new information)

The balance shifts based on the situation. In a quiet round, the AI is mostly proactive. During a crisis (military attack, economic shock, coup attempt), it's mostly reactive.

---

## Module Interface Protocol

The standardized API that connects the AI Participant Module to any host SIM. This is what makes the module reusable.

### From SIM to Module (Inbound)

**1. World State Update**
```
Trigger: After each World Model Engine batch processing
Contains:
  - Full world state visible to this role (respecting information asymmetry)
  - Country-level indicators (economic, military, political, tech)
  - Round number and scenario time
  - Narrative briefing text
```

**2. Event Notification**
```
Trigger: During rounds, whenever something happens that this role can see
Contains:
  - Event type (combat_result, transaction_completed, message_received,
    meeting_invitation, vote_session, alert, public_announcement...)
  - Event data (structured, SIM-specific — translated by adapter)
  - Priority (immediate / normal / background)
  - Response required? (yes/no, with deadline if yes)
```

**3. Action Menu**
```
Trigger: On request from module, or at round start
Contains:
  - Available actions for this role at this moment
  - For each action: type, required parameters, authorization status,
    constraints
  - Pending submissions (what's still needed before deadline)
```

**4. Conversation Incoming**
```
Trigger: When another participant sends a message or meeting invitation
Contains:
  - Sender identity (role, country, relationship context)
  - Message content or meeting details
  - Conversation thread ID (for multi-turn exchanges)
  - Response expected? (and urgency)
```

### From Module to SIM (Outbound)

**5. Action Submission**
```
What: A structured game action
Contains:
  - Action type (budget_submission, tariff_change, transaction_proposal,
    attack_order, covert_op, deployment, etc.)
  - Action parameters (SIM-specific structured data)
  - Authorization chain status (who has approved)
```

**6. Communication Outbound**
```
What: A message or meeting request from the AI to another participant
Contains:
  - Target (role ID or meeting/channel ID)
  - Content (text message, voice session request, meeting call)
  - Context flags (formal/informal, public/private)
```

**7. Status Update**
```
What: The AI's current operational status
Contains:
  - Status (idle, thinking, in_conversation, submitting)
  - Current activity description
  - Queue depth (pending items to process)
```

### Protocol Characteristics

- **Asynchronous** — messages can arrive at any time; the module processes them according to its own priority system
- **Event-driven** — the SIM pushes events to the module; the module pushes actions to the SIM
- **Stateless connection** — all persistent state lives in the module's cognitive blocks and the SIM's database; the protocol itself carries no state
- **Version-tolerant** — event and action types can be extended without breaking existing integrations

---

## TTT SIM Adapter

The TTT-specific translation layer. This is where knowledge of TTT's game mechanics lives.

### Inbound Translation (SIM → Core)

Converts TTT's game state into digestible briefings:

- **Economic data** → "Your GDP grew 2.3% this round. Revenue next round: 45 coins (down from 48 — sanctions cost 3 coins). Inflation at 4.2%. Reserves: 12 coins."
- **Military situation** → "You have 8 ground units (4 in home territory, 4 at Gulf base), 3 naval units (Persian Gulf), 2 air defense (1 home, 1 Gulf). No active combat involving your forces. Nordostan-Heartland war continues — 3 new zones changed control."
- **Diplomatic context** → "Pending proposals: Cathay offers 10-year oil contract at fixed price. Columbia's Fixer requests private meeting about Iran. BRICS+ currency vote scheduled Round 4."
- **Political state** → "Your stability: 7 (stable). Political support: 65%. No domestic threats active."

The adapter knows which information this role has access to (respecting TTT's information asymmetry rules) and presents only what the role would know.

### Outbound Translation (Core → SIM)

Converts the core's decisions into TTT's structured submissions:

- Core decides: "Set oil production to LOW this round to push prices up"
  → Adapter submits: `{ action: "opec_production", level: "low" }`

- Core decides: "Offer Cathay 5 coins for 1 air defense unit"
  → Adapter submits: `{ action: "transaction_proposal", target: "cathay", offer: { coins: 5 }, request: { unit_type: "air_defense", quantity: 1 } }`

- Core decides: "Allocate budget: 40% social, 20% ground military, 15% naval, 10% tech R&D, 15% reserves"
  → Adapter submits: `{ action: "budget_submission", allocations: { social: 0.40, ground_production: 0.20, naval_production: 0.15, tech_rd: 0.10, reserves: 0.15 } }`

### Decision Framework

The adapter provides the core with a structured decision framework for each type of decision TTT requires. This maps the free-form AI reasoning to the specific structured outputs the game engines expect:

**Budget decisions** — category list, constraints (total = 100%, mandatory maintenance pre-deducted), current revenue, trade-offs explained
**Tariff decisions** — target countries × sectors matrix, current levels, effects of changes
**Sanctions decisions** — target × type matrix, coalition context, cost-to-self
**Military decisions** — available units, valid zones, authorization requirements
**Diplomatic decisions** — available treaty types, counterparty positions (as perceived), organizational agendas

---

## Reference: KING SIM Inheritance

What is borrowed from KING SIM's proven architecture and what is new for TTT:

| Component | KING (proven) | TTT (extended) |
|-----------|--------------|----------------|
| 4-block cognitive model | Blocks 1–4, JSONB storage, atomic versioning | Same architecture. Block 4 extended for multi-round strategic planning with conditional branches |
| Initialization pipeline | 4-stage sequential (Block 1 → 2 → 3 → 4) | Same pipeline. Stage 1 assembles from TTT-specific rules and role definition |
| Reflection system | Event-triggered, priority queue, batched processing | Same system. More event types, higher throughput needed (TTT generates ~5× more events per round than KING per phase) |
| Conversation manager | Round-robin turns, context caching, AI-AI and AI-human | Extended: more conversation types (bilateral, multilateral via voice interface with listen-first behavior, organization meetings). Multi-thread management (AI may be in multiple conversations in a round) |
| Voice synthesis | ElevenLabs integration, intent notes, transcript capture | Same approach. Voice profiles per character. Chat-only fallback |
| Decision services | Vote decisions, King decisions (structured output) | Massively expanded: budget, tariffs, sanctions, military, diplomatic, covert — each with structured output schema |
| Auto phase triggers | Phase transitions trigger clan councils, King decisions | Extended: round start deliberation, continuous action loop during rounds, deadline-driven submissions |
| **NEW: Autonomous action loop** | Minimal (basic idle-check in Free Consultations) | Full continuous loop during rounds with proactive goal pursuit |
| **NEW: Module interface protocol** | Tightly coupled to KING app | Standardized API enabling reuse across SIMs |
| **NEW: SIM adapter layer** | Not separated | Clean separation of SIM-specific knowledge from cognitive core |

### Key KING Lesson Applied

The March 2026 "AI Realism Overhaul" in KING found that:
- Block 1 in conversation context was drowning personality in rules → **Solution**: inject rules at initialization, use identity (Block 2) as primary conversation context
- Explicit behavioral constraints ("MUST disagree") produced stubborn, circular arguments → **Solution**: frame the AI as "a political actor" and let it reason naturally from its interests
- Characters needed more personality diversity → **Solution**: higher temperature (0.85) for identity generation, plain-speech guidance

All three lessons are embedded in TTT's design from the start.

---

## Technical Considerations (Concept-Level)

### LLM Selection

The cognitive core is LLM-agnostic — it works through a provider abstraction that allows switching models before and during the SIM (as proven in KING). Current leading providers:

- **Google Gemini** (latest available models) — proven in KING for conversations and reflections, context caching dramatically reduces costs for multi-turn exchanges
- **Anthropic Claude** (latest available models) — strong reasoning capabilities, particularly suited for complex geopolitical deliberation and strategic planning

The architecture supports mixing models by task: a faster, cheaper model for high-frequency operations (perception filtering, routine reflections, simple responses) and a stronger reasoning model for critical decisions (strategic deliberation, complex negotiations, multi-dimensional policy choices like budget allocation). Model selection is configurable per task type and adjustable at runtime — the moderator or technical operator can switch models during the SIM if performance or cost requires it.

### Scaling

A full TTT session might have 10 AI-operated solo countries active simultaneously. Each runs its own cognitive loop. Key considerations:
- API rate limits across 10 concurrent AI participants
- Context caching to reduce redundant calls (shared world state)
- Staggered loop intervals to spread load (not all 10 AI participants deliberate at the same second)
- Graceful degradation: if API latency spikes, reduce AI activity frequency rather than fail

### Data Storage

Each AI participant's cognitive state (4 blocks + version history) stored in the SIM database. All AI decisions logged with reasoning (for post-SIM analysis and debugging). Conversation transcripts stored as meeting records (same format as human meetings).

### Moderator Visibility

The moderator can:
- View any AI participant's current cognitive state (all 4 blocks)
- See the AI's reasoning for any decision
- Adjust AI behavior parameters (activity frequency, aggressiveness tuning)
- Pause/resume any AI participant
- Override an AI decision before it executes
- Trigger a manual reflection (force the AI to reconsider after moderator-injected information)

---

## Scope Boundaries

**This module IS:**
- The AI system that enables autonomous participation in the SIM
- A reusable architecture separable from any specific SIM
- A cognitive agent that perceives, reasons, communicates, and acts

**This module is NOT:**
- The World Model Engine (which calculates game physics — GDP, combat, stability)
- The game UI (which displays information to humans)
- The communication infrastructure (Telegram, web app chat — the module plugs into whatever exists)
- A replacement for the SIM's own engines — it's a player, using those engines as a human would

---

## Open Questions for Detailed Design

1. **AI-to-AI optimization** — when two AI participants negotiate, should they run a fast-mode (more turns, shorter messages, less delay) or pace themselves realistically?
3. **Deception capability** — the AI should be able to bluff and mislead, but should there be any limits? (e.g., AI cannot lie about publicly verifiable facts, but can misrepresent private intentions)
4. **Learning across rounds** — should Block 4 (strategy) carry forward detailed plans for future rounds, or regenerate fresh each round from updated Block 3 (memory)?
5. **Emotional modeling** — should the AI model emotional states (angry, fearful, confident) that affect its negotiation style and risk tolerance? KING did this through personality dimensions in Block 2.
6. **API cost budget** — at 10 concurrent AI participants × continuous action loops × multi-turn conversations, what's the realistic cost per SIM session? This affects loop frequency and conversation depth.

---

## Changelog

- **v1.1 (2026-03-25):** Multi-party meetings simplified to standard voice interface with listen-first behavioral instructions. LLM selection updated: Gemini and Anthropic Claude as leading candidates (latest available models), with per-task model mixing and runtime switching. Removed specific model version references. Multi-conversation concurrency question resolved (voice interface handles it).
- **v1.0 (2026-03-25):** Initial concept. Three-layer architecture (Cognitive Core / SIM Adapter / Module Interface Protocol). 4-block cognitive model inherited from KING with extensions for strategic planning. Autonomous action loop for continuous round participation. Conversation and voice engines. Seven inbound/outbound protocol message types. TTT adapter specifications. KING inheritance analysis. Open questions identified.
