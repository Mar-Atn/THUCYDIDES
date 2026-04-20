# Thucydides Trap -- Living Architecture Document

**Version:** 1.0 | **Date:** 2026-04-21 | **Status:** ACTIVE
**This is the single source of truth for the project's architecture.**
**Owner:** Marat Atn (marat@metagames.org)

---

## Part 1: Vision & Concept

### 1.1 What We Are Building

The Thucydides Trap (TTT) is an immersive leadership simulation with 25-39 human participants, 10+ AI-operated countries, 6-8 rounds, and 4 interconnected domains (military, economy, politics, technology). It is a full-stack web platform with autonomous AI participants -- designed for CEOs, founders, and senior leaders.

The central question is not "will there be war over Taiwan." It is: **what happens to the entire global order when the power that built it can no longer sustain it alone -- and the power rising to challenge it has a fundamentally different vision of how the world should work?**

The simulation uses fictional country names with transparent real-world parallels -- close enough for instant recognition, distant enough for psychological freedom and political safety in corporate settings. 20 countries in total: Columbia (USA), Cathay (China), Sarmatia (Russia), Ruthenia (Ukraine), Persia (Iran), plus 5 European countries (Gallia, Teutonia, Freeland, Ponte, Albion), and 10 solo countries (Bharata, Levantia, Formosa, Phrygia, Yamato, Solaria, Choson, Hanguk, Caribe, Mirage).

### 1.2 Core Tensions

The growing economic, military, and technological power of China is creating structural tension with the United States and its alliance system. This is the Thucydides Trap: a power transition that history tells us ends in war 75% of the time.

What makes THIS transition uniquely dangerous is the personal dimension. China's leader has staked his legacy on "national rejuvenation" -- including the Taiwan question. He is 73, has abolished succession mechanisms, and faces an economic slowdown his system has never experienced. When structural opportunity meets personal desperation, that is when traps spring.

**The 5 Focal Attractors (not scripted -- emergent):**

1. **Formosa Crisis** -- where the structural power shift meets geography, semiconductors, and nuclear risk. The ultimate attractor.
2. **Columbia Presidential Election** -- the structural climax. Every alliance, every deal, every military posture is haunted by the question: what happens after the election?
3. **Ruthenia Resolution** -- peace deal, frozen conflict, or escalation. Tests whether borders can be changed by force.
4. **Financial Architecture Fracture** -- BRICS+ currency union, de-dollarization. The quiet catastrophe that may matter more than any war.
5. **AI Breakthrough Moment** -- whoever reaches frontier AI first gains decisive advantages across ALL domains. The tech race IS the modern arms race.

Which attractor becomes the SIM's climax depends entirely on participant decisions. The number of active crises at game end is itself the scorecard.

### 1.3 The Three-Layer Trap

The simulation is built on the insight that the Thucydides Trap operates at three layers simultaneously:

**Layer 1 -- Structural.** The visible power balance is shifting. China leads in manufacturing, trade volume, and key technologies. The US leads in military power, financial systems, AI research, and alliances. Neither side has a decisive advantage. This ambiguity is itself destabilizing. Visible on the Power Balance Dashboard each round.

**Layer 2 -- Situational.** Five simultaneous crises create a "too many fires" problem. Each is manageable alone. Together, they overwhelm the system's capacity to respond. Attending to one means neglecting another, and the neglected one gets worse.

**Layer 3 -- Personal.** Three aging leaders face the intersection of national interest and personal survival. The Chairman (73, no successor, legacy depends on reunification). The President of the revisionist power (73, no successor, war must produce "victory"). The US President (every decision measured against an election). The structural clock says patience. The personal clock says act now. When they contradict -- that is when traps spring.

The SIM succeeds when participants emerge saying: *"I understood the trap intellectually before. Now I understand why it's so hard to escape -- and I understand it because I felt the pull myself."*

### 1.4 AI Participant Philosophy

> *"An AI participant is a player, not a calculator."*

The AI participants are autonomous, self-authoring agents who sit in the same seat a human would sit in. They see what a human would see -- no more, no less. They reason about strategy, talk to other leaders, make deals, and surprise the designers.

**Core principles:**

- **Trust the AI's reasoning.** Explicit behavioral constraints ("MUST be aggressive") produce rigid characters. Instead, give the AI a rich identity, clear interests, and accurate situational awareness -- then let it reason naturally. Proven in KING SIM testing (March 2026).
- **Same rights, same constraints.** An AI participant has exactly the same action menu, information access, and authorization requirements as a human in the same role.
- **Continuous presence during rounds.** The AI is active throughout Phase A -- monitoring, responding to proposals, initiating conversations, making real-time decisions. It operates on the same timeline as human players.
- **Separate module, clear protocol.** The cognitive core (how the AI thinks) is SIM-agnostic. The SIM adapter (what the AI knows and can do in THIS game) is SIM-specific.

**4-Block Cognitive Model (proven in KING SIM):**

| Block | Content | Update Frequency |
|-------|---------|------------------|
| **Block 1 -- RULES** | Game mechanics, available actions, role-specific powers, behavioral guidelines | Once at game start (cached) |
| **Block 2 -- IDENTITY** | Who the AI IS: personality, values, speaking style, factional alignment | Rarely (only on regime change, trauma) |
| **Block 3 -- MEMORY** | What the AI remembers: relationships, commitments, betrayals, intel obtained, meeting outcomes | After each conversation and decision |
| **Block 4 -- GOALS** | What the AI wants: current objectives, multi-round strategic plans, contingencies | Per round + after major events |

This is not a dogma -- but the most relevant and tested approach. The model has been validated across 8+ KING SIM runs and adapted for TTT's higher complexity (more event types, 5x more events per round, autonomous action loop).

**Perceive -> Think -> Act cycle:**
- **PERCEIVE:** Process incoming events, filter by relevance, route to processing
- **THINK:** Reflect on new information (update blocks), deliberate on what to do next
- **ACT:** Submit structured game actions, initiate conversations, make proposals

