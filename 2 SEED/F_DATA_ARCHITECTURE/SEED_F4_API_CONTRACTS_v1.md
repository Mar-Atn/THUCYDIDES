# TTT API Contracts
## Interface Specifications for All System Components

**Version:** 1.0 | **Date:** 2026-03-28
**Status:** SEED Design (pre-implementation)
**Cross-references:** [F2 Data Architecture](SEED_F2_DATA_ARCHITECTURE_v1.md) | [F3 Data Flows](SEED_F3_DATA_FLOWS_v1.md) | [D Engine Interface](../D_ENGINES/SEED_D_ENGINE_INTERFACE_v1.md)

---

# 1. CONVENTIONS

## 1.1 General Principles

- All endpoints accept and return JSON.
- All timestamps are ISO 8601 UTC (e.g., `"2026-04-15T14:23:07Z"`).
- All IDs are lowercase snake_case strings (matching CSV IDs).
- Pagination uses cursor-based pagination (not offset) for event log queries.
- Errors return structured error objects, not plain strings.
- All state-modifying endpoints are idempotent when given the same idempotency key.

## 1.2 Error Format

Every error response follows this structure:

```json
{
  "error": {
    "code": "INSUFFICIENT_TREASURY",
    "message": "Treasury balance (3.2) insufficient for requested spending (8.5)",
    "details": {
      "treasury": 3.2,
      "requested": 8.5,
      "deficit": 5.3
    },
    "timestamp": "2026-04-15T14:23:07Z",
    "request_id": "req_abc123"
  }
}
```

## 1.3 Error Code Categories

| Code Prefix | Category | HTTP Status | Examples |
|------------|----------|-------------|---------|
| `AUTH_*` | Authentication/Authorization | 401/403 | `AUTH_INVALID_TOKEN`, `AUTH_ROLE_MISMATCH` |
| `VALIDATION_*` | Input validation | 400 | `VALIDATION_INVALID_ROUND`, `VALIDATION_MISSING_FIELD` |
| `STATE_*` | State conflict | 409 | `STATE_ROUND_FROZEN`, `STATE_ACTION_ALREADY_SUBMITTED` |
| `RESOURCE_*` | Resource constraint | 422 | `RESOURCE_INSUFFICIENT_TREASURY`, `RESOURCE_NO_UNITS` |
| `ENGINE_*` | Engine processing | 500 | `ENGINE_PROCESSING_FAILED`, `ENGINE_TIMEOUT` |
| `NOT_FOUND_*` | Entity not found | 404 | `NOT_FOUND_COUNTRY`, `NOT_FOUND_ZONE` |

## 1.4 Standard HTTP Status Codes

| Status | Usage |
|--------|-------|
| 200 | Successful read or idempotent write |
| 201 | Successful creation (new event, new agreement) |
| 400 | Invalid request (bad JSON, missing field, invalid value) |
| 401 | Not authenticated |
| 403 | Authenticated but not authorized for this data/action |
| 404 | Entity not found |
| 409 | State conflict (round frozen, action already submitted) |
| 422 | Valid request but unprocessable (insufficient resources, invalid game state) |
| 429 | Rate limited |
| 500 | Server error |

---

# 2. AUTHENTICATION AND AUTHORIZATION

## 2.1 Identity Model

```
Session
  +-- user_id         (human player or AI agent identifier)
  +-- sim_id          (which SIM instance)
  +-- role_id         (assigned role, e.g., "dealer")
  +-- country_id      (derived from role)
  +-- access_level    (participant | moderator | spectator | admin)
  +-- permissions     (list of allowed action types, derived from role powers)
```

## 2.2 Authorization Rules

Every API request is authorized against these rules:

