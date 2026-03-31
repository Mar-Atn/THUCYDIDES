# DET_NAMING_CONVENTIONS.md
## Canonical Naming Dictionary -- Single Source of Truth
**Version:** 1.0 | **Date:** 2026-03-30 | **Status:** ACTIVE
**Purpose:** Every field name, type enum, and identifier format used across B1, C1, C3, and F5 is defined HERE. When documents disagree, this file wins.

**Referenced by:** DET_B1_DATABASE_SCHEMA.sql, DET_C1_SYSTEM_CONTRACTS.md, DET_C3_API_SPEC.yaml, DET_F5_ENGINE_API.md, DET_EDGE_FUNCTIONS.md

---

## 1.1 Field Names (canonical, snake_case everywhere)

These are the ONE correct name for each concept. All documents, database columns, API fields, and engine parameters must use these names. Where a legacy name exists, the Edge Function translation layer handles the mapping.

| Concept | Canonical Name | Used In | Notes |
|---------|---------------|---------|-------|
| Simulation instance | `sim_run_id` | B1 column, C1 envelope, F5 request, JWT claim | JWT claim is `sim_run_id` (not `sim_id`). C3 path uses `sim_run_id`. |
| Round number | `round_num` | B1 column, C1 envelope, C3 fields, F5 request/response | B1 uses `round_num` as column. API path parameter is `round_num`. Event envelope uses `round_num`. |
| Role identifier | `role_id` | B1 `roles.id`, C3 path param, F5 AI endpoints | For event context, use `actor_role_id`. For targets, use `target_role_id`. |
| Event actor role | `actor_role_id` | C1 event envelope, F5 action request | B1 `events.actor` column stores this value. Edge Function maps `actor` <-> `actor_role_id`. |
| Event actor country | `actor_country_id` | C1 event envelope, F5 action request | B1 `events.country_context` column stores this value. Edge Function maps `country_context` <-> `actor_country_id`. |
| Country identifier | `country_id` | B1 most tables, C3 path param, F5 request | See Section 1.1.1 for directional column names. |
| Target zone | `target_zone` | C3, F5 | Not `target.zone`. Flat field in API requests. |
| Origin zone | `from_zone` | C3, F5 | Not `origin_zone`. |

### 1.1.1 Directional Country References in B1

Where two countries are involved, use these canonical paired names:

| Context | Column 1 | Column 2 | Used In |
|---------|----------|----------|---------|
| Sanctions | `imposer_country_id` | `target_country_id` | `sanctions` table |
| Tariffs | `imposer_country_id` | `target_country_id` | `tariffs` table |
| Relationships | `from_country_id` | `to_country_id` | `relationships` table |
| Transactions | `from_country_id` | `to_country_id` | `transactions` table |
| Combat | `attacker_country_id` | `defender_country_id` | `combat_results` table |

**Rule:** Always suffix with `_id` when referring to a country identifier. Never use bare `country`, `imposer`, or `target` alone as a column that holds a country_id value.

### 1.1.2 Visibility Values

| Canonical Value | Case | Used In |
|----------------|------|---------|
| `public` | lowercase | B1 CHECK constraint, database storage |
| `country` | lowercase | B1 CHECK constraint, database storage |
| `role` | lowercase | B1 CHECK constraint, database storage |
| `moderator` | lowercase | B1 CHECK constraint, database storage |

C1 documentation uses UPPERCASE (`PUBLIC`, `COUNTRY`, `ROLE`, `MODERATOR`) for readability. The Edge Function normalizes to lowercase before DB write.

---

---

## 0. DEPLOYMENT RULES (Canonical)

Deployment happens once per round during Phase B. No transit delays — each round represents 6 months of world time.

### Ground Units
- Deploy to: own territory, controlled territory, allied territory (basing agreement)
- No limit per hex. No adjacency requirement. (Adjacency only matters for ATTACKING.)
- Can embark on own-country ships: **1 ground unit per ship**

