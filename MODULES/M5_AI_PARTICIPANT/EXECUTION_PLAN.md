# M5 AI Participant — Execution Plan

**Version:** 1.0
**Date:** 2026-04-21
**Status:** APPROVED — Ready for execution
**SPEC:** `SPEC_M5_AI_PARTICIPANT.md` v1.0

---

## Prerequisites (Before M5 Core)

### P1: Game Rules Reference

**What:** A human-readable document covering all game domains and actions. Not formulas — logic, steps, dependencies. "X substantially impacts Y" not "X generates 2.3 points of Y."

**Purpose:** Feeds both the AI agent's Layer 1 prompt AND a future human reference section in M6.

**Source material:**
- `3 DETAILED DESIGN/DET_D8_FORMULAS_v3.md` — all formulas (extract logic, discard numbers)
- `3 DETAILED DESIGN/CARDS/` — 28 action specification cards
- `3 DETAILED DESIGN/CONTRACTS/` — action contracts
- `2 SEED/C_MECHANICS/` — domain mechanics
- `engine/agents/action_schemas.py` — current 33 action types with Pydantic models

**Deliverable:** `MODULES/M5_AI_PARTICIPANT/GAME_RULES_REFERENCE.md`

**Structure (proposed):**

```
1. THE WORLD
   - 20 countries, geography, theaters, chokepoints
   - Round structure (phases A/B/C, what happens when)
   - Time: 6-8 rounds, each = ~6 months simulated

2. ECONOMIC DOMAIN
   - GDP: what drives growth, what causes decline
   - Budget: social spending ↔ stability, military ↔ force maintenance, tech ↔ R&D
   - Treasury: income sources, spending drains, debt risk
   - Tariffs: levels 0-3, bilateral impact, who gets hurt more
   - Sanctions: levels 0-3, coalition stacking, cost to imposer
   - Oil & OPEC: production decisions, price impact, chokepoint dependency
   - Trade: balance, dependencies, Formosa semiconductor risk

3. MILITARY DOMAIN
   - Unit types: ground, naval, tactical air, strategic missiles, air defense
   - Movement: how units move, theater vs global, embarking
   - Combat: attack types (ground, air, naval, bombardment, blockade)
   - Authorization: who can order what, co-sign requirements
   - Nuclear: levels 0-3, R&D, test, authorize, launch, intercept chain
   - Casualties, capture, occupation

4. POLITICAL DOMAIN
   - Stability: what raises it, what crashes it
   - Elections: when, how, consequences of losing
   - Regime types: democracy vs autocracy (different powers)
   - Public statements: narrative power, alliance signaling
   - Propaganda, repression (autocracy tools)

5. DIPLOMATIC DOMAIN
   - Transactions: 10 types (arms sale, treaty, alliance, basing rights, etc.)
   - Propose → evaluate → confirm flow
   - Organizations: Western Treaty, Eastern Pact, OPEC, UNSC, etc.
   - Org meetings: who can call, what they accomplish
   - War declarations, ceasefires, peace treaties

6. COVERT DOMAIN
   - Operation types: espionage, sabotage, cyber, disinformation, election meddling
   - Intelligence pool: limited cards per round
   - Detection risk, success probability factors
   - Assassination (rare, high-risk)

7. TECHNOLOGY DOMAIN
   - R&D investment: nuclear and AI tracks
   - Level progression: what each level unlocks
   - Strategic implications of tech superiority

8. ACTION QUICK REFERENCE
   - All 33 action types in one table
   - For each: what it does, who can do it, what it costs, what it requires
```

**🔴 MARAT INPUT NEEDED:** Review structure above. Any domains or mechanics missing? Any emphasis to adjust? I'll draft the full document and bring it for review.

**Effort:** 1 day to draft, 1 review cycle

---

### P2: Chat Backend (Extend Existing)

**What:** Extend existing meeting invitation system with chat message persistence and real-time delivery.

**Existing infrastructure (already built):**
- ✅ `meeting_invitations` table in Supabase (full schema: status, expiration, responses JSONB)
- ✅ `invite_to_meet` + `respond_meeting` actions in `action_dispatcher.py`
- ✅ `ConversationEngine` class in `conversations.py` (502 lines — bilateral flow, intent notes, 8-turn, reflections)
- ✅ Frontend `SetMeetingsForm` with real-time subscriptions
- ✅ `ParticipantDashboard` showing pending invitations

**What's missing (to build):**

