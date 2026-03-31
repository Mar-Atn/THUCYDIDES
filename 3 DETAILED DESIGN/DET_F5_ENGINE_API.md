# DET_F5_ENGINE_API.md
## TTT Detailed Design -- Engine API Specification
**Version:** 1.1 | **Date:** 2026-03-30 | **Status:** DRAFT
**Owner:** NOVA (Backend) + ATLAS (Engine)
**Cross-references:** [D1 Tech Stack](DET_D1_TECH_STACK.md) | [F4 API Contracts](../2%20SEED/F_DATA_ARCHITECTURE/SEED_F4_API_CONTRACTS_v1.md) | [D Engine Interface](../2%20SEED/D_ENGINES/SEED_D_ENGINE_INTERFACE_v1.md) | [D8 Engine Formulas](../2%20SEED/D_ENGINES/SEED_D8_ENGINE_FORMULAS_v1.md) | [Naming Conventions](DET_NAMING_CONVENTIONS.md) | [Edge Functions](DET_EDGE_FUNCTIONS.md)

---

# PURPOSE

This document specifies the REST API that wraps the Python engine server. It is the bridge between the web application (React frontend + Supabase Edge Functions) and the simulation engines (Python).

The web app never calls engine Python code directly. All engine operations go through these HTTP endpoints, hosted on Railway as a FastAPI server.

---

# 1. ARCHITECTURE

## 1.1 Request Flow

```
Participant Browser (React)
        |
        | HTTPS (Supabase client SDK)
        v
Supabase Edge Function (Deno/TypeScript)
        |
        | 1. Validates JWT + extracts claims (sim_id, role_id, country_id, access_level)
        | 2. Checks role permissions against requested action
        | 3. Forwards to engine server with internal auth token
        |
        | HTTPS (internal)
        v
Python Engine Server (FastAPI on Railway)
        |
        | 1. Validates internal auth token
        | 2. Loads or retrieves WorldState
        | 3. Calls appropriate engine function
        | 4. Returns result
        |
        | HTTPS (Supabase REST API)
        v
Supabase PostgreSQL
        |
        | Writes state changes + events
        | Realtime pushes to subscribers
```

## 1.2 Authentication

**External authentication** (participant to Supabase) is handled by Supabase Auth (JWT). The Edge Function validates the JWT and extracts claims.

**Internal authentication** (Edge Function to engine server) uses a shared secret:

```
Header: X-Engine-Auth: <HMAC-SHA256 signature of request body using shared secret>
Header: X-Engine-Timestamp: <Unix timestamp>
Header: X-Request-Id: <UUID for tracing>
```

The engine server validates that:
1. Timestamp is within 60 seconds of server time (prevents replay).
2. HMAC signature matches.
3. Request ID is unique (idempotency check against in-memory set, cleared hourly).

## 1.3 Base URL

```
Production: https://ttt-engine.railway.app/api/v1
Development: http://localhost:8000/api/v1
```

## 1.4 Common Response Envelope

All responses follow this structure:

```json
{
  "success": true,
  "data": { ... },
  "events": [ ... ],
  "state_changes": [ ... ],
  "warnings": [ ... ],
  "request_id": "req_abc123",
  "timestamp": "2026-04-15T14:23:07Z"
}
```

Error responses:

```json
{
  "success": false,
  "error": {
    "code": "RESOURCE_INSUFFICIENT_TREASURY",
    "message": "Treasury balance (3.2) insufficient for requested spending (8.5)",
    "details": { "treasury": 3.2, "requested": 8.5 }
  },
  "request_id": "req_abc123",
  "timestamp": "2026-04-15T14:23:07Z"
}
```

Error codes follow the categories defined in F4 API Contracts Section 1.3.

---

# 2. ENDPOINTS

## 2.1 POST /engine/action -- Submit Live Action

Processes a single real-time action (combat, blockade, covert op, political action) through the Live Action Engine.

### Request

```json
{
  "sim_run_id": "sim_2026_04_15",
  "round_num": 3,
  "action_type": "attack",
  "actor_role_id": "dealer",
  "actor_country_id": "columbia",
  "target": {
    "zone": "persia_west",
    "from_zone": "levantia_border"
  },
  "parameters": {
    "units": {
      "ground": 4,
      "tactical_air": 3
    }
  },
  "idempotency_key": "act_r3_dealer_attack_persia_west_v1"
}
```

### Request Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sim_run_id` | string | Yes | Simulation run identifier |
| `round_num` | int | Yes | Current round number (1-8) |
| `action_type` | string | Yes | One of the action types below |
| `actor_role_id` | string | Yes | Role performing the action |
| `actor_country_id` | string | Yes | Country of the acting role |
| `target` | object | Yes | Action-specific target (varies by type) |
| `parameters` | object | Yes | Action-specific parameters (varies by type) |
| `idempotency_key` | string | Yes | Unique key for deduplication |

### Supported Action Types

All action_type values use canonical names per [DET_NAMING_CONVENTIONS.md](DET_NAMING_CONVENTIONS.md) Section 1.3.

