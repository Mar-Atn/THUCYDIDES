# SPEC: M5.7 — Avatar Conversation System

**Version:** 3.0
**Date:** 2026-04-29
**Status:** Architecture finalized. Implementation gaps identified (see Section 12).
**Depends on:** M5 (Managed Agents), M4 (Sim Runner), M6 (Human Interface), M2 (Communication)
**Reference:** KING voice architecture, ElevenLabs Conversational AI SDK

---

## 1. Problem

The original meeting system routed all conversation through the Managed Agent (full Claude session with SSE stream, tool calls, 30-60s per turn). Too slow, too expensive, unnatural.

## 2. Solution: Brain and Mouth

The AI participant has a **Brain** and a **Mouth**.

**The Brain** (Managed Agent) is a full Claude session with tools, memory, strategic reasoning, and world knowledge. It thinks slowly, deeply, and deliberately. It makes decisions, reads intelligence, submits actions, manages alliances. It runs on the Anthropic Managed Agents SDK with a persistent session.

**The Mouth** (Conversation Avatar) is a lightweight, stateless agent — a Claude API call (text) or ElevenLabs voice agent (voice). It speaks fast: 1-3 seconds for text, sub-second for voice. It has no tools, no memory, no ability to take game actions. It can only talk.

**The Brain never speaks directly to other participants. It always speaks through the Mouth.**

**The Managed Agent NEVER writes to meeting_messages.** Only the avatar does.

```
THE BRAIN (Managed Agent)
|
|  Knows the full avatar architecture (explained in system prompt).
|  Understands: "My avatar has ONLY what I give it. If I don't
|  include something, my avatar won't know it."
|
|  At initialization:
|  +-- Generates AVATAR IDENTITY & CONTEXT (self-authored)
|      Comprehensive self-portrait + world knowledge
|      Written to agent_memories key="avatar_identity"
|
|  When inviting or accepting a meeting:
|  +-- Generates INTENT NOTE (self-authored)
|      Tactical briefing for THIS specific meeting
|      Required field on request_meeting / respond_to_invitation
|
|  After each meeting:
|  +-- Receives TRANSCRIPT for reflection & memory update
|
+---> THE MOUTH (Conversation Avatar)
      |
      |  Context = Avatar Identity + Intent Note + Behavior Rules
      |  Stateless. No tools. No memory. No game actions.
      |
      +-- MODE A: Text Chat (Claude Messages API, ~1-3s/response)
      +-- MODE B: Voice Call (ElevenLabs, sub-second response)
```

---

## 3. The Two Context Documents

The Mouth receives exactly **two documents** from the Brain. These are the avatar's entire understanding of reality.

### 3.1 Avatar Identity & Context (generated once at initialization)

The Brain's comprehensive self-portrait and world knowledge, written for an agent that has NO other source of information.

**Self-authorship principle:** The Brain generates this document itself, using its full knowledge and judgment. We provide recommended structure in the system prompt, but the Brain decides what goes in, how detailed it is, and how to organize it. The Brain knows: *"My avatar will ONLY have this document and a per-meeting intent note. If I don't put something here, my avatar won't know it."*

**Recommended scope** (Brain adapts as it sees fit):
- **Who I am**: Name, title, personality, communication style, age, temperament
- **My country**: GDP, stability, military, nuclear/AI capability, key strengths and vulnerabilities
- **My objectives**: Top strategic goals, current priorities
- **The SIM world** (critical for informed conversation):
  - All countries with their leaders' names
  - Key organizations and memberships
  - Geography: theaters, chokepoints, contested areas
  - Current conflicts and tensions
  - My alliances, rivalries, and relationships
- **My positions on key issues**: Where I stand, red lines, negotiating posture

**Size**: No artificial limit. Quality matters more than brevity. A well-informed avatar needs sufficient context — 1,000-2,000 words is typical. Prompt caching makes cost negligible after the first turn.

**Storage**: `agent_memories` table, key = `avatar_identity`, keyed by `(sim_run_id, country_code)`

**Lifecycle**:
1. Generated at AI participant initialization (the Brain is prompted to write it as one of its first actions)
2. Persists across rounds
3. The Brain can update it any time via `write_notes` — especially after major changes (new war, regime change, alliance shift, major deal)
4. The Brain owns this entirely — system never overwrites it