| Action | Required Access |
|--------|----------------|
| Read own country state | `access_level >= participant` AND `country_id == requested_country` |
| Read other country state (public tier) | `access_level >= participant` |
| Read other country state (exact values) | `access_level == moderator` |
| Submit actions for own country | `access_level >= participant` AND `country_id == action_country` AND action_type in role `permissions` |
| Submit actions for other country | DENIED (always) |
| Read moderator-only data | `access_level == moderator` |
| Override/adjust state | `access_level == moderator` |
| Read all data (spectator mode) | `access_level == spectator` (public tier only) OR `access_level == admin` (all tiers) |

## 2.3 Role-Based Permission Mapping

Permissions derive from the `powers` field in `roles.csv`. Examples:

| Power | Allowed Actions |
|-------|----------------|
| `set_tariffs` | `POST /actions` with `action_type: set_tariff` |
| `authorize_attack` | `POST /actions` with `action_type: attack` |
| `fire_team_member` | `POST /actions` with `action_type: fire_role` |
| `approve_nuclear` | `POST /actions` with `action_type: nuclear_strike` or `nuclear_test` |
| `set_opec_production` | `POST /actions` with `action_type: set_opec_production` |
| `negotiate` | `POST /transactions` with any negotiation type |
| `deploy_units` | `POST /deploy` |

Head of state has implicit authority for all country-level actions unless another role has exclusive authority.

---

# 3. PARTICIPANT ENDPOINTS (Read)

## 3.1 Get Country State

```
GET /api/v1/state/{round}/{country_id}

Authorization: participant (own country) or moderator (any country)

Response 200:
{
  "round": 3,
  "country_id": "columbia",
  "economic": {
    "gdp": 278.5,
    "treasury": 42.3,
    "inflation": 5.2,
    "debt_burden": 3.1,
    "economic_state": "normal",        // DERIVED, computed on request
    "momentum": 1.2,
    "market_index": 62,                // DERIVED, computed on request
    "revenue_last_round": 55.8,
    "budget_last_round": {
      "social": 28.0,
      "military": 15.0,
      "technology": 8.0,
      "maintenance": 12.5
    }
  },
  "military": {
    "ground": 22,
    "naval": 11,
    "tactical_air": 15,
    "strategic_missiles": 12,
    "air_defense": 4,
    "total": 64,
    "production_capacity": {
      "ground": { "max": 4, "cost": 3.0 },
      "naval": { "max": 2, "cost": 5.0 },
      "tactical_air": { "max": 3, "cost": 4.0 }
    }
  },
  "political": {
    "stability": 7.0,
    "political_support": 38.0,
    "war_tiredness": 0.0,
    "regime_status": "stable",
    "protest_risk": false,             // DERIVED
    "coup_risk": false                 // DERIVED
  },
  "technology": {
    "nuclear_level": 3,
    "nuclear_rd_progress": 1.0,
    "ai_level": 3,
    "ai_rd_progress": 0.80
  }
}

Error 403:
{
  "error": {
    "code": "AUTH_ROLE_MISMATCH",
    "message": "Role 'dealer' cannot access state for country 'cathay'"
  }
}
```

## 3.2 Get Public Map State

```
GET /api/v1/map/{round}

Authorization: any authenticated user

Response 200:
{
  "round": 3,
  "zones": [
    {
      "id": "col_continental",
      "display_name": "Columbia Continental",
      "type": "land_home",
      "owner": "columbia",
      "theater": "global",
      "visible_forces": {
        "columbia": { "ground": 8, "tactical_air": 5 }
      },
      "status": "normal"
    },
    ...
  ],
  "chokepoint_status": {
    "hormuz": "open",
    "malacca": "open",
    "taiwan_strait": "blocked",
    ...
  },
  "active_wars": [
    {
      "attacker": "sarmatia",
      "defender": "ruthenia",
      "theater": "eastern_ereb"
    },
    ...
  ],
  "oil_price": 112.50,
  "oil_price_trend": [80.0, 95.2, 112.5]
}

Notes:
- visible_forces shows only forces the requesting participant can see
  (own forces + forces in adjacent/shared zones).
- Moderator sees all forces in all zones.
- Zone forces for distant zones are omitted unless revealed by intelligence.
```

