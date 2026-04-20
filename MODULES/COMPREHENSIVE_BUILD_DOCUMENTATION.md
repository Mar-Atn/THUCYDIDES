# COMPREHENSIVE BUILD DOCUMENTATION
**Generated:** 2026-04-20 | **Project:** Thucydides Trap (TTT)
**Purpose:** Complete reference for any developer or AI agent joining the project

---

## TABLE OF CONTENTS

1. [Architecture Overview](#1-architecture-overview)
2. [M10.1 Auth — Authentication](#2-m101-auth)
3. [M1 World Model Engines](#3-m1-world-model-engines)
4. [M2 Communication & Realtime](#4-m2-communication--realtime)
5. [M3 Data Foundation](#5-m3-data-foundation)
6. [M4 Sim Runner & Facilitator](#6-m4-sim-runner--facilitator)
7. [M6 Human Participant Interface](#7-m6-human-participant-interface)
8. [M8 Public Screen](#8-m8-public-screen)
9. [M9 Sim Setup & Configuration](#9-m9-sim-setup--configuration)
10. [Complete Action Reference (32 Actions)](#10-complete-action-reference)
11. [API Endpoint Catalog](#11-api-endpoint-catalog)
12. [Frontend Component Map](#12-frontend-component-map)
13. [Configuration Reference](#13-configuration-reference)
14. [Known Limitations & Stubs](#14-known-limitations--stubs)

---

## 1. ARCHITECTURE OVERVIEW

### System Stack

| Layer | Technology | Location |
|-------|-----------|----------|
| **Backend** | Python 3.11+ / FastAPI | `app/engine/` |
| **Frontend** | TypeScript / React 18+ / Vite | `app/frontend/src/` |
| **Database** | Supabase (PostgreSQL + Realtime + Auth + Storage) | Cloud |
| **LLM** | Dual provider: Anthropic Claude + Google Gemini | `app/engine/config/settings.py` |
| **Maps** | Custom hex renderer (HTML/JS) | `app/test-interface/` |

### Directory Structure

```
app/
├── engine/                         # FastAPI backend (1,935 lines main.py)
│   ├── main.py                     # All API endpoints (~43 endpoints)
│   ├── auth/                       # JWT auth + Supabase integration
│   │   ├── models.py              # AuthUser Pydantic model
│   │   └── dependencies.py        # get_current_user, require_moderator
│   ├── config/
│   │   ├── settings.py            # Environment config + LLM model assignments
│   │   ├── map_config.py          # Hex grid, theaters, adjacency, attack ranges
│   │   └── position_actions.py    # Position-based action authorization
│   ├── engines/                    # Pure stateless engines (8,059 lines total)
│   │   ├── economic.py            # 2,190 lines — GDP, oil, sanctions, tariffs
│   │   ├── military.py            # 3,086 lines — 5 combat types + covert ops
│   │   ├── political.py           # 830 lines — stability, elections, revolutions
│   │   ├── technology.py          # 357 lines — R&D, nuclear, AI levels
│   │   ├── orchestrator.py        # 656 lines — Phase B round processing
│   │   ├── movement.py            # 254 lines — unit repositioning
│   │   └── round_tick.py          # 686 lines — per-round tick bridge
│   ├── services/                   # Business logic, DB access (54 files)
│   │   ├── action_dispatcher.py   # Routes 33 action types to engines
│   │   ├── sim_run_manager.py     # State machine lifecycle
│   │   ├── sim_create.py          # SimRun creation with 11-table copy
│   │   ├── blockade_engine.py     # Naval blockade management
│   │   ├── change_leader.py       # 3-phase leadership change
│   │   ├── transaction_engine.py  # Asset exchange proposals
│   │   ├── agreement_engine.py    # Diplomatic commitments
│   │   ├── election_engine.py     # Nominations + voting
│   │   ├── arrest_engine.py       # Arrest/release mechanics
│   │   ├── assassination_engine.py # Assassination attempts
│   │   ├── martial_law_engine.py  # Martial law enforcement
│   │   ├── intelligence_engine.py # Intelligence reports (LLM)
│   │   ├── ai_stub.py             # AI agent stub (default decisions)
│   │   ├── llm.py                 # Dual-provider plain text LLM calls
│   │   ├── llm_tools.py           # Tool-use adapter (Anthropic/Gemini)
│   │   ├── supabase.py            # DB client operations
│   │   ├── common.py              # write_event, get_scenario_id, etc.
│   │   └── *_validator.py         # 14 validator files
│   ├── orchestrators/
│   │   └── nuclear_chain.py       # 4-phase nuclear decision chain
│   ├── context/
│   │   ├── assembler.py           # LLM context assembly service
│   │   └── blocks.py              # Context block registry + builders
│   ├── agents/                     # AI participant code
│   │   ├── leader.py              # LeaderAgent (4-block cognitive model)
│   │   ├── leader_round.py        # Single-agent round runner
│   │   ├── full_round_runner.py   # 20-agent parallel runner
│   │   └── decisions.py           # Per-category decision functions
│   └── models/
│       ├── api.py                  # API request/response Pydantic models
│       └── db.py                   # DB table Pydantic models
├── frontend/src/                   # React app (13,902 lines total)
│   ├── pages/                      # 15 page components
│   ├── components/                 # Shared components
│   ├── lib/                        # Supabase client, queries, realtime hooks
│   ├── hooks/                      # (in lib/)
│   └── contexts/                   # AuthContext
└── tests/                          # L1/L2/L3 test suites
```

### Data Flow Pattern

```
Human/AI submits action
  → POST /api/sim/{id}/action (main.py)
  → Validate: sim active? role authorized? phase allows?
  → Check: needs moderator confirmation? → queue to pending_actions
  → If immediate: action_dispatcher.dispatch_action()
    → _route() → engine function (pure, no DB)
    → _apply_combat_losses() → DB writes (deployments delete/update)
    → write_event() → observatory_events INSERT
  → Supabase Realtime pushes UPDATE to all connected clients
```

---

## 2. M10.1 AUTH

**Status:** DONE | **Spec:** `MODULES/M10_INFRASTRUCTURE/SPEC_M10.1_AUTH.md`

### Purpose
Front door to the application. Email/password + Google OAuth. Two user types: moderator (needs approval) and participant (self-registers).

### Key Files

| File | Purpose |
|------|---------|
| `app/engine/auth/models.py` | `AuthUser` Pydantic model (id, email, display_name, system_role, status, data_consent) |
| `app/engine/auth/dependencies.py` | FastAPI deps: `get_current_user` (JWT verify via Supabase), `require_moderator` |
| `app/frontend/src/contexts/AuthContext.tsx` | React auth context (session, user, login/logout) |
| `app/frontend/src/pages/Login.tsx` | Login form (160 lines) |
| `app/frontend/src/pages/Register.tsx` | Registration form with role selection + GDPR consent (289 lines) |
| `app/frontend/src/components/ProtectedRoute.tsx` | Route guard component |
| `app/frontend/src/components/DataConsentModal.tsx` | GDPR consent modal |

### Data Model

**Table: `users`**

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Supabase Auth UID |
| email | TEXT | User email |
| display_name | TEXT | Display name in SIM |
| system_role | TEXT | `moderator` or `participant` |
| status | TEXT | `registered`, `pending_approval`, `active`, `suspended` |
| data_consent | BOOLEAN | GDPR consent flag |
| created_at | TIMESTAMPTZ | Registration time |
| last_login_at | TIMESTAMPTZ | Last login |

### Auth Flow
1. User registers (email/password or Google OAuth)
2. If moderator: status = `pending_approval`, existing moderator approves
3. If participant: status = `registered`, immediate access
4. JWT token stored in Supabase session
5. Every API call: `Authorization: Bearer <token>` header
6. FastAPI extracts user via `get_current_user` dependency

### API Endpoints

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/api/auth/me` | User | Get current user profile |
| GET | `/api/admin/users` | Moderator | List all users |
| POST | `/api/admin/users/{id}/approve` | Moderator | Approve pending moderator |
| POST | `/api/admin/users/{id}/suspend` | Moderator | Suspend user |

---

## 3. M1 WORLD MODEL ENGINES

**Status:** MOSTLY ALIGNED | **720 L1 tests passing**

### Purpose
Four domain engines that model the simulation world. All are **pure functions** -- no DB calls, no side effects, stateless. Receive game state as input, return updated state as output.

### Economic Engine (`engines/economic.py` -- 2,190 lines)

**Processing sequence (chained, not parallel):**
1. Oil price (global, S-curve supply/demand model)
2. GDP growth per country (additive factor model + crisis multiplier)
3. Revenue per country (from GDP)
4. Budget execution (mandatory costs, deficit, money printing)
5. Military production costs and maintenance
6. Technology R&D costs
7. Inflation update
8. Debt service update
9. Economic state transitions (crisis ladder: normal -> stressed -> crisis -> collapse)
10. Momentum (confidence variable)
11. Contagion (crisis spreads to trade partners)
12. Sanctions impact (S-curve model, CONTRACT_SANCTIONS v1.0)
13. Tariff impact (CONTRACT_TARIFFS)
14. Dollar credibility

**Key constants:**
```python
OIL_BASE_PRICE = 80.0
OIL_PRICE_FLOOR = 15.0
OIL_SOFT_CAP_THRESHOLD = 200.0
OIL_DEMAND_DESTRUCTION_THRESHOLD = 100.0
OIL_SUPPLY_DEMAND_EXPONENT = 2.5
OIL_BLOCKADE_PARTIAL = 0.25  # 25% production loss
OIL_BLOCKADE_FULL = 0.50     # 50% production loss
```

**Input:** Country dicts + WorldState + actions dict (tariffs, sanctions, OPEC, budget, blockades)
**Output:** `EconomicResult` Pydantic model

### Military Engine (`engines/military.py` -- 3,086 lines)

**Five combat types, all working:**

| Type | Function | Mechanic | DB Effect |
|------|----------|----------|-----------|
| Ground | `resolve_ground_combat()` | RISK dice (1-3 units, iterative exchanges) | Deployment rows deleted |
| Air Strike | `resolve_air_strike()` | 12%/6% hit probability, 15% downed by AD | Deployment rows deleted |
| Naval | `resolve_naval_combat()` | 1v1 dice, ties -> defender wins | Deployment rows deleted |
| Bombardment | `resolve_naval_bombardment()` | 10% per naval unit | Deployment rows deleted |
| Missile | `resolve_missile_strike()` | Two-phase: AD intercept 50% then hit 75% | Deployment rows deleted, missile consumed |

**Combat modifiers (applied to dice):**
- AI Level 4: +1 bonus die
- Low morale (stability <= 3): -1 penalty die
- Air support (defender has tactical_air at hex): +1 defender
- Die hard zone: +1 defender (not yet implemented in dispatcher)

**Covert ops probability tables:**
```python
COVERT_BASE_PROBABILITY = {
    "espionage": 0.60, "sabotage": 0.45, "cyber": 0.50,
    "disinformation": 0.55, "election_meddling": 0.40,
}
```

### Political Engine (`engines/political.py` -- 830 lines)

**Functions:**
- `calc_stability()` -- multi-factor stability calculation (war, economy, assassination, sanctions)
- `calc_political_support()` -- for democracies, opposition dynamics
- `process_election()` -- AI-scored candidate evaluation
- `check_revolution()` -- regime collapse at stability < 2
- `check_health_events()` -- elderly leader health rolls
- `update_war_tiredness()` -- cumulative war fatigue
- `check_capitulation()` -- forced surrender conditions

**Key constants:**
```python
STABILITY_THRESHOLDS = {
    "unstable": 6, "protest_probable": 5,
    "protest_automatic": 3, "regime_collapse_risk": 2, "failed_state": 1,
}
ELDERLY_LEADERS = {
    "columbia": {"role": "dealer", "age": 80, "medical_quality": 0.9},
    "cathay": {"role": "helmsman", "age": 73, "medical_quality": 0.7},
    "sarmatia": {"role": "pathfinder", "age": 73, "medical_quality": 0.6},
}
```

### Technology Engine (`engines/technology.py` -- 357 lines)

**Nuclear progression (5-tier):**
```python
NUCLEAR_RD_THRESHOLDS = {0: 0.60, 1: 0.80, 2: 1.00}  # L0->L1, L1->L2, L2->L3
```

**AI progression (4 levels):**
```python
AI_RD_THRESHOLDS = {0: 0.20, 1: 0.40, 2: 0.60, 3: 1.00}
AI_LEVEL_TECH_FACTOR = {0: 0.0, 1: 0.0, 2: 0.005, 3: 0.015, 4: 0.030}  # growth rate boost
AI_LEVEL_COMBAT_BONUS = {0: 0, 1: 0, 2: 0, 3: 1, 4: 2}
```

### Orchestrator (`engines/orchestrator.py` -- 656 lines)

**Phase B round processing -- calls all engines in sequence:**
1. Apply submitted actions (tariffs, sanctions, OPEC, blockades)
2. Economic engine (steps 1-11)
3. Stability per country
4. Political support per country
5. War tiredness, revolution checks, health events
6. Elections (if scheduled for this round)
7. Capitulation checks
8. Write results to `country_states_per_round` and `global_state_per_round`
9. Generate observatory events

**Output:** `RoundResult` Pydantic model containing all domain results

---

## 4. M2 COMMUNICATION & REALTIME

**Status:** DONE

### Action Dispatcher (`services/action_dispatcher.py`)

Routes all 33 canonical action types to engines. Three dispatch categories:
- **IMMEDIATE** (Phase A): combat, covert ops, domestic, political, transactions
- **BATCH** (Phase B): budget, sanctions, tariffs, OPEC -- queued to `agent_decisions` table
- **MOVEMENT** (Inter-Round): unit repositioning

**Key function:** `dispatch_action(sim_run_id, round_num, action) -> dict`

After any combat action, automatically checks blockade integrity (units destroyed may degrade blockades).

### Validators (14 files)

All under `app/engine/services/*_validator.py`:

| Validator | Actions | Error Codes |
|-----------|---------|-------------|
| movement_validator | move_units | 17 |
| budget_validator | set_budget | 36 |
| tariff_validator | set_tariff | 11 |
| sanction_validator | set_sanction | 44 |
| opec_validator | set_opec | 39 |
| ground_combat_validator | ground_attack | 33 |
| air_strike_validator | air_strike | 23 |
| naval_combat_validator | naval_combat | 14 |
| bombardment_validator | bombardment | - |
| blockade_validator | blockade | - |
| missile_validator | launch_missile | - |
| nuclear_validator | nuclear_test/launch | 17 |
| domestic_validator | arrest, martial_law | 11 |
| covert_ops_validator | intelligence, sabotage, propaganda, election_meddling | 13 |
| political_validator | assassination, coup, mass_protest | 9 |

### Realtime Architecture

**Pattern: FastAPI is write-only. Supabase Realtime is the read distribution layer.**

```
WRITE: React -> FastAPI POST -> Supabase DB -> engine processing -> DB write
READ:  Supabase DB change -> Supabase Realtime (WebSocket) -> React client directly
```

**Tables with Realtime enabled:**
- `sim_runs` (UPDATE) -- phase transitions, timer
- `pending_actions` (INSERT, UPDATE) -- moderator queue
- `observatory_events` (INSERT) -- action feed
- `exchange_transactions` (INSERT, UPDATE) -- trade proposals
- `countries` (UPDATE) -- economic/political state
- `deployments` (INSERT, UPDATE, DELETE) -- unit movements
- `hex_control` (INSERT, UPDATE) -- territory occupation

**Frontend hooks:**
- `useRealtimeTable(table, filter)` -- subscribes to Postgres Changes, zero polling
- `useRealtimeRow(table, id)` -- subscribes to single row changes

**Channel structure:**
```
sim:{sim_id}:global        -- sim_runs, observatory_events
sim:{sim_id}:pending       -- pending_actions (moderator)
sim:{sim_id}:country:{cc}  -- countries filtered by id
sim:{sim_id}:diplomacy     -- exchange_transactions, agreements
sim:{sim_id}:map           -- Broadcast: unit positions, territory
sim:{sim_id}:presence      -- Presence: who's online
```

---

## 5. M3 DATA FOUNDATION

**Status:** ALIGNED

### Template -> SimRun Hierarchy

```
TEMPLATE (master SIM design, stored in default sim_run 00000000-0000-0000-0000-000000000001)
  └── SIM-RUN (one execution -- full copy of template data, immutable once started)
```

The `sim_scenarios` table is **retired**. All customization lives on Template or SimRun.

### Core Tables

| Table | Description | Key Columns |
|-------|-------------|-------------|
| `sim_templates` | Game definitions | id, name, version, schedule_defaults, key_events_defaults |
| `sim_runs` | Individual playthroughs | id, name, status, current_round, current_phase, template_id, facilitator_id, schedule, key_events, auto_approve, auto_attack, dice_mode |
| `countries` | 20 countries per sim | id, sim_run_id, sim_name, regime_type, gdp, stability, nuclear_level, ai_level, + 40 economic/military/political fields |
| `roles` | 40 roles per sim | id, sim_run_id, character_name, country_id, positions[], position_type, status, public_bio, confidential_brief |
| `role_actions` | 713 action permissions | sim_run_id, role_id, action_id |
| `deployments` | 345 units (1 row per unit) | sim_run_id, unit_id, country_id, unit_type, unit_status, global_row, global_col, theater, theater_row, theater_col, embarked_on |
| `zones` | 57 map zones | sim_run_id, zone_id, display_name, type, owner, theater |
| `relationships` | 380 bilateral relationships | sim_run_id, from_country, to_country, relationship, basing_rights_a_to_b, basing_rights_b_to_a |
| `organizations` | 7 organizations | sim_run_id, sim_name, decision_rule, chair_role_id |
| `org_memberships` | 50 memberships | sim_run_id, organization_id, country_code, role_in_org, has_veto |
| `sanctions` | 43 initial sanctions | sim_run_id, imposer, target, level |
| `tariffs` | 14 initial tariffs | sim_run_id, imposer, target, level |
| `world_state` | 1 global state row | sim_run_id, round_num, oil_price, wall_street_index, europa_index, dragon_index |

### Per-Round State Tables

| Table | Description |
|-------|-------------|
| `country_states_per_round` | All country metrics snapshotted after Phase B |
| `global_state_per_round` | Oil price, market indexes per round |

### Runtime Tables

| Table | Description |
|-------|-------------|
| `observatory_events` | All action outcomes with JSONB payload |
| `pending_actions` | Moderator confirmation queue |
| `agent_decisions` | Batch decisions (budget, tariffs, sanctions, OPEC) queued for Phase B |
| `exchange_transactions` | Asset transfer proposals |
| `agreements` | Diplomatic commitments with signatory tracking |
| `election_nominations` | Candidate registrations |
| `election_votes` | Secret ballots |
| `election_results` | Outcome with vote breakdown |
| `hex_control` | Territory occupation (occupied hexes) |
| `blockades` | Active naval blockades |
| `meeting_invitations` | Meeting requests (pending/accepted/expired) |
| `artefacts` | Role-specific classified documents |

### SimRun Creation (11-table copy)

When `POST /api/sim/create` is called, `engine/services/sim_create.py` copies:
1. countries (20 rows)
2. roles (40 rows)
3. role_actions (713 rows)
4. relationships (380 rows)
5. zones (57 rows)
6. deployments (345 rows)
7. organizations (7 rows)
8. org_memberships (50 rows)
9. sanctions (43 rows)
10. tariffs (14 rows)
11. world_state (1 row)

All re-keyed to new `sim_run_id`. Wizard customizations applied (role active/inactive, human/AI flags).

### Individual Unit Model

**Decision:** Each deployment row = 1 unit (not aggregate counts).

```
unit_id: "sar_g_01"          -- canonical unit ID from units.csv
country_id: "sarmatia"       -- owner
unit_type: "ground"          -- ground|naval|tactical_air|strategic_missile|air_defense
unit_status: "active"        -- active|reserve|destroyed|embarked
global_row: 4, global_col: 3 -- hex coordinates (1-indexed)
theater: "eastern_ereb"      -- theater name
theater_row: 4, theater_col: 3
embarked_on: null             -- carrier unit_id if embarked
```

345 units on 68 distinct hex positions. Source: `2 SEED/C_MECHANICS/C4_DATA/units.csv`.

### Hex Coordinate System

- **Type:** Pointy-top hexagons, odd-r offset
- **Coordinates:** `(row, col)`, 1-indexed, row first
- **Global map:** 10 rows x 20 cols
- **Theater maps:** 10 rows x 10 cols (Eastern Ereb, Mashriq)
- **Adjacency:** 6 neighbors per hex (even/odd row shift)
- **Config:** `app/engine/config/map_config.py` (THE source of truth)

---

## 6. M4 SIM RUNNER & FACILITATOR

**Status:** DONE (all 5 phases) | **Spec:** `MODULES/M4_SIM_RUNNER/SPEC_M4_SIM_RUNNER.md`

### Purpose
Runtime engine for live simulations. Manages lifecycle from pre-start through rounds to completion. Provides moderator with real-time control and visibility.

### State Machine (`services/sim_run_manager.py`)

```
setup -> pre_start -> active (Phase A) -> processing (Phase B)
  -> inter_round -> active (next round) -> ... -> completed
```

Valid transitions:
```python
VALID_TRANSITIONS = {
    "setup": ["pre_start", "aborted"],
    "pre_start": ["active", "aborted"],
    "active": ["processing", "paused", "aborted"],
    "processing": ["inter_round", "active", "aborted"],
    "inter_round": ["active", "aborted"],
    "paused": ["active", "aborted"],
    "completed": [],
    "aborted": [],
}
```

### Round Flow

1. **Phase A** (60-80 min): Free gameplay. Actions submitted. Immediate actions processed instantly. Batch decisions queued.
2. **Phase B** (5-12 min, automated): Orchestrator runs economic + political engines. Results written to DB.
3. **Inter-Round** (5-10 min): Unit movement only. Military repositioning.
4. **Next Round**: Round counter advances, key events triggered.

### Moderator Controls

| Control | Endpoint | Effect |
|---------|----------|--------|
| Start sim | `POST /api/sim/{id}/start` | pre_start -> active, R1 Phase A begins |
| End phase | `POST /api/sim/{id}/phase/end` | Advances to next phase (auto-triggers Phase B engines) |
| Extend | `POST /api/sim/{id}/phase/extend` | Adds minutes to current phase |
| Pause | `POST /api/sim/{id}/pause` | Freezes timer |
| Resume | `POST /api/sim/{id}/resume` | Resumes timer |
| End sim | `POST /api/sim/{id}/end` | Graceful end |
| Abort | `POST /api/sim/{id}/abort` | Emergency stop |
| Restart | `POST /api/sim/{id}/restart` | Full cleanup, re-copies 11 tables |
| Rollback | `POST /api/sim/{id}/rollback?target_round=N` | Delete data after round N |
| Go back | `POST /api/sim/{id}/phase/back` | Return to Phase A of current round |
| Set mode | `POST /api/sim/{id}/mode` | Toggle auto_approve, auto_attack, dice_mode |

### Confirmation Queue

Actions requiring moderator approval:
- `assassination`, `arrest` -- always queued (unless auto_approve ON)
- All combat (`ground_attack`, `air_strike`, `naval_combat`, `naval_bombardment`, `launch_missile_conventional`) -- queued unless auto_attack ON

**Table: `pending_actions`**

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| sim_run_id | UUID | FK |
| round_num | INT | Round submitted |
| action_type | TEXT | Action ID |
| role_id | TEXT | Who submitted |
| country_code | TEXT | Country |
| target_info | TEXT | Human-readable target description |
| payload | JSONB | Full action payload |
| status | TEXT | pending, confirmed, rejected |
| result | JSONB | Engine result (stored after confirmation) |

### Dice Mode

Two toggle states on `sim_runs`:
- `dice_mode` (BOOLEAN): When ON, ground_attack and naval_combat pause for physical dice input
- `auto_attack` (BOOLEAN): When ON, combat bypasses confirmation queue entirely

Physical dice flow:
1. Combat submitted -> queued as pending with `_requires_dice: true`
2. Moderator sees dice requirements (e.g., "Attacker rolls 3 dice, Defender rolls 2 dice")
3. Moderator inputs dice values in UI
4. `POST /api/sim/{id}/pending/{id}/confirm` with `{precomputed_rolls: {...}}`
5. Engine uses provided values instead of random generation

### Key Files

| File | Lines | Purpose |
|------|-------|---------|
| `app/engine/main.py` | 1,935 | All API endpoints |
| `app/engine/services/sim_run_manager.py` | ~300 | State machine lifecycle |
| `app/engine/services/action_dispatcher.py` | ~800 | Action routing |
| `app/frontend/src/pages/FacilitatorDashboard.tsx` | 2,160 | Moderator cockpit |

### Facilitator Dashboard Layout

```
Top Bar: R3 · Phase A · 42:17 [Back] [Pause] [Next] [Extend] [End Sim]
  Toggles: [Auto-Approve] [Auto-Attack] [Dice Mode]

Left Column (60%):
  - Pending Actions (confirmation queue with dice input)
  - SIM Events (live feed, filterable by category)
  - AI Participants (status, trigger button)

Right Column (40%):
  - Test Action Panel (submit as any role)
  - Participants (assignment)
  - Map/Public Screen links
  - Explore SIM Data
```

---

## 7. M6 HUMAN PARTICIPANT INTERFACE

**Status:** IN PROGRESS (Sprint 6.7 done) | **Spec:** `MODULES/M6_HUMAN_INTERFACE/SPEC_M6_HUMAN_INTERFACE.md`

### Purpose
What 25-30 human participants see and interact with during the simulation. Action submission, world view, asymmetric information (artefacts), Navigator AI assistant shell.

### Key Files

| File | Lines | Purpose |
|------|-------|---------|
| `app/frontend/src/pages/ParticipantDashboard.tsx` | 7,108 | Main participant view |
| `app/frontend/src/lib/action_constants.ts` | - | Action categories and descriptions |
| `app/frontend/src/components/ArtefactRenderer.tsx` | - | Classified document rendering |

### Tab Structure

| Tab | Content |
|-----|---------|
| **Actions** | Available actions by category (Military, Economic, Diplomatic, Political, Covert). "Actions Expected Now" section for urgent items. |
| **Strictly Confidential** | Role artefacts (classified reports, cables), confidential brief, intelligence |
| **Country** | Own country full state (GDP, stability, military, budget, sanctions) |
| **World** | All countries public data, relationship matrix, markets |
| **Global Map** | Clean map embed with blast markers |

### Unified Attack System (BUILT)

Single "Attack" button replaces 5 individual military action buttons. Combat type determined automatically from units.

**Flow:**
1. Click "Attack" -> map enters attack mode
2. Click source hex -> unit selection panel
3. Select units (max = min(3, count-1), must leave 1 behind)
4. Valid targets highlighted (red glow) based on `ATTACK_RANGE` + BFS adjacency
5. Click target hex -> combat preview (modifiers + win probability)
6. Confirm -> submitted (pending moderator or auto-resolved)

**Layout:** 25% sidebar / 75% map (side-by-side, stable)

**Map interaction via postMessage:**
```
Parent -> Map: highlight-hexes, clear-highlights, navigate-theater, refresh-units
Map -> Parent: hex-click (coordinates)
Map URL: ?mode=attack&country=X&sim_run_id=Y
```

### Territory & Capture

- **hex_control table:** Persistent occupation. Upserted on ground_attack victory and ground_move advance.
- **Unit capture:** Ground victory captures non-ground enemies as trophies (country_id changed, status=reserve)
- **Map display:** Diagonal stripes (owner + occupier colors) for occupied hexes
- **Basing rights:** Foreign units with basing agreement NOT treated as occupiers

### Artefacts System

Three types (from SEED_H3):
1. **Classified Intelligence Report** -- dark header, classification badge, structured sections
2. **Diplomatic Cable / Telegram** -- urgent styling, flash priority markers
3. **Personal Email** -- informal, from a specific sender

Current content: 3 pre-loaded artefacts (Helmsman/Cathay, Dealer/Columbia, Sabre/Levantia)

### Information Visibility

- **Public:** Map, unit counts, GDP, stability, market indexes, public agreements
- **Confidential (own country only):** Treasury, debt, production, budget, artefacts, secret agreements, covert ops results

Implementation: Frontend filters by `role.country_id === targetCountry.id`

---

## 8. M8 PUBLIC SCREEN

**Status:** ~90% | **Spec:** `MODULES/M8_PUBLIC_SCREEN/SPEC_M8_PUBLIC_SCREEN.md`

### Purpose
Room projection visible to all participants. Visual heartbeat of the simulation -- war room situation display meets stock exchange ticker meets doomsday clock.

### Key File
`app/frontend/src/pages/PublicScreen.tsx` -- 936 lines

### Layout

```
Header: Round + Phase + Timer + Real-world time (H1 2028)
Left (60-70%): Global hex map with units, blast markers, territory occupation
  Auto-rotates to theater maps when combat occurred (30s global, 15s each theater)
Right (30%): 4 Doomsday Indices (1-10 gauges)
  - Geopolitical Tension
  - Economic Health
  - Nuclear Danger
  - AI Race
Bottom left: Columbia vs Cathay power balance trend
Bottom: 2-line news ticker (public events, sorted by significance)
```

### Implementation Details

- **Map:** Same hex renderer, display-optimized (`?display=clean&sim_run_id=`)
- **Blast markers:** Combat events at hex coordinates, current round only, refreshed on unit changes
- **Blockade visuals:** Red border (dashed partial, solid full)
- **Doomsday indices:** PLACEHOLDER -- awaiting LLM calculation (Phase B engine hook)
- **News ticker:** Reads public `observatory_events`, filters out covert/secret

### Known Limitations
- Doomsday indices are hardcoded placeholders (LLM calculation TODO)
- Columbia vs Cathay power trend uses static data (needs real computation)

---

## 9. M9 SIM SETUP & CONFIGURATION

**Status:** v2 DONE | **Spec:** `MODULES/M9_SIM_SETUP/SPEC_M9_SIM_SETUP.md`

### Purpose
Moderator's control center before simulation starts. Template editing, SimRun creation, user management, AI setup.

### Key Files

| File | Lines | Purpose |
|------|-------|---------|
| `app/frontend/src/pages/ModeratorDashboard.tsx` | 267 | Quick actions + My Simulations |
| `app/frontend/src/pages/SimRunWizard.tsx` | 1,572 | 5-step create/edit wizard |
| `app/frontend/src/pages/TemplateEditor.tsx` | 159 | Tabbed template workspace |
| `app/frontend/src/pages/TemplateList.tsx` | 204 | Template management |
| `app/frontend/src/pages/UserManagement.tsx` | 535 | User admin (sortable table) |
| `app/frontend/src/pages/AISetup.tsx` | 246 | Global LLM model selection |
| `app/frontend/src/lib/queries.ts` | - | Supabase data layer |
| `app/engine/services/sim_create.py` | ~200 | Server-side SimRun creation |

### SimRun Wizard (5 steps)

1. **Select Template** -- list templates, click to select
2. **Configure** -- name, logo, description
3. **Countries & Roles** -- toggle active/inactive, human/AI per role
4. **Schedule** -- round durations, key events (elections, meetings)
5. **Review & Create** -- summary + create button

### Template Editor (10 tabs)

| Tab | Content |
|-----|---------|
| General | Name, version, description, status |
| Countries | 20 countries, 80+ fields each (economic, military, political, tech) |
| Roles | 40 roles grouped by country (identity, positions, covert ops deck) |
| Organizations | 7 orgs with membership matrix |
| Relationships | 20x20 matrix (5 relationship types, basing rights) |
| Sanctions & Tariffs | Imposer -> target -> level tables |
| Map | Hex map viewer + zone editing |
| Deployments | Unit placement (345 units) |
| Schedule | Default durations + key events |
| Formulas | READ-ONLY reference (12 key parameters displayed) |

### Key Events Convention

Stored as JSONB arrays on `sim_runs.key_events`:

| Round | Event | Type |
|-------|-------|------|
| R1 | Ereb Union Session | Organization meeting |
| R1 | The Cartel Meeting | Organization meeting |
| R1 | Global Security Council Session on Persia Crisis | Organization meeting |
| R1 | Columbia Parliament Session | Organization meeting |
| R1 | Phrygia Peace Talks (Shadow, Broker, Compass) | Trilateral negotiation |
| R2 | Columbia Mid-Term Parliamentary Elections | Election (nominations R1) |
| R2 | The New League Meeting | Organization meeting |
| R2 | Western Treaty Session | Organization meeting |
| R6 | Columbia Presidential Election | Election (nominations R5) |

### LLM Configuration

Stored in `sim_config` table. Current assignments:

| Use Case | Primary | Fallback |
|----------|---------|----------|
| Moderator (Argus) | Claude Sonnet 4 | Gemini 2.5 Pro |
| Agent decisions | Claude Sonnet 4 | Gemini 2.5 Flash |
| Agent conversations | Claude Sonnet 4 | Gemini 2.5 Flash |
| Agent reflection | Claude Sonnet 4 | Gemini 2.5 Pro |
| Quick scan | Gemini 2.5 Flash Lite | Claude Haiku 4.5 |
| Narrative | Gemini 2.5 Flash | Claude Haiku 4.5 |

---

## 10. COMPLETE ACTION REFERENCE (33 Actions)

### Action Categories and Routing

```python
ACTION_CATEGORIES = {
    # Military (14)
    "ground_attack", "ground_move", "air_strike", "naval_combat",
    "naval_bombardment", "naval_blockade", "launch_missile_conventional",
    "nuclear_test", "nuclear_launch_initiate", "nuclear_authorize",
    "nuclear_intercept", "basing_rights", "martial_law", "move_units",
    # Economic (4)
    "set_budget", "set_tariffs", "set_sanctions", "set_opec",
    # Diplomatic (8)
    "propose_transaction", "accept_transaction", "propose_agreement",
    "sign_agreement", "public_statement", "call_org_meeting",
    "meet_freely", "declare_war",
    # Covert (2)
    "covert_operation", "intelligence",
    # Political (5)
    "arrest", "assassination", "change_leader", "reassign_types",
    "self_nominate", "cast_vote",
}
```

### Detailed Action Specifications

For each action: action_id, required payload, response format, pre-conditions, DB side effects, events generated.

---

#### `ground_attack` -- WORKING

**Payload:**
```json
{
  "action_type": "ground_attack",
  "role_id": "shield",
  "country_code": "columbia",
  "target_row": 4,
  "target_col": 11,
  "source_global_row": 4,
  "source_global_col": 10,
  "attacker_unit_codes": ["col_g_01", "col_g_02", "col_g_03"],
  "theater": "eastern_ereb",
  "target_theater_row": 4,
  "target_theater_col": 5
}
```

**Pre-conditions:**
- Role has `ground_attack` permission (positions: head_of_state or military)
- Sim in active phase
- Attacker has ground units at source hex
- Target hex within attack range (BFS adjacency, range=1 for ground)
- Must leave 1 unit behind (max = min(3, count-1))

**Response:**
```json
{
  "success": true,
  "narrative": "Ground attack at (4,11): 2 losses each | 1 unit(s) advance to (4,11)",
  "attacker_won": true,
  "exchanges": [...],
  "attacker_losses": ["col_g_02"],
  "defender_losses": ["sar_g_15", "sar_g_16"],
  "moved_forward": ["col_g_01", "col_g_03"],
  "captured": [{"unit_id": "sar_ad_01", "type": "air_defense", "from": "sarmatia"}]
}
```

**DB Side Effects:**
- Destroyed units: `deployments` rows deleted (unit_status = destroyed)
- Surviving attackers: moved to target hex (global_row/col updated)
- Non-ground enemies: captured (country_id changed, status=reserve, position cleared)
- Territory: `hex_control` upserted (controlled_by = attacker)
- Blockade integrity checked after all combat

**Events:** `observatory_events` INSERT with event_type = "ground_attack"

---

#### `air_strike` -- WORKING

**Payload:**
```json
{
  "action_type": "air_strike",
  "role_id": "shield",
  "country_code": "columbia",
  "target_row": 4,
  "target_col": 11,
  "attacker_unit_codes": ["col_ta_01", "col_ta_02"]
}
```

**Pre-conditions:** Role has air_strike permission. Tactical air units at source hex (or embarked on carrier).

**Mechanic:** 12% hit per aircraft (6% if target has AD). 15% downed by AD per aircraft. Once per round per unit.

**DB Side Effects:** Destroyed units deleted from deployments. Downed attackers deleted.

---

#### `naval_combat` -- WORKING

**Payload:**
```json
{
  "action_type": "naval_combat",
  "role_id": "shield",
  "country_code": "columbia",
  "target_row": 5,
  "target_col": 15,
  "attacker_unit_codes": ["col_n_01"]
}
```

**Mechanic:** 1v1 dice (each side rolls, higher wins, ties -> defender). Once per round per unit.

**DB Side Effects:** Losing unit deleted from deployments.

---

#### `naval_bombardment` -- WORKING

**Payload:** Same as naval_combat but targets ground units at hex.

**Mechanic:** 10% hit probability per naval unit. Probability-based (no dice).

---

#### `launch_missile_conventional` -- WORKING

**Payload:**
```json
{
  "action_type": "launch_missile_conventional",
  "role_id": "helmsman",
  "country_code": "cathay",
  "target_row": 6,
  "target_col": 8,
  "attacker_unit_codes": ["cat_sm_01"],
  "target_choice": "military"
}
```

**`target_choice` options:** `military` (destroy unit), `infrastructure` (-2% GDP), `nuclear_site` (halve R&D), `AD` (destroy AD unit)

**Mechanic:** Two-phase: AD intercept 50% per AD unit BEFORE hit roll at 75% flat. Missile always consumed.

**Range:** T1 (nuc 0-1) <= 2 hexes, T2 (nuc 2) <= 4 hexes, T3 (nuc 3+) global

---

#### `ground_move` -- WORKING

**Payload:**
```json
{
  "action_type": "ground_move",
  "role_id": "shield",
  "country_code": "columbia",
  "target_row": 5,
  "target_col": 10,
  "source_global_row": 4,
  "source_global_col": 10,
  "attacker_unit_codes": ["col_g_01"]
}
```

**Pre-conditions:** Authorized by `ground_attack` permission. Adjacent LAND hex. Must leave 1 behind. Sea hexes filtered.

**DB Side Effects:** Unit moved to target hex. Non-ground enemies captured. hex_control upserted.

---

#### `naval_blockade` -- WORKING

**Payload:**
```json
{
  "action_type": "naval_blockade",
  "role_id": "shield",
  "country_code": "columbia",
  "operation": "establish",
  "zone_id": "gulf_gate",
  "level": "full"
}
```

**Operations:** `establish`, `lift`, `reduce`
**Chokepoints:** `gulf_gate`, `caribe_passage`, `cathay_strait`

**Pre-conditions:** Naval units at chokepoint hex (or ground units adjacent for gulf_gate).

**DB Side Effects:** `blockades` table upserted.

---

#### `martial_law` -- WORKING

**Payload:**
```json
{
  "action_type": "martial_law",
  "role_id": "helmsman",
  "country_code": "cathay"
}
```

**Pre-conditions:** Country in eligible list (Sarmatia 10, Cathay 10, Persia 8, Ruthenia 6 military threshold). Not already declared (`martial_law_declared` flag).

**DB Side Effects:** Country stability boost, martial_law_declared = true.

---

#### `move_units` -- WORKING

**Payload:**
```json
{
  "action_type": "move_units",
  "role_id": "shield",
  "country_code": "columbia",
  "movements": [
    {"unit_id": "col_g_05", "action": "deploy", "target_row": 4, "target_col": 8},
    {"unit_id": "col_g_06", "action": "withdraw"},
    {"unit_id": "col_g_07", "action": "reposition", "target_row": 5, "target_col": 9}
  ]
}
```

**Pre-conditions:** Phase = inter_round. Role has move_units permission.

**Movement types:** deploy (reserve -> active), withdraw (active -> reserve), reposition (hex -> hex)

**Auto-embark:** Ground/air deployed to sea hex with carrier auto-embarks.
**Auto-debark:** Embarked unit to land hex auto-debarks.

---

#### `set_budget` -- QUEUED FOR PHASE B

**Payload:**
```json
{
  "action_type": "set_budget",
  "role_id": "dealer",
  "country_code": "columbia",
  "social_spending": 0.20,
  "military_spending": 0.35,
  "technology_spending": 0.15,
  "infrastructure_spending": 0.30
}
```

**DB Side Effects:** Written to `agent_decisions`. Processed by orchestrator in Phase B.

---

#### `set_tariffs` -- QUEUED FOR PHASE B

**Payload:**
```json
{
  "action_type": "set_tariffs",
  "role_id": "dealer",
  "country_code": "columbia",
  "target_country": "cathay",
  "level": 2
}
```

---

#### `set_sanctions` -- QUEUED FOR PHASE B

**Payload:**
```json
{
  "action_type": "set_sanctions",
  "role_id": "dealer",
  "country_code": "columbia",
  "target_country": "cathay",
  "level": -2
}
```

---

#### `set_opec` -- QUEUED FOR PHASE B

**Payload:**
```json
{
  "action_type": "set_opec",
  "role_id": "helmsman",
  "country_code": "solaria",
  "production_level": "increase"
}
```

**Options:** `increase`, `decrease`, `maintain`

---

#### `declare_war` -- WORKING

**Payload:**
```json
{
  "action_type": "declare_war",
  "role_id": "dealer",
  "country_code": "columbia",
  "target_country": "cathay"
}
```

**DB Side Effects:** Both relationship directions set to `at_war`. Observatory event generated.

---

#### `public_statement` -- WORKING

**Payload:**
```json
{
  "action_type": "public_statement",
  "role_id": "dealer",
  "country_code": "columbia",
  "statement": "Columbia stands with Formosa against aggression."
}
```

**DB Side Effects:** Observatory event only (no engine processing).

---

#### `propose_transaction` -- ROUTED

**Payload:**
```json
{
  "action_type": "propose_transaction",
  "role_id": "dealer",
  "country_code": "columbia",
  "counterpart_country": "albion",
  "offer": {"type": "military_units", "units": ["col_g_10"]},
  "request": {"type": "technology", "tech_type": "nuclear", "boost": 0.20},
  "visibility": "secret"
}
```

**DB Side Effects:** `exchange_transactions` row created with status=pending.

---

#### `accept_transaction` -- ROUTED

**Payload:**
```json
{
  "action_type": "accept_transaction",
  "role_id": "broker",
  "country_code": "albion",
  "transaction_id": "uuid",
  "response": "accept"
}
```

**Response options:** `accept`, `reject`, `counter`

---

#### `propose_agreement` -- ROUTED

**Payload:**
```json
{
  "action_type": "propose_agreement",
  "role_id": "dealer",
  "country_code": "columbia",
  "agreement_name": "Mutual Defense Pact",
  "agreement_type": "defense_pact",
  "counterpart_countries": ["albion", "gallia"],
  "terms": "Mutual defense against aggression...",
  "visibility": "public"
}
```

---

#### `sign_agreement` -- ROUTED

**Payload:**
```json
{
  "action_type": "sign_agreement",
  "role_id": "anchor",
  "country_code": "albion",
  "agreement_id": "uuid",
  "confirm": true,
  "comments": "Albion signs this pact."
}
```

---

#### `arrest` -- WORKING (requires confirmation)

**Payload:**
```json
{
  "action_type": "arrest",
  "role_id": "furnace",
  "country_code": "sarmatia",
  "target_role": "ironhand",
  "rationale": "Suspected treason"
}
```

**Pre-conditions:** Initiator is HoS. Target is same country, active.

**DB Side Effects:** Target role status set to "arrested". Observatory event.

---

#### `assassination` -- WORKING (requires confirmation)

**Payload:**
```json
{
  "action_type": "assassination",
  "role_id": "shadow",
  "country_code": "levantia",
  "target_role": "furnace"
}
```

**Mechanic:** 20% base probability (+ country bonuses: Levantia +30%, Sarmatia +10%). Kill -> role removed. Survive -> sympathy stability boost to target country.

**DB Side Effects:** On kill: target role status=dead, stability penalty. On survive: stability boost (sympathy).

---

#### `change_leader` -- WORKING (3-phase)

**Payload (initiation):**
```json
{
  "action_type": "change_leader",
  "role_id": "ironhand",
  "country_code": "sarmatia"
}
```

**Flow:**
1. **Initiate:** Validate stability <= 4.0, initiator is non-HoS, 3+ active roles
2. **Removal vote:** `cast_vote` with election_type="change_leader", strict majority of non-HoS
3. **Election vote:** `cast_vote`, absolute majority of all citizens

**DB Side Effects:** On success: HoS position transferred to winner. `role_actions` recomputed.

---

#### `reassign_types` -- WORKING

**Payload:**
```json
{
  "action_type": "reassign_types",
  "role_id": "dealer",
  "country_code": "columbia",
  "position": "military",
  "target_role_id": "shield"
}
```

**Pre-conditions:** Initiator is HoS. Cannot reassign head_of_state (use change_leader).

**Valid positions:** `military`, `economy`, `diplomat`, `security`, `opposition`

**DB Side Effects:** positions[] array updated on roles. `role_actions` recomputed.

---

#### `self_nominate` -- ROUTED

**Payload:**
```json
{
  "action_type": "self_nominate",
  "role_id": "shadow",
  "country_code": "columbia",
  "election_type": "parliamentary_midterm",
  "election_round": 2
}
```

---

#### `cast_vote` -- ROUTED

**Payload:**
```json
{
  "action_type": "cast_vote",
  "role_id": "dealer",
  "country_code": "columbia",
  "candidate_role_id": "shadow",
  "election_type": "parliamentary_midterm"
}
```

---

#### `covert_operation` -- ROUTED

**Payload:**
```json
{
  "action_type": "covert_operation",
  "role_id": "shadow",
  "country_code": "levantia",
  "op_type": "sabotage",
  "target_country": "sarmatia"
}
```

**Op types:** `espionage`, `sabotage`, `cyber`, `disinformation`, `election_meddling`

---

#### `intelligence` -- ROUTED

**Payload:**
```json
{
  "action_type": "intelligence",
  "role_id": "shadow",
  "country_code": "columbia",
  "question": "What is Cathay's military readiness?"
}
```

**Mechanic:** LLM generates intelligence report based on world state and question.

---

#### `basing_rights` -- ROUTED

**Payload:**
```json
{
  "action_type": "basing_rights",
  "role_id": "dealer",
  "country_code": "columbia",
  "guest_country": "albion",
  "operation": "grant"
}
```

**Operations:** `grant`, `revoke`

---

#### `nuclear_launch_initiate` -- WIRED

**Payload:**
```json
{
  "action_type": "nuclear_launch_initiate",
  "role_id": "dealer",
  "country_code": "columbia",
  "missiles": [{"target_row": 8, "target_col": 15}],
  "rationale": "Retaliatory strike"
}
```

**Flow:** INITIATE -> AUTHORIZE (military officer) -> ALERT + INTERCEPT (target countries) -> RESOLVE

---

#### `nuclear_authorize` -- WIRED (reactive)

**Payload:**
```json
{
  "action_type": "nuclear_authorize",
  "role_id": "shield",
  "country_code": "columbia",
  "nuclear_action_id": "uuid",
  "confirm": true,
  "rationale": "Confirmed"
}
```

---

#### `nuclear_intercept` -- WIRED (reactive)

**Payload:**
```json
{
  "action_type": "nuclear_intercept",
  "role_id": "helmsman",
  "country_code": "cathay",
  "nuclear_action_id": "uuid",
  "intercept": true
}
```

---

#### `nuclear_test` -- NOT WIRED (engine expects Pydantic input)

---

#### `call_org_meeting`, `meet_freely`, `invite_to_meet` -- STUB/BASIC

**Payload (invite_to_meet):**
```json
{
  "action_type": "invite_to_meet",
  "role_id": "dealer",
  "country_code": "columbia",
  "invitation_type": "one_on_one",
  "invitee_role_id": "helmsman",
  "message": "Let's discuss the Formosa situation"
}
```

**DB Side Effects:** `meeting_invitations` row created (expires in 10 minutes). Max 2 active per role.

---

## 11. API ENDPOINT CATALOG

### Health & System

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/health` | None | Infrastructure health (DB, LLM providers) |
| POST | `/api/test/llm` | None | Test LLM connectivity |
| GET | `/api/llm/health` | None | LLM provider health stats |

### Auth & Users

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/api/auth/me` | User | Current user profile |
| GET | `/api/admin/users` | Moderator | List all users |
| POST | `/api/admin/users/{id}/approve` | Moderator | Approve pending moderator |
| POST | `/api/admin/users/{id}/suspend` | Moderator | Suspend user |

### SIM Data (Read)

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/api/sim/{id}/countries` | None | All countries |
| GET | `/api/sim/{id}/country/{cid}` | None | Single country |
| GET | `/api/sim/{id}/roles` | None | Roles (optionally by country) |
| GET | `/api/sim/{id}/zones` | None | Map zones |
| GET | `/api/sim/{id}/deployments` | None | Military deployments |
| GET | `/api/sim/{id}/units/my` | User | Own country units (active/reserve/embarked) |
| GET | `/api/sim/{id}/world` | None | World state (oil, indexes) |
| GET | `/api/sim/{id}/relationships` | None | Bilateral relationships |
| GET | `/api/sim/{id}/sanctions` | None | Active sanctions |
| GET | `/api/sim/{id}/organizations` | None | Organizations + memberships |

### Map

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/api/sim/{id}/map/units` | None | All unit positions for map renderer |
| GET | `/api/sim/{id}/map/hex-control` | None | Occupied hexes for territory overlay |
| GET | `/api/sim/{id}/map/blockades` | None | Active blockades for map rendering |
| GET | `/api/sim/{id}/map/combat-events` | None | Blast marker data |

### SIM Creation & Management

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/api/sim/create` | Moderator | Create SimRun (11-table copy) |
| GET | `/api/sim/{id}/state` | None | Current runtime state (cached 5s) |

### SIM Lifecycle (Moderator)

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/api/sim/{id}/pre-start` | Moderator | setup -> pre_start |
| POST | `/api/sim/{id}/start` | Moderator | pre_start -> active (R1 Phase A) |
| POST | `/api/sim/{id}/phase/end` | Moderator | End phase, advance (triggers Phase B) |
| POST | `/api/sim/{id}/phase/extend` | Moderator | Add minutes to phase |
| POST | `/api/sim/{id}/phase/back` | Moderator | Return to Phase A |
| POST | `/api/sim/{id}/pause` | Moderator | Pause timer |
| POST | `/api/sim/{id}/resume` | Moderator | Resume timer |
| POST | `/api/sim/{id}/end` | Moderator | Graceful end |
| POST | `/api/sim/{id}/abort` | Moderator | Emergency stop |
| POST | `/api/sim/{id}/restart` | Moderator | Full cleanup |
| POST | `/api/sim/{id}/rollback` | Moderator | Rollback to round N |
| POST | `/api/sim/{id}/mode` | Moderator | Toggle auto_approve/auto_attack/dice_mode |

### Actions

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/api/sim/{id}/action` | User | Submit action (validated, dispatched or queued) |
| GET | `/api/sim/{id}/pending` | User | List pending actions |
| POST | `/api/sim/{id}/pending/{id}/confirm` | Moderator | Approve pending action (with optional dice) |
| POST | `/api/sim/{id}/pending/{id}/reject` | Moderator | Reject pending action |

### Attack Targeting

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/api/sim/{id}/attack/valid-targets` | User | Valid targets for a unit (BFS + range) |
| GET | `/api/sim/{id}/attack/preview` | User | Combat preview (modifiers + probability) |
| GET | `/api/sim/{id}/blockades` | User | Blockade status + chokepoint capabilities |

### AI

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/api/sim/{id}/ai/trigger` | Moderator | Trigger AI agents to submit decisions |

---

## 12. FRONTEND COMPONENT MAP

### Pages (15 files, 13,902 lines total)

| Page | Lines | Route | Purpose |
|------|-------|-------|---------|
| `ParticipantDashboard.tsx` | 7,108 | `/sim/{id}` | Human participant view (actions, world, map, artefacts) |
| `FacilitatorDashboard.tsx` | 2,160 | `/sim/{id}/facilitator` | Moderator cockpit (events, pending, controls) |
| `SimRunWizard.tsx` | 1,572 | `/admin/simrun/new`, `/admin/simrun/{id}` | Create/edit SimRun (5-step wizard) |
| `PublicScreen.tsx` | 936 | `/sim/{id}/public` | Room projection (map, indices, ticker) |
| `UserManagement.tsx` | 535 | `/admin/users` | User admin table |
| `Register.tsx` | 289 | `/register` | Registration with role selection |
| `ModeratorDashboard.tsx` | 267 | `/admin` | Quick actions + My Simulations |
| `AISetup.tsx` | 246 | `/admin/ai-setup` | Global LLM model selection |
| `TemplateList.tsx` | 204 | `/admin/templates` | Template management |
| `Login.tsx` | 160 | `/login` | Email + Google login |
| `TemplateEditor.tsx` | 159 | `/admin/template/{id}` | Tabbed template workspace |
| `ResetPassword.tsx` | 101 | `/reset-password` | Password reset |
| `UpdatePassword.tsx` | 101 | `/update-password` | Password update |
| `PendingApproval.tsx` | 42 | `/pending-approval` | Moderator approval waiting |
| `Dashboard.tsx` | 22 | `/dashboard` | Redirect to correct dashboard |

### Shared Components

| Component | Purpose |
|-----------|---------|
| `Header.tsx` | User name + role badge + sign out, clickable logo |
| `ProtectedRoute.tsx` | Route guard (auth + role check) |
| `DataConsentModal.tsx` | GDPR consent modal |
| `ArtefactRenderer.tsx` | Classified document rendering (3 types) |
| `template/*` | Template editor sub-components |

### Libraries

| File | Purpose |
|------|---------|
| `lib/supabase.ts` | Supabase client initialization |
| `lib/queries.ts` | Data layer (all Supabase queries, createSimRun, etc.) |
| `lib/action_constants.ts` | Action category definitions and descriptions |
| `lib/channelManager.ts` | Supabase Realtime channel management |
| `hooks/useRealtimeTable.ts` | Zero-polling realtime table subscription hook |
| `contexts/AuthContext.tsx` | Auth state management (session, user) |

---

## 13. CONFIGURATION REFERENCE

### Map Configuration (`config/map_config.py`)

```python
GLOBAL_ROWS = 10
GLOBAL_COLS = 20
THEATERS = {
    "eastern_ereb": {"rows": 10, "cols": 10},
    "mashriq": {"rows": 10, "cols": 10},
}
COUNTRY_CODES = [20 countries, alphabetical from "albion" to "yamato"]

ATTACK_RANGE = {
    "ground": 1, "naval": 1, "tactical_air": 3,
    "strategic_missile": varies_by_nuc_tier, "air_defense": 0,
}

CHOKEPOINTS = {
    "gulf_gate": {"hex": (row, col), "name": "...", "ground_ok": True},
    "caribe_passage": {"hex": (row, col), "name": "...", "ground_ok": False},
    "cathay_strait": {"hex": (row, col), "name": "...", "ground_ok": False},
}

GLOBAL_HEX_OWNERS = {(row, col): "country_code", ...}  # 64 land hexes
GLOBAL_SEA_HEXES = frozenset({...})  # sea hex coordinates
THEATER_SEA_HEXES = {"eastern_ereb": frozenset({...}), "mashriq": frozenset({...})}
```

### Position-Based Actions (`config/position_actions.py`)

**Universal actions (all roles):** `public_statement`, `invite_to_meet`, `change_leader`

**Position actions:**

| Position | Actions |
|----------|---------|
| head_of_state | declare_war, arrest, reassign_types, martial_law, basing_rights, set_budget, set_tariffs, set_sanctions, all combat, move_units, propose_transaction, propose_agreement + dynamic: set_opec (OPEC), nuclear_test (nuc>=1), nuclear_launch (confirmed) |
| military | all combat, move_units, basing_rights |
| economy | set_budget, set_tariffs, set_sanctions, propose_transaction + dynamic: set_opec |
| diplomat | propose_agreement, propose_transaction, basing_rights |
| security | covert_operation, intelligence, arrest, assassination |
| opposition | (universal only) |

**Dynamic conditions:** set_opec (OPEC member), nuclear_test (nuclear_level >= 1), nuclear_launch (nuclear_confirmed)

### Environment Variables (.env)

```
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_AI_API_KEY=AIza...
APP_ENV=development
LOG_LEVEL=INFO
```

---

## 14. KNOWN LIMITATIONS & STUBS

### Not Yet Built (by module)

| Item | Status | When |
|------|--------|------|
| **M5 AI Participant** | STUB -- default decisions only (budget, public_statement, OPEC) | Sprint 5 |
| **M7 Navigator** | NOT STARTED -- personal AI assistant for participants | Sprint 5-6 |
| **M10 Final Assembly** | NOT STARTED -- integration testing, production deployment | Sprint 6 |

### Stubs and Partial Implementations

| Action/Feature | Status | Gap |
|----------------|--------|-----|
| `nuclear_test` | NOT WIRED | Engine expects Pydantic model, dispatcher passes kwargs |
| `call_org_meeting` | BASIC | Creates meeting invitation, no org logic |
| `meet_freely` | BASIC | Creates meeting invitation only |
| `propose_transaction` | ROUTED | Engine works, needs real payload testing |
| `propose_agreement` | ROUTED | Engine works, needs testing |
| Public Screen doomsday indices | PLACEHOLDER | Hardcoded values, needs LLM calculation |
| Formula parameters UI | READ-ONLY | Display only in template editor, not editable |
| Chain attack (ground) | NOT IMPLEMENTED | Single exchange only |
| Air sortie mechanics | NOT IMPLEMENTED | Simplified hit probability |
| Per-round unit snapshots | NOT IMPLEMENTED | `unit_states_per_round` table exists but unused |
| Information scoping / fog of war | NOT IMPLEMENTED | All data available, frontend filters |
| Multi-session support | NOT IMPLEMENTED | Single continuous session only |
| Voice integration | NOT IMPLEMENTED | ElevenLabs key in settings but unused |
| Court/tribunal mechanics | NOT IMPLEMENTED | Postponed |

### Architectural Debt

| Item | Description |
|------|-------------|
| DB calls in dispatcher | `action_dispatcher.py` makes DB calls directly (should be services only) |
| Engine param signatures | 9 military engine functions have param signature mismatches with v2 refactor |
| Formula coefficients | Hardcoded in Python, not yet configurable per template |
| Scenario level retired | `sim_scenarios` table still in DB, `scenario_id` FK nullable/unused |

### Test Coverage

| Layer | Count | Coverage |
|-------|-------|----------|
| L1 (formula unit tests) | 720+ | All economic, political, technology formulas |
| L2 (integration) | 18+ movement tests + module acceptance | Core flows |
| L3 (AI simulation) | Skill deployment tests | Basic coverage |

---

*End of Comprehensive Build Documentation*
