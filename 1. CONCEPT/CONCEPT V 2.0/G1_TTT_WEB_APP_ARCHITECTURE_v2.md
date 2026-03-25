# Thucydides Trap SIM — Web App Architecture
**Code:** G1 | **Version:** 1.0 | **Date:** 2026-03-25 | **Status:** Conceptual architecture

---

## Purpose

This document defines the overall architecture of the TTT web application: what modules exist, what each one does, how they connect to each other, and the shared infrastructure that ties everything together. It is the single reference for understanding how the platform is structured.

The app serves four types of users simultaneously: participants (27–39 human players), AI participants (up to 10 concurrent autonomous agents), the facilitator team (1–3 people), and a public audience (via shared display screens). All interact with the same underlying data in real time.

---

## Architectural Overview

The platform has three layers plus shared infrastructure.

```
┌──────────────────────────────────────────────────────────────────────┐
│                        USER-FACING LAYER                              │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ PARTICIPANT  │  │ FACILITATOR  │  │   PUBLIC     │              │
│  │ INTERFACE    │  │ DASHBOARD    │  │   DISPLAY    │              │
│  │              │  │              │  │              │              │
│  │ Role-specific│  │ God-view     │  │ Map + news + │              │
│  │ dashboards,  │  │ controls,    │  │ indicators,  │              │
│  │ actions,     │  │ overrides,   │  │ large-screen │              │
│  │ intel, comms │  │ AI manager   │  │ optimized    │              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
│         │                 │                 │                        │
│  ┌──────┴─────────────────┴─────────────────┴───────┐              │
│  │            SCENARIO CONFIGURATOR                   │              │
│  │  Template library, scenario builder, AI updater   │              │
│  └──────────────────────┬────────────────────────────┘              │
└─────────────────────────┼────────────────────────────────────────────┘
                          │
┌─────────────────────────┼────────────────────────────────────────────┐
│                    CORE SIMULATION LAYER                               │
│                          │                                            │
│  ┌──────────────┐  ┌────┴─────────┐  ┌──────────────┐              │
│  │ TRANSACTION  │  │ LIVE ACTION  │  │ WORLD MODEL  │              │
│  │ (MARKET)     │  │ ENGINE       │  │ ENGINE       │              │
│  │ ENGINE       │  │              │  │              │              │
│  │              │  │ Unilateral   │  │ Batch        │              │
│  │ Bilateral    │  │ actions,     │  │ processing,  │              │
│  │ transfers,   │  │ dice,        │  │ AI-assisted  │              │
│  │ real-time    │  │ real-time    │  │ calculations │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ COMMUNICATION│  │ AI PARTICIPANT│  │ AI ASSISTANT │              │
│  │ SYSTEM       │  │ MODULE       │  │ MODULE       │              │
│  │              │  │              │  │ (Navigator)  │              │
│  │ Messaging,   │  │ Autonomous   │  │              │              │
│  │ meetings,    │  │ AI players,  │  │ Personal     │              │
│  │ channels     │  │ reusable     │  │ mentor,      │              │
│  │              │  │ module       │  │ reusable     │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└──────────────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────┼────────────────────────────────────────────┐
│                    PLATFORM LAYER                                      │
│                          │                                            │
│  ┌──────────────┐  ┌────┴─────────┐  ┌──────────────┐              │
│  │ AUTH &       │  │ DATABASE     │  │ REAL-TIME    │              │
│  │ IDENTITY     │  │              │  │ LAYER        │              │
│  │              │  │ Supabase     │  │              │              │
│  │ Registration,│  │ PostgreSQL,  │  │ WebSocket    │              │
│  │ GDPR,        │  │ single       │  │ subscriptions│              │
│  │ consents     │  │ source of    │  │ for all live │              │
│  │              │  │ truth        │  │ updates      │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐                                │
│  │ RECORDING &  │  │ FILE &       │                                │
│  │ TRANSCRIPTS  │  │ MEDIA        │                                │
│  │              │  │ STORAGE      │                                │
│  │ Session      │  │              │                                │
│  │ capture,     │  │ Briefs,      │                                │
│  │ export,      │  │ maps,        │                                │
│  │ analytics    │  │ audio,       │                                │
│  │              │  │ transcripts  │                                │
│  └──────────────┘  └──────────────┘                                │
└──────────────────────────────────────────────────────────────────────┘
```

**Why three layers?** Dependencies flow downward. The platform layer has no knowledge of the SIM — it provides generic services (database, auth, real-time transport, storage). The core simulation layer knows TTT's rules and mechanics but not how things are displayed. The user-facing layer presents everything to the right audience in the right format. This separation means platform components are reusable across future SIMs, core engines can be tested independently of UI, and interfaces can evolve without touching game logic.

---

## Platform Layer

### 1. Auth & Identity

Handles everything about who the user is and what they're allowed to do.

**Registration and login.** Email-based registration. Facilitators create accounts via invitation. Participants can be pre-registered (facilitator uploads a roster) or self-register with an invitation code. Support for returning users across multiple SIM runs.