### Naval Units
- Deploy to: **ANY water hex** on the global ocean
- Multiple nations' ships can coexist on the same water hex
- **CANNOT deploy into an actively blockaded area**
- If entering a zone with a detailed theater map (e.g., Eastern Ereb), must deploy to a specific theater hex

### Tactical Air / Missiles
- Deploy to: any ground hex (same rules as ground units)
- Can embark on own-country ships: **up to 2 air units per ship**

### Air Defense
- Deploy to: any ground hex (same rules as ground units)
- Global map level only — covers the entire hex area

### Strategic Missiles
- Deploy to: any ground hex (same rules as ground units)
- **Cannot embark on ships**

### Ship Capacity
- **1 ground unit + up to 2 tactical air units** per ship (own-country ships only)

### Enforcement
These rules are **mechanically enforced** by the deployment validation function. Checks:
1. Territory ownership / control / basing agreement (ground, air, AD, strategic)
2. Blockade status (naval — cannot enter blockaded area)
3. Ship capacity (1 ground + 2 air max per ship, own ships only)
4. Strategic missiles cannot embark on ships
5. Theater-level placement if entering a theater zone

The facilitator has override authority but should not need it. No adjacency check. No transit delay.

---

## 1.2 Transaction Types (canonical enum)

Source of truth: `transaction_engine.py` TRANSACTION_TYPES dict + extensions for personal/political.

| Canonical Type | Description | Exclusive? | Engine Class | C1 Event |
|---------------|-------------|:----------:|-------------|----------|
| `coin_transfer` | Country-to-country treasury transfer | Yes | `TransactionEngine` | `action.transaction_propose` / `action.transaction_confirm` |
| `arms_transfer` | Military unit transfer (1-round reduced effectiveness) | Yes | `TransactionEngine` | `action.transaction_propose` / `action.transaction_confirm` |
| `tech_transfer` | Technology sharing (replicable: receiver gains, sender keeps) | No | `TransactionEngine` | `action.transaction_propose` / `action.transaction_confirm` |
| `basing_rights` | Military basing access (revocable by host) | No | `TransactionEngine` | `action.transaction_propose` / `action.transaction_confirm` |
| `treaty` | Recorded text agreement (not mechanically enforced) | No | `TransactionEngine` | `action.transaction_propose` / `action.transaction_confirm` |
| `agreement` | Mechanically binding agreement (subtypes: ceasefire, peace, trade, alliance) | No | `TransactionEngine` | `action.agreement_sign` |
| `org_creation` | Create new international organization | No | `TransactionEngine` | `action.organization_create` |
| `personal_investment` | Personal coins into country R&D | Yes | `TransactionEngine` | `action.transaction_propose` / `action.transaction_confirm` |
| `bribe` | Role-to-role covert payment | Yes | `TransactionEngine` | `action.transaction_propose` / `action.transaction_confirm` |

### Deprecated names (do NOT use)

| Old Name | Canonical Replacement | Where It Was |
|----------|----------------------|-------------|
| `transfer_coins` | `coin_transfer` | C3 v1.0, B1 v1.0 |
| `trade_deal` | Use `coin_transfer`, `arms_transfer`, or `tech_transfer` as appropriate | C3 v1.0 |
| `aid_package` | Use `coin_transfer` with conditions field | C3 v1.0 |
| `personal_invest` | `personal_investment` | C3 v1.0 |
| `organization_create` | `org_creation` | F5 v1.0 |

---

## 1.3 Action Types (canonical enum, 31 types)

Source of truth: SEED_G_WEB_APP_SPEC_v1.md (31 actions). Each action has:
- A canonical `action_type` string (used in F5 engine requests)
- A canonical `event_type` string (used in C1 events, dot-separated)
- The API endpoint it routes through
- The engine method it maps to