| Action Type | Target | Parameters | Engine Method | C1 Event Type |
|-------------|--------|------------|---------------|---------------|
| `ground_attack` | `{zone, from_zone}` | `{units: {ground, naval, tactical_air}}` | `LiveActionEngine.resolve_attack()` | `action.ground_attack` |
| `blockade` | `{zone}` | `{level: "partial"\|"full", naval_units: int}` | `LiveActionEngine.resolve_blockade()` | `action.blockade` |
| `naval_combat` | `{zone}` | `{ships: int, target_country: str}` | `LiveActionEngine.resolve_naval_combat()` | `action.naval_combat` |
| `naval_bombardment` | `{zone}` | `{ships: int}` | `LiveActionEngine.resolve_naval_bombardment()` | `action.naval_bombardment` |
| `air_strike` | `{zone}` | `{tactical_air: int}` | `LiveActionEngine.resolve_air_strike()` | `action.air_strike` |
| `strategic_missile` | `{zone}` | `{missiles: int, nuclear: bool}` | `LiveActionEngine.resolve_missile_strike()` | `action.strategic_missile` |
| `intelligence_request` | `{target_country}` | `{question: str}` | `LiveActionEngine.resolve_covert_op()` | `action.intelligence_request` |
| `sabotage` | `{target_country}` | `{target_type: str}` | `LiveActionEngine.resolve_covert_op()` | `action.sabotage` |
| `cyber_attack` | `{target_country}` | `{target_type: str}` | `LiveActionEngine.resolve_covert_op()` | `action.cyber_attack` |
| `disinformation` | `{target_country}` | `{narrative: str}` | `LiveActionEngine.resolve_covert_op()` | `action.disinformation` |
| `election_meddling` | `{target_country}` | `{direction: str}` | `LiveActionEngine.resolve_covert_op()` | `action.election_meddling` |
| `arrest` | `{target_role_id}` | `{}` | `LiveActionEngine.resolve_arrest()` | `action.arrest` |
| `fire_role` | `{target_role_id}` | `{replacement_role_id: str\|null}` | `LiveActionEngine.resolve_fire()` | `action.fire_role` |
| `propaganda` | `{}` | `{coins_spent: float}` | `LiveActionEngine.resolve_propaganda()` | `action.propaganda` |
| `assassination` | `{target_role_id}` | `{}` | `LiveActionEngine.resolve_assassination()` | `action.assassination` |
| `coup_attempt` | `{}` | `{conspirators: [role_id, role_id]}` | `LiveActionEngine.resolve_coup()` | `action.coup_attempt` |
| `impeachment` | `{target_role_id}` | `{parliament_votes: {for: int, against: int}}` | `LiveActionEngine.resolve_impeachment()` | `action.impeachment` |
| `mobilization_order` | `{}` | `{units: int, deploy_to_zone: str}` | `LiveActionEngine.resolve_mobilization()` | `action.mobilization_order` |
| `militia_call` | `{}` | `{units: int, deploy_to_zone: str}` | `LiveActionEngine.resolve_militia()` | `action.militia_call` |

**Deprecated action_type names** (do not use): `attack` (use `ground_attack`), `espionage` (use `intelligence_request`), `cyber` (use `cyber_attack`).

### Response (200)

```json
{
  "success": true,
  "data": {
    "outcome": "attacker_wins",
    "attacker_losses": { "ground": 1 },
    "defender_losses": { "ground": 3 },
    "zone_control_change": {
      "zone": "persia_west",
      "old_owner": "persia",
      "new_owner": "columbia"
    },
    "narrative": "Columbia forces crossed from Levantia into western Persia. After fierce resistance, Persian defenders were overwhelmed. Columbia now controls the zone."
  },
  "events": [
    {
      "id": "evt_auto_001",
      "round_num": 3,
      "phase": "A",
      "action_type": "attack",
      "actor_role_id": "dealer",
      "target": "persia_west",
      "details": {
        "units_committed": { "ground": 4, "tactical_air": 3 },
        "outcome": "attacker_wins"
      },
      "visibility": "public"
    },
    {
      "id": "evt_auto_002",
      "round_num": 3,
      "phase": "A",
      "action_type": "combat_losses",
      "actor_role_id": "engine",
      "details": {
        "columbia": { "ground": -1 },
        "persia": { "ground": -3 }
      },
      "visibility": "public"
    }
  ],
  "state_changes": [
    { "path": "countries.columbia.military.ground", "old": 22, "new": 21 },
    { "path": "countries.persia.military.ground", "old": 15, "new": 12 },
    { "path": "zones.persia_west.owner", "old": "persia", "new": "columbia" },
    { "path": "countries.columbia.political.war_tiredness", "old": 0, "new": 0.5 },
    { "path": "countries.persia.political.war_tiredness", "old": 0, "new": 1.0 }
  ],
  "warnings": [],
  "request_id": "req_abc123",
  "timestamp": "2026-04-15T14:23:07Z"
}
```

### Error Responses

| HTTP | Code | When |
|------|------|------|
| 400 | `VALIDATION_INVALID_ACTION_TYPE` | Unrecognized action type |
| 400 | `VALIDATION_MISSING_FIELD` | Required field missing in target or parameters |
| 403 | `AUTH_ROLE_MISMATCH` | Actor role does not have permission for this action type |
| 409 | `STATE_ROUND_FROZEN` | Attempting action on a non-current round |
| 409 | `STATE_ACTION_ALREADY_SUBMITTED` | Idempotency key already processed |
| 422 | `RESOURCE_NO_UNITS` | Insufficient units in from_zone |
| 422 | `RESOURCE_ZONES_NOT_ADJACENT` | from_zone and target zone not adjacent |
| 422 | `RESOURCE_COVERT_OPS_EXHAUSTED` | Max covert ops per round reached |
| 500 | `ENGINE_PROCESSING_FAILED` | Unexpected engine error |

### Notes

- **Idempotency:** If a request with the same `idempotency_key` is received again, the server returns the cached result from the first call (HTTP 200) without re-processing.
- **Rate limit:** 10 requests/minute per role (matches F4 Section 9.3).
- **Latency target:** < 2 seconds including network round-trip.
- **Internal call:** Instantiates `LiveActionEngine(world_state)` and calls the appropriate `resolve_*()` method. State changes are applied to the in-memory WorldState and persisted to Supabase.

---

## 2.2 POST /engine/transaction -- Propose Transaction

Creates a new bilateral transaction proposal through the Transaction Engine.

### Request

