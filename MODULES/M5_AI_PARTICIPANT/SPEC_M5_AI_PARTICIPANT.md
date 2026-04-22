# SPEC: M5 — AI Participant Module

**Version:** 1.0
**Date:** 2026-04-21
**Status:** APPROVED DECISIONS — Ready for build planning
**Depends on:** M1 (Engines), M2 (Communication), M3 (Data), M4 (Sim Runner)
**Spike:** PASSED (2026-04-20) — Managed Agent played 2 rounds, 10 valid actions, $0.35
**External Dependencies:** M6 chat interface (shared), game rules reference (shared M5/M6)

---

## 1. What This Module Does

M5 makes AI countries play the simulation — same actions, same contracts, same information, indistinguishable from human players. An AI participant explores the game state, reasons about strategy, initiates conversations, submits actions, reacts to events, and remembers across rounds.

**This is NOT a chatbot.** It is an autonomous head of state (or military chief, intelligence director, diplomat, or opposition leader) with persistent identity, self-authored goals, and the full action catalog. It decides what to investigate, whom to trust, when to act, and when to wait.

**Spike validation (2026-04-20):** A Claude Managed Agent session playing Dealer (Columbia) autonomously explored game state, identified a two-front trap, issued public statements, ordered covert ops, invested in R&D, set tariffs, called an alliance meeting, sent military aid, and forward-deployed units — all with coherent strategic rationale, at $0.17/round.

**Key principle:** The system is agnostic about who's AI and who's human. Actions, chat messages, unit moves, proposals — all flow through the same infrastructure regardless of source.

---

## 2. Module Architecture — Three Layers

```
┌─────────────────────────────────────────────────────┐
│  LAYER 1: IDENTITY (Immutable per SIM)              │
│  System prompt: character + world rules + game       │
│  mechanics + meta-awareness + autonomy doctrine      │
│  ~5-8K tokens, built once, cached for session        │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│  LAYER 2: AGENT SESSION (Agent-controlled)          │
│  Claude Managed Agent (persistent session)           │
│  16 game tools → real DB queries + writes            │
│  Memory: agent decides what to remember              │
│  Goals: agent sets own strategy                      │
│  Character traits: self-assigned at initialization   │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│  LAYER 3: EVENT DISPATCHER (Invisible to agent)     │
│  Unified event queue: everything writes to queue,    │
│  single dispatcher delivers. No concurrent streams.  │
│  Tier 1 (critical) <5s, Tier 2 (urgent) <10s,      │
│  Tier 3 (routine) batched at pulse interval.         │
└─────────────────────────────────────────────────────┘
```

---

## 3. Sub-Modules

| Sub-Module | Location | Responsibility | Status |
|------------|----------|----------------|--------|
| **M5.1 Identity Builder** | `engine/agents/managed/system_prompt.py` | Build Layer 1 from DB role + country + rules + meta | DONE |
| **M5.2 Tool Interface** | `engine/agents/managed/tool_*.py` | 16 game tools (definitions + executor) | DONE |
| **M5.3 Session Manager** | `engine/agents/managed/session_manager.py` | AsyncAnthropic: create/manage sessions, SSE streams, tool dispatch | DONE (async) |
| **M5.4 Event Dispatcher** | `engine/agents/managed/event_dispatcher.py` | **THE CORE** — unified event queue, tiered delivery, single dispatch loop | BUILDING |
| **M5.5 Conversation Router** | `engine/agents/managed/conversations.py` | Bilateral meetings: AI↔AI and AI↔Human via direct send_event | DONE |
| **M5.6 Observer** | Dashboard + Agent Detail Page | AI dashboard with queue depth, agent detail with full activity log | DONE |

**Architecture change (2026-04-22):** M5.4 changed from "Orchestrator" (dual-path: scheduled pulses + auto-pulse) to "Event Dispatcher" (single unified queue). All events flow through one queue, one dispatcher. Eliminates race conditions, lost events, stuck sessions. See `SPRINT_UNIFIED_QUEUE.md` for full design.