| # | G Spec Action | Canonical `action_type` | Canonical `event_type` | C3 Endpoint | F5 Route | Engine Method |
|---|--------------|------------------------|----------------------|-------------|----------|---------------|
| 1 | Budget allocation | `budget_submit` | `action.budget_submit` | `POST /actions/{round_num}/{country_id}` | `POST /engine/round/process` (batch) | `WorldModelEngine.process_round()` |
| 2 | Oil production | `opec_production_set` | `action.opec_production_set` | `POST /actions/{round_num}/{country_id}` | `POST /engine/round/process` (batch) | `WorldModelEngine.process_round()` |
| 3 | Tariff settings | `tariff_set` | `action.tariff_set` | `POST /actions/{round_num}/{country_id}` | `POST /engine/round/process` (batch) | `WorldModelEngine.process_round()` |
| 4 | Sanctions | `sanction_set` | `action.sanction_set` | `POST /actions/{round_num}/{country_id}` | `POST /engine/round/process` (batch) | `WorldModelEngine.process_round()` |
| 5 | Mobilization | `mobilization_order` | `action.mobilization_order` | `POST /actions/{round_num}/{country_id}` | `POST /engine/action` | `LiveActionEngine.resolve_mobilization()` |
| 6 | Militia call | `militia_call` | `action.militia_call` | `POST /actions/{round_num}/{country_id}` | `POST /engine/action` | `LiveActionEngine.resolve_militia()` |
| 7 | Ground attack | `ground_attack` | `action.ground_attack` | `POST /actions/{round_num}/{country_id}` | `POST /engine/action` | `LiveActionEngine.resolve_attack()` |
| 8 | Blockade | `blockade` | `action.blockade` | `POST /actions/{round_num}/{country_id}` | `POST /engine/action` | `LiveActionEngine.resolve_blockade()` |
| 9 | Naval combat | `naval_combat` | `action.naval_combat` | `POST /actions/{round_num}/{country_id}` | `POST /engine/action` | `LiveActionEngine.resolve_naval_combat()` |
| 10 | Naval bombardment | `naval_bombardment` | `action.naval_bombardment` | `POST /actions/{round_num}/{country_id}` | `POST /engine/action` | `LiveActionEngine.resolve_naval_bombardment()` |
| 11 | Air strike | `air_strike` | `action.air_strike` | `POST /actions/{round_num}/{country_id}` | `POST /engine/action` | `LiveActionEngine.resolve_air_strike()` |
| 12 | Strategic missile | `strategic_missile` | `action.strategic_missile` | `POST /actions/{round_num}/{country_id}` | `POST /engine/action` | `LiveActionEngine.resolve_missile_strike()` |
| 13 | Troop deployment | `troop_deployment` | `action.troop_deployment` | `POST /deploy/{round_num}/{country_id}` | `POST /engine/deploy` | `deployment_validation()` DB function + direct write |
| 14 | Intelligence | `intelligence_request` | `action.intelligence_request` | `POST /actions/{round_num}/{country_id}` | `POST /engine/action` | `LiveActionEngine.resolve_covert_op()` |
| 15 | Sabotage | `sabotage` | `action.sabotage` | `POST /actions/{round_num}/{country_id}` | `POST /engine/action` | `LiveActionEngine.resolve_covert_op()` |
| 16 | Cyber attack | `cyber_attack` | `action.cyber_attack` | `POST /actions/{round_num}/{country_id}` | `POST /engine/action` | `LiveActionEngine.resolve_covert_op()` |
| 17 | Disinformation | `disinformation` | `action.disinformation` | `POST /actions/{round_num}/{country_id}` | `POST /engine/action` | `LiveActionEngine.resolve_covert_op()` |
| 18 | Election meddling | `election_meddling` | `action.election_meddling` | `POST /actions/{round_num}/{country_id}` | `POST /engine/action` | `LiveActionEngine.resolve_covert_op()` |
| 19 | Arrest | `arrest` | `action.arrest` | `POST /actions/{round_num}/{country_id}` | `POST /engine/action` | `LiveActionEngine.resolve_arrest()` |
| 20 | Fire/reassign | `fire_role` | `action.fire_role` | `POST /actions/{round_num}/{country_id}` | `POST /engine/action` | `LiveActionEngine.resolve_fire()` |
| 21 | Propaganda | `propaganda` | `action.propaganda` | `POST /actions/{round_num}/{country_id}` | `POST /engine/action` | `LiveActionEngine.resolve_propaganda()` |
| 22 | Assassination | `assassination` | `action.assassination` | `POST /actions/{round_num}/{country_id}` | `POST /engine/action` | `LiveActionEngine.resolve_assassination()` |
| 23 | Coup attempt | `coup_attempt` | `action.coup_attempt` | `POST /actions/{round_num}/{country_id}` | `POST /engine/action` | `LiveActionEngine.resolve_coup()` |
| 24 | Protest | `protest` | `action.protest` | Engine-generated | Engine-internal | `LiveActionEngine.resolve_protest()` |
| 25 | Impeachment | `impeachment` | `action.impeachment` | `POST /actions/{round_num}/{country_id}` | `POST /engine/action` | `LiveActionEngine.resolve_impeachment()` |
| 26 | Trade/transfer | `transaction_propose` | `action.transaction_propose` | `POST /transactions` | `POST /engine/transaction` | `TransactionEngine.propose_transaction()` |
| 26b | (confirm) | `transaction_confirm` | `action.transaction_confirm` | `POST /transactions/{id}/confirm` | `POST /engine/transaction/{id}/confirm` | `TransactionEngine.confirm_transaction()` |
| 27 | Agreement | `agreement_sign` | `action.agreement_sign` | `POST /transactions` (type: agreement) | `POST /engine/transaction` | `TransactionEngine.propose_transaction()` |
| 28 | New organization | `org_creation` | `action.organization_create` | `POST /transactions` (type: org_creation) | `POST /engine/transaction` | `TransactionEngine.propose_transaction()` |
| 29 | Public statement | `public_statement` | `action.public_statement` | `POST /actions/{round_num}/{country_id}` | No engine processing | Direct event write |
| 30 | Call meeting | `meeting_call` | `action.meeting_call` | `POST /actions/{round_num}/{country_id}` | No engine processing | Direct event write |
| 31 | Election nominate | `election_nominate` | `action.election_nominate` | `POST /actions/{round_num}/{country_id}` | No engine processing | Direct event write |