```json
{
  "sim_run_id": "sim_2026_04_15",
  "round_num": 3,
  "proposer_role_id": "dealer",
  "proposer_country_id": "columbia",
  "receiver_role_id": "helmsman",
  "receiver_country_id": "cathay",
  "transaction_type": "coin_transfer",
  "terms": {
    "amount": 10.0,
    "from_country": "columbia",
    "to_country": "cathay",
    "conditions": "In exchange for lifting rare earth restrictions on Columbia"
  },
  "idempotency_key": "txn_r3_dealer_helmsman_coins_v1"
}
```

### Request Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sim_run_id` | string | Yes | Simulation run identifier |
| `round_num` | int | Yes | Current round |
| `proposer_role_id` | string | Yes | Role proposing the transaction |
| `proposer_country_id` | string | Yes | Proposer's country |
| `receiver_role_id` | string | Yes | Counterparty role |
| `receiver_country_id` | string | Yes | Counterparty's country |
| `transaction_type` | string | Yes | See supported types below |
| `terms` | object | Yes | Type-specific terms |
| `idempotency_key` | string | Yes | Unique key |

### Supported Transaction Types

All transaction types use canonical names per [DET_NAMING_CONVENTIONS.md](DET_NAMING_CONVENTIONS.md) Section 1.2.

| Type | Terms | Engine Behavior | C1 Event Type |
|------|-------|-----------------|---------------|
| `coin_transfer` | `{amount, from_country, to_country}` | Exclusive: sender loses, receiver gains. Requires sufficient treasury. | `action.transaction_propose` / `action.transaction_confirm` |
| `arms_transfer` | `{unit_type, count, from_country, to_country}` | Exclusive. 1-round reduced effectiveness for transferred units. | `action.transaction_propose` / `action.transaction_confirm` |
| `tech_transfer` | `{tech_type: "nuclear"\|"ai", from_country, to_country}` | Replicable: receiver gains progress, sender keeps. | `action.transaction_propose` / `action.transaction_confirm` |
| `basing_rights` | `{host_country, guest_country, zone_id}` | Grants deployment access. Revocable by host. | `action.transaction_propose` / `action.transaction_confirm` |
| `treaty` | `{title, text, signatories[]}` | Stored as record. Not mechanically enforced. | `action.transaction_propose` / `action.transaction_confirm` |
| `agreement` | `{title, text, type: "armistice"\|"peace"\|"alliance"\|"custom"}` | Stored. Armistice/peace update war state. | `action.agreement_sign` |
| `org_creation` | `{name, members[], charter}` | Creates new organization. Public event. | `action.organization_create` |
| `personal_investment` | `{role_id, amount, target: "nuclear"\|"ai"}` | Personal coins into country R&D. | `action.transaction_propose` / `action.transaction_confirm` |
| `bribe` | `{from_role_id, to_role_id, amount}` | Role-to-role. Visibility: role only. | `action.transaction_propose` / `action.transaction_confirm` |

**Deprecated name:** `organization_create` (use `org_creation`).

### Response (201) -- Proposal Created

```json
{
  "success": true,
  "data": {
    "transaction_id": "txn_abc123",
    "status": "pending_confirmation",
    "confirmation_token": "conf_xyz789",
    "expires_at": "2026-04-15T15:00:00Z",
    "validation": {
      "proposer_can_afford": true,
      "proposer_treasury": 42.3,
      "amount": 10.0
    }
  },
  "events": [
    {
      "id": "evt_auto_003",
      "action_type": "transaction_proposed",
      "actor_role_id": "dealer",
      "details": {
        "event_type": "coin_transfer",
        "counterparty": "helmsman",
        "amount": 10.0
      },
      "visibility": "role"
    }
  ],
  "state_changes": [],
  "warnings": [],
  "request_id": "req_def456",
  "timestamp": "2026-04-15T14:25:00Z"
}
```

### Error Responses

| HTTP | Code | When |
|------|------|------|
| 400 | `VALIDATION_INVALID_TRANSACTION_TYPE` | Unrecognized type |
| 403 | `AUTH_ROLE_MISMATCH` | Proposer lacks `negotiate` power |
| 422 | `RESOURCE_INSUFFICIENT_TREASURY` | Sender cannot afford transfer |
| 422 | `RESOURCE_NO_UNITS` | Sender does not have the units to transfer |

### Notes

- **Two-phase:** Proposal creates the transaction in `pending_confirmation` status. No state changes until confirmed.
- **Expiration:** Unconfirmed transactions expire after 30 minutes (configurable).
- **Rate limit:** 20 requests/minute per role.
- **Internal call:** `TransactionEngine.propose(transaction)` validates and creates the pending record.

---

## 2.3 POST /engine/transaction/{id}/confirm -- Confirm Transaction

Executes or rejects a pending transaction.

### Request

```json
{
  "confirmation_token": "conf_xyz789",
  "accepted": true,
  "confirmer_role_id": "helmsman"
}
```

### Response (200) -- Accepted and Executed

```json
{
  "success": true,
  "data": {
    "transaction_id": "txn_abc123",
    "status": "executed",
    "execution_timestamp": "2026-04-15T14:30:00Z"
  },
  "events": [
    {
      "id": "evt_auto_004",
      "action_type": "transaction_executed",
      "actor_role_id": "engine",
      "details": {
        "event_type": "coin_transfer",
        "from": "columbia",
        "to": "cathay",
        "amount": 10.0
      },
      "visibility": "country"
    }
  ],
  "state_changes": [
    { "path": "countries.columbia.economic.treasury", "old": 42.3, "new": 32.3 },
    { "path": "countries.cathay.economic.treasury", "old": 85.0, "new": 95.0 }
  ],
  "warnings": [],
  "request_id": "req_ghi789",
  "timestamp": "2026-04-15T14:30:00Z"
}
```

### Response (200) -- Rejected