## 3.3 Get Events

```
GET /api/v1/events/{round}?cursor={cursor}&limit={limit}

Authorization: filtered by requesting role's visibility level

Query Parameters:
  round:    int (required) -- which round's events
  cursor:   string (optional) -- pagination cursor (event ID)
  limit:    int (optional, default 50, max 200) -- events per page
  type:     string (optional) -- filter by action_type
  actor:    string (optional) -- filter by actor
  country:  string (optional) -- filter by country_context

Response 200:
{
  "round": 3,
  "events": [
    {
      "id": "evt_a1b2c3d4",
      "round": 3,
      "phase": "A",
      "timestamp": "2026-04-15T14:23:07Z",
      "actor": "dealer",
      "action_type": "set_tariff",
      "target": "cathay",
      "details": {
        "old_level": 2,
        "new_level": 3,
        "sector": "all"
      },
      "result": {
        "applied": true
      },
      "visibility": "public"
    },
    ...
  ],
  "pagination": {
    "cursor": "evt_x9y8z7",
    "has_more": true,
    "total_visible": 47
  }
}

Notes:
- Events with visibility higher than the requester's access are excluded.
- 'moderator' visibility events are never returned to participants.
- 'role' visibility events are only returned to the specific role_id.
- 'country' visibility events are returned to all roles in that country.
- 'public' events are returned to everyone.
```

## 3.4 Get Round Briefing

```
GET /api/v1/briefing/{round}

Authorization: any authenticated user (content filtered by role)

Response 200:
{
  "round": 3,
  "public_narrative": "Round 3 saw escalation in the Eastern Ereb theater...",
  "country_briefing": "Columbia's economy grew 1.8% this round despite rising oil prices...",
  "key_events": [
    {
      "description": "Oil price rose to $112.50",
      "impact": "Increased import costs for major economies"
    },
    ...
  ],
  "warnings": [
    "Treasury running low -- consider reducing military spending"
  ]
}

Notes:
- public_narrative is the same for all participants.
- country_briefing is specific to the requesting participant's country.
- warnings are country-specific and only shown to country team members.
```

## 3.5 Get Role Data

```
GET /api/v1/role/{role_id}

Authorization: own role only, or moderator

Response 200:
{
  "role_id": "dealer",
  "character_name": "Dealer",
  "country_id": "columbia",
  "title": "President of Columbia",
  "status": "active",
  "personal_coins": 5.0,
  "powers": ["set_tariffs", "authorize_attack", "fire_team_member", "approve_nuclear"],
  "objectives": ["secure_legacy", "manage_succession", "contain_cathay"],
  "ticking_clock": "Term-limited, age 80. Legacy = reshaping world order.",
  "artefacts": [
    {
      "id": "dealer_intel_cathay_buildup",
      "title": "CIA Assessment: Cathay Naval Buildup Timeline",
      "classification": "role_specific"
    },
    ...
  ]
}
```

---

# 4. PARTICIPANT ENDPOINTS (Write)

## 4.1 Submit Country Actions