### F5 action_type to C1 event_type Mapping

This is the formal translation table. The engine server (`server.py`) converts F5 internal `action_type` to the canonical `event_type` when constructing events.

| F5 `action_type` (engine internal) | C1 `event_type` (canonical) |
|------------------------------------|---------------------------|
| `ground_attack` | `action.ground_attack` |
| `blockade` | `action.blockade` |
| `naval_combat` | `action.naval_combat` |
| `naval_bombardment` | `action.naval_bombardment` |
| `air_strike` | `action.air_strike` |
| `strategic_missile` | `action.strategic_missile` |
| `intelligence_request` | `action.intelligence_request` |
| `sabotage` | `action.sabotage` |
| `cyber_attack` | `action.cyber_attack` |
| `disinformation` | `action.disinformation` |
| `election_meddling` | `action.election_meddling` |
| `arrest` | `action.arrest` |
| `fire_role` | `action.fire_role` |
| `propaganda` | `action.propaganda` |
| `assassination` | `action.assassination` |
| `coup_attempt` | `action.coup_attempt` |
| `impeachment` | `action.impeachment` |
| `troop_deployment` | `action.troop_deployment` |

**Note:** F5 v1.0 used short names `attack`, `espionage`, `cyber` which are now replaced with canonical names `ground_attack`, `intelligence_request`, `cyber_attack`. The engine server wrapper handles backward compatibility during migration.

---

## 1.4 Event Type Naming Convention

Format: `{category}.{action}` (dot-separated, lowercase, snake_case)

