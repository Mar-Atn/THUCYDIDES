# SPEC: M5 — AI Participant Module

**Version:** 2.0
**Date:** 2026-04-28
**Status:** ACTIVE — Core module tested. Avatar conversations (M5.7) functional. Dispatcher resilience (M5.8) done.
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
| **M5.1 Identity Builder** | `engine/agents/managed/system_prompt.py` | Build Layer 1 from DB role + country + rules + meta + avatar architecture | DONE |
| **M5.2 Tool Interface** | `engine/agents/managed/tool_*.py` | 18 game tools (16 original + intent_note fields on meeting tools) | DONE |
| **M5.3 Session Manager** | `engine/agents/managed/session_manager.py` | AsyncAnthropic: create/manage sessions, SSE streams, tool dispatch, recovery | DONE |
| **M5.4 Event Dispatcher** | `engine/agents/managed/event_dispatcher.py` | **THE CORE** — unified event queue, three background loops, DB-backed auto-recovery | DONE |
| **M5.5 Conversation Router** | `engine/agents/managed/conversations.py` | **SUPERSEDED by M5.7.** Legacy file kept but not used. Avatar system handles all meetings. | SUPERSEDED |
| **M5.6 Observer** | Dashboard + Agent Detail Page | AI dashboard with status, cost, activity, voice icons, real-time meeting state. | DONE |
| **M5.7 Avatar Conversations** | `avatar_service.py`, `avatar_generator.py`, `VoiceCallInterface.tsx`, `MeetingChat.tsx` | Text chat (Claude API) + Voice call (ElevenLabs). Mode popup. See SPEC_M5_AVATAR_CONVERSATIONS.md | DONE — text + voice both working with full context |
| **M5.8 Dispatcher Resilience** | `event_dispatcher.py`, `main.py` lifespan | DB-backed auto-recovery on restart. Always-recreate sessions. Init/recovery lock. Active-sims-only filter. See SPEC_M5_DISPATCHER_RESILIENCE.md + M4 SPEC 5.1-5.6 | DONE |

**Architecture (2026-04-25):** Single-process, three async background loops:
1. **Dispatch loop** — checks `agent_event_queue`, delivers events to IDLE agents in parallel (`asyncio.gather`). Tiers: 1=critical/3s, 2=urgent/5s, 3=routine/30s.
2. **Auto-pulse loop** — during active Phase A, sends enriched round_pulse events (with recent events, pending items, country snapshot) at configurable intervals. Moderator controls pace (0-10 per round).
3. **Meeting monitor** — every 10s checks for active meetings. AI-AI: launches `run_text_meeting()` (avatar-based, ~60s for 16 turns). AI-Human: avatar responds via `_avatar_respond_to_message()` when human sends a message. 15-minute auto-end for stale meetings.

**Phase B solicitation:** Two-phase wait pattern — waits for agents to START processing (leave IDLE), then waits for them to FINISH (return to IDLE). Enriched context includes full economic snapshot + exact field format for each batch action.

**Stuck agent detection:** Agents in ACTING state for >3 minutes are forced back to IDLE (handles SSE stream hangs).

**Schema-engine alignment (2026-04-25):** All 33 action schemas audited and corrected to match engine contracts exactly. See `AUDIT_SCHEMA_VS_ENGINE.md` for full report.

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

### D6: Conversations — Avatar System (M5.7)

**Decision:** AI uses lightweight conversation avatars instead of full managed agent sessions for meetings. Same meeting/chat infrastructure as humans. See `SPEC_M5_AVATAR_CONVERSATIONS.md` for full details.

**Key architecture:**
- Managed Agent ("the mind") generates Avatar Identity at init + Intent Note per meeting
- Conversation Avatar ("the mouth") handles dialogue via Claude API (text) or ElevenLabs (voice)
- The Managed Agent NEVER writes to meeting_messages — only the avatar does
- After meeting: transcript delivered to Managed Agent for reflection

**Three conversation types:**

| Type | Mode | Execution | Who speaks first |
|------|------|-----------|-----------------|
| AI-AI | Text only | Automated turn-by-turn (`run_text_meeting`) | Avatar A |
| AI-Human | Text or Voice (human chooses) | Human sends/speaks, avatar responds | Human |
| Human-Human | Text only | Direct relay via `meeting_messages` | Either |