```
POST /api/v1/actions/{round}/{country_id}

Authorization: participant with appropriate powers for each action

Request Body:
{
  "idempotency_key": "act_round3_columbia_v2",
  "actions": {
    "budget": {
      "social_allocation": 30.0,
      "military_allocation": 15.0,
      "technology_allocation": 8.0,
      "military_production": {
        "ground": { "coins": 6.0, "tier": "normal" },
        "naval": { "coins": 5.0, "tier": "normal" },
        "tactical_air": { "coins": 4.0, "tier": "normal" }
      },
      "tech_rd": {
        "nuclear": 0.0,
        "ai": 8.0
      }
    },
    "tariffs": [
      { "target": "cathay", "new_level": 3 }
    ],
    "sanctions": [
      { "target": "persia", "new_level": 2 }
    ],
    "military": [
      { "action_type": "attack", "target_zone": "persia_west", "units": { "ground": 4, "tactical_air": 3 } }
    ],
    "diplomatic": [
      { "action_type": "public_statement", "content": "Columbia stands with Ruthenia." }
    ]
  }
}

Response 201:
{
  "status": "accepted",
  "round": 3,
  "country_id": "columbia",
  "validation": {
    "budget_valid": true,
    "actions_valid": true,
    "warnings": [
      "Military production at 'normal' tier -- 'accelerated' available with higher cost"
    ]
  },
  "events_created": 5,
  "idempotency_key": "act_round3_columbia_v2"
}

Error 422 (validation failure):
{
  "error": {
    "code": "VALIDATION_BUDGET_EXCEEDS_REVENUE",
    "message": "Total budget allocation (53.0) exceeds projected revenue (48.5)",
    "details": {
      "total_allocation": 53.0,
      "projected_revenue": 48.5,
      "treasury_available": 42.3,
      "max_with_treasury": 90.8
    }
  }
}

Error 409 (state conflict):
{
  "error": {
    "code": "STATE_ROUND_FROZEN",
    "message": "Round 2 is frozen. Current round is 3."
  }
}
```

## 4.2 Submit Deployment Orders

```
POST /api/v1/deploy/{round}/{country_id}

Authorization: participant with deploy_units power

Request Body:
{
  "idempotency_key": "dep_round3_columbia_v1",
  "deployments": [
    {
      "unit_type": "ground",
      "count": 3,
      "from_zone": "col_continental",
      "to_zone": "col_pacific"
    },
    {
      "unit_type": "naval",
      "count": 2,
      "from_zone": "col_continental",
      "to_zone": "w(12,5)"
    }
  ]
}

Response 201:
{
  "status": "accepted",
  "deployments_applied": 2,
  "events_created": 2,
  "warnings": []
}

Error 422:
{
  "error": {
    "code": "RESOURCE_NO_UNITS",
    "message": "Insufficient ground units in zone 'col_continental'. Available: 2, Requested: 3"
  }
}
```

## 4.3 Propose Transaction

```
POST /api/v1/transactions

Authorization: participant with negotiate power

Request Body:
{
  "idempotency_key": "txn_round3_dealer_helmsman_v1",
  "transaction_type": "transfer_coins",
  "proposer": "dealer",
  "counterparty": "helmsman",
  "details": {
    "from_country": "columbia",
    "to_country": "cathay",
    "amount": 10.0,
    "conditions": "In exchange for lifting rare earth restrictions on Columbia"
  }
}

Response 201:
{
  "status": "pending_confirmation",
  "transaction_id": "txn_abc123",
  "confirmation_token": "conf_xyz789",
  "expires_at": "2026-04-15T15:00:00Z",
  "message": "Awaiting confirmation from 'helmsman'"
}
```

## 4.4 Confirm Transaction

```
POST /api/v1/transactions/{transaction_id}/confirm

Authorization: counterparty role

Request Body:
{
  "confirmation_token": "conf_xyz789",
  "accepted": true
}

Response 200:
{
  "status": "executed",
  "transaction_id": "txn_abc123",
  "state_changes": [
    { "path": "countries.columbia.economic.treasury", "old": 42.3, "new": 32.3 },
    { "path": "countries.cathay.economic.treasury", "old": 85.0, "new": 95.0 }
  ],
  "events_created": 2
}

Response 200 (rejected):
{
  "status": "rejected",
  "transaction_id": "txn_abc123",
  "message": "Counterparty declined the transaction"
}
```

---

# 5. MODERATOR ENDPOINTS

## 5.1 Get Full World State (Unfiltered)