```json
{
  "success": true,
  "data": {
    "transaction_id": "txn_abc123",
    "status": "rejected",
    "rejection_reason": "Counterparty declined"
  },
  "events": [
    {
      "id": "evt_auto_005",
      "action_type": "transaction_rejected",
      "actor_role_id": "helmsman",
      "visibility": "role"
    }
  ],
  "state_changes": [],
  "warnings": [],
  "request_id": "req_ghi790",
  "timestamp": "2026-04-15T14:30:00Z"
}
```

### Error Responses

| HTTP | Code | When |
|------|------|------|
| 403 | `AUTH_NOT_COUNTERPARTY` | Confirmer is not the designated counterparty |
| 404 | `NOT_FOUND_TRANSACTION` | Transaction ID does not exist |
| 409 | `STATE_TRANSACTION_EXPIRED` | Transaction passed expiration time |
| 409 | `STATE_TRANSACTION_ALREADY_RESOLVED` | Already confirmed or rejected |
| 422 | `RESOURCE_INSUFFICIENT_TREASURY` | Proposer's treasury changed since proposal; no longer sufficient |

### Notes

- **Idempotent:** Confirming an already-executed transaction returns the original result.
- **Re-validation:** Treasury balance is re-checked at confirmation time. If the proposer spent coins between proposal and confirmation, the transaction fails with `RESOURCE_INSUFFICIENT_TREASURY`.
- **Internal call:** `TransactionEngine.confirm(transaction_id, accepted)` executes the transfer and applies state changes.

---

## 2.4 POST /engine/round/process -- Process Round (World Model Engine)

Triggers the full between-round batch processing cycle. **Facilitator only.**

### Request

```json
{
  "sim_run_id": "sim_2026_04_15",
  "round_num": 3,
  "country_actions": {
    "columbia": {
      "budget": {
        "social_allocation": 30.0,
        "military_allocation": 15.0,
        "technology_allocation": 8.0,
        "military_production": {
          "ground": { "coins": 6.0, "tier": "normal" },
          "naval": { "coins": 5.0, "tier": "normal" }
        },
        "tech_rd": { "nuclear": 0.0, "ai": 8.0 }
      },
      "tariffs": [{ "target": "cathay", "new_level": 3 }],
      "sanctions": [{ "target": "persia", "new_level": 2 }],
      "military": [],
      "diplomatic": []
    },
    "cathay": { "...": "..." },
    "sarmatia": { "...": "..." }
  },
  "event_log": [
    {
      "id": "evt_001",
      "action_type": "attack",
      "actor_role_id": "dealer",
      "round_num": 3,
      "phase": "A",
      "details": { "...": "..." }
    }
  ],
  "options": {
    "use_ai_panel": true,
    "generate_narrative": true,
    "auto_fix_coherence": true
  },
  "idempotency_key": "round_3_process_v1"
}
```

### Request Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sim_run_id` | string | Yes | Simulation run identifier |
| `round_num` | int | Yes | Round to process |
| `country_actions` | object | Yes | All 20+ countries' submitted actions (including AI-generated). Keys are country IDs. |
| `event_log` | array | Yes | All Phase A events for this round |
| `options.use_ai_panel` | bool | No (default: true) | Whether to run Pass 2 (AI expert panel). If false, only deterministic Pass 1 runs. |
| `options.generate_narrative` | bool | No (default: true) | Whether to generate round narrative in Pass 3 |
| `options.auto_fix_coherence` | bool | No (default: true) | Whether Pass 3 auto-fixes HIGH severity contradictions |
| `idempotency_key` | string | Yes | Unique key |

### Response (200)

```json
{
  "success": true,
  "data": {
    "round_num": 3,
    "processing_time_ms": 12500,
    "passes_completed": ["deterministic", "ai_panel", "coherence"],
    "new_world_state": {
      "_schema_version": "1.0",
      "round_num": 4,
      "oil_price": 112.5,
      "countries": {
        "columbia": {
          "economic": {
            "gdp": 285.3,
            "treasury": 38.1,
            "inflation": 5.8,
            "debt_burden": 3.4,
            "economic_state": "normal",
            "momentum": 1.1,
            "revenue_last_round": 57.2
          },
          "military": { "ground": 23, "naval": 12, "tactical_air": 15, "strategic_missile": 12, "air_defense": 4 },
          "political": { "stability": 6.8, "political_support": 36.0, "war_tiredness": 0.5 },
          "technology": { "nuclear_level": 3, "nuclear_rd_progress": 1.0, "ai_level": 3, "ai_rd_progress": 0.85 }
        },
        "cathay": { "...": "..." }
      },
      "zones": { "...": "..." },
      "bilateral": { "...": "..." }
    },
    "combat_results": [
      {
        "attacker": "columbia",
        "defender": "persia",
        "zone": "persia_west",
        "outcome": "attacker_wins",
        "attacker_losses": { "ground": 1 },
        "defender_losses": { "ground": 3 }
      }
    ],
    "elections": {
      "columbia_midterms": {
        "winner": "dem",
        "margin": 52,
        "effects": { "political_support": 5 }
      }
    },
    "narrative": "Round 3 ended with a major shift in the Mashriq theater. Columbia's forces breached Persian defenses in the west, establishing a foothold that could threaten oil infrastructure. Meanwhile, the global economy showed signs of strain as oil prices climbed to $112.50, driven by OPEC production cuts and Gulf Gate tensions...",
    "expert_panel": {
      "keynes": [
        {
          "actor_country_id": "cathay",
          "assessment": "Semiconductor supply chain showing early stress from trade restrictions",
          "adjustment": { "path": "gdp_growth_rate", "delta": -0.008 },
          "confidence": 0.7
        }
      ],
      "clausewitz": [ "..." ],
      "machiavelli": [ "..." ],
      "synthesis": {
        "applied": [ "..." ],
        "rejected": [ "..." ]
      }
    },
    "coherence_flags": [
      {
        "severity": "MEDIUM",
        "description": "Persia GDP growth positive despite L2 sanctions and territorial loss",
        "auto_fixed": false,
        "actor_country_id": "persia"
      }
    ]
  },
  "events": [
    { "action_type": "gdp_update", "actor_role_id": "engine", "details": { "actor_country_id": "columbia", "old_gdp": 278.5, "new_gdp": 285.3 }, "visibility": "moderator" },
    { "action_type": "round_narrative", "actor_role_id": "engine", "details": { "narrative": "..." }, "visibility": "public" }
  ],
  "state_changes": [
    { "path": "oil_price", "old": 95.2, "new": 112.5 },
    { "path": "countries.columbia.economic.gdp", "old": 278.5, "new": 285.3 }
  ],
  "warnings": [
    "1 coherence flag at MEDIUM severity (not auto-fixed). Review recommended."
  ],
  "request_id": "req_round3",
  "timestamp": "2026-04-15T14:45:00Z"
}
```