| Category | Prefix | Examples |
|----------|--------|---------|
| Player actions | `action.` | `action.ground_attack`, `action.budget_submit`, `action.impeachment` |
| Engine outputs | `engine.` | `engine.round_end`, `engine.combat_result`, `engine.election_result` |
| System events | `system.` | `system.phase_change`, `system.player_login`, `system.moderator_override` |
| Communications | `comms.` | `comms.message_sent`, `comms.meeting_started`, `comms.public_broadcast` |
| AI events | `ai.` | `ai.decision_made`, `ai.context_updated`, `ai.argus_conversation` |

Full index: 52 event types. See C1 Section 1.7 for the complete table.

---

## 1.5 Event ID Format

**Decision: ULID** (Universally Unique Lexicographically Sortable Identifier)

| Property | Value |
|----------|-------|
| Format | `evt_` prefix + 26-character ULID (e.g., `evt_01H5K3B2Y4P8R6T0VW1X9Z`) |
| Generation | Application layer (Edge Function or engine server) |
| Time-sortable | Yes (first 10 chars encode millisecond timestamp) |
| Database column | `events.id TEXT PRIMARY KEY` (not UUID) |
| Pagination | Cursor-based using event_id directly (no separate cursor column needed) |

**Rationale:** ULIDs are time-sortable, which is critical for cursor-based pagination of the event log. UUID v4 is random and requires a separate timestamp column + index for ordering. ULID eliminates this overhead.

**Implementation:** Use `ulid` package in Python (`python-ulid`) and `ulid` package in TypeScript (`ulid`). Prefix with `evt_` for type-safety and readability.

---

## 1.6 Table Names

All lowercase, snake_case. Collections are plural. State snapshots use `_state` suffix.

| Table | Type | Description |
|-------|------|-------------|
| `sim_runs` | Collection | SIM instances |
| `users` | Collection | Auth users |
| `facilitators` | Collection | Moderator assignments |
| `countries` | Collection | Country master data |
| `roles` | Collection | Role definitions |
| `zones` | Collection | Map zones |
| `zone_adjacency` | Collection | Zone connections |
| `deployments` | Mutable collection | Unit placements |
| `organizations` | Collection | International orgs |
| `org_memberships` | Collection | Country-org links |
| `relationships` | Mutable collection | Bilateral relationships |
| `sanctions` | Mutable collection | Bilateral sanctions |
| `tariffs` | Mutable collection | Bilateral tariffs |
| `world_state` | Snapshot (per round) | Global state |
| `country_state` | Snapshot (per round per country) | Country state |
| `role_state` | Snapshot (per round per role) | Role state |
| `events` | Immutable log | Event stream |
| `transactions` | Collection | Bilateral transactions |
| `combat_results` | Collection | Combat records |
| `messages` | Collection | In-app messages |
| `meetings` | Collection | Meeting records |
| `ai_contexts` | Collection | AI context snapshots |
| `ai_decisions` | Collection | AI decision log |
| `artefacts` | Collection | Role artefacts |

---

## 1.7 JWT Claims

Claims embedded in Supabase JWT token for authenticated users:

| Claim | Type | Maps To |
|-------|------|---------|
| `sub` | UUID | `users.id` |
| `sim_run_id` | UUID | `sim_runs.id` |
| `role_id` | string | `roles.id` |
| `country_id` | string | `countries.id` (derived from role) |
| `access_level` | enum | `participant`, `moderator`, `spectator`, `admin` |
| `permissions` | string[] | Derived from `roles.powers` -- list of action_types the role can perform |

**Note:** JWT claim names match canonical field names exactly. No translation needed.

---

## 1.8 API Path Parameters

| Parameter | Canonical Name | Type | Example |
|-----------|---------------|------|---------|
| Round number | `round_num` | integer (0-8) | `/actions/3/columbia` |
| Country ID | `country_id` | string | `/actions/3/columbia` |
| Role ID | `role_id` | string | `/role/dealer` |
| Transaction ID | `transaction_id` | string (ULID) | `/transactions/txn_01H5.../confirm` |

---

*This document is the canonical naming reference for the TTT Detailed Design. All other documents defer to it. When adding a new field, type, or identifier to any document, add it here first.*