**Role assignment.** Once registered for a specific SIM run, the facilitator assigns each participant to a role. The assignment links the user to a specific country, character, and permission set. From that point, the app shows only what that role is authorized to see and do.

**Permission model.** Row-level security (RLS) enforced at the database level — not just in the UI. A participant cannot access another country's private data even if they manipulate the client. Permissions map directly to the role architecture defined in B2: each role has specific action rights, information access, and authorization chains. The facilitator has unrestricted read access and configurable write access.

**GDPR and consents.** Consent collection at registration: data processing, voice recording, transcript storage, analytics use. Consent is granular — a participant can consent to text recording but decline voice. All personal data (names, emails) stored separately from SIM data (which uses character names). Export and deletion on request. Retention policy configurable per organization.

**Session management.** A single user may participate in multiple SIM runs over time. Each run is a separate session with its own role assignment, data, and transcripts. Cross-session analytics (for organizations running repeated SIMs) require explicit opt-in.

### 2. Database

One Supabase PostgreSQL database for the entire platform. All modules read from and write to the same database. This is the single source of truth.

**Why one database?** TTT is a real-time multiplayer system where every action in one domain affects others. If the Transaction Engine records a coin transfer, the Participant Interface must show the updated balance immediately, the Facilitator Dashboard must reflect it, and the AI Participant Module must perceive it. Splitting into multiple databases creates synchronization problems that a single-source-of-truth approach avoids entirely.

**Key schema areas:**

**World state** — the complete state of the simulated world, versioned by round. Every indicator at every level (world, country, individual) as defined in E1's output structure. Previous rounds preserved for rollback and history display.

**Events log** — every action, transaction, combat outcome, covert op result, communication, meeting, vote, and system event. Timestamped, attributed, typed. This is the authoritative record of everything that happened. Used by: engines (for processing), AI modules (for perception), facilitator (for monitoring), recording system (for export), Navigator (for event memory).

**User and session data** — registration, role assignments, consent records, session membership. Linked to world state through role-to-country mappings.

**AI cognitive state** — the 4-block cognitive model for each AI participant (as defined in F1), with full version history. AI decision logs with reasoning chains. Conversation transcripts for AI-to-AI and AI-to-human interactions.

**Navigator data** — per-participant conversation transcripts across all three phases (intro/mid/outro). Structured data extracted from outro conversations. Intro completion flags (goals_covered, rules_covered, strategy_covered).

**Communication records** — all messages, meeting logs, channel histories. Both human and AI communications stored in the same format.

**Scenario configuration** — template definitions, scenario parameter sets, run configurations. Seed data (starting world state) stored as a complete world state snapshot that becomes Round 0.

**Supabase-specific capabilities used:**

Row-Level Security (RLS) — enforces information asymmetry at the database level. A participant querying country data receives only what their role is authorized to see. This is critical for TTT where incomplete information is a core mechanic.

Realtime subscriptions — the foundation of the real-time layer (see below). Tables with frequent updates (events, world state, messages) have Realtime enabled, allowing all connected clients to receive changes instantly.

Edge Functions — serverless functions for operations that need server-side execution: engine processing, AI API calls, voice session management, structured data extraction.

Storage — for file assets: map images, role briefs, audio recordings, exported reports.

### 3. Real-Time Layer

The infrastructure that makes the SIM feel live. Every connected client — participant interfaces, facilitator dashboard, public display, AI participant modules — receives updates the moment something changes.

**Why this matters.** TTT runs two engines simultaneously during Phase A (Transaction Engine and Live Action Engine), with up to 40 concurrent users plus 10 AI agents, all interacting with the same world state. When an attack happens, the map must update for everyone. When a trade completes, both parties' balances must change. When a missile launches, a global alert must appear on every screen. Without a proper real-time layer, participants see stale data and lose trust in the system.

**KING lesson.** KING SIM used Supabase Realtime subscriptions and a BroadcastChannel-based EventDispatcher for cross-component communication. This worked but was never designed as a coherent layer — it was added incrementally, causing issues: missed updates when clients reconnected, race conditions between UI updates and database writes, inconsistent event ordering across clients. TTT designs this layer from the start.

**Architecture:**

Supabase Realtime as the transport. PostgreSQL changes (inserts, updates) on subscribed tables automatically push to all connected clients via WebSocket. This handles the heavy lifting: world state changes, event log entries, message delivery, AI status updates.

Event channels for coordination. Beyond database changes, certain events need broadcast without a database write: round timer ticks, facilitator announcements, temporary UI states (someone is typing, a vote session is active). These use Supabase Broadcast channels — lightweight pub/sub over the same WebSocket connection.

Client-side event processing. Each client type (participant, facilitator, public display, AI module) subscribes to different channels and filters events by relevance. A participant's client subscribes to: their country's data, public world state, messages addressed to them, global alerts. The facilitator subscribes to everything. The public display subscribes to public world state and global events only.

**Reconnection and consistency.** If a client disconnects and reconnects, it must catch up on missed events. The events log in the database is the authoritative source — on reconnection, the client queries for events since its last known timestamp and replays them. This prevents the "I missed the attack" problem that plagued KING.