The AI balances proactive goal pursuit with reactive responses. In a quiet round, it is mostly proactive. During a crisis, it is mostly reactive.

**Current implementation status:** LeaderAgent class in `app/engine/agents/leader.py` implements the 4-block model with tool-use via Gemini Flash + Claude fallback. 10 context blocks assembled per agent per round. Orchestrator prompts each AI 2 times per round, max 5 free actions total, plus mandatory decisions. Full autonomous polling loop is a remaining gap (see Part 6).

---

## Part 2: System Architecture

### 2.1 Tech Stack

| Layer | Technology | Location |
|-------|-----------|----------|
| **Backend** | Python 3.11+ / FastAPI | `app/engine/` |
| **Frontend** | TypeScript / React 18+ / Vite | `app/frontend/src/` |
| **Database** | Supabase (PostgreSQL 17 + Realtime + Auth + Storage) | Cloud (eu-west-2) |
| **LLM** | Dual provider: Anthropic Claude + Google Gemini | `app/engine/config/settings.py` |
| **Maps** | Custom hex renderer (HTML/JS) | `app/test-interface/` |
| **Supabase Project** | `lukcymegoldprbovglmn` (Pro plan, MetaGames Lab org) | eu-west-2 |

**LLM Configuration:**

| Use Case | Primary | Fallback |
|----------|---------|----------|
| Agent decisions | Claude Sonnet 4 | Gemini 2.5 Flash |
| Agent conversations | Claude Sonnet 4 | Gemini 2.5 Flash |
| Agent reflection | Claude Sonnet 4 | Gemini 2.5 Pro |
| Quick scan | Gemini 2.5 Flash Lite | Claude Haiku 4.5 |
| Narrative | Gemini 2.5 Flash | Claude Haiku 4.5 |
| Moderator (Argus) | Claude Sonnet 4 | Gemini 2.5 Pro |

### 2.2 Directory Structure

```
THUCYDIDES/
├── ARCHITECTURE.md              <- THIS FILE (living truth)
├── CLAUDE.md                    <- Root constitution (project rules)
├── 1. CONCEPT/                  <- FROZEN. Original vision. Read for context.
├── 2 SEED/                      <- FROZEN. Canonical specs. Read for design decisions.
├── 3 DETAILED DESIGN/           <- Reference specs (DET), includes CONTRACTS/ and CARDS/
│   ├── CONTRACTS/               <- 28 locked action specifications
│   └── CARDS/                   <- Action reference cards
├── MODULES/                     <- Execution phase: SPECs, roadmap, registry
│   ├── ROADMAP.md               <- Module sequence, timeline
│   ├── MODULE_REGISTRY.md       <- Live status of all modules
│   ├── COMPREHENSIVE_BUILD_DOCUMENTATION.md <- Detailed build reference
│   ├── AUDIT_*.md               <- 4 audit reports (2026-04-20)
│   └── M*/                      <- Per-module specs and design docs
├── app/                         <- APPLICATION CODE
│   ├── CLAUDE.md                <- Build standards
│   ├── engine/                  <- Python (FastAPI backend)
│   │   ├── CLAUDE.md            <- Engine-specific rules
│   │   ├── main.py              <- All API endpoints (~43 endpoints, 1,935 lines)
│   │   ├── auth/                <- JWT auth + Supabase integration
│   │   ├── config/              <- Settings, map, position-action rules
│   │   ├── engines/             <- Pure stateless domain engines (8,059 lines)
│   │   │   ├── economic.py      <- 2,190 lines: GDP, oil, sanctions, tariffs
│   │   │   ├── military.py      <- 3,086 lines: 5 combat types + covert ops
│   │   │   ├── political.py     <- 830 lines: stability, elections, revolutions
│   │   │   ├── technology.py    <- 357 lines: R&D, nuclear, AI levels
│   │   │   ├── orchestrator.py  <- 656 lines: Phase B round processing
│   │   │   ├── movement.py      <- 254 lines: unit repositioning
│   │   │   └── round_tick.py    <- 686 lines: per-round tick bridge
│   │   ├── agents/              <- AI participant code
│   │   │   ├── leader.py        <- LeaderAgent (4-block cognitive model)
│   │   │   ├── leader_round.py  <- Single-agent round runner (tool-use)
│   │   │   └── full_round_runner.py <- 20-agent parallel runner
│   │   ├── services/            <- Business logic, DB access (54 files)
│   │   │   ├── action_dispatcher.py  <- Routes 33 action types to engines
│   │   │   ├── sim_run_manager.py    <- State machine lifecycle
│   │   │   ├── sim_create.py         <- SimRun creation (11-table copy)
│   │   │   └── *_engine.py, *_validator.py  <- Per-action engines + validators
│   │   ├── context/             <- Context Assembly Service (10 blocks)
│   │   ├── orchestrators/       <- Nuclear chain (4-phase decision chain)
│   │   └── models/              <- Pydantic models (API + DB)
│   ├── frontend/src/            <- React app (13,902 lines total)
│   │   ├── pages/               <- 15 page components
│   │   │   ├── ParticipantDashboard.tsx  <- 7,108 lines (monolith -- see Part 6)
│   │   │   ├── FacilitatorDashboard.tsx  <- 2,160 lines
│   │   │   ├── PublicScreen.tsx          <- 936 lines
│   │   │   └── SimRunWizard.tsx          <- 1,572 lines
│   │   ├── lib/                 <- Supabase client, queries, realtime hooks
│   │   └── contexts/            <- AuthContext
│   ├── test-interface/          <- Hex map renderer (server.py + JS)
│   └── tests/                   <- L1/L2/L3 test suites
├── ARCHIVE/                     <- Session summaries, old designs, superseded docs
├── EVOLVING METHODOLOGY/        <- Knowledge base
└── .claude/agents/              <- 14 agent definitions
```

### 2.3 Data Flow

