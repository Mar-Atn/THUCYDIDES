# M9 — Sim Setup & Configuration SPEC

**Version:** 2.0 | **Date:** 2026-04-16
**Status:** v1 COMPLETE — Phase A + Phase B delivered and tested
**KING source:** `Dashboard.tsx`, `SimulationWizard.tsx`, `EditScenario.tsx`, `ParticipantManagement.tsx`, `UserManagementModal.tsx`, `simulationStore.ts`

---

## 1. What This Module Does

M9 is the moderator's control center before the simulation starts. It answers:
1. **What SIM am I running?** (select or create a SimRun from a template)
2. **Who's playing?** (assign participants to roles)
3. **What's the world like?** (edit templates — countries, roles, maps, economics)

This is the biggest UI module. It has two phases:
- **Phase A:** Dashboard + SimRun creation + User management (enables running a SIM)
- **Phase B:** Template editor (enables designing new SIMs)

---

## 2. Fundamental Convention: Template → SimRun

**ARCHITECTURAL DECISION: Two levels, not three.**

```
TEMPLATE (master SIM design — editable, versioned)
  └── SIM-RUN (one execution — snapshot of template at creation, immutable once started)
```

The `sim_scenarios` table from DET_F is **retired**. All customization that was on "scenario" now lives either on the Template (design-time) or on the SimRun (run-time).

**How it works:**
- A **Template** holds the complete world: countries, roles, organizations, map, deployments, relationships, sanctions, tariffs, schedule defaults, formula coefficients.
- Template data lives in the **default SimRun** (`00000000-0000-0000-0000-000000000001`), which serves as the canonical source for all game data.
- When moderator clicks "Create SimRun", the frontend wizard calls `POST /api/sim/create` which:
  1. Creates the `sim_runs` row with wizard settings (name, schedule, key_events, max_rounds)
  2. Server-side copies **all 11 game tables** from the source sim, re-keying `sim_run_id` (see `engine/services/sim_create.py`)
  3. Applies wizard customizations: role active/inactive status, human/AI flags
  4. Tables copied: countries (20), roles (40), role_actions (713), relationships (380), zones (57), deployments (146), organizations (7), org_memberships (50), sanctions (43), tariffs (14), world_state (1)
- The moderator can then further customize the SimRun via the edit wizard. These changes affect ONLY this run.
- Once the SIM starts, the run is immutable.

**Implementation:** `engine/services/sim_create.py` + `POST /api/sim/create` endpoint in `engine/main.py`. Frontend: `queries.ts:createSimRun()` calls the API. Duplicate also uses the same server-side path.

**Impact on design docs:** DET_F_SCENARIO_CONFIG_SCHEMA.md and DET_B1a_TEMPLATE_TAXONOMY.sql need updating. The "sparse override" model in DET_F is replaced by "full copy + per-run edits."

---

## 3. Phase A — Moderator Dashboard & SimRun Creation

### 3a. Dashboard Layout

**Header bar** (all pages, not just dashboard):
- Left: "Thucydides Trap" title
- Right: user display name + system role badge + "Sign out" link

**Quick Actions** (2×3 grid, like KING):

| Row 1 | Row 2 |
|---|---|
| Create New SIM-Run | Sim Data Analysis |
| Manage Scenario Templates | User Management |
| AI System Setup | *(reserved)* |

**My Simulations** (below quick actions):
- Card per SimRun, ordered by created_at DESC
- Each card shows: name, status (setup/ready/running/completed), created date, participant counts
- Card actions (icon buttons): Edit, Duplicate, Delete
- **Duplicate SimRun:** creates a new SimRun with identical settings (same template, same role config, same schedule). Useful for re-running a simulation with the same setup.
- Click card → opens the SimRun (M4 moderator live view, built later — for now, opens edit mode)

### 3b. Create New SimRun (wizard, 5 steps)

Same wizard is used for editing an existing SimRun ("Save Changes" instead of "Create").

#### Step 1: Select Template
- List available templates (name, version, description, country count, role count)
- Click to select
- Preview panel: key stats from template

#### Step 2: Configure
- **SimRun name** (required, min 3 chars)
- **Logo upload** (optional — PNG/JPG/SVG, max 2MB, stored in Supabase Storage)
- **Description** (optional, free text)

#### Step 3: Countries & Roles
- Full roster loaded from template, grouped by country
- For each country:
  - Toggle ON/OFF (entire country + all its roles)
  - Expand to see roles