**Latency targets.** Action results (combat, transactions) should appear on all relevant clients within 2 seconds of the database write. Message delivery within 1 second. World state updates (between rounds) can take 5–10 seconds to propagate fully (larger payload).

### 4. Recording & Transcripts

Captures everything for post-SIM analysis and export.

**What is recorded:**

All events from the events log (already in the database — recording is inherent). All communication transcripts (messages, meetings, voice conversations — text versions). AI participant decision logs with reasoning. Navigator conversation transcripts with structured data extractions. World state snapshots at each round boundary. Facilitator actions and overrides.

**Voice recording.** Voice conversations (AI participant meetings, Navigator sessions) are captured as audio files (stored in Supabase Storage) and as text transcripts (speech-to-text, stored in the database). The text transcript is the primary record; audio is supplementary.

**Export formats.** Full session export as structured data (JSON or CSV) for research and analytics. Narrative export (formatted report of what happened, generated by AI from the events log). Individual participant reports (combining Navigator data, actions taken, outcomes achieved). All exports respect GDPR consent — only data the participant consented to share is included.

**Retention.** Configurable per organization. Default: full data retained for 12 months, anonymized after that, deleted after 24 months. Organizations can request longer retention for research purposes.

### 5. File & Media Storage

Supabase Storage for all binary assets. Role briefs (PDF/HTML generated from scenario configuration). Map images and theater zoom-ins. Voice recordings. Exported reports. Uploaded scenario templates. Organized by SIM run, with access control matching the permission model.

---

## Core Simulation Layer

### 6. Transaction (Market) Engine

Handles all bilateral resource transfers and agreements during Phase A. Both parties must confirm. Pure data operations — no calculation, no AI, no dice. Executes immediately on confirmation.

**Processes:** Coin transfers, arms transfers (with 1-round reduced effectiveness), technology transfers (replicable — sender keeps), basing rights, treaties/agreements (stored, not enforced), organization creation, asset seizure.

**Key behaviors:** Authorization chain enforcement (e.g., arms transfer needs head of state + defense minister). Sufficient balance validation. Irreversible execution (reverse requires a new voluntary transaction). Full logging with timestamp, parties, and terms.

**Interface to participants:** Participants initiate transactions through the Participant Interface (propose a deal → counterparty receives notification → confirms or rejects). The engine validates, executes, and writes to the database. Realtime subscriptions push the result to both parties' interfaces.

**Defined in detail:** E1_TTT_ENGINE_ARCHITECTURE_v2.md, System 1.

### 7. Live Action Engine

Handles all unilateral actions requiring calculation during Phase A. One party decides (with internal authorization chain), the engine resolves the outcome using dice mechanics and modifiers.

**Processes:** Combat (ground/naval/air attacks, blockades, missile/drone strikes, nuclear test, nuclear strike), covert operations (espionage, sabotage, cyber attack, disinformation), domestic actions (arrest, fire/reassign, propaganda, assassination attempt, coup attempt), other (call organization meeting, territorial claim).

**Resolution mechanic:** Universal across all action types. AI calculates probability → key factors displayed to the initiating participant → visual dice/fortune wheel → result with narrative. Immediate primary effects applied to the database (map changes, unit losses, role status changes). Secondary effects deferred to World Model Engine batch processing.

**Authorization enforcement:** Combat needs head of state + military chief. Nuclear strike needs head of state + defense minister + one additional authority. Covert ops need intelligence chief or head of state. The engine checks authorization chain before executing — if co-authorization is missing, the action queues and the co-authorizer receives a notification.

**Moderator controls:** The facilitator can pause any action type, adjust dice modifiers on the fly, delay covert op results (configurable per operation), or override an outcome before it's published.

**Defined in detail:** E1_TTT_ENGINE_ARCHITECTURE_v2.md, System 2.

### 8. World Model Engine

The core calculation engine. Runs between rounds (Phase B). Reads the complete world state from the database (including everything that happened during Phase A), processes all cumulative effects, and writes the new world state back.

**8-step processing sequence:** (1) Validate & lock inputs, (2) Economic state update (AI-assisted), (3) Political state update (AI-assisted), (4) Revenue & military production (pure calculation), (5) Technology advancement (AI-assisted), (6) Narrative generation (AI-generated), (7) Moderator review & approval, (8) Publish to database.

**AI-assisted steps** use LLM reasoning for second-order effects (market confidence, qualitative political factors, tech breakthrough impact) bounded by deterministic base formulas. The moderator reviews and can adjust any calculated value before publication.

**Output structure:** Three levels — World state (global indicators, structural clocks, risk flags), Country state (economic, military, political, technology, diplomatic indicators per country), Individual state (personal balances, role status, covert op results).

**Forecasting reuse.** The same engine can be run after the final round to project "what would happen next" — showing participants the long-term trajectory of their decisions. This is a powerful debrief tool.

**Defined in detail:** E1_TTT_ENGINE_ARCHITECTURE_v2.md, System 3 + Processing Sequence.