### Error Responses

| HTTP | Code | When |
|------|------|------|
| 403 | `AUTH_NOT_MODERATOR` | Non-moderator attempting round processing |
| 409 | `STATE_ROUND_ALREADY_PROCESSED` | This round has already been processed |
| 409 | `STATE_MISSING_SUBMISSIONS` | One or more countries have not submitted budgets |
| 422 | `VALIDATION_INVALID_ROUND` | Round number does not match current game state |
| 500 | `ENGINE_PROCESSING_FAILED` | Engine error during processing |
| 504 | `ENGINE_TIMEOUT` | Processing exceeded 5-minute timeout |

### Notes

- **Authorization:** Facilitator (moderator) only. This is the most privileged engine operation.
- **Idempotent:** Re-submitting with the same key returns the cached result. The world state is not re-processed.
- **Rate limit:** 2 requests/minute (facilitator only; prevents accidental double-processing).
- **Latency:** Target < 5 minutes. Pass 1 (deterministic): < 1 second. Pass 2 (AI panel): < 30 seconds. Pass 3 (coherence + narrative): < 60 seconds.
- **Internal call:** `WorldModelEngine(world_state).process_round(round_num, country_actions, event_log)` -- the full 14-step chained pipeline.
- **Facilitator review:** The response includes `coherence_flags` and `expert_panel` data. The facilitator reviews these before publishing the new state. A separate endpoint (2.9) handles publishing.

---

## 2.5 GET /engine/state/{sim_run_id} -- Get World State

Returns the current world state snapshot.

### Request

```
GET /api/v1/engine/state/sim_2026_04_15
```

### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `round_num` | int | No | current | Specific round snapshot (for history) |
| `format` | string | No | `full` | `full` (complete state) or `summary` (key indicators only) |

### Response (200)

```json
{
  "success": true,
  "data": {
    "_schema_version": "1.0",
    "round_num": 3,
    "oil_price": 112.5,
    "oil_price_trend": [80.0, 95.2, 112.5],
    "global_trade_volume_index": 95.3,
    "nuclear_used_this_sim": false,
    "dollar_credibility": 88.5,
    "active_wars": [
      { "attacker": "sarmatia", "defender": "ruthenia", "theater": "eastern_ereb" }
    ],
    "countries": {
      "columbia": { "...": "full country state" },
      "cathay": { "...": "full country state" }
    },
    "zones": {
      "col_continental": { "owner": "columbia", "forces": { "...": "..." } }
    },
    "bilateral": {
      "columbia_cathay": { "tariff_level": 3, "sanctions_level": 0, "trade_volume": 45.0 }
    },
    "chokepoint_status": {
      "hormuz": "open",
      "malacca": "open",
      "taiwan_strait": "contested"
    }
  },
  "request_id": "req_state_001",
  "timestamp": "2026-04-15T14:50:00Z"
}
```

### Notes

- **No authentication filtering at engine level.** The engine returns the complete, unfiltered state. The Edge Function (or the caller) is responsible for filtering by role visibility before sending to the participant.
- **Rate limit:** 60 requests/minute.
- **Internal call:** `world_state.to_dict()` serialization of the in-memory WorldState object.

---

## 2.6 POST /engine/ai/deliberate -- AI Participant Decision

Requests a full decision cycle for one AI participant.

### Request

```json
{
  "sim_run_id": "sim_2026_04_15",
  "round_num": 3,
  "role_id": "helmsman",
  "country_id": "cathay",
  "world_state": { "...": "visible state only, per role visibility" },
  "role_brief": "You are the Helmsman, paramount leader of Cathay...",
  "available_actions": [
    {
      "action_type": "set_tariff",
      "constraints": { "target": "any_country", "level_range": [0, 3] }
    },
    {
      "action_type": "budget_submit",
      "constraints": { "max_total": 85.0 }
    }
  ],
  "round_context": {
    "phase": "A",
    "time_remaining_seconds": 1800,
    "recent_events": [
      { "summary": "Columbia increased tariffs on Cathay to level 3", "round_num": 3 },
      { "summary": "Oil price rose to $112.50", "round_num": 2 }
    ]
  },
  "conversation_history": [],
  "objectives": ["cathay_dominance", "formosa_control", "tech_supremacy"],
  "ticking_clock": "Must secure Formosa before Columbia builds coalition."
}
```

### Response (200)