```
GET /api/v1/moderator/state/{round}

Authorization: moderator only

Response 200:
{
  "round": 3,
  "countries": { ... },     // ALL countries, ALL variables, exact values
  "zones": { ... },          // ALL zones, ALL forces
  "wars": [ ... ],
  "bilateral": { ... },
  "oil_price": 112.50,
  "global_trade_volume_index": 95.3,
  "nuclear_used_this_sim": false,
  "dollar_credibility": 88.5,
  "expert_panel_last_round": {
    "keynes": [ ... ],
    "clausewitz": [ ... ],
    "machiavelli": [ ... ],
    "applied": [ ... ],
    "flags": [ ... ]
  },
  "coherence_flags": [ ... ]
}
```

## 5.2 Moderator Override

```
POST /api/v1/moderator/override

Authorization: moderator only

Request Body:
{
  "idempotency_key": "mod_override_round3_v1",
  "overrides": [
    {
      "path": "countries.ruthenia.political.stability",
      "new_value": 4.0,
      "reason": "Manual adjustment for off-screen political crisis"
    }
  ]
}

Response 200:
{
  "status": "applied",
  "overrides_applied": 1,
  "events_created": 1,
  "warnings": [
    "Stability set to 4.0 -- this triggers protest_probable threshold"
  ]
}

Notes:
- Every override creates a moderator-visibility event in the event log.
- Overrides are applied immediately but do not retroactively change past snapshots.
- The engine will process overridden values in the next round's batch processing.
```

## 5.3 Get Expert Panel Results

```
GET /api/v1/moderator/expert-panel/{round}

Authorization: moderator only

Response 200:
{
  "round": 3,
  "panel": {
    "keynes": [
      {
        "country": "cathay",
        "assessment": "Semiconductor blockade creating demand shock. GDP contraction underestimated by 1.5pp.",
        "adjustment": { "path": "gdp_growth_rate", "delta": -0.015 },
        "confidence": 0.8
      },
      ...
    ],
    "clausewitz": [ ... ],
    "machiavelli": [ ... ],
    "synthesis": {
      "applied": [
        {
          "country": "cathay",
          "adjustment": "GDP growth reduced by additional 1.2pp (majority-rule synthesis)",
          "source_votes": ["keynes", "machiavelli"]
        }
      ],
      "rejected": [ ... ]
    },
    "flags": [
      {
        "severity": "MEDIUM",
        "description": "Cathay GDP growth positive despite active semiconductor blockade -- plausible if short duration",
        "auto_fixed": false
      }
    ]
  }
}
```

---

# 6. ENGINE INTERFACE CONTRACTS

These contracts define how the backend communicates with the three engines. They are internal interfaces (not exposed to participants) but are versioned and stable per [D Engine Interface](../D_ENGINES/SEED_D_ENGINE_INTERFACE_v1.md).

## 6.1 World Model Engine

```
FUNCTION: process_round(input) -> output

INPUT:
{
  "round_num": 3,
  "world_state": { <WorldState as JSON -- full, unfiltered> },
  "country_actions": {
    "columbia": {
      "budget": { <budget allocations> },
      "tariffs": [ <tariff changes> ],
      "sanctions": [ <sanction changes> ],
      "military": [ <military actions> ],
      "diplomatic": [ <diplomatic actions> ]
    },
    "cathay": { ... },
    ... (all 20 countries, including AI-generated actions)
  },
  "event_log": [ <all events from Phase A> ]
}

OUTPUT:
{
  "round_num": 3,
  "new_world_state": { <updated WorldState as JSON> },
  "events": [
    { <engine-generated events: gdp_update, inflation_update, etc.> }
  ],
  "combat_results": [
    {
      "attacker": "columbia",
      "defender": "persia",
      "zone": "persia_west",
      "attacker_units": { "ground": 4, "tactical_air": 3 },
      "defender_units": { "ground": 6 },
      "outcome": "attacker_repelled",
      "attacker_losses": { "ground": 2 },
      "defender_losses": { "ground": 1 }
    }
  ],
  "transactions_executed": [ ... ],
  "elections": {
    "columbia_midterms": {
      "winner": "dem",
      "margin": 52,
      "effects": { "political_support": +5 }
    }
  },
  "narrative": "Round 3: The war in Mashriq intensified as Columbia launched...",
  "expert_panel": {
    "keynes": [ ... ],
    "clausewitz": [ ... ],
    "machiavelli": [ ... ],
    "applied": [ ... ],
    "flags": [ ... ]
  },
  "coherence_flags": [
    {
      "severity": "HIGH",
      "description": "GDP growth positive during economic collapse -- forced to -2%",
      "auto_fixed": true,
      "country": "persia"
    }
  ]
}

TIMING:
  Target: < 5 minutes total
  Pass 1 (deterministic): < 1 second
  Pass 2 (AI adjustments): < 30 seconds (3 parallel LLM calls) or < 1 second (heuristic)
  Pass 3 (coherence + narrative): < 60 seconds (LLM) or < 1 second (heuristic)
```