**Intent notes glued to invite/accept:** `request_meeting` requires `intent_note` field. `respond_to_invitation(accept)` includes `intent_note`. Generated in same cognitive cycle as the decision.

**No system-generated opening messages.** Human speaks first. Avatar responds.

**No live mode switching.** Human selects Text Chat or Voice Call before meeting opens. End and reconnect to change mode.

### D7: Voice Calls — ElevenLabs (M5.7 Phase 2)

**Decision:** KING architecture adapted. Voice is a mode choice, not a layer on top of text.

**Two-tier delegation — same as text but different delivery:**
```
MANAGED AGENT ("The Mind")
  → Generates Avatar Identity (once at init)
  → Generates Intent Note (per meeting, in invite/accept)
  → Receives transcript after meeting
  → Reflects and updates memory

VOICE AVATAR (ElevenLabs, "The Mouth")
  → Receives: Avatar Identity + Intent Note + VOICE_RULES as prompt override
  → Speaks naturally in character
  → Sub-second responses
  → Each AI role has an assigned ElevenLabs agent (voice profile)
```

**Mode selection:** Human sees popup before meeting opens — [Text Chat] | [Voice Call]. Voice button only visible if AI has `elevenlabs_agent_id`.

**Ending:** Ending the voice call = ending the meeting. No reconnection. New call requires new meeting request.

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
- Global controls: [Stop All AI] [Resume All]

**Level 2: Agent Detail View** (click from dashboard)
- Expandable activity log: lookups, actions, meetings, reasoning
- Each entry: collapsed = one-liner, expanded = full detail + rationale
- Meeting entries: link to chat transcript
- Per-agent controls: [Freeze] [Resume]

**Moderator controls:**

| Action | Effect | API |
|--------|--------|-----|
| Freeze one agent | Stops receiving events. Agent stays initialized but idle. | `POST /ai/freeze/{role_id}` |
| Resume one / Resume all | Agent(s) return to IDLE. Fresh events from current state. | `POST /ai/resume/{role_id}` or `/ai/resume-all` |
| **Stop All AI** | Freezes ALL agents AND clears all pending event queues. Hard reset — agents start fresh on resume. Humans continue. | `POST /ai/stop-all` |
| Shutdown AI | Terminates all sessions. Requires re-initialization. | `POST /ai/shutdown` |
| Act on behalf | Opens human participant interface for that role (from Manage Participants). Actions tagged `source: moderator_override`. Agent informed at next pulse. | M4 territory |

**Stop All AI** is the emergency brake. It:
1. Sets all agents to FROZEN state
2. Deletes all unprocessed events from `agent_event_queue`
3. Returns count of agents frozen + events cleared
4. On resume, agents receive fresh events from current world state (no stale backlog)

**Other players see nothing AI-specific.** No indication of who's AI.

### D10: Phase-Aware Action Restrictions

AI agents have different action availability depending on the simulation phase:

**Pre-Start (R0):** Observation tools + write_notes only. No actions, no meetings.

**Phase A (active round):** All immediate actions available — combat (ground_attack, air_strike, naval_combat, etc.), covert operations, diplomatic actions (propose_transaction, declare_war, etc.), political actions, communication (public_statement, invite_to_meet, call_org_meeting).
NOT available during Phase A: set_budget, set_tariffs, set_sanctions, set_opec, move_units — these are solicited ONCE at Phase B.

**Phase B solicitation windows:**
1. Batch decisions — agent receives a Tier 1 event: 'Submit your batch decisions NOW.' Agent should use get_my_country to review economic state, then submit set_budget + optionally set_tariffs/set_sanctions/set_opec. One chance per round, 2-minute timeout.
2. Troop movements — agent receives a Tier 1 event: 'Submit troop movements NOW.' Agent should review forces with get_my_forces, then submit move_units if repositioning needed. One chance per round, 2-minute timeout.

The tool_executor enforces these restrictions: attempting batch actions during Phase A returns a clear error message directing the agent to wait for Phase B solicitation.

### D11: Session Recovery & Dispatcher Resilience (M5.8)