```json
{
  "success": true,
  "data": {
    "actions": [
      {
        "action_type": "set_tariff",
        "params": { "target": "columbia", "new_level": 3 },
        "priority": 1,
        "reasoning": "Retaliatory tariff. Columbia escalated first."
      },
      {
        "action_type": "budget_submit",
        "params": {
          "social_allocation": 25.0,
          "military_allocation": 20.0,
          "technology_allocation": 12.0,
          "military_production": {
            "naval": { "coins": 10.0, "tier": "accelerated" }
          },
          "tech_rd": { "nuclear": 0.0, "ai": 12.0 }
        },
        "priority": 2,
        "reasoning": "Accelerating naval buildup for Formosa contingency."
      }
    ],
    "negotiations": [
      {
        "target_role": "shah",
        "proposal": "Joint opposition to Columbia sanctions. Cathay offers favorable trade terms.",
        "reasoning": "Persia is under Columbia pressure. Natural ally."
      }
    ],
    "statements": [
      {
        "audience": "public",
        "content": "Cathay calls for peaceful resolution and condemns unilateral tariff escalation."
      }
    ],
    "internal_reasoning": "Columbia's tariff escalation signals preparation for broader containment. Priority: (1) secure Formosa-area naval dominance, (2) build alternative trade bloc, (3) reach AI L4."
  },
  "events": [],
  "state_changes": [],
  "warnings": [],
  "request_id": "req_ai_helmsman_r3",
  "timestamp": "2026-04-15T14:52:00Z"
}
```

### Notes

- **`internal_reasoning` is MODERATOR-ONLY.** Never exposed to participants.
- **AI actions are NOT auto-executed.** The response contains the AI's decisions. The calling system (Edge Function or orchestrator) must submit them through the normal action/transaction endpoints for validation and execution.
- **Rate limit:** 30 requests/minute (burst during AI turn processing).
- **Latency:** Target < 15 seconds per AI participant (Claude API call + reasoning).
- **Internal call:** Constructs 7-block prompt per E4 spec, calls Claude API, parses structured JSON output.

---

## 2.7 POST /engine/ai/argus -- Argus AI Assistant Query

Handles a single Argus conversation turn.

### Request

```json
{
  "sim_run_id": "sim_2026_04_15",
  "role_id": "dealer",
  "phase": "mid",
  "question": "What should I do about Cathay's naval buildup near Formosa?",
  "conversation_history": [
    { "role": "user", "content": "I'm worried about Cathay's military movements." },
    { "role": "assistant", "content": "That's a valid concern. Cathay has been increasing naval production..." }
  ],
  "context": {
    "world_state_summary": "Round 3. Oil at $112.50. Columbia-Cathay tariffs at L3...",
    "role_objectives": ["secure_legacy", "manage_succession", "contain_cathay"]
  }
}
```

### Response (200)

```json
{
  "success": true,
  "data": {
    "text": "The Formosa situation requires balancing deterrence with avoiding escalation. Consider: (1) Reinforcing your Pacific naval presence signals resolve without aggression. (2) The Western Treaty alliance gives you coalition options. (3) Your election timeline means any military action must be weighed against domestic political cost. What is your primary concern -- military capability or political timing?",
    "voice_url": "https://api.elevenlabs.io/v1/text-to-speech/argus_voice_id/stream?text=...",
    "follow_up_prompts": [
      "Tell me more about the military balance",
      "How does the election affect my options?",
      "What are Cathay's likely next moves?"
    ]
  },
  "events": [],
  "state_changes": [],
  "warnings": [],
  "request_id": "req_argus_dealer_005",
  "timestamp": "2026-04-15T14:55:00Z"
}
```

### Notes

- **Argus never reveals classified information.** Prompt includes strict boundaries: no other country's private data, no moderator-only information, no AI participant internal reasoning.
- **Voice URL:** Optional. Only generated if `voice_output: true` is included in the request (default: false). Uses ElevenLabs streaming endpoint.
- **Rate limit:** 30 requests/minute per role.
- **Latency:** Target < 5 seconds (text), < 8 seconds (text + voice URL generation).
- **Internal call:** Constructs Argus prompt per E4 spec (different from AI participant prompt), calls Claude API.

---

## 2.8 POST /engine/election -- Process Election

Processes an election event. **Facilitator only.**

### Request

```json
{
  "sim_run_id": "sim_2026_04_15",
  "round_num": 3,
  "country_id": "ruthenia",
  "election_type": "wartime",
  "candidates": [
    { "role_id": "strongman", "party": "incumbent", "name": "The Strongman" },
    { "role_id": "challenger_hrt", "party": "opposition", "name": "The Challenger" }
  ],
  "votes": {
    "strongman": 45,
    "challenger_hrt": 55
  },
  "election_meddling_effects": [
    { "source_country": "columbia", "target_candidate": "challenger_hrt", "impact_percent": 3.0 }
  ],
  "idempotency_key": "election_r3_ruthenia_v1"
}
```

### Response (200)

```json
{
  "success": true,
  "data": {
    "winner": "challenger_hrt",
    "margin": 10,
    "final_votes": {
      "strongman": 45,
      "challenger_hrt": 55
    },
    "meddling_impact": {
      "columbia_for_challenger_hrt": 3.0,
      "net_effect": "Challenger gained ~3% from external meddling"
    },
    "effects": {
      "political_support": -10,
      "stability": -0.5,
      "leadership_change": {
        "old_leader": "strongman",
        "new_leader": "challenger_hrt"
      }
    }
  },
  "events": [
    {
      "id": "evt_auto_010",
      "action_type": "election_result",
      "actor_role_id": "engine",
      "details": {
        "actor_country_id": "ruthenia",
        "winner": "challenger_hrt",
        "margin": 10,
        "event_type": "wartime"
      },
      "visibility": "public"
    }
  ],
  "state_changes": [
    { "path": "countries.ruthenia.political.political_support", "old": 38, "new": 28 },
    { "path": "countries.ruthenia.political.stability", "old": 5.5, "new": 5.0 }
  ],
  "warnings": [],
  "request_id": "req_election_hrt",
  "timestamp": "2026-04-15T15:00:00Z"
}
```

### Notes