### 9. Communication System

The infrastructure for all human-to-human, human-to-AI, and AI-to-AI communication during the SIM.

**Channel types:**

**Direct messages** — private 1-on-1 text messages between any two participants. Delivered instantly via the real-time layer. Stored in the database as communication records. Both human-to-human and human-to-AI use the same channel.

**Meeting rooms** — virtual rooms for bilateral or multilateral conversations. A participant requests a meeting, invitees accept or decline. Once in a meeting: voice mode (via the web app's voice interface) or text mode. Meetings have a transcript that is automatically captured and stored. Organization meetings (NATO, BRICS+, etc.) use the same room mechanic with pre-defined member lists.

**Country channels** — internal team communication for multi-role countries. Columbia's 7–9 players have a private team channel. Cathay's 5. These mirror the "behind closed doors" dynamic — Cathay's channel is opaque to outsiders.

**Public broadcast** — moderator announcements, press publications, world update delivery. Read-only for participants. Displayed on the public display as well.

**AI integration:** AI participants send and receive messages through the same channels as humans. The Communication System doesn't distinguish between human and AI senders — it's the Module Interface Protocol (defined in F1) that routes messages between the system and the AI participant's cognitive core. Navigator conversations use a separate, private channel per participant — visible only to that participant and the facilitator.

**Opacity enforcement.** Cathay's internal communications are marked as opaque — the facilitator can see them, but other participants cannot, even through the system. If a Cathay member leaks information, they do it manually (send a message to an outsider). The system enforces the "visible facade / hidden internal" dynamic architecturally.

### 10. AI Participant Module

Defined in F1_TTT_AI_PARTICIPANT_MODULE_v2.md. A standalone, reusable module that enables AI characters to participate autonomously alongside human players.

**Connection to the web app:** Through the Module Interface Protocol — the standardized API of 7 message types (4 inbound, 3 outbound). The web app sends world state updates, event notifications, action menus, and incoming conversations. The module sends action submissions, outbound communications, and status updates.

**What the web app provides to this module:** Access to the same world state a human player would see (respecting information asymmetry via RLS). The same action submission endpoints (budget, transactions, combat, etc.). Communication channels (direct messages, meeting rooms). Database storage for cognitive state and decision logs.

**What the web app does NOT provide:** The module handles its own reasoning, conversation management, voice synthesis, and decision-making internally. The web app treats the AI participant as another client — it doesn't know or care whether the submissions come from a human clicking buttons or an AI agent.

**Scaling consideration:** Up to 10 AI participants active simultaneously. Each runs its own autonomous action loop (30–90 second cycles). API calls to LLM providers go through Edge Functions with rate limiting and cost tracking. Staggered loop intervals prevent all 10 from hitting the API at the same instant.

### 11. AI Assistant Module (Navigator)

Defined in F2_TTT_AI_ASSISTANT_MODULE_v2.md. A personal AI mentor available to every human participant across three SIM phases (intro, mid, outro).

**Connection to the web app:** Through its own Module Interface Protocol. The web app provides: role assignment data, SIM rules and mechanics, current world state, event log (for event memory), and conversation storage. Navigator provides: conversation transcripts, intro completion flags, structured data extractions from outro conversations.

**Participant access:** A "Talk to Navigator" button on the Participant Interface. Opens a voice session (primary) or text chat (fallback). Available during check-in (intro), during Phase A of each round (mid), and during the debrief period (outro).

**Facilitator visibility:** The Facilitator Dashboard shows Navigator status for all participants: intro completion tracking, mid-session activity, outro completion, conversation duration, extracted data status.

---

## User-Facing Layer

### 12. Scenario Configurator

The pre-SIM tool where facilitators prepare scenarios and configure runs.

**Template management.** A template is a complete scenario definition at the SEED level: world state, role definitions, starting parameters, scheduled events, all values from Block A (Seed Design) of the parameter structure (D0). Templates are versioned and stored in the database. The initial template is created from the TTT seed data; subsequent templates can branch from it.

**AI-assisted context refresh.** This is the feature that keeps TTT contemporary. A facilitator opens a template and asks the AI assistant: "Update this scenario to reflect the current geopolitical situation." The AI reviews the template's starting conditions against current world events (using web search or a curated news feed) and proposes specific changes: GDP adjustments, new sanctions, shifted alliance positions, updated military deployments, new crisis points.

The facilitator reviews each proposed change and approves or rejects individually. The AI explains its reasoning for each change: "I'm suggesting raising Cathay's GDP growth from 4.2% to 3.8% because Q3 2026 data shows continued deflation pressure and property sector weakness." This is a conversation, not automated rewriting — the facilitator stays in control.

Implementation can use Claude Code or an in-app conversational interface — either way, the mechanic is: AI proposes changes with reasoning → facilitator approves/rejects → approved changes applied to a new template version. The in-app approach is more accessible for non-technical facilitators; Claude Code is more powerful for deep structural changes.

**Scenario creation (from template to run).** Once a template is selected, the facilitator creates a SIM run by configuring Block B (Scenario Configuration) and Block C (SIM-Run Preset) parameters from D0: number of participants, round count, format (one-day/two-day), which expansion roles are active, specific parameter adjustments (starting coins, AI aggressiveness, engine sensitivity). The configurator validates that the configuration is internally consistent (enough roles assigned, budget totals balanced, all required parameters set).

**Role assignment.** The facilitator assigns registered participants to roles. Drag-and-drop from a participant roster to a role map. Unassigned solo country roles default to AI. The system generates role briefs automatically from the template + configuration.

**Brief generation.** Once configuration is complete, the system generates: public world briefing (D1 — the same for everyone), private role briefs (D4 — customized per role, containing classified information, personal motivations, secret timelines), and AI country initial postures (D5 — loaded into AI participant Block 2/3/4 initialization).

### 13. Participant Interface

The primary interface for human players during the SIM. Mobile-friendly. Role-specific.

**Design principles.** The interface must handle a wide range of complexity: a Columbia President manages budget, military, diplomacy, elections, intelligence, and internal politics. A solo country operator manages a simpler set. The interface should show each participant only what is relevant to their role — not overwhelm them with mechanics they don't use.

**Core screens:**

**Role home.** Who you are, your team, your powers, your current situation at a glance. Always accessible. This is the participant's anchor in a complex simulation.

**World view.** The global map (as defined in C4) with current state: active theaters, military deployments visible to this role, chokepoint status, organization memberships. Country-level indicators for all countries (public data). World-level indicators (oil price, trade volume, structural clocks). This is what's on the public display, but with additional intelligence that this role has access to.

**Country dashboard.** Your country's detailed situation: economic indicators (GDP, inflation, reserves, revenue, budget execution), military (unit counts by type, deployments, production status), political (stability index, political support, threshold warnings), technology (tech levels, R&D progress). For multi-role countries, each team member sees the same country data but different action options based on their role.

**Actions panel.** All available actions for this role, organized by type: budget/policy submissions (with deadline countdown), real-time transactions (propose, review, confirm), real-time actions (combat, covert ops, domestic — with authorization chain status showing who needs to approve), deployments (during Phase C window). Each action has clear requirements, costs, and expected effects. Authorization chains are visible: "Attack requires your approval + Shield's approval — Shield has not yet confirmed."

**Communications.** Inbox for direct messages. Meeting room access. Country team channel. Public announcements feed. Clear indication of unread messages. "Talk to Navigator" button. Meeting request/accept flow.

**Intelligence.** Role-specific information that others don't see. Covert operation results (for intelligence chiefs). Economic data that only the finance authority has. Military intelligence (for military chiefs). This is where information asymmetry becomes tangible — different roles literally see different screens.

**Notifications.** Real-time alerts for: incoming messages, meeting invitations, action results, vote sessions, authorization requests, deadline warnings, world events. Non-intrusive but impossible to miss. Configurable priority — a nuclear launch alert overrides everything.

**Mobile optimization.** The participant interface must work on phones and tablets. During a SIM, participants move around the room for meetings — they carry the interface with them. The action submission flow must work one-handed. Maps must be pinch-zoomable. Messages must be readable and sendable on a small screen. This is non-negotiable for TTT's physical format where participants walk between meeting spaces.

### 14. Facilitator Dashboard

The command center for the moderator team. Full visibility, full control.

**God-view.** Everything, everywhere, all at once. The complete world map with all military deployments (not just what each country sees — the actual full picture). All country indicators. All active transactions and actions in progress. All communication channels (ability to read any message, enter any meeting). The facilitator sees the simulation as it truly is, not through any country's lens.

**Round management.** Timer controls (start, pause, extend, end round). Phase transitions (Phase A → submit deadline → Phase B processing → Phase C deployment → next round). The moderator controls the rhythm of the game.

**Engine controls.** Trigger World Model Engine processing. Review AI-generated calculations before publication. Adjust any calculated value (GDP, stability, tech progress). Modify narrative text. Approve or reject the output package. Override dice results before they publish (for Live Action Engine).

**AI participant manager.** Status of all AI participants: current activity, queue depth, recent decisions. Ability to: pause/resume any AI, adjust activity frequency, view cognitive state (all 4 blocks), see reasoning for any decision, override a pending AI action, trigger manual reflection (inject information into the AI's perception). This is essential for a facilitator who needs to ensure AI participants behave appropriately and don't derail the game.

**Event injection.** The moderator can create events that appear in the simulation: "Breaking: Nordostan general defects to Heartland" or "Earthquake damages Cathay's southern industrial zone." These become entries in the events log, are pushed to all relevant clients, and feed into the next World Model Engine processing. This is how the moderator shapes the narrative beyond what participants and engines produce.

**Navigator oversight.** Aggregated view of all Navigator conversations: intro completion status per participant, mid-session activity, outro completion. Ability to view any transcript. Ability to add events to Navigator's event memory feed. This is the facilitator's window into participant engagement quality.

**Alert system.** Automatic flags for situations requiring attention: stability dropping below threshold (crisis imminent), military escalation (new theater about to activate), budget not submitted (deadline approaching), AI participant error (API failure, stuck in loop), nuclear launch initiated (the facilitator probably wants to watch this one closely).

### 15. Public Display

A read-only view designed for large screens visible to all participants and observers. The public display shows what a general audience would see — the "CNN broadcast" of the simulation.

**Content elements:**

**Global map.** The two-layer map from C4, showing: active theaters with current control, naval positions in maritime zones, chokepoint status (open/contested/blocked), military movements that are publicly visible (not covert). Updated in real time via the real-time layer.

**Key indicators dashboard.** A panel of global metrics: global oil price, trade volume index, power balance indicators (aggregate military/economic comparisons without giving conclusions), structural clock positions (Formosa capability, Columbia election countdown, Nordostan reserves, Persia nuclear progress), active conflict count.

**News feed.** A scrolling ticker of public events: treaty signings, public speeches, combat outcomes (publicly visible ones), election results, organization meeting outcomes, moderator-injected events, press publications (if the Veritas press role is active). Each item is timestamped and attributed.

**Current and upcoming events.** "NOW: UN Security Council in session" or "NEXT: OPEC+ meeting in 15 minutes." Shows scheduled events from the round timeline.

**Round clock.** Current round number, scenario date (e.g., "H1 2028"), time remaining in the current phase, phase indicator (Negotiation / Submission deadline / World update / Deployment).

**Display modes.** The public display can be configured for different physical setups: single screen (all elements on one display, rotating between map and dashboards), multi-screen (map on one screen, indicators on another, news on a third), or focus mode (facilitator selects what to highlight — e.g., zoom into the Pacific theater during a Taiwan crisis). The facilitator controls the display mode from the dashboard.

**Design principles.** Large fonts, high contrast, readable from 5 meters. No participant-specific data. No classified information. Minimal text — visual indicators where possible. The display should tell a story that observers can follow without understanding every mechanic.

---

## Cross-Cutting Concerns

### Data Flow: Key Scenarios

To illustrate how the modules work together, here are three representative scenarios:

**Scenario A: A ground attack during Phase A.**

1. Columbia's Dealer (participant) opens Actions panel → selects "Attack" → chooses target zone → submits
2. Participant Interface sends authorization request to Shield (defense minister) via the Communication System
3. Shield receives notification, opens pending authorization, approves
4. Participant Interface submits the authorized action to the Live Action Engine
5. Live Action Engine calculates: dice probability from unit matchups, morale modifier (from stability), tech modifier, terrain. Displays factors. Rolls dice. Resolves casualties and territory changes
6. Live Action Engine writes results to database: events log (attack event + result), world state (territory control change, unit losses)
7. Real-time layer pushes: map update to ALL connected clients (new territory control visible), casualty notification to both attacker and defender, alert to all participants ("Combat in Eastern European theater"), event to AI Participant Modules (perception input for affected AI countries)
8. Public Display updates: map redraws, news ticker shows "Columbia forces engage Nordostan positions in southern sector"
9. Facilitator Dashboard highlights the event; moderator can annotate
10. AI participants in affected countries trigger immediate reflection cycle (Block 3/4 update), may initiate reactive actions (messages to allies, counter-deployment planning)
11. Secondary effects (GDP damage, stability impact) deferred to World Model Engine processing in Phase B

**Scenario B: World update between rounds (Phase B).**

1. Facilitator triggers "End round" from dashboard. Submission deadline fires.
2. All pending routine submissions (budgets, tariffs, sanctions, OPEC+ production) are locked in the database. Missing submissions default to previous round's values.
3. World Model Engine begins 8-step processing. Reads all data from the database: previous world state, all transactions from Transaction Engine, all action results from Live Action Engine, all submitted settings.
4. Steps 2–5 execute sequentially: economic update (AI-assisted), political update (AI-assisted), revenue & production (deterministic), tech advancement (AI-assisted). Each step writes intermediate results.
5. Step 6: AI generates narratives (world-level, country-level briefings, structural clock updates, risk flags).
6. Step 7: Complete output package presented to facilitator on the dashboard. Facilitator reviews calculated values, adjusts if needed (e.g., "This GDP drop seems too steep, adjust from -8% to -5%"), approves narratives, signs off.
7. Step 8: Approved world state written to database as "Round N+1 initial state."
8. Real-time layer pushes new world state to all clients. Participant Interfaces refresh with updated dashboards. Public Display updates all indicators. AI Participant Modules receive World State Update via the Module Interface Protocol, triggering a full perception-reflection cycle.
9. Phase C begins: 5-minute deployment window. Participants with military authority deploy newly available units via the Actions panel. Deployments write to database and push to map in real time.
10. Next round starts.

**Scenario C: A participant talks to Navigator during Phase A.**

1. Participant clicks "Talk to Navigator" on their interface
2. Participant Interface sends a session request to the AI Assistant Module
3. Navigator's Prompt Assembler builds context from 7 blocks: identity, SIM knowledge (from adapter), person context (role, country, team), conversation history (all previous Navigator sessions with this participant), event memory (recent SIM events), phase-specific assignment (MID mode — advisory), greeting logic
4. Voice Engine establishes a voice session via ElevenLabs Conversational AI. The assembled prompt is loaded as the agent's context
5. Participant speaks: "I'm confused about what sanctions I should set against Nordostan"
6. Navigator responds in voice: clear explanation of how sanctions work, what levels mean, what the cost-to-self is, questions about what the participant is trying to achieve
7. Full transcript captured (speech-to-text for participant, direct text for Navigator responses), stored in the database
8. Session ends. If Navigator detects any commitments or intentions ("I think I'll set sanctions to level 2"), it logs this as a contextual note for future reference
9. Facilitator Dashboard shows: this participant is active with Navigator, session duration, running count of mid-session conversations

### Information Asymmetry

A fundamental architectural concern. TTT is a game of incomplete information — participants must NOT see data they shouldn't have. This is enforced at multiple levels:

**Database level.** RLS policies on all tables containing country-specific or role-specific data. A query from a participant's client returns only rows their role is authorized to see.

**API level.** Edge Functions that serve data to clients filter responses based on the authenticated user's role. Even if someone bypasses the client, the server never returns unauthorized data.

**Client level.** The Participant Interface renders only data received from the API. No "hidden" data in the DOM that could be inspected. The interface for a Cathay Circuit (tech chief) looks fundamentally different from a Columbia Shadow (CIA director) — different actions, different intelligence, different dashboards.

**AI level.** AI participants receive world state updates through the SIM Adapter, which respects the same RLS rules. An AI playing Wellspring (Saudi Arabia) doesn't know Cathay's internal stability index unless that information is public or was obtained through intelligence actions.

### Offline Resilience

During a live SIM, internet connectivity is critical but not always reliable. Key mitigations:

**Optimistic UI.** Action submissions show "pending" immediately on the client, then confirm or revert when the server responds. Participants don't stare at a spinner.

**Local state cache.** Each client maintains a local copy of the world state it has received. If the WebSocket connection drops, the client continues displaying the last known state (with a "reconnecting" indicator) rather than going blank.

**Reconnection sync.** On reconnection, the client queries the events log for any events missed during the outage and replays them. No manual refresh needed.

**Engine independence.** The three engines run server-side. A participant's client going offline doesn't affect engine processing. The world continues to turn.

### Performance and Scaling

**Concurrent users.** Peak load: ~50 simultaneous connections (40 humans + 10 AI agents). This is modest by web standards but demanding in real-time update throughput — each action can trigger updates to 50 clients.

**AI API throughput.** 10 AI participants × action loop (every 30–90 seconds) × reflection calls + conversation calls = potentially 200+ LLM API calls per round during active play. Rate limiting, request queuing, staggered loop intervals, and context caching (proven in KING to reduce costs ~90% for multi-turn conversations) manage this.

**World Model Engine processing.** Phase B (between rounds) involves multiple sequential LLM calls for AI-assisted steps plus deterministic calculations. Target: complete processing in under 5 minutes. The facilitator review step adds human time on top.

---

## Technology Stack (Concept-Level)

This section captures technology choices at the concept level. All are proven in KING SIM and appropriate for TTT's requirements.

**Frontend:** React (Next.js) — SPA with real-time state management via Zustand. Responsive design for desktop and mobile. Map rendering via a 2D library (Leaflet, Mapbox, or custom SVG — to be determined based on map design requirements from C4).

**Backend:** Supabase — PostgreSQL database, Auth, Realtime, Edge Functions, Storage. The entire platform runs on Supabase services, minimizing custom infrastructure.

**AI/LLM:** Provider-agnostic abstraction layer (proven in KING). Gemini and Anthropic Claude as primary providers, selectable per task type and switchable at runtime. Context caching where supported.

**Voice:** ElevenLabs Conversational AI — for AI participant voice interactions and Navigator voice sessions. Per-character voice profiles.

**Deployment:** Vercel for the frontend. Supabase Cloud for the backend. Both are managed services — no infrastructure to maintain.

---

## Module Dependencies

A summary of which modules depend on which:

| Module | Depends on | Depended on by |
|--------|-----------|----------------|
| Auth & Identity | Database | All user-facing modules, all engines |
| Database | — (foundation) | Everything |
| Real-Time Layer | Database (Realtime) | All user-facing modules, Communication, AI modules |
| Recording & Transcripts | Database, Storage | Analytics (post-SIM) |
| Transaction Engine | Database, Auth | Participant Interface, AI Participant Module |
| Live Action Engine | Database, Auth | Participant Interface, AI Participant Module, Facilitator Dashboard |
| World Model Engine | Database, AI/LLM providers | Facilitator Dashboard (trigger + review) |
| Communication System | Database, Real-Time Layer | Participant Interface, AI modules, Facilitator Dashboard |
| AI Participant Module | Database, Communication, Real-Time Layer, AI/LLM providers, Voice | Operates autonomously; submits through Transaction + Live Action engines |
| AI Assistant (Navigator) | Database, Communication, Real-Time Layer, AI/LLM providers, Voice | Participant Interface (access point), Facilitator Dashboard (oversight) |
| Scenario Configurator | Database, AI/LLM providers (for context refresh) | Creates the data all other modules consume |
| Participant Interface | Auth, Database, Real-Time Layer, Communication, all engines (for action submission) | — (end user) |
| Facilitator Dashboard | Auth, Database, Real-Time Layer, all engines, AI modules, Communication | Controls World Model Engine, AI modules, round flow |
| Public Display | Database, Real-Time Layer | — (read-only end display) |

---

## Relationship to Existing Concept Documents

| This document's module | Detailed in |
|------------------------|-------------|
| Transaction Engine, Live Action Engine, World Model Engine | E1_TTT_ENGINE_ARCHITECTURE_v2.md |
| AI Participant Module | F1_TTT_AI_PARTICIPANT_MODULE_v2.md |
| AI Assistant (Navigator) | F2_TTT_AI_ASSISTANT_MODULE_v2.md |
| Participant actions, authorization chains | C2_TTT_ACTION_SYSTEM_v2.md |
| Role permissions, team structures | B2_TTT_ROLES_ARCHITECTURE_v2.md |
| Map and theater system | C4_TTT_MAP_CONCEPT_v2.md |
| Round structure, phase timing | C3_TTT_TIME_STRUCTURE_v2.md |
| Game domains, mechanics | C1_TTT_DOMAINS_ARCHITECTURE_v2.md |
| Parameter structure (Seed/Config/Preset) | D0_TTT_PARAMETER_STRUCTURE_v2.md |

---

## KING SIM Inheritance

| Component | KING (proven) | TTT (designed from start) |
|-----------|--------------|--------------------------|
| Database | Supabase PostgreSQL with RLS | Same. Extended schema for multi-engine world state, information asymmetry enforcement |
| Real-time updates | Supabase Realtime + BroadcastChannel EventDispatcher, added incrementally | Same transport, designed as a coherent layer from inception with reconnection sync |
| Auth | Supabase Auth, basic role-based | Extended: GDPR consent management, granular permissions per role, cross-session identity |
| State management | Zustand stores, real-time subscriptions | Same pattern, more stores (participant state, world state, communication state) |
| AI integration | Tightly coupled to KING app | Modular: AI Participant and Navigator connect through standardized protocols |
| Facilitator tools | Basic dashboard with phase controls | Full command center: engine controls, AI manager, event injection, Navigator oversight |
| Participant interface | Role-specific pages with action menus | Extended: mobile-first, real-time map, intelligence view, authorization chain UI |
| Public display | Simple leaderboard + map | Full broadcast experience: map, indicators, news, events, multi-screen support |
| Scenario management | Manual seed file loading | Full configurator: template library, AI-assisted context refresh, automated brief generation |
| Communication | Basic chat, Telegram integration | Integrated system: DMs, meeting rooms, team channels, public broadcast, AI-routed |
| Recording | Basic event logs + conversation transcripts | Comprehensive: all events, all transcripts, structured data extraction, export pipeline |

---

## Scope Boundaries

**This document IS:** The architectural blueprint for the entire TTT web platform — what modules exist, what they do, how they connect, and what infrastructure they share.

**This document is NOT:** Implementation specifications for individual modules (those live in their own documents: E1, F1, F2, and future detailed specs). Database schema design (a separate technical document for development). UI/UX wireframes or visual design. API endpoint specifications.

---

## Open Questions for Detailed Design

1. **Map rendering technology** — Leaflet, Mapbox, or custom SVG? Depends on C4's final map design requirements and whether we need interactive unit placement or just display.
2. **Communication system implementation** — Build custom on Supabase Realtime, or integrate a third-party chat SDK? KING used Telegram as an external channel; TTT should have in-app communication but may still support Telegram as a secondary channel for overnight (two-day format).
3. **Scenario Configurator AI interface** — In-app conversational UI vs. Claude Code session? The in-app approach is more accessible; Claude Code is more powerful. May offer both.
4. **Public display technology** — Standard web page on a large screen, or a dedicated display application? Web page is simpler; dedicated app could offer better full-screen controls and multi-screen coordination.
5. **Offline mode depth** — How much functionality should work offline beyond displaying cached state? Can participants draft actions offline that submit on reconnection?
6. **Voice infrastructure** — How many concurrent voice sessions can ElevenLabs support? 10 AI participant voice terminals + Navigator sessions for 40 participants could spike to 15+ simultaneous sessions.

---

## Changelog

- **v1.0 (2026-03-25):** Initial concept. Three-layer architecture (Platform / Core Simulation / User-Facing) with 15 modules. Shared infrastructure: Supabase database, real-time layer, auth, recording. Core: three engines (from E1), communication system, AI Participant Module (from F1), AI Assistant Navigator (from F2). User-facing: Scenario Configurator with AI-assisted context refresh, Participant Interface (mobile-first), Facilitator Dashboard (god-view command center), Public Display (large-screen broadcast). KING inheritance analysis. Data flow scenarios. Module dependency map.