**Decision:** DB-backed auto-recovery. See M4 SPEC Section 5.1-5.6 for full lifecycle.

**On server restart:**
1. `lifespan()` queries `sim_runs` (active/pre_start only) + `ai_agent_sessions` (active/ready)
2. For each qualifying sim: creates dispatcher, calls `recover_from_db()`
3. **Always recreates** Anthropic sessions — reconnecting old sessions is unreliable (zombie sessions pass health-check but never respond). Recreation takes ~10s per agent.
4. Recovery pulse sent with agent's saved memories: "Read your notes, continue your strategy"
5. All agents set to IDLE after recovery — old state meaningless after restart
6. Dispatch + auto-pulse + meeting monitor loops restart automatically
7. Init/recovery race prevention via `_initializing_sims` lock

**No manual "Initialize AI Agents" needed after restart.** Moderator only clicks it once at SIM start.

**Verified (2026-04-29):** 3 agents auto-recovered, dispatch loop delivering events, avatar conversations working after restart.

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

## 10. Build Status & Remaining Work

### Completed (Phases 1-8)

| Phase | Status | Date |
|-------|--------|------|
| Phase 1: Foundation (Layer 1, 16 tools, session manager) | DONE | 2026-04-21 |
| Phase 2: Orchestrator Core (dispatch loop, pulses, busy state) | DONE | 2026-04-22 |
| Phase 3: Solo Agent Lifecycle (1 agent, full round) | DONE | 2026-04-23 |
| Phase 4: Multi-Agent (3 agents parallel) | DONE | 2026-04-25 |
| Phase 5: Conversations (AI-AI text meetings) | DONE | 2026-04-27 |
| Phase 6: Mixed Mode (AI-Human text chat) | DONE | 2026-04-28 |
| Phase 7: Observability (dashboard, agent detail, freeze/resume) | DONE | 2026-04-28 |
| Phase 8: Voice (ElevenLabs, mode popup, prompt override) | DONE | 2026-04-29 |

### Remaining Work

| # | Item | Category | Priority | Effort |
|---|------|----------|----------|--------|
| 1 | **Multi-round lifecycle test** — agents across R0→R1→R2 with memory persistence, Phase A/B transitions, batch solicitation | Testing | HIGH | 1 day |
| 2 | **10+ agents simultaneously** — scale from 3 to 10-21 agents, verify performance and cost | Testing | HIGH | 0.5 day |
| 3 | **AI-AI meeting test** — verify `run_text_meeting()` works after dispatcher fixes | Testing | HIGH | 0.5 day |
| 4 | **Transcript delivery verification** — confirm Brain receives transcript, reflects, updates memory | Testing | HIGH | 0.5 day |
| 5 | **Phase B solicitation test** — batch decisions (budget/tariffs/sanctions) + troop movement | Testing | HIGH | 0.5 day |
| 6 | **Critical interrupt test** — nuclear launch, direct attack → Tier 1 delivery during meeting | Testing | MEDIUM | 0.5 day |
| 7 | **Voice transcript on end** — verify voice messages compiled into transcript, delivered to Brain | Testing | MEDIUM | 0.5 day |
| 8 | **`meetings.modality` tracking** — write 'text'/'voice' to DB on mode select | Code | LOW | 0.5 hr |
| 9 | **Voice fallback to text** — if ElevenLabs connection fails before meeting starts, switch to text | Code | MEDIUM | 2 hr |
| 10 | **Active meetings mode indicator** — show text/voice icon in participant dashboard meeting cards | Code | LOW | 1 hr |
| 11 | **Monitoring metrics** — actions/round, tokens/pulse, cost/agent displayed in dashboard | Code | MEDIUM | 0.5 day |
| 12 | **Cross-browser testing** — Safari desktop, Safari iOS, Chrome Android | Testing | HIGH | 0.5 day |
| 13 | **Round restart test** — verify AI sessions survive, round data clears, agents get fresh context | Testing | HIGH | 0.5 day |
| 14 | **Phase 9: All Roles** — multi-role per country, role-specific prompts, position change handling | Code + Test | DEFERRED | 2-3 days |