- For each role:
  - Toggle ON/OFF individually
  - Set: **Human** or **AI** (radio)
- Summary bar at bottom: "X countries active, Y roles (Z human, W AI)"
- All countries/roles ON by default. Moderator toggles OFF what's not needed.

#### Step 4: Schedule
All values loaded from template defaults, editable per SimRun:

| Setting | Default Source | Editable |
|---|---|---|
| Total number of rounds | Template | Yes |
| Duration of Round 1 (minutes) | Template | Yes |
| Duration of subsequent rounds (minutes) | Template | Yes |
| Break between rounds (minutes) | Template | Yes |
| Duration of introduction (minutes) | Template | Yes |
| Duration of reflection (minutes) | Template | Yes |
| Duration of debriefing (minutes) | Template | Yes |
| **Total net sim play** | *Calculated* | No (display only) |
| **Total event duration** | *Calculated* | No (display only) |

**Key Events** (from template, adjustable):
- Mid-term parliament elections: Round __ (default from template)
- Presidential elections in Columbia: Round __ (default from template)
- Pre-set meetings R1/R2 (from template, e.g., UNSC opening session)

#### Step 5: Review & Create
- Summary of all choices: template, name, active countries/roles, schedule, key events
- "Create SimRun" button → copies template data into run tables → redirects to My Simulations
- For edit mode: "Save Changes" button

### 3c. User Management (full page, not popup)

Route: `/admin/users`

**Table view** of all registered users with columns:
- Display name
- Email
- System role (moderator/participant) — badge
- Status (registered/active/pending/suspended) — badge
- Registration date
- Last login

**Features:**
- Sort by any column (click header)
- Search by name or email
- **Actions per user:**
  - Approve (if pending moderator)
  - Suspend / Reactivate
  - Reset password (sends reset email)
  - Delete (with confirmation)

### 3d. AI System Setup (global AI configuration)

Route: `/admin/ai-setup`

**All settings stored in `sim_config` table with `category='ai'`.** Read by `engine/agents/managed/ai_config.py` at runtime. Apply globally across all sim runs.

**Model Configuration:**

| Setting | DB Key | Default | Description |
|---|---|---|---|
| AI Participants (decisions) | `model_decisions` | `claude-sonnet-4-6` | Strategic decisions, action selection, tool use |
| AI Participants (conversations) | `model_conversations` | `claude-sonnet-4-6` | Bilateral meetings, negotiations |

**Behavior Configuration:**

| Setting | DB Key | Range | Default | Description |
|---|---|---|---|---|
| Assertiveness Dial | `assertiveness` | 1-10 | 5 | 1=cooperative, 5=balanced, 10=competitive. Affects AI system prompt — shifts decision-making tendency. |

**UI:** Model dropdowns + assertiveness slider. Save persists to `sim_config` via upsert.

**Backend integration:** `ai_config.get_ai_model("decisions")` and `ai_config.get_assertiveness()` read these values at session creation time. Falls back to defaults if DB has no entry.

**AI Prompt Management** — placeholder card: "Prompt editor coming in M5."

---

## 4. Phase B — Template Editor

### 4a. Template Management

Route: `/admin/templates`

- List all templates (name, version, status, created date)
- Actions: Edit, Duplicate (creates copy with incremented version), Delete
- "Create New Template" (blank or duplicate existing)

### 4b. Template Editor (tabbed interface)

When editing a template, the moderator sees a tabbed workspace:

#### Tab 1: General
- Template name, version, description
- Status (draft / published)

#### Tab 2: Countries (20 entries)
Expandable list, one row per country. Click to expand full editor:

**Identity:** sim_name, parallel (real-world), regime_type, team_type, team_size_min/max, ai_default

**Economic (per country):**
- GDP, GDP growth base
- Sector split: resources, industry, services, technology (must sum to 100)
- Tax rate, treasury, inflation, trade balance
- Oil: producer (bool), OPEC member (bool), OPEC production level, oil_production_mbpd
- Formosa dependency, debt burden, debt ratio, social baseline
- Sanctions coefficient, tariff coefficient

**Military (per country):**
- Units: ground, naval, tactical air, strategic missiles, air defense
- Production costs: ground, naval, tactical
- Production capacity: ground, naval, tactical
- Maintenance per unit, strategic missile growth, mobilization pool