---

## 4. Decisions Log

### D1: AI Behavior — Fully Autonomous + Traits + Global Dial

**Decision:** Fully autonomous. No per-agent behavior dials.

**Three layers of personality:**
1. **Identity** — from role data (character name, title, country, objectives, powers). Already exists.
2. **Character traits** — generated at initialization. Agent self-assigns from a framework: temperament, Thomas-Kilmann conflict style, risk orientation, decision speed, trust default. Creates natural variability across runs.
3. **Global assertiveness dial** — sim-level setting (1 = cooperative, 10 = assertive). Shifts the average AI toward accommodation or competition. Default: 5.

### D2: AI↔Human Switching — Locked at Start

**Decision:** AI/Human assignments set in the sim wizard, locked once running. No switching in v1. Moderator can add/remove participants (M4 territory).

**Deferred to v2:** When switching is built, the human inherits the agent's memory notes as a briefing document.

### D3: All Roles Supported

**Decision:** All role types from day one — HoS, military chiefs, intelligence directors, diplomats, opposition. Not just HoS.

The system prompt adapts per role type (different powers, different action emphasis). Action validation respects `role_actions` permissions. Position changes mid-SIM trigger immediate update to information access and available actions, delivered as a pulse event.

### D4: Pulse-Based Activity — Phased + Batched + Critical Interrupts

**Decision:** The orchestrator sends exactly N pulses per round (configurable 1-20, recommended 5-10). Agent is told the exact number. Timing calculated by orchestrator (evenly spaced across round duration).

**Each pulse contains:**
- Public events since last pulse (batched)
- Private/confidential events (intel reports, covert results, artefacts)
- Pending items requiring response (meeting invitations, proposals)
- Resource dashboard (meetings remaining, intel cards, mandatory inputs status)
- Pulse number: "This is update 4 of 8"

**Critical interrupts** bypass the pulse schedule for: nuclear launch, direct attack on territory, other existential events. Rare — 0-2 per round maximum.

**Meta-awareness:** Agent's Layer 1 prompt explains the pulse system. Agent learns to budget actions across pulses rather than front-loading.

### D5: Activity Limits — Real Game Constraints + Caps + Busy State

**Decision:** No artificial "3 actions per round" cap. Real game constraints apply (intelligence pool, role_actions, authorization chains). Additional caps:

| Limit | Default | Configurable |
|-------|---------|:------------:|
| Meetings per round | 5 | Yes |
| Info lookups per pulse | TBD (monitor first) | Yes |
| Intelligence cards | From role data | No (game rule) |
| Turns per meeting | 8 per side | Yes |

**Busy state enforced:**
- `IDLE` → can receive pulses, start activities
- `IN_MEETING` → busy. Incoming events queue. No other actions possible.
- `ACTING` → processing a pulse. Short busy window.

Meeting requests while busy → queued, delivered at next available pulse. This creates the same time-pressure tradeoffs humans face.

### D6: Conversations — Same Infrastructure as Humans

**Decision:** AI uses the SAME meeting/chat system as human players. No separate AI conversation channel.

**Flow:**
1. Agent calls `request_meeting(country, agenda)` → same DB invitation record
2. Counterpart receives invitation at next pulse → accepts/declines via tool
3. Chat channel opens → same `meeting_messages` table
4. Messages via `send_message` tool → same chat UI (observable!)
5. Meeting ends → both agents reflect at next pulse

**Three conversation types — same interface, different execution:**

| Type | Chat | Voice | Notes |
|------|:----:|:-----:|-------|
| AI ↔ AI | Same chat UI (observable) | Not needed | Orchestrator relays between sessions |
| AI ↔ Human | Same chat UI | v2: ElevenLabs avatar | Human types/speaks, AI responds |
| Human ↔ Human | Same chat UI | Direct (outside system) | No M5 involvement |