**Priority grouping:**
- **Sprint A (testing, no code):** Items 1-7. Validate everything works end-to-end. ~3 days.
- **Sprint B (small code items):** Items 8-11. Polish. ~1 day.
- **Sprint C (cross-browser + round restart):** Items 12-13. Production readiness. ~1 day.
- **Deferred:** Item 14 (all roles) — not needed for first production SIMs with HoS-only AI.

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

---

## 13. Agent DB Tables

Four tables support M5 agent state. All created via Supabase migrations.

### `ai_agent_sessions`
Tracks active Claude Managed Agent sessions. One row per sim_run + role.

| Column | Type | Purpose |
|--------|------|---------|
| `id` | UUID PK | Row identifier |
| `sim_run_id` | UUID | Which simulation |
| `role_id` | TEXT | Which role this agent plays |
| `country_code` | TEXT | Country shorthand |
| `agent_id` | TEXT | Anthropic Agent ID |
| `environment_id` | TEXT | Anthropic Environment ID |
| `session_id` | TEXT | Anthropic Session ID (for reconnect) |
| `status` | TEXT | `initializing` / `ready` / `active` / `frozen` / `terminated` / `archived` |
| `model` | TEXT | LLM model used (default: `claude-sonnet-4-6`) |
| `round_num` | INT | Current round the agent is in |
| `total_input_tokens` | BIGINT | Cumulative input token usage |
| `total_output_tokens` | BIGINT | Cumulative output token usage |
| `events_sent` | INT | Events delivered to this agent |
| `actions_submitted` | INT | Actions this agent has submitted |
| `tool_calls` | INT | Total tool calls made |
| `metadata` | JSONB | Extensible metadata |

Unique constraint: `(sim_run_id, role_id)`.

### `agent_event_queue`
Unified event queue for all AI agent event delivery. The EventDispatcher reads pending events and delivers to idle agents.

| Column | Type | Purpose |
|--------|------|---------|
| `id` | UUID PK | Row identifier |
| `sim_run_id` | UUID | Which simulation |
| `role_id` | TEXT | Target agent |
| `tier` | INT | Priority: 1 (critical, <5s), 2 (urgent, <10s), 3 (routine, batched) |
| `event_type` | TEXT | Event category (see event types table below) |
| `message` | TEXT | Human-readable event content delivered to agent |
| `metadata` | JSONB | Structured event data |
| `processed_at` | TIMESTAMPTZ | NULL while pending, set when delivered |
| `processing_error` | TEXT | Error message if delivery failed |

Indexed on `(sim_run_id, role_id, tier) WHERE processed_at IS NULL` for fast pending-event lookup.

**Event Types:**

| Event Type | Tier | Purpose |
|------------|------|---------|
| `round_pulse` | 3 | Regular pulse during Phase A (batched events + situation update) |
| `critical_interrupt` | 1 | Existential events: nuclear launch, direct attack on territory |
| `manual_pulse` | 2 | Moderator-triggered manual pulse |
| `batch_decision_request` | 1 | Solicits batch decisions (budget, tariffs, sanctions, OPEC) at Phase B start |
| `movement_request` | 1 | Solicits troop movements (move_units) after engine processing in Phase B |

### `agent_memories`
Self-authored agent memory. Agents write notes via `write_notes` tool and recall via `read_notes`. Survives session crashes.

| Column | Type | Purpose |
|--------|------|---------|
| `id` | UUID PK | Row identifier |
| `sim_run_id` | UUID | Which simulation |
| `country_code` | TEXT | Which country's agent |
| `scenario_id` | UUID | Scenario reference |
| `memory_key` | TEXT | Agent-chosen key (e.g. `strategy`, `round_2_reflection`) |
| `content` | TEXT | Free-form memory content |
| `round_num` | INT | Round when written/updated |
| `updated_at` | TIMESTAMPTZ | Last update timestamp |

Upsert key: `(sim_run_id, country_code, memory_key)`. Agent decides what to remember.

### `agent_decisions`
Audit trail of every action an AI agent submits. Written before dispatch, updated with result.