| Component | What | Why |
|-----------|------|-----|
| `meetings` table | Chat channel record (who, status, turns, transcript) | Track active conversations |
| `meeting_messages` table | Turn-by-turn message persistence | Real-time chat + AI observation |
| Message API endpoints | Send/receive/list messages | Both human UI and AI tools need this |
| Conversation trigger | "Both accepted → meeting starts" wiring | Currently invitations exist but don't trigger execution |
| Transcript persistence | Save completed transcripts to meetings table | Post-meeting review + AI reflection |

**DB Schema (new tables only):**

```sql
-- Meetings (conversation channels)
CREATE TABLE meetings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sim_run_id UUID REFERENCES sim_runs(id),
    invitation_id UUID REFERENCES meeting_invitations(id),
    round_num INTEGER,
    status TEXT CHECK (status IN ('active', 'completed', 'abandoned')) DEFAULT 'active',
    participant_a_role_id TEXT NOT NULL,
    participant_a_country TEXT NOT NULL,
    participant_b_role_id TEXT NOT NULL,
    participant_b_country TEXT NOT NULL,
    agenda TEXT,
    modality TEXT CHECK (modality IN ('text', 'voice', 'hybrid')) DEFAULT 'text',
    turn_count INTEGER DEFAULT 0,
    max_turns INTEGER DEFAULT 16,
    started_at TIMESTAMPTZ DEFAULT now(),
    ended_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'
);

-- Meeting messages (turn-by-turn chat)
CREATE TABLE meeting_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meeting_id UUID REFERENCES meetings(id),
    role_id TEXT NOT NULL,
    country_code TEXT NOT NULL,
    content TEXT NOT NULL,
    channel TEXT CHECK (channel IN ('text', 'voice', 'system')) DEFAULT 'text',
    turn_number INTEGER,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

**New API Endpoints:**

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/sim/{id}/meetings/{meeting_id}` | Meeting details + messages |
| POST | `/api/sim/{id}/meetings/{meeting_id}/message` | Send a message |
| POST | `/api/sim/{id}/meetings/{meeting_id}/end` | End the meeting |
| GET | `/api/sim/{id}/meetings/active/{role_id}` | My active meetings |

**Existing endpoints (keep as-is):** `invite_to_meet` and `respond_meeting` actions via `/api/sim/{id}/action`.

**Marat decisions:**
- Facilitator sees meetings only on demand (via AI participant detail view), not real-time dashboard
- No constraints on who can meet whom (for now)

**Effort:** 1-2 days (much less than original estimate — extending, not building)

---

### P3: Chat UI (Frontend)

**What:** Telegram-style text chat interface for meetings. Full-screen on mobile, standard wide panel on desktop. Shared by all conversation types.

**Entry point:** From existing `set_meetings` action flow. Once a meeting is confirmed (invitation accepted), the chat interface opens automatically.

**Design principles (from Marat):**
- Full-screen on mobile (most participants use phones)
- Standard wide chat panel on desktop (within actions area)
- Telegram-style UX — simple, great design, no fancy features
- Typing animation (messages appear gradually, not instant)
- Same interface for AI↔Human, Human↔Human, and AI↔AI (observable)
- Voice button (🎤) visible but disabled in v1 — placeholder for ElevenLabs v2

**Components:**

| Component | What |
|-----------|------|
| **MeetingChat** | Full-screen (mobile) / wide panel (desktop) chat view |
| **TypingAnimation** | Messages reveal gradually (proportional to length) |
| **MessageInput** | Text input + send button. Voice button (disabled v1). |

**Layout (phone — full screen):**

```
┌──────────────────────────┐
│ ← Meeting with Dealer     │
│ Columbia | Round 3         │
│ ─────────────────────────│
│                           │
│         ┌───────────┐    │
│         │ Let's talk │    │
│         │ about trade│    │
│         └───────────┘    │
│                      14:23│
│                           │
│ ┌────────────┐           │
│ │ I'm open to│           │
│ │ discussion │           │
│ └────────────┘           │
│ 14:24                    │
│                           │
│         ┌───────────┐    │
│         │ typing... │    │
│         └───────────┘    │
│                           │
│ ─────────────────────────│
│ [Type a message...   📎🎤]│
└──────────────────────────┘
```

- Left-aligned = other person's messages (with character name + country)
- Right-aligned = my messages
- Typing indicator when other side is composing
- Minimal chrome — conversation is the focus
- Back button returns to game view

**Invitation display:** Uses existing `SetMeetingsForm` fields (character name, country, message, optional theme).