```
Human/AI submits action
  -> POST /api/sim/{id}/action (main.py)
  -> Validate: sim active? role authorized? phase allows?
  -> Check: needs moderator confirmation? -> queue to pending_actions
  -> If immediate: action_dispatcher.dispatch_action()
    -> _route() -> engine function (pure, no DB)
    -> _apply_combat_losses() -> DB writes (deployments delete/update)
    -> write_event() -> observatory_events INSERT
  -> Supabase Realtime pushes UPDATE to all connected clients

Realtime architecture (write/read split):
  WRITE: React -> FastAPI POST -> Supabase DB -> engine -> DB write
  READ:  Supabase DB change -> Supabase Realtime (WebSocket) -> React client
```

**Round flow:**

```
Phase A (60-80 min): Free gameplay. Actions submitted.
  -> Immediate actions processed instantly (combat, covert, domestic)
  -> Batch decisions queued (budget, sanctions, tariffs, OPEC)
Phase B (5-12 min, automated): Orchestrator runs all engines in sequence
  -> Economic -> Stability -> Political support -> War tiredness
  -> Revolution checks -> Health events -> Elections -> Capitulation
  -> Results written to country_states_per_round + global_state_per_round
Inter-Round (5-10 min): Unit movement only
  -> Deploy from reserve, withdraw, reposition
Next Round: Round counter advances, key events triggered
```

**State machine:** `setup -> pre_start -> active (A) -> processing (B) -> inter_round -> active (next) -> ... -> completed`

### 2.4 Data Model

**Template -> SimRun Hierarchy:**
```
TEMPLATE (master SIM design, stored in default sim_run 00000000-0000-0000-0000-000000000001)
  -> SIM-RUN (one execution -- full copy of template data, immutable once started)
```

**Core tables (copied on SimRun creation -- 11-table copy):**

| Table | Rows | Description |
|-------|------|-------------|
| `countries` | 20 | Country entities with 40+ fields (economic, military, political, tech) |
| `roles` | 40 | Player roles with positions[], character_name, public_bio, confidential_brief |
| `role_actions` | 713 | Action permissions (role_id x action_id) |
| `deployments` | 345 | Individual military units (1 row = 1 unit) with hex coordinates |
| `relationships` | 380 | Bilateral relationships (from/to country, basing rights) |
| `zones` | 57 | Map zones (named entities for chokepoints, blockades) |
| `organizations` | 7 | Orgs (Western Treaty, EU, BRICS+, OPEC+, UNSC, etc.) |
| `org_memberships` | 50 | Country membership in organizations |
| `sanctions` | 43 | Initial sanctions (imposer, target, level) |
| `tariffs` | 14 | Initial tariffs (imposer, target, level) |
| `world_state` | 1 | Global state (oil_price, market indexes) |

**Runtime tables (populated during play):**

| Table | Description |
|-------|-------------|
| `observatory_events` | All action outcomes with JSONB payload |
| `pending_actions` | Moderator confirmation queue |
| `agent_decisions` | Batch decisions queued for Phase B processing |
| `exchange_transactions` | Asset transfer proposals (coins, units, tech) |
| `agreements` | Diplomatic commitments with signatory tracking |
| `election_*` | Nominations, votes, results |
| `hex_control` | Territory occupation (persistent) |
| `blockades` | Active naval blockades |
| `meeting_invitations` | Meeting requests (pending/accepted/expired) |
| `artefacts` | Role-specific classified documents |
| `country_states_per_round` | All country metrics snapshotted after Phase B |
| `global_state_per_round` | Oil price, market indexes per round |

**Hex coordinate system:** Pointy-top hexagons, odd-r offset, (row, col) 1-indexed. Global: 10x20. Theater: 10x10. Config: `app/engine/config/map_config.py`.

**Individual unit model:** Each deployment row = 1 unit (not aggregate counts). 345 units on 68 hex positions. Source: `2 SEED/C_MECHANICS/C4_DATA/units.csv`.

Full data model reference: `MODULES/COMPREHENSIVE_BUILD_DOCUMENTATION.md` sections 3-5.

---

## Part 3: Module Status

### M1 -- World Model Engines

**Purpose:** Four domain engines that model the simulation world. All are pure functions -- no DB calls, stateless. Receive game state as input, return updated state as output.

**Status:** MOSTLY ALIGNED | 720 L1 tests passing

| Engine | File | Lines | Key Capabilities |
|--------|------|-------|-----------------|
| Economic | `engines/economic.py` | 2,190 | GDP growth, oil price (S-curve), sanctions (S-curve), tariffs, budget, inflation, debt, contagion, dollar credibility |
| Military | `engines/military.py` | 3,086 | Ground (RISK dice), air strike (12%/6%), naval (1v1 dice), bombardment (10%/unit), missile (two-phase), covert ops |
| Political | `engines/political.py` | 830 | Stability, support, elections (AI-scored), revolution, health events, war tiredness, capitulation |
| Technology | `engines/technology.py` | 357 | Nuclear progression (5-tier), AI progression (4 levels), R&D thresholds |
| Orchestrator | `engines/orchestrator.py` | 656 | Phase B round processing (calls all engines in sequence) |

**Key files:** `app/engine/engines/*.py`, `app/engine/config/map_config.py`
**Applicable contracts:** All 28 contracts in `3 DETAILED DESIGN/CONTRACTS/`

### M2 -- Communication & Realtime

**Purpose:** Action contracts, dispatcher, validators, real-time channels, event schemas.

**Status:** DONE | 33 canonical action types reconciled

**Key files:** `app/engine/services/action_dispatcher.py`, 14 validator files, `app/frontend/src/lib/channelManager.ts`
**Realtime:** 16 tables published for WebSocket push. ChannelManager deduplicates channels.

### M3 -- Data Foundation

**Purpose:** Template/SimRun hierarchy, DB schema, seed data, state snapshots.

**Status:** ALIGNED | 64 DB tables, 11-table copy on SimRun creation

**Key files:** `app/engine/services/sim_create.py`, `app/engine/models/db.py`

### M4 -- Sim Runner & Facilitator

**Purpose:** Runtime engine for live simulations. Lifecycle management, moderator controls, confirmation queue.

**Status:** DONE (all 5 phases) | 43+ API endpoints