**Communication style:** System prompt enforces natural language — short sentences, conversational idioms, occasional humor, appropriate emotions. No bullet points or headers in meetings. 1-3 sentences per turn.

**Chat UI:** Full-screen on mobile. Telegram-style simplicity. Typing animation (messages appear gradually, not as instant jumps).

### D7: Voice Meetings — ElevenLabs Avatar Delegated by Managed Agent

**Decision (v2, designed now):** KING architecture reused.

**Two-tier delegation:**
```
MANAGED AGENT ("The Mind")
  → Generates intent notes: {goal, tone, tactics, boundaries}
  → Passes cognitive summary to voice avatar
  → Receives transcript after meeting
  → Reflects and updates memory

VOICE AVATAR (ElevenLabs, "The Mouth")
  → Speaks naturally in character
  → Follows intent notes
  → Cannot commit outside boundaries
  → Each character has unique voice profile
```

**New tool:** `prepare_voice_meeting(counterpart, context)` → returns structured intent notes.

**Human can drop to text anytime** — same chat interface, voice is an overlay. Text always available as fallback.

### D8: Information Parity — Agent Sees What Humans See

**Decision:** Same information, same scoping. No advantage, no disadvantage.

| Information Type | Delivery |
|------------------|----------|
| Public events | Batched in pulse |
| Private intel reports | Delivered in pulse, marked confidential |
| Covert op results | Delivered in pulse |
| Confidential brief | Layer 1 system prompt |
| Private proposals | Pulse + `get_pending_proposals` tool |
| Artefacts | `get_my_artefacts` tool |
| Detected threats | Critical interrupt or pulse |

### D9: Observability — Facilitator Only, Two Levels

**Level 1: AI Participants Dashboard** (on main facilitator interface)
- All AI agents at a glance: name, country, status (idle/in_meeting/acting/frozen), current/last activity
- Global controls: [Freeze All AI] [Resume All]

**Level 2: Agent Detail View** (click from dashboard)
- Expandable activity log: lookups, actions, meetings, reasoning
- Each entry: collapsed = one-liner, expanded = full detail + rationale
- Meeting entries: link to chat transcript
- Per-agent controls: [Freeze] [Resume]

**Moderator controls:**

| Action | Effect |
|--------|--------|
| Freeze one agent | Stops receiving pulses, queues events |
| Freeze all AI | Global pause, humans continue |
| Resume | Receives batched events from freeze period |
| Act on behalf | Opens human participant interface for that role (from Manage Participants). Actions tagged `source: moderator_override`. Agent informed at next pulse. |

**Other players see nothing AI-specific.** No indication of who's AI.

### D10: Session Recovery

**Decision:** Managed Agent sessions persist on Anthropic's side. Our server can crash and reconnect.

**Recovery strategy:**
1. Load active session IDs from DB
2. `sessions.retrieve(id)` → check status
3. Idle → resume at next pulse
4. Running → reconnect stream
5. Terminated → create new session, feed agent's memory notes from `agent_memories` table as context recovery

**Health check before every pulse.** Agent's `write_notes` is the ultimate safety net — self-authored memory in our DB survives any session failure.

---

## 5. Tool Interface — 16 Tools

| # | Tool | Category | Mirrors Human UI |
|---|------|----------|-----------------|
| 1 | `get_my_country` | Situation | Country dashboard |
| 2 | `get_my_forces` | Situation | Unit panel / map |
| 3 | `get_relationships` | Situation | Diplomacy panel |
| 4 | `get_pending_proposals` | Situation | Inbox / notifications |
| 5 | `get_recent_events` | World | Observatory feed |
| 6 | `get_country_info(country)` | World | Click country on map |
| 7 | `get_hex_info(row, col)` | World | Click hex on map |
| 8 | `get_organizations` | World | Organizations panel |
| 9 | `get_my_artefacts` | World | Artefact viewer (intel, cables) |
| 10 | `get_action_rules(type)` | Reference | Help / reference cards |
| 11 | `request_meeting(country, agenda)` | Communication | Invite button |
| 12 | `respond_to_invitation(id, decision)` | Communication | Accept/decline |
| 13 | `send_message(meeting_id, text)` | Communication | Chat input |
| 14 | `submit_action(action)` | Action | Action forms |
| 15 | `write_notes(key, content)` | Memory | AI-only (persistent across rounds) |
| 16 | `read_notes(key)` | Memory | AI-only (recall own memory) |