**Real-time:** Supabase Realtime subscription on `meeting_messages` filtered by `meeting_id`.

**Effort:** 2-3 days (React component + Realtime + responsive + typing animation)

---

## Phase 1: Foundation

**After prerequisites are done.**

### 1A: Expand Layer 1 System Prompt (~5-8K tokens)

| Task | Source | Output |
|------|--------|--------|
| Game rules context builder | `GAME_RULES_REFERENCE.md` → condensed for prompt | `engine/agents/managed/game_rules_context.py` |
| Meta-awareness context | Pulse system, tools, timing, busy state, limits | `engine/agents/managed/meta_context.py` |
| Character trait generation | Thomas-Kilmann + temperament framework | Added to `system_prompt.py` |
| Global assertiveness dial | Inject cooperation/competition framing | Added to `system_prompt.py` |
| Confidential brief injection | From role's `brief_file` or artefacts | Added to `system_prompt.py` |

### 1B: Expand to 16 Tools

| Tool | Status | Work Needed |
|------|--------|-------------|
| `get_my_country` | DONE (spike) | — |
| `get_my_forces` | DONE (spike) | — |
| `get_relationships` | DONE (spike) | — |
| `get_pending_proposals` | DONE (spike) | — |
| `get_recent_events` | DONE (spike) | — |
| `submit_action` | DONE (spike) | — |
| `write_notes` | DONE (spike) | — |
| `read_notes` | Map to existing `read_memory` + `list_my_memories` | Minor wiring |
| `get_country_info(country)` | NEW | Query public info for any specific country |
| `get_hex_info(row, col)` | EXISTS in tools.py | Wire into managed tool definitions |
| `get_organizations` | EXISTS in tools.py | Wire into managed tool definitions |
| `get_my_artefacts` | NEW | Query artefacts table for this role |
| `get_action_rules(type)` | NEW | Return rules for a specific action type (from reference) |
| `request_meeting(country, agenda)` | NEW | Write to meeting_invitations table |
| `respond_to_invitation(id, decision)` | NEW | Update invitation status |
| `send_message(meeting_id, text)` | NEW | Write to meeting_messages table |

### 1C: Harden Session Manager

| Task | What |
|------|------|
| Health check | `sessions.retrieve()` before every pulse, handle stale sessions |
| Recovery flow | Detect terminated → rebuild from DB memory → new session |
| Session metadata | Store session_id, agent_id, role_id, round_num in our DB |
| Cost tracking | Accumulate tokens per agent, expose via API |
| Error handling | Graceful degradation on API errors, rate limits, timeouts |

### 1D: Character Trait Framework

**Dimensions (proposed):**

| Dimension | Scale | Example |
|-----------|-------|---------|
| **Conflict style** (Thomas-Kilmann) | competing / collaborating / compromising / avoiding / accommodating | Dealer: competing |
| **Risk orientation** | risk-averse ↔ risk-seeking | Scale 1-5 |
| **Decision speed** | deliberate ↔ impulsive | Scale 1-5 |
| **Trust default** | suspicious ↔ trusting | Scale 1-5 |
| **Communication style** | guarded ↔ transparent | Scale 1-5 |
| **Strategic horizon** | short-term tactical ↔ long-term strategic | Scale 1-5 |

At initialization, the agent self-assigns these based on its character identity + the global assertiveness dial. They become part of the system prompt:

```
Your character traits (self-assigned based on your identity):
- Conflict style: Competing — you push for your interests directly
- Risk orientation: 3/5 — moderate, calculated risks
- Decision speed: 4/5 — you prefer to act decisively
- Trust default: 2/5 — suspicious, verify before trusting
- Communication: 2/5 — guarded, reveal little unless strategic
- Strategic horizon: 4/5 — you think in multi-round arcs
```

**Effort Phase 1 total:** 3-4 days

---

## Phase 2: Orchestrator Core

### 2A: Pulse Scheduler

| Task | What |
|------|------|
| Round timing calculator | Given round duration + pulse count → schedule |
| Pulse dispatcher | Send pulse event to agent session at scheduled time |
| Event collector | Gather all events since last pulse, categorize public/private |
| Resource dashboard builder | Meetings remaining, intel cards, mandatory status, pulse N of M |

**Pulse Event Format (proposed — 🔴 MARAT REVIEW):**