**Voice consideration**: ElevenLabs prompt override has practical size limits (~5,000-10,000 characters depending on plan). For voice calls, a more concise version may be needed. The text chat avatar has no such constraint.

### 3.2 Intent Note (generated per meeting)

The Brain's tactical briefing for ONE specific meeting. Written at the exact moment the Brain decides to invite or accept — in the same cognitive cycle, not as a separate step.

**Self-authorship principle:** Same as above. The Brain knows: *"My avatar will walk into this meeting with my Identity document and THIS note. This is my only way to guide the conversation."*

**Recommended scope** (Brain adapts):
- **Objective**: What to achieve in this meeting (1-2 sentences)
- **Approach**: Key arguments, proposals, questions to ask, what to probe, concessions available
- **Boundaries**: What NOT to reveal, what NOT to agree to, red lines
- **Tone**: How to sound — warm/cold, cautious/bold, formal/casual
- **Context**: Recent events relevant to this counterpart, shared history, intelligence about their position

**Size**: No artificial limit. Short for routine meetings, detailed for critical negotiations. The Brain decides.

**Timing**: The intent note is a **required field** on `request_meeting` and an **expected field** on `respond_to_invitation(accept)`. The invitation or acceptance does NOT leave without the intent note being written and saved.

**Storage flow**:
- Inviter's intent: stored on invitation (`responses._inviter_intent_note`), transferred to `meetings.metadata.intent_note_a` when meeting is created
- Accepter's intent: stored directly in `meetings.metadata.intent_note_b`

---

## 4. What the Brain Knows About Avatars

The Brain's system prompt (Layer 1) includes an explicit section explaining the avatar architecture. The Brain understands:

1. It communicates through avatars, never directly
2. The avatar has ONLY the two context documents — nothing else
3. If the Brain doesn't include something in the Identity or Intent Note, the avatar won't know it
4. After meetings, the Brain receives transcripts for reflection
5. The Brain can update its Avatar Identity at any time via `write_notes`
6. The quality of the Intent Note directly determines conversation quality

This is already implemented in `system_prompt.py` as the `AVATAR_ARCHITECTURE` constant, injected into every Managed Agent's Layer 1 prompt.

---

## 5. Conversation Modes

### 5.1 Mode A: Text Chat (Claude API)

**When:** AI-AI meetings (always), AI-Human meetings (when human selects text).

- Claude Messages API (NOT managed agent session) — fully stateless
- Model from `ai_settings.model_conversations` (adjustable without reinitialization)
- System prompt = Avatar Identity + Intent Note + TEXT_CHAT_RULES
- Prompt caching enabled (~1-3s response time)
- Messages saved to `meeting_messages` table (channel='text')
- Human speaks first. Avatar responds. No system-generated opening message.

### 5.2 Mode B: Voice Call (ElevenLabs)

**When:** AI-Human meetings, when human selects voice in mode popup.

- ElevenLabs Conversational AI via React SDK (`useConversation` + `ConversationProvider`)
- System prompt override = Avatar Identity + Intent Note + VOICE_RULES
- ElevenLabs agent_id from `roles.elevenlabs_agent_id`
- Sub-second voice responses
- Human speaks first. ElevenLabs agent responds.
- Voice messages saved to `meeting_messages` (channel='voice')
- Live transcript visible (toggle on/off)

### 5.3 AI-AI Text Chat

Automated turn-by-turn via `run_text_meeting()`:
1. Avatar A speaks -> written to `meeting_messages`
2. Avatar B responds -> written to `meeting_messages`
3. Repeat until max turns (16) or `[END MEETING]` marker
4. Both transcripts delivered to respective Managed Agents

---

## 6. Meeting Lifecycle

### 6.1 Invitation

Human or AI initiates meeting. AI includes `intent_note` in `request_meeting` tool call. The intent note is written in the same cognitive cycle — the agent doesn't send the invitation without it.

### 6.2 Acceptance

Counterpart accepts. AI includes `intent_note` in `respond_to_invitation(accept)` call. Meeting record created. Intent notes transferred to `meetings.metadata`. AI participant(s) set to `IN_MEETING`.

### 6.3 Mode Selection (Human-AI only)

Human sees popup: "Connecting you to [Name], [Country] - [Position]" with **[Text Chat]** and **[Voice Call]** buttons.