**Principle:** If a human can find it in the UI, the agent can find it through a tool.

**Note:** `get_action_rules` and `get_my_artefacts` depend on shared reference infrastructure with M6. Built when that infrastructure exists; agent uses Layer 1 game rules knowledge as fallback.

---

## 6. Layer 1 System Prompt — Four Sources (~5-8K tokens)

| Source | Content | Tokens | Module |
|--------|---------|--------|--------|
| **World Context** | Roster, geography, theaters, starting situation, wars, sanctions | ~2,000 | `world_context.py` (exists) |
| **Role Identity** | Character, title, objectives, powers, confidential brief, trait generation | ~800 | `profiles.py` (exists) + trait gen (new) |
| **Game Rules** | All action types, combat, economy, diplomacy, covert, elections, nuclear — condensed but complete | ~2,000-3,000 | `game_rules_context.py` (NEW) |
| **Meta-Awareness** | Pulse system, tool descriptions, timing, busy state, resource limits, information scoping, memory instructions | ~1,000-1,500 | `meta_context.py` (NEW) |

Built once per session, cached. Agent can use `get_action_rules` tool for detailed lookups beyond what's in Layer 1.

---

## 7. Global AI Configuration

Set at sim level in the wizard. Affects all AI participants.

| Setting | Range | Default | Purpose |
|---------|-------|---------|---------|
| **Assertiveness dial** | 1-10 | 5 | 1=cooperative world, 10=assertive world |
| **Pulses per round** | 1-20 | 8 | How often agents think/act |
| **Max meetings per round** | 1-10 | 5 | Fairness + cost |
| **Max info lookups per pulse** | 1-20 | 10 | Cost control (adjust after monitoring) |
| **Max turns per meeting** | 4-16 | 8 per side | Conversation depth |

---

## 8. Cost Model

Based on spike (Sonnet 4.6, $3/M input, $15/M output):

| Scenario | Agents | Rounds | Pulses | Est. Cost |
|----------|--------|--------|--------|-----------|
| Single agent test | 1 | 2 | 8 | $0.35 |
| Small unmanned (10 HoS) | 10 | 6 | 8 | $10-25 |
| Full unmanned (21 HoS) | 21 | 6 | 8 | $20-50 |
| All roles (40 agents) | 40 | 6 | 8 | $40-100 |
| With conversations (+3/agent/round) | 21 | 6 | 8 | $50-120 |

**Cost levers:** model choice (Sonnet vs Haiku for minor roles), pulses per round, meeting limits, prompt conciseness.

---

## 9. Testing & Staging Framework

### Test Configurations

| Config | Countries | Roles | Purpose |
|--------|-----------|-------|---------|
| **Solo** | 1 (Columbia) | 1 HoS | Basic agent loop, action validation |
| **Duo** | 2 (Columbia + Cathay) | 2 HoS | Conversation testing, bilateral dynamics |
| **Team** | 1 (Columbia: 7 roles) + 7 international HoS | 14 | Internal team dynamics, multi-role |
| **Small world** | 10 countries, HoS only | 10 | Cost-effective full dynamics |
| **Full unmanned** | 21 countries, HoS only | 21 | Production validation |
| **All roles** | 21 countries, all positions | 40 | Maximum complexity |

### Restricted Sim Runs

Custom sim_runs with reduced country sets. Template supports selecting which countries are active. Inactive countries exist in data but have no agent — their state is static.

### Orchestrator as Co-Moderator