```json
{
  "type": "round_pulse",
  "round_num": 3,
  "pulse": 4,
  "total_pulses": 8,
  "time_remaining": "24 minutes",

  "public_events": [
    {"type": "public_statement", "by": "Pathfinder (Sarmatia)", "summary": "..."},
    {"type": "military_move", "by": "Cathay", "summary": "Naval units moved to Formosa Strait"}
  ],

  "private_events": [
    {"type": "intel_report", "summary": "Espionage reveals Cathay naval buildup..."},
    {"type": "covert_result", "op": "sabotage_nuclear", "target": "persia", "result": "succeeded"}
  ],

  "pending_items": [
    {"type": "meeting_invitation", "from": "Helmsman (Cathay)", "agenda": "Trade terms"},
    {"type": "proposal", "from": "Beacon (Ruthenia)", "summary": "Arms purchase request"}
  ],

  "your_status": {
    "state": "IDLE",
    "meetings_used": 2,
    "meetings_remaining": 3,
    "intel_cards_remaining": 1,
    "actions_this_round": 3,
    "mandatory_submitted": {
      "budget": false,
      "tariffs": true,
      "sanctions": true
    }
  }
}
```

### 2B: Event Batching & Critical Interrupts

| Event Category | Delivery | Examples |
|----------------|----------|---------|
| Normal | Batched into next pulse | Public statements, market changes, troop movements |
| Urgent | Next pulse, highlighted | Proposals with deadline, meeting requests |
| Critical | Immediate interrupt | Nuclear launch detected, direct attack on territory, leader incapacitated |

### 2C: Busy State Machine

```
IDLE ──→ ACTING (pulse received, agent processing)
  │         │
  │         └──→ IDLE (agent done with pulse)
  │
  └──→ IN_MEETING (meeting accepted)
          │
          └──→ IDLE (meeting ended)

FROZEN ←── any state (moderator freeze)
  │
  └──→ previous state (moderator resume, batched events delivered)
```

### 2D: Multi-Agent Parallel Execution

- All agents receive pulses in parallel (async)
- Each agent processes independently
- Orchestrator tracks all agent states
- Conversation requests detected and queued for next pulse cycle

**Effort Phase 2:** 3-4 days

---

## Phases 3-9: Summary

| Phase | What | Effort |
|-------|------|--------|
| **3: Solo Full Lifecycle** | 1 agent through complete round. Co-moderator auto-advance. | 1-2 days |
| **4: Multi-Agent** | 10-21 agents parallel, no conversations. First full unmanned test. | 1-2 days |
| **5: Conversations** | AI↔AI bilateral via chat system. Turn relay. Meeting tools wired. | 2-3 days |
| **6: Mixed Mode** | AI + Human in same SIM. AI↔Human text chat. | 2-3 days |
| **7: Observability** | AI dashboard, agent log, freeze/resume, moderator override. | 2-3 days |
| **8: All Roles** | Multi-role per country. Role-specific prompts. Position changes. | 2-3 days |
| **9: Voice** | ElevenLabs avatar. Intent notes. Transcript capture. KING port. | 3-4 days |

---

## Total Effort Estimate

| Block | Days |
|-------|------|
| Prerequisites (P1 + P2 + P3) | 4-6 days |
| Phase 1: Foundation | 3-4 days |
| Phase 2: Orchestrator | 3-4 days |
| Phase 3: Solo lifecycle | 1-2 days |
| Phase 4: Multi-agent | 1-2 days |
| Phase 5: Conversations | 2-3 days |
| Phase 6: Mixed mode | 2-3 days |
| Phase 7: Observability | 2-3 days |
| Phase 8: All roles | 2-3 days |
| Phase 9: Voice | 3-4 days |
| **Total** | **~22-32 days** |

**Critical path to first unmanned test (P1+P2 → Phases 1-4):** ~10-14 days.
**Critical path to AI↔AI conversations (add Phase 5):** ~12-17 days.
**Critical path to mixed mode with humans (add P3 + Phase 6):** ~16-22 days.

---

## Items Awaiting Marat Input

| Item | Question | Where |
|------|----------|-------|
| 🔴 P1 | Game rules reference structure — review proposed outline | P1 section above |
| 🔴 P2 | Existing meeting tables? Facilitator visibility? Who can meet whom? | P2 section above |
| 🔴 P3 | Chat UI: tab vs overlay? Desktop layout? Telegram features? Invitation display? | P3 section above |
| 🔴 Phase 2A | Pulse event format — review proposed JSON | Phase 2A section above |

---

*Plan approved for execution 2026-04-21. Prerequisites first, then sequential phases. Parallel tracks possible: P2+P3 can overlap, Phases 5+7 can overlap after Phase 4.*