- Voice Call button only visible if AI has `elevenlabs_agent_id`
- Human-Human meetings: no popup, always text
- AI-AI meetings: always text, automated
- Selected mode written to `meetings.modality` ('text' or 'voice')
- **No live switching.** One mode per meeting. End and reconnect to change.
- If voice connection fails before meeting starts: fallback to text chat
- If meeting already started: no mode change allowed

### 6.4 Conversation

**Text:** Human types first -> avatar responds (1-3s). Max 16 turns. 15-minute auto-end.

**Voice:** Human speaks first -> ElevenLabs responds (sub-second). End by button press.

**AI-AI:** Automated, 16 turns, ~60s total.

### 6.5 Meeting End

Whoever decides to end it — ends it. For voice: ending the call = ending the meeting.

1. `end_meeting` API called (by human UI or by avatar at max turns)
2. Transcript compiled from `meeting_messages` and saved to `meetings.transcript`
3. Meeting status -> `completed`
4. AI participant(s) set to `IDLE`
5. Transcript delivered to Managed Agent as Tier 2 event for reflection

**No reconnection.** Meeting is over. To talk again: initiate a new meeting.

For text chat: human can reopen the chat to read history (read-only after end). For voice: call is over.

### 6.6 No System-Generated Opening Message

The avatar does NOT speak first. There is no `_avatar_opening_message`. The human opens the conversation, and the avatar responds using Identity + Intent Note.

For AI-AI meetings: Avatar A speaks first (handled by `run_text_meeting` which starts with A).

### 6.7 Transcript Delivery to the Brain

After meeting ends, the Brain receives the full transcript as a Tier 2 event:

```
MEETING COMPLETED
Meeting with: [counterpart name], [country] - [position]
Duration: [X messages / Y minutes]
Mode: [text/voice]

[Full transcript]

Reflect on this conversation. Update your notes and strategy as needed.
```

The Brain can then:
- Update Avatar Identity if the world changed significantly
- Write strategic notes about the counterpart
- Adjust actions based on what was learned
- Plan follow-up meetings with new intent notes

---

## 7. Stateless Avatar — No Dispatcher Dependency

**Critical architectural principle:** The avatar response mechanism MUST NOT depend on in-memory dispatcher state.

The avatar service is completely stateless:
- Reads Avatar Identity from `agent_memories` table (DB)
- Reads Intent Note from `meetings.metadata` (DB)
- Reads conversation history from `meeting_messages` (DB)
- Calls Claude API (stateless)
- Writes response to `meeting_messages` (DB)

Nothing in this flow requires the dispatcher or the Managed Agent session. The dispatcher is needed for the Brain (event delivery, tool execution), but the Mouth operates independently.

**"Is this an AI role?" check:** When a human sends a message, the backend must determine if the counterpart is an AI (to trigger avatar response). This check MUST use DB state (`roles.user_id IS NULL` or `ai_agent_sessions` table), NOT `dispatcher.agents` (in-memory, lost on restart).

This ensures: if the server restarts mid-meeting, the avatar continues to respond to human messages — even before the Brain's managed sessions are recovered.

---

## 8. Human Participant Experience

### 8.1 Meeting Invitation

Incoming: "[Country] has invited you to a meeting. Agenda: [text]" with **Accept** | **Decline** | **Not now**.

Position tags shown: character name + position (HoS, Diplomat, Military, etc.).

### 8.2 Mode Selection Popup