## 6.2 Live Action Engine

```
FUNCTION: process_action(input) -> output

INPUT:
{
  "action_type": "attack",
  "actor": "dealer",
  "params": {
    "target_zone": "persia_west",
    "from_zone": "levantia_border",
    "units": { "ground": 4, "tactical_air": 3 }
  },
  "current_state": { <WorldState as JSON -- full> }
}

OUTPUT:
{
  "success": true,
  "result": {
    "outcome": "attacker_wins",
    "attacker_losses": { "ground": 1 },
    "defender_losses": { "ground": 3 },
    "zone_control_change": {
      "zone": "persia_west",
      "old_owner": "persia",
      "new_owner": "columbia"
    }
  },
  "state_changes": [
    { "path": "countries.columbia.military.ground", "old": 22, "new": 21 },
    { "path": "countries.persia.military.ground", "old": 15, "new": 12 },
    { "path": "zones.persia_west.owner", "old": "persia", "new": "columbia" }
  ],
  "events": [
    {
      "action_type": "attack",
      "actor": "dealer",
      "target": "persia_west",
      "details": { ... },
      "result": { ... },
      "visibility": "public"
    },
    {
      "action_type": "combat_result",
      "actor": "engine",
      "details": { ... },
      "visibility": "public"
    }
  ],
  "error": null
}

VALIDATION (performed before processing):
- Actor has authorization (role powers include action_type)
- Units are available in from_zone
- from_zone and target_zone are adjacent
- Action is legal in current game state (e.g., can't attack ally without war declaration)

TIMING: < 2 seconds
```

## 6.3 Transaction Engine

```
FUNCTION: process_transaction(input) -> output

INPUT:
{
  "transaction_type": "transfer_coins",
  "proposer": "dealer",
  "counterparty": "helmsman",
  "details": {
    "from_country": "columbia",
    "to_country": "cathay",
    "amount": 10.0,
    "conditions": "In exchange for lifting rare earth restrictions"
  },
  "current_state": { <WorldState as JSON -- full> }
}

OUTPUT (proposal stage):
{
  "success": true,
  "requires_confirmation": true,
  "confirmation_token": "conf_xyz789",
  "validation": {
    "proposer_can_afford": true,
    "proposer_treasury": 42.3,
    "amount": 10.0
  },
  "state_changes": [],
  "events": [
    {
      "action_type": "transfer_coins",
      "actor": "dealer",
      "phase": "proposed",
      "visibility": "role"
    }
  ],
  "error": null
}

OUTPUT (execution stage, after counterparty confirms):
{
  "success": true,
  "requires_confirmation": false,
  "state_changes": [
    { "path": "countries.columbia.economic.treasury", "old": 42.3, "new": 32.3 },
    { "path": "countries.cathay.economic.treasury", "old": 85.0, "new": 95.0 }
  ],
  "events": [
    {
      "action_type": "transfer_coins",
      "actor": "dealer",
      "phase": "executed",
      "details": { "amount": 10.0, "from": "columbia", "to": "cathay" },
      "visibility": "country"
    }
  ],
  "error": null
}

SUPPORTED TRANSACTION TYPES:
  transfer_coins    -- direct treasury transfer between countries
  trade_deal        -- structured trade agreement with terms
  basing_rights     -- military basing permission
  aid_package       -- economic aid (may be public or secret)
  personal_invest   -- role personal coins into country R&D
  bribe             -- covert payment (role-to-role, visibility: role)

TIMING: < 5 seconds (including validation)
```