**Political (per country):**
- Stability (1-10), political support (0-100%)
- Dem/Rep split (parliament seats)
- War tiredness

**Technology (per country):**
- Nuclear level (0-3), nuclear R&D progress
- AI level (0-4), AI R&D progress

**Geography:** home zones (comma-separated zone IDs)

#### Tab 3: Roles (40+ entries)
Expandable list, grouped by country. Click to expand:

**Identity:** character_name, country, team, faction, title, age, gender, public_bio
**Position:** is_head_of_state, is_military_chief, is_diplomat, parliament_seat
**Resources:** personal_coins, personal_coins_notes
**Covert ops deck:** intelligence_pool, sabotage_cards, cyber_cards, disinfo_cards, election_meddling_cards, assassination_cards, protest_stim_cards
**Role definition:** powers[] (multi-select), objectives[] (text list)
*(ticking_clock and fatherland_appeal DEPRECATED 2026-04-17 — scrapped from DB and code)*
**Config:** expansion_role (bool), ai_candidate (bool), brief_file (upload reference)

#### Tab 4: Organizations
List of 8+ organizations. Per org:
- Name (sim_name), parallel, description
- Decision rule (consensus/majority/veto), voting threshold, meeting frequency
- Chair role (dropdown from roles)
- Can be created at runtime (bool)
- **Members table:** country + role_in_org + has_veto (per row)

#### Tab 5: Relationships
**Matrix view** — 20×20 grid (from_country × to_country):
- Cell shows: relationship type (alliance → hostile, color-coded)
- Click cell to edit: relationship, status, basing_rights A→B, basing_rights B→A
- Filter by: relationship type, country

#### Tab 6: Sanctions & Tariffs
Two sub-tabs:

**Sanctions:** Table of imposer → target → level (-3 to +3). Add/remove rows.
**Tariffs:** Table of imposer → target → level (0-3). Add/remove rows.

#### Tab 7: Map & Deployments
**Two panels side by side:**

Left: **Map viewer** (reuse existing hex map component from test-interface)
- Global map (10×20) showing zone ownership, chokepoint markers
- Click zone to edit: display_name, type, owner, controlled_by, theater, is_chokepoint, die_hard
- Theater views (Eastern Ereb 10×10, Mashriq 10×10)

Right: **Deployment editor**
- List of all units (345+), filterable by country, unit_type, zone
- Click unit row to edit: country, unit_type, count, zone assignment
- Add/remove deployments
- Drag-and-drop unit onto map hex (future enhancement — table editing first)
- Unit totals per country displayed

**Zone adjacency** — separate sub-tab:
- Table: zone_a, zone_b, connection_type
- Add/remove adjacency rules

#### Tab 8: Schedule Defaults
These are the template-level defaults that get copied into each SimRun:

| Setting | Value |
|---|---|
| Default number of rounds | 8 |
| Default Round 1 duration (min) | 80 |
| Default subsequent round duration (min) | 60 |
| Default break duration (min) | 15 |
| Default introduction duration (min) | 30 |
| Default reflection duration (min) | 20 |
| Default debriefing duration (min) | 30 |

**Key Events Schedule:**
- Table: event_type, event_name, default_round, country (editable)
- Pre-loaded from template data (elections, UNSC meetings, etc.)

#### Tab 10: Formula Parameters
**Current status: READ-ONLY REFERENCE.** All formula coefficients are currently hardcoded in the Python engine files. A small selection of key parameters is displayed in this tab for moderator visibility. They are NOT yet configurable — editing them here has no effect on engine behavior.

**Displayed parameters (key selection, 12 total):**
- Economic: oil_base_price, gdp_floor, sanctions_floor, money_printing_inflation_multiplier, dollar_credibility_floor
- Political: change_leader_threshold
- Military: assassination stability boosts, nuclear hit probability, missile intercept probability
- Technology: rd_multiplier, rare_earth_penalty_per_level

**Future (M4/engine migration):** All ~150 constants will be moved to `formula_coefficients` JSONB on the template. At SimRun creation, coefficients are copied to `run_config`. The engine fetches all coefficients ONCE at round start into a Python dict — zero DB calls during computation. This enables different templates to have different formula tuning.

---

## 5. Database Changes

### 5a. Template → SimRun wiring

Add to `sim_runs`:
```
template_id     UUID FK → sim_templates    (which template this run was created from)
logo_url        TEXT                        (optional company/event logo)
schedule        JSONB                       (round durations, intro/reflection/debrief)
key_events      JSONB                       (election rounds, pre-set meetings)
```