After acceptance (or when AI accepts human's invitation):

```
+------------------------------------------+
|  Connecting you to...                    |
|                                          |
|  Vizier                                  |
|  Phrygia - Head of State                 |
|                                          |
|  [Text Chat]  [Voice Call]               |
|                                          |
|  Not now                                 |
+------------------------------------------+
```

- Appears for ALL AI counterparts
- Voice Call button only if AI has voice agent assigned
- Human-Human: no popup, straight to text
- Avatar context (identity + intent note) pre-fetched while popup is displayed

### 8.3 Text Chat

Telegram-style. Human types, avatar responds 1-3s. End button in header.

### 8.4 Voice Call

Light theme UI matching the app. Header (name + country + timer), center (waveform), controls (Mute, Phone Mode, Transcript toggle, End Call). Live transcript panel.

### 8.5 Active Meetings

Participant dashboard shows active meetings with:
- Counterpart name + position tag
- Mode indicator (text/voice)
- Text meetings: "Open Chat" button (can rejoin)
- Voice meetings: not shown as rejoinable (voice = live, when you leave it ends)

---

## 9. What the Avatar CANNOT Do

- Take game actions (submit proposals, move units, set tariffs)
- Access the Brain's memory or tools
- Read intelligence reports
- Modify any game state
- Continue after the meeting ends
- Switch between text and voice mid-meeting

---

## 10. Database

### 10.1 Roles Table
- `elevenlabs_agent_id` TEXT NULL

### 10.2 Meetings Table
- `modality` TEXT ('text' | 'voice') — set when human selects mode
- `metadata` JSONB — `intent_note_a`, `intent_note_b`
- `transcript` TEXT — compiled after meeting ends

### 10.3 Meeting Messages
- `channel` TEXT: 'text' | 'voice' | 'system'

### 10.4 Agent Memories
- `avatar_identity` key — comprehensive identity + world context for avatars

### 10.5 AI Agent Sessions (M5.8)
- `agent_state` TEXT (IDLE/ACTING/IN_MEETING/FROZEN) — write-through from dispatcher
- `prompt_hash` TEXT — for smart session recreation on code changes

---

## 11. Voice Agent Assignment

### Template Level (M9)
- Voice Agent dropdown in role editor (fetches from ElevenLabs API)
- Inherited by SimRuns on creation

### SimRun Level (Moderator Dashboard)
- Voice icon per AI agent row
- Click to assign/change voice agent
- Immediate effect

### ElevenLabs Configuration
- Agents pre-created in ElevenLabs dashboard
- Must have "Allow prompt override" enabled
- Opening message configurable in ElevenLabs (overridable from client)

---

## 12. Implementation Status

| Feature | Status | Verified |
|---------|--------|----------|
| Avatar Identity at init (self-authored by Brain) | DONE | 2026-04-29 — rich identities (8-10K chars) |
| Brain knows avatar architecture (system prompt) | DONE | AVATAR_ARCHITECTURE constant in Layer 1 |
| Intent Note in invite/accept (required field) | DONE | 2026-04-29 — rich notes with counterpart context |
| Text chat (AI-Human via Claude API) | DONE | 2026-04-29 — full context, ~1-3s |
| Text chat (AI-AI via run_text_meeting) | DONE | Needs re-test after dispatcher fixes |
| Voice call (ElevenLabs prompt override) | DONE | 2026-04-29 — full context, strategic responses |
| Voice call firstMessage suppression | DONE | `firstMessage: ''` in overrides |
| Mode selection popup | DONE | 2026-04-29 |
| Voice context fetch (direct, not pre-fetch) | DONE | 2026-04-29 — loading spinner until ready |
| Avatar response: DB-based AI check | DONE | `_check_is_ai_role()` — no dispatcher dependency |
| Voice agent assignment UI | DONE | Template editor + AI Dashboard |
| Transcript save + delivery | DONE | Needs verification test |
| Dispatcher resilience (M5.8) | DONE | Always-recreate, init lock, active-sims filter |
| Chat message deduplication | DONE | Optimistic → Realtime replace |
| Tool descriptions (counterpart context reminder) | DONE | Agent told avatar needs WHO in intent note |
| `meetings.modality` tracking | TODO | Write 'text'/'voice' on mode select |
| Voice fallback to text on failure | TODO | |
| Active meetings mode indicator | TODO | |

---

## 13. Open Questions (Resolved)

1. ~~Should AI-AI conversations ever be voice?~~ No. Text only.
2. ~~Meeting duration limits for voice?~~ 15-minute auto-end same as text.
3. ~~Should avatars have tools?~~ No. Pure conversation.
4. ~~Live text-voice switching?~~ No. Mode chosen upfront. End and reconnect.
5. ~~Who speaks first?~~ Human always speaks first. No system-generated opening.
6. ~~What if voice connection fails?~~ Fallback to text if meeting hasn't started.
7. ~~Who generates the Avatar Identity?~~ The Brain (Managed Agent) itself. Self-authored. System provides recommended structure, agent decides content.
8. ~~Context size limits?~~ No artificial limits. Text chat: unlimited (prompt caching). Voice: practical ElevenLabs limit (~5-10K chars).

---

*Version 3.0 — Architecture clarity: Brain/Mouth metaphor, self-authorship principle, stateless avatar, no dispatcher dependency. All design decisions finalized with Marat.*