**Key files:** `app/engine/services/sim_run_manager.py`, `app/frontend/src/pages/FacilitatorDashboard.tsx`
**Spec:** `MODULES/M4_SIM_RUNNER/SPEC_M4_SIM_RUNNER.md`

### M5 -- AI Participant

**Purpose:** Autonomous AI agents that play alongside humans. 4-block cognitive model, tool-use interface, 25 action types.

**Status:** STUB | AI stub submits default decisions. Full LLM agent wiring pending.

**Key files:** `app/engine/agents/leader.py`, `app/engine/agents/leader_round.py`, `app/engine/agents/full_round_runner.py`
**Concept:** `1. CONCEPT/CONCEPT V 2.0/CON_F1_AI_PARTICIPANT_MODULE_v2.frozen.md`
**Design:** `3 DETAILED DESIGN/AI_CONCEPT.md`, `PHASES/UNMANNED_SPACECRAFT/AI_CONCEPT.md`
**Heritage spec:** `2 SEED/D_ENGINES/SEED_E5_AI_PARTICIPANT_MODULE_v1.md`

**Vision-to-implementation gaps (see Part 6):** Information scoping not enforced, autonomous polling loop not built, agent-initiated conversations not implemented, goal evolution not persisted.

### M6 -- Human Participant Interface

**Purpose:** What 25-30 human participants see and interact with. Action submission, world view, asymmetric information.

**Status:** IN PROGRESS (Sprint 6.7 done)

**Key files:** `app/frontend/src/pages/ParticipantDashboard.tsx` (7,108 lines)
**Spec:** `MODULES/M6_HUMAN_INTERFACE/SPEC_M6_HUMAN_INTERFACE.md`

**Built:** Unified Attack system (5 combat types), territory occupation, ground movement, blockade, martial law, conventional missile, all action forms, artefact rendering, 5-tab structure (Actions, Confidential, Country, World, Map).

### M7 -- Navigator

**Purpose:** Personal AI assistant for human participants. Rules explanation, strategy guidance, post-SIM reflection.

**Status:** NOT STARTED

### M8 -- Public Screen

**Purpose:** Room projection. War room situation display + stock exchange ticker + doomsday clock.

**Status:** ~90%

**Key files:** `app/frontend/src/pages/PublicScreen.tsx` (936 lines)
**Remaining:** Doomsday indices are hardcoded placeholders (LLM calculation at Phase B needed). Columbia vs Cathay power trend uses static data.

### M9 -- Sim Setup & Configuration

**Purpose:** Template editing, SimRun creation, user management, AI setup. Pre-simulation.

**Status:** v2 DONE | 10-tab Template Editor, 5-step SimRun wizard

**Key files:** `app/frontend/src/pages/SimRunWizard.tsx`, `app/frontend/src/pages/TemplateEditor.tsx`
**Spec:** `MODULES/M9_SIM_SETUP/SPEC_M9_SIM_SETUP.md`

### M10.1 -- Auth

**Purpose:** Front door. Email/password + Google OAuth. Moderator and participant roles.

**Status:** DONE

**Key files:** `app/engine/auth/`, `app/frontend/src/contexts/AuthContext.tsx`

### M10 -- Final Assembly

**Purpose:** Integration testing, reliability, production deployment.

**Status:** NOT STARTED

---

## Part 4: Action Reference

This section is designed for direct use by M5 AI agents. All 33 canonical action types with payload format, pre-conditions, and side effects.

### 4.1 Action Categories Overview

| Category | Actions | Dispatch | Count |
|----------|---------|----------|-------|
| Military | ground_attack, ground_move, air_strike, naval_combat, naval_bombardment, naval_blockade, launch_missile_conventional, nuclear_test, nuclear_launch_initiate, nuclear_authorize, nuclear_intercept, basing_rights, martial_law, move_units | IMMEDIATE (Phase A) | 14 |
| Economic | set_budget, set_tariffs, set_sanctions, set_opec | BATCH (Phase B) | 4 |
| Diplomatic | propose_transaction, accept_transaction, propose_agreement, sign_agreement, public_statement, call_org_meeting, meet_freely, declare_war | IMMEDIATE | 8 |
| Covert | covert_operation, intelligence | IMMEDIATE | 2 |
| Political | arrest, assassination, change_leader, reassign_types, self_nominate, cast_vote | IMMEDIATE | 6 |

**Routing:** `POST /api/sim/{id}/action` -> validate -> `action_dispatcher.dispatch_action()` -> engine function -> DB writes -> observatory_events

### 4.2 Position-Based Authorization

Actions are authorized by position held (stored in `roles.positions[]`):

| Position | Actions |
|----------|---------|
| **head_of_state** | declare_war, arrest, reassign_types, martial_law, set_budget, set_tariffs, set_sanctions, ground_attack, air_strike, naval_combat, naval_bombardment, launch_missile_conventional, naval_blockade, move_units, ground_move, propose_transaction, propose_agreement, basing_rights + dynamic: set_opec (OPEC), nuclear_* (nuclear level) |
| **military** | ground_attack, air_strike, naval_combat, naval_bombardment, launch_missile_conventional, naval_blockade, move_units, ground_move, intelligence, assassination |
| **economy** | set_budget, set_tariffs, set_sanctions + dynamic: set_opec (OPEC) |
| **diplomat** | propose_transaction, propose_agreement, basing_rights, intelligence |
| **security** | intelligence, covert_operation, assassination, arrest |
| **opposition** | intelligence |
| **all roles** | public_statement, invite_to_meet, change_leader |

**Action limits (per SIM):**

| Position | intelligence | covert_operation | assassination | arrest |
|----------|-------------|-----------------|---------------|--------|
| security | 5 | 7 | 3 | 4 |
| military | 5 | -- | 2 | -- |
| head_of_state | -- | -- | -- | 4 |
| diplomat | 1 | -- | -- | -- |
| opposition | 2 | -- | -- | -- |