Add to `sim_templates`:
```
schedule_defaults   JSONB    (default round/intro/reflection/debrief durations)
key_events_defaults JSONB    (default election schedule, pre-set meetings)
```

### 5b. Global LLM config

Use existing `sim_config` table:
```
category = 'llm'
key = 'agent_decision' | 'agent_conversation' | 'moderator' | 'fallback_1' | 'fallback_2'
content = model ID string
```

### 5c. sim_scenarios — retired

Table stays in DB (no destructive migration) but is not used by any new code. `sim_runs.scenario_id` FK becomes nullable and unused.

---

## 6. What This Module Does NOT Do

| Out of Scope | Which Module |
|---|---|
| Running the simulation (round control, phase transitions) | M4 (Sim Runner) |
| Participant's view of the simulation | M6 (Human Interface) |
| Public screen display | M8 |
| AI agent cognitive architecture | M5 |
| AI prompt editing | M5 |
| Print materials generation | Later (after M6) |
| Sim Data Analysis | Later |

**Participant-to-role assignment** lives on the SimRun's moderator dashboard (within M4 facilitator view). The M9 wizard sets which roles are active and human/AI. The actual "John Smith → Dealer" binding happens in the facilitator dashboard before launch.

---

## 7. Acceptance Criteria

### Phase A (Moderator Dashboard + SimRun + Users)
- [ ] Dashboard shows quick actions grid (6 cards) + My Simulations list
- [ ] Header shows user name + role + sign out (all pages)
- [ ] Create SimRun wizard: 5 steps, creates run from template
- [ ] Edit SimRun: same wizard, loads existing data, saves changes
- [ ] Delete SimRun: with confirmation
- [ ] Click SimRun card → opens it (edit mode for now, live view in M4)
- [ ] User management: full page, sortable table, approve/suspend/delete
- [ ] AI Setup: global LLM model selection saved to sim_config
- [ ] All pages follow TTT UX style

### Phase B (Template Editor)
- [ ] Template list: create, duplicate, delete
- [ ] Countries tab: view/edit all 80+ fields per country
- [ ] Roles tab: view/edit all fields per role, grouped by country
- [ ] Organizations tab: edit orgs + membership matrix
- [ ] Relationships tab: matrix view, edit bilateral status
- [ ] Sanctions & Tariffs tab: add/edit/remove rows
- [ ] Map tab: hex map viewer with zone editing + deployment table
- [ ] Schedule tab: default durations + key events
- [ ] Formula parameters tab: all engine constants editable
- [ ] Changes save to template in Supabase

---

## 8. Design Heritage

| Document | What It Provides |
|---|---|
| **DET_F** Scenario Config Schema | Template/Scenario/Run hierarchy (MODIFIED: scenario level removed) |
| **DET_B1a** Template Taxonomy SQL | Table definitions for sim_templates, unit_layouts |
| **DET_B1** Database Schema | countries, roles, zones, deployments, relationships, orgs |
| **CON_G1** Web App Architecture | Facilitator dashboard, scenario configurator concept |
| **SEED_G** Web App Spec | Facilitator workflow, role assignment |
| **SEED_H1** UX Style v2 | Visual design tokens |
| **KING** Sim setup implementation | Dashboard, wizard, participant management, role management |

### Deviations from Design Heritage

1. **Scenario level removed.** DET_F specifies Template → Scenario → Run. We simplify to Template → Run. The "sparse override" model is replaced by "full copy + per-run edits." This is a fundamental convention change that must be reflected in DET_F, DET_B1a, and related docs.

2. **Schedule stored on template.** DET_F doesn't define schedule defaults as template-level data. We add `schedule_defaults` and `key_events_defaults` JSONB columns to `sim_templates`.

3. **Formula coefficients editable via UI.** Currently hardcoded in Python engine files. We move them to `sim_templates.formula_coefficients` JSONB. At SimRun creation, coefficients are copied into `run_config`. At round start, the engine fetches all coefficients ONCE from `run_config` into a Python dict and uses them from memory for the entire run. Zero performance cost during computation.

---

## 9. Resolved Questions (Marat, 2026-04-13)