| Column | Type | Purpose |
|--------|------|---------|
| `id` | UUID PK | Row identifier |
| `sim_run_id` | UUID | Which simulation |
| `scenario_id` | UUID | Scenario reference |
| `country_code` | TEXT | Acting country |
| `action_type` | TEXT | Canonical action type (e.g. `set_budget`, `ground_attack`) |
| `action_payload` | JSONB | Full validated action payload |
| `rationale` | TEXT | Agent's stated reason for the action |
| `validation_status` | TEXT | `passed` → `executed` or `dispatch_failed` |
| `validation_notes` | TEXT | Narrative from dispatch result |
| `round_num` | INT | Round when submitted |

---

## 14. M4↔M5 Integration

### API Endpoints (all under `/api/sim/{sim_id}/ai/`)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/ai/initialize` | POST | Create managed agent sessions for all AI roles, start dispatcher loop |
| `/ai/run-round` | POST | Enqueue `round_pulse` (Tier 3) for all agents — triggers round activity |
| `/ai/send-pulse` | POST | Send a manual pulse to all idle agents |
| `/ai/status` | GET | Dashboard data: agent states, costs, queue depths, token usage |
| `/ai/freeze/{role_id}` | POST | Freeze one agent (stops receiving events) |
| `/ai/resume/{role_id}` | POST | Resume one frozen agent (batched events delivered) |
| `/ai/freeze-all` | POST | Global AI pause — humans continue |
| `/ai/resume-all` | POST | Resume all frozen agents |
| `/ai/interrupt` | POST | Send Tier 1 critical interrupt to specific agents (<5s delivery) |
| `/ai/shutdown` | POST | Archive all sessions, stop dispatcher |
| `/ai/restart` | POST | Full cleanup: archive sessions, clear queue, optionally clear memories/decisions |
| `/ai/trigger` | POST | Legacy stub: trigger AI decisions via simple defaults (pre-M5) |

### How M4 Starts AI Agents

1. Moderator clicks "Initialize AI Agents" in the facilitator UI.
2. Frontend calls `POST /ai/initialize` with optional `role_ids` and `model`.
3. Backend creates an `EventDispatcher` for the sim, which creates Managed Agent sessions (one per AI role) via the Anthropic SDK.
4. Sessions are recorded in `ai_agent_sessions` with status `initializing` -> `ready`.
5. The dispatcher's background loop starts, delivering any enqueued init events.

### How M4 Stops AI Agents

1. Moderator clicks "Shutdown AI" or sim completes.
2. Frontend calls `POST /ai/shutdown`.
3. Dispatcher archives all Anthropic sessions and sets DB status to `archived`.
4. Dispatcher is removed from the in-memory registry.
5. For full reset (e.g. sim restart): `POST /ai/restart` clears queue, optionally clears memories and decisions.

### How AI Actions Flow Through the Dispatcher

1. Agent receives an event (pulse, interrupt) via the EventDispatcher.
2. Agent reasons using its tools (`get_my_country`, `get_relationships`, etc.) — these are read-only DB queries.
3. Agent calls `submit_action(action)` tool with a validated payload.
4. `ToolExecutor.submit_action()` validates the payload via Pydantic action schemas.
5. The action is recorded in `agent_decisions` (audit trail).
6. The action is dispatched via `engine.services.action_dispatcher.dispatch_action()` — the **same pipeline** used for human-submitted actions.
7. `agent_decisions` is updated with the dispatch result (`executed` or `dispatch_failed`).
8. The result is returned to the agent as tool output.

### How Round Transitions Notify AI Agents

1. M4's round advancement logic (facilitator clicks "Next Round" or auto-advance triggers).
2. Frontend or orchestrator calls `POST /ai/run-round` with the new round number.
3. The endpoint enqueues a `round_pulse` event (Tier 3) for every registered agent.
4. The EventDispatcher's background loop picks up pending events and delivers them to idle agents.
5. Agents that are `FROZEN` or `IN_MEETING` receive their events when they return to `IDLE` state.
6. Critical events (nuclear launch, direct attack) use `POST /ai/interrupt` for Tier 1 delivery (<5s).

---

*Decisions made in collaboration with Marat Atn, 2026-04-21. All Q1-Q14 resolved. Status updated 2026-04-24: Phase-aware action restrictions (D10) and event types added. PAUSED for stage gate review.*