**Dynamic conditions:**
- `set_opec`: OPEC members only (caribe, mirage, persia, sarmatia, solaria)
- `martial_law`: Eligible countries only (sarmatia, cathay, persia, ruthenia)
- `nuclear_test/launch`: Gated on nuclear_level
- Columbia election actions (`self_nominate`, `cast_election_vote`): All Columbia citizens

### 4.3 Military Actions

#### `ground_attack` -- WORKING

```json
{
  "action_type": "ground_attack",
  "role_id": "shield", "country_code": "columbia",
  "target_row": 4, "target_col": 11,
  "source_global_row": 4, "source_global_col": 10,
  "attacker_unit_codes": ["col_g_01", "col_g_02", "col_g_03"],
  "theater": "eastern_ereb",
  "target_theater_row": 4, "target_theater_col": 5
}
```

**Pre-conditions:** ground_attack permission, ground units at source hex, target within range (BFS adjacency, range=1), must leave 1 unit behind (max = min(3, count-1))
**Mechanic:** RISK dice (1-3 units, iterative exchanges). Modifiers: AI L4 (+1 die), low morale stability<=3 (-1 die), air support (+1 defender)
**Side effects:** Destroyed units deleted. Survivors advance to target hex. Non-ground enemies captured (country_id changed, status=reserve). `hex_control` upserted. Blockade integrity checked.
**Event:** `observatory_events` INSERT, event_type = "ground_attack"

#### `ground_move` -- WORKING

```json
{
  "action_type": "ground_move",
  "role_id": "shield", "country_code": "columbia",
  "target_row": 5, "target_col": 10,
  "source_global_row": 4, "source_global_col": 10,
  "attacker_unit_codes": ["col_g_01"]
}
```

**Pre-conditions:** ground_attack permission, adjacent LAND hex (sea hexes filtered), leave 1 behind
**Side effects:** Unit moved. Non-ground enemies captured. hex_control upserted.

#### `air_strike` -- WORKING

```json
{
  "action_type": "air_strike",
  "role_id": "shield", "country_code": "columbia",
  "target_row": 4, "target_col": 11,
  "attacker_unit_codes": ["col_ta_01", "col_ta_02"]
}
```

**Mechanic:** 12% hit per aircraft (6% if target has AD). 15% downed by AD per aircraft. Once per round per unit.

#### `naval_combat` -- WORKING

```json
{
  "action_type": "naval_combat",
  "role_id": "shield", "country_code": "columbia",
  "target_row": 5, "target_col": 15,
  "attacker_unit_codes": ["col_n_01"]
}
```

**Mechanic:** 1v1 dice (higher wins, ties -> defender wins). Once per round per unit.

#### `naval_bombardment` -- WORKING

Same payload as naval_combat but targets ground units at hex. 10% hit probability per naval unit (probability-based, no dice).

#### `launch_missile_conventional` -- WORKING

```json
{
  "action_type": "launch_missile_conventional",
  "role_id": "helmsman", "country_code": "cathay",
  "target_row": 6, "target_col": 8,
  "attacker_unit_codes": ["cat_sm_01"],
  "target_choice": "military"
}
```

**`target_choice`:** `military` (destroy unit), `infrastructure` (-2% GDP), `nuclear_site` (halve R&D), `AD` (destroy AD unit)
**Mechanic:** Two-phase: AD intercept 50% per AD unit, then hit at 75% flat. Missile always consumed.
**Range:** T1 (nuc 0-1) <= 2 hexes, T2 (nuc 2) <= 4 hexes, T3 (nuc 3+) global

#### `naval_blockade` -- WORKING

```json
{
  "action_type": "naval_blockade",
  "role_id": "shield", "country_code": "columbia",
  "operation": "establish", "zone_id": "gulf_gate", "level": "full"
}
```

**Operations:** `establish`, `lift`, `reduce`
**Chokepoints:** `gulf_gate`, `caribe_passage`, `cathay_strait`
**Pre-conditions:** Naval units at chokepoint hex

#### `martial_law` -- WORKING

```json
{
  "action_type": "martial_law",
  "role_id": "helmsman", "country_code": "cathay"
}
```

**Pre-conditions:** Country in eligible list. Not already declared.
**Side effects:** Stability boost, martial_law_declared = true

#### `move_units` -- WORKING (inter_round phase only)

```json
{
  "action_type": "move_units",
  "role_id": "shield", "country_code": "columbia",
  "movements": [
    {"unit_id": "col_g_05", "action": "deploy", "target_row": 4, "target_col": 8},
    {"unit_id": "col_g_06", "action": "withdraw"},
    {"unit_id": "col_g_07", "action": "reposition", "target_row": 5, "target_col": 9}
  ]
}
```

**Movement types:** deploy (reserve -> active), withdraw (active -> reserve), reposition (hex -> hex)
**Auto-embark:** Ground/air to sea hex with carrier auto-embarks. Auto-debark on land move.

#### `nuclear_launch_initiate` -- WIRED

```json
{
  "action_type": "nuclear_launch_initiate",
  "role_id": "dealer", "country_code": "columbia",
  "missiles": [{"target_row": 8, "target_col": 15}],
  "rationale": "Retaliatory strike"
}
```

**Flow:** INITIATE -> AUTHORIZE (military officer) -> ALERT + INTERCEPT (target) -> RESOLVE
**Mechanics:** Nuclear hit prob 80%, AD intercept 50%, leader death probability 1/6

#### `nuclear_authorize` / `nuclear_intercept` -- WIRED (reactive)

Reactive actions triggered by nuclear launch. Payload includes `nuclear_action_id` and `confirm`/`intercept` boolean.

#### `nuclear_test` -- NOT WIRED (engine expects Pydantic input model)

#### `basing_rights` -- ROUTED

Operations: `grant`, `revoke`. Allows foreign military units on your territory.

### 4.4 Economic Actions (Batch -- queued for Phase B)

#### `set_budget`

```json
{
  "action_type": "set_budget",
  "role_id": "dealer", "country_code": "columbia",
  "social_spending": 0.20, "military_spending": 0.35,
  "technology_spending": 0.15, "infrastructure_spending": 0.30
}
```