---

# 7. REAL-TIME UPDATES (WebSocket)

## 7.1 Connection Model

```
WebSocket: wss://api.example.com/ws/v1/sim/{sim_id}

Authentication: JWT token in connection handshake
Channel assignment: automatic based on role_id in token

Channels:
  public          -- all participants receive (oil price, war declarations, etc.)
  country:{id}    -- country team members receive (own economic updates, etc.)
  role:{id}       -- specific role receives (personal coin changes, intel, etc.)
  moderator       -- moderator only (engine diagnostics, flags, etc.)
```

## 7.2 Message Format

```json
{
  "type": "event",
  "channel": "public",
  "payload": {
    "id": "evt_a1b2c3d4",
    "round": 3,
    "phase": "A",
    "timestamp": "2026-04-15T14:23:07Z",
    "action_type": "attack",
    "summary": "Columbia forces attacked Persia West -- attacker wins",
    "details": { ... }
  }
}
```

## 7.3 Message Types

| Type | Direction | Description |
|------|-----------|-------------|
| `event` | Server -> Client | New event matching client's visibility level |
| `state_update` | Server -> Client | State change notification (delta, not full state) |
| `phase_change` | Server -> Client | Round phase transition (A->B, B->C, etc.) |
| `timer` | Server -> Client | Phase time remaining countdown |
| `notification` | Server -> Client | System message (moderator announcement, etc.) |
| `ping` | Client -> Server | Keepalive |
| `pong` | Server -> Client | Keepalive response |
| `subscribe` | Client -> Server | Request additional channel subscription (moderator use) |

## 7.4 State Update Deltas

Rather than pushing the full state on every change, the server pushes deltas:

```json
{
  "type": "state_update",
  "channel": "country:columbia",
  "payload": {
    "round": 3,
    "changes": [
      {
        "path": "military.ground",
        "old": 22,
        "new": 21,
        "reason": "combat_losses"
      }
    ],
    "snapshot_version": 47
  }
}
```

Clients maintain a local state copy and apply deltas. If a client detects a version mismatch, it requests the full state via REST (`GET /api/v1/state/{round}/{country_id}`).

---

# 8. AI PARTICIPANT INTERFACE

## 8.1 AI Agent Input

```json
{
  "role_id": "helmsman",
  "role_brief": "<full prose brief from role_briefs/HELMSMAN.md>",
  "visible_state": {
    "own_country": {
      "economic": { ... },
      "military": { ... },
      "political": { ... },
      "technology": { ... }
    },
    "world": {
      "oil_price": 112.5,
      "active_wars": [ ... ],
      "chokepoint_status": { ... },
      "public_economic_tiers": {
        "columbia": "major",
        "ruthenia": "medium",
        "persia": "medium"
      }
    },
    "map": {
      "own_forces": { ... },
      "visible_forces": { ... }
    },
    "relationships": {
      "columbia": "hostile",
      "ruthenia": "tense",
      "persia": "neutral"
    }
  },
  "available_actions": [
    {
      "action_type": "set_tariff",
      "constraints": { "target": "<any country>", "level": "0-3" },
      "cost": null
    },
    {
      "action_type": "budget_submit",
      "constraints": { "total": "<= revenue + treasury" },
      "cost": null
    },
    ...
  ],
  "round_context": {
    "round_num": 3,
    "phase": "A",
    "time_remaining_seconds": 1800,
    "recent_events": [
      { "summary": "Columbia increased tariffs on Cathay to level 3", "round": 3 },
      { "summary": "Oil price rose to $112.50", "round": 2 }
    ]
  },
  "objectives": ["cathay_dominance", "formosa_control", "tech_supremacy"],
  "ticking_clock": "Must secure Formosa before Columbia builds coalition."
}
```