- **Authorization:** Facilitator only.
- **Vote collection is external.** The facilitator collects votes (physically or through the app's voting UI) and submits the tallied results here. The engine applies election effects to world state.
- **Election meddling:** Previously resolved covert ops that targeted this election are passed in `election_meddling_effects`. The engine factors these into the narrative but does not re-roll them.
- **Rate limit:** 2 requests/minute (facilitator only).

---

## 2.9 POST /engine/round/publish -- Publish Round Results

After the facilitator reviews the round processing results (from 2.4), this endpoint commits the new world state and broadcasts it. **Facilitator only.**

### Request

```json
{
  "sim_run_id": "sim_2026_04_15",
  "round_num": 3,
  "approved_state": "full",
  "overrides": [
    {
      "path": "countries.persia.economic.gdp_growth_rate",
      "new_value": -0.02,
      "reason": "Adjusting growth to reflect territorial loss impact"
    }
  ],
  "idempotency_key": "publish_round3_v1"
}
```

### Request Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sim_run_id` | string | Yes | Simulation run identifier |
| `round_num` | int | Yes | Round being published |
| `approved_state` | string | Yes | `"full"` (approve as-is) or `"with_overrides"` |
| `overrides` | array | No | Facilitator adjustments to engine output |
| `idempotency_key` | string | Yes | Unique key |

### Response (200)

```json
{
  "success": true,
  "data": {
    "round_published": 3,
    "overrides_applied": 1,
    "current_round": 4,
    "state_snapshot_id": "snap_r4_001"
  },
  "events": [
    {
      "action_type": "round_published",
      "actor_role_id": "facilitator",
      "visibility": "moderator"
    },
    {
      "action_type": "round_briefing",
      "actor_role_id": "engine",
      "details": { "narrative": "Round 3 ended with..." },
      "visibility": "public"
    }
  ],
  "state_changes": [
    { "path": "round_num", "old": 3, "new": 4 }
  ],
  "warnings": [],
  "request_id": "req_publish_r3",
  "timestamp": "2026-04-15T15:05:00Z"
}
```

### Notes

- **This is the trigger for state propagation.** Only after publishing does the new world state become visible to participants via Supabase Realtime.
- **Overrides create moderator-visibility events.** Every override is logged.
- **The engine server persists the new state to Supabase** via REST API, which triggers Realtime updates to all subscribers.

---

## 2.10 GET /engine/health -- Health Check

### Response (200)

```json
{
  "status": "healthy",
  "engine_version": "2.0",
  "uptime_seconds": 86400,
  "loaded_sims": ["sim_2026_04_15"],
  "python_version": "3.11.9",
  "memory_mb": 128,
  "last_round_processed": {
    "sim_run_id": "sim_2026_04_15",
    "round_num": 2,
    "processing_time_ms": 11200,
    "timestamp": "2026-04-15T12:30:00Z"
  }
}
```

---

# 3. ENGINE SERVER INTERNALS

## 3.1 State Management

The engine server holds the active WorldState in memory for the duration of a SIM run. This avoids re-loading from the database on every request.

```python
# server.py (simplified)
from fastapi import FastAPI
from world_state import WorldState
from world_model_engine import WorldModelEngine
from live_action_engine import LiveActionEngine
from transaction_engine import TransactionEngine

app = FastAPI(title="TTT Engine Server", version="2.0")

# In-memory state (one SIM at a time)
active_state: WorldState | None = None
active_sim_id: str | None = None

@app.post("/api/v1/engine/action")
async def process_action(request: ActionRequest):
    engine = LiveActionEngine(active_state)
    result = engine.resolve_action(request.action_type, request.actor_role_id, ...)
    # Persist state changes to Supabase
    await persist_state_changes(result.state_changes)
    return result
```

### State Lifecycle

1. **Load:** On SIM start, Edge Function calls `POST /engine/state/load` with initial world state JSON. Engine deserializes into `WorldState` object.
2. **Modify:** Each action/transaction/round modifies the in-memory state.
3. **Persist:** After each modification, state changes are written to Supabase via REST.
4. **Snapshot:** At round boundaries, a full state snapshot is persisted.
5. **Recovery:** If the engine server restarts, it loads the latest snapshot from Supabase.

## 3.2 Concurrency Model

```
Phase A (live play):
  - Multiple live actions can arrive concurrently
  - Transaction proposals are independent
  - Transaction confirmations must be serialized (to prevent double-spend)
  - Solution: asyncio.Lock per country for state modifications

Phase B (batch processing):
  - Single process_round call
  - No concurrent modifications allowed
  - Engine acquires global lock, processes, releases
```

## 3.3 Internal Function Mapping

| Endpoint | Engine | Method |
|----------|--------|--------|
| `POST /engine/action` (ground_attack) | `LiveActionEngine` | `resolve_attack(attacker, defender, zone, units, world_state)` |
| `POST /engine/action` (blockade) | `LiveActionEngine` | `resolve_blockade(...)` |
| `POST /engine/action` (covert) | `LiveActionEngine` | `resolve_covert_op(op_type, actor, target, world_state)` |
| `POST /engine/action` (political) | `LiveActionEngine` | `resolve_arrest()`, `resolve_fire()`, `resolve_propaganda()`, `resolve_impeachment()`, etc. |
| `POST /engine/action` (impeachment) | `LiveActionEngine` | `resolve_impeachment(country, target_role, parliament_votes)` |
| `POST /engine/action` (mobilization_order) | `LiveActionEngine` | `resolve_mobilization(country, units, deploy_to_zone)` |
| `POST /engine/action` (militia_call) | `LiveActionEngine` | `resolve_militia(country, units, deploy_to_zone)` |
| `POST /engine/deploy` | DB function | `deployment_validation()` -- validates then writes directly to deployments table |
| `POST /engine/transaction` | `TransactionEngine` | `propose_transaction(sender, receiver, tx_type, details)` |
| `POST /engine/transaction/{id}/confirm` | `TransactionEngine` | `confirm_transaction(tx_id, confirmer)` |
| `POST /engine/round/process` | `WorldModelEngine` | `process_round(world_state, all_actions, round_num)` |
| `POST /engine/election` | `WorldModelEngine` | `process_election(country, candidates, votes)` |

---

# 4. DEPLOYMENT

## 4.1 Recommended Architecture: Dedicated Server (Railway)

| Factor | Assessment |
|--------|-----------|
| **Why dedicated** | World Model Engine processing (up to 5 minutes) exceeds Edge Function limits. Engine holds state in memory for performance. Python runtime not available in Supabase Edge Functions. |
| **Why Railway** | Always-warm instances (no cold starts). Simple Python deployment. Built-in metrics. Affordable ($5-20/month). Auto-deploy from GitHub. |
| **Scaling** | Single instance. TTT runs one SIM at a time. Sequential processing by design. |
| **Alternatives rejected** | **Supabase Edge Functions:** No Python, 50s timeout. **AWS Lambda:** Cold starts (3-5s), Python dependency loading. **Fly.io:** More complex setup, similar cost. |

## 4.2 Docker Configuration

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY engine/ ./engine/
COPY server.py .

EXPOSE 8000
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 4.3 Environment Variables

| Variable | Purpose |
|----------|---------|
| `ENGINE_AUTH_SECRET` | Shared secret for HMAC authentication |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | Service role key (full database access) |
| `ANTHROPIC_API_KEY` | Claude API key (for Pass 2, Pass 3, AI participants) |
| `SENTRY_DSN` | Error tracking |

## 4.4 Monitoring Checklist (SIM Day)

| Check | Frequency | Alert threshold |
|-------|-----------|----------------|
| Health endpoint | Every 30s | Non-200 for 2 consecutive checks |
| Round processing time | Per round | > 5 minutes |
| Memory usage | Every 60s | > 512 MB |
| Error rate | Real-time | > 5 errors/minute |
| API latency (live actions) | Per request | > 3 seconds |
| Claude API availability | Every 60s | Non-200 response |

---

# 5. EDGE FUNCTION PROXY PATTERN

The Supabase Edge Functions act as authenticated proxies between the frontend and the engine server.

```typescript
// supabase/functions/engine-action/index.ts (simplified)
import { createClient } from '@supabase/supabase-js'
import { serve } from 'https://deno.land/std@0.177.0/http/server.ts'

const ENGINE_URL = Deno.env.get('ENGINE_URL')!
const ENGINE_SECRET = Deno.env.get('ENGINE_AUTH_SECRET')!

serve(async (req) => {
  // 1. Validate JWT
  const supabase = createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_ANON_KEY')!,
    { global: { headers: { Authorization: req.headers.get('Authorization')! } } }
  )
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) return new Response('Unauthorized', { status: 401 })

  // 2. Extract role claims and validate permissions
  const { role_id, country_id, access_level } = user.app_metadata
  const body = await req.json()

  // 3. Permission check (role has power for action_type)
  if (!hasPermission(role_id, body.action_type)) {
    return new Response(JSON.stringify({ error: { code: 'AUTH_ROLE_MISMATCH' } }), { status: 403 })
  }

  // 4. Forward to engine with internal auth
  const timestamp = Math.floor(Date.now() / 1000).toString()
  const signature = await hmacSign(ENGINE_SECRET, JSON.stringify(body) + timestamp)

  const engineResponse = await fetch(`${ENGINE_URL}/api/v1/engine/action`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Engine-Auth': signature,
      'X-Engine-Timestamp': timestamp,
      'X-Request-Id': crypto.randomUUID(),
    },
    body: JSON.stringify(body),
  })

  // 5. Return engine response to client
  return new Response(await engineResponse.text(), {
    status: engineResponse.status,
    headers: { 'Content-Type': 'application/json' },
  })
})
```

---

*This document specifies the complete API surface between the TTT web application and the Python engine server. For the participant-facing REST API (what the frontend calls directly via Supabase), see [F4 API Contracts](../2%20SEED/F_DATA_ARCHITECTURE/SEED_F4_API_CONTRACTS_v1.md). For engine formula details, see [D8 Engine Formulas](../2%20SEED/D_ENGINES/SEED_D8_ENGINE_FORMULAS_v1.md). For the Edge Function middleware, see [DET_EDGE_FUNCTIONS.md](DET_EDGE_FUNCTIONS.md).*

---

## CHANGELOG (v1.1, 2026-03-30)

Fixes applied per DET_VALIDATION_LEVEL1 + DET_VALIDATION_LEVEL3 findings:

- **[HIGH] Canonical action_type names:** Replaced short names (`attack`, `espionage`, `cyber`) with canonical names (`ground_attack`, `intelligence_request`, `cyber_attack`). Per DET_NAMING_CONVENTIONS 1.3. Deprecated names documented.
- **[HIGH] Added impeachment route:** `POST /engine/action` with `action_type: "impeachment"`, mapped to `LiveActionEngine.resolve_impeachment()`. Parliament vote resolution for Columbia/Ruthenia democracies.
- **[HIGH] Added deployment validation route:** `POST /engine/deploy` mapped to `deployment_validation()` database function. Validates zone adjacency, transit time, unit availability, basing rights.
- **[HIGH] Added mobilization_order and militia_call** to supported action types table.
- **[MEDIUM] Event type mapping column:** Added C1 Event Type column to both action types and transaction types tables, establishing formal mapping between F5 internal types and C1 event types.
- **[MEDIUM] Transaction type canonical names:** `org_creation` replaces `organization_create`. Per DET_NAMING_CONVENTIONS 1.2.
- **[MEDIUM] Internal function mapping updated:** Added impeachment, mobilization, militia, and deployment routes to Section 3.3 mapping table. Corrected method signatures to match actual engine code.
- **[LOW] Cross-references updated:** Added links to DET_NAMING_CONVENTIONS.md and DET_EDGE_FUNCTIONS.md.
- **[LOW] Edge Function proxy pattern:** Section 5 already existed; now references DET_EDGE_FUNCTIONS.md for the complete specification.