#### `set_tariffs`

```json
{
  "action_type": "set_tariffs",
  "role_id": "dealer", "country_code": "columbia",
  "target_country": "cathay", "level": 2
}
```

**Levels:** L0 (none) to L3 (heavy). Hurt both sides asymmetrically.

#### `set_sanctions`

```json
{
  "action_type": "set_sanctions",
  "role_id": "dealer", "country_code": "columbia",
  "target_country": "cathay", "level": -2
}
```

**Levels:** -3 to +3. Coalition-based. Cost imposer 30-50% of damage inflicted.

#### `set_opec`

```json
{
  "action_type": "set_opec",
  "role_id": "wellspring", "country_code": "solaria",
  "production_level": "increase"
}
```

**Options:** `increase`, `decrease`, `maintain`

### 4.5 Diplomatic Actions

#### `declare_war` -- WORKING

```json
{
  "action_type": "declare_war",
  "role_id": "dealer", "country_code": "columbia",
  "target_country": "cathay"
}
```

**Side effects:** Both relationship directions set to `at_war`.

#### `public_statement` -- WORKING

```json
{
  "action_type": "public_statement",
  "role_id": "dealer", "country_code": "columbia",
  "statement": "Columbia stands with Formosa against aggression."
}
```

**Side effects:** Observatory event only (no engine processing).

#### `propose_transaction` / `accept_transaction` -- ROUTED

```json
{
  "action_type": "propose_transaction",
  "role_id": "dealer", "country_code": "columbia",
  "counterpart_country": "albion",
  "offer": {"type": "military_units", "units": ["col_g_10"]},
  "request": {"type": "technology", "tech_type": "nuclear", "boost": 0.20},
  "visibility": "secret"
}
```

**Response options for accept_transaction:** `accept`, `reject`, `counter`

#### `propose_agreement` / `sign_agreement` -- ROUTED

```json
{
  "action_type": "propose_agreement",
  "role_id": "dealer", "country_code": "columbia",
  "agreement_name": "Mutual Defense Pact", "agreement_type": "defense_pact",
  "counterpart_countries": ["albion", "gallia"],
  "terms": "Mutual defense against aggression...", "visibility": "public"
}
```

#### `call_org_meeting` / `meet_freely` / `invite_to_meet` -- STUB/BASIC

`invite_to_meet` creates a `meeting_invitations` row (expires in 10 minutes, max 2 active per role).

### 4.6 Covert Actions

#### `covert_operation` -- ROUTED

```json
{
  "action_type": "covert_operation",
  "role_id": "shadow", "country_code": "levantia",
  "op_type": "sabotage", "target_country": "sarmatia"
}
```

**Op types:** `espionage`, `sabotage`, `cyber`, `disinformation`, `election_meddling`

**Base probabilities:** espionage 60%, sabotage 45%, cyber 50%, disinformation 55%, election_meddling 40%

#### `intelligence` -- ROUTED

```json
{
  "action_type": "intelligence",
  "role_id": "shadow", "country_code": "columbia",
  "question": "What is Cathay's military readiness?"
}
```

**Mechanic:** LLM generates intelligence report based on world state and question. Result stored as artefact.

### 4.7 Political Actions

#### `arrest` -- WORKING (requires moderator confirmation)

```json
{
  "action_type": "arrest",
  "role_id": "furnace", "country_code": "sarmatia",
  "target_role": "ironhand", "rationale": "Suspected treason"
}
```

**Pre-conditions:** Initiator is HoS. Target is same country, active.
**Side effects:** Target role status = "arrested".

#### `assassination` -- WORKING (requires confirmation)

```json
{
  "action_type": "assassination",
  "role_id": "shadow", "country_code": "levantia",
  "target_role": "furnace"
}
```

**Mechanic:** 20% base probability (+ country bonuses: Levantia +30%, Sarmatia +10%). Kill -> role removed. Survive -> sympathy stability boost.

#### `change_leader` -- WORKING (3-phase)

Initiation -> Removal vote (strict majority of non-HoS) -> Election vote (absolute majority of all citizens)
**Pre-conditions:** Stability <= 4.0, initiator is non-HoS, 3+ active roles

#### `reassign_types` -- WORKING

HoS reassigns positions (military, economy, diplomat, security, opposition) to other roles. Cannot reassign head_of_state.

#### `self_nominate` / `cast_vote` -- ROUTED

Columbia election system. Nominations opened by moderator. Secret ballot.

---

## Part 5: Configuration Reference

### 5.1 Country Constants

**OPEC Members:** caribe, mirage, persia, sarmatia, solaria
**Martial Law Eligible:** sarmatia (pool 10), cathay (10), persia (8), ruthenia (6)
**Columbia Election Actions:** self_nominate, cast_election_vote (all Columbia citizens)
**Elderly Leaders:** columbia/dealer (age 80, medical 0.9), cathay/helmsman (73, 0.7), sarmatia/pathfinder (73, 0.6)

### 5.2 Regime Types

Countries have `regime_type` that affects political mechanics:
- **Democratic:** Face elections, opposition has power, stability affected by public support
- **Authoritarian:** Face coups, no meaningful opposition, stability affected by elite loyalty
- **Hybrid:** Mixed mechanics

### 5.3 Key Scheduled Events

| Round | Event |
|-------|-------|
| R1 | Ereb Union Session, The Cartel Meeting, GSC Session on Persia Crisis, Columbia Parliament Session, Phrygia Peace Talks |
| R2 | Columbia Mid-Term Parliamentary Elections (nominations R1), New League Meeting, Western Treaty Session |
| R6 | Columbia Presidential Election (nominations R5) |

### 5.4 Engine Constants

**Economic:**
- OIL_BASE_PRICE = 80.0, FLOOR = 15.0, SOFT_CAP = 200.0
- Economic states: normal -> stressed -> crisis -> collapse