## 8.2 AI Agent Output

```json
{
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
      "reasoning": "Accelerating naval buildup for Formosa contingency. Heavy AI investment to reach L4."
    }
  ],
  "negotiations": [
    {
      "target_role": "shah",
      "proposal": "Joint opposition to Columbia sanctions. Cathay offers favorable trade terms.",
      "reasoning": "Persia is under Columbia pressure. Natural ally against Western coalition."
    }
  ],
  "statements": [
    {
      "audience": "public",
      "content": "Cathay calls for peaceful resolution of all disputes and condemns unilateral tariff escalation."
    }
  ],
  "internal_reasoning": "Columbia's tariff escalation signals preparation for broader containment. Priority: (1) secure Formosa-area naval dominance, (2) build alternative trade bloc, (3) reach AI L4 for economic and military advantage. Risk: overextension if Formosa blockade triggers semiconductor disruption to own economy."
}

Notes:
- internal_reasoning is MODERATOR-ONLY visibility. Never shown to other participants.
- AI actions go through the same validation pipeline as human actions.
- AI output is logged as events with actor = role_id (not 'ai').
```

---

# 9. PAGINATION AND QUERY PATTERNS

## 9.1 Cursor-Based Pagination

All list endpoints use cursor-based pagination for consistent results even as new events are appended.

```
First page:   GET /api/v1/events/3?limit=50
Next page:    GET /api/v1/events/3?limit=50&cursor=evt_x9y8z7
```

The cursor is the ID of the last item in the previous page. The server returns items AFTER this cursor.

## 9.2 Event Log Query Optimization

Event log queries are the most frequent read operation. Index strategy:

| Index | Query Pattern |
|-------|--------------|
| `(round, visibility, timestamp)` | Events for a round, filtered by visibility |
| `(actor, round)` | Events by a specific actor |
| `(action_type, round)` | Events of a specific type |
| `(country_context, round)` | Events affecting a specific country |
| `(id)` | Cursor-based pagination |

## 9.3 Rate Limiting

| Endpoint Category | Rate Limit |
|------------------|-----------|
| Read (state, map, events) | 60 requests/minute per role |
| Write (actions, deploy) | 10 requests/minute per role |
| Transactions | 20 requests/minute per role |
| WebSocket messages | 30 messages/minute per connection |
| Moderator endpoints | 120 requests/minute |

---

# 10. VERSIONING AND BACKWARD COMPATIBILITY

## 10.1 API Versioning

All endpoints are prefixed with `/api/v1/`. When breaking changes are needed:

1. New version deployed at `/api/v2/` alongside `/api/v1/`.
2. Old version supported for at least one full SIM cycle.
3. Deprecation warnings added to old version responses.
4. Migration guide published.

## 10.2 State Schema Versioning

Every state snapshot includes a schema version:

```json
{
  "_schema_version": "1.0",
  "round_num": 3,
  ...
}
```

The engine's `from_dict()` method handles backward compatibility by checking `_schema_version` and applying migrations for older snapshots.

## 10.3 Event Schema Stability

The event log schema (Part 4 of [F2 Data Architecture](SEED_F2_DATA_ARCHITECTURE_v1.md)) is treated as a public interface. Changes to event structure require:

1. New fields added as optional (backward compatible).
2. Existing fields never removed (only deprecated).
3. `action_type` vocabulary is append-only (new types added, existing types never removed or renamed).

---

*This document specifies all API interfaces for the TTT system. For data structure definitions, see [F2 Data Architecture](SEED_F2_DATA_ARCHITECTURE_v1.md). For data flow diagrams, see [F3 Data Flows](SEED_F3_DATA_FLOWS_v1.md).*