| # | Question | Decision |
|---|----------|----------|
| Q1 | Participant-to-role assignment | **Lives in SimRun moderator dashboard** (M4 facilitator view). M9 wizard sets active roles + human/AI. User binding happens before launch in facilitator view. |
| Q2 | Template duplication | **Full deep copy** — all countries, roles, orgs, zones, deployments, relationships, sanctions, tariffs, formula coefficients. New template_id. |
| Q3 | Formula coefficients migration | **Now, with load-once pattern.** Store in template JSONB → copy to run_config at SimRun creation → engine fetches once at round start into memory dict → zero DB calls during computation. |
| Q4 | Map editor approach | **Port existing test-interface** hex map into React component. Rewire to save into specific template. Marat will provide UI corrections. |

### Additional decisions:
- **SimRun duplication** added — allows re-running a simulation with identical settings
- **Formula coefficients architecture:** stored in DB (template), copied to run_config (SimRun), loaded once into memory (engine). Different runs can have different formulas. No performance impact.
- **Key events field renamed:** `default_round` → `round` in SimRun context (actual scheduled round, not a default)
- **Bilateral/trilateral meetings:** participants specified at role level (`role_id`, `country_code`, `character_name`), not country level

---

## 10. Key Events Convention (Canonical)

Key events are stored as JSONB arrays on `sim_templates.key_events_defaults` (template) and `sim_runs.key_events` (per-run copy). They are the canonical schedule of elections and mandatory meetings that the Sim Runner (M4) must process.

### Schema

Two event types:

**Elections:**
```json
{
  "type": "election",
  "subtype": "parliamentary_midterm | presidential | wartime",
  "name": "Human-readable name",
  "country_code": "columbia",
  "round": 2,
  "nominations_round": 1
}
```

**Mandatory Meetings — Organization Sessions:**
```json
{
  "type": "mandatory_meeting",
  "subtype": "organization_session",
  "name": "UNSC Session on Persia Crisis",
  "organization": "unsc",
  "round": 1
}
```

**Mandatory Meetings — Bilateral/Trilateral (role-level participants):**
```json
{
  "type": "mandatory_meeting",
  "subtype": "trilateral_negotiation | bilateral",
  "name": "Phrygia Peace Talks",
  "participants": [
    {"role_id": "fixer", "country_code": "columbia", "character_name": "Fixer"},
    {"role_id": "broker", "country_code": "ruthenia", "character_name": "Broker"},
    {"role_id": "compass", "country_code": "sarmatia", "character_name": "Compass"}
  ],
  "note": "Representatives, not Heads of State",
  "round": 1
}
```

### Template v1.0 Canonical Events (updated 2026-04-15)

| Round | Event | Type |
|---|---|---|
| R1 | Ereb Union Session | Organization meeting |
| R1 | The Cartel Meeting | Organization meeting |
| R1 | Global Security Council Session on Persia Crisis | Organization meeting |
| R1 | Columbia Parliament Session | Organization meeting |
| R1 | Phrygia Peace Talks (Shadow, Broker, Compass) | Trilateral negotiation |
| R2 | Columbia Mid-Term Parliamentary Elections (nominations R1) | Election |
| R2 | The New League Meeting | Organization meeting |
| R2 | Western Treaty Session | Organization meeting |
| R6 | Columbia Presidential Election (nominations R5) | Election |

### How the Sim Runner (M4) will use this

When a round starts, the orchestrator queries `key_events WHERE round = current_round`:
- **Election events** → trigger the election engine (create nominations if `nominations_round`, resolve votes if `round`)
- **Organization meetings** → auto-create meeting record, pull members from `org_memberships` table
- **Bilateral/trilateral** → create ad-hoc meeting with the specified `role_id` participants

This is a canonical convention for M4 implementation.

---

## 11. Phase A Delivery Summary (2026-04-13)

### What was built

| Layer | Files | Details |
|---|---|---|
| **Database** | 4 ALTER TABLE + RLS | sim_runs: +template_id, +facilitator_id, +logo_url, +schedule, +key_events, +human/ai_participants. sim_templates: +schedule_defaults, +key_events_defaults. RLS policies for sim_runs, sim_templates, roles, countries, zones, deployments, relationships, orgs, sanctions, world_state, sim_config |
| **Frontend** | 8 new/updated files | ModeratorDashboard (quick actions + my simulations), SimRunWizard (5-step create/edit), UserManagement (full page), AISetup (global LLM), Header (shared, clickable logo), DataConsentModal, queries.ts (data layer) |
| **Assets** | 3 files | favicon.png (32x32), logo-48.png, logo-96.png — from two dragons.png |
| **Infra** | Supabase | Storage bucket "assets", template seeded with schedule defaults + 9 canonical key events, Google OAuth user promoted to moderator |