**Military:**
- COVERT_BASE_PROBABILITY: espionage 0.60, sabotage 0.45, cyber 0.50, disinformation 0.55, election_meddling 0.40
- NUCLEAR_HIT_PROB = 0.80, AD_INTERCEPT = 0.50, LEADER_DEATH = 1/6
- MISSILE_HIT_PROB = 0.75, MISSILE_AD_INTERCEPT = 0.50

**Political:**
- STABILITY_THRESHOLDS: unstable 6, protest_probable 5, protest_automatic 3, regime_collapse 2, failed_state 1

**Technology:**
- NUCLEAR_RD_THRESHOLDS: L0->L1 at 0.60, L1->L2 at 0.80, L2->L3 at 1.00
- AI_RD_THRESHOLDS: L0->L1 at 0.20, L1->L2 at 0.40, L2->L3 at 0.60, L3->L4 at 1.00
- AI_LEVEL_COMBAT_BONUS: {0:0, 1:0, 2:0, 3:1, 4:2}
- AI L4: +30% GDP growth rate

### 5.5 Probability Reference (Covert/Political)

| Module | Constant | Value |
|--------|----------|-------|
| propaganda_engine | SUCCESS_PROB | 0.55 |
| propaganda_engine | ATTRIBUTION_PROB | 0.20 |
| sabotage_engine | SUCCESS_PROB | 0.50 |
| sabotage_engine | ATTRIBUTION_PROB | 0.50 |
| election_meddling_engine | SUCCESS_PROB | 0.40 |
| election_meddling_engine | DETECTION_PROB | 0.45 |
| assassination_engine | SUCCESS_PROB | 0.20 |
| assassination_engine | ATTRIBUTION_PROB | 0.50 |
| coup_engine | BASE_PROB | 0.15 |
| coup_engine | PROTEST_BONUS | 0.25 |

**Note:** These probabilities are scattered across 8+ engine files with no central config. This is a known debt item (see Part 6, M13).

---

## Part 6: Known Debt & Next Steps

Consolidated from 4 audit reports (2026-04-20) and cross-checked independently. Ordered by priority.

### CRITICAL (must fix before any live event)

| # | Issue | Source | Effort |
|---|-------|--------|--------|
| C1 | **RLS blocks participants** from `sim_runs`, `roles`, `role_actions`, `sanctions`, `tariffs`, `world_state`, `org_memberships`, `organizations` -- ParticipantDashboard is broken for non-moderator users | Realtime Audit | 1 migration, 9 policies, ~30 min |
| C2 | **`role_relationships` has NO SELECT policy** -- blocked for everyone | Realtime Audit | 5 min |
| C3 | **Sync-over-async DB calls** -- all `supabase.py` async functions wrap sync HTTP, blocking FastAPI event loop under load | Scalability Audit | 1-3 days |
| C4 | **Sync LLM calls blocking event loop** -- `_call_anthropic()` and `_call_gemini()` are sync inside async `_call_provider()` | Scalability Audit | 30 min |

### HIGH (should fix before production)

| # | Issue | Effort |
|---|-------|--------|
| H1 | **49 tables NOT published for Realtime** -- key tables (`roles`, `sanctions`, `tariffs`, `world_state`) cause stale data | 1 day |
| H2 | **Single FastAPI process, no workers** -- one blocked request stalls all | 1 hour |
| H3 | **PublicScreen has no auth but needs authenticated RLS** -- broken for unauthenticated viewers | Half day |
| H4 | **14 duplicate `_write_event()` functions** with inconsistent parameter order | 1 day |
| H5 | **13 duplicate `_get_scenario_id()` functions** | Half day |
| H6 | **`resolve_round.py` labeled DEPRECATED but is core engine** -- imported by 29 test files + `full_round_runner.py` | Design decision |
| H7 | **Batch ParticipantDashboard REST calls** -- 22 REST calls per page load x 30 users = 660 burst | 1 day |
| H8 | **Election votes readable by unauthenticated users** -- secret ballot compromised | 15 min |

### MEDIUM (should fix before scaling)

| # | Issue | Effort |
|---|-------|--------|
| M1 | `_hex_distance()` duplicated in 5 files | 1 hour |
| M2 | MARTIAL_LAW_POOLS in 4 places (3 backend + 1 frontend) | 1 hour |
| M3 | OPEC_MEMBERS in 3 places | 30 min |
| M4 | ParticipantDashboard.tsx is 7,108 lines -- monolith | 2-3 days |
| M5 | N+1 query in combat events endpoint | 30 min |
| M6 | `country_code` vs `country_id` naming split across DB and code (11 tables use one, 4 use the other) | Multi-sprint |
| M7 | `position_type` vs `positions[]` vs `is_*` booleans -- 3 systems for same concept | Design decision |
| M8 | 14 orphan DB tables (0 rows, no code references) | 30 min |
| M9 | Deprecated columns still in schema (`ticking_clock`, `fatherland_appeal`, `zone_id`) | 1 migration |
| M10 | Doomsday Indices and Power Balance hardcoded on PublicScreen | 1 day |
| M11 | 7 deprecated files (4,500 lines) still imported by active code | Half day |
| M12 | `useRealtimeRow` bypasses ChannelManager deduplication | 2 hours |
| M13 | Probabilities scattered across 8+ engine files with no central config | 1 day |

### BLIND SPOTS (not covered by any audit)

1. **Error handling / partial failure resilience** -- no analysis of LLM failure mid-agent-round or DB write failure mid-combat
2. **`test-interface/` directory** -- hex map renderer has own server, endpoints, config duplication. Unaudited.
3. **Actual database indexes** -- no audit queried `pg_indexes`. Scalability recommendations unverified.
4. **Security beyond RLS** -- CORS is currently `*`. No rate limiting on action submissions.
5. **Data migration / rollback safety** -- rollback endpoint untested for full 11-table restoration.
6. **WebSocket reconnection behavior** -- ChannelManager re-subscribe behavior under network instability unknown.

### M5 AI Participant -- Vision vs Implementation Gaps