For fast testing, the orchestrator plays co-moderator role:
- Auto-advances rounds (no human facilitator needed)
- Injects test events (military alerts, proposals, crises)
- Monitors and logs all activity
- Generates test reports (actions per agent, cost, conversation count, error rate)

### External Dependencies to Test

| Dependency | Module | Needed For |
|------------|--------|------------|
| Chat interface (text) | M6 | AI↔Human meetings, AI↔AI observation |
| Meeting invitations | M4/M6 | Shared invitation system |
| Artefact viewer | M6 | `get_my_artefacts` tool |
| Game rules reference | M5/M6 shared | `get_action_rules` tool |

### Monitoring Metrics

| Metric | Purpose |
|--------|---------|
| Actions per agent per round | Activity level calibration |
| Tool calls per pulse | Lookup cost monitoring |
| Meeting count + avg turns | Conversation calibration |
| Token usage per agent per round | Cost tracking |
| Action validation pass/fail rate | Quality signal |
| Latency (pulse send → agent done) | Performance |
| Session health (disconnects, recoveries) | Reliability |

---

## 10. Build Phases

| Phase | What | Depends On | Est. Effort |
|-------|------|------------|-------------|
| **Phase 1: Foundation** | Expand Layer 1 (game rules + meta context), expand to 16 tools, harden session manager with recovery | Spike (done) | 2-3 days |
| **Phase 2: Orchestrator Core** | Pulse scheduling, event batching, busy state, multi-agent parallel execution, resource tracking | Phase 1 | 3-4 days |
| **Phase 3: Solo Agent Full Lifecycle** | One agent through complete round (pulses, actions, mandatory inputs, reflection). Orchestrator as co-moderator for testing. | Phase 2 | 1-2 days |
| **Phase 4: Multi-Agent** | 10-21 agents in parallel, independent (no conversations yet) | Phase 3 | 1-2 days |
| **Phase 5: Conversations** | AI↔AI bilateral meetings via shared chat system. Requires chat backend (M6 dependency). | Phase 4 + M6 chat | 2-3 days |
| **Phase 6: Mixed Mode** | AI + Human in same SIM, AI↔Human text chat | Phase 5 + M6 UI | 2-3 days |
| **Phase 7: Observability** | AI dashboard, agent activity log, freeze/resume, moderator override | Phase 4 | 2-3 days |
| **Phase 8: Voice** | ElevenLabs avatar integration, intent notes, transcript capture | Phase 6 + KING port | 3-4 days |
| **Phase 9: All Roles** | Multi-role per country, role-specific prompts, position change handling | Phase 4 | 2-3 days |

**Critical path:** Phases 1→2→3→4 (foundation to multi-agent). Then 5+6 (conversations) and 7 (observability) can run in parallel.

---

## 11. Out of Scope (v1)

- Multi-party meetings (3+ agents) — bilateral only
- AI↔Human switching mid-SIM
- Automatic strategy optimization / learning across SIMs
- Per-agent behavior dials (autonomy is the point)
- Agent-to-agent direct messaging outside chat system

---

## 12. Architectural Principles

1. **Same system for everyone.** Actions, chat, invitations, map — all flow through identical infrastructure regardless of AI or human.
2. **Autonomy is the product.** We provide identity, context, and tools. The agent provides strategy, decisions, and personality.
3. **Information parity.** Agent sees exactly what a human sees. No advantage, no disadvantage.
4. **Busy means busy.** When in a meeting, you miss updates — just like a real leader.
5. **Memory is self-authored.** What the agent doesn't write down, it forgets. This IS the cognitive model.
6. **Observable by default.** Every AI action flows through the same DB tables. Facilitator sees everything. Other players see only public actions.
7. **Recover gracefully.** Sessions can die. Memory in DB survives. New session + old notes = continuity.

---

*Decisions made in collaboration with Marat Atn, 2026-04-21. All Q1-Q14 resolved. Ready for build planning and Phase 1 implementation.*