### Acceptance criteria status

- [x] Dashboard shows quick actions grid (6 cards) + My Simulations list ✅
- [x] Header shows user name + role + sign out, clickable logo → dashboard ✅
- [x] Create SimRun wizard: 5 steps, creates run from template ✅
- [x] Edit SimRun: same wizard, free step navigation, saves changes ✅
- [x] Delete SimRun: with confirmation ✅
- [x] Duplicate SimRun ✅
- [x] **Full data inheritance on create** (2026-04-16): server-side `POST /api/sim/create` copies 11 tables (countries, roles, role_actions, relationships, zones, deployments, organizations, org_memberships, sanctions, tariffs, world_state) with role customizations (active/inactive, human/AI). See `engine/services/sim_create.py`. ✅
- [x] User management: full page, sortable table, approve/suspend/delete ✅
- [x] AI Setup: global LLM model selection ✅
- [x] Countries & Roles: 40 roles, grouped by country, custom sort, HoS/Military/Budget/optional badges ✅
- [x] Schedule: correct calculations, structured key events with role-level participants ✅
- [x] All pages follow TTT UX style ✅

---

## 12. v2 Delivery Summary (2026-04-15)

### Phase B — Template Editor + Simplification

| Deliverable | Status |
|---|---|
| **Template Editor** (10 tabs) | ✅ General, Countries, Roles, Organizations, Relationships, Sanctions/Tariffs, Map, Deployments, Schedule, Formulas |
| **Map Viewer & Editor** | ✅ Geography mode (no units), country painting, chokepoint/diehard/nuclear toggles, color picker, undo/redo, save to template |
| **Deployment Editor** | ✅ Full unit placement via embedded map editor |
| **Role System** | ✅ 5 position types (HoS, Military, Economy, Diplomat, Security) + Opposition. 40 roles, 713 action assignments |
| **Role Briefs** | ✅ 40 public bios + confidential briefs + objectives (Harvard style, gender-neutral, no real-world names) |
| **Country Briefs** | ✅ 20 country descriptions (narrative, no numbers) |
| **Simplification A-E** | ✅ Stability only, no personal coins, 5 relation types, change_leader, Columbia elections |
| **Info Popups** | ✅ Role and country dashboard cards in SimRun wizard |
| **Delete Protection** | ✅ Type name to confirm, canonical template protected |
| **Hex Convention** | ✅ Pointy-top odd-r, formalized in map_config.py, 7 adjacency tests |
| **Map Rendering Contract** | ✅ CONTRACT_MAP_RENDERING.md locked v1.0 |

### L2 Integration Test Results (2026-04-16)

| Check | Result |
|---|---|
| Template exists with data | ✅ TTT Main Template v1.0 |
| Map config (global + 2 theaters) | ✅ 10x20 + 2x(10x10) |
| Schedule + key events | ✅ 6 rounds, 9 events (all SIM names) |
| Countries (20) with briefs + colors | ✅ 20/20 |
| Roles (40) with bios + position types | ✅ 40/40, 6 position types |
| Role actions | ✅ 713 assignments, 32 action types |
| Organizations + memberships + chairs | ✅ 7 orgs, 50 memberships |
| Relationships (5 types) | ✅ 380 total |
| Deployments | ✅ **345 individual units** (1 row per unit, from canonical `units.csv`). Each with `unit_id`, `global_row/col`, `theater/row/col`, `unit_status`. zone_id deprecated for positioning. |
| SimRun creation from template | ✅ Full 11-table copy via `POST /api/sim/create` (20 countries, 40 roles, 713 role_actions, 380 relationships, 57 zones, 345 deployments, 7 orgs, 50 memberships, 43 sanctions, 14 tariffs, 1 world_state) |
| Sanctions + Tariffs | ✅ 43 + 14 |
| Key events naming (no real-world) | ✅ All SIM names |

### Cross-Module Reconciliation (2026-04-15)

- M1 (Engines): deprecated fields marked, agent prompts use stability only, 720 L1 tests pass
- M2 (Communication): 24 action types, 3 new contracts, orphaned validators marked deprecated
- M3 (Data): template JSONB has map + schedule + formulas, country colors in DB