| Aspect | Vision | Current | Gap |
|--------|--------|---------|-----|
| Cognitive model (4 blocks) | Full | Block 1+2 loaded, Block 3+4 basic | Memory tiers, goal evolution |
| Information scoping | Role-based visibility | Agents see most data | **Critical -- need filtering** |
| Active loop | Continuous 10-30s polling | Up to 3 actions per round (batch) | Need real polling loop |
| Conversations | Initiated by agent proactively | Triggered by orchestrator after actions | Agent should REQUEST conversations |
| Transactions | Agent proposes + counterpart evaluates | Proposals logged but not executed | Wire transactions.py |
| Memory persistence | All blocks persisted to DB | Conversation memories persisted | Goal updates need persistence |
| Event reactions | Real-time push -> agent responds | Prior-round events in prompt | Need intra-round reactions |
| Module independence | Standalone, API-only | Tightly coupled to round runner | Need clean API boundary |

---

## Part 7: Document Heritage

### The Design Hierarchy

```
CONCEPT (frozen) -> WHAT and WHY
  1. CONCEPT/CON_TOP_TTT_CONCEPT_v1.frozen.md   -- top of hierarchy, overall vision
  1. CONCEPT/CONCEPT V 2.0/CON_A1_*.frozen.md    -- Thucydides Trap phenomenon
  1. CONCEPT/CONCEPT V 2.0/CON_A2_*.frozen.md    -- Core tensions
  1. CONCEPT/CONCEPT V 2.0/CON_F1_*.frozen.md    -- AI Participant Module concept

SEED (frozen) -> HOW (specification level)
  2 SEED/C_MECHANICS/   -- game mechanics, map, units
  2 SEED/D_ENGINES/     -- engine specs, AI participant spec (SEED_E5)
  2 SEED/B_ACTORS/      -- countries, roles, organizations

DET (reference) -> HOW (implementation level)
  3 DETAILED DESIGN/CONTRACTS/  -- 28 locked action specifications
  3 DETAILED DESIGN/CARDS/      -- action reference cards
  3 DETAILED DESIGN/AI_CONCEPT.md  -- AI participant design (living)

CODE (active) -> IMPLEMENTS DET SPECS
  app/                          -- application code

THIS DOCUMENT (ARCHITECTURE.md) -> LIVING TRUTH
  Single source for architecture, status, and debt
```

### Contract Status

**Contracts still accurate (code matches spec):**

| Contract | Version | Notes |
|----------|---------|-------|
| CONTRACT_GROUND_COMBAT | - | RISK dice, modifiers, advance/capture |
| CONTRACT_AIR_STRIKES | - | 12%/6% hit, 15% downed by AD |
| CONTRACT_NAVAL_COMBAT | - | 1v1 dice, ties -> defender |
| CONTRACT_NAVAL_BOMBARDMENT_BLOCKADE | - | 10%/unit, 3 chokepoints |
| CONTRACT_NUCLEAR_CHAIN | 1.0 | 4-phase: initiate/authorize/alert+intercept/resolve |
| CONTRACT_CHANGE_LEADER | 1.0 | 3-phase voting, stability gate |
| CONTRACT_COLUMBIA_ELECTIONS | 2.0 | Mid-term + presidential |
| CONTRACT_MAP_RENDERING | 1.0 | Hex renderer, blast markers, clean mode |
| CONTRACT_BUDGET | 1.1 | Social/military/tech allocation |
| CONTRACT_SANCTIONS | 1.0 | S-curve model, coalition-based |
| CONTRACT_POWER_ASSIGNMENTS | 1.0 | Position reassignment |

**Contracts with potential divergence (verify before relying):**

| Contract | Concern |
|----------|---------|
| CONTRACT_MOVEMENT | Code added auto-embark/debark not in original spec |
| CONTRACT_TARIFFS | Code may have evolved beyond original spec |
| CONTRACT_TRANSACTIONS | Engine routed but transaction execution may be incomplete |
| CONTRACT_AGREEMENTS | Engine routed but full lifecycle may differ from spec |
| CONTRACT_INTELLIGENCE | LLM-based generation -- behavior depends on prompts |
| CONTRACT_ASSASSINATION | Country bonuses (Levantia +30%) may not match contract values |
| CONTRACT_ARREST | Spec may not cover all edge cases in current code |

**Archived contracts (superseded):**
- CONTRACT_COUP.md, CONTRACT_MASS_PROTEST.md, CONTRACT_ELECTIONS.md (v1) -- in `CONTRACTS/DEPRECATED/`

### Key Divergences: Vision vs Implementation

1. **"Unmanned Spacecraft" -> "Humans First" pivot.** The original strategy was to build a fully autonomous AI-only simulation first, test with 50+ runs, then add human interfaces. In practice, the project pivoted to humans-first: M6 (Human Interface) was built before M5 (AI Participant) is complete. The unmanned capability remains a target but is not the current priority.

2. **Scenario layer removed.** The original design had Template -> Scenario -> SimRun. The `sim_scenarios` table is retired. Customization now lives directly on Template or SimRun.

3. **AI Participant autonomy.** The concept envisions continuous 10-30s polling loops with proactive goal pursuit. Current implementation uses batch orchestration (2 visits per round, 3 actions each). The gap is acknowledged and planned for M5 completion.

4. **Information scoping.** The concept requires strict role-based visibility (public/country/role/moderator). Current AI agents see most data without filtering. This is the most critical gap for game integrity.

5. **Voice engine.** The concept includes ElevenLabs voice synthesis for face-to-face human-AI conversations. This is postponed beyond the 6-week sprint.

6. **Navigator AI.** Personal AI assistant for every participant (M7). Not started. Postponed to after core simulation works.

7. **33 vs 51 actions.** The concept mentioned ~51 action types across all categories. The implementation consolidated to 33 canonical action types. The reduction is intentional simplification, not a gap.

---

*This document supersedes `MODULES/COMPREHENSIVE_BUILD_DOCUMENTATION.md` as the project's architectural reference. The comprehensive build doc remains valuable for deep implementation details (line numbers, exact API responses, component-level analysis). This document provides the strategic overview.*

*Last updated: 2026-04-21. Next scheduled review: after M5 AI Participant completion.*
